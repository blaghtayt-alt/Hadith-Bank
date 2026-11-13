"""Freeze explicit source-first judgements after all 32 actual candidate comparisons."""
from pathlib import Path
import datetime, gzip, hashlib, json

ROOT=Path(__file__).resolve().parent
OWNER=ROOT.parent/'phase21-checkpoint0d2fa-nasai-ibnmajah16-review'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint0d2fa-nasai-ibnmajah16-20261113.json.gz'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
reading_bytes=(ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(reading_bytes)=='8ad705d9d3d92d2051fa7a1c5a4fc2439926579eebbbcdfb7d3761cfa5f20b8c'
reading=json.loads(reading_bytes)
assert reading['complete_fields_read']==32 and not reading['primary_candidate_or_semantic_notes_opened']
read_fields={(r['occurrence_id'],r['language']):r for r in reading['fields']}
manifest_bytes=(OWNER/'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_bytes)=='75b39b220c619859b998b513b79dee87074cce550ac4f249e4ffb10824097e33'
active_bytes=(OWNER/'publish'/ACTIVE).read_bytes()
assert sha(active_bytes)=='3ae6d94ea8a5ecd7e048543d57218fa94e33126333c745d110db5c2c39ffa1d6'
ledger=json.loads(gzip.decompress(active_bytes))
# These are explicit decisions after full source reading and full displayed span inspection.
ACCEPT={
 'deenhindi-nasai:2553':'Accept all three ordered components in one family: Adi actions, Shubah repetition count, and the own-language exhortation. Hindi damaged/abbreviated join stays qualified; Urdu explicit reply/alternative is not supplied to Hindi.',
 'deenhindi-nasai:2568':'Accept the full source dialogue and current first-person understanding limitation, which supplies the finite predicate for the exception. The awkward terminal source wording remains unrepaired; only the two Urdu footnote markers are context.',
 'deenhindi-nasai:2574':'Refine the initial biography-as-context hypothesis. This actual source framing states the finite pledge action and the candidate identifies its voice as source narration, not as words quoted from Umm Bujayd. It may remain with qualified reporter framing. The occasional-scenario condition is material; the Hindi khurda apposition is a lexical gloss and remains context.',
 'deenhindi-nasai:2579':'Accept the finite assumed-debt scene and actual reply, with inability-to-repay, until-paid and then-stop limitations retained. Three cases are announced but only the one printed case is selected; the other two are not invented.',
 'deenhindi-nasai:2619':'Accept the complete sermon and repeated annual question, conditional obligation/inability, earlier-people explanation and capacity/refrain clauses. Only the one Urdu footnote locator is context.',
 'deenhindi-nasai:2621':'Accept the actual aged-father question/reply under qualified source wording. The defective Hindi question is literal; no negative or missing Hajj clause is borrowed. The Urdu footnote locator is context.',
 'deenhindi-ibnmajah:2554':'Accept all four confessions/turnings and the actual historical event, flight and final question. No unnamed actor identity, external legal rule or extra source episode is inserted.',
 'deenhindi-ibnmajah:2560':'Accept the separate reported discussion, actual question containing the hypothetical Prophet quotation, and Ibn Abbas reply. The source Hindi Shaddad and Urdu Ibn Shaddad remain distinct literal strings; damaged Hindi is not repaired.',
 'deenhindi-ibnmajah:2565':'Accept all three printed reporter names and the actual unmarried/status condition, repeated-offence clauses, third-or-fourth uncertainty and hair-rope consideration. No count or actor identity is resolved externally.',
 'deenhindi-ibnmajah:2571':'Accept the historical scene and separately attributed Ali comparison/assessment in the same family. Preserve forty/forty/eighty and source narrator spellings. Ali sunnah conclusion is not direct Prophet speech; only Urdu footnote apparatus is excluded.',
 'deenhindi-ibnmajah:2578':'Accept the complete historical narrative and attributed conditional advice. The duplicate apostasy lexical explanation and three Urdu footnote locators are context; all actual actions and conditions remain source text.',
 'deenhindi-ibnmajah:2579':'Accept Aisha brief own report independently of the adjacent Anas occurrence. Keep all printed acts and unknown people; only Urdu footnote apparatus is context.',
 'deenhindi-ibnmajah:2584':'Accept the finite shield-theft event and three-dirham price. No broader rule or offender identity is invented.',
 'deenhindi-ibnmajah:2587':'Accept the separate Ibn Muhayriz question and Fudalah answer citing a Prophet action, in one family. Fudalah sunnah assessment stays under his own voice and the own Urdu spelling is literal.',
 'deenhindi-ibnmajah:2607':'Accept the actual encounter, flag, question and uncle statement of commission, including father-death timing. Hushaym identification apparatus and duplicate stepmother gloss are context. Preserve defective Hindi joins; no completed execution or missing identity is asserted.',
 'deenhindi-ibnmajah:2608':'Accept Qurrah finite report of commission with both stated purposes and all-property scope. Do not merge the occurrence with the adjacent Bara account or assert task completion; only Urdu footnote apparatus is context.',
}
checks=[]
for parent in ledger['records']:
    ident=parent['id'];assert ident in ACCEPT and parent['decision']=='register'
    for field in parent['field_reviews']:
        key=(ident,field['language'])
        if key not in read_fields:
            assert not field['reviewed'] and not field['spans'];continue
        text=read_fields[key]['text'];cursor=0;gaps=[]
        for s in field['spans']:
            a,b=s['start'],s['end'];assert cursor<=a<b<=len(text)
            assert sha(text[a:b].encode())==s['sha256']
            if a>cursor:gaps.append({'start':cursor,'end':a,'text':text[cursor:a]})
            cursor=b
        if cursor<len(text):gaps.append({'start':cursor,'end':len(text),'text':text[cursor:]})
        checks.append({'id':ident,'language':field['language'],'source_field_sha256':sha(text.encode()),
            'complete_original_read_before_candidate':True,'complete_candidate_mask_and_voice_inspected':True,
            'accepted':True,'candidate_field_decision':field,'candidate_field_sha256':sha(enc(field)),
            'context_gaps':gaps,'independent_assessment':ACCEPT[ident],
            'initial_source_first_note':read_fields[key]['independent_note']})
assert len(checks)==32 and {(r['id'],r['language']) for r in checks}==set(read_fields)
out={'schema':'independent-complete-boundary-assessment-v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'source_commit':reading['source_commit'],'primary_manifest_sha256':sha(manifest_bytes),'primary_active_sha256':sha(active_bytes),
     'source_first_receipt_sha256':sha(reading_bytes),'all_candidate_field_checks':checks,
     'required_amendments':[],'parent_dispositions_supported':{'register':16,'source_only':0},
     'explicit_initial_judgement_refinements':[{'id':'deenhindi-nasai:2574','languages':['hi','ur'],'initial_judgement':'The short pledge biography could remain context.','final_judgement':ACCEPT['deenhindi-nasai:2574'],'initial_readings_preserved':True}],
     'coverage':{'complete_fields_read_and_compared':32,'unread_sibling_fields':48,'additional_language_readings_claimed':0},
     'scope':'This is an exact source-bound boundary/attribution assessment, not independent authenticity grading or external canonical identity corroboration.'}
p=ROOT/'independent-boundary-assessment-v1.json';assert not p.exists();b=enc(out);p.write_bytes(b)
print(json.dumps({'path':p.name,'sha256':sha(b),'bytes':len(b),'compared_fields':32,'required_amendments':0}))
