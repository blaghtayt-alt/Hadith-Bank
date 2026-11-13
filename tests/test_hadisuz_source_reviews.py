"""Offline export checks for explicit, hash-bound Hadis.uz source reviews."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_hadisuz as importer


def sha(value):
    return hashlib.sha256(value).hexdigest()


class HadisuzSourceReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.worker = importer.Importer(self.root, max_pages=1, max_seconds=30, delay=1)

    def source(self, number, primary, note='TEST separate scholarly comment.'):
        url = importer.ORIGIN + '/hadith/' + str(number)
        raw = ('<h1>TEST heading</h1><div class="col-md-9">'
               '<p><i>TEST source chain.</i> <b>' + primary + '</b></p>'
               '<p>' + note + '</p><hr></div>').encode('utf-8')
        snapshot = self.worker.preserve(raw, url, {
            'retrieved_at': '2026-11-13T00:00:00Z', 'status': 200,
            'final_url': url, 'content_type': 'text/html; charset=utf-8'})
        self.worker.state['snapshots'][url] = snapshot
        self.worker.enqueue(url, 'detail', importer.CATALOG)
        task = next(t for t in self.worker.state['tasks'] if t['url'] == url)
        self.worker.process(task, raw, snapshot)
        entry = self.worker.state['entries'][str(number)]
        parsed = json.loads(self.worker.checked(entry))
        return importer.record_from(parsed, snapshot, [], [])

    def decision(self, row, action='register', end=None):
        version = row['language_versions'][0]
        text = version['text']
        selected = action == 'register'
        end = len(text) if end is None else end
        field = {
            'field_path': ['language_versions', 0, 'text'],
            'version_id': version['id'], 'language': version['language'],
            'text_sha256': sha(text.encode('utf-8')), 'chars_reviewed': len(text),
            'bytes_reviewed': len(text.encode('utf-8')),
            'decision': ('whole' if end == len(text) else 'excerpts') if selected else 'source_context',
            'selected_spans': ([{'start': 0, 'end': end,
                'sha256': sha(text[:end].encode('utf-8')),
                'report_type': 'companion_report', 'speaker': 'TEST named Companion'}]
                if selected else []),
            'reason': 'TEST explicit source-bound classification and boundary review.',
        }
        fields = [field]
        for index, comment in enumerate(version.get('comments', [])):
            content = comment['text']
            fields.append({
                'field_path': ['language_versions', 0, 'comments', index, 'text'],
                'version_id': version['id'], 'language': version['language'],
                'text_sha256': sha(content.encode('utf-8')), 'chars_reviewed': len(content),
                'bytes_reviewed': len(content.encode('utf-8')), 'decision': 'source_context',
                'selected_spans': [], 'reason': 'TEST commentary remains separately preserved.',
            })
        return {
            'occurrence_id': row['id'], 'book_key': 'tirmidhi', 'overalldecision': action,
            'baseline_record_sha256': sha(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                                      separators=(',', ':')).encode('utf-8')),
            'source_snapshot': {key: row['source_locator'][key] for key in ('path', 'sha256')},
            'fields': fields,
        }

    def write_reviews(self, decisions, originals):
        folder = self.worker.folder / 'reviews'
        folder.mkdir(parents=True, exist_ok=True)
        original = gzip.compress(b''.join(importer.row_bytes(row) for row in originals), mtime=0)
        (folder / 'original-held-records.jsonl.gz').write_bytes(original)
        (folder / 'coverage.json').write_bytes(importer.json_bytes({'reviewed': len(decisions)}))
        (folder / 'source-review-test.json').write_bytes(importer.json_bytes({
            'schema': 'hadith-bank-web-source-review-v1', 'source': 'hadisuz',
            'source_ledger_path': str((folder / 'original-held-records.jsonl.gz').relative_to(self.root)),
            'source_ledger_sha256': sha(original), 'offset_unit': 'python_unicode_codepoints',
            'decisions': decisions,
        }))
        return folder

    def rows(self, path):
        data = path.read_bytes()
        if path.suffix == '.gz':
            data = gzip.decompress(data)
        return [json.loads(line) for line in data.splitlines()]

    def files(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_explicit_decisions_control_registration_and_preserve_all_occurrences(self):
        whole = self.source(1, 'TEST Companion said this.')
        excerpt = self.source(2, 'TEST Companion report. TEST trailing source context:')
        held = self.source(3, 'TEST Расулуллоҳ unresolved review attribution.')
        excluded = self.source(4, 'TEST Расулуллоҳ mentioned in compiler discussion.')
        legacy = self.source(5, 'TEST Расулуллоҳ explicit legacy report.')
        pending = self.source(6, 'TEST unreviewed statement.')
        end = excerpt['text']['translation'].index(' TEST trailing')
        self.write_reviews([
            self.decision(whole), self.decision(excerpt, end=end),
            self.decision(held, 'hold'), self.decision(excluded, 'exclude'),
        ], [whole, excerpt, held, excluded])
        before_sources = {p: b for p, b in self.files().items()
                          if '/snapshots/' in p or '/parsed/' in p or '/reviews/' in p}
        with mock.patch.object(self.worker.opener, 'open', side_effect=AssertionError('Offline export requested HTTP')):
            report = self.worker.export()
        self.assertEqual(report['source_entries_obtained'], 6)
        self.assertEqual(report['registered_source_occurrences'], 3)
        self.assertEqual(report['prophetic_source_entries_registered'], 3)
        self.assertEqual(report['classification_pending_hidden'], 2)
        self.assertEqual(report['non_narration_source_entries'], 1)
        self.assertIn('actual report type', report['scope_note'])
        self.assertEqual(len(report['source_review_inputs']), 3)
        registered = {r['id']: r for r in self.rows(self.root / 'materials' / importer.SLUG / 'records.jsonl')}
        self.assertEqual(set(registered), {whole['id'], excerpt['id'], legacy['id']})
        version = registered[whole['id']]['language_versions'][0]
        self.assertEqual(version['text'], whole['language_versions'][0]['text'])
        self.assertEqual(version['source']['report_type'], 'companion_report')
        self.assertEqual(version['source']['report_component_classifications'][0]['speaker_description'],
                         'TEST named Companion')
        self.assertEqual(version['comments'][0]['text'], whole['language_versions'][0]['comments'][0]['text'])
        selected = registered[excerpt['id']]['language_versions'][0]
        self.assertEqual(selected['text'], excerpt['text']['translation'][:end])
        self.assertEqual(selected['comments'][-1]['text'], excerpt['text']['translation'][end:])
        self.assertEqual(registered[excerpt['id']]['number'], excerpt['number'])
        self.assertEqual({r['id'] for r in self.rows(self.worker.folder / 'held-records.jsonl.gz')},
                         {held['id'], pending['id']})
        self.assertEqual([r['id'] for r in self.rows(self.worker.folder / 'excluded-records.jsonl.gz')],
                         [excluded['id']])
        for path, data in before_sources.items():
            self.assertEqual((self.root / path).read_bytes(), data, path)

    def test_review_dependencies_reach_every_shard_and_repeat_export_is_identical(self):
        reviewed = self.source(1, 'TEST Companion report.')
        legacy = self.source(2, 'TEST Расулуллоҳ explicit report.')
        self.worker.state['part_assignments'] = {reviewed['id']: 1, legacy['id']: 2}
        folder = self.write_reviews([self.decision(reviewed)], [reviewed])
        evidence = {str(p.relative_to(self.root)): sha(p.read_bytes()) for p in folder.iterdir()}
        report = self.worker.export()
        manifests = list((self.root / 'materials').glob('*/manifest.json'))
        self.assertEqual(len(manifests), 2)
        for path in manifests:
            manifest = json.loads(path.read_text())
            supported = {item['path']: item['sha256'] for item in manifest['supporting_files']}
            for name, checksum in evidence.items():
                self.assertEqual(supported[name], checksum)
            self.assertEqual(manifest['extraction_scope']['source_review_inputs'], report['source_review_inputs'])
        before = self.files()
        resumed = importer.Importer(self.root, max_pages=1, max_seconds=30, delay=1)
        with mock.patch.object(resumed.opener, 'open', side_effect=AssertionError('Offline resume requested HTTP')):
            self.assertEqual(resumed.export(), report)
        self.assertEqual(self.files(), before)

    def test_unknown_review_identity_rejects_export_before_changing_existing_artifacts(self):
        row = self.source(1, 'TEST Companion report.')
        self.worker.export()
        decision = self.decision(row)
        decision['occurrence_id'] = 'hadisuz:tirmidhi:999'
        self.write_reviews([decision], [row])
        before = self.files()
        assignments = copy.deepcopy(self.worker.state['part_assignments'])
        with self.assertRaisesRegex(ValueError, 'review IDs absent from source'):
            self.worker.export()
        self.assertEqual(self.files(), before)
        self.assertEqual(self.worker.state['part_assignments'], assignments)

    def test_changed_review_baseline_cannot_publish_or_replace_existing_exports(self):
        row = self.source(1, 'TEST Companion report.')
        self.worker.export()
        decision = self.decision(row)
        decision['baseline_record_sha256'] = '0' * 64
        self.write_reviews([decision], [row])
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'baseline record changed'):
            self.worker.export()
        self.assertEqual(self.files(), before)

    def test_review_does_not_bypass_original_snapshot_checksum(self):
        row = self.source(1, 'TEST Companion report.')
        self.write_reviews([self.decision(row)], [row])
        snapshot = self.root / row['source_locator']['path']
        snapshot.write_bytes(b'TEST changed preserved source')
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.worker.export()
        self.assertEqual(self.files(), before)


if __name__ == '__main__':
    unittest.main()
