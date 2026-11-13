"""Synthetic v2 reader production tests; fixture strings are not source quotations."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader


def record(index=1):
    return {
        'id': 'TEST-occurrence-' + str(index), 'language': 'en', 'book_key': 'bukhari',
        'edition': 'TEST edition', 'source_id': 'TEST source',
        'source': {'name': 'TEST publisher'}, 'translator': {},
        'translation_provenance': {'ai_translation': False}, 'review': {},
        'topic_tags': [], 'editorial_tags': [], 'source_headings': [], 'footnotes': [],
        'text_arabic': None, 'text_translation': 'TEST text ' + str(index),
        'title': None, 'number': {'in_book': index}, 'references': {},
    }


def compact(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


@unittest.skipUnless(shutil.which('node'), 'Node is required for exact JavaScript projections')
class LazyReaderProducerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'index.html'
        self.directory = self.root / 'data'
        self.records = [record(), record(2)]

    def build(self, **kwargs):
        return reader.write_lazy_reader_shards(self.records, self.output, self.directory, **kwargs)

    def stream(self, store):
        chunks = []
        for part in store['shards']:
            data = (self.root / part['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), part['sha256'])
            self.assertEqual(len(data), part['bytes'])
            plain = gzip.decompress(data)
            self.assertEqual(len(plain), part['uncompressed_bytes'])
            chunks.append(plain)
        raw = b''.join(chunks)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), store['jsonl_sha256'])
        return raw

    def snapshot(self, manifest):
        return {(self.root / part['path']): (self.root / part['path']).read_bytes()
                for part in reader._reader_manifest_parts(manifest)}

    def assert_snapshot(self, original):
        for path, data in original.items():
            self.assertEqual(path.read_bytes(), data, str(path))

    def test_exact_detail_bytes_v1_chunks_and_complete_projection_ranges(self):
        self.records[0]['text_translation'] = 'TEST العربية ۱۲۳ 漢字 🌿'
        self.records[0]['unknown_source_field'] = {'unchanged': '🌿أ漢' * 8000, 'flag': False}
        manifest = self.build(max_shard_bytes=4096)
        original = b''.join(map(compact, self.records))
        self.assertEqual(self.stream(manifest['details']), original)
        self.assertEqual(manifest['jsonl_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(manifest['max_detail_record_bytes'], max(map(lambda r: len(compact(r)), self.records)))
        legacy = reader.write_reader_shards(self.records, self.output, self.root / 'legacy', 4096)
        for old, new in zip(legacy['shards'], manifest['details']['shards']):
            self.assertEqual({key: old[key] for key in ('sha256', 'bytes', 'uncompressed_bytes', 'count')},
                             {key: new[key] for key in ('sha256', 'bytes', 'uncompressed_bytes', 'count')})
            self.assertEqual((self.root / old['path']).read_bytes(), (self.root / new['path']).read_bytes())
        self.assertEqual(len(legacy['shards']), len(manifest['details']['shards']))
        self.assertGreater(len(manifest['details']['shards']), 2)
        self.assertTrue(any(part['count'] == 0 for part in manifest['details']['shards']))
        position = 0
        for name in ('directory', 'search', 'annotations'):
            rows = self.stream(manifest[name]).splitlines(keepends=True)
            self.assertEqual(len(rows), len(self.records))
            self.assertEqual(manifest['max_projection_row_bytes'][name], max(map(len, rows)))
            ordinal = 0
            for part in manifest[name]['shards']:
                self.assertEqual(part['first_ordinal'], ordinal)
                self.assertEqual(part['count'], part['last_ordinal'] - ordinal + 1)
                ordinal += part['count']
            self.assertEqual(ordinal, len(self.records))
        directory = list(map(json.loads, self.stream(manifest['directory']).splitlines()))
        for row, full in zip(directory, self.records):
            span = row['_reader']['detail']
            self.assertEqual(span, [position, len(compact(full))])
            self.assertEqual(original[span[0]:sum(span)], compact(full))
            self.assertEqual(row['id'], full['id'])
            self.assertNotIn('unknown_source_field', row)
            position += span[1]
        self.assertEqual(position, len(original))
        self.assertEqual(json.loads((self.directory / 'manifest.json').read_text()), manifest)
        self.assertEqual(self.build(max_shard_bytes=4096), manifest)

    def test_projection_retains_search_and_filter_semantics_without_context_leakage(self):
        item = self.records[0]
        item.update(text_translation='TEST ۱۲۳ ٤٥٦ 漢字', text_arabic='TEST أَ',
                    number={'in_book': '٠٠١٢'}, narrator={'name': 'TEST narrator'},
                    extraction={'ocr_used': True}, review={'status': 'pending'},
                    translation_provenance={'ai_translation': True,
                                            'current_policy': {'classification': 'human'}})
        item['source']['original_context'] = 'TEST-only-context'
        item['language_versions'] = [
            {'id': 'TEST-ur', 'language': 'ur', 'text': None,
             'comments': [{'text': 'TEST-pending-sibling'}],
             'source': {'name': 'TEST publisher'}},
        ]
        item['footnotes'] = [{'text': 'TEST-footnote'}]
        item['grading'] = {'is_true': True, 'is_false': False, 'score': 319}
        manifest = self.build()
        directory = list(map(json.loads, self.stream(manifest['directory']).splitlines()))
        search = dict(map(json.loads, self.stream(manifest['search']).splitlines()))
        annotations = dict(map(json.loads, self.stream(manifest['annotations']).splitlines()))
        self.assertIn('123 456 漢字', search[0])
        self.assertIn('test narrator', search[0])
        self.assertIn('319', search[0])
        self.assertNotIn('true', search[0])
        self.assertNotIn('false', search[0])
        for context in ('test-only-context', 'test-pending-sibling', 'test-footnote'):
            self.assertNotIn(context, search[0])
            self.assertIn(context, annotations[0])
        meta = directory[0]['_reader']
        self.assertEqual(meta['origin'], 'human')
        self.assertEqual(meta['availability'], {'arabic': 'text', 'english': 'text'})
        self.assertTrue(meta['ocr_pending'])
        self.assertIn('bukhari:12', meta['citation_pairs'])
        item['number']['numbering_scheme'] = 'source_entry_sequence_not_canonical'
        item['display_policy'] = {'qc_tags': False}
        manifest = self.build()
        meta = json.loads(self.stream(manifest['directory']).splitlines()[0])['_reader']
        self.assertEqual(meta['citation_pairs'], [])
        self.assertFalse(meta['ocr_pending'])

    def test_empty_stores_and_metrics_have_valid_empty_digests(self):
        self.records = []
        manifest = self.build()
        self.assertEqual(manifest['record_count'], 0)
        self.assertEqual(manifest['max_detail_record_bytes'], 0)
        self.assertEqual(manifest['max_projection_row_bytes'],
                         dict(directory=0, search=0, annotations=0))
        for name in ('directory', 'search', 'annotations', 'details'):
            self.assertEqual(manifest[name]['shards'], [])
            self.assertEqual(manifest[name]['record_count'], 0)
            self.assertEqual(manifest[name]['jsonl_sha256'], hashlib.sha256(b'').hexdigest())

    def test_large_projection_is_rejected_without_truncating_or_replacing_previous_manifest(self):
        previous = self.build(max_shard_bytes=4096)
        snapshot = self.snapshot(previous)
        original_manifest = (self.directory / 'manifest.json').read_bytes()
        self.records[0]['text_translation'] = 'TEST oversized ' * 4000
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            self.build(max_shard_bytes=4096)
        self.assertEqual((self.directory / 'manifest.json').read_bytes(), original_manifest)
        self.assert_snapshot(snapshot)
        self.assertFalse(any(t.name.startswith('reader-projection-') for t in threading.enumerate()))

    def test_failed_input_closes_child_and_preserves_previous_publication(self):
        previous = self.build()
        snapshot = self.snapshot(previous)
        original_manifest = (self.directory / 'manifest.json').read_bytes()
        self.records[1]['bad_unknown_value'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'input failed'):
            self.build()
        self.assertEqual((self.directory / 'manifest.json').read_bytes(), original_manifest)
        self.assert_snapshot(snapshot)
        self.assertFalse(any(t.name.startswith('reader-projection-') for t in threading.enumerate()))

    def test_reserved_projection_field_is_rejected_and_pipe_does_not_deadlock(self):
        self.records = [record(i) for i in range(30)]
        for item in self.records:
            item['unknown_payload'] = 'TEST payload ' * 10000
        self.records[0]['_reader'] = {}
        started = time.monotonic()
        with self.assertRaisesRegex(ValueError, 'reserved _reader'):
            self.build()
        self.assertLess(time.monotonic() - started, 10)
        self.assertFalse((self.directory / 'manifest.json').exists())
        self.assertFalse(any(t.name.startswith('reader-projection-') for t in threading.enumerate()))

    def test_both_pipe_directions_drain_with_many_large_records(self):
        self.records = [record(i) for i in range(140)]
        for item in self.records:
            item['text_translation'] = 'TEST searchable ' * 70
            item['unknown_payload'] = 'TEST opaque ' * 1000
        manifest = self.build(max_shard_bytes=4096)
        self.assertEqual(manifest['record_count'], len(self.records))
        self.assertEqual(list(map(json.loads, self.stream(manifest['details']).splitlines())), self.records)
        self.assertFalse(any(t.name.startswith('reader-projection-') for t in threading.enumerate()))

    def test_invalid_child_output_terminates_process_and_drains_large_diagnostics(self):
        child = self.root / 'bad-projector.js'
        child.write_text("process.stderr.write('TEST diagnostic '.repeat(20000));"
                         "process.stdout.write('[]\\n');setInterval(()=>{},1000);")
        actual_popen = subprocess.Popen
        processes = []
        def replacement(args, **kwargs):
            process = actual_popen([shutil.which('node'), str(child)], **kwargs)
            processes.append(process)
            return process
        started = time.monotonic()
        with mock.patch.object(reader.subprocess, 'Popen', side_effect=replacement):
            with self.assertRaisesRegex(ValueError, 'Invalid ordered'):
                self.build()
        self.assertLess(time.monotonic() - started, 10)
        self.assertTrue(processes and all(p.poll() is not None for p in processes))
        self.assertFalse(any(t.name.startswith('reader-projection-') for t in threading.enumerate()))
        self.assertFalse((self.directory / 'manifest.json').exists())

    def test_manifest_commit_failure_preserves_all_prior_bytes(self):
        previous = self.build()
        original_manifest = (self.directory / 'manifest.json').read_bytes()
        snapshot = self.snapshot(previous)
        self.records = [record(17)]
        real_replace = reader.os.replace
        def fail_manifest(source, target):
            if Path(target) == self.directory / 'manifest.json':
                raise OSError('TEST manifest commit failure')
            return real_replace(source, target)
        with mock.patch.object(reader.os, 'replace', side_effect=fail_manifest):
            with self.assertRaisesRegex(OSError, 'manifest commit failure'):
                self.build()
        self.assertEqual((self.directory / 'manifest.json').read_bytes(), original_manifest)
        self.assert_snapshot(snapshot)
        self.assertFalse(list(self.directory.glob('.manifest-*')))

    def test_deferred_publication_keeps_old_html_manifest_and_parts_on_html_failure(self):
        previous = self.build()
        self.output.write_text('TEST original HTML')
        old_manifest = (self.directory / 'manifest.json').read_bytes()
        old_parts = self.snapshot(previous)
        self.records = [record(30)]
        candidate = self.build(publish=False)
        self.assertEqual((self.directory / 'manifest.json').read_bytes(), old_manifest)
        self.assert_snapshot(old_parts)
        real_replace = reader.os.replace
        def fail_html(source, target):
            if Path(target) == self.output:
                raise OSError('TEST HTML replace failure')
            return real_replace(source, target)
        with mock.patch.object(reader.os, 'replace', side_effect=fail_html):
            with self.assertRaisesRegex(OSError, 'HTML replace failure'):
                reader._publish_reader_document(self.output, 'TEST candidate HTML',
                                                self.directory / 'manifest.json', candidate)
        self.assertEqual(self.output.read_text(), 'TEST original HTML')
        self.assertEqual((self.directory / 'manifest.json').read_bytes(), old_manifest)
        self.assert_snapshot(old_parts)
        self.assertFalse(list(self.root.glob('.reader-publish-*')))
        self.assertFalse(list(self.directory.glob('.reader-publish-*')))

    def test_projector_identity_and_exact_byte_locators_are_not_trusted(self):
        actual_popen = subprocess.Popen
        processes = []
        child = self.root / 'wrong-projector.js'
        def replacement(args, **kwargs):
            process = actual_popen([shutil.which('node'), str(child)], **kwargs)
            processes.append(process)
            return process
        entry = {key: self.records[0][key] for key in ('id', 'language', 'book_key', 'edition', 'source_id')}
        entry['_reader'] = {'detail': [0, len(compact(self.records[0]))]}
        for change, message in ((lambda x: x.update(source_id='TEST wrong source'), 'identity mismatch'),
                                (lambda x: x['_reader'].update(detail=[1, 5]), 'byte locator')):
            corrupted = copy.deepcopy(entry)
            change(corrupted)
            child.write_text('process.stdout.write(' + json.dumps(compact([0, corrupted, '', '']).decode()) +
                             ');setInterval(()=>{},1000);')
            with mock.patch.object(reader.subprocess, 'Popen', side_effect=replacement):
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    self.build()
        self.assertTrue(all(process.poll() is not None for process in processes))
        self.assertFalse((self.directory / 'manifest.json').exists())

    def test_migration_prunes_only_prior_checksum_matching_owned_paths(self):
        previous = reader.write_reader_shards(self.records, self.output, self.directory, 1024)
        modified = self.root / previous['shards'][0]['path']
        modified.write_bytes(b'TEST preserve edited file')
        unrelated = self.directory / 'TEST-unrelated.txt'
        unrelated.write_text('TEST unrelated')
        self.records = [record(70)]
        manifest = self.build(max_shard_bytes=4096)
        self.assertEqual(modified.read_bytes(), b'TEST preserve edited file')
        self.assertEqual(unrelated.read_text(), 'TEST unrelated')
        for part in previous['shards'][1:]:
            self.assertFalse((self.root / part['path']).exists())
        generated = reader._reader_manifest_parts(manifest)
        edited_new = self.root / generated[0]['path']
        edited_new.write_bytes(b'TEST preserve second edit')
        self.records = [record(80)]
        current = self.build(max_shard_bytes=4096)
        retained = {p['path'] for p in reader._reader_manifest_parts(current)}
        self.assertEqual(edited_new.read_bytes(), b'TEST preserve second edit')
        for part in generated[1:]:
            if part['path'] not in retained:
                self.assertFalse((self.root / part['path']).exists())

    def test_cleanup_ignores_malformed_and_outside_previous_manifest_entries(self):
        previous = self.build()
        external = self.root / 'TEST-external'
        external.write_bytes(b'TEST external')
        forged = copy.deepcopy(previous)
        forged['search'] = None
        forged['annotations']['shards'] = [None, {}, {'path': []}, {'path': {}}, {'path': '../TEST-external',
            'sha256': hashlib.sha256(external.read_bytes()).hexdigest()}]
        (self.directory / 'manifest.json').write_text(json.dumps(forged))
        self.records = [record(90)]
        current = self.build()
        self.assertEqual(current['record_count'], 1)
        self.assertEqual(json.loads((self.directory / 'manifest.json').read_text()), current)
        self.assertEqual(external.read_bytes(), b'TEST external')

    def test_unhashable_previous_v1_paths_do_not_fail_after_new_publication(self):
        self.directory.mkdir()
        previous = {'schema': 'hadith-bank-reader-shards-v1',
                    'shards': [{'path': []}, {'path': {}}]}
        (self.directory / 'manifest.json').write_text(json.dumps(previous))
        current = self.build()
        self.assertEqual(current['record_count'], len(self.records))
        self.assertEqual(json.loads((self.directory / 'manifest.json').read_text()), current)

    def test_hosted_and_standalone_builds_include_runtime_without_modifying_records(self):
        (self.root / 'catalog').mkdir()
        (self.root / 'search').mkdir()
        raw = b''.join(map(compact, self.records))
        source_raw = b''.join((json.dumps(row, ensure_ascii=False) + '\n').encode('utf-8')
                              for row in self.records)
        self.assertNotEqual(source_raw, raw)
        (self.root / 'search/records.jsonl').write_bytes(source_raw)
        catalog = {'search': {'records_path': 'search/records.jsonl',
                             'records_sha256': hashlib.sha256(source_raw).hexdigest(),
                             'count': len(self.records)}, 'materials': []}
        (self.root / 'catalog/materials.json').write_text(json.dumps(catalog))
        template_path = Path(reader.__file__).resolve().parents[1] / 'reader/template.html'
        if '__HADITH_LAZY_STORE_JS__' not in template_path.read_text():
            self.skipTest('Template lazy runtime integration is not yet present')
        for hosted in (False, True):
            result = reader.build(self.root, self.output, data_directory=self.directory if hosted else None)
            text = self.output.read_text()
            self.assertNotIn('__HADITH_LAZY_STORE_JS__', text)
            self.assertIn('HadithLazyStore', text)
            self.assertEqual(result['embedded_encoding'], 'gzip-jsonl-lazy-v2' if hosted else 'gzip-base64')
            snapshot = json.loads(re.search(r'<script\b[^>]*\bid="hadith-snapshot"[^>]*>(.*?)</script\s*>',
                                            text, re.S).group(1))
            self.assertEqual(snapshot['records_sha256'], hashlib.sha256(source_raw).hexdigest())
            self.assertEqual(result['records_sha256'], snapshot['records_sha256'])
            if hosted:
                manifest = json.loads((self.directory / 'manifest.json').read_text())
                self.assertEqual(snapshot['data_delivery']['jsonl_sha256'], manifest['jsonl_sha256'])
                self.assertEqual(manifest['jsonl_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertNotEqual(snapshot['records_sha256'], manifest['jsonl_sha256'])
                self.assertEqual(self.stream(manifest['details']), raw)
                self.assertEqual(result['max_detail_record_bytes'], max(len(compact(r)) for r in self.records))
                self.assertEqual(result['reader_store_metrics']['details']['uncompressed_bytes'], len(raw))
            else:
                self.assertNotIn('jsonl_sha256', snapshot['data_delivery'])


if __name__ == '__main__':
    unittest.main()

