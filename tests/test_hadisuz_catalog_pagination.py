"""Offline discovery tests for actually linked previous, numbered and next pages."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_hadisuz as importer


def catalogue(links='', outside='', title='Сунани Термизий'):
    return ('<h1>' + title + '</h1><div class="col-md-9">'
            '<a href="/hadith/615">TEST observed detail</a>' + links +
            '</div>' + outside).encode()


class HadisuzCatalogPaginationTests(unittest.TestCase):
    def test_observed_previous_numbered_and_next_urls_are_retained_once(self):
        raw = catalogue('<a rel="prev" href="?page=1">TEST previous</a>'
                        '<a href="?page=1">TEST duplicate numbered first page</a>'
                        '<a href="?page=9">TEST observed numbered page</a>'
                        '<a rel="next" href="?page=3">TEST next</a>'
                        '<a href="https://hadis.uz/hadiths/3?page=9">TEST absolute duplicate</a>'
                        '<a href="/hadiths/45?page=2">TEST other collection</a>'
                        '<a href="?page=0">TEST invalid page</a>'
                        '<a href="?page=2&amp;sort=asc">TEST invalid query</a>', title='Таҳорат боблари')
        base = importer.ORIGIN + '/hadiths/3'
        parsed = importer.parse_catalog(raw, base + '?page=2')
        self.assertEqual(parsed['pagination'], [base + '?page=1', base + '?page=9', base + '?page=3'])
        self.assertEqual(parsed['next'], [base + '?page=3'])
        self.assertEqual(parsed['chapters'], [])
        self.assertEqual(parsed['details'], [importer.ORIGIN + '/hadith/615'])

    def test_processing_enqueues_observed_page_one_alias_without_guessing_ranges(self):
        with tempfile.TemporaryDirectory() as folder:
            worker = importer.Importer(Path(folder), max_pages=1, max_seconds=30, delay=0)
            current = importer.CATALOG + '?page=2'
            worker.enqueue(current, 'catalog', importer.CATALOG)
            task = next(item for item in worker.state['tasks'] if item['url'] == current)
            raw = catalogue('<a rel="prev" href="?page=1">TEST first-page alias</a>'
                            '<a href="?page=9">TEST observed numbered page</a>'
                            '<a rel="next" href="?page=3">TEST next</a>'
                            '<a href="?page=9">TEST duplicate</a>')
            with mock.patch.object(worker.opener, 'open', side_effect=AssertionError('No HTTP permitted')):
                worker.process(task, raw, {'path': 'TEST saved catalogue'})
                worker.process(task, raw, {'path': 'TEST saved catalogue'})
            self.assertEqual([item['url'] for item in worker.state['tasks']],
                [importer.CATALOG, current, importer.ORIGIN + '/hadith/615',
                 importer.CATALOG + '?page=3', importer.CATALOG + '?page=1', importer.CATALOG + '?page=9'])
            self.assertEqual(task['discovery']['pagination'],
                [importer.CATALOG + '?page=1', importer.CATALOG + '?page=9', importer.CATALOG + '?page=3'])
            for item in worker.state['tasks'][3:]:
                self.assertEqual((item['kind'], item['status'], item['discovered_on']),
                                 ('catalog', 'pending', current))

    def test_unlinked_pages_and_pagination_outside_content_column_are_not_discovered(self):
        raw = catalogue('<span>TEST page=1 and page=9 are mentioned without links.</span>'
                        '<a data-href="?page=1">TEST no actual href</a>'
                        '<a href="https://example.invalid/hadiths/3?page=1">TEST foreign</a>',
                        '<aside><a href="/hadiths/3?page=1">TEST outside content column</a></aside>', title='Таҳорат боблари')
        parsed = importer.parse_catalog(raw, importer.ORIGIN + '/hadiths/3?page=10')
        self.assertEqual(parsed['pagination'], [])
        self.assertEqual(parsed['next'], [])
        self.assertEqual(parsed['chapters'], [])


if __name__ == '__main__':
    unittest.main()
