#!/usr/bin/env python3
"""Reproduce the candidate from the exact source PDF and frozen boundary ledger."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parents[1]
EXPECTED='c859ce57c211ea1bfddb98b268241da25fe077782dd4d6be4cd9e10628b18d6a'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output-dir',type=Path,required=True,help='New or empty local directory for reproducible work')
    a=p.parse_args();root=a.root.resolve();out=a.output_dir.resolve()
    if out.exists() and any(out.iterdir()):raise SystemExit('Output directory must be new or empty; existing work is not overwritten.')
    out.mkdir(parents=True,exist_ok=True)
    pdf=root/'sources/ja-muslim-web.pdf'
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=EXPECTED:raise SystemExit('Source PDF SHA256 mismatch.')
    work=out/'work';(work/'pdf').mkdir(parents=True)
    (work/'metadata-review').mkdir()
    shutil.copyfile(root/'source.json',work/'metadata-review/source-metadata-evidence.json')
    shutil.copyfile(root/'evidence/boundary-overrides.json',work/'boundary-overrides.json')
    pages=[];lines=[]
    doc=fitz.open(pdf)
    for pn,page in enumerate(doc,1):
        pages.append({'pdf_page':pn,'text':page.get_text()})
        offset=0;li=0
        for bi,b in enumerate(page.get_text('dict')['blocks']):
            if 'lines' not in b:continue
            for line in b['lines']:
                t=''.join(s['text'] for s in line['spans']);li+=1
                item={'id':f'p{pn:04d}-l{li:03d}','pdf_page':pn,'line_index':li,'text':t,
                      'bbox':[round(v,4) for v in line['bbox']],
                      'fonts':sorted(set(s['font'] for s in line['spans'])),
                      'max_font_size':max(s['size'] for s in line['spans']),
                      'block_index':bi,'page_char_start':offset}
                offset+=len(t)+1;lines.append(item)
    (work/'pdf/raw-pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf8')
    (work/'pdf/lines.json').write_text(json.dumps(lines,ensure_ascii=False,indent=2),encoding='utf8')
    (work/'pdf/lines.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in lines),encoding='utf8')
    for script in ['segment_pdf.py','build_records.py']:
        subprocess.run([sys.executable,str(root/'scripts'/script),'--work-dir',str(work)],check=True)
    results=[]
    for filename in ['records.json','records.jsonl']:
        generated=work/'intake'/filename
        reference=root/'languages/ja/books/muslim/editions/pdf-c859ce57c211ea1b'/filename
        actual=hashlib.sha256(generated.read_bytes()).hexdigest();expected=hashlib.sha256(reference.read_bytes()).hexdigest()
        shutil.copyfile(generated,out/filename)
        results.append({'file':filename,'generated_sha256':actual,'package_sha256':expected,'identical':actual==expected})
    report={'source_sha256':EXPECTED,'pymupdf_version':fitz.VersionBind,'files':results,'passed':all(r['identical'] for r in results)}
    (out/'rebuild-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
