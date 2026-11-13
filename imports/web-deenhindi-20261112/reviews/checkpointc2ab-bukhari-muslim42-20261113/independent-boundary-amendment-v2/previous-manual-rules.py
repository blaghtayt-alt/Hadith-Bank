"""Serialize individually read source fields with explicit source-bound rules."""
from manual_readings import READINGS
SPECS={}

def put(key,kind,speaker,reason,**rules):
    SPECS[key]={'id':key,'decision':'register','languages':['hi','ur'],
        'read_languages':list(READINGS[key]),'field_notes':dict(READINGS[key]),
        'report_type':kind,'speaker':speaker,'reason':reason,**rules}

put('bukhari:2157','companion_pledge_report','Jarir reporting his pledge to Prophet Muhammad',
    'Keep the complete pledge and its actual scope. The designated-leader parenthesis limits obedience and supplies its referent; it is retained with the testimony and other pledge clauses.')
put('bukhari:2159','prophetic_prohibition_report','Ibn Umar transmitting the Messenger prohibition',
    'The actual rural-sale prohibition is supplied. The final Ibn Abbas said-the-same pointer remains context, with no duplicate report body manufactured.',
    stop_before={'hi':'यही इब्न अब्बास','ur':'یہی ابن عباس'})
put('bukhari:2161','attributed_passive_prohibition_report','Anas reporting that they were forbidden; the prohibiting authority is unnamed in this field',
    'Preserve the finite passive Anas report without inventing a named authority or direct Prophetic quotation.')
put('bukhari:2162','prophetic_prohibition_report','Abu Hurayra reporting the Prophet two prohibitions',
    'Retain both actual prohibitions, including the caravan target that restricts the interception instruction.')
put('bukhari:2163','attributed_question_and_answer','Tawus questioning Ibn Abbas, who supplies his own explanatory reply',
    'Keep the actual question/cited Prophetic prohibition separately from Ibn Abbas broker interpretation in this one transmitted dialogue.',
    shared_report_family=True,components={
      'hi':[{'stop_before':'तो उन्होंने कहा','report_type':'question_with_explicit_prophetic_citation','speaker':'Tawus asking Ibn Abbas about the expressly cited Prophet prohibition'},
            {'start_at':'तो उन्होंने कहा','report_type':'companion_explanatory_reply','speaker':'Ibn Abbas answering that he should not be the broker'}],
      'ur':[{'stop_before':'تو انہوں نے کہا','report_type':'question_with_explicit_prophetic_citation','speaker':'Tawus asking Ibn Abbas about the expressly cited Prophet prohibition'},
            {'start_at':'تو انہوں نے کہا','report_type':'companion_explanatory_reply','speaker':'Ibn Abbas answering that he should not be the broker'}]})
put('bukhari:2164','distinct_attributed_reports','Ibn Masud ruling followed by a separately attributed Prophetic prohibition',
    'Retain the actual goat-return instruction and one sa without filling its commodity. Separate the following Prophetic caravan prohibition from Ibn Masud own statement.',
    components={
      'hi':[{'stop_before':'और नबी करीम','report_type':'companion_legal_saying','speaker':'Ibn Masud giving the supplied goat-return ruling'},
            {'start_at':'और नबी करीम','report_type':'prophetic_prohibition_report','speaker':'Ibn Masud separately reporting the Prophet caravan prohibition'}],
      'ur':[{'stop_before':'اور نبی کریم','report_type':'companion_legal_saying','speaker':'Ibn Masud giving the supplied goat-return ruling'},
            {'start_at':'اور نبی کریم','report_type':'prophetic_prohibition_report','speaker':'Ibn Masud separately reporting the Prophet caravan prohibition'}]})
put('bukhari:2167','prophetic_market_practice_report','Abdullah reporting food sales and the Messenger prohibition until movement of the goods',
    'Only Arabic and English supply the actual market report. Hindi, Urdu and Roman Urdu are complete but duplicated chain-only fields and stay reviewed context. Each admitted field preserves its own movement/destination wording.',
    languages=['ar','en'],annotations={
      'ar':'The other three local-language fields contain repeated chains with no body. This Arabic report is independently supplied; no missing Hindi, Urdu or Roman text is synthesized. Arabic says to move the goods and is not expanded to the English destination wording.',
      'en':'This own complete English report is retained, including its their-places qualification. Arabic has its own wording; Hindi, Urdu and Roman Urdu lack the report body and remain context.'})
for key in ['bukhari:2180','bukhari:2181']:
    put(key,'companion_dialogue_with_prophetic_report','Source-named questioner, Bara and Zayd, with both Companions reporting the Prophet prohibition',
        'Preserve the question and mutual deference separately from the explicitly cited prohibition in one dialogue family. The sarf definition is glossary context. Similar wording does not merge the separate source IDs or repair the Hindi narrator name.',
        exclude_substrings={'hi':['(सोना चांदी के तबादले)'],'ur':['(سونا چاندی کے تبادلے)']},shared_report_family=True,
        components={
          'hi':[{'stop_before':'फिर दोनों ने कहा','report_type':'historical_question_and_companion_dialogue','speaker':'The Hindi source-named Abu al-Minhaj reporting his question and Bara/Zayd mutual deference'},
                {'start_at':'फिर दोनों ने कहा','report_type':'prophetic_prohibition_report','speaker':'Bara and Zayd jointly reporting the Messenger gold-for-silver-on-credit prohibition'}],
          'ur':[{'stop_before':'پھر دونوں نے کہا','report_type':'historical_question_and_companion_dialogue','speaker':'Abu al-Minhal reporting his question and Bara/Zayd mutual deference'},
                {'start_at':'پھر دونوں نے کہا','report_type':'prophetic_prohibition_report','speaker':'Bara and Zayd jointly reporting the Messenger gold-for-silver-on-credit prohibition'}]},
        annotations={'hi':'The Hindi source prints Abu al-Minhaj; it is not silently corrected to the different Urdu name. This occurrence remains distinct from the identically worded separate provider ID.'})
put('bukhari:2182','prophetic_exchange_instruction','Abu Bakra reporting the Prophet same-metal restrictions and cross-metal permissions',
    'Retain all source conditions and reciprocal permissions. No absent hand-to-hand clause is added.')
put('bukhari:2187','prophetic_prohibition_report','Ibn Abbas reporting the Prophet prohibition of muhaqala and muzabana',
    'The whole short field supplies the actual prohibition; no lexical definitions or canonical identities are added.')
put('bukhari:2189','prophetic_sale_prohibition_and_exception','Jabir reporting date-ripeness and exchange conditions and the ariya exception',
    'Retain the complete restriction and exception. Dry-fruit parentheses restrict the otherwise broad exchange category and remain. Hindi chain omissions and spellings are not repaired from Urdu.',
    annotations={'hi':'The Hindi chain is damaged and omits names supplied in Urdu. Its exact text remains unfilled; no sibling chain is imported.'})
put('bukhari:2196','prophetic_question_and_answer','Jabir reporting the Prophet fruit-sale prohibition and ripeness answer',
    'The actual question and yellow/red edible-ripeness answer remain. The final ripeness-is-meant gloss stays separately as context.',
    exclude_substrings={'hi':['(फल का पुख़्ता होना मुराद है)'],'ur':['( پھل کا پختہ ہونا مراد ہے )']})
put('bukhari:2203','attributed_legal_saying','Nafi giving the transmitted sale ruling; no Prophetic attribution asserted',
    'This is a finite source-attributed Nafi statement, not an unattributed compiler essay. Preserve all three named categories and the transmission confirmation. Abu Abdullah identity gloss is context.',
    exclude_substrings={'hi':['(इमाम बुख़ारी रहमतुल्लाह)'],'ur':['(امام بخاری رحمہ اللہ)']})
put('bukhari:2205','prophetic_prohibition_with_supplied_transaction_scope','Ibn Umar reporting the Prophet prohibition and its three specified sale cases',
    'The yani passage enumerates the actual cases governed by the explicitly resumed he-forbade-all-these-kinds assertion. Retain this substantive transaction scope with the report rather than detach it as a glossary.')
put('bukhari:2207','prophetic_prohibition_report','Anas transmitting the Prophet five named transaction prohibitions',
    'The full list is supplied report content. No definition or missing rule is added to the named transactions.')
put('bukhari:2209','companion_eyewitness_prophetic_dialogue','Ibn Umar reporting his presence, thought and silence during the Prophet tree comparison',
    'Retain the complete dialogue and finite first-person silence-in-deference parenthesis; it is an actual narrated act, not a lexical gloss.')
put('bukhari:2210','prophetic_cupping_payment_report','Anas reporting Abu Tayba cupping, the Prophet dates-payment order and levy-reduction request',
    'Retain the concrete payment purpose expressed by the wages parenthesis, the dates amount and the request to the masters. No general legal inference is introduced.')
put('bukhari:2211','prophetic_dialogue_report','Aisha narrating Hind question and the Prophet limited maintenance reply',
    'Preserve the actual question, answer, intention and family-sufficiency conditions; no unprinted amount or permission is inferred.')
put('bukhari:2212','companion_quran_explanation_report','Aisha citing the supplied verse and explaining the orphan-guardian scope',
    'Retain the actual reported recitation/transliteration, source translation and Aisha explanation. Remove only chain and verse labels plus explicit interpretive parenthetical expansions. This is Aisha attributed explanation, not a new Prophetic quotation.',
    exclude_substrings={
      'hi':['(दूसरी सनद)','(क़ुरान की आयत)','(अपनी ज़ेर-ए-परवरिश यतीम का माल हज़म करने से)','(इस ख़िदमत के एवज़)'],
      'ur':['(دوسری سند)','( قرآن کی آیت )','( اپنی زیر پرورش یتیم کا مال ہضم کرنے سے )','( اس خدمت کے عوض )']},
    annotations={'hi':'The Quran wording and its source translation are part of the explicitly attributed Aisha explanation and are retained in that role. No canonical verse locator or Prophetic attribution is supplied.',
                 'ur':'The printed Arabic Quran wording and Urdu rendering remain within Aisha own explanation. The source punctuation is preserved; no absent canonical locator is inferred.'})
put('bukhari:2213','prophetic_preemption_report','Jabir transmitting the Prophet rule and its boundary/road limitation',
    'Retain the full undivided-property rule and both source limitations without merging source occurrences.')
put('bukhari:2214','prophetic_preemption_report','Jabir transmitting this occurrence own Prophet rule and its boundary/road limitation',
    'Preserve the complete independently numbered report and source chain. It does not provide missing text for2214.2.')
put('bukhari:2218','prophetic_judgment_dialogue','Aisha narrating Sad and Abd claims, Prophet judgment and Sawda direction',
    'Keep the coherent multi-speaker event with its actual claims, resemblance, judgment and later conduct. No wording, identity or legal commentary is manufactured.')

put('muslim:2162','finite_transmitted_rebuke_variant','Unspecified speaker and addressee in Abdul Aziz transmitted rebuke; the Messenger is its object, not an asserted speaker',
    'Only the actual affirmative Abdul Aziz variant is selected. The initial similar-chain reference remains context, and the rebuke speaker/addressee are not filled from another record.',
    start_at={'hi':'और अब्दुल अज़ीज़ की हदीस में','ur':'اور عبد العزیز کی حدیث میں'},
    annotations={'hi':'The field gives a complete rebuke but does not identify who says it or to whom. The Messenger is the person allegedly troubled; this is not labelled his own speech.',
                 'ur':'The speaker and addressee of this finite variant are not named. They remain unspecified; no prior body is reconstructed.'})
put('muslim:2163','companion_pledge_and_compliance_report','Umm Atiyya reporting the Prophet pledge and the women compliance',
    'Retain the full pledge, literal five/list/alternative wording, and material fully-complied qualifier. Separate the transmitter identity gloss only.',
    exclude_substrings={'hi':['(बिन सीरीन)'],'ur':['( بن سیرین )']},
    annotations={'hi':'The list/alternative wording and announced five are preserved without reconciling a count or adding a missing woman.',
                 'ur':'Damaged spacing and the literal alternative between named women stay unchanged; no list harmonization is performed.'})
put('muslim:2164','attributed_pledge_and_compliance_report','The source-named female reporter describing the pledge and five exceptions',
    'Retain the full account and extent-of-compliance qualification. The parenthetic repeated five is an explanatory repeat of the already explicit count, not a new condition.',
    exclude_substrings={'hi':['(पाँच)'],'ur':['( پانچ )']},
    components={
      'hi':[{'report_type':'companion_pledge_and_compliance_report','speaker':'Umm Atiyya reporting the Prophet pledge and five exceptions'}],
      'ur':[{'report_type':'attributed_pledge_and_compliance_report','speaker':'The Urdu source-named Atiyya reporting the Prophet pledge and five exceptions; missing Umm is not inserted'}]},
    annotations={'ur':'This own source prints حضرت عطیہ. The missing Umm prefix is not copied from Hindi or another record.'})
put('muslim:2166','attributed_funeral_practice_report','Umm Atiyya reporting a passive prohibition with an expressly non-strict qualification',
    'Keep the complete non-strictness qualification and unspecified commanding authority; no direct Prophetic quotation is invented.')
put('muslim:2167','attributed_funeral_practice_report','Umm Atiyya report transmitted through Hafsa; the prohibiting authority is unnamed',
    'Retain the actual passive prohibition and non-strictness qualification under their supplied attribution.')
put('muslim:2168','companion_report_with_prophetic_washing_instruction','Umm Atiyya describing the Prophet visit during his daughter washing and his instructions',
    'Keep the actual washing quantities, optional increase, source leaf-material specification, camphor and garment instructions. Missing daughter identity and punctuation are not repaired.')
put('muslim:2169','attributed_historical_practice_report','Umm Atiyya describing their combing and three plaits; the person is unnamed here',
    'The finite braiding report stands on its own. Do not name the person from a neighboring source; the Urdu hair-object clarification remains context.',
    exclude_substrings={'ur':['( کے بالوں )']},
    annotations={'hi':'The supplied लातें spelling remains literal. The person whose hair is arranged is not identified in this own field.',
                 'ur':'The person whose hair was combed is not named; no daughter identity is filled.'})
put('muslim:2170','affirmative_transmitted_historical_variants','Umm Atiyya death/arrival report and its Ibn Ulayya and Malik transmitted openings',
    'Keep all three actually supplied affirmative fragments as variants of one report family. The parenthetic Umm Atiyya attribution stays in the Ibn Ulayya variant so it cannot be mistaken for his eyewitness account. Only the redundant Urdu yuun connector and final same-report pointer remain context.',
    stop_before={'hi':'(इस से आगे)','ur':'( اس سے آگے )'},exclude_substrings={'ur':['( یوں )']},shared_report_family=True,
    components={
      'hi':[{'stop_before':'इब्न-ए-उलैय्या की हदीस में','report_type':'historical_death_report','speaker':'Umm Atiyya reporting the death of one Prophet daughter'},
            {'start_at':'इब्न-ए-उलैय्या की हदीस में','stop_before':'और मालिक की हदीस में','report_type':'transmitted_arrival_during_washing_variant','speaker':'Umm Atiyya explicit first-person report in Ibn Ulayya transmission'},
            {'start_at':'और मालिक की हदीस में','report_type':'transmitted_arrival_after_death_variant','speaker':'Umm Atiyya report in Malik transmission, not Malik own eyewitness act'}],
      'ur':[{'stop_before':'ابن علیہ کی حدیث میں','report_type':'historical_death_report','speaker':'Umm Atiyya reporting the death of one Prophet daughter'},
            {'start_at':'ابن علیہ کی حدیث میں','stop_before':'اور مالک کی حدیث میں','report_type':'transmitted_arrival_during_washing_variant','speaker':'Umm Atiyya explicit first-person report in Ibn Ulayya transmission'},
            {'start_at':'اور مالک کی حدیث میں','report_type':'transmitted_arrival_after_death_variant','speaker':'Umm Atiyya report in Malik transmission, not Malik own eyewitness act'}]})
put('muslim:2171','finite_washing_and_braiding_fragments','An unnamed respectful-pronoun directive followed by the literal Hafsa-to-Umm-Atiyya braiding attribution',
    'Keep the actual variant directive, including its parenthetic wash predicate, and the separately supplied braiding statement. Do not turn آپ into a named Prophet or repair the printed Hafsa-to-Umm-Atiyya relation from a parallel.',
    start_at={'hi':'इसके सिवा के आपने','ur':'اس کے سوا کہ آپ'},exclude_substrings={'ur':['( کے بالوں )']},shared_report_family=True,
    components={
      'hi':[{'stop_before':'हफसा ने उम्मे अतिया','report_type':'transmitted_washing_directive_with_unspecified_speaker','speaker':'An unnamed respectful-pronoun speaker in the supplied affirmative variant; no Prophetic identity asserted'},
            {'start_at':'हफसा ने उम्मे अतिया','report_type':'historical_braiding_statement_as_printed','speaker':'The source literally prints Hafsa saying to Umm Atiyya that we made three plaits; no speaker repair'}],
      'ur':[{'stop_before':'حفصہ نے ام عطیہ','report_type':'transmitted_washing_directive_with_unspecified_speaker','speaker':'An unnamed respectful-pronoun speaker in the supplied affirmative variant; no Prophetic identity asserted'},
            {'start_at':'حفصہ نے ام عطیہ','report_type':'historical_braiding_statement_as_printed','speaker':'The source literally prints Hafsa saying to Umm Atiyya that we made three plaits; no speaker repair'}]},
    annotations={l:'This field does not name the directive speaker. Its following Hafsa-to-Umm-Atiyya wording is preserved literally rather than corrected from another version.' for l in ['hi','ur']})
put('muslim:2172','washing_instruction_and_historical_braiding_report','Expressly source-named Prophet directive and Umm Atiyya separately stated braiding observation',
    'Retain the parenthetic Messenger attribution and reporting relation because they establish actual speaker scope. Separate the directive from Umm Atiyya observation; only Ismail and the repeated Urdu hair-object gloss are context.',
    exclude_substrings={'hi':['(इस्माईल)'],'ur':['(اسماعیل )','( کے بالوں )']},shared_report_family=True,
    components={
      'hi':[{'stop_before':'कहा और उम्मे अतिया','report_type':'prophetic_washing_instruction','speaker':'Prophet Muhammad as explicitly named within this source parenthesis, transmitted through Hafsa/Umm Atiyya'},
            {'start_at':'कहा और उम्मे अतिया','report_type':'attributed_historical_braiding_report','speaker':'Umm Atiyya explicitly describing their three-plait action'}],
      'ur':[{'stop_before':'کہا اور ام عطیہ','report_type':'prophetic_washing_instruction','speaker':'Prophet Muhammad as explicitly named within this source parenthesis, transmitted through Hafsa/Umm Atiyya'},
            {'start_at':'کہا اور ام عطیہ','report_type':'attributed_historical_braiding_report','speaker':'Umm Atiyya explicitly describing their three-plait action'}]})
put('muslim:2174','washing_report_and_explicit_braiding_addition','Umm Atiyya visit/washing report and her later expressly attributed braid detail',
    'Keep the two actual fragments and each language own length. The Ayyub/Asim similar-meaning bridge is context. Retain the parenthetic Umm Atiyya subject in the resumed fragment to preserve its actual attribution.',
    shared_report_family=True,components={
      'hi':[{'stop_before':'(आगे)','report_type':'prophetic_washing_instruction_report','speaker':'Umm Atiyya reporting the Prophet arrival and odd-five-or-more washing direction'},
            {'start_at':'इस हदीथ में उन्होंने कहा:','report_type':'explicit_historical_braiding_addition','speaker':'Umm Atiyya expressly identified in the source resumed three-part braiding statement'}],
      'ur':[{'stop_before':'( آگے )','report_type':'prophetic_washing_instruction_report','speaker':'Umm Atiyya reporting the Prophet arrival and odd-five-or-more washing direction'},
            {'start_at':'اس حدیث میں انھوں نے کہا :','report_type':'explicit_historical_braiding_addition','speaker':'Umm Atiyya expressly identified in the resumed braiding statement, including the Urdu sides/front detail'}]},
    annotations={'hi':'The Hindi supplied braid addition stops after three parts. The longer Urdu side/front detail is not inserted.'})
put('muslim:2179','burial_report_and_companion_historical_account','Aisha reporting the Prophet shrouding and Abdullah ibn Abi Bakr later hulla statements/actions',
    'Keep the shrouding narrative and later Abdullah history as separate components in one linked source account. Exact identity/geographic/lexical expansions are context, while the actual intention, counterfactual, sale and charity remain.',
    exclude_substrings={
      'hi':['(उरवा)','(यमन)','(हम-रंग चादरों पर मुश्तमिल जोड़े)','(हुल्ले)','(अपने पास)','(देने का बंदोबस्त कर)'],
      'ur':['( عروہ )','( یمن )','( ہم رنگ چادروں پر مشتمل جوڑے )','( حلے )','( اپنے پاس )','( دینے کا بندوبست کر )']},shared_report_family=True,
    components={
      'hi':[{'stop_before':'और उस (हुल्ले)','report_type':'prophetic_burial_report','speaker':'Aisha describing the Prophet three-cloth shrouding and the unused hulla account'},
            {'start_at':'और उस (हुल्ले)','report_type':'companion_historical_saying_and_action','speaker':'Aisha reporting Abdullah ibn Abi Bakr own intention, reconsideration, sale and monetary charity'}],
      'ur':[{'stop_before':'اور اس ( حلے )','report_type':'prophetic_burial_report','speaker':'Aisha describing the Prophet three-cloth shrouding and the unused hulla account'},
            {'start_at':'اور اس ( حلے )','report_type':'companion_historical_saying_and_action','speaker':'Aisha reporting Abdullah ibn Abi Bakr own intention, reconsideration, sale and monetary charity'}]})
put('muslim:2180','burial_report_and_companion_historical_account','Urwa transmission of shrouding and Abdullah ibn Abi Bakr later garment account',
    'This field has no Aisha link and is not completed from2179. Preserve actual wrapping/removal and Abdullah own rhetorical statement and garment donation. Identity/kafn glosses remain context.',
    exclude_substrings={'hi':['(उरवा)','(कफ़न दिया)'],'ur':['( عروہ )','( کفن دیا )']},shared_report_family=True,
    components={
      'hi':[{'stop_before':'अब्दुल्लाह (रज़ियल्लाहु अन्हु) ने वो','report_type':'transmitted_prophetic_burial_report','speaker':'Urwa, Hisham father, transmitting the Prophet temporary wrapping and three-cloth shrouding; no Aisha link supplied'},
            {'start_at':'अब्दुल्लाह (रज़ियल्लाहु अन्हु) ने वो','report_type':'companion_historical_saying_and_action','speaker':'Urwa transmission describing Abdullah ibn Abi Bakr statements and donation of the garment'}],
      'ur':[{'stop_before':'عبد اللہ رضی اللہ تعالیٰ عنہ نے وہ حلہ','report_type':'transmitted_prophetic_burial_report','speaker':'Urwa, Hisham father, transmitting the Prophet temporary wrapping and three-cloth shrouding; no Aisha link supplied'},
            {'start_at':'عبد اللہ رضی اللہ تعالیٰ عنہ نے وہ حلہ','report_type':'companion_historical_saying_and_action','speaker':'Urwa transmission describing Abdullah ibn Abi Bakr statements and donation of the garment'}]},
    annotations={l:'The own source transmits through Hisham father and does not name Aisha. Its garment donation remains distinct from the sale/monetary-charity wording of2179.' for l in ['hi','ur']})
put('muslim:2183','prophetic_death_observation_report','Aisha reporting the striped Yemeni covering after the Prophet death',
    'Keep the entire finite death/covering report. The malformed Urdu parenthesis cannot exclude the body: only the two identity fragments and stranded closing delimiter are context; no source punctuation is repaired.',
    exclude_substrings={'hi':['(बिन कैसान)','(ज़ुहरी)'],'ur':['( بن کیسان )','( زہری',')']},
    annotations={'ur':'The source opens a parenthesis before Zuhri and closes it after the entire report. Only the identity fragment and stranded delimiter are separated as context; all intervening narrative words remain literal.'})
put('muslim:2215','prophetic_inquiry_and_grave_prayer_report','Abu Hurayra narrating the cleaner inquiry and grave prayer, with each own language actual extent',
    'Preserve the source woman/man uncertainty and complete historical report. Hindi lacks the final speech opening and attribution, so its orphaned tail remains context. Urdu independently supplies a fully introduced Prophetic statement and retains it separately.',
    exclude_substrings={'hi':['(सहाबा)'],'ur':['( صحابہ رضوان اللہ عنھم اجمعین )','( قبروں )']},
    stop_before={'hi':'वजह से अल्लाह'},shared_report_family=True,
    components={
      'hi':[{'report_type':'prophetic_inquiry_and_grave_prayer_report_with_source_omission','speaker':'Abu Hurayra reporting the Prophet inquiry and prayer; the source woman/youth alternative is damaged and remains unfilled'}],
      'ur':[{'stop_before':'پھر فرمایا :','report_type':'prophetic_inquiry_and_grave_prayer_report','speaker':'Abu Hurayra narrating the Prophet inquiry, explicit woman-or-man uncertainty and grave prayer'},
            {'start_at':'پھر فرمایا :','report_type':'prophetic_statement_about_grave_prayer','speaker':'Prophet Muhammad as expressly introduced in the complete Urdu source'}]},
    annotations={'hi':'The Hindi field omits the first or in the woman/youth opening and the start/attribution of the final graves-light speech. The coherent story is preserved; the dangling final tail is context, not filled from Urdu.'})
put('muslim:2222','prophetic_funeral_question_and_answer','Jabir reporting standing for the funeral, the Jewish-woman question and the Prophet reply',
    'Keep the complete dialogue and cause-of-fear qualification inside the actual reply. The parenthetic funeral label repeats the already supplied event and remains explanatory context.',
    exclude_substrings={'hi':['(का जनाज़ा)'],'ur':['( کا جنازہ )']})

for key,reason in [
 ('bukhari:2214.2','All five complete fields contain same-as chains and isolated prepositional property-scope comparisons without the underlying assertion. No rule is reconstructed from another number.'),
 ('muslim:2181','All five complete fields contain same-chain transmission and an omitted-story comparison, without the report body. A statement that the story is absent does not supply that story.'),
 ('muslim:2229','All five complete fields contain only a same-chain/same-report pointer. There is no finite report body to register.')]:
    SPECS[key]={'id':key,'decision':'exclude','languages':[],
        'read_languages':list(READINGS[key]),'field_notes':dict(READINGS[key]),
        'report_type':'source_context_only','speaker':'No supplied report speaker/body',
        'reason':reason}

# These refinements preserve the first-reading notes while recording the exact
# later attribution-boundary assessment before any candidate was frozen.
BOUNDARY_REFINEMENTS={
 'muslim:2170':'Retain the explicit parenthetic Umm Atiyya subject at the opening of Ibn Ulayya variant: it materially distinguishes the report speaker from the transmitting Ibn Ulayya.',
 'muslim:2174':'Retain the explicit parenthetic Umm Atiyya subject in the resumed braid fragment; the intervening compiler bridge does not make her actual supplied attribution expendable.'}
for key,note in BOUNDARY_REFINEMENTS.items():
    for language in ['hi','ur']:
        SPECS[key]['field_notes'][language] += ' Exact boundary refinement: '+note

assert set(SPECS)==set(READINGS)
assert len(SPECS)==42
RETAINED_NONHONORIFIC={}
RETAINED_MARKER_WORDS={}
RETAINED_MARKER_WORDS[('bukhari:2218','hi','सूरत')]='This word means the child appearance/face in the actual resemblance observation. It is not a Surah name or verse locator.'

def keep(key,hi,ur,reason):
    if hi is not None: RETAINED_NONHONORIFIC[(key,'hi',hi)]=reason
    if ur is not None: RETAINED_NONHONORIFIC[(key,'ur',ur)]=reason

keep('bukhari:2157','(अपने मुक़र्ररा अमीर की बात)','( اپنے مقررہ امیر کی بات )',
     'Limits the actual listening/obedience clause to the designated leader and supplies the following possessive antecedent.')
keep('bukhari:2162','(तिजारती क़ाफ़िलों से)','( تجارتی قافلوں سے )',
     'Supplies the actual target of going out to meet; removing it would broaden the prohibition beyond the source caravan scope.')
keep('bukhari:2164','(वह बकरी फेर दे)','( وہ بکری پھیر دے )',
     'Actual finite return-the-goat directive within Ibn Masud own reported ruling.')
RETAINED_NONHONORIFIC[('bukhari:2167','en','(their)')]='The possessive restricts the English destination wording; it stays independently of the different Arabic movement wording.'
keep('bukhari:2189','(सूखे फल)','( سوکھے پھل )',
     'Material exchange-category qualifier on otherwise unrestricted any-other-thing wording; it prevents broadening the supplied prohibition.')
keep('bukhari:2209','(इस लिये बतौरे-अदब मैं चुप रहा)','( اس لیے بطور ادب میں چپ رہا )',
     'A finite first-person narrated silence action and its supplied reason, not a dictionary or identity gloss.')
keep('bukhari:2210','(मज़दूरी में)','( مزدوری میں )',
     'Supplied concrete payment purpose in the cupping event; retained as remuneration scope, without deriving a general legal rule.')
for key in ['muslim:2163','muslim:2164']:
    keep(key,'(कमा-हक़्क़ा)','( کماحقہ )',
         'Material degree-of-compliance qualification; removing fully would overstate the report as complete noncompliance.')
keep('muslim:2168','(के पत्तों)','( کے پتوں )',
     'Specifies the actual plant material in the practical washing instruction; retain the source leaf limitation.')
keep('muslim:2170','(उम्मे अतिया रज़ि अल्लाहु अन्हा ने)','( ام عطیہ رضی اللہ تعالیٰ عنہا نے )',
     'Explicit subject of the first-person transmitted variant, distinguishing Umm Atiyya from transmitting Ibn Ulayya.')
keep('muslim:2171','(गुस्ल देना)','( غسل دینا ۔ )',
     'Supplies the only printed operative wash predicate for the three/five/seven/more directive; necessary actual report content.')
keep('muslim:2172','(बयान करते हुए)','( بیان کرتے ہو ئے )',
     'Qualifies the actual Hafsa-from-Umm-Atiyya transmission relation and prevents an unsupported direct-conversation reading.')
keep('muslim:2172','(रसूल अल्लाह सल्लल्लाहु अलैहि वसल्लम ने)','( رسول اللہ صلی اللہ علیہ وسلم نے )',
     'Only express source naming of the directive speaker; retaining it preserves supplied attribution rather than inferring it.')
keep('muslim:2174','(उम्मे आतिया रज़ियल्लाहु अन्हा ने)','( ام عطیہ رضی اللہ تعالیٰ عنہا نے )',
     'Express attribution of the resumed braiding statement after the separate compiler bridge; material to its actual speaker.')
keep('muslim:2222','(का बाइस)','( کا باعث )',
     'Qualifies the actual predication as death causing fear/distress; preserve the source causal relation in the quoted reply.')
