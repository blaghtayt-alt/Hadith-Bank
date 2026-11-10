#!/usr/bin/env python3
"""Offline full-text and tag search of the private HadeethEnc import."""
import argparse,json,pathlib,sys,unicodedata
WARNING='Translation authorship is unknown. This private candidate has not passed independent Pro QC.'
def fold(value):return ''.join(c for c in unicodedata.normalize('NFKD',str(value)).casefold() if not unicodedata.combining(c))
def search(root,query='',language=None,topic_id=None,entry_id=None,limit=10,commentary=False):
 index=json.loads((root/'collections.json').read_text(encoding='utf-8'));results=[];matched=0
 for collection in index['collections']:
  if language and collection['language']!=language:continue
  path=(root/collection['records_path']).resolve()
  if not path.is_relative_to(root.resolve()):raise ValueError('Unsafe collection path')
  with path.open(encoding='utf-8') as f:
   for line in f:
    item=json.loads(line)
    if entry_id and entry_id not in [item['source_entry_id'],item['record_id'],item['occurrence_id']]:continue
    if topic_id is not None and not any(t['relation_verbatim']['category_id']==topic_id for t in item['topic_tags']):continue
    parts=[item['title_verbatim'],item['texts']['arabic_verbatim'],item['texts']['translation_verbatim'],json.dumps(item['source_references'],ensure_ascii=False)]
    if commentary:parts.append(json.dumps(item['commentary'],ensure_ascii=False))
    text=fold('\n'.join(x or '' for x in parts))
    if not all(fold(word) in text for word in query.split()):continue
    matched+=1
    if len(results)<limit:
     results.append({'record_id':item['record_id'],'language':item['language'],'source_entry_id':item['source_entry_id'],'title':item['title_verbatim'],'arabic':item['texts']['arabic_verbatim'],'translation':item['texts']['translation_verbatim'],'grading':item['grading'],'source_references':item['source_references'],'ai_translation':item['ai_translation'],'warning':WARNING,'arabic_alignment':item['arabic_alignment']['status'],'release_status':item['review']['release_status']})
 return {'matched':matched,'shown':len(results),'warning':WARNING,'results':results}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('query',nargs='?',default='');p.add_argument('--language',choices=['ja','fil','vi','zh-CN','uz','hi']);p.add_argument('--topic-id',type=int);p.add_argument('--id');p.add_argument('--limit',type=int,default=10);p.add_argument('--include-commentary',action='store_true');a=p.parse_args()
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 try:print(json.dumps(search(a.root.resolve(),a.query,a.language,a.topic_id,a.id,max(0,a.limit),a.include_commentary),ensure_ascii=False,indent=2))
 except (OSError,ValueError,KeyError) as e:sys.exit('Search failed: '+str(e))
