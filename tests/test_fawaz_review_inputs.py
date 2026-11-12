"""Small synthetic fixtures for integrity and immutable baseline guarantees."""

import copy
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fawaz_review_inputs as inputs


PROVIDER = "fixture/source"
REVISION = "a" * 40


def decision(number, **changes):
    value = {
        "provider_book": "fixture", "provider_edition": "eng-fixture",
        "typed_hadithnumber": str(number), "source_text_sha256": "0" * 64,
        "quotation_spans": [[0, 7]], "decision_note": "Exact fixture: α\nβ",
    }
    value.update(changes)
    return value


def catalog(decisions):
    return {"schema": inputs.CATALOG_SCHEMA, "repository": PROVIDER,
            "revision": REVISION, "decisions": decisions}


class ReviewInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.baseline = catalog([decision(1)])
        self.recovered = catalog([decision(1), decision(2)])
        self.extra = catalog([decision(3)])
        self.extra_members = []
        self.raw_extra = None
        self.write_fixture()

    def write(self, path, raw):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return {"path": path, "bytes": len(raw), "sha256": inputs.sha256(raw)}

    def write_fixture(self):
        baseline = self.write(inputs.BASELINE_PATH, inputs.json_bytes(self.baseline))
        recovered_raw = inputs.json_bytes(self.recovered)
        recovered = self.write("evidence/recovered.json.gz", inputs.gzip_bytes(recovered_raw))
        recovered.update(raw_bytes=len(recovered_raw), raw_sha256=inputs.sha256(recovered_raw))
        extra = self.raw_extra if self.raw_extra is not None else inputs.json_bytes(self.extra)
        manifest = {
            "schema": inputs.ARCHIVE_SCHEMA,
            "files": [{"path": "review.json", "bytes": len(extra),
                       "sha256": inputs.sha256(extra), "decisions": len(self.extra["decisions"])}],
        }
        manifest_raw = inputs.json_bytes(manifest)
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for name, raw, kind in [("review.json", extra, "file"),
                                    ("manifest.json", manifest_raw, "file"),
                                    *self.extra_members]:
                member = tarfile.TarInfo(name)
                member.mtime = 0
                member.size = len(raw)
                if kind == "symlink":
                    member.type = tarfile.SYMTYPE
                    member.linkname = "outside.json"
                    member.size = 0
                archive.addfile(member, io.BytesIO(raw) if member.isfile() else None)
        archive = self.write("evidence/reviews.tar.gz", inputs.gzip_bytes(buffer.getvalue()))
        archive["manifest"] = {"path": "manifest.json", "bytes": len(manifest_raw),
                               "sha256": inputs.sha256(manifest_raw)}
        self.manifest = {"schema": inputs.INPUT_SCHEMA, "repository": PROVIDER,
                         "revision": REVISION, "baseline": baseline,
                         "recovered_catalog": recovered, "phase_archive": archive}
        self.write_manifest()

    def write_manifest(self):
        self.write(inputs.MANIFEST_PATH, inputs.json_bytes(self.manifest))

    def load(self):
        return inputs.load_review_catalog(self.root, repository=PROVIDER, revision=REVISION)

    def test_additive_values_and_deterministic_output(self):
        paths = [path for path in self.root.rglob("*") if path.is_file()]
        before = {str(path): path.read_bytes() for path in paths}
        value = self.load()
        self.assertEqual(value["decisions"], [decision(1), decision(2), decision(3)])
        self.assertEqual(value["compressed_input_assembly"]["baseline_decisions_preserved"], 1)
        first = inputs.gzip_bytes(inputs.json_bytes(value))
        second = inputs.gzip_bytes(inputs.json_bytes(self.load()))
        self.assertEqual(first, second)
        self.assertEqual(before, {str(path): path.read_bytes() for path in paths})

    def test_legacy_catalog_and_absent_catalog(self):
        (self.root / inputs.MANIFEST_PATH).unlink()
        self.assertEqual(self.load(), self.baseline)
        (self.root / inputs.BASELINE_PATH).unlink()
        self.assertIsNone(self.load())

    def add_fresh_review(self, value):
        raw = inputs.json_bytes(value)
        spec = self.write("evidence/fresh.json.gz", inputs.gzip_bytes(raw))
        spec.update(compression="gzip", raw_bytes=len(raw), raw_sha256=inputs.sha256(raw))
        self.manifest["additional_reviews"] = [spec]
        self.write_manifest()
        return spec

    def test_new_review_batch_adds_exact_values_and_rejects_prior_identity(self):
        self.add_fresh_review(catalog([decision(4)]))
        self.assertEqual(self.load()["decisions"], [decision(n) for n in range(1, 5)])
        for number in (1, 2, 3):
            with self.subTest(previous=number):
                self.add_fresh_review(catalog([decision(number)]))
                with self.assertRaisesRegex(ValueError, "previously decided identity"):
                    self.load()

    def test_new_review_batch_rejects_corruption_duplicate_paths_and_wrong_revision(self):
        spec = self.add_fresh_review(catalog([decision(4)]))
        (self.root / spec["path"]).write_bytes(b"damaged")
        with self.assertRaisesRegex(ValueError, "byte count changed|SHA-256"):
            self.load()
        spec = self.add_fresh_review(catalog([decision(4)]))
        self.manifest["additional_reviews"].append(copy.deepcopy(spec))
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "Repeated additional"):
            self.load()
        wrong = catalog([decision(4)])
        wrong["revision"] = "c" * 40
        self.add_fresh_review(wrong)
        with self.assertRaisesRegex(ValueError, "revision mismatch"):
            self.load()

    def test_checksum_and_expanded_hash_fail_closed(self):
        for component in ("baseline", "recovered_catalog", "phase_archive"):
            with self.subTest(component=component):
                self.write_fixture()
                target = self.root / self.manifest[component]["path"]
                raw = bytearray(target.read_bytes())
                raw[-1] ^= 1
                target.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    self.load()
        self.write_fixture()
        self.manifest["recovered_catalog"]["raw_sha256"] = "f" * 64
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "expanded checksum"):
            self.load()

    def test_changed_or_removed_baseline_rejected_even_with_updated_hashes(self):
        for updated in ([decision(1, decision_note="Changed"), decision(2)], [decision(2)]):
            with self.subTest(updated=updated):
                self.recovered = catalog(updated)
                self.write_fixture()
                with self.assertRaisesRegex(ValueError, "baseline decision"):
                    self.load()

    def test_repeated_identity_identical_or_conflicting_is_rejected(self):
        for repeated in (decision(2), decision(2, decision_note="Different")):
            with self.subTest(repeated=repeated):
                self.extra = catalog([repeated])
                self.write_fixture()
                with self.assertRaisesRegex(ValueError, "repeat a recovered identity"):
                    self.load()
        self.extra = catalog([decision(3), decision(3)])
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "Repeated decision identity"):
            self.load()

    def test_repository_revision_and_schema_mismatch_rejected(self):
        for field, wrong in (("repository", "another/source"), ("revision", "b" * 40),
                             ("schema", "unknown-review-schema")):
            with self.subTest(field=field):
                self.extra = catalog([decision(3)])
                self.extra[field] = wrong
                self.write_fixture()
                with self.assertRaisesRegex(ValueError, "mismatch|Unsupported"):
                    self.load()
        self.extra = catalog([decision(3)])
        self.write_fixture()
        self.manifest["revision"] = "b" * 40
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "revision mismatch"):
            self.load()

    def test_unsafe_duplicate_or_unlisted_tar_members_rejected(self):
        for member, message in (
            (("../escape.json", b"{}", "file"), "Unsafe relative"),
            (("link.json", b"", "symlink"), "regular tar members"),
            (("review.json", b"{}", "file"), "Repeated tar member"),
            (("unlisted.json", b"{}", "file"), "unlisted JSON"),
        ):
            with self.subTest(member=member[0]):
                self.extra_members = [member]
                self.write_fixture()
                with self.assertRaisesRegex(ValueError, message):
                    self.load()
        self.assertFalse((self.root.parent / "escape.json").exists())

    def test_duplicate_json_keys_rejected_even_with_valid_file_hash(self):
        raw = inputs.json_bytes(self.extra).decode("utf-8")
        self.raw_extra = raw.replace('"schema":', '"schema":"ignored","schema":').encode("utf-8")
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate JSON object key"):
            self.load()

    def test_file_size_and_path_limits_rejected(self):
        self.manifest["recovered_catalog"]["raw_bytes"] = inputs.MAX_RAW_BYTES + 1
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "excessive byte count"):
            self.load()
        self.write_fixture()
        self.manifest["phase_archive"]["path"] = "../outside.tar.gz"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "Unsafe relative input path"):
            self.load()


if __name__ == "__main__":
    unittest.main()
