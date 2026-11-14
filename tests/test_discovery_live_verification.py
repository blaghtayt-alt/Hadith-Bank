"""Publication binding guards; TEST data and mocked HTTP, never a live-site claim."""
import asyncio
import contextlib
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_discovery_browser as browser


class LiveVerificationCliTests(unittest.TestCase):
    base = ['--report', 'TEST-report.json']
    live = ['--production-url', 'https://example.org/Hadith-Bank/',
            '--expected-source-commit', 'a' * 40, '--expected-reader-sha256', 'b' * 64]

    def test_existing_fixture_and_local_production_modes_remain_available(self):
        self.assertIsNone(browser.parse_args(self.base).production_url)
        self.assertFalse(browser.parse_args(self.base + ['--site-root', '_site']).production_only)
        self.assertTrue(browser.parse_args(
            self.base + ['--production-only', '--site-root', '_site']).production_only)

    def test_live_requires_exact_revision_inputs_and_normalizes_hex_case(self):
        args = browser.parse_args(self.base + self.live[:-1] + ['B' * 64])
        self.assertEqual(args.expected_source_commit, 'a' * 40)
        self.assertEqual(args.expected_reader_sha256, 'b' * 64)
        self.assertIsNone(args.site_root)

    def test_ambiguous_modes_missing_bindings_and_non_https_urls_are_rejected(self):
        cases = [
            ['--production-url', 'https://example.org/'],
            self.live + ['--site-root', '_site'],
            self.live + ['--production-only'],
            self.live + ['--build-only'],
            ['--expected-source-commit', 'a' * 40],
            ['--expected-reader-sha256', 'b' * 64],
            [self.live[0], 'http://example.org/', *self.live[2:]],
            [self.live[0], 'https://user:TEST@example.org/', *self.live[2:]],
            [self.live[0], 'https://example.org/?old=1', *self.live[2:]],
            [self.live[0], 'https://example.org/#old', *self.live[2:]],
            [*self.live[:-1], 'b' * 63],
            [*self.live[:3], 'z' * 40, *self.live[4:]],
            ['--production-only'],
            ['--production-only', '--site-root', '_site', '--build-only'],
        ]
        for case in cases:
            with self.subTest(case=case), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    browser.parse_args(self.base + case)
                self.assertEqual(raised.exception.code, 2)


@unittest.skipUnless(shutil.which('node'), 'Node is required for the real reader producer')
class LiveDiscoveryBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='hadith-live-binding-test-')
        cls.addClassCleanup(cls.temporary.cleanup)
        fixture = browser.build_fixture(Path(cls.temporary.name))
        cls.snapshot = fixture['snapshot']
        cls.raw = (fixture['site'] / cls.snapshot['discovery']['path']).read_bytes()
        cls.base_url = 'https://example.org/Hadith-Bank/'

    def test_real_fixture_navigation_retains_bytes_source_count_and_id_sequence(self):
        self.assertTrue(browser.live_discovery_url(self.base_url, self.snapshot).startswith(
            self.base_url + 'data/'))
        verified = browser.validate_live_discovery(self.raw, self.snapshot)
        self.assertEqual(verified['record_count'], 11)
        self.assertEqual(verified['records_sha256'], self.snapshot['records_sha256'])
        self.assertEqual(verified['uncompressed_sha256'], self.snapshot['discovery']['uncompressed_sha256'])
        self.assertEqual(verified['occurrence_ids_sha256'],
                         '1fa31db427504f707c886b262dfa565d21d15e3d54c585efcd26af80eab10f13')

    def test_mixed_source_descriptor_and_unsafe_publication_paths_are_rejected(self):
        for field, value in [('record_count', 12), ('records_sha256', 'd' * 64)]:
            with self.subTest(field=field), self.assertRaisesRegex(AssertionError, 'source snapshot'):
                browser.live_discovery_url(self.base_url, {**self.snapshot, field: value})
        for path in ['../data/TEST.gz', 'https://example.org/TEST.gz', 'data/%2e%2e/TEST.gz']:
            wrong = {**self.snapshot, 'discovery': {**self.snapshot['discovery'], 'path': path}}
            with self.subTest(path=path), self.assertRaisesRegex(AssertionError, 'safe local'):
                browser.live_discovery_url(self.base_url, wrong)

    def test_compressed_and_decoded_corruption_are_rejected(self):
        corrupt = self.raw[:-1] + bytes([self.raw[-1] ^ 1])
        with self.assertRaisesRegex(AssertionError, 'compressed bytes/hash mismatch'):
            browser.validate_live_discovery(corrupt, self.snapshot)
        wrong = {**self.snapshot, 'discovery': {
            **self.snapshot['discovery'], 'uncompressed_sha256': '0' * 64}}
        with self.assertRaisesRegex(AssertionError, 'decoded bytes/hash mismatch'):
            browser.validate_live_discovery(self.raw, wrong)

    def test_checksum_consistent_but_wrong_source_count_hash_or_ids_are_rejected(self):
        payload = browser.expand_discovery_payload(json.loads(gzip.decompress(self.raw)))
        payload.pop('row_columns', None)
        payload.pop('row_pools', None)
        for change in ['record_count', 'records_sha256', 'row_id']:
            altered = copy.deepcopy(payload)
            if change == 'row_id':
                altered['rows'][0]['id'] = 'TEST changed preserved identity'
            else:
                altered[change] = 12 if change == 'record_count' else 'f' * 64
            plain = json.dumps(altered, ensure_ascii=False).encode('utf-8')
            raw = gzip.compress(plain, mtime=0)
            snapshot = {**self.snapshot, 'discovery': {
                **self.snapshot['discovery'], 'bytes': len(raw),
                'sha256': hashlib.sha256(raw).hexdigest(), 'uncompressed_bytes': len(plain),
                'uncompressed_sha256': hashlib.sha256(plain).hexdigest()}}
            message = 'ID sequence' if change == 'row_id' else 'source snapshot'
            with self.subTest(change=change), self.assertRaisesRegex(AssertionError, message):
                browser.validate_live_discovery(raw, snapshot)


class LivePublicationRetryTests(unittest.TestCase):
    commit = 'a' * 40

    @staticmethod
    def html(commit):
        return ('<script id="hadith-snapshot">' + json.dumps({
            'site': {'build_commit': commit}}) + '</script>').encode('utf-8')

    def run_wait(self, responses, expected_sha=None):
        args = SimpleNamespace(production_url='https://example.org/Hadith-Bank/',
                               expected_source_commit=self.commit,
                               expected_reader_sha256=expected_sha or hashlib.sha256(self.html(self.commit)).hexdigest())
        pending = list(responses)
        self.clock, self.timeouts, self.report = [0.0], [], {'checks': []}

        def fetch(url, timeout, limit):
            self.timeouts.append(timeout)
            response = pending.pop(0) if len(pending) > 1 else pending[0]
            if isinstance(response, Exception):
                raise response
            return response, {'url': url, 'status': 200, 'bytes': len(response),
                              'sha256': hashlib.sha256(response).hexdigest(), 'http_date': 'TEST'}

        async def sleep(seconds):
            self.clock[0] += seconds

        async def thread(function, *arguments):
            return function(*arguments)

        with patch.object(browser, 'fetch_live_bytes', fetch), \
                patch.object(browser, 'time', SimpleNamespace(monotonic=lambda: self.clock[0])), \
                patch.object(browser.asyncio, 'sleep', sleep), patch.object(browser.asyncio, 'to_thread', thread):
            return asyncio.run(browser.wait_for_live_publication(args, self.report))

    def test_transient_error_and_stale_html_retry_until_both_bindings_match(self):
        expected = self.html(self.commit)
        html, snapshot, binding = self.run_wait([
            OSError('TEST transient HTTP failure'), self.html('c' * 40), expected])
        self.assertEqual(html, expected)
        self.assertEqual(snapshot['site']['build_commit'], self.commit)
        self.assertEqual(binding['sha256'], hashlib.sha256(expected).hexdigest())
        observations = self.report['live_publication']['attempts']
        self.assertEqual(len(observations), 3)
        self.assertIn('error', observations[0])
        self.assertFalse(observations[1]['matches_expected_publication'])
        self.assertTrue(observations[2]['matches_expected_publication'])
        self.assertEqual(self.clock[0], 10)

    def test_matching_html_hash_cannot_substitute_for_wrong_source_commit(self):
        wrong = self.html('c' * 40)
        with self.assertRaisesRegex(AssertionError, 'within 120 seconds'):
            self.run_wait([wrong], hashlib.sha256(wrong).hexdigest())
        self.assertEqual(self.clock[0], 120)
        self.assertEqual(self.report['live_publication']['status'], 'expected_html_not_observed')
        self.assertEqual(len(self.report['live_publication']['attempts']), 24)
        self.assertLessEqual(max(self.timeouts), 15)
        self.assertEqual(self.timeouts[-1], 5)

    def test_matching_source_commit_cannot_substitute_for_wrong_html_hash(self):
        with self.assertRaisesRegex(AssertionError, 'within 120 seconds'):
            self.run_wait([self.html(self.commit)], 'f' * 64)
        self.assertEqual(self.clock[0], 120)
        self.assertTrue(all(not attempt['matches_expected_publication']
                            for attempt in self.report['live_publication']['attempts']))


if __name__ == '__main__':
    unittest.main()
