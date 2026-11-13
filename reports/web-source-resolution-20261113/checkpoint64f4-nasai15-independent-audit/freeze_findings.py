"""Freeze the independently inspected masks and the only two requested cuts."""
from pathlib import Path
import copy,gzip,hashlib,json,datetime
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda d:(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
first=json.loads((R/'complete-independent-source-first-readings.json').read_bytes())
assert sha((R/'complete-independent-source-first-readings.json').read_bytes())=='dbd2b4f8d1aa09eb4bda2075791cf7b317518df385d8bfa8fb416d54b324b801'
ledger=json.loads(gzip.decompress((R/'input/primary-active-v1.json.gz').read_bytes()))
assert sha((R/'input/primary-active-v1.json.gz').read_bytes())=='52e11ef9b376797269f4a09bbc0f31cf0629f9c9236d6b6577185f3e2341dd76'
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(R/'input/cohort.jsonl').read_bytes().splitlines())}
notes={(r['occurrence_id'],r['language']):r for r in first['fields']}
cuts={('deenhindi-nasai:2732','hi'):[(1507,1522)],('deenhindi-nasai:2732','ur'):[(1442,1460)]}
rows=[];findings=[]
for d in ledger['records']:
 for f in d['field_reviews']:
  if not f['reviewed']:continue
  key=(d['id'],f['language']);text=sources[d['id']]['source_record'][f['source_field']]
  assert notes[key]['text']==text and f['text_sha256']==sha(text.encode())
  expected=[]
  for s in f['spans']:
   ranges=[(s['start'],s['end'])]
   for a,b in cuts.get(key,[]):
    update=[]
    for x,y in ranges:
     if b<=x or a>=y:update.append((x,y));continue
     if x<a:update.append((x,a))
     if b<y:update.append((b,y))
    ranges=update
   for a,b in ranges:
    e=copy.deepcopy(s);e.update(start=a,end=b,sha256=sha(text[a:b].encode()));expected.append(e)
  row={'id':d['id'],'language':f['language'],'source_field_sha256':f['text_sha256'],'full_own_field_read':True,'initial_note':notes[key]['independent_note'],'v1_field_sha256':sha(enc(f)),'current_spans':f['spans'],'accepted_spans':expected,'required_source_mask_change':key in cuts,'all_retained_types_speakers_component_ids_and_families_unchanged':True}
  rows.append(row)
  for a,b in cuts.get(key,[]):
   assert all(any(s['start']<=i<s['end'] for s in f['spans']) for i in range(a,b))
   findings.append({'id':d['id'],'language':f['language'],'source_field_sha256':f['text_sha256'],'source_span':[a,b],'text':text[a:b],'text_sha256':sha(text[a:b].encode()),'characters':b-a,'utf8_bytes':len(text[a:b].encode()),'change':'selected_to_complete_context','reason':'This is a calendar-equivalence apposition after the already printed Yawm al-Nahr. Keep the named actual event day and sacrifice; the separate eighth-DhulHijja command-time clause supplies otherwise absent temporal scope and stays selected.'})
assert len(rows)==30 and len(findings)==2
assert sum(f['characters'] for f in findings)==33 and sum(f['utf8_bytes'] for f in findings)==65
plan={'schema':'independent-exact-reviewed-field-plan-v1','primary_manifest_sha256':'f98a9ca4644a15fa2bfedfd2a1c571d84275a7e1f315a2090f3c0f4409e75438','primary_active_sha256':'52e11ef9b376797269f4a09bbc0f31cf0629f9c9236d6b6577185f3e2341dd76','complete_reviewed_fields':30,'fields':rows,'source_mask_changed_fields':2,'selected_characters_removed':33,'selected_utf8_bytes_removed':65,'selected_characters_added':0,'allow_affected_reason_annotation_refinement':True,'unaffected_field_and_parent_metadata_must_remain_exact':True}
plan_raw=enc(plan);p=R/'accepted-reviewed-field-plan-v1.json';assert not p.exists();p.write_bytes(plan_raw)
report={'schema':'independent-source-boundary-findings-v1','status':'COMPLETE_COMPARISON_TWO_NARROW_CALENDAR_CUTS','recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reader':'/root/checkpoint_inventory','source_commit':'64f4ed50ed6026855237a5d547a86dd03e73f804','source_first_receipt_sha256':sha((R/'complete-independent-source-first-readings.json').read_bytes()),'independent_source_proof_sha256':sha((R/'input/own-source-verification.json').read_bytes()),'primary_manifest_sha256':plan['primary_manifest_sha256'],'primary_active_sha256':plan['primary_active_sha256'],'complete_source_fields_read_and_candidate_masks_compared':30,'characters_read':13448,'utf8_bytes_read':28971,'required_findings':findings,'accepted_exact_plan_sha256':sha(plan_raw),'parent_changes':0,'language_admission_changes':0,'source_text_changes':0,'all_other28_read_fields_accepted':True,'refinements_of_preserved_initial_notes':[{'ids':['deenhindi-nasai:2738','deenhindi-nasai:2757'],'language':'hi','refinement':'Initial notes allowed context or explicitly uncompleted source-fragment treatment for the damaged tails. The actual candidate keeps them inside a finite source report with precise missing-predicate/place annotations and a truncated report type where needed. No action, place or subject is filled. That explicit qualified preservation is accepted, without revising the original notes.'},{'ids':['deenhindi-nasai:2732'],'language':'ur','refinement':'The short there parenthesis functions as coherent location framing for the narrated action after the stated place and may remain. The eighth-day command timing remains material scope; only the adjacent tenth-day calendar definition is moved to context.'},{'ids':['deenhindi-nasai:2705'],'language':'hi/ur','refinement':'The source links the two distinct voice components through Muhammad own hearing and later visit. One shared source-report family with distinct Ibn Umar and Aisha components is supported; neither is relabelled as direct Prophet speech.'}],'limits':'This is the final primary-boundary findings set, not a final v2 native/preservation PASS. The initial own-source notes remain immutable. No source-site request, additional-language reading, external identity or GitHub write occurred.'}
p=R/'independent-boundary-findings-v1.json';assert not p.exists();raw=enc(report);p.write_bytes(raw)
print(json.dumps({'findings_sha256':sha(raw),'plan_sha256':sha(plan_raw),'fields':30,'affected_fields':2,'removed_chars':33,'removed_bytes':65}))
