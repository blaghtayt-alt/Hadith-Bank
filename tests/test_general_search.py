"""Regression checks for JSONL discovery, metadata search and review-policy overlays."""
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import search as general_search
import search_hadeethenc


class LocalSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.path = self.root / 'languages/ja/books/hadeethenc/editions/test/records.jsonl'
        self.path.parent.mkdir(parents=True)
        self.record = {
            'record_id': 'example:entry:1:translation:ja:revision:a',
            'occurrence_id': 'example:entry:1:translation:ja',
            'source_entry_id': '1',
            'language': 'ja',
            'title_verbatim': 'Fixture title',
            'texts': {'arabic_verbatim': 'نص المصدر', 'translation_verbatim': 'x' * 1600},
            'grading': {},
            'source_references': {'bibliography_verbatim': 'Distinct collection reference 123'},
            'publication': {
                'publisher': 'Example source archive',
                'translator': 'Maryam al-Miṣrī',
                'source_arabic_version': 1,
                'translation_version': None,
                'digital_snapshot_sha256': 'a' * 64,
            },
            'ai_translation': 'unknown',
            'arabic_alignment': {'status': 'source_version_unavailable'},
            'review': {
                'release_status': 'published_unreviewed_source_import',
                'independent_pro_qc': 'pending',
                'certified_release_eligible': False,
            },
            'topic_tags': [],
            'commentary': {'explanation': 'commentary-only-needle'},
            'source_row_verbatim': {'explanation': 'commentary-only-needle'},
        }
        self.path.write_text(json.dumps(self.record, ensure_ascii=False) + '\n', encoding='utf-8')
        registry = self.root / 'datasets/hadeethenc/collections.json'
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({'collections': [{
            'language': 'ja',
            'records_path': self.path.relative_to(self.root).as_posix(),
            'records_sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(),
            'bytes': self.path.stat().st_size,
            'count': 1,
        }]}), encoding='utf-8')

    def write_policy(self, policy):
        path = self.root / 'catalog/review-policy.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(policy), encoding='utf-8')

    def test_fulltext_finds_jsonl_metadata_and_shows_actual_unicode_match(self):
        result = general_search.fulltext_search(self.root, 'misri', language='ja')
        self.assertEqual(result['matched'], 1)
        hit = result['results'][0]
        self.assertEqual(hit['record_id'], self.record['record_id'])
        self.assertEqual(hit['line'], 1)
        self.assertIn('al-Miṣrī', hit['excerpt'])
        self.assertLess(len(hit['excerpt']), 500)

    def test_fulltext_keeps_legacy_formats_and_counts_beyond_result_limit(self):
        (self.path.parent / 'source.txt').write_text('Example source archive\n', encoding='utf-8')
        result = general_search.fulltext_search(self.root, 'Example source archive', limit=1)
        self.assertEqual(result['matched'], 2)
        self.assertEqual(result['shown'], 1)
        self.assertEqual(result['match_unit'], 'source_line')

    def test_hadeethenc_search_includes_source_translator_and_record_metadata(self):
        for query in ('misri', 'Example source archive', 'Distinct collection reference 123', self.record['record_id']):
            with self.subTest(query=query):
                result = search_hadeethenc.search(self.root, query=query)
                self.assertEqual(result['matched'], 1)
                self.assertEqual(result['results'][0]['translator'], 'Maryam al-Miṣrī')

    def test_commentary_remains_explicitly_opt_in(self):
        self.assertEqual(search_hadeethenc.search(self.root, 'commentary-only-needle')['matched'], 0)
        self.assertEqual(search_hadeethenc.search(self.root, 'commentary-only-needle', commentary=True)['matched'], 1)

    def test_current_waiver_does_not_change_historical_flags_or_source_bytes(self):
        original = self.path.read_bytes()
        baseline = search_hadeethenc.search(self.root)
        self.assertIn(search_hadeethenc.WARNING, baseline['warning'])
        self.assertIn('Recorded independent Pro QC status: pending', baseline['warning'])
        self.assertNotIn('current_review_policy', baseline)
        self.write_policy({
            'schema': 'hadith-bank-review-policy-v1',
            'hadeethenc': {
                'decision': 'owner_waived_separate_bank_review',
                'separate_bank_review_required': False,
                'independent_review_performed': False,
                'arabic_alignment_flags_retained': True,
            },
        })
        result = search_hadeethenc.search(self.root)
        self.assertIn('not required by owner', result['warning'])
        hit = result['results'][0]
        self.assertEqual(hit['historical_review'], self.record['review'])
        self.assertEqual(hit['release_status'], self.record['review']['release_status'])
        self.assertEqual(hit['ai_translation'], 'unknown')
        self.assertEqual(hit['arabic_alignment'], 'source_version_unavailable')
        self.assertFalse(hit['certified_release_eligible'])
        self.assertEqual(hit['independent_pro_qc'], 'pending')
        self.assertIn('Historical independent Pro QC status: pending', result['warning'])
        self.assertEqual(result['integrity']['collections'][0]['count'], 1)
        self.assertEqual(search_hadeethenc.search(self.root, approved_only=True)['matched'], 0)
        self.assertEqual(self.path.read_bytes(), original)

    def test_unrecognized_policy_cannot_suppress_historical_notice(self):
        base = {
            'schema': 'hadith-bank-review-policy-v1',
            'hadeethenc': {'decision': 'owner_waived_separate_bank_review', 'separate_bank_review_required': False},
        }
        cases = []
        policy = copy.deepcopy(base); policy['schema'] = 'unrecognized'; cases.append(policy)
        policy = copy.deepcopy(base); policy['hadeethenc']['decision'] = 'review_pending'; cases.append(policy)
        policy = copy.deepcopy(base); policy['hadeethenc']['separate_bank_review_required'] = True; cases.append(policy)
        policy = copy.deepcopy(base); policy['hadeethenc']['separate_bank_review_required'] = 'false'; cases.append(policy)
        for policy in cases:
            with self.subTest(policy=policy):
                self.write_policy(policy)
                result = search_hadeethenc.search(self.root)
                self.assertIn(search_hadeethenc.WARNING, result['warning'])
                self.assertNotIn('not required by owner', result['warning'])
                self.assertIn('Recorded independent Pro QC status: pending', result['warning'])
                self.assertNotIn('current_review_policy', result)


if __name__ == '__main__':
    unittest.main()
