"""Freeze root's actual complete independent readings before candidate access."""
from pathlib import Path
import datetime, hashlib, json, sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PIN = 'bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
INPUT = WORK/'phase18-checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-review/input/full-field-reading-input-55.jsonl'
EVID = WORK/'phase16-successor-acquisition-monitor/held-evidence'
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer

NOTES = {
 'abudawud:2385': 'Jabir reports Umar\'s own account of kissing while fasting, his question, the mouth-rinsing analogy, his no-harm answer and the final reply. Preserve the parenthetic then-what-happened question complement as actual discourse and retain the fasting condition. Do not turn Umar\'s first-person admission into Prophetic first-person speech.',
 'abudawud:2403': 'Hamza gives his actual transport/rental work, occasional Ramadan travel, youth and strength, and concern about deferred fasting becoming a debt before asking which choice has greater reward. Retain the complete circumstances and the conditional personal reply as supplied in each field, including the inline identification of Ramadan. These are the participant\'s question, not compiler exposition.',
 'abudawud:2405': 'Anas reports the Ramadan journey, both fasting and nonfasting participants, and the mutual absence of rebuke. Keep both negated directions as a finite observation in Anas\'s voice; do not invent a separate Prophetic command.',
 'abudawud:2409': 'Abu Darda reports the expedition, extreme heat, hand-or-palm alternative, and the explicit exception that only the Prophet and Abdullah ibn Rawaha were fasting. Retain the alternative and exception without generalizing beyond the reported occasion.',
 'abudawud:2417': 'Keep the two named festival fast prohibitions, the two named garment practices and both after-prayer times. The parenthetic possible-exposure explanation describes the rationale of the one-garment posture and remains explanatory source context; it is not an additional direct quotation. Urdu footnote pointers are apparatus. No garment definition or missing condition is supplied externally.',
 'abudawud:2423': 'Read all five complete fields. Each is a transmission/provenance assessment: when the Saturday prohibition was mentioned, Ibn Shihab called it a Himsi tradition. The Arabic chain, English report and Roman Urdu add no substantive report body. A named scholar and finite assessment wording do not convert this criticism of a transmitted report into its absent matn. Preserve all five as read context, with source-only proposed.',
 'abudawud:2426': 'After the same-chain/same-hadith pointer, retain the actual question about Monday and Thursday and the supplied first-person birth/revelation answer. Hindi has no intact explicit answer introducer and a damaged question-to-answer join: do not insert Urdu\'s speaker words. Keep the source\'s singular day and do not repair the apparent two-day question. The parenthetic Pir term only aliases Monday and can remain lexical context. The omitted preceding report is not reconstructed.',
 'abudawud:2456': 'Keep Umm Hani\'s Fath Mecca setting, Fatima on the left and her on the right, the servant\'s unnamed beverage, drinking sequence, fasting admission, qada question, negative answer and voluntary-fast condition. Do not identify the drink or remove the distinction between obligatory make-up and voluntary fasting. Urdu footnote pointer is context.',
 'tirmidhi:2382': 'Hindi is an abbreviated but actual Shafiya/Abu Huraira meeting and first-person witnessed reaction followed by the supplied judgment account; do not fill its missing dialogues or Muawiya sequel from Urdu. Its knee synonym is lexical context. Urdu was read completely (4,533 characters), including all repeated fainting/recovery episodes, the three full judgments, the reciter/rich-man/martyr order, claimed deeds, denials and reputation motives. Preserve the parenthetic Quran-learning object as a qualification of the stated motive rather than silently erasing its reference. After the compiler introducer there are actual later encounter/reaction reports involving Shafiya, Muawiya, the executioner-witness, an unnamed visitor, crying, the observers\' fear/comment and Muawiya\'s recovery and recitation. Retain these as bounded later historical components in the same source family, with their own voices and no invented visitor identity. Keep the actual Arabic verse and supplied Urdu translation; the parenthetic surah/verse reference and final compiler grade are context. Do not promote the compiler\'s frame or cross-route report to a new Prophetic statement.',
 'tirmidhi:2392': 'Retain the actual conditional instruction to tell the Muslim brother whom one loves. The final compiler grade and other-narrator list are context. No reading coverage is claimed for empty or unread siblings.',
 'tirmidhi:2397': 'Abu Wail reports Aisha\'s personal comparison of observed pain. Keep the actual comparison in her voice and the visible source words; it is not a spoken saying of the Prophet. The appended compiler grade is context.',
 'tirmidhi:2406': 'Preserve Uqba\'s salvation question and all three supplied instructions: controlling the tongue, remaining within the house and weeping over one\'s faults. Keep the question as its own participant speech and exclude only the compiler grade and Urdu pointer.',
 'tirmidhi:2410': 'Keep Sufyan\'s request for something to hold firmly, the statement of the Lord and steadfastness instruction, the later fear question, actual tongue-grasping demonstration and deictic reply. Hindi\'s defective transition after Allah remains unchanged; do not borrow Urdu\'s covenant wording. Parenthetic true-object-of-worship phrases only gloss Rabb and remain lexical context. Grade and route discussion are context.',
 'tirmidhi:2413': 'Retain the brotherhood arrangement, Salman\'s visit, Umm Darda\'s clothes and explanation, meal/fast exchange, repeated sleep commands, near-dawn prayer, all four rights and the final Prophetic approval. Both source fields actually say Salman ate at the relevant join; do not replace that printed actor with a familiar parallel. The rights statement is Salman\'s speech, followed by the separate approval. Compiler grade and Urdu pointer are context.',
 'tirmidhi:2429': 'Keep the recited revelation as actually printed in each script, the question, companions\' reply, the earth\'s testimony explanation and concluding answer. Hindi omits the Urdu place/day details and has a damaged join before did-such-work; preserve it without filling those missing clauses. The final grade is compiler context; no external canonical verse mapping is inferred.',
 'tirmidhi:2434': 'Read all 5,410 Hindi and all 5,061 Urdu characters. Retain the meat-serving/preference event and the entire supplied intercession narrative: gathering, heat/distress, each successive request/referral, every stated reason and qualification, the unnamed unauthorized killing, the narrated absence of a specified error for Isa, the approach to Muhammad, prostration/praise, repeated requests, right-gate/no-reckoning condition, access to other gates and the final distance alternative. Keep each embedded speaker distinct within the same report family. The parenthetic deep-friend phrase is a lexical gloss; Abu Hayyan\'s note only points to unprovided wording; the parenthetic forward-speaker label is apparatus. The parenthetic Ummah identity and entering-the-gates phrase materially qualify the beneficiaries/action and should remain with an explicit source-rendering qualification, without treating the brackets as proof of literal direct speech. Do not delete these automatically with the glosses. Preserve each field\'s own repetitions, Hajar-or-Busra alternative and spelling, without choosing an alternative or filling the three unspecified lies. Final compiler grade/routes and footnote pointer are context.',
 'tirmidhi:2454': 'Retain the square/central/side-line drawing sequence and its actual supplied explanatory speech about human, encircling death, successive harms and the protruding hope line. The parenthetic square synonym and wishes gloss are explanatory source context. Do not harmonize the printed central-human wording with the separate wishes gloss or redraw an inferred diagram. Urdu footnote pointer is context.',
 'muslim:2464': 'All five fields are a chain plus an explicit statement that the quoted arrow/religion wording is NOT present in this version. The quoted omission must not be admitted as affirmative matn. Arabic, English and Roman Urdu supply no additional actual report. Source-only after all five complete readings.',
 'muslim:2465': 'Retain Ali\'s actual Khawarij description with its short-or-excess/moving-flesh alternative and comparison, his fear-of-boasting condition and unspecified promised reward, Ubaida\'s direct-hearing question and all three Kaaba oaths/affirmations. Parenthetic comparison, questioner identity and promise/direct-hearing qualifiers materially carry comparison, attribution or scope and should be retained with their source-rendering status. Do not invent the unspecified reward or label Ali\'s statement itself as Prophetic speech.',
 'muslim:2466': 'All five complete fields contain only Ubaida\'s transmission-fidelity preface and an onward similar/Ayyub/marfu pointer; English ends after saying he narrated. No actual substantive report body is supplied. Preserve these as read transmission context, without importing Ali\'s neighboring report. Source-only proposed.',
 'muslim:2474': 'The route pointer and the old we-do-not-eat-charity wording are apparatus, while the new charity-is-not-lawful-for-us wording is an actually supplied finite variant and is admissible. Keep its original words and unresolved quoted speaker identity: the visible Waki/Shuba transmission frame does not establish that either personally issued this statement, nor does it identify the unseen parent\'s actor. Do not reconstruct the absent surrounding event.',
 'ibnmajah:2449': 'Retain both named sale prohibitions and the full three-category farming statement. The gifted-or-loaned parenthesis materially states alternative tenure bases, and cash specifies the supplied payment mode; retain them with the gold-or-silver alternative, ownership and leasing conditions. Do not substitute a modern contract description or delete these as mere synonyms.',
 'ibnmajah:2450': 'Keep Ibn Umar\'s actual former sharecropping practice, prior no-objection view, hearing Rafi\'s report of the prohibition and consequent stopping. The parenthetic sharecropping phrase only defines the already named muzaraat term; it remains lexical context. Preserve the historical change in the companion\'s own voice and the embedded attributed prohibition. Urdu pointer is context.'
}

def sha(b): return hashlib.sha256(b).hexdigest()
def enc(o): return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): assert p.read_bytes()==b,p
    else: p.write_bytes(b)

raw=INPUT.read_bytes()
assert sha(raw)=='b5a039a0a9ca5a667dd70c4060925f13122faa8e1af21eef8beff6b54fec0c9b'
readings=[json.loads(x) for x in raw.splitlines()]
all_cohort=(WORK/'phase16-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl').read_bytes()
assert sha(all_cohort)=='849f800d50e8a32ff14d872717b9c5ca843231884bd07f852308e29a33bddfa5'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,all_cohort.splitlines()) if r['collection']+':'+r['number'] in NOTES}
assert len(sources)==23 and set(sources)==set(NOTES)
manifest=json.loads((EVID/'evidence-manifest.json').read_bytes())
entries=json.loads((EVID/'held-state-entries.json').read_bytes())
assert manifest['saved_head']==PIN
proof=[]
for key,r in sources.items():
    files=[]
    for kind,d in [('raw',r['snapshot']),('parsed',entries[key]['parsed'])]:
        b=(EVID/'sources'/d['path']).read_bytes(); authority=manifest['files'][d['path']]
        g=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        assert sha(b)==authority.get('stored_sha256',authority['sha256']) and g==authority['git_blob_sha1']
        plain=importer.checked_bytes(EVID/'sources',d)
        if kind=='raw':
            obj,cite=importer.parse_record(plain,r['collection'],r['number'])
            assert obj==r['source_record'] and cite==r['source_reference_verbatim']
        else:
            obj=json.loads(plain)
            for k in ['collection','number','source_record','source_reference_verbatim','snapshot']: assert obj[k]==r[k]
        files.append({'kind':kind,'path':d['path'],'stored_bytes':len(b),'stored_sha256':sha(b),'git_blob_sha1':g,'plain_sha256':sha(plain)})
    proof.append({'id':'deenhindi-'+key,'files':files,'full_raw_reparse_exact':True})
fields=[]
for f in readings:
    key=f['collection']+':'+f['number']; value=f['text']
    assert value==sources[key]['source_record'][f['source_field']] and sha(value.encode())==f['text_sha256']
    assert len(value)==f['characters'] and len(value.encode())==f['utf8_bytes']
    fields.append({'id':f['occurrence_id'],'language':f['language'],'source_field':f['source_field'],'text':value,'sha256':sha(value.encode()),'characters':len(value),'utf8_bytes':len(value.encode()),'complete_field_read':True,'independent_reading_note':NOTES[key]})
assert len(fields)==55 and sum(f['characters'] for f in fields)==34118 and sum(f['utf8_bytes'] for f in fields)==70795
only=['deenhindi-abudawud:2423','deenhindi-muslim:2464','deenhindi-muslim:2466']
for ident in only: assert len([f for f in fields if f['id']==ident])==5
receipt={'schema':'hadith-bank-complete-independent-source-first-reading-v1','reviewer':'/root','source_commit':PIN,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_or_primary_notes_inspected':False,'all_fields_read_in_full_before_candidate_access':True,'input_sha256':sha(raw),'complete_fields':55,'characters':34118,'utf8_bytes':70795,'source_only_proposed_ids':only,'every_supplied_field_of_source_only_actually_read':True,'fields':fields,'coverage_note':'46 Hi/Ur fields plus 9 Arabic/English/Roman fields for the three proposed source-only occurrences. A truncated display of fields15-34 was repaired by a separate complete display of27-32 before freezing; no unseen text is counted. No other sibling-language semantic reading is claimed.','independent_pro_qc':'not_performed'}
target=ROOT/'complete-independent-source-first-readings.json';assert not target.exists();put(target,enc(receipt))
put(ROOT/'independent-source-verification.json',enc({'status':'PASS','source_commit':PIN,'records':proof,'source_files_verified':46,'full_raw_reparses_exact':23,'new_semantic_approvals_from_hashing':0}))
put(ROOT/'input/full-field-reading-input-55.jsonl',raw)
print(json.dumps({'source_first_sha256':sha(target.read_bytes()),'source_verification_sha256':sha((ROOT/'independent-source-verification.json').read_bytes()),'complete_fields':55,'characters':34118,'utf8_bytes':70795,'candidate_inspected':False},indent=2))
