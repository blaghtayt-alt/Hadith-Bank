#!/usr/bin/env python3
"""Resumable, source-preserving intake of Deen Hindi's public hadith pages.

Only ordinary public HTML is fetched. The complete seven-book identifier queue
comes from those pages' own embedded inventories, never an invented number range.
Every successful response and parsed source object is immutable and hash-bound.
Run bounded batches, for example --max-records 21 --delay-seconds 1.25. A zero
budget rebuilds derived files from saved inputs without making network requests.
Publication is owner-authorized pending review; rights and source AI provenance
remain unassessed. A source's book label is not a marfu/authenticity decision.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import datetime as dt
import gzip
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

from web_source_reviews import SourceReviews
from deenhindi_review_reuse import ExactReviewReuse


BASE = "https://deenhindi.com"
IMPORT = "imports/web-deenhindi-20261112"
RETRY_MANIFEST = IMPORT + "/retry-authorizations.json"
EDITION = "deenhindi-web-20261112"
MAX_CANONICAL_BYTES = 40 * 1024 * 1024
USER_AGENT = "HadithBankSourceImporter/1.0"
BOOKS = {
    "bukhari": ("bukhari", "Sahih Al-Bukhari"),
    "muslim": ("muslim", "Sahih Muslim"),
    "tirmidhi": ("tirmidhi", "Jami` at-Tirmidhi"),
    "nasai": ("nasai", "Sunan an-Nasa'i"),
    "abudawud": ("abu-dawud", "Sunan Abi Dawud"),
    "ibnmajah": ("ibn-majah", "Sunan Ibn Majah"),
    "malik": ("malik", "Muwatta Malik"),
}
LANGUAGE_FIELDS = {
    "ar": "textArabic", "hi": "translationHindi", "ur": "translationUrdu",
    "ur-Latn": "translationUrduRoman", "en": "translationEnglish",
}
UPSTREAM = [
    {"name": "Fawaz Ahmed Hadith API", "url": "https://github.com/fawazahmed0/hadith-api",
     "scope": "site_level_attribution_not_record_verified"},
    {"name": "Sunnah.com", "url": "https://sunnah.com/",
     "scope": "site_level_attribution_not_record_verified"},
]
DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
PROPHETIC = re.compile(
    r"(?:قال|يقول|سمعت|سمع|سمعنا|رايت|راي|راينا|سال|سالت|سئل|كان|عن|ان|نهانا|امرنا|صلي|توضا|اغتسل|سجد|قام|جلس|خرج|دخل|دعا)"
    r"\s+(?:(?:لنا|لهم|لي|له)\s+)?(?:رسول الله|النبي|نبي الله)\b"
    r"|(?:رسول الله|النبي|نبي الله)\b\s+(?:صلي الله عليه وسلم\s+)?(?:قال|يقول|فقال|كان|امر|نهي)"
    r"|(?:كنت مع|كنا مع|دخلت علي|جاء رجل الي|اتي رجل الي)\s+(?:رسول الله|النبي|نبي الله)\b"
)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path, value):
    atomic(path, json_bytes(value))


def immutable(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError("Immutable snapshot collision: " + str(path))


def rows_bytes(rows):
    return b"".join((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8") for row in rows)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts, self.visible = [], []
        self.in_script = False
        self.in_style = False
        self.current = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.in_script, self.current = True, []
        elif tag == "style":
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.scripts.append("".join(self.current))
            self.in_script = False
        elif tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_script:
            self.current.append(data)
        elif not self.in_style:
            self.visible.append(data)


def page_payload(raw):
    parser = PageParser()
    parser.feed(raw.decode("utf-8", errors="strict"))
    chunks = []
    for script in parser.scripts:
        for match in re.finditer(r'self\.__next_f\.push\(\[1,("(?:\\.|[^"\\])*")\]\)', script):
            chunks.append(json.loads(match.group(1)))
    if not chunks:
        raise ValueError("No public page data found; extraction stopped without guessing")
    return "".join(chunks), " ".join(parser.visible)


def flight_texts(payload):
    """Read length-prefixed React text rows without executing any JavaScript."""
    data, values = payload.encode("utf-8"), {}
    position = 0
    while position < len(data):
        match = re.match(rb'([0-9a-f]+):T([0-9a-f]+),', data[position:])
        if match:
            start = position + match.end()
            end = start + int(match.group(2), 16)
            if end > len(data):
                raise ValueError("Incomplete length-prefixed page text")
            values[match.group(1).decode()] = data[start:end].decode("utf-8", errors="strict")
            position = end
        else:
            end = data.find(b"\n", position)
            if end < 0:
                break
            position = end + 1
    return values


def payload_object(payload, key):
    pattern = re.compile('"' + re.escape(key) + r'"\s*:')
    for match in pattern.finditer(payload):
        try:
            value, _ = json.JSONDecoder().raw_decode(payload[match.end():].lstrip())
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("Missing page object: " + key)


def is_soft_verification_page(raw):
    """Recognize the observed HTTP-200 gate without mistaking source text for it."""
    html = raw.decode("utf-8", errors="replace")
    if not re.search(r"<title\b[^>]*>\s*One moment,\s*please(?:\.{3}|…)\s*</title\s*>",
                     html, re.IGNORECASE):
        return False
    parser = PageParser()
    parser.feed(html)
    if not re.search(r"\bPlease\s+wait\s+while\s+your\s+request\s+is\s+being\s+verified(?:\.{3}|…)",
                     " ".join(parser.visible), re.IGNORECASE):
        return False
    try:
        payload, _ = page_payload(raw)
    except (ValueError, UnicodeError):
        return True
    # A real source object still goes through the existing identity and text
    # checks, even if a page happens to display the same verification wording.
    for key in ("hadith", "collection"):
        try:
            payload_object(payload, key)
        except ValueError:
            continue
        return False
    return True


def parse_inventory(raw, slug):
    payload, _ = page_payload(raw)
    value = payload_object(payload, "collection")
    if value.get("slug") != slug:
        raise ValueError("Collection page identity mismatch")
    metadata = value.get("hadithsMetadata")
    if not isinstance(metadata, list) or not metadata:
        raise ValueError("Missing observed collection inventory")
    identifiers = []
    for item in metadata:
        number = item.get("hadithNumber")
        if not isinstance(number, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", number):
            raise ValueError("Unexpected source identifier; preserve and inspect before import")
        identifiers.append(number)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate identifiers in source inventory")
    return {"slug": slug, "name": value.get("name"), "identifiers": identifiers}


def parse_record(raw, slug, number):
    payload, visible = page_payload(raw)
    value = payload_object(payload, "hadith")
    if str(value.get("hadithNumber")) != number or value.get("collectionSlug", slug) != slug:
        raise ValueError("Record page identity differs from queued identity")
    strings = flight_texts(payload)
    for field in LANGUAGE_FIELDS.values():
        text = value.get(field)
        if isinstance(text, str) and re.fullmatch(r"\$[0-9a-f]+", text):
            if text[1:] not in strings:
                raise ValueError("Unresolved source text reference: " + field)
            value[field] = strings[text[1:]]
        if value.get(field) is not None and not isinstance(value[field], str):
            raise ValueError("Nontext language field: " + field)
    reference = re.search(r"Reference\s*:\s*(\[[^\]]+\])", visible)
    return value, reference.group(1) if reference else None


def classify(value):
    """Conservative source attribution, never an authenticity/grade assessment."""
    arabic = value.get("textArabic") or ""
    normalized = DIACRITICS.sub("", arabic).translate(str.maketrans("أإآى", "اااي"))
    normalized = re.sub(r"\s+", " ", normalized)
    match = PROPHETIC.search(normalized)
    if match:
        return {"classification": "hadith", "method": "explicit_prophetic_attribution_in_source_arabic",
                "rule_version": "deenhindi-attribution-v3-token-boundaries", "evidence_language": "ar",
                "evidence": match.group(), "evidence_normalization": "Arabic diacritics/tatweel removed, alef/ya normalized only for attribution check; source text unchanged",
                "independent_authenticity_assessment": False,
                "scope_note": "Prophetic attribution evidence includes narrated speech, actions, dhikr and dialogue; source grade is a separate claim."}
    return {"classification": "unknown", "method": "no_unambiguous_supported_attribution_pattern",
            "rule_version": "deenhindi-attribution-v3-token-boundaries",
            "evidence": None, "independent_authenticity_assessment": False,
            "scope_note": "Not excluded as non-hadith; retained for classification. Book membership or a grade alone does not establish Prophetic attribution."}


class Halt(Exception):
    def __init__(self, message, snapshot=None):
        super().__init__(message)
        self.snapshot = snapshot


class BudgetExpired(Exception):
    pass


class Fetcher:
    def __init__(self, root, delay, timeout, deadline=None):
        self.root, self.delay, self.timeout = root, delay, timeout
        self.deadline = deadline
        self.last = None
        self.robot = None

    def get(self, url):
        if self.deadline is not None and time.monotonic() >= self.deadline:
            raise BudgetExpired()
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "deenhindi.com" or parsed.path.startswith(("/api/", "/_next/", "/admin", "/profile/")):
            raise ValueError("Only observed ordinary public Deen Hindi pages are allowed")
        if self.robot is not None and not self.robot.can_fetch(USER_AGENT, url):
            raise Halt("robots.txt disallows this ordinary public URL: " + url)
        if self.last is not None:
            time.sleep(max(0, self.delay - (time.monotonic() - self.last)))
        if self.deadline is not None and time.monotonic() >= self.deadline:
            raise BudgetExpired()
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                final = response.geturl()
                if urllib.parse.urlsplit(final).netloc != "deenhindi.com":
                    raise Halt("Unexpected cross-site redirect: " + final)
                data = response.read(16 * 1024 * 1024 + 1)
                if len(data) > 16 * 1024 * 1024:
                    raise ValueError("Response exceeds bounded single-page size")
                metadata = {"url": url, "final_url": final, "retrieved_at": now(),
                            "status": response.status, "content_type": response.headers.get("Content-Type"),
                            "sha256": digest(data), "bytes": len(data)}
        except urllib.error.HTTPError as error:
            if error.code in (401, 403, 429):
                raise Halt("HTTP " + str(error.code) + " received; no retry or bypass: " + url) from error
            raise
        finally:
            self.last = time.monotonic()
        is_text = parsed.path.endswith("robots.txt")
        suffix = ".txt" if is_text else ".html.gz"
        stored = data if is_text else gzip.compress(data, compresslevel=9, mtime=0)
        path = Path(IMPORT) / "raw" / (metadata["sha256"] + suffix)
        immutable(self.root / path, stored)
        metadata["path"] = path.as_posix()
        metadata["compression"] = None if is_text else "gzip"
        metadata["stored_sha256"] = digest(stored)
        metadata["stored_bytes"] = len(stored)
        if metadata["status"] == 200 and is_soft_verification_page(data):
            raise Halt("HTTP 200 verification page received; no retry or bypass: " + url,
                       snapshot=metadata)
        return data, metadata


def load_json(path, fallback=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


@contextlib.contextmanager
def importer_lock(root):
    """Prevent simultaneous batches from replacing each other's checkpoints."""
    path = root.resolve() / ".work" / "deenhindi-import.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def checked_bytes(root, evidence):
    relative = Path(evidence["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Unsafe source snapshot path")
    stored = (root / relative).read_bytes()
    if evidence.get("stored_sha256") and digest(stored) != evidence["stored_sha256"]:
        raise ValueError("Saved source storage checksum mismatch: " + str(relative))
    raw = gzip.decompress(stored) if evidence.get("compression") == "gzip" else stored
    if digest(raw) != evidence["sha256"]:
        raise ValueError("Saved source checksum mismatch: " + str(relative))
    return raw


def historical_error_class(root, key, error):
    """Classify an archived failure without contacting the source website."""
    snapshot = error.get("snapshot") or {}
    status = snapshot.get("status", error.get("http_status"))
    if status in (401, 403, 429):
        return "access_or_rate_limit_stop"
    if snapshot.get("path"):
        raw = checked_bytes(root, snapshot)
        if is_soft_verification_page(raw):
            return "http_200_verification_page"
        slug, number = key.split(":", 1)
        try:
            parse_record(raw, slug, number)
        except (ValueError, UnicodeError):
            return "saved_page_parse_failure"
        return "offline_recovery_available"
    message = error.get("error", "")
    match = re.search(r"\bHTTP(?: Error)?\s+(\d{3})\b", message)
    if status is None and match:
        status = int(match.group(1))
    if status in (401, 403, 429):
        return "access_or_rate_limit_stop"
    if status in (500, 502, 503, 504) or re.search(
            r"\btimed? out\b|\btemporary failure\b|\bconnection reset\b", message, re.IGNORECASE):
        return "transient_fetch_error"
    return "unclassified_historical_error"


def reviewed_error_candidates(root, state, inventories):
    """Validate exact one-request authorizations; never clear an access stop.

    Receipt identity binds to the original error bytes, so editing or growing
    the manifest cannot replay an already consumed historical request. A
    prepared request with an uncertain outcome remains consumed after a crash.
    """
    path = root / RETRY_MANIFEST
    if not path.exists():
        return {}
    encoded = path.read_bytes()
    manifest = json.loads(encoded)
    if (not isinstance(manifest, dict)
            or manifest.get("schema") != "deenhindi-reviewed-error-retry-v1"
            or manifest.get("site") != "deenhindi.com"
            or manifest.get("scope") != "one_ordinary_request_per_listed_error"
            or manifest.get("automatic_challenge_retries") is not False
            or type(manifest.get("stop_batch_after_reviewed_retry", False)) is not bool
            or not isinstance(manifest.get("authorization_basis"), str)
            or not manifest["authorization_basis"].strip()
            or not isinstance(manifest.get("entries"), list)):
        raise ValueError("Invalid reviewed Deen Hindi retry manifest")
    candidates, seen = {}, set()
    attempts = state.get("reviewed_error_attempts", {})
    for decision in manifest["entries"]:
        if not isinstance(decision, dict):
            raise ValueError("Reviewed retry entries must be objects")
        key = decision.get("key")
        if not isinstance(key, str) or key.count(":") != 1 or key in seen:
            raise ValueError("Invalid or duplicate reviewed error identity")
        seen.add(key)
        slug, number = key.split(":", 1)
        if slug not in BOOKS or number not in inventories.get(slug, {}).get("identifiers", []):
            raise ValueError("Reviewed retry is absent from the observed source inventory: " + key)
        url = BASE + "/hadith/" + slug + "/" + urllib.parse.quote(number, safe="")
        if (decision.get("url") != url or decision.get("archived_response_reviewed") is not True
                or type(decision.get("max_requests")) is not int or decision["max_requests"] != 1
                or not isinstance(decision.get("reason"), str) or not decision["reason"].strip()
                or not re.fullmatch(r"[0-9a-f]{64}", decision.get("error_entry_sha256", ""))
                or not re.fullmatch(r"[0-9a-f]{64}", decision.get("snapshot_sha256", ""))):
            raise ValueError("Reviewed retry lacks exact source/error evidence: " + key)
        attempt_id = key + ":" + decision["error_entry_sha256"]
        receipt = attempts.get(attempt_id)
        if receipt:
            if (receipt.get("key") != key
                    or digest(json_bytes(receipt.get("prior_error"))) != decision["error_entry_sha256"]
                    or (receipt["prior_error"].get("snapshot") or {}).get("sha256") != decision["snapshot_sha256"]):
                raise ValueError("Reviewed retry receipt no longer binds to its historical evidence: " + key)
            if receipt.get("authorization_consumed") is not False:
                continue
            if receipt.get("status") != "not_requested_deadline":
                raise ValueError("Only a proven pre-request deadline may leave retry authorization unconsumed")
        error = state.get("errors", {}).get(key)
        if error is None or key in state.get("imported", {}):
            raise ValueError("Reviewed retry does not identify an unresolved source error: " + key)
        snapshot = error.get("snapshot") or {}
        if (digest(json_bytes(error)) != decision["error_entry_sha256"]
                or error.get("url") != url or snapshot.get("url") != url
                or snapshot.get("sha256") != decision["snapshot_sha256"]):
            raise ValueError("Reviewed retry source/error hash mismatch: " + key)
        classification = historical_error_class(root, key, error)
        if (classification not in ("http_200_verification_page", "saved_page_parse_failure")
                or classification != decision.get("archive_classification")):
            raise ValueError("Reviewed retry archive classification is unsupported or changed: " + key)
        candidates[key] = {"attempt_id": attempt_id, "decision": decision,
            "manifest": {"path": RETRY_MANIFEST, "sha256": digest(encoded)},
            "authorization_basis": manifest["authorization_basis"], "prior_error": error,
            "stop_batch_after_reviewed_retry": manifest.get("stop_batch_after_reviewed_retry", False)}
    return candidates


def retain_error_history(state, key):
    previous = state.get("errors", {}).get(key)
    if previous is None:
        return
    history = state.setdefault("error_history", {}).setdefault(key, [])
    if not any(digest(json_bytes(item)) == digest(json_bytes(previous)) for item in history):
        history.append(json.loads(json_bytes(previous)))


def retry_progress(state, reviewed_candidates):
    errors = state.get("errors", {})
    history = state.get("error_history", {})
    attempts = state.get("reviewed_error_attempts", {})
    return {
        "historical_error_identities_count": len(set(errors) | set(history)),
        "resolved_historical_error_identities_count": sum(
            key in state.get("imported", {}) and key not in errors for key in history),
        "unresolved_historical_error_identities_count": len(errors),
        "reviewed_error_retry_pending_count": len(reviewed_candidates),
        "reviewed_error_attempts_count": len(attempts),
        "reviewed_error_attempt_outcomes": dict(collections.Counter(
            item.get("status", "unknown") for item in attempts.values())),
    }


def reference_objects(slug, number, literal, url):
    return [{"collection": BOOKS[slug][1], "number": number,
             "source_citation": literal, "url": url,
             "source_citation_extraction": "HTML text nodes joined with single spaces; collection and identifier preserved",
             "scope": "source_site_numbering_not_independently_canonicalized"}]


def canonical_record(saved):
    slug, number, value = saved["collection"], saved["number"], saved["source_record"]
    source_id = "deenhindi-" + slug
    occurrence = source_id + ":" + number
    url = saved["snapshot"]["url"]
    refs = reference_objects(slug, number, saved["source_reference_verbatim"], url)
    provenance = {"ai_translation": "unknown", "origin": "unknown", "translator": None,
                  "basis": "Source page does not identify translation origin; extraction is not translation.",
                  "source_declaration": None}
    versions = []
    for language, field in LANGUAGE_FIELDS.items():
        body = value.get(field)
        if body is None or body == "":
            continue
        versions.append({"id": occurrence + ":" + language, "language": language,
                         "script": {"ar": "Arab", "hi": "Deva", "ur": "Arab", "ur-Latn": "Latn", "en": "Latn"}[language],
                         "text": body, "source": {"name": "Deen Hindi — " + BOOKS[slug][1],
                             "url": BASE + "/hadith/" + slug, "record_url": url,
                             "upstream_sources": UPSTREAM, "upstream_attribution_evidence_url": BASE + "/page/about-us",
                             "snapshot_path": saved["snapshot"]["path"], "snapshot_sha256": saved["snapshot"]["sha256"],
                             "snapshot_compression": saved["snapshot"].get("compression"),
                             "snapshot_stored_sha256": saved["snapshot"].get("stored_sha256"),
                             "source_field": field},
                         "references": refs, "comments": [],
                         "translation_provenance": None if language == "ar" else dict(provenance),
                         "scope": "source_entry", "match_status": "same_source_record"})
    return {"id": occurrence, "language": "hi", "book_key": BOOKS[slug][0], "edition": EDITION,
            "record_type": "hadith", "content_kind": "source_attributed_prophetic_narration",
            "title": value.get("chapterHindi") or value.get("chapterName"),
            "text": {"arabic": value.get("textArabic") or None, "translation": value.get("translationHindi") or None},
            "language_versions": versions,
            "source": {"title": "Deen Hindi — " + BOOKS[slug][1], "url": BASE + "/hadith/" + slug,
                       "record_url": url, "source_internal_id": value.get("id"),
                       "snapshot": saved["snapshot"], "parsed_source_path": saved["parsed_path"],
                       "upstream_sources": UPSTREAM, "upstream_attribution_evidence_url": BASE + "/page/about-us"},
            "number": {"source_entry_id": number, "in_book": None, "canonical": None,
                       "scope": "source_site", "as_printed": saved["source_reference_verbatim"],
                       "numbering_system": "Deen Hindi source numbering; not assumed identical across editions"},
            "narrator": {"name": value.get("narrator"), "as_supplied": {k: value.get(k) for k in ("narrator", "narratorHindi", "narratorUrdu", "narratorEnglish")}},
            "translator": {"name": None, "evidence": None}, "ai_translation": "unknown",
            "translation_provenance": dict(provenance),
            "commentary": {"arabic": None, "translation": None}, "footnotes": [],
            "references": {"items": refs, "scope": "source_site_numbering", "canonical_mapping_status": "unassessed"},
            "grading": {"grade": value.get("grade"), "grader": None, "basis": "Literal website grade; grader not supplied"},
            "page": {"pdf": [], "printed": [], "sheet": None, "row": None},
            "source_headings": [value[k] for k in ("chapterName",) if value.get(k)],
            "review": {"status": "source_transcription_unreviewed", "independent_pro_qc": "pending",
                       "release_status": "owner_authorized_pending_review", "release_eligible": False,
                       "certified_release_eligible": False, "issues": []},
            "rights": {"status": "not_assessed_for_publication", "reuse_basis": None,
                       "source_notice": "© 2026 Deen Hindi. All rights reserved.", "source_notice_url": url},
            "extraction": {"method": "public_html_embedded_json", "ocr_used": False, "is_excerpt": False,
                           "source_text_unchanged": True, "new_translation_produced": False,
                           "empty_field_normalization": "Empty source strings become null in canonical text; exact original values remain in the parsed source snapshot"},
            "source_locator": {"path": saved["snapshot"]["path"], "sha256": saved["snapshot"]["sha256"],
                               "compression": saved["snapshot"].get("compression"),
                               "stored_sha256": saved["snapshot"].get("stored_sha256"),
                               "embedded_object": "hadith", "translation_field": "translationHindi"},
            "classification": saved["classification"], "related_versions": []}


def canonical_shards(rows, limit=MAX_CANONICAL_BYTES):
    """Greedily partition stable source order using actual UTF-8 JSONL bytes.

    The first material/edition keeps its existing identity. Later parts have
    deterministic suffixes. Occurrence and language-version IDs never change.
    """
    if limit < 1:
        raise ValueError("Canonical shard limit must be positive")
    result, current, encoded, size, part = [], [], [], 0, 1
    for original in rows:
        row = dict(original)
        row["edition"] = EDITION if part == 1 else EDITION + "-part-" + str(part).zfill(3)
        data = rows_bytes([row])
        if current and size + len(data) > limit:
            result.append({"part": part, "edition": current[0]["edition"], "rows": current, "data": b"".join(encoded)})
            part += 1
            current, encoded, size = [], [], 0
            row["edition"] = EDITION + "-part-" + str(part).zfill(3)
            data = rows_bytes([row])
        if len(data) > limit:
            raise ValueError("One canonical occurrence exceeds the safe shard size: " + str(row.get("id")))
        current.append(row)
        encoded.append(data)
        size += len(data)
    if current:
        result.append({"part": part, "edition": current[0]["edition"], "rows": current, "data": b"".join(encoded)})
    return result


def write_material_shard(root, slug, book, title, shard, shard_count, sources, state, inventories, coverage):
    suffix = "" if shard["part"] == 1 else "-part-" + str(shard["part"]).zfill(3)
    identifier = "deenhindi-" + slug + suffix
    directory = root / "materials" / identifier
    record_path = directory / "records.jsonl"
    atomic(record_path, shard["data"])
    numbers = {row["number"]["source_entry_id"] for row in shard["rows"]}
    sources = [source for source in sources if source["number"] in numbers]
    source_index = {"schema": "hadith-bank-html-source-index-v1", "source_site": BASE,
                    "collection": slug, "source_snapshots": sources,
                    "site_evidence": state.get("site_evidence", {}),
                    "inventory_snapshot": inventories.get(slug, {}).get("snapshot"),
                    "scope": "Exact saved public HTML responses and parsed objects; not a whole-book completion claim"}
    source_data = json_bytes(source_index)
    source_path = directory / "source-index.json"
    atomic(source_path, source_data)
    evidence_files = [item[key] for item in sources for key in ("snapshot", "parsed")]
    evidence_files.extend(state.get("site_evidence", {}).values())
    if inventories.get(slug, {}).get("snapshot"):
        evidence_files.append(inventories[slug]["snapshot"])
    supporting = {}
    for evidence in evidence_files:
        checked_bytes(root, evidence)
        path = evidence["path"]
        stored = (root / path).read_bytes()
        supporting[path] = {"path": path, "sha256": digest(stored), "size_bytes": len(stored),
                            "compression": evidence.get("compression"), "uncompressed_sha256": evidence["sha256"]}
        if evidence.get("url"):
            supporting[path]["original_response_sha256"] = evidence["sha256"]
    manifest = {"schema": "hadith-bank-material-v1", "id": identifier,
                "adapter": "records-v1", "language": "hi", "book": book, "edition": shard["edition"],
                "source_id": identifier,
                "records": {"path": record_path.relative_to(root).as_posix(), "sha256": digest(shard["data"]), "count": len(shard["rows"])},
                "source": {"path": source_path.relative_to(root).as_posix(), "sha256": digest(source_data),
                           "name": "Deen Hindi — " + title, "format": "html_snapshot_index", "url": BASE + "/hadith/" + slug},
                "publication": {"authorized": True, "decision": "owner_requested_public_pending_review",
                                "decision_date_japan": "2026-11-12", "independent_qc_asserted": False,
                                "rights_clearance_asserted": False},
                "import_coverage": coverage,
                "supporting_files": [supporting[path] for path in sorted(supporting)],
                "rights": {"status": "not_assessed_for_publication", "reuse_basis": None}}
    if shard_count > 1:
        manifest["storage_shard"] = {"part": shard["part"], "parts": shard_count,
                                     "max_canonical_bytes": MAX_CANONICAL_BYTES,
                                     "original_source_edition": EDITION,
                                     "original_source_id": "deenhindi-" + slug,
                                     "occurrence_ids_unchanged": True,
                                     "scope": "Disjoint storage part of the same source edition; not a new translation"}
    write_json(directory / "manifest.json", manifest)
    return identifier


def retire_stale_shards(root, slug, active):
    """Keep obsolete derived parts as evidence outside the active registry."""
    prefix = "deenhindi-" + slug
    candidates = [root / "materials" / prefix, *(root / "materials").glob(prefix + "-part-*")]
    for directory in candidates:
        if not directory.is_dir() or directory.name in active:
            continue
        if not re.fullmatch(re.escape(prefix) + r"(?:-part-\d{3,})?", directory.name):
            continue
        manifest = directory / "manifest.json"
        if not manifest.is_file():
            raise ValueError("Cannot retire an unrecognized incomplete material directory")
        archive = root / IMPORT / "retired-materials" / (directory.name + "-" + digest(manifest.read_bytes())[:16])
        archive.parent.mkdir(parents=True, exist_ok=True)
        if archive.exists():
            raise ValueError("Existing retired shard needs inspection before replacement: " + archive.name)
        directory.rename(archive)


def rebuild(root, state, inventories):
    overrides = load_json(root / IMPORT / "classification-overrides.json", {})
    reviews = SourceReviews(root, 'deenhindi')
    retry_summary = retry_progress(state, reviewed_error_candidates(root, state, inventories))
    reuse = ExactReviewReuse(root)

    def prepare_saved(entry):
        saved = json.loads(checked_bytes(root, entry["parsed"]))
        saved["parsed_path"] = entry["parsed"]["path"]
        checked_bytes(root, saved["snapshot"])
        saved["intake_classification"] = saved["classification"]
        override = overrides.get(entry['collection'] + ":" + entry["number"])
        if override is not None:
            if override.get("snapshot_sha256") != saved["snapshot"]["sha256"] or override.get("source_record_sha256") != digest(json_bytes(saved["source_record"])):
                raise ValueError("Classification override does not bind to the saved source")
            if override.get("classification") not in ("hadith", "unknown", "non_hadith"):
                raise ValueError("Invalid source-bound classification override")
            saved["classification"] = override
        else:
            saved["classification"] = classify(saved["source_record"])
        return saved

    # Validate the entire review set before replacing any staged/material file.
    # A late unknown ID or source mismatch must not leave earlier books partly
    # republished by a worker that subsequently records a failed stop.
    reviewed, saved_reviews, reused = {}, {}, {}
    for entry in state['imported'].values():
        identity = 'deenhindi-' + entry['collection'] + ':' + entry['number']
        if reuse.enabled:
            saved = prepare_saved(entry)
            saved_reviews[identity] = saved
            # Explicit local review decisions always take precedence. Reuse
            # cannot alter an already accepted ordinary-intake occurrence.
            if identity not in reviews.decisions and saved['classification']['classification'] == 'unknown':
                decision = reuse.review(saved)
                if decision is not None:
                    reused[identity] = decision
    reuse_receipt = reuse.prepare()
    if reuse_receipt:
        reviews.files.extend([*reuse.supporting_files(), reuse_receipt])
        for identity, decision in reused.items():
            reviews.decisions[identity] = (decision, reuse_receipt, 'register')
    for entry in state['imported'].values():
        identity = 'deenhindi-' + entry['collection'] + ':' + entry['number']
        if identity in reviews.decisions:
            saved = saved_reviews.get(identity)
            if saved is None:
                saved = prepare_saved(entry)
            saved_reviews[identity] = saved
            reviewed[identity] = reviews.apply(canonical_record(saved), saved=saved)
    reviews.finish()
    # Do not replace evidence referenced by existing material manifests until
    # every source/manual/reused decision has passed preflight validation.
    reuse.commit()
    counts, registered = {}, 0
    for slug, (book, title) in BOOKS.items():
        entries = [entry for entry in state["imported"].values() if entry["collection"] == slug]
        order = {n: i for i, n in enumerate(inventories.get(slug, {}).get("identifiers", []))}
        entries.sort(key=lambda entry: order.get(entry["number"], 10**9))
        accepted, staged, excluded, sources = [], [], [], []
        for entry in entries:
            identity = 'deenhindi-' + entry['collection'] + ':' + entry['number']
            saved = saved_reviews.get(identity)
            if saved is None:
                saved = prepare_saved(entry)
            row, decision = reviewed.get(identity, (canonical_record(saved), None))
            if decision == 'register' or (decision is None and saved["classification"]["classification"] == "hadith"):
                accepted.append(row)
                sources.append({"number": entry["number"], "snapshot": saved["snapshot"], "parsed": entry["parsed"]})
            elif decision == 'exclude':
                excluded.append(saved)
            else:
                staged.append(saved)
        counts[slug] = {"inventory": len(inventories.get(slug, {}).get("identifiers", [])),
                        "fetched": len(entries), "registered_hadith": len(accepted),
                        "classification_pending": len(staged), "non_narration_source_entries": len(excluded)}
        atomic(root / IMPORT / "staged" / (slug + ".jsonl"), rows_bytes(staged))
        atomic(root / IMPORT / "excluded" / (slug + ".jsonl"), rows_bytes(excluded))
        if not accepted:
            retire_stale_shards(root, slug, set())
            continue
        shards = canonical_shards(accepted)
        active = {write_material_shard(root, slug, book, title, shard, len(shards), sources, state, inventories, counts[slug])
                  for shard in shards}
        for material in active:
            path = root / 'materials' / material / 'manifest.json'
            manifest = load_json(path, {})
            manifest.setdefault('supporting_files', []).extend(reviews.supporting_files())
            write_json(path, manifest)
        retire_stale_shards(root, slug, active)
        registered += len(accepted)
    inventory_total = sum(len(value.get("identifiers", [])) for value in inventories.values())
    remaining = inventory_total - len(state["imported"])
    pending = max(0, remaining - len(state.get("errors", {})))
    summary = {"site": "deenhindi.com", "inventory_count": inventory_total,
               "imported_count": len(state["imported"]), "registered_hadith_count": registered,
               "classification_pending_count": sum(value['classification_pending'] for value in counts.values()),
               "non_narration_source_entries": sum(value['non_narration_source_entries'] for value in counts.values()),
               "source_review_inputs": reviews.supporting_files(),
               "source_review_engine_sha256": reviews.engine_sha256,
               "exact_field_review_reuse": {"enabled": reuse.enabled,
                    "registered_occurrences": len(reused),
                    "selected_language_fields": sum(len(d['field_reviews']) for d in reused.values()),
                    "conflicting_fields_held": len(reuse.conflicts),
                    "source_context_dependent_fields_not_reused": len(reuse.context_dependent),
                    "ledger": reuse_receipt,
                    "supporting_input_copies": reuse.supporting_files(),
                    "input_receipts": reuse.inputs},
               "remaining_count": remaining, "done": len(inventories) == len(BOOKS) and remaining == 0,
               "pending_fetch_count": pending,
               "requires_attention": bool(state.get("blocked")) or (remaining > 0 and pending == 0),
               "blocked": bool(state.get("blocked")), "block_reason": state.get("blocked"),
               "errors_count": len(state.get("errors", {})), "by_collection": counts,
               **retry_summary,
               "certified_release_eligible": False, "updated_at": now()}
    write_json(root / IMPORT / "progress.json", summary)
    return summary


def run(args):
    started = time.monotonic()
    root = args.root.resolve()
    if not (root / "AGENTS.md").is_file():
        raise ValueError("--root must point to the Hadith Bank repository")
    workspace = root / IMPORT
    state_path, inventory_path = workspace / "state.json", workspace / "inventory.json"
    state = load_json(state_path, {"schema": "deenhindi-import-state-v1", "imported": {}, "errors": {}, "site_evidence": {}})
    inventories = load_json(inventory_path, {})
    if args.max_records == 0 or state.get("blocked"):
        return rebuild(root, state, inventories)
    reviewed_retries = reviewed_error_candidates(root, state, inventories)
    fetcher = Fetcher(root, args.delay_seconds, args.timeout_seconds, started + args.max_seconds)
    attempted = 0
    budget_exhausted = False
    reviewed_retry_checkpoint = None
    try:
        # Refresh robots once per active batch, and retain every distinct version.
        robots_raw, robots_snapshot = fetcher.get(BASE + "/robots.txt")
        fetcher.robot = urllib.robotparser.RobotFileParser()
        fetcher.robot.parse(robots_raw.decode("utf-8").splitlines())
        state["site_evidence"]["robots"] = robots_snapshot
        if "about" not in state["site_evidence"]:
            _, state["site_evidence"]["about"] = fetcher.get(BASE + "/page/about-us")
        for slug in BOOKS:
            if slug not in inventories:
                if time.monotonic() - started >= args.max_seconds:
                    write_json(state_path, state)
                    summary = rebuild(root, state, inventories)
                    summary.update({"attempted_this_run": 0, "time_budget_exhausted": True})
                    return summary
                data, snapshot = fetcher.get(BASE + "/hadith/" + slug)
                inventories[slug] = {**parse_inventory(data, slug), "snapshot": snapshot}
                write_json(inventory_path, inventories)
        write_json(state_path, state)
        pending = {}
        for slug in BOOKS:
            approved, ordinary = [], []
            for number in inventories[slug]["identifiers"]:
                key = slug + ":" + number
                if key in state["imported"]:
                    continue
                if key in reviewed_retries:
                    approved.append(number)
                elif key not in state["errors"]:
                    ordinary.append(number)
                elif args.retry_errors and historical_error_class(root, key, state["errors"][key]) == "transient_fetch_error":
                    ordinary.append(number)
            # Explicit historical reviews use the same per-host request budget
            # and round-robin collection order as ordinary new source pages.
            pending[slug] = collections.deque([*approved, *ordinary])
        while attempted < args.max_records and any(pending.values()):
            for slug in BOOKS:
                if time.monotonic() - started >= args.max_seconds:
                    budget_exhausted = True
                    break
                if attempted >= args.max_records or not pending[slug]:
                    continue
                number = pending[slug].popleft()
                key = slug + ":" + number
                url = BASE + "/hadith/" + slug + "/" + urllib.parse.quote(number, safe="")
                attempted += 1
                snapshot = None
                retry_receipt = None
                retain_error_history(state, key)
                if key in reviewed_retries:
                    review = reviewed_retries[key]
                    old_receipt = state.get("reviewed_error_attempts", {}).get(review["attempt_id"])
                    retry_receipt = {"key": key, "url": url, "prepared_at": now(),
                        "authorization_consumed": True, "status": "request_prepared",
                        "manifest": review["manifest"], "decision": review["decision"],
                        "authorization_basis": review["authorization_basis"],
                        "stop_batch_after_reviewed_retry": review["stop_batch_after_reviewed_retry"],
                        "prior_error": json.loads(json_bytes(review["prior_error"]))}
                    if old_receipt:
                        retry_receipt["previous_preparations"] = [*old_receipt.get("previous_preparations", []),
                            {k: v for k, v in old_receipt.items() if k != "previous_preparations"}]
                    state.setdefault("reviewed_error_attempts", {})[review["attempt_id"]] = retry_receipt
                if key in state["errors"]:
                    # Consume before a request can leave this process. An
                    # interrupted run cannot silently replay the authorization.
                    write_json(state_path, state)
                try:
                    data, snapshot = fetcher.get(url)
                    value, citation = parse_record(data, slug, number)
                    saved = {"schema": "deenhindi-source-record-v1", "collection": slug, "number": number,
                             "snapshot": snapshot, "source_reference_verbatim": citation,
                             "source_record": value, "classification": classify(value)}
                    encoded = json_bytes(saved)
                    compressed = gzip.compress(encoded, compresslevel=9, mtime=0)
                    parsed_path = Path(IMPORT) / "parsed" / slug / (digest(encoded) + ".json.gz")
                    immutable(root / parsed_path, compressed)
                    state["imported"][key] = {"collection": slug, "number": number,
                        "parsed": {"path": parsed_path.as_posix(), "sha256": digest(encoded),
                                   "compression": "gzip", "stored_sha256": digest(compressed)}}
                    state["errors"].pop(key, None)
                    if retry_receipt is not None:
                        retry_receipt.update(status="succeeded", finished_at=now(),
                            response_snapshot=snapshot, parsed=state["imported"][key]["parsed"])
                except Halt as error:
                    if retry_receipt is not None:
                        retry_receipt.update(status="blocked", finished_at=now(), error=str(error),
                                             response_snapshot=error.snapshot)
                    raise
                except BudgetExpired:
                    if retry_receipt is not None:
                        # Fetcher raises this exception only before urlopen;
                        # there is positive evidence that no request was sent.
                        retry_receipt.update(status="not_requested_deadline", finished_at=now(),
                                             authorization_consumed=False)
                    raise
                except (OSError, ValueError, urllib.error.URLError) as error:
                    state["errors"][key] = {"url": url, "error": str(error), "at": now(), "snapshot": snapshot,
                        "error_type": type(error).__name__,
                        "http_status": error.code if isinstance(error, urllib.error.HTTPError) else None}
                    if retry_receipt is not None:
                        retry_receipt.update(status="failed", finished_at=now(), error=state["errors"][key])
                write_json(state_path, state)
                if retry_receipt is not None and reviewed_retries[key]["stop_batch_after_reviewed_retry"]:
                    # A pilot outcome must reach the existing rebuild/save path
                    # before ordinary acquisition continues. Consumed receipts
                    # are excluded next run, so this does not cap later batches.
                    reviewed_retry_checkpoint = key
                    break
            # Source checkpoints are durable after every record. Regenerate
            # canonical shards once at batch completion, avoiding a whole-bank
            # rewrite after every seven new pages as the collection grows.
            if budget_exhausted or reviewed_retry_checkpoint is not None:
                break
    except BudgetExpired:
        budget_exhausted = True
        write_json(state_path, state)
    except Halt as error:
        state["blocked"] = {"reason": str(error), "at": now(), "automatic_retry_allowed": False}
        if error.snapshot is not None:
            state["blocked"]["snapshot"] = error.snapshot
        write_json(state_path, state)
    summary = rebuild(root, state, inventories)
    summary["attempted_this_run"] = attempted
    summary["time_budget_exhausted"] = budget_exhausted
    summary["reviewed_retry_checkpoint"] = reviewed_retry_checkpoint
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--max-records", type=int, default=21, help="Maximum new record requests in this batch; zero rebuilds saved data offline")
    parser.add_argument("--delay-seconds", type=float, default=1.25, help="Minimum pause after each response, including failures")
    parser.add_argument("--timeout-seconds", type=float, default=30)
    parser.add_argument("--max-seconds", type=float, default=600, help="Gracefully checkpoint when this elapsed-time budget is reached; one in-flight request may finish")
    parser.add_argument("--retry-errors", action="store_true", help="Retry only classified transient transport/HTTP failures; historical verification or parser responses require the exact reviewed-error manifest. Never overrides a persisted access stop")
    args = parser.parse_args()
    if args.max_records < 0 or args.delay_seconds < 0.5 or args.timeout_seconds <= 0 or args.max_seconds <= 0:
        parser.error("Nonnegative record budget, delay >= 0.5 seconds and positive time budgets required")
    try:
        with importer_lock(args.root):
            summary = run(args)
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(json.dumps({"site": "deenhindi.com", "error": str(error), "done": False}, ensure_ascii=False))
        return 1
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 2 if summary.get("blocked") else 0


if __name__ == "__main__":
    raise SystemExit(main())
