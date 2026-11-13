"""Offline saved-head evidence export, using only synthetic TEST source pages."""
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import export_deenhindi_held_evidence as exporter
import import_deenhindi as importer
import recover_deenhindi_artifact as recovery
from test_recover_deenhindi_artifact import source_object


class CommittedHeldEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'scripts').mkdir()
        for path in (ROOT / 'scripts').glob('*.py'):
            shutil.copy2(path, self.root / 'scripts' / path.name)
        (self.root / '.gitignore').write_text('.work/\n__pycache__/\n')
        self.git('init', '-q')
        self.entries, self.saved, self.objects = {}, {}, {}
        for slug, number in (('bukhari', '1'), ('bukhari', '10'), ('bukhari', '2'), ('malik', '88')):
            entry, saved, files = source_object(slug, number)
            key = slug + ':' + number
            self.entries[key], self.saved[key] = entry, saved
            self.objects.update(files)
        for name, data in self.objects.items():
            importer.atomic(self.root / name, data)
        self.inventory = {slug: {'slug': slug, 'identifiers': []} for slug in importer.BOOKS}
        self.inventory['bukhari']['identifiers'] = ['2', '1', '10']
        self.inventory['malik']['identifiers'] = ['88']
        self.state = {'schema': 'deenhindi-import-state-v1', 'imported': self.entries,
            'blocked': {'reason': 'TEST retained block'}, 'errors': {'TEST': {'message': 'retained'}},
            'reviewed_error_attempts': {'TEST': {'authorization_consumed': True}}, 'future_control': ['TEST']}
        self.write_checkpoint()
        self.head = self.commit()
        guard = mock.patch.object(importer.urllib.request, 'urlopen',
            side_effect=AssertionError('Evidence export must not request source pages'))
        self.network = guard.start()
        self.addCleanup(guard.stop)
        env = mock.patch.dict(os.environ, {'GITHUB_RUN_ID': '12345', 'GITHUB_RUN_ATTEMPT': '2'})
        env.start()
        self.addCleanup(env.stop)

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.root), *args], check=True,
            capture_output=True, text=True)
        return result.stdout.strip()

    def commit(self):
        self.git('add', '-A')
        self.git('-c', 'user.name=TEST', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'TEST committed source checkpoint')
        return self.git('rev-parse', 'HEAD')

    def write_checkpoint(self, held=None, reverse=False):
        selected = set(self.entries if held is None else held)
        importer.write_json(self.root / importer.IMPORT / 'state.json', self.state)
        importer.write_json(self.root / importer.IMPORT / 'inventory.json', self.inventory)
        by_book = {}
        for slug in importer.BOOKS:
            rows = []
            for key in sorted(selected, reverse=reverse):
                if self.entries[key]['collection'] != slug:
                    continue
                row = copy.deepcopy(self.saved[key])
                row.update(parsed_path=self.entries[key]['parsed']['path'],
                           intake_classification=copy.deepcopy(row['classification']))
                rows.append(row)
            importer.atomic(self.root / importer.IMPORT / 'staged' / (slug + '.jsonl'), importer.rows_bytes(rows))
            fetched = sum(entry['collection'] == slug for entry in self.entries.values())
            by_book[slug] = {'fetched': fetched, 'classification_pending': len(rows),
                            'registered_hadith': fetched - len(rows), 'non_narration_source_entries': 0}
        progress = {'imported_count': len(self.entries), 'classification_pending_count': len(selected),
            'registered_hadith_count': len(self.entries) - len(selected), 'non_narration_source_entries': 0,
            'blocked': True, 'by_collection': by_book, 'updated_at': 'TEST committed time'}
        importer.write_json(self.root / importer.IMPORT / 'progress.json', progress)

    def export(self, **kwargs):
        return exporter.export(self.root, self.head, **kwargs)

    def bundle(self, result):
        folder = self.root / result['output']
        return {path.relative_to(folder).as_posix(): path.read_bytes() for path in folder.rglob('*') if path.is_file()}

    def test_stable_inventory_prefix_exact_bytes_and_remaining_count(self):
        before = {path: path.read_bytes() for path in (self.root / importer.IMPORT).rglob('*') if path.is_file()}
        result = self.export(max_records=2)
        files = self.bundle(result)
        receipt = json.loads(files['checkpoint.json'])
        self.assertEqual(receipt['selected_keys'], ['bukhari:2', 'bukhari:1'])
        self.assertEqual((receipt['held_entries_total'], receipt['selected_held_entries'], receipt['remaining_held_queue_count']), (4, 2, 2))
        self.assertEqual(receipt['next_held_key'], 'bukhari:10')
        self.assertEqual(receipt['saved_head'], self.head)
        self.assertTrue(receipt['source_progress']['blocked'])
        self.assertEqual(result['total_output_bytes'], sum(map(len, files.values())))
        manifest = json.loads(files['evidence-manifest.json'])
        self.assertEqual(manifest['total_output_bytes'], result['total_output_bytes'])
        self.assertLessEqual(result['total_output_bytes'], exporter.MAX_BYTES)
        for path, descriptor in manifest['artifact_files'].items():
            self.assertEqual(recovery.sha(files[path]), descriptor['sha256'])
            self.assertEqual(len(files[path]), descriptor['bytes'])
        for name in manifest['files']:
            self.assertEqual(files['sources/' + name], self.objects[name])
            self.assertEqual(manifest['files'][name]['git_blob_sha1'], self.git('rev-parse', self.head + ':' + name))
        self.assertEqual(self.bundle(self.export(max_records=2)), files)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.network.assert_not_called()
        self.write_checkpoint(reverse=True)
        self.head = self.commit()
        self.assertEqual(json.loads(self.bundle(self.export(max_records=2))['checkpoint.json'])['selected_keys'], receipt['selected_keys'])

    def test_byte_limit_includes_rows_state_receipts_and_manifest(self):
        one = self.export(max_records=1)
        limit = one['total_output_bytes'] + 100
        result = self.export(max_bytes=limit)
        self.assertEqual(result['selected_held_entries'], 1)
        self.assertEqual(result['remaining_held_queue_count'], 3)
        self.assertLessEqual(sum(map(len, self.bundle(result).values())), limit)
        for options in ({'max_records': 0}, {'max_records': 251}, {'max_bytes': exporter.MAX_BYTES + 1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.export(**options)
        before = self.bundle(result)
        with self.assertRaisesRegex(ValueError, 'exceed.*byte bound'):
            self.export(max_bytes=1)
        self.assertEqual(self.bundle(result), before)

    def test_zero_held_is_a_complete_empty_diagnostic(self):
        self.write_checkpoint(held=[])
        self.head = self.commit()
        result = self.export()
        self.assertEqual((result['held_entries_total'], result['selected_held_entries'], result['remaining_held_queue_count']), (0, 0, 0))
        files = self.bundle(result)
        self.assertFalse(any(name.startswith('sources/') for name in files))
        self.assertEqual(files['held-source-records.jsonl'], b'')
        state = (self.root / importer.IMPORT / 'state.json').read_bytes()
        self.assertEqual(gzip.decompress(files[exporter.STATE_ARTIFACT]), state)

    def test_complete_saved_state_is_exact_deterministic_and_hash_bound(self):
        self.state['error_history'] = {'TEST': [{'message': 'retained original error',
                                               'response_sha256': 'a' * 64}]}
        self.write_checkpoint()
        path = self.root / importer.IMPORT / 'state.json'
        # Valid, deliberately noncanonical JSON spacing proves byte preservation,
        # not a reconstruction from selected entries or a parsed state object.
        source = b' \n' + path.read_bytes() + b'\t\n'
        path.write_bytes(source)
        self.head = self.commit()
        result = self.export(max_records=1)
        files = self.bundle(result)
        checkpoint = json.loads(files['checkpoint.json'])
        descriptor = checkpoint['saved_state']
        stored = files[descriptor['path']]
        self.assertEqual(descriptor['source_path'], importer.IMPORT + '/state.json')
        self.assertEqual(descriptor['compression'], 'gzip')
        self.assertEqual(descriptor['bytes'], len(source))
        self.assertEqual(descriptor['sha256'], recovery.sha(source))
        self.assertEqual(descriptor['stored_bytes'], len(stored))
        self.assertEqual(descriptor['stored_sha256'], recovery.sha(stored))
        self.assertEqual(descriptor['maximum_uncompressed_bytes'], recovery.MAX_STATE_BYTES)
        self.assertEqual(descriptor['git_blob_sha1'], self.git('rev-parse', self.head + ':' + descriptor['source_path']))
        self.assertEqual(descriptor['git_blob_sha1'], hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest())
        self.assertEqual(checkpoint['input_receipts'][descriptor['source_path']]['sha256'], descriptor['sha256'])
        self.assertEqual(gzip.decompress(stored), source)
        self.assertEqual(recovery.uncompress(stored, descriptor['bytes']), source)
        with self.assertRaisesRegex(ValueError, 'gzip source exceeds object limit'):
            recovery.uncompress(stored, descriptor['bytes'] - 1)
        recovered = json.loads(gzip.decompress(stored))
        self.assertEqual(recovered, self.state)
        self.assertEqual(len(recovered['imported']), 4)
        self.assertEqual(result['selected_held_entries'], 1)
        self.assertEqual(recovered['blocked'], self.state['blocked'])
        self.assertEqual(recovered['errors'], self.state['errors'])
        self.assertEqual(recovered['error_history'], self.state['error_history'])
        self.assertEqual(recovered['reviewed_error_attempts'], self.state['reviewed_error_attempts'])
        self.assertEqual(recovered['future_control'], self.state['future_control'])
        self.assertEqual(stored[4:8], b'\0' * 4)
        self.assertEqual(stored[3], 0)  # No filename or other variable gzip headers.
        self.assertEqual(stored[9], 255)  # Stable platform-independent gzip header.
        manifest = json.loads(files['evidence-manifest.json'])
        self.assertEqual(manifest['artifact_files'][descriptor['path']],
                         {'bytes': len(stored), 'sha256': recovery.sha(stored)})
        self.assertEqual(self.bundle(self.export(max_records=1)), files)
        self.assertEqual(path.read_bytes(), source)
        self.network.assert_not_called()

    def test_whole_state_and_receipts_use_existing_cap_without_replacing_bundle(self):
        prior = self.export(max_records=1)
        before = self.bundle(prior)
        budget = prior['total_output_bytes'] + 100
        self.state['future_control'] = random.Random(117).randbytes(65536).hex()
        self.write_checkpoint()
        self.head = self.commit()
        state_before = (self.root / importer.IMPORT / 'state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'committed state and checkpoint receipts exceed the byte bound'):
            self.export(max_bytes=budget)
        self.assertEqual(self.bundle(prior), before)
        self.assertEqual((self.root / importer.IMPORT / 'state.json').read_bytes(), state_before)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        self.network.assert_not_called()

    def test_missing_committed_source_fails_without_replacing_a_prior_bundle(self):
        prior = self.export()
        before = self.bundle(prior)
        raw = self.root / self.saved['bukhari:2']['snapshot']['path']
        raw.unlink()
        self.head = self.commit()
        state = (self.root / importer.IMPORT / 'state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'missing committed source file'):
            self.export()
        self.assertEqual(self.bundle(prior), before)
        self.assertEqual((self.root / importer.IMPORT / 'state.json').read_bytes(), state)

    def test_committed_source_hash_and_current_parser_agreement_are_required(self):
        raw_path = self.root / self.saved['bukhari:2']['snapshot']['path']
        original = raw_path.read_bytes()
        raw_path.write_bytes(gzip.compress(b'TEST invalid changed response', mtime=0))
        self.head = self.commit()
        with self.assertRaisesRegex(ValueError, 'stored source hash differs'):
            self.export()
        raw_path.write_bytes(original)
        saved = self.saved['bukhari:2']
        saved['source_record']['translationEnglish'] = 'TEST invented parsed content'
        data = importer.json_bytes(saved)
        stored = gzip.compress(data, mtime=0)
        descriptor = {'path': importer.IMPORT + '/parsed/bukhari/' + recovery.sha(data) + '.json.gz',
            'sha256': recovery.sha(data), 'stored_sha256': recovery.sha(stored), 'compression': 'gzip'}
        importer.atomic(self.root / descriptor['path'], stored)
        self.entries['bukhari:2']['parsed'] = descriptor
        self.write_checkpoint()
        self.head = self.commit()
        with self.assertRaisesRegex(ValueError, 'current parser disagrees'):
            self.export()

    def test_dirty_state_progress_and_wrong_saved_head_fail_closed(self):
        for name in ('state.json', 'progress.json'):
            path = self.root / importer.IMPORT / name
            before = path.read_bytes()
            path.write_bytes(before + b'\n')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Git checkpoint check failed'):
                self.export()
            self.assertEqual(path.read_bytes(), before + b'\n')
            path.write_bytes(before)
        with self.assertRaisesRegex(ValueError, 'saved local HEAD differs'):
            exporter.export(self.root, 'f' * 40)
        self.assertFalse((self.root / exporter.OUTPUT_BASE).exists())

    def test_workflow_uses_actual_saved_head_and_diagnostics_follow_continuation(self):
        older = self.head
        progress = self.root / importer.IMPORT / 'progress.json'
        value = json.loads(progress.read_bytes())
        value['updated_at'] = 'TEST newer remote checkpoint'
        importer.write_json(progress, value)
        newer = self.commit()
        self.git('update-ref', 'refs/remotes/origin/main', newer)
        self.git('checkout', '--detach', '-q', older)
        lines = (ROOT / '.github/workflows/import-web-hadith.yml').read_text().splitlines()
        name = '      - name: Export bounded held evidence from the saved checkpoint'
        first = lines.index(name)
        last = next(i for i in range(first + 1, len(lines)) if lines[i].startswith('      - name: '))
        step = lines[first:last]
        self.assertGreater(first, lines.index('      - name: Continue the authorized Hindi queue after saved progress'))
        self.assertIn("        if: ${{ !cancelled() && steps.save.outcome == 'success' }}", step)
        self.assertIn('        continue-on-error: true', step)
        start = step.index('        run: >-')
        command = ' '.join(line[10:] for line in step[start + 1:] if line.startswith('          '))
        result = subprocess.run(['bash', '-euo', 'pipefail', '-c', command], cwd=self.root,
            env={**os.environ, 'GITHUB_SHA': 'a' * 40}, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        directory = self.root / exporter.OUTPUT_BASE / '12345-2'
        receipt = json.loads((directory / 'checkpoint.json').read_bytes())
        self.assertEqual(receipt['saved_head'], older)
        self.assertNotEqual(receipt['saved_head'], newer)
        self.assertEqual(receipt['source_progress']['updated_at'], 'TEST committed time')
        self.assertEqual(self.git('rev-parse', 'HEAD'), older)
        self.assertEqual(self.git('rev-parse', 'refs/remotes/origin/main'), newer)
        upload_first = lines.index('      - name: Retain bounded ordinary held-source evidence')
        upload_last = next(i for i in range(upload_first + 1, len(lines)) if lines[i].startswith('      - name: '))
        upload = lines[upload_first:upload_last]
        self.assertIn("        if: ${{ !cancelled() && steps.held_evidence.outcome == 'success' }}", upload)
        self.assertIn('        continue-on-error: true', upload)
        self.assertIn('          path: .work/deenhindi-held-evidence/${{ github.run_id }}-${{ github.run_attempt }}/', upload)


if __name__ == '__main__':
    unittest.main()
