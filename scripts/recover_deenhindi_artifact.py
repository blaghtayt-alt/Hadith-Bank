#!/usr/bin/env python3
"""Recover one explicitly approved failed-worker archive without source requests.

The CLI accepts only the pinned GitHub artifact in the checked-in plan. Archive
contents are data, never executable code. Current importer parsing and immutable
source hashes validate every archived entry before the append-only transaction.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import zipfile

import import_deenhindi as importer

REPOSITORY = 'blaghtayt-alt/Hadith-Bank'
PLAN_PATH = 'catalog/deenhindi-artifact-recovery.json'
RECOVERY_ID = 'run-43400779530-artifact-14026408835'
RECOVERY_DIR = importer.IMPORT + '/recoveries/' + RECOVERY_ID
RECEIPT_PATH = RECOVERY_DIR + '/receipt.json'
INDEX_PATH = RECOVERY_DIR + '/verified-archive-index.json.gz'
WORK = '.work/deenhindi-artifact-recovery'
DELTA = WORK + '/delta'
HELD = WORK + '/held'
PIN = {
    'repository': REPOSITORY, 'run_id': 43400779530, 'artifact_id': 14026408835,
    'artifact_name': 'web-import-recovery-43400779530-1',
    'archive_bytes': 674433448,
    'archive_sha256': '286f14110e2de2c64e01c079ba23b5c2b4a8a0de574244d869f00fa7edbc341f',
    'archive_imported_entries': 13283, 'minimum_common_entries': 12775,
    'maximum_missing_entries': 508,
}
MAX_ARCHIVE_UNCOMPRESSED = 2 * 1024**3
MAX_MEMBERS = 250000
MAX_STATE_BYTES = 64 * 1024**2
MAX_OBJECT_BYTES = 32 * 1024**2
MAX_DELTA_BYTES = 128 * 1024**2
MAX_HELD_BYTES = 32 * 1024**2
HEX = re.compile(r'[0-9a-f]{64}')


def require(condition, message):
    if not condition:
        raise ValueError('Deen artifact recovery: ' + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key ' + key)
        result[key] = value
    return result


def json_value(data):
    return json.loads(data, object_pairs_hook=unique_pairs)


def safe_name(name):
    require(isinstance(name, str) and name and '\\' not in name and '\x00' not in name,
            'unsafe path')
    parts = name.rstrip('/').split('/')
    require(all(part not in ('', '.', '..') and ':' not in part for part in parts)
            and not name.startswith('/') and PurePosixPath(name).as_posix() == name.rstrip('/'),
            'unsafe path ' + repr(name))
    return name.rstrip('/')


def local(root, relative):
    name = safe_name(relative)
    path = root / name
    require(path.resolve().is_relative_to(root), 'path escaped root')
    require(not any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)),
            'symlink in local evidence path ' + name)
    return path


def read_local(root, relative, limit=MAX_STATE_BYTES):
    path = local(root, relative)
    require(path.is_file() and path.stat().st_size <= limit, 'missing or oversized file ' + relative)
    return path.read_bytes()


def load_plan(root):
    path = local(root, PLAN_PATH)
    if not path.exists():
        return None
    plan = json_value(read_local(root, PLAN_PATH))
    require(plan.get('schema') == 'deenhindi-fixed-artifact-recovery-v1', 'unsupported plan schema')
    require(type(plan.get('enabled')) is bool, 'explicit enabled flag required')
    require({k: plan.get(k) for k in PIN} == PIN, 'plan differs from the single approved artifact')
    require(plan.get('recovery_id') == RECOVERY_ID, 'recovery identity differs')
    return plan if plan['enabled'] else None


def verify_archive(path, expected):
    require(path.is_file() and not path.is_symlink(), 'archive is missing or is a symlink')
    require(path.stat().st_size == expected['archive_bytes'], 'archive byte length differs')
    require(file_sha(path) == expected['archive_sha256'], 'archive checksum differs')


def download_archive(root, expected):
    """Use the existing Actions job credential only with fixed GitHub API routes."""
    require(expected == PIN, 'download is restricted to the approved artifact')
    require(os.environ.get('GITHUB_REPOSITORY', REPOSITORY) == REPOSITORY,
            'workflow repository differs')
    target = local(root, WORK + '/archive.zip')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        verify_archive(target, expected)
        return target
    route = f'repos/{REPOSITORY}/actions/artifacts/{expected["artifact_id"]}'
    metadata = subprocess.run(['gh', 'api', '--hostname', 'github.com', route],
        capture_output=True, check=True, timeout=60)
    require(len(metadata.stdout) <= 1024**2, 'oversized GitHub artifact metadata')
    info = json_value(metadata.stdout)
    require(info.get('id') == expected['artifact_id'] and info.get('name') == expected['artifact_name']
            and (info.get('workflow_run') or {}).get('id') == expected['run_id']
            and info.get('size_in_bytes') == expected['archive_bytes']
            and info.get('expired') is False, 'GitHub artifact identity, size, run or expiry differs')
    if info.get('digest') is not None:
        require(info['digest'] == 'sha256:' + expected['archive_sha256'], 'GitHub artifact digest differs')
    # No arbitrary URL, archive-supplied command or redirected authorization
    # header is constructed here. gh handles its normal authenticated API flow.
    descriptor = {k: info.get(k) for k in ('id', 'name', 'size_in_bytes', 'digest', 'expired', 'created_at')}
    descriptor['workflow_run_id'] = expected['run_id']
    importer.write_json(local(root, WORK + '/github-artifact-metadata.json'), descriptor)
    fd, temporary = tempfile.mkstemp(prefix='archive-', suffix='.zip.part', dir=target.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as stream:
            subprocess.run(['gh', 'api', '--hostname', 'github.com', route + '/zip'],
                stdout=stream, check=True, timeout=900)
            stream.flush()
            os.fsync(stream.fileno())
        verify_archive(temporary, expected)
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


class CheckedArchive:
    def __init__(self, path, expected):
        verify_archive(path, expected)
        self.zip = zipfile.ZipFile(path)
        try:
            entries = self.zip.infolist()
            require(len(entries) <= MAX_MEMBERS, 'too many ZIP entries')
            require(sum(item.file_size for item in entries) <= MAX_ARCHIVE_UNCOMPRESSED,
                    'ZIP expanded size exceeds the recovery budget')
            self.members = {}
            for item in entries:
                name = safe_name(item.filename)
                require(name not in self.members, 'duplicate ZIP path ' + name)
                mode = stat.S_IFMT(item.external_attr >> 16)
                require(mode in (0, stat.S_IFREG, stat.S_IFDIR), 'unsafe ZIP file type ' + name)
                require(not item.flag_bits & 1, 'encrypted ZIP entry ' + name)
                require(item.is_dir() == (mode == stat.S_IFDIR) or mode == 0 or
                        (not item.is_dir() and mode == stat.S_IFREG), 'inconsistent ZIP file type')
                self.members[name] = item
        except BaseException:
            self.zip.close()
            raise

    def close(self):
        self.zip.close()

    def read(self, relative, limit=MAX_OBJECT_BYTES):
        name = safe_name(relative)
        item = self.members.get(name)
        require(item is not None and not item.is_dir() and item.file_size <= limit,
                'missing or oversized ZIP source member ' + name)
        with self.zip.open(item) as stream:
            data = stream.read(limit + 1)
        require(len(data) == item.file_size and len(data) <= limit, 'ZIP member size differs')
        return data


def uncompress(stored, limit=MAX_OBJECT_BYTES):
    with gzip.GzipFile(fileobj=io.BytesIO(stored)) as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'gzip source exceeds object limit')
    return raw


def evidence_bytes(read, evidence, kind, slug=None):
    require(isinstance(evidence, dict), 'source evidence must be an object')
    digest, stored_digest = evidence.get('sha256'), evidence.get('stored_sha256')
    require(isinstance(digest, str) and HEX.fullmatch(digest)
            and isinstance(stored_digest, str) and HEX.fullmatch(stored_digest), 'full source hashes required')
    expected = (f'{importer.IMPORT}/parsed/{slug}/{digest}.json.gz' if kind == 'parsed'
                else f'{importer.IMPORT}/raw/{digest}.html.gz')
    require(evidence.get('path') == expected and evidence.get('compression') == 'gzip',
            'source hash/path/compression binding differs')
    stored = read(expected)
    require(sha(stored) == stored_digest, 'stored source hash differs: ' + expected)
    raw = uncompress(stored)
    require(sha(raw) == digest, 'uncompressed source hash differs: ' + expected)
    for key, actual in (('bytes', len(raw)), ('stored_bytes', len(stored))):
        if key in evidence:
            require(evidence[key] == actual, 'source byte length differs: ' + expected)
    return stored, raw


def checked_entry(key, entry, read, inventories):
    require(isinstance(entry, dict), 'imported entry is not an object')
    slug, number = entry.get('collection'), entry.get('number')
    require(slug in importer.BOOKS and isinstance(number, str)
            and re.fullmatch(r'[A-Za-z0-9._-]+', number) and key == slug + ':' + number,
            'source-local entry identity differs')
    require(number in inventories.get(slug, {}).get('identifiers', []),
            'source-local entry is absent from the current observed inventory: ' + key)
    parsed_stored, parsed_raw = evidence_bytes(read, entry['parsed'], 'parsed', slug)
    saved = json_value(parsed_raw)
    require(saved.get('schema') == 'deenhindi-source-record-v1'
            and saved.get('collection') == slug and saved.get('number') == number,
            'parsed source identity differs: ' + key)
    snapshot = saved['snapshot']
    url = f'https://deenhindi.com/hadith/{slug}/{number}'
    require(snapshot.get('url') == url and snapshot.get('final_url', url) == url
            and snapshot.get('status') == 200, 'saved response identity/status differs: ' + key)
    raw_stored, raw = evidence_bytes(read, snapshot, 'raw')
    source, citation = importer.parse_record(raw, slug, number)
    require(source == saved.get('source_record') and citation == saved.get('source_reference_verbatim'),
            'current parser disagrees with saved source object/reference: ' + key)
    return saved, {entry['parsed']['path']: parsed_stored, snapshot['path']: raw_stored}


def install_immutable(root, relative, data):
    """Atomically create missing source objects; partial writes never become sources."""
    path = local(root, relative)
    if path.exists():
        require(path.is_file() and path.read_bytes() == data, 'immutable source collision: ' + relative)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = local(root, WORK + '/object-stage')
    staging.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='object-', dir=staging)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
            return True
        except FileExistsError:
            require(path.is_file() and path.read_bytes() == data, 'immutable source collision: ' + relative)
            return False
    finally:
        temporary.unlink(missing_ok=True)


def source_state(root):
    raw = read_local(root, importer.IMPORT + '/state.json')
    state = json_value(raw)
    require(state.get('schema') == 'deenhindi-import-state-v1' and isinstance(state.get('imported'), dict),
            'current source state is invalid')
    inventory = json_value(read_local(root, importer.IMPORT + '/inventory.json'))
    require(isinstance(inventory, dict), 'current source inventory is invalid')
    return state, inventory, raw


def replace_generated_directory(root, relative, files):
    """Replace this job's exact artifact set, omitting obsolete held evidence."""
    require(relative in (DELTA, HELD), 'unexpected generated artifact directory')
    destination = local(root, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=destination.name + '-new-', dir=destination.parent))
    backup = None
    try:
        for name, data in files.items():
            path = temporary / safe_name(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        if destination.exists():
            require(destination.is_dir(), 'generated artifact path is not a directory')
            backup = Path(tempfile.mkdtemp(prefix=destination.name + '-old-', dir=destination.parent))
            backup.rmdir()
            destination.rename(backup)
        try:
            temporary.rename(destination)
        except BaseException:
            if backup is not None:
                backup.rename(destination)
                backup = None
            raise
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        if backup is not None:
            shutil.rmtree(backup)


def controls(state):
    return {key: value for key, value in state.items() if key != 'imported'}


def receipt(root, expected):
    path = local(root, RECEIPT_PATH)
    if not path.exists():
        return None
    value = json_value(read_local(root, RECEIPT_PATH))
    require(value.get('schema') == 'deenhindi-artifact-recovery-receipt-v1'
            and value.get('recovery_id') == RECOVERY_ID and value.get('artifact') == expected
            and value.get('status') in ('prepared', 'sources_restored', 'derivatives_validated'),
            'recovery receipt identity or state differs')
    return value


def write_receipt(root, value):
    importer.write_json(local(root, RECEIPT_PATH), value)


def index_bytes(root, journal):
    descriptor = journal['verified_index']
    require(descriptor['path'] == INDEX_PATH and descriptor['compression'] == 'gzip', 'unsafe index path')
    stored = read_local(root, INDEX_PATH)
    require(sha(stored) == descriptor['stored_sha256'], 'verified archive index storage hash differs')
    raw = uncompress(stored, MAX_STATE_BYTES)
    require(sha(raw) == descriptor['sha256'], 'verified archive index hash differs')
    value = json_value(raw)
    require(value.get('schema') == 'deenhindi-verified-archive-index-v1'
            and value.get('artifact') == journal['artifact'], 'verified archive index identity differs')
    return value


def current_compatible(state, imported, expected):
    common = set(state['imported']) & set(imported)
    missing = set(imported) - set(state['imported'])
    require(len(imported) == expected['archive_imported_entries'], 'archived imported count differs')
    require(len(common) >= expected['minimum_common_entries']
            and len(missing) <= expected['maximum_missing_entries'], 'current baseline/delta exceeds approved scope')
    for key in common:
        require(state['imported'][key] == imported[key], 'common imported entry differs: ' + key)
    for key in missing:
        require(key not in state.get('errors', {}), 'recovery would overlap a current source error: ' + key)
        attempts = state.get('reviewed_error_attempts', {})
        require(not any(value.get('key') == key for value in attempts.values()),
                'recovery would overlap current retry control state: ' + key)
    return sorted(common), sorted(missing)


def restore(root, expected, archive=None, archive_provider=None, before_status=None):
    """Pure local recovery transaction after archive acquisition; caller supplies pin."""
    root = root.resolve()
    with importer.importer_lock(root):
        state, inventories, state_raw = source_state(root)
        journal = receipt(root, expected)
        current_read = lambda name: read_local(root, name, MAX_OBJECT_BYTES)
        archive_index = index_bytes(root, journal) if journal else None
        # A validated durable index permits network-free replay. Missing source
        # objects still require the exact pinned archive; corruption never does.
        all_local = False
        if archive_index:
            _, missing = current_compatible(state, archive_index['imported'], expected)
            all_local = not missing
            for key, entry in archive_index['imported'].items():
                paths = (entry['parsed']['path'], archive_index['snapshots'][key]['path'])
                if not all(local(root, name).is_file() for name in paths):
                    all_local = False
                    continue
                saved, _ = checked_entry(key, entry, current_read, inventories)
                require(saved['snapshot'] == archive_index['snapshots'][key], 'snapshot receipt differs: ' + key)
            if all_local:
                required = journal['status'] != 'derivatives_validated'
                if journal['status'] == 'prepared':
                    journal.update(status='sources_restored', imported_after=len(state['imported']))
                    write_receipt(root, journal)
                return {'checkpoint_required': required, 'new_entries_this_attempt': 0,
                        'recovered_entries': len(journal['recovered_keys']), 'receipt': journal}
        if archive is None:
            require(archive_provider is not None, 'exact archive required for missing source objects')
            archive = archive_provider()
        checked = CheckedArchive(Path(archive), expected)
        try:
            archive_state_raw = checked.read(importer.IMPORT + '/state.json', MAX_STATE_BYTES)
            archived = json_value(archive_state_raw)
            require(archived.get('schema') == 'deenhindi-import-state-v1'
                    and isinstance(archived.get('imported'), dict), 'invalid archived source state')
            imported = archived['imported']
            common, missing = current_compatible(state, imported, expected)
            snapshots, objects = {}, {}
            # The temporary spool is ignored, bounded to missing objects, and is
            # not an extraction of arbitrary archive paths.
            spool = local(root, WORK + '/verified-spool')
            spool.mkdir(parents=True, exist_ok=True)
            total_missing_bytes = 0
            for key, entry in imported.items():
                saved, source_objects = checked_entry(key, entry, checked.read, inventories)
                snapshots[key] = saved['snapshot']
                for relative, data in source_objects.items():
                    path = local(root, relative)
                    if path.exists():
                        require(path.is_file() and path.read_bytes() == data,
                                'existing immutable source differs: ' + relative)
                    elif relative not in objects:
                        total_missing_bytes += len(data)
                        require(total_missing_bytes <= MAX_DELTA_BYTES, 'missing source byte budget exceeded')
                        staged = spool / sha(relative.encode())
                        importer.atomic(staged, data)
                        objects[relative] = {'spool': staged, 'sha256': sha(data)}
            index = {'schema': 'deenhindi-verified-archive-index-v1', 'artifact': expected,
                     'archive_state_sha256': sha(archive_state_raw), 'imported': imported, 'snapshots': snapshots}
            if archive_index:
                require(index == archive_index, 'replayed archive index differs')
                require(set(missing) <= set(journal['recovered_keys']), 'new replay keys outside prepared transaction')
            else:
                index_raw = importer.json_bytes(index)
                index_stored = gzip.compress(index_raw, mtime=0)
                install_immutable(root, INDEX_PATH, index_stored)
                journal = {'schema': 'deenhindi-artifact-recovery-receipt-v1', 'recovery_id': RECOVERY_ID,
                    'artifact': expected, 'status': 'prepared', 'common_entries_verified': len(common),
                    'imported_before': len(state['imported']), 'source_state_before_sha256': sha(state_raw),
                    'preserved_control_state_sha256': sha(importer.json_bytes(controls(state))),
                    'recovered_keys': missing, 'verified_index': {'path': INDEX_PATH, 'compression': 'gzip',
                        'sha256': sha(index_raw), 'stored_sha256': sha(index_stored)},
                    'before_status': before_status,
                    'scope': 'Only missing immutable Deen snapshots and imported entries; no archive control state or derivatives adopted.'}
                write_receipt(root, journal)
            # No source or state mutation starts until every archived/common
            # entry and every existing destination has passed complete checks.
            for relative, item in objects.items():
                data = item['spool'].read_bytes()
                require(sha(data) == item['sha256'], 'verified spool changed')
                install_immutable(root, relative, data)
            latest, _, latest_raw = source_state(root)
            require(latest_raw == state_raw, 'current source state changed during recovery')
            merged = copy.deepcopy(latest)
            for key in missing:
                merged['imported'][key] = imported[key]
            require(controls(merged) == controls(latest), 'recovery altered control state')
            if missing:
                importer.write_json(local(root, importer.IMPORT + '/state.json'), merged)
            journal.update(status='sources_restored', imported_after=len(merged['imported']))
            write_receipt(root, journal)
            return {'checkpoint_required': True, 'new_entries_this_attempt': len(missing),
                    'recovered_entries': len(journal['recovered_keys']), 'receipt': journal}
        finally:
            checked.close()


def offline_rebuild(root, expected):
    """A fixed zero-request importer run; a retained block is valid source state."""
    root = root.resolve()
    with importer.importer_lock(root):
        state, _, before = source_state(root)
        journal = receipt(root, expected)
        require(journal is not None, 'recovery receipt missing before offline rebuild')
        index = index_bytes(root, journal)
        _, missing = current_compatible(state, index['imported'], expected)
        require(not missing, 'recovered entries missing before offline rebuild')
        # The regular CLI exits 2 for an existing block even after a successful
        # rebuild. Invoke the same engine with a fixed zero request budget and
        # preserve that block; exceptions still prevent validation/publication.
        summary = importer.run(SimpleNamespace(root=root, max_records=0, delay_seconds=1.25,
            timeout_seconds=30, max_seconds=600, retry_errors=False))
        require(read_local(root, importer.IMPORT + '/state.json') == before,
                'offline rebuild altered source/control state')
        proof = {'schema': 'deenhindi-recovery-offline-rebuild-v1', 'recovery_id': RECOVERY_ID,
            'source_state_sha256': sha(before), 'verified_index_sha256': journal['verified_index']['sha256'],
            'progress_sha256': sha(read_local(root, importer.IMPORT + '/progress.json')),
            'importer_sha256': file_sha(Path(importer.__file__)),
            'max_records': 0, 'imported_count': summary['imported_count']}
        importer.write_json(local(root, WORK + '/offline-rebuild.json'), proof)
        return {'imported_count': summary['imported_count'], 'max_records': 0,
                'existing_block_preserved': bool(state.get('blocked'))}


def report(root, expected):
    """Export only this transaction's exact source rows and current held subset."""
    root = root.resolve()
    with importer.importer_lock(root):
        state, inventories, state_raw = source_state(root)
        journal = receipt(root, expected)
        require(journal is not None, 'recovery receipt missing')
        index = index_bytes(root, journal)
        current_compatible(state, index['imported'], expected)
        require(set(index['imported']) <= set(state['imported']), 'recovered entries still missing')
        progress = json_value(read_local(root, importer.IMPORT + '/progress.json'))
        diagnostic = json_value(read_local(root, '.work/web-import-batch/status.json'))
        proof = json_value(read_local(root, WORK + '/offline-rebuild.json'))
        require(proof.get('schema') == 'deenhindi-recovery-offline-rebuild-v1'
                and proof.get('recovery_id') == RECOVERY_ID and proof.get('max_records') == 0
                and proof.get('source_state_sha256') == sha(state_raw)
                and proof.get('verified_index_sha256') == journal['verified_index']['sha256']
                and proof.get('importer_sha256') == file_sha(Path(importer.__file__))
                and proof.get('progress_sha256') == sha(read_local(root, importer.IMPORT + '/progress.json')),
                'current offline rebuild receipt differs')
        from web_import_batch import has_review_export_work
        require(progress.get('imported_count') == len(state['imported'])
                and diagnostic.get('validation_state') == 'passed'
                and progress.get('source_review_engine_sha256') == importer.SourceReviews(root, 'deenhindi').engine_sha256
                and not has_review_export_work(root, 'deenhindi'), 'current offline rebuild/registry not validated')
        recovered = set(journal['recovered_keys'])
        rows, objects = {}, {}
        current_read = lambda name: read_local(root, name, MAX_OBJECT_BYTES)
        for key in sorted(recovered):
            saved, files = checked_entry(key, index['imported'][key], current_read, inventories)
            saved['parsed_path'] = index['imported'][key]['parsed']['path']
            rows[key] = saved
            objects.update(files)
        held = {}
        for slug in importer.BOOKS:
            path = local(root, importer.IMPORT + '/staged/' + slug + '.jsonl')
            require(path.is_file(), 'current staged source file missing: ' + slug)
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    value = json_value(line)
                    key = value['collection'] + ':' + value['number']
                    if key not in recovered:
                        continue
                    require(key not in held and value['source_record'] == rows[key]['source_record']
                            and value['snapshot'] == rows[key]['snapshot']
                            and value['source_reference_verbatim'] == rows[key]['source_reference_verbatim']
                            and value['parsed_path'] == rows[key]['parsed_path'], 'staged row differs from exact source: ' + key)
                    held[key] = value
        # The delta carries every recovered exact source object and its state
        # descriptor. The separately bounded review bundle includes immutable
        # HTML/parsed bytes only for this recovery's currently held rows.
        held_objects = {}
        for key in held:
            for relative in (rows[key]['parsed_path'], rows[key]['snapshot']['path']):
                held_objects[relative] = objects[relative]
        held_rows = importer.rows_bytes(list(held.values()))
        held_entries = importer.json_bytes({key: index['imported'][key] for key in sorted(held)})
        held_bytes = len(held_rows) + len(held_entries) + sum(map(len, held_objects.values()))
        require(held_bytes <= MAX_HELD_BYTES, 'held review evidence byte budget exceeded')
        summary = {'schema': 'deenhindi-artifact-recovery-delta-v1', 'recovery_id': RECOVERY_ID,
            'artifact': expected, 'source_receipt_path': RECEIPT_PATH,
            'recovered_entries': len(rows), 'held_recovered_entries': len(held),
            'current_imported_entries': len(state['imported']), 'current_progress_sha256': sha(importer.json_bytes(progress)),
            'current_review_engine_sha256': progress.get('source_review_engine_sha256'),
            'current_importer_sha256': file_sha(Path(importer.__file__)),
            'held_evidence_source_bytes': held_bytes,
            'held_keys': sorted(held), 'source_identity_sha256': {key: sha(importer.json_bytes(value['source_record']))
                                                               for key, value in rows.items()},
            'source_snapshots_preserved': True, 'new_requests_made_by_recovery': 0,
            'source_controls_imported_from_archive': False, 'independent_pro_qc': 'not_performed'}
        require(sum(map(len, objects.values())) <= MAX_DELTA_BYTES, 'delta source byte budget exceeded')
        journal.update(status='derivatives_validated', rebuilt_imported_count=len(state['imported']),
                       held_recovered_entries=len(held), held_keys=sorted(held),
                       recovery_delta_summary_sha256=sha(importer.json_bytes(summary)))
        held_manifest = {
            'schema': 'deenhindi-recovered-held-evidence-v1', 'held_keys': sorted(held),
            'source_record_sha256': {key: summary['source_identity_sha256'][key] for key in sorted(held)},
            'files': {relative: {'sha256': sha(data), 'bytes': len(data)}
                      for relative, data in sorted(held_objects.items())},
            'maximum_source_bytes': MAX_HELD_BYTES, 'total_source_bytes': held_bytes}
        replace_generated_directory(root, DELTA, {
            'recovered-source-records.jsonl.gz': gzip.compress(importer.rows_bytes(list(rows.values())), mtime=0),
            'held-source-records.jsonl': held_rows,
            'recovered-state-entries.json': importer.json_bytes({key: index['imported'][key] for key in sorted(recovered)}),
            'summary.json': importer.json_bytes(summary), 'recovery-receipt.json': importer.json_bytes(journal)})
        replace_generated_directory(root, HELD, {
            'held-source-records.jsonl': held_rows, 'held-state-entries.json': held_entries,
            'summary.json': importer.json_bytes(summary), 'evidence-manifest.json': importer.json_bytes(held_manifest),
            **{'sources/' + name: data for name, data in held_objects.items()}})
        write_receipt(root, journal)
        return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--archive', type=Path, help='Already downloaded exact pinned ZIP; its size/digest are still required')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--report', action='store_true', help='Create the small delta after current offline rebuild and registry validation')
    mode.add_argument('--offline-rebuild', action='store_true', help='Run the current importer with a fixed zero request budget, preserving blocks')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    require((root / 'AGENTS.md').is_file(), '--root must identify the bank repository')
    plan = load_plan(root)
    if plan is None:
        result = {'checkpoint_required': False, 'reason': 'fixed recovery plan is absent or disabled'}
    elif args.report:
        result = report(root, PIN)
    elif args.offline_rebuild:
        result = offline_rebuild(root, PIN)
    else:
        from web_import_batch import summarize
        web_plan = json_value(read_local(root, 'catalog/web-import-plan.json'))
        before = summarize(root, web_plan)
        result = restore(root, PIN, args.archive, lambda: download_archive(root, PIN), before_status=before)
        if result['checkpoint_required']:
            prior = result['receipt'].get('before_status')
            require(isinstance(prior, dict), 'pre-recovery continuation receipt missing')
            before_path = local(root, '.work/web-import-batch/before-status.json')
            if before_path.exists():
                require(json_value(before_path.read_bytes()) == prior, 'existing before-batch receipt differs')
            else:
                importer.write_json(before_path, prior)
        result = {key: value for key, value in result.items() if key != 'receipt'}
    if not args.report and not args.offline_rebuild and os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write('checkpoint_required=' + str(result['checkpoint_required']).lower() + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
