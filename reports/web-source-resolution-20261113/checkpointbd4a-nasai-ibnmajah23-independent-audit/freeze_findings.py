"""Freeze the completed49-field independent boundary comparison and exact findings."""
from pathlib import Path
import datetime,gzip,hashlib,json
ROOT=Path(__file__).resolve().parent
OWNER=ROOT.parent/'phase18-checkpointbd4a-nasai-ibnmajah23-review'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpointbd4a-nasai-ibnmajah23-20261113.json.gz'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):return json.loads(p.read_bytes())
manifest_path=OWNER/'delivery-manifest-v1.json';manifest=read(manifest_path)
assert sha(manifest_path.read_bytes())=='3c6edbb4854df1e34dcc3f3241c83e19a1d146c73b250ebdcf087b005f2ba056'
for r in manifest['files']:
    b=Path(r['local_path']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
active_raw=(OWNER/'publish'/ACTIVE).read_bytes()
assert sha(active_raw)=='3b430498bcef0f5934dcd3157fc55e2a8da11aaab72fa39ae1b1d3c3e77509c8'
ledger=json.loads(gzip.decompress(active_raw))
notes=read(ROOT/'complete-independent-source-first-readings.json')
assert sha((ROOT/'complete-independent-source-first-readings.json').read_bytes())=='90d8cb83116f17a3a0ac5d006dec3cf642a4608f1d4d2323eea1459c4cf9a7ad'
assert not notes['candidate_viewed'] and not notes['author_semantic_notes_viewed']
originals=list(map(json.loads,(ROOT/'input/full-hi-ur-reading-input-46.jsonl').read_text().splitlines()))
originals+=list(map(json.loads,(ROOT/'input/additional-nasai2412-originals.jsonl').read_text().splitlines()))
source={(r['occurrence_id'],r['language']):r for r in originals}
observations={
'deenhindi-nasai:2387': 'The actual initial negative answer is already supplied outside the appended transmitter comparison. Request only the exact two comparison blocks as context, preserving all resumed dialogue, fasting frequencies, strength/wish qualifications, the okay discourse token and the final Ramadan/monthly conclusion. The unclosed parenthesis must not extend the exclusion beyond the bounded comparison. Remaining speakers/components belong to one family.',
'deenhindi-nasai:2389': 'Both entire fields and the Mujahid/Abdullah/father/wife roles are supported. Retain the weekly three-days wording, progressive alternatives and explicit one-day timing in Urdu, without converting it to monthly from another report.',
'deenhindi-nasai:2395': 'The whole own Hindi field has an unrepaired broken first-answer join and missing first reward clause. Urdu independently supplies its fuller beginning. All actually printed later numbers/reward replies and alternate-day conclusion are preserved; no cross-language fill.',
'deenhindi-nasai:2405': 'Actual Witr/Friday bathing/three monthly fasts are complete and correctly attributed; only the exact Urdu footnote marker is context, with every instruction intact.',
'deenhindi-nasai:2406': 'The Chasht-parentheses explain the already named Duha term and are correctly context. Both units, the negative no-sleep-without-Witr condition and three monthly days stay selected.',
'deenhindi-nasai:2407': 'Separate provider occurrence genuinely supplies Witr/Friday bath/three monthly fasts. Both full fields and attribution are sound; no imported Duha wording.',
'deenhindi-nasai:2412': 'All five fields were independently read completely. Every field supplies only chain/name/similarity/mursal apparatus; the full context-only source disposition is supported, without an invented absent body.',
'deenhindi-nasai:2416': 'Hafsa observation and all four supplied practices/counts/times remain. Numeric list markers are actual enumeration, not footnotes. Only the Urdu footnote glyph is context; no inferred day exceptions.',
'deenhindi-nasai:2436': 'Complete named-grandfather Muawiya ibn Hayda report preserves his prior repeated oaths, limited knowledge, both actual questions and complete supplied answer. Source attribution and all conditions are sound.',
'deenhindi-nasai:2438': 'Joint Abu Hurayrah/Abu Said source narration retains the three oaths, uncertainty/reaction and final conditions. The damaged Hindi kabail word remains visibly qualified rather than changed to Urdu kabair. Only the Urdu note marker is excluded.',
'deenhindi-nasai:2447': 'Hindi letter introduction and finite later rules are correctly separated across the source omission-summary pointer, all in one written-report family. The complete3561-character Urdu schedule retains all age/count/sex/payment-direction/voluntary exceptions. The recipient role, breeding-readiness requirement, unavailable eligible-age condition and no-extra-payment clause carry material scope; retain them. Only collector synonym and note glyphs remain context. This refines my initial optional age-condition gloss view, transparently retained in the source-first note.',
'deenhindi-nasai:2451': 'The entire independent Muadh commission and forty/thirty/adult instructions are sound. Parenthetic numbers and jizya payment category are material source quantities/scope, not apparatus.',
'deenhindi-nasai:2452': 'Hindi orphan two-year-heifer noun phrase lacks the distinct threshold/predicate and is correctly context; no forty condition is inferred. Urdu actually supplies that condition and remains whole. The adult jizya/dinar-or-cloth clauses stay intact independently.',
'deenhindi-nasai:2453': 'Both full fields retain the negative below-thirty limit, thirty-to-forty interval, male-or-female alternative and forty/two-year change. No quantity parenthesis is mistaken for a reference marker.',
'deenhindi-nasai:2455': 'Both full long schedules were independently inspected, including every threshold, sex/age/breeding condition, compensation direction, exception and silver amount. Sadaqa/zakat synonym and footnote/explicit omission-ellipsis are context. Urdu for-example scope remains. Missing compensation conjunction and duplicated ka remain literal with qualification; do not supply OR or a different silver threshold.',
'deenhindi-nasai:2460': 'The initial exchange and Jarir own later conduct are correctly distinct components in one family. Hindi defective actor/question joins remain unrepaired; Urdu own fuller exchange remains. All even-if-oppression questions and since-hearing limitation are preserved.',
'deenhindi-ibnmajah:2389': 'Khayra reported gift/permission event and both inquiries remain whole. Hindi ends at the husband answer; only Urdu supplies acceptance. Literal differing source spellings and actual relationship remain without external identity repair.',
'deenhindi-ibnmajah:2392': 'Own source names Abdullah ibn Abbas, and that attribution is correctly preserved. Complete donated-horse/cheap-sale inquiry and reply remain without replacing the narrator from a familiar parallel.',
'deenhindi-ibnmajah:2396': 'Ibn Umar reports Umar consultation, actual endowment and all beneficiaries/restrictions. The fruit/profit parenthetical specifies the donated object against the retained principal, a material distinction absent from the bare pronoun. Retention is supported on closer scope review; this explicitly refines my initial source-first suggestion of referent-gloss context. No words or legal status are repaired.',
'deenhindi-ibnmajah:2428': 'Harmas/Harames father/grandfather chain is literal; the unnamed grandfather is the actual witness, not a guessed identified Companion. Both full debt encounter/evening question fields and one-family qualification are supported.',
'deenhindi-ibnmajah:2437': 'Anas actual armor-pledge/barley transaction retains Medina, counterparty description and household purpose. Full fields are independently finite and appropriately attributed.',
'deenhindi-ibnmajah:2444': 'Utbah group encounter, actual Tasm-recitation description and Musa eight-OR-ten employment statement remain. This is actual recitation, not a verse locator to remove. Only terminal Urdu footnote glyph is context; no chapter identification or duration choice.',
'deenhindi-ibnmajah:2448': 'Abu Hurayrah narrated unnamed Ansari encounter includes all hunger/job/dialogue/payment/date-quality conditions, approximate two-sa amount and return. No actor name, exact quantity or acceptance is invented. Whole own fields are supported.'}
cuts={('deenhindi-nasai:2387','hi'):(202,269),('deenhindi-nasai:2387','ur'):(183,246)}
inspected=[];findings=[]
for rec in ledger['records']:
    ident=rec['id'];assert ident in observations
    for f in rec['field_reviews']:
        if not f['reviewed']:continue
        key=(ident,f['language']);r=source[key];text=r['text']
        assert sha(text.encode())==f['text_sha256'];spans=f['spans'];cursor=0;parts=[]
        for span in spans:
            assert cursor<=span['start']<span['end']<=len(text)
            if cursor<span['start']:parts.append({'start':cursor,'end':span['start'],'kind':'context','text':text[cursor:span['start']]})
            assert sha(text[span['start']:span['end']].encode())==span['sha256']
            parts.append({'kind':'selected',**span,'text':text[span['start']:span['end']]});cursor=span['end']
        if cursor<len(text):parts.append({'start':cursor,'end':len(text),'kind':'context','text':text[cursor:]})
        assert ''.join(p['text'] for p in parts)==text
        item={'id':ident,'language':f['language'],'source_record_sha256':rec['source_record_sha256'],
            'text_sha256':f['text_sha256'],'field_decision_sha256':sha(enc(f)),
            'characters':len(text),'utf8_bytes':len(text.encode()),'complete_source_first_reading':True,
            'every_candidate_boundary_and_voice_inspected':True,'independent_observation':observations[ident],
            'decision':'exact_narrow_amendment_requested' if key in cuts else 'accepted',
            'candidate_partition':parts}
        inspected.append(item)
        if key in cuts:
            a,b=cuts[key];selected=[s for s in spans if s['start']==a and s['end']==b];assert len(selected)==1
            findings.append({'id':ident,'language':f['language'],'source_record_sha256':rec['source_record_sha256'],
                'text_sha256':f['text_sha256'],'action':'move_exact_selected_span_to_context','start':a,'end':b,
                'text':text[a:b],'span_sha256':sha(text[a:b].encode()),'characters':b-a,'utf8_bytes':len(text[a:b].encode()),
                'before_span':selected[0],
                'reason':'This is an explicitly labelled unnamed-transmitter comparison of equivalent negative formulas. The complete actual negative answer appears immediately before it. It does not supply a new event, quantity/endpoint qualification or independently attributed first-person report. Keep the exact comparison visible as source context; do not let its unclosed parenthesis swallow resumed dialogue.',
                'preserve':['all source bytes','initial actual negative answer','all resumed questions and answers','every fasting amount and alternative','remaining report voices and one-family identity','parent disposition and complete reading coverage']})
assert len(inspected)==49 and len(findings)==2
assert sum(x['characters'] for x in inspected)==29579 and sum(x['utf8_bytes'] for x in inspected)==61743
result={'schema':'hadith-bank-independent-boundary-findings-v1','status':'TWO_EXACT_AMENDMENTS_REQUESTED',
    'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'primary_manifest_sha256':sha(manifest_path.read_bytes()),'primary_active_sha256':sha(active_raw),
    'source_first_receipt_sha256':sha((ROOT/'complete-independent-source-first-readings.json').read_bytes()),
    'independent_source_verification_sha256':sha((ROOT/'independent-source-verification.json').read_bytes()),
    'source_first_reading_completed_before_candidate_or_author_notes':True,
    'complete_fields_read_and_all_candidate_boundaries_inspected':49,
    'characters_read':29579,'utf8_bytes_read':61743,'parent_dispositions_supported':{'register':22,'source_only':1},
    'source_only_ids':['deenhindi-nasai:2412'],'requested_changes':findings,
    'total_characters_to_context':sum(r['characters'] for r in findings),
    'total_utf8_bytes_to_context':sum(r['utf8_bytes'] for r in findings),
    'all_other47_read_field_decisions_accepted':True,'all_fields_inspected':inspected,
    'transparent_refinements_of_initial_independent_notes':[
        {'id':'deenhindi-nasai:2447','languages':['ur'],'initial_view':'The eligible-age parenthesis could be lexical explanation; recipient and breeding scope needed exact consideration.',
         'final_view':'Retain recipient role, breeding readiness and unavailable-eligible-age clauses because each constrains actual recipients/animals/applicability, not just a technical-word synonym. The full initial note remains immutable.'},
        {'id':'deenhindi-ibnmajah:2396','languages':['hi','ur'],'initial_view':'Fruits/profits could be treated as explanatory pronoun gloss.',
         'final_view':'Retain because it specifies the donated yield as distinct from retained principal; the bare pronoun does not supply that object distinction. No hypothetical external law is used.'},
        {'id':'deenhindi-nasai:2455','languages':['hi'],'initial_view':'Preserve the literal omission ellipsis.',
         'final_view':'The exact ellipsis remains in complete source context. Its context placement does not delete or complete the absent source matter.'}],
    'primary_notes_refinement_required':'The primary2387 initial comparison-as-report proposal must remain archived; a versioned amendment records context placement instead.',
    'independent_pro_qc':'not_performed','source_requests':0,'github_writes':0,'owner_package_mutated':False}
p=ROOT/'independent-boundary-findings-v1.json';assert not p.exists();data=enc(result);p.write_bytes(data)
print(json.dumps({'path':str(p),'bytes':len(data),'sha256':sha(data),'findings':len(findings),
    'characters_to_context':result['total_characters_to_context'],'utf8_bytes_to_context':result['total_utf8_bytes_to_context']}))
