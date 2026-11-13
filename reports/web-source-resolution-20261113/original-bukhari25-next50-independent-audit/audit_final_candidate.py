"""Independent full477 native, exact amendment, source and queue preservation audit."""
from collections import Counter,defaultdict
from pathlib import Path
import copy,gzip,hashlib,json,sys

HERE=Path(__file__).resolve().parent
PRIMARY=HERE.parent/'phase20-original-bukhari25-hi-ur'
sys.path.insert(0,str(HERE.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
from verify_original_sources import verify as verify_sources
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=importer.json_bytes
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
fields=lambda r:{f['language']:f for f in r['fields']}
parent=lambda r:{k:v for k,v in r.items() if k!='fields'}
positions=lambda f:{p for s in f['selected_spans'] for p in range(s['start'],s['end'])}

def write_exact(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data,('Frozen audit output differs',str(path))
    else:path.write_bytes(data)

def leaves(v):
    if isinstance(v,dict):return sum(leaves(x) for x in v.values())
    if isinstance(v,list):return sum(leaves(x) for x in v)
    return 1

def normalize_version(v,stored,plain):
    n=copy.deepcopy(v);r=n['source']['manual_review']
    assert r['sha256']==stored and r['uncompressed_sha256']==plain
    r['sha256']='EXACT_STORED_LEDGER_HASH';r['uncompressed_sha256']='EXACT_PLAIN_LEDGER_HASH'
    return n

def normalize_record(r,stored,plain):
    n=copy.deepcopy(r)
    n['language_versions']=[normalize_version(v,stored,plain) for v in n['language_versions']]
    q=n['review']['source_bound_review'];assert q['sha256']==stored and q['uncompressed_sha256']==plain
    q['sha256']='EXACT_STORED_LEDGER_HASH';q['uncompressed_sha256']='EXACT_PLAIN_LEDGER_HASH'
    return n

def load_manifest(name,expected):
    raw=(PRIMARY/name).read_bytes();assert sha(raw)==expected
    m=json.loads(raw);files={f['path']:f for f in m['files']}
    assert len(files)==len(m['files'])
    for f in files.values():
        p=Path(f['local_path']);assert p.is_file() and not p.is_symlink()
        b=p.read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
        assert git(b)==f['git_blob_sha1']
    return raw,m,files

def current_file(files,suffix):
    candidates=[f for f in files.values() if f['path'].endswith('/'+suffix)
        and '/previous-' not in f['path'] and '/before-' not in f['path']
        and '/previous/' not in f['path'] and '/before/' not in f['path']]
    # The shortest path is the active derivative; immutable archived closures nest below it.
    candidates.sort(key=lambda f:(len(f['path'].split('/')),len(f['path'])))
    assert candidates,suffix
    if len(candidates)>1:assert len(candidates[0]['path'].split('/'))<len(candidates[1]['path'].split('/'))
    return Path(candidates[0]['local_path'])

def main(manifest_name,manifest_sha,active_sha):
    selected=json.loads((PRIMARY/'input/selection.json').read_bytes())
    assert selected['source_publication_commit']=='d369026ca42af6ff972ffab83c9180e03759da41'
    manifest_raw,manifest,files=load_manifest(manifest_name,manifest_sha)
    v1raw,v1manifest,v1files=load_manifest('delivery-manifest-v1.json','9f3b6612ee3dd871f47b2741f55570a07567554eb569807dfaa48b2663d35e51')
    active_path=selected['active_review_path'];baseline_path=selected['source_baseline_path']
    oldraw=(PRIMARY/'input/pinned'/active_path).read_bytes()
    baseline_raw=(PRIMARY/'input/pinned'/baseline_path).read_bytes()
    assert sha(oldraw)==selected['active_review_sha256']=='18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'
    assert sha(baseline_raw)==selected['source_baseline_sha256']=='5c9598c1c61cee509155013dde44221de2e17f11bd29d0f475092f2a6e86fb36'
    newraw=Path(files[active_path]['local_path']).read_bytes();assert sha(newraw)==active_sha
    v1active=Path(v1files[active_path]['local_path']).read_bytes()
    assert sha(v1active)=='14ae19f71bac85c74fa4652ca40d46c3a5f94d3d0e2dbdff7da0bb18a212c8e2'
    old={r['occurrence_id']:r for r in json.loads(gzip.decompress(oldraw))['records']}
    new={r['occurrence_id']:r for r in json.loads(gzip.decompress(newraw))['records']}
    v1={r['occurrence_id']:r for r in json.loads(gzip.decompress(v1active))['records']}
    sources=list(map(json.loads,gzip.decompress(baseline_raw).splitlines()))
    source_by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in sources}
    assert len(old)==len(new)==len(v1)==len(source_by_id)==477
    assert set(old)==set(new)==set(v1)==set(source_by_id)
    original_input=(HERE/'input/full-hi-ur-reading-input-50.jsonl').read_bytes()
    assert sha(original_input)=='5c204cde7e73d4195281c8681455016a4ddb635e847c28564cc84ab352b26a1c'
    readmap={(r['occurrence_id'],r['language']):r for r in map(json.loads,original_input.splitlines())}
    assert len(readmap)==50
    readreceipt=(HERE/'complete-independent-source-first-readings.json').read_bytes()
    assert sha(readreceipt)=='073b9eb372627f21dde24a7f2179449fdf92cd12e7c6bd7a55e544b1bd52f67a'
    assert json.loads(readreceipt)['primary_candidate_opened_before_receipt'] is False
    selected_ids={k[0] for k in readmap};assert len(selected_ids)==25
    proof=verify_sources();proof_raw=enc(proof)
    assert (HERE/'independent-source-verification.json').read_bytes()==proof_raw
    findings_raw=(HERE/'independent-boundary-findings-v1.json').read_bytes()
    assert sha(findings_raw)=='ecc345ed2f2c3f34316267769bef30ec7fedcea043001db70a7f9cae36f7d1a1'
    finding=json.loads(findings_raw)
    requested={(r['occurrence_id'],r['language']):r for r in finding['requested_source_mask_changes']}
    meta_key=('deenhindi-bukhari:1536','hi');amended=set(requested)|{meta_key}
    count=Counter();coverage=defaultdict(Counter);field_receipts=[]
    for oid,before in old.items():
        after=new[oid];first=v1[oid]
        assert parent(before)==parent(after)==parent(first),(oid,'parent decision/metadata changed')
        if oid not in selected_ids:
            assert before==after;count['untouched_full_parent_decisions_exact']+=1
        if oid not in {k[0] for k in amended}:
            assert first==after;count['v1_other_full_parent_decisions_exact']+=1
        om,nm,vm=fields(before),fields(after),fields(first);assert set(om)==set(nm)==set(vm)
        for lang,bf in om.items():
            key=(oid,lang);af=nm[lang];vf=vm[lang]
            if key not in readmap:
                assert bf==af;count['prior_other_field_definitions_exact']+=1
            else:
                r=readmap[key]
                assert bf['reviewed'] is False and bf['decision']=='unreviewed' and not bf['selected_spans']
                assert af['reviewed'] is True and af['review_scope']=='complete_current_language_field'
                assert af['text_sha256']==r['text_sha256'] and af['source_field']==r['source_field']
                assert af['chars_reviewed']==r['characters'] and af['bytes_reviewed']==r['utf8_bytes']
                assert af['selected_spans'] and af['speaker'] and af['report_type']
            if key not in amended:
                assert vf==af;count['v1_other_field_definitions_exact']+=1
            elif key in requested:
                req=requested[key];t=readmap[key]['text']
                assert t[req['start']:req['end']]==req['text']
                expected=req['expected_selected_spans_before_transparent_reason_refinement']
                strip=lambda ss:[{k:v for k,v in s.items() if k!='reason'} for s in ss]
                assert strip(af['selected_spans'])==strip(expected),(key,'unexpected final spans/labels')
                assert positions(vf)-positions(af)==set(range(req['start'],req['end']))
                assert not positions(af)-positions(vf)
                stable=lambda f:{k:v for k,v in f.items() if k not in ('selected_spans','reason','source_text_annotations','decision')}
                assert stable(vf)==stable(af),(key,'unrequested field metadata change')
                count['exact_mask_amended_fields']+=1
                count['characters_to_context']+=len(req['text']);count['utf8_bytes_to_context']+=len(req['text'].encode())
            else:
                assert key==meta_key
                strip=lambda f:{k:v for k,v in f.items() if k not in ('selected_spans','speaker','reason','source_text_annotations')}
                assert strip(vf)==strip(af)
                assert len(vf['selected_spans'])==len(af['selected_spans'])
                for a,b in zip(vf['selected_spans'],af['selected_spans']):
                    stable=lambda s:{k:v for k,v in s.items() if k not in ('speaker','reason')}
                    assert stable(a)==stable(b)
                assert 'अत' in af['speaker']
                assert 'अत' in next(s for s in af['selected_spans'] if s['component_id']=='hi-report-2')['speaker']
                count['metadata_only_source_name_refinements']+=1
    assert count['untouched_full_parent_decisions_exact']==452
    assert count['prior_other_field_definitions_exact']==2335
    assert count['v1_other_field_definitions_exact']==2378
    assert count['v1_other_full_parent_decisions_exact']==473
    assert count['exact_mask_amended_fields']==6 and count['metadata_only_source_name_refinements']==1
    assert count['characters_to_context']==89 and count['utf8_bytes_to_context']==179
    available={f['sha256'] for f in files.values()}
    assert sha(oldraw) in available and sha(v1active) in available and sha(v1raw) in available
    assert all(f['sha256'] in available for f in v1manifest['files'])
    engines=[]
    for label,data in [('native-before-final',oldraw),('native-after-final',newraw)]:
        stage=HERE/label;write_exact(stage/active_path,data);write_exact(stage/baseline_path,baseline_raw)
        engines.append(SourceReviews(stage,'deenhindi'))
    oldengine,newengine=engines
    oldplain=sha(gzip.decompress(oldraw));newplain=sha(gzip.decompress(newraw));dispositions=Counter()
    for saved in sources:
        oid='deenhindi-'+saved['collection']+':'+saved['number'];base=importer.canonical_record(saved);copybase=copy.deepcopy(base)
        before,ba=oldengine.apply(base,saved=saved);after,aa=newengine.apply(base,saved=saved)
        assert base==copybase and ba==aa==old[oid]['decision']==new[oid]['decision'];dispositions[aa]+=1
        assert old[oid]['source_record_sha256']==new[oid]['source_record_sha256']==sha(enc(saved['source_record']))
        for k,value in base.items():
            if k not in ('text','language_versions','review','extraction','content_kind'):
                assert after[k]==value,(oid,k);count['parent_metadata_leaf_equalities']+=leaves(value)
        assert after['review']['independent_pro_qc']=='not_performed' and after['review']['certified_release_eligible'] is False
        if oid not in selected_ids:
            assert normalize_record(before,sha(oldraw),oldplain)==normalize_record(after,sha(newraw),newplain)
            count['untouched_native_parent_outputs_exact_except_ledger_hashes']+=1
        bv={v['id']:v for v in before['language_versions']};av={v['id']:v for v in after['language_versions']}
        assert set(bv)==set(av)=={v['id'] for v in base['language_versions']}
        for original in base['language_versions']:
            lang=original['language'];key=(oid,lang);v=av[original['id']];ov=bv[original['id']]
            f=fields(new[oid])[lang];priorf=fields(old[oid])[lang];text=original['text']
            assert text==saved['source_record'][importer.LANGUAGE_FIELDS[lang]]
            for name in ('id','language','references','translation_provenance'):
                assert v[name]==original[name];count['language_metadata_leaf_equalities']+=leaves(original[name])
            assert v['script']==ov['script'];count['prior_native_script_values_exact']+=1
            if priorf.get('observed_script'):
                assert f['observed_script']==priorf['observed_script'] and f['source_script_note']==priorf['source_script_note']
                count['prior_explicit_script_corrections_exact']+=1
            for name,value in original['source'].items():
                assert v['source'][name]==value;count['language_source_metadata_leaf_equalities']+=leaves(value)
            assert v['source']['source_text_sha256']==sha(text.encode())
            pieces=[];spans=f['selected_spans']
            for s in spans:
                a,b=s['start'],s['end'];assert a<b and s['sha256']==sha(text[a:b].encode())
                pieces.append((a,b,text[a:b]))
            assert v['text']==(''.join(text[s['start']:s['end']] for s in spans) if spans else None)
            for c in v['comments']:
                a,b=c['source_span'];assert c['scope']=='source_context_not_narration'
                assert c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode())
                pieces.append((a,b,c['text']))
            cursor=0
            for a,b,piece in sorted(pieces):assert cursor==a and a<b and piece==text[a:b];cursor=b
            assert cursor==len(text) and ''.join(x[2] for x in sorted(pieces))==text
            count['lossless_source_field_partitions']+=1
            if key not in readmap:
                assert normalize_version(ov,sha(oldraw),oldplain)==normalize_version(v,sha(newraw),newplain)
                count['other_native_field_outputs_exact_except_ledger_hashes']+=1
            else:
                assert text==readmap[key]['text'];c=coverage[lang]
                c['complete_fields_read']+=1;c['characters_read']+=len(text);c['utf8_bytes_read']+=len(text.encode())
                c['admitted_fields']+=bool(spans);c['selected_spans']+=len(spans);c['context_gaps']+=len(v['comments'])
                c['selected_characters']+=len(v['text'] or '');c['selected_utf8_bytes']+=len((v['text'] or '').encode())
                classes=v['source']['report_component_classifications'];families={r['source_report_family_id'] for r in classes}
                assert classes and all(r['speaker_description'] and r['report_type'] for r in classes) and None not in families
                if len(spans)>1:assert v['source']['source_report_count']==len(families)
                else:assert len(classes)==len(families)==1 and 'source_report_count' not in v['source']
                field_receipts.append({'occurrence_id':oid,'language':lang,'source_text_sha256':sha(text.encode()),
                    'final_field_decision_sha256':sha(enc(f)),'selected_spans':spans,'context_gaps':len(v['comments']),
                    'selected_characters':len(v['text'] or ''),'component_count':len(classes),
                    'report_family_count':len(families),'lossless_partition_verified':True})
    oldengine.finish();newengine.finish()
    assert count['lossless_source_field_partitions']==2385 and count['other_native_field_outputs_exact_except_ledger_hashes']==2335
    assert count['prior_explicit_script_corrections_exact']==19 and count['untouched_native_parent_outputs_exact_except_ledger_hashes']==452
    oqraw=(PRIMARY/'input/pinned'/selected['canonical_queue_path']).read_bytes()
    assert sha(oqraw)==selected['canonical_queue_sha256']=='74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
    nqraw=current_file(files,'candidate-priority-field-queue.jsonl.gz').read_bytes()
    ol=gzip.decompress(oqraw).splitlines(keepends=True);nl=gzip.decompress(nqraw).splitlines(keepends=True)
    assert nl==[line for line in ol if json.loads(line)['id'] not in selected_ids]
    oq=list(map(json.loads,ol));nq=list(map(json.loads,nl))
    op={(r['id'],f['language']) for r in oq for f in r['fields']};np={(r['id'],f['language']) for r in nq for f in r['fields']}
    assert op-np==set(readmap) and not np-op
    assert len(oq)==3379 and len(nq)==3354 and len(op)==6361 and len(np)==6311
    languages=dict(Counter(f['language'] for r in nq for f in r['fields']));assert languages=={'hi':3260,'ur':3051}
    assert selected['canonical_queue_path'] not in files
    delta=json.loads(current_file(files,'field-decision-delta.json').read_bytes())
    qdelta=json.loads(current_file(files,'priority-field-queue-delta.json').read_bytes())
    assert len(delta)==50 and qdelta['removed_fields']==delta
    assert {(r['occurrence_id'],r['language']) for r in delta}==set(readmap)
    for r in delta:
        oid,lang=r['occurrence_id'],r['language'];bf=fields(old[oid])[lang];af=fields(new[oid])[lang]
        assert r['before_field_decision_sha256']==sha(enc(bf)) and r['after_field_decision_sha256']==sha(enc(af))
        assert r['before_decision']==bf['decision'] and r['after_decision']==af['decision']
        assert r['source_text_sha256']==readmap[(oid,lang)]['text_sha256']
        assert r['source_record_sha256']==sha(enc(source_by_id[oid]['source_record']))
    assert qdelta['before_sha256']==sha(oqraw) and qdelta['after_sha256']==sha(nqraw)
    assert qdelta['before_fields']==6361 and qdelta['after_fields']==6311
    assert set(qdelta['removed_occurrence_ids'])==selected_ids
    report={'schema':'hadith-bank-independent-original-language-extension-final-v2-audit','result':'PASS',
        'source_commit':selected['source_publication_commit'],'primary_manifest_sha256':sha(manifest_raw),
        'primary_active_sha256':sha(newraw),'primary_v1_manifest_sha256':sha(v1raw),'primary_v1_active_sha256':sha(v1active),
        'primary_manifest_files_rehashed':len(files),'primary_manifest_bytes_rehashed':sum(f['bytes'] for f in files.values()),
        'all_v1_payloads_and_manifest_archived_by_exact_hash':True,'prior_published_active_sha256':sha(oldraw),
        'full477_source_baseline_sha256':sha(baseline_raw),'independent_source_first_receipt_sha256':sha(readreceipt),
        'independent_source_verification_sha256':sha(proof_raw),'independent_boundary_findings_sha256':sha(findings_raw),
        'full477_before_after_native_apply_finish':'PASS','all477_parent_dispositions_unchanged':True,
        'parent_dispositions':dict(dispositions),'counts':dict(count),'field_coverage':{k:dict(v) for k,v in coverage.items()},
        'amendment':{'exact_source_mask_fields':6,'metadata_only_Hindi_name_fields':1,'characters_to_context':89,
            'utf8_bytes_to_context':179,'newly_added_source_positions':0,'unrequested_source_position_changes':0,
            'component_types_and_report_families_unchanged':True,'original_initial_notes_preserved':True},
        'queue':{'before_sha256':sha(oqraw),'candidate_sha256':sha(nqraw),'before_pending_fields':6361,
            'before_occurrences':3379,'removed_fields':50,'removed_occurrences':25,'remaining_fields':6311,
            'remaining_occurrences':3354,'remaining_by_language':languages,'all_remaining_line_bytes_and_order_exact':True,
            'field_delta_and_nested_queue_delta_bind_final_decisions_and_actions':True,
            'canonical_queue_not_in_primary_manifest':True,'publication_status':'candidate only; publisher owns promotion'},
        'native_receipt_comparison':'Only the two expected stored/plain ledger hash values at manual_review and source_bound_review receipts were normalized after verifying their original literal hashes; all other values remained compared.',
        'source_files_independently_reopened':50,'complete_raw_reparses':25,'field_receipts':field_receipts,
        'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed',
        'importer_sha256':sha(Path(importer.__file__).read_bytes()),
        'review_engine_sha256':sha(Path(sys.modules['web_source_reviews'].__file__).read_bytes())}
    out=HERE/'independent-final-v2-audit.json';write_exact(out,enc(report))
    print(json.dumps({'result':'PASS','path':str(out),'sha256':sha(out.read_bytes()),'counts':dict(count),
        'field_coverage':report['field_coverage'],'queue':report['queue']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    assert len(sys.argv)==4,'manifest_name manifest_sha active_sha'
    main(*sys.argv[1:])
