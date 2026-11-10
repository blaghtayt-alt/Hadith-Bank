"""Regression checks for omitted JSONL text and fail-closed source integrity.

Fixtures retain real source text from the repository; no religious text is invented.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import search_hadeethenc

spec = importlib.util.spec_from_file_location('legacy_bank_search', ROOT / 'scripts/search.py')
legacy_search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_search)


class SearchIntegrityRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = json.loads((ROOT / 'datasets/hadeethenc/collections.json').read_text(encoding='utf-8'))
        cls.collection = next(c for c in registry['collections'] if c['language'] == 'ja')
        with (ROOT / cls.collection['records_path']).open(encoding='utf-8') as stream:
            cls.records = [json.loads(next(stream)), json.loads(next(stream))]

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.data_path = self.root / self.collection['records_path']
        self.data_path.parent.mkdir(parents=True)
        self.index_path = self.root / 'datasets/hadeethenc/collections.json'
        self.index_path.parent.mkdir(parents=True)
        self.write_records(self.records)

    def write_records(self, records):
        data = b''.join(json.dumps(row, ensure_ascii=False).encode('utf-8') + b'\n' for row in records)
        self.data_path.write_bytes(data)
        self.specification = dict(self.collection, count=len(records), bytes=len(data),
                                  records_sha256=hashlib.sha256(data).hexdigest())
        self.write_registry()

    def write_registry(self):
        self.index_path.write_text(json.dumps({'collections': [self.specification]}), encoding='utf-8')

    def test_real_jsonl_narration_is_found_with_the_query_in_excerpt(self):
        query = 'アブー・フライラ（アッラーのご満悦あれ）は言った'
        result = legacy_search.fulltext_search(ROOT, query, language='ja', limit=20)
        matches = [row for row in result['results'] if row['path'].endswith('records.jsonl')]
        self.assertEqual(len(matches), 4)
        self.assertTrue(all(query in row['excerpt'] for row in matches))

    def test_filters_and_returned_source_text_remain_exact(self):
        record = self.records[0]
        result = search_hadeethenc.search(self.root, language='ja', entry_id=record['source_entry_id'], limit=1)
        self.assertEqual(result['matched'], 1)
        hit = result['results'][0]
        self.assertEqual(hit['arabic'], record['texts']['arabic_verbatim'])
        self.assertEqual(hit['translation'], record['texts']['translation_verbatim'])
        self.assertEqual(hit['ai_translation'], record['ai_translation'])
        self.assertEqual(hit['release_status'], record['review']['release_status'])
        self.assertFalse(hit['certified_release_eligible'])
        self.assertEqual(result['integrity']['collections'][0]['count'], 2)

    def test_corruption_after_first_matching_record_is_rejected(self):
        self.data_path.write_bytes(self.data_path.read_bytes().rstrip(b'\n') + b' \n')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            search_hadeethenc.search(self.root, language='ja', entry_id=self.records[0]['source_entry_id'], limit=1)

    def test_wrong_declared_byte_count_and_record_count_are_rejected(self):
        for field in ('bytes', 'count'):
            with self.subTest(field=field):
                self.specification[field] += 1
                self.write_registry()
                with self.assertRaisesRegex(ValueError, 'count mismatch'):
                    search_hadeethenc.search(self.root, language='ja', limit=0)
                self.specification[field] -= 1

    def test_escaping_source_path_is_rejected(self):
        self.specification['records_path'] = '../outside.jsonl'
        self.write_registry()
        with self.assertRaisesRegex(ValueError, 'Unsafe collection path'):
            search_hadeethenc.search(self.root)

    def test_warning_uses_recorded_ai_and_qc_fields(self):
        records = copy.deepcopy(self.records)
        for row in records:
            row['ai_translation'] = False
        self.write_records(records)
        result = search_hadeethenc.search(self.root, limit=1)
        self.assertNotIn('origin is unknown', result['warning'])
        self.assertIn('ai_translation=false', result['warning'])
        self.assertIn('pending', result['warning'])
        self.assertFalse(result['results'][0]['certified_release_eligible'])

    def test_missing_integrity_metadata_cannot_bypass_verification(self):
        original = dict(self.specification)
        for field in ('records_sha256', 'bytes', 'count'):
            with self.subTest(field=field):
                self.specification = dict(original)
                del self.specification[field]
                self.write_registry()
                with self.assertRaisesRegex(ValueError, 'Missing/invalid'):
                    search_hadeethenc.search(self.root, limit=0)

    def test_older_private_manifest_hash_is_checked(self):
        self.index_path.unlink()
        self.index_path = self.root / 'collections.json'
        del self.specification['records_sha256']
        del self.specification['bytes']
        self.write_registry()
        manifest = self.data_path.parent / 'manifest.json'
        manifest.write_text(json.dumps({'coverage': {
            'records_sha256': hashlib.sha256(self.data_path.read_bytes()).hexdigest(),
        }}), encoding='utf-8')
        result = search_hadeethenc.search(self.root, limit=1)
        self.assertEqual(result['matched'], 2)
        self.assertFalse(result['integrity']['collections'][0]['expected_bytes_verified'])
        self.data_path.write_bytes(self.data_path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Blank JSONL line|SHA-256 mismatch'):
            search_hadeethenc.search(self.root, limit=1)

    def test_current_review_waiver_does_not_bypass_integrity(self):
        policy = self.root / 'catalog/review-policy.json'
        policy.parent.mkdir()
        policy.write_text(json.dumps({
            'schema': 'hadith-bank-review-policy-v1',
            'hadeethenc': {
                'decision': 'owner_waived_separate_bank_review',
                'separate_bank_review_required': False,
            },
        }), encoding='utf-8')
        self.assertIn('not required by owner', search_hadeethenc.search(self.root)['warning'])
        self.data_path.write_bytes(self.data_path.read_bytes().rstrip(b'\n') + b' \n')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            search_hadeethenc.search(self.root, limit=0)


if __name__ == '__main__':
    unittest.main()
