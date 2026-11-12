"""Synthetic source fixtures; no TEST text is an actual religious quotation."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_fawaz_bulk as importer
import validate_fawaz_sources as validator
from test_fawaz_bulk import catalog, row, source_data


class PartitionValidationTests(unittest.TestCase):
    def test_interleaved_unicode_quotation_and_source_context_reconstruct_original(self):
        original = 'TEST اَ[NOTE]বাংলা😀END'
        start, end = original.index('[NOTE]'), original.index('[NOTE]') + len('[NOTE]')
        spans = {'quotation_spans': [[0, start], [end, len(original)]], 'notes': [[start, end]]}
        result = validator.verify_partition(original, spans, original[:start] + original[end:], ['[NOTE]'])
        self.assertEqual(len(result['quotation_spans']), 2)
        pending = {'quotation_spans': [], 'quotation': [0, 0], 'notes': [[0, len(original)]]}
        validator.verify_partition(original, pending, None, [original], pending=True)
        excerpt = {'quotation_spans': [[start, end]], 'quotation': [start, end],
                   'notes': [[0, start], [end, len(original)]]}
        validator.verify_partition(original, excerpt, '[NOTE]', [original[:start], original[end:]])

    def test_gaps_overlaps_insertions_and_false_pending_quotations_are_rejected(self):
        original = 'TEST quotation|NOTE'
        boundary = original.index('|')
        good = {'quotation': [0, boundary], 'notes': [[boundary, len(original)]]}
        bad_cases = [
            ({'quotation': [0, boundary - 1], 'notes': [[boundary, len(original)]]}, original[:boundary - 1], [original[boundary:]], False),
            ({'quotation': [0, boundary + 1], 'notes': [[boundary, len(original)]]}, original[:boundary + 1], [original[boundary:]], False),
            (good, original[:boundary] + ' TEST INSERTED', [original[boundary:]], False),
            (good, original[:boundary], ['TEST rewritten note'], False),
            (good, None, [original[boundary:]], True),
            ({'quotation_spans': [[0, boundary]], 'quotation': [0, boundary - 1], 'notes': [[boundary, len(original)]]}, original[:boundary], [original[boundary:]], False),
        ]
        for spans, quotation, notes, pending in bad_cases:
            with self.subTest(spans=spans, pending=pending):
                with self.assertRaises(ValueError):
                    validator.verify_partition(original, spans, quotation, notes, pending=pending)

    def test_source_report_components_preserve_explicit_internal_citation_and_notes(self):
        original = 'TEST first report|CITE|TEST second report|TAIL'
        first_end, second_start, quote_end = original.index('|CITE|'), original.index('|CITE|') + 6, original.index('|TAIL')
        info = {'source_report_count': 2, 'source_report_boundaries': [[0, first_end], [second_start, quote_end]],
                'text_spans': {'quotation': [0, quote_end], 'notes': [[quote_end, len(original)]],
                               'retained_internal_citation_spans': [[first_end, second_start]]}}
        self.assertEqual(validator.verify_report_components(original, info, 'multiple_source_reports'), (2, 1))
        contiguous = {'source_report_count': 2, 'source_report_boundaries': [[0, first_end], [first_end, quote_end]],
                      'text_spans': {'quotation': [0, quote_end], 'notes': [[quote_end, len(original)]]}}
        self.assertEqual(validator.verify_report_components(original, contiguous, 'multiple_source_reports'), (2, 0))
        for change in ('missing_internal_citation', 'overlap', 'count', 'status', 'source_note_inclusion', 'nested_evidence'):
            with self.subTest(change=change):
                damaged = copy.deepcopy(info)
                status = 'multiple_source_reports'
                if change == 'missing_internal_citation':
                    damaged['text_spans'].pop('retained_internal_citation_spans')
                elif change == 'overlap':
                    damaged['source_report_boundaries'][0][1] += 1
                elif change == 'count':
                    damaged['source_report_count'] = 3
                elif change == 'status':
                    status = 'bounded'
                elif change == 'source_note_inclusion':
                    damaged['source_report_boundaries'][1][1] = len(original)
                else:
                    damaged['text_spans']['source_report_boundaries'] = [[0, quote_end]]
                with self.assertRaises(ValueError):
                    validator.verify_report_components(original, damaged, status)


class ExportValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'current'
        self.root.mkdir()
        (self.root / 'AGENTS.md').write_text('TEST source-preservation rules')
        self.plan = {'schema': 'hadith-bank-fawaz-bulk-plan-v1', 'enabled': True,
                     'repository': importer.REPOSITORY, 'revision': importer.REVISION,
                     'books': ['malik'], 'languages': list(importer.BASE_LANGUAGES), 'max_books_per_batch': 7}
        importer.save_json(self.root, importer.PLAN, self.plan)
        self.state = {'schema': 'hadith-bank-fawaz-bulk-state-v1', 'revision': importer.REVISION,
                      'inputs': {}, 'stop': None}
        values = {'editions.json': importer.encoded(catalog(['malik'])),
                  'README.md': b'TEST README', 'LICENSE': b'TEST LICENSE',
                  'References.md': b'TEST project credit https://example.invalid/source',
                  'CONTRIBUTING.md': b'TEST provider numbering documentation'}
        self.texts = {'ara': 'TEST قال رسول الله TEST narration',
                      'eng': 'Malik said: TEST source context without a bounded narration.',
                      'urd': 'TEST Urdu source narration'}
        for prefix, text in self.texts.items():
            values['editions/' + prefix + '-malik.json'] = importer.encoded(source_data('malik', [
                row(1, text), row(2, 'TEST ' + prefix + ' independent source statement')]))
        for key, raw in values.items():
            self.state['inputs'][key] = importer.snapshot(self.root, key, raw, {
                'url': importer.provider_url(key), 'retrieved_at': 'TEST'})
        importer.save_json(self.root, importer.IMPORT + '/state.json', self.state)
        self.args = argparse.Namespace(root=self.root, fetch=False, export_only=True,
                                       adopt_dir=None, max_books=None, retry_failed=False)
        summary, code = importer.run(self.args)
        self.assertEqual((code, summary['registered_occurrences'], summary['held_occurrences']), (0, 1, 1))
        self.manifest_path = next((self.root / 'materials').glob('fawaz-*/manifest.json'))
        self.manifest = json.loads(self.manifest_path.read_text())
        self.records_path = self.root / self.manifest['records']['path']
        self.record = json.loads(self.records_path.read_text())

    def save_record(self, record):
        data = importer.encoded(record)
        self.records_path.write_bytes(data)
        manifest = copy.deepcopy(self.manifest)
        manifest['records']['sha256'] = importer.sha(data)
        self.manifest_path.write_bytes(importer.encoded(manifest))

    def test_whole_export_source_context_and_every_old_held_id_are_accounted(self):
        audit = validator.SourceAudit(self.root)
        result = audit.run()
        self.assertEqual((result['registered_occurrences'], result['held_occurrences']), (1, 1))
        self.assertEqual(result['languages']['en']['source_context'], 1)
        self.assertEqual(result['held_all_source_texts_empty'] if 'held_all_source_texts_empty' in result else 0, 0)
        previous = self.base / 'previous'
        shutil.copytree(self.root, previous)
        text = 'TEST ara independent source statement'
        importer.save_json(self.root, 'catalog/fawaz-reviewed-spans.json', {
            'schema': 'hadith-bank-fawaz-reviewed-spans-v1', 'repository': importer.REPOSITORY,
            'revision': importer.REVISION, 'decisions': [{
                'provider_book': 'malik', 'provider_edition': 'ara-malik', 'typed_hadithnumber': '2',
                'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': [[0, len(text)]],
                'review_scope': 'TEST synthetic bookkeeping decision; not an actual religious quotation'}]})
        importer.run(self.args)
        audit = validator.SourceAudit(self.root)
        result = audit.run()
        comparison = validator.reconcile(audit, previous)
        self.assertEqual((result['registered_occurrences'], result['held_occurrences']), (2, 0))
        self.assertEqual(comparison['previous_held'], 1)
        self.assertEqual(comparison['previous_held_now_registered'], 1)
        self.assertEqual(comparison['previous_held_still_held'], 0)
        self.assertEqual(comparison['original_held_reconciliation'][0]['id'], validator.identity('malik', '2'))
        self.assertEqual(comparison['new_provider_ids'], [])

    def test_recomputed_manifest_hash_cannot_hide_text_binding_or_context_corruption(self):
        mutations = ['quotation', 'own_language', 'source_hash', 'pending_text', 'context_note']
        for change in mutations:
            with self.subTest(change=change):
                record = copy.deepcopy(self.record)
                views = {item['language']: item for item in record['language_versions']}
                if change == 'quotation':
                    views['ar']['text'] += ' TEST INVENTED'
                elif change == 'own_language':
                    views['ar']['source']['provider_edition'] = 'eng-malik'
                elif change == 'source_hash':
                    views['ar']['source']['source_text_sha256'] = '0' * 64
                elif change == 'pending_text':
                    views['en']['text'] = self.texts['eng']
                else:
                    views['en']['comments'][0]['text'] = 'TEST changed context'
                self.save_record(record)
                with self.assertRaises(ValueError):
                    validator.SourceAudit(self.root).run()
        self.save_record(self.record)
        validator.SourceAudit(self.root).run()

    def test_provider_content_mismatch_remains_source_context_with_no_arabic_counterpart(self):
        record = copy.deepcopy(self.record)
        versions = {item['language']: item for item in record['language_versions']}
        for code, prefix in (('ar', 'ara'), ('en', 'eng')):
            view = versions[code]
            original = self.texts[prefix]
            view.update(text=None, scope='source_context', quotation_status='content_mismatch',
                        match_status='provider_entry_content_mismatch')
            view['source'].update(quotation_boundary_status='content_mismatch',
                                  quotation_boundary_reason='TEST provider content mismatch',
                                  text_spans={'quotation': [0, 0], 'quotation_spans': [],
                                              'notes': [[0, len(original)]]})
            view['comments'] = [{'text': original, 'scope': 'source_context_not_narration',
                                 'source_url': view['source']['record_url']}] + [
                note for note in view['comments'] if note.get('scope') not in (
                    'source_context_not_narration', 'source_compiler_note')]
            record['source']['language_availability'][code] = 'provider_content_mismatch'
        record['language'] = 'ur'
        record['text']['translation'] = versions['ur']['text']
        record['text']['arabic'] = None
        self.manifest['language'] = 'ur'
        self.save_record(record)
        result = validator.SourceAudit(self.root).run()
        self.assertEqual(result['languages']['ar']['provider_content_mismatch'], 1)
        self.assertEqual(result['languages']['en']['provider_content_mismatch'], 1)
        self.assertEqual(result['languages']['ar'].get('active_quotations', 0), 0)
        self.assertEqual(result['languages']['en'].get('active_quotations', 0), 0)
        self.assertEqual(result['languages']['ur']['active_quotations'], 1)
        for change in ('narration_text', 'counterpart_scope', 'counterpart_status', 'availability', 'arabic_compatibility', 'rewritten_context'):
            with self.subTest(change=change):
                damaged = copy.deepcopy(record)
                view = next(item for item in damaged['language_versions'] if item['language'] == 'ar')
                if change == 'narration_text':
                    view['text'] = self.texts['ara']
                elif change == 'counterpart_scope':
                    view['scope'] = 'external_source'
                elif change == 'counterpart_status':
                    view['match_status'] = 'same_source_record'
                elif change == 'availability':
                    damaged['source']['language_availability']['ar'] = 'available'
                elif change == 'arabic_compatibility':
                    damaged['text']['arabic'] = self.texts['ara']
                else:
                    view['comments'][0]['text'] = 'TEST rewritten unrelated source'
                self.save_record(damaged)
                with self.assertRaises(ValueError):
                    validator.SourceAudit(self.root).run()

    def test_valid_partial_language_extension_does_not_require_acquisition_complete(self):
        self.plan['languages'] = list(importer.LANGUAGES)
        importer.save_json(self.root, importer.PLAN, self.plan)
        summary, _ = importer.run(self.args)
        self.assertFalse(summary['complete'])
        result = validator.SourceAudit(self.root).run()
        self.assertFalse(result['acquisition_complete'])
        self.assertEqual(result['registered_occurrences'], 1)
        self.assertEqual(result['languages']['bn']['edition_pending'], 1)

    def test_saved_optional_edition_does_not_change_legacy_plan_source_inventory(self):
        key = 'editions/ben-malik.json'
        raw = importer.encoded(source_data('malik', [
            row(1, 'TEST Bengali source text'), row(2, 'TEST Bengali independent source statement')]))
        self.state['inputs'][key] = importer.snapshot(self.root, key, raw, {
            'url': importer.provider_url(key), 'retrieved_at': 'TEST'})
        importer.save_json(self.root, importer.IMPORT + '/state.json', self.state)
        summary, _ = importer.run(self.args)
        self.assertTrue(summary['complete'])
        self.assertEqual(summary['by_book']['malik']['processed_languages'], list(importer.BASE_LANGUAGES))
        result = validator.SourceAudit(self.root).run()
        self.assertEqual(result['verified_edition_snapshots'], 4)
        self.assertEqual((result['registered_occurrences'], result['held_occurrences']), (1, 1))
        self.assertNotIn('bn', result['languages'])

    def test_nawawi_missing_urdu_and_named_compiler_are_not_invented_translation_evidence(self):
        target = self.base / 'nawawi'
        target.mkdir()
        (target / 'AGENTS.md').write_text('TEST source-preservation rules')
        plan = {**self.plan, 'books': ['nawawi'], 'languages': list(importer.LANGUAGES)}
        importer.save_json(target, importer.PLAN, plan)
        metadata = catalog(['nawawi'])
        metadata['nawawi']['collection'] = [item for item in metadata['nawawi']['collection']
                                            if item['name'] != 'urd-nawawi']
        for item in metadata['nawawi']['collection']:
            item['author'] = 'Imam Nawawi'
        values = {'editions.json': importer.encoded(metadata), 'README.md': b'TEST README',
                  'LICENSE': b'TEST LICENSE', 'References.md': b'TEST project references',
                  'CONTRIBUTING.md': b'TEST provider numbering'}
        for prefix in ('ara', 'eng', 'ben'):
            text = 'TEST قال رسول الله TEST narration' if prefix == 'ara' else 'TEST ' + prefix + ' source text'
            values['editions/' + prefix + '-nawawi.json'] = importer.encoded(source_data('nawawi', [row(1, text)]))
        state = {'schema': 'hadith-bank-fawaz-bulk-state-v1', 'revision': importer.REVISION, 'inputs': {}, 'stop': None}
        for key, raw in values.items():
            state['inputs'][key] = importer.snapshot(target, key, raw, {'url': importer.provider_url(key), 'retrieved_at': 'TEST'})
        importer.save_json(target, importer.IMPORT + '/state.json', state)
        args = copy.copy(self.args)
        args.root = target
        summary, _ = importer.run(args)
        self.assertTrue(summary['complete'])
        result = validator.SourceAudit(target).run()
        self.assertEqual(result['languages']['ur']['edition_not_published_in_pinned_catalog'], 1)
        manifest_path = next((target / 'materials').glob('fawaz-*/manifest.json'))
        manifest = json.loads(manifest_path.read_text())
        path = target / manifest['records']['path']
        record = json.loads(path.read_text())
        english = next(item for item in record['language_versions'] if item['language'] == 'en')
        self.assertIsNone(english['source']['translator']['name'])
        self.assertEqual(english['source']['catalog_author_as_supplied'], 'Imam Nawawi')
        english['source']['translator']['name'] = 'Imam Nawawi'
        data = importer.encoded(record)
        path.write_bytes(data)
        manifest['records']['sha256'] = importer.sha(data)
        manifest_path.write_bytes(importer.encoded(manifest))
        with self.assertRaisesRegex(ValueError, 'translator'):
            validator.SourceAudit(target).run()

    def test_missing_language_dependency_is_rejected_even_with_recomputed_index_hash(self):
        path = self.root / self.manifest['source']['path']
        index = json.loads(path.read_text())
        removed = index['source_snapshots'].pop('editions/eng-malik.json')
        data = importer.encoded(index)
        path.write_bytes(data)
        manifest = copy.deepcopy(self.manifest)
        manifest['source']['sha256'] = importer.sha(data)
        manifest['supporting_files'] = [item for item in manifest['supporting_files'] if item['path'] != removed['path']]
        self.manifest_path.write_bytes(importer.encoded(manifest))
        with self.assertRaisesRegex(ValueError, 'omits a processed language'):
            validator.SourceAudit(self.root).run()


if __name__ == '__main__':
    unittest.main()
