"""TEST-only narration fixtures; these are not religious source quotations."""
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reviewed_counterparts import ReviewedCounterpartResolver, MANIFEST, SCHEMA, text_hash
from resolve_counterparts import CounterpartResolver, enrich_records, MANIFEST as PROVIDER_MANIFEST
from counterpart_display import counterpart_data, counterpart_source_data, counterpart_qualification
from citation_search import record_citation_pairs


ARABIC = 'نص تجريبي للاختبار فقط ولا يمثل حديثا أو نصا دينيا من المصدر'
ENGLISH = 'TEST English source quotation for software verification only.'


class ReviewedCounterpartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / 'TEST-original.doc'
        self.original.write_bytes(b'TEST original source binary')
        self.record = {'id': 'TEST-source:42:occurrence-1', 'source_id': 'TEST-source',
            'language': 'zh-CN', 'book_key': 'abu-dawud', 'edition': 'TEST-edition',
            'text_translation': 'TEST 原始中文测试引文，保留文字和资料内编号。', 'text_arabic': None,
            'number': {'in_book': '42', 'sequence_is_hadith_number': False,
                       'numbering_scope': 'source_internal'},
            'source': {'original_file': self.original.name,
                       'sha256': hashlib.sha256(self.original.read_bytes()).hexdigest()},
            'translation_provenance': {'current_policy': {'classification': 'unknown'}}}
        reference = {'book_key': 'abu-dawud', 'collection': 'TEST Sunan Abi Dawud',
                     'collection_ar': 'مرجع تجريبي', 'number': '987654',
                     'numbering_scheme': 'TEST published reference', 'scope': 'main_quote'}
        self.entry = {'id': 'TEST-target-987654', 'arabic': {'text': ARABIC, 'text_sha256': text_hash(ARABIC),
            'source_url': 'https://example.invalid/TEST/ar/987654', 'translation_origin': 'unknown',
            'references': [copy.deepcopy(reference)]}, 'english': {'text': ENGLISH, 'text_sha256': text_hash(ENGLISH),
            'source_url': 'https://example.invalid/TEST/en/987654', 'translation_origin': 'human',
            'references': [copy.deepcopy(reference)]}}
        self.mapping = {'record_id': self.record['id'], 'source_id': 'TEST-source', 'language': 'zh-CN',
            'source_text_sha256': text_hash(self.record['text_translation']),
            'source_file_sha256': self.record['source']['sha256'], 'target_id': self.entry['id'],
            'target_text_sha256': {'arabic': text_hash(ARABIC), 'english': text_hash(ENGLISH)},
            'relation': 'same_narration', 'review': {'status': 'verified', 'reviewer': 'TEST alignment reviewer',
            'method': 'TEST narration content comparison', 'human_review': False,
            'evidence': ['TEST shared speaker, action, context, and occurrence boundaries']}}
        self.write_bundle()

    def asset(self, relative, raw):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    def write_bundle(self, mappings=None, entries=None, authorized=True):
        def lines(values):
            return ''.join(json.dumps(value, ensure_ascii=False) + '\n' for value in values).encode()
        self.bundle = {'id': 'TEST-bundle', 'provider': 'TEST-provider', 'source_name': 'TEST source',
            'source_snapshot': 'TEST immutable snapshot', 'publication': {'authorized': authorized},
            'source_assets': [self.asset('TEST-source.txt', b'TEST upstream snapshot')],
            'entries': self.asset('TEST-entries.jsonl', lines(entries if entries is not None else [self.entry])),
            'mappings': self.asset('TEST-mappings.jsonl', lines(mappings if mappings is not None else [self.mapping]))}
        manifest = self.root / MANIFEST
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({'schema': SCHEMA, 'bundles': [self.bundle]}), encoding='utf-8')

    def test_reviewed_alignment_is_additive_and_keeps_original_number_separate(self):
        before, original_bytes = copy.deepcopy(self.record), self.original.read_bytes()
        value = CounterpartResolver(self.root, [self.record]).for_record(self.record)
        self.assertEqual(value['status'], 'reviewed_parallel')
        self.assertEqual(value['english']['text'], ENGLISH)
        self.assertEqual(value['arabic']['text'], ARABIC)
        self.assertEqual(value['english']['citation'], '[TEST Sunan Abi Dawud no. 987654]')
        self.assertEqual(record_citation_pairs({**self.record, 'counterparts': value}), {('abu-dawud', '987654')})
        self.assertEqual(self.record, before)
        self.assertEqual(self.original.read_bytes(), original_bytes)
        self.assertEqual(value['quotation_evidence']['review']['human_review'], False)
        self.assertEqual(value['arabic']['translation_origin'], 'unknown')
        self.assertEqual(value['english']['translation_origin'], 'human')
        self.assertIs(value['english']['independent_authenticity_certification'], False)
        value['english']['references'][0]['number'] = 'CHANGED'
        self.assertEqual(CounterpartResolver(self.root).for_record(self.record)['english']['references'][0]['number'], '987654')

    def test_stale_source_text_file_identity_and_language_fail_closed(self):
        variants = [{'text_translation': self.record['text_translation'] + ' TEST change'},
                    {'source_id': 'TEST-other-source'}, {'language': 'en'},
                    {'source': {**self.record['source'], 'sha256': 'f' * 64}}]
        resolver = CounterpartResolver(self.root)
        for changes in variants:
            with self.subTest(changes=changes):
                value = resolver.for_record({**self.record, **changes})
                self.assertEqual(value['status'], 'unresolved')
                self.assertEqual(value['match_method'], 'stale_reviewed_source_binding')
                self.assertIsNone(value['arabic'])
                self.assertIsNone(value['english'])

    def test_record_ids_are_occurrence_specific_not_number_matches(self):
        value = CounterpartResolver(self.root).for_record({**self.record, 'id': 'TEST-source:42:occurrence-2'})
        self.assertEqual(value['status'], 'unresolved')
        self.assertIsNone(value['english'])

    def test_duplicate_reviewed_assignments_are_ambiguous_even_when_targets_agree(self):
        self.write_bundle(mappings=[self.mapping, copy.deepcopy(self.mapping)])
        value = CounterpartResolver(self.root).for_record(self.record)
        self.assertEqual(value['match_method'], 'ambiguous_reviewed_mapping')
        self.assertIsNone(value['arabic'])

    def test_unreviewed_candidates_and_unauthorized_bundles_do_not_resolve(self):
        self.mapping['review']['status'] = 'candidate'
        self.mapping['target_id'] = 'TEST-not-present'
        self.write_bundle()
        self.assertIsNone(ReviewedCounterpartResolver(self.root).for_record(self.record))
        self.write_bundle(authorized=False)
        (self.root / 'TEST-entries.jsonl').unlink()
        self.assertIsNone(ReviewedCounterpartResolver(self.root).for_record(self.record))

    def test_each_pinned_asset_corruption_is_rejected(self):
        for relative in ('TEST-source.txt', 'TEST-entries.jsonl', 'TEST-mappings.jsonl'):
            with self.subTest(relative=relative):
                self.write_bundle()
                path = self.root / relative
                path.write_bytes(path.read_bytes() + b'corrupted')
                with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                    CounterpartResolver(self.root)

    def test_entry_text_and_mapping_target_hashes_are_independently_verified(self):
        self.entry['english']['text'] += ' TEST changed'
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, 'text checksum mismatch'):
            CounterpartResolver(self.root)
        self.entry['english']['text_sha256'] = text_hash(self.entry['english']['text'])
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, 'target text checksum mismatch'):
            CounterpartResolver(self.root)

    def test_stale_target_id_is_rejected(self):
        self.mapping['target_id'] = 'TEST-missing-target'
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, 'target is absent'):
            CounterpartResolver(self.root)

    def test_review_requires_evidence_and_explicit_human_state_not_number_only(self):
        for changes in ({'method': 'number_only'}, {'evidence': []}, {'human_review': None}, {'reviewer': ''}):
            with self.subTest(changes=changes):
                saved = copy.deepcopy(self.mapping['review'])
                self.mapping['review'].update(changes)
                self.write_bundle()
                with self.assertRaises(ValueError):
                    CounterpartResolver(self.root)
                self.mapping['review'] = saved

    def test_external_english_has_citation_but_no_text_availability(self):
        self.entry['english'].update(text=None, text_sha256=None, translation_origin='unknown')
        self.mapping['target_text_sha256']['english'] = None
        self.mapping['relation'] = 'source_excerpt'
        self.write_bundle()
        before = copy.deepcopy(self.record)
        summary = enrich_records(self.root, [self.record])
        self.assertEqual(summary['arabic_available'], 1)
        self.assertEqual(summary['english_available'], 0)
        self.assertEqual(summary['english_external_links'], 1)
        self.assertEqual(summary['reviewed_parallel_links'], 1)
        self.assertEqual(summary['exact_links'], 0)
        self.assertIsNone(counterpart_data(self.record, 'english'))
        source = counterpart_source_data(self.record, 'english')
        self.assertIsNotNone(source)
        self.assertEqual(source['translation_origin'], 'unknown')
        self.assertIn('Reviewed source parallel', counterpart_qualification(source, self.record))
        self.assertIn('Linked source entry', counterpart_qualification(source, self.record))
        self.assertEqual(record_citation_pairs(self.record), {('abu-dawud', '987654')})
        self.assertEqual({k: v for k, v in self.record.items() if k != 'counterparts'}, before)

    def test_null_language_does_not_become_a_source_or_translation(self):
        self.entry['english'] = None
        self.mapping['target_text_sha256']['english'] = None
        self.write_bundle()
        value = CounterpartResolver(self.root).for_record(self.record)
        self.assertIsNone(value['english'])
        self.assertEqual(value['arabic']['text'], ARABIC)

    def test_source_entry_scope_preserves_provider_bytes_and_rejects_false_scope(self):
        self.entry['arabic']['scope'] = 'source_entry'
        self.write_bundle()
        value = CounterpartResolver(self.root).for_record(self.record)
        self.assertEqual(value['arabic']['scope'], 'source_entry')
        self.assertEqual(value['arabic']['text'], ARABIC)
        self.assertEqual(value['arabic']['text_sha256'], text_hash(ARABIC))
        note = counterpart_qualification(value['arabic'], self.record)
        self.assertIn("May include the compiler's notes; the Chinese source can be an excerpt.", note)
        self.assertNotIn('Full narration', note)
        self.entry['arabic']['scope'] = 'external_source'
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, 'scope is not supported'):
            CounterpartResolver(self.root)

    def test_distinct_source_occurrences_can_share_one_target_entry(self):
        second = copy.deepcopy(self.record)
        second['id'] += ':TEST-second-occurrence'
        second['text_translation'] += ' TEST distinct excerpt'
        mapping = copy.deepcopy(self.mapping)
        mapping.update(record_id=second['id'], source_text_sha256=text_hash(second['text_translation']))
        self.write_bundle(mappings=[self.mapping, mapping])
        resolver = CounterpartResolver(self.root)
        for source in (self.record, second):
            value = resolver.for_record(source)
            self.assertEqual(value['status'], 'reviewed_parallel')
            self.assertEqual(value['arabic']['source_record_id'], self.entry['id'])
            self.assertEqual(value['quotation_evidence']['source_text_sha256'], text_hash(source['text_translation']))

    def test_language_specific_publisher_identity_and_cross_reference_note_are_preserved(self):
        note = 'TEST collection number is a reviewed Arabic-source cross-reference; TEST publisher supplies no hadith number.'
        item = self.entry['english']
        item.update(source_snapshot='TEST English publisher snapshot version 3', source_record_id='TEST-publisher-id-123',
                    publisher_references=[], citation_note=note)
        item['references'][0]['numbering_scheme'] = 'reviewed_source_parallel'
        self.write_bundle()
        value = CounterpartResolver(self.root).for_record(self.record)
        english = value['english']
        self.assertEqual(english['source_snapshot'], item['source_snapshot'])
        self.assertEqual(english['source_record_id'], item['source_record_id'])
        self.assertEqual(english['publisher_references'], [])
        self.assertEqual(english['references'][0]['numbering_scheme'], 'reviewed_source_parallel')
        self.assertEqual(english['citation_note'], note)
        self.assertIn(note, counterpart_qualification(english, self.record))
        self.assertEqual(value['arabic']['source_snapshot'], self.bundle['source_snapshot'])
        self.assertEqual(value['arabic']['source_record_id'], self.entry['id'])

    def test_supplied_english_excerpt_is_not_promoted_to_a_full_counterpart(self):
        self.entry['english']['scope'] = 'source_excerpt'
        self.write_bundle()
        value = CounterpartResolver(self.root).for_record(self.record)
        self.assertEqual(value['english']['scope'], 'source_excerpt')
        self.assertEqual(value['english']['text'], ENGLISH)
        note = counterpart_qualification(value['english'], self.record)
        self.assertIn('does not supply the complete source entry', note)
        self.assertNotIn('Full narration', note)

    def test_unsafe_assets_and_symlinks_are_rejected(self):
        for relative in ('../TEST-entries.jsonl', '/TEST-entries.jsonl', 'TEST/../entries.jsonl', 'TEST\\entries.jsonl'):
            with self.subTest(relative=relative):
                self.write_bundle()
                self.bundle['entries']['path'] = relative
                (self.root / MANIFEST).write_text(json.dumps({'schema': SCHEMA, 'bundles': [self.bundle]}))
                with self.assertRaisesRegex(ValueError, 'Unsafe'):
                    CounterpartResolver(self.root)
        self.write_bundle()
        path = self.root / 'TEST-entries.jsonl'
        target = self.root / 'TEST-real-entries.jsonl'
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            CounterpartResolver(self.root)

    def provider_manifest(self):
        for name, statement, row in (
            ('TEST-en.sqlite', 'CREATE TABLE hadeeths (id INTEGER,hadeeth TEXT,hadeeth_ar TEXT,ar_version INTEGER)', (101, ENGLISH, ARABIC, 7)),
            ('TEST-ar.sqlite', 'CREATE TABLE hadeeths (id INTEGER,hadeeth TEXT,version INTEGER,reference TEXT)', (101, ARABIC, 7, 'سنن أبي داود (987654).'))):
            with closing(sqlite3.connect(self.root / name)) as db, db:
                db.execute(statement)
                db.execute('INSERT INTO hadeeths VALUES (?,?,?,?)', row)
        def descriptor(name):
            raw = (self.root / name).read_bytes()
            return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        path = self.root / PROVIDER_MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema': 'hadith-bank-hadeethenc-counterpart-sources-v1',
            'english_database': descriptor('TEST-en.sqlite'), 'arabic_database': descriptor('TEST-ar.sqlite'),
            'english_version': 'TEST-v1'}))

    def test_existing_provider_fallback_remains_but_cannot_hide_stale_reviewed_mapping(self):
        self.provider_manifest()
        provider_record = {**self.record, 'book_key': 'hadeethenc', 'provider_entry_id': '101', 'text_arabic': ARABIC}
        resolver = CounterpartResolver(self.root, [])
        self.assertEqual(resolver.for_record({**provider_record, 'id': 'TEST-provider-only'})['status'], 'exact')
        value = resolver.for_record({**provider_record, 'text_translation': 'TEST stale source'})
        self.assertEqual(value['match_method'], 'stale_reviewed_source_binding')
        self.assertIsNone(value['english'])


if __name__ == '__main__':
    unittest.main()
