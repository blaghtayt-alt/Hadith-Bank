"""Independent reopening of the saved source files only; no network operations."""
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase19-checkpoint3e574-bukhari20-review'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer

sha=lambda x:hashlib.sha256(x).hexdigest()
git=lambda x:hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def verify():
    cohort=(ROOT/'input/cohort.jsonl').read_bytes()
    reading=(ROOT/'input/full-hi-ur-reading-input-40.jsonl').read_bytes()
    proof_bytes=(PRIMARY/'input/own-source-verification.json').read_bytes()
    assert sha(reading)=='c9734b24953790cf443d7b17ade0d51c6c41acd4e05b17b35ccbd03454812742'
    assert sha(proof_bytes)=='f3cb6c855cd26c13e1ecc748f0f2a152e36f929a50e1a796ff3e0b6b472acfcc'
    proof=json.loads(proof_bytes)
    assert sha(cohort)==proof['cohort_sha256']
    assert proof['source_commit']=='3e574b9e7e4dd7cf8bc23232249004a18692c61c'
    rows=[json.loads(x) for x in cohort.splitlines()]
    assert len(rows)==20
    previous={x['id']:x for x in proof['records']}
    originals={x['collection']+':'+x['number']:x for x in rows}
    result=[]
    for key,saved in originals.items():
        oid='deenhindi-'+key
        receipt=previous[oid]
        assert sha(importer.json_bytes(saved['source_record']))==receipt['source_record_sha256']
        assert saved['source_reference_verbatim']==receipt['source_reference_verbatim']
        files=[]
        for f in receipt['files']:
            path=PRIMARY/'sources'/f['path']
            assert path.is_file() and not path.is_symlink()
            stored=path.read_bytes();plain=gzip.decompress(stored)
            assert len(stored)==f['stored_bytes'] and sha(stored)==f['stored_sha256']
            assert len(plain)==f['plain_bytes'] and sha(plain)==f['plain_sha256']
            assert git(stored)==f['git_blob_sha1']
            if f['kind']=='raw':
                body,reference=importer.parse_record(plain,saved['collection'],saved['number'])
                assert body==saved['source_record'] and reference==saved['source_reference_verbatim']
                assert saved['snapshot']['path']==f['path'] and saved['snapshot']['sha256']==sha(plain)
            else:
                assert f['kind']=='parsed' and saved['parsed_path']==f['path']
                expected={k:saved[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
                expected['classification']=saved['intake_classification']
                assert json.loads(plain)==expected
            files.append(dict(f,independently_reopened_and_all_hashes_verified=True))
        result.append({'occurrence_id':oid,'source_record_sha256':receipt['source_record_sha256'],
            'source_reference_verbatim':saved['source_reference_verbatim'],'files':files,
            'complete_current_raw_reparse_equal':True,'complete_original_parsed_object_equal':True})
    for x in [json.loads(x) for x in reading.splitlines()]:
        saved=originals[x['collection']+':'+x['number']]
        assert x['text']==saved['source_record'][x['source_field']]
        assert sha(x['text'].encode())==x['text_sha256']
        assert x['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
    assert len(result)==20 and sum(len(x['files']) for x in result)==40
    return {'schema':'hadith-bank-independent-original-source-verification-v1','result':'PASS',
        'source_commit':proof['source_commit'],'cohort_sha256':sha(cohort),
        'source_input_sha256':sha(reading),'pinned_primary_original_source_proof_sha256':sha(proof_bytes),
        'source_files_reopened':40,'complete_raw_reparses':20,'complete_original_objects_checked':20,
        'full_own_field_inputs_bound':40,'records':result,'source_http_requests':0,'github_writes':0,
        'parser_sha256':sha(Path(importer.__file__).read_bytes()),
        'new_semantic_readings_claimed_by_verifier':0}

if __name__=='__main__':
    report=verify();data=enc(report);target=ROOT/'independent-source-verification.json'
    if target.exists():assert target.read_bytes()==data
    else:target.write_bytes(data)
    print(json.dumps({'result':report['result'],'sha256':sha(data),'bytes':len(data),
        'files':40,'complete_raw_reparses':20}))
