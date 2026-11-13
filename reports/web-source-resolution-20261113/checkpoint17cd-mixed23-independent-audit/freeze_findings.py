"""Freeze the completed46-field independent comparison and bounded six-field plan."""
from pathlib import Path
import copy
import gzip
import hashlib
import json

H=Path(__file__).resolve().parent
P=H.parent/'phase22-checkpoint17cd-abudawud-tirmidhi23-review'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    if p.exists():assert p.read_bytes()==b,p
    else:p.write_bytes(b)
    return sha(b)
def mask(spans):return {i for s in spans for i in range(s['start'],s['end'])}
ownb=(H/'complete-independent-source-first-readings.json').read_bytes()
assert sha(ownb)=='a0e6792db0303627d5702438a90fa129bf8bd2913906e6c13e23a3591cfb3ae5'
own=json.loads(ownb)
assert own['candidate_or_primary_notes_opened'] is False and own['all_complete_fields_read_before_candidate_inspection']
assert (own['complete_fields'],own['characters'],own['utf8_bytes'])==(46,24000,51211)
readings={(r['id'],r['language']):r for r in own['fields']}
for item in own['initial_note_documents']:
    b=(H/item['path']).read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256']
mb=(P/'delivery-manifest-v1.json').read_bytes()
assert sha(mb)=='147636cd951ff1714315f9b83b13362be327059a80d8361485172422f2a43565'
m=json.loads(mb)
for f in m['files']:
    b=Path(f['local_path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
af=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ab=Path(af['local_path']).read_bytes();assert sha(ab)=='9be6b24bbca390f3317bc9b44bf08ebb55f84f3dae9e4e84e931d84607126134'
ledger=json.loads(gzip.decompress(ab));records={r['id']:r for r in ledger['records']}
fields={(r['id'],f['language']):f for r in records.values() for f in r['field_reviews']}
assert len(records)==23 and set(fields)==set(readings) and len(fields)==46
notes=[];covered=[]
for n in range(1,7):
    p=H/f'candidate-inspection-notes-{n:02d}.json';b=p.read_bytes();j=json.loads(b)
    assert j['candidate_manifest_sha256']==sha(mb) and j['own_source_first_receipt_sha256']==sha(ownb)
    covered+=j['actually_inspected_field_indices'];notes.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
assert covered==list(range(46))
peer_path=H.parent/'phase22-tirmidhi2622-independent-scope-adjudication/independent-complete-original-scope-adjudication.json'
peerb=peer_path.read_bytes();assert sha(peerb)=='2b25450fb5622a567d958e594f4525d3ed9de0aa2c80cf27499891717233dda0'
peer=json.loads(peerb)
assert peer['status']=='independent_source_first_scope_adjudication_complete'
assert peer['actual_coverage']=={'fields':2,'characters':636,'utf8_bytes':1354}
for r in peer['complete_original_readings']:
    mine=readings[r['occurrence_id'],r['language']]
    assert r['text']==mine['text'] and r['text_sha256']==mine['sha256']
assert sha(Path(peer['policy']['path']).read_bytes())==peer['policy']['sha256']
put(H/'peer-scope-adjudication-2622.json',peerb)

restores=[
 ('deenhindi-abudawud:2645','hi',482,508,'(यानी इस्लाम और कुफ़्र की)',
  'The parenthetical Islam/kufr words specify the source-rendered referents of both fires. Preserve that material subject/domain qualification within the actual reply, explicitly qualified as this provider rendering rather than independently certified verbatim Prophetic wording.'),
 ('deenhindi-abudawud:2645','ur',435,460,'( یعنی اسلام اور کفر کی )',
  'Preserve the source-rendered Islam/kufr referents of both fires as material reply scope. Keep compiler transmission criticism and note markers as context, and do not claim that this explanatory wording is independently certified verbatim speech.'),
 ('deenhindi-abudawud:2658','hi',128,167,'(यानि शिकस्त खा कर इधर उधर भाग खड़े हुए)',
  'Defeat and fleeing here and there are substantive finite historical circumstances in this source rendering, beyond the damaged scattering word. Preserve that action/sequence qualification while leaving the plural participant unidentified and every printed defect unchanged.'),
 ('deenhindi-abudawud:2658','ur',111,156,'( یعنی شکست کھا کر ادھر ادھر بھاگ کھڑے ہوئے )',
  'The source adds a finite defeat-and-flight circumstance, not only an interchangeable lexical label. Preserve it with a source-rendering qualification, without resolving which group fled from another version or external history.')]
findings=[]
for oid,lang,start,end,text,reason in restores:
    r=readings[oid,lang];f=fields[oid,lang]
    assert r['text'][start:end]==text and not (set(range(start,end))&mask(f['spans']))
    findings.append({'id':oid,'language':lang,'kind':'restore_material_source_rendered_scope','start':start,'end':end,
     'text':text,'sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),
     'source_text_sha256':r['sha256'],'selection_add_ranges':[[start,end]],'selection_remove_ranges':[],
     'reason':reason,'initial_independent_reading_note':r['initial_independent_reading_note']})
for lang,start,end in [('hi',131,303),('ur',120,333)]:
    oid='deenhindi-tirmidhi:2622';r=readings[oid,lang];f=fields[oid,lang];text=r['text'][start:end]
    cuts=[[max(start,s['start']),min(end,s['end'])] for s in f['spans'] if max(start,s['start'])<min(end,s['end'])]
    removed=''.join(r['text'][a:b] for a,b in cuts)
    findings.append({'id':oid,'language':lang,'kind':'retain_appended_compiler_legal_commentary_as_context',
     'start':start,'end':end,'text':text,'sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),
     'source_text_sha256':r['sha256'],'selection_add_ranges':[],'selection_remove_ranges':cuts,
     'selected_characters_to_context':len(removed),'selected_utf8_bytes_to_context':len(removed.encode()),
     'reason':'The main Abdullah ibn Shaqiq report of the Companions\u2019 view stays admitted under its actual voice. The explicit transition to Tirmidhi\u2019s appended heard Abu Musab doctrinal/legal ruling gives local attribution, but its role is compiler legal commentary under the owner\u2019s explicit exclusion. Preserve the complete attributed appendix in context, including every language-specific condition or defect. This is not a rejection based on severity, later speakers, or absence of Prophetic attribution.',
     'peer_adjudication_sha256':sha(peerb),'initial_independent_reading_note':r['initial_independent_reading_note']})
changed={(r['id'],r['language']) for r in findings}
expected={
 ('deenhindi-abudawud:2645','hi'):[(0,532)],
 ('deenhindi-abudawud:2645','ur'):[(0,273),(275,486)],
 ('deenhindi-abudawud:2658','hi'):[(0,234)],
 ('deenhindi-abudawud:2658','ur'):[(0,216)],
 ('deenhindi-tirmidhi:2622','hi'):[(0,131)],
 ('deenhindi-tirmidhi:2622','ur'):[(0,120)]}
plans=[];inspection=[]
for key,r in readings.items():
    oid,lang=key;f=fields[key];spans=copy.deepcopy(f['spans'])
    if key in changed:
        new=[]
        for a,b in expected[key]:
            overlaps=[s for s in spans if max(a,s['start'])<min(b,s['end'])]
            assert overlaps
            signatures=[{k:v for k,v in s.items() if k not in ('start','end','sha256')} for s in overlaps]
            assert all(s==signatures[0] for s in signatures)
            new.append(dict(signatures[0],start=a,end=b,sha256=sha(r['text'][a:b].encode())))
        add={i for x in findings if (x['id'],x['language'])==key for a,b in x['selection_add_ranges'] for i in range(a,b)}
        remove={i for x in findings if (x['id'],x['language'])==key for a,b in x['selection_remove_ranges'] for i in range(a,b)}
        assert mask(new)-mask(spans)==add and mask(spans)-mask(new)==remove
        spans=new
    plans.append({'id':oid,'language':lang,'decision':records[oid]['decision'],'source_text_sha256':r['sha256'],'expected_spans':spans})
    inspection.append({'id':oid,'language':lang,'original_blind_note':r['initial_independent_reading_note'],
       'v1_field':f,'expected_spans':spans,'decision':'bounded_amendment_required' if key in changed else 'accepted_v1_exact'})
assert len(changed)==len(findings)==6 and len({i for i,l in changed})==3
restored_chars=sum(f['characters'] for f in findings if f['selection_add_ranges'])
restored_bytes=sum(f['utf8_bytes'] for f in findings if f['selection_add_ranges'])
removed_chars=sum(f.get('selected_characters_to_context',0) for f in findings)
removed_bytes=sum(f.get('selected_utf8_bytes_to_context',0) for f in findings)
assert restored_chars==135 and removed_chars==333
assert sum(len(p['expected_spans']) for p in plans)==71
plan_sha=put(H/'accepted-reviewed-field-plan.json',enc({'schema':'hadith-bank-independent-accepted-field-plan-v1',
 'primary_v1_manifest_sha256':sha(mb),'independent_source_first_sha256':sha(ownb),'reviewed_fields':plans}))
adjudication={'schema':'hadith-bank-root-source-scope-adjudication-v1','status':'FINAL_SOURCE_CONTEXT_DECISION',
 'id':'deenhindi-tirmidhi:2622','languages':['hi','ur'],'independent_peer_receipt_sha256':sha(peerb),
 'root_complete_originals_read_before_candidate':True,'all46_candidate_fields_inspected':True,
 'root_agrees_with_independent_peer_role_based_decision':True,'main_abdullah_report_remains_admitted':True,
 'appendix_full_own_context_ranges':{'hi':[131,303],'ur':[120,333]},
 'reason':'Explicit hearing establishes the local source of an appended ruling; it does not override the policy that compiler legal commentary stays context. No severity-based censorship, canonical attribution inference, or missing Hindi condition repair is used.',
 'copied_peer_input_row_review_flags_describe_frozen_input_preparation_not_actual_completed_peer_reading':True,
 'initial_blind_notes_and_provisional_candidate_note05_remain_unchanged':True,'additional_cohort_reading_credit':0}
adj_sha=put(H/'root-scope-adjudication-2622.json',enc(adjudication))
result={'schema':'hadith-bank-independent-boundary-findings-v1','primary_v1_manifest_sha256':sha(mb),
 'active_v1_sha256':sha(ab),'independent_source_first_sha256':sha(ownb),'accepted_field_plan_sha256':plan_sha,
 'all46_exact_candidate_fields_inspected_after_complete_original_readings':True,'candidate_inspection_note_receipts':notes,
 'peer_scope_adjudication_sha256':sha(peerb),'root_scope_adjudication_sha256':adj_sha,'findings':findings,
 'accepted_unchanged_fields':40,'changed_fields':6,'changed_parents':3,'restore_ranges':4,
 'restore_characters':restored_chars,'restore_utf8_bytes':restored_bytes,'selected_characters_moved_to_context':removed_chars,
 'selected_utf8_bytes_moved_to_context':removed_bytes,'final_selected_spans':71,'all_inspected_fields':inspection,
 'required_preservation':{'all40_other_read_fields_exact':True,'all69_unread_fields_exact':True,'all20_other_whole_parents_exact':True,
 'all27_v1_payload_files_and_v1_manifest_archived_exact':True,'all_source_bytes_and_metadata_exact':True,
 'surviving_component_identity_and_voice_metadata_exact':True,'only_two_appendix_component_families_removed_from_selection':True,
 'initial_notes_retained_with_transparent_final_refinement':True,'new_reading_credit':0,'new_parent_registration_credit':0,'new_canonical_occurrences':0}}
finding_sha=put(H/'independent-boundary-findings-v1.json',enc(result))
print(json.dumps({'findings_sha256':finding_sha,'plan_sha256':plan_sha,'root_adjudication_sha256':adj_sha,
 'findings':len(findings),'changed_fields':len(changed),'restore_characters':restored_chars,'restore_utf8_bytes':restored_bytes,
 'selected_characters_moved_to_context':removed_chars,'selected_utf8_bytes_moved_to_context':removed_bytes,'final_selected_spans':71},indent=2))
