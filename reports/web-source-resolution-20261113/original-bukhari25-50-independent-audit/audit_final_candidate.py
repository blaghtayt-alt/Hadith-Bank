"""Independent exact amendment, full477 native preservation and queue binding audit."""
from collections import Counter, defaultdict
from pathlib import Path
import copy, gzip, hashlib, json, sys

HERE=Path(__file__).resolve().parent
PRIMARY=HERE.parent/'phase17-original-bukhari25-hi-ur'
sys.path.insert(0,str(HERE.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

sha=lambda b:hashlib.sha256(b).hexdigest()
enc=importer.json_bytes
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
fieldmap=lambda r:{f['language']:f for f in r['fields']}
parent=lambda r:{k:v for k,v in r.items() if k!='fields'}
positions=lambda f:{p for s in f['selected_spans'] for p in range(s['start'],s['end'])}

def write_exact(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data,('immutable audit output',str(path))
    else:path.write_bytes(data)

def leaves(v):
    if isinstance(v,dict):return sum(leaves(x) for x in v.values())
    if isinstance(v,list):return sum(leaves(x) for x in v)
    return 1

def normalized_version(version,stored_hash,plain_hash):
    result=copy.deepcopy(version)
    receipt=result['source']['manual_review']
    assert receipt['sha256']==stored_hash and receipt['uncompressed_sha256']==plain_hash
    receipt['sha256']='EXACT_ACTIVE_LEDGER_STORED_HASH'
    receipt['uncompressed_sha256']='EXACT_ACTIVE_LEDGER_PLAIN_HASH'
    return result

def normalized_record(record,stored_hash,plain_hash):
    result=copy.deepcopy(record)
    result['language_versions']=[normalized_version(v,stored_hash,plain_hash) for v in result['language_versions']]
    receipt=result['review']['source_bound_review']
    assert receipt['sha256']==stored_hash and receipt['uncompressed_sha256']==plain_hash
    receipt['sha256']='EXACT_ACTIVE_LEDGER_STORED_HASH'
    receipt['uncompressed_sha256']='EXACT_ACTIVE_LEDGER_PLAIN_HASH'
    return result

def read_manifest(name,expected):
    raw=(PRIMARY/name).read_bytes();assert sha(raw)==expected
    doc=json.loads(raw);listed={f['path']:f for f in doc['files']}
    assert len(listed)==len(doc['files'])
    for f in listed.values():
        data=Path(f['local_path']).read_bytes()
        assert sha(data)==f['sha256'] and len(data)==f['bytes']
    return raw,doc,listed

def main(manifest_name,manifest_sha,expected_active_sha):
    out=HERE/'independent-final-v2-audit.json'
    assert not out.exists(),'Refusing to replace frozen final audit'
    selection=json.loads((HERE/'input/selection.json').read_bytes())
    pin=selection['source_publication_commit']
    manifest_raw,manifest,listed=read_manifest(manifest_name,manifest_sha)
    v1raw,v1manifest,v1files=read_manifest('delivery-manifest-v1.json','2c6584f7ec87532a5345163af8ff5c60c736b41275a8e683eb1cfe853965f848')
    active_path=selection['active_review_path'];baseline_path=selection['source_baseline_path']
    old_raw=(PRIMARY/'input/pinned'/active_path).read_bytes()
    baseline_raw=(PRIMARY/'input/pinned'/baseline_path).read_bytes()
    assert sha(old_raw)=='ac53483e3eab6c0a4c508c86180c75091792e895b5e29f602a061aa2cd080c62'
    assert sha(baseline_raw)=='5c9598c1c61cee509155013dde44221de2e17f11bd29d0f475092f2a6e86fb36'
    new_raw=Path(listed[active_path]['local_path']).read_bytes();assert sha(new_raw)==expected_active_sha
    v1_active=Path(v1files[active_path]['local_path']).read_bytes()
    assert sha(v1_active)=='c069236c43adbb00cd1c62214372a71353959fc58ccd8f9ecb985e263436a7b2'
    old_doc=json.loads(gzip.decompress(old_raw));new_doc=json.loads(gzip.decompress(new_raw));v1_doc=json.loads(gzip.decompress(v1_active))
    old={r['occurrence_id']:r for r in old_doc['records']};new={r['occurrence_id']:r for r in new_doc['records']};v1={r['occurrence_id']:r for r in v1_doc['records']}
    sources=[json.loads(x) for x in gzip.decompress(baseline_raw).splitlines()]
    by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in sources}
    assert len(old)==len(new)==len(v1)==len(by_id)==477 and set(old)==set(new)==set(v1)==set(by_id)
    read_raw=(HERE/'complete-independent-source-first-readings.json').read_bytes()
    assert sha(read_raw)=='f44c6f4d353e5f2e8e0de2ddfd74e1f0ca0dd21406d9420b9c95ca78c978807c'
    readings=json.loads(read_raw)['fields'];readmap={(r['occurrence_id'],r['language']):r for r in readings}
    assert len(readmap)==50
    selected_ids={oid for oid,lang in readmap};assert len(selected_ids)==25
    findings_raw=(HERE/'independent-boundary-findings-v1.json').read_bytes()
    assert sha(findings_raw)=='3329baca9ec9275c696d9ec5d2c63ad582d006788c5d8e3b25ca4d83da2404fe'
    findings=json.loads(findings_raw)
    requests={(r['occurrence_id'],r['language']):r for r in findings['requested_changes']}
    counts=Counter();coverage=defaultdict(Counter);field_receipts=[]
    for oid,before in old.items():
        after=new[oid]
        assert parent(before)==parent(after)==parent(v1[oid]),(oid,'parent mutation')
        if oid not in selected_ids:
            assert before==after;counts['untouched_parent_records_exact']+=1
        om,nm,vm=fieldmap(before),fieldmap(after),fieldmap(v1[oid])
        assert set(om)==set(nm)==set(vm)
        for lang,bf in om.items():
            af=nm[lang];vf=vm[lang];key=(oid,lang)
            if key not in readmap:
                assert bf==af;counts['previous_other_explicit_field_definitions_exact']+=1
            else:
                r=readmap[key]
                assert bf['reviewed'] is False and bf['decision']=='unreviewed' and not bf['selected_spans']
                assert af['reviewed'] is True and af['review_scope']=='complete_current_language_field'
                assert af['text_sha256']==r['text_sha256']
                assert af['chars_reviewed']==r['characters'] and af['bytes_reviewed']==r['utf8_bytes']
                assert af['selected_spans']
            if key not in requests:
                assert vf==af;counts['v1_other_field_definitions_exact']+=1
            else:
                req=requests[key];old_pos,new_pos=positions(vf),positions(af)
                assert new_pos-old_pos==set(range(req['start'],req['end'])) and not old_pos-new_pos
                text=by_id[oid]['source_record'][af['source_field']]
                assert text[req['start']:req['end']]==req['text']
                def voices(f):
                    return {p:tuple(s[k] for k in ('component_id','source_report_family_id','report_type','speaker'))
                            for s in f['selected_spans'] for p in range(s['start'],s['end'])}
                vbefore,vafter=voices(vf),voices(af)
                assert all(vafter[p]==value for p,value in vbefore.items())
                target=tuple(vf['selected_spans'][0][k] for k in ('component_id','source_report_family_id','report_type','speaker'))
                assert all(vafter[p]==target for p in new_pos-old_pos)
                assert af['speaker']==vf['speaker'] and af['report_type']==vf['report_type']
                counts['exact_requested_amended_fields']+=1
                counts['restored_characters']+=len(new_pos-old_pos)
                counts['restored_utf8_bytes']+=len(req['text'].encode())
        if oid!='deenhindi-bukhari:1467':assert v1[oid]==after;counts['v1_other_parent_records_exact']+=1
    assert counts['untouched_parent_records_exact']==452
    assert counts['previous_other_explicit_field_definitions_exact']==2335
    assert counts['v1_other_field_definitions_exact']==2383
    assert counts['v1_other_parent_records_exact']==476
    assert counts['exact_requested_amended_fields']==2 and counts['restored_characters']==36 and counts['restored_utf8_bytes']==75
    available_hashes={f['sha256'] for f in listed.values()}
    assert sha(old_raw) in available_hashes and sha(v1_active) in available_hashes and sha(v1raw) in available_hashes
    assert all(f['sha256'] in available_hashes for f in v1manifest['files']), 'Complete immutable v1 payload closure must be preserved'
    stages=[]
    for name,raw in [('native-before-final',old_raw),('native-after-final',new_raw)]:
        stage=HERE/name
        write_exact(stage/active_path,raw);write_exact(stage/baseline_path,baseline_raw)
        stages.append(SourceReviews(stage,'deenhindi'))
    old_engine,new_engine=stages
    old_plain_sha=sha(gzip.decompress(old_raw));new_plain_sha=sha(gzip.decompress(new_raw))
    dispositions=Counter()
    for saved in sources:
        oid='deenhindi-'+saved['collection']+':'+saved['number']
        baseline=importer.canonical_record(saved);unchanged=copy.deepcopy(baseline)
        before,ba=old_engine.apply(baseline,saved=saved);after,aa=new_engine.apply(baseline,saved=saved)
        assert baseline==unchanged
        assert ba==aa==old[oid]['decision']==new[oid]['decision'];dispositions[aa]+=1
        assert old[oid]['source_record_sha256']==new[oid]['source_record_sha256']==sha(enc(saved['source_record']))
        for k,value in baseline.items():
            if k not in ('text','language_versions','review','extraction','content_kind'):
                assert after[k]==value,(oid,k)
                counts['parent_metadata_leaf_equalities']+=leaves(value)
        assert after['review']['independent_pro_qc']=='not_performed'
        assert after['review']['certified_release_eligible'] is False
        old_normal=normalized_record(before,sha(old_raw),old_plain_sha)
        new_normal=normalized_record(after,sha(new_raw),new_plain_sha)
        if oid not in selected_ids:
            assert old_normal==new_normal,(oid,'untouched complete native record differs beyond receipt hashes')
            counts['untouched_native_parent_outputs_exact_except_two_ledger_hashes']+=1
        old_versions={v['id']:v for v in before['language_versions']}
        new_versions={v['id']:v for v in after['language_versions']}
        assert set(old_versions)==set(new_versions)=={v['id'] for v in baseline['language_versions']}
        om,nm=fieldmap(old[oid]),fieldmap(new[oid])
        for original in baseline['language_versions']:
            lang=original['language'];key=(oid,lang);version=new_versions[original['id']];old_version=old_versions[original['id']]
            f=nm[lang];text=original['text']
            assert text==saved['source_record'][importer.LANGUAGE_FIELDS[lang]]
            for name in ('id','language','references','translation_provenance'):
                assert version[name]==original[name];counts['language_metadata_leaf_equalities']+=leaves(original[name])
            assert version['script']==old_version['script'];counts['prior_native_script_values_exact']+=1
            if om[lang].get('observed_script'):
                assert f['observed_script']==om[lang]['observed_script']
                assert f['source_script_note']==om[lang]['source_script_note']
                counts['prior_explicit_script_corrections_exact']+=1
            for name,value in original['source'].items():
                assert version['source'][name]==value,(oid,lang,name)
                counts['language_source_metadata_leaf_equalities']+=leaves(value)
            assert version['source']['source_text_sha256']==sha(text.encode())
            spans=f['selected_spans'];pieces=[]
            for span in spans:
                a,b=span['start'],span['end'];assert a<b and span['sha256']==sha(text[a:b].encode())
                pieces.append((a,b,text[a:b]))
            assert version['text']==(''.join(text[s['start']:s['end']] for s in spans) if spans else None)
            for context in version['comments']:
                a,b=context['source_span'];assert context['scope']=='source_context_not_narration'
                assert context['text']==text[a:b] and context['source_text_sha256']==sha(text[a:b].encode())
                pieces.append((a,b,context['text']))
            cursor=0
            for a,b,piece in sorted(pieces):
                assert cursor==a and a<b and piece==text[a:b],(oid,lang,'partition')
                cursor=b
            assert cursor==len(text) and ''.join(x[2] for x in sorted(pieces))==text
            counts['lossless_full_source_field_partitions']+=1
            if key not in readmap:
                assert normalized_version(old_version,sha(old_raw),old_plain_sha)==normalized_version(version,sha(new_raw),new_plain_sha)
                counts['other_native_field_outputs_exact_except_two_ledger_hashes']+=1
            else:
                assert text==readmap[key]['text']
                c=coverage[lang];c['complete_fields_read']+=1;c['characters_read']+=len(text);c['utf8_bytes_read']+=len(text.encode())
                c['admitted_fields']+=bool(spans);c['selected_spans']+=len(spans);c['context_gaps']+=len(version['comments'])
                c['selected_characters']+=len(version['text'] or '');c['selected_utf8_bytes']+=len((version['text'] or '').encode())
                classes=version['source'].get('report_component_classifications',[])
                assert classes and all(x['speaker_description'] and x['report_type'] for x in classes)
                families={x['source_report_family_id'] for x in classes}
                assert None not in families
                if len(spans)>1:
                    assert version['source']['source_report_count']==len(families)
                else:
                    assert len(classes)==len(families)==1
                    assert 'source_report_count' not in version['source']
                field_receipts.append({'occurrence_id':oid,'language':lang,'source_text_sha256':sha(text.encode()),
                    'final_field_decision_sha256':sha(enc(f)), 'selected_spans':len(spans),
                    'context_gaps':len(version['comments']),'selected_characters':len(version['text'] or ''),
                    'component_count':len(classes),'report_family_count':len(families),
                    'lossless_partition_verified':True})
    old_engine.finish();new_engine.finish()
    assert counts['lossless_full_source_field_partitions']==2385
    assert counts['other_native_field_outputs_exact_except_two_ledger_hashes']==2335
    assert counts['prior_explicit_script_corrections_exact']==19
    old_queue=(PRIMARY/'input/pinned'/selection['canonical_queue_path']).read_bytes()
    queue_item=next(f for f in listed.values() if f['path'].endswith('/candidate-priority-field-queue.jsonl.gz') and '/independent-boundary-amendment' not in f['path'])
    new_queue=Path(queue_item['local_path']).read_bytes()
    old_lines=gzip.decompress(old_queue).splitlines(keepends=True);new_lines=gzip.decompress(new_queue).splitlines(keepends=True)
    assert new_lines==[line for line in old_lines if json.loads(line)['id'] not in selected_ids]
    oq=[json.loads(x) for x in old_lines];nq=[json.loads(x) for x in new_lines]
    before_pairs={(r['id'],f['language']) for r in oq for f in r['fields']};after_pairs={(r['id'],f['language']) for r in nq for f in r['fields']}
    assert before_pairs-after_pairs==set(readmap) and not after_pairs-before_pairs
    assert len(oq)==3404 and len(nq)==3379 and len(before_pairs)==6411 and len(after_pairs)==6361
    assert selection['canonical_queue_path'] not in listed,'Canonical queue publication remains publisher-owned'
    def current_suffix(suffix):
        candidates=[f for f in listed.values() if f['path'].endswith('/'+suffix) and '/independent-boundary-amendment' not in f['path']]
        assert len(candidates)==1,(suffix,[x['path'] for x in candidates])
        return json.loads(Path(candidates[0]['local_path']).read_bytes())
    delta=current_suffix('field-decision-delta.json');queue_delta=current_suffix('priority-field-queue-delta.json')
    assert len(delta)==50 and queue_delta['removed_fields']==delta
    assert {(r['occurrence_id'],r['language']) for r in delta}==set(readmap)
    for row in delta:
        oid,lang=row['occurrence_id'],row['language'];bf=fieldmap(old[oid])[lang];af=fieldmap(new[oid])[lang]
        assert row['before_field_decision_sha256']==sha(enc(bf)) and row['after_field_decision_sha256']==sha(enc(af))
        assert row['before_decision']==bf['decision'] and row['after_decision']==af['decision']
        assert row['source_text_sha256']==readmap[(oid,lang)]['text_sha256']
        assert row['source_record_sha256']==sha(enc(by_id[oid]['source_record']))
    assert queue_delta['before_sha256']==sha(old_queue) and queue_delta['after_sha256']==sha(new_queue)
    assert queue_delta['before_fields']==6411 and queue_delta['after_fields']==6361
    assert set(queue_delta['removed_occurrence_ids'])==selected_ids
    report={'schema':'hadith-bank-independent-original-language-expansion-final-v2-audit', 'result':'PASS',
        'source_commit':pin,'primary_manifest_sha256':sha(manifest_raw),'primary_active_sha256':sha(new_raw),
        'primary_v1_manifest_sha256':sha(v1raw),'primary_v1_active_sha256':sha(v1_active),
        'primary_manifest_files_rehashed':len(listed),'primary_manifest_bytes_rehashed':sum(f['bytes'] for f in listed.values()),
        'all_v1_payloads_and_manifest_preserved_by_hash_in_final_package':True,
        'prior_published_active_sha256':sha(old_raw),'prior_full477_source_baseline_sha256':sha(baseline_raw),
        'prior_exact_compressed_active_preserved':True,
        'independent_source_first_reading_receipt_sha256':sha(read_raw),
        'independent_source_verification_sha256':sha((HERE/'independent-source-verification.json').read_bytes()),
        'independent_boundary_findings_sha256':sha(findings_raw),
        'full_native_before_and_after_apply_finish':'PASS','full_ledger_occurrences':477,
        'all477_parent_dispositions_unchanged':True,'parent_dispositions':dict(dispositions),
        'counts':dict(counts),'complete_reading_coverage':{k:dict(v) for k,v in coverage.items()},
        'amendment':{'only_occurrence':'deenhindi-bukhari:1467','fields':['hi','ur'],
            'restored_characters':36,'restored_utf8_bytes':75,'removed_positions':0,
            'actual_former_spouse_scope_restored_in_same_components_and_families':True,
            'all_prior_selected_position_voices_and_types_unchanged':True},
        'scope_decisions':'All50 actual candidate fields were independently read; exact final v2 accepts only the requested two-field restoration, with the explicit refinements archived in the immutable findings receipt. No other candidate boundary or speaker changes are authorized by this report.',
        'queue':{'before_sha256':sha(old_queue),'candidate_sha256':sha(new_queue),
            'before_pending_fields':6411,'before_occurrences':3404,'removed_fields':50,'removed_occurrences':25,
            'remaining_fields':6361,'remaining_occurrences':3379,
            'remaining_by_language':dict(Counter(f['language'] for r in nq for f in r['fields'])),
            'all_remaining_json_line_bytes_and_order_exact':True,
            'field_delta_and_copied_queue_delta_match_final_active_hashes_and_actions':True,
            'canonical_queue_not_in_primary_manifest':True,'publication_status':'candidate only; publisher owns composition'},
        'field_receipts':field_receipts,
        'source_files_reopened_and_verified':50,'complete_raw_reparses':25,
        'native_receipt_normalization':'Only source.manual_review and review.source_bound_review stored/uncompressed active-ledger hashes were normalized for before/after equality. Every expected literal hash was asserted first; no other values were ignored.',
        'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed',
        'importer_sha256':sha(Path(importer.__file__).read_bytes()),
        'review_engine_sha256':sha(Path(sys.modules['web_source_reviews'].__file__).read_bytes())}
    write_exact(out,enc(report))
    print(json.dumps({'result':'PASS','path':str(out),'sha256':sha(out.read_bytes()),'counts':dict(counts),
        'coverage':report['complete_reading_coverage'],'queue':report['queue']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    assert len(sys.argv)==4,'manifest_name manifest_sha active_sha'
    main(*sys.argv[1:])
