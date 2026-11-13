"""Independent exact amendment, native metadata and lossless-partition audit."""
from pathlib import Path
import collections, copy, gzip, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase15-checkpoint0639-bukhari43-review'
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
sha=lambda data:hashlib.sha256(data).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
leaf=lambda value:sum(leaf(x) for x in value.values()) if isinstance(value,dict) and value else sum(leaf(x) for x in value) if isinstance(value,list) and value else 1
v1_bytes=(PRIMARY/'delivery-manifest-v1.json').read_bytes()
assert sha(v1_bytes)=='1c2418b2dcd475e247f0fcd2228d1fa29dee631075105bc5b5cc091af01889b5'
v2_path=PRIMARY/'delivery-manifest-v2.json'
v2_bytes=v2_path.read_bytes();v1=json.loads(v1_bytes);v2=json.loads(v2_bytes)

def verify_manifest(manifest):
    assert len({f['path'] for f in manifest['files']})==len(manifest['files'])
    for f in manifest['files']:
        data=Path(f['local_path']).read_bytes()
        assert len(data)==f['bytes'] and sha(data)==f['sha256']
        if f.get('git_blob_sha1'):
            assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==f['git_blob_sha1']

verify_manifest(v1);verify_manifest(v2)
old_entry=next(f for f in v1['files'] if '/source-review-' in f['path'])
new_entry=next(f for f in v2['files'] if '/source-review-' in f['path'])
assert old_entry['path']==new_entry['path']
old_bytes=Path(old_entry['local_path']).read_bytes();new_bytes=Path(new_entry['local_path']).read_bytes()
assert sha(old_bytes)=='9e0a2ec1579c489087a8229db97d2d8c56a977b546e08a26f0f9bbea898832bc'
before=json.loads(gzip.decompress(old_bytes));after=json.loads(gzip.decompress(new_bytes))
original_rows=[json.loads(line) for line in (PRIMARY/'input/cohort.jsonl').read_bytes().splitlines()]
source_by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in original_rows}
source_first_bytes=(ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(source_first_bytes)=='ab201199a8051fe974e19c296ba71a4738309901ee8c33956a4009fa58dbc6bb'
source_first=json.loads(source_first_bytes)
own_fields={(r['occurrence_id'],r['language']):r for r in source_first['records']}
findings_bytes=(ROOT/'independent-boundary-findings-v1.json').read_bytes()
assert sha(findings_bytes)=='231dbdb85b2b6d2a4d9b9b85fd4fa7eb3cf20cd1b2692ad3c7c2162223f5ea1f'
findings=json.loads(findings_bytes)
expected={(r['occurrence_id'],r['language']):r for r in findings['requested_changes']}
assert len(expected)==7
fields_of=lambda row:row.get('field_reviews',row.get('fields'))
identity=lambda row:row.get('id',row.get('occurrence_id'))
spans_of=lambda field:field.get('spans',field.get('selected_spans',[]))
positions=lambda field:{i for s in spans_of(field) for i in range(s['start'],s['end'])}
old_by_id={identity(r):r for r in before['records']};new_by_id={identity(r):r for r in after['records']}
assert set(old_by_id)==set(new_by_id)==set(source_by_id) and len(new_by_id)==43
changes=[];unchanged_parents=unchanged_fields=0
for oid,old in old_by_id.items():
    new=new_by_id[oid]
    assert {k:v for k,v in old.items() if k not in ('reason','field_reviews','fields')}=={k:v for k,v in new.items() if k not in ('reason','field_reviews','fields')}
    if old==new:unchanged_parents+=1
    for prior,field in zip(fields_of(old),fields_of(new)):
        key=(oid,field['language'])
        if prior==field:unchanged_fields+=1;assert key not in expected;continue
        assert key in expected
        requested=expected[key];text=source_by_id[oid]['source_record'][field['source_field']]
        assert sha(text.encode())==requested['source_text_sha256']
        a,b=requested['start'],requested['end']
        assert text[a:b]==requested['text'] and sha(text[a:b].encode())==requested['sha256']
        old_mask,new_mask=positions(prior),positions(field)
        add,cut=new_mask-old_mask,old_mask-new_mask
        if requested['requested_disposition']=='selected':assert add==set(range(a,b)) and not cut
        else:assert cut==set(range(a,b)) and not add
        for k in ('language_version_id','version_id','language','source_field','text_sha256','text_chars','reviewed','chars_reviewed','bytes_reviewed'):
            assert prior.get(k)==field.get(k)
        def voices(f):
            return {i:(s.get('component_id'),s.get('report_type'),s.get('speaker'),s.get('source_report_family_id'))
                    for s in spans_of(f) for i in range(s['start'],s['end'])}
        old_voice,new_voice=voices(prior),voices(field)
        assert all(old_voice[i]==new_voice[i] for i in old_mask&new_mask)
        if oid=='deenhindi-bukhari:2244':
            added_spans=[s for s in spans_of(field) if s['start']==533 and s['end']==591]
            assert len(added_spans)==1
            span=added_spans[0]
            assert span['source_report_family_id']=='deenhindi-bukhari:2244:report-2'
            assert any(word in span['speaker'].lower() for word in ('unknown','unnamed','unidentified'))
            assert not set(range(516,533))&new_mask
        changes.append({'occurrence_id':oid,'language':field['language'],
                        'before_field_sha256':sha(enc(prior)),'after_field_sha256':sha(enc(field)),
                        'added_positions':len(add),'removed_positions':len(cut),
                        'retained_position_attribution_exact':True,'requested_span':requested})
assert len(changes)==7 and unchanged_fields==208 and unchanged_parents==39
assert sum(c['added_positions'] for c in changes)==84
assert sum(c['removed_positions'] for c in changes)==204

root=Path(new_entry['local_path'])
for _ in Path(new_entry['path']).parts:root=root.parent
assert root.name=='publish-v2'
source_ledger=root/after['source_ledger_path']
assert sha(source_ledger.read_bytes())==after['source_ledger_sha256']
assert [json.loads(line) for line in gzip.decompress(source_ledger.read_bytes()).splitlines()]==original_rows
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
    else:assert saved['number']=='2239.2' and not admitted and all(f['reviewed'] for f in fields_of(decision))
    counts[action+'_occurrences']+=1;checks.append({'occurrence_id':oid,'decision':action,'fields':field_checks})
engine.finish()
assert counts['register_occurrences']==42 and counts['exclude_occurrences']==1
assert counts['lossless_partitions']==215 and counts['complete_fields_read']==89 and counts['admitted_fields']==84
assert counts['unread_context_fields']==126 and counts['fully_read_context_only_fields']==5
assert counts['characters_read']==47262 and counts['utf8_bytes_read']==101769
verify_manifest(v1);verify_manifest(v2)
source_proof_bytes=(ROOT/'independent-source-verification.json').read_bytes()
assert sha(source_proof_bytes)=='4c85745a2f0f5d6c63951fbd2d00658865fb0416a8c025d8963dbbd994b6af0f'
report={'schema':'hadith-bank-independent-complete-review-audit-v2','result':'PASS',
    'source_commit':'0639af7fd15786284b4c413fced77e38eec8825a','reviewer':'OpenAI assistant /root/queue_audit',
    'source_first_reading_receipt_sha256':sha(source_first_bytes),'independent_source_verification_sha256':sha(source_proof_bytes),
    'original_findings_sha256':sha(findings_bytes),'primary_manifest_v1_sha256':sha(v1_bytes),'primary_manifest_v2_sha256':sha(v2_bytes),
    'active_v1_sha256':sha(old_bytes),'active_v2_sha256':sha(new_bytes),
    'all_v1_payloads_still_exact':True,'all_v2_payload_hashes_verified':True,
    'native_SourceReviews_apply_finish':'PASS','all43_parent_source_metadata_and_dispositions_preserved':True,
    'unchanged_whole_parents':39,'unchanged_field_definitions':208,'exact_amendments':changes,
    'counts':dict(counts),'language_coverage':{k:dict(v) for k,v in by_language.items()},
    'source_only_id':'deenhindi-bukhari:2239.2','source_only_all5_fields_read':True,
    'all86_source_files_reopened_and43_raw_reparses':True,'source_metadata_changes':0,'source_wording_changes':0,
    'independent_pro_qc':'not_performed','canonical_identity_asserted':False,
    'source_http_requests':0,'github_writes':0,'open_findings':[],
    'checks':checks,
    'code_inputs':{'import_deenhindi':sha(Path(importer.__file__).read_bytes()),'web_source_reviews':sha(Path(sys.modules['web_source_reviews'].__file__).read_bytes())}}
dest=ROOT/'independent-final-v2-audit.json';data=enc(report)
assert not dest.exists();dest.write_bytes(data)
print(json.dumps({'result':'PASS','report_sha256':sha(data),'bytes':len(data),'primary_v2_manifest':sha(v2_bytes),
                  'active_v2':sha(new_bytes),'counts':dict(counts)},indent=2))
