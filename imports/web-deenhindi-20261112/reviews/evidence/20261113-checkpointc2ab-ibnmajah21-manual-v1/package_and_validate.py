"""Serialize the twenty-one complete own-field Hindi/Urdu readings and verify native preservation."""
import collections
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
from manual_readings import READINGS

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
COMMIT='c2ab74d74821e244d8a83620f0e8e68dda694b16'
NAME='20261113-checkpointc2ab-ibnmajah21-manual-v1'
OUT=ROOT/'publish-v1'
REV=Path('imports/web-deenhindi-20261112/reviews')
EVIDENCE=REV/'evidence'/NAME
ACTIVE=REV/('source-review-'+NAME+'.json.gz')
sha=lambda data:hashlib.sha256(data).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def put(relative,data):
    path=OUT/relative;path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        assert path.read_bytes()==data,('immutable candidate collision',str(path))
    else:
        path.write_bytes(data)
    return path


def anchor(text,value):
    assert isinstance(value,str) and text.count(value)==1,('nonunique/missing explicit anchor',repr(value),text.count(value))
    return text.index(value)


def complement(text,spans):
    intervals=[];cursor=0
    for span in spans:
        start,end=span['start'],span['end']
        assert 0<=cursor<=start<end<=len(text)
        if start>cursor:intervals.append((cursor,start))
        cursor=end
    if cursor<len(text):intervals.append((cursor,len(text)))
    return intervals


def field_review(version,index,note):
    text=version['text'];language=version['language'];spans=[];explicit_cuts=[]
    result={'version_id':version['id'],'language':language,'source_field':importer.LANGUAGE_FIELDS[language],
        'field_path':['language_versions',index,'text'],'text_sha256':sha(text.encode()),'text_chars':len(text),
        'reviewed':note is not None,'chars_reviewed':len(text) if note else 0,'bytes_reviewed':len(text.encode()) if note else 0}
    if note is None:
        result.update(decision='unreviewed',selected_spans=[],review_scope='not_read_in_this_batch',
            reason='This sibling language has not received its own complete semantic reading in this batch. Its exact full source text remains context without quotation admission.')
        return result
    if not note.get('context_all'):
        for snippet in note.get('context',[]):
            start=anchor(text,snippet);explicit_cuts.append((start,start+len(snippet)))
        for repeated in note.get('context_repeated',[]):
            snippet=repeated['text'];assert text.count(snippet)==repeated['count']
            cursor=0
            for _ in range(repeated['count']):
                start=text.index(snippet,cursor);explicit_cuts.append((start,start+len(snippet)));cursor=start+len(snippet)
        explicit_cuts.sort();assert all(a[1]<=b[0] for a,b in zip(explicit_cuts,explicit_cuts[1:]))
        parts=note.get('segments',[{'start':None,'end':None}]);last=0
        for n,part in enumerate(parts,1):
            start=0 if part['start'] is None else anchor(text,part['start'])
            end=len(text) if part['end'] is None else anchor(text,part['end'])
            assert 0<=last<=start<end<=len(text);last=end
            keep=[(start,end)]
            for a,b in explicit_cuts:
                pieces=[]
                for x,y in keep:
                    if b<=x or y<=a:pieces.append((x,y))
                    else:
                        if x<a:pieces.append((x,a))
                        if b<y:pieces.append((b,y))
                keep=pieces
            for a,b in keep:
                assert text[a:b].strip(),('empty selected fragment',version['id'],a,b)
                spans.append({'start':a,'end':b,'sha256':sha(text[a:b].encode()),
                    'component_id':part.get('id','report-'+str(n)),'report_type':part.get('type',note['type']),
                    'speaker':part.get('speaker',note['speaker']),'reason':note['note']})
        assert spans
    contexts=complement(text,spans)
    assert all(any(x<=a<b<=y for x,y in contexts) for a,b in explicit_cuts)
    result.update(decision='source_context' if not spans else 'whole' if len(spans)==1 and spans[0]['start']==0 and spans[0]['end']==len(text) else 'excerpts',
        selected_spans=spans,reason=note['note'],review_method='manual_complete_own_field_reading_and_exact_span_selection',
        review_scope='The complete saved '+language+' field was read independently for its own attribution, report content, apparatus, source defects and exact boundaries. No sibling supplies absent wording.',
        reviewed_context_spans=[{'start':a,'end':b,'sha256':sha(text[a:b].encode()),'reason':note['note']} for a,b in contexts],
        explicit_lexical_or_apparatus_cuts=[{'start':a,'end':b,'sha256':sha(text[a:b].encode()),'text':text[a:b]} for a,b in explicit_cuts])
    if spans:result.update(report_type=note['type'],speaker=note['speaker'])
    return result


source_bytes=(ROOT/'source-21.jsonl').read_bytes();rows=[json.loads(line) for line in source_bytes.splitlines()]
assert sha(source_bytes)=='9f0b035f1c285740f6d1dd0ad0405ff000a94bc31e75909d012f546c5ad175e5'
source_checks=json.loads((ROOT/'source-verification.json').read_bytes());checks={r['occurrence_id']:r for r in source_checks['records']}
assert source_checks['result']=='passed' and source_checks['source_commit']==COMMIT and len(rows)==len(READINGS)==len(checks)==21
assert source_checks['raw_reparses_equal']==21
records=[];boundary_view=[];empty_states=[]
for saved in rows:
    key=saved['collection']+':'+saved['number'];oid='deenhindi-'+key;baseline=importer.canonical_record(saved)
    assert set(READINGS[key])<=set(v['language'] for v in baseline['language_versions'])
    fields=[field_review(v,i,READINGS[key].get(v['language'])) for i,v in enumerate(baseline['language_versions'])]
    chosen=any(f['selected_spans'] for f in fields)
    if not chosen:assert all(f['reviewed'] and f['decision']=='source_context' for f in fields)
    empty=[{'language':language,'source_field':field,'source_value':saved['source_record'].get(field)} for language,field in importer.LANGUAGE_FIELDS.items() if saved['source_record'].get(field) in ('',None)]
    empty_states.extend({'occurrence_id':oid,**item,'inspected':True} for item in empty)
    decision={'occurrence_id':oid,'collection':saved['collection'],'number':saved['number'],'decision':'register' if chosen else 'exclude',
        'source_record_sha256':sha(importer.json_bytes(saved['source_record'])),'source_snapshot':saved['snapshot'],
        'source_parsed_path':saved['parsed_path'],'source_parsed_sha256':checks[oid]['source_parsed_descriptor']['sha256'],
        'source_reference_verbatim':saved['source_reference_verbatim'],'numbering_system':'deenhindi_source_local',
        'external_canonical_identity':None,'verified_external_reference':None,'independent_pro_qc':'not_performed',
        'reviewer':'OpenAI assistant /root/queue_audit; complete own-field reading, not independent Pro certification',
        'report_type':'source_numbered_attributed_report_with_per_field_classification' if chosen else 'source_only_compiler_apparatus_or_unavailable_body',
        'speaker':'See each individually read language and report component for its actual source attribution.' if chosen else None,
        'reason':'Complete Hindi and Urdu readings support the selected source-bound report or fragment under its actual speaker and stated limits. Unread siblings remain context; all apparatus and source defects are retained.' if chosen else 'Every nonempty source field was actually read. This occurrence supplies only a missing-body pointer, compiler/transmission/legal apparatus, or literal unavailable-body notice. Preserve all original text and metadata as source context without reconstructing a report.',
        'fields':fields,'inspected_empty_source_fields':empty}
    assert decision['source_record_sha256']==checks[oid]['source_record_sha256'];records.append(decision)
    body=saved['source_record'];boundary_view.append({'occurrence_id':oid,'decision':decision['decision'],'source_reference_verbatim':saved['source_reference_verbatim'],
        'source_record_sha256':decision['source_record_sha256'],'fields':[{'language':f['language'],'source_field':f['source_field'],'text_sha256':f['text_sha256'],'source_text':body[f['source_field']],
            'selected':[dict(s,text=body[f['source_field']][s['start']:s['end']]) for s in f['selected_spans']],
            'context':[dict(s,text=body[f['source_field']][s['start']:s['end']]) for s in f['reviewed_context_spans']],
            'reason':f['reason']} for f in fields if f['reviewed']]})
baseline_path=EVIDENCE/'source-ledger-21.jsonl.gz';baseline_data=gzip.compress(source_bytes,mtime=0);put(baseline_path,baseline_data)
document={'schema':'hadith-bank-web-source-review-v1','site':'deenhindi','review_batch':NAME,'review_date_utc':'2026-11-13',
    'source_commit':COMMIT,'independent_pro_qc':'not_performed','source_ledger_path':baseline_path.as_posix(),
    'source_ledger_sha256':sha(baseline_data),'source_ledger_uncompressed_sha256':sha(source_bytes),
    'scope':'21 newly acquired held IbnMajah occurrences from checkpointc2ab. All42 Hindi/Urdu fields were completely read independently;63 Arabic/English/Roman-Urdu siblings remain unread source context. Hindi2169 remains explicitly truncated;2189 and2195 retain their visibly qualified source-wording defects. No missing text or identity is reconstructed.',
    'records':records}
active_data=gzip.compress(enc(document),mtime=0);put(ACTIVE,active_data)
put(EVIDENCE/'source-verification.json.gz',gzip.compress((ROOT/'source-verification.json').read_bytes(),mtime=0))
put(EVIDENCE/'manual-field-reading-notes.json.gz',gzip.compress(enc({'schema':'hadith-bank-manual-field-reading-notes-v1','review_batch':NAME,'source_commit':COMMIT,'records':READINGS,'inspected_empty_source_fields':empty_states,'no_heuristic_batch_approvals':True,'independent_pro_qc':'not_performed'}),mtime=0))
put(EVIDENCE/'full-hi-ur-reading-input-42.jsonl.gz',gzip.compress((ROOT/'full-hi-ur-reading-input-42.jsonl').read_bytes(),mtime=0))
put(EVIDENCE/'input-delivery-manifest.json',(ROOT/'input-delivery-manifest.json').read_bytes())
put(EVIDENCE/'manual_readings.py',(ROOT/'manual_readings.py').read_bytes())
put(EVIDENCE/'package_and_validate.py',Path(__file__).read_bytes())
engine=SourceReviews(OUT,'deenhindi');totals=collections.Counter();coverage=collections.defaultdict(collections.Counter);books=collections.defaultdict(collections.Counter);derived=[]
metadata=('id','language','book_key','edition','title','source','number','narrator','translator','ai_translation','translation_provenance','commentary','footnotes','references','grading','page','source_headings','rights','source_locator')
for saved,decision in zip(rows,records):
    baseline=importer.canonical_record(saved);before=copy.deepcopy(baseline);result,action=engine.apply(baseline,saved=saved)
    assert baseline==before and action==decision['decision']
    for name in metadata:assert result.get(name)==before.get(name),(decision['occurrence_id'],name)
    assert result['number']['canonical'] is None and result['review']['independent_pro_qc']=='not_performed' and result['review']['certified_release_eligible'] is False
    assert len(result['language_versions'])==len(before['language_versions'])==len(decision['fields'])
    admitted={}
    for original,version,field in zip(before['language_versions'],result['language_versions'],decision['fields']):
        text=original['text'];language=original['language'];spans=field['selected_spans'];pieces=[]
        assert version['id']==original['id']==field['version_id'] and version['language']==language==field['language']
        assert version['references']==original['references'] and version['translation_provenance']==original['translation_provenance']
        assert field['text_sha256']==sha(text.encode()) and field['text_chars']==len(text) and saved['source_record'][field['source_field']]==text
        for count in (totals,coverage[language]):count['nonempty_fields']+=1
        if field['reviewed']:
            assert field['chars_reviewed']==len(text) and field['bytes_reviewed']==len(text.encode())
            for count in (totals,coverage[language]):count['complete_fields_read']+=1;count['characters_read']+=len(text);count['utf8_bytes_read']+=len(text.encode())
        else:
            assert not spans and field['decision']=='unreviewed' and field['chars_reviewed']==field['bytes_reviewed']==0
            for count in (totals,coverage[language]):count['unread_context_fields']+=1
        if spans:
            assert field['reviewed'] and version['text']==''.join(text[s['start']:s['end']] for s in spans)
            admitted[language]=version['text']
            for span in spans:
                a,b=span['start'],span['end'];assert sha(text[a:b].encode())==span['sha256'];pieces.append((a,b,text[a:b]))
            for count in (totals,coverage[language]):count['admitted_fields']+=1;count['selected_spans']+=len(spans);count['admitted_characters']+=len(version['text']);count['admitted_utf8_bytes']+=len(version['text'].encode())
        else:
            assert version['text'] is None
            if field['reviewed']:
                for count in (totals,coverage[language]):count['fully_read_context_only_fields']+=1
        for comment in version['comments']:
            a,b=comment['source_span'];assert comment['scope']=='source_context_not_narration' and comment['text']==text[a:b] and comment['source_text_sha256']==sha(text[a:b].encode());pieces.append((a,b,comment['text']))
        cursor=0
        for a,b,part in sorted(pieces):assert a==cursor and a<b and text[a:b]==part;cursor=b
        assert cursor==len(text) and ''.join(part for a,b,part in sorted(pieces))==text
        if field['reviewed']:assert [c['source_span'] for c in version['comments']]==[[c['start'],c['end']] for c in field['reviewed_context_spans']]
        totals['lossless_partitions']+=1
    if action=='register':
        expected_languages={'hi','ur'}
        assert set(admitted)==expected_languages and result['text']=={'arabic':admitted.get('ar'),'translation':admitted['hi']}
    else:assert not admitted and all(f['reviewed'] for f in decision['fields'])
    totals[action+'_occurrences']+=1;books[saved['collection']][action+'_occurrences']+=1;totals['metadata_invariants']+=len(metadata);derived.append(result)
engine.finish()
assert totals['register_occurrences']==21 and totals['exclude_occurrences']==0
assert totals['nonempty_fields']==totals['lossless_partitions']==105 and totals['complete_fields_read']==42 and totals['admitted_fields']==42 and totals['unread_context_fields']==63
assert totals['characters_read']==12243 and totals['utf8_bytes_read']==26640
assert not empty_states
assert not [r for r in records if r['decision']=='exclude']
baseline_state=json.loads((ROOT.parent/'phase8-acquisition-monitor/saved-checkpoint/state.json').read_bytes())
assert not ({r['collection']+':'+r['number'] for r in rows}&set(baseline_state['imported']))
validation={'schema':'hadith-bank-manual-source-review-validation-v1','result':'PASS','source_commit':COMMIT,'review_batch':NAME,
    'counts':dict(totals),'language_coverage':{k:dict(v) for k,v in coverage.items()},'by_collection':{k:dict(v) for k,v in books.items()},
    'empty_source_fields_inspected':empty_states,'source_only_ids':[r['occurrence_id'] for r in records if r['decision']=='exclude'],
    'actual_reading_scope':'42 complete nonempty fields:21Hindi and21Urdu;12,243 characters and26,640 UTF8 bytes.63 nonempty sibling fields remain unread source context. The21 registered parent dispositions do not claim those siblings were linguistically reviewed.',
    'raw_parsed_pairs_reopened_and_reparsed':21,'source_fields_modified':0,'source_metadata_modified':0,'source_identity_merges':0,
    'canonical_identity_asserted':False,'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes':0,
    'all21_new_ids_absent_from_prior14737_imports':True,'native_SourceReviews_apply_finish':'PASS',
    'active_ledger_path':ACTIVE.as_posix(),'active_ledger_sha256':sha(active_data),'source_ledger_path':baseline_path.as_posix(),
    'source_ledger_sha256':sha(baseline_data),'source_ledger_uncompressed_sha256':sha(source_bytes),
    'code_inputs':{name:sha(Path(module.__file__).read_bytes()) for name,module in [('import_deenhindi',importer),('web_source_reviews',sys.modules['web_source_reviews']),('web_commentary_quotes',sys.modules['web_commentary_quotes'])]}}
put(Path('reports/web-source-resolution-20261113')/(NAME+'-validation.json'),enc(validation))
(ROOT/'validation-v1.json').write_bytes(enc(validation));(ROOT/'boundary-view-v1.json').write_bytes(enc(boundary_view))
(ROOT/'derived-preview-v1.jsonl.gz').write_bytes(gzip.compress(importer.rows_bytes(derived),mtime=0))
manifest={'schema':'hadith-bank-source-review-delivery-v1','source_commit':COMMIT,'result':'PASS','review_batch':NAME,
    'active_ledger_path':ACTIVE.as_posix(),'active_ledger_sha256':sha(active_data),'expected_delta':{'registered':21,'held':-21,'source_only':0,'admitted_hindi_fields':21,'admitted_urdu_fields':21,'admitted_arabic_fields':0,'admitted_english_fields':0,'admitted_roman_urdu_fields':0},
    'files':[{'path':path.relative_to(OUT).as_posix(),'local_path':str(path),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())} for path in sorted(OUT.rglob('*')) if path.is_file()]}
portable={'schema':'hadith-bank-source-review-portable-manifest-v1','source_commit':COMMIT,'review_batch':NAME,
    'active_ledger_path':ACTIVE.as_posix(),'active_ledger_sha256':sha(active_data),
    'files':[{k:v for k,v in entry.items()if k!='local_path'}for entry in manifest['files']]}
put(EVIDENCE/'portable-manifest.json',enc(portable))
portable_path=OUT/EVIDENCE/'portable-manifest.json'
manifest['files'].append({'path':portable_path.relative_to(OUT).as_posix(),'local_path':str(portable_path),
    'bytes':portable_path.stat().st_size,'sha256':sha(portable_path.read_bytes())})
(ROOT/'delivery-manifest-v1.json').write_bytes(enc(manifest))
print(json.dumps({'status':'PASS','counts':dict(totals),'by_collection':validation['by_collection'],'active_sha256':sha(active_data),'files':len(manifest['files']),'bytes':sum(f['bytes']for f in manifest['files'])},indent=2))
