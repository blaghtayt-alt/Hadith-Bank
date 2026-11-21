import hashlib, importlib.util, os, pathlib, subprocess, tempfile, unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import classify_integration_event as g
class SparseTests(unittest.TestCase):
 def run_case(self,dirs,mutate=False):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);src=root/'source';src.mkdir();dst=root/'checkout'
   env=dict(os.environ,GIT_ALLOW_PROTOCOL='file',GIT_TERMINAL_PROMPT='0')
   def git(where,*args):return subprocess.check_output(['git','-C',str(where),*args],env=env,stderr=subprocess.PIPE)
   git(src,'init','-q');git(src,'config','user.name','TEST');git(src,'config','user.email','test@example.invalid');git(src,'config','uploadpack.allowFilter','true')
   for p,status in g.EXPECTED_CHANGES.items():
    if status=='M':
     f=src/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('OLD '+p)
   git(src,'add','.');git(src,'commit','-qm','before');before=git(src,'rev-parse','HEAD').decode().strip()
   for p in g.EXPECTED_CHANGES:
    f=src/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('NEW '+p)
   git(src,'add','.');git(src,'commit','-qm','after');after=git(src,'rev-parse','HEAD').decode().strip()
   subprocess.check_output(['git','clone','--no-checkout','--filter=blob:none',src.as_uri(),str(dst)],env=env,stderr=subprocess.PIPE)
   git(dst,'sparse-checkout','set',*dirs);git(dst,'checkout','--detach',after)
   # Block ALL later acquisition, including local lazy fetch; only retained objects may satisfy adapter.
   git(dst,'remote','set-url','origin',str(root/'nonexistent-offline'))
   if mutate:(dst/'tests/test_import_deenhindi.py').write_text('tampered')
   payload=dict(before=before,after=after,ref='refs/heads/main',forced=False,created=False,deleted=False)
   pins={p:hashlib.sha256(('NEW '+p).encode()).hexdigest() for p in g.REVIEWED_HASHES}
   trace=[]
   def runner(root,*args):
    try:return g.git(root,*args)
    except ValueError:
     trace.append(args)
     raise
   with patch.object(g,'EXPECTED_BEFORE',before),patch.object(g,'REVIEWED_HASHES',pins),patch.dict(os.environ,env):
    result=g.decide('push','refs/heads/main',after,payload,dst,runner)
   print('dirs',dirs,'mode',result,'failed_command',trace)
   return result,trace
 def test_original_sparse_checkout_holds_at_first_test_blob(self):
  mode,trace=self.run_case(['scripts']);self.assertEqual(mode,'hold');self.assertEqual(trace[0][0],'show');self.assertTrue(trace[0][1].endswith(':tests/test_import_deenhindi.py'))
 def test_materialize_pinned_tests_passes_without_lazy_fetch(self):self.assertEqual(self.run_case(['scripts','tests'])[0],'offline_maintenance')
 def test_dirty_pinned_test_still_holds(self):self.assertEqual(self.run_case(['scripts','tests'],True)[0],'hold')
if __name__=='__main__':unittest.main(verbosity=2)
