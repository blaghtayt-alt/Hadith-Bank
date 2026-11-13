"""Check note anchors against saved main-story text with harmless TEST data."""
import copy
import gzip
import hashlib
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_bn_source_context import validate_note, validate_story_stream

class BengaliNoteBindingTests(unittest.TestCase):
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
