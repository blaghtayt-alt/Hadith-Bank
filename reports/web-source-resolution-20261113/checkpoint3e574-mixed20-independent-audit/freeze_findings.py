"""Freeze root's actually inspected40-field comparison and four exact chain cuts."""
from pathlib import Path
import copy,gzip,hashlib,json
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
PRIMARY=WORK/'phase19-checkpoint3e574-abudawud-tirmidhi-bukhari-ibnmajah20-review'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
mp=PRIMARY/'delivery-manifest-v1.json';mb=mp.read_bytes();assert sha(mb)=='313c1d051177932acbc232ee47b8314fcb7966f9da122367017d678ef29dd9b4'
m=json.loads(mb)
for f in m['files']:
 b=Path(f['local_path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes']
af=next(f for f in m['files'] if f['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
ab=Path(af['local_path']).read_bytes();assert sha(ab)=='a667f1881c9731b51ea59be17a148558decb3423d812496b4acfaf78e458b104'
ledger=json.loads(gzip.decompress(ab));rows={r['id']:r for r in ledger['records']}
ownb=(ROOT/'complete-independent-source-first-readings.json').read_bytes();assert sha(ownb)=='b60d6f124504794d1ad2441fd32d326f9a04483115aeb0f30a680a204ea92058'
own=json.loads(ownb);assert own['candidate_or_primary_notes_inspected'] is False
readings={(r['id'],r['language']):r for r in own['fields']};assert len(readings)==40
cuts={('deenhindi-bukhari:2535','hi'):181,('deenhindi-bukhari:2535','ur'):159,('deenhindi-bukhari:2536','hi'):99,('deenhindi-bukhari:2536','ur'):158}
findings=[];plans=[];inspections=[]
for key,r in readings.items():
 ident,lang=key;d=rows[ident];f=next(f for f in d['field_reviews'] if f['language']==lang)
 assert f['reviewed'] and f['text_sha256']==r['sha256'] and f['chars_reviewed']==r['characters'] and f['bytes_reviewed']==r['utf8_bytes']
 text=r['text'];expected=copy.deepcopy(f['spans'])
 for s in expected:assert s['sha256']==sha(text[s['start']:s['end']].encode())
 if key in cuts:
  end=cuts[key];assert expected[0]['start']==0 and expected[0]['end']>end
  prior=copy.deepcopy(expected[0]);expected[0]['start']=end;expected[0]['sha256']=sha(text[end:expected[0]['end']].encode())
  findings.append({'id':ident,'language':lang,'source_text_sha256':r['sha256'],'change':'move the exact prefatory transmission chain to lossless source context','start':0,'end':end,'text':text[:end],'sha256':sha(text[:end].encode()),'characters':end,'utf8_bytes':len(text[:end].encode()),'before_first_span':prior,'expected_first_span':expected[0],'reason':'The source supplies an opening transmission route before the actual final reporter framing or first-person event. AGENTS requires narrator chains separately. The exact chain and source identity remain in context and existing source-qualified speaker metadata, without correcting the damaged Hindi name or creating missing words. All actual report wording, contract conditions and later dialogue components remain selected.'})
 plans.append({'id':ident,'language':lang,'decision':d['decision'],'source_text_sha256':r['sha256'],'expected_spans':expected})
 inspections.append({'id':ident,'language':lang,'complete_source_first_reading_sha256':r['sha256'],'original_blind_note':r['independent_reading_note'],'v1_field':f,'expected_spans':expected,'decision':'bounded_chain_prefix_correction' if key in cuts else 'accepted_v1_exact'})
assert len(findings)==4 and sum(f['characters'] for f in findings)==597 and sum(f['utf8_bytes'] for f in findings)==1272
refinements=[{'id':'deenhindi-tirmidhi:2502','language':'hi','source_first_note_retained_unchanged':True,'refined_assessment':'The short (दूसरी बीवी) phrase is appositional biographical identification of the already named Safiyya, not a condition, recipient relation governing the reported action, or additional narrated event. Accept its exact preservation as context. The separate full parenthetic hand gesture is a finite action and remains selected; the source words, identities, full gesture, quoted replies and conditional sea-water comparison are preserved. This refines the initial broader relationship-parenthesis note on the basis of the full own field and exact proposed cut, without treating every parenthesis alike.','accepted_context_span':{'start':279,'end':291,'text':'(दूसरी बीवी)'}}]
report={'schema':'hadith-bank-independent-boundary-findings-v1','reviewer':'/root','source_commit':'3e574b9e7e4dd7cf8bc23232249004a18692c61c','source_first_receipt_sha256':sha(ownb),'primary_v1_manifest_sha256':sha(mb),'primary_v1_active_sha256':sha(ab),'all40_exact_candidate_fields_inspected_after_complete_original_readings':True,'findings':findings,'accepted_unchanged_fields':36,'initial_note_refinements':refinements,'all_inspected_fields':inspections,'independent_pro_qc':'not_performed','github_writes':0}
plan={'schema':'hadith-bank-independent-accepted-field-plan-v1','source_commit':report['source_commit'],'source_first_receipt_sha256':sha(ownb),'primary_v1_manifest_sha256':sha(mb),'reviewed_fields':plans}
put(ROOT/'independent-boundary-findings-v1.json',enc(report));put(ROOT/'accepted-reviewed-field-plan.json',enc(plan))
print(json.dumps({'findings_sha256':sha(enc(report)),'accepted_plan_sha256':sha(enc(plan)),'complete_fields_inspected':40,'unchanged_fields_accepted':36,'chain_cuts':4,'characters_to_context':597,'utf8_bytes_to_context':1272},indent=2))
