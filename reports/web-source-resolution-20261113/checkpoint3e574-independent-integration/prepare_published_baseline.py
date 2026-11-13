"""Bind the phase19 source packet to the independently read-back d369 baseline."""
from pathlib import Path
import collections
import datetime
import json
from prepare_source_and_published_baseline import (
    ROOT, WORK, COMMIT, REVIEWS, QUEUE, COHORT_SHA, sha, git, enc, read, lines,
    safe, bind, identity, immutable, SourceReviews)

PUBLISHED = 'd369026ca42af6ff972ffab83c9180e03759da41'
TREE = '84b3a3b3ee1fbab4a2dbb6efbf68a69e94cc2d70'
READBACK = WORK / 'phase18-independent-readback'
READBACK_MANIFEST_SHA = '798d2120046a2ee07d10694e3c1a8f68b467e6564a30bddf5f83a2b18b7a8bff'


def main():
    target = ROOT / 'prepared-source-and-published-baseline.json'
    assert not target.exists(), 'This prepared binding is immutable.'
    prep_path = ROOT / 'prepared-source-cohort.json'
    assert bind(prep_path)['sha256'] == 'd6873df1443a5fd53907f1e404e1a0499de19a6e67e2d836331c7abcab7407bb'
    prep = read(prep_path)
    assert prep['result'] == 'SOURCE_PROVENANCE_PASS' and prep['source_commit'] == COMMIT
    cohort = ROOT / 'input/source-cohort-80.jsonl'
    assert bind(cohort)['sha256'] == COHORT_SHA
    sources = {identity(r): r for r in lines(cohort)}
    assert len(sources) == 80
    delivery_path = READBACK / 'delivery-manifest.json'
    assert bind(delivery_path)['sha256'] == READBACK_MANIFEST_SHA
    delivery = read(delivery_path)
    for item in delivery['files']:
        p = Path(item['local_path']); b = bind(p)
        assert all(b[k] == item[k] for k in b)
    receipt_path = READBACK / 'readback-receipt.json'
    assert bind(receipt_path)['sha256'] == '303d4d41d4db49525e314cbfc9feecc81dd7d892b7f9a6cc2978cae3d61745c7'
    receipt = read(receipt_path)
    assert receipt['status'] == 'PASS' and receipt['published_commit'] == PUBLISHED
    assert receipt['actual_root_tree'] == TREE and receipt['resulting_active_ledgers'] == 37

    def api(name):
        return json.loads(read(READBACK / 'input' / (name + '.json'))['content'])

    commit = api('published-commit')
    assert commit['sha'] == PUBLISHED and commit['tree']['sha'] == TREE
    assert [p['sha'] for p in commit['parents']] == ['a3f9427d7bd235d27318a9470910c182b806a26c']
    names = {'': 'published-root-tree', 'imports': 'after-tree-imports',
             'imports/web-deenhindi-20261112': 'after-tree-imports-web-deenhindi',
             REVIEWS.as_posix(): 'after-tree-reviews', 'reports': 'after-tree-reports',
             'reports/web-source-resolution-20261113': 'after-tree-reports-web-source'}
    trees = {}; tree_receipts = []
    for path, name in names.items():
        tree = api(name)
        assert tree['truncated'] is False
        rows = tree['tree']
        assert len(rows) == len({r['path'] for r in rows})
        assert all('/' not in r['path'] and '\0' not in r['path'] for r in rows)
        ordered = sorted(rows, key=lambda r: (r['path'] + ('/' if r['type'] == 'tree' else '')).encode())
        raw = b''.join((r['mode'].lstrip('0') + ' ' + r['path']).encode() + b'\0' + bytes.fromhex(r['sha']) for r in ordered)
        assert git('tree', raw) == tree['sha']
        trees[path] = tree
        if path:
            parent, _, leaf = path.rpartition('/')
            assert next(r for r in trees[parent]['tree'] if r['path'] == leaf)['sha'] == tree['sha']
        else:
            assert tree['sha'] == TREE
        p = READBACK / 'input' / (name + '.json')
        immutable(ROOT / 'input/published-tree-authority' / p.name, p.read_bytes())
        tree_receipts.append({'path': path or '/', 'git_tree_sha1': tree['sha'],
                              'complete_entries': len(rows), 'response': bind(p), 'complete_git_object_rehashed': True})
    immutable(ROOT / 'input/published-tree-authority/published-commit.json', (READBACK / 'input/published-commit.json').read_bytes())
    review_entries = {r['path']: r for r in trees[REVIEWS.as_posix()]['tree']
                      if r['type'] == 'blob' and r['path'].startswith('source-review')}
    assert len(review_entries) == 37
    prior_repo = WORK / 'phase18-checkpointbd4a-independent-integration/validation/combined-reviews'
    published_root = ROOT / 'validation/published-reviews'
    bindings = []; dependencies = {}; ids = set()
    for name, entry in sorted(review_entries.items()):
        downloaded = READBACK / 'downloaded' / REVIEWS / name
        p = downloaded if downloaded.exists() else prior_repo / REVIEWS / name
        b = bind(p)
        assert b['git_blob_sha1'] == entry['sha'] and b['bytes'] == entry['size']
        ledger = read(p); decisions = ledger.get('records', ledger.get('decisions'))
        group = {identity(r) for r in decisions}
        assert len(group) == len(decisions) and not group & ids and not group & set(sources)
        ids |= group
        relative = (REVIEWS / name).as_posix()
        immutable(published_root / relative, p.read_bytes())
        bindings.append({'path': relative, 'original_local_path': str(p), **b, 'records': len(group),
                         'ids': sorted(group), 'exact_d369_git_blob_verified': True})
        if 'source_ledger_path' in ledger:
            dep = str(safe(ledger['source_ledger_path']))
            source_dep = prior_repo / dep
            assert source_dep.is_file() and bind(source_dep)['sha256'] == ledger['source_ledger_sha256']
            if dep in dependencies:
                assert dependencies[dep]['sha256'] == ledger['source_ledger_sha256']
            dependencies[dep] = {'path': dep, 'original_local_path': str(source_dep), **bind(source_dep)}
            immutable(published_root / dep, source_dep.read_bytes())
    assert len(ids) == 3410
    native = SourceReviews(published_root, 'deenhindi')
    assert set(native.decisions) == ids
    current477 = next(r for r in bindings if r['records'] == 477)
    assert current477['sha256'] == '18970b44b24868634c9e9d5f7db729c9f76c054502627c350a10f139c66e1d9c'
    queue_path = WORK / 'phase17-independent-readback/downloaded' / QUEUE
    qb = bind(queue_path)
    assert qb['sha256'] == '74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a'
    qe = next(r for r in trees['reports/web-source-resolution-20261113']['tree'] if r['path'] == Path(QUEUE).name)
    assert qe['sha'] == qb['git_blob_sha1'] and qe['size'] == qb['bytes']
    queue_rows = lines(queue_path)
    counts = collections.Counter(f['language'] for r in queue_rows for f in r['fields'])
    assert len(queue_rows) == 3379 and counts == {'hi': 3285, 'ur': 3076}
    immutable(published_root / QUEUE, queue_path.read_bytes())
    old92_path = WORK / 'phase18-checkpointbd4a-independent-integration/input/source-cohort-92.jsonl'
    old92 = {identity(r) for r in lines(old92_path)}
    assert len(old92) == 92 and old92 <= ids and not old92 & set(sources)
    old92_counts = collections.Counter(native.decisions[k][2] for k in old92)
    assert old92_counts == {'register': 87, 'exclude': 5}
    result = {**prep, 'schema': 'hadith-bank-checkpoint3e574-integration-preparation-v1', 'result': 'PASS',
        'source_preparation_receipt': bind(prep_path),
        'publication_binding_generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'published_review_baseline_commit': PUBLISHED, 'published_root_tree': TREE,
        'published_review_baseline_checked_here': True,
        'independent_readback_delivery': bind(delivery_path), 'independent_readback_receipt': bind(receipt_path),
        'published_review_tree_ancestry': tree_receipts, 'published_active_ledgers': 37,
        'published_manual_decision_ids': 3410, 'published_ledger_bindings': bindings,
        'published_source_ledger_dependencies': list(dependencies.values()),
        'all80_disjoint_from_all3410_prior_manual_ids': True,
        'old92_published_dispositions': dict(old92_counts),
        'updated477_active_sha256': current477['sha256'],
        'canonical_priority_queue': {'path': QUEUE, **qb, 'pending_fields': 6361, 'occurrences': 3379,
                                     'by_language': dict(counts)},
        'current_newer_main_checkpoint_or_history_not_audited_here': True}
    immutable(target, enc(result))
    print(json.dumps({'result': 'PASS', 'preparation': bind(target), 'published_ledgers': 37,
                      'published_ids': 3410, 'new_source_ids': 80, 'queue_fields': 6361}))


if __name__ == '__main__':
    main()
