"""Shared display titles must agree across browser and static reading surfaces."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from book_titles import book_label, title_metadata
import build_book_catalog
import build_discovery
import build_reader
from test_reader import fixture, navigation_fixture, READER_SNAPSHOT_JS


EXPECTED = {
    ('zh-CN', 'bukhari'): '布哈里圣训实录 — Sahih al-Bukhari',
    ('fa', 'muslim'): 'صحیح مسلم — Sahih Muslim',
    ('ja', 'muslim'): 'サヒーフ・ムスリム — Sahih Muslim',
    ('zh-CN', 'ibn-majah'): '伊本·马哲圣训集 — Sunan Ibn Majah',
    ('fa', 'ibn-majah'): 'سنن ابن‌ماجه — Sunan Ibn Majah',
}


class VisibleText(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.values = []
        self.ignored = 0
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.values.append(data)


class BookTitleTests(unittest.TestCase):
    def test_native_order_aliases_and_mixed_language_fallback(self):
        for (language, book), expected in EXPECTED.items():
            with self.subTest(language=language, book=book):
                self.assertEqual(book_label(book, language), expected)
        self.assertEqual(book_label('muslim', 'fa-IR'), book_label('muslim', 'fa'))
        self.assertEqual(book_label('ibn-majah', 'zh'), book_label('ibn-majah', 'zh-CN'))
        self.assertEqual(book_label('al-nasai', 'fa'), book_label('nasai', 'fa'))
        self.assertEqual(build_discovery.book_name('al-nasai', 'fa'),
                         build_discovery.book_name('nasai', 'fa'))
        self.assertEqual(book_label('riyad-as-salihin', 'fa'), book_label('riyadh-al-salihin', 'fa'))
        self.assertEqual(book_label('bukhari', ''), 'Sahih al-Bukhari')
        self.assertEqual(book_label('bukhari', 'en'), 'Sahih al-Bukhari')
        self.assertEqual(book_label('TEST-unlisted', 'fa'), 'TEST-unlisted')
        qualified = 'Reports attributed to al-Hakim'
        self.assertEqual(book_label('hakim', '', english=qualified), qualified)
        self.assertTrue(book_label('hakim', 'fa', english=qualified).endswith(' — ' + qualified))

    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser title parity')
    def test_browser_uses_shared_titles_and_keeps_language_filters_distinct(self):
        metadata = title_metadata()
        queries = [(language, book) for language, books in metadata.items() for book in books]
        queries += [('fa-IR', 'muslim'), ('zh', 'ibn-majah'), ('fa', 'al-nasai'),
                    ('fa', 'riyad-as-salihin'), ('', 'bukhari'), ('fa', 'TEST-unlisted')]
        records = [navigation_fixture(i, language=language, book=book,
                                      source='TEST-source-' + str(i))
                   for i, (language, book) in enumerate(EXPECTED, 1)]
        template = (Path(build_reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = READER_SNAPSHOT_JS + '''
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=input.records,names={};
const valueText = ''' + helpers + '''
const selections=input.scopes.map(([language,book])=>{
 const scope=resolveMaterialFilters(records,{language,book});
 return {books:[...scope.books.values()],sources:[...scope.sources.values()],ids:scope.rows.map(r=>r.id)};
});
const mixed=resolveMaterialFilters(records,{book:'muslim'});
process.stdout.write(JSON.stringify({labels:input.queries.map(([language,book])=>bookLabel(book,language)),
 selections,mixed:{books:[...mixed.books.values()],ids:mixed.rows.map(r=>r.id)}}));
'''
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'queries': queries, 'records': records,
                                                  'scopes': list(EXPECTED)}),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual['labels'], [book_label(book, language) for language, book in queries])
        for i, ((language, book), expected) in enumerate(EXPECTED.items(), 1):
            selected = actual['selections'][i - 1]
            self.assertIn(expected, selected['books'])
            self.assertTrue(all(expected in value for value in selected['sources']))
            self.assertEqual(selected['ids'], ['TEST-' + str(i)])
        self.assertEqual(actual['mixed']['ids'], ['TEST-2', 'TEST-3'])
        self.assertIn('Sahih Muslim', actual['mixed']['books'])
        self.assertNotIn(EXPECTED[('fa', 'muslim')], actual['mixed']['books'])
        self.assertNotIn(EXPECTED[('ja', 'muslim')], actual['mixed']['books'])

    def test_native_titles_reach_static_markdown_and_book_catalog_without_source_edits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'search').mkdir()
            (root / 'catalog').mkdir()
            records, materials = [], []
            for index, (language, book) in enumerate(EXPECTED, 1):
                record = fixture(index)
                record.update(language=language, source_language_code=language,
                              book_key=book, source_id='TEST-source-' + str(index))
                record['source']['name'] = 'TEST exact publisher title ' + str(index)
                records.append(record)
                materials.append({'dataset_id': record['source_id'], 'language': language,
                                  'book_key': book, 'edition': record['edition'], 'count': 1,
                                  'source_name': record['source']['name']})
            original = copy.deepcopy(records)
            stream = b''.join((json.dumps(item, ensure_ascii=False) + '\n').encode() for item in records)
            (root / 'search/records.jsonl').write_bytes(stream)
            catalog = {'record_count': len(records), 'materials': materials,
                       'search': {'records_path': 'search/records.jsonl', 'count': len(records),
                                  'records_sha256': hashlib.sha256(stream).hexdigest()}}
            (root / 'catalog/materials.json').write_text(json.dumps(catalog, ensure_ascii=False))
            build_reader.build(root, root / 'reader.html', root / 'browse')
            build_discovery.build(root, root / '_site')
            build_book_catalog.write_catalog(root, catalog)
            book_catalog = (root / 'catalog/BOOKS.md').read_text()
            for record, ((language, book), label) in zip(records, EXPECTED.items()):
                paths = [root / 'browse' / language / 'README.md',
                         root / 'browse' / language / book / 'README.md',
                         root / 'browse' / language / book / record['edition'] / 'page-0001.md',
                         root / '_site' / build_discovery.record_path(record),
                         root / '_site/browse' / language / 'index.html',
                         root / '_site/browse' / language / book / 'index.html',
                         root / '_site/browse' / language / book / record['edition'] / 'index.html']
                for path in paths:
                    with self.subTest(language=language, book=book, path=str(path)):
                        content = path.read_text()
                        if path.suffix == '.html':
                            content = ''.join(VisibleText(content).values)
                        self.assertIn(label, content)
                self.assertIn('### ' + label, book_catalog)
                self.assertIn(record['source']['name'], book_catalog)
            self.assertEqual(records, original)
            self.assertEqual((root / 'search/records.jsonl').read_bytes(), stream)


if __name__ == '__main__':
    unittest.main()
