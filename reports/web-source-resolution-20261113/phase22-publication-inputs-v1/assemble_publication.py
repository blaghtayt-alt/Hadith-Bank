"""Stage the exact85 reviewed parents and64f4 audit against independently read-back7a3462e."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import collections,gzip,hashlib,json
H=Path(__file__).resolve().parent;W=H.parent;OUT=H/'publish'
PREFIX=Path('reports/web-source-resolution-20261113/phase22-publication-inputs-v1')
REV=Path('imports/web-deenhindi-20261112/reviews')
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def th(es):
 es=sorted(es,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
 b=b''.join((str(e['mode']).lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in es)
 return hashlib.sha1(b'tree '+str(len(b)).encode()+b'\0'+b).hexdigest()
def safe(s):
 s=str(s);p=PurePosixPath(s);assert s and not p.is_absolute() and '..' not in p.parts and '\\' not in s;return s
def read(p):return json.loads(p.read_bytes())
def local(f):return Path(f.get('local_path',f.get('source_path')))
def main():
 assert not (H/'manifest.json').exists(),'Frozen publication is immutable.'
 cb=(H/'staging-inputs.json').read_bytes();cfg=json.loads(cb)
 base=cfg['documented_base_commit'];root=cfg['root_tree_sha']
 assert base=='7a3462ef5513e3c116ead9a496420e8b9f484841' and root=='6829cc1d072631e6526ff0d9218a08c12fd5b406'
 assert cfg['root_status_review_complete']
 staged={};packages={};provenance=[]
 def add(path,b,origin):
  path=safe(path)
  if path in staged:assert staged[path]['sha256']==sha(b);staged[path]['origins'].append(origin);return
  p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert p.read_bytes()==b
  else:p.write_bytes(b)
  staged[path]={'path':path,'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b),'mode':'100644','origins':[origin]}
 for spec in cfg['packages']:
  name=spec['name'];p=W/spec['manifest_path'];b=p.read_bytes();assert sha(b)==spec['manifest_sha256']
  m=json.loads(b);assert name not in packages;assert len(m['files'])==len({f['path'] for f in m['files']})
  for f in m['files']:
   q=local(f);assert q.is_file() and not q.is_symlink() and q.resolve().is_relative_to(p.parent.resolve())
   d=q.read_bytes();assert len(d)==f.get('bytes',f.get('size_bytes')) and sha(d)==f['sha256']
   assert not f.get('git_blob_sha1') or git(d)==f['git_blob_sha1'];add(f['path'],d,name)
  add(PREFIX/'manifests'/f'{name}.json',b,'Exact frozen input manifest');packages[name]=m
  provenance.append({'name':name,'local_manifest':str(p),'sha256':sha(b),'files':len(m['files']),'bytes':sum(f.get('bytes',f.get('size_bytes')) for f in m['files'])})
 assert len(packages)==12
 def payload(name,suffix):
  fs=[f for f in packages[name]['files'] if f['path'].endswith(suffix)];assert len(fs)==1;return local(fs[0]).read_bytes()
 ir=payload('combined85-integration','validation-report.json');assert sha(ir)==cfg['integration_report_sha256'];integ=json.loads(ir)
 expected={'register':84,'exclude':1,'read_fields':173,'admitted':168,'read_context':5,'unread_context':252,'empty':0,'source_slots':425,'partitions':425,'read_characters':79196,'read_utf8_bytes':170479}
 assert integ['result']=='PASS' and integ['source_commit']=='17cd396eb858a29162505d545aad556ac73ce9ce'
 assert integ['published_review_baseline_commit']==base
 assert all(integ['counts'].get(k,0)==v for k,v in expected.items())
 assert (integ['native_combined_loader_ledgers'],integ['native_combined_loader_ids'])==(49,3661)
 assert (integ['source_count'],integ['source_files_rehashed_against_frozen_proof'],integ['full_raw_reparses_bound_from_frozen_preparation'])==(85,170,85)
 assert integ['native_new85_apply_finish']=='PASS' and integ['all45_prior_blobs_dependencies_and3576_decisions_unchanged']
 primaries=cfg['primary_packages'];assert len(primaries)==4
 ids=set();primary_entries=[];counts=collections.Counter();reads=collections.Counter()
 for name,number in primaries.items():
  fs=[f for f in packages[name]['files'] if Path(f['path']).parent==REV and Path(f['path']).name.startswith('source-review-')];assert len(fs)==1
  f=fs[0];primary_entries.append(f);ledger=json.loads(gzip.decompress((OUT/f['path']).read_bytes()))
  sb=(OUT/safe(ledger['source_ledger_path'])).read_bytes();assert sha(sb)==ledger['source_ledger_sha256']
  rows=[json.loads(x) for x in gzip.decompress(sb).splitlines()];saved={'deenhindi-'+r['collection']+':'+r['number']:r for r in rows}
  assert len(rows)==len(saved)==len(ledger['records'])==number
  for d in ledger['records']:
   ident=d.get('id',d.get('occurrence_id'))
   assert ident in saved and ident not in ids;ids.add(ident);counts[d['decision']]+=1
   for f in d.get('field_reviews',d.get('fields')):
    if f['reviewed']:
     reads['read_fields']+=1;reads['read_characters']+=f['chars_reviewed'];reads['read_utf8_bytes']+=f['bytes_reviewed'];reads['admitted' if f.get('spans',f.get('selected_spans',[])) else 'read_context']+=1
 assert len(ids)==85 and counts=={'register':84,'exclude':1} and all(reads[k]==expected[k] for k in reads)
 ar=payload('acquisition-64f4-state-history','saved-state-audit.json');assert sha(ar)==cfg['acquisition_report_sha256'];acq=json.loads(ar)
 assert acq['status']=='PASS_SAVED_CHECKPOINT_AUDIT' and acq['saved_commit']=='64f4ed50ed6026855237a5d547a86dd03e73f804'
 assert acq['saved_tree']=='829d4cab7e8d95270537aa12f1e43e3ae2e7805b'
 actual={k:acq['saved_progress'][k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count']}
 assert actual=={'imported_count':18570,'registered_hadith_count':18132,'non_narration_source_entries':165,'classification_pending_count':273,'pending_fetch_count':17820,'errors_count':0}
 part=acq['held_partition'];keys={i.removeprefix('deenhindi-') for i in ids}
 assert keys<=set(part['retained_prior171_keys']) and not keys&set(part['new102_keys'])
 assert len(part['retained_prior171_keys'])==171 and len(part['new102_keys'])==102
 assert set(part['current273_held_keys'])==set(part['retained_prior171_keys'])|set(part['new102_keys'])
 assert acq['complete_cap_augmentation']['source_files_verified']==546 and acq['complete_cap_augmentation']['raw_html_reparses']==273
 assert acq['source_state_preservation']['all18089_prior_imported_descriptors_exact']
 assert acq['source_state_preservation']['all1000_error_histories_exact'] and acq['source_state_preservation']['all1000_consumed_attempts_exact']
 assert acq['continuation_failure']['target_workflow_id']==415715399 and not acq['continuation_failure']['workflow_enabled_by_auditor']
 rb=W/'phase21-independent-readback';receipt=read(rb/'readback-receipt.json')
 assert sha((rb/'readback-receipt.json').read_bytes())=='fd04bede279d773a0ebbc53dc66f3df4e19e662046deb798e77bb3f1214ebf0b'
 assert receipt['status']=='PASS' and receipt['published_commit']==base and receipt['actual_root_tree']==root and receipt['actual_parent_commit']==acq['saved_commit']
 assert receipt['resulting_active_ledgers']==45 and receipt['resulting_manual_ids']==3576
 assert all(e['before_after_full_entry_equal'] for e in receipt['source64f4_all12_nonreview_entries_preserved'])
 pool={};origins=collections.defaultdict(list);used=set()
 def addtree(t,origin):
  assert not t.get('truncated',False)
  if t['sha'] is None:assert t['tree']==[];return
  assert th(t['tree'])==t['sha'] and len(t['tree'])==len({e['path'] for e in t['tree']})
  es=sorted([{k:e[k] for k in ['path','mode','type','sha']} for e in t['tree']],key=lambda e:e['path'])
  if t['sha'] in pool:assert pool[t['sha']]==es
  else:pool[t['sha']]=es
  origins[t['sha']].append(origin)
 prior_receipts={}
 for spec in cfg['prior_publication_receipts']:
  b=(W/'phase21-final-publication'/spec['name']).read_bytes();assert sha(b)==spec['sha256'] and len(b)==spec['bytes']
  prior_receipts[spec['name']]=json.loads(b);add(PREFIX/'receipts'/('phase21-'+spec['name']),b,'Prior exact publication receipt')
 assert prior_receipts['publication-receipt.json']['commit']==base and prior_receipts['publication-receipt.json']['tree_sha']==root
 for d,t in prior_receipts['verified-base-trees.json'].items():
  if t is not None:addtree(t,'Prior verified before tree '+d)
 for r in prior_receipts['tree-verification-receipts.json']:addtree(r['complete_tree'],'Prior verified published tree '+r['directory'])
 for p in sorted((rb/'input').glob('*tree*.json')):
  d=read(p)
  if 'content' in d:addtree(json.loads(d['content']),'Fresh independent readback '+p.name)
 def lookup(path):
  parts=safe(path).split('/');current=root;chain=[]
  for index,name in enumerate(parts):
   assert current in pool,('Missing actual ancestor',path,index,current);used.add(current);chain.append({'directory':'/'.join(parts[:index]),'git_tree_sha1':current})
   es=[e for e in pool[current] if e['path']==name];assert len(es)<=1
   if not es:return {'status':'new_path','first_absent_component':'/'.join(parts[:index+1]),'ancestor_chain':chain}
   e=es[0]
   if index==len(parts)-1:return {'status':'existing_path','git_object_sha1':e['sha'],'mode':e['mode'],'type':e['type'],'ancestor_chain':chain}
   assert e['type']=='tree';current=e['sha']
 queue=(W/'phase20-independent-readback/downloaded'/QUEUE).read_bytes()
 assert sha(queue)=='8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349' and lookup(QUEUE)['git_object_sha1']==git(queue)
 qrows=[json.loads(r) for r in gzip.decompress(queue).splitlines()];qlang=collections.Counter(f['language'] for r in qrows for f in r['fields'])
 assert len(qrows)==3354 and qlang=={'hi':3260,'ur':3051} and QUEUE not in staged
 rev=lookup(REV);old=[e for e in pool[rev['git_object_sha1']] if e['type']=='blob' and e['path'].startswith('source-review-')];assert len(old)==45
 baseline=W/'phase22-checkpoint17cd-independent-integration/validation/published-reviews'
 for e in old:assert git((baseline/REV/e['path']).read_bytes())==e['sha'] and (REV/e['path']).as_posix() not in staged
 before=(rb/'downloaded'/DOC).read_bytes();assert len(before)==121575 and sha(before)=='69767930e7c653ae36473427286132defcc783c62f8902c600bb6478fc73b2c4'
 assert lookup(DOC)['git_object_sha1']==git(before)
 prefix=(H/cfg['status_prefix_path']).read_bytes();assert sha(prefix)==cfg['root_approved_status_prefix_sha256']
 after=prefix+before;assert after.endswith(before)
 add(DOC,after,'Approved current prefix plus complete previous document')
 add(PREFIX/'previous-status-document.md',before,'Exact previous121575-byte document')
 add(PREFIX/'current-status-prefix.md',prefix,'Root-read current status')
 dr={'schema':'hadith-bank-versioned-status-document-update-v1','documented_base_commit':base,'path':DOC,'before_bytes':len(before),'before_sha256':sha(before),'before_git_blob_sha1':git(before),'prefix_bytes':len(prefix),'prefix_sha256':sha(prefix),'after_bytes':len(after),'after_sha256':sha(after),'after_git_blob_sha1':git(after),'complete_old_document_exact_suffix_including_original_title':True,'current_saved_export_source_commit':acq['saved_commit'],'review_projection_is_a_new_saved_export':False,'current_publication_live_deployment_claimed':False}
 add(PREFIX/'document-update-receipt.json',enc(dr),'Exact document preservation receipt')
 add(PREFIX/'staging-inputs.json',cb,'Frozen package bindings');add(PREFIX/'assemble_publication.py',Path(__file__).read_bytes(),'Publication assembler')
 proofs={p:lookup(p) for p in staged};assert {p for p,v in proofs.items() if v['status']=='existing_path'}=={DOC}
 assert all(lookup(f['path'])['status']=='new_path' for f in primary_entries)
 assert all(p.startswith(('docs/','imports/web-deenhindi-20261112/reviews/','reports/web-source-resolution-20261113/')) for p in staged)
 tp=str(PREFIX/'complete-used-base-ancestor-trees.json.gz');assert lookup(tp)['status']=='new_path'
 add(tp,gzip.compress(enc({'schema':'hadith-bank-exact-base-complete-ancestor-proof-v1','commit':base,'root_tree_sha':root,'trees':[{'git_tree_sha1':s,'entries':pool[s],'origins':origins[s]} for s in sorted(used)]}),mtime=0),'Exact linked complete Git ancestor trees')
 projection={'fetched':18570,'registered':18132+84+84,'source_only':165+2+1,'held':273-86-85,'unfetched':17820}
 validation={'schema':'hadith-bank-phase22-publication-staging-validation-v1','result':'PASS','documented_base_commit':base,'base_root_tree_sha':root,'only_existing_path_update':DOC,'path_proofs':proofs,'old45_active_review_entries_unchanged':old,'prior_manual_ids':3576,'combined_active_ledgers':49,'combined_manual_ids':3661,'canonical_priority_queue_sha256':sha(queue),'canonical_priority_queue_not_in_write_set':True,'canonical_queue_fields':6311,'canonical_queue_ids':3354,'canonical_queue_by_language':dict(qlang),'new_active_ledgers':[{'path':f['path'],'sha256':f['sha256']} for f in primary_entries],'review_cohort_occurrences':85,'review_counts':expected,'integration_report_sha256':sha(ir),'actual_acquisition_audit_sha256':sha(ar),'actual_saved_progress':actual,'fixed64f4_projection_after_published86_and_current85':projection,'projection_is_saved_export':False,'all_declared_packages_hash_checked':provenance,'source_requests':0,'workflow_dispatches':0,'disabled_source_workflow_unchanged':True,'live_deployment_claimed':False,'fresh_expected_head_lease_required':True}
 vp=str(PREFIX/'staging-validation.json');assert lookup(vp)['status']=='new_path';add(vp,enc(validation),'Final package/path/status gate')
 pp=str(PREFIX/'payload-file-manifest.json');assert lookup(pp)['status']=='new_path'
 add(pp,enc({'schema':'hadith-bank-portable-publication-payload-manifest-v1','documented_base_commit':base,'base_root_tree_sha':root,'manifest_excludes_its_own_recursive_hash':True,'files':[{k:v for k,v in staged[p].items() if k not in ['local_path','origins']} for p in sorted(staged)]}),'Portable payload manifest')
 for f in staged.values():
  b=Path(f['local_path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
 assert {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}==set(staged)
 manifest={'schema':'hadith-bank-frozen-phase22-publication-manifest-v1','repository':'blaghtayt-alt/Hadith-Bank','branch':'main','documented_base_commit':base,'base_root_tree_sha':root,'published_review_baseline_commit':base,'source_review_pin':integ['source_commit'],'generated_at_utc':datetime.now(timezone.utc).isoformat(),'input_packages':provenance,'expected_overwrites':[{'path':DOC,'before':{'bytes':len(before),'sha256':sha(before),'git_blob_sha1':git(before)},'after':{'bytes':len(after),'sha256':sha(after),'git_blob_sha1':git(after)}}],'files':[staged[p] for p in sorted(staged)],'total_files':len(staged),'total_bytes':sum(f['bytes'] for f in staged.values()),'new_repository_paths_at_documented_base':len(staged)-1,'existing_paths_changed':1,'new_active_ledgers':4,'existing_active_ledgers_changed':0,'canonical_priority_queue_changed':False,'local_validation':{'status':'PASS','path':vp,'sha256':staged[vp]['sha256'],'combined85_native_source_report_sha256':sha(ir),'actual_saved_state_audit_sha256':sha(ar),'portable_payload_file_manifest_path':pp,'portable_payload_file_manifest_sha256':staged[pp]['sha256']},'fresh_base_required_before_publication':True,'github_branch_updated':False,'new_review_projection_is_saved_export':False,'current_publication_live_deployment_verified':False}
 (H/'manifest.json').write_bytes(enc(manifest));(H/'document-update.md').write_bytes(after);(H/'document-update-receipt.json').write_bytes(enc(dr))
 print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),'files':len(staged),'bytes':manifest['total_bytes'],'new_paths':len(staged)-1,'overwrites':1,'document_bytes':len(after),'document_sha256':sha(after),'validation_sha256':staged[vp]['sha256']},indent=2))
if __name__=='__main__':main()
