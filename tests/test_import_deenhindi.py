"""Offline importer regressions using TEST fixtures, never religious source text."""
import collections
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_deenhindi as importer


def page(flight, citation='TEST source reference'):
    # Fragmenting the Flight stream across scripts exercises normal page chunks.
    split = len(flight) // 2
    scripts = ''.join('<script>self.__next_f.push([1,' + json.dumps(chunk) + '])</script>'
                      for chunk in (flight[:split], flight[split:]))
    return ('<html><p>Reference : [' + citation + ']</p>' + scripts + '</html>').encode()


def object_page(key, value):
    return page('0:' + json.dumps({key: value}, ensure_ascii=False) + '\n')


class Response(io.BytesIO):
    status = 200
    headers = {'Content-Type': 'text/html; charset=utf-8'}

    def __init__(self, url, data):
        super().__init__(data)
        self.url = url

    def geturl(self):
        return self.url


class DeenHindiImporterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'AGENTS.md').write_text('TEST repository fixture\n', encoding='utf-8')
        guard = mock.patch.object(importer.urllib.request, 'urlopen',
                                  side_effect=AssertionError('Live network is forbidden in these tests'))
        guard.start()
        self.addCleanup(guard.stop)

    def args(self, **changes):
        values = dict(root=self.root, max_records=7, max_seconds=600,
                      delay_seconds=1.25, timeout_seconds=30, retry_errors=False)
        values.update(changes)
        return SimpleNamespace(**values)

    def test_flight_utf8_offsets_chunking_and_identity(self):
        hindi = 'TEST हिन्दी\n🙂'
        english = 'TEST adjacent text row'
        source = {'id': 'TEST', 'collectionSlug': 'bukhari', 'hadithNumber': '1a',
                  'textArabic': 'TEST Arabic field', 'translationHindi': '$a',
                  'translationEnglish': '$b'}
        flight = '0:' + json.dumps({'hadith': source}) + '\n'
        flight += 'a:T' + format(len(hindi.encode()), 'x') + ',' + hindi
        flight += 'b:T' + format(len(english.encode()), 'x') + ',' + english
        extracted, citation = importer.parse_record(page(flight), 'bukhari', '1a')
        self.assertEqual(extracted['translationHindi'], hindi)
        self.assertEqual(extracted['translationEnglish'], english)
        self.assertEqual(extracted['textArabic'], source['textArabic'])
        self.assertEqual(citation, '[TEST source reference]')
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            importer.parse_record(page(flight), 'bukhari', '2')
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            importer.parse_record(page(flight), 'muslim', '1a')
        with self.assertRaisesRegex(ValueError, 'Incomplete length-prefixed'):
            importer.flight_texts('a:Tff,TEST')
        source['translationHindi'] = '$c'
        with self.assertRaisesRegex(ValueError, 'Unresolved source text reference'):
            importer.parse_record(object_page('hadith', source), 'bukhari', '1a')

    def test_inventory_preserves_observed_suffixes_and_rejects_duplicates(self):
        inventory = {'slug': 'bukhari', 'name': 'TEST collection',
                     'hadithsMetadata': [{'hadithNumber': '1'}, {'hadithNumber': '1a'},
                                         {'hadithNumber': '1.1'}]}
        self.assertEqual(importer.parse_inventory(object_page('collection', inventory), 'bukhari')['identifiers'],
                         ['1', '1a', '1.1'])
        inventory['hadithsMetadata'].append({'hadithNumber': '1a'})
        with self.assertRaisesRegex(ValueError, 'Duplicate identifiers'):
            importer.parse_inventory(object_page('collection', inventory), 'bukhari')

    def test_resume_and_offline_export_are_idempotent(self):
        requested = []

        def response(request, **_kwargs):
            url = request.full_url
            requested.append(url)
            path = importer.urllib.parse.urlsplit(url).path
            if path == '/robots.txt':
                body = b'User-agent: *\nAllow: /\n'
            elif path == '/page/about-us':
                body = b'<p>TEST source description</p>'
            else:
                parts = path.strip('/').split('/')
                slug = parts[1]
                if len(parts) == 2:
                    body = object_page('collection', {'slug': slug, 'name': 'TEST ' + slug,
                        'hadithsMetadata': [{'hadithNumber': '1a'}, {'hadithNumber': '2'}]})
                else:
                    body = object_page('hadith', {
                        'id': 'TEST-' + slug + '-' + parts[2], 'collectionSlug': slug,
                        'hadithNumber': parts[2], 'textArabic': '' if slug == 'muslim' else 'TEST Arabic',
                        'translationHindi': 'TEST हिन्दी', 'translationUrdu': 'TEST اردو',
                        'translationUrduRoman': 'TEST Roman Urdu',
                        'translationEnglish': '' if slug == 'bukhari' else 'TEST English'})
            return Response(url, body)

        classification = {'classification': 'hadith', 'method': 'TEST fixture only', 'evidence': 'TEST'}
        with mock.patch.object(importer.urllib.request, 'urlopen', side_effect=response), \
                mock.patch.object(importer.time, 'sleep'), \
                mock.patch.object(importer, 'classify', return_value=classification):
            first = importer.run(self.args())
            self.assertEqual(first['imported_count'], 7)
            self.assertEqual(first['remaining_count'], 7)
            material_files = list((self.root / 'materials').glob('deenhindi-*/*'))
            before = {path: importer.digest(path.read_bytes()) for path in material_files}
            request_count = len(requested)
            importer.run(self.args(max_records=0))
            self.assertEqual(len(requested), request_count)
            self.assertEqual(before, {path: importer.digest(path.read_bytes()) for path in material_files})
            second = importer.run(self.args())
        self.assertTrue(second['done'])
        self.assertEqual(second['imported_count'], 14)
        record_requests = [url for url in requested if len(importer.urllib.parse.urlsplit(url).path.strip('/').split('/')) == 3]
        self.assertEqual(len(record_requests), 14)
        self.assertTrue(all(count == 1 for count in collections.Counter(record_requests).values()))
        state = importer.load_json(self.root / importer.IMPORT / 'state.json')
        for saved in state['imported'].values():
            parsed = json.loads(importer.checked_bytes(self.root, saved['parsed']))
            source, _ = importer.parse_record(importer.checked_bytes(self.root, parsed['snapshot']),
                                              parsed['collection'], parsed['number'])
            self.assertEqual(source, parsed['source_record'])
        row = json.loads((self.root / 'materials/deenhindi-muslim/records.jsonl').read_text().splitlines()[0])
        self.assertIsNone(row['text']['arabic'])
        self.assertNotIn('ar', [version['language'] for version in row['language_versions']])

    def test_http_403_is_checkpointed_and_never_automatically_retried(self):
        error = urllib.error.HTTPError(importer.BASE + '/robots.txt', 403, 'TEST block', None, None)
        with mock.patch.object(importer.urllib.request, 'urlopen', side_effect=error) as request:
            first = importer.run(self.args())
            second = importer.run(self.args())
        self.assertTrue(first['blocked'])
        self.assertTrue(second['blocked'])
        self.assertEqual(request.call_count, 1)
        self.assertFalse(second['done'])

    def test_expired_deadline_stops_without_network(self):
        summary = importer.run(self.args(max_seconds=0.000000001))
        self.assertTrue(summary['time_budget_exhausted'])
        self.assertFalse(summary['blocked'])
        self.assertEqual(summary['imported_count'], 0)

    def test_canonical_shards_use_utf8_bytes_and_preserve_ids(self):
        rows = [{'id': 'TEST:' + str(i), 'edition': importer.EDITION,
                 'text': {'arabic': None, 'translation': 'TEST ' + 'क' * 50},
                 'language_versions': [{'id': 'TEST:' + str(i) + ':hi', 'text': 'TEST ' + 'क' * 50}]}
                for i in range(12)]
        original = copy.deepcopy(rows)
        limit = len(importer.rows_bytes(rows[:2]))
        shards = importer.canonical_shards(rows, limit=limit)
        flattened = [row for shard in shards for row in shard['rows']]
        self.assertGreater(len(shards), 1)
        self.assertEqual(len(shards[0]['data']), limit)
        self.assertTrue(all(len(shard['data']) <= limit for shard in shards))
        self.assertEqual([row['id'] for row in flattened], [row['id'] for row in rows])
        self.assertEqual(len({row['id'] for row in flattened}), len(rows))
        self.assertEqual([row['language_versions'] for row in flattened], [row['language_versions'] for row in rows])
        self.assertEqual(rows, original)
        self.assertEqual(shards, importer.canonical_shards(rows, limit=limit))
        self.assertEqual(shards[0]['edition'], importer.EDITION)
        self.assertEqual(shards[1]['edition'], importer.EDITION + '-part-002')
        with self.assertRaisesRegex(ValueError, 'One canonical occurrence exceeds'):
            importer.canonical_shards(rows, limit=1)


if __name__ == '__main__':
    unittest.main()
