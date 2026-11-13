"""Freeze six untouched sibling originals for two chain-only Hi/Ur parents."""
from pathlib import Path
import json, hashlib
R=Path(__file__).resolve().parent
cohort={str(x['number']):x for x in map(json.loads,(R/'input/cohort.jsonl').read_text().splitlines())}
prior=list(map(json.loads,(R/'input/full-hi-ur-reading-input-60.jsonl').read_text().splitlines()))
out=[]
for number in ('2773','2774'):
 r=cohort[number]
 template=next(x for x in prior if x['number']==number)
 for language,field in (('ar','textArabic'),('en','translationEnglish'),('ur-Latn','translationUrduRoman')):
  text=r['source_record'][field]
  assert isinstance(text,str) and text.strip()
  item=dict(template)
  item.update(language=language,source_field=field,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),characters=len(text),utf8_bytes=len(text.encode()),reading_order=61+len(out))
  out.append(item)
raw=''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in out).encode()
p=R/'input/additional2773-2774-originals-6.jsonl'
assert not p.exists()
p.write_bytes(raw)
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'fields':len(out),'characters':sum(x['characters'] for x in out),'utf8_bytes':sum(x['utf8_bytes'] for x in out)}))
