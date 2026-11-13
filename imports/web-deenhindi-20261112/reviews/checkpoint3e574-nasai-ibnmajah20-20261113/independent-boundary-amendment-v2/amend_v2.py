"""Apply the exact independently identified interpretation and report-type refinements."""
from pathlib import Path
import copy,gzip,hashlib,importlib.util,json,pprint,subprocess,sys
HERE=Path(__file__).resolve().parent
REL=Path('imports/web-deenhindi-20261112/reviews/checkpoint3e574-nasai-ibnmajah20-20261113')
OUT=HERE/'publish-v2';ARCHIVE=REL/'independent-boundary-amendment-v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
mp=HERE/'delivery-manifest-v1.json';mb=mp.read_bytes()
assert sha(mb)=='fda319d9c0c9a2bf0b6f7a98cdb32e5ae1bce7684a89fe4b7fcfc98e4cdb856a'
m=json.loads(mb);assert not (HERE/'delivery-manifest-v2.json').exists()
for f in m['files']:
 b=Path(f['local_path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes'] and git(b)==f['git_blob_sha1']
af=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
before={r['id']:r for r in json.loads(gzip.decompress(Path(af['local_path']).read_bytes()))['records']}
findp=HERE.parent/'phase19-checkpoint3e574-nasai-ibnmajah20-independent-audit/independent-boundary-findings-v1.json'
fb=findp.read_bytes();assert sha(fb)=='7e3fd736813bc75a70909a72de203bd9a233f2756a7225d0b33919ef20e315ae'
specfile=next(Path(f['local_path']) for f in m['files'] if f['path']==(REL/'manual_rules.py').as_posix())
spec=importlib.util.spec_from_file_location('immutable_v1_rules',specfile);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rules=copy.deepcopy(module.SPECS)
sources={r['collection']+':'+r['number']:r for r in map(json.loads,(HERE/'input/cohort.jsonl').read_text().splitlines())}
rule=rules['nasai:2492'];starts=rule.pop('start_at')
rule['component_identity_overrides']={'report-1':'attributed-exegesis','report-2':'report-1'}
rule['report_type']='attributed_interpretation_and_separate_prophetic_prohibition'
rule['speaker']='Ibn Shihab transmits the source-named Abu Umama interpretation, followed by the separately attributed Prophetic prohibition'
rule['exclude_substrings']={'ur':['( البقرہ: ۲۶۷ )']}
rule['components']={}
changes=[]
for lang,field,end in [('hi','translationHindi',276),('ur','translationUrdu',257)]:
 text=sources['nasai:2492']['source_record'][field];assert text.index(starts[lang])==end
 speaker=("Ibn Shihab relays the interpretation explicitly supplied by the Hindi source-named अबू उम्मा बिन सहल बिन हुनैफ़. The quoted verse and rendering are the subject of that interpretation, with no recitation event inferred."
          if lang=='hi' else "Ibn Shihab relays the interpretation explicitly supplied by the Urdu source-named ابوامامہ بن سہیل بن حنیف. The quoted verse and rendering are the subject of that interpretation, with no recitation event inferred.")
 rule['components'][lang]=[
  {'stop_before':starts[lang],'report_type':'attributed_exegetical_statement','speaker':speaker},
  {'start_at':starts[lang],'report_type':'actual_prophetic_prohibition','speaker':'The source separately attributes the actually supplied prohibition of taking bad property in zakat to the Prophet; the preceding interpreter statement is not Prophetic speech.'}]
 refinement='Final source-based refinement after independent review: the opening is an explicitly transmitted interpretation identifying the verse\'s referent, not a dictionary synonym. Preserve it under the source-named interpreter\'s own voice, with the quoted verse/rendering as its stated subject. No recitation event or external biographical identity is inferred. Keep the separately attributed actual Prophetic prohibition in its original report-1 component and original family; its former lexical-apparatus type/description is corrected transparently. Only the Urdu verse locator remains context.'
 rule['annotations'][lang]=refinement
 rule['field_notes'][lang]='The immutable initial reading and v1 classification remain archived. '+refinement
 selected=[(0,end)] if lang=='hi' else [(0,170),(185,end)]
 if lang=='ur':assert text[170:185]=='( البقرہ: ۲۶۷ )'
 changes.append({'id':'deenhindi-nasai:2492','language':lang,'change':'restore actual attributed interpretation as separate component; correct former lexical-apparatus metadata on unchanged prohibition text','restored_spans':[{'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode())} for a,b in selected], 'original_prohibition_start':end,'original_prohibition_end':len(text),'original_prohibition_component_id_retained':'report-1','source_text_sha256':sha(text.encode()),'refinement':refinement})
rules['nasai:2540']['report_type']='reported_speech_and_prophetic_statement'
for lang in ['hi','ur']:
 changes.append({'id':'deenhindi-nasai:2540','language':lang,'change':'narrow unsupported witnessed type to reported speech','before_report_type':'witnessed_speech_and_prophetic_statement','after_report_type':'reported_speech_and_prophetic_statement','all_spans_speakers_families_and_other_field_values_unchanged':True})
(HERE/'manual_rules.py').write_text('"""Final v2 rules; initial source-first reading and v1 classifications remain archived."""\nSPECS = '+pprint.pformat(rules,width=115,sort_dicts=True)+'\n')
subprocess.run([sys.executable,str(HERE/'build_delivery.py'),'--output-dir',str(OUT),'--manifest-file',str(HERE/'native-v2-core-manifest.json')],check=True)
after={r['id']:r for r in json.loads(gzip.decompress((OUT/af['path']).read_bytes()))['records']}
unchanged_fields=unchanged_parents=0
for ident,old in before.items():
 new=after[ident]
 assert {k:v for k,v in old.items() if k!='field_reviews'}=={k:v for k,v in new.items() if k!='field_reviews'}
 if ident not in ['deenhindi-nasai:2492','deenhindi-nasai:2540']:assert old==new;unchanged_parents+=1
 for of,nf in zip(old['field_reviews'],new['field_reviews']):
  assert of['language']==nf['language'];lang=of['language']
  if ident=='deenhindi-nasai:2492' and lang in ['hi','ur']:
   assert {k:v for k,v in of.items() if k not in ['spans','reason','source_text_annotations','action']}=={k:v for k,v in nf.items() if k not in ['spans','reason','source_text_annotations','action']}
   prior=of['spans'];kept=[s for s in nf['spans'] if s['component_id']=='report-1'];assert len(prior)==len(kept)==1
   assert {k:v for k,v in prior[0].items() if k not in ['report_type','speaker']}=={k:v for k,v in kept[0].items() if k not in ['report_type','speaker']}
   expected=[(0,276)] if lang=='hi' else [(0,170),(185,257)]
   restored=[s for s in nf['spans'] if s['component_id']=='attributed-exegesis']
   assert [(s['start'],s['end']) for s in restored]==expected
   assert all(s['report_type']=='attributed_exegetical_statement' and s['source_report_family_id']==prior[0]['source_report_family_id'] for s in restored)
  elif ident=='deenhindi-nasai:2540' and lang in ['hi','ur']:
   expected=copy.deepcopy(of)
   for s in expected['spans']:s['report_type']='reported_speech_and_prophetic_statement'
   assert nf==expected
  else:assert of==nf;unchanged_fields+=1
assert (unchanged_fields,unchanged_parents)==(94,18)
for f in m['files']:put(OUT/ARCHIVE/'previous-v1-payload'/f['path'],Path(f['local_path']).read_bytes())
put(OUT/ARCHIVE/'previous-delivery-manifest-v1.json',mb)
put(OUT/ARCHIVE/'independent-boundary-findings-v1.json',fb)
put(OUT/ARCHIVE/'amend_v2.py',Path(__file__).read_bytes())
restored=[s for c in changes for s in c.get('restored_spans',[])]
receipt={'schema':'hadith-bank-exact-independent-boundary-amendment-v2','status':'PASS','source_commit':'3e574b9e7e4dd7cf8bc23232249004a18692c61c','previous_manifest_sha256':sha(mb),'previous_active_sha256':af['sha256'],'final_active_sha256':sha((OUT/af['path']).read_bytes()),'independent_findings_sha256':sha(fb),'changes':changes,'restored_characters':sum(len(s['text']) for s in restored),'restored_utf8_bytes':sum(len(s['text'].encode()) for s in restored),'other_field_definitions_exact':94,'whole_other_parents_exact':18,'all_parent_dispositions_unchanged':True,'original_source_and_initial_reading_notes_unchanged':True,'v1_payload_files_archived_exact':len(m['files']),'v1_manifest_archived_exact':True,'native_all20_validation':'PASS','native_lossless_partitions':98,'exact_empty_source_slots':2,'independent_final_v2_audit_pending':True,'github_writes':0}
put(OUT/ARCHIVE/'amendment-receipt.json',enc(receipt))
def binding(p,local=False):
 b=p.read_bytes();f={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'size_bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
 if local:f.update(local_path=str(p),source_path=str(p))
 return f
core=json.loads((HERE/'native-v2-core-manifest.json').read_bytes());portable=OUT/REL/'package-file-manifest.json'
portable.write_bytes(enc({'schema':'hadith-bank-source-review-package-manifest-v2','source_checkpoint':receipt['source_commit'],'active_ledger':af['path'],'summary':core['summary'],'independent_amendment':receipt,'manifest_excludes_its_own_recursive_hash':True,'files':[binding(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p!=portable]}))
final={'output_root':str(OUT),'summary':core['summary'],'independent_amendment':receipt,'files':[binding(p,True) for p in sorted(OUT.rglob('*')) if p.is_file()]}
put(HERE/'delivery-manifest-v2.json',enc(final))
print(json.dumps({'manifest_sha256':sha(enc(final)),'files':len(final['files']),'bytes':sum(f['bytes'] for f in final['files']),'active_sha256':receipt['final_active_sha256'],'other_fields_exact':94,'whole_other_parents_exact':18,'restored_characters':receipt['restored_characters'],'restored_utf8_bytes':receipt['restored_utf8_bytes']},indent=2))
