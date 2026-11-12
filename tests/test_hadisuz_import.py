"""Synthetic TEST fixtures exercise public link discovery and exact separation."""
import gzip
import html
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_hadisuz as importer
from material_registry import load_public_materials
from build_discovery import render_language_reading
from language_display import language_readings


def catalogue(next_page=False):
    next_link = '<ul class="pagination"><a rel="next" href="?page=2">TEST next</a></ul>' if next_page else ''
    return ('<h1>Сунани Термизий</h1><div class="col-md-9"><div class="panel-body">'
            '<p>TEST preview must never become a record.</p><a href="/hadith/615">TEST detail</a>'
            '</div>' + next_link + '</div><a href="/auth/login">TEST excluded</a>'
            '<a href="/hadiths/45">TEST unrelated source</a>').encode()


def detail(primary='TEST Расулуллоҳ attribution. TEST quoted narration.', notes='', tags=('i', 'b')):
    a, b = tags
    return ('<h1>TEST topic</h1><div class="col-md-9">'
            f'<p><{a}>TEST source chain.</{a}> <{b}>{primary}</{b}></p>' + notes +
            '<script src="/unused.js"></script><div class="ya-share2">TEST share</div>'
            '<hr><p class="text-center"><a href="/hadiths">TEST back</a></p></div>').encode()


class Response(io.BytesIO):
    status = 200
    headers = {'Content-Type': 'text/html; charset=utf-8'}

    def __init__(self, url, raw):
        super().__init__(raw)
        self.url = url

    def geturl(self):
        return self.url


class HadisuzImportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def worker(self, budget=20):
        worker = importer.Importer(self.root, max_pages=budget, max_seconds=30, delay=1)
        worker.delay = 0  # Synthetic in-process responses; no HTTP in these tests.
        return worker

    def responses(self, mapping, calls):
        def open_response(request, timeout=None):
            url = request.full_url
            calls.append(url)
            value = mapping[url]
            if isinstance(value, Exception):
                raise value
            return Response(url, value)
        return open_response

    def source_map(self, raw=None):
        return {importer.ORIGIN + '/robots.txt': b'User-agent: *\nDisallow: /auth\n',
                importer.CATALOG: catalogue(),
                importer.ORIGIN + '/hadith/615': raw or detail()}

    def run_source(self, mapping=None, budget=20):
        worker = self.worker(budget)
        calls = []
        with mock.patch.object(worker.opener, 'open', side_effect=self.responses(mapping or self.source_map(), calls)):
            report = worker.run()
        return worker, report, calls

    def test_catalogue_follows_only_observed_detail_and_same_collection_next(self):
        parsed = importer.parse_catalog(catalogue(True), importer.CATALOG)
        self.assertEqual(parsed['details'], [importer.ORIGIN + '/hadith/615'])
        self.assertEqual(parsed['next'], [importer.CATALOG + '?page=2'])
        self.assertTrue(parsed['previews_not_registered'])

    def test_primary_narration_excludes_later_scholarly_bold_and_quran_comments(self):
        notes = '<p>TEST source grade</p><p><i>TEST scholar</i><b>TEST Quran and commentary</b></p>'
        parsed = importer.parse_detail(detail(notes=notes), importer.ORIGIN + '/hadith/615')
        self.assertEqual(parsed['content_kind'], 'prophetic_report')
        self.assertEqual(len(parsed['comments']), 2)
        self.assertNotIn('TEST scholar', parsed['text'])
        self.assertNotIn('TEST Quran', parsed['text'])
        self.assertNotIn('TEST share', str(parsed))

    def test_em_strong_markup_is_supported_without_rewriting_source_words(self):
        parsed = importer.parse_detail(detail(tags=('em', 'strong')), importer.ORIGIN + '/hadith/1')
        self.assertEqual(parsed['content_kind'], 'prophetic_report')
        self.assertEqual(parsed['text'], 'TEST source chain. TEST Расулуллоҳ attribution. TEST quoted narration.')

    def test_incomplete_primary_and_unattributed_sayings_remain_held(self):
        for primary in ['TEST Расулуллоҳ incomplete context:', 'TEST independent scholarly statement.']:
            parsed = importer.parse_detail(detail(primary), importer.ORIGIN + '/hadith/615')
            self.assertEqual(parsed['content_kind'], 'classification_pending_hidden')

    def test_unrecognized_detail_structure_does_not_silently_publish_partial_body(self):
        raw = detail().replace(b'<p>', b'<section>TEST unseen content</section><p>', 1)
        parsed = importer.parse_detail(raw, importer.ORIGIN + '/hadith/615')
        self.assertIn('unrecognized_body_structure', parsed['classification']['issues'])

    def test_nonpublic_routes_ranges_and_foreign_hosts_are_rejected(self):
        for url in ['https://hadis.uz/auth/login', 'https://hadis.uz/backend',
                    'https://hadis.uz/profile', 'https://hadis.uz/hadiths/45',
                    'https://hadis.uz/hadiths/1?page=2&page=3',
                    'https://example.invalid/hadith/615', 'http://hadis.uz/hadith/615']:
            self.assertFalse(importer.allowed_url(url), url)

    def test_redirect_cannot_relabel_another_entry_or_visit_auth_route(self):
        redirect = importer.PublicRedirects()
        request = urllib.request.Request(importer.ORIGIN + '/hadith/615')
        for target in ['/hadith/614', '/auth/login', 'https://example.invalid/hadith/615']:
            with self.assertRaisesRegex(ValueError, 'source identity'):
                redirect.redirect_request(request, None, 302, 'TEST redirect', {}, target)

    def test_resume_reuses_saved_responses_and_registers_details_only(self):
        _, first, calls = self.run_source(budget=2)
        self.assertEqual(calls, [importer.ORIGIN + '/robots.txt', importer.CATALOG])
        self.assertEqual(first['source_entries_obtained'], 0)
        _, second, calls = self.run_source(budget=1)
        self.assertEqual(calls, [importer.ORIGIN + '/hadith/615'])
        self.assertEqual(second['prophetic_source_entries_registered'], 1)
        self.assertTrue(second['done'])
        data = json.loads((self.root / 'materials' / importer.SLUG / 'records.jsonl').read_text())
        self.assertEqual(data['number']['source_entry_id'], '615')
        self.assertIsNone(data['number']['canonical'])
        self.assertIsNone(data['number']['in_book'])
        self.assertIsNone(data['text']['arabic'])
        registry = load_public_materials(self.root)
        self.assertEqual(len(registry['manifests']), 1)

    def test_403_is_retained_and_never_automatically_retried(self):
        mapping = self.source_map()
        mapping[importer.ORIGIN + '/hadith/615'] = urllib.error.HTTPError(
            importer.ORIGIN + '/hadith/615', 403, 'TEST denial', {}, io.BytesIO(b'TEST denied'))
        _, report, _ = self.run_source(mapping)
        self.assertTrue(report['blocked'])
        worker = self.worker()
        with mock.patch.object(worker.opener, 'open') as request:
            again = worker.run()
        request.assert_not_called()
        self.assertFalse(again['done'])
        self.assertEqual(again['access_block']['status'], 403)

    def test_robots_denial_is_enforced_before_detail_request(self):
        mapping = self.source_map()
        mapping[importer.ORIGIN + '/robots.txt'] = b'User-agent: *\nDisallow: /hadith/\n'
        _, report, calls = self.run_source(mapping)
        self.assertTrue(report['blocked'])
        self.assertNotIn(importer.ORIGIN + '/hadith/615', calls)

    def test_transient_detail_error_retries_are_bounded_across_batches(self):
        def mapping():
            values = self.source_map()
            values[importer.ORIGIN + '/hadith/615'] = urllib.error.HTTPError(
                importer.ORIGIN + '/hadith/615', 500, 'TEST temporary failure', {}, io.BytesIO(b'TEST error'))
            return values
        for attempt in range(3):
            _, report, _ = self.run_source(mapping())
            self.assertFalse(report['done'])
        _, report, calls = self.run_source(mapping())
        self.assertEqual(calls, [])
        self.assertEqual(report['retryable_errors'], 0)
        self.assertEqual(report['errors'], 1)

    def test_corrupt_original_snapshot_blocks_offline_export(self):
        worker, _, _ = self.run_source()
        path = self.root / worker.state['snapshots'][importer.ORIGIN + '/hadith/615']['path']
        path.write_bytes(b'TEST corrupted bytes')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            worker.export()

    def test_exhausted_robots_startup_retries_stop_without_false_completion(self):
        for _ in range(3):
            mapping = self.source_map()
            mapping[importer.ORIGIN + '/robots.txt'] = urllib.error.HTTPError(
                importer.ORIGIN + '/robots.txt', 500, 'TEST startup failure', {}, io.BytesIO(b'TEST error'))
            self.run_source(mapping)
        worker = self.worker()
        with mock.patch.object(worker.opener, 'open') as request:
            report = worker.run()
        request.assert_not_called()
        self.assertTrue(report['startup_stopped'])
        self.assertFalse(report['done'])
        self.assertEqual(report['errors'], 1)

    def test_offline_reexport_is_deterministic_and_keeps_notes_per_language(self):
        raw = detail(notes='<p>Бу ҳадис ҳасан-саҳиҳ.</p><p>TEST Муслим parallel source.</p>')
        worker, _, _ = self.run_source(self.source_map(raw))
        directory = self.root / 'materials' / importer.SLUG
        before = {p.name: p.read_bytes() for p in directory.iterdir()}
        worker.export()
        self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})
        row = json.loads((directory / 'records.jsonl').read_text())
        self.assertEqual(len(row['language_versions'][0]['comments']), 2)
        self.assertEqual(row['language_versions'][0]['references'][1]['scope'], 'source_commentary_citation')
        self.assertIsNone(row['grading']['grader'])
        self.assertNotIn('ҳасан-саҳиҳ', row['text']['translation'])

    def test_saved_collection_credits_render_in_own_language_without_changing_narration(self):
        url = importer.ORIGIN + '/page/about-project'
        translator_credit = ('Ҳадислар учун манба сифатида TEST collection translation. '
                             'Таржимон TEST Мирзо Кенжабек ("Адолат" 1999).')
        electronic_credit = 'Камина шу китобларни TEST www.ziyouz.com электрон нусҳасидан фойдаланди.'
        raw = ('<h1>TEST project information</h1><div class="col-md-9">'
               '<p>TEST unrelated acknowledgement must not become an entry reference.</p>'
               '<p>' + translator_credit + '</p><p>Камина шу китобларни TEST '
               '<a href="http://www.ziyouz.com">www.ziyouz.com</a> электрон нусҳасидан фойдаланди.</p></div>').encode()
        worker, _, _ = self.run_source()
        path = self.root / 'materials' / importer.SLUG / 'records.jsonl'
        before = json.loads(path.read_text())
        descriptor = worker.preserve(raw, url, {'retrieved_at': 'TEST saved time', 'status': 200})
        worker.state['snapshots'][url] = descriptor
        worker.state['collection_credits'][url] = {
            'url': url, 'snapshot': descriptor, 'scope': importer.COLLECTION_CREDIT_SCOPE,
            'text': 'TEST obsolete cached text must not supply visible source credits'}
        worker.save()
        with mock.patch.object(worker.opener, 'open') as request:
            report = worker.export()
        request.assert_not_called()
        row = json.loads(path.read_text())
        version = row['language_versions'][0]
        credits = [r for r in version['references'] if r['scope'] == importer.COLLECTION_CREDIT_SCOPE]
        self.assertEqual([r['source_citation'] for r in credits], [translator_credit, electronic_credit])
        self.assertEqual([r['source_locator']['paragraph'] for r in credits], [2, 3])
        for credit in credits:
            self.assertEqual(credit['source_locator']['sha256'], importer.digest(raw))
            self.assertEqual(credit['source_locator']['path'], descriptor['path'])
            self.assertEqual(credit['canonical_mapping_status'], 'not_inferred')
        self.assertEqual(row['text'], before['text'])
        self.assertEqual(version['text'], before['language_versions'][0]['text'])
        self.assertEqual(version['comments'], before['language_versions'][0]['comments'])
        self.assertIsNone(row['translator']['name'])
        self.assertIsNone(version['translation_provenance']['translator'])
        self.assertIsNone(row['number']['canonical'])
        self.assertEqual(report['prophetic_source_entries_registered'], 1)
        rendered = render_language_reading(language_readings(row)[0])
        self.assertIn(html.escape(translator_credit, quote=True), rendered)
        self.assertIn(html.escape(electronic_credit, quote=True), rendered)
        self.assertIn('href="http://www.ziyouz.com"', rendered)
        self.assertIn('publisher_collection_credit_not_per_entry_identity', rendered)
        self.assertNotIn('TEST unrelated acknowledgement', rendered)
        self.assertNotIn('TEST obsolete cached text', rendered)
        self.assertEqual(len(load_public_materials(self.root)['manifests']), 1)
        unchanged = path.read_bytes()
        worker.export()
        self.assertEqual(path.read_bytes(), unchanged)

    def test_edition_credit_paragraphs_preserve_sources_and_exclude_intro_narrations(self):
        url = importer.ORIGIN + '/page/sunani-termiziy'
        paragraphs = [
            'Мирзо Кенжабек, таржимон, TEST collection attribution.',
            'TEST Расулуллоҳ introduction quotation is not a collection credit.',
            '1. Мазкур таржима TEST source edition <not corrected>.',
            '2. Ҳадисларни ўрганишда TEST translation resources.',
            '7. Сахифа остида TEST commentary sources.',
        ]
        raw = ('<div class="col-md-9">' + ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs) + '</div>').encode()
        worker = self.worker()
        snapshot = worker.preserve(raw, url, {'retrieved_at': 'TEST time', 'status': 200})
        credits = importer.collection_credit_statements(raw, url, snapshot)
        self.assertEqual([c['name'] for c in credits], [paragraphs[i] for i in (0, 2, 3, 4)])
        self.assertEqual([c['source_locator']['paragraph'] for c in credits], [1, 3, 4, 5])
        self.assertTrue(all(c['scope'] == importer.COLLECTION_CREDIT_SCOPE for c in credits))
        with self.assertRaisesRegex(ValueError, 'does not match'):
            importer.collection_credit_statements(raw, importer.ORIGIN + '/page/about-project', snapshot)

    def test_corrupt_collection_credit_snapshot_cannot_supply_visible_attribution(self):
        worker, _, _ = self.run_source()
        url = importer.ORIGIN + '/page/about-project'
        raw = '<div class="col-md-9"><p>Ҳадислар учун манба сифатида TEST source.</p></div>'.encode()
        snapshot = worker.preserve(raw, url, {'retrieved_at': 'TEST time', 'status': 200})
        worker.state['collection_credits'][url] = {'url': url, 'snapshot': snapshot,
            'scope': importer.COLLECTION_CREDIT_SCOPE, 'text': 'TEST preserved cached credit'}
        (self.root / snapshot['path']).write_bytes(b'TEST corrupt credit evidence')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            worker.export()


if __name__ == '__main__':
    unittest.main()
