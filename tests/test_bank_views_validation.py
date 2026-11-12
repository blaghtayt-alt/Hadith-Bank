"""Portable-validation regressions using actual unchanged source projections."""
import base64
import contextlib
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate_bank_views as validator
from build_reader import prose


class NavigationValidationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        (self.root / 'browse').mkdir()
        (self.root / 'catalog').mkdir()
        (self.root / 'README.md').write_text('[Browse](browse/source.md)\n', encoding='utf-8')
        self.page = self.root / 'browse/source.md'

    def test_literal_source_paragraphs_and_metadata_are_not_navigation(self):
        citation = '[৫১১৫, ৫৫২৩, ৬৯৬১; মুসলিম ১৬/২, হাঃ ১৪০৭](আধুনিক প্রকাশনীঃ ৩৮৯৫, ইসলামিক ফাউন্ডেশনঃ)'
        self.page.write_text(prose(citation, 'ltr') + '\n\n'
            '<pre>[source metadata](missing-source-text.md)</pre>\n\n'
            '<details>\n<summary>Navigation</summary>\n\n[Home](../README.md)\n\n</details>\n\n'
            '<p><a href="../README.md">Actual HTML navigation</a></p>\n', encoding='utf-8')
        report = validator.verify_navigation(self.root)
        self.assertEqual(report['markdown_files_checked'], 2)
        self.assertEqual(report['local_targets_checked'], 3)

    def test_actual_missing_links_still_fail_inside_and_outside_literal_blocks(self):
        examples = ['[Broken](missing.md)',
            '<details>\n<summary>Navigation</summary>\n\n[Broken](missing.md)\n\n</details>',
            '<p><a href="missing.md">Broken HTML link</a></p>',
            '<pre><a href="missing.md">Broken HTML link</a></pre>']
        for markup in examples:
            with self.subTest(markup=markup):
                self.page.write_text(markup, encoding='utf-8')
                with self.assertRaisesRegex(validator.ValidationError, 'Missing navigation target'):
                    validator.verify_navigation(self.root)

    def test_actual_escaping_links_still_fail(self):
        for markup in ('[Escape](../../outside.md)',
                       '<p><a href="../../outside.md">Escape</a></p>'):
            with self.subTest(markup=markup):
                self.page.write_text(markup, encoding='utf-8')
                with self.assertRaisesRegex(validator.ValidationError, 'Navigation escapes bank'):
                    validator.verify_navigation(self.root)


class PortableViewValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads((ROOT / 'catalog/materials.json').read_text(encoding='utf-8'))
        cls.material = next(m for m in catalog['materials'] if m['language'] == 'ja' and m['edition'].startswith('sqlite-'))
        shard = next(s for s in catalog['search']['shards'] if '/ja/' in s['path'])
        with (ROOT / shard['path']).open(encoding='utf-8') as stream:
            cls.records = [json.loads(next(stream)), json.loads(next(stream))]
        # This small fixture validates the original source projection without
        # installing the optional counterpart databases. Their additive field
        # is separately rejected below when no verified manifest is present.
        for record in cls.records:
            record.pop('counterparts', None)
        with (ROOT / cls.material['canonical_records_path']).open(encoding='utf-8') as stream:
            cls.canonical = [json.loads(next(stream)), json.loads(next(stream))]
        cls.policy = json.loads((ROOT / 'catalog/review-policy.json').read_text())['hadeethenc']
        cls.provenance_policy = validator.load_provenance_policy(ROOT)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for relative in (self.material['source_file'], self.material['canonical_records_path'],
                         'catalog/translation-origins.json', 'catalog/review-policy.json', 'catalog/provenance-policy.json'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            # Counterpart source labels now read the same validated provenance
            # policy used to reconstruct these source projections.
            fixture = self.provenance_policy if relative == 'catalog/provenance-policy.json' else {}
            target.write_text(json.dumps(fixture), encoding='utf-8')
        self.expected = {row['record_id']: validator.expected_record(row, self.material, i, True, self.policy, self.provenance_policy)
                         for i, row in enumerate(self.canonical)}

    def shards(self):
        specifications, aggregate = [], hashlib.sha256()
        for i, record in enumerate(self.records):
            relative = 'search/part-' + str(i) + '.jsonl'
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            data = json.dumps(record, ensure_ascii=False).encode('utf-8') + b'\n'
            path.write_bytes(data); aggregate.update(data)
            specifications.append({'path': relative, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'count': 1})
        return {'shards': specifications, 'records_path': 'search/records.jsonl',
                'records_sha256': aggregate.hexdigest(), 'count': 2, 'whole_file_optional': True}

    def test_complete_public_projection_rejects_injected_commentary_and_extra_fields(self):
        record = self.records[0]
        validator.compare_projection(record, self.expected[record['id']], self.root, True)
        for altered in (dict(record, private_note='unrelated attachment'),
                        dict(record, commentary={'translation': 'unrelated attachment'})):
            with self.assertRaisesRegex(validator.ValidationError, 'Public projection fields differ'):
                validator.compare_projection(altered, self.expected[record['id']], self.root, True)

    def test_shard_order_and_individual_hash_are_both_enforced(self):
        search = self.shards()
        validator.verify_shards(self.root, search, self.expected, True)
        reordered = dict(search, shards=list(reversed(search['shards'])))
        with self.assertRaisesRegex(validator.ValidationError, 'Ordered shard aggregate'):
            validator.verify_shards(self.root, reordered, self.expected, True)
        bad_hash = copy.deepcopy(search)
        bad_hash['shards'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(validator.ValidationError, 'Shard SHA-256 mismatch'):
            validator.verify_shards(self.root, bad_hash, self.expected, True)

    def test_counterparts_require_their_own_verified_source_manifest(self):
        record = dict(self.records[0], counterparts={'english': {'text': 'TEST unsupported'}})
        with self.assertRaisesRegex(validator.ValidationError, 'Counterpart lacks a verified source manifest'):
            validator.compare_projection(record, self.expected[record['id']], self.root, True)

    def test_reader_compares_complete_objects_not_just_ids_or_counts(self):
        search = self.shards()
        expected = [(r['id'], validator.object_hash(r)) for r in self.records]
        def write_reader(records):
            payload = base64.b64encode(gzip.compress(json.dumps(records, ensure_ascii=False).encode('utf-8'))).decode('ascii')
            snapshot = json.dumps({'record_count': 2, 'records_sha256': search['records_sha256']})
            (self.root / 'reader.html').write_text('<script id="hadith-records" data-encoding="gzip-base64">' + payload + '</script>'
                                                  '<script id="hadith-snapshot">' + snapshot + '</script>', encoding='utf-8')
        write_reader(self.records)
        validator.verify_reader(self.root, 'reader.html', expected, search)
        changed = copy.deepcopy(self.records)
        changed[0]['translator']['name'] = 'unrelated attachment'
        write_reader(changed)
        with self.assertRaisesRegex(validator.ValidationError, 'Reader differs from source projection'):
            validator.verify_reader(self.root, 'reader.html', expected, search)

    def test_paths_and_symlinks_cannot_escape_local_bank(self):
        for relative in ('../outside', '/tmp/outside', 'a/../b', 'a\\b', 'https://example.org/file', 'a//b'):
            with self.subTest(relative=relative), self.assertRaises(validator.ValidationError):
                validator.local(self.root, relative, exists=False)
        (self.root / 'escape').symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(validator.ValidationError, 'Symlink'):
            validator.local(self.root, 'escape/file', exists=False)

    def test_report_option_cannot_overwrite_historical_audit(self):
        prior = self.root / 'reports/organization-final-audit.json'
        prior.parent.mkdir(); prior.write_text('{"preserved":true}')
        with contextlib.redirect_stderr(io.StringIO()):
            result = validator.main(['--root', str(self.root), '--report', 'reports/organization-final-audit.json'])
        self.assertEqual(result, 1)
        self.assertEqual(prior.read_text(), '{"preserved":true}')

    def test_duplicate_json_keys_fail_closed(self):
        with self.assertRaisesRegex(validator.ValidationError, 'Duplicate JSON key'):
            validator.parse_json('{"id":"first","id":"second"}')


class GitBaselineTests(unittest.TestCase):
    def test_new_registered_sources_are_distinct_from_unchanged_baseline_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            def git(*args):
                return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
            git('init', '--quiet')
            existing = root / 'source.txt'; existing.write_text('TEST existing')
            git('add', 'source.txt')
            git('-c', 'user.name=TEST', '-c', 'user.email=TEST@example.invalid', 'commit', '--quiet', '-m', 'TEST')
            baseline = git('rev-parse', 'HEAD')
            added = root / 'materials/test-source/source.txt'
            added.parent.mkdir(parents=True); added.write_text('TEST added')
            relative = added.relative_to(root).as_posix()
            evidence = {'source.txt': {'sha256': validator.file_hash(existing)}, relative: {'sha256': validator.file_hash(added)}}
            allowed = {relative: validator.file_hash(added)}
            result = validator.verify_git_baseline(root, baseline, evidence, allowed)
            self.assertEqual(result['files_compared'], 1)
            self.assertEqual(result['new_registered_files_absent_from_baseline'], 1)
            self.assertEqual(result['new_registered_files'], [{'path': relative, 'sha256': allowed[relative]}])
            with self.assertRaisesRegex(validator.ValidationError, 'Unregistered source absent'):
                validator.verify_git_baseline(root, baseline, evidence)
            existing.write_text('TEST changed')
            evidence['source.txt']['sha256'] = validator.file_hash(existing)
            with self.assertRaisesRegex(validator.ValidationError, 'Source bytes differ from baseline Git'):
                validator.verify_git_baseline(root, baseline, evidence, allowed)


if __name__ == '__main__':
    unittest.main()
