"""Portable generated-page provenance, identity, and fail-closed regressions."""
import copy
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_discovery as discovery

SITE = {'repository_url': 'https://github.com/example/bank',
        'live_url': 'https://example.test/bank/', 'source_ref': 'a' * 40}
PANEL = re.compile(r'<details><summary>Source translation-origin history</summary>.*?</details>', re.S)

def history():
    return {'origin': 'unknown', 'ai_translation': 'unknown',
            'current_policy': {'classification': 'human'},
            'typed': [None, False, 0, '0', True, 1.5],
            'evidence': 'Exact retained source history. ' * 300,
            'hostile_literal': '</pre><img src=x onerror=alert(1)>'}

def record(identity, provenance, source='edition-one'):
    return {'id': identity, 'language': 'hi', 'book_key': 'bukhari',
            'edition': source, 'source_id': source, 'title': 'Exact source',
            'text_translation': 'Original quotation & <letters>.\nSecond source line.',
            'text_arabic': None, 'number': {'in_book': None, 'canonical': None},
            'page': {'pdf': [3]}, 'source': {'name': source, 'url': None},
            'translator': {'name': 'Named source translator'},
            'translation_provenance': copy.deepcopy(provenance),
            'review': {'status': 'pending', 'issues': ['Retained source qualification']},
            'record_type': 'hadith_occurrence', 'footnotes': [], 'commentary': {}}

class Inspection(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.tags = []; self.links = []; self.value = ''; self.inside = False
        self.feed(value)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs); self.tags.append((tag, attrs))
        if tag in ('a', 'link') and 'href' in attrs: self.links.append((tag, attrs))
        if tag == 'pre' and attrs.get('id') == 'exact-translation-provenance': self.inside = True
    def handle_endtag(self, tag):
        if tag == 'pre': self.inside = False
    def handle_data(self, value):
        if self.inside: self.value += value

class SharedProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def writer(self, name):
        return discovery.Writer(self.root, self.root / name, SITE)
    def render(self, writer, records, sharing=True):
        if sharing: discovery.plan_shared_translation_provenance(writer, records)
        for item in records: discovery.render_record(writer, item, {}, {})
        return discovery.finalize_shared_translation_provenance(writer)

    def test_exact_typed_metadata_and_hostile_text_are_inert(self):
        value = history(); digest, encoded = discovery.translation_provenance_identity(value)
        writer = self.writer('metadata'); discovery.shared_translation_provenance_page(writer, digest, value)
        parsed = Inspection((self.root / 'metadata' / discovery.shared_translation_provenance_path(digest)).read_text(encoding='utf-8'))
        self.assertEqual(json.dumps(json.loads(parsed.value), ensure_ascii=False, separators=(',', ':')), encoded)
        self.assertFalse(any(tag == 'img' for tag, attrs in parsed.tags))
        self.assertNotEqual(discovery.translation_provenance_identity({'x': False})[0], discovery.translation_provenance_identity({'x': 0})[0])
        self.assertNotEqual(discovery.translation_provenance_identity({'x': None})[0], discovery.translation_provenance_identity({'x': 'null'})[0])
        self.assertEqual(value, history())

    def test_only_history_panel_changes_and_actual_assets_save_bytes(self):
        rows = [record('source-one', history()), record('source-two', history())]
        old = self.writer('inline'); self.render(old, rows, sharing=False)
        new = self.writer('shared'); report = self.render(new, rows)
        self.assertEqual(report['shared_metadata_pages'], 1); self.assertLess(new.bytes, old.bytes)
        self.assertEqual(len(new.pages), 2)
        for item in rows:
            path = discovery.record_path(item)
            before = (self.root / 'inline' / path).read_text(encoding='utf-8')
            after = (self.root / 'shared' / path).read_text(encoding='utf-8')
            self.assertEqual(PANEL.sub('<HISTORY>', before), PANEL.sub('<HISTORY>', after))
            self.assertIn(html.escape(item['text_translation'], quote=False), after)

    def test_distinct_source_occurrence_and_edition_identities_remain(self):
        rows = [record('source-one', history(), 'edition-one'), record('source-two', history(), 'edition-two')]
        writer = self.writer('identities'); self.render(writer, rows)
        paths = {discovery.record_path(item) for item in rows}; self.assertEqual(len(paths), 2)
        self.assertEqual(len(writer.pages), 2)
        for item in rows:
            output = (self.root / 'identities' / discovery.record_path(item)).read_text(encoding='utf-8')
            self.assertIn(item['id'], output); self.assertIn(item['edition'], output)

    def test_singleton_and_too_small_values_keep_exact_inline_output(self):
        rows = [record('single', history()), record('small-one', {'x': 'y'}), record('small-two', {'x': 'y'})]
        old = self.writer('old'); self.render(old, rows, sharing=False)
        new = self.writer('new'); report = self.render(new, rows)
        self.assertEqual(report['shared_metadata_pages'], 0)
        self.assertEqual(old.bytes, new.bytes)
        self.assertFalse((self.root / 'new' / 'source-metadata').exists())
        for item in rows:
            path = discovery.record_path(item)
            self.assertEqual((self.root / 'old' / path).read_bytes(), (self.root / 'new' / path).read_bytes())

    def test_invalid_paths_and_forced_hash_collisions_fail_closed(self):
        for digest in (None, '../escape', 'A' * 64, '0' * 63, '0' * 64 + '/x'):
            with self.subTest(digest=digest), self.assertRaises(ValueError): discovery.shared_translation_provenance_path(digest)
        rows = [record('one', {'value': 'one'}), record('two', {'value': 'two'})]
        with patch.object(discovery.hashlib, 'sha256', return_value=SimpleNamespace(hexdigest=lambda: '0' * 64)):
            with self.assertRaisesRegex(ValueError, 'collision'): discovery.plan_shared_translation_provenance(self.writer('collision'), rows)

    def test_changed_value_after_planning_rejects_incomplete_sharing(self):
        rows = [record('one', history()), record('two', history())]; writer = self.writer('mutated')
        discovery.plan_shared_translation_provenance(writer, rows)
        rows[0]['translation_provenance']['evidence'] += 'changed'
        for item in rows: discovery.render_record(writer, item, {}, {})
        with self.assertRaises(ValueError): discovery.finalize_shared_translation_provenance(writer)

    def test_noindex_metadata_uses_local_links_and_404_keeps_absolute_links(self):
        writer = self.writer('links'); value = history(); digest = discovery.translation_provenance_identity(value)[0]
        discovery.shared_translation_provenance_page(writer, digest, value)
        page = Inspection((self.root / 'links' / discovery.shared_translation_provenance_path(digest)).read_text(encoding='utf-8'))
        self.assertTrue(any(tag == 'meta' and attrs.get('name') == 'robots' and 'noindex' in attrs.get('content', '') for tag, attrs in page.tags))
        self.assertTrue(any(tag == 'link' and attrs.get('rel') == 'stylesheet' and attrs['href'].startswith('../../') for tag, attrs in page.links))
        writer.page('404.html', 'Not found', 'Missing URL', '<h1>Not found</h1>', indexable=False)
        missing = Inspection((self.root / 'links/404.html').read_text(encoding='utf-8'))
        self.assertTrue(any(tag == 'link' and attrs.get('rel') == 'stylesheet' and attrs['href'].startswith(SITE['live_url']) for tag, attrs in missing.links))
        self.assertEqual(writer.pages, [])

    def test_shared_web_reader_occurrences_do_not_create_new_metadata_pages(self):
        rows = [record('one', history(), 'fawaz-fixture'), record('two', history(), 'fawaz-fixture')]
        for item in rows: item['language_versions'] = [{'language': 'hi', 'text': item['text_translation']}]
        self.assertTrue(all(discovery.uses_shared_web_reader(item) for item in rows))
        writer = self.writer('web'); self.assertEqual(discovery.plan_shared_translation_provenance(writer, rows), {})
        self.assertEqual(discovery.finalize_shared_translation_provenance(writer)['shared_metadata_pages'], 0)

if __name__ == '__main__': unittest.main()
