#!/usr/bin/env python3
"""Prepare only exact saved originals; no semantic decision or reading credit."""
from pathlib import Path
import gzip, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PACKET=BASE/'phase23-checkpoint64f4-input-partitions/deployment-abudawud13-tirmidhi18'
SOURCE=BASE/'phase22-successor-acquisition-monitor/complete-held-evidence'
HEAD='64f4ed50ed6026855237a5d547a86dd03e73f804'
sys.path.insert(0,str(BASE/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (ROOT/'source-verification.json').exists()
mb=(PACKET/'input-delivery-manifest.json').read_bytes()
assert sha(mb)=='02823e9854d81dcd0fdd64f1358887138a2a2608eb3bd29088cc671d3f28911a'
manifest=json.loads(mb);assert manifest['source_commit']==HEAD and len(manifest['files'])==66
for f in manifest['files']:
    p=Path(f['local_path']);assert p.resolve().is_relative_to(BASE.resolve()) and p.is_file() and not p.is_symlink()
    b=p.read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
    if 'git_blob_sha1' in f:assert blob(b)==f['git_blob_sha1']
raw=(PACKET/'cohort.jsonl').read_bytes()
assert sha(raw)=='0a13beaaab0870f9e9ca031bac2d29be050e456cae18fbe139d5db02f027cd7d'
rows=[json.loads(x) for x in raw.splitlines()];assert len(rows)==31
fields=(PACKET/'full-hi-ur-reading-input-62.jsonl').read_bytes()
assert sha(fields)=='41f87a48423f60e7757e3410f57739d6484a6dd287b192509568ac4a4c559c68'
originals=[json.loads(x) for x in fields.splitlines()]
assert len(originals)==62 and sum(x['characters'] for x in originals)==28202 and sum(x['utf8_bytes'] for x in originals)==60537
ab=(SOURCE/'evidence-manifest.json').read_bytes();assert sha(ab)=='c2abcc3fb29dbada01127031b902026f785be51b225d590407d8917465a80a0c'
artifact=json.loads(ab);assert artifact['saved_head']==HEAD
state=json.loads((SOURCE/'held-state-entries.json').read_bytes());checks=[]
for row in rows:
    key=row['collection']+':'+row['number'];entry=state[key];files=[]
    assert entry['collection']==row['collection'] and entry['number']==row['number'] and entry['parsed']['path']==row['parsed_path']
    assert sha(importer.json_bytes(row['source_record']))==artifact['source_record_sha256'][key]
    expected={n:row[n] for n in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')};expected['classification']=row['intake_classification']
    for kind,desc in [('raw',row['snapshot']),('parsed',entry['parsed'])]:
        p=SOURCE/'sources'/desc['path'];assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to((SOURCE/'sources').resolve())
        b=p.read_bytes();plain=gzip.decompress(b);f=artifact['files'][desc['path']]
        assert len(b)==f['bytes']==f['stored_bytes'] and sha(b)==f['sha256']==f['stored_sha256']==desc['stored_sha256'] and blob(b)==f['git_blob_sha1']
        assert sha(plain)==desc['sha256']==f['uncompressed_sha256'] and len(plain)==f['uncompressed_bytes']
        if kind=='raw':
            assert len(plain)==desc['bytes'];actual,ref=importer.parse_record(plain,row['collection'],row['number']);assert actual==row['source_record'] and ref==row['source_reference_verbatim']
        else:assert plain==importer.json_bytes(expected)
        files.append({'kind':kind,'path':desc['path'],'bytes':len(plain),'sha256':sha(plain),'stored_bytes':len(b),'stored_sha256':sha(b),'git_blob_sha1':blob(b),'evidence_origin':f['evidence_origin']})
    checks.append({'id':'deenhindi-'+key,'source_record_sha256':sha(importer.json_bytes(row['source_record'])),'exact_html_reparse_and_reference':True,'files':files})
source_by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in rows}
for f in originals:
    r=source_by_id[f['occurrence_id']];t=r['source_record'][f['source_field']]
    assert t==f['text'] and sha(t.encode())==f['text_sha256'] and len(t)==f['characters'] and len(t.encode())==f['utf8_bytes']
    assert f['complete_own_field_read'] is False
(ROOT/'input').mkdir(exist_ok=True)
for name in ('cohort.jsonl','full-hi-ur-reading-input-62.jsonl','partition-receipt.json','source-verification.json'):
    (ROOT/'input'/name).write_bytes((PACKET/name).read_bytes())
(ROOT/'input/original-partition-delivery-manifest.json').write_bytes(mb)
proof={'schema':'hadith-bank-primary-original-source-reopen-v1','result':'PASS','source_commit':HEAD,
       'source_cohort_sha256':sha(raw),'original_reading_input_sha256':sha(fields),'source_occurrences':31,
       'source_files_reopened':62,'exact_raw_reparses':31,'source_evidence_manifest_sha256':sha(ab),
       'source_evidence_method':'Original250 bounded artifact plus exact23 saved-GitHub supplementation, already bound to the complete273-source manifest; output caps are unchanged.',
       'input_manifest_sha256':sha(mb),'all66_input_file_bindings_verified':True,
       'parser_sha256':sha(Path(importer.__file__).read_bytes()),'records':checks,
       'complete_semantic_readings_claimed':0,'decisions_created':0,'source_http_requests':0,'github_writes':0}
(ROOT/'source-verification.json').write_bytes(enc(proof))
print(json.dumps({'result':'PASS','source_verification_sha256':sha(enc(proof)),'files':62,'raw_reparses':31,'original_fields':62,'characters':28202,'utf8_bytes':60537},indent=2))
