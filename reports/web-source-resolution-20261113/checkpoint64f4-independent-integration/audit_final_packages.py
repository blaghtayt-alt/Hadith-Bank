"""Integrate the four final independently approved64f4 102 packages offline."""
from pathlib import Path
import collections,copy,datetime,gzip,json,os
from prepare_source_and_published_baseline import (ROOT,WORK,COMMIT,REVIEWS,COHORT_SHA,QUEUE,
    sha,git,enc,read,lines,safe,bind,identity,immutable,SourceReviews,importer)
from prepare_published_baseline import PUBLISHED

def checked_delivery(path,expected):
    path=Path(path);assert bind(path)['sha256']==expected
    manifest=read(path);result=[]
    for item in manifest['files']:
        relative=str(safe(item.get('path',item.get('repository_path'))))
        local=Path(item.get('local_path') or item['source_path'])
        assert local.is_file() and not local.is_symlink() and local.resolve().is_relative_to(path.parent.resolve())
        b=bind(local);assert b['bytes']==item.get('bytes',item.get('size_bytes')) and b['sha256']==item['sha256']
        assert not item.get('git_blob_sha1') or b['git_blob_sha1']==item['git_blob_sha1']
        result.append({'path':relative,'local_path':str(local),**b})
    assert len(result)==len({r['path'] for r in result});return manifest,result

def hardlink_frozen(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert bind(target)==bind(source)
    else:os.link(source,target)

def leaves(v):
    if isinstance(v,dict):return sum(leaves(x) for x in v.values()) if v else 1
    if isinstance(v,list):return sum(leaves(x) for x in v) if v else 1
    return 1

def main():
    assert not (ROOT/'delivery-manifest.json').exists(),'Completed integration is immutable.'
    config_path=ROOT/'input-manifests.json';config_bytes=config_path.read_bytes();config=read(config_path)
    specs=config['review_packages'];assert len(specs)==4 and all(s['confirmed_final'] for s in specs),'All four independent final approvals required.'
    prep_path=ROOT/'prepared-source-and-published-baseline.json'
    assert bind(prep_path)['sha256']=='a612eba433e0d087903f2349bac6e89172435dae00b6cbd54914e626ae75278f'
    prep=read(prep_path);assert prep['result']=='PASS' and prep['source_commit']==COMMIT and prep['published_review_baseline_commit']==PUBLISHED
    source_path=ROOT/'input/source-cohort-102.jsonl';assert bind(source_path)['sha256']==COHORT_SHA
    sources={identity(r):r for r in lines(source_path)};assert len(sources)==102
    assert bind(ROOT/'new102-raw-parsed-source-proof.json.gz')['sha256']=='f7e512fda97e0f7c7d4223b20db3023188636b7f2236d92b70bd1eb6ccab3d4a'
    source_files=read(ROOT/'new102-raw-parsed-source-proof.json.gz')['records'];assert len(source_files)==204
    for r in source_files:
        b=bind(WORK/'phase22-successor-acquisition-monitor/complete-held-evidence/sources'/r['path'])
        assert all(b[k]==r[k] for k in b)
    published_root=ROOT/'validation/published-reviews'
    for r in prep['published_ledger_bindings']+prep['published_source_ledger_dependencies']:
        assert bind(published_root/r['path'])['sha256']==r['sha256']
    assert bind(published_root/QUEUE)['sha256']==prep['canonical_priority_queue']['sha256']
    prior=SourceReviews(published_root,'deenhindi');prior_ids=set(prior.decisions)
    assert len(prior_ids)==3661 and not prior_ids&set(sources)
    new_root=ROOT/'validation/new-reviews';combined_root=ROOT/'validation/combined-reviews'
    delivered={};decisions={};decision_paths={};membership={};package_expected={}
    primary_receipts=[];independent_receipts=[]
    for spec in specs:
        _,files=checked_delivery(spec['manifest_path'],spec['manifest_sha256'])
        _,audit_files=checked_delivery(spec['independent_audit_manifest_path'],spec['independent_audit_manifest_sha256'])
        exact_report=next(x for x in audit_files if x['sha256']==spec['independent_report_sha256'])
        report=read(Path(exact_report['local_path']))
        assert report.get('result',report.get('status'))=='PASS'
        assert spec['manifest_sha256'] in json.dumps(report) and spec['active_sha256'] in json.dumps(report)
        active_files=[r for r in files if Path(r['path']).parent.as_posix()==REVIEWS.as_posix() and Path(r['path']).name.startswith('source-review')]
        assert len(active_files)==1 and active_files[0]['sha256']==spec['active_sha256']
        for r in files:
            if r['path'] in delivered:assert delivered[r['path']]['sha256']==r['sha256'] and delivered[r['path']]['bytes']==r['bytes']
            else:delivered[r['path']]=r;hardlink_frozen(Path(r['local_path']),new_root/r['path'])
        active=active_files[0];ledger=read(new_root/active['path'])
        baseline_path=new_root/str(safe(ledger['source_ledger_path']));assert bind(baseline_path)['sha256']==ledger['source_ledger_sha256']
        baseline_rows=lines(baseline_path);baseline={identity(r):r for r in baseline_rows}
        records=ledger.get('records',ledger.get('decisions'));assert len(records)==len(baseline_rows)==len(baseline)==spec['expected']['occurrences']
        for d in records:
            oid=identity(d);assert oid in sources and oid not in decisions and oid not in prior_ids
            assert baseline[oid]==sources[oid] and d['source_record_sha256']==sha(importer.json_bytes(sources[oid]['source_record']))
            assert d['source_reference_verbatim']==sources[oid]['source_reference_verbatim']
            decisions[oid]=d;decision_paths[oid]=active['path'];membership[oid]=spec['name']
        package_expected[spec['name']]=spec['expected']
        primary_receipts.append({'name':spec['name'],'manifest_sha256':spec['manifest_sha256'],
            'active_ledger_path':active['path'],'active_ledger_sha256':spec['active_sha256'],
            'files':[{k:v for k,v in r.items() if k!='local_path'} for r in files]})
        independent_receipts.append({'name':spec['name'],'manifest_sha256':spec['independent_audit_manifest_sha256'],
            'exact_final_pass_report_sha256':spec['independent_report_sha256'],
            'files':[{k:v for k,v in r.items() if k!='local_path'} for r in audit_files]})
    assert set(decisions)==set(sources)
    for tree in [published_root,new_root]:
        for p in sorted(tree.rglob('*')):
            if p.is_file():hardlink_frozen(p,combined_root/p.relative_to(tree))
    combined=SourceReviews(combined_root,'deenhindi')
    assert set(combined.decisions)==prior_ids|set(sources) and len(combined.decisions)==3763
    assert len(list((combined_root/REVIEWS).glob('source-review*.json*')))==53
    assert all(combined.decisions[k]==prior.decisions[k] for k in prior_ids)
    for r in prep['published_ledger_bindings']+prep['published_source_ledger_dependencies']:
        assert bind(combined_root/r['path'])['sha256']==r['sha256']
    assert bind(combined_root/QUEUE)==bind(published_root/QUEUE)=={k:prep['canonical_priority_queue'][k] for k in ['bytes','sha256','git_blob_sha1']}

    native=SourceReviews(new_root,'deenhindi');assert set(native.decisions)==set(sources)
    counts=collections.Counter();metadata=collections.Counter();languages=collections.defaultdict(collections.Counter)
    bycollection=collections.defaultdict(collections.Counter);packages=collections.defaultdict(collections.Counter)
    checks=[];script_changes=[];empty_slots=[]
    for oid,saved in sorted(sources.items()):
        decision=decisions[oid];original=importer.canonical_record(saved);before=copy.deepcopy(original)
        result,action=native.apply(original,saved=saved);assert original==before and action==decision['decision']
        assert result['review']['independent_pro_qc']=='not_performed' and result['review']['certified_release_eligible'] is False
        assert result['number']['canonical'] is None
        for k,v in before.items():
            if k not in ('text','language_versions','review','content_kind','extraction','report_types'):
                assert result.get(k)==v,(oid,k);metadata['parent']+=leaves(v)
        fs=decision.get('fields',decision.get('field_reviews'));fields={f['language']:f for f in fs}
        assert len(fs)==len(fields)<=5
        nonempty_languages={lang for lang,source_field in importer.LANGUAGE_FIELDS.items() if saved['source_record'][source_field]}
        assert {v['language'] for v in before['language_versions']}=={v['language'] for v in result['language_versions']}==nonempty_languages
        assert len(before['language_versions'])==len(result['language_versions'])==len(nonempty_languages)
        parent_admitted={};details=[]
        for prior_v,version in zip(before['language_versions'],result['language_versions']):
            lang=prior_v['language'];text=saved['source_record'][importer.LANGUAGE_FIELDS[lang]]
            assert isinstance(text,str) and (prior_v['text'] or '')==text
            f=fields.get(lang);reviewed=f['reviewed'] if f else False;assert type(reviewed) is bool
            if f:
                assert f['source_field']==importer.LANGUAGE_FIELDS[lang] and f['text_sha256']==sha(text.encode())
                assert f.get('text_chars',len(text))==len(text) and f['chars_reviewed']==(len(text) if reviewed else 0)
                assert f['bytes_reviewed']==(len(text.encode()) if reviewed else 0)
                spans=f.get('spans',f.get('selected_spans',[]));counts['explicit_field_decisions']+=1
            else:spans=[];counts['implicit_field_slots']+=1
            assert not spans or reviewed
            for counter in [counts,packages[membership[oid]],languages[lang]]:counter['source_slots']+=1
            if text:
                assert lang not in ['hi','ur'] or reviewed
                assert version['source']['manual_review']['field_reviewed'] is reviewed
            else:
                assert not reviewed and not spans and version['text'] is None
                empty_slots.append({'id':oid,'language':lang,'source_field':importer.LANGUAGE_FIELDS[lang]})
            selected=''.join(text[s['start']:s['end']] for s in spans);assert (version['text'] or '')==selected
            pieces=[]
            for s in spans:
                a,b=s['start'],s['end'];assert 0<=a<b<=len(text) and sha(text[a:b].encode())==s['sha256']
                assert s['speaker'].strip() and s['report_type'].strip() and s['source_report_family_id'].strip()
                pieces.append((a,b,text[a:b]))
            for c in version.get('comments',[]):
                if 'source_span' not in c:continue
                a,b=c['source_span'];assert c['scope']=='source_context_not_narration'
                assert c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode());pieces.append((a,b,c['text']))
            cursor=0
            for a,b,t in sorted(pieces):assert a==cursor and a<b<=len(text) and t==text[a:b];cursor=b
            assert cursor==len(text) and ''.join(t for a,b,t in sorted(pieces))==text
            status='empty' if not text else 'admitted' if spans else 'read_context' if reviewed else 'unread_context'
            for counter in [counts,packages[membership[oid]],languages[lang]]:
                counter[status]+=1
                if text:counter['partitions']+=1
                if reviewed:
                    counter['read_fields']+=1;counter['read_characters']+=len(text);counter['read_utf8_bytes']+=len(text.encode())
                if spans:
                    counter['selected_spans']+=len(spans);counter['selected_characters']+=len(selected);counter['selected_utf8_bytes']+=len(selected.encode())
            if spans:
                parent_admitted[lang]=selected
                for cls in version['source']['report_component_classifications']:
                    matching=[s for s in spans if s['component_id']==cls['component_id']]
                    assert cls['spans']==[[s['start'],s['end']] for s in matching]
                    assert all(cls['speaker_description']==s['speaker'] and cls['report_type']==s['report_type'] and cls['source_report_family_id']==s['source_report_family_id'] for s in matching)
            if action=='exclude' and text:assert reviewed and not spans
            for k,v in prior_v.items():
                if k in ('text','scope','source','comments','quotation_status'):continue
                if k=='script' and v!=version[k]:
                    assert reviewed and f['observed_script']==version[k] and f['source_script_note'];script_changes.append({'id':oid,'language':lang,'before':v,'after':version[k]})
                else:assert version.get(k)==v,(oid,lang,k);metadata['language']+=leaves(v)
            for k,v in prior_v['source'].items():assert version['source'].get(k)==v,(oid,lang,'source',k);metadata['source']+=leaves(v)
            for i,c in enumerate(prior_v.get('comments',[])):
                for k,v in c.items():assert version['comments'][i][k]==v;metadata['previous_comments']+=leaves(v)
            details.append({'language':lang,'source_text_sha256':sha(text.encode()),'characters':len(text),'utf8_bytes':len(text.encode()),
                'status':status,'explicit_field_decision':f is not None,'selected_spans':spans,'lossless_partition':bool(text),'empty_source_preserved':not text})
        # The importer omits language_versions for literal empty source fields.
        # Account for those source slots without inventing a native field/review.
        for lang,source_field in importer.LANGUAGE_FIELDS.items():
            if lang in nonempty_languages:continue
            assert saved['source_record'][source_field]=='' and lang not in fields
            counts['implicit_field_slots']+=1
            for counter in [counts,packages[membership[oid]],languages[lang]]:
                counter['source_slots']+=1;counter['empty']+=1
            empty_slots.append({'id':oid,'language':lang,'source_field':source_field})
            details.append({'language':lang,'source_text_sha256':sha(b''),'characters':0,'utf8_bytes':0,
                'status':'empty','explicit_field_decision':False,'selected_spans':[],
                'lossless_partition':False,'empty_source_preserved':True,'native_language_version_absent_before_and_after':True})
        if action=='register':
            assert parent_admitted, 'Registered parent must contain an actually supplied admitted field'
            assert result['text']=={'arabic':parent_admitted.get('ar'),'translation':parent_admitted.get(before.get('source_language_code',before['language']))}
        else:assert not parent_admitted and result['text']==before['text']
        for counter in [counts,packages[membership[oid]],bycollection[saved['collection']]]:counter[action]+=1
        checks.append({'id':oid,'decision':action,'source_record_sha256':decision['source_record_sha256'],'review_path':decision_paths[oid],'fields':details})
    native.finish()
    expected={'register':100,'exclude':2,'read_fields':216,'admitted':200,'read_context':16,'unread_context':294,'empty':0,
        'source_slots':510,'partitions':510,'read_characters':112759,'read_utf8_bytes':239747,'selected_spans':425}
    assert all(counts[k]==v for k,v in expected.items()),(dict(counts),expected)
    assert counts['explicit_field_decisions']+counts['implicit_field_slots']==510
    counts['spans']=counts['selected_spans']
    for name,e in package_expected.items():
        actual=packages[name];assert actual['register']+actual['exclude']==e['occurrences']
        assert all(actual[k]==v for k,v in e.items() if k!='occurrences'),(name,dict(actual),e)
    assert languages['hi']['read_fields']==languages['ur']['read_fields']==102
    assert languages['hi']['admitted']==languages['ur']['admitted']==98
    assert languages['ar']['read_fields']==languages['en']['read_fields']==languages['ur-Latn']['read_fields']==4
    assert languages['ar']['admitted']==languages['en']['admitted']==2 and languages['ur-Latn']['admitted']==0
    assert languages['hi']['read_context']==languages['ur']['read_context']==4
    assert languages['ar']['read_context']==languages['en']['read_context']==2 and languages['ur-Latn']['read_context']==4
    assert not empty_slots and not script_changes
    excluded=sorted(k for k,d in decisions.items() if d['decision']=='exclude')
    assert excluded==['deenhindi-abudawud:2720','deenhindi-muslim:2725']
    old86_path=WORK/'phase21-checkpoint0d2fa-independent-integration/input/source-cohort-86.jsonl'
    old85_path=WORK/'phase22-checkpoint17cd-independent-integration/input/source-cohort-85.jsonl'
    old86={identity(r) for r in lines(old86_path)};old85={identity(r) for r in lines(old85_path)}
    assert len(old86)==86 and len(old85)==85 and not old86&old85 and not (old86|old85)&set(sources)
    old86_counts=collections.Counter(prior.decisions[k][2] for k in old86)
    old85_counts=collections.Counter(prior.decisions[k][2] for k in old85)
    assert old86_counts=={'register':84,'exclude':2} and old85_counts=={'register':84,'exclude':1}
    assert dict(old86_counts)==prep['old86_published_dispositions'] and dict(old85_counts)==prep['old85_published_dispositions']
    current=prep['current_published_generated_export_binding']
    progress_path=ROOT/'input/current-published-progress.json'
    assert bind(progress_path)==current['progress_binding']
    progress=read(progress_path);progress_inputs={r['path']:r for r in progress['source_review_inputs']}
    assert len(progress_inputs)==len(progress['source_review_inputs'])
    consumed86_ledgers={prior.decisions[k][1]['path']:prior.decisions[k][1]['sha256'] for k in old86}
    pending85_ledgers={prior.decisions[k][1]['path']:prior.decisions[k][1]['sha256'] for k in old85}
    assert len(consumed86_ledgers)==len(pending85_ledgers)==4
    assert all(progress_inputs[p]['sha256']==h for p,h in consumed86_ledgers.items())
    assert not set(pending85_ledgers)&set(progress_inputs)
    assert not set(decision_paths.values())&set(progress_inputs)
    projection={'fetched':progress['imported_count'],
        'registered':progress['registered_hadith_count']+old85_counts['register']+counts['register'],
        'source_only':progress['non_narration_source_entries']+old85_counts['exclude']+counts['exclude'],
        'held':progress['classification_pending_count']-len(old85)-len(sources),
        'unfetched':progress['pending_fetch_count']}
    assert projection=={'fetched':18570,'registered':18400,'source_only':170,'held':0,'unfetched':17820}
    for spec in specs:
        checked_delivery(spec['manifest_path'],spec['manifest_sha256']);checked_delivery(spec['independent_audit_manifest_path'],spec['independent_audit_manifest_sha256'])
    assert config_path.read_bytes()==config_bytes
    report={'schema':'hadith-bank-checkpoint64f4-independent-integration-v1','result':'PASS',
        'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':COMMIT,
        'published_review_baseline_commit':PUBLISHED,'source_count':102,'source_cohort_sha256':COHORT_SHA,
        'preparation_receipt':bind(prep_path),'source_files_rehashed_against_frozen_proof':204,'full_raw_reparses_bound_from_frozen_preparation':102,
        'source_preparation_rerun_by_this_gate':False,
        'full_saved_64f4_state_and102_descriptors_bound_to_preparation':prep['full_saved_64f4_state'],
        'all102_absent_from_complete_prior18089_imported_ids':prep['all102_absent_from_all18089_prior_imported_ids'],
        'prior49_published_manual_ledgers':49,'prior_published_manual_ids':3661,'new_active_ledgers':4,
        'native_combined_loader_ledgers':53,'native_combined_loader_ids':3763,'id_collisions':[],
        'all49_prior_blobs_dependencies_and3661_decisions_unchanged':True,
        'canonical6311_priority_queue_unchanged':prep['canonical_priority_queue'],
        'updated477_current_6d099f91_ledger_preserved':True,
        'combined_loader_scope':'Native constructor collision/dependency validation of all53 ledgers; apply/finish for the newly approved102. Prior3661 decisions are preserved, not newly read here.',
        'native_new102_apply_finish':'PASS','counts':dict(counts),'empty_source_slots':empty_slots,
        'metadata_leaf_equalities':dict(metadata),'metadata_leaf_equalities_total':sum(metadata.values()),
        'by_package':{k:dict(v) for k,v in packages.items()},'by_language':{k:dict(v) for k,v in languages.items()},
        'by_collection':{k:dict(v) for k,v in bycollection.items()},'script_corrections':script_changes,
        'primary_package_receipts':primary_receipts,'independent_complete_reading_audit_receipts':independent_receipts,
        'source_only_ids':excluded,
        'source_context_qualification':'AbuDawud2720 and Muslim2725 each have all five nonempty own fields actually read and retained as context, with no admitted narration. Bukhari2773/2774 register only their own finite Arabic/English bodies; all six Hindi/Urdu/Roman duplicated-chain fields were read and remain context. Other294 sibling fields remain wholly unread context.216 complete fields are distinct source-language fields, not doubled for primary and independent readings. This integration adds no linguistic reading or semantic decision; source-side explanations and nominal version apparatus retain their original bytes in context.',
        'old86_already_consumed_dispositions':dict(old86_counts),'old85_published_unconsumed_dispositions':dict(old85_counts),
        'actual_generated_export_inputs_include_old86_exact_ledgers':consumed86_ledgers,
        'actual_generated_export_inputs_omit_old85_and_all_new102_ledgers':pending85_ledgers,
        'historical64f4_worker_counts':prep['historical_64f4_worker_counts'],
        'actual_d304_31c_published_generated_export_counts':current['actual_generated_export'],
        'actual_published_progress_receipt':bind(progress_path),
        'fixed64f4_projection_after_unconsumed85_and_new102':projection,
        'already_consumed86_applied_again':False,'projection_is_newly_saved_export':False,'newer_state_or_live_deployment_audited_here':False,
        'full_history_audit_scope':prep['history_scope'],
        'new_linguistic_readings_by_integration':0,'new_semantic_decisions_by_integration':0,'source_requests':0,'github_writes':0,
        'independent_pro_qc':'not_performed','parser_sha256':sha(Path(importer.__file__).read_bytes()),'review_engine_sha256':native.engine_sha256,
        'limitations':'This frozen64f4 102-source packet, exact independently read-back31c011 prior49-ledger baseline and four final independent gates only. Actual generated d304/31c progress already consumed86 decisions and records187 holds; only the unconsumed85 plus these102 are added to the fixed-source projection. No regenerated export or live deployment is claimed. Full saved-state identity and102 raw reparses are bound to the unchanged preparation receipt; historical error/retry/control preservation is the separately frozen full acquisition audit.'}
    prefix=Path('reports/web-source-resolution-20261113/checkpoint64f4-independent-integration')
    tree_authority={'files':{p.name:read(p) for p in sorted((ROOT/'input/published-tree-authority').glob('*.json'))}}
    outputs={'validation-report.json':enc(report),'per-occurrence-field-partitions.json.gz':gzip.compress(enc({'records':checks}),mtime=0),
        'prepared-source-and-published-baseline.json':prep_path.read_bytes(),
        'prepared-source-cohort.json':(ROOT/'prepared-source-cohort.json').read_bytes(),
        'current-published-progress.json.gz':gzip.compress(progress_path.read_bytes(),mtime=0),
        'new102-raw-parsed-source-proof.json.gz':(ROOT/'new102-raw-parsed-source-proof.json.gz').read_bytes(),
        'published-tree-authority.json.gz':gzip.compress(enc(tree_authority),mtime=0),
        'input-manifests.json':config_bytes,'audit_final_packages.py':Path(__file__).read_bytes(),
        'prepare_source_and_published_baseline.py':(ROOT/'prepare_source_and_published_baseline.py').read_bytes(),
        'prepare_published_baseline.py':(ROOT/'prepare_published_baseline.py').read_bytes()}
    files=[]
    for name,data in outputs.items():
        path=ROOT/'publish'/prefix/name;immutable(path,data);files.append({'path':str(prefix/name),'local_path':str(path),**bind(path)})
    delivery={'schema':'hadith-bank-independent-integration-delivery-v1','result':'PASS','source_commit':COMMIT,
        'published_review_baseline_commit':PUBLISHED,'files':files,'counts':dict(counts),'total_files':len(files),'total_bytes':sum(r['bytes'] for r in files)}
    immutable(ROOT/'delivery-manifest.json',enc(delivery))
    print(json.dumps({'result':'PASS','counts':dict(counts),'metadata_leaf_equalities':sum(metadata.values()),
        'manifest_sha256':sha(enc(delivery)),'report_sha256':sha(enc(report)),'files':len(files),'bytes':delivery['total_bytes']},indent=2))

if __name__=='__main__':main()
