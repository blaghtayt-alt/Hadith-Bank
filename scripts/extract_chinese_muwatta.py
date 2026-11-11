#!/usr/bin/env python3
"""Auditable native DOCX extraction, preserving every paragraph and split segment.
Fixed owner-supplied Muwatta al-Shaybani Chinese source; no canonical mappings.
All paragraph indices are zero-based document-body paragraph indices.
"""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from collections import Counter
import argparse, hashlib, json, re

N = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + N['w'] + '}'
SOURCE_SHA256 = 'cf65c0e865be95a709f228b021e23b94dbc2e3a88d52139330b623a070f5d1b3'
NUMBER = re.compile(r'^(\d+)\s*[、.．。]')
SUBSECTION = re.compile(r'^[（(](\d+)[）)]\s*(.*)$')
SOURCE_CONTINUATIONS = {
    123: (64, 'The preceding paragraph ends inside the same quotation; this paragraph begins with its Qur’an verse citation and closes the quoted account.'),
    245: (135, 'Ibn Shihab’s unnumbered addition expressly reports the Prophet saying Amin and directly follows numbered report 135; retained as a distinct paragraph within that source occurrence, not a new global hadith.'),
}
INLINE_SPLITS = {
    83: (44, '—即流精溢只破小净不坏大净，年老及体弱者时有发生。', 'commentary', 'Unquoted explanatory medical/legal gloss appended after the report; author not established.'),
    233: (131, '（系指拜功之回赐)', 'commentary', 'Explicit interpretive gloss following the closed Prophetic quotation.'),
    1055: (525, '谢巴尼说', 'commentary', 'Explicit al-Shaybani legal commentary appended inside the numbered source paragraph.'),
    1131: (558, '伊布·麦斯欧德、艾布·哈尼法及哈奈菲教法学家们均这样主张。', 'commentary', 'School-position comment after the closed quotation attributed to Ali; not part of his quoted report.'),
    1194: (585, '谢巴尼说', 'commentary', 'Explicit al-Shaybani legal commentary appended inside the numbered source paragraph.'),
    1219: (596, '注：', 'translator_note', 'Explicit translator/editor note appended inside the numbered source paragraph.'),
    1274: (631, '由此可见，宰牲节宰牲的人剃头属可佳行为。', 'commentary', 'Unattributed legal conclusion following the narrated account; report about Ibn Umar retained.'),
    1995: (958, '（穆圣说此话的意思是：', 'commentary', 'Explicit explanatory gloss after the closed Prophetic quotation.'),
}
INLINE_REMOVALS = {
    1235: (603, '（欧勒沃认为“古勒义”系净期，故第三次月经来潮时，则待婚期业已结束）',
           'commentary', 'Explanatory editorial parenthesis between two portions of the narrated account; both surrounding report portions retained.'),
}
UNNUMBERED_REPORT_INDEX = 1062
COMMENTARY_CONTINUATIONS = {
    204: 'Unnumbered Ibrahim legal/narrator discussion following report 107; separated from its Prophetic report rather than joined to the searchable hadith body.',
}
NOTE_CONTINUATIONS = {
    738: 'Second numbered item of the translator note begun in paragraph 737.',
    739: 'Third numbered item of the translator note begun in paragraph 737.',
    740: 'Fourth numbered item of the translator note begun in paragraph 737.',
    1864: 'Second item of the translator note begun in paragraph 1863.',
}

def load_paragraphs(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('This source-specific extractor requires the registered original DOCX checksum')
    with ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
        if root.findall('.//w:tbl', N):
            raise ValueError('Source now contains tables; review extraction order before import')
        body = root.find('w:body', N)
        paragraphs = []
        for i, para in enumerate(body.findall('w:p', N)):
            text = ''.join(x.text or '' for x in para.iter(W+'t'))
            style_el = para.find('w:pPr/w:pStyle', N)
            style = style_el.get(W+'val', '') if style_el is not None else ''
            paragraphs.append({'index': i, 'style': style, 'text': text})
        return paragraphs

def extract(path):
    paragraphs = load_paragraphs(path)
    if len(paragraphs) != 2067:
        raise ValueError('Paragraph count differs; source-specific decisions need review')
    records, ledger, annotations, books = [], [], [], []
    book = section = current = None
    positions = {}
    for p in paragraphs:
        i, text, style = p['index'], p['text'], p['style']
        segments = []
        def segment(kind, start=0, end=None, reason=None, record=None):
            end = len(text) if end is None else end
            s = {'kind': kind, 'start': start, 'end': end, 'text': text[start:end]}
            if reason: s['reason'] = reason
            if record is not None: s['recordId'] = record['id']
            segments.append(s)
            if kind in {'commentary', 'translator_note'}:
                annotations.append({'paragraphIndex': i, **s, 'book': book, 'section': section})
            return s
        if i <= 12:
            segment('front_matter')
        elif i >= 2059:
            segment('back_matter')
        elif style == 'Heading1':
            book = {'ordinal':len(books)+1, 'title':text, 'sourceParagraphIndex':i}
            books.append(book)
            section = None
            current = None
            segment('book_heading')
        elif style == 'Heading2':
            match = SUBSECTION.match(text)
            if not match: raise ValueError(f'Unknown internal subsection heading {i}: {text}')
            section = {'number':int(match.group(1)), 'title':match.group(2), 'raw':text, 'sourceParagraphIndex':i}
            current = None
            segment('section_heading')
        elif match := NUMBER.match(text):
            number = int(match.group(1))
            if number in positions: raise ValueError(f'Duplicate source number {number}')
            positions[number] = i
            current = {'id':f'muwatta-shaybani-zh-source-{number}', 'sourceNumber': number, 'sourceNumberStatus':'explicit', 'book':book, 'section':section, 'bodyParagraphs':[], 'sourceParagraphIndices':[i]}
            records.append(current)
            segment('source_number',0,match.end(),record=current)
            end=len(text)
            split = INLINE_SPLITS.get(i)
            if split:
                expected, marker, kind, reason = split
                if number!=expected or text.count(marker)!=1: raise ValueError(f'Inline split mismatch at {i}')
                end=text.index(marker)
            removal = INLINE_REMOVALS.get(i)
            if removal:
                expected, marker, kind, reason = removal
                if split or number != expected or text.count(marker) != 1:
                    raise ValueError(f'Inline removal mismatch at {i}')
                a = text.index(marker)
                b = a + len(marker)
                body = segment('report_text', match.end(), a, record=current)
                current['bodyParagraphs'].append({'paragraphIndex': i, 'start': body['start'], 'end': body['end'], 'text': body['text']})
                segment(kind, a, b, reason=reason, record=current)
                body = segment('report_text', b, end, record=current)
                current['bodyParagraphs'].append({'paragraphIndex': i, 'start': body['start'], 'end': body['end'], 'text': body['text']})
            else:
                body=segment('report_text',match.end(),end,record=current)
                current['bodyParagraphs'].append({'paragraphIndex':i,'start':body['start'],'end':body['end'],'text':body['text']})
            if split: segment(kind,end,reason=reason,record=current)
        elif i == UNNUMBERED_REPORT_INDEX:
            if text != '艾布·胡莱勒传述：穆圣说：“你们任何人不得在穆斯林弟兄的求婚之上求婚。”': raise ValueError('Unnumbered report changed')
            current = {'id':'muwatta-shaybani-zh-source-unnumbered-marriage-4','sourceNumber':None,'sourceNumberStatus':'unnumbered','book':book,'section':section,'bodyParagraphs':[],'sourceParagraphIndices':[i],'sourceNote':'The source prints no report number. It occurs between printed 527 and 529; no number is assigned and no canonical identity is inferred.'}
            records.append(current)
            body=segment('report_text',record=current)
            current['bodyParagraphs'].append({'paragraphIndex':i,'start':body['start'],'end':body['end'],'text':body['text']})
        elif i in SOURCE_CONTINUATIONS:
            expected,reason=SOURCE_CONTINUATIONS[i]
            if current is None or current['sourceNumber']!=expected: raise ValueError(f'Continuation mismatch {i}')
            body=segment('report_text',reason=reason,record=current)
            current['bodyParagraphs'].append({'paragraphIndex':i,'start':body['start'],'end':body['end'],'text':body['text'],'continuationReason':reason})
            current['sourceParagraphIndices'].append(i)
        elif i in COMMENTARY_CONTINUATIONS:
            segment('commentary',reason=COMMENTARY_CONTINUATIONS[i],record=current)
        elif i in NOTE_CONTINUATIONS:
            segment('translator_note',reason=NOTE_CONTINUATIONS[i],record=current)
        elif re.match(r'^(?:穆罕默德·本·哈桑·)?谢巴尼说',text):
            segment('commentary',reason='Explicit separate al-Shaybani commentary paragraph.',record=current)
        elif text.startswith('注'):
            segment('translator_note',reason='Explicit separate translator/editor note paragraph.',record=current)
        else:
            raise ValueError(f'Unclassified paragraph {i}: {text[:120]}')
        if ''.join(s['text'] for s in segments)!=text:
            raise AssertionError(f'Exact reconstruction failed at {i}')
        if any(s['start'] != (segments[j-1]['end'] if j else 0) for j,s in enumerate(segments)) or segments[-1]['end']!=len(text):
            raise AssertionError(f'Coverage gap/overlap at {i}')
        ledger.append({**p,'segments':segments})
    for r in records:
        parts = r['bodyParagraphs']
        r['text'] = ''.join(('\n\n' if j and part['paragraphIndex'] != parts[j-1]['paragraphIndex'] else '') + part['text']
                            for j, part in enumerate(parts))
    missing=[n for n in range(1,1009) if n not in positions]
    if missing!=[196,528,764] or len(records)!=1006: raise AssertionError('Unexpected source coverage')
    kinds=Counter(s['kind'] for p in ledger for s in p['segments'])
    char_counts=Counter()
    for p in ledger:
        for s in p['segments']: char_counts[s['kind']]+=len(s['text'])
    book_counts=[]
    for b in books:
        rs=[r for r in records if r['book']['ordinal']==b['ordinal']]
        book_counts.append({**b,'reportCount':len(rs),'explicitlyNumberedCount':sum(r['sourceNumber'] is not None for r in rs),'firstPrintedNumber':next((r['sourceNumber'] for r in rs if r['sourceNumber'] is not None),None),'lastPrintedNumber':next((r['sourceNumber'] for r in reversed(rs) if r['sourceNumber'] is not None),None)})
    audit={
        'sourceFile':path.name,'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'sourceBytes':path.stat().st_size,
        'extraction':'Native DOCX paragraph text with styles; no OCR performed for this import. Upstream transcription method is not established by this file.',
        'titleChinese':paragraphs[0]['text'],'titleEnglish':'Muwatta of Imam Malik — al-Shaybani recension',
        'compilerCredit':paragraphs[1]['text'],'translatorCredit':paragraphs[10]['text'],'translatorDate':paragraphs[11]['text'],
        'recensionEvidenceParagraphIndices':[8,9],
        'paragraphCount':len(paragraphs),'paragraphScope':'Top-level document-body paragraphs; no tables, footnotes, or endnotes are present.', 'sourceCharacterCount':sum(len(p['text']) for p in paragraphs),
        'pageFurniture':{'word/header1.xml':'穆宛塔圣训集','word/header2.xml':'','word/footer1.xml':'PAGE field with displayed value 1','word/footer2.xml':''},
        'reportCount':len(records),'explicitlyNumberedReports':len(positions),'unnumberedReports':1,'printedNumberRange':[1,1008],
        'missingPrintedNumbers':missing,'unfilledSourceGaps':[196,764],
        'unnumberedReport':{'paragraphIndex':1062,'printedPredecessor':527,'printedSuccessor':529,'assignedNumber':None},
        'bookCount':len(books),'subsectionCount':kinds['section_heading'],'segmentCounts':dict(kinds),'segmentCharacterCounts':dict(char_counts),
        'exactParagraphReconstructionVerified':True,'allParagraphsClassified':True,'inlineSeparations':[{ 'paragraphIndex':i,'sourceNumber':s[0],'marker':s[1],'kind':s[2],'reason':s[3]} for i,s in sorted({**INLINE_SPLITS, **INLINE_REMOVALS}.items())],
        'continuationDecisions':[{ 'paragraphIndex':i,'sourceNumber':s[0],'reason':s[1]} for i,s in SOURCE_CONTINUATIONS.items()],
        'books':book_counts,
        'cautions':[
            'Source numbers belong to this Chinese al-Shaybani recension. Do not use as canonical Yahya recension or Sunnah.com IDs.',
            'Numbered material includes Prophetic reports, Companion reports, Successor statements, and legal material. Do not uniformly label every item as a direct saying of the Prophet.',
            'No source numbers, spelling, punctuation, OCR-like anomalies, names, or doctrinal wording have been silently corrected.',
            'Editorial and legal-school statements in preface, commentary, and translator notes are excluded from report bodies, and preserved exactly in the raw ledger and downloadable DOCX.',
            'Small parenthetical translations inside numbered reports remain verbatim unless explicitly marked as a translator note.',
            'The apparent missing source slot 528 has an unnumbered report; it is not assigned 528 without a second source.'
        ]
    }
    assert sum(char_counts.values())==audit['sourceCharacterCount']
    return {'audit':audit,'reports':records,'annotations':annotations,'paragraphLedger':ledger}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('--out-dir',type=Path,default=Path('muwatta-source-review'))
    args=parser.parse_args()
    result=extract(args.source)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    for name,data in result.items():
        (args.out_dir/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['audit'],ensure_ascii=False,indent=2))

if __name__=='__main__': main()
