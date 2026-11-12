"""Source-preservation checks for Chinese Hisn, without regenerating expectations.

These checks establish partition and quotation fidelity, not authenticity or a
new independent review of the original PDF.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_reader import record_type_info

IMPORT = ROOT / 'imports/chinese-hisn-final-20261110'
MATERIAL = ROOT / 'materials/zh-cn-hisn-muslim-1a09ee75'
SUMMARY_IDS = {f'ZH-HISN-{number:03}' for number in (
    12, 24, 70, 71, 75, 76, 99, 100, 101, 110, 115, 133, 141)}


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


class ChineseHisnSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((IMPORT / 'zh_hisn_final_corrected.json').read_text(encoding='utf-8'))
        cls.original = {row['record_id']: row for row in cls.source['records']}
        cls.ledger = json.loads((IMPORT / 'classification/decisions.json').read_text(encoding='utf-8'))
        cls.decisions = {row['record_id']: row for row in cls.ledger['decisions']}
        cls.rows = read_rows(MATERIAL / 'records.jsonl')
        cls.by_id = {row['id']: row for row in cls.rows}
        cls.non_hadith = read_rows(ROOT / 'non-hadith/zh-cn-hisn-muslim-1a09ee75/records.jsonl')
        cls.unknown = read_rows(ROOT / 'unclassified/zh-cn-hisn-muslim-1a09ee75/records.jsonl')
        cls.manifest = json.loads((MATERIAL / 'manifest.json').read_text(encoding='utf-8'))

    def test_seven_deliverables_and_original_pdf_keep_exact_bytes(self):
        hashes = {
            'zh_hisn_final_corrected.json': '0c000f5f5cfac6ba52bd8339b205bcdd775f952ace81bc261930960fda8f38d5',
            'zh_hisn_final_corrected.jsonl': 'ad369931a3107bb3bc87feb2613bdba0564b0ead4e16eb837e4050ce6a013146',
            'zh_hisn_final_corrected.csv': '0f5b0a15d1504ef26c2bc2eae242f5de7bc0e76eda7b4819bee65e3fc1658da4',
            'zh_hisn_final_pages.jsonl': 'd850cdd0014c08e51c39b6b63c4d695740abf438a22a023987dd7a7cb6c6106a',
            'zh_hisn_final_metadata.json': 'abb5319b34cb81deb0c9f68649c6389e0ae7b22036d687c1a867cfb903e34131',
            'FINAL_EVALUATION_REPORT_JA.txt': '4d8396ea9d0a9237d78f66e841ac62e2abff628ef0234974acb7cf4de73c483f',
            'zh_hisn_final_delivery_receipt.json': '6da626b28d3477ed2fc839397d7e1a7ce9b83e6def7206d9ee8b6b928846b911',
        }
        for name, digest in hashes.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((IMPORT / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256((MATERIAL / 'zh-hisn.pdf').read_bytes()).hexdigest(),
                         '1a09ee75c544d3ced4ac287bd9c996aec9e508f7c98c0965b5e3744131c2cfd4')

    def test_all_279_source_occurrences_are_preserved_in_one_partition(self):
        self.assertEqual([len(self.rows), len(self.non_hadith), len(self.unknown)], [251, 23, 5])
        all_rows = self.rows + self.non_hadith + self.unknown
        self.assertEqual(Counter(row['id'] for row in all_rows), Counter(self.original.keys()))
        for kind, rows in (('hadith', self.rows), ('non_hadith', self.non_hadith), ('unknown', self.unknown)):
            for row in rows:
                self.assertEqual(self.decisions[row['id']]['classification'], kind)
                if kind != 'hadith':
                    self.assertFalse(row['visible_in_hadith_html'])
                    self.assertEqual(row['original_source_record'], self.original[row['id']])
        self.assertEqual(self.manifest['records']['count'], 251)
        self.assertEqual(self.manifest['records']['sha256'],
                         hashlib.sha256((MATERIAL / 'records.jsonl').read_bytes()).hexdigest())

    def test_selected_and_excluded_spans_account_for_every_original_character(self):
        for identifier, decision in self.decisions.items():
            body = self.original[identifier]['body_text_verbatim']
            spans = sorted(decision['included_body_spans'] + decision['excluded_body_spans'])
            boundaries = [0]
            for start, end in spans:
                self.assertEqual(start, boundaries[-1], identifier)
                self.assertGreater(end, start, identifier)
                boundaries.append(end)
            self.assertEqual(boundaries[-1], len(body), identifier)
            for part in decision['selected_segments']:
                self.assertEqual(body[part['start']:part['end']], part['text_verbatim'], identifier)
                self.assertEqual(hashlib.sha256(part['text_verbatim'].encode()).hexdigest(), part['sha256'])
            if identifier in self.by_id:
                row = self.by_id[identifier]
                self.assertEqual(row['source_locator']['included_body_spans'], decision['included_body_spans'])
                actual = row['text']['translation']
                for part in reversed(decision['selected_segments']):
                    self.assertTrue(actual.endswith(part['text_verbatim']), identifier)
                    actual = actual[:-len(part['text_verbatim'])]
                    if actual:
                        join = next(join for join in row['source_locator']['display_joins']
                                    if join['between_body_offsets'][1] == part['start'])
                        separator = join['separator']
                        self.assertTrue(actual.endswith(separator), identifier)
                        if separator:
                            actual = actual[:-len(separator)]
                self.assertEqual(actual, '', identifier)
        self.assertEqual(self.by_id['ZH-HISN-114']['source_locator']['included_body_spans'],
                         [[0, 34], [39, 61], [66, 73], [78, 91]])

    def test_reported_practices_are_included_without_becoming_direct_quotes(self):
        summaries = {row['id'] for row in self.rows if row['record_type'] == 'hadith_meaning_excerpt'}
        self.assertEqual(summaries, SUMMARY_IDS)
        for identifier in summaries:
            row = self.by_id[identifier]
            qualifiers = row['source_locator']['classification_qualifications']
            self.assertTrue(qualifiers['source_wording_is_compiler_summary'])
            self.assertFalse(qualifiers['render_as_direct_prophetic_quote'])
            self.assertIn(qualifiers['source_summary_qualification'], row['review']['issues'])
            self.assertEqual(record_type_info(row)['label'], 'Reported meaning')

    def test_original_review_and_unapproved_counterpart_hold_are_preserved(self):
        self.assertEqual(self.manifest['counterpart_policy']['mode'], 'disabled')
        self.assertEqual(self.manifest['publication']['historical_bank_readiness'], 'FAIL')
        self.assertFalse(self.manifest['publication']['certified_release_eligible'])
        for row in self.rows:
            self.assertIsNone(row['text']['arabic'])
            self.assertIsNone(row['number']['canonical'])
            self.assertIsNone(row['grading']['grade'])
            self.assertFalse(row['review']['certified_release_eligible'])
            self.assertEqual(row['review']['historical_source_review'], self.original[row['id']]['review'])
            self.assertEqual(row['review']['historical_publication_assessment'],
                             self.original[row['id']]['publication_assessment'])
            history = ROOT / row['extraction']['source_extraction_history']
            self.assertTrue(history.is_file())
            self.assertEqual(history.name, 'FINAL_EVALUATION_REPORT_JA.txt')


if __name__ == '__main__':
    unittest.main()
