"""Read-only exact field display, gated on frozen own original readings."""
import gzip, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PRIMARY=ROOT.parent/'phase23-checkpoint64f4-bukhari30-review'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((ROOT/'complete-independent-source-first-readings.json').read_bytes())=='da0ae55af31743029a6e6fead8edf08edc678ea63c42b2e93e4cbd7415ec3cc2'
mp=PRIMARY/'delivery-manifest-v1.json'
assert sha(mp.read_bytes())=='98355c7137fb76a49d6fafe206c101d39a844d84f8806d13744d51f13affa6db'
m=json.loads(mp.read_bytes())
ap='imports/web-deenhindi-20261112/reviews/source-review-checkpoint64f4-bukhari30-20261113.json.gz'
e=next(x for x in m['files'] if x['path']==ap)
b=Path(e['local_path']).read_bytes();assert sha(b)==e['sha256']
byid={x['id']:x for x in json.loads(gzip.decompress(b))['records']}
rows=[json.loads(x) for x in (ROOT/'input/full-field-reading-input-66.jsonl').read_text().splitlines()]
for r in rows[int(sys.argv[1]):int(sys.argv[2])]:
 f=next(x for x in byid[r['occurrence_id']]['field_reviews'] if x['language']==r['language'])
 t=r['text'];assert sha(t.encode())==f['text_sha256']
 print('\n###',r['occurrence_id'],r['language'],len(t),'chars')
 print('REASON',f['reason'].split(' Complete-field reading:')[0])
 pos=0;seen=set()
 for s in f['spans']:
  assert pos<=s['start']<s['end']<=len(t)
  assert sha(t[s['start']:s['end']].encode())==s['sha256']
  if pos<s['start']:print('CONTEXT',f'[{pos},{s["start"]})',repr(t[pos:s['start']]))
  print('SELECTED',f'[{s["start"]},{s["end"]})',repr(t[s['start']:s['end']]))
  lab={k:v for k,v in s.items() if k not in ('start','end','sha256','reason')}
  ls=json.dumps(lab,ensure_ascii=False,sort_keys=True)
  if ls not in seen:print('LABEL',ls);seen.add(ls)
  pos=s['end']
 if pos<len(t):print('CONTEXT',f'[{pos},{len(t)})',repr(t[pos:]))
