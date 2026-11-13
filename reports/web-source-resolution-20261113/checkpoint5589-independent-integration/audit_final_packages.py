"""Integrate four independently approved new100 packages without new decisions."""
from pathlib import Path
import collections, copy, datetime, gzip, json, shutil
from prepare_source_and_published_baseline import (ROOT, WORK, COMMIT, PUBLISHED, REVIEWS,
    COHORT_SHA, sha, git, enc, read, lines, safe, bind, identity, immutable, SourceReviews, importer)


def checked_delivery(path, expected):
    path = Path(path)
    assert bind(path)['sha256'] == expected
    manifest = read(path); result = []
    for item in manifest['files']:
        relative = str(safe(item.get('path', item.get('repository_path'))))
        local = Path(item.get('local_path') or item['source_path'])
        assert local.is_file() and not local.is_symlink() and local.resolve().is_relative_to(path.parent.resolve())
        receipt = bind(local)
        assert receipt['bytes'] == item.get('bytes', item.get('size_bytes')) and receipt['sha256'] == item['sha256']
        assert not item.get('git_blob_sha1') or receipt['git_blob_sha1'] == item['git_blob_sha1']
        result.append({'path': relative, 'local_path': str(local), **receipt})
    assert len(result) == len({item['path'] for item in result})
    return manifest, result


def leaves(value):
    if isinstance(value, dict): return sum(leaves(v) for v in value.values()) if value else 1
    if isinstance(value, list): return sum(leaves(v) for v in value) if value else 1
    return 1


def main():
    assert not (ROOT / 'delivery-manifest.json').exists(), 'The completed integration is immutable.'
    config_path = ROOT / 'input-manifests.json'; config_bytes = config_path.read_bytes(); config = read(config_path)
    specs = config['review_packages']
    assert len(specs) == 4 and all(spec['confirmed_final'] for spec in specs), 'Final independent approvals still pending.'
    preparation_path = ROOT / 'prepared-source-and-published-baseline.json'
    assert bind(preparation_path)['sha256'] == '3757b51d7a2996f4ee04132ad661a53a5a88a661e458a65a7fb14c2218c76c70'
    preparation = read(preparation_path)
    assert preparation['result'] == 'PASS' and preparation['source_commit'] == COMMIT
    source_path = ROOT / 'input/source-cohort-100.jsonl'
    assert bind(source_path)['sha256'] == COHORT_SHA
    source_rows = lines(source_path); sources = {identity(row): row for row in source_rows}
    assert len(sources) == len(source_rows) == 100
    assert bind(ROOT / 'new100-raw-parsed-source-proof.json.gz')['sha256'] == 'ec11a368dbcd8526ece91daed6505cc1012338a073c549dc583c4500d9b969c1'
    source_files = read(ROOT / 'new100-raw-parsed-source-proof.json.gz')['records']
    assert len(source_files) == 200
    for receipt in source_files:
        path = WORK / 'phase15-successor-acquisition-monitor/held-evidence/sources' / receipt['path']
        actual = bind(path)
        assert all(actual[k] == receipt[k] for k in actual)

    published_root = ROOT / 'validation/published-reviews'
    for item in preparation['published_ledger_bindings'] + preparation['published_source_ledger_dependencies']:
        assert bind(published_root / item['path'])['sha256'] == item['sha256']
    prior_engine = SourceReviews(published_root, 'deenhindi')
    prior_ids = set(prior_engine.decisions)
    assert len(prior_ids) == 3218 and not prior_ids & set(sources)

    new_root = ROOT / 'validation/new-reviews'
    combined_root = ROOT / 'validation/combined-reviews'
    delivered, decisions, decision_paths, package_receipts, independent_receipts = {}, {}, {}, [], []
    package_expected, membership = {}, {}
    for spec in specs:
        _, files = checked_delivery(spec['manifest_path'], spec['manifest_sha256'])
        _, audit_files = checked_delivery(spec['independent_audit_manifest_path'], spec['independent_audit_manifest_sha256'])
        detailed_reports = [read(Path(item['local_path'])) for item in audit_files
                            if item['path'].endswith(('.json', '.json.gz')) and 'manifest' not in Path(item['path']).name]
        assert any(isinstance(report, dict) and report.get('result', report.get('status')) == 'PASS'
                   and spec['manifest_sha256'] in json.dumps(report)
                   and spec['active_sha256'] in json.dumps(report) for report in detailed_reports), spec['name']
        active = [item for item in files if Path(item['path']).parent.as_posix() == REVIEWS.as_posix()
                  and Path(item['path']).name.startswith('source-review')]
        assert len(active) == 1 and active[0]['sha256'] == spec['active_sha256']
        for item in files:
            relative = item['path']
            if relative in delivered:
                assert delivered[relative]['sha256'] == item['sha256'] and delivered[relative]['bytes'] == item['bytes']
            else:
                delivered[relative] = item
                immutable(new_root / relative, Path(item['local_path']).read_bytes())
        ledger = read(new_root / active[0]['path'])
        baseline_path = new_root / str(safe(ledger['source_ledger_path']))
        assert bind(baseline_path)['sha256'] == ledger['source_ledger_sha256']
        baseline = {identity(row): row for row in lines(baseline_path)}
        rows = ledger.get('records', ledger.get('decisions'))
        assert len(rows) == len(baseline) == spec['expected']['occurrences'] == 25
        for decision in rows:
            oid = identity(decision)
            assert oid in sources and oid not in decisions and oid not in prior_ids
            assert baseline[oid] == sources[oid]
            assert decision['source_record_sha256'] == sha(importer.json_bytes(sources[oid]['source_record']))
            assert decision['source_reference_verbatim'] == sources[oid]['source_reference_verbatim']
            decisions[oid] = decision; decision_paths[oid] = active[0]['path']; membership[oid] = spec['name']
        package_expected[spec['name']] = spec['expected']
        package_receipts.append({'name': spec['name'], 'manifest_sha256': spec['manifest_sha256'],
            'active_ledger_path': active[0]['path'], 'active_ledger_sha256': spec['active_sha256'],
            'files': [{k: v for k, v in item.items() if k != 'local_path'} for item in files]})
        independent_receipts.append({'name': spec['name'], 'manifest_sha256': spec['independent_audit_manifest_sha256'],
            'files': [{k: v for k, v in item.items() if k != 'local_path'} for item in audit_files]})
    assert set(decisions) == set(sources)

    # Native loader must accept all current29 plus the four new active ledgers.
    for tree in [published_root, new_root]:
        for path in sorted(tree.rglob('*')):
            if path.is_file(): immutable(combined_root / path.relative_to(tree), path.read_bytes())
    combined = SourceReviews(combined_root, 'deenhindi')
    assert set(combined.decisions) == prior_ids | set(sources) and len(combined.decisions) == 3318
    for oid in prior_ids:
        assert combined.decisions[oid] == prior_engine.decisions[oid]

    native = SourceReviews(new_root, 'deenhindi')
    assert set(native.decisions) == set(sources)
    counts = collections.Counter(); metadata = collections.Counter()
    languages = collections.defaultdict(collections.Counter); collections_count = collections.defaultdict(collections.Counter)
    packages = collections.defaultdict(collections.Counter); checks, script_corrections = [], []
    for oid, saved in sorted(sources.items()):
        decision = decisions[oid]; original = importer.canonical_record(saved); before = copy.deepcopy(original)
        result, action = native.apply(original, saved=saved)
        assert original == before and action == decision['decision']
        assert result['review']['independent_pro_qc'] == 'not_performed' and result['review']['certified_release_eligible'] is False
        assert result['number']['canonical'] is None
        for key, value in before.items():
            if key not in ('text', 'language_versions', 'review', 'content_kind', 'extraction', 'report_types'):
                assert result.get(key) == value, (oid, key)
                metadata['parent'] += leaves(value)
        fields = decision.get('fields', decision.get('field_reviews')); by_language = {f['language']: f for f in fields}
        assert len(fields) == len(by_language) <= 5
        assert len(before['language_versions']) == len(result['language_versions']) == 5
        parent_admitted, details = {}, []
        for prior, version in zip(before['language_versions'], result['language_versions']):
            language, text = prior['language'], prior['text']; assert text
            field = by_language.get(language); reviewed = field['reviewed'] if field else False
            assert type(reviewed) is bool and (language not in ('hi', 'ur') or reviewed)
            if field:
                assert field['source_field'] == importer.LANGUAGE_FIELDS[language]
                assert field['text_sha256'] == sha(text.encode()) and field.get('text_chars', len(text)) == len(text)
                assert field['chars_reviewed'] == (len(text) if reviewed else 0)
                assert field['bytes_reviewed'] == (len(text.encode()) if reviewed else 0)
                spans = field.get('spans', field.get('selected_spans', [])); counts['explicit_field_decisions'] += 1
            else:
                spans = []; counts['implicit_unread_fields'] += 1
            assert not spans or reviewed
            assert version['source']['manual_review']['field_reviewed'] is reviewed
            selected = ''.join(text[s['start']:s['end']] for s in spans)
            assert (version['text'] or '') == selected
            pieces = []
            for span in spans:
                a, b = span['start'], span['end']
                assert 0 <= a < b <= len(text) and span['sha256'] == sha(text[a:b].encode())
                assert span['speaker'].strip() and span['report_type'].strip() and span['source_report_family_id'].strip()
                pieces.append((a, b, text[a:b]))
            for comment in version.get('comments', []):
                if 'source_span' not in comment: continue
                a, b = comment['source_span']; assert comment['scope'] == 'source_context_not_narration'
                assert comment['text'] == text[a:b] and comment['source_text_sha256'] == sha(text[a:b].encode())
                pieces.append((a, b, comment['text']))
            cursor = 0
            for a, b, part in sorted(pieces):
                assert a == cursor and a < b <= len(text) and part == text[a:b]; cursor = b
            assert cursor == len(text) and ''.join(part for _, _, part in sorted(pieces)) == text
            status = 'admitted' if spans else 'read_context' if reviewed else 'unread_context'
            for counter in (counts, packages[membership[oid]], languages[language]):
                counter[status] += 1; counter['partitions'] += 1
                if reviewed:
                    counter['read_fields'] += 1; counter['read_characters'] += len(text); counter['read_utf8_bytes'] += len(text.encode())
                if spans:
                    counter['selected_spans'] += len(spans); counter['selected_characters'] += len(selected)
                    counter['selected_utf8_bytes'] += len(selected.encode())
            if spans:
                parent_admitted[language] = selected
                for classification in version['source']['report_component_classifications']:
                    matching = [s for s in spans if s['component_id'] == classification['component_id']]
                    assert classification['spans'] == [[s['start'], s['end']] for s in matching]
                    assert all(classification['speaker_description'] == s['speaker'] and classification['report_type'] == s['report_type']
                               and classification['source_report_family_id'] == s['source_report_family_id'] for s in matching)
            if action == 'exclude': assert reviewed and not spans
            for key, value in prior.items():
                if key in ('text', 'scope', 'source', 'comments', 'quotation_status'): continue
                if key == 'script' and value != version[key]:
                    assert reviewed and field['observed_script'] == version[key] and field['source_script_note']
                    script_corrections.append({'id': oid, 'language': language, 'before': value, 'after': version[key]})
                else:
                    assert version.get(key) == value, (oid, language, key); metadata['language'] += leaves(value)
            for key, value in prior['source'].items():
                assert version['source'].get(key) == value, (oid, language, 'source', key); metadata['source'] += leaves(value)
            for index, comment in enumerate(prior.get('comments', [])):
                for key, value in comment.items():
                    assert version['comments'][index][key] == value; metadata['prior_comments'] += leaves(value)
            details.append({'language': language, 'source_text_sha256': sha(text.encode()), 'characters': len(text),
                'utf8_bytes': len(text.encode()), 'status': status, 'explicit_field_decision': field is not None,
                'selected_spans': spans, 'lossless_partition': True})
        if action == 'register':
            assert set(parent_admitted) == {'hi', 'ur'} and result['text'] == {'arabic': None, 'translation': parent_admitted['hi']}
        else: assert not parent_admitted and result['text'] == before['text']
        for counter in (counts, packages[membership[oid]], collections_count[saved['collection']]): counter[action] += 1
        checks.append({'id': oid, 'decision': action, 'source_record_sha256': decision['source_record_sha256'],
                       'review_path': decision_paths[oid], 'fields': details})
    native.finish()
    expected = {'register': 96, 'exclude': 4, 'read_fields': 212, 'admitted': 192, 'read_context': 20,
                'unread_context': 288, 'partitions': 500, 'read_characters': 91600, 'read_utf8_bytes': 194325}
    assert all(counts[key] == value for key, value in expected.items()), (dict(counts), expected)
    for name, e in package_expected.items():
        actual = packages[name]
        assert actual['register'] + actual['exclude'] == e['occurrences']
        assert all(actual[key] == value for key, value in e.items() if key != 'occurrences'), (name, dict(actual), e)
    assert languages['hi']['admitted'] == languages['ur']['admitted'] == 96
    assert languages['hi']['read_fields'] == languages['ur']['read_fields'] == 100
    assert all(languages[language]['read_fields'] == 4 and languages[language]['admitted'] == 0 for language in ('ar', 'en', 'ur-Latn'))
    old117 = {identity(row) for row in lines(WORK / 'phase13-successor-acquisition-monitor/next-review-cohort/held-source-records.jsonl')}
    old_counts = collections.Counter(prior_engine.decisions[oid][2] for oid in old117)
    assert old_counts == {'register': 112, 'exclude': 5}
    progress = preparation['saved5589_progress_counts']
    projection = {'fetched': progress['imported_count'], 'registered': progress['registered_hadith_count'] + old_counts['register'] + counts['register'],
                  'source_only': progress['non_narration_source_entries'] + old_counts['exclude'] + counts['exclude'],
                  'held': progress['classification_pending_count'] - len(old117) - len(sources),
                  'unfetched': progress['pending_fetch_count']}
    assert projection == {'fetched': 16169, 'registered': 16014, 'source_only': 155, 'held': 0, 'unfetched': 20221}
    for spec in specs:
        checked_delivery(spec['manifest_path'], spec['manifest_sha256'])
        checked_delivery(spec['independent_audit_manifest_path'], spec['independent_audit_manifest_sha256'])
    assert config_path.read_bytes() == config_bytes
    report = {'schema': 'hadith-bank-checkpoint5589-independent-integration-v1', 'result': 'PASS',
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_commit': COMMIT, 'published_review_baseline_commit': PUBLISHED, 'source_count': 100,
        'source_cohort_sha256': COHORT_SHA, 'preparation_receipt': bind(preparation_path),
        'source_files_verified': 200, 'full_raw_reparses_bound': 100, 'prior15672_absence_and_old117_disjoint': True,
        'published_manual_ledgers': 29, 'published_manual_ids': 3218, 'new_active_ledgers': 4,
        'native_combined_loader_ledgers': 33, 'native_combined_loader_ids': 3318, 'id_collisions': [],
        'all_prior_decisions_unchanged_in_combined_loader': True,
        'combined_loader_scope': 'Native constructor collision/dependency validation of all33 ledgers; complete apply/finish only for the independently approved new100. Prior3218 are not newly reviewed here.',
        'native_new100_apply_finish': 'PASS', 'counts': dict(counts), 'metadata_leaf_equalities': dict(metadata),
        'metadata_leaf_equalities_total': sum(metadata.values()), 'by_package': {k: dict(v) for k, v in packages.items()},
        'by_language': {k: dict(v) for k, v in languages.items()}, 'by_collection': {k: dict(v) for k, v in collections_count.items()},
        'script_corrections': script_corrections, 'primary_package_receipts': package_receipts,
        'independent_complete_reading_audit_receipts': independent_receipts,
        'old117_published_dispositions': dict(old_counts), 'fixed5589_projection_after_published117_and_new100': projection,
        'projection_is_newly_saved_export': False, 'complete5589_state_history_preservation_claimed': False,
        'full_current_state_limit': preparation['complete5589_prior_imports_and_error_retry_history_comparison'],
        'new_linguistic_readings_by_integration': 0, 'new_semantic_decisions_by_integration': 0,
        'source_http_requests': 0, 'github_writes': 0, 'independent_pro_qc': 'not_performed',
        'parser_sha256': sha(Path(importer.__file__).read_bytes()), 'review_engine_sha256': native.engine_sha256,
        'limitations': 'Exact new100 and hash-bound independent semantic audits only. Source authority is the bounded5589 artifact plus exact progress and complete prior0639 state. No complete5589 state/error/retry-history preservation, latest remote checkpoint, regenerated export or live deployment is certified.'}
    prefix = Path('reports/web-source-resolution-20261113/checkpoint5589-independent-integration')
    outputs = {'validation-report.json': enc(report),
               'per-occurrence-field-partitions.json.gz': gzip.compress(enc({'records': checks}), mtime=0),
               'prepared-source-and-published-baseline.json': preparation_path.read_bytes(),
               'new100-raw-parsed-source-proof.json.gz': (ROOT / 'new100-raw-parsed-source-proof.json.gz').read_bytes(),
               'input-manifests.json': config_bytes, 'audit_final_packages.py': Path(__file__).read_bytes(),
               'prepare_source_and_published_baseline.py': (ROOT / 'prepare_source_and_published_baseline.py').read_bytes()}
    files = []
    for name, data in outputs.items():
        relative = prefix / name; path = ROOT / 'publish' / relative; immutable(path, data)
        files.append({'path': relative.as_posix(), 'local_path': str(path), **bind(path)})
    manifest = {'schema': 'hadith-bank-independent-integration-delivery-v1', 'result': 'PASS', 'source_commit': COMMIT,
        'published_review_baseline_commit': PUBLISHED, 'files': files, 'counts': dict(counts),
        'total_files': len(files), 'total_bytes': sum(item['bytes'] for item in files)}
    immutable(ROOT / 'delivery-manifest.json', enc(manifest))
    print(json.dumps({'result': 'PASS', 'counts': dict(counts), 'metadata_leaf_equalities': sum(metadata.values()),
        'manifest_sha256': sha(enc(manifest)), 'report_sha256': sha(enc(report)),
        'files': len(files), 'bytes': manifest['total_bytes']}, indent=2))


if __name__ == '__main__':
    main()
