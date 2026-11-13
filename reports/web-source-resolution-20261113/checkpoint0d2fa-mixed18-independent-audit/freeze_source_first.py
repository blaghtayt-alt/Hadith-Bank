"""Freeze the independent48-field original pass before opening primary decisions."""
from pathlib import Path
import datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
INPUT=WORK/'phase21-checkpoint0d2fa-abudawud-tirmidhi18-review/input'
EVID=WORK/'phase19-successor-acquisition-monitor/held-evidence'
PIN='0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a'
sys.dont_write_bytecode=True;sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
assert not (ROOT/'complete-independent-source-first-readings.json').exists()
ib=(INPUT/'full-field-reading-input-48.jsonl').read_bytes()
assert sha(ib)=='d5fab447f9bcae574117b2d8f1eb976a382a88f6f2b657a70aa7bdc445dea7fb'
rows=list(map(json.loads,ib.splitlines()));assert len(rows)==48
cb=(INPUT/'cohort.jsonl').read_bytes();sources={r['collection']+':'+r['number']:r for r in map(json.loads,cb.splitlines())};assert len(sources)==18
note_documents=[];notes_by_row={};notes_by_id={}
for n in range(1,7):
 p=ROOT/('source-first-notes-%02d.json'%n);b=p.read_bytes();d=json.loads(b)
 assert d['input_sha256']==sha(ib) and d['candidate_or_primary_reading_notes_opened'] is False
 for index in d['complete_input_rows_read']:
  assert index not in notes_by_row;row=rows[index-1];notes_by_row[index]=d['notes'][row['occurrence_id']]
 for ident,note in d['notes'].items():notes_by_id.setdefault(ident,[]).append({'batch':n,'note':note})
 note_documents.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
assert set(notes_by_row)==set(range(1,49))
entries=json.loads((EVID/'held-state-entries.json').read_bytes());manifest=json.loads((EVID/'evidence-manifest.json').read_bytes());assert manifest['saved_head']==PIN
proof=[]
for key,saved in sources.items():
 files=[]
 for kind,descriptor in [('raw',saved['snapshot']),('parsed',entries[key]['parsed'])]:
  stored=(EVID/'sources'/descriptor['path']).read_bytes();authority=manifest['files'][descriptor['path']]
  assert sha(stored)==authority.get('stored_sha256',authority['sha256']) and git(stored)==authority['git_blob_sha1']
  plain=importer.checked_bytes(EVID/'sources',descriptor)
  if kind=='raw':
   obj,reference=importer.parse_record(plain,saved['collection'],saved['number'])
   assert obj==saved['source_record'] and reference==saved['source_reference_verbatim']
  else:
   expected={k:saved[k] for k in ['schema','collection','number','snapshot','source_reference_verbatim','source_record']};expected['classification']=saved['intake_classification']
   assert json.loads(plain)==expected and plain==importer.json_bytes(expected)
  files.append({'kind':kind,'path':descriptor['path'],'stored_bytes':len(stored),'stored_sha256':sha(stored),'git_blob_sha1':git(stored),'plain_bytes':len(plain),'plain_sha256':sha(plain)})
 proof.append({'id':'deenhindi-'+key,'files':files,'raw_reparse_exact':True})
fields=[]
for index,row in enumerate(rows,1):
 saved=sources[row['collection']+':'+row['number']];text=row['text']
 assert text==saved['source_record'][row['source_field']] and sha(text.encode())==row['text_sha256']
 assert sha(importer.json_bytes(saved['source_record']))==row['source_record_sha256']
 fields.append({'id':row['occurrence_id'],'language':row['language'],'source_field':row['source_field'],'text':text,'sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),'complete_field_read':True,'input_row':index,'initial_independent_reading_note':notes_by_row[index],'own_parent_note_history':notes_by_id[row['occurrence_id']]})
assert (len(fields),sum(f['characters'] for f in fields),sum(f['utf8_bytes'] for f in fields))==(48,13826,27038)
assert len({(f['id'],f['language']) for f in fields})==48
for ident in ['deenhindi-abudawud:2582','deenhindi-abudawud:2617']:
 assert {f['language'] for f in fields if f['id']==ident}=={'ar','en','hi','ur','ur-Latn'}
receipt={'schema':'hadith-bank-independent-complete-source-first-reading-v1','source_commit':PIN,'reader':'/root','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'complete_fields':48,'characters':13826,'utf8_bytes':27038,'all_complete_fields_read_before_candidate_inspection':True,'candidate_or_primary_notes_opened':False,'input_sha256':sha(ib),'cohort_sha256':sha(cb),'source_files_reopened':36,'exact_raw_reparses':18,'initial_note_documents':note_documents,'source_only_proposed_after_all_five_own_fields':['deenhindi-abudawud:2582','deenhindi-abudawud:2617'],'fields':fields,'independent_pro_qc':'not_performed','github_writes':0,'source_http_requests':0}
source_proof={'schema':'hadith-bank-independent-complete-source-reopening-v1','status':'PASS','source_commit':PIN,'saved_files_reopened':36,'exact_raw_reparses':18,'input_sha256':sha(ib),'cohort_sha256':sha(cb),'records':proof,'linguistic_reading_claim_from_hashing':False}
put(ROOT/'complete-independent-source-first-readings.json',enc(receipt));put(ROOT/'independent-source-verification.json',enc(source_proof))
put(ROOT/'input/full-field-reading-input-48.jsonl',ib);put(ROOT/'input/cohort.jsonl',cb)
print(json.dumps({'source_first_sha256':sha(enc(receipt)),'source_proof_sha256':sha(enc(source_proof)),'fields':48,'characters':13826,'utf8_bytes':27038,'candidate_opened':False},indent=2))
