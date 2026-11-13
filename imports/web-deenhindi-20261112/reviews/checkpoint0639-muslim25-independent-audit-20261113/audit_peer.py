"""Final independent saved-source/native audit, with exact source-first amendments."""
from pathlib import Path
import collections, copy, gzip, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OWNER=BASE/'phase15-checkpoint0639-muslim25-review'
SOURCE=BASE/'phase13-successor-acquisition-monitor/held-evidence'
CHECKPOINT='0639af7fd15786284b4c413fced77e38eec8825a'
OLD_MANIFEST='b7d1e30f93974ed746e1d660cb3f8799ac3d48f38e29ec431b50957f7c9a3503'
OLD_ACTIVE='deffc347dd549d63caa58100a64701e9a4c2304f473d090a7761e2af68660854'
INPUT_HASH='5f3f7103a180f543f50df6fc5c6fc7ccc36bcb0d3c6d2911d3d9fe811a163d3c'
READING_HASH='6c9d08376ce36b2a8329130540e91f90bc874b66b6d33e25aa708a2cbe02d8c8'
SOURCE_PROOF_HASH='c6bde7a6096f164870cbfa69563c2267fda81f43e00aaa6039d38553aed66940'
EXCLUDED={'2264','2299'}
LANGUAGES={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
CHANGES={
 ('2240','hi'):{'restore':[(149,168),(290,306)],'cut':[],
   'reason':'The sole supplied family addressee and grave object are actual actor/object scope. Keep Sad as the speaker of the instruction.'},
 ('2240','ur'):{'restore':[(137,156),(267,280)],'cut':[],
   'reason':'The sole supplied family addressee and grave object are actual actor/object scope; malformed grave delimiters remain exact.'},
 ('2291','hi'):{'restore':[(132,174)],'cut':[],
   'reason':'Expressly affirmed camel-owner negative-predicate wording is an actual abbreviated conditional/relative fragment. Retain it in the same transmitted family with unknown ultimate speaker and missing consequence.'},
 ('2291','ur'):{'restore':[(122,166)],'cut':[],
   'reason':'Expressly affirmed camel-owner negative-predicate wording is an actual abbreviated conditional/relative fragment. Do not infer its missing consequence or ultimate speaker.'},
 ('2301','hi'):{'restore':[(378,488)],'cut':[],
   'reason':'Retain the supplied death/unpaid-cattle conditional ending under the explicit Prophetic link, with no consequence reconstructed.'},
 ('2301','ur'):{'restore':[(333,444)],'cut':[],
   'reason':'Retain the own supplied death/unpaid-cattle conditional ending with its missing consequence explicitly qualified and not filled.'},
 ('2307','hi'):{'restore':[],'cut':[(780,785)],
   'reason':'The help parenthesis is a lexical explanation of the defective preceding word; keep it as context and preserve that defective Hindi word unchanged.'},
 ('2307','ur'):{'restore':[],'cut':[(829,836)],
   'reason':'The help parenthesis repeats the already printed assistance term as a lexical synonym; retain it as context.'},
}
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def checked_file(root,path):
    p=root/path
    assert not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(root.resolve()),path
    return p.read_bytes()

def equal_leaves(a,b):
    assert a==b
    if isinstance(a,dict):return sum(equal_leaves(a[k],b[k]) for k in a)
    if isinstance(a,list):return sum(equal_leaves(x,y) for x,y in zip(a,b,strict=True))
    return 1

def mask(field):return {i for s in field['selected_spans'] for i in range(s['start'],s['end'])}

def main():
    config=json.loads((ROOT/'final-candidate-binding.json').read_bytes())
    assert config['semantic_final_candidate_comparison_complete'] is True
    sys.path.insert(0,str(BASE/'hindi-resolve/work/scripts'))
    import import_deenhindi as importer
    from web_source_reviews import SourceReviews
    assert sha(Path(importer.__file__).read_bytes())=='c2b6df1d243b7e9c695358d9f06221c4cba45e880a1a215e4ef697008ed144d0'
    old_manifest_bytes=(OWNER/'delivery-manifest-v1.json').read_bytes();assert sha(old_manifest_bytes)==OLD_MANIFEST
    old_manifest=json.loads(old_manifest_bytes);old_root=OWNER/'publish-v1'
    old_bytes=checked_file(old_root,old_manifest['active_ledger_path']);assert sha(old_bytes)==OLD_ACTIVE
    old_doc=json.loads(gzip.decompress(old_bytes));old_records={r['occurrence_id']:r for r in old_doc['records']}
    final_manifest_bytes=(OWNER/config['manifest_name']).read_bytes()
    assert sha(final_manifest_bytes)==config['manifest_sha256']
    manifest=json.loads(final_manifest_bytes);published=OWNER/config['publish_directory']
    final_files=[]
    for item in manifest['files']:
        data=checked_file(published,item['path'])
        assert len(data)==item['bytes'] and sha(data)==item['sha256']
        if 'git_blob_sha1' in item:assert git(data)==item['git_blob_sha1']
        final_files.append({'path':item['path'],'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)})
    # Frozen v1 is evidence, never overwritten by a final correction.
    for item in old_manifest['files']:
        data=checked_file(old_root,item['path']);assert len(data)==item['bytes'] and sha(data)==item['sha256']
    active_path=manifest['active_ledger_path'];active_bytes=checked_file(published,active_path)
    assert sha(active_bytes)==config['active_sha256']==manifest['active_ledger_sha256']
    doc=json.loads(gzip.decompress(active_bytes));records={r['occurrence_id']:r for r in doc['records']}
    assert len(records)==len(doc['records'])==len(old_records)==25 and set(records)==set(old_records)
    input_bytes=(ROOT/'input/cohort.jsonl').read_bytes();assert sha(input_bytes)==INPUT_HASH
    input_rows=[json.loads(x) for x in input_bytes.decode().splitlines()]
    keyed=lambda xs:{r['collection']+':'+r['number']:r for r in xs}
    baseline_bytes=checked_file(published,doc['source_ledger_path']);assert sha(baseline_bytes)==doc['source_ledger_sha256']
    rows=[json.loads(x) for x in gzip.decompress(baseline_bytes).decode().splitlines()]
    assert keyed(rows)==keyed(input_rows)
    assert baseline_bytes==checked_file(old_root,old_doc['source_ledger_path'])
    source_rows=keyed(map(json.loads,(SOURCE/'held-source-records.jsonl').read_text().splitlines()))
    assert all(source_rows[k]==v for k,v in keyed(rows).items())
    first_bytes=(ROOT/'complete-independent-readings.json').read_bytes();assert sha(first_bytes)==READING_HASH
    first=json.loads(first_bytes);readings={(r['key'],r['language']):r for r in first['fields']}
    assert len(readings)==first['complete_fields_read']==59
    assert first['characters_read']==29190 and first['utf8_bytes_read']==60905
    assert first['source_read_before_primary_notes_and_decisions'] is True
    proof_bytes=(ROOT/'independent-source-verification.json').read_bytes();assert sha(proof_bytes)==SOURCE_PROOF_HASH
    proof=json.loads(proof_bytes);assert proof['status']=='PASS' and proof['raw_responses_reparsed']==25
    evidence_bytes=(SOURCE/'evidence-manifest.json').read_bytes()
    assert sha(evidence_bytes)=='d15b00231f3f9a86e91bb6a6ed571426413d049a4b63e8fd05a2db092a5b080f'
    evidence=json.loads(evidence_bytes);assert evidence['saved_head']==CHECKPOINT
    states=json.loads((SOURCE/'held-state-entries.json').read_bytes())
    native=SourceReviews(published,'deenhindi');assert set(native.decisions)==set(records)
    totals=collections.Counter();field_receipts=[];amendments=[];source_receipts=[];attributions=[]
    expected_components={('2237','hi'):2,('2237','ur'):2,('2280','hi'):2,('2280','ur'):2,
      ('2284','hi'):2,('2284','ur'):3,('2285','hi'):3,('2285','ur'):3,('2287','hi'):2,('2287','ur'):2,
      ('2291','hi'):3,('2291','ur'):3,('2301','hi'):3,('2301','ur'):3,('2305','hi'):4,('2305','ur'):2,
      ('2306','hi'):3,('2306','ur'):3,('2307','hi'):2,('2307','ur'):2}
    for row in rows:
        number=row['number'];key='muslim:'+number;identity='deenhindi-'+key
        old=old_records[identity];record=records[identity]
        action='exclude' if number in EXCLUDED else 'register'
        assert old['decision']==record['decision']==action
        assert old['source_snapshot']==record['source_snapshot']==row['snapshot']
        for metadata in ['source_record_sha256','source_parsed_path','source_parsed_sha256','source_reference_verbatim',
                         'collection','number','numbering_system','external_canonical_identity','verified_external_reference']:
            assert old[metadata]==record[metadata],(identity,metadata)
        entry=states[key];verified=[]
        for relative in [row['snapshot']['path'],row['parsed_path']]:
            data=checked_file(SOURCE/'sources',relative);binding=evidence['files'][relative]
            assert len(data)==binding['bytes']==binding['stored_bytes'] and sha(data)==binding['sha256']==binding['stored_sha256']
            assert git(data)==binding['git_blob_sha1'];plain=gzip.decompress(data)
            verified.append({'path':relative,'stored_bytes':len(data),'stored_sha256':sha(data),'git_blob_sha1':git(data),
                             'bytes':len(plain),'sha256':sha(plain)})
            if relative==row['snapshot']['path']:
                raw=plain;assert sha(raw)==row['snapshot']['sha256'] and len(raw)==row['snapshot']['bytes']
            else:
                parsed=plain;assert sha(parsed)==entry['parsed']['sha256'] and sha(data)==entry['parsed']['stored_sha256']
        expected={k:row[k] for k in ['schema','collection','number','snapshot','source_reference_verbatim','source_record']}
        expected['classification']=row['intake_classification'];assert parsed==importer.json_bytes(expected)
        actual,ref=importer.parse_record(raw,'muslim',number)
        assert actual==row['source_record'] and ref==row['source_reference_verbatim']
        assert sha(importer.json_bytes(actual))==evidence['source_record_sha256'][key]
        source_receipts.append({'id':identity,'exact_reparse':True,'source_record_sha256':sha(importer.json_bytes(actual)),'files':verified})
        totals.update(raw_parsed_files_verified=2,exact_html_reparses=1)
        canonical=importer.canonical_record(row);before=copy.deepcopy(canonical);row_before=copy.deepcopy(row)
        after,native_action=native.apply(canonical,saved=row)
        assert native_action==action and canonical==before and row==row_before
        for name in set(before)-{'language_versions','text','content_kind','review','report_types','extraction'}:
            totals['metadata_leaf_equalities']+=equal_leaves(before[name],after[name])
        for name in before['extraction']:
            if name!='is_excerpt':totals['metadata_leaf_equalities']+=equal_leaves(before['extraction'][name],after['extraction'][name])
        old_fields={f['language']:f for f in old['fields']};fields={f['language']:f for f in record['fields']}
        assert set(fields)==set(old_fields)==set(LANGUAGES)
        selected={}
        for old_version,new_version in zip(before['language_versions'],after['language_versions'],strict=True):
            lang=old_version['language'];text=old_version['text'];field=fields[lang];old_field=old_fields[lang];binding=(number,lang)
            assert field['text_sha256']==sha(text.encode()) and field['source_field']==LANGUAGES[lang]
            read_key=(key,lang);assert field['reviewed']==(read_key in readings)
            if read_key in readings:
                reading=readings[read_key];assert reading['text']==text and reading['sha256']==sha(text.encode())
                assert field['chars_reviewed']==reading['chars']==len(text) and field['bytes_reviewed']==reading['utf8_bytes']==len(text.encode())
                totals.update(complete_fields_independently_read=1,characters_read=len(text),utf8_bytes_read=len(text.encode()))
            else:assert field['chars_reviewed']==field['bytes_reviewed']==0
            expected_mask=mask(old_field)
            if binding in CHANGES:
                delta=CHANGES[binding];bound_changes=[]
                for verb in ['restore','cut']:
                    for start,end in delta[verb]:
                        positions=set(range(start,end))
                        if verb=='restore':assert not positions&expected_mask;expected_mask|=positions
                        else:assert positions<=expected_mask;expected_mask-=positions
                        bound_changes.append({'action':verb,'start':start,'end':end,'text':text[start:end],
                                              'sha256':sha(text[start:end].encode()),'characters':end-start,'utf8_bytes':len(text[start:end].encode())})
                amendments.append({'id':identity,'language':lang,'source_text_sha256':sha(text.encode()),
                  'independent_reason':delta['reason'],'before_field_sha256':sha(enc(old_field)),
                  'after_field_sha256':sha(enc(field)),'changes':bound_changes})
                totals['changed_fields']+=1
            else:
                assert field==old_field,(identity,lang,'unexpected field mutation')
                totals['unchanged_read_fields' if field['reviewed'] else 'unchanged_unread_fields']+=1
            assert mask(field)==expected_mask,(identity,lang,'unexpected selected positions')
            for name in set(old_version)-{'text','scope','quotation_status','source','comments'}:
                totals['metadata_leaf_equalities']+=equal_leaves(old_version[name],new_version[name])
            for name in old_version['source']:
                totals['metadata_leaf_equalities']+=equal_leaves(old_version['source'][name],new_version['source'][name])
            spans=field['selected_spans'];pieces=[];context=[]
            for span in spans:
                a,b=span['start'],span['end'];assert 0<=a<b<=len(text) and text[a:b].strip()
                assert sha(text[a:b].encode())==span['sha256'];pieces.append((a,b,text[a:b]))
                totals['selected_spans']+=1;totals['selected_characters']+=b-a
            if spans:
                positions=[[s['start'],s['end']] for s in spans]
                assert new_version['source']['text_spans']['quotation_spans']==positions
                assert new_version['text']==''.join(text[a:b] for a,b in positions)
                selected[lang]=new_version['text'];totals['admitted_fields']+=1
                classifications=new_version['source']['report_component_classifications']
                assert len(classifications)==expected_components.get(binding,1),(binding,len(classifications))
                assert new_version['source'].get('source_report_count',1)==1
                assert all(c['report_type'] and c['speaker_description'] and c['spans'] for c in classifications)
                attributions.append({'id':identity,'language':lang,'source_report_families':1,'classifications':classifications})
            else:
                assert new_version['text'] is None
                totals['reviewed_context_fields' if field['reviewed'] else 'unread_context_fields']+=1
            assert new_version['source']['manual_review']['field_reviewed']==field['reviewed']
            for comment in new_version['comments']:
                a,b=comment['source_span'];assert comment['text']==text[a:b] and comment['source_text_sha256']==sha(text[a:b].encode())
                assert comment['scope']=='source_context_not_narration'
                pieces.append((a,b,comment['text']));context.append({'start':a,'end':b,'text':comment['text'],'sha256':comment['source_text_sha256']})
            cursor=0
            for a,b,part in sorted(pieces):assert a==cursor and b>a;cursor=b
            assert cursor==len(text) and ''.join(p[2] for p in sorted(pieces))==text
            totals['lossless_field_partitions']+=1
            if field['reviewed']:
                field_receipts.append({**readings[read_key], 'final_field_review':field,
                   'selected_source_spans':[{**s,'text':text[s['start']:s['end']]} for s in spans],
                   'source_context_spans':context,'all_boundaries_independently_accepted':True})
        if action=='register':assert after['text']=={'arabic':selected.get('ar'),'translation':selected.get('hi')}
        else:assert after['text']==before['text']
        assert after['number']['canonical'] is None
        assert after['review']['independent_pro_qc']=='not_performed' and after['review']['certified_release_eligible'] is False
        totals[action]+=1;totals['source_occurrences']+=1
    native.finish()
    assert totals['source_occurrences']==25 and totals['register']==23 and totals['exclude']==2
    assert totals['complete_fields_independently_read']==59 and totals['characters_read']==29190 and totals['utf8_bytes_read']==60905
    assert totals['admitted_fields']==45 and totals['reviewed_context_fields']==14 and totals['unread_context_fields']==66
    assert totals['lossless_field_partitions']==125 and totals['changed_fields']==8
    assert totals['unchanged_read_fields']==51 and totals['unchanged_unread_fields']==66
    assert sha((OWNER/config['manifest_name']).read_bytes())==config['manifest_sha256']
    prefix='imports/web-deenhindi-20261112/reviews/checkpoint0639-muslim25-independent-audit-20261113'
    artifacts={
      prefix+'/source-first-complete-reading.json.gz':gzip.compress(first_bytes,mtime=0),
      prefix+'/complete-field-boundary-audit.json.gz':gzip.compress(enc({'source_commit':CHECKPOINT,'active_sha256':config['active_sha256'],
        'fields':field_receipts,'actual_attribution_components':attributions}),mtime=0),
      prefix+'/saved-source-and-package-verification.json.gz':gzip.compress(enc({'source_commit':CHECKPOINT,
        'source_first_raw_proof_sha256':SOURCE_PROOF_HASH,'primary_package_files':final_files,'records':source_receipts}),mtime=0),
      prefix+'/exact-independent-amendments.json':enc({'source_commit':CHECKPOINT,'before_manifest_sha256':OLD_MANIFEST,
        'before_active_sha256':OLD_ACTIVE,'after_manifest_sha256':config['manifest_sha256'],'after_active_sha256':config['active_sha256'],
        'changed_fields':8,'unchanged_read_fields':51,'unchanged_unread_fields':66,'unchanged_parent_decisions':25,
        'all_frozen_v1_files_unchanged':True,'amendments':amendments})}
    report={'schema':'hadith-bank-independent-source-review-audit-v1','result':'PASS','source_commit':CHECKPOINT,
      'source_baseline_sha256':sha(baseline_bytes),'owner_manifest_sha256':config['manifest_sha256'],
      'active_ledger_path':active_path,'active_ledger_sha256':config['active_sha256'],
      'actual_independent_readings_and_checks':dict(totals),'findings_resolved':4,'open_findings':[],
      'source_only_ids':['deenhindi-muslim:'+n for n in sorted(EXCLUDED,key=int)],
      'all_source_only_siblings_completely_read':True,'all_59_field_boundaries_and_voices_independently_checked':True,
      'arabic_2293_only_finite_branding_fragment_with_unknown_actor':True,
      'finite_conditional_fragments_preserved_without_missing_consequences':True,
      'hindi_source_defects_and_unnamed_2306_actor_preserved':True,'native_apply_and_finish':'PASS',
      'new_source_http_requests':0,'github_writes':0,'owner_package_mutated':False,'formal_independent_pro_certification':False,
      'limits':'Independent complete own-field reading and saved-source/native checks. Full-checkout export, shared reader/browser CI, actual deployment and formal Pro certification remain separate gates.',
      'evidence':[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in artifacts.items()]}
    report_path='reports/web-source-resolution-20261113/checkpoint0639-muslim25-independent-review.json'
    artifacts[report_path]=enc(report)
    artifacts[prefix+'/audit_peer.py']=Path(__file__).read_bytes()
    artifacts[prefix+'/final-candidate-binding.json']=(ROOT/'final-candidate-binding.json').read_bytes()
    delivered=[]
    for relative,data in artifacts.items():
        p=ROOT/'publish'/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        delivered.append({'path':relative,'local_path':str(p),'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)})
    delivery={'schema':'hadith-bank-independent-audit-delivery-v1','source_commit':CHECKPOINT,
      'active_ledger_sha256':config['active_sha256'],'files':delivered,'total_files':len(delivered),'total_bytes':sum(f['bytes'] for f in delivered)}
    (ROOT/'delivery-manifest.json').write_bytes(enc(delivery))
    print(json.dumps({'result':'PASS','totals':dict(totals),'manifest_sha256':sha(enc(delivery)),
                     'report_sha256':sha(artifacts[report_path]),'files':len(delivered),'bytes':delivery['total_bytes']},indent=2))

if __name__=='__main__':main()
