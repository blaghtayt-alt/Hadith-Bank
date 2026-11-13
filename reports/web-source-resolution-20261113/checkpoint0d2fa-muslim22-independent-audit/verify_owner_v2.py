#!/usr/bin/env python3
"""Verify only the two accepted participant-identity variant restorations."""
import copy,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OWNER=ROOT.parent/'phase21-checkpoint0d2fa-muslim22-review'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())
def field_map(doc):return {(r['occurrence_id'],f['language']):f for r in doc['records'] for f in r['fields']}
def point_labels(field):
    return {i:{k:s[k] for k in ('component_id','report_type','speaker','source_report_family_id')}
            for s in field['selected_spans'] for i in range(s['start'],s['end'])}
def main():
    binding=read(ROOT/'final-candidate-binding.json')
    before_bytes=(ROOT/'before-owner-v1/delivery-manifest-v1.json').read_bytes()
    assert sha(before_bytes)=='a43ba89def3d84bf83775664d501d4d1bfc7a0ca84cace7c8edd5d97452b37fe'
    before_manifest=json.loads(before_bytes)
    assert (OWNER/'delivery-manifest-v1.json').read_bytes()==before_bytes
    for f in before_manifest['files']:
        b=Path(f['local_path']).read_bytes()
        assert len(b)==f['bytes'] and sha(b)==f['sha256']
    mb=Path(binding['owner_manifest_path']).read_bytes()
    assert sha(mb)==binding['owner_manifest_sha256']
    manifest=json.loads(mb)
    out=OWNER/binding['owner_output_directory']
    blobs={}
    for f in manifest['files']:
        p=out/f['path'];b=p.read_bytes()
        assert p.is_file() and not p.is_symlink() and len(b)==f['bytes'] and sha(b)==f['sha256']
        blobs.setdefault((sha(b),len(b)),[]).append(f['path'])
    assert (sha(before_bytes),len(before_bytes)) in blobs,'Exact v1 manifest must be preserved in the final durable payload'
    for f in before_manifest['files']:assert (f['sha256'],f['bytes']) in blobs,('missing preserved v1 payload',f['path'])
    old_bytes=(ROOT/'before-owner-v1/active-ledger-v1.json.gz').read_bytes()
    assert sha(old_bytes)=='74ce5ef0f8f15c46da1b5b858c5db368a4b62ae8fae1ef931cfb3704ab13b42e'
    new_bytes=(out/manifest['active_ledger_path']).read_bytes()
    assert sha(new_bytes)==manifest['active_ledger_sha256']==binding['active_ledger_sha256']
    old=json.loads(gzip.decompress(old_bytes));new=json.loads(gzip.decompress(new_bytes))
    assert old['source_commit']==new['source_commit']=='0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a'
    old_records={r['occurrence_id']:r for r in old['records']};new_records={r['occurrence_id']:r for r in new['records']}
    assert set(old_records)==set(new_records) and len(old_records)==22
    before=field_map(old);after=field_map(new)
    changes=read(ROOT/'independent-boundary-findings-v1.json')['findings']
    changed={(f['id'],f['language']):f for f in changes}
    assert set(before)==set(after) and len(before)==110
    unchanged_fields=0;proof=[]
    sources={r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_bytes().splitlines())}
    for key,oldf in before.items():
        newf=after[key]
        if key not in changed:
            assert oldf==newf,key;unchanged_fields+=1;continue
        finding=changed[key]
        text=sources[key[0].removeprefix('deenhindi-')]['source_record'][oldf['source_field']]
        assert sha(text.encode())==finding['field_sha256']==oldf['text_sha256']==newf['text_sha256']
        a,b=finding['start'],finding['end'];assert text[a:b]==finding['text']
        oldpoints=point_labels(oldf);newpoints=point_labels(newf)
        assert set(newpoints)-set(oldpoints)==set(range(a,b)) and not(set(oldpoints)-set(newpoints))
        for i,label in oldpoints.items():
            assert {k:v for k,v in label.items() if k!='speaker'}=={k:v for k,v in newpoints[i].items() if k!='speaker'},(key,i)
        added=[s for s in newf['selected_spans'] if s['start']==a and s['end']==b]
        assert len(added)==1
        s=added[0]
        assert s['component_id']==finding['required_component_id'] and s['report_type']==finding['required_report_type'] and s['source_report_family_id']==finding['required_source_report_family_id']
        assert s['sha256']==sha(text[a:b].encode())
        allowed={'selected_spans','reviewed_context_spans','reason','speaker','report_type','boundary_refinement'}
        assert {k:v for k,v in oldf.items() if k not in allowed}=={k:v for k,v in newf.items() if k not in allowed},key
        for span in newf['selected_spans']:assert sha(text[span['start']:span['end']].encode())==span['sha256']
        proof.append({'id':key[0],'language':key[1],'start':a,'end':b,'text':text[a:b],'characters':b-a,'utf8_bytes':len(text[a:b].encode()),'new_component':s,'all_old_selected_positions_and_component_ids_types_families_exact':True})
    assert unchanged_fields==108
    for key,oldr in old_records.items():
        if key=='deenhindi-muslim:2556':assert {k:v for k,v in oldr.items() if k!='fields'}=={k:v for k,v in new_records[key].items() if k!='fields'}
        else:assert oldr==new_records[key]
    result={'result':'PASS','changed_fields':2,'changed_parents':1,'restored_characters':sum(p['characters'] for p in proof),'restored_utf8_bytes':sum(p['utf8_bytes'] for p in proof),'moved_to_context_characters':0,'unchanged_other_field_definitions':108,'unchanged_other_reviewed_fields':45,'unchanged_unread_fields':63,'unchanged_whole_parents':21,'all22_parent_dispositions_exact':True,'all14_v1_payloads_and_exact_manifest_preserved':True,'old_component_ids_types_families_and_selected_positions_exact':True,'two_fields_final_speakers_and_refinement_reasons_separately_read':binding['two_amended_fields_final_metadata_independently_read'],'changes':proof}
    assert result['restored_characters']==169 and result['restored_utf8_bytes']==373 and result['two_fields_final_speakers_and_refinement_reasons_separately_read']
    (ROOT/'final-amendment-comparison.json').write_bytes(enc(result))
    binding['independent_amendment_result']={k:v for k,v in result.items() if k!='changes'}
    (ROOT/'final-candidate-binding.json').write_bytes(enc(binding))
    print(json.dumps({k:v for k,v in result.items() if k!='changes'},indent=2))
if __name__=='__main__':main()
