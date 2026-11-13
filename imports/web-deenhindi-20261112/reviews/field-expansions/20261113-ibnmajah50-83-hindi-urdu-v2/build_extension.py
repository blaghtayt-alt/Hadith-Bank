from pathlib import Path
import collections, copy, gzip, hashlib, json, shutil, sys
from manual_reading_spec import (SPECS, CUTS, STOPS, STARTS, SPLITS, COMPONENTS,
                                 REQUIRED_RETENTIONS, FOCUSED_ADJUDICATIONS)

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

EXTENSION='20261113-ibnmajah50-83-hindi-urdu-v2'
EVIDENCE=Path('imports/web-deenhindi-20261112/reviews/field-expansions')/EXTENSION
OUT=ROOT/'publish-v2'
VALIDATION=ROOT/'validation-repo'
def sha(data):return hashlib.sha256(data).hexdigest()
def gitsha(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
def locate(text,selector):
    literal,n,count=(selector,0,1) if isinstance(selector,str) else selector
    assert text.count(literal)==count,('explicit delimiter count mismatch',selector,text.count(literal))
    cursor=-1
    for _ in range(n+1):cursor=text.index(literal,cursor+1)
    return cursor,cursor+len(literal)

input_bytes=(ROOT/'full-field-reading-input-83.jsonl').read_bytes()
assert sha(input_bytes)=='f4a95c14afeb07c56759ad1af36a9f705eba29a34ad8c6d0429b4de56007a512'
inputs=[json.loads(line) for line in input_bytes.splitlines()]
targets={(r['occurrence_id'],r['language']):r for r in inputs}
assert len(targets)==83
root_notes=json.loads((ROOT/'root-complete-reading-notes.json').read_bytes())
notes_by_key={(r['occurrence_id'],r['language']):r for r in root_notes['records']}
assert set(notes_by_key)==set(targets)
selection=json.loads((ROOT/'selection.json').read_bytes())
old_bytes=(ROOT/'pinned-inputs'/selection['active_ledger_path']).read_bytes()
assert sha(old_bytes)==selection['active_ledger_sha256']=='07d2e5dc1a8fcdeaac7a0696dd1a0517ebcab77d617e48e618eb8077bed9fb54'
old=json.loads(gzip.decompress(old_bytes));new=copy.deepcopy(old)
old_rows={r['occurrence_id']:r for r in old['records']}
rows={r['occurrence_id']:r for r in new['records']}
sources={f"deenhindi-{s['collection']}:{s['number']}":s for s in map(json.loads,(ROOT/'source-ledger-50.jsonl').read_text().splitlines())}
assert set(sources)=={k[0] for k in targets}
assert set(SPECS)=={k.rsplit(':',1)[1] for k in sources}
apparatus_receipts=[]

def sections(number,language,text):
    key=(number,language);kind,speaker=SPECS[number]
    family='deenhindi-ibnmajah:'+number+':report-1'
    if number=='309':
        stop='अबुल हसन अल-क़त्तन कहते हैं:' if language=='hi' else 'ابوالحسن القطان کہتے ہیں:'
        quote="'आना रा'एतुहु यबूले का'इदं'" if language=='hi' else '«أنا رأيته يبول قاعدا»'
        final='देखो! वो औरतों की तरह बैठ कर पेशाब करते हैं.' if language=='hi' else 'دیکھو! وہ عورتوں کی طرح بیٹھ کر پیشاب کرتے ہیں ۔'
        a,b=locate(text,quote);c,d=locate(text,final)
        return [(0,locate(text,stop)[0],kind,speaker,family),
                (a,b,'quoted_companion_observation','Aisha as attributed in the compiler discussion; the source pronoun is not expanded','deenhindi-ibnmajah:309:aisha-quoted-observation'),
                (c,d,'quoted_historical_remark','Unnamed speaker in another report quoted by Ahmad ibn Abd alRahman; no repaired Hindi reporter identity or named pronoun subject','deenhindi-ibnmajah:309:unnamed-quoted-remark')]
    if number=='1232':
        outer='(अबू मुआविया ने कहा: जब आप मरज़ की गिरानी में मुब्तला हुए)' if language=='hi' else '( ابومعاویہ نے کہا: جب آپ مرض کی گرانی میں مبتلا ہوئے )'
        inner='जब आप मरज़ की गिरानी में मुब्तला हुए' if language=='hi' else 'جب آپ مرض کی گرانی میں مبتلا ہوئے'
        a,b=locate(text,outer);c,d=locate(text,inner)
        assert a<c<d<b
        return [(0,a,kind,speaker,family),
                (c,d,'transmitted_wording_variant_of_prophetic_illness','AbuMuawiya transmitting an alternative illness phrase within Aisha account; no independent eyewitness claim',family),
                (b,len(text),kind,speaker,family)]
    begin=locate(text,STARTS[key])[0] if key in STARTS else 0
    end=locate(text,STOPS[key])[0] if key in STOPS else len(text)
    splits=SPLITS.get(key,[])
    if isinstance(splits,str):splits=[splits]
    bounds=[begin]+[locate(text,x)[0] for x in splits]+[end]
    assert bounds==sorted(set(bounds)),key
    descriptors=COMPONENTS.get(number,[SPECS[number]])
    assert len(descriptors)==len(bounds)-1
    return [(a,b,*descriptor,f'deenhindi-ibnmajah:{number}:report-{1 if number=="927" else i+1}')
            for i,((a,b),descriptor) in enumerate(zip(zip(bounds,bounds[1:]),descriptors))]

def make_spans(number,language,text,reason):
    component_sections=sections(number,language,text)
    omissions=[]
    for literal in CUTS.get((number,language),[]):
        a,b=locate(text,literal)
        assert any(left<=a<b<=right for left,right,*_ in component_sections),(number,language,'cut outside selected report',literal)
        omissions.append((a,b))
        apparatus_receipts.append({'occurrence_id':'deenhindi-ibnmajah:'+number,'language':language,
            'whole_field_sha256':sha(text.encode()),'start':a,'end':b,'text':text[a:b],
            'sha256':sha(text[a:b].encode()),'decision':'retained_source_context',
            'reason':'Individually read source locator, footnote reference, lexical explanation, or explicitly framed narrator interpretation; not a blanket parenthesis rule.'})
    omissions.sort()
    assert all(omissions[i][1]<=omissions[i+1][0] for i in range(len(omissions)-1))
    selected=[]
    for i,(left,right,kind,speaker,family) in enumerate(component_sections):
        cursor=left;pieces=[]
        for a,b in omissions:
            if b<=left or a>=right:continue
            assert left<=a<b<=right
            if cursor<a:pieces.append((cursor,a))
            cursor=b
        if cursor<right:pieces.append((cursor,right))
        for a,b in pieces:
            assert text[a:b].strip(),(number,language,'whitespace-only selected span',a,b)
            selected.append({'start':a,'end':b,'sha256':sha(text[a:b].encode()),
                'component_id':f'{language}-report-{i+1}','source_report_family_id':family,
                'report_type':kind,'speaker':speaker,'reason':reason})
    for literal in REQUIRED_RETENTIONS.get((number,language),[]):
        a,b=locate(text,literal)
        assert sum(max(0,min(b,s['end'])-max(a,s['start'])) for s in selected)==b-a,(number,language,'required meaning lost',literal)
    return selected

reading_notes=[]
for key,item in targets.items():
    identity,language=key;number=identity.rsplit(':',1)[1]
    saved=sources[identity];decision=rows[identity]
    assert sha(importer.json_bytes(saved['source_record']))==decision['source_record_sha256']==item['source_record_sha256']
    field=next(f for f in decision['fields'] if f['language']==language)
    assert field['reviewed'] is False and not field['selected_spans']
    assert sha(encoded(field))==item['current_field_decision_sha256']
    text=saved['source_record'][field['source_field']]
    assert text==item['text'] and sha(text.encode())==item['text_sha256']==field['text_sha256']
    n=notes_by_key[key];assert n['fully_read'] is True and n['text_sha256']==item['text_sha256']
    assert len(text)==item['characters']==n['characters'] and len(text.encode())==item['utf8_bytes']==n['utf8_bytes']
    reason=n['note']+(' Final boundary decision: '+FOCUSED_ADJUDICATIONS[number] if number in FOCUSED_ADJUDICATIONS else '')
    selected=make_spans(number,language,text,reason)
    assert selected
    action='whole' if len(selected)==1 and selected[0]['start']==0 and selected[0]['end']==len(text) else 'excerpts'
    field.update(decision=action,reviewed=True,chars_reviewed=len(text),bytes_reviewed=len(text.encode()),
        review_scope='complete_current_language_field',review_extension_id=EXTENSION,
        review_method='complete_own_field_manual_reading_and_exact_span_decisions',reason=reason,
        selected_spans=selected,independent_pro_qc='not_performed')
    context=[];cursor=0
    for span in selected:
        if cursor<span['start']:context.append((cursor,span['start']))
        cursor=span['end']
    if cursor<len(text):context.append((cursor,len(text)))
    reading_notes.append({'occurrence_id':identity,'source_record_sha256':decision['source_record_sha256'],
        'source_field':field['source_field'],'version_id':field['version_id'],'language':language,
        'complete_field_text':text,'full_field_sha256':sha(text.encode()),'chars_read':len(text),
        'utf8_bytes_read':len(text.encode()),'complete_own_field_read':True,'decision':action,
        'semantic_reading':reason,'selected_spans':selected,
        'retained_context':[{'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode())} for a,b in context]})

notes_bytes=gzip.compress(encoded({'schema':'hadith-bank-field-reading-extension-v1','extension_id':EXTENSION,
    'source_commit':selection['source_commit'],'reader':'/root','independent_pro_qc':'not_performed',
    'frozen_reading_input_sha256':sha(input_bytes),'fields':reading_notes}),mtime=0)
new['field_review_extensions'].append({'extension_id':EXTENSION,'source_commit':selection['source_commit'],
    'previous_active_ledger':{'path':(EVIDENCE/'previous-review-ledger.json.gz').as_posix(),'sha256':sha(old_bytes)},
    'reading_notes':{'path':(EVIDENCE/'complete-field-reading-notes.json.gz').as_posix(),'sha256':sha(notes_bytes)},
    'occurrences':50,'complete_fields_read':83,'complete_fields_by_language':{'hi':33,'ur':50},
    'languages':['hi','ur'],'already_reviewed_hindi_fields_preserved':17,
    'existing_record_dispositions_unchanged':True,'previous_other_language_decisions_unchanged':True,
    'independent_pro_qc':'not_performed'})
new_bytes=gzip.compress(encoded(new),mtime=0)
write(OUT/selection['active_ledger_path'],new_bytes)
write(OUT/EVIDENCE/'previous-review-ledger.json.gz',old_bytes)
write(OUT/EVIDENCE/'complete-field-reading-notes.json.gz',notes_bytes)
write(OUT/EVIDENCE/'full-field-reading-input-83.jsonl.gz',gzip.compress(input_bytes,mtime=0))
for name in ['manual_reading_spec.py','build_extension.py','root-complete-reading-notes.json',
             'source-verification.json','selection.json','preserve-existing-hindi17.json']:
    write(OUT/EVIDENCE/name,(ROOT/name).read_bytes())
write(OUT/EVIDENCE/'explicit-apparatus-decisions.json',encoded({'schema':'source-hash-bound-explicit-apparatus-decisions-v1',
    'decisions':apparatus_receipts,'focused_adjudications':FOCUSED_ADJUDICATIONS,
    'scope':'Only these83 fully read fields; original text remains losslessly partitioned.'}))

# Validate all477 unchanged parent records and all2,385 fields using native code.
if VALIDATION.exists():shutil.rmtree(VALIDATION)
shutil.copytree(OUT,VALIDATION)
baseline_bytes=(ROOT/'pinned-inputs'/old['source_ledger_path']).read_bytes()
assert sha(baseline_bytes)==selection['source_baseline_sha256']
write(VALIDATION/old['source_ledger_path'],baseline_bytes)
original_sources=[json.loads(line) for line in gzip.decompress(baseline_bytes).splitlines()]
assert len(original_sources)==477
reviews=SourceReviews(VALIDATION,'deenhindi')
partitions=metadata_checks=unchanged_fields=untouched_rows=script_checks=0
for saved in original_sources:
    identity=f"deenhindi-{saved['collection']}:{saved['number']}"
    before=importer.canonical_record(saved);input_copy=copy.deepcopy(before)
    derived,action=reviews.apply(before,saved=saved)
    assert before==input_copy and action=='register'
    prior=old_rows[identity];decision=rows[identity]
    assert {k:v for k,v in prior.items() if k!='fields'}=={k:v for k,v in decision.items() if k!='fields'}
    if identity not in sources:assert decision==prior;untouched_rows+=1
    for name in ['id','source_id','number','references','grading','narrator','source_locator','source']:
        assert (name in derived)==(name in before) and derived.get(name)==before.get(name),(identity,name)
        metadata_checks+=1
    assert len(prior['fields'])==len(decision['fields'])==len(before['language_versions'])==len(derived['language_versions'])==5
    for old_field,field,original,result in zip(prior['fields'],decision['fields'],before['language_versions'],derived['language_versions']):
        key=(identity,field['language'])
        if key not in targets:assert old_field==field,key;unchanged_fields+=1
        if 'observed_script' in old_field:
            assert old_field.get('observed_script')==field.get('observed_script')==result['script']
            assert old_field.get('source_script_note')==field.get('source_script_note')
            script_checks+=1
        text=original['text']
        pieces=[(s['start'],s['end'],text[s['start']:s['end']]) for s in field['selected_spans']]
        pieces += [(c['source_span'][0],c['source_span'][1],c['text']) for c in result.get('comments',[]) if 'source_span' in c]
        cursor=0
        for a,b,part in sorted(pieces):
            assert a==cursor and part==text[a:b];cursor=b
        assert cursor==len(text) and ''.join(p[2] for p in sorted(pieces))==text,key
        for name in ['id','language','references']:
            assert result[name]==original[name];metadata_checks+=1
        partitions+=1
reviews.finish()
assert partitions==2385 and unchanged_fields==2302 and untouched_rows==427 and script_checks==19
assert len(reading_notes)==83 and sum(x['chars_read'] for x in reading_notes)==60060
assert sum(x['utf8_bytes_read'] for x in reading_notes)==128277

# Remove precisely the reviewed83 source-bound queue fields; preserve every other row.
queue_before=(ROOT/'pinned-inputs'/selection['priority_queue_path']).read_bytes()
assert sha(queue_before)==selection['priority_queue_sha256']
queue=[json.loads(line) for line in gzip.decompress(queue_before).splitlines()]
removed=[];remaining=[]
for item in queue:
    retained_fields=[]
    for pending_field in item['fields']:
        key=(item['id'],pending_field['language'])
        if key in targets:
            target=targets[key]
            assert pending_field['text_sha256']==target['text_sha256']
            removed.append({'id':item['id'],'field':pending_field,
                'source_record_sha256':item['source_record_sha256'],
                'prior_queue_record_sha256':sha(encoded(item))})
        else:retained_fields.append(pending_field)
    if retained_fields:
        retained=copy.deepcopy(item);retained['fields']=retained_fields
        assert retained==item,'selected50 should have no pending priority sibling after these83 readings'
        remaining.append(retained)
remaining_fields=sum(len(r['fields']) for r in remaining)
remaining_by_language=collections.Counter(f['language'] for r in remaining for f in r['fields'])
assert len(removed)==83 and remaining_fields==6615 and len(remaining)==3598
assert remaining_by_language=={'hi':3320,'ur':3295}
queue_after=gzip.compress(b''.join((json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for x in remaining),mtime=0)
write(OUT/selection['priority_queue_path'],queue_after)
write(OUT/EVIDENCE/'previous-priority-field-queue.jsonl.gz',queue_before)
queue_delta={'schema':'hadith-bank-exact-field-queue-delta-v1','status':'PASS','before_sha256':sha(queue_before),
    'after_sha256':sha(queue_after),'removed_count':83,'removed':removed,
    'remaining_fields':remaining_fields,'remaining_occurrences':len(remaining),
    'remaining_by_language':dict(remaining_by_language),
    'all_other_rows_values_and_order_unchanged':True,'source_occurrence_count_delta':0,'registration_delta':0}
write(OUT/EVIDENCE/'priority-field-queue-delta.json',encoded(queue_delta))

report={'schema':'hadith-bank-language-field-extension-validation-v1','status':'PASS','extension_id':EXTENSION,
    'source_commit':selection['source_commit'],'newly_reviewed_occurrences':50,'newly_fully_read_fields':83,
    'newly_admitted_fields':83,'newly_read_context_only_fields':0,'newly_read_characters':60060,
    'newly_read_utf8_bytes':128277,'new_admissions_by_language':{'hi':33,'ur':50},
    'source_count_delta':0,'registration_delta':0,'prior_active_ledger_sha256':sha(old_bytes),
    'new_active_ledger_sha256':sha(new_bytes),'all_previous_477_record_dispositions_unchanged':True,
    'untouched_rows':untouched_rows,'unchanged_field_decisions':unchanged_fields,
    'already_reviewed_hindi_fields_preserved':17,'existing_script_corrections_preserved':script_checks,
    'native_source_reviews_apply_and_finish':'PASS for all477 records',
    'full_field_partitions_verified':partitions,'metadata_invariants_verified':metadata_checks,
    'raw_and_parsed_source_pairs_independently_reopened':50,
    'source_provenance_report_sha256':sha((ROOT/'source-verification.json').read_bytes()),
    'frozen_reading_input_sha256':sha(input_bytes),'root_reading_notes_sha256':sha((ROOT/'root-complete-reading-notes.json').read_bytes()),
    'explicit_apparatus_cuts':len(apparatus_receipts),'source_http_requests':0,
    'remaining_original3942_priority_fields':remaining_fields,
    'remaining_original3942_priority_occurrences':queue_delta['remaining_occurrences'],
    'remaining_original3942_priority_by_language':queue_delta['remaining_by_language'],
    'independent_pro_qc':'not_performed','independent_candidate_audit':'pending exact final manifest handoff'}
write(OUT/EVIDENCE/'validation.json',encoded(report))
files=[]
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data=path.read_bytes();files.append({'path':path.relative_to(OUT).as_posix(),'local_path':str(path),
            'bytes':len(data),'sha256':sha(data),'git_blob_sha1':gitsha(data)})
manifest={'schema':'hadith-bank-language-extension-delivery-v1','files':files,'total_files':len(files),
    'total_bytes':sum(f['bytes'] for f in files),'validation':report}
write(ROOT/'review-delivery-manifest-v2.json',encoded(manifest))
print(json.dumps(report,indent=2));print('review_manifest_sha256',sha(encoded(manifest)))
