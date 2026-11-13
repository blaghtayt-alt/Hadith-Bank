"""Verify the Fadael intake against its independently preserved source edition.

These are source-preservation and integration-contract checks. They do not claim
new PDF visual inspection, translation certification, or hadith authenticity.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from current_provenance import apply_policy, classification, load_policy
from import_japanese_fadael import (ARCHIVE, AUDIT, CONTEXT, CORRECTED_JSON,
                                   CORRECTED_JSON_SHA256, MANIFEST, NOTES,
                                   ORIGINAL_JSON, PDF_PATH, PDF_SHA256,
                                   PREFIX, PRESERVATION, RECORDS, SLUG,
                                   INTERMEDIATES, INTERMEDIATES_MANIFEST,
                                   deterministic_intermediates, material_descriptor,
                                   run, verify_intermediates)
from material_registry import checked_supporting_files, normalized_projection


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class JapaneseFadaelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = read_json(ROOT / CORRECTED_JSON)
        cls.original = read_json(ROOT / ORIGINAL_JSON)
        cls.rows = [json.loads(line) for line in (ROOT / RECORDS).read_text(encoding='utf-8').splitlines()]
        cls.by_id = {row['id']: row for row in cls.rows}
        cls.by_note = {row['number']['source_note_number']: row for row in cls.rows}
        cls.notes = read_json(ROOT / NOTES)
        cls.context = read_json(ROOT / CONTEXT)
        cls.manifest = read_json(ROOT / MANIFEST)
        cls.audit = read_json(ROOT / AUDIT)

    def test_57_exact_source_occurrences_without_note_19_as_a_hadith(self):
        self.assertEqual(len(self.rows), 57)
        self.assertEqual(len(self.by_id), 57)
        self.assertEqual(set(self.by_note), set(range(1, 59)) - {19})
        self.assertEqual(set(self.by_id), {row['occurrence_id'] for row in self.source['occurrences']})
        for source in self.source['occurrences']:
            row = self.by_id[source['occurrence_id']]
            with self.subTest(record_id=row['id']):
                self.assertEqual(row['text']['translation'], source['corrected_text'])
                self.assertEqual(row['source']['original_text'], source['original_text'])
                self.assertIsNone(row['text']['arabic'])
                self.assertIsNone(row['isnad'])
                self.assertIsNone(row['number']['in_book'])
                self.assertIsNone(row['number']['canonical'])
                self.assertIsNone(row['number']['printed_hadith_number'])
                self.assertEqual(row['source_locator']['source_unit_ids'], source['source_unit_ids'])
                self.assertEqual(row['source_locator']['display_text_sha256'], sha(source['corrected_text'].encode('utf-8')))
        self.assertTrue(self.by_note[33]['text']['translation'].startswith('1－アーイシャ'))
        self.assertEqual(self.by_note[33]['narrator']['name'], 'アーイシャ')
        self.assertEqual(self.by_note[55]['narrator']['name'], 'タルハ')
        self.assertEqual(self.by_note[55]['record_type'], 'companion_report')

    def test_every_original_unit_and_note_is_retained_in_exactly_its_role(self):
        original_units = {u['unit_id']: u for p in self.original['pages'] for u in p['source_units']}
        units = {u['unit_id']: u for p in self.source['pages'] for u in p['source_units']}
        self.assertEqual(len(units), 621)
        self.assertEqual(set(units), set(original_units))
        for identity, unit in units.items():
            self.assertEqual(unit['original_text'], original_units[identity]['text'], identity)
        body_ids = [u for row in self.rows for u in row['source_locator']['source_unit_ids']]
        self.assertEqual(len(body_ids), 376)
        self.assertEqual(len(set(body_ids)), 376)
        self.assertEqual(set(body_ids), {key for key, unit in units.items() if unit['kind'] == 'body_line'})
        context_ids = [unit['unit_id'] for unit in self.context['units']]
        self.assertEqual(len(context_ids), 245)
        self.assertEqual(set(context_ids), set(units) - set(body_ids))
        self.assertFalse(self.context['show_in_html_hadith'])
        self.assertEqual(self.notes, self.source['footnotes'])
        linked = [note['note_number'] for row in self.rows for note in row['footnotes']]
        self.assertEqual(Counter(linked), Counter(range(1, 59)))
        note19 = next(note for note in self.notes if note['note_number'] == 19)
        self.assertEqual(self.by_note[20]['commentary']['translation'], note19['text'])
        self.assertNotIn(note19['text'], self.by_note[20]['text']['translation'])
        self.assertEqual(self.by_note[20]['commentary']['source_note_numbers'], [19])

    def test_reference_corrections_and_parallel_scopes_cannot_be_lost(self):
        self.assertEqual(sum(len(row['references']['items']) for row in self.rows), 93)
        self.assertEqual(self.by_note[5]['references']['corrected_reference_keys'], ['bukhari:5653'])
        self.assertEqual(self.by_note[5]['references']['original_reference_keys'], ['bukhari:5253'])
        self.assertEqual(self.by_note[20]['references']['corrected_reference_keys'], ['bukhari:52', 'muslim:1599'])
        self.assertEqual(self.by_note[20]['references']['original_reference_keys'], ['bukhari:5304', 'muslim:2983'])
        self.assertEqual(self.by_note[35]['references']['corrected_reference_keys'], ['bukhari:5304', 'muslim:2983'])
        self.assertIn('C01', self.by_note[5]['source']['all_correction_ids'])
        self.assertEqual(self.by_note[20]['source']['all_correction_ids'], ['C02', 'C05'])
        self.assertIn('C10', self.by_note[58]['source']['all_correction_ids'])
        for n, scope in [(31, 'broader_supporting_parallel'), (35, 'broader_supporting_parallel_different_narrator')]:
            ref = next(item for item in self.by_note[n]['references']['items'] if item['collection_id'] == 'muslim')
            self.assertEqual(ref['scope'], scope)
            self.assertFalse(ref['is_accepted_canonical_identity'])
            self.assertEqual(ref['matching_role'], 'reference_only')
        secondary = [ref for row in self.rows for ref in row['references']['secondary_edition_references']]
        self.assertEqual({ref['reference_key'] for ref in secondary}, {
            'sahih_sunan_al_tirmidhi:1957', 'al_silsila_al_sahiha:2280',
            'sahih_sunan_al_tirmidhi:2379', 'sahih_sunan_abi_dawud:1300'})
        self.assertTrue(all(ref['verification_status'] == 'not_independently_verified' for ref in secondary))
        self.assertNotEqual(self.by_note[21]['id'], self.by_note[41]['id'])
        self.assertEqual(self.by_note[21]['references']['corrected_reference_keys'], self.by_note[41]['references']['corrected_reference_keys'])

    def test_source_ai_flags_survive_owner_display_policy_and_projection(self):
        material, policy = material_descriptor(self.manifest), load_policy(ROOT)
        projected = []
        for index, row in enumerate(self.rows):
            item = normalized_projection(row, material, index)
            apply_policy(item, policy, registered_material=True)
            projected.append(item)
            n = row['number']['source_note_number']
            expected = True if n in (47, 50) else 'unknown'
            self.assertEqual(row['ai_translation'], expected)
            self.assertEqual(item['ai_translation'], expected)
            self.assertEqual(row['translation_provenance']['original_source_ai_translation'], 'unknown')
            self.assertEqual(item['text_translation'], row['text']['translation'])
            self.assertTrue(item['extraction']['ocr_used'])
            self.assertFalse(item['review']['human_review'])
            self.assertFalse(item['review']['certified_release_eligible'])
            self.assertFalse(item['publication']['independent_qc_asserted'])
            if n in (47, 50):
                provenance = item['translation_provenance']
                self.assertEqual(provenance['source_declaration']['classification'], 'ai')
                self.assertEqual(provenance['ai_generation']['model'], 'GPT-6 Astra Pro')
                self.assertIsNone(provenance['ai_generation']['backend_model_id'])
                self.assertIsNone(provenance['ai_generation']['reasoning_effort'])
                self.assertFalse(provenance['ai_generation']['human_review'])
                self.assertEqual(provenance['ai_generation']['translation_sha256'], sha(item['text_translation'].encode('utf-8')))
            else:
                self.assertNotIn('ai_generation', item['translation_provenance'])
        self.assertEqual(Counter(classification(item) for item in projected), {'human': 55, 'ai': 2})

    def test_original_and_corrected_files_are_checksum_bound_and_offline(self):
        self.assertEqual(sha((ROOT / PDF_PATH).read_bytes()), PDF_SHA256)
        self.assertEqual(sha((ROOT / CORRECTED_JSON).read_bytes()), CORRECTED_JSON_SHA256)
        checked = checked_supporting_files(ROOT, self.manifest, MANIFEST)
        self.assertGreaterEqual(len(checked), len(read_json(ROOT / PRESERVATION)['files']) + 4)
        paths = {item['path'] for item in checked}
        for suffix in ['json', 'pdf', 'docx', 'txt']:
            self.assertIn(ARCHIVE + 'qc_v1/output/ja_ketab_elfadael_corrected.' + suffix, paths)
        self.assertEqual(self.manifest['source']['url'], 'https://islamhouse.com/ja/main')
        self.assertEqual(self.manifest['publication']['decision'], 'owner_requested_public_source_import')
        self.assertFalse(self.manifest['publication']['rights_clearance_asserted'])
        self.assertEqual(self.audit['source_qc_scope']['full_original_pages_rechecked'], 25)
        self.assertEqual(self.audit['source_qc_scope']['source_units_compared'], 621)
        self.assertEqual(self.audit['source_qc_scope']['main_collection_reference_occurrences_checked'], 93)

    def test_intermediate_zip_is_exact_deterministic_and_excludes_web_responses(self):
        import zipfile
        entries = verify_intermediates(ROOT)
        self.assertGreaterEqual(len(entries), 100)
        with zipfile.ZipFile(ROOT / INTERMEDIATES) as archive:
            members = {entry['member']: archive.read(entry['member']) for entry in entries}
        rebuilt, manifest_raw = deterministic_intermediates(members)
        self.assertEqual(rebuilt, (ROOT / INTERMEDIATES).read_bytes())
        self.assertEqual(manifest_raw, (ROOT / INTERMEDIATES_MANIFEST).read_bytes())
        self.assertFalse(any('qc_v1/work/' in name for name in members))
        public_work = ROOT / ARCHIVE / 'qc_v1/work'
        self.assertEqual({p.name for p in public_work.iterdir() if p.is_file()},
                         {'reference_targets.json', 'reference_urls.json'})
        self.assertFalse(any(p.is_file() for p in (ROOT / ARCHIVE / 'work/ja_ketab_elfadael/raw').glob('*')))
        self.assertFalse(any(p.is_file() for p in (ROOT / ARCHIVE / 'work/ja_ketab_elfadael/ocr').glob('*')))

    def test_offline_rerun_is_idempotent_and_preserves_additive_sidecars(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            shutil.copytree(ROOT / PREFIX, root / PREFIX)
            # Parent-owned reviewed group bindings may live outside this material.
            for item in self.manifest.get('supporting_files', []):
                if not item['path'].startswith(PREFIX):
                    target = root / item['path']
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / item['path'], target)
            (root / 'catalog').mkdir()
            shutil.copyfile(ROOT / 'catalog/provenance-policy.json', root / 'catalog/provenance-policy.json')
            sidecar_path = PREFIX + 'test-independent-binding-sidecar.json'
            sidecar_bytes = b'{"scope":"independent reviewed identity decisions"}\n'
            (root / sidecar_path).write_bytes(sidecar_bytes)
            manifest = read_json(root / MANIFEST)
            manifest['test_parent_owned_binding_descriptor'] = {'path': sidecar_path, 'sha256': sha(sidecar_bytes)}
            manifest['supporting_files'].append({'path': sidecar_path, 'sha256': sha(sidecar_bytes), 'size_bytes': len(sidecar_bytes)})
            (root / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
            first = run(root)
            before = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in (root / PREFIX).rglob('*') if p.is_file()}
            second = run(root)
            after = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in (root / PREFIX).rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(first, second)
            self.assertEqual(first['records'], 57)
            self.assertEqual(first['records_sha256'], sha((ROOT / RECORDS).read_bytes()))
            self.assertIn('test_parent_owned_binding_descriptor', read_json(root / MANIFEST))
            self.assertEqual((root / sidecar_path).read_bytes(), sidecar_bytes)
            # Input tampering must fail before an importer can accept new source bytes.
            changed = root / CORRECTED_JSON
            changed.write_bytes(changed.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                run(root)


if __name__ == '__main__':
    unittest.main()
