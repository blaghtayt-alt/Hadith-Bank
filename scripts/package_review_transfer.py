#!/usr/bin/env python3
"""Select exact ZIP members for resumable, bounded, offline byte transfer.

This utility does not extract narrations, change source text, or approve review.
The final manifest is written only after all selected bytes have been packaged.
Keep its SHA-256 from the pack summary to verify the received manifest.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import zipfile
import zlib


SCHEMA = 'hadith-bank-review-transfer-v1'
CHUNK_BYTES = 256 * 1024
BUFFER_BYTES = 64 * 1024
MANIFEST = 'manifest.json'
PLAN = 'plan.json'
COMPLETE = '.review-transfer-complete.json'
HASH = re.compile(r'[0-9a-f]{64}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(BUFFER_BYTES), b''):
            digest.update(block)
    return digest.hexdigest()


def valid_hash(value):
    require(isinstance(value, str) and HASH.fullmatch(value), 'Invalid SHA-256')
    return value


def safe_name(value):
    require(isinstance(value, str) and value and len(value) <= 4096,
            'Invalid archive member name')
    pieces = value.split('/')
    require(not any(c in value for c in '\\:') and
            not any(ord(c) < 32 or ord(c) == 127 for c in value) and
            all(p and p not in ('.', '..') and not p.endswith((' ', '.')) for p in pieces),
            'Unsafe archive member path')
    require(not any(re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',
                                 p, re.I) for p in pieces), 'Unsafe reserved filename')
    require(value.casefold() != COMPLETE.casefold(), 'Reserved transfer completion filename')
    return value


def safe_path(root, name=None):
    target = Path(root).absolute()
    if name is not None:
        target = target.joinpath(*safe_name(name).split('/'))
    require(not any(p.is_symlink() for p in (target, *target.parents)),
            'Symlinks are not permitted in transfer paths')
    # Normalize lexical aliases only after inspecting every supplied ancestor;
    # resolving first would hide a symlink that appeared before a '..' segment.
    return Path(os.path.abspath(target))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    with safe_path(path).open('rb') as stream:
        raw = stream.read(32 * 1024 * 1024 + 1)
    require(len(raw) <= 32 * 1024 * 1024, 'Transfer metadata exceeds 32 MiB')
    return json.loads(raw, object_pairs_hook=unique)


def write_exact(path, data):
    """Atomically create bytes, or verify an existing file without replacing it."""
    path = safe_path(path)
    if path.exists():
        require(path.is_file() and path.stat().st_size == len(data) and
                digest_file(path) == hashlib.sha256(data).hexdigest(),
                'Existing transfer file differs or is corrupt: ' + path.name)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.transfer-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Refuse concurrent writers rather than overwrite an unexpected file.
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return True


def checked_selection(selection):
    require(isinstance(selection, list) and 0 < len(selection) <= 10000,
            'Selection must be an explicit nonempty JSON array of member names')
    names = [safe_name(name) for name in selection]
    require(len(set(names)) == len(names), 'Duplicate selected member')
    folded = [name.casefold() for name in names]
    require(len(set(folded)) == len(folded), 'Case-colliding selected members')
    files = set(folded)
    require(not any('/'.join(name.split('/')[:i]) in files
                    for name in folded for i in range(1, len(name.split('/')))),
            'Selected file and directory paths collide')
    return names


class ChunkWriter:
    def __init__(self, root, index, chunk_bytes):
        self.root, self.index, self.chunk_bytes = root, index, chunk_bytes
        self.pending = bytearray()
        self.parts, self.size, self.reused = [], 0, 0
        self.digest = hashlib.sha256()

    def write(self, data):
        self.digest.update(data)
        self.size += len(data)
        offset = 0
        while offset < len(data):
            count = min(self.chunk_bytes - len(self.pending), len(data) - offset)
            self.pending.extend(data[offset:offset + count])
            offset += count
            if len(self.pending) == self.chunk_bytes:
                self.flush_part()
        return len(data)

    def flush_part(self):
        if not self.pending:
            return
        data = bytes(self.pending)
        name = 'parts/%05d-%08d.bin' % (self.index, len(self.parts))
        self.reused += not write_exact(safe_path(self.root, name), data)
        self.parts.append({'path': name, 'size_bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()})
        self.pending.clear()

    def flush(self):
        pass


def pack(archive, expected_sha256, selection, output, chunk_bytes=CHUNK_BYTES, compression='gzip'):
    valid_hash(expected_sha256)
    require(type(chunk_bytes) is int and 1024 <= chunk_bytes <= CHUNK_BYTES,
            'chunk-bytes must be between 1024 and 262144')
    require(compression in ('none', 'gzip'), 'Unsupported compression')
    archive = safe_path(archive)
    require(archive.is_file() and digest_file(archive) == expected_sha256,
            'Archive SHA-256 mismatch')
    names = checked_selection(selection)
    root = safe_path(output)
    plan = {'schema': SCHEMA, 'archive_sha256': expected_sha256,
            'archive_size_bytes': archive.stat().st_size, 'selection': names,
            'chunk_bytes': chunk_bytes, 'compression': compression}
    with zipfile.ZipFile(archive) as source:
        members = {}
        for info in source.infolist():
            require(info.orig_filename == info.filename, 'Unsafe truncated archive member name')
            name = safe_name(info.filename[:-1] if info.is_dir() else info.filename)
            require(name not in members, 'Duplicate archive member')
            mode = stat.S_IFMT(info.external_attr >> 16)
            require(mode in (0, stat.S_IFREG, stat.S_IFDIR), 'Unsafe archive member type')
            members[name] = info
        require(all(name in members and not members[name].is_dir() for name in names),
                'Selected archive member is missing or is a directory')
        require(all(not members[name].flag_bits & 1 for name in names),
                'Encrypted members are unsupported')
        if root.exists() and not safe_path(root, PLAN).exists():
            require(root.is_dir() and not any(root.iterdir()), 'Output is not an empty transfer directory')
        write_exact(safe_path(root, PLAN), json_bytes(plan))
        files, reused = [], 0
        for index, name in enumerate(names):
            writer = ChunkWriter(root, index, chunk_bytes)
            digest, size = hashlib.sha256(), 0
            target = gzip.GzipFile(filename='', mode='wb', fileobj=writer,
                                   compresslevel=6, mtime=0) if compression == 'gzip' else writer
            try:
                with source.open(members[name]) as stream:
                    for block in iter(lambda: stream.read(BUFFER_BYTES), b''):
                        digest.update(block)
                        size += len(block)
                        target.write(block)
            finally:
                if compression == 'gzip':
                    target.close()
            require(size == members[name].file_size, 'ZIP member size mismatch')
            writer.flush_part()
            reused += writer.reused
            files.append({'path': name, 'size_bytes': size, 'sha256': digest.hexdigest(),
                          'stored_size_bytes': writer.size, 'stored_sha256': writer.digest.hexdigest(),
                          'parts': writer.parts})
    manifest = {**plan, 'files': files}
    for entry in files:
        verify_entry(root, entry, compression)
    write_exact(safe_path(root, MANIFEST), json_bytes(manifest))
    result = summary(root, manifest)
    result.update(status='packaged', reused_parts=reused)
    return result


def read_manifest(root, expected_sha256=None, expected_manifest_sha256=None):
    root = safe_path(root)
    path = safe_path(root, MANIFEST)
    if expected_manifest_sha256 is not None:
        require(digest_file(path) == valid_hash(expected_manifest_sha256), 'Manifest SHA-256 mismatch')
    manifest = load_json(path)
    require(isinstance(manifest, dict) and manifest.get('schema') == SCHEMA, 'Invalid transfer schema')
    valid_hash(manifest.get('archive_sha256'))
    if expected_sha256 is not None:
        require(manifest['archive_sha256'] == valid_hash(expected_sha256), 'Archive identity mismatch')
    require(type(manifest.get('archive_size_bytes')) is int and manifest['archive_size_bytes'] >= 0,
            'Invalid archive size')
    require(type(manifest.get('chunk_bytes')) is int and 1024 <= manifest['chunk_bytes'] <= CHUNK_BYTES,
            'Invalid chunk size')
    require(manifest.get('compression') in ('none', 'gzip'), 'Invalid compression')
    names = checked_selection(manifest.get('selection'))
    files = manifest.get('files')
    require(isinstance(files, list) and len(files) == len(names), 'Manifest selection/count mismatch')
    for index, (entry, name) in enumerate(zip(files, names)):
        require(isinstance(entry, dict) and entry.get('path') == name, 'Manifest member identity mismatch')
        for key in ('size_bytes', 'stored_size_bytes'):
            require(type(entry.get(key)) is int and entry[key] >= 0, 'Invalid member size')
        for key in ('sha256', 'stored_sha256'):
            valid_hash(entry.get(key))
        require(isinstance(entry.get('parts'), list), 'Invalid part list')
        total = 0
        for number, part in enumerate(entry['parts']):
            require(isinstance(part, dict) and part.get('path') ==
                    'parts/%05d-%08d.bin' % (index, number), 'Unsafe or reordered part path')
            require(type(part.get('size_bytes')) is int and 0 < part['size_bytes'] <= manifest['chunk_bytes'],
                    'Invalid part size')
            valid_hash(part.get('sha256'))
            total += part['size_bytes']
        require(total == entry['stored_size_bytes'], 'Stored size does not match parts')
    return manifest


def verify_entry(root, entry, compression, output=None):
    """Bound memory and decoded size; verify stored and original bytes separately."""
    with tempfile.TemporaryFile() as stored:
        combined = hashlib.sha256()
        for part in entry['parts']:
            path = safe_path(root, part['path'])
            require(path.is_file() and path.stat().st_size == part['size_bytes'], 'Part missing or size mismatch')
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(BUFFER_BYTES), b''):
                    digest.update(block)
                    combined.update(block)
                    stored.write(block)
            require(digest.hexdigest() == part['sha256'], 'Part SHA-256 mismatch')
        require(combined.hexdigest() == entry['stored_sha256'] and
                stored.tell() == entry['stored_size_bytes'], 'Stored SHA-256 or size mismatch')
        stored.seek(0)
        reader = gzip.GzipFile(fileobj=stored, mode='rb') if compression == 'gzip' else stored
        digest, size = hashlib.sha256(), 0
        try:
            while True:
                block = reader.read(min(BUFFER_BYTES, entry['size_bytes'] - size + 1))
                if not block:
                    break
                size += len(block)
                require(size <= entry['size_bytes'], 'Decoded data exceeds declared size')
                digest.update(block)
                if output is not None:
                    output.write(block)
        finally:
            if compression == 'gzip':
                reader.close()
        require(size == entry['size_bytes'] and digest.hexdigest() == entry['sha256'],
                'Original SHA-256 or size mismatch')


def summary(root, manifest):
    return {'status': 'verified', 'files': len(manifest['files']),
            'parts': sum(len(entry['parts']) for entry in manifest['files']),
            'original_bytes': sum(entry['size_bytes'] for entry in manifest['files']),
            'stored_bytes': sum(entry['stored_size_bytes'] for entry in manifest['files']),
            'archive_sha256': manifest['archive_sha256'],
            'manifest_sha256': digest_file(safe_path(root, MANIFEST)),
            'review_status_changed': False}


def verify(directory, expected_sha256=None, expected_manifest_sha256=None):
    root = safe_path(directory)
    manifest = read_manifest(root, expected_sha256, expected_manifest_sha256)
    for entry in manifest['files']:
        verify_entry(root, entry, manifest['compression'])
    return summary(root, manifest)


def reassemble(directory, output, expected_sha256=None, expected_manifest_sha256=None):
    result = verify(directory, expected_sha256, expected_manifest_sha256)
    root, destination = safe_path(directory), safe_path(output)
    require(root != destination and root not in destination.parents and destination not in root.parents,
            'Transfer and reconstruction directories must be separate')
    manifest = read_manifest(root, expected_sha256, result['manifest_sha256'])
    marker = {'schema': SCHEMA, 'manifest_sha256': result['manifest_sha256'], 'files': result['files']}
    completion = destination / COMPLETE
    safe_path(completion)
    if completion.exists():
        require(load_json(completion) == marker, 'Output belongs to a different transfer')
    # Preflight all target paths and existing bytes before restoring any new file.
    for entry in manifest['files']:
        path = safe_path(destination, entry['path'])
        require(all(not p.exists() or p.is_dir() for p in path.parents), 'Destination parent is not a directory')
        if path.exists():
            require(path.is_file() and path.stat().st_size == entry['size_bytes'] and
                    digest_file(path) == entry['sha256'], 'Existing reconstructed file differs or is corrupt')
    reused = 0
    for entry in manifest['files']:
        path = safe_path(destination, entry['path'])
        if path.exists():
            reused += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.transfer-', suffix='.tmp', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                verify_entry(root, entry, manifest['compression'], stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
    write_exact(completion, json_bytes(marker))
    result.update(status='reassembled', reused_files=reused)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    create = modes.add_parser('pack', help='Package only explicitly selected ZIP members')
    create.add_argument('--archive', type=Path, required=True)
    create.add_argument('--expected-sha256', required=True)
    create.add_argument('--selection', type=Path, required=True, help='JSON array of exact archive member names')
    create.add_argument('--output', type=Path, required=True)
    create.add_argument('--chunk-bytes', type=int, default=CHUNK_BYTES)
    create.add_argument('--compression', choices=('gzip', 'none'), default='gzip')
    for name in ('verify', 'reassemble'):
        mode = modes.add_parser(name)
        mode.add_argument('--input', type=Path, required=True)
        mode.add_argument('--expected-sha256', help='Expected original archive SHA-256')
        mode.add_argument('--expected-manifest-sha256', help='Trusted manifest SHA-256 from pack output')
        if name == 'reassemble':
            mode.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == 'pack':
            result = pack(args.archive, args.expected_sha256, load_json(args.selection),
                          args.output, args.chunk_bytes, args.compression)
        elif args.mode == 'verify':
            result = verify(args.input, args.expected_sha256, args.expected_manifest_sha256)
        else:
            result = reassemble(args.input, args.output, args.expected_sha256, args.expected_manifest_sha256)
    except (OSError, ValueError, EOFError, zipfile.BadZipFile, zlib.error, RuntimeError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)[:512]}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
