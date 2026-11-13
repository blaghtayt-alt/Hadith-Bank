"""Explicit boundaries after fifty complete own Hindi/Urdu field readings."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECEIPT = json.loads((ROOT / 'complete-source-first-reading-receipt.json').read_bytes())
READINGS = {}
for row in RECEIPT['readings']:
    note = row['source_first_note']
    if row.get('language_specific_note'):
        note += ' ' + row['language_specific_note']
    READINGS.setdefault(row['occurrence_id'].replace('deenhindi-', ''), {})[row['language']] = note
SPECS = {}


def put(key, kind, speaker, reason, **rules):
    SPECS[key] = {'id': key, 'decision': 'register', 'languages': ['hi', 'ur'],
        'read_languages': list(READINGS[key]), 'field_notes': dict(READINGS[key]),
        'report_type': kind, 'speaker': speaker, 'reason': reason, **rules}


def comp(start, end, kind, speaker):
    return {'start_at': start, 'stop_before': end, 'report_type': kind, 'speaker': speaker}


put('bukhari:2313', 'companion_endowment_stipulation_and_administration_report',
    'The supplied Umar written stipulation and subsequent Abdullah ibn Umar administration account have distinct historical roles.',
    'Preserve the written endowment terms separately from the later administrator and gift practice. Neither is represented as direct Prophetic speech; the shortened Hindi chain and source spellings remain literal.',
    shared_report_family=True, components={
      'hi': [comp(None, 'और अब्दुल्लाह बिन उम्र', 'companion_written_endowment_stipulation', 'Umar is the source-named author of the written endowment stipulation.'),
             comp('और अब्दुल्लाह बिन उम्र', None, 'historical_endowment_administration_report', 'The source reporting voice describes Abdullah ibn Umar administering his father’s endowment and sending gifts; no new eyewitness identity is supplied.')],
      'ur': [comp(None, 'اور عبداللہ بن عمر', 'companion_written_endowment_stipulation', 'Umar is the source-named author of the written endowment stipulation.'),
             comp('اور عبداللہ بن عمر', None, 'historical_endowment_administration_report', 'The source reporting voice describes Abdullah ibn Umar administering his father’s endowment and sending gifts; no new eyewitness identity is supplied.')]})

put('bukhari:2316', 'companion_witness_report_with_prophetic_instruction',
    'Uqbah ibn Harith reports the brought-in man, the Prophet’s instruction and his own participation.',
    'Retain the explicitly unresolved Nuayman-or-his-son identity, the actual instruction and witness participation. No missing chain or definitive personal identity is filled.')

put('bukhari:2317', 'companion_report_of_prophetic_sacrifice_arrangements',
    'Aisha reports her own braiding, the Prophet’s actions, sending the animals with her father, and the stated consequence.',
    'Keep the printed destination/purpose and the sending-related causal limitation of the final statement. The father remains as named by relationship in the source; no expanded name is added.')

put('bukhari:2325', 'prophetic_dialogue_and_companion_agreement_report',
    'Abu Hurayrah reports the Ansar proposal, Prophet’s refusal, subsequent work/share offer and acceptance.',
    'Retain the supplied Muhajir recipients and Muhajirin addressee labels as the actual parties to the dialogue. Preserve every source character, including the Hindi field’s mixed-script chain.',
    annotations={'hi': 'This field begins in Latin script and continues in Devanagari. The exact mixed-script source is preserved without transliteration or changing the language label; no part of the chain is reconstructed.'})

put('bukhari:2327', 'companion_historical_land_arrangement_report_with_passive_prohibition',
    'Rafi ibn Khadij reports the actual crop-yield practice, differing losses and an unnamed passive prohibition.',
    'The own field does not identify who imposed the prohibition. Preserve that limitation, the crop-yield rather than land-ownership object, and the absence of gold/silver rent at that time; do not borrow a Prophetic attribution from another entry.',
    annotations={'hi': 'The source says that they were forbidden, without naming the person imposing the prohibition in this own field. The field’s actual historical testimony remains under Rafi’s reported voice.',
                 'ur': 'The passive prohibition has no expressly named imposing speaker in this field. It is not expanded using a similar report elsewhere.'})

put('bukhari:2329', 'prophetic_crop_agreement_report',
    'Ibn Umar reports the Prophet’s actual agreement with the people of Khaybar.',
    'Preserve the source’s half-yield fraction, both crop categories and own parties without adding terms from another occurrence.')

put('bukhari:2332', 'prophetic_prohibition_with_historical_crop_practice',
    'Rafi ibn Khadij reports the crop arrangement and the expressly named Prophet’s prohibition.',
    'Preserve this own field’s explicit attribution, the contrasting loss conditions and its source spelling. The word surat denotes a situation here, not a Quran locator.')

put('bukhari:2334', 'companion_counterfactual_distribution_saying',
    'Umar supplies the actual counterfactual distribution statement and his comparison with the Prophet’s Khaybar distribution.',
    'Keep the future-Muslim condition and comparison as Umar’s actual saying. The appended related-chapters label and topic are compiler apparatus. Preserve Urdu’s duplicated chain exactly rather than silently deduplicating it.',
    stop_before={'hi': '… हदीस मुतालि़क़ा अबवाब:', 'ur': '… حدیث متعلقہ ابواب:'},
    annotations={'ur': 'The original Urdu source repeats an opening transmission sequence. Both printed copies are preserved verbatim; the report body is not silently normalized.'})

put('bukhari:2345', 'companion_historical_testimony_with_precautionary_response',
    'Ibn Umar supplies the first-person historical knowledge; the following source reporting voice describes his fear and precautionary action.',
    'Keep the possibility of an unknown later instruction explicitly uncertain. The subsequent discontinuance is stated as precaution, not proof of a newly established Prophetic prohibition.',
    shared_report_family=True, components={
      'hi': [comp(None, 'फिर उन्हें डर हुआ', 'companion_first_person_historical_testimony', 'Ibn Umar states his own knowledge of the practice in the Prophet’s time.'),
             comp('फिर उन्हें डर हुआ', None, 'reported_companion_uncertainty_and_precaution', 'The reporting voice in the supplied Salim route describes Ibn Umar’s possible-unknown-instruction concern and precaution, without an invented eyewitness identity.')],
      'ur': [comp(None, 'پھر انہیں ڈر ہوا', 'companion_first_person_historical_testimony', 'Ibn Umar states his own knowledge of the practice in the Prophet’s time.'),
             comp('پھر انہیں ڈر ہوا', None, 'reported_companion_uncertainty_and_precaution', 'The reporting voice in the supplied Salim route describes Ibn Umar’s possible-unknown-instruction concern and precaution, without an invented eyewitness identity.')]})

for number in ('2346', '2347'):
    put('bukhari:' + number, 'prophetic_crop_report_and_later_companion_answer',
        'The own transmitted crop practice/prohibition is followed by the narrator’s actual inquiry and Rafi’s monetary-rent answer.',
        'Each occurrence and each language was read separately. Keep the actual reported practice/prohibition and later question/answer in their own voice groups. The appended Layth legal appraisal is explanation context, not a newly registered report. Hindi’s missing initial informant link and literal currency spellings are not repaired from Urdu.',
        stop_before={'hi': 'लैथ ने कहा कि', 'ur': 'لیث نے کہا کہ'},
        shared_report_family=True, components={
          'hi': [comp(None, 'मैंने रफ़ी से पुछा', 'qualified_transmitted_prophetic_prohibition_report', 'The Hindi Hanzala route supplies the practice and expressly names the Prophet’s prohibition, but the initial informant/participant link is missing and remains unspecified.'),
                 comp('मैंने रफ़ी से पुछा', 'लैथ ने कहा कि', 'later_companion_question_and_answer', 'The source’s first-person questioner asks Rafi; Rafi gives the actual monetary-rent answer. No missing expanded name is supplied.')],
          'ur': [comp(None, 'میں نے رافع سے پوچھا', 'prophetic_prohibition_report_via_named_companion_route', 'The complete Urdu route states Rafi’s two unnamed uncles’ historical account and the Prophet’s prohibition.'),
                 comp('میں نے رافع سے پوچھا', 'لیث نے کہا کہ', 'later_companion_question_and_answer', 'The source’s Hanzala inquiry and Rafi’s actual monetary-rent answer remain distinct from the earlier report.') ]},
        annotations={'hi': 'The initial Hindi informant link is shortened/damaged. Rafi’s two uncles and the complete Urdu introduction are not inserted. The source’s dinar/dirham spellings remain unrepaired.',
                     'ur': 'The actual initial route and later question/answer are preserved. The terminal Layth appraisal and gharar explanation remain complete visible source context, without attribution as new Prophetic speech.'})

put('bukhari:2349', 'companion_historical_meal_report_with_named_memory_qualification',
    'Sahl’s historical meal account is interrupted by Abu Hazim’s own explicitly uncertain memory qualification, then resumes.',
    'Retain Abu Hazim’s substantive uncertainty over the fat/grease description in its own non-Prophetic component, in the same report family. Do not present the disputed description as certain or infer an unprinted Prophetic era.',
    shared_report_family=True, components={
      'hi': [comp(None, 'अबू हाज़िम ने कहा', 'companion_historical_meal_account', 'Sahl ibn Sad reports the Friday meal preparation and the group’s happiness.'),
             comp('अबू हाज़िम ने कहा', 'फिर जब हम जुम्मा', 'named_transmitter_material_memory_qualification', 'Abu Hazim explicitly says he does not know whether Sahl supplied this food-description wording.'),
             comp('फिर जब हम जुम्मा', None, 'resumed_companion_historical_meal_account', 'Sahl’s collective account resumes with the meal, happiness and timing.')],
      'ur': [comp(None, 'ابوحازم نے کہا', 'companion_historical_meal_account', 'Sahl ibn Sad reports the Friday meal preparation and the group’s happiness.'),
             comp('ابوحازم نے کہا', 'پھر جب ہم جمعہ', 'named_transmitter_material_memory_qualification', 'Abu Hazim explicitly says he does not know whether Sahl supplied this food-description wording.'),
             comp('پھر جب ہم جمعہ', None, 'resumed_companion_historical_meal_account', 'Sahl’s collective account resumes with the meal, happiness and timing.')]})

put('bukhari:2351', 'prophetic_permission_dialogue_and_distribution_report',
    'Sahl reports the cup, unnamed right-side boy, left-side elders and the Prophet’s permission dialogue and action.',
    'Keep the positional relationships, refusal and actual giving. The boy remains unnamed; Hindi source defects and its shortened chain are not repaired from Urdu.',
    annotations={'hi': 'The source’s unusual cup/left/remaining-drink wording and shortened introduction are preserved literally. No corrected text or boy’s identity is supplied from another source.'})

put('bukhari:2352', 'prophetic_drink_distribution_with_companion_request',
    'Anas reports the source-named milk/water setting, Abu Bakr’s left position, unnamed Bedouin on the right, Umar’s request and the Prophet’s rule/action.',
    'Retain the actual positions, narrated concern and rightward sequence. No identity is supplied for the unnamed Bedouin, and all source honorifics remain literal.')

put('bukhari:2366', 'prophetic_permission_dialogue_and_distribution_report',
    'Sahl reports the youngest unnamed boy on the right, elders on the left and the actual permission exchange.',
    'Preserve this separate occurrence’s own drink wording. Do not fill a milk/water introduction or boy’s name from another entry.')

put('bukhari:2375', 'companion_historical_episode_with_later_transmitter_inquiry',
    'Ali’s supplied camel/Hamzah/Prophet account contains a separate later Ibn Jurayj inquiry, then resumes, followed by an unassigned source chronology qualification.',
    'Keep the actual historical narrative and quoted participants, the later transmitter inquiry and the final pre-prohibition time qualification in one report family. The idhkhir botanical definition and duplicate Ansari-house label are context. Preserve Hindi’s damaged quote/action and inquiry seams with explicit unknown links; do not copy Urdu’s complete wording or harmonize identities.',
    shared_report_family=True,
    exclude_substrings={
        'hi': ['(अरब की एक खुश्बूदार घास जिसे सुनकर वगेरा इस्तेमाल करते थे)', '(अंसारी के)'],
        'ur': ['( عرب کی ایک خوشبودار گھاس جسے سنار وغیرہ استعمال کرتے تھے )', '( انصاری کے )']},
    components={
      'hi': [comp(None, '(इब्न-इ-जुरेज ने बयां किया की)', 'qualified_companion_historical_episode', 'Ali’s source-named narrative includes the supplied lyric/action fragments. The Hindi quote boundary and action-subject connector are damaged and remain explicitly unresolved.'),
             comp('(इब्न-इ-जुरेज ने बयां किया की)', 'काट लिए और उन्हें ले गए.', 'finite_later_transmitter_inquiry_fragment', 'Ibn Jurayj states that he asked Ibn Shihab; the question content is absent in this own Hindi field and is not filled.'),
             comp('काट लिए और उन्हें ले गए.', 'इब्न-इ-शिहाब ने बयां किया कि अली', 'finite_unassigned_action_fragment_in_damaged_inquiry', 'The source supplies the finite cut-and-took predicate, but the respondent, subject and object connection in this damaged seam are not established; none is borrowed from Urdu.'),
             comp('इब्न-इ-शिहाब ने बयां किया कि अली', 'ये शराब की हुरमत से पहले', 'resumed_companion_historical_episode', 'The field expressly resumes Ibn Shihab’s report of Ali’s account, including the source’s abbreviated pain statement and ensuing encounter.'),
             comp('ये शराब की हुरमत से पहले', None, 'source_narrative_chronology_qualification', 'The final source reporting voice supplies the before-prohibition temporal qualification; it is not asserted to be direct Prophetic speech or assigned to an unprinted speaker.')],
      'ur': [comp(None, '( ابن جریج نے بیان کیا کہ )', 'companion_historical_episode', 'Ali’s complete own Urdu narrative supplies the camels, wedding plan, lyric, action and damage.'),
             comp('( ابن جریج نے بیان کیا کہ )', 'ابن شہاب نے بیان کیا کہ علی', 'later_transmitter_question_and_answer', 'Ibn Jurayj asks Ibn Shihab the actually printed hump-meat question; Ibn Shihab supplies the actual answer. Their first-person inquiry is not attributed to Ali.'),
             comp('ابن شہاب نے بیان کیا کہ علی', 'یہ شراب کی حرمت سے پہلے', 'resumed_companion_historical_episode', 'The source expressly resumes Ibn Shihab’s report of Ali’s pain and the subsequent Prophet/Hamzah encounter.'),
             comp('یہ شراب کی حرمت سے پہلے', None, 'source_narrative_chronology_qualification', 'The final source reporting voice supplies the before-prohibition temporal qualification; no unprinted speaker identity is assigned.')]},
    annotations={'hi': 'This source has a shortened chain, a damaged lyric/action seam and an incomplete later inquiry. The fragment “काट लिए और उन्हें ले गए.” has no intact respondent/subject/object link here; those links and the omitted question are not reconstructed from Urdu. All original source words remain available, and the chronology qualification is kept distinct from direct Prophetic speech.',
                 'ur': 'The complete own Urdu lyric, action, later Ibn Jurayj/Ibn Shihab question-and-answer and resumed Ali account are retained under their distinct actual voices. These words are not used to repair the damaged Hindi sibling.'})

put('bukhari:2376', 'prophetic_land_offer_and_patience_instruction',
    'Anas reports the proposed Bahrain land grants, Ansar’s condition for their Muhajir brothers, and the Prophet’s ensuing instruction.',
    'Keep the source-supplied Ansar recipient, other-person object of future preference and afterlife endpoint. They constrain the actual narrative and command rather than merely defining vocabulary.')

put('bukhari:2380', 'prophetic_ariyah_permission_report',
    'Zayd ibn Thabit through Ibn Umar supplies the ariyah permission.',
    'Retain the actual estimate and dry-date exchange wording without expanding the technical term or importing limits from neighboring entries.')

put('bukhari:2381', 'prophetic_transaction_prohibitions_and_exception_report',
    'Jabir supplies the complete prohibition/permission report.',
    'Keep every source transaction category, fruit-readiness condition, own monetary-exchange wording and ariyah exception without harmonizing technical terms.')

put('bukhari:2382', 'prophetic_permission_with_named_material_threshold_uncertainty',
    'Abu Hurayrah supplies the permission report; the final source qualification assigns the threshold doubt to Dawud ibn Husayn.',
    'Both threshold alternatives and the named transmitter uncertainty must remain visible in the same family. The final pointer to an earlier detailed discussion is compiler context. Do not settle the threshold or represent Dawud’s doubt as the Prophet’s own speech.',
    stop_before={'hi': '(बै-ए-अरिय का बयान पीछे', 'ur': '( بیع عریہ کا بیان پیچھے'},
    shared_report_family=True, components={
      'hi': [comp(None, 'इस में शक दाऊद', 'prophetic_permission_with_transmitted_threshold_alternatives', 'Abu Hurayrah reports the permission with the source’s unresolved less-than-five/within-five alternatives.'),
             comp('इस में शक दाऊद', '(बै-ए-अरिय का बयान पीछे', 'named_transmitter_threshold_uncertainty_qualification', 'The source expressly locates the doubt in Dawud ibn Husayn, not in the Prophet.')],
      'ur': [comp(None, 'اس میں شک داؤد', 'prophetic_permission_with_transmitted_threshold_alternatives', 'Abu Hurayrah reports the permission with the source’s unresolved less-than-five/within-five alternatives.'),
             comp('اس میں شک داؤد', '( بیع عریہ کا بیان پیچھے', 'named_transmitter_threshold_uncertainty_qualification', 'The source expressly locates the doubt in Dawud ibn Husayn, not in the Prophet.')]})

put('ibnmajah:2291', 'prophetic_reply_to_unnamed_man',
    'Jabir reports the unnamed man’s complaint and the Prophet’s actual reply.',
    'Preserve the complete supplied question and answer, the unexpanded interlocutor and the original source grade. This is not a new present-day legal ruling or authentication claim.')

put('ibnmajah:2298', 'companion_famine_episode_with_prophetic_response',
    'Abu Bishr introduces the source-named Abbad’s first-person garden/grain account and the Prophet’s response.',
    'Preserve the hunger/ignorance predicates, return order and one-or-half-wasq uncertainty. The Hindi and Urdu patronymic spellings remain literal rather than being harmonized.',
    annotations={'hi': 'The own source prints the Abbad patronymic in its Hindi form. It is preserved without replacing it with the different Urdu rendering.',
                 'ur': 'The own Urdu patronymic and chain remain exact; the Hindi spelling is not used to rewrite them.'})

put('ibnmajah:2303', 'prophetic_dialogue_with_need_conditioned_permission',
    'Abu Hurayrah reports the travel encounter, companions’ intended milking, the Prophet’s analogy and their need-conditioned question/answer.',
    'Keep the actual milking-purpose and in-that-condition parentheses: they state the action and limit the final permission. Only the terminal Urdu footnote glyph is apparatus; the complete source defect in its connective is preserved.',
    exclude_substrings={'ur': ['۱؎']},
    annotations={'ur': 'The malformed connective before the approach to the camel is preserved verbatim. The source’s parenthetic condition and complete consume-without-carrying restriction remain selected; no correction is copied from Hindi.'})

put('ibnmajah:2305', 'prophetic_three_part_livestock_saying',
    'Urwah Bariqi transmits the source’s complete three-part saying.',
    'Preserve all three subjects and the until-Judgment temporal scope, with the original source grade and no additional authentication claim.')

put('ibnmajah:2307', 'prophetic_attributed_household_instruction_and_conditional_saying',
    'Abu Hurayrah transmits the source-stated instruction and appended conditional saying.',
    'Preserve the wealthy/needy distinction, supplied conditional wording and original grade exactly. Registration records the source’s actual attribution and words, not a new authenticity determination or present-day recommendation.')

BOUNDARY_REFINEMENTS = {
    'bukhari:2375:hi': 'Exact boundary authoring preserves the frozen first-pass description but separates the finite Ibn Jurayj inquiry event from the following cut-and-took predicate. The Hindi field lacks the question, respondent and object link in that seam. Separate qualified components make those gaps visible; no text or identity is filled from Urdu.',
    'bukhari:2382:hi': 'The named Dawud uncertainty is kept as its own transmitter-qualified component after the report’s two actual threshold alternatives. The trailing earlier-discussion pointer alone remains context.',
    'bukhari:2382:ur': 'The named Dawud uncertainty is kept as its own transmitter-qualified component after the report’s two actual threshold alternatives. The trailing earlier-discussion pointer alone remains context.'
}

RETAINED_HONORIFICS = {
    '(रज़ियल्लाहु अन्हा)', '(रज़ियल्लाहु अन्हु)', '(रज़ियल्लाहु अन्हुमा)', '(रज़ियल्लाहु अन्हुम)',
    '(रदी अल्लाहु अन्हु)', '(रदी अल्लाहु अन्हुम)', '(रदी अल्लाहु अन्हुमा)',
    '(रज़ि अल्लाहू अन्हु)', '(रज़ि अल्लाहु अन्हु)', '(सल्लल्लाहु अलैहि वसल्लम)', '( رضی اللہ عنہ )',
}
RETAINED_NONHONORIFIC = {}


def keep(key, language, literal, reason):
    RETAINED_NONHONORIFIC[(key, language, literal)] = reason


for language, purpose, cause in [('hi', '(मक्का में कुर्बानी के लिए)', '(इस भेजने की वजह से)'),
                                ('ur', '( مکہ میں قربانی کے لیے )', '( اس بھیجنے کی وجہ سے )')]:
    keep('bukhari:2317', language, purpose, 'The actual destination and sacrifice purpose of sending the animals are supplied here.')
    keep('bukhari:2317', language, cause, 'This limits the final statement to the consequence of sending the animals; omission broadens it.')
for language, recipient, addressee in [('hi', '(मुहाजिर)', '(मुहाजिरीन से)'),
                                      ('ur', '( مہاجر )', '( مہاجرین سے )')]:
    keep('bukhari:2325', language, recipient, 'The parenthesis supplies the actual proposed recipients in the dialogue.')
    keep('bukhari:2325', language, addressee, 'The parenthesis supplies the actual addressee of the work/share offer.')
for language, literal in [('hi', '(की पैदावार)'), ('ur', '( کی پیداوار )')]:
    keep('bukhari:2327', language, literal, 'This makes the object the crop yield rather than acquisition of the land itself.')
for language, literal in [('hi', '(एहतियातन)'), ('ur', '( احتیاطاً )')]:
    keep('bukhari:2345', language, literal, 'The source states the action was precautionary, not an asserted new prohibition.')
for language, literal in [('hi', '(इस बात की)'), ('ur', '( اس بات کی )')]:
    keep('bukhari:2349', language, literal, 'This is the coherent source narrative linker into the cause of the group’s happiness.')
for language, intention, marriage, label in [
    ('hi', '(ख्याल ये था की)', '(जिन से मैं निकाह करने वाला था उन)', '(इब्न-इ-जुरेज ने बयां किया की)'),
    ('ur', '( خیال یہ تھا کہ )', '( جن سے میں نکاح کرنے والا تھا ان )', '( ابن جریج نے بیان کیا کہ )')]:
    keep('bukhari:2375', language, intention, 'The source’s intention bridge qualifies the prospective funding plan.')
    keep('bukhari:2375', language, marriage, 'The first-person forthcoming-marriage relation supplies actual narrative timing and relationship.')
    keep('bukhari:2375', language, label, 'The printed speaker switch is necessary to distinguish the later transmitter inquiry from Ali’s narrative.')
keep('bukhari:2375', 'ur', '( بڑھ )', 'This is the actual finite advance imperative completing the quoted lyric, not a dictionary definition.')
for language, recipient, others, endpoint in [
    ('hi', '(अनसार को)', '(दूसरे लोगों को)', '(आख़िरत में आ कर)'),
    ('ur', '( انصار کو )', '( دوسرے لوگوں کو )', '( آخرت میں آ کر )')]:
    keep('bukhari:2376', language, recipient, 'This supplies the actual recipients of the proposed land grants.')
    keep('bukhari:2376', language, others, 'This supplies the object of future preference, preserving the stated comparison.')
    keep('bukhari:2376', language, endpoint, 'This is the supplied endpoint of the patience instruction.')
for language, literal in [('hi', '(ये कहा कि)'), ('ur', '( یہ کہا کہ )')]:
    keep('bukhari:2382', language, literal, 'The source explicitly introduces the alternative threshold wording; the uncertainty remains visible.')
for language, purpose, condition in [('hi', '(का दूध दोहने के लिए)', '(ऐसी हालत में)'),
                                    ('ur', '( کا دودھ دوہنے کے لیے )', '( ایسی حالت میں )')]:
    keep('ibnmajah:2303', language, purpose, 'The source supplies the action-purpose of the companions’ approach to the camel.')
    keep('ibnmajah:2303', language, condition, 'The final permission is limited to the need condition actually asked about; removing this broadens it.')

RETAINED_MARKER_WORDS = {
    ('bukhari:2332', 'hi', 'सूरत'): 'This ordinary word means the arrangement/situation in the actual historical account; it is not a surah label or verse locator.'
}
