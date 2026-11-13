"""Apply independently inspected restorations and two source-voice splits."""
from pathlib import Path
import copy, gzip, hashlib, importlib.util, json, pprint, shutil, subprocess, sys

HERE=Path(__file__).resolve().parent
OLD=HERE/'publish'
OUT=HERE/'publish-v2'
REL=Path('imports/web-deenhindi-20261112/reviews')
EVID=REL/'checkpoint0639-nasai-ibnmajah28-20261113'
ACTIVE=REL/'source-review-checkpoint0639-nasai-ibnmajah28-20261113.json.gz'
AMEND=EVID/'independent-boundary-amendment-v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

old_manifest=(HERE/'delivery-manifest.json').read_bytes()
assert sha(old_manifest)=='16ea5e794e9706cc9053915513c3cfd1841917b94b9d1ce63a03be75bc2859b7'
old_active=(OLD/ACTIVE).read_bytes()
assert sha(old_active)=='3898c6efeb62b5e87b6158365cfbade43cb9a323d57d4b6803bca1799c7ca217'
old_rules=(OLD/EVID/'manual_rules.py').read_bytes()
assert sha(old_rules)=='0604accb6147569b04f8278f2d412a6945036ce729ed096eda1f3734e69f520b'
findings=(HERE.parent/'phase15-checkpoint0639-nasai-ibnmajah28-independent-audit/independent-boundary-findings-v1.json').read_bytes()
assert sha(findings)=='673b42871f3ea8faf14d25f9972de769ece6d9fe8f1705d125b4223952b949e8'
module={};exec(compile(old_rules,'frozen-own-v1-specifications','exec'),module)
specs=copy.deepcopy(module['SPECS'])
changes=[
 ('nasai:2239','hi',125,143,'(जवानी के जोश में)','The supplied youthful-desire circumstance limits the otherwise absolute control statement; retain this meaning-bearing qualifier.'),
 ('nasai:2239','ur',110,130,'( جوانی کے جوش میں )','The supplied youthful-desire circumstance limits the otherwise absolute control statement; retain this meaning-bearing qualifier.'),
 ('nasai:2271','hi',245,261,'(खा कर चले जाना)','This is a finite supplied eat-then-leave invitation predicate, not a dictionary definition; retain it without adding words to another field.'),
 ('nasai:2271','ur',189,208,'( کھا کر چلے جانا )','This is a finite supplied eat-then-leave invitation predicate, not a dictionary definition; retain it without adding words to another field.'),
 ('nasai:2279','hi',232,254,'(खाना में शरीक हो जाओ)','The source supplies the actual join-the-meal imperative. Retain its action while keeping the father and intermediary unnamed.'),
 ('nasai:2279','ur',220,246,'( کھانے میں شریک ہو جاؤ )','The source supplies the actual join-the-meal imperative. Retain its action while keeping the father and intermediary unnamed.'),
 ('nasai:2281','hi',156,168,'(खाना खा लो)','The parenthesis supplies a finite eat-food command within this invitation; retain the source own predicate.'),
 ('nasai:2281','ur',144,160,'( کھانا کھا لو )','The parenthesis supplies a finite eat-food command within this invitation; retain the source own predicate.'),
]
for key,lang,a,b,literal,reason in changes:
 assert literal in specs[key]['exclude_substrings'][lang]
 specs[key]['exclude_substrings'][lang].remove(literal)
 specs[key]['field_notes'][lang]='The whole field was read before the initial candidate. Independent source review corrected the initial boundary interpretation: '+reason+' All other source acts, qualifications and words remain exact. The original source-first note is preserved in the amendment history.'
for lang,marker in [('hi','उन्होंने कहा: मुझसे मेरे एक रिश्तेदार'),('ur','انہوں نے کہا: مجھ سے میرے ایک رشتہ دار')]:
 specs['nasai:2276'].setdefault('components',{})[lang]=[
  {'stop_before':marker,'report_type':'historical_transmission_dialogue','speaker':'Ayyub reporting Abu Qilaba guidance and his own later meeting with the unnamed transmitter'},
  {'start_at':marker,'report_type':'prophetic_dialogue_report','speaker':'The unnamed transmitter relays his source-named relative Anas ibn Malik; the seized-camel and food/fasting exchange remains attributed to that relative'},
 ]
 specs['nasai:2276']['field_notes'][lang]+=' Independent component refinement distinguishes the later Ayyub meeting from the relative reported encounter as two ordered voices in the same report family; no extra identity or character is supplied.'
put(HERE/'manual_rules.py',('"""V2 source-bound specifications; see preserved V1 and amendment receipt."""\nSPECS = '+pprint.pformat(specs,width=120,sort_dicts=False)+'\n').encode())
assert not OUT.exists()
subprocess.run([sys.executable,str(HERE/'build_delivery.py'),'--output-dir',str(OUT),'--manifest-file',str(HERE/'delivery-manifest-v2.json')],check=True,capture_output=True)
new_active=(OUT/ACTIVE).read_bytes()
old=json.loads(gzip.decompress(old_active));new=json.loads(gzip.decompress(new_active))
before={r['id']:r for r in old['records']};after={r['id']:r for r in new['records']}
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(HERE/'input/cohort.jsonl').read_bytes().splitlines())}
expected={('deenhindi-'+k,l):(a,b,t,n) for k,l,a,b,t,n in changes}
split={('deenhindi-nasai:2276',l) for l in ['hi','ur']}
changed=[];same_fields=same_rows=restored_chars=restored_bytes=0
for ident,prior in before.items():
 current=after[ident]
 assert {k:v for k,v in prior.items() if k!='field_reviews'}=={k:v for k,v in current.items() if k!='field_reviews'}
 same_rows+=prior==current
 for f,g in zip(prior['field_reviews'],current['field_reviews']):
  key=(ident,f['language']);text=sources[ident]['source_record'][f['source_field']]
  selected=lambda item:{i for s in item['spans'] for i in range(s['start'],s['end'])}
  added=selected(g)-selected(f);removed=selected(f)-selected(g)
  assert not removed
  if key in expected:
   a,b,literal,note=expected[key];assert text[a:b]==literal and added==set(range(a,b))
   restored_chars+=b-a;restored_bytes+=len(literal.encode())
   changed.append({'id':ident,'language':f['language'],'kind':'restore_source_scope_or_finite_predicate','start':a,'end':b,'text':literal,'reason':note})
  elif key in split:
   assert not added and len(f['spans'])==1 and len(g['spans'])==2
   assert len({s['source_report_family_id'] for s in g['spans']})==1
   changed.append({'id':ident,'language':f['language'],'kind':'split_supplied_event_voices_in_one_family','before_spans':f['spans'],'after_spans':g['spans']})
  else:assert f==g;same_fields+=1
assert (same_fields,same_rows,restored_chars)==(130,23,149)
receipt={'schema':'hadith-bank-source-boundary-restoration-and-voice-amendment-v2','status':'PASS',
 'source_commit':'0639af7fd15786284b4c413fced77e38eec8825a','prior_manifest_sha256':sha(old_manifest),
 'prior_active_sha256':sha(old_active),'final_active_sha256':sha(new_active),'independent_findings_sha256':sha(findings),
 'restored_fields':8,'restored_characters':restored_chars,'restored_utf8_bytes':restored_bytes,
 'additional_two_component_voice_fields':2,'removed_positions':0,'unchanged_field_definitions':same_fields,
 'unchanged_complete_parent_rows':same_rows,'all28_parent_dispositions_and_source_metadata_unchanged':True,
 'all65_original_complete_reading_receipt_bytes_unchanged':True,'new_language_readings':0,
 'all_native140_lossless_partitions':'PASS','field_changes':changed,
 'scope':'Only the eight individually reviewed source qualifiers or finite predicates and the two distinct event-voice partitions change. Original full readings and initial interpretive notes remain immutable historical evidence. No source text, identity, grade or translation is repaired.'}
for name,b in [
 ('previous-active-review.json.gz',old_active),('previous-delivery-manifest.json',old_manifest),
 ('previous-manual_rules.py',old_rules),('independent-boundary-findings-v1.json',findings),
 ('amendment-receipt.json',enc(receipt)),('amend_v2.py',Path(__file__).read_bytes())]:put(OUT/AMEND/name,b)
def describe(p,local=False):
 b=p.read_bytes();d={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'size_bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
 if local:d.update(local_path=str(p),source_path=str(p))
 return d
portable=OUT/EVID/'package-file-manifest.json';o=json.loads(portable.read_bytes())
o['candidate_revision']='v2';o['independent_boundary_amendment']=receipt
o['files']=[describe(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p!=portable];put(portable,enc(o))
m=json.loads((HERE/'delivery-manifest-v2.json').read_bytes());m.update(candidate_revision='v2',independent_boundary_amendment=receipt)
m['files']=[describe(p,True) for p in sorted(OUT.rglob('*')) if p.is_file()]
put(HERE/'delivery-manifest-v2.json',enc(m))
print(json.dumps({'manifest_sha256':sha(enc(m)),'active_sha256':sha(new_active),'files':len(m['files']),'bytes':sum(f['bytes'] for f in m['files']),'restored_characters':restored_chars,'restored_utf8_bytes':restored_bytes,'unchanged_field_definitions':same_fields,'unchanged_parent_rows':same_rows},indent=2))
