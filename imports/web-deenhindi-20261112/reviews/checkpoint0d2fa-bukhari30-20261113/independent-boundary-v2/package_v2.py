"""Freeze the exact two-field2597 scope restoration and complete v1 evidence."""
from pathlib import Path
import gzip,hashlib,json,shutil
HERE=Path(__file__).resolve().parent
EVID=Path('imports/web-deenhindi-20261112/reviews/checkpoint0d2fa-bukhari30-20261113')
ACTIVE=Path('imports/web-deenhindi-20261112/reviews/source-review-checkpoint0d2fa-bukhari30-20261113.json.gz')
FIND=HERE.parent/'phase21-checkpoint0d2fa-bukhari30-independent-audit/independent-boundary-findings-v1.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def binding(b):return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('Immutable v2 output differs',str(p))
    else:p.write_bytes(b)
def fieldmap(r):return {f['language']:f for f in r['field_reviews']}
def mask(f):return {i for s in f['spans'] for i in range(s['start'],s['end'])}
def attributes(f):
    return {i:{k:v for k,v in s.items() if k not in ['start','end','sha256','reason']} for s in f['spans'] for i in range(s['start'],s['end'])}

v1raw=(HERE/'delivery-manifest-v1.json').read_bytes()
assert sha(v1raw)=='70a0fce9c10f36d47163672f3d636ca82668a65d04055c6c853c807a9ba16fc6'
v1=json.loads(v1raw);draft=json.loads((HERE/'candidate-delivery-manifest-v2.json').read_bytes())
for manifest in [v1,draft]:
    for r in manifest['files']:
        b=Path(r['local_path']).read_bytes();assert binding(b)=={k:r[k] for k in ['bytes','sha256','git_blob_sha1']}
findings=FIND.read_bytes();assert sha(findings)=='22f9399f491002af777824cacea81ffd4c4dbc033611d98bfdff59f89818e753'
before_raw=(HERE/'publish-v1'/ACTIVE).read_bytes();after_raw=(HERE/'candidate-v2'/ACTIVE).read_bytes()
assert sha(before_raw)=='1e08c967257c0a21bc5525130801bac71af357ba97400af21345ad30e1e94f08'
before={r['id']:r for r in json.loads(gzip.decompress(before_raw))['records']}
after={r['id']:r for r in json.loads(gzip.decompress(after_raw))['records']}
source={'deenhindi-'+r['collection']+':'+r['number']:r['source_record'] for r in map(json.loads,(HERE/'input/cohort.jsonl').read_bytes().splitlines())}
assert set(before)==set(after)==set(source) and len(before)==30
changed=[];unchanged_fields=0;unchanged_parents=0
requested={'hi':(601,614,'(माल-ए-ज़कात)'),'ur':(549,562,'( مال زکوٰۃ )')}
for ident,old in before.items():
    new=after[ident]
    stable=lambda r:{k:v for k,v in r.items() if k not in ['field_reviews','reason']}
    assert stable(old)==stable(new)
    if ident!='deenhindi-bukhari:2597':assert old==new;unchanged_parents+=1
    a,b=fieldmap(old),fieldmap(new);assert set(a)==set(b)
    for language,f in a.items():
        g=b[language]
        if ident!='deenhindi-bukhari:2597' or language not in requested:
            assert f==g;unchanged_fields+=1;continue
        start,end,literal=requested[language];text=source[ident][f['source_field']]
        assert text[start:end]==literal
        assert mask(g)-mask(f)==set(range(start,end)) and not mask(f)-mask(g)
        oldattrs,newattrs=attributes(f),attributes(g)
        assert all(newattrs[i]==v for i,v in oldattrs.items())
        assert len({json.dumps(newattrs[i],sort_keys=True) for i in range(start,end)})==1
        assert newattrs[start]==newattrs[start-1]==newattrs[end]
        stable_field=lambda x:{k:v for k,v in x.items() if k not in ['spans','reason']}
        assert stable_field(f)==stable_field(g)
        changed.append({'id':ident,'language':language,'start':start,'end':end,'text':literal,
            'text_sha256':sha(literal.encode()),'characters_restored':end-start,'utf8_bytes_restored':len(literal.encode()),
            'before_field_sha256':sha(enc(f)),'after_field_sha256':sha(enc(g)),
            'all_previously_selected_positions_and_attribution_values_exact':True})
assert len(changed)==2 and unchanged_fields==148 and unchanged_parents==29
assert sum(r['characters_restored'] for r in changed)==26 and sum(r['utf8_bytes_restored'] for r in changed)==52
summary=draft['summary'];assert summary==v1['summary']
out=HERE/'publish-v2';archive=EVID/'independent-boundary-v2/before-v1'
for r in draft['files']:
    if r['path']==str(EVID/'package-file-manifest.json'):continue
    put(out/r['path'],Path(r['local_path']).read_bytes())
for r in v1['files']:put(out/archive/'payload'/r['path'],Path(r['local_path']).read_bytes())
put(out/archive/'delivery-manifest-v1.json',v1raw)
receipt={'schema':'hadith-bank-two-field-source-scope-restoration-v2','status':'PASS',
    'source_checkpoint':'0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a','previous_manifest_sha256':sha(v1raw),
    'previous_active_sha256':sha(before_raw),'final_active_sha256':sha(after_raw),'independent_findings_sha256':sha(findings),
    'exact_changes':changed,'characters_restored':26,'utf8_bytes_restored':52,'characters_removed':0,
    'unchanged_other_field_definitions':148,'unchanged_whole_parents':29,
    'parent_source_and_dispositions_unchanged':True,'component_types_speakers_families_and_all_prior_selected_position_assignments_exact':True,
    'initial_complete_source_first_receipt_unchanged':True,'initial_notes_and_all_v1_payloads_preserved':True,
    'v1_payload_files_archived':len(v1['files']),'v1_manifest_archived':True,
    'final_native_summary':summary,'final_independent_gate_pending':True,
    'reason':'The source already contrasts collected property and a claimed personal gift. The zakah-property phrase limits the domain of the ensuing taking/oath statement. The final review therefore restores its exact two literals while leaving the explicit treasury explanation as context. Earlier broader-context judgments remain immutable historical evidence.',
    'github_writes':0,'source_http_requests':0}
put(out/EVID/'independent-boundary-v2/amendment-receipt.json',enc(receipt))
put(out/EVID/'independent-boundary-v2/independent-boundary-findings-v1.json',findings)
put(out/EVID/'independent-boundary-v2/package_v2.py',Path(__file__).read_bytes())
def record(p,local=False):
    r={'path':p.relative_to(out).as_posix(),**binding(p.read_bytes())}
    if local:r.update(local_path=str(p),source_path=str(p))
    return r
portable=out/EVID/'package-file-manifest.json'
put(portable,enc({'schema':'hadith-bank-source-review-package-manifest-v2','source_checkpoint':receipt['source_checkpoint'],
    'active_ledger':str(ACTIVE),'summary':summary,'amendment':receipt,
    'manifest_excludes_its_own_recursive_hash':True,
    'files':[record(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=portable]}))
manifest={'schema':'hadith-bank-source-review-delivery-v2','output_root':str(out),'summary':summary,'amendment':receipt,
    'files':[record(p,True) for p in sorted(out.rglob('*')) if p.is_file()]}
manifest.update(total_files=len(manifest['files']),total_bytes=sum(r['bytes'] for r in manifest['files']))
put(HERE/'delivery-manifest-v2.json',enc(manifest));put(HERE/'amendment-receipt-v2.json',enc(receipt))
for r in v1['files']:assert binding(Path(r['local_path']).read_bytes())=={k:r[k] for k in ['bytes','sha256','git_blob_sha1']}
assert (HERE/'delivery-manifest-v1.json').read_bytes()==v1raw
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),'active_sha256':sha(after_raw),
    'files':manifest['total_files'],'bytes':manifest['total_bytes'],'amendment_receipt_sha256':sha(enc(receipt)),
    'restored_characters':26,'restored_utf8_bytes':52,'unchanged_fields':148,'unchanged_parents':29}))
