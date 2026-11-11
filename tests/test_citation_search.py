"""Synthetic TEST records for paired collection-and-number search."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hadith_search as searcher
import citation_search as citations
import build_reader as reader
from counterpart_references import _BOOKS as PROVIDER_BOOKS
import test_hadith_search as search_fixtures
from test_counterpart_reader import counterparts


def persian_structured_references():
    return [
        {'collection': 'صحيح البخاري', 'numbers': ['١', '۴۴b'],
         'citation_scope': 'Exact terminal citation for this source narration',
         'number_raw': ['91'], 'cross_reference_numbers': ['92']},
        {'field': 'citations_as_printed', 'value': [
            {'collection': 'صحیح مسلم', 'number_as_printed': '۱۹۰۷'},
            {'collection': 'موطأ مالك', 'number_as_printed': '١٢'},
            {'collection': 'Sahih Muslim', 'number_as_printed': '1/23'},
        ]},
        {'collection': 'Sahih al-Bukhari', 'number': '55', 'numbers': ['66']},
        {'collection': 'Sahih al-Bukhari', 'numbers': [],
         'number_raw': ['93'], 'cross_reference_numbers': ['94']},
        {'collection': 'Sahih al-Bukhari', 'numbers': ['95'],
         'citation_scope': 'Reference in commentary'},
        {'field': 'citations_as_printed', 'scope': 'context', 'value': [
            {'collection': 'Sahih Muslim', 'number_as_printed': '96'}]},
        {'field': 'source_assessment', 'value': [
            {'collection': 'Sahih Muslim', 'number_as_printed': '97'}]},
        {'collection': 'Sahih Muslim', 'numbers': ['98'],
         'numbering_system': 'Source-local numbering'},
        {'book_key': 'bukhari', 'collection': 'Sahih Muslim', 'numbers': ['99']},
    ]


class CitationSearchTests(unittest.TestCase):
    def setUp(self):
        self.case = search_fixtures.HadithSearchTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.records = self.case.records[:3]
        for i, row in enumerate(self.records):
            row['book_key'] = 'hadeethenc'
            row['provider_entry_id'] = str(1907 + i)
            row['number'] = {'in_book': None, 'canonical': None}
            row['references'] = {'items': [], 'bibliography_verbatim': 'TEST Bukhari volume 19 page 1907, edition 2020'}
            row['counterparts'] = counterparts()
            row['counterparts']['arabic'] = None
            english = row['counterparts']['english']
            english['text'] = 'TEST reward' if i != 1 else 'TEST generosity'
            english['citation'] = None
            english['references'] = ([{'book_key': 'bukhari', 'number': '1'},
                                      {'book_key': 'muslim', 'number': '1907'}] if i == 0
                                     else [{'book_key': 'bukhari', 'number': '1907'}])
        self.case.records = self.records
        self.case.save()

    def test_cli_pairs_do_not_cross_collections_and_keep_counts_before_limit(self):
        checks = [
            ('Bukhari 1907', [1, 2]),
            ('Bukhari 1 Muslim 1907', [0]),
            ('Bukhari 1, Muslim 1907', [0]),
            ('Bukhari 1907 Muslim 1', []),
            ('reward Bukhari 1907', [2]),
            ('Sahih al-Bukhari no. ١٩٠٧', [1, 2]),
            ('صحيح البخاري رقم ۱۹۰۷', [1, 2]),
            ('Sahih Muslim number 1907', [0]),
            ('1907', [0, 1, 2]),
        ]
        for query, indexes in checks:
            with self.subTest(query=query):
                result = self.case.call(query, limit=1)
                self.assertEqual(result['matched'], len(indexes))
                self.assertEqual([row['id'] for row in result['results']], [self.records[i]['id'] for i in indexes[:1]])
        zero = self.case.call('Bukhari 1907', limit=0)
        self.assertEqual((zero['matched'], zero['shown']), (2, 0))
        self.assertFalse(zero['cache']['rebuilt'])

    def test_explicit_reference_scopes_and_variant_suffixes(self):
        record = self.records[0]
        record['counterparts'] = {'arabic': None, 'english': None}
        record['references']['items'] = [
            {'book_key': 'bukhari', 'number': '88', 'scope': 'commentary'},
            {'book_key': 'bukhari', 'number': '89', 'numbering_scheme': 'unresolved_volume_page_or_number'},
            {'book_key': 'bukhari', 'number': '44b', 'scope': 'variant'},
            {'collection': 'Sahih Muslim', 'number': '٩٩', 'scope': 'main_quote'},
            {'book_key': 'muslim', 'collection': 'Sahih al-Bukhari', 'number': '100'},
            {'book_key': 'muslim', 'number': '17', 'scope': 'main_quote', 'numbering_scheme': 'number_within_source_named_book'},
            {'book_key': 'riyad-as-salihin', 'number': '67', 'scope': 'main_quote', 'numbering_scheme': 'selected_Vietnamese_abridgment_number_not_canonical_Riyad_number'},
        ]
        record['book_key'] = 'bukhari'
        record['number'] = {'in_book': '77', 'numbering_scope': 'this_source_part_and_language_column'}
        self.case.records = [record]
        self.case.save()
        for query in ('Bukhari 88', 'Bukhari 89', 'Bukhari 77', 'Bukhari 1907',
                      'Bukhari 2020', 'Bukhari 44', 'Bukhari 44a', 'Muslim 100', 'Bukhari 100',
                      'Muslim 17', 'Riyad as-Salihin 67'):
            self.assertEqual(self.case.call(query, include_commentary=True)['matched'], 0, query)
        for query in ('Bukhari no. ٤٤b', 'صحيح مسلم رقم ۹۹'):
            self.assertEqual(self.case.call(query)['matched'], 1, query)
        record['number'] = {'in_book': '77', 'numbering_scheme': 'as_cited_in_source'}
        self.case.save()
        self.assertEqual(self.case.call('Bukhari 77')['matched'], 1)
        record['number']['sequence_is_hadith_number'] = False
        self.case.save()
        self.assertEqual(self.case.call('Bukhari 77')['matched'], 0)
        self.assertIn('Number in source 77', reader.number_label(record))
        self.assertNotIn('Number in collection', reader.number_label(record))
        self.assertIn('Source number: 77', searcher.format_results(self.case.call('')))

    def test_volume_page_queries_are_not_misparsed_as_hadith_number_clauses(self):
        for query in ('Bukhari 1/23', 'Muslim 1:23', 'Bukhari 1-23', 'Ahmad (1/23)'):
            self.assertEqual(citations.split_citation_query(searcher._fold(query))[0], [], query)
        self.assertEqual(citations.split_citation_query(searcher._fold('AbuDawud5092')),
                         ([('abu-dawud', '5092')], ''))

    def test_persian_structured_citations_keep_book_number_scope_and_source_bytes(self):
        record = self.records[0]
        record.update(language='fa', source_language_code='fa', book_key='bukhari',
                      text_translation='TEST آزمایش كوتاه براي جست\u200cوجو')
        record['counterparts'] = {'arabic': None, 'english': None}
        record['number'] = {'in_book': '1907', 'canonical': None,
                            'numbering_system': 'Source-local numbering; not canonical Bukhari numbering'}
        record['references'] = {'items': persian_structured_references()}
        before = copy.deepcopy(record)
        self.case.records = [record]
        self.case.save()
        self.assertEqual(citations.record_citation_pairs(record), {
            ('bukhari', '1'), ('bukhari', '44b'), ('bukhari', '55'),
            ('muslim', '1907'), ('malik', '12')})
        for query in ('صحيح البخاري حديث ١', 'صحیح البخاری حدیث ۱',
                      'صحیح البخا\u200cری رقم ۱', 'Bukhari 44b', 'Bukhari 55',
                      'صحيح مسلم رقم ١٩٠٧', 'صحیح مسلم حدیث ۱۹۰۷',
                      'موطأ مالک ۱۲', 'آزمایش کوتاه برای جستوجو صحیح البخاری رقم ۱'):
            with self.subTest(query=query):
                result = self.case.call(query)
                self.assertEqual(result['matched'], 1)
                self.assertEqual(result['results'][0]['text_translation'], before['text_translation'])
        for query in ('Bukhari 1907', 'Muslim 1', 'Bukhari 12', 'Malik 1907', 'Bukhari 66',
                      'Bukhari 91', 'Bukhari 92', 'Bukhari 93', 'Bukhari 94', 'Bukhari 95',
                      'Muslim 96', 'Muslim 97', 'Muslim 98', 'Muslim 99', 'Bukhari 99'):
            self.assertEqual(self.case.call(query)['matched'], 0, query)
        self.assertEqual(record, before)
        self.assertIn('Source number: 1907', searcher.format_results(self.case.call('')))

    def test_publisher_collection_names_are_complete_and_distinct(self):
        for aliases, key, english, arabic in PROVIDER_BOOKS:
            for name in (english, arabic, *aliases):
                with self.subTest(key=key, name=name):
                    self.assertEqual(citations.collection_key(name), key)
                    self.assertEqual(citations.split_citation_query(searcher._fold(name + ' no.9963')),
                                     ([(key, '9963')], ''))
        record = self.records[0]
        record['counterparts']['english']['references'] = [
            {'book_key': key, 'collection': english, 'collection_ar': arabic, 'number': '9963'}
            for _, key, english, arabic in PROVIDER_BOOKS
            if key in ('nasai-kubra', 'tabarani-saghir', 'ibn-khuzaymah')]
        self.case.records = [record]
        self.case.save()
        for query in ("Al-Sunan al-Kubra by al-Nasa'i no.9963", 'السنن الكبرى للنسائي رقم9963',
                      'Al-Mujam al-Saghir by al-Tabarani 9963', 'Sahih Ibn Khuzaymah 9963'):
            self.assertEqual(self.case.call(query)['matched'], 1, query)
        for query in ("Sunan al-Nasa'i 9963", 'سنن النسائي 9963', 'Al-Mujam al-Kabir by al-Tabarani 9963',
                      'Al-Mujam al-Awsat by al-Tabarani 9963', 'Tabarani 9963', 'Sahih Ibn Hibban 9963'):
            self.assertEqual(self.case.call(query)['matched'], 0, query)

    def test_disposable_cache_migrates_from_previous_query_semantics(self):
        result = self.case.call('Bukhari 1907')
        receipt = self.case.root / (result['cache']['path'] + '.json')
        # Locate the receipt by the actual sibling filename used by the cache.
        if not receipt.exists():
            receipt = next((self.case.root / '.cache').glob('*.json'))
        data = json.loads(receipt.read_text())
        data['version'] = '5:literal-substrings:arabic-digits:scoped-counterparts:current-origin'
        receipt.write_text(json.dumps(data))
        migrated = self.case.call('Bukhari 1907', limit=0)
        self.assertTrue(migrated['cache']['rebuilt'])
        self.assertEqual(migrated['matched'], 2)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser/CLI citation parity')
    def test_browser_and_cli_parse_and_match_same_pairs(self):
        self.records[0]['references']['items'] = [
            {'book_key': 'muslim', 'number': '17', 'scope': 'main_quote',
             'numbering_scheme': 'number_within_source_named_book'},
            {'book_key': 'riyad-as-salihin', 'number': '67', 'scope': 'main_quote',
             'numbering_scheme': 'selected_Vietnamese_abridgment_number_not_canonical_Riyad_number'},
            {'book_key': 'bukhari', 'number': '44b', 'scope': 'variant'},
            {'book_key': 'bukhari', 'number': '88', 'scope': 'commentary'},
            {'book_key': 'nasai-kubra', 'collection': "Al-Sunan al-Kubra by al-Nasa'i",
             'collection_ar': 'السنن الكبرى للنسائي', 'number': '9963'},
            {'book_key': 'tabarani-saghir', 'collection': 'Al-Mujam al-Saghir by al-Tabarani',
             'collection_ar': 'المعجم الصغير للطبراني', 'number': '9963'},
            {'book_key': 'ibn-khuzaymah', 'collection': 'Sahih Ibn Khuzaymah', 'number': '9963'},
        ]
        self.records[0]['references']['items'].extend(persian_structured_references())
        self.records[1]['book_key'] = 'bukhari'
        self.records[1]['number'] = {'in_book': '77', 'numbering_system': 'Source-local numbering'}
        self.case.save()
        template = (Path(__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        filter_function = template.split('function applyFilters(){', 1)[1].split('$("query").addEventListener', 1)[0]
        program = '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=input.records,names={},state={matches:[]},fields={query:{value:''},'language-filter':{value:''},'book-filter':{value:''},'source-filter':{value:''},'origin-filter':{value:''},'include-commentary':{checked:false}};
const $=id=>fields[id],render=()=>{};
const valueText = ''' + helpers + '''\nfunction applyFilters(){''' + filter_function + '''
const results=input.queries.map(query=>{fields.query.value=query;applyFilters();return {parsed:splitCitationQuery(fold(query,false)),ids:state.matches.map(i=>records[i].id)};});
process.stdout.write(JSON.stringify({aliases:citationAliases,keyAliases:citationKeyAliases,results,numberLabels:records.map(numberLabel)}));'''
        queries = ['Bukhari 1907', 'Sahih al-Bukhari no. ١٩٠٧', 'صحيح البخاري رقم ۱۹۰۷',
                   'reward Bukhari 1907', 'Bukhari 1 Muslim 1907', 'Bukhari 1907 Muslim 1',
                   'Bukhari 1/23', 'AbuDawud5092', "Jami' at-Tirmidhi no. 123", 'سنن أبي داود رقم ١٢٣a',
                   'سنن النسائي 123', 'Sunan Ibn Majah 123', 'موطأ مالك 123', 'مسند أحمد 123',
                   'رياض الصالحين 123', 'Hisn al-Muslim 123', 'الأدب المفرد 123',
                   'Muslim 17', 'Riyad as-Salihin 67', 'Bukhari 77', 'Bukhari 88',
                   'Bukhari ٤٤b', 'Bukhari 44', "Al-Sunan al-Kubra by al-Nasa'i no.9963",
                   'السنن الكبرى للنسائي رقم9963', "Sunan al-Nasa'i 9963", 'سنن النسائي 9963',
                   'Al-Mujam al-Saghir by al-Tabarani 9963', 'المعجم الصغير للطبراني 9963',
                   'Al-Mujam al-Kabir by al-Tabarani 9963', 'Al-Mujam al-Awsat by al-Tabarani 9963',
                   'Tabarani 9963', 'Sahih Ibn Khuzaymah 9963', 'Sahih Ibn Hibban 9963',
                   'صحیح البخاری حدیث ۱', 'صحیح البخا\u200cری رقم ۱', 'صحیح مسلم حدیث ۱۹۰۷',
                   'موطأ مالک ۱۲', 'موطأ مالك رقم ١٢', 'Bukhari 55', 'Bukhari 66',
                   'Bukhari 91', 'Bukhari 92', 'Bukhari 93', 'Bukhari 94', 'Bukhari 95',
                   'Muslim 96', 'Muslim 97', 'Muslim 98', 'Muslim 99', 'Bukhari 99']
        output = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'records': self.records, 'queries': queries}),
                                text=True, encoding='utf-8', capture_output=True, check=True)
        actual = json.loads(output.stdout)
        self.assertEqual(actual['aliases'], [list(row) for row in citations.COLLECTION_ALIASES])
        self.assertEqual(actual['keyAliases'], citations.KEY_ALIASES)
        self.assertEqual(actual['numberLabels'], [reader.number_label(record) for record in self.records])
        for query, result in zip(queries, actual['results']):
            with self.subTest(query=query):
                pairs, remaining = citations.split_citation_query(searcher._fold(query, join_cjk=False))
                self.assertEqual(result['parsed'], {'pairs': [key + ':' + number for key, number in pairs], 'text': remaining})
                self.assertEqual(result['ids'], [item['id'] for item in self.case.call(query, limit=10)['results']])


if __name__ == '__main__':
    unittest.main()
