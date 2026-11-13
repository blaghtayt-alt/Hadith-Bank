#!/usr/bin/env python3
"""Verify the exact bounded phase15 GitHub publication read-back, without writes upstream."""
from __future__ import annotations

import ast
import base64
import collections
import datetime
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
COMMIT = 'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d'
PARENT = '5589a3ffc3b43c3324ae26f2b6c4d33152834456'
TREE = 'bb937a8efb1fd95128f02b63028f4d25838d9355'
MANIFEST_SHA = 'ca2d2a1425601b797b13c8662f6875f6639d370d77bb71f60a03d2e84de85f17'
REL = Path('reports/web-source-resolution-20261113/phase15-independent-readback')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_hash(kind, raw):
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def data(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def dump(path, value):
    raw = data(value)
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, ('immutable output', str(path))
    else:
        path.write_bytes(raw)


def bind(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': sha(raw), 'git_blob_sha1': git_hash('blob', raw)}


def main():
    inputs = {p.relative_to(HERE).as_posix(): bind(p) for p in sorted((HERE / 'input').rglob('*')) if p.is_file()}
    local_manifest_raw = (HERE / 'input/manifest.json').read_bytes()
    assert sha(local_manifest_raw) == MANIFEST_SHA
    local_manifest = json.loads(local_manifest_raw)
    assert len(local_manifest['files']) == 273
    assert sum(x['bytes'] for x in local_manifest['files']) == 11532317
    authoritative = {x['path']: x for x in local_manifest['files']}
    targets = json.loads((HERE / 'input/targets.json').read_bytes())
    assert len(targets) == 10
    assert targets == [authoritative[x['path']] for x in targets]
    commit = json.loads(json.loads((HERE / 'input/github-commit.json').read_bytes())['content'])
    current_ref = json.loads((HERE / 'input/github-main-ref.json').read_bytes())
    assert commit['sha'] == COMMIT and commit['tree']['sha'] == TREE
    assert [p['sha'] for p in commit['parents']] == [PARENT]
    assert current_ref['ref'] == 'refs/heads/main' and current_ref['object']['sha'] == COMMIT
    root_tree = json.loads(json.loads((HERE / 'input/github-root_tree.json').read_bytes())['content'])
    root_tree['path'] = ''
    trees = [root_tree] + [json.loads(p.read_bytes()) for p in sorted((HERE / 'input').glob('tree-*.json'))]
    assert len(trees) == 9
    trees_by_path = {t['path']: t for t in trees}
    assert len(trees_by_path) == len(trees)
    tree_bindings = []
    for tree in trees:
        assert tree['truncated'] is False
        entries = tree['tree']
        assert len({e['path'] for e in entries}) == len(entries)
        assert all('/' not in e['path'] and '\0' not in e['path'] for e in entries)
        ordered = sorted(entries, key=lambda e: (e['path'] + ('/' if e['type'] == 'tree' else '')).encode())
        raw_tree = b''.join((e['mode'].lstrip('0') + ' ' + e['path']).encode() + b'\0' + bytes.fromhex(e['sha']) for e in ordered)
        assert git_hash('tree', raw_tree) == tree['sha'], tree['path']
        if tree['path']:
            parent, _, name = tree['path'].rpartition('/')
            entry = next(e for e in trees_by_path[parent]['tree'] if e['path'] == name)
            assert entry['type'] == 'tree' and entry['sha'] == tree['sha']
        else:
            assert tree['sha'] == TREE
        tree_bindings.append({'path': tree['path'] or '/', 'git_tree_sha1': tree['sha'],
            'complete_entries': len(entries), 'truncated': False, 'git_tree_object_rehashed': True,
            'serialized_tree_object_sha256': sha(raw_tree), 'serialized_tree_object_bytes': len(raw_tree)})

    files, ledgers, ids, decisions = [], [], set(), collections.Counter()
    for index, target in enumerate(targets):
        response_path = HERE / f'input/file-{index:02d}.json'
        response = json.loads(response_path.read_bytes())
        assert response['encoding'] == 'base64'
        raw = base64.b64decode(response['content'])
        assert len(raw) == target['bytes'] and sha(raw) == target['sha256']
        assert git_hash('blob', raw) == target['git_blob_sha1'] == response['sha']
        assert raw == Path(target['local_path']).read_bytes()
        downloaded = HERE / 'downloaded' / target['path']
        assert downloaded.read_bytes() == raw
        directory, _, filename = target['path'].rpartition('/')
        tree = trees_by_path[directory]
        entry = next(e for e in tree['tree'] if e['path'] == filename)
        assert entry['type'] == 'blob' and entry['sha'] == response['sha']
        assert entry.get('size', len(raw)) == len(raw)
        ancestry = []
        path = directory
        while True:
            ancestry.append({'path': path or '/', 'sha': trees_by_path[path]['sha']})
            if not path:
                break
            path = path.rpartition('/')[0]
        file_result = {'path': target['path'], **bind(downloaded), 'github_blob_sha1': response['sha'],
            'github_url': response['display_url'], 'complete_bytes_match_frozen_payload': True,
            'ancestral_trees': list(reversed(ancestry)), 'response_snapshot_sha256': sha(response_path.read_bytes())}
        if target['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'):
            ledger = json.loads(gzip.decompress(raw))
            rows = ledger.get('records', ledger.get('decisions'))
            count = collections.Counter()
            field_definitions = 0
            for row in rows:
                identity = row.get('id', row.get('occurrence_id'))
                assert identity and identity not in ids, identity
                ids.add(identity)
                decision = row.get('decision', row.get('action'))
                assert decision in ('register', 'exclude')
                count[decision] += 1
                decisions[decision] += 1
                field_definitions += len(row.get('field_reviews', row.get('fields', [])))
            ledger_result = {'path': target['path'], 'sha256': sha(raw), 'occurrences': len(rows),
                'registered': count['register'], 'resolved_source_only': count['exclude'],
                'explicit_field_decisions': field_definitions}
            ledgers.append(ledger_result)
            file_result['semantic_counts'] = ledger_result
        elif target['path'].endswith('current-original3942-priority-field-queue.jsonl.gz'):
            queue_bytes = gzip.decompress(raw)
            queue_rows = [json.loads(line) for line in queue_bytes.splitlines()]
            queue_keys = {(row['id'], field['language']) for row in queue_rows for field in row['fields']}
            queue_languages = collections.Counter(field['language'] for row in queue_rows for field in row['fields'])
            assert len(queue_rows) == len({row['id'] for row in queue_rows}) == 3404
            assert len(queue_keys) == sum(queue_languages.values()) == 6411
            assert queue_languages == {'hi': 3310, 'ur': 3101}
            assert sha(raw) == '343e72455fe122b59b37d795a59f9f8cca2358077723f1c725e4b1eaa3f57227'
            queue_result = {'occurrences': len(queue_rows), 'pending_fields': len(queue_keys),
                'by_language': dict(queue_languages), 'decompressed_sha256': sha(queue_bytes),
                'canonical_combined_queue_verified': True,
                'individual_6451_field_abudawud_candidate_not_at_canonical_path': True}
            file_result['semantic_counts'] = queue_result
        elif target['path'].endswith('.py'):
            ast.parse(raw.decode(), filename=target['path'])
            file_result['python_syntax_parses'] = True
            file_result['test_execution'] = 'not_repeated_in_readback; exact bytes bound to the separately validated publication payload'
        files.append(file_result)

    assert len(ledgers) == 6 and len(ids) == 1230
    assert decisions == {'register': 1201, 'exclude': 29}
    new_ledgers = [x for x in ledgers if 'checkpoint0639' in x['path']]
    assert len(new_ledgers) == 4
    assert sum(x['occurrences'] for x in new_ledgers) == 117
    assert sum(x['registered'] for x in new_ledgers) == 112
    assert sum(x['resolved_source_only'] for x in new_ledgers) == 5
    doc = (HERE / 'downloaded/docs/WEB-SOURCE-RESOLUTION-20261113.md').read_text()
    assert '**112 register and five remain as' in doc
    assert '**6,411 fields across 3,404 occurrences**' in doc
    assert '**3,310 Hindi and\n3,101 Urdu fields**' in doc
    assert '**1,201 registered\nand 29 source-only**' in doc
    assert COMMIT not in doc, 'The prepublication doc must not invent its own future commit.'

    assert inputs == {p.relative_to(HERE).as_posix(): bind(p) for p in sorted((HERE / 'input').rglob('*')) if p.is_file()}
    for target in targets:
        assert bind(Path(target['local_path'])) == {k: target[k] for k in ('bytes', 'sha256', 'git_blob_sha1')}
    report = {'schema': 'hadith-bank-independent-publication-readback-v1', 'status': 'PASS',
        'repository': 'blaghtayt-alt/Hadith-Bank', 'commit_sha': COMMIT, 'parent_sha': PARENT,
        'root_tree_sha': TREE, 'branch_observed_sha': current_ref['object']['sha'],
        'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'publication_manifest_sha256': MANIFEST_SHA,
        'publication_payload_total_files': 273, 'publication_payload_total_bytes': 11532317,
        'independent_content_readback_files': len(files), 'independent_content_readback_bytes': sum(x['bytes'] for x in files),
        'scope': 'Six active Deen review ledgers, the canonical combined priority queue, the status document, the exporter and its focused test file. The complete nine ancestral tree objects were independently fetched and rehashed. This receipt does not claim all273 file bodies were reread.',
        'commit_identity_parent_root_verified_from_github_api': True,
        'raw_commit_object_reconstructed': False,
        'complete_ancestral_tree_objects_verified': len(trees),
        'complete_tree_entries_verified': sum(x['complete_entries'] for x in tree_bindings),
        'all_target_sha256_git_blob_sha1_and_full_bytes_match': True,
        'all_target_paths_bound_through_complete_rehashed_trees': True,
        'six_ledgers_semantic_counts': {'unique_occurrences': len(ids), 'registered': decisions['register'],
            'resolved_source_only': decisions['exclude'], 'duplicate_ids': 0,
            'new_checkpoint0639_occurrences': 117, 'new_checkpoint0639_registered': 112,
            'new_checkpoint0639_resolved_source_only': 5},
        'canonical_priority_queue': queue_result, 'status_doc_current_count_checks_pass': True,
        'source_or_candidate_inputs_mutated': False, 'github_writes_performed': False,
        'source_site_requests_performed': False, 'additional_linguistic_readings_claimed': 0,
        'live_deployment_verified': False, 'native_engine_execution_repeated': False,
        'prior_combined_native_validation': {
            'repo_report_path': 'reports/web-source-resolution-20261113/phase15-combined1230-native-audit/validation-report.json',
            'sha256': '8e17b7843d4013bb2f56a4db936956c3c241a563ef599b3701860525df8d401c',
            'meaning': 'The exact six downloaded ledger bytes match the staged set previously applied together to1230 complete source baselines; no new source acquisition or linguistic approval is claimed by this readback.'},
        'tree_bindings': tree_bindings, 'files': files, 'ledger_counts': ledgers}
    evidence = {'schema': 'hadith-bank-independent-publication-readback-evidence-v1',
        'commit_sha': COMMIT, 'source': 'Fresh read-only GitHub connector responses at the explicit pinned commit; full file bodies were downloaded with encoding=base64.',
        'commit_metadata': commit, 'observed_main_ref': current_ref,
        'complete_tree_objects': trees, 'input_response_and_manifest_bindings': inputs,
        'target_file_hash_bindings': files}
    out = HERE / 'publish'
    dump(out / REL / 'readback-evidence.json.gz', evidence)
    dump(out / REL / 'readback-receipt.json', report)
    own = out / REL / 'audit_readback.py'
    own.parent.mkdir(parents=True, exist_ok=True)
    if own.exists():
        assert own.read_bytes() == Path(__file__).read_bytes()
    else:
        own.write_bytes(Path(__file__).read_bytes())
    payload = [{'path': p.relative_to(out).as_posix(), 'local_path': str(p.resolve()), **bind(p)}
               for p in sorted(out.rglob('*')) if p.is_file()]
    dump(HERE / 'delivery-manifest.json', {'schema': 'hadith-bank-independent-audit-delivery-v1',
        'status': 'PASS', 'commit_sha': COMMIT, 'output_root': str(out.resolve()),
        'files': payload, 'total_files': len(payload), 'total_bytes': sum(x['bytes'] for x in payload)})
    print(json.dumps({'status': 'PASS', 'manifest': bind(HERE / 'delivery-manifest.json'),
        'report': bind(out / REL / 'readback-receipt.json'), 'files': len(files),
        'downloaded_bytes': sum(x['bytes'] for x in files), 'trees': len(trees),
        'tree_entries': sum(x['complete_entries'] for x in tree_bindings), 'queue': queue_result,
        'payload_files': len(payload), 'payload_bytes': sum(x['bytes'] for x in payload)}, indent=2))


if __name__ == '__main__':
    main()
