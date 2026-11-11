from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sync_hadeethenc_counterparts as acquisition


def database(language, ids):
    with closing(sqlite3.connect(':memory:')) as connection:
        if language != 'ar':
            connection.execute('CREATE TABLE hadeeths (id INTEGER, hadeeth TEXT, hadeeth_ar TEXT, ar_version INTEGER)')
            connection.executemany('INSERT INTO hadeeths VALUES (?, ?, ?, ?)',
                                   [(identifier, 'TEST English ' + str(identifier), 'TEST Arabic ' + str(identifier), 1)
                                    for identifier in ids])
        else:
            connection.execute('CREATE TABLE hadeeths (id INTEGER, version INTEGER, hadeeth TEXT)')
            connection.executemany('INSERT INTO hadeeths VALUES (?, ?, ?)',
                                   [(identifier, 1, 'TEST Arabic ' + str(identifier)) for identifier in ids])
        connection.commit()
        return connection.serialize()


class CounterpartSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.snapshot = acquisition.BASE / '2026-11-11'
        english = acquisition.store_bytes(self.root, self.snapshot, 'en.sqlite', database('en', [1]))
        arabic = acquisition.store_bytes(self.root, self.snapshot, 'ar.sqlite', database('ar', [1]))
        self.manifest = {
            'schema': acquisition.SCHEMA, 'english_database': acquisition.descriptor(self.root, english),
            'arabic_database': acquisition.descriptor(self.root, arabic), 'english_version': 'v1.0.0',
            'requested_provider_ids': ['1'], 'requested_id_count': 1, 'downloaded_id_count': 1,
            'missing_provider_ids': [], 'additional_provider_ids': [], 'raw_exports': []}
        acquisition._write_manifest(self.root, self.manifest)

    def test_readers_close_connections_on_success_and_validation_errors(self):
        english = self.root / self.manifest['english_database']['path']
        arabic = self.root / self.manifest['arabic_database']['path']
        original_connect = acquisition._connect
        cases = [
            ('english IDs', lambda: acquisition.english_ids(english), None),
            ('invalid schema', lambda: acquisition.english_ids(arabic), ValueError),
            ('alignment', lambda: acquisition.alignment(self.root, english, arabic), None),
            ('invalid alignment schema',
             lambda: acquisition.alignment(self.root, english, english), sqlite3.OperationalError),
            ('missing second source',
             lambda: acquisition.alignment(self.root, english, self.root / 'missing.sqlite'),
             sqlite3.OperationalError),
        ]
        for label, operation, error in cases:
            with self.subTest(label=label):
                connections = []

                def tracked_connect(path):
                    connection = original_connect(path)
                    connections.append(connection)
                    self.addCleanup(connection.close)
                    return connection

                with patch.object(acquisition, '_connect', side_effect=tracked_connect):
                    if error is None:
                        operation()
                    else:
                        with self.assertRaises(error):
                            operation()
                self.assertTrue(connections)
                for connection in connections:
                    with self.assertRaises(sqlite3.ProgrammingError):
                        connection.execute('SELECT 1')

    def test_complete_cache_never_contacts_provider(self):
        before = (self.root / acquisition.BASE / 'manifest.json').read_bytes()
        with patch.object(acquisition, 'fetch', side_effect=AssertionError('Unexpected network request')):
            result = acquisition.sync(self.root, required_ids={'1'})
        self.assertEqual(result, self.manifest)
        self.assertEqual((self.root / acquisition.BASE / 'manifest.json').read_bytes(), before)

    def test_offline_missing_id_is_recorded_and_existing_text_is_retained(self):
        source = self.root / self.manifest['english_database']['path']
        original = source.read_bytes()
        result = acquisition.sync(self.root, offline=True, required_ids={'1', '2'})
        self.assertEqual(result['missing_provider_ids'], ['2'])
        self.assertEqual(result['requested_id_count'], 2)
        self.assertEqual(source.read_bytes(), original)

    def test_corrupt_cached_source_is_rejected_without_network(self):
        source = self.root / self.manifest['english_database']['path']
        source.write_bytes(source.read_bytes() + b'changed')
        with patch.object(acquisition, 'fetch', side_effect=AssertionError('Unexpected network request')):
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                acquisition.sync(self.root, required_ids={'1'})

    def test_new_snapshot_preserves_previous_raw_bytes_and_manifest(self):
        source = self.root / self.manifest['english_database']['path']
        original = source.read_bytes()
        original_manifest = (self.root / acquisition.BASE / 'manifest.json').read_bytes()

        def fake_fetch(url):
            if url == acquisition.VERSION_URL:
                data = b"There is a new version (v1.2.0) of the translation 'en'"
            else:
                language = 'en' if '/en.sqlite.zip' in url else 'ar'
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w') as archive:
                    archive.writestr(language + '.sqlite', database(language, [1, 2]))
                data = buffer.getvalue()
            return data, {'source_url': url, 'final_url': url, 'http_status': 200,
                          'retrieved_at': '2026-11-11T00:00:00+00:00'}

        with patch.object(acquisition, 'fetch', side_effect=fake_fetch):
            result = acquisition.sync(self.root, required_ids={'1', '2'}, snapshot='2026-11-11')
        self.assertEqual(result['missing_provider_ids'], [])
        self.assertEqual(result['downloaded_id_count'], 2)
        self.assertEqual(result['english_version'], 'v1.2.0')
        self.assertEqual(result['arabic_alignment']['exact_provider_id_version_and_text_match'], 2)
        self.assertEqual(source.read_bytes(), original)
        self.assertNotEqual(result['english_database']['path'], self.manifest['english_database']['path'])
        old_hash = hashlib.sha256(original_manifest).hexdigest()
        self.assertEqual((self.root / acquisition.BASE / 'manifests' / (old_hash + '.json')).read_bytes(), original_manifest)

    def test_unexpected_zip_paths_are_rejected(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('../en.sqlite', b'TEST')
        with self.assertRaisesRegex(ValueError, 'Unexpected files'):
            acquisition._unpack(output.getvalue(), 'en')

    def test_required_ids_come_from_new_registered_material_not_generated_search(self):
        with patch('material_registry.load_public_materials', return_value={
                'groups': [[{'book_key': 'hadeethenc', 'provider_entry_id': '2'}]]}):
            self.assertEqual(acquisition.required_provider_ids(self.root), {'2'})

    def test_auxiliary_evidence_downloads_without_refetching_the_main_snapshot(self):
        requested_urls = []

        def fake_fetch(url):
            requested_urls.append(url)
            if url.endswith('/fa/v1.0.0'):
                data = b"There is a new version (v1.30.0) of the translation 'fa'"
            elif url.endswith('/fa.sqlite.zip'):
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w') as archive:
                    archive.writestr('fa.sqlite', database('fa', [1]))
                data = buffer.getvalue()
            else:
                self.fail('Main snapshot was unexpectedly downloaded: ' + url)
            return data, {'source_url': url, 'final_url': url, 'http_status': 200,
                          'retrieved_at': '2026-11-11T00:00:00+00:00'}

        with patch.object(acquisition, 'fetch', side_effect=fake_fetch):
            result = acquisition.sync(self.root, required_ids={'1'}, auxiliary_languages=['fa'])
        self.assertEqual(len(requested_urls), 2)
        self.assertEqual(result['english_database'], self.manifest['english_database'])
        self.assertEqual(result['auxiliary_translation_databases'][0]['version'], 'v1.30.0')
        with patch.object(acquisition, 'fetch', side_effect=AssertionError('Unexpected network request')):
            cached = acquisition.sync(self.root, required_ids={'1'})
        self.assertEqual(cached, result)

    def test_auxiliary_hashes_are_checked_and_missing_offline_evidence_is_reported(self):
        with self.assertRaisesRegex(ValueError, 'No verified auxiliary translation'):
            acquisition.sync(self.root, required_ids={'1'}, auxiliary_languages=['fa'], offline=True)
        auxiliary = acquisition.store_bytes(self.root, self.snapshot, 'fa.sqlite', database('fa', [1]))
        self.manifest['auxiliary_translation_databases'] = [
            {'language': 'fa', **acquisition.descriptor(self.root, auxiliary)}]
        acquisition._write_manifest(self.root, self.manifest)
        auxiliary.write_bytes(auxiliary.read_bytes() + b'changed')
        with patch.object(acquisition, 'fetch', side_effect=AssertionError('Unexpected network request')):
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                acquisition.sync(self.root, required_ids={'1'})


if __name__ == '__main__':
    unittest.main()
