"""Explicit source-bound selections authored only after the complete original pass."""
from source_first_notes import NOTES

def field(key,lang,kind,speaker,end=None,cuts=(),parts=None):
    family=key+':'+lang+':source-numbered-report'
    return {'action':'excerpts','reason':NOTES[(key,lang)],'report_type':kind,'speaker':speaker,
      'spans':parts if parts is not None else [{'from':None,'to':end,'component_id':'reported-account','report_type':kind,'speaker':speaker,'source_report_family_id':family}],
      'omit_source_context':[{'text':literal,'expected_count':1,'reason':reason} for literal,reason in cuts]}

def part(key,lang,name,kind,speaker,start,end):
    return {'from':start,'to':end,'component_id':name,'report_type':kind,'speaker':speaker,'source_report_family_id':key+':'+lang+':source-numbered-report'}

records=[]
def row(key,hi,ur):
    records.append({'key':key,'decision':'register','reason':'The complete own Hindi and Urdu fields supply the individually selected actual report, finite fragment or substantive attributed scholarly dialogue. Other source languages remain unread context; all missing words, identities, original defects and metadata remain unchanged.','fields':{'hi':hi,'ur':ur}})

k='abudawud:2492';speaker='Umm Haram/Rumaisa supplies the sleep/waking, hair-washing, question and the Messenger’s no. The same-report pointer and compiler identity note are not an inferred continuation.'
row(k,field(k,'hi','abbreviated_companion_report_with_prophetic_reply',speaker,end='कमी बेशी के साथ बयां की.'),field(k,'ur','abbreviated_companion_report_with_prophetic_reply',speaker,end='، پھر انہوں نے یہی حدیث',cuts=[('۱؎','Exact source footnote label, retained as context; no source identity correction is inferred.')]))
k='abudawud:2521'
row(k,field(k,'hi','unnamed_companion_question_and_prophetic_reply','Hasna bint Muawiyah’s unnamed uncle supplies the question and this shorter answer. The underage restriction remains; Urdu’s martyr category is not added.'),field(k,'ur','unnamed_companion_question_and_prophetic_reply','Hasna bint Muawiyah’s unnamed uncle supplies the question and the full own list including martyrs. The underage restriction remains source-qualified.'))
k='abudawud:2527';speaker='Ya’la supplies the worker’s actual request, the three-dinar agreement and his later question to the Messenger, with the printed bounded reply.'
row(k,field(k,'hi','companion_contract_report_with_prophetic_reply',speaker),field(k,'ur','companion_contract_report_with_prophetic_reply',speaker))
k='abudawud:2535';speaker='The source route reaches Abdullah ibn Hawalah’s own visit/account. The expedition, Messenger’s three prayers, head-or-nape gesture and conditional future statement retain their printed participants and limits.'
row(k,field(k,'hi','companion_report_of_prophetic_prayer_and_conditional_saying',speaker),field(k,'ur','companion_report_of_prophetic_prayer_and_conditional_saying',speaker))
k='tirmidhi:2464';speaker='Abdur Rahman ibn Awf supplies his own collective recollection of hardship with the Messenger and later ease. This is Companion reflection, not the Prophet’s direct speech.'
row(k,field(k,'hi','companion_historical_reflection',speaker),field(k,'ur','companion_historical_reflection',speaker,end='۱؎'))
k='tirmidhi:2469';speaker='Aisha reports the leather pillow, its use and palm-bark filling. The furnishing alias and compiler apparatus remain context.'
row(k,field(k,'hi','companion_household_observation',speaker,cuts=[('(बिस्तर)','Lexical furnishing alias after the already named pillow; the complete actual object/use description remains.')]),field(k,'ur','companion_household_observation',speaker,end='۱؎',cuts=[('( بستر )','Lexical furnishing alias after the named pillow, preserved as source context without normalizing terminology.')]))
k='tirmidhi:2471';speaker='Aisha supplies the family’s own month-long household memory and dates/water livelihood, rather than words spoken by the Messenger.'
row(k,field(k,'hi','companion_household_testimony',speaker),field(k,'ur','companion_household_testimony',speaker,end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2473';speaker='Ali recounts his own hunger, clothing, work and dialogue with an unnamed garden owner, and final observation of the Messenger in the mosque. No unprinted Prophetic saying is supplied.'
row(k,field(k,'hi','companion_personal_historical_report',speaker),field(k,'ur','companion_personal_historical_report',speaker,end='۱؎'))
k='tirmidhi:2474';speaker='Abu Hurayrah transmits the actual hunger occasion and the Messenger’s one-date-per-person giving, retaining the source’s only/each scope.'
row(k,field(k,'hi','companion_report_of_prophetic_giving',speaker),field(k,'ur','companion_report_of_prophetic_giving',speaker,end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2475';fs={}
for lang,q,resume,end in [('hi','उन से कहा गया:','उन्होंने फ़रमाया:',None),('ur','ان سے کہا گیا:','انہوں نے فرمایا:','۱؎')]:
    ps=[part(k,lang,'mission-and-ration','companion_mission_report','Jabir recounts the three-hundred-person mission and dwindling one-date ration.',None,q),part(k,lang,'later-ration-question-and-response','qualified_later_question_and_companion_response','An unnamed person asks Abu Abdullah about the ration; the printed first-person response follows with an abbreviated reply link. No questioner identity or missing link is invented.',q,resume),part(k,lang,'resumed-fish-account','companion_resumed_mission_report','The explicitly resumed Jabir narration supplies the sea fish and eighteen-day eating account.',resume,end)]
    fs[lang]=field(k,lang,'companion_mission_report_with_later_question','Jabir’s mission account, the later unnamed question/reply and resumed fish episode are three ordered components of one source report family.',parts=ps)
row(k,fs['hi'],fs['ur'])
k='tirmidhi:2479';speaker='Abu Musa addresses his unnamed son with the actual conditional recollection of rain and sheep-like smell. The compiler’s clothing explanation is not supplied as another narration.'
row(k,field(k,'hi','companion_conditional_historical_recollection',speaker,end='इमाम तिर्मिज़ी कहते हैं:',cuts=[('(sheep)','English lexical translation of the already printed sheep word.')]),field(k,'ur','companion_conditional_historical_recollection',speaker,end='امام ترمذی کہتے ہیں:'))
k='tirmidhi:2480';fs={}
for lang,q,a in [('hi','मैंने कहा:','उन्होंने कहा:'),('ur','میں نے کہا:','انہوں نے کہا:')]:
    ps=[part(k,lang,'ibrahim-general-judgment','transmitted_scholarly_saying','Abu Hamzah reports Ibrahim al-Nakha’i’s substantive building judgment; this is not Prophetic speech.',None,q),part(k,lang,'abuhamzah-necessity-question','transmitted_scholarly_dialogue_question','Abu Hamzah asks about an unavoidable building, retaining the supplied necessity condition.',q,a),part(k,lang,'ibrahim-specific-reply','transmitted_scholarly_reply','Ibrahim supplies the printed no-reward/no-sin reply to that necessity question.',a,None)]
    fs[lang]=field(k,lang,'substantive_transmitted_scholarly_dialogue','The independently supplied Abu Hamzah/Ibrahim dialogue is an actual attributed judgment, question and reply; no Prophetic attribution or modern legal application is inferred.',parts=ps)
row(k,fs['hi'],fs['ur'])
k='tirmidhi:2485';fs={}
for lang,transition,end in [('hi','और सब से पहली बात',None),('ur','اور سب سے پہلی بات','۱؎')]:
    ps=[part(k,lang,'arrival-and-personal-recognition','companion_event_and_personal_recognition_testimony','Abdullah ibn Salam reports the arrival, repeated crowd announcements and his event-specific personal assessment after looking at the Messenger’s face.',None,transition),part(k,lang,'first-prophetic-address','prophetic_saying_in_companion_arrival_report','The source explicitly introduces the Messenger’s first address about greeting, food and night prayer. Its while-others-sleep qualification remains.',transition,end)]
    fs[lang]=field(k,lang,'companion_arrival_testimony_with_prophetic_address','Abdullah’s actual event/personal observation stays distinct from the explicitly introduced Prophetic speech, within one continuous source report family.',parts=ps)
row(k,fs['hi'],fs['ur'])
k='tirmidhi:2502';speaker='Aisha transmits her own imitation and Safiyyah remark, the actual hand gesture with its supplied meaning qualification, and the Messenger’s two replies. The unnamed imitated person remains unnamed.'
row(k,field(k,'hi','companion_report_with_prophetic_replies_and_gesture',speaker,cuts=[('(दूसरी बीवी)','Appended biographical relationship label after the named Safiyyah; it is retained as context without inferring a marriage-order fact. The separate finite hand-gesture parenthesis remains selected.')]),field(k,'ur','companion_report_with_prophetic_replies_and_gesture',speaker,end='۱؎'))
k='tirmidhi:2516';speaker='Ibn Abbas reports the ride and the Messenger’s supplied counsel. All exclusive requests, collective benefit/harm counterfactuals and the source-qualified destiny-scrolls conclusion remain exact.'
row(k,field(k,'hi','companion_report_of_prophetic_counsel',speaker,end='इमाम तिरमिज़ी कहते हैं:'),field(k,'ur','companion_report_of_prophetic_counsel',speaker,end='۱؎'))
k='bukhari:2535';speaker='Abdullah ibn Umar through the complete own source route reports the Messenger’s prohibition of both sale and gift of wala, without an added legal paraphrase.'
row(k,field(k,'hi','prophetic_prohibition_in_companion_transmission',speaker),field(k,'ur','prophetic_prohibition_in_companion_transmission',speaker))
k='bukhari:2536';fs={}
for lang,choice,refusal,ending in [('hi','फिर नबी करीम','बारीरा ने कहा','चुनांचा'),('ur','پھر نبی کریم','بریرہ نے کہا','چنانچہ')]:
    qualifier=('The Hindi female reporter’s name and route are damaged; neither Aisha’s clean name nor the missing wala-link is borrowed from Urdu.' if lang=='hi' else 'The Urdu route explicitly identifies Aisha and supplies the complete wala statement.')
    ps=[part(k,lang,'purchase-and-emancipation','qualified_companion_purchase_report_with_prophetic_reply',qualifier+' The actual purchase, retained-wala contract condition and emancipation reply remain supplied.',None,choice),part(k,lang,'marital-choice-scene','companion_report_of_prophetic_marital_choice_action','The narrative expressly supplies the Messenger summoning Barira and granting the choice concerning her husband.',choice,refusal),part(k,lang,'barira-conditional-refusal','companion_personal_conditional_statement','Barira supplies the actual conditional refusal despite unspecified gifts; these are her own words, not the Messenger’s.',refusal,ending),part(k,lang,'narrated-final-separation','companion_narrative_resolution','The reporting voice returns to the source’s final separation event.',ending,None)]
    fs[lang]=field(k,lang,'continuous_companion_report_with_prophetic_and_barira_voices',qualifier+' Four ordered attribution components preserve this continuous source account in one family; no canonical split or absent words are inferred.',parts=ps)
row(k,fs['hi'],fs['ur'])
k='ibnmajah:2499';speaker='Jabir transmits the supplied undivided-property statement and its boundaries/separate-path limiting condition under the Messenger’s attribution, without modern legal application.'
row(k,field(k,'hi','companion_report_of_prophetic_conditional_ruling',speaker),field(k,'ur','companion_report_of_prophetic_conditional_ruling',speaker,end='۱؎'))
k='ibnmajah:2513'
row(k,field(k,'hi','qualified_companion_report_of_prophetic_sale','Jabir’s shorter Hindi supplies the unnamed owner, mudabbar status, lack of other property, sale and defective purchaser-name fragment. Urdu’s tribe and fuller name are not inserted.'),field(k,'ur','companion_report_of_prophetic_sale','Jabir supplies the unnamed owner, mudabbar status, lack of other property, sale and the source-named Banu Adi purchaser. Its spelling is kept exact.'))
k='ibnmajah:2523';speaker='Abu Dharr asks the emancipation question, and the Messenger’s supplied reply retains both owner-preference and highest-price criteria without an inferred particular person.'
row(k,field(k,'hi','companion_question_and_prophetic_comparative_reply',speaker),field(k,'ur','companion_question_and_prophetic_comparative_reply',speaker,end='۱؎'))
