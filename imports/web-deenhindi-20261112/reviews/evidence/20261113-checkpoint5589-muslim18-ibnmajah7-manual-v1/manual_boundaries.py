"""Individually authored boundaries for the frozen53 complete source readings."""
from manual_source_first_readings import NOTES
READINGS = {}


def field(collection, number, language, report_type=None, speaker=None, cuts=(),
          segments=None, exact=None, context_all=False, retained=()):
    key=collection+':'+number
    assert ('deenhindi-'+key,language) in NOTES
    assert language not in READINGS.setdefault(key,{})
    READINGS[key][language]={'note':NOTES['deenhindi-'+key,language],
        'type':report_type,'speaker':speaker,'context':list(cuts),'context_all':context_all,
        'source_report_family_id':key+':source-numbered-report',
        'retained_meaningful_structures':list(retained)}
    if segments is not None:READINGS[key][language]['segments']=segments
    if exact is not None:READINGS[key][language]['exact_selections']=exact


def part(start=None,end=None,component='report-1',report_type=None,speaker=None):
    item={'start':start,'end':end,'id':component}
    if report_type:item['type']=report_type
    if speaker:item['speaker']=speaker
    return item


field('ibnmajah','2310','hi','companion_testimony_with_prophetic_prayer',
      'Ali reports the Yemen appointment, his own youth/inexperience, and the Messenger’s action and prayer; the final lack-of-doubt experience is Ali’s own testimony.',
      segments=[part(end='फिर इसके बाद मुझे',component='appointment-and-prayer'),
                part(start='फिर इसके बाद मुझे',component='ali-later-testimony',report_type='companion_personal_testimony',
                     speaker='Ali personally reports his later experience in deciding between two people; these are not words spoken by the Prophet.')],
      retained=['(क़ाज़ी बना कर)','(जवान)'])
field('ibnmajah','2310','ur','companion_testimony_with_prophetic_prayer',
      'Ali’s actual appointment account includes his question and the Messenger’s action/invocation, followed by Ali’s own subsequent experience.',
      cuts=['۱؎'],segments=[part(end='پھر اس کے بعد مجھے',component='appointment-and-prayer'),
                part(start='پھر اس کے بعد مجھے',component='ali-later-testimony',report_type='companion_personal_testimony',
                     speaker='Ali supplies the later first-person no-doubt testimony; it is not additional Prophetic speech.')],
      retained=['( قاضی بنا کر )','( جوان )'])
field('ibnmajah','2329','hi','prophetic_judgment_report',
      'Abu Hurayrah reports the two anonymous men’s animal dispute, lack of witnesses and the Prophet’s actual lot/oath instruction.')
field('ibnmajah','2329','ur','prophetic_judgment_report',
      'Abu Hurayrah’s supplied case reports the Prophet’s lot/oath instruction under the explicit no-witnesses condition.',cuts=['۱؎'])
field('ibnmajah','2332','hi','prophetic_judgment_report',
      'Ibn Muhayyisah al-Ansari reports Bara’s camel damage and the Messenger’s actual day/night allocation; both time-dependent scopes remain exact.')
field('ibnmajah','2332','ur','prophetic_judgment_report',
      'The source-named Ibn Muhayyisah reports the camel/garden case and the Messenger’s day/night ruling, preserving the printed grammar and conditions.',cuts=['۱؎'])
field('ibnmajah','2345','hi','prophetic_judgment_and_selection_report',
      'Imran ibn Husayn reports the dying owner’s only property, the release of six slaves and the Messenger’s actual division and selection, with four remaining in the source account.',
      retained=['(दो दो के तीन हिस्से)','(क़ुरआ-अंदाज़ी कर के)','(जिन के नाम क़ुरा निकला)'])
field('ibnmajah','2345','ur','prophetic_judgment_and_selection_report',
      'Imran ibn Husayn reports the source’s six-slave case, actual grouping and lot-selection procedure, with the specified two/four outcome.',
      cuts=['۱؎'],retained=['( دو دو کے تین حصے )','( اور قرعہ اندازی کر کے )','( جن کے نام قرعہ نکلا )'])
field('ibnmajah','2346','hi','qualified_honorific_pronoun_judgment_report',
      'Abu Hurayrah reports a sale dispute and an instruction attributed to आप with the printed Prophetic honorific. This own field does not separately name that figure; the no-testimony and like-or-dislike conditions are preserved.',
      cuts=['(सौदे)'])
field('ibnmajah','2346','ur','qualified_honorific_pronoun_judgment_report',
      'Abu Hurayrah’s own report attributes the instruction to آپ with the printed honorific; no additional named introduction is supplied. The actual dispute, missing witnesses and conditional acceptance wording remain.')
field('ibnmajah','2349','hi','companion_testimony_with_nested_prophetic_retelling',
      'Aisha reports the Messenger’s happy arrival and his retelling of Mujazziz’s observation; the final resemblance claim is Mujazziz’s reported speech.',
      segments=[part(end='तोह कहा: ये पाँव',component='aisha-and-prophetic-retelling'),
                part(start='तोह कहा: ये पाँव',component='mujazziz-observation',report_type='reported_named_observer_saying',
                     speaker='Mujazziz is the observer/speaker of the feet-resemblance statement within the Messenger’s retelling, not the Prophet making an independent observation.')])
field('ibnmajah','2349','ur','companion_testimony_with_nested_prophetic_retelling',
      'Aisha supplies the Messenger’s actual retelling; the final feet observation is distinctly attributed to Mujazziz within that account.',
      cuts=['۱؎'],segments=[part(end='تو کہا: یہ پاؤں',component='aisha-and-prophetic-retelling'),
                part(start='تو کہا: یہ پاؤں',component='mujazziz-observation',report_type='reported_named_observer_saying',
                     speaker='The source attributes the feet-resemblance utterance to Mujazziz inside the Messenger’s retelling; no independent Prophetic observation is asserted.')])
field('ibnmajah','2352','hi','source_qualified_family_dispute_and_prophetic_prayer',
      'The source names Rafi ibn Sinan and parenthetically identifies the choice recipient as Rafi. Preserve that printed family/actor relationship, the actual choice, prayer and placement without external correction of the child or parent identities.',
      cuts=['(मुसलमान)'],retained=['(राफ़े)','(के जिसके साथ जाना चाहें जा सकते हैं)'])
field('ibnmajah','2352','ur','source_qualified_family_dispute_and_prophetic_prayer',
      'The own Urdu source explicitly uses Rafi’s name for the choice recipient in its unusual family framing. Preserve that source interpretation and the Messenger’s prayer/placement without repairing identities from elsewhere.',
      cuts=['( مسلمان )'],retained=['( رافع )','( کہ جس کے ساتھ جانا چاہیں جا سکتے ہیں )'])

field('muslim','2313','hi','companion_testimony_with_prophetic_sale_and_instruction',
      'Jabir reports the after-death emancipation, no-other-property inquiry, sale and the Messenger’s conditional spending instruction; the closing gesture description is the source reporter’s frame.',
      cuts=['(ग़ुलाम)','(800)'],
      segments=[part(end='(रावी ने कहा:)',component='sale-and-spending-instruction'),
                part(start='(रावी ने कहा:)',component='reporter-gesture-description',report_type='source_reporter_description_of_prophetic_gesture',
                     speaker='The source explicitly labels this as the reporter’s description of the Messenger’s directional gesture; the reporter is not uniquely named in this closing frame.')],
      retained=['(के मेरे मरने के बाद वो आज़ाद होगा)','(रावी ने कहा:)'])
field('muslim','2313','ur','companion_testimony_with_prophetic_sale_and_instruction',
      'Jabir’s source account supplies the death condition, sale and spending sequence. The closing generic reporter describes the Messenger’s actual directional gesture.',
      cuts=['( غلام )','( 800 )'],
      segments=[part(end='( راوی نے کہا : )',component='sale-and-spending-instruction'),
                part(start='( راوی نے کہا : )',component='reporter-gesture-description',report_type='source_reporter_description_of_prophetic_gesture',
                     speaker='The source’s generic reporter introduces the gesture description; its final parenthetic spend imperative is the actual predicate completion, not an added outside instruction.')],
      retained=['( کہ میرے مرنے کے بعد وہ آزاد ہو گا )','( راوی نے کہا : )','( خرچ کرو ۔)'])
field('muslim','2320','hi','companion_question_and_prophetic_answer',
      'Umm Salamah expressly asks about spending on Abu Salamah’s children, states her own relationship/resolve and receives the Messenger’s actual affirmative answer.')
field('muslim','2320','ur','companion_question_and_prophetic_answer',
      'Umm Salamah’s own question and personal statements are distinct from the Messenger’s affirmative answer; all source grammar and the unclosed quotation remain exact.')
field('muslim','2324','hi','companion_question_and_prophetic_answer',
      'Asma’s source question includes the mother’s wish-or-fear alternative and the Messenger’s yes. Preserve the actual predicate objects and unresolved alternative without importing another version.',
      retained=['(सिला रहमी की)','(ख़ाली हाथ वापसी से)'])
field('muslim','2324','ur','companion_question_and_prophetic_answer',
      'Asma reports the actual mother/kinship question and affirmative answer. The source’s wish-or-fear alternative and both substantive predicate objects remain unresolved and exact.',
      retained=['( صلہ رحمی کی )','( خالی ہاتھ واپسی سے )'])
field('muslim','2325','hi','companion_historical_question_and_prophetic_answer',
      'Asma bint Abi Bakr supplies the treaty setting, her mother’s printed state and hope, and the Messenger’s actual kinship instruction; the hope’s object is retained as source scope.',
      retained=['(मुझ से सिला रहमी की)'])
field('muslim','2325','ur','companion_historical_question_and_prophetic_answer',
      'Asma’s full treaty-time account and actual question/reply are source supplied. The from-me kinship qualification specifies the mother’s hope rather than an inferred external motive.',
      retained=['( مجھ سے صلہ رحمی کی )'])
field('muslim','2327','hi','qualified_transmitted_negative_report_fragment',
      'The actual did-not-make-a-will clause is explicitly supplied in Abu Usamah’s variant. The woman’s identity and the ultimate reporting voice are absent and remain unknown; the chain and omitted-word comparisons are context.',
      exact=[{'text':"'वलम तूसी' (उसने वसीयत नहीं की)",'id':'negative-will-fragment'}],
      retained=['(उसने वसीयत नहीं की)'])
field('muslim','2327','ur','qualified_transmitted_negative_report_fragment',
      'The source transmits this finite negative-will clause and its own rendering, while leaving the woman and ultimate voice unidentified. No absent report or Prophetic speaker is inferred.',
      exact=[{'text':'ولم توص ( اس نے وصیت نہیں کی )','id':'negative-will-fragment'}],
      retained=['( اس نے وصیت نہیں کی )'])
field('muslim','2331','hi','qualified_transmitted_variant_fragments',
      'Two actual source variants are supplied, but their actor, complete condition and ultimate speaker are absent. Preserve the printed transliteration/rendering without repairing the damaged opening or importing another language.',
      cuts=['(और की बजाये)'],
      segments=[part(start="'अवमुरु बिल-माँ'रूफ",end=' और कहा:',component='command-good-fragment'),
                part(start="फ इन्नहु यूमसी यौमा'इज़िन",component='reaches-evening-fragment')])
field('muslim','2331','ur','qualified_transmitted_variant_fragments',
      'The actual or-commanded-good and reaches-evening clauses are source variants with unresolved actor/condition and ultimate voice. Their supplied renderings remain exact; word-substitution apparatus stays context.',
      cuts=['( اور کی بجائے )'],
      segments=[part(start='" اوامربالمعروف',end=' اور کہا :',component='command-good-fragment'),
                part(start='فانه يمسي يومئذ',component='reaches-evening-fragment')])
field('muslim','2344','hi','qualified_transmitted_placement_variants',
      'The field supplies actual placement-of-charity variants and their own renderings. Its ultimate speaker and pronoun referents are not specified; the first variant’s route is not uniquely labelled Ruh in this Hindi wording.',
      segments=[part(start="मं आल-कस्ब अल-तैय्यब फायदा'उहा",end=' और सुलैमान की हदीस में है:',component='first-placement-fragment'),
                part(start="फायदा'उहा फि मवड़ी'यह",component='sulayman-placement-fragment',
                     speaker='The second source variant is expressly labelled Sulayman’s. Its ultimate report speaker remains unnamed; no missing full charity report is supplied.')],
      retained=['(हलाल कमाई से सदक़ा करता है फिर उसको वहाँ लगता है जहाँ इसका हक़ है)','(और उसे इसकी जगह पर खर्च करता है)'])
field('muslim','2344','ur','qualified_transmitted_placement_variants',
      'The source expressly labels Ruh’s and Sulayman’s actual placement variants. Preserve their Arabic wording and own Urdu renderings, with ultimate speaker and pronoun referents unresolved.',
      segments=[part(start='من الكسب الطيب فيضعها في حقها',end=' اور سلیمان کی حدیث میں ہے',component='ruh-placement-fragment',
                     speaker='This wording is expressly assigned to Ruh’s transmitted variant, without naming its ultimate speaker.'),
                part(start='فيضعها في موضعها',component='sulayman-placement-fragment',
                     speaker='This wording is expressly assigned to Sulayman’s transmitted variant; no ultimate voice or omitted full report is inferred.')],
      retained=['( حلال کمائی سے صدقہ کرتا ہے پھر اس کو وہاں لگا تا ہے جہاں اس کا حق ہے )','( اور اسے اس کی جگہ پر خرچ کرتا ہے)'])
field('muslim','2349','hi','prophetic_gesture_and_charity_instruction_report',
      'Adi ibn Hatim reports the Messenger’s actual turning/gesture and fire-avoidance instruction with the half-date/good-word fallback. The final Abu Kurayb omission/chain appendix remains visible source context.',
      cuts=['(आग)'],segments=[part(end='अबू कुराइब ने का-अन्नमा',component='gesture-and-instruction')])
field('muslim','2349','ur','prophetic_gesture_and_charity_instruction_report',
      'Adi ibn Hatim reports the actual Messenger gestures/instruction. The own Urdu defects and fallback qualification remain; the complete trailing word-omission/chain discussion stays context.',
      cuts=['( آگ )'],segments=[part(end='ابو کریب نےكانما',component='gesture-and-instruction')],retained=['( یہ بھی )'])
field('muslim','2352','hi','qualified_abbreviated_historical_and_prophetic_action_report',
      'Through Mundhir ibn Jarir’s father, the field supplies the early-day attendance scene and a separate finite prayer/sermon addition. No omitted whole story is reconstructed.',
      segments=[part(end='(आगे इब्न जाफ़र',component='early-day-attendance',
                     speaker='The source’s father-through-Mundhir chain supplies the actual early-day attendance with the named Messenger.'),
                part(start='फिर आप ने ज़ोहर की नमाज़ अदा फ़रमाई',end=')।',component='prayer-and-sermon-addition',report_type='transmitted_prophetic_action_variant',
                     speaker='The source expressly supplies an Ibn Muadh-route addition: the already named figure prays Zuhr and delivers a sermon. The pointed-to intervening story remains absent.')])
field('muslim','2352','ur','qualified_abbreviated_historical_and_prophetic_action_report',
      'The source’s Mundhir/father route supplies actual early-day presence and a finite prayer/sermon addition within comparison framing; no full missing story is supplied.',
      segments=[part(end='( آگے ابن جعفر',component='early-day-attendance',
                     speaker='The father-through-Mundhir source chain reports actual early-day presence with the named Messenger.'),
                part(start='پھر آپ نے ظہر کی نماز ادا فرمائی',end=416,component='prayer-and-sermon-addition',report_type='transmitted_prophetic_action_variant',
                     speaker='The Ibn Muadh-route addition actually supplies the prayer and sermon actions concerning the previously named Messenger; its omitted story is not reconstructed.')],
      retained=['( حا ضر )'])
field('muslim','2353','hi','qualified_abbreviated_historical_and_prophetic_sermon_report',
      'The source’s Mundhir/father report supplies a wool-clad group’s arrival and a separate prayer/pulpit/sermon passage with short actual Quran words. No unseen continuation is filled.',
      segments=[part(end='और पूरा वाक़ेआ बयान किया',component='arrival-fragment'),
                part(start='आप ने ज़ोहर की नमाज़ पढ़ायी',end='आयत के आख़िर तक।',component='sermon-and-quoted-verse',report_type='prophetic_sermon_fragment_with_reported_quran',
                     speaker='The source reports the Prophet’s prayer/pulpit actions and his statement introducing the supplied fear-your-Lord Quran words. The unprinted rest of the verse remains absent.')])
field('muslim','2353','ur','qualified_abbreviated_historical_and_prophetic_sermon_report',
      'The actual arrival and prayer/sermon portions are transmitted through Mundhir’s father. Their source relationship and quoted Quran words remain exact, with the missing full account/verse explicit.',
      segments=[part(end='اور پورا واقعہ بیان کیا',component='arrival-fragment'),
                part(start='آپ نے ظہر کی نماز پڑھائی',end='آیت کے آخر تک',component='sermon-and-quoted-verse',report_type='prophetic_sermon_fragment_with_reported_quran',
                     speaker='The source expressly reports the Prophet’s supplied sermon introduction and short Quran quote; no words beyond that quote are supplied by the reviewer.')])
field('muslim','2354','hi','companion_historical_scene_fragment',
      'Jarir ibn Abdullah reports the actual Bedouins’ arrival, clothing and visible hunger before the Messenger. The remaining event is only pointed to and is not reconstructed.',
      segments=[part(end='फिर उन (साबिक़ा रावीयन-ए-हदीस)',component='arrival-and-hunger-scene')])
field('muslim','2354','ur','companion_historical_scene_fragment',
      'Jarir ibn Abdullah supplies the actual arrival/poor-condition scene. Preserve all own source words and ellipsis; the closing prior-report comparison is context.',
      segments=[part(end='پھر ان ( سابقہ راویان حدیث )',component='arrival-and-hunger-scene')])
field('muslim','2355','hi','companion_testimony_with_reported_dialogue_and_quran',
      'Abu Masud reports an unnamed charity command, labor and donations, followed by the hypocrites’ actual remarks and the reported revelation wording. The command’s issuer is not supplied in this field.',
      cuts=['(लफ़्ज़ बिश्र के हैं)','(घुन्दर)'],
      segments=[part(end='तो मुनाफ़िक़ों ने कहा:',component='labor-and-donations',report_type='companion_collective_testimony',
                     speaker='Abu Masud supplies the collective testimony and donors’ actions. The passive charity command has no locally named issuer.'),
                part(start='तो मुनाफ़िक़ों ने कहा:',end='इस पर यह आयत-ए-मुबारक उतरी:',component='reported-hypocrites-remarks',report_type='reported_unnamed_group_saying',
                     speaker='The source explicitly attributes these disparaging remarks to unnamed hypocrites; they are not Prophetic words or reviewer endorsement.'),
                part(start='इस पर यह आयत-ए-मुबारक उतरी:',end='बिश्र ने अल-मुतव्वी’ईन',component='reported-revelation',report_type='reported_quran_revelation_with_source_rendering',
                     speaker='Abu Masud’s testimony reports the revelation and supplies the source’s actual verse rendering; the wage qualification remains within that rendering.')],
      retained=['(की उजरत)'])
field('muslim','2355','ur','companion_testimony_with_reported_dialogue_and_quran',
      'Abu Masud’s own testimony describes the charity command without naming its issuer, the labor/donations, hostile remarks and supplied revelation rendering.',
      cuts=['۔ لفظ بشر کے ہیں ۔','( غندر )'],
      segments=[part(end='تو منافقوں نے کہا :',component='labor-and-donations',report_type='companion_collective_testimony',
                     speaker='Abu Masud gives the actual collective testimony and donor actions; the command’s issuer remains unspecified.'),
                part(start='تو منافقوں نے کہا :',end='اس پر یہ آیت مبارک اتری :',component='reported-hypocrites-remarks',report_type='reported_unnamed_group_saying',
                     speaker='The quoted disparaging remarks belong to the unnamed hypocrites in the source narrative, not the Prophet.'),
                part(start='اس پر یہ آیت مبارک اتری :',end='بشر نے المطوعين',component='reported-revelation',report_type='reported_quran_revelation_with_source_rendering',
                     speaker='The source testimony reports the revealed wording and gives this actual rendering, including the wage qualification; no outside verse text is inserted.')],
      retained=['( کی اجرت )'])
field('muslim','2356','hi','qualified_transmitted_collective_testimony_fragment',
      'The source labels a Said ibn Rabi variant containing an actual we-carried-burdens clause. Its ultimate we-group is unspecified in this own field, and no identity is borrowed from2355.',
      exact=[{'text':'हम अपनी पुश्तों पर बोझ उठाते थे।','id':'backs-and-burdens-fragment'}])
field('muslim','2356','ur','qualified_transmitted_collective_testimony_fragment',
      'The actual backs/burdens clause is expressly supplied in Said ibn Rabi’s variant. The ultimate participants remain unidentified; the source chain/comparison is retained as context.',
      exact=[{'text':'ہم اپنی پشتوں پر بوجھ اٹھاتے تھے ۔','id':'backs-and-burdens-fragment'}])
field('muslim','2357','hi','source_raised_attribution_report_via_companion',
      'Abu Hurayrah’s source explicitly raises the report to the honorific-pronoun target in its printed parenthesis. Preserve that qualified source attribution and the actual milk-gift/reward statement without external canonical identification.',
      cuts=['(ऐसी दूध देने वाली)','(ऊँटनी)'],retained=['(आप सल्लल्लाहु अलैहि वसल्लम तक)'])
field('muslim','2357','ur','source_raised_attribution_report_via_companion',
      'The source expressly raises Abu Hurayrah’s report to the printed honorific-pronoun target. That actual attribution frame and all morning/evening milk conditions remain; no outside canonical identity is asserted.',
      cuts=['( ایسی دودھ دینے والی )','( اونٹنی )'],retained=['( آپ صلی اللہ علیہ وسلم تک )'])
for language in ('ar','hi','ur','ur-Latn','en'):
    field('muslim','2365',language,context_all=True)
field('muslim','2369','hi','companion_personal_testimony_with_prophetic_dialogue',
      'Umayr reports his master’s order, feeding the poor man, beating and the ensuing Messenger/master dialogue. The shared-reward answer is actual Prophetic speech, while the appended equivalent explanation remains context.',
      segments=[part(end='(तुम दोनों को मिलेगा)',component='feeding-and-reward-dialogue')],retained=['(दूसरों को)'])
field('muslim','2369','ur','companion_personal_testimony_with_prophetic_dialogue',
      'Umayr’s source testimony supplies the acts and the Messenger’s inquiry and reward answer, with the master’s complaint separately voiced. Preserve all grammar and recipient scope; the final restatement is context.',
      segments=[part(end='( تم دونوں کو ملے گا)',component='feeding-and-reward-dialogue')],retained=['( دوسروں کو )'])
field('muslim','2382','hi','prophetic_conditional_instruction_in_dialogue',
      'Abu Hurayrah reports an unnamed visitor’s reward question and the Messenger’s conditional answer. The time, life and heir qualifications restrict actual source scope and remain; no generic unconditional ruling is substituted.',
      retained=['(अजर में)','(उस वक़्त)','(तुम्हारी जान)','(फिर)','(वारिस)'])
field('muslim','2382','ur','prophetic_conditional_instruction_in_dialogue',
      'Abu Hurayrah supplies the visitor’s actual question and the Messenger’s timing/health/wealth/deathbed answer. Preserve the source’s reward dimension, temporal predicates, life subject and heir role.',
      retained=['( اجر میں )','( اس وقت )','( تمھا ری جا ن )','( پھر )','( وارث )'])
field('muslim','2384','hi','qualified_transmitted_question_fragment',
      'The source actually quotes the best-charity question but does not name its questioner or supply its answer in this field. Keep only the supplied interrogative wording without importing2382.',
      exact=[{'text':'कौन सा सदक़ा अफ़ज़ल है?','id':'best-charity-question'}])
field('muslim','2384','ur','qualified_transmitted_question_fragment',
      'The transmitted best-charity question is actual speech wording. Its questioner and missing answer remain unknown locally; the same-chain comparison does not fill them.',
      exact=[{'text':'کون سا صدقہ افضل ہے ؟','id':'best-charity-question'}])

assert len(READINGS)==25 and sum(len(x) for x in READINGS.values())==53
assert set(NOTES)=={('deenhindi-'+key,language) for key,value in READINGS.items() for language in value}
