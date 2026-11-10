#!/usr/bin/env python3
"""Search a private attachment intake offline, without changing source records.

The root must contain a hadith-bank-attachment-collections-v1 collections.json.
Only local, checksum-verified JSON arrays are read. Filters are exact metadata
matches; query words are ANDed, case/width folded, and searched in source text,
titles, references, narrator information, and explicit book/tag metadata.
Arabic vocalization marks and CJK line wraps are ignored for matching only.
--include-commentary also searches and returns commentary and footnotes.

Python API: search(root, query='', *, language=None, book=None, edition=None,
entry_id=None, tag=None, kind=None, limit=10, include_commentary=False).
The return value contains matched, shown, verified_collections, and results.
Each result preserves verbatim text and metadata, with its own authorship and
review warning. This utility performs no translation, classification, network
access, canonical alignment, merging, or publication.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata


INDEX_SCHEMA = "hadith-bank-attachment-collections-v1"
RESULT_SCHEMA = "hadith-bank-attachment-search-v1"
LANGUAGE_ALIASES = {"zh": "zh-CN", "tl": "fil"}
WARNING = (
    "Private attachment intake. Independent Pro QC and release status are "
    "reported per record; pending review is not cleared by this search. "
    "Search is not publication approval. AI-translation flags vary by record."
)
_HEX_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
_CJK = "\\u3040-\\u30ff\\u3400-\\u9fff\\uf900-\\ufaff"
_CJK_SPACING = re.compile(r"(?<=[" + _CJK + r"])\s+(?=[" + _CJK + r"])")
_OUTPUT_FIELDS = (
    "id", "record_id", "source_entry_id", "provider_entry_id", "language", "source_language_code", "record_type",
    "content_kind", "source_record_type", "subtype", "title", "text", "book",
    "number", "narrator", "source", "translator", "page", "references",
    "grading", "ai_translation", "review", "source_structure_tags",
    "topic_tags", "editorial_tags",
)


def _language(value):
    if value is not None and not isinstance(value, str):
        raise ValueError("language must be a string or null")
    return LANGUAGE_ALIASES.get(value, value)


def _component(value, field):
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or any(c in value for c in "/\\:\x00")
        or any(ord(c) < 32 for c in value)
    ):
        raise ValueError("Invalid collection " + field + " path component")
    return value


def _local_path(root, relative):
    """Reject noncanonical relative paths and resolved escapes, including links."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Unsafe local collection path")
    path = PurePosixPath(relative)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != relative
        or any(":" in part or "\x00" in part for part in path.parts)
    ):
        raise ValueError("Unsafe local collection path")
    resolved = root.joinpath(*path.parts).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Unsafe local collection path: resolved outside root") from exc
    return resolved


def _load_index(root):
    index_path = _local_path(root, "collections.json")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(index, dict) or index.get("schema") != INDEX_SCHEMA:
        raise ValueError("Unsupported attachment collections schema")
    collections = index.get("collections")
    if not isinstance(collections, list):
        raise ValueError("collections must be a JSON array")
    checked = []
    paths = set()
    for collection in collections:
        if not isinstance(collection, dict):
            raise ValueError("Each collection must be a JSON object")
        language = _component(collection.get("language"), "language")
        book = _component(collection.get("book"), "book")
        edition = _component(collection.get("edition"), "edition")
        relative = collection.get("records_path")
        path = _local_path(root, relative)
        expected = (
            f"languages/{language}/books/{book}/editions/{edition}/records.json"
        )
        if relative != expected:
            raise ValueError("Collection path does not match language/book/edition")
        if relative in paths:
            raise ValueError("Duplicate records_path in collections index")
        paths.add(relative)
        digest = collection.get("records_sha256")
        if not isinstance(digest, str) or not _HEX_SHA256.fullmatch(digest):
            raise ValueError("Collection records_sha256 must be 64 hexadecimal digits")
        count = collection.get("count")
        if type(count) is not int or count < 0:
            raise ValueError("Collection count must be a nonnegative integer")
        checked.append((collection, path))
    return checked


def _records(collection, path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != collection["records_sha256"].lower():
        raise ValueError("SHA-256 mismatch: " + collection["records_path"])
    records = json.loads(data.decode("utf-8"))
    if not isinstance(records, list):
        raise ValueError("records.json must contain a JSON array")
    if len(records) != collection["count"]:
        raise ValueError("Record count mismatch: " + collection["records_path"])
    return records


def _validate_record(item, collection):
    if not isinstance(item, dict):
        raise ValueError("Each narration record must be a JSON object")
    record_id = item.get("id")
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("Record id must be a nonempty string")
    if item.get("record_id") != record_id:
        raise ValueError("Record id and record_id disagree: " + record_id)
    if _language(item.get("language")) != _language(collection["language"]):
        raise ValueError("Record language disagrees with collection: " + record_id)
    texts = item.get("text")
    if not isinstance(texts, dict) or any(
        field not in texts or (texts[field] is not None and not isinstance(texts[field], str))
        for field in ("arabic", "translation")
    ):
        raise ValueError("Record text requires Arabic/translation strings or null: " + record_id)
    flag = item.get("ai_translation")
    if type(flag) is not bool and flag != "unknown":
        raise ValueError("Invalid ai_translation flag: " + record_id)
    if not isinstance(item.get("review"), dict):
        raise ValueError("Record review must be an object: " + record_id)


def _strings(value):
    """Yield values only, never search JSON field names or invented labels."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)
    elif type(value) in (int, float):
        yield str(value)


def _fold(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    value = "".join(
        char for char in value
        if char != "\u0640" and not (
            unicodedata.category(char).startswith("M")
            and ("\u0610" <= char <= "\u061a"
                 or "\u064b" <= char <= "\u065f"
                 or char == "\u0670"
                 or "\u06d6" <= char <= "\u06ed")
        )
    )
    return " ".join(_CJK_SPACING.sub("", value).split())


def _id_values(item):
    # Only explicit identity/source-number fields, never guessed canonical IDs.
    yield item.get("id")
    yield item.get("record_id")
    yield item.get("source_entry_id")
    yield item.get("provider_entry_id")
    number = item.get("number")
    if isinstance(number, dict):
        yield number.get("in_book")
        yield number.get("source_entry_id")
        yield number.get("provider_entry_id")
        yield number.get("provider_entry_number")
    source = item.get("source")
    if isinstance(source, dict):
        yield source.get("entry_id")
        yield source.get("source_entry_id")
        yield source.get("provider_entry_id")


def _matches_id(item, requested):
    return any(
        type(value) in (str, int) and str(value) == str(requested)
        for value in _id_values(item)
    )


def _tag_values(item):
    editorial = item.get("editorial_tags")
    if isinstance(editorial, dict) and isinstance(editorial.get("values"), list):
        yield from editorial["values"]
    for field in ("source_structure_tags", "topic_tags"):
        tags = item.get(field)
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict):
                    yield tag.get("tag_id")
                    yield tag.get("value_verbatim")


def _searchable(item, include_commentary):
    fields = ("text", "title", "narrator", "references", "book", "number")
    parts = [text for field in fields for text in _strings(item.get(field))]
    parts.extend(tag for tag in _tag_values(item) if isinstance(tag, str))
    if include_commentary:
        for field in ("commentary", "footnotes"):
            parts.extend(_strings(item.get(field)))
    return _fold("\n".join(parts))


def _record_warning(item):
    flag = item["ai_translation"]
    if flag is True:
        authorship = "ai_translation=true: this record is labeled as an AI translation."
    elif flag is False:
        authorship = "ai_translation=false: this record is labeled as a human translation."
    else:
        authorship = "ai_translation=unknown: authorship is not established for this record."
    review = item["review"]
    qc = review.get("independent_pro_qc", "not documented")
    release = review.get("release_status", "not documented")
    eligible = json.dumps(review.get("release_eligible"), ensure_ascii=False)
    return (
        f"{authorship} Independent Pro QC: {qc}. "
        f"Release status: {release}; release_eligible={eligible}. "
        "Search is not publication approval."
    )


def _result(item, collection, include_commentary):
    result = {key: item[key] for key in _OUTPUT_FIELDS if key in item}
    if include_commentary:
        result["commentary"] = item.get("commentary")
        result["footnotes"] = item.get("footnotes")
    result["collection"] = {
        key: collection.get(key) for key in (
            "language", "source_language_code", "book", "edition",
            "records_path", "records_sha256",
        )
    }
    result["warning"] = _record_warning(item)
    return result


def search(root, query="", *, language=None, book=None, edition=None,
           entry_id=None, tag=None, kind=None, limit=10, include_commentary=False):
    """Return all-match counts and up to limit verbatim, independently kept records.

    SHA-256/count checks cover every collection selected by language/book/edition,
    even when limit is zero. Paths for the entire manifest are checked. Result
    order follows the manifest and source arrays. No occurrences are deduplicated.
    Raises OSError or ValueError for unsafe, missing, malformed or altered input.
    """
    if type(limit) is not int or limit < 0:
        raise ValueError("limit must be a nonnegative integer")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    root = Path(root).resolve()
    language = _language(language)
    terms = [_fold(word) for word in query.split()]
    results = []
    verified = []
    seen_ids = set()
    matched = 0
    for collection, path in _load_index(root):
        if language is not None and _language(collection["language"]) != language:
            continue
        if book is not None and collection["book"] != book:
            continue
        if edition is not None and collection["edition"] != edition:
            continue
        records = _records(collection, path)
        verified.append({
            key: collection.get(key) for key in (
                "language", "source_language_code", "book", "edition",
                "records_path", "records_sha256", "count",
            )
        })
        for item in records:
            _validate_record(item, collection)
            if item["id"] in seen_ids:
                raise ValueError("Duplicate occurrence id in selected collections: " + item["id"])
            seen_ids.add(item["id"])
            if entry_id is not None and not _matches_id(item, entry_id):
                continue
            if tag is not None and not any(value == tag for value in _tag_values(item)):
                continue
            if kind is not None and kind not in (item.get("record_type"), item.get("content_kind")):
                continue
            if terms:
                searchable = _searchable(item, include_commentary)
                if not all(term in searchable for term in terms):
                    continue
            matched += 1
            if len(results) < limit:
                results.append(_result(item, collection, include_commentary))
    return {
        "schema": RESULT_SCHEMA,
        "matched": matched,
        "shown": len(results),
        "limit": limit,
        "warning": WARNING,
        "filters": {
            "query": query, "language": language, "book": book, "edition": edition,
            "id": entry_id, "tag": tag, "kind": kind,
            "include_commentary": include_commentary,
        },
        "verified_collections": verified,
        "results": results,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="private attachment candidate root")
    parser.add_argument("query", nargs="?", default="", help="AND search terms (quote multiword queries)")
    parser.add_argument("--language", help="bank language code; zh aliases zh-CN and tl aliases fil")
    parser.add_argument("--book", help="exact collection book code")
    parser.add_argument("--edition", help="exact collection edition snapshot")
    parser.add_argument("--id", dest="entry_id", help="exact occurrence ID or explicit source entry number")
    parser.add_argument("--tag", help="exact editorial tag, source heading text, or structure/topic tag ID")
    parser.add_argument("--kind", help="exact explicit record_type or content_kind; no inferred classification")
    parser.add_argument("--limit", type=int, default=10, help="maximum displayed results; 0 counts only")
    parser.add_argument("--include-commentary", action="store_true", help="search and return commentary and footnotes")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = search(**vars(args))
    except (OSError, ValueError, RuntimeError) as exc:
        print("Search failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
