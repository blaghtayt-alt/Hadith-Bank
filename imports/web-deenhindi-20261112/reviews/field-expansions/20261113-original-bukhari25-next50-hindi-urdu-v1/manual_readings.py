"""Exact own-field boundaries authored only after the frozen50-field reading."""
READINGS={}
def pair(n,kind,speaker,hi=None,ur=None,speaker_ur=None):
 for lang,start,voice in [('hi',hi,speaker),('ur',ur,speaker_ur or speaker)]:
  assert (n,lang) not in READINGS
  READINGS[n,lang]={'type':kind,'speaker':voice,'context':[],'segments':[{'start':start,'end':None}],'annotations':[]}
def split(n,lang,parts):READINGS[n,lang]['segments']=parts

pair('1487','prophetic_prohibition_report','Jabir transmits the actual prohibition and ripeness condition; the preceding route is retained in source context',
 'रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने फल','رسول اللہ صلی اللہ علیہ وسلم نے پھل')
pair('1489','companion_report_and_later_companion_practice','Ibn Umar reports Umar’s horse incident; the later Ibn Umar practice is separately attributed',
 'अब्दुल्लाह बिन उमर (रज़ि अल्लाहु अन्हुमा) बयान करते थे','عبداللہ بن عمر رضی اللہ عنہما بیان کرتے تھے')
for lang,mark,end in [('hi','इसी वजह से अगर इब्न उमर',' (अपने इस्तेमाल'),('ur','اسی وجہ سے اگر ابن عمر',' ( اپنے استعمال')]:
 start=READINGS['1489',lang]['segments'][0]['start']
 split('1489',lang,[{'start':start,'end':mark,'type':'companion_horse_incident_with_prophetic_reply'},
  {'start':mark,'end':end,'type':'reported_later_companion_charity_practice','speaker':'The source reports Ibn Umar’s later conditional practice of giving again charity he had purchased; this is not a new Prophetic instruction'}])

pair('1493','two_ordered_companion_encounters','Aisha reports the Barira purchase/emancipation and the separately introduced meat encounter; the prefatory chain remains context',
 'उनका इरादा हुआ','ان کا ارادہ ہوا')
for lang,mark in [('hi','उन्होंने कहा के नबी करीम'),('ur','انہوں نے کہا کہ نبی کریم')]:
 start=READINGS['1493',lang]['segments'][0]['start']
 split('1493',lang,[{'start':start,'end':mark,'type':'companion_purchase_and_emancipation_report_with_prophetic_reply'},
  {'start':mark,'end':None,'type':'companion_meat_encounter_with_prophetic_reply','speaker':'Aisha separately introduces the actual meat, charity and gift exchange'}])
 READINGS['1493',lang]['annotations']=['The parenthetic enslaved status belongs to the person in the actual purchase/emancipation transaction and remains source-qualified material status.']

pair('1500','companion_report_of_prophetic_appointment_and_accounting','Abu Humayd transmits the named collector appointment and subsequent accounting; names and groups retain their own source spellings',
 'रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने बनी असद','رسول اللہ صلی اللہ علیہ وسلم نے بنی اسد')
pair('1501','companion_historical_incident_with_prophetic_actions','Anas transmits the actual Urayna incident; source-preserved historical treatment and punishment wording is not current advice',
 'उरैनाह के कुछ लोगों','عرینہ کے کچھ لوگوں')
for lang,end,aside in [
 ('hi','इस रिवायत की मुताबाअत','(क्योंकि वह ऐसे मर्ज़ में मुब्तला थे जिसकी दवा यही थी)'),
 ('ur','اس روایت کی متابعت','( کیونکہ وہ ایسے مرض میں مبتلا تھے جس کی دوا یہی تھی )')]:
 READINGS['1501',lang]['segments'][0]['end']=end
 READINGS['1501',lang]['context']=[aside]
 READINGS['1501',lang]['annotations']=['The medical-cure explanation is preserved as source context. The supplied illness, actual permission, those-camels relation, heat-intensity link and every historical action remain exact; no modern treatment claim is made.']

pair('1502','companion_purpose_and_actual_observation_report','Anas reports bringing Abdullah ibn Abi Talha for tahnik and actually observing zakat-camel branding; performance of the intended tahnik is not invented',
 'मैं अब्दुल्लाह बिन अबी तल्हा को लेकर','میں عبداللہ بن ابی طلحہ کو لے کر')
READINGS['1502','hi']['context']=['(यानी अपने मुँह से कोई चीज़ चबा कर इनके मुँह में डाल दें)']
READINGS['1502','ur']['context']=['( یعنی اپنے منہ سے کوئی چیز چبا کر ان کے منہ میں ڈال دیں )']
pair('1503','prophetic_payment_instruction_with_scope_and_deadline','Ibn Umar transmits the complete own fitr instruction, quantity, alternatives, all supplied Muslim categories and Eid-prayer deadline',
 'रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने फ़ित्र की ज़कात','رسول اللہ صلی اللہ علیہ وسلم نے فطر کی زکوٰۃ')
READINGS['1503','hi']['context']=['(सदक़ा-ए-फ़ित्र)']
READINGS['1503','ur']['context']=['( صدقہ فطر )']
for lang in ['hi','ur']:READINGS['1503',lang]['annotations']=['The sadaqa-fitr parenthesis repeats the already explicit fitr-zakat category and stays lexical context. The separate Eid parenthesis materially identifies the deadline’s prayer and remains.']
pair('1505','companion_collective_charity_practice','Abu Said supplies the actual collective one-sa barley practice; no unprinted fitr or timing label is added',
 "हम एक सा' 'जौ'","ہم ایک صاع ”جَو“")
pair('1506','companion_collective_fitr_practice','Abu Said supplies the actual full list of one-sa alternatives; the final reporting predicate is retained after the prefatory chain',
 'आप फ़रमाते थे कि','آپ فرماتے تھے کہ')
READINGS['1506','hi']['context']=['(खुश्क अंगूर या अंजी़र)']
READINGS['1506','ur']['context']=['( خشک انگور یا انجیر )']
for lang in ['hi','ur']:READINGS['1506',lang]['annotations']=['The parenthetic dried-grapes-or-figs wording is a source lexical explanation of zabib and remains unchanged context. Every actual preceding list alternative, including grain-or-wheat, stays selected without correction.']
pair('1507','prophetic_instruction_and_later_community_determination','Ibn Umar transmits the instruction and separately reports the later people’s equivalence determination',
 "रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने एक सा'अ खजूर",'رسول اللہ صلی اللہ علیہ وسلم نے ایک صاع کھجور')
for lang,mark in [('hi','अब्दुल्लाह बिन उमर (रज़ियल्लाहु अन्हुमा) ने बयान किया कि फिर लोगों'),('ur','عبداللہ بن عمر رضی اللہ عنہما نے بیان کیا کہ پھر لوگوں')]:
 start=READINGS['1507',lang]['segments'][0]['start']
 split('1507',lang,[{'start':start,'end':mark,'type':'prophetic_payment_instruction'},
  {'start':mark,'end':None,'type':'later_community_quantity_determination','speaker':'Ibn Umar explicitly reports the later people’s two-mudd wheat equivalence, not a second Prophetic instruction'}])
 READINGS['1507',lang]['annotations']=['Both the two-mudd amount and its source-rendered half-sa equivalent remain material quantity information.']
pair('1510','companion_collective_practice_and_food_description','Abu Said supplies the Eid practice and the separately introduced description of their food in that period',
 'हम नबी करीम','ہم نبی کریم')
for lang,mark in [('hi','अबू सईद (रज़ियल्लाहु अन्हु) ने बयान किया'),('ur','ابوسعید رضی اللہ عنہ نے بیان کیا')]:
 start=READINGS['1510',lang]['segments'][0]['start']
 split('1510',lang,[{'start':start,'end':mark,'type':'companion_collective_eid_payment_practice'},
  {'start':mark,'end':None,'type':'companion_period_food_description','speaker':'Abu Said expressly introduces the actual food list under its supplied period qualification'}])
 READINGS['1510',lang]['annotations']=['The food-grain object and those-days temporal parentheses materially limit the actual payment and food description and remain exact.']
pair('1511','qualified_instruction_and_later_reported_practices','The source reports the Prophetic instruction, later people’s determination, Ibn Umar practices and earlier community payment separately',
 'नबी करीम (सल्लल्लाहु अलैहि वसल्लम) ने सदक़ा-ए-फ़ित्र','نبی کریم صلی اللہ علیہ وسلم نے صدقہ فطر')
for lang,a,b,c,end in [
 ('hi','फिर लोगों ने आधा','लेकिन इब्न-ए-उमर','और लोग सदक़ा-ए-फ़ित्र एक या दो दिन','इमाम बुख़ारी (रहिमहुल्लाह) ने कहा मेरे बेटों'),
 ('ur','پھر لوگوں نے آدھا','لیکن ابن عمر','اور لوگ صدقہ فطر ایک یا دو دن','امام بخاری رحمہ اللہ نے کہا میرے بیٹوں')]:
 start=READINGS['1511',lang]['segments'][0]['start']
 split('1511',lang,[{'start':start,'end':a,'type':'prophetic_payment_instruction_with_source_wording_uncertainty','speaker':'Ibn Umar’s source report retains its printed fitr-or-Ramadan wording uncertainty and all participant/quantity scope'},
  {'start':a,'end':b,'type':'later_community_quantity_determination','speaker':'The source explicitly attributes the later wheat equivalence to people'},
  {'start':b,'end':c,'type':'transmitted_companion_payment_practices_with_qualified_pronoun','speaker':'The source narrates Ibn Umar’s later practices; its my-sons first-person link is preserved, and the compiler’s Nafi explanation remains separately in context'},
  {'start':c,'end':end,'type':'reported_community_payment_timing','speaker':'The source reports the people’s one-or-two-days-prior practice; the following compiler interpretation is not included as more narration'}])
 READINGS['1511',lang]['annotations']=['The source’s fitr-or-Ramadan wording uncertainty remains explicit. The later my-sons pronoun and every-poor-recipient-who-accepts clause stay as printed; the compiler’s subsequent speaker/collection explanations do not rewrite them. Both explicit Bukhari explanations are retained in source context.']
pair('1512','companion_report_of_prophetic_payment_instruction','Ibn Umar explicitly reports the own barley-or-dates instruction and exactly its supplied participant categories',
 'अब्दुल्लाह बिन उमर (रज़ियल्लाहु अन्हुमा) ने फ़रमाया','عبداللہ بن عمر رضی اللہ عنہما نے فرمایا')
pair('1513','companion_hajj_encounter_with_prophetic_reply','Ibn Abbas transmits the Fadl/woman encounter, the actual on-her-father’s-behalf question and yes reply with the supplied incapacity and event setting',
 'फ़ज़्ल बिन अब्बास (हज्जतुल विदा में)','فضل بن عباس ( حجۃ الوداع میں )')
READINGS['1513','hi']['context']=['(बदल)']
READINGS['1513','ur']['context']=['( بدل )']
for lang in ['hi','ur']:READINGS['1513',lang]['annotations']=['Preserve the source’s wanted-to-turn wording, farewell-pilgrimage time, old-age/camel-incapacity and on-his-behalf relation. The redundant technical badal label is context; no stronger completed-action wording is substituted.']
pair('1515','companion_report_of_prophetic_ihram_event','Jabir transmits the actual Dhul-Hulayfa event and mount-standing circumstance; corroborating routes remain context',
 'रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने ज़ुल-हुलैफ़ा','رسول اللہ صلی اللہ علیہ وسلم نے ذوالحلیفہ')
READINGS['1515','hi']['segments'][0]['end']='इब्राहीम बिन मूसा की यह हदीस'
READINGS['1515','ur']['segments'][0]['end']='ابراہیم بن موسیٰ کی یہ حدیث'
pair('1518','qualified_companion_umrah_encounter','The Hindi female reporter/name and place are source-damaged; retain the actual complaint, sibling instruction, ride and Umrah without Urdu repair',
 'उन्होंने कहा या रसूल अल्लाह!','انھوں نے کہا یا رسول اللہ!',
 speaker_ur='Aisha supplies the actual Umrah complaint, Abdur Rahman sibling instruction, ride and performance, with the place as this Urdu field prints it')
READINGS['1518','hi']['annotations']=['The Hindi source prints ऐसा and तांईं and has an abbreviated route. Neither the names, place spelling nor missing links are repaired from Urdu.']
pair('1520','companion_question_and_prophetic_qualified_reply','Aisha supplies the actual question; the reply’s no and mabrur-Hajj qualification remain exact',
 'उन्होंने पूछा या रसूल अल्लाह!','انہوں نے پوچھا یا رسول اللہ!')
pair('1522','reported_visit_question_and_companion_reply','Zayd ibn Jubayr supplies the actual Ibn Umar visit and question; Ibn Umar reports the three Prophet-assigned places under the source’s own group names',
 'ज़ैद बिन जुबैर ने बयान किया कि वो','زید بن جبیر نے بیان کیا کہ وہ')
for lang in ['hi','ur']:READINGS['1522',lang]['annotations']=['The internal Zayd-said parenthesis returns the actual questioner’s voice after the visit setting and remains narrator framing. The preceding multistep route alone is context.']
pair('1523','companion_historical_report_with_revelation','Ibn Abbas reports the Yemenis’ practice and the explicitly stated revelation event with its own verse rendering; no recitation or external verse mapping is invented',
 'यमन के लोग रास्ते','یمن کے لوگ راستہ')
READINGS['1523','hi']['segments'][0]['end']='इसको इब्न उयैना'
READINGS['1523','ur']['segments'][0]['end']='اس کو ابن عیینہ'
pair('1526','companion_report_of_prophetic_miqat_assignments','Ibn Abbas transmits the four actual assignments, visitor/intention conditions and source-abbreviated inner-region/Mecca continuation',
 'रसूल अल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने मदीना वालों','رسول اللہ صلی اللہ علیہ وسلم نے مدینہ والوں')
for lang in ['hi','ur']:READINGS['1526',lang]['annotations']=['The supplied join after people living inside the miqat is abbreviated before the Mecca case. No missing general-resident clause is filled from memory or another version. All actual place, visitor and intention conditions remain.']
pair('1536','qualified_companion_revelation_encounter_and_later_dialogue','Hindi retains its damaged initial bin-Umayyah actor and later Ya’la name; the actual revelation/Umrah encounter and later Ata exchange have separate voices',
 'बिन उमैय्यह ने उम्र','یعلیٰ بن امیہ نے عمر',
 speaker_ur='Ya’la ibn Umayya supplies the actual request/observation encounter; the later narrator/Ata interpretive exchange remains a separately attributed dialogue')
for lang,mark in [('hi','मैंने अत से पुछा'),('ur','میں نے عطاء سے پوچھا')]:
 start=READINGS['1536',lang]['segments'][0]['start']
 split('1536',lang,[{'start':start,'end':mark,'type':'qualified_revelation_encounter_and_prophetic_instruction'},
  {'start':mark,'end':None,'type':'actual_later_attributed_interpretive_dialogue','speaker':'The source’s first-person questioner, not externally identified, asks the source-named Ata about the three-wash instruction and receives the actual yes answer; this is not additional Prophetic speech'}])
READINGS['1536','hi']['annotations']=['The source’s missing initial personal name and shortened route remain absent; its later Ya’la mention does not repair that earlier join. The last first-person questioner’s name is not inferred from the route.']
for n in ['1537','1538']:
 pair(n,'companion_practice_successor_exchange_and_companion_observation','The source’s short Saeed attribution, Ibn Umar practice, Ibrahim exchange and explicitly relayed Aisha recollection remain separately voiced; no unprinted first-person identity is supplied')
 for lang,a,b in [('hi','मैंने इसका ज़िक्र इब्राहिम से किया','असवद ने आइशा (रदी अल्लाहु अन्हा) से रिवायत की'),('ur','میں نے اس کا ذکر ابراہیم سے کیا','اسود نے عائشہ رضی اللہ عنہا سے روایت کی')]:
  split(n,lang,[{'start':None,'end':a,'type':'transmitted_companion_oil_practice','speaker':'The short Saeed ibn Jubayr attribution transmits Ibn Umar’s actual oiling practice'},
   {'start':a,'end':b,'type':'actual_attributed_successor_exchange','speaker':'The source’s first-person reporter mentions the practice to Ibrahim, who asks the actual question; no missing narrator name is supplied'},
   {'start':b,'end':None,'type':'explicitly_transmitted_companion_physical_observation','speaker':'Aswad explicitly relays Aisha’s actual perfume recollection while the Prophet was in ihram, not direct Prophetic words'}])
  READINGS[n,lang]['annotations']=['This occurrence retains its own identity even where its full wording matches another numbered source occurrence. The short coherent attribution and citation within actual dialogue are retained, without a blanket chain trim.']
pair('1541','companion_report_of_prophetic_ihram_location','The final source reporter’s predicate and Dhul-Hulayfa-mosque proximity statement remain; both prefatory routes are preserved as context',
 'वो कह रहे थे कि','وہ کہہ رہے تھے کہ')
pair('1543','companion_route_report_and_joint_transmitted_observation','Ibn Abbas gives the distinct Usama/Fadl route report and then explicitly attributes the talbiyah observation to both')
for lang,mark in [('hi','इब्न अब्बास ने मज़ीद कहा'),('ur','ابن عباس نے مزید کہا')]:
 split('1543',lang,[{'start':None,'end':mark,'type':'companion_report_of_two_riding_routes'},
  {'start':mark,'end':None,'type':'joint_companion_testimony_as_explicitly_relayed','speaker':'Ibn Abbas expressly relays both riders’ account of talbiyah until the source-named Jamrah-Aqabah stoning; no formula or extra time is inserted'}])
assert len(READINGS)==50
