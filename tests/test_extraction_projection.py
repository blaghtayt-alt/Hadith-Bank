"""Extraction metadata and citation fidelity checks using literal TEST records."""
import copy
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from material_registry import normalized_projection
from review_display_policy import review_badges


class ExtractionProjectionTests(unittest.TestCase):
    def setUp(self):
        self.material = {
            'language': 'fa', 'book_key': 'bukhari', 'edition': 'test-edition',
            'dataset_id': 'TEST-fa-source',
            'canonical_records_path': 'materials/test-source/records.jsonl',
            'source_file': 'materials/test-source/source.json', 'source_sha256': 'a' * 64,
            'source_descriptor': {'name': 'TEST source', 'format': 'json'},
            'publication': {'authorized': True, 'status': 'published_pending_review',
                            'independent_qc_asserted': False},
        }
        self.row = {
            'id': 'TEST:fa:quote-one', 'text': {'arabic': None, 'translation': 'TEST\nTEST'},
            'extraction': {'ocr_used': False, 'method': 'structured_json_quote_extraction', 'is_excerpt': True},
            'source': {'title': 'TEST', 'quote_locator': {'json_pointer': '/parts/0/text',
                       'character_start': 0, 'character_end': 9}},
            'number': {'in_book': 'TEST-1', 'canonical': None},
            'references': {'items': [{'book_key': 'bukhari', 'collection': 'Sahih al-Bukhari',
                            'number': 'TEST-1', 'scope': 'main_quote', 'source_citation': 'TEST'}]},
            'review': {'status': 'pending', 'independent_pro_qc': 'pending',
                       'release_status': 'private_candidate', 'certified_release_eligible': False},
            'ai_translation': 'unknown',
        }

    def test_digital_extraction_retains_quote_references_history_and_locator(self):
        original = copy.deepcopy(self.row)
        result = normalized_projection(self.row, self.material, 0)
        self.assertEqual(self.row, original)
        self.assertEqual(result['text_translation'], original['text']['translation'])
        self.assertEqual(result['references'], original['references'])
        self.assertEqual(result['number'], original['number'])
        self.assertEqual(result['source']['original_metadata'], original['source'])
        self.assertIs(result['extraction']['ocr_used'], False)
        self.assertEqual(result['extraction']['method'], original['extraction']['method'])
        self.assertIs(result['extraction']['is_excerpt'], True)
        self.assertIsNone(result['translation_provenance']['policy_path'])
        self.assertEqual(result['review']['independent_pro_qc'], 'pending')
        self.assertEqual(review_badges(result), [])

    def test_actual_ocr_keeps_its_review_requirement(self):
        self.row['extraction'] = {'ocr_used': True, 'method': 'tesseract_ocr'}
        result = normalized_projection(self.row, self.material, 0)
        self.assertIs(result['extraction']['ocr_used'], True)
        self.assertEqual(review_badges(result), [{'label': 'OCR review: pending', 'pending': True}])
        self.assertIs(result['review']['certified_release_eligible'], False)

    def test_malformed_ocr_metadata_is_rejected(self):
        for value in ('false', 0, [], {}):
            with self.subTest(value=value):
                self.row['extraction']['ocr_used'] = value
                with self.assertRaisesRegex(ValueError, 'ocr_used'):
                    normalized_projection(self.row, self.material, 0)

    def test_search_schema_accepts_registered_persian_language(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / 'schemas/search.record.schema.json').read_text())
        language = schema['properties']['language']
        self.assertNotIn('enum', language)
        for code in ('fa', 'ja', 'fil', 'vi', 'zh-CN', 'uz', 'hi'):
            self.assertIsNotNone(re.fullmatch(language['pattern'], code))


if __name__ == '__main__':
    unittest.main()
