"""Read an immutable candidate view against this auditor's own complete originals."""
from pathlib import Path
import argparse
import hashlib
import json

H = Path(__file__).resolve().parent
P = H.parent / 'phase22-checkpoint17cd-abudawud-tirmidhi23-review'
sha = lambda b: hashlib.sha256(b).hexdigest()
args = argparse.ArgumentParser()
args.add_argument('start', type=int)
args.add_argument('stop', type=int)
a = args.parse_args()
manifest_bytes = (P / 'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_bytes) == '147636cd951ff1714315f9b83b13362be327059a80d8361485172422f2a43565'
manifest = json.loads(manifest_bytes)
for f in manifest['files']:
    b = Path(f['local_path']).read_bytes()
    assert len(b) == f['bytes'] and sha(b) == f['sha256']
original_bytes = (H / 'input/full-field-reading-input-46.jsonl').read_bytes()
assert sha(original_bytes) == '1c6567cef512392b28923d0ab271219e07e89d01b723daa87605deacb346f93f'
originals = {(r['occurrence_id'], r['language']): r for r in map(json.loads, original_bytes.splitlines())}
view_bytes = (P / 'boundary-view-v1.json').read_bytes()
view = json.loads(view_bytes)
assert len(view) == len(originals) == 46
assert {(r['id'], r['language']) for r in view} == set(originals)
for row in view:
    text = originals[row['id'], row['language']]['text']
    assert row['text'] == text
    cursor = 0
    segments = sorted(row['selected_spans'] + row['retained_context'], key=lambda s: s['start'])
    for segment in segments:
        assert segment['start'] == cursor and segment['end'] > cursor
        assert segment['text'] == text[segment['start']:segment['end']]
        assert sha(segment['text'].encode()) == segment['sha256']
        cursor = segment['end']
    assert cursor == len(text)
print('PACKAGE_HASH_AND_OWN_ORIGINAL_PARTITIONS_PASS', len(view), sha(view_bytes))
for index in range(a.start, a.stop):
    row = view[index]
    print('\nFIELD', index, row['id'], row['language'])
    print('REASON', row['reason'])
    components = {s['component_id']: (s['report_type'], s['speaker']) for s in row['selected_spans']}
    for key, value in components.items():
        print('COMPONENT', key, json.dumps(value, ensure_ascii=False))
    for segment in sorted(row['selected_spans'] + row['retained_context'], key=lambda s: s['start']):
        print('SELECTED' if 'component_id' in segment else 'CONTEXT', segment['start'], segment['end'],
              segment.get('component_id', ''), json.dumps(segment['text'], ensure_ascii=False))
