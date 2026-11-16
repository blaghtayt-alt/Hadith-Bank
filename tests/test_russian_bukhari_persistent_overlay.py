"""Frozen one-version overlay guards, not a substitute for authoritative rebuild CI."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ru_bukhari_001_persistent_overlay as overlay
import validate_bank_views as validator


class RussianPersistentOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent, cls.candidate, cls.receipt = overlay.load_frozen_candidate(ROOT)

    def test_frozen_source_and_separate_code_authority(self):
        self.assertEqual(overlay.TRUSTED_PINS_SHA256, 'cb6c7196135b34ed6af06db9daad090249862c85dca3bf72b3df5f95f1b3386a')
        self.assertEqual(self.receipt['new_source_occurrences'], 0)
        self.assertEqual(self.receipt['display_sha256'], '1b36b7d0a1d29b0bc47701568e76ab5f110cd79c14f205cca99593084a73a3b4')

    def test_one_append_all_four_originals_and_idempotence(self):
        other = {'id': 'test:unrelated', 'text_translation': 'unchanged'}
        groups = [[copy.deepcopy(self.parent), copy.deepcopy(other)]]
        result = overlay.apply_ru_bukhari_001_overlay(ROOT, groups)
        self.assertEqual(result['action'], 'APPENDED_ONE_RUSSIAN_VERSION')
        self.assertEqual(groups[0][0], self.candidate)
        self.assertEqual(groups[0][1], other)
        self.assertEqual(groups[0][0]['language_versions'][:-1], self.parent['language_versions'])
        for key, value in self.parent.items():
            if key != 'language_versions':
                self.assertEqual(groups[0][0][key], value)
        self.assertEqual(overlay.apply_ru_bukhari_001_overlay(ROOT, groups)['action'], 'IDEMPOTENT_VERIFIED_EXACT_CANDIDATE')
        self.assertEqual(len(groups[0]), 2)

    def test_missing_duplicate_changed_and_conflicting_parent_rejected(self):
        changed = copy.deepcopy(self.parent)
        changed['text_translation'] += ' changed'
        conflicting = copy.deepcopy(self.candidate)
        conflicting['language_versions'][-1]['text'] += ' changed'
        cases = [[], [[self.parent, self.parent]], [[changed]], [[conflicting]]]
        for groups in cases:
            with self.subTest(groups_count=len(groups)):
                before = copy.deepcopy(groups)
                with self.assertRaisesRegex(ValueError, 'PERSISTENT-OVERLAY HOLD'):
                    overlay.apply_ru_bukhari_001_overlay(ROOT, groups)
                self.assertEqual(groups, before)

    def test_evidence_changes_and_coordinated_pin_rewrite_rejected(self):
        for relative in ['api-entry1-field.raw.utf8', 'isnad-1.html', 'source-display-map.json', 'candidate/record-one.json', 'TRUSTED-PINS.json']:
            with self.subTest(path=relative), tempfile.TemporaryDirectory(prefix='ru-overlay-test-') as directory:
                root = Path(directory)
                source = root / overlay.SOURCE_DIR
                shutil.copytree(ROOT / overlay.SOURCE_DIR, source)
                target = source / relative
                target.write_bytes(target.read_bytes() + b' ')
                if relative == 'api-entry1-field.raw.utf8':
                    pins = json.loads((source / 'TRUSTED-PINS.json').read_bytes())
                    pins['raw_russian']['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
                    pins['raw_russian']['bytes'] = target.stat().st_size
                    (source / 'TRUSTED-PINS.json').write_text(json.dumps(pins), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'PERSISTENT-OVERLAY HOLD'):
                    overlay.load_frozen_candidate(root)

    def test_validator_binds_only_the_independently_derived_original_descriptor(self):
        # The full validator must reconstruct this descriptor from the actual
        # registered source in corpus CI. This test checks only its bounded bind.
        p = self.parent
        descriptor = {'id': p['id'], 'authorized_material': True,
            'full_projection_sha256': validator.object_hash({k: v for k, v in p.items() if k != 'counterparts'}),
            **{k: p[k] for k in ['text_arabic', 'text_translation', 'canonical_record_sha256', 'source_id', 'language', 'book_key', 'edition']},
            'locator': p['source']['record_locator'], 'source_file': p['source']['original_file'], 'source_sha256': p['source']['sha256']}
        expected = {overlay.TARGET: copy.deepcopy(descriptor), 'other': {'sentinel': 'unchanged'}}
        overlay.bind_validator_expected(ROOT, expected, validator.object_hash)
        self.assertEqual(expected[overlay.TARGET]['full_projection_sha256'], validator.object_hash({k: v for k, v in self.candidate.items() if k != 'counterparts'}))
        self.assertEqual(expected['other'], {'sentinel': 'unchanged'})
        for field in descriptor:
            with self.subTest(field=field):
                altered = copy.deepcopy(descriptor)
                altered[field] = False if field == 'authorized_material' else 'changed'
                with self.assertRaisesRegex(ValueError, 'PERSISTENT-OVERLAY HOLD'):
                    overlay.bind_validator_expected(ROOT, {overlay.TARGET: altered}, validator.object_hash)
        with self.assertRaisesRegex(ValueError, 'PERSISTENT-OVERLAY HOLD'):
            overlay.bind_validator_expected(ROOT, {}, validator.object_hash)


if __name__ == '__main__':
    unittest.main()
