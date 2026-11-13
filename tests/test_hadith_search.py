"""Synthetic search fixtures only: no fixture passage is religious source text."""
import copy
from contextlib import closing
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from test_reader import READER_SNAPSHOT_JS, READER_FILTER_HARNESS_JS
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/hadith_search.py'
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location('flat_hadith_search', SCRIPT)
searcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(searcher)


class HadithSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'original').mkdir()
        self.original = self.root / 'original/source.bin'
        self.original.write_bytes(b'SYNTHETIC ORIGINAL SOURCE ASSET\n')
        (self.root / 'original/records.json').write_text('[{"fixture": true}]\n', encoding='utf-8')
        first = self.fixture('occurrence-ja-1')
        second = self.fixture('occurrence-ja-2')
        second['edition'] = 'snapshot-b'
        second['source_id'] = 'fixture-private'
        second['translation_provenance'].update(origin='human_published', label='Fixture named human translation', ai_translation=False)
        second['translator']['name'] = 'FIXTURE TRANSLATOR'
        third = self.fixture('occurrence-zh')
        third.update(language='zh-CN', source_language_code='zh', provider_entry_id='8', book_key='fixture-book',
                     title=None, text_arabic=None, text_translation='这是合成\n示例，测试连续中文子字符串。')
        third['topic_tags'] = []
        fourth = self.fixture('occurrence-missing-translation')
        fourth.update(language='pt', source_language_code='pt', provider_entry_id='9', text_translation=None)
        fourth['title'] = None
        fourth['translation_provenance'].update(origin='ai_generated', label='Fixture AI translation', ai_translation=True)
        self.records = [first, second, third, fourth]
        self.save()

    def fixture(self, occurrence_id):
        return {
            'id': occurrence_id, 'language': 'ja', 'source_language_code': 'ja',
            'book_key': 'hadeethenc', 'edition': 'snapshot-a', 'source_id': 'fixture-public',
            'provider_entry_id': '7', 'title': '日本語の合成タイトル',
            'text_arabic': 'نَصٌّ تَجْرِيبِيٌّ',
            'text_translation': '信仰について学び、礼拝を守ります。Ａｌｐｈａ 100% a_b literal\\slash',
            'number': {'in_book': '12', 'canonical': None},
            'narrator': {'name': 'FIXTURE NARRATOR', 'verbatim': 'FIXTURE REPORTER'},
            'source': {
                'name': 'Synthetic source', 'url': 'https://example.invalid/source',
                'record_url': 'https://example.invalid/record/7',
                'original_file': 'original/source.bin',
                'sha256': hashlib.sha256(self.original.read_bytes()).hexdigest(),
                'record_locator': {'path': 'original/records.json', 'json_pointer': '/0'},
                'format': 'json',
            },
            'translator': {'name': None, 'evidence': None},
            'translation_provenance': {
                'origin': 'unknown', 'label': 'Method not supplied', 'basis': 'synthetic fixture',
                'human_involvement': 'not stated', 'ai_translation': 'unknown', 'evidence_ids': [],
            },
            'topic_tags': [{'id': 'topic-belief', 'label': '信仰', 'path': ['合成分類', '信仰']}],
            'editorial_tags': ['source:fixture', 'review:pending'],
            'source_headings': ['合成見出し'],
            'review': {'status': 'fixture_review_pending', 'issues': ['synthetic_flag'],
                       'independent_pro_qc': 'pending', 'release_status': 'unreviewed_snapshot'},
            'commentary': {'arabic': None, 'translation': 'commentary-only-token'},
            'footnotes': [{'text': 'footnote-only-token'}],
            'references': {'translation': None, 'arabic': None},
            'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None},
        }

    def save(self, *, shards=False, whole=True):
        lines = [(json.dumps(r, ensure_ascii=False) + '\n').encode('utf-8') for r in self.records]
        raw = b''.join(lines)
        (self.root / 'search').mkdir(exist_ok=True)
        path = self.root / 'search/records.jsonl'
        if whole:
            path.write_bytes(raw)
        else:
            path.unlink(missing_ok=True)
        search = {'records_path': 'search/records.jsonl', 'records_sha256': hashlib.sha256(raw).hexdigest(),
                  'count': len(self.records)}
        if shards:
            search['shards'] = []
            for i, chunk in enumerate((lines[:2], lines[2:]), 1):
                shard = b''.join(chunk)
                relative = 'search/shard-' + str(i) + '.jsonl'
                (self.root / relative).write_bytes(shard)
                search['shards'].append({'path': relative, 'sha256': hashlib.sha256(shard).hexdigest(),
                                         'count': len(chunk), 'bytes': len(shard)})
        catalog = {'schema': 'fixture-materials', 'search': search, 'datasets': [{'id': 'synthetic'}]}
        (self.root / 'catalog').mkdir(exist_ok=True)
        (self.root / 'catalog/materials.json').write_text(json.dumps(catalog), encoding='utf-8')

    def call(self, query='', **kwargs):
        return searcher.search(self.root, query, **kwargs)

    def test_optional_grading_version_and_digest_metadata_survive_json_results(self):
        original = self.records[0]
        original['grading'] = {'status': 'synthetic_source_claim', 'named_assessor': None}
        original['related_versions'] = ['synthetic-other-snapshot']
        original['canonical_record_sha256'] = '0' * 64
        original['source_occurrence_group'] = {'synthetic': True}
        original['benefits'] = {'translation': ['synthetic benefit']}
        self.save()
        result = self.call(entry_id=original['id'])['results'][0]
        for key in ('grading', 'related_versions', 'canonical_record_sha256', 'source_occurrence_group'):
            self.assertEqual(result[key], original[key])
        self.assertNotIn('benefits', result)
        complete = self.call(entry_id=original['id'], include_commentary=True)['results'][0]
        for key, value in original.items():
            self.assertEqual(complete[key], value)

    def test_japanese_chinese_short_and_long_substrings_preserve_text(self):
        for query, expected in [('礼拝', 2), ('仰について', 2), ('合成示例', 1), ('中文', 1), ('文子字符串', 1), ('测试 字符串', 1)]:
            with self.subTest(query=query):
                result = self.call(query)
                self.assertEqual(result['matched'], expected)
                for item in result['results']:
                    original = next(r for r in self.records if r['id'] == item['id'])
                    self.assertEqual(item['text_translation'], original['text_translation'])
        self.assertEqual(self.call('alpha')['matched'], 2)

    def test_arabic_diacritics_and_tatweel_are_search_keys_only(self):
        original = self.records[0]['text_arabic']
        for query in ['نص تجريبي', 'نَصٌّ', 'تجـريبي']:
            result = self.call(query)
            self.assertEqual(result['matched'], 3)
            self.assertEqual(result['results'][0]['text_arabic'], original)

    def test_exact_filters_ids_tags_origin_and_duplicate_versions(self):
        self.assertEqual(self.call(entry_id='7')['matched'], 2)
        self.assertEqual(self.call(entry_id='occurrence-ja-1')['matched'], 1)
        self.assertEqual(self.call(entry_id='occurrence-ja')['matched'], 0)
        self.assertEqual(self.call(entry_id='07')['matched'], 0)
        self.assertEqual(self.call(language='zh')['results'][0]['language'], 'zh-CN')
        self.assertEqual(self.call(book='fixture-book')['matched'], 1)
        self.assertEqual(self.call(source='fixture-private')['matched'], 1)
        self.assertEqual(self.call(translation_origin='human_published')['matched'], 1)
        for tag, count in [('topic-belief', 3), ('信仰', 3), ('review:pending', 4), ('review', 0)]:
            self.assertEqual(self.call(tag=tag)['matched'], count)
        result = self.call(language='ja', source='fixture-private', entry_id='7', tag='信仰', translation_origin='human_published')
        self.assertEqual(result['matched'], 1)
        self.assertEqual(result['results'][0]['id'], 'occurrence-ja-2')
        # Distinct versions with the same text and provider ID remain separate.
        result = self.call(entry_id='7')
        self.assertEqual([r['edition'] for r in result['results']], ['snapshot-a', 'snapshot-b'])

    def test_reference_translator_source_and_identity_metadata_are_searchable(self):
        self.records[1]['references']['translation'] = 'SYNTHETIC BIBLIOGRAPHY ZETA-321'
        self.records[1]['source']['name'] = 'Distinct source publication'
        self.records[1]['translator']['evidence'] = 'Named on synthetic title page'
        self.save()
        for query in ('ZETA-321', 'FIXTURE TRANSLATOR', 'Distinct source publication',
                      'synthetic title page', 'occurrence-ja-2', 'snapshot-b', 'fixture-private'):
            with self.subTest(query=query):
                result = self.call(query)
                self.assertEqual(result['matched'], 1)
                self.assertEqual(result['results'][0]['id'], 'occurrence-ja-2')
                self.assertEqual(result['results'][0]['references'], self.records[1]['references'])

    def test_current_origin_categories_and_historical_evidence_filters(self):
        # Owner confirmation overrides historical AI metadata for display/filtering.
        self.records[0]['translation_provenance'].update(
            origin='legacy_source_history', ai_translation=True,
            current_policy={'classification': 'unknown', 'basis': 'TEST owner decision'})
        self.records[3]['translation_provenance']['current_policy'] = {
            'classification': 'human', 'basis': 'TEST owner-confirmed source'}
        original = copy.deepcopy(self.records)
        self.save()
        for engine in ('trigram', 'like'):
            with self.subTest(engine=engine):
                context = mock.patch.object(searcher, '_create_fts', return_value='like') if engine == 'like' else mock.patch.object(searcher, '_create_fts', wraps=searcher._create_fts)
                with context:
                    unknown = self.call(translation_origin='unknown', database=':memory:')
                    self.assertEqual([x['id'] for x in unknown['results']], ['occurrence-ja-1', 'occurrence-zh'])
                    self.assertIn('Translation origin: Unknown', searcher.format_results(unknown))
                    self.assertIn('Preserved source AI translation: true', searcher.format_results(unknown))
                    human = self.call(translation_origin='human', database=':memory:')
                    self.assertEqual([x['id'] for x in human['results']], ['occurrence-ja-2', 'occurrence-missing-translation'])
                    self.assertEqual(self.call(translation_origin='ai', database=':memory:')['matched'], 0)
                    self.assertEqual(self.call(translation_origin='legacy_source_history', database=':memory:')['matched'], 1)
                    self.assertEqual(self.call(translation_origin='human_published', database=':memory:')['matched'], 1)
                    self.assertEqual(self.call(translation_origin='ai_generated', database=':memory:')['matched'], 1)
        self.assertEqual(self.records, original)

    def test_nested_source_context_is_opt_in_without_losing_citation_search(self):
        record = self.records[0]
        record['source']['original_metadata'] = {
            'original_context': 'TEST-LESSON-CONTEXT-ONLY',
            'historical_metadata': {'selected_parent': {
                'full_explanation': 'TEST-PARENT-EXPLANATION-ONLY',
                'full_translation': 'TEST-PARENT-WORDS-OUTSIDE-QUOTE',
            }},
        }
        record['narrator']['source_context'] = 'TEST-NARRATOR-CONTEXT-ONLY'
        record['number']['in_book'] = 'TEST-2311'
        record['references']['items'] = [{'collection': 'TEST COLLECTION', 'number': 'TEST-2311', 'scope': 'main_quote'}]
        original = copy.deepcopy(record)
        self.save()
        for query in ('TEST-LESSON-CONTEXT-ONLY', 'TEST-PARENT-EXPLANATION-ONLY',
                      'TEST-PARENT-WORDS-OUTSIDE-QUOTE', 'TEST-NARRATOR-CONTEXT-ONLY'):
            with self.subTest(query=query):
                self.assertEqual(self.call(query)['matched'], 0)
                included = self.call(query, include_commentary=True)
                self.assertEqual([x['id'] for x in included['results']], [record['id']])
                self.assertEqual(included['results'][0]['source'], original['source'])
        self.assertEqual(self.call('TEST COLLECTION TEST-2311')['matched'], 1)
        self.assertEqual(self.call('FIXTURE NARRATOR', entry_id=record['id'])['matched'], 1)
        self.assertEqual(self.call('Synthetic source', entry_id=record['id'])['matched'], 1)
        self.assertEqual(record, original)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for reader/search parity')
    def test_nested_context_and_current_origin_match_reader_behavior(self):
        first = self.records[0]
        first['source']['original_metadata'] = {
            'original_context': 'TEST surrounding lesson text',
            'historical_metadata': {'selected_parent': {'full_explanation': 'TEST parent explanation'}},
        }
        first['translation_provenance'].update(origin='legacy_source_history', ai_translation=True,
            current_policy={'classification': 'unknown', 'basis': 'TEST'})
        first['references']['items'] = [{'collection': 'TEST-COLLECTION', 'number': 'TEST-2311'}]
        self.save()
        queries = [
            {'query': 'TEST surrounding', 'commentary': False, 'origin': ''},
            {'query': 'TEST surrounding', 'commentary': True, 'origin': ''},
            {'query': 'TEST parent explanation', 'commentary': False, 'origin': ''},
            {'query': 'TEST parent explanation', 'commentary': True, 'origin': 'unknown'},
            {'query': 'TEST-COLLECTION TEST-2311', 'commentary': False, 'origin': 'unknown'},
            {'query': '', 'commentary': False, 'origin': 'unknown'},
            {'query': '', 'commentary': False, 'origin': 'human'},
            {'query': '', 'commentary': False, 'origin': 'ai'},
        ]
        expected = [[row['id'] for row in self.call(item['query'],
                    include_commentary=item['commentary'], translation_origin=item['origin'] or None)['results']]
                    for item in queries]
        template = (SCRIPT.parents[1] / 'reader/template.html').read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        filtering = template.split('function applyFilters(){', 1)[1].split('$("query").addEventListener', 1)[0]
        program = READER_SNAPSHOT_JS + '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=input.records,names={},state={matches:[]},fields={query:{value:''},'language-filter':{value:''},'book-filter':{value:''},'source-filter':{value:''},'origin-filter':{value:''},'include-commentary':{checked:false}};
const $=id=>fields[id],render=()=>{};
const valueText = ''' + helpers + READER_FILTER_HARNESS_JS + '''\nasync function applyFilters(){''' + filtering + '''
(async()=>{
const results=[];
for(const item of input.queries){fields.query.value=item.query;fields['origin-filter'].value=item.origin;fields['include-commentary'].checked=item.commentary;await applyFilters();results.push(state.matches.map(index=>records[index].id));}
process.stdout.write(JSON.stringify({results,records}));
})().catch(error=>{process.stderr.write(String(error.stack || error));process.exitCode=1;});'''
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'records': self.records, 'queries': queries}, ensure_ascii=False),
                                text=True, encoding='utf-8', capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual['results'], expected)
        self.assertEqual(actual['records'], self.records)

    def test_sql_fts_and_like_input_is_literal(self):
        for query in ['" OR 1=1 --', 'alpha OR missing', '%not-present%', '_not-present_', '"*) OR *']:
            self.assertEqual(self.call(query)['matched'], 0, query)
        self.assertEqual(self.call('100%')['matched'], 2)
        self.assertEqual(self.call('a_b')['matched'], 2)
        self.assertEqual(self.call('literal\\slash')['matched'], 2)
        self.assertEqual(self.call(source="fixture-public' OR 1=1 --")['matched'], 0)
        self.assertEqual(self.call(tag="review:pending' OR 1=1 --")['matched'], 0)

    def test_commentary_and_footnotes_are_opt_in(self):
        for query in ['commentary-only-token', 'footnote-only-token']:
            self.assertEqual(self.call(query)['matched'], 0)
            result = self.call(query, include_commentary=True)
            self.assertEqual(result['matched'], 4)
            self.assertEqual(result['results'][0]['commentary'], self.records[0]['commentary'])
            self.assertEqual(result['results'][0]['footnotes'], self.records[0]['footnotes'])
        result = self.call('礼拝')
        self.assertNotIn('commentary', result['results'][0])
        self.assertNotIn('footnotes', result['results'][0])

    def test_decoded_benefits_are_supplementary_and_preserved(self):
        supplied = {'arabic': ['فَائِدَةٌ تَجْرِيبِيَّةٌ فَقَطْ'],
                    'translation': ['benefits-only-marker', 'SECOND BENEFIT FIXTURE']}
        self.records[0]['benefits'] = supplied
        self.save()
        self.assertEqual(self.call('benefits-only-marker')['matched'], 0)
        result = self.call('benefits-only-marker', include_commentary=True)
        self.assertEqual(result['matched'], 1)
        self.assertEqual(result['results'][0]['benefits'], supplied)
        self.assertIn('SECOND BENEFIT FIXTURE', searcher.format_results(result))
        self.assertEqual(self.call('فائدة تجريبية فقط', include_commentary=True)['matched'], 1)
        self.assertNotIn('benefits', self.call(entry_id='occurrence-ja-1')['results'][0])

    def test_private_intake_null_benefits_search_and_commentary_remain_exact(self):
        # Newly supplied PDF records have no approved Arabic/provider ID and
        # explicitly null benefits. This matches their real projection shape.
        record = self.records[0]
        record.update(book_key='muslim', source_id='fixture-new-intake',
                      provider_entry_id=None, text_arabic=None, benefits=None)
        record['review'].update(release_status='private_candidate',
                                release_eligible=False, certified_release_eligible=False)
        self.save()
        result = self.call('礼拝', source='fixture-new-intake')
        self.assertEqual((result['matched'], result['shown']), (1, 1))
        self.assertEqual(result['results'][0]['text_translation'], record['text_translation'])
        self.assertIsNone(result['results'][0]['text_arabic'])
        self.assertNotIn('benefits', result['results'][0])
        complete = self.call('commentary-only-token', source='fixture-new-intake',
                             include_commentary=True)
        hit = complete['results'][0]
        self.assertEqual(complete['matched'], 1)
        self.assertIn('benefits', hit)
        self.assertIsNone(hit['benefits'])
        self.assertEqual(hit['commentary'], record['commentary'])
        self.assertEqual(hit['review'], record['review'])
        self.assertIn('commentary-only-token', searcher.format_results(complete))

    def test_like_fallback_handles_same_unicode_queries(self):
        with mock.patch.object(searcher, '_create_fts', return_value='like'):
            for query, expected in [('合成示例', 1), ('礼拝', 2), ('نص تجريبي', 3), ('100%', 2), ('a_b', 2)]:
                result = self.call(query, database=':memory:')
                self.assertEqual(result['matched'], expected)
                self.assertEqual(result['cache']['engine'], 'like')

    def test_input_hash_verified_even_on_warm_cache_and_limit_zero(self):
        self.call('alpha')
        path = self.root / 'search/records.jsonl'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch|Blank lines'):
            self.call('alpha', limit=0)

    def test_updated_verified_stream_refreshes_stale_cache(self):
        first = self.call('alpha')
        self.assertTrue(first['cache']['rebuilt'])
        second = self.call('alpha')
        self.assertFalse(second['cache']['rebuilt'])
        self.records[0]['text_translation'] += ' fresh-cache-marker'
        self.save()
        updated = self.call('fresh-cache-marker')
        self.assertTrue(updated['cache']['rebuilt'])
        self.assertEqual(updated['matched'], 1)
        self.assertNotEqual(updated['integrity']['records_sha256'], first['integrity']['records_sha256'])

    def test_connection_initialization_error_closes_the_database(self):
        class FailingConnection(sqlite3.Connection):
            def execute(self, sql, *args, **kwargs):
                if sql == 'PRAGMA foreign_keys=ON':
                    raise sqlite3.OperationalError('TEST connection initialization failure')
                return super().execute(sql, *args, **kwargs)

        database = self.root / 'initialization-failure.sqlite'
        connection = sqlite3.connect(database, factory=FailingConnection)
        self.addCleanup(connection.close)
        with mock.patch.object(searcher.sqlite3, 'connect', return_value=connection):
            with self.assertRaisesRegex(sqlite3.OperationalError, 'TEST connection initialization failure'):
                searcher._connect(database)
        with self.assertRaisesRegex(sqlite3.ProgrammingError, 'closed database'):
            connection.execute('SELECT 1')
        database.unlink()

    def test_modified_cache_is_discarded_and_results_remain_original(self):
        self.call('alpha')
        database = self.root / '.cache/hadith-search.sqlite'
        # A connection's transaction context commits, but does not close its
        # file handle; close it before the cache is replaced on Windows.
        with closing(sqlite3.connect(database)) as connection:
            with connection:
                connection.execute("UPDATE records SET body = 'tampered-cache-only' WHERE line=1")
        result = self.call('alpha')
        self.assertTrue(result['cache']['rebuilt'])
        self.assertEqual(result['matched'], 2)
        self.assertEqual(result['results'][0]['text_translation'], self.records[0]['text_translation'])
        self.assertEqual(self.call('tampered-cache-only')['matched'], 0)

    def test_sharded_only_stream_verifies_individual_and_aggregate_bytes(self):
        self.save(shards=True, whole=False)
        result = self.call('alpha')
        self.assertEqual(result['matched'], 2)
        self.assertEqual(result['integrity']['input_mode'], 'shards')
        self.assertEqual(result['integrity']['input_files_verified'], 2)
        catalog_path = self.root / 'catalog/materials.json'
        catalog = json.loads(catalog_path.read_text())
        catalog['search']['records_sha256'] = '0' * 64
        catalog_path.write_text(json.dumps(catalog))
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch for complete'):
            self.call()

    def test_shard_tamper_and_count_fail_before_cache_use(self):
        self.save(shards=True, whole=False)
        self.call()
        shard = self.root / 'search/shard-2.jsonl'
        shard.write_bytes(shard.read_bytes().replace('中文'.encode(), '改文'.encode()))
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch for search shard'):
            self.call()
        self.save(shards=True, whole=False)
        catalog_path = self.root / 'catalog/materials.json'
        catalog = json.loads(catalog_path.read_text())
        catalog['search']['shards'][0]['count'] += 1
        catalog_path.write_text(json.dumps(catalog))
        with self.assertRaisesRegex(ValueError, 'Byte/count mismatch'):
            self.call()

    def test_present_corrupt_whole_stream_does_not_fall_back_to_shards(self):
        self.save(shards=True, whole=True)
        path = self.root / 'search/records.jsonl'
        path.write_bytes(path.read_bytes().replace(b'Alpha', b'Other') + b' ')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch|Blank lines'):
            self.call()

    def test_unsafe_source_stream_and_cache_paths_are_rejected(self):
        self.records[0]['source']['original_file'] = '../outside.bin'
        self.save()
        with self.assertRaisesRegex(ValueError, 'Unsafe local path'):
            self.call()
        self.records[0]['source']['original_file'] = 'original/source.bin'
        self.save()
        with self.assertRaisesRegex(ValueError, 'cache must be under'):
            self.call(database='search/records.jsonl')
        catalog_path = self.root / 'catalog/materials.json'
        catalog = json.loads(catalog_path.read_text())
        catalog['search']['records_path'] = '../outside.jsonl'
        catalog_path.write_text(json.dumps(catalog))
        with self.assertRaisesRegex(ValueError, 'Unsafe local path'):
            self.call()

    def test_result_original_asset_tamper_is_detected_on_warm_cache(self):
        self.call('alpha')
        self.original.write_bytes(b'ALTERED ORIGINAL SOURCE')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch for result original source'):
            self.call('alpha')

    def test_human_output_shows_text_url_translator_origin_and_pending_review(self):
        result = self.call(entry_id='occurrence-ja-2')
        text = searcher.format_results(result)
        self.assertIn(self.records[1]['text_translation'], text)
        self.assertIn('https://example.invalid/record/7', text)
        self.assertIn('FIXTURE TRANSLATOR', text)
        self.assertIn('human_published', text)
        self.assertIn('AI translation: false', text)
        self.assertIn('independent Pro QC: pending', text)
        self.assertNotIn('record_locator', text)
        self.assertNotIn('commentary-only-token', text)

    def test_human_output_distinguishes_current_waiver_from_historical_flags(self):
        review = self.records[0]['review']
        review['current_policy'] = {
            'label': 'No separate bank review required — owner decision',
            'separate_bank_review_required': False,
            'independent_review_performed': False,
        }
        self.save()
        result = self.call(entry_id='occurrence-ja-1')
        self.assertEqual(result['results'][0]['review'], review)
        text = searcher.format_results(result)
        self.assertIn('Current review policy: No separate bank review required — owner decision', text)
        self.assertIn('Historical import review: fixture_review_pending', text)
        self.assertIn('independent Pro QC: pending', text)
        self.assertIn('synthetic_flag', text)

    def test_cli_json_and_limits(self):
        completed = subprocess.run([sys.executable, str(SCRIPT), '礼拝', '--root', str(self.root),
                                    '--language', 'ja', '--limit', '1', '--json'],
                                   capture_output=True, text=True, encoding='utf-8', check=True,
                                   env={**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
        value = json.loads(completed.stdout)
        self.assertEqual((value['matched'], value['shown']), (2, 1))
        self.assertEqual(self.call(limit=0)['results'], [])
        with self.assertRaisesRegex(ValueError, 'Limit'):
            self.call(limit=-1)


if __name__ == '__main__':
    unittest.main()
