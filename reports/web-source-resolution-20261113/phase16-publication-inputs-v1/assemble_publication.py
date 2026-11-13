"""Assemble frozen phase16 payloads; never update GitHub or prior packages."""
from pathlib import Path, PurePosixPath
import collections, datetime, hashlib, json

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
BASE = 'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d'
BASE_TREE = 'bb937a8efb1fd95128f02b63028f4d25838d9355'
DOC = 'docs/WEB-SOURCE-RESOLUTION-20261113.md'
PREFIX = 'reports/web-source-resolution-20261113/phase16-publication-inputs-v1'
REVIEWS = 'imports/web-deenhindi-20261112/reviews'


def unique_pairs(items):
    result = {}
    for key, value in items:
        assert key not in result, ('duplicate JSON key', key)
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_pairs)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def git(kind, value):
    return hashlib.sha1(kind.encode() + b' ' + str(len(value)).encode() + b'\0' + value).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def safe(relative):
    path = PurePosixPath(relative)
    assert relative and not path.is_absolute() and '..' not in path.parts and '\\' not in relative and '\0' not in relative
    return path.as_posix()


def binding(raw):
    return {'bytes': len(raw), 'sha256': sha(raw), 'git_blob_sha1': git('blob', raw)}


def checked_manifest(path, expected_sha):
    path = Path(path); data = path.read_bytes(); assert sha(data) == expected_sha
    manifest = json.loads(data, object_pairs_hook=unique_pairs); result = []
    for item in manifest['files']:
        relative = safe(item.get('path', item.get('repository_path')))
        local = Path(item.get('local_path') or item['source_path'])
        assert local.is_file() and not local.is_symlink() and local.resolve().is_relative_to(path.parent.resolve())
        raw = local.read_bytes(); receipt = binding(raw)
        assert receipt['bytes'] == item.get('bytes', item.get('size_bytes')) and receipt['sha256'] == item['sha256']
        assert not item.get('git_blob_sha1') or receipt['git_blob_sha1'] == item['git_blob_sha1']
        result.append((relative, local, raw, receipt))
    assert len(result) == len({item[0] for item in result})
    return data, result


def tree_authority():
    proof_path = WORK / 'phase15-final-publication/tree-verification-receipts.json'
    proof_raw = proof_path.read_bytes()
    assert sha(proof_raw) == '8929e8d135183c355c9af7edf5236fc6e50734173cd51e3a355a70cd5386cb4b'
    proof = json.loads(proof_raw, object_pairs_hook=unique_pairs)
    assert proof['complete'] is True and proof['root_tree_sha'] == BASE_TREE
    trees = {}
    for entry in proof['trees']:
        trees[entry['directory']] = {'path': entry['directory'], 'sha': entry['after_tree_sha'], 'tree': entry['entries']}
    readback = WORK / 'phase15-independent-readback/input'
    root_tree = json.loads(read(readback / 'github-root_tree.json')['content']); root_tree['path'] = ''
    for tree in [root_tree] + [read(path) for path in sorted(readback.glob('tree-*.json'))]:
        assert tree['truncated'] is False
        if tree['path'] in trees: assert trees[tree['path']]['sha'] == tree['sha']
        trees[tree['path']] = tree
    receipts = []
    for path, tree in trees.items():
        entries = tree['tree']; assert len(entries) == len({entry['path'] for entry in entries})
        assert all('/' not in entry['path'] and '\0' not in entry['path'] for entry in entries)
        ordered = sorted(entries, key=lambda entry: (entry['path'] + ('/' if entry['type'] == 'tree' else '')).encode())
        raw = b''.join((entry['mode'].lstrip('0') + ' ' + entry['path']).encode() + b'\0' + bytes.fromhex(entry['sha']) for entry in ordered)
        assert git('tree', raw) == tree['sha'], path
        if path:
            parent, _, name = path.rpartition('/')
            assert parent in trees and next(entry for entry in trees[parent]['tree'] if entry['path'] == name)['sha'] == tree['sha']
        else: assert tree['sha'] == BASE_TREE
        receipts.append({'path': path or '/', 'git_tree_sha1': tree['sha'], 'complete_entries': len(entries)})
    return trees, receipts


def prove_path(relative, trees):
    path = ''; pieces = PurePosixPath(relative).parts
    for index, name in enumerate(pieces):
        assert path in trees, ('missing complete tree proof for an existing ancestor', path, relative)
        tree = trees[path]; found = next((entry for entry in tree['tree'] if entry['path'] == name), None)
        if found is None:
            return {'path': relative, 'status': 'NEW_AT_PINNED_BASE', 'base_commit': BASE,
                    'first_absent_child': name, 'proven_parent': path or '/', 'complete_parent_tree_sha1': tree['sha']}
        if index == len(pieces) - 1:
            assert relative == DOC and found['type'] == 'blob', ('unsolicited overwrite rejected', relative)
            return {'path': relative, 'status': 'SOLE_PERMITTED_DOCUMENT_UPDATE', 'base_commit': BASE,
                    'before_git_blob_sha1': found['sha'], 'complete_parent_tree_sha1': tree['sha']}
        assert found['type'] == 'tree', ('non-directory ancestor', relative, name)
        path = name if not path else path + '/' + name
    raise AssertionError(relative)


def main():
    assert not (HERE / 'delivery-manifest.json').exists(), 'Final staging is immutable.'
    config_path = HERE / 'publication-inputs.json'; config_raw = config_path.read_bytes(); config = read(config_path)
    assert config['all_inputs_final'] is True and config['document']['final'] is True
    assert config['path_absence_base_commit'] == BASE
    kinds = collections.Counter(item['kind'] for item in config['package_manifests'])
    assert kinds == {'primary': 4, 'independent': 4, 'integration': 1, 'source_partitions': 1, 'phase15_readback': 1, 'reader5589': 1}
    trees, tree_receipts = tree_authority()
    staged, package_receipts, duplicates = {}, [], []

    def add(relative, raw, origin):
        relative = safe(relative); receipt = binding(raw)
        assert relative == DOC or relative.startswith(REVIEWS + '/') or relative.startswith('reports/web-source-resolution-20261113/')
        if relative in staged:
            assert staged[relative]['receipt'] == receipt and staged[relative]['bytes'] == raw, ('conflicting target payload', relative)
            duplicates.append({'path': relative, 'sha256': receipt['sha256'], 'additional_origin': origin})
            staged[relative]['origins'].append(origin)
        else: staged[relative] = {'bytes': raw, 'receipt': receipt, 'origins': [origin]}

    active_expected = set()
    for spec in config['package_manifests']:
        manifest_raw, files = checked_manifest(spec['manifest_path'], spec['manifest_sha256'])
        prefix = spec.get('payload_repository_prefix', '')
        for relative, local, raw, receipt in files:
            target = safe(prefix + '/' + relative) if prefix else relative
            add(target, raw, {'package': spec['name'], 'kind': spec['kind'], 'source_path': str(local)})
            if spec['kind'] == 'primary' and str(PurePosixPath(relative).parent) == REVIEWS and PurePosixPath(relative).name.startswith('source-review'):
                assert 'checkpoint5589' in relative
                active_expected.add(relative)
        manifest_target = PREFIX + '/manifests/' + spec['name'] + '.json'
        add(manifest_target, manifest_raw, {'package': spec['name'], 'kind': 'exact_input_manifest', 'source_path': spec['manifest_path']})
        package_receipts.append({'name': spec['name'], 'kind': spec['kind'], 'manifest_sha256': spec['manifest_sha256'],
                                 'payload_files': len(files), 'manifest_repository_path': manifest_target})
    assert len(active_expected) == 4
    for spec in config['extra_files']:
        path = Path(spec['local_path']); assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes(); assert sha(raw) == spec['sha256']
        add(spec['path'], raw, {'kind': spec['kind'], 'source_path': str(path)})
    document = config['document']; doc_path = Path(document['local_path']); raw = doc_path.read_bytes()
    assert sha(raw) == document['sha256'] and len(raw) == document['bytes']
    assert document['before_sha256'] == 'ee2dbc858e5100c0e0d29ebb2426a955caebf280b66c2491475e42e5da3f867d'
    add(DOC, raw, {'kind': 'root_authored_final_status_document', 'source_path': str(doc_path)})
    add(PREFIX + '/publication-inputs.json', config_raw, {'kind': 'exact_staging_configuration'})
    add(PREFIX + '/assemble_publication.py', Path(__file__).read_bytes(), {'kind': 'immutable_assembler_source'})
    active_staged = {path for path in staged if str(PurePosixPath(path).parent) == REVIEWS and PurePosixPath(path).name.startswith('source-review')}
    assert active_staged == active_expected
    proofs = [prove_path(relative, trees) for relative in sorted(staged)]
    document_proof = next(item for item in proofs if item['path'] == DOC)
    assert document_proof['before_git_blob_sha1'] == '25a9bd3d09df08589a693a00715641d83c88c1b6'
    assert sum(item['status'] != 'NEW_AT_PINNED_BASE' for item in proofs) == 1
    proof = {'schema': 'hadith-bank-phase16-immutable-publication-staging-validation-v1', 'result': 'PASS',
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_checkpoint': '5589a3ffc3b43c3324ae26f2b6c4d33152834456',
        'path_absence_base_commit': BASE, 'path_absence_base_tree': BASE_TREE,
        'latest_main_proof_claimed': False, 'later_main_observation_from_root': config.get('later_main_observation_from_root'),
        'fresh_main_complete_tree_and_expected_head_lease_required': True,
        'frozen_payloads_checked': len(staged), 'new_active_ledgers': sorted(active_staged),
        'only_permitted_existing_path': DOC, 'canonical_priority_queue_staged_or_changed': False,
        'prior_active_ledgers_staged_or_changed': False, 'package_receipts': package_receipts,
        'identical_path_hash_deduplications': duplicates, 'rehash_verified_complete_trees': tree_receipts,
        'path_proofs': proofs, 'github_writes': 0, 'source_http_requests': 0,
        'limitations': 'Every absence proof is relative only to the exact e3f88ac8 tree. Root must preserve the later concurrent merge and refresh current complete trees before a normal expected-head publication. This assembly makes no new source acquisition, linguistic decision, export or deployment claim.'}
    proof_relative = PREFIX + '/staging-validation.json'
    assert prove_path(proof_relative, trees)['status'] == 'NEW_AT_PINNED_BASE'
    add(proof_relative, enc(proof), {'kind': 'staging_validation'})
    files = []
    for relative, item in sorted(staged.items()):
        path = HERE / 'publish' / relative; path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists(): assert path.read_bytes() == item['bytes']
        else: path.write_bytes(item['bytes'])
        assert binding(path.read_bytes()) == item['receipt']
        files.append({'path': relative, 'local_path': str(path), **item['receipt']})
    assert config_path.read_bytes() == config_raw
    for spec in config['package_manifests']: checked_manifest(spec['manifest_path'], spec['manifest_sha256'])
    manifest = {'schema': 'hadith-bank-immutable-phase16-publication-staging-v1', 'result': 'PASS',
        'source_checkpoint': '5589a3ffc3b43c3324ae26f2b6c4d33152834456', 'path_absence_base_commit': BASE,
        'latest_main_proof_claimed': False, 'fresh_main_tree_and_expected_head_lease_required': True,
        'only_expected_overwrite': {'path': DOC, 'before_sha256': document['before_sha256'], 'before_git_blob_sha1': document_proof['before_git_blob_sha1']},
        'files': files, 'total_files': len(files), 'total_bytes': sum(item['bytes'] for item in files),
        'staging_validation_sha256': sha(enc(proof)), 'github_writes': 0}
    raw = enc(manifest); (HERE / 'delivery-manifest.json').write_bytes(raw)
    print(json.dumps({'result': 'PASS', 'manifest_sha256': sha(raw), 'files': len(files),
        'bytes': manifest['total_bytes'], 'new_paths': len(files) - 1, 'document_updates': 1,
        'path_absence_base': BASE, 'validation_sha256': sha(enc(proof))}, indent=2))


if __name__ == '__main__':
    main()
