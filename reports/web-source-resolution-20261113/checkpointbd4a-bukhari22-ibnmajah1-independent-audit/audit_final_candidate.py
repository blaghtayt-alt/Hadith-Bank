"""Independent native, complete-field boundary and immutable-source audit of phase18 v1."""
from pathlib import Path
import collections,copy,gzip,hashlib,json,sys
from verify_original_sources import verify as verify_original_sources
ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase18-checkpointbd4a-bukhari-ibnmajah23-review'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
sha=lambda data:hashlib.sha256(data).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
leaf=lambda value:sum(leaf(x) for x in value.values()) if isinstance(value,dict) and value else sum(leaf(x) for x in value) if isinstance(value,list) and value else 1
manifest_bytes=(PRIMARY/'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_bytes)=='946a522840b2c5351b7cb0015810c3079513b6a15d935867ae37f48701b4910c'
manifest=json.loads(manifest_bytes)

def verify_manifest():
    assert len({f['path'] for f in manifest['files']})==len(manifest['files'])==15
    for f in manifest['files']:
        data=Path(f['local_path']).read_bytes()
        assert len(data)==f['bytes'] and sha(data)==f['sha256']
        if f.get('git_blob_sha1'):assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==f['git_blob_sha1']

verify_manifest()
entry=next(f for f in manifest['files'] if '/source-review-' in f['path'])
active_bytes=Path(entry['local_path']).read_bytes()
assert sha(active_bytes)=='4bfcfdbe8e401dadcda9e9a684dc70a83d3e7f35eefdeb597791cb9b60c4b98c'
after=json.loads(gzip.decompress(active_bytes))
original_rows=[json.loads(line) for line in (ROOT/'input/cohort.jsonl').read_bytes().splitlines()]
source_by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in original_rows}
source_first_bytes=(ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(source_first_bytes)=='db201784656c54aa1d5049c2097566adfdff15de02876dbc4dfae4fddcc0dd38'
source_first=json.loads(source_first_bytes)
own_fields={(r['occurrence_id'],r['language']):r for r in source_first['records']}
assessment_bytes=(ROOT/'independent-boundary-assessment-v1.json').read_bytes()
assert sha(assessment_bytes)=='3c40ddef7805006d63bf81ee9c6eed2ae5dc4403ae6fe58c591a62cb310fc4db'
assessment=json.loads(assessment_bytes)
assert assessment['requested_amendments']==[] and len(assessment['fields'])==46
accepted={(x['occurrence_id'],x['language']):x for x in assessment['fields']}
fields_of=lambda row:row.get('field_reviews',row.get('fields'))
identity=lambda row:row.get('id',row.get('occurrence_id'))
spans_of=lambda field:field.get('spans',field.get('selected_spans',[]))
new_by_id={identity(r):r for r in after['records']}
assert set(new_by_id)==set(source_by_id) and len(new_by_id)==23
for oid,record in new_by_id.items():
    for field in fields_of(record):
        key=(oid,field['language'])
        if field['reviewed']:
            assert sha(enc(field))==accepted[key]['final_candidate_field_sha256']
        else:assert key not in accepted
root=Path(entry['local_path'])
for _ in Path(entry['path']).parts:root=root.parent
assert root.name=='publish-v1'
source_ledger=root/after['source_ledger_path']
assert sha(source_ledger.read_bytes())==after['source_ledger_sha256']
assert [json.loads(line) for line in gzip.decompress(source_ledger.read_bytes()).splitlines()]==original_rows
source_proof_bytes=(ROOT/'independent-source-verification.json').read_bytes()
assert sha(source_proof_bytes)=='182e830b968f76f86a391e558d41b52d57e8690d6b2278aa9449548f5e554e05'
assert enc(verify_original_sources())==source_proof_bytes
engine=SourceReviews(root,'deenhindi')
counts=collections.Counter();by_language=collections.defaultdict(collections.Counter);checks=[]
for saved in original_rows:
    oid='deenhindi-'+saved['collection']+':'+saved['number'];decision=new_by_id[oid]
    base=importer.canonical_record(saved);original=copy.deepcopy(base)
    result,action=engine.apply(base,saved=saved)
    assert base==original and action==decision['decision']
    assert decision['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))
    for key,value in original.items():
        if key not in ('text','language_versions','review','extraction','content_kind','report_types'):
            assert result.get(key)==value,(oid,key)
            counts['parent_metadata_leaf_equalities']+=leaf(value)
    assert result['review']['independent_pro_qc']=='not_performed' and not result['review']['certified_release_eligible']
    assert result['number']['canonical'] is None
    assert len(original['language_versions'])==len(result['language_versions'])==len(fields_of(decision))==5
    admitted={};field_checks=[]
    for old,version,field in zip(original['language_versions'],result['language_versions'],fields_of(decision)):
        lang=old['language'];text=old['text'];spans=spans_of(field);parts=[]
        assert version['id']==old['id']==field.get('language_version_id',field.get('version_id'))
        assert field['language']==lang and text==saved['source_record'][field['source_field']]
        assert field['text_sha256']==sha(text.encode()) and field['text_chars']==len(text)
        assert bool(field['reviewed'])==((oid,lang) in own_fields)
        if field['reviewed']:
            own=own_fields[oid,lang]
            assert own['text_sha256']==field['text_sha256'] and own['characters']==len(text) and own['utf8_bytes']==len(text.encode())
            assert field['chars_reviewed']==len(text) and field['bytes_reviewed']==len(text.encode())
            for counter in (counts,by_language[lang]):
                counter['complete_fields_read']+=1;counter['characters_read']+=len(text);counter['utf8_bytes_read']+=len(text.encode())
        else:
            assert not spans and field['chars_reviewed']==field['bytes_reviewed']==0
            counts['unread_context_fields']+=1
        for key,value in old.items():
            if key not in ('text','source','comments','scope','quotation_status'):
                assert version.get(key)==value,(oid,lang,key)
                counts['language_metadata_leaf_equalities']+=leaf(value)
        for key,value in old['source'].items():
            assert version['source'].get(key)==value,(oid,lang,'source',key)
            counts['source_metadata_leaf_equalities']+=leaf(value)
        if spans:
            assert field['reviewed'] and version['text']==''.join(text[s['start']:s['end']] for s in spans)
            admitted[lang]=version['text']
            for span in spans:
                a,b=span['start'],span['end'];assert sha(text[a:b].encode())==span['sha256'];parts.append((a,b,text[a:b]))
                assert span['report_type'] and span['speaker'] and span['source_report_family_id']
            for counter in (counts,by_language[lang]):
                counter['admitted_fields']+=1;counter['selected_spans']+=len(spans)
                counter['selected_characters']+=len(version['text']);counter['selected_utf8_bytes']+=len(version['text'].encode())
            for classification in version['source']['report_component_classifications']:
                own_spans=[s for s in spans if s['component_id']==classification['component_id']]
                assert classification['spans']==[[s['start'],s['end']] for s in own_spans]
                assert all(s['speaker']==classification['speaker_description'] and s['report_type']==classification['report_type'] and s['source_report_family_id']==classification['source_report_family_id'] for s in own_spans)
        else:
            assert version['text'] is None
            if field['reviewed']:counts['fully_read_context_only_fields']+=1
        assert not old.get('comments')
        for comment in version['comments']:
            a,b=comment['source_span'];assert comment['text']==text[a:b] and sha(text[a:b].encode())==comment['source_text_sha256']
            assert comment['scope']=='source_context_not_narration';parts.append((a,b,comment['text']))
        cursor=0
        for a,b,value in sorted(parts):assert a==cursor and a<b and text[a:b]==value;cursor=b
        assert cursor==len(text) and ''.join(value for a,b,value in sorted(parts))==text
        counts['lossless_partitions']+=1
        if field['reviewed']:counts['reviewed_context_gaps']+=len(version['comments'])
        field_checks.append({'language':lang,'source_sha256':sha(text.encode()),'reviewed':field['reviewed'],
                             'selected_spans':len(spans),'comments':len(version['comments']),'lossless':True})
    if action=='register':assert set(admitted)=={'hi','ur'} and result['text']=={'arabic':None,'translation':admitted['hi']}
    else:raise AssertionError('No parent is source-only in this reviewed cohort.')
    counts[action+'_occurrences']+=1;checks.append({'occurrence_id':oid,'decision':action,'fields':field_checks})
engine.finish()
assert counts['register_occurrences']==23 and counts['exclude_occurrences']==0
assert counts['lossless_partitions']==115 and counts['complete_fields_read']==46 and counts['admitted_fields']==46
assert counts['unread_context_fields']==69 and counts['fully_read_context_only_fields']==0
assert counts['characters_read']==32677 and counts['utf8_bytes_read']==70504
assert counts['selected_spans']==70 and counts['reviewed_context_gaps']==21
verify_manifest()
report={'schema':'hadith-bank-independent-complete-review-audit-v1','result':'PASS',
    'source_commit':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633','reviewer':'OpenAI assistant /root/queue_audit',
    'source_first_reading_receipt_sha256':sha(source_first_bytes),'independent_source_verification_sha256':sha(source_proof_bytes),
    'complete_boundary_assessment_sha256':sha(assessment_bytes),'primary_manifest_v1_sha256':sha(manifest_bytes),
    'active_v1_sha256':sha(active_bytes),'all15_frozen_primary_payload_hashes_verified':True,
    'native_SourceReviews_apply_finish':'PASS','all23_parent_source_metadata_and_dispositions_preserved':True,
    'counts':dict(counts),'language_coverage':{k:dict(v) for k,v in by_language.items()},
    'source_only_ids':[],'all46_source_files_reopened_and23_raw_reparses':True,
    'independent_first_pass_notes_preserved_with_explicit_later_refinements':True,
    'explicit_refinements':assessment['explicit_refinements'],
    'source_metadata_changes':0,'source_wording_changes':0,'candidate_mutations':0,
    'independent_pro_qc':'not_performed','canonical_identity_asserted':False,
    'source_http_requests':0,'github_writes':0,'open_findings':[],'checks':checks,
    'code_inputs':{'import_deenhindi':sha(Path(importer.__file__).read_bytes()),'web_source_reviews':sha(Path(sys.modules['web_source_reviews'].__file__).read_bytes())}}
dest=ROOT/'independent-final-v1-audit.json';data=enc(report)
assert not dest.exists();dest.write_bytes(data)
print(json.dumps({'result':'PASS','report_sha256':sha(data),'bytes':len(data),'primary_manifest':sha(manifest_bytes),
                  'active':sha(active_bytes),'counts':dict(counts)},indent=2))
