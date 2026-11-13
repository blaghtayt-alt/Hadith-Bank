"""Check note anchors against saved main-story text with harmless TEST data."""
import base64
import copy
import gzip
import hashlib
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_bn_source_context import read_reader_data, require_bengali_site_files, validate_note, validate_story_stream

class BengaliNoteBindingTests(unittest.TestCase):
    def test_compressed_reader_preserves_exact_json_and_rejects_corruption(self):
        raw = '{"text":"TEST \uf079 বাংলা"}'.encode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        encoded = base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii')
        html = '<script id="reader-data" type="application/octet-stream" data-encoding="gzip-base64">'+encoded+'</script>'
        self.assertEqual(read_reader_data(html, digest)['text'], 'TEST \uf079 বাংলা')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            read_reader_data(html, '0'*64)
        with self.assertRaisesRegex(ValueError, 'compressed reader data is invalid'):
            read_reader_data(html.replace(encoded, 'invalid!'), digest)
        plain = '<script id="reader-data" type="application/json">'+raw.decode('utf-8')+'</script>'
        self.assertEqual(read_reader_data(plain, digest)['text'], 'TEST \uf079 বাংলা')
        with self.assertRaisesRegex(ValueError, 'missing or duplicated'):
            read_reader_data(html + plain, digest)

    def test_original_pdfs_must_be_staged_for_page_links(self):
        prefix = 'source-context/bn-riyadh-cp017/originals/'
        entry = {'files':[{'path':prefix+'bn_riyadh_01.pdf','publish_to_site':True},
                          {'path':prefix+'bn_riyadh_02.pdf','publish_to_site':True}]}
        require_bengali_site_files(entry)
        entry['files'][0]['publish_to_site'] = False
        with self.assertRaisesRegex(ValueError, 'original PDFs must be published'):
            require_bengali_site_files(entry)
        entry['files'] = entry['files'][1:]
        with self.assertRaisesRegex(ValueError, 'original PDFs must be published'):
            require_bengali_site_files(entry)

    def test_requires_exact_original_story_bytes(self):
        raw = 'TEST\r\u0002\uf079'.encode('utf-8')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'story.gz'
            with gzip.open(path, 'wb') as stream: stream.write(raw)
            validate_story_stream(path, hashlib.sha256(raw).hexdigest(), raw.decode('utf-8'))
            with self.assertRaisesRegex(ValueError, 'story text mismatch'):
                validate_story_stream(path, hashlib.sha256(raw).hexdigest(), 'TEST')
            with self.assertRaisesRegex(ValueError, 'story hash mismatch'):
                validate_story_stream(path, '0' * 64, raw.decode('utf-8'))

    def test_requires_exact_marker_range_and_note_parts(self):
        record = {'source_volume':1,'doc_story':'main','doc_cp_start':0,'doc_cp_end':3}
        note = {'cp_start':10,'cp_end':14,'raw_text':'TEST','main_cp_anchor':1,'main_anchor_char':'X'}
        parts = [{'source_volume':1,'story':'footnote','cp_start':10,'cp_end':12,'text_verbatim':'TE'},
                 {'source_volume':1,'story':'footnote','cp_start':12,'cp_end':14,'text_verbatim':'ST'}]
        validate_note(parts,note,record,'AXZ')
        for issue in ('marker','out_of_range','gap','text','volume'):
            p,n,r=copy.deepcopy((parts,note,record))
            if issue=='marker':n['main_anchor_char']='Z'
            if issue=='out_of_range':r['doc_cp_start']=2
            if issue=='gap':p[1]['cp_start']=13
            if issue=='text':p[1]['text_verbatim']='NO'
            if issue=='volume':p[1]['source_volume']=2
            with self.assertRaises(ValueError,msg=issue):validate_note(p,n,r,'AXZ')
        record['doc_story']='footnote';record['doc_cp_start']=999;record['doc_cp_end']=1000
        validate_note(parts,note,record,'AXZ')

if __name__=='__main__':unittest.main()
