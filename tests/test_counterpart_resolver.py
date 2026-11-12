"""Synthetic TEST sources only; none of these fixtures are religious text."""
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from resolve_counterparts import (CounterpartResolver, MANIFEST, source_references,
                                  normalize_arabic_quote, normalize_quote)

ARABIC = 'نص تجريبي للاختبار فقط يحتوي على كلمات عربية متعددة للتحقق من الربط وحفظ النص'
ENGLISH = 'TEST source translation only; this text tests exact counterpart preservation.'


class CounterpartResolverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.english = self.root / 'english.sqlite'
        self.arabic = self.root / 'arabic.sqlite'
        with closing(sqlite3.connect(self.english)) as db, db:
            db.execute('CREATE TABLE hadeeths (id INTEGER,hadeeth TEXT,hadeeth_ar TEXT,ar_version INTEGER)')
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (101, ENGLISH, ARABIC, 7))
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('CREATE TABLE hadeeths (id INTEGER,hadeeth TEXT,version INTEGER,reference TEXT)')
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (101, ARABIC, 7, 'صحيح مسلم (1/ 2) (12345).'))
        self.manifest()

    def manifest(self):
        def info(path):
            return {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'bytes': path.stat().st_size}
        path = self.root / MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema': 'hadith-bank-hadeethenc-counterpart-sources-v1',
            'english_database': info(self.english), 'arabic_database': info(self.arabic),
            'english_version': 'TEST-v1'}), encoding='utf-8')

    def record(self, **changes):
        record = {'id': 'TEST-101', 'language': 'ja', 'book_key': 'hadeethenc',
                  'provider_entry_id': '101', 'text_arabic': ARABIC,
                  'text_translation': 'TEST original translation', 'references': {},
                  'source': {'name': 'TEST publisher', 'url': 'https://example.invalid/TEST'},
                  'source_id': 'TEST-source', 'edition': 'TEST-edition',
                  'translation_provenance': {'current_policy': {'classification': 'unknown'}}}
        record.update(changes)
        return record

    def test_primary_identity_preserves_both_sources_and_number(self):
        record = self.record()
        before = copy.deepcopy(record)
        result = CounterpartResolver(self.root, [record]).for_record(record)
        self.assertEqual(record, before)
        self.assertEqual(result['english']['text'], ENGLISH)
        self.assertEqual(result['arabic']['text'], ARABIC)
        self.assertEqual(result['english']['citation'], '[Sahih Muslim no. 12345]')
        self.assertEqual(result['status'], 'exact')
        self.assertEqual(record['translation_provenance']['current_policy']['classification'], 'unknown')

    def test_material_opt_out_blocks_provider_link_without_affecting_other_records(self):
        enabled = self.record()
        disabled = self.record(id='TEST-disabled', counterpart_policy={
            'mode': 'disabled', 'reason': 'TEST alignment is not approved'})
        before = copy.deepcopy(disabled)
        resolver = CounterpartResolver(self.root, [enabled, disabled])
        result = resolver.for_record(disabled)
        self.assertEqual(result['status'], 'unresolved')
        self.assertEqual(result['match_method'], 'material_counterparts_disabled')
        self.assertEqual(result['match_note'], disabled['counterpart_policy']['reason'])
        self.assertIsNone(result['arabic'])
        self.assertIsNone(result['english'])
        self.assertIsNone(result['quotation_evidence'])
        self.assertEqual(disabled, before)
        self.assertEqual(disabled['text_arabic'], ARABIC)
        unaffected = resolver.for_record(enabled)
        self.assertEqual(unaffected['status'], 'exact')
        self.assertEqual(unaffected['arabic']['text'], ARABIC)
        self.assertEqual(unaffected['english']['text'], ENGLISH)

    def test_material_opt_out_blocks_unique_chinese_translation_match(self):
        translated = 'TEST仅用于软件测试的足够长中文文本不会作为宗教资料发布'
        provider = self.record(language='zh-CN', text_translation=translated)
        source = self.record(id='TEST-Chinese-source', language='zh-CN',
                             book_key='hisn-al-muslim', provider_entry_id=None,
                             text_arabic=None, text_translation=translated)
        resolver = CounterpartResolver(self.root, [provider])
        baseline = resolver.for_record(source)
        self.assertEqual(baseline['match_method'], 'unique_source_quotation')
        self.assertEqual(baseline['english']['text'], ENGLISH)
        source['counterpart_policy'] = {'mode': 'disabled', 'reason': 'TEST pending source'}
        before = copy.deepcopy(source)
        blocked = resolver.for_record(source)
        self.assertEqual(blocked['match_method'], 'material_counterparts_disabled')
        self.assertIsNone(blocked['arabic'])
        self.assertIsNone(blocked['english'])
        self.assertEqual(source, before)

    def test_material_opt_out_precedes_reviewed_and_automatic_resolution(self):
        record = self.record(counterpart_policy={
            'mode': 'disabled', 'reason': 'TEST material decision takes precedence'})
        resolver = CounterpartResolver(self.root, [record])
        with patch.object(resolver.reviewed, 'for_record',
                          side_effect=AssertionError('Reviewed matching must not run')), \
                patch.object(resolver, '_select',
                             side_effect=AssertionError('Automatic matching must not run')):
            result = resolver.for_record(record)
        self.assertEqual(result['match_method'], 'material_counterparts_disabled')
        self.assertIsNone(result['arabic'])
        self.assertIsNone(result['english'])

    def test_same_provider_changed_arabic_is_qualified(self):
        record = self.record(text_arabic='نص تجريبي مختلف في النسخة القديمة')
        result = CounterpartResolver(self.root, [record]).for_record(record)
        self.assertEqual(result['status'], 'related_version')
        self.assertEqual(result['english']['match_status'], 'related_version')
        self.assertNotEqual(record['text_arabic'], result['arabic']['text'])

    def test_parent_url_does_not_assign_unrelated_note(self):
        record = self.record(book_key='muslim', provider_entry_id='lesson-1', text_arabic=None,
            text_translation='TEST unrelated note', source={'url': 'https://hadeethenc.com/ja/browse/hadith/101'})
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertIsNone(result['english'])
        self.assertEqual(result['match_method'], 'parent_source_link_without_quotation_alignment')

    def test_number_alone_never_links(self):
        references = [
            {'book_key': 'muslim', 'number': '12345', 'scope': 'main_quote'},
            {'collection': 'Sahih Muslim', 'numbers': ['12345'], 'scope': 'source_citation'},
            {'field': 'citations_as_printed', 'value': [
                {'collection': 'Sahih Muslim', 'number_as_printed': '۱۲۳۴۵'}]},
        ]
        for reference in references:
            with self.subTest(reference=reference):
                record = self.record(book_key='muslim', provider_entry_id=None, text_arabic=None,
                    text_translation='TEST unrelated quotation', references={'items': [reference]})
                self.assertIsNone(CounterpartResolver(self.root, []).for_record(record)['english'])

    def test_structured_source_citation_blocks_conflicting_match_and_preserves_arabic_citation(self):
        citation = 'TEST exact source citation: صحیح مسلم، رقم ۹۹۹۹۹'
        terminal = 'Exact terminal citation for this source narration; moved from reader text to metadata.'
        references = [
            {'collection': 'صحیح مسلم', 'numbers': ['۹۹۹۹۹'], 'scope': 'main_quote',
             'citation_raw': citation},
            {'collection': 'صحیح مسلم', 'numbers': ['۹۹۹۹۹'], 'scope': 'source_citation',
             'source_citation': citation},
            {'collection': 'صحیح مسلم', 'numbers': ['۹۹۹۹۹'], 'citation_scope': terminal,
             'citation_raw': citation},
            {'field': 'citations_as_printed', 'value': [
                {'collection': 'صحیح مسلم', 'number_as_printed': '۹۹۹۹۹',
                 'citation_raw': citation}]},
        ]
        for reference in references:
            with self.subTest(reference=reference):
                record = self.record(book_key='muslim', provider_entry_id=None,
                                     references={'items': [reference]})
                before = copy.deepcopy(record)
                result = CounterpartResolver(self.root, []).for_record(record)
                self.assertIsNone(result['english'])
                self.assertEqual(result['arabic']['text'], ARABIC)
                self.assertEqual(result['arabic']['citation'], '[صحيح مسلم، رقم ۹۹۹۹۹]')
                supplied = result['arabic']['references'][0]
                self.assertEqual(supplied['source_citation'], citation)
                original_item = reference['value'][0] if reference.get('field') else reference
                self.assertEqual(supplied['source_reference'], original_item)
                self.assertEqual(supplied['number'], '۹۹۹۹۹')
                self.assertEqual(record, before)

    def test_structured_source_references_keep_strict_quotation_scope(self):
        record = self.record(references={'items': [
            {'collection': 'Sahih Muslim', 'numbers': ['1'], 'scope': 'variant'},
            {'collection': 'Sahih Muslim', 'numbers': ['2'], 'scope': 'commentary'},
            {'collection': 'Sahih Muslim', 'numbers': ['3']},
            {'collection': 'Sahih Muslim', 'numbers': [], 'scope': 'main_quote',
             'number_raw': ['4'], 'cross_reference_numbers': ['5']},
            {'collection': 'Sahih Muslim', 'numbers': ['6'], 'scope': 'source_citation',
             'numbering_system': 'Source-local numbering'},
            {'field': 'citations_as_printed', 'scope': 'context', 'value': [
                {'collection': 'Sahih Muslim', 'number_as_printed': '7'}]},
            {'field': 'citations_as_printed', 'value': [
                {'collection': 'Sahih Muslim', 'number_as_printed': '8', 'scope': 'variant'},
                {'collection': 'Sahih Muslim', 'number_as_printed': '9',
                 'citation_scope': 'Reference to a variant'}]},
            {'field': 'source_assessment', 'value': [
                {'collection': 'Sahih Muslim', 'number_as_printed': '10'}]},
        ]})
        before = copy.deepcopy(record)
        self.assertEqual(source_references(record), [])
        self.assertEqual(record, before)

    def test_unique_exact_arabic_can_link_without_provider_id(self):
        record = self.record(book_key='muslim', provider_entry_id=None)
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(result['english']['text'], ENGLISH)
        self.assertEqual(result['quotation_evidence']['field'], 'text_arabic')

    def test_number_suffix_requires_arabic_alignment_and_preserves_both_references(self):
        record = self.record(book_key='muslim', provider_entry_id=None,
            references={'items': [{'book_key': 'muslim', 'number': '12345a', 'scope': 'main_quote'}]})
        before = copy.deepcopy(record)
        value = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(value['english']['text'], ENGLISH)
        self.assertEqual(value['english']['references'][0]['number'], '12345')
        proof = value['quotation_evidence']
        self.assertEqual(proof['shared_explicit_references'], [])
        self.assertEqual(proof['suffix_compatible_references'],
                         [{'source': ['muslim', '12345a'], 'target': ['muslim', '12345']}])
        self.assertEqual(record, before)

    def test_suffix_number_and_matching_translation_without_arabic_do_not_join(self):
        donor = self.record()
        record = self.record(book_key='muslim', provider_entry_id=None, text_arabic=None,
            references={'items': [{'book_key': 'muslim', 'number': '12345a', 'scope': 'main_quote'}]})
        value = CounterpartResolver(self.root, [donor]).for_record(record)
        self.assertIsNone(value['english'])

    def test_two_different_number_suffixes_remain_conflicting(self):
        record = self.record(book_key='muslim', provider_entry_id=None,
            references={'items': [{'book_key': 'muslim', 'number': '12345a', 'scope': 'main_quote'}]})
        resolver = CounterpartResolver(self.root, [])
        resolver.entries['101']['references'][0]['number'] = '12345b'
        self.assertIsNone(resolver.for_record(record)['english'])

    def test_suffix_corroboration_does_not_enable_reverse_containment(self):
        record = self.record(book_key='muslim', provider_entry_id=None,
            text_arabic='بداية مختلفة ' + ARABIC + ' نهاية مختلفة',
            references={'items': [{'book_key': 'muslim', 'number': '12345a', 'scope': 'main_quote'}]})
        resolver = CounterpartResolver(self.root, [])
        self.assertIsNone(resolver._quotation_evidence(record, '101'))
        self.assertIsNone(resolver.for_record(record)['english'])

    def test_suffix_corroboration_keeps_duplicate_arabic_targets_ambiguous(self):
        with closing(sqlite3.connect(self.english)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, 'TEST other route', ARABIC, 7))
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, ARABIC, 7, 'صحيح مسلم (1/ 2) (12345).'))
        self.manifest()
        record = self.record(book_key='muslim', provider_entry_id=None,
            references={'items': [{'book_key': 'muslim', 'number': '12345a', 'scope': 'main_quote'}]})
        value = CounterpartResolver(self.root, []).for_record(record)
        self.assertIsNone(value['english'])
        self.assertEqual(value['match_method'], 'ambiguous_source_quotation')

    def test_persian_keyboard_letters_match_arabic_without_changing_either_source(self):
        source = ARABIC.replace('ك', 'ک').replace('ي', 'ی')
        self.assertNotEqual(normalize_quote(source), normalize_quote(ARABIC))
        record = self.record(book_key='muslim', provider_entry_id=None, text_arabic=source)
        before = copy.deepcopy(record)
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(result['status'], 'exact')
        self.assertEqual(result['english']['text'], ENGLISH)
        self.assertEqual(result['arabic']['text'], ARABIC)
        evidence = result['quotation_evidence']
        self.assertEqual(evidence['relation'], 'normalized_exact')
        self.assertEqual(evidence['source_text_sha256'], hashlib.sha256(source.encode()).hexdigest())
        self.assertEqual(evidence['target_text_sha256'], hashlib.sha256(ARABIC.encode()).hexdigest())
        self.assertIn('Persian kaf and yeh', evidence['normalization'])
        self.assertEqual(record, before)

    def test_distinct_arabic_letters_are_not_collapsed_with_keyboard_variants(self):
        self.assertNotEqual(normalize_arabic_quote('على'), normalize_arabic_quote('علي'))
        self.assertNotEqual(normalize_arabic_quote('أمر'), normalize_arabic_quote('امر'))
        record = self.record(book_key='muslim', provider_entry_id=None,
                             text_arabic=ARABIC.replace('على', 'علي'))
        self.assertIsNone(CounterpartResolver(self.root, []).for_record(record)['english'])

    def test_keyboard_normalization_does_not_choose_between_matching_occurrences(self):
        variant = ARABIC.replace('ك', 'ک').replace('ي', 'ی')
        with closing(sqlite3.connect(self.english)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, 'TEST second translation', variant, 7))
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, variant, 7, 'صحيح مسلم (1/ 3) (12346).'))
        self.manifest()
        record = self.record(book_key='muslim', provider_entry_id=None)
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(result['match_method'], 'ambiguous_source_quotation')
        self.assertIsNone(result['english'])

    def test_reference_supported_shorter_counterpart_is_explicitly_partial(self):
        source = 'مقدمة تجريبية مطولة من المصدر ' + ARABIC + ' ونهاية تجريبية إضافية محفوظة'
        references = {'items': [{'book_key': 'muslim', 'number': '12345', 'scope': 'main_quote'}]}
        record = self.record(book_key='muslim', provider_entry_id=None,
                             text_arabic=source, references=references)
        before = copy.deepcopy(record)
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(result['quotation_evidence']['relation'], 'target_excerpt')
        self.assertEqual(result['quotation_evidence']['shared_explicit_references'], [['muslim', '12345']])
        self.assertEqual(result['english']['scope'], 'source_excerpt')
        self.assertEqual(result['arabic']['scope'], 'source_excerpt')
        self.assertEqual(result['english']['text'], ENGLISH)
        self.assertEqual(result['arabic']['text'], ARABIC)
        self.assertIn('literal excerpt', result['match_note'])
        self.assertEqual(record, before)

    def test_reverse_containment_needs_a_matching_explicit_collection_reference(self):
        source = 'مقدمة تجريبية مطولة من المصدر ' + ARABIC + ' ونهاية تجريبية إضافية محفوظة'
        reference_sets = [{},
            {'items': [{'book_key': 'muslim', 'number': '99999', 'scope': 'main_quote'}]},
            {'items': [{'book_key': 'muslim', 'number': '12345', 'scope': 'commentary'}]},
            {'items': [{'book_key': 'muslim', 'number': '12345', 'scope': 'main_quote',
                        'numbering_scheme': 'number_within_source_named_book'}]}]
        for references in reference_sets:
            with self.subTest(references=references):
                record = self.record(book_key='muslim', provider_entry_id=None,
                                     text_arabic=source, references=references)
                self.assertIsNone(CounterpartResolver(self.root, []).for_record(record)['english'])

    def test_chapter_numbers_and_wrapper_variant_references_cannot_authorize_reverse_match(self):
        source = 'مقدمة تجريبية مطولة من المصدر ' + ARABIC + ' ونهاية تجريبية إضافية محفوظة'
        references = [
            {'book_key': 'muslim', 'number': '12345', 'scope': 'main_quote',
             'numbering_scheme': 'chapter_number'},
            {'book_key': 'muslim', 'number': '12345', 'scope': 'main_quote',
             'citation_scope': 'chapter number, not hadith number'},
            {'field': 'citations_as_printed',
             'citation_scope': 'Reference for a variant narration only',
             'value': [{'book_key': 'muslim', 'number_as_printed': '12345'}]},
            {'field': 'citations_as_printed', 'numbering_scope': 'Chapter_Number',
             'value': [{'book_key': 'muslim', 'number_as_printed': '12345'}]},
            {'field': 'citations_as_printed',
             'value': [{'book_key': 'muslim', 'number_as_printed': '12345',
                        'citation_scope': 'chapter number, not hadith number'}]},
        ]
        resolver = CounterpartResolver(self.root, [])
        for reference in references:
            with self.subTest(reference=reference):
                record = self.record(book_key='muslim', provider_entry_id=None,
                    text_arabic=source, references={'items': [reference]})
                before = copy.deepcopy(record)
                self.assertEqual(source_references(record), [])
                self.assertIsNone(resolver.for_record(record)['english'])
                self.assertEqual(record, before)

    def test_reverse_containment_rejects_short_anchors_even_with_the_same_reference(self):
        short = 'هذا نص تجريبي قصير لا يمثل حديثا من المصدر'
        self.assertGreaterEqual(len(normalize_arabic_quote(short)), 32)
        self.assertLess(len(normalize_arabic_quote(short)), 64)
        with closing(sqlite3.connect(self.english)) as db, db:
            db.execute('UPDATE hadeeths SET hadeeth_ar=?', (short,))
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('UPDATE hadeeths SET hadeeth=?', (short,))
        self.manifest()
        record = self.record(book_key='muslim', provider_entry_id=None,
            text_arabic='مقدمة تجريبية طويلة ' + short + ' وتتمة إضافية لا يغطيها النص القصير',
            references={'items': [{'book_key': 'muslim', 'number': '12345', 'scope': 'main_quote'}]})
        self.assertIsNone(CounterpartResolver(self.root, []).for_record(record)['english'])

    def test_reverse_containment_does_not_choose_one_of_several_supported_quotes(self):
        second = 'مثال تجريبي مختلف طويل للتحقق من حفظ كل نص في المصدر دون اختيار إحدى العبارات المتعددة عشوائيا'
        with closing(sqlite3.connect(self.english)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, 'TEST second source', second, 7))
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, second, 7, 'صحيح مسلم (1/ 3) (12346).'))
        self.manifest()
        record = self.record(book_key='muslim', provider_entry_id=None,
            text_arabic=ARABIC + ' ثم ' + second,
            references={'items': [{'book_key': 'muslim', 'number': n, 'scope': 'main_quote'}
                                  for n in ('12345', '12346')]})
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(result['match_method'], 'ambiguous_source_quotation')
        self.assertIsNone(result['english'])

    def test_ambiguous_text_remains_unresolved(self):
        with closing(sqlite3.connect(self.english)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, 'TEST other translation', ARABIC, 7))
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', (102, ARABIC, 7, 'صحيح مسلم (1/ 3) (12346).'))
        self.manifest()
        result = CounterpartResolver(self.root, []).for_record(self.record(book_key='muslim', provider_entry_id=None))
        self.assertIsNone(result['english'])
        self.assertEqual(result['match_method'], 'ambiguous_source_quotation')

    def test_unaligned_bibliography_not_copied(self):
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('UPDATE hadeeths SET version=8')
        self.manifest()
        result = CounterpartResolver(self.root, []).for_record(self.record())
        self.assertEqual(result['english']['references'], [])
        self.assertIsNone(result['english']['citation'])
        self.assertFalse(result['english']['bibliography_arabic_version_aligned'])

    def test_other_arabic_revision_cannot_lend_a_reference(self):
        with closing(sqlite3.connect(self.arabic)) as db, db:
            db.execute('UPDATE hadeeths SET version=8')
        self.manifest()
        record = self.record(text_arabic='TEST another Arabic revision', references={
            'items': [{'book_key': 'muslim', 'number': '12345', 'scope': 'main_quote'}]})
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(result['status'], 'related_version')
        self.assertIsNone(result['english']['citation'])

    def test_translation_identity_does_not_hide_arabic_wording_difference(self):
        primary = self.record(text_translation='TEST exact translation with sufficient characters for comparison')
        record = self.record(book_key='muslim', provider_entry_id=None,
            text_arabic='هذا نص تجريبي آخر تختلف كلماته عن نص المصدر المقابل',
            text_translation=primary['text_translation'],
            source={'url': 'https://hadeethenc.com/ja/browse/hadith/101'})
        result = CounterpartResolver(self.root, [primary]).for_record(record)
        self.assertIsNotNone(result['english'])
        self.assertEqual(result['status'], 'related_version')

    def test_bidi_formatting_alone_is_not_a_different_wording(self):
        record = self.record(book_key='muslim', provider_entry_id=None, text_arabic='\u200f' + ARABIC)
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertEqual(result['status'], 'exact')

    def test_local_abridgment_number_not_used_for_source_arabic_citation(self):
        record = self.record(book_key='muslim', provider_entry_id=None,
            text_arabic='TEST Arabic without any matching source quotation',
            references={'items': [{'book_key': 'muslim', 'number': '17', 'scope': 'main_quote',
                'numbering_scheme': 'number_within_source_named_book'}]})
        result = CounterpartResolver(self.root, []).for_record(record)
        self.assertIsNone(result['arabic']['citation'])

    def test_corrupt_source_export_fails_closed(self):
        with self.english.open('ab') as stream:
            stream.write(b'TEST corruption')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            CounterpartResolver(self.root, [])

    def test_conflicting_source_number_blocks_inferred_join(self):
        record = self.record(book_key='muslim', provider_entry_id=None,
            references={'items': [{'book_key': 'muslim', 'number': '99999', 'scope': 'main_quote'}]})
        self.assertIsNone(CounterpartResolver(self.root, []).for_record(record)['english'])


if __name__ == '__main__':
    unittest.main()
