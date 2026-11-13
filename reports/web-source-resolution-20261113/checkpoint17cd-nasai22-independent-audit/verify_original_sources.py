"""Reopen original source-only preparation without inspecting any primary candidate."""
from pathlib import Path
import gzip,hashlib,json,sys
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
PREP=WORK/'phase22-checkpoint17cd-input-partitions/root-nasai22'
EVIDENCE=WORK/'phase21-successor-acquisition-monitor/held-evidence'
sys.dont_write_bytecode=True;sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b
    else:p.write_bytes(b)
def verify():
    raw=(PREP/'input-delivery-manifest.json').read_bytes();assert sha(raw)=='3919913d9490dc25d87910b04b50a18b211320d04cbb7a5d16e6c5b27a3a4c3c'
    m=json.loads(raw);assert len(m['files'])==48 and m['source_commit']=='17cd396eb858a29162505d545aad556ac73ce9ce'
    for f in m['files']:
        p=Path(f['local_path']);assert p.is_file() and not p.is_symlink();b=p.read_bytes()
        assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
    for name in ['input-delivery-manifest.json','cohort.jsonl','full-hi-ur-reading-input-44.jsonl','source-verification.json']:
        put(HERE/'input'/name,(PREP/name).read_bytes())
    cohort=(HERE/'input/cohort.jsonl').read_bytes();reading=(HERE/'input/full-hi-ur-reading-input-44.jsonl').read_bytes()
    assert sha(cohort)=='e606722e94cffde01f011c34bd9cd7dbe53003b8522a1d4f24c8545223f78f17'
    assert sha(reading)=='b60efedb67ec47bfcd7950d5760858bcc2e591a3f4c2150c889894d75052422c'
    extra=(WORK/'phase22-checkpoint17cd-nasai22-review/additional2636-source-only-input-3.jsonl').read_bytes()
    assert sha(extra)=='c7b238656dafcb4aa9f211974942df0da78ddcf8320082dca253a7eb987345f6'
    put(HERE/'input/additional2636-source-only-input-3.jsonl',extra)
    records=list(map(json.loads,cohort.splitlines()));fields=list(map(json.loads,reading.splitlines()+extra.splitlines()))
    entries=json.loads((EVIDENCE/'held-state-entries.json').read_bytes())
    authority=json.loads((EVIDENCE/'evidence-manifest.json').read_bytes());assert authority['saved_head']==m['source_commit']
    proofs=[]
    for r in records:
        key=r['collection']+':'+r['number'];entry=entries[key]
        assert entry['parsed']['path']==r['parsed_path']
        raw=importer.checked_bytes(EVIDENCE/'sources',r['snapshot']);parsed=json.loads(importer.checked_bytes(EVIDENCE/'sources',entry['parsed']))
        for k in ['collection','number','source_record','source_reference_verbatim','snapshot']:assert parsed[k]==r[k]
        source,ref=importer.parse_record(raw,r['collection'],r['number'])
        assert source==r['source_record'] and ref==r['source_reference_verbatim']
        files=[]
        for descriptor in [r['snapshot'],entry['parsed']]:
            p=EVIDENCE/'sources'/descriptor['path'];b=p.read_bytes();a=authority['files'][descriptor['path']]
            assert sha(b)==a['sha256'] and git(b)==a['git_blob_sha1']
            put(HERE/'sources'/descriptor['path'],b)
            files.append({'path':descriptor['path'],'bytes':len(b),'stored_sha256':sha(b),'git_blob_sha1':git(b),
                'decompressed_sha256':sha(gzip.decompress(b)),'descriptor':descriptor})
        proofs.append({'id':'deenhindi-'+key,'source_record_sha256':sha(importer.json_bytes(source)),
            'source_reference_verbatim':ref,'files':files,'full_source_reparse_exact':True})
    by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in records}
    assert len(by_id)==22 and len(fields)==47
    for f in fields:
        r=by_id[f['occurrence_id']];t=r['source_record'][f['source_field']]
        assert f['text']==t and f['text_sha256']==sha(t.encode())
        if 'source_record_sha256' in f:assert f['source_record_sha256']==sha(importer.json_bytes(r['source_record']))
        assert f['characters']==len(t) and f['utf8_bytes']==len(t.encode()) and t
    return {'schema':'hadith-bank-independent-source-only-preparation-proof-v1','result':'PASS',
        'source_commit':m['source_commit'],'input_manifest_sha256':sha((PREP/'input-delivery-manifest.json').read_bytes()),
        'cohort_sha256':sha(cohort),'original_reading_input_sha256':sha(reading),'additional_original_input_sha256':sha(extra),'occurrences':22,
        'raw_and_parsed_files_reopened':44,'complete_raw_reparses':22,'reading_input_fields_bound':47,
        'characters_in_reading_input':sum(f['characters'] for f in fields),'utf8_bytes_in_reading_input':sum(f['utf8_bytes'] for f in fields),
        'semantic_readings_claimed_by_this_verifier':0,'primary_candidate_or_semantic_notes_opened':False,
        'source_http_requests':0,'github_writes':0,'rows':proofs}
if __name__=='__main__':
    report=verify();b=enc(report);put(HERE/'independent-source-verification.json',b)
    print(json.dumps({'status':'PASS','sha256':sha(b),'files':44,'reparses':22,'fields':47}))
