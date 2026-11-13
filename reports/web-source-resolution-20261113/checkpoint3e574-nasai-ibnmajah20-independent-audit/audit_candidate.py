"""Independent native and surgical audit against the forty source-first readings."""
from pathlib import Path
import argparse, collections, copy, gzip, hashlib, json, sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
OWNER=WORK/'phase19-checkpoint3e574-nasai-ibnmajah20-review'
CENTRAL=WORK/'phase18-successor-acquisition-monitor/held-evidence'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint3e574-nasai-ibnmajah20-20261113.json.gz'
PIN='3e574b9e7e4dd7cf8bc23232249004a18692c61c'
OLD_SHA='ecaa9e8e077b2a55e64288e6b10adb63af69f3c64b56d4fddd32eaa1542316e1'
READING_SHA='088d0cf7ca63c5c4daecfa21dc2ef7823d9f95e096f650674b76785a2b333f08'
FINDING_SHA='7e3fd736813bc75a70909a72de203bd9a233f2756a7225d0b33919ef20e315ae'
FIELDS={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews


def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def bind(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('immutable output mismatch',str(p))
    else:p.write_bytes(b)
def leaves(x):
    if isinstance(x,dict):return sum(leaves(v) for v in x.values())
    if isinstance(x,list):return sum(leaves(v) for v in x)
    return 1
def equal(a,b):assert a==b;return leaves(a)
def mask(text,spans):
    result=[False]*len(text);cursor=0
    for span in spans:
        a,b=span['start'],span['end']
        assert cursor<=a<b<=len(text) and sha(text[a:b].encode())==span['sha256']
        result[a:b]=[True]*(b-a);cursor=b
    return result


def audit(args):
    reading_path=HERE/'complete-independent-source-first-readings.json'
    assert sha(reading_path.read_bytes())==READING_SHA
    reading=read(reading_path)
    assert not reading['candidate_inspected'] and not reading['author_semantic_notes_inspected']
    read_fields={(r['occurrence_id'],r['language']):r for r in reading['fields']}
    assert len(read_fields)==40
    finding_path=HERE/'independent-boundary-findings-v1.json'
    assert sha(finding_path.read_bytes())==FINDING_SHA
    finding=read(finding_path)
    inspected={(r['id'],r['language']):r for r in finding['all_candidate_field_checks']}
    assert set(inspected)==set(read_fields)
    changes={(r['id'],r['language']):r for r in finding['findings']}
    assert len(changes)==4
    source_rows=list(map(json.loads,(HERE/'input/cohort.jsonl').read_bytes().splitlines()))
    source_by={'deenhindi-'+r['collection']+':'+r['number']:r for r in source_rows}
    assert len(source_by)==len(source_rows)==20
    shared={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(CENTRAL/'held-source-records.jsonl').read_bytes().splitlines())}
    assert all(shared[k]==v for k,v in source_by.items())
    manifest_path=OWNER/args.manifest
    assert sha(manifest_path.read_bytes())==args.manifest_sha
    manifest=read(manifest_path)
    suffix='final' if args.final else 'v1-preflight'
    repo=HERE/'validation'/suffix
    owner_bindings=[]
    for item in manifest['files']:
        relative=Path(item['path']);assert not relative.is_absolute() and '..' not in relative.parts
        path=Path(item['local_path'])
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(OWNER)
        b=bind(path)
        assert all(b[k]==item[k] for k in ['bytes','sha256','git_blob_sha1'])
        put(repo/relative,path.read_bytes())
        owner_bindings.append({'path':str(relative),'owner_path':str(path),**b})
    assert len(owner_bindings)==len({r['path'] for r in owner_bindings})
    assert sha((repo/ACTIVE).read_bytes())==args.active_sha
    ledger=read(repo/ACTIVE)
    baseline=repo/ledger['source_ledger_path']
    assert sha(baseline.read_bytes())==ledger['source_ledger_sha256']
    assert list(map(json.loads,gzip.decompress(baseline.read_bytes()).splitlines()))==source_rows
    decisions={r['id']:r for r in ledger['records']}
    assert len(decisions)==len(ledger['records'])==20 and set(decisions)==set(source_by)
    old_path=OWNER/'publish'/ACTIVE;assert sha(old_path.read_bytes())==OLD_SHA
    old={r['id']:r for r in read(old_path)['records']}
    authority=read(CENTRAL/'evidence-manifest.json');assert authority['saved_head']==PIN
    state=read(CENTRAL/'held-state-entries.json')
    engine=SourceReviews(repo,'deenhindi')
    counts=collections.Counter();metadata=collections.Counter()
    field_proofs=[];source_proofs=[];surgical=[];script_changes=[]
    for ident,saved in source_by.items():
        decision=decisions[ident];old_decision=old[ident]
        entry=state[saved['collection']+':'+saved['number']]
        assert entry['parsed']['path']==saved['parsed_path']
        for descriptor in [saved['snapshot'],entry['parsed']]:
            path=CENTRAL/'sources'/descriptor['path'];given=authority['files'][descriptor['path']]
            b=bind(path);assert all(b[k]==given[k] for k in ['bytes','sha256','git_blob_sha1'])
            plain=importer.checked_bytes(CENTRAL/'sources',descriptor)
            source_proofs.append({'id':ident,'path':descriptor['path'],**b,'plain_bytes':len(plain),'plain_sha256':sha(plain)})
        parsed=json.loads(importer.checked_bytes(CENTRAL/'sources',entry['parsed']))
        for k in ['collection','number','source_record','source_reference_verbatim','snapshot']:assert parsed[k]==saved[k]
        assert parsed['classification']==saved.get('intake_classification',saved['classification'])
        obj,ref=importer.parse_record(importer.checked_bytes(CENTRAL/'sources',saved['snapshot']),saved['collection'],saved['number'])
        assert obj==saved['source_record'] and ref==saved['source_reference_verbatim']
        assert decision['source_record_sha256']==sha(importer.json_bytes(obj))
        assert decision['source_snapshot']==saved['snapshot'] and decision['source_reference_verbatim']==ref
        assert decision['collection']==saved['collection'] and decision['number']==saved['number']
        original=importer.canonical_record(saved)
        revised,action=engine.apply(copy.deepcopy(original),saved=saved)
        assert action==decision['decision']=='register';counts['register']+=1
        assert revised['review']['independent_pro_qc']=='not_performed' and revised['review']['certified_release_eligible'] is False
        for k,v in original.items():
            if k not in ['text','language_versions','review','content_kind','extraction']:
                metadata['parent']+=equal(v,revised[k])
        fields={f['language']:f for f in decision['field_reviews']}
        old_fields={f['language']:f for f in old_decision['field_reviews']}
        assert len(fields)==len(decision['field_reviews'])
        actual_nonempty={lang for lang,name in FIELDS.items() if obj[name]}
        assert set(fields)==actual_nonempty
        original_versions={v['language']:v for v in original['language_versions']}
        revised_versions={v['language']:v for v in revised['language_versions']}
        assert set(original_versions)==set(revised_versions)==actual_nonempty
        if args.final:
            assert {k:v for k,v in decision.items() if k not in ['field_reviews','reason']}=={k:v for k,v in old_decision.items() if k not in ['field_reviews','reason']}
            if not any(key[0]==ident for key in changes):
                assert decision==old_decision;counts['unchanged_whole_parents']+=1
        for lang,name in FIELDS.items():
            key=(ident,lang);text=obj[name];counts['source_slots']+=1
            assert isinstance(text,str)
            if not text:
                assert key not in read_fields and lang not in fields and lang not in revised_versions
                counts['empty_source_slots']+=1
                field_proofs.append({'id':ident,'language':lang,'source_field_sha256':sha(b''),'source_value_state':'empty','native_version_absent_before_and_after':True})
                continue
            before=original_versions[lang];after=revised_versions[lang];field=fields[lang]
            assert before['text']==text and field['source_field']==name
            assert field['text_sha256']==sha(text.encode()) and field['text_chars']==len(text)
            reviewed=key in read_fields;assert field['reviewed'] is reviewed
            assert field['chars_reviewed']==(len(text) if reviewed else 0)
            assert field['bytes_reviewed']==(len(text.encode()) if reviewed else 0)
            selected=mask(text,field['spans'])
            counts['selected_spans']+=len(field['spans'])
            if reviewed:
                r=read_fields[key]
                assert r['text_sha256']==sha(text.encode()) and r['characters']==len(text) and r['utf8_bytes']==len(text.encode())
                counts['complete_fields_read']+=1;counts['characters_read']+=len(text);counts['utf8_bytes_read']+=len(text.encode())
                counts['admitted_fields' if any(selected) else 'read_context_fields']+=1
                approved=inspected[key]['candidate_field_decision']
                expected=mask(text,approved['spans'])
                if args.final and key in changes:
                    requested=changes[key]
                    if ident=='deenhindi-nasai:2492':
                        a,b=requested['opening_interval'];expected[a:b]=[True]*(b-a)
                        for locator in requested['retain_as_context']:
                            a,b=locator['start'],locator['end'];assert text[a:b]==locator['text'];expected[a:b]=[False]*(b-a)
                        new_parts=[s for s in field['spans'] if s['end']<=requested['opening_interval'][1]]
                        final_parts=[s for s in field['spans'] if s['start']>=requested['opening_interval'][1]]
                        assert new_parts and all(s['report_type']=='attributed_exegetical_statement' for s in new_parts)
                        named_voice = {
                            'hi': 'Ibn Shihab relays the interpretation explicitly supplied by the Hindi source-named अबू उम्मा बिन सहल बिन हुनैफ़. The quoted verse and rendering are the subject of that interpretation, with no recitation event inferred.',
                            'ur': 'Ibn Shihab relays the interpretation explicitly supplied by the Urdu source-named ابوامامہ بن سہیل بن حنیف. The quoted verse and rendering are the subject of that interpretation, with no recitation event inferred.',
                        }[lang]
                        assert all(s['speaker']==named_voice and s['component_id']=='attributed-exegesis' for s in new_parts)
                        assert all(s['reason']==approved['spans'][0]['reason'] and set(s)==set(approved['spans'][0]) for s in new_parts)
                        assert len({s['component_id'] for s in new_parts})==1
                        assert len(final_parts)==len(approved['spans'])==1
                        expected_prohibition=copy.deepcopy(approved['spans'][0])
                        expected_prohibition['report_type']='actual_prophetic_prohibition'
                        expected_prohibition['speaker']='The source separately attributes the actually supplied prohibition of taking bad property in zakat to the Prophet; the preceding interpreter statement is not Prophetic speech.'
                        assert final_parts[0]==expected_prohibition
                        assert new_parts[0]['component_id']!=final_parts[0]['component_id']
                        assert len({s['source_report_family_id'] for s in field['spans']})==1
                    else:
                        assert ident=='deenhindi-nasai:2540'
                        expected_spans=copy.deepcopy(approved['spans'])
                        for s in expected_spans:s['report_type']='reported_speech_and_prophetic_statement'
                        assert field['spans']==expected_spans
                else:
                    assert field['spans']==approved['spans']
                assert selected==expected,(key,'unexpected exact selected positions')
            else:
                assert not field['spans'] and after['text'] is None;counts['unread_context_fields']+=1
            if args.final:
                old_field=old_fields[lang]
                if key not in changes:
                    assert old_field==field;counts['unchanged_other_field_definitions']+=1
                else:
                    for k in ['language_version_id','language','source_field','text_sha256','text_chars','reviewed','chars_reviewed','bytes_reviewed','review_method','review_scope']:
                        assert old_field[k]==field[k]
                    surgical.append({'id':ident,'language':lang,'before_field_sha256':sha(enc(old_field)),
                                     'after_field_sha256':sha(enc(field)),'requested_change':changes[key]})
            assert (after['text'] or '')==''.join(text[s['start']:s['end']] for s in field['spans'])
            pieces=[(s['start'],s['end'],text[s['start']:s['end']]) for s in field['spans']]
            pieces.extend((c['source_span'][0],c['source_span'][1],c['text']) for c in after.get('comments',[]) if c.get('source_span') is not None)
            cursor=0
            for a,b,t in sorted(pieces):assert a==cursor and text[a:b]==t;cursor=b
            assert cursor==len(text) and ''.join(t for a,b,t in sorted(pieces))==text;counts['lossless_nonempty_partitions']+=1
            if 'observed_script' in field:
                assert key in read_fields and lang=='hi' and before['script']=='Deva' and after['script']==field['observed_script']=='Latn'
                assert after['source']['importer_script_before_review']=='Deva'
                assert after['source']['source_script_note']==field['source_script_note']
                script_changes.append({'id':ident,'language':lang,'before':'Deva','after':'Latn','source_field_sha256':field['text_sha256']})
            else:assert before['script']==after['script']
            for k,v in before.items():
                if k not in ['text','scope','source','comments','script']:metadata['language']+=equal(v,after[k])
            for k,v in before['source'].items():metadata['source']+=equal(v,after['source'][k])
            for i,c in enumerate(before.get('comments',[])):
                for k,v in c.items():metadata['previous_comments']+=equal(v,after['comments'][i][k])
            field_proofs.append({'id':ident,'language':lang,'source_field_sha256':sha(text.encode()),
                'characters':len(text),'utf8_bytes':len(text.encode()),'complete_own_field_read':reviewed,
                'selected_mask_sha256':sha(bytes(selected)),'selected_spans':field['spans'],'lossless_partition_pass':True})
    engine.finish()
    assert (counts['register'],counts['source_slots'],counts['lossless_nonempty_partitions'],counts['empty_source_slots'])==(20,100,98,2)
    assert (counts['complete_fields_read'],counts['characters_read'],counts['utf8_bytes_read'])==(40,10697,21245)
    assert (counts['admitted_fields'],counts['read_context_fields'],counts['unread_context_fields'])==(40,0,58)
    assert len(source_proofs)==40 and len(field_proofs)==100 and len(script_changes)==3
    archive_proof=[]
    if args.final:
        assert (counts['unchanged_other_field_definitions'],counts['unchanged_whole_parents'],len(surgical))==(94,18,4)
        original_manifest=read(OWNER/'delivery-manifest-v1.json')
        for item in original_manifest['files']:
            matches=[b['path'] for b in owner_bindings if b['sha256']==item['sha256'] and b['bytes']==item['bytes']]
            assert matches,('missing original payload evidence',item['path'])
            archive_proof.append({'v1_path':item['path'],'sha256':item['sha256'],'final_matching_paths':matches})
        assert any(b['sha256']==sha((OWNER/'delivery-manifest-v1.json').read_bytes()) for b in owner_bindings)
    for b in owner_bindings:assert bind(Path(b['owner_path']))=={k:b[k] for k in ['bytes','sha256','git_blob_sha1']}
    assert sha(manifest_path.read_bytes())==args.manifest_sha
    report={'schema':'independent-source-reading-native-audit-v1',
        'status':'PASS' if args.final else 'NATIVE_SOURCE_PASS_SEMANTIC_AMENDMENT_PENDING',
        'source_checkpoint':PIN,'primary_manifest_path':args.manifest,'primary_manifest_sha256':args.manifest_sha,
        'primary_active_ledger':ACTIVE,'primary_active_sha256':args.active_sha,
        'baseline_path':ledger['source_ledger_path'],'baseline_sha256':ledger['source_ledger_sha256'],
        'source_first_reading_receipt_sha256':READING_SHA,'independent_findings_sha256':FINDING_SHA,
        'counts':dict(counts),'metadata_leaf_equalities':dict(metadata),'metadata_leaf_equalities_total':sum(metadata.values()),
        'observed_script_corrections':script_changes,'source_files_reopened':40,'complete_raw_reparses':20,
        'stored_decompressed_git_blob_hashes_pass':True,'all_complete_objects_and_references_equal':True,
        'native_apply_and_finish_pass':True,'all_exact_independently_accepted_positions_verified':True,
        'source_parser_sha256':sha(Path(importer.__file__).read_bytes()),'source_review_engine_sha256':engine.engine_sha256,
        'frozen_candidate_file_bindings':owner_bindings,'surgical_final_amendment':surgical,
        'v1_payload_evidence_retained':archive_proof,'all_inputs_unchanged':True,
        'github_writes':0,'source_site_requests':0,'independent_pro_qc':'not_performed',
        'limitations':'This exact source packet and reviewed languages only. No canonical identity repair, authenticity certification or deployment claim.'}
    put(HERE/('native-source-audit-'+suffix+'.json'),enc(report))
    put(HERE/('field-and-source-proof-'+suffix+'.json.gz'),gzip.compress(enc({'fields':field_proofs,'source_files':source_proofs}),mtime=0))
    print(json.dumps({'status':report['status'],'report':bind(HERE/('native-source-audit-'+suffix+'.json')),
        'counts':dict(counts),'metadata_leaf_equalities':sum(metadata.values())}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',required=True);parser.add_argument('--manifest-sha',required=True)
    parser.add_argument('--active-sha',required=True);parser.add_argument('--final',action='store_true')
    audit(parser.parse_args())
