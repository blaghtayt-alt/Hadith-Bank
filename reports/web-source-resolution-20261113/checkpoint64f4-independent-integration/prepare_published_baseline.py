"""Bind the phase23 source packet to the independently read-back31c0113 baseline."""
from pathlib import Path
import collections
import datetime
import json
from prepare_source_and_published_baseline import (
    ROOT, WORK, COMMIT, REVIEWS, QUEUE, COHORT_SHA, sha, git, enc, read, lines,
    safe, bind, identity, immutable, SourceReviews)

PUBLISHED = '31c01136611b163683a01b47833bf74354820851'
TREE = 'ef2a623731fad42608136ccff3118e174e47d0b1'
READBACK = WORK / 'phase22-independent-readback'
READBACK_MANIFEST_SHA = 'f90886e0cf94bbe0e13716c19eea46e172419e0a2e59c8ae7d1691e82aba0e56'


def main():
    target = ROOT / 'prepared-source-and-published-baseline.json'
    assert not target.exists(), 'This prepared binding is immutable.'
    prep_path = ROOT / 'prepared-source-cohort.json'
    assert bind(prep_path)['sha256'] == '09b0a9c26bba2bb1a2c2ebf55d043c1ef8dbbbed65b81e1a93c30946ca15d6ba'
    prep = read(prep_path)
    assert prep['result'] == 'SOURCE_PROVENANCE_PASS' and prep['source_commit'] == COMMIT
    cohort = ROOT / 'input/source-cohort-102.jsonl'
    assert bind(cohort)['sha256'] == COHORT_SHA
    sources = {identity(r): r for r in lines(cohort)}
    assert len(sources) == 102
    delivery_path = READBACK / 'delivery-manifest.json'
    assert bind(delivery_path)['sha256'] == READBACK_MANIFEST_SHA
    delivery = read(delivery_path)
    for item in delivery['files']:
        p = Path(item['local_path']); b = bind(p)
        assert all(b[k] == item[k] for k in b)
    receipt_path = READBACK / 'readback-receipt.json'
    assert bind(receipt_path)['sha256'] == '7c8aa6deff7a735a8bd98a4e6c0902289454f1b38cfa51c4afb9602682616b48'
    receipt = read(receipt_path)
    assert receipt['status'] == 'PASS' and receipt['published_commit'] == PUBLISHED
    assert receipt['actual_root_tree'] == TREE and receipt['resulting_active_ledgers'] == 49

    def api(name):
        return json.loads(read(READBACK / 'input' / (name + '.json'))['content'])

    commit = api('published-commit')
    assert commit['sha'] == PUBLISHED and commit['tree']['sha'] == TREE
    assert [p['sha'] for p in commit['parents']] == ['a6c52f35a320b10259bc7cc6200c53118d77f149']
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
    assert len(review_entries) == 49
    prior_repo = WORK / 'phase22-checkpoint17cd-independent-integration/validation/combined-reviews'
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
                         'ids': sorted(group), 'exact_31c0113_git_blob_verified': True})
        if 'source_ledger_path' in ledger:
            dep = str(safe(ledger['source_ledger_path']))
            source_dep = prior_repo / dep
            assert source_dep.is_file() and bind(source_dep)['sha256'] == ledger['source_ledger_sha256']
            if dep in dependencies:
                assert dependencies[dep]['sha256'] == ledger['source_ledger_sha256']
            dependencies[dep] = {'path': dep, 'original_local_path': str(source_dep), **bind(source_dep)}
            immutable(published_root / dep, source_dep.read_bytes())
    assert len(ids) == 3661
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
    old86_path = WORK / 'phase21-checkpoint0d2fa-independent-integration/input/source-cohort-86.jsonl'
    old86 = {identity(r) for r in lines(old86_path)}
    assert len(old86) == 86 and old86 <= ids and not old86 & set(sources)
    old86_counts = collections.Counter(native.decisions[k][2] for k in old86)
    assert old86_counts == {'register': 84, 'exclude': 2}
    old85_path = WORK / 'phase22-checkpoint17cd-independent-integration/input/source-cohort-85.jsonl'
    old85 = {identity(r) for r in lines(old85_path)}
    assert len(old85) == 85 and old85 <= ids and not old85 & set(sources) and not old85 & old86
    old85_counts = collections.Counter(native.decisions[k][2] for k in old85)
    assert old85_counts == {'register': 84, 'exclude': 1}
    current_progress_path = WORK / 'phase23-generated-export-audit/progress.json'
    current_progress_binding = bind(current_progress_path)
    assert current_progress_binding['sha256'] == 'b205eaaf981fdb83286c4ca38b4ef0cff6065b0608ea84cd3d12ad24a94be1dd'
    assert current_progress_binding['git_blob_sha1'] == '558b4eaa1aa7d7174447db9e5475880681ef6226'
    source_tree = trees['imports/web-deenhindi-20261112']['tree']
    published_progress = next(r for r in source_tree if r['path'] == 'progress.json')
    assert published_progress['sha'] == current_progress_binding['git_blob_sha1'] and published_progress['size'] == current_progress_binding['bytes']
    current_progress = read(current_progress_path)
    current_counts = {k:current_progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked','done']}
    assert [current_counts[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count']] == [18570,18216,167,187,17820]
    state_binding = prep['full_saved_64f4_state']
    published_state = next(r for r in source_tree if r['path'] == 'state.json')
    assert published_state['sha'] == state_binding['git_blob_sha1'] and published_state['size'] == state_binding['bytes']
    immutable(ROOT / 'input/current-published-progress.json', current_progress_path.read_bytes())
    current_counts_receipt = {'published_commit':PUBLISHED, 'actual_generated_export':current_counts,
        'progress_binding':current_progress_binding, 'immutable_source_state_binding':state_binding,
        'generated_export_commit':'d304bef0c7955377026a0c2aeebdd677b1e05b0a',
        'historical64f4_worker_holds':273, 'current_published_generated_holds':187,
        'published85_review_projection_not_a_saved_export':{'registered':18300,'source_context':168,'held':102},
        'source_acquisition_count_unchanged':18570, 'new_export_or_live_deployment_claim':False}
    result = {**prep, 'schema': 'hadith-bank-checkpoint64f4-integration-preparation-v1', 'result': 'PASS',
        'source_preparation_receipt': bind(prep_path),
        'publication_binding_generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'published_review_baseline_commit': PUBLISHED, 'published_root_tree': TREE,
        'published_review_baseline_checked_here': True,
        'independent_readback_delivery': bind(delivery_path), 'independent_readback_receipt': bind(receipt_path),
        'published_review_tree_ancestry': tree_receipts, 'published_active_ledgers': 49,
        'published_manual_decision_ids': 3661, 'published_ledger_bindings': bindings,
        'published_source_ledger_dependencies': list(dependencies.values()),
        'all102_disjoint_from_all3661_prior_manual_ids': True,
        'old86_published_dispositions': dict(old86_counts),
        'old85_published_dispositions': dict(old85_counts),
        'all_old171_published_and_disjoint_new102': True,
        'current_published_generated_export_binding': current_counts_receipt,
        'updated477_active_sha256': current477['sha256'],
        'canonical_priority_queue': {'path': QUEUE, **qb, 'pending_fields': 6311, 'occurrences': 3354,
                                     'by_language': dict(counts)},
        'current_newer_main_checkpoint_or_history_not_audited_here': True}
    immutable(target, enc(result))
    print(json.dumps({'result': 'PASS', 'preparation': bind(target), 'published_ledgers': 49,
                      'published_ids': 3661, 'new_source_ids': 102, 'queue_fields': 6311}))


if __name__ == '__main__':
    main()
