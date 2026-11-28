"""Synthetic byte-transfer tests; no source extraction or religious review."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import package_review_transfer as transfer


class ReviewTransferTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / 'review.zip'
        self.output = self.root / 'parts'
        self.restored = self.root / 'restored'
        self.payloads = {
            'data/原本.json': ('{"test":"نَصّ 原本\u2028TEST"}\r\n' * 150).encode('utf-8'),
            'audit/source.bin': bytes(range(256)) * 23,
            'audit/empty.txt': b'',
        }
        with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in self.payloads.items():
                archive.writestr(name, data)
            archive.writestr('images/not-selected.png', b'Unselected exact bytes')
        self.sha = transfer.digest_file(self.archive)
        self.selection = list(self.payloads)

    def pack(self, compression='none'):
        return transfer.pack(self.archive, self.sha, self.selection, self.output,
                             chunk_bytes=1024, compression=compression)

    def manifest(self):
        return json.loads((self.output / transfer.MANIFEST).read_text('utf-8'))

    def change_manifest(self, change):
        manifest = self.manifest()
        change(manifest)
        (self.output / transfer.MANIFEST).write_bytes(transfer.json_bytes(manifest))

    def test_exact_utf8_binary_empty_and_selection_only(self):
        for compression in ('none', 'gzip'):
            with self.subTest(compression=compression):
                self.output = self.root / ('parts-' + compression)
                self.restored = self.root / ('restored-' + compression)
                result = self.pack(compression)
                self.assertEqual(result['original_bytes'], sum(map(len, self.payloads.values())))
                self.assertFalse(result['review_status_changed'])
                manifest = self.manifest()
                self.assertEqual([e['path'] for e in manifest['files']], self.selection)
                self.assertTrue(all(p['size_bytes'] <= 1024 for e in manifest['files'] for p in e['parts']))
                restored = transfer.reassemble(self.output, self.restored, self.sha, result['manifest_sha256'])
                self.assertEqual(restored['status'], 'reassembled')
                for name, expected in self.payloads.items():
                    self.assertEqual((self.restored / name).read_bytes(), expected)
                self.assertFalse((self.restored / 'images').exists())
                self.assertTrue((self.restored / transfer.COMPLETE).is_file())

    def test_repeat_pack_and_restore_preserve_existing_files(self):
        first = self.pack('gzip')
        before = {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in self.output.rglob('*.bin')}
        second = self.pack('gzip')
        self.assertEqual(second['manifest_sha256'], first['manifest_sha256'])
        self.assertEqual(second['reused_parts'], second['parts'])
        self.assertEqual(before, {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in before})
        transfer.reassemble(self.output, self.restored)
        before = {name: (self.restored / name).stat().st_mtime_ns for name in self.payloads}
        result = transfer.reassemble(self.output, self.restored)
        self.assertEqual(result['reused_files'], len(self.payloads))
        self.assertEqual(before, {name: (self.restored / name).stat().st_mtime_ns for name in before})

    def test_gzip_manifest_and_parts_are_deterministic(self):
        first = self.pack('gzip')
        another = self.root / 'another'
        second = transfer.pack(self.archive, self.sha, self.selection, another, 1024, 'gzip')
        self.assertEqual(first['manifest_sha256'], second['manifest_sha256'])
        for part in self.output.rglob('*.bin'):
            self.assertEqual(part.read_bytes(), (another / part.relative_to(self.output)).read_bytes())

    def test_interrupted_pack_resumes_verified_parts(self):
        write = transfer.write_exact
        def interrupted(path, data):
            if str(path).endswith('00000-00000001.bin'):
                raise OSError('simulated interruption')
            return write(path, data)
        with mock.patch.object(transfer, 'write_exact', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'simulated interruption'):
                self.pack()
        first_part = self.output / 'parts/00000-00000000.bin'
        before = (first_part.stat().st_ino, first_part.stat().st_mtime_ns)
        self.assertFalse((self.output / transfer.MANIFEST).exists())
        with self.assertRaises(FileNotFoundError):
            transfer.verify(self.output)
        result = self.pack()
        self.assertEqual(result['reused_parts'], 1)
        self.assertEqual(before, (first_part.stat().st_ino, first_part.stat().st_mtime_ns))
        transfer.reassemble(self.output, self.restored)

    def test_corruption_blocks_resume_verify_and_restore(self):
        self.pack()
        last = self.manifest()['files'][1]['parts'][-1]
        target = self.output / last['path']
        altered = bytearray(target.read_bytes())
        altered[-1] ^= 1
        target.write_bytes(altered)
        for call in (self.pack, lambda: transfer.verify(self.output),
                     lambda: transfer.reassemble(self.output, self.restored)):
            with self.subTest(call=call), self.assertRaises(ValueError):
                call()
        self.assertFalse(self.restored.exists())

    def test_interrupted_restore_resumes_without_premature_completion(self):
        self.pack()
        verify = transfer.verify_entry
        def interrupted(root, entry, compression, output=None):
            if output is not None and entry['path'] == self.selection[1]:
                raise OSError('simulated restore interruption')
            return verify(root, entry, compression, output)
        with mock.patch.object(transfer, 'verify_entry', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'restore interruption'):
                transfer.reassemble(self.output, self.restored)
        first = self.restored / self.selection[0]
        before = (first.stat().st_ino, first.stat().st_mtime_ns)
        self.assertFalse((self.restored / transfer.COMPLETE).exists())
        self.assertEqual(list(self.restored.rglob('.transfer-*.tmp')), [])
        result = transfer.reassemble(self.output, self.restored)
        self.assertEqual(result['reused_files'], 1)
        self.assertEqual(before, (first.stat().st_ino, first.stat().st_mtime_ns))
        self.assertTrue((self.restored / transfer.COMPLETE).exists())

    def test_wrong_archive_hash_has_no_output(self):
        with self.assertRaisesRegex(ValueError, 'Archive SHA-256 mismatch'):
            transfer.pack(self.archive, '0' * 64, self.selection, self.output)
        self.assertFalse(self.output.exists())

    def test_changed_resume_selection_is_rejected(self):
        self.pack()
        original = (self.output / transfer.MANIFEST).read_bytes()
        with self.assertRaisesRegex(ValueError, 'differs or is corrupt'):
            transfer.pack(self.archive, self.sha, self.selection[:1], self.output, 1024, 'none')
        self.assertEqual((self.output / transfer.MANIFEST).read_bytes(), original)

    def test_selection_rejects_traversal_duplicates_and_missing_members(self):
        for selection in (['../escape'], ['/absolute'], ['data\\evil'], ['C:evil'],
                          [self.selection[0]] * 2, ['missing'], ['a', 'a/b'], ['A', 'a'],
                          ['.REVIEW-TRANSFER-COMPLETE.JSON']):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                transfer.pack(self.archive, self.sha, selection, self.output)
        self.assertFalse(self.output.exists())

    def test_parent_segment_alias_cannot_restore_inside_transfer_directory(self):
        self.pack()
        alias = self.root / 'alias'
        alias.mkdir()
        destination = alias / '..' / self.output.name / 'restored'
        with self.assertRaisesRegex(ValueError, 'must be separate'):
            transfer.reassemble(self.output, destination)
        self.assertFalse((self.output / 'restored').exists())

    def test_unsafe_duplicate_and_symlink_archive_members_are_rejected(self):
        for case in ('traversal', 'duplicate', 'symlink'):
            archive_path = self.root / (case + '.zip')
            with warnings.catch_warnings(), zipfile.ZipFile(archive_path, 'w') as archive:
                warnings.simplefilter('ignore', UserWarning)
                archive.writestr('safe.txt', b'TEST')
                if case == 'traversal':
                    archive.writestr('../outside.txt', b'NO')
                elif case == 'duplicate':
                    archive.writestr('safe.txt', b'CONFLICT')
                else:
                    info = zipfile.ZipInfo('link')
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    archive.writestr(info, '../outside')
            with self.subTest(case=case), self.assertRaises(ValueError):
                transfer.pack(archive_path, transfer.digest_file(archive_path), ['safe.txt'], self.output)
        self.assertFalse(self.output.exists())

    def test_manifest_hash_pin_and_original_hash_are_checked(self):
        result = self.pack('gzip')
        self.change_manifest(lambda value: value['files'][0].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'Manifest SHA-256 mismatch'):
            transfer.verify(self.output, expected_manifest_sha256=result['manifest_sha256'])
        with self.assertRaisesRegex(ValueError, 'Original SHA-256'):
            transfer.verify(self.output)
        with self.assertRaisesRegex(ValueError, 'Archive identity mismatch'):
            transfer.verify(self.output, '0' * 64)

    def test_manifest_part_traversal_and_decompression_overflow_rejected(self):
        self.pack('gzip')
        original = (self.output / transfer.MANIFEST).read_bytes()
        self.change_manifest(lambda value: value['files'][0]['parts'][0].update(path='../escape'))
        with self.assertRaisesRegex(ValueError, 'Unsafe or reordered'):
            transfer.verify(self.output)
        (self.output / transfer.MANIFEST).write_bytes(original)
        self.change_manifest(lambda value: value['files'][0].update(size_bytes=1))
        with self.assertRaisesRegex(ValueError, 'exceeds declared size'):
            transfer.verify(self.output)

    def test_symlink_and_conflicting_restore_targets_leave_other_files_untouched(self):
        self.pack()
        outside = self.root / 'outside'
        outside.mkdir()
        self.restored.mkdir()
        (self.restored / 'data').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            transfer.reassemble(self.output, self.restored)
        self.assertEqual(list(outside.iterdir()), [])
        (self.restored / 'data').unlink()
        conflicting = self.restored / 'audit/source.bin'
        conflicting.parent.mkdir()
        conflicting.write_bytes(b'OWNER DATA')
        with self.assertRaisesRegex(ValueError, 'differs or is corrupt'):
            transfer.reassemble(self.output, self.restored)
        self.assertEqual(conflicting.read_bytes(), b'OWNER DATA')
        self.assertFalse((self.restored / self.selection[0]).exists())
        self.assertFalse((self.restored / transfer.COMPLETE).exists())

    def test_completion_manifest_not_written_if_final_verification_fails(self):
        with mock.patch.object(transfer, 'verify_entry', side_effect=ValueError('verification failed')):
            with self.assertRaisesRegex(ValueError, 'verification failed'):
                self.pack()
        self.assertFalse((self.output / transfer.MANIFEST).exists())

    def test_cli_prints_small_summaries_not_payloads(self):
        selection = self.root / 'selection.json'
        selection.write_text(json.dumps(self.selection), 'utf-8')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = transfer.main(['pack', '--archive', str(self.archive), '--expected-sha256', self.sha,
                                  '--selection', str(selection), '--output', str(self.output)])
        self.assertEqual(code, 0)
        self.assertLess(len(output.getvalue()), 1024)
        self.assertEqual(json.loads(output.getvalue())['status'], 'packaged')
        self.assertNotIn('TEST', output.getvalue())


if __name__ == '__main__':
    unittest.main()
