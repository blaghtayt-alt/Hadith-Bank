#!/usr/bin/env python3
"""Resume the three authorized finite intakes with independent host budgets."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

from web_source_reviews import SourceReviews, FOLDERS as REVIEW_FOLDERS

PROGRESS = {
    'deenhindi': 'imports/web-deenhindi-20261112/progress.json',
    'rivoyat': 'imports/web-uzbek-20261112/rivoyat/progress.json',
    'islom': 'imports/web-uzbek-20261112/islom/progress.json',
    'hadisuz': 'imports/web-hadisuz-20261112/progress.json',
}
STOP_FILE = 'imports/web-import-worker-stops.json'
BEFORE_STATUS = '.work/web-import-batch/before-status.json'


def read_json(path, fallback=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback


def write_changed(path, value):
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if not path.exists() or path.read_text(encoding='utf-8') != data:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                             prefix='.' + path.name + '.', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def source_status(root, name):
    progress = read_json(root / PROGRESS[name], {})
    if name == 'hadisuz':
        blocked = bool(progress.get('blocked') or progress.get('access_block'))
        stopped = bool(progress.get('startup_stopped'))
        pending = int(progress.get('pending_requests', 0))
        retryable = int(progress.get('retryable_errors', 0))
        errors = int(progress.get('errors', 0))
        return {
            'source': name, 'source_progress': PROGRESS[name],
            'last_source_update': progress.get('updated_at'),
            'fetched_entries': progress.get('source_entries_obtained', 0),
            'registered_occurrences': progress.get('prophetic_source_entries_registered', 0),
            'held_entries': progress.get('classification_pending_hidden', 0),
            'non_narration_source_entries': progress.get('non_narration_source_entries', 0),
            'pending_requests': pending,
            'pending_unit': 'observed catalogue and detail pages; pagination may discover more',
            'fetch_queue_done': bool(progress.get('done')) and not (blocked or stopped or errors),
            'blocked': blocked, 'startup_stopped': stopped,
            'access_block': progress.get('access_block'), 'errors': errors,
            'has_fetch_work': not blocked and not stopped and
                (not progress or (not progress.get('done') and bool(pending or retryable))),
        }
    if name == 'deenhindi':
        books = progress.get('by_collection', {})
        unfinished_inventory = len(books) < 7 or any(not item.get('inventory') for item in books.values())
        return {
            'source': name, 'source_progress': PROGRESS[name],
            'last_source_update': progress.get('updated_at'),
            'fetched_entries': progress.get('imported_count', 0),
            'registered_occurrences': progress.get('registered_hadith_count', 0),
            'held_entries': progress.get('classification_pending_count', 0),
            'non_narration_source_entries': progress.get('non_narration_source_entries', 0),
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
    page_tasks = checkpoint.get('tasks', [])
    detail_tasks = list(checkpoint.get('detail_metadata_tasks', {}).values())
    tasks = [*page_tasks, *detail_tasks]
    access_block = (checkpoint.get('site_access_block') or checkpoint.get('access_block')
                    or progress.get('access_block'))
    blocked = bool(access_block) or bool(progress.get('blocked')) or any(task.get('status') == 'blocked' for task in tasks)
    pending_pages = sum(task.get('status') == 'pending' for task in page_tasks)
    pending_details = sum(task.get('status') == 'pending' for task in detail_tasks)
    pending = pending_pages + pending_details
    retryable = sum(task.get('status') == 'failed' and task.get('attempts', 1) < 3
                    and not task.get('error', '').startswith('HTTP 404') for task in tasks)
    return {
        'source': name, 'source_progress': PROGRESS[name],
        'last_source_update': progress.get('updated_at'),
        'fetched_entries': progress.get('source_entries_obtained', 0),
        'registered_occurrences': progress.get('prophetic_source_entries_registered', 0),
        'held_entries': progress.get('classification_pending_hidden', 0),
        'non_narration_source_entries': progress.get('non_narration_source_entries', 0),
        'pending_requests': pending,
        'pending_unit': 'linked catalogue, section or detail pages; pagination may discover more',
        'pending_page_requests': pending_pages,
        'pending_detail_requests': pending_details,
        'discovered_page_tasks': len(page_tasks),
        'discovered_detail_tasks': len(detail_tasks),
        'detail_metadata_processed': sum(task.get('status') == 'done' for task in detail_tasks),
        'fetch_queue_done': not blocked and bool(tasks) and all(task.get('status') == 'done' for task in tasks),
        'blocked': blocked, 'errors': sum(task.get('status') == 'failed' for task in tasks),
        'access_block': access_block,
        'has_fetch_work': not blocked and (not checkpoint or bool(pending or retryable)),
    }


def command(root, name, settings):
    count, seconds, delay = int(settings['max_requests_per_batch']), int(settings['max_seconds_per_batch']), float(settings['delay_seconds'])
    if name not in PROGRESS or not 1 <= count <= 2000 or not 1 <= seconds <= 2400 or not 1 <= delay <= 30:
        raise ValueError('Invalid bounded source budget')
    if name == 'deenhindi':
        args = ['scripts/import_deenhindi.py', '--max-records', '0' if settings.get('export_only') else str(count), '--delay-seconds', str(delay)]
    elif name == 'hadisuz':
        args = ['scripts/import_hadisuz.py', '--max-pages', str(count), '--delay', str(delay)]
    else:
        args = ['scripts/import_uzbek_web.py', '--site', name, '--max-pages', str(count), '--delay', str(delay)]
    if settings.get('export_only') and name != 'deenhindi':
        args.append('--export-only')
    return [sys.executable, *args, '--root', str(root), '--max-seconds', str(seconds)]


def has_review_export_work(root, name):
    """A newly saved review can be applied even when public fetching is done.

    This compares durable input receipts; it never resets an access stop or a
    failed URL, and it does not turn an unchanged review into a recurring job.
    """
    if name not in REVIEW_FOLDERS:
        return False
    reviews = SourceReviews(root, name)
    if not reviews.decisions:
        return False
    progress = read_json(root / PROGRESS[name], {})
    return (progress.get('source_review_inputs', []) != reviews.supporting_files()
            or progress.get('source_review_engine_sha256') != reviews.engine_sha256)


def run_source(root, name, settings, logs):
    logs.mkdir(parents=True, exist_ok=True)
    path = logs / (name + '.log')
    try:
        with path.open('wb') as stream:
            result = subprocess.run(command(root, name, settings), cwd=root, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, timeout=int(settings['max_seconds_per_batch']) + 180, check=False)
        result = {'source': name, 'exit_code': result.returncode, 'log': str(path.relative_to(root))}
    except subprocess.TimeoutExpired:
        result = {'source': name, 'exit_code': 124, 'log': str(path.relative_to(root)),
                  'error': 'Importer exceeded its graceful budget; inspect the retained checkpoint.'}
    except Exception as error:
        with path.open('a', encoding='utf-8') as stream:
            traceback.print_exc(file=stream)
        result = {'source': name, 'exit_code': 1, 'log': str(path.relative_to(root)),
                  'error': type(error).__name__ + ': ' + str(error)[:300]}
    # Each result survives a later worker or registry failure and is included
    # in the run's diagnostic artifact. A hard timeout is not safe to retry.
    write_changed(logs / (name + '.result.json'), result)
    return result


def summarize(root, plan):
    sources = [source_status(root, name) for name in PROGRESS]
    stops = read_json(root / STOP_FILE, {})
    for item in sources:
        item['enabled'] = bool(plan['sources'][item['source']]['enabled'])
        item['excluded_by_owner'] = bool(plan['sources'][item['source']].get('excluded_by_owner'))
        if item['source'] in stops:
            item['worker_stop'] = stops[item['source']]
            item['blocked'] = item['blocked'] or item['worker_stop'].get('blocked') is True
            item['has_fetch_work'] = False
        if item.get('worker_stop') or item['blocked']:
            item['fetch_queue_done'] = False
        item['state'] = ('blocked' if item['blocked'] else 'stopped' if item.get('worker_stop')
                         else 'complete' if item['fetch_queue_done'] else 'pending' if item['has_fetch_work']
                         else 'failed' if item['errors'] else 'paused')
        if item['excluded_by_owner']:
            item['historical_source_counts'] = {key: item[key] for key in
                ('fetched_entries', 'registered_occurrences', 'held_entries')}
            item.update(enabled=False, state='excluded_by_owner', has_fetch_work=False,
                        fetch_queue_done=False, registered_occurrences=0,
                        fetched_entries=0, held_entries=0)
    active_sources = [item for item in sources if not item['excluded_by_owner']]
    has_work = bool(plan['enabled']) and any(item['has_fetch_work'] and item['enabled'] for item in sources)
    done = bool(active_sources) and all(item['fetch_queue_done'] for item in active_sources)
    attention = any(item.get('worker_stop') or item['blocked'] or item['errors'] or
                    item.get('startup_stopped') for item in active_sources)
    return {
        'schema': 'hadith-bank-web-import-status-v1',
        'enabled': plan['enabled'], 'source_status': sources,
        'fetched_entries': sum(item['fetched_entries'] for item in sources),
        'registered_occurrences': sum(item['registered_occurrences'] for item in sources),
        'held_entries': sum(item['held_entries'] for item in sources),
        'non_narration_source_entries': sum(item['non_narration_source_entries'] for item in active_sources),
        'requires_attention': attention,
        'fetch_queues_done': done,
        'has_fetch_work': has_work,
        'schedule_should_pause': not has_work,
        'schedule_pause_reason': (None if has_work else 'plan_disabled' if not plan['enabled']
                                  else 'fetch_queues_complete' if done else 'inspection_required' if attention
                                  else 'no_enabled_fetch_work'),
        'complete_content_import_certified': False,
        'note': 'Counts describe preserved source entries, not unique canonical hadiths. Queue completion still requires reconciliation of held entries, source omissions and embedded quotations.',
    }


def continuation_request(root):
    """Request another finite batch only after a validated, productive batch.

    This is advisory. The workflow may dispatch it only after the source
    checkpoint has actually been saved. A status-only refresh must not replace
    the before-batch receipt or turn an idle/error loop into fresh progress.
    """
    plan = read_json(root / 'catalog/web-import-plan.json', {})
    before = read_json(root / BEFORE_STATUS, {})
    diagnostic = read_json(root / '.work/web-import-batch/status.json', {})
    result = {'schema': 'hadith-bank-finite-import-continuation-v1',
              'continue': False, 'sources': [],
              'reason': 'no_validated_productive_authorized_source'}
    if (not plan.get('enabled') or diagnostic.get('validation_state') != 'passed'
            or not isinstance(before.get('source_status'), list)):
        return result
    previous = {item['source']: item for item in before['source_status']}
    for current in summarize(root, plan)['source_status']:
        name = current['source']
        settings = plan.get('sources', {}).get(name, {})
        original = previous.get(name)
        if (not settings.get('continue_after_success') or original is None
                or not current.get('enabled') or current.get('excluded_by_owner')
                or current.get('blocked') or current.get('worker_stop')
                or current.get('startup_stopped') or not current.get('has_fetch_work')
                or (current['fetched_entries'] <= original.get('fetched_entries', 0)
                    and name not in diagnostic.get('applied_review_sources', []))):
            continue
        result['sources'].append({'source': name,
            'before_fetched': original['fetched_entries'],
            'after_fetched': current['fetched_entries'],
            'remaining_requests': current.get('pending_requests')})
    if result['sources']:
        result['continue'] = True
        result['reason'] = 'validated_new_source_pages_and_remaining_authorized_queue'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--status-only', action='store_true')
    parser.add_argument('--reviews-only', action='store_true',
                        help='Apply changed saved reviews offline without fetching or replacing the acquisition-before receipt')
    parser.add_argument('--continuation-request', action='store_true',
                        help='Report whether a successfully saved batch may continue; do not fetch or dispatch')
    args = parser.parse_args(argv)
    if args.status_only and args.reviews_only:
        parser.error('status-only and reviews-only cannot be combined')
    root = args.root.resolve()
    plan = read_json(root / 'catalog/web-import-plan.json')
    if not isinstance(plan, dict) or plan.get('schema') != 'hadith-bank-web-import-plan-v1':
        raise ValueError('Missing authorized web-import plan')
    if args.continuation_request:
        print(json.dumps(continuation_request(root), ensure_ascii=False))
        return 0
    stops = read_json(root / STOP_FILE, {})
    review_sources = []
    if plan.get('enabled') and not args.status_only:
        if not args.reviews_only:
            write_changed(root / BEFORE_STATUS, summarize(root, plan))
        eligible = [name for name in PROGRESS if name not in stops and plan['sources'][name]['enabled']
                   and not plan['sources'][name].get('excluded_by_owner')
                   ]
        review_sources = [name for name in eligible if has_review_export_work(root, name)]
        # Save newly reviewed source selections promptly in one network-free
        # cycle. The ordinary Hindi queue resumes only after that checkpoint
        # passes validation and is saved by the existing workflow.
        pending = review_sources or ([] if args.reviews_only else
                                     [name for name in eligible if source_status(root, name)['has_fetch_work']])
        with ThreadPoolExecutor(max_workers=3) as executor:
            jobs = {}
            for name in pending:
                settings = dict(plan['sources'][name])
                if review_sources:
                    settings['export_only'] = True
                if not (root / PROGRESS[name]).exists():
                    settings['max_seconds_per_batch'] = min(settings['max_seconds_per_batch'], plan.get('initial_max_seconds', 300))
                logs = root / '.work/web-import-batch'
                if args.reviews_only:
                    logs = logs / 'rebase-review'
                jobs[executor.submit(run_source, root, name, settings, logs)] = name
            for future in as_completed(jobs):
                try:
                    result = future.result()
                except Exception as error:
                    # An unexpected worker wrapper failure must not discard
                    # other hosts' completed results or their saved stops.
                    result = {'source': jobs[future], 'exit_code': 1,
                              'error': type(error).__name__ + ': ' + str(error)[:300]}
                    diagnostic_dir = root / '.work/web-import-batch'
                    if args.reviews_only:
                        diagnostic_dir = diagnostic_dir / 'rebase-review'
                    write_changed(diagnostic_dir / (jobs[future] + '.result.json'), result)
                print(json.dumps(result), flush=True)
                if result['exit_code']:
                    stops[result['source']] = {**result,
                        'reason': 'Inspect the saved log/checkpoint, fix the cause, then explicitly remove this worker stop.'}
                # Persist control state before global validation. Invalid
                # source evidence still raises below and prevents publication.
                write_changed(root / STOP_FILE, stops)
    write_changed(root / STOP_FILE, stops)
    status = summarize(root, plan)
    from material_registry import load_public_materials
    try:
        registry = load_public_materials(root)
        del registry
    except Exception as error:
        write_changed(root / '.work/web-import-batch/status.json', {
            **status, 'validation_state': 'failed',
            'validation_error': type(error).__name__ + ': ' + str(error)[:300],
        })
        raise
    if args.status_only or args.reviews_only:
        prior_diagnostic = read_json(root / '.work/web-import-batch/status.json', {})
        if prior_diagnostic.get('validation_state') == 'passed':
            review_sources = list(dict.fromkeys([*review_sources, *prior_diagnostic.get('applied_review_sources', [])]))
    applied_reviews = [name for name in review_sources if name in REVIEW_FOLDERS
                       and name not in stops and not has_review_export_work(root, name)]
    write_changed(root / '.work/web-import-batch/status.json', {
        **status, 'validation_state': 'passed', 'applied_review_sources': applied_reviews})
    write_changed(root / 'imports/web-import-status.json', status)
    print(json.dumps({k: v for k, v in status.items() if k != 'source_status'}, ensure_ascii=False), flush=True)
    # Valid stopped/blocked checkpoints must be committed. Invalid evidence
    # raises above and cannot reach automatic publication.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
