#!/usr/bin/env python3
"""Deterministic source-preserving extraction of the uploaded Persian Riyadh DOCX.

Source chapter/local numbering is kept distinct from original collection numbers.
No optical recognition is performed.  Font symbols and their run attributes are
preserved separately; display substitutions require a separately evidenced map.
"""
from pathlib import Path
from lxml import etree as E
from collections import Counter
import hashlib, json, re, unicodedata, zipfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1] / 'upload/tarjomeye-farsi-reyaz-al-salehin-heravi-Word.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
QN = lambda s: '{'+W+'}'+s

def dump(name,obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def jsonl(name,items):
    with (ROOT/name).open('w',encoding='utf-8') as f:
        for item in items: f.write(json.dumps(item,ensure_ascii=False,separators=(',',':'))+'\n')

def norm(s):
    return ''.join(c for c in s if not unicodedata.combining(c)).replace('ـ','').strip(' «\xa0')

def paragraph(p,i,part):
    tokens=[]; text=''; runs=[]
    for n in p.iter():
        tag=E.QName(n).localname
        v=None
        if tag=='t': v=n.text or ''
        elif tag=='sym': v=chr(int(n.get(QN('char')),16))
        elif tag=='tab':v='\t'
        elif tag=='br':v='\n'
        elif tag=='cr':v='\n'
        elif tag=='noBreakHyphen':v='\u2011'
        elif tag=='softHyphen':v='\u00ad'
        if v is not None:
            r=n
            while r is not None and r.tag != QN('r'):r=r.getparent()
            fonts={}
            if r is not None:
                f=r.find('w:rPr/w:rFonts',NS)
                if f is not None:fonts={E.QName(k).localname:v for k,v in f.attrib.items()}
            t={'kind':tag,'start':len(text),'end':len(text)+len(v),'value':v,'fonts':fonts}
            if tag=='sym':t.update(font=n.get(QN('font')),char_hex=n.get(QN('char')))
            tokens.append(t);text+=v
    for r in p.xpath('.//w:r',namespaces=NS):
        attrs={}
        rp=r.find('w:rPr',NS)
        if rp is not None:
            for n in rp:
                attrs[E.QName(n).localname]={E.QName(k).localname:v for k,v in n.attrib.items()}
        runs.append({'text':''.join(r.xpath('.//w:t/text()',namespaces=NS)),'properties':attrs,
                     'symbols':[dict(font=s.get(QN('font')),char_hex=s.get(QN('char'))) for s in r.xpath('.//w:sym',namespaces=NS)]})
    return {'paragraph_index':i,'part':part,'text':text,
            'plain_text':''.join(p.xpath('.//w:t/text()',namespaces=NS)),
            'style':p.xpath('string(w:pPr/w:pStyle/@w:val)',namespaces=NS),
            'tokens':tokens,'runs':runs,
            'footnote_ids':p.xpath('.//w:footnoteReference/@w:id',namespaces=NS),
            'endnote_ids':p.xpath('.//w:endnoteReference/@w:id',namespaces=NS),
            'bookmarks':p.xpath('.//w:bookmarkStart/@w:name',namespaces=NS)}

with zipfile.ZipFile(SOURCE) as z:
    body=E.fromstring(z.read('word/document.xml'))
    ps=[paragraph(p,i,'word/document.xml') for i,p in enumerate(body.xpath('//w:body//w:p',namespaces=NS))]
    ancillary_parts=[]
    for part in z.namelist():
        if re.match(r'word/(?:header\d+|footer\d+|footnotes|endnotes)\.xml$',part):
            root=E.fromstring(z.read(part))
            ancillary_parts.append({'part':part,'paragraphs':[paragraph(p,i,part) for i,p in enumerate(root.xpath('.//w:p',namespaces=NS))]})
    raw_xml_hashes={part:hashlib.sha256(z.read(part)).hexdigest() for part in z.namelist() if part.endswith('.xml')}

num_re=re.compile(r'^\s*([0-9۰-۹٠-٩]+)\s*(?:[-–.]\s*|(?=[و«]))')
ar_begin=re.compile(r'(?:و?عن|و\s+عن|ف?الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي|العشرون|وأما|حديث |فمنها)')
starts=[]
for p in ps[511:]:
    m=num_re.match(p['plain_text'])
    if m and p['style'] not in ['a1','a2'] and ar_begin.match(norm(p['plain_text'][m.end():])):
        starts.append((p['paragraph_index'],int(m[1])))
assert len(starts)==1896, len(starts)
assert [n for _,n in starts] == [989 if n==289 else 241 if n==341 else n for n in range(1,1897)]

toc=[]
for p in ps[75:466]:
    t=p['plain_text'];m=re.search(r'(\d+)\s*$',t)
    if m:toc.append({'title':t[:m.start()].strip(),'printed_page':int(m[1]),'paragraph_index':p['paragraph_index']})
toc_by_title={norm(x['title']):x for x in toc}
headings=[]
for p in ps[511:]:
    if p['style'] in ['a1','a2']:
        h={'text':p['text'],'paragraph_index':p['paragraph_index'],'style':p['style'],'toc':toc_by_title.get(norm(p['plain_text']))}
        headings.append(h)

assignments={i:{'paragraph_index':i,'role':('front_matter' if i<75 else 'table_of_contents' if i<466 else 'author_introduction' if i<511 else 'chapter_context'),'record_ids':[]} for i in range(len(ps))}
for h in headings:assignments[h['paragraph_index']]['role']='source_heading'

records=[];anomalies=[]
head_i=0;current_head=[]

def fa_start_text(t):
    t=norm(t)
    return (t.startswith(('از','و هم از','و نیز از','و از','پیامبر')) or
            any(w in t[:170] for w in ('روایت','می\u200cکند','می کند',' گفت','فرمود')))

def source_refs(indices):
    refs=[]
    for i in indices:
        raw=ps[i]['text'];n=norm(raw)
        if not any(s in n for s in ('رواه','رواها','روى','روی','رواية','روایت','متفق')):continue
        names=[]
        for code,pattern in [('sahih-bukhari',r'بخاري|بخاری'),('sahih-muslim',r'مسلم'),('jami-tirmidhi',r'ترمذي|ترمذی'),('sunan-abu-dawud',r'أبو داود|أبي داود|ابی داود|ابو داود'),('sunan-nasai',r'نسائي|نسائی'),('sunan-ibn-majah',r'ابن ماجه|ابن ماجة'),('muwatta-malik',r'مالك.*الموطأ|مالک.*الموطأ'),('musnad-ahmad',r'أحمد|احمد')]:
            if re.search(pattern,n):names.append(code)
        if 'متفق' in n:names=sorted(set(names+['sahih-bukhari','sahih-muslim']))
        if names:refs.append({'collection_ids':names,'hadith_number':None,'numbering_system':None,'scope':'printed_paragraph','paragraph_index':i,'text':raw,'verification':'printed_source_attribution_only'})
    return refs

def record_id(n):return f'fa-riyadh-heravi-{n:04d}'

for seq,(start,printed_ar) in enumerate(starts,1):
    end=starts[seq][0] if seq<len(starts) else 10138
    for i in range(start+1,end):
        if ps[i]['style'] in ['a1','a2']:end=i;break
    while head_i<len(headings) and headings[head_i]['paragraph_index']<start:
        h=headings[head_i]
        if norm(h['text']).startswith(('كتاب','کتاب')):current_head=[h]
        elif current_head and norm(current_head[0]['text']).startswith(('كتاب','کتاب')):current_head=current_head[:1]+[h]
        else:current_head=[h]
        head_i+=1
    fa_candidates=[i for i in range(start+1,end) if num_re.match(ps[i]['plain_text'])]
    if fa_candidates:fa_start=fa_candidates[0]
    else:
        candidates=[i for i in range(start+1,end) if fa_start_text(ps[i]['plain_text'])]
        assert candidates,(seq,start,end)
        fa_start=candidates[0]
        anomalies.append({'type':'persian_number_label_absent','record_id':record_id(seq),'paragraph_index':fa_start,'text':ps[fa_start]['text']})
    m=num_re.match(ps[fa_start]['plain_text']);printed_fa=int(m[1]) if m else None
    if printed_ar!=seq or (printed_fa is not None and printed_fa!=seq):
        anomalies.append({'type':'source_number_disagreement','record_id':record_id(seq),'sequence':seq,'printed_arabic_number':printed_ar,'printed_persian_number':printed_fa,'arabic_paragraph_index':start,'persian_paragraph_index':fa_start,'policy':'printed labels preserved; local source sequence independently stored; no canonical collection numbering asserted'})
    ar_ix=[];fa_ix=[];comment_ix=[];components=[];in_comment=False
    for i in range(start,end):
        p=ps[i];t=norm(p['plain_text'])
        if i<fa_start:
            if i!=start and (t.startswith(('ومعناه','والمعنى','معناه','قوله','وقوله','قال المصنف','قال العلماء','قلت')) or p['style']=='a7' and t.startswith(('معنى','ومعنى','هو','بضم','بفتح','وهو'))):
                role='arabic_editorial_note';comment_ix.append(i)
            else:role='arabic_source_text';ar_ix.append(i)
        else:
            if re.match(r'^ش\s*:',t):in_comment=True
            if in_comment:role='persian_translator_commentary';comment_ix.append(i)
            else:role='persian_source_translation';fa_ix.append(i)
        if not t:role='blank_paragraph'
        components.append({'paragraph_index':i,'role':role,'text':p['text']})
        assignments[i]={'paragraph_index':i,'role':role,'record_ids':[record_id(seq)]}
    ar_text='\n'.join(ps[i]['text'] for i in ar_ix if ps[i]['text'])
    fa_text='\n'.join(ps[i]['text'] for i in fa_ix if ps[i]['text'])
    first=ps[start]['text'];number=num_re.match(first)
    beginning=first[number.end():] if number else first
    narrator_match=re.search(r'(?:ع[َ]?ن[ْ]?|عَنِ)\s+(.+?)(?=\s+(?:قَال|قال|أَن|أن|عَنِ|عَن\s|عن النبي|عن النبی))',beginning)
    narrator=narrator_match.group(1).strip(' «') if narrator_match else None
    rec={'id':record_id(seq),'language':'fa','record_type':'hadith','occurrence_kind':'numbered_source_occurrence',
         'local_sequence':seq,'source_local_number':str(seq),'printed_labels':{'arabic':printed_ar,'translation':printed_fa},
         'collection':'riyadh-al-salihin','book_title':'ترجمه فارسی ریاض الصالحین',
         'edition_id':'fa-riyadh-heravi-1394-digital','translator':'عبد الله خاموش هروی',
         'text':{'arabic':ar_text,'translation':fa_text},
         'commentary':{'segments':[{'paragraph_index':i,'text':ps[i]['text'],'language':'ar' if i<fa_start else 'fa'} for i in comment_ix]},
         'narrator':{'as_printed':narrator,'identification':'source_prefix_only' if narrator else None},
         'isnad':None,'references':{'original_collections':source_refs(ar_ix),'canonical_numbers':None},
         'footnotes':[], 'source_headings':list(current_head),
         'source_locator':{'file':SOURCE.name,'part':'word/document.xml','paragraph_start':start,'paragraph_end_exclusive':end,'arabic_start':start,'translation_start':fa_start,'page':None,'page_note':'The DOCX has only three stale rendered page breaks; no reliable per-occurrence page mapping is asserted.'},
         'source_components':components,
         'provenance':{'translation_method':'human','translation_method_basis':'Named translator printed in source front matter','input_kind':'native_docx_text','source_website_as_printed':'www.aqeedeh.com','extraction':'direct OOXML; all symbols retained'},
         'doctrinal_notes':[]}
    if seq==1251:rec['doctrinal_notes']=[{'kind':'explicit_shia_view_in_translator_commentary','paragraph_index':6893,'text':ps[6893]['text'],'attribution':'translator note describing a Shia view; not the narration; does not establish author affiliation'}]
    records.append(rec)

context=[{'paragraph_index':i,'role':a['role'],'text':ps[i]['text'],'style':ps[i]['style']} for i,a in assignments.items() if not a['record_ids']]
context_candidates=[x for x in context if x['paragraph_index']>=466 and any(w in norm(x['text']) for w in ('رسول','النبي','النبی','پیامبر','حديث','حدیث'))]

jsonl('source-paragraphs.jsonl',ps)
dump('source-parts.json',ancillary_parts)
dump('records-primary.json',records)
jsonl('records-primary.jsonl',records)
dump('source-number-anomalies.json',anomalies)
dump('source-headings.json',headings)
dump('source-context.json',context)
dump('context-hadith-candidates.json',context_candidates)
dump('coverage.json',{'source_file':SOURCE.name,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'body_paragraph_count':len(ps),'body_plain_text_characters':sum(len(p['plain_text']) for p in ps),
    'body_symbol_count':sum(t['kind']=='sym' for p in ps for t in p['tokens']),
    'primary_hadith_count':len(records),'first_local_sequence':1,'last_local_sequence':1896,
    'missing_source_sequence_positions':[],'paragraph_assignments':list(assignments.values()),
    'source_number_anomaly_count':len(anomalies),'raw_xml_part_sha256':raw_xml_hashes,
    'footnote_content_count':0,'record_text_characters':sum(len(r['text']['arabic'])+len(r['text']['translation']) for r in records),
    'integrity':'All body paragraphs, tokens, symbols and auxiliary part paragraphs retained. Primary record text plus commentary and context cover the body. No deduplication or row limits applied.',
    'limits':['Display font symbol mapping requires separate visual evidence.','No complete visual page fidelity review is claimed.','Canonical original-collection numbering is not inferred from Riyadh local numbering.']})
print(json.dumps({'primary_records':len(records),'body_paragraphs':len(ps),'source_anomalies':len(anomalies),'context_hadith_candidates':len(context_candidates)},ensure_ascii=False))
