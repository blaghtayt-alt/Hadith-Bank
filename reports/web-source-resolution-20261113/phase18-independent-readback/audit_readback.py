"""Independently bind five complete phase18 bodies to fresh GitHub commit/tree reads."""
from pathlib import Path
import base64,collections,datetime,gzip,hashlib,json,sys

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
PIN='d369026ca42af6ff972ffab83c9180e03759da41'
PARENT='a3f9427d7bd235d27318a9470910c182b806a26c'
SOURCE='3e574b9e7e4dd7cf8bc23232249004a18692c61c'
TREE='84b3a3b3ee1fbab4a2dbb6efbf68a69e94cc2d70'
MANIFEST_SHA='dee7cdb3be66993d8e95051553b2bdffa8215c0fdc1fe16e637d1cd77dd53093'
REVIEWS='imports/web-deenhindi-20261112/reviews'
SOURCE_DIR='imports/web-deenhindi-20261112'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
REL=Path('reports/web-source-resolution-20261113/phase18-independent-readback')
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
import import_deenhindi as importer

def sha(b):return hashlib.sha256(b).hexdigest()
def git(kind,b):return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def bind(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b),'git_blob_sha1':git('blob',b)}
def read(p):return json.loads(p.read_bytes())
def api(name):return json.loads(read(ROOT/'input'/(name+'.json'))['content'])
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,('immutable result differs',str(p))
    else:p.write_bytes(b)
def entries(tree):return {r['path']:r for r in tree['tree']}
def identity(r):return r.get('id',r.get('occurrence_id'))

manifest_raw=(ROOT/'input/manifest.json').read_bytes();assert sha(manifest_raw)==MANIFEST_SHA
manifest=json.loads(manifest_raw)
assert len(manifest['files'])==223 and sum(r['bytes'] for r in manifest['files'])==6289342
manifest_by_path={r['path']:r for r in manifest['files']};assert len(manifest_by_path)==223
targets=read(ROOT/'input/targets.json');assert len(targets)==5
assert targets==[manifest_by_path[t['path']] for t in targets]
commit=api('published-commit');before_commit=api('before-commit');source_commit=api('source-commit');ref=api('observed-main-ref')
assert commit['sha']==PIN and commit['tree']['sha']==TREE and [p['sha'] for p in commit['parents']]==[PARENT]
assert before_commit['sha']==PARENT and [p['sha'] for p in before_commit['parents']]==[SOURCE]
assert source_commit['sha']==SOURCE and source_commit['tree']['sha']=='8f45b8c41b1e7f3c1831c24b5fc053fcd7cceb4e'
assert ref['ref']=='refs/heads/main' and ref['object']['sha']==PIN

path_names={'':'root-tree','docs':'tree-docs','imports':'tree-imports',
    SOURCE_DIR:'tree-imports-web-deenhindi',REVIEWS:'tree-reviews',
    'reports':'tree-reports','reports/web-source-resolution-20261113':'tree-reports-web-source'}
trees={};tree_bindings=[]
for side in ['before','after','source']:
    paths=path_names if side!='source' else {k:v for k,v in path_names.items() if k in ('','imports',SOURCE_DIR)}
    for path,name in paths.items():
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
        else:
            expected={'after':TREE,'before':before_commit['tree']['sha'],'source':source_commit['tree']['sha']}[side]
            assert tree['sha']==expected
        tree_bindings.append({'snapshot':side,'path':path or '/','git_tree_sha1':tree['sha'],
            'complete_entries':len(original),'truncated':False,'git_tree_object_rehashed':True,
            'tree_object_bytes':len(raw),'tree_object_sha256':sha(raw),
            'saved_response_sha256':sha((ROOT/'input'/(response+'.json')).read_bytes())})
assert len(tree_bindings)==17 and sum(r['complete_entries'] for r in tree_bindings)==1041
assert len({r['git_tree_sha1'] for r in tree_bindings})==16

comparisons=[]
for path in path_names:
    a=entries(trees[('before',path)]);b=entries(trees[('after',path)])
    assert not set(a)-set(b),(path,'removed entries')
    changed={k for k in a if a[k]!=b[k]};added=set(b)-set(a)
    prefix=path+'/' if path else ''
    allowed={p[len(prefix):].split('/')[0] for p in manifest_by_path if p.startswith(prefix)}
    assert changed|added<=allowed,(path,'unpublished-path mutation',changed|added-allowed)
    comparisons.append({'path':path or '/','before_tree_sha':trees[('before',path)]['sha'],
        'after_tree_sha':trees[('after',path)]['sha'],'unchanged_existing_entries':len(a)-len(changed),
        'changed_existing_entries':sorted(changed),'added_entries':sorted(added),'removed_entries':[]})
assert comparisons[0]['changed_existing_entries']==['docs','imports','reports']
assert entries(trees[('before',SOURCE_DIR)])==entries(trees[('source',SOURCE_DIR)])

before_reviews=entries(trees[('before',REVIEWS)]);after_reviews=entries(trees[('after',REVIEWS)])
old33={k:v for k,v in before_reviews.items() if v['type']=='blob' and k.startswith('source-review-')}
all37={k:v for k,v in after_reviews.items() if v['type']=='blob' and k.startswith('source-review-')}
new_paths={t['path'] for t in targets if t['path'].startswith(REVIEWS+'/')}
assert len(old33)==33 and len(all37)==37 and set(all37)-set(old33)=={Path(p).name for p in new_paths}
prior_repo=WORK/'phase18-checkpointbd4a-independent-integration/validation/combined-reviews'
prior_preserved=[];all_prior_ids=set()
for name,item in sorted(old33.items()):
    assert item==all37[name]
    path=prior_repo/REVIEWS/name;raw=path.read_bytes();binding=bind(path)
    assert binding['git_blob_sha1']==item['sha'] and binding['bytes']==item['size']
    ledger=json.loads(gzip.decompress(raw));ids={identity(r) for r in ledger.get('records',ledger.get('decisions'))}
    assert len(ids)==len(ledger.get('records',ledger.get('decisions'))) and not ids&all_prior_ids
    all_prior_ids|=ids
    prior_preserved.append({'path':REVIEWS+'/'+name,**binding,'decisions':len(ids),
        'before_after_full_git_entry_equal':True,
        'body_origin':'Previously validated complete local body, freshly rehashed against both independently fetched trees; not redownloaded in this read-back.'})
assert len(all_prior_ids)==3318

preserved_acquisition=[]
for name,item in sorted(entries(trees[('before',SOURCE_DIR)]).items()):
    if name=='reviews':continue
    assert item==entries(trees[('after',SOURCE_DIR)])[name]==entries(trees[('source',SOURCE_DIR)])[name]
    preserved_acquisition.append({'path':SOURCE_DIR+'/'+name,'kind':item['type'],
        'git_object_sha1':item['sha'],'bytes':item.get('size'),'all_three_full_entries_equal':True})
assert len(preserved_acquisition)==12
assert {'raw','parsed','state.json','progress.json','inventory.json'}<={Path(r['path']).name for r in preserved_acquisition}

files=[]
for i,target in enumerate(targets):
    response_path=ROOT/f'input/file-{i:02d}.json';response=read(response_path)
    assert response['encoding']=='base64'
    raw=base64.b64decode(''.join(response['content'].split()),validate=True)
    assert len(raw)==target['bytes'] and sha(raw)==target['sha256']
    assert git('blob',raw)==target['git_blob_sha1']==response['sha']
    assert raw==Path(target['local_path']).read_bytes()
    downloaded=ROOT/'downloaded'/target['path'];assert downloaded.read_bytes()==raw
    folder,_,name=target['path'].rpartition('/');entry=entries(trees[('after',folder)])[name]
    assert entry['type']=='blob' and entry['sha']==response['sha'] and entry['size']==len(raw)
    ancestry=[];path=folder
    while True:
        ancestry.append({'path':path or '/','git_tree_sha1':trees[('after',path)]['sha']})
        if not path:break
        path=path.rpartition('/')[0]
    files.append({'path':target['path'],**bind(downloaded),'github_blob_sha1':response['sha'],
        'github_url':response['display_url'],'complete_bytes_match_frozen_payload':True,
        'ancestral_trees':list(reversed(ancestry)),'response_snapshot_sha256':sha(response_path.read_bytes())})
assert sum(f['bytes'] for f in files)==211885

queue_before=entries(trees[('before','reports/web-source-resolution-20261113')])[Path(QUEUE).name]
queue_after=entries(trees[('after','reports/web-source-resolution-20261113')])[Path(QUEUE).name]
assert queue_before==queue_after
queue_path=WORK/'phase17-independent-readback/downloaded'/QUEUE;qb=bind(queue_path)
assert qb['sha256']=='74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
assert qb['git_blob_sha1']==queue_before['sha'] and qb['bytes']==queue_before['size']
queue_rows=[json.loads(line) for line in gzip.decompress(queue_path.read_bytes()).splitlines()]
queue_counts=collections.Counter(f['language'] for r in queue_rows for f in r['fields'])
assert len(queue_rows)==3379 and queue_counts=={'hi':3285,'ur':3076}

source_rows={identity(r) or 'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(WORK/'phase18-checkpointbd4a-independent-integration/input/source-cohort-92.jsonl').read_bytes().splitlines())}
assert len(source_rows)==92
counts=collections.Counter();new_ids=set();new_ledger_counts=[];excluded=[]
for relative in sorted(new_paths):
    raw=(ROOT/'downloaded'/relative).read_bytes();ledger=json.loads(gzip.decompress(raw))
    records=ledger.get('records',ledger.get('decisions'));group=collections.Counter()
    for record in records:
        ident=identity(record);assert ident in source_rows and ident not in new_ids and ident not in all_prior_ids;new_ids.add(ident)
        source=source_rows[ident]['source_record']
        assert record['source_record_sha256']==sha(importer.json_bytes(source))
        action=record['decision'];assert action in ['register','exclude'];counts[action]+=1;group[action]+=1
        if action=='exclude':excluded.append(ident)
        fields={f['language']:f for f in record.get('field_reviews',record.get('fields'))}
        for language,name in importer.LANGUAGE_FIELDS.items():
            text=source[name];field=fields.get(language);counts['source_slots']+=1
            if not text:
                assert field is None;counts['empty_source_fields']+=1;continue
            counts['nonempty_source_fields']+=1
            reviewed=bool(field and field['reviewed'])
            spans=field.get('spans',field.get('selected_spans',[])) if field else []
            if field:
                assert field['source_field']==name and field['text_sha256']==sha(text.encode())
                assert field['chars_reviewed']==(len(text) if reviewed else 0)
                assert field['bytes_reviewed']==(len(text.encode()) if reviewed else 0)
            if reviewed:
                counts['read_fields']+=1;counts['read_characters']+=len(text);counts['read_utf8_bytes']+=len(text.encode())
                group['read_fields']+=1
            status='admitted_fields' if spans else 'read_context_fields' if reviewed else 'unread_context_fields'
            counts[status]+=1;group[status]+=1
            if action=='exclude':assert reviewed and not spans
            for span in spans:
                assert sha(text[span['start']:span['end']].encode())==span['sha256']
    new_ledger_counts.append({'path':relative,'records':len(records),'counts':dict(group)})
assert new_ids==set(source_rows)
expected={'register':87,'exclude':5,'source_slots':460,'nonempty_source_fields':458,'empty_source_fields':2,
          'read_fields':199,'read_characters':131417,'read_utf8_bytes':275705,
          'admitted_fields':174,'read_context_fields':25,'unread_context_fields':259}
assert all(counts[k]==v for k,v in expected.items()),dict(counts)

saved_path=WORK/'phase18-successor-acquisition-monitor/saved-checkpoint'
state_bindings=[]
for name in ['state.json','progress.json','inventory.json','retry-authorizations.json']:
    path=saved_path/name;binding=bind(path);entry=entries(trees[('after',SOURCE_DIR)])[name]
    assert entry['sha']==binding['git_blob_sha1'] and entry['size']==binding['bytes']
    state_bindings.append({'path':SOURCE_DIR+'/'+name,**binding,'body_origin':'Exact saved source-checkpoint local body freshly rehashed against the preserved Git entry; not downloaded again here.'})
progress=read(saved_path/'progress.json')
actual={k:progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked']}
assert actual=={'imported_count':17131,'registered_hadith_count':16804,'non_narration_source_entries':155,'classification_pending_count':172,'pending_fetch_count':19259,'errors_count':0,'blocked':False}
projection={'fetched':17131,'registered':16804+87,'source_only':155+5,'held':172-92,'unfetched':19259}
doc=(ROOT/'downloaded/docs/WEB-SOURCE-RESOLUTION-20261113.md').read_text()
assert '**87 registrations and five source-only dispositions**' in doc and '199 nonempty fields: 131,417 characters and 275,705 UTF-8 bytes' in doc
assert '| Registered occurrences | 16,804 | 16,891 |' in doc and '| Held occurrences | 172 | 80 |' in doc
assert 'The right-hand column is a fixed-source projection.' in doc
assert 'Publishing the decisions does not itself prove' in doc
assert '6,361 pending fields across 3,379 source occurrences: 3,285 Hindi and 3,076 Urdu' in doc

report={'schema':'hadith-bank-independent-publication-readback-v1','status':'PASS',
    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'repository':'blaghtayt-alt/Hadith-Bank','published_commit':PIN,'actual_parent_commit':PARENT,'actual_root_tree':TREE,
    'source_checkpoint':SOURCE,'observed_main_ref':ref['object']['sha'],
    'publication_manifest_sha256':MANIFEST_SHA,'publication_manifest_files':223,'publication_manifest_bytes':6289342,
    'independently_downloaded_full_bodies':5,'independently_downloaded_body_bytes':211885,'file_checks':files,
    'all_five_complete_stored_bytes_sha256_git_blob_and_frozen_payload_equal':True,
    'complete_git_tree_bindings':17,'unique_git_tree_objects':16,'complete_tree_entries_across_bindings':1041,
    'all_full_tree_objects_rehashed':True,'tree_bindings':tree_bindings,'directory_comparisons':comparisons,
    'old33_active_entries_and_complete_local_body_hashes_preserved':prior_preserved,
    'prior_manual_ids':3318,'new_manual_ids':92,'resulting_manual_ids':3410,'resulting_active_ledgers':37,
    'new_review_counts_from_complete_saved_bodies':dict(counts),'new_ledger_counts':new_ledger_counts,'source_only_ids':sorted(excluded),
    'canonical_priority_queue':{'path':QUEUE,**qb,'pending_fields':6361,'occurrences':3379,'by_language':dict(queue_counts),
        'before_after_full_git_entry_equal':True,'body_origin':'Previous independent full GitHub download, freshly rehashed against both current tree entries.'},
    'acquisition_entries_preserved_from_source_checkpoint_through_generated_parent_and_publication':preserved_acquisition,
    'selected_full_acquisition_body_bindings':state_bindings,'actual_saved_3e574_progress':actual,
    'fixed_source_projection_after_new92':projection,'projection_is_new_saved_export':False,
    'generated_reader_parent_retained_in_exact_ancestry':True,
    'all_unrelated_root_entries_including_generated_reader_and_code_preserved':True,
    'current_d369_live_deployment_verified':False,'linguistic_rereading_in_this_readback':0,'native_tests_repeated_in_this_readback':False,
    'github_writes':0,'source_site_requests':0,
    'limits':'Independent fresh GitHub reads of the exact commit/ref, before/after/source tree paths and five complete bodies only. Other223-payload-file contents rely on their frozen root manifest and are not all independently redownloaded. Existing33 bodies and queue/acquisition bytes are rehashed against fresh exact tree identities. Current saved exports, future acquisitions, live deployment and authenticity certification remain separate gates.'}
put(ROOT/'readback-receipt.json',enc(report))
input_evidence={'schema':'independent-github-readback-input-snapshots-v1',
    'content':'Exact saved connector responses including five base64 body responses; tree object shared at identical before/source SHA was fetched once and bound to both paths.',
    'inputs':{p.name:read(p) for p in sorted((ROOT/'input').glob('*.json'))}}
outputs={'readback-receipt.json':enc(report),'response-and-tree-evidence.json.gz':gzip.compress(enc(input_evidence),mtime=0),
         'audit_readback.py':Path(__file__).read_bytes()}
files_out=[]
for name,raw in outputs.items():
    path=ROOT/'publish'/REL/name;put(path,raw)
    files_out.append({'path':str(REL/name),'local_path':str(path),'source_path':str(path),**bind(path)})
delivery={'schema':'independent-github-readback-delivery-v1','status':'PASS','published_commit':PIN,
    'files':files_out,'total_files':len(files_out),'total_bytes':sum(r['bytes'] for r in files_out)}
put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(delivery)),'report_sha256':sha(enc(report)),
    'files':len(files_out),'bytes':delivery['total_bytes'],'full_bodies':5,'body_bytes':211885,
    'tree_bindings':17,'unique_tree_objects':16,'tree_entries':1041,'preserved_ledgers':33,'counts':dict(counts)}))
