"""Run the real batch-save step with concurrent Git sources and derived status."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STATUS = 'imports/web-import-status.json'
RAW = 'imports/web-deenhindi-20261112/raw.html'


def save_step():
    lines = (ROOT / '.github/workflows/import-web-hadith.yml').read_text().splitlines()
    start = lines.index('      - name: Save validated source snapshots and queue checkpoints')
    start = lines.index('        run: |', start) + 1
    body = []
    for line in lines[start:]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:])
    return '\n'.join(body)


class WebImportPublishTests(unittest.TestCase):
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
        self.write(self.work, 'scripts/web_import_batch.py',
            'import json\nfrom pathlib import Path\n'
            'root=Path(".")\n'
            'if (root/"invalid-registry").exists(): raise ValueError("TEST invalid registry")\n'
            'count=sum(len(p.read_text().splitlines()) for p in root.glob("materials/*/records.jsonl"))\n'
            '(root/"imports/web-import-status.json").write_text(json.dumps({"registered_occurrences":count},indent=2)+"\\n")\n')
        self.write(self.work, 'materials/islom-test/records.jsonl', '{"id":"TEST original"}\n')
        self.write(self.work, RAW, 'TEST original response bytes\n')
        self.write_status(self.work, 1)
        self.git(self.work, 'add', '.')
        self.git(self.work, 'commit', '-m', 'TEST original bank')
        self.git(self.work, 'push', 'origin', 'main')
        self.start = self.git(self.work, 'rev-parse', 'HEAD').strip()
        self.git(self.root, 'clone', str(self.remote), str(self.writer))
        self.identity(self.writer)
        self.write(self.work, 'materials/deenhindi-test/records.jsonl', '{"id":"TEST worker"}\n')
        self.write(self.work, RAW, 'TEST newly fetched exact response bytes\n')
        self.write_status(self.work, 2)

    @staticmethod
    def git(root, *args):
        return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, check=True).stdout

    def identity(self, root):
        self.git(root, 'config', 'user.name', 'TEST batch writer')
        self.git(root, 'config', 'user.email', 'test@example.invalid')

    def write(self, root, path, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)

    def write_status(self, root, count):
        self.write(root, STATUS, json.dumps({'registered_occurrences': count}, indent=2) + '\n')

    def concurrent_source(self, count=1, publish=True, raw_conflict=False, invalid=False):
        content = ''.join(json.dumps({'id': 'TEST concurrent ' + str(i)}) + '\n' for i in range(count))
        self.write(self.writer, 'materials/hadisuz-test/records.jsonl', content)
        self.write(self.writer, 'imports/web-hadisuz-20261112/raw.html', 'TEST other provider source bytes\n')
        self.write_status(self.writer, 1 + count)
        if raw_conflict:
            self.write(self.writer, RAW, 'TEST different concurrent source bytes\n')
        if invalid:
            self.write(self.writer, 'invalid-registry', 'TEST invalid\n')
        self.git(self.writer, 'add', '.')
        self.git(self.writer, 'commit', '-m', 'TEST concurrent provider')
        commit = self.git(self.writer, 'rev-parse', 'HEAD').strip()
        self.git(self.writer, 'push', 'origin', 'HEAD:' + ('main' if publish else 'refs/heads/concurrent-fixture'))
        return commit

    def run_save(self):
        return subprocess.run(['bash', '-c', save_step()], cwd=self.work,
                              env=os.environ.copy(), capture_output=True, text=True)

    def remote_text(self, path):
        return self.git(self.remote, 'show', 'main:' + path)

    def assert_integrated(self, count):
        self.assertEqual(json.loads(self.remote_text(STATUS))['registered_occurrences'], count)
        self.assertEqual(self.remote_text(RAW), 'TEST newly fetched exact response bytes\n')
        self.assertEqual(self.remote_text('imports/web-hadisuz-20261112/raw.html'),
                         'TEST other provider source bytes\n')
        self.assertEqual(self.remote_text('materials/deenhindi-test/records.jsonl'), '{"id":"TEST worker"}\n')

    def test_concurrent_source_addition_recomputes_status_inside_saved_batch(self):
        self.concurrent_source(count=1)
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_integrated(3)
        self.assertIn(STATUS, self.git(self.remote, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'main'))

    def test_only_derived_summary_conflict_is_resolved_from_integrated_sources(self):
        self.concurrent_source(count=2)
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_integrated(4)

    def test_confirmed_push_race_retries_rebase_and_regenerates_status(self):
        concurrent = self.concurrent_source(count=2, publish=False)
        once = self.root / 'race-ran'
        hook = self.work / '.git/hooks/pre-push'
        hook.write_text('#!/bin/sh\nset -e\nif [ ! -e ' + shlex.quote(str(once)) + ' ]; then\n'
            'touch ' + shlex.quote(str(once)) + '\n'
            'git --git-dir=' + shlex.quote(str(self.remote)) + ' update-ref refs/heads/main ' +
            concurrent + ' ' + self.start + '\nfi\n')
        hook.chmod(0o755)
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_integrated(4)

    def test_unchanged_remote_push_failure_does_not_claim_or_retry_publication(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), self.start)
        self.assertEqual(self.remote_text(RAW), 'TEST original response bytes\n')
        self.assertEqual(self.git(self.work, 'show', 'HEAD:' + RAW), 'TEST newly fetched exact response bytes\n')

    def test_real_source_conflict_is_not_automatically_resolved(self):
        concurrent = self.concurrent_source(count=2, raw_conflict=True)
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), concurrent)
        self.assertEqual(self.remote_text(RAW), 'TEST different concurrent source bytes\n')
        self.assertIn('not limited to the derived import summary', result.stderr)

    def test_registry_failure_after_rebase_prevents_source_push(self):
        concurrent = self.concurrent_source(invalid=True)
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('TEST invalid registry', result.stderr)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), concurrent)

    def test_excluded_rivoyat_material_is_not_staged(self):
        self.write(self.work, 'materials/rivoyat-test/records.jsonl', '{"id":"TEST excluded"}\n')
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(['git', 'cat-file', '-e', 'main:materials/rivoyat-test/records.jsonl'],
                                cwd=self.remote, capture_output=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
