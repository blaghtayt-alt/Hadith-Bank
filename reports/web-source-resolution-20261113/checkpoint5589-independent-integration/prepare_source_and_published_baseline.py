"""Bind the exact new100 sources and current published review IDs offline.

No linguistic classification occurs here. The complete prior0639 state is read;
the later5589 authority is deliberately limited to its saved bounded artifact
and progress. The unavailable complete5589 state/history is not certified.
"""
from pathlib import Path, PurePosixPath
import collections, datetime, gzip, hashlib, json, sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews, unique_pairs

COMMIT = '5589a3ffc3b43c3324ae26f2b6c4d33152834456'
PUBLISHED = 'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d'
MONITOR = WORK / 'phase15-successor-acquisition-monitor'
EVIDENCE = MONITOR / 'held-evidence'
PARTITIONS = WORK / 'phase16-checkpoint5589-input-partitions'
READBACK = WORK / 'phase15-independent-readback'
REVIEWS = Path('imports/web-deenhindi-20261112/reviews')
COHORT_SHA = '4a4000d46dba9cff36695a62e7e5207af8f5183644141e8ca23b047e62434490'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def git(kind, value):
    return hashlib.sha1(kind.encode() + b' ' + str(len(value)).encode() + b'\0' + value).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if Path(path).suffix == '.gz' else raw, object_pairs_hook=unique_pairs)


def lines(path):
    raw = Path(path).read_bytes()
    if Path(path).suffix == '.gz':
        raw = gzip.decompress(raw)
    return [json.loads(line, object_pairs_hook=unique_pairs) for line in raw.splitlines() if line.strip()]


def safe(relative):
    p = PurePosixPath(relative)
    assert relative and not p.is_absolute() and '..' not in p.parts and '\\' not in relative
    return p


def bind(path):
    raw = Path(path).read_bytes()
    return {'bytes': len(raw), 'sha256': sha(raw), 'git_blob_sha1': git('blob', raw)}


def identity(row):
    return row.get('occurrence_id', row.get('id')) or 'deenhindi-' + row['collection'] + ':' + str(row['number'])


def immutable(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, ('different pre-existing isolated output', str(path))
    else:
        path.write_bytes(raw)


def main():
    report_path = ROOT / 'prepared-source-and-published-baseline.json'
    assert not report_path.exists(), 'Preparation receipt is frozen; do not rewrite it.'
    source_path = MONITOR / 'next-review-cohort/held-source-records.jsonl'
    assert bind(source_path)['sha256'] == COHORT_SHA
    rows = lines(source_path); sources = {identity(row): row for row in rows}
    keys = {key.removeprefix('deenhindi-') for key in sources}
    assert len(rows) == len(sources) == len(keys) == 100
    assert collections.Counter(row['collection'] for row in rows) == {
        'bukhari': 20, 'muslim': 18, 'nasai': 22, 'abudawud': 8, 'tirmidhi': 17, 'ibnmajah': 15}
    cohort_manifest_path = MONITOR / 'next-review-cohort/evidence-manifest.json'
    assert bind(cohort_manifest_path)['sha256'] == 'b68c07912aecf94eeca7461b8671b1cd91aeb24468172bca0dd11a8119acf027'
    cohort_manifest = read(cohort_manifest_path)
    assert cohort_manifest['source_commit'] == COMMIT and set(cohort_manifest['keys']) == keys
    assert cohort_manifest['source_rows_sha256'] == COHORT_SHA

    # Every frozen partition line is an exact row of the original new100 packet.
    partition_manifest = read(PARTITIONS / 'delivery-manifest.json')
    assert bind(PARTITIONS / 'delivery-manifest.json')['sha256'] == '6dd654b3e8900cb19b3bd50ed76558dedb5fc7840459e495c3c05672ec7d629c'
    for item in partition_manifest['files']:
        actual = bind(Path(item['local_path']))
        assert actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes']
    partition_ids, partition_bindings = set(), []
    for name in ['checkpoint-bukhari20-ibnmajah5', 'queue-muslim18-ibnmajah7',
                 'deployment-abudawud8-tirmidhi17', 'root-nasai22-ibnmajah3']:
        path = PARTITIONS / name / 'cohort.jsonl'
        group = lines(path); group_ids = {identity(row) for row in group}
        assert len(group) == len(group_ids) == 25 and not group_ids & partition_ids
        assert all(row == sources[identity(row)] for row in group)
        partition_ids |= group_ids
        partition_bindings.append({'name': name, 'cohort': bind(path), 'ids': sorted(group_ids)})
    assert partition_ids == set(sources)

    prior_path = WORK / 'phase13-successor-acquisition-monitor/saved-checkpoint/state.json'
    assert bind(prior_path)['sha256'] == '5ce4a7ef9633cda58831c116d46f6a494703c6fa3931783d368fbd7fec62c4e1'
    prior = read(prior_path)
    assert len(prior['imported']) == 15672 and not keys & set(prior['imported'])
    old117_path = WORK / 'phase13-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl'
    assert bind(old117_path)['sha256'] == 'a253b86c17219976a4db42e0b203a14affa8f01b62f7e58fbe3ec145aeb3efb8'
    old117 = {identity(row): row for row in lines(old117_path)}
    assert len(old117) == 117 and not set(old117) & set(sources)

    artifact_path = EVIDENCE / 'evidence-manifest.json'
    assert bind(artifact_path)['sha256'] == '90817d73a72aad32e9faa5f46063cf54946c607fea7aafbd025b6b67208d14ab'
    artifact = read(artifact_path)
    assert artifact['saved_head'] == COMMIT
    for name in ['checkpoint.json', 'held-source-records.jsonl', 'held-state-entries.json']:
        expected = artifact['artifact_files'][name]
        actual = bind(EVIDENCE / name)
        assert actual['sha256'] == expected['sha256'] and actual['bytes'] == expected['bytes']
    checkpoint = read(EVIDENCE / 'checkpoint.json')
    entries = read(EVIDENCE / 'held-state-entries.json')
    all_held = {identity(row): row for row in lines(EVIDENCE / 'held-source-records.jsonl')}
    assert len(all_held) == len(entries) == checkpoint['selected_held_entries'] == checkpoint['held_entries_total'] == 217
    assert checkpoint['saved_head'] == COMMIT and checkpoint['remaining_held_queue_count'] == 0
    assert set(all_held) == set(sources) | set(old117)
    assert set(artifact['held_keys']) == set(entries) == {key.removeprefix('deenhindi-') for key in all_held}
    assert all(all_held[key] == row for key, row in sources.items())
    assert all(all_held[key] == row for key, row in old117.items())
    assert all(entries[key.removeprefix('deenhindi-')] == prior['imported'][key.removeprefix('deenhindi-')] for key in old117)

    # The new100 authority consists of these exact bounded descriptors and files.
    source_files = []
    for oid, row in sources.items():
        key = oid.removeprefix('deenhindi-'); entry = entries[key]
        assert entry['collection'] == row['collection'] and entry['number'] == row['number']
        assert entry['parsed']['path'] == row['parsed_path']
        assert sha(importer.json_bytes(row['source_record'])) == artifact['source_record_sha256'][key]
        for kind, descriptor in [('raw', row['snapshot']), ('parsed', entry['parsed'])]:
            relative = str(safe(descriptor['path'])); path = EVIDENCE / 'sources' / relative
            assert path.is_file() and not path.is_symlink()
            stored = path.read_bytes(); plain = gzip.decompress(stored); receipt = bind(path)
            declared = artifact['files'][relative]
            assert receipt['bytes'] == declared['bytes'] == declared['stored_bytes']
            assert receipt['sha256'] == descriptor['stored_sha256'] == declared['sha256'] == declared['stored_sha256']
            assert receipt['git_blob_sha1'] == declared['git_blob_sha1']
            assert sha(plain) == descriptor['sha256']
            if 'bytes' in descriptor: assert len(plain) == descriptor['bytes']
            if kind == 'raw':
                parsed, reference = importer.parse_record(plain, row['collection'], row['number'])
                assert parsed == row['source_record'] and reference == row['source_reference_verbatim']
            else:
                expected = {k: row[k] for k in ['schema', 'collection', 'number', 'source_record', 'source_reference_verbatim', 'snapshot']}
                expected['classification'] = row['intake_classification']
                assert json.loads(plain, object_pairs_hook=unique_pairs) == expected
            source_files.append({'id': oid, 'kind': kind, 'path': relative, **receipt,
                                 'plain_bytes': len(plain), 'plain_sha256': sha(plain)})
    assert len(source_files) == 200 and len({x['path'] for x in source_files}) == 200

    progress_path = MONITOR / 'saved-checkpoint/progress.json'
    progress_receipt = checkpoint['input_receipts']['imports/web-deenhindi-20261112/progress.json']
    assert all(bind(progress_path)[key] == progress_receipt[key] for key in ('bytes', 'sha256', 'git_blob_sha1'))
    progress = read(progress_path)
    assert progress['imported_count'] == 16169 and progress['classification_pending_count'] == 217
    assert progress['registered_hadith_count'] == 15806 and progress['non_narration_source_entries'] == 146

    # Rehash the complete already-retrieved Git tree ancestry for current reviews.
    commit_path = READBACK / 'input/github-commit.json'
    commit = json.loads(read(commit_path)['content'])
    assert commit['sha'] == PUBLISHED and commit['tree']['sha'] == 'bb937a8efb1fd95128f02b63028f4d25838d9355'
    assert [p['sha'] for p in commit['parents']] == [COMMIT]
    root_path = READBACK / 'input/github-root_tree.json'
    root_tree = json.loads(read(root_path)['content']); root_tree['path'] = ''
    tree_sources = [(root_path, root_tree)]
    for tree_sha in ['2e1043e2e383321975442c96dc297ce56261980b', '6e75d5c1db245279600fcff086be7a5ac164b881',
                     '582d11796013cdaccf24862be0a1f49b5140a2d3']:
        path = READBACK / ('input/tree-' + tree_sha + '.json')
        tree_sources.append((path, read(path)))
    trees = {tree['path']: tree for _, tree in tree_sources}
    tree_receipts = []
    for path, tree in tree_sources:
        assert tree['truncated'] is False
        listed = tree['tree']; assert len(listed) == len({e['path'] for e in listed})
        assert all('/' not in e['path'] and '\0' not in e['path'] for e in listed)
        ordered = sorted(listed, key=lambda e: (e['path'] + ('/' if e['type'] == 'tree' else '')).encode())
        raw = b''.join((e['mode'].lstrip('0') + ' ' + e['path']).encode() + b'\0' + bytes.fromhex(e['sha']) for e in ordered)
        assert git('tree', raw) == tree['sha']
        if tree['path']:
            parent, _, name = tree['path'].rpartition('/')
            assert next(e for e in trees[parent]['tree'] if e['path'] == name)['sha'] == tree['sha']
        else: assert tree['sha'] == commit['tree']['sha']
        tree_receipts.append({'path': tree['path'] or '/', 'git_tree_sha1': tree['sha'],
                              'complete_entries': len(listed), 'retrieved_json': bind(path),
                              'complete_tree_rehashed': True})
        immutable(ROOT / 'input/published-tree-authority' / path.name, path.read_bytes())
    immutable(ROOT / 'input/published-tree-authority/github-commit.json', commit_path.read_bytes())

    directories = [WORK / directory for directory in [
        'phase2-integration/repo', 'phase3-recovered-review/publish', 'phase5-language-publication/publish',
        'phase6-final-publication/publish', 'phase8-next93-publication/publish', 'phase10-final-publication/publish',
        'phase11-original-ibnmajah-remaining-urdu/publish-v2', 'phase13-final-publication/publish',
        'phase15-final-publication/publish']]
    overlays = {}
    for directory in directories:
        for path in (directory / REVIEWS).glob('source-review*.json*'):
            overlays[path.name] = path
    overlays['source-review-20261113-bukhari-first300.json.gz'] = WORK / 'reuse-evidence-fix/existing-deen300-review.json.gz'
    review_tree = trees[REVIEWS.as_posix()]
    active_entries = {entry['path']: entry for entry in review_tree['tree']
                      if entry['type'] == 'blob' and entry['path'].startswith('source-review')
                      and (entry['path'].endswith('.json') or entry['path'].endswith('.json.gz'))}
    assert set(overlays) == set(active_entries) and len(overlays) == 29
    existing_ids, bindings, dependencies = set(), [], {}
    published_root = ROOT / 'validation/published-reviews'
    for name, path in sorted(overlays.items()):
        receipt = bind(path); entry = active_entries[name]
        assert receipt['git_blob_sha1'] == entry['sha'] and receipt['bytes'] == entry['size']
        ledger = read(path); decisions = ledger.get('records', ledger.get('decisions'))
        ids = {identity(row) for row in decisions}
        assert len(ids) == len(decisions) and not ids & existing_ids and not ids & set(sources)
        existing_ids |= ids
        relative = (REVIEWS / name).as_posix()
        immutable(published_root / relative, path.read_bytes())
        bindings.append({'path': relative, 'original_local_path': str(path), **receipt, 'records': len(ids),
                         'ids': sorted(ids), 'exact_published_git_blob_verified': True})
        if 'source_ledger_path' in ledger:
            dep = str(safe(ledger['source_ledger_path'])); expected_sha = ledger['source_ledger_sha256']
            candidates = [directory / dep for directory in reversed(directories)]
            found = next((candidate for candidate in candidates if candidate.is_file() and bind(candidate)['sha256'] == expected_sha), None)
            assert found is not None, ('missing current declared source-ledger dependency', dep, expected_sha)
            if dep in dependencies: assert dependencies[dep]['sha256'] == expected_sha
            dependencies[dep] = {'path': dep, 'original_local_path': str(found), **bind(found)}
            immutable(published_root / dep, found.read_bytes())
    assert len(existing_ids) == 3218 and set(old117) <= existing_ids and not existing_ids & set(sources)
    existing_engine = SourceReviews(published_root, 'deenhindi')
    assert set(existing_engine.decisions) == existing_ids

    proof = {'schema': 'hadith-bank-checkpoint5589-integration-preparation-v1', 'result': 'PASS',
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_commit': COMMIT, 'published_review_baseline_commit': PUBLISHED,
        'source_cohort': bind(source_path), 'source_cohort_count': 100,
        'source_cohort_ids': sorted(sources), 'collection_counts': dict(collections.Counter(row['collection'] for row in rows)),
        'partitions': partition_bindings, 'all_four_partitions_disjoint_and_exact_cover': True,
        'prior0639_full_state': bind(prior_path), 'prior_imported_count': 15672,
        'all100_absent_prior15672': True, 'old117_cohort': bind(old117_path), 'old117_disjoint': True,
        'bounded5589_held_count': 217, 'old117_source_rows_and_imported_descriptors_exact': True,
        'bounded5589_checkpoint': bind(EVIDENCE / 'checkpoint.json'),
        'bounded5589_artifact_manifest': bind(artifact_path), 'bounded5589_descriptors': bind(EVIDENCE / 'held-state-entries.json'),
        'new100_source_files_reopened': 200, 'new100_raw_reparses_exact': 100,
        'saved5589_progress': bind(progress_path),
        'saved5589_progress_counts': {key: progress[key] for key in ['imported_count', 'registered_hadith_count',
            'non_narration_source_entries', 'classification_pending_count', 'pending_fetch_count', 'errors_count', 'blocked', 'done']},
        'complete5589_state_bytes_retrieved_by_this_audit': False,
        'complete5589_prior_imports_and_error_retry_history_comparison': 'NOT_PERFORMED; complete current state unavailable in this bounded audit',
        'published_review_tree_ancestry': tree_receipts,
        'published_active_ledgers': 29, 'published_manual_decision_ids': 3218,
        'all100_absent_published_manual_ids': True, 'published_review_loader_collision_check': 'PASS',
        'published_prior_review_application_finish': 'NOT_PERFORMED; constructor and exact ID checks only, no new interpretation of prior3218',
        'published_ledger_bindings': bindings, 'published_source_ledger_dependencies': list(dependencies.values()),
        'new_semantic_readings': 0, 'new_review_decisions': 0, 'source_http_requests': 0, 'github_writes': 0,
        'parser_sha256': sha(Path(importer.__file__).read_bytes()), 'review_engine_sha256': existing_engine.engine_sha256,
        'limitations': 'Fixed new100 source cohort, complete prior0639 state, bounded5589 held artifact/progress, and the independently retrieved e3f88ac8 published review tree. No complete5589 state/history preservation, latest remote head, export regeneration, or deployment is claimed.'}
    immutable(ROOT / 'input/source-cohort-100.jsonl', source_path.read_bytes())
    immutable(ROOT / 'new100-raw-parsed-source-proof.json.gz', gzip.compress(enc({'records': source_files}), mtime=0))
    immutable(report_path, enc(proof))
    print(json.dumps({'result': 'PASS', 'source_count': 100, 'source_files': 200, 'raw_reparses': 100,
        'published_ledgers': 29, 'published_ids': 3218, 'collisions': 0,
        'preparation_sha256': sha(report_path.read_bytes()),
        'source_proof_sha256': sha((ROOT / 'new100-raw-parsed-source-proof.json.gz').read_bytes())}, indent=2))


if __name__ == '__main__':
    main()
