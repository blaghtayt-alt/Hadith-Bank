"""Bounded checks against retained source records and the reviewed ledger."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_translation_evidence import apply_projected_decisions
from current_provenance import apply_policy, load_policy
from material_registry import project_for_material, publication

LEDGER = 'catalog/translation-evidence-decisions-20261113.json'
FILES = [
    'materials/legacy-fa-bukhari/records.json', 'materials/legacy-fa-muslim/records.json',
    'materials/legacy-hi-bukhari/records.json', 'materials/legacy-hi-muslim/records.json',
    'materials/legacy-zh-CN-bukhari/records.json', 'materials/legacy-zh-CN-muslim/records.json',
    'materials/legacy-ja-bukhari/records.json', 'materials/legacy-ja-unclassified/records.json',
    'materials/legacy-uz-unclassified/records.json',
]


class RealRecordProjectionTest(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads((ROOT / LEDGER).read_text(encoding='utf-8'))
        self.materials = [{} for _ in FILES]
        self.groups = []
        for relative in FILES:
            rows = json.loads((ROOT / relative).read_text(encoding='utf-8'))
            self.groups.append([{'id': row['id'], 'language': row['language'],
                                 'text_translation': row['text']['translation'],
                                 'translation_provenance': copy.deepcopy(row['translation_provenance'])}
                                for row in rows])

    def test_only_exact_reviewed_occurrences_change(self):
        before = copy.deepcopy(self.groups)
        report = apply_projected_decisions(self.materials, self.groups, self.ledger, ROOT, LEDGER)
        self.assertEqual(report['counts']['ai'], 187)
        self.assertEqual(report['counts']['human'], 4)
        decisions = {d['occurrence_id']: d for d in self.ledger['decisions']}
        changed = 0
        for oldgroup, newgroup, material in zip(before, self.groups, self.materials):
            for old, new in zip(oldgroup, newgroup):
                entry = decisions.get(old['id'])
                if not entry:
                    self.assertEqual(old, new)
                    continue
                changed += 1
                self.assertEqual(new['text_translation'], old['text_translation'])
                self.assertEqual(new['id'], old['id'])
                p = new['translation_provenance']
                self.assertEqual(p['ai_translation'], old['translation_provenance']['ai_translation'])
                self.assertEqual(p['current_policy']['classification'], entry['classification'])
                self.assertEqual(p['current_policy']['previous_display_policy'], old['translation_provenance'].get('current_policy'))
                self.assertEqual(material['current_translation_policy_overrides'][old['id']], p['current_policy'])
        self.assertEqual(changed, 191)
        copy_after = copy.deepcopy(self.groups)
        apply_projected_decisions(self.materials, self.groups, self.ledger, ROOT, LEDGER)
        self.assertEqual(self.groups, copy_after)

    def test_normal_projection_and_validator_reconstruction_agree(self):
        policy = load_policy(ROOT)
        materials, groups, source_rows = [], [], []
        for relative in FILES:
            manifest_path = str(Path(relative).parent / 'manifest.json')
            manifest = json.loads((ROOT / manifest_path).read_text(encoding='utf-8'))
            rows = json.loads((ROOT / relative).read_text(encoding='utf-8'))
            material = {'adapter': 'records-v1', 'dataset_id': manifest['source_id'],
                        'language': manifest['language'], 'book_key': manifest['book'],
                        'edition': manifest['edition'], 'canonical_records_path': relative,
                        'source_file': manifest['source']['path'], 'source_sha256': manifest['source']['sha256'],
                        'source_descriptor': manifest['source'],
                        'publication': publication(manifest, manifest_path)}
            projected = [project_for_material(row, material, i) for i, row in enumerate(rows)]
            for record in projected:
                apply_policy(record, policy, registered_material=True)
            # The validator applies this owner policy through the material descriptor.
            material['current_translation_policy'] = copy.deepcopy(projected[0]['translation_provenance']['current_policy'])
            materials.append(material); groups.append(projected); source_rows.append(rows)
        apply_projected_decisions(materials, groups, self.ledger, ROOT, LEDGER)
        for material, group, rows in zip(materials, groups, source_rows):
            for i, (record, row) in enumerate(zip(group, rows)):
                self.assertEqual(project_for_material(row, material, i), record)

    def test_stale_translation_rejects_before_any_projection_change(self):
        self.groups[-1][0]['text_translation'] = 'changed text'
        # Force the stale case on a known decision, regardless of ordering.
        target_id = self.ledger['decisions'][0]['occurrence_id']
        target = next(r for group in self.groups for r in group if r['id'] == target_id)
        target['text_translation'] += ' changed'
        before = copy.deepcopy(self.groups)
        with self.assertRaises(ValueError):
            apply_projected_decisions(self.materials, self.groups, self.ledger, ROOT, LEDGER)
        self.assertEqual(self.groups, before)
        self.assertEqual(self.materials, [{} for _ in FILES])

    def test_unmatched_decision_rejected_before_change(self):
        self.ledger['decisions'][0]['occurrence_id'] = 'not-in-bank'
        before = copy.deepcopy(self.groups)
        with self.assertRaises(ValueError):
            apply_projected_decisions(self.materials, self.groups, self.ledger, ROOT, LEDGER)
        self.assertEqual(self.groups, before)


if __name__ == '__main__':
    unittest.main()
