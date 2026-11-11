"""Source-risk regressions for the fixed, owner-supplied Chinese Word edition.

These checks inspect the published candidate and source bytes independently of
the importer. They establish preservation and integration behavior, not hadith
authenticity or independent translation certification.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from citation_search import has_noncanonical_numbering, record_citation_pairs
from counterpart_identity import provider_identity
from current_provenance import classification
from review_display_policy import review_badges

MATERIAL = ROOT / 'materials/zh-abu-dawud-yu-2002-doc'
SOURCE_SHA256 = 'cbff2d2c521e553c6eb11a75d6079fe526930295b7a3fc4726cc8e7a4e0a42c8'


class ChineseAbuDawudSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((MATERIAL / 'manifest.json').read_text(encoding='utf-8'))
        cls.source = (ROOT / cls.manifest['source']['path']).read_bytes()
        cls.native = (MATERIAL / 'native-text.txt').read_text(encoding='utf-8')
        cls.rows = [json.loads(line) for line in (MATERIAL / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
        cls.ledger = json.loads((MATERIAL / 'source-number-ledger.json').read_text(encoding='utf-8'))['entries']
        cls.exclusions = json.loads(gzip.decompress((MATERIAL / 'excluded-commentary.json.gz').read_bytes()))['items']
        cls.metadata = json.loads((MATERIAL / 'source-metadata.json').read_text(encoding='utf-8'))
        cls.plan = json.loads((MATERIAL / 'extraction-plan.json').read_text(encoding='utf-8'))

    def test_original_doc_and_registered_hashes(self):
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), SOURCE_SHA256)
        self.assertEqual(self.manifest['source']['sha256'], SOURCE_SHA256)
        self.assertEqual(self.manifest['source']['format'], 'doc')
        self.assertEqual(hashlib.sha256((MATERIAL / 'records.jsonl').read_bytes()).hexdigest(), self.manifest['records']['sha256'])
        self.assertEqual(self.manifest['records']['count'], len(self.rows))

    def test_native_text_is_present_byte_for_byte_in_original_word_data(self):
        # Independent check for this fixed file: removing its physical FAT
        # sectors exposes the entire native UTF-16LE text as one byte string.
        # It does not call the importer's CFB/CLX decoding implementation.
        self.assertEqual(struct.unpack_from('<I', self.source, 72)[0], 0)
        sector_size = 1 << struct.unpack_from('<H', self.source, 30)[0]
        fat_ids = {sid for sid in struct.unpack_from('<109I', self.source, 76) if sid < 0xfffffff0}
        physical = self.source[:sector_size] + b''.join(
            self.source[start:start + sector_size]
            for start in range(sector_size, len(self.source), sector_size)
            if start // sector_size - 1 not in fat_ids)
        encoded = self.native.replace('\n', '\r').encode('utf-16le')
        self.assertEqual(len(self.native), 304619)
        self.assertEqual(physical.count(encoded), 1)
        self.assertEqual(hashlib.sha256(self.native.encode()).hexdigest(), self.metadata['extraction']['native_text_sha256'])

    def test_every_imported_character_has_exact_source_spans(self):
        all_spans = []
        for row in self.rows:
            location = row['source_locator']
            spans = location['included_source_spans']
            self.assertTrue(spans, row['id'])
            self.assertEqual(''.join(self.native[a:b] for a, b in spans), row['text']['translation'], row['id'])
            low, high = location['source_span']
            self.assertTrue(all(low <= a < b <= high for a, b in spans), row['id'])
            self.assertTrue(all(spans[i][1] <= spans[i + 1][0] for i in range(len(spans) - 1)), row['id'])
            all_spans.extend(spans)
        all_spans.sort()
        self.assertTrue(all(all_spans[i][1] <= all_spans[i + 1][0] for i in range(len(all_spans) - 1)))

    def test_reviewed_comments_and_headings_do_not_leak_into_narrations(self):
        removed = [item['span'] for item in self.exclusions]
        for item in self.exclusions:
            a, b = item['span']
            self.assertEqual(self.native[a:b], item['text'])
        for row in self.rows:
            for a, b in row['source_locator']['included_source_spans']:
                self.assertFalse(any(a < right and left < b for left, right in removed), row['id'])
            self.assertNotRegex(row['text']['translation'], r'(?m)^\s*(?:注[：:]|\d+、论)')
            self.assertNotRegex(row['text']['translation'], r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]')
            self.assertEqual(row['commentary'], {'arabic': None, 'translation': None})
            self.assertEqual(row['footnotes'], [])

    def test_source_occurrences_and_six_numbered_glosses_are_accounted_for(self):
        self.assertEqual(len(self.ledger), 2834)
        self.assertEqual(len(self.rows), 2828)
        self.assertEqual(len({row['id'] for row in self.rows}), 2828)
        imported = {item['id'] for item in self.ledger if item['imported']}
        self.assertEqual(imported, {row['id'] for row in self.rows})
        excluded = {item['source_entry_id'] for item in self.ledger if not item['imported']}
        self.assertEqual(excluded, {'1432', '1434', '1440', '2604', '2847', '2866'})
        self.assertFalse(excluded & {row['number']['in_book'] for row in self.rows})

    def test_four_duplicated_printed_numbers_keep_distinct_occurrences(self):
        counts = Counter(row['number']['in_book'] for row in self.rows)
        self.assertEqual({key: count for key, count in counts.items() if count > 1},
                         {'1599': 2, '2455': 2, '2489': 2, '2505': 2})
        for number in ('1599', '2455', '2489', '2505'):
            pair = [row for row in self.rows if row['number']['in_book'] == number]
            self.assertNotEqual(pair[0]['id'], pair[1]['id'])
            self.assertNotEqual(pair[0]['text']['translation'], pair[1]['text']['translation'])
            self.assertTrue(all(row['source_defects'] for row in pair))

    def test_five_embedded_entry_starts_are_retained_separately(self):
        embedded = [entry for entry in self.plan['entry_starts'] if entry['char_offset'] > 0]
        self.assertEqual({entry['printed_number'] for entry in embedded}, {'763', '1000', '1250', '2070', '2201'})
        offsets, position = [], 0
        for paragraph in self.native.split('\n'):
            offsets.append(position)
            position += len(paragraph) + 1
        by_start = {row['source_locator']['source_span'][0]: row for row in self.rows}
        for entry in embedded:
            start = offsets[entry['paragraph_index']] + entry['char_offset']
            row = by_start[start]
            self.assertEqual(row['number']['in_book'], entry['printed_number'])
            self.assertTrue(any('inside the preceding paragraph' in issue for issue in row['source_defects']))

    def test_local_numbers_never_become_canonical_or_provider_identity(self):
        for row in self.rows:
            self.assertIsNone(row['number']['canonical'], row['id'])
            self.assertTrue(has_noncanonical_numbering(row['number']), row['id'])
            self.assertEqual(record_citation_pairs(row), set(), row['id'])
            self.assertEqual(provider_identity(row)['status'], 'absent', row['id'])
            self.assertIsNone(provider_identity(row)['id'], row['id'])

    def test_native_human_provenance_and_unperformed_certification_remain_distinct(self):
        self.assertIn('穆萨·余崇仁书', self.native)
        self.assertIn('2002年8月于银川新城', self.native)
        self.assertTrue(self.manifest['publication']['authorized'])
        self.assertNotIn('display_policy', self.manifest)
        for row in self.rows:
            self.assertEqual(classification(row), 'human')
            self.assertFalse(row['ai_translation'])
            self.assertFalse(row['extraction']['ocr_used'])
            self.assertEqual(review_badges(row), [])
            self.assertIsNone(row['text']['arabic'])
            self.assertIsNone(row['grading']['grade'])
            self.assertEqual(row['review']['independent_pro_qc'], 'not_performed')
            self.assertFalse(row['review']['certified_release_eligible'])
            self.assertEqual(row['rights']['status'], 'not_assessed_for_publication')

    def test_source_extent_and_actual_mid_sentence_fragment_stay_visible(self):
        self.assertFalse(self.metadata['completeness']['full_collection'])
        self.assertEqual(self.metadata['completeness']['last_printed_number'], '2868')
        self.assertIn('partial', self.manifest['source']['name'])
        fragment = next(row for row in self.rows if row['source_locator']['source_span'][0] == 253672)
        self.assertEqual(fragment['number']['in_book'], '2455')
        self.assertTrue(fragment['text']['translation'].endswith('白尼·奈迪尔被驱逐时，'))
        self.assertTrue(fragment['extraction']['is_excerpt'])
        self.assertEqual(fragment['content_kind'], 'source_fragment')
        self.assertTrue(any('truncat' in note.lower() or 'mid-sentence' in note.lower() for note in fragment['source_defects']))
        self.assertEqual(record_citation_pairs(fragment), set())


if __name__ == '__main__':
    unittest.main()
