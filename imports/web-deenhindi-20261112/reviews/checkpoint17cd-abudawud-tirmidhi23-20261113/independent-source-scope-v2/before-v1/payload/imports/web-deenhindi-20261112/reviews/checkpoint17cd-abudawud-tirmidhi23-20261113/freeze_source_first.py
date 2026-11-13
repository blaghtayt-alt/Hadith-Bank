#!/usr/bin/env python3
"""Bind the actual 46 complete original readings before candidate creation."""
import hashlib,json
from pathlib import Path
from source_first_notes import NOTES
ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (ROOT/'complete-source-first-readings.json').exists()
assert not any(ROOT.glob('publish*')) and not (ROOT/'manual_boundaries.py').exists()
raw=(ROOT/'input/cohort.jsonl').read_bytes()
assert sha(raw)=='e9d55267c7f2ea3f0f2c008a440276e33736b5c0a036cbd0e937b067a4e9bfaf'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,raw.splitlines())}
original=(ROOT/'input/full-hi-ur-reading-input-46.jsonl').read_bytes()
assert sha(original)=='1c6567cef512392b28923d0ab271219e07e89d01b723daa87605deacb346f93f'
fields=[json.loads(x) for x in original.splitlines()]
assert len(fields)==len(NOTES)==46 and len(sources)==23
assert {(r['occurrence_id'].removeprefix('deenhindi-'),r['language']) for r in fields}==set(NOTES)
(ROOT/'input/full-field-reading-input-46.jsonl').write_bytes(original)
records=[]
for r in fields:
    key=r['occurrence_id'].removeprefix('deenhindi-');text=sources[key]['source_record'][r['source_field']]
    assert text==r['text'] and sha(text.encode())==r['text_sha256']
    records.append({k:r[k] for k in ('occurrence_id','language','source_field','characters','utf8_bytes','text_sha256')}|{'complete_own_field_read':True,'independent_or_primary_candidate_inspected_before_reading':False,'own_source_first_note':NOTES[(key,r['language'])]})
assert sum(r['characters'] for r in records)==24000 and sum(r['utf8_bytes'] for r in records)==51211
receipt={'schema':'hadith-bank-complete-source-first-reading-v1','source_commit':'17cd396eb858a29162505d545aad556ac73ce9ce','source_cohort_sha256':sha(raw),'original_full_field_input_sha256':sha(original),'original_priority_input_sha256':sha(original),'source_verification_sha256':sha((ROOT/'source-verification.json').read_bytes()),'own_notes_sha256':sha((ROOT/'source_first_notes.py').read_bytes()),'full_fields_read':46,'characters_read':24000,'utf8_bytes_read':51211,'additional_sibling_readings_required_in_own_pass':False,'additional_sibling_scope':{},'candidate_exists_at_freeze':False,'peer_notes_or_candidate_inspected_before_freeze':False,'source_http_requests':0,'github_writes':0,'records':records}
b=enc(receipt);(ROOT/'complete-source-first-readings.json').write_bytes(b)
print(json.dumps({'status':'FROZEN','receipt_sha256':sha(b),'own_notes_sha256':receipt['own_notes_sha256'],'full_fields_read':46,'characters_read':24000,'utf8_bytes_read':51211,'candidate_exists_at_freeze':False}))
