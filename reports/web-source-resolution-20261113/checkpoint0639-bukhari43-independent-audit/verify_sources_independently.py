"""Reopen and reparse all43 source pairs, independently of primary validation output."""
from pathlib import Path
import gzip, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase15-checkpoint0639-bukhari43-review'
SHARED=ROOT.parent/'phase13-successor-acquisition-monitor/held-evidence'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda data:hashlib.sha256(data).hexdigest()
blob=lambda data:hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

source_bytes=(PRIMARY/'input/cohort.jsonl').read_bytes()
assert sha(source_bytes)=='ba26eacd5ab7b93a329d98e0df60626f158800815ffd39224d345e2d61ee1f5e'
rows=[json.loads(line) for line in source_bytes.splitlines()]
all_source=(ROOT.parent/'phase13-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl').read_bytes()
assert sha(all_source)=='a253b86c17219976a4db42e0b203a14affa8f01b62f7e58fbe3ec145aeb3efb8'
all_rows=[json.loads(line) for line in all_source.splitlines()]
assert rows==[row for row in all_rows if row['collection']=='bukhari']
assert len(rows)==43
checkpoint_bytes=(SHARED/'checkpoint.json').read_bytes();checkpoint=json.loads(checkpoint_bytes)
manifest_bytes=(SHARED/'evidence-manifest.json').read_bytes();manifest=json.loads(manifest_bytes)
entries=json.loads((SHARED/'held-state-entries.json').read_bytes())
assert checkpoint['saved_head']==manifest['saved_head']=='0639af7fd15786284b4c413fced77e38eec8825a'
assert sha(source_bytes)==checkpoint['input_receipts']['imports/web-deenhindi-20261112/staged/bukhari.jsonl']['sha256']
reading_bytes=(PRIMARY/'input/full-field-reading-input-89.jsonl').read_bytes()
assert sha(reading_bytes)=='4c8bc18bbc6d28bd432ef76f3937dc24bb8883651f95fa2dbce5d86b34f312b1'
reading=[json.loads(line) for line in reading_bytes.splitlines()]
read_by_id={(r['occurrence_id'],r['language']):r for r in reading}
proof=[]
for saved in rows:
    key=saved['collection']+':'+saved['number'];oid='deenhindi-'+key;state=entries[key]
    assert state['collection']==saved['collection'] and state['number']==saved['number']
    assert state['parsed']['path']==saved['parsed_path']
    source_hash=sha(importer.json_bytes(saved['source_record']))
    assert source_hash==manifest['source_record_sha256'][key]
    receipts=[]
    for kind,descriptor in (('raw',saved['snapshot']),('parsed',state['parsed'])):
        path=descriptor['path'];local=PRIMARY/'sources'/path
        assert not local.is_symlink()
        data=local.read_bytes();assert data==(SHARED/'sources'/path).read_bytes()
        plain=gzip.decompress(data);bound=manifest['files'][path]
        assert sha(data)==descriptor['stored_sha256']==bound['stored_sha256']==bound['sha256']
        assert len(data)==bound['bytes']==bound['stored_bytes']
        assert blob(data)==bound['git_blob_sha1']
        assert sha(plain)==descriptor['sha256']
        if 'stored_bytes' in descriptor:assert descriptor['stored_bytes']==len(data)
        if 'bytes' in descriptor:assert descriptor['bytes']==len(plain)
        if kind=='raw':
            body,reference=importer.parse_record(plain,saved['collection'],saved['number'])
            assert body==saved['source_record'] and reference==saved['source_reference_verbatim']
        else:
            expected={k:saved[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
            expected['classification']=saved['intake_classification']
            assert json.loads(plain)==expected
        receipts.append({'kind':kind,'path':path,'stored_bytes':len(data),'stored_sha256':sha(data),
                         'plain_bytes':len(plain),'plain_sha256':sha(plain),'git_blob_sha1':blob(data)})
    languages=('ar','hi','ur','ur-Latn','en') if saved['number']=='2239.2' else ('hi','ur')
    for language in languages:
        field=read_by_id[oid,language];text=saved['source_record'][importer.LANGUAGE_FIELDS[language]]
        assert text==field['text'] and sha(text.encode())==field['text_sha256']
        assert len(text)==field['characters'] and len(text.encode())==field['utf8_bytes']
    proof.append({'occurrence_id':oid,'source_record_sha256':source_hash,
                  'source_reference_verbatim':saved['source_reference_verbatim'],
                  'raw_reparse_exact':True,'complete_immutable_parsed_object_exact':True,
                  'own_read_fields_rebound':list(languages),'files':receipts})
report={'schema':'hadith-bank-independent-source-pair-verification-v1','result':'PASS',
        'source_commit':checkpoint['saved_head'],'occurrences':43,'files_reopened':86,'raw_reparses_exact':43,
        'own_read_fields_rebound':89,'source_cohort_sha256':sha(source_bytes),'source_input_sha256':sha(reading_bytes),
        'bounded_checkpoint_sha256':sha(checkpoint_bytes),'bounded_manifest_sha256':sha(manifest_bytes),
        'source_http_requests':0,'github_writes':0,'source_fields_modified':0,
        'importer_sha256':sha(Path(importer.__file__).read_bytes()),'records':proof}
dest=ROOT/'independent-source-verification.json';data=enc(report)
assert not dest.exists() or dest.read_bytes()==data
dest.write_bytes(data)
print(json.dumps({'result':'PASS','files':86,'reparses':43,'sha256':sha(data),'bytes':len(data)},indent=2))
