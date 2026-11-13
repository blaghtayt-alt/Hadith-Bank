"""Complete own-field source readings and literal boundaries by /root."""
SPECS={}
def add(local_id,report_type,speaker,hi_note,ur_note,**extra):
    SPECS[local_id]={'id':local_id,'decision':'register','report_type':report_type,'speaker':speaker,
        'reason':'Actual source-supplied report with its own attribution and qualifications; no missing wording, canonical identity or grade is reconstructed.',
        'read_languages':['hi','ur'],'languages':['hi','ur'],'field_notes':{'hi':hi_note,'ur':ur_note},'shared_report_family':True,**extra}

add('ibnmajah:2213','prophetic_judgment_report','Ubada ibn Samit reporting two linked source rulings',
    'Read all372 Hindi characters. Retain both fruit and servant-property clauses and each buyer-stipulation exception. Only the parenthetic grafting synonym explaining tabir is lexical context; the actual tabir act and all conditions remain. No modern legal guidance or corrected technical translation is supplied.',
    'Read all346 Urdu characters. Preserve the two reported judgments, the person performing tabir, seller property and each explicitly supplied buyer condition. Only the parenthetic lexical equivalent of tabir is contextual, with the source term and meaning-bearing clauses intact.',
    exclude_substrings={'hi':['(पैवंदकारी)'],'ur':['( پیوندکاری )']})
add('ibnmajah:2223','companion_report_of_prophetic_arrival_and_revelation','Abdullah ibn Abbas reporting the Medina arrival and revelation-related change',
    'Read all302 characters of this Hindi-labelled Latin field. Preserve the Medina weighing/measuring account, actual short transliterated Quran quotation and its parenthetic supplied meaning, followed by the change in measurement. This is a narrated revelation event, not an invented direct Prophetic utterance. Correct only its script toLatn, without changing the publisher language label or any source character.',
    'Read all248 Urdu characters. Preserve the arrival, measurement account, actual Arabic verse fragment and its supplied Urdu meaning, and the subsequent changed practice. The explicit continuation abbreviation is source apparatus; no absent verse continuation or number is supplied.',
    observed_scripts={'hi':'Latn'},script_notes={'hi':'The publisher Hindi-labelled field contains Latin transliteration. Language identity and every original character are preserved; only the observed script is corrected from Deva to Latn.'},
    exclude_substrings={'ur':['الخ']})
add('ibnmajah:2228','prophetic_prohibition_report','Jabir ibn Abdullah reporting the supplied prohibition',
    'Read all183 Hindi characters, preserving the printed man spelling defect without repair. Keep the full grain-sale prohibition and the condition involving both seller and buyer measures; no absent explanation of the measure unit is supplied.',
    'Read all167 Urdu characters. Retain the complete prohibition and both seller/buyer measure condition. Only the terminal footnote reference and its punctuation are contextual apparatus.',
    stop_before={'ur':' ۱؎'})
add('ibnmajah:2249','prophetic_dialogue_and_practice_report','Ali reporting the gift, sale, question and return instruction',
    'Read all355 Hindi-labelled Latin characters. Retain the two full brothers given to Ali, his sale of one, the Prophet question, Ali answer and instruction to recover him. Only the parenthetic synonym for hiba is lexical context. Correct the observed script toLatn without changing the language label or text.',
    'Read all289 Urdu characters. The full own field supplies the gift of two brothers, sale of one, actual question and answer and the return instruction. Preserve the relationship and every step; no identities or extra rationale are inserted.',
    observed_scripts={'hi':'Latn'},script_notes={'hi':'The publisher Hindi-labelled field is Latin transliteration. Preserve its Hindi identity and all source characters; record the observed script as Latn.'},
    exclude_substrings={'hi':['(tohfe)']})
add('ibnmajah:2251','historical_dialogue_and_reported_prophetic_document','Abdul Majid ibn Wahb reporting Adda ibn Khalid ibn Hawza and the source-quoted document',
    'Read all574 Hindi-labelled Latin characters. Preserve the offer to read, affirmative reply, document production and actual quoted sale text, including male-or-female servant uncertainty, all three stated exclusions and Muslim-to-Muslim wording. The source states Adda bought from Muhammad; do not reverse that direction from another edition or infer a handwriting claim. Correct only the observed script toLatn.',
    'Read all488 Urdu characters. Keep the complete dialogue, narrator observation and printed document contents, its buyer/seller direction, servant-or-maid uncertainty, absence of illness/stolen/forbidden goods and final transaction wording. No names, signature, authorship mechanics or canonical document identity beyond this source are invented.',
    observed_scripts={'hi':'Latn'},script_notes={'hi':'This Hindi-labelled source field uses Latin transliteration. Its language label and exact574 characters remain unchanged; script metadata is corrected to Latn.'})
add('ibnmajah:2263','prophetic_prohibition_report','Abdullah ibn Masud reporting the supplied prohibition',
    'Read all156 Hindi characters. Preserve the source spelling, the prohibition concerning breaking circulating Muslim coin and the without-need qualification. No modern currency, legal application or missing explanation is added.',
    'Read all132 Urdu characters. The complete finite prohibition includes the material without-necessity exception and circulating-coin description. Retain all of it under the printed attribution without expansion.')

add('ibnmajah:2265','prophetic_prohibition_with_transmitted_scope_description','Ibn Umar reports the prohibition; the internal descriptive voice is not separately assigned as direct Prophetic speech',
    'Read all385 Hindi characters. Preserve the opening prohibition, the three source-specified forms involving standing dates/dried dates, grapes/raisins and standing crop/dried grain, and the final statement that all were prohibited. Those forms define the reported scope and remain as a separate same-family descriptive component, not an invented direct quotation. Preserve the printed bail spelling defect and all measured-sale conditions.',
    'Read all359 Urdu characters. Retain the prohibition and all three actually supplied transaction descriptions, plus the explicit concluding prohibition of all of them. The descriptive voice is distinguished from direct Prophetic speech in the same report family. Only the terminal footnote reference is context.',
    stop_before={'ur':' ۱؎'})
SPECS['ibnmajah:2265']['components']={
    'hi':[
        {'stop_before':'मुज़ाबाना यह है','report_type':'prophetic_prohibition_report','speaker':'Ibn Umar reporting the Prophet prohibition'},
        {'start_at':'मुज़ाबाना यह है','stop_before':'आप (सल्लल्लाहु अलैहि वसल्लम) ने इन सब','report_type':'transmitted_scope_description','speaker':'Descriptive voice within the supplied Ibn Umar report; not separately identified as direct Prophetic speech'},
        {'start_at':'आप (सल्लल्लाहु अलैहि वसल्लम) ने इन सब','report_type':'prophetic_prohibition_report','speaker':'Ibn Umar reporting that the Prophet forbade all the described forms'},
    ],
    'ur':[
        {'stop_before':'مزابنہ یہ ہے','report_type':'prophetic_prohibition_report','speaker':'Ibn Umar reporting the Prophet prohibition'},
        {'start_at':'مزابنہ یہ ہے','stop_before':'آپ صلی اللہ علیہ وسلم نے ان سب','report_type':'transmitted_scope_description','speaker':'Descriptive voice within the supplied Ibn Umar report; not separately identified as direct Prophetic speech'},
        {'start_at':'آپ صلی اللہ علیہ وسلم نے ان سب','report_type':'prophetic_prohibition_report','speaker':'Ibn Umar reporting that the Prophet forbade all the described forms'},
    ]}
add('ibnmajah:2267','prophetic_prohibition_report','Rafi ibn Khadij reporting the supplied prohibition',
    'Read all117 Hindi characters. Keep both printed transaction terms and the source man spelling exactly. Do not supply definitions or missing letters from adjacent reports or Urdu.',
    'Read all102 Urdu characters. The field supplies the complete prohibition of muhaqala and muzabana under Rafi attribution. Retain it without importing absent explanatory terms.')
add('ibnmajah:2280','prophetic_arrival_and_transaction_condition_report','Ibn Abbas reporting the Medina practice and the Prophet stated conditions',
    'Read all375 Hindi characters. Preserve the Medina arrival, actual two-and-three-year advance-price practice and the condition of specified measure/weight and a fixed term. The English advance-payment label and inline yani restatement are lexical explanations of the already described prepayment, retained as context. The substantive contract conditions and printed wording remain exact.',
    'Read all328 Urdu characters. Retain the arrival, supplied multi-year prepayment practice and the entire stated measure/weight-and-term requirement. The inline definition of paying in advance merely repeats the opening described act and is source lexical context, as is the terminal footnote marker; no conditions are omitted or modern application added.',
    exclude_substrings={'hi':['(एडवांस पेमेंट)','यानी क़ीमत पेशगी अदा कर दे'],'ur':['یعنی قیمت پیشگی ادا کر دے']},stop_before={'ur':' ۱؎'})
add('nasai:2232','abbreviated_historical_arrival_report','Said ibn Abi Hind reporting that Mutarrif came to the source-named Uthman',
    'Read all112 Hindi characters. A finite named-person arrival is actually supplied before the missing-story pointer. Retain that bounded historical action as an excerpt and leave the pointer in context; do not invent the omitted story or assign a Prophetic voice.',
    'Read all118 Urdu characters. Retain only the actual Mutarrif-to-Uthman arrival reported by Said. The following similar-report pointer and mursal assessment remain complete source context, preserving the qualification without turning it into the missing report body.',
    stop_before={'hi':'आगे रावी','ur':'آگے راوی'})
add('nasai:2239','prophetic_speech_with_companion_narrative_frame','Abdullah ibn Masud reporting their travel and the Prophet advice to young men',
    'Read all474 Hindi characters. Preserve the source own cannot-control wording without correcting it from another edition, the young group, full marriage instruction, gaze/chastity reasons, inability qualification concerning maintenance and fasting comparison. The youthful-excitement parenthesis is an interpretive motive gloss and remains context. The maintenance clause materially qualifies the stated inability and stays as the supplied source limitation.',
    'Read all459 Urdu characters. Retain the whole actual advice, its stated effects, the source inability/maintenance qualification and fasting comparison. The parenthetic youthful excitement is explanatory tone context. Preserve this field own control wording and all operative conditions without borrowing a different translation.',
    exclude_substrings={'hi':['(जवानी के जोश में)'],'ur':['( جوانی کے جوش میں )']})
SPECS['nasai:2259']={
    'id':'nasai:2259','decision':'exclude','report_type':'source_chain_and_similarity_pointer','speaker':'Yahya and Muhammad ibn Abd alRahman transmit an unnamed intermediary from Jabir; no report body or ultimate report speaker is supplied',
    'reason':'Every one of the five supplied fields was completely read. Each gives only a chain or similar-report pointer; no finite report body is present. Preserve the complete occurrence as resolved source-only without importing a neighboring narration.',
    'read_languages':['hi','ur','ar','en','ur-Latn'],'languages':[],
    'field_notes':{
        'hi':'Read all144 characters. Yahya relays Muhammad through an unnamed hearer of Jabir and says similarly; the referred-to body is absent.',
        'ur':'Read all128 characters. The chain and unnamed hearer are supplied, but the text stops at the similarity pointer. No utterance or action of the omitted report is printed.',
        'ar':'Read all234 Arabic characters including the full Mahmud/Firyabi/Awzai/Yahya/Muhammad chain and unnamed hearer from Jabir, ending nahwahu. No report matn follows.',
        'en':'Read all90 characters. Muhammad says someone who heard Jabir told him something similar; preserve its source missing closing quotation punctuation. The content of that similar report is not supplied.',
        'ur-Latn':'Read all162 Roman characters. It repeats the chain, unnamed Jabir hearer and usi tarah pointer without the referred-to body. No omitted text is reconstructed.',
    }}
add('nasai:2264','prophetic_dialogue_and_practice_report','Abu Hurayra reporting the Prophet, Abu Bakr and Umar exchange at Marr alZahran',
    'Read all346 Hindi characters. Preserve the location, offered food, invitation to both named companions, their fasting reply and instructions to saddle and assist the two companions. The complete actual dialogue has no separate explanatory tail to remove.',
    'Read all360 Urdu characters. Retain the place name and all invitation/reply/assistance wording. Only the parenthetical geographical definition between Mecca and Medina and the terminal footnote pointer are source context; neither named actor nor instruction is lost.',
    exclude_substrings={'ur':['( مکہ و مدینہ کے درمیان ایک مقام کا نام ہے )']},stop_before={'ur':' ۱؎'})
add('nasai:2265','abbreviated_prophetic_speech_and_practice_report','Abu Salama relaying the supplied meal scene and invitation',
    'Read all206 Hindi characters. Retain the finite midday meal scene with AbuBakr and Umar and the actual invitation to eat. The final mursal assessment is preserved as source evaluation context, not narration or a new grade supplied by this review. No omitted response is copied from a neighboring entry.',
    'Read all189 Urdu characters. The actual eating, two named companions and invitation form a bounded report. Keep the final mursal qualification separately in source context; do not expand the abbreviated scene.',
    stop_before={'hi':'यह रिवायत मुर्सल है','ur':'یہ روایت مرسل ہے'})
add('nasai:2267','prophetic_dialogue_report','Amr ibn Umayya Damri reporting his own return and the Prophet invitation and explanation',
    'Read all401 Hindi characters. Preserve the journey, morning-meal invitation, AbuUmayya address, fasting reply and complete traveler fasting/half-prayer statement. Do not replace the morning wording with another entry noon wording.',
    'Read all356 Urdu characters. Retain the complete own dialogue, the supplied sit imperative inside the invitation and the traveler conditions. Only the terminal footnote reference is context; the sit command is not an automatic parenthesis deletion and is not inserted into Hindi.',
    stop_before={'ur':' ۱؎'})
add('nasai:2269','prophetic_dialogue_report','Abu Umayya Damri reporting the greeting, attempted departure and subsequent exchange',
    'Read all492 Hindi characters. Keep the source own narrator spelling, arrival from travel, greeting, attempted departure, noon-meal invitation, fasting reply and both concessions. This separate occurrence has its own sequence and time wording.',
    'Read all377 Urdu characters. Preserve every arrival/greeting/departure step, the noon meal and complete question-response. No morning label or absent command is added from2267.')
add('nasai:2270','abbreviated_historical_encounter_report','Abu Muhajir relaying Abu Umayya with the source own Damri identification',
    'Read all186 Hindi characters. Retain the supplied narrator attribution and actual finite visit to the Prophet. The inline Damri identification names the source own actor and stays; the final same-report pointer supplies no body and remains context.',
    'Read all158 Urdu characters. Preserve the own identified AbuUmayya-to-Prophet arrival excerpt. Stop before the similarity pointer and do not fill the omitted meal or fasting conversation.',
    stop_before={'hi':'फिर रावी','ur':'پھر راوی'})
add('nasai:2271','prophetic_dialogue_report','Abu Qilaba reporting Abu Umayya Damri own travel and dialogue',
    'Read all448 Hindi characters. Preserve the arrival, noon-meal invitation, fasting response and full traveler explanation. The outside-quotation eat-then-leave parenthesis paraphrases the invitation and remains explanatory source context; no explicit dialogue words are dropped.',
    'Read all382 Urdu characters. Retain the complete source dialogue and its third-person/first-person framing as printed. Only the parenthetic invitation paraphrase outside the quotation is contextual; travel, fasting and half-prayer wording remain exact.',
    exclude_substrings={'hi':['(खा कर चले जाना)'],'ur':['( کھا کر چلے جانا )']})
add('nasai:2273','abbreviated_historical_encounter_report','Abu Umayya reporting his own arrival from a journey',
    'Read all139 Hindi characters. Retain the actually supplied arrival from travel to the Messenger as a finite report excerpt. The remainder announces an omitted full similar narration and stays context, with the source ravi spelling uncorrected.',
    'Read all122 Urdu characters. Retain the complete finite travel-arrival clause alone. The later omitted-report pointer is not filled from2271 or any other number.',
    stop_before={'hi':'रवि ने पूरी','ur':'آگے راوی'})
add('nasai:2275','historical_transmission_frame_and_prophetic_dialogue','Ayyub and Abu Qilaba in the transmission encounter, then an unnamed Qushayri sheikh relaying his unnamed paternal uncle',
    'Read all753 Hindi characters. Preserve the actual transmission encounter, its source-printed Ayyub/sheikh/addressee qualifications, and the unnamed uncle food/fasting exchange and all supplied concession subjects. Keep the two narrative voices as ordered components in one underlying report family. The two explicitly metalinguistic alternative-word comparisons are context, with the actual eating and invitation wording intact. No Anas identity is imported from2276.',
    'Read all714 Urdu characters. Retain the finite transmission dialogue and uncle encounter, actual quoted fasting reply including its source glyph defect, and all supplied traveler/pregnant/nursing wording without legal expansion. Source actor/addressee qualifications remain. Only the two metalinguistic variant comparisons and numbered footnote marks are contextual; the unknown sheikh and uncle remain unnamed.',
    exclude_substrings={
        'hi':["(रावी को शक है 'याकुल' कहा या 'युतइम' कहा)","(रावी को शक है 'अदनी फ़कुल' कहा या 'अदनी फ़तिइम' कहा)"],
        'ur':[' ۱؎','( راوی کو شک ہے «یا ٔکل» کہا یا «یطعم» کہا )','( راوی کو شک ہے «ادن فکل» کہا یا «ادن فاطعم» کہا )'],
        'ur-Latn':["(ravi ko shak hai 'ya'kul' kaha ya 'yut'im' kaha)","(ravi ko shak hai 'adni fakul' kaha ya 'adni fa'tim' kaha)"]},
    stop_before={'ur':' ۲؎'})
SPECS['nasai:2275']['read_languages']=['hi','ur','ar','en','ur-Latn']
SPECS['nasai:2275']['languages']=['hi','ur','ar','en','ur-Latn']
SPECS['nasai:2275']['field_notes'].update({
    'ar':'Read all640 Arabic characters and diacritics. Preserve the complete source chain, finite Ayyub/AbuQilaba/sheikh encounter and unnamed uncle report. The inline yakul-or-yatam and invitation alternatives remain source-transmitted wording variants within the report, not a claim that the Prophet uttered both alternatives. Keep the actual pregnant/nursing terms and do not invent either unnamed relative identity.',
    'en':'Read all477 English characters. Preserve the actual transmission encounter and report, including Shailh/BuQilabah defects and the unclosed final punctuation. This source field says pregnant woman and the sick, whereas the other independently read fields say nursing. Retain that exact English discrepancy visibly, without replacing sick or asserting exact cross-language equivalence.',
    'ur-Latn':'Read all864 Roman characters. Preserve the two connected narrative voices, source identity/addressee labels and actual full dialogue. The two explicit foreign-word comparison parentheses are contextual apparatus. Keep all actual concession subjects, and leave the source unknown relatives unnamed.'})
SPECS['nasai:2275']['annotations']={'en':'The supplied English ends with the sick, while this occurrence Arabic, Hindi, Urdu and Roman Urdu supply nursing women. This wording discrepancy is preserved verbatim and is not certified as an exact translation or counterpart; no source repair was made.'}
for lang,marker in {
    'hi':'तो (कुशैरी) शैख़ ने कहा:',
    'ur':'تو ( قشیری ) شیخ نے کہا:',
    'ar':'فَقَالَ الشَّيْخُ حَدَّثَنِي عَمِّي',
    'en':'The old man said:',
    'ur-Latn':'toh (Qushairi) sheikh ne kaha:',
}.items():
    SPECS['nasai:2275'].setdefault('components',{})[lang]=[
        {'stop_before':marker,'report_type':'historical_transmission_dialogue','speaker':'Ayyub reporting the encounter and Abu Qilaba request; source own participant labels preserved'},
        {'start_at':marker,'report_type':'prophetic_dialogue_report_with_source_wording_qualifications','speaker':'Unnamed Qushayri sheikh relaying his unnamed paternal uncle; internal source wording alternatives are not the Prophet own uncertainty'},
    ]
add('nasai:2276','historical_transmission_frame_and_prophetic_dialogue','Ayyub reports Abu Qilaba guidance and an unnamed transmitter relaying his source-named relative Anas ibn Malik',
    'Read all709 Hindi characters. Keep the actual offer to meet the transmitter, guidance and meeting, the source-named relative Anas ibnMalik, seized-camel circumstance and complete food/fasting dialogue. Preserve the listen imperative and both traveler concessions. Do not identify this Anas further or transfer his name into neighboring anonymous reports.',
    'Read all624 Urdu characters. Retain both connected narrative voices, the exact named-relative description, seized camels, invitation and fasting reply, and the supplied listen/traveler statement. No pregnancy or nursing continuation absent from this field is inserted.')
add('nasai:2277','prophetic_dialogue_report','An unnamed Companion reporting his own visit and exchange',
    'Read all462 Hindi characters. Preserve the unnamed Companion visit for a need, midday food, invitation, fasting response and all actually printed traveler/pregnancy/nursing subjects. No identity or expanded legal scope is guessed.',
    'Read all368 Urdu characters. Retain the full own food/fasting dialogue and every supplied concession term. Only the terminal footnote marker is context; the unspecified Companion remains unspecified.',
    stop_before={'ur':' ۱؎'})
add('nasai:2279','prophetic_dialogue_report','Hani ibn Shikhir relaying an unnamed Balharish man from his unnamed father',
    'Read all484 Hindi characters. Preserve the exact unnamed family chain, traveler/fasting/eating circumstances, actual come invitation, subsequent question and reply. The parenthetic join-the-meal expansion after the quoted come is explanation, retained as context. Do not supply Abdullah ibnShikhir from2281.',
    'Read all459 Urdu characters. Keep both actual invitation/question turns and the fasting/half-prayer answer with the own unnamed father attribution. Only the outside-quotation meal-participation paraphrase is context; no absent name or tribe normalization is introduced.',
    exclude_substrings={'hi':['(खाना में शरीक हो जाओ)'],'ur':['( کھانے میں شریک ہو جاؤ )']})
add('nasai:2281','prophetic_dialogue_report','Abdullah ibn Shikhir reporting his own travel and exchange',
    'Read all413 Hindi characters. Preserve this occurrence named reporter, traveler and fasting state, the actual invitation and both question-answer turns. The parenthetic eat-food expansion of come is contextual explanation; the eating circumstance and every actual reported condition remain.',
    'Read all382 Urdu characters. Retain the source named Abdullah, full encounter and complete fasting/half-prayer dialogue. Only the parenthetic invitation paraphrase is context. Do not use this name to complete the anonymous father in2279.',
    exclude_substrings={'hi':['(खाना खा लो)'],'ur':['( کھانا کھا لو )']})
add('nasai:2288','prophetic_practice_report','Ibn Abbas reporting the journey and fasting sequence',
    'Read all215 Hindi characters. Preserve fasting in Medina, the parenthetic actual onward-travel action, arrival at Qadid, breaking the fast and remaining without fasting until Mecca. The action parenthesis and endpoints carry the narrative sequence and remain; no Ramadan date is supplied.',
    'Read all191 Urdu characters. Retain the complete own travel/fasting sequence and the parenthetic movement, Qadid and Mecca endpoints. Do not substitute Usfan or another occurrence time wording.')
add('nasai:2291','prophetic_practice_report','Ibn Abbas reporting the Ramadan journey and public drinking act',
    'Read all259 Hindi characters. Preserve Ramadan travel, fasting until Usfan, asking for a vessel, drinking during the day while people watched and subsequent nonfasting. No drink identity or additional purpose is invented.',
    'Read all237 Urdu characters. Retain the entire own act and all timing, location and public-observation details. The source says a vessel and drinking; no unprinted contents are added.')
SPECS['nasai:2295']={
    'id':'nasai:2295','decision':'exclude','report_type':'source_address_formula_and_omitted_report_pointer','speaker':'Sulaiman ibn Yasar relaying Hamza ibn Amr initial address; the subsequent question/report is absent',
    'reason':'All five supplied fields were completely read. They provide only the introductory address O Messenger of Allah, a similar-report pointer and mursal qualification; no substantive question, answer or report body follows. Preserve the entire occurrence as resolved source-only without importing2298 or another nearby report.',
    'read_languages':['hi','ur','ar','en','ur-Latn'],'languages':[],
    'field_notes':{
        'hi':'Read all146 Hindi characters. The chain, opening vocative and omitted-similar-hadith/mursal notice supply no actual question or reply. Do not reconstruct it from a neighbor.',
        'ur':'Read all134 Urdu characters. Only Hamza opening address precedes the missing-story pointer and mursal/footnote apparatus; no body is printed.',
        'ar':'Read all174 Arabic characters including the full Qutayba/Layth/Bukayr/Sulaiman chain and Hamza vocative. Mithlahu mursal follows immediately; the referred-to body is absent.',
        'en':'Read all141 English characters. It supplies only the address and similar-in-Mursal notice. Preserve the printed from spelling rather than correcting it, and do not import the absent question.',
        'ur-Latn':'Read all160 Roman characters. The initial address is followed directly by the upper-hadith similarity pointer and mursal statement, without the omitted narration.',
    }}
add('nasai:2298','prophetic_question_and_answer_report','Hamza ibn Amr Aslami reporting his own request and the Prophet reply',
    'Read all189 Hindi characters. Preserve the travel-fasting capacity, actual parenthetic question and the supplied affirmative option only. This field ends after if you wish then fast; do not add Urdu alternative permission or terminal punctuation absent from Hindi.',
    'Read all206 Urdu characters. Keep the complete capacity statement, parenthetic actual question and both supplied options to fast or not fast. The second option is this field own wording and is not copied into shorter Hindi.',
    annotations={'hi':'This Hindi field supplies only the affirmative if-you-wish-then-fast reply. Its Urdu sibling additionally supplies the option not to fast. The shorter Hindi source ending is preserved exactly; no continuation was added.'})
