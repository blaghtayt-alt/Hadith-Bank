#!/usr/bin/env python3
"""Bind the owner v2 only after exact agreement with the independently frozen plan."""
from pathlib import Path
import collections,copy,gzip,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parent;OWNER=ROOT.parent/'phase19-checkpoint3e574-muslim20-review'
sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
KEYS=('start','end','sha256','component_id','report_type','speaker','source_report_family_id')
def normalized(spans):return [{k:s[k] for k in KEYS} for s in spans]
def mask(spans):return {i for s in spans for i in range(s['start'],s['end'])}
def main():
 assert len(sys.argv)==4 and not (ROOT/'delivery-manifest.json').exists()
 manifest_name,manifest_hash,active_hash=sys.argv[1:];mbytes=(OWNER/manifest_name).read_bytes();assert sha(mbytes)==manifest_hash;manifest=json.loads(mbytes);OUT=OWNER/'publish-v2'
 oldmb=(OWNER/'delivery-manifest-v1.json').read_bytes();assert sha(oldmb)=='5850b223457d7b89dc0e0e5b7e354af176924c524240bf6d713ab70cac54fc81';oldm=json.loads(oldmb)
 for f in manifest['files']:
  b=(OUT/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
 oldraw=(OWNER/'publish-v1'/oldm['active_ledger_path']).read_bytes();assert sha(oldraw)=='0bbd74ad3c3b0cfe05813936739886ff8f464dd6a7aa0e16f2c49667d66843dc'
 raw=(OUT/manifest['active_ledger_path']).read_bytes();assert sha(raw)==active_hash==manifest['active_ledger_sha256']
 before=json.loads(gzip.decompress(oldraw));after=json.loads(gzip.decompress(raw));oldrows={r['occurrence_id']:r for r in before['records']};newrows={r['occurrence_id']:r for r in after['records']};assert oldrows.keys()==newrows.keys()
 pb=(ROOT/'accepted-reviewed-field-plan-v1.2.json').read_bytes();assert sha(pb)=='aca4cf394178bfd09c430a800b3557065fe2d858f1af0a60909b9f5249098139';plan=json.loads(pb);expected={(f['id'],f['language']):f for f in plan['fields']}
 findings=json.loads((ROOT/'independent-boundary-findings-v1.json').read_bytes());assert sha((ROOT/'independent-boundary-findings-v1.json').read_bytes())=='b68399b2a2db3370112bf270eccc454b52d4e2f020be31d4889d6640b8062bd8'
 changed={(f['id'],f['language']) for f in findings['findings']};counts=collections.Counter();changes=[]
 rows={r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_bytes().splitlines())}
 for rid,oldrow in oldrows.items():
  newrow=newrows[rid];assert {k:v for k,v in oldrow.items() if k!='fields'}=={k:v for k,v in newrow.items() if k!='fields'}
  if oldrow==newrow:counts['unchanged_whole_parents']+=1
  for old,new in zip(oldrow['fields'],newrow['fields'],strict=True):
   key=(rid,old['language']);assert new['language']==old['language']
   if key not in changed:
    assert old==new;counts['unchanged_reviewed_fields' if old['reviewed'] else 'unchanged_unread_fields']+=1
   else:
    assert old!=new
    allowed={'decision','reason','speaker','selected_spans','reviewed_context_spans','explicit_context_cuts','retained_meaningful_structures','boundary_refinement'}
    assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in new.items() if k not in allowed}
    text=rows[rid.removeprefix('deenhindi-')]['source_record'][old['source_field']];removed=mask(old['selected_spans'])-mask(new['selected_spans']);added=mask(new['selected_spans'])-mask(old['selected_spans'])
    assert old['decision']==('whole' if len(old['selected_spans'])==1 and mask(old['selected_spans'])==set(range(len(text))) else 'excerpts')
    assert new['decision']==('whole' if len(new['selected_spans'])==1 and mask(new['selected_spans'])==set(range(len(text))) else 'excerpts')
    refinement=new['boundary_refinement'];assert set(refinement)=={'version','final_source_bound_judgment','independent_findings_sha256','initial_full_reading_note_preserved'}
    assert refinement['version']=='v2' and refinement['initial_full_reading_note_preserved'] is True and refinement['independent_findings_sha256']=='b68399b2a2db3370112bf270eccc454b52d4e2f020be31d4889d6640b8062bd8'
    counts['removed_characters']+=len(removed);counts['removed_utf8_bytes']+=sum(len(text[i].encode()) for i in removed);counts['restored_characters']+=len(added);counts['restored_utf8_bytes']+=sum(len(text[i].encode()) for i in added);counts['changed_fields']+=1
    changes.append({'id':rid,'language':new['language'],'removed_characters':len(removed),'restored_characters':len(added),'before_reason':old['reason'],'after_reason':new['reason'],'before_field_speaker':old['speaker'],'after_field_speaker':new['speaker']})
   if new['reviewed']:assert normalized(new['selected_spans'])==expected[key]['approved_spans'] and new['text_sha256']==expected[key]['text_sha256']
 assert dict(counts)=={'unchanged_whole_parents':11,'unchanged_reviewed_fields':40,'unchanged_unread_fields':42,'removed_characters':712,'removed_utf8_bytes':1491,'restored_characters':31,'restored_utf8_bytes':52,'changed_fields':18},dict(counts)
 assert before['source_ledger_sha256']==after['source_ledger_sha256'] and before['source_ledger_uncompressed_sha256']==after['source_ledger_uncompressed_sha256']
 archive=[]
 for f in oldm['files']:
  b=(OWNER/'publish-v1'/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
  matches=[x for x in manifest['files'] if x['path']!=f['path'] and x['sha256']==f['sha256'] and x['bytes']==f['bytes']];assert matches,('no exact archived prior payload',f['path']);archive.append({'before_path':f['path'],'archived_path':matches[0]['path'],'sha256':f['sha256']})
 assert any(x['sha256']==sha(oldmb) and x['bytes']==len(oldmb) for x in manifest['files'])
 assert sha((OWNER/'complete-source-first-readings.json').read_bytes())=='dc0c5d01715f1e1784af223fd588e90ccc05f4f8b920ab6700882ec824c61ba0'
 comparison={'result':'PASS','before_manifest_sha256':sha(oldmb),'after_manifest_sha256':sha(mbytes),'before_active_sha256':sha(oldraw),'after_active_sha256':sha(raw),'accepted_final_field_plan_sha256':sha(pb),'counts':dict(counts),'exact_changes':findings['findings'],'metadata_consistency_supplements':[json.loads((ROOT/name).read_bytes()) for name in ('source-scope-description-supplement.json','prefatory-route-description-supplement.json')],'changed_field_note_refinements':changes,'parent_dispositions_unchanged':True,'all58_final_boundaries_and_attribution_labels_match_independent_plan':True,'all14_before_payloads_and_manifest_archived_and_rehashed':True,'archived_payload_bindings':archive,'owner_original_first_reading_receipt_unchanged':True,'all_actual_source_bytes_empty_fields_and_unknown_identities_unchanged':True}
 binding={'owner_manifest_path':str(OWNER/manifest_name),'owner_manifest_sha256':sha(mbytes),'owner_output_directory':'publish-v2','active_ledger_sha256':sha(raw),'all58_complete_original_fields_and_candidate_boundaries_independently_read':True,'owner_accepted_all_requested_changes':True,'approved_admitted_fields':33,'independent_amendment_result':comparison}
 plan['open_findings']=[];plan['exact_final_v2_amendment_verified']=True
 (ROOT/'final-candidate-binding.json').write_bytes(enc(binding));(ROOT/'final-field-boundary-assessment.json').write_bytes(enc(plan));(ROOT/'changed-field-final-notes.json').write_bytes(enc(changes))
 print(json.dumps({'comparison':'PASS','counts':dict(counts),'final_changed_field_notes_path':str(ROOT/'changed-field-final-notes.json'),'next':'Independently inspect the explicit changed reasons, then run audit_final_candidate.py.'},indent=2))
if __name__=='__main__':main()
