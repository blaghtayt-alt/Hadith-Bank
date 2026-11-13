"""Freeze the independent review after the actual final native/source gate."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase21-checkpoint0d2fa-bukhari30-review'
sha=lambda value:hashlib.sha256(value).hexdigest()
git=lambda value:hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def write_exact(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)

report_bytes=(ROOT/'independent-final-v2-audit.json').read_bytes()
assert sha(report_bytes)=='c654b041aa7e5fc3bca37d177d265a49ac6449fae5246b526ce3f5c208e6e60d'
report=json.loads(report_bytes)
assert report['result']=='PASS' and report['native_SourceReviews_apply_finish']=='PASS'
manifest_bytes=(PRIMARY/'delivery-manifest-v2.json').read_bytes()
assert sha(manifest_bytes)==report['primary_manifest_v2_sha256']=='a47efe44c8336f382a7587090ceb8c6d5d07bef545ce13181cf5f36761e3fc2e'
manifest=json.loads(manifest_bytes)
active_path='imports/web-deenhindi-20261112/reviews/source-review-checkpoint0d2fa-bukhari30-20261113.json.gz'
item=next(x for x in manifest['files'] if x['path']==active_path)
data=Path(item['local_path']).read_bytes();assert sha(data)==report['active_v2_sha256']
ledger=json.loads(gzip.decompress(data))
parent=next(x for x in ledger['records'] if x['id']=='deenhindi-bukhari:2597')
fields=[f for f in parent['field_reviews'] if f['language'] in ('hi','ur')]
amendment_receipt={
    'schema':'hadith-bank-independent-final-amendment-reading-receipt-v1',
    'source_commit':report['source_commit'],'primary_manifest_v2_sha256':sha(manifest_bytes),
    'active_v2_sha256':sha(data),'findings_sha256':report['complete_boundary_findings_sha256'],
    'author_accepted_source_based_refinement':'The preceding claimed-personal-gift/public-property contrast makes the zakah-property phrase the domain of the ensuing unlawful-taking statement. Restore exactly the two proposed source ranges; the explicit yani-treasury gloss remains context.',
    'final_two_complete_source_fields_and_actual_v2_masks_reread':True,
    'final_field_and_parent_descriptions_inspected':True,
    'final_description_assessment':'Both descriptions now accurately distinguish the selected property-domain qualification from the contextual treasury gloss. They explicitly preserve the initial broader-context judgment as historical evidence rather than presenting it as the final boundary. No actor, source word, report type or family changes.',
    'parent_final_reason':parent['reason'],
    'fields':[{'language':f['language'],'complete_field_definition_sha256':sha(enc(f)),
        'final_reason':f['reason'],'selected_ranges':[[s['start'],s['end']] for s in f['spans']]} for f in fields],
    'unchanged_other_fields':148,'unchanged_other_whole_parents':29,
    'native_final_report_sha256':sha(report_bytes),'open_findings':[],
    'candidate_mutations':0,'github_writes':0,'source_http_requests':0,
}
write_exact(ROOT/'author-amendment-and-final-reading-receipt.json',enc(amendment_receipt))
names=[
    'complete-independent-source-first-readings.json','independent_source_first_notes.py',
    'independent-source-verification.json','verify_original_sources.py',
    'independent-boundary-findings-v1.json','freeze_candidate_findings.py',
    'author-amendment-and-final-reading-receipt.json','independent-final-v2-audit.json',
    'audit_final_candidate.py','show_candidate_fields.py','package_final_audit.py',
]
prefix='reports/web-source-resolution-20261113/checkpoint0d2fa-bukhari30-independent-audit'
files=[]
for name in names:
    value=(ROOT/name).read_bytes();path=prefix+'/'+name;target=ROOT/'publish'/path
    write_exact(target,value)
    files.append({'path':path,'local_path':str(target),'bytes':len(value),'sha256':sha(value),'git_blob_sha1':git(value)})
delivery={
    'schema':'hadith-bank-frozen-independent-review-delivery-v1','status':'PASS',
    'source_commit':report['source_commit'],
    'primary_manifest_v2_sha256':report['primary_manifest_v2_sha256'],
    'primary_active_v2_sha256':report['active_v2_sha256'],
    'independent_final_report_sha256':sha(report_bytes),
    'summary':{
        'parent_occurrences':30,'registered':30,'source_only':0,
        'complete_independent_fields_read':63,'characters_read':37985,'utf8_bytes_read':81545,
        'admitted_fields':60,'fully_read_context_only_fields':3,'unread_context_fields':87,
        'lossless_partitions':150,'selected_spans':122,'typed_source_components':98,
        'reviewed_context_parts_including_three_whole_fields':92,
        'metadata_leaf_equalities':6900,'source_files_reopened':60,'complete_raw_reparses':30,
        'source_characters_restored':26,'source_utf8_bytes_restored':52,'removed_characters':0,
        'unchanged_other_complete_field_definitions':148,'unchanged_other_whole_parents':29,
        'new_reading_credit_from_amendment':0,'initial_source_first_notes_preserved':True,
        '2603_arabic_english_only_primary_hindi_null':True,
        'new_source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed',
        'publication_export_and_live_deployment':'not claimed'},
    'files':files,'total_files':len(files),'total_bytes':sum(x['bytes'] for x in files),
    'source_dependencies':'The exact pinned source baseline, full field inputs and all60 saved raw/parsed files are bound by the included independent source proof and frozen primary v2. All28 original v1 payloads plus its manifest survive in that final primary package. No prior active ledger, queue, source state or engine was modified.',
}
target=ROOT/'delivery-manifest.json';write_exact(target,enc(delivery))
print(json.dumps({'result':'PASS','manifest':str(target),'sha256':sha(target.read_bytes()),
    'files':len(files),'bytes':delivery['total_bytes'],'report_sha256':sha(report_bytes)},indent=2))
