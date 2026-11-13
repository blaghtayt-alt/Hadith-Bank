"""Explicit source anchors and voices after all47 original fields were fully read."""
from manual_source_first_readings import NOTES
READINGS={}

def part(start=None,end=None,component='report-1',report_type=None,speaker=None):
    r={'start':start,'end':end,'id':component}
    if report_type:r['type']=report_type
    if speaker:r['speaker']=speaker
    return r

def field(number,language,report_type=None,speaker=None,*,start=None,end=None,cuts=(),segments=None,exact=None,context_all=False,retained=()):
    assert language in NOTES[number]
    key='muslim:'+number;assert language not in READINGS.setdefault(key,{})
    r={'note':NOTES[number][language],'type':report_type,'speaker':speaker,'context':list(cuts),
       'context_all':context_all,'source_report_family_id':key+':source-numbered-report',
       'retained_meaningful_structures':list(retained)}
    if exact is not None:r['exact_selections']=exact
    elif not context_all:r['segments']=segments if segments is not None else [part(start,end)]
    READINGS[key][language]=r

field('2556','hi','companion_visit_dialogue_with_prophetic_practice_report',
      'Abu Atiyyah reports the actual visit with Masruq, Aisha’s question, the answer naming Abdullah and her Messenger-practice reply. The separate Ibn Masud identification and final other-person identity notice remain source context.',
      start='हज़रत अबू अत्तियाह (रज़ियल्लाहु अन्हु) से रिवायत',end='अबू कुुरैब की रिवायत',cuts=['(देर)','यानी इब्न मसऊद।'])
field('2556','ur','companion_visit_dialogue_with_prophetic_practice_report',
      'Abu Atiyyah reports the actual visit/question/Abdullah-answer and Aisha’s Messenger-practice reply. The printed Ibn Masud and Abu Musa identification apparatus is preserved separately without rewriting the dialogue.',
      start='حضرت ابو عطیہ رضی اللہ تعالیٰ عنہ سے روایت',end='اب کریب کی روایت',cuts=['یعنی ابن مسعود ،'])

field('2561','hi','companion_journey_report_with_prophetic_command',
      'The source names Abdullah ibn Awfa for the actual fasting journey, sunset and unnamed-addressee sattu command; the unprinted continuation is not supplied.',
      start='हज़रत अब्दुल्लाह बिन औफ़ा',end='आगे हदीस इसी तरह है।')
field('2561','ur','companion_journey_report_with_prophetic_command',
      'The own Abdullah ibn Awfa report retains its printed تم pronoun, sunset and unnamed-addressee command. No Hindi-derived pronoun correction or omitted continuation is supplied.',
      start='حضرت عبداللہ بن اوفیٰ',end='آگے حدیث اسی طرح ہے ۔')

field('2571','hi','companion_report_of_prophetic_practice_and_conditional_reply',
      'Anas transmits the actual continuous-fasting incident and the Messenger’s counterfactual and feeding/drinking reply with all source conditions intact.',
      start='हज़रत अनस (रज़ियल्लाहु अन्हु) से रिवायत')
field('2571','ur','companion_report_of_prophetic_practice_and_conditional_reply',
      'Anas’s own Urdu report supplies the incident, longer-month counterfactual, difference from the followers and feeding/drinking statement; no unprinted act or instruction is added.',
      start='حضرت انس رضی اللہ تعالیٰ عنہ سے روایت')
field('2572','hi','companion_report_of_prophetic_prohibition_and_dialogue',
      'Aisha reports the compassion-qualified prohibition, Companions’ question and actual Messenger reply; the unnamed उनको group is not externally identified.',
      start='हज़रत आयशा (रज़ियल्लाहु अन्हा) फ़रमाती हैं')
field('2572','ur','companion_report_of_prophetic_prohibition_and_dialogue',
      'Aisha supplies the actual compassionate prohibition, question and reply. The source’s ان کو group remains unexpanded.',
      start='حضرت عائشہ رضی اللہ تعالیٰ عنہا فرماتی ہیں')

for language in ('hi','ur','ar','ur-Latn'):
    field('2596',language,context_all=True)
field('2596','en','qualified_transmitted_passive_event_fragment',
      'Within the source’s Zuhri same-chain comparison, the English explicitly supplies a passive brought-dates-container event. The bringer, recipient and ultimate speaker remain unknown; its affirmative predicate is not copied into the differing sibling fields.',
      exact=[{'text':"There was brought an 'araq containing dates,",'id':'affirmative-passive-delivery-fragment'}])

field('2597','hi','qualified_source_report_with_prophetic_expiation_dialogue',
      'The Hindi supplies only its short Yahya-bin-Yahya attribution, then the man’s Ramadan incident and explicit Messenger dialogue. Its final साथ मिस्कीनों spelling remains defective and is not silently converted to Urdu’s sixty; no omitted Abu Hurayra route is imported.')
field('2597','ur','companion_report_with_prophetic_expiation_dialogue',
      'The Urdu explicitly reaches Abu Hurayra, then gives the Ramadan incident, two negative answers and the literal sixty-poor-person instruction; the prefatory route is context.',
      start='حضرت ابوہریرۃ رضی اللہ تعالیٰ عنہ سے روایت')

field('2598','hi','qualified_abbreviated_report_of_prophetic_expiation_instruction',
      'The Zuhri-route preface introduces this actual finite man/broken-fast/enslaved-person-expiation fragment; omitted surrounding narration and other expiation alternatives are not supplied.',
      start='एक आदमी ने रमज़ान',end='फिर इब्न उयैना की हदीस')
field('2598','ur','qualified_abbreviated_report_of_prophetic_expiation_instruction',
      'The source expressly supplies the man’s Ramadan event and the Messenger’s slave-freeing expiation order, with the final Ibn Uyaynah-equivalent continuation remaining unexpanded context.',
      start='ایک آدمی نے رمضان',end='پھر ابن عینیہ کی حدیث')

field('2606','hi','successor_transmitted_historical_assertions',
      'Zuhri’s two finite historical assertions remain separately qualified: breaking the fast as the last act within an unspecified omitted comparison, and the source’s Ramadan13 arrival date. The intervening general legal-precedence rule is context.',
      segments=[part('ज़ुहरी ने कहा के रोज़ा','और रसूल अल्लाह',component='qualified-last-act-assertion',
                     report_type='qualified_successor_historical_assertion',speaker='Zuhri reports breaking the fast as the last act in a comparison whose full context is absent; no lifetime-final-act claim or legal rule is inferred.'),
                part('ज़ुहरी ने कहा के नबी करीम',component='source-arrival-date-assertion',
                     report_type='successor_historical_arrival_report',speaker='Zuhri explicitly reports the Prophet’s Mecca arrival on the source-printed Ramadan13 date; no external chronological correction is made.')])
field('2606','ur','successor_transmitted_historical_assertions',
      'Zuhri supplies two actual historical assertions, distinct from the intervening legal-precedence commentary. Preserve the unspecified comparison scope and literal تیرہ date.',
      segments=[part('زہری نے کہا کہ روزہ','اور رسول اللہ',component='qualified-last-act-assertion',
                     report_type='qualified_successor_historical_assertion',speaker='Zuhri’s آخری عمل assertion keeps its absent comparison context qualified; it is not expanded into a universal normative or lifetime-final-act claim.'),
                part('زہری نے کہا کہ نبی کریم',component='source-arrival-date-assertion',
                     report_type='successor_historical_arrival_report',speaker='Zuhri explicitly supplies the Prophet’s arrival at Mecca on رمضان کی تیرہ تاریخ, retained as printed.')])

field('2608','hi','companion_historical_report_and_attributed_travel_judgment',
      'Ibn Abbas supplies the actual Usfan/drinking/Mecca narrative and separately reintroduced testimony and choice judgment; the latter is not relabelled as direct Prophetic speech.',
      segments=[part('हज़रत इब्न अब्बास (रदी अल्लाहु अन्हु) से रिवायत','हज़रत इब्न अब्बास (रदी अल्लाहु अन्हु) फ़रमाते हैं',component='journey-and-drinking-report'),
                part('हज़रत इब्न अब्बास (रदी अल्लाहु अन्हु) फ़रमाते हैं',component='companion-testimony-and-choice',report_type='companion_testimony_and_travel_judgment',speaker='Ibn Abbas expressly reports both travel practices and the traveller’s choice in his own source-framed statement.')])
field('2608','ur','companion_historical_report_and_attributed_travel_judgment',
      'Ibn Abbas’s Urdu supplies the actual journey/drinking narrative and a separately reintroduced Companion testimony/choice statement; exact source joins and all conditions remain.',
      segments=[part('حضرت ابن عباس رضی اللہ تعالیٰ عنہ سے روایت','حضرت ابن عباس رضی اللہ تعالیٰ عنہ فرماتے ہیں',component='journey-and-drinking-report'),
                part('حضرت ابن عباس رضی اللہ تعالیٰ عنہ فرماتے ہیں',component='companion-testimony-and-choice',report_type='companion_testimony_and_travel_judgment',speaker='The explicit Ibn Abbas voice supplies the travel-practice testimony and choice, not an added verbatim Prophetic instruction.')])
field('2609','hi','companion_collective_practice_and_prophetic_practice_testimony',
      'Ibn Abbas reports both nonblame practices and their stated basis in the Messenger’s travel actions; these are his source-framed testimony, not invented direct commands.',
      start='हज़रत इब्न अब्बास (रदी अल्लाहु अन्हु) से रिवायत')
field('2609','ur','companion_collective_practice_and_prophetic_practice_testimony',
      'Ibn Abbas’s own report retains both negatives, the travel domain and the stated two Messenger practices with the source’s awkward grammar unchanged.',
      start='حضرت ابن عباس رضی اللہ تعالیٰ عنہ سے روایت')

field('2611','hi','qualified_transmitted_honorific_designated_action_fragment',
      'The source’s addition supplies unnamed people’s hardship message and an honorific-designated actor’s water-cup request. The Hindi time token is printed अस्त्र; it is not repaired from Urdu, and no unprinted drinking action or named earlier narrator is supplied.',
      start='आप से अर्ज़ किया गया')
field('2611','ur','qualified_transmitted_honorific_designated_action_fragment',
      'The addition supplies the hardship message, waiting for the honorific-designated actor and his water-cup request after the own عصر. The message-givers and omitted original linkage remain unnamed.',
      start='آپ سے عرض کیاگیا')

field('2614','hi','qualified_transmitted_concession_injunction',
      'The actual concession injunction is expressly transmitted, but its ultimate speaker and the concession’s omitted occasion remain unknown. The unnamed later memory-check discussion stays context.',
      start='अल्लाह तआला ने तुम्हें',end='रावी ने कहा')
field('2614','ur','qualified_transmitted_concession_injunction',
      'The source supplies this finite injunction without an ultimate-speaker name or the concession’s full referent; no Prophetic attribution is inferred from another report. The memory discussion remains context.',
      start='اللہ تعالیٰ نے تمھیں',end='راوی نے کہا')

field('2615','hi','companion_collective_campaign_practice_report',
      'Abu Said reports the source-printed Ramadan16 campaign and both fasting groups’ noncriticism; the date and both negatives remain exact.',
      start='हज़रत अबू सईद ख़ुदरी (रज़ियल्लाहु अन्हु) से रिवायत')
field('2615','ur','companion_collective_campaign_practice_report',
      'Abu Said’s report retains literal سولہ رمضان, the duplicated کو and both directions of noncriticism without harmonization.',
      start='حضرت ابو سعید خدری رضی اللہ تعالیٰ عنہ سے روایت')
field('2617','hi','companion_collective_travel_practice_report',
      'Abu Said’s own Ramadan travel report supplies both noncriticism predicates; no unprinted pronoun or extra practice is supplied.',
      start='हज़रत अबू सईद ख़ुदरी (रज़ियल्लाहु अन्हु) फरमाते हैं')
field('2617','ur','companion_collective_travel_practice_report',
      'The actual Abu Said framing, Ramadan journey and both noncriticism clauses remain after the prefatory chain and its identity gloss.',
      start='حضرت ابو سعید خدری رضی اللہ تعالیٰ عنہ فرماتے ہیں')
field('2618','hi','companion_report_of_collective_practice_and_conditioned_judgment',
      'Abu Said’s source report contains only its printed one-direction noncriticism and both strength/weakness-conditioned group judgments. No reciprocal clause is filled; कमज़ोरी is a lexical gloss retained in context.',
      start='हज़रत अबू सईद ख़ुदरी (रज़ियल्लाहु अन्हु) से रिवायत',cuts=['(कमज़ोरी)'])
field('2618','ur','companion_report_of_collective_practice_and_conditioned_judgment',
      'The Abu Said report keeps its own one-direction noncriticism, both group judgments and all conditions; no reciprocal predicate is copied from parallels.',
      start='حضرت ابو سعید خدری رضی اللہ تعالیٰ عنہ سے روایت')

field('2619','hi','qualified_companion_collective_travel_report',
      'The source’s prefatory list names Abu Said and repeats Jabir. Its final reported collective voice supplies the travel, fasting/nonfasting and mutual nonblame body; the defective duplicated linkage remains visible in context and is not externally settled.',
      start='फरमाया के हम ने')
field('2619','ur','qualified_companion_collective_travel_report',
      'The duplicated Jabir/Abu Said source list remains exact context. The final reported we-voice supplies the finite journey/practices/nonblame account without a repaired single-narrator identity.',
      start='فرمایا کہ ہم نے')
field('2620','hi','companion_question_scene_and_collective_testimony',
      'The actual scene has Anas being asked about Ramadan travel fasting and supplying both nonblame practices. The asker is not named; the question is retained as body rather than being discarded with the preceding route.',
      start='हज़रत अनस (रज़ियल्लाहु अन्हु) से सफ़र')
field('2620','ur','companion_question_scene_and_collective_testimony',
      'The source gives Anas’s being asked and his actual collective testimony, with the asker unnamed and both negative practices preserved.',
      start='حضرت انس رضی اللہ تعالیٰ عنہ سے سفر')
field('2625','hi','companion_report_of_prophetic_travel_choice_dialogue',
      'Aisha reports the source-named Hamza’s travel-fasting question and the Messenger’s two conditional alternatives; own name spellings are not harmonized.',
      start='सईदा आयशा सिद्दीक़ा')
field('2625','ur','companion_report_of_prophetic_travel_choice_dialogue',
      'The own سید عائشہ framing reports the source-spelled Hamza-bin-Umar question and both Messenger alternatives. The name and reporter wording remain exactly as supplied.',
      start='سید عائشہ صدیقہ')

field('2630','hi','companion_travel_heat_and_fasting_observation',
      'Abu Darda’s short source framing and complete Ramadan/heat/hands-on-head scene retain the exact only-two-fasters exception; no route is removed where none is supplied.')
field('2630','ur','companion_travel_heat_and_fasting_observation',
      'Abu Darda’s actual account follows the longer route; every Ramadan/travel/heat condition and the full named exception remain.',
      start='حضرت ابو درداء رضی اللہ تعالیٰ عنہ سے روایت')
field('2631','hi','companion_travel_heat_and_fasting_observation',
      'The short Abu Darda source frame reports some hot-weather journeys and the full named fasting exception. No Ramadan label, corrected name spelling or identity merge with2630 is added.')
field('2631','ur','companion_travel_heat_and_fasting_observation',
      'Abu Darda’s separately framed testimony retains the some-journeys domain, heat scene and full exception; the earlier route is context and Ramadan is not imported.',
      start='حضرت ابو درداء رضی اللہ تعالیٰ عنہ فرماتے ہیں')
field('2635','hi','companion_milk_sending_and_prophetic_action_report',
      'Umm Fadl’s own short report supplies the Arafah-day uncertainty, sending of milk and drinking. No Urdu-only we-were-present clause is inserted.')
field('2635','ur','companion_milk_sending_and_prophetic_action_report',
      'Umm Fadl’s own report includes both the uncertainty and explicitly reintroduced we-were-present clause, then milk sending and drinking; all own source repetitions remain.',
      start='حضرت ام فضل رضی اللہ تعالیٰ عنہا فرماتی ہیں ۔')
field('2636','hi','companion_milk_sending_and_prophetic_action_report',
      'Maimuna’s complete short report retains the fasting doubt, milk vessel, Arafat standing circumstance and drinking while people watched.')
field('2636','ur','companion_milk_sending_and_prophetic_action_report',
      'The source frames Maimuna as the Prophet’s wife before her actual report; that coherent final attribution and every standing/watching circumstance remain, while the preceding route is context.',
      start='حضرت میمونہ رضی اللہ تعالیٰ عنہا نبی کریم')

assert len(READINGS)==22
assert sum(len(f) for f in READINGS.values())==47
