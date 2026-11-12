"""Exact saved Urdu regression and explicitly synthetic grouped-report fixtures."""
import copy
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader
import import_fawaz_bulk as importer
from build_discovery import render_language_reading
from language_display import language_readings
from language_versions import language_search_values, quotation_parts
from validate_fawaz_sources import SourceAudit, verify_partition, verify_report_components
import test_fawaz_bulk as bulk_fixtures
from test_language_readings import multilingual_fixture
from test_reader import READER_SNAPSHOT_JS


ROOT = Path(__file__).resolve().parents[1]


def synthetic_grouped_report():
    """TEST strings are not religious source quotations."""
    passages = ['TEST A: first report.', 'TEST B: second report.',
                'TEST C: opening passage 🧪.', 'TEST final passage.']
    text = ('TEST opening context. ' + passages[0] + ' TEST between reports. ' +
            passages[1] + passages[2] + '[TEST-INTERNAL-GLOSS]' + passages[3] + ' TEST ending context.')
    spans = [[text.index(value), text.index(value) + len(value)] for value in passages]
    groups = [[spans[0]], [spans[1]], spans[2:]]
    speakers = [{'name_as_supplied': name, 'role': role,
                 'source_spans': [[spans[index][0] + 5, spans[index][0] + 6]]}
                for index, (name, role) in enumerate([('A', 'companion'), ('B', 'successor'), ('C', 'other')])]
    decision = {'provider_book': 'bukhari', 'provider_edition': 'eng-bukhari', 'typed_hadithnumber': '1',
                'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': spans,
                'source_report_count': 3, 'source_report_groups': groups,
                'report_type': 'mixed_attributed_reports', 'reported_speakers': speakers,
                'report_classification_note': 'TEST Three separately attributed reports; the final report has two passages.',
                'report_component_classifications': [
                    {'spans': group, 'report_type': kind, 'reported_speakers': [speaker]}
                    for group, kind, speaker in zip(groups,
                        ['companion_report', 'successor_report', 'attributed_saying'], speakers)]}
    return text, passages, decision


def reading_source(decision, evidence):
    return {'source_report_count': decision['source_report_count'],
            'source_report_groups': copy.deepcopy(decision['source_report_groups']),
            'text_spans': copy.deepcopy(evidence)}


class GroupedReportTests(unittest.TestCase):
    def test_saved_urd_malik18_has_three_reports_four_passages_and_exact_gloss(self):
        saved = json.loads((ROOT / 'reports/fawaz-import-review/continuation-20261113/'
                           'urd-malik18-grouped-decision.json').read_text())
        text, decision = saved['source_text'], saved['decision']
        self.assertEqual(importer.sha(text.encode()),
                         '7b43220ff383f97d9b899493ed572d14ffdbd36b7d6a72a3e352c13ace34cda9')
        quotation, notes, evidence = importer.apply_reviewed_span(text, decision)
        self.assertEqual(len(text), 381)
        self.assertEqual(decision['source_report_groups'], [[[0, 80]], [[80, 209]], [[209, 306], [320, 381]]])
        self.assertEqual(notes, [text[306:320]])
        self.assertEqual(notes[0], 'یعنی رکعت پائی')
        self.assertEqual(importer.sha(quotation.encode()), decision['quotation_sha256'])
        self.assertNotIn(notes[0], quotation)
        verify_partition(text, evidence, quotation, notes)
        self.assertEqual(verify_report_components(text, reading_source(decision, evidence),
                         'multiple_source_reports'), (3, 0))
        version = {'text': quotation, 'source': reading_source(decision, evidence),
                   'quotation_status': 'multiple_source_reports'}
        parts = quotation_parts(version)
        self.assertEqual(len(parts), 3)
        self.assertEqual([len(part['passages']) for part in parts], [1, 1, 2])
        self.assertTrue(parts[2]['passages'][1]['gap_before'])

    def test_invalid_grouping_or_comment_speaker_evidence_is_rejected(self):
        text, _, valid = synthetic_grouped_report()
        invalid = []

        def change(label, mutate):
            decision = copy.deepcopy(valid)
            mutate(decision)
            invalid.append((label, decision))

        change('count', lambda d: d.update(source_report_count=4))
        change('missing quotation coverage', lambda d: d['quotation_spans'].pop())
        change('group order', lambda d: d['source_report_groups'].reverse())
        change('empty group', lambda d: d['source_report_groups'].append([]))
        change('bounding envelopes', lambda d: d.update(source_report_boundaries=[
            [group[0][0], group[-1][1]] for group in d['source_report_groups']]))
        change('missing group attribution', lambda d: d['report_component_classifications'].pop())
        change('duplicate group attribution', lambda d: d['report_component_classifications'].append(
            copy.deepcopy(d['report_component_classifications'][0])))
        change('legacy component envelope', lambda d: d['report_component_classifications'][2].update(
            span=[d['source_report_groups'][2][0][0], d['source_report_groups'][2][-1][1]]))
        change('no report type', lambda d: d.pop('report_type'))

        def overlap(d):
            d['source_report_groups'][2][1][0] = d['source_report_groups'][2][0][1] - 1
            d['quotation_spans'] = [span for group in d['source_report_groups'] for span in group]

        change('overlap', overlap)
        comment_start = text.index('TEST-INTERNAL-GLOSS')
        change('speaker from intervening note', lambda d: d['report_component_classifications'][2].update(
            reported_speakers=[{'name_as_supplied': 'TEST-INTERNAL-GLOSS', 'role': 'other',
                                'source_spans': [[comment_start, comment_start + len('TEST-INTERNAL-GLOSS')]]}]))
        for label, decision in invalid:
            with self.subTest(label=label), self.assertRaises(ValueError):
                importer.apply_reviewed_span(text, decision)

        quotation, notes, evidence = importer.apply_reviewed_span(text, valid)
        info = reading_source(valid, evidence)
        for label, mutate in [
            ('nested count', lambda value: value['text_spans'].update(source_report_count=4)),
            ('nested groups', lambda value: value['text_spans']['source_report_groups'].pop()),
            ('nested envelope', lambda value: value['text_spans'].update(source_report_boundaries=[[0, len(text)]])),
            ('double assignment', lambda value: value['text_spans'].update(
                retained_internal_citation_spans=[valid['quotation_spans'][0]])),
            ('missing source group', lambda value: value.pop('source_report_groups')),
            ('lost note', lambda value: value['text_spans']['notes'].pop()),
        ]:
            malformed = copy.deepcopy(info)
            mutate(malformed)
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify_report_components(text, malformed, 'multiple_source_reports')
        with self.assertRaises(ValueError):
            verify_report_components(text, info, 'disjoint_source_spans')
        verify_partition(text, evidence, quotation, notes)

    def test_import_and_source_audit_preserve_groups_and_exclude_comments_from_matn_search(self):
        case = bulk_fixtures.FawazBulkTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        text, passages, decision = synthetic_grouped_report()
        inputs = case.inputs()
        for prefix in case.plan['languages']:
            inputs['editions/' + prefix + '-bukhari.json'] = importer.encoded(
                bulk_fixtures.source_data('bukhari', [bulk_fixtures.row(1, 'TEST ' + prefix + ' source context.')]))
        inputs['editions/eng-bukhari.json'] = importer.encoded(
            bulk_fixtures.source_data('bukhari', [bulk_fixtures.row(1, text)]))
        importer.save_json(case.root, 'catalog/fawaz-reviewed-spans.json', {
            'schema': 'hadith-bank-fawaz-reviewed-spans-v1', 'repository': importer.REPOSITORY,
            'revision': importer.REVISION, 'decisions': [decision]})
        case.seed(inputs)
        summary, _ = importer.run(case.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        canonical = next(json.loads(line) for path in (case.root / 'materials').glob('*/records.jsonl')
                         for line in path.read_text().splitlines())
        own = next(item for item in canonical['language_versions'] if item['language'] == 'en')
        self.assertEqual(own['text'], ''.join(passages))
        self.assertEqual(own['source']['source_report_groups'], decision['source_report_groups'])
        self.assertEqual(own['source']['report_component_classifications'], decision['report_component_classifications'])
        self.assertEqual(own['quotation_status'], 'multiple_source_reports')
        self.assertNotIn('TEST-INTERNAL-GLOSS', json.dumps(list(language_search_values(canonical))))
        self.assertIn('TEST-INTERNAL-GLOSS', json.dumps(list(language_search_values(canonical, include_comments=True))))
        audit = SourceAudit(case.root).run()
        self.assertEqual(audit['status'], 'passed')
        self.assertEqual(audit['verified_source_report_components'], 3)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser parity')
    def test_browser_and_static_rendering_keep_three_labels_four_passages_and_comment_gap(self):
        text, passages, decision = synthetic_grouped_report()
        quotation, notes, evidence = importer.apply_reviewed_span(text, decision)
        record = multilingual_fixture()
        version = record['language_versions'][1]
        version.update(text=quotation, quotation_status='multiple_source_reports',
                       comments=[{'text': note, 'scope': 'source_compiler_note'} for note in notes])
        version['source'].update(reading_source(decision, evidence))
        before = copy.deepcopy(record)
        template = (ROOT / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = READER_SNAPSHOT_JS + '''const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify({views:languageReadings(records[0]),
 key:primarySearchKey(records[0]),notes:annotationSearchKey(records[0])}));'''
        run = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps([record]),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        views = language_readings(record)
        self.assertEqual(actual['views'], views)
        self.assertNotIn('test-internal-gloss', actual['key'])
        self.assertIn('test-internal-gloss', actual['notes'])
        own = next(item for item in views if item['language'] == 'en')
        self.assertEqual([part['label'] for part in own['quotation_parts']],
                         ['Source report 1', 'Source report 2', 'Source report 3'])
        self.assertEqual([passage['text'] for part in own['quotation_parts'] for passage in part['passages']], passages)
        self.assertIn('3 separately attributed reports', own['qualification'])
        self.assertIn('Intervening source text is retained under Comments.', own['qualification'])
        page = render_language_reading(own)
        self.assertEqual(page.count('class="text quotation"'), 4)
        for passage in passages:
            self.assertIn(html.escape(passage), page)
        self.assertNotIn(html.escape(passages[2] + passages[3]), page)
        self.assertNotIn('Source report 4', page)
        self.assertIn('Intervening source text is retained under Comments.', page)
        markdown = reader.markdown_record(record, 1)
        self.assertIn('Source report 3', markdown)
        self.assertNotIn(html.escape(passages[2] + passages[3]), markdown)
        self.assertEqual(record, before)


if __name__ == '__main__':
    unittest.main()
