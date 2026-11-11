"""Review tooling fixtures use literal TEST content, never invented hadith."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from counterpart_review import (RAW_ABU_BASE, canonical, load_source_records,
    raw_abu_dawud_targets, read_rows, selected_entry, source_binding,
    validate_language_decisions)
from prepare_counterpart_review import prepare_review
from compile_reviewed_counterparts import compile_reviews
from register_material import register
from reviewed_counterparts import MANIFEST, ReviewedCounterpartResolver


TEXT = 'TEST source quotation with sufficient distinctive words and exact preserved boundaries'


class CounterpartReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source_dir = self.root / 'materials/test-source'
        self.source_dir.mkdir(parents=True)
        self.canonical_rows = [{'id': 'TEST-occurrence-one', 'text': {
            'arabic': TEXT, 'translation': 'TEST original translation; no number identifies another occurrence.'},
            'source_locator': {'paragraph': 4}, 'number': {'source_entry_id': '42'}}]
        self.register_source()
        raw = canonical({'hadiths': [
            {'hadithnumber': 42, 'text': 'TEST target introduction. ' + TEXT + '. TEST target ending.'},
            {'hadithnumber': 43, 'text': 'TEST different source context. ' + TEXT + '. TEST distinct chain.'},
            {'hadithnumber': 44, 'text': ''}]})
        folder = self.root / RAW_ABU_BASE
        (folder / 'raw').mkdir(parents=True)
        (folder / 'raw/ara-abudawud.json.gz').write_bytes(gzip.compress(raw, mtime=0))
        (folder / 'provenance.json').write_bytes(canonical({'arabic_source': {
            'provider': 'TEST-source-provider', 'revision': 'TEST-snapshot',
            'url': 'https://example.invalid/TEST/immutable-source.json',
            'raw_sha256': hashlib.sha256(raw).hexdigest(), 'raw_bytes': len(raw)}}))
        self.records = load_source_records(self.root)
        self.record = self.records[0]
        self.queue = self.root / 'generated-review'
        self.reviews = self.root / 'decisions.jsonl'
        self.options = {'root': self.root, 'queue': self.queue, 'reviews': self.reviews,
            'bundle_id': 'test-source-alignment', 'snapshot': 'test-snapshot',
            'publication_basis': 'TEST owner authorization for this exact source scope'}

    def register_source(self, replace=False):
        (self.source_dir / 'records.json').write_bytes(canonical(self.canonical_rows))
        (self.source_dir / 'source.txt').write_text('TEST original source document\n' + TEXT)
        register(self.root, 'materials/test-source', 'sw', 'test-book', 'test-edition',
                 'TEST source', 'records.json', 'source.txt', replace=replace)

    def prepare(self, **kwargs):
        return prepare_review(self.root, self.queue, **kwargs)

    def queue_rows(self):
        return read_rows((self.queue / 'queue.jsonl.gz').read_bytes(), compressed=True)

    def review(self, record=None, target_key='raw-abu-dawud:42'):
        record = record or self.record
        targets, _ = raw_abu_dawud_targets(self.root)
        target = targets[target_key]
        return {**source_binding(record, 'text_arabic'), 'target_key': target_key,
            'target_entry_sha256': target['target_entry_sha256'], 'status': 'verified',
            'relation': 'source_excerpt', 'review': {'reviewer': 'TEST actual reviewer',
                'human_review': False, 'method': 'TEST source and target content comparison',
                'official_page_review': {'url': 'https://sunnah.com/abudawud:42',
                    'retrieved_date': 'TEST date', 'retrieval_reference': 'TEST fixture page check',
                    'english_compared': True},
                'evidence': [{'source_field': 'text_arabic', 'source_quote': TEXT,
                    'target_language': 'arabic', 'target_quote': TEXT,
                    'rationale': 'TEST manually checked content, context and quotation boundaries'}],
                'qualifications': ['TEST source is an excerpt of the target source entry']},
            'language_decisions': {
                'arabic': {'decision': 'approved_text', 'rationale': 'TEST exact target inspected'},
                'english': {'decision': 'approved_external', 'rationale': 'TEST external page inspected',
                    'reviewed_url': 'https://sunnah.com/abudawud:42',
                    'counterpart': {'text': None, 'text_sha256': None, 'scope': 'external_source',
                        'source_url': 'https://sunnah.com/abudawud:42',
                        'source_record_id': '42', 'source_name': 'TEST English source',
                        'source_snapshot': 'TEST page check', 'translation_origin': 'unknown',
                        'coverage': 'partial', 'citation_note': 'TEST page omits part of the source quote.',
                        'references': [{'book_key': 'abu-dawud', 'collection': 'TEST collection',
                            'number': '42', 'numbering_scheme': 'TEST page numbering', 'scope': 'main_quote'}]}}}}

    def save_reviews(self, values):
        self.reviews.write_bytes(b''.join(canonical(value) + b'\n' for value in values))

    def compile(self, decisions=None, **kwargs):
        if decisions is not None:
            self.save_reviews(decisions)
        return compile_reviews(**{**self.options, **kwargs})

    def test_preparation_keeps_ambiguous_candidates_unapproved_and_is_deterministic(self):
        before = (self.source_dir / 'records.json').read_bytes()
        result = self.prepare(max_candidates=2)
        row = self.queue_rows()[0]
        self.assertEqual(result['status'], 'candidates_only')
        self.assertEqual(result['accepted_by_this_preparation'], 0)
        self.assertEqual(row['requested_languages'], ['english'])
        self.assertEqual({item['target_key'] for item in row['candidates']},
                         {'raw-abu-dawud:42', 'raw-abu-dawud:43'})
        self.assertTrue(all(item['candidate_only'] and not item['source_compatibility_verified']
                            for item in row['candidates']))
        files = {path.name: path.read_bytes() for path in self.queue.iterdir()}
        self.prepare(max_candidates=2)
        self.assertEqual({path.name: path.read_bytes() for path in self.queue.iterdir()}, files)
        self.assertEqual((self.source_dir / 'records.json').read_bytes(), before)
        self.assertFalse((self.root / MANIFEST).exists())

    def test_existing_arabic_review_still_queues_missing_english_without_resolving_again(self):
        record = copy.deepcopy(self.record)
        record['counterparts'] = {'status': 'reviewed_parallel', 'arabic': {
            'text': TEXT, 'source_url': 'https://example.invalid/TEST', 'scope': 'source_excerpt'}, 'english': None}
        with patch('resolve_counterparts.CounterpartResolver.for_record', side_effect=AssertionError('re-resolution')):
            self.prepare(records=[record])
        self.assertEqual(self.queue_rows()[0]['requested_languages'], ['english'])

    def test_native_languages_and_invalid_external_urls_follow_public_availability(self):
        record = copy.deepcopy(self.record)
        record['language'] = 'en-US'
        self.assertEqual(self.prepare(records=[record])['queued_occurrences'], 0)
        record['language'] = 'sw'
        record['counterparts'] = {'status': 'reviewed_parallel', 'english': {
            'text': None, 'scope': 'external_source', 'source_url': 'javascript:TEST'}}
        self.prepare(records=[record])
        self.assertEqual(self.queue_rows()[0]['requested_languages'], ['english'])

    def test_small_bank_without_counterpart_assets_and_new_source_id(self):
        shutil.rmtree(self.root / 'sources')
        self.assertEqual(self.prepare()['occurrences_without_candidate'], 1)
        with self.assertRaisesRegex(ValueError, 'Registered source ID not found'):
            self.prepare(source_id='TEST-unregistered')

    def test_compilation_preserves_source_and_partial_external_english_and_is_idempotent(self):
        self.prepare()
        before = {path: path.read_bytes() for path in self.source_dir.iterdir()}
        result = self.compile([self.review()])
        self.assertEqual((result['verified'], result['arabic_text'], result['english_external']), (1, 1, 1))
        value = ReviewedCounterpartResolver(self.root).for_record(self.record)
        self.assertEqual(value['status'], 'reviewed_parallel')
        self.assertEqual(value['quotation_evidence']['field'], 'text_arabic')
        self.assertEqual(value['english']['coverage'], 'partial')
        self.assertIn('omits', value['english']['citation_note'])
        self.assertIsNone(value['english']['text'])
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        registry = (self.root / MANIFEST).read_bytes()
        self.assertEqual(self.compile()['status'], 'already_compiled')
        self.assertEqual((self.root / MANIFEST).read_bytes(), registry)

    def test_check_only_validates_without_creating_a_bundle(self):
        self.prepare()
        self.assertEqual(self.compile([self.review()], check_only=True)['status'], 'validated')
        self.assertFalse((self.root / MANIFEST).exists())

    def test_unresolved_decisions_remain_in_audit_without_becoming_links(self):
        other = copy.deepcopy(self.canonical_rows[0]); other['id'] = 'TEST-occurrence-two'
        self.canonical_rows.append(other)
        self.register_source(replace=True)
        records = load_source_records(self.root)
        self.prepare()
        unresolved = {**source_binding(records[1]), 'status': 'unresolved',
                      'reason': 'TEST ambiguous source occurrence remains unresolved'}
        result = self.compile([self.review(records[0]), unresolved])
        self.assertEqual((result['verified'], result['unresolved']), (1, 1))
        self.assertIsNone(ReviewedCounterpartResolver(self.root).for_record(records[1]))
        self.assertTrue(any('review-decisions-original' in path.name for path in
                            (self.root / result['bundle_path']).iterdir()))

    def test_active_compiler_lock_prevents_registry_overwrite(self):
        self.prepare()
        lock = self.root / 'sources/counterparts/reviewed/.counterpart-compile.lock'
        lock.write_text('TEST other compiler owns this lock')
        with self.assertRaisesRegex(ValueError, 'registry lock'):
            self.compile([self.review()])
        self.assertEqual(lock.read_text(), 'TEST other compiler owns this lock')
        self.assertFalse((self.root / MANIFEST).exists())

    def test_each_source_hash_and_occurrence_identity_is_required(self):
        self.prepare()
        for key in ('source_text_sha256', 'source_file_sha256', 'source_record_sha256', 'source_locator_sha256',
                    'source_id', 'language'):
            with self.subTest(key=key):
                review = self.review()
                review[key] = 'f' * 64 if key.endswith('sha256') else 'TEST-wrong'
                with self.assertRaisesRegex(ValueError, 'Stale review source binding'):
                    self.compile([review], check_only=True)

    def test_metadata_or_locator_change_with_same_text_fails_closed_at_runtime(self):
        self.prepare()
        self.compile([self.review()])
        resolver = ReviewedCounterpartResolver(self.root)
        for changes in ({'canonical_record_sha256': 'f' * 64}, {'source_locator': {'paragraph': 999}},
                        {'source': {**self.record['source'], 'record_locator': {'path': 'TEST-other.json'}}}):
            with self.subTest(changes=changes):
                value = resolver.for_record({**self.record, **changes})
                self.assertEqual(value['match_method'], 'stale_reviewed_source_binding')
                self.assertIsNone(value['english'])
        self.assertIsNone(resolver.for_record({**self.record, 'id': 'TEST-another-occurrence'}))

    def test_stale_target_metadata_and_actual_input_corruption_are_rejected(self):
        self.prepare()
        review = self.review()
        review['target_entry_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'target binding'):
            self.compile([review], check_only=True)
        review = self.review()
        path = self.root / RAW_ABU_BASE / 'raw/ara-abudawud.json.gz'
        path.write_bytes(path.read_bytes() + b'TEST corruption')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.compile([review], check_only=True)

    def test_number_only_missing_anchor_and_omitted_language_cannot_be_accepted(self):
        self.prepare()
        decisions = []
        value = self.review(); value['review']['method'] = 'number_only'; decisions.append(value)
        value = self.review(); value['review']['evidence'][0]['source_quote'] = '42'; decisions.append(value)
        value = self.review(); value['review']['evidence'][0]['source_quote'] = 'T'; decisions.append(value)
        value = self.review(); value['review']['evidence'][0]['target_quote'] = 'TEST absent'; decisions.append(value)
        value = self.review(); del value['language_decisions']['english']; decisions.append(value)
        value = self.review(); value['language_decisions']['english']['reviewed_url'] += '/changed'; decisions.append(value)
        value = self.review(); value['language_decisions']['english']['decision'] = 'approved_text'; decisions.append(value)
        for decision in decisions:
            with self.subTest(decision=decision):
                with self.assertRaises(ValueError):
                    self.compile([decision], check_only=True)
        self.assertFalse((self.root / MANIFEST).exists())

    def test_external_identity_cannot_add_foreign_references_or_remove_pinned_qualifications(self):
        self.prepare()
        review = self.review()
        other = copy.deepcopy(review['language_decisions']['english']['counterpart']['references'][0])
        other.update(book_key='muslim', number='99999', scope='source_quotation')
        review['language_decisions']['english']['counterpart']['references'].append(other)
        with self.assertRaisesRegex(ValueError, 'identity contract'):
            self.compile([review], check_only=True)
        review = self.review()
        targets, _ = raw_abu_dawud_targets(self.root)
        base = selected_entry(targets['raw-abu-dawud:42']['entry'], review['language_decisions'])
        for changes in ({'coverage': 'complete'}, {'citation_note': ''}, {'source_url': 'https://example.invalid/foreign'}):
            with self.subTest(changes=changes):
                decisions = copy.deepcopy(review['language_decisions'])
                decisions['english']['counterpart'].update(changes)
                with self.assertRaises(ValueError):
                    validate_language_decisions(base, decisions, review['review'], 'TEST-pinned-entry')

    def test_stored_english_requires_its_own_exact_content_evidence(self):
        review = self.review()
        targets, _ = raw_abu_dawud_targets(self.root)
        base = copy.deepcopy(targets['raw-abu-dawud:42']['entry'])
        base['english'] = {'text': 'TEST English quotation distinct from an Arabic comparison'}
        review['language_decisions']['english'] = {'decision': 'approved_text', 'rationale': 'TEST paired target'}
        with self.assertRaisesRegex(ValueError, 'own content comparison'):
            validate_language_decisions(base, review['language_decisions'], review['review'], 'TEST-pinned')

    def test_stored_text_can_narrow_coverage_without_rewriting_text_or_erasing_notes(self):
        targets, _ = raw_abu_dawud_targets(self.root)
        base = copy.deepcopy(targets['raw-abu-dawud:42']['entry'])
        base['arabic']['citation_note'] = 'TEST original publisher variant qualification.'
        decision = self.review()['language_decisions']
        decision['arabic'].update(scope='source_excerpt', coverage='partial',
                                  citation_note='TEST target covers the first source clause only.')
        original = copy.deepcopy(base)
        selected = selected_entry(base, decision)
        self.assertEqual(base, original)
        self.assertEqual(selected['arabic']['text'], base['arabic']['text'])
        self.assertEqual(selected['arabic']['text_sha256'], base['arabic']['text_sha256'])
        self.assertEqual(selected['arabic']['references'], base['arabic']['references'])
        self.assertEqual(selected['arabic']['source_url'], base['arabic']['source_url'])
        self.assertEqual(selected['arabic']['source_scope'], 'source_entry')
        self.assertEqual(selected['arabic']['coverage'], 'partial')
        self.assertEqual(selected['arabic']['scope'], 'source_excerpt')
        self.assertEqual(selected['arabic']['citation_note'],
            base['arabic']['citation_note'] + '\n' + decision['arabic']['citation_note'])
        for changes in ({'coverage': 'complete'}, {'scope': 'full_narration'}, {'citation_note': ''}):
            with self.subTest(changes=changes):
                invalid = copy.deepcopy(decision); invalid['arabic'].update(changes)
                with self.assertRaisesRegex(ValueError, 'may only narrow'):
                    selected_entry(base, invalid)
        missing = copy.deepcopy(decision); del missing['arabic']['citation_note']
        with self.assertRaisesRegex(ValueError, 'may only narrow'):
            selected_entry(base, missing)

    def test_narrowed_coverage_survives_compilation_and_runtime_without_changing_text(self):
        self.prepare()
        review = self.review()
        review['language_decisions']['arabic'].update(scope='source_excerpt', coverage='partial',
            citation_note='TEST the target quotation corresponds to one source clause only.')
        self.compile([review])
        value = ReviewedCounterpartResolver(self.root).for_record(self.record)
        self.assertEqual(value['arabic']['scope'], 'source_excerpt')
        self.assertEqual(value['arabic']['source_scope'], 'source_entry')
        self.assertEqual(value['arabic']['coverage'], 'partial')
        targets, _ = raw_abu_dawud_targets(self.root)
        self.assertEqual(value['arabic']['text'], targets['raw-abu-dawud:42']['entry']['arabic']['text'])

    def test_strict_provider_entry_reference_scope_is_preserved(self):
        targets, _ = raw_abu_dawud_targets(self.root)
        base = copy.deepcopy(targets['raw-abu-dawud:42']['entry'])
        base['arabic']['references'][0]['scope'] = 'publisher_entry'
        validator = ReviewedCounterpartResolver.__new__(ReviewedCounterpartResolver)
        validator._validate_entry(base, strict=True)
        self.assertEqual(base['arabic']['references'][0]['scope'], 'publisher_entry')
        with self.assertRaisesRegex(ValueError, 'scoped numbered reference'):
            validator._validate_entry(base)

    def test_explicit_unresolved_english_stays_absent(self):
        self.prepare()
        decision = self.review()
        decision['language_decisions']['english'] = {'decision': 'unresolved', 'rationale': 'TEST no verified source page'}
        self.compile([decision])
        value = ReviewedCounterpartResolver(self.root).for_record(self.record)
        self.assertIsNotNone(value['arabic'])
        self.assertIsNone(value['english'])

    def test_external_only_output_keeps_pinned_comparison_text_in_audit(self):
        self.prepare()
        decision = self.review()
        decision['language_decisions']['arabic'] = {'decision': 'unavailable', 'rationale': 'TEST audit text only'}
        self.compile([decision])
        value = ReviewedCounterpartResolver(self.root).for_record(self.record)
        self.assertEqual(value['status'], 'reviewed_parallel')
        self.assertIsNone(value['arabic'])
        self.assertIsNotNone(value['english'])

    def test_immutable_bundle_cannot_be_rewritten_or_duplicated_under_another_id(self):
        self.prepare()
        self.compile([self.review()])
        registry = (self.root / MANIFEST).read_bytes()
        decision = self.review(); decision['review']['qualifications'].append('TEST new decision')
        with self.assertRaisesRegex(ValueError, 'different content'):
            self.compile([decision])
        with self.assertRaisesRegex(ValueError, 'already has a reviewed assignment'):
            self.compile([self.review()], bundle_id='test-second-bundle')
        self.assertEqual((self.root / MANIFEST).read_bytes(), registry)

    def test_queue_refuses_to_overwrite_manual_reviews_or_follow_symlinks(self):
        self.prepare()
        (self.queue / 'manual-decisions.jsonl').write_text('TEST important evidence')
        with self.assertRaisesRegex(ValueError, 'manual reviews'):
            self.prepare()
        self.assertEqual((self.queue / 'manual-decisions.jsonl').read_text(), 'TEST important evidence')
        link = self.root / 'TEST-link'; link.symlink_to(self.queue, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            prepare_review(self.root, link)


if __name__ == '__main__':
    unittest.main()
