"""Rehash all complete publication trees, exact payloads and preserved concurrent work."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def gitblob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def treehash(entries):
 entries=sorted(entries,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
 body=b''.join((str(e['mode']).lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in entries)
 return hashlib.sha1(b'tree '+str(len(body)).encode()+b'\0'+body).hexdigest()
def canon(entries):return {e['path']:{k:e[k] for k in ['path','mode','type','sha']} for e in entries}
mb=(ROOT/'manifest.json').read_bytes();assert sha(mb)=='b7ce63801ddaecb8febc279726297c28e6fc32a71f691ad907f42fc299412114';m=json.loads(mb)
bb=(ROOT/'verified-base-trees.json').read_bytes();base=json.loads(bb)
rb=(ROOT/'tree-verification-receipts.json').read_bytes();rs=json.loads(rb)
receipts={r['directory']:r for r in rs};assert len(receipts)==len(rs)==56
existing=0
for directory,t in base.items():
 if t['sha'] is None:assert t['tree']==[];continue
 assert not t.get('truncated') and treehash(t['tree'])==t['sha'],directory;existing+=1
for directory,r in receipts.items():
 t=r['complete_tree'];assert not t.get('truncated') and r['full_entry_map_verified']
 assert t['sha']==r['after_tree_sha']==treehash(t['tree']),directory
 assert r['before_tree_sha']==base[directory]['sha']
 expected=canon(base[directory]['tree'])
 for e in r['changes']:expected[e['path']]={k:e[k] for k in ['path','mode','type','sha']}
 assert canon(t['tree'])==expected,directory
 for e in t['tree']:
  child=directory+'/'+e['path'] if directory else e['path']
  if e['type']=='tree' and child in receipts:assert e['sha']==receipts[child]['after_tree_sha']
assert base['']['sha']=='6b68e57442f6503f8044b455363a0645c7d2ca04'
assert receipts['']['after_tree_sha']=='1a4a609c58936eda0dfae376dd4370d2988a5997'
overwrites=[]
for f in m['files']:
 b=Path(f['local_path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'] and gitblob(b)==f['git_blob_sha1'],f['path']
 p=Path(f['path']);d=p.parent.as_posix();d='' if d=='.' else d
 entry=canon(receipts[d]['complete_tree']['tree'])[p.name]
 assert entry['sha']==f['git_blob_sha1'] and entry['type']=='blob' and entry['mode']==f['mode']
 old=canon(base[d]['tree']).get(p.name)
 if old:
  expected=next(x for x in m['expected_overwrites'] if x['path']==f['path'])
  assert old['sha']==expected['before_git_blob_sha1'];overwrites.append(f['path'])
assert overwrites==['docs/WEB-SOURCE-RESOLUTION-20261113.md']
assert len(m['files'])==281 and sum(f['bytes'] for f in m['files'])==7945012
preserve_raw=(ROOT/'successor-preservation-gate.json').read_bytes();preserve=json.loads(preserve_raw)
assert preserve['from']=='0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a' and preserve['to']=='88222b998c9c3db241cf1f37048dc2db4a8609e8'
assert preserve['ancestry_chain_verified'] and preserve['direct_parent_verified_for_each_link']
assert preserve['previous_active_ledgers_exact']==37 and preserve['canonical_priority_queue_6361_unchanged']
assert preserve['source_state_and_saved_imports_unchanged'] and preserve['new_paths']==280
assert preserve['all281_paths_checked'] and len(preserve['verified_overwrites'])==1
finalroot=canon(receipts['']['complete_tree']['tree'])
assert finalroot['AGENTS.md']['sha']=='458f2213b02f1f35bfcab17aebd4ac507b4d1740'
assert finalroot['README.md']['sha']=='80eca8d8d758d845c51b8615ab0fdba403be9f3f'
assert canon(receipts['docs']['complete_tree']['tree'])['WEBSITE.md']['sha']=='09456492053511f861c040a25a8c8b9f2b9311eb'
reports=canon(receipts['reports']['complete_tree']['tree'])
assert reports['ACTIVE-BOOKS-AUDIT-2026-11-14.json']['sha']=='549a21fd01f44c30e43200c4aae03457cb58c198'
assert reports['ACTIVE-BOOKS-AUDIT-2026-11-14.md']['sha']=='d23e06538b19fd7749f0893b755cd4112d481cbe'
for name in ['scripts','.github','catalog','materials']:
 assert finalroot[name]==canon(base['']['tree'])[name]
report={'schema':'hadith-bank-publication-rehash-gate-v1','status':'PASS','manifest_sha256':sha(mb),'parent_commit':preserve['to'],'documented_source_checkpoint':preserve['from'],'source_review_pin':m['source_review_pin'],'before_root_tree_sha':base['']['sha'],'after_root_tree_sha':receipts['']['after_tree_sha'],'complete_before_tree_objects_rehashed':existing,'complete_after_tree_objects_rehashed':56,'payload_files_rehashed':281,'payload_bytes_rehashed':7945012,'tree_verification_receipts_sha256':sha(rb),'verified_base_trees_sha256':sha(bb),'successor_preservation_gate_sha256':sha(preserve_raw),'all_payload_paths_resolve_to_frozen_blob_ids':True,'full_expected_entry_maps_match':True,'concurrent_readme_and_active_book_audit_preserved':True,'only_preexisting_overwrite':overwrites,'all37_prior_active_ledgers_and_canonical6361_queue_preserved':True,'github_branch_updated':False,'live_deployment_claimed':False}
target=ROOT/'publication-rehash-gate.json'
if target.exists():assert target.read_bytes()==enc(report)
else:target.write_bytes(enc(report))
print(json.dumps(report,indent=2))
