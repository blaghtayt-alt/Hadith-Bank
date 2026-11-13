"""Freeze root's 42 completed original-field readings before candidate inspection."""
from pathlib import Path
import datetime, hashlib, json, sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
PIN='0639af7fd15786284b4c413fced77e38eec8825a'
INPUT=WORK/'phase15-checkpoint0639-abudawud-tirmidhi21-review/input/held-source-records.jsonl'
EXPECTED='07b2088e9e69091fe5d6a40f14d372b4a93727ac3a5ef573eb933b3eb5b48f1b'
NOTES={
'abudawud:2221':(
 'Complete Hindi reading: Ikrima reports the unnamed man, zihar, intercourse before expiation, his visit, the question and his moonlit shin explanation, then the instruction to remain apart until his own expiation. All supplied sequence and condition belong to the actual report; no additional legal application or identity is supplied.',
 'Complete Urdu reading: retain the entire Ikrima narrative and two dialogue turns, including before-expiation timing and the until-expiation condition. The source gives no independent commentary tail; no word is filled from another occurrence.'),
'abudawud:2222':(
 'Complete Hindi reading: the shorter Ikrima occurrence supplies zihar, moonlit glimpse, intercourse, visit and expiation instruction. Preserve its own abbreviated content without adding2221 separation instruction.',
 'Complete Urdu reading: keep all actually supplied acts and the expiation command. This short occurrence is complete as supplied and must not be harmonized with2221.'),
'abudawud:2232':(
 'Complete Hindi reading: IbnAbbas describes Barira husband Mughith as enslaved and reports the choice and waiting-period instruction. The parenthetical choice of remaining with Mughith and condition of not remaining define the actual scope and must not disappear through blanket parenthesis removal. Preserve the source descriptive wording without endorsement or invented evaluation.',
 'Complete Urdu reading: the named husband, status, choice and conditional waiting-period instruction are an actual report. Both parenthetical qualifiers specify its objects or operative condition and remain distinguishable from a lexical gloss.'),
'abudawud:2233':(
 'Complete Hindi reading: Aisha report contains a source defect: before the action the actor is represented by an honorific without the explicit Messenger noun present in Urdu. Do not insert that noun. Preserve emancipation timing, Barira own choice and the counterfactual free-husband condition; the final parenthetical Barira is a redundant pronoun identification.',
 'Complete Urdu reading: the explicit Messenger actor, after-emancipation timing, her choice and counterfactual husband status are all supplied. The final Barira parenthesis repeats an already named object and can remain explanatory context without changing the operative condition.'),
'abudawud:2234':(
 'Complete Hindi reading: Aisha reports only that the Messenger gave Barira a choice. The field ends there without the Urdu husband-status clause; neither clause nor punctuation may be imported.',
 'Complete Urdu reading: retain the supplied choice report and own final statement that her husband was enslaved. The shorter Hindi field does not authorize removing this Urdu fact.'),
'abudawud:2236':(
 'Complete Hindi reading: retain emancipation, the source household name, Mughith marriage and exact quoted intercourse condition removing the choice. Preserve printed spellings and do not rewrite the historical legal report as current advice.',
 'Complete Urdu reading: keep all named actors, emancipation/marriage frame and complete quoted condition. No separate commentary tail is present.'),
'abudawud:2243':(
 'Complete Hindi reading: Firuz states his conversion and marriage to two sisters and asks; the actual reply gives the printed choice of divorce. Preserve source tense/wording without harmonizing another translation.',
 'Complete Urdu reading: retain the whole named-person question and reply with its own choice wording. Do not generalize beyond the supplied dialogue.'),
'abudawud:2251':(
 'Complete Hindi reading: retain Sahl age fifteen and actual witnessed separation report; also retain the second supplied variant account and man conditional accusation statement under its own transmission frame. The Musaddad-ending notice is apparatus. The final AbuDawud/Sufyan noncorroboration assessment is source criticism, not another report body or a grade newly assigned by us.',
 'Complete Urdu reading: both finite supplied variants are reviewable, including the age and exact conditional statement. The intervening version-boundary notice and final transmission critique remain context with every character preserved; do not silently convert the critique repeated phrase into an additional independent narration.'),
'abudawud:2253':(
 'Complete Hindi reading: keep IbnMasud mosque scene, unnamed Ansari alternatives actually present, next-day visit, printed omission, prayer, revelation reference and child prediction/outcome. This Hindi is much shorter than Urdu; no absent killing alternative, full question, verse, oath sequence or response can be copied into it.',
 'Complete Urdu reading: retain all actual scenario alternatives, repeated question, prayer, quoted verse and its actual supplied rendering, full oath sequence, the stop instruction and final child prediction/outcome. The appended Nur6 locator and continuation marker are apparatus; the parenthetic legal explanation identifying a slander penalty is interpretation. Preserve narrative timing/actor qualifiers where they carry the source own account.'),
'abudawud:2258':(
 'Complete Hindi reading: Said question is unspecified in this field; retain it as printed and keep IbnUmar BanuAjlan report, three repetitions of the question and both refusal/separation acts. Do not supply Urdu fuller opening question or rewrite the source brother/sister wording.',
 'Complete Urdu reading: retain the supplied accusation question, own BanuAjlan description, contextual condition, complete repeated repentance invitation and refusal/separation. The numbered footnote mark is apparatus; no lineage inference or new grade follows.'),
'abudawud:2268':(
 'Complete Hindi reading: after the similarity/chain introduction an actual Aisha observation of a joyful arrival and shining face is printed. Then comes transmission criticism about asarir wording, which is context. A final separately attributed AhmadibnSalih historical complexion assertion is also actually supplied; if admitted it must keep its own scholar voice and family, not be attributed to the Prophet. Preserve source name defects.',
 'Complete Urdu reading: distinguish the finite Aisha arrival observation, AbuDawud lexical/transmission criticism and separately attributed AhmadibnSalih comparison of Usama and Zayd. The last is a historical assertion in the source voice, not Prophetic speech. Its inline numbered marker remains context.'),
'abudawud:2269':(
 'Complete Hindi reading: retain Zayd encounter, Yemeni narrator, three claimants and repeated failed agreement, Ali lottery and the one-third payments, then the Prophet laughter with the molars-or-canines uncertainty intact. Purity in parentheses is a lexical synonym of tuhr; the third-person identification specifies the recipient and cannot be conflated with a new unnamed actor.',
 'Complete Urdu reading: the entire nested reported case and laughter are actually supplied. Keep both repeated attempts, payment fraction and exact alternative tooth wording. Distinguish lexical purity gloss from the participant-target qualification.'),
'abudawud:2272':(
 'Complete Hindi reading: all four described pre-Islamic marriage practices form Aisha historical report through Urwa and IbnShihab. Keep all numbers, order, conditions, reported actions and final exception. The two parenthetical definitions of noble lineage and istibda are lexical explanation; their surrounding reported motives and acts remain.',
 'Complete Urdu reading: retain the complete four-part historical account, up-to-nine count, later identification acts and final stated abolition/exception. The two lexical parentheses may remain context; no historical count, actor, condition or quoted invitation should be lost.'),
'abudawud:2276':(
 'Complete Hindi reading: retain the unnamed mother bodily metaphors, divorce and custody request, then the exact until-remarriage reply. The parenthetic second defines the remarriage condition within the supplied quote and should be assessed as meaningful scope, not automatically deleted.',
 'Complete Urdu reading: all mother statements and the whole conditional response are supplied. The second-marriage qualification belongs to the source own condition; no modern custody advice or absent name is supplied.'),
'abudawud:2280':(
 'Complete Hindi reading: retain the actual Mecca departure, Hamza daughter call, Ali taking her and source-named Fatima addressee. The omitted-full-story pointer is context. After it a real Jafar statement, maternal-aunt judgment and actual quoted comparison are present and must be retained as a second ordered excerpt of this occurrence.',
 'Complete Urdu reading: the source supplies two actual narrative portions around a missing-story pointer. Preserve their order, named Fatima addressee, Jafar kinship/marriage assertion and the final judgment and saying. Never manufacture the unprinted middle story.'),
'tirmidhi:2225':(
 'Complete Hindi reading: IbnUmar reports the request to Umar and Umar own conditional comparison of AbuBakr appointment and the Prophet nonappointment. Keep it attributed to Umar. The final Tirmidhi grading is source evaluation context.',
 'Complete Urdu reading: retain Umar complete reply and both alternatives. The numbered reference, Tirmidhi notice of omitted story, grading and multiple-chain statement are apparatus/context and provide no missing story body.'),
'tirmidhi:2239':(
 'Complete Hindi reading: the finite Constantinople prediction is AnasibnMalik own attributed statement; no Prophet is named as its speaker. The MahmudibnGhaylan gharib assessment is separate context.',
 'Complete Urdu reading: retain the Anas saying with its stated timing, without upgrading it to direct Prophetic speech. Keep Mahmud transmission evaluation as source context.'),
'tirmidhi:2240':(
 'Complete2169-character Hindi reading: retain the entire supplied Nawas report through the long Dajjal dialogue, precise forty-day/year/month/week durations, prayer-estimation answer, instructed recitation, Isa sequence, Gog/Magog outcome, blessing and final wind/resurrection. It is substantially abbreviated relative to Urdu; do not fill omitted names, clauses, questions, numbers or images. Only the final Tirmidhi grading is a clear separate tail.',
 'Complete5720-character Urdu reading: preserve all supplied question/reply turns, durations and prayer estimation, instructed Kahf recitation, named comparison, wind/rain and livestock sequence, young man, Isa descent and breath, Ludd, Tur instruction, Gog/Magog sequence, actual Arabic verse and rendering, siege, death/removal, seven years of fuel, restored fruit/milk, final wind and remaining people. Assess each parenthesis by function: motives, synonym/lexical definitions, location labels, repeated pronoun explanations and price/famine interpretive glosses are context; meaningful narrative location/time/action qualifiers require individual judgment. The verse itself is spoken report content; only its appended locator is apparatus. Footnote marks and final Tirmidhi grading/transmission statements are context. Never replace the shorter Hindi with this fuller wording.'),
'tirmidhi:2246':(
 'Complete Hindi reading: AbuSaid reports travel and fear, IbnSayyad own defensive questions invoking Prophetic statements, AbuSaid changing impression, IbnSayyad claim to know Dajjal and AbuSaid final reply. Preserve pilgrimage-or-umra uncertainty and all nested voices. Do not flatten IbnSayyad assertions into direct verified Prophet narration or supply Urdu omitted material.',
 'Complete Urdu reading: retain all actual travel/actions/dialogue, IbnSayyad reported self-destructive statement and arguments as historical quoted content, source own changing impression and exact closing exchange. Name alias and explanatory Dajjal identifiers need contextual distinction. The numbered marker and Tirmidhi grading are apparatus. No advice, endorsement or verification of IbnSayyad claims is supplied.'),
'tirmidhi:2289':(
 'Complete Hindi reading: retain the reported dream, AbuBakr one-or-two bucket uncertainty, invocation for forgiveness, Umar action and actual final resting-place phrase. The yani restatement is explanation, and Tirmidhi grading/cross-reference are context; no uncertainty or prayer should be removed.',
 'Complete Urdu reading: retain the dream and all source actual acts, including one-or-two ambiguity and prayer. The parenthetic well location specifies the dream scene; the final yani restatement with footnote and following grading/other-companion pointer are context.'),
'tirmidhi:2290':(
 'Complete Hindi reading: retain the full dream and its interpretation expressly attributed to the Prophet, including source description and Medina-toMuhayya/Juhfa sequence. The parenthetic alternate place-name gloss and final grading are context; the actual interpretation is report content, not our explanation.',
 'Complete Urdu reading: retain dream and source-attributed interpretation, including parenthetic fever qualification identifying the illness. The explicit Muhayya/Juhfa synonym parenthesis is lexical geography context; final Tirmidhi grading is not newly assigned by this review.'),
}

def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def main():
 raw=INPUT.read_bytes();assert sha(raw)==EXPECTED
 rows=[json.loads(x) for x in raw.splitlines()]
 assert len(rows)==21 and {r['collection']+':'+r['number'] for r in rows}==set(NOTES)
 evidence=WORK/'phase13-successor-acquisition-monitor/held-evidence'
 authority=json.loads((evidence/'evidence-manifest.json').read_bytes())
 entries=json.loads((evidence/'held-state-entries.json').read_bytes())
 assert authority['saved_head']==PIN
 sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
 import import_deenhindi as importer
 fields,proofs=[],[]
 for saved in rows:
  key=saved['collection']+':'+saved['number'];identity='deenhindi-'+key
  entry=entries[key];files=[]
  for d in (saved['snapshot'],entry['parsed']):
   stored=(evidence/'sources'/d['path']).read_bytes();a=authority['files'][d['path']]
   blob=hashlib.sha1(b'blob '+str(len(stored)).encode()+b'\0'+stored).hexdigest()
   assert sha(stored)==a.get('stored_sha256',a['sha256']) and blob==a['git_blob_sha1']
   decoded=importer.checked_bytes(evidence/'sources',d)
   files.append({'path':d['path'],'stored_sha256':sha(stored),'git_blob_sha1':blob,
    'stored_bytes':len(stored),'decoded_sha256':sha(decoded),'decoded_bytes':len(decoded)})
  parsed=json.loads(importer.checked_bytes(evidence/'sources',entry['parsed']))
  for k in ('collection','number','source_record','source_reference_verbatim','snapshot'):
   assert parsed[k]==saved[k]
  html=importer.checked_bytes(evidence/'sources',saved['snapshot'])
  reparsed,reference=importer.parse_record(html,saved['collection'],saved['number'])
  assert reparsed==saved['source_record'] and reference==saved['source_reference_verbatim']
  proofs.append({'id':identity,'source_url':saved['snapshot']['url'],'files':files,
   'complete_html_reparse_matches_source_and_reference':True})
  for i,(language,name) in enumerate([('hi','translationHindi'),('ur','translationUrdu')]):
   t=saved['source_record'][name]
   fields.append({'id':identity,'language':language,'source_field':name,'text':t,
    'text_sha256':sha(t.encode()),'characters':len(t),'utf8_bytes':len(t.encode()),
    'complete_field_read':True,'independent_source_first_note':NOTES[key][i]})
 assert (len(fields),sum(f['characters'] for f in fields),sum(f['utf8_bytes'] for f in fields))==(42,30305,63236)
 proof={'schema':'hadith-bank-independent-source-reopen-and-reparse-v1','source_commit':PIN,
  'input_sha256':EXPECTED,'evidence_manifest_sha256':sha((evidence/'evidence-manifest.json').read_bytes()),
  'current_parser_sha256':sha(Path(importer.__file__).read_bytes()),'records':21,'source_files':42,'rows':proofs}
 dump(HERE/'independent-source-verification.json',proof)
 receipt={'schema':'hadith-bank-independent-complete-source-first-readings-v1',
  'reviewer':'/root','source_commit':PIN,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'candidate_inspected_before_this_freeze':False,'scope':'All21 supplied original Hindi and Urdu fields read in full before inspecting the primary candidate; no other language reading is claimed.',
  'complete_fields':42,'characters':30305,'utf8_bytes':63236,'source_input_sha256':EXPECTED,
  'independent_source_verification_sha256':sha((HERE/'independent-source-verification.json').read_bytes()),
  'independent_pro_qc':'not_performed','fields':fields}
 dump(HERE/'independent-complete-source-first-readings.json',receipt)
 print(json.dumps({p.name:sha(p.read_bytes()) for p in [HERE/'independent-complete-source-first-readings.json',HERE/'independent-source-verification.json']},indent=2))

if __name__=='__main__':main()
