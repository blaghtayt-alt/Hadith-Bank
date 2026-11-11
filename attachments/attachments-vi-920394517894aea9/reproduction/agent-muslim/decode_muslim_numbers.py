#!/usr/bin/env python3
"""Add exact-font-resource decoded digit derivatives; retain all raw text.
Run extract_muslim.py first, then this script with the v2 helper location.
"""
from pathlib import Path
from collections import Counter
import sys,json,re,argparse,hashlib,fitz,importlib.util

def load(path):return json.loads(path.read_text())
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def save_lines(path,rows):path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).parent/'extracted');ap.add_argument('--source',type=Path,default=Path(__file__).parent.parent/'source-extracted/vietnamese/Sahih Muslim');ap.add_argument('--helper',type=Path,default=Path(__file__).parent.parent/'agent-schema/glyph_cmap_repair.py');a=ap.parse_args()
 sp=importlib.util.spec_from_file_location('glyph_cmap_repair',a.helper);mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
 if mod.REPAIR_VERSION!='2.0.0-exact-resource-ascii-digits':raise RuntimeError('unexpected helper version')
 exspec=importlib.util.spec_from_file_location('extract_muslim',Path(__file__).with_name('extract_muslim.py'));ex=importlib.util.module_from_spec(exspec);exspec.loader.exec_module(ex)
 manifest=load(a.root/'manifest.json');total_repairs=0;total_ref_changes=0;report=[]
 for src in manifest['sources']:
  d=a.root/Path(src['directory']).name;s=load(d/'source.json');records=load(d/'records.json');chapters=load(d/'chapters.json');pages=[json.loads(x) for x in (d/'pages.jsonl').read_text().splitlines()];lines=[json.loads(x) for x in (d/'lines.jsonl').read_text().splitlines()];byid={x['line_id']:x for x in lines};p=a.source/s['source_filename']
  if hashlib.sha256(p.read_bytes()).hexdigest()!=s['sha256']:raise RuntimeError('source hash mismatch')
  doc=fitz.open(p);decoder=mod.GlyphMapDecoder(doc);changes=[];diagnostics=[]
  for pi,page in enumerate(doc,1):
   pd,cs=decoder.repair_page(page);diagnostics.append(pd['glyph_repair_diagnostics']);changes.extend(cs)
   for bi,b in enumerate(pd['blocks']):
    for li,line in enumerate(b.get('lines',[])):
     key=f'p{pi:04d}-b{bi:04d}-l{li:03d}'
     if key not in byid:continue
     row=byid[key];original=''.join(sp['raw_text'] for sp in line['spans']);decoded=''.join(sp['text'] for sp in line['spans'])
     if original!=row['text']:raise RuntimeError('raw line mismatch after resource decoder: '+key)
     row['font_decoded_text']=decoded;row['font_digit_repair_count']=sum(sp['repair_count'] for sp in line['spans'])
     if row['role']=='running_footer' and re.fullmatch(r'\s*\d+\s*',original):pages[pi-1]['printed_page_font_decoded']=decoded.strip()
  refchanges=[]
  for r in records:
   def rebuild(key):return '\n'.join(byid[x['line_id']].get('font_decoded_text',byid[x['line_id']]['text']) for x in r[key])
   tx=rebuild('translation_spans');ar=rebuild('arabic_spans');match=ex.LABEL.match(tx.lstrip())
   r['translation_font_decoded']=tx.lstrip()[match.end():].lstrip() if match else tx
   r['translation_search_font_decoded']=re.sub(r'\s+',' ',r['translation_font_decoded']).strip();r['arabic_font_decoded']=ar or None
   r['printed_label_font_decoded']=match.group(0) if match else None
   r['local_number_font_decoded']=(match.group('local') or match.group('local_inner')) if match else None
   r['reference_number_font_decoded']=(match.group('reference') or match.group('reference_inner')) if match else None
   r['number_decoding_method']='embedded_font_exact_content_stream_resource_glyph_id; unambiguous_ASCII_digits_only'
   r['font_digit_repair_count']=sum(byid[q['line_id']]['font_digit_repair_count'] for key in ['translation_spans','arabic_spans'] for q in r[key])
   if r['printed_label_raw']!=r['printed_label_font_decoded']:refchanges.append({'record_id':r['id'],'before':r['printed_label_raw'],'after':r['printed_label_font_decoded']})
   for key in ['translation_spans','arabic_spans']:
    for q in r[key]:q['printed_page_font_decoded']=pages[q['pdf_page']-1].get('printed_page_font_decoded',q['printed_page_raw'])
   for fn in r['footnotes']:fn['text_font_decoded']='\n'.join(byid[q['line_id']]['font_decoded_text'] for q in fn['spans'])
  for c in chapters:
   c['title_vi_font_decoded']='\n'.join(byid[q['line_id']]['font_decoded_text'] for q in c['spans']);c['title_arabic_font_decoded']='\n'.join(byid[q['line_id']]['font_decoded_text'] for q in c['arabic_spans']) or None
  s['numeric_decode_version']=mod.REPAIR_VERSION;s['numeric_decode_status']='derivative_only_raw_source_preserved';save(d/'source.json',s)
  save(d/'records.json',records);save(d/'chapters.json',chapters);save_lines(d/'pages.jsonl',pages);save_lines(d/'lines.jsonl',lines);save_lines(d/'glyph-digit-repairs.jsonl',changes);save(d/'glyph-decoder-diagnostics.json',{'version':mod.REPAIR_VERSION,'font_diagnostics':decoder.font_diagnostics,'page_diagnostics':diagnostics,'printed_label_changes':refchanges})
  status=Counter(x['status'] for x in diagnostics);fails=[x for x in diagnostics if x['status']!='exact_content_stream_resource_alignment']
  record={'source_id':s['source_id'],'source_filename':s['source_filename'],'records_before':src['records'],'records_after':len(records),'glyph_digit_repairs':len(changes),'printed_label_changes':len(refchanges),'page_diagnostic_status_counts':dict(status),'fail_closed_pages':[x['pdf_page'] for x in fails]}
  report.append(record);total_repairs+=len(changes);total_ref_changes+=len(refchanges);print(json.dumps(record,ensure_ascii=False))
 save(a.root/'numeric-decoding-report.json',{'version':mod.REPAIR_VERSION,'glyph_digit_repairs':total_repairs,'printed_label_changes':total_ref_changes,'raw_text_preserved':True,'record_counts_preserved':all(r['records_before']==r['records_after'] for r in report),'canonical_references_verified':False,'scope':'digits only; Arabic wording, letters, diacritics and ordering remain unverified','sources':report})
if __name__=='__main__':main()
