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
                     "books": self.books, "languages": list(importer.LANGUAGES), "max_books_per_batch": 7}
        importer.save_json(self.root, importer.PLAN, self.plan)
        self.state = {"schema": "hadith-bank-fawaz-bulk-state-v1", "revision": importer.REVISION, "inputs": {}, "stop": None}

    def inputs(self, books=None):
        books = books or self.books
        values = {"editions.json": importer.encoded(catalog(books)),
                  "README.md": b"TEST whole edition documentation\n", "LICENSE": b"TEST source license bytes\n",
                  "References.md": b"TEST project-wide credit https://example.invalid/source\n",
                  "CONTRIBUTING.md": b"TEST same provider numbering across editions\n"}
        for book in books:
            for prefix in importer.LANGUAGES:
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
        for prefix in importer.LANGUAGES:
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
        for prefix in importer.LANGUAGES:
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

    def test_duplicate_or_inconsistent_provider_identity_is_held(self):
        inputs = self.inputs()
        for prefix in importer.LANGUAGES:
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

    def test_non_prophetic_empty_and_explicit_intro_are_held_but_book_zero_is_not_enough(self):
        inputs = self.inputs()
        for prefix in importer.LANGUAGES:
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
        ]:
            with self.subTest(language=language, book=book):
                quotation, notes, spans = importer.split_compiler_note(text, book, language)
                self.assertEqual(quotation + "".join(notes), text)
                self.assertEqual(quotation, text[slice(*spans["quotation"])])
                self.assertEqual(notes, [text[slice(*item)] for item in spans["notes"]])
                self.assertIn("pending", spans["note_embedded_narration_extraction"])
        untouched = "TEST Anas ibn Malik said TEST"
        self.assertEqual(importer.split_compiler_note(untouched, "malik", "en")[0], untouched)

    def test_ambiguous_compiler_boundaries_remain_outside_hadith_text(self):
        inputs = self.inputs()
        inputs["editions/ara-bukhari.json"] = importer.encoded(source_data("bukhari", [
            row(1, "TEST قال رسول الله TEST quotation. قال أبو عبد الله TEST compiler material")]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary["registered_occurrences"], 0)
        self.assertEqual(summary["by_book"]["bukhari"]["by_hold_reason"], {"commentary_boundary_pending": 1})

    def test_nabidh_and_wishes_about_prophet_do_not_establish_speaker_identity(self):
        inputs = self.inputs()
        arabic = [row(1, 'TEST عن النبيذ TEST'),
                  row(2, 'TEST وددت أن رسول الله صلى الله عليه وسلم كان عهد إلينا TEST'),
                  row(3, 'TEST سمعت عمر علي منبر رسول الله صلى الله عليه وسلم يقول TEST')]
        for prefix in importer.LANGUAGES:
            rows = arabic if prefix == 'ara' else [row(i, 'TEST independent source statement') for i in (1, 2, 3)]
            inputs['editions/' + prefix + '-bukhari.json'] = importer.encoded(source_data('bukhari', rows))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 0)
        self.assertEqual(summary['by_book']['bukhari']['by_hold_reason']['attribution_subject_requires_review'], 2)

    def test_unlabelled_tirmidhi_grading_tail_requires_a_boundary_review(self):
        self.plan['books'] = ['tirmidhi']
        importer.save_json(self.root, importer.PLAN, self.plan)
        inputs = self.inputs(['tirmidhi'])
        inputs['editions/ara-tirmidhi.json'] = importer.encoded(source_data('tirmidhi', [
            row(1, 'TEST قال رسول الله TEST quotation. هذا حديث حسن صحيح TEST compiler analysis')]))
        self.seed(inputs)
        summary, _ = importer.run(self.args())
        self.assertEqual(summary['registered_occurrences'], 0)
        self.assertEqual(summary['by_book']['tirmidhi']['by_hold_reason'], {'commentary_boundary_pending': 1})

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
