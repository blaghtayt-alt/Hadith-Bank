"""Freeze the assigned original source packet and independently reopen every saved pair."""
from pathlib import Path
import gzip, hashlib, json, sys

HERE=Path(__file__).resolve().parent
PACKET=HERE.parent/'phase23-checkpoint64f4-input-partitions/queue-muslim13-ibnmajah13'
PIN='64f4ed50ed6026855237a5d547a86dd03e73f804'
sys.path.insert(0,str(HERE.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def write_exact(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)

manifest_raw=(PACKET/'input-delivery-manifest.json').read_bytes()
assert sha(manifest_raw)=='21249c6a25fcfb8749a9a4fa9f925497c68f7ba6959af71ab57fd771d347e404'
manifest=json.loads(manifest_raw);assert manifest['source_commit']==PIN
for item in manifest['files']:
    raw=Path(item['local_path']).read_bytes()
    assert len(raw)==item['bytes'] and sha(raw)==item['sha256'] and git(raw)==item['git_blob_sha1']
for name in ['cohort.jsonl','full-hi-ur-reading-input-52.jsonl','source-verification.json','partition-receipt.json','input-delivery-manifest.json']:
    write_exact(HERE/'input'/name,(PACKET/name).read_bytes())
cohort_raw=(HERE/'input/cohort.jsonl').read_bytes()
assert sha(cohort_raw)=='177817c054b00b6439014cb0f30e8f097e7f6c142851ae78f1c3ea397f3a00b5'
rows=[json.loads(x) for x in cohort_raw.splitlines()]
by_key={s['collection']+':'+s['number']:s for s in rows}
assert len(by_key)==26 and sum(s['collection']=='muslim' for s in rows)==13 and sum(s['collection']=='ibnmajah' for s in rows)==13
proof_raw=(HERE/'input/source-verification.json').read_bytes()
assert sha(proof_raw)=='d9793798669cd890655efdcbe7458a6a4dd80097408290bb05c60f0662bbbdff'
proof=json.loads(proof_raw);assert proof['source_commit']==PIN
checked=[]
for row in proof['records']:
    saved=by_key[row['key']]
    assert sha(importer.json_bytes(saved['source_record']))==row['source_record_sha256']
    file_receipts=[]
    for item in row['files']:
        path=Path(item['local_path']);assert not path.is_symlink()
        stored=path.read_bytes();plain=gzip.decompress(stored)
        assert len(stored)==item['stored_bytes'] and sha(stored)==item['stored_sha256']
        assert len(plain)==item['bytes'] and sha(plain)==item['sha256'] and git(stored)==item['git_blob_sha1']
        rel=item['path'];assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
        write_exact(HERE/'sources'/rel,stored)
        assert (HERE/'sources'/rel).read_bytes()==stored
        if item['kind']=='raw':
            assert rel==saved['snapshot']['path']
            assert sha(plain)==saved['snapshot']['sha256'] and sha(stored)==saved['snapshot']['stored_sha256']
            body,reference=importer.parse_record(plain,saved['collection'],saved['number'])
            assert body==saved['source_record'] and reference==saved['source_reference_verbatim']
        else:
            assert item['kind']=='parsed' and rel==saved['parsed_path']
            expected={k:saved[k] for k in ('schema','collection','number','snapshot','source_record','source_reference_verbatim')}
            expected['classification']=saved['intake_classification']
            assert json.loads(plain)==expected
        file_receipts.append({k:v for k,v in item.items() if k!='local_path'})
    checked.append({'occurrence_id':'deenhindi-'+row['key'],'source_record_sha256':row['source_record_sha256'],
        'source_reference_verbatim':saved['source_reference_verbatim'],'raw_complete_object_and_reference_reparse_exact':True,
        'complete_immutable_parsed_object_exact':True,'files':file_receipts})
reading_raw=(HERE/'input/full-hi-ur-reading-input-52.jsonl').read_bytes()
assert sha(reading_raw)=='89f05bd3473c59c9a52a04b27cf9cff29a3e5dd034f0e79e4ef6f1c0a3f52b2d'
readings=[json.loads(x) for x in reading_raw.splitlines()]
assert len(readings)==52
for row in readings:
    saved=by_key[row['collection']+':'+row['number']]
    text=saved['source_record'][row['source_field']]
    assert row['text']==text and row['text_sha256']==sha(text.encode())
    assert row['characters']==len(text) and row['utf8_bytes']==len(text.encode())
    assert row['source_commit']==PIN and row['complete_own_field_read'] is False
assert sum(x['characters'] for x in readings)==22574 and sum(x['utf8_bytes'] for x in readings)==48122
result={'schema':'hadith-bank-primary-saved-source-reopen-proof-v1','result':'PASS','source_commit':PIN,
    'source_packet_manifest_sha256':sha(manifest_raw),'partition_source_proof_sha256':sha(proof_raw),
    'source_cohort_sha256':sha(cohort_raw),'full_hi_ur_input_sha256':sha(reading_raw),
    'source_files_reopened':52,'complete_raw_reparses':26,'source_occurrences':26,
    'source_fields_bound':52,'source_field_characters':22574,'source_field_utf8_bytes':48122,
    'full_saved_state_sha256_from_partition_proof':proof['full_saved_state_sha256'],
    'full_state_scope':'This primary check independently verifies the assigned saved source files and original objects. The broader saved-state/old-ID comparison belongs to the separate acquisition audit.',
    'parser_sha256':sha(Path(importer.__file__).read_bytes()),'records':checked,
    'new_linguistic_readings_claimed_by_preparation':0,'candidate_created':False,'source_http_requests':0,'github_writes':0}
dest=HERE/'source-verification.json';assert not dest.exists();dest.write_bytes(importer.json_bytes(result))
print(json.dumps({'result':'PASS','path':str(dest),'sha256':sha(dest.read_bytes()),'source_files':52,'raw_reparses':26,'own_reading_fields_prepared':52},indent=2))
