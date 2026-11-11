#!/usr/bin/env python3
"""Apply evidence-qualified metadata and validate the extraction outputs."""
from pathlib import Path
import collections, hashlib, json, re, shutil
import fitz

BASE=Path(__file__).resolve().parent
OUT=BASE/'extracted'
SRC=BASE.parent/'source-extracted/vietnamese/Sunan Abu Dawud'
VISUAL_SCOPES={
 '2307':{2:'Parallel columns, initial narration labels997/998, honorific glyphs, and corrupted Arabic embedded mapping.'},
 '2479':{6:'Printed narration labels1887/1888/1889.',7:'Printed jump from1889 to1900 across pp6–7, both Vietnamese and Arabic labels.'},
 '2378':{2:'First printed narration label1372; rejected initial family-based font-mapping change.'},
 '2335':{22:'Long footnote9 visibly overlays the two narration columns.'},
 '2405':{1:'Named cover credit Abu Rohman Anas and UIA Malaysia; explicit translator role absent on this cover.'},
}

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def finalize(out=OUT):
 sources=[];failures=[];total_records=total_pages=total_footnotes=total_chapters=0;ids=set()
 source_metadata={}
 for folder in sorted(x for x in out.iterdir() if x.is_dir()):
  if not (folder/'records.json').exists():continue
  source=json.loads((folder/'source.json').read_text())
  sid=source['source_id'];fp=SRC/source['source_filename']
  records=json.loads((folder/'records.json').read_text());pages=[json.loads(l) for l in (folder/'pages.jsonl').open()]
  roles=[];page_index={}
  for p in pages:
   pn=p['pdf_page'];scope=VISUAL_SCOPES.get(sid,{}).get(pn)
   p['visual_reviewed']=bool(scope)
   p['visual_review_scope']=scope
   p['character_fidelity_review_complete']=False
   page_index[pn]={l['line_id']:l for l in p['lines']}
   for l in p['lines']:
    if re.search(r'Chuyển ngữ|Chuyễn ngữ',l['text']):
     roles.append({'text':l['text'].strip(),'pdf_page':pn,'line_id':l['line_id'],'bbox':l['bbox']})
  explicit=bool(roles)
  source['translator_role_evidence']=roles
  source['translator_role_status']='explicit_in_this_pdf' if explicit else 'name_credited_role_inferred_from_same_uploaded_series'
  source['ai_translation']=False if explicit else 'unknown'
  source['translation_origin']='human_published_translation' if explicit else 'human_credit_present_role_inferred'
  source['visual_review_pages']=[{'pdf_page':pn,'scope':scope} for pn,scope in VISUAL_SCOPES.get(sid,{}).items()]
  source['full_character_fidelity_review_complete']=False
  source['numeric_glyph_decoder_version']='2.0.0-exact-resource-ascii-digits'
  source['numeric_glyph_repairs']=len(json.loads((folder/'numeric-glyph-repair-log.json').read_text()))
  for r in records:
   r['ai_translation']=source['ai_translation']
   r['translation_origin']['type']=source['translation_origin']
   r['translation_origin']['translator_role_evidence']=roles
   r['translation_origin']['role_status']=source['translator_role_status']
   r['translation_origin']['evidence']=('Named person and explicit translation role printed in this PDF.' if explicit else 'A person is named in this PDF. Translation role is inferred from earlier booklets in the same uploaded series; this PDF does not explicitly state the role in its text layer. AI status retained as unknown.')
   r['translation_origin']['ai_translation_performed_during_extraction']=False
   r['printed_hadith_number_raw']=r['printed_hadith_number']
   r['number_extraction_status']='embedded_ascii_retained_exact_resource_glyph_check_found_no_change'
   if r['id'] in ids:failures.append({'type':'duplicate_stable_id','id':r['id']})
   ids.add(r['id'])
   if not r['translation_text'].strip():failures.append({'type':'empty_translation','id':r['id']})
   if r['arabic_text'] is not None:failures.append({'type':'unapproved_arabic_promoted','id':r['id']})
   for ref in [r['marker_line']]+r['line_refs']+r['arabic_line_refs']:
    if ref['line_id'] not in page_index.get(ref['pdf_page'],{}):failures.append({'type':'missing_line_ref','id':r['id'],'ref':ref})
   full='\n'.join(l['text'].rstrip() for l in r['translation_source_lines'])
   if full!=r['translation_full_text']:failures.append({'type':'record_text_reconstruction_mismatch','id':r['id']})
   if hashlib.sha256(full.encode()).hexdigest()!=r['source_text_hash_sha256']:failures.append({'type':'record_hash_mismatch','id':r['id']})
  doc=fitz.open(fp)
  if hashlib.sha256(fp.read_bytes()).hexdigest()!=source['source_sha256']:failures.append({'type':'source_hash_changed','source_id':sid})
  if len(doc)!=len(pages):failures.append({'type':'page_count_mismatch','source_id':sid})
  for p in pages:
   if p['text_native']!=doc[p['pdf_page']-1].get_text():failures.append({'type':'raw_page_text_mismatch','source_id':sid,'pdf_page':p['pdf_page']})
  stats={'source_id':sid,'source_sha256':source['source_sha256'],'pdf_pages':len(pages),'records':len(records),
    'chapters':len(json.loads((folder/'chapters.json').read_text())),
    'footnotes':len(json.loads((folder/'footnotes.json').read_text())),
    'printed_number_gaps':source['printed_number_gaps'],'duplicate_numbers':source['duplicate_numbers'],
    'records_without_separate_printed_vi_grade':sum(not r['grades'] for r in records),
    'ai_translation':source['ai_translation'],'translator_role_status':source['translator_role_status'],
    'numeric_glyph_repairs':source['numeric_glyph_repairs'],
    'glyph_alignment_status_counts':dict(collections.Counter(d['status'] for d in json.loads((folder/'glyph-repair-page-diagnostics.json').read_text())))}
  sources.append(stats);source_metadata[sid]=source
  total_records+=len(records);total_pages+=len(pages);total_chapters+=stats['chapters'];total_footnotes+=stats['footnotes']
  dump(folder/'source.json',source);dump(folder/'records.json',records)
  with (folder/'pages.jsonl').open('w',encoding='utf-8') as f:
   for p in pages:f.write(json.dumps(p,ensure_ascii=False)+'\n')
 summary=json.loads((out/'summary.json').read_text())
 summary['sources']=[{**source_metadata[s['source_id']],'output_directory':s['output_directory']} for s in summary['sources']]
 dump(out/'summary.json',summary)
 report={'status':'mechanical_extraction_checks_passed' if not failures else 'failed','source_count':len(sources),
   'pdf_pages':total_pages,'numbered_occurrence_records':total_records,'chapter_headings':total_chapters,'footnote_objects':total_footnotes,
   'actual_visual_inspection_pages':sum(len(v) for v in VISUAL_SCOPES.values()),
   'visual_scope':'Six distinct pages inspected for layout, numbering or credit evidence; this is not all-page or character-level independent review.',
   'full_character_fidelity_review_complete':False,'arabic_transcription_approved':False,
   'all_native_page_texts_compared_against_source':True,
   'source_pdf_bytes_hash_verified':True,'every_record_nonempty':not any(f['type']=='empty_translation' for f in failures),
   'record_line_references_verified':True,'record_source_text_hashes_verified':True,
   'numeric_glyph_repairs_applied':sum(s['numeric_glyph_repairs'] for s in sources),
   'source_defects':[{'source_id':'2479','pdf_pages':[6,7],'printed_pages':['585','586'],'detail':'Printed numbering jumps1889→1900 in both columns; no invented records1890–1899.'},
                     {'source_id':'2335','pdf_page':22,'printed_page':'346','printed_number':'1247','detail':'Footnote9 overlaps narration text; both embedded layers retained, source image obstructed.'}],
   'unresolved':['Arabic embedded glyph mapping/ordering errors; original PDF retained, approved Arabic null.',
                 'Honorific glyphs are source-font private-use characters and need an evidenced display mapping.',
                 'Vietnamese full character fidelity and internal commentary/narration boundaries require independent review.',
                 'Exact canonical variant/chain crosswalk not independently established.',
                 'Footnotes with additional quoted narrations remain footnote objects; ancillary-occurrence classification review is pending.'],
   'sources':sources,'failures':failures}
 dump(out/'validation-report.json',report)
 print(json.dumps({k:report[k] for k in ['status','source_count','pdf_pages','numbered_occurrence_records','chapter_headings','footnote_objects','numeric_glyph_repairs_applied','failures']},ensure_ascii=False))
 return report

if __name__=='__main__':finalize()
