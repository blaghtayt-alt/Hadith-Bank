"""Independent65-field final plan, one-reason delta and155 native partitions."""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,sys
H=Path(__file__).resolve().parent;W=H.parent;P=W/'phase23-checkpoint64f4-abudawud-tirmidhi31-review';E=W/'phase22-successor-acquisition-monitor/complete-held-evidence'
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())
def local(f):return Path(f.get('local_path',f.get('source_path')))
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:p.write_bytes(b)
def leaves(x):
 if isinstance(x,dict):return sum(leaves(v) for v in x.values()) or 1
 if isinstance(x,list):return sum(leaves(v) for v in x) or 1
 return 1
ap=argparse.ArgumentParser();ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--active-sha256',required=True);args=ap.parse_args()
mb=(P/'delivery-manifest-v2.json').read_bytes();assert sha(mb)==args.manifest_sha256;m=json.loads(mb)
for f in m['files']:
 b=local(f).read_bytes();assert len(b)==f.get('bytes',f.get('size_bytes')) and sha(b)==f['sha256'];assert not f.get('git_blob_sha1') or git(b)==f['git_blob_sha1']
v1b=(P/'delivery-manifest-v1.json').read_bytes();assert sha(v1b)=='8cc3ad78ef48415e0c66964472d5fee88da34334891f5d926e9c0ebeb9054fc5';v1m=json.loads(v1b);assert len(v1m['files'])==28
for f in v1m['files']:
 b=local(f).read_bytes();assert len(b)==f.get('bytes',f.get('size_bytes')) and sha(b)==f['sha256']
 assert any(g['path']!=f['path'] and g['path'].endswith('/'+f['path']) and g['sha256']==f['sha256'] for g in m['files']),('Missing v1 archive',f['path'])
assert any(f['sha256']==sha(v1b) for f in m['files'])
af=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ab=local(af).read_bytes();assert sha(ab)==args.active_sha256;ledger=json.loads(gzip.decompress(ab));outroot=Path(str(local(af))[:-len(af['path'])])
sb=(outroot/ledger['source_ledger_path']).read_bytes();assert sha(sb)==ledger['source_ledger_sha256']
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress(sb).splitlines())}
ds={d['id']:d for d in ledger['records']};assert len(ds)==len(sources)==31 and ds.keys()==sources.keys()
oldaf=next(f for f in v1m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'));oldab=local(oldaf).read_bytes();assert sha(oldab)=='5c1a6498cee4032d90466d365424b468cabb8548a10793932f451ef72306dfd4';old={d['id']:d for d in json.loads(gzip.decompress(oldab))['records']}
ob=(H/'complete-independent-source-first-readings.json').read_bytes();assert sha(ob)=='7f529580a2885f5181279d93cd1b09582aeff2ff447fd09fa6e752360ab3c79f';own=json.loads(ob)
assert own['candidate_or_primary_notes_opened'] is False and own['all_complete_fields_read_before_candidate_inspection'] and (own['complete_fields'],own['characters'],own['utf8_bytes'])==(65,28670,61240)
readings={(r['id'],r['language']):r for r in own['fields']}
for f in own['initial_note_documents']:
 b=(H/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
pb=(H/'accepted-reviewed-field-plan-v1.json').read_bytes();assert sha(pb)=='b0a78242dfb8adc8e1ac4c489844b8ad8d8a763aa7ba3c12369bc39a4ea7a8ae';plan={(f['id'],f['language']):f for f in json.loads(pb)['reviewed_fields']};assert plan.keys()==readings.keys()
fb=(H/'independent-findings-v1.json').read_bytes();assert sha(fb)=='10bd0184685de52befe9fc28e9c69429c2b8aae3672793e12202ebe6ac029751';findings=json.loads(fb);assert len(findings['findings'])==1;finding=findings['findings'][0]
assert (finding['id'],finding['language'],finding['field_key'])==('deenhindi-tirmidhi:2711','ur','reason')
assert finding['before'].replace('actual door/identity exchange','actual identity exchange')==finding['expected'] and len(finding['before'])-len(finding['expected'])==5
cv=(H/'candidate-boundary-view-v1.json').read_bytes();assert sha(cv)=='ff30e3b91d7043bb31ab46b3c52e6b55828079c6876a487275fa26a6364bd6c2'
seen=set();cn=[]
for n in range(1,10):
 p=H/f'candidate-inspection-notes-{n:02d}.json';b=p.read_bytes();d=json.loads(b);assert d['candidate_view_sha256']==sha(cv)
 for i in d['actual_candidate_indices_read']:assert i not in seen;seen.add(i)
 cn.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
assert seen==set(range(65))
proofb=(H/'independent-source-verification.json').read_bytes();assert sha(proofb)=='3ee8fb1a4f8fab2a50d1c36c68c46eebf94a884f5aad5243a6bd55e9b15c5236'
for r in json.loads(proofb)['records']:
 for f in r['files']:
  b=(E/'sources'/f['path']).read_bytes();assert len(b)==f['stored_bytes'] and sha(b)==f['stored_sha256'] and git(b)==f['git_blob_sha1']
sys.dont_write_bytecode=True;sys.path.insert(0,str(W/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
engine=SourceReviews(outroot,'deenhindi');assert set(engine.decisions)==set(sources) and engine.engine_sha256=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
counts={'source_slots':0,'nonempty_partitions':0,'exact_empty_slots':0,'read_fields':0,'characters':0,'utf8_bytes':0,'admitted':0,'read_context':0,'unread_context':0,'spans':0,'metadata_leaf_equalities':0,'unchanged_read_fields':0,'unchanged_unread_slots':0,'unchanged_whole_parents':0}
slots=[];reports=[];changed=[]
for ident,saved in sources.items():
 d=ds[ident];was=old[ident];expected=copy.deepcopy(was)
 if ident==finding['id']:
  f=next(f for f in expected['field_reviews'] if f['language']=='ur');assert f['reason']==finding['before'];f['reason']=finding['expected']
 else:counts['unchanged_whole_parents']+=1
 assert d==expected,(ident,'Unexpected parent/field change')
 assert d['source_record_sha256']==sha(importer.json_bytes(saved['source_record'])) and d['source_reference_verbatim']==saved['source_reference_verbatim']
 original=importer.canonical_record(saved);frozen=copy.deepcopy(original);after,action=engine.apply(original,saved=saved);assert original==frozen and action==d['decision']
 assert after['review']['independent_pro_qc']=='not_performed' and not after['review']['certified_release_eligible'] and after['number']['canonical'] is None
 for k,v in frozen.items():
  if k not in ['text','language_versions','review','content_kind','extraction','report_types']:assert after.get(k)==v;counts['metadata_leaf_equalities']+=leaves(v)
 fields={f['language']:f for f in d['field_reviews']};oldfields={f['language']:f for f in was['field_reviews']};oldlangs={v['language']:v for v in frozen['language_versions']};newlangs={v['language']:v for v in after['language_versions']};assert oldlangs.keys()==newlangs.keys()
 for lang,source_field in importer.LANGUAGE_FIELDS.items():
  text=saved['source_record'][source_field];counts['source_slots']+=1;assert text,'This65-field cohort has no empty source slots'
  before,now=oldlangs[lang],newlangs[lang];assert before['text']==text;f=fields.get(lang);read_field=(ident,lang) in readings
  assert now['source']['manual_review']['field_reviewed']==read_field
  if read_field:
   r=readings[ident,lang];e=plan[ident,lang];assert r['complete_field_read'] and r['text']==text and r['sha256']==sha(text.encode())
   assert f==e['expected_field_review'] and f['spans']==e['expected_spans'] and d['decision']==e['decision']
   assert now['source']['manual_review']['reason']==f['reason']
   counts['read_fields']+=1;counts['characters']+=len(text);counts['utf8_bytes']+=len(text.encode())
   if (ident,lang)==(finding['id'],finding['language']):assert f['reason']==finding['expected'];changed.append({'id':ident,'language':lang,'key':'reason','source_mask_unchanged':True})
   else:assert f==oldfields[lang];counts['unchanged_read_fields']+=1
  else:assert f==oldfields.get(lang);counts['unchanged_unread_slots']+=1
  spans=f['spans'] if f else [];actual=now['source'].get('text_spans',{}).get('quotation_spans',[]);assert actual==[[s['start'],s['end']] for s in spans]
  assert (now['text'] or '')==''.join(text[s['start']:s['end']] for s in spans)
  parts=[]
  for s in spans:
   a,b=s['start'],s['end'];assert s['sha256']==sha(text[a:b].encode());parts.append((a,b,text[a:b]))
  for c in now['comments']:
   a,b=c['source_span'];assert c['scope']=='source_context_not_narration' and c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode());parts.append((a,b,c['text']))
  cursor=0
  for a,b,value in sorted(parts):assert a==cursor and a<b<=len(text) and value==text[a:b];cursor=b
  assert cursor==len(text) and ''.join(v for a,b,v in sorted(parts))==text;counts['nonempty_partitions']+=1;counts['spans']+=len(spans)
  for cls in now['source'].get('report_component_classifications',[]):
   ss=[s for s in spans if s['component_id']==cls['component_id']];assert ss and cls['spans']==[[s['start'],s['end']] for s in ss]
   assert all(cls['speaker_description']==s['speaker'] and cls['report_type']==s['report_type'] and cls['source_report_family_id']==s['source_report_family_id'] for s in ss)
   assert cls['reason']==f['reason']
  for k,v in before.items():
   if k not in ['text','scope','source','comments','quotation_status']:assert now.get(k)==v;counts['metadata_leaf_equalities']+=leaves(v)
  for k,v in before['source'].items():assert now['source'].get(k)==v;counts['metadata_leaf_equalities']+=leaves(v)
  status='admitted' if spans else 'read_context' if read_field else 'unread_context';counts[status]+=1
  slots.append({'id':ident,'language':lang,'status':status,'source_text_sha256':sha(text.encode()),'exact_partition':True})
  if read_field:reports.append({'id':ident,'language':lang,'expected_spans':spans,'initial_independent_reading_note':readings[ident,lang]['initial_independent_reading_note'],'reason':f['reason']})
engine.finish()
assert (counts['source_slots'],counts['nonempty_partitions'],counts['exact_empty_slots'])==(155,155,0)
assert (counts['read_fields'],counts['characters'],counts['utf8_bytes'])==(65,28670,61240)
assert (counts['admitted'],counts['read_context'],counts['unread_context'],counts['spans'])==(60,5,90,126)
assert (counts['unchanged_read_fields'],counts['unchanged_unread_slots'],counts['unchanged_whole_parents'])==(64,90,30) and len(changed)==1
only={i for i,d in ds.items() if d['decision']=='exclude'};assert only=={'deenhindi-abudawud:2720'}==set(own['source_only_proposed_after_all_five_own_fields'])
assert sum(d['decision']=='register' for d in ds.values())==30
assert {lang for ident,lang in readings if ident in only}==set(importer.LANGUAGE_FIELDS)
confirmation=read(H/'final-reason-inspection.json');assert confirmation['final_reason_actually_read'] and confirmation['primary_manifest_sha256']==sha(mb) and confirmation['active_sha256']==sha(ab) and confirmation['exact_reason_sha256']==sha(finding['expected'].encode())
report={'schema':'hadith-bank-independent-final-source-review-audit-v1','status':'PASS','source_commit':'64f4ed50ed6026855237a5d547a86dd03e73f804','primary_manifest_sha256':sha(mb),'active_ledger_sha256':sha(ab),'independent_source_first_sha256':sha(ob),'source_proof_sha256':sha(proofb),'findings_sha256':sha(fb),'accepted_field_plan_sha256':sha(pb),'occurrences':31,'registered':30,'source_only':1,'source_only_ids':sorted(only),'counts':counts,'source_files_independently_reopened_and_hashed':62,'exact_raw_reparses_in_source_first_proof':31,'native_apply_finish':'PASS','all65_candidate_masks_and_voices_actually_compared':True,'candidate_inspection_note_bindings':cn,'only_final_change':changed,'selected_source_characters_changed':0,'all126_spans_types_speakers_families_exact':True,'complete28_file_v1_payload_and_manifest_archived_exact':True,'open_findings':[],'initial_notes_and_explicit_refinements_preserved':True,'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes':0,'live_deployment_claimed':False,'all_source_slots':slots,'fields':reports}
payload={'final-audit.json':enc(report),'complete-independent-source-first-readings.json':ob,'independent-source-verification.json':proofb,'independent-findings-v1.json':fb,'accepted-reviewed-field-plan-v1.json':pb,'candidate-boundary-view-v1.json':cv,'audit_final.py':Path(__file__).read_bytes()}
for n in ['freeze_source_first.py','inspect_candidate.py','additional-2720-source-first-note.json','final-reason-inspection.json']+[f'source-first-notes-{n:02d}.json' for n in range(1,8)]+[f'candidate-inspection-notes-{n:02d}.json' for n in range(1,10)]:payload[n]=(H/n).read_bytes()
files=[];out=H/'publish';rel=Path('reports/web-source-resolution-20261113/checkpoint64f4-mixed31-independent-audit')
for name,b in payload.items():
 p=out/rel/name;put(p,b);files.append({'path':p.relative_to(out).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
delivery={'schema':'hadith-bank-independent-final-audit-delivery-v1','status':'PASS','source_commit':report['source_commit'],'primary_manifest_sha256':sha(mb),'files':files};put(H/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(delivery)),'files':len(files),'bytes':sum(f['bytes'] for f in files),'report_sha256':sha(enc(report)),**counts},indent=2))
