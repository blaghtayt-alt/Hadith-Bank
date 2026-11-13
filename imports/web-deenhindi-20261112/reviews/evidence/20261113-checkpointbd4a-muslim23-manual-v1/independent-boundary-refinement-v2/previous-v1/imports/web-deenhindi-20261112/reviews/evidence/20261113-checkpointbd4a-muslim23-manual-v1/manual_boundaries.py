"""Explicit own-field boundaries after the frozen49 complete original readings."""
from manual_source_first_readings import NOTES

READINGS = {}

def field(number, language, report_type=None, speaker=None, cuts=(), segments=None,
          exact=None, context_all=False, retained=()):
    key='muslim:'+number
    assert ('deenhindi-'+key,language) in NOTES
    assert language not in READINGS.setdefault(key,{})
    READINGS[key][language]={'note':NOTES['deenhindi-'+key,language],
        'type':report_type,'speaker':speaker,'context':list(cuts),'context_all':context_all,
        'source_report_family_id':key+':source-numbered-report',
        'retained_meaningful_structures':list(retained)}
    if segments is not None:READINGS[key][language]['segments']=segments
    if exact is not None:READINGS[key][language]['exact_selections']=exact

def part(start=None,end=None,component='report-1',report_type=None,speaker=None):
    result={'start':start,'end':end,'id':component}
    if report_type:result['type']=report_type
    if speaker:result['speaker']=speaker
    return result

field('2403','hi','qualified_prophetic_pledge_dialogue',
    'The damaged Abu Muslim route leaves the ultimate Hindi reporter unnamed. The actual Messenger invitation and answer remain supplied, without importing Awf, the full group-count alternative or obedience term.',
    segments=[part(end='इस के बाद मैं ने',component='pledge-dialogue'),
      part(start='इस के बाद मैं ने',component='later-whip-observation',report_type='qualified_reporter_personal_observation',
           speaker='The source’s unnamed ultimate first-person reporter describes the later whip incident; these are not additional words spoken by the Prophet.')])
field('2403','ur','prophetic_pledge_dialogue_in_named_reporter_frame',
    'Abu Muslim’s supplied route identifies Awf ibn Malik as the reporter of the nine/eight/seven group and actual Messenger pledge; its complete terms and uncertainty remain.',
    cuts=['( شخص )','( حاضر )'],retained=['( ایک بار )'],
    segments=[part(end='اس کے بعد میں نے',component='pledge-dialogue'),
      part(start='اس کے بعد میں نے',component='awf-later-whip-observation',report_type='companion_personal_observation',
           speaker='Awf ibn Malik’s first-person narrative reports the later whip incident; it is not another Prophetic instruction.')])

field('2404','hi','companion_request_and_prophetic_conditional_reply',
    'Qabisah ibn Mukhariq al-Hilali reports his actual undertaking/request and the Messenger’s three delimited cases, with all stop conditions and alternative livelihood wording retained.')
field('2404','ur','companion_request_and_prophetic_conditional_reply',
    'Qabisah supplies the undertaking and actual request/reply. The purpose of his undertaking, the asking-object of stopping and the witnesses’ say-it predicate remain explicit source scope.',
    retained=['( لوگوں کے معاملات میں اصلاح کے لئے )','( سوال سے )','( اور کہہ دیں )'])

field('2409','hi','abbreviated_companion_administrative_report',
    'Ibn Saadi expressly reports Umar appointing him as charity collector. The absent continuation and Layth-route comparison are not supplied as matn.',
    segments=[part(end='... (आगे)',component='appointment-fragment')])
field('2409','ur','abbreviated_companion_administrative_report',
    'Ibn Saadi’s actual first-person appointment by Umar is supplied; it is not a Prophetic saying, and the pointed-to continuation remains absent.',
    segments=[part(end=' ۔ ۔ ۔ ( آگے )',component='appointment-fragment')])

field('2419','hi','companion_address_with_qualified_recitation_recollection',
    'The father of Abu Harb ibn Abi al-Aswad reports Abu Musa’s gathering/address and claims of remembered recitation. The quoted fragments are preserved as Abu Musa’s source-supplied recollection, without certifying canonical Quran status or filling forgotten text.',
    cuts=['(अबू मूसा रज़ियल्लाहु अन्हु)','(का वक़्फ़ा)','(डराने की)','(सूरह)'],
    retained=['(उन्हें बुलाने के लिए क़ासिद)'],
    segments=[part(end='अगर आदम के बेटे',component='gathering-address-and-memory-frame'),
      part(start='अगर आदम के बेटे',end='हम एक और सूरत',component='first-recalled-passage',report_type='source_claimed_remembered_recitation_fragment',
           speaker='Abu Musa quotes what he says he remembers of an otherwise forgotten recited passage. No external canonical identity or ultimate-speaker certification is asserted.'),
      part(start='हम एक और सूरत',end="'ऐ ईमान वालो!",component='second-memory-frame',report_type='companion_recitation_memory_testimony',
           speaker='Abu Musa states his own second recollection and forgetting limit.'),
      part(start="'ऐ ईमान वालो!",component='second-recalled-passage',report_type='source_claimed_remembered_recitation_fragment',
           speaker='The actual quoted reminder is the passage Abu Musa says remains in his memory; no missing words or canonical verse mapping are added.')])
field('2419','ur','companion_address_with_qualified_recitation_recollection',
    'Abu Musa’s actual address and first-person recitation/memory claims are supplied through the named father-of-Abu-Harb route. The recalled wording stays qualified as this source’s testimony, not a new independently certified Quran quotation.',
    cuts=['( ابو موسیٰ رضی اللہ تعالیٰ عنہ )','( کا وقفہ )','( ڈرا نے کی )','( سورہ )'],
    retained=['( انھیں بلا نے کے لیے قاصد )'],
    segments=[part(end='آگر آدم کے بیٹے',component='gathering-address-and-memory-frame'),
      part(start='آگر آدم کے بیٹے',end='ہم ایک اور سورت',component='first-recalled-passage',report_type='source_claimed_remembered_recitation_fragment',
           speaker='Abu Musa supplies this actual remembered fragment while expressly saying the rest was forgotten. The source spelling and unknown external identity remain untouched.'),
      part(start='ہم ایک اور سورت',end='" اے ایمان والو!',component='second-memory-frame',report_type='companion_recitation_memory_testimony',
           speaker='Abu Musa gives his own second recollection and forgetting limitation.'),
      part(start='" اے ایمان والو!',component='second-recalled-passage',report_type='source_claimed_remembered_recitation_fragment',
           speaker='This is the actual fragment Abu Musa says he remembers; the unclosed quotation and absent remainder are preserved without outside supplementation.')])

field('2424','hi','prophetic_giving_and_sayings_report',
    'Abu Said reports the actual repeated requests/gifts and Messenger sayings, retaining the positive distribution predicate and asking-restraint scope in their supplied speech.',
    cuts=['(बे-नियाज़ी)','(की कुव्वत)'],retained=['(तुमी में बांट दूंगा)','(सवाल से बाज़ रहेगा)'])
field('2424','ur','prophetic_giving_and_sayings_report',
    'Abu Said’s own report supplies the complete negative storing predicate, positive distribution speech and asking-restraint qualification. The malformed outer delimiter and literal قناعت wording are not repaired.',
    cuts=['( بے نیازی )','( کی قوت )',{'start':368,'end':369,'text':'('}],
    retained=['( تمھی میں بانٹ دو ں گا )','( سوال سے باز رہے گا )'])

field('2428','hi','companion_objection_and_prophetic_reply',
    'Umar’s objection concerns the actual named-by-scope gift recipients; the Messenger supplies the two alternatives and refusal to be miserly.',
    cuts=['(बे-जा इसरार)'],retained=['(जिन्हें आपने अता फरमाया)'])
field('2428','ur','companion_objection_and_prophetic_reply',
    'Umar’s actual objection and the Messenger’s alternative/negative reply retain the recipient comparison group; the manner synonym remains context.',
    cuts=['( بے جا اصرار )'],retained=['( جنھیں آپ نے عطا فر ما یا )'])

field('2429','hi','qualified_abbreviated_prophetic_action_report',
    'Anas is named in the damaged Hindi route. The cloak pull, mark, demand and Messenger turning are supplied; the missing walk, laugh and giving order are not imported.',cuts=['(देहाती)'])
field('2429','ur','companion_witness_of_prophetic_encounter',
    'Anas supplies the full own walk/pull/demand/turn/laugh/giving account. The shoulder location and grasping action remain actual event scope.',
    retained=['( کے کندھوں )','( پکڑ کر )'])

field('2431','hi','companion_family_dialogue_and_prophetic_gift_report',
    'Miswar recounts Makhromah’s actual request and the Messenger’s reserved-cloak reply and satisfaction statement; the garment synonym is context.',cuts=['(चोग़े)'])
field('2431','ur','companion_family_dialogue_and_prophetic_gift_report',
    'The supplied Layth/Abdullah route reaches Miswar’s actual father/son encounter and the Messenger’s reserved-cloak reply. Shoulder location remains, while the repeated plural garment label is context.',
    cuts=['( قباؤں )'],retained=['( عبد اللہ )','( کے کندھے )'])
field('2432','hi','companion_witness_of_prophetic_gift_report',
    'Miswar reports his father’s request, voice recognition, showing of the garment and both repeated reserved-for-you statements; this source occurrence stays separate from2431.')
field('2432','ur','companion_witness_of_prophetic_gift_report',
    'Miswar’s own source account supplies the request and repeated saying. The single-cloak object fixes the request’s supplied object and quantity without filling another field.',
    retained=['( کو ئی قباء )'])

field('2433','hi','qualified_prophetic_giving_dialogue',
    'The ultimate Hindi reporter is unnamed in its damaged route. The actual giving dialogue and believer/Muslim wording remain, with missing exchange links and fear wording unfilled.',
    cuts=['(इग्नोर)'],retained=['(देता हूँ)'])
field('2433','ur','companion_dialogue_with_prophetic_giving_explanation',
    'Saad through Amir reports the actual dialogue and Messenger’s giving explanation. The separate Halwani repetition-count comparison remains visible transmission criticism, without settling its two-versus-three disagreement.',
    segments=[part(end='اور حلوانی کی حدیث میں',component='giving-dialogue')],
    retained=['( پھر )','( دیتا ہوں )'])

field('2435','hi','qualified_transmitted_action_and_saying_fragment',
    'The later Muhammad-ibn-Saad route supplies actual Messenger hand action and an address to Saad. The unknown first-person addressee link is not expanded to make Muhammad an eyewitness; the omitted body remains absent.',
    segments=[part(start='रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने मेरी गर्दन',end=' (आगे',component='actual-added-action-and-address')])
field('2435','ur','qualified_transmitted_action_and_saying_fragment',
    'The source’s later route supplies this actual Messenger action, question and Saad address. Its first-person link remains unexpanded and its continuation unfilled.',
    segments=[part(start='تو رسول اللہ صلی اللہ علیہ وسلم نے میری گردن',end=' ( آگے',component='actual-added-action-and-address')])

field('2437','hi','qualified_companion_negative_statement_fragment',
    'Anas expressly says that we did not show patience. The circumstance and missing main story remain unknown; the youth noun-phrase comparison is not additional matn.',
    segments=[part(start='हज़रत अनस (रज़ियल्लाहु अन्हु) ने कहा:',end=' और उन्होंने',component='anas-negative-fragment')])
field('2437','ur','qualified_companion_setting_and_statement_fragments',
    'Anas’s source route supplies the Hawazin-fay conditional setting and a separate actual negative collective statement. Their missing main event and consequence are not invented.',
    cuts=['( زہری )','( قبیلہ )'],
    segments=[part(end=' ۔ ۔ ۔ اور اس',component='supplied-conditional-setting'),
      part(start='حضرت انس رضی اللہ تعالیٰ عنہ نے کہا : ہم نے صبر نہ کیا',end=' اور انہوں نے',component='anas-negative-fragment',
           report_type='companion_negative_statement_fragment',speaker='Anas supplies the actual we-did-not-show-patience clause; its omitted situation is not filled.')])

field('2438','hi','qualified_companion_report_of_group_saying',
    'Anas transmits the Ansar group’s actual future affirmative patience statement. Their source-supplied group identity remains; the absent story and route comparison stay context.',
    segments=[part(start='हज़रत अनस (रज़ियल्लाहु अन्हु) ने फरमाया:',end=' जिस तरह यूनुस',component='ansar-future-statement')],retained=['(अंसार)'])
field('2438','ur','qualified_companion_report_of_group_saying',
    'Anas expressly reports the Ansar’s supplied we-will-show-patience statement, without importing the missing surrounding event.',
    segments=[part(start='حضرت انس رضی اللہ تعالیٰ عنہ نے فرمایا :',end=' جس طرح یونس',component='ansar-future-statement')],retained=['( انصار )'])

field('2440','hi','qualified_historical_companion_dialogue_and_prophetic_reply',
    'Abu Tiyah’s abbreviated source route supplies the scene and Ansar/Prophet exchange; the absent ultimate Anas link and sword complaint are not imported.',
    segments=[part(end='(वह लोग झूठ नहीं बोलते थे)',component='gathering-and-group-answer'),
      part(start='(वह लोग झूठ नहीं बोलते थे)',end=443,component='reporter-truthfulness-characterization',
           report_type='qualified_narrator_characterization',speaker='The narrative voice in the abbreviated source route says the group did not lie. It is not the group’s own utterance or another Prophetic statement.'),
      part(start=443,component='prophetic-return-and-valley-reply',report_type='prophetic_reply_with_conditional_choice',
           speaker='The source explicitly introduces the Messenger’s return-with-him question and conditional valley choice.')],
    retained=['(वह लोग झूठ नहीं बोलते थे)'])
field('2440','ur','companion_dialogue_and_prophetic_reply',
    'Anas through Abu Tiyah reports the actual spoils scene and exchanges; source narrator characterization is separated from the direct speakers.',
    cuts=['( اس پر )'],retained=['( رسول اللہ صلی اللہ علیہ وسلم نے حنین کی )'],
    segments=[part(end='وہ لوگ جھوٹ نہیں بولتے تھے',component='gathering-and-group-answer'),
      part(start='وہ لوگ جھوٹ نہیں بولتے تھے',end='۔ آپ صلی اللہ علیہ وسلم نے فرمایا : " کیا تم',component='anas-truthfulness-characterization',
           report_type='companion_narrative_characterization',speaker='Anas’s narrative characterizes the group’s truthfulness; this is not another Prophetic utterance.'),
      part(start='۔ آپ صلی اللہ علیہ وسلم نے فرمایا : " کیا تم',end=' ( انصار سے بھی یہی توقع ہے',component='prophetic-return-and-valley-reply',
           report_type='prophetic_reply_with_conditional_choice',speaker='The actual Messenger reply is supplied. The later expectation-of-Ansar inference remains context.')])

field('2441','hi','abbreviated_companion_battle_and_prophetic_reply_report',
    'Anas through Hisham supplies this shorter Hunayn report, participant count, calls, distribution and reply. The extensive Urdu-only events and later eyewitness dialogue remain absent.')
field('2441','ur','companion_battle_report_with_later_witness_dialogue',
    'Anas supplies the full own Hunayn narrative with participant/time qualifications; Hisham’s later eyewitness question and Abu Hamzah’s reply are separate voices in the same report family.',
    cuts=['( اس پر )','( حضرت انس رضی اللہ تعالیٰ عنہ کی کنیت )'],
    retained=['( اپنے ساتھی )','( فتح مکہ کے موقع پر غلام بنانے کی بجائے )','( مہاجرین کے بعد انصار کو )','( اس وقت )','( فتح مکہ سے زرا قبل )','( فتح مکہ کے موقع پر )','( عینی )'],
    segments=[part(end='ہشام نے کہا میں نے پوچھا',component='hunayn-account'),
      part(start='ہشام نے کہا میں نے پوچھا',component='hisham-eyewitness-question',report_type='later_question_and_companion_witness_reply',
           speaker='Hisham asks Abu Hamzah about eyewitness presence and receives his actual reply. The source’s separate kunyah explanation identifies Anas, but no unprinted witness detail is supplied.')])

field('2442','hi','qualified_abbreviated_companion_battle_report',
    'The truncated Sumayt/Anas source supplies the six-thousand Ansar, calls, arrival then victory, forty-day siege and distribution. Missing locations and Urdu-only details are not inserted; the own arrival order remains literal.')
field('2442','ur','companion_battle_report_with_collective_transmission_qualification',
    'Anas’s own report explicitly qualifies parts by the participating group’s transmission. Preserve that limitation, actual participants, numbers and the victory-before-arrival wording, without harmonizing Hindi.',
    cuts=['( لڑنے والوں )'],
    retained=['( مقابلہ میں )','( انصار )','( مکہ کے نو مسلم )','( میرے اپنے مشاہدے کے علاوہ جنگ میں شریک لوگوں کی )','( کے حساب سے )'],
    segments=[part(end=' ۔ ۔ ۔ پھرحدیث کا باقی حصہ',component='actual-battle-and-distribution-report')])

field('2443','hi','companion_report_of_prophetic_gifts_and_complaint',
    'Rafi ibn Khadij supplies the actual gifts and Abbas’s complaint in verse, followed by completion of his hundred. The Hindi does not print the poem itself.',
    retained=['(अशआर में शिकायत की)'])
field('2443','ur','companion_report_with_actual_recipient_poem',
    'Rafi’s account includes the actual gifts and Abbas’s supplied poem. The poem belongs to Abbas as the field prints his name, distinct from the narrator’s gift account and completion.',
    cuts=['( اشعار میں )','( بن حصین بن حذیفہ بن بدر سید بن غطفان )','( بن حابس رئیس تمیم )','( عینیہ کے پردادا )','( اقرع کے والد )'],
    retained=['( بن عینیہ )','( سعید بن مسروق )','( بڑوں کے )','( میرے والد )'],
    segments=[part(end='کیا آپ میری اور میرے گھوڑے',component='gift-and-poem-frame'),
      part(start='کیا آپ میری اور میرے گھوڑے',end='کہا : اس پر آپ',component='abbas-actual-poem',report_type='companion_recipient_poem_saying',
           speaker='Abbas, with the source’s variant name spellings preserved, supplies this actual poem and comparison. It is not the Prophet’s own speech.'),
      part(start='کہا : اس پر آپ',component='narrator-gift-completion',report_type='companion_report_of_prophetic_giving',
           speaker='The reporting voice resumes the actual account that the Messenger completed his hundred; the poem is not continued here.')])

for language in ('hi','ur','ar','en','ur-Latn'):
    field('2445',language,context_all=True)

field('2447','hi','companion_report_of_accusation_and_prophetic_reply',
    'Ibn Masud reports an unnamed man’s accusation and the Messenger’s actual justice/Musa replies. The accusation is quoted as hostile source speech, not endorsed fact.',
    segments=[part(end='मैं ने दिल में सोचा',component='accusation-and-prophetic-replies'),
      part(start='मैं ने दिल में सोचा',component='ibn-masud-closing-thought',report_type='companion_personal_intention',
           speaker='Ibn Masud personally states his subsequent intention; these are not the Prophet’s words.')])
field('2447','ur','qualified_companion_report_of_accusation_and_prophetic_reply',
    'Ibn Masud’s Urdu route has an unintroduced accusation whose missing speaker-link is not filled from Hindi. Its later reference to what he said remains qualified rather than a settled narrator finding.',
    cuts=['( اس بات سے )','( غصے سے )'],
    retained=['( شقیق )','( بن مسعود )','( مال غنیمت کی )','( اونٹ )','( دل میں )','( ابن مسعود رضی اللہ تعالیٰ عنہ نے )','( اس قسم کی )'],
    segments=[part(end='اور اس دن',component='distribution-scene'),
      part(start='اور اس دن',end=' کہا : میں نے ( دل میں )',component='source-unintroduced-accusation',report_type='qualified_unnamed_reported_accusation_fragment',
           speaker='This accusation has a damaged introduction in Urdu; a later clause refers to what another person said. The missing reporting link and identity remain unfilled, and the accusation is not endorsed.'),
      part(start=' کہا : میں نے ( دل میں )',end='( ابن مسعود رضی اللہ تعالیٰ عنہ نے )',component='informing-and-prophetic-replies',
           speaker='Ibn Masud reports his actual informing, the face change and the explicitly introduced Messenger replies about justice and Musa.'),
      part(start='( ابن مسعود رضی اللہ تعالیٰ عنہ نے )',component='ibn-masud-closing-thought',report_type='companion_personal_intention',
           speaker='The source explicitly resumes Ibn Masud’s own limited intention about this kind of report; it is not another Prophetic statement.')])

field('2448','hi','companion_report_of_accusation_and_prophetic_reply',
    'Abdullah, without an added father-name in this field, reports the unnamed man’s charge, private informing, regret and the Messenger’s actual Musa reply.')
field('2448','ur','companion_report_of_accusation_and_prophetic_reply',
    'The source names Abdullah and supplies the actual private informing/anger/regret/Musa account. No absent father-name or external opponent identity is inserted.',
    retained=['( ابو وائل )','( مال )'])

field('2449','hi','companion_report_of_dialogue_refusal_and_prediction',
    'Jabir reports the unnamed man’s demand, Messenger reply, Umar request and actual refusal/prediction. These retain their historical speakers and are not a present instruction or an asserted outside identity.',
    cuts=['(हलाकत या जहन्नम)','(आगे)'],
    retained=['(मैं इस बात से)','(मांगता हूं)','(ये लोग)','(दीन-ए-इस्लाम)'])
field('2449','ur','companion_report_of_dialogue_refusal_and_prediction',
    'Jabir supplies the actual dialogue with the unnamed man, Umar and Messenger; the source’s defective phrase and explicit protection-formula/people/religion referents remain literal.',
    cuts=['( ہلاکت یاجہنم )','( آگے )'],
    retained=['( میں اس بات سے )','( مانگتا ہوں )','( یہ لوگ )','( دین اسلام )'])

field('2453','hi','qualified_transmitted_prophetic_addition_and_uncertain_saying',
    'The actual addition supplies Umar/Khalid requests and Messenger refusals/prediction, while the omitted earlier person and chain links remain unknown. The final Umara attribution is explicitly uncertain.',
    segments=[part(start='उमर बिन खत्ताब',end='(जरीर ने)',component='actual-request-refusal-addition'),
      part(start='(जरीर ने)',component='umara-uncertain-saying',report_type='named_transmitter_uncertain_prophetic_saying',
           speaker='Jarir transmits Umara’s explicit I-think-the-Messenger-said qualification. The final conditional statement is not certified as an unqualified Prophetic utterance.')],retained=['(जरीर ने)'])
field('2453','ur','qualified_transmitted_prophetic_addition_and_uncertain_saying',
    'The added Umar/Khalid dialogue and prediction are actual supplied wording; Jarir then transmits Umara’s explicit uncertainty about the closing saying.',
    segments=[part(start='عمر بن خطاب',end='( جریر نے )',component='actual-request-refusal-addition'),
      part(start='( جریر نے )',component='umara-uncertain-saying',report_type='named_transmitter_uncertain_prophetic_saying',
           speaker='The source names Umara’s I-think qualification through Jarir. It remains material transmission uncertainty within this same source family.')],retained=['( جریر نے )'])

field('2454','hi','qualified_transmitted_distribution_and_predictive_fragments',
    'The source’s Ibn Fudayl route supplies an actual gold-distribution fragment and a separate finite future-people fragment. Its damaged four-person list, unknown predictive ultimate speaker and pronoun referent remain unfilled.',
    cuts=['(जिस से इसका ताल्लुक़ है)'],
    segments=[part(start='(रसूल अल्लाह',end=202,component='actual-gold-distribution',report_type='qualified_transmitted_prophetic_action_fragment',
           speaker='The source’s parenthetic core explicitly names the Messenger and supplies the distribution predicate; the damaged list is not completed from Urdu.'),
      part(start="'इसकी असल से",end=' के अलफ़ाज़ बयां किये',component='actual-predictive-fragment',report_type='qualified_transmitted_finite_prediction_fragment',
           speaker='The field expressly transmits this future-people wording, but does not independently name its ultimate speaker or identify the antecedent. The later Thamud quote is explicitly not mentioned and remains context.')],
    retained=['(तक्सीम किया.)'])
field('2454','ur','qualified_transmitted_distribution_and_predictive_fragments',
    'Ibn Fudayl’s source route supplies the full own recipient list and an actual finite future-people quotation. The final Thamud wording is expressly absent from this route, not an admitted additional saying.',
    cuts=['( جس سے اس کا تعلق ہے )'],
    segments=[part(start='( رسول اللہ',end=239,component='actual-gold-distribution',report_type='transmitted_prophetic_action_fragment',
           speaker='The source explicitly supplies the Messenger/gold subject-object and distribution predicate, with its own alternative recipient names kept exact.'),
      part(start='" اس کی اصل سے',end=' کے الفاظ بیان کیے',component='actual-predictive-fragment',report_type='qualified_transmitted_finite_prediction_fragment',
           speaker='This supplied future-people fragment retains its unknown ultimate speaker and antecedent; no voice is borrowed from the previous report or from the explicitly absent closing quotation.')],
    retained=['( رسول اللہ صلی اللہ علیہ وسلم نے خام سونا )','( تقسیم کیا ۔ )'])

assert len(READINGS)==23
assert {(('deenhindi-'+key),lang) for key,fields in READINGS.items() for lang in fields}==set(NOTES)
