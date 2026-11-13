"""Prepare the exact bd4a92 packet and f9be121 published review baseline offline."""
from pathlib import Path,PurePosixPath
import collections,datetime,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
COMMIT='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
PUBLISHED='f9be12177046e372df088f96b255fd09914fad5a'
TREE='dd0f6ca52b3b93b2d89e3e8509bcc5e7eea64e57'
REVIEWS=Path('imports/web-deenhindi-20261112/reviews')
MONITOR=WORK/'phase16-successor-acquisition-monitor'
EVIDENCE=MONITOR/'held-evidence'
PARTITIONS=WORK/'phase18-checkpointbd4a-input-partitions'
READBACK=WORK/'phase17-independent-readback'
COHORT_SHA='849f800d50e8a32ff14d872717b9c5ca843231884bd07f852308e29a33bddfa5'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
ACTIVE477='source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz'
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews,unique_pairs
def sha(b):return hashlib.sha256(b).hexdigest()
def git(kind,b):return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):
    b=Path(p).read_bytes();return json.loads(gzip.decompress(b) if Path(p).suffix=='.gz' else b,object_pairs_hook=unique_pairs)
def lines(p):
    b=Path(p).read_bytes();b=gzip.decompress(b) if Path(p).suffix=='.gz' else b
    return [json.loads(l,object_pairs_hook=unique_pairs) for l in b.splitlines() if l.strip()]
def safe(p):
    p=str(p);v=PurePosixPath(p);assert p and not v.is_absolute() and '..' not in v.parts and '\\' not in p;return v
def bind(p):
    b=Path(p).read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git('blob',b)}
def identity(r):return r.get('occurrence_id',r.get('id')) or 'deenhindi-'+r['collection']+':'+str(r['number'])
def immutable(p,b):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('Frozen output differs',str(p))
    else:p.write_bytes(b)

def main():
    report_path=ROOT/'prepared-source-and-published-baseline.json';assert not report_path.exists()
    source_path=MONITOR/'next-review-cohort/held-source-records.jsonl';assert bind(source_path)['sha256']==COHORT_SHA
    rows=lines(source_path);sources={identity(r):r for r in rows};keys={k.removeprefix('deenhindi-') for k in sources}
    assert len(rows)==len(sources)==92
    assert collections.Counter(r['collection'] for r in rows)=={'bukhari':22,'muslim':27,'nasai':16,'abudawud':8,'tirmidhi':9,'ibnmajah':10}
    cohort_manifest_path=MONITOR/'next-review-cohort/evidence-manifest.json'
    assert bind(cohort_manifest_path)['sha256']=='f2df62f8e82ca86716e1c2bd44f8970be8ffad0a641d586bfc8cf9a767dc6a25'
    cohort_manifest=read(cohort_manifest_path);assert cohort_manifest['source_commit']==COMMIT
    assert cohort_manifest['source_rows']['sha256']==COHORT_SHA and cohort_manifest['count']==92
    partition_specs=[('checkpoint-bukhari22-ibnmajah1','2ba23d7cb570ad2d5c947ba9669d4e3d0bd83e9c5d7010a70790c6f8101f885d'),
        ('queue-muslim23','7bf60e95582121244b81ccaf8cd6c1094cab2b03bca1b0ec89becc505aed0b80'),
        ('root-nasai16-ibnmajah7','90b226b6a4b31c6432d5788c4e7571f3940647b12e443058ef771977e2d8ac2f'),
        ('deployment-abudawud8-tirmidhi9-muslim4-ibnmajah2','707a173526fb4a78ceef30c3b3069a5522fbd9998dbcedee8779d8a28223df5b')]
    partition_ids=set();partition_bindings=[]
    for name,expected in partition_specs:
        manifest_path=PARTITIONS/name/'input-delivery-manifest.json';assert bind(manifest_path)['sha256']==expected
        manifest=read(manifest_path);assert manifest['source_commit']==COMMIT
        for item in manifest['files']:
            b=bind(Path(item['local_path']));assert b['bytes']==item['bytes'] and b['sha256']==item['sha256'] and b['git_blob_sha1']==item['git_blob_sha1']
        p=PARTITIONS/name/'cohort.jsonl';group=lines(p);ids={identity(r) for r in group}
        assert len(group)==len(ids)==23 and not ids&partition_ids and all(r==sources[identity(r)] for r in group)
        partition_ids|=ids;partition_bindings.append({'name':name,'input_manifest':bind(manifest_path),'cohort':bind(p),'ids':sorted(ids)})
    assert partition_ids==set(sources)
    artifact_path=EVIDENCE/'evidence-manifest.json';assert bind(artifact_path)['sha256']=='72f36a11482b3f630570d2c9298e73039fe6bf2978a17083bb17a3482981302f'
    artifact=read(artifact_path);assert artifact['saved_head']==COMMIT
    for name in ['checkpoint.json','held-source-records.jsonl','held-state-entries.json']:
        expected=artifact['artifact_files'][name];b=bind(EVIDENCE/name)
        assert b['sha256']==expected['sha256'] and b['bytes']==expected['bytes']
    checkpoint=read(EVIDENCE/'checkpoint.json');entries=read(EVIDENCE/'held-state-entries.json')
    all_held={identity(r):r for r in lines(EVIDENCE/'held-source-records.jsonl')}
    old100_path=WORK/'phase15-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl'
    assert bind(old100_path)['sha256']=='4a4000d46dba9cff36695a62e7e5207af8f5183644141e8ca23b047e62434490'
    old100={identity(r):r for r in lines(old100_path)}
    assert len(old100)==100 and not set(old100)&set(sources)
    assert len(all_held)==len(entries)==checkpoint['selected_held_entries']==checkpoint['held_entries_total']==192
    assert checkpoint['saved_head']==COMMIT and checkpoint['remaining_held_queue_count']==0
    assert set(all_held)==set(sources)|set(old100)
    assert all(all_held[k]==v for k,v in sources.items()) and all(all_held[k]==v for k,v in old100.items())
    state_path=MONITOR/'saved-checkpoint/state.json';state_receipt=checkpoint['input_receipts']['imports/web-deenhindi-20261112/state.json']
    assert all(bind(state_path)[k]==state_receipt[k] for k in ('bytes','sha256','git_blob_sha1'))
    state=read(state_path);assert len(state['imported'])==16664
    prior_path=WORK/'phase13-successor-acquisition-monitor/saved-checkpoint/state.json'
    assert bind(prior_path)['sha256']=='5ce4a7ef9633cda58831c116d46f6a494703c6fa3931783d368fbd7fec62c4e1'
    prior=read(prior_path);assert len(prior['imported'])==15672 and not keys&set(prior['imported'])
    prior217=read(WORK/'phase15-successor-acquisition-monitor/held-evidence/held-state-entries.json')
    assert len(prior217)==217 and not keys&set(prior217)
    source_files=[]
    for oid,row in sources.items():
        key=oid.removeprefix('deenhindi-');entry=entries[key];assert entry==state['imported'][key]
        assert entry['collection']==row['collection'] and entry['number']==row['number'] and entry['parsed']['path']==row['parsed_path']
        assert sha(importer.json_bytes(row['source_record']))==artifact['source_record_sha256'][key]
        for kind,desc in [('raw',row['snapshot']),('parsed',entry['parsed'])]:
            relative=str(safe(desc['path']));p=EVIDENCE/'sources'/relative;assert p.is_file() and not p.is_symlink()
            b=bind(p);given=artifact['files'][relative];plain=importer.checked_bytes(EVIDENCE/'sources',desc)
            assert b['bytes']==given['bytes'] and b['sha256']==given['sha256'] and b['git_blob_sha1']==given['git_blob_sha1']
            if kind=='raw':
                obj,ref=importer.parse_record(plain,row['collection'],row['number'])
                assert obj==row['source_record'] and ref==row['source_reference_verbatim']
            else:
                parsed=json.loads(plain,object_pairs_hook=unique_pairs)
                expected={k:row[k] for k in ['schema','collection','number','source_record','source_reference_verbatim','snapshot']}
                expected['classification']=row.get('intake_classification',row['classification']);assert parsed==expected
            source_files.append({'id':oid,'kind':kind,'path':relative,**b,'plain_bytes':len(plain),'plain_sha256':sha(plain)})
    assert len(source_files)==len({r['path'] for r in source_files})==184
    progress_path=MONITOR/'saved-checkpoint/progress.json';progress_receipt=checkpoint['input_receipts']['imports/web-deenhindi-20261112/progress.json']
    assert all(bind(progress_path)[k]==progress_receipt[k] for k in ('bytes','sha256','git_blob_sha1'))
    progress=read(progress_path);assert progress['imported_count']==16664 and progress['classification_pending_count']==192
    assert progress['registered_hadith_count']==16321 and progress['non_narration_source_entries']==151

    # Reuse complete independently fetched f9be121 trees, rehash each object again.
    def api(name):return json.loads(read(READBACK/'input'/(name+'.json'))['content'])
    commit=api('published-commit');assert commit['sha']==PUBLISHED and commit['tree']['sha']==TREE
    names={'':'published-root-tree','imports':'after-tree-imports','imports/web-deenhindi-20261112':'after-tree-imports-web-deenhindi',
        REVIEWS.as_posix():'after-tree-reviews','reports':'after-tree-reports','reports/web-source-resolution-20261113':'after-tree-reports-web-source'}
    trees={};tree_receipts=[]
    for path,name in names.items():
        tree=api(name);assert tree['truncated'] is False
        rows2=tree['tree'];assert len(rows2)==len({x['path'] for x in rows2}) and all('/' not in x['path'] and '\0' not in x['path'] for x in rows2)
        ordered=sorted(rows2,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
        raw=b''.join((e['mode'].lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in ordered)
        assert git('tree',raw)==tree['sha'];trees[path]=tree
        if path:
            parent,_,leaf=path.rpartition('/');assert next(x for x in trees[parent]['tree'] if x['path']==leaf)['sha']==tree['sha']
        else:assert tree['sha']==TREE
        p=READBACK/'input'/(name+'.json');immutable(ROOT/'input/published-tree-authority'/p.name,p.read_bytes())
        tree_receipts.append({'path':path or '/','git_tree_sha1':tree['sha'],'complete_entries':len(rows2),'response':bind(p),'complete_git_object_rehashed':True})
    immutable(ROOT/'input/published-tree-authority/published-commit.json',(READBACK/'input/published-commit.json').read_bytes())
    review_entries={e['path']:e for e in trees[REVIEWS.as_posix()]['tree'] if e['type']=='blob' and e['path'].startswith('source-review')}
    assert len(review_entries)==33
    prior_repo=WORK/'phase16-checkpoint5589-independent-integration/validation/combined-reviews'
    published_root=ROOT/'validation/published-reviews';existing_ids=set();bindings=[];dependencies={}
    for name,entry in sorted(review_entries.items()):
        p=READBACK/'downloaded'/REVIEWS/name if name==ACTIVE477 else prior_repo/REVIEWS/name
        b=bind(p);assert b['git_blob_sha1']==entry['sha'] and b['bytes']==entry['size']
        if name==ACTIVE477:assert b['sha256']=='18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'
        ledger=read(p);decisions=ledger.get('records',ledger.get('decisions'));ids={identity(r) for r in decisions}
        assert len(ids)==len(decisions) and not ids&existing_ids and not ids&set(sources);existing_ids|=ids
        relative=(REVIEWS/name).as_posix();immutable(published_root/relative,p.read_bytes())
        bindings.append({'path':relative,'original_local_path':str(p),**b,'records':len(ids),'ids':sorted(ids),'exact_f9be121_git_blob_verified':True})
        if 'source_ledger_path' in ledger:
            dep=str(safe(ledger['source_ledger_path']));expected=ledger['source_ledger_sha256'];source_dep=prior_repo/dep
            assert source_dep.is_file() and bind(source_dep)['sha256']==expected,(dep,'missing exact declared source baseline')
            if dep in dependencies:assert dependencies[dep]['sha256']==expected
            dependencies[dep]={'path':dep,'original_local_path':str(source_dep),**bind(source_dep)}
            immutable(published_root/dep,source_dep.read_bytes())
    assert len(existing_ids)==3318 and set(old100)<=existing_ids and not existing_ids&set(sources)
    engine=SourceReviews(published_root,'deenhindi');assert set(engine.decisions)==existing_ids
    queue_path=READBACK/'downloaded'/QUEUE;qb=bind(queue_path)
    assert qb['sha256']=='74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
    qe=next(e for e in trees['reports/web-source-resolution-20261113']['tree'] if e['path']==Path(QUEUE).name)
    assert qe['sha']==qb['git_blob_sha1'] and qe['size']==qb['bytes']
    qrows=lines(queue_path);qlang=collections.Counter(f['language'] for r in qrows for f in r['fields'])
    assert len(qrows)==3379 and qlang=={'hi':3285,'ur':3076}
    immutable(published_root/QUEUE,queue_path.read_bytes())
    proof={'schema':'hadith-bank-checkpointbd4a-integration-preparation-v1','result':'PASS',
        'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':COMMIT,
        'published_review_baseline_commit':PUBLISHED,'source_cohort':bind(source_path),'source_cohort_count':92,
        'source_cohort_ids':sorted(sources),'collection_counts':dict(collections.Counter(r['collection'] for r in rows)),
        'partitions':partition_bindings,'all_four_partitions_disjoint_and_exact_cover':True,
        'full_saved_bd4a_state':bind(state_path),'full_saved_bd4a_imported_count':16664,
        'all92_saved_imported_descriptors_exact':True,'all92_absent_full0639_imported15672':True,
        'prior0639_state':bind(prior_path),'all92_absent_complete_prior217_held_set':True,
        'direct_absence_from_complete_intermediate5589_imported16169_proved':False,
        'intermediate_state_limit':'Complete5589 state unavailable. This audit does not infer absence from all16169 prior imported IDs; it verifies the exact saved92 packet, absence from full0639 imported15672 and prior217 held, and disjointness from all3318 published manual IDs.',
        'bounded_bd4a_held_count':192,'old100_source_rows_exact':True,'old100_cohort':bind(old100_path),
        'bounded_bd4a_artifact_manifest':bind(artifact_path),'bounded_bd4a_checkpoint':bind(EVIDENCE/'checkpoint.json'),
        'bounded_bd4a_descriptors':bind(EVIDENCE/'held-state-entries.json'),'new92_source_files_reopened':184,'new92_raw_reparses_exact':92,
        'saved_bd4a_progress':bind(progress_path),'saved_bd4a_progress_counts':{k:progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked','done']},
        'published_review_tree_ancestry':tree_receipts,'published_active_ledgers':33,'published_manual_decision_ids':3318,
        'published_ledger_bindings':bindings,'published_source_ledger_dependencies':list(dependencies.values()),
        'updated477_active_sha256':'18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c',
        'canonical_priority_queue':{'path':QUEUE,**qb,'pending_fields':6361,'occurrences':3379,'by_language':dict(qlang)},
        'new_linguistic_readings':0,'new_semantic_decisions':0,'source_requests':0,'github_writes':0,
        'current_newer_main_checkpoint_or_history_not_audited_here':True}
    immutable(ROOT/'input/source-cohort-92.jsonl',source_path.read_bytes())
    immutable(ROOT/'new92-raw-parsed-source-proof.json.gz',gzip.compress(enc({'records':source_files}),mtime=0))
    immutable(report_path,enc(proof))
    print(json.dumps({'result':'PASS','preparation':bind(report_path),'sources':92,'files':184,'raw_reparses':92,
        'published_ledgers':33,'published_ids':3318,'queue_fields':6361}))

if __name__=='__main__':main()
