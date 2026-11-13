"""Explicit source boundaries authored after the frozen55-field own-source reading."""
from manual_source_first_readings import NOTES

READINGS = {}

def part(start=None, end=None, component='report-1', report_type=None, speaker=None):
    value = {'start': start, 'end': end, 'id': component}
    if report_type: value['type'] = report_type
    if speaker: value['speaker'] = speaker
    return value

def field(key, language, report_type, speaker, *, start=None, end=None,
          cuts=(), segments=None, retained=(), annotations=()):
    assert ('deenhindi-' + key, language) in NOTES
    assert language not in READINGS.setdefault(key, {})
    value = {'note': NOTES['deenhindi-' + key, language], 'type': report_type,
             'speaker': speaker, 'context': list(cuts), 'context_all': False,
             'source_report_family_id': key + ':source-numbered-report',
             'retained_meaningful_structures': list(retained),
             'segments': segments if segments is not None else [part(start, end)]}
    if annotations: value['source_text_annotations'] = list(annotations)
    READINGS[key][language] = value

def context_field(key, language):
    assert ('deenhindi-' + key, language) in NOTES
    assert language not in READINGS.setdefault(key, {})
    READINGS[key][language] = {'note': NOTES['deenhindi-' + key, language],
        'type': None, 'speaker': None, 'context': [], 'context_all': True,
        'source_report_family_id': key + ':source-numbered-report',
        'retained_meaningful_structures': []}

def qualification(note):
    return {'kind': 'own_field_wording_or_attribution_qualification',
            'note': note, 'new_translation': False}

field('muslim:2715', 'hi', 'companion_report_of_two_prophetic_food_encounters',
      'Aisha reports two separate-day food encounters with the explicitly named Messenger. The second Hindi reply is damaged and does not supply the fasting-in-the-morning statement found in another language.',
      segments=[
          part('उम्-उल-मोमिनीन', 'फिर एक और दिन', 'first-food-question-and-fast-declaration'),
          part('फिर एक और दिन', component='later-gift-and-eating-encounter'),
      ], annotations=[qualification('The second reply remains exactly मुझे खिलाइये सुबह की थी. No fasting predicate or connector is supplied from Urdu.')])
field('muslim:2715', 'ur', 'companion_report_of_two_prophetic_food_encounters',
      'Aisha supplies both the first food question and fasting declaration and the later hays-gift, morning-fast reply and eating episode. Their participants and temporal distinction are her reported narrative.',
      segments=[
          part('ام المومنین', 'پھر ایک اور دن', 'first-food-question-and-fast-declaration'),
          part('پھر ایک اور دن', component='later-gift-and-eating-encounter'),
      ], retained=['( کھانے کی )'])

field('muslim:2720', 'hi', 'abbreviated_named_questioner_encounter',
      'Abdullah ibn Shaqiq supplies his finite first-person asking encounter with Aisha. The question content and answer are not printed and remain absent.',
      start='अब्दुल्लाह बिन शक़ीक़', end='... इसी')
field('muslim:2720', 'ur', 'abbreviated_named_questioner_encounter',
      'The source names Abdullah ibn Shaqiq and Aisha in a short first-person asking encounter, printing the defective predicate سوا کیا. No omitted question, reply or missing letter is reconstructed.',
      start='عبداللہ بن شقیق', end=' ۔ ۔ ۔ اسی',
      annotations=[qualification('The Urdu predicate is printed سوا کیا and is retained exactly. Its spelling is not silently repaired to سوال کیا.')])

field('muslim:2723', 'hi', 'qualified_habitual_saying_fragments',
      'The damaged Hindi introduction leaves the ultimate saying voice represented only by a broken honorific frame. The two actual habitual sayings remain, without importing the omitted Shaaban fasting report or an explicit personal name.',
      segments=[
          part("फ़रमाया करते थे: 'इतने", 'और आप', 'capacity-and-continuation-saying'),
          part('और आप', component='best-continuing-deed-saying'),
      ], retained=['(अमल करने से)'],
      annotations=[qualification('The opening साल के किसी महीने में lacks its own comparison/fasting predicate. It remains context; the explicit Urdu Messenger name and Shaaban claim are not inserted into Hindi.')])
field('muslim:2723', 'ur', 'companion_report_of_fasting_pattern_and_habitual_prophetic_sayings',
      'Aisha reports the explicit Messenger’s Shaaban fasting comparison and two habitual sayings, including the domain of tiring from acts and the final unclosed quotation as printed.',
      segments=[
          part('حضرت عائشہ', 'آپ صلی اللہ علیہ وسلم فرمایا کر تے تھے : " اتنے', 'shaaban-fasting-pattern'),
          part('آپ صلی اللہ علیہ وسلم فرمایا کر تے تھے : " اتنے', 'اور آپ', 'capacity-and-continuation-saying'),
          part('اور آپ', component='best-continuing-deed-saying'),
      ], retained=['( عمل کرنے سے )'])

field('muslim:2724', 'hi', 'companion_fasting_pattern_report_with_anonymous_onlooker_oaths',
      'Ibn Abbas reports the Messenger’s fasting and cessation patterns and the Ramadan exception. The two quoted oaths belong to unnamed onlookers within his report, never to the Prophet.',
      segments=[
          part('हज़रत इब्न अब्बास', 'कहने वाला कहता: नहीं, अल्लाह की क़सम! आप (', 'fasting-pattern-before-onlooker'),
          part('कहने वाला कहता: नहीं, अल्लाह की क़सम! आप (', 'और जब आप', 'first-anonymous-onlooker-oath',
               'anonymous_onlooker_saying_within_companion_report',
               'An unnamed onlooker’s actual oath about not stopping fasting, quoted by Ibn Abbas; not Prophet speech.'),
          part('और जब आप', 'हत्ता कि कहने वाला', 'cessation-pattern'),
          part('हत्ता कि कहने वाला', component='second-anonymous-onlooker-oath',
               report_type='anonymous_onlooker_saying_within_companion_report',
               speaker='A second source-indefinite onlooker utterance about not fasting, within Ibn Abbas’s pattern report; the source does not establish a separate named speaker.'),
      ], retained=['(मुसलसल)'])
field('muslim:2724', 'ur', 'companion_fasting_pattern_report_with_anonymous_onlooker_oaths',
      'Ibn Abbas’s report supplies the explicit Messenger’s fasting/cessation patterns and Ramadan exception. Both oaths are spoken by indefinite onlookers in the narration.',
      segments=[
          part('حضرت ابن عباس', 'کہنے والا کہتا : نہیں ، اللہ کی قسم!آپ صلی', 'fasting-pattern-before-onlooker'),
          part('کہنے والا کہتا : نہیں ، اللہ کی قسم!آپ صلی', 'اور جب آپ', 'first-anonymous-onlooker-oath',
               'anonymous_onlooker_saying_within_companion_report',
               'The unnamed onlooker says the first oath about uninterrupted fasting; this is not attributed to the Prophet.'),
          part('اور جب آپ', 'حتیٰ کہ کہنے والا', 'cessation-pattern'),
          part('حتیٰ کہ کہنے والا', component='second-anonymous-onlooker-oath',
               report_type='anonymous_onlooker_saying_within_companion_report',
               speaker='The source’s indefinite onlooker says the second oath about not fasting; no further identity or quoted Prophet voice is inferred.'),
      ], retained=['( مسلسل )'])

for language in ('hi', 'ur', 'ar', 'en', 'ur-Latn'):
    context_field('muslim:2725', language)

field('muslim:2745', 'hi', 'companion_report_with_uncertain_question_addressee',
      'Imran either received the Messenger’s question himself or heard it addressed to another unnamed man. That source uncertainty, the no-answer, Ramadan completion and every-month two-day instruction all remain.',
      retained=['(रमजान मुकम्मल कर के)', '(हर महीने)'],
      annotations=[qualification('The source’s literal &quot; strings remain literal. The either/or addressee is not resolved.')])
field('muslim:2745', 'ur', 'companion_report_with_uncertain_question_addressee',
      'Imran’s source report preserves whether the Messenger addressed him or another man he overheard, plus the Ramadan endpoint and recurring two-day instruction. The quotation’s unclosed ending remains as supplied.',
      retained=['( رمضان مکمل کرکے )', '( ہرمہینے )'])

field('muslim:2750', 'hi', 'companion_report_of_prophetic_monday_fast_reply',
      'Abu Qatadah reports an unspecified questioner asking the Messenger about Monday fasting and the explicit birth-and-revelation reply. The parenthetic Quran supplies the object of the revelation predicate.',
      start='अबू क़तादा अंसारी', retained=['(क़ुरआन)'])
field('muslim:2750', 'ur', 'companion_report_of_prophetic_monday_fast_reply',
      'Abu Qatadah’s own Urdu supplies the Monday question and Messenger reply about birth and Quran revelation. No questioner identity or date is inferred.',
      start='ابو قتادہ انصاری', retained=['( قرآن )'])

field('muslim:2753', 'hi', 'companion_month_fast_encounter_with_transmitter_quantity_doubt',
      'Imran’s supplied report contains the explicit Prophet question, no-answer and post-Ramadan command. Its first command lacks a number; Shubah’s separately printed tentative two-day recollection does not silently fill that gap.',
      segments=[
          part('हज़रात इमरान बिन हुसैन', "शु'बा ने...", 'month-fast-question-and-instruction'),
          part("शु'बा ने...", component='shubah-material-quantity-doubt',
               report_type='named_transmitter_material_memory_qualification',
               speaker='Shubah explicitly doubts and thinks that the reported instruction said two days. This is his qualified recollection, not an unqualified new Prophet utterance.'),
      ], retained=['यानि शबन', '(या दोरान)'],
      annotations=[qualification('The prefatory route is damaged and the first Hindi command supplies no number before दिन. Neither the missing route link nor Urdu’s one-or-two phrase is inserted.')])
field('muslim:2753', 'ur', 'companion_month_fast_encounter_with_transmitter_quantity_doubt',
      'Imran’s own report supplies the Prophet’s Shaaban question, no-answer and post-Ramadan one-or-two-day instruction, followed by Shubah’s explicit uncertainty and tentative two-day recollection.',
      segments=[
          part('حضرت عمرا ن بن حصین', 'شعبہ نے ۔ ۔ ۔', 'month-fast-question-and-instruction'),
          part('شعبہ نے ۔ ۔ ۔', component='shubah-material-quantity-doubt',
               report_type='named_transmitter_material_memory_qualification',
               speaker='Shubah’s named I-think statement and material doubt qualify the quantity. They do not become the Prophet’s independent first-person speech.'),
      ], retained=['یعنی شعبا ن', '( یا دوران )'])

field('muslim:2756', 'hi', 'explicitly_raised_report_of_prayer_and_fast_questions',
      'Abu Hurayra expressly relates this to the Prophet. Preserve both actual questions and answers, including the after-obligatory/after-Ramadan restrictions, midnight and Allah’s month Muharram.',
      start='हज़रत अबू हुरैरा')
field('muslim:2756', 'ur', 'explicitly_raised_report_of_prayer_and_fast_questions',
      'Abu Hurayra’s source expressly raises the paired prayer-and-fast questions to the Prophet, with both restricted comparisons and the given answers; no further legal inference is appended.',
      start='حضرت ابو ہریرہ')

field('muslim:2768', 'hi', 'companion_report_of_night_vision_with_transmitted_wording_variant',
      'Abu Hurayra reports the Messenger’s dream, household waking, forgetting and last-ten search command. The final named Harmala version supplies an alternate first-person forgetting predicate, separately qualified as transmitted wording.',
      segments=[
          part('हज़रत अबू हुरैराह', 'हरमाला ने (मुझे', 'vision-waking-and-search-report'),
          part('हरमाला ने (मुझे', component='harmala-forgetting-wording-variant',
               report_type='qualified_transmitted_first_person_predicate_variant',
               speaker='Harmala is the source-named transmitter of the finite I-forgot wording variant in this report. It is not an assertion that Harmala personally experienced the described vision.'),
      ], cuts=['(मुझे भुला दी गई के बजाय)'], retained=['(ख़्वाब में)', '(आख़िरी)'])
field('muslim:2768', 'ur', 'companion_report_of_night_vision_with_transmitted_wording_variant',
      'Abu Hurayra’s own report gives the explicit Messenger’s dream, waking and last-ten search command. Harmala’s final I-forgot version is kept as separately qualified transmitted wording; doubled quote marks remain literal.',
      segments=[
          part('حضرت ابو ہریرہ', 'حرملہ نے (', 'vision-waking-and-search-report'),
          part('حرملہ نے (', component='harmala-forgetting-wording-variant',
               report_type='qualified_transmitted_first_person_predicate_variant',
               speaker='The named Harmala frame introduces the finite first-person forgetting variant of this report, not a biographical statement about Harmala himself.'),
      ], cuts=['( "" مجھے بھلوادی گئی "" کے بجا ئے )'], retained=['( خواب میں )', '( آخری )'])

field('muslim:2774', 'hi', 'companion_retreat_and_search_report_with_later_counting_dialogue',
      'Abu Said reports the Messenger’s retreat, tents, public announcement and search instruction. The later Abu Nadrah/Abu Said counting exchange is an actual separately voiced encounter, not another Prophet saying.',
      segments=[
          part('हज़रत अबू सईद ख़ुदरी', 'अबू नदरा ने कहा:', 'retreat-announcement-and-search-report'),
          part('अबू नदरा ने कहा:', component='abu-nadrah-abu-said-counting-dialogue',
               report_type='named_questioner_companion_counting_dialogue',
               speaker='Abu Nadrah asks Abu Said; Abu Said claims greater knowledge of the count and gives the printed ordinal explanation. Its peculiar sequence is not corrected from another edition or language.'),
      ], annotations=[qualification('The actual ninth/seventh/fifth and twenty-first/twenty-third/twenty-fifth sequence remains literal. No calendrical correction is introduced.')])
field('muslim:2774', 'ur', 'companion_retreat_and_search_report_with_later_counting_dialogue',
      'Abu Said’s source report supplies the Messenger’s retreat/announcement and the subsequent actual Abu Nadrah/Abu Said count dialogue. Supplied parenthetic actors, objects, interval, reciprocal claim and counting clause remain.',
      segments=[
          part('حضرت ابو سعید خدری', '( ابو نضرہ نے )', 'retreat-announcement-and-search-report'),
          part('( ابو نضرہ نے )', component='abu-nadrah-abu-said-counting-dialogue',
               report_type='named_questioner_companion_counting_dialogue',
               speaker='The source identifies Abu Nadrah as questioner and Abu Said as the answering Companion. The latter’s counting explanation, duplicate تم and malformed final delimiters remain his supplied report, not Prophet speech.'),
      ], retained=['( دس راتیں )', '( وہ رات )', '( خیمے لگا نے کا )', '( ایک دوسرے پر )', '( رات )', '( ابو نضرہ نے )', '( آخر سے گنتے ہو ئے ساتویں رات آتی ہے )'],
      annotations=[qualification('The Urdu’s source spellings, repeated تم and unbalanced final closing parenthesis remain exactly supplied. Its ordinal explanation is not harmonized with Hindi.')])

field('muslim:2777', 'hi', 'named_questioner_companion_dialogue_about_night_sign',
      'Zirr questions Ubay, initially citing Ibn Masud’s year-long-qiyam view. Ubay supplies his interpretation, oath, date claim and an explicitly reported Messenger sign; none of Ubay’s own commentary is relabelled Prophet speech.',
      segments=[
          part('हज़रत ज़र बिन हुबैश', 'उन्होंने फ़रमाया:', 'zirr-question-with-ibn-masud-view',
               'question_citing_companion_view',
               'Zirr’s actual question cites the view attributed to Ibn Masud about year-long night standing; it is not a Prophet utterance.'),
          part('उन्होंने फ़रमाया:', 'इस पर मैंने कहा:', 'ubay-interpretation-and-oath',
               'companion_interpretation_and_date_oath',
               'Ubay gives the expressed motive, Ramadan/last-ten/twenty-seventh claims and his own oath without an exception formula.'),
          part('इस पर मैंने कहा:', component='question-and-reported-sign',
               report_type='companion_answer_citing_prophetic_sign',
               speaker='Zirr asks the basis; Ubay answers by citing the sign he says the Messenger told them. Preserve that indirect attribution and the source’s non-visible-rays qualification.'),
      ], cuts=['(इन्शाअल्लाह कहे)'])
field('muslim:2777', 'ur', 'named_questioner_companion_dialogue_about_night_sign',
      'Zirr questions Ubay and cites Ibn Masud. Ubay’s motive interpretation, date oath and later answer about the reported Messenger sign have distinct source roles; meaningful night, limited-worship and visibility qualifiers remain.',
      segments=[
          part('حضرت زربن حبیش', 'انھوں نے فر ما یا :', 'zirr-question-with-ibn-masud-view',
               'question_citing_companion_view',
               'Zirr’s question quotes the view assigned to Ibn Masud about standing through the year at night. No Prophet attribution is added.'),
          part('انھوں نے فر ما یا :', 'اس پر میں نے کہا :', 'ubay-interpretation-and-oath',
               'companion_interpretation_and_date_oath',
               'Ubay interprets Ibn Masud’s motive and states his own Ramadan/last-ten/date claim and oath; the source explicitly says it was without the exception formula.'),
          part('اس پر میں نے کہا :', component='question-and-reported-sign',
               report_type='companion_answer_citing_prophetic_sign',
               speaker='Zirr asks the grounds, and Ubay cites the sign that he attributes to the Messenger. The rays are described as not conspicuous, not silently rewritten as physically absent.'),
      ], cuts=['( ان شاء اللہ کہے )'], retained=['( رات کو )', '( کم راتوں کی عبادت پر )', '( نما یاں )'])

field('muslim:2793', 'hi', 'qualified_clothing_prohibition_and_conditional_instruction_report',
      'The short Abdullah ibn Dinar/Ibn Umar attribution is supplied, but the ultimate prohibiting actor is printed only as the broken honorific अलैहि वसल्लम). Preserve that limitation with both dye alternatives and the no-shoes conditional; no missing Prophet name is inserted.',
      annotations=[qualification('The ultimate subject of the Hindi report is an incomplete honorific frame. The explicit Urdu Messenger name is not used to repair it.')])
field('muslim:2793', 'ur', 'short_companion_report_of_prophetic_clothing_instruction',
      'The short Abdullah ibn Dinar/Ibn Umar report expressly names Allah’s Messenger for the saffron-or-wars prohibition and the conditional stockings/cutting instruction. Preserve the alternatives and below-ankles endpoint.')

field('ibnmajah:2695', 'hi', 'companion_report_of_prophetic_at_death_inventory',
      'Aisha’s negative dinar/dirham/goat/camel inventory and no-bequest report are explicitly limited to the Messenger’s death, not generalized into a lifetime property claim.',
      retained=['(अपनी वफ़ात के वक़्त)'])
field('ibnmajah:2695', 'ur', 'companion_report_of_prophetic_at_death_inventory',
      'Aisha reports the Messenger’s at-death negative inventory and no-bequest statement; the time restriction remains, while the printed footnote glyph is context.',
      cuts=['۱؎'], retained=['( اپنی وفات کے وقت )'])

field('ibnmajah:2707', 'hi', 'companion_demonstration_report_with_source_attributed_divine_speech',
      'Busr reports the explicit Messenger’s palm, saliva and finger demonstration and his quotation attributed to Allah. The intervening throat-pointing action is narrated action, not Allah’s speech.',
      segments=[
          part(None, 'अल्लाह तआला फ़रमाता है:', 'busr-demonstration-report',
               'companion_report_of_prophetic_demonstration',
               'Busr narrates the Messenger’s palm/saliva/index-finger demonstration and introduction of a saying.'),
          part('अल्लाह तआला फ़रमाता है:', '(आपने हलक़', 'source-attributed-divine-speech',
               'prophetic_report_quoting_speech_attributed_to_allah',
               'The source explicitly presents the Messenger as quoting Allah, including the embedded human charity declaration. This describes its local attribution without separate authenticity certification.'),
          part('(आपने हलक़', 'तो कहता है', 'narrated-throat-pointing-gesture',
               'narrated_prophetic_demonstration_action',
               'The parenthesis reports the Messenger’s pointing toward the throat, an actual gesture interrupting the quoted saying.'),
          part('तो कहता है', component='source-attributed-divine-speech-resumed',
               report_type='prophetic_report_quoting_speech_attributed_to_allah',
               speaker='The source explicitly presents the Messenger as quoting Allah, including the embedded human charity declaration. This describes its local attribution without separate authenticity certification.'),
      ], cuts=['(मनी)'], retained=['(आपने हलक़ की तरफ़ इशारा फ़रमाया)'])
field('ibnmajah:2707', 'ur', 'companion_demonstration_report_with_source_attributed_divine_speech',
      'Busr’s report distinguishes the Messenger’s demonstration, the explicitly attributed Allah-saying and the narrator’s intervening throat gesture. The own Urdu’s action is preserved even though it is not parenthesized.',
      segments=[
          part(None, 'اللہ تعالیٰ فرماتا ہے:', 'busr-demonstration-report',
               'companion_report_of_prophetic_demonstration',
               'Busr supplies the Messenger’s palm, saliva and finger action before the attributed quotation.'),
          part('اللہ تعالیٰ فرماتا ہے:', 'آپ نے اپنے حلق', 'source-attributed-divine-speech',
               'prophetic_report_quoting_speech_attributed_to_allah',
               'The source has the Messenger quote Allah, with a human charity declaration embedded inside the same saying. This is a source-attribution classification only.'),
          part('آپ نے اپنے حلق', 'تو کہتا ہے', 'narrated-throat-pointing-gesture',
               'narrated_prophetic_demonstration_action',
               speaker='The actual intervening clause describes the Messenger pointing toward his throat; it is not part of Allah’s voice.'),
          part('تو کہتا ہے', component='source-attributed-divine-speech-resumed',
               report_type='prophetic_report_quoting_speech_attributed_to_allah',
               speaker='The source has the Messenger quote Allah, with a human charity declaration embedded inside the same saying. This is a source-attribution classification only.'),
      ], cuts=['( منی )', '۱؎'])

field('ibnmajah:2708', 'hi', 'companion_illness_visit_and_bequest_dialogue',
      'Sad’s own report dates the illness to the conquest-of-Mecca year and gives the Messenger’s visit, sole-daughter condition, successive fractions and heirs comparison. The source’s date and all answers remain uncorrected.',
      annotations=[qualification('The field explicitly says the conquest-of-Mecca year; no alternate chronology or canonical wording is substituted.')])
field('ibnmajah:2708', 'ur', 'companion_illness_visit_and_bequest_dialogue',
      'Sad reports the conquest-year illness, visit and fraction-by-fraction dialogue with the Messenger, followed by the heirs’ circumstances. The iyadah synonym and footnote glyph are context; no actual reply or condition is removed.',
      cuts=['( بیمار پرسی )', '۱؎'],
      annotations=[qualification('The date remains exactly فتح مکہ کے سال, without outside chronological correction.')])

field('ibnmajah:2715', 'hi', 'companion_report_and_own_recitation_inheritance_statement',
      'Ali first reports the explicit Messenger’s debt-before-bequest decision, then addresses his listeners with the supplied verse/rendering and gives an unreintroduced brother-inheritance statement. These later words are not relabelled a direct Prophet quotation.',
      segments=[
          part(None, 'हालानके तुम', 'reported-prophetic-debt-order',
               'companion_report_of_prophetic_decision',
               'Ali reports the Messenger’s debt-payment-before-bequest decision, including the actual payment qualification.'),
          part('हालानके तुम', 'और हक़ीक़ी भाई', 'ali-recitation-and-source-rendering',
               'companion_address_with_actual_verse_and_rendering',
               'Ali’s address supplies the quoted verse and its own printed rendering. The citation locator is retained separately as context, not recited speech.'),
          part('और हक़ीक़ी भाई', component='ali-brother-inheritance-statement',
               report_type='unreintroduced_companion_inheritance_statement',
               speaker='The source continues Ali’s account with the actual full-brother/half-brother statement without a renewed direct-Prophet quotation link.'),
      ], cuts=['(सूरह अन-निसा: 11)', '(सौतेले)'], retained=['(की अदायगी)', '(की तकमील)'])
field('ibnmajah:2715', 'ur', 'companion_report_and_own_recitation_inheritance_statement',
      'Ali reports the Messenger’s decision, then supplies his address, the actual Arabic verse and Urdu rendering, followed by the unreintroduced brother statement. Payment/fulfilment qualifiers remain actual scope.',
      segments=[
          part(None, 'حالانکہ تم', 'reported-prophetic-debt-order',
               'companion_report_of_prophetic_decision',
               'Ali’s own report attributes the debt-payment order to the Messenger.'),
          part('حالانکہ تم', 'اور حقیقی بھائی', 'ali-recitation-and-source-rendering',
               'companion_address_with_actual_verse_and_rendering',
               'Ali addresses the reader and supplies the actual verse and Urdu rendering; locator and footnote glyph remain context.'),
          part('اور حقیقی بھائی', component='ali-brother-inheritance-statement',
               report_type='unreintroduced_companion_inheritance_statement',
               speaker='The source’s continuing Ali account gives the brother-inheritance statement without explicitly renewing direct Prophet attribution.'),
      ], cuts=['( سورۃ النساء: ۱۱ ) ۱؎ '], retained=['( کی ادائیگی )', '( کی تکمیل )'])

field('ibnmajah:2723', 'hi', 'companion_report_of_particular_grandfather_share_decision',
      'The source-named Maqil reports the Messenger’s one-sixth decision for a grandfather in the reporter’s family. No universal heir formula or absent family members are inferred.')
field('ibnmajah:2723', 'ur', 'companion_report_of_particular_grandfather_share_decision',
      'Maqil’s own field supplies the particular family grandfather and the Messenger’s one-sixth decision. The case is not expanded beyond its actual wording.')

field('ibnmajah:2732', 'hi', 'qualified_historical_inheritance_case_with_embedded_report_and_judgments',
      'The source-named Abdullah ibn Amr gives a damaged historical case, an Umar undertaking with a cited Messenger rule, later documentary events and Abd al-Malik’s own statement/judgment. Hindi omissions and names remain literal; Urdu supplies no missing facts.',
      segments=[
          part(None, 'उम्र (रज़ियल्लाहु अन्हु) ने फ़रमाया:', 'historical-case-before-umar'),
          part('उम्र (रज़ियल्लाहु अन्हु) ने फ़रमाया:', 'आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया:', 'umar-judgment-undertaking',
               'named_companion_judgment_undertaking',
               'The source-named उम्र promises to decide by what he heard from the Messenger. This is his own undertaking, not the Messenger’s first-person statement.'),
          part('आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया:', 'उम्र (रज़ियल्लाहु अन्हु) ने हमारे', 'umar-cited-prophetic-wala-rule',
               'companion_citation_of_prophetic_saying',
               'The preceding source explicitly identifies the Messenger as the authority Umar heard; this finite wala rule is the quoted saying, without additional absent conditions.'),
          part('उम्र (रज़ियल्लाहु अन्हु) ने हमारे', 'अब्दुल मलिक ने कहा:', 'judgment-document-and-later-estate-history'),
          part('अब्दुल मलिक ने कहा:', 'आखिर-कर अब्दुल मलिक', 'abd-al-malik-judgment-appraisal',
               'named_historical_actor_judgment_statement',
               'Abd al-Malik states his own appraisal of the earlier decision and his expectation concerning Medina’s people; this is actual case dialogue, not Prophet speech.'),
          part('आखिर-कर अब्दुल मलिक', component='reported-final-judgment-outcome'),
      ], cuts=['(हक़-इ-मीरास)'],
      annotations=[qualification('The source prints रबाह, सहम and damaged unlinked clauses. It omits the Urdu’s children count, maternal death, land/plague detail, Zayd witness, reversal/Hisham link and continued-possession conclusion. None is supplied or repaired.')])
field('ibnmajah:2732', 'ur', 'historical_inheritance_case_with_embedded_prophetic_report_and_judgments',
      'Abdullah ibn Amr’s own Urdu gives the family deaths, property/wala dispute, Umar undertaking and cited Messenger rule, witnessed document, later reversal/appeal and Abd al-Malik outcome. Actual judicial dialogue remains separately voiced within this one case report.',
      segments=[
          part(None, 'عمر رضی اللہ عنہ نے کہا:', 'historical-case-before-umar'),
          part('عمر رضی اللہ عنہ نے کہا:', 'میں نے آپ صلی اللہعلیہ وسلم کو فرماتے سنا:', 'umar-judgment-undertaking',
               'named_companion_judgment_undertaking',
               'Umar says that he will judge according to what he heard from the Messenger, as his own judicial undertaking.'),
          part('میں نے آپ صلی اللہعلیہ وسلم کو فرماتے سنا:', 'اس کے بعد عمر', 'umar-cited-prophetic-wala-rule',
               'companion_citation_of_prophetic_saying',
               'Umar explicitly reports hearing the Messenger’s finite wala rule, including the Urdu’s whoever-they-may-be qualification.'),
          part('اس کے بعد عمر', 'جس پر عبدالملک نے کہا:', 'judgment-document-and-later-estate-history'),
          part('جس پر عبدالملک نے کہا:', 'آخر کار عبدالملک', 'abd-al-malik-judgment-appraisal',
               'named_historical_actor_judgment_statement',
               'Abd al-Malik supplies his actual appraisal in this case. The supplementary clear adjective is lexical context; the complete doubt/appraisal predicates remain his speech.'),
          part('آخر کار عبدالملک', component='reported-final-judgment-and-possession-outcome'),
      ], cuts=['( حق میراث )', '( واضح )', '۱؎'])

field('ibnmajah:2734', 'hi', 'named_woman_report_of_particular_estate_division',
      'Bint Hamzah is introduced as Abdullah ibn Shaddad’s maternal half-sister, not the deceased slave’s sister. Her report supplies the death and Messenger’s half-and-half division; the unattributed final legal explanation remains context.',
      cuts=['(बेटी को फ़र्ज़ के तौर पर और बेहेन को असबा के तौर पर)'],
      annotations=[qualification('The source does not expressly say that she freed this slave. The daughter-left-behind clause printed in Urdu is not added to Hindi, and the final unvoiced legal aside is not used to change the named relation.')])
field('ibnmajah:2734', 'ur', 'named_woman_report_of_particular_estate_division',
      'Bint Hamzah, identified as Abdullah ibn Shaddad’s maternal half-sister, reports her slave’s death leaving a daughter and the Messenger’s equal division. The appended fixed-share/asabah explanation is unvoiced legal context.',
      cuts=['( بیٹی کو بطور فرض اور بہن کو بطور عصبہ )'],
      annotations=[qualification('The introductory maternal-half-sister relation is to Abdullah ibn Shaddad. It is not silently reassigned to the deceased slave, and no unprinted manumission is inferred.')])

field('ibnmajah:2739', 'hi', 'companion_report_of_prophetic_full_brother_inheritance_statement',
      'Ali’s own Hindi attributes the finite mutual-full-brother inheritance statement to the Messenger. It ends there without the Urdu’s additional negative clauses or final punctuation.',
      annotations=[qualification('No half-brother exclusion clause is supplied to this shorter Hindi wording.')])
field('ibnmajah:2739', 'ur', 'companion_report_of_prophetic_brother_inheritance_statement',
      'Ali’s own Urdu supplies both the full-brother inheritance statement and its repeated negative half-brother exclusions, explicitly attributed to the Messenger. All actual repetitions remain.')

field('ibnmajah:2741', 'hi', 'companion_report_of_estate_award_to_explicitly_freed_slave',
      'Ibn Abbas reports an unnamed man’s death in the Messenger’s time, no heir except the slave he had freed, and the ensuing award. The source expressly supplies the manumission and exception; no missing kin are inferred.')
field('ibnmajah:2741', 'ur', 'companion_report_of_estate_award_to_explicitly_freed_slave',
      'Ibn Abbas’s source states the Prophet-era death, the sole exception of the previously freed slave and the honorific-pronominal award action. The original pronoun is preserved without inserting a new personal-name clause.')

field('ibnmajah:2747', 'hi', 'companion_report_of_prophetic_wala_sale_and_gift_prohibition',
      'Ibn Umar’s own occurrence supplies the Messenger’s ban on selling and gifting wala. The parenthetic inheritance definition is lexical context; source-local identity remains distinct from 2748.',
      cuts=['(मीरास)'])
field('ibnmajah:2747', 'ur', 'companion_report_of_prophetic_wala_sale_and_gift_prohibition',
      'This separately read Ibn Umar field gives the sale-and-gift ban, with its inheritance definition and footnote glyph preserved as context. No merge with the adjacent source occurrence is made.',
      cuts=['( میراث )', '۱؎'])
field('ibnmajah:2748', 'hi', 'companion_report_of_prophetic_wala_sale_and_gift_prohibition',
      'The separately numbered and separately read Ibn Umar field preserves its own उसको wording in the sale-and-gift ban. Only the lexical inheritance definition is context.',
      cuts=['(मीरास)'])
field('ibnmajah:2748', 'ur', 'companion_report_of_prophetic_wala_sale_and_gift_prohibition',
      'This own Urdu field preserves its اس کو wording and has no footnote glyph to invent or remove. The wala inheritance definition is lexical context.',
      cuts=['( میراث )'])

field('ibnmajah:2752', 'hi', 'short_hearing_frame_with_companion_conversion_question',
      'The source-named Abdullah ibn Mohib directly hears Tamim’s actual question to the Messenger and the life-and-death closeness reply. This short hearing frame is retained; no explicit inheritance allocation is supplied by the field.',
      annotations=[qualification('The supplied reply says greater closeness in life and death. An inheritance formula is not inferred from the chapter or another source.')])
field('ibnmajah:2752', 'ur', 'short_hearing_frame_with_companion_conversion_question',
      'Abdullah ibn Mawhab’s short hearing statement introduces Tamim’s actual People-of-the-Book conversion question and the Messenger’s closeness reply. Preserve the conditions and reply without adding a share or inheritance rule.',
      cuts=['۱؎'])

field('ibnmajah:2764', 'hi', 'companion_tabuk_return_report_with_question_and_reply',
      'Anas reports the Messenger’s Tabuk return near Medina, the every-route/every-valley participation statement, the Companions’ question and the excuse-based reply. All place/time/domain qualifications remain; no specific excuse or reward is added.')
field('ibnmajah:2764', 'ur', 'companion_tabuk_return_report_with_question_and_reply',
      'Anas’s own Urdu supplies the Tabuk return, Medina location, route/valley scope, actual question and affirmative excuse-based answer. The footnote glyph is context; no illness, poverty or reward term is inserted.',
      cuts=['۱؎'])

assert len(READINGS) == 26
assert sum(map(len, READINGS.values())) == 55
