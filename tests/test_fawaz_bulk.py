"""Synthetic source fixtures; TEST text is not an actual religious quotation."""
import argparse
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import import_fawaz_bulk as importer
from material_registry import load_public_materials
from language_display import language_readings


def row(number, text="TEST قال رسول الله TEST source quotation", book=1):
    return {"hadithnumber": number, "arabicnumber": number, "text": text,
            "reference": {"book": book, "hadith": number},
            "grades": [{"name": "TEST assessor", "grade": "TEST source grade"}]}


def catalog(books):
    return {book: {"name": importer.BOOKS[book][1], "collection": [
        {"name": prefix + "-" + book, "book": book, "language": label,
         "author": "Unknown" if prefix != "eng" else "TEST source translator",
         "source": "", "comments": "TEST edition note" if prefix == "eng" else ""}
        for prefix, (_, label, _) in importer.LANGUAGES.items()]} for book in books}


def source_data(book, rows, sections=None):
    return {"metadata": {"name": importer.BOOKS[book][1],
                         "sections": sections or {"0": "The Book of the Sunnah", "1": "TEST section"},
                         "section_details": {}}, "hadiths": rows}


class FawazBulkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "AGENTS.md").write_text("TEST source-preservation rules")
        self.books = ["bukhari"]
        self.plan = {"schema": "hadith-bank-fawaz-bulk-plan-v1", "enabled": True,
                     "repository": importer.REPOSITORY, "revision": importer.REVISION,
                     "books": self.books, "languages": list(importer.BASE_LANGUAGES), "max_books_per_batch": 7}
        importer.save_json(self.root, importer.PLAN, self.plan)
        self.state = {"schema": "hadith-bank-fawaz-bulk-state-v1", "revision": importer.REVISION, "inputs": {}, "stop": None}

    def inputs(self, books=None):
        books = books or self.books
        values = {"editions.json": importer.encoded(catalog(books)),
                  "README.md": b"TEST whole edition documentation\n", "LICENSE": b"TEST source license bytes\n",
                  "References.md": b"TEST project-wide credit https://example.invalid/source\n",
                  "CONTRIBUTING.md": b"TEST same provider numbering across editions\n"}
        for book in books:
            for prefix in self.plan["languages"]:
                values["editions/" + prefix + "-" + book + ".json"] = importer.encoded(source_data(book, [row(1)]))
        return values

    def seed(self, inputs=None):
        for key, raw in (inputs or self.inputs()).items():
            self.state["inputs"][key] = importer.snapshot(self.root, key, raw, {
                "url": importer.provider_url(key), "retrieved_at": "2026-11-12T00:00:00+00:00"})
        importer.save_json(self.root, importer.IMPORT + "/state.json", self.state)

    def args(self, **changes):
        values = dict(root=self.root, fetch=False, export_only=True, adopt_dir=None,
                      max_books=None, retry_failed=False)
        values.update(changes)
        return argparse.Namespace(**values)

    def test_exact_text_own_references_grades_and_registry_projection(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            text = "TEST قال رسول الله TEST exact\nsource " if prefix == "ara" else "TEST " + prefix + " quotation\n"
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", [row(1, text)]))
        self.seed(inputs)
        importer.save_json(self.root, "catalog/provenance-policy.json", {
            "schema": "hadith-bank-provenance-policy-v1", "decision_date_japan": "2026-11-11", "source_rules": [],
            "new_material_rule": {"scope": "registered_nonlegacy_materials_and_counterparts", "classification": "human",
                                  "basis": "TEST owner decision", "source_declarations_take_precedence": True}})
        summary, code = importer.run(self.args())
        self.assertEqual((code, summary["registered_occurrences"], summary["held_occurrences"]), (0, 1, 0))
        materials = load_public_materials(self.root)
        records = [value for group in materials["groups"] for value in group]
        self.assertEqual(len(records), 1)
        record = records[0]
        versions = {item["language"]: item for item in record["language_versions"]}
        self.assertEqual(versions["ar"]["text"], "TEST قال رسول الله TEST exact\nsource ")
        self.assertIsNone(versions["ar"]["translation_provenance"])
        self.assertEqual(versions["en"]["translation_provenance"]["current_policy"]["classification"], "human")
        self.assertIsNone(versions["ur"]["source"]["translator"]["name"])
        self.assertEqual(versions["en"]["source"]["translator"]["name"], "TEST source translator")
        for code, prefix in [("ar", "ara"), ("en", "eng"), ("ur", "urd")]:
            own = versions[code]
            self.assertEqual(own["grading"], row(1)["grades"])
            self.assertIn(prefix + "-bukhari", own["source"]["record_url"])
            self.assertEqual(own["references"][0]["numbering_system"], "fawaz_api_hadithnumber")
            self.assertTrue(any(note["text"] == "Source assessment — TEST assessor: TEST source grade" for note in own["comments"]))
        self.assertEqual(len(language_readings(record)), 3)
        self.assertIsNone(record["number"]["canonical"])
        self.assertIsNone(record["grading"]["grade"])

    def test_unique_typed_provider_ids_not_array_positions_or_integer_casts(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            rows = [row(1), row(1.5)]
            if prefix == "eng":
                rows.reverse()
            if prefix == "urd":
                rows.append(row(1.75, "TEST رسول اللہ نے فرمایا TEST Urdu quotation"))
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", rows))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary["registered_occurrences"], 3)
        rows = [json.loads(line) for path in (self.root / "materials").glob("*/records.jsonl") for line in path.read_text().splitlines()]
        self.assertEqual({item["number"]["source_entry_id"] for item in rows}, {1, 1.5, 1.75})
        for item in rows:
            for version in item["language_versions"]:
                self.assertEqual(version["provider_numbers"]["hadithnumber"], item["number"]["source_entry_id"])

    def test_bengali_extension_preserves_base_books_own_metadata_and_missing_states(self):
        inputs = self.inputs()
        metadata = json.loads(inputs['editions.json'])
        bengali = next(item for item in metadata['bukhari']['collection'] if item['name'] == 'ben-bukhari')
        bengali.update(author='TEST Bengali translator', comments='TEST Bengali edition comment',
                       source='https://example.invalid/bengali-edition')
        inputs['editions.json'] = importer.encoded(metadata)
        for prefix in self.plan['languages']:
            text = 'TEST قال رسول الله TEST quotation' if prefix == 'ara' else 'TEST ' + prefix + ' quotation'
            inputs['editions/' + prefix + '-bukhari.json'] = importer.encoded(source_data('bukhari',
                [row(1, text), row(1.5, text), row(2, text)]))
        self.seed(inputs)
        first, _ = importer.run(self.args())
        self.assertTrue(first['complete'])

        def records():
            return {item['id']: item for path in (self.root / 'materials').glob('*/records.jsonl')
                    for line in path.read_text().splitlines() if (item := json.loads(line))}

        before = records()
        source_hashes = {key: value['sha256'] for key, value in self.state['inputs'].items()}
        self.plan['languages'] = list(importer.LANGUAGES)
        importer.save_json(self.root, importer.PLAN, self.plan)
        pending, _ = importer.run(self.args())
        self.assertFalse(pending['complete'])
        self.assertEqual(pending['registered_occurrences'], 3)
        self.assertEqual(pending['pending_books'], ['bukhari'])
        self.assertEqual(pending['pending_editions'], ['editions/ben-bukhari.json'])
        self.assertEqual(set(records()), set(before))
        self.assertTrue(all(item['source']['language_availability']['bn'] == 'edition_pending'
                            for item in records().values()))

        bengali_row = row(1, 'TEST বাংলা মূল বাণী\n')
        bengali_row['grades'] = [{'name': 'TEST Bengali assessor', 'grade': 'TEST Bengali grade'}]
        raw = importer.encoded(source_data('bukhari', [row(1.5, ' '), bengali_row]))
        with mock.patch.object(importer, 'fetch_bytes', return_value=(raw, {
                'url': importer.provider_url('editions/ben-bukhari.json'), 'retrieved_at': 'TEST'})) as request:
            completed, code = importer.run(self.args(fetch=True, export_only=False))
        self.assertEqual(request.call_args_list, [mock.call('editions/ben-bukhari.json')])
        self.assertEqual((code, completed['complete'], completed['fetched_editions']), (0, True, 4))
        self.assertEqual(completed['registered_occurrences'], 3)
        after = records()
        self.assertEqual(set(before), set(after))
        by_number = {item['number']['source_entry_id']: item for item in after.values()}
        self.assertEqual({number: item['source']['language_availability']['bn'] for number, item in by_number.items()},
                         {1: 'available', 1.5: 'source_text_empty', 2: 'provider_entry_absent'})
        own = next(item for item in by_number[1]['language_versions'] if item['language'] == 'bn')
        self.assertEqual((own['text'], own['script']), (bengali_row['text'], 'Beng'))
        self.assertEqual(own['provider_numbers']['hadithnumber'], 1)
        self.assertEqual(own['source']['provider_edition'], 'ben-bukhari')
        self.assertEqual(own['source']['translator']['name'], 'TEST Bengali translator')
        self.assertEqual(own['grading'], bengali_row['grades'])
        self.assertTrue(any(note['text'] == 'TEST Bengali edition comment' for note in own['comments']))
        self.assertTrue(any('TEST Bengali assessor: TEST Bengali grade' in note['text'] for note in own['comments']))
        for identifier, item in after.items():
            self.assertEqual([view for view in item['language_versions'] if view['language'] != 'bn'],
                             before[identifier]['language_versions'])
        saved_state = importer.read_json(self.root, importer.IMPORT + '/state.json')
        self.assertTrue(all(saved_state['inputs'][key]['sha256'] == value for key, value in source_hashes.items()))
        projected = [item for group in load_public_materials(self.root)['groups'] for item in group]
        self.assertEqual(len(projected), 3)
        self.assertEqual(sum(view['language'] == 'bn' for item in projected for view in language_readings(item)), 1)

    def test_duplicate_or_inconsistent_provider_identity_is_held(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            rows = [row(1), row(2)]
            if prefix == "eng":
                rows.append(row(1))
                rows[1]["arabicnumber"] = 99
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", rows))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual((summary["registered_occurrences"], summary["held_occurrences"]), (0, 2))
        held = [json.loads(line) for line in gzip.decompress((self.root / importer.IMPORT / "held/bukhari.jsonl.gz").read_bytes()).splitlines()]
        self.assertEqual({item["classification"]["reason"] for item in held},
                         {"duplicate_provider_identity_within_edition", "inconsistent_shared_provider_arabicnumber"})
        self.assertTrue(all(item["show_in_html_hadith"] is False for item in held))
        self.assertEqual(len(held[0]["source_versions"]["eng"]), 2)

    def test_bengali_nawawi_has_no_urdu_edition_or_invented_translator(self):
        self.plan.update(books=['nawawi'], languages=list(importer.LANGUAGES))
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(['nawawi'])
        del inputs['editions/urd-nawawi.json']
        catalog_data = json.loads(inputs['editions.json'])
        catalog_data['nawawi']['collection'] = [item for item in catalog_data['nawawi']['collection'] if item['name'] != 'urd-nawawi']
        for meta in catalog_data['nawawi']['collection']:
            meta['author'] = 'Imam Nawawi'
        inputs['editions.json'] = importer.encoded(catalog_data)
        for prefix, text in [('eng', 'TEST source English quotation'), ('ben', 'TEST source Bengali quotation')]:
            inputs['editions/' + prefix + '-nawawi.json'] = importer.encoded(source_data('nawawi', [row(1, text)]))
        self.seed(inputs)
        with mock.patch.object(importer, 'fetch_bytes', side_effect=AssertionError('No unavailable edition may be requested')) as fetch:
            summary, code = importer.run(self.args(fetch=True, export_only=False))
        self.assertEqual((code, summary['complete'], summary['configured_editions'], summary['fetched_editions']), (0, True, 3, 3))
        self.assertEqual(summary['pending_editions'], [])
        fetch.assert_not_called()
        records = [item for group in load_public_materials(self.root)['groups'] for item in group]
        self.assertEqual(len(records), 1)
        canonical = [json.loads(line) for path in (self.root / 'materials').glob('*/records.jsonl') for line in path.read_text().splitlines()]
        self.assertEqual(canonical[0]['source']['language_availability']['ur'], 'edition_not_published_in_pinned_catalog')
        self.assertEqual({view['language'] for view in records[0]['language_versions']}, {'ar', 'en', 'bn'})
        for view in records[0]['language_versions']:
            self.assertIsNone(view['source']['translator']['name'])
            self.assertEqual(view['source']['catalog_author_as_supplied'], 'Imam Nawawi')
            self.assertEqual(view['source']['catalog_author_role'], 'collection_compiler_not_translation_credit')
        with self.assertRaisesRegex(ValueError, 'Unconfigured upstream path'):
            importer.provider_url('editions/urd-nawawi.json')

    def test_non_prophetic_empty_and_explicit_intro_are_held_but_book_zero_is_not_enough(self):
        inputs = self.inputs()
        for prefix in self.plan["languages"]:
            rows = [row(1, book=0), row(2, "TEST independent statement"), row(3, " "), row(4, book=2)]
            inputs["editions/" + prefix + "-bukhari.json"] = importer.encoded(source_data("bukhari", rows,
                {"0": "The Book of the Sunnah", "1": "TEST", "2": "Introduction"}))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual((summary["registered_occurrences"], summary["held_occurrences"]), (1, 3))

    def test_literal_compiler_note_spans_partition_without_rewriting(self):
        for book, language, text in [
            ("abudawud", "en", "TEST narration. Abu Dawud said: TEST note with additional report"),
            ("tirmidhi", "en", "TEST narration. [Abu 'Eisa said:] TEST note"),
            ("tirmidhi", "en", "TEST narration. [Abu `Eisa said: TEST note]"),
            ("tirmidhi", "ar", "TEST قَالَ رَسُولُ اللَّهِ TEST. قَالَ أَبُو عِيسَى TEST note"),
            ("abudawud", "bn", "TEST বাংলা বাণী। ইমাম আবূ দাঊদ (রহঃ) বলেন, TEST note"),
            ("abudawud", "bn", "TEST বাংলা বাণী। ইমাম আবূ দাউদ (রহঃ) বলেছেন, TEST note"),
            ("abudawud", "bn", "TEST বাংলা বাণী। قَالَ أَبُو دَاوُدَ TEST note. ইমাম আবূ দাঊদ (রহঃ) বলেন, TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। আবু ঈসা বলেন, TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। আবূ ঈসা বলেছেন, TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। TEST হাদীসটিকে আবু ঈসা হাসান সহীহ বলেছেন। TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। TEST হাদীসটিকে আবূ ঈসা গারীব বলেছেন। TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। আমি (আবূ ঈসা) TEST note"),
            ("tirmidhi", "bn", "TEST বাংলা বাণী। —সহীহ। TEST source grade. আবূ ঈসা বলেন, TEST note"),
        ]:
            with self.subTest(language=language, book=book):
                quotation, notes, spans = importer.split_compiler_note(text, book, language)
                self.assertEqual(quotation + "".join(notes), text)
                self.assertEqual(quotation, text[slice(*spans["quotation"])])
                self.assertEqual(notes, [text[slice(*item)] for item in spans["notes"]])
                self.assertIn("pending", spans["note_embedded_narration_extraction"])
                if language == "bn":
                    self.assertTrue(quotation.strip().endswith('বাণী।'))
                    self.assertNotIn('قَالَ', quotation)
                    self.assertNotIn('সহীহ', quotation)
        untouched = "TEST Anas ibn Malik said TEST"
        self.assertEqual(importer.split_compiler_note(untouched, "malik", "en")[0], untouched)

    def test_explicit_compiler_tail_is_kept_in_its_own_source_notes(self):
        inputs = self.inputs()
        inputs["editions/ara-bukhari.json"] = importer.encoded(source_data("bukhari", [
            row(1, "TEST قال رسول الله TEST quotation. قال أبو عبد الله TEST compiler material")]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary["registered_occurrences"], 1)
        records = [json.loads(line) for path in (self.root / 'materials').glob('*/records.jsonl') for line in path.read_text().splitlines()]
        own = next(item for item in records[0]['language_versions'] if item['language'] == 'ar')
        self.assertNotIn('compiler material', own['text'])
        self.assertTrue(any('compiler material' in item['text'] for item in own['comments']))

    def test_nabidh_and_wishes_about_prophet_do_not_establish_speaker_identity(self):
        inputs = self.inputs()
        arabic = [row(1, 'TEST عن النبيذ TEST'),
                  row(2, 'TEST وددت أن رسول الله صلى الله عليه وسلم كان عهد إلينا TEST'),
                  row(3, 'TEST سمعت عمر علي منبر رسول الله صلى الله عليه وسلم يقول TEST')]
        for prefix in self.plan["languages"]:
            rows = arabic if prefix == 'ara' else [row(i, 'TEST independent source statement') for i in (1, 2, 3)]
            inputs['editions/' + prefix + '-bukhari.json'] = importer.encoded(source_data('bukhari', rows))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 0)
        self.assertEqual(summary['by_book']['bukhari']['by_hold_reason']['attribution_subject_requires_review'], 2)

    def test_explicit_tirmidhi_grading_tail_is_source_commentary(self):
        self.plan['books'] = ['tirmidhi']
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(['tirmidhi'])
        inputs['editions/ara-tirmidhi.json'] = importer.encoded(source_data('tirmidhi', [
            row(1, 'TEST قال رسول الله TEST quotation. هذا حديث حسن صحيح TEST compiler analysis')]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        records = [json.loads(line) for path in (self.root / 'materials').glob('*/records.jsonl') for line in path.read_text().splitlines()]
        own = next(item for item in records[0]['language_versions'] if item['language'] == 'ar')
        self.assertNotIn('compiler analysis', own['text'])
        self.assertTrue(any('compiler analysis' in item['text'] for item in own['comments']))

    def test_pending_english_context_does_not_hide_valid_arabic_or_become_matn(self):
        self.plan['books'] = ['malik']
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(['malik'])
        source = 'Malik said TEST independent legal discussion. The Prophet said TEST embedded report.'
        inputs['editions/eng-malik.json'] = importer.encoded(source_data('malik', [row(1, source)]))
        inputs['editions/urd-malik.json'] = importer.encoded(source_data('malik', [row(1, 'TEST Urdu translation')]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        records = [item for group in load_public_materials(self.root)['groups'] for item in group]
        own = next(item for item in records[0]['language_versions'] if item['language'] == 'en')
        self.assertIsNone(own['text'])
        self.assertEqual(own['quotation_status'], 'boundary_pending')
        self.assertEqual(own['comments'][0]['text'], source)
        self.assertEqual(own['comments'][0]['scope'], 'source_context_not_narration')
        self.assertIn('narration boundary', next(item for item in language_readings(records[0]) if item['language'] == 'en')['qualification'])

    def test_missing_book_zero_reference_does_not_extend_muslim_introduction(self):
        item = {'row': row(125, book=0), 'metadata': {'sections': {'0': 'Introduction'},
                'section_details': {'0': {'hadithnumber_first': 1, 'hadithnumber_last': 92}}}}
        original = copy.deepcopy(item)
        self.assertIsNone(importer.source_section_name(item))
        self.assertEqual(item, original)
        item['row']['hadithnumber'] = 15
        self.assertEqual(importer.source_section_name(item), 'Introduction')
        item['row']['hadithnumber'] = 0
        self.assertEqual(importer.source_section_name(item), 'Introduction')

    def test_reviewed_excerpt_is_hash_bound_and_preserves_context_on_both_sides(self):
        text = 'TEST Quran/context. TEST Prophetic quotation. TEST compiler discussion.'
        start, end = text.index('TEST Prophetic'), text.index(' TEST compiler')
        decision = {'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': [[start, end]]}
        quotation, notes, spans = importer.apply_reviewed_span(text, decision)
        self.assertEqual(quotation, text[start:end])
        self.assertEqual(notes, [text[:start], text[end:]])
        self.assertEqual(spans['quotation'], [start, end])
        with self.assertRaisesRegex(ValueError, 'source hash changed'):
            importer.apply_reviewed_span(text + 'x', decision)

    def test_source_content_mismatch_does_not_create_false_arabic_or_english_counterparts(self):
        self.plan.update(books=['malik'], languages=list(importer.LANGUAGES))
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs, decisions = self.inputs(['malik']), []
        for prefix in self.plan['languages']:
            text = 'TEST Urdu Prophetic report' if prefix == 'urd' else 'TEST independent ruling ' + prefix
            inputs['editions/' + prefix + '-malik.json'] = importer.encoded(source_data('malik', [row(224, text)]))
            decision = {'provider_book': 'malik', 'provider_edition': prefix + '-malik', 'typed_hadithnumber': '224',
                        'source_text_sha256': importer.sha(text.encode()), 'quotation_spans': [[0, len(text)]]}
            if prefix != 'urd':
                decision.update(action='source_context_only', quotation_spans=[], reason='TEST verified provider content mismatch')
            decisions.append(decision)
        importer.save_json(self.root, 'catalog/fawaz-reviewed-spans.json', {
            'schema': 'hadith-bank-fawaz-reviewed-spans-v1', 'repository': importer.REPOSITORY,
            'revision': importer.REVISION, 'decisions': decisions})
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 1)
        records = [item for group in load_public_materials(self.root)['groups'] for item in group]
        record = records[0]
        self.assertEqual(record['language'], 'ur')
        self.assertIsNone(record['text_arabic'])
        for view in language_readings(record):
            if view['language'] == 'ur':
                self.assertEqual(view['text'], 'TEST Urdu Prophetic report')
            else:
                self.assertIsNone(view['text'])
                self.assertEqual(view['scope'], 'source_context')
                self.assertIn('not a translation or Arabic counterpart', view['qualification'])
                self.assertTrue(view['comments'][0]['text'].startswith('TEST independent ruling'))
        from counterpart_coverage import availability_for
        self.assertEqual(availability_for(record), {'arabic': 'missing', 'english': 'missing'})

    def test_partial_book_never_published_and_saved_checksums_are_required(self):
        inputs = self.inputs()
        del inputs["editions/urd-bukhari.json"]
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary["registered_occurrences"], 0)
        self.assertEqual(summary["pending_books"], ["bukhari"])
        item = self.state["inputs"]["editions/ara-bukhari.json"]
        path = self.root / item["path"]
        path.write_bytes(path.read_bytes() + b"TEST corrupt")
        with self.assertRaisesRegex(ValueError, "checksum"):
            importer.run(self.args())
        self.assertFalse((self.root / "materials").exists())

    def test_swapped_language_snapshot_descriptors_are_rejected_before_export(self):
        self.seed()
        inputs = self.state["inputs"]
        left, right = "editions/ara-bukhari.json", "editions/eng-bukhari.json"
        inputs[left], inputs[right] = inputs[right], inputs[left]
        importer.save_json(self.root, importer.IMPORT + "/state.json", self.state)
        with self.assertRaisesRegex(ValueError, "input key does not match"):
            importer.run(self.args())
        with self.assertRaisesRegex(ValueError, "input key does not match"):
            importer.export_saved(self.root, self.plan, self.state)
        self.assertFalse((self.root / "materials").exists())

    def test_fetch_is_whole_book_bounded_and_resumes_without_reacquiring_inputs(self):
        self.plan["books"] = ["bukhari", "malik"]
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(self.plan["books"])
        def fetch(key):
            return inputs[key], {"url": importer.provider_url(key), "retrieved_at": "TEST"}
        with mock.patch.object(importer, "fetch_bytes", side_effect=fetch) as request:
            first, code = importer.run(self.args(fetch=True, export_only=False, max_books=1))
            self.assertEqual(code, 0)
            self.assertEqual(first["completed_books"], ["bukhari"])
            self.assertEqual(request.call_count, len(importer.DOCUMENTS) + 3)
            request.reset_mock()
            second, code = importer.run(self.args(fetch=True, export_only=False, max_books=1))
            self.assertEqual(code, 0)
            self.assertTrue(second["complete"])
            self.assertEqual(request.call_count, 3)
            self.assertTrue(all(call.args[0].endswith("-malik.json") for call in request.call_args_list))
        with mock.patch.object(importer, "fetch_bytes", side_effect=AssertionError("offline must not fetch")):
            before = {path.relative_to(self.root).as_posix(): importer.sha(path.read_bytes()) for path in (self.root / "materials").rglob("*") if path.is_file()}
            offline, _ = importer.run(self.args())
            after = {path.relative_to(self.root).as_posix(): importer.sha(path.read_bytes()) for path in (self.root / "materials").rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(offline, second)

    def test_later_access_failure_preserves_completed_book_and_does_not_retry(self):
        self.plan["books"] = ["bukhari", "malik"]
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(self.plan["books"])
        def fetch(key):
            if key == "editions/ara-malik.json":
                raise importer.FetchFailure("TEST HTTP 403", access_denied=True)
            return inputs[key], {"url": importer.provider_url(key), "retrieved_at": "TEST"}
        with mock.patch.object(importer, "fetch_bytes", side_effect=fetch):
            summary, code = importer.run(self.args(fetch=True, export_only=False))
        self.assertEqual(code, 1)
        self.assertEqual(summary["completed_books"], ["bukhari"])
        with mock.patch.object(importer, "fetch_bytes", side_effect=AssertionError("denial must not retry")):
            offline, code = importer.run(self.args())
            self.assertEqual(code, 0)
            self.assertEqual(offline, summary)
            with self.assertRaisesRegex(ValueError, "access denials"):
                importer.run(self.args(fetch=True, export_only=False, retry_failed=True))

    def test_invalid_edition_is_preserved_as_rejected_evidence_not_active_input(self):
        inputs = self.inputs()
        inputs["editions/urd-bukhari.json"] = importer.encoded({"metadata": {}, "hadiths": []})
        with mock.patch.object(importer, "fetch_bytes", side_effect=lambda key: (inputs[key], {"url": importer.provider_url(key), "retrieved_at": "TEST"})):
            summary, code = importer.run(self.args(fetch=True, export_only=False))
        state = importer.read_json(self.root, importer.IMPORT + "/state.json")
        self.assertEqual(code, 1)
        self.assertEqual(summary["registered_occurrences"], 0)
        self.assertNotIn("editions/urd-bukhari.json", state["inputs"])
        self.assertIn("editions/urd-bukhari.json", state["rejected_inputs"])
        self.assertEqual(importer.run(self.args())[1], 0)

    def test_adoption_verifies_pinned_receipts_and_shards_preserve_ids(self):
        directory = self.root / "seed"
        directory.mkdir()
        raw = self.inputs()["editions/ara-bukhari.json"]
        (directory / "ara-bukhari.json").write_bytes(raw)
        receipt = {"url": importer.provider_url("editions/ara-bukhari.json"), "commit": importer.REVISION,
                   "sha256": importer.sha(raw), "bytes": len(raw), "retrieved_at": "TEST"}
        (directory / "ara-bukhari.receipt.json").write_bytes(importer.encoded(receipt))
        self.assertEqual(importer.adopt_input(self.root, directory, "editions/ara-bukhari.json")[0], raw)
        receipt["commit"] = "0" * 40
        (directory / "ara-bukhari.receipt.json").write_bytes(importer.encoded(receipt))
        with self.assertRaisesRegex(ValueError, "revision/URL"):
            importer.adopt_input(self.root, directory, "editions/ara-bukhari.json")
        records = [{"id": "TEST-" + str(i), "edition": importer.EDITION, "text": "TEST " * 50} for i in range(4)]
        shards = importer.canonical_shards(records, limit=450)
        recovered = [json.loads(line) for _, data in shards for line in data.splitlines()]
        self.assertEqual([row["id"] for row in recovered], [row["id"] for row in records])
        self.assertTrue(all(len(data) <= 450 for _, data in shards))
        with self.assertRaisesRegex(ValueError, "exceeds"):
            importer.canonical_shards(records, limit=10)


if __name__ == "__main__":
    unittest.main()
