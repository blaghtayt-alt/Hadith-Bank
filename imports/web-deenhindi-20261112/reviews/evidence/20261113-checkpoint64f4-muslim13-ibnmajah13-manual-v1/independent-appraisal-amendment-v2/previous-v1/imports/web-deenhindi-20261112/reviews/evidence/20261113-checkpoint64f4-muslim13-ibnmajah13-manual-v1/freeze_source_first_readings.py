"""Freeze actual55 complete own readings before candidate serialization."""
from pathlib import Path
import collections,datetime,hashlib,json
from manual_source_first_readings import NOTES
ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not (ROOT/'publish-v1').exists() and not (ROOT/'manual_boundaries.py').exists()
sb=(ROOT/'input/cohort.jsonl').read_bytes();rb=(ROOT/'input/full-hi-ur-reading-input-52.jsonl').read_bytes()
eb=(ROOT/'input/additional-muslim2725-originals.jsonl').read_bytes();pb=(ROOT/'source-verification.json').read_bytes()
assert sha(sb)=='177817c054b00b6439014cb0f30e8f097e7f6c142851ae78f1c3ea397f3a00b5'
assert sha(rb)=='89f05bd3473c59c9a52a04b27cf9cff29a3e5dd034f0e79e4ef6f1c0a3f52b2d'
assert sha(eb)=='796d19f06d0b7ee8e8d72837f1796eab19e5b3ffea40a132f3045f8f89cd593b'
assert sha(pb)=='5c1f269b5a71714d297c5fedcc28771f3eab70f594f2a8a417cd26ca6d655e39'
sources={'deenhindi-'+x['collection']+':'+x['number']:x for x in map(json.loads,sb.splitlines())}
rows=[json.loads(x) for x in rb.splitlines()]+[json.loads(x) for x in eb.splitlines()]
assert len(rows)==len(NOTES)==55 and len(sources)==26
fields=[];languages=collections.Counter()
for x in rows:
 oid=x['occurrence_id'];lang=x['language'];text=x['text']
 assert text==sources[oid]['source_record'][x['source_field']] and sha(text.encode())==x['text_sha256']
 assert x['characters']==len(text) and x['utf8_bytes']==len(text.encode())
 languages[lang]+=1
 fields.append({'occurrence_id':oid,'collection':x['collection'],'number':x['number'],'language':lang,'source_field':x['source_field'],
  'source_text_sha256':x['text_sha256'],'characters_read':len(text),'utf8_bytes_read':len(text.encode()),'complete_own_field_read':True,'source_first_note':NOTES[oid,lang]})
assert sum(x['characters_read'] for x in fields)==23149 and sum(x['utf8_bytes_read'] for x in fields)==48862
assert languages=={'hi':26,'ur':26,'ar':1,'en':1,'ur-Latn':1}
combined=ROOT/'input/full-field-reading-input-55.jsonl';assert not combined.exists();combined.write_bytes(rb+eb)
note_files=[]
for n in range(1,7):
 p=ROOT/f'source_first_batch{n:02d}.py';note_files.append({'name':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
report={'schema':'hadith-bank-source-first-complete-reading-receipt-v1','source_commit':'64f4ed50ed6026855237a5d547a86dd03e73f804','reviewer':'OpenAI assistant /root/queue_audit',
 'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_cohort_sha256':sha(sb),'full_original_hi_ur_input_sha256':sha(rb),'additional_originals_sha256':sha(eb),
 'full_original_reading_input_sha256':sha(combined.read_bytes()),'own_source_verification_sha256':sha(pb),'source_first_note_files':note_files,
 'occurrences':26,'complete_fields_read':55,'characters_read':23149,'utf8_bytes_read':48862,'by_language':dict(languages),'additional_sibling_fields_read':3,
 'candidate_existed_before_complete_reading':False,'notes_or_candidate_from_another_reviewer_inspected':False,
 'source_only_candidates_requiring_all_siblings':['deenhindi-muslim:2725'],
 'scope_note':'All52 assigned Hindi/Urdu fields were actually read, plus all3 remaining original siblings of Muslim2725. The other25 parents supply finite own-field reports, encounters or attributed sayings; their75 sibling-language fields remain unread context. The comparison-only candidate has all5 nonempty fields read before any whole-parent disposition. No missing predicates, source defects or identities are supplied from another language.',
 'fields':fields,'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed'}
f=ROOT/'complete-source-first-readings.json';assert not f.exists();f.write_bytes(enc(report))
print(json.dumps({'receipt_sha256':sha(f.read_bytes()),'bytes':f.stat().st_size,'full55_input_sha256':sha(combined.read_bytes()),'fields':55,'characters':23149,'utf8_bytes':48862},indent=2))
