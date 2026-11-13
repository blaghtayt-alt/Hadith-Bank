"""Prepare exact phase21 source evidence; publication binding is a separate gate."""
from pathlib import Path,PurePosixPath
import collections,datetime,gzip,hashlib,json,sys

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
COMMIT='0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a'
REVIEWS=Path('imports/web-deenhindi-20261112/reviews')
MONITOR=WORK/'phase19-successor-acquisition-monitor'
EVIDENCE=MONITOR/'held-evidence'
PARTITIONS=WORK/'phase21-checkpoint0d2fa-input-partitions'
COHORT_SHA='bcc56c4f5d441a0117bff7ff1ba42889d249f51b9f4cf23800f327358b5b8559'
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
    assert len(rows)==len(sources)==86
    assert collections.Counter(r['collection'] for r in rows)=={'bukhari':30,'muslim':22,'nasai':6,'abudawud':12,'tirmidhi':6,'ibnmajah':10}
    input_path=MONITOR/'next-review-cohort/input-manifest.json'
    assert bind(input_path)['sha256']=='00d9bbd315aec5305d553451bab51fe19b8ee7ed061e0f7bd07f48c5b7922716'
    partition_specs=[
        ('checkpoint-bukhari30','9481c8813dea9d9ebaf6cf0b2c28d44cceae87aca0b531bf9813695c5550be0b',30),
        ('queue-muslim22','dec1e207adca8876ecf9b0781e5ce1be13d7f5b506f8c41dd00e3502972f496d',22),
        ('root-nasai6-ibnmajah10','d7cb3846d0908603bc268134d5e533733163470b43ec9d7806adcd3846132507',16),
        ('deployment-abudawud12-tirmidhi6','d55469c5da40c1ffed35bcf4765d380bb842491f3ba69bc639dde7af2293ae64',18)]
    partition_ids=set();partition_bindings=[]
    for name,expected,count in partition_specs:
        manifest_path=PARTITIONS/name/'input-delivery-manifest.json'
        assert bind(manifest_path)['sha256']==expected
        manifest=read(manifest_path);assert manifest['source_commit']==COMMIT
        for item in manifest['files']:
            path=Path(item['local_path']);assert path.is_file() and not path.is_symlink()
            b=bind(path);assert all(b[k]==item[k] for k in ['bytes','sha256','git_blob_sha1'])
        path=PARTITIONS/name/'cohort.jsonl';group=lines(path);ids={identity(r) for r in group}
        assert len(group)==len(ids)==count and not ids&partition_ids
        assert all(r==sources[identity(r)] for r in group)
        partition_ids|=ids
        partition_bindings.append({'name':name,'input_manifest':bind(manifest_path),'cohort':bind(path),'ids':sorted(ids)})
    assert partition_ids==set(sources)
    artifact_path=EVIDENCE/'evidence-manifest.json'
    assert bind(artifact_path)['sha256']=='a7bbcf2bbf0004feace3b31966cc11bed9d3ab0cb6608671d2c09d5c635a91b1'
    artifact=read(artifact_path);assert artifact['saved_head']==COMMIT
    for name in ['checkpoint.json','held-source-records.jsonl','held-state-entries.json']:
        expected=artifact['artifact_files'][name];b=bind(EVIDENCE/name)
        assert b['sha256']==expected['sha256'] and b['bytes']==expected['bytes']
    checkpoint=read(EVIDENCE/'checkpoint.json');entries=read(EVIDENCE/'held-state-entries.json')
    all_held={identity(r):r for r in lines(EVIDENCE/'held-source-records.jsonl')}
    old_path=WORK/'phase18-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl'
    assert bind(old_path)['sha256']=='e34d421b335ffedcac3a6b179e9c2e773f5f753bedf85203f1d949e76723e15a'
    old80={identity(r):r for r in lines(old_path)}
    assert len(old80)==80 and not set(old80)&set(sources)
    assert len(all_held)==len(entries)==checkpoint['selected_held_entries']==checkpoint['held_entries_total']==166
    assert checkpoint['saved_head']==COMMIT and checkpoint['remaining_held_queue_count']==0
    assert set(all_held)==set(sources)|set(old80)
    assert all(all_held[k]==v for k,v in sources.items()) and all(all_held[k]==v for k,v in old80.items())
    state_path=MONITOR/'saved-checkpoint/state.json';state_receipt=checkpoint['input_receipts']['imports/web-deenhindi-20261112/state.json']
    assert all(bind(state_path)[k]==state_receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    state=read(state_path);assert len(state['imported'])==17627
    prior_path=WORK/'phase18-successor-acquisition-monitor/saved-checkpoint/state.json'
    prior_checkpoint=read(WORK/'phase18-successor-acquisition-monitor/held-evidence/checkpoint.json')
    assert prior_checkpoint['saved_head']=='3e574b9e7e4dd7cf8bc23232249004a18692c61c'
    receipt=prior_checkpoint['input_receipts']['imports/web-deenhindi-20261112/state.json']
    assert all(bind(prior_path)[k]==receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    prior=read(prior_path)
    assert len(prior['imported'])==17131 and not keys&set(prior['imported'])
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
    assert len(source_files)==len({r['path'] for r in source_files})==172
    progress_path=MONITOR/'saved-checkpoint/progress.json';progress_receipt=checkpoint['input_receipts']['imports/web-deenhindi-20261112/progress.json']
    assert all(bind(progress_path)[k]==progress_receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    progress=read(progress_path)
    assert (progress['imported_count'],progress['registered_hadith_count'],progress['non_narration_source_entries'],progress['classification_pending_count'])==(17627,17301,160,166)
    proof={'schema':'hadith-bank-checkpoint0d2fa-source-integration-preparation-v1','result':'SOURCE_PROVENANCE_PASS',
        'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':COMMIT,
        'source_cohort':bind(source_path),'source_cohort_count':86,'source_cohort_ids':sorted(sources),
        'collection_counts':dict(collections.Counter(r['collection'] for r in rows)),
        'partitions':partition_bindings,'all_four_partitions_disjoint_and_exact_cover':True,
        'full_saved_0d2fa_state':bind(state_path),'full_saved_0d2fa_imported_count':17627,
        'all86_saved_imported_descriptors_exact':True,'all86_absent_from_all17131_prior_imported_ids':True,
        'prior_3e574_state':bind(prior_path),'bounded_0d2fa_held_count':166,'old80_source_rows_exact':True,
        'old80_cohort':bind(old_path),'bounded_artifact_manifest':bind(artifact_path),
        'bounded_checkpoint':bind(EVIDENCE/'checkpoint.json'),'bounded_descriptors':bind(EVIDENCE/'held-state-entries.json'),
        'new86_source_files_reopened':172,'new86_raw_reparses_exact':86,
        'saved_0d2fa_progress':bind(progress_path),'saved_0d2fa_progress_counts':{k:progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked','done']},
        'published_review_baseline_checked_here':False,'final_primary_and_independent_gates_checked_here':False,
        'new_linguistic_readings':0,'new_semantic_decisions':0,'source_requests':0,'github_writes':0,
        'full_acquisition_history_audit_scope':'Not repeated here; this integration verifies full saved-state byte identity, the86 descriptors and absence from the complete prior imported set. The separate acquisition audit covers histories and controls.'}
    immutable(ROOT/'input/source-cohort-86.jsonl',source_path.read_bytes())
    immutable(ROOT/'new86-raw-parsed-source-proof.json.gz',gzip.compress(enc({'records':source_files}),mtime=0))
    immutable(report_path,enc(proof))
    print(json.dumps({'result':proof['result'],'preparation':bind(report_path),'sources':86,'files':172,'raw_reparses':86,'prior_imported_ids_checked':17131}))


if __name__=='__main__':prepare_source()
