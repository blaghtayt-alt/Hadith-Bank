"""Synthetic transport fixtures; no narration extraction or religious review."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import restore_persian_targhib_records as transport


class PersianTarghibTransportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'bank'
        self.root.mkdir()
        self.manifest = {'schema': transport.SCHEMA, 'files': []}
        self.expected = {}
        for index, (path, compressed_path) in enumerate(transport.EXPECTED_PATHS.items(), 1):
            data = (json.dumps({'id': f'TEST-{index}', 'text': 'TEST\u2028TEST\u2029原本'},
                               ensure_ascii=False) + '\n').encode('utf-8')
            self.set_file(path, compressed_path, data)
        self.save_manifest()

    def set_file(self, relative, compressed_path, data, count=1):
        compressed = gzip.compress(data, mtime=0)
        compressed_file = self.root / compressed_path
        compressed_file.parent.mkdir(parents=True, exist_ok=True)
        compressed_file.write_bytes(compressed)
        entry = {'path': relative, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                 'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
                 'count': count, 'transport_path': compressed_path, 'transport_bytes': len(compressed),
                 'transport_sha256': hashlib.sha256(compressed).hexdigest()}
        self.manifest['files'] = [item for item in self.manifest['files'] if item['path'] != relative] + [entry]
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.with_name('manifest.json').write_text(json.dumps({'records': {
            'path': relative, 'sha256': entry['sha256'], 'count': count}}), encoding='utf-8')
        self.expected[relative] = data

    def save_manifest(self):
        (self.root / transport.TRANSPORT_MANIFEST).write_text(json.dumps(self.manifest), encoding='utf-8')

    def assert_no_canonical_files(self):
        for relative in transport.EXPECTED_PATHS:
            self.assertFalse((self.root / relative).exists(), relative)
        self.assertEqual(list(self.root.rglob('.records-transport-*')), [])

    def test_exact_restore_then_idempotent_reuse(self):
        first = transport.restore(self.root)
        self.assertEqual((first['restored'], first['reused'], first['records']), (3, 0, 3))
        before = {}
        for relative, expected in self.expected.items():
            target = self.root / relative
            self.assertEqual(target.read_bytes(), expected)
            before[relative] = (target.stat().st_ino, target.stat().st_mtime_ns)
        second = transport.restore(self.root)
        self.assertEqual((second['restored'], second['reused']), (0, 3))
        for relative in self.expected:
            target = self.root / relative
            self.assertEqual(before[relative], (target.stat().st_ino, target.stat().st_mtime_ns))
        self.assertEqual(list(self.root.rglob('.records-transport-*')), [])

    def test_last_hash_mismatch_writes_nothing(self):
        self.manifest['files'][-1]['sha256'] = '0' * 64
        last = self.manifest['files'][-1]
        path = self.root / last['path']
        path.with_name('manifest.json').write_text(json.dumps({'records': {
            'path': last['path'], 'sha256': last['sha256'], 'count': last['count']}}), encoding='utf-8')
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'Canonical size or SHA-256 mismatch'):
            transport.restore(self.root)
        self.assert_no_canonical_files()

    def test_compressed_integrity_mismatch_writes_nothing(self):
        last = self.manifest['files'][-1]
        source = self.root / last['transport_path']
        source.write_bytes(source.read_bytes() + b'TEST')
        with self.assertRaisesRegex(ValueError, 'Compressed size or SHA-256 mismatch'):
            transport.restore(self.root)
        self.assert_no_canonical_files()

    def test_git_blob_mismatch_writes_nothing(self):
        self.manifest['files'][-1]['git_blob_sha'] = '0' * 40
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'Git blob SHA mismatch'):
            transport.restore(self.root)
        self.assert_no_canonical_files()

    def test_material_manifest_disagreement_writes_nothing(self):
        last = self.manifest['files'][-1]
        path = (self.root / last['path']).with_name('manifest.json')
        material = json.loads(path.read_text())
        material['records']['count'] += 1
        path.write_text(json.dumps(material), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Material manifest disagrees'):
            transport.restore(self.root)
        self.assert_no_canonical_files()

    def test_existing_changed_file_is_never_replaced_and_blocks_other_writes(self):
        relative = self.manifest['files'][-1]['path']
        target = self.root / relative
        target.write_bytes(b'TEST existing change\n')
        before = target.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Existing canonical file differs'):
            transport.restore(self.root)
        self.assertEqual(target.read_bytes(), before)
        for other in transport.EXPECTED_PATHS:
            if other != relative:
                self.assertFalse((self.root / other).exists())

    def test_only_exact_three_path_pairs_are_allowed(self):
        original = copy.deepcopy(self.manifest)
        invalids = []
        for key, value in [('path', '../records.jsonl'), ('path', '/tmp/TEST.jsonl'),
                           ('transport_path', 'imports/../TEST.gz'),
                           ('transport_path', self.manifest['files'][0]['transport_path'])]:
            candidate = copy.deepcopy(original)
            candidate['files'][-1][key] = value
            invalids.append(candidate)
        invalids.append({'schema': transport.SCHEMA, 'files': original['files'][:-1]})
        invalids.append({'schema': transport.SCHEMA, 'files': original['files'] + [original['files'][0]]})
        candidate = copy.deepcopy(original)
        candidate['files'][-1] = candidate['files'][0]
        invalids.append(candidate)
        for candidate in invalids:
            with self.subTest(candidate=candidate):
                self.manifest = candidate
                self.save_manifest()
                with self.assertRaisesRegex(ValueError, 'approved|three'):
                    transport.restore(self.root)
                self.assert_no_canonical_files()

    def test_symlink_destination_is_rejected_without_touching_target(self):
        outside = Path(self.temporary.name) / 'outside.jsonl'
        outside.write_bytes(b'TEST outside\n')
        relative = self.manifest['files'][-1]['path']
        (self.root / relative).symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            transport.restore(self.root)
        self.assertEqual(outside.read_bytes(), b'TEST outside\n')
        self.assertTrue((self.root / relative).is_symlink())
        self.assertFalse((self.root / self.manifest['files'][0]['path']).exists())

    def test_symlink_source_or_parent_is_rejected(self):
        entry = self.manifest['files'][-1]
        source = self.root / entry['transport_path']
        outside = Path(self.temporary.name) / 'outside.gz'
        source.rename(outside)
        source.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            transport.restore(self.root)
        self.assert_no_canonical_files()
        source.unlink()
        outside.rename(source)
        parent = (self.root / entry['path']).parent
        external_directory = Path(self.temporary.name) / 'outside-material'
        parent.rename(external_directory)
        parent.symlink_to(external_directory, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            transport.restore(self.root)
        self.assert_no_canonical_files()

    def test_invalid_json_ids_counts_and_unbounded_output_are_rejected(self):
        relative, compressed_path = list(transport.EXPECTED_PATHS.items())[-1]
        samples = [
            (b'{invalid}\n', 1, '.*'),
            (b'{"id":null}\n', 1, 'nonempty string ID'),
            (b'{"id":"TEST-1"}\n', 1, 'Duplicate record ID'),
            (b'{"id":"TEST-last"}\n{"id":"TEST-last"}\n', 2, 'Duplicate record ID'),
            (b'{"id":"TEST-last"}\n', 2, 'Record count mismatch'),
            (b'{"id":"TEST-last"}', 1, 'must end in a newline'),
        ]
        for data, count, message in samples:
            with self.subTest(data=data, count=count):
                self.set_file(relative, compressed_path, data, count)
                self.save_manifest()
                with self.assertRaisesRegex(ValueError, message):
                    transport.restore(self.root)
                self.assert_no_canonical_files()
        self.set_file(relative, compressed_path, b'{"id":"TEST-last"}\n')
        self.manifest['files'][-1]['bytes'] = transport.MAX_RECORD_BYTES + 1
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'Invalid canonical byte count'):
            transport.restore(self.root)
        self.assert_no_canonical_files()

    def test_decompression_exceeding_declared_size_is_bounded(self):
        last = self.manifest['files'][-1]
        last['bytes'] -= 1
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'Canonical size or SHA-256 mismatch'):
            transport.restore(self.root)
        self.assert_no_canonical_files()

    def test_concurrent_destination_is_not_overwritten(self):
        original_link = transport.os.link
        first = self.manifest['files'][0]['path']
        destination = self.root / first

        def raced_link(source, target):
            if Path(target) == destination:
                destination.write_bytes(b'TEST concurrent change\n')
            return original_link(source, target)

        with mock.patch.object(transport.os, 'link', side_effect=raced_link):
            with self.assertRaisesRegex(ValueError, 'Concurrent canonical file differs'):
                transport.restore(self.root)
        self.assertEqual(destination.read_bytes(), b'TEST concurrent change\n')
        self.assertEqual(list(self.root.rglob('.records-transport-*')), [])
        for relative in list(transport.EXPECTED_PATHS)[1:]:
            self.assertFalse((self.root / relative).exists())


if __name__ == '__main__':
    unittest.main()
