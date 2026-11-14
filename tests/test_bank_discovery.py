"""Synthetic search/index acceptance fixtures; none is a religious source."""
import copy
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from bank_discovery import (build_discovery_payload, normalize, tokenize,
                            serialize_discovery, write_discovery_artifact,
                            quotation_fingerprint_bytes, load_discovery_material_metadata, expand_discovery_payload,
                            expected_discovery_row, validate_discovery_posting, expected_discovery_segments)


def record(identifier, language='en', text='TEST source wording', **values):
    result = {'id': identifier, 'language': language, 'source_language_code': language,
              'book_key': 'bukhari', 'edition': 'TEST-edition', 'source_id': 'TEST-source',
              'title': 'TEST title', 'text_translation': text, 'text_arabic': None,
              'number': {'in_book': None, 'source_entry_id': None}, 'narrator': {'name': None},
              'source': {'name': 'TEST publisher', 'record_url': 'https://example.invalid/TEST/' + identifier,
                         'original_file': 'sources/TEST.pdf', 'sha256': 'a' * 64},
              'translator': {'name': 'TEST Translator'},
              'translation_provenance': {'ai_translation': False}, 'topic_tags': [], 'editorial_tags': [],
              'source_headings': [], 'review': {'status': 'pending'}, 'references': {},
              'commentary': {'translation': 'TEST hiddenannotationword'}, 'footnotes': []}
    result.update(values)
    return result


def fixtures():
    family_arabic = 'نَصٌّ تَجْرِيبِيٌّ مُشْتَرَكٌ'
    first = record('TEST-provider-en', text='TEST actions depend on intentions. This is synthetic wording.',
                   book_key='hadeethenc', provider_entry_id='100', text_arabic=family_arabic,
                   references={'items': [{'book_key': 'bukhari', 'number': '1', 'scope': 'narration'}]})
    first['source']['record_url'] = 'https://hadeethenc.com/en/browse/hadith/100'
    second = record('TEST-provider-ja', language='ja', text='合成資料。行為は意図に従う。',
                    book_key='hadeethenc', provider_entry_id='100', text_arabic=family_arabic,
                    references={'items': [{'book_key': 'bukhari', 'number': '1', 'scope': 'narration'}]})
    second['source']['record_url'] = 'https://hadeethenc.com/ja/browse/hadith/100'
    third = record('TEST-local-one', text='TEST actions appear here, and intentions appear later, depend on wording.',
                   number={'in_book': '1', 'numbering_system': 'provider_sequence'}, provider_entry_id='1')
    fourth = record('TEST-facets', text='TEST kindness to parents and a mother. Synthetic example.',
                    source_headings=['TEST Book / TEST Chapter'], narrator={'name': 'TEST Named Narrator'},
                    record_type='companion_report', grading={'grade': 'TEST Grade', 'grader': 'TEST Authority'},
                    topic_tags=[{'id': 'TEST-source-topic', 'label': 'TEST Published Topic', 'path': ['TEST Category']}])
    fifth = record('TEST-anger', text='TEST angry expression. Synthetic source text.', grading={'grade': 'TEST Uncredited', 'grader': None})
    sixth = record('TEST-arabic', language='ar', text='تَجْرِيب أَعْمَال وَنِيَّات وَالصَّلَاة', text_arabic='تَجْرِيب أَعْمَال وَنِيَّات وَالصَّلَاة')
    seventh = record('TEST-long', text=('TEST prefix ' * 60) + 'needleword late matching phrase نهاية')
    eighth = record('TEST-zh', language='zh-CN', text='合成资料：父母与孩子。行为和意图。')
    ninth = record('TEST-hi', language='hi', text='परीक्षण की माता पिता और प्रार्थना')
    tenth = record('TEST-other-route', book_key='hadeethenc', provider_entry_id='100', text_arabic='نَصٌّ آخَرُ مُخْتَلِفٌ')
    tenth['source']['record_url'] = 'https://hadeethenc.com/en/browse/hadith/100'
    return [first, second, third, fourth, fifth, sixth, seventh, eighth, ninth, tenth]


def payload():
    records = fixtures()
    return build_discovery_payload(records, {'record_count': len(records), 'records_sha256': 'b' * 64})


def broader_payload():
    records = [record('TEST-broader-positive', text='TEST actions are judged by intentions.'),
               record('TEST-broader-negative', text='TEST Do not base actions on intentions alone.'),
               record('TEST-broader-one-word', text='TEST actions are described here.'),
               record('TEST-broader-metadata', text='TEST intentions appear here.', title='TEST actions'),
               record('TEST-broader-ar-positive', language='ar', text='TEST تجريب عمل'),
               record('TEST-broader-ar-negative', language='ar', text='TEST لا تجريب عمل'),
               record('TEST-broader-separate-readings', text='TEST actions are judged by intentions.',
                      language_versions=[{'id': 'TEST-other-reading', 'language': 'en', 'text': 'TEST Never invent source words.',
                                          'scope': 'source_entry', 'source': {'name': 'TEST alternative'}}])]
    return build_discovery_payload(records, {'record_count': len(records), 'records_sha256': 'c' * 64})


class BankDiscoveryTests(unittest.TestCase):
    def test_source_preservation_and_determinism(self):
        records = fixtures(); original = copy.deepcopy(records)
        first = build_discovery_payload(iter(records), {'record_count': len(records)})
        second = build_discovery_payload(iter(records), {'record_count': len(records)})
        self.assertEqual(records, original)
        self.assertEqual(serialize_discovery(first), serialize_discovery(second))
        self.assertEqual(first['occurrence_ids_sha256'], hashlib.sha256(''.join(item['id'] + '\n' for item in records).encode()).hexdigest())
        self.assertEqual(first['indexed_quotation_fields_sha256'], hashlib.sha256(b''.join(quotation_fingerprint_bytes(item) for item in records)).hexdigest())
        self.assertNotIn('hiddenannotationword', first['terms'])
        self.assertIn('needleword', first['terms'])
        self.assertNotIn('needleword', first['rows'][6]['readings'][0]['text'])

    def test_safe_multiscript_normalization(self):
        self.assertEqual(normalize('أَعْمَال إيمان آداب'), normalize('اعمال ايمان اداب'))
        self.assertEqual(normalize('كِتاب يَكي ١۲'), normalize('کتاب يكي 12'))
        self.assertEqual(normalize('ṣalāh'), 'salah')
        self.assertEqual(tokenize('日 本語'), ('日', '本', '語'))
        self.assertNotEqual(tokenize('की'), tokenize('क'))
        self.assertEqual(normalize('ガ'), 'ガ')

    def test_canonical_local_and_provider_numbers_remain_distinct(self):
        data = payload()
        self.assertEqual(data['reference_index']['bukhari:1'], [0, 1])
        self.assertEqual(data['rows'][2]['sourceNumber'], '1')
        self.assertEqual(data['rows'][2]['providerNumber'], '1')
        self.assertEqual(data['rows'][2]['references'], [])

    def test_provider_families_require_identity_and_exact_arabic(self):
        data = payload()
        self.assertEqual(len(data['groups']), 1)
        self.assertEqual(data['groups'][0]['members'], [0, 1])
        self.assertIsNone(data['rows'][9]['groupId'])
        self.assertIsNone(data['rows'][2]['groupId'])
        changed = fixtures()
        changed[1]['source']['record_url'] = 'https://hadeethenc.com/ja/browse/hadith/999'
        self.assertFalse(build_discovery_payload(changed, {})['groups'])

    def test_same_labels_do_not_unite_unrelated_editions(self):
        first = record('TEST-1')
        second = record('TEST-2', source_id='TEST-other-source')
        second['source']['sha256'] = 'c' * 64
        data = build_discovery_payload([first, second], {})
        self.assertNotEqual(data['rows'][0]['editionGroup'], data['rows'][1]['editionGroup'])
        self.assertNotEqual(data['rows'][0]['editionLabel'], data['rows'][1]['editionLabel'])
        self.assertFalse(data['groups'])

    def test_facets_are_own_source_metadata_and_unknown_grader_stays_unknown(self):
        data = payload()
        self.assertEqual(data['rows'][3]['narrators'], ['TEST Named Narrator'])
        self.assertEqual(data['rows'][3]['reportType'], 'companion_report')
        self.assertEqual(data['rows'][3]['grades'][0]['authority'], 'TEST Authority')
        self.assertEqual(data['rows'][4]['grades'], [])
        self.assertEqual(data['rows'][4]['unattributedGrades'], ['TEST Uncredited'])
        self.assertEqual(data['rows'][2]['reportType'], 'unknown')
        self.assertEqual(data['rows'][3]['topics'][0]['origin'], 'source')

    def test_no_source_context_as_stored_counterpart(self):
        item = record('TEST-boundary')
        item['language_versions'] = [{'id': 'TEST-link', 'language': 'ur', 'scope': 'external_source',
            'quotation_status': 'boundary_pending', 'text': None, 'source': {'name': 'TEST source', 'url': 'https://example.invalid/TEST'},
            'comments': [{'text': 'do-not-index-context', 'scope': 'source_context_not_narration'}]}]
        data = build_discovery_payload([item], {})
        self.assertNotIn('ur', data['rows'][0]['languages'])
        self.assertEqual(data['rows'][0]['languageStates']['ur'], 'pending_review')
        self.assertNotIn('context', data['terms'])

    def test_pending_or_mismatched_english_is_not_counterpart_availability(self):
        for status, scope in [('boundary_pending', 'external_source'), ('attribution_pending', 'external_source'),
                              ('content_mismatch', 'source_context')]:
            with self.subTest(status=status):
                item = record('TEST-boundary', language='ar', text='تجريب')
                item['language_versions'] = [{'id': 'TEST-en', 'language': 'en', 'text': None,
                    'scope': scope, 'quotation_status': status, 'source': {'name': 'TEST', 'url': 'https://example.invalid/TEST'},
                    'comments': [{'text': 'unrelated preserved context', 'scope': 'source_context_not_narration'}]}]
                row = build_discovery_payload([item], {})['rows'][0]
                self.assertEqual(row['availability']['english'], 'missing')
                self.assertNotIn('en', row['languages'])

    def test_source_hierarchy_is_explicit_and_narration_titles_are_not_books(self):
        item = record('TEST-hierarchy')
        item['source_structure_tags'] = [
            {'origin': 'source_book_structure', 'hierarchy': 2, 'value_verbatim': 'TEST Chapter'},
            {'origin': 'source_book_structure', 'hierarchy': 1, 'value_verbatim': 'TEST Book'}]
        data = build_discovery_payload([item, record('TEST-unclassified-title')], {})
        self.assertEqual(data['rows'][0]['sourcePath'], ['TEST Book', 'TEST Chapter'])
        self.assertEqual(data['rows'][0]['sourceBooks'], ['TEST Book'])
        self.assertIn('TEST Chapter', data['rows'][0]['chapters'])
        self.assertEqual(data['rows'][1]['sourceBooks'], [])

    def test_source_row_metadata_helper_matches_producer_and_namespaces_categories(self):
        items = fixtures()
        data = build_discovery_payload(items, {})
        for ordinal, item in enumerate(items):
            expected = expected_discovery_row(item, ordinal)
            self.assertEqual(data['rows'][ordinal]['searchSegments'], expected_discovery_segments(item))
            for key, value in expected.items():
                if key != 'editionLabel':
                    self.assertEqual(data['rows'][ordinal][key], value, key)
        category = data['rows'][3]['topics'][0]
        self.assertEqual(category['sourceTopicId'], 'TEST-source-topic')
        self.assertTrue(category['value'].startswith(data['rows'][3]['editionGroup'] + '\x1f'))
        other = copy.deepcopy(items[3]); other['id'] += '-other'; other['source']['sha256'] = 'f' * 64
        combined = build_discovery_payload([items[3], other], {})
        self.assertNotEqual(combined['rows'][0]['topics'][0]['value'], combined['rows'][1]['topics'][0]['value'])

    def test_friendly_edition_prefers_accepted_work_name_over_entry_title(self):
        item = record('TEST-narration-heading')
        item['source']['name'] = 'TEST Individual narration title'
        material = {'dataset_id': item['source_id'], 'source_name': 'TEST Accepted source edition'}
        row = build_discovery_payload([item], {'materials': [material]})['rows'][0]
        self.assertEqual(row['sourceName'], 'TEST Accepted source edition')
        self.assertIn('TEST Accepted source edition', row['editionLabel'])
        self.assertEqual(item['source']['name'], 'TEST Individual narration title')
        item['source']['work_title'] = 'TEST Exact supplied work title'
        self.assertEqual(expected_discovery_row(item, 0, material)['sourceName'], 'TEST Accepted source edition')
        self.assertEqual(expected_discovery_row(item, 0)['sourceName'], 'TEST Exact supplied work title')
        self.assertEqual(item['source']['work_title'], 'TEST Exact supplied work title')
        item['edition'] = 'legacy-embedded-ae2c075-v1'
        self.assertNotIn(item['edition'], expected_discovery_row(item, 0, material)['editionLabel'])
        item['source']['edition'] = 'Second edition, 1987'
        self.assertIn('Second edition, 1987', expected_discovery_row(item, 0, material)['editionLabel'])
        material['source_name'] = 'TEST Named Work — Volume 2'
        self.assertIn('Volume 2', expected_discovery_row(item, 0, material)['editionLabel'])

    def test_posting_structure_validator_checks_real_wire_and_rejects_corruption(self):
        data = payload()
        for count, encoded in data['postings']:
            self.assertEqual(validate_discovery_posting(encoded, data['record_count'], count)['documents'], count)
        for wire, count in (([0, 1, 1, 1], 1), ([1, 128, 1, 1, 1], 1),
                            ([1, 1, 0], 1), ([1, 2, 1, 1], 1), ([1, 1, 1, 0], 1),
                            ([1, 1, 1], 1), ([128, 0, 1, 1, 1], 1),
                            ([1, 1, 1, 1], 2)):
            with self.subTest(wire=wire), self.assertRaises(ValueError):
                validate_discovery_posting(base64.b64encode(bytes(wire)).decode(), 2, count)

    def test_ambiguous_raw_ids_cannot_form_provider_families(self):
        items = fixtures()[:2]
        items[1]['id'] = items[0]['id']
        data = build_discovery_payload(items, {})
        self.assertFalse(data['groups'])
        self.assertTrue(all(row['groupId'] is None for row in data['rows']))

    def test_counterpart_grouping_requires_exact_current_source_binding(self):
        first = fixtures()[0]
        other = record('TEST-reviewed', text_arabic='تجريب')
        target = first['text_arabic']
        other['counterparts'] = {'status': 'exact', 'match_method': 'provider_id_and_source_quotation',
            'provider_identity': {'provider': 'hadeethenc', 'id': '100', 'status': 'linked'},
            'quotation_evidence': {'field': 'text_arabic', 'relation': 'source_excerpt',
                'source_text_sha256': hashlib.sha256(other['text_arabic'].encode()).hexdigest(),
                'target_text_sha256': hashlib.sha256(target.encode()).hexdigest()},
            'arabic': {'text': target, 'source_url': 'https://hadeethenc.com/ar/browse/hadith/100', 'scope': 'full_narration'}}
        data = build_discovery_payload([first, other], {})
        self.assertEqual(data['groups'][0]['members'], [0, 1])
        other['counterparts']['quotation_evidence']['source_text_sha256'] = '0' * 64
        self.assertFalse(build_discovery_payload([first, other], {})['groups'])
        other['counterparts']['status'] = 'related_version'
        self.assertFalse(build_discovery_payload([first, other], {})['groups'])

    def test_manifest_enrichment_rejects_stale_registered_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'materials/TEST/manifest.json'; path.parent.mkdir(parents=True)
            manifest = {'id': 'TEST', 'source_id': 'TEST', 'language': 'en', 'book': 'bukhari', 'edition': 'TEST',
                        'source': {'sha256': 'a' * 64}, 'records': {'sha256': 'b' * 64},
                        'storage_shard': {'original_source_edition': 'TEST'}}
            path.write_text(json.dumps(manifest))
            material = {'dataset_id': 'TEST', 'language': 'en', 'book_key': 'bukhari', 'edition': 'TEST',
                        'source_sha256': 'a' * 64, 'canonical_records_sha256': 'b' * 64,
                        'manifest_path': 'materials/TEST/manifest.json'}
            output = load_discovery_material_metadata(folder, [material])
            self.assertEqual(output[0]['storage_shard'], manifest['storage_shard'])
            self.assertNotIn('storage_shard', material)
            material['canonical_records_sha256'] = 'c' * 64
            with self.assertRaisesRegex(ValueError, 'differs from accepted catalog'):
                load_discovery_material_metadata(folder, [material])

    def test_pdf_intake_pointer_is_scoped_without_inventing_chunk_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'materials/TEST/manifest.json'; path.parent.mkdir(parents=True)
            prefix = 'attachments/TEST-package'
            manifest = {'id': 'TEST-package', 'adapter': 'pdf-intake-package-v1', 'package_root': prefix,
                        'publication': {'authorized': True}, 'storage_shard': {'untrusted': True}}
            path.write_text(json.dumps(manifest))
            material = {'dataset_id': 'TEST-actual-source', 'adapter': 'pdf-intake-package-v1',
                        'manifest_path': 'materials/TEST/manifest.json', 'intake_root': prefix,
                        'publication': {'authorized': True}, 'source_file': prefix + '/source.pdf',
                        'canonical_records_path': prefix + '/records.json', 'source_metadata_path': prefix + '/source.json'}
            self.assertEqual(load_discovery_material_metadata(folder, [material]), [material])
            material['source_file'] = 'attachments/another/source.pdf'
            with self.assertRaisesRegex(ValueError, 'intake pointer differs'):
                load_discovery_material_metadata(folder, [material])

    def test_descriptor_verifies_exact_gzip_bytes_and_safe_path(self):
        with tempfile.TemporaryDirectory() as folder:
            data = payload()
            descriptor = write_discovery_artifact(data, folder, 'reader-data')
            compressed = (Path(folder) / Path(descriptor['path']).name).read_bytes()
            raw = gzip.decompress(compressed)
            self.assertEqual(len(compressed), descriptor['bytes'])
            self.assertEqual(hashlib.sha256(compressed).hexdigest(), descriptor['sha256'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), descriptor['uncompressed_sha256'])
            expanded = expand_discovery_payload(json.loads(raw))
            self.assertEqual([row['id'] for row in expanded['rows']], [row['id'] for row in data['rows']])
            self.assertTrue(all(not row['readings'] for row in expanded['rows']))
            self.assertEqual(expanded['indexed_quotation_fields_sha256'], data['indexed_quotation_fields_sha256'])
            self.assertTrue(descriptor['parts'])
            self.assertEqual(write_discovery_artifact(data, folder, 'reader-data'), descriptor)
            with self.assertRaises(ValueError):
                write_discovery_artifact(data, folder, '../escape')

    def test_count_and_duplicate_full_identity_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'record count'):
            build_discovery_payload([record('TEST-a')], {'record_count': 2})
        with self.assertRaisesRegex(ValueError, 'full occurrence identity'):
            build_discovery_payload([record('TEST-a'), record('TEST-a')], {})
        data = build_discovery_payload([record('TEST-a'), record('TEST-a', edition='TEST-second')], {})
        self.assertEqual(data['record_count'], 2)
        self.assertEqual([row['id'] for row in data['rows']], ['TEST-a', 'TEST-a'])

    def test_partition_evidence_is_required_for_differing_source_bytes(self):
        a = record('TEST-a', source_id='deenhindi-bukhari', edition='deenhindi-web-20261112')
        b = record('TEST-b', source_id='deenhindi-bukhari-part-002', edition='deenhindi-web-20261112-part-002')
        b['source']['sha256'] = 'b' * 64
        materials = []
        for item in (a, b):
            materials.append({'dataset_id': item['source_id'], 'manifest_path': 'materials/' + item['source_id'] + '/manifest.json',
                              'source_descriptor': {'format': 'html_snapshot_index', 'url': 'https://deenhindi.com/hadith/bukhari'},
                              'storage_shard': {'original_source_edition': 'deenhindi-web-20261112', 'original_source_id': 'deenhindi-bukhari', 'occurrence_ids_unchanged': True}})
        plain = build_discovery_payload([a, b], {})
        evidence = build_discovery_payload([a, b], {'materials': materials})
        self.assertNotEqual(plain['rows'][0]['editionGroup'], plain['rows'][1]['editionGroup'])
        self.assertEqual(evidence['rows'][0]['editionGroup'], evidence['rows'][1]['editionGroup'])
        self.assertEqual(evidence['rows'][1]['editionEvidence']['sha256'], 'b' * 64)


if __name__ == '__main__':
    if '--fixture' in sys.argv:
        print(json.dumps(payload(), ensure_ascii=False, separators=(',', ':')))
    elif '--broader-fixture' in sys.argv:
        print(json.dumps(broader_payload(), ensure_ascii=False, separators=(',', ':')))
    elif '--sharded-fixture' in sys.argv:
        import bank_discovery
        bank_discovery.MAX_POSTING_PART_BYTES = 256
        bank_discovery.PREVIEW_ROWS_PER_PART = 2
        directory = sys.argv[sys.argv.index('--sharded-fixture') + 1]
        print(json.dumps(write_discovery_artifact(payload(), directory)))
    else:
        unittest.main()
