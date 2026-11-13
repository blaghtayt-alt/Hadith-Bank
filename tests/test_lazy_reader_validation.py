"""Bounded reader validation with synthetic source objects, not quotations."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import validate_bank_views as validator


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n'


class LazyReaderValidationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.path = self.root / 'reader.html'
        self.records = [
            {'id': 'TEST:1', 'language': 'ur', 'book_key': 'TEST', 'edition': 'test-edition',
             'source_id': 'TEST-source', 'text_translation': 'TEST العربية 🌿 漢字 ' * 20,
             'unknown': None, 'source_context': {'held': 'TEST context'}},
            {'id': 'TEST:2', 'language': 'bn', 'book_key': 'TEST', 'edition': 'test-edition',
             'source_id': 'TEST-source', 'text_translation': 'TEST বাংলা',
             'unmodified_extra': [None, False, 7, {'text': 'TEST'}]},
        ]

    def part(self, field, index, raw, **metadata):
        relative = f'data/{field}-{index}.jsonl.gz'
        path = self.root / relative
        path.parent.mkdir(exist_ok=True)
        compressed = gzip.compress(raw, mtime=0)
        path.write_bytes(compressed)
        return {'path': relative, 'sha256': hashlib.sha256(compressed).hexdigest(),
                'bytes': len(compressed), 'uncompressed_bytes': len(raw),
                'count': raw.count(b'\n'), **metadata}

    def row_store(self, field, rows):
        aggregate = b''.join(encoded(row) for row in rows)
        return {'encoding': 'gzip-jsonl-shards', 'record_count': len(rows),
                'jsonl_sha256': hashlib.sha256(aggregate).hexdigest(), 'max_shard_bytes': 4096,
                'shards': [self.part(field, ordinal, encoded(row), first_ordinal=ordinal,
                                     last_ordinal=ordinal) for ordinal, row in enumerate(rows)]}

    def manifest(self):
        raw = b''.join(encoded(record) for record in self.records)
        size = 71
        details = {'schema': 'hadith-bank-reader-shards-v1', 'encoding': 'gzip-jsonl-shards',
                   'record_count': len(self.records), 'jsonl_sha256': hashlib.sha256(raw).hexdigest(),
                   'max_shard_bytes': 4096, 'plain_part_bytes': size,
                   'shards': [self.part('details', i // size, raw[i:i + size])
                              for i in range(0, len(raw), size)]}
        directory, offset = [], 0
        for record in self.records:
            length = len(encoded(record))
            row = {key: record[key] for key in validator.READER_ID_FIELDS}
            row['_reader'] = {'languages': [record['language']], 'origin': 'human',
                              'availability': {'arabic': 'missing', 'english': 'missing'},
                              'ocr_pending': False, 'citation_pairs': [], 'detail': [offset, length]}
            directory.append(row)
            offset += length
        stores = {'directory': self.row_store('directory', directory),
                  'search': self.row_store('search', [[i, 'test source'] for i in range(len(self.records))]),
                  'annotations': self.row_store('annotations', [[i, 'test context'] for i in range(len(self.records))])}
        maxima = {key: max((part['uncompressed_bytes'] for part in store['shards']), default=0)
                  for key, store in stores.items()}
        return {'schema': 'hadith-bank-reader-lazy-v2', 'encoding': 'gzip-jsonl-lazy-v2',
                'record_count': len(self.records), 'jsonl_sha256': details['jsonl_sha256'],
                'max_shard_bytes': 4096, 'details': details, **stores,
                'max_projection_row_bytes': maxima,
                'max_detail_record_bytes': max((len(encoded(record)) for record in self.records), default=0)}

    def read(self, manifest):
        metrics = {}
        records = list(validator.reader_shard_records(self.path, manifest, metrics))
        return records, metrics

    def write_html(self, manifest):
        snapshot = {'record_count': len(self.records), 'records_sha256': 'a' * 64,
                    'data_delivery': {'jsonl_sha256': manifest['jsonl_sha256']}}
        self.path.write_text('<script id="hadith-records" data-encoding="gzip-jsonl-lazy-v2">' +
                             json.dumps(manifest) + '</script><script id="hadith-snapshot">' +
                             json.dumps(snapshot) + '</script>', encoding='utf-8')
        return snapshot

    def test_all_stores_and_exact_detail_objects_are_checked(self):
        manifest = self.manifest()
        records, metrics = self.read(manifest)
        self.assertEqual(records, self.records)
        self.assertEqual(metrics['detail_stream_sha256'], manifest['jsonl_sha256'])
        self.assertEqual(metrics['max_projection_row_bytes'], manifest['max_projection_row_bytes'])
        self.assertEqual(metrics['max_detail_record_bytes'], manifest['max_detail_record_bytes'])
        self.assertEqual(metrics['directory_bytes'], sum(part['uncompressed_bytes'] for part in manifest['directory']['shards']))
        snapshot = self.write_html(manifest)
        projected = [(record['id'], validator.object_hash(record)) for record in self.records]
        report = validator.verify_reader(self.root, 'reader.html', projected, snapshot)
        self.assertEqual(report['embedded_objects_compared'], len(self.records))
        self.assertEqual(report['data_shards_verified'], sum(len(manifest[key]['shards']) for key in ('directory', 'search', 'annotations', 'details')))
        self.assertEqual(report['reader_store_metrics'], metrics['reader_store_metrics'])
        wrong = copy.deepcopy(self.records)
        wrong[0]['unknown'] = 'TEST changed source field'
        projected = [(record['id'], validator.object_hash(record)) for record in wrong]
        with self.assertRaisesRegex(validator.ValidationError, 'differs from source projection'):
            validator.verify_reader(self.root, 'reader.html', projected, snapshot)

    def test_empty_lazy_and_v1_streams_remain_valid(self):
        self.records = []
        manifest = self.manifest()
        records, metrics = self.read(manifest)
        self.assertEqual(records, [])
        self.assertEqual(metrics['directory_bytes'], 0)
        self.assertEqual(self.read(manifest['details'])[0], [])

    def test_v1_details_still_reassemble_records_crossing_utf8_chunks(self):
        manifest = self.manifest()
        broken_utf8_parts = 0
        for part in manifest['details']['shards']:
            try:
                gzip.decompress((self.root / part['path']).read_bytes()).decode('utf-8')
            except UnicodeDecodeError:
                broken_utf8_parts += 1
        self.assertGreater(broken_utf8_parts, 0)
        self.assertEqual(self.read(manifest['details'])[0], self.records)

    def test_search_hash_cannot_substitute_for_the_full_record_hash(self):
        manifest = self.manifest()
        manifest['jsonl_sha256'] = manifest['search']['jsonl_sha256']
        with self.assertRaisesRegex(validator.ValidationError, 'full-detail stream SHA-256'):
            self.read(manifest)
        manifest['details']['jsonl_sha256'] = manifest['jsonl_sha256']
        with self.assertRaisesRegex(validator.ValidationError, 'JSONL stream SHA-256'):
            self.read(manifest)

    def test_snapshot_keeps_canonical_input_and_compact_detail_hashes_distinct(self):
        manifest = self.manifest()
        snapshot = self.write_html(manifest)
        self.assertNotEqual(snapshot['records_sha256'], manifest['jsonl_sha256'])
        projected = [(record['id'], validator.object_hash(record)) for record in self.records]
        validator.verify_reader(self.root, 'reader.html', projected, snapshot)
        # A canonical input stream may use different whitespace, but its hash
        # must never be substituted for the byte-addressed compact detail hash.
        snapshot['data_delivery']['jsonl_sha256'] = snapshot['records_sha256']
        source = self.path.read_text(encoding='utf-8')
        prefix = source.split('<script id="hadith-snapshot">', 1)[0]
        self.path.write_text(prefix + '<script id="hadith-snapshot">' +
                             json.dumps(snapshot) + '</script>', encoding='utf-8')
        with self.assertRaisesRegex(validator.ValidationError, 'delivery snapshot.*full-detail'):
            validator.verify_reader(self.root, 'reader.html', projected, snapshot)

    def test_projection_and_detail_structure_corruption_is_rejected(self):
        mutations = [
            (lambda m: m['search']['shards'][0].update(sha256='0' * 64), 'SHA-256'),
            (lambda m: m['annotations']['shards'][0].update(first_ordinal=1), 'ordinal'),
            (lambda m: m['directory']['shards'][0].update(count=2), 'ordinal'),
            (lambda m: m['search'].update(record_count=True), 'count'),
            (lambda m: m['details'].update(plain_part_bytes=72), 'fixed-part'),
            (lambda m: m['details']['shards'][0].update(path='../escape.gz'), 'path'),
            (lambda m: m['search']['shards'][0].update(path='data/%2e%2e.gz'), 'path'),
            (lambda m: m['max_projection_row_bytes'].update(search=0), 'maximum row'),
            (lambda m: m.update(max_detail_record_bytes=0), 'maximum detail'),
        ]
        for mutation, message in mutations:
            with self.subTest(message=message):
                manifest = self.manifest()
                mutation(manifest)
                with self.assertRaisesRegex(ValueError, message):
                    self.read(manifest)

    def test_rehashed_wrong_directory_locators_and_ids_are_rejected(self):
        mutations = [
            (lambda r: r['_reader']['detail'].__setitem__(0, 1), 'contiguous'),
            (lambda r: r['_reader']['detail'].__setitem__(1, r['_reader']['detail'][1] - 1), 'locator'),
            (lambda r: r.update(id='TEST:different'), 'identity'),
            (lambda r: r['_reader'].update(origin='invented'), 'origin'),
            (lambda r: r['_reader']['availability'].update(arabic='invented'), 'availability'),
            (lambda r: r['_reader'].update(ocr_pending=0), 'OCR'),
            (lambda r: r['_reader'].update(languages=[]), 'languages'),
            (lambda r: r.update(full_text='TEST must not be in directory'), 'row fields'),
        ]
        for mutation, message in mutations:
            with self.subTest(message=message):
                manifest = self.manifest()
                rows = [json.loads(gzip.decompress((self.root / part['path']).read_bytes()))
                        for part in manifest['directory']['shards']]
                mutation(rows[0])
                manifest['directory'] = self.row_store('directory', rows)
                with self.assertRaisesRegex(ValueError, message):
                    self.read(manifest)

    def test_search_rows_require_exact_ordinals_and_string_keys(self):
        for rows in ([[1, 'wrong order'], [0, 'wrong order']], [[0, False], [1, 'test']]):
            manifest = self.manifest()
            manifest['search'] = self.row_store('search', rows)
            with self.assertRaisesRegex(validator.ValidationError, 'search projection row'):
                self.read(manifest)

    def test_utf8_and_decompression_lengths_are_strict(self):
        for raw, message in ((b'[0,"\xff"]\n', None), (b'[0,"longer than declared"]\n', 'uncompressed byte')):
            manifest = self.manifest()
            manifest['search']['shards'][0] = self.part('search', 0, raw, first_ordinal=0, last_ordinal=0)
            if message:
                manifest['search']['shards'][0]['uncompressed_bytes'] = 1
                with self.assertRaisesRegex(ValueError, message):
                    self.read(manifest)
            else:
                with self.assertRaises(UnicodeDecodeError):
                    self.read(manifest)


if __name__ == '__main__':
    unittest.main()
