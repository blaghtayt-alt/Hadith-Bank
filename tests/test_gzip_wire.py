"""Lossless deterministic generated gzip strategy selection, synthetic-only tests."""
import gzip
import hashlib
from pathlib import Path
import random
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from gzip_wire import smallest_gzip


class GeneratedGzipChoiceTests(unittest.TestCase):
    def test_deterministic_and_never_larger_than_gzip9(self):
        rng = random.Random(98017)
        examples = [b'', b'\x00', b'\xff\x00' * 10000,
                    ('العربية বাংলা 漢字 日本語 Hindi Urdu English ' * 4000).encode(),
                    b'{"id":1,"reading":"TEST"}\n' * 16000,
                    bytes(rng.randrange(0, 256) for _ in range(128 * 1024))]
        for raw in examples:
            with self.subTest(sha=hashlib.sha256(raw).hexdigest()[:12]):
                expected = gzip.compress(raw, compresslevel=9, mtime=0)
                chosen = smallest_gzip(raw)
                self.assertLessEqual(len(chosen), len(expected))
                self.assertEqual(gzip.decompress(chosen), raw)
                self.assertEqual(chosen, smallest_gzip(raw))
                self.assertEqual(chosen[:2], b'\x1f\x8b')

    def test_safe_multiple_levels_and_strategies_are_exact_candidates(self):
        samples = [b'{"kind":"TEST","source":"synthetic"}\n' * 1000,
                   b'UTF-8 \xe2\x98\x83\n' * 2000,
                   b'a' * 4096 + b'b' * 8192]
        for raw in samples:
            variants = [gzip.compress(raw, compresslevel=9, mtime=0)]
            for mem, strategy in ((9,zlib.Z_DEFAULT_STRATEGY),
                                  (9,zlib.Z_FILTERED),(8,zlib.Z_FILTERED)):
                compressor = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=31,
                                               memLevel=mem, strategy=strategy)
                variants.append(compressor.compress(raw) + compressor.flush())
            selected = smallest_gzip(raw)
            self.assertEqual(len(selected), min(len(x) for x in variants))
            self.assertEqual(gzip.decompress(selected), raw)

    def test_nonbytes_input_is_not_accepted(self):
        with self.assertRaises(TypeError):
            smallest_gzip("not raw bytes")


if __name__ == '__main__':
    unittest.main()
