"""Compose the two independently read disjoint original-cohort field deltas."""
from pathlib import Path
import collections,gzip,hashlib,json
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
OUT=HERE/'publish';REPORT=Path('reports/web-source-resolution-20261113')
QUEUE=REPORT/'current-original3942-priority-field-queue.jsonl.gz'
INPUTS=[
 ('abudawud50','phase14-original-abudawud50-urdu/delivery-manifest-v2.json','db63f76f44ee298577960c255ab5298d9c6b96936597ffb3aebca776f1f94bf6'),
 ('bukhari40','phase14-original-bukhari30-hi-ur/delivery-manifest-v3.json','3f0515c09ffb0739d6db734390c5b98669d2875b0f4e11f1da0fec5aafbb6af0'),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
packages=[];targets={};baseline=None
for name,local,digest in INPUTS:
 raw=(WORK/local).read_bytes();assert sha(raw)==digest;m=json.loads(raw)
 for f in m['files']:
  b=Path(f['local_path']).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256']
  if f.get('git_blob_sha1'):assert git(b)==f['git_blob_sha1']
 previous=next(f for f in m['files'] if f['path'].endswith('previous-priority-field-queue.jsonl.gz'))
 previous_bytes=Path(previous['local_path']).read_bytes()
 assert sha(previous_bytes)=='f5fa86ff645098396c7daf978f7491bddff6fd9104f5e50acc72f7d02701a660'
 if baseline is None:baseline=previous_bytes
 else:assert baseline==previous_bytes
 delta_item=next(f for f in m['files'] if f['path'].endswith('priority-field-queue-delta.json'))
 delta=json.loads(Path(delta_item['local_path']).read_bytes())
 active_item=next(f for f in m['files'] if Path(f['path']).name.startswith('source-review-'))
 active=json.loads(gzip.decompress(Path(active_item['local_path']).read_bytes()))
 by={(r.get('id',r.get('occurrence_id')),f['language']):f for r in active['records'] for f in r.get('field_reviews',r.get('fields'))}
 removals=delta['removed'] if name=='abudawud50' else delta['removed_fields']
 for row in removals:
  ident=row['id'] if name=='abudawud50' else row['occurrence_id']
  language=row['field']['language'] if name=='abudawud50' else row['language']
  text_hash=row['field']['text_sha256'] if name=='abudawud50' else row['source_text_sha256']
  key=(ident,language);assert key not in targets
  field=by[key];assert field['reviewed'] and field['text_sha256']==text_hash
  action=field.get('action',field.get('decision'));assert action in ('whole','excerpts','excerpt')
  if name=='bukhari40':
   assert row['after_field_decision_sha256']==sha(enc(field)) and row['after_decision']==action
  targets[key]={'id':ident,'language':language,'source_field':field['source_field'],
   'source_text_sha256':text_hash,'final_field_decision_sha256':sha(enc(field)),
   'final_action':action,'package':name,'active_ledger_path':active_item['path'],'active_ledger_sha256':active_item['sha256']}
 packages.append({'name':name,'manifest_sha256':digest,'delta_path':delta_item['path'],
  'delta_sha256':delta_item['sha256'],'active_ledger_sha256':active_item['sha256'],'removed_fields':len(removals)})
assert len(targets)==90 and len({k[0] for k in targets})==80
lines=gzip.decompress(baseline).splitlines(keepends=True)
assert len(lines)==3484 and all(line.endswith(b'\n') for line in lines)
remaining=[];removed=[];seen=set();old_field_count=0
for line in lines:
 row=json.loads(line);old_field_count+=len(row['fields'])
 keys={(row['id'],f['language']) for f in row['fields']}
 matching=keys.intersection(targets)
 if matching:
  assert matching==keys,'These frozen two deltas remove every pending field of each selected occurrence.'
  for f in row['fields']:
   key=(row['id'],f['language']);target=targets[key]
   assert f['text_sha256']==target['source_text_sha256'] and f['source_field']==target['source_field']
   assert row['active_review_path']==target['active_ledger_path'] and row['existing_parent_decision']=='register'
   removed.append({**target,'original_queue_line_sha256':sha(line),'source_record_sha256':row['source_record_sha256']});seen.add(key)
 else:remaining.append(line)
assert old_field_count==6501 and seen==set(targets) and len(remaining)==3404
counts=collections.Counter(f['language'] for line in remaining for f in json.loads(line)['fields'])
assert counts=={'hi':3310,'ur':3101}
new=gzip.compress(b''.join(remaining),mtime=0)
assert gzip.decompress(new)==b''.join(line for line in lines if json.loads(line)['id'] not in {k[0] for k in targets})
report={'schema':'hadith-bank-exact-disjoint90-language-queue-composition-v1','status':'PASS',
 'base_review_publication':'6b20d4578c85ec2a8fb00bb7a7796f487cde755f',
 'queue_path':QUEUE.as_posix(),'before_sha256':sha(baseline),'before_git_blob_sha1':git(baseline),
 'after_sha256':sha(new),'after_git_blob_sha1':git(new),'input_packages':packages,
 'before_occurrences':3484,'before_fields':6501,'removed_occurrences':80,'removed_fields':90,
 'removed_languages':{'hi':10,'ur':80},'remaining_occurrences':3404,'remaining_fields':6411,
 'remaining_by_language':dict(counts),'all_remaining_json_line_bytes_and_order_exact':True,
 'all90_final_field_decisions_read_admitted_and_source_hash_bound':True,
 'all80_parent_dispositions_unchanged':'register','source_count_delta':0,'parent_registration_delta':0,
 'scope':'Compose only the two approved original-cohort language extensions. Individual candidate queues remain archived as evidence; this combined queue is the canonical output. No other pending field is removed.',
 'removed':removed}
put(OUT/QUEUE,new);put(OUT/REPORT/'phase15-original90-combined-queue-delta.json',enc(report))
put(OUT/REPORT/'phase15-original90-combined-queue-builder.py',Path(__file__).read_bytes())
files=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file():
  b=p.read_bytes();files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)})
m={'schema':'hadith-bank-exact-queue-composition-delivery-v1','status':'PASS','files':files,
 'summary':{k:report[k] for k in ['before_fields','removed_fields','remaining_fields','remaining_occurrences','remaining_by_language']}}
put(HERE/'delivery-manifest.json',enc(m));print(json.dumps({'manifest_sha256':sha(enc(m)),'queue_sha256':sha(new),'files':len(files),'bytes':sum(f['bytes'] for f in files),**m['summary']},indent=2))
