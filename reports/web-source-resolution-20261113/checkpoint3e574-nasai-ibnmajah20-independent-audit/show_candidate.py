"""Display exact proposed spans only after frozen independent source-first reading."""
from pathlib import Path
import gzip,json,sys
ROOT=Path(__file__).resolve().parent
OWNER=ROOT.parent/'phase19-checkpoint3e574-nasai-ibnmajah20-review'
readings=json.loads((ROOT/'complete-independent-source-first-readings.json').read_bytes())
assert readings['complete_fields_read']==40 and not readings['candidate_inspected']
source={('deenhindi-'+r['collection']+':'+r['number']):r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_text().splitlines())}
ledger=json.loads(gzip.decompress((OWNER/'publish/imports/web-deenhindi-20261112/reviews/source-review-checkpoint3e574-nasai-ibnmajah20-20261113.json.gz').read_bytes()))
FIELDS={'ar':'textArabic','hi':'translationHindi','ur':'translationUrdu','ur-Latn':'translationUrduRoman','en':'translationEnglish'}
rows=[]
for record in ledger['records']:
    ident=record.get('occurrence_id',record.get('id'))
    for f in record.get('fields',record.get('field_reviews')):
        if not f['reviewed']:continue
        text=source[ident]['source_record'][FIELDS[f['language']]]
        rows.append((ident,record,f,text))
start=int(sys.argv[1]);end=int(sys.argv[2])
for i,(ident,r,f,text) in enumerate(rows[start:end],start):
    print('\nFIELD',i,ident,f['language'],len(text),r['decision'])
    print('FIELD REASON',f.get('reason'));print('PARENT',r.get('report_type'),r.get('speaker'))
    cursor=0
    for s in f.get('selected_spans',f.get('spans')):
        if s['start']>cursor:print('CONTEXT',cursor,s['start'],repr(text[cursor:s['start']]))
        print('SELECTED',s['start'],s['end'],s.get('component_id'),s.get('report_type'),s.get('speaker'),s.get('source_report_family_id'))
        print(text[s['start']:s['end']]);cursor=s['end']
    if cursor<len(text):print('CONTEXT',cursor,len(text),repr(text[cursor:]))
