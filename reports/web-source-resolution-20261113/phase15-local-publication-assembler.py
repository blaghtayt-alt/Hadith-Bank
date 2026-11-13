"""Freeze the exact reviewed publication and its expected overwrite baselines."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;OUT=HERE/'publish'
REPORT=Path('reports/web-source-resolution-20261113')
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(relative,b):
 p=OUT/relative;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,relative
 else:p.write_bytes(b)
def describe(p,local=False):
 b=p.read_bytes();d={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
 if local:d['local_path']=str(p)
 return d

config=json.loads((HERE/'input-manifests.json').read_bytes());assert len(config['packages'])==25
integration=OUT/REPORT/'checkpoint0639-independent-integration/validation-report.json';i=json.loads(integration.read_bytes())
assert sha(integration.read_bytes())=='44396439e0e24b5f1365e8ce03e94fec71854919c603cdc6a702196c92b5e673'
assert i['status']=='PASS' and i['source_count']==117 and i['counts']=={'admitted':226,'exclude':5,'explicit_field_decisions':522,'implicit_unread_field_slots':63,'partitions':585,'read_characters':127519,'read_context':29,'read_fields':255,'read_utf8_bytes':266493,'register':112,'selected_spans':445,'unread_context':330}
combined=OUT/REPORT/'phase15-combined1230-native-audit/validation-report.json';c=json.loads(combined.read_bytes())
assert sha(combined.read_bytes())=='8e17b7843d4013bb2f56a4db936956c3c241a563ef599b3701860525df8d401c' and c['status']=='PASS'
assert c['counts']['register']==1201 and c['counts']['exclude']==29 and c['counts']['nonempty_lossless_partitions']==6088
for f in c['active_ledgers']:
 b=(OUT/f['path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
queue=OUT/REPORT/'current-original3942-priority-field-queue.jsonl.gz'
assert sha(queue.read_bytes())=='343e72455fe122b59b37d795a59f9f8cca2358077723f1c725e4b1eaa3f57227'
prior_doc=WORK/'phase13-final-publication/publish/docs/WEB-SOURCE-RESOLUTION-20261113.md'
old=prior_doc.read_text().split('\n',1)[1].lstrip('\n')
heading='## Current review checkpoint — 93 new holds, 114 Urdu fields and Hadisuz323'
assert old.count(heading)==1
old=old.replace(heading,'## Historical phase13 status — 93 new holds, 114 Urdu fields and Hadisuz323',1)
put(Path('docs/WEB-SOURCE-RESOLUTION-20261113.md'),((HERE/'current-status.md').read_text().rstrip()+'\n\n'+old).encode())

overwrites=[]
def baseline(relative,local,expected):
 b=Path(local).read_bytes();assert sha(b)==expected
 assert (OUT/relative).is_file() and (OUT/relative).read_bytes()!=b
 overwrites.append({'path':relative,'expected_before_bytes':len(b),'expected_before_sha256':sha(b),'expected_before_git_blob_sha1':git(b),'after_sha256':sha((OUT/relative).read_bytes())})
baseline('imports/web-deenhindi-20261112/reviews/source-review-20261113-abudawud-tirmidhi-manual.json.gz',WORK/'phase14-original-abudawud50-urdu/staged-inputs/previous-active636.json.gz','6167b575a7f944a149f2db965ee937a4f9f74d856e39194b13ac7fcad6bc6abf')
bukh=WORK/'phase14-original-bukhari30-hi-ur';s=json.loads((bukh/'selection.json').read_bytes())
baseline(s['active_ledger_path'],bukh/'pinned-inputs'/s['active_ledger_path'],'925f5b3b70b6b3a23274ab7667b23d8577495c6a313c4cf0a66f786622352864')
baseline(s['priority_queue_path'],bukh/'pinned-inputs'/s['priority_queue_path'],'f5fa86ff645098396c7daf978f7491bddff6fd9104f5e50acc72f7d02701a660')
prior_manifest=json.loads((WORK/'phase13-final-publication/manifest.json').read_bytes());prior_doc_ref=next(f for f in prior_manifest['files'] if f['path']=='docs/WEB-SOURCE-RESOLUTION-20261113.md')
baseline(prior_doc_ref['path'],prior_doc,prior_doc_ref['sha256'])
for f in json.loads((WORK/'held-state-gzip-repair/baseline-receipts.json').read_bytes())['files']:
 if f['path'].startswith(('scripts/','tests/')):baseline(f['path'],WORK/'held-state-gzip-repair/baseline'/f['path'],f['sha256'])
assert len(overwrites)==6
summary={'schema':'hadith-bank-phase15-final-publication-validation-v1','status':'PASS',
 'source_review_checkpoint':config['source_review_checkpoint'],'latest_observed_acquisition_checkpoint':config['latest_observed_acquisition_checkpoint'],
 'new_cohort':i['counts'],'new_parent_dispositions_resolved':117,'source_count_delta':0,
 'original_cohort_extension':{'new_fields':90,'occurrences':80,'hi':10,'ur':80,'characters':47897,'utf8_bytes':89574,'parent_disposition_changes':0,'remaining_priority_fields':6411,'remaining_priority_occurrences':3404},
 'combined_native':{'active_ledgers':6,'sources':1230,'register':1201,'source_only':29,'field_slots':6150,'lossless_nonempty_partitions':6088,'exact_empty_states':62,'metadata_leaf_equalities':276219},
 'all25_final_packages_hash_verified':True,'expected_overwrites':overwrites,
 'future_state_artifact_change':{'primary_manifest_sha256':'2936aeba688b305832a80c3ff17d647bf8b6a395f5bcf64226eba8c8dac0d09f','independent_manifest_sha256':'ae880cabfbc27dec81526152cd7340b9adbf64f763f3cee3b21ce1aa3f626c8c','focused_tests':9,'same_caps_and_workflow':True},
 'latest5589_full_state_history_audit_performed':False,'latest5589_bounded217_source_audit':'PASS',
 'latest5589_new100_semantically_resolved_by_this_payload':False,'current_head_build_or_deployment_claimed':False,
 'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes_by_local_assembly':0,
 'publication_requires_fresh_main_and_exact_expected_blob_checks':True}
put(REPORT/'phase15-final-publication-validation.json',enc(summary))
put(REPORT/'phase15-local-publication-assembler.py',Path(__file__).read_bytes())
paths=sorted(p for p in OUT.rglob('*') if p.is_file())
payload_path=OUT/REPORT/'phase15-file-manifest.json'
assert payload_path not in paths
payload={'schema':'hadith-bank-phase15-payload-manifest-v1','source_review_checkpoint':config['source_review_checkpoint'],
 'prior_review_publication':'6b20d4578c85ec2a8fb00bb7a7796f487cde755f','latest_observed_source_checkpoint':config['latest_observed_acquisition_checkpoint'],
 'validation':summary,'package_receipts':[{'name':p['name'],'original_manifest_sha256':p['manifest_sha256'],'portable_manifest_path':p['portable_manifest_path']} for p in config['packages']],
 'manifest_excludes_own_recursive_hash':True,'files':[describe(p) for p in paths]}
put(payload_path.relative_to(OUT),enc(payload));paths.append(payload_path);paths.sort()
m={'schema':'hadith-bank-phase15-final-publication-manifest-v1','local_validation':'PASS','files':[describe(p,True) for p in paths],
 'total_files':len(paths),'total_bytes':sum(p.stat().st_size for p in paths),'expected_overwrites':overwrites,
 'reviewed_new_held_occurrences':117,'new_original_cohort_fields':90,'latest_observed_main':config['latest_observed_acquisition_checkpoint'],
 'fresh_base_required_before_publication':True,'github_branch_updated':False}
(HERE/'manifest.json').write_bytes(enc(m));(HERE/'overwrite-baselines.json').write_bytes(enc(overwrites))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(m)),'files':len(paths),'bytes':m['total_bytes'],'expected_overwrites':len(overwrites)},indent=2))
