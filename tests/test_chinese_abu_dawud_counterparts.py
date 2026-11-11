"""Synthetic builder contracts; no fixture is a religious source quotation."""
from contextlib import redirect_stdout
import gzip
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_chinese_abu_dawud_counterparts as builder
from counterpart_references import parse_provider_references
from reviewed_counterparts import ReviewedCounterpartResolver


ARABIC = 'نص اصطناعي لاختبار البرنامج فقط وليس حديثا'
ENGLISH = 'TEST publisher translation; this is not a religious quotation.'


class ChineseCounterpartBuilderContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / builder.BASE
        self.records = [
            {'id': 'TEST-Chinese-source:' + str(index),
             'text': {'translation': 'TEST 中文来源记录 ' + str(index)}}
            for index in range(2827)
        ] + [{'id': builder.UNRESOLVED_ID,
              'text': {'translation': 'TEST 尚未确认的中文来源记录'}}]
        self.source_path = 'TEST-input/records.jsonl'
        source_bytes = ''.join(json.dumps(row, ensure_ascii=False) + '\n'
                               for row in self.records).encode('utf-8')
        self.put(self.source_path, source_bytes)
        self.put('TEST-input/original.doc', b'TEST original binary source')
        self.before = source_bytes
        raw_arabic = json.dumps({'hadiths': [
            {'hadithnumber': 1, 'text': ARABIC},
            {'hadithnumber': 2319, 'text': ARABIC + ' TEST second entry'},
        ]}, ensure_ascii=False).encode('utf-8')
        self.put(builder.BASE + '/raw/ara-abudawud.json.gz', gzip.compress(raw_arabic))
        capture_path = builder.BASE + '/raw/supplements/907.capture.json'
        capture = {'id': '907', 'arabic': ARABIC + '\nGrade: TEST page footer'}
        self.json(capture_path, capture)
        self.json(builder.BASE + '/raw/supplements/907.json', {
            'id': '907', 'arabic': ARABIC, 'extraction': {
                'source_character_span': [0, len(ARABIC)],
                'raw_capture_sha256': builder.digest((self.root / capture_path).read_bytes())}})
        self.json(builder.BASE + '/raw/supplements/907b.json', {
            'id': '907b', 'arabic': ARABIC + ' TEST separate entry'})
        self.english_db = 'TEST-input/en.sqlite'
        self.arabic_db = 'TEST-input/ar.sqlite'
        self.publisher_bibliography = 'سنن أبي داود (2).'
        self.database(self.english_db,
            'CREATE TABLE hadeeths (id INTEGER, hadeeth TEXT, hadeeth_ar TEXT, ar_version INTEGER)',
            (100, ENGLISH, ARABIC, 1))
        self.database(self.arabic_db,
            'CREATE TABLE hadeeths (id INTEGER, hadeeth TEXT, version INTEGER, reference TEXT, attribution TEXT)',
            (100, ARABIC, 1, self.publisher_bibliography, 'رواه أبو داود'))
        self.provenance = {
            'original_source': {'records_path': self.source_path,
                'records_sha256': builder.digest(source_bytes),
                'original_file': 'TEST-input/original.doc',
                'sha256': builder.digest(b'TEST original binary source')},
            'arabic_source': {'raw_sha256': builder.digest(raw_arabic), 'revision': 'TEST-pinned'},
            'authorized_english': {'english_database': self.english_db,
                'english_database_sha256': builder.digest((self.root / self.english_db).read_bytes()),
                'arabic_database': self.arabic_db,
                'arabic_database_sha256': builder.digest((self.root / self.arabic_db).read_bytes()),
                'english_version': 'TEST-version'},
            'publication': {'authorized': True, 'basis': 'TEST fixture only'},
        }
        self.json(builder.BASE + '/provenance.json', self.provenance)
        reviews = []
        for index, source in enumerate(self.records[:-1]):
            number = 2319 if index == 2 else 1
            target = ARABIC + ' TEST second entry' if number == 2319 else ARABIC
            reviews.append({'chinese_record_id': source['id'], 'canonical_number': number,
                'source_text_sha256': builder.text_hash(source['text']['translation']),
                'arabic_target_sha256': builder.text_hash(target),
                'source_evidence_substring': source['text']['translation'],
                'rationale': 'TEST independent content-comparison evidence',
                'reviewer': 'TEST Arabic alignment reviewer', 'human_review': False,
                'review_basis': 'TEST source-content comparison', 'relation': 'same_narration',
                'reference_url': 'https://example.invalid/TEST/' + str(number),
                'source_local_number': str(index + 1)})
        for index, name in enumerate(builder.REVIEW_FILES):
            self.rows(name, reviews if index == 0 else [])
        self.rows('jihad-unresolved', [{'chinese_record_id': builder.UNRESOLVED_ID,
            'source_text_sha256': builder.text_hash(self.records[-1]['text']['translation'])}])
        self.rows('hadeethenc-english-unresolved', [])
        self.json(builder.BASE + '/reviews/review-union-audit.json', {'status': 'TEST fixture'})
        approved_id = self.records[0]['id']
        self.english_review = {'canonical_number': 1, 'provider_id': '100',
            'relation': 'full_parallel', 'human_review': False,
            'arabic_target_sha256': builder.text_hash(ARABIC),
            'hadeethenc_arabic_sha256': builder.text_hash(ARABIC),
            'english_text_sha256': builder.text_hash(ENGLISH),
            'references': parse_provider_references(self.publisher_bibliography),
            'approved_chinese_record_ids': [approved_id],
            'source_url': 'https://hadeethenc.com/en/browse/hadith/100',
            'reviewer': 'TEST English parallel reviewer',
            'rationale': 'TEST English and Arabic narrative comparison',
            'chinese_occurrence_review': {'reviewer': 'TEST occurrence reviewer',
                'human_review': False, 'method': 'TEST individual occurrence compatibility',
                'source_text_sha256_by_id': {
                    approved_id: builder.text_hash(self.records[0]['text']['translation'])}}}

    def put(self, relative, raw):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def json(self, relative, value):
        self.put(relative, (json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8'))

    def rows(self, name, rows):
        raw = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows).encode('utf-8')
        self.put(builder.BASE + '/reviews/' + name + '.jsonl.gz', gzip.compress(raw))

    def database(self, relative, schema, values):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute(schema)
            connection.execute('INSERT INTO hadeeths VALUES (' + ','.join('?' for _ in values) + ')', values)

    def compile(self):
        self.rows('hadeethenc-english-reviewed', [self.english_review])
        with redirect_stdout(io.StringIO()):
            builder.compile_bundle(self.root)
        return ReviewedCounterpartResolver(self.root)

    def normalized(self, index):
        row = self.records[index]
        return {'id': row['id'], 'source_id': builder.SOURCE_ID, 'language': 'zh-CN',
            'text_translation': row['text']['translation'],
            'source': {'sha256': self.provenance['original_source']['sha256']}}

    def test_english_approval_is_occurrence_specific_and_source_is_unchanged(self):
        resolver = self.compile()
        approved = resolver.for_record(self.normalized(0))
        other = resolver.for_record(self.normalized(1))
        self.assertEqual(approved['english']['text'], ENGLISH)
        self.assertIsNone(other['english']['text'])
        self.assertEqual(other['arabic']['text'], approved['arabic']['text'])
        self.assertIsNone(resolver.for_record(self.normalized(-1)))
        self.assertEqual((self.root / self.source_path).read_bytes(), self.before)

    def test_publisher_reference_is_separate_from_reviewed_parallel_number(self):
        english = self.compile().for_record(self.normalized(0))['english']
        self.assertEqual(english['references'][0]['number'], '2')
        self.assertEqual(english['references'][0]['numbering_scheme'], 'publisher_bibliography')
        self.assertEqual(english['reviewed_parallel_reference']['number'], '1')
        self.assertEqual(english['reviewed_parallel_reference']['numbering_scheme'], 'reviewed_source_parallel')

    def test_wrong_paired_english_is_suppressed_for_2319(self):
        value = self.compile().for_record(self.normalized(2))
        self.assertIsNotNone(value['arabic'])
        self.assertIsNone(value['english'])

    def test_excerpt_english_is_accepted_by_production_resolver(self):
        self.english_review['relation'] = 'source_excerpt'
        value = self.compile().for_record(self.normalized(0))
        self.assertEqual(value['english']['text'], ENGLISH)
        self.assertEqual(value['english']['scope'], 'source_excerpt')

    def test_stale_english_occurrence_review_hash_is_rejected(self):
        evidence = self.english_review['chinese_occurrence_review']
        evidence['source_text_sha256_by_id'][self.records[0]['id']] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'approval is stale'):
            self.compile()

    def test_missing_english_occurrence_review_is_rejected(self):
        self.english_review.pop('chinese_occurrence_review')
        with self.assertRaisesRegex(ValueError, 'explicit occurrence-level'):
            self.compile()

    def test_changed_supplement_quote_boundary_is_rejected(self):
        path = self.base / 'raw/supplements/907.json'
        value = json.loads(path.read_text())
        value['arabic'] += ' TEST uncaptured addition'
        path.write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'narration boundary'):
            self.compile()


if __name__ == '__main__':
    unittest.main()
