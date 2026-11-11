"""Printed Arabic quotations are review hints only; all fixtures are TEST text."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from counterpart_review import object_hash, text_hash
from prepare_counterpart_review import CandidateIndex, arabic_key, printed_arabic_quote_anchors


TEXT = ('هذه عبارة تجريبية طويلة تستخدم لفحص حدود النصوص والاقتباسات كما وردت '
        'في ملفات الاختبار دون تعديل الكلمات الأصلية')
REFERENCE = {'book_key': 'muslim', 'collection': 'Sahih Muslim', 'number': '12345',
             'numbering_scheme': 'TEST printed hadith number', 'scope': 'main_quote'}


def source_record(arabic=None, references=None):
    return {'id': 'TEST-occurrence', 'source_id': 'TEST-source', 'language': 'fa',
            'text_translation': 'TEST preserved source translation and additional context.',
            'text_arabic': arabic or 'TEST مقدمة محفوظة «' + TEXT + '» TEST جملة إضافية محفوظة.',
            'source': {'original_file': 'materials/TEST/source.txt', 'sha256': 'a' * 64,
                       'record_locator': {'path': 'materials/TEST/records.json', 'json_pointer': '/0'}},
            'source_locator': {'paragraph': 4}, 'canonical_record_sha256': 'b' * 64,
            'references': {'items': copy.deepcopy([REFERENCE] if references is None else references)}}


def target(key='TEST:1', arabic=None, references=None):
    entry = {'id': key, 'arabic': {'text': arabic or 'TEST سياق الناشر ' + TEXT + ' TEST نهاية مختلفة.',
             'references': copy.deepcopy([{**REFERENCE, 'scope': 'publisher_entry',
                                           'numbering_scheme': 'publisher_bibliography'}]
                                         if references is None else references)},
             'english': {'text': 'TEST English needs a separate occurrence review.', 'references': [REFERENCE]}}
    return {'target_key': key, 'entry': entry, 'target_entry_sha256': object_hash(entry), 'candidate_only': True}


def index_for(*targets):
    return CandidateIndex({item['target_key']: item for item in targets}, [], None)


def anchor_hints(index, record):
    return [item for item in index.candidates(record) if item.get('quoted_arabic_anchors')]


class QuotedMatnCandidateTests(unittest.TestCase):
    def test_exact_source_and_target_spans_remain_unapproved_and_preserve_extra_clauses(self):
        record, item = source_record(), target()
        original_record, original_target = copy.deepcopy(record), copy.deepcopy(item)
        index = index_for(item)
        self.assertNotIn(arabic_key(record['text_arabic']), arabic_key(item['entry']['arabic']['text']))
        hint, = anchor_hints(index, record)
        self.assertTrue(hint['candidate_only'])
        self.assertFalse(hint['source_compatibility_verified'])
        self.assertNotIn('language_decisions', hint)
        anchor, = hint['quoted_arabic_anchors']
        self.assertEqual(anchor['shared_explicit_references'], [['muslim', '12345']])
        self.assertEqual(anchor['target_anchor_occurrence_count'], 1)
        self.assertEqual(anchor['source_arabic_sha256'], text_hash(record['text_arabic']))
        for evidence, text in ((anchor['source'], record['text_arabic']),
                               (anchor['target'], item['entry']['arabic']['text'])):
            self.assertEqual(text[evidence['start']:evidence['end']], evidence['text'])
            self.assertEqual(evidence['sha256'], text_hash(evidence['text']))
            self.assertEqual(evidence['text'], TEXT)
        self.assertIn('not_approved', anchor['coverage_decision'])
        self.assertTrue(anchor['source_context_outside_anchor_preserved'])
        self.assertEqual(record, original_record)
        self.assertEqual(item, original_target)
        self.assertEqual(index.candidates(record), index.candidates(record))

    def test_matching_keyboard_variants_preserve_original_spans_and_hamza(self):
        persian_letters = TEXT.translate(str.maketrans({'ي': 'ی', 'ك': 'ک'}))
        record, item = source_record('TEST «' + persian_letters + '»'), target()
        hint, = anchor_hints(index_for(item), record)
        anchor, = hint['quoted_arabic_anchors']
        self.assertEqual(anchor['source']['text'], persian_letters)
        self.assertEqual(anchor['target']['text'], TEXT)
        self.assertFalse(anchor['literal_anchor_in_target'])
        self.assertNotEqual(arabic_key('أصل'), arabic_key('اصل'))
        self.assertNotEqual(arabic_key('على'), arabic_key('علي'))

    def test_no_reference_conflicting_reference_or_variant_cannot_supply_anchor_hint(self):
        invalid = [[], [{**REFERENCE, 'number': '54321'}],
                   [{**REFERENCE, 'numbering_scheme': 'chapter_number'}],
                   [{**REFERENCE, 'citation_scope': 'chapter number, not hadith number'}],
                   [{'field': 'citations_as_printed',
                     'citation_scope': 'Reference for a variant narration only',
                     'value': [{'book_key': 'muslim', 'number_as_printed': '12345'}]}],
                   [{**REFERENCE, 'scope': 'commentary'}]]
        index = index_for(target())
        for references in invalid:
            with self.subTest(references=references):
                self.assertFalse(anchor_hints(index, source_record(references=references)))

    def test_target_requires_its_own_eligible_arabic_reference(self):
        invalid = [[], [{**REFERENCE, 'number': '54321'}],
                   [{**REFERENCE, 'numbering_scheme': 'chapter_number'}],
                   [{**REFERENCE, 'citation_scope': 'Reference for a variant narration only'}],
                   [{**REFERENCE, 'scope': 'commentary'}]]
        for references in invalid:
            with self.subTest(references=references):
                # A valid English reference must not authorize the Arabic hint.
                self.assertFalse(anchor_hints(index_for(target(references=references)), source_record()))

    def test_aliases_and_printed_digits_keep_canonical_reference_compatibility(self):
        source_reference = {'book_key': 'riyadh-al-salihin', 'number': '۰۰۱۲', 'scope': 'main_quote'}
        target_reference = {'book_key': 'riyad-as-salihin', 'number': '12', 'scope': 'main_quote'}
        hints = anchor_hints(index_for(target(references=[target_reference])),
                             source_record(references=[source_reference]))
        self.assertEqual(hints[0]['quoted_arabic_anchors'][0]['shared_explicit_references'],
                         [['riyad-as-salihin', '12']])

    def test_short_and_unbalanced_quotes_are_not_matn_hints(self):
        for text in ('TEST «نص قصير»', 'TEST «' + TEXT, 'TEST ' + TEXT + '»',
                     'TEST «' + 'TEST ' * 100 + '»'):
            with self.subTest(text=text[:40]):
                self.assertFalse(printed_arabic_quote_anchors(text))
                self.assertFalse(anchor_hints(index_for(target()), source_record(text)))

    def test_supported_balanced_quote_delimiters_keep_exact_text(self):
        for opening, closing in (('«', '»'), ('“', '”'), ('‹', '›'), ('「', '」')):
            with self.subTest(opening=opening):
                record = source_record('TEST ' + opening + TEXT + closing)
                hint, = anchor_hints(index_for(target()), record)
                anchor, = hint['quoted_arabic_anchors']
                self.assertEqual(anchor['source']['text'], TEXT)
                self.assertEqual(anchor['source']['delimiters'], opening + closing)

    def test_repeated_target_anchor_is_not_a_unique_span_hint(self):
        item = target(arabic='TEST ' + TEXT + ' TEST ' + TEXT)
        self.assertFalse(anchor_hints(index_for(item), source_record()))

    def test_distinct_compatible_target_occurrences_stay_separate_candidates(self):
        hints = anchor_hints(index_for(target('TEST:1'), target('TEST:2')), source_record())
        self.assertEqual([hint['target_key'] for hint in hints], ['TEST:1', 'TEST:2'])
        for hint in hints:
            self.assertTrue(hint['candidate_only'])
            self.assertFalse(hint['source_compatibility_verified'])
            self.assertEqual(hint['quoted_arabic_anchors'][0]['reference_compatible_matching_targets'], 2)


if __name__ == '__main__':
    unittest.main()
