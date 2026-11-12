"""Synthetic TEST reports exercise the isolated source-reference proposal gate."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fawaz_relative_references import propose


def node(ident, text, position=0, direct=False, section=1):
    return {'book': 'TEST', 'edition': 'ara-TEST', 'id': str(ident), 'position': position,
        'section': section, 'text': text, 'span': [0, len(text)], 'quotation': text,
        'source_sha256': '1' * 64, 'status': 'hadith' if direct else 'held',
        'independent_prophetic': direct}


class RelativeReferencePrototypeTests(unittest.TestCase):
    def setUp(self):
        self.parent = node(15, 'حدثنا TEST عن عبد الله بن دينار قال TEST independently established report.', direct=True)
        self.child = node(900, 'وحدثنا TEST عن عبد الله بن دينار بهذا الاسناد مثله.', position=1)

    def result(self, child=None, parent=None, **options):
        return propose([parent or self.parent, child or self.child], **options)[0]

    def test_exact_relative_reference_uses_source_order_without_numeric_adjacency_or_body_copy(self):
        before = self.child['text']
        result = self.result()
        self.assertEqual(result['status'], 'positive_candidate')
        self.assertEqual(result['dependency_path'], ['900', '15'])
        self.assertEqual(result['antecedent']['source_position'], 0)
        self.assertEqual(self.child['text'], before)
        self.assertFalse(result['canonical_identity_inferred'])
        self.assertFalse(result['antecedent_text_inserted'])
        a, b = result['reference_evidence']['span']
        self.assertEqual(before[a:b], result['reference_evidence']['text'])

    def test_adjacency_and_shared_names_without_explicit_reference_are_insufficient(self):
        child = node(16, 'حدثنا TEST عن عبد الله بن دينار قال TEST independent statement.', position=1)
        self.assertNotEqual(self.result(child)['status'], 'positive_candidate')

    def test_relative_wording_without_named_chain_support_is_insufficient(self):
        child = node(16, 'حدثنا TEST عن سعيد بن عمران بهذا الاسناد مثله.', position=1)
        self.assertEqual(self.result(child)['reason'], 'named_chain_not_corroborated')

    def test_shared_collector_does_not_replace_the_final_child_chain_anchor(self):
        parent = node(15, 'حدثنا سعيد بن عمر عن خالد بن عيسى قال TEST report.', direct=True)
        child = node(16, 'حدثنا سعيد بن عمر عن ثابت بن يحيى بهذا الاسناد مثله.', position=1)
        self.assertEqual(self.result(child, parent)['reason'], 'named_chain_not_corroborated')

    def test_section_boundary_prevents_crossing_to_neighboring_source(self):
        self.child['section'] = 2
        self.assertEqual(self.result()['reason'], 'no_preceding_source_in_same_declared_section')

    def test_same_section_number_cannot_cross_books_or_editions(self):
        for field in ('book', 'edition'):
            with self.subTest(field=field):
                child = {**self.child, field: 'DIFFERENT'}
                self.assertNotEqual(self.result(child)['status'], 'positive_candidate')

    def test_duplicate_identity_or_reversed_source_order_cannot_form_a_reference(self):
        for child in ({**self.child, 'id': '15'}, {**self.child, 'position': -1}):
            with self.assertRaisesRegex(ValueError, 'unique and ordered'):
                self.result(child)

    def test_source_context_and_quoted_reference_are_not_narration_evidence(self):
        hidden = {**self.child, 'quotation': '', 'span': None}
        self.assertEqual(self.result(hidden)['reason'], 'no_bounded_arabic_reading')
        quote = node(16, 'حدثنا TEST عن عبد الله بن دينار قال "بهذا الاسناد مثله" TEST.', position=1)
        self.assertEqual(self.result(quote)['reason'], 'relative_phrase_inside_prior_quoted_or_mixed_context')

    def test_explicit_attribution_omission_and_reviewed_negatives_remain_unresolved(self):
        child = node(16, self.child['text'] + ' ولم يرفعه.', position=1)
        self.assertEqual(self.result(child)['reason'], 'source_explicitly_qualifies_or_denies_prophetic_attribution')
        self.assertEqual(self.result(negatives={'900': {'reason': 'TEST lexical source note'}})['reason'],
                         'retained_negative_source_review')

    def test_bare_chain_requires_a_source_bound_content_reference(self):
        child = node(16, 'حدثنا TEST عن عبد الله بن دينار بهذا الاسناد وقال TEST.', position=1)
        self.assertEqual(self.result(child)['reason'], 'chain_only_reference_needs_content_relation_evidence')
        child['english_quotation'] = 'This hadith was narrated through this chain.'
        self.assertNotEqual(self.result(child)['status'], 'positive_candidate')
        child['english_reference_evidence'] = {'text': 'This hadith', 'span': [0, 11], 'source_text_sha256': '2' * 64}
        self.assertEqual(self.result(child)['status'], 'positive_candidate')

    def test_backward_dependencies_must_end_in_independently_established_report(self):
        third = node(1007, self.child['text'], position=2)
        results = propose([self.parent, self.child, third])
        self.assertEqual(results[-1]['dependency_path'], ['1007', '900', '15'])
        unresolved = {**self.parent, 'status': 'held', 'independent_prophetic': False}
        self.assertTrue(all(item['status'] != 'positive_candidate' for item in propose([unresolved, self.child, third])))

    def test_unresolved_intervening_source_is_not_skipped_to_find_a_matching_root(self):
        intervening = node(16, 'حدثنا TEST عن سعيد بن ثابت قال TEST independent statement.', position=1)
        child = {**self.child, 'position': 2}
        result = propose([self.parent, intervening, child])[-1]
        self.assertEqual(result['antecedent']['typed_hadithnumber'], '16')
        self.assertNotEqual(result['status'], 'positive_candidate')

    def test_empty_intervening_source_cannot_be_skipped_to_a_matching_root(self):
        for status in ('held', 'hadith'):
            with self.subTest(status=status):
                empty = {**node(16, '', position=1), 'status': status}
                child = {**self.child, 'position': 2}
                result = propose([self.parent, empty, child])[-1]
                self.assertEqual(result['reason'], 'preceding_source_reading_absent_or_unbounded')
                self.assertNotEqual(result['status'], 'positive_candidate')

    def test_chain_label_evidence_preserves_original_offset_after_opening_punctuation(self):
        parent = node(15, 'حدثنا TEST عن (عبد الله بن دينار) قال TEST report.', direct=True)
        child = node(16, 'حدثنا TEST عن (عبد الله بن دينار) بهذا الاسناد مثله.', position=1)
        result = self.result(child, parent)
        self.assertEqual(result['status'], 'positive_candidate')
        for field, source in [('child_chain_evidence', child), ('antecedent_chain_evidence', parent)]:
            evidence = result[field]
            self.assertEqual(evidence['text'], 'عبد الله بن دينار')
            self.assertEqual(source['text'][slice(*evidence['span'])], evidence['text'])

    def test_alias_requires_explicit_source_local_evidence(self):
        parent = node(15, 'حدثنا TEST عن ابن شهاب قال TEST report.', direct=True)
        child = node(16, 'حدثنا TEST عن الزهري بهذا الاسناد مثله.', position=1)
        self.assertNotEqual(self.result(child, parent)['status'], 'positive_candidate')
        evidence = {'text': 'ابن شهاب الزهري', 'source_text_sha256': '3' * 64, 'span': [20, 34]}
        result = self.result(child, parent, aliases={('الزهري', 'ابن شهاب'): evidence})
        self.assertEqual(result['status'], 'positive_candidate')
        self.assertEqual(result['source_local_alias_evidence'], evidence)

    def test_generic_narrator_labels_are_not_specific_chain_evidence(self):
        parent = node(15, 'حدثنا TEST عن رجل قال TEST report.', direct=True)
        child = node(16, 'حدثنا TEST عن رجل بهذا الاسناد مثله.', position=1)
        self.assertEqual(self.result(child, parent)['reason'], 'named_chain_not_corroborated')


if __name__ == '__main__':
    unittest.main()
