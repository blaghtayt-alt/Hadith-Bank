#!/usr/bin/env python3
"""Export saved Fawaz review inputs through a source-preserving publication gate.

This entry point is additive: without catalog/fawaz-review-inputs.json it does
nothing. It never downloads sources. Git must already contain the pinned
published baseline, or the caller must supply its previously verified snapshot
and an explicit SHA-256. All export/audit work happens in a private staging
directory before any generated checkout path changes.
"""
from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile

import import_fawaz_bulk as source
import validate_fawaz_sources as validator
from build_reader import parse_json
from fawaz_report_types import REPORT_METADATA_FIELDS
from fawaz_held_dispositions import audit_export_dispositions
from fawaz_review_inputs import load_review_catalog, MANIFEST_PATH, BASELINE_PATH
from fawaz_source_checkpoint import SCHEMA, compare_snapshot, require_preserved, write_snapshot


BASELINE = {
    'source_commit': 'ca5f3f18e682376ce2c91e5f97f4b0d7e24eb4c6',
    'provider_occurrences': 36464, 'registered_occurrences': 29911,
    'held_occurrences': 6553, 'edition_inputs': 31,
}
CONTEXT_ACTIONS = {'source_context_only', 'source_attribution_pending'}
RESERVE_BYTES = 512 * 1024 * 1024
MIN_EXPORT_BYTES = 1024 * 1024 * 1024
INSTALL_MARKER = '.work/fawaz-reviewed-install.json'
OUTPUT_FILES = {'manifest.json', 'source-index.json', 'records.jsonl'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(root, relative):
    """Reject links and ambiguous paths even when their current target is local."""
    require(isinstance(relative, str) and relative and '\\' not in relative,
            'Invalid repository path')
    path = PurePosixPath(relative)
    require(not path.is_absolute() and all(part not in ('', '.', '..')
            for part in relative.split('/')), 'Unsafe repository path: ' + relative)
    result = root
    for part in path.parts:
        result = result / part
        require(not result.is_symlink(), 'Symlink path requires inspection: ' + relative)
    require(result.resolve().is_relative_to(root.resolve()), 'Path escapes repository')
    return result


def digest_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                   separators=(',', ':')) + '\n', encoding='utf-8')
    temporary.replace(path)


def event(job, phase, **details):
    value = {'phase': phase, **details}
    write_json(job / 'status.json', value)
    with (job / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=True, separators=(',', ':')) + '\n')
    # Only bounded stage metadata is printed; quotations and full audits stay on disk.
    print(json.dumps(value, ensure_ascii=True, separators=(',', ':'))[:3000], flush=True)


def preflight(path, needed):
    available = shutil.disk_usage(path).free
    require(available >= needed,
            'Insufficient disk space: need ' + str(needed) + ', available ' + str(available))
    return {'required_bytes': needed, 'available_bytes': available}


def input_path(relative):
    path = PurePosixPath(relative)
    return (relative == 'AGENTS.md' or relative.startswith(source.IMPORT + '/')
            or (len(path.parts) >= 2 and path.parts[0] in ('catalog', 'reports')
                and path.parts[1].startswith('fawaz-')))


def baseline_path(relative):
    path = PurePosixPath(relative)
    return input_path(relative) or (len(path.parts) >= 3 and path.parts[0] == 'materials'
                                    and path.parts[1].startswith('fawaz-'))


def git_environment():
    return {**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'GIT_NO_REPLACE_OBJECTS': '1'}


def git_baseline_inventory(root, commit):
    require(re.fullmatch(r'[0-9a-f]{40}', commit) is not None,
            'Baseline must be a complete immutable Git commit ID')
    completed = subprocess.run(['git', '-C', str(root), 'ls-tree', '-rlz', commit, '--',
                                'AGENTS.md', 'catalog', 'reports', source.IMPORT, 'materials'],
                               capture_output=True, check=False, env=git_environment())
    require(completed.returncode == 0,
            'Pinned baseline Git objects are unavailable; checkout must include ' + commit
            + ' or provide a verified --baseline-snapshot and its SHA-256')
    result = {}
    for entry in completed.stdout.split(b'\0'):
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        relative = raw_path.decode('utf-8')
        if not baseline_path(relative):
            continue
        local(root, relative)
        mode, kind, oid, size = metadata.decode('ascii').split()
        require(mode in ('100644', '100755') and kind == 'blob',
                'Baseline contains a nonregular source file: ' + relative)
        result[relative] = {'object': oid, 'bytes': int(size)}
    require('AGENTS.md' in result and BASELINE_PATH in result and source.IMPORT + '/state.json' in result
            and any(name.startswith('materials/') for name in result),
            'Pinned baseline is missing its source/export inventory')
    return result


def restore_baseline(root, destination, inventory, log):
    """Stream immutable Git blobs directly to disk; never extract arbitrary paths."""
    destination.mkdir()
    with log.open('ab') as errors:
        process = subprocess.Popen(['git', '-C', str(root), 'cat-file', '--batch'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=errors, env=git_environment())
        try:
            for relative, descriptor in inventory.items():
                process.stdin.write((descriptor['object'] + '\n').encode('ascii'))
                process.stdin.flush()
                header = process.stdout.readline(256).decode('ascii').strip().split()
                require(header == [descriptor['object'], 'blob', str(descriptor['bytes'])],
                        'Pinned Git blob is unavailable or changed: ' + relative)
                path = local(destination, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                remaining = descriptor['bytes']
                with path.open('xb') as stream:
                    while remaining:
                        chunk = process.stdout.read(min(remaining, 1024 * 1024))
                        require(chunk, 'Truncated pinned baseline blob: ' + relative)
                        stream.write(chunk)
                        remaining -= len(chunk)
                require(process.stdout.read(1) == b'\n', 'Invalid Git blob stream terminator')
            process.stdin.close()
            require(process.wait() == 0, 'Git baseline restoration failed; inspect the job log')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdout.close()
            if not process.stdin.closed:
                process.stdin.close()


def source_files(root):
    result = {}
    candidates = [root / 'AGENTS.md', root / source.IMPORT]
    for parent in ('catalog', 'reports'):
        directory = local(root, parent)
        if directory.exists():
            candidates.extend(directory.glob('fawaz-*'))
    for candidate in candidates:
        relative = candidate.relative_to(root).as_posix()
        local(root, relative)
        if candidate.is_dir():
            paths = candidate.rglob('*')
        else:
            paths = [candidate]
        for path in paths:
            relative = path.relative_to(root).as_posix()
            local(root, relative)
            if path.is_dir():
                continue
            require(path.is_file() and input_path(relative), 'Invalid Fawaz input file: ' + relative)
            result[relative] = {'bytes': path.stat().st_size, 'sha256': digest_file(path)}
    require('AGENTS.md' in result and MANIFEST_PATH in result, 'Missing Fawaz review inputs')
    return result


def copy_inputs(root, stage, inventory):
    stage.mkdir()
    for relative, descriptor in inventory.items():
        path = local(stage, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local(root, relative), path)
        require(path.stat().st_size == descriptor['bytes'] and digest_file(path) == descriptor['sha256'],
                'Source input changed while staging: ' + relative)


def load_baseline_snapshot(path, expected_sha256):
    require(isinstance(expected_sha256, str) and re.fullmatch(r'[0-9a-f]{64}', expected_sha256),
            'A supplied preservation snapshot requires its expected SHA-256')
    require(path.is_file() and path.stat().st_size <= 64 * 1024 * 1024,
            'Missing or excessive preservation snapshot')
    require(digest_file(path) == expected_sha256, 'Preservation snapshot checksum mismatch')
    with (gzip.open(path, 'rb') if path.suffix == '.gz' else path.open('rb')) as stream:
        raw = stream.read(128 * 1024 * 1024 + 1)
    require(len(raw) <= 128 * 1024 * 1024, 'Preservation snapshot expansion is excessive')
    value = parse_json(raw.decode('utf-8'))
    require(value.get('schema') == SCHEMA and value.get('source_revision') == source.REVISION
            and value.get('source_commit') == BASELINE['source_commit'],
            'Preservation snapshot is not bound to the pinned published baseline')
    require(value.get('counts') == {key: BASELINE[key] for key in
            ('provider_occurrences', 'registered_occurrences', 'held_occurrences')},
            'Preservation snapshot has unexpected baseline counts')
    require(len(value['ledger']) == BASELINE['provider_occurrences']
            and len(value['registered_language_fingerprints']) == BASELINE['registered_occurrences'],
            'Preservation snapshot inventory disagrees with baseline counts')
    require(sum(key.startswith('editions/') for key in value['inputs']) == BASELINE['edition_inputs'],
            'Preservation snapshot does not cover all pinned editions')
    return value


def decision_key(decision):
    return (decision['provider_book'], decision['provider_edition'].split('-', 1)[0],
            decision['typed_hadithnumber'])


def supplemental_decisions(root, catalog):
    previous = parse_json(local(root, BASELINE_PATH).read_text(encoding='utf-8'))
    previous_keys = {decision_key(value) for value in previous['decisions']}
    return {decision_key(value): value for value in catalog['decisions']
            if decision_key(value) not in previous_keys}


def verify_projection(audit, supplement, baseline):
    """Independently inspect the written selected spans, metadata and provider set."""
    positives, expected, seen = set(), {}, set()
    for key, decision in supplement.items():
        book, prefix, number = key
        require(decision['provider_edition'] == prefix + '-' + book, 'Review edition identity mismatch')
        positions = audit.groups.get((book, number), {}).get(prefix, [])
        require(len(positions) == 1, 'Review lacks one exact source occurrence: ' + repr(key))
        original = audit.row(book, prefix, positions[0])
        quote, notes, spans = source.apply_reviewed_span(original['text'], decision)
        identifier = validator.identity(book, number)
        positive = decision.get('action') not in CONTEXT_ACTIONS
        if positive:
            positives.add(identifier)
            require(identifier in audit.accepted, 'Reviewed positive provider ID was not registered: ' + identifier)
        if identifier in audit.accepted:
            expected[key] = (quote, notes, spans, positive)
    previous = set(baseline['registered_language_fingerprints'])
    require(set(audit.accepted) == previous | positives,
            'Registered provider IDs differ from the preserved baseline plus saved positive decisions')
    for path in sorted((audit.root / 'materials').glob('fawaz-*/manifest.json')):
        manifest = parse_json(path.read_text(encoding='utf-8'))
        for record in validator.manifest_records(audit.root, manifest):
            own = record['source']['provider_identity']
            for version in record['language_versions']:
                info = version['source']
                key = (own['book'], info['provider_edition'].split('-', 1)[0], own['typed_hadithnumber'])
                if key not in expected:
                    continue
                require(key not in seen, 'Supplemental reading was duplicated')
                seen.add(key)
                quote, notes, spans, positive = expected[key]
                decision = supplement[key]
                require(info['source_text_sha256'] == decision['source_text_sha256']
                        and validator.same(info['text_spans'], spans)
                        and version.get('text') == (quote if positive else None),
                        'Written reading changed its saved review spans: ' + repr(key))
                actual_notes = [item['text'] for item in version.get('comments', []) if item.get('scope')
                                in ('source_compiler_note', 'source_context_not_narration')]
                require(actual_notes == notes, 'Written review notes differ from the selected partition')
                if positive:
                    fields = (*REPORT_METADATA_FIELDS, 'source_report_groups', 'source_report_boundaries',
                              'source_report_alignment_note', 'quotation_kind')
                    require(all(validator.same(info.get(field), decision.get(field)) for field in fields)
                            and info.get('source_report_count') == decision.get('source_report_count', 1),
                            'Written reading changed saved report metadata: ' + repr(key))
                else:
                    kind = 'attribution_pending' if decision['action'] == 'source_attribution_pending' else 'content_mismatch'
                    require(version.get('quotation_status') == kind
                            and info.get('quotation_boundary_reason') == decision['reason'],
                            'Written source-context decision changed its scope or reason')
    require(seen == set(expected), 'A reviewed language reading is absent from the written export')
    return {'supplemental_decisions': len(supplement), 'positive_provider_ids': len(positives),
            'newly_registered_occurrences': len(positives - previous), 'verified_projected_readings': len(seen)}


def owned_materials(root):
    result = set()
    directory = local(root, 'materials')
    if not directory.exists():
        return result
    for path in directory.glob('fawaz-*'):
        relative = path.relative_to(root).as_posix()
        local(root, relative)
        require(path.is_dir(), 'Unrecognized Fawaz material path: ' + relative)
        contents = {child.name for child in path.iterdir()}
        require(contents == OUTPUT_FILES and all(local(root, relative + '/' + name).is_file()
                for name in contents), 'Unexpected files in Fawaz material directory: ' + relative)
        manifest = parse_json((path / 'manifest.json').read_text(encoding='utf-8'))
        index = parse_json((path / 'source-index.json').read_text(encoding='utf-8'))
        book = index.get('provider_book')
        require(book in source.BOOKS and index.get('repository') == source.REPOSITORY
                and index.get('revision') == source.REVISION and manifest.get('id') == path.name
                and manifest.get('schema') == 'hadith-bank-material-v1'
                and path.name.startswith('fawaz-' + book + '-' + source.REVISION[:12] + '-')
                and manifest.get('records', {}).get('path') == relative + '/records.jsonl'
                and manifest.get('source', {}).get('path') == relative + '/source-index.json',
                'Fawaz directory ownership cannot be verified: ' + relative)
        result.add(relative)
    return result


def install_outputs(root, stage, job):
    """Replace only importer-owned outputs, retaining rollback bytes until success."""
    materials = owned_materials(root) | owned_materials(stage)
    paths = sorted(materials) + [source.IMPORT + '/' + name for name in
            ('classification', 'held', 'progress.json', 'source-integrity-validation.json')]
    for relative in paths:
        old, new = local(root, relative), local(stage, relative)
        if relative.endswith(('/classification', '/held')):
            for directory in (old, new):
                if directory.exists():
                    require(directory.is_dir() and all(path.is_file() and not path.is_symlink()
                            and path.name in {book + '.jsonl.gz' for book in source.BOOKS}
                            for path in directory.iterdir()), 'Unrecognized Fawaz generated ledger directory')
        elif relative not in materials:
            require(not old.exists() or old.is_file(), 'Unexpected generated output path')
        require(new.exists() or relative in materials, 'Staged generated output is missing')
    marker = local(root, INSTALL_MARKER)
    require(not marker.exists(), 'An unfinished Fawaz installation requires inspection: ' + str(marker))
    operations = []
    write_json(marker, {'job': str(job), 'status': 'installing', 'paths': paths})
    try:
        for relative in paths:
            destination, candidate = local(root, relative), local(stage, relative)
            backup = local(job / 'backup', relative)
            item = {'path': relative, 'previous': destination.exists(), 'installed': False}
            operations.append(item)
            if item['previous']:
                backup.parent.mkdir(parents=True, exist_ok=True)
                destination.rename(backup)
            if candidate.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                candidate.rename(destination)
                item['installed'] = True
            write_json(job / 'installation.json', operations)
    except BaseException:
        for item in reversed(operations):
            destination = local(root, item['path'])
            backup = local(job / 'backup', item['path'])
            if item['installed']:
                failed = local(job / 'failed-output', item['path'])
                failed.parent.mkdir(parents=True, exist_ok=True)
                destination.rename(failed)
            if backup.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                backup.rename(destination)
        marker.unlink()
        raise
    marker.unlink()
    shutil.rmtree(job / 'backup', ignore_errors=True)


def run(args):
    root = args.root.resolve()
    if not local(root, MANIFEST_PATH).exists():
        return {'status': 'skipped', 'reason': 'No supplemental Fawaz review manifest'}
    require(local(root, 'AGENTS.md').is_file(), '--root must be a Hadith Bank checkout')
    require(not local(root, INSTALL_MARKER).exists(),
            'An interrupted Fawaz installation requires inspection: ' + INSTALL_MARKER)
    require(bool(args.baseline_snapshot) == bool(args.baseline_snapshot_sha256),
            'Supply both --baseline-snapshot and --baseline-snapshot-sha256')
    work = local(root, '.work/fawaz-reviewed-refresh')
    work.mkdir(parents=True, exist_ok=True)
    job = Path(tempfile.mkdtemp(prefix='run-', dir=work))
    try:
        with source.importer_lock(root):
            manifest = parse_json(local(root, MANIFEST_PATH).read_text(encoding='utf-8'))
            require(manifest.get('preservation_baseline') == BASELINE,
                    'Review inputs changed the pinned preservation baseline')
            catalog = load_review_catalog(root, repository=source.REPOSITORY, revision=source.REVISION)
            supplement = supplemental_decisions(root, catalog)
            require(supplement, 'Supplemental review manifest contains no additional decisions')
            inputs = source_files(root)
            owned_materials(root)
            inventory = {} if args.baseline_snapshot else git_baseline_inventory(root, BASELINE['source_commit'])
            baseline_bytes = sum(value['bytes'] for value in inventory.values())
            material_bytes = sum(value['bytes'] for key, value in inventory.items() if key.startswith('materials/'))
            export_budget = max(material_bytes * 2, MIN_EXPORT_BYTES)
            input_bytes = sum(value['bytes'] for value in inputs.values())
            event(job, 'preflight', **preflight(root, baseline_bytes + input_bytes + export_budget + RESERVE_BYTES))
            snapshot = job / 'baseline-snapshot.json.gz'
            if args.baseline_snapshot:
                baseline = load_baseline_snapshot(args.baseline_snapshot, args.baseline_snapshot_sha256)
                shutil.copyfile(args.baseline_snapshot, snapshot)
                # Preserve the supplied compression format for subsequent comparison.
                if args.baseline_snapshot.suffix != '.gz':
                    snapshot.rename(job / 'baseline-snapshot.json')
                    snapshot = job / 'baseline-snapshot.json'
                snapshot_sha = args.baseline_snapshot_sha256
            else:
                event(job, 'restoring_baseline', source_commit=BASELINE['source_commit'], bytes=baseline_bytes)
                previous = job / 'baseline'
                restore_baseline(root, previous, inventory, job / 'git.log')
                audit = validator.SourceAudit(previous)
                previous_result = audit.run()
                require(all(previous_result.get(key) == BASELINE[key] for key in
                        ('provider_occurrences', 'registered_occurrences', 'held_occurrences'))
                        and previous_result.get('verified_edition_snapshots') == BASELINE['edition_inputs'],
                        'Pinned baseline source inventory does not match the approved checkpoint')
                write_json(job / 'baseline-audit.json', previous_result)
                saved = write_snapshot(audit, snapshot, BASELINE['source_commit'])
                snapshot_sha = saved['sha256']
                del audit
                gc.collect()
                baseline = load_baseline_snapshot(snapshot, snapshot_sha)
                shutil.rmtree(previous)
            stage = job / 'candidate'
            copy_inputs(root, stage, inputs)
            plan = source.load_plan(stage)
            state = source.read_json(stage, source.IMPORT + '/state.json')
            expected_inputs = set(source.DOCUMENTS) | {'editions/' + prefix + '-' + book + '.json'
                    for book in plan['books'] for prefix in source.book_languages(plan, book)}
            require(set(state['inputs']) == expected_inputs and sum(key.startswith('editions/')
                    for key in expected_inputs) == BASELINE['edition_inputs'], 'All 31 pinned editions must be present')
            event(job, 'exporting', **preflight(root, export_budget + RESERVE_BYTES))
            export_args = argparse.Namespace(root=stage, export_only=True, fetch=False, adopt_dir=None,
                                            max_books=None, retry_failed=False)
            progress, code = source.run(export_args)
            require(code == 0 and progress['complete'], 'Reviewed source export is incomplete')
            event(job, 'validating_candidate')
            audit = validator.SourceAudit(stage)
            result = audit.run()
            try:
                result['comparison'] = compare_snapshot(audit, snapshot, snapshot_sha)
                require_preserved(result['comparison'])
                result['reviewed_projection'] = verify_projection(audit, supplement, baseline)
                result['held_dispositions'] = audit_export_dispositions(audit)
            except (ValueError, OSError, KeyError, TypeError) as error:
                result['source_integrity_status'] = result.get('status')
                result['status'] = 'failed_preservation_or_projection'
                result['publication_gate_error'] = str(error)
                write_json(job / 'candidate-audit.json', result)
                raise
            write_json(job / 'candidate-audit.json', result)
            summary = {key: value for key, value in result.items() if key != 'comparison'}
            summary['comparison'] = {key: value for key, value in result['comparison'].items()
                                     if not isinstance(value, list)}
            write_json(local(stage, source.IMPORT + '/source-integrity-validation.json'), summary)
            require(source_files(root) == inputs, 'Checkout source inputs changed during the reviewed export')
            event(job, 'installing_verified_output', registered_occurrences=result['registered_occurrences'],
                  newly_registered_occurrences=result['reviewed_projection']['newly_registered_occurrences'])
            install_outputs(root, stage, job)
            shutil.rmtree(stage)
            status = {'status': 'passed', 'job_dir': str(job),
                      'provider_occurrences': result['provider_occurrences'],
                      'previous_registered': result['comparison']['previous_registered'],
                      'registered_occurrences': result['registered_occurrences'],
                      'held_occurrences': result['held_occurrences'], **result['reviewed_projection']}
            event(job, 'complete', **status)
            return status
    except BaseException as error:
        event(job, 'failed', error=str(error)[:500], job_dir=str(job))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline-snapshot', type=Path,
                        help='Previously verified source snapshot bound to the pinned baseline commit')
    parser.add_argument('--baseline-snapshot-sha256', help='Expected SHA-256 of the supplied snapshot')
    args = parser.parse_args(argv)
    try:
        result = run(args)
        if result['status'] == 'skipped':
            print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, IndexError, EOFError) as error:
        print('Fawaz reviewed refresh stopped: ' + str(error)[:500], file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
