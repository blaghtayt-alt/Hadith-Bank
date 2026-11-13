"""Display exact candidate masks only after independent65-field originals were frozen."""
from pathlib import Path
import argparse,gzip,hashlib,json
H=Path(__file__).resolve().parent;P=H.parent/'phase23-checkpoint64f4-abudawud-tirmidhi31-review'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
ap=argparse.ArgumentParser();ap.add_argument('start',type=int);ap.add_argument('stop',type=int);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--active-sha256',required=True);a=ap.parse_args()
ownb=(H/'complete-independent-source-first-readings.json').read_bytes();assert sha(ownb)=='7f529580a2885f5181279d93cd1b09582aeff2ff447fd09fa6e752360ab3c79f';own=json.loads(ownb)
assert own['candidate_or_primary_notes_opened'] is False and own['all_complete_fields_read_before_candidate_inspection'] and own['complete_fields']==65
mb=(P/'delivery-manifest-v1.json').read_bytes();assert sha(mb)==a.manifest_sha256;m=json.loads(mb)
for f in m['files']:
 b=Path(f.get('local_path',f.get('source_path'))).read_bytes();assert len(b)==f.get('bytes',f.get('size_bytes')) and sha(b)==f['sha256']
active=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ab=Path(active.get('local_path',active.get('source_path'))).read_bytes();assert sha(ab)==a.active_sha256
ledger=json.loads(gzip.decompress(ab));ds={r.get('id',r.get('occurrence_id')):r for r in ledger['records']};assert len(ds)==31
out=[]
for r in own['fields']:
 d=ds[r['id']];fields={f['language']:f for f in d.get('field_reviews',d.get('fields'))};f=fields[r['language']];text=r['text']
 assert f['reviewed'] and f['text_sha256']==r['sha256']==sha(text.encode()) and f['chars_reviewed']==len(text) and f['bytes_reviewed']==len(text.encode())
 spans=f.get('spans',f.get('selected_spans',[]));segments=[];cursor=0
 for s in spans:
  start,end=s['start'],s['end'];assert cursor<=start<end<=len(text) and s['sha256']==sha(text[start:end].encode())
  if cursor<start:segments.append({'start':cursor,'end':start,'text':text[cursor:start],'sha256':sha(text[cursor:start].encode()),'selection':'context'})
  segments.append({**s,'text':text[start:end],'selection':'selected'});cursor=end
 if cursor<len(text):segments.append({'start':cursor,'end':len(text),'text':text[cursor:],'sha256':sha(text[cursor:].encode()),'selection':'context'})
 assert ''.join(s['text'] for s in segments)==text
 out.append({'id':r['id'],'language':r['language'],'decision':d['decision'],'reason':f['reason'],'field_report_type':f.get('report_type'),'field_speaker':f.get('speaker'),'text':text,'selected_spans':spans,'segments':segments})
v={'schema':'hadith-bank-exact-candidate-masks-for-independent-comparison-v1','primary_manifest_sha256':sha(mb),'active_sha256':sha(ab),'own_frozen_source_first_sha256':sha(ownb),'fields':out};vb=enc(v);vp=H/'candidate-boundary-view-v1.json'
if vp.exists():assert vp.read_bytes()==vb
else:vp.write_bytes(vb)
print('HASH_AND_ALL65_OWN_SOURCE_MASK_PARTITIONS_PASS',sha(vb))
for i in range(a.start,a.stop):
 r=out[i];print('\nFIELD',i,r['id'],r['language'],'PARENT',r['decision']);print('REASON',r['reason'])
 if r['field_report_type'] or r['field_speaker']:print('FIELD_DESCRIPTOR',r['field_report_type'],r['field_speaker'])
 for cid,info in {s['component_id']:(s['report_type'],s['speaker'],s['source_report_family_id']) for s in r['selected_spans']}.items():print('COMPONENT',cid,json.dumps(info,ensure_ascii=False))
 for s in r['segments']:print(s['selection'].upper(),s['start'],s['end'],s.get('component_id',''),json.dumps(s['text'],ensure_ascii=False))
