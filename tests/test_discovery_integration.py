"""Integration checks use synthetic text, never invented religious quotations."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader
import build_discovery
import build_book_catalog
import refresh_bank
from test_reader import fixture


class DiscoveryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'bank'
        (self.root / 'catalog').mkdir(parents=True)
        (self.root / 'search').mkdir()
        self.record = fixture()
        self.record['id'] = 'synthetic 日本語 occurrence 1'
        raw = (json.dumps(self.record, ensure_ascii=False) + '\n').encode()
        (self.root / 'search/records.jsonl').write_bytes(raw)
        self.catalog = {'title': 'Synthetic bank', 'materials': [], 'search': {
            'records_path': 'search/records.jsonl', 'count': 1,
            'records_sha256': hashlib.sha256(raw).hexdigest()}}
        (self.root / 'catalog/materials.json').write_text(json.dumps(self.catalog))

    def test_reader_contains_crawlable_language_links_before_payload(self):
        target = self.root / 'hadith-bank-reader.html'
        build_reader.build(self.root, target, site={'live_url': 'https://example.test/library/'})
        document = target.read_text()
        before_payload = document.split('<script id="hadith-records"', 1)[0]
        self.assertIn('href="https://example.test/library/browse/ja/"', before_payload)
        self.assertIn('rel="canonical" href="https://example.test/library/"', before_payload)
        self.assertIn('日本語', before_payload)
        self.assertNotIn('__HADITH_DISCOVERY_', before_payload)
        self.assertIn('without JavaScript', before_payload)

    @unittest.skipUnless(shutil.which('node'), 'Node is required to verify browser permalink parity')
    def test_browser_permalink_matches_generator_for_unicode_identity(self):
        template = (Path(build_reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helper = 'const recordPageURL =' + template.split('const recordPageURL =', 1)[1].split('const recordFileURL =', 1)[0]
        program = helper + '\n(async()=>{console.log(JSON.stringify([' + \
            'await recordPageURL(' + json.dumps(self.record) + ',{live_url:"https://example.test/library/"}),' + \
            'await recordPageURL(' + json.dumps(dict(self.record, edition='../bad')) + ',{live_url:"https://example.test/library/"})]));})();'
        result = subprocess.run(['node', '-e', program], capture_output=True, text=True, check=True)
        actual, unsafe = json.loads(result.stdout)
        self.assertEqual(actual, 'https://example.test/library/' + build_discovery.record_path(self.record))
        self.assertIsNone(unsafe)

    def test_failed_discovery_build_preserves_deployed_site(self):
        (self.root / 'hadith-bank-reader.html').write_text('SYNTHETIC NEW READER')
        output = self.root / '_site'
        output.mkdir()
        (output / '.hadith-bank-generated-site').write_text('SYNTHETIC MARKER')
        (output / 'index.html').write_text('SYNTHETIC PREVIOUS SITE')
        with patch('refresh_bank.build_discovery', side_effect=ValueError('Synthetic failed validation')):
            with self.assertRaisesRegex(ValueError, 'Synthetic failed validation'):
                refresh_bank.stage_site(self.root, output, {'source_ref': 'main'})
        self.assertEqual((output / 'index.html').read_text(), 'SYNTHETIC PREVIOUS SITE')
        self.assertEqual(list(self.root.glob('.hadith-site-*')), [])

    def test_book_directory_preserves_native_titles_and_real_downloads(self):
        source = self.root / 'materials/synthetic/原本.docx'
        source.parent.mkdir(parents=True)
        source.write_text('SYNTHETIC SOURCE BYTES')
        self.catalog['materials'] = [{'dataset_id': 'synthetic', 'language': 'zh-CN',
            'book_key': 'malik', 'edition': 'source-a', 'count': 1,
            'source_name': '合成資料 — Synthetic source', 'source_file': 'materials/synthetic/原本.docx'}]
        result = build_book_catalog.write_catalog(self.root, self.catalog)
        directory = (self.root / 'catalog/BOOKS.md').read_text()
        self.assertEqual(result['source_editions'], 1)
        self.assertIn('合成資料', directory)
        self.assertIn('/browse/zh-CN/malik/source-a/', directory)
        self.assertIn('Supplied source (Word .docx)', directory)
        self.assertIn('Extracted text | Original source (PDF) | Other source formats', directory)
        self.assertIn('Original PDF unverified — Word source supplied', directory)
        self.assertIn('/raw/main/materials/synthetic/', directory)
        self.assertIn('selected quotations', directory)


if __name__ == '__main__':
    unittest.main()
