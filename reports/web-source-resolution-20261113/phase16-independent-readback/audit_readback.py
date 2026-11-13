"""Independently bind phase16 bytes and preserved state to complete Git trees."""
from pathlib import Path
import base64,collections,datetime,gzip,hashlib,json
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
PIN='d0a863b0966c7eb1ae1d5c36202de282caf77cab'
PARENT='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
TREE='ee5e26732dba6ea2ce9a7d3380085dac061f1845'
MERGE='4b61373da1cd6205270f0c87d7c502ee5b36db26'
MANIFEST_SHA='53e332441c181bb7e59eda327a40876df213909f3662325d598ab5cbb4f333c6'
REL=Path('reports/web-source-resolution-20261113/phase16-independent-readback')

def sha(b):return hashlib.sha256(b).hexdigest()
def git(kind,b):return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def bind(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git('blob',b)}
def read(p):return json.loads(p.read_bytes())
def api(name):return json.loads(read(ROOT/'input'/(name+'.json'))['content'])
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('Frozen output differs',str(p))
    else:p.write_bytes(b)
def entries(tree):return {r['path']:r for r in tree['tree']}

inputs={str(p.relative_to(ROOT)):bind(p) for p in sorted((ROOT/'input').rglob('*')) if p.is_file()}
manifest_raw=(ROOT/'input/manifest.json').read_bytes()
assert sha(manifest_raw)==MANIFEST_SHA
manifest=json.loads(manifest_raw)
assert len(manifest['files'])==234 and sum(r['bytes'] for r in manifest['files'])==6430764
manifest_by_path={r['path']:r for r in manifest['files']}
targets=read(ROOT/'input/targets.json');assert len(targets)==5
assert targets==[manifest_by_path[t['path']] for t in targets]
commit=api('published-commit');before_commit=api('before-commit');merge=api('pr15-merge-commit');ref=api('observed-main-ref')
assert commit['sha']==PIN and commit['tree']['sha']==TREE and [p['sha'] for p in commit['parents']]==[PARENT]
assert before_commit['sha']==PARENT and [p['sha'] for p in before_commit['parents']]==[MERGE]
assert merge['sha']==MERGE and [p['sha'] for p in merge['parents']]==[
    'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d','7cb61d9fe46bbfab826b9b1b93c451968910cbae']
assert ref['ref']=='refs/heads/main' and ref['object']['sha']==PIN

path_names={
    '':'root-tree','docs':'tree-docs','imports':'tree-imports',
    'imports/web-deenhindi-20261112':'tree-imports-web-deenhindi',
    'imports/web-deenhindi-20261112/reviews':'tree-reviews',
    'reports':'tree-reports','reports/web-source-resolution-20261113':'tree-reports-web-source',
}
trees={};tree_bindings=[]
for side in ['before','after']:
    for path,name in path_names.items():
        response='published-root-tree' if side=='after' and not path else side+'-'+name
        tree=api(response);trees[(side,path)]=tree
        assert tree['truncated'] is False
        original=tree['tree'];assert len({e['path'] for e in original})==len(original)
        assert all('/' not in e['path'] and '\0' not in e['path'] for e in original)
        ordered=sorted(original,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
        raw=b''.join((e['mode'].lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in ordered)
        assert git('tree',raw)==tree['sha'],(side,path)
        if path:
            parent,_,name=path.rpartition('/')
            entry=entries(trees[(side,parent)])[name]
            assert entry['type']=='tree' and entry['sha']==tree['sha']
        else:assert tree['sha']==(TREE if side=='after' else before_commit['tree']['sha'])
        tree_bindings.append({'snapshot':side,'path':path or '/',
            'git_tree_sha1':tree['sha'],'complete_entries':len(original),'truncated':False,
            'git_tree_object_rehashed':True,'tree_object_sha256':sha(raw),'tree_object_bytes':len(raw)})
assert len(tree_bindings)==14 and sum(r['complete_entries'] for r in tree_bindings)==923

def compare_directory(path,allowed_changed=(),expected_added=None):
    a=entries(trees[('before',path)]);b=entries(trees[('after',path)])
    assert not set(a)-set(b),(path,'removed entries')
    changed={name for name in a if a[name]!=b[name]}
    assert changed==set(allowed_changed),(path,changed)
    added=set(b)-set(a)
    if expected_added is not None:assert added==set(expected_added),(path,added)
    return {'path':path or '/', 'before_tree_sha':trees[('before',path)]['sha'],
        'after_tree_sha':trees[('after',path)]['sha'],'unchanged_existing_entries':len(a)-len(changed),
        'changed_existing_entries':sorted(changed),'added_entries':sorted(added),'removed_entries':[]}

comparisons=[
    compare_directory('',('docs','imports','reports'),()),
    compare_directory('docs',('WEB-SOURCE-RESOLUTION-20261113.md',),()),
    compare_directory('imports',('web-deenhindi-20261112',),()),
    compare_directory('imports/web-deenhindi-20261112',('reviews',),()),
    compare_directory('reports',('web-source-resolution-20261113',),()),
    compare_directory('reports/web-source-resolution-20261113',()),
]
reviews_path='imports/web-deenhindi-20261112/reviews'
before_reviews=entries(trees[('before',reviews_path)])
after_reviews=entries(trees[('after',reviews_path)])
old29={k:v for k,v in before_reviews.items() if k.startswith('source-review-')}
new33={k:v for k,v in after_reviews.items() if k.startswith('source-review-')}
assert len(old29)==29 and len(new33)==33
assert all(new33[k]==v for k,v in old29.items())
new_names=set(new33)-set(old29)
assert new_names=={Path(t['path']).name for t in targets if Path(t['path']).parent.as_posix()==reviews_path}
comparisons.append(compare_directory(reviews_path,('evidence',),new_names|{
    'checkpoint5589-abudawud-tirmidhi25-20261113',
    'checkpoint5589-bukhari20-ibnmajah5-20261113',
    'checkpoint5589-nasai-ibnmajah25-20261113'}))
preserved_reviews=[{'path':reviews_path+'/'+name,'git_blob_sha1':item['sha'],
    'bytes':item.get('size'),'before_after_full_entry_equal':True} for name,item in sorted(old29.items())]

queue_path='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
queue_local=WORK/'phase15-independent-readback/downloaded'/queue_path
queue_raw=queue_local.read_bytes()
assert sha(queue_raw)=='343e72455fe122b59b37d795a59f9f8cca2358077723f1c725e4b1eaa3f57227'
queue_dir,_,queue_name=queue_path.rpartition('/')
qe_before=entries(trees[('before',queue_dir)])[queue_name]
qe_after=entries(trees[('after',queue_dir)])[queue_name]
assert qe_before==qe_after and git('blob',queue_raw)==qe_after['sha'] and len(queue_raw)==qe_after['size']
queue_rows=list(map(json.loads,gzip.decompress(queue_raw).splitlines()))
queue_lang=collections.Counter(f['language'] for r in queue_rows for f in r['fields'])
assert len(queue_rows)==len({r['id'] for r in queue_rows})==3404
assert queue_lang=={'hi':3310,'ur':3101} and sum(queue_lang.values())==6411
queue_result={'path':queue_path,**bind(queue_local),'occurrences':3404,'pending_fields':6411,
    'by_language':dict(queue_lang),'before_after_git_entry_equal':True,
    'identity_basis':'The complete previously downloaded queue bytes have the required SHA256 and exact Git blob identity present in both freshly fetched complete ancestor trees. The queue body was not downloaded again.'}

source_dir='imports/web-deenhindi-20261112'
source_before=entries(trees[('before',source_dir)])
source_after=entries(trees[('after',source_dir)])
source_preserved=[]
for name,item in sorted(source_before.items()):
    if name=='reviews':continue
    assert item==source_after[name]
    source_preserved.append({'path':source_dir+'/'+name,'kind':item['type'],'git_object_sha1':item['sha'],
        'bytes':item.get('size'),'before_after_full_entry_equal':True})
assert len(source_preserved)==12
assert {'state.json','progress.json','raw','parsed'} <= {Path(r['path']).name for r in source_preserved}

files=[];ledger_counts=[];ids=set();counts=collections.Counter();reading_languages=collections.Counter();excluded=[]
for index,target in enumerate(targets):
    response_path=ROOT/f'input/file-{index:02d}.json';response=read(response_path)
    assert response['encoding']=='base64'
    raw=base64.b64decode(response['content'])
    assert len(raw)==target['bytes'] and sha(raw)==target['sha256']
    assert git('blob',raw)==target['git_blob_sha1']==response['sha']
    assert raw==Path(target['local_path']).read_bytes()
    downloaded=ROOT/'downloaded'/target['path'];assert downloaded.read_bytes()==raw
    folder,_,name=target['path'].rpartition('/')
    tree_entry=entries(trees[('after',folder)])[name]
    assert tree_entry['type']=='blob' and tree_entry['sha']==response['sha'] and tree_entry['size']==len(raw)
    ancestry=[];path=folder
    while True:
        ancestry.append({'path':path or '/','sha':trees[('after',path)]['sha']})
        if not path:break
        path=path.rpartition('/')[0]
    item={'path':target['path'],**bind(downloaded),'github_blob_sha1':response['sha'],
        'github_url':response['display_url'],'full_bytes_match_frozen_payload':True,
        'ancestral_trees':list(reversed(ancestry)),'response_snapshot_sha256':sha(response_path.read_bytes())}
    if folder==reviews_path:
        doc=json.loads(gzip.decompress(raw));rows=doc.get('records',doc.get('decisions'))
        local=collections.Counter();local_excluded=[]
        for row in rows:
            identity=row.get('occurrence_id',row.get('id'));assert identity and identity not in ids;ids.add(identity)
            action=row.get('decision',row.get('action'));assert action in ['register','exclude']
            local[action]+=1;counts[action]+=1
            if action=='exclude':excluded.append(identity);local_excluded.append(identity)
            fields=row.get('fields',row.get('field_reviews'));assert isinstance(fields,list)
            assert len({f['language'] for f in fields})==len(fields)
            assert all(f['language'] in ['ar','hi','ur','ur-Latn','en'] for f in fields)
            local['implicit_unread_slots']+=5-len(fields)
            for f in fields:
                reviewed=f.get('reviewed',False);spans=f.get('selected_spans',f.get('spans',[]))
                assert isinstance(reviewed,bool)
                local['explicit_field_decisions']+=1
                if reviewed:
                    assert isinstance(f['chars_reviewed'],int) and f['chars_reviewed']>=0 and f['bytes_reviewed']>=0
                    if 'text_chars' in f:assert f['chars_reviewed']==f['text_chars']
                    local['complete_fields_read']+=1
                    local['characters_read']+=f['chars_reviewed'];local['utf8_bytes_read']+=f['bytes_reviewed']
                    reading_languages[f['language']]+=1
                    local['admitted_fields' if spans else 'read_context_fields']+=1
                else:
                    assert not spans and f['chars_reviewed']==0 and f['bytes_reviewed']==0
                    local['explicit_unread_fields']+=1
                local['selected_spans']+=len(spans)
        local['unread_fields']=local['explicit_unread_fields']+local['implicit_unread_slots']
        local['total_language_slots']=len(rows)*5
        for key,value in local.items():
            if key not in ['register','exclude']:counts[key]+=value
        summary={'path':target['path'],'sha256':sha(raw),'occurrences':len(rows),**dict(local),'source_only_ids':local_excluded}
        ledger_counts.append(summary);item['ledger_counts']=summary
    files.append(item)
assert len(ledger_counts)==4 and len(ids)==100
assert counts['register']==96 and counts['exclude']==4
assert counts['explicit_field_decisions']==434 and counts['total_language_slots']==500
assert counts['complete_fields_read']==212 and counts['admitted_fields']==192 and counts['read_context_fields']==20
assert counts['explicit_unread_fields']==222 and counts['implicit_unread_slots']==66 and counts['unread_fields']==288
assert counts['characters_read']==91600 and counts['utf8_bytes_read']==194325 and counts['selected_spans']==310
assert sorted(excluded)==['deenhindi-abudawud:2330','deenhindi-abudawud:2331','deenhindi-muslim:2365','deenhindi-tirmidhi:2296']
assert reading_languages=={'hi':100,'ur':100,'ar':4,'en':4,'ur-Latn':4}
doc=(ROOT/'downloaded/docs/WEB-SOURCE-RESOLUTION-20261113.md').read_text()
assert '| **Total** | **100** | **96** | **4** | **212** | **192** | **20** | **288** |' in doc
assert '6,411 unreviewed' in doc and 'Hindi/Urdu fields across 3,404 occurrences: 3,310 Hindi and 3,101 Urdu' in doc
assert PARENT in doc and MERGE in doc and 'Derived application of these 100 reviewed decisions' in doc
assert PIN not in doc
assert sum(f['bytes'] for f in files)==180880
assert inputs=={str(p.relative_to(ROOT)):bind(p) for p in sorted((ROOT/'input').rglob('*')) if p.is_file()}

report={'schema':'hadith-bank-independent-publication-readback-v1','status':'PASS',
    'repository':'blaghtayt-alt/Hadith-Bank','commit_sha':PIN,'parent_sha':PARENT,'root_tree_sha':TREE,
    'branch_observed_sha':ref['object']['sha'],'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'publication_manifest_sha256':MANIFEST_SHA,'publication_payload_files':234,'publication_payload_bytes':6430764,
    'complete_file_bodies_downloaded_and_checked':5,'complete_file_bytes_checked':180880,
    'scope':'Four new active Deen ledgers and complete status document, with independently fetched and Git-rehashed before/after ancestral trees. Old29 active entries, canonical queue, acquisition files/subtrees, PR15 ancestry and all other top-level areas are preserved by exact Git identity. This does not claim all234 payload bodies or all old ledger bodies were downloaded again.',
    'complete_ancestral_tree_objects_verified':14,'complete_tree_entries_verified':923,
    'commit_identity_parent_root_verified_from_github_api':True,'raw_commit_object_reconstructed':False,
    'all_five_full_sha256_git_blob_and_payload_byte_equalities_pass':True,
    'all_five_paths_bound_through_complete_rehashed_trees':True,
    'new_active_ledger_counts':{'unique_occurrences':100,'duplicate_ids':0,**dict(counts),
        'complete_read_fields_by_language':dict(reading_languages),'source_only_ids':sorted(excluded),
        'sparse_decision_note':'One ledger explicitly supplies59 read fields and leaves66 other slots implicit. Native default context is preserved;434 explicit definitions are not misreported as500 explicit reviews.'},
    'old29_active_review_entries_unchanged':preserved_reviews,'canonical_priority_queue':queue_result,
    'bd4a_acquisition_entries_unchanged':source_preserved,
    'acquisition_preservation_scope':'Equal before/after blob and tree identities; the large state/progress contents were not downloaded or semantically re-audited in this readback.',
    'pr15_merge_preserved':{'merge_sha':MERGE,'merge_parents':[p['sha'] for p in merge['parents']],
        'published_to_parent_to_merge_chain':[PIN,PARENT,MERGE],
        'all_top_level_entries_other_than_docs_imports_reports_exact':True,
        'all_other_import_source_subtrees_exact':True},
    'status_document_current_count_and_derived_vs_saved_labels_checked':True,
    'directory_comparisons':comparisons,'tree_bindings':tree_bindings,'files':files,'ledger_counts':ledger_counts,
    'source_or_candidate_inputs_mutated':False,'github_writes':0,'source_site_requests':0,
    'additional_linguistic_readings_claimed':0,'native_engine_repeated_in_readback':False,
    'live_deployment_verified':False}
evidence={'schema':'hadith-bank-independent-publication-readback-evidence-v1','source':'Fresh read-only GitHub connector responses at exact published and parent snapshots.',
    'published_commit':commit,'before_commit':before_commit,'pr15_merge_commit':merge,'observed_main_ref':ref,
    'complete_tree_objects':[{'snapshot':side,'path':path,**tree} for (side,path),tree in trees.items()],
    'input_response_and_manifest_bindings':inputs,'file_body_hash_bindings':files,
    'old29_complete_entries':old29,'canonical_queue_before_entry':qe_before,'canonical_queue_after_entry':qe_after}
OUT=ROOT/'publish'
put(OUT/REL/'readback-receipt.json',enc(report))
put(OUT/REL/'readback-evidence.json.gz',gzip.compress(enc(evidence),mtime=0))
put(OUT/REL/'audit_readback.py',Path(__file__).read_bytes())
payload=[{'path':str(p.relative_to(OUT)),'local_path':str(p),**bind(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
delivery={'schema':'hadith-bank-independent-audit-delivery-v1','status':'PASS','commit_sha':PIN,
    'files':payload,'total_files':len(payload),'total_bytes':sum(r['bytes'] for r in payload)}
put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest':bind(ROOT/'delivery-manifest.json'),
    'report':bind(OUT/REL/'readback-receipt.json'),'payload_files':len(payload),
    'payload_bytes':delivery['total_bytes'],'readback_files':5,'readback_bytes':180880,
    'trees':14,'tree_entries':923,'old_reviews_unchanged':29,'new_reviews':4,
    'new_registered':96,'new_source_only':4,'canonical_queue_fields':6411},indent=2))
