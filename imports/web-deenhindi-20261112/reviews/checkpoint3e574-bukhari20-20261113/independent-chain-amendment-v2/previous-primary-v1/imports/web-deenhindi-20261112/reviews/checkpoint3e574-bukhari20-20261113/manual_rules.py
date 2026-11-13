"""Exact boundaries authored after forty complete own Hindi/Urdu readings."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECEIPT = json.loads((ROOT / 'complete-source-first-reading-receipt.json').read_bytes())
READINGS = {}
for row in RECEIPT['fields']:
    READINGS.setdefault(row['occurrence_id'].removeprefix('deenhindi-'), {})[row['language']] = row['source_first_note']
SPECS = {}


def put(number, kind, speaker, reason, **rules):
    key = 'bukhari:' + number
    assert key not in SPECS
    SPECS[key] = {'id': key, 'decision': 'register', 'languages': ['hi', 'ur'],
        'read_languages': list(READINGS[key]), 'field_notes': dict(READINGS[key]),
        'report_type': kind, 'speaker': speaker, 'reason': reason, **rules}


def comp(start, end, kind, speaker):
    return {'start_at': start, 'stop_before': end, 'report_type': kind, 'speaker': speaker}


put('2469', 'companion_oath_upper_room_and_return_report',
    'Anas transmits the upper-room account, Umar question and the Prophet replies and return.',
    'Preserve the sprain, actual oath, divorce question and denial, one-month interval and twenty-nine-day return. The finite moon-appearance parenthesis supplies the actual stated cause of return. The earlier-year chronology and Eela event labels remain compiler context; no date or chronological reconciliation is supplied.',
    exclude_substrings={'hi': ['(Eela ke waqea se pehle 5 Hijri mein)', '(Eela ke mauqe par)'],
                        'ur': ['( ایلاء کے واقعہ سے پہلے 5 ھ میں )', '( ایلاء کے موقع پر )']})

put('2473', 'prophetic_disputed_route_measure_decision',
    'Ikrimah reports hearing Abu Hurayrah transmit the Prophet route-dispute decision.',
    'Retain the actual disputed route and its land-object scope, with the exact seven-hand measure. Do not convert units or supply another route, legal case or modern ruling.')

put('2474', 'prophetic_prohibition_report',
    'Adi reports hearing the source-named Abdullah ibn Yazeed Ansari transmit the prohibition.',
    'The own field supplies the prohibition of plunder and mutilation. Preserve its supplied route and body, while the appended grandfather relationship is transmitter biography and remains context.',
    exclude_substrings={'hi': ['jo Adi bin Sabit ke nana thay.'],
                        'ur': ['جو عدی بن ثابت کے نانا تھے۔']})

put('2479', 'companion_picture_curtain_and_cushion_report',
    'Aisha reports the picture curtain, the Prophet removal, her own cushion making and his later sitting.',
    'Retain the seeing trigger and the explicit Aisha first-person voice transition as actual narrative framing. All supplied actions and the two cushions remain; no additional image or material description is supplied.')

put('2483', 'expedition_account_interrupted_by_transmitter_question',
    'The expedition participant account is interrupted by the explicitly named Wahb question to Jabir and Jabir answer.',
    'Preserve the three-hundred-person expedition, collective remaining-provision condition, date ration, actual Wahb/Jabir dialogue and resumed fish/ribs account as ordered parts of one family. The Hindi opening route is damaged and lacks the full participant name; do not fill it from Urdu. Only the calendar parenthesis and redundant physical-comparison gloss are context.',
    shared_report_family=True,
    exclude_substrings={'hi': ['(रजब ७ हिजरी में)', '(अपने जिस्म में)'],
                        'ur': ['( رجب 7 ھ میں )', '( اپنے جسم میں )']},
    components={
        'hi': [
            comp(None, 'मैं (वहब बिन कइसन)', 'qualified_expedition_participant_report',
                 'The own Hindi first-person expedition participant; its opening route is damaged and the full name is not supplied there.'),
            comp('मैं (वहब बिन कइसन)', 'उन्हों ने बयां किया कि आखिर', 'named_transmitter_question_and_companion_answer',
                 'The source explicitly identifies Wahb ibn Kaysan asking Jabir, followed by Jabir answer about the date ration.'),
            comp('उन्हों ने बयां किया कि आखिर', None, 'companion_resumed_expedition_account',
                 'The Jabir response continues with the sea, fish and ribs account; all supplied Hindi defects remain literal.')],
        'ur': [
            comp(None, 'میں ( وہب بن کیسان )', 'companion_expedition_participant_report',
                 'Jabir ibn Abdullah, explicitly supplied by the own Urdu route, recounts the expedition and rations.'),
            comp('میں ( وہب بن کیسان )', 'انہوں نے بیان کیا کہ آخر', 'named_transmitter_question_and_companion_answer',
                 'The source explicitly identifies Wahb ibn Kaysan asking Jabir, followed by Jabir answer about the date ration.'),
            comp('انہوں نے بیان کیا کہ آخر', None, 'companion_resumed_expedition_account',
                 'Jabir resumes the sea, fish, eighteen nights and ribs account.')]},
    annotations={'hi': 'The opening Hindi route prints a broken ibn-Abdullah fragment and omits preceding links supplied in Urdu. No missing narrator words are inserted; the later Wahb/Jabir names are independently present. The fish-action spelling remains exactly as printed.',
                 'ur': 'The Urdu field supplies its own complete Jabir route. It is not used to repair the separate Hindi introduction.'})

put('2485', 'companion_collective_prayer_camel_and_food_report',
    'Abul Najashi reports hearing Rafi ibn Khadij describe the collective prayer and camel-meat preparation.',
    'Retain the actual asr prayer, slaughter, ten shares and cooked meat before sunset as printed, without filling any omitted circumstance.')

put('2489', 'prophetic_shared_food_prohibition_with_permission_exception',
    'Abdullah ibn Umar reports the Prophet instruction through the source Jabla route.',
    'Retain the shared-table setting, two dates together and companions-permission exception. The setting qualifies the actual domain of this supplied instruction; no wider prohibition is inferred.')

put('2494', 'companion_exegetical_dialogue_and_revelation_context',
    'Urwah asks Aisha; Aisha supplies the orphan-guardian explanation and later revelation interpretation.',
    'The actual Quran quotations and translations and Aisha bounded explanations are substantive supplied sayings. Preserve the complete-mahr and fairness conditions, permitted consequence and later-question scope. The second-route label, Surah locator and illustrative guardian definition remain apparatus. Ordered Aisha/Urwah relaying clauses stay in one explanatory dialogue family, without relabelling them Prophet speech.',
    shared_report_family=True,
    exclude_substrings={'hi': ['(doosri sanad)', '(Surah Nisa mein)', '(muhafiz rishtedar jaise chachera bhai, phuphi zaad ya mamu zaad bhai)'],
                        'ur': ['(دوسری سند)', '( سورۃ نساء میں )', '( محافظ رشتہ دار جیسے چچیرا بھائی، پھوپھی زاد یا ماموں زاد بھائی )']},
    components={
        'hi': [
            comp(None, 'Urwah bin Zubair ne kaha ke Aishah', 'companion_exegetical_question_and_answer',
                 'Urwah asks Aisha about the supplied verse; Aisha gives her own conditional guardian/orphan explanation.'),
            comp('Urwah bin Zubair ne kaha ke Aishah', 'Sayyidah Aishah (Radi Allahu Anha) ne kaha yeh', 'companion_revelation_context_relayed_by_named_transmitter',
                 'Urwah relays Aisha account of the subsequent question, revelation and connection to the first verse.'),
            comp('Sayyidah Aishah (Radi Allahu Anha) ne kaha yeh', None, 'companion_exegetical_saying',
                 'Aisha explicitly gives the final supplied interpretation and full-mahr condition.')],
        'ur': [
            comp(None, 'عروہ بن زبیر نے کہا کہ عائشہ', 'companion_exegetical_question_and_answer',
                 'Urwah asks Aisha about the supplied verse; Aisha gives her own conditional guardian/orphan explanation.'),
            comp('عروہ بن زبیر نے کہا کہ عائشہ', 'سیدہ عائشہ رضی اللہ عنہا نے کہا یہ', 'companion_revelation_context_relayed_by_named_transmitter',
                 'Urwah relays Aisha account of the subsequent question, revelation and connection to the first verse.'),
            comp('سیدہ عائشہ رضی اللہ عنہا نے کہا یہ', None, 'companion_exegetical_saying',
                 'Aisha explicitly gives the final supplied interpretation and full-mahr condition.')]})

put('2495', 'companion_report_of_prophetic_undivided_property_decision',
    'Jabir reports the source-stated pre-emption decision through the route printed with Zubairi.',
    'Preserve the actual undivided-property limitation and termination when boundaries and routes separate. The parenthetic list of property examples is a lexical explanation. The printed Zubairi name is not corrected from another occurrence.',
    exclude_substrings={'hi': ['(zameen jaidad waghera)'], 'ur': ['( زمین جائیداد وغیرہ )']},
    annotations={'hi': 'The source route prints Zubairi; no external or adjacent identity correction is made.',
                 'ur': 'The source prints زبیری. It is preserved independently of the different name in occurrence2496.'})

put('2496', 'companion_report_of_prophetic_undivided_property_decision',
    'Jabir reports the source-stated decision through the own route printed with Zuhri.',
    'This independently read occurrence retains its full undivided-partnership and boundary/route conditions. Its identity and exact different source route remain distinct from2495.')

for number in ['2497', '2498']:
    put(number, 'two_transaction_accounts_with_prophetic_reply',
        'Sulaiman asks Abu Minhal about the latter transaction; Baraa then recounts his own earlier transaction with Zayd and Prophet reply.',
        'Both full languages of this occurrence were actually read. Preserve the present Abu Minhal encounter and separate earlier Baraa/Zayd transaction as two report families, including all immediate-versus-deferred conditions. The repeated cash synonyms explain the already explicit hand-to-hand term and remain context. Identical wording does not merge the two provider IDs.',
        exclude_substrings={'hi': ['(naqd)'], 'ur': ['(نقد)']},
        components={
            'hi': [comp(None, 'Unhon ne jawab diya:', 'transmitted_transaction_and_consultation_report',
                        'Sulaiman questions Abu Minhal, who recounts his own transaction, companion and consultation with Baraa.'),
                   comp('Unhon ne jawab diya:', None, 'companion_prior_transaction_and_prophetic_reply',
                        'Baraa recounts his separate earlier transaction with Zayd ibn Arqam and their actual Prophet question and response.')],
            'ur': [comp(None, 'انہوں نے جواب دیا:', 'transmitted_transaction_and_consultation_report',
                        'Sulaiman questions Abu Minhal, who recounts his own transaction, companion and consultation with Baraa.'),
                   comp('انہوں نے جواب دیا:', None, 'companion_prior_transaction_and_prophetic_reply',
                        'Baraa recounts his separate earlier transaction with Zayd ibn Arqam and their actual Prophet question and response.')]})

put('2499', 'transmitted_prophetic_land_work_and_yield_condition',
    'Nafi transmits from the source-named Abdullah; the own field supplies no further Abdullah identity.',
    'Keep the Khaybar land recipients, their work/sowing/ploughing obligations and half-yield condition. Do not expand Abdullah from a familiar parallel or add a different contract.',
    annotations={'hi': 'The own source names Abdullah only; no Ibn Umar or other missing identity is supplied.',
                 'ur': 'The source Abdullah remains unexpanded; all participant and yield conditions remain exact.'})

for number in ['2505', '2506']:
    put(number, 'companion_pilgrimage_account_with_multiple_supplied_voices',
        'The own source names Ibn Abbas, with Jabir objection, Prophet sermon, Suraqah question and Ali arrival as ordered narrated parts.',
        'Preserve this independently read occurrence and its full actual pilgrimage sequence. Split the supplied voices within one report family. The Hindi conditional join remains visibly damaged and its duration reply lacks meaningful supplied duration; keep that exact broken answer in context without importing Urdu forever. Urdu supplies its own full conditional and answer; only its hady lexical gloss is context.',
        shared_report_family=True,
        exclude_substrings={'ur': ['(قربانی)']},
        components={
            'hi': [
                comp(None, 'जाबिर (रज़ियल्लाहु अन्हु) ने ता', 'companion_pilgrimage_arrival_and_instruction_report',
                     'Ibn Abbas reports the arrival, collective ihram instruction and ensuing talk.'),
                comp('जाबिर (रज़ियल्लाहु अन्हु) ने ता', 'जब यह खबर नबी करीम', 'companion_supplied_objection_and_gesture',
                     'Jabir actual objection and gesture, as reported inside the source-named Ibn Abbas account.'),
                comp('जब यह खबर नबी करीम', 'इस पर सुरका बिन मालिक', 'prophetic_sermon_with_damaged_conditional_wording',
                     'The Prophet sermon as supplied in Hindi, with its broken conditional join retained literally and visibly qualified.'),
                comp('इस पर सुरका बिन मालिक', "आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया: 'नहीं के लिए है.'", 'companion_question_with_missing_meaningful_answer',
                     'Suraqah actual supplied duration question; the following damaged reply is retained in source context without repair.'),
                comp('इसी दौरान अली बिन आबि तालिब', None, 'companion_arrival_and_prophetic_ihram_instruction_report',
                     'The source reports Ali arrival, talbiyah, instruction to retain ihram and shared hady.')],
            'ur': [
                comp(None, 'جابر رضی اللہ عنہ نے تعجب', 'companion_pilgrimage_arrival_and_instruction_report',
                     'Ibn Abbas reports the arrival, collective ihram instruction and ensuing talk.'),
                comp('جابر رضی اللہ عنہ نے تعجب', 'جب یہ خبر نبی کریم', 'companion_supplied_objection_and_gesture',
                     'Jabir actual objection and gesture, as reported inside the source-named Ibn Abbas account.'),
                comp('جب یہ خبر نبی کریم', 'اس پر سراقہ بن مالک', 'prophetic_sermon_and_conditional_statement',
                     'The Prophet sermon and full condition as independently supplied in Urdu.'),
                comp('اس پر سراقہ بن مالک', 'اسی دوران علی بن ابی طالب', 'companion_question_and_prophetic_duration_reply',
                     'Suraqah question and the Urdu source own explicit forever reply, without supplying it to Hindi.'),
                comp('اسی دوران علی بن ابی طالب', None, 'companion_arrival_and_prophetic_ihram_instruction_report',
                     'The source reports Ali arrival, talbiyah, instruction to retain ihram and shared hady.')]},
        annotations={'hi': "The own Hindi condition omits connecting wording and its later reply is literally 'नहीं के लिए है.'; the full broken reply stays in source context. No duration or missing phrase is copied from Urdu. All other original Hindi words remain literal.",
                     'ur': 'This own Urdu field independently supplies the conditional wording and forever answer. These are not used to fill the separate Hindi defects.'})

put('2508', 'companion_multiple_supplied_household_reports',
    'Anas transmits the pledge, his own food visit and his hearing of the Prophet household statement; the final nine-house clause is reporting voice.',
    'Keep all finite clauses in order while distinguishing the pledge, the separately introduced one-day visit and the hearing account as three report families. The closing third-person nine-house circumstance shares the hearing family but is not presented as the Prophet first-person assertion. No common date or unprinted transaction counterparty is invented.',
    source_report_family_by_component={'report-4': 'report-3'},
    components={
        'hi': [comp(None, 'Ek din main khud', 'companion_report_of_prophetic_pledge', 'Anas transmits the armor-for-barley pledge.'),
               comp('Ek din main khud', 'Main ne khud aap', 'companion_own_food_visit_report', 'Anas reports his own separately introduced one-day food visit.'),
               comp('Main ne khud aap', 'halankeh aap ke nau ghar the', 'companion_own_hearing_of_prophetic_household_statement', 'Anas says he personally heard the Prophet household quantity statement.'),
               comp('halankeh aap ke nau ghar the', None, 'qualified_reporting_voice_household_circumstance', 'The source reporting voice adds nine houses; the third-person clause is not labelled Prophet speech.')],
        'ur': [comp(None, 'ایک دن میں خود', 'companion_report_of_prophetic_pledge', 'Anas transmits the armor-for-barley pledge.'),
               comp('ایک دن میں خود', 'میں نے خود آپ', 'companion_own_food_visit_report', 'Anas reports his own separately introduced one-day food visit.'),
               comp('میں نے خود آپ', 'حالانکہ آپ کے نو گھر تھے', 'companion_own_hearing_of_prophetic_household_statement', 'Anas says he personally heard the Prophet household quantity statement.'),
               comp('حالانکہ آپ کے نو گھر تھے', None, 'qualified_reporting_voice_household_circumstance', 'The source reporting voice adds nine houses; the third-person clause is not labelled Prophet speech.')]})

put('2513', 'companion_report_of_prophetic_deferred_purchase_and_pledge',
    'Aisha reports the grain purchase from an unnamed Jewish counterparty and armor pledge.',
    'Preserve the delayed-term purchase and pledge exactly. Do not infer a duration, amount or personal identity absent from this own field.')

put('2519', 'companion_report_of_prophetic_eclipse_instruction',
    'Asma bint Abi Bakr reports the explicitly attributed Prophet instruction.',
    'Retain the eclipse timing and actual slave-release instruction. The final parallel-route appendix supplies no report body and remains context; source chain spellings are not repaired.',
    stop_before={'hi': ' मूसा के साथ इस हदीस को', 'ur': ' موسیٰ کے ساتھ اس حدیث کو'})

put('2520', 'companion_received_instruction_with_unnamed_issuer',
    'Asma bint Abi Bakr reports that we were ordered; the issuer is not explicitly named in either own field.',
    'This source contains a finite collective received-instruction report with eclipse timing. Preserve its passive wording and leave the issuing voice unspecified; do not borrow explicit Prophet attribution from2519.',
    annotations={'hi': 'The own field uses a passive instruction and does not name its issuer. Its source-bound Companion report remains qualified.',
                 'ur': 'The passive instruction is retained without importing an issuing identity from another occurrence.'})

put('2532', 'interrupted_transmitted_journey_and_companion_declaration',
    'Qais transmits the Abu Hurayrah journey fragment and the later actual Abu Hurayrah declaration; Qais is not asserted to be an eyewitness.',
    'Retain the finite Islam-intent journey, slave separation and separately supplied declaration. The same-hadith pointer and in-it-is transition are transmission context. Preserve the actual witness address and for-Allah wording, without adding freedom, a reunion or a missing explicit addressee name.',
    shared_report_family=True,
    components={
        'hi': [comp(None, '(फिर यही हदीस बयान की)', 'transmitted_companion_journey_fragment', 'Qais transmits the source-supplied Abu Hurayrah journey and separation fragment.'),
               comp('और अबू हुरैरा (रज़ियल्लाहु अन्हु) ने कहा था', None, 'companion_declaration_with_qualified_addressee', 'Abu Hurayrah actual declaration addresses a pronoun figure with the Prophetic honorific, without an added explicit name or missing action.')],
        'ur': [comp(None, '( پھر یہی حدیث بیان کی )', 'transmitted_companion_journey_fragment', 'Qais transmits the source-supplied Abu Hurayrah journey and separation fragment.'),
               comp('اور ابوہریرہ رضی اللہ عنہ نے کہا تھا', None, 'companion_declaration_with_qualified_addressee', 'Abu Hurayrah actual declaration addresses a pronoun figure with the Prophetic honorific, without an added explicit name or missing action.')]},
    annotations={'hi': 'The source explicitly omits intervening report content. The later actual declaration is retained without supplying an absent reunion or translating its for-Allah wording into an unprinted act.',
                 'ur': 'The omission remains visible and all actual supplied fragments stay exact; no missing event or explicit addressee identity is invented.'})

# These are individually observed scripts, not inferred language replacements.
for number in ['2469', '2473', '2474', '2479', '2485', '2489', '2494',
               '2495', '2496', '2497', '2498', '2499', '2508']:
    SPECS['bukhari:' + number]['observed_scripts'] = {'hi': 'Latn'}

BOUNDARY_REFINEMENTS = {
    'bukhari:2483:hi': 'The damaged opening participant is explicitly qualified, while the own later Wahb/Jabir exchange is separately attributed; no Urdu route is supplied to Hindi.',
    'bukhari:2505:hi': 'The full broken duration-answer attribution and literal reply stay together in context; the preceding complete Suraqah question and following Ali report remain separately selected.',
    'bukhari:2506:hi': 'This duplicate wording was independently read; its complete broken duration-answer clause remains source context under the same source-bound rationale.',
    'bukhari:2508:hi': 'The separately introduced pledge, one-day visit and own hearing are distinct source report families. The final reporting-voice household clause belongs with the hearing family.',
    'bukhari:2508:ur': 'The finite clauses remain exact, with no invented common date; the final third-person household statement is not converted into Prophet first-person speech.',
}

RETAINED_HONORIFICS = {
    '(Radi Allahu Anhu)', '(Radi Allahu Anha)', '(Radi Allahu Anhuma)',
    '(Sallallahu Alaihi Wasallam)', '(रज़ियल्लाहु अन्हा)', '(रज़ियल्लाहु अन्हु)',
    '(रज़ियल्लाहु अन्हुमा)', '(सल्लल्लाहु अलैहि वसल्लम)',
}
RETAINED_NONHONORIFIC = {}


def keep(number, language, literal, reason):
    RETAINED_NONHONORIFIC[('bukhari:' + number, language, literal)] = reason


for lang, literal in [('hi', '(aur untees tareekh ko hi chand ho gaya tha)'), ('ur', '( اور انتیس تاریخ کو ہی چاند ہو گیا تھا )')]:
    keep('2469', lang, literal, 'This finite moon-appearance event supplies the stated causal condition for the subsequent return.')
for lang, literal in [('hi', '(ki zameen)'), ('ur', '( کی زمین )')]:
    keep('2473', lang, literal, 'This supplies the disputed land-object scope of the route-measure decision.')
for lang, seeing, voice in [('hi', '(jab dekha toh)', '(Ayesha Radi Allahu Anha ne bayan kiya ke)'), ('ur', '( جب دیکھا تو )', '( عائشہ رضی اللہ عنہا نے بیان کیا کہ )')]:
    keep('2479', lang, seeing, 'This finite perception clause supplies the trigger for the removal action.')
    keep('2479', lang, voice, 'This marks Aisha own first-person continuation after the earlier introduction.')
for lang, provision, voice in [('hi', '(जो कुछ भी बाक़ी रह गए हों)', '(वहब बिन कइसन)'), ('ur', '( جو کچھ بھی باقی رہ گئے ہوں )', '( وہب بن کیسان )')]:
    keep('2483', lang, provision, 'The remaining-provision condition limits what each soldier is instructed to collect.')
    keep('2483', lang, voice, 'This is the own source explicit switch from the expedition first person to Wahb question; it prevents merging two speakers.')
for lang, literal in [('hi', '(dastarkhwan par)'), ('ur', '( دستر خوان پر )')]:
    keep('2489', lang, literal, 'The shared-table setting limits the domain of the actual food instruction.')
for lang, permission, scope in [('hi', '(toh is soorat mein nikah karne ki ijazat hai)', '(aisi ladkiyon se nikah ki ijazat ke bare mein)'), ('ur', '( تو اس صورت میں نکاح کرنے کی اجازت ہے )', '( ایسی لڑکیوں سے نکاح کی اجازت کے بارے میں )')]:
    keep('2494', lang, permission, 'The finite permission is the stated consequence of the preceding fairness and full-mahr condition.')
    keep('2494', lang, scope, 'This supplies the subject and scope of the actual later question in Aisha account.')
RETAINED_MARKER_WORDS = {}
assert len(SPECS) == 20
