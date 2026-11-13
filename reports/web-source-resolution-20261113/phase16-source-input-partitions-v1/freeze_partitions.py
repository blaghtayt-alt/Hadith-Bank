"""Freeze four source-first input partitions; no semantic readings or decisions."""
from pathlib import Path
from decimal import Decimal
import collections, gzip, hashlib, itertools, json, sys

ROOT=Path(__file__).resolve().parent
MONITOR=ROOT.parent/'phase15-successor-acquisition-monitor'
SOURCE=MONITOR/'next-review-cohort'
ARTIFACT=MONITOR/'held-evidence'
COMMIT='5589a3ffc3b43c3324ae26f2b6c4d33152834456'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda value:hashlib.sha256(value).hexdigest()
git=lambda value:hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
lines=lambda rows:b''.join((json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for row in rows)


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    assert not path.exists() or path.read_bytes()==data, ('frozen input collision',str(path))
    path.write_bytes(data)


source_bytes=(SOURCE/'held-source-records.jsonl').read_bytes()
assert sha(source_bytes)=='4a4000d46dba9cff36695a62e7e5207af8f5183644141e8ca23b047e62434490'
raw_lines=source_bytes.splitlines(keepends=True)
rows=[json.loads(line) for line in raw_lines]
assert len(rows)==100
key=lambda row:row['collection']+':'+row['number']
by_key={key(row):row for row in rows}
assert len(by_key)==100
source_receipt_bytes=(SOURCE/'evidence-manifest.json').read_bytes()
assert sha(source_receipt_bytes)=='b68c07912aecf94eeca7461b8671b1cd91aeb24468172bca0dd11a8119acf027'
source_receipt=json.loads(source_receipt_bytes)
assert source_receipt['source_commit']==COMMIT and set(source_receipt['keys'])==set(by_key)
assert source_receipt['source_rows_sha256']==sha(source_bytes)
artifact_bytes=(ARTIFACT/'evidence-manifest.json').read_bytes();artifact=json.loads(artifact_bytes)
assert sha(artifact_bytes)==source_receipt['source_evidence_manifest_sha256']
checkpoint_bytes=(ARTIFACT/'checkpoint.json').read_bytes();checkpoint=json.loads(checkpoint_bytes)
assert checkpoint['saved_head']==artifact['saved_head']==COMMIT
state_entries=json.loads((ARTIFACT/'held-state-entries.json').read_bytes())
prior_state_bytes=(ROOT.parent/'phase13-successor-acquisition-monitor/saved-checkpoint/state.json').read_bytes()
assert sha(prior_state_bytes)==source_receipt['baseline_state_sha256']=='5ce4a7ef9633cda58831c116d46f6a494703c6fa3931783d368fbd7fec62c4e1'
prior_state=json.loads(prior_state_bytes)
assert len(prior_state['imported'])==15672 and not set(by_key)&set(prior_state['imported'])
counts=collections.Counter(row['collection'] for row in rows)
assert counts=={'bukhari':20,'muslim':18,'nasai':22,'abudawud':8,'tirmidhi':17,'ibnmajah':15}
ibn=sorted((row for row in rows if row['collection']=='ibnmajah'),key=lambda row:(Decimal(row['number']),row['number'],key(row)))
ibn_keys=[key(row) for row in ibn]
groups={
    'checkpoint-bukhari20-ibnmajah5':{'primary_owner':'/root/checkpoint_inventory','independent_owner':'/root/queue_audit',
        'keys':{key(row) for row in rows if row['collection']=='bukhari'}|set(ibn_keys[:5])},
    'queue-muslim18-ibnmajah7':{'primary_owner':'/root/queue_audit','independent_owner':'/root/deployment_audit',
        'keys':{key(row) for row in rows if row['collection']=='muslim'}|set(ibn_keys[5:12])},
    'deployment-abudawud8-tirmidhi17':{'primary_owner':'/root/deployment_audit','independent_owner':'/root',
        'keys':{key(row) for row in rows if row['collection'] in ('abudawud','tirmidhi')}},
    'root-nasai22-ibnmajah3':{'primary_owner':'/root','independent_owner':'/root/checkpoint_inventory',
        'keys':{key(row) for row in rows if row['collection']=='nasai'}|set(ibn_keys[12:])},
}
assert all(len(group['keys'])==25 for group in groups.values())
assert set().union(*(g['keys'] for g in groups.values()))==set(by_key)
assert all(not a['keys']&b['keys'] for a,b in itertools.combinations(groups.values(),2))
proof={}
for row in rows:
    identity=key(row);entry=state_entries[identity]
    assert identity in artifact['held_keys'] and entry['collection']==row['collection'] and entry['number']==row['number']
    assert entry['parsed']['path']==row['parsed_path']
    body_sha=sha(importer.json_bytes(row['source_record']))
    assert body_sha==artifact['source_record_sha256'][identity]
    file_receipts=[]
    for kind,descriptor in (('raw',row['snapshot']),('parsed',entry['parsed'])):
        relative=descriptor['path'];path=ARTIFACT/'sources'/relative
        assert not path.is_symlink() and '..' not in Path(relative).parts and not Path(relative).is_absolute()
        stored=path.read_bytes();plain=gzip.decompress(stored);bound=artifact['files'][relative]
        assert sha(stored)==descriptor['stored_sha256']==bound['stored_sha256']==bound['sha256']
        assert len(stored)==bound['bytes']==bound['stored_bytes'] and git(stored)==bound['git_blob_sha1']
        assert sha(plain)==descriptor['sha256']
        if 'bytes' in descriptor:assert len(plain)==descriptor['bytes']
        if 'stored_bytes' in descriptor:assert len(stored)==descriptor['stored_bytes']
        if kind=='raw':
            parsed,reference=importer.parse_record(plain,row['collection'],row['number'])
            assert parsed==row['source_record'] and reference==row['source_reference_verbatim']
        else:
            expected={k:row[k] for k in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
            expected['classification']=row['intake_classification']
            assert json.loads(plain)==expected
        file_receipts.append({'kind':kind,'path':relative,'shared_local_path':str(path.resolve()),
            'stored_bytes':len(stored),'stored_sha256':sha(stored),'plain_bytes':len(plain),
            'plain_sha256':sha(plain),'git_blob_sha1':git(stored)})
    proof[identity]={'occurrence_id':'deenhindi-'+identity,'source_record_sha256':body_sha,
        'source_reference_verbatim':row['source_reference_verbatim'],'raw_reparse_exact':True,
        'complete_immutable_parsed_object_exact':True,'absent_from_prior0639_imported':True,'files':file_receipts}

group_receipts=[]
for name,group in groups.items():
    selected=[row for row in rows if key(row) in group['keys']]
    selected_bytes=b''.join(line for row,line in zip(rows,raw_lines) if key(row) in group['keys'])
    assert [json.loads(line) for line in selected_bytes.splitlines()]==selected
    reading=[]
    for order,row in enumerate(selected,1):
        identity=key(row)
        for language in ('hi','ur'):
            field=importer.LANGUAGE_FIELDS[language];text=row['source_record'].get(field)
            assert isinstance(text,str) or text is None
            reading.append({'reading_order':len(reading)+1,'occurrence_order':order,
                'occurrence_id':'deenhindi-'+identity,'collection':row['collection'],'number':row['number'],
                'language':language,'source_field':field,'text':text,
                'source_value_state':'missing' if field not in row['source_record'] else 'null' if text is None else 'empty_string' if not text else 'nonempty',
                'text_sha256':sha(text.encode()) if text is not None else None,
                'characters':len(text) if text is not None else 0,'utf8_bytes':len(text.encode()) if text is not None else 0,
                'source_record_sha256':proof[identity]['source_record_sha256'],
                'source_reference_verbatim':row['source_reference_verbatim'],'source_commit':COMMIT,
                'source_snapshot_path':row['snapshot']['path'],'source_parsed_path':row['parsed_path'],
                'semantic_review_status':'unread_at_frozen_source_preparation','complete_own_field_read':False})
    reading_bytes=lines(reading)
    verification={'schema':'hadith-bank-source-first-partition-verification-v1','result':'PASS',
        'source_commit':COMMIT,'partition':name,'source_manifest_sha256':sha(source_receipt_bytes),
        'artifact_manifest_sha256':sha(artifact_bytes),'prior0639_state_sha256':sha(prior_state_bytes),
        'original_cohort_sha256':sha(selected_bytes),'occurrences':25,'source_files_reopened':50,'raw_reparses_exact':25,
        'new_readings_claimed':0,'new_review_decisions':0,'source_http_requests':0,'github_writes':0,
        'records':[proof[key(row)] for row in selected]}
    save(ROOT/name/'cohort.jsonl',selected_bytes)
    save(ROOT/name/'full-hi-ur-reading-input-50.jsonl',reading_bytes)
    save(ROOT/name/'source-verification.json',enc(verification))
    receipt={'partition':name,'primary_owner':group['primary_owner'],'independent_owner':group['independent_owner'],
        'source_commit':COMMIT,'selected_keys':[key(row) for row in selected],
        'collection_counts':dict(collections.Counter(row['collection'] for row in selected)),
        'cohort_path':str((ROOT/name/'cohort.jsonl').resolve()),'cohort_sha256':sha(selected_bytes),'cohort_bytes':len(selected_bytes),
        'reading_input_path':str((ROOT/name/'full-hi-ur-reading-input-50.jsonl').resolve()),
        'reading_input_sha256':sha(reading_bytes),'reading_input_bytes':len(reading_bytes),
        'prepared_field_slots':50,'prepared_nonempty_fields':sum(x['source_value_state']=='nonempty' for x in reading),
        'prepared_characters':sum(x['characters'] for x in reading),'prepared_utf8_bytes':sum(x['utf8_bytes'] for x in reading),
        'verification_path':str((ROOT/name/'source-verification.json').resolve()),'verification_sha256':sha(enc(verification)),
        'new_semantic_readings_claimed':0,'new_review_decisions':0}
    save(ROOT/name/'partition-receipt.json',enc(receipt));group_receipts.append(receipt)

report={'schema':'hadith-bank-four-way-source-first-partition-v1','result':'PASS','source_commit':COMMIT,
    'original100_sha256':sha(source_bytes),'authoritative_source_manifest_sha256':sha(source_receipt_bytes),
    'bounded_artifact_manifest_sha256':sha(artifact_bytes),'bounded_checkpoint_sha256':sha(checkpoint_bytes),
    'prior0639_state_sha256':sha(prior_state_bytes),'all100_absent_from_prior15672_imported':True,
    'all100_raw_reparses_exact':True,'all200_saved_files_reopened':True,
    'partition_rule':'All complete book subsets as assigned. IbnMajah sorted by Decimal(source number), literal source number and provider key as stable tie-breakers: first5 checkpoint, next7 queue, last3 root. Selected source lines preserve original packet order within each group. Ordering never implies admission.',
    'ibnmajah_numeric_order':ibn_keys,'ibnmajah_slices':{'checkpoint':ibn_keys[:5],'queue':ibn_keys[5:12],'root':ibn_keys[12:]},
    'groups':group_receipts,'pairwise_disjoint':True,'union_equals_exact_new100':True,
    'source_http_requests':0,'github_writes':0,'engine_changes':0,'new_semantic_readings_claimed':0,'new_review_decisions':0,
    'current_full_state_history_scope':'This preparation proves source/parsed fidelity and absence from the exact prior0639 imported set. It makes no new claim about the current5589 complete-state/history audit.',
    'importer_sha256':sha(Path(importer.__file__).read_bytes())}
save(ROOT/'partition-receipt.json',enc(report))
files=[{'path':path.relative_to(ROOT).as_posix(),'local_path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())} for path in sorted(ROOT.rglob('*')) if path.is_file() and path.name!='delivery-manifest.json']
manifest={'schema':'hadith-bank-source-input-partition-delivery-v1','result':'PASS','source_commit':COMMIT,
          'partition_receipt_sha256':sha(enc(report)),'files':files}
save(ROOT/'delivery-manifest.json',enc(manifest))
print(json.dumps({'result':'PASS','manifest_sha256':sha(enc(manifest)),'partition_receipt_sha256':sha(enc(report)),
                  'groups':[dict(x) for x in group_receipts],'files':len(files),'bytes':sum(x['bytes'] for x in files)},ensure_ascii=False,indent=2))
