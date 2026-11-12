#!/usr/bin/env python3
"""Reproduce lossless JSONL/CSV and complete-record partitions from corrected JSON."""
from pathlib import Path
import argparse,csv,json,collections
GROUPS=['hisn_hadith_dhikr_context','independent_non_prophetic','quran_and_author_only','attribution_unresolved']
def dump(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def csvout(p,rows,cols):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);a=p.parse_args()
    d=json.loads(a.input.read_text(encoding='utf-8'));rs=d['records'];out=a.output_root
    group=lambda r:r['content_classification_reconstructed_v2']['record_partition']
    artifact=d['reconstruction_v2']['review_id']
    assert set(group(r) for r in rs)<=set(GROUPS)
    dump(out/'data/records_export_envelope.json',{k:v for k,v in d.items() if k!='records'})
    jsonl(out/'data/corrected_all_records.jsonl',rs)
    csvout(out/'data/corrected_all_records.csv',[{'record_index':i,'record_id':r['record_id'],'record_partition':group(r),
       'record_json':json.dumps(r,ensure_ascii=False,separators=(',',':'))} for i,r in enumerate(rs)],
       ['record_index','record_id','record_partition','record_json'])
    cs=[c for r in rs for c in r['components']]
    jsonl(out/'data/components.jsonl',cs)
    csvout(out/'data/components.csv',[{'component_index':i,'record_id':c['record_id'],'segment_id':c['segment_id'],
       'component_json':json.dumps(c,ensure_ascii=False,separators=(',',':'))} for i,c in enumerate(cs)],
       ['component_index','record_id','segment_id','component_json'])
    for g in GROUPS:
        sub=[r for r in rs if group(r)==g]
        dump(out/'partitions'/(g+'_HOLD.json'),{'artifact_id':artifact,'partition':g,'status':'HOLD',
          'record_count':len(sub),'component_count':sum(len(r['components']) for r in sub),'records':sub,
          'complete_source_records_with_context':True,'not_unique_or_release_approved_hadith_count':True,
          'approved_for_bank':False,'approved_for_html':False,'separate_independent_final_evaluation':'NOT_RUN'})
    print(json.dumps({'records':len(rs),'components':len(cs),'partitions':dict(collections.Counter(group(r) for r in rs))}))
if __name__=='__main__':main()
