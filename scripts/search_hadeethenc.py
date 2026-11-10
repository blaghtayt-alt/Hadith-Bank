#!/usr/bin/env python3
"""Offline full-text and topic search of HadeethEnc source records (public or private)."""
import argparse,json,pathlib,sys,unicodedata
WARNING='Translation authorship is unknown. Independent Pro QC is pending; public availability does not certify authenticity or translation accuracy.'
def fold(value):return ''.join(c for c in unicodedata.normalize('NFKD',str(value)).casefold() if not unicodedata.combining(c))
def search(root,query='',language=None,topic_id=None,entry_id=None,limit=10,commentary=False,approved_only=False):
 root=root.resolve();public=root/'datasets/hadeethenc/collections.json';index_path=public if public.is_file() else root/'collections.json'
 index=json.loads(index_path.read_text(encoding='utf-8'));results=[];matched=0
 for collection in index['collections']:
  if language and collection['language']!=language:continue
  path=(root/collection['records_path']).resolve()
  if not path.is_relative_to(root):raise ValueError('Unsafe collection path')
  with path.open(encoding='utf-8') as stream:
   for line in stream:
    item=json.loads(line)
    if approved_only and not item['review'].get('certified_release_eligible',False):continue
    if entry_id and entry_id not in [item['source_entry_id'],item['record_id'],item['occurrence_id']]:continue
    if topic_id is not None and not any(t['relation_verbatim']['category_id']==topic_id for t in item['topic_tags']):continue
    parts=[item['title_verbatim'],item['texts']['arabic_verbatim'],item['texts']['translation_verbatim'],json.dumps(item['source_references'],ensure_ascii=False)]
    if commentary:parts.append(json.dumps(item['commentary'],ensure_ascii=False))
    haystack=fold('\n'.join(x or '' for x in parts))
    if not all(fold(word) in haystack for word in query.split()):continue
    matched+=1
    if len(results)<limit:
     results.append({'record_id':item['record_id'],'language':item['language'],'source_entry_id':item['source_entry_id'],'title':item['title_verbatim'],'arabic':item['texts']['arabic_verbatim'],'translation':item['texts']['translation_verbatim'],'grading':item['grading'],'source_references':item['source_references'],'publisher':item['publication']['publisher'],'source_arabic_version':item['publication']['source_arabic_version'],'translation_version':item['publication']['translation_version'],'digital_snapshot_sha256':item['publication']['digital_snapshot_sha256'],'ai_translation':item['ai_translation'],'warning':WARNING,'arabic_alignment':item['arabic_alignment']['status'],'release_status':item['review']['release_status']})
 return {'matched':matched,'shown':len(results),'warning':WARNING,'results':results}
def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]);parser.add_argument('query',nargs='?',default='');parser.add_argument('--language',choices=['ja','fil','vi','zh-CN','uz','hi']);parser.add_argument('--topic-id',type=int);parser.add_argument('--id');parser.add_argument('--limit',type=int,default=10);parser.add_argument('--include-commentary',action='store_true');parser.add_argument('--approved-only',action='store_true');args=parser.parse_args(argv)
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 print(json.dumps(search(args.root,args.query,args.language,args.topic_id,args.id,max(0,args.limit),args.include_commentary,args.approved_only),ensure_ascii=False,indent=2));return 0
if __name__=='__main__':
 try:sys.exit(main())
 except (OSError,ValueError,KeyError) as error:sys.exit('Search failed: '+str(error))
