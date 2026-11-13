"""Offline source-bound retry tests. All text and responses are TEST fixtures."""
import copy
import gzip
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
import web_import_batch as worker
from test_import_deenhindi import Response, VERIFICATION_PAGE, object_page


class ReviewedHistoricalErrorTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / 'AGENTS.md').write_text('TEST fixture\n')
        self.state_path = self.root / importer.IMPORT / 'state.json'
        self.inventory = {slug: {'slug': slug, 'identifiers': ['1']} for slug in importer.BOOKS}
        importer.write_json(self.root / importer.IMPORT / 'inventory.json', self.inventory)
        self.state = {'schema': 'deenhindi-import-state-v1', 'imported': {},
                      'errors': {slug + ':1': self.error(slug + ':1') for slug in importer.BOOKS},
                      'site_evidence': {'about': {'TEST': 'already retained'}}}
        importer.write_json(self.state_path, self.state)
        self.requested = []
        network = mock.patch.object(importer.urllib.request, 'urlopen',
            side_effect=AssertionError('Live network is forbidden'))
        network.start()
        self.addCleanup(network.stop)
        sleep = mock.patch.object(importer.time, 'sleep')
        sleep.start()
        self.addCleanup(sleep.stop)

    def error(self, key, raw=VERIFICATION_PAGE):
        slug, number = key.split(':')
        url = importer.BASE + '/hadith/' + slug + '/' + number
        stored = gzip.compress(raw, mtime=0)
        relative = importer.IMPORT + '/raw/' + importer.digest(raw) + '.html.gz'
        importer.immutable(self.root / relative, stored)
        return {'url': url, 'error': 'No public page data found; extraction stopped without guessing',
            'at': '2026-11-12T00:00:00+00:00', 'snapshot': {'url': url, 'final_url': url,
            'status': 200, 'path': relative, 'compression': 'gzip',
            'sha256': importer.digest(raw), 'stored_sha256': importer.digest(stored)}}

    def decision(self, key):
        error = self.state['errors'][key]
        return {'key': key, 'url': error['url'], 'error_entry_sha256': importer.digest(importer.json_bytes(error)),
            'snapshot_sha256': error['snapshot']['sha256'], 'archive_classification': 'http_200_verification_page',
            'archived_response_reviewed': True, 'max_requests': 1,
            'reason': 'TEST exact historical response reviewed; one ordinary source request authorized.'}

    def authorize(self, keys=('bukhari:1',)):
        manifest = {'schema': 'deenhindi-reviewed-error-retry-v1', 'site': 'deenhindi.com',
            'scope': 'one_ordinary_request_per_listed_error', 'automatic_challenge_retries': False,
            'authorization_basis': 'TEST explicit instruction to make one ordinary recheck.',
            'entries': [self.decision(key) for key in keys]}
        importer.write_json(self.root / importer.RETRY_MANIFEST, manifest)
        return manifest

    def args(self, **updates):
        values = dict(root=self.root, max_records=7, max_seconds=60,
                      delay_seconds=1.25, timeout_seconds=30, retry_errors=False)
        values.update(updates)
        return SimpleNamespace(**values)

    def response(self, request, **kwargs):
        url = request.full_url
        self.requested.append(url)
        if url.endswith('/robots.txt'):
            return Response(url, b'User-agent: *\nAllow: /\n')
        parts = importer.urllib.parse.urlsplit(url).path.strip('/').split('/')
        slug, number = parts[-2:]
        return Response(url, object_page('hadith', {'id': 'TEST-' + slug + '-' + number,
            'collectionSlug': slug, 'hadithNumber': number, 'textArabic': 'TEST Arabic',
            'translationHindi': 'TEST Hindi'}))

    def run_mock(self, response=None, **options):
        with mock.patch.object(importer.urllib.request, 'urlopen', side_effect=response or self.response):
            return importer.run(self.args(**options))

    def record_requests(self):
        return [url for url in self.requested if '/hadith/' in url]

    def test_authorization_consumed_before_request_success_preserves_history_and_does_not_replay(self):
        self.authorize()
        previous = copy.deepcopy(self.state['errors']['bukhari:1'])

        def assert_before_request(request, **kwargs):
            if '/hadith/' in request.full_url:
                saved = importer.load_json(self.state_path)
                receipt, = saved['reviewed_error_attempts'].values()
                self.assertTrue(receipt['authorization_consumed'])
                self.assertEqual(receipt['status'], 'request_prepared')
                self.assertEqual(saved['error_history']['bukhari:1'], [previous])
            return self.response(request, **kwargs)

        first = self.run_mock(assert_before_request)
        self.assertEqual(self.record_requests(), [previous['url']])
        self.assertEqual(first['imported_count'], 1)
        self.assertEqual(first['errors_count'], 6)
        self.assertEqual(first['historical_error_identities_count'], 7)
        self.assertEqual(first['resolved_historical_error_identities_count'], 1)
        self.assertEqual(first['reviewed_error_attempt_outcomes'], {'succeeded': 1})
        state = importer.load_json(self.state_path)
        receipt, = state['reviewed_error_attempts'].values()
        self.assertEqual(receipt['prior_error'], previous)
        self.assertEqual(importer.checked_bytes(self.root, previous['snapshot']), VERIFICATION_PAGE)
        self.assertEqual(importer.checked_bytes(self.root, receipt['response_snapshot']),
            importer.checked_bytes(self.root, json.loads(importer.checked_bytes(
                self.root, state['imported']['bukhari:1']['parsed']))['snapshot']))
        # Manifest bytes may grow or change; the consumed original error must
        # not become a new authorization merely because its enclosing hash did.
        manifest = self.authorize()
        manifest['entries'][0]['reason'] += ' TEST explanation updated.'
        importer.write_json(self.root / importer.RETRY_MANIFEST, manifest)
        self.run_mock()
        self.assertEqual(self.record_requests(), [previous['url']])

    def test_repeated_verification_stops_the_whole_source_and_keeps_original_failure(self):
        self.authorize()
        previous_errors = copy.deepcopy(self.state['errors'])

        def response(request, **kwargs):
            if '/hadith/' in request.full_url:
                self.requested.append(request.full_url)
                return Response(request.full_url, VERIFICATION_PAGE)
            return self.response(request, **kwargs)

        first = self.run_mock(response)
        count = len(self.requested)
        second = self.run_mock(retry_errors=True)
        self.assertTrue(first['blocked'])
        self.assertTrue(second['blocked'])
        self.assertEqual(len(self.requested), count)
        state = importer.load_json(self.state_path)
        self.assertEqual(state['errors'], previous_errors)
        self.assertEqual(state['blocked']['snapshot']['sha256'], importer.digest(VERIFICATION_PAGE))
        self.assertEqual(first['reviewed_error_attempt_outcomes'], {'blocked': 1})

    def test_interrupted_uncertain_request_is_not_replayed(self):
        self.authorize()

        def interrupt(request, **kwargs):
            if '/hadith/' in request.full_url:
                self.requested.append(request.full_url)
                raise KeyboardInterrupt('TEST uncertain response after prepared receipt')
            return self.response(request, **kwargs)

        with self.assertRaises(KeyboardInterrupt):
            self.run_mock(interrupt)
        saved = importer.load_json(self.state_path)
        receipt, = saved['reviewed_error_attempts'].values()
        self.assertEqual(receipt['status'], 'request_prepared')
        self.assertTrue(receipt['authorization_consumed'])
        self.run_mock()
        self.assertEqual(len(self.record_requests()), 1)

    def test_invalid_evidence_fails_before_any_request_or_derived_change(self):
        manifest = self.authorize()
        manifest['entries'][0]['error_entry_sha256'] = '0' * 64
        importer.write_json(self.root / importer.RETRY_MANIFEST, manifest)
        before = self.state_path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.run_mock()
        self.assertEqual(self.requested, [])
        self.assertEqual(before, self.state_path.read_bytes())
        self.assertFalse((self.root / importer.IMPORT / 'progress.json').exists())

    def test_blanket_retry_only_retries_transient_errors_and_never_legacy_verification_pages(self):
        self.state['errors']['muslim:1'] = {'url': importer.BASE + '/hadith/muslim/1',
            'error': 'HTTP Error 503: TEST transient failure', 'snapshot': None,
            'at': '2026-11-12T00:00:00+00:00'}
        importer.write_json(self.state_path, self.state)
        result = self.run_mock(retry_errors=True)
        self.assertEqual(self.record_requests(), [importer.BASE + '/hadith/muslim/1'])
        self.assertEqual(result['errors_count'], 6)
        self.assertEqual(result['resolved_historical_error_identities_count'], 1)
        self.assertEqual(result['reviewed_error_attempts_count'], 0)

    def test_deadline_before_network_is_proven_unspent_and_can_resume_once(self):
        self.authorize()
        real_get = importer.Fetcher.get

        def deadline(fetcher, url):
            if '/hadith/' in url:
                raise importer.BudgetExpired()
            return real_get(fetcher, url)

        with mock.patch.object(importer.Fetcher, 'get', deadline):
            first = self.run_mock()
        self.assertTrue(first['time_budget_exhausted'])
        self.assertEqual(self.record_requests(), [])
        state = importer.load_json(self.state_path)
        receipt, = state['reviewed_error_attempts'].values()
        self.assertFalse(receipt['authorization_consumed'])
        self.assertEqual(receipt['status'], 'not_requested_deadline')
        self.assertEqual(first['reviewed_error_retry_pending_count'], 1)
        second = self.run_mock()
        self.assertEqual(len(self.record_requests()), 1)
        self.assertEqual(second['resolved_historical_error_identities_count'], 1)

    def test_new_authorized_id_can_join_manifest_without_replaying_previous_success(self):
        self.authorize()
        self.run_mock()
        self.authorize(('bukhari:1', 'muslim:1'))
        result = self.run_mock()
        self.assertEqual(self.record_requests(), [importer.BASE + '/hadith/bukhari/1',
                                                  importer.BASE + '/hadith/muslim/1'])
        self.assertEqual(result['errors_count'], 5)
        self.assertEqual(result['historical_error_identities_count'], 7)
        self.assertEqual(result['resolved_historical_error_identities_count'], 2)

    def test_serialized_worker_sees_new_authorization_and_respects_saved_stop(self):
        importer.write_json(self.root / importer.IMPORT / 'progress.json', {
            'done': False, 'blocked': False, 'pending_fetch_count': 0,
            'errors_count': 7, 'by_collection': {slug: {'inventory': 1} for slug in importer.BOOKS}})
        self.assertFalse(worker.source_status(self.root, 'deenhindi')['has_fetch_work'])
        self.authorize()
        status = worker.source_status(self.root, 'deenhindi')
        self.assertTrue(status['has_fetch_work'])
        self.assertEqual(status['reviewed_error_retry_pending_count'], 1)
        self.state['blocked'] = {'reason': 'TEST persisted source gate', 'automatic_retry_allowed': False}
        importer.write_json(self.state_path, self.state)
        status = worker.source_status(self.root, 'deenhindi')
        self.assertTrue(status['blocked'])
        self.assertFalse(status['has_fetch_work'])
        with mock.patch.object(importer.urllib.request, 'urlopen') as network:
            summary = importer.run(self.args(retry_errors=True))
        network.assert_not_called()
        self.assertTrue(summary['blocked'])

    def test_source_response_parseable_offline_is_not_retried_over_network(self):
        key = 'bukhari:1'
        raw = object_page('hadith', {'collectionSlug': 'bukhari', 'hadithNumber': '1',
                                   'textArabic': 'TEST preserved source'})
        self.state['errors'][key] = self.error(key, raw)
        importer.write_json(self.state_path, self.state)
        self.authorize()
        with self.assertRaisesRegex(ValueError, 'classification is unsupported'):
            self.run_mock()
        self.assertEqual(self.requested, [])

    def test_new_transient_failure_keeps_both_attempts_and_is_not_replayed_by_the_manifest(self):
        self.authorize()
        previous = copy.deepcopy(self.state['errors']['bukhari:1'])

        def failure(request, **kwargs):
            if '/hadith/' in request.full_url:
                self.requested.append(request.full_url)
                raise urllib.error.HTTPError(request.full_url, 503, 'TEST transient response', None, None)
            return self.response(request, **kwargs)

        result = self.run_mock(failure)
        self.assertFalse(result['blocked'])
        state = importer.load_json(self.state_path)
        self.assertEqual(state['error_history']['bukhari:1'], [previous])
        self.assertEqual(state['errors']['bukhari:1']['http_status'], 503)
        receipt, = state['reviewed_error_attempts'].values()
        self.assertEqual(receipt['status'], 'failed')
        self.assertEqual(receipt['prior_error'], previous)
        self.assertEqual(receipt['error'], state['errors']['bukhari:1'])
        self.run_mock()
        self.assertEqual(len(self.record_requests()), 1)

    def test_http_access_stop_cannot_be_reset_by_adding_another_reviewed_id(self):
        self.authorize()

        def denied(request, **kwargs):
            if '/hadith/' in request.full_url:
                self.requested.append(request.full_url)
                raise urllib.error.HTTPError(request.full_url, 403, 'TEST access stop', None, None)
            return self.response(request, **kwargs)

        result = self.run_mock(denied)
        self.assertTrue(result['blocked'])
        self.authorize(('bukhari:1', 'muslim:1'))
        count = len(self.requested)
        second = self.run_mock()
        self.assertTrue(second['blocked'])
        self.assertEqual(len(self.requested), count)


if __name__ == '__main__':
    unittest.main()
