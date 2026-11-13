"""Bind the exact four-parent revision to the independently frozen125-slot plan."""
from pathlib import Path
import collections,gzip,hashlib,json
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent
OUT=OLD/'publish-v2'
PREFIX='imports/web-deenhindi-20261112/reviews/checkpoint5589-abudawud-tirmidhi25-20261113'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
mask=lambda f:{i for s in (f or {}).get('spans',[]) for i in range(s['start'],s['end'])}
def ranges(positions):
 result=[]
 for i in sorted(positions):
  if result and result[-1][1]==i:result[-1][1]=i+1
  else:result.append([i,i+1])
 return result
def put(relative,data):
 p=OUT/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return {'path':relative,'bytes':len(data),'sha256':sha(data)}
def main():
 mb=(OLD/'delivery-manifest-v1.json').read_bytes();assert sha(mb)=='4e82a1b13b65c21c8d31034e79439e11b1353aea1ca27d6510513aa2308668ec'
 manifest=json.loads(mb)
 for item in manifest['files']:
  b=(OLD/'publish'/item['path']).read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256']
 active=manifest['active_ledger_path'];before_bytes=(OLD/'publish'/active).read_bytes();after_bytes=(OUT/active).read_bytes()
 assert sha(before_bytes)=='b2f5305335c2a896ea850a2ef79b7f6b878a6f6f72e5301972c256cd1d8296af'
 before=json.loads(gzip.decompress(before_bytes));after=json.loads(gzip.decompress(after_bytes))
 old={r['id']:r for r in before['records']};new={r['id']:r for r in after['records']};assert set(old)==set(new) and len(new)==25
 assert (OLD/'publish'/before['source_ledger_path']).read_bytes()==(OUT/after['source_ledger_path']).read_bytes()
 rows={r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress((OUT/after['source_ledger_path']).read_bytes()).splitlines())}
 pb=(ROOT/'accepted-final-field-plan.json').read_bytes();assert sha(pb)=='8d179a06414e49543410b88c1be6a0714fbb93f8919f7b37e5a987ac5d9c926b'
 plan={r['id']:r for r in json.loads(pb)['rows']};assert set(plan)==set(new)
 changed={'deenhindi-abudawud:2306','deenhindi-abudawud:2330','deenhindi-abudawud:2331','deenhindi-tirmidhi:2363'}
 totals=collections.Counter();changes=[]
 for identity,record in new.items():
  previous=old[identity];accepted=plan[identity];assert record['decision']==accepted['decision']
  if identity not in changed:assert record==previous;totals['whole_parents_unchanged']+=1
  else:
   for name in set(previous)-{'field_reviews','decision','reason'}:assert record[name]==previous[name]
   totals['changed_parents']+=1
  old_fields={f['language']:f for f in previous['field_reviews']};fields={f['language']:f for f in record['field_reviews']}
  for expected in accepted['fields']:
   lang=expected['language'];f=fields.get(lang);prior=old_fields.get(lang);text=rows[identity.removeprefix('deenhindi-')]['source_record'][expected['source_field']]
   assert sha(text.encode())==expected['source_text_sha256']
   assert bool(f)==expected['reviewed']
   wanted={i for a,b in expected['accepted_positions'] for i in range(a,b)};assert mask(f)==wanted,(identity,lang)
   if not expected['allowed_semantic_change']:
    assert f==prior;totals['unchanged_explicit_fields' if prior else 'unchanged_implicit_unread_slots']+=1
   else:
    assert f!=prior
    totals['changed_existing_explicit_fields' if prior else 'newly_read_explicit_fields']+=1
    item={'id':identity,'language':lang,'source_text_sha256':sha(text.encode()),'before_field_sha256':sha(enc(prior)) if prior else None,'after_field_sha256':sha(enc(f)),
     'initially_reviewed':bool(prior),'finally_reviewed':True,'reason':expected.get('reason','Exact independent scope plan.'),'changes':[]}
    for action,positions in [('to_context',mask(prior)-mask(f)),('restored_to_report',mask(f)-mask(prior))]:
     for a,b in ranges(positions):
      item['changes'].append({'action':action,'start':a,'end':b,'text':text[a:b],'sha256':sha(text[a:b].encode()),'characters':b-a,'utf8_bytes':len(text[a:b].encode())})
      totals[action+'_characters']+=b-a;totals[action+'_bytes']+=len(text[a:b].encode())
    changes.append(item)
   totals['source_field_slots_verified']+=1
 assert totals['whole_parents_unchanged']==21 and totals['changed_parents']==4
 assert totals['changed_existing_explicit_fields']==8 and totals['newly_read_explicit_fields']==6
 assert totals['unchanged_explicit_fields']==45 and totals['unchanged_implicit_unread_slots']==66 and totals['source_field_slots_verified']==125
 assert totals['restored_to_report_characters']==18
 archive=PREFIX+'/independent-scope-v2'
 put(archive+'/active-before-v1.json.gz',before_bytes)
 put(archive+'/delivery-manifest-before-v1.json',mb)
 for item in manifest['files']:
  put(archive+'/before-v1/payload/'+item['path'],(OLD/'publish'/item['path']).read_bytes())
 for name in ['manual_readings.py','manual-abudawud.json','manual-tirmidhi.json','source-first-notes.json','complete-source-first-readings.json','build_review.py','package_review.py']:
  data=(OLD/name).read_bytes();put(archive+'/before-v1/'+name,data)
 for name in ['independent-boundary-findings-v1.json','accepted-final-field-plan.json','additional-six-original-fields.jsonl','additional-six-complete-source-readings.json','complete-source-reading-history.json']:
  put(archive+'/'+name,(ROOT/name).read_bytes())
 put(archive+'/verify_amendment.py',Path(__file__).read_bytes())
 receipt={'schema':'hadith-bank-exact-independent-scope-amendment-v1','result':'PASS','before_active_sha256':sha(before_bytes),'after_active_sha256':sha(after_bytes),
  'before_manifest_sha256':sha(mb),'independent_findings_sha256':'ec424ce3205fe1ff438df8b4fdc5a94412e1069ad5e55877a9ee64fd497af4c5','accepted125_slot_plan_sha256':sha(pb),
  'totals':dict(totals),'changes':changes,'all21_original_payloads_and_initial_reading_notes_preserved':True,'all21_original_payloads_archived_verbatim':True,'source_baseline_bytes_unchanged':True,
  'scope':'Two lexical-only parents become source-only after all five fields were read; appended2306 legal explanation stays context;2363 exact OR-object phrases are restored. No other source positions or field decisions change.',
  'reading_order':'53 complete readings preceded v1. Six additional complete source fields were read after independent findings and before the new source-only dispositions. Original observations remain historical evidence.',
  'source_http_requests':0,'github_writes':0,'engine_changes':False}
 put(archive+'/exact-scope-amendment.json',enc(receipt))
 (ROOT/'exact-scope-amendment.json').write_bytes(enc(receipt))
 print(json.dumps({'result':'PASS','receipt_sha256':sha(enc(receipt)),'after_active_sha256':sha(after_bytes),'totals':dict(totals)},indent=2))
if __name__=='__main__':main()
