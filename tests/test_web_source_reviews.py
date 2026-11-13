"""Evidence-binding and reader isolation checks using synthetic TEST text."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from language_versions import validate_language_versions, quotation_parts, language_search_values
from web_source_reviews import SourceReviews, canonical_hash, sha, FOLDERS
from web_import_batch import command, has_review_export_work


class SourceReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.row = {'id': 'TEST:1', 'language': 'uz', 'source_language_code': 'uz-Cyrl',
            'text': {'arabic': 'TEST first | NOTE | TEST second', 'translation': 'UNREAD SIBLING'},
            'source_locator': {'path': 'snapshots/TEST.gz', 'sha256': 'a' * 64},
            'review': {'independent_pro_qc': 'not_performed'}, 'extraction': {},
            'language_versions': [
                {'id': 'TEST:1:ar', 'language': 'ar', 'text': 'TEST first | NOTE | TEST second',
                 'source': {'name': 'TEST publisher', 'url': 'https://example.org/TEST'},
                 'comments': [{'text': 'TEST commentary'}]},
                {'id': 'TEST:1:uz-Cyrl', 'language': 'uz-Cyrl', 'text': 'UNREAD SIBLING',
                 'source': {'name': 'TEST publisher', 'url': 'https://example.org/TEST'}, 'comments': []}]}
        self.path = self.root / FOLDERS['islom'] / 'reviews/source-review-test.json'
        self.path.parent.mkdir(parents=True)

    def field(self, spans):
        text = self.row['language_versions'][0]['text']
        return {'version_id': 'TEST:1:ar', 'language': 'ar',
            'field_path': ['language_versions', 0, 'text'], 'text_sha256': sha(text.encode()),
            'chars_reviewed': len(text), 'bytes_reviewed': len(text.encode()),
            'decision': 'excerpts', 'reason': 'TEST source-attributed separate reports.',
            'selected_spans': [{'start': a, 'end': b, 'sha256': sha(text[a:b].encode()),
                'component_id': 'TEST-component-' + str(i), 'report_type': 'companion_report',
                'speaker': 'TEST named speaker'} for i, (a, b) in enumerate(spans)]}

    def save(self, field=None, action='register'):
        decision = {'occurrence_id': self.row['id'], 'decision': action,
            'baseline_record_sha256': canonical_hash(self.row),
            'source_snapshot': self.row['source_locator'],
            'fields': [field or self.field([(0, 10), (20, len(self.row['language_versions'][0]['text']))])]}
        self.path.write_text(json.dumps({'schema': 'hadith-bank-web-source-review-v1',
            'site': 'islom', 'records': [decision]}))
        return decision

    def test_exact_components_preserve_original_and_exclude_unread_sibling_from_search(self):
        self.save()
        original = copy.deepcopy(self.row)
        reviews = SourceReviews(self.root, 'islom')
        result, action = reviews.apply(self.row)
        reviews.finish()
        self.assertEqual(self.row, original)
        self.assertEqual(action, 'register')
        validate_language_versions(result['language_versions'])
        first, sibling = result['language_versions']
        self.assertEqual([p['text'] for p in quotation_parts(first)], ['TEST first', 'TEST second'])
        self.assertIsNone(sibling['text'])
        self.assertEqual(sibling['comments'][0]['text'], 'UNREAD SIBLING')
        self.assertIsNone(result['text']['translation'])
        self.assertNotIn('UNREAD SIBLING', str(list(language_search_values(result))))
        self.assertNotIn('NOTE', str(list(language_search_values(result))))
        self.assertIn('UNREAD SIBLING', str(list(language_search_values(result, include_comments=True))))
        self.assertIn('NOTE', first['comments'][-1]['text'])
        self.assertFalse(result['review']['certified_release_eligible'])

    def test_changed_record_or_field_or_selected_span_fails_closed(self):
        self.save()
        changed = copy.deepcopy(self.row)
        changed['language_versions'][0]['text'] += ' altered'
        with self.assertRaisesRegex(ValueError, 'baseline record changed'):
            SourceReviews(self.root, 'islom').apply(changed)
        field = self.field([(0, 10)])
        field['text_sha256'] = '0' * 64
        self.save(field)
        with self.assertRaisesRegex(ValueError, 'field hash mismatch'):
            SourceReviews(self.root, 'islom').apply(self.row)
        field = self.field([(0, 10)])
        field['selected_spans'][0]['sha256'] = '0' * 64
        self.save(field)
        with self.assertRaisesRegex(ValueError, 'span hash mismatch'):
            SourceReviews(self.root, 'islom').apply(self.row)

    def test_unread_or_partial_whole_approval_is_rejected(self):
        field = self.field([(0, 10)])
        field['reviewed'] = False
        self.save(field)
        with self.assertRaisesRegex(ValueError, 'unread field'):
            SourceReviews(self.root, 'islom').apply(self.row)
        field.pop('reviewed')
        field['decision'] = 'whole'
        self.save(field)
        with self.assertRaisesRegex(ValueError, 'complete field'):
            SourceReviews(self.root, 'islom').apply(self.row)

    def test_reviewed_source_script_correction_preserves_language_identity_and_text(self):
        self.row['language_versions'][0]['script'] = 'Arab'
        field = self.field([(0, len(self.row['language_versions'][0]['text']))])
        field.update(decision='whole', observed_script='Latn', source_script_note='TEST original field uses Latin script.')
        self.save(field)
        result, _ = SourceReviews(self.root, 'islom').apply(self.row)
        version = result['language_versions'][0]
        self.assertEqual(version['id'], 'TEST:1:ar')
        self.assertEqual(version['language'], 'ar')
        self.assertEqual(version['text'], self.row['language_versions'][0]['text'])
        self.assertEqual(version['script'], 'Latn')
        self.assertEqual(version['source']['importer_script_before_review'], 'Arab')
        self.assertIn(field['source_script_note'], version['source']['report_classification_note'])

    def test_context_comment_review_cannot_promote_embedded_report(self):
        self.save()
        data = json.loads(self.path.read_text())
        comment = 'TEST commentary'
        field = {'version_id': 'TEST:1:ar', 'language': 'ar',
            'field_path': ['language_versions', 0, 'comments', 0, 'text'],
            'text_sha256': sha(comment.encode()), 'chars_reviewed': len(comment),
            'bytes_reviewed': len(comment.encode()), 'decision': 'source_context',
            'selected_spans': [], 'reason': 'TEST comment retained separately.'}
        data['records'][0]['fields'].append(field)
        self.path.write_text(json.dumps(data))
        result, _ = SourceReviews(self.root, 'islom').apply(self.row)
        reviewed = result['language_versions'][0]['comments'][0]
        self.assertEqual(reviewed['text'], comment)
        self.assertFalse(reviewed['source_bound_review']['embedded_report_registration'])
        field['selected_spans'] = [{'start': 0, 'end': 4}]
        self.path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'cannot silently register'):
            SourceReviews(self.root, 'islom').apply(self.row)

    def test_missing_review_occurrence_is_not_silently_ignored(self):
        self.save()
        with self.assertRaisesRegex(ValueError, 'absent from source'):
            SourceReviews(self.root, 'islom').finish()

    def test_compressed_decision_binds_immutable_baseline_ledger(self):
        self.save()
        data = json.loads(self.path.read_text())
        ledger = self.path.parent / 'original-source.jsonl.gz'
        ledger.write_bytes(gzip.compress(b'TEST immutable baseline\n', mtime=0))
        data['source_ledger_path'] = ledger.relative_to(self.root).as_posix()
        data['source_ledger_sha256'] = sha(ledger.read_bytes())
        compressed = self.path.with_suffix('.json.gz')
        compressed.write_bytes(gzip.compress(json.dumps(data).encode(), mtime=0))
        self.path.unlink()
        reviews = SourceReviews(self.root, 'islom')
        result, action = reviews.apply(self.row)
        reviews.finish()
        self.assertEqual(action, 'register')
        self.assertEqual(result['review']['source_bound_review']['compression'], 'gzip')
        ledger.write_bytes(b'TEST changed baseline')
        with self.assertRaisesRegex(ValueError, 'baseline ledger checksum mismatch'):
            SourceReviews(self.root, 'islom')

    def test_new_review_requests_one_offline_export_without_requeueing_failed_urls(self):
        self.save()
        self.assertTrue(has_review_export_work(self.root, 'islom'))
        progress = self.root / FOLDERS['islom'] / 'progress.json'
        reviews = SourceReviews(self.root, 'islom')
        progress.write_text(json.dumps({'source_review_inputs': reviews.supporting_files(),
                                       'source_review_engine_sha256': reviews.engine_sha256}))
        self.assertFalse(has_review_export_work(self.root, 'islom'))
        args = command(self.root, 'islom', {'max_requests_per_batch': 3,
            'max_seconds_per_batch': 60, 'delay_seconds': 1.25, 'export_only': True})
        self.assertIn('--export-only', args)
        args = command(self.root, 'deenhindi', {'max_requests_per_batch': 3,
            'max_seconds_per_batch': 60, 'delay_seconds': 1.25, 'export_only': True})
        self.assertEqual(args[args.index('--max-records') + 1], '0')


if __name__ == '__main__':
    unittest.main()
