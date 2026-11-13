"""Exact source boundaries authored after the frozen63-field complete reading pass."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECEIPT = json.loads((ROOT / 'complete-source-first-reading-receipt.json').read_bytes())
READINGS = {}
for row in RECEIPT['fields']:
    READINGS.setdefault(row['occurrence_id'].removeprefix('deenhindi-'), {})[row['language']] = row['source_first_note']
SPECS = {}
BOUNDARY_REFINEMENTS = []

def put(number, kind, speaker, reason, **rules):
    key = 'bukhari:' + number
    assert key not in SPECS
    SPECS[key] = {'id':key, 'decision':'register', 'languages':['hi','ur'],
        'read_languages':list(READINGS[key]), 'field_notes':dict(READINGS[key]),
        'report_type':kind, 'speaker':speaker, 'reason':reason, **rules}

def comp(start, end, kind, speaker):
    return {'start_at':start, 'stop_before':end, 'report_type':kind, 'speaker':speaker}

put('2567', 'companion_household_dialogue',
    'Aisha addresses her nephew Urwah; his question and her answer recount household provisions and the Prophet sharing neighbours milk.',
    'Preserve the actual three-crescent/two-month interval, cooking-fire limitation, dates and water, and supplied milk-gift account as a bounded Companion dialogue. The deictic introductory gloss and pure multistep route remain context; no missing food or duration is inferred.',
    start_at={'hi':'आयशा (रदी अल्लाहु अन्हा) ने बयान किया', 'ur':'عائشہ رضی اللہ عنہا نے بیان کیا'},
    exclude_substrings={'hi':['(ये हाल था के)'], 'ur':['( یہ حال تھا کہ )']})

put('2571', 'companion_visit_and_right_side_priority_report',
    'Anas recounts the visit and the Prophet right-side instruction; the closing sunnah assertion is Anas own saying.',
    'Keep the actual occasion, participants, seating, remaining-drink causal circumstance and right-side priority. The preparation-name gloss is context. Distinguish Anas closing repeated sunnah assertion from the Prophet speech, preserving its supplied threefold count and speech predicate in the same family.',
    start_at={'hi':'वोह कहते थे के', 'ur':'وہ کہتے تھے کہ'},
    exclude_substrings={'hi':['(लस्सी बना कर)'], 'ur':['( لسی بنا کر )']},
    shared_report_family=True,
    components={
        'hi':[comp(None,'अनस (रदी अल्लाहु अन्हु) ने कहा के यही', 'companion_visit_with_prophetic_drink_priority_instruction', 'Anas supplies the household visit, seating and Prophet instruction.'),
              comp('अनस (रदी अल्लाहु अन्हु) ने कहा के यही',None,'companion_sunnah_assertion_and_repetition', 'Anas calls this sunnah; the source records his threefold repetition, not new Prophet speech.')],
        'ur':[comp(None,'انس رضی اللہ عنہ نے کہا کہ یہی', 'companion_visit_with_prophetic_drink_priority_instruction', 'Anas supplies the household visit, seating and Prophet instruction.'),
              comp('انس رضی اللہ عنہ نے کہا کہ یہی',None,'companion_sunnah_assertion_and_repetition', 'Anas calls this sunnah; the source records his threefold repetition, not new Prophet speech.')]})

put('2572', 'companion_hunt_gift_and_qualified_transmitted_testimony',
    'Anas hunt/gift account is interrupted by Shuba named certainty and then by an unnamed questioning voice and transmitted answer.',
    'Retain both initially supplied meat alternatives, Shuba own certainty, acceptance and the eating question/answer followed by the return to acceptance-only wording. The latter qualification is visible rather than silently asserting a settled eating testimony. The chase-object gloss and prefatory route remain context. No omitted Hindi route or unnamed questioner identity is borrowed from Urdu or elsewhere.',
    start_at={'hi':'अनस (रज़ियल्लाहु अन्हु) ने बयां किया', 'ur':'انس رضی اللہ عنہ نے بیان کیا'},
    exclude_substrings={'hi':['(उस के पीछे)'], 'ur':['( اس کے پیچھے )']},
    shared_report_family=True,
    components={
        'hi':[comp(None,"(शु'बा ने बाद में",'companion_hunt_and_gift_report','Anas recounts the chase, capture, slaughter and initially alternative gifted parts.'),
              comp("(शु'बा ने बाद में",'रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने उसे', 'named_transmitter_material_certainty', 'The source names Shuba as affirming both thighs without doubt; this is his transmission qualification.'),
              comp('रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने उसे','मैं ने पुछा','transmitted_prophetic_gift_acceptance', 'The source resumes the report of the Prophet acceptance.'),
              comp('मैं ने पुछा',None,'qualified_question_answer_and_resumed_acceptance_wording', 'The questioner is not explicitly named in this supplied clause; preserve the affirmative answer and later acceptance-only wording without supplying a missing identity.')],
        'ur':[comp(None,'( شعبہ نے بعد میں','companion_hunt_and_gift_report','Anas recounts the chase, capture, slaughter and initially alternative gifted parts.'),
              comp('( شعبہ نے بعد میں','رسول اللہ صلی اللہ علیہ وسلم نے اسے','named_transmitter_material_certainty','The source names Shuba as affirming both thighs without doubt; this is his transmission qualification.'),
              comp('رسول اللہ صلی اللہ علیہ وسلم نے اسے','میں نے پوچھا','transmitted_prophetic_gift_acceptance','The source resumes the report of the Prophet acceptance.'),
              comp('میں نے پوچھا',None,'qualified_question_answer_and_resumed_acceptance_wording','The questioner is not explicitly named in this supplied clause; preserve the affirmative answer and later acceptance-only wording without supplying a missing identity.')]},
    annotations={'hi':'The Hindi introduction lacks the additional route printed in Urdu. Its unusual source spellings and unnamed questioner link remain literal; no missing transmitter or corrected word is inserted.',
                 'ur':'The complete own Urdu route remains available as source context. It does not justify inserting an unprinted speaker link into either later question clause or the Hindi field.'})

put('2573', 'companion_gift_return_with_location_uncertainty',
    'The source-named Saab gift account includes the Prophet return/explanation and an unnamed transmitter location uncertainty.',
    'Keep Abwa or Waddan and the explicit uncertainty, the observed grief signs and the stated ihram-only reason. The English animal synonym and prefatory route remain context. Separate the materially uncertain location qualifier from Prophet speech without inventing a settled place.',
    start_at={'hi':"सा'अब बिन जथामा", 'ur':'صعب بن جثامہ'},
    exclude_substrings={'hi':['(wild donkey)']}, shared_report_family=True,
    components={
        'hi':[comp(None,'(रावी को शुबहा है)','transmitted_companion_gift_and_alternative_location','The source-named Saab gives the gift at one of the two printed locations.'),
              comp('(रावी को शुबहा है)','आप (सल्लल्लाहु अलैहि वसल्लम) ने उन का','unnamed_transmitter_material_location_uncertainty','The unnamed transmitter explicitly leaves which location uncertain.'),
              comp('आप (सल्लल्लाहु अलैहि वसल्लम) ने उन का',None,'prophetic_return_and_ihram_reason_report','The report resumes with return, observed grief and the Prophet own stated reason.')],
        'ur':[comp(None,'( راوی کو شبہ ہے )','transmitted_companion_gift_and_alternative_location','The source-named Saab gives the gift at one of the two printed locations.'),
              comp('( راوی کو شبہ ہے )','آپ صلی اللہ علیہ وسلم نے ان کا','unnamed_transmitter_material_location_uncertainty','The unnamed transmitter explicitly leaves which location uncertain.'),
              comp('آپ صلی اللہ علیہ وسلم نے ان کا',None,'prophetic_return_and_ihram_reason_report','The report resumes with return, observed grief and the Prophet own stated reason.')]})

put('2574', 'companion_report_of_gift_timing_and_qualified_motive',
    'Aisha reports the gift timing; the source explicitly retains an unnamed transmitter alternative about gifts versus the particular day.',
    'Keep the actual Prophet recipient, Aisha turn and both supplied motive formulations with the uncertainty that limits them. The pure prefatory route remains context; no formulation is silently preferred and no new Prophet quotation is asserted.',
    start_at={'hi':'आयशा (रदी अल्लाहु अन्हा) ने के', 'ur':'عائشہ رضی اللہ عنہا نے کہ'},
    shared_report_family=True,
    components={
        'hi':[comp(None,'अपने हदाया से,','companion_gift_timing_report','Aisha transmits the actual gift timing and recipient.'),
              comp('अपने हदाया से,',None,'qualified_transmitted_motive_with_unnamed_uncertainty','The source reporting voice preserves gifts or waiting for that day, with unnamed transmitter doubt, as the stated motive.')],
        'ur':[comp(None,'اپنے ہدایا سے،','companion_gift_timing_report','Aisha transmits the actual gift timing and recipient.'),
              comp('اپنے ہدایا سے،',None,'qualified_transmitted_motive_with_unnamed_uncertainty','The source reporting voice preserves gifts or waiting for that day, with unnamed transmitter doubt, as the stated motive.')]})

put('2575', 'companion_food_gift_report_and_table_argument',
    'Ibn Abbas reports his aunt gift and the Prophet conduct, then supplies his own table-based conditional argument.',
    'Retain the three supplied foods, what was eaten or disliked, and the separately attributed actual Ibn Abbas inference. Its same-table restriction remains part of that source argument. Both reptile synonyms are lexical context, as is the prefatory route. Do not recast the Companion argument as a new Prophet ruling.',
    start_at={'hi':'इब्न-ए-अब्बास (रदी अल्लाहु अन्हुमा) ने बयान किया', 'ur':'ابن عباس رضی اللہ عنہما نے بیان کیا'},
    exclude_substrings={'hi':['(साहना)'], 'ur':['( ساہنہ )']}, shared_report_family=True,
    components={
        'hi':[comp(None,'इब्न-ए-अब्बास (रदी अल्लाहु अन्हुमा) ने कहा','companion_food_gift_and_prophetic_conduct_report','Ibn Abbas transmits the actual gift and eating/leaving conduct.'),
              comp('इब्न-ए-अब्बास (रदी अल्लाहु अन्हुमा) ने कहा',None,'companion_conditional_table_based_argument','Ibn Abbas gives his own supplied conditional argument about eating at that same table.')],
        'ur':[comp(None,'ابن عباس رضی اللہ عنہما نے کہا','companion_food_gift_and_prophetic_conduct_report','Ibn Abbas transmits the actual gift and eating/leaving conduct.'),
              comp('ابن عباس رضی اللہ عنہما نے کہا',None,'companion_conditional_table_based_argument','Ibn Abbas gives his own supplied conditional argument about eating at that same table.')]})

put('2577', 'companion_meat_gift_report_with_recipient_condition',
    'Anas transmits the offered meat, its charity provenance and the Prophet recipient-dependent reply.',
    'The when-it-arrived-from-her qualification supplies the actual transfer condition and stays with the statement. Keep the original recipient contrast without inventing another transaction or generalized legal rule. Only the prefatory route is context.',
    start_at={'hi':'अनस (रदी अल्लाहु अन्हु) ने बयान किया', 'ur':'انس رضی اللہ عنہ نے بیان کیا'})

put('2580', 'two_companion_household_reports',
    'Aisha reports habitual gift timing; Umm Salamah separately describes her co-wives gathering and complaint.',
    'Preserve two supplied Companion voices and their distinct report families: habitual gift timing and the separately introduced gathering/complaint with no reply. The complaint-topic/manner qualification is actual narrative scope. The appended mothers-of-believers title and its attached blessing are identity apparatus retained in source context, together with the prefatory route.',
    start_at={'hi':'आयशा (रदी अल्लाहु अन्हा) ने बयान किया', 'ur':'عائشہ رضی اللہ عنہا نے بیان کیا'},
    exclude_substrings={'hi':['(उम्माहत-ुल-मोमिनीन (रिदवानुल्लाहि अलैहिन्ना))'], 'ur':['( امہات المؤمنین رضوان اللہ علیہن )']},
    components={
        'hi':[comp(None,'और उम्म-ए-सलमा','companion_habitual_gift_timing_report','Aisha gives her own habitual gift-timing report.'),
              comp('और उम्म-ए-सलमा',None,'companion_household_gathering_and_complaint_report','Umm Salamah reports the gathering, the actual complaint/topic and the Prophet lack of reply.')],
        'ur':[comp(None,'اور ام سلمہ','companion_habitual_gift_timing_report','Aisha gives her own habitual gift-timing report.'),
              comp('اور ام سلمہ',None,'companion_household_gathering_and_complaint_report','Umm Salamah reports the gathering, the actual complaint/topic and the Prophet lack of reply.')]})

put('2588', 'companion_illness_account_and_later_identification_dialogue',
    'Aisha reports the illness and assisted movement; Ubaydullah later recounts his own exchange with Ibn Abbas about the unnamed man.',
    'Retain the wives permission, severe illness, dragging feet and two-person support. Keep Aisha unnamed-man wording unchanged and the later source-supplied Ibn Abbas identification as a separately attributed actual dialogue in the same report family. No identity is silently inserted into Aisha earlier words; the multistep route is context.',
    start_at={'hi':'आइशा (रज़ियल्लाहु अन्हा) ने बयान किया', 'ur':'عائشہ رضی اللہ عنہا نے بیان کیا'}, shared_report_family=True,
    components={
        'hi':[comp(None,'उबैदुल्लाह ने बयान किया के फिर','companion_illness_permission_and_movement_report','Aisha recounts the supplied permission and movement, naming Abbas and leaving the other man unnamed.'),
              comp('उबैदुल्लाह ने बयान किया के फिर',None,'named_transmitter_later_question_and_companion_identification','Ubaydullah recounts his own later question/answer with Ibn Abbas, who identifies Ali in that separate supplied dialogue.')],
        'ur':[comp(None,'عبیداللہ نے بیان کیا کہ پھر','companion_illness_permission_and_movement_report','Aisha recounts the supplied permission and movement, naming Abbas and leaving the other man unnamed.'),
              comp('عبیداللہ نے بیان کیا کہ پھر',None,'named_transmitter_later_question_and_companion_identification','Ubaydullah recounts his own later question/answer with Ibn Abbas, who identifies Ali in that separate supplied dialogue.')]})

put('2590', 'companion_property_question_and_prophetic_charity_reply',
    'Asma asks about the only property left with her by her husband Zubayr; the source supplies the Prophet response.',
    'Keep the husband relationship and sole-property condition as actual participant/property scope. Retain the warning parenthesis containing Allah as agent and the supplied negation; removing it changes the clause. Preserve the Urdu stray punctuation without repairing it. The pure prefatory route is context.',
    start_at={'hi':'अस्मा (रज़ियल्लाहु अन्हा) ने बयान किया', 'ur':'اسماء رضی اللہ عنہا نے بیان کیا'})

put('2592', 'companion_emancipation_report_and_finite_abbreviated_variant',
    'Maimunah supplies the emancipation and Prophet dialogue; the alternate route contains only a finite repeated emancipation clause.',
    'Retain the actual no-prior-permission circumstance, later visit, question/yes answer and maternal-relative counterfactual. The appended alternate route is context, but its supplied finite Maimunah-freed-her-slave clause is an eligible abbreviated report in the same family. Its bare to-the-end pointer stays context and supplies no unseen continuation. The opening title and multistep route are also context.',
    start_at={'hi':'मैमूनह बिंत हारिस', 'ur':'میمونہ بنت حارث'}, shared_report_family=True,
    components={
        'hi':[comp(None,'इस हदीस को बुकैयर','companion_emancipation_and_prophetic_counterfactual_reply','Maimunah reports her emancipation, subsequent conversation and the Prophet actual counterfactual reply.'),
              comp('मैमूनह (रज़ियल्लाहु अन्हा) ने अपनी','अखीर तक','finite_abbreviated_companion_emancipation_variant','The alternate source transmission supplies only the finite Maimunah emancipation clause; its omitted continuation is not reconstructed.')],
        'ur':[comp(None,'اس حدیث کو بکیر','companion_emancipation_and_prophetic_counterfactual_reply','Maimunah reports her emancipation, subsequent conversation and the Prophet actual counterfactual reply.'),
              comp('میمونہ رضی اللہ عنہا نے اپنی','اخیر تک','finite_abbreviated_companion_emancipation_variant','The alternate source transmission supplies only the finite Maimunah emancipation clause; its omitted continuation is not reconstructed.')]})

put('2594', 'abbreviated_companion_emancipation_and_prophetic_reply',
    'The own source names Maimunah as the Prophet wife and supplies her emancipation followed by the counterfactual reply.',
    'This separately identified occurrence contains its own finite report despite the conjunctive opening route. Keep the participant relationship, emancipation and maternal-relative reward condition. Separate the pure route and its saying connector without borrowing the fuller2592 account or merging their IDs.',
    start_at={'hi':'नबी करीम (सल्लल्लाहु अलैहि वसल्लम) की ज़ौजा', 'ur':'نبی کریم صلی اللہ علیہ وسلم کی زوجہ'})

put('2595', 'companion_neighbour_gift_question_and_prophetic_reply',
    'Aisha asks which of her two neighbours should receive the gift; the Prophet supplies the nearest-door answer.',
    'Preserve both neighbours, the actual gift question and relative door-distance reply. The multistep transmission route and affiliation stay source context; no additional neighbour identity or contemporary rule is supplied.',
    start_at={'hi':'आइशा (रज़ियल्लाहु अन्हा) ने बयान किया', 'ur':'عائشہ رضی اللہ عنہا نے بیان کیا'})

put('2596', 'companion_gift_return_and_resumed_first_person_reaction',
    'The source-named Saab recounts the gift, return and his own observed facial reaction followed by the Prophet explanation.',
    'Keep both alternative locations, the source-stated ihram condition, actual reaction object and stated return reason. The prefatory route, appended Companion biography and Hindi English-animal synonym are context. Preserve every own-field name and spelling, including the Hindi condition wording, without repairing it from2573 or Urdu.',
    start_at={'hi':'उन का बयान था के', 'ur':'ان کا بیان تھا کہ'},
    exclude_substrings={'hi':['(वाइल्ड ऐस)']},
    annotations={'hi':'The own source prints its names and the condition spelling मेहरम. Those exact bytes remain; no familiar or sibling form replaces them.',
                 'ur':'This separately read Urdu occurrence retains its own source wording and is not merged with2573.'})

put('2597', 'companion_collector_gift_claim_and_prophetic_response',
    'Abu Humayd transmits the source-named collector claim, Prophet challenge/oath and collective observation of raised hands.',
    'Retain the actual challenge, parents-house test, oath, unlawful-taking restriction, animal burdens, observed gesture and threefold speech. The explicit treasury gloss remains context; the zakah-property domain, unlawful qualifier and actual speech/repetition predicates remain substantive source scope after the collected-property versus claimed-personal-gift contrast. Preserve the printed collector name without replacing it with a familiar external name.',
    start_at={'hi':'अबू हुमैद साइदी', 'ur':'ابو حمید ساعدی'},
    exclude_substrings={'hi':['(यानी बैत-उल-माल का)'], 'ur':['( یعنی بیت المال کا )']},
    annotations={'hi':'The source prints इब्न अतबिय्या. No alternate collector identity or spelling is substituted.',
                 'ur':'The source prints ابن اتبیہ. The original name remains exactly as supplied.'})

put('2599', 'companion_father_son_visit_and_reserved_garment_report',
    'The source-named Miswar recounts his father request and their visit, with the Prophet reserved-garment statement and question.',
    'Keep the actual son/addressee framing, father relationship, visit sequence, garment gift and pleasure question as one supplied event family. These source relationships are not removed as name synonyms. The prefatory route remains context; source names are uncorrected.',
    start_at={'hi':'मिसवर बिन मखरामा', 'ur':'مسور بن مخرمہ'})

put('2603', 'companion_mosque_payment_report',
    'The own Arabic route names Jabir and the own English field names him directly; he reports the mosque visit and excess repayment.',
    'All five complete fields were read. Arabic and English each independently supply a finite mosque-visit/payment report. Hindi, Urdu and Roman Urdu contain only duplicated routes ending at a missing-body connector and remain reviewed source context. Preserve the exact short report and English unclosed quotation without adding the camel or prayer-unit details from2604 or another source.',
    languages=['ar','en'], start_at={'ar':'أَتَيْتُ'},
    annotations={'ar':'Only the actual supplied first-person mosque/payment body is selected; the complete prefatory route remains available in source context.',
                 'en':'The English field ends without a closing quotation mark. Its exact finite report is retained with no punctuation or missing-text repair.',
                 'hi':'The full Hindi field is a duplicated transmission route with no supplied report body. No sibling translation is copied into this field.',
                 'ur':'The full Urdu field repeats the route and stops before a report body. It remains completely preserved, reviewed source context.',
                 'ur-Latn':'The complete Roman Urdu field likewise supplies only duplicated routes and a missing-body connector; no narration text is inferred.'})

put('2604', 'companion_camel_payment_and_later_personal_history',
    'Jabir reports the camel transaction; Shuba explicitly qualifies the wording of the payment detail; the final personal-history clause is separately supplied.',
    'Keep the mosque/two-unit instruction and actual weighing account. Preserve Shuba named uncertainty, the explicit Jabir voice, Bilal agency under the Prophet command, coin-side pan and excess-payment purpose. The final retained-money/Harrah seizure is a separate later personal-history family; only its appended Umayyad-army identification gloss is context. Do not broaden certainty or import details into2603.',
    start_at={'hi':'आप फ़रमाते थे के मैं ने', 'ur':'آپ فرماتے تھے کہ میں نے'},
    exclude_substrings={'hi':['(उमवी लश्कर)'], 'ur':['( اموی لشکر )']},
    source_report_family_by_component={'report-1':'report-1','report-2':'report-1','report-3':'report-2'},
    components={
        'hi':[comp(None,'शुआबा ने बयान किया, मेरा','companion_camel_sale_and_prophetic_prayer_payment_report','Jabir recounts the sale, arrival, prayer instruction and payment.'),
              comp('शुआबा ने बयान किया, मेरा','इस में से कुछ थोड़ा','named_transmitter_uncertain_relay_of_payment_detail','Shuba says he thinks Jabir used the supplied weighing wording; the actual detail remains visibly qualified, with its printed speaker and agency.'),
              comp('इस में से कुछ थोड़ा',None,'companion_later_retained_money_and_seizure_report','The resumed first-person Jabir account supplies later retention and seizure at Harrah; this is distinct from the earlier camel/payment event.')],
        'ur':[comp(None,'شعبہ نے بیان کیا، میرا','companion_camel_sale_and_prophetic_prayer_payment_report','Jabir recounts the sale, arrival, prayer instruction and payment.'),
              comp('شعبہ نے بیان کیا، میرا','اس میں سے کچھ تھوڑا','named_transmitter_uncertain_relay_of_payment_detail','Shuba says he thinks Jabir used the supplied weighing wording; the actual detail remains visibly qualified, with its printed speaker and agency.'),
              comp('اس میں سے کچھ تھوڑا',None,'companion_later_retained_money_and_seizure_report','The resumed first-person Jabir account supplies later retention and seizure at Harrah; this is distinct from the earlier camel/payment event.')]})

put('2606', 'companion_creditor_demand_and_prophetic_repayment_report',
    'Abu Hurayrah transmits the creditor demand, companions movement and the Prophet leave-him and repayment instructions.',
    'Retain the supplied harsh-demand predicate as the actual cause, same-age request, better-age availability and repayment statement. The Hindi route and later speech join are visibly damaged; its omitted rights-holder sentence is not supplied from Urdu. Each language retains only its own report words after the prefatory route.',
    start_at={'hi':'अबू हुरैरा (रज़ियल्लाहु अन्हु) ने कहा', 'ur':'ابوہریرہ رضی اللہ عنہ نے کہا'},
    annotations={'hi':'The source duplicates a route verb and omits the rights-holder speech found in Urdu. Its later honorific/speech join remains literal; no missing route or sentence is reconstructed.',
                 'ur':'This Urdu field independently supplies the rights-holder sentence. That wording is admitted here only, not transferred into Hindi.'})

put('2612', 'companion_silk_garment_proposal_gift_and_recipient_report',
    'Ibn Umar reports Umar proposal, the Prophet objection and later gift/reply, and Umar transfer to his brother.',
    'Keep the for-sale circumstance, Friday/delegation proposal, actual silk material of the later gifts, objection, not-for-wearing reply and the brother religious/location scope. The supplied personal name is not expanded or corrected. Only the multistep prefatory route is context; the meaningful sale/material predicates stay selected.',
    start_at={'hi':'इब्न उमर (रज़ियल्लाहु अन्हुमा) ने बयान किया', 'ur':'ابن عمر رضی اللہ عنہما نے بیان کیا'})

put('2613', 'qualified_household_visit_and_curtain_dialogue_report',
    'Ibn Umar transmits the household account; the damaged Hindi bridge leaves an unidentified reporting voice before its supplied non-entry clause.',
    'Keep the finite visit, non-entry, striped-curtain reason, return, world-adornment limitation, relay, request and needy-house instruction. The Hindi orphan reporting connector has no supplied subject and remains context; its actual finite non-entry clause stays a qualified fragment in the same family. Do not fill Ali return or Fatima reporting from Urdu. The meaningful return/scope/message predicates are preserved, not removed as generic parentheses.',
    start_at={'hi':'इब्न उमर (रज़ियल्लाहु अन्हुमा) ने बयां किया', 'ur':'ابن عمر رضی اللہ عنہما نے بیان کیا'},
    shared_report_family=True,
    components={'hi':[
        comp(None,'ने ज़िक्र किया','companion_transmitted_visit_report','Ibn Umar supplies the Prophet visit to Fatima house; the following source bridge is incomplete.'),
        comp('(की आप','अली (रज़ियल्लाहु अन्हु) ने इसका','finite_non_entry_fragment_with_missing_reporting_link','The Hindi source supplies a finite non-entry clause but no complete preceding speaker/reporting link; its voice remains qualified without borrowing Urdu.'),
        comp('अली (रज़ियल्लाहु अन्हु) ने इसका',None,'household_curtain_dialogue_and_prophetic_instruction','The source resumes a named Ali relay, actual curtain explanation, recipient request and Prophet instruction; source pronouns remain as printed.')]},
    annotations={'hi':'The Hindi opening skips the complete Ali-return/Fatima-reporting sequence printed in Urdu and leaves ने ज़िक्र किया without its speaker. That orphan connector is context; the supplied visit and finite non-entry statement remain separately qualified. No missing subject or wording is inserted.',
                 'ur':'The full Urdu field independently supplies its own Ali-return/Fatima-reporting sequence. It is not used to repair the distinct Hindi omission.'})
BOUNDARY_REFINEMENTS.append({'id':'bukhari:2613','language':'hi',
    'refinement':'During exact-boundary serialization, the already noted missing-subject connector ने ज़िक्र किया is isolated as context, while the supplied finite non-entry clause remains a separately qualified component in the same family. The initial complete-reading note remains unchanged.'})

put('2614', 'companion_garment_wearing_reaction_and_distribution_report',
    'Ali reports his gift, wearing, observed anger and subsequent division among his women.',
    'Preserve the supplied conduct account without inventing a spoken Prophet prohibition or naming the women. The actual source does not expand them to wives or provide individual identities. The prefatory route remains context.',
    start_at={'hi':'अली (रज़ियल्लाहु अन्हु) ने बयान किया', 'ur':'علی رضی اللہ عنہ نے بیان کیا'})

for number in ['2615','2616']:
    put(number, 'companion_silk_gift_and_prophetic_comparison_report',
        'The source-named Anas transmits the silk gift, men restriction, companions reaction and the Prophet oath/comparison.',
        'Both complete languages of this distinct source occurrence were actually read. Retain the men-only restriction, supplied reaction content and finite direct-address bridge, together with the oath and Saad comparison. The shortened/damaged Hindi route stays exact source context. Identical wording does not merge2615 and2616 or create borrowed-language review credit.',
        start_at={'hi':'अनास (रज़ियल्लाहु अन्हु) ने बयां किया', 'ur':'انس رضی اللہ عنہ نے بیان کیا'},
        annotations={'hi':'The source introduction is visibly shortened and prints कटड़ा and अनास. No omitted links, corrected name or spelling is inserted; this field was independently read for this exact occurrence.',
                     'ur':'This complete Urdu field was independently read for this exact source ID even where another occurrence supplies identical wording. Parenthetical narrative predicates remain the source wording, not an independent verbatim-speech certification.'})

put('2617', 'companion_poisoned_meat_account_and_later_observation',
    'Anas ibn Malik transmits the unnamed woman episode and separately supplies his own continuing observation.',
    'Keep the immediate statement and actual confession predicates inside the source parentheses, the proposal/refusal and the final Anas observation as distinct voices within the same report family. Do not infer the unnamed woman identity or recast the final personal observation as Prophet speech. The prefatory route remains context.',
    start_at={'hi':'अनस बिन मालिक', 'ur':'انس بن مالک'}, shared_report_family=True,
    components={
        'hi':[comp(None,'इस ज़ेहर का असर मैं ने','companion_poisoned_meat_episode_with_prophetic_reply','Anas transmits the source-stated episode, confession and proposal/refusal.'),
              comp('इस ज़ेहर का असर मैं ने',None,'companion_own_continuing_observation','Anas supplies his own continuing palate observation; it is not a new Prophet utterance or an independent medical verification.')],
        'ur':[comp(None,'اس زہر کا اثر میں نے','companion_poisoned_meat_episode_with_prophetic_reply','Anas transmits the source-stated episode, confession and proposal/refusal.'),
              comp('اس زہر کا اثر میں نے',None,'companion_own_continuing_observation','Anas supplies his own continuing palate observation; it is not a new Prophet utterance or an independent medical verification.')]})

put('2619', 'qualified_garment_proposal_gift_reply_and_transfer_report',
    'Abdullah ibn Umar supplies the garment account; the Hindi response bridge is damaged and its resumed purpose clause has no supplied speaker link.',
    'Keep the actual sale/proposal, objection, gift, Umar question and final brother transfer. In Hindi, retain the finite resumed sale-or-dress purpose as an explicitly unidentified voice, leaving its dangling comparison connector in context; do not insert the missing Prophet attribution or not-for-wearing negation from Urdu. The non-Muslim recipient condition is material and remains selected. Urdu independently supplies its complete actual reply.',
    start_at={'hi':'अब्दुल्लाह बिन उमर ने की', 'ur':'عبداللہ بن عمر نے کہ'}, shared_report_family=True,
    components={
        'hi':[comp(None,'उम्र (रज़ियल्लाहु अन्हु) ने कहा कि मैं इसे','companion_garment_proposal_objection_and_gift_report','The source-named Abdullah ibn Umar transmits the proposal, objection and later garment gift.'),
              comp('उम्र (रज़ियल्लाहु अन्हु) ने कहा कि मैं इसे','जबकि आप खुद ही','companion_question_before_damaged_response_bridge','Umar actual supplied how-can-I-wear question remains; the following incomplete comparison connector is context.'),
              comp('इसलिए दिया कि', 'चुनांचे उम्र','finite_resumed_purpose_fragment_with_unidentified_voice','The Hindi source resumes a finite sale-or-dress purpose without a complete speaker/response link. Preserve it as unidentified, never borrowing the Urdu Prophet attribution or missing negation.'),
              comp('चुनांचे उम्र',None,'companion_garment_transfer_report','The source reports Umar sending the garment to his brother who had not accepted Islam, in Mecca.')],
        'ur':[comp(None,'عمر رضی اللہ عنہ نے کہا کہ میں اسے','companion_garment_proposal_objection_and_gift_report','The source-named Abdullah ibn Umar transmits the proposal, objection and later garment gift.'),
              comp('عمر رضی اللہ عنہ نے کہا کہ میں اسے','آپ صلی اللہ علیہ وسلم نے فرمایا کہ میں نے','companion_question_and_reference_to_prior_statement','Umar complete own Urdu question and reference to the prior statement are supplied.'),
              comp('آپ صلی اللہ علیہ وسلم نے فرمایا کہ میں نے','چنانچہ عمر','prophetic_garment_purpose_reply','The own Urdu field explicitly attributes the not-for-wearing and sale-or-dress reply to the Prophet, with its recipient restriction.'),
              comp('چنانچہ عمر',None,'companion_garment_transfer_report','The source reports Umar sending the garment to his brother who had not accepted Islam, in Mecca.')]},
    annotations={'hi':'The original Hindi wording omits the response attribution and negation supplied in Urdu and joins the preceding question to इसलिए दिया कि. The incomplete जबकि...था bridge remains source context; the finite resumed purpose is visibly labelled an unidentified voice. No missing words, name, punctuation or negation are repaired.',
                 'ur':'The Urdu source itself supplies the full question, explicit Prophet response and not-for-wearing negation. These are admitted only in this independently read field.'})

put('2620', 'companion_mother_visit_and_kinship_question_report',
    'Asma bint Abi Bakr reports her mother visit, own question and the Prophet affirmative kinship reply.',
    'Keep the mother religious status and actual desire-to-meet object, which limits the supplied intention rather than asserting another purpose. The appended mother personal-name identification is biography retained in context, with the prefatory route. No conversion, financial request or external identity is inferred.',
    start_at={'hi':'अस्मा बिंत अबी बक्र', 'ur':'اسماء بنت ابی بکر'},
    exclude_substrings={'hi':['(क़तीला बिंत अब्दुल उज़्ज़ा)'], 'ur':['( قتیلہ بنت عبدالعزیٰ )']})

put('2625', 'companion_report_of_prophetic_gift_decision',
    'Jabir transmits the source-stated decision about the printed umra/umri gift term.',
    'The field supplies a finite attributed decision and recipient ownership consequence. Preserve the original term without adding a technical definition or identifying it with a different practice. The pure prefatory chain remains context.',
    start_at={'hi':'जाबिर (रज़ियल्लाहु अन्हु) ने बयान किया', 'ur':'جابر رضی اللہ عنہ نے بیان کیا'})

put('2627', 'companion_fear_borrowed_horse_and_return_report',
    'Anas reports the Medina fear, the Prophet borrowing and ride, and the supplied return statement.',
    'Retain the enemy-attack domain of the fear and the finite companions-were-along predicate as actual source circumstances. Preserve the owner/name, no-danger statement and sea comparison. The speed explanation of that metaphor is lexical context, as is the prefatory route; no added military event is inferred.',
    start_at={'hi':'आप ने बयान किया कि मदीने', 'ur':'آپ نے بیان کیا کہ مدینے'},
    exclude_substrings={'hi':['(तेज़ दौड़ता)'], 'ur':['( تیز دوڑتا )']})

put('2628', 'visitor_observation_and_companion_garment_recollection',
    'The source-defined father of Abd al-Wahid ibn Ayman reports his visit; Aisha then supplies her own garment and lending recollection.',
    'Keep the visitor observation, exact price, actual addressee frame, servant comparison, earlier-period garment and bridal borrowing practice. Distinguish the visitor voice from Aisha recollection within the same encounter family, without labelling either as Prophet speech. The textile-origin/material definition is lexical context, together with the prefatory route; no fuller visitor identity is supplied.',
    start_at={'hi':'उन्होंने कहा कि मैं आइशा', 'ur':'انہوں نے کہا کہ میں عائشہ'},
    exclude_substrings={'hi':['(यमन का एक दबीज़ खुरदुरा कपड़ा)'], 'ur':['( یمن کا ایک دبیز کھردرا کپڑا )']},
    shared_report_family=True,
    components={
        'hi':[comp(None,'आप ने (मुझसे) फ़रमाया','visitor_own_companion_garment_observation','The source-defined father of Abd al-Wahid ibn Ayman supplies his own visit and observation; no expanded identity is asserted.'),
              comp('आप ने (मुझसे) फ़रमाया',None,'companion_garment_comparison_and_lending_recollection','Aisha addresses the visitor and recounts her garment, servant comparison and bridal lending practice.')],
        'ur':[comp(None,'آپ نے ( مجھ سے ) فرمایا','visitor_own_companion_garment_observation','The source-defined father of Abd al-Wahid ibn Ayman supplies his own visit and observation; no expanded identity is asserted.'),
              comp('آپ نے ( مجھ سے ) فرمایا',None,'companion_garment_comparison_and_lending_recollection','Aisha addresses the visitor and recounts her garment, servant comparison and bridal lending practice.')]})

assert len(SPECS) == 30
assert sum(len(s['read_languages']) for s in SPECS.values()) == 63
assert sum(len(s['languages']) for s in SPECS.values()) == 60

# Exact inventory of the retained source apparatus after the full readings.
# These literal declarations validate authored masks; no pattern admits text.
RETAINED_HONORIFICS = {
    '(रदी अल्लाहु अन्हा)', '(रदी अल्लाहु अन्हु)', '(रदी अल्लाहु अन्हुमा)',
    '(रज़ियल्लाहु अन्हा)', '(रज़ियल्लाहु अन्हु)', '(रज़ियल्लाहु अन्हुमा)',
    '(सल्लल्लाहु अलैहि वसल्लम)', '(ra)', '(peace and blessings of Allah be upon him)'
}
RETAINED_NONHONORIFIC = {}
def retain(number, hindi, urdu, reason):
    for language, literal in [('hi',hindi),('ur',urdu)]:
        key=('bukhari:'+number,language,literal)
        assert key not in RETAINED_NONHONORIFIC
        RETAINED_NONHONORIFIC[key]=reason

retain('2567','(खाना पकाने के लिये)','( کھانا پکانے کے لیے )','The cooking-purpose limitation defines which use of fire the household report denies.')
retain('2571','(एक मर्तबा)','( ایک مرتبہ )','The source frames this as an actual occasion.')
retain('2571','(प्याले में कुछ दूध बच गया था इस लिये)','( پیالے میں کچھ دودھ بچ گیا تھا اس لیے )','A finite remaining-drink circumstance supplies the cause of the next request.')
retain('2571','(क्यूंके वोह दायें तरफ था)','( کیونکہ وہ دائیں طرف تھا )','The supplied seat position is the actual stated reason for the recipient choice.')
retain('2571','(आप ने इस बात को दोहराया)','( آپ نے اس بات کو دہرایا )','This supplies the actual repetition predicate and qualifies the preceding threefold count under Anas voice.')
retain('2572',"(शु'बा ने बाद में यक़ीन के साथ)",'( شعبہ نے بعد میں یقین کے ساتھ )','The source explicitly names Shuba and the later certainty that qualifies the earlier alternative gifted parts.')
retain('2573','(रावी को शुबहा है)','( راوی کو شبہ ہے )','This explicit unnamed uncertainty materially qualifies which of the two supplied locations applies; it is separated from Prophet speech.')
retain('2573','(रंज के आसार)','( رنج کے آثار )','The phrase supplies the actual observed reaction object preceding the explanation.')
retain('2574','(रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) की ख़िदमत में)','( رسول اللہ صلی اللہ علیہ وسلم کی خدمت میں )','The source specifies the actual recipient of the gifts.')
retain('2574','(रावी को शक है)','( راوی کو شک ہے )','The source explicitly leaves gifts versus waiting-for-the-day motivation formulation uncertain; neither alternative is silently preferred.')
retain('2575','(इसी)','( اسی )','The same-table connection defines the domain of Ibn Abbas actual conditional argument.')
retain('2577','(जब उन के यहां से पहुँचा तो)','( جب ان کے یہاں سے پہنچا تو )','The transfer-from-her condition limits the recipient-dependent charity/gift statement.')
retain('2580','(बतोर-ए-शिकायत लोगों की इस रौश का)','( بطور شکایت لوگوں کی اس روش کا )','This supplies the actual complaint manner and topic of the co-wives speech.')
retain('2590','(मेरे शौहर)','( میرے شوہر )','The spouse relationship supplies actual participant/property scope in Asma question.')
retain('2590','(अल्लाह की तरफ़ से न)','( اللہ کی طرف سے نہ )','The warning phrase contains the supplied agent and negation; omission changes the statement.')
retain('2596','(नाराज़गी का असर)','( ناراضی کا اثر )','This is the supplied observed reaction object motivating the explanation.')
retain('2597','(नाजाएज़)','( ناجائز )','The unlawful-taking condition limits the object of the oath and threatened consequence.')
retain('2597','(और फ़रमाया)','( اور فرمایا )','The source supplies an actual speech predicate connecting the gesture to the following utterance.')
retain('2597','(आप (सल्लल्लाहु अलैहि वसल्लम) ने यही फ़रमाया)','( آپ صلی اللہ علیہ وسلم نے یہی فرمایا )','The finite predicate binds the actual repeated statement to its threefold count.')
retain('2599','(मुझ से)','( مجھ سے )','The source states the son as actual addressee of the father invitation.')
retain('2599','(मेरे वालिद)','( میرے والد )','The first-person relationship defines the speaker-participant connection in the resumed observation.')
retain('2604','(जाबिर (रज़ियल्लाहु अन्हु) ने कहा)','( جابر رضی اللہ عنہ نے کہا )','This names the reported speaker within Shuba explicitly uncertain wording relay; it is not asserted independently certain.')
retain('2604','(आप (सल्लल्लाहु अलैहि वसल्लम) के हुकुम से बिलाल (रज़ियल्लाहु अन्हु) ने)','( آپ صلی اللہ علیہ وسلم کے حکم سے بلال رضی اللہ عنہ نے )','The source identifies Bilal as weighing under the Prophet instruction, preserving the actual agency distinction.')
retain('2604','(उस पलरे को जिस में सिक्का था)','( اس پلڑے کو جس میں سکہ تھا )','The coin-side pan identifies which object was lowered, defining the direction of the weight detail.')
retain('2604','(ताके मुझे ज़्यादा मिले)','( تاکہ مجھے زیادہ ملے )','The excess-payment purpose limits the weighing account as actually supplied.')
retain('2606','(उसने सख्ती के साथ तक़ाज़ा किया)','( اس نے سختی کے ساتھ تقاضا کیا )','This is a finite creditor action and the actual cause of the companions response.')
retain('2612','(फ़रोख़्त हो रहा)','( فروخت ہو رہا )','The source supplies the finite for-sale circumstance behind the proposed purchase.')
retain('2612','(रेशमी)','( ریشمی )','The later gifted garments material is essential to the reported wearing objection and reply.')
retain('2613','(की आप (सल्लल्लाहु अलैहि वसल्लम) घर में तशरीफ़ नहीं लाये)','( کہ آپ صلی اللہ علیہ وسلم گھر میں تشریف نہیں لائے )','This is an actual finite non-entry clause; the Hindi missing reporting link is explicitly qualified without a borrowed identity.')
retain('2613','(इसलिए वापस चला आया)','( اس لیے واپس چلا آیا )','The source supplies a finite return action and its stated cause.')
retain('2613','(की आराइश-ो-ज़ेबेश)','( کی آرائش و زیبائش )','The adornment restriction limits the object of the otherwise broader world statement.')
retain('2613','(आप (सल्लल्लाहु अलैहि वसल्लम) को जब यह बात पहुंची तो)','( آپ صلی اللہ علیہ وسلم کو جب یہ بات پہنچی تو )','This finite message-reaching circumstance connects the recipient request with the following instruction.')
for number in ['2615','2616']:
    retain(number,'(मर्दों को)','( مردوں کو )','The men restriction defines the actual class covered by the supplied prohibition.')
    retain(number,'(की कितना उम्दा रेशम है)','( کہ کتنا عمدہ ریشم ہے )','The source supplies the content/object of the companions actual reaction; it remains source wording without independent verbatim certification.')
    retain(number,'(तुम्हें इस पर हैरत है)','( تمہیں اس پر حیرت ہے )','The source supplies a finite direct-address bridge to the comparison, preserved as printed rather than certified externally.')
retain('2617','(लेकिन फ़ौरन ही फ़रमाया कि इस में ज़ेहर पड़ा हुआ है)','( لیکن فوراً ہی فرمایا کہ اس میں زہر پڑا ہوا ہے )','This is actual finite immediate speech supplied inside the source parenthesis.')
retain('2617','(और उसने ज़ेहर डालने का इक़रार भी कर लिया)','( اور اس نے زہر ڈالنے کا اقرار بھی کر لیا )','This is a finite confession action supplied in the source, not a lexical gloss.')
retain('2619','(ग़ैर मुस्लिम)','( غیر مسلم )','The recipient restriction qualifies the sale-or-dress purpose; the Hindi speaker link remains separately unknown.')
retain('2620','(मुझसे मुलाक़ात की)','( مجھ سے ملاقات کی )','The source specifies the object of the mother desire and does not supply a conversion or financial intention.')
retain('2627','(दुश्मन के हमले का)','( دشمن کے حملے کا )','The enemy-attack domain limits the reported fear.')
retain('2627','(सहाबा भी साथ थे)','( صحابہ بھی ساتھ تھے )','This is an actual finite accompanying-participant circumstance.')
retain('2628','(मुझसे)','( مجھ سے )','The source identifies the visitor as the actual addressee of Aisha statement.')

RETAINED_MARKER_WORDS = {
    ('bukhari:2615','hi','सूरत'):'This is the internal ending of ख़ूबसूरत, the actual beautiful comparison word; it is not a Surah or verse locator.',
    ('bukhari:2616','hi','सूरत'):'This is the internal ending of ख़ूबसूरत, the actual beautiful comparison word; it is not a Surah or verse locator.'
}
assert len(RETAINED_NONHONORIFIC) == 90

# Transparent final refinement after the separately frozen independent review.
retain('2597','(माल-ए-ज़कात)','( مال زکوٰۃ )','The source has contrasted collected public property with a claimed personal gift; this phrase defines the zakah-property domain of the ensuing taking/oath statement. Its removal could broaden that domain.')
assert len(RETAINED_NONHONORIFIC) == 92
for language in ['hi','ur']:
    SPECS['bukhari:2597'].setdefault('final_field_reason',{})[language] = SPECS['bukhari:2597']['reason'] + ' Final independent refinement: restore the exact zakah-property domain after the preceding contrast, preserving the same source component, speaker and report family. The initial broader-context judgment remains immutable in the source-first notes and archived v1; it is not the final boundary decision.'
BOUNDARY_REFINEMENTS.append({'id':'bukhari:2597','languages':['hi','ur'],
    'independent_findings_sha256':'22f9399f491002af777824cacea81ffd4c4dbc033611d98bfdff59f89818e753',
    'restored_exact_ranges':{'hi':[601,614],'ur':[549,562]},'characters_restored':26,'utf8_bytes_restored':52,
    'refinement':'The source public-property/personal-gift contrast makes the zakah-property phrase a material scope qualification rather than a dispensable lexical repetition. Restore it in the same component, leaving the explicit treasury gloss in context. Initial notes and v1 remain unchanged.'})
