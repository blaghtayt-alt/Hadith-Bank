"""Freeze only the65 actual independent original readings; no candidate input."""
from pathlib import Path
import datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
INPUT=WORK/'phase23-checkpoint64f4-input-partitions/deployment-abudawud13-tirmidhi18'
EVID=WORK/'phase22-successor-acquisition-monitor/complete-held-evidence'
PIN='64f4ed50ed6026855237a5d547a86dd03e73f804'
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
ib=(INPUT/'full-hi-ur-reading-input-62.jsonl').read_bytes()
assert sha(ib)=='41f87a48423f60e7757e3410f57739d6484a6dd287b192509568ac4a4c559c68'
rows=list(map(json.loads,ib.splitlines()));assert len(rows)==62
cb=(INPUT/'cohort.jsonl').read_bytes()
assert sha(cb)=='0a13beaaab0870f9e9ca031bac2d29be050e456cae18fbe139d5db02f027cd7d'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,cb.splitlines())};assert len(sources)==31
notes_by_row={};notes_by_id={};note_documents=[]
for n in range(1,8):
 p=ROOT/f'source-first-notes-{n:02d}.json';b=p.read_bytes();d=json.loads(b)
 assert d['input_sha256']==sha(ib) and d['candidate_or_primary_notes_opened'] is False
 for index in d['complete_original_reading_orders']:
  assert index not in notes_by_row;row=rows[index-1];notes_by_row[index]=d['notes'][row['occurrence_id']]
 for ident,note in d['notes'].items():notes_by_id.setdefault(ident,[]).append({'batch':n,'note':note})
 note_documents.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
assert set(notes_by_row)==set(range(1,63))
ep=ROOT/'additional-2720-source-first-note.json';eb=ep.read_bytes();ed=json.loads(eb)
assert ed['candidate_or_primary_notes_opened'] is False and ed['actual_complete_languages_read']==['ar','en','ur-Latn']
note_documents.append({'path':ep.name,'bytes':len(eb),'sha256':sha(eb)})
additional=[];saved=sources['abudawud:2720']
for lang,field in [('ar','textArabic'),('en','translationEnglish'),('ur-Latn','translationUrduRoman')]:
 text=saved['source_record'][field];assert text
 row={'occurrence_id':'deenhindi-abudawud:2720','collection':'abudawud','number':'2720','language':lang,'source_field':field,'text':text,'text_sha256':sha(text.encode()),'source_record_sha256':sha(importer.json_bytes(saved['source_record']))}
 additional.append(row);rows.append(row);notes_by_row[len(rows)]=ed['note']
notes_by_id['deenhindi-abudawud:2720'].append({'batch':'additional-three-own-fields','note':ed['note']})
mb=(EVID/'evidence-manifest.json').read_bytes();assert sha(mb)=='c2abcc3fb29dbada01127031b902026f785be51b225d590407d8917465a80a0c'
manifest=json.loads(mb);assert manifest['saved_head']==PIN
entries=json.loads((EVID/'held-state-entries.json').read_bytes());proof=[]
for key,saved in sources.items():
 files=[]
 for kind,descriptor in [('raw',saved['snapshot']),('parsed',entries[key]['parsed'])]:
  stored=(EVID/'sources'/descriptor['path']).read_bytes();authority=manifest['files'][descriptor['path']]
  assert sha(stored)==authority['stored_sha256'] and git(stored)==authority['git_blob_sha1'] and len(stored)==authority['stored_bytes']
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
assert len(fields)==65 and len({(f['id'],f['language']) for f in fields})==65
assert sum(f['characters'] for f in fields)==28670
assert {f['language'] for f in fields if f['id']=='deenhindi-abudawud:2720'}=={'ar','en','ur-Latn','hi','ur'}
counts={'complete_fields':65,'characters':sum(f['characters'] for f in fields),'utf8_bytes':sum(f['utf8_bytes'] for f in fields)}
receipt={'schema':'hadith-bank-independent-complete-source-first-reading-v1','source_commit':PIN,'reader':'/root','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**counts,'all_complete_fields_read_before_candidate_inspection':True,'candidate_or_primary_notes_opened':False,'input_sha256':sha(ib),'cohort_sha256':sha(cb),'complete_evidence_manifest_sha256':sha(mb),'source_files_reopened':62,'exact_raw_reparses':31,'initial_note_documents':note_documents,'source_only_proposed_after_all_five_own_fields':['deenhindi-abudawud:2720'],'fields':fields,'independent_pro_qc':'not_performed','github_writes':0,'source_http_requests':0}
source_proof={'schema':'hadith-bank-independent-complete-source-reopening-v1','status':'PASS','source_commit':PIN,'saved_files_reopened':62,'exact_raw_reparses':31,'input_sha256':sha(ib),'cohort_sha256':sha(cb),'complete_evidence_manifest_sha256':sha(mb),'records':proof,'linguistic_reading_claim_from_hashing':False}
put(ROOT/'complete-independent-source-first-readings.json',enc(receipt));put(ROOT/'independent-source-verification.json',enc(source_proof))
put(ROOT/'input/full-field-reading-input-62.jsonl',ib);put(ROOT/'input/cohort.jsonl',cb)
put(ROOT/'input/additional-2720-own-field-inputs.json',enc(additional))
print(json.dumps({'source_first_sha256':sha(enc(receipt)),'source_proof_sha256':sha(enc(source_proof)),**counts,'candidate_opened':False},indent=2))
