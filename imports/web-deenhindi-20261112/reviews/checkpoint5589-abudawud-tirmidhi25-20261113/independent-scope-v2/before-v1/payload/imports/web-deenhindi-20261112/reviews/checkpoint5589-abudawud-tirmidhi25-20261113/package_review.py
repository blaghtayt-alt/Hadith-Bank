"""Freeze the25-parent source-bound primary candidate without source or Git writes."""
from pathlib import Path
import collections,gzip,hashlib,json,re
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'publish'
COHORT='checkpoint5589-abudawud-tirmidhi25-20261113'
PREFIX='imports/web-deenhindi-20261112/reviews/'+COHORT
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-'+COHORT+'.json.gz'
ACTIVE_SHA='b2f5305335c2a896ea850a2ef79b7f6b878a6f6f72e5301972c256cd1d8296af'
FIRST_SHA='42de70f584c2667487bc8eca7774b25e7fd32e8d623bd0f40de2b680ce22d9c8'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,data):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return {'path':path,'bytes':len(data),'sha256':sha(data),'git_blob_sha1':blob(data)}
HONORIFICS={'(रज़ियल्लाहु अन्हा)','(रज़ियल्लाहु अन्हु)','(रज़ियल्लाहु अन्हुम)',
 '(रदी अल्लाहु अन्हा)','(रदी अल्लाहु अन्हु)','(रज़ि अल्लाहु अन्हु)','(सल्लल्लाहु अलैहि वसल्लम)'}
RETAINED={
 ('abudawud:2310','ur','( سب سے بڑا گناہ یہ ہے کہ )'):'The source places this answer-ranking frame directly after the Messenger-said introduction; it is retained as that supplied frame, not a new speaker or external explanation.',
 ('abudawud:2352','ur','( سواری سے )'):'Sole own-field vehicle-from qualifier of the actual descent instruction.',
 ('tirmidhi:2359','hi','(अहल-ए-खाना की)'):'Specifies whose need defines the actual bread-quantity statement.',
 ('tirmidhi:2359','ur','( اہل خانہ کی )'):'Specifies whose need defines the actual bread-quantity statement.',
 ('tirmidhi:2366','hi','(अबी वक़्क़ास)'):'Source-supplied identification of the actual named first-person speaker.',
 ('tirmidhi:2366','ur','(ابی وقاص)'):'Source-supplied identification of the actual named first-person speaker.',
 ('tirmidhi:2371','hi','(जंग-इ-ख़ंदक़ के दौरान)'):'Source-supplied timing of the actual hunger complaint; no external historical dating is added.',
 ('tirmidhi:2371','ur','( جنگ خندق کے دوران )'):'Source-supplied timing of the actual hunger complaint; no external historical dating is added.'}

def main():
 active=(OUT/ACTIVE).read_bytes();assert sha(active)==ACTIVE_SHA
 ledger=json.loads(gzip.decompress(active))
 sources={r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress((OUT/ledger['source_ledger_path']).read_bytes()).splitlines())}
 first=(ROOT/'complete-source-first-readings.json').read_bytes();assert sha(first)==FIRST_SHA
 firstdoc=json.loads(first);notes={(r['key'],r['language']):r for r in firstdoc['fields']}
 partitions={r['id']:r for r in json.loads(gzip.decompress((OUT/PREFIX/'field-partitions.json.gz').read_bytes()))}
 readings=[];parentheses=[];counts=collections.Counter();used=set();whitespace=[]
 for record in ledger['records']:
  key=record['id'].removeprefix('deenhindi-')
  for field in record['field_reviews']:
   lang=field['language'];text=sources[key]['source_record'][field['source_field']];note=notes[(key,lang)]
   assert note['text']==text and note['sha256']==field['text_sha256']==sha(text.encode())
   assert note['chars']==field['chars_reviewed']==len(text)
   assert note['utf8_bytes']==field['bytes_reviewed']==len(text.encode())
   selected=[{**s,'text':text[s['start']:s['end']]} for s in field['spans']]
   contexts=[{**s,'text':text[s['start']:s['end']]} for s in partitions[record['id']+':'+lang]['parts'] if s['role']=='context']
   assert all(s['text'].strip() for s in selected)
   assert not any('؎' in s['text'] or 'الخ' in s['text'] for s in selected)
   for c in contexts:
    if c['text'] and not c['text'].strip():whitespace.append({'id':record['id'],'language':lang,**c})
   mask={i for s in field['spans'] for i in range(s['start'],s['end'])}
   for m in re.finditer(r'\([^()]*\)',text):
    if set(range(m.start(),m.end()))<=mask:
     literal=m.group();binding=(key,lang,literal)
     if literal in HONORIFICS:
      category='honorific';reason='Printed honorific retained exactly.';counts['retained_honorific_parentheses']+=1
     else:
      assert binding in RETAINED,binding;used.add(binding);category='individually_reviewed_source_qualifier';reason=RETAINED[binding];counts['retained_narrative_parentheses']+=1
     parentheses.append({'id':record['id'],'language':lang,'source_text_sha256':sha(text.encode()),'start':m.start(),'end':m.end(),'text':literal,'sha256':sha(literal.encode()),'category':category,'reason':reason})
   readings.append({**note,'actual_field_review':field,'selected_spans':selected,'retained_context':contexts})
   counts.update(complete_fields_read=1,characters_read=len(text),utf8_bytes_read=len(text.encode()),selected_spans=len(selected),selected_characters=sum(len(s['text']) for s in selected))
 assert used==set(RETAINED) and len(readings)==53
 assert counts['characters_read']==24310 and counts['utf8_bytes_read']==51279
 assert counts['retained_narrative_parentheses']==8
 validation=json.loads((OUT/PREFIX/'validation.json').read_bytes())
 context=json.loads((OUT/PREFIX/'explicit-source-apparatus-context.json').read_bytes())
 counts['explicit_literal_context_cuts']=context['literal_omissions']
 put(PREFIX+'/complete-source-first-readings.json.gz',gzip.compress(first,mtime=0))
 put(PREFIX+'/source-first-notes.json',(ROOT/'source-first-notes.json').read_bytes())
 put(PREFIX+'/complete-field-readings-and-boundaries.json.gz',gzip.compress(enc({'source_commit':ledger['source_checkpoint'],'active_ledger_sha256':sha(active),'fields':readings}),mtime=0))
 put(PREFIX+'/retained-source-parentheses.json',enc({'scope':'Exact individually assessed selected parentheses; no automatic admission or removal rule.','counts':dict(counts),'items':parentheses,'selected_footnote_markers':0,'selected_explicit_verse_locators':0,'whitespace_only_context_gaps':whitespace}))
 report={'schema':'hadith-bank-source-bound-primary-review-v1','result':'PASS','source_checkpoint':ledger['source_checkpoint'],'source_worker_run_id':43443662972,
  'cohort':'Exactly25 of100 newly acquired5589 held entries:8 AbuDawud and17 Tirmidhi; disjoint from prior0639 imports and old117 holds.',
  'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),'source_baseline_path':ledger['source_ledger_path'],'source_baseline_sha256':ledger['source_ledger_sha256'],
  'source_first_receipt_sha256':sha(first),'actual_reading':dict(counts),'native_and_source_validation':validation['totals'],'by_book':validation['by_book'],'by_language':validation['by_language'],
  'parent_decisions':{'register':24,'source_only':1,'unresolved':0},'source_only_ids':['deenhindi-tirmidhi:2296'],
  'source_only_all_nonempty_fields_read':True,'admitted_fields':48,'read_context_fields':5,'unread_sibling_fields_retained_context':72,
  'script_and_language_metadata_changes':0,
  'source_limit_notes':[
   'Abu2368 supplies a finite walking-with-the-Prophet frame only; the hanging speech introduction and preceding-report pointer remain context.',
   'Abu2330 and2331 contain actual transmitted named scholarly lexical sayings; no Prophetic status is supplied. The2331 compiler unnamed alternatives remain context.',
   'Tirmidhi2356 Hindi omits the Urdu bread/meat/frequency clause, which is not filled.',
   'Tirmidhi2371 Hindi lacks the second garment-lifting actor link; its actual printed sequence remains qualified, with no Urdu words transferred.',
   'Tirmidhi2377 Hindi has damaged departure wording, retained exactly.'],
  'report_family_notes':{
   'abudawud:2306':'Two independently attributed families: Subayah correspondence account and IbnShihab own legal opinion.',
   'abudawud:2310':'Two ordered voices in one account: direct Messenger Q&A and the following narratorial revelation confirmation/actual recitation.',
   'tirmidhi:2356':'Masruq encounter and Aisha retrospective memory are distinct voice components of one narrated encounter.',
   'tirmidhi:2367':'IbnSirin witness framing and AbuHurayra actual retrospective speech are distinct voice components of one encounter.'},
  'preservation_notes':['All original source words, numbers, references, grades and script metadata remain exactly reconstructible.','Actual recitations and translations are retained; explicit locators, footnotes, omitted-continuation pointers and individually assessed lexical apparatus remain context.','No canonical identity is filled from another language or occurrence.'],
  'source_http_requests':0,'github_writes':0,'engine_changes':False,'independent_pro_qc':'not_performed','certified_release_eligible':False,
  'limits':'Primary source-bound review and local native validation only. The complete5589 saved-state history remains unavailable; this package makes no full-state audit claim. Independent second reading, combined integration, full repository export and actual deployment remain separate gates.'}
 put('reports/web-source-resolution-20261113/checkpoint5589-abudawud-tirmidhi25-primary-review.json',enc(report))
 put(PREFIX+'/package_review.py',Path(__file__).read_bytes())
 def inventory(local=False):
  files=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and (local or p.name!='portable-manifest.json'):
    item={'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'git_blob_sha1':blob(p.read_bytes())}
    if local:item['local_path']=str(p)
    files.append(item)
  return files
 files=inventory()
 put(PREFIX+'/portable-manifest.json',enc({'schema':'hadith-bank-portable-review-package-v1','source_checkpoint':ledger['source_checkpoint'],'active_ledger_sha256':sha(active),'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}))
 files=inventory(True)
 manifest={'schema':'hadith-bank-source-review-delivery-v1','source_checkpoint':ledger['source_checkpoint'],'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),'source_baseline_sha256':ledger['source_ledger_sha256'],'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
 (ROOT/'delivery-manifest-v1.json').write_bytes(enc(manifest))
 print(json.dumps({'status':'FROZEN','manifest_sha256':sha(enc(manifest)),'active_sha256':sha(active),'files':len(files),'bytes':manifest['total_bytes'],'actual_reading':dict(counts),'whitespace_only_context_gaps':len(whitespace)},indent=2))
if __name__=='__main__':main()
