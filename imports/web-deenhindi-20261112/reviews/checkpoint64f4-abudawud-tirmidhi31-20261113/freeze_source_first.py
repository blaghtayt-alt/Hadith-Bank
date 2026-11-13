#!/usr/bin/env python3
"""Freeze actual complete own-field readings before preparing any review candidate."""
from pathlib import Path
import hashlib,json
from source_first_notes import NOTES

ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (ROOT/'complete-source-first-readings.json').exists()
assert not (ROOT/'manual_boundaries.py').exists() and not (ROOT/'publish-v1').exists()
raw=(ROOT/'input/cohort.jsonl').read_bytes();assert sha(raw)=='0a13beaaab0870f9e9ca031bac2d29be050e456cae18fbe139d5db02f027cd7d'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,raw.splitlines())}
priority=(ROOT/'input/full-hi-ur-reading-input-62.jsonl').read_bytes();assert sha(priority)=='41f87a48423f60e7757e3410f57739d6484a6dd287b192509568ac4a4c559c68'
extra=(ROOT/'input/additional-abudawud2720-originals.jsonl').read_bytes();assert sha(extra)=='c204ce128e50cb69f7866246564d2888a018ff090230a2b07df0db378ceddf3d'
fields=[json.loads(x) for x in (priority+extra).splitlines()]
assert len(fields)==65 and len(NOTES)==65
assert {(f['occurrence_id'].removeprefix('deenhindi-'),f['language']) for f in fields}==set(NOTES)
records=[]
for f in fields:
    key=f['occurrence_id'].removeprefix('deenhindi-');language=f['language'];text=sources[key]['source_record'][f['source_field']]
    assert text==f['text'] and sha(text.encode())==f['text_sha256'] and len(text)==f['characters'] and len(text.encode())==f['utf8_bytes']
    records.append({'occurrence_id':f['occurrence_id'],'language':language,'source_field':f['source_field'],
                    'text_sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),
                    'complete_own_field_read':True,'primary_reading_note':NOTES[(key,language)],
                    'peer_candidate_or_notes_inspected_before_own_reading':False})
proof=(ROOT/'source-verification.json').read_bytes();assert sha(proof)=='47da3ce0e2e483c3854c2a1c917eb2b9a40e35333faf28faef701ba86267ef7e'
expanded=b''.join((json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for f in fields)
(ROOT/'input/full-field-reading-input-65.jsonl').write_bytes(expanded)
receipt={'schema':'hadith-bank-primary-complete-source-first-reading-v1',
         'source_commit':'64f4ed50ed6026855237a5d547a86dd03e73f804','source_cohort_sha256':sha(raw),
         'priority_original_input_sha256':sha(priority),'additional_original_input_sha256':sha(extra),
         'all_original_input_sha256':sha(expanded),'source_verification_sha256':sha(proof),
         'own_notes_sha256':sha((ROOT/'source_first_notes.py').read_bytes()),
         'full_fields_read':len(records),'characters_read':sum(f['characters'] for f in records),
         'utf8_bytes_read':sum(f['utf8_bytes'] for f in records),'extra_sibling_scope':{'abudawud:2720':['ar','en','ur-Latn']},
         'candidate_exists_at_freeze':False,'peer_notes_or_candidate_opened_before_freeze':False,
         'high_level_scope_hints_received':True,'source_only_parent_assessment_requires_all_five_own_fields':True,
         'new_semantic_decision_ledger_created':False,'source_http_requests':0,'github_writes':0,'records':records}
assert (receipt['full_fields_read'],receipt['characters_read'],receipt['utf8_bytes_read'])==(65,28670,61240)
(ROOT/'complete-source-first-readings.json').write_bytes(enc(receipt))
print(json.dumps({'status':'FROZEN','receipt_sha256':sha(enc(receipt)),'notes_sha256':receipt['own_notes_sha256'],'original_input_sha256':sha(expanded),'fields_read':65,'characters_read':28670,'utf8_bytes_read':61240,'candidate_exists':False},indent=2))
