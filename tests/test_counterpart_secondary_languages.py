"""Secondary-source binding regressions; synthetic alignments use TEST text only."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_deenhindi
from counterpart_review import (canonical, load_source_records, object_hash, source_binding,
                                source_text, text_hash, validate_source_binding)
from prepare_counterpart_review import prepare_review
from register_material import register
from reviewed_counterparts import ReviewedCounterpartResolver
from web_source_reviews import SourceReviews
import test_counterpart_review_workflow as workflow


class ActualSecondarySourceRegression(unittest.TestCase):
    def test_malik_1057_queues_its_actual_reviewed_urdu_without_filling_primaries(self):
        fixture_path = Path(__file__).parent / 'fixtures/deenhindi-malik-1057-secondary-source.json'
        fixture_bytes = fixture_path.read_bytes()
        fixture = json.loads(fixture_bytes)
        saved = fixture['saved']
        before_saved = copy.deepcopy(saved)
        self.assertEqual(saved['source_record']['textArabic'], '')
        self.assertEqual(saved['source_record']['translationEnglish'], '')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger = root / import_deenhindi.IMPORT / 'reviews/source-review-regression.json'
            import_deenhindi.write_json(ledger, {'schema': 'hadith-bank-web-source-review-v1',
                'site': 'deenhindi', 'records': [fixture['decision']]})
            reviews = SourceReviews(root, 'deenhindi')
            row, action = reviews.apply(import_deenhindi.canonical_record(saved), saved=saved)
            reviews.finish()
            self.assertEqual(action, 'register')
            self.assertEqual(row['text'], {'arabic': None, 'translation': None})
            self.assertEqual([v['language'] for v in row['language_versions'] if v['text']], ['ur'])
            source_dir = root / 'materials/secondary-source-regression'
            source_dir.mkdir(parents=True)
            # The test material explicitly names the frozen review fixture as
            # its local source; it does not fabricate the missing HTML bytes.
            (source_dir / 'saved-review-fixture.json').write_bytes(fixture_bytes)
            (source_dir / 'records.jsonl').write_bytes(canonical(row) + b'\n')
            register(root, 'materials/secondary-source-regression', row['language'], row['book_key'],
                     row['edition'], 'Frozen Malik 1057 software regression fixture',
                     'records.jsonl', 'saved-review-fixture.json')
            record = load_source_records(root)[0]
            before_record = copy.deepcopy(record)
            before_files = {p: p.read_bytes() for p in source_dir.iterdir() if p.is_file()}
            result = prepare_review(root, 'generated-review', records=[record])
            from counterpart_review import read_rows
            queue = read_rows((root / 'generated-review/queue.jsonl.gz').read_bytes(), compressed=True)
            self.assertEqual(result['queued_occurrences'], 1)
            self.assertEqual(result['accepted_by_this_preparation'], 0)
            item = queue[0]
            self.assertEqual(item['source_text_field'], 'language_versions:deenhindi-malik:1057:ur')
            self.assertEqual(item['source_language_version_id'], 'deenhindi-malik:1057:ur')
            self.assertEqual(item['source_text_language'], 'ur')
            self.assertEqual(item['language'], 'hi')
            urdu = next(v for v in record['language_versions'] if v['language'] == 'ur')
            self.assertEqual(len(urdu['text']), 224)
            self.assertEqual(item['source_preview'], urdu['text'][:240])
            self.assertEqual(item['source_text_sha256'], text_hash(urdu['text']))
            self.assertEqual(item['source_language_version_sha256'], object_hash(urdu))
            self.assertEqual(item['requested_languages'], ['arabic', 'english'])
            self.assertEqual(item['candidates'], [])
            self.assertIsNone(record['text_arabic'])
            self.assertIsNone(record['text_translation'])
            self.assertEqual(record, before_record)
            self.assertEqual(saved, before_saved)
            self.assertEqual({p: p.read_bytes() for p in before_files}, before_files)
            for version in record['language_versions']:
                if version['language'] != 'ur':
                    self.assertIsNone(version['text'])
                    self.assertEqual(len(version['comments']), 1)


class SecondaryBindingContracts(unittest.TestCase):
    def setUp(self):
        self.fixture = workflow.CounterpartReviewWorkflowTests(methodName='test_small_bank_without_counterpart_assets_and_new_source_id')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base_review = self.fixture.review()
        row = self.fixture.canonical_rows[0]
        row['text'] = {'arabic': None, 'translation': None}
        row['language_versions'] = [{'id': row['id'] + ':ur', 'language': 'ur',
            'text': workflow.TEXT, 'scope': 'source_excerpt', 'quotation_status': 'bounded',
            'source': {'name': 'TEST independently supplied secondary reading'},
            'comments': [{'text': 'TEST retained compiler context', 'scope': 'source_context_not_narration'}]}]
        self.fixture.register_source(replace=True)
        self.record = load_source_records(self.fixture.root)[0]
        self.fixture.record = self.record
        self.field = 'language_versions:TEST-occurrence-one:ur'

    def review(self):
        decision = copy.deepcopy(self.base_review)
        decision.update(source_binding(self.record, self.field))
        decision['review']['evidence'][0]['source_field'] = self.field
        return decision

    def test_secondary_binding_compiles_and_runtime_validation_retains_whole_field_metadata(self):
        self.fixture.prepare(include_targets=['raw-abu-dawud:42'])
        before = copy.deepcopy(self.record)
        result = self.fixture.compile([self.review()])
        self.assertEqual(result['verified'], 1)
        resolver = ReviewedCounterpartResolver(self.fixture.root)
        linked = resolver.for_record(self.record)
        self.assertEqual(linked['status'], 'reviewed_parallel')
        self.assertEqual(linked['quotation_evidence']['field'], self.field)
        self.assertEqual(linked['quotation_evidence']['source_text_language'], 'ur')
        self.assertEqual(linked['quotation_evidence']['source_language_version_id'], 'TEST-occurrence-one:ur')
        self.assertEqual(self.record, before)
        self.assertIsNone(self.record['text_arabic'])
        self.assertIsNone(self.record['text_translation'])
        self.fixture.prepare(include_resolved=True)
        candidate = next(c for c in self.fixture.queue_rows()[0]['candidates'] if c['score'] == 100)
        self.assertIn('same_occurrence_binding_previously_reviewed', candidate['reasons'][0])
        for mutation in ('text', 'language', 'comments', 'id', 'duplicate', 'missing'):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.record)
                version = changed['language_versions'][0]
                if mutation == 'text': version['text'] += ' TEST changed'
                elif mutation == 'language': version['language'] = 'en'
                elif mutation == 'comments': version['comments'][0]['text'] += ' TEST changed context'
                elif mutation == 'id': version['id'] += '-changed'
                elif mutation == 'duplicate': changed['language_versions'].append(copy.deepcopy(version))
                elif mutation == 'missing': changed['language_versions'] = []
                value = resolver.for_record(changed)
                self.assertEqual(value['match_method'], 'stale_reviewed_source_binding')
                self.assertIsNone(value['arabic'])
                self.assertIsNone(value['english'])

    def test_context_or_absent_field_cannot_be_substituted_for_a_quotation(self):
        for mutation in ('null', 'context_scope', 'pending_status', 'empty_versions'):
            with self.subTest(mutation=mutation):
                record = copy.deepcopy(self.record)
                if mutation == 'null': record['language_versions'][0]['text'] = None
                elif mutation == 'context_scope': record['language_versions'][0]['scope'] = 'source_context'
                elif mutation == 'pending_status': record['language_versions'][0]['quotation_status'] = 'attribution_pending'
                else: record['language_versions'] = []
                with self.assertRaises(ValueError): source_binding(record)
        # Explicit old-field reviews never silently switch to a secondary field.
        with self.assertRaisesRegex(ValueError, 'no source text'):
            source_binding(self.record, 'text_translation')
        with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
            source_text(self.record, 'language_versions:TEST-absent')

    def test_version_identity_language_and_whole_version_hash_are_required(self):
        binding = source_binding(self.record)
        for key in ('source_language_version_id', 'source_text_language', 'source_language_version_sha256'):
            with self.subTest(key=key):
                missing = dict(binding)
                del missing[key]
                with self.assertRaisesRegex(ValueError, 'Stale review source binding'):
                    validate_source_binding(self.record, missing)
        self.fixture.prepare(include_targets=['raw-abu-dawud:42'])
        decision = self.review()
        decision['review']['evidence'][0]['source_field'] = 'text_translation'
        with self.assertRaisesRegex(ValueError, 'no source text'):
            self.fixture.compile([decision], check_only=True)


if __name__ == '__main__':
    unittest.main()
