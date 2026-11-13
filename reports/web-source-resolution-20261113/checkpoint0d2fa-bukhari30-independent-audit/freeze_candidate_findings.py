"""Freeze the completed independent candidate comparison without changing it."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase21-checkpoint0d2fa-bukhari30-review'
sha=lambda value:hashlib.sha256(value).hexdigest()
enc=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
manifest_bytes=(PRIMARY/'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_bytes)=='70a0fce9c10f36d47163672f3d636ca82668a65d04055c6c853c807a9ba16fc6'
manifest=json.loads(manifest_bytes)
for item in manifest['files']:
    data=Path(item['local_path']).read_bytes()
    assert len(data)==item['bytes'] and sha(data)==item['sha256']
entry=next(item for item in manifest['files'] if '/source-review-' in item['path'] and '/evidence/' not in item['path'])
active_bytes=Path(entry['local_path']).read_bytes()
assert sha(active_bytes)=='1e08c967257c0a21bc5525130801bac71af357ba97400af21345ad30e1e94f08'
active=json.loads(gzip.decompress(active_bytes))
records={record['id']:record for record in active['records']}
read_bytes=(ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(read_bytes)=='409323a027fd5c7bc3c745d82e1b394ceaf976b788d11c0a6c1d833161eb08e7'
reading=json.loads(read_bytes)
inputs=[json.loads(line) for line in (ROOT/'input/full-hi-ur-reading-input-60.jsonl').read_bytes().splitlines()]
inputs += [json.loads(line) for line in (ROOT/'input/additional-bukhari2603-originals.jsonl').read_bytes().splitlines()]
originals={(row['occurrence_id'],row['language']):row for row in inputs}
own={(row['occurrence_id'],row['language']):row for row in reading['fields']}
assert set(own)==set(originals) and len(own)==63

refinements=[
    {'ids':['2571'],'languages':['hi','ur'],
     'initial_hypothesis':'The right-side causal aside might be a repetition of the already supplied seat.',
     'final_assessment':'Retain it: the actual because-clause links the handover to the seating despite the preceding request for Abu Bakr. It supplies the reported reason for that decision, rather than a dictionary synonym. The lassi label remains context, and the remaining-milk/repetition predicates remain selected.'},
    {'ids':['2573','2574'],'languages':['hi','ur'],
     'initial_hypothesis':'The anonymous narrator-doubt label could remain context if both alternatives stayed.',
     'final_assessment':'Accept the expressly qualified uncertainty component. The source distinguishes an unsettled transmitted location or motive from an intentional two-option assertion; it remains an unnamed transmission qualification within the same family and is not attributed to the Prophet.'},
    {'ids':['2592'],'languages':['hi','ur'],
     'initial_hypothesis':'An honorific title must not be removed automatically.',
     'final_assessment':'The specific title here is appended within the prefatory route before the intact final Maimunah report frame. Its source-context placement preserves the entire actual event, named reporter and later finite abbreviated emancipation variant; it is not a general removal of honorifics.'},
    {'ids':['2599'],'languages':['hi','ur'],
     'initial_hypothesis':'The addressed-to-me and my-father phrases might duplicate the name and son address.',
     'final_assessment':'Accept these actual first-person addressee/kinship relations in the visit narrative. They bind the reported speech and later looking action to the narrator’s participant roles; they are not alternate-name glosses. Every original relation remains qualified by the supplied report.'},
    {'ids':['2613'],'languages':['hi','ur'],
     'initial_hypothesis':'The world-adornment parenthesis might be an interpretive lexical gloss.',
     'final_assessment':'Accept it as the supplied object-domain qualification of the withdrawal statement. It limits that statement to worldly adornment within this curtain account; the actual return and message-arrival predicates also remain. Hindi’s missing reporting link stays explicitly unfilled.'},
    {'ids':['2615','2616'],'languages':['hi','ur'],
     'initial_hypothesis':'The how-fine-silk clause might be an explanation of the reported wonder.',
     'final_assessment':'Accept the finite content of the companions’ reaction: it identifies what they admired, rather than silently turning their wonder into a response to the prohibition. Keep the men-only restriction and the separately introduced actual rhetorical address. Both source IDs were individually read and remain distinct.'},
    {'ids':['2627'],'languages':['hi','ur'],
     'initial_hypothesis':'The fast-running parenthesis required a specific metaphor-domain versus lexical-function assessment.',
     'final_assessment':'Accept context placement for the appended speed explanation of the sea metaphor. The complete finite original comparison remains selected. By contrast, enemy-attack scope and the companions’ accompanying action remain actual reported circumstances.'},
    {'ids':['2628'],'languages':['hi','ur'],
     'initial_hypothesis':'The to-me phrase might be redundant after the visitor framing.',
     'final_assessment':'Accept it as the actual addressee of Aisha’s ensuing speech, tied to the source-defined visitor without inventing his fuller identity. The textile definition remains context, and the two actual voices remain separately attributed in one family.'},
]

requests=[]
for language,start,end,literal in [
    ('hi',601,614,'(माल-ए-ज़कात)'),
    ('ur',549,562,'( مال زکوٰۃ )'),
]:
    oid='deenhindi-bukhari:2597'
    row=originals[oid,language];text=row['text']
    field=next(field for field in records[oid]['field_reviews'] if field['language']==language)
    assert text[start:end]==literal
    assert not any(max(start,s['start'])<min(end,s['end']) for s in field['spans'])
    before=next(s for s in field['spans'] if s['end']==start)
    after=next(s for s in field['spans'] if s['start']==end)
    keys=('component_id','report_type','speaker','source_report_family_id')
    assert all(before[key]==after[key] for key in keys)
    expected=[]
    for span in field['spans']:
        if span is before:
            expected.append([span['start'],after['end']])
        elif span is after:
            continue
        else:
            expected.append([span['start'],span['end']])
    requests.append({
        'occurrence_id':oid,'language':language,'source_field':row['source_field'],
        'source_text_sha256':sha(text.encode()),'range':[start,end],
        'text':literal,'text_sha256':sha(literal.encode()),'characters':len(literal),
        'utf8_bytes':len(literal.encode()),'action':'restore_to_existing_report_component',
        'before_complete_field_definition_sha256':sha(enc(field)),
        'expected_final_selected_ranges':expected,
        'unchanged_component_metadata':{key:before[key] for key in keys},
        'reason':'The own field expressly contrasts collected/public property and the collector’s claimed personal gift. This phrase fixes the property domain of the subsequent taking/oath statement. It is a meaningful object restriction, not a lexical synonym; the distinct explicit yani-treasury explanation remains context.',
        'description_refinement':'Refine only descriptions or inventories that currently call this zakah-property qualification context. Preserve original source-first notes and all v1 bytes, recording the reconsideration additively.'})

fields=[]
for key,source in originals.items():
    field=next(f for f in records[key[0]]['field_reviews'] if f['language']==key[1])
    assert field['reviewed'] is True and field['text_sha256']==sha(source['text'].encode())
    req=next((r for r in requests if (r['occurrence_id'],r['language'])==key),None)
    fields.append({
        'occurrence_id':key[0],'language':key[1],'source_text_sha256':sha(source['text'].encode()),
        'characters_actually_read':len(source['text']),'utf8_bytes_actually_read':len(source['text'].encode()),
        'complete_candidate_field_definition_sha256':sha(enc(field)),
        'all_selected_and_context_boundaries_and_voices_independently_compared':True,
        'disposition':'bounded_restore_requested' if req else 'accepted_unchanged',
        'selected_ranges_v1':[[s['start'],s['end']] for s in field['spans']],
        'expected_final_ranges':req['expected_final_selected_ranges'] if req else [[s['start'],s['end']] for s in field['spans']],
        'source_first_note':own[key]['independent_note'],
        'additive_refinements':[r for r in refinements if key[0].split(':')[1] in r['ids'] and key[1] in r['languages']],
    })
assert len(fields)==63 and sum(x['disposition']=='accepted_unchanged' for x in fields)==61
report={
    'schema':'hadith-bank-independent-complete-candidate-boundary-findings-v1',
    'source_commit':reading['source_commit'],
    'reviewer':'OpenAI assistant /root/queue_audit',
    'source_first_complete_reading_receipt_sha256':sha(read_bytes),
    'source_first_notes_sha256':reading['notes_sha256'],
    'independent_source_verification_sha256':'2e74f16316d288a96628db13ecd65b2f310237dc3caea62a6d734197af316330',
    'primary_manifest_v1_sha256':sha(manifest_bytes),'active_v1_sha256':sha(active_bytes),
    'all28_primary_payloads_hash_verified':True,
    'complete_fields_read_and_candidate_compared':63,'characters_read':37985,'utf8_bytes_read':81545,
    'requested_amendments':requests,
    'restored_characters':sum(x['characters'] for x in requests),
    'restored_utf8_bytes':sum(x['utf8_bytes'] for x in requests),'removed_characters':0,
    'accepted_unchanged_reviewed_fields':61,'unread_fields_to_preserve_exactly':87,
    'other_whole_parents_to_preserve_exactly':29,
    'all30_parent_registration_decisions_supported':True,
    'parent_source_metadata_changes_requested':0,'component_identity_changes_requested':0,
    'source_only_parent_ids':[],
    '2603_independent_field_result':{'admitted':['ar','en'],'reviewed_context':['hi','ur','ur-Latn'],'primary_hindi_must_remain_null':True,'missing_english_closing_quote_must_remain_missing':True},
    'explicit_source_based_refinements':refinements,
    'original_notes_and_receipts_unchanged':True,
    'candidate_mutations':0,'github_writes':0,'source_http_requests':0,
    'independent_pro_qc':'not_performed','fields':fields,
}
target=ROOT/'independent-boundary-findings-v1.json';data=enc(report)
if target.exists():assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({'path':str(target),'sha256':sha(data),'bytes':len(data),'restored_characters':report['restored_characters'],'restored_utf8_bytes':report['restored_utf8_bytes'],'fields':63,'affected_fields':2},indent=2))
