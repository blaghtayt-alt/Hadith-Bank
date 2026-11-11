"""Discovery regression checks: literal source text, stable routes and crawl graph."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_discovery as discovery


SITE = {'repository_url': 'https://github.com/blaghtayt-alt/Hadith-Bank',
        'live_url': 'https://blaghtayt-alt.github.io/Hadith-Bank/',
        'source_ref': 'a' * 40}


def record(identity='zh-source-1', language='zh-CN', origin='unknown'):
    return {
        'id': identity, 'language': language, 'book_key': 'abu-dawud', 'edition': 'source-2026',
        'source_id': 'fixture-source', 'title': '保留原文 Preserve the original',
        'text_translation': '使者说：原文。\n第二行 & <字>。', 'text_arabic': 'نص عربي محفوظ',
        'number': {'in_book': '1', 'numbering_system': 'chapter_local'},
        'source': {'name': '艾布达吾德圣训 — Sunan Abi Dawud',
                   'original_file': 'materials/fixture/原本.pdf',
                   'record_locator': {'path': 'materials/fixture/records.jsonl', 'line': 1},
                   'url': 'https://example.test/source?a=1&b=2'},
        'translator': {'name': 'Source Translator'}, 'translation_provenance': {'ai_translation': origin},
        'review': {'status': 'pending', 'issues': ['A retained source issue.']},
        'narrator': {'name': 'Named narrator'}, 'page': {'pdf': [5], 'printed': [3]},
        'record_type': 'hadith_occurrence', 'topic_tags': [], 'editorial_tags': [],
        'source_headings': ['第一章'], 'footnotes': [{'text': 'Source footnote'}],
        'commentary': {'translation': 'Separate explanation.'},
    }


class Parsed(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.tags, self.values = [], []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.values.append(data)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.base = Path(self.directory.name)
        self.root = self.base / 'bank'
        self.root.mkdir()
        self.output = self.base / 'site'

    def tearDown(self):
        self.directory.cleanup()

    def fixture(self, records):
        original = self.root / 'materials/fixture/原本.pdf'
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(b'%PDF-1.7\nPreserved source fixture\n')
        digest = hashlib.sha256(original.read_bytes()).hexdigest()
        for item in records:
            item['source']['sha256'] = digest
        stream = b''.join((json.dumps(item, ensure_ascii=False) + '\n').encode('utf-8') for item in records)
        (self.root / 'search').mkdir(exist_ok=True)
        (self.root / 'search/records.jsonl').write_bytes(stream)
        catalog = {'record_count': len(records),
                   'search': {'count': len(records), 'records_path': 'search/records.jsonl',
                              'records_sha256': hashlib.sha256(stream).hexdigest()},
                   'materials': [{'dataset_id': 'fixture-source', 'language': 'zh-CN',
                                  'book_key': 'abu-dawud', 'edition': 'source-2026',
                                  'source_file': 'materials/fixture/原本.pdf', 'source_sha256': digest,
                                  'source_name': '艾布达吾德圣训 — Sunan Abi Dawud'}],
                   'private_materials_not_in_this_tree': [{'language': 'zz', 'book_key': 'private-book', 'count': 99}]}
        (self.root / 'catalog').mkdir(exist_ok=True)
        (self.root / 'catalog/materials.json').write_text(json.dumps(catalog, ensure_ascii=False), encoding='utf-8')
        return catalog

    def build(self, records):
        catalog = self.fixture(records)
        result = discovery.build(self.root, self.output, SITE)
        return catalog, result

    def test_literal_multilingual_text_metadata_and_counterpart_qualification(self):
        chinese = record()
        chinese['number']['printed_labels'] = {'printed_prefix': '5472-3775-(6)'}
        chinese['counterparts'] = {'english': {'scope': 'full_narration',
            'text': 'Exact English counterpart.', 'match_status': 'related_version',
            'source_name': 'Credited publisher', 'source_url': 'https://example.test/en/1',
            'citation': 'Sunan Abi Dawud · 10', 'translation_origin': 'unknown',
            'current_translation_policy': {'classification': 'human'}}}
        persian = record('fa-source-1', 'fa', True)
        persian['text_translation'] = 'متن فارسی\nبدون تغییر'
        persian['record_type'] = 'hadith_excerpt'
        japanese = record('ja-source-1', 'ja', False)
        japanese['text_translation'] = '日本語の引用。\n原文を保存します。'
        japanese['record_type'] = 'companion_report'
        source_before = copy.deepcopy([chinese, persian, japanese])
        _, report = self.build([chinese, persian, japanese])
        for item in (chinese, persian, japanese):
            markup = (self.output / discovery.record_path(item)).read_text()
            parsed = Parsed(markup)
            self.assertIn(item['text_translation'], parsed.values)
            self.assertIn(item['text_arabic'], parsed.values)
            self.assertIn('Source number 1', markup)
            self.assertNotIn('Number in collection 1', markup)
            self.assertIn('Separate explanation.', markup)
            self.assertIn('Source footnote', markup)
            self.assertIn('Source Translator', markup)
            self.assertIn('Occurrence ID:', markup)
            self.assertNotIn('OCR review:', markup)
            self.assertEqual(item['text_translation'], next(source['text_translation'] for source in source_before if source['id'] == item['id']))
        chinese_markup = (self.output / discovery.record_path(chinese)).read_text()
        self.assertIn('Related publisher version', chinese_markup)
        self.assertIn('Exact English counterpart.', chinese_markup)
        self.assertIn('Translation: Unknown', chinese_markup)
        self.assertIn('Translation origin: Human', chinese_markup)
        self.assertIn('5472-3775-(6)', chinese_markup)
        self.assertIn('Source numbering details', chinese_markup)
        persian_markup = (self.output / discovery.record_path(persian)).read_text()
        self.assertIn('lang="fa" dir="rtl"', persian_markup)
        self.assertIn('AI-generated', persian_markup)
        self.assertIn('Hadith excerpt', persian_markup)
        self.assertIn('Companion report', (self.output / discovery.record_path(japanese)).read_text())
        self.assertEqual(report['record_pages'], 3)
        self.assertEqual(report['language_count'], 3)
        self.assertEqual(report['site_bytes'], sum(path.stat().st_size for path in self.output.rglob('*') if path.is_file()))
        self.assertEqual(report['generated_files'], sum(path.is_file() for path in self.output.rglob('*')))
        self.assertTrue(discovery.record_title(chinese).startswith('艾布达吾德圣训'))
        self.assertFalse((self.output / 'browse/zz').exists())

    def test_no_javascript_needed_and_every_crawl_link_resolves(self):
        items = [record('one'), record('two', 'fa')]
        self.build(items)
        for path in self.output.rglob('*.html'):
            parsed = Parsed(path.read_text())
            for tag, attrs in parsed.tags:
                if tag == 'script':
                    self.assertEqual(attrs.get('type'), 'application/ld+json')
                if tag not in ('a', 'link'):
                    continue
                url = attrs.get('href', '')
                if not url or url.startswith('#') or urlsplit(url).scheme:
                    continue
                if url == 'hadith-bank-reader.html' or url.endswith('/hadith-bank-reader.html'):
                    continue  # The parent site builder stages the interactive reader.
                resolved = (path.parent / url).resolve()
                self.assertTrue(resolved.is_relative_to(self.output.resolve()), url)
                self.assertTrue(resolved.is_file() or (resolved / 'index.html').is_file(), (path, url))
            canonical = [attrs['href'] for tag, attrs in parsed.tags if tag == 'link' and attrs.get('rel') == 'canonical']
            self.assertEqual(len(canonical), 1)
            self.assertTrue(canonical[0].startswith(SITE['live_url']))
        sitemap = ET.parse(self.output / 'sitemap.xml').getroot()
        namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locations = []
        for element in sitemap.findall('s:sitemap/s:loc', namespace):
            filename = element.text.removeprefix(SITE['live_url'])
            locations.extend(node.text for node in ET.parse(self.output / filename).getroot().findall('s:url/s:loc', namespace))
        self.assertTrue(all(discovery.canonical_url(discovery.record_path(item), SITE) in locations for item in items))
        self.assertNotIn(SITE['live_url'] + '404.html', locations)
        self.assertFalse((self.output / 'robots.txt').exists())

    def test_source_download_is_real_hashed_and_commit_pinned(self):
        item = record()
        self.build([item])
        markup = (self.output / discovery.record_path(item)).read_text()
        self.assertIn('/raw/' + SITE['source_ref'] + '/materials/fixture/%E5%8E%9F%E6%9C%AC.pdf', markup)
        self.assertIn('Download PDF', markup)
        self.assertIn('/blob/' + SITE['source_ref'] + '/materials/fixture/records.jsonl', markup)
        self.assertFalse((self.root / 'materials/fixture/records.jsonl').exists())
        # A sparse checkout may omit the canonical JSON file while GitHub retains it.
        bad_output = self.base / 'bad-source-site'
        (self.root / 'materials/fixture/原本.pdf').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            discovery.build(self.root, bad_output, SITE)

    def test_script_injection_and_raw_html_stay_literal(self):
        item = record()
        item['text_translation'] = '</script><script>alert("bad")</script><img src=x onerror=bad> & 原文'
        item['title'] = '</title><script>bad()</script>'
        self.build([item])
        markup = (self.output / discovery.record_path(item)).read_text()
        parsed = Parsed(markup)
        self.assertIn(item['text_translation'], parsed.values)
        scripts = [attrs for tag, attrs in parsed.tags if tag == 'script']
        self.assertEqual(scripts, [{'type': 'application/ld+json'}])
        self.assertNotIn('<img src=x', markup)
        payload = markup.split('<script type="application/ld+json">', 1)[1].split('</script>', 1)[0]
        structured = json.loads(payload)
        self.assertEqual(structured['mainEntity']['identifier']['value'], item['id'])
        self.assertNotIn('</script>', payload)

    def test_stable_paths_pagination_and_counts(self):
        one, two, three = record('one'), record('two'), record('three')
        catalog = self.fixture([one, two, three])
        with patch.object(discovery, 'PAGE_SIZE', 2):
            first = discovery.build(self.root, self.output, SITE)
            other = self.base / 'reordered'
            second = discovery.build(self.root, other, SITE, [three, one, two], catalog)
        for item in (one, two, three):
            path = discovery.record_path(item)
            self.assertEqual((self.output / path).read_bytes(), (other / path).read_bytes())
        second_page = self.output / 'browse/zh-CN/abu-dawud/source-2026/page-2.html'
        self.assertTrue(second_page.is_file())
        self.assertEqual(first['record_pages'], second['record_pages'])
        self.assertEqual(first['sitemap_url_count'], first['indexable_pages'] + 1)
        self.assertIn('aria-current="page">2', second_page.read_text())
        first_page = (self.output / 'browse/zh-CN/abu-dawud/source-2026/index.html').read_text()
        self.assertIn(discovery.record_path(one).split('/')[-1], first_page)
        self.assertIn(discovery.record_path(two).split('/')[-1], first_page)
        self.assertNotIn(discovery.record_path(three).split('/')[-1], first_page)

    def test_path_safety_duplicate_ids_and_output_guards(self):
        item = record()
        for field in ('language', 'book_key', 'edition'):
            for value in ('../bad', '/bad', 'bad/x', '.', 'bad\\x'):
                invalid = {**item, field: value}
                with self.assertRaises(ValueError):
                    discovery.record_path(invalid)
        with self.assertRaises(ValueError):
            discovery.repository_file(self.root, '../outside.json', SITE)
        catalog = self.fixture([item])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            discovery.build(self.root, self.output, SITE, [item, item], catalog)
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            discovery.build(self.root, self.root, SITE)
        with self.assertRaisesRegex(ValueError, 'both'):
            discovery.build(self.root, self.output, SITE, [item])
        (self.output / 'browse').mkdir(parents=True, exist_ok=True)
        with self.assertRaisesRegex(ValueError, 'fresh staged'):
            discovery.build(self.root, self.output, SITE)

    def test_sitemap_shards_xml_and_404(self):
        item = record()
        self.build([item])
        separate = self.base / 'sitemaps-only'
        separate.mkdir()
        settings = {**SITE, 'live_url': 'https://example.test/本&bank/'}
        writer = discovery.Writer(self.root, separate, settings)
        report = discovery.write_sitemaps(writer, ['browse/index.html', 'hadith/a.html', 'hadith/b.html'], page_size=2)
        self.assertEqual(report['sitemap_count'], 2)
        self.assertEqual(report['sitemap_url_count'], 4)
        self.assertFalse((separate / 'sitemaps').exists())
        self.assertIn('%E6%9C%AC%26bank', (separate / 'sitemap.xml').read_text())
        for path in separate.rglob('*.xml'):
            ET.parse(path)
            self.assertNotIn('lastmod', path.read_text())
        not_found = Parsed((self.output / '404.html').read_text())
        self.assertIn(('meta', {'name': 'robots', 'content': 'noindex,follow'}), not_found.tags)
        for tag, attrs in not_found.tags:
            if tag in ('a', 'link') and attrs.get('href') and not attrs['href'].startswith('#'):
                self.assertTrue(attrs['href'].startswith('https://'), attrs)

    def test_ocr_badges_current_origin_policy_and_site_size_limit(self):
        item = record()
        item['extraction'] = {'ocr_used': True}
        item['translation_provenance']['current_policy'] = {'classification': 'human'}
        self.build([item])
        markup = (self.output / discovery.record_path(item)).read_text()
        self.assertIn('OCR review: pending', markup)
        self.assertIn('Translation: Human', markup)
        with patch.object(discovery, 'MAX_SITE_BYTES', 100):
            with self.assertRaisesRegex(ValueError, 'size budget'):
                discovery.build(self.root, self.base / 'too-large', SITE)


if __name__ == '__main__':
    unittest.main()
