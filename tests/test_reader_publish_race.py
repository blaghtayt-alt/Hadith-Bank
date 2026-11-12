"""Exercise the publication workflow against real concurrent Git updates."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def workflow_shell(step='Keep generated bank files synchronized'):
    """Read the actual workflow step without adding a YAML runtime dependency."""
    lines = (ROOT / '.github/workflows/reader-pages.yml').read_text().splitlines()
    start = lines.index('      - name: ' + step)
    start = lines.index('        run: |', start) + 1
    body = []
    for line in lines[start:]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:])
    return '\n'.join(body)


class ReaderPublishRaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.bare = self.folder / 'origin.git'
        self.work = self.folder / 'work'
        self.writer = self.folder / 'writer'
        self.work.mkdir()
        self.git(self.folder, 'init', '--bare', '--initial-branch=main', str(self.bare))
        self.git(self.work, 'init', '--initial-branch=main')
        self.identity(self.work)
        paths = [
            'catalog/index.json', 'search/index.json', 'browse/index.md',
            'index.json', 'hadith-bank-reader.html', 'sources/counterparts/index.json',
            'reports/counterpart-coverage.json', 'reports/counterpart-availability.json',
            'reports/counterpart-availability.md', 'reports/counterpart-review/index.json',
            'reports/reading-views-validation.json', 'reports/portable-validation.json',
            'reports/site-build.json',
        ]
        for name in paths:
            path = self.work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('original\n')
        (self.work / 'scripts').mkdir()
        shutil.copyfile(ROOT / 'scripts/push_reader_commit.py', self.work / 'scripts/push_reader_commit.py')
        self.git(self.work, 'add', '.')
        self.git(self.work, 'commit', '-m', 'Original bank')
        self.base = self.git(self.work, 'rev-parse', 'HEAD').strip()
        self.git(self.work, 'remote', 'add', 'origin', str(self.bare))
        self.git(self.work, 'push', 'origin', 'main')
        self.git(self.folder, 'clone', str(self.bare), str(self.writer))
        self.identity(self.writer)
        self.bin = self.folder / 'bin'
        self.bin.mkdir()
        gh = self.bin / 'gh'
        gh.write_text('#!/bin/sh\nif [ "$1" = api ]; then\n'
                      '  printf "%s\\n" "$MAIN_REF"\n  exit 0\nfi\n'
                      'printf "%s\\n" "$*" >> "$GH_CALLS"\nexit "${DISPATCH_EXIT:-0}"\n')
        gh.chmod(0o755)
        self.output = self.folder / 'github-output'
        self.calls = self.folder / 'dispatch-calls'
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'GITHUB_SHA': self.base, 'GITHUB_OUTPUT': str(self.output),
                    'GITHUB_REPOSITORY': 'local-test/hadith-bank',
                    'GH_CALLS': str(self.calls), 'GH_TOKEN': 'local-test-placeholder'}
        (self.work / 'index.json').write_text('generated\n')

    @staticmethod
    def git(cwd, *args):
        return subprocess.run(['git', *args], cwd=cwd, text=True, capture_output=True,
                              check=True).stdout

    def identity(self, folder):
        self.git(folder, 'config', 'user.name', 'Local test')
        self.git(folder, 'config', 'user.email', 'local-test@example.invalid')

    def next_source_commit(self):
        (self.writer / 'new-source.txt').write_text('Exact concurrent source bytes\n')
        self.git(self.writer, 'add', 'new-source.txt')
        self.git(self.writer, 'commit', '-m', 'Concurrent source import')
        commit = self.git(self.writer, 'rev-parse', 'HEAD').strip()
        # Make the object available in the bare repository without moving main.
        self.git(self.writer, 'push', 'origin', 'HEAD:refs/heads/concurrent-fixture')
        return commit

    def run_sync(self):
        result = subprocess.run(['bash', '-c', workflow_shell()], cwd=self.work,
                                env=self.env, text=True, capture_output=True)
        outputs = dict(line.split('=', 1) for line in self.output.read_text().splitlines()) if self.output.exists() else {}
        calls = self.calls.read_text().splitlines() if self.calls.exists() else []
        remote = self.git(self.folder, '--git-dir=' + str(self.bare), 'rev-parse', 'refs/heads/main').strip()
        return result, outputs, calls, remote

    def test_success_publishes_only_its_generated_commit(self):
        result, outputs, calls, remote = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(outputs, {'published_commit': remote, 'publish': 'true'})
        self.assertNotEqual(remote, self.base)
        self.assertEqual(calls, [])

    def test_already_stale_build_dispatches_current_main(self):
        concurrent = self.next_source_commit()
        self.git(self.writer, 'push', 'origin', 'HEAD:main')
        result, outputs, calls, remote = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(outputs, {'publish': 'false'})
        self.assertEqual(calls, ['workflow run reader-pages.yml --ref main --repo local-test/hadith-bank'])
        self.assertEqual(remote, concurrent)

    def test_source_push_between_check_and_push_is_preserved(self):
        concurrent = self.next_source_commit()
        hook = self.work / '.git/hooks/pre-push'
        hook.write_text('#!/bin/sh\nset -e\ngit --git-dir=' + shlex.quote(str(self.bare)) +
                        ' update-ref refs/heads/main ' + concurrent + ' ' + self.base + '\n')
        hook.chmod(0o755)
        result, outputs, calls, remote = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(outputs, {'publish': 'false'})
        self.assertEqual(calls, ['workflow run reader-pages.yml --ref main --repo local-test/hadith-bank'])
        self.assertEqual(remote, concurrent)
        saved_source = self.git(self.folder, '--git-dir=' + str(self.bare), 'show', 'main:new-source.txt')
        self.assertEqual(saved_source, 'Exact concurrent source bytes\n')
        self.assertEqual(self.git(self.folder, '--git-dir=' + str(self.bare), 'show', 'main:index.json'), 'original\n')

    def test_failed_push_without_a_new_source_remains_failure(self):
        hook = self.bare / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        result, outputs, calls, remote = self.run_sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(outputs.get('publish'), 'true')
        self.assertEqual(calls, [])
        self.assertEqual(remote, self.base)

    def test_lost_dispatch_is_not_reported_as_success(self):
        self.next_source_commit()
        self.git(self.writer, 'push', 'origin', 'HEAD:main')
        self.env['DISPATCH_EXIT'] = '47'
        result, outputs, calls, _ = self.run_sync()
        self.assertEqual(result.returncode, 47)
        self.assertEqual(outputs, {'publish': 'false'})
        self.assertEqual(len(calls), 1)

    def test_stale_deploy_requests_current_build_without_publishing(self):
        self.env.update({'EXPECTED_COMMIT': self.base, 'MAIN_REF': 'f' * 40})
        result = subprocess.run(['bash', '-c', workflow_shell('Check that this is still the current bank')],
                                cwd=self.work, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), 'publish=false\n')
        self.assertEqual(self.calls.read_text().strip(),
                         'workflow run reader-pages.yml --ref main --repo local-test/hadith-bank')

    def test_deploy_dispatch_failure_is_not_hidden(self):
        self.env.update({'EXPECTED_COMMIT': self.base, 'MAIN_REF': 'f' * 40, 'DISPATCH_EXIT': '47'})
        result = subprocess.run(['bash', '-c', workflow_shell('Check that this is still the current bank')],
                                cwd=self.work, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 47)
        self.assertEqual(self.output.read_text(), 'publish=false\n')

    def test_invalid_remote_revision_does_not_publish_or_dispatch(self):
        self.env.update({'EXPECTED_COMMIT': self.base, 'MAIN_REF': ''})
        result = subprocess.run(['bash', '-c', workflow_shell('Check that this is still the current bank')],
                                cwd=self.work, env=self.env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.calls.exists())


if __name__ == '__main__':
    unittest.main()
