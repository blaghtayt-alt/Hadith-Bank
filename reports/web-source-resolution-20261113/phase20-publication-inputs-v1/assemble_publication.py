"""Stage the exact original-language extension against independently read-back phase19."""
from pathlib import Path, PurePosixPath
import collections, datetime, gzip, hashlib, json, sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
PREFIX = PurePosixPath('reports/web-source-resolution-20261113/phase20-publication-inputs-v1')
REV = 'imports/web-deenhindi-20261112/reviews'
ACTIVE = REV + '/source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz'
QUEUE = 'reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
DOC = 'docs/WEB-SOURCE-RESOLUTION-20261113.md'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer

def sha(b): return hashlib.sha256(b).hexdigest()
def git(b): return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
def enc(v): return (json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def binding(b): return {'bytes': len(b), 'sha256': sha(b), 'git_blob_sha1': git(b)}
def safe(p):
    s = str(p); q = PurePosixPath(s)
    assert not q.is_absolute() and '..' not in q.parts and '\\' not in s and '\0' not in s
    assert q.as_posix() == s
    return s
def write_exact(p, b):
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists(): assert p.read_bytes() == b, ('Immutable output differs', str(p))
    else: p.write_bytes(b)
def tree_hash(rows):
    rows = sorted(rows, key=lambda r: (r['path'] + ('/' if r['type'] == 'tree' else '')).encode())
    raw = b''.join((str(r['mode']).lstrip('0') + ' ' + r['path']).encode() + b'\0' + bytes.fromhex(r['sha']) for r in rows)
    return hashlib.sha1(b'tree ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
def ledger_rows(b):
    x = json.loads(gzip.decompress(b)); return x.get('records', x.get('decisions'))
def oid(r): return r.get('occurrence_id', r.get('id'))

def main():
    config_raw = (HERE / 'staging-inputs.json').read_bytes(); config = json.loads(config_raw)
    assert config['root_status_approval_pending'] is False
    base = config['base_commit']; root_sha = config['base_tree']
    assert base == '70c1a0799bcf67a18bf28bdb9a6672fe1edbc552' and root_sha == '1a4a609c58936eda0dfae376dd4370d2988a5997'
    staged = {}; provenance = []; packages = {}; portable = []
    def add(path, b, origin):
        path = safe(path)
        if path in staged: assert staged[path][0] == b, ('Payload collision', path)
        else: staged[path] = (b, origin)
    for item in config['packages']:
        manifest_path = Path(item['manifest']); raw = manifest_path.read_bytes(); assert sha(raw) == item['sha256']
        manifest = json.loads(raw); rows = manifest['files']
        assert len(rows) == item['files'] == len({r['path'] for r in rows})
        assert sum(r['bytes'] for r in rows) == item['bytes']
        package_files = {}
        for r in rows:
            path = safe(r['path']); p = Path(r['local_path']); assert p.is_file() and not p.is_symlink()
            b = p.read_bytes(); assert binding(b) == {k: r[k] for k in ['bytes', 'sha256', 'git_blob_sha1']}
            add(path, b, item['name']); package_files[path] = b
        packages[item['name']] = (manifest, package_files)
        provenance.append({k: v for k, v in item.items() if k != 'manifest'})
        portable.append({'name': item['name'], 'original_manifest_sha256': sha(raw),
            'files': [{'path': r['path'], **{k: r[k] for k in ['bytes', 'sha256', 'git_blob_sha1']}} for r in rows]})
        add(PREFIX / 'exact-input-manifests' / (item['name'] + '.json'), raw, 'Exact immutable input manifest; original local paths retained as historical evidence')
    assert len(packages) == 4
    primary, primary_files = packages['primary-original50']
    audit_files = packages['independent-original50'][1]
    audit_path = next(p for p in audit_files if p.endswith('/independent-final-v2-audit.json'))
    audit_raw = audit_files[audit_path]; audit = json.loads(audit_raw)
    assert audit['result'] == 'PASS' and audit['primary_manifest_sha256'] == config['packages'][0]['sha256']
    assert audit['primary_active_sha256'] == sha(primary_files[ACTIVE]) == '6d099f91f2e406b6ca026930f4437cc1ce3983e26883cfedc3049f9cbb2f91a7'
    assert audit['full477_before_after_native_apply_finish'] == 'PASS' and audit['all477_parent_dispositions_unchanged']
    assert audit['counts']['lossless_source_field_partitions'] == 2385 and audit['counts']['prior_other_field_definitions_exact'] == 2335
    assert audit['counts']['prior_explicit_script_corrections_exact'] == 19
    assert audit['source_files_independently_reopened'] == 50 and audit['complete_raw_reparses'] == 25
    assert sum(x['complete_fields_read'] for x in audit['field_coverage'].values()) == 50
    assert sum(x['characters_read'] for x in audit['field_coverage'].values()) == 27103
    assert sum(x['utf8_bytes_read'] for x in audit['field_coverage'].values()) == 58879
    current = lambda suffix: min((p for p in primary_files if p.endswith('/' + suffix)), key=lambda p: len(p.split('/')))
    candidate_queue = primary_files[current('candidate-priority-field-queue.jsonl.gz')]
    assert sha(candidate_queue) == audit['queue']['candidate_sha256'] == '8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349'
    add(QUEUE, candidate_queue, 'Exact independently audited candidate promoted to the canonical priority queue')

    readback = WORK / 'phase19-independent-readback'
    rb = json.loads((readback / 'readback-receipt.json').read_bytes())
    assert rb['status'] == 'PASS' and rb['published_commit'] == base and rb['actual_root_tree'] == root_sha
    assert rb['resulting_active_ledgers'] == 41 and rb['resulting_manual_ids'] == 3490
    pool = {}; origins = collections.defaultdict(list); used = set()
    def ingest(tree, origin):
        assert tree.get('truncated') is False
        rows = tree['tree']; assert len(rows) == len({r['path'] for r in rows})
        assert all('/' not in r['path'] and '\0' not in r['path'] for r in rows)
        assert tree_hash(rows) == tree['sha']
        canonical = sorted([{k: r[k] for k in ['path', 'mode', 'type', 'sha']} for r in rows], key=lambda r: r['path'])
        if tree['sha'] in pool: assert pool[tree['sha']] == canonical
        else: pool[tree['sha']] = canonical
        origins[tree['sha']].append(origin)
    for p in sorted((readback / 'input').glob('after-*tree*.json')):
        ingest(json.loads(json.loads(p.read_bytes())['content']), 'Fresh independent phase19 GitHub response ' + p.name)
    p = HERE / 'input/base-field-expansions-tree.json'
    ingest(json.loads(json.loads(p.read_bytes())['content']), 'Fresh exact field-expansions Git tree linked from phase19 reviews')
    def lookup(path):
        parts = safe(path).split('/'); expected = root_sha; directory = ''; chain = []
        for i, name in enumerate(parts):
            assert expected in pool, ('Missing complete ancestor', directory, expected, path)
            used.add(expected); chain.append({'directory': directory or '/', 'git_tree_sha1': expected})
            found = [r for r in pool[expected] if r['path'] == name]; assert len(found) <= 1
            if not found: return {'status': 'new_path', 'first_absent_component': '/'.join(parts[:i+1]), 'ancestor_chain': chain}
            r = found[0]
            if i == len(parts)-1: return {'status': 'existing_path', 'type': r['type'], 'mode': r['mode'], 'git_object_sha1': r['sha'], 'ancestor_chain': chain}
            assert r['type'] == 'tree'; expected = r['sha']; directory = '/'.join(parts[:i+1])
        raise AssertionError('Unreachable')
    prior_rows = pool[lookup(REV)['git_object_sha1']]
    active_entries = [r for r in prior_rows if r['type'] == 'blob' and r['path'].startswith('source-review-')]
    assert len(active_entries) == 41
    all_ids = set(); unchanged_ledgers = []; active_before = None
    for r in active_entries:
        path = REV + '/' + r['path']
        p = readback / 'downloaded' / path
        if not p.exists(): p = WORK / 'phase19-checkpoint3e574-independent-integration/validation/published-reviews' / path
        b = p.read_bytes(); assert git(b) == r['sha']
        rows = ledger_rows(b); ids = {oid(x) for x in rows}
        assert len(ids) == len(rows) and not ids & all_ids; all_ids |= ids
        if path == ACTIVE: active_before = b
        else:
            assert path not in staged
            unchanged_ledgers.append({'path': path, **binding(b), 'decision_ids': len(ids)})
    assert len(all_ids) == 3490 and len(unchanged_ledgers) == 40 and active_before is not None
    assert sha(active_before) == audit['prior_published_active_sha256'] == '18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'
    selection = json.loads(primary_files[current('selection.json')]); selected_ids = {r['id'] for r in selection['selected']}
    selected_keys = {(r['id'], f['language']) for r in selection['selected'] for f in r['fields']}
    assert len(selected_ids) == 25 and len(selected_keys) == 50
    old = {oid(r): r for r in ledger_rows(active_before)}; new = {oid(r): r for r in ledger_rows(primary_files[ACTIVE])}
    assert set(old) == set(new) and len(new) == 477
    changed = set(); unchanged_fields = 0
    for ident, before in old.items():
        after = new[ident]
        assert {k:v for k,v in before.items() if k!='fields'} == {k:v for k,v in after.items() if k!='fields'}
        assert before['decision'] == after['decision'] == 'register'
        if ident not in selected_ids: assert before == after
        a = {f['language']:f for f in before['fields']}; b = {f['language']:f for f in after['fields']}; assert set(a) == set(b)
        for lang, f in a.items():
            key = (ident, lang)
            if f == b[lang]: unchanged_fields += 1; assert key not in selected_keys
            else:
                changed.add(key); assert key in selected_keys and not f['reviewed'] and b[lang]['reviewed']
                assert f['text_sha256'] == b[lang]['text_sha256'] and b[lang]['selected_spans']
    assert changed == selected_keys and unchanged_fields == 2335
    old_queue = (WORK / 'phase17-independent-readback/downloaded' / QUEUE).read_bytes()
    assert sha(old_queue) == audit['queue']['before_sha256'] == '74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
    assert lookup(QUEUE)['git_object_sha1'] == git(old_queue)
    before_lines = gzip.decompress(old_queue).splitlines(keepends=True)
    after_lines = gzip.decompress(candidate_queue).splitlines(keepends=True)
    queue_before = [json.loads(x) for x in before_lines]; queue_after = [json.loads(x) for x in after_lines]
    removed = {(r['id'], f['language']) for r in queue_before if r['id'] in selected_ids for f in r['fields']}
    assert removed == selected_keys and after_lines == [line for line in before_lines if json.loads(line)['id'] not in selected_ids]
    q_before = collections.Counter(f['language'] for r in queue_before for f in r['fields'])
    q_after = collections.Counter(f['language'] for r in queue_after for f in r['fields'])
    assert len(queue_before) == 3379 and q_before == {'hi':3285,'ur':3076}
    assert len(queue_after) == 3354 and q_after == {'hi':3260,'ur':3051}
    delta = json.loads(primary_files[current('priority-field-queue-delta.json')])
    assert {(r['occurrence_id'],r['language']) for r in delta['removed_fields']} == selected_keys
    for r in delta['removed_fields']:
        a = next(f for f in old[r['occurrence_id']]['fields'] if f['language'] == r['language'])
        b = next(f for f in new[r['occurrence_id']]['fields'] if f['language'] == r['language'])
        assert sha(importer.json_bytes(a)) == r['before_field_decision_sha256']
        assert sha(importer.json_bytes(b)) == r['after_field_decision_sha256']
        assert a['decision'] == r['before_decision'] and b['decision'] == r['after_decision']
    for item in config['phase19_receipts']:
        b = Path(item['local_path']).read_bytes(); assert len(b) == item['bytes'] and sha(b) == item['sha256']
        add(PREFIX / 'receipts' / ('phase19-' + item['name']), b, 'Exact phase19 publication receipt or verifier')
    before_doc = (readback / 'downloaded' / DOC).read_bytes()
    assert len(before_doc) == 102908 and sha(before_doc) == '49531b091370524d35dc505e2b0b24b9401db39ad493d2e790c47f17c666318a'
    assert lookup(DOC)['git_object_sha1'] == git(before_doc)
    prefix = (HERE / config['status_prefix_path']).read_bytes(); assert sha(prefix) == config['expected_status_prefix_sha256']
    new_doc = prefix + before_doc; assert new_doc[len(prefix):] == before_doc
    add(DOC, new_doc, 'Root-approved English prefix and complete untouched phase19 document suffix')
    add(PREFIX / 'previous-status-document.md', before_doc, 'Exact complete prior102908-byte phase19 document')
    add(PREFIX / 'current-status-prefix.md', prefix, 'Exact root-approved current English status prefix')
    add(PREFIX / 'document-update-receipt.json', enc({'schema':'versioned-status-document-update-v1','base_commit':base,
        'before':binding(before_doc),'prefix':binding(prefix),'after':binding(new_doc),'root_prefix_approval':True,
        'full_prior_document_is_exact_suffix':True,'archive_path':str(PREFIX/'previous-status-document.md')}), 'Exact complete historical document preservation')
    add(PREFIX / 'staging-inputs.json', config_raw, 'Exact final staging declarations')
    add(PREFIX / 'assemble_publication.py', Path(__file__).read_bytes(), 'Exact local staging validator and assembler')
    add(PREFIX / 'portable-input-package-manifests.json', enc({'schema':'portable-input-manifest-inventory-v1','packages':portable}), 'Portable path/hash input inventories without local paths')
    proofs = {path:lookup(path) for path in staged}
    existing = {p for p,r in proofs.items() if r['status']=='existing_path'}
    assert existing == {ACTIVE,QUEUE,DOC}, ('Unexpected existing overwrite',existing)
    for path in existing: assert proofs[path]['type']=='blob' and proofs[path]['mode']=='100644'
    assert proofs[ACTIVE]['git_object_sha1']==git(active_before)
    assert not any(p.startswith(('scripts/','.github/','materials/','catalog/')) for p in staged)
    tree_path = str(PREFIX/'complete-used-base-ancestor-trees.json.gz'); assert lookup(tree_path)['status']=='new_path'
    add(tree_path,gzip.compress(enc({'schema':'exact-base-complete-ancestor-proof-v1','base_commit':base,'root_tree_sha':root_sha,
        'trees':[{'git_tree_sha1':h,'entries':pool[h],'origins':origins[h]} for h in sorted(used)]}),mtime=0), 'Complete fresh GitHub tree entries used by every path proof')
    validation={'schema':'hadith-bank-phase20-publication-staging-validation-v1','result':'PASS','base_commit':base,'base_root_tree_sha':root_sha,
        'expected_existing_overwrites':sorted(existing),'path_proofs':proofs,'complete_ancestor_tree_proof_path':tree_path,
        'unchanged_other40_active_ledgers':unchanged_ledgers,'active_ledgers_before_and_after':41,'distinct_manual_parent_ids_before_and_after':3490,
        'all477_parent_dispositions_unchanged':True,'untouched_field_decisions':2335,'exact_changed_fields':50,'occurrences_extended':25,
        'parent_registration_delta':0,'source_occurrence_delta':0,'new_linguistic_reading_during_staging':0,
        'source_first_and_independent_full_readings_each':{'fields':50,'characters':27103,'utf8_bytes':58879},
        'exact_independent_final_native_report_sha256':sha(audit_raw),'native477_before_after_passed_in_bound_primary_and_independent_audits':True,
        'native_tests_repeated_for_this_staging':False,'lossless_partitions_in_bound_audit':2385,'prior_script_corrections_preserved':19,
        'queue_before':{'sha256':sha(old_queue),'fields':6361,'occurrences':3379,'by_language':dict(q_before)},
        'queue_after':{'sha256':sha(candidate_queue),'fields':6311,'occurrences':3354,'by_language':dict(q_after)},
        'all_remaining_queue_line_bytes_and_order_exact':True,'queue_delta_final_field_hashes_and_actions_verified':True,
        'bound_input_packages':provenance,'github_writes':0,'source_http_requests':0,'frozen_input_mutations':0,
        'live_deployment_of_phase19_or_phase20_claimed':False,'fresh_base_and_expected_head_lease_required_before_publication':True}
    validation_path=str(PREFIX/'staging-validation.json'); assert lookup(validation_path)['status']=='new_path'
    add(validation_path,enc(validation),'Exact local composition/path/baseline/queue-preservation validation')
    payload_path=str(PREFIX/'payload-file-manifest.json'); assert lookup(payload_path)['status']=='new_path'
    payload={'schema':'portable-publication-payload-files-v1','base_commit':base,'self_excluded':payload_path,
        'files':[{'path':p,**binding(v[0]),'origin':v[1]} for p,v in sorted(staged.items())]}
    add(payload_path,enc(payload),'Portable payload path/size/SHA256/Git-blob inventory; self omitted')
    rows=[]
    for path,(b,origin) in sorted(staged.items()):
        p=HERE/'publish'/path;write_exact(p,b)
        rows.append({'path':path,'local_path':str(p),'source_path':str(p),**binding(b),'origin':origin})
    before_by_path={ACTIVE:active_before,QUEUE:old_queue,DOC:before_doc}
    manifest={'schema':'hadith-bank-frozen-phase20-publication-manifest-v1','repository':'blaghtayt-alt/Hadith-Bank','branch':'main',
        'documented_base_commit':base,'base_root_tree_sha':root_sha,'source_review_pin':config['source_review_pin'],
        'files':rows,'total_files':len(rows),'total_bytes':sum(r['bytes'] for r in rows),'existing_paths_changed':3,
        'expected_overwrites':[{'path':p,'before':binding(before_by_path[p]),'after':binding(staged[p][0])} for p in sorted(existing)],
        'new_repository_paths_at_documented_base':len(rows)-3,'existing_active_ledgers_changed':1,'new_active_ledgers':0,
        'parent_registration_delta':0,'source_occurrence_delta':0,'canonical_priority_queue_changed':True,
        'local_validation':{'status':'PASS','path':validation_path,'sha256':sha(enc(validation)),
            'portable_payload_file_manifest_path':payload_path,'portable_payload_file_manifest_sha256':sha(enc(payload))},
        'input_packages':provenance,'fresh_base_required_before_publication':True,'github_branch_updated':False,
        'current_publication_live_deployment_verified':False}
    write_exact(HERE/'manifest.json',enc(manifest));write_exact(HERE/'staging-validation.json',enc(validation))
    print(json.dumps({'status':'PASS','manifest_sha256':sha(enc(manifest)),'files':len(rows),'bytes':manifest['total_bytes'],
        'validation_sha256':sha(enc(validation)),'payload_manifest_sha256':sha(enc(payload)),'existing_overwrites':sorted(existing),
        'document':binding(new_doc),'queue':binding(candidate_queue),'active':binding(primary_files[ACTIVE])}))

if __name__=='__main__':main()
