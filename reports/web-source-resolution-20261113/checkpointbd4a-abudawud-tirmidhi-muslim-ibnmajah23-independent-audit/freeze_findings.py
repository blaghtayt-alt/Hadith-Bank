"""Freeze independently established boundary findings after the blind full readings."""
from pathlib import Path
import datetime,gzip,hashlib,json
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
MP=WORK/'phase18-checkpointbd4a-abudawud-tirmidhi-muslim-ibnmajah23-review/delivery-manifest-v1.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(name,obj):
 p=ROOT/name;b=enc(obj)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
 return sha(b)
mb=MP.read_bytes();assert sha(mb)=='8d66fd9f9373f513cf06d31c42ff8128e5c55f38e8f228da9f61bba0b8806a64'
m=json.loads(mb);active=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ab=Path(active.get('local_path',active.get('source_path'))).read_bytes();assert sha(ab)=='1ae17b3b034812f8c40789881abd9d0184bbdb57c3c58a3eb09e682116b04fe8'
ledger=json.loads(gzip.decompress(ab));records={r['id']:r for r in ledger['records']}
rb=(ROOT/'complete-independent-source-first-readings.json').read_bytes();assert sha(rb)=='76bbb3cc2225960e170f664699136e32a534e20dd41216eb1c968acbb4ccf443'
reading=json.loads(rb);fields={(f['id'],f['language']):f for f in reading['fields']}
RESTORE=[
 ('deenhindi-tirmidhi:2382','ur','( قرآن سیکھنے سے )','The actual parenthesis supplies the object of the stated intention: learning the Quran. Retain this source-rendered qualification of the motive, without treating its brackets as proof of literal direct speech.'),
 ('deenhindi-tirmidhi:2434','hi','(उम्मत-ए-मुहम्मदी)','The source names the beneficiary group of the gate-entry statement; retain the source-rendered scope instead of silently broadening or leaving its reference implicit.'),
 ('deenhindi-tirmidhi:2434','hi','(दाख़िल होने में)','The source states the action in which the specified group shares the other gates. Preserve the actual entry qualification.'),
 ('deenhindi-tirmidhi:2434','ur','( امت محمد )','The source names the beneficiary group of the gate-entry statement. Preserve the printed Urdu scope without adding words from Hindi.'),
 ('deenhindi-tirmidhi:2434','ur','( داخل ہونے میں )','The source explicitly qualifies the shared action as entering. Preserve that exact scope.'),
 ('deenhindi-ibnmajah:2449','hi','(नक़द)','The source specifies the payment mode for the gold-or-silver lease alternative. Cash is material supplied transaction scope, unlike a mere alias for a named technical term.'),
 ('deenhindi-ibnmajah:2449','ur','( نقد )','The source explicitly specifies cash as the payment mode within its actual cultivation category; preserve that qualification.')
]
findings=[]
for ident,lang,literal,reason in RESTORE:
 f=fields[ident,lang];t=f['text'];assert t.count(literal)==1
 start=t.index(literal);end=start+len(literal)
 rule=next(x for x in records[ident]['field_reviews'] if x['language']==lang)
 assert not any(s['start']<end and s['end']>start for s in rule['spans'])
 left=next(s for s in rule['spans'] if s['end']==start);right=next(s for s in rule['spans'] if s['start']==end)
 for k in ['component_id','source_report_family_id','report_type','speaker']:assert left[k]==right[k]
 findings.append({'id':ident,'language':lang,'source_field':f['source_field'],'source_field_sha256':f['sha256'],'start':start,'end':end,'text':literal,'text_sha256':sha(literal.encode()),'characters':len(literal),'utf8_bytes':len(literal.encode()),'requested_change':'restore_exact_source_span_in_existing_component','component_id':left['component_id'],'source_report_family_id':left['source_report_family_id'],'report_type':left['report_type'],'speaker':left['speaker'],'reason':reason,'new_translation':False})
assert len(findings)==7 and sum(f['characters'] for f in findings)==96
accepted=[]
for ident,r in records.items():
 for f in r['field_reviews']:
  if not f.get('reviewed'):continue
  t=fields[ident,f['language']]['text']
  pieces=[dict(s) for s in f.get('spans',[])]
  for a in findings:
   if (a['id'],a['language'])==(ident,f['language']):
    source=next(s for s in pieces if s['end']==a['start'])
    pieces.append({**source,'start':a['start'],'end':a['end'],'sha256':sha(t[a['start']:a['end']].encode())})
  pieces.sort(key=lambda s:s['start']);merged=[]
  for s in pieces:
   same=bool(merged) and all(s.get(k)==merged[-1].get(k) for k in ['component_id','source_report_family_id','report_type','speaker'])
   if same and merged[-1]['end']==s['start']:
    merged[-1]['end']=s['end'];merged[-1]['sha256']=sha(t[merged[-1]['start']:s['end']].encode())
   else:merged.append(s)
  accepted.append({'id':ident,'language':f['language'],'source_field_sha256':fields[ident,f['language']]['sha256'],'decision':r['decision'],'expected_spans':merged,'reviewed_in_full':True,'approved_after_requested_corrections':True})
assert len(accepted)==55
plan_sha=put('accepted-reviewed-field-plan.json',{'source_pin':reading['source_commit'],'primary_v1_active_sha256':sha(ab),'independent_source_first_sha256':sha(rb),'reviewed_fields':accepted,'unread_siblings_approved':False,'source_only_ids':reading['source_only_proposed_ids']})
report={'schema':'hadith-bank-independent-boundary-findings-v1','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_pin':reading['source_commit'],'reviewer':'/root','primary_manifest_sha256':sha(mb),'primary_active_sha256':sha(ab),'independent_source_first_sha256':sha(rb),'all55_source_fields_read_before_candidate':True,'source_files_independently_verified':46,'full_reparses':23,'findings':findings,'required_exact_restorations':7,'affected_fields':5,'affected_parent_occurrences':3,'restored_characters':96,'restored_utf8_bytes':sum(f['utf8_bytes'] for f in findings),'required_parent_disposition_changes':0,'required_speaker_or_family_changes':0,'accepted_reviewed_field_plan_sha256':plan_sha,
 'initial_note_refinements':[{'id':'deenhindi-tirmidhi:2434','languages':['hi','ur'],'initial_note_preserved':'The frozen blind note treated the parenthetic forward-speaker label as apparatus.','refined_assessment':'On the full candidate comparison, the explicit return-to-Messenger attribution is retained as source narrative framing: it resolves the switch from the embedded requests back to the first-person account and is not labelled as a separate saying. This narrow refinement preserves the candidate bytes; it does not assert that the parenthesis is literal direct speech.'},
 {'id':'deenhindi-tirmidhi:2382','languages':['ur'],'initial_note_preserved':'The blind note referred broadly to the later reaction components as the same source family.','refined_assessment':'The candidate reasonably distinguishes the judgment report from the separate later Muawiya reception as two event families under the same original source occurrence. The two reception components share their family; no new source parent or invented event is created. Their exact supplied voices and attribution are accepted.'}],
 'preservation_required':'Archive the complete exact v1 payload and manifest and preserve original source-first notes. Keep all20 unaffected parent decisions and all50 other explicit reviewed-field definitions exact, together with58 unread siblings and2 empty source slots. Preserve all parent dispositions, source identities, metadata, original raw/parsed bytes and speaker/family bindings. Re-run native partitions on the final exact candidate.',
 'remaining_reviewed_boundaries':'All other candidate selected spans and context gaps were compared with the complete originals and frozen reading notes. No other amendment is requested. This does not approve unread sibling fields.',
 'independent_pro_qc':'not_performed'}
target=ROOT/'independent-boundary-findings-v1.json';assert not target.exists();fh=put(target.name,report)
print(json.dumps({'findings_sha256':fh,'plan_sha256':plan_sha,'restorations':7,'affected_fields':5,'characters':96,'utf8_bytes':report['restored_utf8_bytes']},indent=2))
