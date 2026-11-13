"""Independent final-byte, accepted-boundary, preservation and native audit."""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
PRIMARY=WORK/'phase22-checkpoint17cd-abudawud-tirmidhi23-review'
PIN='17cd396eb858a29162505d545aad556ac73ce9ce'
EVID=WORK/'phase21-successor-acquisition-monitor/held-evidence'
FIELDS={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())
def local(f):return Path(f.get('local_path',f.get('source_path')))
def leaf(x):
 if isinstance(x,dict):return sum(leaf(v) for v in x.values()) or 1
 if isinstance(x,list):return sum(leaf(v) for v in x) or 1
 return 1
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
def sig(s):return tuple(s.get(k) for k in ['component_id','source_report_family_id','report_type','speaker'])
def mask(spans):return {i for s in spans for i in range(s['start'],s['end'])}
parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--active-sha256',required=True);args=parser.parse_args()
mp=PRIMARY/'delivery-manifest-v2.json';mb=mp.read_bytes();assert sha(mb)==args.manifest_sha256;m=json.loads(mb)
for f in m['files']:
 b=local(f).read_bytes();assert len(b)==f.get('bytes',f.get('size_bytes')) and sha(b)==f['sha256']
 if f.get('git_blob_sha1'):assert git(b)==f['git_blob_sha1']
active=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ap=local(active);ab=ap.read_bytes();assert sha(ab)==args.active_sha256
out_root=Path(str(ap)[:-len(active['path'])]);ledger=json.loads(gzip.decompress(ab))
baseline=(out_root/ledger['source_ledger_path']).read_bytes();assert sha(baseline)==ledger['source_ledger_sha256']
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress(baseline).splitlines())}
decisions={r['id']:r for r in ledger['records']};assert len(sources)==len(decisions)==23 and sources.keys()==decisions.keys()
ownp=ROOT/'complete-independent-source-first-readings.json';ownb=ownp.read_bytes();assert sha(ownb)=='a0e6792db0303627d5702438a90fa129bf8bd2913906e6c13e23a3591cfb3ae5'
own=json.loads(ownb);assert own['candidate_or_primary_notes_opened'] is False and own['all_complete_fields_read_before_candidate_inspection']
assert (own['complete_fields'],own['characters'],own['utf8_bytes'])==(46,24000,51211)
readings={(f['id'],f['language']):f for f in own['fields']}
for note in own['initial_note_documents']:
 b=(ROOT/note['path']).read_bytes();assert len(b)==note['bytes'] and sha(b)==note['sha256']
planp=ROOT/'accepted-reviewed-field-plan-v2.json';assert sha(planp.read_bytes())=='1ec8f955b73bcf791a28153a4e646a4280dc929198bc5716947b209192d76086'
plan={(f['id'],f['language']):f for f in read(planp)['reviewed_fields']};assert plan.keys()==readings.keys()
findingp=ROOT/'independent-boundary-findings-v2.json';assert sha(findingp.read_bytes())=='6cda382a2d116e2f7b193d5a26d1888c6d135a1ebf265606d0211567e55ea5ed'
findings=read(findingp);changed={(f['id'],f['language']) for f in findings['findings']};assert len(changed)==6 and len(findings['findings'])==6
umbrella_path=ROOT/'umbrella-description-refinement.json'
assert sha(umbrella_path.read_bytes())=='d855f266746edcb8c9e2fe15c4461949ac5a443207882f3f2821dc67f003b1b5'
umbrella={(r['id'],r['language']):r for r in read(umbrella_path)['changes']}
assert set(umbrella)=={('deenhindi-tirmidhi:2622','hi'),('deenhindi-tirmidhi:2622','ur')}
proofp=ROOT/'independent-source-verification.json';assert sha(proofp.read_bytes())=='efab5d768587acb7a226293985ec318d4f5a073a386230aeb4d323b17cc40f9f'
for r in read(proofp)['records']:
 for f in r['files']:
  b=(EVID/'sources'/f['path']).read_bytes();assert len(b)==f['stored_bytes'] and sha(b)==f['stored_sha256'] and git(b)==f['git_blob_sha1']
v1mb=(PRIMARY/'delivery-manifest-v1.json').read_bytes();assert sha(v1mb)=='147636cd951ff1714315f9b83b13362be327059a80d8361485172422f2a43565';v1m=json.loads(v1mb)
for f in v1m['files']:
 b=local(f).read_bytes();assert sha(b)==f['sha256'] and len(b)==f.get('bytes',f.get('size_bytes'))
 assert any(g['path']!=f['path'] and g['path'].endswith('/'+f['path']) and g['sha256']==f['sha256'] and g.get('bytes',g.get('size_bytes'))==len(b) for g in m['files']),('v1 archive missing',f['path'])
assert any(f['sha256']==sha(v1mb) for f in m['files'])
v1f=next(f for f in v1m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
v1b=local(v1f).read_bytes();assert sha(v1b)=='9be6b24bbca390f3317bc9b44bf08ebb55f84f3dae9e4e84e931d84607126134'
v1={r['id']:r for r in json.loads(gzip.decompress(v1b))['records']}
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
engine=SourceReviews(out_root,'deenhindi');assert set(engine.decisions)==set(sources)
assert engine.engine_sha256=='cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
counts={'source_slots':0,'nonempty_partitions':0,'exact_empty_slots':0,'metadata_value_equalities':0,'admitted':0,'read_context':0,'unread_context':0,'read_fields':0,'characters':0,'utf8_bytes':0,'spans':0,'unchanged_explicit_fields':0,'unchanged_implicit_nonempty_slots':0,'unchanged_whole_parents':0}
field_reports=[];slot_reports=[]
for ident,saved in sources.items():
 d=decisions[ident];old_d=v1[ident];assert d['decision']==old_d['decision']
 assert d['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
 assert d['source_reference_verbatim']==saved['source_reference_verbatim']
 original=importer.canonical_record(saved);frozen=copy.deepcopy(original);after,disposition=engine.apply(original,saved=saved)
 assert original==frozen and disposition==d['decision']
 for key in ['id','number','narrator','grading','references','source_locator','source','translator','translation_provenance','rights','source_headings']:
  assert after[key]==frozen[key];counts['metadata_value_equalities']+=leaf(frozen[key])
 assert after['review']['independent_pro_qc']=='not_performed' and not after['review']['certified_release_eligible']
 bylang={f['language']:f for f in d['field_reviews']};oldfields={f['language']:f for f in old_d['field_reviews']}
 assert bylang.keys()==oldfields.keys()
 if not any(i==ident for i,l in changed):assert d==old_d;counts['unchanged_whole_parents']+=1
 oldlangs={f['language']:f for f in frozen['language_versions']};newlangs={f['language']:f for f in after['language_versions']}
 assert oldlangs.keys()==newlangs.keys()
 for lang,source_field in FIELDS.items():
  text=saved['source_record'][source_field];counts['source_slots']+=1
  assert isinstance(text,str)
  if not text:
   assert (ident,lang) not in readings and lang not in bylang and lang not in oldlangs
   counts['exact_empty_slots']+=1;slot_reports.append({'id':ident,'language':lang,'source_field':source_field,'source_text_sha256':sha(b''),'status':'exact_empty_not_read'});continue
  old,new=oldlangs[lang],newlangs[lang];assert old['text']==text
  f=bylang.get(lang);was=oldfields.get(lang);read_field=(ident,lang) in readings
  for key in ['id','language','script','references','translation_provenance']:
   assert old[key]==new[key];counts['metadata_value_equalities']+=leaf(old[key])
  assert new['source']['manual_review']['field_reviewed']==read_field
  if (ident,lang) in changed:
   allowed={'spans','reason','source_text_annotations'}
   if ident=='deenhindi-abudawud:2645':
    correction=findings['speaker_description_qualification_corrections']
    assert was['speaker']==correction['previous_speaker_description']
    assert f['speaker']==correction['expected_speaker_description']
    allowed.add('speaker')
   if (ident,lang) in umbrella:
    u=umbrella[ident,lang]
    assert {k:was[k] for k in u['previous']}==u['previous']
    assert {k:f[k] for k in u['expected']}==u['expected']
    allowed|=set(u['expected'])
   assert {k:v for k,v in f.items() if k not in allowed}=={k:v for k,v in was.items() if k not in allowed}
   matching=[x for x in findings['findings'] if (x['id'],x['language'])==(ident,lang)]
   restored={i for x in matching for a,b in x['selection_add_ranges'] for i in range(a,b)}
   removed={i for x in matching for a,b in x['selection_remove_ranges'] for i in range(a,b)}
   assert mask(f['spans'])-mask(was['spans'])==restored and mask(was['spans'])-mask(f['spans'])==removed
   assert f['spans']==plan[ident,lang]['expected_spans']
   if ident=='deenhindi-abudawud:2645':
    correction=findings['speaker_description_qualification_corrections']
    assert all(s['speaker']==correction['previous_speaker_description'] for s in was['spans'])
    assert all(s['speaker']==correction['expected_speaker_description'] for s in f['spans'])
   if ident=='deenhindi-tirmidhi:2622':
    assert len(f['spans'])==1 and f['spans'][0]['component_id']=='successor-community-view-report'
    assert f['spans'][0]==was['spans'][0]
   # The v2 source-rendering qualifications are in the exact field reason.
   # Verify that the native output retains them; an optional annotation key
   # is not required when the persisted boundary/classification note carries it.
   assert f['reason']!=was['reason']
   assert new['source']['manual_review']['reason']==f['reason']
   assert all(component['reason']==f['reason'] for component in new['source']['report_component_classifications'])
   for before_span in was['spans']:
    for after_span in f['spans']:
     if max(before_span['start'],after_span['start'])<min(before_span['end'],after_span['end']):
      assert sig(before_span)[:3]==sig(after_span)[:3]
      if ident!='deenhindi-abudawud:2645':assert sig(before_span)==sig(after_span)
  if (ident,lang) not in changed:
   assert f==was
   if f is None:counts['unchanged_implicit_nonempty_slots']+=1
   else:counts['unchanged_explicit_fields']+=1
  if read_field:
   r=readings[ident,lang];e=plan[ident,lang]
   assert f and f['reviewed'] and r['complete_field_read'] and r['text']==text and r['sha256']==sha(text.encode())
   assert f['text_sha256']==sha(text.encode()) and f['chars_reviewed']==len(text) and f['bytes_reviewed']==len(text.encode())
   assert d['decision']==e['decision'] and f['spans']==e['expected_spans'],(ident,lang)
   assert {sig(s) for s in f['spans']}=={sig(s) for s in e['expected_spans']}
   counts['read_fields']+=1;counts['characters']+=len(text);counts['utf8_bytes']+=len(text.encode())
  else:assert f is None
  spans=new['source'].get('text_spans',{}).get('quotation_spans',[])
  assert spans==([[s['start'],s['end']] for s in f['spans']] if f else [])
  assert (new['text'] or '')==''.join(text[a:b] for a,b in spans)
  if f:
   for s in f['spans']:assert s['sha256']==sha(text[s['start']:s['end']].encode())
  parts=[(a,b,text[a:b]) for a,b in spans];gaps=[]
  for c in new['comments']:
   a,b=c['source_span'];assert c['scope']=='source_context_not_narration' and c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode())
   parts.append((a,b,c['text']));gaps.append({'start':a,'end':b,'text':c['text'],'sha256':c['source_text_sha256']})
  cursor=0
  for a,b,value in sorted(parts):assert a==cursor and a<b<=len(text) and value==text[a:b];cursor=b
  assert cursor==len(text) and ''.join(value for a,b,value in sorted(parts))==text
  counts['nonempty_partitions']+=1;counts['spans']+=len(spans)
  status='admitted' if spans else 'read_context' if read_field else 'unread_context';counts[status]+=1
  slot_reports.append({'id':ident,'language':lang,'source_field':source_field,'source_text_sha256':sha(text.encode()),'status':status,'exact_partition':True})
  if read_field:field_reports.append({'id':ident,'language':lang,'complete_source_first_reading':True,'source_sha256':sha(text.encode()),'selected_spans':f['spans'],'context_gaps':gaps,'original_blind_note':readings[ident,lang]['initial_independent_reading_note'],'expected_plan':plan[ident,lang]})
engine.finish()
assert (counts['source_slots'],counts['nonempty_partitions'],counts['exact_empty_slots'])==(115,115,0)
assert (counts['read_fields'],counts['characters'],counts['utf8_bytes'])==(46,24000,51211)
assert (counts['admitted'],counts['read_context'],counts['unread_context'])==(46,0,69)
assert (counts['unchanged_explicit_fields'],counts['unchanged_implicit_nonempty_slots'],counts['unchanged_whole_parents'])==(40,69,20)
assert sum(f['characters'] for f in findings['findings'] if f['selection_add_ranges'])==135
assert sum(f['utf8_bytes'] for f in findings['findings'] if f['selection_add_ranges'])==283
assert sum(f.get('selected_characters_to_context',0) for f in findings['findings'])==333
assert sum(f.get('selected_utf8_bytes_to_context',0) for f in findings['findings'])==697
assert counts['spans']==71
assert sum(d['decision']=='register' for d in decisions.values())==23
only={i for i,d in decisions.items() if d['decision']=='exclude'};assert only==set(own['source_only_proposed_after_all_five_own_fields'])
for i in only:assert len([r for r in readings if r[0]==i])==5
report={'schema':'hadith-bank-independent-final-source-review-audit-v1','status':'PASS','source_commit':PIN,'primary_manifest_sha256':sha(mb),'active_ledger_sha256':sha(ab),'independent_source_first_sha256':sha(ownb),'source_proof_sha256':sha(proofp.read_bytes()),'findings_sha256':sha(findingp.read_bytes()),'accepted_field_plan_sha256':sha(planp.read_bytes()),'occurrences':23,'registered':23,'source_only':0,'source_only_ids':sorted(only),'counts':counts,'source_files_independently_reopened_and_hashed':46,'exact_raw_reparses_in_source_first_proof':23,'native_apply_finish':'PASS','all_six_independent_boundary_findings_resolved':True,'source_context_characters_restored_to_selection':135,'source_context_utf8_bytes_restored_to_selection':283,'selected_characters_moved_to_compiler_context':333,'selected_utf8_bytes_moved_to_compiler_context':697,'open_findings':[],'all_source_metadata_unchanged':True,'complete27_file_v1_payload_and_manifest_archived_exact':True,'initial_notes_and_refinements_preserved':True,'two_source_boundary_descriptions_corrected_without_actual_voice_change':True,'independent_peer2622_context_adjudication_bound':True,'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes':0,'live_deployment_claimed':False,'all_source_slots':slot_reports,'fields':field_reports}
out=ROOT/'publish';rel=Path('reports/web-source-resolution-20261113/checkpoint17cd-mixed23-independent-audit')
payload={'final-audit.json':enc(report),'complete-independent-source-first-readings.json':ownb,'independent-source-verification.json':proofp.read_bytes(),'independent-boundary-findings-v2.json':findingp.read_bytes(),'accepted-reviewed-field-plan-v2.json':planp.read_bytes(),'freeze_source_first.py':(ROOT/'freeze_source_first.py').read_bytes(),'freeze_findings.py':(ROOT/'freeze_findings.py').read_bytes(),'audit_final.py':Path(__file__).read_bytes()}
for name in ['independent-boundary-findings-v1.json','accepted-reviewed-field-plan.json','peer-scope-adjudication-2622.json','root-scope-adjudication-2622.json','speaker-qualification-plan-refinement.json','finalize_speaker_qualifier_plan.py','inspect_candidate.py','umbrella-description-refinement.json']:
 payload[name]=(ROOT/name).read_bytes()
assert sha(payload['peer-scope-adjudication-2622.json'])=='2b25450fb5622a567d958e594f4525d3ed9de0aa2c80cf27499891717233dda0'
assert sha(payload['root-scope-adjudication-2622.json'])=='3901df834a53dd4e40b55101ebd59318813526d8ad3c81ad0896a0f10195e5bd'
assert sha(payload['speaker-qualification-plan-refinement.json'])=='0df1cbaf75bb7e0229387b0975475802e52f62364216d9b1080c6e3fb8f3969d'
assert sha(payload['umbrella-description-refinement.json'])=='d855f266746edcb8c9e2fe15c4461949ac5a443207882f3f2821dc67f003b1b5'
for batch in range(1,7):
 payload[f'candidate-inspection-notes-{batch:02d}.json']=(ROOT/f'candidate-inspection-notes-{batch:02d}.json').read_bytes()
 payload[f'source-first-notes-{batch:02d}.json']=(ROOT/f'source-first-notes-{batch:02d}.json').read_bytes()
files=[]
for name,b in payload.items():
 p=out/rel/name;put(p,b);files.append({'path':p.relative_to(out).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
delivery={'schema':'hadith-bank-independent-final-audit-delivery-v1','status':'PASS','source_commit':PIN,'primary_manifest_sha256':sha(mb),'files':files};put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(delivery)),'files':len(files),'bytes':sum(f['bytes'] for f in files),'report_sha256':sha(enc(report)),**counts},indent=2))
