"""Independent source-first, exact-boundary and native verification of final21."""
from pathlib import Path
import copy,gzip,hashlib,json,sys
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
PRIMARY=WORK/'phase15-checkpoint0639-abudawud-tirmidhi21-review'
PIN='0639af7fd15786284b4c413fced77e38eec8825a'
EVID=WORK/'phase13-successor-acquisition-monitor/held-evidence'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

manifest_path=PRIMARY/'delivery-manifest-v2.json';manifest_raw=manifest_path.read_bytes()
assert sha(manifest_raw)=='cfa965d100052e481a10c36c2534b799088293e05ff95154ecb6f699765eb77f'
m=json.loads(manifest_raw)
for item in m['files']:
 b=Path(item.get('local_path',item.get('source_path'))).read_bytes()
 assert len(b)==item.get('bytes',item.get('size_bytes')) and sha(b)==item['sha256']
 if item.get('git_blob_sha1'):assert git(b)==item['git_blob_sha1']
active_item=next(f for f in m['files'] if Path(f.get('path',f.get('repository_path'))).name.startswith('source-review-'))
active_path=Path(active_item.get('local_path',active_item.get('source_path')))
active_bytes=active_path.read_bytes();assert sha(active_bytes)=='b4735dc63110fd87e92205140a305fee5164f26eafe8b09bddcbca7643a13e34'
out_root=PRIMARY/'publish-v2'
ledger=json.loads(gzip.decompress(active_bytes))
input_bytes=(PRIMARY/'input/held-source-records.jsonl').read_bytes()
assert sha(input_bytes)=='07b2088e9e69091fe5d6a40f14d372b4a93727ac3a5ef573eb933b3eb5b48f1b'
sources={'deenhindi-'+x['collection']+':'+x['number']:x for x in map(json.loads,input_bytes.splitlines())}
baseline=(out_root/ledger['source_ledger_path']).read_bytes()
assert sha(baseline)==ledger['source_ledger_sha256']
assert {'deenhindi-'+x['collection']+':'+x['number']:x for x in map(json.loads,gzip.decompress(baseline).splitlines())}==sources
decisions={r['id']:r for r in ledger['records']}
assert len(sources)==len(decisions)==21 and sources.keys()==decisions.keys()
own_raw=(HERE/'independent-complete-source-first-readings.json').read_bytes()
assert sha(own_raw)=='0f0a882140bbf9e5d6f9552a51b699f4d72864399fd65975d7ea80912dc36729'
own=json.loads(own_raw);assert own['candidate_inspected_before_this_freeze'] is False
assert (own['complete_fields'],own['characters'],own['utf8_bytes'])==(42,30305,63236)
readings={(f['id'],f['language']):f for f in own['fields']}
proof_raw=(HERE/'independent-source-verification.json').read_bytes()
assert sha(proof_raw)==own['independent_source_verification_sha256']=='b47538af55a81b0a8dd398bdf4cf5dd1c92988469d0c20f56c9f4573047d0f16'
source_proof=json.loads(proof_raw);assert source_proof['source_commit']==PIN
previous=read(WORK/'phase13-acquisition-monitor/saved-checkpoint/state.json')
assert len(previous['imported'])==15215
assert not {x.removeprefix('deenhindi-') for x in sources}.intersection(previous['imported'])
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
engine=SourceReviews(out_root,'deenhindi');assert engine.decisions.keys()==sources.keys()
partitions=parent_checks=language_checks=selected_fields=spans_total=read_chars=read_bytes=0
field_reports=[]
for ident,saved in sources.items():
 d=decisions[ident]
 assert d['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
 assert d['source_reference_verbatim']==saved['source_reference_verbatim']
 before=importer.canonical_record(saved);frozen=copy.deepcopy(before)
 after,action=engine.apply(before,saved=saved);assert before==frozen and action==d['decision']=='register'
 for k in ['id','number','narrator','grading','references','source_locator','source','translator','translation_provenance','rights','source_headings']:
  assert after[k]==frozen[k];parent_checks+=1
 assert after['review']['independent_pro_qc']=='not_performed' and after['review']['certified_release_eligible'] is False
 bylang={f['language']:f for f in d['field_reviews']};assert set(bylang)=={'hi','ur'}
 assert len(frozen['language_versions'])==len(after['language_versions'])==5
 for old,new in zip(frozen['language_versions'],after['language_versions']):
  text=old['text'];lang=old['language'];f=bylang.get(lang)
  for k in ['id','language','script','references','translation_provenance']:
   assert old[k]==new[k];language_checks+=1
  assert new['source']['manual_review']['field_reviewed']==bool(f)
  if f:
   r=readings[(ident,lang)];assert r['text']==text and r['text_sha256']==sha(text.encode()) and r['complete_field_read']
   assert f['reviewed'] and f['text_sha256']==sha(text.encode())
   assert f['chars_reviewed']==len(text) and f['bytes_reviewed']==len(text.encode())
   read_chars+=len(text);read_bytes+=len(text.encode())
  spans=new['source'].get('text_spans',{}).get('quotation_spans',[])
  assert (new['text'] or '')==''.join(text[a:b] for a,b in spans)
  if f:assert spans==[[s['start'],s['end']] for s in f['spans']] and spans
  else:assert not spans and (new['text'] or '')==''
  pieces=[(a,b,text[a:b]) for a,b in spans];gaps=[]
  for c in new['comments']:
   a,b=c['source_span'];assert c['scope']=='source_context_not_narration' and c['text']==text[a:b]
   assert c['source_text_sha256']==sha(text[a:b].encode())
   pieces.append((a,b,c['text']));gaps.append({'start':a,'end':b,'text':c['text'],'sha256':c['source_text_sha256']})
  cursor=0
  for a,b,t in sorted(pieces):assert a==cursor and a<b<=len(text) and t==text[a:b];cursor=b
  assert cursor==len(text) and ''.join(x[2] for x in sorted(pieces))==text
  partitions+=1;selected_fields+=bool(spans);spans_total+=len(spans)
  if f:field_reports.append({'id':ident,'language':lang,'source_text_sha256':sha(text.encode()),
   'characters':len(text),'utf8_bytes':len(text.encode()),'complete_source_first_reading':True,
   'every_selected_boundary_context_gap_and_voice_independently_inspected':True,
   'selected_spans':f['spans'],'context_gaps':gaps,'own_source_first_note':readings[(ident,lang)]['independent_source_first_note']})
engine.finish()
assert (partitions,selected_fields,len(field_reports),spans_total,read_chars,read_bytes)==(105,42,42,85,30305,63236)

# Verify the exact amendment independently of the primary receipt.
v1_manifest_raw=(PRIMARY/'delivery-manifest.json').read_bytes()
assert sha(v1_manifest_raw)=='cb1f293fc0d21c128a3cf18ba7b432e6630cebb92a81f47db27b91b5de693166'
v1active=PRIMARY/'publish'/active_item['path'];v1raw=v1active.read_bytes()
assert sha(v1raw)=='b03ba173957857ac7acf9b0eaa4375151f4320fa212cda765a7d10a1036f4410'
v1={r['id']:r for r in json.loads(gzip.decompress(v1raw))['records']}
expected={('deenhindi-abudawud:2233','hi'):(260,271,'(बारीरा को)'),
 ('deenhindi-abudawud:2233','ur'):(223,235,'( بریرہ کو )'),
 ('deenhindi-abudawud:2253','ur'):(993,1000,' آخر تک')}
changes=[];unchanged=removed_chars=removed_bytes=0
for ident,d in decisions.items():
 previous_d=v1[ident]
 assert {k:v for k,v in d.items() if k!='field_reviews'}=={k:v for k,v in previous_d.items() if k!='field_reviews'}
 for old,new in zip(previous_d['field_reviews'],d['field_reviews']):
  key=(ident,old['language']);text=sources[ident]['source_record'][old['source_field']]
  mask=lambda f:{i for s in f['spans'] for i in range(s['start'],s['end'])}
  assert not mask(new)-mask(old)
  if key in expected:
   a,b,t=expected[key];assert text[a:b]==t and mask(old)-mask(new)==set(range(a,b))
   signatures=lambda f:{(s['component_id'],s['report_type'],s['speaker'],s['source_report_family_id']) for s in f['spans']}
   assert signatures(old)==signatures(new)
   removed_chars+=b-a;removed_bytes+=len(t.encode());changes.append({'id':ident,'language':key[1],'start':a,'end':b,'text':t})
  else:assert old==new;unchanged+=1
assert (unchanged,removed_chars,removed_bytes)==(39,30,58)
findings={'schema':'hadith-bank-independent-boundary-findings-resolution-v1',
 'initial_candidate_manifest_sha256':sha(v1_manifest_raw),'final_candidate_manifest_sha256':sha(manifest_raw),
 'source_first_receipt_sha256':sha(own_raw),'status':'ALL_RESOLVED','findings':changes,
 'reason':'The two Barira parentheses repeat the already named object. The Urdu2253 continuation pointer refers to unprinted verse text and is context; its now-isolated preceding space is also context. Actual emancipation/counterfactual conditions, recitation/rendering and revelation narrative remain.',
 'exact_extra_spacing':{'id':'deenhindi-abudawud:2253','language':'ur','start':993,'end':994,'text':' ','reason':'Only the isolated source space between two adjacent apparatus gaps; no report word was removed.'},
 'all_other39_explicit_fields_exact':True,'all63_unread_sibling_slots_unchanged':True,
 'new_positions_admitted':0,'parent_dispositions_source_metadata_component_types_speakers_and_families_unchanged':True}
report={'schema':'hadith-bank-checkpoint0639-abudawud-tirmidhi21-independent-final-audit-v1',
 'status':'PASS','source_commit':PIN,'primary_manifest_sha256':sha(manifest_raw),'active_ledger_sha256':sha(active_bytes),
 'own_source_first_reading_sha256':sha(own_raw),'independent_source_proof_sha256':sha(proof_raw),
 'occurrences':21,'registered':21,'resolved_source_only':0,'complete_fields_read':42,
 'characters_read':read_chars,'utf8_bytes_read':read_bytes,'admitted_fields':42,'unread_fields_context':63,
 'source_files_independently_reopened':42,'exact_html_reparses':21,'native_apply_finish':'PASS',
 'full_lossless_field_partitions':partitions,'parent_metadata_equalities':parent_checks,
 'language_metadata_equalities':language_checks,'selected_spans':spans_total,
 'source_ids_absent_from_prior15215':True,'independent_boundary_amendment':findings,
 'open_findings':[],'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes':0,
 'scope':'Every original Hindi and Urdu field was independently read in full before candidate inspection. Other languages remain unread context. No source claim, identity, defect, numbering or authenticity grade was repaired or invented.',
 'fields':field_reports}
OUT=HERE/'publish';rel=Path('reports/web-source-resolution-20261113/checkpoint0639-abudawud-tirmidhi21-independent-audit')
files=[]
for name,b in [('final-audit.json',enc(report)),('independent-complete-source-first-readings.json',own_raw),
 ('independent-source-verification.json',proof_raw),('independent-findings-resolution.json',enc(findings)),
 ('source_first.py',(HERE/'source_first.py').read_bytes()),('audit_final.py',Path(__file__).read_bytes())]:
 p=OUT/rel/name;put(p,b);files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
delivery={'schema':'hadith-bank-independent-final-audit-delivery-v1','status':'PASS','files':files}
put(HERE/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(delivery)),'files':len(files),'bytes':sum(f['bytes'] for f in files),
 'records':21,'read_fields':42,'lossless_partitions':partitions,'selected_spans':spans_total,'exact_characters_moved_to_context':removed_chars},indent=2))
