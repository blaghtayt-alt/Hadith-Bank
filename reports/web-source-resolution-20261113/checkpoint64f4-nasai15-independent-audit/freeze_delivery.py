"""Freeze independent original readings, exact refinement and native final evidence."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PREFIX = Path('reports/web-source-resolution-20261113/checkpoint64f4-nasai15-independent-audit')
sha = lambda data: hashlib.sha256(data).hexdigest()
enc = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data
    else:
        path.write_bytes(data)


def binding(path, relative):
    data = path.read_bytes()
    return {'path': str(relative), 'local_path': str(path), 'bytes': len(data), 'size_bytes': len(data),
            'sha256': sha(data),
            'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}


report_raw = (ROOT / 'independent-final-audit.json').read_bytes()
assert sha(report_raw) == 'ef8ce3bce7a6e8191770cc0465ae351b23a15c20e865b0be87de4f726f8db828'
report = json.loads(report_raw)
assert report['status'] == 'PASS' and not report['required_amendments'] and not report['open_findings']
direct = [
    'independent-final-audit.json', 'field-and-source-proof-final.json.gz',
    'audit_final_v2.py', 'verify_original_sources.py', 'show_candidate.py',
    'record_blind_readings.py', 'read_batch_01.py', 'read_batch_02.py', 'read_batch_03.py',
    'freeze_source_first.py', 'freeze_findings.py', 'freeze_delivery.py',
]
compressed = [
    'complete-independent-source-first-readings.json', 'independent-boundary-findings-v1.json',
    'accepted-reviewed-field-plan-v1.json', 'input/own-source-verification.json',
    'input/cohort.jsonl', 'input/full-hi-ur-reading-input-30.jsonl', 'input/selection.json',
    'input/input-delivery-manifest.json', 'input/primary-manifest-v1.json',
    'source-first-notes-01.json', 'source-first-notes-02.json', 'source-first-notes-03.json',
]
files = []
for name in direct:
    relative = PREFIX / name
    target = ROOT / 'publish' / relative
    put(target, (ROOT / name).read_bytes())
    files.append(binding(target, relative))
for name in compressed:
    relative = PREFIX / (name + '.gz')
    target = ROOT / 'publish' / relative
    put(target, gzip.compress((ROOT / name).read_bytes(), mtime=0))
    files.append(binding(target, relative))
final_owner_manifest = ROOT.parent / 'phase23-checkpoint64f4-nasai15-review/delivery-manifest-v2.json'
assert sha(final_owner_manifest.read_bytes()) == report['primary_manifest_sha256']
relative = PREFIX / 'input/primary-manifest-v2.json.gz'
target = ROOT / 'publish' / relative
put(target, gzip.compress(final_owner_manifest.read_bytes(), mtime=0))
files.append(binding(target, relative))
files.sort(key=lambda row: row['path'])
portable = {'schema': 'portable-independent-audit-payload-manifest-v2',
    'source_checkpoint': report['source_checkpoint'],
    'primary_manifest_sha256': report['primary_manifest_sha256'],
    'primary_active_sha256': report['primary_active_sha256'],
    'files': [{k: v for k, v in row.items() if k != 'local_path'} for row in files]}
relative = PREFIX / 'package-file-manifest.json'
target = ROOT / 'publish' / relative
put(target, enc(portable))
files.append(binding(target, relative))
files.sort(key=lambda row: row['path'])
delivery = {'schema': 'independent-review-delivery-manifest-v2', 'status': 'PASS',
    'files': files, 'file_count': len(files), 'total_bytes': sum(row['bytes'] for row in files),
    'report_sha256': sha(report_raw), 'primary_manifest_sha256': report['primary_manifest_sha256'],
    'primary_active_sha256': report['primary_active_sha256'],
    'complete_fields_read': 30, 'characters_read': 13448, 'utf8_bytes_read': 28971,
    'registered_parents': 15, 'resolved_source_only_parents': 0, 'admitted_fields': 30,
    'reviewed_context_fields': 0, 'unread_context_fields': 45, 'lossless_source_partitions': 75,
    'exact_amended_fields': 2, 'characters_moved_to_context': 33, 'utf8_bytes_moved_to_context': 65,
    'unchanged_other_fields': 73, 'unchanged_whole_parents': 14, 'open_findings': []}
put(ROOT / 'delivery-manifest.json', enc(delivery))
for row in files:
    assert binding(Path(row['local_path']), row['path']) == row
print(json.dumps({'manifest': str(ROOT / 'delivery-manifest.json'), 'sha256': sha(enc(delivery)),
                  'files': len(files), 'bytes': delivery['total_bytes'], 'status': 'PASS'}))
