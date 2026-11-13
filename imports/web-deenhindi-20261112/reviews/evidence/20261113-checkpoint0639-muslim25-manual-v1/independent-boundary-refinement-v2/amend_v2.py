"""Apply eight source-bound field refinements, retaining the entire frozen v1."""
import collections
import copy
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

sha = lambda data: hashlib.sha256(data).hexdigest()
enc = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
OUT = ROOT/'publish-v2'
assert not (ROOT/'delivery-manifest-v2.json').exists(), 'Frozen v2 must not be overwritten.'
manifest_path = ROOT/'delivery-manifest-v1.json'
manifest_bytes = manifest_path.read_bytes()
assert sha(manifest_bytes) == 'b7d1e30f93974ed746e1d660cb3f8799ac3d48f38e29ec431b50957f7c9a3503'
old_manifest = json.loads(manifest_bytes)
ACTIVE = Path(old_manifest['active_ledger_path'])
EVIDENCE = Path('imports/web-deenhindi-20261112/reviews/evidence/20261113-checkpoint0639-muslim25-manual-v1')
AMEND = EVIDENCE/'independent-boundary-refinement-v2'


def put(path, data):
    destination = OUT/path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


for item in old_manifest['files']:
    data = Path(item['local_path']).read_bytes()
    assert len(data) == item['bytes'] and sha(data) == item['sha256']
    put(Path(item['path']), data)
    put(AMEND/'previous-v1'/item['path'], data)
put(AMEND/'previous-v1/delivery-manifest-v1.json', manifest_bytes)
old_active = (ROOT/'publish-v1'/ACTIVE).read_bytes()
assert sha(old_active) == 'deffc347dd549d63caa58100a64701e9a4c2304f473d090a7761e2af68660854'
before = json.loads(gzip.decompress(old_active))
after = copy.deepcopy(before)
source_bytes = (ROOT/'input/cohort.jsonl').read_bytes()
assert sha(source_bytes) == '5f3f7103a180f543f50df6fc5c6fc7ccc36bcb0d3c6d2911d3d9fe811a163d3c'
rows = [json.loads(line) for line in source_bytes.splitlines()]
source_by_number = {r['number']:r for r in rows}
by_number = {r['number']:r for r in after['records']}
changes = []


def positions(field):
    return {i for s in field['selected_spans'] for i in range(s['start'],s['end'])}


def complement(text, spans):
    out=[]; cursor=0
    for s in spans:
        a,b=s['start'],s['end']
        assert 0<=cursor<=a<b<=len(text)
        if cursor<a:out.append((cursor,a))
        cursor=b
    if cursor<len(text):out.append((cursor,len(text)))
    return out


for number in ('2240','2291','2301','2307'):
    row = by_number[number]
    for language in ('hi','ur'):
        field = next(f for f in row['fields'] if f['language']==language)
        prior = copy.deepcopy(field)
        text = source_by_number[number]['source_record'][field['source_field']]
        mask_before = positions(field)
        family = 'muslim:'+number+':source-numbered-report'
        if number == '2240':
            restored = [(149,168),(290,306)] if language=='hi' else [(137,156),(267,280)]
            expected = ['(अपने लवाहीक़ीन से)','(क़ब्र-ए-मुबारक)'] if language=='hi' else ['( اپنے لواحقین سے )',') قبر مبارک )']
            assert [text[a:b] for a,b in restored]==expected
            reason = ('Final independent refinement: retain the sole source-supplied family addressees and grave object. They provide actual actor/object scope for Sad’s deathbed instruction and burial comparison, rather than duplicate a term already present. The malformed Urdu delimiters remain exact. Sad remains the speaker, not the Prophet.')
            span = copy.deepcopy(field['selected_spans'][0])
            span.update(start=0,end=len(text),sha256=sha(text.encode()),reason=reason)
            field['selected_spans']=[span]
            field['explicit_context_cuts']=[]
            field['retained_meaningful_structures']=[{'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode()),'reason':reason} for a,b in restored]
            added = set().union(*(set(range(a,b)) for a,b in restored)); removed=set()
        elif number == '2291':
            a,b=(132,174) if language=='hi' else (122,166)
            expected = "'जो ऊंटों का मालिक इन का हक अदा नहीं करता'" if language=='hi' else '" جو اونٹوں کا مالک ان کا حق ادا نہیں کرتا "'
            assert text[a:b]==expected
            reason = ('Final independent refinement: retain all three actually supplied finite fragments, including the expressly quoted owner-not-paying-rights relative/conditional clause. Its negative predicate is present although its consequence and ultimate speaker are absent. Preserve that incompleteness explicitly; do not reconstruct the referenced full report. The calf and branding fragments and the source’s own rendering remain unchanged.')
            new_span={'start':a,'end':b,'sha256':sha(text[a:b].encode()),'component_id':'unpaid-camel-owner-fragment',
                      'report_type':'qualified_transmitted_conditional_fragment',
                      'speaker':'The source expressly quotes an owner-not-paying-rights clause, but gives neither its consequence nor its ultimate speaker locally. Preserve only that supplied conditional/relative fragment with unnamed attribution.',
                      'source_report_family_id':family,'reason':reason}
            field['selected_spans']=[new_span]+field['selected_spans']
            added=set(range(a,b));removed=set();restored=[(a,b)]
        elif number == '2301':
            a,b=(378,488) if language=='hi' else (333,444)
            assert b==len(text)
            reason = ('Final independent refinement: retain the actual arrival scene, explicit Prophetic oath and the supplied death/left-unpaid-cattle condition. The last condition has finite source predicates but no consequence; that missing outcome stays explicitly absent. The initial conservative context classification is superseded only for the actual supplied conditional wording, without importing2300 or completing punctuation.')
            field['selected_spans'].append({'start':a,'end':b,'sha256':sha(text[a:b].encode()),
                'component_id':'unpaid-cattle-condition','report_type':'prophetic_conditional_fragment',
                'speaker':'The same own-field speech frame explicitly attributes this death/left-unpaid-cattle condition to the Messenger. Its consequence is not supplied and is not inferred; source quotation punctuation remains exact.',
                'source_report_family_id':family,'reason':reason})
            added=set(range(a,b));removed=set();restored=[(a,b)]
        else:
            a,b=(780,785) if language=='hi' else (829,836)
            assert text[a:b]==('(मदद)' if language=='hi' else '( مدد )')
            reason = ('Final independent refinement: the parenthetic help label is a lexical explanation and remains source context. Urdu’s maunat already expresses assistance; Hindi’s defective mount word is preserved without using the gloss to repair it. The meaningful fire and government-source qualifications remain selected. The warning’s actual reported Prophetic link and Abu Dharr’s separate own financial answer stay distinct.')
            new=[]
            for span in field['selected_spans']:
                x,y=span['start'],span['end']
                if b<=x or y<=a:new.append(span)
                else:
                    assert x<=a<b<=y
                    for left,right in ((x,a),(b,y)):
                        if left<right:
                            item=copy.deepcopy(span);item.update(start=left,end=right,sha256=sha(text[left:right].encode()));new.append(item)
            field['selected_spans']=new
            field['explicit_context_cuts'].append({'start':a,'end':b,'sha256':sha(text[a:b].encode()),'text':text[a:b]})
            field['explicit_context_cuts'].sort(key=lambda x:x['start'])
            field['retained_meaningful_structures']=[r for r in field['retained_meaningful_structures'] if (r['start'],r['end'])!=(a,b)]
            added=set();removed=set(range(a,b));restored=[]
        field['reason']=reason
        field['prior_complete_reading_note']=prior['reason']
        field['independent_refinement']='Source-first primary assessment reconsidered after the independent reader supplied the exact own-field scope distinction. Full previous decision and initial reading notes are retained in immutable v1 evidence.'
        for span in field['selected_spans']:span['reason']=reason
        gaps=complement(text,field['selected_spans'])
        field['reviewed_context_spans']=[{'start':a,'end':b,'sha256':sha(text[a:b].encode()),'reason':reason} for a,b in gaps]
        field['decision']='whole' if len(field['selected_spans'])==1 and field['selected_spans'][0]['start']==0 and field['selected_spans'][0]['end']==len(text) else 'excerpts'
        mask_after=positions(field)
        assert mask_after-mask_before==added and mask_before-mask_after==removed
        changes.append({'occurrence_id':row['occurrence_id'],'language':language,
                        'source_text_sha256':sha(text.encode()),'before_field_sha256':sha(enc(prior)),
                        'after_field_sha256':sha(enc(field)),
                        'added_positions':len(added),'removed_positions':len(removed),
                        'added_exact_spans':[{'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode())} for a,b in restored],
                        'removed_exact_spans':[] if not removed else [{'start':min(removed),'end':max(removed)+1,'text':text[min(removed):max(removed)+1],'sha256':sha(text[min(removed):max(removed)+1].encode())}],
                        'reason':reason,'initial_primary_reason':prior['reason']})

assert len(changes)==8
unchanged_parents=unchanged_fields=0
for old,new in zip(before['records'],after['records']):
    assert {k:v for k,v in old.items() if k!='fields'}=={k:v for k,v in new.items() if k!='fields'}
    if old==new:unchanged_parents+=1
    for old_f,new_f in zip(old['fields'],new['fields']):
        if old_f==new_f:unchanged_fields+=1
        else:
            for key in ('version_id','language','source_field','field_path','text_sha256','text_chars','reviewed','chars_reviewed','bytes_reviewed','review_method','review_scope','report_type','speaker'):
                assert old_f.get(key)==new_f.get(key)
assert unchanged_parents==21 and unchanged_fields==117
after['independent_boundary_refinement']={'version':2,'before_active_sha256':sha(old_active),
    'scope':'Eight exact field refinements across four parents after full independent reading; no source, parent disposition, other117 field decisions or reading coverage changes.',
    'evidence_path':(AMEND/'exact-amendment-and-validation.json').as_posix()}
after['scope']=before['scope']+' Final v2 retains explicitly supplied finite conditional fragments with absent consequences qualified, restores sole actor/object scope, and separates the2307 lexical help labels as context.'
active=gzip.compress(enc(after),mtime=0);put(ACTIVE,active)

engine=SourceReviews(OUT,'deenhindi')
totals=collections.Counter();language_counts=collections.defaultdict(collections.Counter);derived=[]
for saved,decision in zip(rows,after['records']):
    base=importer.canonical_record(saved);original=copy.deepcopy(base)
    result,action=engine.apply(base,saved=saved)
    assert base==original and action==decision['decision']
    for key in ('id','language','book_key','edition','title','source','number','narrator','translator','ai_translation','translation_provenance','commentary','footnotes','references','grading','page','source_headings','rights','source_locator'):
        assert result.get(key)==original.get(key)
    selected={}
    for old,version,field in zip(original['language_versions'],result['language_versions'],decision['fields']):
        text=old['text'];lang=old['language'];pieces=[]
        for key,value in old.items():
            if key not in ('text','scope','quotation_status','comments','source'):assert version.get(key)==value
        for key,value in old['source'].items():assert version['source'].get(key)==value
        for s in field['selected_spans']:
            a,b=s['start'],s['end'];assert sha(text[a:b].encode())==s['sha256'];pieces.append((a,b,text[a:b]))
        if field['selected_spans']:
            assert version['text']==''.join(p[2] for p in pieces);selected[lang]=version['text']
            for counter in (totals,language_counts[lang]):
                counter['admitted_fields']+=1;counter['selected_spans']+=len(field['selected_spans'])
                counter['admitted_characters']+=len(version['text']);counter['admitted_utf8_bytes']+=len(version['text'].encode())
            totals['typed_components']+=len(version['source']['report_component_classifications'])
            assert {x['source_report_family_id'] for x in version['source']['report_component_classifications']}=={'muslim:'+saved['number']+':source-numbered-report'}
        else:assert version['text'] is None
        for c in version['comments']:
            a,b=c['source_span'];assert c['text']==text[a:b] and c['source_text_sha256']==sha(text[a:b].encode())
            pieces.append((a,b,c['text']))
        cursor=0
        for a,b,part in sorted(pieces):assert a==cursor and text[a:b]==part;cursor=b
        assert cursor==len(text) and ''.join(x[2] for x in sorted(pieces))==text
        totals['lossless_partitions']+=1
        if field['reviewed']:
            assert field['chars_reviewed']==len(text) and field['bytes_reviewed']==len(text.encode())
            for counter in (totals,language_counts[lang]):
                counter['complete_fields_read']+=1;counter['characters_read']+=len(text);counter['utf8_bytes_read']+=len(text.encode())
                counter['reviewed_context_gaps']+=len(version['comments'])
                if not field['selected_spans']:counter['fully_read_context_only_fields']+=1
        else:totals['unread_context_fields']+=1;assert not field['selected_spans']
    expected={'ar'} if saved['number']=='2293' else set() if saved['number'] in ('2264','2299') else {'hi','ur'}
    assert set(selected)==expected
    if action=='register':assert result['text']=={'arabic':selected.get('ar'),'translation':selected.get('hi')}
    totals[action+'_occurrences']+=1;derived.append(result)
engine.finish()
assert totals['register_occurrences']==23 and totals['exclude_occurrences']==2
assert totals['lossless_partitions']==125 and totals['complete_fields_read']==59 and totals['admitted_fields']==45
assert totals['fully_read_context_only_fields']==14 and totals['unread_context_fields']==66
assert totals['characters_read']==29190 and totals['utf8_bytes_read']==60905
assert totals['selected_spans']==122 and totals['admitted_characters']==24739
for item in old_manifest['files']:
    assert sha(Path(item['local_path']).read_bytes())==item['sha256']
    assert sha((OUT/AMEND/'previous-v1'/item['path']).read_bytes())==item['sha256']
validation={'schema':'hadith-bank-independent-boundary-amendment-v2','result':'PASS',
    'source_commit':old_manifest['source_commit'],'source_review_batch':old_manifest['review_batch'],
    'before_active_sha256':sha(old_active),'after_active_sha256':sha(active),
    'before_manifest_sha256':sha(manifest_bytes),'exact_changes':changes,
    'unchanged_parent_decision_metadata':25,'unchanged_whole_parents':21,'unchanged_field_definitions':117,
    'preserved_v1_payloads':13,'preserved_v1_manifest':True,'source_fields_modified':0,'source_metadata_modified':0,
    'new_readings':0,'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed',
    'native_SourceReviews_apply_finish':'PASS','counts':dict(totals),'language_coverage':{k:dict(v) for k,v in language_counts.items()},
    'reasoning_refinement':'The first primary pass conservatively treated missing consequences as excluding complete relative/conditional predicates. The independent own-field reading establishes that the actual expressly supplied predicates can remain as qualified fragments while their consequences and any missing ultimate speakers remain absent. Sole actor/object scope is retained, whereas lexical help labels stay visible context. No initial source-first receipt is rewritten.'}
put(AMEND/'exact-amendment-and-validation.json',enc(validation))
put(AMEND/'amend_v2.py',Path(__file__).read_bytes())
put(Path('reports/web-source-resolution-20261113/20261113-checkpoint0639-muslim25-manual-v2-validation.json'),enc(validation))
(ROOT/'validation-v2.json').write_bytes(enc(validation))
(ROOT/'derived-preview-v2.jsonl.gz').write_bytes(gzip.compress(importer.rows_bytes(derived),mtime=0))
manifest={k:v for k,v in old_manifest.items() if k!='files'}
manifest.update(active_ledger_sha256=sha(active),version=2,previous_manifest_sha256=sha(manifest_bytes),
                files=[{'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()])
portable={k:copy.deepcopy(v) for k,v in manifest.items() if k!='files'}
portable['schema']='hadith-bank-source-review-portable-manifest-v2'
portable['files']=[{k:v for k,v in f.items() if k!='local_path'} for f in manifest['files']]
portable_path=put(AMEND/'portable-manifest-v2.json',enc(portable))
manifest['files'].append({'path':portable_path.relative_to(OUT).as_posix(),'local_path':str(portable_path),'bytes':portable_path.stat().st_size,'sha256':sha(portable_path.read_bytes())})
(ROOT/'delivery-manifest-v2.json').write_bytes(enc(manifest))
print(json.dumps({'result':'PASS','active_sha256':sha(active),'manifest_sha256':sha(enc(manifest)),
                  'counts':dict(totals),'files':len(manifest['files']),'bytes':sum(x['bytes'] for x in manifest['files'])},indent=2))
