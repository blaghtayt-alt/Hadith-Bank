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


def navigation_fixture(index, language='ja', book='TEST-a', edition='TEST-edition-a',
                       source='TEST-source-a', origin='unknown', ai='unknown', current=None):
    """Literal TEST content for navigation and classification regressions."""
    provenance = {'origin': origin, 'ai_translation': ai, 'label': 'TEST', 'basis': 'TEST'}
    if current is not None:
        provenance['current_policy'] = {'classification': current, 'basis': 'TEST'}
    return {
        'id': 'TEST-' + str(index), 'language': language, 'book_key': book,
        'edition': edition, 'source_id': source, 'title': 'TEST',
        'text_translation': 'TEST', 'text_arabic': None,
        'source': {'name': 'TEST', 'url': 'https://example.invalid/TEST'},
        'translator': {'name': 'TEST'}, 'translation_provenance': provenance,
        'review': {'status': 'pending'}, 'topic_tags': [], 'editorial_tags': [],
        'source_headings': [], 'footnotes': [],
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

    def test_hosted_metadata_preserves_pending_records_and_new_language(self):
        record = fixture()
        record.update({'language': 'sw', 'title': 'TEST', 'text_translation': 'TEST TEST',
                       'text_arabic': None, 'commentary': {}})
        record['review'] = {'release_status': 'private_candidate',
                            'independent_pro_qc': 'pending', 'release_eligible': False}
        record['publication'] = {'visibility': 'public', 'authorized': True,
                                 'status': 'published_pending_review',
                                 'independent_qc_asserted': False}
        self.save([record])
        commit = 'a' * 40
        reader.build(self.root, self.output, site={'source_ref': commit, 'build_commit': commit})
        embedded, document = self.embedded_records()
        self.assertEqual(embedded, [record])
        metadata = json.loads(re.search(r'<script id="hadith-snapshot" type="application/json">(.*?)</script>',
                                        document, re.S).group(1))
        self.assertEqual(metadata['site']['source_ref'], commit)
        self.assertEqual(metadata['site']['build_commit'], commit)
        self.assertIn('Download offline reader', document)
        self.assertIn('window.location.href.split("#")[0]', document)
        self.assertIn('Published · independent review pending', document)
        self.assertIn('languageLabel(r.language)', document)
        self.assertIn('new Intl.DisplayNames', document)

    def test_unsafe_site_navigation_rejected_before_output(self):
        self.save([fixture()])
        for site in ({'repository_url': 'javascript:TEST'},
                     {'repository_url': 'https://github.com/TEST/TEST?redirect=TEST'},
                     {'live_url': 'https://TEST:TEST@example.invalid/'},
                     {'source_ref': 'TEST/../TEST'},
                     {'build_commit': 'TEST'}):
            with self.subTest(site=site), self.assertRaises(ValueError):
                reader.build(self.root, self.output, site=site)
            self.assertFalse(self.output.exists())

    @unittest.skipUnless(shutil.which('node'), 'Node is optional; required for reader JavaScript regression checks')
    def test_hosted_local_source_links_and_review_labels(self):
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=[],names={};
const valueText = ''' + helpers + '''
const site=input.site;
process.stdout.write(JSON.stringify({
  hosted:recordFileURL('attachments/TEST/TEST #.pdf',site,'https:'),
  local:recordFileURL('attachments/TEST/TEST #.pdf',site,'file:'),
  encoded:recordFileURL('%2e%2e/TEST.pdf',site,'https:'),
  invalid:input.invalid.map(path=>recordFileURL(path,site,'https:')),
  review:input.review.map(record=>({pending:needsIndependentReview(record),published:hasPublicAuthorization(record)})),
  language:languageLabel('sw')
}));'''
        sample = {'site': {'repository_url': 'https://github.com/TEST/TEST', 'source_ref': 'a' * 40},
                  'invalid': ['../TEST.pdf', '/TEST.pdf', 'TEST\\TEST.pdf', 'TEST//TEST.pdf',
                              'TEST/./TEST.pdf', 'javascript:TEST', 'TEST\nTEST.pdf'],
                  'review': [
                      {'review': {'release_status': 'private_candidate', 'independent_pro_qc': 'pending'},
                       'publication': {'visibility': 'public', 'authorized': True,
                                       'status': 'published_pending_review', 'independent_qc_asserted': False}},
                      {'review': {'independent_pro_qc': 'pending',
                                  'current_policy': {'separate_bank_review_required': False}}},
                      {'review': {'independent_pro_qc': 'passed'}}]}
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(sample),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        base = 'https://github.com/TEST/TEST/blob/' + 'a' * 40 + '/'
        self.assertEqual(actual['hosted'], base + 'attachments/TEST/TEST%20%23.pdf')
        self.assertEqual(actual['local'], 'attachments/TEST/TEST%20%23.pdf')
        self.assertEqual(actual['encoded'], base + '%252e%252e/TEST.pdf')
        self.assertEqual(actual['invalid'], [None] * len(sample['invalid']))
        self.assertEqual(actual['review'], [{'pending': True, 'published': True},
                                             {'pending': False, 'published': False},
                                             {'pending': False, 'published': False}])
        self.assertEqual(actual['language'], 'Swahili')

    @unittest.skipUnless(shutil.which('node'), 'Node is optional; required for reader JavaScript regression checks')
    def test_language_scoped_materials_reset_only_incompatible_filters(self):
        records = [
            navigation_fixture(1, origin='publisher_human_workflow'),
            navigation_fixture(2, origin='publisher_human_workflow'),
            navigation_fixture(3, edition='TEST-edition-b', source='TEST-source-b',
                               origin='human_translator_credited'),
            navigation_fixture(4, book='TEST-b', source='TEST-source-c'),
            navigation_fixture(5, language='vi', book='TEST-b', source='TEST-source-vi-b', ai=True),
            navigation_fixture(6, language='vi', book='TEST-c', source='TEST-source-vi-c', ai=False),
            navigation_fixture(7, language='sw', book='TEST-d', source='TEST-source-sw', current='human'),
        ]
        selections = [
            {'language': 'ja', 'book': 'TEST-c', 'source': 'TEST-source-vi-c'},
            {'language': 'ja', 'book': 'TEST-b', 'source': 'TEST-source-vi-b'},
            {'language': 'ja', 'book': 'TEST-a', 'source': 'TEST-source-b'},
            {'language': 'ja', 'book': 'TEST-b', 'source': 'TEST-source-c', 'origin': 'human'},
            {'language': 'ja', 'book': 'TEST-a', 'source': 'TEST-source-b', 'origin': 'ai'},
            {'language': 'sw'},
        ]
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=input.records,names={};
const valueText = ''' + helpers + '''
const result=input.selections.map(selection=>{
 const scope=resolveMaterialFilters(records,selection);
 return {...scope,books:[...scope.books.keys()],sources:[...scope.sources.keys()],rows:scope.rows.map(record=>record.id)};
});
process.stdout.write(JSON.stringify(result));'''
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'records': records, 'selections': selections}),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual[0]['book'], '')
        self.assertEqual(actual[0]['source'], '')
        self.assertEqual(actual[0]['books'], ['TEST-a', 'TEST-b'])
        self.assertEqual(actual[0]['sources'], ['TEST-source-a', 'TEST-source-b', 'TEST-source-c'])
        self.assertEqual(actual[0]['language_count'], 4)
        self.assertEqual(actual[0]['materials'], [
            {'book_key': 'TEST-a', 'count': 3, 'edition_count': 2},
            {'book_key': 'TEST-b', 'count': 1, 'edition_count': 1}])
        self.assertEqual(actual[1]['book'], 'TEST-b')
        self.assertEqual(actual[1]['source'], '')
        self.assertEqual(actual[1]['rows'], ['TEST-4'])
        self.assertEqual(actual[2]['source'], 'TEST-source-b')
        self.assertEqual(actual[2]['rows'], ['TEST-3'])
        self.assertEqual(actual[3]['book'], '')
        self.assertEqual(actual[3]['books'], ['TEST-a'])
        self.assertEqual(actual[3]['rows'], ['TEST-1', 'TEST-2', 'TEST-3'])
        self.assertEqual(actual[4]['books'], [])
        self.assertEqual(actual[4]['sources'], [])
        self.assertEqual(actual[4]['materials'], [])
        self.assertEqual(actual[4]['rows'], [])
        self.assertEqual(actual[4]['origin_counts'], {'human': 3, 'ai': 0, 'unknown': 1})
        self.assertEqual(actual[5]['rows'], ['TEST-7'])
        self.assertEqual(actual[5]['materials'], [{'book_key': 'TEST-d', 'count': 1, 'edition_count': 1}])

    @unittest.skipUnless(shutil.which('node'), 'Node is optional; required for reader JavaScript regression checks')
    def test_origin_categories_keep_unknown_and_preserve_source_history(self):
        records = [
            navigation_fixture(1, origin='publisher_human_workflow'),
            navigation_fixture(2, origin='human_translator_credited'),
            navigation_fixture(3, origin='publisher_human_workflow', ai=True),
            navigation_fixture(4, ai=False),
            navigation_fixture(5),
            navigation_fixture(6, current='human'),
            navigation_fixture(7, origin='publisher_human_workflow', ai=False, current='unknown'),
        ]
        legacy = [
            {'kind': 'legacy_source_document', 'translation_origin': 'publisher_human_workflow'},
            {'kind': 'legacy_source_document', 'current_policy': {'classification': 'unknown'}},
            {'kind': 'legacy_source_document', 'current_policy': {'classification': 'human'}},
        ]
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        filter_function = template.split('function applyFilters(){', 1)[1].split('$("query").addEventListener', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=input.records,names={},state={matches:[]},fields={query:{value:''},'language-filter':{value:''},'book-filter':{value:''},'source-filter':{value:''},'origin-filter':{value:''},'include-commentary':{checked:false}};
const $=id=>fields[id],render=()=>{};
const valueText = ''' + helpers + '''\nfunction applyFilters(){''' + filter_function + '''
const results=['','human','ai','unknown'].map(origin=>{fields['origin-filter'].value=origin;applyFilters();return state.matches.map(index=>records[index].id);});
process.stdout.write(JSON.stringify({results,categories:records.map(originLabel),legacy:input.legacy.map(legacyOrigin),records}));'''
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'records': records, 'legacy': legacy}),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual['records'], records)
        self.assertEqual(actual['categories'], ['Human', 'Human', 'AI', 'Human', 'Unknown', 'Human', 'Unknown'])
        self.assertEqual(actual['results'], [
            ['TEST-1', 'TEST-2', 'TEST-3', 'TEST-4', 'TEST-5', 'TEST-6', 'TEST-7'],
            ['TEST-1', 'TEST-2', 'TEST-4', 'TEST-6'], ['TEST-3'], ['TEST-5', 'TEST-7']])
        self.assertEqual(actual['legacy'], ['unknown', 'unknown', 'human'])

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
