"""Bind actual complete own readings to the immutable original source packet."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sha=lambda value:hashlib.sha256(value).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (ROOT/'publish-v1').exists()
source_bytes=(ROOT/'input/cohort.jsonl').read_bytes()
reading_bytes=(ROOT/'input/full-hi-ur-reading-input-36.jsonl').read_bytes()
proof_bytes=(ROOT/'source-verification.json').read_bytes()
assert sha(source_bytes)=='4e89ffeedce15ea35358c8c1d5dd4079047505909ad82e436b9730f8ba90c28a'
assert sha(reading_bytes)=='2f2fb4a801e29497ed7f62f768af9d1899c19063b89e1b26a2fda9b9e17ab5bc'
assert sha(proof_bytes)=='dde8f242ad63471b39831c8474870d35e31b56fe5d97ff248e2c0671e7d17e28'
notes={};note_files=[]
for name in ('source_first_batch01.py','source_first_batch02.py','source_first_batch03.py'):
    path=ROOT/name
    module_spec=importlib.util.spec_from_file_location(path.stem,path)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    assert not (set(notes)&set(module.NOTES));notes.update(module.NOTES)
    note_files.append({'name':name,'sha256':sha(path.read_bytes()),'bytes':len(path.read_bytes())})
rows=[json.loads(line) for line in reading_bytes.splitlines()]
assert len(rows)==36 and len(notes)==18
assert sum(len(row['text']) for row in rows)==12695 and sum(len(row['text'].encode()) for row in rows)==27402
fields=[]
for row in rows:
    key=row['collection']+':'+row['number'];language=row['language']
    assert language in ('hi','ur') and sha(row['text'].encode())==row['text_sha256']
    fields.append({'occurrence_id':row['occurrence_id'],'collection':row['collection'],'number':row['number'],
        'language':language,'source_field':row['source_field'],'source_text_sha256':row['text_sha256'],
        'characters_read':len(row['text']),'utf8_bytes_read':len(row['text'].encode()),
        'complete_own_field_read':True,'source_first_note':notes[key][language]})
report={'schema':'hadith-bank-source-first-complete-reading-receipt-v1',
    'source_commit':'17cd396eb858a29162505d545aad556ac73ce9ce',
    'reviewer':'OpenAI assistant /root/queue_audit','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_cohort_sha256':sha(source_bytes),'full_original_reading_input_sha256':sha(reading_bytes),
    'own_source_verification_sha256':sha(proof_bytes),'source_first_note_files':note_files,
    'occurrences':18,'complete_fields_read':36,'characters_read':12695,'utf8_bytes_read':27402,
    'by_language':{'hi':18,'ur':18},'additional_sibling_fields_read':0,
    'candidate_existed_before_complete_reading':False,'notes_or_candidate_from_another_reviewer_inspected':False,
    'source_only_candidates_requiring_all_siblings':[],
    'scope_note':'Every assigned parent supplies a finite own Hindi and Urdu report or encounter. No whole-parent exclusion is proposed from these readings; no additional sibling language has been read or receives reading credit.',
    'fields':fields,'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed'}
target=ROOT/'complete-source-first-readings.json';assert not target.exists();target.write_bytes(enc(report))
print(json.dumps({'path':str(target),'sha256':sha(target.read_bytes()),'bytes':len(target.read_bytes()),
    'fields':36,'characters':12695,'utf8_bytes':27402,'additional_languages_read':0},indent=2))
