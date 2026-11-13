"""Bind the published phase17 extension to complete Git trees and exact prior bytes."""
from pathlib import Path
import base64, collections, datetime, gzip, hashlib, json

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
PIN='f9be12177046e372df088f96b255fd09914fad5a'
PARENT='d0a863b0966c7eb1ae1d5c36202de282caf77cab'
TREE='dd0f6ca52b3b93b2d89e3e8509bcc5e7eea64e57'
BD4A='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
MERGE='4b61373da1cd6205270f0c87d7c502ee5b36db26'
MANIFEST_SHA='e429c03a9eea251b4e5263dde01bc44d562a325bd519c16ba5356f67f76a0f59'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
REL=Path('reports/web-source-resolution-20261113/phase17-independent-readback')

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
manifest_raw=(ROOT/'input/manifest.json').read_bytes();assert sha(manifest_raw)==MANIFEST_SHA
manifest=json.loads(manifest_raw)
assert len(manifest['files'])==69 and sum(r['bytes'] for r in manifest['files'])==7845375
manifest_by_path={r['path']:r for r in manifest['files']}
targets=read(ROOT/'input/targets.json');assert len(targets)==3
assert targets==[manifest_by_path[t['path']] for t in targets]
commit=api('published-commit');before_commit=api('before-commit');ref=api('observed-main-ref')
bd4a=api('bd4a-commit');merge=api('pr15-merge-commit')
assert commit['sha']==PIN and commit['tree']['sha']==TREE and [p['sha'] for p in commit['parents']]==[PARENT]
assert before_commit['sha']==PARENT and [p['sha'] for p in before_commit['parents']]==[BD4A]
assert bd4a['sha']==BD4A and [p['sha'] for p in bd4a['parents']]==[MERGE]
assert merge['sha']==MERGE and [p['sha'] for p in merge['parents']]==[
    'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d','7cb61d9fe46bbfab826b9b1b93c451968910cbae']
assert ref['ref']=='refs/heads/main' and ref['object']['sha']==PIN
before_provenance=read(ROOT/'input/before-response-provenance.json')
for item in before_provenance:
    current=ROOT/'input'/item['current_input'];prior=Path(item['prior_independent_response'])
    assert current.read_bytes()==prior.read_bytes()
    assert sha(current.read_bytes())==item['sha256'] and item['same_immutable_commit']==PARENT

path_names={'':'root-tree','docs':'tree-docs','imports':'tree-imports',
    'imports/web-deenhindi-20261112':'tree-imports-web-deenhindi',
    'imports/web-deenhindi-20261112/reviews':'tree-reviews',
    'reports':'tree-reports','reports/web-source-resolution-20261113':'tree-reports-web-source'}
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
            parent,_,name=path.rpartition('/');entry=entries(trees[(side,parent)])[name]
            assert entry['type']=='tree' and entry['sha']==tree['sha']
        else:assert tree['sha']==(TREE if side=='after' else before_commit['tree']['sha'])
        tree_bindings.append({'snapshot':side,'path':path or '/','git_tree_sha1':tree['sha'],
            'complete_entries':len(original),'truncated':False,'git_tree_object_rehashed':True,
            'tree_object_sha256':sha(raw),'tree_object_bytes':len(raw)})
assert len(tree_bindings)==14 and sum(r['complete_entries'] for r in tree_bindings)==961

def compare_directory(path,changed=(),added=()):
    a=entries(trees[('before',path)]);b=entries(trees[('after',path)])
    assert not set(a)-set(b),(path,'removed entries')
    actual_changed={k for k in a if a[k]!=b[k]};actual_added=set(b)-set(a)
    assert actual_changed==set(changed),(path,actual_changed)
    assert actual_added==set(added),(path,actual_added)
    return {'path':path or '/','before_tree_sha':trees[('before',path)]['sha'],
        'after_tree_sha':trees[('after',path)]['sha'],'unchanged_existing_entries':len(a)-len(changed),
        'changed_existing_entries':sorted(changed),'added_entries':sorted(added),'removed_entries':[]}

reviews_path=ACTIVE.rpartition('/')[0]
comparisons=[compare_directory('',('docs','imports','reports')),
    compare_directory('docs',('WEB-SOURCE-RESOLUTION-20261113.md',)),
    compare_directory('imports',('web-deenhindi-20261112',)),
    compare_directory('imports/web-deenhindi-20261112',('reviews',)),
    compare_directory(reviews_path,('field-expansions',Path(ACTIVE).name)),
    compare_directory('reports',('web-source-resolution-20261113',)),
    compare_directory('reports/web-source-resolution-20261113',(Path(QUEUE).name,),
        ('original-bukhari25-50-independent-audit','phase16-independent-readback','phase17-publication-inputs-v1'))]
before_reviews=entries(trees[('before',reviews_path)]);after_reviews=entries(trees[('after',reviews_path)])
old33={k:v for k,v in before_reviews.items() if k.startswith('source-review-')}
new33={k:v for k,v in after_reviews.items() if k.startswith('source-review-')}
assert set(old33)==set(new33) and len(old33)==33
preserved_reviews=[]
for name,item in sorted(old33.items()):
    if name==Path(ACTIVE).name:continue
    assert item==new33[name]
    preserved_reviews.append({'path':reviews_path+'/'+name,'git_blob_sha1':item['sha'],
        'bytes':item.get('size'),'before_after_full_entry_equal':True})
assert len(preserved_reviews)==32
source_dir='imports/web-deenhindi-20261112'
source_before=entries(trees[('before',source_dir)]);source_after=entries(trees[('after',source_dir)])
source_preserved=[]
for name,item in sorted(source_before.items()):
    if name=='reviews':continue
    assert item==source_after[name]
    source_preserved.append({'path':source_dir+'/'+name,'kind':item['type'],'git_object_sha1':item['sha'],
        'bytes':item.get('size'),'before_after_full_entry_equal':True})
assert len(source_preserved)==12
assert {'state.json','progress.json','raw','parsed'}<={Path(r['path']).name for r in source_preserved}

files=[]
for index,target in enumerate(targets):
    response_path=ROOT/f'input/file-{index:02d}.json';response=read(response_path)
    assert response['encoding']=='base64';raw=base64.b64decode(''.join(response['content'].split()),validate=True)
    assert len(raw)==target['bytes'] and sha(raw)==target['sha256']
    assert git('blob',raw)==target['git_blob_sha1']==response['sha']
    assert raw==Path(target['local_path']).read_bytes()
    downloaded=ROOT/'downloaded'/target['path'];assert downloaded.read_bytes()==raw
    folder,_,name=target['path'].rpartition('/');entry=entries(trees[('after',folder)])[name]
    assert entry['type']=='blob' and entry['sha']==response['sha'] and entry['size']==len(raw)
    ancestry=[];path=folder
    while True:
        ancestry.append({'path':path or '/','sha':trees[('after',path)]['sha']})
        if not path:break
        path=path.rpartition('/')[0]
    files.append({'path':target['path'],**bind(downloaded),'github_blob_sha1':response['sha'],
        'github_url':response['display_url'],'full_bytes_match_frozen_payload':True,
        'ancestral_trees':list(reversed(ancestry)),'response_snapshot_sha256':sha(response_path.read_bytes())})
assert sum(f['bytes'] for f in files)==1194770

before_active=WORK/'phase15-independent-readback/downloaded'/ACTIVE
before_queue=WORK/'phase15-independent-readback/downloaded'/QUEUE
prior_body_bindings=[]
for p,path,expected in [(before_active,ACTIVE,'ac53483e3eab6c0a4c508c86180c75091792e895b5e29f602a061aa2cd080c62'),
        (before_queue,QUEUE,'343e72455fe122b59b37d795a59f9f8cca2358077723f1c725e4b1eaa3f57227')]:
    raw=p.read_bytes();assert sha(raw)==expected
    folder,_,name=path.rpartition('/');entry=entries(trees[('before',folder)])[name]
    assert git('blob',raw)==entry['sha'] and len(raw)==entry['size']
    prior_body_bindings.append({'path':path,**bind(p),'before_commit_git_entry_match':True,
        'origin':'Complete independently downloaded prior immutable GitHub bytes, rehashed against the exact d0a863 parent tree; body not redownloaded.'})
old=json.loads(gzip.decompress(before_active.read_bytes()))
new=json.loads(gzip.decompress((ROOT/'downloaded'/ACTIVE).read_bytes()))
assert {k:v for k,v in old.items() if k not in ['records','field_review_extensions']}=={k:v for k,v in new.items() if k not in ['records','field_review_extensions']}
assert new['field_review_extensions'][:-1]==old['field_review_extensions'] and len(new['field_review_extensions'])==len(old['field_review_extensions'])+1
selection_path=WORK/'phase17-original-bukhari25-hi-ur/input/selection.json';selection=read(selection_path)
selected={r['id'] for r in selection['selected']};assert len(selected)==25
reading_path=WORK/'phase17-original-bukhari25-hi-ur/input/full-hi-ur-reading-input-50.jsonl'
reading={(r['occurrence_id'],r['language']):r for r in map(json.loads,reading_path.read_text().splitlines())}
assert len(reading)==50 and {i for i,l in reading}==selected
assert list(r['occurrence_id'] for r in old['records'])==list(r['occurrence_id'] for r in new['records'])
assert len(old['records'])==len(new['records'])==len({r['occurrence_id'] for r in new['records']})==477
changed_fields=[];unchanged_fields=0;unchanged_parents=0;new_spans=0;context_gaps=0;chars=0;utf8=0
for a,b in zip(old['records'],new['records']):
    identity=a['occurrence_id'];assert a['decision']==b['decision']=='register'
    assert {k:v for k,v in a.items() if k!='fields'}=={k:v for k,v in b.items() if k!='fields'}
    assert [f['language'] for f in a['fields']]==[f['language'] for f in b['fields']]
    assert len(a['fields'])==len(b['fields'])==5
    if identity not in selected:assert a==b;unchanged_parents+=1
    for x,y in zip(a['fields'],b['fields']):
        lang=x['language'];key=(identity,lang)
        if key not in reading:assert x==y;unchanged_fields+=1;continue
        assert x!=y and x['reviewed'] is False and x['selected_spans']==[]
        r=reading[key];text=r['text'];raw=text.encode();assert sha(raw)==r['text_sha256']==x['text_sha256']==y['text_sha256']
        assert y['reviewed'] is True and y['chars_reviewed']==len(text)==r['characters']
        assert y['bytes_reviewed']==len(raw)==r['utf8_bytes'] and y['selected_spans']
        for key2 in ['field_path','language','source_field','text_chars','text_sha256','version_id']:
            assert x[key2]==y[key2]
        cursor=0;local_gaps=0
        for span in y['selected_spans']:
            start,end=span['start'],span['end'];assert cursor<=start<end<=len(text)
            assert sha(text[start:end].encode())==span['sha256']
            if start>cursor:local_gaps+=1
            cursor=end
        if cursor<len(text):local_gaps+=1
        context_gaps+=local_gaps;new_spans+=len(y['selected_spans']);chars+=len(text);utf8+=len(raw)
        changed_fields.append({'id':identity,'language':lang,'source_record_sha256':b['source_record_sha256'],
            'text_sha256':y['text_sha256'],'characters':len(text),'utf8_bytes':len(raw),
            'selected_spans':len(y['selected_spans']),'context_gaps':local_gaps,
            'before_field_sha256':sha(enc(x)),'after_field_sha256':sha(enc(y))})
assert unchanged_parents==452 and unchanged_fields==2335
assert len(changed_fields)==50 and chars==40338 and utf8==86636 and new_spans==89 and context_gaps==32
assert collections.Counter(f['language'] for f in changed_fields)=={'hi':25,'ur':25}
old_lines=gzip.decompress(before_queue.read_bytes()).splitlines(keepends=True)
new_bytes=gzip.decompress((ROOT/'downloaded'/QUEUE).read_bytes());new_lines=new_bytes.splitlines(keepends=True)
old_rows=list(map(json.loads,old_lines));new_rows=list(map(json.loads,new_lines))
assert len(old_rows)==len({r['id'] for r in old_rows})==3404
assert len(new_rows)==len({r['id'] for r in new_rows})==3379
removed=[r for r in old_rows if r['id'] in selected]
assert len(removed)==25 and {r['id'] for r in removed}==selected
assert all({f['language'] for f in r['fields']}=={'hi','ur'} and len(r['fields'])==2 for r in removed)
assert b''.join(line for line,row in zip(old_lines,old_rows) if row['id'] not in selected)==new_bytes
before_lang=collections.Counter(f['language'] for r in old_rows for f in r['fields'])
after_lang=collections.Counter(f['language'] for r in new_rows for f in r['fields'])
assert before_lang=={'hi':3310,'ur':3101} and after_lang=={'hi':3285,'ur':3076}
queue_result={'path':QUEUE,**bind(ROOT/'downloaded'/QUEUE),'before_fields':6411,'after_fields':6361,
    'before_occurrences':3404,'after_occurrences':3379,'before_by_language':dict(before_lang),
    'after_by_language':dict(after_lang),'exact_removed_fields':50,'exact_removed_occurrences':25,
    'removed_occurrence_ids':sorted(selected),'all_remaining_decompressed_line_bytes_and_order_exact':True}
doc=(ROOT/'downloaded/docs/WEB-SOURCE-RESOLUTION-20261113.md').read_text()
for fragment in ['| Complete source fields read and admitted | 25 | 25 | 50 |',
        '| Total pending fields | 6,411 | 6,361 |',
        '| Occurrences with pending priority fields | 3,404 | 3,379 |',
        'It does not add newly fetched occurrences or','all 477 existing',
        PARENT,'Derived application of these 100 reviewed decisions']:
    assert fragment in doc,fragment
assert PIN not in doc
assert inputs=={str(p.relative_to(ROOT)):bind(p) for p in sorted((ROOT/'input').rglob('*')) if p.is_file()}

report={'schema':'hadith-bank-independent-publication-readback-v1','status':'PASS',
    'repository':'blaghtayt-alt/Hadith-Bank','commit_sha':PIN,'parent_sha':PARENT,'root_tree_sha':TREE,
    'branch_observed_sha':ref['object']['sha'],'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'publication_manifest_sha256':MANIFEST_SHA,'publication_payload_files':69,'publication_payload_bytes':7845375,
    'complete_file_bodies_downloaded_and_checked':3,'complete_file_bytes_checked':1194770,
    'scope':'Complete published original477 active ledger, canonical priority queue and status document. All three bodies match the frozen payload and complete rehashed ancestral Git trees. Other32 active review entries and all acquisition entries remain identical. This is not a claim that all69 payload bodies or every old ledger/source body were downloaded again.',
    'before_snapshot_provenance':'Complete before responses were independently fetched for this exact immutable d0a863 commit in the immediately preceding phase16 audit and were copied and rehashed here; after responses and the three after bodies were fetched freshly for phase17.',
    'complete_ancestral_tree_objects_verified':14,'complete_tree_entries_verified':961,
    'commit_identity_parent_root_verified_from_github_api':True,'raw_commit_object_reconstructed':False,
    'all_three_full_sha256_git_blob_and_payload_byte_equalities_pass':True,
    'all_three_paths_bound_through_complete_rehashed_trees':True,
    'published_extension_comparison':{'active_path':ACTIVE,'occurrences':477,'registered_before':477,'registered_after':477,
        'parent_disposition_delta':0,'all_parent_metadata_exact':True,'untouched_whole_parents':452,
        'unchanged_other_explicit_field_definitions':2335,'new_complete_reviewed_and_admitted_fields':50,
        'new_fields_by_language':{'hi':25,'ur':25},'new_source_characters_reviewed':40338,
        'new_source_utf8_bytes_reviewed':86636,'new_selected_spans':89,'new_preserved_context_gaps':32,
        'selected_source_hashes_and_every_selected_span_hash_verified':True,
        'previous_top_level_metadata_and_extension_history_preserved':True,
        'sourcefetch_delta_from_this_publication':0,'changed_fields':changed_fields},
    'other32_active_review_entries_unchanged':preserved_reviews,'canonical_priority_queue':queue_result,
    'acquisition_entries_unchanged':source_preserved,
    'acquisition_preservation_scope':'Exact before/after blob and subtree identities, including state, progress, raw and parsed. Large acquisition contents were not downloaded or semantically re-audited here.',
    'pr15_and_bd4a_preserved':{'published_ancestry':[PIN,PARENT,BD4A,MERGE],
        'merge_parents':[p['sha'] for p in merge['parents']],
        'all_top_level_entries_other_than_docs_imports_reports_exact':True,'all_other_import_source_subtrees_exact':True},
    'status_document_counts_and_no_new_sourcefetch_labels_checked':True,
    'directory_comparisons':comparisons,'tree_bindings':tree_bindings,'files':files,
    'before_complete_body_hash_bindings':prior_body_bindings,
    'original_selection_binding':bind(selection_path),'original_reading_packet_binding':bind(reading_path),
    'source_or_candidate_inputs_mutated':False,'github_writes':0,'source_site_requests':0,
    'additional_linguistic_readings_claimed':0,'native_engine_repeated_in_readback':False,
    'live_deployment_verified':False}
evidence={'schema':'hadith-bank-independent-publication-readback-evidence-v1',
    'source':'Read-only pinned GitHub responses. Fresh phase17 after responses; rehashed exact same-commit before responses from preceding independent audit.',
    'published_commit':commit,'before_commit':before_commit,'bd4a_commit':bd4a,'pr15_merge_commit':merge,
    'observed_main_ref':ref,'before_response_provenance':before_provenance,
    'complete_tree_objects':[{'snapshot':side,'path':path,**tree} for (side,path),tree in trees.items()],
    'input_response_and_manifest_bindings':inputs,'file_body_hash_bindings':files,
    'other32_complete_entries':{k:v for k,v in old33.items() if k!=Path(ACTIVE).name},
    'before_complete_body_hash_bindings':prior_body_bindings}
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
    'payload_bytes':delivery['total_bytes'],'readback_bytes':1194770,'trees':14,'tree_entries':961}))
