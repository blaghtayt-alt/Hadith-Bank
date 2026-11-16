#!/usr/bin/env python3
"""Portable private rebase proof; production Node and Python APIs, no mocks/shims.

Run from any directory:
  python proof/replay_real_callers.py --out <directory> [--baseline <pinned-main-dir>]

Uses exactly the supplied 14 full Hindi records and actual ordinary PT6/DE3 rows.
No GitHub/network, PDF, database or public registration is necessary.
"""
import argparse
import collections
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/software_rebase'
sys.path.insert(0,str(ROOT/'scripts'))
from build_reader import write_lazy_reader_shards, validate_record, markdown_record
from bank_discovery import expected_discovery_row, expected_discovery_segments
from language_display import language_readings
from build_discovery import render_language_reading
from source_uncertainty_notes import validated_parts, checked_source_identity

sha=lambda x:hashlib.sha256(x).hexdigest()
compact=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n'

def require(condition, message):
    if not condition:raise AssertionError(message)

def run_node(records,code_root):
    cmd=['node',str(code_root/'scripts/reader_projection.js'),str(code_root/'reader/template.html')]
    proc=subprocess.run(cmd,input=records,capture_output=True,timeout=45)
    return proc

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'proof-output');parser.add_argument('--baseline',type=Path,default=None)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    fixture_manifest=json.loads((FIX/'FIXTURE_HASHES.json').read_text())
    for name,meta in fixture_manifest['files'].items():
        payload=(FIX/name).read_bytes()
        require(len(payload)==meta['bytes'] and sha(payload)==meta['sha256'],
                'portable fixture hash mismatch: '+name)
    records=json.loads((FIX/'hindi-fourteen.json').read_text(encoding='utf-8'))
    require(len(records)==14,'14 exact Hindi records required')
    raw=b''.join(compact(r).encode('utf8') for r in records)
    phases={};counts=collections.Counter()
    for r in records:
        checked_source_identity(r,r['source_uncertainty_projection']);validate_record(r,r['id']);
        parts=validated_parts(r['text_translation'],r['source_uncertainty_projection'],record_id=r['id'])
        counts.update(x['kind'] for x in r['source_uncertainty_projection']['annotations'])
        views=language_readings(r)
        selected=[v for v in views if 'source_uncertainty_parts' in v]
        require(len(selected)==1 and selected[0]['primary'],'source scope must be one primary')
        static=render_language_reading(selected[0],r);markdown=markdown_record(r,1)
        require('⟦' not in static and '⟦' not in markdown,'unreviewed audit marker in visible body')
        require('(OCR wasn’t clear)' in static and '(OCR wasn’t clear)' in markdown,'separate OCR note missing')
        preview=expected_discovery_row(r,0)
        require(preview['sourceUncertainty'] is True,'source uncertainty index binding missing')
        require(all('⟦' not in reading['text'] for reading in preview['readings']),'raw audit marker in compact source preview')
    require(counts=={'accepted_uncertain_reading':15,'unfilled_source_gap':1,'unreviewed_source_gap':2},'closed annotation count changed')
    phases['source_controls']={'count':len(records),'annotations':dict(counts),'raw_full_record_jsonl_sha256':sha(raw),'records_sha256':[sha(compact(r).encode()) for r in records]}
    node=run_node(raw,ROOT);require(node.returncode==0,'real Node projector failed: '+node.stderr.decode(errors='replace')[:600]);
    (args.out/'actual14-node-projection.jsonl').write_bytes(node.stdout)
    projected=[json.loads(x) for x in node.stdout.decode().splitlines()]
    require(len(projected)==14,'Node projector did not return 14 lines')
    offset=0
    for i,(r,x) in enumerate(zip(records,projected)):
        length=len(compact(r).encode())
        require(x[0]==i and x[1]['_reader']['detail']==[offset,length],'index/byte detail span misaligned')
        require(all(x[1][k]==r[k] for k in ('id','language','book_key','edition','source_id')),'Node identity drift')
        require('⟦' not in x[2],'audit marker in Node search stream');offset+=length
    require(offset==len(raw),'Node detail offsets do not span exact source JSONL')
    phases['real_node_projection']={'records':14,'stdout_sha256':sha(node.stdout),'raw_span_bytes':len(raw),'stderr':node.stderr.decode(errors='replace')[:200]}
    with tempfile.TemporaryDirectory(prefix='portable-rebase-builder-',dir=str(args.out)) as tmp:
        work=Path(tmp);output=work/'reader.html';data=work/'reader-data'
        m=write_lazy_reader_shards(records,output,data,max_shard_bytes=65536,template_path=ROOT/'reader/template.html',publish=True)
        require(m['record_count']==14 and m['jsonl_sha256']==sha(raw),'Python manifest source digest mismatch')
        require(json.loads((data/'manifest.json').read_text())==m,'published manifest differs from return value')
        stores={};parts={}
        for name in ('details','directory','search','annotations'):
            data_bytes=b'';pieces=[]
            for s in m[name]['shards']:
                p=work/s['path']; gz=p.read_bytes();plain=gzip.decompress(gz)
                require(sha(gz)==s['sha256'] and len(gz)==s['bytes'],'gzip hash/size mismatch: '+name)
                require(len(plain)==s['uncompressed_bytes'] and plain.count(b'\n')==s['count'],'gzip source line count mismatch')
                require(len(gz)<=m['max_shard_bytes'],'oversized gzip shard')
                data_bytes+=plain
                saved=args.out/'actual-lazy-store-shards'/s['path']
                saved.parent.mkdir(parents=True,exist_ok=True)
                saved.write_bytes(gz)
                pieces.append({'path':s['path'],'sha256':sha(gz),'bytes':len(gz),'uncompressed_bytes':len(plain)})
            require(sha(data_bytes)==m[name]['jsonl_sha256'],'concatenated store hash mismatch: '+name)
            stores[name]=data_bytes;parts[name]=pieces
            (args.out/('actual-'+name+'-source-stream.jsonl')).write_bytes(data_bytes)
        require(stores['details']==raw,'exact full 14 Hindi details modified')
        for name,wanted in {'directory':[x[1] for x in projected],
                            'search':[[x[0],x[2]] for x in projected],
                            'annotations':[[x[0],x[3]] for x in projected]}.items():
            require([json.loads(x) for x in stores[name].decode().splitlines()]==wanted,'Python/Node stream discrepancy: '+name)
        (args.out/'actual14-reader-manifest.json').write_text(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
        phases['real_python_lazy_builder']={'record_count':14,'raw_detail_sha256':sha(stores['details']),
                     'shard_sha256_by_store':{name:sha(value) for name,value in stores.items()},
                     'actual_gzip_shards':parts,'source_audit_markers_in_detail':b'\xe2\x9f\xa6' in stores['details'],
                     'raw_audit_tokens_in_search':b'\xe2\x9f\xa6' in stores['search'],
                     'module_shim_used':False,'full_record_detail_bytes_exact':True}
    negative=[]
    base=next(r for r in records if r['id']=='HI-MSB-V1-P0374-N0434')
    for kind in ('coherent_body_rehash','held_U014_promotion','parent_id_change','text_record_id','issue_id_change','span_mutation','missing_annotations'):
        r=copy.deepcopy(base)
        if kind=='coherent_body_rehash':
            r['text_translation']='X'+r['text_translation'][1:]
            r['source_uncertainty_projection']['expected_body_sha256']=sha(r['text_translation'].encode())
        elif kind=='held_U014_promotion':
            a=next(a for a in r['source_uncertainty_projection']['annotations'] if a['kind']=='unreviewed_source_gap');a['kind']='unfilled_source_gap'
        elif kind=='parent_id_change':r['id']='forged-id';r['source_uncertainty_projection']['record_id']='forged-id'
        elif kind=='text_record_id':r['source_uncertainty_projection']['text_record_id']='forged-text-id'
        elif kind=='issue_id_change':r['source_uncertainty_projection']['annotations'][0]['issue_id']='forged-issue'
        elif kind=='span_mutation':r['source_uncertainty_projection']['annotations'][0]['start']+=1
        elif kind=='missing_annotations':r['source_uncertainty_projection']['annotations']=[]
        one=run_node(compact(r).encode(),ROOT)
        require(one.returncode!=0,'Node accepted tampered Hindi control: '+kind)
        try:
            validate_record(r,r['id'])
        except (ValueError,TypeError):pass
        else:raise AssertionError('Python validate_record accepted tampered Hindi control: '+kind)
        negative.append({'kind':kind,'node_exit':one.returncode,'node_error':one.stderr.decode(errors='replace').strip()[:280],'python':'REJECT'})
    # The full Python lazy builder, not only its validator, must fail before
    # publishing a manifest for coherent source-body or review-status attacks.
    python_negative=[]
    for name in ('coherent_body_rehash','held_U014_promotion'):
        record=copy.deepcopy(base)
        if name=='coherent_body_rehash':
            record['text_translation']='X'+record['text_translation'][1:]
            record['source_uncertainty_projection']['expected_body_sha256']=sha(record['text_translation'].encode())
        else:
            next(x for x in record['source_uncertainty_projection']['annotations'] if
                 x['kind']=='unreviewed_source_gap')['kind']='unfilled_source_gap'
        with tempfile.TemporaryDirectory(prefix='rebase-negative-',dir=str(args.out)) as tmp:
            work=Path(tmp);target=work/'reader.html';parts=work/'reader-data'
            try:
                write_lazy_reader_shards([record],target,parts,max_shard_bytes=65536,
                                         template_path=ROOT/'reader/template.html',publish=True)
            except (ValueError,TypeError,RuntimeError,subprocess.CalledProcessError):
                require(not (parts/'manifest.json').exists(),
                        'tampered Python source produced a published manifest')
                python_negative.append({'kind':name,'builder':'REJECT','published_manifest':False})
            else:raise AssertionError('actual Python builder accepted '+name)
    phases['negative_controls']={'rejections':negative,'total':len(negative),
                                 'actual_python_builder_rejections':python_negative} 
    ordinary=(FIX/'actual-ordinary-pt6-de3.jsonl').read_bytes()
    input_records=[json.loads(s) for s in ordinary.decode().splitlines()]
    require(len(input_records)==9 and collections.Counter(r['language'] for r in input_records)=={'pt':6,'de':3},'actual ordinary fixture counts')
    out=run_node(ordinary,ROOT)
    require(out.returncode==0,'ordinary Node stream failure '+out.stderr.decode(errors='replace')[:200])
    require(sha(out.stdout)=='f148bb932a4fd833d32f49cc8ac434cc0ae94150311ada642c83209238b31f01','pinned actual current-main ordinary projector output changed')
    (args.out/'actual9-ordinary-projection.jsonl').write_bytes(out.stdout)
    phases['ordinary_actual_pt6_de3']={'records':9,'pt':6,'de':3,'projection_sha256':sha(out.stdout),'pinned_current_main_projection_sha256':'f148bb932a4fd833d32f49cc8ac434cc0ae94150311ada642c83209238b31f01','byte_identical_to_current_main':True}
    if args.baseline is not None:
        before=run_node(ordinary,args.baseline);require(before.returncode==0 and before.stdout==out.stdout,'current-main ordinary projection differs bytewise')
        phases['ordinary_actual_pt6_de3']['paired_main_replay']=True
    receipt={'task':'BOOKS-FR004-HI003-CURRENT-SOFTWARE-REBASE-001','private':True,'status':'PASS_BOUNDED',
             'phases':phases,'limits':['no hosted browser','no whole corpus','no GitHub writes or source publication','no PDF or full source-intake review']}
    path=args.out/'actual-real-callers-results.json';path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
    print('PASS portable real callers',json.dumps({k:(v.get('record_count') or v.get('records') or v.get('total') or v.get('count')) for k,v in phases.items()}))
    print('RECEIPT',path)

if __name__=='__main__':main()
