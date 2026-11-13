"""Bind the complete actual reading set before creating any candidate ledger."""
from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
files=sorted(R.glob('source-first-notes-*.json'))
assert len(files)==9
fields=[]
for p in files:
 d=json.loads(p.read_text()); assert not d['candidate_authored']
 fields.extend(d['fields'])
packets=[R/'input/full-hi-ur-reading-input-60.jsonl',R/'input/additional2773-2774-originals-6.jsonl']
originals=[r for p in packets for r in map(json.loads,p.read_text().splitlines())]
key=lambda x:(x['occurrence_id'],x['language'])
assert len(fields)==len(originals)==66
assert {key(x) for x in fields}=={key(x) for x in originals}
assert len({key(x) for x in fields})==66
by={key(x):x for x in originals}
for x in fields:
 y=by[key(x)]
 assert x['complete_own_field_read'] and x['text_sha256']==sha(y['text'].encode())
 assert x['source_record_sha256']==y['source_record_sha256']
assert not list(R.glob('delivery-manifest*.json'))
result={'schema':'complete-source-first-reading-receipt-v1','reader':'/root/checkpoint_inventory','source_commit':'64f4ed50ed6026855237a5d547a86dd03e73f804','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_created_or_inspected':False,'complete_read_fields':66,'complete_read_characters':sum(x['characters'] for x in fields),'complete_read_utf8_bytes':sum(x['utf8_bytes'] for x in fields),'language_counts':{lang:sum(x['language']==lang for x in fields) for lang in ('hi','ur','ar','en','ur-Latn')},'input_bindings':[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in packets],'batch_bindings':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files],'own_source_verification_sha256':sha((R/'input/own-source-verification.json').read_bytes()),'fields':fields,'scope':'Actual complete source-language readings only; candidate boundaries and structural validation follow separately. No source-site requests or external/canonical identity inference.'}
p=R/'source-first-complete-reading.json';assert not p.exists()
raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();p.write_bytes(raw)
print(json.dumps({'path':str(p),'sha256':sha(raw),'fields':len(fields),'characters':result['complete_read_characters'],'utf8_bytes':result['complete_read_utf8_bytes']}))
