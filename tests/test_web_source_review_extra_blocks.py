"""Focused recovery checks for reviewed lists omitted by paragraph extraction."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from web_source_reviews import SourceReviews, canonical_hash, sha, FOLDERS
from language_versions import language_search_values


class AdditionalSourceBlockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = b'<div class="col-md-9"><p>TEST primary report</p>\n<ol><li>TEST omitted list context</li></ol></div>'
        stored = gzip.compress(self.raw, mtime=0)
        relative = FOLDERS['hadisuz'] + '/snapshots/TEST.html.gz'
        self.snapshot = {'path': relative, 'sha256': sha(self.raw), 'stored_sha256': sha(stored)}
        path = self.root / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(stored)
        text = 'TEST primary report'
        self.row = {'id': 'TEST:1', 'language': 'uz', 'source_language_code': 'uz-Cyrl',
            'text': {'arabic': None, 'translation': text}, 'review': {}, 'extraction': {},
            'source': {'record_url': 'https://example.org/TEST'},
            'source_locator': {'path': relative, 'sha256': sha(self.raw)},
            'language_versions': [{'id': 'TEST:1:uz-Cyrl', 'language': 'uz-Cyrl',
                'text': text, 'source': {'name': 'TEST source'},
                'comments': [{'text': 'TEST pre-existing comment'}]}]}
        self.block = {'text': 'TEST omitted list context', 'decision': 'source_context',
            'source_selector': '.col-md-9', 'child_index': 2, 'tag': 'ol',
            'sha256': sha(b'TEST omitted list context'), 'chars_reviewed': 25,
            'bytes_reviewed': 25, 'reason': 'TEST separately reviewed commentary.'}
        self.decision = {'occurrence_id': self.row['id'], 'decision': 'register',
            'baseline_record_sha256': canonical_hash(self.row), 'source_snapshot': self.snapshot,
            'additional_source_blocks': [self.block],
            'fields': [{'version_id': 'TEST:1:uz-Cyrl', 'language': 'uz-Cyrl',
                'text_sha256': sha(text.encode()), 'chars_reviewed': len(text),
                'bytes_reviewed': len(text.encode()), 'decision': 'whole',
                'reason': 'TEST original primary report.',
                'selected_spans': [{'start': 0, 'end': len(text), 'sha256': sha(text.encode()),
                    'report_type': 'companion_report', 'speaker': 'TEST named speaker'}]}]}
        self.review_path = self.root / FOLDERS['hadisuz'] / 'reviews/source-review-test.json'
        self.review_path.parent.mkdir(parents=True)

    def apply(self):
        self.review_path.write_text(json.dumps({'schema': 'hadith-bank-web-source-review-v1',
            'site': 'hadisuz', 'records': [self.decision]}))
        reviews = SourceReviews(self.root, 'hadisuz')
        result, action = reviews.apply(self.row)
        reviews.finish()
        return result, action

    def test_exact_list_context_is_visible_without_changing_primary_or_search(self):
        before = copy.deepcopy(self.row)
        result, action = self.apply()
        self.assertEqual(self.row, before)
        self.assertEqual(result['id'], self.row['id'])
        self.assertEqual(action, 'register')
        version = result['language_versions'][0]
        self.assertEqual(version['text'], self.row['language_versions'][0]['text'])
        self.assertEqual(version['comments'][0], self.row['language_versions'][0]['comments'][0])
        extra = version['comments'][1]
        self.assertEqual(extra['text'], self.block['text'])
        self.assertEqual(extra['scope'], 'source_context_not_narration')
        self.assertEqual(extra['source_snapshot_sha256'], self.snapshot['sha256'])
        self.assertFalse(extra['source_bound_review']['embedded_report_registration'])
        self.assertNotIn(self.block['text'], str(list(language_search_values(result))))
        self.assertIn(self.block['text'], str(list(language_search_values(result, include_comments=True))))
        second, _ = self.apply()
        self.assertEqual(second, result)

    def test_changed_block_text_or_incomplete_coverage_fails_closed(self):
        self.block['text'] += ' altered'
        with self.assertRaisesRegex(ValueError, 'block text checksum mismatch'):
            self.apply()
        self.block['sha256'] = sha(self.block['text'].encode())
        with self.assertRaisesRegex(ValueError, 'complete review coverage'):
            self.apply()

    def test_changed_snapshot_or_wrong_child_locator_fails_closed(self):
        self.block['child_index'] = 0
        with self.assertRaisesRegex(ValueError, 'exact saved HTML locator'):
            self.apply()
        self.block['child_index'] = 2
        path = self.root / self.snapshot['path']
        path.write_bytes(gzip.compress(self.raw + b' changed', mtime=0))
        with self.assertRaisesRegex(ValueError, 'stored snapshot checksum mismatch'):
            self.apply()


if __name__ == '__main__':
    unittest.main()
