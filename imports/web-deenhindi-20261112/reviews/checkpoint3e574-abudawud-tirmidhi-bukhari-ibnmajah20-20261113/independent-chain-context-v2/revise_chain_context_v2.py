#!/usr/bin/env python3
"""Archive v1 and separate exactly four independently read prefatory chains."""
from pathlib import Path
import collections,copy,gzip,hashlib,json,pprint,subprocess,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import manual_boundaries
PREFIX='imports/web-deenhindi-20261112/reviews/checkpoint3e574-abudawud-tirmidhi-bukhari-ibnmajah20-20261113'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpoint3e574-abudawud-tirmidhi-bukhari-ibnmajah20-20261113.json.gz'
OLD=ROOT/'publish-v1';OUT=ROOT/'publish-v2';REV=PREFIX+'/independent-chain-context-v2'
AUDIT=ROOT.parent/'phase19-checkpoint3e574-mixed20-independent-audit'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 q=OUT/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
def positions(f):return {i for s in f['spans'] for i in range(s['start'],s['end'])}
def label(f,i):return {k:v for k,v in next(s for s in f['spans'] if s['start']<=i<s['end']).items() if k not in ('start','end','sha256')}
def main():
 assert not OUT.exists() and not (ROOT/'delivery-manifest-v2.json').exists()
 mb=(ROOT/'delivery-manifest-v1.json').read_bytes();assert sha(mb)=='313c1d051177932acbc232ee47b8314fcb7966f9da122367017d678ef29dd9b4'
 manifest=json.loads(mb)
 for f in manifest['files']:
  b=(OLD/f['path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes'];put(REV+'/before-v1/payload/'+f['path'],b)
 put(REV+'/before-v1/delivery-manifest-v1.json',mb)
 for name,expected in [('independent-boundary-findings-v1.json','82c89c1115ace1ebdebe66e1a4e7e5a2fc59abcb2908b9cb85f22ae71f452e8f'),('accepted-reviewed-field-plan.json','8504ff231b3c93c2c68f9321a33d9dfe877e6dfa31fd8b6e30c40bcdb87fce45')]:
  b=(AUDIT/name).read_bytes();assert sha(b)==expected;put(REV+'/'+name,b)
 findings=json.loads((OUT/REV/'independent-boundary-findings-v1.json').read_bytes())
 plan=json.loads((OUT/REV/'accepted-reviewed-field-plan.json').read_bytes())
 changes={(f['id'].removeprefix('deenhindi-'),f['language']):f for f in findings['findings']}
 assert len(changes)==4 and sum(f['characters'] for f in changes.values())==597 and sum(f['utf8_bytes'] for f in changes.values())==1272
 sources={r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_bytes().splitlines())}
 records=copy.deepcopy(manual_boundaries.records)
 for row in records:
  for language,field in row['fields'].items():
   key=(row['key'],language)
   if key not in changes:continue
   change=changes[key];text=sources[row['key']]['source_record'][{'hi':'translationHindi','ur':'translationUrdu'}[language]]
   assert sha(text.encode())==change['source_text_sha256'] and text[:change['end']]==change['text'] and change['start']==0
   start=text[change['end']:change['end']+45];assert text.count(start)==1 and field['spans'][0]['from'] is None
   field['spans'][0]['from']=start
   field['reason']+=' V2 independently reviewed refinement: the exact prefatory transmission route is retained separately as source context, while the last reporter’s actual framing or first-person account begins the selected body. Existing speaker, component, type and family metadata remain unchanged, including all source-qualified damaged-name limits. The complete original reading and prior selection remain archived rather than rewritten.'
 (ROOT/'manual_boundaries_v2.py').write_text('"""Four exact prefatory-chain cuts; immutable initial readings remain archived."""\nrecords = '+pprint.pformat(records,width=110,sort_dicts=False)+'\n',encoding='utf-8')
 script=(ROOT/'compile_review.py').read_text().replace('from manual_boundaries import records as instructions','from manual_boundaries_v2 import records as instructions').replace("OUT=ROOT/'publish-v1'","OUT=ROOT/'publish-v2'").replace('delivery-manifest-v1.json','delivery-manifest-v2.json')
 script=script.replace("for n in ('source_first_notes.py','manual_boundaries.py','compile_review.py'):put(PREFIX+'/'+n,(ROOT/n).read_bytes())","for target,source in (('source_first_notes.py','source_first_notes.py'),('manual_boundaries.py','manual_boundaries_v2.py'),('compile_review.py','compile_review_v2.py')):put(PREFIX+'/'+target,(ROOT/source).read_bytes())")
 script=script.replace('Initial primary20register/0source-only','Version2 primary20register/0source-only after four independently agreed prefatory-chain context cuts')
 (ROOT/'compile_review_v2.py').write_text(script)
 subprocess.run([sys.executable,str(ROOT/'compile_review_v2.py')],check=True)
 before=json.loads(gzip.decompress((OLD/ACTIVE).read_bytes()));after=json.loads(gzip.decompress((OUT/ACTIVE).read_bytes()))
 oldrows={r['id']:r for r in before['records']};newrows={r['id']:r for r in after['records']};assert oldrows.keys()==newrows.keys()
 expected={(f['id'],f['language']):f for f in plan['reviewed_fields']}
 unchanged_fields=whole_unchanged=removed=prior_selected=0;proof=[]
 for rid,a in oldrows.items():
  b=newrows[rid];assert {k:v for k,v in a.items() if k!='field_reviews'}=={k:v for k,v in b.items() if k!='field_reviews'}
  if a==b:whole_unchanged+=1
  for old,new in zip(a['field_reviews'],b['field_reviews'],strict=True):
   key=(rid,new['language']);assert new['spans']==expected[key]['expected_spans'] and new['text_sha256']==old['text_sha256']==expected[key]['source_text_sha256']
   prior_selected+=len(positions(old));cut=changes.get((rid.removeprefix('deenhindi-'),new['language']))
   if cut:
    assert {k:v for k,v in old.items() if k not in ('spans','reason')}=={k:v for k,v in new.items() if k not in ('spans','reason')}
    assert positions(new)<=positions(old) and positions(old)-positions(new)==set(range(cut['start'],cut['end']))
    for i in positions(new):assert label(old,i)==label(new,i)
    removed+=len(positions(old)-positions(new));proof.append({'id':rid,'language':new['language'],'before_reason':old['reason'],'after_reason':new['reason'],'remaining_selected_labels_unchanged':True})
   else:assert old==new;unchanged_fields+=1
 assert (unchanged_fields,whole_unchanged,removed,prior_selected)==(36,18,597,16776)
 assert before['source_ledger_sha256']==after['source_ledger_sha256']
 assert sha((ROOT/'complete-source-first-readings.json').read_bytes())=='5531d8749a00a62ac22c5e6b677d72c33679db38a776a525e6c9e70cfea5cefa'
 assert sha((ROOT/'source_first_notes.py').read_bytes())=='30b93e16987332c469c32e9ce9e62b56dc9f8bb2c29cfdb5b64cb8a24dd5a9ed'
 for f in manifest['files']:assert (OLD/f['path']).read_bytes()==(OUT/REV/'before-v1/payload'/f['path']).read_bytes()
 receipt={'schema':'hadith-bank-source-chain-context-amendment-v2','result':'PASS','source_checkpoint':after['source_checkpoint'],'before_manifest_sha256':sha(mb),'before_active_sha256':sha((OLD/ACTIVE).read_bytes()),'after_active_sha256':sha((OUT/ACTIVE).read_bytes()),'exact_changes':findings['findings'],'changed_reasons':proof,'chain_prefixes':4,'selected_characters_moved_to_context':597,'utf8_bytes_moved_to_context':1272,'restored_characters':0,'isolated_whitespace_changes':0,'remaining16179_selected_positions_and_component_type_speaker_family_exact':True,'unchanged_reviewed_fields':36,'unchanged_whole_parents':18,'unchanged_unread_nonempty_slots':60,'parent_dispositions_unchanged':{'register':20,'source_only':0},'all40_final_fields_match_root_accepted_plan':True,'all21_v1_payloads_and_manifest_archived_and_rehashed':True,'initial_notes_and_source_first_receipt_unchanged':True,'source_http_requests':0,'github_writes':0,'canonical_identity_fills':0,'independent_pro_qc':'not_performed','final_independent_hash_bound_gate':'pending_parent'}
 put(REV+'/amendment-receipt.json',enc(receipt));put(REV+'/revise_chain_context_v2.py',Path(__file__).read_bytes())
 packaging=(ROOT/'package_review.py').read_text().replace("OUT=ROOT/'publish-v1'","OUT=ROOT/'publish-v2'").replace('delivery-manifest-v1.json','delivery-manifest-v2.json').replace('boundary-view-v1.json','boundary-view-v2.json').replace('a667f1881c9731b51ea59be17a148558decb3423d812496b4acfaf78e458b104',sha((OUT/ACTIVE).read_bytes()))
 packaging=packaging.replace("report={'schema'","report={'amendment_receipt_path':PREFIX+'/independent-chain-context-v2/amendment-receipt.json','revision':'v2 after four exact independently agreed chain-prefix cuts; parent final hash-bound audit remains separate','schema'")
 (ROOT/'package_review_v2.py').write_text(packaging)
 subprocess.run([sys.executable,str(ROOT/'package_review_v2.py')],check=True)
 print(json.dumps({'amendment_receipt_sha256':sha((OUT/REV/'amendment-receipt.json').read_bytes()),'unchanged_fields':unchanged_fields,'unchanged_whole_parents':whole_unchanged,'chain_characters':removed,'selected_characters':prior_selected-removed}))
if __name__=='__main__':main()
