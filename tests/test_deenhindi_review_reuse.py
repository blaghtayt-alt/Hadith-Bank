"""Source-identity, boundary and context guards for exact prior-review reuse."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from deenhindi_review_reuse import ExactReviewReuse, METHOD, sha
from import_deenhindi import canonical_record
from web_source_reviews import SourceReviews


class ExactPriorReviewReuseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.text = 'TEST narrated account. TEST compiler explanation.'
        self.stop = self.text.index(' TEST compiler')
        self.prior = {'provider_book': 'malik', 'provider_edition': 'eng-malik',
                      'typed_hadithnumber': '999.1', 'source_text_sha256': sha(self.text.encode()),
                      'quotation_spans': [[0, self.stop]],
                      'classification': 'source_attributed_prophetic_narration',
                      'decision_note': 'TEST exact report boundary, following explanation excluded.'}
        self.saved = {'collection': 'bukhari', 'number': '12a',
                      'source_record': {'translationEnglish': self.text,
                                        'textArabic': 'TEST unread Arabic sibling',
                                        'translationHindi': 'TEST unread Hindi sibling',
                                        'grade': 'TEST Deen-only grade', 'narrator': 'TEST Deen narrator'},
                      'source_reference_verbatim': '[TEST Deen reference12a]',
                      'parsed_path': 'TEST parsed evidence',
                      'snapshot': {'path': 'TEST source.html.gz', 'sha256': 'a' * 64,
                                   'url': 'https://deenhindi.com/hadith/bukhari/12a'},
                      'classification': {'classification': 'unknown'}}

    def engine(self, decisions=None):
        return ExactReviewReuse(self.root, decisions=decisions or [self.prior])

    def apply(self, engine):
        decision = engine.review(self.saved)
        receipt = engine.save()
        reviews = SourceReviews(self.root, 'deenhindi')
        reviews.decisions[decision['id']] = (decision, receipt, 'register')
        row, action = reviews.apply(canonical_record(self.saved), saved=self.saved)
        reviews.finish()
        self.assertEqual(action, 'register')
        return row

    def test_exact_reading_reuses_only_bounds_and_preserves_local_identity(self):
        original = canonical_record(self.saved)
        row = self.apply(self.engine())
        for key in ('id', 'number', 'references', 'grading', 'narrator', 'source', 'source_locator'):
            self.assertEqual(row[key], original[key], key)
        english = next(v for v in row['language_versions'] if v['language'] == 'en')
        self.assertEqual(english['text'], self.text[:self.stop])
        self.assertEqual(english['comments'][-1]['text'], self.text[self.stop:])
        self.assertEqual(english['source']['manual_review']['method'], METHOD)
        for v in row['language_versions']:
            if v['language'] != 'en':
                self.assertIsNone(v['text'])
                self.assertEqual(v['quotation_status'], 'attribution_pending')
        self.assertIsNone(row['text']['translation'])

    def test_number_match_and_partial_normalized_or_cross_language_text_do_not_qualify(self):
        for value in (self.text + ' ', self.text.lower(), self.text[:self.stop]):
            self.saved['source_record']['translationEnglish'] = value
            self.assertIsNone(self.engine().review(self.saved))
        self.saved['source_record']['translationEnglish'] = ''
        self.saved['source_record']['translationHindi'] = self.text
        self.assertIsNone(self.engine().review(self.saved))

    def test_pending_or_negative_decisions_are_never_positive_review(self):
        for action in ('source_context_only', 'source_attribution_pending'):
            prior = {**self.prior, 'action': action, 'quotation_spans': []}
            self.assertIsNone(self.engine([prior]).review(self.saved))

    def test_relative_prior_reference_cannot_establish_local_attribution(self):
        prior = {**self.prior, 'source_reference': {'parent_typed_hadithnumber': '998'}}
        engine = self.engine([prior])
        self.assertIsNone(engine.review(self.saved))
        self.assertEqual(len(engine.context_dependent), 1)

    def test_prepare_does_not_replace_existing_published_evidence(self):
        engine = self.engine()
        engine.review(self.saved)
        receipt = engine.save()
        path = self.root / receipt['path']
        original = path.read_bytes()
        engine.records.append({'TEST': 'new candidate only'})
        changed = engine.prepare()
        self.assertNotEqual(receipt['sha256'], changed['sha256'])
        self.assertEqual(path.read_bytes(), original)
        engine.commit()
        self.assertEqual(sha(path.read_bytes()), changed['sha256'])

    def test_inconsistent_prior_decisions_hold_the_field(self):
        second = {**self.prior, 'typed_hadithnumber': '2',
                  'quotation_spans': [[0, len(self.text)]]}
        engine = self.engine([self.prior, second])
        self.assertIsNone(engine.review(self.saved))
        self.assertEqual(len(engine.conflicts), 1)

    def test_multiple_passages_preserve_one_report_and_separate_context(self):
        text = 'TEST first. TEST note. TEST last.'
        self.saved['source_record']['translationEnglish'] = text
        spans = [[0, 11], [22, len(text)]]
        prior = {**self.prior, 'source_text_sha256': sha(text.encode()),
                 'quotation_spans': spans, 'source_report_count': 1,
                 'source_report_relationship': 'separate_passages_of_one_source_report',
                 'source_passage_boundaries': spans}
        row = self.apply(self.engine([prior]))
        english = next(v for v in row['language_versions'] if v['language'] == 'en')
        self.assertEqual(english['source']['source_report_count'], 1)
        self.assertEqual(english['source']['source_report_groups'], [spans])
        self.assertEqual(english['comments'][-1]['text'], text[11:22])

    def test_disjoint_passages_without_relationship_fail(self):
        prior = {**self.prior, 'quotation_spans': [[0, 5], [6, self.stop]]}
        with self.assertRaisesRegex(ValueError, 'explicit original report relationship'):
            self.engine([prior]).review(self.saved)

    def test_source_bound_speaker_metadata_is_preserved_and_validated(self):
        text = self.text
        prior = {**self.prior, 'classification': 'source_attributed_report_or_saying',
                 'report_type': 'historical_report',
                 'report_classification_note': 'TEST explicit historical account.',
                 'reported_speakers': [{'name_as_supplied': 'TEST', 'role': 'other', 'source_spans': [[0, 4]]}]}
        row = self.apply(self.engine([prior]))
        english = next(v for v in row['language_versions'] if v['language'] == 'en')
        self.assertEqual(english['source']['report_type'], 'historical_report')
        prior['reported_speakers'][0]['name_as_supplied'] = 'Invented'
        with self.assertRaisesRegex(ValueError, 'Speaker name'):
            self.engine([prior]).review(self.saved)

    def test_source_change_after_matching_fails_before_admission(self):
        engine = self.engine()
        decision = engine.review(self.saved)
        receipt = engine.save()
        reviews = SourceReviews(self.root, 'deenhindi')
        reviews.decisions[decision['id']] = (decision, receipt, 'register')
        self.saved['source_record']['translationEnglish'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'original source object changed'):
            reviews.apply(canonical_record(self.saved), saved=self.saved)

    def test_ledger_is_deterministic_and_contains_original_review_identity(self):
        engine = self.engine()
        engine.review(self.saved)
        receipt = engine.save()
        before = (self.root / receipt['path']).read_bytes()
        self.assertEqual(receipt, engine.save())
        self.assertEqual(before, (self.root / receipt['path']).read_bytes())
        doc = json.loads(gzip.decompress(before))
        evidence = doc['records'][0]['field_reviews'][0]['prior_review_evidence'][0]
        self.assertEqual(evidence['typed_hadithnumber'], '999.1')
        self.assertEqual(doc['records'][0]['number'], '12a')
        self.assertIsNone(doc['records'][0]['verified_external_reference'])

    def test_reuse_only_refresh_detects_missing_ledger_and_engine_change(self):
        import web_import_batch as batch
        from deenhindi_review_reuse import LEDGER_PATH
        engine = self.engine()
        engine.review(self.saved)
        receipt = engine.save()
        inputs = [{'path': 'TEST pinned input', 'sha256': 'f' * 64}]
        source_reviews = SourceReviews(self.root, 'deenhindi')
        progress = {'source_review_inputs': [receipt],
                    'source_review_engine_sha256': source_reviews.engine_sha256,
                    'exact_field_review_reuse': {'input_receipts': inputs, 'ledger': receipt}}
        with mock.patch('deenhindi_review_reuse.input_receipts', return_value=inputs), \
                mock.patch.object(batch, 'read_json', return_value=progress):
            self.assertFalse(batch.has_review_export_work(self.root, 'deenhindi'))
            progress['source_review_engine_sha256'] = 'changed engine'
            self.assertTrue(batch.has_review_export_work(self.root, 'deenhindi'))
            progress['source_review_engine_sha256'] = source_reviews.engine_sha256
            (self.root / LEDGER_PATH).unlink()
            self.assertTrue(batch.has_review_export_work(self.root, 'deenhindi'))


if __name__ == '__main__':
    unittest.main()
