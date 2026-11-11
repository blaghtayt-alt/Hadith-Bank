"""Verify public Quran excerpts against their bundled, pinned original bytes.

These tests need neither network access nor the transient acquisition cache.
They protect the distinctions that matter to users: exact words, source scope,
canonical citations, excluded commentary, and unknown translation provenance.
"""
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from extract_quran_hadith import Extractor, PIN, TYPE_LABELS, blob_sha, pointer_get, references


class QuranHadithExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        cls.bundles = {}
        cls.sources = {}
        cls.manifests = []
        for path in sorted((ROOT / 'materials').glob('quran-excerpts-*/manifest.json')):
            manifest = json.loads(path.read_text(encoding='utf-8'))
            cls.manifests.append(manifest)
            records_path = ROOT / manifest['records']['path']
            source_path = ROOT / manifest['source']['path']
            rows = json.loads(records_path.read_text(encoding='utf-8'))
            cls.rows.extend(rows)
            source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if source_hash not in cls.bundles:
                bundle = json.loads(source_path.read_text(encoding='utf-8'))
                cls.bundles[source_hash] = bundle
                for entry in bundle['files']:
                    previous = cls.sources.setdefault(entry['path'], entry)
                    if previous != entry:
                        raise AssertionError('Conflicting original source versions: ' + entry['path'])
        cls.by_id = {row['id']: row for row in cls.rows}
        cls.report = json.loads((ROOT / 'reports/quran-hadith-extraction.json').read_text(encoding='utf-8'))

    def verify_location(self, locator, expected):
        source = self.sources[locator['path']]
        document = json.loads(source['raw_text'])
        whole = pointer_get(document, locator['json_pointer'])
        start, end = locator['char_start'], locator['char_end']
        self.assertEqual(whole[start:end], expected, locator)
        self.assertEqual(locator['git_blob_sha'], source['git_blob_sha'])
        self.assertEqual(locator['sha256'], source['sha256'])
        self.assertEqual(locator['text_sha256'], hashlib.sha256(expected.encode('utf-8')).hexdigest())
        self.assertEqual(locator['decoded_utf8_start'], len(whole[:start].encode('utf-8')))
        self.assertEqual(locator['decoded_utf8_end'], len(whole[:end].encode('utf-8')))

    def test_original_bytes_and_manifests_are_pinned(self):
        self.assertEqual(len(self.bundles), 7, 'One identical source bundle per language, reused by its collections')
        for bundle in self.bundles.values():
            self.assertEqual(bundle['commit'], PIN)
            for entry in bundle['files']:
                raw = entry['raw_text'].encode('utf-8')
                self.assertEqual(len(raw), entry['byte_count'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
                self.assertEqual(blob_sha(raw), entry['git_blob_sha'])
        for manifest in self.manifests:
            for key in ('source', 'records'):
                path = ROOT / manifest[key]['path']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), manifest[key]['sha256'])
            rows = json.loads((ROOT / manifest['records']['path']).read_text())
            self.assertEqual(len(rows), manifest['records']['count'])
            self.assertTrue(all(row['book_key'] == manifest['book'] for row in rows))

    def test_every_quote_arabic_and_citation_is_an_exact_source_slice(self):
        for row in self.rows:
            with self.subTest(id=row['id']):
                self.verify_location(row['source']['original_locator'], row['text']['translation'])
                if row['text']['arabic'] is not None:
                    self.verify_location(row['source']['arabic_locator'], row['text']['arabic'])
                for reference in row['references']['items']:
                    self.verify_location(reference['locator'], reference['source_citation'])
                self.assertIn(row['record_type'], TYPE_LABELS)
                self.assertTrue(row['source']['is_excerpt'])

    def test_mirrors_do_not_inflate_occurrence_counts(self):
        self.assertEqual(len(self.rows), len(self.by_id))
        spans = [(x['language'], x['source']['original_locator']['path'], x['source']['original_locator']['json_pointer'],
                  x['source']['original_locator']['char_start'], x['source']['original_locator']['char_end']) for x in self.rows]
        self.assertEqual(len(spans), len(set(spans)))
        self.assertEqual(len(self.rows), self.report['occurrences'])
        self.assertEqual(dict(collections.Counter(x['language'] for x in self.rows)), self.report['by_language'])
        self.assertFalse(any(x['source']['original_locator']['path'].endswith(('.md', '.txt')) for x in self.rows))

    def test_proverbs_questions_glosses_and_pure_explanation_are_excluded(self):
        for row in self.rows:
            family, token = row['source']['family'], row['source']['source_token']
            if family == 'ikhlas':
                self.assertNotIn(token, ('N34', 'N49', 'N96', 'N131'))
            if family == 'fatiha':
                self.assertNotEqual(token, 'H28')
            if family == 'qiyamah':
                self.assertLessEqual(int(token[1:]), 10)
        for value in ('iman-quran-fa-ikhlas-n82', 'iman-quran-vi-ikhlas-n62',
                      'iman-quran-zh-cn-ikhlas-n36', 'iman-quran-hi-ikhlas-n60',
                      'iman-quran-ja-fatiha-h26', 'iman-quran-fa-fatiha-h20'):
            self.assertNotIn(value, self.by_id)
        decisions = self.report['decisions']
        self.assertTrue(any(x['status'].startswith('excluded') and x['source_token'] == 'N131' for x in decisions))
        self.assertTrue(any(x['status'].startswith('excluded') and x['source_token'] == 'H28' for x in decisions))

    def test_actual_parallel_reference_and_numbering_scopes(self):
        row = self.by_id['iman-quran-ja-qiyamah-h09']
        self.assertEqual((row['book_key'], row['number']['in_book']), ('ibn-majah', '2707'))
        self.assertTrue(all(x['scope'] == 'variant' for x in row['references']['items'] if x['book_key'] in ('ahmad', 'hakim')))
        row = self.by_id['iman-quran-ja-qiyamah-h10']
        self.assertEqual(row['number']['in_book'], '884')
        self.assertEqual(row['references']['items'][0]['alternate_numbering']['english'], '883')
        row = self.by_id['iman-quran-hi-ikhlas-n82']
        self.assertEqual(row['number']['in_book'], '6313')
        self.assertFalse(any(x['scope'] == 'main_quote' and x['number'] == '247' for x in row['references']['items']))
        self.assertEqual(self.by_id['iman-quran-fil-ikhlas-n12']['number']['in_book'], '128')
        self.assertEqual(self.by_id['iman-quran-vi-ikhlas-n36']['number']['in_book'], '68')
        self.assertEqual(self.by_id['iman-quran-fa-fatiha-h0']['number']['in_book'], '5092')
        for language in ('ja','fil','vi','zh-cn','uz'):
            row = self.by_id[f'iman-quran-{language}-fatiha-h13']
            self.assertFalse(any(x['scope'] == 'main_quote' and x['book_key'] == 'bukhari' for x in row['references']['items']))

    def test_companions_persian_and_unknown_origin_remain_distinct(self):
        companion_rows = [x for x in self.rows if x['record_type'] == 'companion_report_excerpt']
        self.assertEqual(len(companion_rows), 4)
        self.assertTrue(all(x['source']['source_token'] == 'N32' for x in companion_rows))
        self.assertTrue(any(x['language'] == 'fa' for x in self.rows))
        for row in self.rows:
            self.assertEqual(row['translation_provenance']['origin'], 'unknown')
            self.assertEqual(row['ai_translation'], 'unknown')
            self.assertIs(row['extraction']['ocr_used'], False)
            self.assertIsNone(row['number']['canonical'])

    def test_discontinuous_source_fields_are_not_silently_joined(self):
        for language, token in [('hi','n36'),('hi','n89'),('zh-cn','n89')]:
            left = self.by_id[f'iman-quran-{language}-ikhlas-{token}-1']
            right = self.by_id[f'iman-quran-{language}-ikhlas-{token}-2']
            self.assertNotEqual(left['source']['original_locator']['json_pointer'], right['source']['original_locator']['json_pointer'])
            self.assertNotIn(f'iman-quran-{language}-ikhlas-{token}', self.by_id)

    def test_compact_citations_do_not_absorb_annotation_letters(self):
        for text, expected in [('Bukhari5013parallel','5013'), ('AbuDawud1463seek','1463'),
                               ('Muslim591prayer','591'), ('IbnMajah150parent','150'), ('Muslim811a','811a')]:
            self.assertEqual(references(text)[0]['number'], expected)
        self.assertEqual(references('QahtaniHisn2015/1436'), [])

    def test_scope_files_and_markdown_evidence_are_preserved(self):
        for row in self.report['source_files']:
            self.assertTrue(row['locally_verified'], row['path'])
            source = self.sources[row['path']]
            self.assertEqual(row['git_blob_sha'], source['git_blob_sha'])
            self.assertEqual(row['sha256'], source['sha256'])
            self.assertEqual(row['byte_count'], source['byte_count'])
        comparisons = self.report['markdown_comparisons']
        markdown_paths = {x['path'] for x in self.report['source_files'] if x['path'].endswith(('.md', '.txt'))}
        self.assertEqual(markdown_paths, {x['path'] for x in comparisons})
        normalized = lambda text: re.sub(r'\s+', ' ', text).strip()
        for row in comparisons:
            text = self.sources[row['path']]['raw_text']
            self.assertEqual(hashlib.sha256(text.encode('utf-8')).hexdigest(), row['sha256'])
            if not row['is_format_mirror']:
                self.assertEqual(row['status'], 'examined_source_note')
                self.assertNotIn('paired_json_path', row)
                continue
            self.assertEqual(row['paired_json_sha256'], self.sources[row['paired_json_path']]['sha256'])
            self.assertEqual(row['unaccounted_quoted_spans'], 0)
            for check in row['quotation_checks']:
                quote = text[check['char_start']:check['char_end']]
                self.assertEqual(hashlib.sha256(quote.encode('utf-8')).hexdigest(), check['text_sha256'])
                source_values = []
                for match in check['source_fields']:
                    value = pointer_get(json.loads(self.sources[match['path']]['raw_text']), match['json_pointer'])
                    self.assertEqual(hashlib.sha256(value.encode('utf-8')).hexdigest(), match['source_field_sha256'])
                    source_values.append(value)
                if check['status'] == 'matched_structured_source_field':
                    self.assertIn(normalized(quote), normalized(source_values[0]))
                else:
                    self.assertEqual(check['status'], 'matched_rendered_quran_sequence_and_credits')
                    parts = [line.strip().removeprefix('> ').strip() for line in quote.splitlines()
                             if line.strip() and not line.lstrip().startswith('#')
                             and not re.fullmatch(r'\s*\[[^\]]+\]\([^)]+\)\s*', line)]
                    self.assertEqual(len(parts), len(source_values))
                    for part, value in zip(parts, source_values):
                        self.assertIn(normalized(part), normalized(value))
            for check in row['extracted_record_checks']:
                quote = self.by_id[check['record_id']]['text']['translation']
                if check['comparison'] == 'exact_substring':
                    self.assertIn(quote, text)
                else:
                    self.assertEqual(check['comparison'], 'layout_whitespace_only')
                    self.assertIn(normalized(quote), normalized(text))

    def test_bundled_sources_replay_without_external_checkout(self):
        extractor = Extractor.from_bundles(ROOT)
        self.assertIsNone(extractor.snapshot)
        extractor.fatiha()
        extractor.ikhlas()
        extractor.qiyamah()
        extractor.heart_quran()
        self.assertEqual({x['id']: x for x in extractor.records}, self.by_id)


if __name__ == '__main__':
    unittest.main()
