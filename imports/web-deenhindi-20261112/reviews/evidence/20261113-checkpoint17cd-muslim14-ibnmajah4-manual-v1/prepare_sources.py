"""Freeze the assigned original source packet and independently reopen every saved pair."""
from pathlib import Path
import gzip, hashlib, json, sys

HERE=Path(__file__).resolve().parent
PACKET=HERE.parent/'phase22-checkpoint17cd-input-partitions/queue-muslim14-ibnmajah4'
PIN='17cd396eb858a29162505d545aad556ac73ce9ce'
sys.path.insert(0,str(HERE.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def write_exact(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)

manifest_raw=(PACKET/'input-delivery-manifest.json').read_bytes()
assert sha(manifest_raw)=='5d81d847d0e4f917ef692c9ea47313a34d11db892446451bdb21dda4b2045f39'
manifest=json.loads(manifest_raw);assert manifest['source_commit']==PIN
for item in manifest['files']:
    raw=Path(item['local_path']).read_bytes()
    assert len(raw)==item['bytes'] and sha(raw)==item['sha256'] and git(raw)==item['git_blob_sha1']
for name in ['cohort.jsonl','full-hi-ur-reading-input-36.jsonl','source-verification.json','partition-receipt.json','input-delivery-manifest.json']:
    write_exact(HERE/'input'/name,(PACKET/name).read_bytes())
cohort_raw=(HERE/'input/cohort.jsonl').read_bytes()
assert sha(cohort_raw)=='4e89ffeedce15ea35358c8c1d5dd4079047505909ad82e436b9730f8ba90c28a'
rows=[json.loads(x) for x in cohort_raw.splitlines()]
by_key={s['collection']+':'+s['number']:s for s in rows}
assert len(by_key)==18 and sum(s['collection']=='muslim' for s in rows)==14 and sum(s['collection']=='ibnmajah' for s in rows)==4
proof_raw=(HERE/'input/source-verification.json').read_bytes()
assert sha(proof_raw)=='f6a4b8fe530e35f742631b535e79af23b4f43ea44874fc5f14c1d846f61d12d8'
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
reading_raw=(HERE/'input/full-hi-ur-reading-input-36.jsonl').read_bytes()
assert sha(reading_raw)=='2f2fb4a801e29497ed7f62f768af9d1899c19063b89e1b26a2fda9b9e17ab5bc'
readings=[json.loads(x) for x in reading_raw.splitlines()]
assert len(readings)==36
for row in readings:
    saved=by_key[row['collection']+':'+row['number']]
    text=saved['source_record'][row['source_field']]
    assert row['text']==text and row['text_sha256']==sha(text.encode())
    assert row['characters']==len(text) and row['utf8_bytes']==len(text.encode())
    assert row['source_commit']==PIN and row['complete_own_field_read'] is False
assert sum(x['characters'] for x in readings)==12695 and sum(x['utf8_bytes'] for x in readings)==27402
result={'schema':'hadith-bank-primary-saved-source-reopen-proof-v1','result':'PASS','source_commit':PIN,
    'source_packet_manifest_sha256':sha(manifest_raw),'partition_source_proof_sha256':sha(proof_raw),
    'source_cohort_sha256':sha(cohort_raw),'full_hi_ur_input_sha256':sha(reading_raw),
    'source_files_reopened':36,'complete_raw_reparses':18,'source_occurrences':18,
    'source_fields_bound':36,'source_field_characters':12695,'source_field_utf8_bytes':27402,
    'full_saved_state_sha256_from_partition_proof':proof['full_saved_state_sha256'],
    'full_state_scope':'This primary check independently verifies the assigned saved source files and original objects. The broader saved-state/old-ID comparison belongs to the separate acquisition audit.',
    'parser_sha256':sha(Path(importer.__file__).read_bytes()),'records':checked,
    'new_linguistic_readings_claimed_by_preparation':0,'candidate_created':False,'source_http_requests':0,'github_writes':0}
dest=HERE/'source-verification.json';assert not dest.exists();dest.write_bytes(importer.json_bytes(result))
print(json.dumps({'result':'PASS','path':str(dest),'sha256':sha(dest.read_bytes()),'source_files':36,'raw_reparses':18,'own_reading_fields_prepared':36},indent=2))
