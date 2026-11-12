"""Source-language, original-byte and stopped-worker regression tests."""
import contextlib
import copy
import gzip
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from language_versions import available_language_codes, project_language_versions, validate_language_versions
from hadith_search import _keys
from citation_search import record_citation_pairs
from counterpart_coverage import availability_for
from material_registry import checked_supporting_files
from build_discovery import occurrence_link
import web_import_batch as batch


def version(language, text='TEST'):
    return {'id': 'TEST:' + language, 'language': language, 'text': text,
        'source': {'name': 'TEST publisher', 'record_url': 'https://example.org/test'},
        'references': [], 'comments': [],
        'translation_provenance': None if language == 'ar' else {'ai_translation': 'unknown'}}


class LanguageFrameworkTests(unittest.TestCase):
    def test_secondary_language_search_and_commentary_opt_in(self):
        own = version('en', 'TEST distinct English quotation')
        own['comments'] = ['TEST separate note marker']
        row = {'language': 'hi', 'language_versions': [own, version('uz-Cyrl')]}
        body, comments = _keys(row)
        self.assertIn('distinct english quotation', body)
        self.assertNotIn('separate note marker', body)
        self.assertIn('separate note marker', comments)
        self.assertTrue({'en', 'uz', 'uz-Cyrl'} <= set(available_language_codes(row)))

    def test_language_references_stay_paired(self):
        first, second = version('en'), version('hi')
        first['references'] = [{'collection': 'Sahih Muslim', 'number': '20', 'scope': 'source_citation'}]
        second['references'] = [{'collection': 'Sahih al-Bukhari', 'number': '90', 'scope': 'source_citation'}]
        self.assertEqual(record_citation_pairs({'language_versions': [first, second]}),
                         {('muslim', '20'), ('bukhari', '90')})

    def test_version_policy_preserves_history_and_own_declaration(self):
        first, second, arabic = version('hi'), version('en'), version('ar')
        second['translation_provenance']['source_declaration'] = {'classification': 'ai', 'evidence': 'TEST publisher declaration'}
        original = copy.deepcopy([first, second, arabic])
        result = project_language_versions(original, {'classification': 'human', 'basis': 'TEST owner policy'})
        self.assertEqual(result[0]['translation_provenance']['current_policy']['classification'], 'human')
        self.assertEqual(result[1]['translation_provenance']['current_policy']['classification'], 'ai')
        self.assertEqual(result[1]['translation_provenance']['ai_translation'], 'unknown')
        self.assertIsNone(result[2]['translation_provenance'])
        self.assertEqual(original, [first, second, arabic])

    def test_duplicate_versions_and_missing_sources_are_rejected(self):
        own = version('en')
        with self.assertRaises(ValueError):
            validate_language_versions([own, copy.deepcopy(own)])
        own['source'] = {}
        with self.assertRaises(ValueError):
            validate_language_versions([own])

    def test_availability_counts_supplied_text_and_safe_links(self):
        row = {'language': 'hi', 'language_versions': [version('en'), version('ar')]}
        self.assertEqual(availability_for(row), {'arabic': 'text', 'english': 'text'})
        row['language_versions'][0].update(text=None, scope='external_source')
        self.assertEqual(availability_for(row)['english'], 'external_link')
        row['language_versions'][0]['source']['record_url'] = 'javascript:alert(1)'
        self.assertEqual(availability_for(row)['english'], 'missing')

    def test_boundary_pending_language_preserves_context_without_becoming_narration(self):
        own = version('en', None)
        own.update(scope='external_source', quotation_status='boundary_pending')
        own['comments'] = [{'scope': 'source_context_not_narration', 'text': 'CONTEXT-ONLY compiler discussion'}]
        self.assertEqual(validate_language_versions([own]), [own])
        row = {'language': 'ar', 'language_versions': [own, version('ar')]}
        body, comments = _keys(row)
        self.assertNotIn('context-only', body)
        self.assertIn('context-only', comments)
        self.assertNotIn('en', available_language_codes(row))
        self.assertEqual(availability_for(row)['english'], 'external_link')
        for change in ({'quotation_status': None}, {'comments': []}, {'text': ''},
                       {'source': {'name': 'TEST', 'url': 'javascript:alert(1)'}}):
            bad = copy.deepcopy(own)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_language_versions([bad])

    def test_mismatched_provider_language_is_context_and_not_a_counterpart_link(self):
        own = version('en', None)
        own.update(scope='source_context', quotation_status='content_mismatch', match_status='provider_entry_content_mismatch')
        own['comments'] = [{'scope': 'source_context_not_narration', 'text': 'UNRELATED source ruling'}]
        self.assertEqual(validate_language_versions([own]), [own])
        record = {'language': 'ur', 'language_versions': [own, version('ur')]}
        self.assertEqual(availability_for(record)['english'], 'missing')
        self.assertNotIn('en', available_language_codes(record))
        body, comments = _keys(record)
        self.assertNotIn('unrelated source ruling', body)
        self.assertIn('unrelated source ruling', comments)
        own['text'] = 'UNRELATED source ruling'
        with self.assertRaises(ValueError):
            validate_language_versions([own])

    def test_new_links_are_exact_and_old_urls_remain(self):
        row = {'id': 'TEST:web:1&other=2', 'source_id': 'deenhindi-bukhari',
            'language_versions': [version('hi')], 'language': 'hi', 'book_key': 'bukhari', 'edition': 'test'}
        self.assertIn('?occurrence=TEST%3Aweb%3A1%26other%3D2', occurrence_link(row, 'browse/index.html'))
        row['source_id'] = 'legacy-test'
        self.assertNotIn('?occurrence=', occurrence_link(row, 'browse/index.html'))


class SourceEvidenceTests(unittest.TestCase):
    def test_stored_and_expanded_source_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'imports/test/source.html.gz'
            path.parent.mkdir(parents=True)
            raw = b'TEST\r\nsource bytes'
            stored = gzip.compress(raw, mtime=0)
            path.write_bytes(stored)
            entry = {'path': 'imports/test/source.html.gz', 'sha256': hashlib.sha256(stored).hexdigest(),
                'size_bytes': len(stored), 'compression': 'gzip', 'original_response_sha256': hashlib.sha256(raw).hexdigest()}
            self.assertEqual(checked_supporting_files(root, {'supporting_files': [entry]}, 'TEST'), [entry])
            entry['original_response_sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'Expanded source checksum mismatch'):
                checked_supporting_files(root, {'supporting_files': [entry]}, 'TEST')
            path.write_bytes(stored + b'changed')
            with self.assertRaisesRegex(ValueError, 'Material checksum mismatch'):
                checked_supporting_files(root, {'supporting_files': [entry]}, 'TEST')

    def test_traversal_and_unrelated_files_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for path in ('../secret', 'imports/../../secret', '.git/config'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    checked_supporting_files(Path(directory), {'supporting_files': [{'path': path, 'sha256': '0' * 64}]}, 'TEST')


class QueueLifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def save(self, path, data):
        batch.write_changed(self.root / path, data)

    def test_incomplete_setup_resumes_but_blocks_and_completion_do_not(self):
        self.save(batch.PROGRESS['deenhindi'], {'done': False, 'pending_fetch_count': 0, 'by_collection': {}})
        self.assertTrue(batch.source_status(self.root, 'deenhindi')['has_fetch_work'])
        for value in ({'done': True}, {'blocked': True, 'done': False, 'pending_fetch_count': 10}):
            self.save(batch.PROGRESS['deenhindi'], value)
            self.assertFalse(batch.source_status(self.root, 'deenhindi')['has_fetch_work'])

    def test_unexpected_worker_stop_is_saved_and_not_retried(self):
        self.save('catalog/web-import-plan.json', {'schema': 'hadith-bank-web-import-plan-v1', 'enabled': True,
            'sources': {name: {'enabled': name == 'deenhindi', 'max_requests_per_batch': 10,
                'max_seconds_per_batch': 60, 'delay_seconds': 1.25} for name in batch.PROGRESS}})
        with mock.patch('material_registry.load_public_materials', return_value={}), contextlib.redirect_stdout(io.StringIO()):
            with mock.patch.object(batch, 'run_source', return_value={'source': 'deenhindi', 'exit_code': 1, 'log': 'TEST'}) as runner:
                self.assertEqual(batch.main(['--root', str(self.root)]), 0)
                self.assertEqual(runner.call_count, 1)
            self.assertIn('deenhindi', batch.read_json(self.root / batch.STOP_FILE))
            with mock.patch.object(batch, 'run_source', side_effect=AssertionError('must not retry')) as runner:
                self.assertEqual(batch.main(['--root', str(self.root)]), 0)
                runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
