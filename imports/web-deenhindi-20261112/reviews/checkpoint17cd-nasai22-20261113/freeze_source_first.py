"""Bind already completed original readings to unchanged full saved sources."""
from pathlib import Path
import datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
INPUT=WORK/'phase22-checkpoint17cd-input-partitions/root-nasai22'
EVID=WORK/'phase21-successor-acquisition-monitor/held-evidence'
PIN='17cd396eb858a29162505d545aad556ac73ce9ce'
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
assert not (ROOT/'source-first-complete-reading.json').exists() and not (ROOT/'manual_rules.py').exists()
mb=(INPUT/'input-delivery-manifest.json').read_bytes();assert sha(mb)=='3919913d9490dc25d87910b04b50a18b211320d04cbb7a5d16e6c5b27a3a4c3c'
manifest=json.loads(mb)
for f in manifest['files']:
 b=Path(f['local_path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes'] and git(b)==f['git_blob_sha1']
cb=(INPUT/'cohort.jsonl').read_bytes();assert sha(cb)=='e606722e94cffde01f011c34bd9cd7dbe53003b8522a1d4f24c8545223f78f17'
ib=(INPUT/'full-hi-ur-reading-input-44.jsonl').read_bytes();assert sha(ib)=='b60efedb67ec47bfcd7950d5760858bcc2e591a3f4c2150c889894d75052422c'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,cb.splitlines())}
notes={};note_files=[];orders=[];history={}
for index in range(1,8):
 p=ROOT/('initial-reading-notes-%02d.json'%index);b=p.read_bytes();d=json.loads(b)
 assert d['source_commit']==PIN and d['input_sha256']==sha(ib) and d['candidate_or_peer_notes_opened'] is False
 for ident,note in d['notes'].items():
  history.setdefault(ident,[]).append({'batch':index,'note':note});notes[ident]=' '.join(entry['note'] for entry in history[ident])
 orders+=d['complete_original_reading_orders']
 note_files.append({'path':p.name,'sha256':sha(b),'bytes':len(b)})
assert orders==list(range(1,48)) and set(notes)=={'deenhindi-'+k for k in sources} and len(sources)==22
entries=json.loads((EVID/'held-state-entries.json').read_bytes())
evidence=json.loads((EVID/'evidence-manifest.json').read_bytes());assert evidence['saved_head']==PIN
proof=[]
for key,r in sources.items():
 files=[]
 for kind,descriptor in [('raw',r['snapshot']),('parsed',entries[key]['parsed'])]:
  b=(EVID/'sources'/descriptor['path']).read_bytes();authority=evidence['files'][descriptor['path']]
  assert sha(b)==authority.get('stored_sha256',authority['sha256']) and git(b)==authority['git_blob_sha1']
  plain=importer.checked_bytes(EVID/'sources',descriptor)
  if kind=='raw':
   obj,ref=importer.parse_record(plain,r['collection'],r['number'])
   assert obj==r['source_record'] and ref==r['source_reference_verbatim']
  else:
   expected={k:r[k] for k in ['schema','collection','number','snapshot','source_reference_verbatim','source_record']}
   expected['classification']=r['intake_classification']
   assert json.loads(plain)==expected and plain==importer.json_bytes(expected)
  files.append({'kind':kind,'path':descriptor['path'],'stored_bytes':len(b),'stored_sha256':sha(b),'git_blob_sha1':git(b),'plain_bytes':len(plain),'plain_sha256':sha(plain)})
 proof.append({'id':'deenhindi-'+key,'files':files,'raw_reparse_exact':True})
fields=[]
additional=(ROOT/'additional2636-source-only-input-3.jsonl').read_bytes();assert sha(additional)=='c7b238656dafcb4aa9f211974942df0da78ddcf8320082dca253a7eb987345f6'
for f in [json.loads(line) for line in ib.splitlines()]+[json.loads(line) for line in additional.splitlines()]:
 key=f['collection']+':'+f['number'];text=f['text']
 assert text==sources[key]['source_record'][f['source_field']] and sha(text.encode())==f['text_sha256']
 if 'source_record_sha256' in f:assert sha(importer.json_bytes(sources[key]['source_record']))==f['source_record_sha256']
 fields.append({'id':f['occurrence_id'],'language':f['language'],'source_field':f['source_field'],'text':text,'sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),'complete_field_read':True,'reading_note':notes[f['occurrence_id']],'initial_note_history':history[f['occurrence_id']],'original_reading_order':f['reading_order']})
assert (len(fields),sum(f['characters'] for f in fields),sum(f['utf8_bytes'] for f in fields))==(47,12443,26863)
receipt={'source_commit':PIN,'reviewer':'/root','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_full_fields_read_before_candidate_creation':True,'candidate_or_peer_notes_inspected':False,'complete_fields':47,'characters':12443,'utf8_bytes':26863,'source_files_rehashed':44,'source_raw_reparses_exact':22,'source_only_proposed_ids':['deenhindi-nasai:2636'],'proposed_finite_report_occurrences':21,'initial_notes':note_files,'input_sha256':sha(ib),'additional_input_sha256':sha(additional),'input_manifest_sha256':sha(mb),'field_scope':'All44 complete saved Hindi/Urdu originals were read in six bounded original-only passes, followed by all three remaining own fields of2636. The latter five-field chain/pointer-only occurrence is proposed source-only. The other21 have supplied report content, with the two truncated Hindi main-action predicates explicitly left unfilled.63 other sibling fields remain unread.','fields':fields,'independent_pro_qc':'not_performed'}
assert {f['language'] for f in fields if f['id']=='deenhindi-nasai:2636'}=={'ar','en','hi','ur','ur-Latn'}
put(ROOT/'source-first-complete-reading.json',enc(receipt))
put(ROOT/'input/cohort.jsonl',cb);put(ROOT/'input/full-hi-ur-reading-input-44.jsonl',ib);put(ROOT/'input/source-packet-manifest.json',mb)
source_proof={'status':'PASS','source_commit':PIN,'source_files_verified':44,'exact_raw_reparses':22,'cohort_sha256':sha(cb),'input_packet_manifest_sha256':sha(mb),'records':proof,'new_semantic_approvals_from_source_hashing':0,'source_http_requests':0,'github_writes':0}
put(ROOT/'source-verification.json',enc(source_proof))
all_fields=['textArabic','translationHindi','translationUrdu','translationUrduRoman','translationEnglish']
empty=[{'id':'deenhindi-'+k,'field':f} for k,r in sources.items() for f in all_fields if not r['source_record'][f]]
print(json.dumps({'source_first_receipt_sha256':sha(enc(receipt)),'source_proof_sha256':sha(enc(source_proof)),'fields':47,'characters':12443,'utf8_bytes':26863,'candidate_created':False,'empty_source_slots':empty},indent=2))
