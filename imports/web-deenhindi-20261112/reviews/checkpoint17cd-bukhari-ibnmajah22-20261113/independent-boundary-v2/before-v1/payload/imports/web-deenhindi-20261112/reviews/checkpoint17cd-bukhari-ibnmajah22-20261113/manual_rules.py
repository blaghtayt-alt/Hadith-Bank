"""Explicit boundaries authored after all44 complete original Hi/Ur fields were read."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RECEIPT=json.loads((ROOT/'complete-source-first-reading-receipt.json').read_bytes())
READINGS={}
for row in RECEIPT['fields']:
    READINGS.setdefault(row['occurrence_id'].removeprefix('deenhindi-'),{})[row['language']]=row['source_first_note']
SPECS={}
BOUNDARY_REFINEMENTS=[]
def put(key,kind,speaker,reason,**rules):
    assert key not in SPECS
    SPECS[key]={'id':key,'decision':'register','languages':['hi','ur'],'read_languages':list(READINGS[key]),
        'field_notes':dict(READINGS[key]),'report_type':kind,'speaker':speaker,'reason':reason,**rules}
def comp(start,end,kind,speaker):return {'start_at':start,'stop_before':end,'report_type':kind,'speaker':speaker}

put('bukhari:2633','companion_encounter_and_conditional_prophetic_reply',
    'Abu Said reports the unnamed Bedouin migration questions and the supplied replies.',
    'Keep the full camel, charity, gift and milking dialogue and the conditional assurance. The multi-step route and zakat term apposition remain complete context; no questioner identity or missing body is supplied.',
    start_at={'hi':'अबू सईद ख़ुदरी (रज़ियल्लाहु अन्हु) ने बयान किया','ur':'ابو سعید خدری رضی اللہ عنہ نے بیان کیا'},
    exclude_substrings={'hi':['(ज़कात)'],'ur':['( زکوٰۃ )']})

put('bukhari:2641','companion_attributed_public_statement',
    'Abdullah ibn Utba reports hearing Umar; the entire supplied judgement is Umar own statement, not direct Prophet speech.',
    'Preserve the final hearing attribution and complete outward-action/inner-accountability statement, including both good/bad alternatives and every condition. The preceding multi-step route is context.',
    start_at={'hi':'उन से अब्दुल्लाह बिन उत्बा ने','ur':'ان سے عبداللہ بن عتبہ نے'})

put('bukhari:2642','companion_funeral_dialogue_with_prophetic_answer',
    'Anas reports the two funeral appraisals, repeated replies and the actual question/answer.',
    'Keep both finite funeral scenes and the actual testimony predicate. The source explicitly equivalent-wording/transmitter-doubt block and the prefatory route are apparatus, retained in context; no unprinted Paradise or Hell object is inserted.',
    start_at={'hi':'अनस (रज़ियल्लाहु अन्हु) ने कहा','ur':'انس رضی اللہ عنہ نے کہا'},
    exclude_substrings={
        'hi':['या उस के सिवा और अलफ़ाज़ (इसी मफ़हूम को अदा करने के लिए) कहे (रावी को शुबा है) '],
        'ur':['یا اس کے سوا اور الفاظ ( اسی مفہوم کو ادا کرنے کے لیے ) کہے ( راوی کو شبہ ہے ) ']},
    annotations={'hi':'The source parenthesis supplies the acceptance predicate in the final attributed answer. Its literal wording is retained without independently certifying a reconstructed original quotation.',
                 'ur':'The parenthetic acceptance predicate remains the supplied source wording of the final answer; no external wording or unprinted outcome is inserted.'})

put('bukhari:2647','companion_household_question_and_nursing_scope_reply',
    'Aisha gives the seated-man encounter, her own milk-brother answer and the supplied young-age nursing restriction.',
    'Preserve the actual identity question, Aisha reply and age limitation. The initial route, final corroborating route, opening home gloss and anticipatory milk-brother apposition remain context, while the actual relationship claim stays in her spoken reply.',
    start_at={'hi':'आयशा (रज़ियल्लाहु अन्हा) ने बयान किया','ur':'عائشہ رضی اللہ عنہا نے بیان کیا'},
    stop_before={'hi':'मुहम्मद बिन कसीर के साथ इस हदीस','ur':'محمد بن کثیر کے ساتھ اس حدیث'},
    exclude_substrings={'hi':['(घर में)','(उन के रज़ाई भाई)'],'ur':['( گھر میں )','( ان کے رضاعی بھائی )']})

put('bukhari:2648','historical_report_and_companion_subsequent_personal_account',
    'Urwah reports the conquest-time incident; Aisha separately gives the unnamed woman subsequent repentance, marriage and requests.',
    'Keep the two supplied voices in source order and one family. Preserve every actual action and the unnamed woman; no external identity or missing quotation is supplied. The two prefatory routes remain context.',
    start_at={'hi':'उन्हें उरवा बिन ज़ुबैर ने ख़बर दी','ur':'انہیں عروہ بن زبیر نے خبر دی'},shared_report_family=True,
    components={
      'hi':[comp(None,'आयशा (रज़ियल्लाहु अन्हा) ने बयान किया','transmitted_historical_incident','Urwah reports the conquest-time theft, presentation and stated order.'),
            comp('आयशा (रज़ियल्लाहु अन्हा) ने बयान किया',None,'companion_subsequent_personal_report','Aisha gives the later repentance/marriage and her own practice of conveying the woman requests.')],
      'ur':[comp(None,'عائشہ رضی اللہ عنہا نے بیان کیا','transmitted_historical_incident','Urwah reports the conquest-time theft, presentation and stated order.'),
            comp('عائشہ رضی اللہ عنہا نے بیان کیا',None,'companion_subsequent_personal_report','Aisha gives the later repentance/marriage and her own practice of conveying the woman requests.')]})

put('bukhari:2659','companion_marriage_milk_testimony_encounter',
    'Uqbah reports his marriage, the woman claim, repeated approaches and the actual reply/prohibition.',
    'Retain the marriage subject and remaining-marriage predicate inside the actual rhetorical reply, together with the stated reason. The parallel routes and equivalent told-me/heard-from transmission formulas remain context. The source departure phrase is not expanded into a completed divorce.',
    start_at={'hi':'मुझ से उक़बा बिन हारिस (रज़ियल्लाहु अन्हु) ने बयान किया','ur':'مجھ سے عقبہ بن حارث رضی اللہ عنہ نے بیان کیا'},
    exclude_substrings={'hi':['या (ये कहा के) मैं ने ये हदीस उन से सुनी '],
                        'ur':['یا (یہ کہا کہ) میں نے یہ حدیث ان سے سنی ']})

put('bukhari:2675','companion_market_report_and_separate_attributed_assessment',
    'Ibn Abi Awfa reports the market oath/verse subject, then separately states his judgement about deceptive bidding.',
    'Retain the actual verse excerpt and rendering as the stated revelation subject, with the later assessment under Ibn Abi Awfa own voice. The earlier route stays context. Hindi duplicated/missing wording is literal and is not completed from Urdu.',
    start_at={'hi':"इब्राहिम अबू इसमे'ईल सिक्सकी ने बयां किया",'ur':'ابراہیم ابواسماعیل سکسکی نے بیان کیا'},shared_report_family=True,
    components={
      'hi':[comp(None,'इब्न आबि ऑफ़ (रज़ियल्लाहु अन्हु) ने कहा','companion_market_oath_and_revelation_report','Ibn Abi Awfa reports the source market oath and supplied verse subject; the damaged Hindi wording is not repaired.'),
            comp('इब्न आबि ऑफ़ (रज़ियल्लाहु अन्हु) ने कहा',None,'companion_attributed_ethical_assessment','Ibn Abi Awfa gives his own actual assessment; this is not Prophet speech or a mere word definition.')],
      'ur':[comp(None,'ابن ابی اوفی رضی اللہ عنہ نے کہا','companion_market_oath_and_revelation_report','Ibn Abi Awfa reports the own Urdu market oath, contrary-price clause and supplied verse subject.'),
            comp('ابن ابی اوفی رضی اللہ عنہ نے کہا',None,'companion_attributed_ethical_assessment','Ibn Abi Awfa gives his own actual assessment; this is not Prophet speech or a mere word definition.')]},
    annotations={'hi':'The Hindi field repeats मिल रहा था and lacks the Urdu explicit contrary-price/negative clause; its final assessment is also damaged. All own words remain unchanged, without asserting the absent clause or repairing names.',
                 'ur':'The Urdu explicitly supplies the contrary-price clause and its own source spellings. They do not fill the separate Hindi field.'})

put('bukhari:2681','historical_report_of_ruler_speech',
    'Abu Sufyan reports Heraclius actual retrospective question and assessment; the five commands are cited within Heraclius speech.',
    'Preserve the complete supplied question/answer reference and conclusion under Heraclius voice. The preceding chain and parenthetic Muhammad name apposition remain context. No new direct Prophet quotation or external identity mapping is asserted.',
    start_at={'hi':'उन्हें अबू सुफ़यान (रज़ियल्लाहु अन्हु) ने खबर दी','ur':'انہیں ابوسفیان رضی اللہ عنہ نے خبر دی'},
    exclude_substrings={'hi':['(मुहम्मद (सल्लल्लाहु अलैहि वसल्लम))'],'ur':['( محمد صلی اللہ علیہ وسلم )']})

put('bukhari:2683','companion_historical_announcement_and_claim_payment_report',
    'Jabir reports the post-death announcement and then his own promise claim and payment.',
    'Keep both announcement alternatives, after-death timing, the claimed promise and all three five-hundred amounts. The Bahrain-agent title and prefatory route are context. Actual Hindi/Urdu name spellings remain separate and literal.',
    start_at={'hi':'जाबिर बिन अब्दुल्लाह (रज़ियल्लाहु अन्हुमा) ने बयान किया','ur':'جابر بن عبداللہ رضی اللہ عنہما نے بیان کیا'},
    exclude_substrings={'hi':['(बहरीन के आमिल)'],'ur':['( بحرین کے عامل )']},shared_report_family=True,
    components={
      'hi':[comp(None,'जाबिर (रज़ियल्लाहु अन्हु) ने बयान किया के इस पर','companion_report_of_post_death_announcement','Jabir supplies the property-arrival and Abu Bakr announcement scene.'),
            comp('जाबिर (रज़ियल्लाहु अन्हु) ने बयान किया के इस पर',None,'companion_personal_claim_and_payment_report','Jabir states his own promise claim and the three actual payments.')],
      'ur':[comp(None,'جابر رضی اللہ عنہ نے بیان کیا کہ اس پر','companion_report_of_post_death_announcement','Jabir supplies the property-arrival and Abu Bakr announcement scene.'),
            comp('جابر رضی اللہ عنہ نے بیان کیا کہ اس پر',None,'companion_personal_claim_and_payment_report','Jabir states his own promise claim and the three actual payments.')]},
    annotations={'hi':'The own Hindi prints अला बिन हज़मी. No name correction is borrowed from Urdu or another source.',
                 'ur':'The own Urdu prints علاء بن حضرمی; the separate Hindi spelling remains unchanged.'})

put('bukhari:2685','companion_attributed_admonition',
    'Ibn Abbas supplies the complete admonition and reasoning; these are his source-attributed words.',
    'Preserve the actual questions, oath and negative claims, including the through-your-Prophet recipient/mode qualification. Earlier chain and short lexical/reference appositions are context. The unclosed Urdu parenthesis does not swallow the resumed question predicate.',
    start_at={'hi':'इब्ने अब्बास (रज़ियल्लाहु अन्हुमा) ने कहा','ur':'ابن عباس رضی اللہ عنہما نے کہا'},
    exclude_substrings={'hi':['(दुनिया की)','(क़ुरान)','(अहल-ए-किताब)'],
                        'ur':['( دنیا کی )','( قرآن )','( اہل کتاب ']},
    annotations={'ur':'The source opens an اہل کتاب parenthesis without closing it. Only the explicit appositional opening/name is context; the following سے پوچھنے کو نہیں روکتا and all later content remain literal narration.'})

put('bukhari:2693','companion_report_of_dispute_and_prophetic_proposal',
    'Sahl reports the Quba dispute and the Prophet proposal to go make peace.',
    'Retain the quarrel, stones, information-reaching and actual proposal; no completed reconciliation is inferred. Only the prefatory route is context.',
    start_at={'hi':'सहल बिन साद (रदी अल्लाहू अन्हु) ने बयान किया','ur':'سہل بن سعد رضی اللہ عنہ نے بیان کیا'})

put('bukhari:2694','companion_attributed_verse_interpretation',
    'Aisha gives the actual interpretation, quoted verse/rendering and hypothetical mutual-consent assessment.',
    'Keep the supplied verse as the subject of Aisha interpretation, not an inferred recitation event. The interpretation-said bridge and maintenance-domain parenthesis supply actual attribution/predicate and scope. The prefatory route alone is context; the Companion assessment is not Prophet speech or an unvoiced compiler essay.',
    start_at={'hi':'आयशा (रदी अल्लाहू अन्हा) ने','ur':'عائشہ رضی اللہ عنہا نے'})

put('bukhari:2698','companion_treaty_document_and_dialogue_report',
    'Bara reports the treaty writing, objection, Ali reply, erasure and actual visit conditions.',
    'Preserve the document wording and all actual dialogue, with next-year and three-day scope. The prefatory route, Quraysh identification gloss and terminal technical-term teaching dialogue remain context. No weapon condition is removed with the glossary.',
    start_at={'hi':'उन्होंने बारा बिन आज़िब (रदी अल्लाहू अन्हु) से सुना','ur':'انہوں نے براء بن عازب رضی اللہ عنہ سے سنا'},
    stop_before={'hi':'शागिर्दों ने पूछा के जलबन','ur':'شاگردوں نے پوچھا کہ جلبان'},
    exclude_substrings={'hi':['(क़ुरैश से)'],'ur':['( قریش سے )']})

put('bukhari:2700','companion_treaty_conditions_and_actual_application_report',
    'Bara gives the three conditions and the actual Abu Jandal arrival/return scene.',
    'Keep all three substantive conditions and their stated count, with the converted/imprisoned circumstance and according-to-treaty restriction on the return. The list labels, pure prefatory route and final compiler omission/word-comparison note are context, without supplying any absent variant body.',
    start_at={'hi':'बारा बिन आज़िब (रदी अल्लाहू अन्हु) ने बयान किया','ur':'براء بن عازب رضی اللہ عنہ نے بیان کیا'},
    stop_before={'hi':'इमाम बुख़ारी (रहिमुल्लाह) ने कहा','ur':'امام بخاری رحمہ اللہ نے کہا'},
    exclude_substrings={'hi':['(1)','(2)','(3)'],'ur':['( 1 )','( 2 )','( 3 )']},shared_report_family=True,
    components={
      'hi':[comp(None,'चुनांचे अबू जंदल','companion_report_of_treaty_conditions','Bara states all three actual conditions and their asymmetric return rules.'),
            comp('चुनांचे अबू जंदल',None,'companion_report_of_qualified_treaty_application','The source supplies Abu Jandal status, chained arrival and return under the treaty condition.')],
      'ur':[comp(None,'چنانچہ ابوجندل','companion_report_of_treaty_conditions','Bara states all three actual conditions and their asymmetric return rules.'),
            comp('چنانچہ ابوجندل',None,'companion_report_of_qualified_treaty_application','The source supplies Abu Jandal status, chained arrival and return under the treaty condition.')]})

put('ibnmajah:2612','companion_delegation_report_and_later_conditional_saying',
    'Ashath reports the delegation dialogue; a later transmitter reports Ashath own habitual conditional statement.',
    'Preserve both supplied reports under their actual voices. The later Companion saying is a separate report family from the delegation encounter, not further Prophet speech or an already executed punishment.',
    components={
      'hi':[comp(None,'रावी कहते हैं:','companion_delegation_question_and_prophetic_reply','Ashath gives the delegation encounter and actual lineage reply.'),
            comp('रावी कहते हैं:',None,'companion_habitual_conditional_statement','The unnamed source transmitter reports Ashath own later conditional saying; no completed action is inferred.')],
      'ur':[comp(None,'راوی کہتے ہیں:','companion_delegation_question_and_prophetic_reply','Ashath gives the delegation encounter and actual lineage reply.'),
            comp('راوی کہتے ہیں:',None,'companion_habitual_conditional_statement','The unnamed source transmitter reports Ashath own later conditional saying; no completed action is inferred.')]})

put('ibnmajah:2622','prophetic_story_and_distinct_named_transmitted_additions',
    'Abu Said expressly reports the heard story; source-named Abu Rafi and Hasan Basri versions supply separate finite additions without a newly asserted ultimate speaker or eyewitness status.',
    'Preserve the full supplied story, all actual numbers, wrongful-action qualifiers, dialogue predicates, sinful-village circumstance and the adjudication/measurement/movement additions. Distinguish the three transmitted components in one story family. The intermediate Hammam/Humayd/Bakr route is context; only Urdu footnote markers are removed from the finite bodies. No missing identity, translation or further story ending is supplied.',
    exclude_substrings={'ur':['۱؎','۲؎']},shared_report_family=True,
    components={
      'hi':[comp(None,'रावी-ए-हदीस हम्माम कहते हैं','explicitly_heard_prophetic_story','Abu Said explicitly says he heard and remembered the supplied story from the Prophet.'),
            comp('और वो अबू राफ़े (रज़ियल्लाहु अन्हु) से रिवायत करते हैं वो कहते हैं:','रावी-ए-हदीस क़तादा कहते हैं','source_named_transmitted_adjudication_addition','The source names Abu Rafi for this finite angel/adjudication addition; no ultimate speaker or eyewitness link is added.'),
            comp('रावी-ए-हदीस क़तादा कहते हैं',None,'named_transmitter_relay_of_near_death_version','Qatadah relays Hasan Basri supplied near-death movement/outcome version; this is not asserted as Hasan eyewitness testimony.')],
      'ur':[comp(None,'راوی حدیث ہمام کہتے ہیں','explicitly_heard_prophetic_story','Abu Said explicitly says he heard and remembered the supplied story from the Prophet.'),
            comp('اور وہ ابورافع رضی اللہ عنہ سے روایت کرتے ہیں وہ کہتے ہیں:','راوی حدیث قتادہ کہتے ہیں','source_named_transmitted_adjudication_addition','The source names Abu Rafi for this finite angel/adjudication addition; no ultimate speaker or eyewitness link is added.'),
            comp('راوی حدیث قتادہ کہتے ہیں',None,'named_transmitter_relay_of_near_death_version','Qatadah relays Hasan Basri supplied near-death movement/outcome version; this is not asserted as Hasan eyewitness testimony.')]},
    annotations={'hi':'The three finite source components share the supplied story family. The latter two are explicitly qualified by their own named transmission voice; no unprinted ultimate speaker or eyewitness status is inserted.',
                 'ur':'The Urdu-only parenthetic mercy-deserving conclusion is kept as its actual supplied finite response wording. It is not copied into Hindi or independently certified as reconstructed verbatim speech. Named later versions remain qualified transmissions.'})

put('ibnmajah:2633','companion_report_of_attributed_decision',
    'Mughira reports the actual diya/upon-aqila decision.',
    'Preserve the original technical term and complete actual decision. Each language own parenthetic definition remains literal source context; their differing inclusion of the killer is not harmonized.',
    exclude_substrings={'hi':['(क़ातिल के खानदान वालों)'],'ur':['( قاتل اور اس کے خاندان والوں )']},
    annotations={'hi':'The Hindi glossary names the killer family; the Urdu glossary additionally names the killer. Both original glosses remain complete context without changing either source judgement.',
                 'ur':'The Urdu glossary includes the killer and his family, unlike the shorter Hindi definition. No external legal definition is substituted.'})

put('ibnmajah:2636','companion_injury_complaint_and_qualified_reply_report',
    'Jariyah supplies the injury, request, reply/blessing and the expressly negative qisas outcome.',
    'Preserve not-at-the-joint, the injured person actual request, diya reply and terminal negation. Urdu blood-money apposition alone is lexical context; no broader rule or identity is supplied.',
    exclude_substrings={'ur':['( خون بہا )']})

put('ibnmajah:2640','companion_consultation_and_separately_attributed_testimony',
    'Miswar reports Umar consultation, Mughira actual witness statement and the resumed request/supporting testimony.',
    'Keep all supplied voices and the slave-or-slave-woman disjunction in one source family, without converting the testimony into an external legal rule. Only the Urdu footnote locator is context.',
    exclude_substrings={'ur':['۱؎']},shared_report_family=True,
    components={
      'hi':[comp(None,'तो मुग़ीरा बिन शुअबा','companion_report_of_consultation','Miswar reports Umar actual consultation.'),
            comp('तो मुग़ीरा बिन शुअबा','तो उमर (रज़ियल्लाहु अन्हु) ने कहा','companion_explicit_witness_statement','Mughira states his own presence and the historical decision he reports.'),
            comp('तो उमर (रज़ियल्लाहु अन्हु) ने कहा',None,'companion_request_and_supporting_testimony','The source resumes Umar witness request and Muhammad ibn Maslamah supporting testimony.')],
      'ur':[comp(None,'تو مغیرہ بن شعبہ','companion_report_of_consultation','Miswar reports Umar actual consultation.'),
            comp('تو مغیرہ بن شعبہ','تو عمر رضی اللہ عنہ نے کہا','companion_explicit_witness_statement','Mughira states his own presence and the historical decision he reports.'),
            comp('تو عمر رضی اللہ عنہ نے کہا',None,'companion_request_and_supporting_testimony','The source resumes Umar witness request and Muhammad ibn Maslamah supporting testimony.')]})

put('ibnmajah:2641','companion_consultation_and_personal_testimony',
    'Ibn Abbas gives the Umar consultation setting; Hamal ibn Malik supplies his own two-wife account and cited decisions.',
    'Preserve the two deaths, participant relations, disjunction and both reported decisions. The two janin word glosses and Urdu footnote locator remain context, with no broader ruling or repaired testimony.',
    exclude_substrings={'hi':['(पेट के बच्चे)'],'ur':['( پیٹ کے بچے )','( پیٹ کے بچہ )','۱؎']},shared_report_family=True,
    components={
      'hi':[comp(None,'तो हमल बिन मालिक','companion_report_of_consultation','Ibn Abbas reports Umar search for the supplied ruling.'),
            comp('तो हमल बिन मालिक',None,'companion_personal_testimony_with_cited_decisions','Hamal ibn Malik stands and gives the actual two-wife incident and the decisions he reports.')],
      'ur':[comp(None,'تو حمل بن مالک','companion_report_of_consultation','Ibn Abbas reports Umar search for the supplied ruling.'),
            comp('تو حمل بن مالک',None,'companion_personal_testimony_with_cited_decisions','Hamal ibn Malik stands and gives the actual two-wife incident and the decisions he reports.')]})

put('ibnmajah:2647','companion_report_of_qualified_prophetic_statement',
    'Abdullah ibn Amr relays the actual liability, inheritance and conditional death statement.',
    'Keep residual-share limits, the if clause and all stated agencies. The asabah definition is lexical context; no modern legal conclusion or expanded actor list is supplied.',
    exclude_substrings={'hi':['(बाप के रिश्तेदार)'],'ur':['( باپ کے رشتہ دار )']})

put('ibnmajah:2648','qualified_companion_report_of_decision_and_reply',
    'Jabir gives the supplied liability event, inheritance claim and final husband/son reply; the Hindi bridge remains explicitly damaged.',
    'Retain every own source party label and finite claim/reply. The asabah word definition is context. Neither the damaged Hindi join nor the unusual party labels are repaired from another language or external source.',
    exclude_substrings={'hi':['(बाप के रिश्तेदार)'],'ur':['( باپ کے رشتہ داروں )']},
    annotations={'hi':'The Hindi prints कटीलाह/मक़तूलाह, a damaged ठहरे तोह join and the stranded वसल्लम) before the final reply. These exact words remain; no missing speech link or honorific is inserted from Urdu.',
                 'ur':'The own Urdu names مقتولہ relatives in the inheritance claim. The source party label is retained literally, without normalization from another version.'})

# Every retained non-honorific parenthesis below is an explicit reading decision.
RETAINED_HONORIFICS={
 '(रज़ियल्लाहु अन्हु)','(रज़ियल्लाहु अन्हा)','(रज़ियल्लाहु अन्हुमा)',
 '(रदी अल्लाहू अन्हु)','(रदी अल्लाहू अन्हा)','(रदी अल्लाहू अन्हुमा)',
 '(सल्लल्लाहु अलैहि वसल्लम)','( صلی اللہ علیہ وسلم )',
}
RETAINED_NONHONORIFIC={}
def retain(key,hi,ur,why):
    if hi:RETAINED_NONHONORIFIC[(key,'hi',hi)]=why
    if ur:RETAINED_NONHONORIFIC[(key,'ur',ur)]=why
retain('bukhari:2642','(बारगाह-ए-इलाही में मक़बूल है)','( بارگاہ الٰہی میں مقبول ہے )','The finite acceptance predicate completes the supplied testimony clause in the actual reply.')
retain('bukhari:2659','(निकाह)','( نکاح )','The source supplies the actual marriage subject of the rhetorical question.')
retain('bukhari:2659','(बाक़ी रह सकता है)','( باقی رہ سکتا ہے )','The source supplies the actual remaining-marriage predicate, not a word synonym.')
retain('bukhari:2675','(जो लोग अल्लाह के आहद और अपनी क़समों के ज़रिये थोड़ी कीमत हासिल करते हैं)',None,'This is the actual supplied rendering of the quoted verse subject, not a locator label.')
retain('bukhari:2685','(तुम्हारे नबी के ज़रीये)','( تمہارے نبی کے ذریعہ )','The mode/recipient relation limits the otherwise collective revealed-to-you wording.')
retain('bukhari:2694','(अल्लाह तआला के इस फ़रमान की तफ़सीर में फ़रमाया)','( اللہ تعالیٰ کے اس فرمان کی تفسیر میں فرمایا )','The source supplies the actual said/in-interpretation attribution bridge and predicate.')
retain('bukhari:2694','(नफ़क़ा वग़ैरह)','( نفقہ وغیرہ )','The maintenance domain defines the object of the wife actual proposal.')
retain('bukhari:2698','(आयंदा साल)','( آئندہ سال )','The temporal qualification limits when the actual three-day treaty visit could occur.')
retain('bukhari:2700','(जो मुसलमान हो गए थे और क़ुरैश ने उन को क़ैद कर रखा था)','( جو مسلمان ہو گئے تھے اور قریش نے ان کو قید کر رکھا تھا )','The finite status/captivity circumstance qualifies the actual arriving participant.')
retain('bukhari:2700','(शरायत-ए-मुआहिदा के मुताबिक़)','( شرائط معاہدہ کے مطابق )','The treaty relation limits the source return action and prevents a broader unqualified claim.')
retain('ibnmajah:2622','(ना-हक़)','( ناحق )','The wrongfulness qualification limits the stated killings and the moral domain of the repentance story.')
retain('ibnmajah:2622','(वाह)','( واہ )','This is an actual supplied interjection in the first respondent reply.')
retain('ibnmajah:2622','(क़त्ल के)','( قتل کے )','The killing predicate supplies what the count of people means in the actual rhetorical question.')
retain('ibnmajah:2622','(तौबा की उम्मीद रखता है)','( توبہ کی امید رکھتا ہے )','This is the actual finite question predicate, not a lexical definition.')
retain('ibnmajah:2622','(जहाँ तुमने इतने भारी गुनाह किए)','( جہاں تم نے اتنے بھاری گناہ کئے )','The finite source circumstance relates the instructed departure location to the person actual acts.')
retain('ibnmajah:2622',None,'( لہٰذا وہ رحمت کا مستحق ہوا )','The own Urdu supplies this finite conclusion in the reported angels response; it is not copied to Hindi.')
retain('ibnmajah:2622','(जब फ़रिश्तों में झगड़ा होने लगा तो)','( جب فرشتوں میں جھگڑا ہونے لگا تو )','The temporal trigger belongs to the separately supplied adjudication version.')
retain('ibnmajah:2622','(उनके फ़ैसले के लिए)','( ان کے فیصلے کے لیے )','The source purpose qualification explains the actual sending within this version.')
retain('ibnmajah:2622','(फ़ासला नाप लो)','( فاصلہ ناپ لو )','This is the finite measure-distance imperative supplied in the adjudication response.')
RETAINED_MARKER_WORDS={}
assert len(SPECS)==22 and set(SPECS)==set(READINGS)
