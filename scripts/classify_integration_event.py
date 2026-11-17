#!/usr/bin/env python3
"""Route one reviewed maintenance push to offline jobs; never fetch or write Git."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

EXPECTED_BEFORE = 'b7d0c75ab1f3418d992f4ea7b8c82ca7e24cb7fe'
EXPECTED_CHANGES = {
    'scripts/import_deenhindi.py': 'M',
    'tests/test_import_deenhindi.py': 'M',
    'tests/test_deenhindi_reviewed_error_retries.py': 'M',
    'tests/test_deenhindi_transport_safety.py': 'A',
    'scripts/classify_integration_event.py': 'A',
    'tests/test_classify_integration_event.py': 'A',
    '.github/workflows/import-web-hadith.yml': 'M',
    '.github/workflows/reader-pages.yml': 'M',
}
# Content already independently reviewed and passed PR31's complete validation.
REVIEWED_HASHES = {'scripts/import_deenhindi.py': '3d7bb891fc4fb699ca5a7fcd6255e4df36fe6efd6def32e2f55e487b54d43b32', 'tests/test_import_deenhindi.py': '8d30ec5a0043f8e65bb070dcf5cf1bce923b14ad2dc780fb39d40b7bf4195410', 'tests/test_deenhindi_reviewed_error_retries.py': 'd3acb9995d53e8fb7f586e7e5c57db821b1de294c58dc5beeec9fcbe41359d0d', 'tests/test_deenhindi_transport_safety.py': '2a007bcbed0bec3c59376eaf9e21e71c89e1d6721a55b328e399e0527fb6acb5'}
MODES = frozenset(('hold', 'validate_only', 'existing_main_flow', 'offline_maintenance'))
MAX_DIFF_BYTES = 8 * 1024 * 1024
MAX_EVENT_BYTES = 32 * 1024 * 1024

def sha_ok(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}', value) is not None and value != '0' * 40

def safe_path(value):
    return (isinstance(value, str) and bool(value) and not value.startswith('/')
            and '\\' not in value and not any(ord(c) < 32 or ord(c) == 127 for c in value)
            and not any(p in ('', '.', '..') for p in value.split('/')))

def parse_diff(raw):
    """Parse complete `git diff --no-renames --name-status -z` bytes only."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_DIFF_BYTES or not raw.endswith(b'\0'):
        raise ValueError('missing, oversized or unterminated diff')
    tokens = raw[:-1].split(b'\0')
    if len(tokens) % 2:
        raise ValueError('incomplete status/path pairs')
    changes = {}
    for index in range(0, len(tokens), 2):
        status = tokens[index].decode('ascii', errors='strict')
        path = tokens[index + 1].decode('utf-8', errors='strict')
        if status not in ('A', 'M', 'D') or not safe_path(path) or path in changes:
            raise ValueError('invalid status, path or duplicate')
        changes[path] = status
    return changes

def classify(event, ref, before=None, after=None, changes=None, diff_complete=False, pins_match=False):
    if event == 'pull_request':
        return 'validate_only'
    if event in ('schedule', 'workflow_dispatch'):
        return 'existing_main_flow' if ref == 'refs/heads/main' else 'hold'
    if event != 'push' or ref != 'refs/heads/main':
        return 'hold'
    if not sha_ok(before) or not sha_ok(after) or before == after or diff_complete is not True:
        return 'hold'
    if not isinstance(changes, dict) or not changes or any(not safe_path(p) or s not in ('A','M','D') for p,s in changes.items()):
        return 'hold'
    if changes.get('scripts/classify_integration_event.py') == 'A':
        return ('offline_maintenance' if before == EXPECTED_BEFORE and changes == EXPECTED_CHANGES
                and pins_match is True else 'hold')
    # All other verified ordinary pushes retain the original job routing.
    return 'existing_main_flow'

def git(root, *arguments):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    result = subprocess.run(['git', '--no-pager', '-C', str(root), *arguments],
                            capture_output=True, check=False, timeout=60, env=env)
    if result.returncode != 0:
        raise ValueError('local Git verification failed')
    return result.stdout

def decide(event, ref, github_sha, payload, root, runner=git):
    if event != 'push':
        return classify(event, ref)
    if ref != 'refs/heads/main' or not isinstance(payload, dict):
        return 'hold'
    before, after = payload.get('before'), payload.get('after')
    if (payload.get('ref') != ref or payload.get('forced') is not False
            or payload.get('deleted') is not False or payload.get('created') is not False
            or not sha_ok(before) or not sha_ok(after) or before == after or github_sha != after):
        return 'hold'
    try:
        for value in (before, after):
            if runner(root, 'rev-parse', '--verify', value + '^{commit}').decode().strip() != value:
                raise ValueError('commit identity mismatch')
        if runner(root, 'rev-parse', '--verify', 'HEAD').decode().strip() != after:
            raise ValueError('checkout identity mismatch')
        runner(root, 'merge-base', '--is-ancestor', before, after)
        runner(root, 'diff', '--no-ext-diff', '--quiet', 'HEAD', '--')
        raw = runner(root, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-status', '-z', before, after, '--')
        changes = parse_diff(raw)
        pins_match = False
        if before == EXPECTED_BEFORE and changes == EXPECTED_CHANGES:
            pins_match = all(hashlib.sha256(runner(root, 'show', after + ':' + path)).hexdigest() == digest
                             for path, digest in REVIEWED_HASHES.items())
        return classify(event, ref, before, after, changes, True, pins_match)
    except (ValueError, OSError, UnicodeError, subprocess.SubprocessError):
        return 'hold'

def main():
    mode = 'hold'
    try:
        event = os.environ.get('GITHUB_EVENT_NAME')
        payload = None
        if event == 'push':
            with Path(os.environ['GITHUB_EVENT_PATH']).open('rb') as handle:
                raw = handle.read(MAX_EVENT_BYTES + 1)
            if len(raw) > MAX_EVENT_BYTES:
                raise ValueError('oversized event')
            payload = json.loads(raw)
        mode = decide(event, os.environ.get('GITHUB_REF'), os.environ.get('GITHUB_SHA'),
                      payload, Path(os.environ.get('GITHUB_WORKSPACE', '.')).resolve())
    except (KeyError, ValueError, OSError, UnicodeError):
        mode = 'hold'
    if mode not in MODES:
        mode = 'hold'
    with Path(os.environ['GITHUB_OUTPUT']).open('a', encoding='utf-8') as handle:
        handle.write('mode=' + mode + '\n')
    print('Integration mode: ' + mode)
    return 1 if mode == 'hold' else 0

if __name__ == '__main__':
    raise SystemExit(main())
