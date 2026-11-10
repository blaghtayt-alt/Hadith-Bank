"""Offline attachment search tests. Every text/source here is synthetic."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "search_attachments.py"
SPEC = importlib.util.spec_from_file_location("attachment_search", SCRIPT)
search_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(search_module)


def synthetic_record(record_id, language="zh-CN", number="7", ai_translation=False):
    """A fabricated fixture, not a quotation or a candidate-corpus passage."""
    return {
        "id": record_id, "record_id": record_id, "language": language,
        "record_type": "narration",
        "content_kind": "source_narration_occurrence_not_independently_classified",
        "title": {"arabic": None, "translation": "Synthetic title"},
        "text": {"arabic": "نَصّ تَجْرِيبِيّ", "translation": "合成\n示例 Ａｌｐｈａ"},
        "book": {"title": "Synthetic book", "chapter": "Synthetic section"},
        "number": {"in_book": number, "canonical": None},
        "narrator": {"name": "Synthetic narrator", "evidence": "synthetic fixture"},
        "source": {"source_id": "synthetic-source", "format": "pdf", "entry_id": number},
        "translator": {"name": None, "evidence": None},
        "page": {"pdf": [2], "printed": ["1"]},
        "references": [{"verbatim": "Synthetic reference"}],
        "commentary": [{"text": "commentary-only-token"}],
        "footnotes": [{"text": "footnote-only-token"}],
        "grading": {"value": None, "assessor": None},
        "ai_translation": ai_translation,
        "source_structure_tags": [{
            "tag_id": "synthetic-section-1", "origin": "source_book_structure",
            "language": language, "field": "book.section", "value_verbatim": "合成見出し",
            "source_id": "synthetic-source", "evidence": {"pdf_page": 2},
        }],
        "topic_tags": [],
        "editorial_tags": {
            "origin": "import_pipeline_not_publisher",
            "values": ["private_intake", "synthetic_fixture"],
        },
        "review": {
            "release_status": "private_candidate", "release_eligible": False,
            "independent_pro_qc": "pending", "issues": ["synthetic_review_flag"],
        },
    }


class AttachmentSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.collections = []

    def add_collection(self, records, language="zh-CN", book="synthetic-book", edition="snapshot-a"):
        relative = f"languages/{language}/books/{book}/editions/{edition}/records.json"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = (json.dumps(records, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        path.write_bytes(data)
        collection = {
            "language": language, "source_language_code": "zh" if language == "zh-CN" else language,
            "book": book, "edition": edition, "records_path": relative,
            "records_sha256": hashlib.sha256(data).hexdigest(), "count": len(records),
        }
        self.collections.append(collection)
        self.save_index()
        return collection, path

    def save_index(self):
        (self.root / "collections.json").write_text(json.dumps({
            "schema": search_module.INDEX_SCHEMA, "collections": self.collections,
        }), encoding="utf-8")

    def test_verbatim_results_keep_occurrences_editions_and_ai_flags(self):
        first = synthetic_record("fixture-first", ai_translation=False)
        second = synthetic_record("fixture-second", ai_translation="unknown")
        third = synthetic_record("fixture-third", language="ja", ai_translation=True)
        self.add_collection([first])
        self.add_collection([second], edition="snapshot-b")
        self.add_collection([third], language="ja")
        result = search_module.search(self.root, entry_id="7", limit=10)
        self.assertEqual((result["matched"], result["shown"]), (3, 3))
        self.assertEqual(len(result["verified_collections"]), 3)
        for original, found in zip((first, second, third), result["results"]):
            self.assertEqual(found["text"], original["text"])
            self.assertEqual(found["review"], original["review"])
            self.assertEqual(found["ai_translation"], original["ai_translation"])
            self.assertIn("Independent Pro QC: pending", found["warning"])
            self.assertIn("release_eligible=false", found["warning"])
        self.assertIn("ai_translation=false", result["results"][0]["warning"])
        self.assertNotIn("authorship is not established", result["results"][0]["warning"])
        self.assertIn("ai_translation=unknown", result["results"][1]["warning"])
        self.assertIn("ai_translation=true", result["results"][2]["warning"])

    def test_exact_identity_filters_aliases_and_limit_do_not_merge(self):
        self.add_collection([synthetic_record("fixture-a")])
        self.add_collection([synthetic_record("fixture-b", number=7)], edition="snapshot-b")
        self.add_collection([synthetic_record("fixture-c", language="ja")], language="ja")
        result = search_module.search(self.root, language="zh", entry_id="7", limit=1)
        self.assertEqual((result["matched"], result["shown"]), (2, 1))
        self.assertEqual(result["filters"]["language"], "zh-CN")
        self.assertEqual(len(result["verified_collections"]), 2)
        result = search_module.search(self.root, language="zh-CN", book="synthetic-book", edition="snapshot-b")
        self.assertEqual([x["id"] for x in result["results"]], ["fixture-b"])
        self.assertEqual(search_module.search(self.root, entry_id="fixture-a")["matched"], 1)
        self.assertEqual(search_module.search(self.root, entry_id="fixture")["matched"], 0)
        self.assertEqual(search_module.search(self.root, entry_id="07")["matched"], 0)
        self.assertEqual(search_module.search(self.root, limit=0)["matched"], 3)
        self.assertEqual(search_module.search(self.root, limit=0)["results"], [])

    def test_structure_editorial_and_future_publisher_tags_remain_separate(self):
        fixture = synthetic_record("fixture-tags")
        fixture["topic_tags"] = [{
            "tag_id": "synthetic-future-category", "origin": "synthetic_publisher_taxonomy",
            "value_verbatim": "Synthetic future category", "evidence": {"row": 1},
        }]
        self.add_collection([fixture])
        for tag in ("private_intake", "synthetic-section-1", "合成見出し", "synthetic-future-category", "Synthetic future category"):
            with self.subTest(tag=tag):
                found = search_module.search(self.root, tag=tag)
                self.assertEqual(found["matched"], 1)
                self.assertEqual(found["results"][0]["source_structure_tags"], fixture["source_structure_tags"])
                self.assertEqual(found["results"][0]["topic_tags"], fixture["topic_tags"])
        self.assertEqual(search_module.search(self.root, tag="private")["matched"], 0)
        self.assertEqual(search_module.search(self.root, kind="narration")["matched"], 1)
        self.assertEqual(search_module.search(self.root, kind=fixture["content_kind"])["matched"], 1)
        self.assertEqual(search_module.search(self.root, kind="prophetic")["matched"], 0)

    def test_provider_number_in_actual_intake_shape_is_resolved_exactly(self):
        fixture = synthetic_record("fixture-provider-id", number=None)
        fixture["number"] = {"in_book": None, "source_entry_id": "314", "canonical": None}
        fixture["source"] = {"source_id": "synthetic-spreadsheet", "format": "xlsx"}
        fixture["source_structure_tags"] = []
        fixture["topic_tags"] = []
        self.add_collection([fixture], book="synthetic-provider")
        found = search_module.search(self.root, entry_id="314")
        self.assertEqual(found["matched"], 1)
        self.assertEqual(found["results"][0]["id"], fixture["id"])
        self.assertEqual(found["results"][0]["number"], fixture["number"])
        self.assertEqual(search_module.search(self.root, entry_id="31")["matched"], 0)

    def test_unicode_query_and_commentary_opt_in_preserve_original_text(self):
        fixture = synthetic_record("fixture-text")
        self.add_collection([fixture])
        for query in ("合成示例 alpha", "نص تجريبي", "Synthetic narrator", "合成見出し"):
            with self.subTest(query=query):
                found = search_module.search(self.root, query)
                self.assertEqual(found["matched"], 1)
                self.assertEqual(found["results"][0]["text"], fixture["text"])
                self.assertNotIn("commentary", found["results"][0])
        self.assertEqual(search_module.search(self.root, "alpha absent-term")["matched"], 0)
        for query in ("commentary-only-token", "footnote-only-token"):
            self.assertEqual(search_module.search(self.root, query)["matched"], 0)
            found = search_module.search(self.root, query, include_commentary=True)
            self.assertEqual(found["matched"], 1)
            self.assertEqual(found["results"][0]["commentary"], fixture["commentary"])
            self.assertEqual(found["results"][0]["footnotes"], fixture["footnotes"])

    def test_altered_bytes_and_count_disagreement_fail_before_returning_results(self):
        collection, path = self.add_collection([synthetic_record("fixture-integrity")])
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            search_module.search(self.root, limit=0)
        path.write_bytes(original)
        collection["count"] = 2
        self.save_index()
        with self.assertRaisesRegex(ValueError, "Record count mismatch"):
            search_module.search(self.root)

    def test_path_traversal_absolute_backslash_and_wrong_layout_are_rejected(self):
        collection, path = self.add_collection([synthetic_record("fixture-path")])
        for malicious in ("../outside.json", str(path), "languages\\outside.json", "languages/zh-CN/../records.json", "other/records.json"):
            with self.subTest(path=malicious):
                collection["records_path"] = malicious
                self.save_index()
                with self.assertRaisesRegex(ValueError, "[Pp]ath"):
                    search_module.search(self.root)

    def test_symlinks_cannot_escape_for_records_or_manifest(self):
        collection, path = self.add_collection([synthetic_record("fixture-link")])
        with tempfile.TemporaryDirectory() as outside_dir:
            outside = Path(outside_dir)
            external_records = outside / "records.json"
            external_records.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(external_records)
            with self.assertRaisesRegex(ValueError, "resolved outside root"):
                search_module.search(self.root)
            path.unlink()
            path.write_bytes(external_records.read_bytes())
            external_index = outside / "collections.json"
            index = self.root / "collections.json"
            external_index.write_bytes(index.read_bytes())
            index.unlink()
            index.symlink_to(external_index)
            with self.assertRaisesRegex(ValueError, "resolved outside root"):
                search_module.search(self.root)

    def test_malformed_manifest_records_and_duplicate_ids_fail_closed(self):
        collection, path = self.add_collection([synthetic_record("fixture-duplicate")])
        self.add_collection([synthetic_record("fixture-duplicate")], edition="snapshot-b")
        with self.assertRaisesRegex(ValueError, "Duplicate occurrence id"):
            search_module.search(self.root)
        self.collections.pop()
        self.save_index()
        bad_records = json.dumps({"not": "an array"}).encode()
        path.write_bytes(bad_records)
        collection["records_sha256"] = hashlib.sha256(bad_records).hexdigest()
        self.save_index()
        with self.assertRaisesRegex(ValueError, "JSON array"):
            search_module.search(self.root)
        (self.root / "collections.json").write_text('{"schema":"other","collections":[]}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            search_module.search(self.root)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            search_module.search(self.root, limit=-1)

    def test_cli_returns_json_and_fails_without_partial_output_on_bad_hash(self):
        fixture = synthetic_record("fixture-cli")
        collection, path = self.add_collection([fixture])
        command = [sys.executable, str(SCRIPT), "--root", str(self.root), "--language", "zh", "--id", "7"]
        success = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(success.returncode, 0, success.stderr)
        result = json.loads(success.stdout)
        self.assertEqual(result["results"][0]["text"], fixture["text"])
        path.write_bytes(path.read_bytes() + b" ")
        failure = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertNotEqual(failure.returncode, 0)
        self.assertEqual(failure.stdout, "")
        self.assertIn("SHA-256 mismatch", failure.stderr)


if __name__ == "__main__":
    unittest.main()
