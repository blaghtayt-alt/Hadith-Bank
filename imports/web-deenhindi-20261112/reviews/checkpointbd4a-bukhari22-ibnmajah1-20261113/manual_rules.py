"""Explicit source boundaries after46 complete own Hindi/Urdu readings."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RECEIPT=json.loads((ROOT/'complete-source-first-reading-receipt.json').read_bytes())
READINGS={}
for row in RECEIPT['readings']:
    READINGS.setdefault(row['occurrence_id'].replace('deenhindi-',''),{})[row['language']]=row['source_first_note']
SPECS={}
def put(key,kind,speaker,reason,**rules):
    assert key not in SPECS
    SPECS[key]={'id':key,'decision':'register','languages':['hi','ur'],
        'read_languages':list(READINGS[key]),'field_notes':dict(READINGS[key]),
        'report_type':kind,'speaker':speaker,'reason':reason,**rules}
def comp(start,end,kind,speaker):
    return {'start_at':start,'stop_before':end,'report_type':kind,'speaker':speaker}

put('bukhari:2390','prophetic_debt_dialogue_and_repayment_instruction',
    'Abu Hurayrah through the source Abu Salamah route reports the creditor encounter and Prophet replies.',
    'Preserve the actual debt demand, restraint of the companions, replacement camel and good-repayment statement. The prior-loan parenthesis specifies the comparison object. Only the final Urdu hadith/chapter-concordance comment is compiler context.',
    stop_before={'ur':' ( حدیث اور باب کی مطابقت ظاہر ہے)'})

put('bukhari:2394','prophetic_visit_prayer_instruction_and_repayment_report',
    'Jabir actual visit and repayment account is interrupted by Misar own qualified time recollection.',
    'The named Misar temporal uncertainty stays separately attributed within the same report family, not as certain Prophet speech. The arrival-at-that-time parenthesis limits what the recollection concerns; retain it as supplied. Resume Jabir account after the qualification.',
    shared_report_family=True,components={
        'hi':[comp(None,"मिस'अर ने बयान किया के मेरा",'companion_visit_report','Jabir reporting his mosque visit to the Prophet.'),
              comp("मिस'अर ने बयान किया के मेरा",'फिर आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया','named_transmitter_temporal_memory_qualification','Misar states his uncertain memory that the arrival time of duha was mentioned.'),
              comp('फिर आप (सल्लल्लाहु अलैहि वसल्लम) ने फ़रमाया',None,'prophetic_instruction_and_repayment_report','Jabir resumes the Prophet two-rakah instruction and repayment with extra.')],
        'ur':[comp(None,'مسعر نے بیان کیا کہ میرا','companion_visit_report','Jabir reporting his mosque visit to the Prophet.'),
              comp('مسعر نے بیان کیا کہ میرا','پھر آپ صلی اللہ علیہ وسلم نے فرمایا','named_transmitter_temporal_memory_qualification','Misar states his uncertain memory that the arrival time of duha was mentioned.'),
              comp('پھر آپ صلی اللہ علیہ وسلم نے فرمایا',None,'prophetic_instruction_and_repayment_report','Jabir resumes the Prophet two-rakah instruction and repayment with extra.')]})

put('bukhari:2395','companion_father_debt_and_prophetic_garden_visit_report',
    'Jabir narrates his father debt, the creditors response and the Prophet garden visit and blessing prayer.',
    'Retain the refusal, promised morning visit, blessing prayer, completed payment and remaining dates. The appended father-name gloss is context, while the father relation remains in the actual sentence. Do not repair the printed Kab route.',
    exclude_substrings={'hi':['(अब्दुल्लाह रदी अल्लाहु अन्हु)'],'ur':['( عبداللہ رضی اللہ عنہ )']})

put('bukhari:2401','prophetic_reply_to_harsh_debt_demand',
    'Abu Hurayrah reports the unnamed creditor demand, companion reaction and Prophet restraint instruction.',
    'This complete own field supplies a finite short report. Preserve its actual right-holder scope without importing a camel or other continuation from another occurrence.')

for number in ['2405','2406']:
    put('bukhari:'+number,'two_companion_narratives_with_prophetic_interactions',
        'Jabir supplies a father-debt/date-payment episode and a separate campaign/camel-sale/marriage episode.',
        'Each occurrence and language was read separately. Preserve two event families in the one provider record, the my-father relations, other-occasion transition, reserved ride to Medina, actual care purpose, uncle reaction, price, returned camel and campaign share. No ID deduplication or unseen actor is introduced.',
        components={
            'hi':[comp(None,'(एक और मौक़े पर)','companion_debt_and_date_payment_report','Jabir narrates his father debt, the requested intercession and date payment.'),
                  comp('(एक और मौक़े पर)',None,'companion_campaign_camel_sale_and_marriage_dialogue','Jabir narrates the distinct campaign, camel sale, marriage explanation and final payment/return.')],
            'ur':[comp(None,'(ایک اور موقع پر)','companion_debt_and_date_payment_report','Jabir narrates his father debt, the requested intercession and date payment.'),
                  comp('(ایک اور موقع پر)',None,'companion_campaign_camel_sale_and_marriage_dialogue','Jabir narrates the distinct campaign, camel sale, marriage explanation and final payment/return.')]})

put('bukhari:2407','prophetic_transaction_reply_and_later_practice_report',
    'The source expressly names Umar through Abdullah ibn Dinar; the unnamed buyer and Prophet dialogue are preserved as printed.',
    'Retain the complaint, no-deception formula and later repeated use. The printed Umar attribution is not changed to Ibn Umar using a familiar parallel.',
    annotations={'hi':'This own field prints Umar. No Ibn prefix or alternative narrator identity is supplied.',
                 'ur':'The source names Umar in its own route; no external narrator correction is made.'})

put('bukhari:2413','historical_injury_question_response_and_prophetic_order_report',
    'Anas reports the injured girl response, suspect confession and the source-stated Prophet order and outcome.',
    'Retain the still-alive circumstance and affirmative yes response as actual event content. Preserve the unnamed actors, confession and sequence; no modern instruction or additional legal conclusion is introduced.')

put('bukhari:2415','companion_report_of_manumission_and_sale',
    'Jabir reports the unnamed owner action, Prophet return and named Naim ibn Nahham purchase.',
    'Retain the no-other-property limitation and all supplied acts. No posthumous or testamentary condition absent from this field is imported.')

put('bukhari:2418','companion_debt_dialogue_and_prophetic_settlement_instruction',
    'Kab reports his demand from Ibn Abi Hadrad, Prophet intervention, Kab remission and the payment instruction.',
    'Keep the named creditor/debtor, mosque and home setting, raised voices, curtain, actual half-debt gesture and all responses in order.')

put('bukhari:2423','prophetic_period_expedition_and_capture_report',
    'Abu Hurayrah reports the Najd dispatch, named captive and mosque-pillar restraint.',
    'The actual supplied actions form a finite abbreviated historical report. Keep the source name spellings and do not add release, conversion or other unseen continuation.')

put('bukhari:2425','companion_debt_dialogue_and_revelation_report',
    'Khabbab recounts his exchange with As ibn Wail, followed by the supplied Quran revelation wording and translation.',
    'Retain both parties actual conditional claims, Khabbab refusal, death-and-renewed-life wording and the actual Quran text and translation. The added unbeliever label, repeated second-life gloss and final continuation pointer remain context; no verse ending is supplied.',
    exclude_substrings={'hi':['(काफ़िर)','(दूसरी ज़िंदगी में)'],'ur':['( کافر )','( دوسری زندگی میں )']},
    stop_before={'hi':' आख़िर आयत तक।','ur':' آخر آیت تک۔'})

put('bukhari:2427','prophetic_found_property_and_lost_livestock_dialogue',
    'Zayd ibn Khalid reports the Bedouin questions and the Prophet supplied answers.',
    'Retain the year, identifying signs, parenthetic return imperative, sheep alternatives and the brother-as-owner recipient scope. The hoof-function explanation remains context; the actual independent water/leaf actions and changed face remain in the report.',
    exclude_substrings={'hi':['(जिन से वो चलेगा)'],'ur':['( جن سے وہ چلے گا )']})

put('bukhari:2431','prophetic_conditional_saying_about_found_date',
    'Anas reports the road date and the Prophet conditional statement.',
    'Preserve the charity concern as uncertainty and the willingness-to-eat counterfactual. Do not assert that the date actually was charity or identify an unseen owner.')

put('bukhari:2437.2','qualified_later_encounter_and_transmission_uncertainty',
    'The source Salamah/Ubay route introduces a quoted later encounter and an unresolved respondent; the I/he links remain unspecified.',
    'The above-hadith chain/pointer is context. The actual Mecca encounter and one-or-three-years uncertainty are finite supplied content and remain in one report family. Do not invent Shuba, expand Kab identity, fill a preceding report or treat the uncertainty as Prophet speech.',
    shared_report_family=True,components={
        'hi':[comp("'मैं बाद में मक्का",'तो उन्होंने कहा','qualified_later_encounter_report','Quoted first-person reporter of the later Mecca encounter; the own field does not uniquely establish this I or the met person.'),
              comp('तो उन्होंने कहा',None,'qualified_transmitted_material_memory_uncertainty','Quoted respondent whose identity is not uniquely fixed in this own field; the one-or-three-years memory alternatives remain unresolved.')],
        'ur':[comp("'میں بعد میں مکہ",'تو انہوں نے کہا','qualified_later_encounter_report','Quoted first-person reporter of the later Mecca encounter; the own field does not uniquely establish this I or the met person.'),
              comp('تو انہوں نے کہا',None,'qualified_transmitted_material_memory_uncertainty','Quoted respondent whose identity is not uniquely fixed in this own field; the one-or-three-years memory alternatives remain unresolved.')]},
    annotations={'hi':'The opening names and shortened pointer do not unambiguously resolve the I/he links of the actual quoted addition. These remain qualified, and neither one nor three years is chosen.',
                 'ur':'The source prints Salamah, Ubay ibn Kab and later Kab, but the addition does not uniquely fix its first-person reporter and respondent. No familiar parallel supplies them.'})

put('bukhari:2439','companion_journey_testimony_with_prophetic_drinking',
    'Abu Bakr recounts the shepherd encounter, preparation and presentation of milk and Prophet drinking.',
    'Preserve both source routes, the migration-to-Medina action setting, all questions and cleaning/cooling acts, and Abu Bakr final satisfaction. Only the second-chain label is apparatus; the known-to-speaker owner remains unnamed.',
    exclude_substrings={'hi':['(दूसरी सनद)'],'ur':['(دوسری سند)']})

put('bukhari:2450','companion_exegetical_saying_with_quran_quotation',
    'Aisha explains the supplied verse circumstance and wife relinquishing her right; this is her own statement, not Prophet speech.',
    'Retain the actual source Quran quotation/transliteration and complete translation, the feared estrangement and source-stated revelation circumstance. The introductory Quran-verse header alone is context.',
    exclude_substrings={'hi':['(क़ुरआन मजीद की आयत)'],'ur':['( قرآن مجید کی آیت )']})

put('bukhari:2460','companion_question_and_prophetic_bounded_permission',
    'Aisha relays Hind question and the Prophet source-supplied customary-amount response.',
    'Retain the explicit husband relationship as material property/participant scope, with its third-person source wording unchanged. Keep the children purpose and customary limit; no unrelated-person permission or repaired direct quotation is created.',
    annotations={'hi':'The husband parenthesis remains as the source own third-person narrative qualification. It is not rewritten as independently verified first-person speech by Hind.',
                 'ur':'The relationship qualifier is printed in third person and remains literal source narrative scope; no voice or pronoun repair is made.'})

put('bukhari:2461','companion_collective_question_and_prophetic_conditional_reply',
    'Uqba ibn Amir reports the collective question and Prophet response.',
    'Retain the sometimes frequency qualification and the actual hospitality conditions. No universal refusal, additional exemption or present-day operational instruction is inferred.')

put('bukhari:2462','companion_historical_saqifa_arrival_testimony',
    'Umar through Ibn Abbas recounts the gathering, his request to Abu Bakr and their arrival after the Prophet death.',
    'Preserve the actual finite historical excerpt and place description. The second-chain marker alone is apparatus; no subsequent speeches, succession events or Prophetic attribution are added.',
    exclude_substrings={'hi':['(दूसरी सनद)'],'ur':['(دوسری سند)']})

put('bukhari:2464','companion_wine_disposal_and_revelation_report',
    'Anas recounts his own service and disposal, Abu Talha response, unnamed people concern and the ensuing supplied revelation.',
    'Retain the source revelation timing and immediate-hearing circumstance as actual narrative sequence. Preserve the exact Quran excerpt/transliteration and translation; the final verse-continuation pointer and isolated terminal quotation apparatus remain context without completion.',
    stop_before={'hi':' (आख़िर आयत तक)','ur':' ( آخر آیت تک )'})

put('bukhari:2467','prophetic_saying_report_with_near_future_scope',
    'Usama ibn Zayd reports the high Medina building and Prophet source-supplied statement.',
    'Preserve the near-future qualifier, comparison and source punctuation. This records the supplied attribution and wording without a current-event or independent prediction claim.',
    annotations={'hi':'The near-future parenthesis contains a stray apostrophe in the supplied source. It remains unchanged.'})

put('ibnmajah:2376','companion_gift_account_with_attributed_question_and_answer',
    'Numan ibn Bashir reports his father gift and the question/answer; Hindi introductory visit wording is damaged and remains qualified.',
    'Retain the gift, witnessing purpose, all-sons question, negative answer and return instruction. The Hindi orphan honorific and missing introduction are not repaired from Urdu. Each own language is admitted on its actual supplied content.',
    components={'hi':[comp(None,None,'qualified_gift_account_with_honorific_attributed_dialogue','Numan ibn Bashir reports his father gift; the replying figure is denoted by repeated Prophetic honorifics, while the Hindi visit introduction is damaged.')],
                'ur':[comp(None,None,'companion_gift_account_with_prophetic_dialogue','Numan ibn Bashir reports his father gift, visit to the explicitly named Prophet and the supplied question and reply.')]},
    annotations={'hi':'The gift-to-visit seam omits introductory words and leaves an orphan honorific fragment. All source words remain exact. The replying figure is indicated by the repeated Prophetic honorifics only; no missing name or connecting words are inserted.',
                 'ur':'The Urdu field independently supplies the Prophet visit. That wording is not copied into the Hindi gap.'})

BOUNDARY_REFINEMENTS={
    'bukhari:2437.2:hi':'The finite encounter and respondent uncertainty are displayed as distinct ordered, qualified components within one family; the absent I/he links remain unspecified.',
    'bukhari:2437.2:ur':'The added encounter and actual material doubt are separately attributed to the source unspecified voices, with the route/pointer retained in context.',
}

RETAINED_HONORIFICS={
    '(रज़ियल्लाहु अन्हा)','(रज़ियल्लाहु अन्हु)','(रज़ियल्लाहु अन्हुमा)','(रज़ियल्लाहु अन्हुम)',
    '(रदी अल्लाहु अन्हु)','(रदी अल्लाहु अन्हुम)','(रदी अल्लाहु अन्हुमा)',
    '(सल्लल्लाहु अलैहि वसल्लम)','( صلی اللہ علیہ وسلم )',
}
RETAINED_NONHONORIFIC={}
def keep(key,language,literal,reason):RETAINED_NONHONORIFIC[(key,language,literal)]=reason
for language,literal in [('hi','(जो उस ने आप को क़र्ज़ दिया था)'),('ur','( جو اس نے آپ کو قرض دیا تھا )')]:
    keep('bukhari:2390',language,literal,'This specifies the loaned camel that is the actual comparison object.')
for language,literal in [('hi','(के इस वक़्त ख़िदमत-ए-नबवी में हाज़िर हुआ)'),('ur','( کہ اس وقت خدمت نبوی میں حاضر ہوا )')]:
    keep('bukhari:2394',language,literal,'The clause gives the arrival domain of Misar uncertain temporal recollection, not an unqualified prayer-time assertion.')
for number in ['2405','2406']:
    for language,relation,timing in [('hi','(मेरे वालिद)','(एक और मौक़े पर)'),('ur','(میرے والد)','(ایک اور موقع پر)')]:
        keep('bukhari:'+number,language,relation,'The first-person father relationship limits the participant and the later marriage-care explanation.')
        keep('bukhari:'+number,language,timing,'This explicitly separates the time of the second episode from the first.')
for language,alive,answer in [('hi','(इस में कुछ जान बाक़ी थी)','(के हां)'),('ur','( اس میں کچھ جان باقی تھی )','( کہ ہاں )')]:
    keep('bukhari:2413',language,alive,'The remaining-life circumstance enables the reported question and response.')
    keep('bukhari:2413',language,answer,'This is the actual affirmative content of the girl gesture, not a lexical gloss.')
keep('bukhari:2425','hi','(क्या तुमने उस शख़्स को देखा जिसने हमारी आयतों का इंकार किया और कहा के मुझे माल और औलाद ज़रूर दी जाएगी)','The source actual Quran translation remains substantive quotation despite its parentheses.')
for language,command,owner in [('hi','(तो उसे उसका माल वापस कर दे)','(मालिक)'),('ur','( تو اسے اس کا مال واپس کر دے )','( مالک )')]:
    keep('bukhari:2427',language,command,'The finite imperative supplies the consequence of correct identification.')
    keep('bukhari:2427',language,owner,'This identifies the actual brother recipient as the owner and limits the property-recipient alternative.')
for language,literal in [('hi','(हिजरत कर के मदीना जाते वक़्त)'),('ur','( ہجرت کر کے مدینہ جاتے وقت )')]:
    keep('bukhari:2439',language,literal,'This supplies the action setting and timing of Abu Bakr search during the journey.')
for language,literal in [('hi','(जो उनके शौहर हैं वो)'),('ur','( جو ان کے شوہر ہیں وہ )')]:
    keep('bukhari:2460',language,literal,'The husband relationship materially limits the property and participant scope; its third-person source wording remains literal.')
for language,literal in [('hi','(बाज़ दफ़ा)'),('ur','( بعض دفعہ )')]:
    keep('bukhari:2461',language,literal,'This is the supplied occasional frequency, preventing a universal complaint.')
for language,timing,hearing in [('hi','(फिर ज्योंही शराब की हुरमत पर आयत-ए-क़ुरआनी उतरी)','(यह सुनते ही)'),('ur','( پھر جونہی شراب کی حرمت پر آیت قرآنی اتری )','( یہ سنتے ہی )')]:
    keep('bukhari:2464',language,timing,'The finite revelation event supplies the temporal condition of the announcement, not a verse-number locator.')
    keep('bukhari:2464',language,hearing,'This identifies the actual immediate-hearing trigger for Abu Talha response.')
for language,literal in [('hi',"('अनक़रीब)"),('ur','( عنقریب )')]:
    keep('bukhari:2467',language,literal,'This gives near-future temporal scope; the Hindi punctuation remains literal.')
RETAINED_MARKER_WORDS={}
assert len(SPECS)==23
