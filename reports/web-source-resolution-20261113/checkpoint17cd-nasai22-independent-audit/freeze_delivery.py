"""Package immutable independent reading, semantic and native receipts."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parent
PREFIX='reports/web-source-resolution-20261113/checkpoint17cd-nasai22-independent-audit'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,b):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==b
    else:path.write_bytes(b)
def binding(path,relative):
    b=path.read_bytes();return {'path':relative,'local_path':str(path),'bytes':len(b),'size_bytes':len(b),
        'sha256':sha(b),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
report=json.loads((ROOT/'independent-final-audit.json').read_bytes())
assert report['status']=='PASS' and not report['required_amendments']
assert sha((ROOT/'independent-final-audit.json').read_bytes())=='5d0a472cb2a9d0ae6ff6b0ae4b85486fdb3ce93547cf5a97886f12611c57bcda'
direct=['independent-final-audit.json','field-and-source-proof-final.json.gz','audit_candidate.py',
        'verify_original_sources.py','show_candidate.py','record_blind_readings.py',
        'blind_readings_01.py','blind_readings_02.py','blind_readings_03.py','blind_readings_04.py',
        'freeze_source_first.py','freeze_semantic_review.py','freeze_delivery.py']
compressed=['independent-source-verification.json','complete-independent-source-first-readings.json',
            'independent-boundary-assessment-v1.json','input/cohort.jsonl','input/full-hi-ur-reading-input-44.jsonl','input/additional2636-source-only-input-3.jsonl']
files=[]
for name in direct:
    target=ROOT/'publish'/PREFIX/name;put(target,(ROOT/name).read_bytes());files.append(binding(target,PREFIX+'/'+name))
for name in compressed:
    target=ROOT/'publish'/PREFIX/(name+'.gz');put(target,gzip.compress((ROOT/name).read_bytes(),mtime=0));files.append(binding(target,PREFIX+'/'+name+'.gz'))
for i in range(1,5):
    name=f'source-first-batch-{i:02}.json';relative='source-first-batches/'+name+'.gz'
    target=ROOT/'publish'/PREFIX/relative;put(target,gzip.compress((ROOT/name).read_bytes(),mtime=0));files.append(binding(target,PREFIX+'/'+relative))
files.sort(key=lambda x:x['path'])
portable={'schema':'portable-independent-audit-payload-manifest-v1','source_checkpoint':report['source_checkpoint'],
          'primary_manifest_sha256':report['primary_manifest_sha256'],'primary_active_sha256':report['primary_active_sha256'],
          'files':[{k:v for k,v in x.items() if k!='local_path'} for x in files]}
target=ROOT/'publish'/PREFIX/'package-file-manifest.json';put(target,enc(portable));files.append(binding(target,PREFIX+'/package-file-manifest.json'));files.sort(key=lambda x:x['path'])
delivery={'schema':'independent-review-delivery-manifest-v1','status':'PASS','files':files,'file_count':len(files),
          'total_bytes':sum(x['bytes'] for x in files),'report_sha256':sha((ROOT/'independent-final-audit.json').read_bytes()),
          'primary_manifest_sha256':report['primary_manifest_sha256'],'primary_active_sha256':report['primary_active_sha256'],
          'complete_fields_read':47,'registered_parents':21,'resolved_source_only_parents':1,'admitted_fields':42,
          'reviewed_context_fields':5,'unread_context_fields':63,'lossless_source_partitions':110,'open_findings':[]}
b=enc(delivery);put(ROOT/'delivery-manifest.json',b)
for x in files:assert binding(Path(x['local_path']),x['path'])==x
print(json.dumps({'manifest':str(ROOT/'delivery-manifest.json'),'sha256':sha(b),'files':len(files),'bytes':delivery['total_bytes'],'status':'PASS'}))
