"""Preservation gates retain exact failure evidence and keep publication failing."""
import contextlib
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fawaz_source_checkpoint as checkpoint
import validate_fawaz_sources as validator


REVISION = 'df57907be35291c91ad6a6691180e22ca9920784'
COMMIT = 'ca5f3f18e682376ce2c91e5f97f4b0d7e24eb4c6'
REGISTERED_ID = 'fawaz-test-registered'
HELD_ID = 'fawaz-test-held'
VERSION_ID = 'fawaz-test-registered-ar'


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def audit_fixture():
    """Explicitly synthetic inventory; no source review decisions are fabricated."""
    return SimpleNamespace(
        state={'revision': REVISION},
        inputs={'editions/ara-bukhari.json': {
            'source_path': 'editions/ara-bukhari.json',
            'sha256': digest('TEST complete raw edition'),
            'stored_sha256': digest('TEST compressed raw edition'),
        }},
        ledgers={
            REGISTERED_ID: {'status': 'hadith', 'reason': 'TEST reviewed source'},
            HELD_ID: {'status': 'held', 'reason': 'TEST attribution pending'},
        },
        accepted={REGISTERED_ID: {VERSION_ID: {
            'language': 'ar', 'status': 'text', 'source_context_kind': None,
            'quotation_sha256': digest('TEST قَالَ — quoted text'),
            'source_text_sha256': digest('TEST complete source field'),
        }}},
        held={HELD_ID: 'TEST attribution pending'},
    )


def source_result(audit):
    return {'status': 'passed', 'source_revision': REVISION,
            'provider_occurrences': len(audit.ledgers),
            'registered_occurrences': len(audit.accepted),
            'held_occurrences': len(audit.held)}


class FawazSourceCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.baseline = audit_fixture()
        self.path = self.root / 'published-baseline.json.gz'
        self.receipt = checkpoint.write_snapshot(self.baseline, self.path, COMMIT)
        self.original_snapshot = self.path.read_bytes()

    def compare(self, candidate):
        return checkpoint.compare_snapshot(candidate, self.path, self.receipt['sha256'])

    def run_cli(self, candidate, expected_sha256=None):
        report_path = self.root / 'reports' / 'candidate-audit.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text('{"status":"previous_attempt"}\n')
        candidate.run = lambda: source_result(candidate)
        args = ['--root', str(self.root), '--compare-snapshot', str(self.path),
                '--expected-comparison-sha256', expected_sha256 or self.receipt['sha256'],
                '--require-preserved', '--output', str(report_path)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(validator, 'SourceAudit', return_value=candidate), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = validator.main(args)
        self.assertTrue(report_path.is_file())
        self.assertFalse(report_path.with_name(report_path.name + '.tmp').exists())
        return code, json.loads(report_path.read_text()), stdout.getvalue(), stderr.getvalue()

    def assert_failed_report(self, result):
        code, report, stdout, stderr = result
        self.assertEqual(code, 1)
        self.assertEqual(report['status'], 'failed_preservation')
        self.assertEqual(report['source_integrity_status'], 'passed')
        self.assertEqual(report['preservation']['status'], 'failed')
        self.assertEqual(report['preservation']['error_type'], 'ValueError')
        self.assertEqual(stdout, '')
        self.assertIn('Fawaz source validation failed:', stderr)
        self.assertEqual(self.path.read_bytes(), self.original_snapshot)
        return report

    def test_snapshot_roundtrip_binds_source_commit_inventory_and_hashes(self):
        saved = json.loads(gzip.decompress(self.path.read_bytes()))
        self.assertEqual(saved['source_commit'], COMMIT)
        self.assertEqual(saved['source_revision'], REVISION)
        self.assertEqual(saved['registered_language_fingerprints'], self.baseline.accepted)
        self.assertEqual(saved['counts'], {'provider_occurrences': 2,
                                          'registered_occurrences': 1, 'held_occurrences': 1})
        self.assertEqual(self.receipt['sha256'], hashlib.sha256(self.original_snapshot).hexdigest())
        checkpoint.require_preserved(self.compare(copy.deepcopy(self.baseline)))

    def test_previously_held_promotion_passes_without_changing_existing_quotation(self):
        candidate = copy.deepcopy(self.baseline)
        candidate.ledgers[HELD_ID] = {'status': 'hadith', 'reason': 'TEST reviewed after baseline'}
        candidate.accepted[HELD_ID] = {'fawaz-test-held-ar': {
            'language': 'ar', 'status': 'text', 'source_context_kind': None,
            'quotation_sha256': digest('TEST newly selected quotation'),
            'source_text_sha256': digest('TEST already saved source field'),
        }}
        candidate.held.pop(HELD_ID)
        code, report, _, stderr = self.run_cli(candidate)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, '')
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['preservation']['status'], 'passed')
        self.assertEqual(report['comparison']['previous_held_now_registered'], 1)
        self.assertEqual(report['comparison']['previous_registered_language_changes_count'], 0)
        self.assertEqual(self.path.read_bytes(), self.original_snapshot)

    def test_deleted_provider_id_fails_and_retains_exact_missing_id(self):
        candidate = copy.deepcopy(self.baseline)
        candidate.ledgers.pop(HELD_ID)
        candidate.held.pop(HELD_ID)
        report = self.assert_failed_report(self.run_cli(candidate))
        self.assertEqual(report['comparison']['missing_previous_provider_ids'], [HELD_ID])

    def test_mutated_registered_quotation_fails_and_retains_before_after_hashes(self):
        candidate = copy.deepcopy(self.baseline)
        candidate.accepted[REGISTERED_ID][VERSION_ID]['quotation_sha256'] = digest('TEST قَال — changed diacritic')
        report = self.assert_failed_report(self.run_cli(candidate))
        changes = report['comparison']['previous_registered_language_changes']
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['id'], REGISTERED_ID)
        self.assertEqual(changes[0]['language_version_id'], VERSION_ID)
        self.assertEqual(changes[0]['previous'], self.baseline.accepted[REGISTERED_ID][VERSION_ID])
        self.assertEqual(changes[0]['current'], candidate.accepted[REGISTERED_ID][VERSION_ID])

    def test_extra_provider_id_fails_and_retains_exact_added_id(self):
        candidate = copy.deepcopy(self.baseline)
        candidate.ledgers['TEST-unexpected-provider'] = {'status': 'held', 'reason': 'TEST extra'}
        candidate.held['TEST-unexpected-provider'] = 'TEST extra'
        report = self.assert_failed_report(self.run_cli(candidate))
        self.assertEqual(report['comparison']['new_provider_ids'], ['TEST-unexpected-provider'])

    def test_demoted_registered_id_fails_and_retains_transition(self):
        candidate = copy.deepcopy(self.baseline)
        candidate.ledgers[REGISTERED_ID] = {'status': 'held', 'reason': 'TEST demotion'}
        candidate.accepted.pop(REGISTERED_ID)
        candidate.held[REGISTERED_ID] = 'TEST demotion'
        report = self.assert_failed_report(self.run_cli(candidate))
        self.assertEqual(report['comparison']['previous_registered_now_held_count'], 1)
        self.assertEqual(report['comparison']['previous_registered_now_held'][0]['id'], REGISTERED_ID)

    def test_snapshot_checksum_mismatch_fails_with_persisted_comparison_error(self):
        report = self.assert_failed_report(self.run_cli(copy.deepcopy(self.baseline), '0' * 64))
        self.assertNotIn('comparison', report)
        self.assertEqual(report['preservation']['error'], 'Preservation snapshot checksum mismatch')
        self.assertEqual(report['preservation']['comparison_snapshot'], str(self.path))
        self.assertEqual(report['preservation']['expected_snapshot_sha256'], '0' * 64)

    def test_mutated_original_source_fails_even_when_quotation_fingerprints_match(self):
        candidate = copy.deepcopy(self.baseline)
        candidate.inputs['editions/ara-bukhari.json']['sha256'] = digest('TEST altered original source')
        report = self.assert_failed_report(self.run_cli(candidate))
        self.assertIn('Original source input changed or disappeared', report['preservation']['error'])


if __name__ == '__main__':
    unittest.main()
