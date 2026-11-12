"""Assemble hash-pinned Fawaz review inputs without changing source decisions.

The baseline catalog remains authoritative and immutable. A recovered catalog
may repeat its decisions only when each full JSON value is identical. Phase
archive decisions must be disjoint from that recovered catalog. This module
checks transport, provenance headers and identity; the existing source audit
must still validate quotation hashes, spans and exported material preservation.
"""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile


CATALOG_SCHEMA = "hadith-bank-fawaz-reviewed-spans-v1"
INPUT_SCHEMA = "hadith-bank-fawaz-compressed-review-inputs-v1"
ARCHIVE_SCHEMA = "hadith-bank-frozen-rereview-input-checkpoint-v1"
BASELINE_PATH = "catalog/fawaz-reviewed-spans.json"
MANIFEST_PATH = "catalog/fawaz-review-inputs.json"
LIST_SCHEMAS = {
    CATALOG_SCHEMA,
    "hadith-bank-source-bound-fresh-review-v1",
    "fawaz-source-bound-expanded-reports-review-v1",
}
SINGLE_SCHEMA = "hadith-bank-recovered-exact-review-evidence-v1"
AUDIT_SCHEMA = "hadith-bank-fawaz-exact-empty-audit-v1"
MAX_STORED_BYTES = 32 * 1024 * 1024
MAX_RAW_BYTES = 128 * 1024 * 1024
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_MEMBERS = 1000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def json_bytes(value):
    """Canonical UTF-8 representation; no timestamps or absolute local paths."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def gzip_bytes(value):
    """Deterministic gzip header, including an empty original filename."""
    result = io.BytesIO()
    with gzip.GzipFile(fileobj=result, mode="wb", filename="", mtime=0,
                       compresslevel=9) as stream:
        stream.write(value)
    return result.getvalue()


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-finite JSON number: " + value)


def _json(raw, label):
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                           parse_constant=_reject_constant)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("Invalid JSON in " + label + ": " + str(exc)) from exc
    require(isinstance(value, dict), "Expected a JSON object in " + label)
    return value


def _relative(value):
    require(isinstance(value, str) and bool(value), "Missing relative input path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and "\\" not in value and ":" not in value
            and "\0" not in value and all(part not in ("", ".", "..")
                                          for part in value.split("/")),
            "Unsafe relative input path: " + value)
    return path


def _path(root, value):
    relative = _relative(value)
    result = root.joinpath(*relative.parts)
    require(result.resolve().is_relative_to(root.resolve()),
            "Input path escapes the repository: " + value)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), "Symlink input path: " + value)
    return result


def _size(value, limit, label):
    require(type(value) is int and 0 <= value <= limit,
            "Invalid or excessive byte count for " + label)
    return value


def _digest(value, label):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value),
            "Invalid SHA-256 for " + label)
    return value


def _read(path, limit, label):
    require(path.is_file(), "Missing input file: " + label)
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "Input exceeds size limit: " + label)
    return raw


def _verified(root, spec, limit):
    require(isinstance(spec, dict), "Missing input descriptor")
    label = spec.get("path")
    path = _path(root, label)
    size = _size(spec.get("bytes"), limit, label)
    digest = _digest(spec.get("sha256"), label)
    raw = _read(path, limit, label)
    require(len(raw) == size, "Input byte count changed: " + label)
    require(sha256(raw) == digest, "Input SHA-256 changed: " + label)
    return raw


def _identity(decision):
    require(isinstance(decision, dict), "A decision must be a JSON object")
    book, edition, number = (decision.get(name) for name in
                             ("provider_book", "provider_edition", "typed_hadithnumber"))
    require(all(isinstance(value, str) and value for value in (book, edition, number)),
            "A decision has incomplete typed provider identity")
    require("-" in edition, "A decision edition lacks its language prefix")
    # Match the existing importer exactly, without changing the stored edition.
    return book, edition.split("-", 1)[0], number


def _index(decisions, label):
    require(isinstance(decisions, list), "Missing decision list: " + label)
    result = {}
    for decision in decisions:
        key = _identity(decision)
        require(key not in result, "Repeated decision identity in " + label + ": " + repr(key))
        result[key] = decision
    return result


def _header(value, repository, revision, schema, label):
    require(value.get("schema") == schema and value.get("repository") == repository
            and value.get("revision") == revision,
            "Schema or pinned provider repository/revision mismatch: " + label)


def _archive_inventory(stored, manifest_spec):
    """Read each tar member as a stream, with no filesystem extraction."""
    manifest_name = manifest_spec.get("path")
    _relative(manifest_name)
    expected_size = _size(manifest_spec.get("bytes"), MAX_MEMBER_BYTES, manifest_name)
    expected_hash = _digest(manifest_spec.get("sha256"), manifest_name)
    members, total, manifest_raw = {}, 0, None
    with tarfile.open(fileobj=io.BytesIO(stored), mode="r|gz") as archive:
        for member in archive:
            _relative(member.name)
            require(member.name not in members, "Repeated tar member path: " + member.name)
            require(member.isfile(), "Only regular tar members are allowed: " + member.name)
            _size(member.size, MAX_MEMBER_BYTES, member.name)
            total += member.size
            require(total <= MAX_RAW_BYTES and len(members) < MAX_MEMBERS,
                    "Archive exceeds its expanded size/member limit")
            stream = archive.extractfile(member)
            require(stream is not None, "Unreadable archive member: " + member.name)
            digest, count, chunks = hashlib.sha256(), 0, []
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                count += len(chunk)
                require(count <= member.size, "Tar member exceeds its declared size")
                digest.update(chunk)
                if member.name == manifest_name:
                    chunks.append(chunk)
            require(count == member.size, "Truncated archive member: " + member.name)
            members[member.name] = {"bytes": count, "sha256": digest.hexdigest()}
            if member.name == manifest_name:
                manifest_raw = b"".join(chunks)
    require(manifest_raw is not None, "Archive manifest is missing")
    require(len(manifest_raw) == expected_size and sha256(manifest_raw) == expected_hash,
            "Archive manifest checksum or size mismatch")
    manifest = _json(manifest_raw, manifest_name)
    require(manifest.get("schema") == ARCHIVE_SCHEMA, "Unsupported archive manifest schema")
    require(isinstance(manifest.get("files"), list), "Archive file inventory is missing")
    listed = {}
    for spec in manifest["files"]:
        require(isinstance(spec, dict), "Invalid archive input descriptor")
        name = spec.get("path")
        _relative(name)
        require(name not in listed and name != manifest_name, "Repeated archive input: " + name)
        size = _size(spec.get("bytes"), MAX_MEMBER_BYTES, name)
        digest = _digest(spec.get("sha256"), name)
        require(members.get(name) == {"bytes": size, "sha256": digest},
                "Missing or changed listed archive input: " + name)
        count = spec.get("decisions")
        require(type(count) is int and count >= 0, "Missing observed decision count: " + name)
        listed[name] = spec
    require(all(name == manifest_name or name in listed or not name.endswith(".json")
                for name in members), "Archive contains an unlisted JSON review input")
    return manifest, listed


def _archive_decisions(stored, listed, repository, revision):
    documents = {}
    with tarfile.open(fileobj=io.BytesIO(stored), mode="r|gz") as archive:
        for member in archive:
            if member.name not in listed:
                continue
            value = _json(archive.extractfile(member).read(member.size + 1), member.name)
            for field, expected in (("repository", repository), ("revision", revision),
                                    ("source_revision", revision)):
                require(field not in value or value[field] == expected,
                        "Pinned source mismatch in " + member.name + ": " + field)
            schema = value.get("schema")
            if schema in LIST_SCHEMAS:
                require("decision" not in value, "Ambiguous decision container")
                decisions = value.get("decisions")
            elif schema == SINGLE_SCHEMA:
                require("decisions" not in value and isinstance(value.get("decision"), dict),
                        "Malformed single-decision evidence")
                decisions = [value["decision"]]
            elif schema == AUDIT_SCHEMA:
                require("decision" not in value and "decisions" not in value,
                        "Audit-only input contains unlisted decisions")
                decisions = []
            else:
                raise ValueError("Unsupported review input schema: " + member.name)
            _index(decisions, member.name)
            require(len(decisions) == listed[member.name]["decisions"],
                    "Observed decision count changed: " + member.name)
            documents[member.name] = decisions
    return [decision for name in listed for decision in documents[name]]


def load_review_catalog(root, *, repository, revision,
                        manifest_path=MANIFEST_PATH, baseline_path=BASELINE_PATH):
    """Return the existing catalog or an additive, verified input assembly."""
    root = Path(root)
    manifest_file = _path(root, manifest_path)
    baseline_file = _path(root, baseline_path)
    if not manifest_file.exists():
        if not baseline_file.exists():
            return None
        baseline = _json(_read(baseline_file, MAX_RAW_BYTES, baseline_path), baseline_path)
        _header(baseline, repository, revision, CATALOG_SCHEMA, baseline_path)
        _index(baseline.get("decisions"), baseline_path)
        return baseline
    manifest_raw = _read(manifest_file, MAX_MEMBER_BYTES, manifest_path)
    manifest = _json(manifest_raw, manifest_path)
    _header(manifest, repository, revision, INPUT_SCHEMA, manifest_path)
    require(manifest.get("baseline", {}).get("path") == baseline_path,
            "Supplemental input manifest changed the baseline catalog path")
    baseline_raw = _verified(root, manifest["baseline"], MAX_RAW_BYTES)
    baseline = _json(baseline_raw, baseline_path)
    _header(baseline, repository, revision, CATALOG_SCHEMA, baseline_path)
    baseline_decisions = _index(baseline.get("decisions"), baseline_path)

    recovered_spec = manifest.get("recovered_catalog")
    recovered_stored = _verified(root, recovered_spec, MAX_STORED_BYTES)
    raw_size = _size(recovered_spec.get("raw_bytes"), MAX_RAW_BYTES, "recovered catalog")
    raw_digest = _digest(recovered_spec.get("raw_sha256"), "recovered catalog")
    with gzip.GzipFile(fileobj=io.BytesIO(recovered_stored), mode="rb") as stream:
        recovered_raw = stream.read(raw_size + 1)
    require(len(recovered_raw) == raw_size and sha256(recovered_raw) == raw_digest,
            "Recovered catalog expanded checksum or size mismatch")
    recovered = _json(recovered_raw, recovered_spec["path"])
    _header(recovered, repository, revision, CATALOG_SCHEMA, recovered_spec["path"])
    recovered_decisions = _index(recovered.get("decisions"), recovered_spec["path"])
    for key, previous in baseline_decisions.items():
        require(key in recovered_decisions, "Recovered catalog removed baseline decision: " + repr(key))
        require(json_bytes(previous) == json_bytes(recovered_decisions[key]),
                "Recovered catalog changed baseline decision: " + repr(key))

    archive_spec = manifest.get("phase_archive")
    stored_archive = _verified(root, archive_spec, MAX_STORED_BYTES)
    archive_manifest, listed = _archive_inventory(stored_archive, archive_spec.get("manifest", {}))
    additional = _archive_decisions(stored_archive, listed, repository, revision)
    additional_index = _index(additional, archive_spec["path"])
    overlap = set(additional_index) & set(recovered_decisions)
    require(not overlap, "Supplemental decisions repeat a recovered identity: "
            + repr(sorted(overlap)[:1]))
    result = dict(recovered)
    result["decisions"] = recovered["decisions"] + additional
    known = set(recovered_decisions) | set(additional_index)
    fresh_specs = manifest.get("additional_reviews", [])
    require(isinstance(fresh_specs, list), "Additional review descriptors must be a list")
    fresh_paths, fresh_count = set(), 0
    for spec in fresh_specs:
        require(isinstance(spec, dict), "Malformed additional review descriptor")
        name = spec.get("path")
        require(isinstance(name, str) and name not in fresh_paths,
                "Repeated additional review input path")
        fresh_paths.add(name)
        stored = _verified(root, spec, MAX_STORED_BYTES)
        require(spec.get("compression") == "gzip", "Additional review input must use gzip")
        size = _size(spec.get("raw_bytes"), MAX_RAW_BYTES, name)
        digest = _digest(spec.get("raw_sha256"), name)
        with gzip.GzipFile(fileobj=io.BytesIO(stored), mode="rb") as stream:
            raw = stream.read(size + 1)
        require(len(raw) == size and sha256(raw) == digest,
                "Additional review expanded checksum or size mismatch: " + name)
        document = _json(raw, name)
        _header(document, repository, revision, CATALOG_SCHEMA, name)
        decisions = _index(document.get("decisions"), name)
        require(not (known & decisions.keys()),
                "Additional review repeats a previously decided identity: " + name)
        known.update(decisions)
        result["decisions"].extend(document["decisions"])
        fresh_count += len(decisions)
    result["compressed_input_assembly"] = {
        "schema": "hadith-bank-fawaz-review-input-assembly-v1",
        "manifest_path": manifest_path,
        "manifest_sha256": sha256(manifest_raw),
        "baseline": manifest["baseline"],
        "recovered_catalog": recovered_spec,
        "phase_archive": archive_spec,
        "baseline_decisions_preserved": len(baseline_decisions),
        "recovered_decisions": len(recovered_decisions),
        "additional_decisions": len(additional),
        "additional_reviews": fresh_specs,
        "fresh_decisions": fresh_count,
        "total_decisions": len(result["decisions"]),
        "scope": "Exact saved decisions assembled; source-span validation, exported quotation preservation and publication remain separate checks.",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--manifest", default=MANIFEST_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = load_review_catalog(args.root, repository=args.repository,
                                 revision=args.revision, manifest_path=args.manifest)
    require(result is not None, "No source review catalog was found")
    raw = json_bytes(result)
    summary = {"decisions": len(result["decisions"]), "raw_bytes": len(raw),
               "raw_sha256": sha256(raw)}
    if args.output:
        stored = gzip_bytes(raw) if args.output.suffix == ".gz" else raw
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_bytes(stored)
        temporary.replace(args.output)
        summary.update(output=str(args.output), stored_bytes=len(stored), stored_sha256=sha256(stored))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
