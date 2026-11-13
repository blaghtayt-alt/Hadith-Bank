"""Stage phase17 with exact dependencies and three permitted prior-path replacements.

This script performs no GitHub mutation. Publication requires a fresh main lease.
"""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PUBLISH=HERE/'publish'
BASE='d0a863b0966c7eb1ae1d5c36202de282caf77cab'
ROOT_TREE='ee5e26732dba6ea2ce9a7d3380085dac061f1845'
PREFIX='reports/web-source-resolution-20261113/phase17-publication-inputs-v1'
ACTIVE='imports/web-deenhindi-20261112/reviews/source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz'
QUEUE='reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
DOC='docs/WEB-SOURCE-RESOLUTION-20261113.md'
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def git_tree(entries):
    ordered=sorted(entries,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
    data=b''.join((str(e['mode']).lstrip('0')+' '+e['path']).encode()+b'\0'+bytes.fromhex(e['sha']) for e in ordered)
    return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).hexdigest()

def main(readback_manifest_sha):
    assert not (HERE/'manifest.json').exists(),'Frozen publication manifest must not be overwritten'
    packages=[
      ('primary-v2',ROOT/'phase17-original-bukhari25-hi-ur/delivery-manifest-v2.json','b82f5ad2274f4aa8ccef1927c9f87e0debf9158c69b9e6ce08a5f9fe80e83456'),
      ('independent-final-v2',ROOT/'phase17-original-bukhari25-independent-audit/delivery-manifest.json','d1c9a0be37c0f5e505dc26fc485c16d9af808869f11506ed11f8b4e312531cb4'),
      ('phase16-independent-readback',ROOT/'phase16-independent-readback/delivery-manifest.json',readback_manifest_sha),
    ]
    provenance=[];staged={}
    def add_bytes(path,data,origin):
        assert not Path(path).is_absolute() and '..' not in Path(path).parts
        if path in staged:
            assert staged[path]['sha256']==sha(data) and staged[path]['bytes']==len(data),('path collision',path)
            staged[path]['origins'].append(origin);return
        dest=PUBLISH/path;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==data,('existing staged bytes differ',path)
        else:dest.write_bytes(data)
        staged[path]={'path':path,'local_path':str(dest),'bytes':len(data),'sha256':sha(data),'git_blob_sha1':git(data),'mode':'100644','origins':[origin]}
    for name,path,expected in packages:
        raw=path.read_bytes();assert sha(raw)==expected,(name,'manifest hash')
        manifest=json.loads(raw);files=manifest['files']
        assert len({f['path'] for f in files})==len(files)
        for item in files:
            data=Path(item['local_path']).read_bytes()
            assert len(data)==item['bytes'] and sha(data)==item['sha256']
            if 'git_blob_sha1' in item:assert git(data)==item['git_blob_sha1']
            add_bytes(item['path'],data,name)
        add_bytes(PREFIX+'/manifests/'+name+'.json',raw,name+' immutable input manifest')
        provenance.append({'name':name,'local_manifest':str(path),'sha256':sha(raw),'files':len(files),'bytes':sum(x['bytes'] for x in files)})
    assert provenance[0]['files']==43 and provenance[1]['files']==9
    assert staged[ACTIVE]['sha256']=='18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'
    receipts=[
      ('publication-receipt.json','91b40a0d0c85866347316aa4aa1bca7134e2a6a211447e657f4a7576f8f36732'),
      ('tree-verification-receipts.json','81678c86d9140d81be5b940ff52e022741525afae2b19476f7d2f2236cc5ec09'),
      ('manifest.json','53e332441c181bb7e59eda327a40876df213909f3662325d598ab5cbb4f333c6'),
    ]
    receipt_docs={}
    for name,expected in receipts:
        data=(ROOT/'phase16-final-publication'/name).read_bytes();assert sha(data)==expected
        receipt_docs[name]=json.loads(data)
        add_bytes(PREFIX+'/receipts/phase16-'+name,data,'phase16 immutable publication receipt')
    pub=receipt_docs['publication-receipt.json']
    assert pub['commit_sha']==BASE and pub['root_tree_sha']==ROOT_TREE
    assert pub['parent_sha']=='bd4a75695d3c695e98bf8efa5ce07764ac5e2633'
    assert pub['manifest_sha256']==receipts[2][1] and pub['tree_receipts_sha256']==receipts[1][1]
    before_root=ROOT/'phase17-original-bukhari25-hi-ur/input/pinned'
    before_active=(before_root/ACTIVE).read_bytes();before_queue=(before_root/QUEUE).read_bytes()
    before_doc=(ROOT/'phase16-final-publication/publish'/DOC).read_bytes()
    assert sha(before_active)=='ac53483e3eab6c0a4c508c86180c75091792e895b5e29f602a061aa2cd080c62'
    assert sha(before_queue)=='343e72455fe122b59b37d795a59f9f8cca2358077723f1c725e4b1eaa3f57227'
    assert sha(before_doc)=='1854ead1fd42428fdab93f7b637cb5c7ae962b090ac3590bd0abbd812eaa500b' and len(before_doc)==74256
    expected_before={ACTIVE:before_active,QUEUE:before_queue,DOC:before_doc}
    current_queue_paths=[p for p in staged if p.endswith('/candidate-priority-field-queue.jsonl.gz') and '/independent-boundary-amendment' not in p]
    assert len(current_queue_paths)==1
    candidate_queue=PUBLISH.joinpath(current_queue_paths[0]).read_bytes()
    assert sha(candidate_queue)=='74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
    add_bytes(QUEUE,candidate_queue,'Exact promotion of already archived standalone phase17 queue')
    old_lines=gzip.decompress(before_queue).splitlines(keepends=True);new_lines=gzip.decompress(candidate_queue).splitlines(keepends=True)
    selected=json.loads((ROOT/'phase17-original-bukhari25-hi-ur/input/selection.json').read_bytes())['selected']
    selected_ids={x.get('occurrence_id',x.get('id')) for x in selected}
    assert len(selected_ids)==25
    assert new_lines==[line for line in old_lines if json.loads(line)['id'] not in selected_ids]
    qrows=[json.loads(x) for x in new_lines]
    assert len(qrows)==3379 and sum(len(r['fields']) for r in qrows)==6361
    prefix=(HERE/'current-status-draft.md').read_bytes()
    first_line,old_body=before_doc.split(b'\n',1)
    assert first_line.lstrip()==b'# Website-source queue resolution \xe2\x80\x94 13 November 2026'
    new_doc=prefix+old_body
    assert new_doc.endswith(old_body)
    add_bytes(DOC,new_doc,'English current status with exact previous body preserved as historical material')
    add_bytes(PREFIX+'/previous-status-document.md',before_doc,'Exact full previous status bytes')
    add_bytes(PREFIX+'/current-status-prefix.md',prefix,'New current status section')
    doc_receipt={'schema':'hadith-bank-versioned-status-document-update-v1','documented_base_commit':BASE,
        'path':DOC,'before_sha256':sha(before_doc),'before_bytes':len(before_doc),'before_git_blob_sha1':git(before_doc),
        'after_sha256':sha(new_doc),'after_bytes':len(new_doc),'after_git_blob_sha1':git(new_doc),
        'old_body_after_first_header_exact_suffix':True,'old_body_sha256':sha(old_body),
        'full_prior_document_archived_path':PREFIX+'/previous-status-document.md',
        'new_export_or_live_deployment_claimed':False}
    add_bytes(PREFIX+'/document-update-receipt.json',enc(doc_receipt),'Versioned document byte proof')
    # Merge complete known bd4a ancestor trees with the43 exact published d0a replacement trees.
    prior_trees_raw=(ROOT/'phase16-final-publication/verified-base-trees.json').read_bytes()
    assert sha(prior_trees_raw)=='b5c0592dbca85dbca1e91d37a8192dede0d253c04b97e1129de4e6ecd7a4c99c'
    prior_trees=json.loads(prior_trees_raw)
    assert prior_trees['base_commit']['sha']==pub['parent_sha']
    trees={}
    for directory,value in prior_trees['trees'].items():
        if value is not None and value.get('sha'):
            assert not value.get('truncated',False)
            assert git_tree(value['tree'])==value['sha']
            trees[directory]={'sha':value['sha'],'entries':value['tree']}
    changes=receipt_docs['tree-verification-receipts.json']
    assert changes['root_tree_sha']==ROOT_TREE and changes['complete'] is True
    for row in changes['trees']:
        assert git_tree(row['entries'])==row['after_tree_sha']
        trees[row['directory']]={'sha':row['after_tree_sha'],'entries':row['entries']}
    old_phase15_raw=(ROOT/'phase15-final-publication/tree-verification-receipts.json').read_bytes()
    assert sha(old_phase15_raw)=='8929e8d135183c355c9af7edf5236fc6e50734173cd51e3a355a70cd5386cb4b'
    field_dir='imports/web-deenhindi-20261112/reviews/field-expansions'
    ft=next(t for t in json.loads(old_phase15_raw)['trees'] if t['directory']==field_dir)
    assert git_tree(ft['entries'])==ft['after_tree_sha']
    trees[field_dir]={'sha':ft['after_tree_sha'],'entries':ft['entries']}
    assert trees['']['sha']==ROOT_TREE
    def lookup(path):
        directory='';expected=ROOT_TREE;parts=path.split('/')
        for index,name in enumerate(parts):
            assert directory in trees,('Missing complete ancestor tree',directory,path)
            tree=trees[directory];assert tree['sha']==expected
            found=[e for e in tree['entries'] if e['path']==name]
            assert len(found)<=1
            if not found:return {'status':'new_path','first_absent_component':'/'.join(parts[:index+1]),'complete_parent_tree_sha1':expected}
            entry=found[0]
            if index==len(parts)-1:return {'status':'existing_path','git_blob_sha1':entry['sha'],'mode':entry['mode'],'type':entry['type']}
            assert entry['type']=='tree'
            expected=entry['sha'];directory='/'.join(parts[:index+1])
        raise AssertionError('unreachable')
    add_bytes(PREFIX+'/field-expansions-ancestor-proof.json',enc({'source_receipt_sha256':sha(old_phase15_raw),
        'directory':field_dir,'git_tree_sha1':ft['after_tree_sha'],'complete_entries':ft['entries'],
        'scope':'Reused exact unchanged tree only after verifying its SHA in the d0a ancestor chain.'}),'Unchanged ancestor content proof')
    add_bytes(PREFIX+'/assemble_publication.py',Path(__file__).read_bytes(),'Exact local assembler used for this stage')
    path_proofs={}
    for path,item in staged.items():
        proof=lookup(path);path_proofs[path]=proof
        if proof['status']=='existing_path':
            assert path in expected_before,('Unapproved existing-path overwrite',path)
            assert proof['type']=='blob' and proof['mode']=='100644'
            assert proof['git_blob_sha1']==git(expected_before[path]),('Wrong prior blob',path)
        else:assert path not in expected_before
    assert {p for p,r in path_proofs.items() if r['status']=='existing_path'}==set(expected_before)
    audit_raw=(ROOT/'phase17-original-bukhari25-independent-audit/independent-final-v2-audit.json').read_bytes()
    assert sha(audit_raw)=='8b52eafe6aca14df40d45aa6a30fab8b92a504978c061665b3c39d146233c03e'
    audit=json.loads(audit_raw)
    assert audit['result']=='PASS' and audit['primary_manifest_sha256']==packages[0][2]
    assert audit['counts']['lossless_full_source_field_partitions']==2385
    assert audit['queue']['candidate_sha256']==sha(candidate_queue)
    validation={'schema':'hadith-bank-phase17-publication-staging-validation-v1','result':'PASS',
        'documented_base_commit':BASE,'base_root_tree_sha':ROOT_TREE,
        'complete_d0a_published_trees_rehashed':len(changes['trees']),
        'additional_unchanged_field_expansions_tree_rehashed_and_linked':True,
        'only_existing_path_updates':sorted(expected_before),'path_proofs':path_proofs,
        'all_declared_primary_and_independent_payloads_preserved':True,
        'archived_and_canonical_queue_bytes_identical':True,
        'queue_removes_exact50_fields_and25_rows_remaining_lines_exact':True,
        'full477_native_and_source_gate_sha256':sha(audit_raw),
        'frozen_input_package_manifests':provenance,
        'publication_commit_created':False,'github_writes':0,'source_http_requests':0,
        'new_export_or_live_deployment_claimed':False,
        'fresh_expected_head_lease_required':'Root must refresh main and preserve later work before publication. These path proofs apply only to the exact documented d0a commit.'}
    validation_path=PREFIX+'/staging-validation.json'
    validation_proof=lookup(validation_path);assert validation_proof['status']=='new_path'
    validation['staging_validation_path_proof']=validation_proof
    add_bytes(validation_path,enc(validation),'Complete local publication stage gate')
    for item in staged.values():
        data=Path(item['local_path']).read_bytes()
        assert len(data)==item['bytes'] and sha(data)==item['sha256'] and git(data)==item['git_blob_sha1']
    assert {p.relative_to(PUBLISH).as_posix() for p in PUBLISH.rglob('*') if p.is_file()}==set(staged)
    overwritten=[{'path':p,'before_bytes':len(expected_before[p]),'before_sha256':sha(expected_before[p]),
        'before_git_blob_sha1':git(expected_before[p]),'after_sha256':staged[p]['sha256'],
        'after_git_blob_sha1':staged[p]['git_blob_sha1']} for p in sorted(expected_before)]
    result={'schema':'hadith-bank-frozen-phase17-publication-manifest-v1','repository':'blaghtayt-alt/Hadith-Bank','branch':'main',
        'documented_base_commit':BASE,'base_root_tree_sha':ROOT_TREE,'source_review_pin':'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d',
        'generated_at_utc':datetime.now(timezone.utc).isoformat(),'expected_overwrites':overwritten,
        'input_packages':provenance,'files':[staged[k] for k in sorted(staged)],
        'total_files':len(staged),'total_bytes':sum(x['bytes'] for x in staged.values()),
        'new_repository_paths_at_documented_base':len(staged)-3,'existing_paths_changed':3,
        'local_validation':{'status':'PASS','path':validation_path,'sha256':staged[validation_path]['sha256'],
            'independent_final_native_source_audit_sha256':sha(audit_raw)},
        'fresh_base_required_before_publication':True,'github_branch_updated':False,
        'new_acquisition_export_claimed':False,'live_deployment_verified':False}
    raw=enc(result);(HERE/'manifest.json').write_bytes(raw)
    (HERE/'document-update.md').write_bytes(new_doc)
    (HERE/'document-update-receipt.json').write_bytes(enc(doc_receipt))
    print(json.dumps({'manifest':str(HERE/'manifest.json'),'sha256':sha(raw),'files':len(staged),'bytes':result['total_bytes'],
        'new_paths':len(staged)-3,'overwrites':3,'document_sha256':sha(new_doc),'document_bytes':len(new_doc),
        'validation_sha256':staged[validation_path]['sha256']},indent=2))

if __name__=='__main__':
    assert len(sys.argv)==2,'Pass the final independently frozen phase16 readback manifest SHA256'
    main(sys.argv[1])
