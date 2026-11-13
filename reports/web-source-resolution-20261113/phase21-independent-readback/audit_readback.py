"""Fresh independent phase21 commit/tree/body read-back, with frozen prior-byte proofs."""
from pathlib import Path
import base64,collections,datetime,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
PIN='7a3462ef5513e3c116ead9a496420e8b9f484841'
PARENT='64f4ed50ed6026855237a5d547a86dd03e73f804'
BASELINE='b7f21cbdd84fc922575b946e92b246e2665478ab'
TREE='6829cc1d072631e6526ff0d9218a08c12fd5b406'
MANIFEST_SHA='adf7c5382ea9952afe3b4c4187587f93af388d26d6fdff04b43ed249c875c503'
REVIEWS='imports/web-deenhindi-20261112/reviews';SOURCE_DIR='imports/web-deenhindi-20261112'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
REL=Path('reports/web-source-resolution-20261113/phase21-independent-readback')
sys.dont_write_bytecode=True;sys.path.insert(0,str(WORK/'hindi-resolve/work/scripts'))
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
def ident(r):return r.get('id',r.get('occurrence_id'))

manifest_raw=(ROOT/'input/manifest.json').read_bytes();assert sha(manifest_raw)==MANIFEST_SHA
manifest=json.loads(manifest_raw);manifest_by={r['path']:r for r in manifest['files']}
assert len(manifest_by)==len(manifest['files'])==288 and sum(r['bytes'] for r in manifest['files'])==8233410
targets=read(ROOT/'input/targets.json');assert len(targets)==5 and targets==[manifest_by[t['path']] for t in targets]
published=api('published-commit');before=api('before-commit');baseline=api('baseline-commit');ref=api('observed-main-ref')
assert published['sha']==PIN and published['tree']['sha']==TREE and [p['sha'] for p in published['parents']]==[PARENT]
assert before['sha']==PARENT and [p['sha'] for p in before['parents']]==[BASELINE]
assert baseline['sha']==BASELINE and baseline['tree']['sha']=='0d477db71751c7be91d761aae27f93b1fbcd9aeb'
assert ref['ref']=='refs/heads/main' and ref['object']['sha']==PIN
paths={'':'root-tree','docs':'tree-docs','imports':'tree-imports','reports':'tree-reports',
       SOURCE_DIR:'tree-imports-web-deenhindi','reports/web-source-resolution-20261113':'tree-reports-web-source',REVIEWS:'tree-reviews'}
trees={};tree_bindings=[]
for side in ['baseline','before','after']:
    for path,suffix in paths.items():
        name=side+'-'+suffix;tree=api(name);trees[(side,path)]=tree
        assert tree['truncated'] is False
        assert len({e['path'] for e in tree['tree']})==len(tree['tree'])
        assert all('/' not in e['path'] and '\0' not in e['path'] for e in tree['tree'])
        ordered=sorted(tree['tree'],key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
        raw=b''.join((e['mode'].lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in ordered)
        assert git('tree',raw)==tree['sha'],(side,path)
        if path:
            parent,_,leaf=path.rpartition('/');e=entries(trees[(side,parent)])[leaf]
            assert e['type']=='tree' and e['sha']==tree['sha']
        else:assert tree['sha']=={'baseline':baseline,'before':before,'after':published}[side]['tree']['sha']
        tree_bindings.append({'snapshot':side,'path':path or '/','git_tree_sha1':tree['sha'],'complete_entries':len(tree['tree']),
            'truncated':False,'complete_tree_object_rehashed':True,'tree_object_bytes':len(raw),'tree_object_sha256':sha(raw),
            'saved_response_sha256':sha((ROOT/'input'/(name+'.json')).read_bytes())})
assert len(tree_bindings)==21
comparisons=[]
for path in paths:
    a=entries(trees[('before',path)]);b=entries(trees[('after',path)])
    assert not set(a)-set(b)
    changed={k for k in a if a[k]!=b[k]};added=set(b)-set(a)
    prefix=path+'/' if path else '';allowed={p[len(prefix):].split('/')[0] for p in manifest_by if p.startswith(prefix)}
    assert (changed|added)<=allowed,(path,changed,added,allowed)
    comparisons.append({'path':path or '/','before_tree':trees[('before',path)]['sha'],'after_tree':trees[('after',path)]['sha'],
        'changed_existing_entries':sorted(changed),'added_entries':sorted(added),'removed_entries':[],
        'unchanged_existing_entries':len(a)-len(changed)})
assert comparisons[0]['changed_existing_entries']==['docs','imports','reports']
assert entries(trees[('before','')])['materials']==entries(trees[('after','')])['materials']
rootbase=entries(trees[('baseline','')]);rootbefore=entries(trees[('before','')])
assert set(rootbase)==set(rootbefore)
assert {k for k in rootbase if rootbase[k]!=rootbefore[k]}=={'imports','materials'}
for path in ['docs','reports','reports/web-source-resolution-20261113',REVIEWS]:
    assert entries(trees[('baseline',path)])==entries(trees[('before',path)])
acq_changes=[]
for path in ['imports',SOURCE_DIR]:
    a=entries(trees[('baseline',path)]);b=entries(trees[('before',path)]);assert set(a)==set(b)
    acq_changes.append({'path':path,'changed_entries':sorted(k for k in a if a[k]!=b[k]),'no_entry_added_or_removed':True})
assert acq_changes[0]['changed_entries']==['web-deenhindi-20261112','web-import-status.json']
aggregate_status=entries(trees[('before','imports')])['web-import-status.json']
assert aggregate_status==entries(trees[('after','imports')])['web-import-status.json']

old_entries=entries(trees[('before',REVIEWS)]);new_entries=entries(trees[('after',REVIEWS)])
old41={k:v for k,v in old_entries.items() if v['type']=='blob' and k.startswith('source-review-')}
all45={k:v for k,v in new_entries.items() if v['type']=='blob' and k.startswith('source-review-')}
new_paths={t['path'] for t in targets if t['path'].startswith(REVIEWS+'/')}
assert len(old41)==41 and len(all45)==45 and set(all45)-set(old41)=={Path(p).name for p in new_paths}
prior_repo=WORK/'phase21-checkpoint0d2fa-independent-integration/validation/published-reviews'
prior=[];old_ids=set();old477=[]
for name,e in sorted(old41.items()):
    assert e==all45[name]==entries(trees[('baseline',REVIEWS)])[name]
    path=prior_repo/REVIEWS/name;b=bind(path)
    assert b['git_blob_sha1']==e['sha'] and b['bytes']==e['size']
    l=json.loads(gzip.decompress(path.read_bytes()));records=l.get('records',l.get('decisions'));ids={ident(r) for r in records}
    assert len(ids)==len(records) and not old_ids&ids;old_ids|=ids
    item={'path':REVIEWS+'/'+name,**b,'decisions':len(records),'baseline_before_after_entries_equal':True,
          'body_origin':'Existing fully validated local body freshly rehashed against all three independent complete Git tree entries; not redownloaded here.'}
    prior.append(item)
    if b['sha256']=='6d099f91f2e406b6ca026930f4437cc1ce3983e26883cfedc3049f9cbb2f91a7':old477.append(item)
assert len(old_ids)==3490 and len(old477)==1 and old477[0]['decisions']==477

files=[]
for i,t in enumerate(targets):
    response_path=ROOT/f'input/file-{i:02d}.json';r=read(response_path);assert r['encoding']=='base64'
    raw=base64.b64decode(''.join(r['content'].split()),validate=True)
    assert len(raw)==t['bytes'] and sha(raw)==t['sha256'] and git('blob',raw)==t['git_blob_sha1']==r['sha']
    downloaded=ROOT/'downloaded'/t['path'];assert raw==downloaded.read_bytes()==Path(t['local_path']).read_bytes()
    folder,_,name=t['path'].rpartition('/');e=entries(trees[('after',folder)])[name]
    assert e['type']=='blob' and e['sha']==r['sha'] and e['size']==len(raw)
    ancestry=[];path=folder
    while True:
        ancestry.append({'path':path or '/','git_tree_sha1':trees[('after',path)]['sha']})
        if not path:break
        path=path.rpartition('/')[0]
    files.append({'path':t['path'],**bind(downloaded),'github_url':r['display_url'],'github_blob_sha1':r['sha'],
        'complete_body_matches_frozen_payload':True,'complete_ancestor_objects':list(reversed(ancestry)),
        'connector_response_sha256':sha(response_path.read_bytes())})
assert sum(f['bytes'] for f in files)==233161
qentry=entries(trees[('before','reports/web-source-resolution-20261113')])[Path(QUEUE).name]
assert qentry==entries(trees[('after','reports/web-source-resolution-20261113')])[Path(QUEUE).name]==entries(trees[('baseline','reports/web-source-resolution-20261113')])[Path(QUEUE).name]
qpath=WORK/'phase20-independent-readback/downloaded'/QUEUE;qb=bind(qpath)
assert qb['git_blob_sha1']==qentry['sha'] and qb['bytes']==qentry['size'] and qb['sha256']=='8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349'
qrows=[json.loads(l) for l in gzip.decompress(qpath.read_bytes()).splitlines()]
qcounts=collections.Counter(f['language'] for r in qrows for f in r['fields'])
assert len(qrows)==3354 and qcounts=={'hi':3260,'ur':3051}

source_rows={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,(WORK/'phase21-checkpoint0d2fa-independent-integration/input/source-cohort-86.jsonl').read_bytes().splitlines())}
assert len(source_rows)==86
counts=collections.Counter();new_ids=set();groups=[];excluded=[];source_binding_forms=collections.Counter()
for relative in sorted(new_paths):
    ledger=json.loads(gzip.decompress((ROOT/'downloaded'/relative).read_bytes()));rows=ledger.get('records',ledger.get('decisions'));group=collections.Counter()
    for record in rows:
        key=ident(record);assert key in source_rows and key not in new_ids and key not in old_ids;new_ids.add(key)
        source=source_rows[key]['source_record'];assert record['source_record_sha256']==sha(importer.json_bytes(source))
        row=source_rows[key]
        assert record['source_reference_verbatim']==row['source_reference_verbatim']
        if 'source_snapshot' in record:
            assert record['source_snapshot']==row['snapshot']
            source_binding_forms['complete_snapshot_descriptor']+=1
        else:
            assert record['source_snapshot_sha256']==row['snapshot']['sha256']
            assert record['source_record_url']==row['snapshot']['url']
            assert record['source_parsed_path']==row['parsed_path']
            assert record['source_parsed_sha256']==Path(row['parsed_path']).name.removesuffix('.json.gz')
            source_binding_forms['snapshot_hash_url_and_parsed_identity']+=1
        action=record['decision'];assert action in ['register','exclude'];counts[action]+=1;group[action]+=1
        if action=='exclude':excluded.append(key)
        fields={f['language']:f for f in record.get('field_reviews',record.get('fields'))}
        for lang,name in importer.LANGUAGE_FIELDS.items():
            text=source[name];field=fields.get(lang);counts['source_slots']+=1
            assert text
            reviewed=bool(field and field['reviewed']);spans=field.get('spans',field.get('selected_spans',[])) if field else []
            if field:
                assert field['source_field']==name and field['text_sha256']==sha(text.encode())
                assert field['chars_reviewed']==(len(text) if reviewed else 0) and field['bytes_reviewed']==(len(text.encode()) if reviewed else 0)
                counts['explicit_field_decisions']+=1
            else:counts['implicit_unread_context_slots']+=1
            if reviewed:
                counts['read_fields']+=1;counts['read_characters']+=len(text);counts['read_utf8_bytes']+=len(text.encode());group['read_fields']+=1
            status='admitted_fields' if spans else 'read_context_fields' if reviewed else 'unread_context_fields'
            counts[status]+=1;group[status]+=1
            if action=='exclude':assert reviewed and not spans
            for span in spans:
                assert sha(text[span['start']:span['end']].encode())==span['sha256'];counts['selected_spans']+=1
    groups.append({'path':relative,'records':len(rows),'counts':dict(group)})
assert new_ids==set(source_rows)
expected={'register':84,'exclude':2,'source_slots':430,'read_fields':190,'read_characters':84550,'read_utf8_bytes':178462,
          'admitted_fields':173,'read_context_fields':17,'unread_context_fields':240,'selected_spans':282,
          'explicit_field_decisions':388,'implicit_unread_context_slots':42}
assert dict(counts)==expected,dict(counts)
assert source_binding_forms=={'complete_snapshot_descriptor':68,'snapshot_hash_url_and_parsed_identity':18}
assert sorted(excluded)==['deenhindi-abudawud:2582','deenhindi-abudawud:2617']

acquisition=[]
for name,e in sorted(entries(trees[('before',SOURCE_DIR)]).items()):
    if name=='reviews':continue
    assert e==entries(trees[('after',SOURCE_DIR)])[name]
    acquisition.append({'path':SOURCE_DIR+'/'+name,'kind':e['type'],'git_object_sha1':e['sha'],'bytes':e.get('size'),'before_after_full_entry_equal':True})
assert len(acquisition)==12
saved=WORK/'phase22-successor-acquisition-monitor/saved-checkpoint';saved_bindings=[]
for name in ['state.json','progress.json']:
    b=bind(saved/name);e=entries(trees[('after',SOURCE_DIR)])[name]
    assert b['git_blob_sha1']==e['sha'] and b['bytes']==e['size']
    saved_bindings.append({'path':SOURCE_DIR+'/'+name,**b,'body_origin':'Existing saved64f4 bytes freshly rehashed against preserved Git tree identity; no full-state history comparison is claimed here.'})
progress=read(saved/'progress.json')
actual={k:progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked']}
assert actual=={'imported_count':18570,'registered_hadith_count':18132,'non_narration_source_entries':165,'classification_pending_count':273,'pending_fetch_count':17820,'errors_count':0,'blocked':False}
doc=(ROOT/'downloaded'/DOC).read_bytes();old_doc=(WORK/'phase20-independent-readback/downloaded'/DOC).read_bytes()
assert len(doc)==121575 and sha(doc)=='69767930e7c653ae36473427286132defcc783c62f8902c600bb6478fc73b2c4'
assert len(old_doc)==111201 and doc.endswith(old_doc)
old_doc_b=bind(WORK/'phase20-independent-readback/downloaded'/DOC)
assert entries(trees[('before','docs')])[Path(DOC).name]['sha']==old_doc_b['git_blob_sha1']
prefix=doc[:-len(old_doc)].decode()
assert '| Total |86|84|2|190|173|17|240|' in prefix and '84,550 characters and 178,462 UTF-8 bytes' in prefix
assert '6,311 fields' in prefix and '3,260 Hindi fields plus 3,051 Urdu fields' in prefix
assert 'full state audit is separate and still in progress' in prefix and 'not presented as the latest post-64f4 export' in prefix
assert 'not a newly saved export' in prefix and 'No b7f21 or phase21 live-site publication is claimed' in prefix
report={'schema':'hadith-bank-independent-publication-readback-v1','status':'PASS','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repository':'blaghtayt-alt/Hadith-Bank','published_commit':PIN,'actual_parent_commit':PARENT,'actual_root_tree':TREE,'prior_review_baseline_commit':BASELINE,
 'observed_main_ref':ref['object']['sha'],'publication_manifest_sha256':MANIFEST_SHA,'payload_files':288,'payload_bytes':8233410,
 'independently_downloaded_complete_bodies':5,'independently_downloaded_body_bytes':233161,'file_checks':files,
 'all_complete_body_bytes_sha256_git_blob_and_payload_equal':True,'complete_git_tree_bindings':len(tree_bindings),
 'unique_git_tree_objects':len({x['git_tree_sha1'] for x in tree_bindings}),'complete_entries_across_bindings':sum(x['complete_entries'] for x in tree_bindings),
 'tree_bindings':tree_bindings,'directory_comparisons':comparisons,'all_full_tree_objects_locally_rehashed':True,
 'all41_prior_active_entries_and_full_local_body_hashes_preserved':prior,'prior_manual_ids':3490,'new_manual_ids':86,'resulting_manual_ids':3576,'resulting_active_ledgers':45,
 'original477_ledger_preserved':old477[0],'canonical_priority_queue':{'path':QUEUE,**qb,'pending_fields':6311,'occurrences':3354,'by_language':dict(qcounts),'baseline_before_after_exact_entry_equal':True},
 'new_counts_from_fresh_complete_bodies':dict(counts),'new_ledger_counts':groups,'source_only_ids':sorted(excluded),
 'exact_source_provenance_binding_forms':dict(source_binding_forms),
 'source64f4_all12_nonreview_entries_preserved':acquisition,'source64f4_materials_entry_preserved':entries(trees[('after','')])['materials'],
 'source64f4_aggregate_web_import_status_preserved':aggregate_status,
 'source64f4_local_body_bindings':saved_bindings,'actual_saved64f4_progress_from_hash_bound_body':actual,'full64f4_history_audit_performed_here':False,
 'source_successor_between_review_publications_retained_in_ancestry':True,'baseline_to_source_directory_changes':acq_changes,
 'previous_document_bytes':len(old_doc),'previous_document_sha256':sha(old_doc),'all_previous_document_bytes_exact_suffix':True,'new_prefix_bytes':len(doc)-len(old_doc),
 'new_document_current_vs_historical_projection_scope_checked':True,'current_publication_live_deployment_verified':False,
 'linguistic_rereadings_in_this_readback':0,'native_tests_repeated_in_this_readback':False,'source_site_requests':0,'github_writes':0,
 'limits':'Fresh independent GitHub commit/ref,21 complete path-tree bindings and five full body reads. The remaining283 payload-file bodies rely on the frozen publication manifest and were not all independently downloaded. Prior41 ledgers,original477,queue and saved64f4 state/progress are independently rehashed local bytes bound to freshly fetched exact Git identities. Full64f4 history/cohort comparison, future source acquisition, native semantic gates, authenticity and live deployment remain separate evidence.'}
raw=enc(report);put(ROOT/'readback-receipt.json',raw)
evidence={'schema':'independent-github-readback-input-snapshots-v1','source':'Exact connector responses; identical ancestor tree objects were retrieved once and bound to each observed path.','inputs':{p.name:read(p) for p in sorted((ROOT/'input').glob('*.json'))}}
outputs={'readback-receipt.json':raw,'response-and-tree-evidence.json.gz':gzip.compress(enc(evidence),mtime=0),'audit_readback.py':Path(__file__).read_bytes()}
out=[]
for name,b in outputs.items():
    p=ROOT/'publish'/REL/name;put(p,b);out.append({'path':str(REL/name),'local_path':str(p),'source_path':str(p),**bind(p)})
delivery={'schema':'independent-github-readback-delivery-v1','status':'PASS','published_commit':PIN,'files':out,'total_files':len(out),'total_bytes':sum(x['bytes'] for x in out)}
put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(delivery)),'report_sha256':sha(raw),'files':len(out),'bytes':delivery['total_bytes'],
 'complete_tree_bindings':len(tree_bindings),'unique_trees':report['unique_git_tree_objects'],'prior_ledgers':41,'prior_ids':3490,'new_ids':86,'body_bytes':233161}))
