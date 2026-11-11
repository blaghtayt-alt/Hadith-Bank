"""Independent source-fidelity regressions for the Chinese al-Shaybani Muwatta.

Read the preserved DOCX and published candidate directly; do not import the
extractor to generate expected values. These checks do not certify authenticity
or the underlying translation.
"""
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from xml.dom import minidom
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from citation_search import has_noncanonical_numbering, record_citation_pairs
from counterpart_identity import provider_identity
from current_provenance import classification
from review_display_policy import review_badges

MATERIAL = ROOT / 'materials/zh-muwatta-shaybani-yu-2000-docx'
SOURCE_SHA256 = 'cf65c0e865be95a709f228b021e23b94dbc2e3a88d52139330b623a070f5d1b3'
WORD_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


class ChineseMuwattaSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((MATERIAL / 'manifest.json').read_text(encoding='utf-8'))
        cls.source = (ROOT / cls.manifest['source']['path']).read_bytes()
        cls.native = (MATERIAL / 'native-text.txt').read_text(encoding='utf-8')
        cls.rows = [json.loads(line) for line in (MATERIAL / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
        cls.by_number = {row['number']['in_book']: row for row in cls.rows}
        cls.ledger = json.loads(gzip.decompress((MATERIAL / 'paragraph-ledger.json.gz').read_bytes()))
        cls.exclusions = json.loads(gzip.decompress((MATERIAL / 'excluded-commentary.json.gz').read_bytes()))['items']
        cls.number_ledger = json.loads((MATERIAL / 'source-number-ledger.json').read_text(encoding='utf-8'))
        cls.metadata = json.loads((MATERIAL / 'source-metadata.json').read_text(encoding='utf-8'))
        # A different XML reader from the importer establishes the body text
        # independently, including every original paragraph boundary.
        with ZipFile(io.BytesIO(cls.source)) as package:
            cls.xml = minidom.parseString(package.read('word/document.xml'))
        body = cls.xml.getElementsByTagNameNS(WORD_NS, 'body')[0]
        nodes = [node for node in body.childNodes
                 if node.nodeType == node.ELEMENT_NODE and node.namespaceURI == WORD_NS and node.localName == 'p']
        cls.paragraphs = [
            ''.join(''.join(child.data for child in node.childNodes
                            if child.nodeType in (child.TEXT_NODE, child.CDATA_SECTION_NODE))
                    for node in paragraph.getElementsByTagNameNS(WORD_NS, 't'))
            for paragraph in nodes]
        cls.offsets = []
        offset = 0
        for text in cls.paragraphs:
            cls.offsets.append(offset)
            offset += len(text) + 2

    def test_original_docx_bytes_and_registered_hashes(self):
        self.assertEqual(len(self.source), 201520)
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), SOURCE_SHA256)
        self.assertEqual(self.manifest['source']['sha256'], SOURCE_SHA256)
        self.assertEqual(self.manifest['source']['format'], 'docx')
        self.assertTrue(self.manifest['source']['name'].startswith('穆宛塔圣训集 — Muwatta'))
        self.assertIn('al-Shaybani', self.manifest['source']['name'])
        self.assertEqual(self.manifest['records']['count'], 1006)
        self.assertEqual(hashlib.sha256((MATERIAL / 'records.jsonl').read_bytes()).hexdigest(),
                         self.manifest['records']['sha256'])

    def test_independent_xml_text_equals_full_native_text_and_paragraph_ledger(self):
        self.assertEqual(len(self.paragraphs), 2067)
        self.assertEqual(sum(map(len, self.paragraphs)), 132443)
        self.assertEqual('\n\n'.join(self.paragraphs), self.native)
        self.assertEqual([p['text'] for p in self.ledger['paragraphs']], self.paragraphs)
        self.assertEqual([p['index'] for p in self.ledger['paragraphs']], list(range(2067)))
        self.assertEqual(hashlib.sha256(self.native.encode('utf-8')).hexdigest(),
                         self.metadata['extraction']['native_text_sha256'])
        for tag in ('tbl', 'txbxContent', 'tab', 'br', 'cr', 'sym', 'delText',
                    'footnoteReference', 'endnoteReference'):
            self.assertFalse(self.xml.getElementsByTagNameNS(WORD_NS, tag), tag)

    def test_every_original_character_has_one_audited_role(self):
        kinds = Counter()
        for index, paragraph in enumerate(self.ledger['paragraphs']):
            cursor = 0
            for span in paragraph['segments']:
                self.assertEqual(span['start'], cursor, index)
                self.assertGreaterEqual(span['end'], span['start'], index)
                self.assertEqual(self.paragraphs[index][span['start']:span['end']], span['text'], index)
                cursor = span['end']
                kinds[span['kind']] += 1
            self.assertEqual(cursor, len(self.paragraphs[index]), index)
        self.assertEqual(kinds['book_heading'], 19)
        self.assertEqual(kinds['section_heading'], 434)
        self.assertEqual(kinds['source_number'], 1005)
        self.assertEqual(kinds['commentary'] + kinds['translator_note'], 594)
        self.assertEqual(len(self.exclusions), 594)

    def test_every_imported_character_reconstructs_from_unmodified_source_spans(self):
        included = []
        expected = []
        for index, paragraph in enumerate(self.ledger['paragraphs']):
            for span in paragraph['segments']:
                if span['kind'] == 'report_text':
                    expected.append((self.offsets[index] + span['start'],
                                     self.offsets[index] + span['end'], span['recordId']))
        for row in self.rows:
            spans = row['source_locator']['included_source_spans']
            self.assertTrue(spans, row['id'])
            self.assertEqual(''.join(self.native[a:b] for a, b in spans), row['text']['translation'], row['id'])
            for a, b in spans:
                self.assertTrue(0 <= a < b <= len(self.native), row['id'])
                if self.native[a:b] != '\n\n':
                    included.append((a, b, row['id']))
            self.assertTrue(all(spans[i][1] <= spans[i + 1][0] for i in range(len(spans) - 1)), row['id'])
        self.assertEqual(sorted(included), sorted(expected))
        ordered = sorted(included)
        self.assertTrue(all(ordered[i][1] <= ordered[i + 1][0] for i in range(len(ordered) - 1)))

    def test_excluded_comments_are_preserved_but_do_not_enter_narration_payload(self):
        removed = []
        by_id = {row['id']: row for row in self.rows}
        for item in self.exclusions:
            a, b = item['source_span']
            self.assertEqual(self.native[a:b], item['text'])
            self.assertEqual(self.paragraphs[item['paragraphIndex']][item['start']:item['end']], item['text'])
            if item.get('recordId'):
                structure = [heading for heading in (item.get('book'), item.get('section')) if heading]
                expected_headings = [heading.get('raw', heading['title']) for heading in structure]
                self.assertEqual(by_id[item['recordId']]['source_headings'], expected_headings)
            removed.append((a, b))
        for index in (1495, 1671, 1775, 1817, 1826):
            item = next(item for item in self.exclusions if item['paragraphIndex'] == index)
            self.assertNotIn('recordId', item, 'A new-section note must not attach to the preceding section report')
        for row in self.rows:
            for a, b in row['source_locator']['included_source_spans']:
                self.assertFalse(any(a < right and left < b for left, right in removed), row['id'])
            self.assertNotIn('谢巴尼说', row['text']['translation'])
            self.assertNotIn('哈奈菲教法学家们均这样主张', row['text']['translation'])
            self.assertNotRegex(row['text']['translation'], r'(?m)^注[：:]')
            self.assertEqual(row['commentary'], {'arabic': None, 'translation': None})
            self.assertEqual(row['footnotes'], [])

    def test_printed_numbers_and_the_unnumbered_report_are_not_filled_or_duplicated(self):
        numbers = [int(row['number']['in_book']) for row in self.rows if row['number']['in_book'] is not None]
        self.assertEqual(len(numbers), 1005)
        self.assertEqual(len(set(numbers)), 1005)
        self.assertEqual(set(range(1, 1009)) - set(numbers), {196, 528, 764})
        self.assertEqual(len({row['id'] for row in self.rows}), 1006)
        self.assertEqual(self.number_ledger['missing_printed_numbers'], [196, 528, 764])
        self.assertFalse(self.number_ledger['unnumbered_report_has_assigned_number'])
        self.assertEqual({entry['id'] for entry in self.number_ledger['entries']}, {row['id'] for row in self.rows})
        unnumbered = self.by_number[None]
        for field in ('source_entry_id', 'in_book', 'canonical', 'as_printed'):
            self.assertIsNone(unnumbered['number'][field], field)
        self.assertEqual(unnumbered['source_locator']['paragraph_indices_zero_based'], [1062])
        self.assertEqual(unnumbered['text']['translation'], self.paragraphs[1062])
        position = self.rows.index(unnumbered)
        self.assertEqual(self.rows[position - 1]['number']['in_book'], '527')
        self.assertEqual(self.rows[position + 1]['number']['in_book'], '529')

    def test_two_source_continuations_are_complete_without_neighboring_comments(self):
        for number, first, second in (('64', 122, 123), ('135', 244, 245)):
            row = self.by_number[number]
            self.assertEqual(row['text']['translation'],
                             self.paragraphs[first][len(number) + 1:] + '\n\n' + self.paragraphs[second])
            self.assertEqual(row['page']['doc_paragraphs'], [first, second])
            self.assertTrue(row['extraction']['continuation_decisions'])
        self.assertEqual(self.by_number['107']['text']['translation'], self.paragraphs[203][4:])
        self.assertTrue(any(item['paragraphIndex'] == 204 and item['text'] == self.paragraphs[204]
                            for item in self.exclusions))

    def test_reviewed_inline_commentary_does_not_leak(self):
        cases = {
            '44': (83, '—即流精溢只破小净不坏大净，年老及体弱者时有发生。'),
            '131': (233, '（系指拜功之回赐)'),
            '525': (1055, '谢巴尼说'),
            '558': (1131, '伊布·麦斯欧德、艾布·哈尼法及哈奈菲教法学家们均这样主张。'),
            '585': (1194, '谢巴尼说'),
            '596': (1219, '注：'),
            '631': (1274, '由此可见，宰牲节宰牲的人剃头属可佳行为。'),
            '958': (1995, '（穆圣说此话的意思是：'),
        }
        for number, (index, marker) in cases.items():
            with self.subTest(number=number):
                original = self.paragraphs[index]
                offset = original.index(marker)
                self.assertEqual(self.by_number[number]['text']['translation'], original[len(number) + 1:offset])
                self.assertTrue(any(item['paragraphIndex'] == index and item['text'] == original[offset:]
                                    for item in self.exclusions))
        self.assertTrue(self.by_number['631']['text']['translation'].endswith('伊本·欧麦尔自己却曾剃头。'))

    def test_midparagraph_comment_removal_retains_both_narration_segments(self):
        note = '（欧勒沃认为“古勒义”系净期，故第三次月经来潮时，则待婚期业已结束）'
        original = self.paragraphs[1235][4:]
        before, after = original.split(note)
        row = self.by_number['603']
        self.assertTrue(before and after)
        self.assertEqual(row['text']['translation'], before + after)
        self.assertEqual(len(row['source_locator']['included_source_spans']), 2)
        self.assertTrue(any(item['paragraphIndex'] == 1235 and item['text'] == note
                            for item in self.exclusions))

    def test_fullwidth_number_and_missing_narrator_are_not_normalized_or_invented(self):
        row = self.by_number['669']
        index = row['source_locator']['paragraph_indices_zero_based'][0]
        self.assertTrue(self.paragraphs[index].startswith('669．'))
        self.assertEqual(row['number']['as_printed'], '669．')
        self.assertEqual(row['text']['translation'], self.paragraphs[index][4:])
        self.assertEqual(self.by_number['325']['text']['translation'], '骆驼不及五峰不纳天课。')
        self.assertIsNone(self.by_number['325']['narrator']['name'])
        self.assertIsNone(self.by_number['325']['isnad'])

    def test_referential_reports_preserve_their_short_source_wording(self):
        expected = {'453': 881, '604': 1236, '606': 1238, '621': 1260, '960': 1997, '972': 2011}
        self.assertEqual({row['number']['in_book'] for row in self.rows
                          if row['content_kind'] == 'referential_source_report'}, set(expected))
        for number, index in expected.items():
            row = self.by_number[number]
            self.assertEqual(row['text']['translation'], self.paragraphs[index][4:])
            self.assertTrue(row['source_defects'], number)

    def test_source_headings_remain_verbatim(self):
        book_titles = set()
        for row in self.rows:
            book_titles.add(row['source_headings'][0])
            self.assertEqual([tag['value_verbatim'] for tag in row['source_structure_tags']], row['source_headings'])
            for tag in row['source_structure_tags']:
                index = tag['source_locator']['paragraph_index_zero_based']
                self.assertEqual(tag['value_verbatim'], self.paragraphs[index])
        self.assertEqual(len(book_titles), 19)

    def test_source_numbers_never_become_canonical_or_provider_matches(self):
        for row in self.rows:
            self.assertIsNone(row['number']['canonical'], row['id'])
            self.assertEqual(row['number']['scope'], 'source_local')
            self.assertTrue(has_noncanonical_numbering(row['number']), row['id'])
            self.assertEqual(record_citation_pairs(row), set(), row['id'])
            identity = provider_identity(row)
            self.assertEqual(identity['status'], 'absent', row['id'])
            self.assertIsNone(identity['id'], row['id'])

    def test_provenance_ocr_display_and_unperformed_certification_stay_distinct(self):
        self.assertEqual(self.paragraphs[10], '译者：穆萨·余崇仁')
        self.assertEqual(self.paragraphs[11], '2000年十月二十三日于韦州')
        self.assertTrue(self.manifest['publication']['authorized'])
        self.assertIsNone(self.metadata['completeness']['full_collection'])
        for row in self.rows:
            self.assertEqual(classification(row), 'human', row['id'])
            self.assertFalse(row['ai_translation'])
            self.assertFalse(row['extraction']['ocr_used'])
            self.assertIsNone(row['extraction']['upstream_transcription_method'])
            self.assertEqual(review_badges(row), [], row['id'])
            self.assertIsNone(row['text']['arabic'])
            self.assertIsNone(row['grading']['grade'])
            self.assertEqual(row['review']['independent_pro_qc'], 'not_performed')
            self.assertFalse(row['review']['certified_release_eligible'])
            self.assertEqual(row['rights']['status'], 'not_assessed_for_publication')


if __name__ == '__main__':
    unittest.main()
