"""Bind the phase21 source packet to the independently read-back b7f21 baseline."""
from pathlib import Path
import collections
import datetime
import json
from prepare_source_and_published_baseline import (
    ROOT, WORK, COMMIT, REVIEWS, QUEUE, COHORT_SHA, sha, git, enc, read, lines,
    safe, bind, identity, immutable, SourceReviews)

PUBLISHED = 'b7f21cbdd84fc922575b946e92b246e2665478ab'
TREE = '0d477db71751c7be91d761aae27f93b1fbcd9aeb'
READBACK = WORK / 'phase20-independent-readback'
READBACK_MANIFEST_SHA = '263bac210a08c823f42ddc2c7d40df437398a31a1739f6f0f5b1db244931020f'


def main():
    target = ROOT / 'prepared-source-and-published-baseline.json'
    assert not target.exists(), 'This prepared binding is immutable.'
    prep_path = ROOT / 'prepared-source-cohort.json'
    assert bind(prep_path)['sha256'] == '0adc0a78adeab76ad550a4d1d2a28fb87be0c9ff896fdce2bfc4d5f371d91b00'
    prep = read(prep_path)
    assert prep['result'] == 'SOURCE_PROVENANCE_PASS' and prep['source_commit'] == COMMIT
    cohort = ROOT / 'input/source-cohort-86.jsonl'
    assert bind(cohort)['sha256'] == COHORT_SHA
    sources = {identity(r): r for r in lines(cohort)}
    assert len(sources) == 86
    delivery_path = READBACK / 'delivery-manifest.json'
    assert bind(delivery_path)['sha256'] == READBACK_MANIFEST_SHA
    delivery = read(delivery_path)
    for item in delivery['files']:
        p = Path(item['local_path']); b = bind(p)
        assert all(b[k] == item[k] for k in b)
    receipt_path = READBACK / 'readback-receipt.json'
    assert bind(receipt_path)['sha256'] == '8f775dc70ed9d65c76b02b18424c0cadf355c212e43a23835d2c7f3c839990e1'
    receipt = read(receipt_path)
    assert receipt['status'] == 'PASS' and receipt['published_commit'] == PUBLISHED
    assert receipt['actual_root_tree'] == TREE and receipt['active_ledgers_before_and_after'] == 41

    def api(name):
        return json.loads(read(READBACK / 'input' / (name + '.json'))['content'])

    commit = api('published-commit')
    assert commit['sha'] == PUBLISHED and commit['tree']['sha'] == TREE
    assert [p['sha'] for p in commit['parents']] == ['17cd396eb858a29162505d545aad556ac73ce9ce']
    names = {'': 'after-root-tree', 'imports': 'after-tree-imports',
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
    assert len(review_entries) == 41
    prior_repo = WORK / 'phase19-checkpoint3e574-independent-integration/validation/combined-reviews'
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
                         'ids': sorted(group), 'exact_b7f21_git_blob_verified': True})
        if 'source_ledger_path' in ledger:
            dep = str(safe(ledger['source_ledger_path']))
            source_dep = prior_repo / dep
            assert source_dep.is_file() and bind(source_dep)['sha256'] == ledger['source_ledger_sha256']
            if dep in dependencies:
                assert dependencies[dep]['sha256'] == ledger['source_ledger_sha256']
            dependencies[dep] = {'path': dep, 'original_local_path': str(source_dep), **bind(source_dep)}
            immutable(published_root / dep, source_dep.read_bytes())
    assert len(ids) == 3490
    native = SourceReviews(published_root, 'deenhindi')
    assert set(native.decisions) == ids
    current477 = next(r for r in bindings if r['records'] == 477)
    assert current477['sha256'] == '6d099f91f2e406b6ca026930f4437cc1ce3983e26883cfedc3049f9cbb2f91a7'
    queue_path = WORK / 'phase20-independent-readback/downloaded' / QUEUE
    qb = bind(queue_path)
    assert qb['sha256'] == '8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349'
    qe = next(r for r in trees['reports/web-source-resolution-20261113']['tree'] if r['path'] == Path(QUEUE).name)
    assert qe['sha'] == qb['git_blob_sha1'] and qe['size'] == qb['bytes']
    queue_rows = lines(queue_path)
    counts = collections.Counter(f['language'] for r in queue_rows for f in r['fields'])
    assert len(queue_rows) == 3354 and counts == {'hi': 3260, 'ur': 3051}
    immutable(published_root / QUEUE, queue_path.read_bytes())
    old80_path = WORK / 'phase19-checkpoint3e574-independent-integration/input/source-cohort-80.jsonl'
    old80 = {identity(r) for r in lines(old80_path)}
    assert len(old80) == 80 and old80 <= ids and not old80 & set(sources)
    old80_counts = collections.Counter(native.decisions[k][2] for k in old80)
    assert old80_counts == {'register': 75, 'exclude': 5}
    result = {**prep, 'schema': 'hadith-bank-checkpoint0d2fa-integration-preparation-v1', 'result': 'PASS',
        'source_preparation_receipt': bind(prep_path),
        'publication_binding_generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'published_review_baseline_commit': PUBLISHED, 'published_root_tree': TREE,
        'published_review_baseline_checked_here': True,
        'independent_readback_delivery': bind(delivery_path), 'independent_readback_receipt': bind(receipt_path),
        'published_review_tree_ancestry': tree_receipts, 'published_active_ledgers': 41,
        'published_manual_decision_ids': 3490, 'published_ledger_bindings': bindings,
        'published_source_ledger_dependencies': list(dependencies.values()),
        'all86_disjoint_from_all3490_prior_manual_ids': True,
        'old80_published_dispositions': dict(old80_counts),
        'updated477_active_sha256': current477['sha256'],
        'canonical_priority_queue': {'path': QUEUE, **qb, 'pending_fields': 6311, 'occurrences': 3354,
                                     'by_language': dict(counts)},
        'current_newer_main_checkpoint_or_history_not_audited_here': True}
    immutable(target, enc(result))
    print(json.dumps({'result': 'PASS', 'preparation': bind(target), 'published_ledgers': 41,
                      'published_ids': 3490, 'new_source_ids': 86, 'queue_fields': 6311}))


if __name__ == '__main__':
    main()
