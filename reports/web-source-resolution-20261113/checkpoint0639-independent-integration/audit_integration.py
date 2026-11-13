"""Verify the four final manual packages against the exact saved 0639 cohort.

This audit does not perform new semantic classification. It binds each primary
package to a separately completed full-reading audit, checks native application
and every original field partition, and checks all prior imported/manual IDs.
"""
from pathlib import Path, PurePosixPath
import collections
import copy
import datetime
import gzip
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews, unique_pairs

MONITOR = WORK / 'phase13-successor-acquisition-monitor'
EVIDENCE = MONITOR / 'held-evidence'
COHORT = MONITOR / 'next-review-cohort/held-source-records.jsonl'
COMMIT = '0639af7fd15786284b4c413fced77e38eec8825a'
COHORT_SHA = 'a253b86c17219976a4db42e0b203a14affa8f01b62f7e58fbe3ec145aeb3efb8'
MONITOR_MANIFEST_SHA = '9d5eb33b8e03816ce8a4356f764ad033410836529aa6186ec92a5a9da279ed0a'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gitsha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data,
                      object_pairs_hook=unique_pairs)


def lines(path):
    data = path.read_bytes()
    if path.suffix == '.gz':
        data = gzip.decompress(data)
    return [json.loads(line, object_pairs_hook=unique_pairs) for line in data.splitlines() if line.strip()]


def oid(row):
    return row.get('occurrence_id', row.get('id')) or 'deenhindi-' + row['collection'] + ':' + str(row['number'])


def safe(path):
    relative = PurePosixPath(path)
    assert path and not relative.is_absolute() and '..' not in relative.parts and '\\' not in path
    return relative


def bind(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': gitsha(data)}


def leaves(value):
    if isinstance(value, dict):
        return sum(leaves(v) for v in value.values())
    if isinstance(value, list):
        return sum(leaves(v) for v in value)
    return 1


def equal(before, after):
    assert before == after
    return leaves(before)


def checked_delivery(path, expected_sha):
    assert sha(path.read_bytes()) == expected_sha
    manifest = read(path)
    result = []
    for item in manifest['files']:
        relative = item.get('path', item.get('repository_path'))
        safe(relative)
        local = Path(item.get('local_path') or item['source_path'])
        assert local.is_file() and not local.is_symlink()
        assert local.resolve().is_relative_to(path.parent.resolve())
        receipt = bind(local)
        assert receipt['bytes'] == item.get('bytes', item.get('size_bytes'))
        assert receipt['sha256'] == item['sha256']
        assert not item.get('git_blob_sha1') or receipt['git_blob_sha1'] == item['git_blob_sha1']
        result.append({'path': relative, 'local_path': str(local), **receipt})
    assert len({x['path'] for x in result}) == len(result)
    return manifest, result


def main():
    config = read(ROOT / 'input-manifests.json')
    assert len(config['review_packages']) == 4
    assert all(x['confirmed_final'] for x in config['review_packages']), 'Final independent audits still pending'
    assert sha(COHORT.read_bytes()) == COHORT_SHA
    source_rows = lines(COHORT)
    sources = {oid(row): row for row in source_rows}
    assert len(sources) == len(source_rows) == 117
    assert collections.Counter(x['collection'] for x in source_rows) == {
        'bukhari': 43, 'muslim': 25, 'nasai': 19, 'abudawud': 15, 'tirmidhi': 6, 'ibnmajah': 9}

    # Exact prior/current acquisition authority, already downloaded from GitHub.
    _, monitor_files = checked_delivery(MONITOR / 'delivery-manifest.json', MONITOR_MANIFEST_SHA)
    authority_item = next(x for x in monitor_files if x['path'].endswith('saved-state-audit.json'))
    acquisition_audit = read(Path(authority_item['local_path']))
    assert acquisition_audit['status'] == 'PASS' and acquisition_audit['saved_commit'] == COMMIT
    before_path = WORK / 'phase13-acquisition-monitor/saved-checkpoint/state.json'
    after_path = MONITOR / 'saved-checkpoint/state.json'
    progress_path = MONITOR / 'saved-checkpoint/progress.json'
    for path, expected in [(before_path, acquisition_audit['baseline_receipts']['state.json']),
                           (after_path, acquisition_audit['source_input_receipts']['state.json']),
                           (progress_path, acquisition_audit['source_input_receipts']['progress.json'])]:
        actual = bind(path)
        assert all(actual[k] == expected[k] for k in actual)
    before, after, progress = read(before_path), read(after_path), read(progress_path)
    assert len(before['imported']) == 15215 and len(after['imported']) == 15672
    held_keys = {x.removeprefix('deenhindi-') for x in sources}
    assert not held_keys & set(before['imported'])
    assert held_keys <= set(after['imported'])
    assert all(before['imported'][k] == after['imported'][k] for k in before['imported'])
    assert before['errors'] == after['errors'] == {}
    assert before['reviewed_error_attempts'] == after['reviewed_error_attempts']
    assert before['error_history'] == after['error_history']

    # Bind all 25 existing manual ledgers to the saved worker's actual inputs.
    overlays = {}
    for directory in ['phase2-integration/repo', 'phase3-recovered-review/publish',
                      'phase5-language-publication/publish', 'phase6-final-publication/publish',
                      'phase8-next93-publication/publish', 'phase10-final-publication/publish',
                      'phase11-original-ibnmajah-remaining-urdu/publish-v2', 'phase13-final-publication/publish']:
        for path in (WORK / directory / 'imports/web-deenhindi-20261112/reviews').glob('source-review*.json*'):
            overlays[path.name] = path
    overlays['source-review-20261113-bukhari-first300.json.gz'] = WORK / 'reuse-evidence-fix/existing-deen300-review.json.gz'
    authority_reviews = {Path(x['path']).name: x for x in progress['source_review_inputs']
                         if '/reviews/source-review' in x['path']}
    assert set(overlays) == set(authority_reviews) and len(overlays) == 25
    prior_ids, prior_bindings = set(), []
    for name, path in sorted(overlays.items()):
        receipt = bind(path)
        assert receipt['sha256'] == authority_reviews[name]['sha256']
        assert receipt['bytes'] == authority_reviews[name]['size_bytes']
        ledger = read(path)
        records = ledger.get('records', ledger.get('decisions'))
        ids = {oid(x) for x in records}
        assert len(ids) == len(records) and not ids & prior_ids and not ids & set(sources)
        prior_ids |= ids
        prior_bindings.append({'path': authority_reviews[name]['path'], **receipt, 'records': len(ids),
                               'id_set_sha256': sha(encode(sorted(ids))), 'bound_to_saved_progress': True})
    assert len(prior_ids) == 3101

    repo = ROOT / 'validation/repo'
    delivered, package_receipts, audit_receipts = {}, [], []
    active_paths, decisions, decision_paths = [], {}, {}
    for spec in config['review_packages']:
        manifest_path = Path(spec['manifest_path'])
        _, files = checked_delivery(manifest_path, spec['manifest_sha256'])
        _, audit_files = checked_delivery(Path(spec['independent_audit_manifest_path']),
                                           spec['independent_audit_manifest_sha256'])
        audit_reports = [read(Path(x['local_path'])) for x in audit_files
                         if x['path'].endswith('.json') and 'manifest' not in x['path']]
        assert any(d.get('status', d.get('result')) == 'PASS' and spec['active_sha256'] in json.dumps(d)
                   and spec['manifest_sha256'] in json.dumps(d) for d in audit_reports)
        audit_receipts.append({'package': spec['name'],
                               'manifest_sha256': spec['independent_audit_manifest_sha256'],
                               'files': [{k: v for k, v in x.items() if k != 'local_path'} for x in audit_files]})
        package_active = [x for x in files if Path(x['path']).parent.as_posix() ==
                          'imports/web-deenhindi-20261112/reviews' and Path(x['path']).name.startswith('source-review')]
        assert len(package_active) == 1 and package_active[0]['sha256'] == spec['active_sha256']
        for item in files:
            relative = item['path']
            assert relative not in delivered
            data = Path(item['local_path']).read_bytes()
            out = repo / relative
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            delivered[relative] = item
        package_receipts.append({'package': spec['name'], 'manifest_sha256': spec['manifest_sha256'],
                                 'active_ledger_path': package_active[0]['path'],
                                 'active_ledger_sha256': spec['active_sha256'],
                                 'files': [{k: v for k, v in x.items() if k != 'local_path'} for x in files]})
        active_path = package_active[0]['path']
        active_paths.append(active_path)
        ledger = read(repo / active_path)
        baseline_path = repo / safe(ledger['source_ledger_path'])
        assert sha(baseline_path.read_bytes()) == ledger['source_ledger_sha256']
        baselines = lines(baseline_path)
        baseline_by_id = {oid(x): x for x in baselines}
        rows = ledger.get('records', ledger.get('decisions'))
        assert len(rows) == len(baselines) == len(baseline_by_id)
        for decision in rows:
            identity = oid(decision)
            assert identity not in decisions and identity in baseline_by_id and identity in sources
            assert baseline_by_id[identity] == sources[identity]
            assert decision['source_record_sha256'] == sha(importer.json_bytes(sources[identity]['source_record']))
            assert decision['source_reference_verbatim'] == sources[identity]['source_reference_verbatim']
            decisions[identity], decision_paths[identity] = decision, active_path
    assert set(decisions) == set(sources) and len(active_paths) == 4

    evidence = read(EVIDENCE / 'evidence-manifest.json')
    entries = read(EVIDENCE / 'held-state-entries.json')
    assert evidence['saved_head'] == COMMIT and set(evidence['held_keys']) == held_keys
    assert set(entries) == held_keys
    source_files = []
    for identity, saved in sources.items():
        key = identity.removeprefix('deenhindi-')
        assert entries[key] == after['imported'][key]
        assert entries[key]['parsed']['path'] == saved['parsed_path']
        for kind, desc in [('raw', saved['snapshot']), ('parsed', entries[key]['parsed'])]:
            path = EVIDENCE / 'sources' / safe(desc['path'])
            receipt = bind(path)
            declared = evidence['files'][desc['path']]
            assert receipt['bytes'] == declared['stored_bytes'] and receipt['sha256'] == declared['stored_sha256']
            assert receipt['git_blob_sha1'] == declared['git_blob_sha1']
            plain = importer.checked_bytes(EVIDENCE / 'sources', desc)
            assert sha(plain) == desc['sha256']
            source_files.append({'id': identity, 'kind': kind, 'path': desc['path'], **receipt,
                                 'plain_sha256': sha(plain)})
            if kind == 'raw':
                record, reference = importer.parse_record(plain, saved['collection'], saved['number'])
                assert record == saved['source_record'] and reference == saved['source_reference_verbatim']
                assert sha(importer.json_bytes(record)) == evidence['source_record_sha256'][key]
            else:
                parsed = json.loads(plain)
                for name in ['collection', 'number', 'source_record', 'source_reference_verbatim', 'snapshot']:
                    assert parsed[name] == saved[name]
                assert parsed['classification'] == saved.get('intake_classification', saved['classification'])

    native = SourceReviews(repo, 'deenhindi')
    assert set(native.decisions) == set(decisions)
    counts, metadata = collections.Counter(), collections.Counter()
    by_language, by_collection = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    records, script_fixes = [], []
    for identity, saved in sorted(sources.items()):
        decision = decisions[identity]
        original = importer.canonical_record(saved)
        original_copy = copy.deepcopy(original)
        revised, action = native.apply(original, saved=saved)
        assert original == original_copy and action == decision['decision']
        assert revised['review']['independent_pro_qc'] == 'not_performed'
        assert revised['review']['certified_release_eligible'] is False
        for name, value in original_copy.items():
            if name not in ['text', 'language_versions', 'review', 'content_kind', 'extraction']:
                metadata['parent'] += equal(value, revised[name])
        fields = decision.get('fields', decision.get('field_reviews'))
        fields_by_language = {f['language']: f for f in fields}
        assert len(fields) == len(fields_by_language) <= 5
        assert set(fields_by_language) <= set(importer.LANGUAGE_FIELDS)
        assert len(original_copy['language_versions']) == len(revised['language_versions']) == 5
        details = []
        for before, after in zip(original_copy['language_versions'], revised['language_versions']):
            language, text = before['language'], before['text']
            assert text
            f = fields_by_language.get(language)
            reviewed = f['reviewed'] if f is not None else False
            assert isinstance(reviewed, bool)
            if f is not None:
                assert f['source_field'] == importer.LANGUAGE_FIELDS[language]
                assert f['text_sha256'] == sha(text.encode()) and f.get('text_chars', len(text)) == len(text)
                assert f['chars_reviewed'] == (len(text) if reviewed else 0)
                assert f['bytes_reviewed'] == (len(text.encode()) if reviewed else 0)
                spans = f.get('spans', f.get('selected_spans', []))
                counts['explicit_field_decisions'] += 1
            else:
                # Native SourceReviews preserves an omitted field as wholly
                # unread context. Verify that actual output below, without
                # adding a synthetic field approval to any source ledger.
                spans = []
                counts['implicit_unread_field_slots'] += 1
            assert not spans or reviewed
            assert after['source']['manual_review']['field_reviewed'] is reviewed
            assert (after['text'] or '') == ''.join(text[s['start']:s['end']] for s in spans)
            parts = []
            for s in spans:
                a, b = s['start'], s['end']
                assert 0 <= a < b <= len(text) and sha(text[a:b].encode()) == s['sha256']
                assert s['speaker'].strip() and s['report_type'].strip()
                parts.append((a, b, text[a:b]))
            for c in after.get('comments', []):
                if c.get('source_span') is None:
                    continue
                a, b = c['source_span']
                assert c['scope'] == 'source_context_not_narration' and c['text'] == text[a:b]
                assert c['source_text_sha256'] == sha(text[a:b].encode())
                parts.append((a, b, c['text']))
            cursor = 0
            for a, b, part in sorted(parts):
                assert a == cursor and a < b <= len(text) and part == text[a:b]
                cursor = b
            assert cursor == len(text) and ''.join(p[2] for p in sorted(parts)) == text
            status = 'admitted' if spans else 'read_context' if reviewed else 'unread_context'
            counts[status] += 1
            by_language[language][status] += 1
            counts['partitions'] += 1
            counts['selected_spans'] += len(spans)
            if reviewed:
                counts['read_fields'] += 1
                counts['read_characters'] += len(text)
                counts['read_utf8_bytes'] += len(text.encode())
            assert language not in ['hi', 'ur'] or reviewed
            if action == 'exclude':
                assert reviewed and not spans
            for name, value in before.items():
                if name in ['text', 'scope', 'source', 'comments']:
                    continue
                if name == 'script' and value != after[name]:
                    assert reviewed and after[name] == f['observed_script'] and f['source_script_note']
                    script_fixes.append({'id': identity, 'language': language, 'before': value, 'after': after[name]})
                else:
                    metadata['language'] += equal(value, after[name])
            for name, value in before['source'].items():
                metadata['source'] += equal(value, after['source'][name])
            for index, comment in enumerate(before.get('comments', [])):
                for name, value in comment.items():
                    metadata['previous_comments'] += equal(value, after['comments'][index][name])
            details.append({'language': language, 'source_field_sha256': sha(text.encode()),
                            'characters': len(text), 'utf8_bytes': len(text.encode()), 'status': status,
                            'selected_spans': spans, 'explicit_field_decision': f is not None,
                            'exact_partition_verified': True})
        counts[action] += 1
        by_collection[saved['collection']][action] += 1
        records.append({'id': identity, 'decision': action, 'review_path': decision_paths[identity],
                        'source_record_sha256': decision['source_record_sha256'], 'fields': details})
    native.finish()
    assert counts['register'] + counts['exclude'] == 117 and counts['partitions'] == 585
    assert counts['admitted'] + counts['read_context'] == counts['read_fields']
    assert counts['read_fields'] + counts['unread_context'] == 585
    for item in delivered.values():
        assert bind(Path(item['local_path']))['sha256'] == item['sha256']
    for spec in config['review_packages']:
        assert sha(Path(spec['manifest_path']).read_bytes()) == spec['manifest_sha256']
        assert sha(Path(spec['independent_audit_manifest_path']).read_bytes()) == spec['independent_audit_manifest_sha256']

    report = {'schema': 'hadith-bank-checkpoint0639-independent-integration-audit-v1', 'status': 'PASS',
              'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_commit': COMMIT, 'source_cohort_sha256': COHORT_SHA,
              'source_count': 117, 'active_ledgers': 4, 'primary_package_files_verified': len(delivered),
              'prior_imported_occurrences': 15215, 'prior_manual_occurrences': 3101,
              'prior_manual_ledgers': 25, 'new_id_collisions': [],
              'all_prior_manual_ledger_hashes_bound_to_actual_saved_progress': True,
              'all117_exactly_cover_current_held_set': True, 'all117_absent_prior_imported_and_manual_sets': True,
              'source_raw_and_parsed_files_reopened': 234, 'raw_pages_reparsed': 117,
              'all_raw_parsed_and_full_source_objects_exact': True,
              'counts': dict(counts), 'language_coverage': dict(by_language), 'collection_coverage': dict(by_collection),
              'metadata_leaf_equalities': dict(metadata), 'metadata_leaf_equalities_total': sum(metadata.values()),
              'script_corrections': script_fixes, 'native_apply_finish': 'PASS',
              'engine_sha256': native.engine_sha256, 'parser_sha256': sha(Path(importer.__file__).read_bytes()),
              'state_authority': {'baseline_commit': acquisition_audit['baseline_commit'],
                                  'baseline_state': bind(before_path), 'saved_state': bind(after_path),
                                  'saved_progress': bind(progress_path), 'acquisition_audit_manifest_sha256': MONITOR_MANIFEST_SHA,
                                  'acquisition_audit_sha256': authority_item['sha256']},
              'primary_package_receipts': package_receipts, 'independent_linguistic_audit_receipts': audit_receipts,
              'prior_manual_ledger_bindings': prior_bindings,
              'fixed_checkpoint_derived_totals_after_this117': {
                  'fetched': 15672, 'registered': 15409 + counts['register'],
                  'resolved_source_only': 146 + counts['exclude'], 'held': 0, 'unfetched': 20718},
              'derived_totals_are_newly_saved_export': False,
              'no_new_linguistic_approvals_by_integration': True,
              'source_http_requests': 0, 'github_writes': 0, 'independent_pro_qc': 'not_performed',
              'limitations': 'Exact four final review packages and fixed0639 cohort only. Full semantic reread receipts are separate and hash-bound; future acquisition checkpoints and live reader deployment are not claimed.'}
    prefix = Path('reports/web-source-resolution-20261113/checkpoint0639-independent-integration')
    outputs = {
        prefix / 'validation-report.json': encode(report),
        prefix / 'per-occurrence-source-and-partition-proof.json.gz': gzip.compress(encode({'records': records, 'source_files': source_files}), mtime=0),
        prefix / 'input-manifests.json': (ROOT / 'input-manifests.json').read_bytes(),
        prefix / 'audit_integration.py': Path(__file__).read_bytes()}
    files = []
    for relative, data in outputs.items():
        out = ROOT / 'publish' / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        assert not out.exists(), 'Final integration output already frozen'
        out.write_bytes(data)
        files.append({'path': relative.as_posix(), 'local_path': str(out), **bind(out)})
    manifest = {'schema': 'hadith-bank-independent-integration-delivery-v1', 'status': 'PASS',
                'source_commit': COMMIT, 'files': files, 'total_files': len(files),
                'total_bytes': sum(x['bytes'] for x in files), 'counts': dict(counts)}
    (ROOT / 'delivery-manifest.json').write_bytes(encode(manifest))
    print(json.dumps({'status': 'PASS', 'counts': dict(counts), 'metadata_leaf_equalities': sum(metadata.values()),
                      'manifest_sha256': sha(encode(manifest)), 'report_sha256': sha(encode(report)),
                      'files': len(files), 'bytes': manifest['total_bytes']}, indent=2))


if __name__ == '__main__':
    main()
