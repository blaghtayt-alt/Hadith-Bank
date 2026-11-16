"""Generated metadata regression: exact source DOM and occurrence identity."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_discovery as discovery

SITE = {'live_url': 'https://example.test/project/',
        'repository_url': 'https://github.com/example/project', 'source_ref': 'a' * 40}


def graph(canonical):
    return {'@context': 'https://schema.org', '@type': 'WebPage', 'url': canonical,
            'inLanguage': 'hi', 'mainEntity': {
                '@type': 'CreativeWork', '@id': canonical + '#occurrence', 'url': canonical,
                'name': 'TEST original العربية हिन्दी "quoted"',
                'identifier': {'@type': 'PropertyValue', 'value': 'TEST:occurrence-one'},
                'citation': 'https://source.test/?a=1&b=2',
                'isPartOf': {'@type': 'CreativeWork', 'name': 'TEST source edition',
                             'url': 'https://example.test/project/browse/hi/book/edition/'}}}


class StaticOccurrenceSchemaTests(unittest.TestCase):
    def test_identity_and_all_other_metadata_restore_exactly_without_mutation(self):
        canonical = 'https://example.test/project/hadith/hi/book/edition/one.html'
        original = graph(canonical)
        preserved = copy.deepcopy(original)
        candidate = discovery.compact_occurrence_schema(original, canonical)
        self.assertEqual(original, preserved)
        self.assertNotIn('url', candidate)
        self.assertNotIn('url', candidate['mainEntity'])
        self.assertEqual(urljoin(canonical, candidate['mainEntity']['@id']),
                         original['mainEntity']['@id'])
        restored = copy.deepcopy(candidate)
        restored['url'] = canonical
        restored['mainEntity']['url'] = canonical
        restored['mainEntity']['@id'] = urljoin(canonical, restored['mainEntity']['@id'])
        self.assertEqual(restored, preserved)

    def test_only_exact_writer_occurrences_are_eligible(self):
        canonical = 'https://example.test/project/hadith/one.html'
        inputs = [graph(canonical), {'@type': 'CollectionPage', 'url': canonical}]
        inputs[0]['mainEntity']['url'] = 'https://other.test/edition.html'
        for item in inputs:
            before = copy.deepcopy(item)
            self.assertEqual(discovery.compact_occurrence_schema(item, canonical), before)
            self.assertEqual(item, before)
        item = graph(canonical)
        item['mainEntity']['@id'] = 'unverified-source-identity'
        self.assertEqual(discovery.compact_occurrence_schema(item, canonical), item)

    def test_actual_page_keeps_every_byte_outside_structured_data(self):
        path = 'hadith/hi/book/edition/one.html'
        canonical = discovery.canonical_url(path, SITE)
        original = graph(canonical)
        source = '<h1>TEST source</h1><div class="quotation" lang="hi">TEST हिन्दी &amp; العربية</div>'
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            baseline = discovery.Writer(root, root / 'baseline', SITE)
            candidate = discovery.Writer(root, root / 'candidate', SITE)
            with patch.object(discovery, 'compact_occurrence_schema', side_effect=lambda g, c: g):
                baseline.page(path, 'TEST title', 'TEST description', source,
                              language='hi', schema={'@type': 'WebPage', 'mainEntity': original['mainEntity']})
            candidate.page(path, 'TEST title', 'TEST description', source,
                           language='hi', schema={'@type': 'WebPage', 'mainEntity': original['mainEntity']})
            a = (root / 'baseline' / path).read_text(encoding='utf-8')
            b = (root / 'candidate' / path).read_text(encoding='utf-8')
            start = '<script type="application/ld+json">'
            def split(s):
                prefix, rest = s.split(start, 1)
                schema, suffix = rest.split('</script>', 1)
                return prefix, json.loads(schema), suffix
            aa, bb = split(a), split(b)
            self.assertEqual((aa[0], aa[2]), (bb[0], bb[2]))
            self.assertIn('href=' + canonical, b)
            self.assertEqual(len(a.encode()) - len(b.encode()), 3 * len(canonical.encode()) + 18)
            self.assertEqual(urljoin(canonical, bb[1]['mainEntity']['@id']), aa[1]['mainEntity']['@id'])

    def test_nonindexable_404_keeps_absolute_schema(self):
        canonical = discovery.canonical_url('404.html', SITE)
        with tempfile.TemporaryDirectory() as name:
            writer = discovery.Writer(Path(name), Path(name), SITE)
            writer.page('404.html', 'TEST missing', 'TEST', '<h1>TEST missing</h1>',
                        schema={'@type': 'WebPage', 'mainEntity': graph(canonical)['mainEntity']}, indexable=False)
            result = (Path(name) / '404.html').read_text(encoding='utf-8')
            schema = json.loads(result.split('<script type="application/ld+json">')[1].split('</script>')[0])
            self.assertEqual(schema['url'], canonical)
            self.assertEqual(schema['mainEntity']['@id'], canonical + '#occurrence')


if __name__ == '__main__':
    unittest.main()
