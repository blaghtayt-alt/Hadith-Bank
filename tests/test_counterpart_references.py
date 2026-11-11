"""Guard book/number labels against bibliographic years and unrelated works."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from counterpart_references import format_citation, parse_provider_references


class CounterpartReferenceTests(unittest.TestCase):
    def test_two_primary_collections_keep_exact_source_lines(self):
        source = 'صحيح البخاري (9/ 2) (6864).\nصحيح مسلم (3/ 1304) (1678).'
        refs = parse_provider_references(source)
        self.assertEqual([(r['book_key'], r['number']) for r in refs],
                         [('bukhari', '6864'), ('muslim', '1678')])
        self.assertEqual([r['source_citation'] for r in refs], source.splitlines())
        self.assertTrue(all(r['scope'] == 'publisher_entry' for r in refs))

    def test_multiple_locations_and_numbers_on_one_line(self):
        source = 'صحيح البخاري (9/ 22) (6953)، (1/ 6) (1).'
        self.assertEqual([r['number'] for r in parse_provider_references(source)], ['6953', '1'])

    def test_publication_years_are_never_promoted_to_numbers(self):
        source = '\n'.join([
            'صحيح البخاري، نشر: دار طوق النجاة (1422).',
            '1- صحيح مسلم، تحقيق محمد فؤاد عبد الباقي، الطبعة (1423).',
            'صحيح البخاري (مصورة عن السلطانية) (1422).',
            'صحيح مسلم (1423 هـ).',
            'صحيح البخاري (1/ 25)، الطبعة الأولى (1422).',
        ])
        self.assertEqual(parse_provider_references(source), [])

    def test_commentary_titles_containing_collection_names_are_excluded(self):
        source = '\n'.join([
            'شرح النووي على مسلم (13/54) (1907).',
            'بهجة الناظرين شرح رياض الصالحين (2/403) (1274).',
            'فتح الباري شرح صحيح البخاري (1/20) (1).',
            'شرح سنن أبي داود للعباد (162/18) (5124).',
        ])
        self.assertEqual(parse_provider_references(source), [])

    def test_numbers_of_following_unrelated_work_are_not_attached_to_first_book(self):
        source = 'صحيح ابن حبان (2/69) (354)، فيض القدير (2/292) (999).'
        self.assertEqual([r['number'] for r in parse_provider_references(source)], ['354'])
        source = 'صحيح البخاري (1/2) (3)، صحيح مسلم (4/5) (6).'
        self.assertEqual([(r['book_key'], r['number']) for r in parse_provider_references(source)],
                         [('bukhari', '3')])

    def test_arabic_and_persian_digits_become_ascii_only_in_parsed_number(self):
        source = 'صحيح مسلم (٣/ ۱۳۰۴) (١٦٧٨).'
        refs = parse_provider_references(source)
        self.assertEqual(refs[0]['number'], '1678')
        self.assertEqual(refs[0]['source_citation'], source)

    def test_volume_page_only_and_ambiguous_ranges_do_not_create_numbers(self):
        for source in ['صحيح مسلم (1/33).', 'رياض الصالحين (ص358).',
                       'صحيح البخاري (2/74) (1258 - 1259).', 'صحيح البخاري (1-9).']:
            with self.subTest(source=source):
                self.assertEqual(parse_provider_references(source), [])

    def test_explicit_comma_lists_work_and_duplicate_same_line_numbers_are_removed(self):
        source = 'سنن أبي داود (2/20) (15، 16) (15).'
        self.assertEqual([r['number'] for r in parse_provider_references(source)], ['15', '16'])

    def test_distinct_nasai_works_are_not_collapsed(self):
        source = 'سنن النسائي (1/279) (572).\nالسنن الكبرى للنسائي (9/87) (9963).'
        self.assertEqual([(r['book_key'], r['number']) for r in parse_provider_references(source)],
                         [('nasai', '572'), ('nasai-kubra', '9963')])

    def test_numbered_bullet_citation_and_formatting(self):
        ref = parse_provider_references('- 1- صحيح مسلم (3/1304) (1678).')[0]
        self.assertEqual(format_citation(ref), '[Sahih Muslim no. 1678]')
        self.assertEqual(format_citation(ref, 'ar'), '[صحيح مسلم، رقم 1678]')

    def test_invalid_and_empty_inputs(self):
        for source in [None, {}, [], '', 'صحيح مسلم (0)', 'صحيح مسلم ((1))']:
            with self.subTest(source=source):
                self.assertEqual(parse_provider_references(source), [])


if __name__ == '__main__':
    unittest.main()
