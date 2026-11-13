"""Bounded input planning for the existing CI Chromium gate; synthetic TEST data."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_reader
import verify_reader_browser as browser
from test_reader_grouping import records_fixture, mapping


@unittest.skipUnless(shutil.which('node'), 'Node is required for the real reader producer')
class BrowserGroupPlanningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.records = records_fixture()
        # Cross detail chunks and retain original unknown fields in the sampled export.
        self.records[1]['opaque_test_field'] = 'TEST raw bytes 日本語 ' * 900
        self.records[3]['opaque_test_field'] = 'TEST unrelated detail ' * 2000
        self.manifest = build_reader.write_lazy_reader_shards(
            self.records, self.root / 'index.html', self.root / 'data', 16384)
        self.snapshot = {'record_count': len(self.records), 'reader_groups': mapping(self.records)}

    def test_plan_prefers_new_ai_member_and_preserves_exact_group_objects(self):
        before = copy.deepcopy(self.records)
        plan = browser.actual_group_plan(self.root, self.manifest, self.snapshot)
        self.assertEqual(plan['member'], self.records[1]['id'])
        self.assertEqual(plan['group']['anchor_id'], self.records[0]['id'])
        self.assertEqual(plan['records'], {row['id']: row for row in self.records[:3]})
        self.assertEqual(self.records, before)
        self.assertNotIn(self.records[3]['id'], plan['records'])

    def test_source_book_language_and_ai_previews_keep_matching_representatives(self):
        plan = browser.actual_group_plan(self.root, self.manifest, self.snapshot)
        cases = [
            (lambda row: row['source_id'] == 'TEST-new', [1], 2),
            (lambda row: row['book_key'] == 'TEST-new-book', [1], 2),
            (lambda row: 'ja' in row['_reader']['languages'], [1, 3], 3),
            (lambda row: row['source_id'] == 'TEST-new' and row['_reader']['origin'] == 'ai', [1], 1),
            (lambda row: row['source_id'] == 'TEST-new' and row['_reader']['origin'] == 'human', [2], 1),
        ]
        for predicate, positions, occurrence_count in cases:
            with self.subTest(positions=positions, occurrences=occurrence_count):
                actual = browser.grouped_filter_preview(self.root, self.manifest,
                    self.snapshot['reader_groups']['groups'], plan['rows'], predicate)
                self.assertEqual(actual['first_page'], [self.records[index]['id'] for index in positions])
                self.assertEqual(actual['reading_cards'], len(positions))
                self.assertEqual(actual['source_occurrences'], occurrence_count)

    def test_unreferenced_detail_parts_are_not_read_and_corrupt_referenced_parts_fail(self):
        plan = browser.actual_group_plan(self.root, self.manifest, self.snapshot)
        chosen = {key: plan['rows'][key] for key in plan['group']['member_ids']}
        needed = browser.detail_paths(self.manifest, [
            row for _, row in browser.directory_rows(self.root, self.manifest)], [0, 1, 2])
        unneeded = [part for part in self.manifest['details']['shards'] if part['path'] not in needed]
        self.assertTrue(unneeded, 'The fixture must contain a detail part outside the sampled group')
        for part in unneeded:
            (self.root / part['path']).write_bytes(b'TEST corrupt unrelated part')
        self.assertEqual(browser.bounded_group_records(self.root, self.manifest, chosen), plan['records'])
        first = next(part for part in self.manifest['details']['shards'] if part['path'] in needed)
        (self.root / first['path']).write_bytes(b'TEST corrupt referenced part')
        with self.assertRaisesRegex(AssertionError, 'checksum mismatch'):
            browser.bounded_group_records(self.root, self.manifest, chosen)

    def test_absent_groups_are_not_applicable_and_oversized_sample_is_rejected(self):
        self.assertIsNone(browser.actual_group_plan(self.root, self.manifest, {'reader_groups': {'groups': []}}))
        plan = browser.actual_group_plan(self.root, self.manifest, self.snapshot)
        rows = copy.deepcopy({key: plan['rows'][key] for key in plan['group']['member_ids']})
        rows[plan['member']]['_reader']['detail'][1] = 8 * 1024 * 1024 + 1
        with self.assertRaisesRegex(AssertionError, 'detail budget'):
            browser.bounded_group_records(self.root, self.manifest, rows)


if __name__ == '__main__':
    unittest.main()
