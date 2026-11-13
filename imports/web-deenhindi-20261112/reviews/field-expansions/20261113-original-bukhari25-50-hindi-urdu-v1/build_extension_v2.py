"""Build the bounded fifty-field extension; preserve all477 previous parents.

This is an offline serializer/validator, not a reader or semantic classifier.
All semantic decisions are explicit in manual_readings.py and are bound to the
preceding complete source-first receipt and immutable source input.
"""
from pathlib import Path
import collections, copy, gzip, hashlib, json, shutil, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
from manual_readings_v2 import READINGS
import import_deenhindi as importer
from web_source_reviews import SourceReviews

EXT = '20261113-original-bukhari25-50-hindi-urdu-v1'
EVID = Path('imports/web-deenhindi-20261112/reviews/field-expansions') / EXT
OUT = ROOT / 'publish-v2'
VALID = ROOT / 'validation-repo-v2'
OLD_VALID = ROOT / 'validation-before-repo-v2'
assert not (ROOT / 'draft-delivery-manifest-v2.json').exists(), 'Frozen candidate already exists'

def sha(data): return hashlib.sha256(data).hexdigest()
def git(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def enc(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
def read(path): return json.loads(path.read_bytes())
def put(path, data): path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
def leaves(value):
    if isinstance(value, dict): return sum(leaves(v) for v in value.values())
    if isinstance(value, list): return sum(leaves(v) for v in value)
    return 1
def equal(a, b):
    assert a == b
    return leaves(a)
def locate(text, literal):
    assert text.count(literal) == 1, ('Nonunique exact anchor', literal)
    start = text.index(literal)
    return start, start+len(literal)
def gaps(text, spans):
    result=[]; cursor=0
    for span in spans:
        if cursor < span['start']: result.append((cursor, span['start']))
        cursor=span['end']
    if cursor < len(text): result.append((cursor,len(text)))
    return result
def normalized_receipt(version):
    result=copy.deepcopy(version)
    review=result['source']['manual_review']
    # The overwritten ledger bytes necessarily get new receipts. Every other
    # output value of every unselected field must remain exactly unchanged.
    review.pop('sha256',None); review.pop('uncompressed_sha256',None)
    return result

selection_raw=(ROOT/'input/selection.json').read_bytes()
selection=json.loads(selection_raw)
assert sha(selection_raw)=='be655a49396693283f17d0eaac5a6eedebe59e4e67bb923ac41dc89916766ac9'
pin=selection['source_publication_commit']
assert pin=='e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d'
input_raw=(ROOT/'input/full-hi-ur-reading-input-50.jsonl').read_bytes()
assert sha(input_raw)==selection['full_field_reading_input_sha256']=='7e7e10e8d24a857a5261db2219af52816874763c56465163cc358640168acc3e'
inputs=list(map(json.loads,input_raw.splitlines()))
targets={(r['occurrence_id'],r['language']):r for r in inputs}
assert len(targets)==50 and {(i.split(':')[1],l) for i,l in targets}==set(READINGS)
own_raw=(ROOT/'complete-source-first-reading-receipt.json').read_bytes()
assert sha(own_raw)=='8bbcf7eae89dd0fc13c497259b38624fe23315e026c99a8b5bb651eda4741893'
own=json.loads(own_raw)
assert own['all_readings_precede_candidate_authoring'] and own['complete_fields']==50
own_fields={(r['occurrence_id'],r['language']):r for r in own['readings']}
assert len(own_fields)==50

proof_raw=(ROOT/'input/source-verification.json').read_bytes()
assert sha(proof_raw)=='4209276da8dc2c2c7cc1c77ff4d902984f4bb1f8419510b0d345f1185c7ef035'
proof=json.loads(proof_raw)
assert proof['status']=='PASS' and proof['complete_raw_reparses']==25 and proof['saved_files_reopened']==50
for row in proof['records']:
    for f in row['files']:
        stored=(ROOT/'source-evidence'/f['path']).read_bytes(); plain=gzip.decompress(stored)
        assert len(stored)==f['bytes'] and sha(stored)==f['sha256']
        assert git(stored)==f['git_blob_sha1']==f['github_blob_sha1']
        assert len(plain)==f['plain_bytes'] and sha(plain)==f['plain_sha256']

old_raw=(ROOT/'input/pinned'/selection['active_review_path']).read_bytes()
queue_raw=(ROOT/'input/pinned'/selection['canonical_queue_path']).read_bytes()
baseline_raw=(ROOT/'input/pinned'/selection['source_baseline_path']).read_bytes()
assert sha(old_raw)==selection['active_review_sha256']=='ac53483e3eab6c0a4c508c86180c75091792e895b5e29f602a061aa2cd080c62'
assert sha(queue_raw)==selection['canonical_queue_sha256']=='343e72455fe122b59b37d795a59f9f8cca2358077723f1c725e4b1eaa3f57227'
assert sha(baseline_raw)==selection['source_baseline_sha256']=='5c9598c1c61cee509155013dde44221de2e17f11bd29d0f475092f2a6e86fb36'
source_raw=(ROOT/'input/source-25.jsonl').read_bytes()
assert sha(source_raw)==selection['selected_source_baseline_sha256']=='8b5454d4143ad95c480fb1b6115f670a6e75ff8c8584f309c4c0cd7d3db600a7'
old=json.loads(gzip.decompress(old_raw)); new=copy.deepcopy(old)
assert sha(baseline_raw)==old['source_ledger_sha256']
assert sha(gzip.decompress(baseline_raw))==old['source_ledger_uncompressed_sha256']
old_rows={r['occurrence_id']:r for r in old['records']}
new_rows={r['occurrence_id']:r for r in new['records']}
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,source_raw.splitlines())}
assert len(old_rows)==477 and len(sources)==25 and set(sources)=={i for i,l in targets}
baseline_rows=list(map(json.loads,gzip.decompress(baseline_raw).splitlines()))
baseline_by_id={'deenhindi-'+r['collection']+':'+r['number']:r for r in baseline_rows}
assert all(s==baseline_by_id[i] for i,s in sources.items())
notes=[]; changes=[]; apparatus=[]; parentheses=[]; spans_total=0
for (ident,language),item in targets.items():
    spec=READINGS[(item['number'],language)]; saved=sources[ident]
    first=own_fields[(ident,language)]
    assert first['complete_own_field_read'] and first['text_sha256']==item['text_sha256']
    row=new_rows[ident]
    assert row['decision']=='register'
    assert row['source_record_sha256']==sha(importer.json_bytes(saved['source_record']))==item['source_record_sha256']
    field=next(f for f in row['fields'] if f['language']==language)
    prior=copy.deepcopy(field)
    assert prior['reviewed'] is False and prior['decision']=='unreviewed' and not prior['selected_spans']
    assert sha(enc(prior))==item['original_active_field_sha256']==first['original_active_field_sha256']
    text=saved['source_record'][field['source_field']]
    assert text==item['text'] and sha(text.encode())==field['text_sha256']==item['text_sha256']
    assert len(text)==first['characters'] and len(text.encode())==first['utf8_bytes']
    note=spec.get('final_note', first['source_first_note'])
    if first['language_specific_note']: note+=' '+first['language_specific_note']
    if spec['annotations']: note+=' Exact-boundary qualifications: '+' '.join(spec['annotations'])
    cuts=sorted(locate(text,x) for x in spec['context'])
    assert all(a[1]<=b[0] for a,b in zip(cuts,cuts[1:]))
    spans=[]; last=0
    for index,part in enumerate(spec['segments'],1):
        start=0 if part['start'] is None else locate(text,part['start'])[0]
        end=len(text) if part['end'] is None else locate(text,part['end'])[0]
        assert 0<=last<=start<end<=len(text); last=end
        pieces=[(start,end)]
        for left,right in cuts:
            result=[]
            for a,b in pieces:
                if b<=left or right<=a: result.append((a,b))
                else:
                    assert start<=left<right<=end
                    if a<left: result.append((a,left))
                    if right<b: result.append((right,b))
            pieces=result
        for a,b in pieces:
            assert text[a:b].strip(), ('Isolated punctuation/space segment requires explicit decision',ident,language,a,b)
            spans.append({'start':a,'end':b,'sha256':sha(text[a:b].encode()),
                'component_id':language+'-report-'+str(index),
                'source_report_family_id':part.get('source_report_family_id',ident+':report-1'),
                'report_type':part.get('type',spec['type']),
                'speaker':part.get('speaker',spec['speaker']), 'reason':note})
    assert spans
    context=gaps(text,spans)
    assert all(any(a<=left<right<=b for a,b in context) for left,right in cuts)
    action='whole' if len(spans)==1 and spans[0]['start']==0 and spans[0]['end']==len(text) else 'excerpts'
    field.update(decision=action, reviewed=True, chars_reviewed=len(text), bytes_reviewed=len(text.encode()),
        review_scope='complete_current_language_field', review_extension_id=EXT,
        review_method='complete_own_field_manual_reading_and_exact_span_decisions', reason=note,
        selected_spans=spans, report_type=spec['type'], speaker=spec['speaker'], independent_pro_qc='not_performed')
    if spec['annotations']:
        field['source_text_annotations']=[{'kind':'own_field_attribution_or_wording_qualification','note':a,'new_translation':False} for a in spec['annotations']]
    retained=[{'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode())} for a,b in context]
    notes.append({'occurrence_id':ident,'language':language,'source_field':field['source_field'],
        'version_id':field['version_id'],'complete_field_text':text,'full_field_sha256':sha(text.encode()),
        'chars_read':len(text),'utf8_bytes_read':len(text.encode()),'complete_own_field_read':True,
        'source_first_note_unchanged':first['source_first_note'],'language_specific_note_unchanged':first['language_specific_note'],
        'semantic_reading':note,'decision':action,'selected_spans':spans,'retained_context':retained,
        'own_field_annotations':copy.deepcopy(spec['annotations'])})
    changes.append({'occurrence_id':ident,'language':language,'version_id':field['version_id'],
        'source_text_sha256':field['text_sha256'],'source_record_sha256':row['source_record_sha256'],
        'before_field_decision_sha256':sha(enc(prior)),'after_field_decision_sha256':sha(enc(field)),
        'before_decision':prior['decision'],'after_decision':action,'parent_disposition_unchanged':True})
    apparatus.extend({'occurrence_id':ident,'language':language,**gap,'reason':note} for gap in retained)
    stack=[]
    for offset,char in enumerate(text):
        if char=='(': stack.append(offset)
        elif char==')' and stack:
            a=stack.pop(); b=offset+1
            coverage=sum(max(0,min(b,s['end'])-max(a,s['start'])) for s in spans)
            assert coverage in (0,b-a),('Partial parenthesis requires explicit handling',ident,language,text[a:b])
            parentheses.append({'occurrence_id':ident,'language':language,'start':a,'end':b,
                'text':text[a:b],'sha256':sha(text[a:b].encode()),
                'disposition':'retained_report_qualification_or_honorific' if coverage else 'retained_context',
                'decision_basis':note})
    assert not stack
    spans_total+=len(spans)

assert len(notes)==50 and sum(n['chars_read'] for n in notes)==40338 and sum(n['utf8_bytes_read'] for n in notes)==86636
notes_raw=gzip.compress(enc({'schema':'hadith-bank-field-reading-extension-v1','extension_id':EXT,
    'reader':'/root/checkpoint_inventory','source_commit':pin,'independent_pro_qc':'not_performed',
    'input_sha256':sha(input_raw),'source_first_receipt_sha256':sha(own_raw),'fields':notes}),mtime=0)
new['field_review_extensions'].append({'extension_id':EXT,'source_commit':pin,
    'previous_active_ledger':{'path':str(EVID/'previous-review-ledger.json.gz'),'sha256':sha(old_raw)},
    'reading_notes':{'path':str(EVID/'complete-field-reading-notes.json.gz'),'sha256':sha(notes_raw)},
    'occurrences':25,'complete_fields_read':50,'complete_fields_by_language':{'hi':25,'ur':25},
    'existing_record_dispositions_unchanged':True,'all_other_field_decisions_unchanged':True,
    'independent_pro_qc':'not_performed',
    'independent_boundary_amendment': {
        'path':str(EVID/'independent-boundary-amendment-v2/amendment-receipt.json'),
        'previous_active_sha256':'c069236c43adbb00cd1c62214372a71353959fc58ccd8f9ecb985e263436a7b2',
        'findings_sha256':'3329baca9ec9275c696d9ec5d2c63ad582d006788c5d8e3b25ca4d83da2404fe',
        'exact_changed_fields':2,'source_characters_restored':36}})
assert {k:v for k,v in old.items() if k not in ['records','field_review_extensions']}=={k:v for k,v in new.items() if k not in ['records','field_review_extensions']}
assert new['field_review_extensions'][:-1]==old['field_review_extensions']
active_raw=gzip.compress(enc(new),mtime=0)
for folder,data in [(VALID,active_raw),(OLD_VALID,old_raw)]:
    if folder.exists(): shutil.rmtree(folder)
    put(folder/selection['active_review_path'],data)
    put(folder/selection['source_baseline_path'],baseline_raw)
before_engine=SourceReviews(OLD_VALID,'deenhindi')
engine=SourceReviews(VALID,'deenhindi')
assert len(engine.decisions)==len(before_engine.decisions)==477
partitions=untouched_rows=unchanged_fields=unchanged_native_fields=preserved_scripts=0
parent_leaf_checks=language_leaf_checks=source_leaf_checks=0
for saved in baseline_rows:
    ident='deenhindi-'+saved['collection']+':'+saved['number']
    prior=old_rows[ident]; decision=new_rows[ident]
    assert {k:v for k,v in prior.items() if k!='fields'}=={k:v for k,v in decision.items() if k!='fields'}
    if ident not in sources: assert decision==prior; untouched_rows+=1
    original=importer.canonical_record(saved); frozen=copy.deepcopy(original)
    old_result,old_action=before_engine.apply(copy.deepcopy(original),saved=saved)
    result,action=engine.apply(original,saved=saved)
    assert original==frozen and action==old_action=='register'
    for name in ['id','number','narrator','grading','references','source_locator','source','translator','translation_provenance','rights','source_headings']:
        parent_leaf_checks+=equal(result[name],frozen[name])
    assert len(prior['fields'])==len(decision['fields'])==len(result['language_versions'])==5
    for of,nf,ov,bv,nv in zip(prior['fields'],decision['fields'],frozen['language_versions'],old_result['language_versions'],result['language_versions']):
        key=(ident,nf['language'])
        if key not in targets:
            assert of==nf; unchanged_fields+=1
            assert normalized_receipt(bv)==normalized_receipt(nv); unchanged_native_fields+=1
        if 'observed_script' in of:
            assert of['observed_script']==nf['observed_script']==nv['script']
            assert of.get('source_script_note')==nf.get('source_script_note'); preserved_scripts+=1
        for name in ['id','language','references','translation_provenance']:
            language_leaf_checks+=equal(ov[name],nv[name])
        for name,value in ov['source'].items(): source_leaf_checks+=equal(value,nv['source'][name])
        text=ov['text']; selected=nv['source'].get('text_spans',{}).get('quotation_spans',[])
        assert (nv['text'] or '')==''.join(text[a:b] for a,b in selected)
        parts=[(a,b,text[a:b]) for a,b in selected]
        for comment in nv['comments']:
            a,b=comment['source_span']
            assert comment['scope']=='source_context_not_narration'
            assert comment['text']==text[a:b] and comment['source_text_sha256']==sha(text[a:b].encode())
            parts.append((a,b,comment['text']))
        cursor=0
        for a,b,t in sorted(parts):
            assert a==cursor and a<b<=len(text) and t==text[a:b]; cursor=b
        assert cursor==len(text) and ''.join(t for a,b,t in sorted(parts))==text
        partitions+=1
before_engine.finish(); engine.finish()
assert partitions==2385 and untouched_rows==452 and unchanged_fields==unchanged_native_fields==2335
assert preserved_scripts==19

queue_lines=gzip.decompress(queue_raw).splitlines(keepends=True)
queue=list(map(json.loads,queue_lines)); remaining_lines=[]; removed=[]
for line,row in zip(queue_lines,queue):
    matches=[f for f in row['fields'] if (row['id'],f['language']) in targets]
    if matches:
        assert len(matches)==len(row['fields'])==2 and row['id'] in sources
        for f in matches:
            target=targets[(row['id'],f['language'])]
            assert f['text_sha256']==target['text_sha256'] and row['source_record_sha256']==target['source_record_sha256']
        removed.append(row)
    else: remaining_lines.append(line)
after=list(map(json.loads,remaining_lines))
assert len(removed)==25 and {r['id'] for r in removed}==set(sources)
assert len(after)==3379 and sum(len(r['fields']) for r in after)==6361
counts=collections.Counter(f['language'] for r in after for f in r['fields'])
assert counts=={'hi':3285,'ur':3076}
queue_after=gzip.compress(b''.join(remaining_lines),mtime=0)
assert gzip.decompress(queue_after)==b''.join(line for line,row in zip(queue_lines,queue) if row['id'] not in sources)
delta={'schema':'hadith-bank-exact-language-priority-queue-delta-v1','source_commit':pin,
    'extension_id':EXT,'before_sha256':sha(queue_raw),'after_sha256':sha(queue_after),
    'before_occurrences':3404,'after_occurrences':3379,'before_fields':6411,'after_fields':6361,
    'after_language_counts':dict(counts),'removed_fields':changes,
    'removed_occurrence_ids':[r['id'] for r in removed],
    'remaining_original_json_line_bytes_and_order_exact':True,'parent_registration_delta':0,
    'scope':'Remove exactly the fifty individually read Hindi/Urdu fields in the selected original477 manual-ledger cohort. The publisher owns canonical queue composition.'}
validation={'schema':'hadith-bank-original-bukhari25-field-extension-native-validation-v1','status':'PASS',
    'source_commit':pin,'active_before_sha256':sha(old_raw),'active_after_sha256':sha(active_raw),
    'occurrences_extended':25,'complete_fields_read':50,'characters_read':40338,'utf8_bytes_read':86636,
    'new_fields_by_language':{'hi':25,'ur':25},'admitted_fields':50,'selected_spans':spans_total,
    'context_gaps':len(apparatus),'all477_parent_dispositions_unchanged':True,
    'before_and_after_all477_native_apply_finish':'PASS','lossless_partitions':partitions,
    'untouched_parent_records':untouched_rows,'unchanged_other_field_decisions':unchanged_fields,
    'unchanged_other_native_language_outputs_except_ledger_receipt_hashes':unchanged_native_fields,
    'preserved_script_corrections':preserved_scripts,'new_script_corrections':0,
    'parent_metadata_leaf_equalities':parent_leaf_checks,'language_metadata_leaf_equalities':language_leaf_checks,
    'source_metadata_leaf_equalities':source_leaf_checks,'source_files_verified':50,'raw_reparses':25,
    'source_first_reading_sha256':sha(own_raw),'source_verification_sha256':sha(proof_raw),
    'engine_sha256':engine.engine_sha256,'remaining_priority_fields_candidate':6361,
    'remaining_priority_occurrences_candidate':3379,'remaining_priority_fields_by_language':dict(counts),
    'independent_review_status':'pending_separate_independent_gate','independent_pro_qc':'not_performed',
    'source_http_requests':0,'github_writes':0,'source_count_delta':0,'parent_registration_delta':0}

put(OUT/selection['active_review_path'],active_raw)
for name,data in [
    ('previous-review-ledger.json.gz',old_raw),('previous-priority-field-queue.jsonl.gz',queue_raw),
    ('candidate-priority-field-queue.jsonl.gz',queue_after),('complete-field-reading-notes.json.gz',notes_raw),
    ('full-field-reading-input-50.jsonl.gz',gzip.compress(input_raw,mtime=0)),
    ('source-ledger-25.jsonl.gz',gzip.compress(source_raw,mtime=0)),
    ('priority-field-queue-delta.json',enc(delta)),('native-validation.json',enc(validation)),
    ('field-decision-delta.json',enc(changes)),
    ('source-apparatus-inventory.json',enc({'context_gaps':apparatus,'parenthetical_inventory':parentheses,'blanket_parenthesis_exclusion':False})),
    ('selection.json',selection_raw),('complete-source-first-reading-receipt.json',own_raw),
    ('source-verification.json',proof_raw),
]: put(OUT/EVID/name,data)
for name in ['manual_readings.py','manual_readings_v2.py','build_extension.py','build_extension_v2.py','verify_sources.py','source-input-delivery-manifest.json']:
    put(OUT/EVID/name,(ROOT/name).read_bytes())
# The candidate queue is retained in evidence; no canonical queue overwrite is
# claimed until the final independent gate and publisher composition.
files=[]
for path in sorted(p for p in OUT.rglob('*') if p.is_file()):
    data=path.read_bytes(); files.append({'path':str(path.relative_to(OUT)),'local_path':str(path),
        'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data)})
manifest={'schema':'hadith-bank-original-language-extension-delivery-v1','status':'PASS',
    'summary':validation,'canonical_queue_publication':'Exact fifty-field candidate delta archived; root owns final canonical queue publication.',
    'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
put(ROOT/'draft-delivery-manifest-v2.json',enc(manifest))
print(json.dumps(validation,indent=2))
print(json.dumps({'manifest_sha256':sha(enc(manifest)),'files':len(files),'bytes':manifest['total_bytes']},indent=2))
