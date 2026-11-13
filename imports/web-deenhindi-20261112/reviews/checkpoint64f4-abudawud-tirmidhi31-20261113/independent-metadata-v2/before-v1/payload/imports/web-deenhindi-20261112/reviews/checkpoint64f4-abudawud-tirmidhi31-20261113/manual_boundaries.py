"""Explicit source boundaries authored after the complete65-field own reading pass."""
from source_first_notes import NOTES

records=[]

def omit(text,reason):
    return {'text':text,'expected_count':1,'reason':reason}

def foot(text):
    return omit(text,'Exact numbered source footnote marker; the full source and note remain context.')

def pair(key,kind,hi_speaker,ur_speaker=None,starts=(None,None),ends=(None,None),cuts=((),())):
    fields={}
    for language,speaker,start,end,omissions in zip(('hi','ur'),(hi_speaker,ur_speaker or hi_speaker),starts,ends,cuts,strict=True):
        fields[language]={'action':'excerpts','reason':NOTES[(key,language)],'report_type':kind,'speaker':speaker,
            'spans':[{'from':start,'to':end,'component_id':'reported-account','report_type':kind,'speaker':speaker,
                      'source_report_family_id':key+':'+language+':source-numbered-account'}],
            'omit_source_context':list(omissions)}
    row={'key':key,'decision':'register','reason':'The actually read own fields supply the selected finite report or expressly transmitted variant under their own attribution. Missing links, unnamed actors, source defects and all apparatus remain preserved; no canonical identity or absent wording is supplied.','fields':fields}
    records.append(row)
    return row

def segment(start,end,cid,kind,speaker,family):
    return {'from':start,'to':end,'component_id':cid,'report_type':kind,'speaker':speaker,'source_report_family_id':family}

pair('abudawud:2705','unnamed_companion_journey_and_prophetic_response_with_wording_uncertainty',
     'An unnamed Ansari reports the journey, goats, pots, bow and actual response. Both alternative carrion/loot comparisons remain as uncertainty within one transmitted account; no narrator name is supplied.',
     ends=(None,'یہ شک ہناد'))

r=pair('abudawud:2707','historical_encounter_with_separately_voiced_companion_report',
     'Abd al-Rahman ibn Ghanm’s Qinnasrin account and his meeting with Muadh precede Muadh’s distinct Khaybar report. The two historical events retain separate report families within this one source occurrence.',
     ends=(None,'۱؎'))
for language,marker,end in [('hi','तो आप ने कहा:',None),('ur','تو آپ نے کہا:','۱؎')]:
    r['fields'][language]['spans']=[
        segment(None,marker,'ibn-ghanm-siege-and-meeting','named_historical_siege_and_reception_account','Ibn Ghanm reports his siege/distribution and subsequent meeting with Muadh; this first event is not relabelled a Prophetic eyewitness account.','abudawud:2707:'+language+':qinnasrin-and-meeting'),
        segment(marker,end,'muadh-embedded-khaybar-report','companion_report_of_prophetic_khaybar_distribution','Muadh’s reply supplies his own Khaybar participation and the Messenger’s reported goat distribution, distinct from the preceding Qinnasrin event.','abudawud:2707:'+language+':muadh-khaybar-account'),
    ]

records.append({'key':'abudawud:2720','decision':'exclude',
    'reason':'All five complete own fields were read. They supply only the transmission route or same-as-above pointer, including the Arabic asking/relating verbs within that route, without the referenced report body. Preserve the complete numbered source occurrence as source-only context; no narration or missing matn is created.',
    'fields':{language:{'action':'source_context','reason':NOTES[('abudawud:2720',language)]} for language in ('ar','hi','ur','ur-Latn','en')}})

r=pair('abudawud:2722','companion_sword_allocation_report_with_qualified_appended_clause',
     'The source-named Abdullah reports receiving Abu Jahl’s sword as nafl on Badr day. The appended third-person killing clause remains finite supplied wording with its pronouns unresolved externally.',
     ends=(None,'۱؎'))
for language,marker,end in [('hi','और उन्होंने ही',None),('ur','اور انہوں نے ہی','۱؎')]:
    family='abudawud:2722:'+language+':source-numbered-account'
    r['fields'][language]['spans']=[
        segment(None,marker,'sword-allocation-report','companion_report_of_prophetic_sword_allocation','Abdullah’s own report attributes giving him Abu Jahl’s sword as nafl on Badr day to the Messenger; the source name and scope stay exact.',family),
        segment(marker,end,'appended-third-person-killing-clause','source_appended_finite_clause_with_unresolved_pronoun','The source appends a finite third-person killing clause. Preserve its actual pronouns without assigning the actor from a different edition or converting it to first-person testimony.',family),
    ]

pair('abudawud:2725','companion_arrival_and_spoils_allocation_report',
     'Abu Musa reports the arrival from the source-printed Habasha origin, Khaybar meeting, spoils allocation/giving alternative, participation restriction and ship-group/Jafar exception. Both parenthetical origin/property-source scopes remain qualified source rendering.',
     ends=(None,'۱؎'))

r=pair('abudawud:2729','grandmother_expedition_report_and_later_reception_dialogue',
     'The source-identified grandmother supplies the six-women expedition and allocation; Hashraj’s later question and her dates answer retain their own reception-scene voices. Her parenthetical source identity remains, without an external genealogy.',
     ends=(None,'۱؎'))
for language,marker,end in [('hi','हशराज बिन ज़ियाद कहते हैं:',None),('ur','حشرج بن زیاد کہتے ہیں:','۱؎')]:
    r['fields'][language]['spans']=[
        segment(None,marker,'grandmother-expedition-account','named_grandmother_report_of_prophetic_expedition_dialogue','The source’s Umm Ziyad grandmother reports the six women, summons, actual questions/replies, services and Khaybar allocation. Her account is not Hashraj’s eyewitness claim.','abudawud:2729:'+language+':grandmother-khaybar-account'),
        segment(marker,end,'hashraj-share-question-and-reply','named_reporter_reception_question_with_grandmother_reply','Hashraj explicitly asks his grandmother what the share was; her finite dates reply is preserved as later reception dialogue, not a new Prophet statement.','abudawud:2729:'+language+':share-reception-dialogue'),
    ]

pair('abudawud:2732','companion_report_of_prophetic_encounter_reply',
     'Aisha supplies the unnamed participant’s arrival and purpose of joining the fight, with the actual return/no-help reply. The campaign and individual identity are not invented.')
pair('abudawud:2734','source_qualified_companion_allocation_report',
     'The source’s printed Abu-Umra/father/Abd-al-Rahman genealogy remains qualified and uncorrected. The report supplies four men, one horse and the one-each/two-horse distribution exactly.')
pair('abudawud:2741','companion_army_and_detachment_allocation_report',
     'Ibn Umar’s Hindi report supplies the dispatch, detachment and twelve-plus-one/thirteen amounts, with its damaged recipient/conjunction join left unchanged and no Urdu wording inserted.',
     'Ibn Umar’s own Urdu distinguishes the army’s twelve-camel shares and the detachment’s extra one, giving thirteen. The groups, purpose and numbers remain exact.')
pair('abudawud:2743','companion_expedition_bonus_and_later_distribution_report',
     'Ibn Umar supplies the commander’s initial one-camel bonus and the later twelve-after-khums distribution, non-counting/non-reproach and thirteen total; no giver is harmonized with another occurrence.',
     starts=('इब्न उमर','ابن عمر'),cuts=([],[foot('۱؎')]))

r=pair('abudawud:2745','companion_allocation_report_with_explicit_passive_variant',
     'The main Ibn Umar account names the Messenger as bonus giver. The separately transmitted passive variant supplies an actual one-camel allocation with no giver named; it is not completed from the main account.',
     starts=('अब्दुल्लाह बिन उमर','عبداللہ بن عمر'),ends=('अबू दाऊद कहते हैं:','ابوداؤد کہتے ہیں:'))
for language,start,mainend,vstart,vend in [
    ('hi','अब्दुल्लाह बिन उमर','अबू दाऊद कहते हैं:','हमें एक-एक ऊंट बतौर-ए-नफ़ल दिए गए','और उन्होंने नबी अकरम'),
    ('ur','عبداللہ بن عمر','ابوداؤد کہتے ہیں:','ہمیں ایک ایک اونٹ بطور نفل دئیے گئے','اور انہوں نے نبی اکرم')]:
    family='abudawud:2745:'+language+':source-numbered-account'
    r['fields'][language]['spans']=[
        segment(start,mainend,'main-allocation-account','companion_report_of_prophetic_expedition_allocation','Ibn Umar’s main source report explicitly attributes the dispatch and one-camel bonus to the Messenger alongside the twelve-camel share.',family),
        segment(vstart,vend,'alternate-passive-bonus-wording','explicit_transmitted_passive_allocation_variant','Abu Dawud quotes actual alternate-version wording that we were each given a camel as nafl. Its giver remains unnamed; route comparison and omitted-Prophet criticism stay context.',family),
    ]

pair('abudawud:2755','companion_prayer_scene_with_prophetic_spoils_statement',
     'Amr ibn Abasa supplies the camel-facing prayer, after-salam hair-taking and reported statement with its khums exception/return clause. All quantities and sequence remain source-bound.',
     ends=(None,'۱؎'))
r=pair('abudawud:2775','companion_journey_observation_with_prophetic_explanation',
     'The source names only Saad. His travel/supplication/prostration observations and the Messenger’s supplied three-thirds explanation remain distinct voices in one account; no fuller name or missing Hindi detail is inserted.',
     cuts=([],[foot('۱؎')]))
for language,marker in [('hi','और फरमाया:'),('ur','اور فرمایا:')]:
    family='abudawud:2775:'+language+':source-numbered-account'
    r['fields'][language]['spans']=[
        segment(None,marker,'saad-travel-and-prayer-observation','companion_journey_and_prayer_observation','The source-named Saad supplies the Mecca-to-Medina journey, location and his own repeated prayer/prostration observations, without an externally expanded identity.',family),
        segment(marker,None,'reported-three-thirds-explanation','reported_prophetic_explanation_of_supplication_and_prostration','The source explicitly attributes the following first-person three-thirds explanation to the Messenger. Preserve the reported claims and quantities without adding an independent historical certification.',family),
    ]

pair('tirmidhi:2711','companion_debt_visit_and_prophetic_identity_reply',
     'Jabir’s father-debt visit and actual identity exchange include the parenthetic questioning predicate as qualified source-rendered reply scope, without a verbatim historical parenthesis claim.',
     ends=('इमाम तिरमिधि कहते हैं:','امام ترمذی کہتے ہیں:'),cuts=([],[foot('۱؎')]))

r=pair('tirmidhi:2715','companion_learning_account_with_transmitted_language_variant',
     'Zayd supplies the writing-learning commission, stated explanation, less-than-half-month learning and letter service. The later Syriac-learning command is actual separately transmitted wording of the commission, not a replacement or a new event.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','امام ترمذی کہتے ہیں:'),
     cuts=([omit('(तहरीर)','Lexical writing synonym for the contextual kitab term, retained separately from the actual letter-service account.')],[omit('( تحریر )','Lexical writing synonym for the contextual kitab term; the actual letter-service event remains.'),foot('۱؎')]))
for language,mainend,vstart in [('hi','इमाम तिर्मिज़ी कहते हैं:','वह कहते हैं:'),('ur','امام ترمذی کہتے ہیں:','وہ کہتے ہیں:')]:
    family='tirmidhi:2715:'+language+':writing-learning-commission'
    r['fields'][language]['spans']=[
        segment(None,mainend,'zayd-learning-and-letter-service','companion_learning_and_letter_service_report','Zayd narrates the commission, stated reason, learning duration and subsequent writing/reading service in the actual main source wording.',family),
        segment(vstart,None,'transmitted-syriac-learning-command','explicit_transmitted_language_commission_variant','The source’s alternate route explicitly relays Zayd’s finite Syriac-learning command. Retain it as transmitted variant wording without choosing it over the main field or inventing another learning incident.',family),
    ]

r=pair('tirmidhi:2717','relayed_companion_encounter_and_written_letter_excerpt',
     'Ibn Abbas relays Abu Sufyan’s merchant/Heraclius encounter and letter-reading event. The letter excerpt and source rendering remain bounded written contents; title biography, lexical notes, omitted-remainder marker and compiler apparatus remain context.',
     ends=('... अलख','… الخ'),
     cuts=([omit('(शाहनशाह-ए-शाम)','Background title apposition to the already named Heraclius; the actor and actual letter title remain.'),omit('(बड़ा मेहरबान)','Explicit lexical synonym of Rahman within the supplied rendering; the divine name remains.'),omit('(निहायत रहम करने वाला)','Explicit lexical synonym of Rahim within the supplied rendering; the divine name remains.')],
           [omit('( شہنشاہ شام )','Background title apposition to already named Heraclius; preserve the actual recipient title in the quoted letter.'),omit('( بڑا مہربان )','Explicit lexical synonym of Rahman; the quoted formula and main rendering remain.'),omit('( نہایت رحم کرنے والا )','Explicit lexical synonym of Rahim; the quoted formula and main rendering remain.')]))
for language,marker,end in [('hi','उस में लिखा था:','... अलख'),('ur','اس میں لکھا تھا','… الخ')]:
    family='tirmidhi:2717:'+language+':heraclius-letter-reading'
    r['fields'][language]['spans']=[
        segment(None,marker,'abu-sufyan-encounter-and-reading-frame','relayed_companion_encounter_and_letter_reading_report','Ibn Abbas expressly relays Abu Sufyan’s merchant-group encounter, summons, reporter continuation and letter-reading event; these are not words written in the letter.',family),
        segment(marker,end,'bounded-letter-contents-and-rendering','reported_prophetic_letter_excerpt_with_source_rendering','The source attributes this bounded written letter excerpt to Muhammad and supplies its own translation. Preserve actual sender/recipient/greeting wording without reconstructing the omitted remainder.',family),
    ]

pair('tirmidhi:2718','companion_letter_seal_ring_and_observation_report',
     'Anas reports the intended foreign kings, seal requirement, ring made for that purpose and his printed palm/shine observation. Recipient and purpose parentheses remain qualified source scope; the damaged observation join is not repaired.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','امام ترمذی کہتے ہیں:'))
pair('tirmidhi:2720','companion_greeting_and_nonresponse_event_report',
     'Ibn Umar supplies the unnamed greeting, urination circumstance and lack of response. No broader rule or missing actor identity is added.')
pair('tirmidhi:2722','companion_greeting_encounter_and_prophetic_correction',
     'Jabir ibn Sulaym supplies the actual greeting, its source rendering and the corrected form. Preserve Hindi’s own plural ending without replacing it from Urdu; the unprinted long story remains absent.',
     'The own Urdu greeting/correction has the printed singular السلام علیک form. Preserve it and its rendering without harmonizing the Hindi or a familiar external formula.',
     ends=('और आगे','اور آگے'))
pair('tirmidhi:2725','companion_group_seating_practice_report',
     'Jabir ibn Samurah describes his group’s actual practice of sitting where space was available on coming to the Prophet; this is not relabelled a direct Prophetic seating command.',
     ends=('इमाम तिरमिधि कहते हैं:','۱؎'))
pair('tirmidhi:2728','companion_report_of_meeting_gesture_questions_and_replies',
     'Anas supplies an unnamed questioner’s three questions and the reported replies. Hindi’s defective बॉस and मुस्तफ़ा remain exact; the final sufficiency predicate remains qualified source rendering, not independently certified verbatim wording.',
     'Anas’s own Urdu preserves the three questions, alternatives and replies, including the source-rendered only-this-is-enough qualification. It does not repair the differing Hindi action words.',
     ends=('इमाम तिरमिधि कहते हैं:','۱؎'))
pair('tirmidhi:2732','companion_arrival_observation_and_greeting_action_report',
     'Aisha’s actual scene and own oath/observation remain distinguished from the Messenger’s movements. The at-that-time and advancing parentheses are source-rendered temporal/action scope, without additional inferred circumstances.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','امام ترمذی کہتے ہیں:'),cuts=([],[foot('۱؎')]))

hi_enum=[omit('('+str(n)+')','Printed list enumeration marker; retain the actual instruction and the separately printed nine quantity.') for n in range(1,10)]
ur_enum=[omit('( '+n+' )','Printed list enumeration marker; the actual instruction and explicit nine quantity remain.') for n in '۱۲۳۴۵۶۷۸۹']
r=pair('tirmidhi:2733','companion_encounter_with_distinct_quoted_dialogue_voices',
     'Safwan reports the two unnamed interlocutors, their actual question, the Messenger’s response/follow-up and their own claimed David-prayer/fear explanation. Material Musa-object and hearing scopes remain; the latter explanation is not promoted to Prophetic speech.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','امام ترمذی کہتے ہیں:'),
     cuts=(hi_enum+[omit('(सनीचर)','Lexical weekday synonym of the already supplied Sabbath term.'),omit('(पैरवी)','Lexical following synonym of the already supplied ittiba term.')],
           ur_enum+[omit('( سنیچر )','Lexical weekday synonym of the actual Sabbath term, retained in context.'),omit('( پیروی )','Lexical following synonym of the actual ittiba term, retained in context.')]))
r['fields']['hi']['reason']+=' The printed बेगाना word in the fifth item remains unchanged and is not normalized to Urdu’s بےگناہ wording.'
for language,answer,hearing,followup,last,end in [
    ('hi','आप ने उन से कहा','(आप का जवाब सुन कर)','आप ने फ़रमाया:','उन्होंने कहा: दाऊद','इमाम तिर्मिज़ी कहते हैं:'),
    ('ur','آپ نے ان سے کہا','( آپ کا جواب سن کر )','آپ نے فرمایا:','انہوں نے کہا: داود','امام ترمذی کہتے ہیں:')]:
    family='tirmidhi:2733:'+language+':source-numbered-encounter'
    r['fields'][language]['spans']=[
        segment(None,answer,'interlocutors-visit-and-question','companion_report_of_interlocutor_exchange_and_question','Safwan reports the two unnamed men’s initial conversation, visit and nine-sign question; their private words retain their own speaker attribution.',family),
        segment(answer,hearing,'reported-answer-instructions','reported_prophetic_answer_with_source_rendered_scope','The source explicitly attributes this answer to the Messenger. Retain the actual instruction bodies and Sabbath qualification; enumeration labels are context.',family),
        segment(hearing,followup,'interlocutors-hearing-kiss-and-testimony','reported_interlocutor_response_and_testimony','The two interlocutors’ hearing, kiss and testimony remain their reported response, not a new Prophetic pronouncement.',family),
        segment(followup,last,'reported-followup-question','reported_prophetic_followup_question','The source attributes the following why-not-follow question to the Messenger within the same encounter.',family),
        segment(last,end,'interlocutors-own-prayer-and-fear-explanation','reported_interlocutor_explanation_with_embedded_historical_claim','The interlocutors state their own David-prayer assertion and fear. Preserve them as their reported explanation without independently certifying or attributing that claim to the Prophet.',family),
    ]

pair('tirmidhi:2734','companion_bathing_visit_and_identity_dialogue_report',
     'Umm Hani supplies the conquest-year visit, bathing/Fatima screen and actual greeting/identity/welcome exchange. The later full-story pointer supplies no continuation.',
     ends=('रावी कहते हैं','راوی کہتے ہیں'))
r=pair('tirmidhi:2738','named_narrator_sneeze_scene_and_companion_reply',
     'Nafi’s scene, the sneezer’s utterance/rendering and Ibn Umar’s actual response retain distinct voices. Literal Hindi HTML entities and defects remain unchanged; whole-formula translations are supplied content.',
     'The source preserves Nafi’s scene, the actual sneezer formula and Ibn Umar’s reply with its negative taught-us contrast and differently taught formula. The whole-utterance renderings remain source content.',
     ends=('इमाम तिरमिधि कहते हैं:','امام ترمذی کہتے ہیں:'),cuts=([],[foot('۱؎'),foot('۲؎')]))
for language,marker,end in [('hi','इब्न उमर (रज़ियल्लाहु अन्हुमा) ने कहा:','इमाम तिरमिधि कहते हैं:'),('ur','ابن عمر رضی الله عنہما نے کہا:','امام ترمذی کہتے ہیں:')]:
    family='tirmidhi:2738:'+language+':source-numbered-encounter'
    r['fields'][language]['spans']=[
        segment(None,marker,'nafi-sneezer-observation','named_narrator_report_of_sneezer_utterance','Nafi reports the unnamed sneezer’s utterance; the formula and source rendering belong to that man’s actual reported speech.',family),
        segment(marker,end,'ibn-umar-reply-and-taught-formula','companion_reply_relaying_prophetic_instruction','Ibn Umar’s actual reply includes what he too could say, the negative taught-us statement and the reported taught formula. It is not all direct Prophet speech.',family),
    ]
pair('tirmidhi:2739','companion_report_of_expected_and_actual_sneeze_responses',
     'Abu Musa distinguishes the hoped-for formula from the actual response. Both renderings remain, and the source’s on-this-occasion-only parenthesis materially limits the actual reply without a verbatim-historical claim.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','۱؎'))
pair('tirmidhi:2743.4','explicit_third_occasion_reply_variant_with_honorific_frame',
     'The transmitted variant supplies a third-occasion reply by the source’s honorific-marked आप to an unnamed recipient. No personal speaker name, earlier exchange or missing sneeze story is filled from another occurrence.',
     'The own variant supplies the honorific-marked آپ, third occasion and finite cold reply. Keep this source-framed attribution without an externally supplied name or omitted prior exchange.',
     starts=('आप (सल्लल्लाहु अलैहि वसल्लम) ने तीसरी बार','آپ (صلی اللہ علیہ وسلم) نے تیسری بار'),
     ends=('(इस की ताअ़ीद','(اس کی تائید'))
pair('tirmidhi:2748','source_relative_reporter_relay_of_prophetic_saying',
     'The source names only Thabit’s father as reporter and expressly supplies a Prophet-said frame for the prayer-context list. The compiler’s narrator-name discussion is not used to fill that identity.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','امام ترمذی کہتے ہیں:'))
r=pair('tirmidhi:2753','source_qualified_sitting_event_and_reported_statement',
     'Abu Mijla’s Hindi supplies the sitting event and a statement according to Muhammad, but lacks Urdu’s Hudhayfa speaker link. Keep that gap explicit and do not import the missing intermediary.',
     'The own Urdu names Abu Mijlaz for the sitting event and Hudhayfa for the reply relaying Muhammad’s statement. Those actual source voices remain distinct.',
     ends=('इमाम तिरमिधि कहते हैं:','امام ترمذی کہتے ہیں:'),
     cuts=([omit('(सर्किल)','Lexical circle synonym of the already supplied halqa term.')],[omit('( دائرہ )','Lexical circle synonym of the already supplied halqa term.'),foot('۱؎')]))
for language,marker,end in [('hi','मुहम्मद (सल्लल्लाहु अलैहि वसल्लम) के फ़रमान','इमाम तिरमिधि कहते हैं:'),('ur','تو حذیفہ نے کہا:','امام ترمذی کہتے ہیں:')]:
    family='tirmidhi:2753:'+language+':source-numbered-encounter'
    r['fields'][language]['spans']=[
        segment(None,marker,'reported-circle-sitting-event','named_source_report_of_sitting_event','The source-named reporter supplies the unnamed man’s finite sitting-in-the-circle event; preserve the actual spelling and missing links.',family),
        segment(marker,end,'source-attributed-statement',
                'indirect_prophetic_statement_with_unprinted_intermediary' if language=='hi' else 'companion_reply_relaying_prophetic_statement',
                'The Hindi source says according to Muhammad but does not name the person pronouncing this statement; Hudhayfa is not supplied from Urdu.' if language=='hi' else 'The Urdu expressly attributes this reply to Hudhayfa, who relays Muhammad’s statement; the actual speaker link is preserved.',family),
    ]
pair('tirmidhi:2759','companion_report_of_passively_stated_grooming_limit',
     'Anas reports that the four-practice limit was prescribed for us, with the no-more-than-forty-days scope. This own passive field does not name its prescriber and is not relabelled a direct Prophet quotation.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','۱؎'))
pair('tirmidhi:2769','companion_question_sequence_with_reported_prophetic_replies',
     'Muawiya ibn Hayda’s three questions and reported replies retain every spouse/bondwoman exception, among-others condition and alone response. Compiler genealogy and route discussion do not add identities or new report bodies.',
     ends=('इमाम तिरमिधि कहते हैं:','امام ترمذی کہتے ہیں:'))

assert len(records)==31 and sum(len(r['fields']) for r in records)==65
