"""Author explicit decisions only after all32 original fields were actually read."""
from pathlib import Path
import hashlib,json,pprint
HERE=Path(__file__).resolve().parent
assert not (HERE/'delivery-manifest-v1.json').exists()
rb=(HERE/'source-first-complete-reading.json').read_bytes()
assert hashlib.sha256(rb).hexdigest()=='8d3f9b4f0321db8210ada007271ecad8691ebb9a48407fd4826fcfebe06790ca'
receipt=json.loads(rb)
WHO={
 'nasai:2553':('reported_prophetic_actions_with_explicit_transmitter_addition','Adi reports the actual actions; the explicitly introduced Shubah repetition count and ensuing exhortation keep their own source attribution'),
 'nasai:2568':('companion_questions_and_prophetic_replies','Muawiyah gives his actual oath/approach/self-description and questions, followed by the supplied replies and their exact scope'),
 'nasai:2574':('narrator_identification_and_actual_question_reply','The source identifies Umm Bujayd among the women who pledged, then gives her actual scarcity question and the supplied reply'),
 'nasai:2579':('companion_debt_question_and_qualified_reply','Qabisah reports assuming a debt and asking; the reply retains inability, until-paid and then-stop conditions'),
 'nasai:2619':('companion_report_of_sermon_question_and_conditional_reply','Abu Hurayrah reports the actual sermon, repeated question and complete conditional reply'),
 'nasai:2621':('qualified_companion_question_and_prophetic_reply','Abu Razin asks concerning his old father and receives the actual on-his-behalf Hajj-and-Umrah reply; each field keeps only its own supplied wording'),
 'ibnmajah:2554':('companion_historical_encounter_and_prophetic_reaction','Abu Hurayrah reports the Maiz encounter, all four confessions, historical actions and the actual final question'),
 'ibnmajah:2560':('actual_attributed_scholarly_dialogue_with_embedded_quote','Qasim supplies the setting, a separately named questioner quotes a conditional Prophetic statement, and Ibn Abbas gives his own reply'),
 'ibnmajah:2565':('joint_companion_encounter_with_qualified_historical_reply','The three source-named reporters give the actual question and reply with repeated-offence conditions and third-or-fourth uncertainty'),
 'ibnmajah:2571':('historical_scene_and_companion_comparison','The source-named reporter describes the actual Uthman/Ali scene; Ali then gives his own comparison of reported practices'),
 'ibnmajah:2578':('companion_historical_incident_with_attributed_instruction','Anas supplies the actual conditional instruction and subsequent historical acts; the account is not current medical or legal advice'),
 'ibnmajah:2579':('companion_historical_report','Aisha supplies this occurrence’s brief camel-attack report and stated ensuing acts, without imported neighbouring details'),
 'ibnmajah:2584':('companion_report_of_prophetic_action','Ibn Umar reports the shield-theft event with its exact three-dirham value'),
 'ibnmajah:2587':('actual_question_and_companion_reply_with_cited_action','Ibn Muhayriz asks Fudalah, who gives his own sunnah classification and cites the reported Prophetic action'),
 'ibnmajah:2607':('companion_encounter_and_reported_commission','Bara gives the uncle encounter and the uncle’s actual statement of an assigned task; the task is not asserted to have been completed'),
 'ibnmajah:2608':('companion_report_of_commission_and_purpose','Qurrah reports being sent with the stated purposes; no completed execution or collection is inferred')
}
SPECS={}
for key,(kind,voice) in WHO.items():
 fields=[f for f in receipt['fields'] if f['id']=='deenhindi-'+key]
 assert len(fields)==2
 SPECS[key]={'id':key,'decision':'register','languages':['hi','ur'],'read_languages':['hi','ur'],
 'field_notes':{f['language']:f['reading_note'] for f in fields},'shared_report_family':True,
 'report_type':kind,'speaker':voice,
 'reason':'Actual finite content supplied in this complete source field, attributed only to its visible source voice. No omitted body, missing identity, canonical mapping or sibling translation is inserted.'}

SPECS['nasai:2553']['components']={}
for lang,addition,exhortation in [('hi',"शु'बाह ने ज़िक्र किया",'आग से बचो'),('ur','شعبہ نے ذکر کیا','پھر فرمایا:')]:
 SPECS['nasai:2553']['components'][lang]=[
  {'stop_before':addition,'report_type':'companion_report_of_prophetic_actions','speaker':'Adi reports the actual mention of Hell, turning away and seeking refuge'},
  {'start_at':addition,'stop_before':exhortation,'report_type':'explicit_transmitter_addition_of_repetition_count','speaker':'The source explicitly introduces Shubah as giving the three-times repetition detail'},
  {'start_at':exhortation,'report_type':'source_abbreviated_exhortation_fragment' if lang=='hi' else 'explicit_prophetic_conditional_exhortation',
   'speaker':'The Hindi source continues with the actual exhortation after the transmitter count, without an explicit said bridge or the complete alternative condition; neither is supplied' if lang=='hi' else 'The Urdu source explicitly introduces the ensuing Prophetic exhortation and preserves its own if-unavailable alternative'}]
SPECS['nasai:2553']['annotations']={'hi':'The join after the three-times detail and the final alternative clause are abbreviated. No Urdu speech bridge, good-word wording or missing condition is inserted.','ur':'The supplied conditional alternative and printed typo remain exactly as saved, without spelling repair.'}
SPECS['nasai:2568']['exclude_substrings']={'ur':['۱؎','۲؎']}
SPECS['nasai:2568']['annotations']={l:'The still-understand-nothing parenthesis supplies the predicate for the following except-what-taught qualification within the actual self-description. The source’s awkward final negative/after-Islam/or wording remains unchanged; no doctrinal correction is supplied.' for l in ['hi','ur']}
SPECS['nasai:2574']['exclude_substrings']={'hi':['(खुरदा)']}
SPECS['nasai:2574']['annotations']={l:'The short source framing identifies the speaker through her actual pledge participation. The occasional-scenario parenthesis limits the actual question. Both remain qualified source narration; the Hindi duplicate hoof term alone is lexical context.' for l in ['hi','ur']}
SPECS['nasai:2579']['annotations']={l:'The inability-to-repay parenthesis materially limits permission to ask. Preserve the restriction to three categories but only the one case actually supplied, together with until-paid and then-stop limits.' for l in ['hi','ur']}
SPECS['nasai:2619']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2621']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2621']['annotations']={'hi':'The old-father question has a damaged predicate and omits part of the inability/Hajj wording. Keep its own finite fragment without borrowing Urdu’s missing clause; the actual reply remains exact.'}
SPECS['ibnmajah:2560']['components']={}
for lang,question,answer in [('hi','शद्दाद ने पुछा:','इब्न अब्बास (रज़ियल्लाहु अन्हुमा) ने कहा:'),('ur','تو ان سے ابن شداد نے پوچھا:','ابن عباس رضی اللہ عنہما نے کہا:')]:
 SPECS['ibnmajah:2560']['components'][lang]=[
  {'stop_before':question,'report_type':'actual_reported_scholarly_setting','speaker':'Qasim reports Ibn Abbas mentioning the two lian participants'},
  {'start_at':question,'stop_before':answer,'report_type':'actual_scholarly_question_with_embedded_prophetic_quote','speaker':'The questioner printed Shaddad in Hindi, or Ibn Shaddad in Urdu, asks the actual question that expressly cites the conditional Prophetic statement; each field keeps its own name'},
  {'start_at':answer,'report_type':'actual_companion_reply','speaker':'Ibn Abbas gives his own reply, not further words of the Prophet'}]
SPECS['ibnmajah:2560']['annotations']={'hi':'The questioner’s name and the damaged final descriptor remain as printed. Neither is repaired from Urdu or external identity.'}
SPECS['ibnmajah:2571']['components']={}
for lang,mark in [('hi','और कहा:'),('ur','اور کہا:')]:
 SPECS['ibnmajah:2571']['components'][lang]=[
  {'stop_before':mark,'report_type':'actual_historical_trial_and_action_scene','speaker':'The source-named reporter describes the testimony, Uthman’s request to Ali and the stated action, including the cousin relation'},
  {'start_at':mark,'report_type':'companion_comparison_of_cited_practices','speaker':'Ali supplies the forty/forty/eighty comparison and his own every-one-is-sunnah assessment; this is not all direct Prophetic speech'}]
SPECS['ibnmajah:2571']['exclude_substrings']={'ur':['۱؎']}
SPECS['ibnmajah:2578']['exclude_substrings']={'hi':['(मुर्तद हो गए)'],'ur':['( مرتد ہو گئے )','۱؎','۲؎','۳؎']}
SPECS['ibnmajah:2579']['exclude_substrings']={'ur':['۱؎']}
SPECS['ibnmajah:2587']['components']={}
for lang,mark in [('hi','उन्होंने कहा:'),('ur','انہوں نے کہا:')]:
 SPECS['ibnmajah:2587']['components'][lang]=[
  {'stop_before':mark,'report_type':'actual_attributed_question','speaker':'Ibn Muhayriz asks Fudalah the supplied question'},
  {'start_at':mark,'report_type':'companion_response_with_cited_prophetic_action','speaker':'Fudalah gives his sunnah assessment and reports the stated Prophetic act; the assessment is kept under his own voice'}]
SPECS['ibnmajah:2607']['exclude_substrings']={
 'hi':['(रवि-इ-हदीस हुशाइम ने उनके मामू का नाम हरिस बिन अम्र बताया)','(यानि अपनी सौतेली मां)'],
 'ur':['( راوی حدیث ہشیم نے ان کے ماموں کا نام حارث بن عمرو بتایا )','( یعنی اپنی سوتیلی ماں )']}
SPECS['ibnmajah:2607']['annotations']={'hi':'The question and final speech-subject join are abbreviated before the standalone honorific. No Urdu wording is inserted. Transmitter-name apparatus and the duplicate stepmother gloss remain context; the actual after-father’s-death condition, father’s-wife relation and stated commission stay exact.'}
SPECS['ibnmajah:2608']['exclude_substrings']={'ur':['۱؎']}
assert len(SPECS)==16 and sum(len(s['read_languages']) for s in SPECS.values())==32
(HERE/'manual_rules.py').write_text('"""Explicit source-bound decisions after the frozen32-field original pass."""\nSPECS = '+pprint.pformat(SPECS,width=115,sort_dicts=True)+'\n')
source=(HERE.parent/'phase19-checkpoint3e574-nasai-ibnmajah20-review/build_delivery.py').read_text()
old_scope='Nasai13/IbnMajah7 at checkpoint3e574. All40 Hindi-labelled/Urdu fields were read completely before candidate creation; all20 parents contain actual supplied finite content. Three Hindi-labelled fields visibly contain Latin-script Roman Urdu and receive only explicit script metadata correction, with source identities/text preserved.58 nonempty siblings remain unread and2 original source slots remain exactly empty. All material scope, quantities and actor distinctions remain; lexical/omission/equivalent-wording apparatus stays in lossless context.'
new_scope='Nasai6/IbnMajah10 at checkpoint0d2fa. All32 complete Hindi and Urdu originals were read before candidate creation; all16 parents contain actual supplied finite content. All48 other nonempty sibling fields remain unread. Every source slot and metadata value is preserved; actual voices, quantities, conditions and damaged wording are distinguished from exact lexical, locator and transmitter apparatus. No observed-script correction or source-only parent is proposed.'
replacements=[
 (old_scope,new_scope),('Nasai13/IbnMajah7','Nasai6/IbnMajah10'),
 ('checkpoint3e574-nasai-ibnmajah20','checkpoint0d2fa-nasai-ibnmajah16'),
 ('3e574b9e7e4dd7cf8bc23232249004a18692c61c','0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a'),
 ('0c794e514bcbebcda174dab501a3139963bda68b636a5a3b1049db0ce93f9a15','639e2cf5033c7f1d637689c511c8709165a1cd62cf561d811e3d8522bbb365d9'),
 ('phase18-successor-acquisition-monitor/held-evidence','phase19-successor-acquisition-monitor/held-evidence'),
 ('len(specifications) == 20','len(specifications) == 16'),("{'nasai':13,'ibnmajah':7}","{'nasai':6,'ibnmajah':10}"),
 ('dafc871d2b94e2976220e2a11309c15a3c550a1e4cc6bf4d5f217cb23ab9fe70','8d3f9b4f0321db8210ada007271ecad8691ebb9a48407fd4826fcfebe06790ca'),
 ('(40,10697,21245)','(32,13693,29601)'),('len(own_fields) == 40','len(own_fields) == 32'),
 ('passed for all20','passed for all16'),('== (20, 0)','== (16, 0)'),('== (40, 40, 0, 58)','== (32, 32, 0, 48)'),
 ('== (10697, 21245)','== (13693, 29601)'),('partitions == 98','partitions == 80'),
 ('len(script_corrections) == 3','len(script_corrections) == 0'),('== (100,98,2)','== (80,80,0)'),
 ('len(apparatus_rows) == 40','len(apparatus_rows) == 32'),('All40 admitted fields','All32 admitted fields'),
 ("'build_delivery.py','freeze_source_first.py','prepare_primary.py']:","'build_delivery.py','freeze_source_first.py','prepare_primary.py'] + ['initial-reading-notes-%02d.json'%i for i in range(1,5)]:")
]
for old,new in replacements:
 assert old in source,old
 source=source.replace(old,new)
source=source.replace('import sys\n','import sys\nsys.dont_write_bytecode = True\n')
source=source.replace("    def file_binding(path, local=False):", "    (out/EVID/'original-source-packet-manifest.json').write_bytes((HERE/'input/source-packet-manifest.json').read_bytes())\n    (out/EVID/'full-hi-ur-reading-input-32.jsonl.gz').write_bytes(gzip.compress((HERE/'input/full-hi-ur-reading-input-32.jsonl').read_bytes(),mtime=0))\n    def file_binding(path, local=False):")
(HERE/'build_delivery.py').write_text(source)
print('Prepared16 explicit parents from32 genuinely read original fields;48 siblings remain unread.')
