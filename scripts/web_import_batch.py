#!/usr/bin/env python3
"""Resume the three authorized finite intakes with independent host budgets."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys

PROGRESS = {
    'deenhindi': 'imports/web-deenhindi-20261112/progress.json',
    'rivoyat': 'imports/web-uzbek-20261112/rivoyat/progress.json',
    'islom': 'imports/web-uzbek-20261112/islom/progress.json',
}
STOP_FILE = 'imports/web-import-worker-stops.json'


def read_json(path, fallback=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback


def write_changed(path, value):
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if not path.exists() or path.read_text(encoding='utf-8') != data:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')


def source_status(root, name):
    progress = read_json(root / PROGRESS[name], {})
    if name == 'deenhindi':
        books = progress.get('by_collection', {})
        unfinished_inventory = len(books) < 7 or any(not item.get('inventory') for item in books.values())
        return {
            'source': name, 'source_progress': PROGRESS[name],
            'last_source_update': progress.get('updated_at'),
            'fetched_entries': progress.get('imported_count', 0),
            'registered_occurrences': progress.get('registered_hadith_count', 0),
            'held_entries': progress.get('classification_pending_count', 0),
            'pending_requests': progress.get('pending_fetch_count'),
            'pending_unit': 'source entry pages',
            'observed_inventory_count': progress.get('inventory_count'),
            'fetch_queue_done': progress.get('done', False),
            'blocked': bool(progress.get('blocked')),
            'errors': progress.get('errors_count', 0),
            'has_fetch_work': not progress or (not progress.get('blocked') and
                not progress.get('done') and (progress.get('pending_fetch_count', 0) > 0 or unfinished_inventory)),
        }
    checkpoint = read_json(root / ('imports/web-uzbek-20261112/' + name + '/checkpoint.json'), {})
    tasks = checkpoint.get('tasks', [])
    blocked = any(task.get('status') == 'blocked' for task in tasks)
    pending = sum(task.get('status') == 'pending' for task in tasks)
    retryable = sum(task.get('status') == 'failed' and task.get('attempts', 1) < 3
                    and not task.get('error', '').startswith('HTTP 404') for task in tasks)
    return {
        'source': name, 'source_progress': PROGRESS[name],
        'last_source_update': progress.get('updated_at'),
        'fetched_entries': progress.get('source_entries_obtained', 0),
        'registered_occurrences': progress.get('prophetic_source_entries_registered', 0),
        'held_entries': progress.get('classification_pending_hidden', 0),
        'pending_requests': pending,
        'pending_unit': 'linked catalogue or section pages; pagination may discover more',
        'discovered_page_tasks': len(tasks),
        'fetch_queue_done': bool(tasks) and all(task.get('status') == 'done' for task in tasks),
        'blocked': blocked, 'errors': sum(task.get('status') == 'failed' for task in tasks),
        'has_fetch_work': not checkpoint or (not blocked and bool(pending or retryable)),
    }


def command(root, name, settings):
    count, seconds, delay = int(settings['max_requests_per_batch']), int(settings['max_seconds_per_batch']), float(settings['delay_seconds'])
    if name not in PROGRESS or not 1 <= count <= 2000 or not 1 <= seconds <= 2400 or not 1 <= delay <= 30:
        raise ValueError('Invalid bounded source budget')
    if name == 'deenhindi':
        args = ['scripts/import_deenhindi.py', '--max-records', str(count), '--delay-seconds', str(delay)]
    else:
        args = ['scripts/import_uzbek_web.py', '--site', name, '--max-pages', str(count), '--delay', str(delay)]
    return [sys.executable, *args, '--root', str(root), '--max-seconds', str(seconds)]


def run_source(root, name, settings, logs):
    logs.mkdir(parents=True, exist_ok=True)
    path = logs / (name + '.log')
    try:
        with path.open('wb') as stream:
            result = subprocess.run(command(root, name, settings), cwd=root, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, timeout=int(settings['max_seconds_per_batch']) + 180, check=False)
        return {'source': name, 'exit_code': result.returncode, 'log': str(path.relative_to(root))}
    except subprocess.TimeoutExpired:
        return {'source': name, 'exit_code': 124, 'log': str(path.relative_to(root)),
                'error': 'Importer exceeded its graceful budget; inspect the retained checkpoint.'}


def summarize(root, plan):
    sources = [source_status(root, name) for name in PROGRESS]
    stops = read_json(root / STOP_FILE, {})
    for item in sources:
        if item['source'] in stops:
            item['worker_stop'] = stops[item['source']]
            item['has_fetch_work'] = False
    return {
        'schema': 'hadith-bank-web-import-status-v1',
        'enabled': plan['enabled'], 'source_status': sources,
        'fetched_entries': sum(item['fetched_entries'] for item in sources),
        'registered_occurrences': sum(item['registered_occurrences'] for item in sources),
        'held_entries': sum(item['held_entries'] for item in sources),
        'requires_attention': bool(stops) or any(item['blocked'] or item['errors'] for item in sources),
        'fetch_queues_done': all(item['fetch_queue_done'] for item in sources),
        'has_fetch_work': any(item['has_fetch_work'] and plan['sources'][item['source']]['enabled'] for item in sources),
        'complete_content_import_certified': False,
        'note': 'Counts describe preserved source entries, not unique canonical hadiths. Queue completion still requires reconciliation of held entries, source omissions and embedded quotations.',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--status-only', action='store_true')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    plan = read_json(root / 'catalog/web-import-plan.json')
    if not isinstance(plan, dict) or plan.get('schema') != 'hadith-bank-web-import-plan-v1':
        raise ValueError('Missing authorized web-import plan')
    stops = read_json(root / STOP_FILE, {})
    if plan.get('enabled') and not args.status_only:
        pending = [name for name in PROGRESS if name not in stops and plan['sources'][name]['enabled']
                   and source_status(root, name)['has_fetch_work']]
        with ThreadPoolExecutor(max_workers=3) as executor:
            jobs = []
            for name in pending:
                settings = dict(plan['sources'][name])
                if not (root / PROGRESS[name]).exists():
                    settings['max_seconds_per_batch'] = min(settings['max_seconds_per_batch'], plan.get('initial_max_seconds', 300))
                jobs.append(executor.submit(run_source, root, name, settings, root / '.work/web-import-batch'))
            for future in as_completed(jobs):
                result = future.result()
                print(json.dumps(result), flush=True)
                if result['exit_code'] and not source_status(root, result['source'])['blocked']:
                    stops[result['source']] = {**result,
                        'reason': 'Inspect the saved log/checkpoint, fix the cause, then explicitly remove this worker stop.'}
    from material_registry import load_public_materials
    registry = load_public_materials(root)
    del registry
    write_changed(root / STOP_FILE, stops)
    status = summarize(root, plan)
    write_changed(root / 'imports/web-import-status.json', status)
    print(json.dumps({k: v for k, v in status.items() if k != 'source_status'}, ensure_ascii=False), flush=True)
    # Valid stopped/blocked checkpoints must be committed. Invalid evidence
    # raises above and cannot reach automatic publication.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
