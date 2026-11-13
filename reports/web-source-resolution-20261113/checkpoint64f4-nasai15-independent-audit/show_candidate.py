from pathlib import Path
import gzip,json,sys
R=Path(__file__).resolve().parent
sources={'deenhindi-'+x['collection']+':'+x['number']:x for x in map(json.loads,(R/'input/cohort.jsonl').read_text().splitlines())}
ledger=json.loads(gzip.decompress((R/'input/primary-active-v1.json.gz').read_bytes()))
start=int(sys.argv[1]);stop=int(sys.argv[2])
for d in ledger['records'][start:stop]:
 print('\nOCCURRENCE',d['id'],d['decision']);print('PARENT',d['reason'])
 for f in d['field_reviews']:
  if not f['reviewed']:continue
  text=sources[d['id']]['source_record'][f['source_field']]
  print('\nFIELD',f['language'],f['action'],f.get('source_text_annotations'))
  cur=0
  for s in f['spans']:
   if s['start']>cur:print('CONTEXT',cur,s['start'],repr(text[cur:s['start']]))
   print('SELECTED',s['start'],s['end'],s['component_id'],s['report_type'],s['speaker'],s.get('source_report_family_id'));print(text[s['start']:s['end']]);cur=s['end']
  if cur<len(text):print('CONTEXT',cur,len(text),repr(text[cur:]))
