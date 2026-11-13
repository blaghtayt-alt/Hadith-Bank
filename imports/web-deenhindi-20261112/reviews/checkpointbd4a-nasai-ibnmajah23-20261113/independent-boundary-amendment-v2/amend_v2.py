"""Apply only the two independently reviewed equivalent-formula context cuts."""
from pathlib import Path
import copy,gzip,hashlib,importlib.util,json,pprint,subprocess,sys
HERE=Path(__file__).resolve().parent
REL=Path('imports/web-deenhindi-20261112/reviews/checkpointbd4a-nasai-ibnmajah23-20261113')
OUT=HERE/'publish-v2';ARCHIVE=REL/'independent-boundary-amendment-v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,b):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():assert path.read_bytes()==b,path
 else:path.write_bytes(b)
mp=HERE/'delivery-manifest-v1.json';mb=mp.read_bytes();assert sha(mb)=='3c6edbb4854df1e34dcc3f3241c83e19a1d146c73b250ebdcf087b005f2ba056';m=json.loads(mb)
assert not (HERE/'delivery-manifest-v2.json').exists()
for f in m['files']:
 b=Path(f['local_path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes'] and git(b)==f['git_blob_sha1']
af=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
old=json.loads(gzip.decompress(Path(af['local_path']).read_bytes()));before={r['id']:r for r in old['records']}
findp=HERE.parent/'phase18-checkpointbd4a-nasai-ibnmajah23-independent-audit/independent-boundary-findings-v1.json'
fb=findp.read_bytes();assert sha(fb)=='a4190628144c9eef5e1bb98987f03efa05d021bb36f0fba98a055746bdd729f7'
specfile=next(Path(f['local_path']) for f in m['files'] if f['path']==(REL/'manual_rules.py').as_posix())
mod=importlib.util.spec_from_file_location('v1_explicit_rules',specfile);module=importlib.util.module_from_spec(mod);mod.loader.exec_module(module)
rules=copy.deepcopy(module.SPECS)
originals={r['collection']+':'+r['number']:r for r in map(json.loads,(HERE/'input/cohort.jsonl').read_text().splitlines())}
changes=[]
for lang,field,start,end in [('hi','translationHindi',202,269),('ur','translationUrdu',183,246)]:
 text=originals['nasai:2387']['source_record'][field];literal=text[start:end]
 previous=next(f for f in before['deenhindi-nasai:2387']['field_reviews'] if f['language']==lang)
 cut=next(s for s in previous['spans'] if s['start']==start and s['end']==end)
 assert cut['component_id']=='report-2' and text.count(literal)==1
 rules['nasai:2387'].setdefault('exclude_substrings',{})[lang]=[literal]
 refinement=' Final independent refinement: the bounded unnamed-transmitter comparison of two equivalent negative formulas is source apparatus. The actual first negative answer is already supplied separately. Keep this exact comparison in context, without choosing a formula, inventing a closing parenthesis or excluding any resumed dialogue. Existing report-1 and report-3 identities and voices remain unchanged.'
 rules['nasai:2387']['field_notes'][lang]+=refinement
 rules['nasai:2387']['annotations'][lang]+=refinement
 changes.append({'id':'deenhindi-nasai:2387','language':lang,'source_field':field,'source_text_sha256':sha(text.encode()),'start':start,'end':end,'text':literal,'sha256':sha(literal.encode()),'characters':len(literal),'utf8_bytes':len(literal.encode()),'change':'selected equivalent-formula apparatus to lossless source context','removed_component':cut})
assert sum(c['characters'] for c in changes)==130 and sum(c['utf8_bytes'] for c in changes)==276
(HERE/'manual_rules.py').write_text('"""Final v2 rules after the preserved independent equivalent-formula amendment."""\nSPECS = '+pprint.pformat(rules,width=115,sort_dicts=True)+'\n')
subprocess.run([sys.executable,str(HERE/'build_delivery.py'),'--output-dir',str(OUT),'--manifest-file',str(HERE/'native-v2-core-manifest.json')],check=True)
new=json.loads(gzip.decompress((OUT/af['path']).read_bytes()));after={r['id']:r for r in new['records']}
unchanged_fields=0;unchanged_parents=0
for ident,row in before.items():
 now=after[ident]
 if ident!='deenhindi-nasai:2387':assert now==row;unchanged_parents+=1
 else:
  assert {k:v for k,v in now.items() if k!='field_reviews'}=={k:v for k,v in row.items() if k!='field_reviews'}
 for oldf,newf in zip(row['field_reviews'],now['field_reviews']):
  assert oldf['language']==newf['language']
  if ident=='deenhindi-nasai:2387' and oldf['language'] in ['hi','ur']:
   kept=[s for s in oldf['spans'] if s['component_id']!='report-2'];assert newf['spans']==kept
   allowed={'spans','action','reason','source_text_annotations'}
   assert {k:v for k,v in oldf.items() if k not in allowed}=={k:v for k,v in newf.items() if k not in allowed}
   assert oldf['action']=='excerpts' and newf['action']=='excerpts'
  else:assert newf==oldf;unchanged_fields+=1
assert (unchanged_fields,unchanged_parents)==(113,22)
for f in m['files']:put(OUT/ARCHIVE/'previous-v1-payload'/f['path'],Path(f['local_path']).read_bytes())
put(OUT/ARCHIVE/'previous-delivery-manifest-v1.json',mb)
put(OUT/ARCHIVE/'independent-boundary-findings-v1.json',fb)
put(OUT/ARCHIVE/'amend_v2.py',Path(__file__).read_bytes())
receipt={'schema':'hadith-bank-exact-independent-boundary-amendment-v2','status':'PASS','source_commit':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633','previous_manifest_sha256':sha(mb),'previous_active_sha256':af['sha256'],'final_active_sha256':sha((OUT/af['path']).read_bytes()),'independent_findings_sha256':sha(fb),'changes':changes,'selected_characters_moved_to_context':130,'selected_utf8_bytes_moved_to_context':276,'other_field_definitions_exact':113,'whole_other_parents_exact':22,'remaining_span_ids_speakers_types_families_exact':True,'all_parent_dispositions_unchanged':True,'original_source_and_initial_reading_notes_unchanged':True,'v1_payload_files_archived_exact':len(m['files']),'v1_manifest_archived_exact':True,'native_all23_validation':'PASS','native_lossless_partitions':115,'independent_final_v2_audit_pending':True,'github_writes':0}
put(OUT/ARCHIVE/'amendment-receipt.json',enc(receipt))
def binding(p,local=False):
 b=p.read_bytes();f={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'size_bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
 if local:f.update(local_path=str(p),source_path=str(p))
 return f
core=json.loads((HERE/'native-v2-core-manifest.json').read_bytes())
portable=OUT/REL/'package-file-manifest.json'
portable.write_bytes(enc({'schema':'hadith-bank-source-review-package-manifest-v2','source_checkpoint':receipt['source_commit'],'active_ledger':af['path'],'summary':core['summary'],'independent_amendment':receipt,'manifest_excludes_its_own_recursive_hash':True,'files':[binding(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p!=portable]}))
final={'output_root':str(OUT),'summary':core['summary'],'independent_amendment':receipt,'files':[binding(p,True) for p in sorted(OUT.rglob('*')) if p.is_file()]}
put(HERE/'delivery-manifest-v2.json',enc(final))
print(json.dumps({'manifest_sha256':sha(enc(final)),'files':len(final['files']),'bytes':sum(f['bytes'] for f in final['files']),'active_sha256':receipt['final_active_sha256'],'other_fields_exact':113,'whole_other_parents_exact':22,'characters_to_context':130,'utf8_bytes_to_context':276},indent=2))
