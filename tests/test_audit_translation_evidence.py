import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_translation_evidence import SCHEMA, audit


def sha(value):
    return hashlib.sha256(value).hexdigest()


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'source.txt').write_bytes(b'published source statement')
        self.record = {'id': 'one', 'language': 'ja', 'text_translation': '日本語',
                       'translation_provenance': {'current_policy': {'classification': 'human'},
                                                  'ai_translation': True}}
        self.decision = {'occurrence_id': 'one', 'language': 'ja', 'classification': 'ai',
                         'translation_sha256': sha('日本語'.encode()),
                         'evidence_path': 'source.txt', 'evidence_sha256': sha(b'published source statement'),
                         'evidence_locator': 'page 3', 'assertion': 'Publisher states translation used AI',
                         'reviewer': 'test reviewer'}
        self.ledger = {'schema': SCHEMA, 'decisions': []}

    def test_policy_and_flags_do_not_imply_actual_origin(self):
        result = audit([self.record], self.ledger, self.root)
        self.assertEqual(result['counts'], {'ai': 0, 'human': 0, 'unknown': 1})

    def test_exact_evidence_decision_and_exclusions(self):
        self.ledger['decisions'] = [self.decision]
        rows = [self.record, {'id': 'two', 'language': 'ar', 'text_translation': 'اصل'},
                {'id': 'three', 'language': 'ja', 'text_translation': None}]
        result = audit(rows, self.ledger, self.root)
        self.assertEqual(result['counts'], {'ai': 1, 'human': 0, 'unknown': 0})
        self.assertEqual(result['excluded'], {'arabic_primary': 1, 'missing_primary_translation': 1})
        self.assertEqual(result['evidence_backed_occurrence_ids']['ai'], ['one'])
        self.assertEqual(self.record['translation_provenance']['current_policy']['classification'], 'human')

    def test_byte_evidence_language_and_locator_required(self):
        self.ledger['decisions'] = [self.decision]
        for field, value in [('translation_sha256', sha(b'other')), ('evidence_sha256', sha(b'other')),
                             ('language', 'en'), ('evidence_locator', ''), ('reviewer', '')]:
            bad = copy.deepcopy(self.ledger)
            bad['decisions'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit([self.record], bad, self.root)

    def test_rejects_duplicate_and_unmatched_decisions(self):
        self.ledger['decisions'] = [self.decision, copy.deepcopy(self.decision)]
        with self.assertRaises(ValueError):
            audit([self.record], self.ledger, self.root)
        self.ledger['decisions'] = [self.decision]
        with self.assertRaises(ValueError):
            audit([], self.ledger, self.root)
        with self.assertRaises(ValueError):
            audit([self.record, self.record], self.ledger, self.root)

    def test_rejects_traversal_and_symlink_escape(self):
        self.ledger['decisions'] = [self.decision]
        for name in ('../outside', '/tmp/outside'):
            self.ledger['decisions'][0]['evidence_path'] = name
            with self.assertRaises(ValueError):
                audit([self.record], self.ledger, self.root)
        (self.root / 'link').symlink_to('/etc/passwd')
        self.ledger['decisions'][0]['evidence_path'] = 'link'
        with self.assertRaises(ValueError):
            audit([self.record], self.ledger, self.root)


if __name__ == '__main__':
    unittest.main()
