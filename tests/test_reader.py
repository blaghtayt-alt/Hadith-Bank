"""Reader fixtures are synthetic; no fixture is a religious quotation."""
import base64
import gzip
import hashlib
import html
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
from review_display_policy import extraction_metadata, review_badges, text_direction


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
        self.assertNotIn('Published · independent review pending', document)
        self.assertEqual(metadata['review_display_policy']['scope'], 'ocr_only')
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
  review:input.review.map(record=>({pending:needsOCRReview(record),published:hasPublicAuthorization(record)})),
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
                      {'review': {'independent_pro_qc': 'passed'}},
                      {'review': {'independent_pro_qc': 'pending'},
                       'publication': {'visibility': 'public', 'authorized': True, 'status': 'published_source_import'},
                       'display_policy': {'qc_tags': False}}]}
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(sample),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        base = 'https://github.com/TEST/TEST/blob/' + 'a' * 40 + '/'
        self.assertEqual(actual['hosted'], base + 'attachments/TEST/TEST%20%23.pdf')
        self.assertEqual(actual['local'], 'attachments/TEST/TEST%20%23.pdf')
        self.assertEqual(actual['encoded'], base + '%252e%252e/TEST.pdf')
        self.assertEqual(actual['invalid'], [None] * len(sample['invalid']))
        self.assertEqual(actual['review'], [{'pending': False, 'published': True},
                                             {'pending': False, 'published': False},
                                             {'pending': False, 'published': False},
                                             {'pending': False, 'published': True}])
        self.assertEqual(actual['language'], 'Swahili')

    def test_extraction_evidence_is_separate_from_review_and_translation_origin(self):
        samples = [
            {'provenance': {'ocr_used': False, 'extraction_method': 'embedded_pdf_text_pymupdf'}},
            {'provenance': {'ocr_used': False, 'acquisition_method': 'official_digital_sqlite_export'}},
            {'extraction': {'method': 'digital_quote_extraction', 'ocr_used': False},
             'translation_provenance': {'origin': 'unknown'}},
            {'provenance': {'ocr_used': True, 'extraction_method': 'tesseract_ocr'}},
            {'extraction': {'method': 'embedded_pdf_text_with_ocr_fallback'}},
            {'source': {'format': 'pdf'}, 'review': {'issues': ['OCR review may be needed']}},
            {'extraction': {'method': 'native_pdf_text_without_ocr'}},
            {'provenance': {'ocr_used': False, 'extraction_method': 'tesseract_ocr'}},
        ]
        before = json.loads(json.dumps(samples))
        metadata = [extraction_metadata(record) for record in samples]
        self.assertEqual([item['ocr_used'] for item in metadata], [False, False, False, True, True, None, False, True])
        self.assertEqual(metadata[0]['evidence_fields'], ['provenance.ocr_used', 'provenance.extraction_method'])
        self.assertTrue(metadata[-1]['conflicting_evidence'])
        self.assertEqual(samples, before)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser-policy parity')
    def test_ocr_only_badges_match_python_and_preserve_historical_flags(self):
        records = []
        for index, method, used, status in [
            (1, 'embedded_pdf_text_pymupdf', False, 'pending'),
            (2, 'official_digital_sqlite_export', False, 'pending'),
            (3, 'digital_quote_extraction', False, 'pending'),
            (4, 'tesseract_ocr', True, 'pending'),
            (5, 'tesseract_ocr', True, 'passed'),
            (6, None, None, 'pending'),
        ]:
            item = navigation_fixture(index)
            item['extraction'] = extraction_metadata({'provenance': {'ocr_used': used, 'extraction_method': method}})
            item['review'] = {'status': 'initial_extraction_with_review_pending',
                              'independent_pro_qc': status, 'release_status': 'private_candidate'}
            item['publication'] = {'visibility': 'public', 'authorized': True, 'status': 'published_pending_review'}
            records.append(item)
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));const records=input,names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify({badges:records.map(reviewBadges),pending:records.filter(needsOCRReview).map(r=>r.id),records}));'''
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(records),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual['badges'], [review_badges(record) for record in records])
        self.assertEqual(actual['badges'][:3], [[], [], []])
        self.assertEqual(actual['badges'][3], [{'label': 'OCR review: pending', 'pending': True}])
        self.assertEqual(actual['pending'], ['TEST-4'])
        self.assertEqual(actual['records'], records)
        self.assertNotIn('Published · independent review pending', template)

    def test_markdown_hides_non_ocr_qc_but_keeps_original_history(self):
        record = navigation_fixture(1)
        record['extraction'] = {'ocr_used': False, 'method': 'digital_quote_extraction'}
        record['review'] = {'status': 'TEST_pending', 'independent_pro_qc': 'pending',
                            'release_status': 'private_candidate'}
        rendered = reader.markdown_record(record, 1)
        normal = re.sub(r'<details>.*?</details>', '', rendered, flags=re.S)
        self.assertNotIn('QC', normal)
        self.assertNotIn('private_candidate', normal)
        self.assertIn('Original import and review history', rendered)
        self.assertIn('TEST_pending', rendered)
        record['extraction']['ocr_used'] = True
        self.assertIn('<strong>OCR review: pending</strong>', reader.markdown_record(record, 1))

    @unittest.skipUnless(shutil.which('node'), 'Node is required for record-type browser parity')
    def test_source_classifications_distinguish_excerpts_and_companion_reports(self):
        classifications = [
            {'record_type': 'hadith', 'extraction': {'is_excerpt': False}},
            {'record_type': 'hadith', 'extraction': {'is_excerpt': True}},
            {'record_type': 'hadith_excerpt'},
            {'record_type': 'hadith_meaning_excerpt'},
            {'record_type': 'companion_report'},
            {'record_type': 'companion_report_excerpt'},
            {'content_kind': 'companion_report', 'extraction': {'is_excerpt': True}},
            {'content_kind': 'hadith'},
            {'record_type': 'unclassified'},
            {'record_type': '__proto__'},
            {},
            {'record_type': 'hadith_occurrence', 'content_kind': 'numbered_source_narration'},
            {'record_type': 'main_hadith_occurrence'},
            {'record_type': 'quoted_hadith', 'content_kind': 'quoted_hadith_excerpt'},
            {'record_type': 'hadith_quote'},
            {'record_type': 'quoted_companion_report'},
            {'record_type': 'companion_report', 'content_kind': 'quoted_companion_saying'},
            {'record_type': 'hadith_occurrence', 'content_kind': 'unnumbered_source_variant'},
            {'record_type': 'translation_occurrence', 'content_kind': 'source_fragment'},
        ]
        expected_labels = ['Hadith', 'Hadith excerpt', 'Hadith excerpt', 'Reported meaning',
                           'Companion report', 'Companion report', 'Companion report',
                           'Hadith', None, None, None,
                           'Hadith', 'Hadith', 'Hadith excerpt', 'Hadith excerpt',
                           'Companion report', 'Companion report', 'Hadith variant', 'Source fragment']
        before = json.loads(json.dumps(classifications))
        actual = [reader.record_type_info(record) for record in classifications]
        self.assertEqual([item['label'] if item else None for item in actual], expected_labels)
        self.assertNotIn('excerpt', actual[0]['note'].lower())
        self.assertNotIn('excerpt', actual[4]['note'].lower())
        self.assertIn('excerpt', actual[5]['note'].lower())
        for index, (classification, label) in enumerate(zip(classifications, expected_labels)):
            record = navigation_fixture(index)
            record.update(classification)
            rendered = reader.markdown_record(record, index)
            if label:
                self.assertIn('<strong>' + label + '</strong>', rendered)
            else:
                self.assertNotIn('<strong>Hadith', rendered)
                self.assertNotIn('<strong>Companion report', rendered)
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));const records=[],names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify(input.map(recordTypeInfo)));'''
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(classifications),
                                text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), actual)
        self.assertEqual(classifications, before)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for direction and citation browser checks')
    def test_persian_direction_and_scoped_references_are_readable(self):
        record = navigation_fixture(1, language='fa', book='muslim')
        record['source_language_code'] = 'fa'
        record['narrator'] = {'name': 'TEST narrator'}
        record['number'] = {'in_book': 'TEST-101', 'canonical': None}
        record['references'] = {'items': [
            {'book_key': 'muslim', 'collection': 'Sahih Muslim', 'number': 'TEST-101',
             'scope': 'main_quote', 'source_citation': 'TEST citation'},
            {'book_key': 'bukhari', 'collection': 'Sahih al-Bukhari', 'number': 'TEST-202',
             'scope': 'variant', 'source_citation': 'TEST variant citation'},
            {'book_key': 'unclassified', 'number': None, 'scope': 'unresolved',
             'source_citation': 'TEST unresolved citation'},
        ]}
        record['commentary'] = {'translation': 'TEST commentary'}
        self.save([record]);reader.build(self.root, self.output, compress=False)
        embedded, document = self.embedded_records()
        self.assertEqual(embedded, [record])
        metadata = json.loads(re.search(r'<script id="hadith-snapshot" type="application/json">(.*?)</script>',document,re.S).group(1))
        self.assertEqual(metadata['language_names']['fa'], 'Persian')
        rendered = reader.markdown_record(record, 1)
        self.assertIn('<p dir="rtl">TEST</p>', rendered)
        self.assertIn('<p dir="rtl">TEST commentary</p>', rendered)
        self.assertIn('Narrator:</strong> TEST narrator', rendered)
        self.assertIn('Sahih Muslim · TEST-101', rendered)
        self.assertIn('Reference to a variant', rendered)
        self.assertIn('Reference not fully resolved', rendered)
        helpers = document.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));const records=[],names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify({directions:input.languages.map(x=>textDirection(x)),references:input.references.map(citationData)}));'''
        languages=['fa','fa-IR','ur','ar','ja','vi']
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'languages':languages,'references':record['references']['items']}),
                                text=True,capture_output=True,check=True)
        actual=json.loads(result.stdout)
        self.assertEqual(actual['directions'],[text_direction(language) for language in languages])
        self.assertEqual(actual['directions'],['rtl','rtl','rtl','rtl','auto','auto'])
        self.assertEqual(actual['references'][0]['label'],'Sahih Muslim · TEST-101')
        self.assertEqual(actual['references'][1]['scope'],'Reference to a variant')
        self.assertEqual(actual['references'][2]['label'],'Collection not established · number not established')

    @unittest.skipUnless(shutil.which('node'), 'Node is required for citation browser parity checks')
    def test_plural_source_citations_preserve_scope_and_local_numbering(self):
        # Citation metadata observed on fa-faiz-al-bari-v1-p00705; the fixture
        # narration remains TEST and does not reproduce religious source text.
        scope = 'Exact terminal citation for this source narration; moved from reader text to metadata.'
        items = [
            {'collection': 'Sahih al-Bukhari', 'collection_id': 'sahih-al-bukhari',
             'number_raw': ['1'], 'numbers': ['1'], 'cross_reference_numbers': [],
             'citation_raw': '[رواه البخاری: 1].', 'citation_scope': scope,
             'status': 'as_cited_in_uploaded_source', 'externally_verified': False},
            {'collection': 'Sahih al-Bukhari', 'numbers': ['3741', '3740'],
             'cross_reference_numbers': ['TEST-CROSS-REFERENCE'],
             'citation_raw': 'TEST multiple citation', 'citation_scope': scope},
            {'collection': 'Sahih al-Bukhari', 'numbers': [],
             'number_raw': ['TEST-UNPARSED'], 'cross_reference_numbers': ['TEST-CROSS-REFERENCE'],
             'citation_raw': 'TEST unresolved <citation>', 'citation_scope': 'TEST exact_source scope'},
            {'collection': 'Sahih Muslim', 'number': 'TEST-101', 'numbers': ['TEST-OTHER'],
             'scope': 'variant', 'citation_scope': 'TEST alternate scope',
             'source_citation': 'TEST legacy citation', 'citation_raw': 'TEST alternate citation'},
            {'collection': None, 'numbers': ['TEST-11'], 'citation_raw': 'TEST unidentified collection'},
        ]
        expected = [
            {'label': 'Sahih al-Bukhari · 1', 'scope': scope, 'source_citation': '[رواه البخاری: 1].'},
            {'label': 'Sahih al-Bukhari · 3741, 3740', 'scope': scope,
             'source_citation': 'TEST multiple citation'},
            {'label': 'Sahih al-Bukhari · number not established', 'scope': 'TEST exact_source scope',
             'source_citation': 'TEST unresolved <citation>'},
            {'label': 'Sahih Muslim · TEST-101', 'scope': 'Reference to a variant',
             'source_citation': 'TEST legacy citation'},
            {'label': 'Collection not established · TEST-11', 'scope': 'Citation scope not supplied',
             'source_citation': 'TEST unidentified collection'},
        ]
        record = navigation_fixture(1, language='fa', book='bukhari')
        record['number'] = {'in_book': 'TEST-LOCAL-77', 'canonical': None,
                            'numbering_system': 'TEST source-local numbering'}
        record['references'] = {'items': items, 'canonical_mapping_status':
                                'Source citations preserved as printed; no independent canonical matching asserted.'}
        before = json.loads(json.dumps(record))
        self.save([record])
        reader.build(self.root, self.output, compress=False)
        embedded, document = self.embedded_records()
        self.assertEqual(embedded, [before])
        rendered = reader.markdown_record(record, 1)
        self.assertIn('Source number TEST-LOCAL-77', rendered)
        self.assertIn(record['references']['canonical_mapping_status'], rendered)
        for item, data in zip(items, expected):
            with self.subTest(label=data['label']):
                parts = '\n'.join(reader.citation_parts(item))
                self.assertIn('<strong>' + html.escape(data['label']) + '</strong>', parts)
                self.assertIn('<br>' + html.escape(data['scope']) + '</p>', parts)
                self.assertIn('<p dir="auto">' + html.escape(data['source_citation']) + '</p>', parts)
        helpers = document.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));const records=[],names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify({references:input.references.items.map(citationData),number:numberLabel(input),record:input}));'''
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(record),
                                text=True, encoding='utf-8', capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual['references'], expected)
        self.assertEqual(actual['number'], 'Source number TEST-LOCAL-77')
        self.assertEqual(actual['record'], before)
        self.assertEqual(record, before)

    def test_docx_reading_page_omits_qc_labels_but_keeps_source_notes(self):
        record = fixture()
        record['language'] = 'fa'
        record['text_translation'] = 'TEST'
        record['commentary'] = {'arabic': None, 'translation': None}
        record['display_policy'] = {'qc_tags': False}
        record['review']['issues'] = ['TEST source fragment']
        record['page']['docx_paragraphs'] = [10, 11]
        record['number'] = {'in_book': 'TEST-7', 'canonical': None,
                            'source_cited': ['TEST canonical citation'],
                            'numbering_system': 'Source-local abridgment numbering'}
        page = reader.markdown_record(record, 1)
        self.assertNotIn('Pro QC', page)
        self.assertNotIn('Historical import status', page)
        self.assertNotIn('Commentary and footnotes', page)
        self.assertIn('TEST source fragment', page)
        self.assertIn('DOCX paragraph 10, 11', page)
        self.assertIn('Source number TEST-7', page)
        self.assertIn('Cited: TEST canonical citation', page)

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
