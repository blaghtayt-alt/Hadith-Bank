"""Freeze all47 actual candidate comparisons after the independent originals pass."""
from pathlib import Path
import datetime,gzip,hashlib,json
ROOT=Path(__file__).resolve().parent
OWNER=ROOT.parent/'phase22-checkpoint17cd-nasai22-review'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint17cd-nasai22-20261113.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
reading_bytes=(ROOT/'complete-independent-source-first-readings.json').read_bytes()
assert sha(reading_bytes)=='2fbf9deda88c1b6290c9286862730192d44153821d58f68d80a59cae93b8f778'
reading=json.loads(reading_bytes);assert reading['actual_complete_fields_read']==47 and not reading['primary_candidate_or_semantic_notes_opened']
read_fields={(r['occurrence_id'],r['language']):r for r in reading['fields']}
manifest_bytes=(OWNER/'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_bytes)=='50c8ee57e971cba885cb163fc85491d3d427730ee6694687b9fcec3de1416ecd'
active_bytes=(OWNER/'publish'/ACTIVE).read_bytes()
assert sha(active_bytes)=='b2bc29aec394390a33b679322842e9ce3fb807081807775fac27a2c3d5b14ce7'
ledger=json.loads(gzip.decompress(active_bytes))
# These offsets were individually inspected against the complete original strings.
CUTS={('2628','hi'):[(307,315)],('2628','ur'):[(262,271)],
 ('2650','hi'):[(241,259)],('2650','ur'):[(267,286)],
 ('2670','hi'):[(194,265)],('2670','ur'):[(152,222)],
 ('2682','hi'):[(241,257),(271,291)],('2682','ur'):[(222,224),(248,250)],
 ('2688','hi'):[(219,248)],('2688','ur'):[(203,230)]}
ACCEPT={
 '2628':'The actual Aisha question and recipient-qualified answer remain; only the maqbul lexical gloss is context. The Quran mention is not recast as a verse recitation.',
 '2632':'The unperformed-vow qualification, brother/sister relation, counterfactual debt question and affirmative reply are retained. No actual later performance or grammatical repair is inserted.',
 '2636':'All five own fields are complete chain/similarity pointers without a finite substantive body. English sahih remains source context. Resolved source-only is supported without a neighboring body.',
 '2637':'The father’s old age, both incapacity clauses and on-his-behalf hajj/umrah instruction all remain. It does not supply the missing2636 body.',
 '2641':'All supplied Fadl/woman actions, the father question, affirmative answer and final event dating remain. No actual scene is misclassified as a prefatory route.',
 '2646':'The supplied parenthetic affirmative child-hajj predicate remains within the source-rendered answer, with reward addressed to the woman; no independent direct-quote authentication is claimed.',
 '2648':'The full Rauha encounter and each actual respondent in the reciprocal identity dialogue remain, then the child question and answer. The occurrence is not collapsed into2646.',
 '2650':'The sole printed Medina origin remains. Only the hady definition is context. Hindi’s missing destination/intention and Urdu’s duplicated from remain visible and unfilled.',
 '2659':'The unusual source locality description, overnight stay and mosque prayer remain literally; no canonical geographical repair is introduced.',
 '2664':'The family relations, birth, mediated command and except-tawaf condition remain. Hindi’s spelling/bridge defects and omitted informing sentence are not filled from Urdu.',
 '2666':'The complete finite prohibition retains muhrim scope and both dyes, without importing another garment rule.',
 '2670':'Only the exact qamis/qumus singular-plural comparison is context; the actual resumed garment list, no-shoes exception, below-ankles instruction and two dyes remain.',
 '2682':'The full Hafsa question and reply retain talbid/taqlid and until-completion scope. Only two Hindi term definitions and two Urdu footnote glyphs are context.',
 '2684':'Aisha’s actual two-handed action and each printed timing clause remain; before-exit is not silently converted to the next occurrence’s before-tawaf.',
 '2685':'The own application predicate and both before relations remain; no neighboring version supplies text or changes this source identity.',
 '2686':'The Hindi candidate explicitly uses truncated_companion_report_with_missing_main_action and discloses the absent main predicate; it admits only the printed fragment and actual exit-time clause. Urdu independently contains the anointing action. This satisfies the initial bounded-fragment condition without inventing Hindi perfuming.',
 '2687':'Both perfume applications and the after-ramy/before-tawaf interval remain exactly as printed.',
 '2688':'The actual unlike-your-perfume comparison remains, while only the unassigned yani durability explanation is context. No separately authenticated or newly named explanatory speaker is invented.',
 '2690':'The actual habitual action and availability limit remain, and the speaker/type expressly preserves the recipient as only the own honorific pronoun rather than naming him externally.',
 '2691':'The visibly incomplete Hindi is expressly classified as a truncated report with missing main action; the actual intention clause remains without adding perfume or quality. Urdu independently retains its full action and temporal qualifiers.',
 '2692':'The tenth-of-Dhu-al-Hijjah timing is actual source content, not a footnote. Both before relations and musk mixture remain.',
 '2701':'The application, availability limit and first-person sheen observation in head/beard remain at the source’s actual before-ihram timing, without canonical harmonization.',
}
checks=[]
for parent in ledger['records']:
    ident=parent['id'];num=parent['number'];assert num in ACCEPT
    assert parent['decision']==('exclude' if num=='2636' else 'register')
    for field in parent['field_reviews']:
        key=(ident,field['language'])
        if key not in read_fields:
            assert not field['reviewed'] and not field['spans'];continue
        text=read_fields[key]['text'];cursor=0;gaps=[];selected=[False]*len(text)
        for s in field['spans']:
            a,b=s['start'],s['end'];assert cursor<=a<b<=len(text)
            assert sha(text[a:b].encode())==s['sha256']
            assert s['component_id']=='report-1' and s['source_report_family_id']==ident+':report-1'
            if a>cursor:gaps.append({'start':cursor,'end':a,'text':text[cursor:a]})
            selected[a:b]=[True]*(b-a);cursor=b
        if cursor<len(text):gaps.append({'start':cursor,'end':len(text),'text':text[cursor:]})
        expected=[num!='2636']*len(text)
        for a,b in CUTS.get((num,field['language']),[]):expected[a:b]=[False]*(b-a)
        assert selected==expected,(key,'independent exact mask mismatch')
        if num in ['2686','2691'] and field['language']=='hi':
            assert all(s['report_type']=='truncated_companion_report_with_missing_main_action' and 'omits her main action' in s['speaker'] for s in field['spans'])
        if num=='2690':assert all('does not itself name that recipient' in s['speaker'] for s in field['spans'])
        checks.append({'id':ident,'language':field['language'],'source_field_sha256':sha(text.encode()),
          'complete_original_read_before_candidate':True,'complete_candidate_mask_and_voice_inspected':True,
          'accepted':True,'candidate_field_decision':field,'candidate_field_sha256':sha(enc(field)),
          'independent_expected_selected_mask_sha256':sha(bytes(expected)),'context_gaps':gaps,
          'independent_assessment':ACCEPT[num],'initial_source_first_note':read_fields[key]['independent_note']})
assert len(checks)==47 and {(r['id'],r['language']) for r in checks}==set(read_fields)
out={'schema':'independent-complete-boundary-assessment-v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_commit':reading['source_commit'],'primary_manifest_sha256':sha(manifest_bytes),'primary_active_sha256':sha(active_bytes),
 'source_first_receipt_sha256':sha(reading_bytes),'all_candidate_field_checks':checks,'required_amendments':[],
 'parent_dispositions_supported':{'register':21,'source_only':1},'explicit_initial_judgement_refinements':[],
 'initial_conditional_judgements_resolved':[{'id':'deenhindi-nasai:'+n,'language':'hi','condition':'Only a visibly qualified truncated fragment is supported; its missing main perfume predicate must not be filled.','candidate_satisfies_condition':True,'source_first_notes_unchanged':True} for n in ['2686','2691']],
 'coverage':{'complete_fields_read_and_compared':47,'unread_sibling_fields':63,'additional_language_readings':3},
 'scope':'Source-bound boundaries and actual attribution only; no authenticity certification, unseen parent substitution or external canonical identity assertion.'}
p=ROOT/'independent-boundary-assessment-v1.json';assert not p.exists();b=enc(out);p.write_bytes(b)
print(json.dumps({'path':p.name,'sha256':sha(b),'bytes':len(b),'compared_fields':47,'required_amendments':0}))
