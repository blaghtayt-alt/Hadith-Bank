"""Verify every legacy excerpt and promoted credit against preserved source bytes."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from extract_legacy_hadith import Extractor, PIN, REPO, git_sha, pointer_get, selected_parent_person


class LegacyHadithExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.documents, cls.manifests = [], {}, []
        seen_bundles = set()
        for path in sorted((ROOT / 'materials').glob('legacy-*/manifest.json')):
            manifest = json.loads(path.read_text(encoding='utf-8'))
            cls.manifests.append(manifest)
            cls.rows.extend(json.loads((ROOT / manifest['records']['path']).read_text(encoding='utf-8')))
            source_path = ROOT / manifest['source']['path']
            raw_bundle = source_path.read_bytes()
            digest = hashlib.sha256(raw_bundle).hexdigest()
            if digest in seen_bundles:
                continue
            seen_bundles.add(digest)
            for entry in json.loads(raw_bundle)['documents']:
                key = entry['repository'], entry['path']
                prior = cls.documents.setdefault(key, entry)
                if prior != entry:
                    raise AssertionError('Conflicting source document: ' + str(key))
        cls.by_id = {r['id']: r for r in cls.rows}

    def resolve(self, locator):
        source = self.documents[locator['repository'], locator['path']]
        self.assertEqual(source['sha256'], locator['sha256'])
        self.assertEqual(source['git_blob_sha'], locator['git_blob_sha'])
        value = pointer_get(json.loads(source['raw_utf8']), locator['json_pointer'])
        if 'code_points' in locator:
            value = value[slice(*locator['code_points'])]
        return value

    def test_all_bundled_bytes_and_material_hashes(self):
        for entry in self.documents.values():
            raw = entry['raw_utf8'].encode('utf-8')
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
            self.assertEqual(git_sha(raw), entry['git_blob_sha'])
            if entry['repository'] == REPO:
                self.assertEqual(entry['revision'], PIN)
        for manifest in self.manifests:
            for key in ('source', 'records'):
                self.assertEqual(hashlib.sha256((ROOT / manifest[key]['path']).read_bytes()).hexdigest(), manifest[key]['sha256'])
            rows = json.loads((ROOT / manifest['records']['path']).read_text(encoding='utf-8'))
            self.assertEqual(len(rows), manifest['records']['count'])
            self.assertTrue(all(r['book_key'] == manifest['book'] for r in rows))

    def test_every_translation_and_arabic_field_has_exact_scalar_location(self):
        for row in self.rows:
            with self.subTest(id=row['id']):
                self.assertEqual(self.resolve(row['source']['legacy_document']), row['text']['translation'])
                self.assertEqual(hashlib.sha256(row['text']['translation'].encode('utf-8')).hexdigest(), row['extraction']['text_sha256'])
                if row['text']['arabic'] is not None:
                    self.assertEqual(self.resolve(row['source']['arabic_quote_locator']), row['text']['arabic'])

    def test_person_credits_resolve_to_selected_parent_scalar_fields(self):
        for row in self.rows:
            for key in ('narrator', 'translator'):
                for evidence in row[key].get('evidence') or []:
                    self.assertEqual(self.resolve(evidence['locator']), evidence['value'])
                    self.assertEqual(row[key]['name'], evidence['value'])
        row = self.by_id['legacy.ja.c5a631bea35be863289f3f97']
        self.assertEqual(row['translator']['name'], 'ゼバ久米')
        self.assertEqual(row['translation_provenance']['current_policy']['classification'], 'unknown')
        self.assertIsNone(self.by_id['legacy.ja.41746fd5242e6c83d4163168']['narrator']['name'])

    def test_absence_statements_and_collection_attributions_are_not_names(self):
        locator = {'repository': 'TEST', 'path': 'TEST', 'json_pointer': '/parent'}
        metadata = {'selected_parent_locator': locator, 'selected_parent': {
            'metadata': {'translator': 'not named in inspected source metadata'},
            'narrator_as_published': 'इसे मुस्लिम ने रिवायत किया है'}}
        self.assertEqual(selected_parent_person(metadata, 'translator'), (None, None))
        self.assertEqual(selected_parent_person(metadata, 'narrator'), (None, None))

    def test_glosses_and_semantic_mirrors_do_not_inflate_records(self):
        for ident in ('legacy.fa.24c99d5103ae995cf641aa00', 'legacy.fa.aaedb4097426598e7f39c6a8',
                      'legacy.fa.dbb55a78a77e20b89576e422', 'legacy.uz.edf032fd2d21777c145702cc',
                      'legacy.uz.e3c2ad414719b24d6ee31197'):
            self.assertNotIn(ident, self.by_id)
        self.assertFalse(any('/editions/unindexed-' in row['source']['legacy_document']['path'] for row in self.rows))
        self.assertEqual(len(self.rows), len(self.by_id))

    def test_excerpt_types_unknown_origin_and_non_ocr_are_preserved(self):
        for row in self.rows:
            self.assertEqual(row['record_type'].endswith('_excerpt'), row['extraction']['is_excerpt'])
            self.assertEqual(row['translation_provenance']['current_policy']['classification'], 'unknown')
            self.assertIs(row['extraction']['ocr_used'], False)
            self.assertIsNone(row['number']['canonical'])
        report = json.loads((ROOT / 'reports/legacy-extraction-audit.json').read_text(encoding='utf-8'))
        self.assertEqual(len(self.rows), report['records'])
        self.assertEqual(dict(collections.Counter(r['language'] for r in self.rows)), report['by_language'])

    def test_publisher_note_narrations_keep_their_own_attribution(self):
        for topic, language, expected in (
            ('closeness-02', 'ja', 'アッラーに対して希望的な観測をもつことなしには、この世を去ってはならない。'),
            ('trust-03', 'ja', 'アッラーに対して希望的な観測をもつことなしには、この世を去ってはならない。'),
            ('sabr-03', 'vi', 'Người phụ nữ khóc cho đứa con nhỏ của bà'),
        ):
            found = [row for row in self.rows
                     if row['source']['legacy_document']['path'] == f'materials/hadith/heart-reminder/{topic}/{language}.json'
                     and row['source']['legacy_document']['json_pointer'] == '/reading/required_published_notes/0/text']
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]['text']['translation'], expected)
            self.assertEqual(found[0]['book_key'], 'muslim')
            self.assertIsNone(found[0]['number']['in_book'])
            self.assertEqual(found[0]['record_type'], 'hadith_excerpt')
            self.assertTrue(found[0]['related_versions'])

    def test_note_work_and_numbering_scopes_do_not_invent_canonical_ids(self):
        local_number = self.by_id['legacy.ja.323cc38f54827e7923a32445']
        self.assertEqual(local_number['number']['in_book'], '17')
        self.assertEqual(local_number['number']['numbering_scheme'], 'number_within_source_named_book')
        self.assertIsNone(local_number['number']['canonical'])
        companion = self.by_id['legacy.ja.76cf9a8e7873025e4a597c6a']
        self.assertEqual(companion['record_type'], 'companion_report_excerpt')
        reference = companion['references']['items'][0]
        self.assertEqual((reference['collection'], reference['volume'], reference['page']), ('Al-Hakim', '2', '338'))
        self.assertIsNone(reference['work_title'])
        self.assertIsNone(companion['number']['in_book'])
        for ident in ('legacy.ja.a74c4ba4b1bc3999e662507c', 'legacy.fil.831414ad451c92d638217f5a'):
            row = self.by_id[ident]
            self.assertEqual(row['record_type'], 'hadith_meaning_excerpt')
            self.assertEqual(row['number']['in_book'], '6319')
            self.assertEqual(row['references']['items'][0]['work_title'], "Al-Mu'jam al-Awsat")
        for ident in ('legacy.hi.863e3585585fbe30136bb8ad', 'legacy.hi.9370bafb6730b736b66528d0'):
            row = self.by_id[ident]
            self.assertEqual(row['text']['translation'], 'मैं ही राजा हूँ।')
            self.assertIsNone(row['number']['in_book'])
            self.assertEqual([r['number'] for r in row['references']['items'] if r['scope'] == 'source_note_context'], ['4812', '6519', '7382', '7413'])
        glossary = self.by_id['legacy.ja.c7bd7318ceca6043aca10891']
        self.assertEqual((glossary['book_key'], glossary['number']['in_book']), ('mishkat-al-masabih', '5737'))
        self.assertIsNone(glossary['number']['canonical'])
        self.assertIs(glossary['grading']['assessments'][0]['independent_verification'], False)

    def test_offline_rerun_recovers_same_occurrences_without_source_cache(self):
        # This checks the real fallback, including semantic-mirror decisions; a
        # local bank copy must not match itself instead of its source counterpart.
        extractor = Extractor(ROOT, ROOT / 'tests' / 'nonexistent-source-cache')
        extractor.save = lambda: None
        extractor.run()
        self.assertEqual({r['id']: r for r in extractor.records}, self.by_id)


if __name__ == '__main__':
    unittest.main()
