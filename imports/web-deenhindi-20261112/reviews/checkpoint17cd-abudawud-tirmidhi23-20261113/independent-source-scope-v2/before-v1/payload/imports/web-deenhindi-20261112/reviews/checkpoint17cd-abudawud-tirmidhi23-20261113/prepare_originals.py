#!/usr/bin/env python3
"""Copy and verify only assigned immutable originals, before semantic review."""
import gzip,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PACKET=ROOT.parent/'phase22-checkpoint17cd-input-partitions/deployment-abudawud17-tirmidhi6'
MON=ROOT.parent/'phase21-successor-acquisition-monitor/held-evidence'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def main():
    assert not (ROOT/'source-verification.json').exists()
    mb=(PACKET/'input-delivery-manifest.json').read_bytes()
    assert sha(mb)=='732377ec4c1dea995f9a2c24312ee3b6440d064118f5b2d4d024b028f0ec4f91'
    manifest=json.loads(mb);assert manifest['source_commit']=='17cd396eb858a29162505d545aad556ac73ce9ce'
    copied=[]
    for f in manifest['files']:
        p=Path(f['local_path']);b=p.read_bytes()
        assert len(b)==f['bytes'] and sha(b)==f['sha256'] and blob(b)==f['git_blob_sha1']
        target=ROOT/f['path'] if f['path'].startswith('sources/') else ROOT/'input'/f['path']
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
        copied.append({'path':str(target.relative_to(ROOT)),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)})
    (ROOT/'input/original-partition-delivery-manifest.json').write_bytes(mb)
    rows=[json.loads(x) for x in (ROOT/'input/cohort.jsonl').read_bytes().splitlines()]
    fields=[json.loads(x) for x in (ROOT/'input/full-hi-ur-reading-input-46.jsonl').read_bytes().splitlines()]
    assert len(rows)==23 and len(fields)==46
    assert sum(f['characters'] for f in fields)==24000 and sum(f['utf8_bytes'] for f in fields)==51211
    artifact=json.loads((MON/'evidence-manifest.json').read_bytes());state=json.loads((MON/'held-state-entries.json').read_bytes())
    proofs=[]
    for row in rows:
        key=row['collection']+':'+row['number'];entry=state[key]
        assert sha(importer.json_bytes(row['source_record']))==artifact['source_record_sha256'][key]
        descs=[('raw',row['snapshot']),('parsed',entry['parsed'])];files=[]
        for kind,desc in descs:
            b=(ROOT/'sources'/desc['path']).read_bytes();plain=gzip.decompress(b);a=artifact['files'][desc['path']]
            assert sha(b)==desc['stored_sha256']==a['stored_sha256'] and blob(b)==a['git_blob_sha1']
            assert sha(plain)==desc['sha256'] and len(b)==a['bytes']
            if kind=='raw':
                obj,ref=importer.parse_record(plain,row['collection'],row['number'])
                assert obj==row['source_record'] and ref==row['source_reference_verbatim'] and len(plain)==desc['bytes']
            else:
                expected={k:row[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
                expected['classification']=row['intake_classification'];assert plain==importer.json_bytes(expected)
            files.append({'kind':kind,'path':desc['path'],'stored_bytes':len(b),'stored_sha256':sha(b),'git_blob_sha1':blob(b),'plain_bytes':len(plain),'plain_sha256':sha(plain)})
        proofs.append({'id':'deenhindi-'+key,'source_record_sha256':sha(importer.json_bytes(row['source_record'])),'exact_raw_reparse':True,'files':files})
    for f in fields:
        assert sha(f['text'].encode())==f['text_sha256'] and len(f['text'])==f['characters'] and len(f['text'].encode())==f['utf8_bytes']
        assert f['complete_own_field_read'] is False
    report={'schema':'hadith-bank-original-only-packet-source-verification-v1','result':'PASS','source_commit':manifest['source_commit'],'input_manifest_sha256':sha(mb),'source_records':23,'source_files_reopened':46,'exact_html_reparses':23,'priority_original_fields':46,'priority_characters':24000,'priority_utf8_bytes':51211,'semantic_readings_claimed':0,'candidate_created':False,'source_http_requests':0,'github_writes':0,'importer_sha256':sha(Path(importer.__file__).read_bytes()),'copied_files':copied,'records':proofs}
    rb=enc(report);(ROOT/'source-verification.json').write_bytes(rb)
    print(json.dumps({'status':'PASS','source_verification_sha256':sha(rb),'source_files':46,'reparses':23,'original_fields':46,'characters':24000,'utf8_bytes':51211,'semantic_readings_claimed':0}))

if __name__=='__main__':main()
