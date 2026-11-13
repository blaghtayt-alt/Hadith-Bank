#!/usr/bin/env python3
"""Freeze the manually read20-parent package after exact native/source validation."""
from pathlib import Path
import collections,gzip,hashlib,json,re
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'publish-v2'
COHORT='checkpoint3e574-abudawud-tirmidhi-bukhari-ibnmajah20-20261113';PREFIX='imports/web-deenhindi-20261112/reviews/'+COHORT;ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-'+COHORT+'.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest();blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,b):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);return {'path':path,'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)}
RETAINED={
 ('abudawud:2521','hi','(नाबालिग)'):'Age restriction of the actual category supplied in the reply; do not broaden the source by dropping it.',
 ('abudawud:2521','ur','( نابالغ )'):'Age restriction of the actual category in this own reply, distinct from the other source-supplied categories.',
 ('abudawud:2535','hi','(भी)'):'Printed additive qualification in the actual negative prayer; it is not a lexical definition or locator.',
 ('abudawud:2535','ur','( بھی )'):'Printed additive qualification in the actual negative prayer, preserved without expanding its scope.',
 ('abudawud:2535','hi','(के ज़ुहूर का वक़्त)'):'Source-rendered occurrence-time qualification of the stated future events; retain its conditional temporal scope.',
 ('abudawud:2535','ur','( کے ظہور کا وقت )'):'Actual source-rendered timing qualification in the conditional future statement, not a new forecast by this review.',
 ('tirmidhi:2502','hi','(और उन्होंने हाथ से इशारा किया कि वो पस्त-क़द हैं)'):'Finite narrated hand action and its stated indication; removing this parenthesis would remove actual incident content.',
 ('tirmidhi:2516','hi','(तक़दीर के)'):'Source-rendered object/domain qualification of the scrolls in the actual supplied counsel; no claim about literal historical bracketed diction.',
 ('tirmidhi:2516','ur','( تقدیر کے )'):'Source-rendered domain of the scrolls in the actual conclusion, retained without external wording or a new interpretation.',
 ('bukhari:2536','hi','(के आज़ादी के बाद वह उन्हीं के हक़ में क़ाइम रहे गी)'):'Actual post-emancipation beneficiary and timing content of the imposed wala condition; the defective surrounding Hindi is not repaired.',
 ('bukhari:2536','ur','( کہ آزادی کے بعد وہ انہیں کے حق میں قائم رہے گی )'):'Actual retained-wala condition with beneficiary and after-emancipation scope; preserve the source contract wording.',
}

def main():
 assert not (ROOT/'delivery-manifest-v2.json').exists()
 raw=(OUT/ACTIVE).read_bytes();assert sha(raw)=='fdb476dd97b56d51a29c644835c81ba886e4dcb52680d819cb5b259db280e9d5';d=json.loads(gzip.decompress(raw));v=json.loads((OUT/PREFIX/'validation.json').read_bytes());t=v['totals']
 assert t['source_occurrences']==t['register']==20 and t.get('exclude',0)==0 and t['complete_fields_read']==t['admitted_language_fields']==40 and t['unread_context_fields']==60
 fields=json.loads(gzip.decompress((OUT/PREFIX/'complete-field-readings-and-boundaries.json.gz').read_bytes()))['fields'];assert len(fields)==40
 items=[];used=set();counts=collections.Counter();boundaryview=[]
 for f in fields:
  text=f['text'];mask={i for s in f['selected_spans'] for i in range(s['start'],s['end'])};stack=[]
  assert all(s['text'].strip() and '؎' not in s['text'] for s in f['selected_spans'])
  assert all(s['text'].strip() for s in f['retained_context'])
  for i,ch in enumerate(text):
   if ch=='(':stack.append(i)
   elif ch==')' and stack:
    a=stack.pop();b=i+1
    if not set(range(a,b))<=mask:continue
    literal=text[a:b];key=(f['occurrence_id'].removeprefix('deenhindi-'),f['language'],literal)
    if key in RETAINED:reason=RETAINED[key];category='individually_read_narrative_qualification';used.add(key);counts['narrative_qualifications']+=1
    else:
     assert re.fullmatch(r'\((?:सल्लल्लाहु|रज़ियल्लाहु|रज़ियल्लाहु|रदि अल्लाहु|रदी अल्लाहु|रज़ि अल्लाहु|\s*صلی اللہ)[^()]*\)',literal),(key,literal)
     reason='Exact printed source honorific, read and preserved without normalization.';category='source_honorific';counts['honorifics']+=1
    items.append({'id':f['occurrence_id'],'language':f['language'],'field_sha256':f['text_sha256'],'start':a,'end':b,'text':literal,'sha256':sha(literal.encode()),'category':category,'reason':reason})
  boundaryview.append({'id':f['occurrence_id'],'language':f['language'],'text':text,'reason':f['actual_field_review']['reason'],'selected_spans':f['selected_spans'],'retained_context':f['retained_context']})
 assert used==set(RETAINED) and counts['narrative_qualifications']==11
 cuts=json.loads((OUT/PREFIX/'explicit-source-apparatus-context.json').read_bytes());assert cuts['literal_omissions']==5
 put(PREFIX+'/retained-source-parentheses.json',enc({'scope':'Each non-honorific selected parenthesis has an individually authored reason. This inventory is evidence of completed readings, not an automatic admission rule.','counts':dict(counts),'items':items,'selected_footnotes':0,'selected_explicit_verse_locator_labels':0,'whitespace_only_selected_or_context_fragments':0}))
 (ROOT/'boundary-view-v2.json').write_bytes(enc(boundaryview))
 report={'amendment_receipt_path':PREFIX+'/independent-chain-context-v2/amendment-receipt.json','revision':'v2 after four exact independently agreed chain-prefix cuts; parent final hash-bound audit remains separate','schema':'hadith-bank-source-bound-primary-review-v1','result':'PASS','source_commit':d['source_checkpoint'],'cohort':'Exactly20 new3e574 occurrences:4 AbuDawud,11 Tirmidhi,2 Bukhari and3 IbnMajah. The other three assigned next80 groups are disjoint.','source_worker_run_id':43458763961,'artifact_id':14059470494,'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(raw),'source_baseline_path':d['source_ledger_path'],'source_baseline_sha256':d['source_ledger_sha256'],'source_first_receipt_sha256':'5531d8749a00a62ac22c5e6b677d72c33679db38a776a525e6c9e70cfea5cefa','source_first_notes_sha256':'30b93e16987332c469c32e9ce9e62b56dc9f8bb2c29cfdb5b64cb8a24dd5a9ed','actual_readings':{'full_fields':40,'characters':17859,'utf8_bytes':38456,'admitted':40,'reviewed_context_only':0,'unread_siblings':60,'empty_siblings':0},'dispositions':{'registered':20,'source_only':0,'unresolved':0},'native_validation':v,'literal_context_cuts_inside_components':5,'retained_parentheses':dict(counts),'source_fields_reopened':40,'exact_raw_reparses':20,'scope_qualifications':[
 'Abu2492 admits the supplied abbreviated sleep/hair/question/no encounter; its absent continuation and compiler identity explanation remain context.',
 'Abu2521 keeps the unknown uncle and each own list, including the source-rendered age restriction; Hindi’s absent martyr category is not borrowed.',
 'Tirm2464 and2471 are actual Companion reflection/household testimony;2473 is Ali’s actual personal action/dialogue account. None becomes direct Prophetic speech.',
 'Tirm2480 is an independently supplied substantive Ibrahim/AbuHamzah scholarly dialogue with actual necessity question/reply, qualified without Prophetic attribution or contemporary legal advice.',
 'Tirm2475 keeps its actual interrupted question/reply and resumed mission in three components sharing one family; the eighteen-day quantity is exact.',
 'Tirm2485 separates the witness’s event-specific personal recognition from the explicitly introduced Prophetic address.',
 'Tirm2502 retains the finite hand gesture and its supplied meaning qualification. Tirm2516 retains the source-rendered destiny-scrolls domain while grade/footnote apparatus stays context.',
 'Bukhari2536 keeps its actual contract condition and four ordered voices in one continuous source family, without filling Hindi’s damaged name, route or wala link from Urdu.',
 'IbnMajah2513 preserves the source-defective Hindi purchaser wording without importing Urdu’s BanuAdi affiliation. All names, numbers, grades, references, script values and raw source bytes remain unchanged.'
 ],'peer_notes_inspected_before_primary_freeze':False,'source_http_requests':0,'github_writes':0,'shared_engine_changes':0,'independent_pro_qc':'not_performed','certified_release_eligible':False,'limitations':'Primary complete own-field review with exact local SourceReviews apply/finish, original-source reparse and metadata/partition validation. Independent second reading, combined repository export and actual reader/deployment remain separate gates.'}
 put('reports/web-source-resolution-20261113/checkpoint3e574-mixed20-primary-review.json',enc(report));put(PREFIX+'/package_review.py',Path(__file__).read_bytes())
 def inventory(local=False):
  files=[]
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and (local or p.relative_to(OUT).as_posix()!=PREFIX+'/portable-manifest.json'):
    b=p.read_bytes();f={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob(b)}
    if local:f['local_path']=str(p)
    files.append(f)
  return files
 files=inventory();put(PREFIX+'/portable-manifest.json',enc({'schema':'hadith-bank-portable-review-package-v1','source_commit':d['source_checkpoint'],'active_ledger_sha256':sha(raw),'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}))
 files=inventory(True);m={'schema':'hadith-bank-source-review-delivery-v1','source_commit':d['source_checkpoint'],'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(raw),'source_baseline_sha256':d['source_ledger_sha256'],'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)};mb=enc(m);(ROOT/'delivery-manifest-v2.json').write_bytes(mb)
 print(json.dumps({'status':'FROZEN','manifest_sha256':sha(mb),'active_ledger_sha256':sha(raw),'files':len(files),'bytes':m['total_bytes'],'dispositions':report['dispositions'],'actual_readings':report['actual_readings'],'retained_parentheses':dict(counts)},indent=2))

if __name__=='__main__':main()
