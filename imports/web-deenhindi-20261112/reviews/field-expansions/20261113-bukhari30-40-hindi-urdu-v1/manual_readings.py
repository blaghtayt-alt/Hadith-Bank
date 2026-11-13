"""Individual complete-source readings and explicit source-bound boundaries by /root."""
READINGS = {
    ('1180','ur'): {
        'type':'prophetic_practice_report',
        'speaker':'Ibn Umar reporting the ten rakahs, then Hafsa as explicitly relayed by Ibn Umar',
        'note':'Read all480 Urdu characters. The ten rakahs, the household locations and the dawn timing are the supplied report. Retain the nafl and fajr parenthetical qualifications. Distinguish the closing Hafsa testimony from Ibn Umar own preceding account while keeping one ordered report family. Do not deduplicate this provider occurrence against1181.',
        'segments':[
            {'start':None,'end':'حضرت حفصہ نے مجھے بتایا','type':'prophetic_practice_report','speaker':'Ibn Umar reporting the supplied prayer routine'},
            {'start':'حضرت حفصہ نے مجھے بتایا','end':None,'type':'prophetic_practice_report','speaker':'Hafsa explicitly relayed by Ibn Umar; dawn-adhan prayer testimony'},
        ],
    },
    ('1181','ur'): {
        'type':'prophetic_practice_report',
        'speaker':'Ibn Umar reporting the ten rakahs, then Hafsa as explicitly relayed by Ibn Umar',
        'note':'Separately read this complete480-character field. Its identical supplied wording remains a distinct source occurrence. Preserve all ten-rakah details, home locations, private dawn interval, nafl/fajr qualifications and the final Hafsa report. The two attributed parts are ordered within one report family.',
        'segments':[
            {'start':None,'end':'حضرت حفصہ نے مجھے بتایا','type':'prophetic_practice_report','speaker':'Ibn Umar reporting the supplied prayer routine'},
            {'start':'حضرت حفصہ نے مجھے بتایا','end':None,'type':'prophetic_practice_report','speaker':'Hafsa explicitly relayed by Ibn Umar; dawn-adhan prayer testimony'},
        ],
    },
    ('1184','ur'): {
        'type':'companion_dialogue_and_prophetic_period_practice',
        'speaker':'Marthad ibn Abdullah questioning Uqba ibn Amir; Uqba gives the reported practice and his own later explanation',
        'note':'Read the complete chain and question-answer report. Marthad mentions Abu Tamim two voluntary rakahs before Maghrib; Uqba reports their practice during the Messenger lifetime and explains his later omission by worldly occupations. Preserve both questions and both answers. Uqba explanation is not turned into Prophetic speech or a Prophetic prohibition.',
    },
    ('1188','ur'): {
        'type':'numbered_historical_report',
        'speaker':'Source narrative voice reporting Abu Said participation; the final sentence ultimate reporting voice is not separately named',
        'note':'Read all308 characters. The opening chain announces four things heard by Abu Said from the Prophet but supplies none of those four bodies, so that transmission announcement remains source context. The final finite sentence actually reports that Abu Said accompanied the Prophet in twelve campaigns; retain that numbered historical report alone. Resolve its actor only through the source own immediately preceding named Abu Said, without inventing the omitted sayings or attributing the closing narrative voice as Prophetic speech.',
        'segments':[{'start':'آپ نے نبی کریم صلی اللہ علیہ وسلم کے ساتھ بارہ جہاد','end':None}],
    },
    ('1198','ur'): {
        'type':'prophetic_practice_report',
        'speaker':'Ibn Abbas reporting the night at his aunt Maimuna household',
        'note':'Read all1384 characters. Preserve bed orientations, the midnight-before-or-after uncertainty, waking gestures, the recited ten final AlImran verses as described, hanging water skin, ablution, Ibn Abbas joining, the right-hand/right-ear act, all six successive two-rakah clauses, one-rakah witr and the final light fajr pair. The parenthetical one-rakah count and fajr identification carry the actual prayer sequence and remain selected. No absent verse wording is reconstructed.',
    },
    ('1199','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Abdullah ibn Masud recounting the earlier and later prayer greetings and the Prophet final reply',
        'note':'Read all501 characters. Preserve the earlier greeting responses, return from the Negus, later unreturned prayer greeting and the final explanation after prayer. Both parenthetical earlier/in-prayer qualifications are necessary temporal and action details and stay in the report. The concluding reply retains its supplied wording.',
    },
    ('1200','ur'): {
        'type':'companion_report_of_prayer_practice_and_revelation',
        'speaker':'Zayd ibn Arqam reporting the prayer conversation practice and subsequent command of silence',
        'note':'Read all449 characters. Retain conversation with nearby worshippers during the Prophet era, the supplied abbreviated Arabic revelation quotation including its explicit ellipsis marker, and the command of silence. The in-prayer parenthetical qualification remains. Do not complete the verse or invent a named speaker for the passive command.',
    },
    ('1208','ur'): {
        'type':'prophetic_period_practice_report',
        'speaker':'Anas ibn Malik reporting their prostration practice while praying with the Prophet',
        'note':'Read all341 characters. The full field supplies their action of spreading a garment and prostrating on it when severe heat prevents placing the face fully on the ground. Preserve the heat condition, face placement and collective practice; no separate commentary or absent explicit command is introduced.',
    },
    ('1209','ur'): {
        'type':'prophetic_practice_report',
        'speaker':'Aisha recounting her own feet placement and the Prophet prayer movements',
        'note':'Read all468 characters. Retain her stretched feet before the praying Prophet, his touch before prostrating, her drawing them back and extending them again when he stood. This is a complete reported practice; there is no supplied side explanation to remove.',
    },
    ('1211','ur'): {
        'type':'historical_companion_dialogue_with_prophetic_period_report',
        'speaker':'Azraq ibn Qays narrating the event; Shuba explicitly identifies Abu Barza; Abu Barza gives the closing response',
        'note':'Read all871 characters. The Ahwaz geography definition is lexical context. Preserve the source-printed Abu Barza actor identification, praying with the horse rein, following the escaping horse, the unnamed Khariji curse and Abu Barza answer. His six-or-seven-or-eight campaigns uncertainty, observation of Prophetic ease and reason for retrieving the horse remain exact. Shuba explicit identity statement is a separately attributed piece of this same narrative family, not Prophetic speech or an extra occurrence.',
        'context':[' ( جو کئی بستیاں ہیں بصرہ اور ایران کے بیچ میں )'],
        'segments':[
            {'start':None,'end':'شعبہ نے کہا یہ ابوبرزہ اسلمی','type':'historical_companion_practice_report','speaker':'Azraq ibn Qays reporting the prayer and horse episode'},
            {'start':'شعبہ نے کہا یہ ابوبرزہ اسلمی','end':'یہ دیکھ کر خوارج میں سے','type':'narrator_identification_in_same_report','speaker':'Shuba explicitly identifying the already described participant as Abu Barza Aslami'},
            {'start':'یہ دیکھ کر خوارج میں سے','end':None,'type':'historical_dialogue_with_companion_testimony','speaker':'Unnamed Khariji and Abu Barza, with the latter reporting his Prophetic-era participation and observed ease'},
        ],
    },
    ('1215','ur'): {
        'type':'prophetic_period_collective_prayer_practice',
        'speaker':'Sahl ibn Sad reporting the worshippers and the command addressed to the women',
        'note':'Read all400 characters. Preserve the short waist garments tied around necks and the instructed delay until men had fully sat. The women-behind-men congregation qualification and the from-prostration head-raising qualification are operative details and remain. The command is passive in this field; no individual issuer is invented.',
    },
    ('1216','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Abdullah ibn Masud recounting prayer greetings and the Prophet reply',
        'note':'Read all569 characters. Preserve the source-printed early-Islam period, Abyssinia return and prior in-prayer greeting qualifications, the nonresponse and final Prophetic explanation. The separate parenthetical causal explanation about the newly revealed prohibition on prayer conversation is retained as source explanatory context, not silently attributed to the Prophet. Nothing is added from1199.',
        'context':[' ( کیونکہ اب نماز میں بات چیت وغیرہ کی ممانعت نازل ہو گئی تھی )'],
    },
    ('1217','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Jabir ibn Abdullah recounting the errand, his own suspicions and the Prophet eventual answer',
        'note':'Read all1002 characters. Preserve the BanuMustaliq setting, completion of the errand, repeated greetings, Jabir inner worry about delay and anger, the third greeting qualification and eventual explanation that prayer prevented the first two answers. Retain that the Prophet was on his she-camel facing away from the qibla. No internal thought becomes Prophetic speech and no missing intention is supplied.',
    },
    ('1221','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Uqba ibn Harith reporting the Asr prayer, quick departure and Prophet explanation',
        'note':'Read all705 characters. Preserve the quick post-salam departure into an unnamed wife chamber, return and recognition of the companions surprise, remembered remaining gold ingot, evening-or-night uncertainty and instruction to distribute it. The unidentified wife remains unidentified; no charity details or exact time are reconstructed.',
    },
    ('1223','ur'): {
        'type':'companion_recollection_and_dialogue_about_prophetic_prayer',
        'speaker':'Abu Hurayra and an unnamed participant in the previous night prayer',
        'note':'Read all554 characters. The opening criticism of his many transmissions, his actual test question, the other man attendance but lack of recall, and Abu Hurayra statement of recall form the report. Retain the rhetorical and test-purpose parentheticals as supplied narrative qualifications. The surahs remain literally such-and-such; no names or absent recitations are filled.',
    },
    ('1228.2','ur'): {
        'type':'scholarly_historical_dialogue',
        'speaker':'Salama ibn Alqama questioning Muhammad ibn Sirin, whose supplied answer concerns Abu Hurayra report',
        'note':'Read all160 characters. This numbered field supplies an actual question about tashahhud after forgetfulness prostrations and Muhammad ibn Sirin finite answer that it is absent from Abu Hurayra hadith. Retain the explicit IbnSirin name qualification and the complete exchange as scholarly dialogue. Do not turn that textual observation into a Prophetic ruling or invent the unquoted underlying hadith.',
    },
    ('1241','ur'): {
        'type':'separately_attributed_historical_reports',
        'speaker':'Aisha for Abu Bakr arrival and farewell; Ibn Abbas through Abu Salama for the subsequent public address',
        'note':'Read all1280 characters. The two explicit source attributions divide two historical reports: Aisha account of Abu Bakr arrival from Sunh, unveiling, kissing, tears and words about death; then AbuSalama from IbnAbbas account of the repeated requests to Umar, shahada, address and public reception. Keep their separate families within this provider occurrence. Preserve the actual abbreviated Quran quotation and its to-the-end marker without supplying the absent verse text or canonical number. The final oath and observation belong to the latter narrated account. Identical1242 remains separately preserved.',
        'segments':[
            {'start':None,'end':'ابوسلمہ نے ابن عباس','type':'historical_companion_report','speaker':'Aisha reporting Abu Bakr farewell words and actions','source_report_family_id':'deenhindi-bukhari:1241:aisha-farewell'},
            {'start':'ابوسلمہ نے ابن عباس','end':None,'type':'historical_companion_address_report','speaker':'Ibn Abbas through Abu Salama reporting Abu Bakr public address and its reception','source_report_family_id':'deenhindi-bukhari:1241:ibnabbas-address'},
        ],
    },
    ('1242','ur'): {
        'type':'separately_attributed_historical_reports',
        'speaker':'Aisha for Abu Bakr arrival and farewell; Ibn Abbas through Abu Salama for the subsequent public address',
        'note':'Separately read all1280 characters of this own source field. Preserve its two actual attributions and two report families, the Sunh arrival and farewell scene, repeated requests to Umar, public address and response, and the source-abridged Quran recitation including its to-the-end qualification. No omitted verse text, canonical number or independent new occurrence is invented. The wording matches1241 but its stable provider identity is not merged.',
        'segments':[
            {'start':None,'end':'ابوسلمہ نے ابن عباس','type':'historical_companion_report','speaker':'Aisha reporting Abu Bakr farewell words and actions','source_report_family_id':'deenhindi-bukhari:1242:aisha-farewell'},
            {'start':'ابوسلمہ نے ابن عباس','end':None,'type':'historical_companion_address_report','speaker':'Ibn Abbas through Abu Salama reporting Abu Bakr public address and its reception','source_report_family_id':'deenhindi-bukhari:1242:ibnabbas-address'},
        ],
    },
    ('1252','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Anas ibn Malik reporting the Prophet encounter and instruction to an unnamed woman',
        'note':'Read all280 characters. The complete field supplies a woman weeping while seated at a grave, the Prophet passing her and his instruction to fear Allah and be patient. No identity, later response or continuation absent from this field is added.',
    },
    ('1253','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Umm Atiyya reporting the washing instructions and the Prophet garment gift',
        'note':'Read all738 characters. Retain the source daughter uncertainty Zaynab-or-UmmKulthum, three-or-five-or-more washings, appropriateness condition, lote leaves and final camphor-or-some-camphor wording uncertainty, notification and garment instruction exactly as translated. The final sentence explaining that the pronoun means his izar is lexical/narrator explanation and stays in context. The printed shirt wording is not repaired from another language or edition.',
        'segments':[{'start':None,'end':'آپ صلی اللہ علیہ وسلم کی مراد اپنے ازار سے تھی۔'}],
    },
    ('1337','hi'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Abu Hurayra narrating the mosque servant death, companions replies and Prophet grave prayer',
        'note':'Read all893 Hindi characters. Preserve the source man-or-woman uncertainty, mosque service, unreported death, the Prophet questions, companions unspecified reasons and supplied not-troubling-you qualification, the narrator perception that the person was treated as insignificant, and the grave visit/funeral prayer. That perception remains narrator framing, not a Prophetic judgment. Do not invent the servant name or the missing specific reasons.',
    },
    ('1337','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Abu Hurayra narrating the mosque servant death, companions replies and Prophet grave prayer',
        'note':'Read all796 Urdu characters, retaining its own opening wording defect and punctuation. Preserve the man-or-woman uncertainty, the lack of notice, the questions and actual replies, the not-troubling-you qualification, narrator perception and final grave prayer. The narrator assessment is not assigned to the Prophet, and no servant identity or unprinted reason is supplied.',
    },
    ('1341','hi'): {
        'type':'prophetic_speech_report_with_historical_setting',
        'speaker':'The Prophet in the supplied report; the Hindi reporter name is printed defectively as aisa and is not repaired from Urdu',
        'note':'Read all709 Hindi characters. Preserve the defective opening chain and printed reporter name, and the final sadi wording exactly. Retain the illness setting, both explicitly named wives in parentheses, their Abyssinian visit, the church name and pictures, raising the head and the full attributed statement. The wives actor identifications are necessary narration qualifications. Do not fill missing chain names from the fuller Urdu field.',
    },
    ('1341','ur'): {
        'type':'prophetic_speech_report_with_historical_setting',
        'speaker':'Aisha reporting the wives account and the Prophet response',
        'note':'Read all719 Urdu characters. Retain this field own complete chain through Aisha, the illness, explicit UmmSalama/UmmHabiba parenthetical identities, Abyssinian church named Mariya, beauty and images, raising the head and complete reported response. These actual identities and setting remain in the report; no wording is transferred into the defective Hindi chain.',
    },
    ('1342','hi'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Anas reporting the Prophet at his daughter burial, with Abu Talha response',
        'note':'Read all777 Hindi characters. Preserve the visibly shortened/defective chain, unnamed daughter, the Prophet tears, the source-translated question about not visiting a woman that night, AbuTalha reply and descent, and Anas statement that he buried the deceased. Stop before IbnMubarak/Fulayh lexical interpretation of lam yuqarif and Bukhari Quran word explanation; both tails remain complete source context. Do not replace the actual reported question with the later lexical interpretation or fill a daughter name.',
        'segments':[{'start':None,'end':'अब्दुल्लाह बिन मुबारक ने बयां किया'}],
    },
    ('1342','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Anas reporting the Prophet at his daughter burial, with Abu Talha response',
        'note':'Read all807 Urdu characters. Retain this field full supplied chain, the funeral scene, tears, exact translated question, AbuTalha answer and descent, and Anas burial statement. IbnMubarak reporting Fulayh lexical opinion and Bukhari separate Quran word explanation are contextual apparatus after the completed event. They do not rewrite the report body or establish a different Prophetic quotation.',
        'segments':[{'start':None,'end':'عبداللہ بن مبارک نے بیان کیا'}],
    },
    ('1351','hi'): {
        'type':'companion_historical_testimony_and_family_dialogue',
        'speaker':'Jabir recounting his father Abdullah pre-Uhud instructions and his own subsequent burial observations',
        'note':'Read all946 Hindi characters. Preserve the father prediction, love comparison with its among-relatives-and-heirs qualification, debt instruction, nine-sister count, morning death, original shared burial and Jabir six-month later observation with the ear exception. These are father and son words/actions; none is turned into Prophetic speech. The unnamed co-buried man and exact biological observation remain source-attributed without additions.',
    },
    ('1351','ur'): {
        'type':'companion_historical_testimony_and_family_dialogue',
        'speaker':'Jabir recounting his father Abdullah pre-Uhud instructions and his own subsequent burial observations',
        'note':'Read all881 Urdu characters. Retain the entire father-son account, first-death expectation, precise affection comparison, relatives/heirs qualification, debt, nine sisters, initial common grave, six-month interval and stated ear-decay exception. Preserve the actual source testimony and unknown companion identity. No wording or additional details are taken from1352.',
    },
    ('1352','hi'): {
        'type':'companion_historical_testimony',
        'speaker':'Jabir reporting the original shared grave and subsequent reburial',
        'note':'Read all388 Hindi characters. Preserve the full own report and its supplied paternal-uncle relationship qualification for the other companion, along with Jabir dissatisfaction, exhumation and reburial. Do not invent a name or use this printed relationship to rewrite the unnamed other person in1351. Source pronouns remain exact.',
    },
    ('1352','ur'): {
        'type':'companion_historical_testimony',
        'speaker':'Jabir reporting the original shared grave and subsequent reburial',
        'note':'Read all368 Urdu characters. The complete finite historical account includes the source paternal-uncle identification in parentheses, Jabir concern and the reburial. Keep that actor relationship in the report and leave the name and exact pronoun wording unchanged; no cross-entry reconstruction is made.',
    },
    ('1357','hi'): {
        'type':'companion_autobiographical_statement',
        'speaker':'Abdullah ibn Abbas describing himself as a child and his mother among the women',
        'note':'Read all366 Hindi characters. Retain IbnAbbas entire autobiographical statement and the parenthetical Makkah-after-the-Prophet-migration setting, which qualifies the vulnerable group he describes. Preserve every supplied chain name exactly, without correction from memory, and do not invent his mother name or assign this saying to the Prophet.',
    },
    ('1357','ur'): {
        'type':'companion_autobiographical_statement',
        'speaker':'Abdullah ibn Abbas describing himself as a child and his mother among the women',
        'note':'Read all331 Urdu characters. Preserve the source chain, Makkah/post-migration temporal and location qualification, his place among the children and his mother among the women. The statement remains IbnAbbas own testimony; neither an unprinted mother name nor a repaired transmitter identity is supplied.',
    },
    ('1362','hi'): {
        'type':'prophetic_dialogue_and_practice_report',
        'speaker':'The Prophet and an unnamed questioner, through the Hindi field own unnamed first-person reporter after its defective chain',
        'note':'Read all1039 Hindi characters. Preserve the repeated bayan kiya chain defect and absent Companion identity rather than supplying Ali from Urdu. Retain the Baqi funeral setting, stick and ground-scratching action, either-person-or-soul wording, recorded destinations and condition, the actual reliance-versus-action question and full answer about ease. Keep the source short transliterated Quran recitation as supplied; no missing verse continuation, number or repaired words are added.',
    },
    ('1362','ur'): {
        'type':'prophetic_dialogue_and_practice_report',
        'speaker':'Ali reporting the Prophet funeral gathering statement and an unnamed companion question',
        'note':'Read all1145 Urdu characters. This field actually supplies Ali in its chain. Preserve the BaqiGharqad gathering, stick movement, person-or-soul alternative, both destinations, question about relying on the record and abandoning action, and complete reply. Retain the actual abbreviated Arabic recitation and ayah continuation marker without completing it or changing the defective Hindi account.',
    },
    ('1370','hi'): {
        'type':'prophetic_dialogue_report',
        'speaker':'Ibn Umar reporting the Prophet address and the accompanying people question',
        'note':'Read all492 Hindi characters. Preserve the shortened chain and printed pa wording defect. Keep the parenthetical identification of the well occupants as the Badr dead because it identifies the actors addressed. Retain the address, people question and the precise hearing/reply distinction; no missing chain members or dead-person names are imported from Urdu or another report.',
    },
    ('1370','ur'): {
        'type':'prophetic_dialogue_report',
        'speaker':'Ibn Umar reporting the Prophet address and the accompanying people question',
        'note':'Read all513 Urdu characters. Retain the complete own chain and source qualification identifying the well occupants, followed by the reported address, question and reply that distinguishes hearing from inability to answer. The parenthetical setting is an operative actor identification. No external counterpart or canonical identity is added.',
    },
    ('1378','hi'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Ibn Abbas reporting the Prophet statements and placement of two branch pieces',
        'note':'Read all640 Hindi characters. Preserve its abbreviated/defective chain, both grave reports, the source not-a-major-matter wording followed by yes, each stated cause, the green branch divided and placed on both graves, and the final perhaps-until-dry qualification. Do not harmonize its wording or remove the tentative scope of the last statement.',
    },
    ('1378','ur'): {
        'type':'prophetic_speech_and_practice_report',
        'speaker':'Ibn Abbas reporting the Prophet statements and placement of two branch pieces',
        'note':'Read all657 Urdu characters. Keep the supplied fuller chain, all two-grave statements and contrasting wording, the two stated causes, branch division and placement, and the precise tentative until-dry statement. No chain words are copied into Hindi and no modern inference or additional assurance is substituted for the source perhaps.',
    },
    ('1388','hi'): {
        'type':'prophetic_question_and_answer_report',
        'speaker':'Aisha reporting an unnamed man question and the Prophet affirmative answer',
        'note':'Read all473 Hindi characters. Retain the mother sudden death, the questioner expressly tentative belief about what she would have donated had she spoken, his proposed donation on her behalf and the full affirmative reply. Neither the man nor his mother is given an absent name, and his belief is not recast as an actual bequest.',
    },
    ('1388','ur'): {
        'type':'prophetic_question_and_answer_report',
        'speaker':'Aisha reporting an unnamed man question and the Prophet affirmative answer',
        'note':'Read all438 Urdu characters. Preserve the whole actual question and response, including sudden death and the son own stated supposition about his mother charitable intention. The proposed act and reward question remain distinct from a claimed spoken instruction; unknown names remain unknown.',
    },
}
