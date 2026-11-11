#!/usr/bin/env python3
"""Evidence-preserving Vietnamese PDF intake; source text is never canonicalized."""
from pathlib import Path
import json, re, hashlib, sys, unicodedata, collections, os
import fitz

BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'root-extraction'/'extracted'
INV=json.loads((BASE/'source-inventory.json').read_text())
sys.path.insert(0,str(BASE/'agent-schema'))
try:
    from glyph_cmap_repair import GlyphMapDecoder
except ImportError:
    GlyphMapDecoder=None
if os.environ.get('VI_DISABLE_GLYPH_REPAIR')=='1':GlyphMapDecoder=None
_PAGE_CACHE={}

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def latin(s):
    return any('LATIN' in unicodedata.name(c,'') for c in s)

def arabic(s):
    return any('\u0600'<=c<='\u06ff' or '\ufb50'<=c<='\ufdff' or '\ufe70'<=c<='\ufeff' for c in s if c!='ﷺ')

def page_lines(doc,idx,decoder):
    page=doc[idx]
    cached=_PAGE_CACHE.get(str(doc.name),{}).get(idx+1)
    if cached is not None:
        bands=[dr['rect'] for dr in page.get_drawings() if dr.get('fill') is not None and dr['rect'].width>page.rect.width*.5 and 22<dr['rect'].height<65]
        for r in cached['lines']:
            cy=(r['bbox'][1]+r['bbox'][3])/2
            r['inside_heading_band']=any(a.y0<=cy<=a.y1 and a.x0-2<=r['bbox'][0] and r['bbox'][2]<=a.x1+4 for a in bands)
        return cached['lines'],cached
    raw=page.get_text('dict')
    if decoder:
        fixed,changes=decoder.repair_page(page)
        if not hasattr(decoder,'changes'):decoder.changes=[]
        decoder.changes.extend(changes)
    else:fixed=raw
    if 'dict' in fixed: fixed=fixed['dict']
    rows=[]
    heading_bands=[]
    for draw in page.get_drawings():
        rect=draw['rect']
        if draw.get('fill') is not None and rect.width>page.rect.width*.5 and 22<rect.height<65:
            heading_bands.append(list(rect))
    for bi,b in enumerate(fixed['blocks']):
        for li,l in enumerate(b.get('lines',[])):
            spans=l['spans']; t=''.join(s['text'] for s in spans)
            raw_spans=raw['blocks'][bi]['lines'][li]['spans']
            rt=''.join(s['text'] for s in raw_spans)
            if not t.strip(): continue
            cy=(l['bbox'][1]+l['bbox'][3])/2
            rows.append({'id':f'p{idx+1:04d}-b{bi:04d}-l{li:03d}','pdf_page':idx+1,'bbox':[round(v,4) for v in l['bbox']],
                'inside_heading_band':any(a[1]<=cy<=a[3] and a[0]-2<=l['bbox'][0] and l['bbox'][2]<=a[2]+4 for a in heading_bands),
                'text':t,'raw_text':rt,'fonts':sorted(set(s['font'] for s in spans)),
                'sizes':sorted(set(round(s['size'],3) for s in spans)),
                'colors':sorted(set(s['color'] for s in spans)),
                'spans':[{'text':s['text'],'raw_text':rs['text'],'font':s['font'],'size':s['size'],'color':s['color'],'bbox':list(s['bbox'])} for s,rs in zip(spans,raw_spans)]})
    rows.sort(key=lambda r:(r['bbox'][1],r['bbox'][0]))
    printed=[]
    for r in rows:
        t=r['text'].strip()
        if r['bbox'][1]>page.rect.height*.9 and re.fullmatch(r'\d+',t): printed.append(t)
    return rows, {'pdf_page':idx+1,'printed_page_labels':printed,'width':page.rect.width,'height':page.rect.height,
        'raw_text':page.get_text(),'lines':rows,'image_review':False}

def classify_bukhari(r,w,h):
    t=r['text'].strip();x,y,x1,y1=r['bbox'];fonts=r['fonts']
    if t=='Chanlyislam' or (y>h*.9 and re.fullmatch(r'\d+',t) and max(r['sizes'])<12): return 'running_footer'
    if re.match(r'^(?:Đón xem|ĐÓN XEM|HẾT CHƯƠNG|HẾT PHẦN|AL-HAJJ PHẦN 3|PHẦN 28 / 2)',t): return 'colophon'
    if re.fullmatch(r'\d+\s*[-–.]',t) and x<w*.15 and max(r['sizes'])>=12:return 'translation_start'
    if not latin(t):
        if arabic(t): return 'arabic_raw'
        if re.fullmatch(r'\d+\s*[-–.]?',t): return 'number_fragment'
        return 'ornament_or_nonlatin'
    if re.search(r'(?:USMAN|Usman|ABU ZAYTUNE|CHUY[ỂỄ]N NGỮ|Chuy[ểễ]n ngữ)',t) and (len(t)<110): return 'translator_credit'
    if re.match(r'^\d+\s*[-–.]\s*',t): return 'translation_start'
    if max(r['sizes'])<=11.5: return 'small_text_footnote_candidate'
    calibri=all('Calibri' in s['font'] for s in r['spans'] if latin(s['text']))
    centered=abs((x+x1)/2-w/2)<w*.06
    inset=x>w*.12 and x1<w*.9
    if calibri and ('Calibri,Bold' in fonts) and any(c in (8288,16777215) for c in r['colors']) and (r['inside_heading_band'] or 16777215 in r['colors'] or (centered and inset)) and not re.search(r'[{}\uf07b\uf07d]',t):
        return 'heading'
    return 'vietnamese_body'

def group_runs(rows,kind):
    out=[];cur=[]
    for r in rows:
        if r.get('kind')==kind:
            if cur and (r['pdf_page']!=cur[-1]['pdf_page'] or r['bbox'][1]-cur[-1]['bbox'][3]>35):
                out.append(cur);cur=[]
            cur.append(r)
        elif cur:
            out.append(cur);cur=[]
    if cur:out.append(cur)
    return out

def spans(rows):
    return [{'line_id':r['id'],'pdf_page':r['pdf_page'],'bbox':r['bbox'],'text':r['text'],'raw_text':r['raw_text']} for r in rows]

def narrator_prefix(t):
    s=re.sub(r'^\s*\d+\s*[-–.]\s*','',t).strip()
    m=re.match(r'^((?:Ông|Bà|Ibnu|Ibn|Abu)\b.{0,240}?)(?=\s+(?:thuật l[ạa]i|nói|rằng|kể|cho biết|đã thuật))',s,re.S)
    return m.group(1) if m else None

def process_bukhari(src):
    doc=fitz.open(src['local_path']); decoder=GlyphMapDecoder(doc) if GlyphMapDecoder else None
    rows=[];pages=[]
    for pi in range(len(doc)):
        lr,pr=page_lines(doc,pi,decoder)
        for r in lr:r['kind']=classify_bukhari(r,pr['width'],pr['height'])
        blocks=collections.defaultdict(list)
        for r in lr:blocks[r['id'].rsplit('-l',1)[0]].append(r)
        for block in blocks.values():
            anchors=[r for r in block if re.match(r'^\s*\([0-9]+\)',r['text']) and max(r['sizes'])<=12.5 and r['bbox'][1]>pr['height']*.65]
            if anchors and all(max(r['sizes'])<=12.5 for r in block):
                for r in block:r['kind']='small_text_footnote_candidate'
            stars=[r for r in block if re.match(r'^\s*\*',r['text']) and latin(r['text'])]
            if stars:
                first_y=min(r['bbox'][1] for r in stars)
                for r in block:
                    if r['bbox'][1]>=first_y and r['kind']=='vietnamese_body':r['kind']='source_commentary'
        # The bare-number start of2062#18 splits its honorific into a separate
        # line. Keep same-block inline symbols with the Vietnamese text.
        for r in lr:
            if r['kind']=='ornament_or_nonlatin' and any('AGA Arabesque' in f for f in r['fonts']) and '\uf048' not in r['text']:
                siblings=[z for z in lr if z['id'].rsplit('-l',1)[0]==r['id'].rsplit('-l',1)[0] and z['kind'] in ('vietnamese_body','translation_start')]
                same=[z for z in siblings if abs(z['bbox'][1]-r['bbox'][1])<3]
                if same:
                    r['kind']='vietnamese_body';r['_sort_y']=same[0]['bbox'][1]
        lr.sort(key=lambda r:(r.get('_sort_y',r['bbox'][1])-(3 if r['kind']=='translation_start' and not latin(r['text']) else 0),r['bbox'][0]))
        rows.extend(lr);pages.append(pr)
    starts=[i for i,r in enumerate(rows) if r['kind']=='translation_start']
    records=[];headings=[];nonrecord=[];assigned=set()
    for n,start in enumerate(starts):
        end=starts[n+1] if n+1<len(starts) else len(rows)
        prev=starts[n-1] if n else 0
        prefix=rows[prev:start]
        recent_heading=[r for r in prefix if r['kind']=='heading']
        # Heading context carries forward; it is never silently appended to narration text.
        if recent_heading:
            last=recent_heading[-1]
            headrun=[]
            for r in reversed(recent_heading):
                if r['pdf_page']!=last['pdf_page'] or last['bbox'][1]-r['bbox'][3]>55: break
                headrun.insert(0,r);last=r
            headings.append({'id':f'chapter-{len(headings)+1:04d}','text':'\n'.join(r['text'] for r in headrun),'spans':spans(headrun)})
        chapter=headings[-1] if headings else None
        body=[];notes=[];comments=[];body_open=True
        for r in rows[start:end]:
            if r['kind'] in ('heading','colophon','translator_credit'):body_open=False
            if r['kind'] in ('translation_start','vietnamese_body') and body_open:
                body.append(r);assigned.add(r['id'])
            elif r['kind']=='small_text_footnote_candidate': notes.append(r)
            elif r['kind']=='source_commentary':comments.append(r)
        # Arabic block precedes its Vietnamese label. Preserve the raw layer, explicitly unapproved.
        anchor=prev
        for k in range(prev,start):
            if rows[k]['kind'] in ('vietnamese_body','translation_start','heading','translator_credit'): anchor=k+1
        ar=[r for r in rows[anchor:start] if r['kind'] in ('arabic_raw','number_fragment')]
        text='\n'.join(r['text'] for r in body)
        raw='\n'.join(r['raw_text'] for r in body)
        label=re.match(r'^\s*(\d+)\s*[-–.]',rows[start]['text']).group(1)
        rawlabel=re.match(r'^\s*(\d+)\s*[-–.]',rows[start]['raw_text'])
        rp=sorted(set(r['pdf_page'] for r in body+ar+notes))
        record={'id':f'vi:bukhari:pdf-{src["sha256"][:16]}:occ-{n+1:05d}', 'sequence':n+1,
            'printed_label':label,'printed_label_raw':rawlabel.group(1) if rawlabel else rows[start]['raw_text'].split()[0],
            'printed_label_status':'embedded_font_cmap_decoded_not_individually_image_checked' if decoder else 'embedded_text_unverified',
            'translation_raw':raw,'translation_text':text,'translation_search':' '.join(text.split()),
            'translation_spans':spans(body),'arabic_text':None,'arabic_raw':'\n'.join(r['raw_text'] for r in ar),
            'arabic_spans':spans(ar),'arabic_association_status':'preceding_arabic_block_candidate_unverified',
            'chapter':chapter,'narrator_prefix_raw':narrator_prefix(text),
            'footnotes':[],
            'references':[],'commentary':[{'text':'\n'.join(r['text'] for r in comments),'spans':spans(comments),'scope':'source_editorial_or_chapter_note_adjacent_to_occurrence_unverified'}] if comments else [],'pdf_pages':rp,'printed_pages':[v for p in rp for v in pages[p-1]['printed_page_labels']],
            'review_flags':['not_full_image_compared','arabic_text_layer_requires_reconstruction','narration_and_editorial_boundary_review_pending']}
        if any('\ue000'<=c<='\uf8ff' for c in text):record['review_flags'].append('font_specific_honorific_symbols_preserved_in_raw_unicode')
        if text!=raw:record['review_flags'].append('embedded_font_cmap_repairs_logged')
        records.append(record)
    for r in rows:
        if r['id'] not in assigned and r['kind'] not in ('running_footer','ornament_or_nonlatin','arabic_raw','number_fragment'):
            nonrecord.append(r)
    return write_source(src,doc,records,pages,headings,nonrecord,decoder,'bukhari')

def process_anthology(src):
    doc=fitz.open(src['local_path']);decoder=GlyphMapDecoder(doc) if GlyphMapDecoder else None
    rows=[];pages=[]
    for pi in range(len(doc)):
        lr,pr=page_lines(doc,pi,decoder)
        for r in lr:
            t=r['text'].strip();x,y,x1,y1=r['bbox'];w=pr['width'];h=pr['height']
            if t=='Chanlyislam' or (y>h*.9 and re.fullmatch(r'\d+',t)): k='running_footer'
            elif pi<2:k='front_matter'
            elif re.fullmatch(r'\d+\s*-',t) and x<w*.11:k='translation_start'
            elif latin(t) and x<w*.51:
                if max(r['sizes'])<12:k='small_text_footnote_candidate'
                else:k='vietnamese_body'
            elif x>w*.11 and x<w*.51 and re.fullmatch(r'[0-9 .()\[\],:;-]+',t):k='vietnamese_body'
            elif arabic(t): k='arabic_raw'
            else:k='other'
            if pi==2 and y<200 and k not in ('running_footer','translation_start'): k='epigraph_quran'
            if pi==len(doc)-1 and y>450 and latin(t) and k!='running_footer':k='translator_credit'
            r['kind']=k
        # Leading number cells have slightly different font ascenders from the
        # same row's first body line; move the marker before that line by a
        # small geometry tolerance, never by inferred sequence numbers.
        lr.sort(key=lambda r:(r['bbox'][1]-(8 if r['kind']=='translation_start' else 0),r['bbox'][0]))
        rows.extend(lr);pages.append(pr)
    starts=[i for i,r in enumerate(rows) if r['kind']=='translation_start']
    recs=[];assigned=set()
    for n,start in enumerate(starts):
        end=starts[n+1] if n+1<len(starts) else len(rows)
        region=rows[start:end];body=[r for r in region if r['kind']=='vietnamese_body'];refs=[];textlines=[];inref=False
        for r in body:
            t=r['text'].strip()
            if re.match(r'^(?:-\s*)?(?:Sahih|Sunan|Jami|Musnad|Al-Adab|Al-Mu.?jam|Al-Mujam|Silsilatul|Riyad|Hadith)',t):inref=True
            if inref or r['kind']=='source_reference':refs.append(r)
            else:textlines.append(r)
        refs.extend(r for r in region if r['kind']=='source_reference')
        ar=[r for r in region if r['kind']=='arabic_raw']
        foot=[r for r in region if r['kind']=='small_text_footnote_candidate']
        text='\n'.join(r['text'] for r in textlines);raw='\n'.join(r['raw_text'] for r in textlines)
        label=re.match(r'\s*(\d+)',rows[start]['text']).group(1)
        pageset=sorted(set(r['pdf_page'] for r in [rows[start]]+textlines+refs+ar))
        recs.append({'id':f'vi:200-golden-hadith:pdf-{src["sha256"][:16]}:occ-{n+1:05d}','sequence':n+1,
            'printed_label':label,'printed_label_raw':rows[start]['raw_text'].strip(),'printed_label_status':'embedded_font_cmap_decoded_not_individually_image_checked' if decoder else 'embedded_text_unverified',
            'translation_text':text,'translation_raw':raw,'translation_search':' '.join(text.split()),'translation_spans':spans(textlines),
            'arabic_text':None,'arabic_raw':'\n'.join(r['raw_text'] for r in ar),'arabic_spans':spans(ar),'arabic_association_status':'aligned_column_interval_candidate_unverified',
            'chapter':None,'narrator_prefix_raw':None,'references':[{'verbatim':'\n'.join(r['text'] for r in refs),'spans':spans(refs),'status':'source_printed_not_independently_verified'}] if refs else [],
            'footnotes':[],'commentary':[],'pdf_pages':pageset,'printed_pages':[v for p in pageset for v in pages[p-1]['printed_page_labels']],
            'review_flags':['not_full_image_compared','arabic_text_layer_requires_reconstruction','source_reference_authentication_pending']})
        if label=='188':
            recs[-1]['review_flags'].append('source_translation_body_omitted_image_confirmed_pdf35')
            recs[-1]['translation_completeness']='introductory_formula_only_no_translated_hadith_body_in_source'
        assigned.update(r['id'] for r in [rows[start]]+textlines+refs+ar)
    nonrecord=[r for r in rows if r['id'] not in assigned and r['kind'] not in ('running_footer','other')]
    return write_source(src,doc,recs,pages,[],nonrecord,decoder,'200-golden-hadith')

def write_source(src,doc,recs,pages,heads,nonrecord,decoder,book):
    key=src['archive_member'].split('/')[-1].split('_')[0]
    if len(key)>20:key='200-golden-hadith'
    dst=OUT/f'{key}-{src["sha256"][:12]}'
    dst.mkdir(parents=True,exist_ok=True)
    source={**src,'book_slug':book,'source_id':f'chanlyislam:vi:{book}:pdf-{src["sha256"][:16]}','record_count':len(recs),
        'credit_evidence':[{'text':r['text'],'pdf_page':r['pdf_page'],'line_id':r['id']} for p in pages for r in p['lines'] if r.get('kind')=='translator_credit'],
        'extraction_method':'embedded_text_with_unambiguous_embedded_font_cmap_repair' if decoder else 'embedded_text',
        'source_claims_preserved':True}
    allnotes=[]
    for page in pages:
        notes=[r for r in page['lines'] if r.get('kind')=='small_text_footnote_candidate']
        groups=[]
        for row in notes:
            if not groups or re.match(r'^\s*(?:\(\d+\)|\d+[.)])\s*',row['text']):groups.append([])
            groups[-1].append(row)
        for group in groups:
            t='\n'.join(r['text'] for r in group);match=re.match(r'^\s*\(?([0-9]+)[).]',t)
            label=match.group(1) if match else None
            candidates=[]
            if label:
                byid={r['id']:r for r in page['lines']}
                for rec in recs:
                    for sp in rec['translation_spans']:
                        if sp['pdf_page']!=page['pdf_page']:continue
                        row=byid[sp['line_id']]
                        if any(label==re.sub(r'[^0-9]','',s['text']) and s['size']<=10 for s in row['spans']):
                            candidates.append(rec['id']);break
            note={'id':f'footnote-{len(allnotes)+1:04d}','text':t,'label':label,'spans':spans(group),
                'pdf_page':page['pdf_page'],'related_occurrence_ids':candidates,
                'assignment_status':'same_page_superscript_anchor' if candidates else 'unassigned_source_page_footnote'}
            allnotes.append(note)
            for rec in recs:
                if rec['id'] in candidates:rec['footnotes'].append(note)
    dump(dst/'records.json',recs);dump(dst/'source.json',source);dump(dst/'chapters.json',heads);dump(dst/'nonrecord-material.json',nonrecord);dump(dst/'footnotes.json',allnotes)
    with (dst/'pages.jsonl').open('w',encoding='utf-8') as f:
        for p in pages:f.write(json.dumps(p,ensure_ascii=False)+'\n')
    if decoder and hasattr(decoder,'changes'):
        changes=getattr(decoder,'changes',getattr(decoder,'change_log',[]))
        dump(dst/'font-repair-log.json',changes)
    summary={'directory':str(dst),'source_id':source['source_id'],'file':src['archive_member'],'sha256':src['sha256'],'book':book,
        'pdf_pages':len(doc),'records':len(recs),'nonrecord_lines':len(nonrecord),'records_without_translation':sum(not r['translation_text'].strip() for r in recs),
        'first_labels':[r['printed_label'] for r in recs[:4]],'last_labels':[r['printed_label'] for r in recs[-4:]],
        'font_repairs_enabled':bool(decoder)}
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summary

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summary=[]
    for src in INV['files']:
        if os.environ.get('VI_USE_CACHED_PAGES')=='1':
            prior=list(OUT.glob('*-'+src['sha256'][:12]+'/pages.jsonl'))
            if prior:
                cached=[json.loads(s) for s in prior[0].read_text().splitlines()]
                _PAGE_CACHE[src['local_path']]={r['pdf_page']:r for r in cached}
        if '/Sahih Al-Bukhari/' in src['archive_member']:summary.append(process_bukhari(src))
        elif len(Path(src['archive_member']).parts)==2:summary.append(process_anthology(src))
    dump(OUT/'summary.json',summary)

if __name__=='__main__':main()
