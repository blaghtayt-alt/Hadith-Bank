#!/usr/bin/env python3
"""Freeze the successful but superseded a6 reader separately from actual deployment."""
import gzip
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'publish'
sha = lambda b: hashlib.sha256(b).hexdigest()
blob = lambda b: hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
enc = lambda o: (json.dumps(o, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def main():
    assert not (ROOT / 'delivery-manifest.json').exists()
    observed = json.loads((ROOT / 'raw-observation.json').read_bytes())
    run = observed['run']
    assert run['id'] == 43497811581 and run['head_sha'] == 'a6c52f35a320b10259bc7cc6200c53118d77f149'
    assert run['status'] == 'completed' and run['conclusion'] == 'success'
    jobs = {j['name']: j for j in observed['jobs']['jobs']}
    build_job = jobs['Refresh bank and build website']
    assert build_job['id'] == 132135412064 and build_job['conclusion'] == 'success'
    steps = {s['name']: s for s in build_job['steps']}
    for name in ('Run software tests', 'Export saved Fawaz reviews and preserve published quotations',
                 'Apply changed saved website reviews before shared validation',
                 'Synchronize official counterpart sources for newly registered IDs',
                 'Rebuild and validate all registered material', 'Verify bounded reader in Chromium',
                 'Keep generated bank files synchronized'):
        assert steps[name]['conclusion'] == 'success'
    assert steps['Upload the verified website']['conclusion'] == 'skipped'
    assert jobs['Publish verified website']['conclusion'] == 'skipped'
    compressed = (ROOT / 'build-job.log.gz').read_bytes()
    raw = gzip.decompress(compressed)
    transfer = json.loads((ROOT / 'build-log-transfer-receipt.json').read_bytes())
    assert len(raw) == transfer['uncompressed_bytes'] == 91351
    assert sha(raw) == transfer['uncompressed_sha256'] == 'a715a8cf11f82ea1406ea92670c804360c4a5c9a900e0a64e16f1f6925b77b69'
    assert sha(compressed) == transfer['stored_sha256'] == 'f5a643168c05bbec458e492ba3289192640e1e922e845470688eb2509c34e4fc'
    log = raw.decode()
    assert 'Ran 994 tests in 52.138s' in log and 'ℹ tests 43' in log and 'ℹ pass 43' in log and 'ℹ fail 0' in log
    sections = json.loads((ROOT / 'log-json-objects.json').read_bytes())
    site = next(o for o in sections if o.get('schema') == 'hadith-bank-site-build-v1')
    browser = next(o for o in sections if o.get('schema') == 'hadith-bank-reader-browser-smoke-v1')
    web = next(o for o in sections if o.get('schema') == 'hadith-bank-web-import-status-v1')
    guard = next(o for o in sections if o.get('status') == 'superseded')
    fawaz = next(o for o in sections if o.get('phase') == 'export' and o.get('status') == 'passed') if any(o.get('phase') == 'export' and o.get('status') == 'passed' for o in sections) else next(o for o in sections if 'provider_occurrences' in o and o.get('status') == 'passed')
    assert site['status'] == browser['status'] == 'passed'
    assert site['source_commit'] == run['head_sha']
    assert site['record_count'] == browser['actual_site']['record_count'] == 102452
    assert site['source_dataset_count'] == 251 and browser['actual_site']['grouped_reading_count'] == 102395
    assert len(browser['checks']) == 14 and browser['elapsed_seconds'] == 17.808
    assert guard == {'status': 'superseded', 'publish': False, 'expected_start': run['head_sha'],
                     'generated_commit': '2619c199cdb24f1edb3c46026259f93ff2da5bdd',
                     'remote_commit': '31c01136611b163683a01b47833bf74354820851', 'build_request': 'submitted'}
    artifacts = observed['artifacts']['artifacts']
    assert {a['id'] for a in artifacts} == {14073907533, 14071809670}
    assert not any(a['name'] == 'github-pages' for a in artifacts)
    actual_deployment_manifest = ROOT.parent / 'reader-monitor-7a3462e/delivery-manifest.json'
    assert sha(actual_deployment_manifest.read_bytes()) == '9fd120fd236fcc6220839a5e12d89380dfec1a1bf2cba99143da93501b3529b4'
    lines = log.splitlines()
    evidence_lines = [line for line in lines if re.search(r'Ran 994 tests|ℹ tests |ℹ pass |ℹ fail |ℹ duration_ms |"status": "superseded"|43501979566|\[main 2619c199c\]', line)]
    report = {
        'schema': 'hadith-bank-reader-terminal-observation-v1', 'result': 'SUCCESS_WITH_SUPERSESSION',
        'run': run, 'job_summaries': observed['jobs']['jobs'],
        'observation_window_start_utc': observed['observation_window_start_utc'],
        'observation_window_end_utc': observed['observation_window_end_utc'],
        'software_tests': {'python_passed': 994, 'python_seconds': 52.138, 'node_tests': 43, 'node_passed': 43, 'node_failed': 0},
        'actual_shared_build': site, 'actual_browser_result': browser,
        'actual_fawaz_export': fawaz, 'actual_web_review_export_status': web,
        'exact_publication_guard': guard,
        'generated_commit_was_not_published_by_this_run': True,
        'verified_website_upload': 'skipped', 'pages_deployment': 'skipped',
        'normal_guard_requested_successor_run': 43501979566,
        'successor_state_at_observation': observed['current_reader'],
        'main_observation': observed['main'], 'artifacts_metadata_only': artifacts,
        'full_job_log': transfer, 'exact_test_and_guard_lines': evidence_lines,
        'last_separately_verified_actual_pages_deployment': {
            'source_commit': '7a3462ef5513e3c116ead9a496420e8b9f484841',
            'generated_commit': 'd304bef0c7955377026a0c2aeebdd677b1e05b0a',
            'run_id': 43492613360, 'success_log_utc': '2026-11-13T19:59:53.8603876Z',
            'receipt_manifest_sha256': '9fd120fd236fcc6220839a5e12d89380dfec1a1bf2cba99143da93501b3529b4'
        },
        'github_writes': 0, 'manual_dispatches': 0, 'workflow_enabling': 0,
        'source_http_requests': 0, 'artifact_archive_downloads': 0,
        'limitations': 'This exact a6 build passed software, export, shared validation and Chromium, then its normal publication guard detected the newer31c main. It neither uploaded a Pages artifact nor deployed. Its unpushed generated2619 commit is a log observation, not a remote checkpoint. The current31c successor was still working at observation; no later deployment, source acquisition or CDN-byte state is inferred.'
    }
    files = []
    prefix = 'reports/web-source-resolution-20261113/reader-a6c52f35-superseded'
    for path, data in [
        ('reports/web-source-resolution-20261113/reader-a6c52f35-superseded-receipt.json', enc(report)),
        (prefix + '/build-job.log.gz', compressed),
        (prefix + '/observed-run-jobs-artifacts.json', (ROOT / 'raw-observation.json').read_bytes()),
        (prefix + '/freeze_receipt.py', Path(__file__).read_bytes()),
    ]:
        p = OUT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        files.append({'path': path, 'local_path': str(p), 'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': blob(data)})
    manifest = {'schema': 'hadith-bank-reader-evidence-delivery-v1', 'run_id': run['id'], 'source_commit': run['head_sha'], 'result': report['result'], 'files': files, 'total_files': len(files), 'total_bytes': sum(f['bytes'] for f in files)}
    mb = enc(manifest)
    (ROOT / 'delivery-manifest.json').write_bytes(mb)
    print(json.dumps({'manifest_sha256': sha(mb), 'report_sha256': files[0]['sha256'], 'files': len(files), 'bytes': manifest['total_bytes'], 'reader_sha256': site['reader_sha256'], 'python_tests': 994, 'node_tests': 43, 'browser_checks': 14, 'superseded_by': guard['remote_commit'], 'deployment': 'skipped'}, indent=2))


if __name__ == '__main__':
    main()
