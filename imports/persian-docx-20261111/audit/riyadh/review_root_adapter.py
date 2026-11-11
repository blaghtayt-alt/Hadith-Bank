#!/usr/bin/env python3
"""Read-only independent comparison of final upstream records to nine canonical imports."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import gzip, hashlib, json, re, sys
BASE=Path(__file__).resolve().parents[2]
WORK=BASE/'work'; REPO=BASE/'hadith-bank'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(line) for line in p.read_text(encoding='utf8').splitlines()]
inputs={}; files=[]
for f in ['hadith_only_primary_records.jsonl','variant_records.jsonl','explicit_hadith_quotation_records.jsonl']:
 rel='bukhari/'+f;files.append(rel)
 for r in read(WORK/rel):inputs.setdefault(r['source_id'],[]).append((r,rel))
for v in (1,2):
 slug=f'fa-muslim-mundhiri-tarshabi-v{v}';inputs[slug]=[]
 for f in [f'muslim-v{v}.main.jsonl',f'muslim-v{v}.confirmed-ancillary-hadiths.jsonl']:
  rel='muslim/'+f;files.append(rel);inputs[slug].extend((r,rel) for r in read(WORK/rel))
rel='riyadh/integration-records.jsonl';files.append(rel)
inputs['fa-riyadh-heravi-1394-digital']=[(r,rel) for r in read(WORK/rel)]
input_hashes={rel:sha(WORK/rel) for rel in files}
findings=[]; source_results=[]; all_canon=[]; all_upstream=[]
def check(ok,code,detail):
 if not ok:findings.append({'code':code,'detail':detail})
for slug,entries in sorted(inputs.items()):
 folder=REPO/'materials'/slug;canon=read(folder/'records.jsonl');byid={r['id']:r for r in canon};src=[r for r,_ in entries]
 all_canon+=canon;all_upstream+=src
 manifest=json.loads((folder/'manifest.json').read_text());missing=sorted({r['id'] for r in src}-set(byid));extra=sorted(set(byid)-{r['id'] for r in src})
 check(not missing and not extra,'ids_differ',{'source':slug,'missing':missing,'extra':extra})
 check(len(byid)==len(canon)==len(src),'source_count_or_duplicate',slug)
 check(manifest['records']['count']==len(canon),'manifest_count_mismatch',slug)
 check(manifest['records']['sha256']==sha(folder/'records.jsonl'),'canonical_hash_mismatch',slug)
 check(manifest['source']['sha256']==sha(folder/'source.docx'),'original_hash_mismatch',slug)
 check(manifest['display_policy']['qc_tags'] is False,'no_qc_policy_absent',slug)
 check(manifest['publication']['decision']=='owner_requested_public_source_import','incorrect_publication_decision',slug)
 if 'faiz-al-bari' in slug:meta_rel=f"bukhari/volume{slug[-1]}.metadata.json"
 elif 'muslim' in slug:meta_rel=f"muslim/muslim-v{slug[-1]}.metadata.json"
 else:meta_rel='riyadh/edition-metadata.json'
 sm=json.loads((WORK/meta_rel).read_text());cm=json.loads((folder/'source-metadata.json').read_text())
 check(all(cm.get(k)==v for k,v in sm.items()),'edition_metadata_loss',slug)
 text_diffs=[];ref_diffs=[];head_diffs=[];relation_diffs=[];locator_diffs=[];defect_diffs=[];grade_diffs=[]
 for r,upstream in entries:
  c=byid.get(r['id'])
  if c is None:continue
  ident=r['id']
  if c['text']!=r['text']:text_diffs.append(ident)
  refs=r.get('references') or {}
  if isinstance(refs,list):
   if c['references']['items'][:len(refs)]!=refs:ref_diffs.append(ident)
  else:
   cr={x.get('field'):x.get('value') for x in c['references']['items'] if isinstance(x,dict)}
   if any(cr.get(k)!=v for k,v in refs.items() if v is not None and v!=[]):ref_diffs.append(ident)
  if r.get('grade'):
   if c['grading'].get('source_assessment')!=r['grade']:grade_diffs.append(ident)
  if r.get('authenticity'):
   if any(c['grading'].get(k)!=v for k,v in r['authenticity'].items()):grade_diffs.append(ident)
  heads=r.get('source_headings',[]);labels=[x['text'] if isinstance(x,dict) else x for x in heads]
  tags=c['source_structure_tags']
  if c['source_headings']!=labels or len(tags)!=len(heads):head_diffs.append(ident)
  else:
   for h,label,tag in zip(heads,labels,tags):
    expected={k:v for k,v in h.items() if k not in ('text','raw_text','text_raw')} if isinstance(h,dict) else {}
    if not(tag['value_verbatim']==label and tag['origin']=='source_book_structure' and tag['source_id']==slug and tag.get('heading_metadata_as_supplied')==expected and tag.get('locator_scope')=='narration_under_heading'):head_diffs.append(ident)
  parents=set(r.get('parent_ids')or[])
  parents.update(v for v in [r.get('parent_id'),r.get('parent_record_id'),r.get('related_record_id')] if v)
  if {x['id'] for x in c['related_versions']}!=parents:relation_diffs.append(ident)
  if any(c['source_locator'].get(k)!=v for k,v in (r.get('source_locator')or{}).items()):locator_diffs.append(ident)
  if r.get('source_paragraphs') and c['source_locator'].get('paragraphs_by_role')!=r['source_paragraphs']:locator_diffs.append(ident)
  if r.get('aligned_translation_locator') and c['source_locator'].get('aligned_translation')!=r['aligned_translation_locator']:locator_diffs.append(ident)
  if c['source_defects']!=r.get('source_exceptions',r.get('source_notes',[])):defect_diffs.append(ident)
  check(c['commentary']=={'arabic':None,'translation':None} and c['footnotes']==[],'populated_commentary_field',ident)
  check(c['editorial_tags']['origin']=='import_pipeline_not_publisher','editorial_tag_origin',ident)
  check(not any(t.startswith(('qc:','review:')) for t in c['editorial_tags']['values']),'qc_tag_added',ident)
  check(c['language']=='fa' and 'language:fa' in c['editorial_tags']['values'],'language_label',ident)
  check(c['translation_provenance']['origin']=='human_translator_credited' and c['ai_translation'] is False,'translation_origin',ident)
  check(c['number']['canonical'] is None,'canonical_number_inferred',ident)
  check(c['extraction']['source_extraction_id']==ident and c['extraction']['source_extraction']==f'imports/persian-docx-20261111/extracted/{upstream}.gz','wrong_upstream_locator',ident)
 for code,values in [('text_difference',text_diffs),('reference_loss',ref_diffs),('heading_metadata_loss',head_diffs),('parent_relation_loss',relation_diffs),('source_locator_loss',locator_diffs),('source_defect_loss',defect_diffs),('source_grade_loss',grade_diffs)]:
  check(not values,code,{'source':slug,'ids':sorted(set(values))})
 source_results.append({'source_id':slug,'upstream_count':len(src),'canonical_count':len(canon),'missing_ids':missing,'extra_ids':extra,'text_difference_ids':text_diffs,'reference_difference_ids':ref_diffs,'source_metadata_preserved':all(cm.get(k)==v for k,v in sm.items()),'canonical_sha256':sha(folder/'records.jsonl'),'manifest_sha256':sha(folder/'manifest.json'),'original_docx_sha256':sha(folder/'source.docx'),'classification_counts':dict(Counter(r['extraction']['occurrence_role'] for r in canon))})
check(len({r['id'] for r in all_canon})==len(all_canon)==6805,'global_id_count',len(all_canon))
known=set(r['id'] for r in all_canon)
check(all(x['id'] in known for r in all_canon for x in r['related_versions']),'dangling_parent_relationship',None)
for rel in files:
 p=REPO/'imports/persian-docx-20261111/extracted'/(rel+'.gz')
 check(p.is_file() and gzip.decompress(p.read_bytes())==(WORK/rel).read_bytes(),'archived_upstream_mismatch',rel)
forbidden={'raw_text','display_text','source_text','raw_paragraphs','source_components','source_text_segments','excluded_side_commentary_paragraphs','excluded_side_commentary_spans','doctrinal_notes'}
leaks=[]
def walk(ident,x,path=''):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in forbidden and v:leaks.append({'id':ident,'path':path+k})
   walk(ident,v,path+k+'.')
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(ident,v,path+str(i)+'.')
for r in all_canon:walk(r['id'],r)
check(not leaks,'raw_or_excluded_commentary_field_leak',leaks)
markers=re.compile(r'(^|\n)\s*(?:ش\s*:|شرح\s*:|توضیح\s*:|یادداشت\s*:)|در بینش شیعه|شرحش قبلا گذشت|یادداشت مترجم')
marker_hits=[{'id':r['id'],'language':lang} for r in all_canon for lang,t in r['text'].items() if isinstance(t,str) and markers.search(t)]
check(not marker_hits,'known_excluded_note_marker',marker_hits)
byid={r['id']:r for r in all_canon}
check(byid['fa-faiz-al-bari-v5-p00697']['title']=='Hadith 1590' and byid['fa-faiz-al-bari-v5-p00697']['extraction']['occurrence_role']=='primary','translation_only_primary_label',None)
check(byid['fa-faiz-al-bari-v5-p01882']['title']=='Source narration fragment' and byid['fa-faiz-al-bari-v5-p01882']['extraction']['occurrence_role']=='primary','source_fragment_label',None)
sys.path.insert(0,str(REPO/'scripts'))
from material_registry import load_public_materials
projected=[r for g in load_public_materials(REPO)['groups'] for r in g if r['language']=='fa']
check(len(projected)==6805,'projection_count',len(projected))
check(all(r.get('display_policy',{}).get('qc_tags') is False for r in projected),'projection_no_qc_policy',None)
check(all(r['text_arabic']==byid[r['id']]['text']['arabic'] and r['text_translation']==byid[r['id']]['text']['translation'] for r in projected),'projection_text_change',None)
check(all(r['translation_provenance']['origin']=='human_translator_credited' for r in projected),'projection_translation_origin',None)
check(all(input_hashes[k]==sha(WORK/k) for k in files),'upstream_changed_during_review',None)
report={'schema':'hadith-bank-independent-adapter-review-v1','generated_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Independent read-only comparison across all nine Persian DOCX material adapters, final upstream extraction files, registered projection, and archived upstream payloads. This verifies adapter fidelity; upstream textual-boundary and authenticity review are separately documented.','status':'pass' if not findings else 'findings','adapter_script_sha256':sha(REPO/'scripts/import_persian_docx.py'),'source_documents':9,'upstream_records':len(all_upstream),'canonical_records':len(all_canon),'unique_ids':len(known),'projected_records':len(projected),'classification_counts':dict(Counter(r['extraction']['occurrence_role'] for r in all_canon)),'source_structure_tag_count':sum(len(r['source_structure_tags']) for r in all_canon),'records_with_parent_relations':sum(bool(r['related_versions']) for r in all_canon),'input_sha256':input_hashes,'checks':{'no_dropped_or_added_ids':True,'text_fields_equal_final_upstream':True,'all_nonempty_reference_fields_preserved':True,'source_grades_preserved':True,'edition_metadata_preserved':True,'heading_labels_and_source_heading_metadata_preserved':True,'source_locator_and_parent_relations_preserved':True,'source_defects_preserved':True,'original_docx_hashes_match_manifests':True,'canonical_hashes_and_counts_match_manifests':True,'archived_inputs_equal_final_upstream':True,'all_projected_records_no_qc_policy':True,'all_projected_records_human_translation_origin':True,'no_qc_or_review_editorial_tags':True,'no_populated_commentary_or_footnote_fields':True,'no_raw_or_excluded_commentary_field_leaks':True,'known_removed_note_markers_absent':True,'no_canonical_number_inferences':True,'inputs_stable_during_review':True},'resolved_findings':[{'issue':'Riyadh parent_record_id ignored','resolution':'24 upstream parent_record_id relationships now retained in related_versions.'},{'issue':'Two Bukhari translation-only primary occurrences mislabeled quotation excerpts','resolution':'1590 is Hadith1590/primary; incomplete surviving fragment is Source narration fragment/primary.'},{'issue':'Source heading tag location conflated with narration location','resolution':'Tag locator explicitly scoped to narration_under_heading; exact original heading metadata including paragraph/style/TOC retained separately.'},{'issue':'Four transient Muslim text differences during glyph recovery update','resolution':'Final upstream and canonical Arabic/Persian text now identical for all occurrences.'}],'findings':findings,'sources':source_results}
if findings:
 for key in report['checks']:report['checks'][key]='see_findings'
(REPO.parent/'work/riyadh/root-adapter-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'records':len(all_canon),'findings':findings,'roles':report['classification_counts'],'report_sha256':sha(REPO.parent/'work/riyadh/root-adapter-review.json')},ensure_ascii=False))
