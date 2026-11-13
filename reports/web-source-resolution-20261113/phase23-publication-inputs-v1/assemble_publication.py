"""Stage the final102 source-bound reviews against independently read-back31c011."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import collections
import gzip
import hashlib
import json

H=Path(__file__).resolve().parent
W=H.parent
OUT=H/'publish'
PREFIX=Path('reports/web-source-resolution-20261113/phase23-publication-inputs-v1')
REV=Path('imports/web-deenhindi-20261112/reviews')
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
BASE='31c01136611b163683a01b47833bf74354820851'
ROOT='ef2a623731fad42608136ccff3118e174e47d0b1'
SOURCE='64f4ed50ed6026855237a5d547a86dd03e73f804'
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
read=lambda p:json.loads(p.read_bytes())
local=lambda f:Path(f.get('local_path',f.get('source_path')))


def th(es):
    es=sorted(es,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
    b=b''.join((str(e['mode']).lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in es)
    return hashlib.sha1(b'tree '+str(len(b)).encode()+b'\0'+b).hexdigest()


def safe(s):
    s=str(s);p=PurePosixPath(s)
    assert s and not p.is_absolute() and '..' not in p.parts and '\\' not in s
    return s


def main():
    assert not (H/'manifest.json').exists(),'Frozen publication is immutable.'
    cb=(H/'staging-inputs.json').read_bytes();cfg=json.loads(cb)
    assert cfg['documented_base_commit']==BASE and cfg['root_tree_sha']==ROOT
    assert cfg['source_review_pin']==SOURCE and cfg['root_status_review_complete']
    staged={};packages={};provenance=[]
    def add(path,b,origin):
        path=safe(path)
        if path in staged:
            assert staged[path]['sha256']==sha(b)
            staged[path]['origins'].append(origin)
            return
        p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():assert p.read_bytes()==b
        else:p.write_bytes(b)
        staged[path]={'path':path,'local_path':str(p),'bytes':len(b),'sha256':sha(b),
            'git_blob_sha1':git(b),'mode':'100644','origins':[origin]}
    for spec in cfg['packages']:
        name=spec['name'];p=W/spec['manifest_path'];b=p.read_bytes()
        assert sha(b)==spec['manifest_sha256'] and name not in packages
        m=json.loads(b)
        assert len(m['files'])==len({f['path'] for f in m['files']})
        for f in m['files']:
            q=local(f)
            assert q.is_file() and not q.is_symlink() and q.resolve().is_relative_to(p.parent.resolve())
            d=q.read_bytes()
            assert len(d)==f.get('bytes',f.get('size_bytes')) and sha(d)==f['sha256']
            assert not f.get('git_blob_sha1') or git(d)==f['git_blob_sha1']
            add(f['path'],d,name)
        add(PREFIX/'manifests'/f'{name}.json',b,'Exact frozen input manifest')
        packages[name]=m
        provenance.append({'name':name,'local_manifest':str(p),'sha256':sha(b),
            'files':len(m['files']),'bytes':sum(f.get('bytes',f.get('size_bytes')) for f in m['files'])})
    assert len(packages)==cfg['expected_package_count']==14
    def payload(name,suffix):
        fs=[f for f in packages[name]['files'] if f['path'].endswith(suffix)]
        assert len(fs)==1,(name,suffix)
        return local(fs[0]).read_bytes()
    ir=payload('combined102-integration','validation-report.json')
    assert sha(ir)==cfg['integration_report_sha256']
    integ=json.loads(ir)
    expected={'register':100,'exclude':2,'read_fields':216,'admitted':200,'read_context':16,
        'unread_context':294,'empty':0,'source_slots':510,'partitions':510,
        'read_characters':112759,'read_utf8_bytes':239747}
    assert integ['result']=='PASS' and integ['source_commit']==SOURCE
    assert integ['published_review_baseline_commit']==BASE
    assert all(integ['counts'].get(k,0)==v for k,v in expected.items())
    assert (integ['native_combined_loader_ledgers'],integ['native_combined_loader_ids'])==(53,3763)
    assert (integ['source_count'],integ['source_files_rehashed_against_frozen_proof'],
        integ['full_raw_reparses_bound_from_frozen_preparation'])==(102,204,102)
    assert integ['native_new102_apply_finish']=='PASS'
    assert integ['all49_prior_blobs_dependencies_and3661_decisions_unchanged']
    ids=set();primary_entries=[];counts=collections.Counter();reads=collections.Counter()
    assert len(cfg['primary_packages'])==4
    for name,number in cfg['primary_packages'].items():
        fs=[f for f in packages[name]['files'] if Path(f['path']).parent==REV and Path(f['path']).name.startswith('source-review-')]
        assert len(fs)==1
        f=fs[0];primary_entries.append(f)
        ledger=json.loads(gzip.decompress((OUT/f['path']).read_bytes()))
        sb=(OUT/safe(ledger['source_ledger_path'])).read_bytes()
        assert sha(sb)==ledger['source_ledger_sha256']
        rows=[json.loads(x) for x in gzip.decompress(sb).splitlines()]
        saved={'deenhindi-'+r['collection']+':'+r['number']:r for r in rows}
        assert len(rows)==len(saved)==len(ledger['records'])==number
        for d in ledger['records']:
            ident=d.get('id',d.get('occurrence_id'))
            assert ident in saved and ident not in ids
            ids.add(ident);counts[d['decision']]+=1
            for f in d.get('field_reviews',d.get('fields')):
                if f['reviewed']:
                    reads['read_fields']+=1;reads['read_characters']+=f['chars_reviewed']
                    reads['read_utf8_bytes']+=f['bytes_reviewed']
                    reads['admitted' if f.get('spans',f.get('selected_spans',[])) else 'read_context']+=1
    assert len(ids)==102 and counts=={'register':100,'exclude':2}
    assert all(reads[k]==expected[k] for k in reads)
    rb=W/'phase22-independent-readback'
    receipt=read(rb/'readback-receipt.json')
    assert sha((rb/'readback-receipt.json').read_bytes())=='7c8aa6deff7a735a8bd98a4e6c0902289454f1b38cfa51c4afb9602682616b48'
    assert receipt['status']=='PASS' and receipt['published_commit']==BASE and receipt['actual_root_tree']==ROOT
    assert (receipt['resulting_active_ledgers'],receipt['resulting_manual_ids'])==(49,3661)
    pool={};origins=collections.defaultdict(list);used=set()
    def addtree(t,origin):
        assert not t.get('truncated',False)
        if t['sha'] is None:
            assert t['tree']==[]
            return
        assert th(t['tree'])==t['sha'] and len(t['tree'])==len({e['path'] for e in t['tree']})
        es=sorted([{k:e[k] for k in ['path','mode','type','sha']} for e in t['tree']],key=lambda e:e['path'])
        if t['sha'] in pool:assert pool[t['sha']]==es
        else:pool[t['sha']]=es
        origins[t['sha']].append(origin)
    prior={}
    for spec in cfg['prior_publication_receipts']:
        b=(W/'phase22-final-publication'/spec['name']).read_bytes()
        assert sha(b)==spec['sha256'] and len(b)==spec['bytes']
        prior[spec['name']]=json.loads(b)
        add(PREFIX/'receipts'/('phase22-'+spec['name']),b,'Prior exact publication receipt')
    assert prior['publication-receipt.json']['commit']==BASE and prior['publication-receipt.json']['tree_sha']==ROOT
    for d,t in prior['verified-base-trees.json'].items():
        if t is not None:addtree(t,'Prior verified before tree '+d)
    for r in prior['tree-verification-receipts.json']:
        addtree(r['complete_tree'],'Prior verified published tree '+r['directory'])
    for p in sorted((rb/'input').glob('*tree*.json')):
        d=read(p)
        if 'content' in d:d=json.loads(d['content'])
        if isinstance(d.get('tree'),list):addtree(d,'Fresh independent readback '+p.name)
    def lookup(path):
        parts=safe(path).split('/');current=ROOT;chain=[]
        for index,name in enumerate(parts):
            assert current in pool,('Missing actual ancestor',path,index,current)
            used.add(current);chain.append({'directory':'/'.join(parts[:index]),'git_tree_sha1':current})
            es=[e for e in pool[current] if e['path']==name]
            assert len(es)<=1
            if not es:return {'status':'new_path','first_absent_component':'/'.join(parts[:index+1]),'ancestor_chain':chain}
            e=es[0]
            if index==len(parts)-1:return {'status':'existing_path','git_object_sha1':e['sha'],'mode':e['mode'],'type':e['type'],'ancestor_chain':chain}
            assert e['type']=='tree'
            current=e['sha']
    queue=(W/'phase20-independent-readback/downloaded'/QUEUE).read_bytes()
    assert sha(queue)=='8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349'
    assert lookup(QUEUE)['git_object_sha1']==git(queue)
    qrows=[json.loads(r) for r in gzip.decompress(queue).splitlines()]
    qlang=collections.Counter(f['language'] for r in qrows for f in r['fields'])
    assert len(qrows)==3354 and qlang=={'hi':3260,'ur':3051} and QUEUE not in staged
    old=[e for e in pool[lookup(REV)['git_object_sha1']] if e['type']=='blob' and e['path'].startswith('source-review-')]
    assert len(old)==49
    baseline=W/'phase22-checkpoint17cd-independent-integration/validation/combined-reviews'
    for e in old:
        assert git((baseline/REV/e['path']).read_bytes())==e['sha']
        assert (REV/e['path']).as_posix() not in staged
    acqspec=cfg['previously_published_acquisition_audit']
    ar=(W/acqspec['local_path']).read_bytes()
    assert sha(ar)==acqspec['sha256'] and lookup(acqspec['repository_path'])['git_object_sha1']==git(ar)
    acq=json.loads(ar)
    assert acq['status']=='PASS_SAVED_CHECKPOINT_AUDIT' and acq['saved_commit']==SOURCE
    assert {i.removeprefix('deenhindi-') for i in ids}==set(acq['held_partition']['new102_keys'])
    assert acq['complete_cap_augmentation']['source_files_verified']==546
    assert acq['complete_cap_augmentation']['raw_html_reparses']==273
    assert acq['continuation_failure']['target_workflow_id']==415715399
    assert not acq['continuation_failure']['workflow_enabled_by_auditor']
    gp=(W/'phase23-generated-export-audit/progress.json').read_bytes()
    assert sha(gp)=='b205eaaf981fdb83286c4ca38b4ef0cff6065b0608ea84cd3d12ad24a94be1dd'
    progress_path='imports/web-deenhindi-20261112/progress.json'
    assert lookup(progress_path)['git_object_sha1']==git(gp)=='558b4eaa1aa7d7174447db9e5475880681ef6226'
    progress=json.loads(gp)
    actual={k:progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count']}
    assert list(actual.values())==[18570,18216,167,187,17820,0]
    projection={'fetched':18570,'registered':18216+84+100,'source_only':167+1+2,'held':187-85-102,'unfetched':17820}
    assert projection=={'fetched':18570,'registered':18400,'source_only':170,'held':0,'unfetched':17820}
    before=(rb/'downloaded'/DOC).read_bytes()
    assert len(before)==128690 and sha(before)=='533bf1a71e9a9f11587810dab613ad4d2e45ea20eb9e7da4c0cc69fa45db4798'
    assert lookup(DOC)['git_object_sha1']==git(before)
    prefix=(H/cfg['status_prefix_path']).read_bytes()
    assert sha(prefix)==cfg['root_approved_status_prefix_sha256']
    after=prefix+before
    assert after.endswith(before)
    add(DOC,after,'Approved current prefix plus complete previous document')
    add(PREFIX/'previous-status-document.md',before,'Exact previous128690-byte document')
    add(PREFIX/'current-status-prefix.md',prefix,'Root-read current status')
    dr={'schema':'hadith-bank-versioned-status-document-update-v1','documented_base_commit':BASE,'path':DOC,
        'before_bytes':len(before),'before_sha256':sha(before),'before_git_blob_sha1':git(before),
        'prefix_bytes':len(prefix),'prefix_sha256':sha(prefix),'after_bytes':len(after),
        'after_sha256':sha(after),'after_git_blob_sha1':git(after),
        'complete_old_document_exact_suffix_including_original_title':True,
        'actual_generated_export_commit':'d304bef0c7955377026a0c2aeebdd677b1e05b0a',
        'review_projection_is_a_new_saved_export':False,'current_publication_live_deployment_claimed':False}
    add(PREFIX/'document-update-receipt.json',enc(dr),'Exact document preservation receipt')
    add(PREFIX/'staging-inputs.json',cb,'Frozen package bindings')
    add(PREFIX/'assemble_publication.py',Path(__file__).read_bytes(),'Publication assembler')
    proofs={p:lookup(p) for p in staged}
    assert {p for p,v in proofs.items() if v['status']=='existing_path'}=={DOC}
    assert all(lookup(f['path'])['status']=='new_path' for f in primary_entries)
    assert all(p.startswith(('docs/','imports/web-deenhindi-20261112/reviews/','reports/web-source-resolution-20261113/')) for p in staged)
    tp=str(PREFIX/'complete-used-base-ancestor-trees.json.gz')
    assert lookup(tp)['status']=='new_path'
    add(tp,gzip.compress(enc({'schema':'hadith-bank-exact-base-complete-ancestor-proof-v1',
        'commit':BASE,'root_tree_sha':ROOT,'trees':[{'git_tree_sha1':s,'entries':pool[s],'origins':origins[s]} for s in sorted(used)]}),mtime=0),'Exact linked complete Git ancestor trees')
    validation={'schema':'hadith-bank-phase23-publication-staging-validation-v1','result':'PASS',
        'documented_base_commit':BASE,'base_root_tree_sha':ROOT,'only_existing_path_update':DOC,
        'path_proofs':proofs,'old49_active_review_entries_unchanged':old,'prior_manual_ids':3661,
        'combined_active_ledgers':53,'combined_manual_ids':3763,'canonical_priority_queue_sha256':sha(queue),
        'canonical_priority_queue_not_in_write_set':True,'canonical_queue_fields':6311,'canonical_queue_ids':3354,
        'canonical_queue_by_language':dict(qlang),
        'new_active_ledgers':[{'path':f['path'],'sha256':f['sha256']} for f in primary_entries],
        'review_cohort_occurrences':102,'review_counts':expected,'integration_report_sha256':sha(ir),
        'previously_published_acquisition_audit':acqspec,
        'actual_generated_export_at_documented_base':actual,
        'actual_generated_export_progress_sha256':sha(gp),'raw_acquisition_state_is_older_than_generated_progress':True,
        'fixed64f4_projection_after_all273_review_decisions':projection,'projection_is_saved_export':False,
        'all_declared_packages_hash_checked':provenance,'source_requests':0,'workflow_dispatches':0,
        'disabled_source_workflow_unchanged':True,'live_deployment_claimed':False,
        'fresh_expected_head_lease_required':True}
    vp=str(PREFIX/'staging-validation.json')
    assert lookup(vp)['status']=='new_path'
    add(vp,enc(validation),'Final package/path/status gate')
    pp=str(PREFIX/'payload-file-manifest.json')
    assert lookup(pp)['status']=='new_path'
    add(pp,enc({'schema':'hadith-bank-portable-publication-payload-manifest-v1',
        'documented_base_commit':BASE,'base_root_tree_sha':ROOT,
        'manifest_excludes_its_own_recursive_hash':True,
        'files':[{k:v for k,v in staged[p].items() if k not in ['local_path','origins']} for p in sorted(staged)]}),'Portable payload manifest')
    for f in staged.values():
        b=Path(f['local_path']).read_bytes()
        assert len(b)==f['bytes'] and sha(b)==f['sha256'] and git(b)==f['git_blob_sha1']
    assert {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}==set(staged)
    manifest={'schema':'hadith-bank-frozen-phase23-publication-manifest-v1',
        'repository':'blaghtayt-alt/Hadith-Bank','branch':'main','documented_base_commit':BASE,
        'base_root_tree_sha':ROOT,'published_review_baseline_commit':BASE,'source_review_pin':SOURCE,
        'generated_at_utc':datetime.now(timezone.utc).isoformat(),'input_packages':provenance,
        'expected_overwrites':[{'path':DOC,'before':{'bytes':len(before),'sha256':sha(before),'git_blob_sha1':git(before)},
            'after':{'bytes':len(after),'sha256':sha(after),'git_blob_sha1':git(after)}}],
        'files':[staged[p] for p in sorted(staged)],'total_files':len(staged),
        'total_bytes':sum(f['bytes'] for f in staged.values()),'new_repository_paths_at_documented_base':len(staged)-1,
        'existing_paths_changed':1,'new_active_ledgers':4,'existing_active_ledgers_changed':0,
        'canonical_priority_queue_changed':False,
        'local_validation':{'status':'PASS','path':vp,'sha256':staged[vp]['sha256'],
            'combined102_native_source_report_sha256':sha(ir),'previously_published_acquisition_audit_sha256':sha(ar),
            'portable_payload_file_manifest_path':pp,'portable_payload_file_manifest_sha256':staged[pp]['sha256']},
        'fresh_base_required_before_publication':True,'github_branch_updated':False,
        'new_review_projection_is_saved_export':False,'current_publication_live_deployment_verified':False}
    (H/'manifest.json').write_bytes(enc(manifest))
    (H/'document-update.md').write_bytes(after)
    (H/'document-update-receipt.json').write_bytes(enc(dr))
    print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),
        'files':len(staged),'bytes':manifest['total_bytes'],'new_paths':len(staged)-1,'overwrites':1,
        'document_bytes':len(after),'document_sha256':sha(after),'validation_sha256':staged[vp]['sha256']},indent=2))


if __name__=='__main__':
    main()
