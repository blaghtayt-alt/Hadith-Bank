"""Automatic integration tests use literal TEST content, never invented Hadith."""
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader
import current_provenance
import material_registry
import refresh_bank
import register_material
import validate_bank_views


class MaterialRegistryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.folder = self.root / 'materials/test-source'
        self.folder.mkdir(parents=True)
        self.record = {'id': 'TEST:source:one', 'text': {'arabic': None, 'translation': 'TEST\nTEST'},
                       'review': {'status': 'pending', 'issues': ['TEST'], 'independent_pro_qc': 'pending',
                                  'release_status': 'private_candidate', 'release_eligible': False},
                       'rights': {'status': 'unknown', 'reuse_basis': None},
                       'translator': {'name': None, 'evidence': None}, 'ai_translation': 'unknown'}
        self.write_records([self.record])
        (self.folder / 'source.txt').write_text('TEST\nTEST', encoding='utf-8')
        self.register()

    def write_records(self, records):
        (self.folder / 'records.json').write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')

    def register(self, replace=False):
        return register_material.register(self.root, 'materials/test-source', 'sw', 'test-book', 'test-edition',
                                          'TEST', 'records.json', 'source.txt', replace=replace)

    def manifest(self):
        return json.loads((self.folder / 'manifest.json').read_text())

    def save_manifest(self, value):
        (self.folder / 'manifest.json').write_text(json.dumps(value), encoding='utf-8')

    def render(self, registry):
        rows = [record for group in registry['groups'] for record in group]
        data = b''.join(json.dumps(record, ensure_ascii=False).encode() + b'\n' for record in rows)
        (self.root / 'search').mkdir(exist_ok=True)
        (self.root / 'search/records.jsonl').write_bytes(data)
        catalog = {'title': 'TEST', 'record_count': len(rows), 'scope': 'public_source_snapshots',
                   'materials': registry['materials'], 'by_language': {'sw': len(rows)},
                   'search': {'records_path': 'search/records.jsonl', 'records_sha256': hashlib.sha256(data).hexdigest(), 'count': len(rows)}}
        (self.root / 'catalog').mkdir(exist_ok=True)
        (self.root / 'catalog/materials.json').write_text(json.dumps(catalog), encoding='utf-8')
        build_reader.build(self.root, self.root / 'hadith-bank-reader.html')
        document = (self.root / 'hadith-bank-reader.html').read_text(encoding='utf-8')
        payload = re.search(r'<script id="hadith-records"[^>]*>(.*?)</script>', document, re.S)
        embedded = json.loads(gzip.decompress(base64.b64decode(payload.group(1))))
        return embedded, document

    def test_new_language_enters_reader_with_exact_text_and_pending_history(self):
        registry = material_registry.load_public_materials(self.root)
        embedded, document = self.render(registry)
        self.assertEqual(len(embedded), 1)
        record = embedded[0]
        self.assertEqual(record['language'], 'sw')
        self.assertEqual(record['text_translation'], self.record['text']['translation'])
        self.assertIsNone(record['text_arabic'])
        for key, value in self.record['review'].items():
            self.assertEqual(record['review'][key], value)
        self.assertEqual(record['rights'], self.record['rights'])
        self.assertEqual(record['translator'], self.record['translator'])
        self.assertTrue(record['publication']['authorized'])
        self.assertFalse(record['publication']['independent_qc_asserted'])
        self.assertFalse(record['publication']['rights_clearance_asserted'])
        expected = validate_bank_views.expected_record(self.record, registry['materials'][0], 0, False, {})
        validate_bank_views.compare_projection(record, expected, self.root, True)
        changed = copy.deepcopy(record)
        changed['review']['independent_pro_qc'] = 'passed'
        with self.assertRaisesRegex(ValueError, 'Public projection fields differ'):
            validate_bank_views.compare_projection(changed, expected, self.root, True)

    def test_rerun_is_idempotent_without_duplicate_occurrences(self):
        first = material_registry.load_public_materials(self.root)
        first_records, first_html = self.render(first)
        second = material_registry.load_public_materials(self.root)
        second_records, second_html = self.render(second)
        self.assertEqual(first_records, second_records)
        self.assertEqual(first_html, second_html)
        self.assertEqual(len({row['id'] for row in second_records}), 1)

    def test_owner_docx_import_preserves_text_without_qc_display_labels(self):
        source = self.folder / 'source.docx'
        source.write_bytes(b'TEST source fixture')
        manifest = self.manifest()
        manifest['source'].update(path='materials/test-source/source.docx', format='docx',
                                  sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        manifest['publication']['decision'] = material_registry.SOURCE_IMPORT_DECISION
        manifest['display_policy'] = {'qc_tags': False,
                                     'decision': 'owner_requested_no_qc_tags_for_non_ocr',
                                     'basis': 'TEST explicit owner source decision'}
        self.save_manifest(manifest)
        registry = material_registry.load_public_materials(self.root)
        record = registry['groups'][0][0]
        self.assertEqual(record['text_translation'], self.record['text']['translation'])
        self.assertFalse(record['display_policy']['qc_tags'])
        self.assertEqual(record['publication']['status'], 'published_source_import')
        self.assertFalse(record['publication']['independent_qc_asserted'])
        self.assertEqual(record['review']['independent_pro_qc'], 'pending')
        self.assertEqual(record['review']['issues'], ['TEST'])

    def test_digital_quote_keeps_normalized_extraction_evidence(self):
        self.record['extraction'] = {
            'method': 'digital_quote_extraction', 'ocr_used': False,
            'is_excerpt': True, 'source_span': 'TEST',
        }
        self.write_records([self.record])
        self.register(replace=True)
        record = material_registry.load_public_materials(self.root)['groups'][0][0]
        self.assertEqual(record['extraction'], {
            'method': 'digital_quote_extraction', 'ocr_used': False,
            'classification': 'digital_text',
            'evidence_fields': ['extraction.ocr_used', 'extraction.method'],
            'conflicting_evidence': False, 'is_excerpt': True,
        })

    def test_native_docx_retains_source_details_and_normalized_evidence(self):
        self.record['extraction'] = {
            'method': 'direct_ooxml', 'ocr_used': False,
            'is_excerpt': False, 'source_paragraph': 7,
        }
        self.write_records([self.record])
        self.register(replace=True)
        record = material_registry.load_public_materials(self.root)['groups'][0][0]
        self.assertEqual(record['extraction'], {
            'method': 'direct_ooxml', 'ocr_used': False,
            'classification': 'digital_text',
            'evidence_fields': ['extraction.ocr_used'],
            'conflicting_evidence': False, 'is_excerpt': False,
            'source_paragraph': 7,
        })

    def test_no_qc_display_policy_cannot_be_applied_to_pdf_intake(self):
        manifest = self.manifest()
        manifest['source']['format'] = 'pdf'
        manifest['publication']['decision'] = material_registry.SOURCE_IMPORT_DECISION
        manifest['display_policy'] = {'qc_tags': False,
                                     'decision': 'owner_requested_no_qc_tags_for_non_ocr',
                                     'basis': 'TEST'}
        self.save_manifest(manifest)
        with self.assertRaisesRegex(ValueError, 'direct DOCX source import'):
            material_registry.load_public_materials(self.root)

    def test_invalid_input_leaves_previously_staged_site_untouched(self):
        site = self.root / '_site'
        site.mkdir()
        (site / 'index.html').write_text('TEST')
        self.write_records([dict(self.record, text={'arabic': None, 'translation': 'TEST TEST'})])
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            refresh_bank.refresh(self.root, '_site')
        self.assertEqual((site / 'index.html').read_text(), 'TEST')

    def test_duplicate_ids_and_unregistered_attachments_fail(self):
        self.write_records([self.record, self.record])
        manifest = self.manifest()
        manifest['records'].update(count=2, sha256=hashlib.sha256((self.folder / 'records.json').read_bytes()).hexdigest())
        self.save_manifest(manifest)
        with self.assertRaisesRegex(ValueError, 'Duplicate material occurrence'):
            material_registry.load_public_materials(self.root)
        self.write_records([self.record]); self.register(replace=True)
        (self.root / 'attachments/not-registered').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'Unregistered attachment package'):
            material_registry.load_public_materials(self.root)

    def test_path_traversal_and_symlinks_rejected(self):
        manifest = self.manifest()
        for path in ('../source.txt', '/tmp/source.txt', 'materials/test-source/../source.txt', 'materials//source.txt'):
            changed = copy.deepcopy(manifest); changed['source']['path'] = path
            self.save_manifest(changed)
            with self.assertRaises(ValueError):
                material_registry.load_public_materials(self.root)
        self.save_manifest(manifest)
        (self.folder / 'source.txt').unlink()
        (self.folder / 'source.txt').symlink_to(self.folder / 'records.json')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            material_registry.load_public_materials(self.root)

    def test_registration_does_not_follow_manifest_symlink(self):
        target = self.folder / 'manifest.json'
        external = self.root / 'TEST-external-manifest.json'
        original = target.read_bytes()
        external.write_bytes(original)
        target.unlink()
        target.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.register(replace=True)
        self.assertEqual(external.read_bytes(), original)

    def test_no_authorization_no_publication(self):
        manifest = self.manifest(); manifest['publication']['authorized'] = False
        self.save_manifest(manifest)
        with self.assertRaisesRegex(ValueError, 'publication.authorized'):
            material_registry.load_public_materials(self.root)

    def test_explicit_replace_preserves_metadata_and_decision(self):
        manifest = self.manifest(); manifest['notes'] = 'TEST'; manifest['source']['publisher'] = 'TEST'
        manifest['publication']['decision_date_japan'] = '2026-01-01'
        self.save_manifest(manifest)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.register()
        self.write_records([dict(self.record, id='TEST:updated')])
        self.register(replace=True)
        after = self.manifest()
        self.assertEqual(after['notes'], 'TEST')
        self.assertEqual(after['source']['publisher'], 'TEST')
        self.assertEqual(after['publication'], manifest['publication'])
        self.assertEqual(after['records']['count'], 1)
        self.assertNotEqual(after['records']['sha256'], manifest['records']['sha256'])

    def test_duplicate_json_keys_rejected(self):
        (self.folder / 'records.json').write_text('[{"id":"TEST","id":"TEST","text":{"arabic":null,"translation":"TEST"}}]')
        manifest = self.manifest()
        manifest['records']['sha256'] = hashlib.sha256((self.folder / 'records.json').read_bytes()).hexdigest()
        self.save_manifest(manifest)
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            material_registry.load_public_materials(self.root)

    def test_scoped_current_origin_preserves_unknown_source_history(self):
        policy = {'schema': 'hadith-bank-provenance-policy-v1', 'decision_date_japan': '2026-11-11',
                  'source_rules': [{'match': {'source_id': self.manifest()['source_id']},
                                    'classification': 'human', 'basis': 'explicit_owner_source_confirmation'}],
                  'legacy_rule': {'match': {'kind': 'legacy_source_document'}, 'classification': 'unknown',
                                  'basis': 'owner_withheld_confirmation_of_old_bank_copies'}}
        (self.root / 'catalog').mkdir()
        (self.root / 'catalog/provenance-policy.json').write_text(json.dumps(policy))
        before = (self.folder / 'records.json').read_bytes()
        registry = material_registry.load_public_materials(self.root)
        embedded, _ = self.render(registry)
        projected = embedded[0]
        self.assertEqual(current_provenance.classification(projected), 'human')
        self.assertEqual(projected['ai_translation'], 'unknown')
        self.assertEqual(projected['translation_provenance']['origin'], 'unknown')
        self.assertEqual(projected['translation_provenance']['ai_translation'], 'unknown')
        self.assertEqual((self.folder / 'records.json').read_bytes(), before)
        expected = validate_bank_views.expected_record(self.record, registry['materials'][0], 0, False, {})
        validate_bank_views.compare_projection(projected, expected, self.root, True)
        unrelated = copy.deepcopy(projected)
        unrelated['source_id'] = 'TEST:unconfirmed-website'
        unrelated['source']['url'] = 'https://example.invalid/TEST'
        del unrelated['translation_provenance']['current_policy']
        current_provenance.apply_policy(unrelated, policy)
        self.assertEqual(current_provenance.classification(unrelated), 'unknown')
        legacy = {'kind': 'legacy_source_document', 'language': 'ja', 'translation_origin': 'human'}
        current_provenance.apply_policy(legacy, policy)
        self.assertEqual(current_provenance.classification(legacy), 'unknown')

    def test_missing_manifest_and_colliding_edition_rejected(self):
        other = self.root / 'materials/test-other'
        other.mkdir()
        with self.assertRaisesRegex(ValueError, 'needs manifest.json'):
            material_registry.load_public_materials(self.root)
        manifest = self.manifest()
        manifest['id'] = 'test-other'; manifest['source_id'] = 'TEST:other'
        manifest['records']['path'] = 'materials/test-other/records.json'
        manifest['source']['path'] = 'materials/test-other/source.txt'
        (other / 'source.txt').write_bytes((self.folder / 'source.txt').read_bytes())
        data = json.dumps([dict(self.record, id='TEST:other')]).encode()
        (other / 'records.json').write_bytes(data)
        manifest['records']['sha256'] = hashlib.sha256(data).hexdigest()
        (other / 'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Duplicate language/book/edition'):
            material_registry.load_public_materials(self.root)

    def test_generated_output_cannot_be_registered_as_source_input(self):
        manifest = self.manifest()
        (self.root / 'search').mkdir()
        generated = self.root / 'search/part-0001.json'
        generated.write_bytes((self.folder / 'records.json').read_bytes())
        for descriptor in ('records', 'source'):
            changed = copy.deepcopy(manifest)
            changed[descriptor]['path'] = 'search/part-0001.json'
            changed[descriptor]['sha256'] = hashlib.sha256(generated.read_bytes()).hexdigest()
            self.save_manifest(changed)
            with self.assertRaisesRegex(ValueError, 'own materials/<slug> directory'):
                material_registry.load_public_materials(self.root)
            self.assertEqual(generated.read_bytes(), (self.folder / 'records.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
