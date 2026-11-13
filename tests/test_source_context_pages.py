"""Source-only pages must be verified and remain separate from narration records."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import source_context_pages as pages

class SourceContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.folder = self.root / 'source-context' / 'test'
        self.folder.mkdir(parents=True)
        self.body = b'<html>TEST context</html>'
        (self.folder / 'reader.html').write_bytes(self.body)
        self.manifest = {'schema':'hadith-bank-source-context-v1','pages':[{'id':'test','title':'TEST source context','html':'source-context/test/reader.html','files':[{'path':'source-context/test/reader.html','bytes':len(self.body),'sha256':hashlib.sha256(self.body).hexdigest()}]}]}
        self.write_manifest()
    def write_manifest(self):
        (self.root / 'source-context/manifest.json').write_text(json.dumps(self.manifest),encoding='utf-8')
    def test_verified_context_is_staged_separately(self):
        entries=pages.load_context_pages(self.root)
        site=self.root/'site';site.mkdir()
        pages.stage_context_assets(self.root,site,entries)
        self.assertEqual((site/'source-context/test/reader.html').read_bytes(),self.body)
    def test_rejects_tampered_or_unsafe_files(self):
        (self.folder/'reader.html').write_bytes(b'tampered')
        with self.assertRaises(ValueError): pages.load_context_pages(self.root)
        (self.folder/'reader.html').write_bytes(self.body)
        self.manifest['pages'][0]['files'][0]['path']='source-context/../TEST'
        self.write_manifest()
        with self.assertRaises(ValueError): pages.load_context_pages(self.root)
    def test_bengali_assets_cannot_skip_their_required_gate(self):
        folder = self.root/'source-context/bn-riyadh-cp017'
        folder.mkdir()
        (folder/'reader.html').write_bytes(self.body)
        saved = self.manifest['pages']
        self.manifest['pages'] = []
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'omitted from its manifest'): pages.load_context_pages(self.root)
        self.manifest['pages'] = saved
        self.manifest['pages'][0]['html'] = 'source-context/bn-riyadh-cp017/reader.html'
        self.manifest['pages'][0]['files'][0]['path'] = 'source-context/bn-riyadh-cp017/reader.html'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'registered identity'): pages.load_context_pages(self.root)
        self.manifest['pages'][0]['id'] = 'bn-riyadh-cp017'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'source-binding gate'): pages.load_context_pages(self.root)
        (self.root/'source-context/manifest.json').unlink()
        with self.assertRaisesRegex(ValueError, 'without its manifest'): pages.load_context_pages(self.root)

    def test_absent_manifest_means_no_context_pages(self):
        (self.root/'source-context/manifest.json').unlink()
        self.assertEqual(pages.load_context_pages(self.root),[])

if __name__ == '__main__': unittest.main()
