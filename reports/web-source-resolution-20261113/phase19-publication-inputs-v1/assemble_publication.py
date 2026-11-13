"""Freeze phase19 on audited0d2 while preserving d369 reviews and all prior doc bytes."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import collections
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
OUT = HERE / 'publish'
PREFIX = Path('reports/web-source-resolution-20261113/phase19-publication-inputs-v1')
REV = Path('imports/web-deenhindi-20261112/reviews')
DOC = 'docs/WEB-SOURCE-RESOLUTION-20261113.md'
QUEUE = 'reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda raw: hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
enc = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def tree_sha(entries):
    ordered = sorted(entries, key=lambda r: (r['path'] + ('/' if r['type'] == 'tree' else '')).encode())
    raw = b''.join((str(r['mode']).lstrip('0') + ' ' + r['path']).encode() + b'\0' + bytes.fromhex(r['sha']) for r in ordered)
    return hashlib.sha1(b'tree ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def safe(path):
    path = str(path); p = PurePosixPath(path)
    assert path and not p.is_absolute() and '..' not in p.parts and '\\' not in path
    return path


def main():
    assert not (HERE / 'manifest.json').exists(), 'A frozen publication stage is immutable.'
    config_raw = (HERE / 'staging-inputs.json').read_bytes(); config = json.loads(config_raw)
    base = config['documented_base_commit']; root_sha = config['root_tree_sha']
    assert base == '0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a'
    assert root_sha == 'd5a7676fba4cc52405c551649e90b96b1b6dd5da'
    assert config['root_status_review_complete'] is True
    staged = {}; packages = {}; provenance = []

    def add(path, raw, origin):
        path = safe(path)
        if path in staged:
            assert staged[path]['sha256'] == sha(raw) and staged[path]['bytes'] == len(raw), ('path collision', path)
            staged[path]['origins'].append(origin)
            return
        dest = OUT / path; dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            assert dest.read_bytes() == raw, ('staged bytes changed', path)
        else:
            dest.write_bytes(raw)
        staged[path] = {'path': path, 'local_path': str(dest), 'bytes': len(raw), 'sha256': sha(raw),
                        'git_blob_sha1': git(raw), 'mode': '100644', 'origins': [origin]}

    for item in config['packages']:
        name = item['name']; path = WORK / item['manifest_path']; raw = path.read_bytes()
        assert sha(raw) == item['manifest_sha256'], name
        manifest = json.loads(raw)
        assert name not in packages and len({f['path'] for f in manifest['files']}) == len(manifest['files'])
        for f in manifest['files']:
            local = Path(f.get('local_path', f.get('source_path')))
            assert local.is_file() and not local.is_symlink() and local.resolve().is_relative_to(path.parent.resolve())
            data = local.read_bytes()
            assert len(data) == f.get('bytes', f.get('size_bytes')) and sha(data) == f['sha256']
            if f.get('git_blob_sha1'):
                assert git(data) == f['git_blob_sha1']
            add(f['path'], data, name)
        add(PREFIX / 'manifests' / (name + '.json'), raw, name + ' immutable input manifest')
        packages[name] = manifest
        provenance.append({'name': name, 'local_manifest': str(path), 'sha256': sha(raw),
                           'files': len(manifest['files']), 'bytes': sum(f.get('bytes', f.get('size_bytes')) for f in manifest['files'])})
    assert len(packages) == 12

    def payload(name, suffix):
        matches = [f for f in packages[name]['files'] if f['path'].endswith(suffix)]
        assert len(matches) == 1, (name, suffix)
        return matches[0], Path(matches[0]['local_path']).read_bytes()

    _, integration_raw = payload('combined80-integration', 'validation-report.json')
    assert sha(integration_raw) == config['integration_report_sha256']
    integration = json.loads(integration_raw)
    expected = {'register': 75, 'exclude': 5, 'read_fields': 178, 'admitted': 153, 'read_context': 25,
                'unread_context': 220, 'empty': 2, 'source_slots': 400, 'partitions': 398,
                'read_characters': 68466, 'read_utf8_bytes': 130414}
    assert integration['result'] == 'PASS' and integration['native_new80_apply_finish'] == 'PASS'
    assert all(integration['counts'][k] == v for k, v in expected.items())
    assert integration['source_commit'] == config['source_review_pin'] == '3e574b9e7e4dd7cf8bc23232249004a18692c61c'
    assert integration['published_review_baseline_commit'] == config['published_review_baseline_commit'] == 'd369026ca42af6ff972ffab83c9180e03759da41'
    assert (integration['source_count'], integration['source_files_verified'], integration['full_raw_reparses_bound']) == (80, 160, 80)
    assert (integration['native_combined_loader_ledgers'], integration['native_combined_loader_ids']) == (41, 3490)
    assert (integration['prior37_published_manual_ledgers'], integration['prior_published_manual_ids']) == (37, 3410)
    assert integration['all37_prior_blobs_dependencies_and3410_decisions_unchanged'] and not integration['id_collisions']
    primary_entries = []; ids = set(); decisions = {}; source_counts = collections.Counter()
    field_counts = collections.Counter(); read_field_ids = []
    for name in ('primary-bukhari20', 'primary-muslim20', 'primary-nasai13_ibnmajah7', 'primary-abudawud4_tirmidhi11_bukhari2_ibnmajah3'):
        active = [f for f in packages[name]['files'] if Path(f['path']).parent == REV and Path(f['path']).name.startswith('source-review-')]
        assert len(active) == 1
        entry = active[0]; primary_entries.append(entry)
        ledger = json.loads(gzip.decompress((OUT / entry['path']).read_bytes()))
        baseline = OUT / safe(ledger['source_ledger_path'])
        assert sha(baseline.read_bytes()) == ledger['source_ledger_sha256']
        saved = [json.loads(line) for line in gzip.decompress(baseline.read_bytes()).splitlines()]
        saved_ids = {'deenhindi-' + r['collection'] + ':' + r['number']: r for r in saved}
        records = ledger.get('records', ledger.get('decisions'))
        assert len(saved_ids) == len(records) == 20
        for record in records:
            oid = record.get('id', record.get('occurrence_id'))
            assert oid in saved_ids and oid not in ids
            ids.add(oid); decisions[oid] = record; source_counts[record['decision']] += 1
            for field in record.get('field_reviews', record.get('fields')):
                if field['reviewed']:
                    field_counts['read_fields'] += 1
                    field_counts['read_characters'] += field['chars_reviewed']
                    field_counts['read_utf8_bytes'] += field['bytes_reviewed']
                    read_field_ids.append((oid, field['language']))
                    field_counts['admitted' if field.get('spans', field.get('selected_spans', [])) else 'read_context'] += 1
    assert len(ids) == 80 and source_counts == {'register': 75, 'exclude': 5}
    assert all(field_counts[k] == expected[k] for k in field_counts)
    assert len(read_field_ids) == len(set(read_field_ids)) == 178
    _, acq_raw = payload('acquisition-0d2-state-history', 'saved-state-audit.json')
    assert sha(acq_raw) == config['acquisition_report_sha256']
    acq = json.loads(acq_raw)
    assert acq['status'] == 'PASS' and acq['saved_commit'] == base and acq['saved_tree'] == root_sha
    assert acq['saved_parent'] == config['published_review_baseline_commit']
    progress = acq['saved_progress']
    actual = {k: progress[k] for k in ('imported_count', 'registered_hadith_count', 'non_narration_source_entries', 'classification_pending_count', 'pending_fetch_count', 'errors_count')}
    assert actual == {'imported_count': 17627, 'registered_hadith_count': 17301, 'non_narration_source_entries': 160,
                      'classification_pending_count': 166, 'pending_fetch_count': 18763, 'errors_count': 0}
    part = acq['held_partition']; keys = {oid.removeprefix('deenhindi-') for oid in ids}
    assert set(part['retained_prior80_keys']) == keys
    assert len(part['new86_keys']) == 86 and not set(part['new86_keys']) & keys
    assert set(part['current166_held_keys']) == keys | set(part['new86_keys'])
    assert len(part['prior92_registered_keys']) == 87 and len(part['prior92_source_only_keys']) == 5
    preserve = acq['source_state_preservation']
    assert preserve['all17131_prior_imported_descriptors_exact'] and preserve['all1000_error_histories_exact'] and preserve['all1000_consumed_attempts_exact']
    assert preserve['new_imported_ids'] == 496 and preserve['new_retry_attempts'] == 0
    assert acq['source_controls']['source_stop_guards_and_cadence_unchanged']
    assert acq['bounded_artifact_audit']['source_files_verified'] == 332 and acq['bounded_artifact_audit']['raw_and_parsed_pairs_reopened_and_reparsed'] == 166
    projection = {'fetched': 17627, 'registered': 17301 + source_counts['register'],
                  'source_only': 160 + source_counts['exclude'], 'held': 166 - len(ids), 'unfetched': 18763}
    assert projection == {'fetched': 17627, 'registered': 17376, 'source_only': 165, 'held': 86, 'unfetched': 18763}
    prior_receipts = {}
    for item in config['phase18_publication_receipts']:
        data = (WORK / 'phase18-final-publication' / item['name']).read_bytes()
        assert sha(data) == item['sha256'] and len(data) == item['bytes']
        prior_receipts[item['name']] = json.loads(data)
        add(PREFIX / 'receipts' / ('phase18-' + item['name']), data, 'Exact phase18 publication receipt')
    pub = prior_receipts['publication-receipt.json']
    assert pub['commit_sha'] == acq['saved_parent'] and pub['root_tree_sha'] == '84b3a3b3ee1fbab4a2dbb6efbf68a69e94cc2d70'
    assert pub['parent_sha'] == 'a3f9427d7bd235d27318a9470910c182b806a26c'
    assert pub['manifest_sha256'] == sha((WORK / 'phase18-final-publication/manifest.json').read_bytes())
    assert pub['force'] is False

    # Every reused tree is accepted only after reconstructing its Git identity
    # and linking it from the exact audited0d2 root used below.
    pool = {}; origins = collections.defaultdict(list); used = set()

    def add_tree(entries, expected_sha, origin):
        assert len(entries) == len({r['path'] for r in entries})
        assert all('/' not in r['path'] and '\0' not in r['path'] for r in entries)
        assert tree_sha(entries) == expected_sha
        canonical = sorted([{'path': r['path'], 'mode': '040000' if r['type'] == 'tree' else str(r['mode']).lstrip('0'),
                             'type': r['type'], 'sha': r['sha']} for r in entries], key=lambda r: r['path'])
        assert tree_sha(canonical) == expected_sha
        if expected_sha in pool:
            assert pool[expected_sha] == canonical
        else:
            pool[expected_sha] = canonical
        origins[expected_sha].append(origin)

    for directory, tree in prior_receipts['verified-base-trees.json'].items():
        if tree is not None and tree.get('sha'):
            assert not tree.get('truncated', False)
            add_tree(tree['tree'], tree['sha'], 'phase18 verified before tree ' + directory)
        elif tree is not None:
            assert tree.get('sha') is None and tree['tree'] == []
    for item in prior_receipts['tree-verification-receipts.json']:
        tree = item['complete_tree']; assert not tree.get('truncated', False)
        assert tree['sha'] == item['after_tree_sha']
        add_tree(tree['tree'], tree['sha'], 'phase18 published complete tree ' + item['directory'])
    readback = WORK / 'phase18-independent-readback'
    for path in sorted((readback / 'input').glob('*tree*.json')):
        response = json.loads(path.read_bytes())
        if 'content' not in response:
            continue
        tree = json.loads(response['content'])
        assert not tree.get('truncated', False)
        add_tree(tree['tree'], tree['sha'], 'Independent phase18 GitHub response ' + path.name)
    _, current_tree_raw = payload('acquisition-0d2-state-history', 'complete-path-trees.json.gz')
    current_trees = json.loads(gzip.decompress(current_tree_raw))
    assert current_trees['']['sha'] == root_sha and len(current_trees) == 7
    for directory, tree in current_trees.items():
        assert not tree.get('truncated', False)
        add_tree(tree['tree'], tree['sha'], 'Audited0d2 complete tree ' + directory)

    def lookup(path):
        directory = ''; expected_sha = root_sha; parts = safe(path).split('/'); chain = []
        for index, name in enumerate(parts):
            assert expected_sha in pool, ('Missing complete current ancestor', directory, expected_sha, path)
            used.add(expected_sha); chain.append({'directory': directory, 'git_tree_sha1': expected_sha})
            found = [r for r in pool[expected_sha] if r['path'] == name]
            assert len(found) <= 1
            if not found:
                return {'status': 'new_path', 'first_absent_component': '/'.join(parts[:index + 1]), 'ancestor_chain': chain}
            entry = found[0]
            if index == len(parts) - 1:
                return {'status': 'existing_path', 'git_object_sha1': entry['sha'], 'mode': entry['mode'],
                        'type': entry['type'], 'ancestor_chain': chain}
            assert entry['type'] == 'tree'
            expected_sha = entry['sha']; directory = '/'.join(parts[:index + 1])
        raise AssertionError('unreachable')

    d369_root = pool['84b3a3b3ee1fbab4a2dbb6efbf68a69e94cc2d70']
    a = {r['path']: r for r in d369_root}; b = {r['path']: r for r in pool[root_sha]}
    assert set(a) == set(b) and {k for k in a if a[k] != b[k]} == {'imports', 'materials'}
    queue_raw = (WORK / 'phase17-independent-readback/downloaded' / QUEUE).read_bytes()
    assert sha(queue_raw) == '74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
    queue_proof = lookup(QUEUE); assert queue_proof['git_object_sha1'] == git(queue_raw)
    queue_rows = [json.loads(line) for line in gzip.decompress(queue_raw).splitlines()]
    queue_langs = collections.Counter(f['language'] for row in queue_rows for f in row['fields'])
    assert len(queue_rows) == 3379 and queue_langs == {'hi': 3285, 'ur': 3076}
    review_proof = lookup(REV.as_posix()); assert review_proof['type'] == 'tree'
    assert review_proof['git_object_sha1'] == '97c635390871214e19e18e54453a33bc963a492c'
    old_reviews = [r for r in pool[review_proof['git_object_sha1']] if r['type'] == 'blob' and r['path'].startswith('source-review-')]
    assert len(old_reviews) == 37 and QUEUE not in staged
    assert not any((REV / r['path']).as_posix() in staged for r in old_reviews)
    baseline = WORK / 'phase19-checkpoint3e574-independent-integration/validation/published-reviews'
    for r in old_reviews:
        assert git((baseline / REV / r['path']).read_bytes()) == r['sha']
    before_doc = (readback / 'downloaded' / DOC).read_bytes()
    assert len(before_doc) == 92010 and sha(before_doc) == 'e896ef3e622e5f911d6c1d288133b6cc7783e15d8b9ec0061b9c3859ccba993c'
    before_doc_proof = lookup(DOC); assert before_doc_proof['git_object_sha1'] == git(before_doc)
    prefix = (HERE / config['status_prefix_path']).read_bytes()
    assert sha(prefix) == config['root_approved_status_prefix_sha256'] == '7699a47d111d2e7bcfca1a0e2ae7f7214b89d99ededaca897dd17fa752bc1468'
    assert b'Draft checkpoint note' not in prefix and b'once frozen' not in prefix
    new_doc = prefix + before_doc
    assert new_doc[len(prefix):] == before_doc and new_doc.endswith(before_doc)
    add(DOC, new_doc, 'Approved English status prefix followed by every prior document byte')
    add(PREFIX / 'previous-status-document.md', before_doc, 'Exact complete92010-byte d369 document preserved at0d2')
    add(PREFIX / 'current-status-prefix.md', prefix, 'Root-read and approved current English status prefix')
    doc_receipt = {'schema': 'hadith-bank-versioned-status-document-update-v1', 'documented_base_commit': base, 'path': DOC,
        'previous_review_publication': config['published_review_baseline_commit'],
        'before_bytes': len(before_doc), 'before_sha256': sha(before_doc), 'before_git_blob_sha1': git(before_doc),
        'prefix_bytes': len(prefix), 'prefix_sha256': sha(prefix), 'root_completed_prefix_read_and_approval': True,
        'after_bytes': len(new_doc), 'after_sha256': sha(new_doc), 'after_git_blob_sha1': git(new_doc),
        'full_previous_document_archived_path': str(PREFIX / 'previous-status-document.md'),
        'complete_old_document_exact_suffix_including_original_title': True,
        'current_saved_export_source_commit': base, 'review_projection_is_a_new_saved_export': False,
        'current_publication_live_deployment_claimed': False}
    add(PREFIX / 'document-update-receipt.json', enc(doc_receipt), 'Exact prior document byte-preservation proof')
    add(PREFIX / 'staging-inputs.json', config_raw, 'Exact12 frozen package and7 publication receipt declarations')
    add(PREFIX / 'assemble_publication.py', Path(__file__).read_bytes(), 'Exact local publication assembler')
    proofs = {path: lookup(path) for path in staged}
    existing = {path for path, proof in proofs.items() if proof['status'] == 'existing_path'}
    assert existing == {DOC}, ('Unexpected existing-path write', existing)
    assert proofs[DOC]['type'] == 'blob' and proofs[DOC]['mode'] == '100644'
    assert all(lookup(f['path'])['status'] == 'new_path' for f in primary_entries)
    assert all(path.startswith(('docs/', 'imports/web-deenhindi-20261112/reviews/', 'reports/web-source-resolution-20261113/')) for path in staged)
    tree_path = str(PREFIX / 'complete-used-base-ancestor-trees.json.gz')
    assert lookup(tree_path)['status'] == 'new_path'
    tree_proof = {'schema': 'hadith-bank-exact-base-complete-ancestor-proof-v1', 'commit': base, 'root_tree_sha': root_sha,
        'scope': 'Complete reused Git tree identities are reconstructed and linked from the exact audited0d2 root. Other branches are preserved by the fresh-head lease at actual publication.',
        'trees': [{'git_tree_sha1': h, 'entries': pool[h], 'origins': origins[h]} for h in sorted(used)]}
    add(tree_path, gzip.compress(enc(tree_proof), mtime=0), 'Complete actual ancestor trees used by path proofs')
    validation = {'schema': 'hadith-bank-phase19-publication-staging-validation-v1', 'result': 'PASS',
        'documented_base_commit': base, 'base_root_tree_sha': root_sha,
        'published_review_baseline_commit': config['published_review_baseline_commit'], 'only_existing_path_update': DOC,
        'path_proofs': proofs, 'complete_ancestor_tree_proof_path': tree_path,
        'old37_active_review_entries_unchanged': old_reviews, 'current0d2_entire_review_tree_equals_d369': True,
        'canonical_priority_queue_not_in_write_set': True, 'canonical_priority_queue_sha256': sha(queue_raw),
        'canonical_queue_fields': 6361, 'canonical_queue_ids': 3379, 'canonical_queue_by_language': dict(queue_langs),
        'canonical_queue_current_tree_proof': queue_proof,
        'new_active_ledgers': [{'path': f['path'], 'sha256': f['sha256']} for f in primary_entries],
        'review_cohort_occurrences': 80, 'review_counts': expected, 'integration_report_sha256': sha(integration_raw),
        'integration_primary_and_independent_package_hashes_checked': True,
        'actual_acquisition_audit_sha256': sha(acq_raw), 'actual_saved_progress': progress,
        'old80_exactly_retained_and_new86_disjoint': True, 'after_review_fixed0d2_projection': projection,
        'projection_is_saved_export': False, 'all12_declared_packages_hash_checked': provenance,
        'source_or_candidate_mutations': 0, 'current_publication_live_deployment_claimed': False,
        'older3e574_pages_deployment_receipt_included': True, 'github_writes': 0, 'source_http_requests': 0,
        'publication_requirement': 'Root must refresh main and preserve any concurrent source or generated-reader commits with a normal expected-head lease. These path proofs bind exactly0d2; only the status document is an existing-path overwrite.'}
    validation_path = str(PREFIX / 'staging-validation.json')
    assert lookup(validation_path)['status'] == 'new_path'
    add(validation_path, enc(validation), 'Final exact package/path/status gate')
    # A portable full payload manifest is independent of local workspace paths.
    portable_path = str(PREFIX / 'payload-file-manifest.json')
    assert lookup(portable_path)['status'] == 'new_path'
    portable = {'schema': 'hadith-bank-portable-publication-payload-manifest-v1', 'documented_base_commit': base,
        'base_root_tree_sha': root_sha, 'source_review_pin': config['source_review_pin'],
        'manifest_excludes_its_own_recursive_hash': True,
        'files': [{k: v for k, v in staged[path].items() if k not in ('local_path', 'origins')} for path in sorted(staged)]}
    add(portable_path, enc(portable), 'Portable payload hashes without local paths')
    for item in staged.values():
        raw = Path(item['local_path']).read_bytes()
        assert len(raw) == item['bytes'] and sha(raw) == item['sha256'] and git(raw) == item['git_blob_sha1']
    assert {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()} == set(staged)
    assert (HERE / 'staging-inputs.json').read_bytes() == config_raw
    for item in config['packages']:
        raw = (WORK / item['manifest_path']).read_bytes(); assert sha(raw) == item['manifest_sha256']
        for f in json.loads(raw)['files']:
            data = Path(f.get('local_path', f.get('source_path'))).read_bytes()
            assert len(data) == f.get('bytes', f.get('size_bytes')) and sha(data) == f['sha256']
    result = {'schema': 'hadith-bank-frozen-phase19-publication-manifest-v1', 'repository': 'blaghtayt-alt/Hadith-Bank', 'branch': 'main',
        'documented_base_commit': base, 'base_root_tree_sha': root_sha,
        'published_review_baseline_commit': config['published_review_baseline_commit'], 'source_review_pin': config['source_review_pin'],
        'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'input_packages': provenance,
        'expected_overwrites': [{'path': DOC, 'before_bytes': len(before_doc), 'before_sha256': sha(before_doc),
            'before_git_blob_sha1': git(before_doc), 'after_sha256': sha(new_doc), 'after_git_blob_sha1': git(new_doc)}],
        'files': [staged[k] for k in sorted(staged)], 'total_files': len(staged), 'total_bytes': sum(r['bytes'] for r in staged.values()),
        'new_repository_paths_at_documented_base': len(staged) - 1, 'existing_paths_changed': 1,
        'new_active_ledgers': 4, 'existing_active_ledgers_changed': 0, 'canonical_priority_queue_changed': False,
        'local_validation': {'status': 'PASS', 'path': validation_path, 'sha256': staged[validation_path]['sha256'],
            'combined80_native_source_report_sha256': sha(integration_raw), 'actual_saved_state_audit_sha256': sha(acq_raw),
            'portable_payload_file_manifest_path': portable_path, 'portable_payload_file_manifest_sha256': staged[portable_path]['sha256']},
        'fresh_base_required_before_publication': True, 'github_branch_updated': False,
        'new_review_projection_is_saved_export': False, 'current_publication_live_deployment_verified': False}
    data = enc(result); (HERE / 'manifest.json').write_bytes(data)
    (HERE / 'document-update.md').write_bytes(new_doc)
    (HERE / 'document-update-receipt.json').write_bytes(enc(doc_receipt))
    print(json.dumps({'result': 'PASS', 'manifest_sha256': sha(data), 'files': len(staged), 'bytes': result['total_bytes'],
        'new_paths': len(staged) - 1, 'overwrites': 1, 'document_sha256': sha(new_doc), 'document_bytes': len(new_doc),
        'validation_sha256': staged[validation_path]['sha256'], 'portable_payload_manifest_sha256': staged[portable_path]['sha256']}, indent=2))


if __name__ == '__main__':
    main()
