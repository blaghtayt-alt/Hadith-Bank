"""Compose frozen phase16 delivery with later checkpoint receipts and a versioned status overlay."""
from pathlib import Path
import hashlib,json,re,shutil
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent;OUT=ROOT/'publish'
REPORT=Path('reports/web-source-resolution-20261113')
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def binding(p):
    b=p.read_bytes();return {'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def put(relative,b):
    relative=Path(relative);assert not relative.is_absolute() and '..' not in relative.parts
    p=OUT/relative;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,p
    else:p.write_bytes(b)
    return p
packages=[
 ('staged215',WORK/'phase16-publication-staging/delivery-manifest.json','7d1e452bb4646ba68504f6b814905807fe2ea3e13abd46e466d4580d54440f75'),
 ('concurrent-pr15',WORK/'concurrent-pr15-checkpoint-reconciliation/delivery-manifest.json','ca3a9d7133a46b080e7baf4320219cce156eefaf7720a4f92eb5b143d6f032bb'),
 ('bd4a-acquisition',WORK/'phase16-successor-acquisition-monitor/delivery-manifest.json','68be0f5c4a88d2c491eee16bd9909e3d111043233ba1477a03d21fa3a0819662'),
]
package_receipts=[];staged_doc=None;staged_paths=set()
for name,mp,expected in packages:
    raw=mp.read_bytes();assert sha(raw)==expected;manifest=json.loads(raw)
    for f in manifest['files']:
        path=f.get('path',f.get('repository_path'));b=Path(f.get('local_path',f.get('source_path'))).read_bytes()
        assert len(b)==f.get('bytes',f.get('size_bytes')) and sha(b)==f['sha256']
        if f.get('git_blob_sha1'):assert git(b)==f['git_blob_sha1']
        if name=='staged215':staged_paths.add(path)
        if name=='staged215' and path==DOC:staged_doc=b;continue
        assert path!=DOC;put(path,b)
    manifest_name={'staged215':'phase16-staged-215-file-manifest.json','concurrent-pr15':'phase16-concurrent-pr15-reconciliation-delivery-manifest.json','bd4a-acquisition':'phase16-bd4a-full-acquisition-audit-delivery-manifest.json'}[name]
    put(REPORT/manifest_name,raw)
    package_receipts.append({'name':name,'manifest_sha256':expected,'files':len(manifest['files']),'bytes':sum(f.get('bytes',f.get('size_bytes')) for f in manifest['files'])})
assert len(staged_paths)==215 and sha(staged_doc)=='be1e4a3d30da206c37252add250a14e0081117d7f948aa29f2a5a8da94132158'
overlay=json.loads((ROOT/'document-bd4a-overlay-receipt.json').read_bytes());doc=(ROOT/'document-update-v2.md').read_bytes()
assert sha(doc)==overlay['after_sha256']=='1854ead1fd42428fdab93f7b637cb5c7ae962b090ac3590bd0abbd812eaa500b'
assert overlay['before_sha256']==sha(staged_doc)
put(DOC,doc);put(REPORT/'phase16-status-before-bd4a-audit.md',staged_doc)
for n in ['document-bd4a-overlay.patch','document-bd4a-overlay-receipt.json','prepare_bd4a_document_overlay.py','finalize_publication.py']:
    put(REPORT/'phase16-final-publication'/n,(ROOT/n).read_bytes())
integration=json.loads((OUT/REPORT/'checkpoint5589-independent-integration/validation-report.json').read_bytes())
c=integration['counts'];assert (c['register'],c['exclude'],c['read_fields'],c['admitted'],c['read_context'],c['unread_context'],c['partitions'],c['read_characters'],c['read_utf8_bytes'])==(96,4,212,192,20,288,500,91600,194325)
assert integration['all_prior_decisions_unchanged_in_combined_loader']
files=[binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
paths={f['path'] for f in files};assert len(paths)==len(files)
active=[f for f in files if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-')]
assert len(active)==4
assert 'reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz' not in paths
for link in re.findall(r'\]\((\.\./reports/[^)]+)\)',doc.decode().split('\n---\n',1)[0]):
    assert link.removeprefix('../') in paths,link
validation={'schema':'hadith-bank-phase16-final-publication-validation-v1','status':'PASS','frozen_input_packages':package_receipts,'staged_payload_paths':215,'staged_non_document_bytes_unchanged':True,'document_overlay':overlay,'four_new_active_ledgers':[{'path':f['path'],'sha256':f['sha256'],'git_blob_sha1':f['git_blob_sha1']} for f in active],
    'existing_canonical_priority_queue_in_payload':False,'old29_active_ledgers_in_payload':False,'reviewed_new_occurrences':100,'register':96,'source_only':4,'complete_read_fields':212,'native_lossless_partitions':500,'reviewed_source_commit':'5589a3ffc3b43c3324ae26f2b6c4d33152834456','later_source_commit_preserved':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633','concurrent_merge_preserved':'4b61373da1cd6205270f0c87d7c502ee5b36db26','source_state_full_bd4a_verified':True,'full_intermediate5589_history_comparison_claimed':False,'latest_acquisition_counts_are_saved_export':True,'post_review_counts_are_projections':True,'fresh_base_tree_and_expected_head_checks_still_required':True,'github_branch_updated':False,'live_deployment_verified':False,'new_semantic_approvals_from_assembly':0,'core_payload_files_checked':len(files)}
put(REPORT/'phase16-final-publication-validation.json',enc(validation))
files=[binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
portable={'schema':'hadith-bank-phase16-final-payload-file-manifest-v1','manifest_excludes_its_own_recursive_hash':True,'files':[{k:v for k,v in f.items() if k!='local_path'} for f in files]}
put(REPORT/'phase16-file-manifest.json',enc(portable))
files=[binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
manifest={'schema':'hadith-bank-phase16-final-publication-v1','files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files),'latest_observed_main':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633','fresh_base_required_before_publication':True,'github_branch_updated':False,'local_validation':{'status':'PASS','report_path':(REPORT/'phase16-final-publication-validation.json').as_posix(),'report_sha256':sha(enc(validation))},'expected_overwrites':[{'path':DOC,'expected_before_bytes':62931,'expected_before_sha256':'ee2dbc858e5100c0e0d29ebb2426a955caebf280b66c2491475e42e5da3f867d','expected_before_git_blob_sha1':'25a9bd3d09df08589a693a00715641d83c88c1b6','after_sha256':sha(doc),'after_git_blob_sha1':git(doc)}],'input_packages':package_receipts}
target=ROOT/'manifest.json';assert not target.exists();target.write_bytes(enc(manifest))
print(json.dumps({'manifest_sha256':sha(target.read_bytes()),'files':len(files),'bytes':manifest['total_bytes'],'new_active_ledgers':len(active),'only_overwrite':DOC,'validation_sha256':sha(enc(validation))},indent=2))
