"""Read-only display of source segments after a frozen primary handoff."""
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIMARY = ROOT.parent / 'phase21-checkpoint0d2fa-bukhari30-review'
sha = lambda value: hashlib.sha256(value).hexdigest()
receipt = (ROOT / 'complete-independent-source-first-readings.json').read_bytes()
assert sha(receipt) == '409323a027fd5c7bc3c745d82e1b394ceaf976b788d11c0a6c1d833161eb08e7'
manifest_path = Path(sys.argv[1]).resolve()
assert manifest_path.parent == PRIMARY and manifest_path.name.startswith('delivery-manifest-')
manifest_bytes = manifest_path.read_bytes()
assert sha(manifest_bytes) == sys.argv[2]
manifest = json.loads(manifest_bytes)
active_path = 'imports/web-deenhindi-20261112/reviews/source-review-checkpoint0d2fa-bukhari30-20261113.json.gz'
entry = next(row for row in manifest['files'] if row['path'] == active_path)
active = Path(entry['local_path']).read_bytes()
assert sha(active) == entry['sha256'] and len(active) == entry['bytes']
ledger = json.loads(gzip.decompress(active))
by_id = {row.get('occurrence_id', row.get('id')): row for row in ledger['records']}
reading = [json.loads(line) for line in (ROOT / 'input/full-hi-ur-reading-input-60.jsonl').read_bytes().splitlines()]
reading += [json.loads(line) for line in (ROOT / 'input/additional-bukhari2603-originals.jsonl').read_bytes().splitlines()]
start, end = int(sys.argv[3]), int(sys.argv[4])
for row in reading[start:end]:
    decision = by_id[row['occurrence_id']]
    field = next(f for f in decision.get('fields', decision.get('field_reviews')) if f['language'] == row['language'])
    text = row['text']
    print('\n###', row['occurrence_id'], row['language'], len(text), 'CHARS')
    print('FIELD', json.dumps({k: v for k, v in field.items() if k in ('decision', 'speaker', 'report_type', 'source_text_annotations', 'reason', 'reviewed')}, ensure_ascii=False))
    cursor = 0
    for span in field.get('selected_spans', field.get('spans', [])):
        if cursor < span['start']:
            print('CONTEXT', f'[{cursor},{span["start"]})', repr(text[cursor:span['start']]))
        print('SELECTED', f'[{span["start"]},{span["end"]})', repr(text[span['start']:span['end']]))
        print('LABEL', json.dumps({k: v for k, v in span.items() if k not in ('start', 'end', 'sha256', 'reason')}, ensure_ascii=False))
        cursor = span['end']
    if cursor < len(text):
        print('CONTEXT', f'[{cursor},{len(text)})', repr(text[cursor:]))
