#!/usr/bin/env python3
"""Build a PRIVATE six-language Hadith Bank candidate from official SQLite exports.
No translation, OCR, canonical-number inference, or network access is performed.
Run validate_hadeethenc.py separately. Publication requires independent Pro QC.
"""
import argparse, collections, hashlib, json, pathlib, shutil, sqlite3, sys
LANGUAGES={'ja':('ja','Japanese'),'tl':('fil','Filipino / Tagalog'),'vi':('vi','Vietnamese'),'zh':('zh-CN','Chinese'),'uz':('uz','Uzbek'),'hi':('hi','Hindi')}
def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def write_json(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def database(path):
 db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('SQLite integrity failure: '+str(path))
 return db

def build(input_root,output):
 manifest=json.loads((input_root/'export-manifest-v2.json').read_text(encoding='utf-8'))
 inputs={r['language']:r for r in manifest if r.get('local_path')}
 if set(inputs)!=set(LANGUAGES)|{'ar'}: raise ValueError('All six exports and Arabic are required')
 if output.exists() and any(output.iterdir()):raise ValueError('Output must be a new or empty directory')
 output.mkdir(parents=True,exist_ok=True)
 (output/'raw').mkdir();(output/'evidence').mkdir();(output/'reports').mkdir()
 for lang,meta in inputs.items():
  for key,hashkey in [('local_path','sqlite_sha256'),('archive_path','sha256')]:
   path=input_root/meta[key]
   if sha(path.read_bytes())!=meta[hashkey]:raise ValueError('Input checksum mismatch: '+str(path))
   shutil.copyfile(path,output/meta[key])
 shutil.copyfile(input_root/'export-manifest-v2.json',output/'evidence/export-manifest.json')
 for name in ['home.html','languages.json','api-readme.md','api-catalog.json','sample-ar-2962.json']:
  if (input_root/'evidence'/name).exists():shutil.copyfile(input_root/'evidence'/name,output/'evidence'/name)
 ardb=database(output/'raw/ar.sqlite')
 arrows=[dict(r) for r in ardb.execute('SELECT rowid AS source_rowid,* FROM hadeeths ORDER BY rowid')]
 ar_by_key=collections.defaultdict(list);ar_by_id=collections.defaultdict(list)
 for row in arrows:ar_by_key[(row['id'],row['version'])].append(row);ar_by_id[row['id']].append(row)
 ardb.close()
 source_rows={};categories={};relations={};version_ids={};occurrences=collections.defaultdict(list)
 for src,(lang,label) in LANGUAGES.items():
  db=database(output/'raw'/f'{src}.sqlite')
  source_rows[src]=[dict(r) for r in db.execute('SELECT rowid AS source_rowid,* FROM hadeeths ORDER BY id')]
  categories[src]={r['id']:dict(r) for r in db.execute('SELECT * FROM categories ORDER BY id')}
  relations[src]=collections.defaultdict(list)
  for r in db.execute('SELECT * FROM category_hadeeth ORDER BY id'):relations[src][r['hadeeth_id']].append(dict(r))
  db.close()
  for row in source_rows[src]:
   oid=f"hadeethenc:entry:{row['id']}:translation:{src}"
   rid=oid+':revision:'+sha(canonical(row))[:16]
   version_ids[(src,row['id'])]=(oid,rid);occurrences[row['id']].append(rid)
 exceptions=[];coverage=[];collections_index=[];field_stats=collections.Counter()
 for src,(lang,label) in LANGUAGES.items():
  meta=inputs[src];edition='sqlite-'+meta['sqlite_sha256'][:16]
  relative=pathlib.Path('languages')/lang/'books'/'hadeethenc'/'editions'/edition
  directory=output/relative;directory.mkdir(parents=True,exist_ok=True)
  write_json(directory/'categories.json',list(categories[src].values()))
  counts=collections.Counter();records_path=directory/'records.jsonl'
  with records_path.open('w',encoding='utf-8',newline='\n') as stream:
   for row in source_rows[src]:
    oid,rid=version_ids[(src,row['id'])];counts['records']+=1
    candidates=ar_by_key.get((row['id'],row['ar_version']),[])
    exact=[r for r in candidates if r['hadeeth']==row['hadeeth_ar']]
    aligned=exact[0] if len(exact)==1 else None
    if aligned: alignment='exact_provider_id_version_and_text_match';counts['arabic_exact_match']+=1
    elif not ar_by_id.get(row['id']):alignment='provider_id_missing_from_arabic_export'
    elif not candidates:alignment='stated_arabic_version_missing_from_arabic_export'
    elif len(exact)>1:alignment='ambiguous_identical_arabic_rows'
    else:alignment='same_id_version_but_arabic_text_differs'
    if not aligned:
     counts['arabic_alignment_exceptions']+=1
     exceptions.append({'record_id':rid,'language':lang,'kind':alignment,'source_id':row['id'],'stated_arabic_version':row['ar_version'],'available_versions':[r['version'] for r in ar_by_id.get(row['id'],[])],'action':'Keep embedded Arabic unchanged; do not attach current-version bibliography or grading.'})
    tags=[]
    for relation in relations[src].get(row['id'],[]):
     cat=categories[src].get(relation['category_id']);chain=[];seen=set();current=cat
     while current:
      if current['id'] in seen:
       exceptions.append({'record_id':rid,'kind':'category_cycle','category_id':current['id']});break
      seen.add(current['id']);chain.append(dict(current));parent=current['parent_id']
      if not parent:break
      current=categories[src].get(parent)
      if current is None:exceptions.append({'record_id':rid,'kind':'category_parent_not_exported','category_id':parent})
     tags.append({'origin':'publisher_taxonomy','source':'HadeethEnc.com','language':src,'relation_verbatim':relation,'category_verbatim':cat,'ancestors_including_self_verbatim':list(reversed(chain))})
    hints=None
    if row['hints'] is not None:
     try:hints=json.loads(row['hints'])
     except (ValueError,TypeError):exceptions.append({'record_id':rid,'kind':'hints_not_valid_json','action':'raw value retained'})
    missing=[]
    for name in ['hadeeth','hadeeth_ar','explanation','hints','grade','attribution']:
     if row[name] is None or row[name]=='':counts['missing_'+name]+=1;missing.append(name)
    refs=aligned['reference'] if aligned else None
    citations=[{'citation_id':rid+':reference:'+str(i+1),'text_verbatim':text,'classification':'unclassified_publisher_bibliography_line','canonical_occurrence_verified':False} for i,text in enumerate(refs.splitlines(keepends=True))] if refs else []
    record={
     'schema_version':'hadith-bank-hadeethenc-candidate-v1','record_id':rid,'occurrence_id':oid,
     'source_entry_id':str(row['id']),'language':lang,'source_language_code':src,
     'content_kind':'hadith_entry_as_classified_by_publisher','ai_translation':'unknown',
     'translation_origin':'published_digital_translation_authorship_not_established',
     'title_verbatim':row['title'],
     'texts':{'arabic_verbatim':row['hadeeth_ar'],'translation_verbatim':row['hadeeth']},
     'commentary':{'translation_explanation_verbatim':row['explanation'],'translation_benefits_raw_json_verbatim':row['hints'],'translation_benefits_decoded':hints,'arabic_explanation_verbatim':aligned['explanation'] if aligned else None,'arabic_benefits_raw_json_verbatim':aligned['hints'] if aligned else None,'arabic_word_meanings_raw_json_verbatim':aligned['words_meanings'] if aligned else None},
     'footnotes':{'separately_supplied':False,'extracted_fields':None,'note':'Inline source footnotes and markers remain verbatim; not segmented.'},
     'narration':{'narrator_names':None,'isnad_verbatim':None,'narrator_intro_verbatim':None,'status':'Source narrator wording remains in full Hadith; separate structured segmentation not performed.'},
     'grading':{'source':'HadeethEnc.com','translation_label_verbatim':row['grade'],'arabic_label_verbatim':aligned['grade'] if aligned else None,'named_assessor':None,'scope':'publisher entry; precise route/clause scope not independently verified','verification':'publisher_reported_not_independently_graded'},
     'source_references':{'translation_attribution_verbatim':row['attribution'],'arabic_attribution_verbatim':aligned['attribution'] if aligned else None,'bibliography_verbatim':refs,'citation_lines':citations,'canonical_occurrences':[],'canonical_mapping_status':'not independently verified; provider entry ID is not a collection Hadith number'},
     'publication':{'translation_work':'HadeethEnc.com — Encyclopedia of Translated Prophetic Hadiths','publisher':'HadeethEnc.com','translator':None,'compiler':None,'edition':None,'translation_version':None,'source_arabic_version':row['ar_version'],'digital_snapshot_sha256':meta['sqlite_sha256'],'printed_page':None,'pdf_page':None},
     'topic_tags':tags,
     'editorial_tags':{'origin':'import_pipeline_not_publisher','values':['source:hadeethenc','language:'+lang,'method:digital_sqlite','review:pending_independent_pro','ai_translation:unknown']},
     'arabic_alignment':{'status':alignment,'source_arabic_version':row['ar_version'],'matched_arabic_rowid':aligned['source_rowid'] if aligned else None,'matched_arabic_row_sha256':sha(canonical(aligned)) if aligned else None,'embedded_arabic_sha256':sha(row['hadeeth_ar'].encode('utf-8')),'scope':'Publisher-version and codepoint equality only; not proof of canonical identity or translation semantics.'},
     'provenance':{'acquisition_method':'official_digital_sqlite_export','ocr_used':False,'ai_translation_created_during_import':False,'retrieved_at':meta['retrieved_at'],'source_download_url':meta['source_url'],'source_download_final_url':meta['final_url'],'source_entry_api_locator':f"https://hadeethenc.com/api/v1/hadeeths/one/?language={src}&id={row['id']}",'local_database_path':meta['local_path'],'local_archive_path':meta['archive_path'],'database_sha256':meta['sqlite_sha256'],'archive_sha256':meta['sha256'],'table':'hadeeths','source_rowid':row['source_rowid'],'source_row_sha256':sha(canonical(row)),'arabic_database_path':'raw/ar.sqlite','arabic_database_sha256':inputs['ar']['sqlite_sha256'],'version_note':'ar_version identifies Arabic source revision, not a verified translation edition; HTTP Last-Modified is not used as publication date.'},
     'related_versions':{'basis':'same publisher entry ID, not asserted canonical narration identity','record_ids':[x for x in occurrences[row['id']] if x!=rid]},
     'rights':{'status':'conditional_republication_terms_require_compliance','publisher':'HadeethEnc.com','terms_source_url':'https://hadeethenc.com/en/home','local_terms_evidence':'evidence/home.html','translation_version_disclosure':'unresolved_not_in_export','publication_authorized_by_this_import':False},
     'review':{'release_status':'private_candidate','independent_pro_qc':'pending','human_review':'not_performed','authenticity_review':'not_performed','mechanical_validation_report':'reports/validation.json','release_eligible':False},
     'metadata_gaps':['translation_author','translation_version','canonical_collection_occurrence_mapping','named_grading_assessor_and_scope','separate_narrator_isnad_segmentation','independent_pro_qc']+(['exact_arabic_revision_alignment'] if not aligned else []),
     'source_missing_content_fields':missing,
     'source_row_verbatim':row,
     'correction_log':[]}
    stream.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
   
  stats={'language':lang,'source_code':src,'language_name':label,**dict(counts),'publisher_categories':len(categories[src]),'publisher_category_links':sum(len(x) for x in relations[src].values()),'records_path':(relative/'records.jsonl').as_posix(),'records_sha256':sha(records_path.read_bytes()),'edition_snapshot':edition}
  coverage.append(stats);collections_index.append({'language':lang,'source_code':src,'book':'hadeethenc','edition':edition,'records_path':stats['records_path'],'count':counts['records'],'release_status':'private_candidate'})
  write_json(directory/'manifest.json',{'source':meta,'coverage':stats,'translation_version':None,'ar_version_is_not_translation_version':True,'independent_pro_qc':'pending','publication_allowed':False})
 total=sum(x['records'] for x in coverage)
 summary={'schema':'hadeethenc-import-summary-v1','selected_languages':[x[0] for x in LANGUAGES.values()],'total_translation_entries':total,'unique_provider_entry_ids':len(occurrences),'scope':'Every row in six downloaded official SQLite snapshots; not a claim to cover every live API entry or all world Hadith.','actual_hadith_text_included':True,'all_translations_include_embedded_arabic':all(not x.get('missing_hadeeth_ar') for x in coverage),'arabic_exact_alignment_count':sum(x.get('arabic_exact_match',0) for x in coverage),'arabic_alignment_exception_count':sum(x.get('arabic_alignment_exceptions',0) for x in coverage),'per_language':coverage,'total_exception_items':len(exceptions),'independent_pro_qc_performed':False,'publication_status':'private_candidate_not_published','published_translation_entries':0,'source':'HadeethEnc.com','acquisition_method':'official_SQLite_exports','new_translations_generated':0}
 write_json(output/'reports/summary.json',summary);write_json(output/'reports/exceptions.json',exceptions)
 write_json(output/'collections.json',{'collections':collections_index})
 write_json(output/'PUBLICATION-GATE.json',{'allowed':False,'reasons':['Independent Pro QC over exact candidate not performed.','Translation version/edition disclosure absent from exports must be resolved.','Per-record metadata and Arabic alignment exceptions require review.'],'release_eligible_records':0})
 write_json(output/'FIELD-MAPPING.json',{'verbatim_mapping':{'hadeeth':'texts.translation_verbatim','hadeeth_ar':'texts.arabic_verbatim','title':'title_verbatim','explanation':'commentary.translation_explanation_verbatim','hints':'commentary.translation_benefits_raw_json_verbatim','grade':'grading.translation_label_verbatim','attribution':'source_references.translation_attribution_verbatim','ar_version':'publication.source_arabic_version'},'all_source_columns':'source_row_verbatim','source_bibliography_rule':'Only attach from Arabic row with exact ID, version and text equality.','ai_translation':'unknown unless independently evidenced for exact source passage; no new translation created'})
 (output/'README.md').write_text('# HadeethEnc private Hadith Bank candidate\n\nActual translated and Arabic texts are stored locally under languages/. Raw official exports are retained under raw/. This candidate is not approved for public publication.\n\nSee reports/summary.json, reports/exceptions.json, reports/validation.json and PUBLICATION-GATE.json. The bank codes fil and zh-CN retain source codes tl and zh without asserting a different source locale. Uzbek text/script is preserved as supplied. Source comments and genuine defects are never silently corrected.\n\nPublisher: HadeethEnc.com. Republish only in compliance with its terms, source version disclosures and the bank independent-Pro-QC gate.\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
 return summary
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 try:build(a.input.resolve(),a.output.resolve())
 except (OSError,ValueError,KeyError,sqlite3.Error) as e:sys.exit('Import failed: '+str(e))
