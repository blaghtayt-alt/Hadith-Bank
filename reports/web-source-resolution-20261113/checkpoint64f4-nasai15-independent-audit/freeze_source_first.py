from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
pack=R/'input/full-hi-ur-reading-input-30.jsonl';originals=list(map(json.loads,pack.read_bytes().splitlines()))
files=sorted(R.glob('source-first-notes-*.json'));assert len(files)==3
fields=[f for p in files for f in json.loads(p.read_bytes())['fields']]
key=lambda x:(x['occurrence_id'],x['language'])
assert len(fields)==len({key(x) for x in fields})==30
by={key(x):x for x in originals};assert {key(x) for x in fields}==set(by)
for f in fields:
 assert f['complete_own_field_read'] and not f['primary_candidate_or_semantic_notes_opened_before_reading']
 assert f['text']==by[key(f)]['text'] and sha(f['text'].encode())==f['text_sha256']
result={'schema':'complete-independent-source-first-reading-v1','reader':'/root/checkpoint_inventory','source_commit':'64f4ed50ed6026855237a5d547a86dd03e73f804','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primary_candidate_and_notes_inspected':False,'complete_fields_read':30,'characters_read':sum(x['characters'] for x in fields),'utf8_bytes_read':sum(x['utf8_bytes'] for x in fields),'original_input_sha256':sha(pack.read_bytes()),'independent_source_proof_sha256':sha((R/'input/own-source-verification.json').read_bytes()),'batches':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files],'fields':fields}
assert (result['characters_read'],result['utf8_bytes_read'])==(13448,28971)
p=R/'complete-independent-source-first-readings.json';assert not p.exists();b=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();p.write_bytes(b)
print(json.dumps({'path':str(p),'sha256':sha(b),'complete_fields':30,'characters':13448,'utf8_bytes':28971}))
