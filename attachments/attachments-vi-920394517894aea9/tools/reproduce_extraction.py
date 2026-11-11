#!/usr/bin/env python3
from pathlib import Path
import argparse,json,shutil,subprocess,sys,hashlib

def main():
    ap=argparse.ArgumentParser(description="Re-run source extraction in a new directory; does not modify delivered records.")
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve()
    if out.exists() and any(out.iterdir()):raise SystemExit('Output directory must be new or empty.')
    root=Path(__file__).resolve().parent.parent
    shutil.copytree(root/'reproduction',out,dirs_exist_ok=True)
    inv=json.loads((root/'reports/input-inventory.json').read_text());catalog=json.loads((root/'catalog/sources.json').read_text())
    bysha={s['sha256']:s for s in catalog}
    for source in inv['files']:
        target=out/'source-extracted'/source['archive_member'];target.parent.mkdir(parents=True,exist_ok=True)
        original=root/bysha[source['sha256']]['package_file']
        if hashlib.sha256(original.read_bytes()).hexdigest()!=source['sha256']:raise RuntimeError('Source hash mismatch')
        shutil.copyfile(original,target);source['local_path']=str(target)
    (out/'source-inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
    for relative in ['root-extraction/extract_bukhari_anthology.py','agent-muslim/extract_muslim.py','agent-muslim/decode_muslim_numbers.py','agent-muslim/validate_muslim.py','agent-abudawud/extract_abudawud.py','agent-abudawud/finalize_abudawud.py']:
        subprocess.run([sys.executable,str(out/relative)],cwd=out,check=True)
    print('Extraction outputs are in the three source-specific extracted directories. The delivered bank JSON has not been changed.')

if __name__=='__main__':main()
