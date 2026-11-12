"""Verify the published Filipino projection against its preserved reconstruction.

These checks establish software routing and exact source-text preservation.
They do not authenticate narrations or perform a new independent PDF review.
"""
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_reader import source_downloads
from current_provenance import classification
from language_display import language_readings
from material_registry import (SOURCE_IMPORT_DECISION, normalized_projection,
                               publication, require_reader_visibility)
from resolve_counterparts import CounterpartResolver
from review_display_policy import review_badges


SLUG = 'fil-hisn-muslim-3e409dd7'
MATERIAL = ROOT / 'materials' / SLUG
IMPORT = ROOT / 'imports/filipino-hisn-reconstructed-20261112'
SOURCE_JSON = IMPORT / 'reconstruction/data/corrected_all_records.json.gz'
SOURCE_HASH = '9607d998949390d4608af9355e40fe24186fcf04c0ff1fd26cc7df95a78bb3d7'
PDF_HASH = '3e409dd7266c2a150645ecfea548f266edf80c9c5df5129aa8df7a977d248a07'
METADATA_HASH = '8e28533cc1353b8d862924bf132ab0e37c55480ab71e469ddf856a1a923140bd'
INDEPENDENT_IDS = {
    'N007', 'N118', 'N129', 'N130', 'N145', 'N160', 'N161', 'N168',
    'N177', 'N225', 'N232', 'U-P171-01', 'U-P185-01', 'U-P188-01',
}
QURAN_AUTHOR_IDS = {
    'QC-U-P014-Q01', 'QC-U-P014-Q02', 'QC-U-P014-Q03',
    'QC-U-P015-Q01', 'U-P100-Q01', 'N135',
}
UNRESOLVED_IDS = {'N015', 'N083', 'U-P100-01', 'U-P114-01', 'N214'}
NARRATION_ONLY_IDS = {
    'U-P039-01', 'U-P043-01', 'U-P044-01', 'N024', 'N026', 'U-P089-01',
    'U-P100-02', 'U-P103-01', 'U-P105-01', 'U-P110-01', 'U-P111-01',
    'U-P112-01', 'U-P118-01', 'U-P118-02', 'U-P122-01', 'U-P123-01',
    'U-P123-02', 'U-P123-03', 'U-P124-01', 'U-P127-01', 'U-P127-02',
    'U-P130-01', 'U-P133-01', 'U-P136-01', 'U-P136-02', 'U-P138-01',
    'N110', 'U-P144-01', 'U-P145-01', 'U-P169-01', 'U-P169-02',
    'U-P170-01', 'U-P176-01', 'U-P212-01',
}
MISSING_ARABIC_IDS = NARRATION_ONLY_IDS | {
    'U-P189-01', 'U-P189-02', 'U-P217-01', 'U-P239-01', 'U-P267-01',
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


class FilipinoHisnSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = gzip.decompress(SOURCE_JSON.read_bytes())
        cls.source = json.loads(cls.source_bytes)
        cls.original = {row['record_id']: row for row in cls.source['records']}
        cls.rows = rows(MATERIAL / 'records.jsonl')
        cls.by_original = {row['source']['original_record_id']: row for row in cls.rows}
        cls.non_hadith = rows(ROOT / 'non-hadith' / SLUG / 'records.jsonl')
        cls.unresolved = rows(ROOT / 'unclassified' / SLUG / 'records.jsonl')
        cls.manifest = json.loads((MATERIAL / 'manifest.json').read_text(encoding='utf-8'))
        cls.metadata = json.loads((IMPORT / 'reconstruction/data/book_metadata.json').read_text(encoding='utf-8'))
        relative = (MATERIAL / 'manifest.json').relative_to(ROOT).as_posix()
        cls.material = {
            'adapter': cls.manifest['adapter'], 'dataset_id': cls.manifest['source_id'],
            'language': cls.manifest['language'], 'book_key': cls.manifest['book'],
            'edition': cls.manifest['edition'],
            'canonical_records_path': cls.manifest['records']['path'],
            'source_file': cls.manifest['source']['path'],
            'source_sha256': cls.manifest['source']['sha256'],
            'source_descriptor': cls.manifest['source'],
            'publication': publication(cls.manifest, relative),
            'counterpart_policy': cls.manifest['counterpart_policy'],
        }
        cls.projected = [normalized_projection(row, cls.material, index)
                         for index, row in enumerate(cls.rows)]
        cls.projected_by_original = {
            row['source']['original_metadata']['original_record_id']: row
            for row in cls.projected
        }

    def test_exact_source_pdf_metadata_and_reconstruction_bytes(self):
        self.assertEqual(len(self.source_bytes), 23_099_110)
        self.assertEqual(sha(self.source_bytes), SOURCE_HASH)
        pdf = (ROOT / self.manifest['source']['path']).read_bytes()
        self.assertEqual(len(pdf), 5_321_887)
        self.assertEqual(sha(pdf), PDF_HASH)
        self.assertEqual(self.manifest['source']['sha256'], PDF_HASH)
        metadata = (IMPORT / 'reconstruction/data/book_metadata.json').read_bytes()
        self.assertEqual(sha(metadata), METADATA_HASH)
        self.assertEqual(self.manifest['records']['sha256'],
                         sha((MATERIAL / 'records.jsonl').read_bytes()))

    def test_323_source_records_1500_components_and_493_candidates_are_preserved(self):
        self.assertEqual(len(self.original), 323)
        self.assertEqual(sum(len(row['components']) for row in self.original.values()), 1500)
        roles = [role for row in self.original.values()
                 for role in row['content_classification_reconstructed_v2']['component_roles']]
        self.assertEqual(len(roles), 1500)
        self.assertEqual(sum(role['preserved_prior_candidate'] for role in roles), 493)
        reconstruction = self.source['reconstruction_v2']
        self.assertEqual(reconstruction['source_wording_changes'], 0)
        self.assertEqual(reconstruction['separate_independent_final_evaluation'], 'NOT_RUN')

    def test_298_reader_records_and_25_exclusions_form_a_disjoint_exhaustive_partition(self):
        self.assertEqual([len(self.rows), len(self.non_hadith), len(self.unresolved)], [298, 20, 5])
        self.assertEqual(self.manifest['records']['count'], 298)
        hidden = self.non_hadith + self.unresolved
        hidden_ids = [item['original_source_record']['record_id'] for item in hidden]
        self.assertEqual(set(hidden_ids), INDEPENDENT_IDS | QURAN_AUTHOR_IDS | UNRESOLVED_IDS)
        self.assertEqual(Counter([*self.by_original, *hidden_ids]), Counter(self.original.keys()))
        self.assertEqual({item['original_source_record']['record_id'] for item in self.unresolved},
                         UNRESOLVED_IDS)
        for item in hidden:
            original = item['original_source_record']
            self.assertEqual(original, self.original[original['record_id']])
            self.assertFalse(item.get('visible_in_hadith_html',
                                      item.get('show_in_html_hadith', True)))
        for original_id in self.by_original:
            decision = self.original[original_id]['content_classification_reconstructed_v2']
            self.assertEqual(decision['record_partition'], 'hisn_hadith_dhikr_context')
        self.assertIn('U-P100-02', self.by_original)
        self.assertNotIn('U-P100-01', self.by_original)

    def test_source_scoped_occurrence_ids_and_unapproved_canonical_numbers(self):
        self.assertEqual(len({row['id'] for row in self.rows}), 298)
        for original_id, row in self.by_original.items():
            self.assertEqual(row['id'], SLUG + ':' + original_id)
            self.assertEqual(row['source_locator']['source_record_sha256'],
                             self.original[original_id]['record_source_sha256'])
            self.assertIsNone(row['number']['canonical'])
            self.assertEqual(row['language'], 'fil')
            self.assertEqual(row['book_key'], 'hisn-al-muslim')

    def test_each_display_span_is_exact_and_all_source_narration_is_reachable(self):
        essential_types = {'narration', 'translation', 'quran_translation', 'transliteration'}
        for original_id, row in self.by_original.items():
            with self.subTest(record=original_id):
                components = self.original[original_id]['components']
                by_id = {component['segment_id']: component for component in components}
                sequence = row['source_locator']['display_sequences']['fil']
                text = row['text']['translation']
                cursor = 0
                segment_ids = []
                for index, span in enumerate(sequence):
                    component = by_id[span['segment_id']]
                    if index:
                        self.assertEqual(text[cursor:span['display_start_codepoint']], '\n\n')
                    else:
                        self.assertEqual(span['display_start_codepoint'], 0)
                    start, end = span['display_start_codepoint'], span['display_end_codepoint']
                    self.assertEqual(text[start:end], component['text'])
                    self.assertEqual(span['source_text_sha256'], sha(component['text'].encode()))
                    self.assertEqual(span['source_type'], component['type'])
                    self.assertGreater(end, start)
                    cursor = end
                    segment_ids.append(span['segment_id'])
                self.assertEqual(cursor, len(text))
                self.assertEqual(len(segment_ids), len(set(segment_ids)))
                source_positions = {component['segment_id']: index for index, component in enumerate(components)}
                self.assertEqual([source_positions[key] for key in segment_ids],
                                 sorted(source_positions[key] for key in segment_ids))
                expected = [component['segment_id'] for component in components
                            if component['type'] in essential_types]
                self.assertEqual([key for key in segment_ids if by_id[key]['type'] in essential_types], expected)

    def test_n262_dialogue_and_inline_n227_n231_context_keep_source_order(self):
        expected = {
            'N262': ['p266-r003', 'p266-r004', 'p266-r005', 'p267-r002',
                     'p267-r003', 'p267-r004', 'p267-r005'],
            'N227': ['p237-r004', 'p237-r005', 'p237-r006', 'p237-r007', 'p237-r008'],
            'N231': ['p240-r002', 'p240-r004', 'p240-r005', 'p240-r006',
                     'p240-r007', 'p240-r009', 'p240-r010', 'p240-r012'],
        }
        for original_id, segment_ids in expected.items():
            with self.subTest(record=original_id):
                row = self.by_original[original_id]
                actual = [part['segment_id'] for part in row['source_locator']['display_sequences']['fil']]
                self.assertEqual(actual, segment_ids)

    def test_all_34_narration_only_records_remain_readable(self):
        actual = {key for key in self.by_original if self.original[key]['translation'] is None}
        self.assertEqual(actual, NARRATION_ONLY_IDS)
        for original_id in NARRATION_ONLY_IDS:
            row = self.by_original[original_id]
            self.assertTrue(row['text']['translation'].strip())
            for component in self.original[original_id]['components']:
                if component['type'] == 'narration':
                    self.assertIn(component['text'], row['text']['translation'])

    def test_no_external_arabic_fills_the_39_missing_pdf_arabic_texts(self):
        missing = {key for key, row in self.by_original.items() if row['text']['arabic'] is None}
        self.assertEqual(missing, MISSING_ARABIC_IDS)
        for original_id, row in self.by_original.items():
            self.assertEqual(row['text']['arabic'], self.original[original_id]['arabic'])
            supplied = [item for item in row['language_versions'] if item['language'] == 'ar']
            self.assertEqual(len(supplied), 0 if original_id in missing else 1)
            if supplied:
                self.assertEqual(supplied[0]['text'], self.original[original_id]['arabic'])
            self.assertNotIn('en', {item['language'] for item in row['language_versions']})
            self.assertNotIn('external_narration_evidence', row)

    def test_named_human_translation_and_unresolved_edition_metadata_remain_honest(self):
        self.assertEqual(self.metadata['translation_identity']['translator_as_printed'],
                         'ABDULKHALIQ SHARIF SARIPADA')
        self.assertIsNone(self.metadata['exact_edition_publication_year'])
        self.assertIsNone(self.metadata['exact_edition_publication_date'])
        self.assertEqual(self.metadata['extent']['actual_pdf_pages'], 276)
        self.assertEqual(self.metadata['extent']['catalogue_extent_numeric'], 280)
        for row in self.projected:
            self.assertEqual(row['translator']['name'], 'ABDULKHALIQ SHARIF SARIPADA')
            self.assertIs(row['ai_translation'], False)
            self.assertEqual(classification(row), 'human')
            # The saved source history establishes visual comparison, not a blanket OCR flag.
            self.assertIsNone(row['extraction']['ocr_used'])

    def test_public_source_import_is_available_without_claiming_independent_certification(self):
        self.assertTrue(self.manifest['publication']['authorized'])
        self.assertEqual(self.manifest['publication']['decision'], SOURCE_IMPORT_DECISION)
        for row in self.projected:
            self.assertEqual(row['publication']['status'], 'published_source_import')
            self.assertEqual(row['publication']['visibility'], 'public')
            self.assertFalse(row['publication']['independent_qc_asserted'])
            self.assertEqual(row['review']['status'], 'source_imported')
            self.assertEqual(row['review']['release_status'], 'source_imported')
            self.assertEqual(row['review']['independent_pro_qc'], 'NOT_RUN')
            self.assertFalse(row['review']['certified_release_eligible'])
            self.assertEqual(review_badges(row), [])
            self.assertNotIn('HOLD', ' '.join(item['label'] for item in review_badges(row)))
            require_reader_visibility(row)

    def test_normalization_keeps_own_language_citations_notes_and_no_alias_duplicates(self):
        for original_id, row in self.by_original.items():
            projected = self.projected_by_original[original_id]
            original_snapshot = copy.deepcopy(row)
            normalized_projection(row, self.material, 0)
            self.assertEqual(row, original_snapshot)
            for original_version, version in zip(row['language_versions'], projected['language_versions'], strict=True):
                for key in ('id', 'language', 'text', 'source', 'references', 'comments', 'citation', 'match_status'):
                    self.assertEqual(version[key], original_version[key])
                self.assertEqual(version['match_status'], 'same_source_record')
                self.assertTrue(version['source']['name'])
                source_references = self.original[original_id].get('references') or []
                self.assertEqual([item['source_citation'] for item in version['references']],
                                 [item['reference_as_printed'] for item in source_references])
                for reference in source_references:
                    self.assertIn(reference['reference_as_printed'], version['citation'])
                for comment in version['comments']:
                    self.assertTrue(comment if isinstance(comment, str) else comment.get('text'))
            readings = language_readings(projected)
            self.assertEqual(len(readings), len(row['language_versions']))
            self.assertEqual(sum(item['language'] == 'fil' for item in readings), 1)
            for item in readings:
                self.assertEqual(item['translation_origin'], None if item['language'] == 'ar' else 'human')
            self.assertEqual(projected['source_locator'], row['source_locator'])

    def test_counterpart_opt_out_precedes_reviewed_and_automatic_matching(self):
        self.assertEqual(self.manifest['counterpart_policy']['mode'], 'disabled')
        resolver = CounterpartResolver.__new__(CounterpartResolver)
        resolver.enabled = True
        resolver.quality_policy = None
        resolver.reviewed = Mock()
        resolver.reviewed.for_record.side_effect = AssertionError('Reviewed mapping must not be consulted')
        resolver._select = Mock(side_effect=AssertionError('Automatic matching must not be consulted'))
        for original_id in ('N039', 'N260', 'U-P100-02'):
            row = self.projected_by_original[original_id]
            self.assertEqual(row['counterpart_policy'], self.manifest['counterpart_policy'])
            original_arabic = row['text_arabic']
            result = resolver.for_record(row)
            self.assertEqual(result['match_method'], 'material_counterparts_disabled')
            self.assertIsNone(result['arabic'])
            self.assertIsNone(result['english'])
            self.assertEqual(row['text_arabic'], original_arabic)
        resolver.reviewed.for_record.assert_not_called()
        resolver._select.assert_not_called()

    def test_pdf_download_is_bound_to_the_preserved_local_file(self):
        downloads = source_downloads(ROOT, self.projected, {})
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]['path'], self.manifest['source']['path'])
        self.assertEqual(downloads[0]['sha256'], PDF_HASH)
        self.assertEqual(downloads[0]['bytes'], 5_321_887)
        self.assertEqual(downloads[0]['translation_origin'], 'human')


if __name__ == '__main__':
    unittest.main()
