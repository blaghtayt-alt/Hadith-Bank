#!/usr/bin/env python3
"""Prove the narrow amendment against v1 and the independent accepted plan."""
import collections, copy, gzip, hashlib, json, pprint, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX='imports/web-deenhindi-20261112/reviews/checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-20261113'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-20261113.json.gz'
OUT=ROOT/'publish-v2';OLD=ROOT/'publish-v1';REV=PREFIX+'/independent-scope-v2'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def write(path,data):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def mask(field):return {i for s in field['spans'] for i in range(s['start'],s['end'])}
def label(field,i):
 s=next(s for s in field['spans'] if s['start']<=i<s['end'])
 return {k:v for k,v in s.items() if k not in ('start','end','sha256')}

def main():
 assert not (ROOT/'delivery-manifest-v2.json').exists()
 old=json.loads(gzip.decompress((OLD/ACTIVE).read_bytes()));new=json.loads(gzip.decompress((OUT/ACTIVE).read_bytes()))
 before={r['id']:r for r in old['records']};after={r['id']:r for r in new['records']};assert before.keys()==after.keys()
 plan=json.loads((OUT/REV/'accepted-reviewed-field-plan.json').read_bytes())
 findings=json.loads((OUT/REV/'independent-boundary-findings-v1.json').read_bytes())
 expected={(f['id'],f['language']):f for f in plan['reviewed_fields']};restorations=collections.defaultdict(set)
 rows={r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_bytes().splitlines())}
 for f in findings['findings']:restorations[(f['id'],f['language'])].update(range(f['start'],f['end']))
 changed=[];unchanged_fields=0;whole_unchanged=0;old_selected_positions=0
 for key,oldrow in before.items():
  newrow=after[key];assert {k:v for k,v in oldrow.items() if k!='field_reviews'}=={k:v for k,v in newrow.items() if k!='field_reviews'}
  if oldrow==newrow:whole_unchanged+=1
  for a,b in zip(oldrow['field_reviews'],newrow['field_reviews'],strict=True):
   k=(key,a['language']);assert k in expected and b['spans']==expected[k]['expected_spans']
   assert a['text_sha256']==b['text_sha256']==expected[k]['source_field_sha256']
   if k in restorations:
    assert {n:v for n,v in a.items() if n not in ('spans','reason')}=={n:v for n,v in b.items() if n not in ('spans','reason')}
    assert mask(a)<=mask(b) and mask(b)-mask(a)==restorations[k]
    for pos in mask(a):assert label(a,pos)==label(b,pos)
    for f in findings['findings']:
     if (f['id'],f['language'])==k:
      for pos in range(f['start'],f['end']):assert label(b,pos)=={n:f[n] for n in ('component_id','report_type','speaker','source_report_family_id')}
    changed.append({'id':key,'language':a['language'],'restored_characters':len(mask(b)-mask(a)),'before_reason':a['reason'],'after_reason':b['reason'],'same_existing_type_speaker_component_family':True})
   else:assert a==b;unchanged_fields+=1
   old_selected_positions+=len(mask(a))
 assert len(changed)==5 and unchanged_fields==50 and whole_unchanged==20
 assert old_selected_positions==29062 and sum(len(v) for v in restorations.values())==96
 assert new['source_ledger_sha256']==old['source_ledger_sha256']
 first=(ROOT/'complete-source-first-readings.json').read_bytes();assert sha(first)=='52b2a84ab340b78e4521fb482e89b989889ece6d0d11c5a87189ea9ba2fdef65'
 assert sha((ROOT/'source_first_notes.py').read_bytes())=='0b2b6a443ce01d3724be31cebbd993024bec6f8e4f3498540d19b53f0b3b9f6c'
 manifest=json.loads((ROOT/'delivery-manifest-v1.json').read_bytes())
 for f in manifest['files']:
  assert (OLD/f['path']).read_bytes()==(OUT/REV/'before-v1/payload'/f['path']).read_bytes()
  assert sha((OLD/f['path']).read_bytes())==f['sha256']
 receipt={'schema':'hadith-bank-source-scope-amendment-v2','result':'PASS','source_checkpoint':new['source_checkpoint'],'prior_manifest_sha256':sha((ROOT/'delivery-manifest-v1.json').read_bytes()),'before_active_sha256':sha((OLD/ACTIVE).read_bytes()),'after_active_sha256':sha((OUT/ACTIVE).read_bytes()),'independent_findings_sha256':sha((OUT/REV/'independent-boundary-findings-v1.json').read_bytes()),'accepted_field_plan_sha256':sha((OUT/REV/'accepted-reviewed-field-plan.json').read_bytes()),'exact_changes':findings['findings'],'changed_field_reasons':changed,'restored_spans':7,'restored_characters':96,'restored_utf8_bytes':192,'removed_selected_characters':0,'all29062_prior_selected_positions_and_types_speakers_components_families_unchanged':True,'unchanged_explicit_field_definitions':50,'unchanged_whole_parents':20,'unread_nonempty_siblings_unchanged':58,'actual_empty_siblings_unchanged':2,'parent_dispositions_unchanged':{'register':20,'source_only':3},'all55_final_fields_match_independent_accepted_plan':True,'prior_payload_files_archived_and_rehashed':21,'initial_source_first_notes_and_receipt_unchanged':True,'new_translation':False,'canonical_identity_fills':0,'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed','final_independent_hash_bound_audit':'pending_parent'}
 write(REV+'/amendment-receipt.json',enc(receipt))
 for name in ('prepare_v2.py','finalize_v2.py','amendment-input-v2.json'):write(REV+'/'+name,(ROOT/name).read_bytes())
 extras={(f['id'].removeprefix('deenhindi-'),f['language'],f['text']):f['reason'] for f in findings['findings']}
 script=(ROOT/'package_review.py').read_text().replace("OUT=ROOT/'publish-v1'","OUT=ROOT/'publish-v2'").replace('delivery-manifest-v1.json','delivery-manifest-v2.json')
 script=script.replace('1ae17b3b034812f8c40789881abd9d0184bbdb57c3c58a3eb09e682116b04fe8',sha((OUT/ACTIVE).read_bytes()))
 script=script.replace("\ndef main():","\nRETAINED.update("+pprint.pformat(extras,sort_dicts=False)+")\n\ndef main():")
 script=script.replace("'retained_narrative_parentheses':12","'retained_narrative_parentheses':19").replace("cuts['literal_omissions']==34","cuts['literal_omissions']==27").replace("'explicit_literal_context_cuts':34","'explicit_literal_context_cuts':27")
 script=script.replace("report={'schema'", "report={'amendment_receipt_path':PREFIX+'/independent-scope-v2/amendment-receipt.json','revision':'v2 after seven independently assessed source-scope restorations; final independent hash-bound audit remains separate','schema'")
 script=script.replace("p.name!='portable-manifest.json'","p.relative_to(OUT).as_posix()!=PREFIX+'/portable-manifest.json'")
 script=script.replace('initial primary decision','parent decision')
 (ROOT/'package_review_v2.py').write_text(script)
 subprocess.run([sys.executable,str(ROOT/'package_review_v2.py')],check=True)

if __name__=='__main__':main()
