"""Offline tests for the seven chapter roots observed in the saved Tirmidhi sidebar."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.request
import urllib.robotparser

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_hadisuz as importer

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
CHAPTERS = [importer.ORIGIN + '/hadiths/' + number for number in ['3', '15', '17', '18', '19', '20', '430']]


def catalogue(sidebar=b'', pagination='', title='Сунани Термизий'):
    return (f'<h1>{title}</h1><div class="col-md-9">'
            '<p>TEST preview is not a narration record.</p>'
            '<a href="/hadith/615">TEST observed detail</a>' + pagination + '</div>').encode() + sidebar


class HadisuzCatalogChapterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sidebar = (FIXTURES / 'hadisuz-tirmidhi-sidebar.html').read_bytes()

    def worker(self):
        return importer.Importer(self.root, max_pages=1, max_seconds=30, delay=0)

    def saved(self, worker, raw, url=importer.CATALOG):
        snapshot = worker.preserve(raw, url, {'retrieved_at': 'TEST saved time', 'status': 200, 'final_url': url})
        worker.state['snapshots'][url] = snapshot
        return snapshot

    def test_exact_saved_sidebar_fixture_has_its_bound_source_hash(self):
        evidence = json.loads((FIXTURES / 'hadisuz-tirmidhi-sidebar.json').read_text())
        self.assertEqual(hashlib.sha256(self.sidebar).hexdigest(), evidence['fixture_sha256'])
        self.assertEqual(evidence['fixture_sha256'], '624910ba52f99978cde778faef6384799d65897aae4fa5b71738f64e39aae3a2')
        self.assertEqual(len(self.sidebar), evidence['raw_utf8_byte_span'][1] - evidence['raw_utf8_byte_span'][0])
        self.assertEqual(evidence['source_url'], importer.CATALOG)
        self.assertFalse(evidence['target_chapter_titles_observed'])

    def test_seven_observed_chapter_routes_and_seed_keep_positive_page_query_support(self):
        for url in [importer.CATALOG, *CHAPTERS]:
            for suffix in ['', '?page=1', '?page=2', '?page=61']:
                with self.subTest(url=url + suffix):
                    self.assertTrue(importer.allowed_url(url + suffix, 'catalog'))
                    self.assertTrue(importer.allowed_url(url + suffix))
                    self.assertFalse(importer.allowed_url(url + suffix, 'detail'))
                    self.assertFalse(importer.allowed_url(url + suffix, 'info'))

    def test_unobserved_catalog_paths_and_other_collections_remain_denied(self):
        for path in ['/hadiths', '/hadiths/2', '/hadiths/4', '/hadiths/14', '/hadiths/16',
                     '/hadiths/21', '/hadiths/45', '/hadiths/431', '/hadiths/999',
                     '/hadiths/03', '/hadiths/3/', '/hadiths/3/details']:
            for suffix in ['', '?page=2']:
                with self.subTest(path=path + suffix):
                    self.assertFalse(importer.allowed_url(importer.ORIGIN + path + suffix, 'catalog'))

    def test_chapters_keep_exact_origin_scheme_fragment_and_query_guards(self):
        for url in ['http://hadis.uz/hadiths/3', 'https://example.invalid/hadiths/3',
                    'https://www.hadis.uz/hadiths/3', 'https://hadis.uz:443/hadiths/3',
                    'https://user@hadis.uz/hadiths/3', 'https://hadis.uz/hadiths/3#next']:
            with self.subTest(url=url):
                self.assertFalse(importer.allowed_url(url, 'catalog'))
        for suffix in ['?page=', '?page=0', '?page=-1', '?page=01', '?page=1.5',
                       '?page=2&page=3', '?page=2&sort=asc', '?sort=asc', '?other=2']:
            with self.subTest(suffix=suffix):
                self.assertFalse(importer.allowed_url(CHAPTERS[0] + suffix, 'catalog'))

    def test_saved_sidebar_links_are_discovered_separately_from_detail_and_next(self):
        raw = catalogue(self.sidebar, '<a rel="next" href="?page=2">TEST next</a>')
        parsed = importer.parse_catalog(raw, importer.CATALOG)
        self.assertEqual(parsed['chapters'], CHAPTERS)
        self.assertEqual(parsed['next'], [importer.CATALOG + '?page=2'])
        self.assertEqual(parsed['details'], [importer.ORIGIN + '/hadith/615'])
        self.assertTrue(parsed['previews_not_registered'])

    def test_membership_alone_never_discovers_or_enqueues_a_chapter(self):
        worker = self.worker()
        self.assertEqual([task['url'] for task in worker.state['tasks']], [importer.CATALOG])
        raw = catalogue(b'<a href="/hadiths/45">TEST unrelated collection</a>'
                        b'<span>TEST /hadiths/3 mentioned without a link</span>'
                        b'<a data-href="/hadiths/15">TEST absent actual href</a>')
        self.assertEqual(importer.parse_catalog(raw, importer.CATALOG)['chapters'], [])
        with mock.patch.object(worker.opener, 'open', side_effect=AssertionError('No HTTP permitted')):
            worker.process(worker.state['tasks'][0], raw, {'path': 'TEST saved catalogue'})
        self.assertEqual([task['url'] for task in worker.state['tasks']],
                         [importer.CATALOG, importer.ORIGIN + '/hadith/615'])

    def test_chapter_discovery_requires_actual_root_href_and_deduplicates(self):
        sidebar = (b'<div class="col-md-3"><div class="panel"><h3 class="panel-title">' + 'Манбалар'.encode() +
                   b'</h3><div class="panel-body">' + 'Сунани Термизий'.encode() + b'</div><ul class="list-group">'
                   b'<a href="/hadiths/3">TEST chapter</a>'
                   b'<a href="https://hadis.uz/hadiths/3">TEST chapter</a>'
                   b'<a href="/hadiths/1">TEST current root</a>'
                   b'<a href="/hadiths/15?page=2">TEST page without next relation</a>'
                   b'<a href="/hadiths/17#part">TEST fragment</a>'
                   b'<a href="/hadiths/18?sort=asc">TEST disallowed query</a></ul></div></div>')
        parsed = importer.parse_catalog(catalogue(sidebar), importer.CATALOG)
        self.assertEqual(parsed['chapters'], [CHAPTERS[0]])
        self.assertEqual(parsed['next'], [])

    def test_processing_persists_only_observed_tasks_and_preserves_next_order(self):
        worker = self.worker()
        raw = catalogue(self.sidebar, '<a rel="next" href="?page=2">TEST next</a>')
        snapshot = self.saved(worker, raw)
        with mock.patch.object(worker.opener, 'open', side_effect=AssertionError('No HTTP permitted')):
            worker.process(worker.state['tasks'][0], raw, snapshot)
            worker.save()
        expected = [importer.CATALOG, importer.ORIGIN + '/hadith/615', importer.CATALOG + '?page=2', *CHAPTERS]
        self.assertEqual([task['url'] for task in worker.state['tasks']], expected)
        for task in worker.state['tasks'][2:]:
            self.assertEqual((task['kind'], task['status'], task['attempts'], task['discovered_on']),
                             ('catalog', 'pending', 0, importer.CATALOG))
        resumed = self.worker()
        self.assertEqual(resumed.state, worker.state)
        resumed.process(resumed.state['tasks'][0], raw, snapshot)
        self.assertEqual([task['url'] for task in resumed.state['tasks']], expected)
        self.assertEqual(resumed.state['tasks'][0]['discovery']['chapters'], CHAPTERS)

    def test_chapter_pagination_still_requires_observed_next_relation(self):
        raw = catalogue(pagination='<a rel="prev" href="?page=1">TEST prev</a>'
                        '<a href="?page=9">TEST numbered page</a>'
                        '<a rel="next" href="?page=3">TEST next</a>', title='Таҳорат боблари')
        parsed = importer.parse_catalog(raw, CHAPTERS[0] + '?page=2')
        self.assertEqual(parsed['next'], [CHAPTERS[0] + '?page=3'])
        self.assertEqual(parsed['chapters'], [])
        ambiguous = catalogue(pagination='<a rel="next" href="?page=3">TEST next</a>'
                              '<a rel="next" href="?page=4">TEST conflicting next</a>', title='Таҳорат боблари')
        with self.assertRaisesRegex(ValueError, 'Ambiguous catalogue next-page'):
            importer.parse_catalog(ambiguous, CHAPTERS[0] + '?page=2')

    def test_chapter_title_matches_verified_parent_label_and_root_stays_tirmidhi(self):
        parsed = importer.parse_catalog(catalogue(title='Таҳорат боблари'), CHAPTERS[0])
        self.assertEqual(parsed['title'], 'Таҳорат боблари')
        for title in ['Сунани Термизий', 'TEST other collection', '']:
            with self.subTest(title=title):
                with self.assertRaisesRegex(ValueError, 'observed parent-link label'):
                    importer.parse_catalog(catalogue(self.sidebar, title=title), CHAPTERS[0])
        with self.assertRaisesRegex(ValueError, 'authorized Tirmidhi collection'):
            importer.parse_catalog(catalogue(title='TEST other collection'), importer.CATALOG)

    def test_allowed_chapters_cannot_bypass_robots_or_persisted_access_stop(self):
        worker = self.worker()
        raw = catalogue(self.sidebar)
        worker.process(worker.state['tasks'][0], raw, self.saved(worker, raw))
        worker.robot = urllib.robotparser.RobotFileParser()
        worker.robot.parse(['User-agent: *', 'Disallow: /hadiths/3'])
        with mock.patch.object(worker.opener, 'open', side_effect=AssertionError('No HTTP permitted')):
            with self.assertRaisesRegex(PermissionError, 'robots_disallowed'):
                worker.fetch(CHAPTERS[0])
            worker.state['access_block'] = {'status': 403, 'automatic_retry_allowed': False}
            with self.assertRaisesRegex(RuntimeError, 'Prior access block'):
                worker.fetch(CHAPTERS[1])

    def test_redirect_still_cannot_change_identity_to_another_allowed_chapter(self):
        redirect = importer.PublicRedirects()
        request = urllib.request.Request(importer.CATALOG)
        for target in [CHAPTERS[0], CHAPTERS[0] + '?page=2', '/auth/login', 'http://hadis.uz/hadiths/3']:
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, 'source identity'):
                    redirect.redirect_request(request, None, 302, 'TEST redirect', {}, target)


if __name__ == '__main__':
    unittest.main()
