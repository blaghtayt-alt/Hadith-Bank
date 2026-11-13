"""Apply only the independent eight-field refinement, preserving every v1 payload."""
from pathlib import Path
import ast
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import re
import sys

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'publish-v2'
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT.parent/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
from manual_source_first_readings import NOTES
from verify_local_sources import verify as verify_local_sources

sha=lambda x:hashlib.sha256(x).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
COMMIT='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
NAME='20261113-checkpointbd4a-muslim23-manual-v1'
REV=Path('imports/web-deenhindi-20261112/reviews')
EVIDENCE=REV/'evidence'/NAME
ACTIVE=REV/('source-review-'+NAME+'.json.gz')
AMEND=EVIDENCE/'independent-boundary-refinement-v2'

assert not (ROOT/'delivery-manifest-v2.json').exists(),'A frozen final package must remain immutable.'
v1_manifest_bytes=(ROOT/'delivery-manifest-v1.json').read_bytes()
assert sha(v1_manifest_bytes)=='3e2d9766c7ca23a12dc7d3e4aaf68e0e0886074024af63b2613adeb2503ed2e4'
v1_manifest=json.loads(v1_manifest_bytes)
old_active=(ROOT/'publish-v1'/ACTIVE).read_bytes()
assert sha(old_active)=='3f766fcad01ff7f9443869386bf0027d03136e8ce341e8292883a70194acd4ee'
old_doc=json.loads(gzip.decompress(old_active))
findings_path=ROOT.parent/'phase18-checkpointbd4a-muslim23-independent-audit/independent-boundary-findings-v1.json'
findings_bytes=findings_path.read_bytes()
assert sha(findings_bytes)=='af74b0e0e921e76eefbe4f4b0d3afcc06c47a9f55b2804636c0bb33f8e0c6082'
findings=json.loads(findings_bytes)
assert findings['primary_active_sha256']==sha(old_active) and findings['primary_manifest_sha256']==sha(v1_manifest_bytes)
changes=copy.deepcopy(findings['findings'])
separator=copy.deepcopy(findings['isolated_separator_space'])
assert separator['start']==71 and separator['end']==72 and separator['text']==' ' and separator['action']=='context'
changes.append(separator)
grouped=collections.defaultdict(list)
for x in changes:grouped[x['id'],x['language']].append(x)
assert len(grouped)==8 and len({k[0] for k in grouped})==5

def put(relative,data):
    path=OUT/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);return path

archived=[]
for f in v1_manifest['files']:
    data=Path(f['local_path']).read_bytes()
    assert len(data)==f['bytes'] and sha(data)==f['sha256']
    put(Path(f['path']),data)
    dest=put(AMEND/'previous-v1'/f['path'],data)
    archived.append({'original_path':f['path'],'archived_path':dest.relative_to(OUT).as_posix(),'bytes':len(data),'sha256':sha(data)})
assert len(archived)==13
put(AMEND/'previous-v1/delivery-manifest-v1.json',v1_manifest_bytes)
for name in ('boundary-view-v1.json','derived-preview-v1.jsonl.gz','validation-v1.json'):
    data=(ROOT/name).read_bytes()
    put(AMEND/'previous-v1-derived'/name,data)
put(AMEND/'independent-boundary-findings-v1.json',findings_bytes)

refinements={
 'deenhindi-muslim:2403':'Final v2: introductory general reliability/love appraisals are transmission context, distinct from the actual pledge dialogue and later incident observation. Preserve the source route and all damaged or missing identities. Exactly one now-isolated Urdu separator space is explicitly retained in context; no other whitespace is cut.',
 'deenhindi-muslim:2419':'Final v2: retain the source’s explicit Abu Musa actor identification after the arriving reader group, and the warning-domain qualifier of severity. They supply actor and comparison scope. The interval synonym and surah-category label remain context; all actual recalled fragments stay qualified as this source’s recollection.',
 'deenhindi-muslim:2443':'Final v2: retain the source’s in-verse speech-mode qualification in the narrative frame of Abbas’s actual complaint. The separate actual poem remains his voice; no additional verses or Prophetic attribution are introduced.',
 'deenhindi-muslim:2447':'Final v2: retain the source’s printed anger cause of the face change as a source-conditioned event qualification. The unintroduced Urdu accusation and missing speaker link remain explicitly unresolved.',
 'deenhindi-muslim:2449':'Final v2: retain the source’s beyond/forward qualification in the arrow simile. It is supplied directional extent, not an omitted-continuation pointer or an outside lexical definition.'}
original_rules=(ROOT/'manual_boundaries.py').read_bytes()
assert original_rules==(ROOT/'publish-v1'/EVIDENCE/'manual_boundaries.py').read_bytes()
append='\n\n# Explicit accepted independent amendments; original source-first NOTES above stay unchanged.\n'
append+='V2_ACCEPTED_CHANGES = '+repr(dict(grouped))+'\n'
append+='V2_REFINEMENTS = '+repr(refinements)+'\n'
append+='''for (_oid,_language),_items in V2_ACCEPTED_CHANGES.items():
    _note=READINGS[_oid.removeprefix('deenhindi-')][_language]
    for _item in _items:
        if _item['action']=='restore':
            assert _note['context'].count(_item['text'])==1
            _note['context'].remove(_item['text'])
            _note['retained_meaningful_structures'].append(_item['text'])
        else:
            assert _item['action']=='context'
            _note['context'].append({'start':_item['start'],'end':_item['end'],'text':_item['text']})
    _note['note']+=' '+V2_REFINEMENTS[_oid]
    _note['boundary_refinement']={'version':'v2','initial_source_first_note_preserved':True,
        'independent_findings_sha256':'af74b0e0e921e76eefbe4f4b0d3afcc06c47a9f55b2804636c0bb33f8e0c6082',
        'final_source_bound_judgment':V2_REFINEMENTS[_oid]}
'''
new_rules=original_rules+append.encode()
v2_rules_path=ROOT/'manual_boundaries_v2.py';v2_rules_path.write_bytes(new_rules)
spec=importlib.util.spec_from_file_location('phase18_explicit_boundaries_v2',v2_rules_path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
READINGS=module.READINGS
put(EVIDENCE/'manual_boundaries.py',new_rules)

# Reuse the frozen, hash-bound span construction functions only; never execute its v1 writer.
packager=(ROOT/'package_and_validate.py').read_text()
assert packager.encode()==(ROOT/'publish-v1'/EVIDENCE/'package_and_validate.py').read_bytes()
parsed_ast=ast.parse(packager)
functions=[x for x in parsed_ast.body if isinstance(x,ast.FunctionDef) and x.name in ('anchor','complement','span_for','field_review')]
assert {x.name for x in functions}=={'anchor','complement','span_for','field_review'}
exec(compile(ast.Module(body=functions,type_ignores=[]),str(ROOT/'package_and_validate.py'),'exec'),globals())
source_bytes=(ROOT/'input/cohort.jsonl').read_bytes()
assert sha(source_bytes)=='cf22bcd083b4cdb70cce62ca81bb73a60571ec62da390d980e8c584bcd65f29e'
rows=[json.loads(x) for x in source_bytes.splitlines()]
saved_by_id={'deenhindi-'+x['collection']+':'+x['number']:x for x in rows}
document=copy.deepcopy(old_doc)
records=document['records'];differences=[]
old_records={x['occurrence_id']:x for x in old_doc['records']}
positions=lambda f:{i for s in f['selected_spans'] for i in range(s['start'],s['end'])}
voice=lambda f:{i:(s['component_id'],s['report_type'],s['speaker'],s['source_report_family_id']) for s in f['selected_spans'] for i in range(s['start'],s['end'])}
for record in records:
    oid=record['occurrence_id'];saved=saved_by_id[oid];base=importer.canonical_record(saved)
    for index,old_field in enumerate(list(record['fields'])):
        key=(oid,old_field['language'])
        if key not in grouped:continue
        text=base['language_versions'][index]['text'];items=grouped[key]
        new_field=field_review(base['language_versions'][index],index,READINGS[oid.removeprefix('deenhindi-')][key[1]])
        add=set();cut=set()
        for item in items:
            a,b=item['start'],item['end'];assert text[a:b]==item['text']
            if item.get('source_field_sha256'):assert sha(text.encode())==item['source_field_sha256']
            if item.get('sha256'):assert sha(text[a:b].encode())==item['sha256']
            (add if item['action']=='restore' else cut).update(range(a,b))
        old_mask,new_mask=positions(old_field),positions(new_field)
        assert new_mask-old_mask==add and old_mask-new_mask==cut
        prior_voice,next_voice=voice(old_field),voice(new_field)
        assert all(prior_voice[i]==next_voice[i] for i in old_mask&new_mask)
        for item in items:
            if item['action']=='restore':
                expected=(item['component_id'],item['report_type'],item['speaker'],item['source_report_family_id'])
                assert all(next_voice[i]==expected for i in range(item['start'],item['end']))
        for k in ('version_id','language','source_field','field_path','text_sha256','text_chars','reviewed','chars_reviewed','bytes_reviewed'):
            assert old_field[k]==new_field[k]
        record['fields'][index]=new_field
        differences.append({'occurrence_id':oid,'language':key[1],'before_field_sha256':sha(enc(old_field)),
            'after_field_sha256':sha(enc(new_field)),'added_characters':len(add),'removed_characters':len(cut),
            'added_utf8_bytes':sum(len(text[i].encode()) for i in add),'removed_utf8_bytes':sum(len(text[i].encode()) for i in cut),
            'retained_position_component_type_speaker_family_exact':True,'explicit_changes':items})
unchanged_fields=unchanged_parents=0
for record in records:
    old=old_records[record['occurrence_id']]
    assert {k:v for k,v in record.items() if k!='fields'}=={k:v for k,v in old.items() if k!='fields'}
    unchanged_parents+=record==old
    for before,after in zip(old['fields'],record['fields']):
        if before==after:unchanged_fields+=1
        else:assert (record['occurrence_id'],after['language']) in grouped
assert len(differences)==8 and unchanged_fields==107 and unchanged_parents==18
assert sum(x['added_characters'] for x in differences)==119 and sum(x['added_utf8_bytes'] for x in differences)==232
assert sum(x['removed_characters'] for x in differences)==151 and sum(x['removed_utf8_bytes'] for x in differences)==313
active_data=gzip.compress(enc(document),mtime=0);put(ACTIVE,active_data)
reading_receipt=(ROOT/'complete-source-first-readings.json').read_bytes()
assert sha(reading_receipt)=='e5d013d075f0411f026a8dd2fd173e331c589f7c9b1111a9060b2127560ff826'
put(EVIDENCE/'manual-field-boundary-notes.json.gz',gzip.compress(enc({'schema':'hadith-bank-manual-field-boundaries-v2',
    'source_commit':COMMIT,'source_first_receipt_sha256':sha(reading_receipt),'records':READINGS,
    'explicit_v2_refinements':refinements,'original_source_first_notes_rewritten':False,
    'no_heuristic_batch_approvals':True,'independent_pro_qc':'not_performed'}),mtime=0))
boundary_view=[]
for decision in records:
    saved=saved_by_id[decision['occurrence_id']]
    boundary_view.append({'occurrence_id':decision['occurrence_id'],'decision':decision['decision'],
        'source_record_sha256':decision['source_record_sha256'],
        'fields':[{'language':f['language'],'text_sha256':f['text_sha256'],
            'source_text':saved['source_record'][f['source_field']],'reason':f['reason'],
            'selected':[dict(s,text=saved['source_record'][f['source_field']][s['start']:s['end']]) for s in f['selected_spans']],
            'context':[dict(s,text=saved['source_record'][f['source_field']][s['start']:s['end']]) for s in f['reviewed_context_spans']]}
            for f in decision['fields'] if f['reviewed']]})
local_source_validation=verify_local_sources()
assert local_source_validation['result']=='PASS'
baseline_path=EVIDENCE/'source-ledger-23.jsonl.gz'
baseline_data=(OUT/baseline_path).read_bytes()
assert gzip.decompress(baseline_data)==source_bytes
# Execute only the unchanged native validation block, using current v2 objects and separate v2 derivative names.
native=packager[packager.index('engine = SourceReviews'):packager.index('\nmanifest =')]
native=native.replace('validation-v1.json','validation-v2.json').replace('boundary-view-v1.json','boundary-view-v2.json').replace('derived-preview-v1.jsonl.gz','derived-preview-v2.jsonl.gz')
exec(compile(native,str(ROOT/'package_and_validate.py')+' [native v2 replay]','exec'),globals())
assert totals['admitted_characters']==30738 and totals['admitted_utf8_bytes']==64326
assert totals['typed_components']==68
receipt={'schema':'hadith-bank-exact-independent-boundary-refinement-v2','result':'PASS','source_commit':COMMIT,
    'previous_manifest_sha256':sha(v1_manifest_bytes),'previous_active_sha256':sha(old_active),
    'final_active_sha256':sha(active_data),'independent_findings_sha256':sha(findings_bytes),
    'primary_assessment':'All eight affected full source fields were reopened and the complete independent finding set was accepted for the explicit source-bound reasons recorded here.',
    'original_source_first_receipt_sha256':sha(reading_receipt),'original_source_first_notes_unchanged':True,
    'general_informant_appraisal_context_characters':150,'general_informant_appraisal_context_utf8_bytes':312,
    'separately_accounted_isolated_separator_context':separator,
    'restored_characters':119,'restored_utf8_bytes':232,'no_unrequested_position_changes':True,
    'unchanged_other_field_definitions':107,'unchanged_other_reviewed_fields':41,'unchanged_unread_fields':66,
    'unchanged_whole_parents':18,'all_parent_metadata_and_dispositions_exact':True,
    'all_existing_component_types_speakers_families_preserved':True,'changes':differences,'refinements':refinements,
    'complete_v1_payloads_archived':archived,'all_v1_payloads_rehashed_unchanged':True,
    'native_SourceReviews_apply_finish':'PASS','native_counts':dict(totals),'source_files_reopened':46,'raw_reparses':23,
    'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed'}
put(AMEND/'exact-amendment-and-validation.json',enc(receipt))
put(AMEND/'amend_v2.py',Path(__file__).read_bytes())
for f in v1_manifest['files']:
    data=Path(f['local_path']).read_bytes();assert len(data)==f['bytes'] and sha(data)==f['sha256']
assert (ROOT/'delivery-manifest-v1.json').read_bytes()==v1_manifest_bytes
portable_path=EVIDENCE/'portable-manifest.json'
files=[{'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
       for p in sorted(OUT.rglob('*')) if p.is_file() and p.relative_to(OUT)!=portable_path]
manifest={'schema':'hadith-bank-source-review-delivery-v2','source_commit':COMMIT,'result':'PASS','review_batch':NAME,
    'active_ledger_path':ACTIVE.as_posix(),'active_ledger_sha256':sha(active_data),'previous_manifest_sha256':sha(v1_manifest_bytes),
    'amendment_receipt_path':(AMEND/'exact-amendment-and-validation.json').as_posix(),'amendment_receipt_sha256':sha(enc(receipt)),
    'expected_delta':v1_manifest['expected_delta'],'files':files}
portable={k:copy.deepcopy(v) for k,v in manifest.items() if k!='files'}
portable['schema']='hadith-bank-source-review-portable-manifest-v2'
portable['files']=[{k:v for k,v in f.items() if k!='local_path'} for f in files]
dest=put(portable_path,enc(portable))
manifest['files'].append({'path':portable_path.as_posix(),'local_path':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest.read_bytes())})
data=enc(manifest);(ROOT/'delivery-manifest-v2.json').write_bytes(data)
print(json.dumps({'result':'PASS','manifest_sha256':sha(data),'active_sha256':sha(active_data),'files':len(manifest['files']),
    'bytes':sum(x['bytes'] for x in manifest['files']),'amendment_sha256':sha(enc(receipt)),'counts':dict(totals)},indent=2))
