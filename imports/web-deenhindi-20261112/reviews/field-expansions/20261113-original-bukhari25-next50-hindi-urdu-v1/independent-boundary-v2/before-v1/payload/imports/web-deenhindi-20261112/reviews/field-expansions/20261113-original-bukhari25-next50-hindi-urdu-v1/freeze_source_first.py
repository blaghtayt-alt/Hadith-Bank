"""Freeze the actual primary50-field reading before any new extension candidate."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (ROOT/'manual_readings.py').exists() and not (ROOT/'delivery-manifest-v1.json').exists()
ib=(ROOT/'input/full-hi-ur-reading-input-50.jsonl').read_bytes();assert sha(ib)=='5c204cde7e73d4195281c8681455016a4ddb635e847c28564cc84ab352b26a1c'
proofb=(ROOT/'input/source-verification.json').read_bytes();assert sha(proofb)=='864a0dcbf04fa261dcd5037590b5800e42d52a71cefe6ac45d1dae4cc93f336e'
proof=json.loads(proofb);assert proof['status']=='PASS' and proof['saved_files_reopened']==50 and proof['complete_raw_reparses']==25
notes={};batches=[];orders=[]
for n in range(1,6):
 p=ROOT/('initial-reading-notes-%02d.json'%n);b=p.read_bytes();j=json.loads(b);assert not j['candidate_authored_or_inspected']
 assert not notes.keys()&j['notes'].keys();notes.update(j['notes']);orders+=j['reading_orders'];batches.append({'path':p.name,'sha256':sha(b),'bytes':len(b)})
assert orders==list(range(1,51)) and len(notes)==25
fields=[]
for r in map(json.loads,ib.splitlines()):
 key=r['collection']+':'+r['number'];text=r['text'];assert sha(text.encode())==r['text_sha256']
 fields.append({'id':r['occurrence_id'],'language':r['language'],'source_field':r['source_field'],'text':text,'sha256':r['text_sha256'],'characters':len(text),'utf8_bytes':len(text.encode()),'complete_field_read':True,'initial_primary_reading_note':notes[key]})
assert len(fields)==50 and sum(f['characters'] for f in fields)==27103 and sum(f['utf8_bytes'] for f in fields)==58879
receipt={'schema':'hadith-bank-complete-primary-source-first-reading-v1','reviewer':'/root','source_commit':'d369026ca42af6ff972ffab83c9180e03759da41','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_extension_candidate_or_peer_notes_inspected':False,'all_full_fields_read_before_candidate_creation':True,'complete_fields':50,'characters':27103,'utf8_bytes':58879,'input_sha256':sha(ib),'source_proof_sha256':sha(proofb),'initial_note_batches':batches,'fields':fields,'coverage_scope':'Only the50 complete Hindi/Urdu fields on these25 existing registered parents were actually read in this primary pass. Existing parent and all unselected field decisions must remain exact. Source-only or all-language review is not asserted. Initial interpretive judgments may be transparently refined after independent review, without rewriting these notes.','independent_pro_qc':'not_performed'}
p=ROOT/'complete-source-first-reading-receipt.json';assert not p.exists();p.write_bytes(enc(receipt))
print(json.dumps({'source_first_sha256':sha(enc(receipt)),'complete_fields':50,'characters':27103,'utf8_bytes':58879,'source_files_verified':50,'raw_reparses':25,'new_candidate_authored':False},indent=2))
