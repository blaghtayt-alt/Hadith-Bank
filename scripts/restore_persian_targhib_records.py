#!/usr/bin/env python3
"""Restore three exact preserved JSONL files from their verified gzip transport.

This only reverses lossless transfer compression. It does not extract, alter,
translate, review, or certify a narration. Existing differing files are errors.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import zlib


TRANSPORT = 'imports/persian-targhib-20261111/transport'
TRANSPORT_MANIFEST = TRANSPORT + '/manifest.json'
SCHEMA = 'hadith-bank-preserved-record-transport-v1'
MAX_RECORD_BYTES = 32 * 1024 * 1024
MAX_TRANSPORT_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 128 * 1024
EXPECTED_PATHS = {
    f'materials/fa-targhib-bazmandegan-v{volume}/records.jsonl':
    f'{TRANSPORT}/canonical-v{volume}-records.jsonl.gz'
    for volume in (1, 2, 3)
}


def checked_root(root):
    root = Path(os.path.abspath(root))
    for part in (*reversed(root.parents), root):
        if part.is_symlink():
            raise ValueError('Symlink in root path: ' + str(part))
        if not part.is_dir():
            raise ValueError('Root is not an existing directory: ' + str(part))
    return root


def checked_file(root, relative, *, missing_ok=False):
    if (not isinstance(relative, str) or not relative or '\\' in relative or
            ':' in relative or relative.startswith('/') or
            any(ord(char) < 32 or ord(char) == 127 for char in relative) or
            any(part in ('', '.', '..') for part in relative.split('/'))):
        raise ValueError('Unsafe relative file path')
    path = root
    parts = relative.split('/')
    for index, part in enumerate(parts):
        path = path / part
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            if missing_ok and index == len(parts) - 1:
                return path
            raise ValueError('Required path is missing: ' + relative) from None
        if stat.S_ISLNK(mode):
            raise ValueError('Symlink in file path: ' + relative)
        if index < len(parts) - 1:
            if not stat.S_ISDIR(mode):
                raise ValueError('File parent is not a directory: ' + relative)
        elif not stat.S_ISREG(mode):
            raise ValueError('Not a regular file: ' + relative)
    return path


def read_bounded(path, limit):
    if path.stat().st_size > limit:
        raise ValueError('File exceeds byte limit: ' + path.name)
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('File exceeds byte limit: ' + path.name)
    return data


def reject_constant(value):
    raise ValueError('Non-JSON numeric constant: ' + value)


def read_json(path):
    return json.loads(read_bounded(path, MAX_MANIFEST_BYTES).decode('utf-8'),
                      parse_constant=reject_constant)


def integer(value, label, maximum=None):
    if type(value) is not int or value < 1 or (maximum is not None and value > maximum):
        raise ValueError('Invalid ' + label)
    return value


def digest(value, length, label):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{' + str(length) + r'}', value):
        raise ValueError('Invalid ' + label)
    return value


def git_blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def validated_candidates(root):
    """Validate every input and existing destination without writing anything."""
    manifest = read_json(checked_file(root, TRANSPORT_MANIFEST))
    if not isinstance(manifest, dict) or manifest.get('schema') != SCHEMA:
        raise ValueError('Unsupported transport manifest schema')
    files = manifest.get('files')
    if not isinstance(files, list) or len(files) != len(EXPECTED_PATHS):
        raise ValueError('Transport must contain exactly the three approved paths')
    entries = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise ValueError('Invalid transport entry')
        relative = entry.get('path')
        if (not isinstance(relative, str) or relative not in EXPECTED_PATHS or
                relative in entries or entry.get('transport_path') != EXPECTED_PATHS[relative]):
            raise ValueError('Transport path is not an approved unique path pair')
        entries[relative] = entry
    candidates = []
    all_ids = set()
    for relative in EXPECTED_PATHS:
        entry = entries[relative]
        expected_size = integer(entry.get('bytes'), 'canonical byte count', MAX_RECORD_BYTES)
        expected_compressed_size = integer(entry.get('transport_bytes'), 'transport byte count', MAX_TRANSPORT_BYTES)
        count = integer(entry.get('count'), 'record count')
        expected_sha = digest(entry.get('sha256'), 64, 'canonical SHA-256')
        expected_git_sha = digest(entry.get('git_blob_sha'), 40, 'Git blob SHA')
        expected_transport_sha = digest(entry.get('transport_sha256'), 64, 'transport SHA-256')
        destination = checked_file(root, relative, missing_ok=True)
        material_path = str(Path(relative).with_name('manifest.json'))
        material = read_json(checked_file(root, material_path))
        records = material.get('records') if isinstance(material, dict) else None
        if (not isinstance(records, dict) or records.get('path') != relative or
                records.get('sha256') != expected_sha or type(records.get('count')) is not int or
                records['count'] != count):
            raise ValueError('Material manifest disagrees with transport: ' + relative)
        compressed = read_bounded(checked_file(root, entry['transport_path']), MAX_TRANSPORT_BYTES)
        if (len(compressed) != expected_compressed_size or
                hashlib.sha256(compressed).hexdigest() != expected_transport_sha):
            raise ValueError('Compressed size or SHA-256 mismatch: ' + relative)
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode='rb') as stream:
                data = stream.read(expected_size + 1)
        except (OSError, EOFError, zlib.error) as error:
            raise ValueError('Invalid gzip transport: ' + relative) from error
        if len(data) != expected_size or hashlib.sha256(data).hexdigest() != expected_sha:
            raise ValueError('Canonical size or SHA-256 mismatch: ' + relative)
        if git_blob_sha(data) != expected_git_sha:
            raise ValueError('Git blob SHA mismatch: ' + relative)
        if not data.endswith(b'\n'):
            raise ValueError('Canonical JSONL must end in a newline: ' + relative)
        lines = data.decode('utf-8')[:-1].split('\n')
        if len(lines) != count:
            raise ValueError('Record count mismatch: ' + relative)
        for line in lines:
            record = json.loads(line, parse_constant=reject_constant)
            record_id = record.get('id') if isinstance(record, dict) else None
            if not isinstance(record_id, str) or not record_id.strip():
                raise ValueError('JSONL record needs a nonempty string ID: ' + relative)
            if record_id in all_ids:
                raise ValueError('Duplicate record ID: ' + record_id)
            all_ids.add(record_id)
        status = 'restored'
        if destination.exists():
            if read_bounded(destination, MAX_RECORD_BYTES) != data:
                raise ValueError('Existing canonical file differs; refusing replacement: ' + relative)
            status = 'reused'
        candidates.append((entry, destination, data, status))
    return candidates


def create_atomic(root, relative, data):
    """Publish a complete file only when the destination does not already exist."""
    destination = checked_file(root, relative, missing_ok=True)
    if destination.exists():
        if read_bounded(destination, MAX_RECORD_BYTES) == data:
            return 'reused'
        raise ValueError('Existing canonical file differs; refusing replacement: ' + relative)
    descriptor, temporary = tempfile.mkstemp(prefix='.records-transport-', dir=destination.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        checked_file(root, relative, missing_ok=True)
        try:
            # A hard link publishes the completed bytes atomically and refuses
            # to overwrite a file created concurrently after validation.
            os.link(temporary, destination)
        except FileExistsError:
            checked_file(root, relative)
            if read_bounded(destination, MAX_RECORD_BYTES) != data:
                raise ValueError('Concurrent canonical file differs; refusing replacement: ' + relative) from None
            return 'reused'
        return 'restored'
    finally:
        os.unlink(temporary)


def restore(root):
    root = checked_root(root)
    candidates = validated_candidates(root)
    results = []
    for entry, destination, data, status in candidates:
        # Recheck existing output immediately before reporting or creating it.
        status = create_atomic(root, entry['path'], data)
        results.append({key: entry[key] for key in ('path', 'bytes', 'sha256', 'git_blob_sha', 'count')} | {'status': status})
    return {'schema': 'hadith-bank-preserved-record-restore-v1', 'status': 'passed',
            'restored': sum(item['status'] == 'restored' for item in results),
            'reused': sum(item['status'] == 'reused' for item in results),
            'records': sum(item['count'] for item in results), 'files': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        result = restore(args.root)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}, ensure_ascii=False, separators=(',', ':')))
        return 1
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
