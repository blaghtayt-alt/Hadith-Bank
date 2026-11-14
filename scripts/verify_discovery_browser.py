#!/usr/bin/env python3
"""Real browser checks for discovery journeys using labelled TEST source fixtures.

These records are technical test material, never religious quotations or Bank
intake. The script checks source-preserving presentation, not source authenticity.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
import traceback
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

import build_reader
from bank_discovery import expand_discovery_payload
from verify_reader_browser import (require, local_server, wait_home, run_search,
                                   wait_results, open_record, wait_workspace,
                                   lazy_audit, discovery_payload, script_payload)


def records_fixture():
    def row(identifier, language, book, number, text, arabic=None):
        return {
            'id': identifier, 'language': language, 'source_language_code': language,
            'book_key': book, 'edition': 'TEST source edition', 'source_id': identifier + '-source',
            'title': 'TEST software fixture, not a religious quotation',
            'text_translation': text, 'text_arabic': arabic,
            'number': {'in_book': number, 'canonical': None},
            'source': {'name': 'TEST Publisher', 'url': 'https://example.org/TEST-source'},
            'translator': {'name': None}, 'narrator': {'name': None},
            'translation_provenance': {'origin': 'unknown', 'ai_translation': 'unknown',
                                       'basis': 'TEST software fixture'},
            'references': {}, 'review': {'status': 'TEST fixture; no religious review'},
            'source_headings': [], 'topic_tags': [], 'editorial_tags': [], 'footnotes': [],
            'unknown_original_field': {'null': None, 'false': False, 'zero': 0,
                                       'unicode': 'TEST 🌿 漢字 أ ۱۲۳',
                                       'payload': ('TEST opaque ' + identifier + ' ') * 6000},
        }
    arabic = 'TEST أَعْمَال نِيَّات — TEST technical words only.'
    rows = [
        row('TEST-provider-ja', 'ja', 'hadeethenc', 100, 'TEST 日本語の技術資料。宗教の引用ではありません。', arabic),
        row('TEST-provider-en', 'en', 'hadeethenc', 100,
            'TEST actions depend on intentions. TEST software fixture, not a religious quotation.', arabic),
        row('TEST-provider-variant', 'en', 'hadeethenc', 100,
            'TEST actions depend on intentions. TEST different source version.', arabic + ' TEST variant'),
        row('TEST-local-number', 'en', 'bukhari', 1, 'TEST source-local number collision.'),
        row('TEST-facets', 'en', 'bukhari', 12, ('TEST prefix material ' * 30) +
            ' TESTdeepword TEST final technical text. TEST vocabulary: angry, mother, prayer.'),
        row('TEST-external-en', 'ja', 'unknown', 5, 'TESTexternalonly 英語は外部リンクだけです。'),
        row('TEST-missing-en', 'ja', 'unknown', 6, 'TESTmissingonly 英語は保存されていません。'),
        row('TEST-chunk-001', 'en', 'bukhari', 20, 'TEST first chunk source text.'),
        row('TEST-chunk-002', 'en', 'bukhari', 21, 'TEST second chunk source text.'),
        row('TEST-shared-id', 'en', 'bukhari', 39, 'TEST ambiguous identity source A.'),
        row('TEST-shared-id', 'en', 'bukhari', 40, 'TEST ambiguous identity source B.'),
    ]
    for item in rows[:3]:
        item['provider_entry_id'] = '100'
        item['source']['record_url'] = 'https://hadeethenc.com/' + item['language'] + '/browse/hadith/100'
        item['references'] = {'items': [{'book_key': 'bukhari', 'number': '1', 'scope': 'narration'}]}
    rows[3]['number']['numbering_system'] = 'provider_entry'
    rows[3]['number']['sequence_is_hadith_number'] = False
    rows[4].update(narrator={'name': 'TEST Narrator'}, source_headings=['TEST Book', 'TEST Chapter'],
                   report_type='companion_report', grading={'grade': 'TEST Grade', 'grader': 'TEST Authority'},
                   topic_tags=[{'id': 'TEST-source-category', 'label': 'TEST Supplied Category',
                                'path': ['TEST Source Taxonomy']}])
    rows[8]['source_headings'] = ['TEST Other Book', 'TEST Other Chapter']
    for index in (4, 8):
        rows[index]['source_structure_tags'] = [
            {'origin': 'source_book_structure', 'source_id': rows[index]['source_id'],
             'hierarchy': hierarchy, 'value_verbatim': heading,
             'source_locator': {'path': 'TEST-source.txt', 'paragraph': hierarchy}}
            for hierarchy, heading in enumerate(rows[index]['source_headings'], 1)
        ]
    rows[5]['counterparts'] = {'english': {'text': None, 'scope': 'external_source',
                                         'source_name': 'TEST Link Publisher',
                                         'source_url': 'https://example.org/TEST-external-English'}}
    rows[6]['grading'] = {'grade': 'TEST Unattributed Assessment'}
    for item in rows[7:9]:
        item['edition'] = 'snapshot-aabbccddeeff-part-' + ('001' if item is rows[7] else '002')
        item['source'].update(name='TEST Single Published Edition', original_file='TEST/original.json', sha256='a' * 64)
    rows[9].update(source_id='TEST-shared-A', edition='TEST edition A')
    rows[10].update(source_id='TEST-shared-B', edition='TEST edition B')
    return rows


def build_fixture(root):
    source, site = root / 'source', root / 'site'
    (source / 'catalog').mkdir(parents=True)
    (source / 'search').mkdir()
    site.mkdir()
    records = records_fixture()
    raw = b''.join((json.dumps(row, ensure_ascii=False) + '\n').encode() for row in records)
    source_file = source / 'search/records.jsonl'
    source_file.write_bytes(raw)
    source_hash = hashlib.sha256(raw).hexdigest()
    (source / 'catalog/materials.json').write_text(json.dumps({
        'title': 'TEST discovery browser fixture', 'materials': [],
        'search': {'records_path': 'search/records.jsonl', 'count': len(records), 'records_sha256': source_hash},
    }))
    build_reader.build(source, site / 'index.html', data_directory=site / 'data', max_shard_bytes=65536)
    build_reader.build(source, site / 'standalone.html')
    require(source_file.read_bytes() == raw, 'Reader generation changed the canonical TEST source bytes')
    document = (site / 'index.html').read_text()
    snapshot = script_payload(document, 'hadith-snapshot')
    payload = discovery_payload(site, snapshot)
    require(len(payload['rows']) == len(records), 'Discovery dropped source occurrences')
    require(payload['rows'][0]['groupId'] == payload['rows'][1]['groupId'] is not None,
            'Same explicit provider and exact source Arabic fixture should share a presentation family')
    require(payload['rows'][2]['groupId'] != payload['rows'][0]['groupId'],
            'Differing source Arabic must not be collapsed into the same family')
    require(payload['rows'][7]['editionGroup'] == payload['rows'][8]['editionGroup'],
            'Identical source-file binding should group only technical chunks of that edition')
    require(not any('Unattributed' in item['label'] for item in payload['facets']['grade']),
            'A grade without a named authority must not be an authority-backed facet')
    require(payload['rows'][4]['sourcePath'] == ['TEST Book', 'TEST Chapter'] and
            payload['rows'][4]['sourceHierarchyBasis'] == 'source_structure_tags',
            'Source book/chapter navigation must preserve its evidenced hierarchy')
    return {'site': site, 'records': records, 'payload': payload, 'snapshot': snapshot,
            'source_sha256': source_hash}


async def result_rows(page):
    return await page.locator('#results > .compact-result').evaluate_all("""nodes => nodes.map(node=>({
      id:node.dataset.occurrenceId, familySize:Number(node.dataset.familySize),
      excerpt:node.querySelector('.result-excerpt')?.textContent,
      language:node.querySelector('.result-excerpt')?.getAttribute('lang'),
      availability:node.querySelector('.compact-availability')?.textContent
    }))""")


async def ready(page, timeout):
    await page.wait_for_function("""() => document.getElementById('results')?.getAttribute('aria-busy')==='false'
      && !document.querySelector('#results .error')""", timeout=timeout)


def observe_failures(page):
    """Keep only bounded diagnostics; do not copy quotation/source bodies."""
    evidence = {'page_errors': [], 'request_failures': [], 'http_errors': [], 'recent_requests': []}

    def add(key, value):
        evidence[key].append(value)
        del evidence[key][:-40]

    page.on('pageerror', lambda error: add('page_errors', str(error)[:1200]))
    page.on('request', lambda request: add('recent_requests', urlsplit(request.url).path))
    page.on('requestfailed', lambda request: add('request_failures',
            {'path': urlsplit(request.url).path, 'error': str(request.failure)[:600]}))
    page.on('response', lambda response: add('http_errors',
            {'path': urlsplit(response.url).path, 'status': response.status}) if response.status >= 400 else None)
    return evidence


async def capture_failure(page, args, report, label, evidence):
    diagnostic = {'label': label, 'step': report.get('current_step'), **evidence}
    report.setdefault('failure_diagnostics', []).append(diagnostic)
    try:
        diagnostic['page'] = await asyncio.wait_for(page.evaluate("""() => ({
          url:location.href, view:document.body.dataset.discoveryView,
          query:document.getElementById('query')?.value,
          mode:document.querySelector('[name="search-mode"]:checked')?.value,
          result_count:document.getElementById('result-count')?.textContent,
          results_busy:document.getElementById('results')?.getAttribute('aria-busy'),
          result_ids:[...document.querySelectorAll('#results > .compact-result')].slice(0,10)
            .map(node=>({id:node.dataset.occurrenceId,source:node.dataset.sourceId,edition:node.dataset.edition})),
          workspace_hidden:document.getElementById('narration-workspace')?.hidden,
          workspace_busy:document.getElementById('workspace-content')?.getAttribute('aria-busy'),
          workspace_status:document.getElementById('workspace-status')?.textContent,
          workspace_version:document.getElementById('workspace-version')?.value,
          workspace_ids:[...document.querySelectorAll('#workspace-content .record-card,#workspace-content .source-version')]
            .slice(0,12).map(node=>node.dataset.occurrenceId),
          comparison_busy:document.getElementById('workspace-comparison-content')?.getAttribute('aria-busy'),
          errors:[...document.querySelectorAll('.error')].slice(0,8).map(node=>node.textContent.slice(0,1600)),
          focused:{tag:document.activeElement?.tagName,id:document.activeElement?.id,
            name:document.activeElement?.getAttribute('aria-label')}
        })"""), timeout=10)
    except Exception as error:
        diagnostic['state_capture_error'] = type(error).__name__ + ': ' + str(error)[:600]
    try:
        path = args.evidence_dir / (label + '-failure.png')
        await page.screenshot(path=str(path), timeout=10000)
        diagnostic['screenshot'] = str(path)
    except Exception as error:
        diagnostic['screenshot_error'] = type(error).__name__ + ': ' + str(error)[:600]


async def desktop_checks(browser, fixture, base, args, report):
    context = await browser.new_context(viewport={'width': 1366, 'height': 900}, accept_downloads=True, locale='en-US')
    page = await context.new_page()
    errors, requests = [], []
    page.on('pageerror', lambda error: errors.append(str(error)[:500]))
    page.on('request', lambda request: requests.append(urlsplit(request.url).path))
    evidence = observe_failures(page)
    try:
        report['current_step'] = 'desktop.home'
        await page.goto(base, wait_until='domcontentloaded', timeout=args.timeout_ms)
        await wait_home(page, args.timeout_ms)
        require(await page.locator('body').get_attribute('data-discovery-view') == 'home',
                'Home must retain its full discovery view')
        home_hero = await page.locator('.hero').bounding_box()
        require(home_hero and home_hero['height'] > 1, 'Home must retain its visible introduction')
        require(not any('/details/' in path for path in requests), 'Home must not request details')
        await page.keyboard.press('Control+k')
        require(await page.locator('#query').evaluate('(node)=>document.activeElement===node'),
                'Keyboard search shortcut must focus the labelled query')
        require(await page.get_by_role('searchbox', name='Find a narration').count() == 1,
                'Search input needs a meaningful accessible name')
        require(await page.locator('#result-count').get_attribute('aria-live') == 'polite',
                'Results must announce changes politely')
        await page.screenshot(path=str(args.evidence_dir / 'discovery-desktop-home.png'))
        report['checks'].append('desktop_search_home_keyboard_shortcut_and_live_region_semantics')

        await run_search(page, 'Bukhari 1', args.timeout_ms)
        await ready(page, args.timeout_ms)
        require(len(await result_rows(page)) == 2,
                'An unambiguous collection reference must work in the default search field')
        require(await page.locator('.recognized-reference').count() == 1,
                'Automatically recognized references must be explained visibly')
        report['checks'].append('default_search_field_recognizes_unambiguous_exact_reference')
        await run_search(page, 'Bukhari 1', args.timeout_ms, 'reference')
        await ready(page, args.timeout_ms)
        results = await result_rows(page)
        require(len(results) == 2 and sorted(item['familySize'] for item in results) == [1, 2],
                'Exact reference must group evidence-bound translations but preserve the differing version')
        require('TEST-local-number' not in {item['id'] for item in results},
                'Provider-local number must not become a canonical reference')
        require(not any('/details/' in path for path in requests), 'Compact results must not request details')
        await page.locator('#preferred-language').select_option('ja')
        await ready(page, args.timeout_ms)
        results = await result_rows(page)
        selected = next(item for item in results if item['familySize'] == 2)
        require(selected['id'] == 'TEST-provider-ja' and selected['language'] == 'ja',
                'Preferred language must select the matching stored source reading')
        require(selected['excerpt'] in fixture['records'][0]['text_translation'],
                'Preferred excerpt must be exact source text')
        await page.evaluate('window.scrollTo(0,0)')
        result_box = await page.locator('#results > .compact-result').first.bounding_box()
        result_hero = await page.locator('.hero').bounding_box()
        require(await page.locator('body').get_attribute('data-discovery-view') == 'results' and
                result_hero and result_hero['height'] <= 1,
                'Compact results must use the compact screen introduction')
        require(result_box and 0 <= result_box['y'] < 600,
                'The first desktop result must occupy a useful part of the initial viewport')
        await page.screenshot(path=str(args.evidence_dir / 'discovery-desktop-results.png'))
        report['checks'].append('reference_number_collision_evidence_family_and_multilingual_preference')

        # Open the explicit preferred-language result by its stable source ID.
        report['current_step'] = 'desktop.open_preferred_family_TEST-provider-ja'
        await open_record(page, 'TEST-provider-ja', args.timeout_ms)
        require(await page.locator('body').get_attribute('data-discovery-view') == 'workspace',
                'Opening a narration must switch to the workspace view')
        require(await page.locator('#workspace-version option').count() == 2,
                'Family workspace must enumerate both preserved versions')
        require(await page.locator('#workspace-content > .record-card').count() == 1,
                'Workspace must hydrate one selected version at a time')
        require(await page.locator('#workspace-evidence').count() == 1,
                'Family workspace must explain the grouping evidence')
        report['current_step'] = 'desktop.grouping_evidence'
        await page.locator('#workspace-evidence > summary').click()
        group_evidence = json.loads(await page.locator('#workspace-evidence pre').text_content())
        require(group_evidence['basis'] == 'accepted_provider_identity_and_source_binding',
                'Grouping must retain its actual source evidence basis')
        require(all(item.get('providerId') == '100' and item.get('arabicSha256')
                    for item in group_evidence['memberRelations']),
                'Provider identity evidence must bind the exact source Arabic')
        report['current_step'] = 'desktop.audit_TEST-provider-ja'
        await lazy_audit(page, fixture['records'][0], args.timeout_ms)
        report['current_step'] = 'desktop.switch_source_TEST-provider-en'
        await page.locator('#workspace-version').select_option('1')
        await wait_workspace(page, 'TEST-provider-en', args.timeout_ms)
        report['current_step'] = 'desktop.audit_TEST-provider-en'
        await lazy_audit(page, fixture['records'][1], args.timeout_ms)
        arabic = page.locator('#workspace-content .language-reading[data-language="ar"] p.narration')
        require(await arabic.text_content() == fixture['records'][1]['text_arabic'],
                'Workspace Arabic must match exact source bytes')
        require(await arabic.evaluate('(node)=>getComputedStyle(node).direction') == 'rtl',
                'Arabic source reading must use RTL layout')
        require(await page.locator('#workspace-content .reading-source').first.get_attribute('href') ==
                fixture['records'][1]['source']['record_url'], 'Source link must preserve its own locator')
        require(await page.locator('#workspace-comparison-content .source-version').count() == 0,
                'Comparison must remain empty until a second source is explicitly chosen')
        report['current_step'] = 'desktop.compare_source_TEST-provider-ja'
        await page.locator('#compare-source-version').select_option('0')
        await page.wait_for_function("""() => {
          const content=document.getElementById('workspace-comparison-content');
          return content?.getAttribute('aria-busy')==='false' &&
            content.querySelector('.source-version')?.dataset.occurrenceId==='TEST-provider-ja';
        }""", timeout=args.timeout_ms)
        comparison = page.locator('#workspace-comparison-content')
        require(fixture['records'][0]['text_translation'] in await comparison.inner_text(),
                'On-demand comparison must show its separate exact source reading')
        require(await page.locator('#workspace-content > .record-card').get_attribute('data-occurrence-id') ==
                'TEST-provider-en', 'Comparing another source must retain the selected primary version')
        await page.locator('#text-size').select_option('large')
        require(await page.locator('body').get_attribute('data-text-size') == 'large',
                'Reading text-size control must still work in workspace')
        await page.screenshot(path=str(args.evidence_dir / 'discovery-desktop-workspace.png'))
        report['checks'].append('workspace_lazy_source_versions_comparison_evidence_exact_bytes_source_links_and_RTL')

        report['current_step'] = 'desktop.return_home_and_wording_journeys'
        await page.locator('#back-to-results').click()
        await page.locator('#reset').click()
        await wait_home(page, args.timeout_ms)
        restored_hero = await page.locator('.hero').bounding_box()
        require(await page.locator('body').get_attribute('data-discovery-view') == 'home' and
                restored_hero and restored_hero['height'] > 1,
                'Resetting to home must restore the introduction')
        await run_search(page, '"actions depend on intentions"', args.timeout_ms, 'wording')
        await ready(page, args.timeout_ms)
        require(len(await result_rows(page)) == 2, 'Quoted wording must search exact phrase positions')
        family = page.locator('#results > .compact-result[data-occurrence-id="TEST-provider-ja"]')
        require(await family.locator(':scope > .result-excerpt').get_attribute('lang') == 'ja',
                'A matched family must retain the preferred-language preview')
        await family.locator('.show-matching-wording').click()
        matching = family.locator('.matching-wording')
        await matching.wait_for(state='visible', timeout=args.timeout_ms)
        passage = await matching.locator('.result-excerpt').text_content()
        require('actions depend on intentions' in passage and
                passage in fixture['records'][1]['text_translation'],
                'Cross-language matching passage must be an exact substring of its own matched source')
        require(await matching.locator('.reading-source').get_attribute('href') ==
                fixture['records'][1]['source']['record_url'],
                'Matched wording must cite the English source that supplied it')
        require(await family.locator(':scope > .result-excerpt').get_attribute('lang') == 'ja',
                'Opening matching English wording must preserve the Japanese preview')
        report['checks'].append('preferred_family_preview_and_matched_other_language_keep_separate_exact_sources')
        await run_search(page, 'actions performed intentions', args.timeout_ms, 'wording')
        await ready(page, args.timeout_ms)
        require(len(await result_rows(page)) == 2,
                'Remembered wording without an all-word result must expose actual broader quotation matches')
        broader = page.locator('#search-suggestions .broader-wording-note')
        require(await broader.count() == 1 and 'Broader wording matches' in await broader.inner_text(),
                'Relaxed all-word matching must be explained before its results')
        matched_terms = await page.locator('#results .broader-wording-terms').all_text_contents()
        require(len(matched_terms) == 2 and all('actions' in text and 'intentions' in text and
                                               'performed' in text for text in matched_terms),
                'Each broader result must distinguish stored matching words from missing query words')
        await run_search(page, '"actions performed intentions"', args.timeout_ms, 'wording')
        await wait_results(page, [], args.timeout_ms)
        require(await page.locator('#search-suggestions .broader-wording-note').count() == 0,
                'Quoted phrases must remain exact and must not be silently broadened')
        report['checks'].append('remembered_wording_broadens_transparently_only_when_unquoted_all_word_matches_are_absent')
        await run_search(page, 'اعمال', args.timeout_ms, 'wording')
        await ready(page, args.timeout_ms)
        plain_ids = [item['id'] for item in await result_rows(page)]
        await run_search(page, 'أَعْمَال', args.timeout_ms, 'wording')
        await ready(page, args.timeout_ms)
        require(plain_ids == [item['id'] for item in await result_rows(page)],
                'Safe Arabic search normalization must not change matching identities')
        await run_search(page, 'TESTabsentZQX', args.timeout_ms)
        await wait_results(page, [], args.timeout_ms)
        require(await page.get_by_role('heading', name='No matching narrations').count() == 1,
                'Completed no-result state must be explicit')
        report['checks'].append('phrase_Arabic_normalization_and_completed_no_results')

        report['current_step'] = 'desktop.topic_and_spelling_journeys'
        for topic in ('anger', 'parents', 'prayer', 'salah'):
            await run_search(page, topic, args.timeout_ms, 'topic')
            await wait_results(page, ['TEST-facets'], args.timeout_ms)
            explanation = await page.locator('#search-suggestions').inner_text()
            require('Editorial search terms:' in explanation and 'not source wording' in explanation,
                    'Broader topic and transliteration aids must explain their editorial scope')
        await run_search(page, 'testdeepwore', args.timeout_ms, 'wording')
        await wait_results(page, [], args.timeout_ms)
        require(await page.locator('#query').input_value() == 'testdeepwore',
                'Spelling assistance must not silently replace the entered query')
        await page.get_by_role('button', name='Try “testdeepword”', exact=True).click()
        await wait_results(page, ['TEST-facets'], args.timeout_ms)
        report['checks'].append('topic_synonyms_limited_transliteration_and_opt_in_spelling_are_transparent')

        report['current_step'] = 'desktop.unique_occurrence_and_back'
        await run_search(page, 'TEST-provider-variant', args.timeout_ms, 'reference')
        await wait_workspace(page, 'TEST-provider-variant', args.timeout_ms)
        await page.locator('#back-to-results').click()
        await page.locator('#narration-workspace').wait_for(state='hidden', timeout=args.timeout_ms)
        require(await page.locator('#discovery-results').is_visible(),
                'Back from a unique-ID search must return to results without reopening the workspace')
        report['checks'].append('unique_occurrence_search_back_navigation_returns_to_results')

        report['current_step'] = 'desktop.ambiguous_occurrence_and_scoped_deep_link'
        await run_search(page, 'TEST-shared-id', args.timeout_ms, 'reference')
        await wait_results(page, ['TEST-shared-id', 'TEST-shared-id'], args.timeout_ms)
        require(await page.locator('#narration-workspace').is_hidden(),
                'Ambiguous source ID must not silently open one edition')
        source_choices = await page.locator('#results .compact-source').all_text_contents()
        expected_captions = [row['editionLabel'] for row in fixture['payload']['rows'][9:11]]
        require(source_choices == expected_captions and len(set(source_choices)) == 2,
                'Ambiguous ID choices must display distinct friendly captions for the preserved editions')
        choices = page.locator('#results > .compact-result')
        for index, original in enumerate(fixture['records'][9:11]):
            choice = choices.nth(index)
            require(await choice.get_attribute('data-edition') == original['edition'] and
                    await choice.get_attribute('data-source-id') == original['source_id'],
                    'Friendly labels must retain each distinct edition and source identity')
            link = parse_qs(urlsplit(await choice.locator('.open-narration').get_attribute('href')).query)
            require(all(link.get(key) == [original[field]] for key, field in
                        [('occurrence', 'id'), ('occurrence-language', 'language'),
                         ('occurrence-collection', 'book_key'), ('occurrence-edition', 'edition'),
                         ('occurrence-source', 'source_id')]),
                    'Ambiguous source links must bind the complete preserved occurrence identity')
        await open_record(page, 'TEST-shared-id', args.timeout_ms)
        await lazy_audit(page, fixture['records'][9], args.timeout_ms)
        selected_url = page.url
        linked = await context.new_page()
        await linked.goto(selected_url, wait_until='domcontentloaded', timeout=args.timeout_ms)
        await wait_workspace(linked, 'TEST-shared-id', args.timeout_ms)
        await lazy_audit(linked, fixture['records'][9], args.timeout_ms)
        await linked.close()
        await page.locator('#back-to-results').click()
        report['checks'].append('ambiguous_occurrence_ID_preserves_edition_choices_and_bound_deep_link')

        report['current_step'] = 'desktop.source_facets'
        await page.locator('#reset').click()
        await page.locator('#book-filter').select_option('bukhari')
        await page.locator('#source-book-filter').select_option('TEST Book')
        require('TEST Other Chapter' not in await page.locator('#chapter-filter option').all_text_contents(),
                'Child chapter choices must follow their evidenced source parent')
        await page.locator('#chapter-filter').select_option('TEST Chapter')
        await wait_results(page, ['TEST-facets'], args.timeout_ms)
        await page.locator('#narrator-filter').select_option('TEST Narrator')
        await page.locator('#type-filter').select_option('companion_report')
        await page.locator('#grade-filter').select_option(label='TEST Grade — TEST Authority')
        supplied_topic = next(topic for topic in fixture['payload']['rows'][4]['topics']
                              if topic.get('sourceTopicId') == 'TEST-source-category')
        await page.locator('#source-topic-filter').select_option(supplied_topic['value'])
        await wait_results(page, ['TEST-facets'], args.timeout_ms)
        require(not any('Unattributed Assessment' in value for value in
                        await page.locator('#grade-filter option').all_text_contents()),
                'Unattributed assessment must remain outside named-authority grade facets')
        report['checks'].append('evidenced_collection_parent_chapter_source_category_narrator_type_and_named_authority_grade_facets')
        await page.locator('#reset').click()
        edition = fixture['payload']['rows'][7]['editionGroup']
        await page.locator('#source-filter').select_option(edition)
        await wait_results(page, ['TEST-chunk-001', 'TEST-chunk-002'], args.timeout_ms)
        label = await page.locator('#source-filter option:checked').text_content()
        require('aabbccddeeff' not in label and 'part-00' not in label,
                'Friendly edition labels must not expose technical chunk/hash names')
        report['checks'].append('technical_chunks_share_only_evidence_bound_friendly_edition_facet')

        report['current_step'] = 'desktop.counterpart_availability'
        await page.locator('#reset').click()
        await run_search(page, 'TESTexternalonly', args.timeout_ms)
        await wait_results(page, ['TEST-external-en'], args.timeout_ms)
        require('English: external source link' in (await result_rows(page))[0]['availability'],
                'External-only English must not be presented as stored text')
        await run_search(page, 'TESTmissingonly', args.timeout_ms)
        await wait_results(page, ['TEST-missing-en'], args.timeout_ms)
        require('English: not supplied' in (await result_rows(page))[0]['availability'],
                'Missing English must remain missing')
        await run_search(page, 'TESTdeepword', args.timeout_ms)
        await wait_results(page, ['TEST-facets'], args.timeout_ms)
        require(await page.locator('.excerpt-fallback').count() > 0 or
                'TESTdeepword' in (await result_rows(page))[0]['excerpt'],
                'A match beyond the preview must give honest location/fallback information')
        report['checks'].append('external_link_missing_text_and_beyond_preview_match_are_distinct')

        # Source data is deliberately uncached; losing connectivity must not
        # erase index results or manufacture an empty stored quotation.
        report['current_step'] = 'desktop.offline_detail_and_retry'
        await context.set_offline(True)
        await page.locator('#results .open-narration').click()
        await page.locator('#workspace-content .error').wait_for(state='visible', timeout=args.timeout_ms)
        require('offline' in (await page.locator('#workspace-content').inner_text()).lower(),
                'Offline source failure must be identified explicitly')
        await context.set_offline(False)
        await page.get_by_role('button', name='Retry this source').click()
        await wait_workspace(page, 'TEST-facets', args.timeout_ms)
        report['checks'].append('offline_missing_detail_preserves_results_and_retry_recovers_exact_source')
        report['current_step'] = 'desktop.matching_late_source_passage'
        await page.locator('#back-to-results').click()
        await wait_results(page, ['TEST-facets'], args.timeout_ms)
        await page.locator('#results .show-matching-wording').click()
        matching = page.locator('#results .matching-wording')
        await matching.wait_for(state='visible', timeout=args.timeout_ms)
        passage = await matching.locator('.result-excerpt').text_content()
        require('TESTdeepword' in passage and passage in fixture['records'][4]['text_translation'],
                'Beyond-preview matching wording must be an exact supplied passage, never synthesized')
        require(await matching.locator('.reading-source').get_attribute('href') ==
                fixture['records'][4]['source']['url'],
                'Beyond-preview passage must retain its own source link')
        report['checks'].append('beyond_preview_matching_passage_is_exact_source_text_with_own_citation')
        require(not errors, 'Browser page errors: ' + '; '.join(errors[:3]))
    except Exception:
        await capture_failure(page, args, report, 'discovery-desktop', evidence)
        raise
    finally:
        await context.close()


async def mobile_checks(browser, fixture, base, args, report, evidence_prefix='discovery-fixture'):
    context = await browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True,
                                        has_touch=True, device_scale_factor=1, locale='en-US')
    page = await context.new_page()
    evidence = observe_failures(page)
    try:
        report['current_step'] = evidence_prefix + '.mobile_home'
        response = await page.goto(base, wait_until='domcontentloaded', timeout=args.timeout_ms)
        if getattr(args, 'production_url', None):
            require(response is not None and response.status == 200,
                    'Live browser navigation must return HTTP 200')
            html = await response.body()
            snapshot = script_payload(html.decode('utf-8'), 'hadith-snapshot')
            binding = {'url': response.url, 'status': response.status,
                       'html_bytes': len(html), 'html_sha256': hashlib.sha256(html).hexdigest(),
                       'http_date': response.headers.get('date'),
                       'build_commit': (snapshot.get('site') or {}).get('build_commit')}
            report['actual_site']['browser_navigation'] = binding
            require(binding['html_sha256'] == args.expected_reader_sha256 and
                    binding['build_commit'] == args.expected_source_commit,
                    'Live browser navigation changed from the expected published revision')
        await wait_home(page, args.timeout_ms)
        require(await page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),
                'Mobile home must not have horizontal overflow')
        report['current_step'] = evidence_prefix + '.mobile_default_reference'
        await run_search(page, 'Bukhari 1', args.timeout_ms)
        await ready(page, args.timeout_ms)
        require(await page.locator('.recognized-reference').count() == 1,
                'Mobile default-field reference recognition must be visible')
        require(await page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),
                'Mobile compact results must not overflow horizontally')
        await page.screenshot(path=str(args.evidence_dir / (evidence_prefix + '-mobile-results.png')), full_page=True)
        identifier = (await result_rows(page))[0]['id']
        report['current_step'] = evidence_prefix + '.mobile_workspace_' + identifier
        await page.locator('.open-narration').first.focus()
        await page.keyboard.press('Enter')
        await wait_workspace(page, identifier, args.timeout_ms)
        require(await page.locator('#workspace-heading').evaluate('(node)=>document.activeElement===node'),
                'Opening a workspace with the keyboard must focus its heading')
        require(await page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),
                'Mobile Arabic/English workspace must not overflow horizontally')
        require(await page.locator('#workspace-content [lang="ar"] p.narration').count() or
                await page.locator('#workspace-content p.narration[lang="ar"]').count(),
                'Mobile test must actually show an Arabic source reading')
        session = await context.new_cdp_session(page)
        tree = await session.send('Accessibility.getFullAXTree')
        names = {node.get('name', {}).get('value') for node in tree['nodes'] if not node.get('ignored')}
        require('Back to results' in names or '← Back to results' in names,
                'Workspace navigation must be present in the browser accessibility tree')
        await page.screenshot(path=str(args.evidence_dir / (evidence_prefix + '-mobile-workspace.png')), full_page=True)
        await page.locator('#back-to-results').focus()
        await page.keyboard.press('Enter')
        await page.wait_for_function("""() => document.getElementById('narration-workspace')?.hidden &&
          document.activeElement.classList.contains('open-narration')""", timeout=args.timeout_ms)
        report['checks'].append(evidence_prefix.replace('-', '_') +
                                '_actual_mobile_layout_keyboard_focus_RTL_and_accessibility_tree')
        report['accessibility_scope'] = 'Actual Chromium keyboard, DOM/ARIA and accessibility-tree checks; no human screenreader session claimed.'
        if evidence_prefix == 'discovery-production':
            report['current_step'] = 'production.remembered_wording'
            await run_search(page, 'actions depend on intentions', args.timeout_ms, 'wording')
            await ready(page, args.timeout_ms)
            results = await result_rows(page)
            require(bool(results), 'The production remembered-wording journey must produce actual source results')
            broader_count = await page.locator('#results .broader-wording-terms').count()
            notice = page.locator('#search-suggestions .broader-wording-note')
            require((broader_count > 0) == (await notice.count() == 1),
                    'Production broader wording results and their explanatory notice must agree')
            count_text = await page.locator('#result-count').inner_text()
            if broader_count:
                require('Broader wording matches' in count_text,
                        'Production relaxed wording search must identify its broadened result count')
            report['actual_site']['remembered_wording'] = {
                'query': 'actions depend on intentions', 'visible_result_count': len(results),
                'count_text': count_text, 'broader_wording': bool(broader_count),
                'notice': await notice.inner_text() if await notice.count() else None,
                'first_occurrence_ids': [result['id'] for result in results[:5]],
            }
            await page.screenshot(path=str(args.evidence_dir / 'discovery-production-mobile-wording.png'),
                                  full_page=True)
            report['checks'].append('production_remembered_wording_returns_sources_with_broader_notice_when_needed')
    except Exception:
        await capture_failure(page, args, report, evidence_prefix + '-mobile', evidence)
        raise
    finally:
        await context.close()


async def transport_failure_checks(browser, fixture, base, args, report):
    """Tamper only browser responses, never the generated/source files."""
    context = await browser.new_context()
    page = await context.new_page()
    evidence = observe_failures(page)
    try:
        report['current_step'] = 'transport.corrupt_navigation_and_reload'
        descriptor = fixture['snapshot']['discovery']
        index_url = base + descriptor['path']
        corrupt = bytearray((fixture['site'] / descriptor['path']).read_bytes())
        corrupt[len(corrupt) // 2] ^= 1

        async def wrong_index(route):
            await route.fulfill(status=200, content_type='application/gzip', body=bytes(corrupt))

        await page.route(index_url, wrong_index)
        await page.goto(base, wait_until='domcontentloaded', timeout=args.timeout_ms)
        await page.locator('#results .error').wait_for(state='visible', timeout=args.timeout_ms)
        require('checksum' in (await page.locator('#results .error').inner_text()).lower(),
                'A corrupted compact index must fail its checksum check explicitly')
        require(await page.locator('#results .compact-result').count() == 0,
                'Unverified index bytes must not produce narration results')
        await page.unroute(index_url, wrong_index)
        await page.get_by_role('button', name='Reload and retry').click()
        await wait_home(page, args.timeout_ms)
        report['checks'].append('corrupt_navigation_index_rejected_and_reload_recovers_verified_home')

        report['current_step'] = 'transport.corrupt_query_part_and_retry'
        terms = fixture['payload']['terms']
        term_index = terms.index('testdeepword')
        part_index = fixture['payload']['postings'][term_index][1]
        part = fixture['payload']['postings_shards'][part_index]
        part_url = base + part['path']
        bad_postings = bytearray((fixture['site'] / part['path']).read_bytes())
        bad_postings[len(bad_postings) // 2] ^= 1

        async def wrong_postings(route):
            await route.fulfill(status=200, content_type='application/gzip', body=bytes(bad_postings))

        await page.route(part_url, wrong_postings)
        await run_search(page, 'TESTdeepword', args.timeout_ms)
        await page.locator('#results .error').wait_for(state='visible', timeout=args.timeout_ms)
        require('checksum' in (await page.locator('#results .error').inner_text()).lower(),
                'A corrupted term part must be an error, never a completed no-result search')
        require('could not be completed' in (await page.locator('#result-count').inner_text()).lower(),
                'Failed retrieval must be distinguishable from zero matches')
        await page.unroute(part_url, wrong_postings)
        await page.get_by_role('button', name='Try again', exact=True).click()
        await wait_results(page, ['TEST-facets'], args.timeout_ms)
        report['checks'].append('corrupt_query_part_rejected_without_false_zero_and_retry_recovers_results')
    except Exception:
        await capture_failure(page, args, report, 'discovery-transport', evidence)
        raise
    finally:
        await context.close()


async def verify_actual_corpus(browser, args, report):
    actual_site = args.site_root.resolve()
    html = (actual_site / 'index.html').read_bytes()
    snapshot = script_payload(html.decode('utf-8'), 'hadith-snapshot')
    report['actual_site'] = {
        'html_bytes': len(html), 'html_sha256': hashlib.sha256(html).hexdigest(),
        'snapshot_identity': {key: snapshot.get(key) for key in
            ('site', 'record_count', 'records_sha256', 'discovery')},
    }
    with local_server(actual_site) as actual_base:
        await mobile_checks(browser, None, actual_base, args, report,
                            evidence_prefix='discovery-production')


def fetch_live_bytes(url, timeout, maximum_bytes):
    """Read a bounded HTTPS response without changing the publication URL."""
    request = Request(url, headers={'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache',
                                    'User-Agent': 'Hadith-Bank-publication-verification/1'})
    with urlopen(request, timeout=timeout) as response:
        require(urlsplit(response.url).scheme == 'https', 'Live verification must remain on HTTPS')
        require(response.status == 200, 'Live verification requires HTTP 200')
        raw = response.read(maximum_bytes + 1)
        require(len(raw) <= maximum_bytes, 'Live response exceeds its allowed byte count')
        binding = {'url': response.url, 'status': response.status, 'bytes': len(raw),
                   'sha256': hashlib.sha256(raw).hexdigest(), 'http_date': response.headers.get('Date'),
                   'content_type': response.headers.get('Content-Type'),
                   'observed_at': datetime.now(timezone.utc).isoformat()}
        return raw, binding


async def wait_for_live_publication(args, report):
    deadline = time.monotonic() + 120
    evidence = {'url': args.production_url, 'expected_source_commit': args.expected_source_commit,
                'expected_reader_sha256': args.expected_reader_sha256, 'wait_limit_seconds': 120,
                'attempts': []}
    report['live_publication'] = evidence
    report['current_step'] = 'production.wait_for_expected_live_publication'
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        observation = {}
        try:
            html, binding = await asyncio.wait_for(asyncio.to_thread(
                fetch_live_bytes, args.production_url, min(15, remaining), 16 * 1024 * 1024),
                timeout=remaining)
            observation.update(binding)
            snapshot = script_payload(html.decode('utf-8'), 'hadith-snapshot')
            observation['build_commit'] = (snapshot.get('site') or {}).get('build_commit')
            observation['matches_expected_publication'] = (
                binding['sha256'] == args.expected_reader_sha256 and
                observation['build_commit'] == args.expected_source_commit)
            evidence['attempts'].append(observation)
            if observation['matches_expected_publication']:
                evidence['status'] = 'expected_html_observed'
                return html, snapshot, binding
        except Exception as error:
            observation['error'] = type(error).__name__ + ': ' + str(error)[:1000]
            evidence['attempts'].append(observation)
        remaining = deadline - time.monotonic()
        if remaining > 0:
            await asyncio.sleep(min(5, remaining))
    evidence['status'] = 'expected_html_not_observed'
    raise AssertionError('Expected live HTML SHA-256 and source commit were not both observed within 120 seconds')


def live_discovery_url(base, snapshot):
    part = snapshot.get('discovery')
    require(isinstance(part, dict), 'Live reader must bind its compact discovery index')
    require(part.get('record_count') == snapshot.get('record_count') and
            part.get('records_sha256') == snapshot.get('records_sha256') and
            re.fullmatch(r'[0-9a-f]{64}', snapshot.get('records_sha256') or '') is not None and
            type(snapshot.get('record_count')) is int and snapshot['record_count'] > 0,
            'Live compact index descriptor belongs to a different or invalid source snapshot')
    path = part.get('path')
    require(isinstance(path, str) and path and not path.startswith('/') and
            re.search(r'[\\%:?#\x00-\x1f\x7f]', path) is None and
            all(segment not in ('', '.', '..') for segment in path.split('/')),
            'Live compact index must use a safe local publication path')
    require(part.get('encoding') == 'gzip-json' and
            type(part.get('bytes')) is int and 0 < part['bytes'] <= 128 * 1024 * 1024 and
            type(part.get('uncompressed_bytes')) is int and
            0 < part['uncompressed_bytes'] <= 512 * 1024 * 1024 and
            all(re.fullmatch(r'[0-9a-f]{64}', part.get(key) or '') is not None
                for key in ('sha256', 'uncompressed_sha256')),
            'Live compact index descriptor has invalid encoding, sizes or hashes')
    return urljoin(base, path)


def validate_live_discovery(raw, snapshot):
    part = snapshot['discovery']
    require(len(raw) == part['bytes'] and hashlib.sha256(raw).hexdigest() == part['sha256'],
            'Live compact index compressed bytes/hash mismatch')
    plain = gzip.decompress(raw)
    require(len(plain) == part['uncompressed_bytes'] and
            hashlib.sha256(plain).hexdigest() == part['uncompressed_sha256'],
            'Live compact index decoded bytes/hash mismatch')
    payload = expand_discovery_payload(json.loads(plain))
    require(payload.get('schema') == part.get('schema') and
            payload.get('record_count') == snapshot['record_count'] and
            len(payload.get('rows', [])) == snapshot['record_count'] and
            payload.get('records_sha256') == snapshot['records_sha256'],
            'Live compact index payload belongs to a different source snapshot')
    digest = hashlib.sha256()
    for row in payload['rows']:
        digest.update((row['id'] + '\n').encode('utf-8'))
    require(digest.hexdigest() == payload.get('occurrence_ids_sha256'),
            'Live compact index occurrence ID sequence is inconsistent')
    return {'schema': payload['schema'], 'record_count': payload['record_count'],
            'records_sha256': payload['records_sha256'],
            'occurrence_ids_sha256': payload['occurrence_ids_sha256'],
            'uncompressed_bytes': len(plain), 'uncompressed_sha256': hashlib.sha256(plain).hexdigest()}


async def verify_live_corpus(browser, args, report):
    html, snapshot, binding = await wait_for_live_publication(args, report)
    report['actual_site'] = {
        'url': binding['url'], 'html_bytes': len(html), 'html_sha256': binding['sha256'],
        'http': binding,
        'snapshot_identity': {key: snapshot.get(key) for key in
            ('site', 'record_count', 'records_sha256', 'discovery')},
    }
    report['current_step'] = 'production.verify_live_discovery_bytes'
    index_url = live_discovery_url(binding['url'], snapshot)
    raw, index_binding = await asyncio.wait_for(asyncio.to_thread(
        fetch_live_bytes, index_url, min(30, args.timeout_ms / 1000), snapshot['discovery']['bytes']),
        timeout=args.timeout_ms / 1000)
    report['actual_site']['discovery_http'] = index_binding
    report['actual_site']['discovery_validation'] = validate_live_discovery(raw, snapshot)
    report['checks'].append('live_expected_html_commit_and_discovery_bytes_source_binding_verified')
    await mobile_checks(browser, None, args.production_url, args, report,
                        evidence_prefix='discovery-production')


async def run(args, fixture, report):
    from playwright.async_api import async_playwright
    async with async_playwright() as playwright:
        options = {'headless': True}
        if args.chromium_executable:
            options['executable_path'] = str(args.chromium_executable.resolve())
        browser = await playwright.chromium.launch(**options)
        try:
            report['browser'] = browser.version
            if not args.production_only and not args.production_url:
                with local_server(fixture['site']) as base:
                    await desktop_checks(browser, fixture, base, args, report)
                    await transport_failure_checks(browser, fixture, base, args, report)
                    await mobile_checks(browser, fixture, base, args, report)
            if args.site_root:
                await verify_actual_corpus(browser, args, report)
            if args.production_url:
                await verify_live_corpus(browser, args, report)
        finally:
            await browser.close()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--production-only', action='store_true',
                        help='Run only actual-corpus mobile/journey checks; requires --site-root.')
    parser.add_argument('--chromium-executable', type=Path)
    parser.add_argument('--site-root', type=Path,
                        help='Also check the actual built site at a mobile viewport, preserving its source/build binding.')
    parser.add_argument('--production-url', help='Verify the expected public HTTPS publication and its actual mobile journeys.')
    parser.add_argument('--expected-source-commit', help='Required 40-character source commit for --production-url.')
    parser.add_argument('--expected-reader-sha256', help='Required 64-character HTML SHA-256 for --production-url.')
    parser.add_argument('--timeout-ms', type=int, default=60000)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, default=Path('.work/discovery-browser-images'))
    args = parser.parse_args(argv)
    if args.production_url:
        url = urlsplit(args.production_url)
        if url.scheme != 'https' or not url.netloc or url.username or url.password or url.query or url.fragment:
            parser.error('--production-url must be a public HTTPS page URL without credentials, query or fragment')
        if args.site_root or args.build_only or args.production_only:
            parser.error('--production-url cannot be combined with --site-root, --build-only or --production-only')
        for field, length in (('expected_source_commit', 40), ('expected_reader_sha256', 64)):
            if not re.fullmatch(r'[0-9a-fA-F]{' + str(length) + '}', getattr(args, field) or ''):
                parser.error('--' + field.replace('_', '-') + ' must contain exactly ' + str(length) + ' hexadecimal characters')
            setattr(args, field, getattr(args, field).lower())
    elif args.expected_source_commit or args.expected_reader_sha256:
        parser.error('--expected-source-commit and --expected-reader-sha256 require --production-url')
    if args.production_only and not args.site_root:
        parser.error('--production-only requires --site-root')
    if args.production_only and args.build_only:
        parser.error('--production-only cannot be combined with --build-only')
    if args.timeout_ms <= 0:
        parser.error('--timeout-ms must be positive')
    return args


def main():
    args = parse_args()
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    scope = ('live_production' if args.production_url else 'production_only' if args.production_only else
             'fixtures_and_production' if args.site_root else 'fixtures')
    report = {'schema': 'hadith-bank-discovery-browser-v1', 'status': 'running', 'scope': scope, 'checks': []}
    started = time.monotonic()
    try:
        if args.production_only or args.production_url:
            asyncio.run(run(args, None, report))
            report['status'] = 'passed'
        else:
            with tempfile.TemporaryDirectory(prefix='hadith-discovery-browser-') as temporary:
                fixture = build_fixture(Path(temporary))
                report['fixture'] = {'record_count': len(fixture['records']),
                                     'source_sha256': fixture['source_sha256'],
                                     'occurrence_ids_sha256': fixture['payload']['occurrence_ids_sha256'],
                                     'presentation_families': fixture['payload']['statistics']['reading_families']}
                if args.build_only:
                    report['status'] = 'fixture_build_passed_browser_not_run'
                else:
                    asyncio.run(run(args, fixture, report))
                    report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = type(error).__name__ + ': ' + str(error)[:1800]
        report['traceback'] = traceback.format_exc(limit=16)[-14000:]
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] in ('passed', 'fixture_build_passed_browser_not_run') else 1


if __name__ == '__main__':
    raise SystemExit(main())
