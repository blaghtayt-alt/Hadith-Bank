"""Freeze phase18 against exact3e574 trees; no GitHub or source-site operations."""
from pathlib import Path
from datetime import datetime,timezone
import collections
import gzip
import hashlib
import json

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
OUT=HERE/'publish'
PREFIX=Path('reports/web-source-resolution-20261113/phase18-publication-inputs-v1')
REV=Path('imports/web-deenhindi-20261112/reviews')
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
sha=lambda x:hashlib.sha256(x).hexdigest()
git=lambda x:hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def tree_sha(entries):
    ordered=sorted(entries,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
    data=b''.join((str(e['mode']).lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in ordered)
    return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).hexdigest()

def main():
    assert not (HERE/'manifest.json').exists(),'A frozen publication stage must remain immutable.'
    config_bytes=(HERE/'staging-inputs.json').read_bytes();config=json.loads(config_bytes)
    base=config['documented_base_commit'];root_sha=config['root_tree_sha']
    assert base=='3e574b9e7e4dd7cf8bc23232249004a18692c61c' and root_sha=='8f45b8c41b1e7f3c1831c24b5fc053fcd7cceb4e'
    staged={};packages={};provenance=[]
    def add(path,data,origin):
        path=str(path);assert not Path(path).is_absolute() and '..' not in Path(path).parts
        if path in staged:
            assert staged[path]['sha256']==sha(data) and staged[path]['bytes']==len(data),('path collision',path)
            staged[path]['origins'].append(origin);return
        dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==data,('staged bytes changed',path)
        else:dest.write_bytes(data)
        staged[path]={'path':path,'local_path':str(dest),'bytes':len(data),'sha256':sha(data),
                      'git_blob_sha1':git(data),'mode':'100644','origins':[origin]}
    for item in config['packages']:
        name=item['name'];p=WORK/item['manifest_path'];raw=p.read_bytes()
        assert sha(raw)==item['manifest_sha256'],name
        manifest=json.loads(raw);assert len({f['path'] for f in manifest['files']})==len(manifest['files'])
        for f in manifest['files']:
            data=Path(f['local_path']).read_bytes();assert len(data)==f['bytes'] and sha(data)==f['sha256']
            if f.get('git_blob_sha1'):assert git(data)==f['git_blob_sha1']
            add(f['path'],data,name)
        add(PREFIX/'manifests'/(name+'.json'),raw,name+' immutable manifest')
        packages[name]=manifest
        provenance.append({'name':name,'local_manifest':str(p),'sha256':sha(raw),'files':len(manifest['files']),
                           'bytes':sum(f['bytes'] for f in manifest['files'])})
    assert len(packages)==13
    def payload(name,suffix):
        fs=[f for f in packages[name]['files'] if f['path'].endswith(suffix)]
        assert len(fs)==1,(name,suffix)
        return fs[0],Path(fs[0]['local_path']).read_bytes()
    integration_entry,integration_bytes=payload('combined92-integration','validation-report.json')
    assert sha(integration_bytes)==config['integration_report_sha256']
    integration=json.loads(integration_bytes)
    expected={'register':87,'exclude':5,'read_fields':199,'admitted':174,'read_context':25,'unread_context':259,
              'empty':2,'source_slots':460,'partitions':458,'read_characters':131417,'read_utf8_bytes':275705}
    assert integration['result']=='PASS' and integration['native_new92_apply_finish']=='PASS'
    assert all(integration['counts'][k]==v for k,v in expected.items())
    assert integration['source_commit']=='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
    assert integration['published_review_baseline_commit']=='f9be12177046e372df088f96b255fd09914fad5a'
    assert integration['source_count']==92 and integration['source_files_verified']==184 and integration['full_raw_reparses_bound']==92
    assert integration['native_combined_loader_ledgers']==37 and integration['native_combined_loader_ids']==3410
    assert integration['prior33_published_manual_ledgers']==33 and integration['prior_published_manual_ids']==3318
    assert integration['all33_prior_blobs_dependencies_and3318_decisions_unchanged'] and not integration['id_collisions']
    # Recount only the already approved immutable decisions; this is not a new language reading.
    primary_entries=[];ids=set();source_counts=collections.Counter();field_counts=collections.Counter();field_reads=[]
    for name in ('primary-bukhari-ibnmajah','primary-muslim','primary-nasai-ibnmajah','primary-other'):
        active=[f for f in packages[name]['files'] if Path(f['path']).parent==REV and Path(f['path']).name.startswith('source-review-')]
        assert len(active)==1;entry=active[0];primary_entries.append(entry)
        doc=json.loads(gzip.decompress(Path(entry['local_path']).read_bytes()))
        baseline=OUT/doc['source_ledger_path'];assert sha(baseline.read_bytes())==doc['source_ledger_sha256']
        saved=[json.loads(x) for x in gzip.decompress(baseline.read_bytes()).splitlines()]
        saved_ids={'deenhindi-'+x['collection']+':'+x['number']:x for x in saved}
        assert len(saved_ids)==len(doc['records'])==23
        for rec in doc['records']:
            oid=rec.get('id',rec.get('occurrence_id'));assert oid in saved_ids and oid not in ids;ids.add(oid)
            source_counts[rec['decision']]+=1
            fields=rec.get('field_reviews',rec.get('fields'))
            for f in fields:
                if f.get('reviewed'):
                    field_counts['read_fields']+=1;field_counts['read_characters']+=f['chars_reviewed'];field_counts['read_utf8_bytes']+=f['bytes_reviewed']
                    field_reads.append((oid,f['language']))
                    field_counts['admitted' if f.get('spans',f.get('selected_spans',[])) else 'read_context']+=1
    assert len(ids)==92 and source_counts=={'register':87,'exclude':5}
    assert all(field_counts[k]==expected[k] for k in field_counts)
    assert len(field_reads)==len(set(field_reads))==199
    acq_entry,acq_bytes=payload('acquisition-3e574-state-history','saved-state-audit.json')
    assert sha(acq_bytes)==config['acquisition_report_sha256'];acq=json.loads(acq_bytes)
    assert acq['status']=='PASS' and acq['saved_commit']==base and acq['saved_tree']==root_sha
    assert acq['saved_parent']=='f9be12177046e372df088f96b255fd09914fad5a'
    progress=acq['saved_progress']
    assert {k:progress[k] for k in ('imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count')}=={
        'imported_count':17131,'registered_hadith_count':16804,'non_narration_source_entries':155,'classification_pending_count':172,'pending_fetch_count':19259,'errors_count':0}
    partition=acq['held_partition'];assert set(partition['retained_prior92_keys'])=={x.removeprefix('deenhindi-') for x in ids} or set(partition['retained_prior92_keys'])==ids
    assert len(partition['new80_keys'])==80 and len(partition['current172_held_keys'])==172
    preserve=acq['source_state_preservation']
    assert preserve['all16664_prior_imported_descriptors_exact'] and preserve['all1000_error_histories_exact'] and preserve['all1000_consumed_attempts_exact']
    assert acq['source_controls']['source_stop_guards_and_cadence_unchanged']
    projection={'fetched':17131,'registered':16804+source_counts['register'],'source_only':155+source_counts['exclude'],
                'held':172-len(ids),'unfetched':19259}
    assert projection=={'fetched':17131,'registered':16891,'source_only':160,'held':80,'unfetched':19259}
    prior_receipts={}
    for r in config['phase17_publication_receipts']:
        data=(WORK/'phase17-final-publication'/r['name']).read_bytes();assert sha(data)==r['sha256']
        prior_receipts[r['name']]=json.loads(data)
        add(PREFIX/'receipts'/('phase17-'+r['name']),data,'Exact phase17 publication receipt')
    pub=prior_receipts['publication-receipt.json']
    assert pub['commit_sha']==acq['saved_parent'] and pub['root_tree_sha']=='dd0f6ca52b3b93b2d89e3e8509bcc5e7eea64e57'
    assert pub['manifest_sha256']==sha((WORK/'phase17-final-publication/manifest.json').read_bytes())
    # Complete tree objects are reusable only by their reconstructed Git identity.
    pool={};origins=collections.defaultdict(list);used=set()
    def add_tree(entries,expected,origin):
        assert tree_sha(entries)==expected
        canonical=sorted([{'path':e['path'],'mode':'040000' if e['type']=='tree' else str(e['mode']).lstrip('0'),
                           'type':e['type'],'sha':e['sha']} for e in entries],key=lambda e:e['path'])
        assert tree_sha(canonical)==expected
        if expected in pool:assert pool[expected]==canonical
        else:pool[expected]=canonical
        origins[expected].append(origin)
    old_base_bytes=(WORK/'phase17-final-publication/verified-base-trees.json').read_bytes()
    assert sha(old_base_bytes)=='300df7178512d58e3540ad98d2de832ef04672085d558f78feaed1367842821f'
    for directory,t in json.loads(old_base_bytes).items():
        if t is not None and t.get('sha'):
            assert not t.get('truncated',False);add_tree(t['tree'],t['sha'],'phase17 verified before tree '+directory)
        elif t is not None:
            assert t.get('sha') is None and t['tree']==[],('Non-object placeholder has content',directory)
    for t in prior_receipts['tree-verification-receipts.json']:
        complete=t['complete_tree'];assert not complete.get('truncated',False)
        assert complete['sha']==t['after_tree_sha'];add_tree(complete['tree'],complete['sha'],'phase17 published tree '+t['directory'])
    phase16_tree_bytes=(WORK/'phase16-final-publication/tree-verification-receipts.json').read_bytes()
    assert sha(phase16_tree_bytes)=='81678c86d9140d81be5b940ff52e022741525afae2b19476f7d2f2236cc5ec09'
    for t in json.loads(phase16_tree_bytes)['trees']:
        add_tree(t['entries'],t['after_tree_sha'],'phase16 complete tree '+t['directory'])
    _,current_tree_bytes=payload('acquisition-3e574-state-history','complete-path-trees.json.gz')
    current_trees=json.loads(gzip.decompress(current_tree_bytes))
    assert current_trees['']['sha']==root_sha
    for directory,t in current_trees.items():
        assert not t.get('truncated',False);add_tree(t['tree'],t['sha'],'3e574 complete tree '+directory)
    def lookup(path):
        directory='';expected=root_sha;parts=path.split('/');chain=[]
        for index,name in enumerate(parts):
            assert expected in pool,('Missing complete current ancestor',directory,expected,path)
            used.add(expected);chain.append({'directory':directory,'git_tree_sha1':expected})
            found=[e for e in pool[expected] if e['path']==name];assert len(found)<=1
            if not found:return {'status':'new_path','first_absent_component':'/'.join(parts[:index+1]),'ancestor_chain':chain}
            entry=found[0]
            if index==len(parts)-1:return {'status':'existing_path','git_object_sha1':entry['sha'],'mode':entry['mode'],'type':entry['type'],'ancestor_chain':chain}
            assert entry['type']=='tree';expected=entry['sha'];directory='/'.join(parts[:index+1])
        raise AssertionError('unreachable')
    queue_bytes=(WORK/'phase17-final-publication/publish'/QUEUE).read_bytes()
    assert sha(queue_bytes)=='74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
    queue_proof=lookup(QUEUE);assert queue_proof['git_object_sha1']==git(queue_bytes)
    queue_rows=[json.loads(x) for x in gzip.decompress(queue_bytes).splitlines()]
    qlangs=collections.Counter(f['language'] for x in queue_rows for f in x['fields'])
    assert len(queue_rows)==3379 and qlangs=={'hi':3285,'ur':3076}
    reviews_proof=lookup(REV.as_posix());assert reviews_proof['type']=='tree'
    old_reviews=[e for e in pool[reviews_proof['git_object_sha1']] if e['type']=='blob' and e['path'].startswith('source-review-') and e['path'].endswith('.json.gz')]
    assert len(old_reviews)==33 and QUEUE not in staged
    assert not any((REV/e['path']).as_posix() in staged for e in old_reviews)
    before_doc=(WORK/'phase17-final-publication/publish'/DOC).read_bytes()
    assert len(before_doc)==82957 and sha(before_doc)=='9746d1eb87ce8f47ae6e35d0781b675544ac8f19017a69e2177d0f8fd16a9708'
    before_doc_proof=lookup(DOC);assert before_doc_proof['git_object_sha1']==git(before_doc)
    old_heading,old_body=before_doc.split(b'\n',1)
    assert old_heading.decode()=='# Website-source queue resolution — 13 November 2026'
    prefix=(HERE/'current-status-draft.md').read_bytes();new_doc=prefix+old_body
    assert new_doc.endswith(old_body)
    add(DOC,new_doc,'Current English status with all prior body retained as history')
    add(PREFIX/'previous-status-document.md',before_doc,'Exact82957-byte f9be status document')
    add(PREFIX/'current-status-prefix.md',prefix,'Current status and exact-head limitations')
    doc_receipt={'schema':'hadith-bank-versioned-status-document-update-v1','documented_base_commit':base,'path':DOC,
        'before_bytes':len(before_doc),'before_sha256':sha(before_doc),'before_git_blob_sha1':git(before_doc),
        'after_bytes':len(new_doc),'after_sha256':sha(new_doc),'after_git_blob_sha1':git(new_doc),
        'full_previous_document_archived_path':str(PREFIX/'previous-status-document.md'),
        'complete_old_body_exact_suffix':True,'old_body_sha256':sha(old_body),'current_saved_export_source_commit':base,
        'review_projection_is_a_new_saved_export':False,'current_live_deployment_claimed':False}
    add(PREFIX/'document-update-receipt.json',enc(doc_receipt),'Document byte preservation proof')
    add(PREFIX/'staging-inputs.json',config_bytes,'Exact13 frozen package declarations')
    add(PREFIX/'assemble_publication.py',Path(__file__).read_bytes(),'Exact local publication assembler')
    proofs={path:lookup(path) for path in staged}
    existing={path for path,p in proofs.items() if p['status']=='existing_path'}
    assert existing=={DOC},('unexpected existing-path write',existing)
    assert proofs[DOC]['mode']=='100644' and proofs[DOC]['type']=='blob'
    assert all(lookup(e['path'])['status']=='new_path' for e in primary_entries)
    tree_path=str(PREFIX/'complete-used-base-ancestor-trees.json.gz')
    assert lookup(tree_path)['status']=='new_path'
    treeproof={'schema':'hadith-bank-exact-base-complete-ancestor-proof-v1','commit':base,'root_tree_sha':root_sha,
        'scope':'Complete reused trees are accepted only after linking their reconstructed Git identities from this exact3e574 root.',
        'trees':[{'git_tree_sha1':s,'entries':pool[s],'origins':origins[s]} for s in sorted(used)]}
    add(tree_path,gzip.compress(enc(treeproof),mtime=0),'Complete actual ancestor trees used by path proofs')
    validation={'schema':'hadith-bank-phase18-publication-staging-validation-v1','result':'PASS',
        'documented_base_commit':base,'base_root_tree_sha':root_sha,'only_existing_path_update':DOC,
        'path_proofs':proofs,'complete_ancestor_tree_proof_path':tree_path,
        'old33_active_review_entries_unchanged':old_reviews,'canonical_priority_queue_not_in_write_set':True,
        'canonical_priority_queue_sha256':sha(queue_bytes),'canonical_queue_fields':6361,'canonical_queue_ids':3379,
        'canonical_queue_by_language':dict(qlangs),'canonical_queue_current_tree_proof':queue_proof,
        'new_active_ledgers':[{'path':f['path'],'sha256':f['sha256']} for f in primary_entries],
        'review_cohort_occurrences':92,'review_counts':expected,'integration_report_sha256':sha(integration_bytes),
        'integration_primary_and_independent_package_hashes_checked':True,'actual_acquisition_audit_sha256':sha(acq_bytes),
        'actual_saved_progress':progress,'after_review_fixed3e574_projection':projection,'projection_is_saved_export':False,
        'all13_declared_packages_hash_checked':provenance,'source_or_candidate_mutations':0,
        'current_live_deployment_claimed':False,'github_writes':0,'source_http_requests':0,
        'publication_requirement':'Root must refresh the main reference and use a normal expected-head lease. These path proofs bind exactly3e574, preserving its new acquisition and material objects.'}
    validation_path=str(PREFIX/'staging-validation.json');assert lookup(validation_path)['status']=='new_path'
    add(validation_path,enc(validation),'Final exact package/path/status gate')
    for entry in staged.values():
        data=Path(entry['local_path']).read_bytes();assert len(data)==entry['bytes'] and sha(data)==entry['sha256'] and git(data)==entry['git_blob_sha1']
    assert {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}==set(staged)
    assert (HERE/'staging-inputs.json').read_bytes()==config_bytes
    # Re-read declared immutable packages after staging to catch a racing local amendment.
    for item in config['packages']:
        raw=(WORK/item['manifest_path']).read_bytes();assert sha(raw)==item['manifest_sha256']
        for f in json.loads(raw)['files']:
            data=Path(f['local_path']).read_bytes();assert len(data)==f['bytes'] and sha(data)==f['sha256']
    result={'schema':'hadith-bank-frozen-phase18-publication-manifest-v1','repository':'blaghtayt-alt/Hadith-Bank','branch':'main',
        'documented_base_commit':base,'base_root_tree_sha':root_sha,'source_review_pin':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633',
        'generated_at_utc':datetime.now(timezone.utc).isoformat(),'input_packages':provenance,
        'expected_overwrites':[{'path':DOC,'before_bytes':len(before_doc),'before_sha256':sha(before_doc),'before_git_blob_sha1':git(before_doc),
                                'after_sha256':sha(new_doc),'after_git_blob_sha1':git(new_doc)}],
        'files':[staged[k] for k in sorted(staged)],'total_files':len(staged),'total_bytes':sum(x['bytes'] for x in staged.values()),
        'new_repository_paths_at_documented_base':len(staged)-1,'existing_paths_changed':1,'new_active_ledgers':4,
        'existing_active_ledgers_changed':0,'canonical_priority_queue_changed':False,
        'local_validation':{'status':'PASS','path':validation_path,'sha256':staged[validation_path]['sha256'],
            'combined92_native_source_report_sha256':sha(integration_bytes),'actual_saved_state_audit_sha256':sha(acq_bytes)},
        'fresh_base_required_before_publication':True,'github_branch_updated':False,
        'new_review_projection_is_saved_export':False,'live_deployment_verified':False}
    data=enc(result);(HERE/'manifest.json').write_bytes(data)
    (HERE/'document-update.md').write_bytes(new_doc);(HERE/'document-update-receipt.json').write_bytes(enc(doc_receipt))
    print(json.dumps({'result':'PASS','manifest_sha256':sha(data),'files':len(staged),'bytes':result['total_bytes'],
        'new_paths':len(staged)-1,'overwrites':1,'document_sha256':sha(new_doc),'document_bytes':len(new_doc),
        'validation_sha256':staged[validation_path]['sha256']},indent=2))

if __name__=='__main__':main()
