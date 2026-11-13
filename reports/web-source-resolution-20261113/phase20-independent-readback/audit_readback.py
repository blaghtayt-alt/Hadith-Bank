"""Independently bind the phase20 overwrite bodies and complete ancestor trees."""
from pathlib import Path
import base64, collections, datetime, gzip, hashlib, json, sys

HERE=Path(__file__).resolve().parent; WORK=HERE.parent
PIN='b7f21cbdd84fc922575b946e92b246e2665478ab'
PARENT='17cd396eb858a29162505d545aad556ac73ce9ce'
BASE='70c1a0799bcf67a18bf28bdb9a6672fe1edbc552'
TREE='0d477db71751c7be91d761aae27f93b1fbcd9aeb'
MANIFEST='e342d350577fe7a0a91ad2907842d26991e03b723c0eaec7b20c22fd9f0adf86'
SD='imports/web-deenhindi-20261112'; REV=SD+'/reviews'
ACTIVE=REV+'/source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
REL=Path('reports/web-source-resolution-20261113/phase20-independent-readback')
sys.dont_write_bytecode=True;sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer
def sha(b):return hashlib.sha256(b).hexdigest()
def git(kind,b):return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def bind(b):return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git('blob',b)}
def read(p):return json.loads(p.read_bytes())
def api(n):return json.loads(read(HERE/'input'/(n+'.json'))['content'])
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('Immutable audit differs',str(p))
    else:p.write_bytes(b)
def ent(t):return {r['path']:r for r in t['tree']}
def ident(r):return r.get('occurrence_id',r.get('id'))
def rows(b):
    x=json.loads(gzip.decompress(b));return x.get('records',x.get('decisions'))

raw=(HERE/'input/manifest.json').read_bytes();assert sha(raw)==MANIFEST
m=json.loads(raw);assert len(m['files'])==92 and sum(r['bytes'] for r in m['files'])==8756155
by_path={r['path']:r for r in m['files']};assert len(by_path)==92
targets=read(HERE/'input/targets.json');assert len(targets)==3
assert {r['path'] for r in targets}=={ACTIVE,QUEUE,DOC}
assert targets==[by_path[t['path']] for t in targets]
c=api('published-commit');bc=api('before-commit');basec=api('base-commit');ref=api('observed-main-ref')
assert c['sha']==PIN and c['tree']['sha']==TREE and [r['sha'] for r in c['parents']]==[PARENT]
assert bc['sha']==PARENT and [r['sha'] for r in bc['parents']]==[BASE]
assert basec['sha']==BASE and basec['tree']['sha']=='1a4a609c58936eda0dfae376dd4370d2988a5997'
assert ref['ref']=='refs/heads/main' and ref['object']['sha']==PIN
names={'':'root-tree','docs':'tree-docs','imports':'tree-imports',SD:'tree-imports-web-deenhindi',
       REV:'tree-reviews','reports':'tree-reports','reports/web-source-resolution-20261113':'tree-reports-web-source'}
trees={};bindings=[]
for side in ['base','before','after']:
    for path,name in names.items():
        n=side+'-'+name;t=api(n);assert t['truncated'] is False
        entries=t['tree'];assert len(entries)==len({r['path'] for r in entries})
        assert all('/' not in r['path'] and '\0' not in r['path'] for r in entries)
        ordered=sorted(entries,key=lambda r:(r['path']+('/' if r['type']=='tree' else '')).encode())
        body=b''.join((r['mode'].lstrip('0')+' '+r['path']).encode()+b'\0'+bytes.fromhex(r['sha']) for r in ordered)
        assert git('tree',body)==t['sha'];trees[(side,path)]=t
        if path:
            parent,_,part=path.rpartition('/');e=ent(trees[(side,parent)])[part]
            assert e['type']=='tree' and e['sha']==t['sha']
        else:assert t['sha']=={'base':basec,'before':bc,'after':c}[side]['tree']['sha']
        bindings.append({'snapshot':side,'path':path or '/','git_tree_sha1':t['sha'],'complete_entries':len(entries),
            'truncated':False,'git_tree_object_rehashed':True,'tree_object_sha256':sha(body),
            'saved_response_sha256':sha((HERE/'input'/(n+'.json')).read_bytes())})
assert len(bindings)==21
comparisons=[]
for path in names:
    a=ent(trees[('before',path)]);b=ent(trees[('after',path)])
    assert not set(a)-set(b)
    changed={k for k in a if a[k]!=b[k]};added=set(b)-set(a)
    prefix=path+'/' if path else ''
    allowed={p[len(prefix):].split('/')[0] for p in by_path if p.startswith(prefix)}
    assert (changed|added)<=allowed,(path,changed,added,allowed)
    comparisons.append({'path':path or '/','before_tree_sha':trees[('before',path)]['sha'],'after_tree_sha':trees[('after',path)]['sha'],
        'changed_existing_entries':sorted(changed),'added_entries':sorted(added),'all_other_complete_entries_equal':True})
assert comparisons[0]['changed_existing_entries']==['docs','imports','reports']
a=ent(trees[('base','')]);b=ent(trees[('before','')]);assert set(a)==set(b)
assert {k for k in a if a[k]!=b[k]}=={'imports','materials'}
for path in ['docs','reports','reports/web-source-resolution-20261113',REV]:
    assert ent(trees[('base',path)])==ent(trees[('before',path)])
assert ent(trees[('after','')])['materials']==ent(trees[('before','')])['materials']
preserved_acquisition=[]
for name,e in sorted(ent(trees[('before',SD)]).items()):
    if name=='reviews':continue
    assert ent(trees[('after',SD)])[name]==e
    preserved_acquisition.append({'path':SD+'/'+name,'kind':e['type'],'git_object_sha1':e['sha'],'bytes':e.get('size'),'before_after_full_entry_equal':True})
assert len(preserved_acquisition)==12 and {'raw','parsed','state.json','progress.json'}<={Path(r['path']).name for r in preserved_acquisition}
files=[]
for i,t in enumerate(targets):
    response_path=HERE/f'input/file-{i:02d}.json';x=read(response_path);assert x['encoding']=='base64'
    data=base64.b64decode(''.join(x['content'].split()),validate=True)
    assert bind(data)=={k:t[k] for k in ['bytes','sha256','git_blob_sha1']}
    assert git('blob',data)==x['sha'] and data==Path(t['local_path']).read_bytes()
    assert (HERE/'downloaded'/t['path']).read_bytes()==data
    folder,_,name=t['path'].rpartition('/');e=ent(trees[('after',folder)])[name]
    assert e['type']=='blob' and e['sha']==x['sha'] and e['size']==len(data)
    chain=[];p=folder
    while True:
        chain.append({'path':p or '/','git_tree_sha1':trees[('after',p)]['sha']})
        if not p:break
        p=p.rpartition('/')[0]
    files.append({'path':t['path'],**bind(data),'complete_body_matches_frozen_payload':True,'github_url':x['display_url'],
        'ancestral_trees':list(reversed(chain)),'response_snapshot_sha256':sha(response_path.read_bytes())})
assert sum(r['bytes'] for r in files)==1234168
before_reviews=ent(trees[('before',REV)]);after_reviews=ent(trees[('after',REV)])
old41={k:v for k,v in before_reviews.items() if v['type']=='blob' and k.startswith('source-review-')}
new41={k:v for k,v in after_reviews.items() if v['type']=='blob' and k.startswith('source-review-')}
assert set(old41)==set(new41) and len(old41)==41
preserved=[];prior_ids=set();before_active=None
for name,e in sorted(old41.items()):
    path=REV+'/'+name;p=WORK/'phase19-independent-readback/downloaded'/path
    if not p.exists():p=WORK/'phase19-checkpoint3e574-independent-integration/validation/published-reviews'/path
    data=p.read_bytes();assert git('blob',data)==e['sha'] and len(data)==e['size']
    records=rows(data);ids={ident(r) for r in records};assert len(ids)==len(records) and not ids&prior_ids;prior_ids|=ids
    if path==ACTIVE:before_active=data;continue
    assert e==new41[name]
    preserved.append({'path':path,**bind(data),'decisions':len(ids),'before_after_full_git_entry_equal':True,
        'body_origin':'Complete previously verified local bytes rehashed against both fresh tree entries; not downloaded anew here.'})
assert len(preserved)==40 and len(prior_ids)==3490 and before_active is not None
after_active=(HERE/'downloaded'/ACTIVE).read_bytes()
assert sha(before_active)=='18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'
assert sha(after_active)=='6d099f91f2e406b6ca026930f4437cc1ce3983e26883cfedc3049f9cbb2f91a7'
old={ident(r):r for r in rows(before_active)};new={ident(r):r for r in rows(after_active)}
assert set(old)==set(new) and len(new)==477
primary=WORK/'phase20-original-bukhari25-hi-ur'
selection=read(primary/'input/selection.json');selected_ids={r['id'] for r in selection['selected']}
keys={(r['id'],f['language']) for r in selection['selected'] for f in r['fields']};assert len(keys)==50 and len(selected_ids)==25
baseline=(primary/'input/pinned'/selection['source_baseline_path']).read_bytes()
assert sha(baseline)==selection['source_baseline_sha256']=='5c9598c1c61cee509155013dde44221de2e17f11bd29d0f475092f2a6e86fb36'
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,gzip.decompress(baseline).splitlines())}
counts=collections.Counter();changed=set()
for ident,before in old.items():
    after=new[ident];assert {k:v for k,v in before.items() if k!='fields'}=={k:v for k,v in after.items() if k!='fields'}
    assert before['decision']==after['decision']=='register'
    if ident not in selected_ids:assert before==after;counts['untouched_parent_records']+=1
    a={f['language']:f for f in before['fields']};b={f['language']:f for f in after['fields']};assert set(a)==set(b)
    for language,f in a.items():
        key=(ident,language);g=b[language]
        if key not in keys:assert f==g;counts['unchanged_other_field_definitions']+=1;continue
        assert f!=g and not f['reviewed'] and g['reviewed'];changed.add(key)
        text=sources[ident]['source_record'][g['source_field']]
        assert g['text_sha256']==f['text_sha256']==sha(text.encode())
        assert g['chars_reviewed']==len(text) and g['bytes_reviewed']==len(text.encode())
        assert g['selected_spans'];counts['new_complete_read_fields']+=1;counts['new_admitted_fields']+=1
        counts['characters_read']+=len(text);counts['utf8_bytes_read']+=len(text.encode())
        for span in g['selected_spans']:
            assert sha(text[span['start']:span['end']].encode())==span['sha256'];counts['selected_spans']+=1
assert changed==keys and counts=={'untouched_parent_records':452,'unchanged_other_field_definitions':2335,
    'new_complete_read_fields':50,'new_admitted_fields':50,'characters_read':27103,'utf8_bytes_read':58879,'selected_spans':92}
oldq=(WORK/'phase17-independent-readback/downloaded'/QUEUE).read_bytes();newq=(HERE/'downloaded'/QUEUE).read_bytes()
for side,data in [('before',oldq),('after',newq)]:
    e=ent(trees[(side,'reports/web-source-resolution-20261113')])[Path(QUEUE).name]
    assert e['sha']==git('blob',data) and e['size']==len(data)
assert sha(newq)=='8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349'
before_lines=gzip.decompress(oldq).splitlines(keepends=True);after_lines=gzip.decompress(newq).splitlines(keepends=True)
assert after_lines==[l for l in before_lines if json.loads(l)['id'] not in selected_ids]
old_langs=collections.Counter(f['language'] for l in before_lines for f in json.loads(l)['fields'])
new_langs=collections.Counter(f['language'] for l in after_lines for f in json.loads(l)['fields'])
assert len(before_lines)==3379 and old_langs=={'hi':3285,'ur':3076}
assert len(after_lines)==3354 and new_langs=={'hi':3260,'ur':3051}
old_doc=(WORK/'phase19-independent-readback/downloaded'/DOC).read_bytes();new_doc=(HERE/'downloaded'/DOC).read_bytes()
assert len(old_doc)==102908 and git('blob',old_doc)==ent(trees[('before','docs')])[Path(DOC).name]['sha']
prefix=(WORK/'phase20-final-publication/status-prefix-draft.md').read_bytes()
assert sha(prefix)=='8a33a84f338be599527ff52555d6eb05fa2acf3c542c6738fddd1cf64c61b637' and new_doc==prefix+old_doc
assert b'6,311' in prefix and b'This is a 50-field extension' in prefix
assert b'skipped the website upload and Pages deployment' in prefix
report={'schema':'hadith-bank-independent-publication-readback-v1','status':'PASS',
    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':'blaghtayt-alt/Hadith-Bank',
    'published_commit':PIN,'actual_parent_commit':PARENT,'actual_root_tree':TREE,'documented_previous_publication':BASE,
    'source_review_pin':selection['source_publication_commit'],'observed_main_ref':ref['object']['sha'],
    'publication_manifest_sha256':MANIFEST,'publication_manifest_files':92,'publication_manifest_bytes':8756155,
    'independently_downloaded_complete_bodies':3,'independently_downloaded_bytes':1234168,'file_checks':files,
    'all_three_complete_bodies_match_frozen_payload_sha256_and_git_blob':True,'tree_bindings':bindings,
    'complete_tree_bindings':21,'unique_tree_objects':len({r['git_tree_sha1'] for r in bindings}),
    'complete_tree_entries_across_bindings':sum(r['complete_entries'] for r in bindings),'all_full_tree_objects_rehashed':True,
    'directory_comparisons':comparisons,'unchanged_other40_active_entries_and_full_local_body_hashes':preserved,
    'active_ledgers_before_and_after':41,'distinct_manual_parent_ids_before_and_after':3490,
    'all477_parent_dispositions_and_nonfield_metadata_exact':True,'new_field_counts_from_complete_saved_active_body':dict(counts),
    'canonical_queue_before':{**bind(oldq),'fields':6361,'occurrences':3379,'by_language':dict(old_langs)},
    'canonical_queue_after':{**bind(newq),'fields':6311,'occurrences':3354,'by_language':dict(new_langs)},
    'exact50_field_25_occurrence_queue_delta':True,'all_remaining_queue_line_bytes_and_order_exact':True,
    'complete_old102908_byte_document_is_exact_suffix':True,'document_prefix_sha256':sha(prefix),
    'concurrent_source_checkpoint17cd_is_actual_direct_parent':True,'17cd_changed_only_imports_and_materials_from70c_root':True,
    'complete_review_tree_and_canonical_queue_unchanged_between70c_and17cd':True,
    'all12_current_acquisition_entries_preserved_from17cd':preserved_acquisition,
    'current_generated_materials_and_all_unrelated_root_entries_preserved':True,
    'full17cd_state_history_audit_performed_here':False,'new17cd_source_counts_claimed_here':False,
    'live_deployment_verified_here':False,'linguistic_rereading_in_this_readback':0,'native_tests_repeated_here':False,
    'github_writes':0,'source_site_requests':0,
    'limits':'Fresh GitHub commit/ref, complete before/after/base ancestor trees and all three complete overwrite bodies were independently retrieved. The remaining89 payload bodies rely on the frozen publisher manifest and are not redownloaded here. Prior40 complete ledger bodies were freshly rehashed against exact tree entries. Current17cd acquisition preservation is proved by immutable subtree/blob identity; its full source history and new counters require a separate audit. No new semantic reading, native rerun, authenticity certification or live-deployment claim is made.'}
put(HERE/'readback-receipt.json',enc(report))
evidence={'schema':'independent-github-readback-input-snapshots-v1','inputs':{p.name:read(p) for p in sorted((HERE/'input').glob('*.json'))}}
output={'readback-receipt.json':enc(report),'response-and-tree-evidence.json.gz':gzip.compress(enc(evidence),mtime=0),'audit_readback.py':Path(__file__).read_bytes()}
delivery=[]
for name,data in output.items():
    p=HERE/'publish'/REL/name;put(p,data);delivery.append({'path':str(REL/name),'local_path':str(p),'source_path':str(p),**bind(data)})
manifest={'schema':'independent-github-readback-delivery-v1','status':'PASS','published_commit':PIN,'files':delivery,'total_files':3,'total_bytes':sum(r['bytes'] for r in delivery)}
put(HERE/'delivery-manifest.json',enc(manifest))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),'report_sha256':sha(enc(report)),
    'files':3,'bytes':manifest['total_bytes'],'full_bodies':3,'body_bytes':1234168,'tree_bindings':21,
    'unique_trees':report['unique_tree_objects'],'tree_entries':report['complete_tree_entries_across_bindings'],'preserved_ledgers':40,'counts':dict(counts)}))
