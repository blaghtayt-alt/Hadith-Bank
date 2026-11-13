"""Correct copied delta hashes to the final, already audited V2 field decisions."""
from pathlib import Path
import gzip,hashlib,json,shutil
HERE=Path(__file__).resolve().parent
OLD=HERE/'publish-v2';OUT=HERE/'publish-v3'
EVID=Path('imports/web-deenhindi-20261112/reviews/field-expansions/20261113-bukhari30-40-hindi-urdu-v1')
FIX=EVID/'queue-binding-correction-v3'
ACTIVE=Path('imports/web-deenhindi-20261112/reviews/source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz')
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
manifest_raw=(HERE/'delivery-manifest-v2.json').read_bytes()
assert sha(manifest_raw)=='0f08b483c0e863442013bf57b6b2e9fea2261c95dcbdd7181986e81c7fd89cde'
if OUT.exists():
 assert {p.relative_to(OUT) for p in OUT.rglob('*') if p.is_file()}=={p.relative_to(OLD) for p in OLD.rglob('*') if p.is_file()}
 assert all(p.read_bytes()==(OLD/p.relative_to(OUT)).read_bytes() for p in OUT.rglob('*') if p.is_file())
 shutil.rmtree(OUT)
shutil.copytree(OLD,OUT)
active=(OUT/ACTIVE).read_bytes();assert sha(active)=='ac53483e3eab6c0a4c508c86180c75091792e895b5e29f602a061aa2cd080c62'
obj=json.loads(gzip.decompress(active));by={(r['occurrence_id'],f['language']):f for r in obj['records'] for f in r['fields']}
prior=(OUT/EVID/'priority-field-queue-delta.json').read_bytes();delta=json.loads(prior)
final=json.loads((OUT/EVID/'field-decision-delta.json').read_bytes())
assert len(final)==len(delta['removed_fields'])==40
changes=[]
for before,after in zip(delta['removed_fields'],final):
 assert before.keys()==after.keys()
 assert {k:v for k,v in before.items() if k not in ('after_field_decision_sha256','after_decision')}=={k:v for k,v in after.items() if k not in ('after_field_decision_sha256','after_decision')}
 key=(after['occurrence_id'],after['language']);assert after['after_field_decision_sha256']==sha(enc(by[key]))
 assert after['after_decision']==by[key]['decision']
 if before!=after:changes.append({'id':key[0],'language':key[1],'before':before['after_field_decision_sha256'],'after':after['after_field_decision_sha256'],'before_action_label':before['after_decision'],'after_action_label':after['after_decision']})
assert len(changes)==10
delta['removed_fields']=final;put(OUT/EVID/'priority-field-queue-delta.json',enc(delta))
unchanged=[]
for p in sorted(OLD.rglob('*')):
 if p.is_file() and p!=OLD/EVID/'priority-field-queue-delta.json':
  assert p.read_bytes()==(OUT/p.relative_to(OLD)).read_bytes();unchanged.append(p.relative_to(OLD).as_posix())
receipt={'schema':'hadith-bank-queue-evidence-hash-correction-v3','status':'PASS',
 'previous_manifest_sha256':sha(manifest_raw),'active_review_sha256_unchanged':sha(active),
 'previous_queue_delta_sha256':sha(prior),'final_queue_delta_sha256':sha(enc(delta)),
 'changed_metadata_hashes':10,'corrected_copied_action_labels':5,'all40_hashes_and_action_labels_match_final_field_decisions':True,'candidate_queue_bytes_unchanged':True,
 'all_field_decisions_and_source_evidence_unchanged':True,'all_other_existing_package_files_exact':unchanged,
 'changes':changes,'reason':'V2 correctly changed the final field ledger and standalone field delta but left ten stale V1 decision hashes and five stale whole-versus-excerpts labels in the copied queue-delta list. This correction updates only those copied metadata values. No text, reading, active decision, queue membership, disposition or native result changes.'}
assert sum(x['before_action_label']!=x['after_action_label'] for x in changes)==5
for name,b in [('previous-priority-field-queue-delta.json',prior),('previous-delivery-manifest-v2.json',manifest_raw),('correction-receipt.json',enc(receipt)),('repair_queue_bindings_v3.py',Path(__file__).read_bytes())]:put(OUT/FIX/name,b)
m=json.loads(manifest_raw);m.update(candidate_revision='v3_metadata_bindings_only',queue_binding_correction=receipt)
files=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file():
  b=p.read_bytes();files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
m.update(files=files,total_files=len(files),total_bytes=sum(f['bytes'] for f in files));put(HERE/'delivery-manifest-v3.json',enc(m))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(m)),'active_sha256_unchanged':sha(active),'files':len(files),'bytes':m['total_bytes'],'corrected_copied_hashes':len(changes),'corrected_copied_action_labels':5},indent=2))
