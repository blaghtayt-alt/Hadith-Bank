"""Independently reopen pinned saved bytes; never request the source website."""
import base64
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PRIMARY=HERE.parent/'phase20-original-bukhari25-hi-ur'
sys.path.insert(0,str(HERE.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def verify():
    raw=(HERE/'input/source-25.jsonl').read_bytes()
    reading=(HERE/'input/full-hi-ur-reading-input-50.jsonl').read_bytes()
    assert sha(raw)=='c9ba0fcc71f74b4f72714894936798b48ff7bf5cfb0d2513ddf32c7eaa65b229'
    assert sha(reading)=='5c204cde7e73d4195281c8681455016a4ddb635e847c28564cc84ab352b26a1c'
    proofraw=(PRIMARY/'input/source-verification.json').read_bytes()
    assert sha(proofraw)=='864a0dcbf04fa261dcd5037590b5800e42d52a71cefe6ac45d1dae4cc93f336e'
    proof=json.loads(proofraw);pin='d369026ca42af6ff972ffab83c9180e03759da41'
    assert proof['source_commit']==pin
    responses={}
    for p in sorted((PRIMARY/'input/github-sources').glob('file-*.json')):
        rb=p.read_bytes();r=json.loads(rb)
        assert r['encoding']=='base64' and r['requested_ref']==pin
        stored=base64.b64decode(r['content'],validate=False)
        assert git(stored)==r['sha']
        assert r['requested_path'] not in responses
        responses[r['requested_path']]=(stored,r,sha(rb))
    assert len(responses)==50
    rows=list(map(json.loads,raw.splitlines()))
    by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in rows}
    previous={r['id']:r for r in proof['records']}
    assert len(by_id)==25 and set(by_id)==set(previous)
    receipts=[]
    for oid,saved in by_id.items():
        rec=previous[oid];assert rec['source_snapshot']==saved['snapshot']
        assert rec['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
        assert rec['source_reference_verbatim']==saved['source_reference_verbatim']
        files=[]
        for f in rec['files']:
            p=PRIMARY/'source-evidence'/f['path']
            assert p.is_file() and not p.is_symlink()
            stored=p.read_bytes();plain=gzip.decompress(stored)
            response,meta,response_sha=responses[f['path']]
            assert stored==response and response_sha==f['response_json_sha256']
            assert len(stored)==f['bytes'] and sha(stored)==f['sha256']
            assert git(stored)==f['git_blob_sha1']==f['github_blob_sha1']==meta['sha']
            assert len(plain)==f['plain_bytes'] and sha(plain)==f['plain_sha256']
            if f['path']==saved['snapshot']['path']:
                desc=saved['snapshot'];kind='raw'
                body,reference=importer.parse_record(plain,saved['collection'],saved['number'])
                assert body==saved['source_record'] and reference==saved['source_reference_verbatim']
                assert desc['bytes']==len(plain) and desc['stored_bytes']==len(stored)
            else:
                assert f['path']==saved['parsed_path']==rec['parsed_descriptor']['path']
                desc=rec['parsed_descriptor'];kind='parsed'
                expected={k:saved[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
                expected['classification']=saved['intake_classification']
                assert json.loads(plain)==expected
            assert desc['sha256']==sha(plain) and desc['stored_sha256']==sha(stored)
            files.append(dict(f,kind=kind,independently_reopened=True,exact_github_body_verified=True))
        assert len(files)==2
        receipts.append({'occurrence_id':oid,'source_record_sha256':rec['source_record_sha256'],
            'source_reference_verbatim':saved['source_reference_verbatim'],'files':files,
            'complete_raw_reparse_equal':True,'complete_original_parsed_object_equal':True})
    fieldrows=list(map(json.loads,reading.splitlines()));assert len(fieldrows)==50
    for r in fieldrows:
        original=by_id[r['occurrence_id']]['source_record'][r['source_field']]
        assert original==r['text'] and sha(original.encode())==r['text_sha256']
        assert r['source_record_sha256']==sha(importer.json_bytes(by_id[r['occurrence_id']]['source_record']))
    manifest_raw=(PRIMARY/'source-input-delivery-manifest.json').read_bytes()
    assert sha(manifest_raw)=='1580d6caa2109437c1143d5d08019b9839c6f12e03d0cd2041a46ea192375962'
    manifest=json.loads(manifest_raw)
    for f in manifest['files']:
        data=Path(f['local_path']).read_bytes()
        assert sha(data)==f['sha256'] and len(data)==f['bytes'] and git(data)==f['git_blob_sha1']
    return {'schema':'hadith-bank-independent-original-source-verification-v1','result':'PASS',
        'source_commit':pin,'source_baseline25_sha256':sha(raw),'source_input_sha256':sha(reading),
        'pinned_primary_original_source_proof_sha256':sha(proofraw),
        'source_input_manifest_sha256':sha(manifest_raw),'source_input_manifest_files_rehashed':len(manifest['files']),
        'source_files_independently_reopened':50,'complete_raw_reparses':25,
        'complete_original_parsed_objects_checked':25,'github_response_bodies_verified':50,
        'full_original_field_inputs_bound':50,'records':receipts,
        'parser_sha256':sha(Path(importer.__file__).read_bytes()),
        'source_http_requests':0,'github_writes':0,'new_linguistic_reading_credit_from_this_verifier':0}

if __name__=='__main__':
    report=verify();data=importer.json_bytes(report);target=HERE/'independent-source-verification.json'
    if target.exists():assert target.read_bytes()==data
    else:target.write_bytes(data)
    print(json.dumps({'result':report['result'],'bytes':len(data),'sha256':sha(data),'source_files':50,'raw_reparses':25}))
