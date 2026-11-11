#!/usr/bin/env python3
"""Search the staged source occurrences without discarding review warnings."""
from pathlib import Path
import argparse,json,unicodedata

def fold(value):
    value=value.casefold().replace('đ','d')
    return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--query',default='')
    p.add_argument('--book',choices=['bukhari','muslim','abu-dawud','200-golden-hadith'])
    p.add_argument('--number',help='Exact source label or local number; not a canonical crosswalk')
    p.add_argument('--source',help='Source filename or SHA prefix')
    p.add_argument('--ai-status',choices=['false','unknown','true'])
    p.add_argument('--limit',type=int,default=20)
    p.add_argument('--full',action='store_true')
    p.add_argument('--data',type=Path,default=Path(__file__).resolve().parent.parent/'vietnamese-hadith-bank.jsonl')
    a=p.parse_args();needle=fold(a.query);n=0
    with a.data.open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line)
            if a.book and r['book']['id']!=a.book:continue
            if a.number and a.number not in [r['number']['in_book'],r['number']['printed_label'],r['number'].get('printed_reference')]:continue
            if a.source and a.source not in r['source']['sha256'] and fold(a.source) not in fold(r['source']['file']):continue
            status='false' if r['ai_translation'] is False else 'true' if r['ai_translation'] is True else 'unknown'
            if a.ai_status and status!=a.ai_status:continue
            hay=' '.join([r['search']['translation'],r['search']['source_reference'],r['search']['chapter'],r['narrator']['verbatim'] or ''])
            if needle and needle not in fold(hay):continue
            result=r if a.full else {'id':r['id'],'book':r['book']['title'],'number':r['number']['printed_label'],
                'translation':r['text']['translation'],'reference':r['references']['translation'],'source_file':r['source']['file'],
                'pdf_pages':r['page']['pdf'],'printed_pages':r['page']['printed'],'ai_translation':r['ai_translation'],
                'review_status':r['review']['status'],'warnings':r['review']['issues']}
            print(json.dumps(result,ensure_ascii=False));n+=1
            if a.limit>0 and n>=a.limit:break
    if n==0:print(json.dumps({'matches':0,'query':a.query},ensure_ascii=False))

if __name__=='__main__':main()
