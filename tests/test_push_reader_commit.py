"""Exercise publication races against real local Git repositories."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import push_reader_commit as publisher


class PushReaderCommitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.remote = self.folder / 'remote.git'
        self.builder = self.folder / 'builder'
        self.writer = self.folder / 'writer'
        self.git(self.folder, 'init', '--bare', '--initial-branch=main', str(self.remote))
        self.git(self.folder, 'clone', str(self.remote), str(self.builder))
        self.commit(self.builder, 'source.txt', 'TEST original source\n', 'Source checkpoint')
        self.git(self.builder, 'push', 'origin', 'HEAD:refs/heads/main')
        self.start = self.git(self.builder, 'rev-parse', 'HEAD')
        self.git(self.folder, 'clone', str(self.remote), str(self.writer))
        self.generated = self.commit(self.builder, 'reader.html', 'TEST built reader\n', 'Generated reader')

    def git(self, root, *args):
        result = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, root, path, text, message):
        (root / path).write_text(text, encoding='utf-8')
        self.git(root, 'add', '--', path)
        self.git(root, '-c', 'user.name=TEST', '-c', 'user.email=test@example.invalid',
                 'commit', '-m', message)
        return self.git(root, 'rev-parse', 'HEAD')

    def advance_source(self, after_generated=False):
        if after_generated:
            self.git(self.writer, 'fetch', 'origin', 'main')
            self.git(self.writer, 'reset', '--hard', 'origin/main')
        head = self.commit(self.writer, 'source.txt', 'TEST newer source\n', 'Concurrent source update')
        self.git(self.writer, 'push', 'origin', 'HEAD:refs/heads/main')
        return head

    def remote_ref(self):
        return self.git(self.remote, 'rev-parse', 'refs/heads/main')

    def test_success_pushes_generated_commit_and_returns_exact_revision(self):
        result = publisher.synchronize(self.builder, self.start)
        self.assertTrue(result['publish'])
        self.assertEqual(result['status'], 'pushed')
        self.assertEqual(result['generated_commit'], self.generated)
        self.assertEqual(self.remote_ref(), self.generated)

    def test_no_generated_changes_needs_no_push(self):
        self.git(self.builder, 'reset', '--hard', self.start)
        original = publisher.run_git
        with mock.patch.object(publisher, 'run_git', wraps=original) as invoked:
            result = publisher.synchronize(self.builder, self.start)
        self.assertTrue(result['publish'])
        self.assertEqual(result['status'], 'current')
        self.assertFalse(any(call.args[1] == 'push' for call in invoked.call_args_list))

    def test_already_advanced_remote_skips_without_pushing(self):
        newer = self.advance_source()
        with mock.patch.object(publisher, 'run_git', wraps=publisher.run_git) as invoked:
            result = publisher.synchronize(self.builder, self.start)
        self.assertFalse(result['publish'])
        self.assertEqual(self.remote_ref(), newer)
        self.assertFalse(any(call.args[1] == 'push' for call in invoked.call_args_list))

    def test_source_push_between_check_and_push_is_clean_skip(self):
        original = publisher.run_git
        raced = []

        def race(root, *args):
            if args[0] == 'push':
                raced.append(self.advance_source())
            return original(root, *args)

        with mock.patch.object(publisher, 'run_git', side_effect=race):
            result = publisher.synchronize(self.builder, self.start)
        self.assertEqual(len(raced), 1)
        self.assertFalse(result['publish'])
        self.assertEqual(result['status'], 'superseded')
        self.assertEqual(self.remote_ref(), raced[0])
        self.assertEqual(self.git(self.remote, 'show', 'main:source.txt'), 'TEST newer source')

    def test_lost_push_acknowledgment_recognizes_saved_generated_commit(self):
        original = publisher.run_git

        def lose_ack(root, *args):
            result = original(root, *args)
            if args[0] == 'push':
                self.assertEqual(result.returncode, 0)
                return subprocess.CompletedProcess(result.args, 1, '', 'TEST lost acknowledgment')
            return result

        with mock.patch.object(publisher, 'run_git', side_effect=lose_ack):
            result = publisher.synchronize(self.builder, self.start)
        self.assertTrue(result['publish'])
        self.assertEqual(result['status'], 'push_acknowledgment_recovered')
        self.assertEqual(self.remote_ref(), self.generated)

    def test_new_source_after_successful_push_still_skips_stale_artifact(self):
        original = publisher.run_git
        advanced = []

        def race_after_push(root, *args):
            result = original(root, *args)
            if args[0] == 'push':
                self.assertEqual(result.returncode, 0)
                advanced.append(self.advance_source(after_generated=True))
            return result

        with mock.patch.object(publisher, 'run_git', side_effect=race_after_push):
            result = publisher.synchronize(self.builder, self.start)
        self.assertFalse(result['publish'])
        self.assertEqual(result['remote_commit'], advanced[0])
        self.assertEqual(self.remote_ref(), advanced[0])

    def test_real_push_rejection_stays_failure_and_withholds_outputs(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nprintf "TEST rejecting push\\n" >&2\nexit 1\n')
        hook.chmod(0o755)
        output = self.folder / 'outputs.txt'
        with contextlib.redirect_stderr(io.StringIO()):
            code = publisher.main(['--root', str(self.builder), '--expected-start', self.start,
                                   '--github-output', str(output)])
        self.assertEqual(code, 1)
        self.assertEqual(output.read_text(), 'publish=false\n')
        self.assertEqual(self.remote_ref(), self.start)

    def test_unavailable_remote_fails_without_claiming_publication(self):
        self.git(self.builder, 'remote', 'set-url', 'origin', str(self.folder / 'missing.git'))
        with self.assertRaisesRegex(publisher.SynchronizationError, 'Could not verify origin/main'):
            publisher.synchronize(self.builder, self.start)
        self.assertEqual(self.remote_ref(), self.start)

    def test_readback_failure_after_push_keeps_outcome_unconfirmed(self):
        original = publisher.run_git
        pushed = []

        def lose_readback(root, *args):
            if args[0] == 'ls-remote' and pushed:
                return subprocess.CompletedProcess(['git', *args], 128, '', 'TEST disconnected')
            result = original(root, *args)
            if args[0] == 'push':
                pushed.append(result.returncode)
            return result

        with mock.patch.object(publisher, 'run_git', side_effect=lose_readback):
            with self.assertRaisesRegex(publisher.SynchronizationError, 'Could not verify origin/main'):
                publisher.synchronize(self.builder, self.start)
        self.assertEqual(self.remote_ref(), self.generated)

    def test_output_only_marks_confirmed_commit_for_publication(self):
        output = self.folder / 'outputs.txt'
        with contextlib.redirect_stdout(io.StringIO()):
            code = publisher.main(['--root', str(self.builder), '--expected-start', self.start,
                                   '--github-output', str(output)])
        self.assertEqual(code, 0)
        self.assertEqual(output.read_text(), 'publish=true\npublished_commit=' + self.generated + '\n')


if __name__ == '__main__':
    unittest.main()
