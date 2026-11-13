#!/usr/bin/env python3
"""Real Chromium smoke checks for the bounded reader.

All generated records are explicitly synthetic TEST fixtures, not religious
quotations. --build-only validates fixture generation without opening sockets or
launching a browser. Normal runs require an allowed Playwright Chromium runtime;
this script does not change sandbox or browser security settings.
"""
import argparse
import asyncio
from collections import Counter
import contextlib
import functools
import gzip
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
from urllib.parse import urlencode, urlsplit

import build_reader


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def fixture_records():
    records = []
    for number in range(1, 61):
        records.append({
            'id': 'TEST-occurrence-' + str(number).zfill(3),
            'language': 'en', 'source_language_code': 'en',
            'book_key': 'bukhari', 'edition': 'TEST synthetic edition',
            'source_id': 'TEST synthetic source',
            'title': 'TEST technical UI fixture ' + str(number),
            'text_translation': 'TEST technical UI text ' + str(number) + '; not a religious quotation.',
            'text_arabic': None, 'number': {'in_book': number, 'canonical': None},
            'source': {'name': 'TEST synthetic publisher', 'url': None, 'original_file': None},
            'translator': {'name': None}, 'narrator': {'name': None},
            'translation_provenance': {'ai_translation': 'unknown', 'origin': 'unknown',
                                       'basis': 'TEST fixture, not a translation'},
            'review': {'status': 'TEST synthetic fixture'},
            'topic_tags': [], 'editorial_tags': [], 'source_headings': [],
            'footnotes': [], 'references': {},
            'unknown_original_field': {
                'null_value': None, 'false_value': False, 'zero_value': 0,
                'nested': [None, {'TEST_unicode': 'TEST 🌿 漢字 أ ۱۲۳'}],
                # An opaque original field makes full details substantially larger
                # than directory/search projections and exercises cache eviction.
                'payload': ('TEST opaque 🌿 漢字 أ 123 ' * 9000) + str(number),
            },
        })
    records[7]['text_translation'] += ' TESTprimaryanchor'
    records[7]['footnotes'] = [{'text': 'TESTannotationneedle', 'original_null': None}]
    # A complete occurrence ID containing recognizable citation syntax must take
    # priority over canonical citation parsing. This remains a TEST identifier.
    records[42]['id'] = 'TEST source occurrence Abu Dawud 4555'
    return records


def script_payload(document, identifier):
    match = re.search(r'<script\b[^>]*\bid="' + re.escape(identifier) +
                      r'"[^>]*>(.*?)</script\s*>', document, re.S)
    require(match is not None, 'Missing embedded ' + identifier)
    return json.loads(match.group(1))


def build_fixture(directory):
    source = directory / 'source'
    site = directory / 'site'
    (source / 'catalog').mkdir(parents=True)
    (source / 'search').mkdir()
    site.mkdir()
    records = fixture_records()
    # Deliberately retain canonical whitespace different from compact details.
    raw = b''.join((json.dumps(row, ensure_ascii=False) + '\n').encode('utf-8')
                   for row in records)
    (source / 'search/records.jsonl').write_bytes(raw)
    catalog = {
        'title': 'TEST synthetic reader browser fixture',
        'search': {'records_path': 'search/records.jsonl', 'count': len(records),
                   'records_sha256': hashlib.sha256(raw).hexdigest()},
        'materials': [],
    }
    (source / 'catalog/materials.json').write_text(json.dumps(catalog), encoding='utf-8')
    hosted = build_reader.build(source, site / 'index.html', data_directory=site / 'data',
                                max_shard_bytes=65536)
    build_reader.build(source, site / 'standalone.html')
    manifest = json.loads((site / 'data/manifest.json').read_text(encoding='utf-8'))
    rows = []
    for part in manifest['directory']['shards']:
        rows.extend(json.loads(line) for line in gzip.decompress((site / part['path']).read_bytes()).splitlines())
    require(len(rows) == 60, 'Synthetic directory must contain all 60 TEST occurrences')
    require(len(manifest['details']['shards']) > 25, 'Synthetic details must require selective loading')
    return {'site': site, 'records': records, 'manifest': manifest, 'directory': rows,
            'build': hosted}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            # Aborted stale views are an expected part of this test.
            pass


@contextlib.contextmanager
def local_server(directory):
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.1}, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port) + '/'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def detail_paths(manifest, directory, ordinals):
    result = set()
    size = manifest['details']['plain_part_bytes']
    for ordinal in ordinals:
        offset, length = directory[ordinal]['_reader']['detail']
        for index in range(offset // size, (offset + length - 1) // size + 1):
            result.add(manifest['details']['shards'][index]['path'])
    return result


async def wait_results(page, identifiers, timeout):
    await page.wait_for_function(
        """expected => {
          const results=document.getElementById("results");
          if(!results || results.getAttribute("aria-busy")!=="false" ||
             results.querySelector(".error"))return false;
          const ids=[...results.querySelectorAll(":scope > .record-card")]
            .map(card=>card.dataset.occurrenceId);
          const count=document.getElementById("result-count").textContent;
          return JSON.stringify(ids)===JSON.stringify(expected) &&
            count.includes("matching source occurrences");
        }""", arg=identifiers, timeout=timeout)


async def card_ids(page):
    return await page.locator('#results > .record-card').evaluate_all(
        'cards => cards.map(card=>card.dataset.occurrenceId)')


async def lazy_audit(page, expected_record, timeout):
    card = page.locator('#results .record-card').first
    audit = card.locator('details').filter(
        has=page.locator('summary', has_text=re.compile(r'^Record details & provenance$')))
    require(await audit.count() == 1, 'Expected one record audit disclosure')
    require(await audit.locator('pre').count() == 0, 'Collapsed audit must not serialize the full record')
    await audit.locator(':scope > summary').click()
    await audit.locator('pre').wait_for(state='attached', timeout=timeout)
    actual = json.loads(await audit.locator('pre').text_content())
    require(actual == expected_record, 'Expanded audit must retain the exact full source object')


async def fixture_browser_checks(browser, fixture, base, timeout, report):
    records, manifest = fixture['records'], fixture['manifest']
    identifiers = [item['id'] for item in records]
    context = await browser.new_context(accept_downloads=True)
    errors = []
    context.on('page', lambda page: page.on('pageerror', lambda error: errors.append(str(error)[:500])))
    page = await context.new_page()
    requests = []
    page.on('request', lambda request: requests.append(urlsplit(request.url).path.lstrip('/')))
    try:
        await page.goto(base + 'index.html', wait_until='domcontentloaded', timeout=timeout)
        await wait_results(page, identifiers[:25], timeout)
        require((await page.locator('#page-meta').text_content()) == 'Page 1 of 3',
                'Ordinary startup must show page 1 of 3')
        initial = set(requests)
        expected_parts = detail_paths(manifest, fixture['directory'], range(25))
        actual_parts = {path for path in initial if path.startswith('data/details/')}
        require(actual_parts == expected_parts, 'Startup must hydrate only detail chunks intersecting the first page')
        require(len(actual_parts) < len(manifest['details']['shards']),
                'Startup must not fetch every full-detail chunk')
        require(not any(path.startswith(('data/search/', 'data/annotations/')) for path in initial),
                'Empty-query startup must not fetch primary or commentary search data')
        report['startup'] = {'cards': 25, 'detail_parts_requested': len(actual_parts),
                             'detail_parts_total': len(manifest['details']['shards']),
                             'text_search_parts_requested': 0}
        report['checks'].append('ordinary_startup_selective_detail_requests')
        await lazy_audit(page, records[0], timeout)
        report['checks'].append('full_audit_serialized_only_when_opened')

        await page.get_by_role('checkbox', name='Select ' + identifiers[0], exact=True).check()
        await page.locator('#next').click()
        await wait_results(page, identifiers[25:50], timeout)
        await page.get_by_role('checkbox', name='Select ' + identifiers[25], exact=True).check()
        await page.locator('#next').click()
        await wait_results(page, identifiers[50:60], timeout)
        await page.get_by_role('checkbox', name='Select ' + identifiers[59], exact=True).check()
        report['checks'].append('paging_preserves_original_order_and_selection')

        await page.locator('#query').fill('TESTprimaryanchor')
        await wait_results(page, [identifiers[7]], timeout)
        await page.locator('#query').fill('TESTprimaryanchor TESTannotationneedle')
        await wait_results(page, [], timeout)
        await page.locator('#include-commentary').check()
        await wait_results(page, [identifiers[7]], timeout)
        report['checks'].append('primary_and_commentary_terms_match_only_with_opt_in')

        before_download_requests = Counter(requests)
        async with page.expect_download(timeout=timeout) as download_event:
            await page.locator('#download').click()
        download = await download_event.value
        require(download.suggested_filename == 'hadith-bank-selected-records.json',
                'Selected download filename must remain stable')
        selected_path = fixture['site'].parent / 'selected.json'
        await download.save_as(str(selected_path))
        selected = json.loads(selected_path.read_text(encoding='utf-8'))
        require(selected == [records[0], records[25], records[59]],
                'Selected JSON must preserve complete original objects, unknown fields, nulls and order')
        after_download_requests = Counter(requests)
        require(any(after_download_requests[path] > before_download_requests[path]
                    for path in detail_paths(manifest, fixture['directory'], [0])),
                'Selection after paging must rehydrate evicted original details')
        report['selected_json_records'] = len(selected)
        report['checks'].append('selected_json_exact_objects_after_paging_and_filters')

        await page.locator('#include-commentary').uncheck()
        await page.locator('#query').fill('Bukhari 12')
        await wait_results(page, [identifiers[11]], timeout)
        await page.locator('#query').fill(identifiers[42])
        await wait_results(page, [identifiers[42]], timeout)
        report['checks'].append('canonical_citation_and_exact_id_priority')

        deep = await context.new_page()
        await deep.goto(base + 'index.html?' + urlencode({'occurrence': identifiers[42]}),
                        wait_until='domcontentloaded', timeout=timeout)
        await wait_results(deep, [identifiers[42]], timeout)
        await deep.close()
        report['checks'].append('exact_occurrence_deep_link')

        # A separate page has no parsed primary-key cache. Hold its first search
        # response, enter a new exact ID, then release the old response.
        stale = await context.new_page()
        started, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
        first_request = True

        async def delayed_search(route):
            nonlocal first_request
            if not first_request:
                await route.continue_()
                return
            first_request = False
            started.set()
            await release.wait()
            try:
                await route.continue_()
            except Exception:
                # Aborting the superseded operation may already close this route.
                # Current-view assertions below still must pass.
                pass
            finally:
                finished.set()

        await stale.route('**/data/search/*.jsonl.gz', delayed_search)
        try:
            await stale.goto(base + 'index.html', wait_until='domcontentloaded', timeout=timeout)
            await wait_results(stale, identifiers[:25], timeout)
            await stale.locator('#query').fill('TESTprimaryanchor')
            await asyncio.wait_for(started.wait(), timeout=timeout / 1000)
            await stale.locator('#query').fill(identifiers[42])
            await wait_results(stale, [identifiers[42]], timeout)
            release.set()
            await asyncio.wait_for(finished.wait(), timeout=timeout / 1000)
            # The fixture has one primary-key shard; give its released completion
            # task time to run so an unguarded stale render would be observable.
            await stale.wait_for_timeout(300)
            await wait_results(stale, [identifiers[42]], timeout)
        finally:
            release.set()
            await stale.close()
        report['checks'].append('slow_search_superseded_without_stale_results')

        standalone = await context.new_page()
        standalone_requests = []
        standalone.on('request', lambda request: standalone_requests.append(request.url))
        await standalone.goto((fixture['site'] / 'standalone.html').as_uri(),
                              wait_until='domcontentloaded', timeout=timeout)
        await wait_results(standalone, identifiers[:25], timeout)
        await standalone.locator('#query').fill('TESTprimaryanchor')
        await wait_results(standalone, [identifiers[7]], timeout)
        require(not any(urlsplit(url).scheme in ('http', 'https') for url in standalone_requests),
                'Standalone file must perform no HTTP fetches')
        await standalone.close()
        report['checks'].append('standalone_file_offline_startup_and_search')
        require(not errors, 'Browser page errors: ' + '; '.join(errors[:3]))
    finally:
        await context.close()


def checked_reader_part(directory, descriptor):
    raw = build_reader.local(directory, descriptor['path']).read_bytes()
    require(len(raw) == descriptor['bytes'] and hashlib.sha256(raw).hexdigest() == descriptor['sha256'],
            'Browser-check input part checksum mismatch: ' + descriptor['path'])
    plain = gzip.decompress(raw)
    require(len(plain) == descriptor['uncompressed_bytes'],
            'Browser-check input decoded length mismatch: ' + descriptor['path'])
    return plain


def directory_rows(directory, manifest):
    """Stream compact metadata only; do not hydrate the whole source corpus."""
    count, checksum = 0, hashlib.sha256()
    for part in manifest['directory']['shards']:
        plain = checked_reader_part(directory, part)
        checksum.update(plain)
        for line in plain.splitlines():
            yield count, json.loads(line)
            count += 1
    require(count == manifest['record_count'] and checksum.hexdigest() == manifest['directory']['jsonl_sha256'],
            'Browser-check directory count/hash mismatch')


def bounded_group_records(directory, manifest, rows):
    """Read only detail parts intersecting the selected source group."""
    require(sum(row['_reader']['detail'][1] for row in rows.values()) <= 8 * 1024 * 1024,
            'Actual browser group sample exceeds the bounded8MiB detail budget')
    size, cache, result = manifest['details']['plain_part_bytes'], {}, {}
    for identifier, row in rows.items():
        offset, length = row['_reader']['detail']
        pieces = []
        for index in range(offset // size, (offset + length - 1) // size + 1):
            if index not in cache:
                cache[index] = checked_reader_part(directory, manifest['details']['shards'][index])
            start, end = max(offset - index * size, 0), min(offset + length - index * size, len(cache[index]))
            pieces.append(cache[index][start:end])
        raw = b''.join(pieces)
        require(len(raw) == length, 'Selected source group detail is truncated')
        record = json.loads(raw.decode('utf-8', errors='strict'))
        require(all(record.get(key) == row[key] for key in ('id', 'language', 'book_key', 'edition', 'source_id')),
                'Selected source group detail identity mismatch')
        result[identifier] = record
    return result


def actual_group_plan(directory, manifest, snapshot):
    definition = snapshot.get('reader_groups')
    if not definition or not definition.get('groups'):
        return None
    require(definition.get('source_occurrence_count') == manifest['record_count'],
            'Actual source/group counts disagree')
    groups = definition['groups']
    wanted = {member for group in groups for member in group['member_ids']}
    rows = {row['id']: row for _, row in directory_rows(directory, manifest) if row['id'] in wanted}
    require(set(rows) == wanted, 'Actual grouping member is missing from the directory')
    candidates = [(group, member) for group in groups if len(group['member_ids']) <= 8
                  for member in group['member_ids'][1:]]
    require(candidates, 'Actual grouping has no bounded source-version sample')
    group, member = next(((group, member) for group, member in candidates
                          if rows[member]['_reader']['origin'] == 'ai'), candidates[0])
    chosen = {identifier: rows[identifier] for identifier in group['member_ids']}
    return {'group': group, 'member': member, 'rows': rows,
            'records': bounded_group_records(directory, manifest, chosen)}


def grouped_filter_preview(directory, manifest, groups, rows, predicate):
    anchor_for = {member: group['anchor_id'] for group in groups for member in group['member_ids']}
    seen, first, occurrences = set(), [], 0
    for _, row in directory_rows(directory, manifest):
        if not predicate(row):
            continue
        occurrences += 1
        anchor = anchor_for.get(row['id'], row['id'])
        if anchor in seen:
            continue
        seen.add(anchor)
        representative = anchor if anchor in rows and predicate(rows[anchor]) else row['id']
        if len(first) < 25:
            first.append(representative)
    return {'first_page': first, 'reading_cards': len(seen), 'source_occurrences': occurrences}


async def actual_group_checks(page, directory, manifest, snapshot, base, timeout, report):
    plan = actual_group_plan(directory, manifest, snapshot)
    if plan is None:
        report['actual_site']['grouping'] = {'status': 'not_applicable', 'groups': 0}
        return
    member, group, rows = plan['member'], plan['group'], plan['rows']
    selected, groups = rows[member], snapshot['reader_groups']['groups']
    require((await page.locator('#total-count').text_content()).replace(',', '') == str(manifest['record_count']),
            'Actual reader must retain its complete source-occurrence count')
    require(str(snapshot['reader_groups']['grouped_reading_count']) ==
            (await page.locator('#reader-group-count').text_content()).split(' reading cards')[0].replace(',', ''),
            'Actual reader must display its separate grouped reading count')
    cases = [
        ('source', {'source': selected['source_id']}, lambda row: row['source_id'] == selected['source_id']),
        ('book', {'book': selected['book_key']}, lambda row: row['book_key'] == selected['book_key']),
        ('language', {'source': selected['source_id'], 'language': selected['language']},
         lambda row: row['source_id'] == selected['source_id'] and selected['language'] in row['_reader']['languages']),
        ('origin', {'source': selected['source_id'], 'origin': selected['_reader']['origin']},
         lambda row: row['source_id'] == selected['source_id'] and row['_reader']['origin'] == selected['_reader']['origin']),
    ]
    filters = {}
    for name, selection, predicate in cases:
        await page.locator('#reset').click()
        for field in ('language', 'book', 'source', 'origin'):
            if field in selection:
                await page.locator('#' + field + '-filter').select_option(selection[field])
        expected = grouped_filter_preview(directory, manifest, groups, rows, predicate)
        await wait_results(page, expected['first_page'], timeout)
        counts = (await page.locator('#result-count').text_content()).replace(',', '')
        require(str(expected['reading_cards']) + ' matching reading cards' in counts and
                str(expected['source_occurrences']) + ' matching source occurrences' in counts,
                'Actual grouped filter counts differ: ' + name)
        filters[name] = {key: value for key, value in expected.items() if key != 'first_page'}
    report['checks'].append('actual_group_source_book_language_origin_filters_keep_matching_representatives')

    await page.goto(base + 'index.html?' + urlencode({'occurrence': member}),
                    wait_until='domcontentloaded', timeout=timeout)
    await wait_results(page, [member], timeout)
    card = page.locator('#results > .record-card')
    require(await card.get_attribute('data-group-id') == group['anchor_id'],
            'Actual new occurrence deep link lost its existing group identity')
    if selected['_reader']['origin'] == 'ai':
        require(await card.locator(':scope > .language-readings .reading-origin.ai').count() > 0,
                'Actual AI source representative lacks its own AI translation badge')
    comparison = next(item for item in group['comparisons'] if item['source_occurrence_id'] == member)
    await card.locator(':scope > .source-comparison > summary').click()
    evidence = await card.locator(':scope > .source-comparison').inner_text()
    require(comparison['review']['evidence'] in evidence and
            all(value in evidence for value in comparison['review'].get('qualifications', [])),
            'Actual source-comparison evidence or qualifications changed')
    require(member in evidence and group['anchor_id'] in evidence and
            ('Yes' if comparison['review']['human_review'] else 'No') in evidence,
            'Actual source-comparison identities or human-review status absent')
    await card.locator(':scope > .source-versions > summary').click()
    panels = [card, *await card.locator('.source-version').all()]
    require(len(panels) == len(group['member_ids']), 'Actual grouped source panels are incomplete')
    from language_display import language_readings
    for panel in panels:
        identifier = await panel.get_attribute('data-occurrence-id')
        original = plan['records'][identifier]
        visible = await panel.locator(':scope > .language-readings p.narration').all_text_contents()
        for reading in language_readings(original):
            if not reading.get('text'):
                continue
            for part in reading.get('quotation_parts') or [{'text': reading['text']}]:
                for passage in part.get('passages') or [part]:
                    require(passage['text'] in visible, 'Actual source-version quotation bytes changed: ' + identifier)
        # The parent has a nested other-source disclosure; restrict by its direct summary.
        audit = panel.locator(':scope > details').filter(
            has=page.locator(':scope > summary', has_text=re.compile(r'^Record details & provenance$')))
        require(await audit.count() == 1, 'Expected one direct audit for each grouped source')
        await audit.locator(':scope > summary').click()
        await audit.locator('pre.audit-text').wait_for(state='attached', timeout=timeout)
        require(json.loads(await audit.locator('pre.audit-text').text_content()) == original,
                'Actual grouped audit lost source text, footnotes, provenance or locators')
    report['checks'].append('actual_new_ID_group_shows_qualified_comparison_and_exact_other_source_text')
    report['checks'].append('actual_group_source_audits_preserve_complete_original_objects')
    await card.locator(':scope > .card-top .record-select input').check()
    async with page.expect_download(timeout=timeout) as event:
        await page.locator('#download').click()
    download = await event.value
    with tempfile.TemporaryDirectory(prefix='hadith-group-export-') as temporary:
        target = Path(temporary) / 'selected.json'
        await download.save_as(str(target))
        exported = json.loads(target.read_text(encoding='utf-8'))
        require(len(exported) == len(group['member_ids']) and
                {record['id'] for record in exported} == set(group['member_ids']) and
                all(record == plan['records'][record['id']] for record in exported),
                'Actual grouped JSON export changed or omitted a distinct source occurrence')
        export_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    report['checks'].append('actual_group_selection_exports_all_exact_member_records')
    report['actual_site']['grouping'] = {
        'status': 'passed', 'groups': len(groups),
        'grouped_reading_count': snapshot['reader_groups']['grouped_reading_count'],
        'sample_member': member, 'sample_anchor': group['anchor_id'],
        'sample_origin': selected['_reader']['origin'], 'sample_relation': comparison['relation'],
        'source_member_count': len(group['member_ids']), 'filters': filters,
        'selected_json_sha256': export_hash,
        'detail_scope': 'Only the selected group, up to8 records and8MiB; other checks stream compact directory metadata.',
    }


async def actual_site_checks(browser, directory, timeout, report):
    document = (directory / 'index.html').read_text(encoding='utf-8')
    manifest = script_payload(document, 'hadith-records')
    snapshot = script_payload(document, 'hadith-snapshot')
    require(manifest.get('schema') == 'hadith-bank-reader-lazy-v2', 'Actual site must use lazy v2')
    require(manifest['record_count'] == snapshot['record_count'] > 0, 'Actual site count must match snapshot')
    with local_server(directory) as base:
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        requests, errors = [], []
        page.on('request', lambda request: requests.append(urlsplit(request.url).path.lstrip('/')))
        page.on('pageerror', lambda error: errors.append(str(error)[:500]))
        try:
            await page.goto(base + 'index.html', wait_until='domcontentloaded', timeout=timeout)
            reading_count = (snapshot.get('reader_groups') or {}).get('grouped_reading_count', manifest['record_count'])
            wanted = min(25, reading_count)
            await page.wait_for_function(
                """count => document.getElementById("results")?.getAttribute("aria-busy")==="false" &&
                  !document.querySelector("#results .error") &&
                  document.querySelectorAll("#results > .record-card").length===count""",
                arg=wanted, timeout=timeout)
            ids = await card_ids(page)
            all_detail_paths = {item['path'] for item in manifest['details']['shards']}
            detail_requests = set(requests) & all_detail_paths
            require(not any(path in {part['path'] for name in ('search', 'annotations')
                                     for part in manifest[name]['shards']} for path in requests),
                    'Actual empty-query startup must not load text-search stores')
            if manifest['record_count'] > 25 and len(all_detail_paths) > 1:
                require(len(detail_requests) < len(all_detail_paths), 'Actual startup eagerly fetched all details')
            await page.goto(base + 'index.html?' + urlencode({'occurrence': ids[0]}),
                            wait_until='domcontentloaded', timeout=timeout)
            await wait_results(page, [ids[0]], timeout)
            report['actual_site'] = {'record_count': manifest['record_count'],
                                     'grouped_reading_count': reading_count,
                                     'initial_cards': wanted, 'exact_occurrence_verified': ids[0],
                                     'startup_detail_parts_requested': len(detail_requests),
                                     'detail_parts_total': len(all_detail_paths)}
            report['checks'].append('actual_site_startup_and_exact_deep_link')
            await actual_group_checks(page, directory, manifest, snapshot, base, timeout, report)
            require(not errors, 'Actual site page errors: ' + '; '.join(errors[:3]))
        finally:
            await context.close()


async def run_browser(args, fixture, report):
    from playwright.async_api import async_playwright
    with local_server(fixture['site']) as base:
        async with async_playwright() as playwright:
            launch = {'headless': True}
            if args.chromium_executable:
                launch['executable_path'] = str(args.chromium_executable.resolve())
            browser = await playwright.chromium.launch(**launch)
            try:
                report['browser'] = browser.version
                await fixture_browser_checks(browser, fixture, base, args.timeout_ms, report)
                if args.site_root:
                    await actual_site_checks(browser, args.site_root.resolve(), args.timeout_ms, report)
            finally:
                await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-only', action='store_true',
                        help='Generate and structurally check fixtures without browser or server startup.')
    parser.add_argument('--chromium-executable', type=Path,
                        help='Existing Chromium executable in an environment permitting browser startup.')
    parser.add_argument('--site-root', type=Path, help='Also smoke-check an actual built site directory.')
    parser.add_argument('--timeout-ms', type=int, default=60000)
    parser.add_argument('--report', type=Path, help='Optional compact JSON result file.')
    args = parser.parse_args()
    if not 1000 <= args.timeout_ms <= 180000:
        parser.error('--timeout-ms must be between 1000 and 180000')
    report = {'schema': 'hadith-bank-reader-browser-smoke-v1', 'status': 'running', 'checks': []}
    started = time.monotonic()
    exit_code = 0
    try:
        with tempfile.TemporaryDirectory(prefix='hadith-reader-browser-') as temporary:
            fixture = build_fixture(Path(temporary))
            report['fixture'] = {'record_count': len(fixture['records']),
                                 'encoding': fixture['manifest']['encoding'],
                                 'detail_parts': len(fixture['manifest']['details']['shards']),
                                 'detail_bytes': fixture['build']['reader_store_metrics']['details']['uncompressed_bytes'],
                                 'canonical_bytes_match_reader_bytes':
                                     fixture['build']['records_sha256'] == fixture['manifest']['jsonl_sha256']}
            if args.build_only:
                report['status'] = 'fixture_build_passed_browser_not_run'
            else:
                asyncio.run(run_browser(args, fixture, report))
                report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = type(error).__name__ + ': ' + str(error)[:2000]
        exit_code = 1
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    output = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding='utf-8')
    print(output, end='')
    return exit_code


if __name__ == '__main__':
    sys.exit(main())

