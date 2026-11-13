"""Package only an actually completed final native gate and manual amendment reread."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase23-checkpoint64f4-bukhari30-review'
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def exact(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():assert path.read_bytes()==data
 else:path.write_bytes(data)
rb=(ROOT/'independent-final-v2-audit.json').read_bytes();assert sha(rb)==sys.argv[1]
r=json.loads(rb);assert r['result']=='PASS' and r['native_SourceReviews_apply_finish']=='PASS' and r['open_findings']==[]
mb=(PRIMARY/'delivery-manifest-v2.json').read_bytes();assert sha(mb)==r['primary_manifest_v2_sha256']
manual_b=(ROOT/'author-amendment-and-final-reading-receipt.json').read_bytes();manual=json.loads(manual_b)
assert manual['primary_manifest_v2_sha256']==r['primary_manifest_v2_sha256'] and manual['active_v2_sha256']==r['active_v2_sha256']
assert manual['actual_complete_amended_fields_reread']==8 and manual['actual_final_descriptions_and_attributions_inspected'] is True
assert manual['no_new_reading_credit']==True and manual['open_findings']==[]
names=['complete-independent-source-first-readings.json','independent-source-first-reading-notes.json',
 'source_first_batch01.py','source_first_batch02.py','source_first_batch03.py','source_first_batch04.py','source_first_batch05.py','source_first_batch06.py','source_first_batch07.py',
 'independent-source-verification.json','verify_original_sources.py','independent-boundary-findings-v1.json',
 'accepted-reviewed-field-plan-v1.json','freeze_boundary_findings.py','show_candidate_fields.py','input/root-complete-original-role-adjudication.json',
 'author-amendment-and-final-reading-receipt.json','independent-final-v2-audit.json','audit_final_candidate.py','package_final_audit.py']
prefix='reports/web-source-resolution-20261113/checkpoint64f4-bukhari30-independent-audit'
files=[]
for name in names:
 b=(ROOT/name).read_bytes();path=prefix+'/'+name;target=ROOT/'publish'/path;exact(target,b)
 files.append({'path':path,'local_path':str(target),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
c=r['counts'];metadata=sum(c[k] for k in ('parent_metadata_leaf_equalities','language_metadata_leaf_equalities','source_metadata_leaf_equalities'))
delivery={'schema':'hadith-bank-frozen-independent-review-delivery-v1','status':'PASS','source_commit':r['source_commit'],
 'primary_manifest_v2_sha256':r['primary_manifest_v2_sha256'],'primary_active_v2_sha256':r['active_v2_sha256'],
 'independent_final_report_sha256':sha(rb),'manual_final_amendment_reading_receipt_sha256':sha(manual_b),
 'summary':{'parent_occurrences':30,'registered':30,'source_only':0,'complete_independent_fields_read':66,
 'characters_read':47492,'utf8_bytes_read':100674,'admitted_fields':60,'fully_read_context_only_fields':6,'unread_context_fields':84,
 'lossless_partitions':150,'selected_spans':c['selected_spans'],'typed_source_components':c['typed_source_components'],
 'reviewed_context_parts':c['reviewed_context_gaps'],'metadata_leaf_equalities':metadata,
 'source_files_reopened':60,'complete_raw_reparses':30,'source_characters_restored':0,'source_utf8_bytes_restored':0,
 'removed_characters':1253,'removed_utf8_bytes':2717,'metadata_only_amended_fields':0,'unchanged_other_complete_field_definitions':142,
 'unchanged_other_whole_parents':26,'new_reading_credit_from_amendment':0,'initial_source_first_notes_preserved':True,
 'new_source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed','publication_export_and_live_deployment':'not claimed'},
 'files':files,'total_files':len(files),'total_bytes':sum(x['bytes'] for x in files),
 'source_dependencies':'The complete pinned source baseline, all66 original reading fields and60 saved raw/parsed files are bound by the independent source proof and frozen primary v2. All30 original primaryv1 payloads plus its manifest survive in that final primary package. Root’s four-field original-only2737/2763 role adjudication is separately bound and adds no cohort reading credit. No active ledger, queue, source state or engine was mutated by this audit.'}
target=ROOT/'delivery-manifest.json';exact(target,enc(delivery))
print(json.dumps({'result':'PASS','manifest':str(target),'sha256':sha(target.read_bytes()),'files':len(files),'bytes':delivery['total_bytes'],'report_sha256':sha(rb)},indent=2))
