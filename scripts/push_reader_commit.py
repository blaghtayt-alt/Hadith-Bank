#!/usr/bin/env python3
"""Publish a generated commit only while it is still the current bank revision.

Use one ordinary fast-forward push and read back the remote ref. A concurrent
source update withholds the stale artifact; an uncertain or genuinely failed
push is an error. The workflow can request a current build after a clean skip.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class SynchronizationError(RuntimeError):
    pass


def run_git(root, *arguments):
    return subprocess.run(['git', *arguments], cwd=root, capture_output=True,
                          text=True, check=False)


def remote_head(root):
    result = run_git(root, 'ls-remote', '--exit-code', 'origin', 'refs/heads/main')
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if (result.returncode or len(rows) != 1 or len(rows[0]) != 2 or
            rows[0][1] != 'refs/heads/main' or not re.fullmatch(r'[0-9a-f]{40,64}', rows[0][0])):
        raise SynchronizationError('Could not verify origin/main; publication withheld.')
    return rows[0][0]


def synchronize(root, expected_start):
    root = Path(root).resolve()
    if not re.fullmatch(r'[0-9a-f]{40,64}', expected_start):
        raise SynchronizationError('Expected starting revision must be a full commit SHA.')
    result = run_git(root, 'rev-parse', '--verify', 'HEAD^{commit}')
    local_head = result.stdout.strip()
    if result.returncode or not re.fullmatch(r'[0-9a-f]{40,64}', local_head):
        raise SynchronizationError('Could not verify the generated local commit.')
    if run_git(root, 'merge-base', '--is-ancestor', expected_start, local_head).returncode:
        raise SynchronizationError('Generated commit does not descend from the expected starting revision.')

    def outcome(current, status, publish):
        return {'status': status, 'publish': publish, 'expected_start': expected_start,
                'generated_commit': local_head, 'remote_commit': current}

    current = remote_head(root)
    if current == local_head:
        return outcome(current, 'current', True)
    if current != expected_start:
        return outcome(current, 'superseded', False)

    # No force, retry or rebase: the artifact was built from this exact commit.
    pushed = run_git(root, 'push', 'origin', local_head + ':refs/heads/main')
    current = remote_head(root)
    if current == local_head:
        return outcome(current, 'pushed' if pushed.returncode == 0 else 'push_acknowledgment_recovered', True)
    if current != expected_start:
        return outcome(current, 'superseded', False)
    raise SynchronizationError(
        'Generated commit was not saved: git push returned ' + str(pushed.returncode) +
        ' and origin/main still points to the starting revision; publication withheld.')


def write_outputs(path, result):
    if not path:
        return
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write('publish=' + str(result['publish']).lower() + '\n')
        if result['publish']:
            stream.write('published_commit=' + result['generated_commit'] + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--expected-start', required=True)
    parser.add_argument('--github-output', default=os.environ.get('GITHUB_OUTPUT'))
    parser.add_argument('--request-current-build', action='store_true',
                        help='Dispatch the current main build after a superseded result')
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY'))
    args = parser.parse_args(argv)
    if args.request_current_build and not args.repository:
        parser.error('--request-current-build requires --repository or GITHUB_REPOSITORY')
    try:
        result = synchronize(args.root, args.expected_start)
    except (OSError, SynchronizationError) as error:
        write_outputs(args.github_output, {'publish': False})
        print(json.dumps({'status': 'failed', 'publish': False, 'error': str(error)}), file=sys.stderr)
        return 1
    write_outputs(args.github_output, result)
    if result['status'] == 'superseded' and args.request_current_build:
        try:
            dispatched = subprocess.run(
                ['gh', 'workflow', 'run', 'reader-pages.yml', '--ref', 'main',
                 '--repo', args.repository], cwd=args.root, check=False)
        except OSError as error:
            print(json.dumps({**result, 'build_request': 'failed', 'error': str(error)}), file=sys.stderr)
            return 1
        if dispatched.returncode:
            print(json.dumps({**result, 'build_request': 'failed',
                              'dispatch_exit_code': dispatched.returncode}), file=sys.stderr)
            return dispatched.returncode if dispatched.returncode > 0 else 1
        result['build_request'] = 'submitted'
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
