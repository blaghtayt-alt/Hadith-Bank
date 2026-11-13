"""Exercise recovery workflow ordering and continuation without source traffic.

Transaction/archive validation lives in test_recover_deenhindi_artifact.py.
These tests run the workflow's actual shell against strict offline CLI doubles,
real local Git remotes and the production logged-task wrapper. They also use
the real recovery entry point and web continuation code for before-status
receipt integration. No GitHub endpoint or publisher endpoint is contacted.
"""
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/import-web-hadith.yml'
sys.path.insert(0, str(ROOT / 'scripts'))
import recover_deenhindi_artifact as recovery
import web_import_batch as batch


def step_lines(name):
    lines = WORKFLOW.read_text().splitlines()
    first = lines.index('      - name: ' + name)
    last = next((i for i in range(first + 1, len(lines))
                 if lines[i].startswith('      - name: ')), len(lines))
    return lines[first:last]


def step_run(name):
    lines = step_lines(name)
    start = next(i for i,line in enumerate(lines) if line in ('        run: |', '        run: >-'))
    folded = lines[start] == '        run: >-'
    body = []
    for line in lines[start + 1:]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:])
    return (' ' if folded else '\n').join(body)


def selected(name, checkpoint_required):
    expression = next(line.strip()[4:] for line in step_lines(name) if line.startswith('        if: '))
    match = re.fullmatch(r"steps\.recovery\.outputs\.checkpoint_required (==|!=) 'true'", expression)
    if not match:
        raise AssertionError('Review the changed Actions condition: ' + expression)
    equal = checkpoint_required == 'true'
    return equal if match.group(1) == '==' else not equal


class RecoveryContinuationReceiptTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root/'AGENTS.md').write_text('TEST repository\n')
        self.plan = {'schema':'hadith-bank-web-import-plan-v1','enabled':True,
            'sources': {name: {'enabled':name=='deenhindi','continue_after_success':True,
                'max_requests_per_batch':1,'max_seconds_per_batch':10,'delay_seconds':1}
                for name in batch.PROGRESS}}
        batch.write_changed(self.root/'catalog/web-import-plan.json', self.plan)
        (self.root/recovery.PLAN_PATH).write_bytes((ROOT/recovery.PLAN_PATH).read_bytes())
        self.progress(10)
        self.output = self.root/'github-output.txt'

    def progress(self, count, blocked=False):
        batch.write_changed(self.root/batch.PROGRESS['deenhindi'], {
            'imported_count':count,'registered_hadith_count':count,'classification_pending_count':0,
            'pending_fetch_count':5,'done':False,'blocked':blocked,'errors_count':0,
            'by_collection':{str(i):{'inventory':10} for i in range(7)}})

    def recover_with_receipt(self, prior=None, blocked=False):
        def restore(root, expected, archive, provider, before_status):
            baseline = before_status if prior is None else prior
            self.progress(11,blocked)
            return {'checkpoint_required':True,'new_entries_this_attempt':1,
                    'recovered_entries':1,'receipt':{'before_status':baseline}}
        with mock.patch.object(recovery,'restore',side_effect=restore), \
             mock.patch.object(recovery,'download_archive',side_effect=AssertionError('TEST no artifact network')), \
             mock.patch.dict(os.environ,{'GITHUB_OUTPUT':str(self.output)}), \
             mock.patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(recovery.main(['--root',str(self.root)]),0)

    def refresh(self):
        with mock.patch.object(batch,'run_source',side_effect=AssertionError('TEST no source HTTP')), \
             mock.patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(batch.main(['--root',str(self.root),'--reviews-only']),0)

    def test_recovery_before_status_survives_offline_validation_and_drives_continuation(self):
        prior = batch.summarize(self.root,self.plan)
        self.recover_with_receipt()
        path = self.root/batch.BEFORE_STATUS
        self.assertEqual(json.loads(path.read_bytes()),prior)
        frozen = path.read_bytes()
        self.refresh()
        self.assertEqual(path.read_bytes(),frozen)
        request = batch.continuation_request(self.root)
        self.assertTrue(request['continue'])
        self.assertEqual(request['sources'][0]['before_fetched'],10)
        self.assertEqual(request['sources'][0]['after_fetched'],11)
        self.assertEqual(self.output.read_text(),'checkpoint_required=true\n')

    def test_replayed_recovery_uses_durable_original_before_status_and_preserves_block(self):
        original = batch.summarize(self.root,self.plan)
        self.progress(11,True)
        self.recover_with_receipt(prior=original,blocked=True)
        self.assertEqual(json.loads((self.root/batch.BEFORE_STATUS).read_bytes()),original)
        self.refresh()
        self.assertFalse(batch.continuation_request(self.root)['continue'])
        self.assertTrue(batch.source_status(self.root,'deenhindi')['blocked'])


CLI_SUPPORT = r'''
import json, os
from pathlib import Path
root = Path('.').resolve()
def read(path, default=None):
    p = root/path
    return json.loads(p.read_text()) if p.exists() else default
def write(path, value):
    p = root/path; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,sort_keys=True)+'\n')
def log(mode):
    with open(os.environ['TEST_WORKFLOW_CALLS'],'a') as out: out.write(mode+'\n')
'''

OFFLINE_RECOVERY = CLI_SUPPORT + r'''
import argparse, shutil
parser=argparse.ArgumentParser()
parser.add_argument('--root',required=True)
mode=parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--offline-rebuild',action='store_true')
mode.add_argument('--report',action='store_true')
args=parser.parse_args()
assert args.root=='.'
if args.offline_rebuild:
    log('offline-rebuild')
    control=read('catalog/test-current-review.json',{'held':['TEST-held']})
    write('imports/web-deenhindi-20261112/staged/test-held.json',control['held'])
    write('.work/test-offline-proof.json',{'held':control['held']})
else:
    log('report')
    status=read('.work/web-import-batch/status.json')
    assert status['validation_state']=='passed'
    held=read('imports/web-deenhindi-20261112/staged/test-held.json')
    assert read('.work/test-offline-proof.json')['held']==held
    folder=root/'.work/deenhindi-artifact-recovery/held'
    if folder.exists(): shutil.rmtree(folder)
    write('.work/deenhindi-artifact-recovery/held/summary.json',{'held_keys':held})
    write('imports/web-deenhindi-20261112/recoveries/TEST/receipt.json',
          {'status':'derivatives_validated','held_keys':held})
'''

OFFLINE_BATCH = CLI_SUPPORT + r'''
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--root',required=True)
mode=parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--reviews-only',action='store_true')
mode.add_argument('--status-only',action='store_true')
args=parser.parse_args()
assert args.root=='.'
log('reviews-only' if args.reviews_only else 'status-only')
if (root/'invalid-review-refresh').exists():
    raise SystemExit('TEST failed current review validation')
control=read('catalog/test-current-review.json',{'held':['TEST-held']})
write('imports/web-deenhindi-20261112/staged/test-held.json',control['held'])
write('.work/web-import-batch/status.json',{'validation_state':'passed'})
write('imports/web-import-status.json',{'validation_state':'passed'})
'''


class WebRecoveryWorkflowExecutionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.work = self.base/'work'
        self.work.mkdir()
        (self.work/'scripts').mkdir()
        shutil.copyfile(ROOT/'scripts/run_logged_task.py',self.work/'scripts/run_logged_task.py')
        (self.work/'scripts/recover_deenhindi_artifact.py').write_text(textwrap.dedent(OFFLINE_RECOVERY))
        (self.work/'scripts/web_import_batch.py').write_text(textwrap.dedent(OFFLINE_BATCH))
        # Any legacy direct importer invocation or ordinary batch mode must fail
        # this integration test instead of contacting an external source.
        (self.work/'scripts/import_deenhindi.py').write_text(
            "raise SystemExit('TEST direct source importer is forbidden in the recovery hook')\n")
        self.log = self.base/'workflow-calls.txt'
        self.env = {**os.environ,'TEST_WORKFLOW_CALLS':str(self.log),'RECOVERY_CHECKPOINT':'true'}
        self.write('catalog/test-current-review.json',{'held':['TEST-held']})
        self.write('.work/web-import-batch/before-status.json',{'source_status':[{'source':'deenhindi','fetched_entries':10}]})
        self.before = (self.work/batch.BEFORE_STATUS).read_bytes()

    def write(self,path,value):
        target=self.work/path; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(value,sort_keys=True)+'\n')

    def read(self,path):
        return json.loads((self.work/path).read_text())

    def run_step(self,name):
        return subprocess.run(['bash','-c',step_run(name)],cwd=self.work,env=self.env,
                              text=True,capture_output=True)

    @staticmethod
    def git(root,*args):
        return subprocess.run(['git',*args],cwd=root,text=True,capture_output=True,check=True).stdout

    def make_remote(self):
        self.remote=self.base/'origin.git'; self.writer=self.base/'writer'
        self.git(self.base,'init','--bare','--initial-branch=main',str(self.remote))
        self.git(self.work,'init','--initial-branch=main')
        self.git(self.work,'config','user.name','TEST recovery')
        self.git(self.work,'config','user.email','recovery@example.invalid')
        (self.work/'.gitignore').write_text('.work/\n')
        self.git(self.work,'add','.')
        self.git(self.work,'commit','-m','TEST initial workflow fixture')
        self.git(self.work,'remote','add','origin',str(self.remote))
        self.git(self.work,'push','-u','origin','main')
        self.git(self.base,'clone',str(self.remote),str(self.writer))
        self.git(self.writer,'config','user.name','TEST concurrent reviewer')
        self.git(self.writer,'config','user.email','reviewer@example.invalid')

    def recovered_sources(self):
        state={'schema':'TEST-source-state','blocked':{'reason':'TEST preserved block'},
               'errors':{'TEST historical':{'attempts':[1,2]}},'imported':{'TEST':{'source':'exact'}}}
        self.write('imports/web-deenhindi-20261112/state.json',state)
        for path,body in [
            ('imports/web-deenhindi-20261112/raw/TEST.html.gz',b'TEST exact raw bytes'),
            ('imports/web-deenhindi-20261112/parsed/bukhari/TEST.json.gz',b'TEST exact parsed bytes'),
            ('imports/web-deenhindi-20261112/recoveries/TEST/verified-index.json.gz',b'TEST exact archive index')]:
            target=self.work/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        self.write('imports/web-deenhindi-20261112/recoveries/TEST/receipt.json',{'status':'sources_restored'})
        return (self.work/'imports/web-deenhindi-20261112/state.json').read_bytes()

    def concurrent_review(self,invalid=False):
        if invalid:
            (self.writer/'invalid-review-refresh').write_text('TEST invalid review\n')
        else:
            (self.writer/'catalog/test-current-review.json').write_text('{"held":[]}\n')
        self.git(self.writer,'add','.')
        self.git(self.writer,'commit','-m','TEST newer review')
        self.git(self.writer,'push','origin','main')
        return self.git(self.writer,'rev-parse','HEAD').strip()

    def test_recovery_branch_runs_only_offline_modes_and_retains_before_status(self):
        name='Rebuild the recovered checkpoint without new source requests'
        ordinary='Resume bounded public-page batches'
        self.assertTrue(selected(name,'true'))
        self.assertFalse(selected(ordinary,'true'))
        self.assertFalse(selected(name,'false'))
        self.assertTrue(selected(ordinary,'false'))
        self.recovered_sources()
        result=self.run_step(name)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),['offline-rebuild','reviews-only','report'])
        self.assertEqual((self.work/batch.BEFORE_STATUS).read_bytes(),self.before)
        self.assertEqual(self.read('.work/deenhindi-artifact-recovery/held/summary.json')['held_keys'],['TEST-held'])
        for path in ('rebuild','validation','report'):
            status=self.read('.work/deenhindi-artifact-recovery-'+path+'/status.json')
            self.assertEqual(status['status'],'succeeded')

    def test_recovery_validation_failure_stops_before_report(self):
        (self.work/'invalid-review-refresh').write_text('TEST failure\n')
        result=self.run_step('Rebuild the recovered checkpoint without new source requests')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.log.read_text().splitlines(),['offline-rebuild','reviews-only'])
        self.assertFalse((self.work/'.work/deenhindi-artifact-recovery/held').exists())
        self.assertEqual((self.work/batch.BEFORE_STATUS).read_bytes(),self.before)

    def test_rebased_review_refreshes_small_artifact_and_stages_exact_sources_and_receipt(self):
        self.make_remote()
        newer=self.concurrent_review()
        state=self.recovered_sources()
        self.write('.work/deenhindi-artifact-recovery/held/stale-object.json',{'stale':True})
        result=self.run_step('Save validated source snapshots and queue checkpoints')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),['offline-rebuild','reviews-only','status-only','report'])
        receipt=json.loads(self.git(self.remote,'show','main:imports/web-deenhindi-20261112/recoveries/TEST/receipt.json'))
        self.assertEqual(receipt,{'status':'derivatives_validated','held_keys':[]})
        self.assertEqual(self.read('.work/deenhindi-artifact-recovery/held/summary.json'),{'held_keys':[]})
        self.assertFalse((self.work/'.work/deenhindi-artifact-recovery/held/stale-object.json').exists())
        for path in ('imports/web-deenhindi-20261112/raw/TEST.html.gz',
                     'imports/web-deenhindi-20261112/parsed/bukhari/TEST.json.gz',
                     'imports/web-deenhindi-20261112/recoveries/TEST/verified-index.json.gz'):
            self.assertEqual(self.git(self.remote,'show','main:'+path).encode(),(self.work/path).read_bytes())
        self.assertEqual(self.git(self.remote,'show','main:imports/web-deenhindi-20261112/state.json').encode(),state)
        self.assertEqual((self.work/batch.BEFORE_STATUS).read_bytes(),self.before)
        self.git(self.remote,'merge-base','--is-ancestor',newer,'main')

    def test_rebase_validation_failure_does_not_publish_recovered_checkpoint(self):
        self.make_remote()
        newer=self.concurrent_review(invalid=True)
        state=self.recovered_sources()
        result=self.run_step('Save validated source snapshots and queue checkpoints')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.git(self.remote,'rev-parse','main').strip(),newer)
        self.assertEqual((self.work/'imports/web-deenhindi-20261112/state.json').read_bytes(),state)
        self.assertEqual(self.log.read_text().splitlines(),['offline-rebuild','reviews-only'])

    def test_ordinary_save_does_not_require_or_replay_recovery(self):
        self.make_remote()
        self.recovered_sources()
        self.env['RECOVERY_CHECKPOINT']='false'
        result=self.run_step('Save validated source snapshots and queue checkpoints')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),['reviews-only','status-only'])
        self.assertFalse((self.work/'.work/deenhindi-artifact-recovery/held').exists())


if __name__=='__main__':
    unittest.main()
