"""Read-only independent composition check of two approved language extensions."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer

QUEUE = 'reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
COMPOSITE_MANIFEST = WORK / 'phase15-original90-combined-queue/delivery-manifest.json'
COMPOSITE_MANIFEST_SHA = 'e1e68f3763806f3141278bef7b7ff2f61e686b5c0d76dc2a73de1bb596da65ba'
BASE_SHA = 'f5fa86ff645098396c7daf978f7491bddff6fd9104f5e50acc72f7d02701a660'
FINAL_SHA = '343e72455fe122b59b37d795a59f9f8cca2358077723f1c725e4b1eaa3f57227'
INPUTS = [
    ('abudawud50', 'phase14-original-abudawud50-urdu/delivery-manifest-v2.json',
     'db63f76f44ee298577960c255ab5298d9c6b96936597ffb3aebca776f1f94bf6',
     '7a1893ac1e838c73b7f4dfa5d4a47ed805b1f5fb82571f633bc86d4804c79f8a', 50),
    ('bukhari40', 'phase14-original-bukhari30-hi-ur/delivery-manifest-v3.json',
     '3f0515c09ffb0739d6db734390c5b98669d2875b0f4e11f1da0fec5aafbb6af0',
     'ac53483e3eab6c0a4c508c86180c75091792e895b5e29f602a061aa2cd080c62', 40)]


def sha(data): return hashlib.sha256(data).hexdigest()
def git(data): return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def enc(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)
def oid(row): return row.get('id', row.get('occurrence_id')) or 'deenhindi-' + row['collection'] + ':' + row['number']
def delivery(path, digest):
    assert sha(path.read_bytes()) == digest
    manifest = read(path)
    bypath = {}
    for item in manifest['files']:
        p = Path(item.get('local_path') or item['source_path'])
        b = p.read_bytes()
        assert not p.is_symlink() and p.resolve().is_relative_to(path.parent.resolve())
        assert sha(b) == item['sha256'] and len(b) == item.get('bytes', item.get('size_bytes'))
        assert not item.get('git_blob_sha1') or git(b) == item['git_blob_sha1']
        assert item['path'] not in bypath
        bypath[item['path']] = (p, item)
    return bypath


def main():
    composed = delivery(COMPOSITE_MANIFEST, COMPOSITE_MANIFEST_SHA)
    final_data = composed[QUEUE][0].read_bytes()
    assert sha(final_data) == FINAL_SHA
    claimed = read(next(p for path, (p, _) in composed.items() if path.endswith('combined-queue-delta.json')))
    claim_by_key = {(r['id'], r['language']): r for r in claimed['removed']}
    assert len(claim_by_key) == len(claimed['removed']) == 90
    pending, baseline_bytes, receipts, bindings = {}, None, [], []
    for name, relative, manifest_sha, active_sha, expected_count in INPUTS:
        files = delivery(WORK / relative, manifest_sha)
        active_path = next(path for path in files if Path(path).parent.as_posix() ==
                           'imports/web-deenhindi-20261112/reviews' and Path(path).name.startswith('source-review'))
        active_local = files[active_path][0]
        assert sha(active_local.read_bytes()) == active_sha
        active = read(active_local)
        records = {oid(r): r for r in active['records']}
        baseline = next(p for path, (p, _) in files.items() if path.endswith('previous-priority-field-queue.jsonl.gz'))
        assert sha(baseline.read_bytes()) == BASE_SHA
        if baseline_bytes is None: baseline_bytes = baseline.read_bytes()
        else: assert baseline_bytes == baseline.read_bytes()
        source_file = next(p for path, (p, _) in files.items() if Path(path).name in ['source-ledger-50.jsonl.gz', 'source-ledger-30.jsonl.gz'])
        source_rows = [json.loads(line) for line in gzip.decompress(source_file.read_bytes()).splitlines()]
        source = {oid(r): r for r in source_rows}
        delta_file = next(p for path, (p, _) in files.items() if path.endswith('/priority-field-queue-delta.json'))
        delta = read(delta_file)
        removed = delta['removed'] if name == 'abudawud50' else delta['removed_fields']
        assert len(removed) == expected_count
        for item in removed:
            identity = item.get('id', item.get('occurrence_id'))
            language = item['field']['language'] if name == 'abudawud50' else item['language']
            key = (identity, language)
            assert key not in pending and key in claim_by_key
            parent = records[identity]
            assert parent['decision'] == 'register'
            field = next(f for f in parent.get('field_reviews', parent.get('fields')) if f['language'] == language)
            original = source[identity]
            text = original['source_record'][field['source_field']]
            record_sha = sha(importer.json_bytes(original['source_record']))
            assert parent['source_record_sha256'] == record_sha
            assert field['text_sha256'] == sha(text.encode()) and field['reviewed'] is True
            assert field['chars_reviewed'] == len(text) and field['bytes_reviewed'] == len(text.encode())
            spans = field.get('spans', field.get('selected_spans', []))
            assert spans
            for span in spans:
                assert sha(text[span['start']:span['end']].encode()) == span['sha256']
            action = field.get('action', field.get('decision'))
            assert action in ['whole', 'excerpts', 'excerpt']
            field_sha = sha(enc(field))
            if name == 'bukhari40':
                assert item['after_field_decision_sha256'] == field_sha and item['after_decision'] == action
            claim = claim_by_key[key]
            assert claim['active_ledger_path'] == active_path and claim['active_ledger_sha256'] == active_sha
            assert claim['final_action'] == action and claim['final_field_decision_sha256'] == field_sha
            assert claim['source_text_sha256'] == field['text_sha256'] and claim['source_record_sha256'] == record_sha
            assert claim['source_field'] == field['source_field'] and claim['package'] == name
            pending[key] = claim
            bindings.append({'id': identity, 'language': language, 'source_record_sha256': record_sha,
                             'source_text_sha256': field['text_sha256'], 'active_ledger_sha256': active_sha,
                             'final_field_decision_sha256': field_sha, 'final_action': action,
                             'reviewed_characters': len(text), 'reviewed_utf8_bytes': len(text.encode()),
                             'selected_span_count': len(spans), 'package': name})
        receipts.append({'package': name, 'manifest_sha256': manifest_sha, 'active_ledger_sha256': active_sha,
                         'source_baseline_sha256': sha(source_file.read_bytes()), 'delta_sha256': sha(delta_file.read_bytes()),
                         'fields': len(removed)})
    assert set(pending) == set(claim_by_key)
    assert len({identity for identity, _ in pending}) == 80
    assert collections.Counter(lang for _, lang in pending) == {'hi': 10, 'ur': 80}
    original_lines = gzip.decompress(baseline_bytes).splitlines(keepends=True)
    remaining, observed = [], set()
    before_fields = 0
    for line in original_lines:
        row = json.loads(line)
        keys = {(row['id'], f['language']) for f in row['fields']}
        before_fields += len(keys)
        matched = keys & set(pending)
        if not matched:
            remaining.append(line)
            continue
        assert matched == keys
        assert row['existing_parent_decision'] == 'register'
        for f in row['fields']:
            key = (row['id'], f['language']); claim = pending[key]
            assert f['text_sha256'] == claim['source_text_sha256']
            assert row['source_record_sha256'] == claim['source_record_sha256']
            assert row['active_review_path'] == claim['active_ledger_path']
            assert sha(line) == claim['original_queue_line_sha256']
            observed.add(key)
    assert observed == set(pending) and before_fields == 6501 and len(original_lines) == 3484
    final_plain = gzip.decompress(final_data)
    assert final_plain == b''.join(remaining)
    assert final_plain.splitlines(keepends=True) == remaining
    after_rows = [json.loads(line) for line in remaining]
    language_counts = collections.Counter(f['language'] for r in after_rows for f in r['fields'])
    assert len(after_rows) == 3404 and sum(language_counts.values()) == 6411
    assert language_counts == {'hi': 3310, 'ur': 3101}
    report = {'schema': 'independent-original90-queue-composition-audit-v1', 'status': 'PASS',
              'composed_manifest_sha256': COMPOSITE_MANIFEST_SHA, 'before_queue_sha256': BASE_SHA,
              'final_queue_sha256': FINAL_SHA, 'input_package_receipts': receipts,
              'before': {'fields': 6501, 'occurrences': 3484},
              'removed': {'fields': 90, 'occurrences': 80, 'hi': 10, 'ur': 80},
              'after': {'fields': 6411, 'occurrences': 3404, 'hi': 3310, 'ur': 3101},
              'all90_exact_final_decision_and_source_hashes_verified': True,
              'all_remaining_json_line_bytes_and_order_exact': True,
              'all80_parent_dispositions_remain_register': True, 'source_occurrence_delta': 0,
              'canonical_queue_path': QUEUE,
              'publisher_staging_requirement': 'Publish only the combined343e queue at the canonical path; archive/remap any standalone Abu6451 queue candidate. This report does not assert the future publication has already done so.',
              'scope': 'Structural source/decision/queue composition only; independent linguistic readings and native whole-ledger validation remain in each primary and its separate independent audit.',
              'new_semantic_decisions': 0, 'source_http_requests': 0, 'github_writes': 0}
    prefix = Path('reports/web-source-resolution-20261113/phase15-original90-combined-queue-independent-audit')
    outputs = {prefix / 'validation-report.json': enc(report),
               prefix / 'per-field-source-and-final-decision-bindings.json.gz': gzip.compress(enc(bindings), mtime=0),
               prefix / 'audit_queue.py': Path(__file__).read_bytes()}
    delivered = []
    for relative, data in outputs.items():
        out = ROOT / 'publish' / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        assert not out.exists()
        out.write_bytes(data)
        delivered.append({'path': relative.as_posix(), 'local_path': str(out), 'bytes': len(data),
                          'sha256': sha(data), 'git_blob_sha1': git(data)})
    manifest = {'schema': 'independent-queue-audit-delivery-v1', 'status': 'PASS', 'files': delivered,
                'total_files': len(delivered), 'total_bytes': sum(x['bytes'] for x in delivered)}
    (ROOT / 'delivery-manifest.json').write_bytes(enc(manifest))
    print(json.dumps({'status': 'PASS', 'manifest_sha256': sha(enc(manifest)), 'report_sha256': sha(enc(report)),
                      'files': len(delivered), 'bytes': manifest['total_bytes']}, indent=2))


if __name__ == '__main__':
    main()
