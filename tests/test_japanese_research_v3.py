"""Check the saved Japanese reader projection against preserved source evidence.

These tests never run the importer or regenerate their expected selections.
They check bytes, occurrence boundaries and publication separation, not original
PDF glyphs, religious authenticity, or a new independent Pro evaluation.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_reader import record_type_info
from material_registry import normalized_projection, publication
from resolve_counterparts import CounterpartResolver


IMPORT = ROOT / 'imports/japanese-research-v3-20261112'
SOURCE = IMPORT / 'preserved-source'
ARCHIVE_SHA256 = '331d2973511301c6cd50d3e2a8612e135defda529e855b8b03894490005c01fa'
ARCHIVE_BYTES = 89158437
SOURCE_FILE_HASHES = {
    'sources/source_records_baseline.json.gz':
        '45badef2b399b857ff062f20309954b0694b866614461c17f6f47e64d54ce5da',
    'sources/source_records_added.json.gz':
        'fe18107bd9abed8f7ed307d7bbfbef9f98b0d7b1987e60e2499084ade280c603',
}
SELECTION_HASHES = {
    'whole_record_display_selections.json':
        '67670a060e901c00af4cb74cb20f42eff2db1583a911e3945e46c8e9c00e92b8',
    'mixed_parent_display_selections.json':
        '7cfe049ec72b44fb0fe2045f3ce271f47cbd3c9a3212a17ec7147e8d8b6b3668',
    'whole_record_text_roles.json':
        '3c4079bfecd6cc52e5864ddc2b709d78f8591a47b133d734efd45496f9a53958',
}
MATERIALS = {
    'ja_hisn_2007': (
        'ja-hisn-2007-research-v3', 261,
        'f96783671a386764ef4c6c87a302dd99d31da40163d536f0c302f60e0911c971'),
    'ja_islam_message': (
        'ja-islam-message-research-v3', 306,
        'cf59932bec72bb04c768dfcc9cad4e58603ef6d776e50dc5648621cd1a3905f8'),
    'ja_otsuka_20230901': (
        'ja-otsuka-20230901-research-v3', 9,
        '6d8c5d599c408b8b2b891e00a7e819c3466c7423bdde5ea197d8c7c77a545147'),
    'ja_tokyo_basic_2012': (
        'ja-tokyo-basic-2012-research-v3', 650,
        'a7794fb0ac3de21bbbd792b02032daace3bc0b54a18bba67ee04b2708a2311df'),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def text_sha256(value):
    return sha256(value.encode('utf-8'))


def file_sha256(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


class JapaneseResearchV3SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = {}

        def saved(relative):
            raw = gzip.decompress((SOURCE / relative).read_bytes())
            cls.source_bytes[relative] = raw
            return json.loads(raw)

        cls.baseline = saved('sources/source_records_baseline.json.gz')
        cls.added = saved('sources/source_records_added.json.gz')
        cls.original_rows = cls.baseline + cls.added
        cls.originals = {row['record_id']: row for row in cls.original_rows}
        cls.record_hashes = saved('manifests/record_hashes.json.gz')
        cls.enrichment = saved('metadata/enrichment_by_record_id.json.gz')
        cls.routing_rows = saved('metadata/routing.json.gz')
        cls.routing = {row['record_id']: row for row in cls.routing_rows}
        cls.component_reviews = saved('metadata/component_origin_reviews_v3.json.gz')
        cls.components = {row['component_id']: row for row in cls.component_reviews}
        cls.whole = read_json(IMPORT / 'selection/whole_record_display_selections.json')
        cls.mixed = read_json(IMPORT / 'selection/mixed_parent_display_selections.json')
        cls.roles = read_json(IMPORT / 'selection/whole_record_text_roles.json')['by_record_id']
        cls.bibliography = read_json(IMPORT / 'Japanese_bibliography.json')
        cls.publication = read_json(IMPORT / 'publication-decisions.json')
        cls.decisions = {row['record_id']: row for row in cls.publication['decisions']}
        cls.audit = read_json(IMPORT / 'integration-audit.json')
        cls.manifests, cls.material_rows, cls.rows = {}, {}, []
        for source_id, (slug, _, _) in MATERIALS.items():
            manifest = read_json(ROOT / 'materials' / slug / 'manifest.json')
            rows = read_rows(ROOT / manifest['records']['path'])
            cls.manifests[source_id] = manifest
            cls.material_rows[source_id] = rows
            cls.rows.extend(rows)
        cls.by_id = {row['id']: row for row in cls.rows}

    def test_exact_source_objects_and_selection_ledgers_remain_preserved(self):
        self.assertEqual((len(self.baseline), len(self.added)), (1687, 202))
        self.assertEqual(len(self.original_rows), len(self.originals))
        self.assertEqual(len(self.originals), 1889)
        for name, expected in SOURCE_FILE_HASHES.items():
            self.assertEqual(sha256(self.source_bytes[name]), expected, name)
        for name, expected in SELECTION_HASHES.items():
            self.assertEqual(file_sha256(IMPORT / 'selection' / name), expected, name)
        self.assertEqual(Counter(row['record_id'] for row in self.record_hashes),
                         Counter(self.originals.keys()))
        for evidence in self.record_hashes:
            identifier = evidence['record_id']
            with self.subTest(record_id=identifier):
                original = self.originals[identifier]
                encoded = json.dumps(original, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')
                self.assertEqual(sha256(encoded), evidence['source_object_canonical_json_sha256'])
                self.assertEqual(text_sha256(original['raw_text']), evidence['raw_text_utf8_sha256'])
                self.assertFalse(evidence['source_text_modified'])

    def test_1226_occurrences_keep_original_ids_without_counting_children_again(self):
        self.assertEqual((len(self.whole), len(self.mixed)), (1147, 79))
        self.assertTrue(set(self.whole).isdisjoint(self.mixed))
        selected = set(self.whole) | set(self.mixed)
        self.assertEqual(len(self.rows), 1226)
        self.assertEqual(Counter(row['id'] for row in self.rows), Counter(selected))
        self.assertTrue(selected <= self.originals.keys())
        whole_route = {row['record_id'] for row in self.routing_rows
                       if row['proposed_route'] == 'proposed_bank/hadith'}
        self.assertEqual(set(self.whole), whole_route)
        child_ids = [part['component_id'] for selection in self.mixed.values()
                     for part in selection['parts']]
        self.assertEqual(len(child_ids), 122)
        self.assertEqual(len(set(child_ids)), 122)
        self.assertTrue(set(child_ids).isdisjoint(self.by_id))
        self.assertEqual({self.components[key]['parent_record_id'] for key in child_ids},
                         set(self.mixed))
        self.assertEqual(self.publication['reader_occurrences'], 1226)
        self.assertEqual(self.publication['preserved_child_component_ids'], 122)
        self.assertEqual(self.audit['reader_source_occurrences'], 1226)

    def test_every_whole_occurrence_matches_its_saved_source_field(self):
        for identifier, selection in self.whole.items():
            with self.subTest(record_id=identifier):
                original, row = self.originals[identifier], self.by_id[identifier]
                text = original[selection['source_field']]
                self.assertIsInstance(text, str)
                self.assertTrue(text.strip())
                self.assertEqual(row['text']['translation'], text)
                self.assertEqual(selection['selected_text'], text)
                self.assertEqual(text_sha256(text), selection['selected_text_sha256'])
                self.assertEqual(text_sha256(original['raw_text']), selection['source_raw_text_sha256'])
                self.assertEqual(row['source_locator']['source_field'], selection['source_field'])
                span = selection.get('raw_text_span_if_contiguous')
                if span is not None:
                    self.assertEqual(original['raw_text'][span[0]:span[1]], text)
                self.assertEqual(self.enrichment[identifier]['classification'], 'prophetic_hadith')

    def test_every_mixed_excerpt_uses_only_saved_approved_component_spans(self):
        for identifier, selection in self.mixed.items():
            with self.subTest(record_id=identifier):
                raw, row = self.originals[identifier]['raw_text'], self.by_id[identifier]
                self.assertEqual(text_sha256(raw), selection['source_raw_text_sha256'])
                parts = selection['parts']
                self.assertEqual(row['source_locator']['parts'], parts)
                self.assertEqual(row['source_locator']['component_ids'],
                                 [part['component_id'] for part in parts])
                self.assertEqual(row['source_locator']['display_assembly'], selection['display_assembly'])
                self.assertFalse(selection['display_assembly']['separator_is_printed_source_text'])
                self.assertTrue(selection['display_assembly']['source_spans_remain_separate'])
                self.assertTrue(selection['display_assembly']['does_not_assert_one_canonical_chain_for_all_components'])
                pieces = []
                for part in parts:
                    component = self.components[part['component_id']]
                    self.assertEqual(component['parent_record_id'], identifier)
                    self.assertEqual(part['parent_record_id'], identifier)
                    self.assertEqual(component['classification'], 'prophetic_hadith')
                    self.assertFalse(component.get('component_boundary_unresolved', False))
                    self.assertFalse(component['show_in_html_hadith'])
                    start, end = component['start_char'], component['end_char']
                    self.assertEqual(part['approved_component_span'], [start, end])
                    self.assertEqual(raw[start:end], component['source_slice'])
                    self.assertEqual(text_sha256(raw[start:end]), component['source_slice_sha256'])
                    self.assertEqual(part['approved_component_sha256'], component['source_slice_sha256'])
                    left, right = part['selected_display_span']
                    self.assertLessEqual(start, left)
                    self.assertLess(left, right)
                    self.assertLessEqual(right, end)
                    self.assertEqual(raw[left:right], part['selected_text'])
                    self.assertEqual(text_sha256(raw[left:right]), part['selected_text_sha256'])
                    pieces.append(raw[left:right])
                separator = selection['display_assembly']['separator']
                self.assertEqual([ord(char) for char in separator],
                                 selection['display_assembly']['separator_codepoints'])
                expected = separator.join(pieces)
                self.assertEqual(expected, selection['selected_text'])
                self.assertEqual(row['text']['translation'], expected)
                self.assertEqual(text_sha256(expected), selection['selected_text_sha256'])

    def test_source_locators_resolve_to_the_exact_original_occurrences(self):
        sources = {
            'source_records_baseline.json.gz': self.baseline,
            'source_records_added.json.gz': self.added,
        }
        for row in self.rows:
            with self.subTest(record_id=row['id']):
                locator = row['source_locator']
                pointer = locator['source_record']
                path = ROOT / pointer['path']
                self.assertEqual(path.parent, SOURCE / 'sources')
                self.assertEqual(pointer['compression'], 'gzip')
                self.assertRegex(pointer['json_pointer'], r'^/\d+$')
                original = sources[path.name][int(pointer['json_pointer'][1:])]
                self.assertEqual(original, self.originals[row['id']])
                self.assertEqual(locator['original_record_id'], row['id'])
                self.assertEqual(locator['raw_text_sha256'], text_sha256(original['raw_text']))
                self.assertEqual(locator['display_text_sha256'], text_sha256(row['text']['translation']))
                self.assertTrue((ROOT / locator['selection_path']).is_file())

    def test_all_663_excluded_source_ids_stay_out_of_registered_reader_rows(self):
        excluded = set(self.originals) - set(self.by_id)
        self.assertEqual(len(excluded), 663)
        decisions_hidden = {key for key, value in self.decisions.items()
                            if value['show_in_html_hadith'] is False}
        self.assertEqual(excluded, decisions_hidden)
        expected_routes = Counter({
            'proposed_bank/non_hadith': 186,
            'source_context/quran': 429,
            'hold/unresolved_origin': 21,
            'hold/mixed_source_parents': 27,
        })
        self.assertEqual(Counter(self.routing[key]['proposed_route'] for key in excluded), expected_routes)
        partition_rows = []
        for descriptor in self.audit['partitions'].values():
            self.assertFalse(descriptor['registered_as_hadith'])
            rows = read_rows(ROOT / descriptor['path'])
            self.assertEqual(len(rows), descriptor['count'])
            partition_rows.extend(rows)
            for row in rows:
                with self.subTest(partition=descriptor['path'], record_id=row['id']):
                    self.assertFalse(row['show_in_html_hadith'])
                    self.assertEqual(row['original_source_record'], self.originals[row['id']])
        partition_ids = [row['id'] for row in partition_rows]
        self.assertEqual(len(partition_ids), len(set(partition_ids)))
        # The 79 mixed parents are deliberately retained as full hidden evidence
        # as well as one bounded reader excerpt each, not additional occurrences.
        self.assertEqual(set(partition_ids) & set(self.by_id), set(self.mixed))
        self.assertEqual(set(partition_ids) - set(self.by_id), excluded)
        self.assertEqual(set(partition_ids) | set(self.by_id), set(self.originals))

    def test_hisn_099_and_translator_note_051_do_not_include_parent_quran(self):
        cases = {
            'ja_hisn_2007:entry:099': (
                [[667, 707], [1072, 1128]],
                '6d00a9ad38adcafd1ac24e820ad8cda9ea57fe92e505e2d7b564664e99a96eaf',
                ['純正章', '黎明章', '人間章']),
            'ja_hisn_2007:translator_note:051': (
                [[21, 33], [67, 77], [96, 106]],
                '18f551fd3786429f0d9953915f322b03e2d081333e9d8021cea9ee16ec3df39b',
                ['女人章', '至高のアッラーは仰られた']),
        }
        for identifier, (spans, expected_hash, excluded_markers) in cases.items():
            with self.subTest(record_id=identifier):
                raw = self.originals[identifier]['raw_text']
                row = self.by_id[identifier]
                self.assertEqual([part['selected_display_span'] for part in row['source_locator']['parts']], spans)
                self.assertEqual(text_sha256(row['text']['translation']), expected_hash)
                for marker in excluded_markers:
                    self.assertIn(marker, raw)
                    self.assertNotIn(marker, row['text']['translation'])
                self.assertNotEqual(row['text']['translation'], raw)
        self.assertEqual(self.by_id['ja_hisn_2007:translator_note:051']['text']['translation'],
                         'アッサラーム アライクム\n\nワ ラハマトゥッラー\n\nワ バ\nラカートゥフ')

    def test_hisn_074_and_162_keep_japanese_subspans_without_broken_arabic(self):
        cases = {
            'ja_hisn_2007:entry:074': (
                [1299, 1922], 'cc21465a80a070917f72f92ce7e020e15c37e0e6b628fc7997dff66af07b1568',
                'イムラーン家章'),
            'ja_hisn_2007:entry:162': (
                [241, 342], 'b9181cb2312533dc3169a56fd96c13385bc363249732f62899392c95b39c4969',
                'またこう言えばより良い'),
        }
        for identifier, (span, expected_hash, excluded) in cases.items():
            with self.subTest(record_id=identifier):
                raw, row = self.originals[identifier]['raw_text'], self.by_id[identifier]
                self.assertEqual(row['source_locator']['parts'][0]['selected_display_span'], span)
                self.assertEqual(row['text']['translation'], raw[span[0]:span[1]])
                self.assertEqual(text_sha256(row['text']['translation']), expected_hash)
                self.assertIn(excluded, raw)
                self.assertNotIn(excluded, row['text']['translation'])
                self.assertNotRegex(row['text']['translation'], r'[\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufeff]')

    def test_four_original_pdf_hashes_and_material_counts_match_saved_evidence(self):
        for source_id, (_, expected_count, expected_hash) in MATERIALS.items():
            with self.subTest(source_id=source_id):
                manifest = self.manifests[source_id]
                rows = self.material_rows[source_id]
                self.assertEqual(len(rows), expected_count)
                self.assertEqual(manifest['records']['count'], expected_count)
                self.assertEqual(file_sha256(ROOT / manifest['records']['path']), manifest['records']['sha256'])
                self.assertEqual(file_sha256(ROOT / manifest['source']['path']), expected_hash)
                self.assertEqual(manifest['source']['sha256'], expected_hash)
                self.assertEqual(self.bibliography[source_id]['source_pdf_sha256'], expected_hash)
                for row in rows:
                    self.assertEqual(row['source_locator']['original_source_id'], source_id)
                    self.assertEqual(row['source_locator']['source_pdf_sha256'], expected_hash)
                    self.assertEqual(row['source_locator']['source_pdf_path'], manifest['source']['path'])

    def test_later_visibility_decision_does_not_rewrite_historical_holds(self):
        self.assertEqual(self.publication['source_archive_sha256'], ARCHIVE_SHA256)
        self.assertEqual(len(self.publication['decisions']), 1889)
        self.assertEqual(set(self.decisions), set(self.originals))
        self.assertEqual(self.publication['decision'], 'owner_requested_public_pending_review')
        self.assertFalse(self.publication['source_certification_holds_changed'])
        self.assertFalse(self.publication['independent_final_pro_qc_performed'])
        digest = file_sha256(IMPORT / 'publication-decisions.json')
        for identifier, decision in self.decisions.items():
            with self.subTest(record_id=identifier):
                self.assertFalse(self.routing[identifier]['show_in_html_hadith'])
                self.assertFalse(self.enrichment[identifier]['show_in_html_hadith'])
                self.assertFalse(decision['historical_show_in_html_hadith'])
                self.assertEqual(decision['show_in_html_hadith'], identifier in self.by_id)
                self.assertFalse(decision['original_source_text_modified'])
                self.assertFalse(decision['certified_release_eligible'])
                if identifier not in self.by_id:
                    continue
                row = self.by_id[identifier]
                review = row['review']
                self.assertTrue(row['show_in_html_hadith'])
                self.assertFalse(review['historical_show_in_html_hadith'])
                self.assertFalse(review['release_eligible'])
                self.assertFalse(review['certified_release_eligible'])
                self.assertEqual(review['independent_pro_qc'], 'pending')
                self.assertEqual(review['historical_release_gates'], self.enrichment[identifier].get('release_gates'))
                for field, value in review['historical_source_review'].items():
                    self.assertEqual(value, self.originals[identifier][field])
                current = review['current_publication_decision']
                self.assertEqual(ROOT / current['path'], IMPORT / 'publication-decisions.json')
                self.assertEqual(current['sha256'], digest)
                self.assertEqual(current['original_record_id'], identifier)
                self.assertEqual(decision['selection_text_sha256'], text_sha256(row['text']['translation']))
                self.assertFalse(row['extraction']['new_ocr_performed'])
                self.assertEqual(row['extraction']['new_original_pages_reviewed'], 0)
        for manifest in self.manifests.values():
            authorization = manifest['publication']
            self.assertTrue(authorization['authorized'])
            self.assertEqual(authorization['decision'], 'owner_requested_public_pending_review')
            self.assertEqual(authorization['publication_decisions_sha256'], digest)
            self.assertFalse(authorization['independent_qc_asserted'])
            self.assertFalse(authorization['certified_release_eligible'])

    def test_unknown_translator_names_remain_null_and_language_versions_are_exact(self):
        expected_hisn_names = ['サイード佐藤', 'ファーティマ佐藤']
        for source_id, rows in self.material_rows.items():
            for row in rows:
                with self.subTest(record_id=row['id']):
                    translator = row['translator']
                    if source_id == 'ja_hisn_2007':
                        self.assertEqual(translator['names'], expected_hisn_names)
                        self.assertEqual(translator['name'], '・'.join(expected_hisn_names))
                    else:
                        self.assertIsNone(translator['name'])
                        self.assertIsNone(translator['names'])
                        self.assertTrue(translator['null_reason'])
                    versions = row['language_versions']
                    self.assertEqual(len(versions), 1)
                    version = versions[0]
                    self.assertEqual(version['id'], row['id'] + ':ja:printed-source')
                    self.assertEqual(version['language'], 'ja')
                    self.assertEqual(version['script'], 'Jpan')
                    self.assertEqual(version['text'], row['text']['translation'])
                    self.assertEqual(version['match_status'], 'same_source_record')
                    self.assertEqual(version['references'], row['references']['items'])
                    self.assertEqual(version['source']['sha256'], self.manifests[source_id]['source']['sha256'])

    def test_current_projection_and_resolver_cannot_promote_candidate_counterparts(self):
        # Exercise the real resolver's material-policy short circuit. Both
        # matching routes deliberately fail if called; no provider corpus or
        # full reader rebuild is needed to establish this precedence.
        resolver = CounterpartResolver.__new__(CounterpartResolver)
        resolver.enabled = True
        resolver.quality_policy = None
        resolver.reviewed = SimpleNamespace(for_record=Mock(side_effect=AssertionError('Reviewed matching must stay disabled')))
        resolver._select = Mock(side_effect=AssertionError('Automatic matching must stay disabled'))
        projected_ids = []
        for source_id, manifest in self.manifests.items():
            manifest_path = 'materials/' + MATERIALS[source_id][0] + '/manifest.json'
            self.assertEqual(manifest['counterpart_policy']['mode'], 'disabled')
            material = {
                'language': manifest['language'], 'book_key': manifest['book'],
                'edition': manifest['edition'], 'dataset_id': manifest['source_id'],
                'canonical_records_path': manifest['records']['path'],
                'source_file': manifest['source']['path'], 'source_sha256': manifest['source']['sha256'],
                'source_descriptor': manifest['source'],
                'publication': publication(manifest, manifest_path),
                'counterpart_policy': manifest['counterpart_policy'],
            }
            for position, row in enumerate(self.material_rows[source_id]):
                with self.subTest(record_id=row['id']):
                    self.assertIsNone(row['text']['arabic'])
                    self.assertIsNone(row['number']['canonical'])
                    self.assertIsNone(row['grading']['grade'])
                    self.assertIsNone(row['grading']['grader'])
                    for reference in row['references']['items']:
                        if str(reference.get('scope') or '').startswith('Research witness:'):
                            self.assertFalse(reference['is_accepted_canonical_identity'])
                    projected = normalized_projection(row, material, position)
                    projected_ids.append(projected['id'])
                    self.assertEqual(projected['text_translation'], row['text']['translation'])
                    self.assertIsNone(projected['text_arabic'])
                    self.assertFalse(projected['review']['certified_release_eligible'])
                    counterpart = resolver.for_record(projected)
                    self.assertEqual(counterpart['match_method'], 'material_counterparts_disabled')
                    self.assertEqual(counterpart['status'], 'unresolved')
                    self.assertIsNone(counterpart['arabic'])
                    self.assertIsNone(counterpart['english'])
        self.assertEqual(Counter(projected_ids), Counter(self.by_id.keys()))
        resolver.reviewed.for_record.assert_not_called()
        resolver._select.assert_not_called()

    def test_saved_reported_meaning_roles_stay_qualified(self):
        expected = {identifier for identifier, role in self.roles.items()
                    if 'reported_meaning_or_author_narrative' in role['suggested_qualifications']}
        actual = {row['id'] for row in self.rows if row['record_type'] == 'hadith_meaning_excerpt'}
        self.assertTrue(expected)
        # This ledger covers whole records. Additional mixed-parent narrative
        # excerpts may also need the qualification; none may lose a saved one.
        self.assertTrue(expected <= actual, 'A saved reported-meaning qualification was lost')
        for identifier in actual:
            self.assertEqual(record_type_info(self.by_id[identifier])['label'], 'Reported meaning')
            self.assertTrue(self.by_id[identifier]['commentary']['translation'])

    def test_component_citations_keep_saved_scope_limits_and_separate_binding_history(self):
        """Regress the observed parent-citation leaks and invisible qualifications."""
        for identifier, retained_id, excluded_id in (
                ('ja_hisn_2007:entry:074', 'V3-hisn-reuse-hisn_ev_e3d97debe7f2033240',
                 'V3-hisn-Wabil-istikhara'),
                ('ja_hisn_2007:entry:162', 'V3-hisn-reuse-hisn_ev_8576c8851473605c41',
                 'V3-hisn-Ithyubi-condolence')):
            with self.subTest(record_id=identifier):
                saved_links = {item['evidence_id']: item for item in
                               self.enrichment[identifier]['hadith_origin_research_v3']['collection_links']}
                self.assertIn(excluded_id, saved_links)  # Still retained in the parent evidence.
                selected_ids = {evidence_id for part in self.mixed[identifier]['parts']
                                for evidence_id in part['evidence_ids']}
                self.assertIn(retained_id, selected_ids)
                self.assertNotIn(excluded_id, selected_ids)
                references = self.by_id[identifier]['references']
                self.assertEqual({item.get('evidence_id') for item in references['items']}, {retained_id})
                self.assertEqual(references['excluded_parent_witness_count'], 1)
                item = references['items'][0]
                saved = saved_links[retained_id]
                self.assertEqual(item['number'], saved['hadith_number'])
                self.assertEqual(item['witness_scope'], saved['scope'])
                self.assertIn(saved['scope'], item['scope'])
                self.assertIn(saved['relationship'], item['scope'])
                self.assertFalse(item['is_accepted_canonical_identity'])

        # The poisoning witness contradicts the Japanese "no harm" assertion;
        # the qualification must be in the visible citation scope, not only JSON.
        identifier = 'ja_tokyo_basic_2012:audit_v2:p241:o001'
        evidence_id = 'V3-tokyo_other-B2617'
        saved = next(item for item in self.enrichment[identifier]['hadith_origin_research_v3']['collection_links']
                     if item['evidence_id'] == evidence_id)
        item = next(item for item in self.by_id[identifier]['references']['items']
                    if item.get('evidence_id') == evidence_id)
        self.assertIn('does not support the Japanese assertion of no harm', saved['scope'])
        self.assertIn(saved['scope'], item['scope'])
        self.assertEqual(item['number'], saved['hadith_number'])
        self.assertEqual(item['source_url'], saved['url'])
        self.assertFalse(item['is_accepted_canonical_identity'])

        # A printed citation gains renderer aliases, while all original claim
        # fields and the original source object remain unchanged.
        identifier = 'ja_islam_message:p0014:o00079:quote'
        original_claim = self.originals[identifier]['canonical_source_claims'][0]
        item = next(item for item in self.by_id[identifier]['references']['items']
                    if item.get('claim_id') == original_claim['claim_id'])
        self.assertNotIn('collection', original_claim)
        for key, value in original_claim.items():
            self.assertEqual(item[key], value)
        self.assertEqual(item['collection'], original_claim['book_as_printed'])
        self.assertEqual(item['number'], original_claim['number_as_printed'])
        self.assertEqual(item['source_citation'], original_claim['citation_as_printed'])

        # The new binding is an explicit overlay over an unchanged component
        # whose historical evidence_ids are empty; no fabricated hadith number.
        overlay = read_json(IMPORT / 'reference-binding-overlays.json')
        component_id = 'ja_tokyo_basic_2012-r136:v3:c001'
        identifier = 'ja_tokyo_basic_2012-r136'
        binding = overlay['bindings_by_component_id'][component_id]
        self.assertEqual(overlay['source_archive_sha256'], ARCHIVE_SHA256)
        self.assertFalse(overlay['source_text_and_historical_metadata_modified'])
        self.assertFalse(binding['original_component_metadata_changed'])
        self.assertFalse(binding['new_external_research_or_authenticity_grade'])
        self.assertEqual(binding['parent_record_id'], identifier)
        self.assertEqual(binding['evidence_id'], 'tokyo-reports-turn256view0')
        component = self.components[component_id]
        self.assertNotIn(binding['evidence_id'], component.get('evidence_ids') or [])
        part = next(part for part in self.mixed[identifier]['parts'] if part['component_id'] == component_id)
        self.assertNotIn(binding['evidence_id'], part['evidence_ids'])
        self.assertEqual(binding['selected_text_sha256'], part['selected_text_sha256'])
        saved = next(item for item in self.enrichment[identifier]['hadith_origin_research_v3']['collection_links']
                     if item['evidence_id'] == binding['evidence_id'])
        references = self.by_id[identifier]['references']
        self.assertEqual(references['integration_reference_bindings'], [{'component_id': component_id, **binding}])
        self.assertEqual(len(references['items']), 1)
        item = references['items'][0]
        self.assertEqual(item['evidence_id'], binding['evidence_id'])
        self.assertEqual(item['source_url'], saved['url'])
        self.assertIsNone(item['number'])
        self.assertIn(saved['scope'], item['scope'])
        self.assertIn(binding['scope_limit'], item['scope'])

        # The Quran-arrangement assertion does not inherit the parent records'
        # Companion compilation-history references just to fill a citation.
        identifier = 'ja_tokyo_basic_2012-r005'
        parent_links = self.enrichment[identifier]['hadith_origin_research_v3']['collection_links']
        self.assertEqual({item['evidence_id'] for item in parent_links},
                         {'tokyo-reports-turn121view1', 'tokyo-reports-turn121view2'})
        row = self.by_id[identifier]
        self.assertEqual(row['references']['items'], [])
        self.assertEqual(row['references']['excluded_parent_witness_count'], 2)
        self.assertTrue(row['references']['selected_witness_null_reason'])
        self.assertIn(identifier, overlay['unresolved_selected_source'])
        self.assertIsNone(row['number']['canonical'])
        self.assertIn('この抜粋に対応する原典の伝承・番号は未確定です。', row['commentary']['translation'])

    def test_transport_parts_reproduce_the_exact_original_zip_without_extraction(self):
        manifest = read_json(IMPORT / 'preserved-delivery/archive-parts.json')
        self.assertEqual(manifest['original_sha256'], ARCHIVE_SHA256)
        self.assertEqual(manifest['original_size_bytes'], ARCHIVE_BYTES)
        self.assertEqual([part['index'] for part in manifest['parts']],
                         list(range(1, len(manifest['parts']) + 1)))
        combined, size = hashlib.sha256(), 0
        for part in manifest['parts']:
            path = ROOT / part['path']
            checksum, part_size = hashlib.sha256(), 0
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    checksum.update(block)
                    combined.update(block)
                    part_size += len(block)
            self.assertEqual(checksum.hexdigest(), part['sha256'], part['path'])
            self.assertEqual(part_size, part['size_bytes'], part['path'])
            size += part_size
        self.assertEqual(size, ARCHIVE_BYTES)
        self.assertEqual(combined.hexdigest(), ARCHIVE_SHA256)


if __name__ == '__main__':
    unittest.main()
