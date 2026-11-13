"""Offline pilot checkpoint tests. Every response and quotation is a TEST fixture."""
import copy
import unittest
from unittest import mock
import urllib.error

import test_deenhindi_reviewed_error_retries as fixtures

importer = fixtures.importer


class PilotCheckpointTests(unittest.TestCase):
    setUp = fixtures.ReviewedHistoricalErrorTests.setUp
    error = fixtures.ReviewedHistoricalErrorTests.error
    decision = fixtures.ReviewedHistoricalErrorTests.decision
    authorize = fixtures.ReviewedHistoricalErrorTests.authorize
    args = fixtures.ReviewedHistoricalErrorTests.args
    response = fixtures.ReviewedHistoricalErrorTests.response
    run_mock = fixtures.ReviewedHistoricalErrorTests.run_mock
    record_requests = fixtures.ReviewedHistoricalErrorTests.record_requests

    def ordinary_pending(self):
        for slug in ('bukhari', 'muslim'):
            self.inventory[slug]['identifiers'].append('2')
        importer.write_json(self.root / importer.IMPORT / 'inventory.json', self.inventory)

    def pilot(self, flag=True):
        manifest = self.authorize()
        manifest['stop_batch_after_reviewed_retry'] = flag
        importer.write_json(self.root / importer.RETRY_MANIFEST, manifest)
        return manifest

    def assert_ordinary_untouched(self):
        saved = importer.load_json(self.state_path)
        self.assertEqual(importer.load_json(self.root / importer.IMPORT / 'inventory.json'), self.inventory)
        for key in ('bukhari:2', 'muslim:2'):
            self.assertNotIn(key, saved['imported'])
            self.assertNotIn(key, saved['errors'])
            self.assertNotIn(importer.BASE + '/hadith/' + key.replace(':', '/'), self.record_requests())

    def test_success_checkpoints_before_ordinary_ids_and_next_batch_resumes(self):
        self.ordinary_pending()
        self.pilot()
        previous = copy.deepcopy(self.state['errors']['bukhari:1'])

        def before_request(request, **kwargs):
            if '/hadith/' in request.full_url:
                receipt, = importer.load_json(self.state_path)['reviewed_error_attempts'].values()
                self.assertTrue(receipt['authorization_consumed'])
                self.assertTrue(receipt['stop_batch_after_reviewed_retry'])
                self.assertEqual(receipt['status'], 'request_prepared')
            return self.response(request, **kwargs)

        first = self.run_mock(before_request)
        self.assertEqual(self.record_requests(), [previous['url']])
        self.assertEqual(first['attempted_this_run'], 1)
        self.assertEqual(first['reviewed_retry_checkpoint'], 'bukhari:1')
        self.assertFalse(first['blocked'])
        self.assertFalse(first['time_budget_exhausted'])
        self.assertEqual(first['pending_fetch_count'], 2)
        self.assertEqual(first['reviewed_error_retry_pending_count'], 0)
        state = importer.load_json(self.state_path)
        receipt, = state['reviewed_error_attempts'].values()
        self.assertEqual(receipt['status'], 'succeeded')
        self.assertEqual(receipt['prior_error'], previous)
        self.assertEqual(state['error_history']['bukhari:1'], [previous])
        progress = importer.load_json(self.root / importer.IMPORT / 'progress.json')
        self.assertEqual(progress['imported_count'], 1)
        self.assertEqual(progress['pending_fetch_count'], 2)
        self.assert_ordinary_untouched()

        second = self.run_mock()
        self.assertEqual(self.record_requests(), [previous['url'],
            importer.BASE + '/hadith/bukhari/2', importer.BASE + '/hadith/muslim/2'])
        self.assertEqual(second['attempted_this_run'], 2)
        self.assertIsNone(second['reviewed_retry_checkpoint'])
        self.assertEqual(second['pending_fetch_count'], 0)

    def test_transient_failure_checkpoints_preserves_history_and_does_not_replay(self):
        self.ordinary_pending()
        self.pilot()
        previous = copy.deepcopy(self.state['errors']['bukhari:1'])

        def failure(request, **kwargs):
            if '/hadith/' in request.full_url:
                self.requested.append(request.full_url)
                raise urllib.error.HTTPError(request.full_url, 503, 'TEST transient response', None, None)
            return self.response(request, **kwargs)

        first = self.run_mock(failure)
        self.assertEqual(self.record_requests(), [previous['url']])
        self.assertEqual(first['attempted_this_run'], 1)
        self.assertEqual(first['reviewed_retry_checkpoint'], 'bukhari:1')
        self.assertFalse(first['blocked'])
        self.assertEqual(first['pending_fetch_count'], 2)
        state = importer.load_json(self.state_path)
        receipt, = state['reviewed_error_attempts'].values()
        self.assertTrue(receipt['authorization_consumed'])
        self.assertEqual(receipt['status'], 'failed')
        self.assertEqual(receipt['prior_error'], previous)
        self.assertEqual(state['error_history']['bukhari:1'], [previous])
        self.assertEqual(state['errors']['bukhari:1']['http_status'], 503)
        self.assert_ordinary_untouched()

        second = self.run_mock()
        self.assertEqual(self.record_requests(), [previous['url'],
            importer.BASE + '/hadith/bukhari/2', importer.BASE + '/hadith/muslim/2'])
        self.assertIsNone(second['reviewed_retry_checkpoint'])

    def assert_access_stop(self, response, expected_record_requests):
        self.ordinary_pending()
        self.pilot()
        previous_errors = copy.deepcopy(self.state['errors'])
        first = self.run_mock(response)
        self.assertTrue(first['blocked'])
        self.assertEqual(first['pending_fetch_count'], 2)
        self.assertIsNone(first['reviewed_retry_checkpoint'])
        self.assertEqual(len(self.record_requests()), expected_record_requests)
        state = importer.load_json(self.state_path)
        self.assertEqual(state['errors'], previous_errors)
        self.assertFalse(state['blocked']['automatic_retry_allowed'])
        receipt, = state['reviewed_error_attempts'].values()
        self.assertEqual(receipt['status'], 'blocked')
        self.assertTrue(receipt['authorization_consumed'])
        self.assert_ordinary_untouched()
        request_count = len(self.requested)
        second = self.run_mock(retry_errors=True)
        self.assertTrue(second['blocked'])
        self.assertEqual(len(self.requested), request_count)

    def test_renewed_verification_still_stops_whole_source(self):
        def verification(request, **kwargs):
            if '/hadith/' in request.full_url:
                self.requested.append(request.full_url)
                return fixtures.Response(request.full_url, fixtures.VERIFICATION_PAGE)
            return self.response(request, **kwargs)
        self.assert_access_stop(verification, 1)

    def test_http_access_stop_still_stops_whole_source(self):
        def denied(request, **kwargs):
            if '/hadith/' in request.full_url:
                self.requested.append(request.full_url)
                raise urllib.error.HTTPError(request.full_url, 403, 'TEST access stop', None, None)
            return self.response(request, **kwargs)
        self.assert_access_stop(denied, 1)

    def test_robots_denial_still_stops_before_record_network_request(self):
        def robots(request, **kwargs):
            if request.full_url.endswith('/robots.txt'):
                self.requested.append(request.full_url)
                return fixtures.Response(request.full_url, b'User-agent: *\nDisallow: /hadith/\n')
            raise AssertionError('TEST robots-denied request must not reach the network')
        self.assert_access_stop(robots, 0)

    def test_pre_request_deadline_does_not_consume_or_report_a_completed_pilot(self):
        self.ordinary_pending()
        self.pilot()
        real_get = importer.Fetcher.get

        def deadline(fetcher, url):
            if '/hadith/' in url:
                raise importer.BudgetExpired()
            return real_get(fetcher, url)

        with mock.patch.object(importer.Fetcher, 'get', deadline):
            first = self.run_mock()
        self.assertTrue(first['time_budget_exhausted'])
        self.assertIsNone(first['reviewed_retry_checkpoint'])
        self.assertEqual(self.record_requests(), [])
        self.assertEqual(first['pending_fetch_count'], 2)
        self.assertEqual(first['reviewed_error_retry_pending_count'], 1)
        receipt, = importer.load_json(self.state_path)['reviewed_error_attempts'].values()
        self.assertFalse(receipt['authorization_consumed'])
        self.assertEqual(receipt['status'], 'not_requested_deadline')
        self.assert_ordinary_untouched()

        second = self.run_mock()
        self.assertEqual(self.record_requests(), [importer.BASE + '/hadith/bukhari/1'])
        self.assertEqual(second['reviewed_retry_checkpoint'], 'bukhari:1')
        receipt, = importer.load_json(self.state_path)['reviewed_error_attempts'].values()
        self.assertEqual(receipt['status'], 'succeeded')
        self.assertEqual(receipt['previous_preparations'][0]['status'], 'not_requested_deadline')
        self.assert_ordinary_untouched()

    def test_invalid_checkpoint_flags_fail_before_network_or_derived_change(self):
        manifest = self.authorize()
        before = self.state_path.read_bytes()
        for flag in (None, 0, 1, 'true', 'false', [], {}):
            with self.subTest(flag=flag):
                manifest['stop_batch_after_reviewed_retry'] = flag
                importer.write_json(self.root / importer.RETRY_MANIFEST, manifest)
                with self.assertRaisesRegex(ValueError, 'Invalid reviewed Deen Hindi retry manifest'):
                    self.run_mock()
                self.assertEqual(self.requested, [])
                self.assertEqual(self.state_path.read_bytes(), before)
                self.assertFalse((self.root / importer.IMPORT / 'progress.json').exists())

    def assert_full_throughput(self):
        self.ordinary_pending()
        result = self.run_mock()
        self.assertEqual(self.record_requests(), [importer.BASE + '/hadith/bukhari/1',
            importer.BASE + '/hadith/muslim/2', importer.BASE + '/hadith/bukhari/2'])
        self.assertEqual(result['attempted_this_run'], 3)
        self.assertIsNone(result['reviewed_retry_checkpoint'])
        self.assertEqual(result['pending_fetch_count'], 0)

    def test_omitted_flag_preserves_normal_batch_throughput(self):
        self.authorize()
        self.assert_full_throughput()

    def test_explicit_false_preserves_normal_batch_throughput(self):
        self.pilot(False)
        self.assert_full_throughput()


if __name__ == '__main__':
    unittest.main()
