#!/usr/bin/env python3
"""Conservative embedded-text extraction of the submitted bilingual PDFs.

No source wording is corrected. The Arabic text layer is retained only as raw
evidence because its font-to-Unicode map is visibly unreliable.
"""
from pathlib import Path
import collections, hashlib, json, re, statistics, sys
import fitz

BASE = Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parent/'agent-schema'))
from glyph_cmap_repair import GlyphMapDecoder
SRC = BASE.parent / 'source-extracted/vietnamese/Sunan Abu Dawud'
OUT = BASE / 'extracted'
OUT.mkdir(exist_ok=True)
RX_MARK = re.compile(r'^([0-9]{3,4})(?:\s*[-–]\s*|\s*$)')
RX_CHAP = re.compile(r'^\(([0-9]+)\)\s*(.*)')
RX_AR = re.compile(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]')
RX_PUA = re.compile(r'[\ue000-\uf8ff]')

def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def ref(l):
    return {'pdf_page':l['pdf_page'], 'line_id':l['line_id'], 'bbox':l['bbox']}

def row_key(l):
    # Baselines, not bounding-box tops, keep raised footnote signs in place.
    offset=-2.0 if l['bbox'][0]<50 and (RX_MARK.match(l['text'].strip()) or RX_CHAP.match(l['text'].strip())) else 0
    return (l['pdf_page'], round((l['baseline']+offset)/2.0)*2.0, l['bbox'][0])

def source_lines(page, page_no, decoder):
    rows=[]
    pd,changes=decoder.repair_page(page)
    for bi,b in enumerate(pd['blocks']):
        for li,l in enumerate(b.get('lines',[])):
            spans=[{k:s[k] for k in ('text','raw_text','repair_count','font','size','flags','bbox','origin')} for s in l['spans']]
            t=''.join(s['text'] for s in spans)
            visible=[s for s in spans if s['text'].strip()]
            baseline=max((s['origin'][1] for s in spans),default=l['bbox'][3])
            rows.append({'line_id':f'p{page_no:04d}-b{bi:04d}-l{li:03d}', 'pdf_page':page_no,
                         'text':t,'bbox':list(l['bbox']),'baseline':baseline,'spans':spans})
    return rows,changes

def main():
    summary=[]
    for fp in sorted(SRC.glob('*.pdf')):
        sha=hashlib.sha256(fp.read_bytes()).hexdigest()
        sid=fp.name.split('_')[0]
        sub=OUT / f'{sid}-{sha[:12]}'
        sub.mkdir(exist_ok=True)
        doc=fitz.open(fp)
        decoder=GlyphMapDecoder(doc);numeric_repairs=[]
        pages=[]; all_lines=[]; vi=[]; ar=[]; footlines=[]; other=[]; printed={}; credits=[]
        for pn,page in enumerate(doc,1):
            lines,repairs=source_lines(page,pn,decoder)
            numeric_repairs.extend(repairs)
            # Some PDF logical lines cross the column gutter. Split at span
            # boundaries; keep the original line in page evidence.
            virtual=[]
            for l in list(lines):
                if l['bbox'][0]<297.5 and l['bbox'][2]>297.5 and any(s['bbox'][0]>=298.5 for s in l['spans']):
                    left=[s for s in l['spans'] if s['bbox'][0]<298.5]
                    right=[s for s in l['spans'] if s['bbox'][0]>=298.5]
                    # True full-width Latin footnotes/colophons must stay intact.
                    if left and right and any(RX_AR.search(s['text']) for s in right) and any(re.search('[A-Za-z]',s['text']) for s in left):
                        l['region']='mixed_original_line_preserved'
                        l['_skip_classification']=True
                        for side,ss in [('vi',left),('ar',right)]:
                            ll=dict(l);ll['line_id']=l['line_id']+'-'+side;ll.pop('_skip_classification',None)
                            ll['text']=''.join(s['text'] for s in ss);ll['spans']=ss
                            ll['bbox']=[min(s['bbox'][0] for s in ss),min(s['bbox'][1] for s in ss),max(s['bbox'][2] for s in ss),max(s['bbox'][3] for s in ss)]
                            ll['baseline']=max(s['origin'][1] for s in ss if s['text'].strip())
                            ll['original_line_id']=l['line_id'];virtual.append(ll)
            lines.extend(virtual)
            labels=[l['text'].strip() for l in lines if l['bbox'][1]>780 and l['bbox'][0]>450 and re.fullmatch(r'[0-9]+',l['text'].strip())]
            printed[pn]=labels[0] if len(labels)==1 else None
            for l in lines:
                t=l['text'].strip(); x0,y0,x1,y1=l['bbox']
                if l.pop('_skip_classification',False):continue
                l['region']='unclassified'
                if not t: l['region']='whitespace'
                elif 'Chanlyislam' in t and y0>780: l['region']='footer'
                elif y0>780 and x0>450 and re.fullmatch(r'[0-9]+',t):l['region']='printed_page_label'
                elif pn==1:l['region']='front_matter'
                else:
                    sizes=[s['size'] for s in l['spans'] if s['text'].strip()]
                    maxsz=max(sizes,default=0)
                    if x0>=80 and maxsz<=11.5 and y0>50 and (x0<297.5 or re.search(r'[A-Za-z]',t)) and not (t.isdigit() and any(s['flags']&1 for s in l['spans'])):
                        l['region']='footnote'; footlines.append(l)
                    elif x0<297.5 and x1<=298.6:
                        l['region']='vietnamese_column'; vi.append(l)
                    elif x0>=297.5 and (RX_AR.search(t) or not re.search(r'[A-Za-z]',t)):
                        l['region']='arabic_column'; ar.append(l)
                    else:l['region']='full_width_or_ancillary'
                if re.search(r'Abu R[ao]hman Anas',t):
                    credits.append({'text':t,**ref(l)})
                if l['region'] not in ('vietnamese_column','arabic_column','footnote','whitespace'):
                    other.append(l)
            pages.append({'source_sha256':sha,'pdf_page':pn,'printed_page_label':printed[pn],
                          'width':page.rect.width,'height':page.rect.height,
                          'text_native':page.get_text(), 'lines':lines,
                          'visual_reviewed':False})
            all_lines.extend(lines)

        vi.sort(key=row_key)
        ar.sort(key=lambda l:(l['pdf_page'],round(l['baseline']/2)*2,-l['bbox'][2]))
        footlines.sort(key=row_key)
        # Footnotes are standalone source objects, never silently narration text.
        footnotes=[]; current_foot=None
        for l in footlines:
            m=re.match(r'^([0-9]+)\s*\.\s*(.*)',l['text'].strip())
            if m or current_foot is None:
                current_foot={'id':f'vi-abudawud-{sha[:12]}-footnote-{len(footnotes)+1:04d}',
                              'printed_number':m.group(1) if m else None,'lines':[],'link_status':'source_marker_match_required'}
                footnotes.append(current_foot)
            current_foot['lines'].append(l)
        for f in footnotes:
            f['text']='\n'.join(l['text'].rstrip() for l in f['lines'])
            f['line_refs']=[ref(l) for l in f['lines']]
            f['pdf_pages']=sorted({l['pdf_page'] for l in f['lines']})
            f['contains_possible_ancillary_narration']=bool(re.search(r'Thiên sứ.*(?:nói|phán)|Sứ giả.*nói',f['text'],re.S))
            del f['lines']

        chapters=[]; records=[]; events=[]; current=None; chap=None; stopped=False
        for l in vi:
            t=l['text'].strip()
            if sid=='2319' and l['pdf_page']==29 and t in ('كتاب الصالة','ُآخ ر'):
                l['region']='closing_arabic_colophon';other.append(l)
                if not stopped:events.append({'kind':'end','at':(l['pdf_page'],l['baseline'])})
                stopped=True;current=None;continue
            m=RX_MARK.match(t) if l['bbox'][0]<50 else None
            c=RX_CHAP.match(t) if l['bbox'][0]<50 else None
            if m:
                current={'id':f'vi-abudawud-{sha[:12]}-occ-{len(records)+1:04d}',
                         'language':'vi','collection':'sunan-abu-dawud','source_id':sid,'source_sha256':sha,
                         'source_filename':fp.name, 'occurrence_sequence':len(records)+1,
                         'printed_hadith_number':m.group(1),'chapter':chap,'_lines':[],
                         '_start':(l['pdf_page'],l['baseline']), 'marker_line':ref(l),
                         'numbering_system':'number printed in this Vietnamese PDF; canonical crosswalk not independently verified',
                         'release_status':'initial_extraction_with_review_pending'}
                records.append(current);events.append({'kind':'record','record':current,'at':current['_start']})
                stopped=False
                rest=t[m.end():]
                if rest:
                    cpy=dict(l);cpy['text']=rest;cpy['source_number_removed']=m.group(0);current['_lines'].append(cpy)
            elif c:
                chap={'id':f'vi-abudawud-{sha[:12]}-chapter-{len(chapters)+1:04d}', 'number':c.group(1),
                      'title':c.group(2),'line_refs':[ref(l)],'_collecting':True}
                chapters.append(chap);events.append({'kind':'chapter','chapter':chap,'at':(l['pdf_page'],l['baseline'])})
                current=None
            elif re.search(r'Abu R[ao]hman Anas|^Cựu sinh viên|^Chuy[eểễ]n ngữ|^Chuyễn ngữ|^Kết thúc|^HẾT PHẦN|^Sách (?:Lễ|Sujud)',t):
                l['region']='closing_credit_or_colophon';other.append(l)
                if not stopped:
                    events.append({'kind':'end','at':(l['pdf_page'],l['baseline'])})
                stopped=True;current=None
            elif chap and chap['_collecting'] and current is None:
                # Chapter titles wrap over multiple bold lines before next number.
                alpha=''.join(ch for ch in t if ch.isalpha())
                if alpha and alpha.upper()==alpha and not RX_AR.search(t):
                    chap['title']=(chap['title']+'\n'+t).strip();chap['line_refs'].append(ref(l))
                else:other.append(l)
            elif current and not stopped:
                current['_lines'].append(l)
            else:other.append(l)

        # Arabic raw lines are associated by the aligned left-column occurrence
        # start and chapter boundaries; this is explicitly a candidate alignment.
        events.sort(key=lambda e:e['at'])
        for i,event in enumerate(events):
            if event['kind']!='record':continue
            r=event['record']; start=event['at']; end=events[i+1]['at'] if i+1<len(events) else (len(doc)+1,0)
            r['_arabic_lines']=[l for l in ar if (l['pdf_page'],l['baseline']) >= (start[0],start[1]-1.5)
                               and (l['pdf_page'],l['baseline']) < (end[0],end[1]-1.5)]

        exceptions=[]
        for r in records:
            lines=r.pop('_lines');r.pop('_start')
            arabic=r.pop('_arabic_lines',[])
            full='\n'.join(l['text'].rstrip() for l in lines)
            r['translation_full_text']=full
            r['translation_source_lines']=[{'text':l['text'],**ref(l)} for l in lines]
            r['source_commentary']=[];r['grades']=[];body=[];comment=[];grade=[];mode='body'
            def flush_comment():
                if comment:
                    r['source_commentary'].append({'type':'explicit_compiler_commentary_candidate','text':'\n'.join(l['text'].rstrip() for l in comment),'line_refs':[ref(l) for l in comment], 'review_status':'boundary_review_pending'})
                    comment.clear()
            def flush_grade():
                if grade:
                    gt='\n'.join(l['text'].rstrip() for l in grade)
                    gm=re.search(r'Xếp loại:\s*(.*?)(?:\s*\(([^()]*)\))?\s*$',gt,re.S)
                    r['grades'].append({'text':gt,'grade_as_printed':gm.group(1).strip() if gm else None,
                                        'attributed_to_as_printed':gm.group(2) if gm else None,
                                        'scope':'this numbered occurrence as printed; clause/chain applicability not independently adjudicated',
                                        'verification':'source_reported_only','line_refs':[ref(l) for l in grade]})
                    grade.clear()
            for l in lines:
                t=l['text'].strip()
                if 'Xếp loại:' in t:
                    marker=t.index('Xếp loại:')
                    prefix=t[:marker].strip()
                    if prefix.strip('- '):
                        before=dict(l);before['text']=prefix;before['text_slice']='before_inline_grade_marker'
                        (comment if mode=='comment' else body).append(before)
                        l=dict(l);l['text']=t[marker:];l['text_slice']='from_inline_grade_marker'
                    dash=None
                    prior=comment if mode=='comment' else body
                    if prior and prior[-1]['text'].strip()=='-':dash=prior.pop()
                    flush_comment();flush_grade()
                    if dash:grade.append(dash)
                    grade.append(l);mode='grade'
                elif re.match(r'^(?:Imam|Imam\s+Abu)\s+Abu\s+Dawud|^Imam Abu Dawud',t):
                    flush_grade();flush_comment();comment.append(l);mode='comment'
                elif mode=='grade':
                    # Grade entries occasionally wrap; remain separate until a
                    # clear new compiler paragraph. Ambiguity remains visible.
                    grade.append(l)
                elif mode=='comment':comment.append(l)
                else:body.append(l)
            flush_comment();flush_grade()
            r['translation_text']='\n'.join(l['text'].rstrip() for l in body)
            r['content_type']='numbered_narration_or_report'
            if not r['translation_text'] and r['source_commentary']:
                r['translation_text']='\n'.join(c['text'] for c in r['source_commentary'])
                r['content_type']='numbered_occurrence_beginning_with_compiler_commentary'
                exceptions.append({'record_id':r['id'],'type':'numbered_compiler_commentary_or_variant','detail':'Occurrence begins with explicit Abu Dawud commentary; full content retained, internal narration boundaries need review.'})
            elif not r['translation_text']:
                exceptions.append({'record_id':r['id'],'type':'empty_primary_translation','detail':'All extracted Vietnamese lines classified as grading; inspect source.'})
            first=' '.join(l['text'].strip() for l in body[:5])
            nm=re.match(r'((?:Ông|Bà)\s+.+?)(?=\s+(?:kể lại|thuật lại|nói(?:\s|:)|thuật rằng|truyền thuật))',first)
            r['narrator']={'name_verbatim':nm.group(1) if nm else None,
                           'evidence':first if nm else None,'normalization':None,
                           'status':'source_opening_phrase_only' if nm else 'not_separately_resolved'}
            r['arabic_text']=None
            r['arabic_raw_text']='\n'.join(l['text'].rstrip() for l in arabic)
            r['arabic_line_refs']=[ref(l) for l in arabic]
            r['arabic_status']='unverified_embedded_text_with_font_mapping_corruption'
            r['arabic_alignment_status']='candidate_by_parallel_column_position_not_independently_verified'
            r['isnad']=None
            r['canonical_reference']=None
            refs=[ref(l) for l in lines]
            r['line_refs']=refs
            r['pdf_pages']=sorted({r['marker_line']['pdf_page']}|{l['pdf_page'] for l in lines}|{l['pdf_page'] for l in arabic})
            r['printed_pages']=[{'pdf_page':p,'printed_page_label':printed[p]} for p in r['pdf_pages']]
            note_markers=[]
            for l in lines:
                for s in l['spans']:
                    if s['text'].strip().isdigit() and s['flags']&1:
                        note_markers.append({'number':s['text'].strip(), 'pdf_page':l['pdf_page'],'line_id':l['line_id']})
            r['footnote_markers']=note_markers
            r['footnotes']=[{**f,'link_status':'same_page_printed_superscript_number_match'} for f in footnotes if any(n['number']==f['printed_number'] and n['pdf_page'] in f['pdf_pages'] for n in note_markers)]
            r['ai_translation']=False
            r['translation_origin']={'type':'human_published_translation','evidence':'Named translation credits printed in this source PDF.', 'translator_credit_variants':credits}
            r['quality_flags']=['vietnamese_character_fidelity_review_pending','special_font_pua_requires_display_mapping','arabic_font_mapping_corruption','canonical_alignment_not_verified','narration_commentary_boundary_review_pending']
            r['pua_characters']=sorted(set(RX_PUA.findall(full)))
            r['source_text_hash_sha256']=hashlib.sha256(full.encode()).hexdigest()
        for c in chapters:c.pop('_collecting',None)
        nums=[int(r['printed_hadith_number']) for r in records]
        counts=collections.Counter(nums)
        gaps=sorted(set(range(min(nums),max(nums)+1))-set(nums)) if nums else []
        duplicates=[{'number':k,'count':v} for k,v in counts.items() if v>1]
        if gaps:exceptions.append({'type':'printed_number_sequence_gaps','numbers':gaps, 'source_visual_confirmation':{'pdf_pages':[6,7],'printed_pages':['585','586'],'observed':'Printed labels jump directly from1889 to1900 in both columns.'} if sid=='2479' else None})
        if sid=='2335':
            exceptions.append({'type':'source_layout_overlap','pdf_page':22,'printed_page':'346','printed_hadith_number':'1247','detail':'Long Tabaristan footnote9 overlays narration columns in the PDF; both embedded layers preserved, obscured visual text cannot be certified from this rendering.'})
            for r in records:
                if r['printed_hadith_number']=='1247':r['quality_flags'].append('source_page22_footnote9_overlays_narration')
        if duplicates:exceptions.append({'type':'duplicate_printed_numbers','numbers':duplicates})
        pp={'source_id':sid,'source_sha256':sha,'source_filename':fp.name,'source_archive_member':'vietnamese/Sunan Abu Dawud/'+fp.name,
            'pdf_pages':len(doc),'record_count':len(records),'first_printed_number':str(min(nums)) if nums else None,'last_printed_number':str(max(nums)) if nums else None,
            'chapter_count':len(chapters),'footnote_count':len(footnotes),'translator_credits':credits,
            'publisher_imprint_as_printed':'Chanlyislam','source_url':None,'edition':None,'publication_date':None,
            'translation_language':'vi','ai_translation':False,
            'extraction_method':'PyMuPDF embedded text, spatial Vietnamese/Arabic column separation, left-margin narration markers',
            'extraction_date':'2026-11-11','all_pages_text_extracted':True,'independent_fidelity_review_complete':False,
            'printed_number_gaps':gaps,'duplicate_numbers':duplicates,'numeric_glyph_repairs':len(numeric_repairs),
            'metadata_notes':['Translator spelling variants are kept exactly as printed.','Source numbers retained without asserting an external canonical numbering system.','Arabic source text is present in PDFs, but defective embedded font mapping prevents reliable Arabic transcription in this extraction.']}
        dump(sub/'records.json',records);dump(sub/'source.json',pp);dump(sub/'chapters.json',chapters)
        dump(sub/'footnotes.json',footnotes);dump(sub/'exceptions.json',exceptions)
        dump(sub/'numeric-glyph-repair-log.json',numeric_repairs)
        dump(sub/'font-diagnostics.json',decoder.font_diagnostics)
        dump(sub/'glyph-repair-page-diagnostics.json',decoder.page_diagnostics)
        dump(sub/'nonrecord-segments.json',[{'text':l['text'],'kind':l['region'],**ref(l)} for l in other])
        with (sub/'pages.jsonl').open('w',encoding='utf-8') as f:
            for p in pages:f.write(json.dumps(p,ensure_ascii=False)+'\n')
        summary.append({**pp,'output_directory':str(sub)})
        print(sid,'records',len(records),'range',pp['first_printed_number'],pp['last_printed_number'],'gaps',gaps,'duplicates',duplicates,flush=True)
    dump(OUT/'summary.json',{'sources':summary,'source_count':len(summary),'pdf_pages':sum(s['pdf_pages'] for s in summary),'record_count':sum(s['record_count'] for s in summary)})

if __name__=='__main__':main()
