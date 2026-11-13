"""Explicit boundaries authored only after all36 original fields were read."""
from manual_source_first_readings import NOTES
READINGS={}

def part(start=None,end=None,component='report-1',report_type=None,speaker=None):
    value={'start':start,'end':end,'id':component}
    if report_type:value['type']=report_type
    if speaker:value['speaker']=speaker
    return value

def field(key,language,report_type,speaker,*,start=None,end=None,cuts=(),segments=None,retained=(),annotations=()):
    assert ('deenhindi-'+key,language) in NOTES
    assert language not in READINGS.setdefault(key,{})
    value={'note':NOTES['deenhindi-'+key,language],'type':report_type,'speaker':speaker,
           'context':list(cuts),'context_all':False,
           'source_report_family_id':key+':source-numbered-report',
           'retained_meaningful_structures':list(retained),
           'segments':segments if segments is not None else [part(start,end)]}
    if annotations:value['source_text_annotations']=list(annotations)
    READINGS[key][language]=value

def qualification(note):
    return {'kind':'own_field_wording_or_attribution_qualification','note':note,'new_translation':False}

field('muslim:2646','hi','abbreviated_companion_report_of_mention_before_prophet',
      'Ibn Umar reports only the supplied event of the Ashura fast being mentioned in the Prophet’s presence. The mentioner, reply and referenced continuation remain unknown.',
      start='हज़रत इब्न उमर',end='फिर आगे इसी तरह')
field('muslim:2646','ur','abbreviated_companion_report_of_mention_before_prophet',
      'The own Ibn Umar frame supplies an Ashura-fast mention before the Prophet; no reply, fasting command or absent continuation is reconstructed.',
      start='حضرت ابن عمر',end='پھر آگے اسی طرح')

field('muslim:2647','hi','companion_report_of_prophetic_ashura_reply',
      'Ibn Umar transmits the Ashura-day mention and the explicit Prophet reply, preserving both choices and the pre-Islamic practice description.',
      start='हज़रत इब्न उमर')
field('muslim:2647','ur','companion_report_of_prophetic_ashura_reply',
      'Ibn Umar’s own Urdu report supplies the mention, the explicitly attributed reply and both fast-or-leave alternatives; its source spacing remains exact.',
      start='حضرت ابن عمر')

field('muslim:2665','hi','named_questioner_companion_encounter_fragment',
      'The Hindi source names हाकम बिन आरज as the questioner who encountered Ibn Abbas at Zamzam and asked about Ashura. Its printed name is not silently repaired, and the unprinted answer remains absent.',
      start='हज़रत हाकम बिन आरज',end='इसके बाद इसी तरह',
      annotations=[qualification('The own Hindi name हाकम बिन आरज remains literal. No Urdu-derived spelling or missing answer is inserted.')])
field('muslim:2665','ur','named_questioner_companion_encounter_fragment',
      'The own Urdu names حکم بن اعرج and supplies his question to Ibn Abbas by Zamzam, with the cloak/resting circumstance. It supplies no answer.',
      start='حضرت حکم بن اعرج',end='اس کے بعد اسی طرح')

field('muslim:2668','hi','companion_report_of_prophetic_conditional_announcement',
      'Salamah reports the Prophet’s unnamed Aslam messenger and the actual Ashura announcement, retaining both fasting/eating conditions and the source’s until-night endpoint.',
      start='हज़रत सलामा बिन अकवा')
field('muslim:2668','ur','companion_report_of_prophetic_conditional_announcement',
      'Salamah’s own field supplies the unnamed Aslam messenger, explicit order, two distinct conditions and the stated night endpoint without an added legal conclusion.',
      start='حضرت سلمہ بن اکوع')

field('muslim:2669','hi','qualified_report_of_prophetic_message_and_group_practice',
      'The damaged Hindi prefix does not name its final female reporting voice. The intact source explicitly attributes the Ashura message to the Prophet; a later unnamed we-voice supplies the children-and-dolls practice. No Rubay identity is borrowed from Urdu.',
      segments=[
          part('फरमाती हैं के','इस के बाद हम',component='prophetic-ashura-message',
               report_type='prophetic_message_report_with_unidentified_female_reporter',
               speaker='The source’s uncompleted introduction leaves its feminine reporting voice unidentified; the following Ashura message is explicitly attributed to the Prophet and retains both printed conditions.'),
          part('इस के बाद हम',component='subsequent-group-child-fasting-practice',
               report_type='qualified_group_practice_report',
               speaker='The Hindi source’s resumed we-voice recounts later fasting with children, mosque visits and dolls until iftar. Its reporter is not named in this damaged field and is not supplied from Urdu.'),
      ],annotations=[qualification('The Hindi opening leaves a transmitter-name/honorific fragment before a feminine reporting verb. That damaged prefatory fragment remains context; no missing Rubay name or route is reconstructed.')])
field('muslim:2669','ur','companion_report_of_prophetic_message_and_group_practice',
      'The own Urdu names ربیع بنت معوذ بن عفراء for the Prophet’s Ashura message and her group’s later child-fasting practice. Its name and honorific are preserved as printed and never copied into the differing Hindi field.',
      segments=[
          part('حضرت ربیع بنت معوذبن عفراء','اس کے بعد ہم',component='prophetic-ashura-message',
               report_type='companion_report_of_prophetic_ashura_message',
               speaker='The own source-named Rubay reports the Prophet’s Ashura-morning message with its two conditions.'),
          part('اس کے بعد ہم',component='subsequent-group-child-fasting-practice',
               report_type='companion_group_practice_report',
               speaker='The named reporter’s subsequent we-account supplies fasting with children, mosque visits and cotton dolls until iftar; these are group practices, not new words spoken by the Prophet.'),
      ])

field('muslim:2670','hi','question_encounter_dispatch_and_resumed_practice_variant',
      'Khalid’s actual question to the source-named Rubay and her representative-dispatch reply are preserved. The later we-practice appears within a variant comparison and keeps its resumed speaker qualified rather than inventing a separate identity.',
      segments=[
          part('हज़रत ख़ालिद बिन ज़कवान','फिर आ कर बिश्र',component='question-and-dispatch-encounter',
               report_type='named_questioner_encounter_with_companion_dispatch_report',
               speaker='Khalid reports his actual Ashura question to the source-named Rubay and her finite reply that the Prophet sent a representative to the Ansar settlement; the missing announcement is not supplied.'),
          part('उन्होंने कहा के हम उन बच्चों',component='resumed-child-fasting-variant',
               report_type='qualified_transmitted_group_practice_variant',
               speaker='The source’s resumed they-said/we clause supplies the dolls, mosque, food requests and completion of the fast. This later variant does not separately name its ultimate speaker and is not labelled Prophet speech.'),
      ])
field('muslim:2670','ur','question_encounter_dispatch_and_resumed_practice_variant',
      'The own Khalid/Rubay question and dispatch report remain before the comparison, followed by the actual separately qualified we-practice variant. No absent message or unprinted later speaker link is added.',
      segments=[
          part('حضرت خالد بن ذکوان','پھر آکر بشر',component='question-and-dispatch-encounter',
               report_type='named_questioner_encounter_with_companion_dispatch_report',
               speaker='Khalid supplies his own question to Rubay and her actual dispatch statement; the question scene is body, not a prefatory transmission route.'),
          part('انہوں نے کہا کہ ہم ان بچوں',component='resumed-child-fasting-variant',
               report_type='qualified_transmitted_group_practice_variant',
               speaker='The source resumes a they-said/we practice variant after the Bishr comparison. Preserve its supplied children/mosque/dolls predicates without silently settling the later pronoun’s speaker or filling the missing message.'),
      ])

field('muslim:2671','hi','witness_report_and_umar_sermon_relay',
      'Abu Ubayd reports attending Umar’s Eid prayer and sermon; Umar’s actual sermon relays the Prophet’s prohibition, rather than becoming a new verbatim Prophet saying.',
      segments=[
          part('हज़रत अबू उबैद','और फरमाया के ये',component='eid-prayer-sermon-encounter',
               report_type='named_witness_eid_prayer_and_sermon_report',
               speaker='The source-named Abu Ubayd reports his presence with Umar, the Eid prayer and ensuing sermon.'),
          part('और फरमाया के ये',component='umar-sermon-relaying-prohibition',
               report_type='companion_sermon_relaying_prophetic_prohibition',
               speaker='Umar delivers the printed statement about the two days and attributes the fasting prohibition to the Prophet; the sermon’s own voice remains Umar’s.'),
      ])
field('muslim:2671','ur','witness_report_and_umar_sermon_relay',
      'The own Abu Ubayd witness account and Umar’s two-day sermon are distinct voices in one encounter. The sermon reports a Prophetic prohibition without asserting that all of Umar’s wording is direct Prophet speech.',
      segments=[
          part('حضرت ابو عبید','اور فرمایا کہ یہ',component='eid-prayer-sermon-encounter',
               report_type='named_witness_eid_prayer_and_sermon_report',
               speaker='Abu Ubayd’s own frame supplies presence with Umar, prayer and the following sermon.'),
          part('اور فرمایا کہ یہ',component='umar-sermon-relaying-prohibition',
               report_type='companion_sermon_relaying_prophetic_prohibition',
               speaker='Umar’s actual sermon relays the Prophet’s prohibition and describes the two days; no external date or new speaker is supplied.'),
      ])

field('muslim:2675','hi','transmitted_vow_question_and_companion_reply',
      'Ziyad ibn Jubayr reports an unnamed man’s Eid-vow question and Ibn Umar’s actual answer relating Allah’s command and the Prophet’s prohibition. The whole reply is not relabelled as direct Prophet speech.',
      start='हज़रत ज़ियाद बिन जुबैर')
field('muslim:2675','ur','transmitted_vow_question_and_companion_reply',
      'The source-named Ziyad relays the anonymous questioner and Ibn Umar’s answer, preserving the two Eid alternatives and each attributed command without an added resolution.',
      start='حضرت زیاد بن جبیر')

field('muslim:2676','hi','companion_report_of_prophetic_two_fast_prohibition',
      'Aisha’s short source attribution reports the two fasts and their two named days; the repeated of-fasts parenthesis is context while the full prohibition remains.',
      cuts=['(के रोज़ों)'])
field('muslim:2676','ur','companion_report_of_prophetic_two_fast_prohibition',
      'Aisha’s coherent short report explicitly supplies two fasts and the named days. Only the redundant restatement of that already supplied object remains context.',
      cuts=['( کے روزوں )'])

field('muslim:2681','hi','question_encounter_and_companion_affirmation_oath',
      'The source-named Muhammad ibn Abbad ibn Jafar asks Jabir during tawaf; Jabir affirms the Friday-fast question and swears by the Lord of the House. The oath is Jabir’s, not the Prophet’s.',
      start='हज़रत मुहम्मद बिन अब्बाद बिन जाफ़र')
field('muslim:2681','ur','question_encounter_and_companion_affirmation_oath',
      'Muhammad ibn Abbad ibn Jafar’s actual question encounter with Jabir includes the tawaf setting and Jabir’s affirmative oath. The Prophet prohibition is relayed through that own question/answer.',
      start='حضرت محمد بن عباد بن جعفر')

field('muslim:2697','hi','qualified_witness_report_of_woman_and_prophetic_replies',
      'The source defines the witness as Abdullah ibn Buraydah’s father without adding a full name. He reports the unnamed woman’s maid/inheritance, one-month fasting and Hajj questions and the actual Prophet replies, retaining the mother and maid referent restrictions.',
      start='कहा: एक बार मैं',retained=['(वालिदा)','(लौंडी)'])
field('muslim:2697','ur','qualified_witness_report_of_woman_and_prophetic_replies',
      'The own source-defined father reports the woman’s complete exchange. Preserve the competing mother/maid referents, the one-month and never-Hajj conditions, and the original unclosed final quotation.',
      start='کہا : ایک بار میں',retained=['( والدہ )','( لونڈی )'],
      annotations=[qualification('The final source quotation is unclosed. No closing delimiter or omitted wording is supplied.')])

field('muslim:2698','hi','qualified_finite_sitting_encounter_fragment',
      'The source-defined father actually reports sitting beside the Prophet. Only that supplied finite encounter is selected; the omitted narrative and isolated two-month nominal variant remain context without an inferred obligation or question.',
      start='कहा: मैं रसूल',end='...',
      annotations=[qualification('The nominal two-month variant and its missing predicate are preserved in context. No woman, debt or request is borrowed from2697.')])
field('muslim:2698','ur','qualified_finite_sitting_encounter_fragment',
      'The own father-framed first-person sitting event is supplied. The later ellipsis, report comparison and nominal two-month wording do not supply an independent predicate and remain exact source context.',
      start='کہا : میں رسول',end='۔ ۔ ۔',
      annotations=[qualification('The omitted narrative and open nominal variant are not completed from another occurrence or language.')])

field('muslim:2699','hi','qualified_finite_woman_arrival_fragment',
      'The source-defined father supplies only the finite arrival of an unnamed woman before the Prophet. Its missing dialogue and isolated one-month nominal variant are not reconstructed.',
      start='कहा: एक औरत',end='...')
field('muslim:2699','ur','qualified_finite_woman_arrival_fragment',
      'The own route-defined father reports an unnamed woman’s arrival. The ellipsis, previous-report comparison and nominal month phrase remain source context without an inferred fasting obligation.',
      start='کہا : ایک عورت',end='۔ ۔ ۔')

field('muslim:2701','hi','qualified_finite_woman_arrival_fragment',
      'The Hindi route defines the reporting father through its printed सुलैमान बिन बुरैदाह. Only the woman’s actual arrival is supplied; no missing dialogue, month-debt predicate or outside identity is added.',
      start='कहा: रसूल अल्लाह',end='...')
field('muslim:2701','ur','qualified_finite_woman_arrival_fragment',
      'The Urdu source actually prints سلیمان بن بریرہ in its route; the final reporter is qualified only as that source-defined father. The woman-arrived clause remains, while the absent continuation and nominal month phrase remain context.',
      start='کہا : رسول اللہ',end='۔ ۔ ۔ ۔',
      annotations=[qualification('The printed Urdu بریرہ remains uncorrected. Neither the Hindi name nor an external familiar form replaces it.')])

field('ibnmajah:2664','hi','companion_report_of_prophetic_historical_judgment',
      'Abdullah ibn Amr ibn al-As reports the supplied intentional slave killing, hundred lashes and share cancellation. Hindi’s missing exile and Muslim-shares qualification are not inserted from Urdu; its defective spelling and join remain exact.',
      annotations=[qualification('The Hindi source omits the one-year exile and Muslims qualifier found in Urdu; it prints घुलम. All own wording and omissions remain.')])
field('ibnmajah:2664','ur','companion_report_of_prophetic_historical_judgment',
      'The own Abdullah ibn Amr report explicitly supplies the intentional killing, hundred lashes, one-year exile and cancelled share among Muslims. Those Urdu-only details are preserved here without repairing Hindi.')

field('ibnmajah:2671','hi','companion_father_son_encounter_and_prophetic_reply',
      'The source-named Khushkhash Anbari reports his visit with his son and the Prophet’s reciprocal statement; both participant directions and both negative scopes remain.')
field('ibnmajah:2671','ur','companion_father_son_encounter_and_prophetic_reply',
      'The own خشخاش عنبری report gives his son’s presence and the explicit reciprocal reply, without expanding the statement into a new legal ruling.')

field('ibnmajah:2675','hi','companion_report_of_prophetic_decision_with_lexical_interruption',
      'Ubadah ibn Samit explicitly reports the actual decision clauses before and after an unassigned dictionary explanation. The printed कान, repeated well clause and animal-subject restriction remain; the lexicon block supplies no separate attributed report.',
      segments=[part(end="और 'अजमा'"),part('कुआँ बेकार ओ रायगाँ है, और बेज़ुबान')],
      retained=['(जानवर)'],annotations=[qualification('The printed term कान and the repeated well clause remain exactly as supplied; no canonical wording or missing legal condition is substituted.')])
field('ibnmajah:2675','ur','companion_report_of_prophetic_decision_with_lexical_interruption',
      'The own Ubadah report supplies actual decision clauses around the explanatory عجماء/جبار definitions. Preserve the repeated well and animal-subject scope, separating only the lexical block and final numeric footnote glyph.',
      segments=[part(end='اور «عجماء»'),part('کنواں بیکار و رائیگاں ہے، اور بےزبان')],
      cuts=['۱؎'],retained=['( جانور )'])

field('ibnmajah:2679','hi','qualified_transmitted_mutilation_and_release_report',
      'The source-named Salamah ibn Ruh ibn Zanba relates the printed third-person arrival, prior act and the Prophet’s release of the slave because of mutilation. No fuller identity is inferred; the body retains its actual causal scope.',
      cuts=['(नाक, कान या कोई उज़ू काट देना)'])
field('ibnmajah:2679','ur','qualified_transmitted_mutilation_and_release_report',
      'The own سلمہ بن روح بن زنباع report preserves its third-person framing, actual acts and stated reason for release. The nose/ear/organ phrase defines a term; it is not asserted as additional injuries in this incident.',
      cuts=['( ناک کان یا کوئی عضو کاٹ دینا )'])

assert len(READINGS)==18 and sum(len(fields) for fields in READINGS.values())==36
