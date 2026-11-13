"""Root's complete independent readings, frozen before candidate inspection."""
from pathlib import Path
import datetime, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
PIN='5589a3ffc3b43c3324ae26f2b6c4d33152834456'
EVID=WORK/'phase15-successor-acquisition-monitor/held-evidence'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
NOTES={
 'abudawud:2306':'Read the complete correspondence/inquiry frame and Subaya account, her named husband, pregnancy/death/birth/purification, grooming, Abu Sanabil assertion, evening inquiry and conditional remarriage permission. The husband tribal/Badr biography is explanatory context. The appended Ibn Shihab I-think paragraph is a juristic gloss on the preceding episode, not the supplied Prophetic answer; it must remain commentary under the explicit exclusion of legal commentary. Do not remove the four-month-ten-day assertion or its contrast with childbirth. Urdu terminal footnote is apparatus.',
 'abudawud:2310':'Retain all three sins in their actual ordered dialogue, creation clause, child-feeding fear and neighbor-wife relationship. The subsequent revelation statement and actually supplied Quran quotation/translation belong to the narrated revelation context, with their own voice distinguished from direct Prophetic speech. Keep the actual Hindi corruption without filling Arabic or Urdu; source verse locator and explicit continuation ellipsis/kh are apparatus. The Urdu parenthetic greatest-sin-is formula restates the answered question rather than adding a condition.',
 'abudawud:2322':'Complete finite comparative practice report: more29-day than30-day fasts with the Prophet. Keep both counts, comparison and collective viewpoint.',
 'abudawud:2324':'Keep the actually supplied festival timing and the stated Arafat, Mina, streets and Muzdalifa locations. Hindi lacks some fuller Urdu framing/Mecca wording and is damaged; do not fill it. The standing explanation of wuquf is lexical context; Urdu inline footnote is apparatus. No omitted full hadith is reconstructed.',
 'abudawud:2330':'Read all five supplied languages. Every field is a chain introducing Awzai\'s definition of sirrahu as the beginning of the month, explicitly in connection with another hadith. This is lexical explanation of an absent report, not a separate substantive report body. The named hearing formula and provider number do not convert a definition into admitted matn. Preserve all five fields as source context; no source-only decision may be finalized from Hindi/Urdu alone.',
 'abudawud:2331':'Read all five supplied languages. Said/Ibn Abd al-Aziz defines sirrahu as its beginning; the Arabic/Hindi/Urdu/Roman append Abu Dawud\'s middle/end lexical alternatives, while English supplies only the initial definition and is visibly unclosed. These are meanings of a term, not an independent event or report body. Preserve all original chain/definition/disagreement text as source context and do not fill English.',
 'abudawud:2352':'Preserve the sunset, every repeated descend/mix command, Bilal\'s two time objections, actual descent/mixing/drinking, the night-arrival condition and the eastern finger gesture. Urdu parenthetic from-the-mount supplies the commanded motion\'s source and remains meaningful.',
 'abudawud:2368':'Retain the finite opening that Shaddad was walking with the Prophet. The then/at-that-time bridge and parenthetic he-said provide no supplied speech content and lead into an explicit same-as-previous-hadith pointer. Keep the omission explicit; do not recreate its absent saying or claim a complete Prophetic utterance.',
 'tirmidhi:2296':'All five original fields were read completely. Hindi/Urdu/Roman contain an analogous-hadith pointer plus grading, chain variation and transmitter biography; Arabic supplies the chain and same apparatus; English is only an alternate-chain/narrator-name statement. No supplied report body appears in any field. This is a source-only occurrence with intact provenance, not a failed download.',
 'tirmidhi:2329':'Retain the actual anonymous question and answer requiring both long life and good deeds. Compiler grading, parallel-report list and Urdu footnote remain context.',
 'tirmidhi:2330':'Keep both best/worst questions, long-life condition and good/bad-action opposition. Compiler grade and Urdu footnote are context; no named identity is invented.',
 'tirmidhi:2335':'Retain the house repair scene, question, explanation and actually worded closer-matter answer. The Hindi old synonym for worn-out is lexical context. The parenthetic death interpretation of the word matter is explanatory gloss in both languages, not an added exact word of the speaker. Compiler grade/Urdu footnote are context.',
 'tirmidhi:2342':'Retain the arrival, actual recited Quran opening, repeated my-wealth claim and all three charity/eating/wearing alternatives. Do not fill the rest of the surah. Compiler evaluation and inline Urdu footnote are apparatus.',
 'tirmidhi:2350':'Preserve all three declarations, both warnings, conditional love, poverty preparation and the flood-speed comparison. Hindi has an omitted connective before the person clause; preserve the damage. Parenthetic garment only glosses the existing sackcloth term and is context.',
 'tirmidhi:2356':'Retain Masruq\'s visit, served food, Aisha\'s weeping and memory explanation. Hindi stops after a damaged statement about the Prophet\'s death; Urdu alone supplies the oath and never-being-full-of-bread-and-meat-twice-in-one-day clause. Never import that Urdu clause into Hindi. Compiler grade remains context.',
 'tirmidhi:2357':'Keep the complete two-consecutive-days, barley-bread, satiety and until-death limits. Compiler grading and parallel-report note stay context.',
 'tirmidhi:2358':'Keep the Prophet plus household subject and all three-consecutive-days, wheat-bread, satiety and until-death limits. Compiler grading stays context.',
 'tirmidhi:2359':'Retain the observation that barley bread did not exceed household needs; the household parenthesis is the actual scope of the need and remains. Entire appended grading/transmitter biographies are commentary, not new historical reports merely because they are finite clauses.',
 'tirmidhi:2363':'Retain both table/platform and fine-flour-bread statements through death. The printed or-table parenthesis supplies an alternative object and should not be automatically deleted as a synonym. Compiler grade/chain evaluation stay context.',
 'tirmidhi:2365':'Retain Saad\'s actual first-blood/first-arrow claims, collective hardship, food limitation and bodily comparison, Banu Asad criticism and conditional self-response. Parenthetic killed-a-disbeliever interprets the blood statement and the thorny-fruit phrase defines habla; both are explanatory glosses, not extra exact speech. Compiler evaluation/Urdu footnote stay context.',
 'tirmidhi:2366':'Retain the named Saad account, Arab-first-arrow claim, actual two food sources, bodily comparison, present Banu Asad criticism and conditional response. The printed Abi Waqqas parenthesis is narrator framing/identity, not an invented second actor. Compiler grade, parallel note and Urdu footnote remain context.',
 'tirmidhi:2367':'Keep Ibn Sirin\'s eyewitness setting, dyed linen, nose wiping, self-address and Abu Hurayra\'s entire hunger/fainting/foot-on-neck memory and explicit not-mad qualification. Do not convert it into a direct Prophetic utterance. Compiler evaluation/Urdu footnote stay context.',
 'tirmidhi:2371':'Keep the actual Khandaq circumstance, hunger complaint, one-stone and two-stone observations. The Hindi second unveiling lacks an explicit actor that Urdu supplies; preserve the source defect and qualify the unresolved subject without filling it. Compiler evaluation is context.',
 'tirmidhi:2372':'Retain Numan\'s contrast with current eating/drinking and his observation that even poor dates were unavailable in a sufficient amount. Keep the comparative quantity qualification; compiler grade stays context.',
 'tirmidhi:2377':'Preserve the mat, marks, offered bedding and actual rider/tree/shade analogy. Hindi has damaged words at the departure transition; do not repair it from Urdu. Compiler grading and parallel-report list are context.'
}

base=WORK/'phase16-checkpoint5589-abudawud-tirmidhi25-review/input/full-field-reading-input-53.jsonl'
extra=ROOT/'input/additional-abudawud2330-2331-source-fields.jsonl'
assert sha(base.read_bytes())=='d669acad2ae59f3da9fdfedf48fcc5e3a5167c3ec6611a795ef678d56c65d11b'
assert sha(extra.read_bytes())=='5c3c20c68f830e7d39c1ee760b1a43b51760dbeb9fca8ced02a5dd979e35981a'
fields=[json.loads(x) for p in [base,extra] for x in p.read_bytes().splitlines()]
assert len(fields)==59 and len({(f['key'],f['language']) for f in fields})==59
all_source=WORK/'phase15-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl'
assert sha(all_source.read_bytes())=='4a4000d46dba9cff36695a62e7e5207af8f5183644141e8ca23b047e62434490'
sources={r['collection']+':'+r['number']:r for r in map(json.loads,all_source.read_bytes().splitlines()) if r['collection']+':'+r['number'] in NOTES}
assert len(sources)==len(NOTES)==25
evidence=json.loads((EVID/'evidence-manifest.json').read_bytes());entries=json.loads((EVID/'held-state-entries.json').read_bytes())
assert evidence['saved_head']==PIN
checks=[]
for key,saved in sources.items():
    files=[]
    for kind,d in [('raw',saved['snapshot']),('parsed',entries[key]['parsed'])]:
        stored=(EVID/'sources'/d['path']).read_bytes();authority=evidence['files'][d['path']]
        git=hashlib.sha1(b'blob '+str(len(stored)).encode()+b'\0'+stored).hexdigest()
        assert sha(stored)==authority.get('stored_sha256',authority['sha256']) and git==authority['git_blob_sha1']
        plain=importer.checked_bytes(EVID/'sources',d)
        if kind=='raw':
            obj,cite=importer.parse_record(plain,saved['collection'],saved['number'])
            assert obj==saved['source_record'] and cite==saved['source_reference_verbatim']
        else:
            parsed=json.loads(plain)
            for name in ['collection','number','source_record','source_reference_verbatim','snapshot']:assert parsed[name]==saved[name]
        files.append({'kind':kind,'path':d['path'],'bytes':len(stored),'sha256':sha(stored),'git_blob_sha1':git,'original_sha256':sha(plain)})
    checks.append({'id':'deenhindi-'+key,'files':files,'raw_reparse_exact':True,'parsed_original_metadata_exact':True})
for f in fields:
    assert f['text']==sources[f['key']]['source_record'][f['source_field']]
    assert sha(f['text'].encode())==f['sha256']
    f['complete_own_field_read']=True;f['independent_reading_note']=NOTES[f['key']]
receipt={'source_commit':PIN,'reviewer':'/root','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'complete_source_fields':len(fields),'characters':sum(len(f['text']) for f in fields),'utf8_bytes':sum(len(f['text'].encode()) for f in fields),
    'candidate_inspected':False,'candidate_notes_inspected':False,'full_fields_read_before_candidate':True,
    'scope':'All50 Hindi/Urdu original fields plus all3 other supplied fields for each Tirmidhi2296, AbuDawud2330 and2331. The additional6 were read to test independently suspected lexical-only source records.',
    'source_files_verified':50,'raw_reparses_exact':25,'fields':fields,
    'initial_findings':'Tirmidhi2296 supplies apparatus only. AbuDawud2330/2331 supply lexical definitions only in all five languages and should remain source context under AGENTS. AbuDawud2306 appended Ibn Shihab legal opinion and the identified lexical glosses must not be promoted into matn. Final comparison with the candidate remains pending.',
    'independent_pro_qc':'not_performed'}
for n,v in [('complete-independent-source-first-readings.json',receipt),('independent-source-proof.json',{'source_commit':PIN,'rows':checks,'files_verified':50,'reparses':25})]:
    p=ROOT/n;assert not p.exists();p.write_bytes(enc(v));print(n,sha(p.read_bytes()))
print(json.dumps({k:receipt[k] for k in ['complete_source_fields','characters','utf8_bytes','candidate_inspected']}))
