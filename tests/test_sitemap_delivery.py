"""Synthetic tests for staged and hosted sitemap integrity. No religious text."""
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_discovery import Writer, write_sitemaps
from verify_sitemap_delivery import verify

SITE = {'live_url': 'https://example.test/Hadith-Bank/',
        'repository_url': 'https://github.com/example/Hadith-Bank',
        'source_ref': 'a' * 40}


class SitemapDeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.site = self.root / '_site'
        self.site.mkdir()
        writer = Writer(self.root, self.site, SITE)
        writer.write('index.html', '<!doctype html><title>TEST HOME</title>')
        writer.write('browse/index.html', '<!doctype html><title>TEST BROWSE</title>')
        writer.write('hadith/example.html', '<!doctype html><title>TEST SOURCE</title>')
        sitemap = write_sitemaps(writer, ['browse/index.html', 'hadith/example.html'], page_size=2)
        self.info = {
            'status': 'passed', 'source_commit': 'a' * 40,
            'discovery': {'source_records_sha256': 'b' * 64, **sitemap}}
        (self.site / 'build-info.json').write_text(json.dumps(self.info))

    def test_entire_inventory_hash_and_staged_html_resolve(self):
        r = verify(site_root=self.site, expected_source_commit='a' * 40)
        self.assertEqual(r['status'], 'passed')
        self.assertEqual(r['canonical_url_count'], 3)
        self.assertEqual(len(r['child_sitemaps']), 2)
        self.assertEqual(r['source_records_sha256'], 'b' * 64)
        self.assertEqual(r['lossless_sitemap_bytes_saved'],
                         self.info['discovery']['sitemap_lossless_bytes_saved'])
        self.assertFalse((self.site / 'sitemap-0001.xml').exists())

    def test_hosted_bytes_match_staged_bytes_and_source_revision(self):
        def fetcher(url):
            path = url.removeprefix(SITE['live_url'])
            self.assertTrue(url.startswith(SITE['live_url']))
            return (self.site / path).read_bytes(), {'content_type': 'application/gzip'}
        r = verify(production_url=SITE['live_url'], expected_source_commit='a' * 40,
                   fetcher=fetcher)
        self.assertEqual(r['mode'], 'live')
        self.assertEqual(r['canonical_url_count'], 3)
        self.assertEqual(len(r['http_response_headers']), 4)

    def test_mismatched_source_revision_or_xml_hash_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'source revision differs'):
            verify(site_root=self.site, expected_source_commit='c' * 40)
        self.info['discovery']['sitemap_original_xml_sha256'][0] = 'f' * 64
        (self.site / 'build-info.json').write_text(json.dumps(self.info))
        with self.assertRaisesRegex(ValueError, 'build-verified XML'):
            verify(site_root=self.site)

    def test_broken_gzip_and_missing_html_are_rejected(self):
        child = self.site / 'sitemap-0001.xml.gz'
        original = child.read_bytes()
        child.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, 'invalid gzip|build-verified XML'):
            verify(site_root=self.site)
        child.write_bytes(original)
        (self.site / 'hadith/example.html').unlink()
        with self.assertRaisesRegex(ValueError, 'does not resolve'):
            verify(site_root=self.site)

    def test_external_child_location_is_not_accepted(self):
        path = self.site / 'sitemap.xml'
        index = ET.parse(path).getroot()
        tag = '{http://www.sitemaps.org/schemas/sitemap/0.9}loc'
        index.find('.//' + tag).text = 'https://example.test/other/sitemap.xml.gz'
        path.write_bytes(ET.tostring(index, encoding='utf-8'))
        with self.assertRaisesRegex(ValueError, 'outside its canonical HTTPS project root'):
            verify(site_root=self.site)

    def test_gzip_output_is_real_xml_not_html_fallback(self):
        raw = (self.site / 'sitemap-0001.xml.gz').read_bytes()
        self.assertEqual(raw[:2], b'\x1f\x8b')
        self.assertEqual(ET.fromstring(gzip.decompress(raw)).tag,
                         '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')


if __name__ == '__main__':
    unittest.main()
