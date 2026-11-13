"""Root independent review of the bounded committed-state diagnostic change."""
from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent/'held-state-gzip-repair'
OUT=HERE/'publish';REL=Path('reports/web-source-resolution-20261113/held-state-gzip-independent-audit')
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
raw=(ROOT/'delivery-manifest.json').read_bytes();assert sha(raw)=='2936aeba688b305832a80c3ff17d647bf8b6a395f5bcf64226eba8c8dac0d09f'
manifest=json.loads(raw)
assert {f['path'] for f in manifest['files']}=={'scripts/export_deenhindi_held_evidence.py','tests/test_export_deenhindi_held_evidence.py','reports/web-source-resolution-20261113/held-state-gzip-export-validation.json'}
for f in manifest['files']:
 b=Path(f['local_path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
receipt=json.loads((ROOT/'publish/reports/web-source-resolution-20261113/held-state-gzip-export-validation.json').read_bytes())
baseline=(ROOT/'baseline-receipts.json').read_bytes();assert sha(baseline)==manifest['baseline_receipts_sha256']
for f in receipt['changed_files']:
 before=(ROOT/'baseline'/f['path']).read_bytes();after=(ROOT/'publish'/f['path']).read_bytes()
 for value,data in [(f['before'],before),(f['after'],after)]:assert value=={'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)}
before=ast.parse((ROOT/'baseline/scripts/export_deenhindi_held_evidence.py').read_text())
after=ast.parse((ROOT/'publish/scripts/export_deenhindi_held_evidence.py').read_text())
named=lambda t:{x.name:x for x in t.body if isinstance(x,(ast.ClassDef,ast.FunctionDef))}
unchanged={}
for name in ['Snapshot','git','main','replace_bundle','require']:
 a=ast.dump(named(before)[name],include_attributes=False);b=ast.dump(named(after)[name],include_attributes=False)
 assert a==b;unchanged[name]=sha(a.encode())
consts=lambda t:{x.targets[0].id:ast.dump(x.value,include_attributes=False) for x in t.body if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name)}
for name in ['MAX_RECORDS','MAX_BYTES','OUTPUT_BASE','SCHEMA','CODE']:assert consts(before)[name]==consts(after)[name]
test_before=ast.parse((ROOT/'baseline/tests/test_export_deenhindi_held_evidence.py').read_text())
test_after=ast.parse((ROOT/'publish/tests/test_export_deenhindi_held_evidence.py').read_text())
tests=lambda t:{n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
assert len(tests(test_before))==7 and len(tests(test_after))==9
assert tests(test_after)-tests(test_before)=={'test_complete_saved_state_is_exact_deterministic_and_hash_bound','test_whole_state_and_receipts_use_existing_cap_without_replacing_bundle'}
log=(ROOT/'validation.log').read_bytes();assert sha(log)==receipt['offline_validation']['log_sha256']=='96880ef0b0ea0eb2487a31f859cb2a23fff13e5d7a4f38f9c79d333777650a0b'
assert b'Ran 9 tests in 1.069s' in log and log.rstrip().endswith(b'OK')
patch=(ROOT/'exact.patch').read_bytes();assert sha(patch)==manifest['exact_patch_sha256']
report={'schema':'hadith-bank-independent-bounded-state-export-code-audit-v1','status':'PASS','reviewer':'/root',
 'base_commit':manifest['base_commit'],'primary_manifest_sha256':sha(raw),'exact_patch_sha256':sha(patch),
 'independent_complete_changed_module_context_and_test_diff_read':True,'all_payload_bytes_hash_verified':True,
 'independent_unchanged_guard_ast_sha256':unchanged,'same_existing_caps':{'records':250,'whole_bundle_bytes':33554432,'state_input_and_declared_decompression_bytes':67108864},
 'reviewed_behavior':['Read the exact committed state through unchanged saved-HEAD, working-copy and Git-blob guards.','Preserve the original complete bytes rather than reserializing JSON or selecting imported rows.','Use zero-time filename-free gzip and bind original/stored sizes and hashes plus the original Git blob.','Count compressed state and complete fixed receipts within the existing total cap before selecting any held row; retain final manifest-inclusive accounting.','Leave atomic output replacement, source selection, command-line bounds, workflow, network behavior, source budgets and review decisions unchanged.'],
 'primary_test_log_reopened_and_hash_verified':True,'focused_tests_passed':9,'new_substantive_tests':2,
 'tests_independently_rerun':False,'reason_no_duplicate_run':'The exact final test/module bytes and complete successful focused log are bound; the independent check reviews behavior, guard identity and the specific regression coverage.',
 'observed_transfer_failure':{'commit':'5589a3ffc3b43c3324ae26f2b6c4d33152834456','expected_state_bytes':12765240,'expected_state_sha256':'e08cbbf205e3fa4d4ac159d80663b392efe440135321c996000364373239e9f6','expected_state_git_blob':'16838750962a9ce31c545dad5eae4e0a62101d40','browser_download':'Timed out; subsequent AX protocol request timed out. No matching complete local file found.','github_fetch_blob':'Transport closed.','github_fetch_file_1000_line_probe':'Returned matching blob metadata with empty content.','no_rate_limit_access_or_github_outage_inferred':True},
 'current5589_full_state_recovered':False,'current5589_full_state_history_audit_performed':False,
 'effect_scope':'Future diagnostic bundles can carry the full state. This code approval does not claim an existing artifact, source run or deployment used the change.',
 'source_http_requests':0,'github_writes':0,'open_findings':[]}
files=[]
for name,b in [('independent-review.json',enc(report)),('exact.patch',patch),('focused-validation.log',log),('baseline-receipts.json',baseline),('audit.py',Path(__file__).read_bytes())]:
 p=OUT/REL/name;put(p,b);files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
m={'schema':'hadith-bank-independent-code-audit-delivery-v1','status':'PASS','files':files};put(HERE/'delivery-manifest.json',enc(m))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(m)),'files':len(files),'bytes':sum(f['bytes'] for f in files)},indent=2))
