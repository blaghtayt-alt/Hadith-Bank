#!/usr/bin/env python3
"""Full mechanical comparison of a private candidate against official SQLite bytes.
This is NOT independent Pro QC, semantic translation review or authentication.
"""
import argparse,collections,hashlib,json,pathlib,sqlite3,sys
LANGS={'ja':'ja','tl':'fil','vi':'vi','zh':'zh-CN','uz':'uz','hi':'hi'}
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def at(o,path):
 for k in path.split('.'):o=o[k]
 return o
def connect(p):
 d=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);d.row_factory=sqlite3.Row;return d

def validate(root):
 errors=[];stats=collections.Counter();language_stats=[];ids=set();families=collections.defaultdict(set);stored_links={}
 def require(test,message):
  if not test:errors.append(message)
 def local(relative):
  p=(root/relative).resolve()
  if not p.is_relative_to(root.resolve()):raise ValueError('Unsafe local path '+relative)
  return p
 manifest=load(root/'evidence/export-manifest.json');inputs={x['language']:x for x in manifest}
 for src,meta in inputs.items():
  for path_key,hash_key in [('local_path','sqlite_sha256'),('archive_path','sha256')]:
   require(digest(local(meta[path_key]).read_bytes())==meta[hash_key],'Raw digest mismatch '+src+' '+path_key);stats['raw_files_hashed']+=1
 adb=connect(root/'raw/ar.sqlite');arrows=[dict(r) for r in adb.execute('SELECT rowid AS source_rowid,* FROM hadeeths')];adb.close()
 ar_by_row={x['source_rowid']:x for x in arrows};ar_by_key=collections.defaultdict(list)
 for x in arrows:ar_by_key[(x['id'],x['version'])].append(x)
 cols=load(root/'collections.json')['collections']
 require({c['source_code'] for c in cols}==set(LANGS),'Wrong language scope')
 mapping={'hadeeth':'texts.translation_verbatim','hadeeth_ar':'texts.arabic_verbatim','title':'title_verbatim','explanation':'commentary.translation_explanation_verbatim','hints':'commentary.translation_benefits_raw_json_verbatim','grade':'grading.translation_label_verbatim','attribution':'source_references.translation_attribution_verbatim','ar_version':'publication.source_arabic_version'}
 for c in cols:
  src=c['source_code'];lang=LANGS[src];db=connect(root/'raw'/f'{src}.sqlite')
  raw={x['id']:dict(x) for x in db.execute('SELECT rowid AS source_rowid,* FROM hadeeths')}
  cats=[dict(x) for x in db.execute('SELECT * FROM categories ORDER BY id')];cats_by_id={x['id']:x for x in cats}
  rels=collections.defaultdict(list)
  for r in db.execute('SELECT * FROM category_hadeeth ORDER BY id'):rels[r['hadeeth_id']].append(dict(r))
  db.close();seen=set();counts=collections.Counter();record_path=local(c['records_path'])
  m=load(record_path.parent/'manifest.json');require(digest(record_path.read_bytes())==m['coverage']['records_sha256'],'Records digest '+lang)
  require(load(record_path.parent/'categories.json')==cats,'Taxonomy table mismatch '+lang)
  with record_path.open(encoding='utf-8') as f:
   for line in f:
    r=json.loads(line);rid=r['record_id'];source_id=int(r['source_entry_id']);s=raw.get(source_id);counts['records']+=1;stats['records_compared']+=1
    require(s is not None,'Unknown source ID '+rid)
    if s is None:continue
    require(source_id not in seen,'Duplicated provider occurrence '+rid);seen.add(source_id)
    require(rid not in ids,'Duplicate record ID '+rid);ids.add(rid);families[source_id].add(rid);stored_links[rid]=(source_id,set(r['related_versions']['record_ids']))
    require(r['source_row_verbatim']==s,'Source row not preserved '+rid)
    require(r['provenance']['source_row_sha256']==digest(canonical(s)),'Source row digest '+rid)
    require(r['language']==lang and r['source_language_code']==src,'Wrong language '+rid)
    require(r['ai_translation']=='unknown','Unproven AI/human provenance '+rid)
    require(r['review']['release_eligible'] is False and r['review']['independent_pro_qc']=='pending','Incorrect release approval '+rid)
    require(r['publication']['translation_version'] is None,'Invented translation version '+rid)
    for key,dest in mapping.items():
     require(at(r,dest)==s[key],'Field mismatch '+rid+' '+key);stats['mapped_fields_compared']+=1
     if isinstance(s[key],str):stats['source_codepoints_compared']+=len(s[key])
    require(bool(r['texts']['translation_verbatim']),'Missing actual translation '+rid)
    require(bool(r['texts']['arabic_verbatim']),'Missing Arabic text '+rid)
    require([x['relation_verbatim'] for x in r['topic_tags']]==rels[source_id],'Topic relations mismatch '+rid)
    for t in r['topic_tags']:
     require(t['category_verbatim']==cats_by_id.get(t['relation_verbatim']['category_id']),'Topic label mismatch '+rid)
     require(t['origin']=='publisher_taxonomy','Topic origin changed '+rid)
    matches=[x for x in ar_by_key.get((s['id'],s['ar_version']),[]) if x['hadeeth']==s['hadeeth_ar']]
    matched=r['arabic_alignment']['matched_arabic_rowid']
    if len(matches)==1:
     a=matches[0];require(matched==a['source_rowid'],'Arabic row binding '+rid);counts['exact_arabic_alignment']+=1
     require(r['arabic_alignment']['matched_arabic_row_sha256']==digest(canonical(a)),'Arabic row hash '+rid)
     for value,source_field in [('source_references.bibliography_verbatim','reference'),('source_references.arabic_attribution_verbatim','attribution'),('grading.arabic_label_verbatim','grade'),('commentary.arabic_explanation_verbatim','explanation'),('commentary.arabic_benefits_raw_json_verbatim','hints'),('commentary.arabic_word_meanings_raw_json_verbatim','words_meanings')]:require(at(r,value)==a[source_field],'Arabic source field mismatch '+rid+' '+value)
     require(''.join(x['text_verbatim'] for x in r['source_references']['citation_lines'])==(a['reference'] or ''),'Reference lines lost '+rid)
    else:
     counts['arabic_alignment_exceptions']+=1
     require(matched is None,'Unverified Arabic binding '+rid)
     require(r['source_references']['bibliography_verbatim'] is None,'Current-version references leaked into mismatch '+rid)
     require(r['grading']['arabic_label_verbatim'] is None,'Current-version grade leaked into mismatch '+rid)
    require(r['provenance']['database_sha256']==inputs[src]['sqlite_sha256'],'Snapshot identity '+rid)
    require(r['texts']['arabic_verbatim'] is not None,'Missing Arabic '+rid)
  require(seen==set(raw),'Source-row coverage incomplete '+src)
  require(len(seen)==c['count'],'Catalog count mismatch '+src)
  language_stats.append({'language':lang,**dict(counts)})
 for rid,(source_id,links) in stored_links.items():require(links==families[source_id]-{rid},'Broken cross-language version links '+rid)
 require(load(root/'PUBLICATION-GATE.json')['allowed'] is False,'Publication gate must remain closed')
 report={'success':not errors,'review_type':'complete_programmatic_source_field_comparison_not_independent_Pro_QC','coverage':dict(stats),'languages':language_stats,'errors':errors,'error_count':len(errors),'independent_pro_qc_performed':False,'human_review_performed':False,'semantic_translation_review_performed':False,'canonical_authenticity_verified':False,'network_required':False}
 (root/'reports/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2));return not errors
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=pathlib.Path,required=True);args=p.parse_args()
 try:sys.exit(0 if validate(args.root.resolve()) else 1)
 except (OSError,ValueError,KeyError,sqlite3.Error) as e:sys.exit('Validation failed: '+str(e))
