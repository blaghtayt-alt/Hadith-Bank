"""Make every acquired provider ID reachable, without reclassifying held text.

Registered IDs link to the narration reader. Other IDs have separate, noindex
original-source pages; they never enter the narration stream or its search.
Every rendered field is checked against its immutable saved edition first.
"""
import gzip
import hashlib
import json
import math
from urllib.parse import quote

from fawaz_held_dispositions import source_view_resolution_text

from import_fawaz_bulk import (BOOKS, IMPORT, LANGUAGES, REVISION, checked_snapshot,
                              edition_metadata, entry_url, parse_edition, parse_json,
                              read_json, typed_identity)


BASE = 'source-editions/fawaz/'
PAGE_SIZE = 100
FILTER = '''<p><label for="source-language">Language</label>
<select id="source-language"><option value="">All supplied languages</option>{options}</select></p>
<script>
(()=>{{const select=document.getElementById('source-language');
const wanted=new URLSearchParams(location.search).get('language');
if([...select.options].some(option=>option.value===wanted))select.value=wanted;
const apply=()=>{{document.querySelectorAll('[data-source-languages]').forEach(item=>{{
item.hidden=!!select.value&&!item.dataset.sourceLanguages.split(',').includes(select.value);}});
document.querySelectorAll('a[data-keep-language]').forEach(link=>{{const url=new URL(link.href);
if(select.value)url.searchParams.set('language',select.value);else url.searchParams.delete('language');link.href=url.href;}});}};
select.addEventListener('change',apply);apply();}})();</script>'''
FILTER_SCRIPT = '<script>' + FILTER.format(options='').split('<script>', 1)[1]


def source_path(book, identity):
    token = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]
    return BASE + book + '/entry-' + token + '.html'


def load_lines(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def occurrence_id(book, identity):
    return 'fawaz:' + REVISION[:12] + ':' + book + ':' + quote(identity, safe='._-')


def render(writer, reader_occurrence_ids=None):
    # Imported lazily to keep the existing discovery/reader import graph acyclic.
    from build_discovery import esc, relative_link, language_name
    progress = read_json(writer.root, IMPORT + '/progress.json')
    if progress is None or progress.get('provider_occurrences') == 0:
        return {'provider_occurrences': 0, 'original_source_pages': 0, 'pages': 0}
    if reader_occurrence_ids is None:
        raise ValueError('Source views require verified reader occurrence IDs')
    state = read_json(writer.root, IMPORT + '/state.json')
    if not state or progress.get('revision') != REVISION:
        raise ValueError('Source views require the pinned provider checkpoint')
    def source_input(key):
        descriptor = state['inputs'][key]
        if descriptor.get('source_path') != key:
            raise ValueError('Source-view input key differs from pinned snapshot path')
        return checked_snapshot(writer.root, descriptor)

    catalog = parse_json(source_input('editions.json'))
    start_files, index_rows, total_ids, total_held = writer.files, [], 0, 0

    def link(current, target, label, preserve=False):
        return '<a' + (' data-keep-language' if preserve else '') + ' href="' + esc(relative_link(current, target)) + '">' + esc(label) + '</a>'

    def filter_html(prefixes):
        options = ''.join('<option value="' + LANGUAGES[p][0] + '">' + esc(language_name(LANGUAGES[p][0])) + '</option>' for p in prefixes)
        return FILTER.format(options=options).split('<script>', 1)[0]

    def edition_links(book, prefixes):
        out = ['<details><summary>Complete original editions and credits</summary><ul>']
        for prefix in prefixes:
            snapshot = state['inputs']['editions/' + prefix + '-' + book + '.json']
            meta = edition_metadata(catalog, book, prefix)
            author = meta.get('author')
            role = 'Compiler' if book == 'nawawi' and author == 'Imam Nawawi' else 'Edition author credit'
            out.append('<li><a href="' + esc(snapshot['url']) + '">' + esc(language_name(LANGUAGES[prefix][0])) + ' · original JSON</a>' +
                       ('<br>' + role + ': ' + esc(author) if author else '') +
                       '<br><small>Original SHA-256: <code>' + esc(snapshot['sha256']) + '</code></small></li>')
        return ''.join(out) + '</ul></details>'

    for book, counts in sorted(progress['by_book'].items()):
        if book not in BOOKS:
            raise ValueError('Unknown provider book in source view')
        ledger = load_lines(writer.root / IMPORT / 'classification' / (book + '.jsonl.gz'))
        held = load_lines(writer.root / IMPORT / 'held' / (book + '.jsonl.gz'))
        held_by_id = {item['typed_hadithnumber']: item for item in held}
        ledger_ids = [item['typed_hadithnumber'] for item in ledger]
        expected_held = {item['typed_hadithnumber'] for item in ledger if item['classification']['classification'] != 'hadith'}
        if (len(held_by_id) != len(held) or len(set(ledger_ids)) != len(ledger_ids) or
                expected_held != set(held_by_id) or len(ledger) != counts['provider_occurrences'] or
                len(held) != counts['held_occurrences']):
            raise ValueError('Incomplete source-view occurrence accounting: ' + book)
        prefixes = [p for p in LANGUAGES if 'editions/' + p + '-' + book + '.json' in state['inputs'] and
                    p in counts.get('processed_languages', ['ara', 'eng', 'urd'])]
        editions = {p: parse_edition(source_input('editions/' + p + '-' + book + '.json'),
                                    edition_metadata(catalog, book, p), catalog[book]['name']) for p in prefixes}
        source_positions = {}
        for prefix, edition in editions.items():
            for position, row in enumerate(edition['hadiths']):
                source_positions.setdefault(typed_identity(row['hadithnumber']), {}).setdefault(prefix, []).append(position)
        if set(ledger_ids) != set(source_positions):
            raise ValueError('Source index IDs differ from the acquired edition union: ' + book)
        expected_reader_ids = {occurrence_id(book, identity) for identity in ledger_ids if identity not in expected_held}
        reader_prefix = 'fawaz:' + REVISION[:12] + ':' + book + ':'
        if expected_reader_ids != {identity for identity in reader_occurrence_ids if identity.startswith(reader_prefix)}:
            raise ValueError('Source index and verified narration reader disagree: ' + book)
        directory = BASE + book + '/'
        title = BOOKS[book][1]
        downloads = edition_links(book, prefixes)
        for identity, item in held_by_id.items():
            current = source_path(book, identity)
            body = [link(current, directory + 'index.html', title + ' · all source entries', True),
                    '<h1>' + esc(title) + ' · provider entry ' + esc(identity) + '</h1>',
                    '<p><strong>Original source entry</strong></p>']
            resolution_text = source_view_resolution_text(item)
            if resolution_text:
                body.append('<p>' + esc(resolution_text) + '</p>')
            else:
                body.append('<p>This entry is preserved outside the narration reader. '
                            'Its attribution or boundaries still need review. Its original wording is available below.</p>')
            if item['classification']['reason'] == 'no_nonempty_narration_text':
                body.append('<p>The saved language fields contain no established narration text. Empty fields are kept explicitly.</p>')
            body.append(filter_html(prefixes))
            expected_versions = source_positions[identity]
            if set(item['source_versions']) != set(expected_versions):
                raise ValueError('Held source language inventory differs from original editions')
            for prefix in prefixes:
                versions = item['source_versions'].get(prefix, [])
                if sorted(version['position'] for version in versions) != expected_versions.get(prefix, []):
                    raise ValueError('Held source positions differ from original editions')
                code, label, _ = LANGUAGES[prefix]
                snapshot = state['inputs']['editions/' + prefix + '-' + book + '.json']
                meta = edition_metadata(catalog, book, prefix)
                for version in versions:
                    position = version['position']
                    row = version['row']
                    if (type(position) is not int or not 0 <= position < len(editions[prefix]['hadiths']) or
                            editions[prefix]['hadiths'][position] != row or typed_identity(row['hadithnumber']) != identity or
                            version['source_path'] != snapshot['path'] or version['source_sha256'] != snapshot['sha256']):
                        raise ValueError('Original source field mismatch in view: ' + book + '/' + prefix + '/' + identity)
                    direction = 'rtl' if code in ('ar', 'ur') else 'auto'
                    body.append('<section data-source-languages="' + code + '"><details class="language-reading" open><summary>' +
                                esc(language_name(code)) + ' · original source text</summary><div class="reading-content">')
                    if row['text']:
                        body.append('<p class="text original-source-text" lang="' + code + '" dir="' + direction + '">' + esc(row['text']) + '</p>')
                    else:
                        body.append('<p class="muted">The provider supplied an empty text field for this language.</p>')
                    body.append('<details><summary>References and source for this language</summary><p><a href="' + esc(entry_url(meta['name'], row['hadithnumber'])) +
                                '">Provider entry</a> · <a href="' + esc(snapshot['url']) + '">Pinned original edition</a></p><pre class="text">' +
                                esc(json.dumps({'provider_edition': meta['name'], 'hadithnumber': row['hadithnumber'],
                                               'arabicnumber': row.get('arabicnumber'), 'reference': row.get('reference'),
                                               'source_position': position, 'source_sha256': snapshot['sha256']}, ensure_ascii=False, indent=2)) + '</pre></details>')
                    body.append('<details><summary>Source assessments and commentary</summary>')
                    for assessment in row.get('grades', []):
                        body.append('<p dir="auto">' + esc(assessment.get('name') or 'Assessor not supplied') + ': ' + esc(assessment.get('grade') or 'Grade not supplied') + '</p>')
                    notes = (version.get('text_spans') or {}).get('notes', [])
                    for span in notes:
                        if (not isinstance(span, list) or len(span) != 2 or any(type(v) is not int for v in span) or
                                not 0 <= span[0] <= span[1] <= len(row['text'])):
                            raise ValueError('Invalid source commentary span in original-source view')
                        body.append('<p class="text" lang="' + code + '" dir="' + direction + '">' + esc(row['text'][span[0]:span[1]]) + '</p>')
                    if not notes:
                        body.append('<p>No separate commentary span has been established for this field. The complete original text remains above.</p>')
                    body.append('</details></div></details></section>')
            body.append(downloads)
            body.append(FILTER_SCRIPT)
            writer.page(current, title + ' · original source entry ' + identity + ' | Hadith Bank',
                        'Original multilingual provider text and its own references, outside the narration search.', ''.join(body), indexable=False)
        page_count = max(1, math.ceil(len(ledger) / PAGE_SIZE))
        for number in range(1, page_count + 1):
            current = directory + ('index.html' if number == 1 else 'page-' + str(number) + '.html')
            navigation = '<nav class="pagination" aria-label="Source entry pages">' + ''.join(
                ('<strong aria-current="page">' + str(n) + '</strong>') if n == number else link(current,
                directory + ('index.html' if n == 1 else 'page-' + str(n) + '.html'), str(n), True)
                for n in range(1, page_count + 1)) + '</nav>'
            body = [link(current, BASE + 'index.html', 'All Fawaz source collections'), '<h1>' + esc(title) + ' · complete source index</h1>',
                    '<p>' + str(len(ledger)) + ' acquired provider entries: ' + str(len(ledger) - len(held)) +
                    ' in the narration reader and ' + str(len(held)) + ' in the original-source view.</p>', filter_html(prefixes), downloads, navigation, '<ul class="records">']
            for item in ledger[(number - 1) * PAGE_SIZE:number * PAGE_SIZE]:
                identity = item['typed_hadithnumber']
                is_held = identity in held_by_id
                occurrence = occurrence_id(book, identity)
                href = relative_link(current, source_path(book, identity)) if is_held else relative_link(current, 'index.html') + '?occurrence=' + quote(occurrence, safe='')
                available = [LANGUAGES[p][0] for p in prefixes if item.get('language_availability', {}).get(LANGUAGES[p][0]) not in ('provider_entry_absent', 'edition_pending', 'edition_not_published_in_pinned_catalog')]
                body.append('<li data-source-languages="' + ','.join(available) + '"><a data-keep-language href="' + esc(href) + '">Provider entry ' + esc(identity) +
                            '</a> · ' + (('Reviewed source entry' if source_view_resolution_text(item) else 'Source entry awaiting review') if is_held else 'Reader narration') + '</li>')
            body.extend(['</ul>', navigation, FILTER_SCRIPT])
            writer.page(current, title + ' · complete source index | Hadith Bank',
                        'Every acquired provider entry has a reader or original-source destination.', ''.join(body), indexable=False)
        index_rows.append((book, title, len(ledger), len(held), prefixes))
        total_ids += len(ledger)
        total_held += len(held)
    if total_ids != progress['provider_occurrences'] or total_held != progress['held_occurrences']:
        raise ValueError('Provider totals disagree with complete source index')
    current = BASE + 'index.html'
    body = ['<h1>Fawaz source editions</h1><p>Every acquired provider entry is listed here. Narrations open in the reader; '
            'other entries open as original source text with each language\'s own references.</p><p><strong>' + str(total_ids) +
            ' source entries</strong> · ' + str(total_ids - total_held) + ' reader narrations · ' + str(total_held) +
            ' original-source entries.</p>']
    if 'resolved_excluded_occurrences' in progress:
        body.append('<p>' + str(progress['resolved_excluded_occurrences']) +
                    ' original-source entries have completed semantic review; ' +
                    str(progress['unresolved_held_occurrences']) + ' await semantic disposition. '
                    'Source gaps remain explicit.</p>')
    all_prefixes = [p for p in LANGUAGES if any(p in row[4] for row in index_rows)]
    body.extend([filter_html(all_prefixes), '<ul class="cards">'])
    for book, title, count, held_count, prefixes in index_rows:
        body.append('<li data-source-languages="' + ','.join(LANGUAGES[p][0] for p in prefixes) + '">' +
                    link(current, BASE + book + '/index.html', title, True) + '<br>' + str(count) + ' source entries · ' +
                    str(count - held_count) + ' reader narrations · ' + str(held_count) + ' original-source entries</li>')
    body.extend(['</ul><p>Provider numbering is retained as supplied. Counts refer to source entries, including variants and empty fields.</p>', FILTER_SCRIPT])
    writer.page(current, 'Fawaz source editions | Hadith Bank', 'Complete acquired Urdu, Bengali, Arabic and English source editions.', ''.join(body), indexable=False)
    return {'provider_occurrences': total_ids, 'original_source_pages': total_held,
            'reader_occurrences': total_ids - total_held, 'pages': writer.files - start_files,
            'index_path': BASE + 'index.html', 'original_texts_verified': True,
            'included_in_narration_search': False}
