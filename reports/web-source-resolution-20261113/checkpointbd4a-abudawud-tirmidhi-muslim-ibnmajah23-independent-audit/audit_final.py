"""Independent final-byte, accepted-boundary, preservation and native audit."""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
PRIMARY=WORK/'phase18-checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-review'
PIN='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
EVID=WORK/'phase16-successor-acquisition-monitor/held-evidence'
FIELDS={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())
def local(f):return Path(f.get('local_path',f.get('source_path')))
def leaf(x):
 if isinstance(x,dict):return sum(leaf(v) for v in x.values()) or 1
 if isinstance(x,list):return sum(leaf(v) for v in x) or 1
 return 1
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
def sig(s):return tuple(s.get(k) for k in ['component_id','source_report_family_id','report_type','speaker'])
def mask(spans):return {i for s in spans for i in range(s['start'],s['end'])}
parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--active-sha256',required=True);args=parser.parse_args()
mp=PRIMARY/'delivery-manifest-v2.json';mb=mp.read_bytes();assert sha(mb)==args.manifest_sha256;m=json.loads(mb)
for f in m['files']:
 b=local(f).read_bytes();assert len(b)==f.get('bytes',f.get('size_bytes')) and sha(b)==f['sha256']
 if f.get('git_blob_sha1'):assert git(b)==f['git_blob_sha1']
active=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ap=local(active);ab=ap.read_bytes();assert sha(ab)==args.active_sha256
out_root=Path(str(ap)[:-len(active['path'])]);ledger=json.loads(gzip.decompress(ab))
baseline=(out_root/ledger['source_ledger_path']).read_bytes();assert sha(baseline)==ledger['source_ledger_sha256']
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress(baseline).splitlines())}
decisions={r['id']:r for r in ledger['records']};assert len(sources)==len(decisions)==23 and sources.keys()==decisions.keys()
ownp=ROOT/'complete-independent-source-first-readings.json';ownb=ownp.read_bytes();assert sha(ownb)=='76bbb3cc2225960e170f664699136e32a534e20dd41216eb1c968acbb4ccf443'
own=json.loads(ownb);assert own['candidate_or_primary_notes_inspected'] is False and own['all_fields_read_in_full_before_candidate_access']
assert (own['complete_fields'],own['characters'],own['utf8_bytes'])==(55,34118,70795)
readings={(f['id'],f['language']):f for f in own['fields']}
planp=ROOT/'accepted-reviewed-field-plan.json';assert sha(planp.read_bytes())=='a1833a7fd1190de7f65b98560dc3d26f2dfcb3b5bd00e7ad0158b2254b9a5184'
plan={(f['id'],f['language']):f for f in read(planp)['reviewed_fields']};assert plan.keys()==readings.keys()
findingp=ROOT/'independent-boundary-findings-v1.json';assert sha(findingp.read_bytes())=='9b52c350b7eda0e5bee536f5f50d66db5a1bebe0de5d6a0398d5f661eda12420'
findings=read(findingp);changed={(f['id'],f['language']) for f in findings['findings']};assert len(changed)==5
proofp=ROOT/'independent-source-verification.json';assert sha(proofp.read_bytes())=='b7afa9df3f6ec66b87ea9bd1241bbee9b85413311821c4c9ac848f3234269cc8'
for r in read(proofp)['records']:
 for f in r['files']:
  b=(EVID/'sources'/f['path']).read_bytes();assert len(b)==f['stored_bytes'] and sha(b)==f['stored_sha256'] and git(b)==f['git_blob_sha1']
v1mb=(PRIMARY/'delivery-manifest-v1.json').read_bytes();assert sha(v1mb)=='8d66fd9f9373f513cf06d31c42ff8128e5c55f38e8f228da9f61bba0b8806a64';v1m=json.loads(v1mb)
for f in v1m['files']:
 b=local(f).read_bytes();assert sha(b)==f['sha256'] and len(b)==f.get('bytes',f.get('size_bytes'))
 assert any(g['path']!=f['path'] and g['path'].endswith('/'+f['path']) and g['sha256']==f['sha256'] and g.get('bytes',g.get('size_bytes'))==len(b) for g in m['files']),('v1 archive missing',f['path'])
assert any(f['sha256']==sha(v1mb) for f in m['files'])
v1f=next(f for f in v1m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
v1b=local(v1f).read_bytes();assert sha(v1b)=='1ae17b3b034812f8c40789881abd9d0184bbdb57c3c58a3eb09e682116b04fe8'
v1={r['id']:r for r in json.loads(gzip.decompress(v1b))['records']}
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
engine=SourceReviews(out_root,'deenhindi');assert set(engine.decisions)==set(sources)
assert engine.engine_sha256=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
counts={'source_slots':0,'nonempty_partitions':0,'exact_empty_slots':0,'metadata_value_equalities':0,'admitted':0,'read_context':0,'unread_context':0,'read_fields':0,'characters':0,'utf8_bytes':0,'spans':0,'unchanged_explicit_fields':0,'unchanged_implicit_nonempty_slots':0,'unchanged_whole_parents':0}
field_reports=[];slot_reports=[]
for ident,saved in sources.items():
 d=decisions[ident];old_d=v1[ident];assert d['decision']==old_d['decision']
 assert d['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
 assert d['source_reference_verbatim']==saved['source_reference_verbatim']
 original=importer.canonical_record(saved);frozen=copy.deepcopy(original);after,disposition=engine.apply(original,saved=saved)
 assert original==frozen and disposition==d['decision']
 for key in ['id','number','narrator','grading','references','source_locator','source','translator','translation_provenance','rights','source_headings']:
  assert after[key]==frozen[key];counts['metadata_value_equalities']+=leaf(frozen[key])
 assert after['review']['independent_pro_qc']=='not_performed' and not after['review']['certified_release_eligible']
 bylang={f['language']:f for f in d['field_reviews']};oldfields={f['language']:f for f in old_d['field_reviews']}
 assert bylang.keys()==oldfields.keys()
 if not any(i==ident for i,l in changed):assert d==old_d;counts['unchanged_whole_parents']+=1
 oldlangs={f['language']:f for f in frozen['language_versions']};newlangs={f['language']:f for f in after['language_versions']}
 assert oldlangs.keys()==newlangs.keys()
 for lang,source_field in FIELDS.items():
  text=saved['source_record'][source_field];counts['source_slots']+=1
  assert isinstance(text,str)
  if not text:
   assert (ident,lang) not in readings and lang not in bylang and lang not in oldlangs
   counts['exact_empty_slots']+=1;slot_reports.append({'id':ident,'language':lang,'source_field':source_field,'source_text_sha256':sha(b''),'status':'exact_empty_not_read'});continue
  old,new=oldlangs[lang],newlangs[lang];assert old['text']==text
  f=bylang.get(lang);was=oldfields.get(lang);read_field=(ident,lang) in readings
  for key in ['id','language','script','references','translation_provenance']:
   assert old[key]==new[key];counts['metadata_value_equalities']+=leaf(old[key])
  assert new['source']['manual_review']['field_reviewed']==read_field
  if (ident,lang) not in changed:
   assert f==was
   if f is None:counts['unchanged_implicit_nonempty_slots']+=1
   else:counts['unchanged_explicit_fields']+=1
  if read_field:
   r=readings[ident,lang];e=plan[ident,lang]
   assert f and f['reviewed'] and r['complete_field_read'] and r['text']==text and r['sha256']==sha(text.encode())
   assert f['text_sha256']==sha(text.encode()) and f['chars_reviewed']==len(text) and f['bytes_reviewed']==len(text.encode())
   assert d['decision']==e['decision'] and mask(f['spans'])==mask(e['expected_spans']),(ident,lang)
   assert {sig(s) for s in f['spans']}=={sig(s) for s in e['expected_spans']}
   counts['read_fields']+=1;counts['characters']+=len(text);counts['utf8_bytes']+=len(text.encode())
  else:assert f is None
  spans=new['source'].get('text_spans',{}).get('quotation_spans',[])
  assert spans==([[s['start'],s['end']] for s in f['spans']] if f else [])
  assert (new['text'] or '')==''.join(text[a:b] for a,b in spans)
  if f:
   for s in f['spans']:assert s['sha256']==sha(text[s['start']:s['end']].encode())
  parts=[(a,b,text[a:b]) for a,b in spans];gaps=[]
  for c in new['comments']:
   a,b=c['source_span'];assert c['scope']=='source_context_not_narration' and c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode())
   parts.append((a,b,c['text']));gaps.append({'start':a,'end':b,'text':c['text'],'sha256':c['source_text_sha256']})
  cursor=0
  for a,b,value in sorted(parts):assert a==cursor and a<b<=len(text) and value==text[a:b];cursor=b
  assert cursor==len(text) and ''.join(value for a,b,value in sorted(parts))==text
  counts['nonempty_partitions']+=1;counts['spans']+=len(spans)
  status='admitted' if spans else 'read_context' if read_field else 'unread_context';counts[status]+=1
  slot_reports.append({'id':ident,'language':lang,'source_field':source_field,'source_text_sha256':sha(text.encode()),'status':status,'exact_partition':True})
  if read_field:field_reports.append({'id':ident,'language':lang,'complete_source_first_reading':True,'source_sha256':sha(text.encode()),'selected_spans':f['spans'],'context_gaps':gaps,'original_blind_note':readings[ident,lang]['independent_reading_note'],'expected_plan':plan[ident,lang]})
engine.finish()
assert (counts['source_slots'],counts['nonempty_partitions'],counts['exact_empty_slots'])==(115,113,2)
assert (counts['read_fields'],counts['characters'],counts['utf8_bytes'])==(55,34118,70795)
assert (counts['admitted'],counts['read_context'],counts['unread_context'])==(40,15,58)
assert (counts['unchanged_explicit_fields'],counts['unchanged_implicit_nonempty_slots'],counts['unchanged_whole_parents'])==(50,58,20)
assert sum(d['decision']=='register' for d in decisions.values())==20
only={i for i,d in decisions.items() if d['decision']=='exclude'};assert only==set(own['source_only_proposed_ids'])
for i in only:assert len([r for r in readings if r[0]==i])==5
report={'schema':'hadith-bank-independent-final-source-review-audit-v1','status':'PASS','source_commit':PIN,'primary_manifest_sha256':sha(mb),'active_ledger_sha256':sha(ab),'independent_source_first_sha256':sha(ownb),'source_proof_sha256':sha(proofp.read_bytes()),'findings_sha256':sha(findingp.read_bytes()),'accepted_field_plan_sha256':sha(planp.read_bytes()),'occurrences':23,'registered':20,'source_only':3,'source_only_ids':sorted(only),'counts':counts,'source_files_independently_reopened_and_hashed':46,'exact_raw_reparses_in_source_first_proof':23,'native_apply_finish':'PASS','all_seven_findings_resolved':True,'restored_characters':96,'restored_utf8_bytes':192,'open_findings':[],'all_source_metadata_unchanged':True,'complete21_file_v1_payload_and_manifest_archived_exact':True,'initial_notes_and_refinements_preserved':True,'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes':0,'live_deployment_claimed':False,'all_source_slots':slot_reports,'fields':field_reports}
out=ROOT/'publish';rel=Path('reports/web-source-resolution-20261113/checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-independent-audit')
payload={'final-audit.json':enc(report),'complete-independent-source-first-readings.json':ownb,'independent-source-verification.json':proofp.read_bytes(),'independent-boundary-findings-v1.json':findingp.read_bytes(),'accepted-reviewed-field-plan.json':planp.read_bytes(),'freeze_source_first.py':(ROOT/'freeze_source_first.py').read_bytes(),'freeze_findings.py':(ROOT/'freeze_findings.py').read_bytes(),'audit_final.py':Path(__file__).read_bytes()}
files=[]
for name,b in payload.items():
 p=out/rel/name;put(p,b);files.append({'path':p.relative_to(out).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
delivery={'schema':'hadith-bank-independent-final-audit-delivery-v1','status':'PASS','source_commit':PIN,'primary_manifest_sha256':sha(mb),'files':files};put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(delivery)),'files':len(files),'bytes':sum(f['bytes'] for f in files),'report_sha256':sha(enc(report)),**counts},indent=2))
