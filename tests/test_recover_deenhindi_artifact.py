"""Offline archive recovery regressions using only synthetic TEST source pages."""
import copy
import gzip
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_deenhindi as importer
import recover_deenhindi_artifact as recovery


def source_object(slug, number, accepted=False):
    source = {'id': 'TEST-' + slug + '-' + number, 'collectionSlug': slug,
              'hadithNumber': number, 'translationEnglish': 'TEST source field ' + number,
              'translationHindi': 'TEST हिन्दी ' + number,
              'textArabic': 'قال النبي TEST synthetic fixture' if accepted else 'TEST Arabic ' + number}
    flight = '0:' + json.dumps({'hadith': source}, ensure_ascii=False) + '\n'
    html = ('<html><p>Reference : [TEST source reference]</p><script>self.__next_f.push([1,'
            + json.dumps(flight) + '])</script></html>').encode()
    parsed_source, reference = importer.parse_record(html, slug, number)
    raw_stored = gzip.compress(html, mtime=0)
    raw_hash = recovery.sha(html)
    url = 'https://deenhindi.com/hadith/' + slug + '/' + number
    snapshot = {'path': importer.IMPORT + '/raw/' + raw_hash + '.html.gz',
                'sha256': raw_hash, 'stored_sha256': recovery.sha(raw_stored), 'compression': 'gzip',
                'url': url, 'final_url': url, 'status': 200, 'bytes': len(html), 'stored_bytes': len(raw_stored),
                'content_type': 'text/html', 'retrieved_at': 'TEST original retrieval'}
    saved = {'schema': 'deenhindi-source-record-v1', 'collection': slug, 'number': number,
             'source_record': parsed_source, 'source_reference_verbatim': reference,
             'snapshot': snapshot, 'classification': importer.classify(parsed_source)}
    parsed_raw = importer.json_bytes(saved)
    parsed_stored = gzip.compress(parsed_raw, mtime=0)
    descriptor = {'path': importer.IMPORT + '/parsed/' + slug + '/' + recovery.sha(parsed_raw) + '.json.gz',
                  'sha256': recovery.sha(parsed_raw), 'stored_sha256': recovery.sha(parsed_stored), 'compression': 'gzip'}
    entry = {'collection': slug, 'number': number, 'parsed': descriptor}
    return entry, saved, {snapshot['path']: raw_stored, descriptor['path']: parsed_stored}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'AGENTS.md').write_text('TEST repository fixture\n')
        guard = mock.patch.object(importer.urllib.request, 'urlopen',
            side_effect=AssertionError('Recovery must not request source pages'))
        self.network = guard.start()
        self.addCleanup(guard.stop)
        self.entries, self.saved, self.objects = {}, {}, {}
        for slug, number, accepted in (('bukhari', '1', False), ('bukhari', '2', False),
                                       ('bukhari', '3', True), ('malik', '88', False)):
            key = slug + ':' + number
            entry, saved, objects = source_object(slug, number, accepted)
            self.entries[key], self.saved[key] = entry, saved
            self.objects.update(objects)
        self.inventory = {slug: {'slug': slug, 'name': 'TEST book', 'identifiers': []}
                          for slug in importer.BOOKS}
        self.inventory['bukhari']['identifiers'] = ['1', '2', '3', '4']
        self.inventory['malik']['identifiers'] = ['88', '98']
        self.inventory['muslim']['identifiers'] = ['99']
        self.state = {'schema': 'deenhindi-import-state-v1',
            'imported': {key: self.entries[key] for key in ('bukhari:1', 'malik:88')},
            'errors': {'muslim:99': {'message': 'TEST current error', 'retained': True}},
            'reviewed_error_attempts': {'TEST-attempt': {'key': 'malik:98', 'authorization_consumed': True,
                                                       'status': 'prepared', 'prior_error': {'message': 'TEST'}}},
            'error_history': {'malik:98': [{'message': 'TEST older error'}]},
            'blocked': {'reason': 'TEST current block must survive'},
            'site_evidence': {}, 'future_control': {'preserve': ['TEST nested value']}}
        self.archived = {'schema': 'deenhindi-import-state-v1',
            'imported': {key: value for key, value in self.entries.items() if key.startswith('bukhari:')},
            'errors': {'TEST-archive-error': {'message': 'must never be copied'}},
            'blocked': None, 'reviewed_error_attempts': {}, 'site_evidence': {}}
        self.write_state(self.state)
        importer.write_json(self.root / importer.IMPORT / 'inventory.json', self.inventory)
        for key in self.state['imported']:
            saved = self.saved[key]
            for path in (saved['snapshot']['path'], self.entries[key]['parsed']['path']):
                importer.atomic(self.root / path, self.objects[path])
        self.archive = self.root / 'TEST-archive.zip'
        self.make_archive()
        self.before = {'source_status': [{'source': 'deenhindi', 'fetched_entries': 2}], 'TEST': 'before'}

    def write_state(self, state):
        importer.write_json(self.root / importer.IMPORT / 'state.json', state)

    def state_now(self):
        return json.loads((self.root / importer.IMPORT / 'state.json').read_bytes())

    def make_archive(self, extras=None, replacements=None):
        members = {importer.IMPORT + '/state.json': importer.json_bytes(self.archived)}
        for key, entry in self.archived['imported'].items():
            for path in (entry['parsed']['path'], self.saved[key]['snapshot']['path']):
                members[path] = self.objects[path]
        members.update({'materials/TEST-archive/records.jsonl': b'TEST old derivative\n',
                        'scripts/TEST-archive-code.py': b'raise RuntimeError("never executed")\n'})
        members.update(replacements or {})
        with zipfile.ZipFile(self.archive, 'w', compression=zipfile.ZIP_STORED) as stream:
            for name, data in members.items():
                stream.writestr(name, data)
            for name, data in extras or []:
                stream.writestr(name, data)
        self.expected = {**recovery.PIN, 'archive_bytes': self.archive.stat().st_size,
            'archive_sha256': recovery.file_sha(self.archive), 'archive_imported_entries': 3,
            'minimum_common_entries': 1, 'maximum_missing_entries': 2}

    def restore(self, **kwargs):
        return recovery.restore(self.root, self.expected, archive=self.archive,
                                before_status=self.before, **kwargs)

    def rebuild(self):
        recovery.offline_rebuild(self.root, self.expected)
        importer.write_json(self.root / '.work/web-import-batch/status.json', {'validation_state': 'passed'})

    def test_adds_only_missing_sources_preserving_all_current_control_and_unrelated_entries(self):
        original_controls = recovery.controls(self.state)
        result = self.restore()
        self.assertTrue(result['checkpoint_required'])
        self.assertEqual(result['new_entries_this_attempt'], 2)
        actual = self.state_now()
        self.assertEqual(recovery.controls(actual), original_controls)
        self.assertEqual(actual['imported'], self.entries)
        self.assertFalse((self.root / 'materials/TEST-archive').exists())
        self.assertFalse((self.root / 'scripts/TEST-archive-code.py').exists())
        for name, data in self.objects.items():
            self.assertEqual((self.root / name).read_bytes(), data)
        journal = recovery.receipt(self.root, self.expected)
        self.assertEqual(journal['recovered_keys'], ['bukhari:2', 'bukhari:3'])
        self.assertEqual(journal['before_status'], self.before)
        self.network.assert_not_called()

    def test_common_entry_mismatch_stops_before_sources_or_state_are_changed(self):
        self.state['imported']['bukhari:1']['extra_current_field'] = 'TEST preserve'
        self.write_state(self.state)
        before = (self.root / importer.IMPORT / 'state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'common imported entry differs'):
            self.restore()
        self.assertEqual((self.root / importer.IMPORT / 'state.json').read_bytes(), before)
        self.assertFalse((self.root / self.entries['bukhari:2']['parsed']['path']).exists())

    def test_current_error_or_consumed_retry_for_missing_key_prevents_merge(self):
        for control in ('error', 'retry'):
            with self.subTest(control=control):
                state = copy.deepcopy(self.state)
                if control == 'error':
                    state['errors']['bukhari:2'] = {'message': 'TEST live error'}
                else:
                    state['reviewed_error_attempts']['TEST-new'] = {'key': 'bukhari:2', 'authorization_consumed': True}
                self.write_state(state)
                with self.assertRaisesRegex(ValueError, 'overlap a current source error|overlap current retry'):
                    self.restore()
                self.assertEqual(self.state_now(), state)

    def test_whole_archive_digest_and_size_are_checked_before_mutation(self):
        for field, value in (('archive_sha256', '0' * 64), ('archive_bytes', 1)):
            with self.subTest(field=field):
                expected = {**self.expected, field: value}
                with self.assertRaisesRegex(ValueError, 'archive checksum|archive byte length'):
                    recovery.restore(self.root, expected, archive=self.archive)
                self.assertEqual(self.state_now(), self.state)

    def test_unsafe_and_duplicate_zip_members_are_rejected_even_when_not_selected(self):
        variants = ['../TEST', '/TEST', 'TEST\\escape', 'TEST/../escape', 'TEST:drive', 'TEST//path']
        for name in variants:
            with self.subTest(name=name):
                self.make_archive(extras=[(name, b'TEST')])
                with self.assertRaisesRegex(ValueError, 'unsafe path'):
                    self.restore()
        symlink = zipfile.ZipInfo('TEST-symlink')
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.make_archive(extras=[(symlink, b'../../TEST')])
        with self.assertRaisesRegex(ValueError, 'unsafe ZIP file type'):
            self.restore()
        with self.assertWarns(UserWarning):
            self.make_archive(extras=[('scripts/TEST-archive-code.py', b'TEST duplicate')])
        with self.assertRaisesRegex(ValueError, 'duplicate ZIP path'):
            self.restore()
        self.assertEqual(self.state_now(), self.state)

    def test_archived_common_raw_bytes_and_current_immutable_bytes_are_both_verified(self):
        raw = self.saved['bukhari:1']['snapshot']['path']
        self.make_archive(replacements={raw: b'TEST corrupt raw gzip'})
        with self.assertRaisesRegex(ValueError, 'stored source hash differs'):
            self.restore()
        self.make_archive()
        (self.root / raw).write_bytes(b'TEST current corrupt bytes')
        with self.assertRaisesRegex(ValueError, 'existing immutable source differs'):
            self.restore()
        self.assertEqual((self.root / raw).read_bytes(), b'TEST current corrupt bytes')
        self.assertEqual(self.state_now(), self.state)

    def test_parsed_object_must_match_current_parser_even_with_valid_internal_hashes(self):
        saved = copy.deepcopy(self.saved['bukhari:2'])
        saved['source_record']['translationEnglish'] = 'TEST invented parsed change'
        raw = importer.json_bytes(saved)
        stored = gzip.compress(raw, mtime=0)
        descriptor = {'path': importer.IMPORT + '/parsed/bukhari/' + recovery.sha(raw) + '.json.gz',
            'sha256': recovery.sha(raw), 'stored_sha256': recovery.sha(stored), 'compression': 'gzip'}
        self.archived['imported']['bukhari:2']['parsed'] = descriptor
        self.objects[descriptor['path']] = stored
        self.make_archive()
        with self.assertRaisesRegex(ValueError, 'current parser disagrees'):
            self.restore()
        self.assertEqual(self.state_now(), self.state)

    def test_missing_inventory_identity_stops_recovery(self):
        self.inventory['bukhari']['identifiers'].remove('2')
        importer.write_json(self.root / importer.IMPORT / 'inventory.json', self.inventory)
        with self.assertRaisesRegex(ValueError, 'absent from the current observed inventory'):
            self.restore()
        self.assertEqual(self.state_now(), self.state)

    def test_partial_source_install_is_replayed_without_resetting_current_controls(self):
        original = recovery.install_immutable
        counter = 0
        def interrupted(root, name, data):
            nonlocal counter
            if '/raw/' in name or '/parsed/' in name:
                counter += 1
                if counter == 2:
                    raise OSError('TEST interrupted install')
            return original(root, name, data)
        with mock.patch.object(recovery, 'install_immutable', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'interrupted install'):
                self.restore()
        self.assertEqual(self.state_now(), self.state)
        self.assertEqual(recovery.receipt(self.root, self.expected)['status'], 'prepared')
        advanced = self.state_now()
        advanced['future_control']['later'] = 'TEST change after interruption'
        self.write_state(advanced)
        result = self.restore()
        self.assertEqual(result['new_entries_this_attempt'], 2)
        self.assertEqual(recovery.controls(self.state_now()), recovery.controls(advanced))

    def test_completed_state_write_with_lost_receipt_is_replayed_without_download(self):
        original = recovery.write_receipt
        def interrupted(root, value):
            if value['status'] == 'sources_restored':
                raise OSError('TEST lost receipt acknowledgement')
            return original(root, value)
        with mock.patch.object(recovery, 'write_receipt', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'lost receipt'):
                self.restore()
        self.assertEqual(self.state_now()['imported'], self.entries)
        unavailable = mock.Mock(side_effect=AssertionError('Unneeded download'))
        result = recovery.restore(self.root, self.expected, archive_provider=unavailable)
        self.assertTrue(result['checkpoint_required'])
        self.assertEqual(recovery.receipt(self.root, self.expected)['status'], 'sources_restored')
        unavailable.assert_not_called()

    def test_crash_after_verified_index_before_receipt_can_resume(self):
        with mock.patch.object(recovery, 'write_receipt', side_effect=OSError('TEST receipt write interrupted')):
            with self.assertRaisesRegex(OSError, 'receipt write interrupted'):
                self.restore()
        self.assertTrue((self.root / recovery.INDEX_PATH).is_file())
        self.assertFalse((self.root / recovery.RECEIPT_PATH).exists())
        self.assertEqual(self.state_now(), self.state)
        result = self.restore()
        self.assertEqual(result['new_entries_this_attempt'], 2)

    def test_offline_rebuild_preserves_block_and_fails_closed_on_engine_error(self):
        self.restore()
        before = (self.root / importer.IMPORT / 'state.json').read_bytes()
        with mock.patch.object(importer, 'run', side_effect=ValueError('TEST bad review evidence')):
            with self.assertRaisesRegex(ValueError, 'bad review evidence'):
                recovery.offline_rebuild(self.root, self.expected)
        self.assertFalse((self.root / recovery.WORK / 'offline-rebuild.json').exists())
        result = recovery.offline_rebuild(self.root, self.expected)
        self.assertEqual(result['max_records'], 0)
        self.assertTrue(result['existing_block_preserved'])
        self.assertEqual((self.root / importer.IMPORT / 'state.json').read_bytes(), before)
        self.network.assert_not_called()

    def test_replay_requires_rebuild_until_validated_then_skips_archive(self):
        self.restore()
        unavailable = mock.Mock(side_effect=AssertionError('Unneeded download'))
        first = recovery.restore(self.root, self.expected, archive_provider=unavailable)
        self.assertTrue(first['checkpoint_required'])
        self.rebuild()
        summary = recovery.report(self.root, self.expected)
        self.assertEqual(summary['recovered_entries'], 2)
        self.assertEqual(summary['held_keys'], ['bukhari:2'])
        again = recovery.restore(self.root, self.expected, archive_provider=unavailable)
        self.assertFalse(again['checkpoint_required'])
        unavailable.assert_not_called()

    def test_validated_receipt_does_not_hide_missing_or_corrupt_source_objects(self):
        self.restore()
        self.rebuild()
        recovery.report(self.root, self.expected)
        path = self.root / self.entries['bukhari:2']['parsed']['path']
        path.unlink()
        provider = mock.Mock(return_value=self.archive)
        result = recovery.restore(self.root, self.expected, archive_provider=provider)
        self.assertTrue(result['checkpoint_required'])
        provider.assert_called_once_with()
        self.assertEqual(path.read_bytes(), self.objects[self.entries['bukhari:2']['parsed']['path']])
        path.write_bytes(b'TEST corrupted existing source')
        with self.assertRaisesRegex(ValueError, 'stored source hash differs'):
            recovery.restore(self.root, self.expected, archive_provider=mock.Mock())

    def test_report_exports_only_recovered_current_held_sources_with_exact_hashes(self):
        self.restore()
        self.rebuild()
        summary = recovery.report(self.root, self.expected)
        held = self.root / recovery.HELD
        rows = [json.loads(line) for line in (held / 'held-source-records.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['source_record'], self.saved['bukhari:2']['source_record'])
        manifest = json.loads((held / 'evidence-manifest.json').read_bytes())
        self.assertEqual(manifest['held_keys'], ['bukhari:2'])
        self.assertEqual(len(manifest['files']), 2)
        for name, receipt in manifest['files'].items():
            data = (held / 'sources' / name).read_bytes()
            self.assertEqual(data, self.objects[name])
            self.assertEqual(recovery.sha(data), receipt['sha256'])
        self.assertNotIn('malik:88', summary['source_identity_sha256'])
        recovered = gzip.decompress((self.root / recovery.DELTA / 'recovered-source-records.jsonl.gz').read_bytes())
        self.assertEqual(len(recovered.splitlines()), 2)
        self.network.assert_not_called()

    def test_new_review_after_rebuild_removes_obsolete_held_artifact_sources(self):
        self.restore()
        self.rebuild()
        recovery.report(self.root, self.expected)
        overrides = {'bukhari:2': {'classification': 'hadith',
            'snapshot_sha256': self.saved['bukhari:2']['snapshot']['sha256'],
            'source_record_sha256': recovery.sha(importer.json_bytes(self.saved['bukhari:2']['source_record'])),
            'reason': 'TEST reviewed fixture'}}
        importer.write_json(self.root / importer.IMPORT / 'classification-overrides.json', overrides)
        self.rebuild()
        summary = recovery.report(self.root, self.expected)
        self.assertEqual(summary['held_keys'], [])
        self.assertEqual(list((self.root / recovery.HELD).rglob('*.html.gz')), [])
        self.assertEqual((self.root / recovery.HELD / 'held-source-records.jsonl').read_bytes(), b'')

    def test_report_rejects_stale_rebuild_or_tampered_held_source(self):
        self.restore()
        self.rebuild()
        progress_path = self.root / importer.IMPORT / 'progress.json'
        progress = json.loads(progress_path.read_bytes())
        for change in ({'imported_count': 2}, {'source_review_engine_sha256': '0' * 64}):
            with self.subTest(change=change):
                importer.write_json(progress_path, {**progress, **change})
                with self.assertRaisesRegex(ValueError, 'offline rebuild receipt differs|offline rebuild/registry not validated'):
                    recovery.report(self.root, self.expected)
        importer.write_json(progress_path, progress)
        staged = self.root / importer.IMPORT / 'staged/bukhari.jsonl'
        rows = [json.loads(line) for line in staged.read_text().splitlines()]
        rows[-1]['source_record']['translationEnglish'] += ' TEST corrupted'
        importer.atomic(staged, importer.rows_bytes(rows))
        with self.assertRaisesRegex(ValueError, 'staged row differs'):
            recovery.report(self.root, self.expected)
        self.assertEqual(recovery.receipt(self.root, self.expected)['status'], 'sources_restored')

    def test_plan_accepts_only_pinned_artifact_and_explicit_disable(self):
        plan = {'schema': 'deenhindi-fixed-artifact-recovery-v1', 'enabled': True,
                'recovery_id': recovery.RECOVERY_ID, **recovery.PIN}
        importer.write_json(self.root / recovery.PLAN_PATH, plan)
        self.assertEqual(recovery.load_plan(self.root), plan)
        plan['enabled'] = False
        importer.write_json(self.root / recovery.PLAN_PATH, plan)
        self.assertIsNone(recovery.load_plan(self.root))
        plan['artifact_id'] += 1
        importer.write_json(self.root / recovery.PLAN_PATH, plan)
        with self.assertRaisesRegex(ValueError, 'single approved artifact'):
            recovery.load_plan(self.root)

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            recovery.json_value(b'{"TEST":1,"TEST":2}')

    def test_download_uses_fixed_api_routes_and_verifies_identity_before_streaming(self):
        metadata = {'id': self.expected['artifact_id'], 'name': self.expected['artifact_name'],
            'workflow_run': {'id': self.expected['run_id']}, 'size_in_bytes': self.expected['archive_bytes'],
            'expired': False, 'digest': 'sha256:' + self.expected['archive_sha256']}
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            self.assertEqual(command[:4], ['gh', 'api', '--hostname', 'github.com'])
            route = 'repos/' + recovery.REPOSITORY + '/actions/artifacts/' + str(self.expected['artifact_id'])
            if command[-1] == route:
                return SimpleNamespace(stdout=importer.json_bytes(metadata))
            self.assertEqual(command[-1], route + '/zip')
            kwargs['stdout'].write(self.archive.read_bytes())
            return SimpleNamespace(returncode=0)
        with mock.patch.dict(recovery.PIN, self.expected), mock.patch.dict(os.environ, {'GITHUB_REPOSITORY': recovery.REPOSITORY}), \
                mock.patch.object(recovery.subprocess, 'run', side_effect=run):
            result = recovery.download_archive(self.root, self.expected)
        self.assertEqual(result.read_bytes(), self.archive.read_bytes())
        self.assertEqual(len(calls), 2)
        result.unlink()
        metadata['workflow_run']['id'] += 1
        with mock.patch.dict(recovery.PIN, self.expected), mock.patch.object(recovery.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(ValueError, 'GitHub artifact identity'):
                recovery.download_archive(self.root, self.expected)
        self.assertEqual(len(calls), 3)


if __name__ == '__main__':
    unittest.main()
