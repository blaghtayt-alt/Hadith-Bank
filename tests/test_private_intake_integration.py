import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from integrate_private_intakes import integrate, merge_intake_metadata, project, verify_package


class PrivateIntakeIntegrationTests(unittest.TestCase):
    def fixture(self):
        record = {
            'id': 'source-anchor-1', 'language': 'ja', 'source_language_code': 'ja',
            'text': {'arabic': None, 'translation': '原文\nそのまま。'},
            'number': {'canonical': None, 'in_book': None}, 'narrator': {'name': None},
            'book': {'title': '原典'},
            'source': {'title': '原典', 'package_file': 'sources/original.pdf', 'sha256': 'a' * 64, 'format': 'pdf'},
            'translator': {'name': None, 'credited_names': ['翻訳者一', '翻訳者二'], 'evidence': {'pdf_pages': [6]}},
            'ai_translation': False, 'editorial_tags': {'values': ['kind:variant_reference']},
            'source_structure_tags': [], 'review': {'status': 'pending', 'issues': ['arabic_missing'],
                'release_status': 'private_candidate', 'release_eligible': False, 'independent_pro_qc': 'pending'},
            'commentary': {'translation': None}, 'footnotes': [], 'references': [], 'grading': [],
            'page': {'pdf': [7], 'printed': [], 'exact_narration_print_pages': None},
            'related_versions': [], 'record_type': 'variant_reference',
            'source_text': {'arabic_embedded_raw': 'RAW UNAPPROVED'},
        }
        collection = {'book': 'muslim', 'edition': 'pdf-aaa', 'source_id': 'source-ja',
                      'records_path': 'languages/ja/books/muslim/editions/pdf-aaa/records.json',
                      'source_metadata_path': 'source.json'}
        return record, collection

    def test_projection_retains_text_unknown_numbers_and_credit_scope(self):
        record, collection = self.fixture()
        before = copy.deepcopy(record)
        output = project(record, collection, 3, 'attachments/intake')
        self.assertEqual(record, before)
        self.assertEqual(output['text_translation'], record['text']['translation'])
        self.assertIsNone(output['text_arabic'])
        self.assertIsNone(output['number']['canonical'])
        self.assertIsNone(output['translator']['name'])
        self.assertEqual(output['translator']['credited_names'], ['翻訳者一', '翻訳者二'])
        self.assertEqual(output['translation_provenance']['origin'], 'human_translator_credited')
        self.assertEqual(output['source']['record_locator']['json_pointer'], '/3')
        self.assertEqual(output['record_type'], 'variant_reference')
        self.assertEqual(output['source_text_evidence']['json_pointer'], '/3/source_text')
        self.assertNotIn('current_policy', output['review'])
        self.assertFalse(output['review']['certified_release_eligible'])

    def test_unknown_origin_stays_unknown_even_with_credited_name(self):
        record, collection = self.fixture()
        record['ai_translation'] = 'unknown'
        output = project(record, collection, 0, 'attachments/intake')
        self.assertEqual(output['translation_provenance']['origin'], 'unknown')
        self.assertEqual(output['translation_provenance']['ai_translation'], 'unknown')

    def test_missing_private_gate_is_rejected(self):
        record, collection = self.fixture()
        record['review']['release_eligible'] = True
        with self.assertRaisesRegex(ValueError, 'private-candidate'):
            project(record, collection, 0, 'attachments/intake')

    def test_checksum_manifest_rejects_mutation_and_unlisted_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = b'Original source bytes\n'
            (root / 'records.json').write_bytes(data)
            (root / 'SHA256SUMS.json').write_text(json.dumps({'files': [
                {'path': 'records.json', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}))
            self.assertEqual(len(verify_package(root)), 2)
            (root / 'unexpected.txt').write_text('extra')
            with self.assertRaisesRegex(ValueError, 'Unlisted'):
                verify_package(root)
            (root / 'unexpected.txt').unlink()
            (root / 'records.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                verify_package(root)

    def test_public_bank_is_rejected_before_any_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'catalog').mkdir()
            (root / 'catalog/materials.json').write_text(json.dumps({'scope': 'public_source_snapshots'}))
            with self.assertRaisesRegex(ValueError, 'refuses public'):
                integrate(root, [])
            self.assertFalse((root / 'attachments').exists())

    def test_second_additive_intake_preserves_prior_history_and_record_evidence(self):
        first_plan = {'id': 'vi-first', 'count': 2, 'root': 'attachments/vi-first'}
        first_evidence = {'id': 'vi-credit', 'translator': {'name': 'Source translator'},
                          'source_metadata_path': 'attachments/vi-first/catalog/sources.json'}
        history, evidence = merge_intake_metadata({}, [first_plan], [], [first_evidence])
        catalog = {'additive_intake_history': history}
        frozen_catalog, frozen_evidence = copy.deepcopy(catalog), copy.deepcopy(evidence)
        second_plan = {'id': 'ja-second', 'count': 1, 'root': 'attachments/ja-second'}
        second_evidence = {'id': 'ja-credit', 'translator': {'name': None, 'credited_names': ['Source name']}}
        combined_history, combined_evidence = merge_intake_metadata(catalog, [second_plan], evidence, [second_evidence])
        self.assertEqual(catalog, frozen_catalog)
        self.assertEqual(evidence, frozen_evidence)
        self.assertEqual(combined_history[0], history[0])
        self.assertEqual([p['intake_id'] for p in combined_history], ['vi-first', 'ja-second'])
        by_id = {e['id']: e for e in combined_evidence}
        # Existing projections must still resolve their original source-credit evidence.
        earlier_record = {'translation_provenance': {'evidence_ids': ['vi-credit']}}
        self.assertEqual(by_id[earlier_record['translation_provenance']['evidence_ids'][0]], first_evidence)
        self.assertEqual(by_id['ja-credit'], second_evidence)

    def test_repeat_metadata_intake_is_rejected_without_rewriting_prior_evidence(self):
        prior = [{'id': 'same-evidence', 'translator': {'name': 'Original credit'}}]
        before = copy.deepcopy(prior)
        with self.assertRaisesRegex(ValueError, 'evidence identity'):
            merge_intake_metadata({}, [], prior, [{'id': 'same-evidence', 'translator': {'name': 'Replacement'}}])
        self.assertEqual(prior, before)


if __name__ == '__main__':
    unittest.main()
