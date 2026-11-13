"""Explicit own-field boundaries after the frozen 58 complete source readings."""
from manual_source_first_readings import NOTES

READINGS = {}


def field(number, language, report_type=None, speaker=None, cuts=(), segments=None,
          exact=None, context_all=False, retained=()):
    key = 'muslim:' + number
    assert ('deenhindi-' + key, language) in NOTES
    assert language not in READINGS.setdefault(key, {})
    READINGS[key][language] = {
        'note': NOTES['deenhindi-' + key, language], 'type': report_type,
        'speaker': speaker, 'context': list(cuts), 'context_all': context_all,
        'source_report_family_id': key + ':source-numbered-report',
        'retained_meaningful_structures': list(retained)}
    if segments is not None:
        READINGS[key][language]['segments'] = segments
    if exact is not None:
        READINGS[key][language]['exact_selections'] = exact


def part(start=None, end=None, component='report-1', report_type=None, speaker=None):
    result = {'start': start, 'end': end, 'id': component}
    if report_type:
        result['type'] = report_type
    if speaker:
        result['speaker'] = speaker
    return result


for number in ('2484', '2512', '2519', '2540', '2551'):
    for language in ('hi', 'ur', 'ar', 'en', 'ur-Latn'):
        field(number, language, context_all=True)

field('2485', 'hi', 'companion_report_of_prophetic_gift_reply',
      'Anas ibn Malik reports Barirah’s gift and the explicitly introduced Prophet’s charity-for-her/gift-for-us reply. The source’s printed names, spellings and gift vocabulary remain exact.')
field('2485', 'ur', 'companion_report_of_prophetic_gift_reply',
      'Anas ibn Malik reports Barirah’s gift and the Prophet’s actual reply. The separate biographical identification of Barirah as Aisha’s freed servant is context, without altering the reported event.',
      cuts=['( حضرت عائشہ رضی اللہ تعالیٰ عنہا کی آزاد کردہ کنیز )'])

field('2486', 'hi', 'companion_report_of_prophetic_gift_reply',
      'Aswad’s source route names Aisha with the source’s defective ऐषः spelling. The cow-meat offering, its stated charity origin and the Prophet’s actual reply remain literal; no name or wording is corrected.')
field('2486', 'ur', 'companion_report_of_prophetic_gift_reply',
      'Aswad transmits Aisha’s account of the cow meat, the supplied charity information and the explicitly introduced Prophet’s gift reply.')

field('2487', 'hi', 'companion_report_of_prophetic_charity_gift_instruction',
      'The supplied Hisham/Abdur Rahman/father route reaches Aisha’s announced three decisions, of which this field supplies the charity/gift decision only. The full eating instruction and its manner remain; the father’s inserted genealogy is context.',
      cuts=['(क़ासिम बिन मुहम्मद बिन अबू बक्र)'])
field('2487', 'ur', 'companion_report_of_prophetic_charity_gift_instruction',
      'Aisha’s source report announces three legal decisions but supplies only the actual charity/gift account and eating instruction here. The legal domain and without-hesitation manner remain supplied scope; only the route genealogy apposition is context.',
      cuts=['( قاسم بن محمد بن ابی بکر )'],
      retained=['( شرعی )', '( بلا ہچکچاہٹ )'])

field('2490', 'hi', 'companion_report_of_prophetic_food_question_and_reply',
      'Umm Atiyyah reports the goat and portion sent to Aisha, the Messenger’s actual food question and its answer. The food-purpose and charity nature remain meaningful scope; the redundant Nasibah identity apposition remains context.',
      cuts=['(उम्मे अतीय्यह रदी अल्लाहु अन्हा)'],
      retained=['(खाने के लिए)', '(सदक़े की)'])
field('2490', 'ur', 'companion_report_of_prophetic_food_question_and_reply',
      'Umm Atiyyah’s own account supplies the goat, Aisha exchange and Messenger reply. Only the unclosed inserted identity label is context; its following نے اس and the charity qualifier stay in the actual sentence, without a fabricated closing delimiter.',
      cuts=['( ام عطیہ رضی اللہ تعالیٰ عنہا'],
      retained=['( کھا نے کے لیے )', '( صدقے کی )'])

field('2493', 'hi', 'qualified_transmitted_supplication_fragment',
      'The Ibn Idris/Shubah comparison expressly supplies this actual mercy imperative. Its ultimate speaker and the pronoun’s referents are absent here and remain unknown; the substituted-name comparison is context.',
      exact=[{'text': 'उन सब पर रहमत भेज', 'id': 'actual-supplication-fragment'}])
field('2493', 'ur', 'qualified_transmitted_supplication_fragment',
      'The source’s Ibn Idris/Shubah wording comparison actually transmits this mercy imperative. No Prophetic attribution or identification of all-of-them is supplied from the omitted report.',
      exact=[{'text': 'ان سب پر رحمت بھیج', 'id': 'actual-supplication-fragment'}])

field('2500', 'hi', 'qualified_transmitted_conditional_instruction_fragment',
      'The source prints an actual cloud condition and thirty-day counting instruction after the repeated route. Its ultimate speaker and the month antecedent are not named here; the preceding chain and following Abu Usamah comparison remain context.',
      exact=[{'text': 'अगर तुम पर बादल छा जायें तो उसके तीस दिन शुमार करो,', 'id': 'actual-cloud-counting-fragment'}])
field('2500', 'ur', 'qualified_transmitted_conditional_instruction_fragment',
      'The complete supplied cloud condition and thirty-day instruction are transmitted wording. The unmarked ultimate voice and missing month antecedent remain qualified; route and comparison apparatus stay context.',
      exact=[{'text': 'اگر تم پر بادل چھاجائیں تو اس کے تیس دن شمار کرو ۔', 'id': 'actual-cloud-counting-fragment'}])

field('2501', 'hi', 'explicitly_attributed_prophetic_month_instruction_fragment',
      'This source explicitly names the Messenger for the Ramadan/month saying, deictic gesture and complete-the-count instruction. Its printed twenty-nine remains unchanged; the opening route and final absence-of-thirty wording notice remain context.',
      segments=[part(start='रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने रमज़ान',
                     end=' और तीस का लफ़्ज़', component='actual-month-and-gesture-fragment')],
      retained=['(इशारे से कहा)'])
field('2501', 'ur', 'explicitly_attributed_prophetic_month_instruction_fragment',
      'The explicitly introduced Messenger supplies the actual month statement, gesture and count instruction. The source’s three-decades parenthesis explains the deictic gesture and remains context alongside the final wording comparison; the printed twenty-nine is not harmonized.',
      cuts=['( تین دہائیاں ہوتا )'],
      segments=[part(start='رسول اللہ صلی اللہ علیہ وسلم نے رمضان',
                     end=' اور تیس کا لفظ', component='actual-month-and-gesture-fragment')],
      retained=['( اشارے سے کہا : )'])

field('2517', 'hi', 'companion_report_of_prophetic_moon_sighting_instructions',
      'Araj/Abu Hurayrah explicitly introduces the Messenger’s sighting, fasting and completion instructions. The parenthetic Eid explanation is context; the actual iftar command and concealed-month condition remain complete.',
      cuts=['(ईद)'])
field('2517', 'ur', 'companion_report_of_prophetic_moon_sighting_instructions',
      'Abu Hurayrah’s supplied route names the Messenger and preserves the source’s unusual printed plural honorific. All actual commands, the condition and thirty-day quantity remain; only the Eid explanation is context.',
      cuts=['( عید )'])

field('2525', 'hi', 'companion_report_of_prophetic_month_gestures',
      'Saad ibn Abi Waqqas reports the Messenger’s hand strike, actual month saying and third-time finger reduction. No absent explicit numerical total is inserted.')
field('2525', 'ur', 'companion_report_of_prophetic_month_gestures',
      'The named Saad route supplies the Messenger’s actual hand action, saying and third-time finger reduction. The source’s deictic words remain as printed without an inferred month total.')

field('2534', 'hi', 'companion_historical_report_with_supplied_revelation_wording',
      'Sahl ibn Saad reports the verse’s revelation, literal thread practice and subsequent min-al-fajr wording. The actually supplied recitation and the attributed explanation remain part of this historical account; no verse locator or omitted continuation is supplied.')
field('2534', 'ur', 'companion_historical_report_with_supplied_revelation_wording',
      'Sahl’s own source report prints the Arabic verse excerpt, eating practice and min-al-fajr wording. The missing space between آیت and وَكُلُوا remains unchanged; this is actual supplied recitation within the historical report, not a compiler verse-reference label.')

field('2535', 'hi', 'companion_historical_report_of_fasting_thread_practice',
      'Sahl’s source report supplies tying the threads to both feet, eating/drinking until distinguishable, and the later min-al-fajr understanding. This field does not print the opening verse; no text from2534 is inserted.')
field('2535', 'ur', 'companion_historical_report_of_fasting_thread_practice',
      'The Sahl route supplies the whole own practice and subsequent understanding as an attributed historical report. Its defective spacing and opening reference to an unprinted verse remain exact.')

field('2542', 'hi', 'qualified_transmitted_dawn_saying_and_gesture_fragment',
      'The actual negative/positive dawn clauses and finger gestures are supplied. The action figure carries the source’s Prophetic honorific, but this abbreviated route does not print a complete ultimate-speaker link; that omission is not filled.',
      segments=[part(start='फ़ज्र वह नहीं जो इस तरह हो', component='actual-dawn-clauses-and-gestures')])
field('2542', 'ur', 'qualified_transmitted_dawn_saying_and_gesture_fragment',
      'The supplied dawn clauses and gestures belong to an unexpanded آپ/انہوں voice in this field. No Messenger name or honorific attribution is imported from Hindi or the omitted earlier narration.',
      segments=[part(start='فجر وہ نہیں جو اس طرح ہو', component='actual-dawn-clauses-and-gestures')])

field('2543', 'hi', 'qualified_transmitted_adhan_purpose_and_dawn_fragments',
      'The field supplies the actual Bilal-adhan purpose clause and a separate negative dawn wording fragment attributed to a later route comparison. The ultimate speaker and absent gesture remain unknown; the final width/length paraphrase is explanatory context.',
      segments=[part(start='हज़रात बिलाल (रज़ियल्लाहु अन्हु)', end=' इश्क़ ने कहा:', component='actual-adhan-purpose'),
                part(start='सुबह इस तरह नहीं है', end=' मतलब यह', component='actual-negative-dawn-fragment',
                     report_type='qualified_transmitted_negative_saying_fragment',
                     speaker='The source’s later Ishaq/Jarir comparison supplies this actual negative dawn clause. The ultimate speaker and deictic gesture are absent and remain unknown.')])
field('2543', 'ur', 'qualified_transmitted_adhan_purpose_and_dawn_fragments',
      'The own field supplies Bilal’s adhan-purpose clause and the actual negative dawn clause within the later Ishaq/Jarir transmission. The ultimate voice remains unexpanded; the final مطلب width/length explanation is context.',
      segments=[part(start='حضرت بلال کی اذان', end=' اسحاق نے کہا :', component='actual-adhan-purpose'),
                part(start='صبح اس طرح نہیں ہے', end=' مطلب یہ', component='actual-negative-dawn-fragment',
                     report_type='qualified_transmitted_negative_saying_fragment',
                     speaker='The later Ishaq/Jarir wording notice transmits this finite negative clause. It does not supply the omitted ultimate speaker or gesture.')])

field('2544', 'hi', 'companion_hearing_of_prophetic_suhoor_instruction',
      'Samurah explicitly reports hearing Muhammad the Messenger of Allah. The entire warning about Bilal’s adhan and the whiteness-until-it-spreads condition remain supplied wording.')
field('2544', 'ur', 'companion_hearing_of_prophetic_suhoor_instruction',
      'Samurah’s own field expressly names Muhammad the Messenger as the heard speaker. Preserve both negative objects and the until-it-spreads limit without an inferred time or gesture.')

field('2552', 'hi', 'companion_suhoor_report_with_qualified_question_and_reply',
      'The printed Zayd route reports the meal with the Messenger and standing for prayer. The resumed question and answer are separate voices; the answer’s Prophetic honorific is retained as the source’s own designation, without constructing a missing named link.',
      cuts=['(50)'],
      segments=[part(end='मैंने अर्ज़ किया', component='zayd-meal-and-prayer-report'),
                part(start='मैंने अर्ज़ किया', end='आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया पचास', component='unresolved-question-voice',
                     report_type='qualified_transmitted_time_question',
                     speaker='The first-person questioner is not separately named in the resumed sentence. No canonical Anas-to-Zayd link is inserted.'),
                part(start='आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया पचास', component='honorific-designated-duration-reply',
                     report_type='qualified_source_honorific_designated_reply',
                     speaker='The source applies a Prophetic honorific to आप in the reply. Its absent explicit name/link remains unfilled; the supplied fifty-verse measure is retained without canonical correction.')])
field('2552', 'ur', 'companion_suhoor_report_with_qualified_question_and_reply',
      'The Zayd route supplies the meal and prayer report, then an unmarked first-person question and آپ reply. Those resumed speakers remain unresolved in this field; no Hindi or Roman honorific is borrowed.',
      segments=[part(end='میں نے عرض کیا', component='zayd-meal-and-prayer-report'),
                part(start='میں نے عرض کیا', end='آپ نے فرمایا پچاس', component='unresolved-question-voice',
                     report_type='qualified_transmitted_time_question', speaker='The source prints this first-person question without a separate named resumed speaker.'),
                part(start='آپ نے فرمایا پچاس', component='unresolved-duration-reply',
                     report_type='qualified_transmitted_duration_reply', speaker='The answer uses آپ without a printed name or Prophetic honorific here. Retain the actual fifty-verses measure with that attribution gap.')])
field('2552', 'ar', 'companion_suhoor_report_with_qualified_question_and_reply',
      'The full printed route reaches Zayd’s meal/prayer report. The resumed قلت and قال are separated without asserting an unstated Anas-to-Zayd dialogue assignment; the full original Arabic and its honorifics remain exact.',
      segments=[part(end='قُلْتُ كَمْ', component='zayd-meal-and-prayer-report'),
                part(start='قُلْتُ كَمْ', end='قَالَ خَمْسِينَ', component='unresolved-question-voice',
                     report_type='qualified_transmitted_time_question', speaker='The resumed قلت is not assigned to an externally reconstructed speaker.'),
                part(start='قَالَ خَمْسِينَ', component='unresolved-duration-reply',
                     report_type='qualified_transmitted_duration_reply', speaker='The source prints قال followed by fifty verses, without restating an unambiguous named answerer at this boundary.')])
field('2552', 'en', 'companion_suhoor_report_with_qualified_question_and_reply',
      'The own English names Zaid for the meal/prayer account, then uses I and He without a new explicit link. The repeated acts paraphrase is context; the actual span-of-reciting measure qualifies the reply and remains selected.',
      cuts=['(acts, i. e. taking of Sahri and observing of prayer)'],
      retained=['(a span of reciting)'],
      segments=[part(end='I said:', component='zayd-meal-and-prayer-report'),
                part(start='I said:', end='He said', component='unresolved-question-voice',
                     report_type='qualified_transmitted_time_question', speaker='The English first-person question is not assigned through an imported canonical dialogue link.'),
                part(start='He said', component='unresolved-duration-reply',
                     report_type='qualified_transmitted_duration_reply', speaker='The source prints He said with the reciting-fifty-verses measure; the resumed answerer is not externally identified.')])
field('2552', 'ur-Latn', 'companion_suhoor_report_with_qualified_question_and_reply',
      'This own Roman Urdu names Zaid for the meal/prayer account but supplies a Prophetic honorific on the later Aap reply. Keep that printed distinction and missing link explicit; the parenthetic numeral duplicates pachas and remains context.',
      cuts=['(50)'],
      segments=[part(end='Maine arz kiya', component='zayd-meal-and-prayer-report'),
                part(start='Maine arz kiya', end='Aap (Sallallahu Alaihi Wasallam)', component='unresolved-question-voice',
                     report_type='qualified_transmitted_time_question', speaker='The resumed first-person question is not separately assigned to a named narrator.'),
                part(start='Aap (Sallallahu Alaihi Wasallam)', component='honorific-designated-duration-reply',
                     report_type='qualified_source_honorific_designated_reply', speaker='The answer’s Prophetic honorific is printed by this source field. The absent name/link remains unfilled and no other language’s attribution is substituted.')])

assert len(READINGS) == 20
assert sum(len(fields) for fields in READINGS.values()) == 58
