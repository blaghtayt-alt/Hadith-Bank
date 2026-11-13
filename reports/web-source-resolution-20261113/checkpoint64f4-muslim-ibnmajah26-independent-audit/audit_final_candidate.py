#!/usr/bin/env python3
"""Independent exact amendment, source preservation and native partition audit."""
import collections,copy,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent;OWNER=BASE/'phase23-checkpoint64f4-muslim-ibnmajah26-review';SOURCE=BASE/'phase22-successor-acquisition-monitor/complete-held-evidence'
COMMIT='64f4ed50ed6026855237a5d547a86dd03e73f804';sha=lambda b:hashlib.sha256(b).hexdigest();blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
LANG={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
def load(p):return json.loads(p.read_bytes())
def checked(root,p):
 target=root/p;assert not Path(p).is_absolute() and '..' not in Path(p).parts and target.is_file() and target.resolve().is_relative_to(root.resolve())
 assert not any(x.is_symlink() for x in (target,*target.parents) if x.is_relative_to(root));return target.read_bytes()
def leafcount(a,b):
 assert a==b
 if isinstance(a,dict):return sum(leafcount(a[k],b[k]) for k in a)
 if isinstance(a,list):return sum(leafcount(x,y) for x,y in zip(a,b,strict=True))
 return 1
def labels(f):
 return {i:{k:s[k] for k in ('component_id','report_type','speaker','source_report_family_id')} for s in f['selected_spans'] for i in range(s['start'],s['end'])}
def write(root,path,data):
 p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==data
 else:p.write_bytes(data)
 return {'path':path,'local_path':str(p),'bytes':len(data),'sha256':sha(data),'git_blob_sha1':blob(data)}

def main():
 assert not (ROOT/'delivery-manifest.json').exists()
 binding=load(ROOT/'final-candidate-binding.json');assert binding['all55_complete_original_fields_and_candidate_boundaries_independently_read'] and binding['owner_accepted_all_requested_changes']
 manifestpath=Path(binding['owner_manifest_path']);mb=manifestpath.read_bytes();assert sha(mb)==binding['owner_manifest_sha256'];manifest=json.loads(mb);PUBLISHED=OWNER/binding['owner_output_directory']
 filebindings=[]
 for f in manifest['files']:
  b=checked(PUBLISHED,f['path']);assert len(b)==f['bytes'] and sha(b)==f['sha256']
  if 'git_blob_sha1' in f:assert blob(b)==f['git_blob_sha1']
  filebindings.append({'path':f['path'],'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)})
 ab=checked(PUBLISHED,manifest['active_ledger_path']);assert sha(ab)==binding['active_ledger_sha256']==manifest['active_ledger_sha256'];doc=json.loads(gzip.decompress(ab));assert doc['source_commit']==COMMIT
 records={r['occurrence_id']:r for r in doc['records']};assert len(records)==len(doc['records'])==26
 findings=load(ROOT/'final-field-boundary-assessment.json');assert findings['all55_candidate_fields_independently_assessed'] and findings['open_findings']==[]
 approved={(f['id'],f['language']):f for f in findings['fields']}
 for record in records.values():
  for field in record['fields']:
   if field['reviewed']:
    expected=approved[(record['occurrence_id'],field['language'])];assert field['text_sha256']==expected['text_sha256']
    observed=[{k:s[k] for k in ('start','end','sha256','component_id','report_type','speaker','source_report_family_id')} for s in field['selected_spans']]
    assert observed==expected['approved_spans']
 amendment=binding.get('independent_amendment_result',{'requested_changes':0})
 sys.path.insert(0,str(BASE/'hindi-resolve/work/scripts'));import import_deenhindi as importer;import web_source_reviews as reviews;import web_commentary_quotes as quotes
 assert sha(Path(importer.__file__).read_bytes())=='c2b6df1d243b7e9c695358d9f06221c4cba45e880a1a215e4ef697008ed144d0'
 assert sha(Path(reviews.__file__).read_bytes()+Path(quotes.__file__).read_bytes())=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
 inbytes=(ROOT/'input/cohort.jsonl').read_bytes();assert sha(inbytes)=='177817c054b00b6439014cb0f30e8f097e7f6c142851ae78f1c3ea397f3a00b5';rows={x['collection']+':'+x['number']:x for x in map(json.loads,inbytes.splitlines())}
 baseline=checked(PUBLISHED,doc['source_ledger_path']);assert sha(baseline)==doc['source_ledger_sha256'];plain=gzip.decompress(baseline);assert sha(plain)==doc['source_ledger_uncompressed_sha256'];assert {x['collection']+':'+x['number']:x for x in map(json.loads,plain.splitlines())}==rows
 firstb=(ROOT/'complete-independent-source-first-readings.json').read_bytes();assert sha(firstb)=='a2a8ef84e907963f0ece1dd7376ea7a7d0cff1e0ca31561ed35f8a9d99a20377';first=json.loads(firstb);assert first['primary_notes_or_candidate_inspected_before_freeze'] is False
 readings={(f['occurrence_id'],f['language']):f for f in first['records']};assert len(readings)==55 and first['characters_read']==23149 and first['utf8_bytes_read']==48862
 originalfields={(f['occurrence_id'],f['language']):f for f in map(json.loads,(ROOT/'input/full-field-reading-input-55.jsonl').read_bytes().splitlines())}
 artifact=load(SOURCE/'evidence-manifest.json');assert sha((SOURCE/'evidence-manifest.json').read_bytes())=='c2abcc3fb29dbada01127031b902026f785be51b225d590407d8917465a80a0c' and artifact['saved_head']==COMMIT
 artifactrows={x['collection']+':'+x['number']:x for x in map(json.loads,(SOURCE/'held-source-records.jsonl').read_bytes().splitlines())};assert len(artifactrows)==273 and all(artifactrows[k]==v for k,v in rows.items());states=load(SOURCE/'held-state-entries.json')
 native=reviews.SourceReviews(PUBLISHED,'deenhindi');assert set(native.decisions)==set(records);totals=collections.Counter();sources=[];fieldproof=[];voices=[]
 for key,row in rows.items():
  identity='deenhindi-'+key;r=records[identity];action='exclude' if identity=='deenhindi-muslim:2725' else 'register'
  assert r['decision']==action and r['source_snapshot']==row['snapshot'] and r['source_record_sha256']==sha(importer.json_bytes(row['source_record']))
  assert r['source_reference_verbatim']==row['source_reference_verbatim'] and r['source_parsed_path']==row['parsed_path'] and r['collection']==row['collection'] and r['number']==row['number'] and r['external_canonical_identity'] is None and r['verified_external_reference'] is None
  fs=[]
  for kind,p in [('raw',row['snapshot']['path']),('parsed',row['parsed_path'])]:
   stored=checked(SOURCE/'sources',p);s=artifact['files'][p];body=gzip.decompress(stored);assert sha(stored)==s['sha256']==s['stored_sha256'] and len(stored)==s['bytes']==s['stored_bytes'] and blob(stored)==s['git_blob_sha1']
   if kind=='raw':raw=body;assert sha(raw)==row['snapshot']['sha256'] and len(raw)==row['snapshot']['bytes']
   else:parsed=body;assert sha(parsed)==states[key]['parsed']['sha256']==r['source_parsed_sha256'] and sha(stored)==states[key]['parsed']['stored_sha256']
   fs.append({'kind':kind,'path':p,'stored_bytes':len(stored),'stored_sha256':sha(stored),'git_blob_sha1':blob(stored),'bytes':len(body),'sha256':sha(body)})
  expected={n:row[n] for n in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')};expected['classification']=row['intake_classification'];assert parsed==importer.json_bytes(expected)
  actual,ref=importer.parse_record(raw,row['collection'],row['number']);assert actual==row['source_record'] and ref==row['source_reference_verbatim'];sources.append({'id':identity,'exact_reparse':True,'files':fs});totals.update(raw_parsed_files_verified=2,exact_html_reparses=1)
  original=importer.canonical_record(row);before=copy.deepcopy(original);rowbefore=copy.deepcopy(row);after,na=native.apply(original,saved=row);assert na==action and original==before and row==rowbefore
  for name in set(before)-{'language_versions','text','content_kind','review','report_types','extraction'}:totals['metadata_leaf_equalities']+=leafcount(before[name],after[name])
  for name in before['extraction']:
   if name!='is_excerpt':totals['metadata_leaf_equalities']+=leafcount(before['extraction'][name],after['extraction'][name])
  fields={f['language']:f for f in r['fields']};assert set(fields)==set(LANG);selected={}
  for oldv,newv in zip(before['language_versions'],after['language_versions'],strict=True):
   lang=oldv['language'];t=oldv['text'];f=fields[lang];rk=(identity,lang);assert f['source_field']==LANG[lang] and f['text_sha256']==sha(t.encode()) and f['reviewed']==(rk in readings)
   if rk in readings:
    rr=readings[rk];assert rr['complete_own_field_read'] and originalfields[rk]['text']==t and rr['text_sha256']==sha(t.encode()) and rr['characters']==f['chars_reviewed']==len(t) and rr['utf8_bytes']==f['bytes_reviewed']==len(t.encode());totals.update(complete_fields_read=1,characters_read=len(t),utf8_bytes_read=len(t.encode()))
   else:assert f['chars_reviewed']==f['bytes_reviewed']==0
   for name in set(oldv)-{'text','scope','quotation_status','source','comments'}:totals['metadata_leaf_equalities']+=leafcount(oldv[name],newv[name])
   for name in oldv['source']:totals['metadata_leaf_equalities']+=leafcount(oldv['source'][name],newv['source'][name])
   pieces=[];contexts=[];spans=f['selected_spans']
   for s in spans:
    a,b=s['start'],s['end'];assert 0<=a<b<=len(t) and t[a:b].strip() and sha(t[a:b].encode())==s['sha256'];pieces.append((a,b,t[a:b]));totals.update(selected_spans=1,selected_characters=b-a)
   if spans:
    positions=[[s['start'],s['end']] for s in spans];assert newv['source']['text_spans']['quotation_spans']==positions and newv['text']==''.join(t[a:b] for a,b in positions);selected[lang]=newv['text'];totals['admitted_fields']+=1
    assert len(newv['source']['report_component_classifications'])==len({s['component_id'] for s in spans}) and newv['source'].get('source_report_count',1)==len({s['source_report_family_id'] for s in spans})==1
    voices.append({'id':identity,'language':lang,'classifications':newv['source']['report_component_classifications'],'source_report_family_count':1})
   else:assert newv['text'] is None;totals['reviewed_context_fields' if f['reviewed'] else 'unread_context_fields']+=1
   assert newv['source']['manual_review']['field_reviewed']==f['reviewed']
   for c in newv['comments']:
    a,b=c['source_span'];assert c['scope']=='source_context_not_narration' and c['text']==t[a:b] and c['source_text_sha256']==sha(t[a:b].encode());pieces.append((a,b,c['text']));contexts.append({'start':a,'end':b,'text':c['text'],'sha256':c['source_text_sha256']})
   cursor=0
   for a,b,body in sorted(pieces):assert a==cursor and b>a;cursor=b
   assert cursor==len(t) and ''.join(x[2] for x in sorted(pieces))==t;totals['lossless_field_partitions']+=1
   if f['reviewed']:fieldproof.append({**readings[rk],'text':t,'final_field_review':f,'source_context':contexts,'all_final_boundaries_accepted':True})
  if action=='register':assert after['text']=={'arabic':selected.get('ar'),'translation':selected.get('hi')}
  else:assert after['text']==before['text'] and all(f['reviewed'] for f in fields.values())
  assert after['number']['canonical'] is None and after['review']['independent_pro_qc']=='not_performed' and after['review']['certified_release_eligible'] is False;totals.update(source_occurrences=1);totals[action]+=1
 native.finish()
 assert totals['source_occurrences']==26 and totals['register']==25 and totals['exclude']==1 and totals['complete_fields_read']==55 and totals['characters_read']==23149 and totals['utf8_bytes_read']==48862
 assert totals['admitted_fields']==binding['approved_admitted_fields'] and totals['reviewed_context_fields']==55-binding['approved_admitted_fields'] and totals['unread_context_fields']==75 and totals['lossless_field_partitions']==130 and totals['raw_parsed_files_verified']==52 and totals['exact_html_reparses']==26
 out=ROOT/'publish';prefix='reports/web-source-resolution-20261113/checkpoint64f4-muslim-ibnmajah26-independent-audit';files=[]
 def emit(name,b):files.append(write(out,prefix+'/'+name,b))
 emit('independent-complete-source-first-readings.json.gz',gzip.compress(firstb,mtime=0));emit('independent_readings.py',(ROOT/'independent_readings.py').read_bytes());emit('final-field-boundary-assessment.json',(ROOT/'final-field-boundary-assessment.json').read_bytes());emit('final-amendment-comparison.json',enc(amendment));emit('final-source-proof.json.gz',gzip.compress(enc(sources),mtime=0));emit('final55-field-partitions.json.gz',gzip.compress(enc(fieldproof),mtime=0));emit('final-attribution-components.json.gz',gzip.compress(enc(voices),mtime=0));emit('final-candidate-binding.json',(ROOT/'final-candidate-binding.json').read_bytes());emit('audit_final_candidate.py',Path(__file__).read_bytes())
 emit('source-first-source-verification.json',(ROOT/'source-verification.json').read_bytes())
 for name in ('freeze_independent_source_first.py','freeze_candidate_findings.py','freeze_final_binding.py','independent-boundary-findings-v1.json','independent-reading-refinements.json','v1-candidate-binding.json'):
  emit(name,(ROOT/name).read_bytes())
 emit('accepted-full130-field-plan.json.gz',gzip.compress((ROOT/'accepted-field-plan-v1.json').read_bytes(),mtime=0))
 report={'schema':'hadith-bank-independent-source-review-audit-v2','result':'PASS','source_commit':COMMIT,'owner_manifest_sha256':sha(mb),'active_ledger_path':manifest['active_ledger_path'],'active_ledger_sha256':sha(ab),'source_baseline_sha256':sha(baseline),'source_first_reading_receipt_sha256':sha(firstb),'totals':dict(totals),'exact_amendment':dict(amendment),'source_only_ids':['deenhindi-muslim:2725'],'all_source_only_nonempty_fields_fully_read':True,'owner_file_bindings':filebindings,'open_findings':[],'initial_note_refinements_preserved':findings.get('initial_note_refinements',[]),'all_unaffected_fields_and_parent_dispositions_exact':True,'candidate_mutations_by_auditor':0,'engine_changes':0,'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed','certified_release_eligible':False,'scope':'Complete independent55-field original-first reading, then every exact candidate boundary and voice,52 saved source files/26 actual HTML reparses and native apply/finish. The final candidate restores exactly one8-character/12-byte source-rendered appraisal qualifier within the existing actor component; all other129 field definitions and25 parents remain exact. The original bounded250-held artifact and independently verified saved-GitHub23 supplement form a documented local union with unchanged export caps. Full repository export and actual reader/deployment remain separate checks.'}
 files.append(write(out,'reports/web-source-resolution-20261113/checkpoint64f4-muslim-ibnmajah26-independent-audit.json',enc(report)))
 delivery={'schema':'hadith-bank-independent-audit-delivery-v1','result':'PASS','source_commit':COMMIT,'owner_manifest_sha256':sha(mb),'active_ledger_sha256':sha(ab),'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)};write(ROOT,'delivery-manifest.json',enc(delivery))
 print(json.dumps({'result':'PASS','manifest_sha256':sha(enc(delivery)),'report_sha256':sha(enc(report)),'files':len(files),'bytes':delivery['total_bytes'],'totals':dict(totals),'amendment':dict(amendment)},indent=2))

if __name__=='__main__':main()
