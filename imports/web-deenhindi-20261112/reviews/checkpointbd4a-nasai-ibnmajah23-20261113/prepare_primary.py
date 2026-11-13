"""Serialize root's frozen readings into explicit per-field rules; no inferred reading."""
from pathlib import Path
import json,pprint
HERE=Path(__file__).resolve().parent
receipt=json.loads((HERE/'source-first-complete-reading.json').read_bytes())
WHO={
 'nasai:2387':('companion_question_and_prophetic_answer_with_wording_uncertainty','Abu Qatada reports Umar\'s questions and the supplied replies; the transmitter qualifies the actual negative variants'),
 'nasai:2389':('reported_family_encounter_and_fasting_dialogue','Mujahid transmits Abdullah ibn Amr\'s marriage/father/wife account and the ensuing fasting dialogue'),
 'nasai:2395':('companion_question_and_prophetic_answer','Abdullah ibn Amr reports his own fasting inquiry and the progressively supplied replies'),
 'nasai:2405':('prophetic_instruction_report','Abu Hurayra reports the three instructions addressed to him'),
 'nasai:2406':('prophetic_instruction_report','Abu Hurayra reports the three instructions addressed to him'),
 'nasai:2407':('prophetic_instruction_report','Abu Hurayra reports the three instructions addressed to him'),
 'nasai:2412':('transmission_pointer_only','Chain names and a similar/mursal pointer; no report-body speaker is supplied'),
 'nasai:2416':('companion_observation_of_prophetic_practice','Hafsa reports the four specified practices'),
 'nasai:2436':('companion_question_and_prophetic_answer','The source-named grandfather Muawiya ibn Hayda describes his own oaths and questions and the supplied replies'),
 'nasai:2438':('witnessed_sermon_and_companion_response','Abu Hurayra and Abu Said describe the sermon, their reaction and the supplied conditional promise'),
 'nasai:2447':('written_report_of_attributed_charity_duties','Anas reports Abu Bakr\'s letter giving the charity duties attributed in the source to the Prophet'),
 'nasai:2451':('commission_and_tax_instruction_report','Muadh ibn Jabal reports his Yemen commission and the supplied tax instructions'),
 'nasai:2452':('commission_and_tax_instruction_report','Muadh ibn Jabal reports his Yemen commission and the instructions actually supplied in each field'),
 'nasai:2453':('commission_and_tax_instruction_report','Muadh ibn Jabal reports the Yemen instruction with its negative threshold and age/sex conditions'),
 'nasai:2455':('written_report_of_attributed_charity_duties','Anas reports Abu Bakr\'s written charity schedule attributed in the source to the Prophet'),
 'nasai:2460':('reported_exchange_and_companion_retrospective','Jarir reports the villagers\' exchange and then his own later conduct'),
 'ibnmajah:2389':('reported_gift_and_permission_inquiry','Khayra, described as Kaab ibn Malik\'s wife, reports the jewelry offering, permission inquiries and each field\'s actual conclusion'),
 'ibnmajah:2392':('companion_transaction_and_prophetic_reply','The source-named Abdullah ibn Abbas reports the donated horse, proposed purchase and supplied prohibition'),
 'ibnmajah:2396':('companion_endowment_and_prophetic_instruction','Ibn Umar reports Umar\'s Khaybar consultation, instruction, endowment and its supplied limits'),
 'ibnmajah:2428':('reported_debt_encounter_and_prophetic_reply','Harmas/Harames ibn Habib transmits through his father the unnamed grandfather\'s actual debt encounter'),
 'ibnmajah:2437':('companion_report_of_prophetic_transaction','Anas reports the armor pledge and household barley purchase'),
 'ibnmajah:2444':('witnessed_recitation_and_prophetic_statement','Utba ibn Nadr reports the group\'s presence, named recitation and the supplied eight-or-ten-year statement'),
 'ibnmajah:2448':('anonymous_companion_work_and_food_account','Abu Hurayra reports the anonymous Ansari\'s inquiry, irrigation agreement, conditions and return')
}
SPECS={}
for key,(kind,who) in WHO.items():
 fields=[f for f in receipt['fields'] if f['id']=='deenhindi-'+key]
 only=key=='nasai:2412'
 SPECS[key]={'id':key,'decision':'exclude' if only else 'register','languages':[] if only else ['hi','ur'],
  'read_languages':[f['language'] for f in fields], 'field_notes':{f['language']:f['reading_note'] for f in fields},
  'shared_report_family':True,'report_type':kind,'speaker':who,
  'reason':('All five supplied fields were read in full and contain only chain/name/similar/mursal apparatus; no actual report body is supplied.' if only else 'Actual finite content supplied in this complete source field, classified by its own speaker and exact wording. No omitted body, neighboring identity, external numbering or sibling translation is used to fill it.')}

SPECS['nasai:2387']['components']={
 'hi':[
  {'stop_before':'(रावी को शक है','report_type':'reported_fasting_question_and_answer','speaker':'Umar asks and the Prophet answers within Abu Qatada\'s report'},
  {'start_at':'(रावी को शक है','stop_before':', उन्होंने अर्ज़ किया: अल्लाह के रसूल! उस शख्स का मामला कैसा है जो दो दिन','report_type':'qualified_actual_wording_variants','speaker':'The transmitter expresses uncertainty between the two actually supplied negative formulations'},
  {'start_at':', उन्होंने अर्ज़ किया: अल्लाह के रसूल! उस शख्स का मामला कैसा है जो दो दिन','report_type':'continued_fasting_questions_and_answers','speaker':'Umar continues the questions and the Prophet gives the supplied replies'}],
 'ur':[
  {'stop_before':'( راوی کو شک ہے','report_type':'reported_fasting_question_and_answer','speaker':'Umar asks and the Prophet answers within Abu Qatada\'s report'},
  {'start_at':'( راوی کو شک ہے','stop_before':', انہوں نے عرض کیا: اللہ کے رسول! اس شخص کا معاملہ کیسا ہے جو دو دن','report_type':'qualified_actual_wording_variants','speaker':'The transmitter expresses uncertainty between the two actually supplied negative formulations'},
  {'start_at':', انہوں نے عرض کیا: اللہ کے رسول! اس شخص کا معاملہ کیسا ہے جو دو دن','report_type':'continued_fasting_questions_and_answers','speaker':'Umar continues the questions and the Prophet gives the supplied replies'}]}
# The actual Urdu separator is an Arabic comma, not an inferred punctuation edit.
for c in SPECS['nasai:2387']['components']['ur']:
 for k in ['start_at','stop_before']:
  if c.get(k,'').startswith(', انہوں'):c[k]='،'+c[k][1:]
SPECS['nasai:2387']['annotations']={l:'The source leaves the uncertainty parenthesis unclosed. All later dialogue remains independently bounded and exact; no closing mark or preferred variant is invented.' for l in ['hi','ur']}
SPECS['nasai:2405']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2406']['exclude_substrings']={'hi':['(चश्त की नमाज़)'],'ur':['( چاشت کی نماز )']}
SPECS['nasai:2416']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2438']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2438']['annotations']={l:'The Hindi source prints सातों कबाइल, while Urdu prints ساتوں کبائر. Each original word is retained; no silent repair or clause-equivalence claim is made.' for l in ['hi','ur']}
SPECS['nasai:2447']['components']={'hi':[
 {'stop_before':' (इस में ऊँटों','report_type':'written_report_introduction','speaker':'Anas reports Abu Bakr\'s letter and its attributed authority'},
 {'start_at':'ज़कात में कोई बूढ़ा','report_type':'supplied_later_written_rules','speaker':'The actual animal/property conditions supplied after an explicit omission pointer in the same written report'}]}
SPECS['nasai:2447']['exclude_substrings']={'ur':['( یعنی زکاۃ وصول کرنے والا )','۱؎','۲؎']}
SPECS['nasai:2447']['annotations']={
 'hi':'The entire camel/sheep schedule is explicitly summarized rather than supplied here. The actual opening and later rules remain, without any Urdu schedule being inserted.',
 'ur':'All supplied thresholds, substitutions, payment directions, recipient/sex/breeding/missing-age conditions and no-additional-payment exception remain exact, including their parenthetic source rendering. Only the tax-collector lexical definition and literal footnote pointers are context.'}
SPECS['nasai:2452']['exclude_substrings']={'hi':['दो साल की बछिया.']}
SPECS['nasai:2452']['annotations']={'hi':'The unattached two-year-heifer nominal fragment lacks its threshold/predicate and remains visible context; the actual thirty/one-year and adult payment clauses are retained. Urdu\'s forty threshold is not inserted.'}
SPECS['nasai:2455']['exclude_substrings']={'hi':['(ज़कात)','...'],'ur':['( زکاۃ )','۱؎']}
SPECS['nasai:2455']['annotations']={l:'The source compensation wording has a damaged two-goat/twenty-dirham join. Its exact supplied words remain without a missing OR being invented. All numeric representations and material parenthetic scope remain.' for l in ['hi','ur']}
SPECS['nasai:2460']['components']={
 'hi':[{'stop_before':'जरीर (रज़ियल्लाहु अन्हु) कहते हैं:','report_type':'reported_villager_exchange','speaker':'Jarir reports the villagers\' questions and the supplied replies'},
       {'start_at':'जरीर (रज़ियल्लाहु अन्हु) कहते हैं:','report_type':'companion_retrospective_conduct','speaker':'Jarir describes his own later conduct since hearing the exchange'}],
 'ur':[{'stop_before':'جریر رضی اللہ عنہ کہتے ہیں:','report_type':'reported_villager_exchange','speaker':'Jarir reports the villagers\' questions and the supplied replies'},
       {'start_at':'جریر رضی اللہ عنہ کہتے ہیں:','report_type':'companion_retrospective_conduct','speaker':'Jarir describes his own later conduct since hearing the exchange'}]}
SPECS['nasai:2460']['annotations']={'hi':'The field omits an explicit actor before one honorific and damages the first follow-up question join. Source words and every condition/repeated reply are preserved without borrowing Urdu.'}
SPECS['ibnmajah:2389']['annotations']={'hi':'The source ends at the husband\'s affirmative permission answer. The acceptance event present only in Urdu is not added to Hindi.'}
SPECS['ibnmajah:2392']['annotations']={l:'The visible source names Abdullah ibn Abbas; no substitution from a familiar parallel or external numbering is made.' for l in ['hi','ur']}
SPECS['ibnmajah:2396']['annotations']={l:'The source parenthesis identifies fruits/profits as the donated object, distinguishing it from the retained corpus. It is preserved as supplied translation scope without a literal-direct-speech assertion.' for l in ['hi','ur']}
SPECS['ibnmajah:2444']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2395']['annotations']={'hi':'The first reward clause is absent and the first answer-to-narrator transition is damaged. The actual remaining numbers and statements are preserved, with no Urdu filling.'}

assert len(SPECS)==23 and sum(len(s['read_languages']) for s in SPECS.values())==49
(HERE/'manual_rules.py').write_text('"""Explicit rules made only after complete frozen primary readings."""\nSPECS = '+pprint.pformat(SPECS,width=115,sort_dicts=True)+'\n')

source=(HERE.parent/'phase16-checkpoint5589-nasai-ibnmajah25-review/build_delivery.py').read_text()
replacements={
 'Nasai22/IbnMajah3':'Nasai16/IbnMajah7',
 'checkpoint5589-nasai-ibnmajah25':'checkpointbd4a-nasai-ibnmajah23',
 '5589a3ffc3b43c3324ae26f2b6c4d33152834456':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633',
 'c9af6dfbbee05702c2d1fe518e8a008d1a3c5e609c95dccf7b5ec09f4bf4a754':'e215153fe6a482802e61087a97201a6faf76dd973ec9cca5c1def72515b9abcd',
 'phase15-successor-acquisition-monitor/held-evidence':'phase16-successor-acquisition-monitor/held-evidence',
 "default=HERE / 'delivery-manifest.json'":"default=HERE / 'delivery-manifest-v1.json'",
 'len(specifications) == 25':'len(specifications) == 23',
 "{'nasai':22,'ibnmajah':3}":"{'nasai':16,'ibnmajah':7}",
 '7d95645364e9fe42cdb5a13b8124ed72808f251526b841bb67f7c656c9d1e032':'7e94a6c162fb033a10a59d6d1d945f37bb2727ee6a2b90027788c39e4e0f623b',
 '(50,17084,36958)':'(49,29579,61743)',
 'len(own_fields) == 50':'len(own_fields) == 49',
 'Nasai16/IbnMajah7 at checkpoint5589. All50 Hindi/Urdu fields were fully read before candidate creation; all25 contain finite supplied reports. Hafsa, Ibn Abbas and Ata retain their distinct source voices. Meaningful conditions and qualifications remain. Biographical, lexical and omission apparatus stays in lossless context. All75 other language fields remain explicitly unread context.':'Nasai16/IbnMajah7 at checkpointbd4a. All46 Hindi/Urdu fields and all3 other Nasai2412 siblings were read completely before candidate creation.22 parents contain actual supplied finite reports; Nasai2412 is source-only after allfive fields were read. Material conditions, quantities, alternative wordings and speaker qualifications remain. Lexical and omission apparatus stays in lossless context. All66 other sibling fields remain explicitly unread.',
 'passed for all25':'passed for all23',
 '== (25, 0)':'== (22, 1)',
 '== (50, 50, 0, 75)':'== (49, 44, 5, 66)',
 '== (17084, 36958)':'== (29579, 61743)',
 'partitions == 125':'partitions == 115',
 'len(apparatus_rows) == 50':'len(apparatus_rows) == 44',
 'All50 admitted fields':'All44 admitted fields',
 "'build_delivery.py','freeze_source_reading.py','assemble_primary.py'":"'build_delivery.py','freeze_source_first.py','prepare_primary.py'",
}
for a,b in replacements.items():
 assert a in source,a
 source=source.replace(a,b)
(HERE/'build_delivery.py').write_text(source)
print('Prepared explicit23-record specifications and phase18 serializer from frozen49-field receipt.')
