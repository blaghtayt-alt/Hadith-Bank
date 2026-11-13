"""Fresh bounded publication read-back; actual merge-parent exports remain distinct."""
from pathlib import Path
import base64,collections,datetime,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
PIN='31c01136611b163683a01b47833bf74354820851'
PARENT='a6c52f35a320b10259bc7cc6200c53118d77f149'
GENERATED='d304bef0c7955377026a0c2aeebdd677b1e05b0a'
BASELINE='7a3462ef5513e3c116ead9a496420e8b9f484841'
TREE='ef2a623731fad42608136ccff3118e174e47d0b1'
MANIFEST_SHA='543618ee8e8ab422a6e647cecda5925263d9447cf79c3cddf3e4d7aef1fa47c3'
REVIEWS='imports/web-deenhindi-20261112/reviews';SOURCE_DIR='imports/web-deenhindi-20261112'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
REL=Path('reports/web-source-resolution-20261113/phase22-independent-readback')
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
def entries(t):return {r['path']:r for r in t['tree']}
def ident(r):return r.get('id',r.get('occurrence_id'))

manifest_raw=(ROOT/'input/manifest.json').read_bytes();assert sha(manifest_raw)==MANIFEST_SHA
manifest=json.loads(manifest_raw);manifest_by={r['path']:r for r in manifest['files']}
assert len(manifest_by)==len(manifest['files'])==292 and sum(r['bytes'] for r in manifest['files'])==8208274
targets=read(ROOT/'input/targets.json');assert len(targets)==5 and targets==[manifest_by[t['path']] for t in targets]
commits={s:api(n) for s,n in {'after':'published-commit','before':'before-commit','generated':'generated-commit','baseline':'baseline-commit'}.items()}
ref=api('observed-main-ref')
assert commits['after']['sha']==PIN and commits['after']['tree']['sha']==TREE
assert [p['sha'] for p in commits['after']['parents']]==[PARENT]
assert commits['before']['sha']==PARENT and [p['sha'] for p in commits['before']['parents']]==[GENERATED,'5a00c0c6e5e306dc74fc9df011c126750513a192']
assert 'Merge pull request #14' in commits['before']['message'] and 'Bengali' in commits['before']['message']
assert commits['generated']['sha']==GENERATED and [p['sha'] for p in commits['generated']['parents']]==[BASELINE]
assert commits['baseline']['sha']==BASELINE and commits['baseline']['tree']['sha']=='6829cc1d072631e6526ff0d9218a08c12fd5b406'
assert ref['ref']=='refs/heads/main' and ref['object']['sha']==PIN
paths={'':'root-tree','docs':'tree-docs','imports':'tree-imports','reports':'tree-reports',SOURCE_DIR:'tree-imports-web-deenhindi','reports/web-source-resolution-20261113':'tree-reports-web-source',REVIEWS:'tree-reviews'}
trees={};tree_bindings=[]
for side in ['baseline','generated','before','after']:
    for path,suffix in paths.items():
        name=side+'-'+suffix;t=api(name);trees[(side,path)]=t
        assert t['truncated'] is False and len({e['path'] for e in t['tree']})==len(t['tree'])
        assert all('/' not in e['path'] and '\0' not in e['path'] for e in t['tree'])
        ordered=sorted(t['tree'],key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
        raw=b''.join((e['mode'].lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in ordered)
        assert git('tree',raw)==t['sha'],(side,path)
        if path:
            parent,_,leaf=path.rpartition('/');e=entries(trees[(side,parent)])[leaf];assert e['type']=='tree' and e['sha']==t['sha']
        else:assert t['sha']==commits[side]['tree']['sha']
        tree_bindings.append({'snapshot':side,'path':path or '/','git_tree_sha1':t['sha'],'complete_entries':len(t['tree']),'truncated':False,'complete_tree_object_rehashed':True,'tree_object_bytes':len(raw),'tree_object_sha256':sha(raw),'saved_response_sha256':sha((ROOT/'input'/(name+'.json')).read_bytes())})
assert len(tree_bindings)==28
comparisons=[]
for path in paths:
    a=entries(trees[('before',path)]);b=entries(trees[('after',path)]);assert not set(a)-set(b)
    changed={k for k in a if a[k]!=b[k]};added=set(b)-set(a)
    prefix=path+'/' if path else '';allowed={p[len(prefix):].split('/')[0] for p in manifest_by if p.startswith(prefix)}
    assert (changed|added)<=allowed,(path,changed,added,allowed)
    comparisons.append({'path':path or '/','before_tree':trees[('before',path)]['sha'],'after_tree':trees[('after',path)]['sha'],'changed_existing_entries':sorted(changed),'added_entries':sorted(added),'removed_entries':[],'unchanged_existing_entries':len(a)-len(changed)})
assert comparisons[0]['changed_existing_entries']==['docs','imports','reports']
root_before=entries(trees[('before','')]);root_after=entries(trees[('after','')])
assert root_before['materials']==root_after['materials']
assert root_before['materials']['sha'].startswith('acb1af95')
merge_preserved=[]
for name in ['.gitattributes','.github','reader','scripts','tests','source-context']:
    assert root_before[name]==root_after[name]
    merge_preserved.append({'path':name,'entry':root_after[name],'actual_merge_parent_entry_preserved':True})
ancestral_diffs=[]
for first,last in [('baseline','generated'),('generated','before')]:
    for path in ['', 'imports',SOURCE_DIR,REVIEWS]:
        a=entries(trees[(first,path)]);b=entries(trees[(last,path)])
        ancestral_diffs.append({'from':first,'to':last,'path':path or '/','added':sorted(set(b)-set(a)),'removed':sorted(set(a)-set(b)),'changed':sorted(k for k in a.keys()&b.keys() if a[k]!=b[k])})
assert next(x for x in ancestral_diffs if x['from']=='baseline' and x['path']==SOURCE_DIR)['changed']==['excluded','progress.json','review-reuse','staged']
assert next(x for x in ancestral_diffs if x['from']=='generated' and x['path']=='imports')['changed']==[]
for side in ['baseline','generated','before']:
    assert entries(trees[(side,REVIEWS)])==entries(trees[('before',REVIEWS)])

old_entries=entries(trees[('before',REVIEWS)]);new_entries=entries(trees[('after',REVIEWS)])
old45={k:v for k,v in old_entries.items() if v['type']=='blob' and k.startswith('source-review-')}
all49={k:v for k,v in new_entries.items() if v['type']=='blob' and k.startswith('source-review-')}
new_paths={t['path'] for t in targets if t['path'].startswith(REVIEWS+'/')}
assert len(old45)==45 and len(all49)==49 and set(all49)-set(old45)=={Path(p).name for p in new_paths}
prior_repo=WORK/'phase22-checkpoint17cd-independent-integration/validation/published-reviews'
prior=[];old_ids=set();old477=[]
for name,e in sorted(old45.items()):
    assert e==all49[name]
    p=prior_repo/REVIEWS/name;b=bind(p);assert b['git_blob_sha1']==e['sha'] and b['bytes']==e['size']
    ledger=json.loads(gzip.decompress(p.read_bytes()));r=ledger.get('records',ledger.get('decisions'));ids={ident(x) for x in r}
    assert len(ids)==len(r) and not old_ids&ids;old_ids|=ids
    item={'path':REVIEWS+'/'+name,**b,'decisions':len(r),'all_four_snapshots_exact_entry_equal':True,'body_origin':'Existing validated local bytes independently rehashed against freshly fetched Git identities; not redownloaded here.'}
    prior.append(item)
    if b['sha256']=='6d099f91f2e406b6ca026930f4437cc1ce3983e26883cfedc3049f9cbb2f91a7':old477.append(item)
assert len(old_ids)==3576 and len(old477)==1 and old477[0]['decisions']==477
files=[]
for i,t in enumerate(targets):
    rp=ROOT/f'input/file-{i:02d}.json';r=read(rp);assert r['encoding']=='base64'
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
    files.append({'path':t['path'],**bind(downloaded),'github_url':r['display_url'],'github_blob_sha1':r['sha'],'complete_body_matches_frozen_payload':True,'complete_ancestor_objects':list(reversed(ancestry)),'connector_response_sha256':sha(rp.read_bytes())})
assert sum(f['bytes'] for f in files)==228519
qentry=entries(trees[('after','reports/web-source-resolution-20261113')])[Path(QUEUE).name]
assert all(qentry==entries(trees[(s,'reports/web-source-resolution-20261113')])[Path(QUEUE).name] for s in ['baseline','generated','before'])
qp=WORK/'phase20-independent-readback/downloaded'/QUEUE;qb=bind(qp)
assert qb['git_blob_sha1']==qentry['sha'] and qb['bytes']==qentry['size'] and qb['sha256']=='8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349'
qr=[json.loads(x) for x in gzip.decompress(qp.read_bytes()).splitlines()];qc=collections.Counter(f['language'] for r in qr for f in r['fields'])
assert len(qr)==3354 and qc=={'hi':3260,'ur':3051}

source_path=WORK/'phase22-checkpoint17cd-independent-integration/input/source-cohort-85.jsonl'
sources={'deenhindi-'+r['collection']+':'+r['number']:r for r in map(json.loads,source_path.read_bytes().splitlines())};assert len(sources)==85
counts=collections.Counter();new_ids=set();groups=[];excluded=[];forms=collections.Counter()
for relative in sorted(new_paths):
    ledger=json.loads(gzip.decompress((ROOT/'downloaded'/relative).read_bytes()));rows=ledger.get('records',ledger.get('decisions'));group=collections.Counter()
    for record in rows:
        key=ident(record);assert key in sources and key not in new_ids and key not in old_ids;new_ids.add(key)
        saved=sources[key];source=saved['source_record'];assert record['source_record_sha256']==sha(importer.json_bytes(source))
        assert record['source_reference_verbatim']==saved['source_reference_verbatim']
        if 'source_snapshot' in record:
            assert record['source_snapshot']==saved['snapshot'];forms['complete_snapshot_descriptor']+=1
        else:
            assert record['source_snapshot_sha256']==saved['snapshot']['sha256'] and record['source_record_url']==saved['snapshot']['url']
            assert record['source_parsed_path']==saved['parsed_path'] and record['source_parsed_sha256']==Path(saved['parsed_path']).name.removesuffix('.json.gz');forms['snapshot_hash_url_and_parsed_identity']+=1
        action=record['decision'];assert action in ['register','exclude'];counts[action]+=1;group[action]+=1
        if action=='exclude':excluded.append(key)
        fields={f['language']:f for f in record.get('field_reviews',record.get('fields'))}
        for lang,name in importer.LANGUAGE_FIELDS.items():
            text=source[name];assert text;field=fields.get(lang);counts['source_slots']+=1
            reviewed=bool(field and field['reviewed']);spans=field.get('spans',field.get('selected_spans',[])) if field else []
            if field:
                assert field['source_field']==name and field['text_sha256']==sha(text.encode())
                assert field['chars_reviewed']==(len(text) if reviewed else 0) and field['bytes_reviewed']==(len(text.encode()) if reviewed else 0);counts['explicit_field_decisions']+=1
            else:counts['implicit_unread_context_slots']+=1
            if reviewed:counts['read_fields']+=1;counts['read_characters']+=len(text);counts['read_utf8_bytes']+=len(text.encode());group['read_fields']+=1
            status='admitted_fields' if spans else 'read_context_fields' if reviewed else 'unread_context_fields';counts[status]+=1;group[status]+=1
            if action=='exclude':assert reviewed and not spans
            for span in spans:
                assert sha(text[span['start']:span['end']].encode())==span['sha256'];counts['selected_spans']+=1
    groups.append({'path':relative,'records':len(rows),'counts':dict(group)})
assert new_ids==set(sources)
for k,v in {'register':84,'exclude':1,'source_slots':425,'read_fields':173,'read_characters':79196,'read_utf8_bytes':170479,'admitted_fields':168,'read_context_fields':5,'unread_context_fields':252}.items():assert counts[k]==v,(k,counts[k])
assert forms=={'complete_snapshot_descriptor':62,'snapshot_hash_url_and_parsed_identity':23}
assert sorted(excluded)==['deenhindi-nasai:2636']

preserved=[]
for name,e in sorted(entries(trees[('before',SOURCE_DIR)]).items()):
    if name=='reviews':continue
    assert e==entries(trees[('after',SOURCE_DIR)])[name]
    preserved.append({'path':SOURCE_DIR+'/'+name,'kind':e['type'],'git_object_sha1':e['sha'],'bytes':e.get('size'),'actual_parent_after_full_entry_equal':True})
assert len(preserved)==12
aggregate=entries(trees[('before','imports')])['web-import-status.json'];assert aggregate==entries(trees[('after','imports')])['web-import-status.json']
state_path=WORK/'phase22-successor-acquisition-monitor/saved-checkpoint/state.json';sb=bind(state_path)
assert sb['git_blob_sha1']=='1435508cde81d7873f1e4c75854f6844fee4fdaa'
for side in ['baseline','generated','before','after']:
    e=entries(trees[(side,SOURCE_DIR)])['state.json'];assert e['sha']==sb['git_blob_sha1'] and e['size']==sb['bytes']
gp=WORK/'phase23-generated-export-audit/progress.json';gb=bind(gp)
assert gb['sha256']=='b205eaaf981fdb83286c4ca38b4ef0cff6065b0608ea84cd3d12ad24a94be1dd' and gb['git_blob_sha1']=='558b4eaa1aa7d7174447db9e5475880681ef6226'
for side in ['generated','before','after']:
    e=entries(trees[(side,SOURCE_DIR)])['progress.json'];assert e['sha']==gb['git_blob_sha1'] and e['size']==gb['bytes']
progress=read(gp);keys=['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked']
actual={k:progress[k] for k in keys};assert actual=={'imported_count':18570,'registered_hadith_count':18216,'non_narration_source_entries':167,'classification_pending_count':187,'pending_fetch_count':17820,'errors_count':0,'blocked':False}
hp=WORK/'phase22-successor-acquisition-monitor/saved-checkpoint/progress.json';hb=bind(hp);he=entries(trees[('baseline',SOURCE_DIR)])['progress.json'];assert he['sha']==hb['git_blob_sha1'] and he['size']==hb['bytes']
historical={k:read(hp)[k] for k in keys};assert historical['classification_pending_count']==273 and historical['registered_hadith_count']==18132 and historical['non_narration_source_entries']==165
projection={**actual,'registered_hadith_count':actual['registered_hadith_count']+84,'non_narration_source_entries':actual['non_narration_source_entries']+1,'classification_pending_count':actual['classification_pending_count']-85}
doc=(ROOT/'downloaded'/DOC).read_bytes();old=(WORK/'phase21-independent-readback/downloaded'/DOC).read_bytes()
assert len(doc)==128690 and sha(doc)=='533bf1a71e9a9f11587810dab613ad4d2e45ea20eb9e7da4c0cc69fa45db4798'
assert len(old)==121575 and doc.endswith(old)
oldb=bind(WORK/'phase21-independent-readback/downloaded'/DOC)
assert entries(trees[('before','docs')])[Path(DOC).name]['sha']==oldb['git_blob_sha1']
prefix=doc[:-len(old)];assert len(prefix)==7115 and sha(prefix)=='da7a7ccd9176bb5521106e198a5f16fda092c1a18aab6f55adefd574e9929b8f'
assert b'| Total |85|84|1|173|' in prefix and b'79,196 characters / 170,479 UTF-8 bytes' in prefix
assert b'6,311 Hindi/Urdu fields across 3,354 parents' in prefix and b'This is not a newly saved acquisition export.' in prefix

report={'schema':'hadith-bank-independent-publication-readback-v1','status':'PASS','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':'blaghtayt-alt/Hadith-Bank','published_commit':PIN,'actual_parent_commit':PARENT,'actual_root_tree':TREE,'prior_review_baseline_commit':BASELINE,'intervening_generated_reader_commit':GENERATED,'merge_parents':[p['sha'] for p in commits['before']['parents']],
 'observed_main_ref':ref['object']['sha'],'publication_manifest_sha256':MANIFEST_SHA,'payload_files':292,'payload_bytes':8208274,'independently_downloaded_complete_bodies':5,'independently_downloaded_body_bytes':sum(x['bytes'] for x in files),'file_checks':files,'all_complete_body_bytes_sha256_git_blob_and_payload_equal':True,
 'complete_git_tree_bindings':28,'unique_git_tree_objects':len({x['git_tree_sha1'] for x in tree_bindings}),'tree_bindings':tree_bindings,'directory_comparisons':comparisons,'all_full_tree_objects_locally_rehashed':True,'ancestral_directory_changes':ancestral_diffs,
 'all45_prior_active_entries_and_full_local_body_hashes_preserved':prior,'prior_manual_ids':3576,'new_manual_ids':85,'resulting_manual_ids':3661,'resulting_active_ledgers':49,'original477_ledger_preserved':old477[0],
 'canonical_priority_queue':{'path':QUEUE,**qb,'pending_fields':6311,'occurrences':3354,'by_language':dict(qc),'all_four_snapshot_entries_equal':True},'new_counts_from_fresh_complete_bodies':dict(counts),'new_ledger_counts':groups,'source_only_ids':sorted(excluded),'exact_source_provenance_binding_forms':dict(forms),'new85_source_baseline':bind(source_path),
 'all12_actual_parent_nonreview_deen_entries_preserved':preserved,'actual_parent_materials_entry_preserved':root_after['materials'],'actual_parent_aggregate_web_import_status_preserved':aggregate,'pr14_merge_root_entries_preserved':merge_preserved,
 'immutable64f4_state_body_binding':{**sb,'body_origin':'Existing saved source-state bytes rehashed against fresh baseline/generated/merge-parent/publication Git identities. Full history comparison is a separate audit.'},
 'actual_generated_export_body_binding':{**gb,'path':SOURCE_DIR+'/progress.json','body_origin':'Root freshly downloaded exact d304 progress body; this audit independently rehashes the complete local bytes against its own fresh generated/actual-parent/published path trees, not an independent second full body download.'},
 'actual_generated_export_counts_at_d304_a6c_and31c':actual,'historical64f4_worker_progress_binding':hb,'historical64f4_worker_counts':historical,'same_source_projection_after_new85_not_a_saved_export':projection,
 'source_state_vs_generated_export_distinction':'The immutable fetched-source state remains1435508c. The d304 generated export already consumed the86 phase21 decisions, so actual saved export holds are187, while the older acquisition-worker progress had273. The new85 publication is a review-input change; no newer generated export or live deployment is claimed.',
 'full64f4_history_audit_performed_here':False,'previous_document_bytes':len(old),'previous_document_sha256':sha(old),'all_previous_document_bytes_exact_suffix':True,'new_prefix_bytes':len(prefix),'new_prefix_sha256':sha(prefix),'document_historical_worker_counts_and_projection_checked':True,
 'current_publication_live_deployment_verified':False,'linguistic_rereadings_in_this_readback':0,'native_tests_repeated_in_this_readback':False,'source_site_requests':0,'github_writes':0,
 'limits':'Fresh independent GitHub commit/ref,28 complete ancestor/path-tree bindings and five complete body reads. The other287 payload bodies were not all downloaded again. Prior45 ledgers,queue,state and progress bodies are explicitly identified local byte proofs bound to fresh Git identities. Full acquisition history, source linguistic readings, native semantic gates, authenticity and live deployment remain separate evidence.'}
raw=enc(report);put(ROOT/'readback-receipt.json',raw)
evidence={'schema':'independent-github-readback-input-snapshots-v1','source':'Exact fresh connector responses. Identical tree objects were retrieved once and bound to every observed path.','inputs':{p.name:read(p) for p in sorted((ROOT/'input').glob('*.json'))}}
outputs={'readback-receipt.json':raw,'response-and-tree-evidence.json.gz':gzip.compress(enc(evidence),mtime=0),'audit_readback.py':Path(__file__).read_bytes()}
out=ROOT/'publish';files_out=[]
for name,b in outputs.items():
    p=out/REL/name;put(p,b);files_out.append({'path':(REL/name).as_posix(),'local_path':str(p),'source_path':str(p),**bind(p)})
delivery={'schema':'hadith-bank-independent-readback-delivery-v1','result':'PASS','published_commit':PIN,'files':files_out,'total_files':len(files_out),'total_bytes':sum(x['bytes'] for x in files_out)}
put(ROOT/'delivery-manifest.json',enc(delivery))
print(json.dumps({'status':'PASS','manifest_sha256':sha((ROOT/'delivery-manifest.json').read_bytes()),'report_sha256':sha(raw),'files':len(files_out),'bytes':delivery['total_bytes'],'counts':dict(counts),'actual_export':actual},indent=2))
