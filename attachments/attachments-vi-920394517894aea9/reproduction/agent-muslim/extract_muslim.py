#!/usr/bin/env python3
"""Lossless-evidence-first extraction of the supplied Vietnamese Muslim PDFs.
Does not OCR, infer canonical numbering, or certify the broken Arabic text layer.
"""
from pathlib import Path
from collections import Counter
import fitz, json, hashlib, re, unicodedata, argparse, sys

BASE=Path(__file__).resolve().parent.parent
DEFAULT_SOURCE=BASE/'source-extracted/vietnamese/Sahih Muslim'
DEFAULT_OUT=BASE/'agent-muslim/extracted'
LABEL=re.compile(r'^(?P<anomaly>[MÔ])?(?:(?P<local>\d+)\s*[-–]\s*\((?P<reference>\d+\s*[a-z]?)\)|\((?:(?P<local_inner>\d+)\s*[-–]\s*)?(?P<reference_inner>\d+\s*[a-z]?)\))',re.I)
CHAPTER=re.compile(r'^Chương\s+(\d+)\s*[:.]',re.I)
VISUAL_PAGES={'2390':[2,36],'2416':[15],'2441':[20,21,35,36,46],'2460':[47],'2471':[47,48],'2493':[7],'2506':[34],'2564':[29,30,33]}
IMAGE_CREDITS={'2460':{'name':'ABU FADIL','role':'Chuyển ngữ','pdf_page':47},'2471':{'name':'ABU FADIL','role':'Chuyển ngữ','pdf_page':47}}

def sha(data): return hashlib.sha256(data).hexdigest()
def jwrite(path,data): path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jlines(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n' for v in data),encoding='utf-8')
def latin_count(t):return sum('LATIN' in unicodedata.name(c,'') and c.isalpha() for c in t)
def arabic_count(t):return sum('ARABIC' in unicodedata.name(c,'') and c.isalpha() for c in t)
def joined(rows):return '\n'.join(r['text'] for r in rows)
def search_text(s):return re.sub(r'\s+',' ',s).strip()
def refs(rows):return [{'line_id':r['line_id'],'pdf_page':r['pdf_page'],'printed_page_raw':r['printed_page_raw'],'bbox':r['bbox']} for r in rows]
def red(color):return ((color>>16)&255)>140 and ((color>>8)&255)<100 and (color&255)<100

def process(path,out):
 rawpdf=path.read_bytes();digest=sha(rawpdf);short=digest[:16];prefix=path.name[:4]
 doc=fitz.open(path);docid=f'vi-muslim-pdf-{short}';edition=out/f'pdf-{short}';edition.mkdir(parents=True,exist_ok=True)
 allrows=[];pages=[];page_labels=[]
 for pi,page in enumerate(doc,1):
  pd=page.get_text('dict');rows=[];page_label=None
  for bi,block in enumerate(pd['blocks']):
   for li,line in enumerate(block.get('lines',[])):
    text=''.join(span['text'] for span in line['spans'])
    if not text.strip():continue
    colors=Counter();fonts=Counter()
    for sp in line['spans']:
     colors[sp['color']]+=len(sp['text']);fonts[sp['font']]+=len(sp['text'])
    row={'line_id':f'p{pi:04d}-b{bi:04d}-l{li:03d}','pdf_page':pi,'bbox':[round(x,3) for x in line['bbox']],'text':text,'fonts':dict(fonts),'colors':dict(colors),'max_font_size':max(s['size'] for s in line['spans']),'role':None}
    rows.append(row)
    if re.fullmatch(r'\s*\d+\s*',text) and line['bbox'][1]>page.rect.height-45:page_label=text.strip()
  for row in rows:row['printed_page_raw']=page_label
  rows.sort(key=lambda r:(r['bbox'][1],r['bbox'][0]))
  for row in rows:row['order']=len(allrows);allrows.append(row)
  pages.append({'source_id':docid,'pdf_page':pi,'printed_page_raw':page_label,'printed_page_status':'embedded_text_unverified','width_points':page.rect.width,'height_points':page.rect.height,'raw_text':page.get_text(),'raw_text_sha256':sha(page.get_text().encode()),'line_ids':[r['line_id'] for r in rows],'image_review_performed':pi in VISUAL_PAGES.get(prefix,[])})
  page_labels.append(page_label)
 records=[];chapters=[];pending_ar=[];pending_heading_ar=[];current=None;current_chapter=None;heading_mode=False;footnote_mode=False;back=False;front=[];backrows=[];unassigned=[]
 def finish():
  nonlocal current
  if current is None:return
  rows=current.pop('_translation_rows');ar=current.pop('_arabic_rows');fn=current.pop('_footnote_rows')
  raw=joined(rows);m=LABEL.match(raw.lstrip());body=raw.lstrip()[m.end():].lstrip() if m else raw
  current.update({'translation_raw':raw,'translation_text':body,'translation_search':search_text(body),'translation_spans':refs(rows),'arabic_raw':joined(ar) or None,'arabic_spans':refs(ar),'arabic_text':None,'arabic_text_status':'source_present_embedded_text_unreliable_not_approved','footnotes':[{'text_raw':joined(fn),'spans':refs(fn),'kind':'explicit_star_note'}] if fn else [],'narrator_prefix_raw':None,'narrator_normalized':None,'isnad':None,'grading':[],'commentary':[],'translation_content_scope':'verbatim_source_translation_with_inline_explanations; semantic_quote/commentary_boundaries_not_certified'})
  n=re.search(r'\b(?:thuật\s+lại|tường\s+thuật|kể\s+lại|truyền\s+lại)\b',body[:600],re.I)
  if n:current['narrator_prefix_raw']=body[:n.start()].strip()
  current['narrator_prefix_status']='source_introductory_phrase_not_canonical_chain'
  flags=['full_character_review_pending','arabic_glyph_order_and_diacritic_review_pending','canonical_reference_alignment_unverified','embedded_inline_commentary_boundaries_unverified']
  if any(0xE000<=ord(c)<=0xF8FF for c in raw):flags.append('private_use_honorific_glyphs_preserved')
  if any(arabic_count(r['text'])>latin_count(r['text']) and arabic_count(r['text'])>2 for r in rows):flags.append('inline_arabic_quote_embedded_text_unverified')
  if current['label_prefix_anomaly_raw']:flags.append('label_prefix_requires_source_review')
  if not ar:flags.append('no_associated_arabic_block_detected')
  current['review_flags']=flags
  current['page_start']=min(r['pdf_page'] for r in ar+rows);current['page_end']=max(r['pdf_page'] for r in ar+rows)
  current['translation_page_start']=min(r['pdf_page'] for r in rows);current['translation_page_end']=max(r['pdf_page'] for r in rows)
  current['translation_raw_sha256']=sha(raw.encode());records.append(current);current=None
 for row in allrows:
  t=row['text'].strip();p=row['pdf_page'];height=pages[p-1]['height_points'];colors=row['colors'];dominant=int(max(colors,key=colors.get));lc=latin_count(t);ac=arabic_count(t)
  if row['bbox'][1]>height-45 and (t=='Chanlyislam' or re.fullmatch(r'\d+',t)):
   row['role']='running_footer';continue
  if p==1:row['role']='frontmatter';front.append(row);continue
  if p>=len(doc)-1 and ((prefix in IMAGE_CREDITS and p==IMAGE_CREDITS[prefix]['pdf_page'] and re.fullmatch('Chuyển ngữ',t,re.I)) or re.match(r'^(?:ABU\s+FA[UD]*IL|Abu\s+Fa[ud]*il)\b',t,re.I) or re.search(r'Hết Phần|CÒN TIẾP',t,re.I)):
   back=True;finish()
  if back:row['role']='backmatter';backrows.append(row);continue
  m=LABEL.match(t) if lc>3 else None
  if m and not (m.group('local') or m.group('local_inner')):
   rv=m.group('reference') or m.group('reference_inner')
   if rv.isdigit() and int(rv)<100:m=None
  if m:
   finish();heading_mode=False;footnote_mode=False
   current={'id':f'{docid}:occ:{len(records)+1:05d}','sequence':len(records)+1,'source_id':docid,'language':'vi','book_id':'muslim','printed_label_raw':m.group(0),'printed_number_status':'embedded_text_unverified','local_number_raw':m.group('local') or m.group('local_inner'),'reference_number_raw':m.group('reference') or m.group('reference_inner'),'label_prefix_anomaly_raw':m.group('anomaly'),'canonical_number':None,'chapter_id':current_chapter['id'] if current_chapter else None,'_translation_rows':[row],'_arabic_rows':pending_ar,'_footnote_rows':[],'release_status':'initial_extraction_with_review_pending'}
   row['role']='translation';row['record_id']=current['id']
   for a in pending_ar:a['role']='arabic_narration_raw';a['record_id']=current['id']
   pending_ar=[];continue
  cm=CHAPTER.match(t) if lc>3 else None
  if cm:
   finish();footnote_mode=False;heading_mode=True
   if pending_ar:
    for r in pending_ar:r['role']='unassigned_source_text';unassigned.append(r)
    pending_ar=[]
   current_chapter={'id':f'{docid}:chapter:{len(chapters)+1:03d}','number_raw':cm.group(1),'number_status':'embedded_text_unverified','_rows':[row],'_arabic_rows':pending_heading_ar}
   for a in pending_heading_ar:a['role']='chapter_arabic_raw';a['chapter_id']=current_chapter['id']
   pending_heading_ar=[];row['role']='chapter_heading';row['chapter_id']=current_chapter['id'];chapters.append(current_chapter);continue
  # Source-image-verified red narration (402b); color alone does not make it a heading.
  if prefix=='2441' and p==21 and any(row['line_id'].startswith('p0021-'+block+'-') for block in ['b0001','b0002','b0003']):
   row['role']='pending_arabic';pending_ar.append(row);heading_mode=False;footnote_mode=False;continue
  # Source-image-verified blue chapter block, including its separately positioned number.
  if prefix=='2416' and p==15 and row['line_id'].startswith('p0015-b0007-'):
   row['role']='pending_arabic_heading';pending_heading_ar.append(row);continue
  # Red Arabic chapters and their numeric fragments are kept outside narration.
  if red(dominant) and (ac>0 or lc<4):
   row['role']='pending_arabic_heading';pending_heading_ar.append(row);continue
  # Complete Arabic narration blocks use the source's blue color. This also
  # captures separately positioned numeric/suffix fragments without assuming their order.
  is_blue=dominant==8288 and (lc<4 or ac>lc)
  is_ar=ac>lc or (lc<4 and any('KFGQPC' in f or 'Courier' in f for f in row['fonts']))
  black_arabic_region=(prefix=='2564' and ((p==29 and row['bbox'][1]>=400) or (p==30 and row['bbox'][1]<516) or (p==33 and 65<=row['bbox'][1]<375)))
  if is_blue or (is_ar and dominant!=0) or black_arabic_region:
   row['role']='pending_arabic';pending_ar.append(row);heading_mode=False;footnote_mode=False;continue
  if re.match(r'^\(\*\)',t) and current:
   footnote_mode=True;current['_footnote_rows'].append(row);row['role']='footnote';row['record_id']=current['id'];continue
  if footnote_mode and current:
   current['_footnote_rows'].append(row);row['role']='footnote';row['record_id']=current['id'];continue
  if heading_mode and current_chapter:
   current_chapter['_rows'].append(row);row['role']='chapter_heading';row['chapter_id']=current_chapter['id'];continue
  if current:
   current['_translation_rows'].append(row);row['role']='translation';row['record_id']=current['id'];continue
  row['role']='unassigned_source_text';unassigned.append(row)
 finish()
 for r in pending_ar+pending_heading_ar:r['role']='unassigned_source_text';unassigned.append(r)
 for c in chapters:
  rows=c.pop('_rows');ar=c.pop('_arabic_rows');c.update({'title_vi_raw':joined(rows),'title_vi_search':search_text(joined(rows)),'spans':refs(rows),'title_arabic_raw':joined(ar) or None,'arabic_spans':refs(ar),'arabic_status':'embedded_text_unverified'})
 credits=[]
 for row in front+backrows:
  if re.search(r'Abu\s+Fa[ud]*il|Chuyển ngữ|University of Madinah|Cựu sinh viên',row['text'],re.I):credits.append({'text_raw':row['text'],'pdf_page':row['pdf_page'],'line_id':row['line_id'],'bbox':row['bbox']})
 if prefix in IMAGE_CREDITS:
  ic=IMAGE_CREDITS[prefix];credits.append({'text_raw':ic['name']+' / '+ic['role'],'pdf_page':ic['pdf_page'],'evidence_type':'visual_source_image_transcription','note':'Name is graphical in PDF; role text is embedded.'})
 ctext='\n'.join(c['text_raw'] for c in credits);has_role=bool(re.search('Chuyển ngữ',ctext,re.I));names=re.findall(r'Abu\s+Fa[ud]*il',ctext,re.I)
 translator=names[0] if names else None
 ais=False if has_role and translator else 'unknown'
 source={'source_id':docid,'language':'vi','book_id':'muslim','archive_member':'vietnamese/Sahih Muslim/'+path.name,'source_filename':path.name,'sha256':digest,'bytes':len(rawpdf),'pdf_pages':len(doc),'pdf_metadata':doc.metadata,'acquisition_method':'user_supplied_zip','extraction_method':'embedded_text_with_page_line_coordinates','extractor_version':'muslim-intake-1.0','pymupdf_version':fitz.VersionBind,'source_url':None,'source_site_as_printed':'Chanlyislam','translator_name_raw':translator if has_role else None,'credited_person_raw':translator,'translator_role_evidenced':has_role,'translator_role_evidence_method':'visual_source_image' if prefix in IMAGE_CREDITS else ('embedded_text' if has_role else None),'credit_evidence':credits,'ai_translation':ais,'ai_translation_basis':'named_human_translation_credit_in_this_pdf' if ais is False else 'no_explicit_translator_role_credit_detected_in_this_pdf','frontmatter_raw':joined(front),'backmatter_raw':joined(backrows),'publication_year':None,'edition_statement':None,'canonical_numbering_system':None}
 for r in records:r['ai_translation']=ais;r['translator']=source['translator_name_raw'];r['source_sha256']=digest
 anomalies=[]
 for r in records:
  if r['label_prefix_anomaly_raw']:anomalies.append({'record_id':r['id'],'type':'label_prefix','label_raw':r['printed_label_raw'],'status':'source_image_check_pending'})
 # Repeated local ordinal labels are reported, never silently deduplicated.
 counts=Counter(r['local_number_raw'] for r in records if r['local_number_raw'])
 for n,c in counts.items():
  if c>1:anomalies.append({'type':'repeated_local_number','local_number_raw':n,'count':c,'record_ids':[r['id'] for r in records if r['local_number_raw']==n],'interpretation':'may_identify_distinct_letter_variants; not_deduplicated'})
 report={'source_id':docid,'source_sha256':digest,'pdf_pages_processed':len(pages),'page_image_reviewed':VISUAL_PAGES.get(prefix,[]),'full_character_review_completed':False,'records':len(records),'chapters':len(chapters),'line_count':len(allrows),'line_roles':dict(Counter(r['role'] for r in allrows)),'unassigned_nonfooter_line_count':len(unassigned),'unassigned_lines':[{'line_id':r['line_id'],'pdf_page':r['pdf_page'],'text':r['text']} for r in unassigned],'zero_arabic_records':[r['id'] for r in records if not r['arabic_raw']],'duplicate_record_ids':len(records)-len(set(r['id'] for r in records)),'notes':['All source pages and nonempty extracted lines are retained in evidence.','Arabic raw data is not approved Arabic text.','Number labels remain extraction values unless independently image verified.','Inline explanation and narration boundaries require further source review.']}
 jwrite(edition/'source.json',source);jwrite(edition/'records.json',records);jwrite(edition/'chapters.json',chapters);jlines(edition/'pages.jsonl',pages);jlines(edition/'lines.jsonl',allrows);jwrite(edition/'coverage.json',report);jwrite(edition/'anomalies.json',anomalies);jwrite(edition/'supplemental-source-text.json',[{'line_id':r['line_id'],'pdf_page':r['pdf_page'],'printed_page_raw':r['printed_page_raw'],'bbox':r['bbox'],'text_raw':r['text'],'classification':'unassigned_source_heading_or_layout_fragment','review_status':'pending'} for r in unassigned])
 return {'source_id':docid,'source_prefix':prefix,'source_filename':path.name,'sha256':digest,'directory':str(edition),'pdf_pages':len(pages),'records':len(records),'chapters':len(chapters),'ai_translation':ais,'unassigned_lines':len(unassigned),'page_image_reviewed':VISUAL_PAGES.get(prefix,[])}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=DEFAULT_SOURCE);ap.add_argument('--out',type=Path,default=DEFAULT_OUT);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 summaries=[]
 for path in sorted(a.source.glob('*.pdf')):
  result=process(path,a.out);summaries.append(result);print(json.dumps(result,ensure_ascii=False))
 jwrite(a.out/'manifest.json',{'sources':summaries,'source_count':len(summaries),'pdf_pages':sum(s['pdf_pages'] for s in summaries),'record_count':sum(s['records'] for s in summaries),'release_status':'initial_extraction_with_review_pending'})
if __name__=='__main__':main()
