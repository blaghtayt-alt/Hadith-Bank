"""Freeze the exact two-field amendment and retain every v1 payload byte."""
from pathlib import Path
import copy,gzip,hashlib,json

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
OUT=ROOT/'publish-v2'
EVID=Path('imports/web-deenhindi-20261112/reviews/field-expansions/20261113-original-bukhari25-50-hindi-urdu-v1')
BEFORE=EVID/'independent-boundary-amendment-v2'
assert not (ROOT/'delivery-manifest-v2.json').exists()
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b
    else:p.write_bytes(b)
def mask(field):return {i for s in field['selected_spans'] for i in range(s['start'],s['end'])}
def classes(field):return {i:(s['component_id'],s['report_type'],s['speaker'],s['source_report_family_id']) for s in field['selected_spans'] for i in range(s['start'],s['end'])}

old_manifest_raw=(ROOT/'delivery-manifest-v1.json').read_bytes()
assert sha(old_manifest_raw)=='2c6584f7ec87532a5345163af8ff5c60c736b41275a8e683eb1cfe853965f848'
old_manifest=json.loads(old_manifest_raw)
draft=json.loads((ROOT/'draft-delivery-manifest-v2.json').read_bytes())
selection=json.loads((ROOT/'input/selection.json').read_bytes())
active_path=selection['active_review_path']
old_raw=(ROOT/'publish-v1'/active_path).read_bytes();new_raw=(OUT/active_path).read_bytes()
assert sha(old_raw)=='c069236c43adbb00cd1c62214372a71353959fc58ccd8f9ecb985e263436a7b2'
assert sha(new_raw)=='18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'
before=json.loads(gzip.decompress(old_raw));after=json.loads(gzip.decompress(new_raw))
assert len(before['records'])==len(after['records'])==477
source={r['language']:r for r in map(json.loads,(ROOT/'input/full-hi-ur-reading-input-50.jsonl').read_bytes().splitlines()) if r['number']=='1467'}
expected={'hi':(224,241,'(अपने पहले खावंद)'), 'ur':(217,236,'( اپنے پہلے خاوند )')}
changes=[];unchanged_fields=unchanged_rows=0
for old,new in zip(before['records'],after['records']):
    ident=old['occurrence_id'];assert ident==new['occurrence_id']
    assert {k:v for k,v in old.items() if k!='fields'}=={k:v for k,v in new.items() if k!='fields'}
    if ident!='deenhindi-bukhari:1467':assert old==new;unchanged_rows+=1
    for prior,field in zip(old['fields'],new['fields']):
        if prior==field:unchanged_fields+=1;continue
        language=prior['language'];assert ident=='deenhindi-bukhari:1467' and language in expected
        start,end,literal=expected[language];text=source[language]['text']
        assert text[start:end]==literal
        prior_mask,new_mask=mask(prior),mask(field)
        assert not prior_mask-new_mask and new_mask-prior_mask==set(range(start,end))
        pc,nc=classes(prior),classes(field)
        assert all(pc[i]==nc[i] for i in prior_mask)
        assert len(set(nc.values()))==1 and set(pc.values())==set(nc.values())
        for name in ['version_id','language','source_field','field_path','text_sha256','text_chars','reviewed','chars_reviewed','bytes_reviewed','review_scope','review_extension_id','review_method','report_type','speaker','independent_pro_qc']:
            assert prior[name]==field[name]
        assert field['decision']=='whole' and prior['decision']=='excerpts'
        changes.append({'occurrence_id':ident,'language':language,'full_field_sha256':sha(text.encode()),
            'source_record_sha256':old['source_record_sha256'],'restored_range':[start,end],
            'restored_text':literal,'restored_sha256':sha(literal.encode()),
            'restored_characters':len(literal),'restored_utf8_bytes':len(literal.encode()),
            'removed_selected_characters':0,'before_field_sha256':sha(enc(prior)),
            'after_field_sha256':sha(enc(field)),'component_type_speaker_and_family_unchanged':True})
assert len(changes)==2 and unchanged_fields==2383 and unchanged_rows==476
assert sum(x['restored_characters'] for x in changes)==36 and sum(x['restored_utf8_bytes'] for x in changes)==75
assert before['field_review_extensions'][:-1]==after['field_review_extensions'][:-1]
assert {k:v for k,v in before.items() if k not in ['records','field_review_extensions']}=={k:v for k,v in after.items() if k not in ['records','field_review_extensions']}
old_notes=json.loads(gzip.decompress((ROOT/'publish-v1'/EVID/'complete-field-reading-notes.json.gz').read_bytes()))
new_notes=json.loads(gzip.decompress((OUT/EVID/'complete-field-reading-notes.json.gz').read_bytes()))
for a,b in zip(old_notes['fields'],new_notes['fields']):
    assert a['occurrence_id']==b['occurrence_id'] and a['language']==b['language']
    assert a['source_first_note_unchanged']==b['source_first_note_unchanged']
    assert a['language_specific_note_unchanged']==b['language_specific_note_unchanged']
    if a['occurrence_id']!='deenhindi-bukhari:1467':assert a==b
assert (ROOT/'publish-v1'/EVID/'candidate-priority-field-queue.jsonl.gz').read_bytes()==(OUT/EVID/'candidate-priority-field-queue.jsonl.gz').read_bytes()
delta=json.loads((OUT/EVID/'priority-field-queue-delta.json').read_bytes())
new_fields={(r['occurrence_id'],f['language']):f for r in after['records'] for f in r['fields']}
assert len(delta['removed_fields'])==50
for row in delta['removed_fields']:
    field=new_fields[(row['occurrence_id'],row['language'])]
    assert row['after_field_decision_sha256']==sha(enc(field)) and row['after_decision']==field['decision']

findings_path=WORK/'phase17-original-bukhari25-independent-audit/independent-boundary-findings-v1.json'
findings_raw=findings_path.read_bytes()
assert sha(findings_raw)=='3329baca9ec9275c696d9ec5d2c63ad582d006788c5d8e3b25ca4d83da2404fe'
archive=[]
for item in old_manifest['files']:
    data=Path(item['local_path']).read_bytes()
    assert len(data)==item['bytes'] and sha(data)==item['sha256'] and git(data)==item['git_blob_sha1']
    path=BEFORE/'previous-v1-payload'/item['path'];put(OUT/path,data)
    archive.append({'original_path':item['path'],'archived_path':str(path),
        'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)})
assert len(archive)==18
put(OUT/BEFORE/'previous-delivery-manifest-v1.json',old_manifest_raw)
put(OUT/BEFORE/'independent-boundary-findings-v1.json',findings_raw)
put(OUT/EVID/'finalize_v2.py',Path(__file__).read_bytes())
report={'schema':'hadith-bank-exact-independent-boundary-amendment-v1','status':'PASS','revision':'phase17-v2',
    'source_commit':selection['source_publication_commit'],'before_active_sha256':sha(old_raw),
    'after_active_sha256':sha(new_raw),'before_delivery_manifest_sha256':sha(old_manifest_raw),
    'independent_findings_sha256':sha(findings_raw),
    'explicit_refinement':'The initial biographical-gloss interpretation of the former-husband parentheses is refined: these first-person words inside Umm Salamah question materially supply former marital relationship and temporal participant scope. Naming Abu Salamah and saying the children are hers do not supply that relationship. Restore the exact two literal ranges in the same report component/family; preserve the initial notes and v1 before evidence.',
    'exact_changes':changes,'restored_characters':36,'restored_utf8_bytes':75,'removed_characters':0,
    'unchanged_other_field_decisions_vs_v1':unchanged_fields,'unchanged_whole_parents_vs_v1':unchanged_rows,
    'unchanged_other_extended_fields_vs_v1':48,'all477_parent_decisions_and_source_metadata_unchanged':True,
    'before_and_after_original477_native_validation':'PASS','full_lossless_partitions':2385,
    'actual_reading_coverage_unchanged':{'hi':25,'ur':25,'characters':40338,'utf8_bytes':86636},
    'queue_candidate_bytes_equal_v1':True,'all50_queue_delta_after_field_hashes_and_actions_rechecked':True,
    'remaining_priority_fields':6361,'remaining_priority_occurrences':3379,
    'all18_v1_payload_files_and_manifest_rehashed_unchanged':True,'before_payload_archive':archive,
    'independent_pro_qc':'not_performed','github_writes':0,'source_site_requests':0}
put(OUT/BEFORE/'amendment-receipt.json',enc(report))
files=[]
for path in sorted(p for p in OUT.rglob('*') if p.is_file()):
    data=path.read_bytes();files.append({'path':str(path.relative_to(OUT)),'local_path':str(path),
        'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)})
portable={'schema':'hadith-bank-original-field-extension-portable-manifest-v1','revision':'v2',
    'source_commit':selection['source_publication_commit'],'active_path':active_path,
    'active_sha256':sha(new_raw),'amendment_receipt_sha256':sha(enc(report)),
    'files':[{k:v for k,v in item.items() if k!='local_path'} for item in files]}
portable_raw=enc(portable);portable_path=EVID/'portable-manifest.json';put(OUT/portable_path,portable_raw)
files.append({'path':str(portable_path),'local_path':str(OUT/portable_path),'bytes':len(portable_raw),
    'sha256':sha(portable_raw),'git_blob_sha1':git(portable_raw)})
manifest={k:v for k,v in draft.items() if k not in ['files','total_files','total_bytes']}
manifest.update(revision='v2',files=files,total_files=len(files),total_bytes=sum(f['bytes'] for f in files),
    amendment_receipt_sha256=sha(enc(report)),active_ledger_path=active_path,active_ledger_sha256=sha(new_raw))
put(ROOT/'delivery-manifest-v2.json',enc(manifest))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),'active_sha256':sha(new_raw),
    'files':len(files),'bytes':manifest['total_bytes'],'amendment_receipt_sha256':sha(enc(report)),
    'exact_restored_characters':36,'exact_restored_utf8_bytes':75,
    'unchanged_other_fields':unchanged_fields,'unchanged_whole_parents':unchanged_rows},indent=2))
