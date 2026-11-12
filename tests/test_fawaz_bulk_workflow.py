"""Exercise source-batch publication against concurrent local Git writers."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def save_step():
    lines = (ROOT / '.github/workflows/import-fawaz-bulk.yml').read_text().splitlines()
    start = lines.index('      - name: Save the validated whole-book batch')
    start = lines.index('        run: |', start) + 1
    body = []
    for line in lines[start:]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:])
    return '\n'.join(body)


class FawazBulkWorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.remote = self.root / 'origin.git'
        self.work = self.root / 'work'
        self.writer = self.root / 'writer'
        self.git(self.root, 'init', '--bare', '--initial-branch=main', str(self.remote))
        self.git(self.root, 'clone', str(self.remote), str(self.work))
        self.identity(self.work)
        (self.work / 'scripts').mkdir()
        (self.work / 'scripts/material_registry.py').write_text(
            'import os\nfrom pathlib import Path\n'
            'def load_public_materials(root):\n'
            '    if (root / "invalid-registry").exists():\n'
            '        raise ValueError("TEST concurrent registry is invalid")\n'
            '    with open(os.environ["VALIDATION_LOG"], "a") as stream:\n'
            '        stream.write("validated\\n")\n'
            '    return {"manifests": []}\n')
        (self.work / 'README.md').write_text('TEST original bank\n')
        self.git(self.work, 'add', '.')
        self.git(self.work, 'commit', '-m', 'TEST initial bank')
        self.git(self.work, 'push', 'origin', 'main')
        self.start = self.git(self.work, 'rev-parse', 'HEAD').strip()
        self.git(self.root, 'clone', str(self.remote), str(self.writer))
        self.identity(self.writer)
        self.validations = self.root / 'validations.txt'
        self.env = {**os.environ, 'VALIDATION_LOG': str(self.validations)}
        self.source = self.work / 'imports/web-fawaz-20261112/source.txt'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('TEST complete exact source bytes\n')
        material = self.work / 'materials/fawaz-test/records.jsonl'
        material.parent.mkdir(parents=True)
        material.write_text('{"id":"TEST-record"}\n')

    @staticmethod
    def git(root, *args):
        return subprocess.run(['git', *args], cwd=root, capture_output=True,
                              text=True, check=True).stdout

    def identity(self, root):
        self.git(root, 'config', 'user.name', 'TEST batch writer')
        self.git(root, 'config', 'user.email', 'test@example.invalid')

    def source_commit(self, path='concurrent-source.txt', publish=True):
        (self.writer / path).write_text('TEST concurrent source bytes\n')
        self.git(self.writer, 'add', path)
        self.git(self.writer, 'commit', '-m', 'TEST concurrent source')
        head = self.git(self.writer, 'rev-parse', 'HEAD').strip()
        target = 'main' if publish else 'refs/heads/concurrent-fixture'
        self.git(self.writer, 'push', 'origin', 'HEAD:' + target)
        return head

    def run_save(self):
        return subprocess.run(['bash', '-c', save_step()], cwd=self.work,
                              env=self.env, capture_output=True, text=True)

    def remote_text(self, path):
        return self.git(self.remote, 'show', 'main:' + path)

    def test_whole_batch_preserves_concurrent_unrelated_source(self):
        self.source_commit()
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_text('concurrent-source.txt'), 'TEST concurrent source bytes\n')
        self.assertEqual(self.remote_text('imports/web-fawaz-20261112/source.txt'),
                         'TEST complete exact source bytes\n')
        self.assertEqual(self.remote_text('materials/fawaz-test/records.jsonl'), '{"id":"TEST-record"}\n')
        self.assertEqual(self.validations.read_text(), 'validated\n')

    def test_push_race_rebases_and_revalidates_without_overwriting_writer(self):
        concurrent = self.source_commit(publish=False)
        once = self.root / 'race-ran'
        hook = self.work / '.git/hooks/pre-push'
        hook.write_text('#!/bin/sh\nset -e\nif [ ! -e ' + shlex.quote(str(once)) + ' ]; then\n'
                        '  touch ' + shlex.quote(str(once)) + '\n'
                        '  git --git-dir=' + shlex.quote(str(self.remote)) +
                        ' update-ref refs/heads/main ' + concurrent + ' ' + self.start + '\nfi\n')
        hook.chmod(0o755)
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_text('concurrent-source.txt'), 'TEST concurrent source bytes\n')
        self.assertEqual(self.remote_text('imports/web-fawaz-20261112/source.txt'),
                         'TEST complete exact source bytes\n')
        self.assertEqual(self.validations.read_text(), 'validated\nvalidated\n')

    def test_unchanged_remote_rejection_is_a_failure(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), self.start)
        self.assertEqual(self.validations.read_text(), 'validated\n')

    def test_rebased_registry_failure_prevents_publication(self):
        concurrent = self.source_commit(path='invalid-registry')
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('TEST concurrent registry is invalid', result.stderr)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), concurrent)
        self.assertFalse(self.validations.exists())

    def test_lost_push_acknowledgment_recovers_confirmed_remote_commit(self):
        executable = shutil.which('git')
        wrapper = self.root / 'bin'
        wrapper.mkdir()
        path = wrapper / 'git'
        path.write_text('#!/bin/sh\n' + shlex.quote(executable) + ' "$@"\nstatus=$?\n'
                        'if [ "$1" = push ] && [ "$status" = 0 ]; then exit 47; fi\nexit "$status"\n')
        path.chmod(0o755)
        self.env['PATH'] = str(wrapper) + os.pathsep + self.env['PATH']
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_text('imports/web-fawaz-20261112/source.txt'),
                         'TEST complete exact source bytes\n')
        self.assertEqual(self.validations.read_text(), 'validated\n')

    def test_unchanged_checkpoint_does_not_create_or_push_another_commit(self):
        first = self.run_save()
        self.assertEqual(first.returncode, 0, first.stderr)
        saved = self.git(self.remote, 'rev-parse', 'main')
        second = self.run_save()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main'), saved)
        self.assertEqual(self.validations.read_text(), 'validated\n')


if __name__ == '__main__':
    unittest.main()
