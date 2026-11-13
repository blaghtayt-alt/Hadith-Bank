"""Explicit source-bound decisions authored only after the55-field source-first freeze."""
from source_first_notes import NOTES

records=[]
FOOTNOTE='Exact source footnote label retained as context; surrounding actual narration is unchanged.'
def cut(text,reason,count=1):return {'text':text,'expected_count':count,'reason':reason}
def part(start,end,component,kind,speaker,family):
    return {'from':start,'to':end,'component_id':component,'report_type':kind,'speaker':speaker,'source_report_family_id':family}
def field(k,lang,speaker,kind='prophetic_report',end=None,cuts=(),parts=None):
    return {'action':'excerpt','reason':NOTES[(k,lang)],'spans':parts or [part(None,end,'reported-account',kind,speaker,k+':'+lang+':reported-account')],'omit_source_context':list(cuts)}
def add(k,hi,ur):records.append({'key':k,'decision':'register','reason':'Each admitted own field was completely read; actual speakers and source-limited wording are preserved independently. Unread siblings remain source context.','fields':{'hi':hi,'ur':ur}})
def exclude(k,kind):
    records.append({'key':k,'decision':'exclude','reason':'All five complete own-language fields were read and contain only the specifically described source/transmission apparatus, with no eligible underlying report body supplied.','fields':{lang:{'action':'source_context','reason':NOTES[(k,lang)],'report_type':kind,'speaker':'No underlying narrated body is supplied; the printed transmitter/critic wording remains visible source context.'} for lang in ('hi','ur','ar','en','ur-Latn')}})

k='abudawud:2385'
add(k,field(k,'hi','Jabir transmits Umar’s fasting/kiss incident and his dialogue with the explicitly addressed Messenger; the rhetorical rinse consequence remains.'),field(k,'ur','Jabir transmits Umar’s fasting/kiss incident and his dialogue with the explicitly addressed Messenger; the rhetorical rinse consequence remains.'))
k='abudawud:2403'
add(k,field(k,'hi','Hamzah narrates his own circumstances and question and the explicitly addressed Messenger’s choice reply.'),field(k,'ur','Hamzah narrates his own circumstances and question and the explicitly addressed Messenger’s choice reply.'))
k='abudawud:2405'
add(k,field(k,'hi','Anas reports the actual travelling group’s fasting practices and mutual absence of reproach.','companion_observation_of_prophetic_company'),field(k,'ur','Anas reports the actual travelling group’s fasting practices and mutual absence of reproach.','companion_observation_of_prophetic_company'))
k='abudawud:2409'
add(k,field(k,'hi','AbuDarda reports the unnamed campaign, heat and two named fasting exceptions.','companion_observation_of_prophetic_company'),field(k,'ur','AbuDarda reports the unnamed campaign, heat and two named fasting exceptions.','companion_observation_of_prophetic_company'))
k='abudawud:2417'
add(k,field(k,'hi','AbuSaid transmits the Messenger’s three paired prohibitions.',cuts=[cut('(जिस से स़त्र खुलने का अंदेशा रहता है)','Explanatory exposure-risk gloss after the stated garment form.')]),field(k,'ur','AbuSaid transmits the Messenger’s three paired prohibitions.',cuts=[cut('۱؎',FOOTNOTE),cut('۲؎',FOOTNOTE),cut('( جس سے ستر کھلنے کا اندیشہ رہتا ہے )','Explanatory exposure-risk gloss after the stated garment form.')]))
exclude('abudawud:2423','source_provenance_criticism_without_underlying_report_body')
k='abudawud:2426'
add(k,field(k,'hi','Per the two separately framed finite units; the Hindi reply’s ultimate speaker link is absent.',cuts=[cut('(पीर)','Lexical synonym for the already supplied Monday term.')],parts=[
    part('कहा: अल्लाह के रसूल!','इसी दिन पैदा हुआ','question-fragment','transmitted_question_fragment','An unnamed questioner addresses the Messenger; AbuQatadah is the printed transmission frame, not automatically this questioner.',k+':hi:added-fasting-variant'),
    part('इसी दिन पैदा हुआ',None,'birth-revelation-fragment','affirmative_first_person_variant_with_missing_speaker_link','The Hindi supplies a first-person birth/revelation clause but omits the reply/link attribution; its ultimate speaker is left unresolved in this field.',k+':hi:added-fasting-variant')]),
 field(k,'ur','Per the actual question and explicit Messenger reply.',parts=[
    part('کہا: اللہ کے رسول!','آپ صلی اللہ علیہ وسلم نے فرمایا:','question-fragment','transmitted_question_fragment','An unnamed questioner addresses the Messenger within the printed AbuQatadah transmission frame.',k+':ur:added-fasting-variant'),
    part('آپ صلی اللہ علیہ وسلم نے فرمایا:',None,'birth-revelation-reply','explicitly_attributed_prophetic_variant','The source expressly attributes this first-person birth/revelation reply to the Messenger; no omitted original body or unstated day identity is added.',k+':ur:added-fasting-variant')]))
k='abudawud:2456'
add(k,field(k,'hi','UmmHani narrates the conquest-day drink and fasting dialogue with the Messenger, preserving Fatimah and the side positions.'),field(k,'ur','UmmHani narrates the conquest-day drink and fasting dialogue with the Messenger, preserving Fatimah and the side positions.',cuts=[cut('۱؎',FOOTNOTE)]))

k='tirmidhi:2382'
add(k,field(k,'hi','Shufayya’s encounter frames AbuHurayrah’s actual shortened account of the Messenger; the Hindi has no Muawiyah sequel.',cuts=[cut('(घुटने)','Lexical knee synonym after the already printed zano term.')]),
 field(k,'ur','Per separately attributed components; the Muawiyah reception is not Prophetic speech.',cuts=[cut('( قرآن سیکھنے سے )','Explanatory motive gloss after the already supplied Quran-study questions.'),cut('( سورۃ ہود: ۱۶ )','Explicit Surah/verse locator; actual recitation and Urdu rendering remain.')],parts=[
    part(None,'امام ترمذی کہتے ہیں: ولید','abuhurayrah-judgment-report','prophetic_report_with_companion_transmission_scene','Shufayya reports the AbuHurayrah encounter, distress and the Messenger’s judgment report and knee gesture.',k+':ur:judgment-report'),
    part('ولید ابوعثمان کہتے ہیں:','ابوعثمان کہتے ہیں: علاء','shufayya-notification','transmitted_historical_notification','WalidAbuUthman transmits Ukbah’s statement that Shufayya informed Muawiyah of this report.',k+':ur:muawiyah-reception'),
    part('ابوعثمان کہتے ہیں: علاء','امام ترمذی کہتے ہیں: یہ حدیث حسن غریب ہے۔','muawiyah-reception-and-recitation','historical_companion_reaction_with_actual_recitation','AbuUthman transmits Alaa’s account of Muawiyah’s reaction, crying and actual Quran recitation/rendering; Muawiyah’s statements are not words of the Messenger.',k+':ur:muawiyah-reception')]))
k='tirmidhi:2392'
add(k,field(k,'hi','Miqdam transmits the Messenger’s instruction to inform the loved brother.',end='इमाम तिर्मिज़ी कहते हैं:'),field(k,'ur','Miqdam transmits the Messenger’s instruction to inform the loved brother.',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2397'
add(k,field(k,'hi','AbuWail transmits Aishah’s own comparison of the Messenger’s pain; it is not a direct Messenger quotation.','companion_observation_of_prophetic_condition',end='इमाम तिरमिधि कहते हैं:'),field(k,'ur','AbuWail transmits Aishah’s own comparison of the Messenger’s pain; it is not a direct Messenger quotation.','companion_observation_of_prophetic_condition',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2406'
add(k,field(k,'hi','Ukbah ibnAmir transmits his salvation question and the Messenger’s three instructions.',end='इमाम तिर्मिज़ी कहते हैं:'),field(k,'ur','Ukbah ibnAmir transmits his salvation question and the Messenger’s three instructions.',end='امام ترمذی کہتے ہیں:',cuts=[cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2410'
add(k,field(k,'hi','Sufyan ibnAbdullah narrates his two questions and the Messenger’s actual words/tongue gesture; defective Hindi joins stay unchanged.',end='इमाम तिरमिधि कहते हैं:',cuts=[cut('(माँ\'बूद-इ-हक़ीक़ी)','Lexical definition of the already printed Lord term.')]),field(k,'ur','Sufyan ibnAbdullah narrates his two questions and the Messenger’s actual words/tongue gesture.',end='امام ترمذی کہتے ہیں:',cuts=[cut('( معبود حقیقی )','Lexical definition of the already printed Lord term.')]))
k='tirmidhi:2413'
add(k,field(k,'hi','Per separately attributed Companion narrative and Prophetic approval.',parts=[
    part(None,'इसके बाद दोनों नबी अकरम','salman-visit-and-instruction','companion_practice_and_instruction_with_prophetic_context','AbuJuhayfah reports the initial brotherhood and Salman/AbuDarda household dialogue; the rights instruction is Salman’s own speech.',k+':hi:salman-abudarda-visit'),
    part('इसके बाद दोनों नबी अकरम','इमाम तिरमिज़ी कहते हैं:','prophetic-approval','prophetic_affirmation_of_companion_instruction','AbuJuhayfah’s narrative reports their visit and the Messenger’s explicit approval of Salman.',k+':hi:salman-abudarda-visit')]),
 field(k,'ur','Per separately attributed Companion narrative and Prophetic approval.',cuts=[cut('۱؎',FOOTNOTE)],parts=[
    part(None,'اس کے بعد دونوں نبی اکرم','salman-visit-and-instruction','companion_practice_and_instruction_with_prophetic_context','AbuJuhayfah reports the initial brotherhood and Salman/AbuDarda household dialogue; the rights instruction is Salman’s own speech.',k+':ur:salman-abudarda-visit'),
    part('اس کے بعد دونوں نبی اکرم','امام ترمذی کہتے ہیں:','prophetic-approval','prophetic_affirmation_of_companion_instruction','AbuJuhayfah’s narrative reports their visit and the Messenger’s explicit approval of Salman.',k+':ur:salman-abudarda-visit')]))
k='tirmidhi:2429'
add(k,field(k,'hi','AbuHurayrah transmits the actual recitation/question/answer; missing Hindi explanatory links are not supplied.',end='इमाम तिरमिधि कहते हैं:'),field(k,'ur','AbuHurayrah transmits the actual Quran recitation and the Messenger’s own supplied explanation.',end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2434'
add(k,field(k,'hi','AbuHurayrah transmits the Messenger’s full own-field intercession narrative with nested speakers; the explicit return-to-Messenger parenthesis is retained.',end='इमाम तिरमिज़ी कहते हैं:',cuts=[
    cut('(यानी गहरे दोस्त)','Lexical definition of the printed Khalil term.'),
    cut('(अबू हय्यान ने अपनी रिवायत में इन तीनों झूठ का ज़िक्र किया है)','Pointer to a differently transmitted list not printed here; no missing falsehoods are supplied.'),
    cut('(उम्मत-ए-मुहम्मदी)','Explanatory community label repeating the already supplied own-community referent.'),
    cut('(दाख़िल होने में)','Explanatory gloss of sharing the already specified gates.')]),
 field(k,'ur','AbuHurayrah transmits the Messenger’s full own-field intercession narrative with nested speakers; the explicit return-to-Messenger parenthesis is retained.',end='امام ترمذی کہتے ہیں:',cuts=[
    cut('( یعنی گہرے دوست )','Lexical definition of the printed Khalil term.'),
    cut('( ابوحیان نے اپنی روایت میں ان تینوں جھوٹ کا ذکر کیا ہے )','Pointer to a differently transmitted list not printed here; no missing falsehoods are supplied.'),
    cut('( امت محمد )','Explanatory community label repeating the already supplied own-community referent.'),
    cut('( داخل ہونے میں )','Explanatory gloss of sharing the already specified gates.'),cut('۱؎',FOOTNOTE)]))
k='tirmidhi:2454'
add(k,field(k,'hi','IbnMasud reports the Messenger’s drawing and actual interpretation, retaining the source’s awkward line/object mapping.',cuts=[cut('(यानी चकोर)','Lexical square synonym.'),cut('(यानी उसकी आरज़ूएं हैं)','Explanatory aspirations gloss; the actual later outside-line/hope predicate remains.')]),field(k,'ur','IbnMasud reports the Messenger’s drawing and actual interpretation, retaining the source’s awkward line/object mapping.',cuts=[cut('( یعنی چوکور )','Lexical square synonym.'),cut('( یعنی اس کی آرزوئیں ہیں )','Explanatory aspirations gloss; the actual later outside-line/hope predicate remains.'),cut('۱؎',FOOTNOTE)]))

exclude('muslim:2464','same_chain_and_explicitly_omitted_wording_only')
k='muslim:2465'
add(k,field(k,'hi','Ayyub/Muhammad/Ubaydah transmit Ali’s own description, withheld promise and oath attestations; Ubaydah is the source-identified questioner and the actual promised content remains absent.','companion_statement_with_attested_prophetic_hearing'),field(k,'ur','Ayyub/Muhammad/Ubaydah transmit Ali’s own description, withheld promise and oath attestations; Ubaydah is the source-identified questioner and the actual promised content remains absent.','companion_statement_with_attested_prophetic_hearing'))
exclude('muslim:2466','hearing_assurance_and_omitted_report_pointer_only')
k='muslim:2474'
add(k,field(k,'hi','Waki/Shubah are the printed transmission frame; the actual finite replacement clause has no ultimate speaker identified in this own field.','affirmative_transmitted_variant_with_unknown_original_speaker',parts=[part("'हमारे लिए सदक़ा हलाल नहीं'"," के अलफ़ाज़ कहे.",'new-alms-variant','affirmative_transmitted_variant_with_unknown_original_speaker','The ultimate speaker is unspecified; no Prophetic identity is borrowed from a prior occurrence.',k+':hi:new-alms-variant')]),field(k,'ur','Waki/Shubah are the printed transmission frame; the actual finite replacement clause has no ultimate speaker identified in this own field.','affirmative_transmitted_variant_with_unknown_original_speaker',parts=[part('" ہمارے لیے صدقہ حلا ل نہیں "',' کہا ہے','new-alms-variant','affirmative_transmitted_variant_with_unknown_original_speaker','The ultimate speaker is unspecified; no Prophetic identity is borrowed from a prior occurrence.',k+':ur:new-alms-variant')]))
k='ibnmajah:2449'
add(k,field(k,'hi','Rafi ibnKhadij transmits the Messenger’s prohibitions and three cultivation categories, including the source-specified gift-or-loan alternative.',cuts=[cut('(नक़द)','Lexical cash gloss after gold/silver.')]),field(k,'ur','Rafi ibnKhadij transmits the Messenger’s prohibitions and three cultivation categories, including the source-specified gift-or-loan alternative.',cuts=[cut('( نقد )','Lexical cash gloss after gold/silver.')]))
k='ibnmajah:2450'
add(k,field(k,'hi','IbnUmar narrates the group’s practice, hearing Rafi’s report of the Messenger’s prohibition, and consequent cessation.','companion_practice_with_indirect_prophetic_report',cuts=[cut('(बटाई खेती)','Lexical definition of the printed muzaraat term.')]),field(k,'ur','IbnUmar narrates the group’s practice, hearing Rafi’s report of the Messenger’s prohibition, and consequent cessation.','companion_practice_with_indirect_prophetic_report',cuts=[cut('( بٹائی کھیتی )','Lexical definition of the printed muzaraat term.'),cut('۱؎',FOOTNOTE)]))

assert len(records)==23 and len({r['key'] for r in records})==23
assert sum(len(r['fields']) for r in records)==55
