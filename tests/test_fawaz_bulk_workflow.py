"""Exercise source-batch publication against concurrent local Git writers."""
import os
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def workflow_step(name):
    lines = (ROOT / '.github/workflows/import-fawaz-bulk.yml').read_text().splitlines()
    start = lines.index('      - name: ' + name)
    end = next((index for index in range(start + 1, len(lines))
                if lines[index].startswith('      - name: ')), len(lines))
    start = next(index for index in range(start, end)
                 if lines[index] in ('        run: |', '        run: >-'))
    folded = lines[start] == '        run: >-'
    body = []
    for line in lines[start + 1:end]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:])
    return (' ' if folded else '\n').join(body)


def save_step():
    return workflow_step('Save the validated whole-book batch')


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
        # Exercise the production logged-task wrapper and the workflow's exact
        # offline CLI contract without running unrelated website importers.
        shutil.copyfile(ROOT / 'scripts/run_logged_task.py',
                        self.work / 'scripts/run_logged_task.py')
        (self.work / 'scripts/web_import_batch.py').write_text(
            'import argparse, os\nfrom pathlib import Path\n'
            'parser = argparse.ArgumentParser()\n'
            'parser.add_argument("--root", required=True)\n'
            'parser.add_argument("--reviews-only", action="store_true", required=True)\n'
            'args = parser.parse_args()\n'
            'assert args.root == "."\n'
            'root = Path(args.root).resolve()\n'
            'with open(os.environ["REVIEW_REFRESH_LOG"], "a") as stream:\n'
            '    stream.write("attempted\\n")\n'
            'if (root / "invalid-review-refresh").exists():\n'
            '    raise SystemExit("TEST offline review refresh failed")\n'
            'review = root / "imports/web-deenhindi-20261112/reviews/reviewed-source.txt"\n'
            'if review.exists():\n'
            '    material = root / "materials/deenhindi-test/reviewed-source.txt"\n'
            '    material.parent.mkdir(parents=True, exist_ok=True)\n'
            '    material.write_bytes(review.read_bytes())\n')
        (self.work / 'scripts/material_registry.py').write_text(
            'import os\nfrom pathlib import Path\n'
            'def load_public_materials(root):\n'
            '    if (root / "invalid-registry").exists():\n'
            '        raise ValueError("TEST concurrent registry is invalid")\n'
            '    review = root / "imports/web-deenhindi-20261112/reviews/reviewed-source.txt"\n'
            '    if review.exists():\n'
            '        material = root / "materials/deenhindi-test/reviewed-source.txt"\n'
            '        if not material.exists() or material.read_bytes() != review.read_bytes():\n'
            '            raise ValueError("TEST current reviews were not refreshed before validation")\n'
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
        self.refreshes = self.root / 'review-refreshes.txt'
        self.env = {**os.environ, 'VALIDATION_LOG': str(self.validations),
                    'REVIEW_REFRESH_LOG': str(self.refreshes)}
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
        (self.writer / path).parent.mkdir(parents=True, exist_ok=True)
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
        self.assertEqual(self.refreshes.read_text(), 'attempted\n')

    def test_rebased_reviews_are_refreshed_offline_before_validation_and_published(self):
        review = 'imports/web-deenhindi-20261112/reviews/reviewed-source.txt'
        concurrent = self.source_commit(path=review)
        result = self.run_save()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_text(review), 'TEST concurrent source bytes\n')
        self.assertEqual(self.remote_text('materials/deenhindi-test/reviewed-source.txt'),
                         'TEST concurrent source bytes\n')
        self.assertEqual(self.remote_text('imports/web-fawaz-20261112/source.txt'),
                         'TEST complete exact source bytes\n')
        self.git(self.remote, 'merge-base', '--is-ancestor', concurrent, 'main')
        self.assertEqual(self.refreshes.read_text(), 'attempted\n')
        self.assertEqual(self.validations.read_text(), 'validated\n')
        status = json.loads((self.work / '.work/fawaz-website-reviews-rebase-1/status.json').read_text())
        self.assertEqual(status['status'], 'succeeded')
        self.assertEqual(status['exit_code'], 0)

    def test_rebased_review_refresh_failure_prevents_publication_and_retains_diagnostics(self):
        concurrent = self.source_commit(path='invalid-review-refresh')
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), concurrent)
        self.assertEqual(self.source.read_text(), 'TEST complete exact source bytes\n')
        self.assertEqual(self.refreshes.read_text(), 'attempted\n')
        self.assertFalse(self.validations.exists())
        job = self.work / '.work/fawaz-website-reviews-rebase-1'
        status = json.loads((job / 'status.json').read_text())
        self.assertEqual(status['status'], 'failed')
        self.assertNotEqual(status['exit_code'], 0)
        self.assertIn('TEST offline review refresh failed', (job / 'output.log').read_text())

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
        self.assertEqual(self.refreshes.read_text(), 'attempted\nattempted\n')

    def test_unchanged_remote_rejection_is_a_failure(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), self.start)
        self.assertEqual(self.validations.read_text(), 'validated\n')
        self.assertEqual(self.refreshes.read_text(), 'attempted\n')

    def test_rebased_registry_failure_prevents_publication(self):
        concurrent = self.source_commit(path='invalid-registry')
        result = self.run_save()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('TEST concurrent registry is invalid', result.stderr)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main').strip(), concurrent)
        self.assertFalse(self.validations.exists())
        self.assertEqual(self.refreshes.read_text(), 'attempted\n')

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
        self.assertEqual(self.refreshes.read_text(), 'attempted\n')

    def test_unchanged_checkpoint_does_not_create_or_push_another_commit(self):
        first = self.run_save()
        self.assertEqual(first.returncode, 0, first.stderr)
        saved = self.git(self.remote, 'rev-parse', 'main')
        second = self.run_save()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.git(self.remote, 'rev-parse', 'main'), saved)
        self.assertEqual(self.validations.read_text(), 'validated\n')
        self.assertEqual(self.refreshes.read_text(), 'attempted\n')

    def record_outcome(self, plan, fetched=21):
        folder = self.work / 'catalog'
        folder.mkdir(exist_ok=True)
        (folder / 'fawaz-bulk-plan.json').write_text(json.dumps(plan))
        checkpoint = self.source.parent / 'progress.json'
        checkpoint.write_text(json.dumps({'status': 'partial', 'fetched_editions': fetched,
                                         'registered_occurrences': 123, 'complete': False}))
        summary = self.root / 'step-summary.md'
        environment = {**self.env, 'GITHUB_STEP_SUMMARY': str(summary),
                       'PYTHONPATH': str(ROOT / 'scripts'),
                       'SOURCE_INTEGRITY_OUTCOME': 'success'}
        result = subprocess.run(['bash', '-c', workflow_step('Record the batch outcome')],
            cwd=self.work, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads((self.work / '.work/fawaz-bulk-run/run-context.json').read_text())
        return context, summary.read_text()

    def test_outcome_counts_only_published_editions_and_distinguishes_partial_checkpoint(self):
        plan = json.loads((ROOT / 'catalog/fawaz-bulk-plan.json').read_text())
        self.assertEqual(plan['languages'], ['ara', 'eng', 'urd', 'ben'])
        self.assertEqual(len(plan['books']), 8)
        self.assertIn('nawawi', plan['books'])
        context, summary = self.record_outcome(plan)
        self.assertEqual(context['planned_languages'], ['ara', 'eng', 'urd', 'ben'])
        self.assertEqual(context['planned_editions'], 31)
        self.assertEqual(context['planned_books'], plan['books'])
        self.assertEqual(context['progress']['fetched_editions'], 21)
        self.assertFalse(context['progress']['complete'])
        self.assertEqual(context['SOURCE_INTEGRITY_OUTCOME'], 'success')
        self.assertIn('ara, eng, urd, ben', summary)
        self.assertIn('planned whole editions: 31', summary)
        self.assertIn('source integrity: success', summary)

    def test_outcome_uses_actual_plan_for_prior_and_restricted_book_selections(self):
        current = json.loads((ROOT / 'catalog/fawaz-bulk-plan.json').read_text())
        original_books = [book for book in current['books'] if book != 'nawawi']
        for books, languages, expected in (
                (original_books, ['ara', 'eng', 'urd', 'ben'], 28),
                (original_books, ['ara', 'eng', 'urd'], 21),
                (['nawawi'], ['ara', 'eng', 'urd', 'ben'], 3)):
            with self.subTest(books=len(books), languages=len(languages)):
                context, summary = self.record_outcome(
                    {**current, 'books': books, 'languages': languages}, fetched=2)
                self.assertEqual(context['planned_editions'], expected)
                self.assertEqual(context['planned_books'], books)
                self.assertEqual(context['planned_languages'], languages)
                self.assertEqual(context['progress']['fetched_editions'], 2)

    def run_integrity_step(self, fail=False):
        scripts = self.work / 'scripts'
        shutil.copyfile(ROOT / 'scripts/run_logged_task.py', scripts / 'run_logged_task.py')
        (scripts / 'validate_fawaz_sources.py').write_text(
            'import argparse, json, os\nfrom pathlib import Path\n'
            'parser = argparse.ArgumentParser()\n'
            'parser.add_argument("--root", required=True)\n'
            'parser.add_argument("--output", required=True, type=Path)\n'
            'args = parser.parse_args()\n'
            'assert args.root == "."\n'
            'assert str(args.output) == "imports/web-fawaz-20261112/source-integrity-validation.json"\n'
            'if os.environ.get("TEST_SOURCE_INTEGRITY_FAIL"):\n'
            '    raise SystemExit("TEST source text differs from its saved spans")\n'
            'args.output.parent.mkdir(parents=True, exist_ok=True)\n'
            'args.output.write_text(json.dumps({"status": "passed", "acquisition_complete": False}))\n')
        return subprocess.run(['bash', '-c', workflow_step(
            'Verify exact saved source text and complete occurrence accounting')],
            cwd=self.work, env={**self.env, 'TEST_SOURCE_INTEGRITY_FAIL': '1' if fail else ''},
            capture_output=True, text=True, timeout=30)

    def test_source_validation_gate_retains_report_for_a_valid_partial_checkpoint(self):
        result = self.run_integrity_step()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.source.parent / 'source-integrity-validation.json'
        self.assertEqual(json.loads(report.read_text()), {'status': 'passed', 'acquisition_complete': False})
        status = json.loads((self.work / '.work/fawaz-source-integrity/status.json').read_text())
        self.assertEqual(status['exit_code'], 0)

    def test_source_validation_failure_stops_the_gate_and_retains_diagnostics(self):
        result = self.run_integrity_step(fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.source.parent / 'source-integrity-validation.json').exists())
        status = json.loads((self.work / '.work/fawaz-source-integrity/status.json').read_text())
        self.assertNotEqual(status['exit_code'], 0)
        self.assertIn('TEST source text differs',
                      (self.work / '.work/fawaz-source-integrity/output.log').read_text())

    def test_source_integrity_gate_precedes_registry_and_save_with_adequate_export_budget(self):
        source = (ROOT / '.github/workflows/import-fawaz-bulk.yml').read_text()
        gate = source.split('      - name: Verify exact saved source text and complete occurrence accounting\n', 1)[1]
        gate = gate.split('      - name: ', 1)[0]
        self.assertNotIn('continue-on-error:', gate)
        self.assertNotIn('if:', gate)
        order = [source.index('      - name: ' + name) for name in (
            'Rebuild only complete verified books from saved sources',
            'Verify exact saved source text and complete occurrence accounting',
            'Validate the complete material registry', 'Save the validated whole-book batch')]
        self.assertEqual(order, sorted(order))
        export = shlex.split(workflow_step('Rebuild only complete verified books from saved sources'))
        self.assertEqual(export[export.index('--timeout') + 1], '900')
        self.assertIn("      - 'scripts/validate_fawaz_sources.py'", source.split('permissions:', 1)[0])
        self.assertIn('            .work/fawaz-source-integrity/', source)
        self.assertIn('            imports/web-fawaz-20261112/source-integrity-validation.json', source)


if __name__ == '__main__':
    unittest.main()
