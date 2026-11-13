#!/usr/bin/env python3
"""Bind actual manually read fields to immutable source originals before candidate creation."""
import copy, hashlib, json
from pathlib import Path
from source_first_notes import NOTES

ROOT = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
enc = lambda x: (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
assert not (ROOT/'complete-source-first-readings.json').exists()
assert not any(ROOT.glob('publish*')) and not (ROOT/'manual_boundaries.py').exists()
raw = (ROOT/'input/cohort.jsonl').read_bytes()
assert sha(raw) == '0c35dfbc215a17776c508c0bc6374c1b937d7fcee67ac105c93ec5e9c3300557'
sources = {r['collection']+':'+r['number']:r for r in map(json.loads, raw.splitlines())}
base = [json.loads(x) for x in (ROOT/'input/full-hi-ur-reading-input-36.jsonl').read_bytes().splitlines()]
assert len(base) == 36 and len(NOTES) == 48
fields = dict(ar='textArabic', hi='translationHindi', ur='translationUrdu', en='translationEnglish')
fields['ur-Latn'] = 'translationUrduRoman'
expanded = copy.deepcopy(base)
extra_keys = ['abudawud:2582', 'abudawud:2610', 'abudawud:2617', 'tirmidhi:2565']
for key in extra_keys:
    template = next(r for r in base if r['occurrence_id'] == 'deenhindi-'+key)
    for lang in ('ar', 'en', 'ur-Latn'):
        row = copy.deepcopy(template)
        text = sources[key]['source_record'][fields[lang]]
        assert isinstance(text, str) and text.strip()
        row.update(language=lang, source_field=fields[lang], text=text,
                   characters=len(text), utf8_bytes=len(text.encode()),
                   text_sha256=sha(text.encode()), reading_order=len(expanded)+1,
                   complete_own_field_read=False,
                   semantic_review_status='original_only_added_scope_before_candidate')
        expanded.append(row)
expanded_raw = b''.join((json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',',':'))+'\n').encode() for r in expanded)
(ROOT/'input/full-field-reading-input-48.jsonl').write_bytes(expanded_raw)
assert {(r['occurrence_id'].removeprefix('deenhindi-'),r['language']) for r in expanded} == set(NOTES)
records=[]
for r in expanded:
    key=r['occurrence_id'].removeprefix('deenhindi-')
    text=sources[key]['source_record'][r['source_field']]
    assert text==r['text'] and sha(text.encode())==r['text_sha256']
    records.append({k:r[k] for k in ('occurrence_id','language','source_field','characters','utf8_bytes','text_sha256')}
                   | {'complete_own_field_read':True,
                      'independent_or_primary_candidate_inspected_before_reading':False,
                      'own_source_first_note':NOTES[(key,r['language'])]})
receipt={
    'schema':'hadith-bank-complete-source-first-reading-v1',
    'source_commit':'0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a',
    'source_cohort_sha256':sha(raw),
    'original_full_field_input_sha256':sha(expanded_raw),
    'original_priority_input_sha256':sha((ROOT/'input/full-hi-ur-reading-input-36.jsonl').read_bytes()),
    'source_verification_sha256':sha((ROOT/'input/source-verification.json').read_bytes()),
    'own_notes_sha256':sha((ROOT/'source_first_notes.py').read_bytes()),
    'full_fields_read':len(records),
    'characters_read':sum(r['characters'] for r in records),
    'utf8_bytes_read':sum(r['utf8_bytes'] for r in records),
    'additional_sibling_readings_required_in_own_pass':True,
    'additional_sibling_scope':{key:['ar','en','ur-Latn'] for key in extra_keys},
    'candidate_exists_at_freeze':False,
    'peer_notes_or_candidate_inspected_before_freeze':False,
    'source_http_requests':0,'github_writes':0,'records':records,
}
(ROOT/'complete-source-first-readings.json').write_bytes(enc(receipt))
print(json.dumps({k:v for k,v in receipt.items() if k!='records'},indent=2))
print('receipt_sha256',sha((ROOT/'complete-source-first-readings.json').read_bytes()))
