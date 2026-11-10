#!/usr/bin/env python3
"""Offline full-text and topic search of HadeethEnc source records (public or private)."""
import argparse,hashlib,json,pathlib,re,sys,unicodedata
WARNING='Public availability does not certify authenticity or translation accuracy.'
CURRENT_REVIEW_NOTICE='Separate bank HadeethEnc review is not required by owner decision. Original records retain historical authorship and review flags, and Arabic-alignment notes remain visible. No independent bank review is claimed.'
def fold(value):return ''.join(c for c in unicodedata.normalize('NFKD',str(value)).casefold() if not unicodedata.combining(c))
def local(root,relative):
 """Resolve one canonical local file without following symlinks or escaping root."""
 if not isinstance(relative,str) or not relative or '\\' in relative or any(ord(c)<32 for c in relative):raise ValueError('Unsafe collection path')
 rel=pathlib.PurePosixPath(relative)
 if rel.is_absolute() or '..' in rel.parts or rel.as_posix()!=relative or any(':' in part for part in rel.parts):raise ValueError('Unsafe collection path')
 path=root
 for part in rel.parts:
  path=path/part
  if path.is_symlink():raise ValueError('Unsafe collection path: '+relative)
 if not path.resolve().is_relative_to(root) or not path.is_file():raise ValueError('Missing/unsafe collection path: '+relative)
 return path
def integrity_spec(root,collection,public):
 """Published registries pin hash, bytes and count; older private manifests pin the hash."""
 path=local(root,collection['records_path'])
 expected_hash=collection.get('records_sha256');expected_bytes=collection.get('bytes')
 expected_count=collection.get('count')
 if expected_hash is None and not public:
  manifest_path=collection.get('manifest_path',str(pathlib.PurePosixPath(collection['records_path']).parent/'manifest.json'))
  manifest=json.loads(local(root,manifest_path).read_text(encoding='utf-8'))
  coverage=manifest.get('coverage',{})
  expected_hash=coverage.get('records_sha256');expected_bytes=coverage.get('bytes',expected_bytes)
 if not isinstance(expected_hash,str) or not re.fullmatch('[0-9a-fA-F]{64}',expected_hash):raise ValueError('Missing/invalid records_sha256: '+collection['records_path'])
 if type(expected_count) is not int or expected_count<0:raise ValueError('Missing/invalid record count: '+collection['records_path'])
 if (public and expected_bytes is None) or (expected_bytes is not None and (type(expected_bytes) is not int or expected_bytes<0)):raise ValueError('Missing/invalid byte count: '+collection['records_path'])
 return path,expected_hash.lower(),expected_bytes,expected_count
def ai_state(value):return 'true' if value is True else 'false' if value is False else 'unknown'
def review_notice(ai_states,qc_states,policy=None):
 """Describe recorded flags; a current waiver does not turn historical QC into a pass."""
 statements=[CURRENT_REVIEW_NOTICE] if policy else []
 if 'unknown' in ai_states:statements.append('Exact-record AI translation origin is unknown for some source records.')
 if 'true' in ai_states:statements.append('Some source records are labeled as AI-translated.')
 if 'false' in ai_states:statements.append('Some source records carry the ai_translation=false label.')
 if qc_states:statements.append(('Historical' if policy else 'Recorded')+' independent Pro QC status: '+', '.join(sorted(qc_states))+'.')
 return ' '.join(statements+[WARNING])
def current_review_policy(root):
 """Read an explicit current waiver without changing historical record metadata."""
 path=root/'catalog/review-policy.json'
 if not path.is_file():return None
 path=local(root,'catalog/review-policy.json')
 policy=json.loads(path.read_text(encoding='utf-8'))
 if not isinstance(policy,dict) or policy.get('schema')!='hadith-bank-review-policy-v1':return None
 hadeethenc=policy.get('hadeethenc')
 if not isinstance(hadeethenc,dict):return None
 if hadeethenc.get('decision')!='owner_waived_separate_bank_review' or hadeethenc.get('separate_bank_review_required') is not False:return None
 return {'policy_path':'catalog/review-policy.json',**hadeethenc}
def search(root,query='',language=None,topic_id=None,entry_id=None,limit=10,commentary=False,approved_only=False):
 root=pathlib.Path(root).resolve();public=(root/'datasets/hadeethenc/collections.json').is_file()
 index_path=local(root,'datasets/hadeethenc/collections.json' if public else 'collections.json')
 if type(limit) is not int or limit<0:raise ValueError('Limit must be a nonnegative integer')
 index=json.loads(index_path.read_text(encoding='utf-8'));results=[];matched=0
 policy=current_review_policy(root);words=[fold(word) for word in query.split()]
 checked=[];ai_states=set();qc_states=set()
 for collection in index['collections']:
  if language and collection['language']!=language:continue
  path,expected_hash,expected_bytes,expected_count=integrity_spec(root,collection,public)
  digest=hashlib.sha256();byte_count=0;record_count=0
  with path.open('rb') as stream:
   for line in stream:
    digest.update(line);byte_count+=len(line)
    if not line.strip():raise ValueError('Blank JSONL line: '+collection['records_path'])
    item=json.loads(line.decode('utf-8'))
    if not isinstance(item,dict):raise ValueError('JSONL record is not an object: '+collection['records_path'])
    record_count+=1
    item_ai=ai_state(item.get('ai_translation'));item_qc=str(item['review'].get('independent_pro_qc','unknown'))
    ai_states.add(item_ai);qc_states.add(item_qc)
    if approved_only and item['review'].get('certified_release_eligible',False) is not True:continue
    if entry_id and entry_id not in [item['source_entry_id'],item['record_id'],item['occurrence_id']]:continue
    if topic_id is not None and not any(t['relation_verbatim']['category_id']==topic_id for t in item['topic_tags']):continue
    if words:
     # Include all record metadata, especially translator, publication, source,
     # IDs and taxonomy. The raw row duplicates commentary, which remains opt-in.
     metadata={k:v for k,v in item.items() if k not in ('title_verbatim','texts','commentary','source_row_verbatim')}
     if policy:metadata['current_review_policy']=policy
     parts=[item['title_verbatim'],item['texts']['arabic_verbatim'],item['texts']['translation_verbatim'],json.dumps(metadata,ensure_ascii=False)]
     if commentary:parts.append(json.dumps(item['commentary'],ensure_ascii=False))
     haystack=fold('\n'.join(x or '' for x in parts))
     if not all(word in haystack for word in words):continue
    matched+=1
    if len(results)<limit:
     result={'record_id':item['record_id'],'language':item['language'],'source_entry_id':item['source_entry_id'],'title':item['title_verbatim'],'arabic':item['texts']['arabic_verbatim'],'translation':item['texts']['translation_verbatim'],'grading':item['grading'],'source_references':item['source_references'],'publisher':item['publication']['publisher'],'translator':item['publication'].get('translator'),'publication':item['publication'],'source_arabic_version':item['publication']['source_arabic_version'],'translation_version':item['publication']['translation_version'],'digital_snapshot_sha256':item['publication']['digital_snapshot_sha256'],'ai_translation':item['ai_translation'],'warning':review_notice({item_ai},{item_qc},policy),'arabic_alignment':item['arabic_alignment']['status'],'release_status':item['review']['release_status'],'independent_pro_qc':item_qc,'certified_release_eligible':item['review'].get('certified_release_eligible',False)}
     if policy:result['current_review_policy']=policy;result['historical_review']=item['review']
     results.append(result)
  # Verify the entire selected collection even after the display limit is met.
  # Results are returned only after every searched collection has passed.
  if digest.hexdigest()!=expected_hash:raise ValueError('SHA-256 mismatch: '+collection['records_path'])
  if expected_bytes is not None and byte_count!=expected_bytes:raise ValueError('Byte count mismatch: '+collection['records_path'])
  if record_count!=expected_count:raise ValueError('Record count mismatch: '+collection['records_path'])
  checked.append({'path':collection['records_path'],'sha256':expected_hash,'bytes':byte_count,'count':record_count,'expected_bytes_verified':expected_bytes is not None})
 output={'matched':matched,'shown':len(results),'warning':review_notice(ai_states,qc_states,policy),'integrity':{'status':'passed','collections':checked},'results':results}
 if policy:output['current_review_policy']=policy
 return output
def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]);parser.add_argument('query',nargs='?',default='');parser.add_argument('--language',choices=['ja','fil','vi','zh-CN','uz','hi']);parser.add_argument('--topic-id',type=int);parser.add_argument('--id');parser.add_argument('--limit',type=int,default=10);parser.add_argument('--include-commentary',action='store_true');parser.add_argument('--approved-only',action='store_true');args=parser.parse_args(argv)
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 print(json.dumps(search(args.root,args.query,args.language,args.topic_id,args.id,max(0,args.limit),args.include_commentary,args.approved_only),ensure_ascii=False,indent=2));return 0
if __name__=='__main__':
 try:sys.exit(main())
 except (OSError,ValueError,KeyError) as error:sys.exit('Search failed: '+str(error))
