"""Freeze actual independent field readings before opening the primary candidate."""
from pathlib import Path
import collections,datetime,hashlib,json
ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
files=[ROOT/'input/full-hi-ur-reading-input-44.jsonl',ROOT/'input/additional2636-source-only-input-3.jsonl']
originals={(r['occurrence_id'],r['language']):r for p in files for r in map(json.loads,p.read_bytes().splitlines())}
assert len(originals)==47
fields=[];batches=[];seen=set()
for p in sorted(ROOT.glob('source-first-batch-*.json')):
    raw=p.read_bytes();v=json.loads(raw);assert not v['primary_candidate_opened']
    batches.append({'path':p.name,'sha256':sha(raw),'bytes':len(raw),'complete_fields_read':v['complete_fields_read']})
    for r in v['fields']:
        key=(r['occurrence_id'],r['language']);assert key not in seen;seen.add(key)
        assert r['complete_own_field_read'] and not r['primary_candidate_or_semantic_notes_opened_before_reading']
        assert r['text']==originals[key]['text'] and sha(r['text'].encode())==r['text_sha256']
        assert r['characters']==len(r['text']) and r['utf8_bytes']==len(r['text'].encode())
        fields.append(r)
assert seen==set(originals)
chars=sum(r['characters'] for r in fields);size=sum(r['utf8_bytes'] for r in fields)
assert chars==12443 and size==26863
value={'schema':'independent-complete-source-first-reading-v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_commit':'17cd396eb858a29162505d545aad556ac73ce9ce','primary_candidate_or_semantic_notes_opened':False,
 'actual_complete_fields_read':47,'characters_read':chars,'utf8_bytes_read':size,
 'by_language':dict(collections.Counter(r['language'] for r in fields)),
 'source_inputs':[{'path':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in files],
 'independent_source_verification_sha256':sha((ROOT/'independent-source-verification.json').read_bytes()),
 'source_first_batches':batches,'fields':fields,
 'limits':'Initial source-first judgments are preserved before any candidate inspection; later evidence-based refinements must be recorded separately. No unread siblings are treated as reviewed, and no external canonical identity, source grading or linguistic repair is inferred.'}
p=ROOT/'complete-independent-source-first-readings.json';assert not p.exists();raw=enc(value);p.write_bytes(raw)
print(json.dumps({'path':str(p),'sha256':sha(raw),'fields':47,'characters':chars,'bytes_read':size}))
