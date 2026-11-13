"""Freeze the exact seven-field independent amendment with unchanged v1 evidence."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'publish-v2'
REL = Path('imports/web-deenhindi-20261112/reviews')
EVID = REL / 'checkpoint0639-bukhari43-20261113'
ACTIVE = REL / 'source-review-checkpoint0639-bukhari43-20261113.json.gz'
BEFORE = ROOT / 'publish-v1'
ARCHIVE = EVID / 'independent-boundary-amendment-v2'
REQUEST = ROOT.parent / 'phase15-checkpoint0639-bukhari43-independent-audit/independent-boundary-findings-v1.json'


def sha(data): return hashlib.sha256(data).hexdigest()
def git(data): return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def enc(obj): return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)
def binding(path):
    b = path.read_bytes()
    return {'bytes': len(b), 'sha256': sha(b), 'git_blob_sha1': git(b)}
def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): assert path.read_bytes() == data
    else: path.write_bytes(data)


before_manifest = ROOT / 'delivery-manifest-v1.json'
assert sha(before_manifest.read_bytes()) == '1c2418b2dcd475e247f0fcd2228d1fa29dee631075105bc5b5cc091af01889b5'
for item in read(before_manifest)['files']:
    p = Path(item['local_path'])
    assert all(binding(p)[k] == item[k] for k in ['bytes', 'sha256', 'git_blob_sha1'])
assert sha(REQUEST.read_bytes()) == '231dbdb85b2b6d2a4d9b9b85fd4fa7eb3cf20cd1b2692ad3c7c2162223f5ea1f'
previous, current = read(BEFORE / ACTIVE), read(OUT / ACTIVE)
assert {k:v for k,v in previous.items() if k != 'records'} == {k:v for k,v in current.items() if k != 'records'}
old = {d['id']: d for d in previous['records']}
new = {d['id']: d for d in current['records']}
source = {'deenhindi-' + r['collection'] + ':' + r['number']: r for r in
          map(json.loads, (ROOT / 'input/cohort.jsonl').read_bytes().splitlines())}
changes = {
    ('deenhindi-bukhari:2239', 'hi'): ('remove', 286, 296),
    ('deenhindi-bukhari:2239', 'ur'): ('remove', 247, 259),
    ('deenhindi-bukhari:2244', 'hi'): ('restore', 533, 591),
    ('deenhindi-bukhari:2256', 'hi'): ('remove', 250, 342),
    ('deenhindi-bukhari:2256', 'ur'): ('remove', 228, 318),
    ('deenhindi-bukhari:2261', 'hi'): ('restore', 292, 304),
    ('deenhindi-bukhari:2261', 'ur'): ('restore', 259, 273),
}
details = []
unchanged_fields = unchanged_parents = 0
changed_parent_reasons = []
for identity, before in old.items():
    after = new[identity]
    if before == after: unchanged_parents += 1
    assert {k:v for k,v in before.items() if k not in ['field_reviews', 'reason']} == {
        k:v for k,v in after.items() if k not in ['field_reviews', 'reason']}
    if before['reason'] != after['reason']:
        changed_parent_reasons.append({'id': identity, 'before': before['reason'], 'after': after['reason']})
    final_fields = {f['language']: f for f in after['field_reviews']}
    for field in before['field_reviews']:
        language = field['language']; final = final_fields[language]
        key = (identity, language)
        if key not in changes:
            assert field == final
            unchanged_fields += 1
            continue
        kind, start, end = changes[key]
        text = source[identity]['source_record'][field['source_field']]
        assert field['text_sha256'] == final['text_sha256'] == sha(text.encode())
        for name in ['reviewed', 'chars_reviewed', 'bytes_reviewed', 'language_version_id', 'source_field', 'text_chars']:
            assert field[name] == final[name]
        mask = lambda f: {i for s in f['spans'] for i in range(s['start'], s['end'])}
        first, last = mask(field), mask(final)
        expected = set(range(start, end))
        assert (last-first, first-last) == ((expected, set()) if kind == 'restore' else (set(), expected))
        if identity.endswith(':2244'):
            spans = final['spans']
            added = next(s for s in spans if s['component_id'] == 'report-3')
            assert (added['start'], added['end']) == (533,591)
            assert added['source_report_family_id'] == identity + ':report-2'
            assert added['report_type'] == 'unattributed_abbreviated_collective_report_fragment'
            assert 'Unidentified resumed we-voice' in added['speaker']
            assert not set(range(516,533)) & last
            assert [(s['start'],s['end']) for s in spans if s['component_id'] != 'report-3'] == [
                (s['start'],s['end']) for s in field['spans']]
        if identity.endswith(':2256'):
            assert len({s['component_id'] for s in final['spans']}) == 1
            assert all(s['report_type'] == 'prophetic_prohibition_report' for s in final['spans'])
        details.append({'id': identity, 'language': language, 'action': kind,
                        'start': start, 'end': end, 'text': text[start:end],
                        'text_sha256': sha(text[start:end].encode()), 'characters': end-start,
                        'utf8_bytes': len(text[start:end].encode()), 'source_field_sha256': field['text_sha256'],
                        'before_field_decision_sha256': sha(enc(field)),
                        'after_field_decision_sha256': sha(enc(final))})
assert unchanged_fields == 208 and unchanged_parents == 39 and len(changed_parent_reasons) == 4
receipt = {
    'schema': 'exact-independent-bukhari43-boundary-amendment-v2', 'status': 'PASS',
    'source_commit': '0639af7fd15786284b4c413fced77e38eec8825a',
    'before_manifest_sha256': sha(before_manifest.read_bytes()),
    'before_active_sha256': sha((BEFORE/ACTIVE).read_bytes()),
    'after_active_sha256': sha((OUT/ACTIVE).read_bytes()),
    'independent_request_sha256': sha(REQUEST.read_bytes()),
    'own_original_source_first_receipt_sha256': sha((ROOT/'complete-source-first-reading-receipt.json').read_bytes()),
    'independent_source_first_receipt_sha256': 'ab201199a8051fe974e19c296ba71a4738309901ee8c33956a4009fa58dbc6bb',
    'exact_changed_fields': 7, 'unchanged_field_definitions': 208,
    'unchanged_complete_parent_records': 39, 'source_and_parent_identity_metadata_unchanged': True,
    'registered': 42, 'resolved_source_only': 1, 'complete_fields_read': 89,
    'admitted_fields': 84, 'reviewed_context_fields': 5, 'unread_context_fields': 126,
    'restored_characters': sum(x['characters'] for x in details if x['action']=='restore'),
    'restored_utf8_bytes': sum(x['utf8_bytes'] for x in details if x['action']=='restore'),
    'moved_to_context_characters': sum(x['characters'] for x in details if x['action']=='remove'),
    'moved_to_context_utf8_bytes': sum(x['utf8_bytes'] for x in details if x['action']=='remove'),
    'all_original_v1_files_unchanged': True, 'changes': details,
    'updated_parent_review_explanations': changed_parent_reasons,
    'reason': 'Preserve source-first notes and v1 as before evidence. The exact independently requested seven changes refine source meaning and explanation boundaries; none add translation, external identity, source text or a new parent.',
}
assert receipt['restored_characters'] == 84 and receipt['moved_to_context_characters'] == 204
archive = {
    'previous-active-ledger.json.gz': BEFORE / ACTIVE,
    'previous-source-first-reading-notes.json': BEFORE / EVID / 'source-first-reading-notes.json',
    'previous-manual-reading-and-boundary-specifications.json.gz': BEFORE / EVID / 'manual-reading-and-boundary-specifications.json.gz',
    'previous-source-apparatus-inventory.json.gz': BEFORE / EVID / 'source-apparatus-inventory.json.gz',
    'previous-package-file-manifest.json': BEFORE / EVID / 'package-file-manifest.json',
    'previous-delivery-manifest.json': before_manifest,
    'independent-boundary-findings-v1.json': REQUEST,
}
for name, path in archive.items(): put(OUT / ARCHIVE / name, path.read_bytes())
put(OUT / ARCHIVE / 'amendment-receipt.json', enc(receipt))
put(OUT / EVID / 'finalize_amendment_v2.py', Path(__file__).read_bytes())
portable_path = OUT / EVID / 'package-file-manifest.json'
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file() and path != portable_path:
        files.append({'path': path.relative_to(OUT).as_posix(), **binding(path)})
portable = {'schema': 'hadith-bank-source-review-package-manifest-v2', 'source_commit': receipt['source_commit'],
            'active_review_path': ACTIVE.as_posix(), 'active_review_sha256': receipt['after_active_sha256'],
            'original_v1_retained': True, 'exact_seven_field_amendment': True,
            'files': files, 'manifest_excludes_its_own_recursive_hash': True}
portable_path.write_bytes(enc(portable))
summary = read(OUT / EVID / 'validation-and-coverage-summary.json')
delivered = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        delivered.append({'path': path.relative_to(OUT).as_posix(), 'local_path': str(path),
                          'source_path': str(path), **binding(path)})
manifest = {'schema': 'hadith-bank-source-review-delivery-v2', 'output_root': str(OUT),
            'source_checkpoint': receipt['source_commit'], 'summary': summary, 'files': delivered,
            'active_ledger_sha256': receipt['after_active_sha256'], 'total_files': len(delivered),
            'total_bytes': sum(x['bytes'] for x in delivered),
            'amendment_receipt_sha256': sha(enc(receipt))}
(ROOT / 'delivery-manifest-v2.json').write_bytes(enc(manifest))
print(json.dumps({'manifest_sha256': sha(enc(manifest)), 'active_sha256': receipt['after_active_sha256'],
                  'files': len(delivered), 'bytes': manifest['total_bytes'],
                  'unchanged_fields': unchanged_fields, 'unchanged_parents': unchanged_parents,
                  'restored_characters': receipt['restored_characters'],
                  'restored_utf8_bytes': receipt['restored_utf8_bytes'],
                  'context_characters': receipt['moved_to_context_characters'],
                  'context_utf8_bytes': receipt['moved_to_context_utf8_bytes'],
                  'amendment_receipt_sha256': sha(enc(receipt))}, indent=2))
