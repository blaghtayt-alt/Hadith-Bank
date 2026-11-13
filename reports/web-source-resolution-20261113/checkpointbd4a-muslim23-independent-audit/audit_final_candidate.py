#!/usr/bin/env python3
"""Independent exact amendment, source preservation and native partition audit."""
import collections,copy,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent;OWNER=BASE/'phase18-checkpointbd4a-muslim23-review';SOURCE=BASE/'phase16-successor-acquisition-monitor/held-evidence'
COMMIT='bd4a75695d3c695e98bf8efa5ce07764ac5e2633';sha=lambda b:hashlib.sha256(b).hexdigest();blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
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
 binding=load(ROOT/'final-candidate-binding.json');assert binding['all49_complete_original_fields_and_candidate_boundaries_independently_read'] and binding['owner_accepted_all_requested_changes']
 manifestpath=Path(binding['owner_manifest_path']);mb=manifestpath.read_bytes();assert sha(mb)==binding['owner_manifest_sha256'];manifest=json.loads(mb);PUBLISHED=OWNER/binding['owner_output_directory']
 filebindings=[]
 for f in manifest['files']:
  b=checked(PUBLISHED,f['path']);assert len(b)==f['bytes'] and sha(b)==f['sha256']
  if 'git_blob_sha1' in f:assert blob(b)==f['git_blob_sha1']
  filebindings.append({'path':f['path'],'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)})
 ab=checked(PUBLISHED,manifest['active_ledger_path']);assert sha(ab)==binding['active_ledger_sha256']==manifest['active_ledger_sha256'];doc=json.loads(gzip.decompress(ab));assert doc['source_commit']==COMMIT
 before_m=load(OWNER/'delivery-manifest-v1.json');before_raw=checked(OWNER/'publish-v1',before_m['active_ledger_path']);assert sha(before_raw)=='3f766fcad01ff7f9443869386bf0027d03136e8ce341e8292883a70194acd4ee'
 old={r['occurrence_id']:r for r in json.loads(gzip.decompress(before_raw))['records']};records={r['occurrence_id']:r for r in doc['records']};assert old.keys()==records.keys() and len(records)==len(doc['records'])==23
 findings=load(ROOT/'independent-boundary-findings-v1.json');assert sha((ROOT/'independent-boundary-findings-v1.json').read_bytes())=='af74b0e0e921e76eefbe4f4b0d3afcc06c47a9f55b2804636c0bb33f8e0c6082'
 changes=collections.defaultdict(list)
 for f in findings['findings']+[findings['isolated_separator_space']]:changes[(f['id'],f['language'])].append(f)
 amendment=collections.Counter();changeproof=[]
 for identity,r in records.items():
  previous=old[identity];assert {k:v for k,v in r.items() if k!='fields'}=={k:v for k,v in previous.items() if k!='fields'}
  if r==previous:amendment['unchanged_whole_parents']+=1
  for a,b in zip(previous['fields'],r['fields'],strict=True):
   k=(identity,a['language']);expected=labels(a);original=copy.deepcopy(expected)
   if k in changes:
    for f in changes[k]:
     for pos in range(f['start'],f['end']):
      if f['action']=='context':assert pos in expected;expected.pop(pos)
      else:assert pos not in expected;expected[pos]={name:f[name] for name in ('component_id','report_type','speaker','source_report_family_id')}
    assert labels(b)==expected,k
    refinement=b['boundary_refinement'];assert 'boundary_refinement' not in a and set(refinement)=={'final_source_bound_judgment','independent_findings_sha256','initial_source_first_note_preserved','version'}
    assert refinement['version']=='v2' and refinement['initial_source_first_note_preserved'] is True and refinement['independent_findings_sha256']=='af74b0e0e921e76eefbe4f4b0d3afcc06c47a9f55b2804636c0bb33f8e0c6082' and refinement['final_source_bound_judgment'].startswith('Final v2:')
    ignored={'selected_spans','reason','explicit_context_cuts','retained_meaningful_structures','reviewed_context_spans','boundary_refinement'}
    assert {n:v for n,v in a.items() if n not in ignored}=={n:v for n,v in b.items() if n not in ignored},k
    amendment['changed_fields']+=1;amendment['restored_characters']+=len(expected.keys()-original.keys());amendment['contextualized_characters_including_one_separator']+=len(original.keys()-expected.keys())
    changeproof.append({'id':identity,'language':a['language'],'removed_positions':sorted(original.keys()-expected.keys()),'restored_positions':sorted(expected.keys()-original.keys()),'all_retained_types_speakers_components_families_exact':True})
   else:
    assert a==b,k;amendment['unchanged_read_fields' if a['reviewed'] else 'unchanged_unread_fields']+=1
 assert dict(amendment)=={'changed_fields':8,'restored_characters':119,'contextualized_characters_including_one_separator':151,'unchanged_unread_fields':66,'unchanged_read_fields':41,'unchanged_whole_parents':18},dict(amendment)
 sys.path.insert(0,str(BASE/'hindi-resolve/work/scripts'));import import_deenhindi as importer;import web_source_reviews as reviews;import web_commentary_quotes as quotes
 assert sha(Path(importer.__file__).read_bytes())=='c2b6df1d243b7e9c695358d9f06221c4cba45e880a1a215e4ef697008ed144d0'
 assert sha(Path(reviews.__file__).read_bytes()+Path(quotes.__file__).read_bytes())=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
 inbytes=(ROOT/'input/cohort.jsonl').read_bytes();assert sha(inbytes)=='cf22bcd083b4cdb70cce62ca81bb73a60571ec62da390d980e8c584bcd65f29e';rows={x['collection']+':'+x['number']:x for x in map(json.loads,inbytes.splitlines())}
 baseline=checked(PUBLISHED,doc['source_ledger_path']);assert sha(baseline)==doc['source_ledger_sha256'];plain=gzip.decompress(baseline);assert sha(plain)==doc['source_ledger_uncompressed_sha256'];assert {x['collection']+':'+x['number']:x for x in map(json.loads,plain.splitlines())}==rows
 firstb=(ROOT/'complete-independent-source-first-readings.json').read_bytes();assert sha(firstb)=='737b95542c68cf40ff989b2e2a5d46b4b2415867d0f2e05fab69a631ed90a37d';first=json.loads(firstb);assert first['primary_candidate_or_notes_inspected_before_freeze'] is False
 readings={(f['occurrence_id'],f['language']):f for f in first['fields']};assert len(readings)==49 and first['characters_read']==35043 and first['utf8_bytes_read']==72663
 originalfields={(f['occurrence_id'],f['language']):f for f in map(json.loads,(ROOT/'input/full-field-reading-input-49.jsonl').read_bytes().splitlines())}
 artifact=load(SOURCE/'evidence-manifest.json');assert sha((SOURCE/'evidence-manifest.json').read_bytes())=='72f36a11482b3f630570d2c9298e73039fe6bf2978a17083bb17a3482981302f' and artifact['saved_head']==COMMIT
 artifactrows={x['collection']+':'+x['number']:x for x in map(json.loads,(SOURCE/'held-source-records.jsonl').read_bytes().splitlines())};assert len(artifactrows)==192 and all(artifactrows[k]==v for k,v in rows.items());states=load(SOURCE/'held-state-entries.json')
 native=reviews.SourceReviews(PUBLISHED,'deenhindi');assert set(native.decisions)==set(records);totals=collections.Counter();sources=[];fieldproof=[];voices=[]
 for key,row in rows.items():
  identity='deenhindi-'+key;r=records[identity];action='exclude' if key=='muslim:2445' else 'register'
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
 assert totals['source_occurrences']==23 and totals['register']==22 and totals['exclude']==1 and totals['complete_fields_read']==49 and totals['characters_read']==35043 and totals['utf8_bytes_read']==72663
 assert totals['admitted_fields']==44 and totals['reviewed_context_fields']==5 and totals['unread_context_fields']==66 and totals['lossless_field_partitions']==115 and totals['raw_parsed_files_verified']==46 and totals['exact_html_reparses']==23
 out=ROOT/'publish';prefix='reports/web-source-resolution-20261113/checkpointbd4a-muslim23-independent-audit';files=[]
 def emit(name,b):files.append(write(out,prefix+'/'+name,b))
 emit('independent-complete-source-first-readings.json.gz',gzip.compress(firstb,mtime=0));emit('independent_readings.py',(ROOT/'independent_readings.py').read_bytes());emit('independent-boundary-findings-v1.json',(ROOT/'independent-boundary-findings-v1.json').read_bytes());emit('final-amendment-comparison.json',enc({'result':'PASS','counts':dict(amendment),'fields':changeproof,'initial_notes_unchanged':True}));emit('final-source-proof.json.gz',gzip.compress(enc(sources),mtime=0));emit('final49-field-partitions.json.gz',gzip.compress(enc(fieldproof),mtime=0));emit('final-attribution-components.json.gz',gzip.compress(enc(voices),mtime=0));emit('final-candidate-binding.json',(ROOT/'final-candidate-binding.json').read_bytes());emit('audit_final_candidate.py',Path(__file__).read_bytes())
 report={'schema':'hadith-bank-independent-source-review-audit-v2','result':'PASS','source_commit':COMMIT,'owner_manifest_sha256':sha(mb),'active_ledger_path':manifest['active_ledger_path'],'active_ledger_sha256':sha(ab),'source_baseline_sha256':sha(baseline),'source_first_reading_receipt_sha256':sha(firstb),'totals':dict(totals),'exact_amendment':dict(amendment),'source_only_ids':['deenhindi-muslim:2445'],'all_source_only_nonempty_fields_fully_read':True,'owner_file_bindings':filebindings,'open_findings':[],'initial_note_refinements_preserved':findings['initial_note_refinements'],'all_unaffected_fields_and_parent_dispositions_exact':True,'candidate_mutations_by_auditor':0,'engine_changes':0,'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed','certified_release_eligible':False,'scope':'Complete independent49-field original-first reading, then all exact candidate boundaries/voices, the agreed eight-field amendment,46 saved source files/23 HTML reparses and native apply/finish. Full repository export and actual reader/deployment remain separate checks.'}
 files.append(write(out,'reports/web-source-resolution-20261113/checkpointbd4a-muslim23-independent-audit.json',enc(report)))
 delivery={'schema':'hadith-bank-independent-audit-delivery-v1','result':'PASS','source_commit':COMMIT,'owner_manifest_sha256':sha(mb),'active_ledger_sha256':sha(ab),'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)};write(ROOT,'delivery-manifest.json',enc(delivery))
 print(json.dumps({'result':'PASS','manifest_sha256':sha(enc(delivery)),'report_sha256':sha(enc(report)),'files':len(files),'bytes':delivery['total_bytes'],'totals':dict(totals),'amendment':dict(amendment)},indent=2))

if __name__=='__main__':main()
