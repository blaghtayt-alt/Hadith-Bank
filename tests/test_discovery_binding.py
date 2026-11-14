"""Independent source-binding gates for the disposable search presentation.

All quotations in these fixtures are explicitly synthetic test strings.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import bank_discovery
import build_reader
import validate_bank_views as validator
from test_bank_discovery import fixtures


class DiscoveryBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.records = fixtures()
        raw = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in self.records).encode()
        self.summary = {'record_count': len(self.records),
                        'records_sha256': hashlib.sha256(raw).hexdigest()}
        self.payload = bank_discovery.build_discovery_payload(self.records, self.summary)
        self.projected = [(row['id'], validator.object_hash(row)) for row in self.records]

    def verify(self, payload=None, hosted=True):
        payload = self.payload if payload is None else payload
        summary = copy.deepcopy(self.summary)
        if hosted:
            summary['discovery'] = bank_discovery.write_discovery_artifact(
                payload, self.root / 'data/discovery', 'data/discovery')
        else:
            summary['discovery_payload'] = payload
        (self.root / 'reader.html').write_text(
            '<script id="hadith-records" data-encoding="json">' +
            json.dumps(self.records, ensure_ascii=False) +
            '</script><script id="hadith-snapshot">' + json.dumps(summary) + '</script>')
        return validator.verify_reader(self.root, 'reader.html', self.projected, self.summary)

    def test_hosted_and_offline_index_bind_every_occurrence_and_exact_quotation(self):
        for hosted in (True, False):
            with self.subTest(hosted=hosted):
                report = self.verify(hosted=hosted)
                self.assertEqual(report['embedded_objects_compared'], len(self.records))
                self.assertEqual(report['discovery']['record_count'], len(self.records))
                self.assertEqual(report['discovery']['family_count'], len(self.records) - 1)
                self.assertFalse(report['discovery']['source_text_modified'])
                self.assertEqual(report['discovery']['indexed_quotation_fields_sha256'],
                                 self.payload['indexed_quotation_fields_sha256'])

    def test_rehashed_index_cannot_change_identity_wording_or_family_membership(self):
        mutations = [
            (lambda p: p['rows'][0].update(id='TEST changed identity'), 'identity'),
            (lambda p: p['rows'][0]['readings'][0].update(text='TEST fabricated preview'), 'preview'),
            (lambda p: p['rows'][0].update(groupId=None), 'membership'),
            (lambda p: p['groups'][0].update(members=[0, 2]), 'families'),
            (lambda p: p.update(occurrence_ids_sha256='0' * 64), 'IDs or quotation'),
            (lambda p: p.update(indexed_quotation_fields_sha256='0' * 64), 'IDs or quotation'),
        ]
        for mutation, message in mutations:
            with self.subTest(message=message):
                payload = copy.deepcopy(self.payload)
                mutation(payload)
                with self.assertRaisesRegex(ValueError, message):
                    self.verify(payload)

    def test_discovery_file_bytes_are_checked_before_use(self):
        descriptor = bank_discovery.write_discovery_artifact(
            self.payload, self.root / 'data/discovery', 'data/discovery')
        summary = dict(self.summary, discovery=descriptor)
        path = self.root / descriptor['parts'][0]['path']
        value = path.read_bytes()
        path.write_bytes(value[:-1] + bytes([value[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, 'bytes or SHA-256'):
            validator.read_discovery_payload(self.root, summary)

    def test_rehashed_navigation_cannot_invent_or_hide_source_evidence(self):
        mutations = [
            (lambda p: p['rows'][0].update(readings=[]), 'previews'),
            (lambda p: p['rows'][0]['readings'].append(copy.deepcopy(p['rows'][0]['readings'][0])), 'previews'),
            (lambda p: p['rows'][0]['readings'][0].update(sourceName='TEST invented publisher'), 'previews'),
            (lambda p: p['rows'][0].update(languages=['ja']), 'languages'),
            (lambda p: p['rows'][2]['availability'].update(arabic='external_link'), 'availability'),
            (lambda p: p['rows'][4].update(grades=[{'grade': 'TEST invented grade'}]), 'grades'),
            (lambda p: p['rows'][0]['searchSegments'][0].update(language='ja'), 'matched-reading locator'),
            (lambda p: p['rows'][0].update(editionLabel='TEST invented source edition'), 'edition label'),
            (lambda p: p['reference_index'].update({'bukhari:1': [2]}), 'reference index'),
            (lambda p: p['facets'].update(grade=[]), 'facets'),
        ]
        for mutation, message in mutations:
            with self.subTest(message=message):
                payload = copy.deepcopy(self.payload)
                mutation(payload)
                with self.assertRaisesRegex(ValueError, message):
                    self.verify(payload)

    def test_rehashed_posting_corruption_is_rejected_before_search(self):
        for hosted in (True, False):
            with self.subTest(hosted=hosted):
                payload = copy.deepcopy(self.payload)
                payload['postings'][0][1] = 'AA=='  # Invalid zero ordinal delta.
                with self.assertRaisesRegex(ValueError, '[Pp]osting'):
                    self.verify(payload, hosted=hosted)

    def test_source_snapshot_binding_cannot_be_relabelled(self):
        payload = copy.deepcopy(self.payload)
        payload['records_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'snapshot'):
            self.verify(payload)

    def test_prune_only_previous_generated_parts_after_publication(self):
        directory = self.root / 'data/discovery'
        directory.mkdir(parents=True)
        paths = ['data/discovery/discovery-' + 'a' * 64 + '.json.gz',
                 'data/discovery/discovery-postings-' + 'b' * 64 + '.json.gz',
                 'data/discovery/discovery-previews-' + 'c' * 64 + '.json.gz',
                 'data/discovery/unlisted-source.json.gz']
        for path in paths:
            (self.root / path).write_bytes(b'TEST')
        previous = {'path': paths[0], 'parts': [{'path': path} for path in paths[1:]]}
        current = {'path': paths[0], 'parts': [{'path': paths[2]}]}
        build_reader._prune_discovery_parts(self.root, 'data', previous, current)
        self.assertTrue((self.root / paths[0]).exists())
        self.assertFalse((self.root / paths[1]).exists())
        self.assertTrue((self.root / paths[2]).exists())
        self.assertTrue((self.root / paths[3]).exists())


if __name__ == '__main__':
    unittest.main()
