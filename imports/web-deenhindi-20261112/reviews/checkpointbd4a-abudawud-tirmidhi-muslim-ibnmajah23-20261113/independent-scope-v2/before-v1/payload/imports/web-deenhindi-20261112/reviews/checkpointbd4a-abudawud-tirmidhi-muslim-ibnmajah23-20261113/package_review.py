"""Freeze the explicitly reviewed23-parent package; no network or shared-engine changes."""
from pathlib import Path
import collections,gzip,hashlib,json,re
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'publish-v1'
COHORT='checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-20261113'
PREFIX='imports/web-deenhindi-20261112/reviews/'+COHORT
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-'+COHORT+'.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,data):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return {'path':path,'bytes':len(data),'sha256':sha(data),'git_blob_sha1':blob(data)}
RETAINED={
 ('abudawud:2385','hi','(तो क्या हुआ)'):'Finite rhetorical consequence within the actual mouth-rinse question.',
 ('abudawud:2385','ur','( تو کیا ہوا )'):'Finite rhetorical consequence within the actual mouth-rinse question.',
 ('tirmidhi:2434','hi','(आगे रसूलुल्लाह (सल्लल्लाहु अलैहि वसल्लम) फ़रमाते हैं)'):'Explicit source identification of the actor who resumes the following first-person intercession speech.',
 ('tirmidhi:2434','ur','( آگے رسول اللہ صلی اللہ علیہ وسلم فرماتے ہیں )'):'Explicit source identification of the actor who resumes the following first-person intercession speech.',
 ('muslim:2465','hi','(जैसे)'):'Actual resemblance qualifier of the supplied hand description, not an inferred anatomy.',
 ('muslim:2465','ur','( جیسے )'):'Actual resemblance qualifier of the supplied hand description, not an inferred anatomy.',
 ('muslim:2465','hi','(उबैदह ने)'):'Source-supplied identification of the actual questioner.',
 ('muslim:2465','ur','( عبیدہ نے )'):'Source-supplied identification of the actual questioner.',
 ('muslim:2465','hi','(वादा बराह-ए-रास्त)'):'Source-supplied promise/direct-hearing qualification of the actual question; the hidden promise content is not filled.',
 ('muslim:2465','ur','( وعدہ برا راست )'):'Source-supplied promise/direct-hearing qualification of the actual question; the hidden promise content is not filled.',
 ('ibnmajah:2449','hi',"(हिबा या मुस्तआ'र)"):'Source-specified alternative legal modes of the second cultivating category’s land grant; the printed OR is preserved without choosing a mode.',
 ('ibnmajah:2449','ur','( ہبہ یا مستعار )'):'Source-specified alternative legal modes of the second cultivating category’s land grant; the printed OR is preserved without choosing a mode.'}

def main():
 assert not (ROOT/'delivery-manifest-v1.json').exists(), 'Candidate already frozen'
 active=(OUT/ACTIVE).read_bytes();assert sha(active)=='1ae17b3b034812f8c40789881abd9d0184bbdb57c3c58a3eb09e682116b04fe8'
 ledger=json.loads(gzip.decompress(active));validation=json.loads((OUT/PREFIX/'validation.json').read_bytes())
 fields=json.loads(gzip.decompress((OUT/PREFIX/'complete-field-readings-and-boundaries.json.gz').read_bytes()))['fields']
 assert len(fields)==55 and validation['totals']['register']==20 and validation['totals']['exclude']==3
 inventory=[];counts=collections.Counter();used=set()
 for f in fields:
  text=f['text'];mask={i for s in f['selected_spans'] for i in range(s['start'],s['end'])};stack=[]
  assert all(s['text'].strip() and '؎' not in s['text'] for s in f['selected_spans'])
  assert all(s['text'].strip() for s in f['retained_context'])
  for i,ch in enumerate(text):
   if ch=='(':stack.append(i)
   elif ch==')' and stack:
    start=stack.pop();end=i+1
    if not set(range(start,end))<=mask:continue
    literal=text[start:end];binding=(f['occurrence_id'].removeprefix('deenhindi-'),f['language'],literal)
    if re.fullmatch(r'\((?:सल्लल्लाहु|रज़ियल्लाहु|रदी अल्लाहु|रज़ि अल्लाहु|अलैहिस|अलैहा)[^()]*\)',literal):
     category='source_honorific';reason='Printed honorific read and retained exactly.';counts['retained_honorific_parentheses']+=1
    else:
     assert binding in RETAINED,binding;used.add(binding);category='individually_reviewed_narrative_qualification';reason=RETAINED[binding];counts['retained_narrative_parentheses']+=1
    inventory.append({'id':f['occurrence_id'],'language':f['language'],'source_text_sha256':f['text_sha256'],'start':start,'end':end,'text':literal,'sha256':sha(literal.encode()),'category':category,'reason':reason})
 assert used==set(RETAINED) and counts=={'retained_honorific_parentheses':77,'retained_narrative_parentheses':12}
 cuts=json.loads((OUT/PREFIX/'explicit-source-apparatus-context.json').read_bytes());assert cuts['literal_omissions']==34
 put(PREFIX+'/retained-source-parentheses.json',enc({'scope':'Each selected non-honorific parenthesis has the individually authored reason below. This inventory adds no admission or removal rule.','counts':dict(counts),'items':inventory,'selected_footnote_markers':0,'selected_explicit_verse_locator_labels':0,'whitespace_only_selected_or_context_fragments':0}))
 report={'schema':'hadith-bank-source-bound-primary-review-v1','result':'PASS','source_checkpoint':ledger['source_checkpoint'],'source_worker_run_id':43450869489,'artifact_id':14055391183,
  'cohort':'Exactly23 of the92 newly held bd4a occurrences:8 AbuDawud,9 Tirmidhi,4 Muslim and2 IbnMajah. Other three assigned groups are disjoint.',
  'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),'source_baseline_path':ledger['source_ledger_path'],'source_baseline_sha256':ledger['source_ledger_sha256'],
  'source_first_reading_receipt_sha256':'52b2a84ab340b78e4521fb482e89b989889ece6d0d11c5a87189ea9ba2fdef65','source_first_original_packet_sha256':'b5a039a0a9ca5a667dd70c4060925f13122faa8e1af21eef8beff6b54fec0c9b',
  'actual_readings':{'complete_fields':55,'characters':34118,'utf8_bytes':70795,'admitted_fields':40,'read_context_fields':15,'unread_nonempty_sibling_fields':58,'actual_empty_sibling_fields_preserved':2},
  'parent_dispositions':{'register':20,'source_only':3,'unresolved':0},'source_only_ids':['deenhindi-abudawud:2423','deenhindi-muslim:2464','deenhindi-muslim:2466'],'source_only_all_five_fields_completely_read':True,
  'native_and_source_validation':validation,'explicit_literal_context_cuts':34,'selected_apparatus_inventory':dict(counts),'selected_footnote_labels':0,'selected_explicit_verse_locators':0,
  'scope_notes':[
   'Abu2423 is a named provenance-criticism statement about the absent Saturday-fast report. The initial primary decision preserves all five fields as source context; number and transmitter name alone do not admit underlying missing matn.',
   'Muslim2464 explicitly negates the quoted omission; it is not converted into affirmative wording. Muslim2466 supplies a hearing-assurance formula and a report pointer without the promised body.',
   'Abu2426 supplies actual finite added wording in both reviewed languages. Hindi lacks the explicit reply speaker link and remains qualified; Urdu expressly names the Messenger. Neither field is completed from the other.',
   'Muslim2474 supplies an affirmative new alms-lawfulness variant despite the same-chain pointer. The replaced comparator is context and the ultimate speaker remains unknown.',
   'Tirm2382 Hindi is substantially shorter than Urdu. Its absent dialogues and Muawiyah sequel are not filled. Urdu has three separately attributed components across the main report and historical Muawiyah-reception family, preserving actual recitation/rendering.',
   'Tirm2413 keeps Salman’s own speech separate from the final Prophetic approval in one incident family. Both source languages’ awkward Salman-ate wording is preserved.',
   'Tirm2434 is completely read in each language. Nested eschatological speakers remain part of that actual transmitted report. The explicit return-to-Messenger attribution is preserved; omitted-list pointers, word definitions and final compiler apparatus are context.',
   'Tirm2392 Arabic and English are actual empty strings; they remain empty. All source names, numbers, grades, references, script metadata and defective joins remain exact.'],
  'source_http_requests':0,'github_writes':0,'shared_engine_changes':False,'independent_pro_qc':'not_performed','certified_release_eligible':False,
  'limitations':'Primary manual review plus exact local SourceReviews apply/finish and source reparse validation. Independent second reading, whole-repository integration and actual reader publication remain separate gates. The complete bd4a saved-state audit is separately published; this packet does not invent intermediate5589 history.'}
 put('reports/web-source-resolution-20261113/checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-primary-review.json',enc(report))
 put(PREFIX+'/package_review.py',Path(__file__).read_bytes())
 def inventory(local=False):
  fs=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and (local or p.name!='portable-manifest.json'):
    b=p.read_bytes();f={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)}
    if local:f['local_path']=str(p)
    fs.append(f)
  return fs
 fs=inventory();put(PREFIX+'/portable-manifest.json',enc({'schema':'hadith-bank-portable-review-package-v1','source_checkpoint':ledger['source_checkpoint'],'active_ledger_sha256':sha(active),'files':fs,'total_files':len(fs),'total_bytes':sum(f['bytes'] for f in fs)}))
 fs=inventory(True);m={'schema':'hadith-bank-source-review-delivery-v1','source_checkpoint':ledger['source_checkpoint'],'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),'source_baseline_sha256':ledger['source_ledger_sha256'],'files':fs,'total_files':len(fs),'total_bytes':sum(f['bytes'] for f in fs)}
 (ROOT/'delivery-manifest-v1.json').write_bytes(enc(m))
 print(json.dumps({'status':'FROZEN','manifest_sha256':sha(enc(m)),'active_ledger_sha256':sha(active),'files':len(fs),'bytes':m['total_bytes'],'parent_dispositions':report['parent_dispositions'],'actual_readings':report['actual_readings'],'retained_parentheses':dict(counts)},indent=2))

if __name__=='__main__':main()
