"""Freeze the exact new Muslim25 and verify only existing saved source bytes."""
from pathlib import Path
import gzip, hashlib, json, shutil, sys

ROOT=Path(__file__).resolve().parent
SHARED=ROOT.parent/'phase13-successor-acquisition-monitor/held-evidence'
COHORT=ROOT.parent/'phase13-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer

sha=lambda data:hashlib.sha256(data).hexdigest()
blob=lambda data:hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)

cohort_bytes=COHORT.read_bytes()
assert sha(cohort_bytes)=='a253b86c17219976a4db42e0b203a14affa8f01b62f7e58fbe3ec145aeb3efb8'
selected_lines=[line for line in cohort_bytes.splitlines(keepends=True) if json.loads(line)['collection']=='muslim']
selected_bytes=b''.join(selected_lines)
rows=[json.loads(line) for line in selected_lines];assert len(rows)==25
assert len({row['number'] for row in rows})==25
manifest_bytes=(SHARED/'evidence-manifest.json').read_bytes();manifest=json.loads(manifest_bytes)
checkpoint_bytes=(SHARED/'checkpoint.json').read_bytes();checkpoint=json.loads(checkpoint_bytes)
assert checkpoint['saved_head']==manifest['saved_head']=='0639af7fd15786284b4c413fced77e38eec8825a'
assert sha(selected_bytes)==checkpoint['input_receipts']['imports/web-deenhindi-20261112/staged/muslim.jsonl']['sha256']
entries=json.loads((SHARED/'held-state-entries.json').read_bytes())
reading=[];proof=[];stored_total=plain_total=0
for order,row in enumerate(rows,1):
    key=row['collection']+':'+row['number'];identity='deenhindi-'+key
    entry=entries[key]
    assert key in manifest['held_keys'] and entry['collection']==row['collection'] and entry['number']==row['number']
    assert entry['parsed']['path']==row['parsed_path']
    source_sha=sha(importer.json_bytes(row['source_record']))
    assert source_sha==manifest['source_record_sha256'][key]
    file_receipts=[]
    for kind,descriptor in [('raw',row['snapshot']),('parsed',entry['parsed'])]:
        path=descriptor['path'];data=(SHARED/'sources'/path).read_bytes();plain=gzip.decompress(data)
        bound=manifest['files'][path]
        assert sha(data)==descriptor['stored_sha256']==bound['stored_sha256']==bound['sha256']
        assert len(data)==bound['bytes']==bound['stored_bytes']
        if 'stored_bytes' in descriptor:assert len(data)==descriptor['stored_bytes']
        assert blob(data)==bound['git_blob_sha1']
        assert sha(plain)==descriptor['sha256']
        if 'bytes' in descriptor:assert len(plain)==descriptor['bytes']
        if kind=='raw':
            body,reference=importer.parse_record(plain,row['collection'],row['number'])
            assert body==row['source_record'] and reference==row['source_reference_verbatim']
        else:
            expected={k:row[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
            expected['classification']=row['intake_classification']
            assert json.loads(plain)==expected
        save(ROOT/'sources'/path,data)
        file_receipts.append({'kind':kind,'path':path,'stored_bytes':len(data),'stored_sha256':sha(data),
            'plain_bytes':len(plain),'plain_sha256':sha(plain),'git_blob_sha1':blob(data)})
        stored_total+=len(data);plain_total+=len(plain)
    for language in ('hi','ur'):
        field=importer.LANGUAGE_FIELDS[language];text=row['source_record'].get(field)
        assert isinstance(text,str) and text.strip()
        reading.append({'occurrence_order':order,'occurrence_id':identity,'language':language,'source_field':field,
            'text':text,'text_sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),
            'source_record_sha256':source_sha,'source_reference_verbatim':row['source_reference_verbatim'],
            'source_commit':checkpoint['saved_head'],'semantic_review_status':'unread_at_frozen_preparation',
            'source_parsed_path':row['parsed_path'],'source_snapshot_path':row['snapshot']['path']})
    proof.append({'occurrence_id':identity,'source_record_sha256':source_sha,
        'source_reference_verbatim':row['source_reference_verbatim'],'raw_reparse_exact':True,
        'complete_immutable_parsed_object_exact':True,'files':file_receipts})
save(ROOT/'input/cohort.jsonl',selected_bytes)
reading_bytes=b''.join((json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n').encode() for row in reading)
save(ROOT/'input/full-hi-ur-reading-input-50.jsonl',reading_bytes)
report={'schema':'hadith-bank-pinned-held-source-cohort-verification-v1','result':'PASS',
    'source_commit':checkpoint['saved_head'],'source_cohort117_sha256':sha(cohort_bytes),
    'source_cohort25_sha256':sha(selected_bytes),'source_reading_input50_sha256':sha(reading_bytes),
    'bounded_checkpoint_sha256':sha(checkpoint_bytes),'bounded_manifest_sha256':sha(manifest_bytes),
    'occurrences':25,'source_files':50,'raw_reparses':25,'source_first_fields_prepared':50,
    'characters':sum(r['characters'] for r in reading),'utf8_bytes':sum(r['utf8_bytes'] for r in reading),
    'stored_source_bytes':stored_total,'uncompressed_source_bytes':plain_total,
    'new_semantic_reading_claims':0,'new_review_decisions':0,'source_http_requests':0,'github_writes':0,
    'importer_sha256':sha(Path(importer.__file__).read_bytes()),'records':proof,
    'scope':'Exactly the new checkpoint0639 Muslim25, verified against the bounded saved-head artifact. Preparation and mechanical checks are not semantic admission. Original classification and immutable intake annotation remain separate.'}
save(ROOT/'source-verification.json',enc(report))
selection={'schema':'hadith-bank-source-cohort-reading-preparation-v1','source_commit':checkpoint['saved_head'],
    'selection':'All and only Muslim entries in the verified new117 held cohort, preserving source inventory order.',
    'selected_ids':[p['occurrence_id'] for p in proof],'source_cohort_sha256':sha(selected_bytes),
    'reading_input_sha256':sha(reading_bytes),'source_verification_sha256':sha(enc(report)),
    'prepared_fields':50,'characters':report['characters'],'utf8_bytes':report['utf8_bytes'],
    'new_manual_readings_claimed':0,'new_review_decisions':0}
save(ROOT/'selection.json',enc(selection))
print(json.dumps({'result':'PASS','cohort25_sha256':sha(selected_bytes),'reading50_sha256':sha(reading_bytes),
    'source_proof_sha256':sha(enc(report)),'source_files':50,'raw_reparses':25,
    'characters':report['characters'],'utf8_bytes':report['utf8_bytes']},indent=2))
