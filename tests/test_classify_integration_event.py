"""Offline gate routing, complete-diff parsing and real local Git regression tests."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import classify_integration_event as gate

A = gate.EXPECTED_BEFORE
B = 'b' * 40
class ClassifierTests(unittest.TestCase):
    def classify(self, **changes):
        args = dict(event='push', ref='refs/heads/main', before=A, after=B,
                    changes=dict(gate.EXPECTED_CHANGES), diff_complete=True, pins_match=True)
        args.update(changes)
        return gate.classify(**args)
    def test_reviewed_exact(self):self.assertEqual(self.classify(), 'offline_maintenance')
    def test_maintenance_base_drift_holds(self):self.assertEqual(self.classify(before='c'*40), 'hold')
    def test_incomplete_set_holds(self):
        changes=dict(gate.EXPECTED_CHANGES);changes.pop('tests/test_import_deenhindi.py')
        self.assertEqual(self.classify(changes=changes), 'hold')
    def test_mixed_source_holds_maintenance(self):
        changes=dict(gate.EXPECTED_CHANGES);changes['imports/source/state.json']='M'
        self.assertEqual(self.classify(changes=changes), 'hold')
    def test_wrong_status_holds(self):
        changes=dict(gate.EXPECTED_CHANGES);changes['scripts/import_deenhindi.py']='D'
        self.assertEqual(self.classify(changes=changes),'hold')
    def test_pins_fail_closed(self):
        for value in [False,None,0,1,'true']:self.assertEqual(self.classify(pins_match=value),'hold')
    def test_complete_requires_literal_true(self):
        for value in [False,None,0,1,'false',[],{}]:self.assertEqual(self.classify(diff_complete=value),'hold')
    def test_other_ordinary_push_preserved(self):
        for changes in [{'catalog/materials.json':'M'},{'scripts/import_deenhindi.py':'M'}]:self.assertEqual(self.classify(changes=changes),'existing_main_flow')
    def test_schedule_dispatch_preserved(self):
        for event in ['schedule','workflow_dispatch']:self.assertEqual(self.classify(event=event),'existing_main_flow')
    def test_pr_validate_only(self):self.assertEqual(self.classify(event='pull_request',ref='refs/pull/31/merge'),'validate_only')
    def test_unknown_event_or_ref_holds(self):
        self.assertEqual(self.classify(event='workflow_run'),'hold');self.assertEqual(self.classify(ref='refs/heads/other'),'hold')
    def test_bad_shas_hold(self):
        for value in ['0'*40,'x'*40,'a'*39,None,'a'*40+';echo BAD']:self.assertEqual(self.classify(before=value),'hold')
        self.assertEqual(self.classify(after=A),'hold')


class RepairRouteTests(unittest.TestCase):
    def classify(self, **changes):
        args=dict(event='push',ref='refs/heads/main',before=gate.REPAIR_BEFORE,after=B,changes=dict(gate.REPAIR_CHANGES),diff_complete=True,pins_match=True)
        args.update(changes);return gate.classify(**args)
    def test_exact_repair(self):self.assertEqual(self.classify(),'offline_maintenance')
    def test_repair_base_drift_holds(self):self.assertEqual(self.classify(before='d'*40),'hold')
    def test_repair_extra_path_holds(self):
        c=dict(gate.REPAIR_CHANGES);c['imports/stop.json']='M';self.assertEqual(self.classify(changes=c),'hold')
    def test_repair_missing_path_holds(self):
        c=dict(gate.REPAIR_CHANGES);c.pop('.github/workflows/reader-pages.yml');self.assertEqual(self.classify(changes=c),'hold')
    def test_repair_wrong_status_holds(self):
        c=dict(gate.REPAIR_CHANGES);c['tests/test_integration_gate_sparse_checkout.py']='M';self.assertEqual(self.classify(changes=c),'hold')
    def test_repair_bad_pin_holds(self):self.assertEqual(self.classify(pins_match=False),'hold')
    def test_unreviewed_helper_change_holds(self):self.assertEqual(self.classify(changes={'scripts/classify_integration_event.py':'M'}),'hold')

class RepairAdapterTests(unittest.TestCase):
    def test_actual_partial_clone_repair_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source';src.mkdir();dst=root/'checkout'
            env=dict(os.environ,GIT_ALLOW_PROTOCOL='file',GIT_TERMINAL_PROMPT='0')
            def git(where,*args):return subprocess.check_output(['git','-C',str(where),*args],env=env,stderr=subprocess.PIPE)
            git(src,'init','-q');git(src,'config','user.name','TEST');git(src,'config','user.email','test@example.invalid');git(src,'config','uploadpack.allowFilter','true')
            for name in set(gate.REPAIR_CHANGES)|set(gate.REVIEWED_HASHES):
                if gate.REPAIR_CHANGES.get(name)!='A':
                    p=src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('OLD '+name)
            git(src,'add','.');git(src,'commit','-qm','before');before=git(src,'rev-parse','HEAD').decode().strip()
            for name in gate.REPAIR_CHANGES:
                p=src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('NEW '+name)
            git(src,'add','.');git(src,'commit','-qm','after');after=git(src,'rev-parse','HEAD').decode().strip()
            pins={p:hashlib.sha256((src/p).read_bytes()).hexdigest() for p in gate.REPAIR_HASHES}
            prior={p:hashlib.sha256((src/p).read_bytes()).hexdigest() for p in gate.REVIEWED_HASHES}
            subprocess.check_output(['git','clone','--no-checkout','--filter=blob:none',src.as_uri(),str(dst)],env=env,stderr=subprocess.PIPE)
            git(dst,'sparse-checkout','set','scripts','tests','.github/workflows');git(dst,'checkout','--detach',after);git(dst,'remote','set-url','origin',str(root/'offline-missing'))
            payload=dict(before=before,after=after,ref='refs/heads/main',forced=False,deleted=False,created=False)
            with patch.object(gate,'REPAIR_BEFORE',before),patch.object(gate,'REPAIR_HASHES',pins),patch.object(gate,'REVIEWED_HASHES',prior),patch.dict(os.environ,env):
                self.assertEqual(gate.decide('push','refs/heads/main',after,payload,dst),'offline_maintenance')
                with patch.object(gate,'REPAIR_HASHES',{**pins,'.github/workflows/reader-pages.yml':'0'*64}):
                    self.assertEqual(gate.decide('push','refs/heads/main',after,payload,dst),'hold')

class DiffParsingTests(unittest.TestCase):
    def test_exact_nul_parse(self):self.assertEqual(gate.parse_diff(b'M\0scripts/test.py\0A\0tests/a.py\0'),{'scripts/test.py':'M','tests/a.py':'A'})
    def test_no_truncation_or_ambiguous_status(self):
        for raw in [b'',b'M\0x',b'M\0',b'M\0x\0A\0',b'R100\0x\0y\0',b'T\0x\0',b'M\0x\0M\0x\0',b'\xff\0x\0',b'M\0\xff\0']:
            with self.assertRaises((ValueError,UnicodeError)):gate.parse_diff(raw)
    def test_bad_paths(self):
        for p in [b'',b'/root',b'a/../b',b'./x',b'a//b',b'a\\b',b'x\n',b'x\t',b'x\x7f']:
            with self.assertRaises(ValueError):gate.parse_diff(b'M\0'+p+b'\0')
    def test_size_cap(self):
        with patch.object(gate,'MAX_DIFF_BYTES',4):
            with self.assertRaises(ValueError):gate.parse_diff(b'M\0x\0A\0y\0')

class ActualGitAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.git('init','-q');self.git('config','user.name','TEST');self.git('config','user.email','test@example.invalid')
        for path,status in gate.EXPECTED_CHANGES.items():
            if status=='M':self.write(path,b'OLD TEST\n')
        self.git('add','.');self.git('commit','-qm','before TEST');self.before=self.git('rev-parse','HEAD').decode().strip()
        for path in gate.EXPECTED_CHANGES:self.write(path,b'NEW TEST\n')
        self.git('add','.');self.git('commit','-qm','after TEST');self.after=self.git('rev-parse','HEAD').decode().strip()
        self.payload={'before':self.before,'after':self.after,'ref':'refs/heads/main','forced':False,'deleted':False,'created':False}
        self.base=patch.object(gate,'EXPECTED_BEFORE',self.before);self.base.start();self.addCleanup(self.base.stop)
        self.pins=patch.object(gate,'REVIEWED_HASHES',{p:hashlib.sha256(b'NEW TEST\n').hexdigest() for p in gate.REVIEWED_HASHES});self.pins.start();self.addCleanup(self.pins.stop)
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.DEVNULL)
    def write(self,name,raw):p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    def decide(self,payload=None,sha=None,runner=gate.git):return gate.decide('push','refs/heads/main',sha or self.after,self.payload if payload is None else payload,self.root,runner)
    def test_actual_git_full_diff_and_pins(self):self.assertEqual(self.decide(),'offline_maintenance')
    def test_force_delete_create_or_missing_rejected_before_git(self):
        def forbidden(*args):self.fail('Git should not run for invalid event')
        for key in ['forced','deleted','created']:
            for value in [True,None,0,'false']:
                payload=dict(self.payload);payload[key]=value;self.assertEqual(self.decide(payload,runner=forbidden),'hold')
    def test_event_sha_mismatch(self):self.assertEqual(self.decide(sha='e'*40),'hold')
    def test_event_ref_mismatch(self):
        payload=dict(self.payload);payload['ref']='refs/heads/else';self.assertEqual(self.decide(payload),'hold')
    def test_head_mismatch(self):self.git('checkout','--detach',self.before);self.assertEqual(self.decide(),'hold')
    def test_dirty_worktree_holds(self):self.write('scripts/import_deenhindi.py',b'DIRTY');self.assertEqual(self.decide(),'hold')
    def test_wrong_content_pin_holds(self):
        with patch.object(gate,'REVIEWED_HASHES',{'scripts/import_deenhindi.py':'0'*64}):self.assertEqual(self.decide(),'hold')
    def test_missing_commit_holds(self):
        payload=dict(self.payload);payload['before']='e'*40;self.assertEqual(self.decide(payload),'hold')
    def test_diverged_history_holds(self):
        self.git('checkout','--orphan','unrelated');self.git('commit','--allow-empty','-qm','unrelated TEST');other=self.git('rev-parse','HEAD').decode().strip();self.git('checkout','--detach',self.after)
        payload=dict(self.payload);payload['before']=other;self.assertEqual(self.decide(payload),'hold')
    def test_git_failure_or_timeout_holds(self):
        for error in [OSError('TEST'),subprocess.TimeoutExpired('git',60),ValueError('TEST')]:
            with patch.object(gate,'git',side_effect=error):self.assertEqual(self.decide(runner=gate.git),'hold')
    def test_truncated_or_malformed_diff_holds(self):
        for raw in [b'M\0file',b'M\0',b'R100\0x\0y\0',b'']:
            def runner(root,*args):return raw if '--name-status' in args else gate.git(root,*args)
            self.assertEqual(self.decide(runner=runner),'hold')
    def test_local_git_has_no_remote(self):self.assertEqual(self.git('remote'),b'')
    def test_main_outputs_only_bounded_mode(self):
        event=self.root/'event.json';event.write_text(json.dumps(self.payload));output=self.root/'output.txt'
        env={'GITHUB_EVENT_NAME':'push','GITHUB_REF':'refs/heads/main','GITHUB_SHA':self.after,'GITHUB_EVENT_PATH':str(event),'GITHUB_WORKSPACE':str(self.root),'GITHUB_OUTPUT':str(output)}
        with patch.dict(os.environ,env):self.assertEqual(gate.main(),0)
        self.assertEqual(output.read_text(),'mode=offline_maintenance\n')
    def test_malformed_event_outputs_hold(self):
        event=self.root/'event.json';event.write_text('{');output=self.root/'output.txt'
        with patch.dict(os.environ,{'GITHUB_EVENT_NAME':'push','GITHUB_EVENT_PATH':str(event),'GITHUB_OUTPUT':str(output)}):self.assertEqual(gate.main(),1)
        self.assertEqual(output.read_text(),'mode=hold\n')

if __name__=='__main__':unittest.main(verbosity=2)
