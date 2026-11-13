"""Record the complete fifty-field independent candidate comparison without mutation."""
from pathlib import Path
import gzip, hashlib, json

HERE=Path(__file__).resolve().parent
PRIMARY=HERE.parent/'phase17-original-bukhari25-hi-ur'
sha=lambda b: hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
manifest_raw=(PRIMARY/'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_raw)=='2c6584f7ec87532a5345163af8ff5c60c736b41275a8e683eb1cfe853965f848'
manifest=json.loads(manifest_raw)
for f in manifest['files']:
    b=Path(f['local_path']).read_bytes()
    assert sha(b)==f['sha256'] and len(b)==f['bytes']
active=next(f for f in manifest['files'] if '/source-review-' in f['path'])
assert active['sha256']=='c069236c43adbb00cd1c62214372a71353959fc58ccd8f9ecb985e263436a7b2'
parents={r['occurrence_id']:r for r in json.loads(gzip.decompress(Path(active['local_path']).read_bytes()))['records']}
input_rows=[json.loads(x) for x in (HERE/'input/full-hi-ur-reading-input-50.jsonl').read_bytes().splitlines()]
read_receipt=(HERE/'complete-independent-source-first-readings.json').read_bytes()
assert sha(read_receipt)=='f44c6f4d353e5f2e8e0de2ddfd74e1f0ca0dd21406d9420b9c95ca78c978807c'
requests=[];checked=[]
for row in input_rows:
    f=next(f for f in parents[row['occurrence_id']]['fields'] if f['language']==row['language'])
    item={'occurrence_id':row['occurrence_id'],'language':row['language'],
          'source_text_sha256':row['text_sha256'],'v1_field_decision_sha256':sha(enc(f)),
          'complete_source_text_and_all_candidate_spans_and_voices_inspected':True,
          'v1_selected_positions':[[s['start'],s['end']] for s in f['selected_spans']],
          'v1_component_bindings':[{k:s[k] for k in ('component_id','source_report_family_id','report_type','speaker','start','end')} for s in f['selected_spans']]}
    if row['number']=='1467':
        a,b,literal=(224,241,'(अपने पहले खावंद)') if row['language']=='hi' else (217,236,'( اپنے پہلے خاوند )')
        assert row['text'][a:b]==literal
        positions={i for s in f['selected_spans'] for i in range(s['start'],s['end'])}
        assert not positions.intersection(range(a,b))
        requests.append({'occurrence_id':row['occurrence_id'],'language':row['language'],
            'source_field':row['source_field'],'source_text_sha256':row['text_sha256'],
            'v1_field_decision_sha256':sha(enc(f)), 'start':a,'end':b,'text':literal,
            'text_sha256':sha(literal.encode()),'characters':b-a,'utf8_bytes':len(literal.encode()),
            'requested_disposition':'selected_existing_component',
            'component_id':f['selected_spans'][0]['component_id'],
            'source_report_family_id':f['selected_spans'][0]['source_report_family_id'],
            'reason':'Inside Umm Salamah’s actual first-person question, these words supply her former marital relationship and temporal status. The named Abu Salamah and the subsequent shared-child statement do not independently supply that relationship. Retain this material participant scope without relabelling the speaker, changing the family, or adding words.'})
        item['independent_verdict']='restore_only_requested_former_spouse_scope'
    else:
        item['independent_verdict']='supported_without_requested_change'
    checked.append(item)
result={'schema':'hadith-bank-independent-original-field-boundary-findings-v1',
    'source_commit':'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d',
    'independent_source_first_receipt_sha256':sha(read_receipt),
    'independent_source_verification_sha256':sha((HERE/'independent-source-verification.json').read_bytes()),
    'primary_v1_manifest_sha256':sha(manifest_raw),'primary_v1_active_sha256':active['sha256'],
    'complete_fields_independently_read_and_candidate_checked':50,
    'characters_read':40338,'utf8_bytes_read':86636,
    'all50_selected_masks_and_attribution_components_inspected':True,
    'parent_disposition_changes_requested':0,'occurrences_with_findings':1,'fields_with_findings':2,
    'restored_characters_requested':36,'restored_utf8_bytes_requested':sum(x['utf8_bytes'] for x in requests),
    'removed_positions_requested':0,'requested_changes':requests,'field_checks':checked,
    'explicit_refinements_to_preserved_initial_notes':[
        {'occurrence_id':'deenhindi-bukhari:1392','languages':['hi','ur'],
         'initial_view':'The initial notes considered the bequest bridge redundant and the explicit protected-community parenthesis legal explanatory context.',
         'refinement':'Retain the source-supplied first-person bequest bridge and the protected-community scope in this actual instruction. The latter supplies the otherwise unstated recipient/antecedent of the ensuing promises, defense and burden limits; cutting it would leave the pronouns liable to attach to the preceding groups. This accepts the source’s own supplied scope without importing a separate rule or certifying historical/legal completeness. The damaged Hindi witness link, succession list and missing group remain unfilled.'},
        {'occurrence_id':'deenhindi-bukhari:1406','languages':['hi','ur'],
         'initial_view':'The first notes considered the arrival parenthesis redundant with the preceding arrival.',
         'refinement':'Retain its finite first-person temporal bridge as actual narration of when the crowd formed. Continue to exclude the separate verse label, appended office biography and repeated place label. No additional arrival or actor is invented.'},
        {'occurrence_id':'deenhindi-bukhari:1415','languages':['hi','ur'],
         'initial_view':'The initial notes tentatively retained both parenthetic donor names as supplied participant identification.',
         'refinement':'Accept their visible-context treatment as isolated identity glosses after complete anonymous participant constructions. Both actual acts, amounts and criticisms remain selected; no predicate, relationship, negation or condition is removed. The source’s names remain preserved in context, and the damaged Hindi ultimate narrator is not supplied from Urdu. The labor-purpose and lesser-donation qualifications within the actual provided verse rendering remain selected.'},
        {'occurrence_id':'deenhindi-bukhari:1454','languages':['hi','ur'],
         'initial_view':'The first notes allowed contextualizing repeated numerical lower-bound parentheses if the complete range was otherwise preserved.',
         'refinement':'Retain all source numerical bounds in this written schedule. Their concrete amount/range function differs from a lexical synonym, and the source’s greater-than/from-one-hundred-twenty formulations must not be harmonized by removing one side. The below-five exception, grazing-duration condition, governor role and currency unit also remain. The Hindi missing category and orphan female-animal tail are left unfilled/contextualized exactly.'},
        {'occurrence_id':'deenhindi-bukhari:1478','languages':['hi','ur'],
         'initial_view':'The initial notes preferred retaining the later route’s named chain introduction as a transmission actor link.',
         'refinement':'Accept the complete later chain/same-report pointer as visible transmission context while retaining the actual finite gesture, address to Saad and abbreviated giving clause in a qualified same-family component. The candidate does not assert the chain’s named transmitter as the original first-person participant, and it fills no omitted continuation. The complete compiler morphology and transmitter-biography appendix remain context.'},
    ],
    'source_metadata_or_wording_changes_requested':False,
    'independent_pro_qc':'not_performed','source_http_requests':0,'github_writes':0}
out=HERE/'independent-boundary-findings-v1.json'
assert not out.exists();out.write_bytes(enc(result))
print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'bytes':out.stat().st_size,'requested_fields':2,'restored_characters':36,'restored_utf8_bytes':result['restored_utf8_bytes_requested']},indent=2))
