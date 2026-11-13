#!/usr/bin/env python3
"""Reopen only pinned originals and freeze completed independent source readings."""
import gzip,hashlib,json,sys
from pathlib import Path
from independent_readings import NOTES
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PACKET=BASE/'phase23-checkpoint64f4-muslim-ibnmajah26-review/input'
OWNER=BASE/'phase23-checkpoint64f4-muslim-ibnmajah26-review'
MONITOR=BASE/'phase22-successor-acquisition-monitor'
sys.path.insert(0,str(BASE/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
read=lambda p:json.loads(p.read_bytes())
assert not (ROOT/'complete-independent-source-first-readings.json').exists()
assert not (ROOT/'candidate').exists()
raw=(PACKET/'cohort.jsonl').read_bytes()
assert sha(raw)=='177817c054b00b6439014cb0f30e8f097e7f6c142851ae78f1c3ea397f3a00b5'
priority=(PACKET/'full-hi-ur-reading-input-52.jsonl').read_bytes()
assert sha(priority)=='89f05bd3473c59c9a52a04b27cf9cff29a3e5dd034f0e79e4ef6f1c0a3f52b2d'
expanded=(OWNER/'input/full-field-reading-input-55.jsonl').read_bytes()
assert sha(expanded)=='8f29e3cea6925729935ba0837024c6f6085b3d353b136fa231d305845938a794'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,raw.splitlines())}
fields=[json.loads(x) for x in expanded.splitlines()]
assert len(sources)==26 and len(fields)==len(NOTES)==55
assert {(f['occurrence_id'].removeprefix('deenhindi-'),f['language']) for f in fields}==set(NOTES)
artifact=read(MONITOR/'complete-held-evidence/evidence-manifest.json')
assert sha((MONITOR/'complete-held-evidence/evidence-manifest.json').read_bytes())=='c2abcc3fb29dbada01127031b902026f785be51b225d590407d8917465a80a0c'
assert artifact['saved_head']=='64f4ed50ed6026855237a5d547a86dd03e73f804'
state=read(MONITOR/'complete-held-evidence/held-state-entries.json')
evidence=[]
for key,saved in sources.items():
    entry=state[key]
    expected={n:saved[n] for n in ('schema','collection','number','snapshot','source_reference_verbatim','source_record')}
    expected['classification']=saved['intake_classification']
    assert entry['parsed']['path']==saved['parsed_path']
    sourcehash=sha(importer.json_bytes(saved['source_record']))
    assert sourcehash==artifact['source_record_sha256'][key]
    files=[]
    for kind,desc in [('raw',saved['snapshot']),('parsed',entry['parsed'])]:
        path=MONITOR/'complete-held-evidence/sources'/desc['path']
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to((MONITOR/'complete-held-evidence/sources').resolve())
        stored=path.read_bytes();plain=gzip.decompress(stored);a=artifact['files'][desc['path']]
        assert len(stored)==a['bytes']==a['stored_bytes'] and sha(stored)==a['sha256']==a['stored_sha256']==desc['stored_sha256'] and blob(stored)==a['git_blob_sha1']
        assert sha(plain)==desc['sha256']
        if kind=='raw':
            assert len(plain)==desc['bytes']
            actual,ref=importer.parse_record(plain,saved['collection'],saved['number'])
            assert actual==saved['source_record'] and ref==saved['source_reference_verbatim']
        else:assert plain==importer.json_bytes(expected)
        files.append({'kind':kind,'path':desc['path'],'bytes':len(plain),'sha256':sha(plain),'stored_bytes':len(stored),'stored_sha256':sha(stored),'git_blob_sha1':blob(stored)})
    evidence.append({'id':'deenhindi-'+key,'source_record_sha256':sourcehash,'exact_html_parser_object_and_reference':True,'files':files})
proof={'schema':'hadith-bank-independent-original-source-reopen-v1','result':'PASS','source_commit':artifact['saved_head'],'source_rows':26,'source_files_reopened':52,'complete_raw_html_reparses':26,'artifact_manifest_sha256':sha((MONITOR/'complete-held-evidence/evidence-manifest.json').read_bytes()),'source_cohort_sha256':sha(raw),'parser_sha256':sha(Path(importer.__file__).read_bytes()),'records':evidence}
(ROOT/'source-verification.json').write_bytes(enc(proof))
(ROOT/'input').mkdir(exist_ok=True)
(ROOT/'input/cohort.jsonl').write_bytes(raw)
(ROOT/'input/full-hi-ur-reading-input-52.jsonl').write_bytes(priority)
(ROOT/'input/full-field-reading-input-55.jsonl').write_bytes(expanded)
records=[]
for f in fields:
    key=f['occurrence_id'].removeprefix('deenhindi-');lang=f['language']
    text=sources[key]['source_record'][importer.LANGUAGE_FIELDS[lang]]
    assert text==f['text'] and sha(text.encode())==f['text_sha256'] and len(text)==f['characters'] and len(text.encode())==f['utf8_bytes']
    records.append({'occurrence_id':f['occurrence_id'],'language':lang,'source_field':importer.LANGUAGE_FIELDS[lang],
                    'characters':len(text),'utf8_bytes':len(text.encode()),'text_sha256':sha(text.encode()),
                    'complete_own_field_read':True,'primary_notes_or_candidate_inspected_before_reading':False,
                    'own_independent_source_first_note':NOTES[(key,lang)]})
receipt={'schema':'hadith-bank-independent-complete-source-first-reading-v1','source_commit':artifact['saved_head'],'source_cohort_sha256':sha(raw),'original_full_field_input_sha256':sha(expanded),'source_verification_sha256':sha((ROOT/'source-verification.json').read_bytes()),'own_notes_sha256':sha((ROOT/'independent_readings.py').read_bytes()),'full_fields_read':len(records),'characters_read':sum(f['characters'] for f in records),'utf8_bytes_read':sum(f['utf8_bytes'] for f in records),'primary_notes_or_candidate_inspected_before_freeze':False,'extra_sibling_scope':{'deenhindi-muslim:2725':['ar','en','ur-Latn']},'scope_hints_received_from_owner':True,'primary_candidate_or_primary_notes_opened_before_freeze':False,'source_http_requests':0,'github_writes':0,'records':records}
assert (receipt['full_fields_read'],receipt['characters_read'],receipt['utf8_bytes_read'])==(55,23149,48862)
(ROOT/'complete-independent-source-first-readings.json').write_bytes(enc(receipt))
print(json.dumps({'status':'FROZEN','receipt_sha256':sha((ROOT/'complete-independent-source-first-readings.json').read_bytes()),'source_verification_sha256':sha((ROOT/'source-verification.json').read_bytes()),'full_fields_read':55,'characters_read':23149,'utf8_bytes_read':48862,'source_files_reopened':52,'raw_reparses':26},indent=2))
