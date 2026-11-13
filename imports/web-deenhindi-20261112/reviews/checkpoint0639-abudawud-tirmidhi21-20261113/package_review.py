"""Freeze the authored21-parent review and its exact own-field evidence."""
from pathlib import Path
import collections,gzip,hashlib,json,re
ROOT=Path(__file__).resolve().parent;OUT=ROOT.parent/'publish-v2'
REV='imports/web-deenhindi-20261112/reviews'
COHORT='checkpoint0639-abudawud-tirmidhi21-20261113';PREFIX=REV+'/'+COHORT
ACTIVE=REV+'/source-review-'+COHORT+'.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(path,data):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return {'path':path,'bytes':len(data),'sha256':sha(data),'git_blob_sha1':blob(data)}
HONORIFICS={'(सल्लल्लाहु अलैहि वसल्लम)','(रज़ियल्लाहु अन्हा)','(रज़ियल्लाहु अन्हु)','(रज़ियल्लाहु अन्हुमा)','(रदी अल्लाहु अन्हु)','(रदी अल्लाहु अन्हुमा)','(अलैहिस्सलाम)'}
RETAINED={
 ('abudawud:2232','hi','(मुग़ीस के साथ रहने या ना रहने का)'):'Own-source object of the legal choice concerning the named husband.',
 ('abudawud:2232','ur','( مغیث کے ساتھ رہنے یا نہ رہنے کا )'):'Own-source object of the legal choice concerning the named husband.',
 ('abudawud:2232','hi','(ना रहने की सूरत में)'):'Actual conditional scope of the iddah instruction.',
 ('abudawud:2232','ur','( نہ رہنے کی صورت میں )'):'Actual conditional scope of the iddah instruction.',
 ('abudawud:2233','hi','(आज़ाद होने के बाद)'):'Actual emancipation-time condition of the described choice.',
 ('abudawud:2233','ur','( آزاد ہونے کے بعد )'):'Actual emancipation-time condition of the described choice.',
 ('abudawud:2253','ur','( ایک دفعہ )'):'Narrated once/on-one-occasion framing, not a lexical definition.',
 ('abudawud:2253','ur','( اجنبی )'):'Qualifies the actual other man in each accusation question; the two exact occurrences are retained.',
 ('abudawud:2258','ur','( اس صورت میں )'):'Restricts the narrated separation to the described accusation circumstance.',
 ('abudawud:2269','hi','(तीसरे को)'):'Identifies the proposed third recipient within the three-man dispute.',
 ('abudawud:2269','ur','( تیسرے کو )'):'Identifies the proposed third recipient within the three-man dispute.',
 ('abudawud:2276','hi','(दूसरा)'):'Specifies another marriage as the narrated custody condition.',
 ('abudawud:2276','ur','( دوسرا )'):'Specifies another marriage as the narrated custody condition.',
 ('abudawud:2280','hi','(फातिमा रदी अल्लाहु अन्हा से)'):'Names the actual addressee receiving the child, as supplied by this field.',
 ('abudawud:2280','ur','( فاطمہ رضی اللہ عنہا سے )'):'Names the actual addressee receiving the child, as supplied by this field.',
 ('tirmidhi:2240','ur','( جب بعد میں )'):'Narrative later-return transition.',
 ('tirmidhi:2240','ur','( اس عرصے میں )'):'Narrative concurrent-time qualification during the siege.',
 ('tirmidhi:2240','ur','( پہاڑ سے )'):'Specifies the physical descent after the mountain refuge, distinct from the earlier descent from above.',
 ('tirmidhi:2240','ur','( کئی سالوں تک )'):'Source-supplied duration of the later condition before the wind.',
 ('tirmidhi:2246','ur','( دجال کے بارے میں )'):'Identifies the subject of Ibn Sayyad’s asserted Prophetic quotation, preserving attribution scope.',
 ('tirmidhi:2289','ur','( ایک کنویں پر )'):'Actual well setting of the dream’s gathering and bucket action, supplied only here in this field.',
 ('tirmidhi:2290','ur','( بخار والی )'):'Qualifies the illness in the actual first-person dream interpretation.'}

def main():
 active=(OUT/ACTIVE).read_bytes();assert sha(active)=='b4735dc63110fd87e92205140a305fee5164f26eafe8b09bddcbca7643a13e34'
 ledger=json.loads(gzip.decompress(active));sources={r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress((OUT/ledger['source_ledger_path']).read_bytes()).splitlines())}
 first=(ROOT/'complete-source-first-readings.json').read_bytes();sourcefirst=json.loads(first);notes={(r['key'],r['language']):r for r in sourcefirst['fields']}
 parts={r['id']:r for r in json.loads(gzip.decompress((OUT/PREFIX/'field-partitions.json.gz').read_bytes()))}
 readings=[];retained=[];counts=collections.Counter();used=set();whitespace=[]
 for record in ledger['records']:
  key=record['id'].removeprefix('deenhindi-')
  for field in record['field_reviews']:
   lang=field['language'];text=sources[key]['source_record'][field['source_field']];note=notes[(key,lang)]
   assert note['text']==text and note['sha256']==field['text_sha256']==sha(text.encode())
   assert note['chars']==field['chars_reviewed']==len(text) and note['utf8_bytes']==field['bytes_reviewed']==len(text.encode())
   mask={i for s in field['spans'] for i in range(s['start'],s['end'])}
   assert not any('؎' in text[s['start']:s['end']] for s in field['spans'])
   contexts=[{**p,'text':text[p['start']:p['end']]} for p in parts[record['id']+':'+lang]['parts'] if p['role']=='context']
   for c in contexts:
    if c['text'] and not c['text'].strip():whitespace.append({'id':record['id'],'language':lang,**c})
   selected=[{**s,'text':text[s['start']:s['end']]} for s in field['spans']]
   readings.append({**note,'actual_field_review':field,'selected_spans':selected,'retained_context':contexts})
   # This inventory checks the explicit manual choices; it does not approve new text.
   for m in re.finditer(r'\([^()]*\)',text):
    if set(range(m.start(),m.end()))<=mask:
     literal=m.group();binding=(key,lang,literal)
     if literal in HONORIFICS:category='honorific';reason='Printed honorific formula retained without alteration.';counts['retained_honorific_parentheses']+=1
     else:
      assert binding in RETAINED,binding;used.add(binding);category='individually_reviewed_narrative_qualifier';reason=RETAINED[binding];counts['retained_narrative_parentheses']+=1
     retained.append({'id':record['id'],'language':lang,'source_text_sha256':sha(text.encode()),'start':m.start(),'end':m.end(),'text':literal,'sha256':sha(literal.encode()),'category':category,'reason':reason})
   counts.update(complete_fields_read=1,characters_read=len(text),utf8_bytes_read=len(text.encode()),selected_spans=len(selected),selected_characters=sum(len(s['text']) for s in selected))
 assert used==set(RETAINED) and counts['complete_fields_read']==42 and counts['characters_read']==30305 and counts['utf8_bytes_read']==63236
 assert counts['retained_narrative_parentheses']==23
 context=json.loads((OUT/PREFIX/'explicit-source-apparatus-context.json').read_bytes());validation=json.loads((OUT/PREFIX/'validation.json').read_bytes())
 counts['explicit_literal_context_cuts']=context['literal_omissions']
 put(PREFIX+'/complete-source-first-readings.json.gz',gzip.compress(first,mtime=0))
 put(PREFIX+'/source-first-notes.json',(ROOT/'source-first-notes.json').read_bytes())
 put(PREFIX+'/complete-field-readings-and-boundaries.json.gz',gzip.compress(enc({'source_commit':ledger['source_checkpoint'],'active_ledger_sha256':sha(active),'fields':readings}),mtime=0))
 put(PREFIX+'/retained-source-parentheses.json',enc({'scope':'Individually justified exact selected source parentheses; no general approval rule is implied.','counts':dict(counts),'items':retained,'selected_footnote_markers':0,'whitespace_only_context_gaps':whitespace}))
 report={'schema':'hadith-bank-source-bound-primary-review-v1','result':'PASS','source_checkpoint':ledger['source_checkpoint'],'source_worker_run_id':43436779480,
  'cohort':'21 of117 newly acquired0639 holds:15 AbuDawud and6 Tirmidhi; disjoint from all priorc2ab imports.',
  'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),'source_baseline_path':ledger['source_ledger_path'],'source_baseline_sha256':ledger['source_ledger_sha256'],
  'source_first_receipt_sha256':sha(first),'actual_reading':dict(counts),'native_and_source_validation':validation['totals'],'by_book':validation['by_book'],'by_language':validation['by_language'],
  'parent_decisions':{'register':21,'source_only':0,'unresolved':0},'unread_sibling_fields_retained_context':63,
  'script_and_language_metadata_changes':0,'unknown_or_defective_attribution_notes':['Abu2233 Hindi initial deciding actor remains honorific-only.','Abu2268 Aisha’s visitor remains the own-field honorific referent; the explicit name is not supplied.'],
  'report_family_notes':{'abudawud:2251':'Two actual transmitted portions in one li-an episode; compiler end-marker and final corroboration critique remain context.',
   'abudawud:2268':'Two independently attributed statement families: Aisha’s finite observation and Ahmad ibn Salih’s historical statement through AbuDawud.',
   'abudawud:2280':'Two finite portions of one Hamza-daughter episode around an explicitly omitted middle.',
   'tirmidhi:2239':'Anas’s own prediction; no Prophetic attribution added.',
   'tirmidhi:2246':'AbuSaid’s eyewitness narrative retains IbnSayyad’s nested claims and asserted Prophetic quotations without affirming his identity.'},
  'preservation_notes':['Hindi/Urdu differences and all abbreviations remain exact.','Actual recitation and supplied scripture translations are retained; explicit locators and footnotes remain context.','No canonically shared number or external parallel was used to fill a source identity.'],
  'independent_boundary_amendment':{'path':PREFIX+'/independent-boundary-v2/exact-amendment.json','sha256':'ffb3e844a48ee7b4b841af13009b8480ccf7fb9c8566144ae64b74bfc81e5265','literal_cuts':3,'orphan_separator_spaces':1,'changed_fields':3,'other_explicit_fields_unchanged':39},
  'source_http_requests':0,'github_writes':0,'engine_changes':False,'independent_pro_qc':'not_performed','certified_release_eligible':False,
  'limits':'This is the primary complete-field review with native saved-source validation. Independent second reading and final integration, full repository export, reader/browser checks and actual deployment are separate gates.'}
 put('reports/web-source-resolution-20261113/checkpoint0639-abudawud-tirmidhi21-primary-review.json',enc(report))
 put(PREFIX+'/package_review.py',Path(__file__).read_bytes())
 files=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name!='portable-manifest.json':files.append({'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'git_blob_sha1':blob(p.read_bytes())})
 put(PREFIX+'/portable-manifest.json',enc({'schema':'hadith-bank-portable-review-package-v1','source_checkpoint':ledger['source_checkpoint'],'active_ledger_sha256':sha(active),'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}))
 files=[]
 for p in sorted(OUT.rglob('*')):
  if p.is_file():files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'git_blob_sha1':blob(p.read_bytes())})
 manifest={'schema':'hadith-bank-source-review-delivery-v1','source_checkpoint':ledger['source_checkpoint'],'active_ledger_path':ACTIVE,'active_ledger_sha256':sha(active),'source_baseline_sha256':ledger['source_ledger_sha256'],'files':files,'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
 (ROOT.parent/'delivery-manifest-v2.json').write_bytes(enc(manifest))
 print(json.dumps({'status':'FROZEN','active_sha256':sha(active),'manifest_sha256':sha(enc(manifest)),'files':len(files),'bytes':manifest['total_bytes'],'actual_reading':dict(counts),'whitespace_context_gaps':len(whitespace)},indent=2))
if __name__=='__main__':main()
