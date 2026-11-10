"""Synthetic fixtures only: do not treat fixture strings as religious source text."""
import contextlib,hashlib,io,json,pathlib,sqlite3,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import import_hadeethenc as imp
import validate_hadeethenc as val
class ImportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.input=self.root/'input';self.input.mkdir();(self.input/'raw').mkdir();self.out=self.root/'candidate'
  entries=[]
  for lang in list(imp.LANGUAGES)+['ar']:
   p=self.input/'raw'/f'{lang}.sqlite';db=sqlite3.connect(p)
   db.execute('CREATE TABLE categories(id INTEGER PRIMARY KEY,title TEXT,num INTEGER,parent_id INTEGER)');db.execute("INSERT INTO categories VALUES(1,'FIXTURE TOPIC',1,0)")
   db.execute('CREATE TABLE category_hadeeth(id INTEGER PRIMARY KEY,category_id INTEGER,hadeeth_id INTEGER)');db.execute('INSERT INTO category_hadeeth VALUES(1,1,101)')
   if lang=='ar':
    db.execute('CREATE TABLE hadeeths(id INTEGER,title TEXT,title_clean TEXT,hadeeth TEXT,hadeeth_clean TEXT,explanation TEXT,explanation_clean TEXT,hints TEXT,words_meanings TEXT,grade TEXT,attribution TEXT,reference TEXT,tarteeb INTEGER,version INTEGER,current INTEGER)')
    db.execute('INSERT INTO hadeeths VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(101,'FIXTURE','','ARABIC FIXTURE','','COMMENTARY FIXTURE','','[]',None,'GRADE FIXTURE','ATTRIBUTION FIXTURE','BIBLIOGRAPHY FIXTURE\n',1,1,1))
   else:
    db.execute('CREATE TABLE hadeeths(id INTEGER PRIMARY KEY,title TEXT,hadeeth TEXT,explanation TEXT,hints TEXT,hadeeth_ar TEXT,grade TEXT,attribution TEXT,tarteeb INTEGER,ar_version INTEGER)')
    ar='DIFFERENT ARABIC FIXTURE' if lang=='zh' else 'ARABIC FIXTURE'
    db.execute('INSERT INTO hadeeths VALUES(?,?,?,?,?,?,?,?,?,?)',(101,'FIXTURE','TRANSLATION FIXTURE '+lang,'COMMENTARY FIXTURE','[]',ar,'GRADE FIXTURE','ATTRIBUTION FIXTURE',1,2 if lang=='ja' else 1))
   db.commit();db.close();archive=p.with_suffix('.sqlite.zip')
   with zipfile.ZipFile(archive,'w') as z:z.write(p,p.name)
   entries.append({'language':lang,'local_path':'raw/'+p.name,'archive_path':'raw/'+archive.name,'sqlite_sha256':imp.sha(p.read_bytes()),'sha256':imp.sha(archive.read_bytes()),'source_url':'https://example.invalid/fixture','final_url':'https://example.invalid/fixture','retrieved_at':'2000-01-01T00:00:00Z'})
  (self.input/'export-manifest-v2.json').write_text(json.dumps(entries),encoding='utf-8')
  with contextlib.redirect_stdout(io.StringIO()):imp.build(self.input,self.out)
 def tearDown(self):self.tmp.cleanup()
 def test_lossless_import_and_version_quarantine(self):
  with contextlib.redirect_stdout(io.StringIO()):self.assertTrue(val.validate(self.out))
  summary=json.loads((self.out/'reports/summary.json').read_text());self.assertEqual(summary['total_translation_entries'],6);self.assertEqual(summary['arabic_exact_alignment_count'],4);self.assertEqual(summary['arabic_alignment_exception_count'],2)
 def test_modified_text_is_rejected_even_with_updated_output_hash(self):
  collection=json.loads((self.out/'collections.json').read_text())['collections'][0];p=self.out/collection['records_path'];r=json.loads(p.read_text(encoding='utf-8'));r['texts']['translation_verbatim']='CORRUPTED FIXTURE';p.write_text(json.dumps(r)+'\n',encoding='utf-8')
  m=p.parent/'manifest.json';meta=json.loads(m.read_text());meta['coverage']['records_sha256']=imp.sha(p.read_bytes());m.write_text(json.dumps(meta),encoding='utf-8')
  with contextlib.redirect_stdout(io.StringIO()):self.assertFalse(val.validate(self.out))
 def test_publication_gate_stays_closed(self):
  gate=json.loads((self.out/'PUBLICATION-GATE.json').read_text());self.assertFalse(gate['allowed']);self.assertEqual(gate['release_eligible_records'],0)
if __name__=='__main__':unittest.main()
