"""Reuse gates for a fully validated sharded reader; quotations are synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader
import refresh_bank
from test_reader import fixture


@unittest.skipUnless(shutil.which('node'), 'Node is required for real lazy reader fixtures')
class RefreshReaderReuseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'bank'
        (self.root / 'catalog').mkdir(parents=True)
        (self.root / 'search').mkdir()
        self.record = fixture()
        raw = (json.dumps(self.record, ensure_ascii=False) + '\n').encode()
        self.catalog = {'title': 'TEST source bank', 'record_count': 1, 'by_language': {'ja': 1},
                        'materials': [], 'search': {'records_path': 'search/records.jsonl', 'count': 1,
                                                   'records_sha256': hashlib.sha256(raw).hexdigest()}}
        (self.root / 'catalog/materials.json').write_text(json.dumps(self.catalog))
        (self.root / 'search/records.jsonl').write_bytes(raw)
        self.site = {'source_ref': 'main', 'build_commit': 'a' * 40}
        self.reader = self.root / 'hadith-bank-reader.html'
        self.result = build_reader.build(self.root, self.reader, site=self.site,
                                         data_directory=self.root / 'hadith-bank-reader-data')
        self.info = self.build_info(self.result)

    def build_info(self, result):
        raw = self.reader.read_bytes()
        return {'status': 'passed', 'source_ref': 'main', 'source_commit': 'a' * 40,
                'record_count': 1, 'search_sha256': self.catalog['search']['records_sha256'],
                'reader_sha256': hashlib.sha256(raw).hexdigest(), 'reader_bytes': len(raw),
                'reader_self_contained': result['self_contained'],
                'reader_transport': refresh_bank.reader_build_metrics(result)}

    def prior_site(self):
        output = self.root / '_site'
        output.mkdir(exist_ok=True)
        (output / '.hadith-bank-generated-site').write_text('TEST generated marker')
        (output / 'index.html').write_bytes(b'TEST previous deployed reader')
        return output

    def stage(self, info=None):
        with patch('refresh_bank.build_discovery', return_value={'pages': 1}):
            return refresh_bank.stage_site(self.root, '_site', self.info if info is None else info)

    def replace_script(self, identifier, value):
        document = self.reader.read_text()
        pattern = r'(<script\b[^>]*\bid="' + identifier + r'"[^>]*>).*?(</script\s*>)'
        document, count = re.subn(pattern, lambda match: match[1] + build_reader.script_json(value) + match[2], document, flags=re.S)
        self.assertEqual(count, 1)
        self.reader.write_text(document)
        raw = self.reader.read_bytes()
        self.info.update(reader_bytes=len(raw), reader_sha256=hashlib.sha256(raw).hexdigest())
        self.info['reader_transport']['html_bytes'] = len(raw)

    def test_sharded_reader_reuses_exact_html_and_every_copied_data_byte(self):
        data = self.root / 'hadith-bank-reader-data'
        (data / 'TEST-preserved-extra.txt').write_bytes(b'TEST unchanged existing data file\x00\xff')
        before = {path.relative_to(data): path.read_bytes() for path in data.rglob('*') if path.is_file()}
        original = self.reader.read_bytes()
        with patch('refresh_bank.build_reader', side_effect=AssertionError('A validated sharded reader must not rebuild')):
            output = self.stage()
        self.assertEqual((output / 'index.html').read_bytes(), original)
        self.assertEqual((output / 'hadith-bank-reader.html').read_bytes(), original)
        self.assertEqual({path.relative_to(output / data.name): path.read_bytes()
                          for path in (output / data.name).rglob('*') if path.is_file()}, before)
        self.assertEqual(self.info['hosted_reader'], self.info['reader_transport'])
        self.assertIsNot(self.info['hosted_reader'], self.info['reader_transport'])
        self.assertFalse((output / 'reader-data').exists())
        self.assertEqual(json.loads((output / 'build-info.json').read_text())['hosted_reader'], self.info['reader_transport'])

    def test_source_hash_count_and_site_binding_fail_without_replacing_existing_site(self):
        output = self.prior_site()
        for key, value in (('search_sha256', 'f' * 64), ('record_count', 2), ('source_ref', 'another-ref'), ('status', 'failed')):
            with self.subTest(key=key):
                info = copy.deepcopy(self.info); info[key] = value
                with patch('refresh_bank.build_reader', side_effect=AssertionError('Do not rebuild around a failed reuse gate')):
                    with self.assertRaisesRegex(ValueError, 'Cannot reuse validated reader'):
                        self.stage(info)
                self.assertEqual((output / 'index.html').read_bytes(), b'TEST previous deployed reader')
                self.assertEqual(list(self.root.glob('.hadith-site-*')), [])

    def test_reader_html_change_after_validation_is_rejected(self):
        self.reader.write_bytes(self.reader.read_bytes() + b'\nTEST changed after validation')
        with self.assertRaisesRegex(ValueError, 'HTML bytes differ'):
            self.stage()
        self.assertFalse((self.root / '_site').exists())

    def test_current_catalog_change_rejects_stale_snapshot(self):
        catalog = copy.deepcopy(self.catalog)
        catalog['search']['records_sha256'] = 'e' * 64
        (self.root / 'catalog/materials.json').write_text(json.dumps(catalog))
        with self.assertRaisesRegex(ValueError, 'source snapshot hash'):
            self.stage()

    def test_disk_manifest_change_is_rejected_before_copy(self):
        path = self.root / 'hadith-bank-reader-data/manifest.json'
        manifest = json.loads(path.read_text()); manifest['jsonl_sha256'] = 'd' * 64
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'data manifest differs'):
            self.stage()

    def test_wrong_relative_data_prefix_is_rejected_even_with_rebound_html(self):
        path = self.root / 'hadith-bank-reader-data/manifest.json'
        manifest = json.loads(path.read_text())
        manifest['details']['shards'][0]['path'] = 'other-data/details/TEST.jsonl.gz'
        path.write_text(json.dumps(manifest))
        self.replace_script('hadith-records', manifest)
        with self.assertRaisesRegex(ValueError, 'unsafe, duplicate or incomplete data descriptor'):
            self.stage()

    def test_copied_data_hash_is_checked_after_source_validation(self):
        output = self.prior_site()
        manifest = json.loads((self.root / 'hadith-bank-reader-data/manifest.json').read_text())
        path = self.root / manifest['details']['shards'][0]['path']
        data = path.read_bytes(); path.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, 'copied data SHA-256 differs'):
            self.stage()
        self.assertEqual((output / 'index.html').read_bytes(), b'TEST previous deployed reader')

    def test_unreferenced_symlink_is_not_followed_into_staged_site(self):
        (self.root / 'hadith-bank-reader-data/unexpected-link').symlink_to(self.root / 'search')
        with self.assertRaisesRegex(ValueError, 'copied data contains a symlink'):
            self.stage()
        self.assertFalse((self.root / '_site').exists())

    def test_standalone_branch_still_builds_a_hosted_reader_and_keeps_download(self):
        result = build_reader.build(self.root, self.reader, site=self.site)
        self.assertTrue(result['self_contained'])
        original = self.reader.read_bytes()
        info = self.build_info(result)
        with patch('refresh_bank.build_reader', wraps=build_reader.build) as builder:
            output = self.stage(info)
        builder.assert_called_once()
        self.assertEqual(builder.call_args.kwargs['data_directory'].name, 'reader-data')
        self.assertTrue(builder.call_args.kwargs['site']['offline_reader_url'].endswith('/hadith-bank-reader.html'))
        self.assertEqual((output / 'hadith-bank-reader.html').read_bytes(), original)
        self.assertNotEqual((output / 'index.html').read_bytes(), original)
        self.assertTrue((output / 'reader-data/manifest.json').is_file())
        self.assertFalse(info['hosted_reader']['self_contained'])

    def test_full_source_validation_failure_still_prevents_staging(self):
        with patch('refresh_bank.build_views', return_value={}), \
                patch('refresh_bank.build_reader', return_value=self.result), \
                patch('refresh_bank.write_book_catalog'), \
                patch('refresh_bank.load_records', return_value=([self.record], self.catalog, {})), \
                patch('refresh_bank.prepare_review', return_value={}), \
                patch('refresh_bank.validate', side_effect=ValueError('TEST full source validation failed')), \
                patch('refresh_bank.stage_site') as stage:
            with self.assertRaisesRegex(ValueError, 'full source validation failed'):
                refresh_bank.refresh(self.root)
        stage.assert_not_called()


if __name__ == '__main__':
    unittest.main()
