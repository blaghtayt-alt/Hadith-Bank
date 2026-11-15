"""Discovery regression checks: literal source text, stable routes and crawl graph."""
import copy
import gzip
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_discovery as discovery
import refresh_bank as refresh


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
    def test_compact_metadata_retains_exact_values_without_creating_markup(self):
        value = {'source': 'TEST "quoted" and apostrophe\'s text',
                 'text': 'TEST </pre><script>unsafe()</script> & العربية 日本語\nline two',
                 'source_id': 'TEST:1', 'nested': [None, True, {'path': 'TEST\\source'}]}
        original = copy.deepcopy(value)
        markup = discovery.data_details('TEST source metadata', value)
        parsed = Parsed(markup)
        self.assertNotIn('script', [tag for tag, _attrs in parsed.tags])
        self.assertEqual(json.loads(parsed.values[-1]), original)
        self.assertEqual(value, original)
        legacy = discovery.esc(json.dumps(value, ensure_ascii=False, indent=2))
        self.assertLess(len(discovery.metadata_json(value).encode()), len(legacy.encode()))

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
            raw = (self.output / filename).read_bytes()
            self.assertTrue(filename.endswith('.xml.gz'))
            decoded = gzip.decompress(raw)
            locations.extend(node.text for node in ET.fromstring(decoded).findall('s:url/s:loc', namespace))
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

    def test_compact_static_markup_keeps_dom_and_literal_source_wording(self):
        original = ('<details class="language-reading" lang="ar" dir="rtl">'
                    '<summary>Source "report" &#x27;one&#x27;</summary>'
                    '<div class="text quotation">TEST "quoted" &#x27;quoted&#x27; '
                    '&amp; &lt;unsafe&gt; class="not-a-tag"</div>'
                    '<a href="https://example.test/?a=1&amp;b=2" target="_blank">'
                    'Original link</a></details>')
        smaller = discovery.compact_static_record_markup(original)
        a, b = Parsed(original), Parsed(smaller)
        self.assertEqual(a.tags, b.tags)
        self.assertEqual(a.values, b.values)
        self.assertLess(len(smaller.encode('utf-8')), len(original.encode('utf-8')))
        self.assertIn('href="https://example.test/?a=1&amp;b=2"', smaller)
        self.assertIn('&lt;unsafe&gt;', smaller)
        self.assertIn('class="not-a-tag"', smaller)
        source = record()
        source['text_translation'] = "TEST quoted: \"double\" and 'single' <script>inert()</script>"
        self.build([source])
        page = Parsed((self.output / discovery.record_path(source)).read_text())
        self.assertIn(source['text_translation'], page.values)
        self.assertEqual([tag for tag, _ in page.tags if tag == 'script'], ['script'])

    def test_quote_aware_tag_parser_preserves_raw_attribute_values(self):
        html = ('<a title="x > &quot; y" class="badge" '
                'href="https://example.test/?q=a&gt;b&amp;v=1" target="_blank">'
                'Quoted "source" &#x27;attribution&#x27;</a>')
        compact = discovery.compact_static_record_markup(html)
        self.assertEqual(discovery._markup_events(html), discovery._markup_events(compact))
        self.assertIn('title="x > &quot; y"', compact)
        self.assertIn('href="https://example.test/?q=a&gt;b&amp;v=1"', compact)
        self.assertLess(len(compact.encode('utf-8')), len(html.encode('utf-8')))
        for unsupported in ('<script>let x = "< > &quot;";</script>',
                            '<div class="badge"><!-- unsupported -->Test</div>'):
            self.assertEqual(discovery.compact_static_record_markup(unsupported), unsupported)

    def test_optional_source_definitions_are_same_semantic_dom_and_values(self):
        original = ('<section class="panel"><dl>'
                    '<dt>Source language</dt><dd dir="auto">العربية &amp; 中文</dd>'
                    '<dt>Publisher</dt><dd dir="auto"><a href="https://example.test/?a=1&amp;b=2">TEST author</a></dd>'
                    '<dt>Qualifier</dt><dd dir="auto"><bdi>Human</bdi> and Unknown are distinct</dd>'
                    '</dl></section>')
        candidate = discovery.compact_source_definition_end_tags(original)
        self.assertLess(len(candidate.encode('utf-8')), len(original.encode('utf-8')))
        self.assertEqual(discovery._definition_list_dom_events(
            original[original.index('<dl>'):original.index('</dl>') + 5]),
            discovery._definition_list_dom_events(
            candidate[candidate.index('<dl>'):candidate.index('</dl>') + 5]))
        self.assertIn('العربية &amp; 中文', candidate)
        self.assertIn('href="https://example.test/?a=1&amp;b=2"', candidate)
        self.assertIn('dir="auto"', candidate)
        self.assertIn('Human</bdi> and Unknown', candidate)
        # Noncanonical arbitrary markup is conservatively left intact.
        unexpected = '<dl><dt>TEST</dt><dd class="unexpected">No change</dd></dl>'
        self.assertEqual(discovery.compact_source_definition_end_tags(unexpected), unexpected)

    def test_full_static_record_source_definitions_no_javascript_or_text_loss(self):
        item = record()
        original = copy.deepcopy(item)
        self.build([item])
        page = (self.output / discovery.record_path(item)).read_text()
        parsed = Parsed(page)
        self.assertIn(item['text_translation'], parsed.values)
        self.assertIn(item['text_arabic'], parsed.values)
        self.assertEqual(item['text_translation'], original['text_translation'])
        self.assertIn('Source and translation', page)
        self.assertIn('Source Translator', page)
        self.assertIn('Occurrence ID:', page)
        self.assertGreater(page.count('<dt>'), 4)
        self.assertNotIn('</dt><dd dir="auto">', page)
        self.assertEqual([tag for tag, _ in parsed.tags if tag == 'script'], ['script'])

    def test_diagnostic_paths_reject_traversal_absolute_stage_and_symlink(self):
        site = self.root / 'staged-site'
        site.mkdir()
        outside = self.base / 'outside'
        outside.mkdir()
        (self.root / 'link-to-outside').symlink_to(outside, target_is_directory=True)
        for unsafe in ('../outside.json', '/tmp/outside.json', 'staged-site/report.json',
                       'link-to-outside/report.json'):
            with self.subTest(destination=unsafe), patch.dict(os.environ, {'HADITH_SITE_SIZE_REPORT': unsafe}):
                with self.assertRaisesRegex(ValueError, 'inventory|symlink'):
                    discovery.write_site_size_inventory(self.root, site, {
                        'source_records_sha256': 'a' * 64, 'site_bytes': 0,
                    })
        self.assertFalse((outside / 'report.json').exists())
        self.assertFalse((site / 'report.json').exists())

    def test_complete_final_site_inventory_and_budget_enforcement(self):
        _, discovery_report = self.build([record()])
        (self.output / '.hadith-bank-generated-site').write_text('Test marker')
        (self.output / 'build-info.json').write_text('{"source_commit":"test"}')
        final = '.work/site-size-final.json'
        with patch.dict(os.environ, {'HADITH_SITE_FINAL_SIZE_REPORT': final}):
            report = refresh.verify_final_site_size(self.root, self.output, {
                'source_commit': 'a' * 40, 'discovery': discovery_report,
            })
        evidence = json.loads((self.root / final).read_text())
        actual_bytes = sum(path.stat().st_size for path in self.output.rglob('*') if path.is_file())
        self.assertEqual(report['final_site_bytes'], actual_bytes)
        self.assertEqual(evidence['final_site_bytes'], actual_bytes)
        self.assertEqual(report['site_budget_bytes'], 950_000_000)
        self.assertEqual(report['final_headroom_bytes'], 950_000_000 - actual_bytes)
        self.assertIn('build-info.json', [item['path'] for item in report['files']])
        self.assertIn('discovery-info.json', [item['path'] for item in report['files']])
        for item in report['files']:
            self.assertEqual(item['sha256'],
                             hashlib.sha256((self.output / item['path']).read_bytes()).hexdigest())
        with patch.object(refresh, 'MAX_SITE_BYTES', actual_bytes):
            with self.assertRaisesRegex(ValueError, 'Final published site exceeds'):
                refresh.verify_final_site_size(self.root, self.output, {
                    'source_commit': 'a' * 40, 'discovery': discovery_report,
                })

    def test_site_size_inventory_is_complete_and_outside_site(self):
        destination = '.work/site-size-histogram.json'
        with patch.dict(os.environ, {'HADITH_SITE_SIZE_REPORT': destination}):
            _, report = self.build([record()])
        path = self.root / destination
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(snapshot['schema'], 'hadith-bank-prepublication-site-file-inventory-v1')
        self.assertEqual(snapshot['site_budget_bytes'], discovery.MAX_SITE_BYTES)
        self.assertEqual(snapshot['projected_site_bytes_including_discovery_info'], report['site_bytes'])
        self.assertEqual(snapshot['measured_site_bytes'], sum(item['bytes'] for item in snapshot['files']))
        self.assertEqual(snapshot['file_count'], len(snapshot['files']))
        for item in snapshot['files']:
            self.assertEqual(hashlib.sha256((self.output / item['path']).read_bytes()).hexdigest(),
                             item['sha256'])
        self.assertFalse((self.output / destination).exists())
        self.assertTrue((self.output / 'discovery-info.json').exists())

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
        for path in separate.rglob('*.xml.gz'):
            decoded = gzip.decompress(path.read_bytes())
            ET.fromstring(decoded)
            self.assertNotIn('lastmod', decoded.decode('utf-8'))
            self.assertEqual(gzip.compress(decoded, compresslevel=9, mtime=0), path.read_bytes())
        self.assertEqual(len(list(separate.glob('sitemap-*.xml.gz'))), 2)
        self.assertEqual(report['sitemap_uncompressed_bytes'] - report['sitemap_stored_bytes'],
                         report['sitemap_lossless_bytes_saved'])
        not_found = Parsed((self.output / '404.html').read_text())
        self.assertIn(('meta', {'name': 'robots', 'content': 'noindex,follow'}), not_found.tags)
        for tag, attrs in not_found.tags:
            if tag in ('a', 'link') and attrs.get('href') and not attrs['href'].startswith('#'):
                self.assertTrue(attrs['href'].startswith('https://'), attrs)

    def test_lossless_sitemap_byte_identity_unchanged_urls_and_hashes(self):
        records = [record('TEST-1'), record('TEST-2', 'fa'), record('TEST-3', 'ja')]
        _, report = self.build(records)
        root = ET.parse(self.output / 'sitemap.xml').getroot()
        namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        paths = [node.text.removeprefix(SITE['live_url']) for node in
                 root.findall('s:sitemap/s:loc', namespace)]
        self.assertEqual(len(paths), report['sitemap_count'])
        self.assertTrue(all(path.endswith('.xml.gz') for path in paths))
        uncompressed = 0
        stored = 0
        urls = set()
        for index, relative in enumerate(paths):
            compressed = (self.output / relative).read_bytes()
            xml = gzip.decompress(compressed)
            self.assertEqual(hashlib.sha256(xml).hexdigest(),
                             report['sitemap_original_xml_sha256'][index])
            self.assertEqual(gzip.compress(xml, compresslevel=9, mtime=0), compressed)
            uncompressed += len(xml)
            stored += len(compressed)
            urls.update(item.text for item in ET.fromstring(xml).findall('s:url/s:loc', namespace))
        self.assertEqual(uncompressed, report['sitemap_uncompressed_bytes'])
        self.assertEqual(stored, report['sitemap_stored_bytes'])
        self.assertEqual(len(urls), report['sitemap_url_count'])
        for record_ in records:
            self.assertIn(discovery.canonical_url(discovery.record_path(record_), SITE), urls)
        self.assertIn(SITE['live_url'], urls)

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
