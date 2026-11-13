"""Archive v1, rebuild normally, then assert only the agreed two field refinements."""
from pathlib import Path
import copy,gzip,hashlib,json,runpy
HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
NAME='20261113-checkpoint0d2fa-muslim22-manual-v1'
E=Path('imports/web-deenhindi-20261112/reviews/evidence')/NAME
OUT=HERE/'publish-v2'
A=E/'independent-variant-amendment-v2'
assert not (HERE/'delivery-manifest-v2.json').exists(),'Frozen v2 may not be rewritten'
def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)
v1raw=(HERE/'delivery-manifest-v1.json').read_bytes()
assert sha(v1raw)=='a43ba89def3d84bf83775664d501d4d1bfc7a0ca84cace7c8edd5d97452b37fe'
v1=json.loads(v1raw);oldbind=[]
for f in v1['files']:
    raw=Path(f['local_path']).read_bytes();assert sha(raw)==f['sha256'] and len(raw)==f['bytes']
    put(OUT/A/'previous-v1'/f['path'],raw);oldbind.append({'path':f['path'],'sha256':sha(raw),'bytes':len(raw)})
put(OUT/A/'previous-v1/delivery-manifest-v1.json',v1raw)
for name in ['validation-v1.json','boundary-view-v1.json','derived-preview-v1.jsonl.gz']:
    put(OUT/A/'previous-v1-local'/name,(HERE/name).read_bytes())
finding_path=HERE.parent/'phase21-checkpoint0d2fa-muslim22-independent-audit/independent-boundary-findings-v1.json'
finding_raw=finding_path.read_bytes();assert sha(finding_raw)=='ed6bb3f68631b447bd75d781c9deb38bc42a62486f4d10c674c0888793ad26b8'
put(OUT/A/'independent-boundary-findings-v1.json',finding_raw)
put(OUT/A/'amend_v2.py',Path(__file__).read_bytes())
builder=(HERE/'package_and_validate.py').read_text()
builder=builder.replace('from manual_boundaries import READINGS','from manual_boundaries_v2 import READINGS')
builder=builder.replace("OUT = ROOT / 'publish-v1'","OUT = ROOT / 'publish-v2'")
builder=builder.replace('delivery-manifest-v1.json','candidate-builder-v2-manifest.json')
builder=builder.replace('validation-v1.json','validation-v2.json').replace('boundary-view-v1.json','boundary-view-v2.json').replace('derived-preview-v1.jsonl.gz','derived-preview-v2.jsonl.gz')
builder=builder.replace("'manual_boundaries.py', 'verify_local_sources.py', 'package_and_validate.py'","'manual_boundaries.py', 'manual_boundaries_v2.py', 'verify_local_sources.py', 'package_and_validate.py', 'package_and_validate_v2.py'")
put(HERE/'package_and_validate_v2.py',builder.encode())
runpy.run_path(str(HERE/'package_and_validate_v2.py'),run_name='__main__')
candidate=json.loads((HERE/'candidate-builder-v2-manifest.json').read_bytes())
oldactive=Path(next(f['local_path'] for f in v1['files'] if f['path']==v1['active_ledger_path'])).read_bytes()
newactive=(OUT/v1['active_ledger_path']).read_bytes()
assert sha(oldactive)=='74ce5ef0f8f15c46da1b5b858c5db368a4b62ae8fae1ef931cfb3704ab13b42e'
old={r['occurrence_id']:r for r in json.loads(gzip.decompress(oldactive))['records']}
new={r['occurrence_id']:r for r in json.loads(gzip.decompress(newactive))['records']}
findings=json.loads(finding_raw)['findings'];requests={(r['id'],r['language']):r for r in findings}
checks={'unchanged_whole_parent_decisions':0,'unchanged_other_field_definitions':0,'unchanged_other_read_fields':0,'unchanged_unread_fields':0,'restored_characters':0,'restored_utf8_bytes':0}
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(HERE/'input/cohort.jsonl').read_bytes().splitlines())}
for oid,before in old.items():
    after=new[oid];assert {k:v for k,v in before.items() if k!='fields'}=={k:v for k,v in after.items() if k!='fields'}
    if oid!='deenhindi-muslim:2556':assert before==after;checks['unchanged_whole_parent_decisions']+=1
    for bf,af in zip(before['fields'],after['fields']):
        key=(oid,bf['language'])
        if key not in requests:
            assert bf==af;checks['unchanged_other_field_definitions']+=1
            checks['unchanged_other_read_fields' if bf['reviewed'] else 'unchanged_unread_fields']+=1
            continue
        req=requests[key];text=sources[oid]['source_record'][bf['source_field']]
        assert sha(text.encode())==req['field_sha256'] and text[req['start']:req['end']]==req['text']
        opos={p for s in bf['selected_spans'] for p in range(s['start'],s['end'])};npos={p for s in af['selected_spans'] for p in range(s['start'],s['end'])}
        assert npos-opos==set(range(req['start'],req['end'])) and not opos-npos
        assert len(af['selected_spans'])==len(bf['selected_spans'])+1
        for a,b in zip(bf['selected_spans'],af['selected_spans']):
            assert {k:v for k,v in a.items() if k not in ('speaker','reason')}=={k:v for k,v in b.items() if k not in ('speaker','reason')}
        last=af['selected_spans'][-1]
        assert last['start']==req['start'] and last['end']==req['end'] and last['sha256']==req['sha256']
        assert last['component_id']==req['required_component_id'] and last['report_type']==req['required_report_type']
        assert last['source_report_family_id']==req['required_source_report_family_id'] and last['speaker']==req['required_speaker_scope']
        stable=lambda f:{k:v for k,v in f.items() if k not in ('selected_spans','reviewed_context_spans','speaker','reason','boundary_refinement')}
        assert stable(bf)==stable(af)
        checks['restored_characters']+=len(req['text']);checks['restored_utf8_bytes']+=len(req['text'].encode())
assert checks=={'unchanged_whole_parent_decisions':21,'unchanged_other_field_definitions':108,'unchanged_other_read_fields':45,'unchanged_unread_fields':63,'restored_characters':169,'restored_utf8_bytes':373}
for f in v1['files']:assert sha(Path(f['local_path']).read_bytes())==f['sha256']
assert (HERE/'delivery-manifest-v1.json').read_bytes()==v1raw
initial=(HERE/'complete-source-first-readings.json').read_bytes()
assert sha(initial)=='397aef12d11f805ba8bf6030bcedc39d97ce0009bc90fe4a2d7b3664ad517368'
receipt={'schema':'hadith-bank-source-bound-exact-variant-amendment-v2','result':'PASS',
    'source_commit':v1['source_commit'],'previous_manifest_sha256':sha(v1raw),'previous_active_sha256':sha(oldactive),
    'final_active_sha256':sha(newactive),'independent_findings_sha256':sha(finding_raw),'checks':checks,
    'all14_v1_payloads_and_manifest_archived_exact':True,'previous_files':oldbind,
    'initial_source_first_receipt_unchanged':sha(initial),'initial_context_judgment_preserved':True,
    'explicit_reconsideration':'The original source-first pass classified both the yani-name apposition and final version tail as identity apparatus. The independent full reading distinguished the final addition’s new finite predicate identifying the previously unnamed other participant, which is actual transmitted report content. That exact tail is now retained as its own same-family component, with source spelling and version attribution. The earlier yani Ibn Masud apposition remains context. Neither Aisha speech nor eyewitness testimony nor a new event is inferred.',
    'new_source_positions_removed':0,'new_occurrences_created':0,'new_linguistic_reading_credit':0,
    'source_http_requests':0,'github_writes':0,'independent_pro_qc':'not_performed',
    'native_validation_sha256':sha((HERE/'validation-v2.json').read_bytes())}
put(OUT/A/'amendment-receipt.json',enc(receipt));put(HERE/'amendment-receipt-v2.json',enc(receipt))
portable_path=E/'portable-manifest.json'
files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.relative_to(OUT)!=portable_path:
        raw=p.read_bytes();files.append({'path':p.relative_to(OUT).as_posix(),'local_path':str(p),'bytes':len(raw),'sha256':sha(raw),'git_blob_sha1':git(raw)})
portable={k:copy.deepcopy(v) for k,v in candidate.items() if k!='files'}
portable['schema']='hadith-bank-source-review-portable-manifest-v2';portable['files']=[{k:v for k,v in f.items() if k!='local_path'} for f in files]
(OUT/portable_path).write_bytes(enc(portable))
raw=(OUT/portable_path).read_bytes();files.append({'path':portable_path.as_posix(),'local_path':str(OUT/portable_path),'bytes':len(raw),'sha256':sha(raw),'git_blob_sha1':git(raw)})
final={k:copy.deepcopy(v) for k,v in candidate.items() if k!='files'}
final.update(schema='hadith-bank-source-review-delivery-v2',files=files,total_files=len(files),total_bytes=sum(f['bytes'] for f in files),
             amendment_receipt_sha256=sha(enc(receipt)),previous_v1_manifest_sha256=sha(v1raw))
put(HERE/'delivery-manifest-v2.json',enc(final))
print(json.dumps({'result':'PASS','manifest_sha256':sha(enc(final)),'active_sha256':sha(newactive),'amendment_receipt_sha256':sha(enc(receipt)),
    'files':len(files),'bytes':final['total_bytes'],'checks':checks},indent=2))
