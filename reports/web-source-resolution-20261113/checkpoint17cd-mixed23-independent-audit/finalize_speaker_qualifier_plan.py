"""Version the accepted plan to correct a superseded boundary-description sentence."""
from pathlib import Path
import copy,hashlib,json
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    if p.exists():assert p.read_bytes()==b,p
    else:p.write_bytes(b)
    return sha(b)
pb=(H/'accepted-reviewed-field-plan.json').read_bytes();fb=(H/'independent-boundary-findings-v1.json').read_bytes()
assert sha(pb)=='f4acef0523c00a8b656a15b87df8800e13554507ce84c1ed9c816601dc8cc218'
assert sha(fb)=='26264137521acb4ff79aa07ea876b2c201ccfffd1c41a615ce59c5e573afe31a'
plan=json.loads(pb);findings=json.loads(fb);old_plan=copy.deepcopy(plan)
old='Jarir reports the Khatham incident, the half-compensation response and the actual question/answer about the two fires. The metaphor’s explicit explanatory alias is kept separately.'
new='Jarir reports the Khatham incident, the half-compensation response and the actual question/answer about the two fires. The source-printed Islam/kufr referents remain qualified scope of this reported reply; no independent claim of verbatim Prophetic wording is made.'
updated=[]
for f in plan['reviewed_fields']:
    if f['id']=='deenhindi-abudawud:2645':
        assert f['language'] in ('hi','ur')
        for s in f['expected_spans']:
            assert s['speaker']==old;s['speaker']=new
        updated.append([f['id'],f['language']])
assert len(updated)==2
for before,after in zip(old_plan['reviewed_fields'],plan['reviewed_fields']):
    if [after['id'],after['language']] not in updated:assert before==after
    else:
        test=copy.deepcopy(after)
        for s in test['expected_spans']:s['speaker']=old
        assert test==before
plan['previous_plan_sha256']=sha(pb)
plan['versioned_qualification_correction']='Only two Abu2645 speaker-description boundary notes change. Jarir remains the actual narrator, and component identity, report type, source family and exact source ranges remain unchanged.'
plan2sha=put(H/'accepted-reviewed-field-plan-v2.json',enc(plan))
findings['previous_v1_findings_sha256']=sha(fb)
findings['accepted_field_plan_sha256']=plan2sha
findings['speaker_description_qualification_corrections']={'fields':updated,'previous_speaker_description':old,'expected_speaker_description':new,
 'actual_speaker_or_report_type_changes':0,'source_range_changes_from_v1_plan':0,
 'reason':'The old wording says the alias is kept separately, describing the superseded context placement. The corrected description agrees with the accepted restoration while preserving the actual narrator and a source-rendering qualification.'}
lookup={(f['id'],f['language']):f for f in plan['reviewed_fields']}
for f in findings['all_inspected_fields']:f['expected_spans']=lookup[f['id'],f['language']]['expected_spans']
preserve=findings['required_preservation']
preserve['surviving_component_identity_and_voice_metadata_exact']=False
preserve['all_actual_speakers_component_ids_report_types_and_source_families_unchanged']=True
preserve['only_two_superseded_boundary_descriptions_corrected_as_specified']=True
find2sha=put(H/'independent-boundary-findings-v2.json',enc(findings))
receipt={'schema':'hadith-bank-independent-versioned-qualification-refinement-v1','old_findings_sha256':sha(fb),'new_findings_sha256':find2sha,
 'old_plan_sha256':sha(pb),'new_plan_sha256':plan2sha,'only_two_speaker_boundary_descriptions_updated':updated,
 'all_six_prior_field_boundaries_and_decisions_unchanged':True,'all46_fields_previously_actually_inspected':True,
 'source_or_primary_payload_mutations':0,'new_reading_credit':0}
receiptsha=put(H/'speaker-qualification-plan-refinement.json',enc(receipt))
print(json.dumps({'findings_v2_sha256':find2sha,'plan_v2_sha256':plan2sha,'refinement_receipt_sha256':receiptsha},indent=2))
