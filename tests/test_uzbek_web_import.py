"""Regression checks for the recovered Uzbek importer.

Fixtures below are synthetic parser tokens, not hadith texts or translations.
These tests never download or reconstruct publisher content.
"""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_uzbek_web as web


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
                self.assertEqual(state['tasks'], [])
                self.assertEqual(state['access_block']['url'], url)
                self.assertEqual(state['access_block']['http_status'], code)
                self.assertEqual(state['access_block']['phase'], 'robots')
                self.assertFalse(state['access_block']['automatic_retry_allowed'])
                self.assertEqual(state['events'][-1], state['access_block'])
                saved_block = copy.deepcopy(state['access_block'])
                resumed = web.Importer(root, 'rivoyat', 5, 1)
                with patch.object(web.urllib.request, 'urlopen') as network, \
                        patch.object(resumed, 'robots') as robots:
                    report = resumed.run()
                network.assert_not_called()
                robots.assert_not_called()
                self.assertTrue(report['blocked'])
                self.assertFalse(report['all_linked_pages_processed'])
                self.assertEqual(resumed.state['access_block'], saved_block)

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
            with self.assertRaises(web.urllib.error.HTTPError):
                self.importer.run()
        self.assertNotIn('access_block', self.importer.state)

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
        manifest = {'extraction_scope': {}}
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


if __name__ == '__main__':
    unittest.main()
