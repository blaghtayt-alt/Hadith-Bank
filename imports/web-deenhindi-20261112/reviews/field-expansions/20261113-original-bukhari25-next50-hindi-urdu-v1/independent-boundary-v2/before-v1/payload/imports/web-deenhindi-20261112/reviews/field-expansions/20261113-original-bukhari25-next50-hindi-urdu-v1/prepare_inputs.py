"""Prepare a disjoint originals-only50-field packet from exact published queue bytes."""
from pathlib import Path
from decimal import Decimal
import base64,gzip,hashlib,json,sys
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
PIN='d369026ca42af6ff972ffab83c9180e03759da41'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
BASE='imports/web-deenhindi-20261112/reviews/evidence/20261113-bukhari-ibnmajah-manual-v1-source-ledger.jsonl.gz'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def lines(xs):return b''.join((json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n').encode() for x in xs)
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
raw={};proof=[]
for name,path,expected in [('active',ACTIVE,'18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'),('queue',QUEUE,'74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'),('baseline',BASE,'5c9598c1c61cee509155013dde44221de2e17f11bd29d0f475092f2a6e86fb36')]:
 p=HERE/'input/github-metadata'/(name+'.json');r=json.loads(p.read_bytes())
 assert r['requested_ref']==PIN and r['requested_path']==path and r['encoding']=='base64'
 b=base64.b64decode(r['content']);assert sha(b)==expected and git(b)==r['sha']
 put(HERE/'input/pinned'/path,b);raw[name]=b
 proof.append({'path':path,'source_commit':PIN,'sha256':sha(b),'git_blob_sha1':git(b),'bytes':len(b),'response_sha256':sha(p.read_bytes())})
queue=[json.loads(x) for x in gzip.decompress(raw['queue']).splitlines()]
assert len(queue)==3379 and sum(len(x['fields']) for x in queue)==6361
ledger=json.loads(gzip.decompress(raw['active']));decisions={r['occurrence_id']:r for r in ledger['records']};assert len(decisions)==477
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress(raw['baseline']).splitlines())};assert sources.keys()==decisions.keys()
eligible=[r for r in queue if r['id'].startswith('deenhindi-bukhari:') and r['active_review_path']==ACTIVE and {f['language'] for f in r['fields']}=={'hi','ur'}]
eligible.sort(key=lambda r:(Decimal(r['id'].split(':',1)[1]),r['id']));assert len(eligible)==176
selected=eligible[:25];chosen=[];readings=[];descriptors={};request_paths=[]
statep=WORK/'phase18-successor-acquisition-monitor/saved-checkpoint/state.json';sb=statep.read_bytes();assert sha(sb)=='9080df3aa1461e05204a0c4cc428bdf30d89501be995729db64b7a64885391dd';state=json.loads(sb)
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'));import import_deenhindi as importer
for n,row in enumerate(selected,1):
 ident=row['id'];source=sources[ident];d=decisions[ident];key=ident.removeprefix('deenhindi-');entry=state['imported'][key]
 assert d['decision']==row['existing_parent_decision']=='register'
 assert row['source_record_sha256']==sha(importer.json_bytes(source['source_record']))==d['source_record_sha256']
 assert row['source_snapshot_path']==source['snapshot']['path']
 assert row['source_parsed_path']==source['parsed_path']==entry['parsed']['path']
 chosen.append(source);descriptors[key]=entry
 for kind,desc in [('raw',source['snapshot']),('parsed',entry['parsed'])]:request_paths.append({'kind':kind,'id':ident,'path':desc['path'],'descriptor':desc})
 for lang,field in [('hi','translationHindi'),('ur','translationUrdu')]:
  q=next(x for x in row['fields'] if x['language']==lang);f=next(x for x in d['fields'] if x['language']==lang);t=source['source_record'][field]
  assert t and sha(t.encode())==q['text_sha256']==f['text_sha256'] and not f['reviewed'] and not f['selected_spans']
  readings.append({'reading_order':len(readings)+1,'occurrence_order':n,'occurrence_id':ident,'collection':source['collection'],'number':source['number'],'language':lang,'source_field':field,'source_commit':PIN,'source_record_sha256':row['source_record_sha256'],'text':t,'text_sha256':sha(t.encode()),'characters':len(t),'utf8_bytes':len(t.encode()),'complete_own_field_read':False,'semantic_review_status':'unread_at_frozen_source_preparation'})
sourceb=lines(chosen);readingb=lines(readings)
selection={'schema':'hadith-bank-frozen-original-language-extension-selection-v1','source_publication_commit':PIN,'canonical_queue_path':QUEUE,'canonical_queue_sha256':sha(raw['queue']),'baseline_queue_fields':6361,'baseline_queue_occurrences':3379,'active_review_path':ACTIVE,'active_review_sha256':sha(raw['active']),'source_baseline_path':BASE,'source_baseline_sha256':sha(raw['baseline']),'eligible_paired_bukhari_count':176,'selection_rule':'First25 numerically ordered Bukhari IDs with both Hindi and Urdu pending in the published queue, restricted to the existing477-parent Bukhari/IbnMajah ledger.','selected_occurrences':25,'selected_fields':50,'selected_characters':sum(r['characters'] for r in readings),'selected_utf8_bytes':sum(r['utf8_bytes'] for r in readings),'selected':selected,'selected_source_baseline_sha256':sha(sourceb),'full_field_reading_input_sha256':sha(readingb),'all_unselected_field_decisions_must_remain_exact':True,'parent_dispositions_must_remain_unchanged':True,'candidate_authored':False,'source_readings_claimed_at_freeze':0,'current_metadata_file_proofs':proof,'descriptor_authority':{'source_commit':'3e574b9e7e4dd7cf8bc23232249004a18692c61c','full_state_sha256':sha(sb)}}
put(HERE/'input/source-25.jsonl',sourceb);put(HERE/'input/full-hi-ur-reading-input-50.jsonl',readingb);put(HERE/'input/prior-saved-state-descriptors.json',enc(descriptors));put(HERE/'input/source-file-requests.json',enc(request_paths));put(HERE/'input/selection.json',enc(selection))
print(json.dumps({'selection_sha256':sha(enc(selection)),'source25_sha256':sha(sourceb),'reading50_sha256':sha(readingb),'fields':50,'characters':selection['selected_characters'],'utf8_bytes':selection['selected_utf8_bytes'],'source_file_requests':len(request_paths),'ids':[r['id'] for r in selected],'candidate_authored':False,'semantic_readings_claimed':0},indent=2))
