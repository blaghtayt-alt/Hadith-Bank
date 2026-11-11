#!/usr/bin/env python3
"""Search the Japanese Sahih Muslim candidate without third-party dependencies."""
import argparse,json,re,unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'languages/ja/books/muslim/editions/pdf-c859ce57c211ea1b/records.json'

def norm(s):
    # Search view only. Canonical source text is never rewritten.
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',s or '')).casefold()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('query',nargs='?',default='')
    p.add_argument('--records',type=Path,default=DEFAULT)
    p.add_argument('--id',dest='record_id')
    p.add_argument('--narrator')
    p.add_argument('--section')
    p.add_argument('--pdf-page',type=int)
    p.add_argument('--record-type',choices=['narration','variant_occurrence','variant_reference'])
    p.add_argument('--has-report-text',action='store_true',help='Exclude abbreviated route-reference records')
    p.add_argument('--text-only',action='store_true',help='Search only the Japanese narration text, excluding headings and notes')
    p.add_argument('--limit',type=int,default=10)
    p.add_argument('--full',action='store_true',help='Return complete record objects')
    a=p.parse_args()
    if a.limit<0:p.error('--limit must be nonnegative; zero means all matches')
    if a.records.suffix=='.jsonl':
        rows=[json.loads(l) for l in a.records.read_text(encoding='utf8').splitlines() if l.strip()]
    else:rows=json.loads(a.records.read_text(encoding='utf8'))
    matches=[]
    for r in rows:
        if a.record_id and r['id']!=a.record_id:continue
        if a.narrator and norm(a.narrator) not in norm(r['narrator'].get('verbatim') or r['narrator'].get('name')):continue
        if a.section and norm(a.section) not in norm((r['book'].get('chapter') or '')+(r['book'].get('section') or '')):continue
        if a.pdf_page and a.pdf_page not in r['page']['pdf']:continue
        if a.record_type and r['record_type']!=a.record_type:continue
        if a.has_report_text and r['record_type']=='variant_reference':continue
        hay=r['text']['translation'] or ''
        if not a.text_only:
            hay+=' '+r['source_unit_text_verbatim']+' '+(r['book'].get('chapter') or '')+' '+(r['book'].get('section') or '')
        if a.query and norm(a.query) not in norm(hay):continue
        matches.append(r)
    selected=matches[:a.limit] if a.limit else matches
    out=selected if a.full else [{
        'id':r['id'],'record_type':r['record_type'],'section':r['book']['section_display'],
        'narrator_attribution':r['narrator']['name'],'pdf_pages':r['page']['pdf'],
        'printed_reference':r['page']['printed'],'printed_reference_scope':'section',
        'ai_translation':False,'review_status':r['review']['status'],
        'text_preview':r['text']['translation'][:420]
    } for r in selected]
    print(json.dumps({'matches':len(matches),'returned':len(out),'records':out},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
