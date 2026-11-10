#!/usr/bin/env python3
"""Offline mechanical verification of the uploaded HadeethEnc source snapshot.
This does not perform independent Pro QC, semantic translation review or authentication.
"""
import argparse,collections,copy,hashlib,json,pathlib,sqlite3,sys
STATUS='published_unreviewed_source_import'
LANGS={'ja':'ja','tl':'fil','vi':'vi','zh':'zh-CN','uz':'uz','hi':'hi'}
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def at(obj,path):
 for key in path.split('.'):obj=obj[key]
 return obj
def db(path):
 con=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row;return con

def validate(root):
 root=root.resolve();errors=[];stats=collections.Counter();language_stats=[];all_ids=set();families=collections.defaultdict(set);links={}
 def require(test,message):
  if not test:errors.append(message)
 def local(relative):
  path=(root/relative).resolve()
  if not path.is_relative_to(root) or not path.is_file():raise ValueError('Missing/unsafe local file: '+str(relative))
  return path
 registry=load(local('datasets/hadeethenc/collections.json'));support=registry['support_directory']
 exports=load(local(support+'/evidence/export-manifest.json'));inputs={x['language']:x for x in exports}
 require(set(inputs)==set(LANGS)|{'ar'},'Wrong source export set')
 for src,meta in inputs.items():
  for field,hashkey in [('local_path','sqlite_sha256'),('archive_path','sha256')]:
   require(sha(local(support+'/'+meta[field]).read_bytes())==meta[hashkey],'Raw source digest '+src+' '+field);stats['raw_files_hashed']+=1
 adb=db(local(support+'/raw/ar.sqlite'));require(adb.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Arabic SQLite integrity')
 arabic=collections.defaultdict(list)
 for row in adb.execute('SELECT rowid AS source_rowid,* FROM hadeeths'):
  a=dict(row);arabic[(a['id'],a['version'])].append(a)
 adb.close()
 mapping={'hadeeth':'texts.translation_verbatim','hadeeth_ar':'texts.arabic_verbatim','title':'title_verbatim','explanation':'commentary.translation_explanation_verbatim','hints':'commentary.translation_benefits_raw_json_verbatim','grade':'grading.translation_label_verbatim','attribution':'source_references.translation_attribution_verbatim','ar_version':'publication.source_arabic_version'}
 require({x['source_code'] for x in registry['collections']}==set(LANGS),'Wrong target language scope')
 schema=load(local('schemas/hadeethenc.public-record.schema.json'))
 for collection in registry['collections']:
  src=collection['source_code'];lang=LANGS[src];counts=collections.Counter();seen=set();candidate_digest=hashlib.sha256()
  con=db(local(support+'/raw/'+src+'.sqlite'));require(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity '+src)
  original={r['id']:dict(r) for r in con.execute('SELECT rowid AS source_rowid,* FROM hadeeths')}
  cats=[dict(r) for r in con.execute('SELECT * FROM categories ORDER BY id')];catmap={r['id']:r for r in cats};rels=collections.defaultdict(list)
  for row in con.execute('SELECT * FROM category_hadeeth ORDER BY id'):rels[row['hadeeth_id']].append(dict(row))
  con.close()
  require(load(local(collection['categories_path']))==cats,'Category table '+lang)
  require(sha(local(collection['categories_path']).read_bytes())==collection['categories_sha256'],'Category hash '+lang)
  path=local(collection['records_path']);require(sha(path.read_bytes())==collection['records_sha256'],'Record-file hash '+lang)
  manifest=load(local(collection['manifest_path']));require(manifest['public_records']==collection,'Manifest registry mismatch '+lang)
  with path.open('rb') as stream:
   for line in stream:
    r=json.loads(line);rid=r['record_id'];sid=int(r['source_entry_id']);s=original.get(sid)
    counts['records']+=1;stats['records_compared']+=1
    require(s is not None,'Unexpected source entry '+rid)
    if s is None:continue
    require(sid not in seen,'Repeated source occurrence '+rid);seen.add(sid)
    require(rid not in all_ids,'Duplicate record ID '+rid);all_ids.add(rid);families[sid].add(rid);links[rid]=(sid,set(r['related_versions']['record_ids']))
    require(set(schema['required']).issubset(r),'Required record keys '+rid)
    require(r['schema_version']=='hadith-bank-hadeethenc-record-v2','Record schema '+rid)
    require(r['language']==lang and r['source_language_code']==src,'Language '+rid)
    require(r['source_row_verbatim']==s,'Full original row differs '+rid)
    require(r['provenance']['source_row_sha256']==sha(canonical(s)),'Source-row digest '+rid)
    require(r['record_id']==r['occurrence_id']+':revision:'+sha(canonical(s))[:16],'Stable source revision ID '+rid)
    require(r['ai_translation']=='unknown','Unevidenced translation authorship '+rid)
    require(r['review']['release_status']==STATUS and r['review']['publicly_available'] is True,'Public status '+rid)
    require(r['review']['independent_pro_qc']=='pending' and r['review']['release_eligible'] is False and r['review']['certified_release_eligible'] is False,'Incorrect approval claim '+rid)
    require(r['publication']['translation_version'] is None,'Invented translation version '+rid)
    require(r['rights']['repository_upload_authorized_by_owner'] is True,'Missing owner upload decision '+rid)
    for sourcefield,dest in mapping.items():
     require(at(r,dest)==s[sourcefield],'Verbatim field differs '+rid+' '+sourcefield);stats['mapped_fields_compared']+=1
     if isinstance(s[sourcefield],str):stats['source_codepoints_compared']+=len(s[sourcefield])
    require(bool(r['texts']['translation_verbatim']) and bool(r['texts']['arabic_verbatim']),'Missing actual Hadith text '+rid)
    require([t['relation_verbatim'] for t in r['topic_tags']]==rels[sid],'Source topic relations '+rid)
    for t in r['topic_tags']:
     require(t['category_verbatim']==catmap.get(t['relation_verbatim']['category_id']),'Source topic category '+rid)
     require(t['origin']=='publisher_taxonomy','Topic provenance '+rid)
    matches=[a for a in arabic.get((s['id'],s['ar_version']),[]) if a['hadeeth']==s['hadeeth_ar']]
    if len(matches)==1:
     a=matches[0];counts['exact_arabic_alignment']+=1
     require(r['arabic_alignment']['matched_arabic_rowid']==a['source_rowid'],'Exact Arabic row binding '+rid)
     require(r['arabic_alignment']['matched_arabic_row_sha256']==sha(canonical(a)),'Exact Arabic row hash '+rid)
     for dest,sfield in [('source_references.bibliography_verbatim','reference'),('source_references.arabic_attribution_verbatim','attribution'),('grading.arabic_label_verbatim','grade'),('commentary.arabic_explanation_verbatim','explanation'),('commentary.arabic_benefits_raw_json_verbatim','hints'),('commentary.arabic_word_meanings_raw_json_verbatim','words_meanings')]:require(at(r,dest)==a[sfield],'Arabic enrichment differs '+rid+' '+dest)
     require(''.join(x['text_verbatim'] for x in r['source_references']['citation_lines'])==(a['reference'] or ''),'Bibliography loss '+rid)
    else:
     counts['arabic_alignment_exceptions']+=1
     require(r['arabic_alignment']['matched_arabic_rowid'] is None,'Unverified Arabic binding '+rid)
     require(r['source_references']['bibliography_verbatim'] is None and r['grading']['arabic_label_verbatim'] is None,'Wrong-version metadata '+rid)
    for key in ['local_database_path','local_archive_path','arabic_database_path']:local(r['provenance'][key])
    local(r['rights']['local_terms_evidence']);local(r['bank_metadata']['publication_status']);local(r['bank_metadata']['metadata_change_log'])
    # Reconstruct the entire previous candidate line: every non-publication field must be identical.
    prior=copy.deepcopy(r);meta=prior.pop('bank_metadata');prior['schema_version']='hadith-bank-hadeethenc-candidate-v1'
    for key in ['local_database_path','local_archive_path','arabic_database_path']:
     value=prior['provenance'][key];require(value.startswith(support+'/'),'Out-of-snapshot locator '+rid);prior['provenance'][key]=value[len(support)+1:]
    prior['rights']['local_terms_evidence']='evidence/home.html';prior['rights'].pop('repository_upload_authorized_by_owner')
    for key in ['prior_release_status','publicly_available','certified_release_eligible']:prior['review'].pop(key)
    prior['review']['release_status']='private_candidate';prior['review']['mechanical_validation_report']='reports/validation.json'
    prior_line=(json.dumps(prior,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
    require(sha(prior_line)==meta['prior_candidate_line_sha256'],'Unexpected candidate-to-public change '+rid)
    candidate_digest.update(prior_line);stats['full_candidate_lines_reconstructed']+=1
  require(seen==set(original),'Incomplete snapshot row coverage '+lang)
  require(counts['records']==collection['count'],'Count mismatch '+lang)
  require(candidate_digest.hexdigest()==manifest['original_candidate_records_sha256'],'Full candidate reconstruction hash '+lang)
  language_stats.append({'language':lang,**dict(counts)})
 for rid,(sid,related) in links.items():require(related==families[sid]-{rid},'Related occurrence links '+rid)
 policy=load(local('datasets/hadeethenc/PUBLICATION-STATUS.json'))
 require(policy['owner_requested_public_upload'] is True and policy['verified_release_allowed'] is False,'Publication/approval distinction lost')
 summary=load(local('reports/hadeethenc/2026-11-11/public/summary.json'))
 require(stats['records_compared']==summary['total_translation_entries']==8423,'Total corpus count')
 require(sum(x.get('arabic_alignment_exceptions',0) for x in language_stats)==267,'Alignment exception total')
 file_manifest=root/'datasets/hadeethenc/FILE-MANIFEST.json'
 if file_manifest.exists():
  for entry in load(file_manifest)['files']:
   data=local(entry['path']).read_bytes();require(len(data)==entry['bytes'] and sha(data)==entry['sha256'],'Published-file manifest mismatch '+entry['path'])
 return {'success':not errors,'validation_type':'full_programmatic_source_comparison_not_independent_Pro_QC','coverage':dict(stats),'languages':language_stats,'source_text_changes':0 if not errors else None,'all_runtime_sources_local':True,'network_required':False,'independent_pro_qc_performed':False,'human_review_performed':False,'publication_status':STATUS,'certified_release_eligible':False,'errors':errors,'error_count':len(errors)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]);p.add_argument('--report',type=pathlib.Path);args=p.parse_args()
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 report=validate(args.root);out=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
 if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_bytes(out.encode('utf-8'))
 print(out,end='');return 0 if report['success'] else 1
if __name__=='__main__':
 try:sys.exit(main())
 except (OSError,ValueError,KeyError,TypeError,sqlite3.Error) as error:sys.exit('Validation failed: '+str(error))
