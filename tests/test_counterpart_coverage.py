"""Availability must describe what a reader can actually read or open."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from counterpart_coverage import availability_for, build_report, write_reports
from test_reader import READER_SNAPSHOT_JS


def samples():
    # Synthetic placeholders, not fabricated religious source text.
    return [
        {'id': 'TEST1', 'source_id': 'source-A', 'language': 'fa', 'text_arabic': 'TEST Arabic',
         'counterparts': {'status': 'unresolved', 'arabic': None, 'english': None}},
        {'id': 'TEST2', 'source_id': 'source-A', 'language': 'zh-CN', 'counterparts': {
            'arabic': {'text': 'TEST Arabic'}, 'english': {'text': 'TEST English'}}},
        {'id': 'TEST3', 'source_id': 'source-B', 'language': 'fa', 'text_arabic': 'TEST source Arabic',
         'counterparts': {'status': 'reviewed_parallel', 'english': {'text': None,
             'scope': 'external_source', 'source_url': 'https://example.invalid/TEST'}}},
        {'id': 'TEST4', 'source_id': 'source-C', 'language': 'ja', 'text_arabic': '  ',
         'counterparts': {'english': {'text': None, 'scope': 'external_source',
                                    'source_url': 'javascript:TEST()'}}},
        {'id': 'TEST5', 'source_id': 'source-D', 'language': 'en-US', 'text_translation': 'TEST English source'},
        {'id': 'TEST6', 'source_id': 'source-B', 'language': 'fa', 'text_arabic': 'TEST retained Arabic',
         'counterparts': {'status': 'unresolved', 'match_method': 'stale_reviewed_source',
                          'arabic': None, 'english': None}},
    ]


class CounterpartCoverageTests(unittest.TestCase):
    def test_unresolved_and_stale_links_do_not_hide_original_arabic(self):
        records = samples()
        for index in (0, 5):
            self.assertEqual(availability_for(records[index]), {'arabic': 'text', 'english': 'missing'})
        self.assertEqual(availability_for(records[4]), {'arabic': 'missing', 'english': 'text'})

    def test_text_links_and_missing_languages_are_independent(self):
        records = samples()
        before = copy.deepcopy(records)
        report = build_report(records)
        self.assertEqual(report['totals'], {
            'total': 6, 'arabic_text': 4, 'arabic_link': 0, 'arabic_available': 4,
            'english_text': 2, 'english_link': 1, 'english_available': 3,
            'missing_arabic': 2, 'missing_english': 3, 'both_text': 1,
            'both_available': 2, 'arabic_only': 2, 'english_only': 1, 'neither_available': 1,
        })
        self.assertEqual(report['by_source']['source-B']['counts']['english_link'], 1)
        self.assertEqual(report['by_source']['source-B']['counts']['missing_english'], 1)
        self.assertEqual(report['by_language']['fa']['missing_english'], 2)
        self.assertEqual(records, before)

    def test_url_without_explicit_external_scope_is_not_an_available_language(self):
        record = {'counterparts': {'english': {'source_url': 'https://example.invalid/TEST'}}}
        self.assertEqual(availability_for(record)['english'], 'missing')
        record['counterparts']['english'].update(scope='external_source', source_url='https://user:secret@example.invalid/TEST')
        self.assertEqual(availability_for(record)['english'], 'missing')
        record['counterparts']['english']['source_url'] = 'https://example.invalid/TEST'
        self.assertEqual(availability_for(record)['english'], 'external_link')

    def test_future_source_language_appears_without_a_hardcoded_book_list(self):
        with tempfile.TemporaryDirectory() as directory:
            record = {'id': 'TEST7', 'source_id': 'future-TEST', 'language': 'TEST-language',
                      'book_key': 'new-collection', 'text_arabic': 'TEST Arabic'}
            report = write_reports(directory, [record])
            self.assertEqual(report['by_language']['TEST-language']['total'], 1)
            self.assertEqual(report['by_source']['future-TEST']['counts']['missing_english'], 1)
            saved = json.loads((Path(directory) / 'reports/counterpart-availability.json').read_text())
            self.assertEqual(saved, report)
            markdown = (Path(directory) / 'reports/counterpart-availability.md').read_text()
            self.assertIn('future-TEST', markdown)
            self.assertIn('Missing English', markdown)
            self.assertIn('counterpart-review/manifest.json', markdown)

    @unittest.skipUnless(shutil.which('node'), 'Node required for reader filter parity')
    def test_reader_filter_distinguishes_text_external_and_missing(self):
        records = samples()
        template = (Path(__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = READER_SNAPSHOT_JS + "const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};\nconst valueText = " + helpers + '''
const choices=['','both-text','both-available','arabic-text','english-text','english-link','missing-arabic','missing-english','neither'];
process.stdout.write(JSON.stringify({states:records.map(counterpartAvailability),matches:choices.map(choice=>records.filter(record=>matchesCounterpartAvailability(record,choice)).map(record=>record.id))}));
'''
        run = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(records),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        self.assertEqual(actual['states'], [availability_for(record) for record in records])
        self.assertEqual(actual['matches'], [
            ['TEST1', 'TEST2', 'TEST3', 'TEST4', 'TEST5', 'TEST6'], ['TEST2'], ['TEST2', 'TEST3'],
            ['TEST1', 'TEST2', 'TEST3', 'TEST6'], ['TEST2', 'TEST5'], ['TEST3'],
            ['TEST4', 'TEST5'], ['TEST1', 'TEST4', 'TEST6'], ['TEST4'],
        ])


if __name__ == '__main__':
    unittest.main()
