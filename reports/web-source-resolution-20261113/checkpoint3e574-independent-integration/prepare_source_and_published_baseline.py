"""Prepare exact phase19 source evidence; publication binding is a separate gate."""
from pathlib import Path,PurePosixPath
import collections,datetime,gzip,hashlib,json,sys

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
COMMIT='3e574b9e7e4dd7cf8bc23232249004a18692c61c'
REVIEWS=Path('imports/web-deenhindi-20261112/reviews')
MONITOR=WORK/'phase18-successor-acquisition-monitor'
EVIDENCE=MONITOR/'held-evidence'
PARTITIONS=WORK/'phase19-checkpoint3e574-input-partitions'
COHORT_SHA='e34d421b335ffedcac3a6b179e9c2e773f5f753bedf85203f1d949e76723e15a'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews,unique_pairs

def sha(b):return hashlib.sha256(b).hexdigest()
def git(kind,b):return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):
    p=Path(p);b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b,object_pairs_hook=unique_pairs)
def lines(p):
    p=Path(p);b=p.read_bytes();b=gzip.decompress(b) if p.suffix=='.gz' else b
    return [json.loads(l,object_pairs_hook=unique_pairs) for l in b.splitlines() if l.strip()]
def safe(p):
    p=str(p);v=PurePosixPath(p)
    assert p and not v.is_absolute() and '..' not in v.parts and '\\' not in p
    return v
def bind(p):
    b=Path(p).read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git('blob',b)}
def identity(r):return r.get('occurrence_id',r.get('id')) or 'deenhindi-'+r['collection']+':'+str(r['number'])
def immutable(p,b):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('Frozen output differs',str(p))
    else:p.write_bytes(b)


def prepare_source():
    report_path=ROOT/'prepared-source-cohort.json';assert not report_path.exists()
    source_path=MONITOR/'next-review-cohort/held-source-records.jsonl'
    assert bind(source_path)['sha256']==COHORT_SHA
    rows=lines(source_path);sources={identity(r):r for r in rows};keys={i.removeprefix('deenhindi-') for i in sources}
    assert len(rows)==len(sources)==80
    assert collections.Counter(r['collection'] for r in rows)=={'bukhari':22,'muslim':20,'nasai':13,'abudawud':4,'tirmidhi':11,'ibnmajah':10}
    input_path=MONITOR/'next-review-cohort/input-manifest.json'
    assert bind(input_path)['sha256']=='9312f560d802669c39721159c0471f447da09f559b647fa85922a885992109fd'
    partition_specs=[
        ('checkpoint-bukhari20','4e33b5dfb74bec315bd3e5aa77e44bde5111f32f75130a929003b23a30ef0e2f'),
        ('queue-muslim20','0165ca3467cca53119ecfd8b29652f24173a04a7798fec3b9af0f6228ee083a1'),
        ('root-nasai13-ibnmajah7','5c24dda1e14ebad6f34d847cf11dda123e04c4e700837e9a32cfeffc18f69fd4'),
        ('deployment-abudawud4-tirmidhi11-bukhari2-ibnmajah3','5d75ec689614acb7ffcdf803c745b49aecb9ccf7a35b41552cd77d76d5ff26d4')]
    partition_ids=set();partition_bindings=[]
    for name,expected in partition_specs:
        manifest_path=PARTITIONS/name/'input-delivery-manifest.json'
        assert bind(manifest_path)['sha256']==expected
        manifest=read(manifest_path);assert manifest['source_commit']==COMMIT
        for item in manifest['files']:
            path=Path(item['local_path']);assert path.is_file() and not path.is_symlink()
            b=bind(path);assert all(b[k]==item[k] for k in ['bytes','sha256','git_blob_sha1'])
        path=PARTITIONS/name/'cohort.jsonl';group=lines(path);ids={identity(r) for r in group}
        assert len(group)==len(ids)==20 and not ids&partition_ids
        assert all(r==sources[identity(r)] for r in group)
        partition_ids|=ids
        partition_bindings.append({'name':name,'input_manifest':bind(manifest_path),'cohort':bind(path),'ids':sorted(ids)})
    assert partition_ids==set(sources)
    artifact_path=EVIDENCE/'evidence-manifest.json'
    assert bind(artifact_path)['sha256']=='1f30cc019a2b06e2a947a8e429cc77a60f1152fa685a8a819788da362baca004'
    artifact=read(artifact_path);assert artifact['saved_head']==COMMIT
    for name in ['checkpoint.json','held-source-records.jsonl','held-state-entries.json']:
        expected=artifact['artifact_files'][name];b=bind(EVIDENCE/name)
        assert b['sha256']==expected['sha256'] and b['bytes']==expected['bytes']
    checkpoint=read(EVIDENCE/'checkpoint.json');entries=read(EVIDENCE/'held-state-entries.json')
    all_held={identity(r):r for r in lines(EVIDENCE/'held-source-records.jsonl')}
    old_path=WORK/'phase16-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl'
    assert bind(old_path)['sha256']=='849f800d50e8a32ff14d872717b9c5ca843231884bd07f852308e29a33bddfa5'
    old92={identity(r):r for r in lines(old_path)}
    assert len(old92)==92 and not set(old92)&set(sources)
    assert len(all_held)==len(entries)==checkpoint['selected_held_entries']==checkpoint['held_entries_total']==172
    assert checkpoint['saved_head']==COMMIT and checkpoint['remaining_held_queue_count']==0
    assert set(all_held)==set(sources)|set(old92)
    assert all(all_held[k]==v for k,v in sources.items()) and all(all_held[k]==v for k,v in old92.items())
    state_path=MONITOR/'saved-checkpoint/state.json';state_receipt=checkpoint['input_receipts']['imports/web-deenhindi-20261112/state.json']
    assert all(bind(state_path)[k]==state_receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    state=read(state_path);assert len(state['imported'])==17131
    prior_path=WORK/'phase16-successor-acquisition-monitor/saved-checkpoint/state.json'
    prior_checkpoint=read(WORK/'phase16-successor-acquisition-monitor/held-evidence/checkpoint.json')
    assert prior_checkpoint['saved_head']=='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
    receipt=prior_checkpoint['input_receipts']['imports/web-deenhindi-20261112/state.json']
    assert all(bind(prior_path)[k]==receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    prior=read(prior_path)
    assert len(prior['imported'])==16664 and not keys&set(prior['imported'])
    source_files=[]
    for oid,row in sources.items():
        key=oid.removeprefix('deenhindi-');entry=entries[key]
        assert entry==state['imported'][key]
        assert entry['collection']==row['collection'] and entry['number']==row['number'] and entry['parsed']['path']==row['parsed_path']
        assert sha(importer.json_bytes(row['source_record']))==artifact['source_record_sha256'][key]
        for kind,desc in [('raw',row['snapshot']),('parsed',entry['parsed'])]:
            relative=str(safe(desc['path']));path=EVIDENCE/'sources'/relative
            assert path.is_file() and not path.is_symlink()
            b=bind(path);given=artifact['files'][relative]
            assert all(b[k]==given[k] for k in ['bytes','sha256','git_blob_sha1'])
            plain=importer.checked_bytes(EVIDENCE/'sources',desc)
            if kind=='raw':
                obj,ref=importer.parse_record(plain,row['collection'],row['number'])
                assert obj==row['source_record'] and ref==row['source_reference_verbatim']
            else:
                parsed=json.loads(plain,object_pairs_hook=unique_pairs)
                expected={k:row[k] for k in ['schema','collection','number','source_record','source_reference_verbatim','snapshot']}
                expected['classification']=row.get('intake_classification',row['classification'])
                assert parsed==expected
            source_files.append({'id':oid,'kind':kind,'path':relative,**b,'plain_bytes':len(plain),'plain_sha256':sha(plain)})
    assert len(source_files)==len({r['path'] for r in source_files})==160
    progress_path=MONITOR/'saved-checkpoint/progress.json';progress_receipt=checkpoint['input_receipts']['imports/web-deenhindi-20261112/progress.json']
    assert all(bind(progress_path)[k]==progress_receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    progress=read(progress_path)
    assert (progress['imported_count'],progress['registered_hadith_count'],progress['non_narration_source_entries'],progress['classification_pending_count'])==(17131,16804,155,172)
    proof={'schema':'hadith-bank-checkpoint3e574-source-integration-preparation-v1','result':'SOURCE_PROVENANCE_PASS',
        'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':COMMIT,
        'source_cohort':bind(source_path),'source_cohort_count':80,'source_cohort_ids':sorted(sources),
        'collection_counts':dict(collections.Counter(r['collection'] for r in rows)),
        'partitions':partition_bindings,'all_four_partitions_disjoint_and_exact_cover':True,
        'full_saved_3e574_state':bind(state_path),'full_saved_3e574_imported_count':17131,
        'all80_saved_imported_descriptors_exact':True,'all80_absent_from_all16664_prior_imported_ids':True,
        'prior_bd4a_state':bind(prior_path),'bounded_3e574_held_count':172,'old92_source_rows_exact':True,
        'old92_cohort':bind(old_path),'bounded_artifact_manifest':bind(artifact_path),
        'bounded_checkpoint':bind(EVIDENCE/'checkpoint.json'),'bounded_descriptors':bind(EVIDENCE/'held-state-entries.json'),
        'new80_source_files_reopened':160,'new80_raw_reparses_exact':80,
        'saved_3e574_progress':bind(progress_path),'saved_3e574_progress_counts':{k:progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked','done']},
        'published_review_baseline_checked_here':False,'final_primary_and_independent_gates_checked_here':False,
        'new_linguistic_readings':0,'new_semantic_decisions':0,'source_requests':0,'github_writes':0,
        'full_acquisition_history_audit_scope':'Not repeated here; this integration verifies full saved-state byte identity, the80 descriptors and absence from the complete prior imported set. The separate acquisition audit covers histories and controls.'}
    immutable(ROOT/'input/source-cohort-80.jsonl',source_path.read_bytes())
    immutable(ROOT/'new80-raw-parsed-source-proof.json.gz',gzip.compress(enc({'records':source_files}),mtime=0))
    immutable(report_path,enc(proof))
    print(json.dumps({'result':proof['result'],'preparation':bind(report_path),'sources':80,'files':160,'raw_reparses':80,'prior_imported_ids_checked':16664}))


if __name__=='__main__':prepare_source()
