#!/usr/bin/env python3
"""Recheck source coverage and character-exact extraction against original OOXML."""
from pathlib import Path
from lxml import etree as E
import hashlib, json, zipfile, collections, re
from extract_bukhari import NUMBER, EXPECTED_COUNTS, strip_terminal_citation

BASE=Path(__file__).resolve().parent
INPUT=BASE.parents[1]/'upload'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def readl(name): return [json.loads(l) for l in (BASE/name).read_text(encoding='utf-8').splitlines()]
def digest(t):return hashlib.sha256(t.encode('utf-8')).hexdigest()
def remove_number(t):return NUMBER.sub('',t,count=1)

def main():
    all_primary=readl('primary_records.jsonl')
    main=readl('hadith_only_primary_records.jsonl')
    variants=readl('variant_records.jsonl')
    quotes=readl('explicit_hadith_quotation_records.jsonl')
    references=readl('reference_only_positions.jsonl')
    ledger=readl('coverage_ledger.jsonl')
    archives={v:json.loads((BASE/f'volume{v}.source-archive.json').read_text(encoding='utf-8')) for v in range(1,7)}
    raw_body_checks=0; raw_footnote_checks=0
    for path in sorted(INPUT.glob('faiz*.docx')):
        v=int(path.name.split('bokhari-')[1][0]); arc=archives[v]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==arc['source_sha256']
        with zipfile.ZipFile(path) as z:
            root=E.fromstring(z.read('word/document.xml'))
            ps=root.xpath('//w:body//w:p',namespaces=NS)
            assert len(ps)==len(arc['body'])
            for n,p in zip(ps,arc['body']):
                assert ''.join(n.xpath('.//w:t/text()',namespaces=NS))==p['raw_w_t']
                assert digest(p['text'])==p['text_sha256']
                raw_body_checks+=1
            fr=E.fromstring(z.read('word/footnotes.xml'))
            fs=[f for f in fr.xpath('./w:footnote',namespaces=NS) if int(f.get('{'+NS['w']+'}id'))>0]
            assert len(fs)==len(arc['footnotes'])
            for f,af in zip(fs,arc['footnotes']):
                assert f.get('{'+NS['w']+'}id')==af['id']
                ns=f.xpath('.//w:p',namespaces=NS)
                assert len(ns)==len(af['paragraphs'])
                for n,p in zip(ns,af['paragraphs']):
                    assert ''.join(n.xpath('.//w:t/text()',namespaces=NS))==p['raw_w_t']
                    assert digest(p['text'])==p['text_sha256']
                    raw_footnote_checks+=1
        assert len([r for r in all_primary if r['source_volume']==v])==EXPECTED_COUNTS[v]
    ids=[r['id'] for r in main+variants+quotes]
    assert len(ids)==len(set(ids)), 'Duplicate integration ID'
    assert len(all_primary)==2230 and len(main)==2225 and len(references)==5 and len(variants)==2
    assert len(ledger)==raw_body_checks+raw_footnote_checks
    for r in all_primary+variants:
        a=archives[r['source_volume']]['body']
        for language,key in [('arabic','arabic'),('translation','translation')]:
            ps=[a[i] for i in r['source_paragraphs'][key]]
            expected='\n'.join(p['display_text'] for p in ps) or None
            raw='\n'.join(p['text'] for p in ps) or None
            if r in all_primary:
                expected=remove_number(expected) if expected else None
                raw=remove_number(raw) if raw else None
            if language=='arabic':expected,_=strip_terminal_citation(expected,json.loads(json.dumps(r['references'])))
            assert r['text'][language]==expected, (r['id'],language,'decoded content')
            assert r['raw_text'][language]==raw, (r['id'],language,'raw content')
        assert r.get('commentary') is None and not r['footnotes']
    for r in quotes:
        assert r.get('commentary') is None and not r['footnotes']
        assert not any(k in r for k in ['full_source_paragraph','context_before']), 'Commentary context leaked to integration'
        assert r['text'].get('arabic') or r['text'].get('translation')
        for language in ['arabic','translation']:
            if r['raw_text'].get(language) is None:continue
            loc=r['source_locator']
            if language=='translation' and r.get('aligned_translation_locator'):loc=r['aligned_translation_locator']
            arc=archives[r['source_volume']]
            if loc['part']=='word/document.xml':p=arc['body'][loc['paragraph_index']]
            else:p=next(f for f in arc['footnotes'] if f['id']==loc['footnote_id'])['paragraphs'][loc['paragraph_index']]
            a,b=loc['start'],loc['end'];raw=p['text'][a:b]
            assert r['raw_text'][language]==raw,(r['id'],language,'quote raw span')
            expected=raw
            for tr in reversed(p['display_normalization']):
                if a<=tr['offset'] and tr['offset']+len(tr['raw'])<=b:
                    k=tr['offset']-a;expected=expected[:k]+tr['display']+expected[k+len(tr['raw']):]
            assert r['text'][language]==expected,(r['id'],language,'quote decoded span')
        if r['grade']:
            loc=r['grade']['source_locator'];arc=archives[r['source_volume']]
            p=next(f for f in arc['footnotes'] if f['id']==loc['footnote_id'])['paragraphs'][loc['paragraph_index']]
            assert p['text'][loc['start']:loc['end']]==r['grade']['evidence_text']
    roles=collections.Counter(x['role'] for x in ledger)
    per_volume=[]
    for v in range(1,7):
        per_volume.append({'volume':v,'source_positions':EXPECTED_COUNTS[v],
            'hadith_text_positions':sum(r['source_volume']==v for r in main),
            'reference_only_positions':sum(r['source_volume']==v for r in references),
            'fragments':sum(r['source_volume']==v and r['content_kind']=='source_fragment' for r in main),
            'unnumbered_variants':sum(r['source_volume']==v for r in variants),
            'hadith_quotation_excerpts':sum(r['source_volume']==v for r in quotes),
            'body_paragraphs':len(archives[v]['body']),
            'commentary_footnotes_excluded':len(archives[v]['footnotes'])})
    result={'passed':True,'input_document_count':6,'raw_body_paragraphs_rechecked':raw_body_checks,
        'raw_footnote_paragraphs_rechecked':raw_footnote_checks,'ledger_entries_rechecked':len(ledger),
        'primary_source_positions':len(all_primary),'hadith_text_positions':len(main),
        'reference_only_positions_excluded':len(references),'unnumbered_variants':len(variants),
        'explicit_hadith_quotation_excerpts':len(quotes),'integration_record_count':len(ids),
        'all_integration_ids_unique':True,'all_integration_comments_empty':True,
        'all_ancillary_quotes_match_exact_source_spans':True,
        'per_volume':per_volume,'source_coverage_roles':dict(roles),
        'printed_source_defects_preserved':True,'canonical_references_independently_validated':False,
        'source_integrity_scope':'Original DOCX hashes, every body/footnote paragraph raw w:t bytes and hashes; canonical main/variant text exactly reconstructs selected source paragraphs plus recorded font decoding/footnote-anchor removal. No assertion of exhaustive interpretation or independent hadith authenticity grading.'}
    (BASE/'validation_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
