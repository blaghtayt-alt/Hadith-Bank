"""Individually authored boundaries after all46 complete own-field readings."""
from source_first_notes import NOTES

records=[]

def omit(text,reason,count=1):
    return {'text':text,'expected_count':count,'reason':reason}

def pair(key,kind,hi_speaker,ur_speaker=None,ends=(None,None),cuts=((),())):
    fields={}
    for lang,speaker,end,omissions in zip(('hi','ur'),(hi_speaker,ur_speaker or hi_speaker),ends,cuts,strict=True):
        fields[lang]={'action':'excerpts','reason':NOTES[(key,lang)],'report_type':kind,'speaker':speaker,
            'spans':[{'from':None,'to':end,'component_id':'reported-account','report_type':kind,'speaker':speaker,'source_report_family_id':key+':'+lang+':source-numbered-report'}],
            'omit_source_context':list(omissions)}
    row={'key':key,'decision':'register','reason':'The actually read own-language fields supply finite reports, expressly abbreviated wording or independently attributed sayings. Source defects, missing links, exact speaker limits and all removed apparatus remain preserved; no external identity or absent text is supplied.','fields':fields}
    records.append(row);return row

foot=lambda text:omit(text,'Exact numbered source footnote marker; the referenced note and surrounding source remain context.')
locator=lambda text:omit(text,'Explicit source surah/verse locator label, kept separately from the actual quoted verse and its supplied rendering.')
gloss=lambda text,reason:omit(text,reason)

pair('abudawud:2624','companion_revelation_occasion_report',
     'Ibn Abbas reports the source-named Abdullah expedition and its claimed revelation occasion. The verse and source translation are quoted within that Companion assertion; participant-name defects remain exact.',
     cuts=([locator('(सौराह आन-निसा: ५९)')],[locator('( سورۃ النساء: ۵۹ )')]))
pair('abudawud:2629','companion_report_of_prophetic_dispatched_instruction',
     'Muadh ibn Anas reports campaign participation, constricted camps/routes and the dispatched announcement. The defective Hindi final object/predicate is preserved without borrowing Urdu.',
     'Muadh ibn Anas reports the camp/road obstruction and the Messenger’s dispatched announcement, including both alternatives and its exact consequence.',
     cuts=([],[foot('۱؎')]))
pair('abudawud:2630','abbreviated_companion_campaign_observation',
     'Muadh’s actually supplied campaign-participation observation with Allah’s Prophet. The subsequent same-meaning pointer supplies no additional body.',
     ends=('फिर रवि ने','پھر راوی نے'))
pair('abudawud:2635','companion_report_of_prophetic_conditional_instruction',
     'The source-named ईसाम मुज़नी reports the expedition commission and the mosque-or-adhan conditions of the instruction not to kill anyone.',
     'The source-named عصام مزنی reports the expedition commission and both mosque/adhan conditions of the no-killing instruction.')
pair('abudawud:2638','companion_expedition_account_with_prophetic_commission',
     'Salama narrates Abu Bakr’s commissioned leadership, the night attack, actual slogan and his own seven-households statement. The latter acts are his reported account, not relabelled direct Prophetic commands.',
     ends=(None,'۲؎'),
     cuts=([gloss('(कोड)','Lexical code synonym for the already supplied slogan term; the actual slogan remains.')],[gloss('( کوڈ )','Lexical code synonym for the already supplied slogan term; the actual slogan remains.'),foot('۱؎')]))
pair('abudawud:2643','companion_account_with_prophetic_rebuke_dialogue',
     'Usama reports the man’s confession, killing, his own fear-of-sword explanation, the Messenger’s repeated challenge and his final wish. The intention alternatives and despite-this parenthesis remain this source’s narrative rendering.',
     cuts=([],[foot('۱؎'),foot('۲؎')]))
pair('abudawud:2645','companion_report_of_incident_and_prophetic_response',
     'Jarir reports the Khatham incident, the half-compensation response and the actual question/answer about the two fires. The metaphor’s explicit explanatory alias is kept separately.',
     ends=(None,'۲؎'),
     cuts=([gloss('(यानी इस्लाम और कुफ़्र की)','Explicit conceptual explanation of the two-fire metaphor, not a separately framed action or condition.')],[foot('۱؎'),gloss('( یعنی اسلام اور کفر کی )','Explicit conceptual explanation of the two-fire metaphor, not a separately framed action or condition.')]))
pair('abudawud:2649','companion_encounter_with_reported_prophetic_reply',
     'Khabbab recounts the complaint, response and attributed endurance/journey prediction. The complaint domain, hearing transition, sheep/wolf exception and all source defects remain exact.')
pair('abudawud:2654','companion_expedition_account_with_allocation_dialogue',
     'Salama ibn al-Akwa reports the visitor, pursuit, killing, return and allocation dialogue. The spy-discovery qualification is preserved as the source’s causal framing; every action and nested voice remains attributed.',
     ends=(None,'۱؎'))
pair('abudawud:2658','companion_report_of_prophetic_dismounting',
     'The source-named बारे reports the Hunayn encounter, a group’s scattering and the Messenger’s dismounting/walking. The plural pronoun and defective source name are not externally resolved.',
     'The source-named براء reports the Hunayn encounter, scattering and the Messenger’s dismounting/walking; the source’s pronoun scope remains unchanged.',
     cuts=([gloss('(यानि शिकस्त खा कर इधर उधर भाग खड़े हुए)','Explicit yani expansion of the supplied scattering word; retain the explanation as context without adding a separate event.')],[gloss('( یعنی شکست کھا کر ادھر ادھر بھاگ کھڑے ہوئے )','Explicit yani expansion of the supplied scattering word; retain the explanation as context without adding a separate event.')]))
pair('abudawud:2668','companion_report_of_prophetic_rebuke',
     'The source-named अब्दुल्लाह बिन उम्र reports an unnamed slain woman in an unspecified campaign and the Messenger’s rebuke concerning women and children; no missing identity is filled.',
     'Abdullah ibn Umar reports the unnamed slain woman and the Messenger’s rebuke concerning killing women and children, with the campaign left unspecified.')
pair('abudawud:2674','expressly_abbreviated_prophetic_condition_in_companion_report',
     'Abu Hurayrah reports the Messenger’s commission and actual if-you-find-so-and-so condition. The consequent and target identities are not printed and remain unknown; no same-meaning pointer is used to complete them.',
     ends=('फिर रावी ने','پھر راوی نے'))
pair('abudawud:2678','companion_expedition_account_with_captive_dialogue',
     'Jundab’s source account contains the expedition commission and Harith/troop dialogue, including both conditional replies and the one-day/one-night period. The soldiers’ words are not attributed to the Prophet.')
pair('abudawud:2688','companion_incident_and_revelation_occasion_report',
     'Anas reports the eighty men’s intended attack, capture/release and a claimed revelation occasion, including actual verse wording and rendering. Hindi’s source place-name defect remains untouched.',
     'Anas reports the eighty-men incident and the actual supplied verse/rendering; the unquoted remainder of the verse is not completed.',
     cuts=([gloss('(८०)','Parenthetic numeral duplicating the already printed eighty; the actual stated quantity remains outside it.'),locator('(सौराह आल-फतह: २४)')],[gloss('إلى آخر الآية','Bare to-the-end-of-the-verse omission pointer, not supplied quotation wording.'),locator('( سورۃ الفتح: ۲۴ )')]))
pair('abudawud:2690','companion_transmitted_ransom_and_revelation_report',
     'Ibn Abbas expressly relays Umar’s Badr/ransom and revelation account. The abbreviated quotation, damaged Hindi rendering, unbeliever-object qualifier and final spoils statement remain source-limited.',
     'Ibn Abbas relays Umar’s account with the source’s bounded beginning/end citation and its supplied rendering. The unbeliever-object scope remains; missing intervening verse wording is not invented.',
     cuts=([locator('(सौराह आल-अनफाल: ६७-६८)'),gloss('(गनीमत के माल)','Lexical definition of the preceding spoils word, not an added narrated event or object restriction.')],[locator('( سورۃ الأنفال: ۶۷-۶۸ )')]))
pair('abudawud:2696','companion_report_of_sale_and_prophetic_prohibition',
     'The source attributes separation of the bondwoman/child to Ali and the prohibition/sale reversal to the Messenger. The subsequent compiler chronology is source criticism, not another reported scene.',
     ends=('अबू दाऊद कहते हैं:','ابوداؤد کہتے ہیں:'))
r=pair('abudawud:2698','companion_account_with_explicit_transmitted_actor_variant',
     'The source preserves the main return account and Abu Dawud’s actual other-version clause naming a different returning actor. Neither is harmonized into the other or counted as a new incident.')
for lang,marker in [('hi','अबू दाऊद कहते हैं:'),('ur','ابوداؤد کہتے ہیں:')]:
    family='abudawud:2698:'+lang+':source-numbered-report'
    r['fields'][lang]['spans']=[
        {'from':None,'to':marker,'component_id':'main-return-account','report_type':'companion_report_of_prophetic_return','speaker':'Ibn Umar’s source account attributes the slave’s return and exclusion from distribution to the Messenger.','source_report_family_id':family},
        {'from':marker,'to':None,'component_id':'other-version-returning-actor','report_type':'explicit_transmitted_actor_variant','speaker':'Abu Dawud reports that other transmitters attribute the finite returning action to Khalid ibn Walid. This is a qualified variant of the same account, not his eyewitness claim or a new scene.','source_report_family_id':family},
    ]
r=pair('tirmidhi:2622','successor_community_report_and_independently_heard_scholarly_saying',
     'Abdullah ibn Shaqiq’s Companion-view report and Tirmidhi’s explicitly heard Abu Musab statement retain their distinct actual speakers. The latter is a historical scholarly quotation, not Prophetic speech, current legal advice or endorsement.',
     cuts=([gloss('(यानि ज़बान से इक़रार करने)','Explicit lexical definition of qawl; the substantive quoted saying and its source defect remain separate.')],[gloss('( یعنی زبان سے اقرار کرنے )','Explicit lexical definition of qawl; the substantive quoted saying and actual conditional alternatives remain separate.')]))
for lang,marker in [('hi','इमाम तिरमिधि कहते हैं:'),('ur','امام ترمذی کہتے ہیں:')]:
    r['fields'][lang]['spans']=[
        {'from':None,'to':marker,'component_id':'successor-community-view-report','report_type':'successor_report_of_companion_view','speaker':'Abdullah ibn Shaqiq reports the Companions’ stated view of abandoning prayer, not a direct Prophetic saying.','source_report_family_id':'tirmidhi:2622:'+lang+':companion-view-report'},
        {'from':marker,'to':None,'component_id':'independently-heard-abu-musab-saying','report_type':'named_scholarly_saying_transmitted_by_tirmidhi','speaker':'Tirmidhi explicitly reports hearing Abu Musab’s substantive doctrinal/legal saying. Hindi’s missing repentance contrast remains unfilled; this attributed historical saying is not endorsed or relabelled as Prophetic teaching.','source_report_family_id':'tirmidhi:2622:'+lang+':abu-musab-heard-saying'},
    ]
pair('tirmidhi:2665','companion_report_of_writing_request_and_refusal',
     'Abu Said reports requesting writing permission and the refusal, with the source-rendered early-Islam temporal and hadith-object restrictions preserved. Later route discussion is context.',
     ends=('इमाम तिरमिधि कहते हैं:','۱؎'))
pair('tirmidhi:2680','source_explicitly_marfu_report_via_companion',
     'The source explicitly marks Abu Hurayrah’s report marfu and supplies the study-journey comparison. The anonymous Medina scholar is not identified using the compiler’s later interpretations.',
     ends=('इमाम तिर्मिज़ी कहते हैं:','امام ترمذی کہتے ہیں:'))
pair('tirmidhi:2683','reported_prophetic_answer_with_source_limited_question',
     'The source-named Yazid supplies hearing/fear/request fragments and the explicitly introduced answer. Hindi’s missing links remain visible; no fuller Urdu question is inserted.',
     'Yazid’s complete question concerning earlier/later reports and the Messenger’s answer are retained independently; subsequent chain/name criticism remains context.',
     ends=(None,'۱؎'),
     cuts=([gloss('(आवल-ो-आखिर)','Appositional labels repeating the earlier/later pair already supplied in the body; the actual both-periods scope remains.')],[gloss('( کوئی ایسی بات )','Lexical synonym of the already supplied saying/kalima noun, not additional requested content.'),gloss('( اول و آخر )','Appositional labels repeating the already supplied earlier/later pair; the actual both-periods scope remains.')]))
r=pair('tirmidhi:2690','companion_reception_account_with_embedded_prophetic_instruction',
     'Abu Said recounts Abu Musa/Umar’s reception dialogue, Abu Musa’s bounded Prophetic quotation and resumed testimony. Printed inner speech, additional waiting, hearing transition and visitor identity remain as source-rendered scope.',
     ends=(None,'۱؎'))
for lang,quote_marker,resume_marker,end in [
    ('hi','क्या रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने यह नहीं फरमाया:','(यह सुन कर)',None),
    ('ur','کیا رسول اللہ صلی اللہ علیہ وسلم نے یہ نہیں فرمایا:','( یہ سن کر )','۱؎'),
]:
    family='tirmidhi:2690:'+lang+':source-reception-and-testimony-account'
    r['fields'][lang]['spans']=[
        {'from':None,'to':quote_marker,'component_id':'companion-reception-and-proof-request','report_type':'companion_reported_reception_dialogue','speaker':'Abu Said’s account reports Abu Musa’s requests, Umar’s inner responses and proof demand, then Abu Musa’s appeal to the Ansar. Each nested speaker remains within this reception narrative.','source_report_family_id':family},
        {'from':quote_marker,'to':resume_marker,'component_id':'embedded-permission-instruction','report_type':'prophetic_instruction_quoted_in_companion_question','speaker':'Abu Musa asks whether the Messenger said the actual three-request permission instruction, as recounted by Abu Said. Its quotation and source rendering remain bounded; no new canonical occurrence is inferred.','source_report_family_id':family},
        {'from':resume_marker,'to':end,'component_id':'resumed-response-and-testimony','report_type':'companion_reception_and_testimony_continuation','speaker':'The narrative resumes the listeners’ response, Abu Said’s supportive utterance and identified visit, then Umar’s acknowledgement of not knowing the report. These are Companion/narrator voices, not Prophetic speech.','source_report_family_id':family},
    ]
pair('tirmidhi:2694','companion_report_of_prophetic_greeting_answer',
     'Abu Umamah reports the two-person greeting question and the answer’s actor/predicate. The parenthetic he-will-initiate is retained as source-rendered answer scope, not claimed as verbatim historical wording.',
     ends=('इमाम तिरमिधि कहते हैं:','امام ترمذی کہتے ہیں:'),cuts=([],[foot('۱؎')]))
