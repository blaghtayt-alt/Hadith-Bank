#!/usr/bin/env python3
"""Deterministic source-preserving extraction of the two supplied Muslim DOCX files.

No canonical edition or grade is inferred from a local serial number.  Annotation
prose is retained in source ledgers only.  Numberless witnessed narrations are
explicitly included.  Unmapped source-font symbols remain explicit placeholders.
"""
from __future__ import annotations
import collections
import hashlib
import json
import pathlib
import re
import zipfile
from lxml import etree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
NUMBER = re.compile(r'^[\s\u200e\u200f]*([0-9٠-٩۰-۹]+)(?:\s*([بم]))?\s*[-ـ–.\)]\s*')
DIACRITICS = re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]')
COMMENT = re.compile(r'^\s*\(?\s*(?:توضیح\s*[:：]|شرح\s*[:：]|نکته\s*[:：]|علامه|امام نووی|نووی می|حافظ|یادآور|مترجم)')
PERSIAN = re.compile(r'[گچپژ]|می[\u200c ]?(?:گو|فر|کن|شو)|فرمود|روایت است|روایت می')
UNNUMBERED = {1: {1516}, 2: {2062, 3633}}
BODY_START = {1: 1104, 2: 1010}
BODY_END = {1: 4774, 2: 5017}
STANDALONE_COMMENTS = {
    1: {1550,1572,1735,1795,1828,1846,2091,2738,3023,3205,3226,3575,3658,
        3742,3875,3888,3964,3968,3998,4073,4145,4236,4285,4289,4319,4331,
        4335,4351,4382,4515,4563,4583,4752},
    2: {1073,1222,1539,1796,2007,2137,2153,2280,2322,2377,2384,2431,2469,
        2517,2565,2656,2702,2824,2844,2881,2886,2891,2945,3018,3279,3290,
        3328,3542,3567,3668,3777,4103,4182,4200,4468,4479,4499,4572,4618,5004},
}
# Exact starts of separately attributed editorial tails inside otherwise valid
# translation paragraphs.  Ordinary parentheticals inside translation remain.
EDITORIAL_TAILS = {
    (1,1500):' (البته گناهان', (1,1528):' (هدف گناهان',
    (1,1657):' (یعنی نشسته', (1,1778):' (یعنی آنچه',
    (1,1808):' (یعنی اینکه', (1,1932):' (چرا که',
    (1,2909):' (یعنی اکنون', (1,3016):' (البته انفاق',
    (1,3147):' (یعنی بلا', (1,3242):' (یعنی روزه',
    (1,3423):' (یعنی از', (1,3472):' (البته بعدها',
    (1,3747):' (ابن خطل', (1,3813):' (که نماز',
    (1,3970):'زیرا عقد آنها',
    (2,1124):' (یعنی او و قاتلش', (2,1777):' (در روایتی',
    (2,1808):' (قابل یادآوری', (2,1999):' (و در روایت صحیح',
    (2,2068):' (تبرک جستن فقط', (2,2152):' (چنین به نظر',
    (2,2971):' (اما امام نووی',
}
AGA_MAP={'F049':'سبحانه وتعالى','F072':'ﷺ','F074':'رضي الله عنه',
         'F079':'رضي الله عنهم','F075':'عليه السلام','F055':'عز وجل'}
FONT_EVIDENCE=ROOT/'work/font-evidence/hadithmv-fonts.html'
FONT_EVIDENCE_URL='https://hadithmv.github.io/tools/textEditor'
FONT_MAP_FILE=ROOT/'work/font-evidence/font-decoding-evidence.json'
FONT_MAP_DATA=json.loads(FONT_MAP_FILE.read_text())if FONT_MAP_FILE.exists()else{}
CTRADITIONAL_MAP=FONT_MAP_DATA.get('ctraditional',{}).get('map',{})
AGA_MAP.update(FONT_MAP_DATA.get('aga',{}).get('map',{}))
AGA_ALIAS=FONT_MAP_DATA.get('aga_lowcode_alias',{})
if AGA_ALIAS.get('font_family')=='AGA Arabesque':
    assert AGA_ALIAS['equivalent_code'] in AGA_MAP
    assert AGA_ALIAS['unicode']==AGA_MAP[AGA_ALIAS['equivalent_code']]
    AGA_MAP[AGA_ALIAS['raw_code']]=AGA_ALIAS['unicode']
SYMBOL_MAPS={'AGA Arabesque':AGA_MAP,**FONT_MAP_DATA.get('symbol_font_maps',{})}
RECOVERY_FILE=OUT/'publisher-text-recoveries.json'
RECOVERIES=json.loads(RECOVERY_FILE.read_text())if RECOVERY_FILE.exists()else[]
CONTEXT_RECOVERY_FILE=OUT/'contextual-symbol-recoveries.json'
if CONTEXT_RECOVERY_FILE.exists():RECOVERIES+=json.loads(CONTEXT_RECOVERY_FILE.read_text())

def decode_symbols(text):
    for font,mapping in SYMBOL_MAPS.items():
        for code,replacement in mapping.items():
            text=text.replace('⟦source-symbol '+font+':'+code+'⟧',replacement)
    return text

def sha(b):
    return hashlib.sha256(b).hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def jsonl(path, rows):
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')

def raw_text(p):
    return ''.join(p.xpath('.//w:t/text()', namespaces=NS))

def row_for(p, part, i, source):
    t = raw_text(p)
    display = []
    decoded = []
    decoding_events=[]
    events = []
    fonts = []
    at = 0
    display_at=0
    for node in p.iter():
        local = ET.QName(node).localname
        if local == 't' and ET.QName(node).namespace == NS['w']:
            s = node.text or ''
            display.append(s)
            run = node.getparent()
            fs = run.xpath('./w:rPr/w:rFonts/@w:ascii | ./w:rPr/w:rFonts/@w:hAnsi | ./w:rPr/w:rFonts/@w:cs', namespaces=NS)
            if any(('AGA' in x or 'HQPB' in x or 'CTraditional' in x) for x in fs):
                fonts.append({'text_offset': at, 'text': s, 'fonts': fs,
                              'run_style': (run.xpath('./w:rPr/w:rStyle/@w:val', namespaces=NS) or [None])[0]})
            csfonts=run.xpath('./w:rPr/w:rFonts/@w:cs',namespaces=NS)
            if csfonts==['CTraditional Arabic']:
                s_decoded=''.join(CTRADITIONAL_MAP.get(c,c)for c in s)
                for k,c in enumerate(s):
                    if c in CTRADITIONAL_MAP:
                        decoding_events.append({'font':'CTraditional Arabic','codepoint':f'U+{ord(c):04X}',
                            'raw_text_offset':at+k,'raw_display_start':display_at+k,'raw_display_end':display_at+k+1,
                            'original':c,'decoded':CTRADITIONAL_MAP[c],
                            'evidence_font_sha256':FONT_MAP_DATA.get('ctraditional',{}).get('font_sha256')})
                decoded.append(s_decoded)
            else:decoded.append(s)
            at += len(s)
            display_at+=len(s)
        elif local == 'sym':
            event = {'kind': 'symbol', 'text_offset': at, 'font': node.get(W+'font'), 'code': node.get(W+'char')}
            events.append(event)
            placeholder='⟦source-symbol ' + str(event['font']) + ':' + str(event['code']) + '⟧'
            display.append(placeholder)
            replacement=SYMBOL_MAPS.get(event['font'],{}).get(event['code'])
            decoded.append(replacement or placeholder)
            if replacement:decoding_events.append({'font':event['font'],'codepoint':event['code'],
                'raw_text_offset':at,'raw_display_start':display_at,'raw_display_end':display_at+len(placeholder),
                'original':placeholder,'decoded':replacement,
                'evidence_url':AGA_ALIAS.get('font_url')if event['font']=='AGA Arabesque'and event['code']==AGA_ALIAS.get('raw_code')else FONT_EVIDENCE_URL,
                'evidence_font_sha256':AGA_ALIAS.get('font_sha256')if event['font']=='AGA Arabesque'and event['code']==AGA_ALIAS.get('raw_code')else None})
            display_at+=len(placeholder)
        elif local in ('footnoteReference', 'endnoteReference'):
            events.append({'kind': local, 'text_offset': at, 'id': node.get(W+'id')})
        elif local in ('tab', 'br', 'cr', 'lastRenderedPageBreak', 'softHyphen', 'noBreakHyphen'):
            events.append({'kind': local, 'text_offset': at, 'type': node.get(W+'type')})
            if local == 'tab': display.append('\t');decoded.append('\t');display_at+=1
            elif local in ('br', 'cr') and node.get(W+'type') != 'page': display.append('\n');decoded.append('\n');display_at+=1
            elif local == 'noBreakHyphen': display.append('\u2011');decoded.append('\u2011');display_at+=1
        elif local in ('drawing', 'pict', 'object'):
            events.append({'kind': local, 'text_offset': at,
                           'xml_sha256': sha(ET.tostring(node))})
    return {
        'source_file': source, 'part': part, 'paragraph_index_zero_based': i,
        'paragraph_style': (p.xpath('./w:pPr/w:pStyle/@w:val', namespaces=NS) or [None])[0],
        'text': t, 'text_with_symbol_placeholders': ''.join(display),
        'text_decoded':''.join(decoded),'font_decoding_events':decoding_events,
        'xml_sha256': sha(ET.tostring(p)), 'events': events,
        'source_font_runs': fonts,
    }

def is_main_start(row, vol):
    i, t = row['paragraph_index_zero_based'], row['text']
    if i in UNNUMBERED[vol]: return True
    if not BODY_START[vol] <= i < BODY_END[vol]: return False
    if (row['paragraph_style'] or '').startswith('TOC'): return False
    m = NUMBER.match(t)
    if not m: return False
    rest = DIACRITICS.sub('', t[m.end():]).lstrip()
    return bool(re.match(r'^و?عن', rest))

def is_heading(row):
    t=row['text'].lstrip(' \t\u200e\u200f')
    s=row['paragraph_style']
    if not t.strip():return False
    if t.startswith('ترجمه'):return False
    if t.startswith('باب'):return True
    if s=='a1':return True
    if s=='a2':return True
    if s=='a3' and t.startswith('نامه'):return True
    # a3 is also used for poetry embedded in a hadith; not a boundary.
    return False

def citation_list(text):
    # Written citations, not an external verification or assumed numbering system.
    found=[]
    for m in re.finditer(r'\(\s*م\s*[/／]\s*([^()]+)\)',text):
        label=m.group(1).strip()
        found.append({'collection':'Sahih Muslim','number_as_printed':label,
                      'number_normalized':label.translate(DIGITS), 'citation_as_printed':m.group(0),
                      'evidence':'source_citation', 'independently_verified':False})
    return found

def strip_prefix(t, start, unnumbered=False):
    if start:
        t=NUMBER.sub('',t,count=1)
        if unnumbered and t.startswith('ترجمه:'):
            t=t[len('ترجمه:'):].lstrip()
    return t

def separate_inline_annotations(text):
    """Parenthetical spans retained as auditable source annotations.

    Their exclusion from clean display is intentionally explicit. It is not a
    claim that source parentheses never contain narration, so source text and
    offsets are retained for review and reconstruction.
    """
    stack=[];spans=[]
    for i,c in enumerate(text):
        if c=='(': stack.append(i)
        elif c==')' and stack:
            a=stack.pop()
            if not stack:spans.append((a,i+1))
    # Pure numeric source references and blank footnote slots are annotations.
    # Inline Persian translator glosses are annotated, not silently discarded.
    return [{'start':a,'end':b,'text':text[a:b],'classification':'source_parenthetical'}for a,b in spans]

def make_record(block, vol, headings, note_map):
    first=block[0];i=first['paragraph_index_zero_based'];m=NUMBER.match(first['text'])
    num=(m.group(1).translate(DIGITS)+(m.group(2) or '')) if m else None
    if num is not None and num.isdigit():num=int(num)
    rid=f'fa-muslim-mundhiri-tarshabi-v{vol}-p{i:05d}'
    state='arabic'; ar=[];fa=[];comments=[];assign=[];exceptions=[];removed_spans=[]
    for j,row in enumerate(block):
        t=row['text_with_symbol_placeholders'];plain=row['text'];part='blank' if not t.strip() else state
        if j>0 and (COMMENT.match(plain) or row['paragraph_index_zero_based'] in STANDALONE_COMMENTS[vol]):state='commentary'
        if j>0 and state=='arabic':
            n=NUMBER.match(plain)
            if plain.lstrip(' \t\u200e\u200f').startswith('ترجمه') or (n and PERSIAN.search(plain[n.end():][:160])) or PERSIAN.search(plain[:160]):
                state='translation'
        part='blank' if not t.strip() else state
        if part=='arabic':ar.append(row)
        elif part=='translation':fa.append(row)
        elif part=='commentary':comments.append(row)
        assign.append((row['paragraph_index_zero_based'],part))
    if not fa:
        exceptions.append('No explicit Persian translation boundary detected')
    ar_strings=[]
    for n,r in enumerate(ar):ar_strings.append(strip_prefix(r['text_with_symbol_placeholders'],n==0,i in UNNUMBERED[vol]))
    ar_source='\n'.join(ar_strings).strip()
    fa_strings=[]
    for n,r in enumerate(fa):
        t=r['text_with_symbol_placeholders']
        if n==0:
            if re.match(r'^[\s\u200e\u200f]*ترجمه\s*[:：]',t):t=re.sub(r'^[\s\u200e\u200f]*ترجمه\s*[:：]\s*','',t,count=1)
            elif NUMBER.match(t):t=NUMBER.sub('',t,count=1)
        fa_strings.append(t)
    fa_source='\n'.join(fa_strings).strip()
    cites=citation_list(ar_source)
    # Collection citations are metadata, never part of the displayed hadith.
    ar_decoded='\n'.join(strip_prefix(r['text_decoded'],n==0,i in UNNUMBERED[vol])for n,r in enumerate(ar)).strip()
    ar_clean=re.sub(r'\(\s*م\s*[/／]\s*[^()]+\)','',ar_decoded).strip()
    # Empty parentheses are original footnote anchors, not hadith wording.
    ar_clean=re.sub(r'\(\s*\)','',ar_clean)
    fa_clean_strings=[]
    for n,r in enumerate(fa):
        t=r['text_decoded']
        key=(vol,r['paragraph_index_zero_based'])
        if key in EDITORIAL_TAILS:
            marker=EDITORIAL_TAILS[key]
            assert marker in t,(key,marker)
            at=t.index(marker)
            raw=r['text_with_symbol_placeholders'];rawat=raw.index(marker)
            removed_spans.append({'paragraph_index_zero_based':r['paragraph_index_zero_based'],
                                  'start':rawat,'end':len(raw),'text':raw[rawat:],
                                  'coordinate_space':'text_with_symbol_placeholders',
                                  'reason':'Separable editorial tail, excluded at user request'})
            t=t[:at].rstrip()
        if n==0:
            if re.match(r'^[\s\u200e\u200f]*ترجمه\s*[:：]',t):t=re.sub(r'^[\s\u200e\u200f]*ترجمه\s*[:：]\s*','',t,count=1)
            elif NUMBER.match(t):t=NUMBER.sub('',t,count=1)
        fa_clean_strings.append(t)
    fa_clean=re.sub(r'\(\s*\)','','\n'.join(fa_clean_strings).strip())
    ar_clean=decode_symbols(ar_clean)
    fa_clean=decode_symbols(fa_clean)
    source_recoveries=[]
    for recovery in RECOVERIES:
        if recovery['record_id']!=rid:continue
        assert recovery['field']in('arabic','translation')
        if recovery['field']=='arabic':
            assert ar_clean.count(recovery['before'])==1,(rid,'Source recovery anchor changed')
            ar_clean=ar_clean.replace(recovery['before'],recovery['after'],1)
        else:
            assert fa_clean.count(recovery['before'])==1,(rid,'Source recovery anchor changed')
            fa_clean=fa_clean.replace(recovery['before'],recovery['after'],1)
        source_recoveries.append(recovery)
    # Preserve typography and all words; no guessed spelling/honorific repairs.
    footids=[]
    for r in block:
        for e in r['events']:
            if e['kind']=='footnoteReference' and e['id'] not in footids:footids.append(e['id'])
    foots=[note_map[n] for n in footids if n in note_map]
    if num==1193 and vol==2:exceptions.append('Printed serial 1193 appears on two separate narrations; each occurrence has a distinct paragraph-based stable ID')
    if i==2062 and vol==2:exceptions.append('Arabic narration incorrectly carries the printed label ترجمه: and no serial; located between printed 1340 and 1342; no serial inferred')
    elif i in UNNUMBERED[vol]:exceptions.append('Separate unnumbered Arabic narration followed by Persian translation retained')
    if vol==1 and i==2054:
        exceptions.append('Uploaded DOCX contains HQPB Quran glyphs and an adjacent CTraditional ب run. A narrowly scoped publisher-HTML recovery supplies the quoted Quran fragment and ordinary preposition; the exact original characters, fonts, tokens and recovery evidence remain in audit metadata.'if source_recoveries else 'Source has an explicit CTraditional Arabic ب glyph immediately before HQPB Quran quotation tokens; font decoding yields a contextually unusual honorific. Original character/font preserved without conjectural correction.')
    if vol==2 and i==3845:
        exceptions.append('Source literally begins عَنْجعَبْدِ with a joined extra ج; preserved as supplied, not silently corrected')
    symbols=[dict(e,paragraph_index_zero_based=r['paragraph_index_zero_based']) for r in block for e in r['events'] if e['kind']=='symbol']
    if symbols:exceptions.append('AGA symbols decoded only where independently documented; any publisher-text recovery is separately evidenced and does not establish a generic HQPB glyph map')
    # Capture the source's opening attribution literally; do not synthesize an isnad.
    opening=ar_clean.split(':',1)[0] if ':' in ar_clean else None
    if opening and len(opening)>300:opening=None
    rawlead=DIACRITICS.sub('',ar_clean)
    variants=[]
    for lang,txt in [('ar',ar_source),('fa',fa_source)]:
        pattern=r'(?:[ووَ\s]*ف[ِِيی]+\s+ر[ِِ]?و[َاا]يَ?ة|(?:و\s+)?در روایت(?:ی| دیگری|ی دیگر)?)'
        for vm in re.finditer(pattern,txt):
            variants.append({'language':lang,'marker_start':vm.start(),'marker':vm.group(0),
                             'text_from_marker':txt[vm.start():], 'scope':'embedded_variant_preserved_with_source_occurrence'})
    record={
        'id':rid,'language':'fa','record_kind':'main_hadith_occurrence',
        'source_edition_id':f'fa-muslim-mundhiri-tarshabi-v{vol}',
        'number':{'source_local':num,'source_local_raw':m.group(1)+(m.group(2) or '') if m else None,
                  'numbering_system':'Mukhtasar Sahih Muslim as printed; not canonical Muslim numbering'},
        'text':{'arabic':ar_clean or None,'translation':fa_clean or None},
        'source_text':{'arabic':ar_source,'translation':fa_source},
        'references':{'canonical_collection':'Sahih Muslim','citations_as_printed':cites,
                      'canonical_number':cites[0]['number_normalized'] if len(cites)==1 else None,
                      'canonical_number_status':'cited_in_supplied_source_not_independently_verified' if cites else 'not_stated',
                      'full_isnad':None,'opening_attribution_as_printed':opening,'grading':None},
        'source_headings':headings,
        'source_locator':{'file':first['source_file'],'part':'word/document.xml',
                          'paragraph_start_zero_based':i,'paragraph_end_zero_based':block[-1]['paragraph_index_zero_based'],
                          'printed_page':None},
        'translation_provenance':{'type':'human','label':'Human','translator':'عبدالقادر ترشابی',
                                   'evidence':'Named translator on supplied title page'},
        'footnote_references':[{'id':n,'source_part':'word/footnotes.xml'}for n in footids],
        'inline_parentheticals':{'arabic':separate_inline_annotations(ar_clean),'translation':separate_inline_annotations(fa_clean)},
        'embedded_variants':variants,
        'source_symbols':symbols,'source_exceptions':exceptions,
        'source_recoveries':source_recoveries,
        'font_decoding_events':[dict(e,paragraph_index_zero_based=r['paragraph_index_zero_based'])for r in block for e in r['font_decoding_events']],
        'excluded_side_commentary_paragraphs':[r['paragraph_index_zero_based']for r in comments],
        'excluded_side_commentary_spans':removed_spans,
        'excluded_note_ids':footids,
        'extraction':{'method':'DOCX OOXML native text','ocr_used':False,'batch_limit':None,
                      'source_words_rewritten':False},
    }
    return record,assign,comments

def process(vol):
    name=f'Sahih-Moslem-{vol}-Word.docx'; path=ROOT/'upload'/name
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('word/document.xml'))
        nodes=root.xpath('//w:body//w:p',namespaces=NS)
        rows=[row_for(p,'word/document.xml',i,name)for i,p in enumerate(nodes)]
        notes=[];note_map={};other=[]
        for part in z.namelist():
            if part in ('word/footnotes.xml','word/endnotes.xml'):
                nr=ET.fromstring(z.read(part))
                for n in nr:
                    ident=n.get(W+'id')
                    nrows=[row_for(p,part,i,name)for i,p in enumerate(n.xpath('.//w:p',namespaces=NS))]
                    note={'source_file':name,'part':part,'id':ident,'note_type':n.get(W+'type'),
                          'text':'\n'.join(r['text']for r in nrows),
                          'text_with_symbol_placeholders':'\n'.join(r['text_with_symbol_placeholders']for r in nrows),
                          'paragraphs':nrows}
                    notes.append(note)
                    if part=='word/footnotes.xml' and not n.get(W+'type'):note_map[ident]=note
            elif re.fullmatch(r'word/(?:header|footer)\d+\.xml',part):
                nr=ET.fromstring(z.read(part))
                other.extend(row_for(p,part,i,name)for i,p in enumerate(nr.xpath('.//w:p',namespaces=NS)))
        metadata={'id':f'fa-muslim-mundhiri-tarshabi-v{vol}','source_file':name,
                  'source_sha256':sha(path.read_bytes()),'source_bytes':path.stat().st_size,
                  'title':'مختصر صحیح مسلم','volume':vol,
                  'original_collection':'Sahih Muslim','compiler':'مسلم بن حجاج نیشابوری',
                  'abridger':'علامه زکی الدین عبدالعظیم منذری','translator':'عبدالقادر ترشابی',
                  'edition_as_printed':'اول (دیجیتال) 'if vol==1 else'اول دیجیتال) ',
                  'publication_date_as_printed':'خرداد (جوزا) 1395 شمسی -شعبان 1437 هجری',
                  'source_as_printed':'سایت عقیده- انتشارات حرمین','website_as_printed':'www.aqeedeh.com',
                  'translation_type':'human','metadata_basis':'Supplied title-page text',
                  'country':None,'canonical_numbering_edition':None,
                  'title_page_paragraphs':[r for r in rows[:54 if vol==1 else 60]if r['text'].strip()]}
    records=[];coverage={};comments_all=[];headers=[];active=[]
    h1=None;h2=None;h3=None
    def flush():
        nonlocal active
        if not active:return
        rec,assign,comments=make_record(active,vol,[h for h in [h1,h2,h3]if h],note_map)
        records.append(rec);comments_all.extend(comments)
        for i,role in assign:coverage[i]={'role':role,'record_id':rec['id']}
        active=[]
    for row in rows:
        i=row['paragraph_index_zero_based'];style=row['paragraph_style'];t=row['text']
        if is_main_start(row,vol):flush();active=[row];continue
        if BODY_START[vol]<=i<BODY_END[vol] and is_heading(row):
            flush()
            h={'text':row['text_decoded'],'text_raw':t,'style':style,'paragraph_index_zero_based':i}
            if style=='a1':h1=h;h2=None;h3=None
            elif style=='a2':h2=h;h3=None
            else:h3=h
            headers.append(h);coverage[i]={'role':'source_heading','record_id':None};continue
        if i>=BODY_END[vol]:flush()
        if active:active.append(row)
        else:
            role='blank' if not t.strip() else ('table_of_contents' if (style or '').startswith('TOC') else ('front_matter' if i<BODY_START[vol] else 'supporting_source_text'))
            coverage[i]={'role':role,'record_id':None}
    flush()
    for row in rows:row['coverage']=coverage[row['paragraph_index_zero_based']]
    assert len(coverage)==len(rows)
    assert sum(len(r['text'])for r in rows)==sum(len(raw_text(p))for p in nodes)
    assert len({r['id']for r in records})==len(records)
    serials=[r['number']['source_local']for r in records if isinstance(r['number']['source_local'],int)]
    suffixed=[r['number']['source_local']for r in records if isinstance(r['number']['source_local'],str)]
    summary={'volume':vol,'source_file':name,'source_sha256':metadata['source_sha256'],
             'body_paragraphs':len(rows),'body_text_characters':sum(len(r['text'])for r in rows),
             'main_narrations':len(records),'numbered_occurrences':len(serials)+len(suffixed),
             'plain_numeric_serial_occurrences':len(serials),'letter_suffixed_serials':suffixed,
             'unnumbered_occurrences':len(records)-len(serials)-len(suffixed),
             'serial_min':min(serials),'serial_max':max(serials),
             'serials_absent_from_printed_range':sorted(set(range(min(serials),max(serials)+1))-set(serials)),
             'repeated_serials':{str(n):c for n,c in collections.Counter(serials).items()if c>1},
             'body_symbol_tokens':sum(e['kind']=='symbol'for r in rows for e in r['events']),
             'footnotes':len(note_map),'header_footer_paragraphs':len(other),
             'coverage_roles':dict(collections.Counter(x['role']for x in coverage.values())),
             'records_missing_translation':[r['id']for r in records if not r['text']['translation']],
             'records_without_written_canonical_citation':sum(not r['references']['citations_as_printed']for r in records),
             'all_body_paragraphs_accounted_for':len(coverage)==len(rows),
             'unmapped_symbol_policy':'Explicit placeholders except documented AGA font decoding; original XML preserved by original DOCX',
             'symbol_mapping_evidence':{'url':FONT_EVIDENCE_URL,'sha256':sha(FONT_EVIDENCE.read_bytes()) if FONT_EVIDENCE.exists()else None},
             'font_decoding_map_evidence_sha256':sha(FONT_MAP_FILE.read_bytes())if FONT_MAP_FILE.exists()else None,
             'font_glyph_decodings':sum(len(r['font_decoding_events'])for r in rows),
             'excluded_standalone_commentary_paragraphs':len(comments_all),
             'excluded_editorial_tails':sum(len(r['excluded_side_commentary_spans'])for r in records),
             'no_ocr':True,'no_batch_cap':True,'no_qc_tags':True}
    base=OUT/f'muslim-v{vol}'
    jsonl(base.with_suffix('.main.jsonl'),records)
    jsonl(base.with_suffix('.source-paragraphs.jsonl'),rows)
    jsonl(base.with_suffix('.source-notes.jsonl'),notes)
    jsonl(base.with_suffix('.source-headers-footers.jsonl'),other)
    dump(base.with_suffix('.metadata.json'),metadata)
    dump(base.with_suffix('.coverage.json'),summary)
    jsonl(base.with_suffix('.excluded-commentary.jsonl'),comments_all)
    return summary

if __name__=='__main__':
    summaries=[process(v)for v in [1,2]]
    dump(OUT/'main-extraction-summary.json',summaries)
    print(json.dumps(summaries,ensure_ascii=False,indent=2))
