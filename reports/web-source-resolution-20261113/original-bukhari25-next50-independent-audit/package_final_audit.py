"""Package only immutable independent evidence after the final native PASS."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def write_exact(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)
report=json.loads((HERE/'independent-final-v2-audit.json').read_bytes())
assert report['result']=='PASS' and report['full477_before_after_native_apply_finish']=='PASS'
assert report['counts']['lossless_source_field_partitions']==2385
names=['complete-independent-source-first-readings.json','independent_source_first_notes.py',
    'independent-source-verification.json','verify_original_sources.py',
    'independent-boundary-findings-v1.json','freeze_findings.py','author-response-receipt.json',
    'independent-final-v2-audit.json','audit_final_candidate.py','package_final_audit.py']
prefix='reports/web-source-resolution-20261113/original-bukhari25-next50-independent-audit'
files=[]
for name in names:
    b=(HERE/name).read_bytes();path=prefix+'/'+name;target=HERE/'publish'/path
    write_exact(target,b)
    files.append({'path':path,'local_path':str(target),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
manifest={'schema':'hadith-bank-frozen-independent-review-delivery-v1','status':'PASS',
    'primary_source_commit':report['source_commit'],'primary_manifest_sha256':report['primary_manifest_sha256'],
    'primary_active_sha256':report['primary_active_sha256'],
    'independent_final_report_sha256':sha((HERE/'independent-final-v2-audit.json').read_bytes()),
    'summary':{'existing_parent_occurrences':25,'complete_independent_fields_read':50,
        'characters_read':27103,'utf8_bytes_read':58879,'newly_admitted_fields':50,
        'whole_ledger_occurrences':477,'whole_ledger_lossless_partitions':2385,
        'prior_other_field_definitions_and_native_outputs_preserved':2335,
        'untouched_parents_preserved':452,'prior_script_corrections_preserved':19,
        'amended_source_mask_fields':6,'metadata_only_refined_fields':1,
        'source_characters_to_context':89,'source_utf8_bytes_to_context':179,
        'remaining_priority_fields_candidate':6311,'remaining_priority_occurrences_candidate':3354,
        'parent_registration_delta':0,'new_source_http_requests':0,'github_writes':0,
        'independent_pro_qc':'not_performed','publication_and_rebuild_status':'not claimed'},
    'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files),
    'source_dependencies':'The primary frozen manifest, original full477 baseline and stored source paths are bound by the included proof. Original raw/parsed bytes, all initial notes and all prior active decisions are unchanged.'}
data=enc(manifest);path=HERE/'delivery-manifest.json';write_exact(path,data)
print(json.dumps({'status':'PASS','manifest':str(path),'manifest_sha256':sha(data),
    'report_sha256':manifest['independent_final_report_sha256'],'files':len(files),'bytes':manifest['total_bytes']}))
