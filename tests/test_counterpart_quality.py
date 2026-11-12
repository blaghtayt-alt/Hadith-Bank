"""Exact quality overrides use synthetic TEST text; preserved source stays intact."""
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
from counterpart_quality import ACTION, PARTIAL_ACTION, POLICY_PATH, SCHEMA, apply_quality_policy, load_quality_policy
from counterpart_display import counterpart_search_values, counterpart_source_data, counterpart_qualification
from counterpart_coverage import availability_for
from resolve_counterparts import CounterpartResolver, MANIFEST
from reviewed_counterparts import ReviewedCounterpartResolver, MANIFEST as REVIEWED_MANIFEST, SCHEMA as REVIEWED_SCHEMA

TEST_ENGLISH = 'TEST English source wording with a documented content problem; no religious quotation.'
TEST_ARABIC = 'TEST exact preserved Arabic-field source text for this regression fixture only.'


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


class CounterpartQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = {'schema': SCHEMA, 'decisions': [{
            'id': 'test-exact-quality-decision', 'provider': 'hadeethenc',
            'source_record_id': '65015', 'language': 'english', 'text_sha256': sha(TEST_ENGLISH),
            'action': ACTION, 'message': 'TEST English counterpart withheld because of a verified wording reversal.',
            'reason_code': 'test_wording_reversal', 'reviewed_date': 'TEST-date',
            'evidence': {'source_note': 'TEST reviewed comparison'}}]}
        self.write_policy()
        self.policy = load_quality_policy(self.root)
        self.english = {'text': TEST_ENGLISH, 'text_sha256': sha(TEST_ENGLISH),
            'source_url': 'https://hadeethenc.com/en/browse/hadith/65015', 'source_record_id': '65015',
            'source_name': 'HadeethEnc.com', 'source_snapshot': 'TEST immutable snapshot',
            'translation_origin': 'human', 'current_translation_policy': {
                'classification': 'human', 'basis': 'TEST existing source origin'}, 'scope': 'full_narration'}
        self.value = {'status': 'exact', 'match_method': 'primary_provider_id',
            'provider_identity': {'provider': 'hadeethenc', 'id': '65015', 'status': 'linked'},
            'english': copy.deepcopy(self.english),
            'arabic': {'text': TEST_ARABIC, 'text_sha256': sha(TEST_ARABIC), 'translation_origin': 'unknown'}}

    def write_policy(self):
        path = self.root / POLICY_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.policy))

    def asset(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    def record(self):
        return {'id': 'TEST-source-occurrence', 'source_id': 'TEST-source', 'language': 'ja',
            'book_key': 'hadeethenc', 'provider_entry_id': '65015', 'text_arabic': TEST_ARABIC,
            'text_translation': 'TEST unchanged primary translation', 'references': {},
            'edition': 'TEST-edition', 'source': {'name': 'TEST source',
                'original_file': 'TEST-original.txt', 'sha256': sha('TEST original source')},
            'translation_provenance': {'current_policy': {'classification': 'human'}}}

    def provider_fixture(self):
        english, arabic = self.root / 'english.sqlite', self.root / 'arabic.sqlite'
        with closing(sqlite3.connect(english)) as connection, connection:
            connection.execute('CREATE TABLE hadeeths(id INTEGER,hadeeth TEXT,hadeeth_ar TEXT,ar_version INTEGER)')
            connection.execute('INSERT INTO hadeeths VALUES(?,?,?,?)', (65015, TEST_ENGLISH, TEST_ARABIC, 2))
        with closing(sqlite3.connect(arabic)) as connection, connection:
            connection.execute('CREATE TABLE hadeeths(id INTEGER,hadeeth TEXT,version INTEGER,reference TEXT)')
            connection.execute('INSERT INTO hadeeths VALUES(?,?,?,?)', (65015, TEST_ARABIC, 2, ''))
        info = lambda path: {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        self.asset(MANIFEST, json.dumps({'schema': 'hadith-bank-hadeethenc-counterpart-sources-v1',
            'english_database': info(english), 'arabic_database': info(arabic), 'english_version': 'TEST'}).encode())
        self.asset('TEST-original.txt', b'TEST original source')
        return english, arabic

    def reviewed_fixture(self, record):
        reference = {'book_key': 'muslim', 'collection': 'TEST collection', 'number': '1',
                     'numbering_scheme': 'TEST source numbering', 'scope': 'main_quote'}
        entry = {'id': 'TEST-reviewed-target', 'arabic': {**self.value['arabic'],
            'source_url': 'https://example.invalid/TEST/ar', 'references': [reference]},
            'english': {**self.english, 'references': [reference]}}
        mapping = {'record_id': record['id'], 'source_id': record['source_id'], 'language': record['language'],
            'source_text_sha256': sha(record['text_translation']), 'source_file_sha256': record['source']['sha256'],
            'target_id': entry['id'], 'target_text_sha256': {'arabic': sha(TEST_ARABIC), 'english': sha(TEST_ENGLISH)},
            'relation': 'same_narration', 'review': {'status': 'verified', 'reviewer': 'TEST reviewer',
                'method': 'TEST content comparison', 'human_review': False,
                'evidence': ['TEST exact source and target comparison']}}
        bundle = {'id': 'TEST-generic-bundle', 'provider': 'hadith-bank-reviewed-source-alignment',
            'source_name': 'TEST reviewed source', 'source_snapshot': 'TEST snapshot',
            'publication': {'authorized': True}, 'source_assets': [self.asset('TEST-original.txt', b'TEST original source')],
            'entries': self.asset('TEST-entries.jsonl', (json.dumps(entry) + '\n').encode()),
            'mappings': self.asset('TEST-mappings.jsonl', (json.dumps(mapping) + '\n').encode())}
        self.asset(REVIEWED_MANIFEST, json.dumps({'schema': REVIEWED_SCHEMA, 'bundles': [bundle]}).encode())

    def test_exact_source_is_withheld_without_reclassifying_or_modifying_input(self):
        before = copy.deepcopy(self.value)
        result = apply_quality_policy(self.value, self.policy)
        self.assertEqual(self.value, before)
        self.assertIsNone(result['english'])
        self.assertEqual(result['arabic'], before['arabic'])
        self.assertEqual(result['status'], 'exact')
        history = result['withheld_languages']['english']
        self.assertEqual(history['translation_origin'], 'human')
        self.assertEqual(history['current_translation_policy']['classification'], 'human')
        self.assertEqual(history['actual_text_sha256'], sha(TEST_ENGLISH))
        self.assertNotIn('text', history)
        self.assertIn('withheld', result['quality_advisories'][0]['message'])
        self.assertEqual(apply_quality_policy(result, self.policy), result)

    def test_changed_actual_hash_other_provider_or_other_id_is_not_withheld(self):
        variants = [
            {'text': TEST_ENGLISH + ' TEST corrected wording'},
            {'source_record_id': '65016'},
            {'source_url': 'https://example.invalid/en/browse/hadith/65015'},
            {'source_url': 'https://hadeethenc.com/en/browse/hadith/65016'},
            {'provider': 'another-provider'},
            {'source_url': 'https://hadeethenc.com.example.invalid/en/browse/hadith/65015'},
            {'source_url': 'https://user@hadeethenc.com/en/browse/hadith/65015'}]
        for changes in variants:
            with self.subTest(changes=changes):
                value = copy.deepcopy(self.value); value['english'].update(changes)
                self.assertEqual(apply_quality_policy(value, self.policy), value)

    def test_declared_hash_cannot_hide_the_exact_actual_english_bytes(self):
        value = copy.deepcopy(self.value); value['english']['text_sha256'] = 'f' * 64
        self.assertIsNone(apply_quality_policy(value, self.policy)['english'])
        value['english']['provider'] = 'HadeethEnc'
        self.assertIsNone(apply_quality_policy(value, self.policy)['english'])

    def test_withheld_source_is_neither_text_nor_external_availability_or_search(self):
        record = {**self.record(), 'counterparts': apply_quality_policy(self.value, self.policy)}
        self.assertIsNone(counterpart_source_data(record, 'english'))
        self.assertEqual(availability_for(record), {'arabic': 'text', 'english': 'missing'})
        self.assertNotIn(TEST_ENGLISH, list(counterpart_search_values(record)))
        self.assertIn(TEST_ARABIC, list(counterpart_search_values(record)))

    def test_absent_policy_preserves_standalone_behavior(self):
        (self.root / POLICY_PATH).unlink()
        self.assertIsNone(load_quality_policy(self.root))
        self.assertIs(apply_quality_policy(self.value, None), self.value)

    def test_malformed_policy_cannot_silently_disable_an_expected_decision(self):
        self.policy['decisions'][0]['text_sha256'] = 'TEST invalid hash'
        self.write_policy()
        with self.assertRaisesRegex(ValueError, 'exact supported'):
            load_quality_policy(self.root)

    def test_partial_source_stays_searchable_with_exact_text_origin_and_visible_scope(self):
        decision = self.policy['decisions'][0]
        decision.update(action=PARTIAL_ACTION, citation_note='TEST English covers the opening question only.',
                        message='TEST English is a bounded excerpt.')
        self.write_policy(); policy = load_quality_policy(self.root)
        self.value['english']['citation_note'] = 'TEST existing source qualification.'
        before = copy.deepcopy(self.value)
        result = apply_quality_policy(self.value, policy)
        self.assertEqual(self.value, before)
        self.assertEqual(result['english']['text'], TEST_ENGLISH)
        self.assertEqual(result['english']['text_sha256'], sha(TEST_ENGLISH))
        self.assertEqual(result['english']['translation_origin'], 'human')
        self.assertEqual(result['english']['source_scope'], 'full_narration')
        self.assertEqual(result['english']['scope'], 'source_excerpt')
        self.assertEqual(result['english']['coverage'], 'partial')
        self.assertIn('TEST existing source qualification.', result['english']['citation_note'])
        record = {**self.record(), 'counterparts': result}
        self.assertEqual(availability_for(record)['english'], 'text')
        self.assertIn(TEST_ENGLISH, list(counterpart_search_values(record)))
        self.assertIn('opening question only', counterpart_qualification(result['english'], record))
        self.assertEqual(apply_quality_policy(result, policy), result)
        corrected = copy.deepcopy(self.value); corrected['english']['text'] += ' TEST new version'
        self.assertEqual(apply_quality_policy(corrected, policy), corrected)

    def test_partial_qualification_cannot_override_an_exact_source_hold(self):
        decision = copy.deepcopy(self.policy['decisions'][0])
        decision.update(id='test-partial-decision', action=PARTIAL_ACTION,
                        citation_note='TEST English covers the opening question only.')
        self.policy['decisions'].append(decision)
        self.write_policy()
        result = apply_quality_policy(self.value, load_quality_policy(self.root))
        self.assertIsNone(result['english'])
        self.assertEqual(result['withheld_languages']['english']['quality_decision_ids'],
                         ['test-exact-quality-decision'])

    def test_partial_qualification_without_a_specific_note_is_rejected(self):
        self.policy['decisions'][0]['action'] = PARTIAL_ACTION
        self.write_policy()
        with self.assertRaisesRegex(ValueError, 'specific citation note'):
            load_quality_policy(self.root)

    def test_final_hook_covers_primary_resolver_and_keeps_original_sqlite_bytes(self):
        paths = self.provider_fixture(); record = self.record(); before = copy.deepcopy(record)
        originals = {path: path.read_bytes() for path in paths}
        with patch('resolve_counterparts.load_quality_policy', wraps=load_quality_policy) as loader:
            resolver = CounterpartResolver(self.root, [record])
            result = resolver.for_record(record)
            resolver.for_record(record)
            self.assertEqual(loader.call_count, 1)
        self.assertIsNone(result['english'])
        self.assertEqual(result['arabic']['text'], TEST_ARABIC)
        self.assertEqual(result['withheld_languages']['english']['translation_origin'], 'human')
        self.assertIn(POLICY_PATH, resolver.assets)
        self.assertEqual(record, before)
        self.assertEqual({path: path.read_bytes() for path in paths}, originals)

    def test_final_hook_covers_generic_reviewed_bundle_from_own_language_identity(self):
        record = self.record(); self.reviewed_fixture(record)
        originals = {path: path.read_bytes() for path in self.root.glob('TEST-*')}
        self.assertEqual(ReviewedCounterpartResolver(self.root).for_record(record)['english']['text'], TEST_ENGLISH)
        result = CounterpartResolver(self.root, [record]).for_record(record)
        self.assertEqual(result['status'], 'reviewed_parallel')
        self.assertIsNone(result['english'])
        self.assertEqual(result['arabic']['text'], TEST_ARABIC)
        self.assertEqual(result['withheld_languages']['english']['translation_origin'], 'human')
        self.assertEqual({path: path.read_bytes() for path in originals}, originals)


if __name__ == '__main__':
    unittest.main()
