"""Build explicit phase19 rules from the frozen40 actual full-field readings."""
from pathlib import Path
import hashlib,json,pprint
HERE=Path(__file__).resolve().parent
rb=(HERE/'source-first-complete-reading.json').read_bytes()
assert hashlib.sha256(rb).hexdigest()=='dafc871d2b94e2976220e2a11309c15a3c550a1e4cc6bf4d5f217cb23ab9fe70'
receipt=json.loads(rb)
WHO={
 'nasai:2465':('abbreviated_finite_command_report','Abu Hurayra reports the actual zakat command before an omitted-body pointer'),
 'nasai:2480':('abbreviated_reported_encounter','Amr ibn Shuayb reports the woman and daughter arriving with two bracelets; the unprovided sequel is not reconstructed'),
 'nasai:2490':('commission_and_tax_instruction_report','Muadh reports the Yemen commission and the actual irrigation/rate conditions supplied in each field'),
 'nasai:2492':('actual_prohibition_after_lexical_apparatus','The source separately attributes a prohibition of bad-property collection to the Prophet after its lexical discussion'),
 'nasai:2500':('reported_command_and_later_determination','Ibn Umar reports the command and a later wheat determination; the Hindi latter actor is unresolved'),
 'nasai:2501':('reported_command_and_community_determination','Ibn Umar reports the command and the people\'s later wheat-equivalence determination'),
 'nasai:2502':('prophetic_instruction_report','Ibn Umar reports the complete supplied participant scope and payment alternatives'),
 'nasai:2504':('prophetic_instruction_report','Ibn Umar reports the Muslim participant scope, payment alternatives and the specified departure deadline'),
 'nasai:2505':('prophetic_instruction_report','Ibn Umar reports the participant categories and amount/food alternatives actually supplied here'),
 'nasai:2511':('prophetic_instruction_report','Abu Said reports the supplied amount and three food alternatives'),
 'nasai:2532':('witnessed_sermon_and_prophetic_instruction','Tariq reports the Medina arrival, minbar sermon and complete family-priority statement'),
 'nasai:2537':('reported_master_worker_encounter_and_reply','Umayr reports his own feeding/appeal account, the master\'s explanation and the supplied reward-to-both reply'),
 'nasai:2540':('witnessed_speech_and_prophetic_statement','Abdullah ibn Amr reports the Mecca-conquest speech and its actual permission-condition statement'),
 'ibnmajah:2455':('actual_prohibition_before_lexical_apparatus','Abu Said transmits the actual muhaqala prohibition; the following definition is not selected'),
 'ibnmajah:2469':('companion_report_of_prophetic_transaction','Anas reports the Khaybar-conquest half-produce transaction'),
 'ibnmajah:2474':('companion_question_and_prophetic_answer','Aisha reports her questions and all actual conditional comparisons in the supplied replies'),
 'ibnmajah:2477':('prophetic_prohibition_report','Jabir reports the supplied water-sale prohibition without replacement wording'),
 'ibnmajah:2481':('prophetic_judgment_report','Thalaba ibn Abi Malik reports the Mahzur-channel judgment with its complete sequence and limits'),
 'ibnmajah:2496':('companion_question_and_prophetic_answer','Shurayd reports the complete property question and the supplied proximity reply'),
 'ibnmajah:2497':('prophetic_judgment_report','Abu Hurayra reports the undivided-property rule and its division-and-boundary exception')
}
SPECS={}
for key,(kind,who) in WHO.items():
 fs=[f for f in receipt['fields'] if f['id']=='deenhindi-'+key]
 SPECS[key]={'id':key,'decision':'register','languages':['hi','ur'],'read_languages':['hi','ur'],'field_notes':{f['language']:f['reading_note'] for f in fs},'shared_report_family':True,'report_type':kind,'speaker':who,'reason':'Actual finite content supplied in this complete source field, attributed only to its visible source voice. No omitted body, identity, canonical mapping or sibling translation is inserted.'}
SPECS['nasai:2465']['stop_before']={'hi':' ऊपर वाली रिवायात','ur':'، آگے کی اوپر والی'}
SPECS['nasai:2480']['stop_before']={'hi':', आगे इसी तरह','ur':'، آگے اسی طرح'}
SPECS['nasai:2490']['annotations']={'hi':'The bucket-water subject and connecting phrase are absent in Hindi. The surviving parenthetic irrigation condition and one-twentieth statement remain exact, without Urdu filling.'}
SPECS['nasai:2492']['start_at']={'hi':'रसूलुल्लाह (सल्लल्लाहु अलैहि वसल्लम) ने ज़कात','ur':'رسول اللہ صلی اللہ علیہ وسلم نے زکاۃ'}
SPECS['nasai:2492']['annotations']={l:'The opening verse quotation/rendering is embedded in a lexical explanation of two date-type terms. It remains source context; only the separately supplied actual prohibition is selected.' for l in ['hi','ur']}
SPECS['nasai:2500']['components']={
 'hi':[{'stop_before':"निस्फ़ सा'आ गेहूं",'report_type':'prophetic_payment_instruction','speaker':'Ibn Umar reports the actual command; the source participant list is visibly incomplete'},
       {'start_at':"निस्फ़ सा'आ गेहूं",'report_type':'finite_determination_with_unresolved_actor','speaker':'The Hindi supplies a later half-sa wheat determination without its actor/equivalence link; no actor is borrowed from Urdu'}],
 'ur':[{'stop_before':'پھر اس کے برابر لوگوں','report_type':'prophetic_payment_instruction','speaker':'Ibn Umar reports the actual Prophetic command and complete supplied participant list'},
       {'start_at':'پھر اس کے برابر لوگوں','report_type':'subsequent_community_determination','speaker':'The source expressly attributes the later half-sa wheat equivalence to people, not the Prophet'}]}
SPECS['nasai:2500']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2500']['annotations']={'hi':'The incomplete participant list and absent later actor/equivalence link are preserved without adding Urdu words. The later finite determination is kept under unresolved attribution; the fitr parenthesis supplies the payment category.'}
SPECS['nasai:2501']['components']={l:[
 {'stop_before':marker,'report_type':'prophetic_payment_instruction','speaker':'Ibn Umar reports the command with its exact scope and amount'},
 {'start_at':marker,'report_type':'subsequent_community_determination','speaker':'The source people make the later wheat-equivalence determination; this is not a new Prophetic command'}]
 for l,marker in [('hi','फिर लोगों ने'),('ur','پھر لوگوں نے')]}
SPECS['nasai:2504']['annotations']={l:'The parenthetic Eid-prayer and from-home phrases materially identify the supplied temporal boundary. They remain as exact source-rendered qualifications without a literal-direct-speech claim.' for l in ['hi','ur']}
SPECS['nasai:2532']['stop_before']={'hi':'Yeh hadith ek lambi hadith ka ikhtisar hai.','ur':'یہ حدیث ایک لمبی حدیث کا اختصار ہے۔'}
SPECS['nasai:2537']['exclude_between']={'hi':[('Aur dusri baar raawi ne kaha:','toh aap ne farmaya:')],'ur':[('اور دوسری بار راوی نے کہا:','تو آپ نے فرمایا:')]}
SPECS['nasai:2537']['annotations']={l:'Only the explicitly marked narrator\'s second-time equivalent wording is kept as context. The actual preceding master\'s explanation, recipient qualification and ensuing reward-to-both reply remain selected.' for l in ['hi','ur']}
SPECS['nasai:2540']['stop_before']={'ur':'، یہ حدیث مختصر ہے۔'}
SPECS['nasai:2540']['exclude_substrings']={'ur':['( منجملہ اور باتوں کے )']}
for key in ['nasai:2532','nasai:2537','nasai:2540']:
 SPECS[key]['observed_scripts']={'hi':'Latn'}
 SPECS[key]['script_notes']={'hi':'The provider labels this field translationHindi, but its complete saved body is Roman Urdu in Latin script. Preserve the source language/version identity and exact original text; record observed script Latn rather than inventing a Hindi translation.'}
SPECS['ibnmajah:2455']['stop_before']={'hi':' और मुहकला ज़मीन','ur':'، اور محاقلہ زمین'}
SPECS['ibnmajah:2474']['exclude_substrings']={'ur':['۱؎']}
SPECS['ibnmajah:2477']['exclude_substrings']={'hi':['(एक्स्ट्रा)'],'ur':['۱؎']}
SPECS['ibnmajah:2477']['annotations']={'hi':'The source prints ज़ैद and supplies a parenthetic English extra gloss. The original spelling remains unchanged and the lexical gloss stays visible context; no replacement is borrowed from Urdu.'}
SPECS['ibnmajah:2481']['exclude_substrings']={'hi':['(तराई)'],'ur':['( ترائی )','۱؎']}
assert len(SPECS)==20 and sum(len(s['read_languages']) for s in SPECS.values())==40
(HERE/'manual_rules.py').write_text('"""Explicit source-bound rules frozen after complete primary readings."""\nSPECS = '+pprint.pformat(SPECS,width=115,sort_dicts=True)+'\n')
source=(HERE.parent/'phase18-checkpointbd4a-nasai-ibnmajah23-review/build_delivery.py').read_text()
replacements={
 'Nasai16/IbnMajah7':'Nasai13/IbnMajah7',
 'checkpointbd4a-nasai-ibnmajah23':'checkpoint3e574-nasai-ibnmajah20',
 'bd4a75695d3c695e98bf8efa5ce07764ac5e2633':'3e574b9e7e4dd7cf8bc23232249004a18692c61c',
 'e215153fe6a482802e61087a97201a6faf76dd973ec9cca5c1def72515b9abcd':'0c794e514bcbebcda174dab501a3139963bda68b636a5a3b1049db0ce93f9a15',
 'phase16-successor-acquisition-monitor/held-evidence':'phase18-successor-acquisition-monitor/held-evidence',
 'len(specifications) == 23':'len(specifications) == 20',
 "{'nasai':16,'ibnmajah':7}":"{'nasai':13,'ibnmajah':7}",
 '7e94a6c162fb033a10a59d6d1d945f37bb2727ee6a2b90027788c39e4e0f623b':'dafc871d2b94e2976220e2a11309c15a3c550a1e4cc6bf4d5f217cb23ab9fe70',
 '(49,29579,61743)':'(40,10697,21245)',
 'len(own_fields) == 49':'len(own_fields) == 40',
 'Nasai13/IbnMajah7 at checkpointbd4a. All46 Hindi/Urdu fields and all3 other Nasai2412 siblings were read completely before candidate creation.22 parents contain actual supplied finite reports; Nasai2412 is source-only after allfive fields were read. Material conditions, quantities, alternative wordings and speaker qualifications remain. Lexical and omission apparatus stays in lossless context. All66 other sibling fields remain explicitly unread.':'Nasai13/IbnMajah7 at checkpoint3e574. All40 Hindi-labelled/Urdu fields were read completely before candidate creation; all20 parents contain actual supplied finite content. Three Hindi-labelled fields visibly contain Latin-script Roman Urdu and receive only explicit script metadata correction, with source identities/text preserved.58 nonempty siblings remain unread and2 original source slots remain exactly empty. All material scope, quantities and actor distinctions remain; lexical/omission/equivalent-wording apparatus stays in lossless context.',
 'passed for all23':'passed for all20',
 '== (22, 1)':'== (20, 0)',
 '== (49, 44, 5, 66)':'== (40, 40, 0, 58)',
 '== (29579, 61743)':'== (10697, 21245)',
 'partitions == 115':'partitions == 98',
 'len(script_corrections) == 0':'len(script_corrections) == 3',
 'len(apparatus_rows) == 44':'len(apparatus_rows) == 40',
 'All44 admitted fields':'All40 admitted fields',
 "assert isinstance(text, str) and text, (identity, field)":"""assert isinstance(text, str), (identity, field)
            if not text:
                assert language not in rules['read_languages'] and language not in rules['languages']
                coverage_row['fields'].append({'language':language,'source_field':field,'text_sha256':sha(b''),'text_chars':0,'text_bytes':0,'field_reviewed':False,'chars_reviewed':0,'bytes_reviewed':0,'status':'empty_source_field','reading_note':'Original source value is exactly an empty string; no semantic reading or admission is claimed.','boundary_reason':'Preserve original empty slot; no invented text.','selected_spans':[]})
                continue""",
 "assert len(original['language_versions']) == len(revised['language_versions']) == 5":"assert len(original['language_versions']) == len(revised['language_versions']) == sum(bool(saved['source_record'][f]) for f in FIELDS.values())",
 "'nonempty_source_fields': len(all_fields),":"'nonempty_source_fields': sum(f['text_chars'] > 0 for f in all_fields),\n        'exact_empty_source_fields': sum(f['status'] == 'empty_source_field' for f in all_fields),",
 "assert len(script_corrections) == 3":"assert len(script_corrections) == 3\n    assert (stats['source_field_slots'],stats['nonempty_source_fields'],stats['exact_empty_source_fields']) == (100,98,2)",
}
for a,b in replacements.items():
 assert a in source,a
 source=source.replace(a,b)
(HERE/'build_delivery.py').write_text(source)
print('Prepared20 explicit records;40 read fields,58 unread siblings,2 exact empties and3 observed-script corrections.')
