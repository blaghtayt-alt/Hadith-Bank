"""Owner provenance defaults with synthetic sources and exact history retention."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import current_provenance as provenance
import material_registry
import register_material
import validate_bank_views


def policy():
    return {
        'schema': 'hadith-bank-provenance-policy-v1',
        'decision_date_japan': '2026-11-11', 'source_rules': [],
        'legacy_rule': {'match': {'kind': 'legacy_source_document'},
                        'classification': 'unknown', 'basis': 'TEST old copies unconfirmed'},
        'new_material_rule': {
            'scope': 'registered_nonlegacy_materials_and_counterparts',
            'classification': 'human', 'basis': 'TEST owner default for new books',
            'source_declarations_take_precedence': True},
    }


def record():
    return {
        'id': 'TEST:one', 'source_id': 'TEST-new-book',
        'translation_provenance': {'origin': 'unknown', 'ai_translation': 'unknown'},
        'ai_translation': 'unknown',
        'source': {'name': 'TEST new source', 'original_file': 'materials/test-new/source.pdf'},
        'publication': {'authorized': True, 'manifest_path': 'materials/test-new/manifest.json'},
    }


class CurrentProvenanceTests(unittest.TestCase):
    def test_new_registered_book_defaults_to_human_preserving_processing_history(self):
        sample = record()
        sample.update(extraction={'ocr_used': True, 'method': 'AI OCR', 'model': 'TEST'},
                      review={'reviewer': 'AI', 'model': 'TEST'})
        before = copy.deepcopy(sample)
        provenance.apply_policy(sample, policy())
        self.assertEqual(provenance.classification(sample), 'human')
        del sample['translation_provenance']['current_policy']
        self.assertEqual(sample, before)

    def test_no_policy_or_unregistered_resource_does_not_gain_default(self):
        sample = record()
        before = copy.deepcopy(sample)
        self.assertIsNone(provenance.decision_for(sample, None))
        provenance.apply_policy(sample, None)
        self.assertEqual(sample, before)
        del sample['publication']
        provenance.apply_policy(sample, policy())
        self.assertEqual(provenance.classification(sample), 'unknown')

    def test_legacy_ids_and_copied_quran_keep_unknown_despite_historical_ai(self):
        for identifier in ('legacy-TEST', 'quran-excerpts-TEST'):
            with self.subTest(identifier=identifier):
                sample = record()
                sample['source_id'] = identifier
                sample['ai_translation'] = True
                sample['translation_provenance']['ai_translation'] = True
                provenance.apply_policy(sample, policy())
                self.assertEqual(provenance.classification(sample), 'unknown')
                self.assertIs(sample['translation_provenance']['ai_translation'], True)
                self.assertIs(sample['ai_translation'], True)

    def test_future_old_bank_lineage_cannot_receive_new_book_default(self):
        samples = [record() for _ in range(3)]
        samples[0]['translation_provenance']['origin'] = 'legacy_source_history'
        samples[1]['source']['original_metadata'] = {
            'legacy_document': {'repository': 'blaghtayt-alt/iman-companion', 'revision': 'TEST'}}
        samples[2]['source']['original_metadata'] = {
            'repository': 'blaghtayt-alt/iman-companion', 'commit': 'TEST'}
        for sample in samples:
            provenance.apply_policy(sample, policy())
            self.assertEqual(provenance.classification(sample), 'unknown')

    def test_legacy_document_retains_unknown_in_every_language(self):
        sample = {'kind': 'legacy_source_document', 'language': 'TEST', 'translation_origin': 'ai'}
        provenance.apply_policy(sample, policy())
        self.assertEqual(provenance.classification(sample), 'unknown')
        self.assertEqual(sample['translation_origin'], 'ai')

    def test_explicit_source_declaration_overrides_default_and_scoped_human_rule(self):
        sample = record()
        sample['translation_provenance']['source_declaration'] = {
            'classification': 'ai', 'evidence': 'TEST source preface explicitly credits AI translation.'}
        current = policy()
        current['source_rules'].append({'match': {'source_id': sample['source_id']},
                                        'classification': 'human', 'basis': 'TEST older default'})
        provenance.apply_policy(sample, current)
        self.assertEqual(provenance.classification(sample), 'ai')
        self.assertEqual(sample['translation_provenance']['current_policy']['source_declaration_evidence'],
                         sample['translation_provenance']['source_declaration']['evidence'])

    def test_missing_source_evidence_and_conflicting_declarations_are_rejected(self):
        sample = record()
        sample['translation_provenance']['source_declaration'] = {'classification': 'ai'}
        with self.assertRaisesRegex(ValueError, 'explicit source evidence'):
            provenance.apply_policy(sample, policy())
        sample['translation_provenance']['source_declaration']['evidence'] = 'TEST explicit source page'
        sample['source']['translation_declaration'] = {'classification': 'human', 'evidence': 'TEST conflicting page'}
        with self.assertRaisesRegex(ValueError, 'Conflicting source translation'):
            provenance.apply_policy(sample, policy())

    def test_counterpart_uses_its_own_old_source_identity_not_its_parent(self):
        source = {'text': 'TEST preserved English quotation', 'translation_origin': 'unknown'}
        # Unknown historical attribution alone does not establish an old source.
        self.assertEqual(provenance.counterpart_decision_for(source, policy())['classification'], 'human')
        parent_only = {**source, 'parent_record': {'source_id': 'legacy-TEST', 'ai_translation': True}}
        self.assertEqual(provenance.counterpart_decision_for(parent_only, policy())['classification'], 'human')
        own_old_sources = [
            {**source, 'source_id': 'legacy-TEST', 'translation_origin': 'ai'},
            {**source, 'origin': 'legacy_source_history'},
            {**source, 'source': {'original_metadata': {
                'repository': 'blaghtayt-alt/iman-companion', 'commit': 'TEST'}}},
        ]
        for counterpart in own_old_sources:
            before = copy.deepcopy(counterpart)
            self.assertEqual(provenance.counterpart_decision_for(counterpart, policy())['classification'], 'unknown')
            self.assertEqual(counterpart, before)

    def test_policy_file_requires_narrow_default_and_source_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / provenance.POLICY_PATH
            path.parent.mkdir()
            for key, value in [('scope', 'all_resources'), ('source_declarations_take_precedence', False)]:
                current = policy()
                current['new_material_rule'][key] = value
                path.write_text(json.dumps(current))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    provenance.load_policy(root)
            path.write_text(json.dumps(policy()))
            self.assertEqual(provenance.load_policy(root), policy())


class MixedMaterialProvenanceTests(unittest.TestCase):
    def test_mixed_explicit_ai_and_default_human_are_independently_reconstructable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'materials/test-mixed'
            folder.mkdir(parents=True)
            rows = [
                {'id': 'TEST:explicit-ai', 'text': {'arabic': None, 'translation': 'TEST AI source text'},
                 'ai_translation': True, 'translation_provenance': {
                     'origin': 'ai_translation', 'ai_translation': True,
                     'source_declaration': {'classification': 'ai', 'evidence': 'TEST page 2 translation credit'}}},
                {'id': 'TEST:new-human', 'text': {'arabic': None, 'translation': 'TEST existing source text'},
                 'ai_translation': 'unknown'},
            ]
            canonical = json.dumps(rows).encode()
            (folder / 'records.json').write_bytes(canonical)
            (folder / 'source.txt').write_text('TEST preserved source')
            register_material.register(root, 'materials/test-mixed', 'en', 'test-book', 'test-edition',
                                       'TEST mixed source', 'records.json', 'source.txt')
            path = root / provenance.POLICY_PATH
            path.parent.mkdir()
            path.write_text(json.dumps(policy()))
            registry = material_registry.load_public_materials(root)
            material, projected = registry['materials'][0], registry['groups'][0]
            self.assertEqual([provenance.classification(item) for item in projected], ['ai', 'human'])
            self.assertEqual(material['current_translation_policy']['classification'], 'human')
            self.assertEqual(material['current_translation_origin_counts'], {'ai': 1, 'human': 1})
            self.assertEqual(set(material['current_translation_policy_overrides']), {'TEST:explicit-ai'})
            for position, (original, view) in enumerate(zip(rows, projected)):
                self.assertEqual(material_registry.project_for_material(original, material, position), view)
                expected = validate_bank_views.expected_record(original, material, position, False, {})
                validate_bank_views.compare_projection(view, expected, root, True)
                self.assertEqual(view['ai_translation'], original['ai_translation'])
            self.assertEqual((folder / 'records.json').read_bytes(), canonical)
            self.assertEqual(material_registry.load_public_materials(root), registry)


class SourceDeclarationProjectionTests(unittest.TestCase):
    def check_registered_projection(self, row, manifest_source=None, expected='ai'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'materials/test-declaration'
            folder.mkdir(parents=True)
            canonical = json.dumps([row]).encode()
            (folder / 'records.json').write_bytes(canonical)
            (folder / 'source.txt').write_text('TEST preserved source')
            register_material.register(root, 'materials/test-declaration', 'en', 'test-book', 'test-edition',
                                       'TEST source declaration', 'records.json', 'source.txt')
            manifest_path = folder / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['source'].update(manifest_source or {})
            manifest_path.write_text(json.dumps(manifest))
            manifest_bytes = manifest_path.read_bytes()
            path = root / provenance.POLICY_PATH
            path.parent.mkdir()
            path.write_text(json.dumps(policy()))
            registry = material_registry.load_public_materials(root)
            material, view = registry['materials'][0], registry['groups'][0][0]
            self.assertEqual(provenance.classification(view), expected)
            self.assertEqual(material_registry.project_for_material(row, material, 0), view)
            verified = validate_bank_views.expected_record(row, material, 0, False, {})
            validate_bank_views.compare_projection(view, verified, root, True)
            self.assertEqual((folder / 'records.json').read_bytes(), canonical)
            self.assertEqual(manifest_path.read_bytes(), manifest_bytes)
            self.assertEqual(view['text_translation'], row['text']['translation'])
            return view

    @staticmethod
    def row():
        return {'id': 'TEST:declaration', 'text': {'arabic': None, 'translation': 'TEST source quotation'},
                'ai_translation': 'unknown'}

    def test_every_accepted_canonical_declaration_location_survives_projection(self):
        locations = [
            ('source_declaration',),
            ('translation_provenance', 'source_declaration'),
            ('source', 'translation_declaration'),
            ('source', 'source_declaration'),
            ('source', 'original_metadata', 'translation_declaration'),
            ('source', 'original_metadata', 'source_declaration'),
        ]
        declaration = {'classification': 'ai', 'evidence': 'TEST original source AI translation credit'}
        for location in locations:
            with self.subTest(location=location):
                row = self.row()
                target = row
                for key in location[:-1]:
                    target = target.setdefault(key, {})
                target[location[-1]] = copy.deepcopy(declaration)
                view = self.check_registered_projection(row)
                self.assertEqual(provenance.source_translation_declaration(view), declaration)
                if len(location) == 1:
                    self.assertEqual(view['source_declaration'], declaration)

    def test_both_manifest_source_declaration_fields_survive_projection(self):
        declaration = {'classification': 'ai', 'evidence': 'TEST manifest attribution to source page 3'}
        for field in ('translation_declaration', 'source_declaration'):
            with self.subTest(field=field):
                view = self.check_registered_projection(self.row(), {field: declaration})
                self.assertEqual(view['source'][field], declaration)
                self.assertEqual(provenance.source_translation_declaration(view), declaration)

    def test_existing_explicit_ai_provenance_needs_no_new_declaration_field(self):
        for evidence in [{'basis': 'TEST source explicitly credits AI translation'},
                         {'evidence_ids': ['TEST source page 3']},
                         {'basis': 'TEST source translation statement', 'evidence_ids': ['TEST source page 4']}]:
            with self.subTest(evidence=evidence):
                row = self.row()
                row['ai_translation'] = True
                row['translation_provenance'] = {'origin': 'ai_translation', 'ai_translation': True, **evidence}
                view = self.check_registered_projection(row)
                self.assertNotIn('source_declaration', view['translation_provenance'])
                for key, value in row['translation_provenance'].items():
                    self.assertEqual(view['translation_provenance'][key], value)

    def test_processing_metadata_and_generated_fallback_basis_are_not_source_evidence(self):
        for origin in ('unknown', 'ai_translation'):
            with self.subTest(origin=origin):
                row = self.row()
                row['ai_translation'] = True
                row['translation_provenance'] = {'origin': origin, 'ai_translation': True}
                row['extraction'] = {'ocr_used': True, 'method': 'AI OCR', 'model': 'TEST model'}
                row['review'] = {'reviewer': 'AI', 'model': 'TEST model'}
                self.check_registered_projection(row, expected='human')


if __name__ == '__main__':
    unittest.main()
