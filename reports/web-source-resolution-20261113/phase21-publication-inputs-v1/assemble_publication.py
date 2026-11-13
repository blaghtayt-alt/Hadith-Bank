"""Freeze phase21 against b7f21, binding the exact17cd acquisition audit and all prior document bytes."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import collections
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
OUT = HERE / 'publish'
PREFIX = Path('reports/web-source-resolution-20261113/phase21-publication-inputs-v1')
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
    assert base == 'b7f21cbdd84fc922575b946e92b246e2665478ab'
    assert root_sha == '0d477db71751c7be91d761aae27f93b1fbcd9aeb'
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
    assert len(packages) == 13

    def payload(name, suffix):
        matches = [f for f in packages[name]['files'] if f['path'].endswith(suffix)]
        assert len(matches) == 1, (name, suffix)
        return matches[0], Path(matches[0]['local_path']).read_bytes()

    _, integration_raw = payload('combined86-integration', 'validation-report.json')
    assert sha(integration_raw) == config['integration_report_sha256']
    integration = json.loads(integration_raw)
    expected = {'register': 84, 'exclude': 2, 'read_fields': 190, 'admitted': 173, 'read_context': 17,
                'unread_context': 240, 'empty': 0, 'source_slots': 430, 'partitions': 430,
                'read_characters': 84550, 'read_utf8_bytes': 178462}
    assert integration['result'] == 'PASS' and integration['native_new86_apply_finish'] == 'PASS'
    assert all(integration['counts'][k] == v for k, v in expected.items() if k != 'empty')
    assert integration['counts'].get('empty', 0) == 0
    assert integration['counts']['read_fields'] + integration['counts']['unread_context'] == integration['counts']['source_slots']
    assert integration['source_commit'] == config['source_review_pin'] == '0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a'
    assert integration['published_review_baseline_commit'] == config['published_review_baseline_commit'] == base
    assert (integration['source_count'], integration['source_files_verified'], integration['full_raw_reparses_bound']) == (86, 172, 86)
    assert (integration['native_combined_loader_ledgers'], integration['native_combined_loader_ids']) == (45, 3576)
    assert (integration['prior41_published_manual_ledgers'], integration['prior_published_manual_ids']) == (41, 3490)
    assert integration['all41_prior_blobs_dependencies_and3490_decisions_unchanged'] and not integration['id_collisions']
    primary_entries = []; ids = set(); decisions = {}; source_counts = collections.Counter()
    field_counts = collections.Counter(); read_field_ids = []
    for name in ('primary-bukhari30', 'primary-muslim22', 'primary-nasai6_ibnmajah10', 'primary-abudawud12_tirmidhi6'):
        active = [f for f in packages[name]['files'] if Path(f['path']).parent == REV and Path(f['path']).name.startswith('source-review-')]
        assert len(active) == 1
        entry = active[0]; primary_entries.append(entry)
        ledger = json.loads(gzip.decompress((OUT / entry['path']).read_bytes()))
        baseline = OUT / safe(ledger['source_ledger_path'])
        assert sha(baseline.read_bytes()) == ledger['source_ledger_sha256']
        saved = [json.loads(line) for line in gzip.decompress(baseline.read_bytes()).splitlines()]
        saved_ids = {'deenhindi-' + r['collection'] + ':' + r['number']: r for r in saved}
        records = ledger.get('records', ledger.get('decisions'))
        assert len(saved_ids) == len(records) == {'primary-bukhari30':30, 'primary-muslim22':22, 'primary-nasai6_ibnmajah10':16, 'primary-abudawud12_tirmidhi6':18}[name]
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
    assert len(ids) == 86 and source_counts == {'register': 84, 'exclude': 2}
    assert all(field_counts[k] == expected[k] for k in field_counts)
    assert len(read_field_ids) == len(set(read_field_ids)) == 190
    _, acq_raw = payload('acquisition-17cd-state-history', 'saved-state-audit.json')
    assert sha(acq_raw) == config['acquisition_report_sha256']
    acq = json.loads(acq_raw)
    assert acq['status'] == 'PASS' and acq['saved_commit'] == '17cd396eb858a29162505d545aad556ac73ce9ce' and acq['saved_tree'] == '7a3df5ed9cd7e3d1380bb2dc6f61b1c5a5424770'
    assert acq['saved_parent'] == '70c1a0799bcf67a18bf28bdb9a6672fe1edbc552'
    progress = acq['saved_progress']
    actual = {k: progress[k] for k in ('imported_count', 'registered_hadith_count', 'non_narration_source_entries', 'classification_pending_count', 'pending_fetch_count', 'errors_count')}
    assert actual == {'imported_count': 18089, 'registered_hadith_count': 17753, 'non_narration_source_entries': 165,
                      'classification_pending_count': 171, 'pending_fetch_count': 18301, 'errors_count': 0}
    part = acq['held_partition']; keys = {oid.removeprefix('deenhindi-') for oid in ids}
    assert set(part['retained_prior86_keys']) == keys
    assert len(part['new85_keys']) == 85 and not set(part['new85_keys']) & keys
    assert set(part['current171_held_keys']) == keys | set(part['new85_keys'])
    assert len(part['prior80_registered_keys']) == 75 and len(part['prior80_source_only_keys']) == 5
    preserve = acq['source_state_preservation']
    assert preserve['all17627_prior_imported_descriptors_exact'] and preserve['all1000_error_histories_exact'] and preserve['all1000_consumed_attempts_exact']
    assert preserve['new_imported_ids'] == 462 and preserve['new_retry_attempts'] == 0
    assert acq['source_controls']['source_stop_guards_and_cadence_unchanged']
    assert acq['bounded_artifact_audit']['source_files_verified'] == 342 and acq['bounded_artifact_audit']['raw_and_parsed_pairs_reopened_and_reparsed'] == 171
    projection = {'fetched': 18089, 'registered': 17753 + source_counts['register'],
                  'source_only': 165 + source_counts['exclude'], 'held': 171 - len(ids), 'unfetched': 18301}
    assert projection == {'fetched': 18089, 'registered': 17837, 'source_only': 167, 'held': 85, 'unfetched': 18301}
    prior_receipts = {}
    for item in config['phase20_publication_receipts']:
        data = (WORK / 'phase20-final-publication' / item['name']).read_bytes()
        assert sha(data) == item['sha256'] and len(data) == item['bytes']
        prior_receipts[item['name']] = json.loads(data)
        add(PREFIX / 'receipts' / ('phase20-' + item['name']), data, 'Exact phase20 publication receipt')
    pub = prior_receipts['publication-receipt.json']
    assert pub['commit'] == base and pub['tree_sha'] == root_sha
    assert pub['parent_commit'] == acq['saved_commit']
    assert pub['manifest_sha256'] == sha((WORK / 'phase20-final-publication/manifest.json').read_bytes())
    assert pub['force'] is False

    # Every reused tree is accepted only after reconstructing its Git identity
    # and linking it from the exact independently read-back b7f21 root used below.
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
            add_tree(tree['tree'], tree['sha'], 'phase20 verified before tree ' + directory)
        elif tree is not None:
            assert tree.get('sha') is None and tree['tree'] == []
    for item in prior_receipts['tree-verification-receipts.json']:
        tree = item['complete_tree']; assert not tree.get('truncated', False)
        assert tree['sha'] == item['after_tree_sha']
        add_tree(tree['tree'], tree['sha'], 'phase20 published complete tree ' + item['directory'])
    readback = WORK / 'phase20-independent-readback'
    for path in sorted((readback / 'input').glob('*tree*.json')):
        response = json.loads(path.read_bytes())
        if 'content' not in response:
            continue
        tree = json.loads(response['content'])
        assert not tree.get('truncated', False)
        add_tree(tree['tree'], tree['sha'], 'Independent phase20 GitHub response ' + path.name)
    _, current_tree_raw = payload('acquisition-17cd-state-history', 'complete-path-trees.json.gz')
    current_trees = json.loads(gzip.decompress(current_tree_raw))
    assert current_trees['']['sha'] == acq['saved_tree'] and len(current_trees) == 7
    for directory, tree in current_trees.items():
        assert not tree.get('truncated', False)
        add_tree(tree['tree'], tree['sha'], 'Audited17cd complete tree ' + directory)
    for path in sorted((HERE / 'input').glob('b7f21-*.json')):
        tree = json.loads(path.read_bytes())
        assert not tree.get('truncated', False)
        add_tree(tree['tree'], tree['sha'], 'Additional complete GitHub ancestor ' + path.name)

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

    source_root = pool[acq['saved_tree']]
    a = {r['path']: r for r in source_root}; b = {r['path']: r for r in pool[root_sha]}
    assert set(a) == set(b) and {k for k in a if a[k] != b[k]} == {'docs', 'imports', 'reports'}
    independent_readback = json.loads((readback / 'readback-receipt.json').read_bytes())
    assert independent_readback['published_commit'] == base and independent_readback['actual_parent_commit'] == acq['saved_commit']
    assert independent_readback['status'] == 'PASS' and len(independent_readback['all12_current_acquisition_entries_preserved_from17cd']) == 12
    assert all(row['before_after_full_entry_equal'] for row in independent_readback['all12_current_acquisition_entries_preserved_from17cd'])
    queue_raw = (WORK / 'phase20-independent-readback/downloaded' / QUEUE).read_bytes()
    assert sha(queue_raw) == '8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349'
    queue_proof = lookup(QUEUE); assert queue_proof['git_object_sha1'] == git(queue_raw)
    queue_rows = [json.loads(line) for line in gzip.decompress(queue_raw).splitlines()]
    queue_langs = collections.Counter(f['language'] for row in queue_rows for f in row['fields'])
    assert len(queue_rows) == 3354 and queue_langs == {'hi': 3260, 'ur': 3051}
    review_proof = lookup(REV.as_posix()); assert review_proof['type'] == 'tree'
    assert review_proof['git_object_sha1'] == 'f2b6ec9782e600c10d135f2ae8e98c884bed91ed'
    old_reviews = [r for r in pool[review_proof['git_object_sha1']] if r['type'] == 'blob' and r['path'].startswith('source-review-')]
    assert len(old_reviews) == 41 and QUEUE not in staged
    assert not any((REV / r['path']).as_posix() in staged for r in old_reviews)
    baseline = WORK / 'phase21-checkpoint0d2fa-independent-integration/validation/published-reviews'
    for r in old_reviews:
        assert git((baseline / REV / r['path']).read_bytes()) == r['sha']
    before_doc = (readback / 'downloaded' / DOC).read_bytes()
    assert len(before_doc) == 111201 and sha(before_doc) == 'c7b72496c4fb06d201935b077903270f14014bc3d36370cbfa1a860ca8fb1982'
    before_doc_proof = lookup(DOC); assert before_doc_proof['git_object_sha1'] == git(before_doc)
    prefix = (HERE / config['status_prefix_path']).read_bytes()
    assert sha(prefix) == config['root_approved_status_prefix_sha256']
    assert b'Draft checkpoint note' not in prefix and b'once frozen' not in prefix
    new_doc = prefix + before_doc
    assert new_doc[len(prefix):] == before_doc and new_doc.endswith(before_doc)
    add(DOC, new_doc, 'Approved English status prefix followed by every prior document byte')
    add(PREFIX / 'previous-status-document.md', before_doc, 'Exact complete111201-byte b7f21 status document')
    add(PREFIX / 'current-status-prefix.md', prefix, 'Root-read and approved current English status prefix')
    doc_receipt = {'schema': 'hadith-bank-versioned-status-document-update-v1', 'documented_base_commit': base, 'path': DOC,
        'previous_review_publication': config['published_review_baseline_commit'],
        'before_bytes': len(before_doc), 'before_sha256': sha(before_doc), 'before_git_blob_sha1': git(before_doc),
        'prefix_bytes': len(prefix), 'prefix_sha256': sha(prefix), 'root_completed_prefix_read_and_approval': True,
        'after_bytes': len(new_doc), 'after_sha256': sha(new_doc), 'after_git_blob_sha1': git(new_doc),
        'full_previous_document_archived_path': str(PREFIX / 'previous-status-document.md'),
        'complete_old_document_exact_suffix_including_original_title': True,
        'current_saved_export_source_commit': acq['saved_commit'], 'review_projection_is_a_new_saved_export': False,
        'current_publication_live_deployment_claimed': False}
    add(PREFIX / 'document-update-receipt.json', enc(doc_receipt), 'Exact prior document byte-preservation proof')
    add(PREFIX / 'staging-inputs.json', config_raw, 'Exact13 frozen package and7 publication receipt declarations')
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
        'scope': 'Complete reused Git tree identities are reconstructed and linked from the exact independently read-back b7f21 root. Other branches are preserved by the fresh-head lease at actual publication.',
        'trees': [{'git_tree_sha1': h, 'entries': pool[h], 'origins': origins[h]} for h in sorted(used)]}
    add(tree_path, gzip.compress(enc(tree_proof), mtime=0), 'Complete actual ancestor trees used by path proofs')
    validation = {'schema': 'hadith-bank-phase21-publication-staging-validation-v1', 'result': 'PASS',
        'documented_base_commit': base, 'base_root_tree_sha': root_sha,
        'published_review_baseline_commit': config['published_review_baseline_commit'], 'only_existing_path_update': DOC,
        'path_proofs': proofs, 'complete_ancestor_tree_proof_path': tree_path,
        'old41_active_review_entries_unchanged': old_reviews, 'b7f21_review_tree_matches_independent_readback': True,
        'canonical_priority_queue_not_in_write_set': True, 'canonical_priority_queue_sha256': sha(queue_raw),
        'canonical_queue_fields': 6311, 'canonical_queue_ids': 3354, 'canonical_queue_by_language': dict(queue_langs),
        'canonical_queue_current_tree_proof': queue_proof,
        'new_active_ledgers': [{'path': f['path'], 'sha256': f['sha256']} for f in primary_entries],
        'review_cohort_occurrences': 86, 'review_counts': expected, 'integration_report_sha256': sha(integration_raw),
        'integration_primary_and_independent_package_hashes_checked': True,
        'actual_acquisition_audit_sha256': sha(acq_raw), 'actual_saved_progress': progress,
        'old86_exactly_retained_and_new85_disjoint': True, 'after_review_fixed17cd_projection': projection,
        'projection_is_saved_export': False, 'all13_declared_packages_hash_checked': provenance,
        'source_or_candidate_mutations': 0, 'current_publication_live_deployment_claimed': False,
        'latest_verified_live_source_remains_3e574': True, 'github_writes': 0, 'source_http_requests': 0,
        'publication_requirement': 'Root must refresh main and preserve any concurrent source or generated-reader commits with a normal expected-head lease. These path proofs bind exactlyb7f21; only the status document is an existing-path overwrite.'}
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
    result = {'schema': 'hadith-bank-frozen-phase21-publication-manifest-v1', 'repository': 'blaghtayt-alt/Hadith-Bank', 'branch': 'main',
        'documented_base_commit': base, 'base_root_tree_sha': root_sha,
        'published_review_baseline_commit': config['published_review_baseline_commit'], 'source_review_pin': config['source_review_pin'],
        'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'input_packages': provenance,
        'expected_overwrites': [{'path': DOC,
            'before': {'bytes': len(before_doc), 'sha256': sha(before_doc), 'git_blob_sha1': git(before_doc)},
            'after': {'bytes': len(new_doc), 'sha256': sha(new_doc), 'git_blob_sha1': git(new_doc)}}],
        'files': [staged[k] for k in sorted(staged)], 'total_files': len(staged), 'total_bytes': sum(r['bytes'] for r in staged.values()),
        'new_repository_paths_at_documented_base': len(staged) - 1, 'existing_paths_changed': 1,
        'new_active_ledgers': 4, 'existing_active_ledgers_changed': 0, 'canonical_priority_queue_changed': False,
        'local_validation': {'status': 'PASS', 'path': validation_path, 'sha256': staged[validation_path]['sha256'],
            'combined86_native_source_report_sha256': sha(integration_raw), 'actual_saved_state_audit_sha256': sha(acq_raw),
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
