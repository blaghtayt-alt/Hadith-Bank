"""Offline recovery regressions; fixtures contain no publisher content."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import web_import_batch as batch


class WebImportBatchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.plan = {
            'schema': 'hadith-bank-web-import-plan-v1', 'enabled': True,
            'initial_max_seconds': 2,
            'sources': {name: {'enabled': True, 'max_requests_per_batch': 1,
                               'max_seconds_per_batch': 10, 'delay_seconds': 1}
                        for name in batch.PROGRESS},
        }
        batch.write_changed(self.root / 'catalog/web-import-plan.json', self.plan)
        for name in batch.PROGRESS:
            self.progress(name)

    def progress(self, name, state='pending', count=0, attempts=1, error=''):
        if name == 'deenhindi':
            value = {'done': state == 'done', 'blocked': state == 'blocked',
                     'imported_count': count, 'registered_hadith_count': count,
                     'classification_pending_count': 0,
                     'pending_fetch_count': int(state == 'pending'),
                     'errors_count': int(state == 'failed'),
                     'by_collection': {str(i): {'inventory': 1} for i in range(7)}}
        else:
            value = {'source_entries_obtained': count,
                     'prophetic_source_entries_registered': count,
                     'classification_pending_hidden': 0}
            batch.write_changed(self.root / ('imports/web-uzbek-20261112/' + name + '/checkpoint.json'),
                                {'tasks': [{'status': state, 'attempts': attempts, 'error': error}]})
        batch.write_changed(self.root / batch.PROGRESS[name], value)

    def read(self, path):
        return batch.read_json(self.root / path)

    def run_batch(self, worker, validator=None, *args):
        with mock.patch.object(batch, 'run_source', side_effect=worker), \
                mock.patch('material_registry.load_public_materials', side_effect=validator,
                           return_value=[]), mock.patch('sys.stdout', new_callable=io.StringIO):
            return batch.main(['--root', str(self.root), *args])

    def test_atomic_write_failure_preserves_previous_checkpoint(self):
        path = self.root / 'status.json'
        batch.write_changed(path, {'checkpoint': 'saved'})
        original = path.read_bytes()
        with mock.patch.object(batch.os, 'replace', side_effect=OSError('TEST interrupted replace')):
            with self.assertRaises(OSError):
                batch.write_changed(path, {'checkpoint': 'new'})
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(list(self.root.glob('.status.json.*')), [])

    def test_unchanged_status_does_not_rewrite_checkpoint(self):
        path = self.root / 'status.json'
        batch.write_changed(path, {'checkpoint': 'saved'})
        with mock.patch.object(batch.os, 'replace') as replace:
            batch.write_changed(path, {'checkpoint': 'saved'})
        replace.assert_not_called()

    def test_blocked_host_does_not_stop_another_pending_host(self):
        self.progress('deenhindi', 'blocked')
        self.progress('islom', 'done')
        status = batch.summarize(self.root, self.plan)
        self.assertTrue(status['requires_attention'])
        self.assertTrue(status['has_fetch_work'])
        self.assertFalse(status['schedule_should_pause'])
        self.assertFalse(status['fetch_queues_done'])
        self.assertEqual(status['source_status'][0]['state'], 'blocked')

    def test_worker_stop_takes_precedence_over_completed_checkpoint(self):
        for name in batch.PROGRESS:
            self.progress(name, 'done', count=2)
        batch.write_changed(self.root / batch.STOP_FILE, {'rivoyat': {'exit_code': 1}})
        status = batch.summarize(self.root, self.plan)
        self.assertFalse(status['fetch_queues_done'])
        self.assertTrue(status['requires_attention'])
        self.assertTrue(status['schedule_should_pause'])
        self.assertEqual(status['schedule_pause_reason'], 'inspection_required')
        self.assertEqual(status['fetched_entries'], 6)

    def test_disabled_plan_or_sources_pause_without_claiming_completion(self):
        self.plan['enabled'] = False
        status = batch.summarize(self.root, self.plan)
        self.assertFalse(status['has_fetch_work'])
        self.assertFalse(status['fetch_queues_done'])
        self.assertEqual(status['schedule_pause_reason'], 'plan_disabled')
        self.plan['enabled'] = True
        for settings in self.plan['sources'].values():
            settings['enabled'] = False
        status = batch.summarize(self.root, self.plan)
        self.assertTrue(status['schedule_should_pause'])
        self.assertFalse(status['fetch_queues_done'])
        self.assertEqual(status['schedule_pause_reason'], 'no_enabled_fetch_work')

    def test_terminal_failed_tasks_pause_but_transient_queue_can_continue(self):
        self.progress('deenhindi', 'done')
        self.progress('islom', 'failed', attempts=1, error='HTTP 404')
        self.progress('rivoyat', 'failed', attempts=2, error='TEST timeout')
        status = batch.summarize(self.root, self.plan)
        self.assertTrue(status['has_fetch_work'])
        self.progress('rivoyat', 'failed', attempts=3, error='TEST timeout')
        status = batch.summarize(self.root, self.plan)
        self.assertTrue(status['schedule_should_pause'])
        self.assertFalse(status['fetch_queues_done'])

    def test_launch_error_saves_log_and_result_receipt(self):
        with mock.patch.object(batch.subprocess, 'run', side_effect=FileNotFoundError('TEST missing executable')):
            result = batch.run_source(self.root, 'deenhindi', self.plan['sources']['deenhindi'],
                                      self.root / '.work/web-import-batch')
        self.assertEqual(result['exit_code'], 1)
        self.assertEqual(self.read('.work/web-import-batch/deenhindi.result.json'), result)
        self.assertIn('TEST missing executable', (self.root / result['log']).read_text())

    def test_hard_timeout_saves_failure_instead_of_claiming_graceful_resume(self):
        with mock.patch.object(batch.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['TEST'], 190)):
            result = batch.run_source(self.root, 'rivoyat', self.plan['sources']['rivoyat'],
                                      self.root / '.work/web-import-batch')
        self.assertEqual(result['exit_code'], 124)
        self.assertIn('inspect', result['error'])
        self.assertEqual(self.read('.work/web-import-batch/rivoyat.result.json'), result)

    def test_one_unexpected_worker_exception_preserves_other_hosts_and_stop(self):
        def worker(root, name, settings, logs):
            if name == 'deenhindi':
                raise RuntimeError('TEST unexpected worker exception')
            self.progress(name, 'done', count=3)
            return {'source': name, 'exit_code': 0}

        self.assertEqual(self.run_batch(worker), 0)
        stops = self.read(batch.STOP_FILE)
        self.assertEqual(set(stops), {'deenhindi'})
        status = self.read('imports/web-import-status.json')
        self.assertEqual(status['fetched_entries'], 6)
        self.assertTrue(status['schedule_should_pause'])
        self.assertFalse(status['fetch_queues_done'])
        self.assertIn('TEST unexpected worker exception', stops['deenhindi']['error'])
        with mock.patch.object(batch, 'run_source') as run, \
                mock.patch('material_registry.load_public_materials', return_value=[]), \
                mock.patch('sys.stdout', new_callable=io.StringIO):
            batch.main(['--root', str(self.root)])
        run.assert_not_called()

    def test_registry_failure_retains_stops_and_diagnostic_status_but_not_public_status(self):
        previous = {'TEST': 'previous validated status'}
        batch.write_changed(self.root / 'imports/web-import-status.json', previous)

        def worker(root, name, settings, logs):
            return {'source': name, 'exit_code': 1 if name == 'rivoyat' else 0}

        with self.assertRaisesRegex(ValueError, 'TEST invalid source hash'):
            self.run_batch(worker, ValueError('TEST invalid source hash'))
        self.assertEqual(set(self.read(batch.STOP_FILE)), {'rivoyat'})
        self.assertEqual(self.read('imports/web-import-status.json'), previous)
        diagnostic = self.read('.work/web-import-batch/status.json')
        self.assertEqual(diagnostic['validation_state'], 'failed')
        self.assertTrue(diagnostic['requires_attention'])

    def test_graceful_partial_batch_remains_resumable_without_worker_stop(self):
        def worker(root, name, settings, logs):
            self.progress(name, 'pending', count=1)
            return {'source': name, 'exit_code': 0}

        self.assertEqual(self.run_batch(worker), 0)
        self.assertEqual(self.read(batch.STOP_FILE), {})
        status = self.read('imports/web-import-status.json')
        self.assertEqual(status['fetched_entries'], 3)
        self.assertTrue(status['has_fetch_work'])
        self.assertFalse(status['schedule_should_pause'])
        self.assertFalse(status['fetch_queues_done'])
        self.assertEqual(self.read('.work/web-import-batch/status.json')['validation_state'], 'passed')


if __name__ == '__main__':
    unittest.main()
