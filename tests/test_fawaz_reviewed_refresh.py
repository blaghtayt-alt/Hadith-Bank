"""Synthetic publication-gate regressions; TEST text is not a source quotation."""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fawaz_review_inputs as inputs
import refresh_fawaz_reviewed as refresh
import import_fawaz_bulk as importer
import validate_fawaz_sources as validator
from fawaz_source_checkpoint import write_snapshot
from test_fawaz_bulk import catalog, row, source_data


class ReviewedRefreshTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'bank'
        self.root.mkdir()
        (self.root / 'AGENTS.md').write_text('TEST rules')
        (self.root / 'unrelated').mkdir()
        (self.root / 'unrelated/keep.txt').write_bytes(b'TEST unrelated source')
        plan = {'schema': 'hadith-bank-fawaz-bulk-plan-v1', 'enabled': True,
                'repository': importer.REPOSITORY, 'revision': importer.REVISION,
                'books': ['malik'], 'languages': list(importer.BASE_LANGUAGES), 'max_books_per_batch': 1}
        importer.save_json(self.root, importer.PLAN, plan)
        state = {'schema': 'hadith-bank-fawaz-bulk-state-v1', 'revision': importer.REVISION,
                 'inputs': {}, 'stop': None}
        values = {'editions.json': importer.encoded(catalog(['malik'])),
                  'README.md': b'TEST readme', 'LICENSE': b'TEST license',
                  'References.md': b'TEST credit https://example.invalid/',
                  'CONTRIBUTING.md': b'TEST numbered source'}
        self.reviewed_text = 'TEST Zayd reported TEST source unit|NOTE TEST legal explanation'
        self.context_text = 'TEST independent English source context'
        for prefix in importer.BASE_LANGUAGES:
            values['editions/' + prefix + '-malik.json'] = importer.encoded(source_data('malik', [
                row(1, 'TEST قال رسول الله TEST old quotation' if prefix == 'ara' else 'TEST old ' + prefix),
                row(2, self.reviewed_text if prefix == 'ara' else self.context_text if prefix == 'eng'
                    else 'TEST independent Urdu source context'),
                row(3, 'TEST other independent source statement ' + prefix)]))
        for key, raw in values.items():
            state['inputs'][key] = importer.snapshot(self.root, key, raw, {
                'url': importer.provider_url(key), 'retrieved_at': 'TEST'})
        importer.save_json(self.root, importer.IMPORT + '/state.json', state)
        self.export_args = argparse.Namespace(root=self.root, export_only=True, fetch=False,
                                               adopt_dir=None, max_books=None, retry_failed=False)
        importer.run(self.export_args)
        baseline = self.review_catalog([])
        importer.save_json(self.root, inputs.BASELINE_PATH, baseline)
        audit = validator.SourceAudit(self.root)
        result = audit.run()
        self.assertEqual((result['provider_occurrences'], result['registered_occurrences'],
                          result['held_occurrences']), (3, 1, 2))
        self.fixture_baseline = {**refresh.BASELINE, 'provider_occurrences': 3,
                                'registered_occurrences': 1, 'held_occurrences': 2, 'edition_inputs': 3}
        patch = mock.patch.object(refresh, 'BASELINE', self.fixture_baseline)
        patch.start()
        self.addCleanup(patch.stop)
        self.snapshot = self.base / 'snapshot.json.gz'
        descriptor = write_snapshot(audit, self.snapshot, refresh.BASELINE['source_commit'])
        self.snapshot_sha = descriptor['sha256']
        self.baseline = refresh.load_baseline_snapshot(self.snapshot, self.snapshot_sha)
        end = self.reviewed_text.index('|NOTE')
        self.positive = {'provider_book': 'malik', 'provider_edition': 'ara-malik',
                         'typed_hadithnumber': '2', 'source_text_sha256': importer.sha(self.reviewed_text.encode()),
                         'quotation_spans': [[0, end]], 'report_type': 'companion_report',
                         'reported_speakers': [{'role': 'companion', 'name_as_supplied': 'Zayd',
                                                'source_spans': [[5, 9]]}],
                         'report_classification_note': 'TEST exact source-bound attributed report'}
        self.context = {'provider_book': 'malik', 'provider_edition': 'eng-malik',
                        'typed_hadithnumber': '2', 'source_text_sha256': importer.sha(self.context_text.encode()),
                        'action': 'source_attribution_pending', 'reason': 'TEST own-language attribution unresolved'}
        baseline_spec = self.write(inputs.BASELINE_PATH, inputs.json_bytes(baseline))
        raw = inputs.json_bytes(self.review_catalog([self.positive]))
        recovered = self.write('reports/fawaz-test/recovered.json.gz', inputs.gzip_bytes(raw))
        recovered.update(raw_bytes=len(raw), raw_sha256=inputs.sha256(raw))
        phase_raw = inputs.json_bytes(self.review_catalog([]))
        phase_manifest = inputs.json_bytes({'schema': inputs.ARCHIVE_SCHEMA, 'files': [
            {'path': 'review.json', 'bytes': len(phase_raw), 'sha256': inputs.sha256(phase_raw), 'decisions': 0}]})
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w') as archive:
            for name, raw in [('review.json', phase_raw), ('manifest.json', phase_manifest)]:
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
        phase = self.write('reports/fawaz-test/reviews.tar.gz', inputs.gzip_bytes(buffer.getvalue()))
        phase['manifest'] = {'path': 'manifest.json', 'bytes': len(phase_manifest),
                             'sha256': inputs.sha256(phase_manifest)}
        extra_raw = inputs.json_bytes(self.review_catalog([self.context]))
        extra = self.write('reports/fawaz-test/additional.json.gz', inputs.gzip_bytes(extra_raw))
        extra.update(compression='gzip', raw_bytes=len(extra_raw), raw_sha256=inputs.sha256(extra_raw))
        manifest = {'schema': inputs.INPUT_SCHEMA, 'repository': importer.REPOSITORY,
                    'revision': importer.REVISION, 'baseline': baseline_spec,
                    'recovered_catalog': recovered, 'phase_archive': phase, 'additional_reviews': [extra],
                    'preservation_baseline': self.fixture_baseline}
        self.write(inputs.MANIFEST_PATH, inputs.json_bytes(manifest))
        self.args = argparse.Namespace(root=self.root, baseline_snapshot=self.snapshot,
                                       baseline_snapshot_sha256=self.snapshot_sha)

    def review_catalog(self, decisions):
        return {'schema': inputs.CATALOG_SCHEMA, 'repository': importer.REPOSITORY,
                'revision': importer.REVISION, 'decisions': decisions}

    def write(self, relative, raw):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {'path': relative, 'bytes': len(raw), 'sha256': inputs.sha256(raw)}

    def fingerprints(self, root=None):
        root = root or self.root
        return {path.relative_to(root).as_posix(): refresh.digest_file(path)
                for path in root.rglob('*') if path.is_file()
                and not any(part in ('.work', '.git') for part in path.relative_to(root).parts)}

    def run_refresh(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return refresh.run(self.args)

    def test_absent_manifest_is_an_additive_noop(self):
        (self.root / inputs.MANIFEST_PATH).unlink()
        before = self.fingerprints()
        with mock.patch.object(refresh, 'git_baseline_inventory', side_effect=AssertionError('Unexpected Git')):
            self.assertEqual(self.run_refresh()['status'], 'skipped')
        self.assertEqual(before, self.fingerprints())
        self.assertFalse((self.root / '.work/fawaz-reviewed-refresh').exists())

    def test_complete_staged_export_preserves_old_quotes_and_exact_review_projection(self):
        inputs_before = refresh.source_files(self.root)
        with mock.patch.object(importer, 'fetch_bytes', side_effect=AssertionError('Unexpected network')):
            result = self.run_refresh()
        self.assertEqual((result['previous_registered'], result['registered_occurrences'],
                          result['held_occurrences'], result['newly_registered_occurrences']), (1, 2, 1, 1))
        self.assertEqual(result['verified_projected_readings'], 2)
        self.assertEqual((self.root / 'unrelated/keep.txt').read_bytes(), b'TEST unrelated source')
        for path, descriptor in inputs_before.items():
            if not path.startswith(importer.IMPORT + '/classification/') and not path.startswith(
                    importer.IMPORT + '/held/') and not path.endswith('/progress.json'):
                self.assertEqual(refresh.digest_file(self.root / path), descriptor['sha256'])
        audit = validator.SourceAudit(self.root)
        audit.run()
        comparison = refresh.compare_snapshot(audit, self.snapshot, self.snapshot_sha)
        refresh.require_preserved(comparison)
        before = self.fingerprints()
        self.run_refresh()
        self.assertEqual(before, self.fingerprints(), 'Repeated export should produce the same canonical bytes')

    def test_failed_candidate_gate_keeps_every_checkout_byte_unchanged(self):
        before = self.fingerprints()
        with mock.patch.object(refresh, 'verify_projection', side_effect=ValueError('TEST failed source gate')):
            with self.assertRaisesRegex(ValueError, 'failed source gate'):
                self.run_refresh()
        self.assertEqual(before, self.fingerprints())
        self.assertFalse((self.root / refresh.INSTALL_MARKER).exists())
        self.assertTrue(list((self.root / '.work/fawaz-reviewed-refresh').glob('run-*/candidate')))
        report = next((self.root / '.work/fawaz-reviewed-refresh').glob('run-*/candidate-audit.json'))
        evidence = json.loads(report.read_text())
        self.assertEqual(evidence['status'], 'failed_preservation_or_projection')
        self.assertEqual(evidence['source_integrity_status'], 'passed')
        self.assertIn('TEST failed source gate', evidence['publication_gate_error'])
        self.assertIn('previous_registered_language_changes_count', evidence['comparison'])

    def test_missing_positive_and_wrong_written_spans_fail_despite_valid_source_partition(self):
        # Before export the positive source exists but is still held.
        audit = validator.SourceAudit(self.root)
        audit.run()
        supplement = {refresh.decision_key(value): value for value in (self.positive, self.context)}
        with self.assertRaisesRegex(ValueError, 'not registered'):
            refresh.verify_projection(audit, supplement, self.baseline)
        importer.run(self.export_args)
        # A different exact partition is still source-faithful, but is not this review's selection.
        for manifest_path in (self.root / 'materials').glob('fawaz-*/manifest.json'):
            manifest = json.loads(manifest_path.read_text())
            records_path = self.root / manifest['records']['path']
            records = [json.loads(line) for line in records_path.read_text().splitlines()]
            for record in records:
                if record['source']['provider_identity']['typed_hadithnumber'] != '2':
                    continue
                reading = next(value for value in record['language_versions'] if value['language'] == 'ar')
                reading['text'] = self.reviewed_text
                reading['source']['text_spans'] = {
                    'quotation_spans': [[0, len(self.reviewed_text)]], 'quotation': [0, len(self.reviewed_text)],
                    'notes': [], 'method': 'source_hash_bound_reviewed_narration_span_v1', 'span_unit': 'unicode_codepoints'}
                reading['comments'] = [note for note in reading['comments'] if note['scope'] != 'source_compiler_note']
                record['text'] = {'arabic': self.reviewed_text, 'translation': self.reviewed_text}
            raw = b''.join(importer.encoded(record) for record in records)
            records_path.write_bytes(raw)
            manifest['records']['sha256'] = importer.sha(raw)
            manifest_path.write_bytes(importer.encoded(manifest))
        audit = validator.SourceAudit(self.root)
        audit.run()
        with self.assertRaisesRegex(ValueError, 'saved review spans'):
            refresh.verify_projection(audit, supplement, self.baseline)

    def test_disk_and_snapshot_identity_fail_before_checkout_changes(self):
        before = self.fingerprints()
        with mock.patch.object(refresh.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(1, 1, 0)):
            with self.assertRaisesRegex(ValueError, 'Insufficient disk'):
                self.run_refresh()
        self.assertEqual(before, self.fingerprints())
        self.args.baseline_snapshot_sha256 = '0' * 64
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.run_refresh()
        self.assertEqual(before, self.fingerprints())

    def test_install_rollback_restores_prior_directories_on_io_failure(self):
        stage = self.base / 'staged'
        shutil.copytree(self.root, stage)
        stage_args = copy.copy(self.export_args)
        stage_args.root = stage
        importer.run(stage_args)
        importer.save_json(stage, importer.IMPORT + '/source-integrity-validation.json', {'status': 'TEST passed'})
        job = self.base / 'job'
        job.mkdir()
        before = self.fingerprints()
        original = Path.rename

        def fail_late(path, destination):
            if path == stage / importer.IMPORT / 'progress.json':
                raise OSError('TEST interrupted install')
            return original(path, destination)

        with mock.patch.object(Path, 'rename', fail_late):
            with self.assertRaisesRegex(OSError, 'interrupted install'):
                refresh.install_outputs(self.root, stage, job)
        self.assertEqual(before, self.fingerprints())
        self.assertFalse((self.root / refresh.INSTALL_MARKER).exists())

    def test_unrecognized_material_files_and_symlink_inputs_are_never_overwritten(self):
        material = next((self.root / 'materials').glob('fawaz-*'))
        (material / 'owner-notes.txt').write_bytes(b'TEST retain me')
        before = self.fingerprints()
        with self.assertRaisesRegex(ValueError, 'Unexpected files'):
            self.run_refresh()
        self.assertEqual(before, self.fingerprints())
        (material / 'owner-notes.txt').unlink()
        (self.root / 'reports/fawaz-linked').symlink_to(self.root / 'unrelated', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.run_refresh()

    def test_git_baseline_restoration_reads_only_pinned_fawaz_paths(self):
        # A local repository with no remotes proves the restoration needs no network.
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'add', 'AGENTS.md', 'catalog', 'imports',
                        'materials', 'reports', 'unrelated'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=TEST', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'TEST pinned baseline'], check=True)
        commit = subprocess.check_output(['git', '-C', str(self.root), 'rev-parse', 'HEAD'], text=True).strip()
        inventory = refresh.git_baseline_inventory(self.root, commit)
        destination = self.base / 'restored'
        refresh.restore_baseline(self.root, destination, inventory, self.base / 'git.log')
        self.assertNotIn('unrelated/keep.txt', inventory)
        self.assertFalse((destination / 'unrelated').exists())
        self.assertEqual({name: refresh.digest_file(self.root / name) for name in inventory},
                         self.fingerprints(destination))
        with self.assertRaisesRegex(ValueError, 'objects are unavailable'):
            refresh.git_baseline_inventory(self.root, 'f' * 40)


if __name__ == '__main__':
    unittest.main()
