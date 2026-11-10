"""Reader fixtures are synthetic; no fixture is a religious quotation."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader


def fixture(index=1):
    return {
        'id': 'fixture-' + str(index), 'language': 'ja', 'source_language_code': 'ja',
        'book_key': 'fixture-book', 'edition': 'snapshot-a', 'source_id': 'fixture-source',
        'provider_entry_id': '101', 'title': 'Synthetic title',
        'text_arabic': 'نَصّ تَجْرِيبِيّ',
        'text_translation': '合成\n日本語の例\n<script>unsafe()</script> & __HADITH_SNAPSHOT_JSON__',
        'number': {'in_book': None, 'source_entry_id': '101', 'canonical': None},
        'narrator': {'name': None},
        'source': {'name': 'Synthetic source', 'url': 'https://example.invalid/source',
                   'record_url': 'https://example.invalid/101', 'original_file': None,
                   'sha256': '0' * 64, 'record_locator': {'path': 'fixture.json', 'json_pointer': '/0'}},
        'translator': {'name': None},
        'translation_provenance': {'origin': 'unknown', 'label': 'Supplied label; origin unknown',
                                   'basis': 'Synthetic fixture', 'human_involvement': 'unknown',
                                   'ai_translation': 'unknown', 'evidence_ids': []},
        'topic_tags': [{'id': 'topic-fixture', 'label': 'Synthetic category', 'path': ['Synthetic category']}],
        'editorial_tags': [], 'source_headings': [],
        'review': {'status': 'fixture_pending', 'issues': [], 'independent_pro_qc': 'pending',
                   'release_status': 'source_snapshot'},
        'commentary': {'arabic': None, 'translation': 'COMMENTARY-ONLY-FIXTURE'},
        'footnotes': [], 'references': {}, 'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None},
    }


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'bank'
        (self.root / 'catalog').mkdir(parents=True)
        (self.root / 'search').mkdir()
        self.output = Path(self.temp.name) / 'reader.html'

    def save(self, records, shards=False):
        lines = [(json.dumps(record, ensure_ascii=False) + '\n').encode('utf-8') for record in records]
        data = b''.join(lines)
        search = {'records_path': 'search/records.jsonl',
                  'records_sha256': hashlib.sha256(data).hexdigest(), 'count': len(records)}
        if shards:
            search['shards'] = []
            for i, raw in enumerate(lines):
                relative = 'search/part-' + str(i) + '.jsonl'
                (self.root / relative).write_bytes(raw)
                search['shards'].append({'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(),
                                         'count': 1, 'bytes': len(raw)})
        else:
            (self.root / search['records_path']).write_bytes(data)
        catalog = {'title': 'Fixture bank', 'search': search, 'materials': []}
        self.write_catalog(catalog)
        return catalog

    def write_catalog(self, catalog):
        (self.root / 'catalog/materials.json').write_text(json.dumps(catalog), encoding='utf-8')

    def embedded_records(self):
        document = self.output.read_text(encoding='utf-8')
        match = re.search(r'<script id="hadith-records" type="application/octet-stream" data-encoding="([^"]+)">(.*?)</script>', document, re.S)
        raw = gzip.decompress(base64.b64decode(match.group(2))).decode('utf-8') if match.group(1) == 'gzip-base64' else match.group(2)
        return json.loads(raw), document

    def test_embedding_preserves_exact_strings_and_escapes_script_delimiters(self):
        records = [fixture()]
        self.save(records)
        result = reader.build(self.root, self.output, compress=False)
        embedded, document = self.embedded_records()
        self.assertEqual(embedded, records)
        self.assertNotIn('<script>unsafe()</script>', document)
        self.assertIn('\\u003cscript\\u003e', document)
        self.assertFalse(result['source_text_modified'])
        self.assertEqual(result['network_dependencies'], [])

    def test_shard_only_input_is_complete_and_preserves_duplicate_occurrences(self):
        first, second = fixture(), fixture()
        second['edition'] = 'snapshot-b'
        records = [first, second]
        self.save(records, shards=True)
        result = reader.build(self.root, self.output)
        embedded, _ = self.embedded_records()
        self.assertEqual(embedded, records)
        self.assertEqual(result['input_files_verified'], 2)
        self.assertEqual(result['input_mode'], 'shards')

    def test_whole_file_tamper_rejected_before_output(self):
        self.save([fixture()])
        with (self.root / 'search/records.jsonl').open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            reader.build(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_shard_tamper_rejected_before_output(self):
        self.save([fixture()], shards=True)
        (self.root / 'search/part-0.jsonl').write_bytes(b'{}\n')
        with self.assertRaises(ValueError):
            reader.build(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_shard_path_traversal_rejected(self):
        catalog = self.save([fixture()], shards=True)
        catalog['search']['shards'][0]['path'] = '../outside.jsonl'
        self.write_catalog(catalog)
        with self.assertRaisesRegex(ValueError, 'Unsafe local source path'):
            reader.build(self.root, self.output)

    def test_combined_shard_hash_checked(self):
        catalog = self.save([fixture(1), fixture(2)], shards=True)
        catalog['search']['shards'].reverse()
        self.write_catalog(catalog)
        with self.assertRaisesRegex(ValueError, 'Combined search stream'):
            reader.build(self.root, self.output)

    def test_markdown_pages_have_25_records_and_explicit_source_origin(self):
        records = [fixture(i) for i in range(26)]
        self.save(records)
        directory = Path(self.temp.name) / 'readable'
        result = reader.build(self.root, self.output, directory)
        page1 = (directory / 'ja/fixture-book/snapshot-a/page-0001.md').read_text()
        page2 = (directory / 'ja/fixture-book/snapshot-a/page-0002.md').read_text()
        self.assertEqual(result['markdown_pages'], 2)
        self.assertEqual(page1.count('## Narration '), 25)
        self.assertEqual(page2.count('## Narration '), 1)
        self.assertIn('https://example.invalid/101', page1)
        self.assertIn('Supplied label; origin unknown', page1)
        self.assertIn('&lt;script&gt;unsafe()&lt;/script&gt; &amp;', page1)
        self.assertIn('<p dir="auto">合成<br>\n日本語の例<br>\n', page1)
        self.assertIn('<p dir="rtl">نَصّ تَجْرِيبِيّ</p>', page1)
        self.assertNotIn('<pre>合成', page1)
        self.assertNotIn('&quot;text_translation&quot;', page1)
        self.assertIn('Canonical record:', page1)
        self.assertTrue((directory / 'README.md').is_file())

    def test_unsafe_source_urls_never_become_links(self):
        record = fixture()
        record['source']['record_url'] = 'javascript:alert(1)'
        record['source']['url'] = None
        rendered = reader.markdown_record(record, 1)
        self.assertNotIn('href="javascript:', rendered)
        self.assertIn('source URL not supplied', rendered)

    def test_supplied_benefits_are_readable_and_separate_from_narration(self):
        record = fixture()
        record['benefits'] = {'translation': ['BENEFIT-ONE\nSECOND-LINE', 'BENEFIT-TWO'],
                              'arabic': 'فَائِدَةٌ\nنَصٌّ',
                              'scope': 'whole_source_entry_not_individually_adjudicated'}
        rendered = reader.markdown_record(record, 1)
        self.assertIn('<summary>Benefits supplied by the source</summary>', rendered)
        benefits = rendered.split('<summary>Benefits supplied by the source</summary>', 1)[1].split('</details>', 1)[0]
        self.assertIn('<p dir="auto">BENEFIT-ONE<br>\nSECOND-LINE</p>', benefits)
        self.assertIn('<p dir="auto">BENEFIT-TWO</p>', benefits)
        self.assertIn('<p dir="rtl">فَائِدَةٌ<br>\nنَصٌّ</p>', benefits)
        self.assertIn('whole_source_entry_not_individually_adjudicated', benefits)
        self.assertNotIn('BENEFIT-ONE', rendered.split('<summary>Benefits supplied by the source</summary>', 1)[0])
        self.assertEqual(record['benefits']['translation'][0], 'BENEFIT-ONE\nSECOND-LINE')

    @unittest.skipUnless(shutil.which('node'), 'Node is optional; required only for reader JavaScript regression checks')
    def test_reader_search_handles_cjk_terms_boundaries_and_benefits(self):
        first, second = fixture(1), fixture(2)
        first['title'] = '合成の甲'
        first['text_translation'] = '乙と私の例'
        first['benefits'] = {'translation': ['BENEFIT-ONLY-SEARCH-TERM']}
        second['title'] = '別の題'
        second['text_translation'] = '私についての例'
        second['benefits'] = {'translation': []}
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        filter_function = template.split('function applyFilters(){', 1)[1].split('$("query").addEventListener', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=input.records,state={matches:[]},fields={query:{value:''},'language-filter':{value:''},'book-filter':{value:''},'source-filter':{value:''},'origin-filter':{value:''},'include-commentary':{checked:false}};
const $=id=>fields[id],render=()=>{};
const valueText = ''' + helpers + '''\nfunction applyFilters(){''' + filter_function + '''
const result=input.queries.map(item=>{fields.query.value=item.query;fields['include-commentary'].checked=item.commentary;applyFilters();return state.matches.map(i=>records[i].id);});
process.stdout.write(JSON.stringify(result));'''
        queries = [{'query': '合成 私', 'commentary': False},
                   {'query': '甲乙', 'commentary': False},
                   {'query': 'BENEFIT-ONLY-SEARCH-TERM', 'commentary': False},
                   {'query': 'BENEFIT-ONLY-SEARCH-TERM', 'commentary': True}]
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'records': [first, second], 'queries': queries}, ensure_ascii=False),
                                text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), [[first['id']], [], [], [first['id']]])


if __name__ == '__main__':
    unittest.main()
