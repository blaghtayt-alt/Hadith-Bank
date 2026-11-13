#!/usr/bin/env python3
"""Export a bounded, exact committed held-source subset without source requests.

Only the ignored run-attempt diagnostic directory is written. The saved local
HEAD is the checkpoint; neither the triggering SHA nor a newer remote revision
is substituted. This tool never fetches, rebuilds, reviews or publishes data.
"""
from __future__ import annotations

import argparse
import bisect
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import import_deenhindi as importer
import recover_deenhindi_artifact as recovery

MAX_RECORDS = 250
MAX_BYTES = 32 * 1024**2
OUTPUT_BASE = '.work/deenhindi-held-evidence'
STATE_ARTIFACT = 'saved-state.json.gz'
SCHEMA = 'deenhindi-committed-held-evidence-v1'
CODE = ('scripts/import_deenhindi.py', 'scripts/recover_deenhindi_artifact.py',
        'scripts/export_deenhindi_held_evidence.py')
SHA1 = re.compile(r'[0-9a-f]{40}\Z')


def require(condition, message):
    if not condition:
        raise ValueError('Deen held evidence: ' + message)


def git(root, *arguments):
    result = subprocess.run(['git', '-C', str(root), *arguments], capture_output=True,
        timeout=60, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_REPLACE_OBJECTS': '1'})
    require(result.returncode == 0, 'Git checkpoint check failed: ' + ' '.join(arguments))
    return result.stdout


class Snapshot:
    def __init__(self, root, expected_head):
        self.root = root.resolve()
        require(Path(git(self.root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() == self.root,
                'root must be the repository worktree root')
        self.head = git(self.root, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
        require(SHA1.fullmatch(self.head) and self.head == expected_head, 'saved local HEAD differs')
        self.tree = git(self.root, 'rev-parse', self.head + '^{tree}').decode().strip()
        require(SHA1.fullmatch(self.tree), 'invalid committed tree')
        self.receipts = {}
        self.assert_unchanged()
        self.process = subprocess.Popen(['git', '-C', str(self.root), 'cat-file', '--batch'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_REPLACE_OBJECTS': '1'})

    def assert_unchanged(self):
        require(git(self.root, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip() == self.head,
                'saved local HEAD changed during export')
        git(self.root, 'diff', '--quiet', '--no-ext-diff', '--no-textconv', self.head, '--',
            importer.IMPORT, *CODE)

    def read(self, relative, limit=recovery.MAX_STATE_BYTES):
        name = recovery.safe_name(relative)
        require(not any(c in name for c in '\r\n\t'), 'unsafe Git evidence path')
        self.process.stdin.write((self.head + ':' + name + '\n').encode())
        self.process.stdin.flush()
        header = self.process.stdout.readline(4097)
        parts = header.decode('ascii', errors='strict').strip().split(' ')
        require(len(header) <= 4096 and len(parts) == 3 and SHA1.fullmatch(parts[0])
                and parts[1] == 'blob' and parts[2].isdigit(), 'missing committed source file: ' + name)
        size = int(parts[2])
        require(size <= limit, 'oversized committed source file: ' + name)
        data = self.process.stdout.read(size)
        require(len(data) == size and self.process.stdout.read(1) == b'\n', 'incomplete Git source bytes')
        require(hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + data).hexdigest() == parts[0],
                'Git source blob hash differs')
        require(recovery.read_local(self.root, name, limit) == data,
                'working source differs from saved commit: ' + name)
        self.receipts[name] = {'path': name, 'git_blob_sha1': parts[0], 'sha256': recovery.sha(data), 'bytes': size}
        return data

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        self.process.communicate(timeout=10)


def replace_bundle(root, relative, files):
    require(relative.startswith(OUTPUT_BASE + '/') and len(Path(relative).parts) == 3,
            'diagnostic output must stay in its run-attempt directory')
    destination = recovery.local(root, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        marker = recovery.local(root, relative + '/evidence-manifest.json')
        require(destination.is_dir() and marker.is_file()
                and recovery.json_value(recovery.read_local(root, relative + '/evidence-manifest.json')).get('schema') == SCHEMA,
                'refusing to replace an unrecognized diagnostic directory')
    staging = Path(tempfile.mkdtemp(prefix=destination.name + '-new-', dir=destination.parent))
    previous = None
    try:
        for name, data in files.items():
            target = staging / recovery.safe_name(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        if destination.exists():
            previous = Path(tempfile.mkdtemp(prefix=destination.name + '-old-', dir=destination.parent))
            previous.rmdir()
            destination.rename(previous)
        try:
            staging.rename(destination)
        except BaseException:
            if previous is not None:
                previous.rename(destination)
                previous = None
            raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if previous is not None:
            shutil.rmtree(previous)


def bundle_files(checkpoint, selected, entries, objects, source_receipts, ordered_keys, maximum_bytes, state_payload):
    count = len(selected)
    summary = {**checkpoint, 'selected_held_entries': count,
        'remaining_held_queue_count': len(ordered_keys) - count,
        'selected_keys': list(selected), 'next_held_key': ordered_keys[count] if count < len(ordered_keys) else None}
    files = {STATE_ARTIFACT: state_payload,
        'held-source-records.jsonl': importer.rows_bytes(list(selected.values())),
        'held-state-entries.json': importer.json_bytes({key: entries[key] for key in selected}),
        'checkpoint.json': importer.json_bytes(summary),
        **{'sources/' + name: data for name, data in sorted(objects.items())}}
    size_without_manifest = sum(map(len, files.values()))
    manifest = {'schema': SCHEMA, 'saved_head': checkpoint['saved_head'], 'held_keys': list(selected),
        'source_record_sha256': {key: recovery.sha(importer.json_bytes(row['source_record'])) for key, row in selected.items()},
        'files': {name: {**source_receipts[name], 'stored_sha256': recovery.sha(data), 'stored_bytes': len(data)}
                  for name, data in sorted(objects.items())},
        'artifact_files': {name: {'sha256': recovery.sha(data), 'bytes': len(data)} for name, data in sorted(files.items())},
        'maximum_output_bytes': maximum_bytes, 'total_output_bytes': size_without_manifest}
    # Include the manifest itself in the hard byte bound without a self-hash.
    for _ in range(8):
        encoded = importer.json_bytes(manifest)
        size = size_without_manifest + len(encoded)
        if size == manifest['total_output_bytes']:
            files['evidence-manifest.json'] = encoded
            return files
        manifest['total_output_bytes'] = size
    raise ValueError('Deen held evidence: manifest byte accounting did not stabilize')


def export(root, expected_head, max_records=MAX_RECORDS, max_bytes=MAX_BYTES):
    require(type(max_records) is int and 1 <= max_records <= MAX_RECORDS, 'record bound must be 1..250')
    require(type(max_bytes) is int and 1 <= max_bytes <= MAX_BYTES, 'byte bound must be at most 32 MiB')
    require(isinstance(expected_head, str) and SHA1.fullmatch(expected_head), 'exact saved commit SHA required')
    root = Path(root).resolve()
    run, attempt = os.environ.get('GITHUB_RUN_ID'), os.environ.get('GITHUB_RUN_ATTEMPT')
    require((run is None and attempt is None) or
            isinstance(run, str) and run.isdigit() and isinstance(attempt, str) and attempt.isdigit(),
            'invalid run-attempt diagnostic identity')
    relative = OUTPUT_BASE + '/' + (run + '-' + attempt if run is not None else 'local')
    snapshot = Snapshot(root, expected_head)
    try:
        code_modules = (importer, recovery, sys.modules[__name__])
        for path, module in zip(CODE, code_modules):
            require(snapshot.read(path) == Path(module.__file__).read_bytes(), 'executed verifier differs from saved code')
        state_path = importer.IMPORT + '/state.json'
        state_bytes = snapshot.read(state_path)
        state = recovery.json_value(state_bytes)
        inventory = recovery.json_value(snapshot.read(importer.IMPORT + '/inventory.json'))
        progress = recovery.json_value(snapshot.read(importer.IMPORT + '/progress.json'))
        require(state.get('schema') == 'deenhindi-import-state-v1' and isinstance(state.get('imported'), dict),
                'invalid committed source state')
        require(isinstance(inventory, dict) and isinstance(progress, dict), 'invalid inventory or progress')
        entries = state['imported']
        require(all(isinstance(key, str) and isinstance(entry, dict)
                    and entry.get('collection') in importer.BOOKS and isinstance(entry.get('number'), str)
                    and key == entry['collection'] + ':' + entry['number'] for key, entry in entries.items()),
                'invalid committed imported identity')
        order = {slug: {number: index for index, number in enumerate(inventory.get(slug, {}).get('identifiers', []))}
                 for slug in importer.BOOKS}
        queued, candidates, priorities, per_book = set(), {}, [], {}
        for slug in sorted(importer.BOOKS):
            staged_path = importer.IMPORT + '/staged/' + slug + '.jsonl'
            data = snapshot.read(staged_path)
            count = 0
            offset = 0
            for line in io.BytesIO(data):
                start, offset = offset, offset + len(line)
                if not line.strip():
                    continue
                require(len(line) <= recovery.MAX_OBJECT_BYTES, 'oversized held source row')
                row = recovery.json_value(line)
                number = row.get('number')
                require(row.get('collection') == slug and isinstance(number, str) and number in order[slug],
                        'held row identity differs from observed inventory')
                key = slug + ':' + number
                require(key not in queued and key in entries, 'duplicate or unimported held identity: ' + key)
                queued.add(key)
                count += 1
                priority = (slug, order[slug][number], key)
                bisect.insort(priorities, priority)
                # Keep only bounded selection descriptors while counting the
                # whole queue; do not retain every complete language object.
                candidates[key] = (staged_path, start, len(line), recovery.sha(line))
                if len(priorities) > max_records:
                    candidates.pop(priorities.pop()[2])
            per_book[slug] = count
        require(progress.get('imported_count') == len(entries)
                and progress.get('classification_pending_count') == len(queued), 'state/progress/held counts differ')
        for slug in importer.BOOKS:
            counts = progress.get('by_collection', {}).get(slug, {})
            require(counts.get('classification_pending') == per_book[slug]
                    and counts.get('fetched') == sum(item.get('collection') == slug for item in entries.values()),
                    'per-book source/held progress differs: ' + slug)
        ordered_keys = sorted(queued, key=lambda key: (key.split(':', 1)[0], order[key.split(':', 1)[0]][key.split(':', 1)[1]], key))
        # Preserve the complete committed bytes, including errors, consumed
        # attempts and unknown controls. A fixed header makes this deterministic;
        # no parsed JSON reserialization or source-state mutation is involved.
        compressed = io.BytesIO()
        with gzip.GzipFile(filename='', mode='wb', fileobj=compressed, mtime=0, compresslevel=9) as stream:
            stream.write(state_bytes)
        state_payload = compressed.getvalue()
        state_receipt = {'path': STATE_ARTIFACT, 'source_path': state_path, 'compression': 'gzip',
            'bytes': len(state_bytes), 'sha256': recovery.sha(state_bytes),
            'git_blob_sha1': snapshot.receipts[state_path]['git_blob_sha1'],
            'stored_bytes': len(state_payload), 'stored_sha256': recovery.sha(state_payload),
            'maximum_uncompressed_bytes': recovery.MAX_STATE_BYTES}
        checkpoint = {'schema': SCHEMA, 'saved_head': snapshot.head, 'saved_tree': snapshot.tree,
            'checkpoint_scope': 'Exact saved local HEAD; not a claim about the latest remote main or deployment.',
            'run_id': run, 'run_attempt': attempt, 'input_receipts': copy.deepcopy(snapshot.receipts),
            'saved_state': state_receipt,
            'held_entries_total': len(queued), 'held_by_collection': per_book,
            'held_queue_order': 'collection key then observed inventory position',
            'held_queue_keys_sha256': recovery.sha(importer.json_bytes(ordered_keys)), 'maximum_records': max_records,
            'source_progress': {key: value for key, value in progress.items() if not isinstance(value, (dict, list))},
            'source_controls_unchanged': True, 'new_source_http_requests': 0, 'new_review_decisions': 0,
            'source_or_publication_mutations': False, 'independent_pro_qc': 'not_performed'}
        selected, objects = {}, {}
        initial_files = bundle_files(checkpoint, selected, entries, objects, snapshot.receipts,
                                     ordered_keys, max_bytes, state_payload)
        require(sum(map(len, initial_files.values())) <= max_bytes,
                'committed state and checkpoint receipts exceed the byte bound')
        for _, _, key in priorities:
            saved, verified_files = recovery.checked_entry(key, entries[key],
                lambda name: snapshot.read(name, recovery.MAX_OBJECT_BYTES), inventory)
            staged_path, start, length, digest = candidates[key]
            with recovery.local(root, staged_path).open('rb') as source:
                source.seek(start)
                line = source.read(length)
            require(len(line) == length and recovery.sha(line) == digest,
                    'selected held row changed after committed-byte verification: ' + key)
            row = recovery.json_value(line)
            require(all(row.get(name) == saved.get(name) for name in
                    ('schema', 'collection', 'number', 'snapshot', 'source_record', 'source_reference_verbatim'))
                    and row.get('intake_classification') == saved.get('classification')
                    and row.get('parsed_path') == entries[key]['parsed']['path'], 'held row differs from immutable source: ' + key)
            provisional = {**selected, key: row}
            new_objects = {**objects, **verified_files}
            # Bound retained source memory before constructing metadata/rows.
            if len(state_payload) + sum(map(len, new_objects.values())) > max_bytes:
                require(selected, 'first held source exceeds the byte bound')
                break
            files = bundle_files(checkpoint, provisional, entries, new_objects, snapshot.receipts, ordered_keys, max_bytes, state_payload)
            if sum(map(len, files.values())) > max_bytes:
                require(selected, 'first held source and receipts exceed the byte bound')
                break
            selected, objects = provisional, new_objects
        files = bundle_files(checkpoint, selected, entries, objects, snapshot.receipts, ordered_keys, max_bytes, state_payload)
        total_bytes = sum(map(len, files.values()))
        require(total_bytes <= max_bytes and (selected or not queued), 'bounded evidence bundle cannot represent the first held record')
        snapshot.assert_unchanged()
        replace_bundle(root, relative, files)
        return {'schema': SCHEMA, 'saved_head': snapshot.head, 'output': relative,
            'held_entries_total': len(queued), 'selected_held_entries': len(selected),
            'remaining_held_queue_count': len(queued) - len(selected), 'total_output_bytes': total_bytes}
    finally:
        snapshot.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--max-records', type=int, default=MAX_RECORDS)
    parser.add_argument('--max-bytes', type=int, default=MAX_BYTES)
    args = parser.parse_args(argv)
    try:
        result = export(args.root, args.expected_head, args.max_records, args.max_bytes)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, 'Held evidence export failed: ' + str(error) + '\n')
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
