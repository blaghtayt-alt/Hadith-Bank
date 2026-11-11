"""Replay the frozen Targhib quotations against the three original DOCX files.

These checks establish reproducible source extraction, not narrational
authenticity, a new translation, or independent scholarly certification.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import import_persian_targhib as intake


class PersianTarghibSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = ROOT / intake.IMPORT / 'extracted'
        font = intake.read_data(ROOT / intake.FONT_EVIDENCE)
        cls.paragraphs = {}
        cls.records = {}
        cls.main = {}
        cls.source_paths = {}
        for volume in (1, 2, 3):
            directory = ROOT / f'materials/fa-targhib-bazmandegan-v{volume}'
            source = directory / 'source.docx'
            cls.source_paths[volume] = source
            cls.paragraphs.update(intake.read_source(source, volume, font))
            cls.main[volume] = intake.read_data(cls.inputs / f'v{volume}-records.jsonl')
            cls.records[volume] = intake.read_data(directory / 'records.jsonl')
        cls.patch_input = intake.read_data(cls.inputs / 'inline-commentary-patches.json')
        cls.patches = intake.reviewed_patches(cls.patch_input, cls.paragraphs)
        cls.ancillary = intake.read_data(cls.inputs / 'ancillary-targhib.jsonl')
        cls.additional = intake.read_data(cls.inputs / 'additional-quotation-spans.json')
        cls.excluded = {item['id'] for item in intake.read_data(cls.inputs / 'excluded-source-units.json')}

    def test_original_documents_match_the_verified_source_hashes(self):
        for volume, path in self.source_paths.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), intake.SOURCE_HASHES[volume])

    def test_every_published_text_replays_from_selected_original_spans(self):
        all_ids = set()
        for volume in (1, 2, 3):
            expected = {}
            extra, _ = intake.additional_rows(self.additional, self.main[volume], self.ancillary, self.paragraphs, volume)
            for row in self.main[volume] + extra:
                if row['id'] in self.excluded:
                    continue
                text, _, _ = intake.materialize_main_text(row, self.paragraphs, self.patches)
                self.assertNotIn(row['id'], expected)
                expected[row['id']] = text
            for row in self.ancillary:
                if row['source_volume'] == volume:
                    text, _ = intake.materialize_ancillary_text(row, self.paragraphs)
                    self.assertNotIn(row['id'], expected)
                    expected[row['id']] = text
            actual = {row['id']: row['text'] for row in self.records[volume]}
            self.assertEqual(len(actual), len(self.records[volume]))
            self.assertFalse(all_ids & set(actual))
            all_ids.update(actual)
            self.assertEqual(actual, expected)

    def test_source_grades_and_unknown_canonical_numbers_are_preserved(self):
        for volume in (1, 2, 3):
            actual = {row['id']: row for row in self.records[volume]}
            for source in self.main[volume]:
                if source['id'] in self.excluded:
                    continue
                record = actual[source['id']]
                if source.get('source_grade'):
                    self.assertEqual(record['grading']['source_grade_as_printed'], source['source_grade'])
            for record in actual.values():
                self.assertIsNone(record['number']['canonical'])
                self.assertIsNone(record['grading'].get('independent_bank_grade'))
                self.assertTrue(any(record['text'].values()))
                if (record['number'].get('printed_labels') or {}).get('unified') == '0':
                    self.assertIsNone(record['number']['in_book'])

    def test_out_of_scope_sayings_remain_outside_the_hadith_payload(self):
        published = {record['id'] for rows in self.records.values() for record in rows}
        self.assertFalse(published & self.excluded)
        self.assertEqual(len(self.excluded), 11)

    def test_excluded_prose_never_returns_as_a_whole_main_paragraph(self):
        for volume in (1, 2, 3):
            decisions = intake.read_data(ROOT / intake.IMPORT / f'audit/v{volume}-ambiguity-decisions.json')
            prohibited = {row['paragraph_id'] for row in decisions
                          if row['classification'] in ('commentary', 'non_hadith_report', 'reference', 'cross_reference', 'heading')}
            for row in self.main[volume]:
                for spans in row['extraction_spans'].values():
                    self.assertFalse(prohibited & {span['paragraph_id'] for span in spans}, row['id'])
            for record in self.records[volume]:
                self.assertEqual(record['commentary'], {'arabic': None, 'translation': None})
                self.assertEqual(record['footnotes'], [])

    def test_changed_selected_source_bytes_are_rejected(self):
        row = copy.deepcopy(self.main[1][0])
        span = next(span for spans in row['extraction_spans'].values() for span in spans)
        span['raw_decoded_span'] += 'TEST'
        with self.assertRaisesRegex(AssertionError, 'Source-span mismatch'):
            intake.materialize_main_text(row, self.paragraphs, self.patches)

    def test_stale_comment_removal_source_is_rejected(self):
        patches = copy.deepcopy(self.patch_input)
        patches['patches'][0]['source_text'] += 'TEST'
        with self.assertRaisesRegex(AssertionError, 'Inline-patch source differs'):
            intake.reviewed_patches(patches, self.paragraphs)

    def test_nested_comment_and_footnote_removals_do_not_delete_extra_text(self):
        text = 'TEST (TEST() TEST) TEST'
        outer = (text.index('('), text.rindex(')') + 1, '')
        inner = (text.index('()'), text.index('()') + 2, '')
        self.assertEqual(intake.apply_removals(text, [inner, outer]), 'TEST  TEST')

    def test_same_physical_quote_cannot_be_reimported_under_another_language(self):
        span = next(span for row in self.main[1] for span in row['extraction_spans']['arabic'])
        paragraph = self.paragraphs[span['paragraph_id']]['decoded']
        selection = {'paragraph_id': span['paragraph_id'], 'start': span['start'], 'end': span['end'],
                     'text': paragraph[span['start']:span['end']], 'language': 'fa',
                     'decoded_sha256': hashlib.sha256(paragraph.encode()).hexdigest()}
        extra, skipped = intake.additional_rows([selection], self.main[1], [], self.paragraphs, 1)
        self.assertEqual(extra, [])
        self.assertEqual(len(skipped), 1)

    def test_explicit_individual_grader_is_not_replaced_by_edition_credit(self):
        record = next(row for row in self.records[3]
                      if 'v3:document:p01892' in row['source_locator']['paragraph_ids'])
        self.assertEqual(record['grading']['grader'], 'الحاكم')
        self.assertEqual(record['grading']['source_grade_as_printed'], 'صحيح الإسناد')

    def test_footnote_symbols_are_separate_from_unresolved_source_glyphs(self):
        flagged = []
        for rows in self.records.values():
            for row in rows:
                self.assertNotIn('\uf020', ''.join(value or '' for value in row['text'].values()))
                if row['extraction']['unresolved_source_glyphs']:
                    flagged.append(row)
                    self.assertTrue(any('Unresolved original source font token' in note for note in row['source_defects']))
        self.assertEqual(len(flagged), 3)

    def test_source_translation_concerns_remain_visible_without_certification(self):
        qualified = []
        for records in self.records.values():
            for record in records:
                self.assertFalse(record['review']['certified_release_eligible'])
                self.assertEqual(record['review']['independent_pro_qc'], 'not_performed')
                self.assertFalse(record['extraction']['ocr_used'])
                self.assertFalse(record['extraction']['new_translation_produced'])
                if record.get('source_translation_qualifications'):
                    qualified.append(record)
                    self.assertTrue(any(x.startswith('Source translation qualification:') for x in record['review']['issues']))
                    self.assertEqual(len(record['review']['issues']), len(set(record['review']['issues'])))
        self.assertGreaterEqual(len(qualified), 3)

    def test_manifest_counts_and_checksums_cover_exact_canonical_files(self):
        for volume, records in self.records.items():
            directory = ROOT / f'materials/fa-targhib-bazmandegan-v{volume}'
            manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['records']['count'], len(records))
            self.assertEqual(manifest['records']['sha256'], intake.digest(directory / 'records.jsonl'))
            self.assertEqual(manifest['source']['sha256'], intake.SOURCE_HASHES[volume])
            self.assertTrue(manifest['publication']['authorized'])
            self.assertFalse(manifest['display_policy']['qc_tags'])


if __name__ == '__main__':
    unittest.main()
