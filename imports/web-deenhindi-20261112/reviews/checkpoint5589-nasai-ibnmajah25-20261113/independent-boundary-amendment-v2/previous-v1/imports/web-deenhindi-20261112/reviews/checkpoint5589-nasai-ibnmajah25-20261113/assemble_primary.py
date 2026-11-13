"""Serialize the root reviewer's explicit, previously read field decisions."""
from pathlib import Path
import json, pprint

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
reading=json.loads((ROOT/'source-first-complete-reading.json').read_bytes())
notes={(r['id'].removeprefix('deenhindi-'),r['language']):r['reading_note'] for r in reading['fields']}
voices={
 'ibnmajah:2355':('historical_account_and_prophetic_transaction_instruction','Muhammad ibn Yahya ibn Habban reporting his grandfather Munqidh and the supplied Prophetic instruction'),
 'ibnmajah:2360':('historical_inquiry_and_reported_prophetic_judgment','Ibn Khalda reporting the inquiry to Abu Hurayra and Abu Hurayra reporting the supplied judgment'),
 'ibnmajah:2370':('prophetic_judgment_report','Abdullah ibn Abbas reporting the supplied one-witness and claimant-oath judgment'),
 'nasai:2300':('companion_question_and_prophetic_answer','Hamza ibn Amr reporting his own practice, question and the supplied answer'),
 'nasai:2301':('companion_question_and_prophetic_answer','Hamza ibn Amr reporting his own habitual fasting, question and the supplied answer'),
 'nasai:2303':('companion_question_and_prophetic_answer','Hamza ibn Amr reporting the conditional question and the supplied answer'),
 'nasai:2305':('companion_question_and_prophetic_answer','Hamza ibn Amr reporting his own question and the source-supplied answer'),
 'nasai:2310':('companion_collective_travel_practice_report','Abu Said al-Khudri reporting shared travel, mixed fasting practice and mutual non-reproach'),
 'nasai:2311':('companion_collective_travel_practice_report','Jabir reporting a journey with the Prophet and the companions mixed fasting practice'),
 'nasai:2314':('prophetic_travel_practice_and_companion_conclusion','Ibn Abbas describing the Prophet travel practice and his own concluding choice'),
 'nasai:2322':('prophetic_practice_dialogue_and_analogy_report','Aisha reporting the two encounters, actual eating and supplied analogy'),
 'nasai:2323':('prophetic_practice_dialogue_and_analogy_report','Aisha reporting the two encounters, her question and the qualified answer'),
 'nasai:2325':('prophetic_practice_and_dialogue_report','Aisha reporting the visit, offered share, fasting declaration and subsequent breaking of the fast'),
 'nasai:2327':('prophetic_dialogue_report','Aisha reporting the food inquiry and fasting declaration'),
 'nasai:2330':('prophetic_practice_and_dialogue_report','Aisha reporting the two encounters and the actual intention qualification'),
 'nasai:2336':('companion_statement','Hafsa as transmitted by Ibn Umar; no direct Prophetic attribution is supplied in these fields'),
 'nasai:2348':('companion_qualified_observation_of_prophetic_practice','Aisha stating her own limited knowledge about the three described practices'),
 'nasai:2349':('historical_inquiry_and_companion_observation','Ibn Shaqiq reporting his question and Aisha describing the Prophet practice with temporal limits'),
 'nasai:2354':('companion_report_of_prophetic_practice','Aisha reporting the Shaban fasting comparison with the supplied whole-or-most qualification'),
 'nasai:2357':('companion_question_and_prophetic_answer','Usama ibn Zayd reporting his observation and the supplied answer about Shaban'),
 'nasai:2358':('companion_question_and_prophetic_answer','Usama ibn Zayd reporting the practice patterns, two days and supplied explanation'),
 'nasai:2369':('prophetic_instruction_report','Abu Hurayra reporting the three instructions addressed to him'),
 'nasai:2370':('companion_qualified_observation_of_prophetic_practice','Ibn Abbas answering the Ashura question under his stated knowledge limitation'),
 'nasai:2378':('abbreviated_event_and_qualified_transmitted_wording','Abdullah ibn Amr reports the opening event; Ata reports qualified remembered wording through Ibn Jurayj'),
 'nasai:2379':('anonymous_question_and_prophetic_answer','Imran ibn Husayn reporting an anonymous question about an unnamed person and the supplied answer'),
}
SPECS={}
for key,(report_type,speaker) in voices.items():
    SPECS[key]={'id':key,'decision':'register','report_type':report_type,'speaker':speaker,
       'reason':'Actual supplied finite report or saying, classified by its own source voice and exact wording. No absent body, missing identity, canonical numbering or translated sibling is used to fill this field.',
       'read_languages':['hi','ur'],'languages':['hi','ur'],'shared_report_family':True,
       'field_notes':{lang:notes[key,lang] for lang in ['hi','ur']}}
SPECS['ibnmajah:2355']['stop_before']={'ur':' ۱؎'}
SPECS['ibnmajah:2360']['exclude_substrings']={'hi':['(वो मदीना के क़ाज़ी थे)'],'ur':['(وہ مدینہ کے قاضی تھے)']}
SPECS['nasai:2305']['annotations']={'hi':'The supplied Hindi answer has a compressed/damaged two-choice construction. Its printed words are retained without inserting Urdu wording or a missing conjunction.'}
SPECS['nasai:2314']['components']={}
for lang,marker in [('hi','अब्दुल्लाह बिन अब्बास (रज़ियल्लाहु अन्हुमा) कहते हैं:'),('ur','عبداللہ بن عباس رضی اللہ عنہما کہتے ہیں:')]:
    SPECS['nasai:2314']['components'][lang]=[
       {'stop_before':marker,'report_type':'prophetic_travel_practice_report','speaker':'Ibn Abbas reporting the journey, daytime drinking and Ramadan conquest'},
       {'start_at':marker,'report_type':'companion_conclusion_from_reported_practice','speaker':'Ibn Abbas giving his own concluding fasting option; not a direct Prophetic utterance'}]
SPECS['nasai:2322']['exclude_substrings']={'hi':['(मगर खाऊँगा)'],'ur':['۱؎','( مگر کھاؤ گا )']}
SPECS['nasai:2323']['stop_before']={'ur':' ۱؎'}
SPECS['nasai:2330']['exclude_substrings']={'hi':['(एक क़िस्म का खाना)']}
SPECS['nasai:2349']['exclude_substrings']={'hi':['(रोज़ा ना रहते)'],'ur':['( روزہ نہ رہتے )']}
SPECS['nasai:2370']['annotations']={lang:'The source mixes a singular day reference with Ramadan and Ashura. Preserve its own awkward wording, explicit exceptions and Ibn Abbas knowledge limitation; do not harmonize the formulation.' for lang in ['hi','ur']}
SPECS['nasai:2378']['exclude_substrings']={'hi':['(रोज़े)'],'ur':['( روزے )']}
SPECS['nasai:2378']['components']={}
for lang,stop,start in [('hi',', और रावी ने पूरी हदीस बयान की।','इब्न जुरैज कहते हैं'),('ur','، اور راوی نے پوری حدیث بیان کی۔','ابن جریج کہتے ہیں')]:
    SPECS['nasai:2378']['components'][lang]=[
        {'stop_before':stop,'report_type':'abbreviated_reported_event','speaker':'Abdullah ibn Amr reporting that the Prophet was informed of his repeated fasting'},
        {'start_at':start,'report_type':'qualified_remembered_wording_fragment','speaker':'Ata, transmitted by Ibn Jurayj, states a memory limitation and actual remembered wording; its internal pronoun antecedent is not independently supplied'}]
SPECS['nasai:2378']['annotations']={lang:'The source explicitly omits an intervening full hadith. The opening event and later qualified remembered wording are two ordered supplied components in one family. Missing intervening content and the final internal speaker are not reconstructed.' for lang in ['hi','ur']}
rules=('"""Explicit source-bound decisions after the complete root source-first reading."""\nSPECS = '+pprint.pformat(SPECS,sort_dicts=True,width=120)+'\n').encode()
rules_path=ROOT/'manual_rules.py'
assert not rules_path.exists(), 'Frozen specifications must be versioned rather than replaced.'
rules_path.write_bytes(rules)
source=(WORK/'phase15-checkpoint0639-nasai-ibnmajah28-review/build_delivery.py').read_text()
replacements={
 'Nasai19/IbnMajah9':'Nasai22/IbnMajah3',
 'checkpoint0639-nasai-ibnmajah28-20261113':'checkpoint5589-nasai-ibnmajah25-20261113',
 '0639af7fd15786284b4c413fced77e38eec8825a':'5589a3ffc3b43c3324ae26f2b6c4d33152834456',
 '6107d315ac7bb26d0a42da2313fb211d70c2308041d277304350a25b7c59fb13':'c9af6dfbbee05702c2d1fe518e8a008d1a3c5e609c95dccf7b5ec09f4bf4a754',
 '9064df272f069bf281097820aca6aa4d52a5d4dad736e11663cf55ba5c9618c7':'7d95645364e9fe42cdb5a13b8124ed72808f251526b841bb67f7c656c9d1e032',
 'phase13-successor-acquisition-monitor/held-evidence':'phase15-successor-acquisition-monitor/held-evidence',
 "== 28":"== 25",
 "{'nasai':19,'ibnmajah':9}":"{'nasai':22,'ibnmajah':3}",
 '(65,20762,40583)':'(50,17084,36958)',
 'len(own_fields) == 65':'len(own_fields) == 50',
 "'scope': 'Nasai22/IbnMajah3 at checkpoint0639. All56 Hindi/Urdu fields were fully read, plus all3 other fields for each Nasai2259,2275,2295:65 actual full readings. Two occurrences contain no substantive report body in any supplied field. Every retained fragment is attributed only to its supplied voice. Three Hindi-labelled Latin transliterations receive script metadata corrections; every source character and language identity remains unchanged.'":"'scope': 'Nasai22/IbnMajah3 at checkpoint5589. All50 Hindi/Urdu fields were fully read before candidate creation; all25 contain finite supplied reports. Hafsa, Ibn Abbas and Ata retain their distinct source voices. Meaningful conditions and qualifications remain. Biographical, lexical and omission apparatus stays in lossless context. All75 other language fields remain explicitly unread context.'",
 'passed for all28':'passed for all25',
 '== (26, 2)':'== (25, 0)',
 '== (65, 55, 10, 75)':'== (50, 50, 0, 75)',
 '== (20762, 40583)':'== (17084, 36958)',
 'assert partitions == 140':'assert partitions == 125',
 'assert len(script_corrections) == 3':'assert len(script_corrections) == 0',
 'len(apparatus_rows) == 55':'len(apparatus_rows) == 50',
 'All55 admitted fields':'All50 admitted fields',
 "'build_delivery.py']":"'build_delivery.py','freeze_source_reading.py','assemble_primary.py']",
}
for before,after in replacements.items():
    assert before in source, before
    source=source.replace(before,after)
build=ROOT/'build_delivery.py'
assert not build.exists()
build.write_text(source)
print('Prepared explicit25-occurrence specifications and source-bound serializer; native validation has not yet run.')
