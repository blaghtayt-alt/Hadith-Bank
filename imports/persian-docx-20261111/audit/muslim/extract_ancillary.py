#!/usr/bin/env python3
"""Extract reviewed exact hadith quotations from the supplied Muslim apparatus.

Only quoted narration or an explicit separately cited narration is emitted.
Scholar commentary, Quran-only quotations, and uncertain paraphrases remain in
the supporting-source audit.  All character spans are zero-based, end-exclusive.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import re
from extract_muslim import OUT, decode_symbols, dump, jsonl

def readlines(path):return [json.loads(s)for s in path.read_text().splitlines()]
ROWS={v:readlines(OUT/f'muslim-v{v}.source-paragraphs.jsonl')for v in [1,2]}
NOTES={v:{n['id']:n for n in readlines(OUT/f'muslim-v{v}.source-notes.jsonl')if n['part']=='word/footnotes.xml'and not n['note_type']}for v in [1,2]}
MAIN={v:readlines(OUT/f'muslim-v{v}.main.jsonl')for v in [1,2]}
BY_ID={r['id']:r for v in [1,2]for r in MAIN[v]}
RECORDS=[];AUDIT=[];USED=set()

def source(v,p,note=False):
    if note:return NOTES[v][str(p)]['text_with_symbol_placeholders']
    return ROWS[v][p]['text_with_symbol_placeholders']

def quotes(text):return [(m.start(1),m.end(1))for m in re.finditer('«([^»]*)»',text)]

def add(v,p,spans_ar=None,spans_fa=None,note=False,suffix='q1',kind='quoted_hadith',narrator=None,source_note_ids=None,explicit_collections=None,explanation=None):
    text=source(v,p,note);spans_ar=spans_ar or [];spans_fa=spans_fa or []
    assert spans_ar or spans_fa
    for a,b in spans_ar+spans_fa:assert 0<=a<b<=len(text)
    row=NOTES[v][str(p)]if note else ROWS[v][p]
    if note:
        font_events=[];base=0
        for nr in row['paragraphs']:
            for event in nr['font_decoding_events']:
                event=dict(event)
                event['source_note_paragraph_index_zero_based']=nr['paragraph_index_zero_based']
                event['raw_display_start']+=base
                event['raw_display_end']+=base
                font_events.append(event)
            base+=len(nr['text_with_symbol_placeholders'])+1
    else:font_events=row['font_decoding_events']
    def fragment(a,b):
        piece=text[a:b]
        # Footnote spans use the concatenated note coordinate space; apply
        # the same explicitly witnessed font events as body quotations.
        edits=[e for e in font_events if a<=e['raw_display_start'] and e['raw_display_end']<=b]
        for e in reversed(edits):
            x=e['raw_display_start']-a;y=e['raw_display_end']-a
            assert piece[x:y]==e['original']
            piece=piece[:x]+e['decoded']+piece[y:]
        return decode_symbols(piece)
    pieces_ar=[fragment(a,b)for a,b in spans_ar];pieces_fa=[fragment(a,b)for a,b in spans_fa]
    for x in pieces_ar+pieces_fa:assert x.strip()
    part='word/footnotes.xml'if note else'word/document.xml'
    locator=f'note{p}'if note else f'p{p:05d}'
    rid=f'fa-muslim-mundhiri-tarshabi-v{v}-{locator}-{suffix}'
    if source_note_ids is None:
        source_note_ids=[] if note else [e['id']for e in row['events']if e['kind']=='footnoteReference']
    # Note text is retained only as citation/attribution evidence in the audit.
    note_citations=[{'note_id':str(i),'citation_text_as_printed':NOTES[v][str(i)]['text']}for i in source_note_ids]
    parent=None if note else row['coverage']['record_id']
    refs={'citations_as_printed':note_citations,'collections_as_stated':explicit_collections or [],
          'canonical_number':None,'canonical_number_status':'not_independently_verified',
          'narrator_as_printed':narrator,'full_isnad':None,'grading':None}
    record={
        'id':rid,'language':'fa','record_kind':kind,
        'source_edition_id':f'fa-muslim-mundhiri-tarshabi-v{v}',
        'number':{'source_local':None,'source_local_raw':None,'numbering_system':'Unnumbered quotation in source apparatus'},
        'text':{'arabic':decode_symbols('\n'.join(pieces_ar))if pieces_ar else None,
                'translation':decode_symbols('\n'.join(pieces_fa))if pieces_fa else None},
        'references':refs,
        'source_locator':{'file':f'Sahih-Moslem-{v}-Word.docx','part':part,
                          'paragraph_index_zero_based':p if not note else None,
                          'note_id':str(p)if note else None,'printed_page':None,
                          'arabic_character_spans':[{'start':a,'end':b}for a,b in spans_ar],
                          'translation_character_spans':[{'start':a,'end':b}for a,b in spans_fa]},
        'source_headings':BY_ID[parent]['source_headings']if parent else [],
        'related_record_id':parent,
        'font_decoding_events':[e for e in font_events if any(a<=e['raw_display_start']and e['raw_display_end']<=b for a,b in spans_ar+spans_fa)],
        'translation_provenance':{'type':'human','label':'Human','translator':'عبدالقادر ترشابی',
                                   'evidence':'Supplied named-translator edition'},
        'extraction':{'method':'Exact manually adjudicated source spans','ocr_used':False,
                      'side_commentary_removed':True,'source_words_rewritten':False},
    }
    RECORDS.append(record)
    AUDIT.append({'id':rid,'source_volume':v,'source_part':part,'source_paragraph_or_note':p,
                  'full_context':text,'source_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                  'arabic_spans':spans_ar,'translation_spans':spans_fa,
                  'source_note_citations':note_citations,'decision':explanation or'Exact narration spans; surrounding commentary omitted'})
    USED.add((v,p,note))

def add_quotes(v,p,qa=None,qf=None,**kwargs):
    q=quotes(source(v,p,kwargs.get('note',False)))
    add(v,p,[q[x]for x in qa or []],[q[x]for x in qf or []],**kwargs)

def exact_span(text,start,end=None):
    a=text.index(start)
    b=text.index(end,a)if end else len(text)
    return(a,b)

# These thirteen introductory quotations were individually read in context.
INTRO={1032:None,1035:None,1036:'عرباض بن ساریه',1037:'مقدام بن معدیکرب',
       1038:None,1039:'عبدالله بن مسعود',1040:'انس بن مالک',1041:'عایشه',
       1046:'ابوهریره',1047:'ابوهریره',1049:'ابوهریره',1053:'عبدالله بن مسعود'}
for p,narrator in INTRO.items():
    add_quotes(1,p,qa=[0],qf=[1],narrator=narrator,
               kind='quoted_companion_report'if p==1053 else'quoted_hadith',
               explicit_collections=['Sahih al-Bukhari','Sahih Muslim']if p==1032 else None)
add_quotes(1,1048,qf=[0],narrator='عمر بن خطاب',kind='quoted_companion_report')

# Explicit prophetic quotations in explanatory apparatus. Repeated excerpts are
# preserved as separate source occurrences, not merged into their main entries.
for v,p,groups in [
    (1,1162,[[0]]),(1,1297,[[0],[1]]),(1,1496,[[0],[1],[2]]),
    (1,1565,[[0]]),(1,1676,[[0]]),(1,1800,[[0]]),(1,1835,[[0,1]]),
    (2,2048,[[0]]),(2,2555,[[0],[1]]),(2,3511,[[0]]),(2,4572,[[0]]),
]:
    for k,g in enumerate(groups):add_quotes(v,p,qf=g,suffix=f'q{k+1}')

# Two clauses of one hadith; the second quote is not closed in the supplied file.
t=source(1,2354);q=quotes(t)
second=exact_span(t,'البته هرکس خواست، نماز بخواند','(). همچنین انس')
add(1,2354,spans_fa=[q[0],second],suffix='q1',source_note_ids=['35'],
    explanation='One narration with two quoted clauses; second source quotation lacks a closing guillemet. Exact words retained without repair.')
# Separate Anas narration, then its separately introduced Muslim variant.
add(1,2354,spans_fa=[exact_span(t,'هنگامی‌که اذان مغرب گفته می‌شد',' و در روایت صحیح مسلم')],
    suffix='q2',narrator='انس',source_note_ids=['36'])
add(1,2354,spans_fa=[exact_span(t,'اگر فرد بیگانه‌ای وارد مسجد می‌شد','(). لذا طبق احادیث فوق')],
    suffix='q3',source_note_ids=['36'],explicit_collections=['Sahih Muslim'])

# Explicitly attributed report clauses, even where the source does not enclose
# the transmitted wording in guillemets. No scholarly inference is included.
t=source(1,2161)
add(1,2161,spans_fa=[exact_span(t,'رسول الله ص بیشتر وقتها',' امام نووی')],suffix='q1',
    narrator='انس',explicit_collections=['Sahih Muslim'])
t=source(1,3575)
add(1,3575,spans_fa=[exact_span(t,'رسول الله ص هر نماز را',' و صحیح هم')],suffix='q1',
    narrator='ابن عمر',explicit_collections=['Sunan Abi Dawud'])
t=source(1,4319)
add(1,4319,spans_fa=[exact_span(t,'رسول الله ص حجامت نمود','، کسب حجام')],suffix='q1')

# Clearly separated transmitted variants in standalone parenthetical apparatus.
t=source(2,3290)
add(2,3290,spans_fa=[exact_span(t,'مردی از انصار گفت:',').')],suffix='q1',
    narrator='مردی از انصار',explicit_collections=['Sahih al-Bukhari'])
t=source(2,3567)
add(2,3567,spans_fa=[exact_span(t,'مادر در ادامه گفت:',').')],suffix='q1',
    explicit_collections=['Sahih al-Bukhari'])
t=source(2,4103)
add(2,4103,spans_fa=[exact_span(t,'الله متعال به روستای مقصدف',').')],suffix='q1')

# Hadith excerpts contained in two separately identified translator tails.
add_quotes(2,1777,qf=[1],suffix='q1',source_note_ids=[],
           explanation='Exact separately introduced variant in translator tail; surrounding annotation excluded.')
t=source(2,1999)
add(2,1999,spans_fa=[exact_span(t,'از آن، تناول فرمود.',')')],
    suffix='q1',source_note_ids=[],explicit_collections=['Sahih al-Bukhari'])

# Actual prophetic narration embedded in source footnotes, not footnote prose.
t=source(1,28,True)
add(1,28,note=True,spans_fa=[exact_span(t,'از رسول الله ص پرسیدم :',' البته حدیث ابن عباس')],
    suffix='q1',narrator='ابوذر')
qs=quotes(t)
add(1,28,note=True,spans_fa=[qs[-1]],suffix='q2',narrator='عایشه')
add_quotes(1,33,note=True,qf=[0],suffix='q1',explicit_collections=['Sahih Muslim'])

# The rest of the apparatus is retained as source evidence, not counted as hadith.
support=[]
for v in [1,2]:
    for r in ROWS[v]:
        p=r['paragraph_index_zero_based']
        if r['coverage']['role']in('front_matter','commentary','supporting_source_text'):
            if '«'in r['text']or re.search(r'حدیث|رسول|روایت',r['text']):
                support.append({'volume':v,'paragraph_index_zero_based':p,'text':r['text'],
                                'disposition':'Has exact extracted quotation(s); surrounding prose excluded'if(v,p,False)in USED else
                                'Supporting text only; not asserted as a separate exact hadith quotation',
                                'not_counted_as_additional_hadith':(v,p,False)not in USED})

assert len(RECORDS)==len({r['id']for r in RECORDS})
for v in [1,2]:
    jsonl(OUT/f'muslim-v{v}.confirmed-ancillary-hadiths.jsonl',[r for r in RECORDS if f'-v{v}-'in r['id']])
jsonl(OUT/'ancillary-span-audit.jsonl',AUDIT)
jsonl(OUT/'supporting-quote-candidates.jsonl',support)
dump(OUT/'ancillary-summary.json',{'confirmed_ancillary_occurrences':len(RECORDS),
                                  'by_volume':{str(v):sum(f'-v{v}-'in r['id']for r in RECORDS)for v in [1,2]},
                                  'scope':'Exact hadith and companion-report quotations only; no surrounding scholarly commentary',
                                  'all_spans_validated_against_exact_source':True})
print(json.dumps({'count':len(RECORDS),'by_volume':{v:sum(f'-v{v}-'in r['id']for r in RECORDS)for v in [1,2]}},ensure_ascii=False))
