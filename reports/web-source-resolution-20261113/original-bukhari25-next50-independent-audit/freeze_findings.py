"""Freeze source-bound findings after the independent complete fifty-field pass."""
import copy,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRIMARY=HERE.parent/'phase20-original-bukhari25-hi-ur'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
selection=json.loads((PRIMARY/'input/selection.json').read_bytes())
manifest_raw=(PRIMARY/'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_raw)=='9f3b6612ee3dd871f47b2741f55570a07567554eb569807dfaa48b2663d35e51'
active=(PRIMARY/'publish-v1'/selection['active_review_path']).read_bytes()
assert sha(active)=='14ae19f71bac85c74fa4652ca40d46c3a5f94d3d0e2dbdff7da0bb18a212c8e2'
records={r['occurrence_id']:r for r in json.loads(gzip.decompress(active))['records']}
inputs=list(map(json.loads,(HERE/'input/full-hi-ur-reading-input-50.jsonl').read_bytes().splitlines()))
by_key={(r['occurrence_id'],r['language']):r for r in inputs}
readraw=(HERE/'complete-independent-source-first-readings.json').read_bytes()
assert sha(readraw)=='073b9eb372627f21dde24a7f2179449fdf92cd12e7c6bd7a55e544b1bd52f67a'
requests=[]
specs=[
 ('1493','hi','(जो बाँदी थीं)','The named Barira status parenthesis is an explanatory apposition. The surrounding actual purchase-for-emancipation purpose, original owners, wala condition, consultation and emancipation reply already supply the complete transaction; putting this duplicate status gloss in context removes no actor, action, condition or permission basis.'),
 ('1493','ur','( جو باندی تھیں )','The named Barira status parenthesis is an explanatory apposition. The surrounding actual purchase-for-emancipation purpose, original owners, wala condition, consultation and emancipation reply already supply the complete transaction; putting this duplicate status gloss in context removes no actor, action, condition or permission basis.'),
 ('1507','hi',"(आधा सा'अ)",'This parenthesis converts the already complete two-mudd measure into another unit. The actual later people’s wheat-equivalence determination and its exact two-mudd amount remain selected; the source conversion remains visible context rather than being attributed as additional words of Ibn Umar or the Prophet.'),
 ('1507','ur','( آدھا صاع )','This parenthesis converts the already complete two-mudd measure into another unit. The actual later people’s wheat-equivalence determination and its exact two-mudd amount remain selected; the source conversion remains visible context rather than being attributed as additional words of Ibn Umar or the Prophet.'),
 ('1513','hi','(हज्जतुल विदा में)','The parenthesis at the opening repeats the explicit final finite sentence identifying this as the Farewell Pilgrimage event. Move only this duplicated chronological apposition to context; the actual final dating sentence and every riding, looking, wanted-to-turn, incapacity, representative-Hajj question and yes-answer remain selected.'),
 ('1513','ur','( حجۃ الوداع میں )','The parenthesis at the opening repeats the explicit final finite sentence identifying this as the Farewell Pilgrimage event. Move only this duplicated chronological apposition to context; the actual final dating sentence and every riding, looking, wanted-to-turn, incapacity, representative-Hajj question and yes-answer remain selected.'),
]
for number,lang,literal,rationale in specs:
    oid='deenhindi-bukhari:'+number;r=by_key[(oid,lang)];text=r['text']
    assert text.count(literal)==1
    start=text.index(literal);end=start+len(literal)
    f=next(f for f in records[oid]['fields'] if f['language']==lang)
    oldpos={i for s in f['selected_spans'] for i in range(s['start'],s['end'])}
    assert set(range(start,end))<=oldpos
    expected=[]
    for s in f['selected_spans']:
        parts=[(s['start'],s['end'])]
        if s['start']<end and start<s['end']:
            parts=[(s['start'],max(s['start'],start)),(min(s['end'],end),s['end'])]
        for a,b in parts:
            if a>=b:continue
            n=copy.deepcopy(s);n.update(start=a,end=b,sha256=sha(text[a:b].encode()));expected.append(n)
    requests.append({'occurrence_id':oid,'language':lang,'source_field':r['source_field'],
        'source_text_sha256':r['text_sha256'],'source_record_sha256':r['source_record_sha256'],
        'prior_field_decision_sha256':sha(enc(f)),'action':'move_exact_selected_range_to_source_context',
        'start':start,'end':end,'text':literal,'text_sha256':sha(literal.encode()),
        'characters':len(literal),'utf8_bytes':len(literal.encode()),'reason':rationale,
        'expected_selected_spans_before_transparent_reason_refinement':expected,
        'existing_component_type_speaker_family_identity_must_remain':True})
oid='deenhindi-bukhari:1536';f=next(f for f in records[oid]['fields'] if f['language']=='hi');r=by_key[(oid,'hi')]
metadata={'occurrence_id':oid,'language':'hi','source_text_sha256':r['text_sha256'],
    'source_record_sha256':r['source_record_sha256'],'prior_field_decision_sha256':sha(enc(f)),
    'action':'qualify_only_the_visible_Hindi_interlocutor_name_in_descriptions',
    'exact_source_name':'अत','actual_later_question_quote':'मैंने अत से पुछा',
    'reason':'The Hindi source prints अत in the opening route and the final actual question, while the current English metadata calls the person Ata without acknowledging that source spelling. Keep the finite later dialogue and all source positions, but make its printed Hindi name explicit in the speaker/annotation wording; do not silently complete the name from Urdu عطاء or external identity.',
    'source_positions_changed':0,'component_id':'hi-report-2',
    'unchanged_report_type':f['selected_spans'][-1]['report_type'],
    'unchanged_source_report_family_id':f['selected_spans'][-1]['source_report_family_id'],
    'suggested_component_speaker':'The source’s first-person questioner, not externally identified, asks the interlocutor printed अत in this Hindi field about the three-wash instruction and receives the actual yes answer; this is not additional Prophetic speech',
    'also_align_field_speaker_reason_annotation_if_they_otherwise_silently_normalize_this_name':True}
assert r['text'].count(metadata['actual_later_question_quote'])==1
report={'schema':'hadith-bank-independent-original-extension-boundary-findings-v1','status':'bounded_amendment_requested',
    'source_commit':selection['source_publication_commit'],'primary_manifest_sha256':sha(manifest_raw),
    'primary_active_sha256':sha(active),'independent_complete_reading_receipt_sha256':sha(readraw),
    'independent_source_verification_sha256':sha((HERE/'independent-source-verification.json').read_bytes()),
    'all50_complete_candidate_fields_and_all_selected_context_boundaries_inspected':True,
    'actual_complete_fields_read':50,'characters_read':27103,'utf8_bytes_read':58879,
    'requested_source_mask_changes':requests,'requested_metadata_only_refinements':[metadata],
    'mask_changed_fields':6,'metadata_only_fields':1,'changed_parent_occurrences':4,
    'newly_removed_selected_characters':sum(r['characters'] for r in requests),
    'newly_removed_selected_utf8_bytes':sum(r['utf8_bytes'] for r in requests),
    'newly_added_selected_positions':0,'other_newly_reviewed_fields_must_remain_exact':43,
    'previous2335_field_decisions_must_remain_exact':True,
    'parent_decisions_unchanged':True,'source_wording_unchanged':True,
    'no_additional_chain_cut_requested':'Every multistep prefatory route is already context. The actual Zayd visit, bin-Umayyah request, later Ata-labelled dialogue, and short1537/1538/1543 attributions remain finite body/framing.',
    'initial_note_refinements':[{'occurrence_ids':['deenhindi-bukhari:1493'],
        'initial_note':'The initial own notes described two actual report families.',
        'refinement':'The candidate separates the two actual encounters into distinct ordered components inside the same supplied Aisha transmission family. This preserves the distinct events and speakers without asserting two independently transmitted occurrences, and is accepted.'},
        {'occurrence_ids':['deenhindi-bukhari:1537','deenhindi-bukhari:1538'],
         'initial_note':'The initial own notes referred to distinct report families for the embedded practice, dialogue and Aisha recollection.',
         'refinement':'The candidate uses three explicit attribution components within each single source occurrence family. The Aisha citation remains separately labelled and is not merged with Ibn Umar’s or Ibrahim’s voice; that family convention is accepted.'}],
    'retained_meaningful_scope':['1501 herdsman charge and heat cause','1503 Eid prayer deadline','1510 food-grain object and those-days domain','1511 all-on participant scope and source fitr-or-Ramadan uncertainty','1522 resumed Zayd attribution','1523 actual supplied verse rendering','1526 actual abbreviated inner-region condition'],
    'no_new_reading_credit_from_candidate_comparison':True,'source_http_requests':0,'github_writes':0}
data=enc(report);target=HERE/'independent-boundary-findings-v1.json'
if target.exists():assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({'path':str(target),'sha256':sha(data),'bytes':len(data),
    'mask_fields':6,'metadata_only':1,'characters_to_context':report['newly_removed_selected_characters'],
    'utf8_bytes_to_context':report['newly_removed_selected_utf8_bytes'],
    'ranges':[[r['occurrence_id'],r['language'],r['start'],r['end']] for r in requests]}))
