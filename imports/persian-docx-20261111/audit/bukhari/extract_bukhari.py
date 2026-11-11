#!/usr/bin/env python3
"""Deterministic, source-preserving Faiz al-Bari DOCX extraction.

No canonical-number repair, editorial reconstruction, or OCR is performed.
Source text and font-encoded honorific metadata are retained separately from
optional display normalizations. Paragraph indexes are zero based.
"""
from pathlib import Path
from lxml import etree as ET
import collections, hashlib, json, re, zipfile

BASE = Path(__file__).resolve().parent
INPUT = BASE.parents[1] / 'upload'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
NUMBER = re.compile(r'^\s*([0-9۰-۹٠-٩]+)\s*[-–ـ.\):]?\s*')
DIACRITICS = re.compile('[\u064b-\u065f\u0670]')
MAIN_RANGES = {1: (705, 2548), 2: (375, 2448), 3: (439, 2891),
               4: (298, 2450), 5: (312, 2205), 6: (427, 2390)}
OFFSET = {1: 0, 2: 324, 3: 701, 4: 1130, 5: 1519, 6: 1827}
EXPECTED_COUNTS = {1: 324, 2: 377, 3: 429, 4: 389, 5: 308, 6: 403}
VARIANT_SPLITS = {(2,1553): [1560], (3,1373): [1374,1375]}
PURE_REFERENCE_PARAGRAPHS = {(1,2054),(2,928),(3,1378),(3,1862),(5,1905)}
HONORIFIC = {'ج': 'صلى الله عليه وسلم', 'س': 'رضي الله عنه', 'ب':'رضي الله عنهما',
             'ل':'رضي الله عنها','/':'رحمه الله','÷':'عليه السلام','ش':'رضي الله عنهم',
             '†':'عليهم السلام','أ':'جل جلاله'}
FONT_EVIDENCE = 'font-decoding-evidence.json; CTraditional font SHA256 d6cd8b2dca3ce04b155e4c4ffb6af5c1d7ce1738520678ca102ad5bcdc24c52e; rendered glyph chart visually verified'
ARABIC_QUOTE_OVERRIDES = {
    'fa-faiz-al-bari-v2-fn9-p1-q001','fa-faiz-al-bari-v2-fn222-p5-q001',
    'fa-faiz-al-bari-v3-fn131-p17-q001','fa-faiz-al-bari-v3-fn504-p2-q001',
    'fa-faiz-al-bari-v4-fn21-p1-q001','fa-faiz-al-bari-v4-fn188-p2-q001',
    'fa-faiz-al-bari-v4-fn320-p1-q001','fa-faiz-al-bari-v4-fn340-p0-q001',
    'fa-faiz-al-bari-v4-fn362-p5-q001','fa-faiz-al-bari-v5-fn22-p2-q001',
    'fa-faiz-al-bari-v5-fn37-p2-q001','fa-faiz-al-bari-v5-fn141-p1-q001',
    'fa-faiz-al-bari-v5-fn141-p2-q001','fa-faiz-al-bari-v5-fn141-p2-q002',
    'fa-faiz-al-bari-v5-fn190-p3-q001','fa-faiz-al-bari-v5-fn190-p3-q002',
    'fa-faiz-al-bari-v5-fn253-p0-q001','fa-faiz-al-bari-v5-fn322-p0-q003',
    'fa-faiz-al-bari-v6-fn174-p1-q001','fa-faiz-al-bari-v6-fn193-p1-q001',
    'fa-faiz-al-bari-v3-fn242-p3-q001','fa-faiz-al-bari-v4-fn242-p9-q001',
}
PERSIAN_QUOTE_OVERRIDES = {
    'fa-faiz-al-bari-v1-fn288-p1-q001','fa-faiz-al-bari-v2-fn274-p2-q001',
    'fa-faiz-al-bari-v2-fn439-p1-q001','fa-faiz-al-bari-v2-fn440-p2-q001',
    'fa-faiz-al-bari-v4-fn16-p2-q001','fa-faiz-al-bari-v4-fn388-p1-q001',
}
HEADING_STYLES = {'1-', '2-', '2-0', '4-', '4-0'}

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def jsonl(path, rows):
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')

def paragraph(node, index, part, footnote_id=None):
    """Preserve source characters, line/tab markers, glyph runs and note anchors."""
    text, tokens, glyphs, notes = '', [], [], []
    # w:t exact characters are also retained independently of layout tokens.
    raw_w_t = ''.join(node.xpath('.//w:t/text()', namespaces=NS))
    for e in node.iter():
        if e.tag not in {W+'t', W+'tab', W+'br', W+'cr', W+'sym', W+'footnoteReference', W+'endnoteReference'}:
            continue
        run = e.getparent()
        while run is not None and run.tag != W+'r':
            run = run.getparent()
        fonts = run.xpath('./w:rPr/w:rFonts/@*', namespaces=NS) if run is not None else []
        if e.tag == W+'t':
            s = e.text or ''
            if any('CTraditional Arabic' in f for f in fonts):
                glyphs.append({'offset': len(text), 'text': s, 'font': 'CTraditional Arabic'})
            tokens.append({'kind': 'text', 'offset': len(text), 'text': s})
            text += s
        elif e.tag == W+'tab':
            tokens.append({'kind':'tab', 'offset':len(text)}); text += '\t'
        elif e.tag in {W+'br', W+'cr'}:
            kind = e.get(W+'type') or 'line'
            tokens.append({'kind':'break', 'type':kind, 'offset':len(text)})
            text += '\n' if kind != 'page' else '\f'
        elif e.tag == W+'sym':
            val = {'offset':len(text),'font':e.get(W+'font'),'hex':e.get(W+'char')}
            tokens.append({'kind':'symbol', **val}); glyphs.append(val)
        else:
            notes.append({'kind':'footnote' if e.tag == W+'footnoteReference' else 'endnote',
                          'id': e.get(W+'id'), 'offset':len(text)})
    display = text
    transforms = []
    for g in glyphs:
        if g.get('font') == 'CTraditional Arabic':
            for i,c in enumerate(g.get('text','')):
                if c in HONORIFIC:
                    transforms.append({'offset':g['offset']+i,'raw':c,'display':' '+HONORIFIC[c]+' ',
                        'kind':'font_glyph_to_unicode','basis':FONT_EVIDENCE})
    for n in notes:
        k=n['offset']
        if k>0 and text[k-1:k+1]=='()':
            transforms.append({'offset':k-1,'raw':'()','display':'','kind':'footnote_marker_removed',
                               'basis':'User requested hadith text without side comments; note reference retained in source locator archive.','footnote_id':n['id']})
    transforms.sort(key=lambda x:x['offset'])
    for t in reversed(transforms):
        display=display[:t['offset']]+t['display']+display[t['offset']+len(t['raw']):]
    style = node.xpath('./w:pPr/w:pStyle/@w:val', namespaces=NS)
    return {'index': index, 'part':part, 'footnote_id':footnote_id,
            'style':style[0] if style else None, 'text':text, 'raw_w_t':raw_w_t,
            'text_sha256':sha(text), 'display_text':display,
            'display_normalization':transforms,
            'font_encoded_glyphs':glyphs, 'note_references':notes,
            'control_tokens':[t for t in tokens if t['kind']!='text'],
            'last_rendered_page_breaks':len(node.xpath('.//w:lastRenderedPageBreak',namespaces=NS))}

def clean_number(text):
    return NUMBER.sub('', text, count=1)

def raw_number(text):
    m = NUMBER.match(text)
    return m.group(1) if m else None

def explicit_refs(text):
    out = []
    # Printed spelling variants are retained verbatim; normalized collection
    # comes from this identified Bukhari edition, never from a numeric lookup.
    for m in re.finditer(r'((?:رواهل|[خب]?رواه|وراه|راه|روه|روا|راوه|ر واه)\s*([^:0-9۰-۹٠-٩\]\)\n]{1,18})[: \u200c\u200d\[]*\s*([0-9۰-۹٠-٩][^\]\n]*|))[\]\)]',text):
        citation=m.group(1)
        before_cross=re.split(r'و?\s*انظر',citation,maxsplit=1)
        nums = re.findall('[0-9۰-۹٠-٩]+', before_cross[0])
        cross=re.findall('[0-9۰-۹٠-٩]+',before_cross[1]) if len(before_cross)>1 else []
        label=m.group(2).strip()
        booklabel=label.replace(' ','').replace('ی','ي')
        if booklabel not in {'البخاري','الخباري','الخاري','البخاي','لبخاري','البخازي','الخايري','الببخاري','بخاري','البخار','البخراي','البخري','البخاريک'}:
            continue
        out.append({'collection':'Sahih al-Bukhari','collection_id':'sahih-al-bukhari',
                    'number_raw':nums,'numbers':[str(int(x)) for x in nums],
                    'cross_reference_number_raw':cross,'cross_reference_numbers':[str(int(x)) for x in cross],
                    'citation_label_raw':label,'citation_raw':m.group(0),'status':'as_cited_in_uploaded_source',
                    'collection_basis':'Identified source edition and printed Bukhari citation label; label typos are preserved.',
                    'externally_verified':False})
    if not out:
        for m in re.finditer(r'\[(?:حديث رقم:\s*)?([0-9۰-۹٠-٩]+)\]',text):
            out.append({'collection':None,'collection_id':None,'number_raw':[m[1]],'numbers':[str(int(m[1]))],
                        'citation_raw':m[0],'status':'unscoped_number_in_source','externally_verified':False,
                        'collection_basis':'No explicit collection label survives in this citation. Source edition is Bukhari, but this field is not silently promoted.'})
    return out

def is_primary(p):
    if not NUMBER.match(p['text']):
        return False
    return p['style'] in {'5-', '6-'} or ('رواه البخ' in p['text'] and p['style'] not in HEADING_STYLES)

def narrator(ar, fa):
    ar_clean = DIACRITICS.sub('', clean_number(ar))
    m = re.match(r'[«\s]*و?عن\s+(.{1,150}?)(?=\s+(?:رضي|رضى|قال|أن|انه|إنه)|[,،:])',ar_clean)
    fa_match = re.match(r'\s*و?\s*از\s+(.{1,150}?)(?=\s+(?:روایت|از پیامبر|نیز)|[,،:])',clean_number(fa))
    return {'arabic_as_written_without_diacritics':m.group(1) if m else None,
            'persian_as_written':fa_match.group(1) if fa_match else None,
            'full_isnad':None,'basis':'source attribution prefix only; no reconstructed chain'}

def strip_terminal_citation(text, references):
    """Remove only a parsed final citation, preserving its exact printed span."""
    if not text:return text,[]
    removed=[]
    for ref in reversed(references):
        token=ref.get('citation_raw')
        if not token:continue
        start=text.rfind(token)
        if start<0:continue
        end=start+len(token)
        suffix=text[end:]
        if re.search(r'[^\s.،؛:!؟?\]\)]',suffix):continue
        a=start
        while a>0 and text[a-1].isspace():a-=1
        if a>0 and text[a-1] in '[(':a-=1
        span=text[a:]
        ref['citation_token_raw']=ref.get('citation_token_raw',token)
        ref['citation_raw']=span
        ref['citation_scope']='Exact terminal citation for this source narration; moved from reader text to metadata.'
        removed.append({'kind':'terminal_source_citation_to_metadata','stage':'after font decoding and source-number removal','start':a,'end':len(text),'raw':span})
        text=text[:a].rstrip()
    return text,removed

def source_record_id(v, p):
    return f'fa-faiz-al-bari-v{v}-p{p:05d}'

def quote_spans(text):
    stack = []
    for i,c in enumerate(text):
        if c == '«': stack.append(i)
        elif c == '»' and stack:
            start = stack.pop()
            if not stack: yield start, i+1

def guess_quote_lang(text):
    if re.search(r'(?:^|[\s،«])(?:که|از|را|این|آن|برای|است|نیست|خدا|پیامبر|خداوند|شما|آنها|کسی|گفت|گفتند|فرمود|فرمودند|در|ولی|من|بلی|نه|مگر|پدر|آدم|مؤمن|چه|بکن|برود|قبر|هنگام|آیا|فاطمه|غضب|چنین|قیامت|آب|باکی|می\u200c\w+|نمی\u200c\w+)(?:[\s،»]|$)', text):
        return 'fa'
    if len(DIACRITICS.findall(text)) >= 3:
        return 'ar'
    return 'und'

def source_quote_kind(context):
    # This only promotes explicitly attributed quotations, not quotations by scholars.
    context=DIACRITICS.sub('',context).rsplit('»',1)[-1]
    if re.search(r'(?:پیامبر|رسول|نبی|نبي|پيامبر).{0,140}(?:فرمود|گفت|می\u200cگوی|مي\u200cگوی|قال|يقول|یقول)',context):
        return 'quoted_hadith'
    if re.search(r'(?:قال|يقول|یقول|سمعت).{0,70}(?:رسول|نبي|النبي|نبی)',context):
        return 'quoted_hadith'
    if re.search(r'(?:قول|فرموده|فرمودۀ|فرمایش|سخن).{0,45}(?:پیامبر|رسول|نبی)',context):
        return 'quoted_hadith'
    return 'supporting_quote'

def build():
    primary, variants, supporting, archives, ledgers, anomalies, doctrine = [], [], [], [], [], [], []
    for path in sorted(INPUT.glob('faiz*.docx')):
        v = int(path.name.split('bokhari-')[1][0])
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read('word/document.xml'))
            ps = [paragraph(n, i, 'word/document.xml') for i,n in enumerate(root.xpath('//w:body//w:p',namespaces=NS))]
            froot = ET.fromstring(z.read('word/footnotes.xml'))
            footnotes = []
            for fn in froot.xpath('./w:footnote',namespaces=NS):
                fid=fn.get(W+'id')
                if int(fid)<1: continue
                fps=[paragraph(n,i,'word/footnotes.xml',fid) for i,n in enumerate(fn.xpath('.//w:p',namespaces=NS))]
                footnotes.append({'id':fid,'paragraphs':fps,'text':'\n'.join(p['text'] for p in fps),
                                  'display_text':'\n'.join(p['display_text'] for p in fps)})
            fnmap={f['id']:f for f in footnotes}
            all_xml=[]
            for name in z.namelist():
                if name.startswith('word/') and name.endswith('.xml') and name not in {'word/document.xml','word/footnotes.xml'}:
                    other=ET.fromstring(z.read(name))
                    texts=other.xpath('//w:t/text()',namespaces=NS)
                    if texts: all_xml.append({'part':name,'text_nodes':texts})
            archive={'volume':v,'source_filename':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'body':ps,'footnotes':footnotes,'other_part_text':all_xml,
                     'original_document_retained':True,
                     'page_locator_note':'DOCX does not encode reliable printed page numbers for each paragraph. Cached page breaks are not treated as exact source pagination.'}
            archives.append(archive)
            first,last=MAIN_RANGES[v]
            boundaries=[p['index'] for p in ps[first:last] if is_primary(p)]
            if v==5:
                boundaries += [697,1882] # source Persian-only #1590 and surviving #1771 fragment
            boundaries.sort()
            assert len(boundaries)==EXPECTED_COUNTS[v], (v,len(boundaries))
            assigned={}
            current_headings=[]
            hcontexts={}
            current_book=[]; current_chapter=[]
            for p in ps:
                if p['style'] in {'1-','2-'} and p['index']>=first-3:
                    if p['style']=='1-': current_book=[p]; current_chapter=[]
                    else: current_book=[x for x in current_book if x['style']!='2-']+[p]
                elif p['style'] in {'2-0','4-','4-0'} and p['index']>=first-3:
                    if p['style']=='2-0': current_chapter=[p]
                    else: current_chapter=[x for x in current_chapter if x['style'] not in {'4-','4-0'}]+[p]
                hcontexts[p['index']]=[{'index':h['index'],'style':h['style'],'text':h['display_text'],'raw_text':h['text']} for h in current_book+current_chapter]
            volume_records=[]
            for seq,start in enumerate(boundaries):
                stop=boundaries[seq+1] if seq+1<len(boundaries) else last
                # Headings introduce later material and never become a preceding translation.
                end=next((i for i in range(start+1,stop) if ps[i]['style'] in HEADING_STYLES),stop)
                arps=[]; faps=[]; extra=[]; translation_started=False
                for p in ps[start:end]:
                    if v==5 and start==1882:
                        faps.append(p);continue
                    if v==5 and start==697:
                        faps.append(p);translation_started=True;continue
                    if not translation_started and (p['style'] in {'5-','6-'} or p['index']==start):
                        arps.append(p)
                    elif p['style'] in {'5-','6-'} and ('رواه البخ' in p['text'] or p['index']==1373 and v==3):
                        extra.append(p)
                    else:
                        faps.append(p); translation_started=True
                # Source defect notice is editorial source annotation, not prior hadith text.
                if v==5 and start==1878:
                    faps=[p for p in faps if p['index']!=1881]
                if v==5 and start==622:
                    # Detached cross-reference comparison after the completed
                    # Mi'raj narration; this is editor prose, not hadith text.
                    faps=[p for p in faps if p['index']!=696]
                source_variant_ps=[p for p in arps+extra if (v,p['index']) in VARIANT_SPLITS]
                variant_translation_indexes={i for p in source_variant_ps for i in VARIANT_SPLITS[(v,p['index'])]}
                arps=[p for p in arps if (v,p['index']) not in VARIANT_SPLITS]
                faps=[p for p in faps if p['index'] not in variant_translation_indexes]
                extra=[p for p in extra if (v,p['index']) not in VARIANT_SPLITS]
                aid=source_record_id(v,start)
                ar='\n'.join(p['text'] for p in arps)
                fa='\n'.join(p['text'] for p in faps)
                expected=OFFSET[v]+seq+1
                number=raw_number(ar or fa)
                fa_number=raw_number(fa)
                notes=[]
                if number is not None and int(number)!=expected:
                    notes.append({'code':'printed_local_number_differs_from_sequence','printed':number,'sequence_position':expected})
                if number and fa_number and int(number)!=int(fa_number):
                    notes.append({'code':'arabic_persian_local_number_disagree','arabic':number,'persian':fa_number})
                if v==5 and start==697:
                    notes.append({'code':'arabic_absent_in_source','detail':'Persian source-local 1590 exists; no corresponding Arabic paragraph in supplied DOCX.'})
                if v==5 and start==1882:
                    number=None;fa_number=None
                    notes.append({'code':'incomplete_uploaded_source','detail':'Only final Persian fragment survives between 1770 and 1772; source explicitly warns printed page 391 / Word page 270 incomplete. 1771 is the inferred sequence position, not a printed surviving label.','source_notice_paragraphs':[1,1881]})
                note_ids=list(dict.fromkeys(n['id'] for p in arps+faps+extra for n in p['note_references'] if n['kind']=='footnote'))
                record={'id':aid,'language':'fa','source_id':f'fa-faiz-al-bari-v{v}','source_volume':v,
                        'source_filename':path.name,'record_type':'hadith_occurrence' if ar else 'translation_occurrence',
                        'content_kind':'source_fragment' if v==5 and start==1882 else 'numbered_source_narration',
                        'source_sequence_position':expected,'source_local_number':number,
                        'translation_local_number':fa_number,'numbering_system':'Faiz al-Bari abridgment local numbering',
                        'text':{'arabic':clean_number('\n'.join(p['display_text'] for p in arps)) if arps else None,
                                'translation':clean_number('\n'.join(p['display_text'] for p in faps)) if faps else None},
                        'raw_text':{'arabic':clean_number(ar) if ar else None,'translation':clean_number(fa) if fa else None},
                        'display_text':{'arabic':clean_number('\n'.join(p['display_text'] for p in arps)) if arps else None,
                                        'translation':clean_number('\n'.join(p['display_text'] for p in faps)) if faps else None},
                        'source_paragraphs':{'arabic':[p['index'] for p in arps],'translation':[p['index'] for p in faps],
                                             'additional_arabic':[p['index'] for p in extra]},
                        'source_headings':hcontexts[start], 'references':explicit_refs(ar),
                        'narrator':narrator(ar,fa),'full_isnad':None,
                        'grade':None,'grade_note':'No independent authenticity judgment or grade inferred from collection name.',
                        'page':None,'footnotes':[], 'commentary':None,'source_footnote_ids':note_ids,
                        'source_notes':notes,'translation_origin':'human','translator':'دکتر عبدالرحیم فیروز هروی',
                        'source_role':'Persian translation and commentary of an abridgment of Sahih al-Bukhari',
                        'source_xml_locator':f'word/document.xml paragraph[{start}] (zero based)',
                        'text_transformations':[{'paragraph':p['index'],**tr} for p in arps+faps for tr in p['display_normalization']],
                        'raw_paragraphs':[{'index':p['index'],'text':p['text'],'sha256':p['text_sha256']} for p in arps+faps+extra]}
                if (v,start) in PURE_REFERENCE_PARAGRAPHS:
                    record['record_type']='hadith_reference'
                    record['content_kind']='source_cross_reference_without_narration_text'
                    record['source_notes'].append({'code':'reference_only_source_position','detail':'Source only points to a previously mentioned narration; retained in audit/reference file and excluded from hadith-only integration.'})
                record['text']['arabic'],record['citation_text_transformations']=strip_terminal_citation(record['text']['arabic'],record['references'])
                record['display_text']['arabic']=record['text']['arabic']
                if not record['text']['translation']:
                    record['source_notes'].append({'code':'translation_missing_or_empty','detail':'No Persian translation paragraphs assigned by source boundaries.'})
                for p in arps+faps:
                    assigned[p['index']]={'role':'hadith_arabic' if p in arps else 'hadith_translation','record_id':aid}
                for n in notes: anomalies.append({'record_id':aid,'volume':v,'paragraph':start,**n})
                primary.append(record); volume_records.append(record)
                for xp in source_variant_ps:
                    vfaps=[ps[i] for i in VARIANT_SPLITS[(v,xp['index'])]]
                    vid=source_record_id(v,xp['index'])+'-variant'
                    var={'id':vid,'language':'fa','source_id':record['source_id'],'source_volume':v,
                         'source_filename':path.name,'record_type':'hadith_occurrence','content_kind':'unnumbered_source_variant',
                         'parent_id':aid,'source_local_number':None,'source_sequence_position':expected,
                         'text':{'arabic':xp['display_text'],'translation':'\n'.join(p['display_text'] for p in vfaps)},
                         'raw_text':{'arabic':xp['text'],'translation':'\n'.join(p['text'] for p in vfaps)},
                         'display_text':{'arabic':xp['display_text'],'translation':'\n'.join(p['display_text'] for p in vfaps)},
                         'references':explicit_refs(xp['text']),'source_headings':record['source_headings'],
                         'source_paragraphs':{'arabic':[xp['index']],'translation':[p['index'] for p in vfaps]},
                         'source_notes':[{'code':'separate_unnumbered_report','detail':'Arabic and Persian source paragraph alignment manually checked.'}],
                         'text_transformations':[{'paragraph':p['index'],**tr} for p in [xp]+vfaps for tr in p['display_normalization']],
                         'translation_origin':'human','translator':record['translator'],'page':None,'footnotes':[],
                         'commentary':None,'source_footnote_ids':list(dict.fromkeys(n['id'] for p in [xp]+vfaps for n in p['note_references']))}
                    variants.append(var)
                    var['text']['arabic'],var['citation_text_transformations']=strip_terminal_citation(var['text']['arabic'],var['references'])
                    var['display_text']['arabic']=var['text']['arabic']
                    assigned[xp['index']]={'role':'unnumbered_variant_arabic','record_id':vid}
                    for p in vfaps: assigned[p['index']]={'role':'unnumbered_variant_translation','record_id':vid}
                # A separately laid out additional Arabic report gets its own occurrence.
                for xp in extra:
                    vid=source_record_id(v,xp['index'])+'-variant'
                    var={'id':vid,'language':'fa','source_id':record['source_id'],'source_volume':v,
                         'source_filename':path.name,'record_type':'hadith_occurrence','content_kind':'unnumbered_source_variant',
                         'parent_id':aid,'source_local_number':None,'source_sequence_position':expected,
                         'text':{'arabic':xp['text'],'translation':None},'references':explicit_refs(xp['text']),
                         'source_headings':record['source_headings'],
                         'source_paragraphs':{'arabic':[xp['index']],'translation':[]},
                         'source_notes':[{'code':'translation_with_parent','detail':'Related Persian narrative remains with parent occurrence; exact variant translation not independently aligned.'}],
                         'translation_origin':'human','translator':record['translator'],'page':None,'footnotes':[]}
                    variants.append(var); assigned[xp['index']]={'role':'unnumbered_variant','record_id':vid}
                # Multiple consecutive Arabic paragraphs can be separately sourced variant.
                for xp in arps[1:]:
                    if re.match(r'\s*وَ?ف[يی]\s+رواية',xp['text']):
                        variants.append({'id':source_record_id(v,xp['index'])+'-variant','language':'fa',
                            'source_id':record['source_id'],'source_volume':v,'source_filename':path.name,
                            'record_type':'hadith_occurrence','content_kind':'unnumbered_source_variant',
                            'parent_id':aid,'source_local_number':None,'source_sequence_position':expected,
                            'text':{'arabic':xp['text'],'translation':None},'references':explicit_refs(xp['text']),
                            'source_paragraphs':{'arabic':[xp['index']],'translation':[]},'source_headings':record['source_headings'],
                            'source_notes':[{'code':'variant_also_retained_in_parent_source_text','detail':'Exact printed variant is separately indexed; full parent source text is retained.'}],
                            'translation_origin':'human','translator':record['translator'],'page':None,'footnotes':[]})
            owners=collections.defaultdict(list)
            for r in volume_records:
                for fid in r['source_footnote_ids']: owners[fid].append(r['id'])
            # Every footnote and every non-primary paragraph is retained and classified.
            for p in ps:
                assignment=assigned.get(p['index'])
                if not assignment:
                    role='empty' if not p['text'].strip() else ('table_of_contents' if (p['style'] or '').startswith('TOC') else 'heading' if p['style'] in HEADING_STYLES else 'supporting_source_text')
                    if v==5 and p['index'] in {696,1881}:role='detached_source_comment_excluded'
                    assignment={'role':role,'record_id':None}
                ledgers.append({'source_id':f'fa-faiz-al-bari-v{v}','part':'word/document.xml',
                                'paragraph_index':p['index'],'characters':len(p['text']),
                                'text_sha256':p['text_sha256'],**assignment})
            ancillary_paragraphs=[]
            for fn in footnotes:
                for p in fn['paragraphs']:
                    loc=f'fn{fn["id"]}-p{p["index"]}'
                    ledgers.append({'source_id':f'fa-faiz-al-bari-v{v}','part':'word/footnotes.xml',
                        'footnote_id':fn['id'],'paragraph_index':p['index'],'characters':len(p['text']),
                        'text_sha256':p['text_sha256'],'role':'source_commentary','record_ids':owners[fn['id']]})
                    ancillary_paragraphs.append((loc,p,owners[fn['id']]))
            for p in ps:
                if p['index'] not in assigned and p['text'].strip() and p['style'] not in HEADING_STYLES and not (p['style'] or '').startswith('TOC'):
                    ancillary_paragraphs.append((f'p{p["index"]}',p,[]))
            for loc,p,parents in ancillary_paragraphs:
                spans=list(quote_spans(p['text']))
                for qi,(a,b) in enumerate(spans):
                    qt=p['text'][a:b]
                    # Use full source paragraph and preceding exact context to make ambiguity inspectable.
                    before=p['text'][max(0,a-350):a]
                    kind=source_quote_kind(before)
                    lang=guess_quote_lang(qt)
                    qid=f'fa-faiz-al-bari-v{v}-{loc}-q{qi+1:03d}'
                    if qid=='fa-faiz-al-bari-v1-fn370-p2-q001':
                        kind='supporting_quote' # "otherwise he would have said" is counterfactual commentator prose.
                    if qid in ARABIC_QUOTE_OVERRIDES: lang='ar'
                    if qid in PERSIAN_QUOTE_OVERRIDES: lang='fa'
                    qtrans=[tr for tr in p['display_normalization'] if a<=tr['offset'] and tr['offset']+len(tr['raw'])<=b]
                    qdisplay=qt
                    for tr in reversed(qtrans):
                        k=tr['offset']-a
                        qdisplay=qdisplay[:k]+tr['display']+qdisplay[k+len(tr['raw']):]
                    supporting.append({'id':qid,
                        'language':'fa','source_id':f'fa-faiz-al-bari-v{v}','source_volume':v,
                        'source_filename':path.name,'record_type':kind,'content_kind':'source_commentary_quotation',
                        'parent_ids':parents,'source_locator':{'part':p['part'],'footnote_id':p['footnote_id'],'paragraph_index':p['index'],'start':a,'end':b},
                        'source_quote':qt,'quote_language':lang,'text':{'arabic':qdisplay if lang=='ar' else None,'translation':qdisplay if lang=='fa' else None},
                        'text_transformations':qtrans,
                        'context_before':before,'full_source_paragraph':p['text'],
                        'references':explicit_refs(p['text']),'narrator':None,'grade':None,'page':None,
                        'attribution_note':'Explicit attribution to Prophet in nearby preceding source text.' if kind=='quoted_hadith' else 'Quotation retained without asserting prophetic attribution.',
                        'translation_origin':'human','translator':'دکتر عبدالرحیم فیروز هروی'})
                # Catch attributed prose reports even if source omitted quote punctuation.
                if not spans and re.search(r'(?:پیامبر|رسول|نبی).{0,130}(?:فرمود|گفت|قال|قَال|يقول)',p['text']) and ('روایت' in p['text'] or 'عَنْ' in p['text']):
                    supporting.append({'id':f'fa-faiz-al-bari-v{v}-{loc}-report',
                        'language':'fa','source_id':f'fa-faiz-al-bari-v{v}','source_volume':v,
                        'source_filename':path.name,'record_type':'supporting_quote','content_kind':'unquoted_report_context',
                        'parent_ids':parents,'source_locator':{'part':p['part'],'footnote_id':p['footnote_id'],'paragraph_index':p['index']},
                        'source_quote':p['text'],'quote_language':'fa','text':{'arabic':None,'translation':p['text']},
                        'full_source_paragraph':p['text'],'references':explicit_refs(p['text']),
                        'narrator':None,'grade':None,'page':None,
                        'attribution_note':'Source prose contains a reporting formula; entire context preserved, not promoted to standalone verified hadith.',
                        'translation_origin':'human','translator':'دکتر عبدالرحیم فیروز هروی'})
            metadata={'id':f'fa-faiz-al-bari-v{v}','language':'fa','source_volume':v,
                'title':'فیض الباری شرح مختصر صحیح البخاری','title_arabic':'فيض البارئ في شرح «التجرید للجامع الصحیح»',
                'author_translator_commentator':'دکتر عبدالرحیم فیروز هروی','canonical_collection':'Sahih al-Bukhari',
                'abridger_as_printed':'احمد بن احمد بن عبداللطیف شَرْجِی زبیدی',
                'abridgment_title_as_printed':'التجرید الصریح لأحادیث الجامع الصحیح',
                'abridger_evidence':'volume 1 body paragraphs 401, 409',
                'edition':'اول (دیجیتال)','publication_date_as_printed':'دی (جدی) 1394شمسی، ربيع الأول 1437 هجری',
                'source_site_as_printed':'www.aqeedeh.com','source_url':'https://www.aqeedeh.com/',
                'file_name':path.name,'file_sha256':archive['source_sha256'],'input_format':'docx','extraction_method':'direct_ooxml',
                'translation_origin':'human','translation_origin_evidence':'Named translator and commentary author on source title and explanatory preface.',
                'primary_occurrence_count':len(volume_records),'body_paragraph_count':len(ps),
                'footnote_count':len(footnotes),'source_local_sequence_range':[OFFSET[v]+1,OFFSET[v]+len(volume_records)],
                'source_notes':['An abridgment and commentary; not the complete canonical Bukhari corpus.','Local numbering and printed canonical citations are separate.','Raw font-encoded honorifics are preserved with font metadata.']}
            if v==5:metadata['source_notes'].append('Supplied document explicitly notes printed page 391 / Word page 270 is incomplete; surviving fragment retained.')
            dump(BASE/f'volume{v}.metadata.json',metadata)
            dump(BASE/f'volume{v}.source-archive.json',archive)
            jsonl(BASE/f'volume{v}.primary.jsonl',volume_records)
            print(f'Volume {v}: {len(volume_records)} primary positions, {len(ps)} paragraphs, {len(footnotes)} footnotes')
    jsonl(BASE/'primary_records.jsonl',primary)
    jsonl(BASE/'hadith_only_primary_records.jsonl',[r for r in primary if r['record_type']!='hadith_reference'])
    jsonl(BASE/'reference_only_positions.jsonl',[r for r in primary if r['record_type']=='hadith_reference'])
    jsonl(BASE/'variant_records.jsonl',variants)
    jsonl(BASE/'supporting_records.jsonl',supporting)
    explicit_quotes=[]
    merged=set()
    for i,q in enumerate(supporting):
        if q['id'] in merged or q['record_type']!='quoted_hadith': continue
        if q.get('quote_language')=='und': continue
        record={k:q[k] for k in ['id','language','source_id','source_volume','source_filename','content_kind','parent_ids','source_locator','text','references','narrator','grade','page','translation_origin','translator','text_transformations']}
        record['text']=dict(record['text'])
        record['raw_text']={'arabic':q['source_quote'] if q['quote_language']=='ar' else None,
                            'translation':q['source_quote'] if q['quote_language']=='fa' else None}
        record.update({'record_type':'quoted_hadith','content_kind':'quoted_hadith_excerpt','footnotes':[],
                       'commentary':None,'source_local_number':None,'source_notes':[{'code':'source_attributed_hadith_excerpt','detail':'Exact quoted words only; author commentary excluded. Source-attribution extraction is not an independent authenticity grading.'}]})
        if q['id']=='fa-faiz-al-bari-v5-fn225-p0-q001':
            record['record_type']='companion_report';record['content_kind']='quoted_companion_saying'
            record['narrator']={'name_as_printed':'علی','role':'quoted_speaker','attribution':'companion, not Prophet'}
            record['source_notes']=[{'code':'source_reported_companion_quote','detail':'The quoted speaker is Ali; source discussion explicitly contrasts this saying with a hypothetical alternative. Commentator argument excluded.'}]
        if q['id']=='fa-faiz-al-bari-v5-fn324-p2-q001':
            record['grade']={'as_printed':'ضعیف','normalized':'weak','scope':'isnad of this quoted report',
                'attributor':'source commentator citing Ibn Kathir','named_authority_as_printed':'امام ابن کثیر',
                'evidence_text':'این حدیث از نگاه سند ضعیف است','source_locator':q['source_locator'],
                'independently_verified':False}
        if q['id']=='fa-faiz-al-bari-v6-fn353-p2-q001':
            record['grade']={'as_printed':'به سند ضعیفی','normalized':'weak','scope':'isnad of this quoted report',
                'attributor':'source commentator','named_authority_as_printed':None,
                'evidence_text':'بیهقی به سند ضعیفی روایت می‌کند','source_locator':q['source_locator'],
                'independently_verified':False}
        if record['grade']:
            ev=record['grade']['evidence_text'];loc=dict(q['source_locator'])
            loc['start']=q['full_source_paragraph'].index(ev);loc['end']=loc['start']+len(ev)
            record['grade']['source_locator']=loc
        # Link explicitly adjacent Arabic/Persian quotation pairs only when "یعنی" establishes translation.
        if q['quote_language']=='ar' and i+1<len(supporting):
            nq=supporting[i+1]
            if nq.get('quote_language')=='fa' and nq['source_id']==q['source_id'] and nq['source_locator']['part']==q['source_locator']['part'] and nq['source_locator'].get('footnote_id')==q['source_locator'].get('footnote_id') and nq['source_locator'].get('paragraph_index')==q['source_locator'].get('paragraph_index'):
                between=q['full_source_paragraph'][q['source_locator']['end']:nq['source_locator'].get('start',q['source_locator']['end'])]
                if len(between)<45 and 'یعنی' in between:
                    record['text']['translation']=nq['text']['translation']
                    record['raw_text']['translation']=nq['source_quote']
                    record['aligned_translation_locator']=nq['source_locator']
                    record['text_transformations']+=nq['text_transformations']
                    record['source_notes'].append({'code':'explicit_translation_pair','detail':'Adjacent source quote introduced by یعنی.'})
                    merged.add(nq['id'])
        explicit_quotes.append(record)
    # Source footnote has a missing closing/opening quotation boundary between
    # two reports about Waraqah. Separate only the two explicitly attributed
    # speech excerpts and exclude the intervening reporter prose.
    for i,r in enumerate(explicit_quotes):
        if r['id']=='fa-faiz-al-bari-v1-fn32-p4-q001':
            q=next(x for x in supporting if x['id']==r['id'])
            raw=q['source_quote']; cut=raw.index('، و از عائشهل')
            second=raw.index('او را در خواب دیدم')
            base=q['source_locator']['start']
            pieces=[]
            for pi,(lo,hi) in enumerate([(1,cut),(second,len(raw)-1)]):
                n=json.loads(json.dumps(r,ensure_ascii=False))
                n['id']=r['id']+f'-part{pi+1}'
                n['source_locator']['start']=base+lo;n['source_locator']['end']=base+hi
                n['text']={'arabic':None,'translation':raw[lo:hi]}
                n['raw_text']=dict(n['text']);n['text_transformations']=[]
                n['source_notes'].append({'code':'malformed_source_quote_boundary_separated','detail':'Two explicitly attributed speech excerpts separated at narration attribution; intervening side commentary excluded. Exact raw character spans retained.'})
                pieces.append(n)
            explicit_quotes[i:i+1]=pieces
            break
    jsonl(BASE/'explicit_hadith_quotation_records.jsonl',explicit_quotes)
    jsonl(BASE/'coverage_ledger.jsonl',ledgers)
    dump(BASE/'numbering_and_source_exceptions.json',anomalies)
    report={'primary_occurrences':len(primary),'separately_indexed_unnumbered_variants':len(variants),
        'supporting_items':len(supporting),'supporting_item_types':dict(collections.Counter(x['record_type'] for x in supporting)),
        'explicit_hadith_quotation_records':len(explicit_quotes),
        'side_comments_in_integration_records':0,
        'excluded_commentary_footnotes':sum(len(a['footnotes']) for a in archives),
        'primary_per_volume':dict(collections.Counter(x['source_volume'] for x in primary)),
        'hadith_only_primary_positions':sum(r['record_type']!='hadith_reference' for r in primary),
        'reference_only_positions':sum(r['record_type']=='hadith_reference' for r in primary),
        'coverage_entries':len(ledgers),'body_paragraphs':sum(len(a['body']) for a in archives),
        'footnotes':sum(len(a['footnotes']) for a in archives),'source_exceptions':len(anomalies),
        'missing_primary_translation_records':[r['id'] for r in primary if not r['text']['translation']],
        'missing_primary_arabic_records':[r['id'] for r in primary if not r['text']['arabic']],
        'unique_primary_ids':len({r['id'] for r in primary}),
        'validation_scope':'All source body paragraphs and footnote paragraphs captured and hash-accounted. Primary source positions reconciled by volume. Ancillary quotation candidates individually retained; ambiguous quotations stay supporting_quote. Not a word-by-word theological or independent canonical-source validation.'}
    dump(BASE/'extraction_summary.json',report)
    assert len(primary)==2230 and len({r['id'] for r in primary})==2230
    assert not report['missing_primary_translation_records'],report['missing_primary_translation_records']
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    build()
