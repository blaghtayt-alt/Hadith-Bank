"""Read-only regression checks against the exact published six-language snapshot."""
import json,pathlib,sys,unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import search_hadeethenc
class PublicSearchTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.registry=json.loads((ROOT/'datasets/hadeethenc/collections.json').read_text(encoding='utf-8'))
 def test_six_language_counts_without_network(self):
  expected={'ja':281,'fil':1949,'vi':1203,'zh-CN':2256,'uz':420,'hi':2314}
  with mock.patch('socket.create_connection',side_effect=AssertionError('Search must not use a network')):
   for lang,count in expected.items():
    result=search_hadeethenc.search(ROOT,language=lang,limit=0)
    self.assertEqual(result['matched'],count);self.assertIn('pending',result['warning'])
 def test_actual_translation_and_arabic_are_returned(self):
  collection=self.registry['collections'][0]
  with (ROOT/collection['records_path']).open(encoding='utf-8') as stream:record=json.loads(next(stream))
  result=search_hadeethenc.search(ROOT,language=collection['language'],entry_id=record['source_entry_id'],limit=1)
  self.assertEqual(result['matched'],1);hit=result['results'][0]
  self.assertEqual(hit['arabic'],record['texts']['arabic_verbatim']);self.assertEqual(hit['translation'],record['texts']['translation_verbatim'])
  self.assertEqual(hit['release_status'],'published_unreviewed_source_import');self.assertEqual(hit['ai_translation'],'unknown')
 def test_pending_records_are_not_reported_as_approved(self):
  result=search_hadeethenc.search(ROOT,language='ja',limit=1,approved_only=True)
  self.assertEqual(result['matched'],0);self.assertEqual(result['results'],[])
if __name__=='__main__':unittest.main()
