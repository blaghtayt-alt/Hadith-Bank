#!/usr/bin/env python3
"""Reproduce the package's structural/integrity checks; this is not textual QC."""
from pathlib import Path
from collections import Counter
import argparse,json,hashlib,sys

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    ap.add_argument('--source-pages',action='store_true',help='Also compare every saved native page text with the included PDF using PyMuPDF')
    ap.add_argument('--output',type=Path);a=ap.parse_args();root=a.root
    manifest=load(root/'manifest.json');sources=load(root/'catalog/sources.json');records=load(root/'vietnamese-hadith-bank.json')
    errors=[];checks=Counter();ids=set();sourcebyid={s['source_id']:s for s in sources};lineindexes={};source_records={}
    from jsonschema import Draft202012Validator
    validator=Draft202012Validator(load(root/'schemas/attachment.record.schema.json'))
    for s in sources:
        f=root/s['package_file']
        if not f.exists() or sha(f)!=s['sha256']:errors.append('source hash mismatch: '+s['source_id'])
        checks['source_pdf_hashes']+=1
        rows=load(root/s['records_file']);source_records[s['source_id']]={r['id']:r for r in rows}
        if len(rows)!=s['record_count']:errors.append('source record count mismatch: '+s['source_id'])
        ev=[json.loads(x) for x in (root/s['page_evidence']).read_text().splitlines()]
        if len(ev)!=s['pdf_pages'] or [p['pdf_page'] for p in ev]!=list(range(1,s['pdf_pages']+1)):errors.append('page coverage mismatch: '+s['source_id'])
        checks['source_pages_present']+=len(ev)
        if s['line_evidence'].endswith('lines.jsonl'):
            lines=[json.loads(x) for x in (root/s['line_evidence']).read_text().splitlines()]
        else:lines=[l for p in ev for l in p['lines']]
        lineindexes[s['source_id']]={l.get('line_id',l.get('id')):l for l in lines}
        if a.source_pages:
            import fitz
            with fitz.open(f) as doc:
                if len(doc)!=len(ev):errors.append('actual PDF page count mismatch: '+s['source_id'])
                for p,page in zip(ev,doc):
                    native=p.get('raw_text',p.get('text_native'))
                    if native!=page.get_text():errors.append('native page text mismatch: '+s['source_id']+':'+str(p['pdf_page']))
                    checks['native_page_texts_compared']+=1
    for r in records:
        if r['id'] in ids:errors.append('duplicate occurrence ID: '+r['id'])
        ids.add(r['id'])
        for e in validator.iter_errors(r):errors.append('schema '+r['id']+':'+str(list(e.path))+':'+e.message)
        checks['schema_records']+=1
        if not r['text']['translation'].strip():errors.append('empty translation: '+r['id'])
        if r['text']['arabic'] is not None or r['number']['canonical'] is not None:errors.append('unverified canonical field populated: '+r['id'])
        if r['review']['release_eligible'] or r['review']['independent_pro_qc']!='pending':errors.append('review state changed: '+r['id'])
        s=sourcebyid[r['source']['source_id']]
        if source_records[s['source_id']].get(r['id'])!=r:errors.append('aggregate/edition mismatch: '+r['id'])
        if r['provenance']['source_anchor_line_id'] not in lineindexes[s['source_id']]:errors.append('unresolved anchor: '+r['id'])
        for kind,spans in r['provenance']['source_spans'].items():
            for span in spans:
                line=lineindexes[s['source_id']].get(span['line_id'])
                if not line or line['pdf_page']!=span['pdf_page']:errors.append('unresolved record span: '+r['id']+':'+span['line_id'])
                checks['record_spans_resolved']+=1
        if any(not 1<=p<=s['pdf_pages'] for p in r['page']['pdf']):errors.append('page out of range: '+r['id'])
        payload={'translation':r['text']['translation'],'arabic_embedded_raw':r['source_text']['arabic_embedded_raw']}
        h=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if h!=r['provenance']['text_payload_sha256']:errors.append('text payload hash mismatch: '+r['id'])
        checks['text_payload_hashes']+=1
    streamed=[json.loads(line) for line in (root/'vietnamese-hadith-bank.jsonl').read_text().splitlines()]
    if streamed!=records:errors.append('JSON/JSONL aggregate mismatch')
    if len(records)!=manifest['record_count']:errors.append('manifest count mismatch')
    result={'status':'passed' if not errors else 'failed','checks':dict(checks),'record_count':len(records),'unique_occurrence_ids':len(ids),'source_files':len(sources),
        'source_pages':sum(s['pdf_pages'] for s in sources),'errors':errors,'full_character_fidelity_review':False,'independent_pro_final_review':'pending',
        'scope':'mechanical schema, identity, source bytes, locators, text preservation and optional native page extraction; not authenticity or complete visual QC'}
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errors:sys.exit(1)

if __name__=='__main__':main()
