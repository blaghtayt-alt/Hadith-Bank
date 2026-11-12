"""Regression checks for the recovered Uzbek importer.

Fixtures below are synthetic parser tokens, not hadith texts or translations.
These tests never download or reconstruct publisher content.
"""
import copy
import gzip
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_uzbek_web as web
import material_registry


class UzbekWebImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.importer = web.Importer(self.root, 'rivoyat', 5, 1)
        self.collection = {'key': 'fixture', 'title': 'Synthetic fixture',
                           'url': 'https://rivoyat.com/fixture',
                           'advertised_count': 1}
        self.importer.state['collections']['fixture'] = self.collection
        self.snapshot = {'path': 'synthetic-fixture.html.gz', 'sha256': '0' * 64}

    def publication_manifest(self, slug='synthetic-material'):
        folder = self.root / 'materials' / slug
        folder.mkdir(parents=True, exist_ok=True)
        source = folder / 'source-evidence.txt'
        source.write_bytes(b'SYNTHETIC SOURCE EVIDENCE')
        return {'schema': 'hadith-bank-material-v1', 'id': slug,
                'adapter': 'records-v1', 'language': 'uz', 'book': 'fixture',
                'edition': 'publisher-web-20261112', 'source_id': slug,
                'source': {'path': str(source.relative_to(self.root)),
                           'sha256': web.sha(source.read_bytes()),
                           'name': 'SYNTHETIC SOURCE', 'format': 'txt', 'url': None},
                'publication': {'authorized': True,
                                'decision': 'owner_requested_public_source_import',
                                'decision_date_japan': '2026-11-12'},
                'extraction_scope': {}}

    def record(self):
        row = web.base_record(
            'rivoyat', self.collection, '1/1',
            'https://rivoyat.com/fixture/1/1',
            {'ar': 'TEST_AR', 'uz-Latn': 'TEST_LATIN', 'uz-Cyrl': 'TEST_CYRILLIC'},
            {language: [] for language in ('ar', 'uz-Latn', 'uz-Cyrl')},
            self.snapshot, 'Synthetic fixture 1', '1')
        row['content_kind'] = 'prophetic_report'
        row['review']['status'] = 'digital_source_import'
        return row

    def test_adjacent_script_spans_do_not_hide_collection(self):
        tree = web.Tree(
            '<a href="/fixture"><span class="lat">Synthetic</span>'
            '<span class="kir">TEST</span><span>7 hadis · 1 kitob</span>'
            '<span class="kir">TEST</span></a>').root
        fresh = web.Importer(self.root / 'catalogue', 'rivoyat', 5, 1)
        fresh.catalogue(tree, self.snapshot)
        self.assertEqual(fresh.state['collections']['fixture']['advertised_count'], 7)
        self.assertTrue(any(t['url'] == 'https://rivoyat.com/fixture'
                            for t in fresh.state['tasks']))

    def test_empty_catalogue_and_section_fail_explicitly(self):
        fresh = web.Importer(self.root / 'empty', 'rivoyat', 5, 1)
        with self.assertRaisesRegex(ValueError, 'No recognizable publisher collections'):
            fresh.catalogue(web.Tree('<main>TEST</main>').root, self.snapshot)
        task = {'collection': 'fixture', 'url': 'https://rivoyat.com/fixture/1'}
        with self.assertRaisesRegex(ValueError, 'No recognizable numbered Rivoyat'):
            self.importer.rivoyat_records(web.Tree('<main>TEST</main>').root,
                                         '', task, self.snapshot)

    def test_copy_payload_is_exact_and_unresolved_flight_is_rejected(self):
        part = {'arabic': 'TEST_AR', 'latin': 'TEST_LATIN',
                'cyrillic': 'TEST_CYRILLIC',
                'url': 'https://rivoyat.com/fixture/1/1',
                'reference': 'TEST_REFERENCE'}
        flight = '1:' + json.dumps(['$', 'div', None, {'parts': part}]) + '\n'
        source = '<script>self.__next_f.push(' + json.dumps([1, flight]) + ')</script>'
        self.assertEqual(web.rivoyat_payloads(source)[part['url']], part)
        part['arabic'] = '$1b'
        flight = '1:' + json.dumps(['$', 'div', None, {'parts': part}]) + '\n'
        source = '<script>self.__next_f.push(' + json.dumps([1, flight]) + ')</script>'
        self.assertEqual(web.rivoyat_payloads(source), {})

    def test_cyrillic_only_changes_have_distinct_held_occurrences(self):
        original = self.record()
        self.importer.add_record(copy.deepcopy(original))
        for marker in ('_VARIANT_A', '_VARIANT_B'):
            row = copy.deepcopy(original)
            next(v for v in row['language_versions']
                 if v['language'] == 'uz-Cyrl')['text'] += marker
            self.importer.add_record(row)
        self.assertEqual(len(self.importer.records), 3)
        candidates = [r for r in self.importer.records.values()
                      if ':version-' in r['id']]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len({r['id'] for r in candidates}), 2)
        # Even a later positive attribution result must not promote a changed
        # source candidate automatically.
        with patch.object(web, 'classify', return_value=('prophetic_report', {})):
            self.importer.enrich_local_metadata()
        for row in candidates:
            self.assertEqual(row['content_kind'], 'unknown')
            self.assertEqual(row['review']['status'], 'source_variant_pending_hidden')
            self.assertTrue(all(v['id'].startswith(row['id'] + ':')
                                for v in row['language_versions']))

    def test_duplicate_source_occurrence_does_not_inflate_count(self):
        row = self.record()
        self.importer.add_record(copy.deepcopy(row))
        self.importer.add_record(copy.deepcopy(row))
        self.assertEqual(len(self.importer.records), 1)

    def test_explicit_commentary_is_kept_in_own_language(self):
        importer = web.Importer(self.root / 'comments', 'islom', 5, 1)
        importer.state['collections']['fixture'] = self.collection
        row = self.record()
        row['separated_commentary'] = {'ar': None, 'uz-Cyrl': 'TEST_COMMENTARY'}
        importer.records[row['id']] = row
        importer.enrich_local_metadata()
        version = next(v for v in row['language_versions'] if v['language'] == 'uz-Cyrl')
        self.assertEqual(version['comments'][0]['text'], 'TEST_COMMENTARY')
        self.assertEqual(version['comments'][0]['source_url'], row['source']['record_url'])
        self.assertEqual(version['comments'][0]['kind'], 'source_commentary')
        self.assertEqual(row['text']['translation'], 'TEST_LATIN')
        body, comment, basis = web.split_islom_text('TEST_BODY\nШарҳ: TEST_COMMENT')
        self.assertEqual((body, comment, basis),
                         ('TEST_BODY', 'Шарҳ: TEST_COMMENT', 'explicit_commentary_heading'))

    def test_citation_rule_requires_declared_scope_and_nonempty_matn(self):
        token = 'TEST_BOUNDED_MATN رواه TEST_SOURCE'
        self.assertEqual(web.classify(token, '')[0], 'unknown')
        declared = {'bounded_matn_declaration': {'title_as_supplied': 'TEST_ANTHOLOGY'}}
        self.assertEqual(web.classify(token, '', declared)[0], 'prophetic_report')
        self.assertEqual(web.classify('TEST_UNCITED_TEXT', '', declared)[0], 'unknown')
        self.assertEqual(web.classify('رواه TEST_SOURCE', '', declared)[0], 'unknown')

    def test_robots_and_time_budget_stop_before_network(self):
        robot = web.urllib.robotparser.RobotFileParser()
        robot.parse(['User-agent: *', 'Disallow: /api/'])
        self.importer.robot = robot
        with patch.object(web.urllib.request, 'urlopen') as network:
            with self.assertRaisesRegex(RuntimeError, 'robots_disallowed'):
                self.importer.request('https://rivoyat.com/api/fixture')
            self.importer.deadline = 0
            with self.assertRaises(StopIteration):
                self.importer.request('https://rivoyat.com/fixture')
            network.assert_not_called()

    def test_robots_startup_access_block_is_saved_and_not_retried(self):
        for code in (401, 403, 429):
            with self.subTest(http_status=code):
                root = self.root / ('robots-block-' + str(code))
                importer = web.Importer(root, 'rivoyat', 5, 1)
                url = 'https://rivoyat.com/robots.txt'
                error = web.urllib.error.HTTPError(url, code, 'TEST access block', {}, None)
                with patch.object(web.urllib.request, 'urlopen', side_effect=error) as network:
                    report = importer.run()
                self.assertEqual(network.call_count, 1)
                self.assertTrue(report['blocked'])
                self.assertEqual(report['source_entries_obtained'], 0)
                self.assertFalse(report['all_linked_pages_processed'])
                state = json.loads(importer.state_path.read_text())
                robots_task = next(task for task in state['tasks'] if task['kind'] == 'robots')
                self.assertEqual(robots_task['status'], 'blocked')
                self.assertTrue(all(task.get('attempts', 0) == 0 for task in state['tasks'] if task['kind'] != 'robots'))
                self.assertEqual(state['site_access_block']['url'], url)
                self.assertEqual(state['site_access_block']['status'], code)
                self.assertEqual(state['events'][-1], state['site_access_block'])
                saved_block = copy.deepcopy(state['site_access_block'])
                resumed = web.Importer(root, 'rivoyat', 5, 1)
                with patch.object(web.urllib.request, 'urlopen') as network, \
                        patch.object(resumed, 'robots') as robots:
                    report = resumed.run()
                network.assert_not_called()
                robots.assert_not_called()
                self.assertTrue(report['blocked'])
                self.assertFalse(report['all_linked_pages_processed'])
                self.assertEqual(resumed.state['site_access_block'], saved_block)

    def test_legacy_access_block_is_honored_by_run_and_direct_request(self):
        block = {'url': 'https://rivoyat.com/robots.txt', 'http_status': 403,
                 'phase': 'robots', 'automatic_retry_allowed': False}
        self.importer.state['access_block'] = block
        with patch.object(web.urllib.request, 'urlopen') as network:
            report = self.importer.run()
            with self.assertRaisesRegex(RuntimeError, 'prior_source_access_block'):
                self.importer.request('https://rivoyat.com/fixture')
        network.assert_not_called()
        self.assertTrue(report['blocked'])
        self.assertFalse(report['all_linked_pages_processed'])
        self.assertEqual(report['access_block'], block)
        self.assertEqual(self.importer.state['access_block'], block)

    def test_owner_withdrawal_prevents_acquisition_and_offline_registration(self):
        root = self.root / 'withdrawn'
        path = root / 'catalog/web-import-plan.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'sources': {'rivoyat': {'enabled': False, 'excluded_by_owner': True}}}))
        with patch.object(web.urllib.request, 'urlopen') as network:
            with self.assertRaisesRegex(ValueError, 'Source excluded by owner'):
                web.Importer(root, 'rivoyat', 5, 1)
        network.assert_not_called()
        self.assertFalse((root / 'materials').exists())
        self.assertFalse((root / web.BASE / 'rivoyat').exists())

    def test_existing_task_block_is_checked_before_robots(self):
        self.importer.state['tasks'] = [{'url': 'https://rivoyat.com/fixture',
                                        'kind': 'home', 'status': 'blocked'}]
        with patch.object(self.importer, 'robots') as robots, \
                patch.object(web.urllib.request, 'urlopen') as network:
            report = self.importer.run()
        robots.assert_not_called()
        network.assert_not_called()
        self.assertTrue(report['blocked'])
        self.assertFalse(report['all_linked_pages_processed'])

    def test_robots_server_error_is_not_falsely_labelled_access_block(self):
        url = 'https://rivoyat.com/robots.txt'
        error = web.urllib.error.HTTPError(url, 500, 'TEST server error', {}, None)
        with patch.object(web.urllib.request, 'urlopen', side_effect=error):
            report = self.importer.run()
        self.assertFalse(report['blocked'])
        self.assertEqual(report['errors'], 1)
        self.assertNotIn('access_block', self.importer.state)
        self.assertNotIn('site_access_block', self.importer.state)

    def test_cached_http_bytes_are_verified_before_reuse(self):
        raw = b'<html>SYNTHETIC_SOURCE_BYTES</html>'
        path = self.root / 'snapshot.html.gz'
        path.write_bytes(gzip.compress(raw, mtime=0))
        url = 'https://rivoyat.com/fixture/1'
        self.importer.state['snapshots'][url] = {
            'path': 'snapshot.html.gz', 'sha256': web.sha(raw)}
        with patch.object(web.urllib.request, 'urlopen') as network:
            text, _ = self.importer.fetch({'url': url})
            self.assertEqual(text.encode(), raw)
            network.assert_not_called()
        self.importer.state['snapshots'][url]['sha256'] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'checksum_mismatch'):
            self.importer.fetch({'url': url})

    def test_publication_partition_assignments_remain_stable(self):
        row = self.record()
        manifest = self.publication_manifest()
        self.importer.write_material_parts('synthetic-material', manifest, [row])
        original_part = self.importer.state['material_partitions']['synthetic-material'][row['id']]
        another = copy.deepcopy(row)
        another['id'] = 'a-new-source-occurrence'
        self.importer.write_material_parts('synthetic-material', manifest, [another, row])
        self.assertEqual(
            self.importer.state['material_partitions']['synthetic-material'][row['id']],
            original_part)
        published = json.loads((self.root / 'materials/synthetic-material/manifest.json').read_text())
        data = (self.root / published['records']['path']).read_bytes()
        self.assertEqual(published['records']['count'], 2)
        self.assertEqual(published['records']['sha256'], web.sha(data))

    def test_small_cap_parts_pass_real_registry_validation(self):
        row = self.record()
        other = copy.deepcopy(row)
        other['id'] = 'fixture:second'
        other['number']['source_entry_id'] = '1/2'
        other['number']['in_book'] = '2'
        other['source']['record_url'] = 'https://rivoyat.com/fixture/1/2'
        for version in other['language_versions']:
            version['id'] = other['id'] + ':' + version['language']
            version['source']['record_url'] = other['source']['record_url']
        for fixture in (row, other):
            fixture.pop('source_locator', None)
            fixture['extraction'].pop('source_snapshot', None)
            for version in fixture['language_versions']:
                version['source'].pop('snapshot_path', None)
                version['source'].pop('snapshot_sha256', None)
        manifest = self.publication_manifest()
        cap = max(len(web.json_bytes(r)) for r in (row, other)) + 256
        with patch.object(web, 'PUBLICATION_PART_BYTES', cap):
            self.importer.write_material_parts('synthetic-material', manifest, [row, other])
        registry = material_registry.load_public_materials(self.root, validate_attachment_roots=False)
        self.assertEqual(len(registry['materials']), 2)
        projected = [r for group in registry['groups'] for r in group]
        self.assertEqual({r['id'] for r in projected}, {row['id'], other['id']})
        self.assertEqual(len({r['id'] for r in projected}), 2)
        self.assertEqual(len({m['edition'] for m in registry['materials']}), 2)
        for registered in registry['materials']:
            folder = self.root / Path(registered['manifest_path']).parent
            self.assertEqual((self.root / registered['source_file']).parent, folder)
            self.assertEqual((self.root / registered['source_file']).read_bytes(), b'SYNTHETIC SOURCE EVIDENCE')
        original = copy.deepcopy(self.importer.state['material_partitions'])
        with patch.object(web, 'PUBLICATION_PART_BYTES', cap):
            self.importer.write_material_parts('synthetic-material', manifest, [other, row])
        self.assertEqual(self.importer.state['material_partitions'], original)
        self.assertEqual(len(material_registry.load_public_materials(self.root)['materials']), 2)

    def test_rivoyat_detail_metadata_is_queued_and_explicitly_pending(self):
        row = self.record()
        self.importer.records[row['id']] = row
        self.importer.prepare_detail_metadata_queue()
        self.importer.prepare_detail_metadata_queue()
        tasks = self.importer.state['detail_metadata_tasks']
        self.assertEqual(len(tasks), 1)
        task = tasks[row['id']]
        self.assertEqual(task['status'], 'pending')
        self.assertEqual(task['record_url'], row['source']['record_url'])
        self.assertEqual(task['expected_language_text_sha256']['uz-Cyrl'], web.sha(b'TEST_CYRILLIC'))
        self.assertEqual(row['detail_metadata_status'], 'detail_metadata_pending')
        self.assertTrue(all(v['comments_status'] == 'detail_metadata_pending'
                            for v in row['language_versions']))
        saved = json.loads((self.importer.folder / 'detail-metadata-queue.json').read_text())
        self.assertFalse(saved['section_import_fetches_detail_pages'])
        self.assertEqual(saved['task_counts'], {'pending': 1})

    def detail_fixture(self, row=None):
        row = row or self.record()
        values = {v['language']: v['text'] for v in row['language_versions']}
        part = {'url': row['source']['record_url'], 'arabic': values['ar'],
                'latin': values['uz-Latn'], 'cyrillic': values['uz-Cyrl']}
        flight = '1:' + json.dumps(['$', 'div', None, {'parts': part}]) + '\n'
        return ('<main><section class="panel"><article class="h-card">TEST_BODY</article>'
                '<div class="hukm"><ol class="hk-list"><li class="is-main">'
                '<div class="hk-top"><span class="chip" title="حكم">'
                '<span class="lat">GRADE_LAT</span><span class="kir">GRADE_CYR</span></span>'
                '<span class="hk-who"><span title="اسم"><span class="lat">WHO_LAT</span>'
                '<span class="kir">WHO_CYR</span></span></span></div>'
                '<div class="hk-src"><span title="كتاب"><span class="lat">BOOK_LAT</span>'
                '<span class="kir">BOOK_CYR</span></span>, 12/3</div>'
                '<div class="hk-tx"><span class="lat">NOTE_LAT</span>'
                '<span class="kir">NOTE_CYR</span></div>'
                '<div class="hk-tx"><bdi class="hk-ar" lang="ar">نص</bdi></div>'
                '</li></ol><ul class="mb-list"><li><span title="مصدر">'
                '<span class="lat">OTHER_LAT</span><span class="kir">OTHER_CYR</span>'
                '</span><span class="mb-loc">12a</span></li>'
                '<li><span></span><span class="mb-loc">505</span></li></ul></div>'
                '<div class="rows"><a href="/other/1/9">UNRELATED_SUGGESTION</a></div>'
                '</section></main><script>self.__next_f.push(' + json.dumps([1, flight]) + ')</script>')

    def cache_detail_fixture(self, row=None):
        row = row or self.record()
        source = self.detail_fixture(row)
        body = source.encode()
        path = self.root / web.BASE / 'rivoyat' / 'snapshots' / ('detail-fixture-' + web.sha(row['source']['record_url'].encode())[:8] + '.html.gz')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(body, mtime=0))
        snapshot = {'path': str(path.relative_to(self.root)), 'sha256': web.sha(body),
                    'stored_sha256': web.sha(path.read_bytes()), 'bytes': len(body),
                    'url': row['source']['record_url'], 'final_url': row['source']['record_url']}
        return row, source, snapshot

    def test_detail_keeps_script_specific_citations_grades_and_comments(self):
        row, source, snapshot = self.cache_detail_fixture()
        result = web.rivoyat_detail_metadata(source, row, snapshot)
        self.assertEqual(result['grading_rows'], 1)
        self.assertEqual(result['listed_source_rows'], 2)
        latin = result['languages']['uz-Latn']
        cyrillic = result['languages']['uz-Cyrl']
        arabic = result['languages']['ar']
        self.assertEqual(latin['grading_details'][0]['grader'], 'WHO_LAT')
        self.assertEqual(arabic['grading_details'][0]['grader'], 'اسم')
        self.assertEqual(latin['references'][0]['source_citation'], 'BOOK_LAT, 12/3')
        self.assertEqual(cyrillic['references'][0]['source_citation'], 'BOOK_CYR, 12/3')
        self.assertEqual(arabic['references'][0]['source_citation'], 'كتاب, 12/3')
        self.assertEqual(latin['references'][1]['source_locator_text'], '12a')
        self.assertIsNone(latin['references'][1]['number'])
        self.assertIsNone(latin['references'][2]['collection'])
        self.assertEqual([c['text'] for c in latin['comments']], ['GRADE_LAT', 'NOTE_LAT'])
        self.assertEqual([c['text'] for c in cyrillic['comments']], ['GRADE_CYR', 'NOTE_CYR'])
        self.assertEqual([c['text'] for c in arabic['comments']], ['حكم', 'نص'])
        self.assertNotIn('UNRELATED_SUGGESTION', json.dumps(result))
        self.assertTrue(all(not r['translation_source_verified'] for r in latin['references']))

    def test_detail_identity_requires_exact_url_and_every_source_language(self):
        row, source, snapshot = self.cache_detail_fixture()
        changed = copy.deepcopy(row)
        next(v for v in changed['language_versions'] if v['language'] == 'uz-Cyrl')['text'] += '_CHANGED'
        with self.assertRaisesRegex(ValueError, 'detail_source_text_mismatch'):
            web.rivoyat_detail_metadata(source, changed, snapshot)
        with self.assertRaisesRegex(ValueError, 'detail_source_identity_mismatch'):
            web.rivoyat_detail_metadata(source, row, {**snapshot, 'final_url': 'https://rivoyat.com/other'})
        with self.assertRaisesRegex(ValueError, 'detail_source_identity_unresolved'):
            web.rivoyat_detail_metadata('<main><article class="h-card">TEST</article></main>', row, snapshot)

    def test_cached_detail_enrichment_preserves_text_and_is_idempotent_during_access_block(self):
        row, source, snapshot = self.cache_detail_fixture()
        before_text = copy.deepcopy(row['text'])
        before_versions = [(v['id'], v['text']) for v in row['language_versions']]
        self.importer.records[row['id']] = row
        self.importer.state['snapshots'][row['source']['record_url']] = snapshot
        self.importer.state['site_access_block'] = {'url': 'https://rivoyat.com/robots.txt', 'status': 403}
        self.importer.prepare_detail_metadata_queue()
        with patch.object(web.urllib.request, 'urlopen') as network:
            self.importer.enrich_cached_details()
            self.importer.prepare_detail_metadata_queue()
            once = copy.deepcopy(row)
            self.importer.enrich_cached_details()
            self.importer.prepare_detail_metadata_queue()
            network.assert_not_called()
        self.assertEqual(row, once)
        self.assertEqual(row['text'], before_text)
        self.assertEqual([(v['id'], v['text']) for v in row['language_versions']], before_versions)
        self.assertEqual(row['detail_metadata_status'], 'detail_metadata_source_parsed')
        self.assertEqual(self.importer.state['detail_metadata_counts'], {'done': 1})
        self.assertEqual(self.importer.state['site_access_block']['status'], 403)
        self.assertTrue(all(v['source']['upstream_sources'] == [] for v in row['language_versions']))

    def test_detail_mismatch_retains_prior_record_and_requires_review(self):
        row, source, snapshot = self.cache_detail_fixture()
        next(v for v in row['language_versions'] if v['language'] == 'ar')['text'] += '_CHANGED'
        self.importer.records[row['id']] = row
        self.importer.state['snapshots'][row['source']['record_url']] = snapshot
        self.importer.prepare_detail_metadata_queue()
        before = copy.deepcopy(row)
        self.importer.enrich_cached_details()
        task = self.importer.state['detail_metadata_tasks'][row['id']]
        self.assertEqual(task['status'], 'failed')
        self.assertEqual(task['attempts'], 3)
        self.assertIn('detail_source_text_mismatch', task['error'])
        self.assertEqual(row, before)

    def test_robots_http_denial_is_preserved_and_blocks_subsequent_network(self):
        importer = web.Importer(self.root / 'blocked', 'rivoyat', 5, 1)
        body = b'SYNTHETIC_ACCESS_DENIAL'
        error = web.urllib.error.HTTPError('https://rivoyat.com/robots.txt', 403,
                                          'Forbidden', {}, io.BytesIO(body))
        with patch.object(web.urllib.request, 'urlopen', side_effect=error) as network:
            first = importer.run()
            self.assertEqual(network.call_count, 1)
        self.assertTrue(first['blocked'])
        block = importer.state['site_access_block']
        self.assertEqual(block['status'], 403)
        self.assertEqual(gzip.decompress((importer.root / block['path']).read_bytes()), body)
        self.assertEqual(block['sha256'], web.sha(body))
        restored = web.Importer(importer.root, 'rivoyat', 5, 1)
        with patch.object(web.urllib.request, 'urlopen') as network:
            second = restored.run()
            network.assert_not_called()
        self.assertTrue(second['blocked'])
        self.assertEqual(second['prophetic_source_entries_registered'], 0)

    def test_transient_robots_error_is_not_mislabelled_as_access_denial(self):
        importer = web.Importer(self.root / 'transient', 'rivoyat', 5, 1)
        error = web.urllib.error.HTTPError('https://rivoyat.com/robots.txt', 503,
                                          'Unavailable', {}, io.BytesIO(b'TEST_TEMPORARY_ERROR'))
        with patch.object(web.urllib.request, 'urlopen', side_effect=error):
            report = importer.run()
        self.assertFalse(report['blocked'])
        self.assertEqual(report['errors'], 1)
        self.assertNotIn('site_access_block', importer.state)
        robots_task = next(t for t in importer.state['tasks'] if t['kind'] == 'robots')
        self.assertEqual(robots_task['status'], 'failed')
        self.assertEqual(robots_task['attempts'], 1)

    def test_export_preserves_detail_snapshot_dependencies_and_access_stop(self):
        section_body = b'<main>SYNTHETIC_SECTION</main>'
        section_path = self.root / web.BASE / 'rivoyat' / 'snapshots' / 'synthetic-fixture.html.gz'
        section_path.parent.mkdir(parents=True, exist_ok=True)
        section_path.write_bytes(gzip.compress(section_body, mtime=0))
        self.snapshot.update({'url': 'https://rivoyat.com/fixture/1',
                              'path': str(section_path.relative_to(self.root)),
                              'sha256': web.sha(section_body),
                              'stored_sha256': web.sha(section_path.read_bytes())})
        row, source, snapshot = self.cache_detail_fixture()
        self.importer.records[row['id']] = row
        self.importer.state['snapshots'] = {self.snapshot['url']: self.snapshot,
                                           row['source']['record_url']: snapshot}
        self.importer.state['tasks'] = [{'url': self.snapshot['url'], 'kind': 'section',
                                         'collection': 'fixture', 'status': 'done'}]
        self.importer.state['site_access_block'] = {'url': 'https://rivoyat.com/robots.txt', 'status': 403}
        with patch.object(web.urllib.request, 'urlopen') as network:
            report = self.importer.export()
            network.assert_not_called()
        self.assertTrue(report['blocked'])
        self.assertEqual(report['detail_metadata_counts'], {'done': 1})
        manifest = json.loads((self.root / 'materials/rivoyat-fixture-uz-web/manifest.json').read_text())
        self.assertIn(snapshot['path'], {item['path'] for item in manifest['supporting_files']})
        registry = material_registry.load_public_materials(self.root, validate_attachment_roots=False)
        self.assertEqual(sum(len(group) for group in registry['groups']), 1)
        restored = web.Importer(self.root, 'rivoyat', 5, 1)
        self.assertEqual(restored.state['detail_metadata_tasks'][row['id']]['status'], 'done')
        self.assertEqual(restored.state['site_access_block']['status'], 403)

    def test_detail_budget_saves_completed_work_and_resumes_remaining_task(self):
        first = self.record()
        second = copy.deepcopy(first)
        second['id'] = 'rivoyat:fixture:1/2'
        second['source']['record_url'] = 'https://rivoyat.com/fixture/1/2'
        for version in second['language_versions']:
            version['id'] = second['id'] + ':' + version['language']
        responses = {}
        for row in (first, second):
            _, source, snapshot = self.cache_detail_fixture(row)
            responses[row['source']['record_url']] = source, snapshot
            self.importer.records[row['id']] = row
        self.importer.state['tasks'] = [{'url': 'https://rivoyat.com/', 'kind': 'home',
                                         'collection': None, 'status': 'done'}]

        def bounded_fetch(task):
            if self.importer.requests >= 1:
                raise StopIteration('request_budget')
            self.importer.requests += 1
            source, snapshot = responses[task['url']]
            self.importer.state['snapshots'][task['url']] = snapshot
            return source, snapshot

        with patch.object(self.importer, 'robots'), patch.object(self.importer, 'fetch', side_effect=bounded_fetch):
            report = self.importer.run()
        self.assertEqual(report['detail_metadata_counts'], {'done': 1, 'pending': 1})
        self.assertEqual(self.importer.state['last_stop_reason'], 'request_budget')
        restored = web.Importer(self.root, 'rivoyat', 5, 1)

        def remaining_fetch(task):
            source, snapshot = responses[task['url']]
            restored.state['snapshots'][task['url']] = snapshot
            return source, snapshot

        with patch.object(restored, 'robots'), patch.object(restored, 'fetch', side_effect=remaining_fetch) as fetch:
            resumed = restored.run()
            self.assertEqual(fetch.call_count, 1)
        self.assertEqual(resumed['detail_metadata_counts'], {'done': 2})
        self.assertEqual(len(restored.records), 2)


if __name__ == '__main__':
    unittest.main()
