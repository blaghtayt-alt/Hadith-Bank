#!/usr/bin/env python3
"""Build an offline Hadith Bank reader and optional paginated Markdown views.

Input: catalog/materials.json, whose search object declares records_path,
records_sha256 and count. If the whole JSONL file is absent, ordered search.shards
are consumed instead; each shard declares path, sha256, count and bytes. The
concatenated shard bytes must match records_sha256. Only verified local inputs
are embedded. Source text/provenance are copied, never translated or reclassified.
"""
import argparse
import base64
import collections
import gzip
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit


PAGE_SIZE = 25
LANGUAGE_NAMES = {
    'ar': 'Arabic', 'bn': 'Bengali', 'fil': 'Filipino', 'hi': 'Hindi',
    'ja': 'Japanese', 'pt': 'Portuguese', 'ur': 'Urdu', 'uz': 'Uzbek',
    'vi': 'Vietnamese', 'zh': 'Chinese', 'zh-CN': 'Chinese (Simplified)',
}
DEFAULT_SITE = {
    'repository_url': 'https://github.com/blaghtayt-alt/Hadith-Bank',
    'live_url': 'https://blaghtayt-alt.github.io/Hadith-Bank/',
    'source_ref': 'main',
}
SHA256 = re.compile(r'[0-9a-fA-F]{64}\Z')


def local(root, relative):
    if (not isinstance(relative, str) or not relative or '\\' in relative or
            any(ord(c) < 32 for c in relative)):
        raise ValueError('Unsafe local source path')
    pure = PurePosixPath(relative)
    if (pure.is_absolute() or '..' in pure.parts or not pure.parts or
            ':' in pure.parts[0] or pure.as_posix() != relative or
            any(p in ('', '.') for p in relative.split('/'))):
        raise ValueError('Unsafe local source path: ' + relative)
    target = root.joinpath(*pure.parts)
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlink source path is not permitted: ' + relative)
    if not target.resolve().is_relative_to(root):
        raise ValueError('Source path escapes bank root: ' + relative)
    return target


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('Non-finite JSON value is not supported')


def parse_json(text):
    return json.loads(text, object_pairs_hook=pairs_unique,
                      parse_constant=invalid_constant)


def valid_hash(value, field):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError(field + ' must be a SHA-256 hexadecimal digest')
    return value.lower()


def valid_count(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(field + ' must be a nonnegative integer')
    return value


def validate_record(record, location):
    if not isinstance(record, dict):
        raise ValueError(location + ': each JSONL line must contain an object')
    for field in ('id', 'language', 'book_key', 'edition', 'source_id'):
        if not isinstance(record.get(field), str) or not record[field]:
            raise ValueError(location + ': missing string ' + field)
    for field in ('title', 'text_arabic', 'text_translation'):
        if record.get(field) is not None and not isinstance(record[field], str):
            raise ValueError(location + ': ' + field + ' must be a string or null')
    for field in ('source', 'translator', 'translation_provenance', 'review'):
        if not isinstance(record.get(field), dict):
            raise ValueError(location + ': ' + field + ' must be an object')
    for field in ('topic_tags', 'editorial_tags', 'source_headings', 'footnotes'):
        if not isinstance(record.get(field), list):
            raise ValueError(location + ': ' + field + ' must be an array')


def load_records(root):
    """Return all occurrences plus catalog after complete input verification."""
    root = Path(root).resolve()
    catalog = parse_json(local(root, 'catalog/materials.json').read_text(encoding='utf-8'))
    if not isinstance(catalog, dict) or not isinstance(catalog.get('search'), dict):
        raise ValueError('catalog/materials.json requires a search object')
    search = catalog['search']
    expected_hash = valid_hash(search.get('records_sha256'), 'search.records_sha256')
    expected_count = valid_count(search.get('count'), 'search.count')
    whole = local(root, search.get('records_path'))
    using_shards = not whole.is_file()
    if using_shards:
        shards = search.get('shards')
        if not isinstance(shards, list) or not shards:
            raise ValueError('Whole search stream is absent and no ordered search.shards are supplied')
        inputs = []
        seen = set()
        for shard in shards:
            if not isinstance(shard, dict):
                raise ValueError('Each search shard must be an object')
            relative = shard.get('path')
            path = local(root, relative)
            if relative in seen:
                raise ValueError('Duplicate search shard path: ' + relative)
            seen.add(relative)
            inputs.append((path, relative, valid_hash(shard.get('sha256'), 'shard.sha256'),
                           valid_count(shard.get('count'), 'shard.count'),
                           valid_count(shard.get('bytes'), 'shard.bytes')))
    else:
        inputs = [(whole, search['records_path'], expected_hash, expected_count, None)]
    records = []
    combined = hashlib.sha256()
    for position, (path, relative, expected, count, size) in enumerate(inputs):
        file_hash = hashlib.sha256()
        actual_count = actual_size = 0
        last = b''
        with path.open('rb') as stream:
            for line_number, raw in enumerate(stream, 1):
                combined.update(raw)
                file_hash.update(raw)
                actual_size += len(raw)
                last = raw
                if not raw.strip():
                    continue
                try:
                    record = parse_json(raw.decode('utf-8'))
                except (ValueError, UnicodeError) as error:
                    raise ValueError(relative + ':' + str(line_number) + ': invalid UTF-8 JSON') from error
                validate_record(record, relative + ':' + str(line_number))
                records.append(record)
                actual_count += 1
        if file_hash.hexdigest() != expected:
            raise ValueError('SHA-256 mismatch: ' + relative)
        if actual_count != count:
            raise ValueError('Record count mismatch: ' + relative)
        if size is not None and actual_size != size:
            raise ValueError('Byte count mismatch: ' + relative)
        if position < len(inputs) - 1 and last and not last.endswith(b'\n'):
            raise ValueError('Non-final shard must end with a JSONL newline: ' + relative)
    if combined.hexdigest() != expected_hash or len(records) != expected_count:
        raise ValueError('Combined search stream hash/count does not match catalog')
    return records, catalog, {'records_sha256': expected_hash, 'record_count': len(records),
                              'input_mode': 'shards' if using_shards else 'whole_file',
                              'input_files_verified': len(inputs)}


def script_json(value):
    """Escape script delimiters without changing the decoded source strings."""
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def safe_url(value):
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    return value if parsed.scheme.lower() in ('https', 'http') and parsed.netloc else None


def text(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if type(value) in (int, float, bool):
        return str(value)
    if isinstance(value, list):
        return ' · '.join(filter(None, (text(v) for v in value)))
    if isinstance(value, dict):
        return ' · '.join(filter(None, (text(v) for v in value.values())))
    return ''


def number_label(record):
    number = record.get('number') or {}
    items = []
    if isinstance(number, dict) and number.get('in_book') is not None:
        items.append('Book number ' + text(number['in_book']))
    if record.get('provider_entry_id') is not None:
        items.append('Source entry ' + text(record['provider_entry_id']))
    return ' · '.join(items) or 'Book number not supplied'


def page_label(record):
    page = record.get('page') or {}
    if not isinstance(page, dict):
        return text(page)
    items = []
    if page.get('pdf'):
        items.append('PDF page ' + ', '.join(map(str, page['pdf'])))
    if page.get('printed'):
        items.append('Printed page ' + ', '.join(map(str, page['printed'])))
    if page.get('sheet'):
        items.append('Sheet ' + str(page['sheet']))
    if page.get('row') is not None:
        items.append('Row ' + str(page['row']))
    return ' · '.join(items) or 'Page locator not supplied'


def escaped(value):
    return html.escape(text(value), quote=True)


def component(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', value) or value in ('.', '..'):
        raise ValueError('Unsafe Markdown language/book/edition path component')
    return value


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8', newline='\n')


def prose(value, direction='auto'):
    """Literal text in wrapping GitHub paragraphs; retain source line breaks."""
    return '<p dir="' + direction + '">' + escaped(value).replace('\n', '<br>\n') + '</p>'


def source_link(relative, bank_root, page_directory):
    if not relative:
        return 'Not supplied'
    label = escaped(relative)
    if bank_root is not None and page_directory is not None:
        target = local(bank_root, relative)
        if target.is_file():
            href = Path(os.path.relpath(target, page_directory)).as_posix()
            return '<a href="' + escaped(href) + '">' + label + '</a>'
    return '<code>' + label + '</code>'


def markdown_record(record, index, bank_root=None, page_directory=None):
    source = record['source']
    provenance = record['translation_provenance']
    translator = record['translator']
    lines = ['## Narration ' + str(index), '']
    if record.get('title'):
        lines += ['<p><strong>' + escaped(record['title']) + '</strong></p>', '']
    primary = record.get('text_translation')
    primary_arabic = not primary and bool(record.get('text_arabic'))
    if primary_arabic:
        primary = record['text_arabic']
    if primary is not None:
        lines += [prose(primary, 'rtl' if primary_arabic else 'auto'), '']
    else:
        lines += ['Text not supplied in this projection.', '']
    if record.get('text_arabic') and not primary_arabic:
        lines += ['<details>', '<summary>Arabic source text</summary>', '',
                  prose(record['text_arabic'], 'rtl'),
                  '', '</details>', '']
    url = safe_url(source.get('record_url')) or safe_url(source.get('url'))
    source_name = source.get('name') or record['source_id']
    source_display = ('<a href="' + escaped(url) + '">' + escaped(source_name) + '</a>'
                      if url else escaped(source_name) + ' — source URL not supplied')
    translator_name = text(translator.get('name')) or 'Not named in the supplied source'
    label = provenance.get('label') or provenance.get('origin') or 'Not supplied'
    lines += [
        '<p><strong>Source:</strong> ' + source_display + '<br>',
        '<strong>Collection:</strong> ' + escaped(record['book_key']) +
        ' · <strong>Edition:</strong> ' + escaped(record['edition']) + '<br>',
        '<strong>Number:</strong> ' + escaped(number_label(record)) + '<br>',
        '<strong>Page:</strong> ' + escaped(page_label(record)) + '<br>',
        '<strong>Translator:</strong> ' + escaped(translator_name) + '<br>',
        '<strong>Translation origin:</strong> ' + escaped(label) +
        ('<br><strong>AI translation flag:</strong> ' + escaped(provenance['ai_translation'])
         if 'ai_translation' in provenance else '') +
        ('<br>' + escaped(provenance['scope_note']) if provenance.get('scope_note') else '') + '</p>', '',
    ]
    if record.get('source_headings'):
        lines += ['<p><strong>Source headings:</strong> ' + escaped(record['source_headings']) + '</p>', '']
    review = record.get('review') or {}
    current = review.get('current_policy') or {}
    review_fields = ['Historical import status: ' + text(review.get('status')),
                     'Historical independent Pro QC: ' + text(review.get('independent_pro_qc')),
                     'Release: ' + text(review.get('release_status'))]
    if current.get('separate_bank_review_required') is False:
        lines += ['<p><strong>Bank review:</strong> ' + escaped(current['label']) + '</p>', '',
                  '<details><summary>Import history and source-alignment notes</summary>', '',
                  '<p>' + escaped(' · '.join(review_fields)) + '</p>', '',
                  prose('\n'.join(text(issue) for issue in review.get('issues', [])) or 'No source-alignment issues listed.'),
                  '', '</details>', '']
    else:
        lines += ['<p>' + escaped(' · '.join(review_fields)) + '</p>', '']
    commentary = record.get('commentary') or {}
    footnotes = record.get('footnotes') or []
    if any(commentary.values()) or footnotes:
        lines += ['<details>', '<summary>Commentary and footnotes</summary>', '']
        for language in ('translation', 'arabic'):
            if commentary.get(language):
                lines += [prose(commentary[language], 'rtl' if language == 'arabic' else 'auto'), '']
        for note in footnotes:
            if isinstance(note, str):
                lines += [prose(note), '']
            else:
                lines += ['<pre>' + escaped(json.dumps(note, ensure_ascii=False, indent=2)) + '</pre>', '']
        lines += ['</details>', '']
    benefits = record.get('benefits') or {}
    if benefits.get('translation') or benefits.get('arabic'):
        lines += ['<details>', '<summary>Benefits supplied by the source</summary>', '']
        for language in ('translation', 'arabic'):
            value = benefits.get(language)
            for item in value if isinstance(value, list) else [value]:
                if isinstance(item, str):
                    lines += [prose(item, 'rtl' if language == 'arabic' else 'auto'), '']
                elif item is not None:
                    lines += ['<pre>' + escaped(json.dumps(item, ensure_ascii=False, indent=2)) + '</pre>', '']
        if benefits.get('scope'):
            lines += ['<p><strong>Source scope:</strong> ' + escaped(benefits['scope']) + '</p>', '']
        lines += ['</details>', '']
    references = record.get('references') or {}
    if references:
        labels = {'translation_attribution_verbatim': 'Translated source attribution',
                  'arabic_attribution_verbatim': 'Arabic source attribution',
                  'bibliography_verbatim': 'Bibliographic references',
                  'arabic': 'Arabic references', 'translation': 'Translated references',
                  'canonical_mapping_status': 'Canonical mapping status'}
        reference_parts = []
        for key, value in references.items():
            if isinstance(value, str) and value:
                reference_parts += ['<p><strong>' + escaped(labels.get(key, key.replace('_', ' '))) + '</strong></p>',
                                    prose(value), '']
            elif key == 'items' and value:
                reference_parts += ['<pre>' + escaped(json.dumps(value, ensure_ascii=False, separators=(',', ':'))) + '</pre>', '']
        if reference_parts:
            lines += ['<details>', '<summary>References</summary>', '', *reference_parts, '</details>', '']
    narrator = record.get('narrator')
    if narrator or record.get('topic_tags') or record.get('editorial_tags'):
        details = {'narrator': narrator, 'topic_tags': record.get('topic_tags', []),
                   'editorial_tags': record.get('editorial_tags', [])}
        lines += ['<details>', '<summary>Narrator and supplied tags</summary>', '',
                  '<pre>' + escaped(json.dumps(details, ensure_ascii=False, separators=(',', ':'))) + '</pre>',
                  '', '</details>', '']
    locator = source.get('record_locator') or {}
    locator_parts = ['<p><strong>Occurrence ID:</strong> <code>' + escaped(record['id']) + '</code><br>',
                     '<strong>Canonical record:</strong> ' + source_link(locator.get('path'), bank_root, page_directory)]
    if locator.get('line') is not None:
        locator_parts.append('<br><strong>Line:</strong> ' + escaped(locator['line']))
    if locator.get('json_pointer') is not None:
        locator_parts.append('<br><strong>JSON pointer:</strong> <code>' + escaped(locator['json_pointer']) + '</code>')
    locator_parts += ['<br><strong>Original file:</strong> ' + source_link(source.get('original_file'), bank_root, page_directory),
                      '<br><strong>Original SHA-256:</strong> <code>' + escaped(source.get('sha256')) + '</code></p>']
    issues = review.get('issues') or []
    lines += ['<details>', '<summary>Source locators and review issues</summary>', '',
              ''.join(locator_parts), '',
              '<p><strong>Review issues:</strong></p>',
              prose('\n'.join(text(issue) for issue in issues) if issues else 'None listed in this record.'),
              '', '</details>', '', '---', '']
    return '\n'.join(lines)


def build_markdown(records, output, info, catalog=None, bank_root=None):
    output = Path(output).resolve()
    groups = collections.defaultdict(list)
    for record in records:
        key = tuple(component(record[field]) for field in ('language', 'book_key', 'edition'))
        groups[key].append(record)
    languages = collections.defaultdict(list)
    books = collections.defaultdict(list)
    written = []
    page_count = 0

    def save(relative, content):
        target = local(output, relative)
        write(target, content)
        written.append(relative)

    for (language, book, edition), items in sorted(groups.items()):
        label = LANGUAGE_NAMES.get(language, language)
        directory = '/'.join((language, book, edition))
        pages = (len(items) + PAGE_SIZE - 1) // PAGE_SIZE
        page_links = []
        for page in range(pages):
            name = 'page-' + str(page + 1).zfill(4) + '.md'
            start, end = page * PAGE_SIZE, min((page + 1) * PAGE_SIZE, len(items))
            nav = ['[Edition index](README.md)']
            if page:
                nav.append('[Previous](page-' + str(page).zfill(4) + '.md)')
            if page + 1 < pages:
                nav.append('[Next](page-' + str(page + 2).zfill(4) + '.md)')
            body = ['# ' + escaped(label) + ' / ' + escaped(book), '',
                    'Edition: `' + edition + '` · Narrations ' + str(start + 1) + '–' + str(end) +
                    ' of ' + str(len(items)) + '.', '', ' · '.join(nav), '']
            body.extend(markdown_record(r, start + i + 1, bank_root, output / directory)
                        for i, r in enumerate(items[start:end]))
            body += ['', ' · '.join(nav), '']
            save(directory + '/' + name, '\n'.join(body))
            page_links.append('- [Narrations ' + str(start + 1) + '–' + str(end) + '](' + name + ')')
            page_count += 1
        save(directory + '/README.md', '\n'.join([
            '# ' + escaped(label) + ' / ' + escaped(book), '',
            'Edition: `' + edition + '` · ' + str(len(items)) + ' source occurrences.', '',
            '[Book index](../README.md) · [Language index](../../README.md) · [All languages](../../../README.md)', '',
            'Each page contains up to 25 records. Source texts, versions and review flags remain separate.', '',
            *page_links, '',
        ]))
        books[(language, book)].append((edition, len(items)))
        languages[language].append((book, edition, len(items)))
    for (language, book), entries in sorted(books.items()):
        save(language + '/' + book + '/README.md', '\n'.join([
            '# ' + escaped(LANGUAGE_NAMES.get(language, language)) + ' / ' + escaped(book), '',
            '[Language index](../README.md) · [All languages](../../README.md)', '',
            *['- [' + edition + '](' + edition + '/README.md) — ' + str(count) + ' source occurrences'
              for edition, count in entries], '',
        ]))
    for language, entries in sorted(languages.items()):
        grouped = collections.Counter()
        for book, edition, count in entries:
            grouped[book] += count
        save(language + '/README.md', '\n'.join([
            '# ' + escaped(LANGUAGE_NAMES.get(language, language)), '', '[All languages](../README.md)', '',
            *['- [' + escaped(book) + '](' + book + '/README.md) — ' + str(count) + ' source occurrences'
              for book, count in sorted(grouped.items())], '',
        ]))
    catalog = catalog or {}
    legacy = catalog.get('legacy_materials', [])
    private = catalog.get('private_materials_not_in_this_tree', [])
    if legacy or private:
        save('materials/README.md', '\n'.join([
            '# Other catalogued materials', '',
            '[Narration reading index](../README.md)', '',
            'These listings are separate from the indexed narration count and search results.', '',
            '- [Legacy source documents](legacy.md) — ' + str(len(legacy)) + ' documents',
            '- [Private materials unavailable in this tree](private.md) — ' + str(len(private)) + ' datasets', '',
        ]))
        legacy_lines = ['# Legacy source documents', '', '[Material index](README.md)', '',
                        'These documents retain their original source format. They are catalogued here without '
                        'adding inferred narrations to the search count. Translation origin is reported as supplied.', '']
        for item in legacy:
            relative = item.get('path')
            label = str(relative or 'Path not supplied')
            if relative and bank_root is not None:
                target = local(bank_root, relative)
                if target.is_file():
                    link = Path(os.path.relpath(target, output / 'materials')).as_posix()
                    label = '<a href="' + escaped(link) + '">' + escaped(relative) + '</a>'
                else:
                    label = escaped(relative) + ' (not present locally)'
            else:
                label = escaped(label)
            legacy_lines += ['<p><strong>' + escaped(LANGUAGE_NAMES.get(item.get('language'), item.get('language'))) +
                             '</strong> · ' + label + '<br>Translation origin: ' +
                             escaped(item.get('translation_origin') or 'unknown') + '<br>Source revision: ' +
                             escaped(item.get('source_revision')) + '<br>SHA-256: <code>' +
                             escaped(item.get('sha256')) + '</code></p>', '']
        save('materials/legacy.md', '\n'.join(legacy_lines))
        private_lines = ['# Private materials unavailable in this tree', '', '[Material index](README.md)', '',
                         'Metadata only. These source datasets are not included in this tree’s narration '
                         'search or its record total. Their content remains in the separate private package.', '']
        for item in private:
            private_lines += ['## ' + escaped(item.get('dataset_id')), '',
                              '<p>' + escaped(LANGUAGE_NAMES.get(item.get('language'), item.get('language'))) +
                              ' · ' + escaped(item.get('book_key')) + ' · ' + escaped(item.get('edition')) +
                              '<br>Source occurrences in separate package: ' + escaped(item.get('count')) +
                              '<br>Release status: ' + escaped(item.get('release_status')) +
                              '<br>' + escaped(item.get('location_note')) + '</p>', '']
        save('materials/private.md', '\n'.join(private_lines))
    save('README.md', '\n'.join([
        '# Hadith Bank — readable records', '',
        str(len(records)) + ' source occurrences, organized by language, book and source edition.', '',
        'Open a language, then a book and edition. Every page shows up to 25 narrations with their source, '
        'translator, translation origin and review status. Arabic, commentary and audit details are expandable. '
        'Repeated narrations and source versions are retained.', '',
        *['- [' + LANGUAGE_NAMES.get(language, language) + '](' + language + '/README.md) — ' +
          str(sum(count for _, _, count in entries)) + ' source occurrences'
          for language, entries in sorted(languages.items())], '',
        *(['[Other catalogued materials](materials/README.md) — ' + str(len(legacy)) +
           ' legacy documents and ' + str(len(private)) + ' private datasets listed separately.', '']
          if legacy or private else []),
        'Source stream SHA-256: `' + info['records_sha256'] + '`.', '',
        'These reading views do not change the source review status or certify narration authenticity.', '',
    ]))
    manifest = {'schema': 'hadith-bank-readable-pages-v1', **info, 'page_size': PAGE_SIZE,
                'narration_pages': page_count, 'files': written}
    save('reader-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return {'markdown_pages': page_count, 'markdown_files': len(written),
            'markdown_output': str(output)}


def site_metadata(catalog, override=None):
    """Keep navigation explicit, safe, and deterministic for hosted/offline builds."""
    configured = catalog.get('site') or {}
    if not isinstance(configured, dict) or (override is not None and not isinstance(override, dict)):
        raise ValueError('Reader site configuration must be an object')
    site = dict(DEFAULT_SITE)
    for source in (configured, override or {}):
        for key in ('repository_url', 'live_url', 'source_ref', 'build_commit'):
            if key in source:
                site[key] = source[key]
    repository = urlsplit(site['repository_url']) if isinstance(site.get('repository_url'), str) else None
    if (repository is None or repository.scheme != 'https' or repository.netloc != 'github.com' or
            repository.query or repository.fragment or
            not re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?', repository.path)):
        raise ValueError('Reader repository_url must identify one HTTPS GitHub repository')
    site['repository_url'] = site['repository_url'].rstrip('/')
    live = urlsplit(site['live_url']) if isinstance(site.get('live_url'), str) else None
    if (live is None or live.scheme != 'https' or not live.netloc or live.username or live.password or
            live.query or live.fragment or any(ord(c) < 32 for c in site['live_url'])):
        raise ValueError('Reader live_url must be a plain HTTPS website URL')
    reference = site.get('source_ref')
    if (not isinstance(reference, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', reference) or
            any(part in ('', '.', '..') for part in reference.split('/'))):
        raise ValueError('Reader source_ref must be a safe Git reference')
    if 'build_commit' in site and (not isinstance(site['build_commit'], str) or
            not re.fullmatch(r'[0-9a-fA-F]{40,64}', site['build_commit'])):
        raise ValueError('Reader build_commit must be a full hexadecimal commit ID')
    return site


def build(root, output, markdown_output=None, compress=True, site=None):
    root = Path(root).resolve()
    output = Path(output).absolute()
    records, catalog, info = load_records(root)
    template_path = Path(__file__).resolve().parents[1] / 'reader' / 'template.html'
    template = template_path.read_text(encoding='utf-8')
    for marker in ('__HADITH_RECORDS_JSON__', '__HADITH_SNAPSHOT_JSON__', '__HADITH_ENCODING__'):
        if template.count(marker) != 1:
            raise ValueError('Reader template must contain one ' + marker)
    if output.is_symlink() or any(parent.is_symlink() for parent in output.parents):
        raise ValueError('Reader output must not use symlinks')
    metadata = {**info, 'title': catalog.get('title') or 'Hadith Bank',
                'materials': catalog.get('materials', []), 'language_names': LANGUAGE_NAMES,
                'site': site_metadata(catalog, site),
                'legacy_materials': catalog.get('legacy_materials', []),
                'private_materials_not_in_this_tree': catalog.get('private_materials_not_in_this_tree', [])}
    if compress:
        payload = base64.b64encode(gzip.compress(
            json.dumps(records, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8'),
            compresslevel=6, mtime=0)).decode('ascii')
    else:
        payload = script_json(records)
    replacements = {'__HADITH_RECORDS_JSON__': payload,
                    '__HADITH_ENCODING__': 'gzip-base64' if compress else 'json',
                    '__HADITH_SNAPSHOT_JSON__': script_json(metadata)}
    # Substitute against the original template once; source text can itself
    # contain either marker and must never be substituted a second time.
    document = re.sub(r'__HADITH_(?:(?:RECORDS|SNAPSHOT)_JSON|ENCODING)__',
                      lambda match: replacements[match.group(0)], template)
    write(output, document)
    result = {**info, 'html_output': str(output), 'html_bytes': output.stat().st_size,
              'source_text_modified': False, 'network_dependencies': [],
              'embedded_encoding': 'gzip-base64' if compress else 'json'}
    if markdown_output is not None:
        result.update(build_markdown(records, markdown_output, info, catalog, root))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--markdown-output', type=Path)
    parser.add_argument('--uncompressed', action='store_true',
                        help='Embed plain JSON for browsers without built-in DecompressionStream support.')
    args = parser.parse_args()
    try:
        result = build(args.root, args.output, args.markdown_output, compress=not args.uncompressed)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Reader build failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
