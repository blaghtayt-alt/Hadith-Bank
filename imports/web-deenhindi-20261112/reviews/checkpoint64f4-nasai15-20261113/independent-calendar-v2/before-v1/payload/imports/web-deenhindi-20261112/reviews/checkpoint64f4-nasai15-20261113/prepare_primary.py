"""Serialize explicit decisions only after the complete frozen30-field reading pass."""
from pathlib import Path
import hashlib,json,pprint
H=Path(__file__).resolve().parent
assert not (H/'delivery-manifest-v1.json').exists()
b=(H/'source-first-complete-reading.json').read_bytes()
assert hashlib.sha256(b).hexdigest()=='20612e9d62e5a6e7f83fe7748519a274c9d389f0ec131efea125669da6982449'
r=json.loads(b);assert r['all_full_fields_read_before_candidate_creation']
WHO={
 '2705':('reported_hearing_and_visit_with_distinct_companion_voices','Muhammad ibn Muntashir reports hearing Ibn Umar, then his own visit and Aisha\u2019s separate observed account; all three actual voices remain distinct.'),
 '2706':('companion_report_of_source_qualified_prophetic_prohibition','Anas reports the saffron prohibition with the source-printed ihram condition; the shortened Urdu ending remains exact.'),
 '2707':('companion_report_of_source_qualified_prophetic_prohibition','Anas ibn Malik reports the saffron prohibition with the source-printed ihram condition; this is the separate printed occurrence.'),
 '2710':('companion_report_of_ritual_encounter_and_reply','Ya\u2019la reports the robe/yellow-hair encounter at the source-named Jirana, the man\u2019s Umrah question and the three-part reply.'),
 '2716':('companion_observation_of_prophetic_hajj_call','Aisha reports that the Messenger called labbayk for Hajj. The unprinted full formula is not supplied.'),
 '2718':('companion_departure_and_intention_report','Aisha reports the actual departure with the Messenger and the source\u2019s only-Hajj intention.'),
 '2726':('reported_companion_statement_about_ritual_and_chronology','Mutarrif reports Imran\u2019s statement about combining Hajj/Umrah and death before a prohibition or prohibitory revelation. This is Imran\u2019s source assertion, not direct Prophetic speech or a certified legal finding.'),
 '2732':('companion_hajj_account_with_conditional_prophetic_instruction','Ibn Umar gives the supplied Farewell-Hajj narrative, separately bounded instruction, and resumed observation; every quantity, condition and actual ritual sequence remains source-limited.'),
 '2737':('reported_companion_encounter_with_source_qualified_purpose','Tawus reports Muawiya\u2019s question to Ibn Abbas about Marwah haircutting and the source-rendered purpose/objection contrast; the parenthetical purpose is not independently certified verbatim speech.'),
 '2738':('companion_ritual_encounter_and_later_historical_discussion','Abu Musa gives his actual first encounter and later practice/discussion with the source-designated Amir alMu\u2019minin. Each nested voice remains distinct and Hindi\u2019s missing links stay missing.'),
 '2741':('companion_menstruation_encounter_and_except_tawaf_instruction','Aisha reports the only-Hajj departure, Sarf scene, actual question/reply and all-rituals-except-tawaf instruction; duplicate lexical glosses remain context.'),
 '2743':('reported_visit_and_ritual_question_with_source_defects','Ja\u2019far reports the actual visit/question to Jabir, then the source\u2019s Hajj account and Ali dialogue. Missing Hindi links and its printed stick wording are not repaired.'),
 '2757':('companion_critical_statement_with_place_qualification','Salim reports actually hearing his father\u2019s Baida criticism. Each own field retains only its supplied subsequent statement, with Hindi\u2019s truncated ending unfilled.'),
 '2765':('companion_report_of_condition_instruction_and_compliance','Ibn Abbas reports Duba\u2019ah\u2019s Hajj intention, instruction to stipulate, and compliance; the condition\u2019s unprinted formula and Hindi\u2019s missing joins are not supplied.'),
 '2781':('companion_ritual_question_and_time_limited_reply','Hafsa asks the actual Umrah/ihram question and receives the source-printed talbid/head and garland/hady reply with its until-my-sacrifice condition.')}
SPECS={}
for number,(kind,voice) in WHO.items():
    fs=[f for f in r['fields'] if f['id']=='deenhindi-nasai:'+number]
    assert {f['language'] for f in fs}=={'hi','ur'}
    key='nasai:'+number
    SPECS[key]={'id':key,'decision':'register','languages':['hi','ur'],'read_languages':['hi','ur'],
      'field_notes':{f['language']:f['reading_note'] for f in fs},'shared_report_family':True,
      'report_type':kind,'speaker':voice,
      'reason':'Retain only the actual supplied report or saying under its own source attribution, exact text and explicit qualifications. No missing action, subject, place, formula, canonical identity or sibling translation is inserted.'}

for language,marker in [('hi','तो मैं आयशा'),('ur','تو میں عائشہ')]:
    SPECS['nasai:2705'].setdefault('components',{})[language]=[
      {'stop_before':marker,'report_type':'heard_companion_preference_statement','speaker':'Muhammad ibn Muntashir reports actually hearing Ibn Umar\u2019s tar-versus-perfume preference. It is Ibn Umar\u2019s saying, not Prophetic speech.'},
      {'start_at':marker,'report_type':'narrator_visit_with_companion_prophetic_observation','speaker':'Muhammad reports his actual visit/relay to Aisha, who gives her own perfuming, wives-visit and muhrim-morning observation. The supplied hearing and reply remain their actual voices.'}]
SPECS['nasai:2705']['component_identity_overrides']={'report-1':'heard-ibn-umar-preference','report-2':'visit-and-aisha-observation'}
for number in ['2706','2707']:
    SPECS['nasai:'+number]['annotations']={lang:'The parenthetical state-of-ihram condition materially restricts this provider\u2019s printed prohibition. Preserve it without canonical scope correction or a claim that the qualification is independently verbatim wording.' for lang in ['hi','ur']}
SPECS['nasai:2710']['annotations']={lang:'The saffron parenthesis identifies the source-stated substance causing the head/beard yellowness. It remains material scene and washing-command scope, qualified as this source rendering.' for lang in ['hi','ur']}
for language,start,resume in [('hi',"'जो लोग",'चुनांचे रसूल'),('ur','”جو لوگ','چنانچہ رسول')]:
    SPECS['nasai:2732'].setdefault('components',{})[language]=[
      {'stop_before':start,'report_type':'companion_hajj_narrative_before_instruction','speaker':'Ibn Umar narrates the source\u2019s actual Umrah/Hajj order, hady and departure circumstances, then introduces the Messenger\u2019s instruction.'},
      {'start_at':start,'stop_before':resume,'report_type':'reported_prophetic_conditional_ritual_instruction','speaker':'The source\u2019s actual reported instruction distinguishes those with/without hady, preserves8Dhul-Hijjah timing and the3-plus7 fasting conditions. Source-rendered qualifications are not independently certified verbatim speech.'},
      {'start_at':resume,'report_type':'resumed_companion_observation_of_ritual_sequence','speaker':'Ibn Umar resumes the supplied actions and quantities: tawaf, kissing,3-running/4-walking, two rakahs, seven saf a-marwah rounds, completion, dated sacrifice and return/tawaf. The source\u2019s actual sequence and terminology remain exact.'}]
SPECS['nasai:2732']['component_identity_overrides']={'report-1':'narrative-before-instruction','report-2':'conditional-ritual-instruction','report-3':'resumed-ritual-observation'}
SPECS['nasai:2732']['exclude_substrings']={'ur':['۱؎','۲؎','( جانور ذبح کئے )','( کا جانور )']}
SPECS['nasai:2732']['annotations']={lang:'Keep the actual finite yani chronology, place, ritual-day, quantity and condition wording as this provider\u2019s rendering. Urdu\u2019s unmatched parenthesis remains exact. Only explicit note markers and duplicate technical slaughter/hady glosses become context; no new ritual action or external legal harmonization is supplied.' for lang in ['hi','ur']}
SPECS['nasai:2737']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2737']['annotations']={lang:'The I-am-saying-this-so parenthesis provides the source-rendered utterance/purpose relation and remains selected. It is not certified as an independently verbatim Muawiya quotation, and the negative/although contrast is not externally resolved.' for lang in ['hi','ur']}
for language,marker in [('hi','चुनांचा मैं'),('ur','چنانچہ میں')]:
    SPECS['nasai:2738'].setdefault('components',{})[language]=[
      {'stop_before':marker,'report_type':'companion_ritual_dialogue_and_compliance_account','speaker':'Abu Musa reports the Batha talbiya/hady questions, the actual ritual instructions and his ensuing account. Hindi\u2019s missing sai/woman-visit bridge is left absent rather than supplied from Urdu.'},
      {'start_at':marker,'report_type':'companion_practice_and_reported_ruler_discussion','speaker':'Abu Musa reports his own practice, the actual Hajj-season interruption and a subsequent exchange with the source-designated Amir alMu\u2019minin. The ruler\u2019s supplied Quran/Sunnah argument remains his reply; a personal name and Hindi\u2019s missing arrival/predicate/hady-ending links are not inserted.'}]
SPECS['nasai:2738']['component_identity_overrides']={'report-1':'first-ritual-encounter','report-2':'later-practice-and-discussion'}
SPECS['nasai:2738']['annotations']={
 'hi':'This own Hindi omits the woman-visit/sai link, part of the later arrival/request bridge, and the final answer\u2019s main predicate/condition. Preserve the actual finite report and its broken fragments without filling them. The source-rendered one-time occasion relation stays; the ruler is retained by the supplied title only.',
 'ur':'The fuller own Urdu keeps the actual woman visit, intervening instruction/arrival and ending-hady condition. Its one-time occasion parenthesis is material scene transition. These own words are not used to repair Hindi.'}
SPECS['nasai:2741']['exclude_substrings']={'hi':['(menstruating)','(औरतों)'],'ur':['( عورتوں )']}
SPECS['nasai:2743']['annotations']={
 'hi':'This field abbreviates the reception reply and prints came-with-a-stick without its missing actor/place link. Preserve that text, the actual later Ali dialogue and the until-Hajj-completion restriction without importing Ali/Yemen/hady wording from Urdu. The restriction is qualified source rendering.',
 'ur':'The source expressly gives Ali/Yemen and Messenger/Medina hady circumstances. Preserve the actual reception and dialogue, including the source-rendered until-Hajj-completion restriction; do not promote that parenthesis to independently certified verbatim wording.'}
SPECS['nasai:2757']['components']={
 'hi':[{'report_type':'truncated_companion_critical_statement','speaker':'Salim reports hearing his father\u2019s finite Baida criticism. The following Messenger/not-from-Baida clause is truncated before its main action/alternative place; neither is filled.'}],
 'ur':[{'report_type':'companion_critical_statement_and_place_restriction','speaker':'Salim reports hearing his father\u2019s Baida criticism and the source\u2019s talbiya statement with the not-Baida contrast and exclusive Dhul-Hulayfah-mosque scope.'}]}
SPECS['nasai:2757']['exclude_substrings']={'ur':['۱؎','۲؎']}
SPECS['nasai:2757']['annotations']={'hi':'The supplied source ends after a negative Baida fragment. No talbiya action, alternative place or final predicate is borrowed from Urdu.','ur':'The parenthetic not-from-Baida wording is material negative place scope and stays as source rendering, with the mosque-only limit intact.'}
SPECS['nasai:2765']['exclude_substrings']={'ur':['۱؎']}
SPECS['nasai:2765']['annotations']={'hi':'The commanding figure is printed only with the abbreviated Akram/honorific join, and the ending has an unmatched honorific fragment. Preserve these exact defects and the finite instruction/compliance fragments; the condition\u2019s absent formula is not supplied.'}
assert len(SPECS)==15 and sum(len(s['read_languages']) for s in SPECS.values())==30
(H/'manual_rules.py').write_text('"""Explicit choices after the complete frozen30-field source-first pass."""\nSPECS = '+pprint.pformat(SPECS,width=115,sort_dicts=True)+'\n')

source=(H.parent/'phase22-checkpoint17cd-nasai22-review/build_delivery.py').read_text()
old_scope='Nasai22 at checkpoint17cd. All44 complete Hindi/Urdu fields and the three remaining own fields of2636 were read before candidate creation.21 parents have supplied report content;2636 is source-only after all five own fields were read.63 other nonempty siblings remain unread. Source-rendered recipient, condition and journey scope remain; the two truncated Hindi main-action predicates are disclosed and left unfilled. Exact lexical/word-form/pointer/interpretive apparatus stays context. No source text, number, narrator or script is repaired.'
new_scope='Nasai15 at checkpoint64f4. All30 complete Hindi/Urdu originals were read before candidate creation. All15 parents contain finite own reports or sayings;45 other nonempty sibling fields remain unread. Actual nested voices and reception scenes, ritual conditions, quantities, dates and place/recipient scope remain source-qualified. Hindi omissions, damaged predicates and literal stick wording remain unfilled. Only explicit note markers and duplicate lexical/technical glosses become context. No source text, number, narrator, script or canonical identity is repaired.'
replacements=[(old_scope,new_scope),('Nasai22','Nasai15'),('checkpoint17cd-nasai22','checkpoint64f4-nasai15'),
 ('17cd396eb858a29162505d545aad556ac73ce9ce','64f4ed50ed6026855237a5d547a86dd03e73f804'),
 ('e606722e94cffde01f011c34bd9cd7dbe53003b8522a1d4f24c8545223f78f17','23013833e118d6b9585cfe40c2f41021f50c06d0673d12f71add638a25c68052'),
 ('phase21-successor-acquisition-monitor/held-evidence','phase22-successor-acquisition-monitor/complete-held-evidence'),
 ('len(specifications) == 22','len(specifications) == 15'),("{'nasai':22}","{'nasai':15}"),
 ('86652d131ab33fb6b8af45f4a042008f3b19a0cb9db55b481b03caaddc0571f8','20612e9d62e5a6e7f83fe7748519a274c9d389f0ec131efea125669da6982449'),
 ('(47,12443,26863)','(30,13448,28971)'),('len(own_fields) == 47','len(own_fields) == 30'),
 ('passed for all22','passed for all15'),('== (21, 1)','== (15, 0)'),('== (47, 42, 5, 63)','== (30, 30, 0, 45)'),
 ('== (12443, 26863)','== (13448, 28971)'),('partitions == 110','partitions == 75'),('== (110,110,0)','== (75,75,0)'),
 ('len(apparatus_rows) == 42','len(apparatus_rows) == 30'),('All42 admitted fields','All30 admitted fields'),
 (",'additional2636-source-only-input-3.jsonl'",''),('range(1,8)','range(1,5)'),
 ('full-hi-ur-reading-input-44.jsonl','full-hi-ur-reading-input-30.jsonl')]
for old,new in replacements:
    assert old in source,old;source=source.replace(old,new)
(H/'build_delivery.py').write_text(source)
print('Prepared15 explicit parents from30 complete own original readings;45 sibling fields remain unread.')
