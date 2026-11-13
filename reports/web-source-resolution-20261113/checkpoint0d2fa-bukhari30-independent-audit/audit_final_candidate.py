"""Independent exact-amendment, native-engine and complete-source preservation gate."""
import collections
import copy
import gzip
import hashlib
import json
import sys
from pathlib import Path
from verify_original_sources import verify as verify_original_sources

ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase21-checkpoint0d2fa-bukhari30-review'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

sha=lambda value:hashlib.sha256(value).hexdigest()
git=lambda value:hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
leaf=lambda value:sum(leaf(v) for v in value.values()) if isinstance(value,dict) and value else sum(leaf(v) for v in value) if isinstance(value,list) and value else 1
fields_of=lambda row:row.get('field_reviews',row.get('fields'))
spans_of=lambda field:field.get('spans',field.get('selected_spans',[]))
identity=lambda row:row.get('id',row.get('occurrence_id'))

manifest_path=Path(sys.argv[1]).resolve()
assert manifest_path.parent==PRIMARY and manifest_path.name=='delivery-manifest-v2.json'
manifest_bytes=manifest_path.read_bytes();assert sha(manifest_bytes)==sys.argv[2]
manifest=json.loads(manifest_bytes)
before_manifest_bytes=(PRIMARY/'delivery-manifest-v1.json').read_bytes()
assert sha(before_manifest_bytes)=='70a0fce9c10f36d47163672f3d636ca82668a65d04055c6c853c807a9ba16fc6'
before_manifest=json.loads(before_manifest_bytes)

def verify_manifest(value):
    assert len({f['path'] for f in value['files']})==len(value['files'])
    for item in value['files']:
        data=Path(item['local_path']).read_bytes()
        assert len(data)==item['bytes'] and sha(data)==item['sha256'],item['path']
        if item.get('git_blob_sha1'):assert git(data)==item['git_blob_sha1']

verify_manifest(manifest);verify_manifest(before_manifest)
active_path='imports/web-deenhindi-20261112/reviews/source-review-checkpoint0d2fa-bukhari30-20261113.json.gz'
active_entry=lambda value:next(f for f in value['files'] if f['path']==active_path)
entry=active_entry(manifest);old_entry=active_entry(before_manifest)
active_bytes=Path(entry['local_path']).read_bytes();assert sha(active_bytes)==sys.argv[3]
old_bytes=Path(old_entry['local_path']).read_bytes()
assert sha(old_bytes)=='1e08c967257c0a21bc5525130801bac71af357ba97400af21345ad30e1e94f08'
active=json.loads(gzip.decompress(active_bytes));old=json.loads(gzip.decompress(old_bytes))
after_by_id={identity(r):r for r in active['records']}
before_by_id={identity(r):r for r in old['records']}
source_rows=[json.loads(line) for line in (ROOT/'input/cohort.jsonl').read_bytes().splitlines()]
source_by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in source_rows}
assert set(source_by_id)==set(after_by_id)==set(before_by_id) and len(source_rows)==30
own_bytes=(ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(own_bytes)=='409323a027fd5c7bc3c745d82e1b394ceaf976b788d11c0a6c1d833161eb08e7'
own=json.loads(own_bytes)
own_fields={(x['occurrence_id'],x['language']):x for x in own['fields']}
assert sha((ROOT/'independent_source_first_notes.py').read_bytes())==own['notes_sha256']=='93123c07b4bfa303f5e333da4ac5862c47fe27a31d282e3e0b502b5dd2f751a2'
findings_bytes=(ROOT/'independent-boundary-findings-v1.json').read_bytes()
assert sha(findings_bytes)=='22f9399f491002af777824cacea81ffd4c4dbc033611d98bfdff59f89818e753'
findings=json.loads(findings_bytes)
assessed={(x['occurrence_id'],x['language']):x for x in findings['fields']}
requests={(x['occurrence_id'],x['language']):x for x in findings['requested_amendments']}
assert len(assessed)==63 and len(requests)==2
root=Path(entry['local_path'])
for _ in Path(entry['path']).parts:root=root.parent
assert root.name=='publish-v2'
source_ledger=root/active['source_ledger_path']
assert sha(source_ledger.read_bytes())==active['source_ledger_sha256']
assert [json.loads(line) for line in gzip.decompress(source_ledger.read_bytes()).splitlines()]==source_rows
assert {k:v for k,v in active.items() if k!='records'}=={k:v for k,v in old.items() if k!='records'}

# Every original v1 payload must survive inside the final portable package,
# either at its identical repository path or at an explicit versioned archive.
archives=[]
for previous in before_manifest['files']:
    matches=[item for item in manifest['files'] if item['sha256']==previous['sha256'] and item['bytes']==previous['bytes']]
    assert matches,('missing durable v1 payload',previous['path'])
    archives.append({'original_path':previous['path'],'sha256':previous['sha256'],
                     'final_paths':[item['path'] for item in matches]})
assert any(item['sha256']==sha(before_manifest_bytes) for item in manifest['files'])

counts=collections.Counter();by_language=collections.defaultdict(collections.Counter)
checks=[];amendments=[]
engine=SourceReviews(root,'deenhindi')
for saved in source_rows:
    oid='deenhindi-'+saved['collection']+':'+saved['number']
    before=before_by_id[oid];decision=after_by_id[oid]
    assert before['decision']==decision['decision']=='register'
    changed_parent=oid=='deenhindi-bukhari:2597'
    if not changed_parent:
        assert decision==before;counts['unchanged_whole_v1_parents']+=1
    else:
        assert {k:v for k,v in decision.items() if k not in ('field_reviews','fields','reason')}=={k:v for k,v in before.items() if k not in ('field_reviews','fields','reason')}
    base=importer.canonical_record(saved);original=copy.deepcopy(base)
    result,action=engine.apply(base,saved=saved)
    assert base==original and action==decision['decision']
    assert decision['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
    for key,value in original.items():
        if key not in ('text','language_versions','review','extraction','content_kind','report_types'):
            assert result.get(key)==value,(oid,key)
            counts['parent_metadata_leaf_equalities']+=leaf(value)
    assert result['review']['independent_pro_qc']=='not_performed' and result['review']['certified_release_eligible'] is False
    assert result['number']['canonical'] is None
    assert len(original['language_versions'])==len(result['language_versions'])==len(fields_of(decision))==len(fields_of(before))==5
    admitted={};field_checks=[]
    for initial,version,field,prior in zip(original['language_versions'],result['language_versions'],fields_of(decision),fields_of(before)):
        language=initial['language'];text=initial['text'];key=(oid,language);spans=spans_of(field);parts=[]
        assert text and isinstance(text,str)
        assert version['id']==initial['id']==field.get('language_version_id',field.get('version_id'))
        assert field['language']==language and text==saved['source_record'][field['source_field']]
        assert field['text_sha256']==sha(text.encode()) and field['text_chars']==len(text)
        assert bool(field['reviewed'])==(key in own_fields)
        assert 'observed_script' not in field and 'observed_script' not in prior
        if key not in requests:
            assert field==prior,(key,'unexpected field change')
            counts['unchanged_v1_complete_field_definitions']+=1
            if key in assessed:assert sha(enc(field))==assessed[key]['complete_candidate_field_definition_sha256']
        else:
            request=requests[key]
            assert sha(enc(prior))==request['before_complete_field_definition_sha256']
            assert {k:v for k,v in field.items() if k not in ('spans','selected_spans','reason','action','decision')}=={k:v for k,v in prior.items() if k not in ('spans','selected_spans','reason','action','decision')}
            assert [[s['start'],s['end']] for s in spans]==request['expected_final_selected_ranges']
            old_mask={i for span in spans_of(prior) for i in range(span['start'],span['end'])}
            new_mask={i for span in spans for i in range(span['start'],span['end'])}
            start,end=request['range'];assert new_mask-old_mask==set(range(start,end)) and not old_mask-new_mask
            for span in spans:
                for k,value in request['unchanged_component_metadata'].items():assert span[k]==value
            counts['restored_characters']+=len(new_mask-old_mask)
            counts['restored_utf8_bytes']+=len(text[start:end].encode())
            counts['amended_reviewed_fields']+=1
            amendments.append({'occurrence_id':oid,'language':language,'restored_span':[start,end],
                'literal':text[start:end],'before_field_sha256':sha(enc(prior)),
                'after_field_sha256':sha(enc(field)),'all_existing_component_labels_unchanged':True})
        if field['reviewed']:
            reading=own_fields[key]
            assert reading['source_text_sha256']==field['text_sha256'] and reading['characters']==len(text) and reading['utf8_bytes']==len(text.encode())
            assert field['chars_reviewed']==len(text) and field['bytes_reviewed']==len(text.encode())
            assert [[s['start'],s['end']] for s in spans]==assessed[key]['expected_final_ranges']
            for counter in (counts,by_language[language]):
                counter['complete_fields_read']+=1;counter['characters_read']+=len(text);counter['utf8_bytes_read']+=len(text.encode())
        else:
            assert not spans and field['chars_reviewed']==field['bytes_reviewed']==0
            counts['unread_context_fields']+=1
        for k,value in initial.items():
            if k not in ('text','source','comments','scope','quotation_status'):
                assert version.get(k)==value,(key,k)
                counts['language_metadata_leaf_equalities']+=leaf(value)
        for k,value in initial['source'].items():
            assert version['source'].get(k)==value,(key,'source',k)
            counts['source_metadata_leaf_equalities']+=leaf(value)
        if spans:
            assert field['reviewed'] and version['text']==''.join(text[s['start']:s['end']] for s in spans)
            admitted[language]=version['text']
            for span in spans:
                a,b=span['start'],span['end'];assert sha(text[a:b].encode())==span['sha256']
                parts.append((a,b,text[a:b]));assert span['report_type'] and span['speaker'] and span['source_report_family_id']
            for counter in (counts,by_language[language]):
                counter['admitted_fields']+=1;counter['selected_spans']+=len(spans)
                counter['selected_characters']+=len(version['text']);counter['selected_utf8_bytes']+=len(version['text'].encode())
            for component in version['source']['report_component_classifications']:
                members=[s for s in spans if s['component_id']==component['component_id']]
                assert component['spans']==[[s['start'],s['end']] for s in members]
                assert all(s['speaker']==component['speaker_description'] and s['report_type']==component['report_type'] and s['source_report_family_id']==component['source_report_family_id'] for s in members)
                counts['typed_source_components']+=1
        else:
            assert version['text'] is None
            if field['reviewed']:counts['fully_read_context_only_fields']+=1
        assert not initial.get('comments')
        for comment in version['comments']:
            a,b=comment['source_span'];assert comment['text']==text[a:b] and sha(text[a:b].encode())==comment['source_text_sha256']
            assert comment['scope']=='source_context_not_narration';parts.append((a,b,comment['text']))
        cursor=0
        for a,b,value in sorted(parts):
            assert a==cursor and a<b and text[a:b]==value;cursor=b
        assert cursor==len(text) and ''.join(value for a,b,value in sorted(parts))==text
        counts['lossless_partitions']+=1
        if field['reviewed']:counts['reviewed_context_gaps']+=len(version['comments'])
        field_checks.append({'language':language,'source_sha256':sha(text.encode()),'reviewed':field['reviewed'],
            'selected_spans':len(spans),'source_context_parts':len(version['comments']),'lossless':True})
    if oid=='deenhindi-bukhari:2603':
        assert set(admitted)=={'ar','en'} and result['text']=={'arabic':admitted['ar'],'translation':None}
        assert admitted['en']==saved['source_record']['translationEnglish']
        assert not admitted['en'].endswith('"')
    else:
        assert set(admitted)=={'hi','ur'} and result['text']=={'arabic':None,'translation':admitted['hi']}
    counts[action+'_occurrences']+=1
    checks.append({'occurrence_id':oid,'decision':action,'fields':field_checks})
engine.finish()
assert counts['register_occurrences']==30 and counts['lossless_partitions']==150
assert counts['complete_fields_read']==63 and counts['admitted_fields']==60
assert counts['fully_read_context_only_fields']==3 and counts['unread_context_fields']==87
assert counts['characters_read']==37985 and counts['utf8_bytes_read']==81545
assert counts['restored_characters']==26 and counts['restored_utf8_bytes']==52
assert counts['amended_reviewed_fields']==2 and counts['unchanged_v1_complete_field_definitions']==148 and counts['unchanged_whole_v1_parents']==29
source_proof_bytes=(ROOT/'independent-source-verification.json').read_bytes()
assert sha(source_proof_bytes)=='2e74f16316d288a96628db13ecd65b2f310237dc3caea62a6d734197af316330'
assert enc(verify_original_sources())==source_proof_bytes
verify_manifest(manifest);verify_manifest(before_manifest)
report={'schema':'hadith-bank-independent-complete-review-amendment-audit-v2','result':'PASS',
    'source_commit':'0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a','reviewer':'OpenAI assistant /root/queue_audit',
    'source_first_reading_receipt_sha256':sha(own_bytes),'independent_source_verification_sha256':sha(source_proof_bytes),
    'complete_boundary_findings_sha256':sha(findings_bytes),
    'primary_manifest_v1_sha256':sha(before_manifest_bytes),'active_v1_sha256':sha(old_bytes),
    'primary_manifest_v2_sha256':sha(manifest_bytes),'active_v2_sha256':sha(active_bytes),
    'all_frozen_primary_payload_hashes_verified':len(manifest['files']),
    'native_SourceReviews_apply_finish':'PASS','all30_parent_source_metadata_and_dispositions_preserved':True,
    'counts':dict(counts),'language_coverage':{k:dict(v) for k,v in by_language.items()},
    'exact_two_field_amendments':amendments,'all28_v1_payloads_durably_preserved':archives,
    'source_files_reopened':60,'complete_raw_reparses':30,
    'initial_notes_preserved_with_additive_refinements':True,
    'explicit_source_based_refinements':findings['explicit_source_based_refinements'],
    '2603_arabic_english_only_and_primary_hindi_null':True,
    'source_wording_changes':0,'original_source_metadata_changes':0,'candidate_mutations':0,
    'source_http_requests':0,'github_writes':0,'canonical_identity_asserted':False,
    'independent_pro_qc':'not_performed','open_findings':[],'checks':checks,
    'code_inputs':{'import_deenhindi':sha(Path(importer.__file__).read_bytes()),
                   'web_source_reviews':sha(Path(sys.modules['web_source_reviews'].__file__).read_bytes())}}
target=ROOT/'independent-final-v2-audit.json';data=enc(report)
if target.exists():assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({'result':'PASS','report_sha256':sha(data),'bytes':len(data),
    'primary_manifest':sha(manifest_bytes),'active':sha(active_bytes),'counts':dict(counts)},indent=2))
