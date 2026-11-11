#!/usr/bin/env python3
"""Restore an already extracted book from its exact preserved transport bytes.

No OCR, extraction, translation, text normalization, or review is performed.
All inputs are verified before any canonical file is installed. The pinned
manifest identifies the owner-authorized package; it is not a generic importer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile

MATERIAL = "materials/zh-cn-ibn-majah-yu-2013"
TRANSPORT = "imports/chinese-ibn-majah-20261111/transport"
MANIFEST = f"{TRANSPORT}/manifest.json"
MANIFEST_SHA256 = "006840640ce73ef6d106af0812a03fabf67dfeed659d5dce90ca69bc01b4fa97"
ARCHIVE_SHA256 = "0f5dbb3848a6c7a2d5bd4ec95d911b7380c4195584bf1189d955e83a780e31d7"
ARCHIVE_SIZE = 34527778
REPORT = "reports/chinese-ibn-majah-transport.json"
RECORD_COUNT, CHAPTER_COUNT, FILE_COUNT, PART_COUNT = 4354, 39, 94, 66
CHUNK = 1024 * 1024


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def safe_relative(name: str) -> PurePosixPath:
    require(isinstance(name, str) and bool(name), "Empty or non-text path")
    require("\\" not in name and "\x00" not in name, "Invalid path characters")
    require(not name.startswith("/"), "Absolute path rejected")
    require(all(p not in ("", ".", "..") for p in name.split("/")),
            "Noncanonical or traversal path rejected")
    return PurePosixPath(name)


def checked_path(root: Path, name: str) -> Path:
    relative = safe_relative(name)
    candidate = root
    for part in relative.parts:
        candidate /= part
        require(not candidate.is_symlink(), "Symlink path rejected")
    require(candidate.resolve().is_relative_to(root.resolve()),
            "Path escapes repository")
    return candidate


def digest_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_file(path: Path, spec: dict, description: str) -> None:
    require(path.is_file() and not path.is_symlink(), f"Missing {description}")
    require(path.stat().st_size == spec["size"], f"Wrong size: {description}")
    require(digest_file(path) == spec["sha256"], f"Hash mismatch: {description}")


def load_manifest(root: Path) -> dict:
    raw = checked_path(root, MANIFEST).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256,
            "Transport manifest differs from the preserved package")
    data = json.loads(raw)
    require(data["version"] == 1, "Unsupported transport manifest")
    require(data["archive"] == {
        "format": "tar.gz", "size": ARCHIVE_SIZE, "sha256": ARCHIVE_SHA256
    }, "Unexpected archive identity")
    require(len(data["parts"]) == PART_COUNT, "Wrong number of parts")
    require(len(data["files"]) == FILE_COUNT, "Wrong number of canonical files")
    require(data["record_count"] == RECORD_COUNT and
            data["chapter_count"] == CHAPTER_COUNT, "Unexpected source counts")
    seen = set()
    for index, item in enumerate(data["parts"]):
        require(item["path"] == f"{TRANSPORT}/part-{index:05d}.bin",
                "Unexpected part order or path")
    for item in data["parts"] + data["files"]:
        safe_relative(item["path"])
        require(item["path"] not in seen, "Duplicate manifest path")
        seen.add(item["path"])
        require(type(item["size"]) is int and item["size"] >= 0, "Invalid size")
        require(re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None,
                "Invalid SHA-256")
    require(all(item["path"].startswith(MATERIAL + "/")
                for item in data["files"]), "File outside the authorized material")
    return data


def assemble_archive(root: Path, manifest: dict, output: Path) -> None:
    """Fail on a missing/corrupt part; never concatenate an unverified part."""
    with output.open("xb") as target:
        for spec in manifest["parts"]:
            source = checked_path(root, spec["path"])
            verify_file(source, spec, spec["path"])
            with source.open("rb") as handle:
                shutil.copyfileobj(handle, target, CHUNK)
    verify_file(output, manifest["archive"], "complete archive")


def stage_archive(archive: Path, specs: list[dict], stage: Path) -> None:
    """Inspect every archive member before writing any extracted file."""
    expected = {item["path"]: item for item in specs}
    require(len(expected) == len(specs), "Duplicate expected canonical path")
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        seen = set()
        for member in members:
            safe_relative(member.name)
            require(member.name.startswith(MATERIAL + "/"),
                    "Archive member outside authorized material")
            require(member.name not in seen, "Duplicate archive member")
            seen.add(member.name)
            require(member.name in expected, "Unlisted archive member")
            require(member.isfile() and not member.issym() and
                    not member.islnk() and not member.sparse,
                    "Nonregular archive member rejected")
            require(member.size == expected[member.name]["size"],
                    "Archive member has wrong size")
        require(seen == set(expected), "Missing canonical archive member")
        for member in members:
            target = checked_path(stage, member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = source.extractfile(member)
            require(handle is not None, "Unreadable archive member")
            with handle, target.open("xb") as destination:
                shutil.copyfileobj(handle, destination, CHUNK)
            verify_file(target, expected[member.name], member.name)


def check_material(stage: Path, manifest: dict) -> dict:
    material = json.loads(checked_path(stage, f"{MATERIAL}/manifest.json").read_text())
    require(material["id"] == "zh-cn-ibn-majah-yu-2013", "Wrong material identity")
    require(material["publication"]["authorized"] is True, "Publication not authorized")
    specs = {item["path"]: item for item in manifest["files"]}
    for key in ("source", "records"):
        identity = material[key]
        require(identity["path"] in specs, f"Unlisted {key} file")
        require(identity["sha256"] == specs[identity["path"]]["sha256"],
                f"Material {key} hash differs from transport manifest")
    require(material["records"]["count"] == RECORD_COUNT, "Wrong material record count")
    ids, chapters = set(), set()
    with checked_path(stage, material["records"]["path"]).open(encoding="utf-8") as handle:
        for line in handle:
            require(bool(line.strip()), "Empty canonical record line")
            record = json.loads(line)
            occurrence_id = record.get("id")
            require(isinstance(occurrence_id, str) and bool(occurrence_id), "Missing record ID")
            require(occurrence_id not in ids, "Duplicate canonical record ID")
            ids.add(occurrence_id)
            chapter = record["number"]["chapter"]
            require(type(chapter) is int, "Invalid chapter value")
            chapters.add(chapter)
    require(len(ids) == RECORD_COUNT, "Wrong canonical record count")
    require(chapters == set(range(1, CHAPTER_COUNT + 1)), "Wrong chapter coverage")
    return {
        "record_count": len(ids), "unique_record_ids": len(ids),
        "chapter_count": len(chapters), "source_sha256": material["source"]["sha256"],
        "records_sha256": material["records"]["sha256"],
    }


def install_files(root: Path, stage: Path, specs: list[dict]) -> None:
    # Check all existing targets before writing. Conflicting files are preserved.
    for spec in specs:
        target = checked_path(root, spec["path"])
        if target.exists():
            verify_file(target, spec, "existing " + spec["path"])
    for spec in specs:
        target = checked_path(root, spec["path"])
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        checked_path(root, spec["path"])
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            name = Path(temporary.name)
            try:
                with checked_path(stage, spec["path"]).open("rb") as source:
                    shutil.copyfileobj(source, temporary, CHUNK)
                temporary.flush()
                os.fsync(temporary.fileno())
            except BaseException:
                name.unlink(missing_ok=True)
                raise
        try:
            verify_file(name, spec, spec["path"])
            require(not target.exists(), "Target appeared during restoration")
            name.replace(target)
        finally:
            name.unlink(missing_ok=True)


def restore(root: Path, dry_run: bool = False) -> dict:
    root = root.resolve()
    manifest = load_manifest(root)
    with tempfile.TemporaryDirectory(prefix="hadith-ibn-restore-") as temporary:
        work = Path(temporary)
        archive, stage = work / "package.tar.gz", work / "staged"
        stage.mkdir()
        assemble_archive(root, manifest, archive)
        stage_archive(archive, manifest["files"], stage)
        details = check_material(stage, manifest)
        result = {
            "schema": "hadith-bank-transport-integrity-v1",
            "material_id": "zh-cn-ibn-majah-yu-2013",
            "status": "verified" if dry_run else "restored",
            "archive_sha256": ARCHIVE_SHA256,
            "archive_size": ARCHIVE_SIZE,
            "verified_parts": len(manifest["parts"]),
            "verified_files": len(manifest["files"]),
            **details,
            "source_text_modified": False,
            "new_extraction_performed": False,
            "independent_qc_performed": False,
        }
        if not dry_run:
            install_files(root, stage, manifest["files"])
            report = checked_path(root, REPORT)
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = restore(args.root, args.dry_run)
    except (ValueError, OSError, KeyError, TypeError, tarfile.TarError) as exc:
        # Concise errors only; source payloads are never logged.
        print(json.dumps({"status": "failed", "error": str(exc)[:300]}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
