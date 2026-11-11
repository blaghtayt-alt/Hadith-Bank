"""Synthetic TEST counterparts; no fixture is a religious quotation."""
import base64
import copy
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
import hadith_search as searcher
from counterpart_display import counterpart_citation, counterpart_qualification, counterpart_alignment_notes
import test_reader as reader_fixtures
import test_hadith_search as search_fixtures


def counterparts():
    def item(language, value, citation):
        return {'text': value, 'citation': citation,
                'references': [{'book_key': 'muslim', 'collection': 'TEST Sahih Muslim',
                                'collection_ar': 'مرجع تجريبي مسلم', 'number': '١٢٣',
                                'numbering_scheme': 'INTERNAL-NUMBERING-MARKER', 'scope': 'main_quote'}],
                'source_name': 'TEST source', 'source_url': 'https://example.invalid/TEST',
                'source_snapshot': 'INTERNAL-SNAPSHOT-MARKER',
                'text_sha256': hashlib.sha256(value.encode()).hexdigest(),
                'match_status': 'related_version' if language == 'english' else 'exact',
                'scope': 'full_narration', 'translation_origin': 'human'}
    return {'status': 'linked', 'match_method': 'TEST', 'match_note': 'INTERNAL-MATCH-NOTE',
            'arabic': item('arabic', 'نَصٌّ تَجْرِيبِيٌّ لِلبَحْثِ', '[مرجع تجريبي مسلم ١٢٣]'),
            'english': item('english', 'TEST counterpart-only phrase\n<script>TEST</script>', '[TEST Sahih Muslim 123]')}


class CounterpartReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'catalog').mkdir()
        (self.root / 'search').mkdir()
        self.record = reader_fixtures.fixture()
        self.record['counterparts'] = counterparts()
        self.record['record_type'] = 'hadith_excerpt'
        self.output = self.root / 'reader.html'

    def build(self):
        raw = (json.dumps(self.record, ensure_ascii=False) + '\n').encode()
        (self.root / 'search/records.jsonl').write_bytes(raw)
        catalog = {'search': {'records_path': 'search/records.jsonl', 'records_sha256': hashlib.sha256(raw).hexdigest(), 'count': 1},
                   'materials': [], 'counterparts': {'total': 1, 'arabic_available': 1, 'english_available': 1}}
        (self.root / 'catalog/materials.json').write_text(json.dumps(catalog))
        reader.build(self.root, self.output)
        return self.output.read_text()

    def test_embedding_and_markdown_preserve_original_and_counterpart_bytes(self):
        before = copy.deepcopy(self.record)
        document = self.build()
        payload = re.search(r'<script id="hadith-records"[^>]*>(.*?)</script>', document, re.S).group(1)
        records = json.loads(gzip.decompress(base64.b64decode(payload)))
        self.assertEqual(records, [before])
        self.assertIn('id="show-english"', document)
        self.assertIn('even when hidden', document)
        markdown = reader.markdown_record(self.record, 1)
        self.assertIn('Arabic source text', markdown)
        self.assertIn('نَصٌّ تَجْرِيبِيٌّ لِلبَحْثِ', markdown)
        self.assertIn('[مرجع تجريبي مسلم ١٢٣]', markdown)
        self.assertIn('[TEST Sahih Muslim 123]', markdown)
        self.assertIn('counterpart-only phrase<br>\n&lt;script&gt;TEST&lt;/script&gt;', markdown)
        self.assertIn('Related publisher version:', markdown)
        self.assertIn('Full narration; the selected source preserves an excerpt', markdown)
        self.assertIn('Translation origin: Human', markdown)
        self.assertIn('Translation origin:</strong> Unknown', markdown)
        self.assertEqual(self.record, before)

    def test_unknown_number_never_uses_provider_entry_id(self):
        data = {'text': 'TEST', 'provider_entry_id': '987654321', 'references': []}
        self.assertEqual(counterpart_citation(data, 'english'), '[Collection and hadith number not supplied]')
        self.assertNotIn('987654321', counterpart_citation(data, 'arabic'))
        data['references'] = [{'collection': 'TEST source', 'number': None}]
        self.assertEqual(counterpart_citation(data, 'english'), '[TEST source · number not supplied]')

    def test_quality_advisory_survives_withheld_english_and_keeps_review_notes(self):
        message = 'TEST English withheld: <script>unsafe markup</script> is a source discrepancy.'
        values = self.record['counterparts']
        values.update(status='exact', english=None, quality_advisories=[{'message': message}, {'message': ' '}, None])
        before = copy.deepcopy(self.record)
        self.assertEqual(counterpart_alignment_notes(self.record), [message])
        page = reader.markdown_record(self.record, 1)
        self.assertIn('TEST English withheld:', page)
        self.assertIn('&lt;script&gt;unsafe markup&lt;/script&gt;', page)
        self.assertNotIn('<script>unsafe markup</script>', page)
        self.assertNotIn('English · full narration', page)
        self.assertEqual(self.record, before)
        values.update(status='reviewed_parallel', quotation_evidence={'review': {
            'human_review': False, 'qualifications': ['TEST previous scope limitation']}})
        notes = counterpart_alignment_notes(self.record)
        self.assertEqual(notes[0], message)
        self.assertIn('TEST previous scope limitation', notes)
        self.assertTrue(any('automated assistant' in note for note in notes))

    @unittest.skipUnless(shutil.which('node'), 'Node is required for display parity')
    def test_quality_advisory_javascript_parity_and_search_exclusion(self):
        message = 'TEST-WITHHELD-ADVISORY source text discrepancy.'
        self.record['counterparts'].update(status='exact', english=None,
            quality_advisories=[{'message': message}, {'message': ' '}, None])
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = "const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};const valueText = " + helpers + "\nprocess.stdout.write(JSON.stringify({notes:counterpartAlignmentNotes(records[0]),key:primarySearchKey(records[0])}));"
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps([self.record]),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual['notes'], counterpart_alignment_notes(self.record))
        self.assertNotIn('test-withheld-advisory', actual['key'])

    def test_unsafe_counterpart_source_link_is_not_rendered(self):
        self.record['counterparts']['english']['source_url'] = 'javascript:TEST'
        self.assertNotIn('href="javascript:', reader.markdown_record(self.record, 1))

    def test_quotation_evidence_qualifies_an_unflagged_source_excerpt(self):
        self.record['record_type'] = self.record['content_kind'] = 'hadith'
        self.record['extraction'] = {'is_excerpt': False}
        self.record['counterparts']['quotation_evidence'] = {
            'field': 'text_arabic', 'relation': 'source_excerpt'}
        before = copy.deepcopy(self.record)
        note = 'Full narration; the selected source preserves an excerpt or reported meaning.'
        for language in ('arabic', 'english'):
            self.assertIn(note, counterpart_qualification(
                self.record['counterparts'][language], self.record))
        self.assertIn(note, reader.markdown_record(self.record, 1))
        self.assertEqual(self.record, before)

        self.record['counterparts']['quotation_evidence']['relation'] = 'normalized_exact'
        self.assertNotIn(note, counterpart_qualification(
            self.record['counterparts']['english'], self.record))

    @unittest.skipUnless(shutil.which('node'), 'Node is required for search parity')
    def test_hidden_counterparts_and_digits_are_searchable_without_internal_metadata(self):
        self.record['record_type'] = self.record['content_kind'] = 'hadith'
        self.record['extraction'] = {'is_excerpt': False}
        self.record['counterparts']['quotation_evidence'] = {
            'field': 'text_arabic', 'relation': 'source_excerpt'}
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));const records=input.records,names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify({keys:records.map(primarySearchKey),queries:input.queries.map(q=>fold(q,false)),
 citations:['arabic','english'].map(lang=>counterpartCitation(records[0].counterparts[lang],lang)),
 notes:['arabic','english'].map(lang=>counterpartQualification(records[0].counterparts[lang],records[0])),records}));'''
        queries = ['counterpart-only phrase', 'نص تجريبي للبحث', 'muslim ١٢٣', 'muslim ۱۲۳',
                   'مرجع تجريبي مسلم 123', 'INTERNAL-SNAPSHOT-MARKER', 'INTERNAL-MATCH-NOTE',
                   'INTERNAL-NUMBERING-MARKER']
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'records': [self.record], 'queries': queries}),
                                text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        key = actual['keys'][0]
        matches = [all(term in key for term in query.split()) for query in actual['queries']]
        self.assertEqual(matches, [True, True, True, True, True, False, False, False])
        python_key = searcher._keys(self.record)[0]
        self.assertEqual([all(searcher._fold(term) in python_key for term in q.split()) for q in queries], matches)
        self.assertEqual(actual['records'], [self.record])
        for i, language in enumerate(('arabic', 'english')):
            data = self.record['counterparts'][language]
            self.assertEqual(actual['citations'][i], counterpart_citation(data, language))
            self.assertEqual(actual['notes'][i], counterpart_qualification(data, self.record))

    def test_cli_retrieval_and_json_keep_counterpart_provenance(self):
        case = search_fixtures.HadithSearchTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        first = case.records[0]
        first['counterparts'] = counterparts()
        first['record_type'] = 'hadith_excerpt'
        case.save()
        for query in ('counterpart-only phrase', 'نص تجريبي للبحث', 'muslim ۱۲۳'):
            result = case.call(query)
            self.assertEqual(result['matched'], 1)
            self.assertEqual(result['results'][0]['counterparts'], first['counterparts'])
            self.assertEqual(result['results'][0]['text_translation'], first['text_translation'])
        for query in ('INTERNAL-SNAPSHOT-MARKER', 'INTERNAL-MATCH-NOTE', 'INTERNAL-NUMBERING-MARKER'):
            self.assertEqual(case.call(query)['matched'], 0)
        human = searcher.format_results(case.call('counterpart-only phrase'))
        self.assertIn('English counterpart:', human)
        self.assertIn('[TEST Sahih Muslim 123]', human)
        self.assertIn('Related publisher version:', human)
        self.assertIn('Counterpart translation origin: Human', human)


if __name__ == '__main__':
    unittest.main()
