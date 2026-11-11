from pathlib import Path
from collections import Counter
import json,hashlib,re,unicodedata,argparse

def validate(root):
 m=json.loads((root/'manifest.json').read_text());errors=[];summary=[];ids=[]
 for d in sorted(root.glob('pdf-*')):
  s=json.loads((d/'source.json').read_text());rs=json.loads((d/'records.json').read_text());ps=[json.loads(l) for l in (d/'pages.jsonl').read_text().splitlines()];ls=[json.loads(l) for l in (d/'lines.jsonl').read_text().splitlines()];cs=json.loads((d/'chapters.json').read_text());byid={l['line_id']:l for l in ls}
  srcerrs=[];assigned=[]
  assert len(byid)==len(ls)
  if len(ps)!=s['pdf_pages']:srcerrs.append('page count mismatch')
  for p in ps:
   if hashlib.sha256(p['raw_text'].encode()).hexdigest()!=p['raw_text_sha256']:srcerrs.append('page evidence hash mismatch')
   if any(x not in byid for x in p['line_ids']):srcerrs.append('unresolved page line reference')
  for r in rs:
   ids.append(r['id'])
   for key,target in [('translation_spans','translation_raw'),('arabic_spans','arabic_raw')]:
    vals=[byid[q['line_id']]['text'] for q in r[key]]
    if '\n'.join(vals)!=(r[target] or ''):srcerrs.append('record evidence reconstruction mismatch: '+r['id']+':'+key)
    assigned.extend(q['line_id'] for q in r[key])
    if any(byid[q['line_id']]['pdf_page']!=q['pdf_page'] for q in r[key]):srcerrs.append('page span mismatch')
   for fn in r['footnotes']:
    vals=[byid[q['line_id']]['text'] for q in fn['spans']]
    if '\n'.join(vals)!=fn['text_raw']:srcerrs.append('footnote reconstruction mismatch')
    assigned.extend(q['line_id'] for q in fn['spans'])
   if not r['translation_text'].strip():srcerrs.append('empty translation')
   if 'arabic_font_decoded' in r:
    decoded_ar='\n'.join(byid[q['line_id']]['font_decoded_text'] for q in r['arabic_spans'])
    if decoded_ar!=(r['arabic_font_decoded'] or ''):srcerrs.append('decoded Arabic evidence reconstruction mismatch')
    for key in ['translation_spans','arabic_spans']:
     for q in r[key]:
      line=byid[q['line_id']];old=line['text'];new=line['font_decoded_text']
      if len(old)!=len(new) or any(a!=b and (a not in '0123456789' or b not in '0123456789') for a,b in zip(old,new)):srcerrs.append('non-digit decoded change')
   if r['arabic_text'] is not None or r['canonical_number'] is not None:srcerrs.append('unverified canonical field populated')
   if r['ai_translation'] not in [False,'unknown']:srcerrs.append('invalid AI status')
   if any(byid[q['line_id']]['role']!='translation' for q in r['translation_spans']):srcerrs.append('role mismatch')
  if len(assigned)!=len(set(assigned)):srcerrs.append('narration evidence double-assigned')
  if any(l['role'] is None for l in ls):srcerrs.append('unclassified line')
  if len(rs)!=next(v['records'] for v in m['sources'] if v['source_id']==s['source_id']):srcerrs.append('manifest count mismatch')
  errors.extend({'source_id':s['source_id'],'error':e} for e in srcerrs)
  summary.append({'source_id':s['source_id'],'source_filename':s['source_filename'],'pages':len(ps),'records':len(rs),'chapters':len(cs),'lines':len(ls),'ai_translation':s['ai_translation'],'visual_pages':sum(p['image_review_performed'] for p in ps),'supplemental_lines':sum(l['role']=='unassigned_source_text' for l in ls),'checks_passed':not srcerrs})
 if len(ids)!=len(set(ids)):errors.append({'error':'duplicate stable IDs across sources'})
 result={'validation_scope':'structural completeness and exact reconstruction against embedded text line evidence, not character-level PDF fidelity or canonical hadith verification','sources':len(summary),'pages':sum(s['pages'] for s in summary),'records':sum(s['records'] for s in summary),'visual_pages':sum(s['visual_pages'] for s in summary),'all_automated_checks_passed':not errors,'errors':errors,'per_source':summary}
 (root/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
 return not errors
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('root',type=Path,nargs='?',default=Path(__file__).parent/'extracted');a=ap.parse_args();raise SystemExit(0 if validate(a.root) else 1)
