#!/usr/bin/env python3
"""Import pinned whole-edition public JSONs with source-bound language versions.

The provider's shared, typed hadithnumber identifies an occurrence in THIS API,
not a canonical number in another edition. Every input and missing/held entry is
preserved. A book is exported only after all three whole-edition files verify.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import copy
import datetime as dt
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from build_reader import local, parse_json, safe_url
from import_deenhindi import classify as classify_arabic


REPOSITORY = "fawazahmed0/hadith-api"
REVISION = "df57907be35291c91ad6a6691180e22ca9920784"
IMPORT = "imports/web-fawaz-20261112"
PLAN = "catalog/fawaz-bulk-plan.json"
EDITION = "fawaz-api-" + REVISION[:12]
MAX_CANONICAL_BYTES = 40 * 1024 * 1024
MAX_RESPONSE_BYTES = 64 * 1024 * 1024
BOOKS = {
    "abudawud": ("abu-dawud", "Sunan Abu Dawud"),
    "bukhari": ("bukhari", "Sahih al Bukhari"),
    "ibnmajah": ("ibn-majah", "Sunan Ibn Majah"),
    "malik": ("malik", "Muwatta Malik"),
    "muslim": ("muslim", "Sahih Muslim"),
    "nasai": ("nasai", "Sunan an Nasai"),
    "tirmidhi": ("tirmidhi", "Jami At Tirmidhi"),
}
LANGUAGES = {"ara": ("ar", "Arabic", "Arab"), "eng": ("en", "English", "Latn"),
             "urd": ("ur", "Urdu", "Arab")}
DOCUMENTS = ("editions.json", "README.md", "LICENSE", "References.md", "CONTRIBUTING.md")
DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
AUTHOR_NOTES = {
    ("abudawud", "en"): re.compile(r"Abu\s+D(?:a['’]?w[uū]d|a['’]?ud)\s+(?:said|says)\s*:?", re.I),
    ("tirmidhi", "en"): re.compile(r"Abu\s+['‘’`]?(?:Eisa|Isa|Eesa)\s+(?:said|says)\s*:?", re.I),
    ("abudawud", "ar"): re.compile(r"قال\s+ابو\s+داود\b"),
    ("tirmidhi", "ar"): re.compile(r"قال\s+ابو\s+عيسي\b"),
    ("abudawud", "ur"): re.compile(r"(?:امام\s+)?ابو\s*دا[ؤو]د\s+کہتے\s+ہیں"),
    ("tirmidhi", "ur"): re.compile(r"(?:امام\s+)?ترمذی\s+کہتے\s+ہیں"),
}
UNRESOLVED_COMPILER_BOUNDARIES = {
    "malik": re.compile(r"قال\s+(?:يحيي\s+قال\s+)?مالك\b"),
    "bukhari": re.compile(r"قال\s+(?:ابو\s+عبد\s*الله|البخاري)\b"),
    "tirmidhi": re.compile(r"(?:هذا|وهذا)\s+حديث\s+(?:حسن|صحيح|غريب)\b"),
}
AMBIGUOUS_ATTRIBUTION = re.compile(
    r"(?:وددت|وددنا|ليتني|ليتنا)\b[\s\S]{0,100}(?:رسول الله|النبي)\b"
    r"|(?:على|علي)\s+منبر\s+(?:رسول الله|النبي)\b[\s\S]{0,70}\bيقول\b")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def atomic(root, relative, data):
    path = local(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def save_json(root, relative, value):
    atomic(root, relative, encoded(value))


def read_json(root, relative, default=None):
    path = local(root, relative)
    return parse_json(path.read_text(encoding="utf-8")) if path.exists() else default


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_plan(root):
    plan = read_json(root, PLAN)
    require(isinstance(plan, dict) and plan.get("schema") == "hadith-bank-fawaz-bulk-plan-v1", "Invalid Fawaz bulk plan")
    require(plan.get("repository") == REPOSITORY and plan.get("revision") == REVISION, "Plan must use the authorized pinned source revision")
    books = plan.get("books")
    require(isinstance(books, list) and books and len(set(books)) == len(books) and set(books) <= set(BOOKS), "Invalid source books")
    require(plan.get("languages") == list(LANGUAGES), "The batch requires Arabic, English and Urdu; Hindi is not supplied by this provider")
    budget = plan.get("max_books_per_batch", 7)
    require(type(budget) is int and 1 <= budget <= 7, "Invalid whole-book batch budget")
    return plan


def provider_url(relative):
    allowed = set(DOCUMENTS) | {"editions/" + prefix + "-" + book + ".json" for book in BOOKS for prefix in LANGUAGES}
    require(relative in allowed, "Unconfigured upstream path")
    return "https://raw.githubusercontent.com/" + REPOSITORY + "/" + REVISION + "/" + relative


def entry_url(edition, number):
    token = str(number)
    require(re.fullmatch(r"[A-Za-z0-9._-]+", token) is not None, "Unsupported provider entry identifier")
    return "https://cdn.jsdelivr.net/gh/" + REPOSITORY + "@" + REVISION + "/editions/" + edition + "/" + token + ".json"


class FetchFailure(Exception):
    def __init__(self, message, *, access_denied=False):
        super().__init__(message)
        self.access_denied = access_denied


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        raise FetchFailure("Pinned source unexpectedly redirected; inspect before changing the acquisition route")


def fetch_bytes(relative):
    url = provider_url(relative)
    request = urllib.request.Request(url, headers={"User-Agent": "HadithBankSourceImporter/1.0", "Accept": "application/json,text/plain"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=45) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
            require(len(data) <= MAX_RESPONSE_BYTES, "Upstream whole-edition response exceeds the bounded size")
            require(response.status == 200 and response.url == url, "Unexpected pinned-source response")
    except urllib.error.HTTPError as error:
        raise FetchFailure("HTTP " + str(error.code) + " for " + relative,
                           access_denied=error.code in (401, 403, 451)) from error
    except urllib.error.URLError as error:
        raise FetchFailure("Source request failed for " + relative + ": " + str(error.reason)[:240]) from error
    return data, {"url": url, "retrieved_at": now(), "method": "documented_public_whole_edition_http_get"}


def snapshot(root, relative, raw, receipt):
    require(receipt.get("url") == provider_url(relative), "Snapshot receipt URL differs from pinned source")
    raw_hash = sha(raw)
    stored = gzip.compress(raw, compresslevel=9, mtime=0)
    path = IMPORT + "/raw/" + raw_hash + (".json.gz" if relative.endswith(".json") else ".txt.gz")
    destination = local(root, path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        require(destination.read_bytes() == stored, "Immutable source snapshot collision")
    else:
        atomic(root, path, stored)
    return {"path": path, "sha256": raw_hash, "bytes": len(raw), "compression": "gzip",
            "stored_sha256": sha(stored), "stored_bytes": len(stored), "source_path": relative,
            "repository": REPOSITORY, "revision": REVISION, "url": receipt["url"],
            "retrieved_at": receipt.get("retrieved_at"), "acquisition_method": receipt.get("method", "verified_prior_download_receipt")}


def checked_snapshot(root, item):
    require(item.get("revision") == REVISION and item.get("url") == provider_url(item.get("source_path")), "Snapshot source revision or URL mismatch")
    require(isinstance(item.get("path"), str) and item["path"].startswith(IMPORT + "/raw/"), "Snapshot path outside this intake")
    stored = local(root, item["path"]).read_bytes()
    require(len(stored) == item["stored_bytes"] and sha(stored) == item["stored_sha256"], "Stored source checksum mismatch")
    raw = gzip.decompress(stored)
    require(len(raw) == item["bytes"] and sha(raw) == item["sha256"], "Expanded source checksum mismatch")
    return raw


def validate_state_inputs(root, state):
    require(isinstance(state.get("inputs"), dict), "Invalid saved source input map")
    for key, item in state["inputs"].items():
        require(isinstance(item, dict) and item.get("source_path") == key,
                "Saved input key does not match its pinned source path: " + str(key))
        checked_snapshot(root, item)


def typed_identity(number):
    require(type(number) in (int, float, str), "Provider identity must be a scalar number or string")
    require(not isinstance(number, float) or math.isfinite(number), "Nonfinite provider identity")
    require(re.fullmatch(r"[A-Za-z0-9._-]+", str(number)) is not None, "Unsupported provider identity")
    # JSON type and decimal value remain significant; never integer-cast IDs.
    return json.dumps(number, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def edition_metadata(catalog, book, prefix):
    require(book in catalog and isinstance(catalog[book], dict), "Missing source catalog book")
    name = prefix + "-" + book
    matches = [value for value in catalog[book].get("collection", []) if value.get("name") == name]
    require(len(matches) == 1 and matches[0].get("book") == book and matches[0].get("language") == LANGUAGES[prefix][1], "Catalog edition identity mismatch: " + name)
    return matches[0]


def parse_edition(raw, metadata, catalog_title):
    data = parse_json(raw.decode("utf-8"))
    require(isinstance(data, dict) and isinstance(data.get("metadata"), dict) and
            isinstance(data.get("hadiths"), list) and data["hadiths"], "Invalid or empty whole-edition JSON")
    require(data["metadata"].get("name") == catalog_title, "Source book title differs from pinned catalog")
    require(isinstance(data["metadata"].get("sections"), dict), "Missing provider section metadata")
    for row in data["hadiths"]:
        require(isinstance(row, dict), "Provider row is not an object")
        typed_identity(row.get("hadithnumber"))
        require(isinstance(row.get("text"), str), "Provider text is not a string")
        require(isinstance(row.get("reference"), dict) and isinstance(row.get("grades"), list), "Missing provider reference or grades")
        require(all(isinstance(grade, dict) for grade in row["grades"]), "Provider grade must be an object")
    return data


def normalized_with_offsets(value):
    characters, offsets = [], []
    trans = str.maketrans("أإآىٱ", "ااايا")
    for position, char in enumerate(value):
        if not DIACRITICS.fullmatch(char):
            characters.append(char.translate(trans))
            offsets.append(position)
    return "".join(characters), offsets


def split_compiler_note(text, book, language):
    pattern = AUTHOR_NOTES.get((book, language))
    if pattern is None:
        return text, [], {"quotation": [0, len(text)], "notes": []}
    normalized, offsets = normalized_with_offsets(text) if language == "ar" else (text, list(range(len(text))))
    match = pattern.search(normalized)
    if not match:
        return text, [], {"quotation": [0, len(text)], "notes": []}
    boundary = offsets[match.start()]
    if boundary and text[boundary - 1] == "[":
        boundary -= 1
    return text[:boundary], [text[boundary:]], {"quotation": [0, boundary], "notes": [[boundary, len(text)]],
        "method": "literal_named_compiler_note_boundary_v1", "rule": pattern.pattern,
        "note_embedded_narration_extraction": "pending; no additional occurrence inferred"}


def classify_group(versions):
    arabic = versions.get("ara", {}).get("quotation", "")
    normalized, _ = normalized_with_offsets(arabic)
    ambiguous = AMBIGUOUS_ATTRIBUTION.search(normalized)
    if ambiguous:
        return {"classification": "held", "reason": "attribution_subject_requires_review",
                "evidence_language": "ar", "normalized_evidence": ambiguous.group(),
                "scope": "A wish about the Prophet or a possessive pulpit mention does not establish that he is the reported speaker"}
    for item in versions.values():
        if item.get("unresolved_compiler_boundary"):
            return {"classification": "held", "reason": "commentary_boundary_pending",
                    "evidence": item["unresolved_compiler_boundary"],
                    "scope": "Named-compiler material may be commentary or narrational context; preserve before separating"}
    for item in versions.values():
        reference = item["row"].get("reference", {})
        section = item["metadata"].get("sections", {}).get(str(reference.get("book")), "")
        if isinstance(section, str) and re.fullmatch(r"\s*(?:Introduction|Muqaddimah|مقدمة|المقدمة)\s*", section, re.I):
            return {"classification": "held", "reason": "source_introduction_requires_bounded_narration_review", "section_as_supplied": section}
    evidence = classify_arabic({"textArabic": arabic})
    if evidence["classification"] == "hadith":
        return {**evidence, "reason": "explicit_prophetic_attribution", "scope": "source_attribution_not_authenticity"}
    # A translational report is usable evidence only for its same provider ID.
    for prefix, pattern in (
        ("eng", r"(?:the\s+Prophet|Allah['’]s\s+(?:Messenger|Apostle)|the\s+Messenger\s+of\s+Allah)\s*(?:\([^)]{0,80}\)\s*)?(?:said|says|replied|asked|ordered|forbade|used\s+to|prayed|performed|commanded|answered)\b"),
        ("urd", r"(?:رسول\s+اللہ|نبی\s+کریم|نبی\s+اکرم)\s*(?:صلی\s+اللہ\s+علیہ\s+وسلم\s*)?(?:نے\s+(?:فرمایا|حکم|منع|کہا)|فرماتے)"),
    ):
        match = re.search(pattern, versions.get(prefix, {}).get("quotation", ""), re.I)
        if match:
            return {"classification": "hadith", "reason": "explicit_prophetic_attribution", "method": "explicit_source_language_report_v1",
                    "evidence_language": LANGUAGES[prefix][0], "evidence": match.group(),
                    "scope": "source_attribution_not_authenticity", "independent_authenticity_assessment": False}
    return {"classification": "held", "reason": "prophetic_attribution_or_quotation_boundary_not_established",
            "scope": "May be non-Prophetic, abbreviated or unresolved; not a final non-hadith judgement"}


def source_credits(root, state):
    raw = checked_snapshot(root, state["inputs"]["References.md"]).decode("utf-8")
    urls = list(dict.fromkeys(re.findall(r"https?://[^\s<>\]\)]+", raw)))
    return [{"name": urllib.parse.urlsplit(url).netloc, "url": url,
             "scope": "provider_project_level_credit_not_record_verified"} for url in urls if safe_url(url)]


def provenance(meta, is_arabic=False):
    author = meta.get("author")
    translator = author if isinstance(author, str) and author.strip() and author.lower() != "unknown" and not is_arabic else None
    return {"ai_translation": "unknown", "origin": "unknown", "translator": translator,
            "basis": "Pinned publisher catalog attribution; extraction is not translation",
            "source_declaration": None}, translator


def canonical_record(book, identity, versions, classification, state):
    occurrence = "fawaz:" + REVISION[:12] + ":" + book + ":" + urllib.parse.quote(identity, safe="._-")
    primary = next(prefix for prefix in LANGUAGES if versions.get(prefix, {}).get("quotation", "").strip())
    language = LANGUAGES[primary][0]
    readings, references, grades = [], [], {}
    for prefix in LANGUAGES:
        item = versions.get(prefix)
        if item is None:
            continue
        row, meta, snap = item["row"], item["catalog"], item["snapshot"]
        grades[LANGUAGES[prefix][0]] = copy.deepcopy(row["grades"])
        quotation = item["quotation"]
        if not quotation.strip():
            continue
        code, _, script = LANGUAGES[prefix]
        url = entry_url(meta["name"], row["hadithnumber"])
        origin, translator = provenance(meta, code == "ar")
        own_refs = [{"collection": BOOKS[book][1], "number": str(row["hadithnumber"]),
                     "source_citation": "Fawaz Ahmed Hadith API · " + meta["name"] + " · entry " + str(row["hadithnumber"]),
                     "url": url, "scope": "provider_entry_identity", "numbering_system": "fawaz_api_hadithnumber",
                     "canonical_mapping_status": "not_inferred", "provider_numbers": {"hadithnumber": row["hadithnumber"],
                         "arabicnumber": row.get("arabicnumber"), "reference": copy.deepcopy(row["reference"])}}]
        comments = [{"text": value, "source_url": url, "scope": "source_compiler_note",
                     "embedded_narrations": "retained_here_pending_separate_boundary_review"} for value in item["notes"]]
        for grade in row["grades"]:
            # Display literal assessment and assessor in this language's own notes.
            name, value = grade.get("name"), grade.get("grade")
            comments.append({"text": "Source assessment — " + (str(name) if name is not None else "Assessor not supplied") + ": " +
                             (str(value) if value is not None else "Grade not supplied"), "source_url": url,
                             "scope": "provider_assessment_metadata", "source_grade": copy.deepcopy(grade)})
        if isinstance(meta.get("comments"), str) and meta["comments"].strip():
            comments.append({"text": meta["comments"], "source_url": state["inputs"]["editions.json"]["url"], "scope": "edition_catalog_comment"})
        own_source = {"name": "Fawaz Ahmed Hadith API — " + BOOKS[book][1] + " — " + LANGUAGES[prefix][1],
            "record_url": url, "url": snap["url"], "provider_edition": meta["name"], "revision": REVISION,
            "snapshot_path": snap["path"], "snapshot_sha256": snap["sha256"],
            "snapshot_stored_sha256": snap["stored_sha256"], "snapshot_compression": "gzip",
            "json_pointer": "/hadiths/" + str(item["position"]), "field": "text",
            "source_text_sha256": sha(row["text"].encode()), "text_spans": item["spans"],
            "catalog_source_as_supplied": meta.get("source"), "catalog_author_as_supplied": meta.get("author"),
            "project_credits_locator": state["inputs"]["References.md"]["path"],
            "project_credits_scope": "provider_project_level_credit_not_record_verified",
            "translator": {"name": translator, "evidence": "pinned_edition_catalog_author" if translator else None},
            "entry_url_status": "documented_provider_route; exact imported bytes come from the pinned bulk snapshot"}
        if safe_url(meta.get("source")):
            own_source["upstream_sources"] = [{"name": meta["source"], "url": meta["source"], "scope": "edition_catalog_source_not_record_verified"}]
        readings.append({"id": occurrence + ":" + prefix, "language": code, "script": script,
                         "text": quotation, "source": own_source, "references": own_refs, "comments": comments,
                         "grading": copy.deepcopy(row["grades"]), "provider_numbers": copy.deepcopy(own_refs[0]["provider_numbers"]),
                         "translation_provenance": None if code == "ar" else origin,
                         "scope": "source_excerpt" if item["notes"] else "source_entry", "match_status": "same_source_record"})
        references.extend(own_refs)
    first = versions[primary]
    origin, translator = provenance(first["catalog"], language == "ar")
    return {"id": occurrence, "language": language, "book_key": BOOKS[book][0], "edition": EDITION,
        "record_type": "hadith", "content_kind": "source_attributed_prophetic_narration",
        "title": first["metadata"]["sections"].get(str(first["row"]["reference"].get("book"))) or None,
        "text": {"arabic": (versions.get("ara", {}).get("quotation")
                            if versions.get("ara", {}).get("quotation", "").strip() else None), "translation": first["quotation"]},
        "language_versions": readings,
        "source": {"title": "Fawaz Ahmed Hadith API — " + BOOKS[book][1], "url": "https://github.com/" + REPOSITORY,
                   "record_url": entry_url(first["catalog"]["name"], first["row"]["hadithnumber"]),
                   "revision": REVISION, "provider_identity": {"book": book, "typed_hadithnumber": identity},
                   "shared_identity_basis": "Documented provider edition numbering, unique within each file, matching supplied reference/arabicnumber"},
        "number": {"source_entry_id": first["row"]["hadithnumber"], "in_book": None, "canonical": None,
                   "numbering_system": "fawaz_api_hadithnumber", "as_supplied_by_language": {
                       LANGUAGES[p][0]: {k: copy.deepcopy(v["row"].get(k)) for k in ("hadithnumber", "arabicnumber", "reference")} for p, v in versions.items()}},
        "narrator": {"name": None}, "translator": {"name": translator, "evidence": "pinned_edition_catalog_author" if translator else None},
        "ai_translation": "unknown", "translation_provenance": origin,
        "references": {"items": references, "canonical_mapping_status": "not_inferred"},
        "grading": {"grade": None, "grader": None, "source_assessments_by_language": grades,
                    "scope": "Each assessment belongs to its supplied language version; not an independent bank grade"},
        "commentary": {"arabic": None, "translation": None}, "footnotes": [], "source_headings": [],
        "page": {"pdf": [], "printed": [], "sheet": None, "row": None},
        "review": {"status": "source_transcription_unreviewed", "independent_pro_qc": "pending", "release_status": "owner_authorized_source_import",
                   "release_eligible": False, "certified_release_eligible": False, "issues": []},
        "rights": {"status": "upstream_translation_rights_not_independently_assessed", "repository_license": "Unlicense",
                   "license_scope": "Repository software declaration; not a new license assertion for each upstream translation", "reuse_basis": None},
        "extraction": {"method": "pinned_public_whole_edition_json", "ocr_used": False, "is_excerpt": bool(first["notes"]),
                       "new_translation_produced": False, "exact_quote_spans_preserved": True,
                       "source_attribution": classification},
        "source_locator": {"revision": REVISION, "provider_book": book, "typed_hadithnumber": identity,
                           "versions": {p: {"path": v["snapshot"]["path"], "sha256": v["snapshot"]["sha256"], "json_pointer": "/hadiths/" + str(v["position"])} for p, v in versions.items()}},
        "related_versions": []}


def book_records(book, editions, catalog, state):
    groups = collections.OrderedDict()
    for prefix in LANGUAGES:
        data = editions[prefix]
        for position, row in enumerate(data["hadiths"]):
            key = typed_identity(row["hadithnumber"])
            quotation, notes, spans = split_compiler_note(row["text"], book, LANGUAGES[prefix][0])
            item = {"row": row, "position": position, "quotation": quotation, "notes": notes, "spans": spans,
                    "metadata": data["metadata"], "catalog": edition_metadata(catalog, book, prefix),
                    "snapshot": state["inputs"]["editions/" + prefix + "-" + book + ".json"]}
            if prefix == "ara" and book in UNRESOLVED_COMPILER_BOUNDARIES:
                normalized, _ = normalized_with_offsets(quotation)
                marker = UNRESOLVED_COMPILER_BOUNDARIES[book].search(normalized)
                if marker:
                    item["unresolved_compiler_boundary"] = {"language": "ar", "normalized_marker": marker.group(),
                        "source_text_sha256": sha(row["text"].encode()), "json_pointer": "/hadiths/" + str(position) + "/text"}
            groups.setdefault(key, {}).setdefault(prefix, []).append(item)
    accepted, held, ledger = [], [], []
    for identity, rows in groups.items():
        reason = None
        if any(len(items) != 1 for items in rows.values()):
            reason = "duplicate_provider_identity_within_edition"
        versions = {prefix: items[0] for prefix, items in rows.items()}
        for field in ("reference", "arabicnumber"):
            values = {json.dumps(value["row"][field], sort_keys=True, ensure_ascii=False) for value in versions.values() if value["row"].get(field) is not None}
            if len(values) > 1:
                reason = "inconsistent_shared_provider_" + field
        if not any(item["quotation"].strip() for item in versions.values()):
            reason = reason or "no_nonempty_narration_text"
        classification = {"classification": "held", "reason": reason} if reason else classify_group(versions)
        item_ledger = {"provider_book": book, "typed_hadithnumber": identity, "classification": classification,
                       "available_text_languages": [LANGUAGES[p][0] for p, v in versions.items() if v["quotation"].strip()],
                       "source_note_languages": [LANGUAGES[p][0] for p, v in versions.items() if v["notes"]]}
        ledger.append(item_ledger)
        if classification["classification"] == "hadith":
            accepted.append(canonical_record(book, identity, versions, classification, state))
        else:
            held.append({**item_ledger, "show_in_html_hadith": False, "source_versions": {
                prefix: [{"position": item["position"], "source_path": item["snapshot"]["path"],
                          "source_sha256": item["snapshot"]["sha256"], "row": item["row"], "text_spans": item["spans"]} for item in items]
                for prefix, items in rows.items()}})
    counts = {"provider_occurrences": len(groups), "registered_occurrences": len(accepted), "held_occurrences": len(held),
              "by_hold_reason": dict(collections.Counter(item["classification"]["reason"] for item in held)),
              "source_rows_by_language": {LANGUAGES[p][0]: len(data["hadiths"]) for p, data in editions.items()},
              "nonempty_source_texts_by_language": {LANGUAGES[p][0]: sum(bool(row["text"].strip()) for row in data["hadiths"]) for p, data in editions.items()}}
    return accepted, held, ledger, counts


def canonical_shards(rows, limit=MAX_CANONICAL_BYTES):
    require(type(limit) is int and limit > 0, "Invalid shard size")
    result, part, current, size = [], 1, [], 0
    for original in rows:
        row = copy.deepcopy(original)
        row["edition"] = EDITION if part == 1 else EDITION + "-part-" + str(part).zfill(3)
        data = encoded(row)
        if current and size + len(data) > limit:
            result.append((part, b"".join(current)))
            part, current, size = part + 1, [], 0
            row["edition"] = EDITION + "-part-" + str(part).zfill(3)
            data = encoded(row)
        require(len(data) <= limit, "One occurrence exceeds the safe canonical shard size")
        current.append(data)
        size += len(data)
    if current:
        result.append((part, b"".join(current)))
    return result


def export_book(root, book, state, catalog):
    editions = {prefix: parse_edition(checked_snapshot(root, state["inputs"]["editions/" + prefix + "-" + book + ".json"]),
                edition_metadata(catalog, book, prefix), catalog[book]["name"]) for prefix in LANGUAGES}
    accepted, held, ledger, counts = book_records(book, editions, catalog, state)
    atomic(root, IMPORT + "/held/" + book + ".jsonl.gz", gzip.compress(b"".join(encoded(row) for row in held), mtime=0))
    atomic(root, IMPORT + "/classification/" + book + ".jsonl.gz", gzip.compress(b"".join(encoded(row) for row in ledger), mtime=0))
    snapshot_keys = list(DOCUMENTS) + ["editions/" + p + "-" + book + ".json" for p in LANGUAGES]
    supporting = [{"path": state["inputs"][key]["path"], "sha256": state["inputs"][key]["stored_sha256"],
                   "size_bytes": state["inputs"][key]["stored_bytes"], "compression": "gzip",
                   "original_response_sha256": state["inputs"][key]["sha256"]} for key in snapshot_keys]
    source_index = {"schema": "hadith-bank-fawaz-source-index-v1", "repository": REPOSITORY, "revision": REVISION,
                    "provider_book": book, "source_snapshots": {key: state["inputs"][key] for key in snapshot_keys},
                    "edition_metadata": {p: edition_metadata(catalog, book, p) for p in LANGUAGES},
                    "project_credits": source_credits(root, state), "project_credits_scope": "project_wide_not_record_verified",
                    "license": {"declaration": "Unlicense", "exact_snapshot": state["inputs"]["LICENSE"],
                                "upstream_translation_rights": "not_independently_assessed"}}
    source_bytes = encoded(source_index)
    active = set()
    for language in sorted({row["language"] for row in accepted}):
        rows = [row for row in accepted if row["language"] == language]
        shards = canonical_shards(rows)
        for part, data in shards:
            suffix = "" if part == 1 else "-part-" + str(part).zfill(3)
            identifier = "fawaz-" + book + "-" + REVISION[:12] + "-" + language + suffix
            active.add(identifier)
            base = "materials/" + identifier
            atomic(root, base + "/records.jsonl", data)
            atomic(root, base + "/source-index.json", source_bytes)
            manifest = {"schema": "hadith-bank-material-v1", "id": identifier, "adapter": "records-v1", "language": language,
                "book": BOOKS[book][0], "edition": EDITION + suffix, "source_id": identifier,
                "records": {"path": base + "/records.jsonl", "sha256": sha(data), "count": data.count(b"\n")},
                "source": {"path": base + "/source-index.json", "sha256": sha(source_bytes),
                           "name": "Fawaz Ahmed Hadith API — " + BOOKS[book][1], "format": "pinned_json_source_index",
                           "url": "https://github.com/" + REPOSITORY + "/tree/" + REVISION},
                "publication": {"authorized": True, "decision": "owner_requested_public_source_import", "decision_date_japan": "2026-11-12",
                                "independent_qc_asserted": False, "rights_clearance_asserted": False},
                "supporting_files": supporting, "import_coverage": counts,
                "rights": {"status": "upstream_translation_rights_not_independently_assessed", "repository_license": "Unlicense"},
                "storage_shard": {"part": part, "parts": len(shards), "max_canonical_bytes": MAX_CANONICAL_BYTES,
                                  "scope": "Disjoint source-occurrence storage part; no new translation or narration"}}
            save_json(root, base + "/manifest.json", manifest)
    # Retire only this pinned source's formerly generated material directories.
    for directory in (root / "materials").glob("fawaz-" + book + "-" + REVISION[:12] + "-*"):
        if directory.name not in active:
            path = directory / "manifest.json"
            require(path.is_file(), "Unrecognized partial material directory requires inspection")
            destination = local(root, IMPORT + "/retired-materials/" + directory.name + "-" + sha(path.read_bytes())[:16])
            require(not destination.exists(), "Existing retired material checkpoint requires inspection")
            destination.parent.mkdir(parents=True, exist_ok=True)
            directory.rename(destination)
    return counts


def export_saved(root, plan, state):
    inputs, by_book = state["inputs"], {}
    # Validate every saved input before writing any new derived material.
    validate_state_inputs(root, state)
    if all(key in inputs for key in DOCUMENTS):
        catalog = parse_json(checked_snapshot(root, inputs["editions.json"]).decode("utf-8"))
        for book in plan["books"]:
            if all("editions/" + prefix + "-" + book + ".json" in inputs for prefix in LANGUAGES):
                by_book[book] = export_book(root, book, state, catalog)
    completed = list(by_book)
    pending = [book for book in plan["books"] if book not in completed]
    summary = {"schema": "hadith-bank-fawaz-bulk-progress-v1", "revision": REVISION,
        "status": "stopped" if state.get("stop") else "complete" if not pending else "partial",
        "fetched_editions": sum(key.startswith("editions/") for key in inputs),
        "registered_occurrences": sum(value["registered_occurrences"] for value in by_book.values()),
        "held_occurrences": sum(value["held_occurrences"] for value in by_book.values()),
        "provider_occurrences": sum(value["provider_occurrences"] for value in by_book.values()),
        "completed_books": completed, "pending_books": pending, "complete": not pending,
        "stop": state.get("stop"), "by_book": by_book,
        "scope": "Pinned Fawaz provider occurrences; not additional Deen Hindi page acquisitions or globally deduplicated narrations",
        "certified_release_eligible": False}
    save_json(root, IMPORT + "/progress.json", summary)
    return summary


def adopt_input(root, directory, relative):
    filename = "editions-pinned.json" if relative == "editions.json" else Path(relative).name
    receipt_name = "editions-pinned.receipt.json" if relative == "editions.json" else filename.replace(".json", ".receipt.json") if relative.startswith("editions/") else filename + ".receipt.json"
    raw_path, receipt_path = directory / filename, directory / receipt_name
    if not raw_path.exists() or not receipt_path.exists():
        return None
    receipt = parse_json(receipt_path.read_text(encoding="utf-8"))
    raw = raw_path.read_bytes()
    require(receipt.get("commit") == REVISION and receipt.get("url") == provider_url(relative), "Adoption receipt revision/URL mismatch: " + filename)
    require(receipt.get("sha256") == sha(raw) and receipt.get("bytes") == len(raw), "Adoption receipt checksum mismatch: " + filename)
    return raw, receipt


@contextlib.contextmanager
def importer_lock(root):
    path = local(root, ".work/fawaz-bulk.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                stream.write(b"0"); stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def run(args):
    root = args.root.resolve()
    require((root / "AGENTS.md").is_file(), "--root must be a Hadith Bank checkout")
    plan = load_plan(root)
    state_path = IMPORT + "/state.json"
    state = read_json(root, state_path, {"schema": "hadith-bank-fawaz-bulk-state-v1", "revision": REVISION, "inputs": {}, "stop": None})
    require(state.get("schema") == "hadith-bank-fawaz-bulk-state-v1" and state.get("revision") == REVISION and isinstance(state.get("inputs"), dict), "Invalid saved source state")
    validate_state_inputs(root, state)
    if args.export_only and not args.adopt_dir:
        return export_saved(root, plan, state), 0
    if args.fetch:
        require(plan.get("enabled") is True, "Bulk acquisition is disabled in the plan")
        if state.get("stop"):
            require(args.retry_failed and not state["stop"].get("access_denied"), "Saved source stop requires inspection; access denials are not retried")
            state["stop"] = None
    books = [book for book in plan["books"] if not all("editions/" + p + "-" + book + ".json" in state["inputs"] for p in LANGUAGES)]
    budget = args.max_books if args.max_books is not None else plan.get("max_books_per_batch", 7)
    require(type(budget) is int and 1 <= budget <= 7, "--max-books must be between 1 and 7")
    keys = list(DOCUMENTS) + ["editions/" + p + "-" + book + ".json" for book in books[:budget] for p in LANGUAGES]
    failed = False
    for relative in keys:
        if relative in state["inputs"]:
            continue
        saved = None
        try:
            adopted = adopt_input(root, args.adopt_dir, relative) if args.adopt_dir else None
            if adopted:
                raw, receipt = adopted
            elif args.fetch:
                raw, receipt = fetch_bytes(relative)
            else:
                continue
            saved = snapshot(root, relative, raw, receipt)
            if relative.endswith(".json"):
                parse_json(raw.decode("utf-8"))
            if relative.startswith("editions/"):
                prefix, book = Path(relative).stem.split("-", 1)
                require("editions.json" in state["inputs"], "A pinned source catalog is required before adopting editions")
                catalog = parse_json(checked_snapshot(root, state["inputs"]["editions.json"]).decode("utf-8"))
                parse_edition(raw, edition_metadata(catalog, book, prefix), catalog[book]["name"])
            state["inputs"][relative] = saved
            state["complete_input_books"] = [book for book in plan["books"] if all(
                "editions/" + prefix + "-" + book + ".json" in state["inputs"] for prefix in LANGUAGES)]
            save_json(root, state_path, state)
        except (FetchFailure, ValueError, OSError, EOFError) as error:
            if saved is not None and relative not in state["inputs"]:
                state.setdefault("rejected_inputs", {})[relative] = saved
            state["stop"] = {"source_path": relative, "error": str(error)[:500],
                             "access_denied": isinstance(error, FetchFailure) and error.access_denied, "at": now()}
            save_json(root, state_path, state)
            failed = True
            break
    summary = export_saved(root, plan, state)
    return summary, 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--fetch", action="store_true", help="Fetch missing configured whole-edition files; checkpoint each verified source")
    modes.add_argument("--export-only", action="store_true", help="Rebuild from verified saved snapshots without network access")
    parser.add_argument("--adopt-dir", type=Path, help="Reuse already downloaded pinned bytes and exact receipts before considering network")
    parser.add_argument("--max-books", type=int, help="Bound this run to this many incomplete books")
    parser.add_argument("--retry-failed", action="store_true", help="Explicitly resume after inspecting a non-access-denial source failure")
    args = parser.parse_args(argv)
    try:
        with importer_lock(args.root.resolve()):
            summary, code = run(args)
        print(json.dumps({key: summary[key] for key in ("status", "revision", "fetched_editions", "registered_occurrences", "held_occurrences", "completed_books", "pending_books", "complete")}, ensure_ascii=True))
        return code
    except (ValueError, OSError, EOFError) as error:
        print("Fawaz bulk import stopped: " + str(error)[:500], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
