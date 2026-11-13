"""Manual source-first readings of Nasai10; no automatic admission rules."""
SPECS={}

def add(number, report_type, speaker, hi_note, ur_note, **extra):
    SPECS[number]={'id':'nasai:'+number,'decision':'register','report_type':report_type,
        'speaker':speaker,'reason':'Complete own-language narration with the printed attribution; no missing wording, external identity or new authenticity grade is supplied.',
        'read_languages':['hi','ur'],'languages':['hi','ur'],
        'field_notes':{'hi':hi_note,'ur':ur_note},'shared_report_family':True,**extra}

add('821','companion_observation_of_prophetic_era_practice',
    'Abd al-Hamid ibn Mahmud reports the shared prayer and Anas saying they avoided praying between pillars during the Messenger’s lifetime; no direct Prophetic utterance is supplied',
    'Abd al-Hamid narrates praying with Anas and a ruler. The crowd pushes them between two pillars; Anas withdraws and recalls avoiding this in the Messenger’s time. Retain the crowd-cause parenthesis and every action. Only the redundant inline English noun gloss (pillars) is separate lexical context; do not turn Anas’s statement into Prophetic speech.',
    'Abd al-Hamid narrates the ruler-led prayer, crowd pressure, two pillars and Anas withdrawing, then Anas’s own earlier-practice statement. Preserve the whole field, including the parenthetical crowd circumstance. The source gives an observed era-practice statement, not an explicit command spoken by the Prophet.',
    exclude_substrings={'hi':[' (pillars)']})
add('822','companion_preference_report',
    'The source-named al-Bara reports his own preference when praying behind the Messenger',
    'The printed Hindi narrator name is bare/Bara; retain it verbatim. He says he preferred standing on the Messenger’s right when praying behind him. Only the redundant parenthetic English right transliterated as राइट is lexical context; the actual right-direction word remains.',
    'Bara says he preferred standing to the Messenger’s right while they prayed behind him. The complete finite statement is his preference, with no added Prophetic approval or command.',
    exclude_substrings={'hi':[' (राइट)']})
add('2153','attributed_historical_report',
    'Zirr ibn Hubaysh describes eating suhur with Hudhayfah and their subsequent prayer sequence',
    'Zirr says he ate suhur with Hudhayfah, then went to prayer. At the mosque they had just prayed two sunnah units when the prayer began, with a very small interval. Preserve the whole sequence and short-interval qualification. The field does not attribute this report to the Prophet.',
    'Zirr’s own account has suhur with Hudhayfah, going to the mosque, two sunnah units, onset of prayer and only a slight interval. Retain all temporal wording; no Prophetic attribution is inferred from the person or collection.')
add('2160','prophetic_practice_report',
    'Abu Atiyyah reports Masruq’s question and Aisha’s reply about the Messenger’s practice',
    'Abu Atiyyah and Masruq visit Aisha. Masruq compares two diligent Companions, one delaying and one hastening both prayer and iftar; Aisha asks who hastens, he identifies Abdullah ibn Masud, and she says the Messenger acted likewise. Retain the contrast parenthesis and both prayer/iftar predicates; no name is supplied for the delaying person in this field.',
    'The field independently supplies Abu Atiyyah and Masruq’s visit, Masruq’s comparison, Aisha’s question, Ibn Masud’s name and her Prophetic-practice reply. Keep the complete dialogue and the contrast parenthesis. Preserve its own present-tense final wording rather than normalizing to another field.')
add('2161','prophetic_practice_report',
    'Abu Atiyyah reports his and Masruq’s exchange with Aisha; a trailing source voice identifies the other person',
    'Abu Atiyyah and Masruq jointly address Aisha about two Companions’ differing prayer and iftar timing. She identifies Ibn Masud’s practice as the Messenger’s. The final parenthetic Abu Musa identification is actual narrative information and remains in a second same-family component, attributed to an unspecified source voice rather than Aisha or the Prophet.',
    'The Urdu independently gives the joint question, both timing differences, Aisha’s question, the Ibn Masud answer and the Prophetic-practice comparison. Retain the complete final Abu Musa identification in a separately attributed second component; parentheses do not make this supplied actor identification disposable.')
add('2180','prophetic_practice_report','Aisha describes the Messenger’s fasting practice',
    'Aisha reports no other month with more fasting than Shaban, followed by approximately the whole Shaban. The parenthetic तक़रीबन is an essential approximation and must remain with the whole-month wording.',
    'Aisha reports the greatest amount of fasting in Shaban and approximately all of it. Preserve تقریباً as an integral limit; do not turn the phrase into an unqualified full-month claim.')
add('2182','prophetic_practice_report','Aisha states the limits of her own knowledge of the Messenger’s practice',
    'Aisha says she does not know of him reading the whole Quran in one night, standing the whole night until morning, or fasting an entire month other than Ramadan. Retain the epistemic opening, each full-scope qualifier and the Ramadan exception.',
    'Aisha’s first-person knowledge qualification governs all three negatives: complete Quran in one night, all-night standing until morning, and complete month fasting outside Ramadan. The complete own field is retained without strengthening the epistemic claim.')
add('2220','prophetic_dialogue_report','Abu Umamah asks the Messenger, who replies about maintaining fasting',
    'Abu Umamah approaches and asks for a command taken directly from the Messenger. The reply instructs fasting and states that no worship equals it. Retain the direct-reception request and the complete supplied reply.',
    'Abu Umamah’s direct-reception request is followed by the fasting instruction and comparison. The parenthetic worship noun is the supplied object of that comparison and remains. Only the appended footnote marker and its trailing punctuation are source apparatus.',
    stop_before={'ur':' ۱؎'})
add('2221','prophetic_dialogue_report','Abu Umamah al-Bahili asks the Messenger, who replies about fasting',
    'Abu Umamah asks for something through which Allah will benefit him; the Messenger instructs maintaining fasting because no worship equals it. The entire finite exchange is supplied and retained.',
    'Abu Umamah’s benefit request and the fasting response are complete. Retain the parenthetic worship noun inside the comparison as the translation’s supplied meaning; it is not an unrelated legal note.')
add('2223','prophetic_dialogue_report','Abu Umamah al-Bahili recounts two requests and two answers from the Messenger',
    'Two separate requests and two fasting replies are actually printed. Retain both, with the first comparison saying nothing like it and the second saying nothing equal to it. Do not collapse the repetition.',
    'The Urdu has two request-answer turns. Retain the parenthetic action noun and the parenthetic again marker because they supply the comparison object and sequence. Keep both source replies separately within the one dialogue.')

SPECS['2161']['read_languages']=['hi','ur','ar','en','ur-Latn']
SPECS['2161']['languages']=['hi','ur','ar','en','ur-Latn']
SPECS['2161']['field_notes'].update({
    'ar':'Read the complete isnad and body. Abu Atiyyah reports his and Masruq’s visit, Aisha’s question and reply, then the source ends with the other being Abu Musa. Retain every character. The final identification has its own source-narrative component; do not assign its speaker to Aisha. No biographical or canonical identity is filled.',
    'en':'The complete source independently reports the Abu Atiyyah/Masruq/Aisha exchange and ends And the other was Abu Musa. Preserve all original quotation punctuation and the printed has hastens wording. Retain the final identification in a second same-family component with unspecified source voice.',
    'ur-Latn':'The complete Roman Urdu field supplies the same connected visit and timing dialogue in its own words, plus the parenthetic Abu Musa Ashari identification. Preserve every source character and honorific, with the final identifying voice unspecified rather than assigned to Aisha or the Prophet.'})
tail_markers={'hi':' (दूसरे शख़्स','ur':' ( دوسرے شخص','ar':' وَالآخَرُ أَبُو مُوسَى','en':' And the other was Abu Musa','ur-Latn':' (Dusre shakhs'}
SPECS['2161']['components']={lang:[
    {'stop_before':marker,'report_type':'prophetic_practice_report','speaker':'Abu Atiyyah reports his and Masruq’s dialogue with Aisha about the Messenger’s practice'},
    {'start_at':marker,'report_type':'source_narrative_identification','speaker':'Unspecified source voice identifying the other person as the source-printed Abu Musa; no attribution to Aisha or the Prophet','reason':'Retain the actual trailing identification as a same-family narrative component, including its own original spelling and honorifics.'}]
    for lang,marker in tail_markers.items()}

RETAINED_NONHONORIFIC={
    ('821','hi','(भीड़ की वजह से)'):'Actual narrative crowd circumstance explaining the physical pressure in this source field.',
    ('821','ur','( بھیڑ کی وجہ سے )'):'Actual crowd circumstance in the supplied prayer narrative.',
    ('2160','hi','(लेकिन)'):'Contrast connecting the two reported practices.',
    ('2160','ur','( لیکن )'):'Contrast connecting the two reported practices.',
    ('2161','hi','(दूसरे शख़्स अबू मूसा अशअरी (रदी अल्लाहु अन्हु) थे।)'):'Source-printed identity of the other participant; separate same-family identifying voice.',
    ('2161','ur','( دوسرے شخص ابوموسیٰ اشعری رضی اللہ عنہ تھے۔)'):'Source-printed identity of the other participant; separate same-family identifying voice.',
    ('2161','ur-Latn',"(Dusre shakhs Abu Musa Ash'ari (Radi Allahu Anhu) the.)"):'Source-printed identification in the independently read Roman field.',
    ('2180','hi','(तक़रीबन)'):'Meaningful approximation limiting the whole-month fasting phrase.',
    ('2180','ur','( تقریباً )'):'Meaningful approximation limiting the whole-month fasting phrase.',
    ('2220','ur','( عبادت )'):'Source-supplied comparison object within the reply.',
    ('2221','ur','( عبادت )'):'Source-supplied comparison object within the reply.',
    ('2223','ur','( عمل )'):'Source-supplied comparison object within the first reply.',
    ('2223','ur','( پھر )'):'Narrative sequence/repetition marker before the second request.'}
RETAINED_MARKER_WORDS={}
