"""Explicit boundaries for fifty completely read original source fields.

The immutable source-first receipt precedes this specification.  Each own field
was read in full; shared helpers only express the already made decisions.
"""
READINGS = {}

def pair(number, report_type, speaker_hi, speaker_ur=None, **extras):
    assert (number, 'hi') not in READINGS and (number, 'ur') not in READINGS
    for language, speaker in [('hi', speaker_hi), ('ur', speaker_ur or speaker_hi)]:
        READINGS[(number, language)] = {
            'type': report_type, 'speaker': speaker,
            'context': [], 'segments': [{'start': None, 'end': None}],
            'annotations': [], **extras,
        }

pair('1390.2', 'later_observation_of_prophetic_grave',
     'Sufyan al-Tammar reporting his own grave observation through Abu Bakr ibn Ayyash; not Prophetic speech')
READINGS[('1390.2','hi')]['context'] = ['(कोहन नुमा)']
READINGS[('1390.2','ur')]['context'] = ['(کوہان نما)']

pair('1390.3', 'historical_report_and_attributed_identification',
     'Urwah as source narrator and speaker of the sworn correction; the unnamed people retain their mistaken belief')
pair('1391', 'companion_bequest',
     'Aisha addressing Abdullah ibn Zubayr in the source-supplied burial bequest')

pair('1392', 'historical_companion_dialogue_and_bequests',
     'Source narrative with the printed Umar, Aisha, Ibn Umar and unnamed young-man dialogue; the opening witness link is damaged and is not reconstructed',
     'Amr ibn Maymun reporting the Umar, Aisha, Ibn Umar and unnamed Ansari young-man dialogue and Umar bequests')
READINGS[('1392','hi')]['context'] = ['आप ने इस मौक़े पर उस्मान तल्हा ']
READINGS[('1392','hi')]['annotations'] = [
    'The supplied Hindi has a damaged opening chain, burial-to-succession seam and incomplete named list. The stranded list remains context. No missing burial alternative, six-person list, Ansari identity or omitted group name is supplied from another language.',
    'The first-person bequest parenthesis and the final protected-non-Muslim scope remain because they specify the source-supplied instruction and the antecedent of its promises, defense and burden limits.',
]
READINGS[('1392','ur')]['annotations'] = [
    'The full supplied burial alternative, named succession group and Ansari identification are retained only as this Urdu field supplies them. The final protected-non-Muslim parenthesis limits the subsequent duties and is retained as source-supplied scope.',
]

pair('1394', 'prophetic_period_incident_and_revelation_report',
     'Ibn Abbas reporting Abu Lahab own hostile words and the subsequent supplied Quran quotation and translation; neither is relabeled as Prophet speech')
pair('1401', 'companion_pledge_report',
     'Jarir ibn Abdullah recounting his own pledge to the Messenger')
pair('1404', 'companion_exegetical_dialogue',
     'Khalid ibn Aslam reporting the unnamed Bedouin question and Ibn Umar own answer; not Prophetic speech')
READINGS[('1404','hi')]['context'] = ['(ख़राबी)']
READINGS[('1404','ur')]['context'] = ['( خرابی )']

pair('1406', 'historical_companion_dialogue_and_testimony',
     'The Hindi source names Wahb as questioner; Abu Dharr recounts his dispute with Muawiyah and exchange with Uthman',
     'Zayd ibn Wahb as questioner; Abu Dharr recounts his dispute with Muawiyah and exchange with Uthman')
READINGS[('1406','hi')]['context'] = ['(क़ुरान की आयत)', '(जो उन दिनों ख़लीफ़तुल मुस्लिमीन थे)', '(राब्जा)']
READINGS[('1406','ur')]['context'] = ['( قرآن کی آیت )', '( جو ان دنوں خلیفۃ المسلمین تھے )', '( ربذہ )']
READINGS[('1406','hi')]['annotations'] = ['The shortened source chain remains as printed; Zayd is not inserted into the supplied Wahb wording. The actual arrival parenthesis remains narrative.']

pair('1415', 'prophetic_period_collective_report_and_revelation',
     'Unnamed ultimate collective witness in the damaged Hindi chain; the actual donation incident and supplied revelation wording remain qualified',
     'Abu Masud al-Ansari reporting collective labor, the donation incident and the supplied revelation wording')
READINGS[('1415','hi')].update(context=['(अब्दुर रहमान बिन ऑफ)', '(अबू अक़ील नामी)'],
    segments=[{'start':None,'end':' आखिर तक.'}],
    annotations=['The damaged Hindi chain and orphan honorific do not supply the missing ultimate narrator. The two added donor-name glosses are context; the labor purpose and lesser-donation verse-rendering qualification remain. The final continuation pointer is not completed.'])
READINGS[('1415','ur')].update(context=['( عبدالرحمٰن بن عوف )', '( ابوعقیل نامی )'],
    segments=[{'start':None,'end':' آخر تک۔'}])

pair('1420', 'prophetic_dialogue_and_companion_recollection',
     'Aisha reporting the wives question, Prophet answer, measurement and later understanding; closing pronominal clause separately qualified')
for language, marker in [('hi','सदक़ा करना आप'), ('ur','صدقہ کرنا آپ')]:
    READINGS[('1420',language)].update(segments=[
        {'start':None,'end':marker},
        {'start':marker,'end':None,'type':'source_supplied_pronominal_character_report',
         'speaker':'Closing source narrative clause with an unresolved antecedent and Prophetic honorific after the named Zaynab; no pronoun or honorific repair'},
    ], annotations=['The final charity-preference clause follows the named Zaynab but bears a Prophetic honorific. Its exact finite wording remains separately qualified; no definitive antecedent or corrected honorific is asserted.'])

pair('1430', 'prophetic_practice_and_explanation_report',
     'Unnamed ultimate Hindi reporter with the explicit I-or-another questioner uncertainty; the Prophet supplied reply is retained',
     'Uqba ibn Harith with the explicit I-or-another questioner uncertainty; the Prophet supplied reply is retained')
READINGS[('1430','hi')]['annotations'] = ['Hindi supplies the wish not to leave charity gold overnight without distribution, but omits the Urdu closing statement that it was distributed. That missing action and the absent narrator-chain names are not supplied.']

pair('1435', 'prophetic_saying_with_companion_dialogue',
     'Hudhayfah and Umar in the supplied dialogue, followed by the separately bounded Abu Wail collective inquiry')
READINGS[('1435','hi')].update(context=['(फितना)'], segments=[
    {'start':None,'end':'आमश ने कहा अबू वैल कभी यूँ कहते थे.'},
    {'start':'उम्र (रज़ियल्लाहु अन्हु) ने फ़रमाया कि मेरी मुराद','end':'अबू वाईल ने कहा की हाँ फिर'},
    {'start':'अबू वाईल ने कहा की हाँ फिर','end':None,
     'type':'later_inquiry_and_companion_reply',
     'speaker':'Abu Wail collective reporting voice, Masruq question and Hudhayfah own replies about Umar'},
], annotations=['The Hindi al-Amash/Abu Wail comparison tail supplies a list and a broken transition without the finite variant predicate supplied in Urdu, so that bounded tail remains context. The earlier damaged expiation clause and later actual dialogue remain literal; no words or chain links are repaired.'])
READINGS[('1435','ur')].update(context=['( فتنہ )'], segments=[
    {'start':None,'end':'اعمش نے کہا ابووائل کبھی یوں کہتے تھے۔'},
    {'start':'اعمش نے کہا ابووائل کبھی یوں کہتے تھے۔','end':'پھر اس فتنے کے متعلق عمر',
     'type':'transmitted_prophetic_saying_variant',
     'speaker':'Abu Wail alternate finite wording transmitted by al-Amash within the Hudhayfah report; not al-Amash eyewitness speech'},
    {'start':'پھر اس فتنے کے متعلق عمر','end':'ابووائل نے کہا کہ ہاں پھر'},
    {'start':'ابووائل نے کہا کہ ہاں پھر','end':None,
     'type':'later_inquiry_and_companion_reply',
     'speaker':'Abu Wail collective reporting voice, Masruq question and Hudhayfah own replies about Umar'},
])

pair('1448', 'transmitted_written_zakat_instructions',
     'Anas reporting Abu Bakr written instructions under the source-stated Allah and Messenger authority; not an invented direct Prophetic quotation')
READINGS[('1448','hi')]['context'] = ['(अपने दौर-इ-खिलाफत में फ़र्ज़ ज़कात से मुतालिक हिदायत देते हुए)']
READINGS[('1448','ur')].update(context=['( اپنے دور خلافت میں فرض زکوٰۃ سے متعلق ہدایت دیتے ہوئے )'],
    segments=[{'start':None,'end':' ‘ وہ مادہ یا نر اونٹ'}])

pair('1449', 'prophetic_practice_and_charity_instruction_report',
     'Ibn Abbas own witness report, followed by a distinct later source report of Ayyub gesture')
for language, marker in [('hi','ये कहते वक़्त अय्यूब'), ('ur','یہ کہتے وقت ایوب')]:
    READINGS[('1449',language)]['segments'] = [
        {'start':None,'end':marker},
        {'start':marker,'end':None,'type':'transmitter_demonstration_report',
         'speaker':'Source reporting voice, not separately named here, describing Ayyub actual ear-and-neck gesture while transmitting the same report'},
    ]

pair('1450', 'transmitted_written_zakat_instructions',
     'Anas reporting Abu Bakr letter conveying the Prophet-obligated rule; the increase-in-zakat motive remains qualified')
pair('1451', 'transmitted_written_zakat_instructions',
     'Anas reporting Abu Bakr letter and its stated Prophet-established joint-account instruction')
pair('1453', 'transmitted_written_zakat_instructions',
     'Anas reporting Abu Bakr written replacement schedule under the source-stated Allah and Messenger authority')
READINGS[('1453','hi')].update(context=["(ताके 'हिक़्क़ा' की कमी पूरी हो जाये)"],
    annotations=['Hindi omits the first-case easy-two-goats or otherwise-twenty-dirhams alternative supplied in Urdu. No option is inserted; the later actual twenty-dirham conditions remain only where printed.'])
READINGS[('1453','ur')]['context'] = ['( تاکہ ”حقہ“ کی کمی پوری ہو جائے )']

pair('1454', 'transmitted_written_zakat_instructions',
     'Source-reported Bahrain letter with issuer and recipient unnamed in the damaged Hindi chain; the body itself states Messenger authority',
     'Anas ibn Malik reporting Abu Bakr Bahrain letter and the source-stated Messenger-established schedule')
READINGS[('1454','hi')].update(context=[' होगी जो मादा होती है.'],
    annotations=['Hindi omits the issuer and recipient names and the twenty-five-to-thirty-five camel category. Its stranded female-animal tail remains context. No actor, number, age or omitted tax category is supplied. All later printed ranges, governor capacity, grazing condition, exceptions and currency unit remain exact.'])
READINGS[('1454','ur')]['annotations'] = ['Retain every actual numerical lower-bound parenthesis, the below-five exception, governor capacity, most-of-year grazing condition and dirham unit. Duplicate connectors remain literal rather than silently normalized.']

pair('1455', 'transmitted_written_zakat_instructions',
     'Anas ibn Malik reporting Abu Bakr written instructions under the stated Messenger rules, including the collector-discretion exception')

pair('1456', 'companion_statement_and_response',
     'Abu Hurayrah transmitting Abu Bakr conditional sworn statement and Umar distinct response; neither is relabeled as Prophetic speech')
pair('1457', 'companion_statement_and_response',
     'Abu Hurayrah transmitting Abu Bakr conditional sworn statement and Umar distinct response in this separately preserved source ID')
for number in ['1456','1457']:
    for language, marker in [('hi','हज़रत उमर'),('ur','حضرت عمر')]:
        READINGS[(number,language)]['segments'] = [
            {'start':None,'end':marker,'type':'companion_conditional_sworn_statement',
             'speaker':'Abu Bakr as transmitted by Abu Hurayrah in this source occurrence'},
            {'start':marker,'end':None,'type':'companion_response_and_personal_recognition',
             'speaker':'Umar own source-supplied response to Abu Bakr statement'},
        ]

pair('1467', 'companion_question_and_prophetic_answer',
     'Umm Salamah own question about her children and the Prophet supplied reward answer')
READINGS[('1467','hi')]['context'] = ['(अपने पहले खावंद)']
READINGS[('1467','ur')]['context'] = ['( اپنے پہلے خاوند )']
pair('1469', 'prophetic_giving_and_saying_report',
     'Abu Said al-Khudri reporting the requests, gifts and supplied Prophet sayings')
READINGS[('1469','hi')].update(segments=[{'start':None,'end':' (सब्र तमाम नेमतों से बढ़ कर है).'}],
    annotations=['Hindi does not print the Urdu funds-exhausted sentence, and no missing action or chain name is supplied. The final parenthetical summary is retained as explanatory context.'])
READINGS[('1469','ur')]['segments'] = [{'start':None,'end':' ( صبر تمام نعمتوں سے بڑھ کر ہے )'}]

pair('1478', 'prophetic_giving_dialogue_and_transmitted_variant',
     'Saad ibn Abi Waqqas main reported dialogue and the separately qualified actual addition in the later route')
READINGS[('1478','hi')]['segments'] = [
    {'start':None,'end':' और (याक़ूब बिन इब्राहिम)'},
    {'start':'उन्होंने कहा कि फिर नबी करीम','end':' आख़िर हदीस तक।',
     'type':'transmitted_prophetic_action_and_abbreviated_saying_variant',
     'speaker':'Actual finite addition transmitted through the source later route, addressing Saad; its first-person addressee link is not expanded beyond the supplied chain'},
]
READINGS[('1478','ur')]['segments'] = [
    {'start':None,'end':' اور ( یعقوب بن ابراہیم )'},
    {'start':'انہوں نے کہا کہ پھر نبی کریم','end':' آخر حدیث تک۔',
     'type':'transmitted_prophetic_action_and_abbreviated_saying_variant',
     'speaker':'Actual finite addition transmitted through the source later route, addressing Saad; its first-person addressee link is not expanded beyond the supplied chain'},
]
for language in ['hi','ur']:
    READINGS[('1478',language)]['annotations'] = ['The later chain and same-hadith pointer remain context, while its finite hand placement, Saad address and abbreviated giving clause remain as a transmitted variant of the same family. The end-of-hadith pointer, compiler word morphology and transmitter biography remain context. The action-comparison and recipient-condition parentheses inside the main report remain because they delimit the supplied assertion. No missing continuation is filled.']

pair('1486', 'prophetic_prohibition_and_companion_explanation',
     'Ibn Umar transmitting the Prophet prohibition, followed by Ibn Umar own actual answer about maturity')
for language, marker in [('hi','और इब्न उमर'),('ur','اور ابن عمر')]:
    READINGS[('1486',language)]['segments'] = [
        {'start':None,'end':marker,'type':'prophetic_prohibition_report','speaker':'Ibn Umar reporting the Prophet date-sale prohibition'},
        {'start':marker,'end':None,'type':'companion_question_answer_explanation','speaker':'Ibn Umar answering unnamed questioners about the reported maturity condition'},
    ]

assert len(READINGS) == 50
