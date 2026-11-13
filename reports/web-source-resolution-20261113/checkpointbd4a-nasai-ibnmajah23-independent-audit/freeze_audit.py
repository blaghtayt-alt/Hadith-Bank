"""Freeze the independent final audit, source-first evidence and exact archive checks."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parent
OWNER=ROOT.parent/'phase18-checkpointbd4a-nasai-ibnmajah23-review'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-checkpointbd4a-nasai-ibnmajah23-20261113.json.gz'
EVID='imports/web-deenhindi-20261112/reviews/checkpointbd4a-nasai-ibnmajah23-20261113'
REL=Path('reports/web-source-resolution-20261113/checkpointbd4a-nasai-ibnmajah23-independent-audit')
def sha(b):return hashlib.sha256(b).hexdigest()
def git(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def bind(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b
    else:p.write_bytes(b)

v1=OWNER/'delivery-manifest-v1.json';v2=OWNER/'delivery-manifest-v2.json'
assert sha(v1.read_bytes())=='3c6edbb4854df1e34dcc3f3241c83e19a1d146c73b250ebdcf087b005f2ba056'
assert sha(v2.read_bytes())=='e0c6d08973dc3c39ec64d586ab6118ea729cb3441ad1fcf7aa82c13425bb965c'
old=read(v1);new=read(v2);by={r['path']:r for r in new['files']}
archive_prefix=EVID+'/independent-boundary-amendment-v2/previous-v1-payload/'
archives=[]
for r in old['files']:
    local=Path(r['local_path']);assert bind(local)['sha256']==r['sha256']
    archive=by[archive_prefix+r['path']];p=Path(archive['local_path'])
    assert p.read_bytes()==local.read_bytes() and bind(p)['sha256']==r['sha256'] and bind(p)['git_blob_sha1']==r['git_blob_sha1']
    archives.append({'original_path':r['path'],'archived_path':archive['path'],**bind(p),'exact_original_bytes_retained':True})
assert len(archives)==15
previous_manifest=Path(by[EVID+'/independent-boundary-amendment-v2/previous-delivery-manifest-v1.json']['local_path'])
assert previous_manifest.read_bytes()==v1.read_bytes()
active=read(Path(by[ACTIVE]['local_path']));assert bind(Path(by[ACTIVE]['local_path']))['sha256']=='644b2a872a77e37ffacbec1c6d8d6a569407f1fb27c1820b35574a20a8b812bf'
decisions={r['id']:r for r in active['records']}
coverage=read(Path(by[EVID+'/field-coverage.json.gz']['local_path']))
assert len(coverage)==len(decisions)==23
coverage_checks=0;actual_gaps=[];selected_masks={}
source={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(ROOT/'input/cohort.jsonl').read_text().splitlines())}
for row in coverage:
    d=decisions[row['id']];assert row['decision']==d['decision'] and row['source_record_sha256']==d['source_record_sha256']
    fs={f['language']:f for f in d['field_reviews']}
    assert len(row['fields'])==5
    for c in row['fields']:
        f=fs[c['language']];key=(row['id'],c['language']);text=source[row['id']]['source_record'][f['source_field']]
        for left,right in [('field_reviewed','reviewed'),('text_sha256','text_sha256'),('chars_reviewed','chars_reviewed'),('bytes_reviewed','bytes_reviewed')]:assert c[left]==f[right]
        assert c['selected_spans']==[[s['start'],s['end']] for s in f['spans']]
        assert c['boundary_reason']==f['reason']
        status='selected_report' if f['spans'] else 'reviewed_source_context' if f['reviewed'] else 'unreviewed_source_context'
        assert c['status']==status;coverage_checks+=1
        if not f['spans']:continue
        cursor=0;mask=[False]*len(text)
        for s in f['spans']:
            a,b=s['start'],s['end'];mask[a:b]=[True]*(b-a)
            if a>cursor:actual_gaps.append((row['id'],f['language'],cursor,a,text[cursor:a]))
            cursor=b
        if cursor<len(text):actual_gaps.append((row['id'],f['language'],cursor,len(text),text[cursor:]))
        selected_masks[key]=mask
assert coverage_checks==115 and len(actual_gaps)==17 and len(selected_masks)==44
inventory=read(Path(by[EVID+'/source-apparatus-inventory.json.gz']['local_path']))
assert inventory['active_ledger_sha256']==by[ACTIVE]['sha256']
assert inventory['exact_source_context_gaps']==17 and inventory['selected_fields']==44 and inventory['selected_literal_apparatus_markers']==0
assert sorted(actual_gaps)==sorted((r['id'],r['language'],r['start'],r['end'],r['text']) for r in inventory['context_gaps'])
assert {(r['id'],r['language']) for r in inventory['fields']}==set(selected_masks)
for row in inventory['fields']:
    key=(row['id'],row['language']);f=next(f for f in decisions[key[0]]['field_reviews'] if f['language']==key[1])
    text=source[key[0]]['source_record'][f['source_field']];mask=selected_masks[key]
    for p in row['retained_parentheses']:
        assert text[p['start']:p['end']]==p['text'] and all(mask[p['start']:p['end']])
    assert not any(ch=='؎' and mask[i] for i,ch in enumerate(text))
native=read(ROOT/'native-source-audit-final.json');assert native['status']=='PASS'
assert native['candidate_manifest_sha256']==sha(v2.read_bytes()) and native['active_ledger_sha256']==by[ACTIVE]['sha256']
report={**native,'schema':'hadith-bank-final-independent-reading-preservation-audit-v1',
    'complete_candidate_semantic_comparison_finished':True,'open_required_amendments':[],
    'exact_requested_v2_changes_verified':True,'before_candidate_and_initial_notes_preserved':True,
    'v1_payload_archive_count':15,'v1_manifest_archive_exact':True,'v1_archives':archives,
    'all115_coverage_derivative_fields_bound_to_final_active':True,
    'all17_admitted_field_context_gaps_match_final_inventory':True,
    'selected_footnote_markers':0,'initial_independent_note_refinements_are_explicit':True,
    'independent_source_first_reading':bind(ROOT/'complete-independent-source-first-readings.json'),
    'independent_saved_source_proof':bind(ROOT/'independent-source-verification.json'),
    'full_v1_boundary_comparison_and_findings':bind(ROOT/'independent-boundary-findings-v1.json'),
    'final_native_report':bind(ROOT/'native-source-audit-final.json')}
put(ROOT/'independent-final-v2-audit.json',enc(report))
out=ROOT/'publish'
names=['independent-final-v2-audit.json','complete-independent-source-first-readings.json',
    'independent-boundary-findings-v1.json','independent-source-verification.json',
    'native-source-audit-v1-preflight.json','native-source-audit-final.json',
    'field-and-source-proof-v1-preflight.json.gz','field-and-source-proof-final.json.gz',
    'record_independent_readings.py','verify_saved_sources.py','show_candidate.py','freeze_findings.py','audit_candidate.py','freeze_audit.py']
for name in names:put(out/REL/name,(ROOT/name).read_bytes())
for p in sorted(ROOT.glob('independent-readings-*.json')):put(out/REL/'source-first-batches'/p.name,p.read_bytes())
payload=[{'path':str(p.relative_to(out)),'local_path':str(p),**bind(p)} for p in sorted(out.rglob('*')) if p.is_file()]
delivery={'schema':'hadith-bank-independent-reading-audit-delivery-v1','status':'PASS',
    'primary_manifest_sha256':sha(v2.read_bytes()),'active_ledger_sha256':by[ACTIVE]['sha256'],
    'complete_source_fields_independently_read':49,'registered':22,'resolved_source_only':1,
    'files':payload,'total_files':len(payload),'total_bytes':sum(r['bytes'] for r in payload)}
put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest':bind(ROOT/'delivery-manifest.json'),
    'report':bind(ROOT/'independent-final-v2-audit.json'),'files':len(payload),'bytes':delivery['total_bytes']}))
