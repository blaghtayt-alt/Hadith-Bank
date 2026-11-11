"""Focused regression checks for the source-package transport boundary."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "restore_chinese_ibn_majah.py"
SPEC = importlib.util.spec_from_file_location("restore_chinese_ibn_majah", SCRIPT)
restore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore)


class TransportGuards(unittest.TestCase):
    def test_corrupted_part_is_rejected_before_canonical_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "part.bin"
            expected = b"original preserved bytes"
            path.write_bytes(b"changed! preserved bytes")
            spec = {"path": "part.bin", "size": len(expected),
                    "sha256": hashlib.sha256(expected).hexdigest()}
            with self.assertRaisesRegex(ValueError, "Hash mismatch|Wrong size"):
                restore.assemble_archive(root, {"parts": [spec]}, root / "archive")
            self.assertFalse((root / "materials").exists())

    def test_traversal_member_is_rejected_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, stage = root / "bad.tar.gz", root / "staged"
            stage.mkdir()
            with tarfile.open(archive, "w:gz") as target:
                member = tarfile.TarInfo("../escape.txt")
                member.size = 1
                target.addfile(member, io.BytesIO(b"x"))
            with self.assertRaisesRegex(ValueError, "traversal"):
                restore.stage_archive(archive, [], stage)
            self.assertEqual(list(stage.iterdir()), [])
            self.assertFalse((root / "escape.txt").exists())

    def test_symlink_and_duplicate_members_are_rejected(self):
        for kind in ("symlink", "duplicate"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive, stage = root / "bad.tar.gz", root / "staged"
                stage.mkdir()
                name = restore.MATERIAL + "/sample.txt"
                with tarfile.open(archive, "w:gz") as target:
                    member = tarfile.TarInfo(name)
                    if kind == "symlink":
                        member.type = tarfile.SYMTYPE
                        member.linkname = "/tmp/unrelated"
                        target.addfile(member)
                    else:
                        member.size = 1
                        target.addfile(member, io.BytesIO(b"x"))
                        target.addfile(member, io.BytesIO(b"x"))
                spec = {"path": name, "size": 0 if kind == "symlink" else 1,
                        "sha256": hashlib.sha256(b"x").hexdigest()}
                with self.assertRaises(ValueError):
                    restore.stage_archive(archive, [spec], stage)
                self.assertEqual(list(stage.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
