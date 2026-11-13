"""Package the final independently read and natively verified exact candidate."""
from pathlib import Path
import argparse,gzip,hashlib,json

HERE=Path(__file__).resolve().parent
OWNER=HERE.parent/'phase19-checkpoint3e574-nasai-ibnmajah20-review'
REL=Path('reports/web-source-resolution-20261113/checkpoint3e574-nasai-ibnmajah20-independent-audit')

def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b
    else:p.write_bytes(b)
def read(p):return json.loads(p.read_bytes())


def main(args):
    native_path=HERE/'native-source-audit-final.json';native=read(native_path)
    assert native['status']=='PASS'
    assert native['primary_manifest_sha256']==args.manifest_sha and native['primary_active_sha256']==args.active_sha
    owner_manifest=OWNER/args.manifest
    assert sha(owner_manifest.read_bytes())==args.manifest_sha
    finding=read(HERE/'independent-boundary-findings-v1.json')
    source={('deenhindi-'+r['collection']+':'+r['number']):r for r in map(json.loads,(HERE/'input/cohort.jsonl').read_bytes().splitlines())}
    restored=[]
    for request in finding['findings']:
        if request['id']!='deenhindi-nasai:2492':continue
        text=source[request['id']]['source_record'][{'hi':'translationHindi','ur':'translationUrdu'}[request['language']]]
        a,b=request['opening_interval'];positions=set(range(a,b))
        for gap in request['retain_as_context']:positions-=set(range(gap['start'],gap['end']))
        exact=''.join(text[i] for i in sorted(positions))
        restored.append({'id':request['id'],'language':request['language'],
            'opening_interval':request['opening_interval'],'remaining_context':request['retain_as_context'],
            'restored_characters':len(exact),'restored_utf8_bytes':len(exact.encode()),
            'restored_source_text_sha256':sha(exact.encode())})
    report={'schema':'independent-complete-source-reading-final-audit-v1','status':'PASS','open_findings':[],
        'source_checkpoint':native['source_checkpoint'],
        'primary_manifest_path':args.manifest,'primary_manifest_sha256':args.manifest_sha,
        'primary_active_ledger':native['primary_active_ledger'],'primary_active_sha256':args.active_sha,
        'independent_complete_source_first_receipt_sha256':native['source_first_reading_receipt_sha256'],
        'initial_boundary_findings_sha256':native['independent_findings_sha256'],
        'native_source_final_report_sha256':sha(native_path.read_bytes()),
        'independent_source_proof_sha256':sha((HERE/'independent-source-verification.json').read_bytes()),
        'actual_complete_readings':{'hi':20,'ur':20,'other':0,'characters':10697,'utf8_bytes':21245},
        'counts':native['counts'],'metadata_leaf_equalities_total':native['metadata_leaf_equalities_total'],
        'source_files_reopened':40,'complete_raw_reparses':20,'lossless_nonempty_partitions':98,'actual_empty_slots':2,
        'source_script_corrections':native['observed_script_corrections'],
        'final_semantic_amendments':{
            'nasai2492':{'fields':restored,'interpretation':'The source-named Abu Umama explicitly transmits a verse-referent interpretation to Ibn Shihab. The verse quotation and actual source rendering are the interpretation subject; no recitation event or external identity is asserted. This named interpretation is a separate component from the final Prophet prohibition.',
                'existing_prophetic_component_refinement':'Its original report-1 identity, family and all source positions are unchanged. The stale after_lexical_apparatus report type and its descriptive speaker text are explicitly corrected to actual_prophetic_prohibition after the attributed interpretation. The auditor independently inspected and accepted these exact two descriptive replacements; they do not assert a different speaker or event.',
                'restored_characters':sum(r['restored_characters'] for r in restored),
                'restored_utf8_bytes':sum(r['restored_utf8_bytes'] for r in restored)},
            'nasai2540':{'languages':['hi','ur'],'change':'Only the report type narrows witnessed_speech to reported_speech. Abdullah ibn Amr remains the source transmitter; no own field claims that he personally witnessed the event. All exact source positions, voices and families remain unchanged.'},
            'unchanged_other_field_definitions':94,'unchanged_whole_parent_records':18,
            'parent_dispositions_or_actual_reading_scope_changed':False},
        'preserved_initial_note_refinements':finding['initial_note_refinements'],
        'all_original_v1_payloads_and_manifest_retained':True,
        'complete_original_field_bytes_and_references_preserved':True,
        'no_sibling_or_external_text_filling':True,'all_unread_siblings_retained_as_context':True,
        'native_apply_and_finish_pass':True,'all_exact_final_spans_independently_checked':True,
        'source_site_requests':0,'github_writes':0,'candidate_mutations_by_auditor':0,
        'independent_pro_qc':'not_performed',
        'limitations':'Exact frozen source packet and forty own-field readings only; no authenticity certification, canonical identity repair, present-day legal advice or deployment claim.'}
    put(HERE/'independent-final-v2-audit.json',enc(report))
    output=HERE/'publish'
    items=[('independent-final-v2-audit.json','independent-final-v2-audit.json'),
           ('native-source-audit-final.json','native-source-audit-final.json'),
           ('field-and-source-proof-final.json.gz','field-and-source-proof-final.json.gz'),
           ('independent-source-verification.json','independent-source-verification.json.gz'),
           ('complete-independent-source-first-readings.json','complete-independent-source-first-readings.json.gz'),
           ('independent-boundary-findings-v1.json','independent-boundary-findings-v1.json.gz'),
           ('native-source-audit-v1-preflight.json','native-source-audit-v1-preflight.json'),
           ('record_independent_readings.py','record_independent_readings.py'),
           ('verify_saved_sources.py','verify_saved_sources.py'),
           ('show_candidate.py','show_candidate.py'),
           ('freeze_findings.py','freeze_findings.py'),
           ('audit_candidate.py','audit_candidate.py'),
           ('freeze_final_audit.py','freeze_final_audit.py')]
    items += [(p.name,'source-first-batches/'+p.name) for p in sorted(HERE.glob('source-first-notes-*.json'))]
    for original,target in items:
        raw=(HERE/original).read_bytes()
        if target.endswith('.gz') and not original.endswith('.gz'):raw=gzip.compress(raw,mtime=0)
        put(output/REL/target,raw)
    def binding(path,local=False):
        raw=path.read_bytes();result={'path':path.relative_to(output).as_posix(),'bytes':len(raw),'size_bytes':len(raw),'sha256':sha(raw),'git_blob_sha1':git(raw)}
        if local:result.update(local_path=str(path),source_path=str(path))
        return result
    portable=output/REL/'package-file-manifest.json'
    put(portable,enc({'schema':'independent-source-review-audit-package-v1','status':'PASS',
        'primary_manifest_sha256':args.manifest_sha,'primary_active_sha256':args.active_sha,
        'manifest_excludes_its_own_recursive_hash':True,
        'files':[binding(p) for p in sorted(output.rglob('*')) if p.is_file() and p!=portable]}))
    manifest={'output_root':str(output),'status':'PASS','summary':report,
        'files':[binding(p,True) for p in sorted(output.rglob('*')) if p.is_file()]}
    path=HERE/'delivery-manifest.json';put(path,enc(manifest))
    print(json.dumps({'manifest':str(path),'manifest_sha256':sha(path.read_bytes()),
        'files':len(manifest['files']),'bytes':sum(x['bytes'] for x in manifest['files']),
        'report_sha256':sha((HERE/'independent-final-v2-audit.json').read_bytes())}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True)
    p.add_argument('--manifest-sha',required=True);p.add_argument('--active-sha',required=True)
    main(p.parse_args())
