#!/usr/bin/env python3
"""Apply the supplied RFC6902 test/add/replace patch without changing its input."""
import argparse, copy, hashlib, json
from pathlib import Path

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def parts(pointer):
    if pointer == '': return []
    if not pointer.startswith('/'): raise ValueError('Invalid JSON pointer')
    return [x.replace('~1','/').replace('~0','~') for x in pointer[1:].split('/')]
def resolve(doc,path):
    cur=doc
    for key in parts(path): cur=cur[int(key)] if isinstance(cur,list) else cur[key]
    return cur
def apply_patch(doc, patch):
    out=copy.deepcopy(doc)
    for i,item in enumerate(patch):
        op=item['op']; path=item['path']
        if op=='test':
            if resolve(out,path)!=item['value']: raise ValueError(f'Test failed at operation {i}, {path}')
            continue
        if op not in {'add','replace'}: raise ValueError(f'Unsupported operation {op}')
        ps=parts(path)
        if not ps: out=copy.deepcopy(item['value']); continue
        parent=out
        for key in ps[:-1]: parent=parent[int(key)] if isinstance(parent,list) else parent[key]
        key=ps[-1]
        if isinstance(parent,list):
            if op=='add': parent.insert(len(parent) if key=='-' else int(key), copy.deepcopy(item['value']))
            else: parent[int(key)]=copy.deepcopy(item['value'])
        else:
            if op=='replace' and key not in parent: raise KeyError(path)
            if op=='add' and key in parent: raise ValueError('Refuse to overwrite an existing added field: '+path)
            parent[key]=copy.deepcopy(item['value'])
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--patch',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expected-input-sha256')
    a=p.parse_args()
    if a.input.resolve()==a.output.resolve(): p.error('Output must differ from original input.')
    data=a.input.read_bytes()
    actual=hashlib.sha256(data).hexdigest()
    if a.expected_input_sha256 and actual!=a.expected_input_sha256: raise ValueError('Input SHA256 mismatch')
    out=apply_patch(json.loads(data),read(a.patch))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(a.output),'size_bytes':a.output.stat().st_size,
                      'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'input_unchanged_sha256':actual}))
if __name__=='__main__': main()
