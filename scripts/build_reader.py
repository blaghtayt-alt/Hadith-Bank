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
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import quote, urljoin, urlsplit
import xml.etree.ElementTree as ET

from review_display_policy import DEFAULT_DISPLAY_POLICY, review_badges, text_direction
from counterpart_display import (counterpart_data, counterpart_source_data,
                                 counterpart_citation, counterpart_qualification, counterpart_alignment_notes,
                                 counterpart_translation_origin)
from citation_search import has_noncanonical_numbering
from book_titles import book_label as collection_label, title_metadata
from language_display import language_readings, available_languages, reading_direction


PAGE_SIZE = 25
MAX_READER_SHARD_BYTES = 2 * 1024 * 1024
LANGUAGE_NAMES = {
    'ar': 'Arabic', 'bn': 'Bengali', 'en': 'English', 'fa': 'Persian', 'fa-IR': 'Persian',
    'fil': 'Filipino', 'hi': 'Hindi',
    'ja': 'Japanese', 'pt': 'Portuguese', 'ur': 'Urdu', 'ur-Latn': 'Roman Urdu',
    'uz': 'Uzbek', 'uz-Latn': 'Uzbek · Latin', 'uz-Cyrl': 'Uzbek · Cyrillic',
    'vi': 'Vietnamese', 'zh': 'Chinese', 'zh-CN': 'Chinese (Simplified)',
}
DEFAULT_SITE = {
    'repository_url': 'https://github.com/blaghtayt-alt/Hadith-Bank',
    'live_url': 'https://blaghtayt-alt.github.io/Hadith-Bank/',
    'source_ref': 'main',
}
SHA256 = re.compile(r'[0-9a-fA-F]{64}\Z')
UI_COLOR_SCALES = ('jade', 'sand', 'gold')
UI_ICON_NAMES = (
    'reader', 'magnifying-glass', 'mixer-horizontal', 'download', 'external-link',
    'chevron-right', 'chevron-down', 'arrow-left', 'arrow-right', 'cross-2',
    'check', 'globe', 'file-text', 'reset', 'text',
)


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

    if 'language_versions' in record:
        from language_versions import validate_language_versions
        validate_language_versions(record['language_versions'], location)


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
    return value if parsed.scheme.lower() in ('https', 'http') and parsed.netloc and not parsed.username and not parsed.password else None


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
        label = ('Source number ' if number.get('numbering_system') else
                 'Number in source ' if has_noncanonical_numbering(number) else
                 'Number in collection ')
        items.append(label + text(number['in_book']))
    if isinstance(number, dict) and number.get('source_cited'):
        items.append('Cited: ' + text(number['source_cited']))
    if record.get('provider_entry_id') is not None:
        items.append('Source entry ' + text(record['provider_entry_id']))
    return ' · '.join(items) or 'Collection number not supplied'


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
    if page.get('docx_paragraphs'):
        items.append('DOCX paragraph ' + ', '.join(map(str, page['docx_paragraphs'])))
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


def citation_parts(item):
    if not isinstance(item, dict) or not any(item.get(k) for k in ('book_key', 'collection', 'source_citation', 'citation_raw')):
        return ['<pre>' + escaped(json.dumps(item, ensure_ascii=False, indent=2)) + '</pre>', '']
    collection = next((item[k] for k in ('collection', 'book_key')
                       if isinstance(item.get(k), str) and item[k]), 'Collection not established')
    def is_number(value):
        return (isinstance(value, str) and bool(value) or type(value) is int or
                type(value) is float and math.isfinite(value))
    # Citation numbers only: do not infer a canonical reference from a record's
    # local numbering, unparsed number_raw, or separately scoped cross-references.
    numbers = [item['number']] if is_number(item.get('number')) else item.get('numbers')
    number = ', '.join(str(value) for value in numbers if is_number(value)) if isinstance(numbers, list) else ''
    number = number or 'number not established'
    scope = item.get('scope')
    if isinstance(scope, str) and scope:
        scope = {'main_quote': 'Citation for this quotation', 'variant': 'Reference to a variant',
                 'commentary': 'Reference in commentary', 'unresolved': 'Reference not fully resolved'}.get(
                     scope, scope.replace('_', ' '))
    else:
        scope = item.get('citation_scope')
        scope = scope if isinstance(scope, str) and scope else 'Citation scope not supplied'
    result = ['<p><strong>' + escaped(collection) + ' · ' + escaped(number) + '</strong><br>' + escaped(scope) + '</p>', '']
    source_citation = next((item[k] for k in ('source_citation', 'citation_raw')
                            if isinstance(item.get(k), str) and item[k]), None)
    if source_citation:
        result += [prose(source_citation), '']
    for field, label in (('numbering_system', 'Numbering'), ('canonical_mapping_status', 'Canonical mapping')):
        if isinstance(item.get(field), str) and item[field]:
            result += [prose(label + ': ' + item[field].replace('_', ' ')), '']
    return result


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


def record_type_info(record):
    """Display an explicit source classification without inferring completeness."""
    kind = record.get('record_type') or record.get('content_kind')
    if not isinstance(kind, str):
        return None
    aliases = {'hadith_occurrence': 'hadith', 'main_hadith_occurrence': 'hadith',
               'translation_occurrence': 'hadith', 'quoted_hadith': 'hadith_excerpt',
               'hadith_quote': 'hadith_excerpt', 'quoted_companion_report': 'companion_report_excerpt'}
    kind = aliases.get(kind, kind)
    content_kind = record.get('content_kind')
    if content_kind == 'source_fragment':
        kind = 'source_fragment'
    elif content_kind == 'unnumbered_source_variant':
        kind = 'hadith_variant'
    elif content_kind == 'quoted_companion_saying':
        kind = 'companion_report_excerpt'
    elif content_kind == 'source_numbered_attributed_report':
        kind = 'source_report_or_saying'
    if (record.get('extraction') or {}).get('is_excerpt') is True:
        kind = {'hadith': 'hadith_excerpt', 'companion_report': 'companion_report_excerpt'}.get(kind, kind)
    kinds = {
        'hadith': ('Hadith', 'A narration preserved from the source.'),
        'hadith_variant': ('Hadith variant', 'A separately preserved variant narration in the source.'),
        'source_fragment': ('Source fragment', 'An incomplete narration fragment preserved as supplied by the source.'),
        'hadith_excerpt': ('Hadith excerpt', 'A quotation preserved from the source; it may contain only part of the narration.'),
        'hadith_meaning_excerpt': ('Reported meaning', 'The source presents this passage as the meaning of a hadith.'),
        'companion_report': ('Companion report', 'Words or a report attributed to a Companion in the source.'),
        'companion_report_excerpt': ('Companion report', 'An excerpt of words or a report attributed to a Companion in the source.'),
        'source_report_or_saying': ('Report or saying', 'The source attribution is explained separately for each language reading.'),
    }
    if kind not in kinds:
        return None
    label, note = kinds[kind]
    return {'label': label, 'note': note}


def markdown_record(record, index, bank_root=None, page_directory=None, downloads=None, site=None):
    from current_provenance import classification
    from build_discovery import occurrence_link
    source = record['source']
    provenance = record['translation_provenance']
    translator = record['translator']
    lines = ['## Narration ' + str(index), '']
    live = site_metadata({}, site)['live_url'].rstrip('/') + '/'
    lines += ['[Open this narration online](' + urljoin(live, occurrence_link(record, 'index.html')) + ')', '']
    if record.get('title'):
        lines += ['<p dir="' + text_direction(record.get('language')) + '"><strong>' + escaped(record['title']) + '</strong></p>', '']
    kind = record_type_info(record)
    if kind:
        lines += ['<p><strong>' + escaped(kind['label']) + '</strong> · ' + escaped(kind['note']) + '</p>', '']
    readings = language_readings(record)
    if not readings:
        lines += ['Text not supplied in this projection.', '']
    for reading in readings:
        direction = reading_direction(reading)
        lines += ['<section class="language-reading" lang="' + escaped(reading['language']) + '">',
                  '<h3>' + escaped(reading['heading']) + '</h3>', '']
        if reading['qualification']:
            lines += [prose(reading['qualification']), '']
        if reading['text']:
            for part in reading['quotation_parts'] or [{'text': reading['text']}]:
                if part.get('label'):
                    lines += ['<p class="counterpart-note">' + escaped(part['label']) + '</p>', '']
                for passage in part.get('passages') or [part]:
                    if passage.get('gap_before'):
                        lines += ['<p class="counterpart-note">Intervening source text is retained under Comments.</p>', '']
                    lines += [prose(passage['text'], direction), '']
        lines += [prose(reading['citation'], direction), '']
        version_source = reading['source']
        version_url = safe_url(version_source.get('record_url')) or safe_url(version_source.get('url'))
        credit = version_source.get('name') or 'Source not named'
        source_credit = ('<a href="' + escaped(version_url) + '" target="_blank" rel="noopener noreferrer">' +
                         escaped(credit) + '</a>') if version_url else escaped(credit)
        if reading['translation_origin'] is not None:
            source_credit += ' · Translation origin: ' + {'human': 'Human', 'ai': 'AI', 'unknown': 'Unknown'}[reading['translation_origin']]
        lines += ['<p><strong>Source:</strong> ' + source_credit + '</p>', '']
        if version_source.get('detail_metadata_status') == 'detail_metadata_pending':
            lines += [prose('Detailed source references and notes have not been retrieved yet.'), '']
        if reading['references']:
            lines += ['<details class="reading-references">', '<summary>' + escaped(reading['heading']) +
                      ' · references (' + str(len(reading['references'])) + ')</summary>', '']
            for reference in reading['references']:
                lines += citation_parts(reference)
                reference_url = safe_url(reference.get('url')) if isinstance(reference, dict) else None
                if reference_url and reference_url != version_url:
                    lines += ['<p><a href="' + escaped(reference_url) + '" target="_blank" rel="noopener noreferrer">Reference at source</a></p>', '']
            lines += ['</details>', '']
        if reading['comments']:
            lines += ['<details>', '<summary>' + escaped(reading['heading']) + ' · notes and commentary</summary>', '']
            for note in reading['comments']:
                value = note if isinstance(note, str) else note.get('text') if isinstance(note, dict) else None
                if value:
                    lines += [prose(value, direction), '']
                note_url = safe_url(note.get('source_url')) if isinstance(note, dict) else None
                if note_url:
                    lines += ['<p><a href="' + escaped(note_url) + '" target="_blank" rel="noopener noreferrer">Commentary source</a></p>', '']
            lines += ['</details>', '']
        upstream = version_source.get('upstream_sources') or []
        if upstream:
            lines += ['<details>', '<summary>Sources credited by this publisher</summary>', '']
            for item in upstream:
                if not isinstance(item, dict):
                    continue
                upstream_url = safe_url(item.get('url'))
                label = item.get('name') or upstream_url or 'Source not named'
                lines += ['<p>' + ('<a href="' + escaped(upstream_url) + '">' + escaped(label) + '</a>'
                                  if upstream_url else escaped(label)) + '</p>', '']
                if isinstance(item.get('scope'), str) and item['scope']:
                    lines += [prose(item['scope'].replace('_', ' ')), '']
            lines += ['</details>', '']
        lines += ['</section>', '']
    alignment_notes = counterpart_alignment_notes(record)
    if alignment_notes:
        lines += ['<details>', '<summary>Alignment notes</summary>', '']
        lines += [prose(note) for note in alignment_notes]
        lines += ['', '</details>', '']
    url = safe_url(source.get('record_url')) or safe_url(source.get('url'))
    source_name = source.get('name') or record['source_id']
    source_display = ('<a href="' + escaped(url) + '">' + escaped(source_name) + '</a>'
                      if url else escaped(source_name) + ' — source URL not supplied')
    translator_name = text(translator.get('name')) or 'Not named in the supplied source'
    label = {'human': 'Human', 'ai': 'AI', 'unknown': 'Unknown'}[classification(record)]
    lines += [
        '<p><strong>Source:</strong> ' + source_display + '<br>',
        '<strong>Collection:</strong> ' + escaped(collection_label(record['book_key'], record['language'])) +
        ' · <strong>Edition:</strong> ' + escaped(record['edition']) + '<br>',
        '<strong>Number:</strong> ' + escaped(number_label(record)) + '<br>',
        '<strong>Page:</strong> ' + escaped(page_label(record)) + '<br>',
        '<strong>Translator:</strong> ' + escaped(translator_name) + '<br>',
        '<strong>Narrator:</strong> ' + escaped(text((record.get('narrator') or {}).get('name')) or 'Not named in the supplied source') + '<br>',
        ('<strong>Translation origin:</strong> ' + escaped(label) if record.get('language', '').split('-')[0] != 'ar' else '') + '</p>', '',
    ]
    lines += ['<details><summary>Source translation-origin history</summary>', '',
              prose('Preserved source label: ' + text(provenance.get('label') or provenance.get('origin'))),
              prose('Preserved source AI-translation flag: ' + text(provenance.get('ai_translation'))),
              prose(provenance.get('scope_note') or 'No additional source-origin note supplied.'),
              '', '</details>', '']
    if record.get('source_headings'):
        lines += ['<p><strong>Source headings:</strong> ' + escaped(record['source_headings']) + '</p>', '']
    review = record.get('review') or {}
    current = review.get('current_policy') or {}
    review_fields = ['Historical import status: ' + text(review.get('status')),
                     'Historical independent Pro QC: ' + text(review.get('independent_pro_qc')),
                     'Release: ' + text(review.get('release_status'))]
    hide_qc = (record.get('display_policy') or {}).get('qc_tags') is False
    if not hide_qc:
        for badge in review_badges(record):
            lines += ['<p><strong>' + escaped(badge['label']) + '</strong></p>', '']
        if current.get('label'):
            review_fields.append('Recorded owner decision: ' + text(current['label']))
        lines += ['<details><summary>Original import and review history</summary>', '',
                  '<p>' + escaped(' · '.join(review_fields)) + '</p>', '',
                  prose('\n'.join(text(issue) for issue in review.get('issues', [])) or 'No source-alignment issues listed.'),
                  '', '</details>', '']
    commentary = record.get('commentary') or {}
    footnotes = record.get('footnotes') or []
    if any(commentary.values()) or footnotes:
        lines += ['<details>', '<summary>Commentary and footnotes</summary>', '']
        for language in ('translation', 'arabic'):
            if commentary.get(language):
                lines += [prose(commentary[language], text_direction(record.get('language'), language == 'arabic')), '']
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
                    lines += [prose(item, text_direction(record.get('language'), language == 'arabic')), '']
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
            elif key == 'items' and isinstance(value, list):
                for item in value:
                    reference_parts += citation_parts(item)
            elif isinstance(value, (dict, list)) and value:
                reference_parts += ['<p><strong>' + escaped(labels.get(key, key.replace('_', ' '))) + '</strong></p>',
                                    '<pre>' + escaped(json.dumps(value, ensure_ascii=False, indent=2)) + '</pre>', '']
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
    download = (downloads or {}).get(source.get('original_file'))
    if download:
        locator_parts.append('<p><a href="' + escaped(source_download_url(download['path'], site)) + '">' +
                             escaped(download['label']) + '</a></p>')
    issues = review.get('issues') or []
    lines += ['<details>', '<summary>' + ('Source locators and source notes' if hide_qc else 'Source locators and review issues') + '</summary>', '',
              ''.join(locator_parts), '',
              '<p><strong>' + ('Source notes:' if hide_qc else 'Review issues:') + '</strong></p>',
              prose('\n'.join(text(issue) for issue in issues) if issues else 'None listed in this record.'),
              '', '</details>', '', '---', '']
    return '\n'.join(lines)


def build_markdown(records, output, info, catalog=None, bank_root=None):
    from build_discovery import book_label, language_label
    output = Path(output).resolve()
    groups = collections.defaultdict(list)
    for record in records:
        key = tuple(component(record[field]) for field in ('language', 'book_key', 'edition'))
        groups[key].append(record)
    languages = collections.defaultdict(list)
    books = collections.defaultdict(list)
    written = []
    page_count = 0
    downloads = {item['path']: item for item in source_downloads(bank_root, records, catalog or {})} if bank_root else {}
    download_site = site_metadata(catalog or {})

    def save(relative, content):
        target = local(output, relative)
        write(target, content)
        written.append(relative)

    for (language, book, edition), items in sorted(groups.items()):
        label = language_label(language)
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
            body = ['# ' + escaped(label) + ' / ' + escaped(book_label(book, language)), '',
                    'Edition: `' + edition + '` · Narrations ' + str(start + 1) + '–' + str(end) +
                    ' of ' + str(len(items)) + '.', '', ' · '.join(nav), '']
            body.extend(markdown_record(r, start + i + 1, bank_root, output / directory, downloads, download_site)
                        for i, r in enumerate(items[start:end]))
            body += ['', ' · '.join(nav), '']
            save(directory + '/' + name, '\n'.join(body))
            page_links.append('- [Narrations ' + str(start + 1) + '–' + str(end) + '](' + name + ')')
            page_count += 1
        save(directory + '/README.md', '\n'.join([
            '# ' + escaped(label) + ' / ' + escaped(book_label(book, language)), '',
            *[prose(name) for name in sorted({r['source'].get('name') or r['source_id'] for r in items})], '',
            '[Read this edition online](' + download_site['live_url'].rstrip('/') + '/browse/' + directory + '/)', '',
            'Edition: `' + edition + '` · ' + str(len(items)) + ' source occurrences.', '',
            '[Book index](../README.md) · [Language index](../../README.md) · [All languages](../../../README.md)', '',
            'Each page contains up to 25 records. Source texts, versions and review flags remain separate.', '',
            *page_links, '',
        ]))
        books[(language, book)].append((edition, len(items)))
        languages[language].append((book, edition, len(items)))
    for (language, book), entries in sorted(books.items()):
        save(language + '/' + book + '/README.md', '\n'.join([
            '# ' + escaped(language_label(language)) + ' / ' + escaped(book_label(book, language)), '',
            '[Read this collection online](' + download_site['live_url'].rstrip('/') + '/browse/' + language + '/' + book + '/)', '',
            '[Language index](../README.md) · [All languages](../../README.md)', '',
            *['- [' + edition + '](' + edition + '/README.md) — ' + str(count) + ' source occurrences'
              for edition, count in entries], '',
        ]))
    for language, entries in sorted(languages.items()):
        grouped = collections.Counter()
        for book, edition, count in entries:
            grouped[book] += count
        save(language + '/README.md', '\n'.join([
            '# ' + escaped(language_label(language)), '', '[All languages](../README.md)', '',
            '[Browse this language online](' + download_site['live_url'].rstrip('/') + '/browse/' + language + '/)', '',
            *['- [' + escaped(book_label(book, language)) + '](' + book + '/README.md) — ' + str(count) + ' source occurrences'
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
                              ' · ' + escaped(collection_label(item.get('book_key') or '', item.get('language') or '')) + ' · ' + escaped(item.get('edition')) +
                              '<br>Source occurrences in separate package: ' + escaped(item.get('count')) +
                              '<br>Release status: ' + escaped(item.get('release_status')) +
                              '<br>' + escaped(item.get('location_note')) + '</p>', '']
        save('materials/private.md', '\n'.join(private_lines))
    save('README.md', '\n'.join([
        '# Hadith Bank — readable records', '',
        '[Browse books online](' + download_site['live_url'].rstrip('/') + '/browse/) · [Book and source-edition directory](../catalog/BOOKS.md)', '',
        str(len(records)) + ' source occurrences, organized by language, book and source edition.', '',
        'Open a language, then a book and edition. Every page shows up to 25 narrations with their source, '
        'translator, translation origin and OCR review where applicable. Arabic, commentary and audit details are expandable. '
        'Repeated narrations and source versions are retained.', '',
        *['- [' + language_label(language) + '](' + language + '/README.md) — ' +
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
        for key in ('repository_url', 'live_url', 'source_ref', 'build_commit', 'offline_reader_url'):
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
    if site.get('offline_reader_url') is not None and safe_url(site['offline_reader_url']) is None:
        raise ValueError('Reader offline_reader_url must be a safe HTTP(S) URL')
    return site


def source_download_label(relative):
    extension = PurePosixPath(relative).suffix.lower() if isinstance(relative, str) else ''
    return {'.doc': 'Download Word (.doc)', '.docx': 'Download Word (.docx)',
            '.pdf': 'Download PDF'}.get(extension)


def source_download_url(relative, site):
    """A direct GitHub file URL; validate both the ref and each path segment."""
    if (not isinstance(relative, str) or not relative or
            re.search(r'[\\:\x00-\x1f\x7f]', relative) or relative.startswith('/') or
            any(part in ('', '.', '..') for part in relative.split('/'))):
        raise ValueError('Unsafe source download path')
    if source_download_label(relative) is None:
        raise ValueError('Source download is not a Word or PDF file')
    settings = site_metadata({}, site)
    return (settings['repository_url'] + '/raw/' + quote(settings['source_ref'], safe='') + '/' +
            '/'.join(quote(part, safe='') for part in relative.split('/')))


def source_downloads(root, records, catalog):
    """List real preserved books; no inferred conversions or missing files."""
    root = Path(root).resolve()
    candidates = {}

    def origin(provenance):
        provenance = provenance or {}
        current = (provenance.get('current_policy') or {}).get('classification')
        if current in ('human', 'ai', 'unknown'):
            return current
        if provenance.get('ai_translation') is True:
            return 'ai'
        if provenance.get('ai_translation') is False or provenance.get('origin') in (
                'publisher_human_workflow', 'human_translator_credited'):
            return 'human'
        return 'unknown'

    def add(relative, sha256, language, book, name, origin):
        label = source_download_label(relative)
        if label is None:
            return
        item = candidates.setdefault(relative, {'path': relative, 'label': label, 'sha256': sha256,
            'language': language, 'book_key': book, 'source_name': name or PurePosixPath(relative).name,
            'translation_origin': origin})
        if sha256 and item.get('sha256') and sha256 != item['sha256']:
            raise ValueError('Conflicting source download hashes: ' + relative)
        if sha256:
            item['sha256'] = sha256

    for item in catalog.get('materials', []):
        if item.get('available_locally') is not False:
            add(item.get('source_file'), item.get('source_sha256'), item.get('language'),
                item.get('book_key'), item.get('source_name'),
                origin(item.get('translation_provenance')))
    for item in catalog.get('legacy_materials', []):
        if item.get('available_locally') is not False:
            add(item.get('path'), item.get('sha256'), item.get('language'), item.get('book_key'),
                item.get('source_name'), (item.get('current_policy') or {}).get('classification', 'unknown'))
    for record in records:
        source = record.get('source') or {}
        add(source.get('original_file'), source.get('sha256'), record.get('language'),
            record.get('book_key'), source.get('name'),
            origin(record.get('translation_provenance')))
    result = []
    for relative, item in sorted(candidates.items()):
        path = local(root, relative)
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        if item.get('sha256') and item['sha256'] != checksum:
            raise ValueError('Source download checksum mismatch: ' + relative)
        result.append({**item, 'sha256': checksum, 'bytes': path.stat().st_size})
    return result


def review_display_metadata(root):
    """Expose the current display decision separately from source review history."""
    path = local(root, 'catalog/review-policy.json')
    if not path.exists():
        return dict(DEFAULT_DISPLAY_POLICY)
    policy = parse_json(path.read_text(encoding='utf-8'))
    display = policy.get('reader_display', DEFAULT_DISPLAY_POLICY)
    if not isinstance(display, dict) or display.get('scope') != 'ocr_only':
        raise ValueError('Reader review policy must declare scope ocr_only')
    return display


def reader_ui_assets(directory):
    """Verify and inline pinned UI assets; the downloaded reader stays offline."""
    directory = Path(directory).resolve()
    manifest = parse_json(local(directory, 'vendor/manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema') != 'hadith-bank-vendored-ui-v1':
        raise ValueError('Unsupported reader UI vendor manifest')
    assets = {}
    for package in manifest['packages']:
        for entry in package['files']:
            relative = entry['path']
            if relative in assets:
                raise ValueError('Duplicate reader UI asset: ' + relative)
            raw = local(directory, 'vendor/' + relative).read_bytes()
            if (len(raw) != valid_count(entry.get('bytes'), 'UI asset bytes') or
                    hashlib.sha256(raw).hexdigest() != valid_hash(entry.get('sha256'), 'UI asset sha256')):
                raise ValueError('Reader UI asset checksum mismatch: ' + relative)
            assets[relative] = raw.decode('utf-8')
    expected = {'radix-colors/' + name + '.css' for name in UI_COLOR_SCALES}
    expected.update('radix-icons/' + name + '.svg' for name in UI_ICON_NAMES)
    expected.update(('radix-colors/LICENSE', 'radix-icons/LICENSE'))
    if set(assets) != expected:
        raise ValueError('Reader UI vendor manifest must contain exactly the pinned asset set')
    styles = []
    for name in ('radix-colors', 'radix-icons'):
        license_text = assets[name + '/LICENSE']
        if '*/' in license_text:
            raise ValueError('Reader UI license cannot contain a CSS comment delimiter')
        styles.append('/* ' + name + ' — MIT license\n' + license_text.rstrip() + '\n*/')
    styles.extend(assets['radix-colors/' + name + '.css'] for name in UI_COLOR_SCALES)
    styles.append(local(directory, 'reading-room.css').read_text(encoding='utf-8'))
    styles = '\n\n'.join(styles)
    if re.search(r'</style\b|@import\b|\burl\s*\(', styles, re.I):
        raise ValueError('Reader UI styles must be self-contained without imports or URL references')
    symbols = []
    svg_namespace = '{http://www.w3.org/2000/svg}'
    allowed_tags = {'svg', 'path', 'g', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon'}
    allowed_attributes = {
        'width', 'height', 'viewBox', 'fill', 'fill-rule', 'clip-rule', 'stroke',
        'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit',
        'fill-opacity', 'stroke-opacity', 'opacity', 'd', 'x', 'y', 'x1', 'y1',
        'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'points', 'transform',
    }
    for name in UI_ICON_NAMES:
        source = assets['radix-icons/' + name + '.svg']
        try:
            svg = ET.fromstring(source)
        except ET.ParseError as error:
            raise ValueError('Invalid reader UI SVG: ' + name) from error
        if svg.tag != svg_namespace + 'svg' or svg.get('viewBox') != '0 0 15 15':
            raise ValueError('Unexpected reader UI SVG viewport: ' + name)
        for element in svg.iter():
            if element.tag.removeprefix(svg_namespace) not in allowed_tags:
                raise ValueError('Unsupported reader UI SVG element: ' + name)
            if (set(element.attrib) - allowed_attributes or
                    any(re.search(r'url\s*\(', value, re.I) for value in element.attrib.values())):
                raise ValueError('Unsupported reader UI SVG attributes: ' + name)
        inner = re.fullmatch(r'\s*<svg\b[^>]*>(.*?)</svg>\s*', source, re.S)
        if inner is None:
            raise ValueError('Unexpected reader UI SVG wrapper: ' + name)
        # Keep the upstream path bytes; only replace the outer SVG with a symbol.
        presentation = ''.join(' ' + attribute + '="' + html.escape(svg.get(attribute), quote=True) + '"'
                               for attribute in ('fill', 'stroke') if svg.get(attribute) is not None)
        symbols.append('<symbol id="icon-' + name + '" viewBox="0 0 15 15"' +
                       presentation + '>' + inner.group(1) + '</symbol>')
    sprite = ('<svg id="hadith-ui-icons" xmlns="http://www.w3.org/2000/svg" '
              'aria-hidden="true" focusable="false" width="0" height="0" '
              'style="position:absolute;overflow:hidden;pointer-events:none">\n' +
              '\n'.join(symbols) + '\n</svg>')
    return styles, sprite


def render_template(template, replacements):
    """Replace each template marker exactly once without revisiting source text."""
    for marker in replacements:
        if template.count(marker) != 1:
            raise ValueError('Reader template must contain one ' + marker)
    pattern = '|'.join(re.escape(marker) for marker in replacements)
    return re.sub(pattern, lambda match: replacements[match.group(0)], template)


def discovery_navigation(records, site):
    """Crawlable links in the initial reader HTML, including without JavaScript."""
    from build_discovery import language_label
    base = site['live_url'].rstrip('/') + '/'
    languages = sorted({component(r['language']) for r in records})
    links = ''.join('<li><a href="' + escaped(base + 'browse/' + code + '/') + '">' +
                    escaped(language_label(code)) + '</a></li>' for code in languages)
    source_views = ('<p><a href="' + escaped(base + 'source-editions/fawaz/') +
                    '">Complete Fawaz source editions</a> — every acquired entry, including original source text outside the narration reader.</p>') if any(
                        str(record.get('source_id') or '').startswith('fawaz-') for record in records) else ''
    return ('<details class="discovery-nav"><summary>Browse languages and source books</summary>'
            '<p><a href="' + escaped(base + 'browse/') + '">All books and languages</a> · '
            '<a href="' + escaped(site['repository_url'] + '/blob/main/catalog/BOOKS.md') +
            '">Book and download directory on GitHub</a></p>'
            '<ul>' + links + '</ul><p>Each narration has its own reading page and source reference. '
            'These pages also work without JavaScript.</p>' + source_views + '</details>')


def discovery_head(records, site):
    names = [LANGUAGE_NAMES.get(code, code) for code in sorted({r['language'] for r in records})]
    description = ('Search hadith texts and source books in ' + ', '.join(names) +
                   '. Read source references and available Arabic/English counterparts; download preserved Word and PDF books.')
    canonical = site['live_url'].rstrip('/') + '/'
    title = 'Hadith Bank — Multilingual Hadith Texts and Source Books'
    return ('<title>' + escaped(title) + '</title>\n'
            '<meta name="description" content="' + escaped(description) + '">\n'
            '<link rel="canonical" href="' + escaped(canonical) + '">\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:title" content="' + escaped(title) + '">\n'
            '<meta property="og:description" content="' + escaped(description) + '">\n'
            '<meta property="og:url" content="' + escaped(canonical) + '">')


def compressed_reader_payload(records, max_embedded_bytes=None):
    """Stream compact JSON into gzip without allocating a full JSON copy."""
    if max_embedded_bytes is not None:
        valid_count(max_embedded_bytes, 'max_embedded_bytes')
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode='wb', compresslevel=6, mtime=0) as stream:
        stream.write(b'[')
        for position, record in enumerate(records):
            if position:
                stream.write(b',')
            stream.write(json.dumps(record, ensure_ascii=False, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8'))
            if max_embedded_bytes is not None and 4 * ((output.tell() + 2) // 3) > max_embedded_bytes:
                return None
        stream.write(b']')
    raw = output.getvalue()
    if max_embedded_bytes is not None and 4 * ((len(raw) + 2) // 3) > max_embedded_bytes:
        return None
    return base64.b64encode(raw).decode('ascii')


def write_reader_shards(records, output, directory, max_shard_bytes=MAX_READER_SHARD_BYTES,
                        publish=True):
    """Write bounded gzip JSONL pieces; a record may span several pieces."""
    if type(max_shard_bytes) is not int or not 1024 <= max_shard_bytes <= MAX_READER_SHARD_BYTES:
        raise ValueError('Reader shard size must be between 1024 and 2097152 bytes')
    output = Path(output).absolute()
    directory = Path(directory).absolute()
    try:
        relative = directory.relative_to(output.parent).as_posix()
    except ValueError as error:
        raise ValueError('Reader data directory must be inside the output directory') from error
    if relative == '.' or re.search(r'[%:?#\\\x00-\x1f\x7f]', relative):
        raise ValueError('Unsafe reader data directory')
    directory = local(output.parent, relative)
    manifest_path = local(output.parent, relative + '/manifest.json')
    previous = {}
    if manifest_path.exists():
        try:
            previous = parse_json(manifest_path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError):
            previous = {}
    directory.mkdir(parents=True, exist_ok=True)
    plain_limit = max_shard_bytes - max(256, max_shard_bytes // 128)
    pending = bytearray()
    shards, aggregate, record_count = [], hashlib.sha256(), 0

    def flush():
        if not pending:
            return
        plain = bytes(pending)
        compressed = gzip.compress(plain, compresslevel=6, mtime=0)
        if len(compressed) > max_shard_bytes:
            raise ValueError('Compressed reader shard exceeds its bound')
        digest = hashlib.sha256(compressed).hexdigest()
        name = 'part-' + str(len(shards) + 1).zfill(5) + '-' + digest[:16] + '.jsonl.gz'
        target = local(output.parent, relative + '/' + name)
        _atomic_reader_bytes(target, compressed)
        shards.append({'path': relative + '/' + name, 'sha256': digest,
                       'bytes': len(compressed), 'uncompressed_bytes': len(plain),
                       'count': plain.count(b'\n')})
        pending.clear()

    for record in records:
        raw = (json.dumps(record, ensure_ascii=False, separators=(',', ':'),
                          allow_nan=False) + '\n').encode('utf-8')
        aggregate.update(raw)
        record_count += 1
        offset = 0
        while offset < len(raw):
            take = min(plain_limit - len(pending), len(raw) - offset)
            pending.extend(raw[offset:offset + take])
            offset += take
            if len(pending) == plain_limit:
                flush()
    flush()
    manifest = {'schema': 'hadith-bank-reader-shards-v1', 'encoding': 'gzip-jsonl-shards',
                'record_count': record_count, 'jsonl_sha256': aggregate.hexdigest(),
                'max_shard_bytes': max_shard_bytes, 'shards': shards}
    if publish:
        _atomic_reader_manifest(manifest_path, manifest)
        _prune_reader_parts(output.parent, relative, previous, manifest)
    return manifest


class _ReaderStore:
    """Write content-addressed pieces without changing a published manifest."""

    def __init__(self, output_root, relative, max_shard_bytes, whole_rows):
        self.root, self.relative = output_root, relative
        self.directory = local(output_root, relative)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.limit = max_shard_bytes
        self.plain_limit = max_shard_bytes - max(256, max_shard_bytes // 128)
        self.whole_rows = whole_rows
        self.pending = bytearray()
        self.shards = []
        self.aggregate = hashlib.sha256()
        self.count = self.max_row_bytes = 0
        self.first = self.last = None

    def _flush(self):
        if not self.pending:
            return
        plain = bytes(self.pending)
        compressed = gzip.compress(plain, compresslevel=6, mtime=0)
        if len(compressed) > self.limit:
            raise ValueError('Compressed reader shard exceeds its bound: ' + self.relative)
        digest = hashlib.sha256(compressed).hexdigest()
        name = 'part-' + str(len(self.shards) + 1).zfill(5) + '-' + digest[:16] + '.jsonl.gz'
        relative = self.relative + '/' + name
        _atomic_reader_bytes(local(self.root, relative), compressed)
        part = {'path': relative, 'sha256': digest, 'bytes': len(compressed),
                'uncompressed_bytes': len(plain), 'count': plain.count(b'\n')}
        if self.whole_rows:
            part.update(first_ordinal=self.first, last_ordinal=self.last)
            if part['count'] != self.last - self.first + 1:
                raise ValueError('Noncontiguous reader projection rows: ' + self.relative)
        self.shards.append(part)
        self.pending.clear()
        self.first = self.last = None

    def add(self, raw, ordinal, identity):
        if ordinal != self.count or not raw.endswith(b'\n') or raw.count(b'\n') != 1:
            raise ValueError('Invalid ordered reader JSONL row: ' + self.relative)
        self.max_row_bytes = max(self.max_row_bytes, len(raw))
        if self.whole_rows:
            if len(raw) > self.plain_limit:
                raise ValueError('Reader projection row exceeds decoded shard limit: ' +
                                 self.relative + ', ordinal ' + str(ordinal) + ', id ' +
                                 str(identity)[:160] + ', bytes ' + str(len(raw)) +
                                 ', limit ' + str(self.plain_limit))
            if len(self.pending) + len(raw) > self.plain_limit:
                self._flush()
            if not self.pending:
                self.first = ordinal
            self.last = ordinal
            self.pending.extend(raw)
            if len(self.pending) == self.plain_limit:
                self._flush()
        else:
            offset = 0
            while offset < len(raw):
                take = min(self.plain_limit - len(self.pending), len(raw) - offset)
                self.pending.extend(raw[offset:offset + take])
                offset += take
                if len(self.pending) == self.plain_limit:
                    self._flush()
        self.aggregate.update(raw)
        self.count += 1

    def finish(self):
        self._flush()
        result = {'encoding': 'gzip-jsonl-shards', 'record_count': self.count,
                  'jsonl_sha256': self.aggregate.hexdigest(), 'max_shard_bytes': self.limit,
                  'shards': self.shards}
        if not self.whole_rows:
            result.update(schema='hadith-bank-reader-shards-v1', plain_part_bytes=self.plain_limit)
        return result


def _reader_manifest_parts(manifest):
    if not isinstance(manifest, dict):
        return []
    if manifest.get('schema') == 'hadith-bank-reader-shards-v1':
        stores = [manifest]
    elif manifest.get('schema') == 'hadith-bank-reader-lazy-v2':
        stores = [manifest.get(name) for name in ('directory', 'search', 'annotations', 'details')]
    else:
        return []
    return [part for store in stores if isinstance(store, dict)
            for part in (store['shards'] if isinstance(store.get('shards'), list) else [])
            if isinstance(part, dict)]


def _prune_reader_parts(root, relative, previous, current):
    retained = {part['path'] for part in _reader_manifest_parts(current)}
    parents = {relative, *(relative + '/' + name for name in ('directory', 'search', 'annotations', 'details'))}
    for part in _reader_manifest_parts(previous):
        candidate = part.get('path')
        if not isinstance(candidate, str) or candidate in retained:
            continue
        if (PurePosixPath(candidate).parent.as_posix() not in parents or
                not re.fullmatch(r'part-[0-9]{5,}-[0-9a-f]{16}\.jsonl\.gz', PurePosixPath(candidate).name)):
            continue
        try:
            target = local(root, candidate)
        except ValueError:
            continue
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == part.get('sha256'):
            target.unlink()


def _atomic_reader_bytes(path, data):
    """A failed write cannot truncate a part still named by the previous manifest."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, prefix='.reader-part-',
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _publish_reader_document(output, document, manifest_path=None, manifest=None):
    """Prepare both files before switching, retaining the prior playable pair.

    Parts are content-addressed and remain untouched until the HTML is installed.
    If the second replacement fails, restore the previous manifest from an already
    prepared file rather than requiring another allocation after a disk failure.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = []

    def stage(path, data):
        with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, prefix='.reader-publish-',
                                         suffix='.tmp', delete=False) as stream:
            candidate = Path(stream.name)
            temporary.append(candidate)
            stream.write(data)
        return candidate

    installed_manifest = False
    previous_manifest = None
    try:
        new_output = stage(output, document.encode('utf-8'))
        if manifest_path is not None:
            if manifest_path.exists():
                previous_manifest = stage(manifest_path, manifest_path.read_bytes())
            new_manifest = stage(manifest_path,
                (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
            os.replace(new_manifest, manifest_path)
            installed_manifest = True
        try:
            os.replace(new_output, output)
        except BaseException:
            if installed_manifest:
                if previous_manifest is not None:
                    os.replace(previous_manifest, manifest_path)
                else:
                    manifest_path.unlink()
            raise
    finally:
        for candidate in temporary:
            if candidate.exists():
                candidate.unlink()


def _atomic_reader_manifest(path, manifest):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.manifest-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(manifest, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def write_lazy_reader_shards(records, output, directory, max_shard_bytes=MAX_READER_SHARD_BYTES,
                             template_path=None, publish=True):
    """Project bounded search stores and an exact, addressable full-record store.

    The existing JSONL byte stream and gzip boundary algorithm are unchanged.
    Only the atomically replaced top-level manifest publishes the new stores;
    stale generated pieces are pruned after all projection and count checks pass.
    With publish=False, leave the existing manifest and chunks intact so build()
    can install its HTML and manifest together before pruning.
    """
    if type(max_shard_bytes) is not int or not 1024 <= max_shard_bytes <= MAX_READER_SHARD_BYTES:
        raise ValueError('Reader shard size must be between 1024 and 2097152 bytes')
    output, directory = Path(output).absolute(), Path(directory).absolute()
    try:
        relative = directory.relative_to(output.parent).as_posix()
    except ValueError as error:
        raise ValueError('Reader data directory must be inside the output directory') from error
    if relative == '.' or re.search(r'[%:?#\\\x00-\x1f\x7f]', relative):
        raise ValueError('Unsafe reader data directory')
    directory = local(output.parent, relative)
    manifest_path = local(output.parent, relative + '/manifest.json')
    previous = {}
    if manifest_path.exists():
        try:
            previous = parse_json(manifest_path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError):
            pass
        if not isinstance(previous, dict):
            previous = {}
    node = shutil.which('node')
    if node is None:
        raise ValueError('Node.js is required to build exact browser reader projections')
    projector = Path(__file__).resolve().with_name('reader_projection.js')
    template_path = Path(template_path) if template_path else projector.parents[1] / 'reader/template.html'
    stores = {name: _ReaderStore(output.parent, relative + '/' + name, max_shard_bytes, name != 'details')
              for name in ('directory', 'search', 'annotations', 'details')}
    compact = lambda value: (json.dumps(value, ensure_ascii=False, separators=(',', ':'),
                                       allow_nan=False) + '\n').encode('utf-8')
    errors, detail_spans = [], []
    # A draining thread avoids stdout/stdin pipe deadlock. The diagnostic file
    # keeps at most 64 KiB even if Node fails before our bounded error handler.
    with tempfile.TemporaryFile() as diagnostics:
        process = subprocess.Popen([node, str(projector), str(template_path)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        def feed():
            offset = 0
            try:
                for ordinal, record in enumerate(records):
                    raw = compact(record)
                    stores['details'].add(raw, ordinal, record.get('id'))
                    detail_spans.append([offset, len(raw)])
                    offset += len(raw)
                    process.stdin.write(raw)
            except BaseException as error:
                errors.append(error)
                # Do not let a failed input writer leave the reader waiting for
                # output from a child that is still processing buffered input.
                try:
                    process.terminate()
                except OSError:
                    pass
            finally:
                try:
                    process.stdin.close()
                except OSError:
                    pass

        def capture_errors():
            retained = 0
            try:
                while True:
                    chunk = process.stderr.read(8192)
                    if not chunk:
                        break
                    keep = chunk[:max(0, 65536 - retained)]
                    diagnostics.write(keep)
                    retained += len(keep)
            except (OSError, ValueError) as error:
                errors.append(error)

        feeder = threading.Thread(target=feed, name='reader-projection-input', daemon=True)
        collector = threading.Thread(target=capture_errors, name='reader-projection-errors', daemon=True)
        feeder.start()
        collector.start()
        received = 0
        try:
            # Each output contains three bounded rows. A corrupt projector must
            # not make an unbounded allocation before the row-size checks run.
            projection_limit = 3 * max_shard_bytes + 4096
            while True:
                raw = process.stdout.readline(projection_limit + 1)
                if not raw:
                    break
                if len(raw) > projection_limit or not raw.endswith(b'\n'):
                    raise ValueError('Reader projection output row exceeds its bound or lacks a newline')
                projected = parse_json(raw.decode('utf-8'))
                if (not isinstance(projected, list) or len(projected) != 4 or
                        type(projected[0]) is not int or projected[0] != received or
                        not isinstance(projected[1], dict) or
                        any(not isinstance(value, str) for value in projected[2:])):
                    raise ValueError('Invalid ordered reader projection output')
                ordinal, entry, search_key, annotation_key = projected
                if ordinal >= len(records) or any(entry.get(key) != records[ordinal].get(key)
                        for key in ('id', 'language', 'book_key', 'edition', 'source_id')):
                    raise ValueError('Reader projection occurrence identity mismatch')
                metadata = entry.get('_reader')
                if not isinstance(metadata, dict):
                    raise ValueError('Invalid reader directory metadata')
                locator = metadata.get('detail')
                if (not isinstance(locator, list) or len(locator) != 2 or
                        any(type(value) is not int or value < 0 for value in locator) or locator[1] == 0 or
                        ordinal >= len(detail_spans) or locator != detail_spans[ordinal]):
                    raise ValueError('Invalid reader detail byte locator')
                stores['directory'].add(compact(entry), ordinal, entry['id'])
                stores['search'].add(compact([ordinal, search_key]), ordinal, entry['id'])
                stores['annotations'].add(compact([ordinal, annotation_key]), ordinal, entry['id'])
                received += 1
            try:
                status = process.wait(timeout=5)
            except subprocess.TimeoutExpired as error:
                raise ValueError('Reader projection process did not exit after closing its output') from error
            feeder.join()
            collector.join()
            if errors and not isinstance(errors[0], BrokenPipeError):
                raise ValueError('Reader projection input failed: ' + str(errors[0])[:1000]) from errors[0]
            if status:
                diagnostics.seek(0)
                message = diagnostics.read(4096).decode('utf-8', 'replace').strip()
                raise ValueError('Reader projection process failed (' + str(status) + '): ' + message)
            if errors:
                raise ValueError('Reader projection input failed: ' + str(errors[0])[:1000]) from errors[0]
            if received != len(records) or stores['details'].count != received:
                raise ValueError('Reader projection record count mismatch')
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            feeder.join(timeout=5)
            collector.join(timeout=5)
            process.stdout.close()
            process.stderr.close()
    finished = {name: store.finish() for name, store in stores.items()}
    manifest = {'schema': 'hadith-bank-reader-lazy-v2', 'encoding': 'gzip-jsonl-lazy-v2',
                'record_count': len(records), 'jsonl_sha256': finished['details']['jsonl_sha256'],
                'max_shard_bytes': max_shard_bytes,
                'max_projection_row_bytes': {name: stores[name].max_row_bytes
                                             for name in ('directory', 'search', 'annotations')},
                'max_detail_record_bytes': stores['details'].max_row_bytes,
                **finished}
    if publish:
        _atomic_reader_manifest(manifest_path, manifest)
        _prune_reader_parts(output.parent, relative, previous, manifest)
    return manifest


def build(root, output, markdown_output=None, compress=True, site=None,
          data_directory=None, max_embedded_bytes=None, max_shard_bytes=MAX_READER_SHARD_BYTES):
    root = Path(root).resolve()
    output = Path(output).absolute()
    records, catalog, info = load_records(root)
    template_path = Path(__file__).resolve().parents[1] / 'reader' / 'template.html'
    template = template_path.read_text(encoding='utf-8')
    ui_styles, ui_icons = reader_ui_assets(template_path.parent)
    if output.is_symlink() or any(parent.is_symlink() for parent in output.parents):
        raise ValueError('Reader output must not use symlinks')
    metadata = {**info, 'title': catalog.get('title') or 'Hadith Bank',
                'materials': [{key: value for key, value in material.items() if key != 'supporting_files'}
                              for material in catalog.get('materials', [])],
                'language_names': LANGUAGE_NAMES, 'book_titles': title_metadata(),
                'site': site_metadata(catalog, site),
                'review_display_policy': review_display_metadata(root),
                'counterparts': catalog.get('counterparts'),
                'source_downloads': source_downloads(root, records, catalog),
                'legacy_materials': catalog.get('legacy_materials', []),
                'private_materials_not_in_this_tree': catalog.get('private_materials_not_in_this_tree', [])}
    if max_embedded_bytes is not None:
        valid_count(max_embedded_bytes, 'max_embedded_bytes')
    payload, manifest, manifest_path, previous_manifest = None, None, None, {}
    if data_directory is None:
        if compress:
            payload = compressed_reader_payload(records, max_embedded_bytes)
        else:
            payload = script_json(records)
            if max_embedded_bytes is not None and len(payload.encode('utf-8')) > max_embedded_bytes:
                payload = None
    if payload is None:
        directory = Path(data_directory) if data_directory is not None else output.parent / (output.stem + '-data')
        manifest = write_lazy_reader_shards(records, output, directory, max_shard_bytes, template_path,
                                            publish=False)
        relative = Path(directory).absolute().relative_to(output.parent).as_posix()
        manifest_path = local(output.parent, relative + '/manifest.json')
        if manifest_path.exists():
            try:
                previous_manifest = parse_json(manifest_path.read_text(encoding='utf-8'))
            except (ValueError, UnicodeError):
                previous_manifest = {}
        payload, encoding = script_json(manifest), manifest['encoding']
    else:
        encoding = 'gzip-base64' if compress else 'json'
    parts = _reader_manifest_parts(manifest) if manifest is not None else []
    metadata['data_delivery'] = {'encoding': encoding, 'self_contained': manifest is None,
                                 'shard_count': len(parts)}
    if manifest is not None:
        # records_sha256 remains the canonical input stream's hash. The hosted
        # detail stream is a compact serialization of those exact objects and
        # can legitimately have different JSON whitespace and a different hash.
        metadata['data_delivery']['jsonl_sha256'] = manifest['jsonl_sha256']
    lazy_store = (template_path.parent / 'lazy-store.js').read_text(encoding='utf-8') if '__HADITH_LAZY_STORE_JS__' in template else ''
    replacements = {'__HADITH_RECORDS_JSON__': payload,
                    '__HADITH_ENCODING__': encoding,
                    '__HADITH_SNAPSHOT_JSON__': script_json(metadata),
                    '__HADITH_UI_STYLES__': ui_styles, '__HADITH_UI_ICONS__': ui_icons,
                    '__HADITH_LAZY_STORE_JS__': lazy_store,
                    '__HADITH_DISCOVERY_HEAD__': discovery_head(records, metadata['site']),
                    '__HADITH_DISCOVERY_NAV__': discovery_navigation(records, metadata['site'])}
    document = render_template(template, replacements)
    _publish_reader_document(output, document, manifest_path, manifest)
    if manifest is not None:
        _prune_reader_parts(output.parent, relative, previous_manifest, manifest)
    result = {**info, 'html_output': str(output), 'html_bytes': output.stat().st_size,
              'source_text_modified': False,
              'network_dependencies': ['same-origin reader data shards'] if manifest is not None else [],
              'embedded_encoding': encoding, 'self_contained': manifest is None}
    if manifest is not None:
        directory = Path(data_directory).absolute() if data_directory is not None else output.parent / (output.stem + '-data')
        result.update(data_directory=str(directory), shard_manifest=str(directory / 'manifest.json'),
                      shard_count=len(parts), shard_bytes=sum(part['bytes'] for part in parts))
        if manifest['schema'] == 'hadith-bank-reader-lazy-v2':
            result['max_projection_row_bytes'] = manifest['max_projection_row_bytes']
            result['max_detail_record_bytes'] = manifest['max_detail_record_bytes']
            result['detail_shard_count'] = len(manifest['details']['shards'])
            result['directory_bytes'] = sum(part['uncompressed_bytes'] for part in manifest['directory']['shards'])
            result['reader_store_metrics'] = {
                name: {'record_count': manifest[name]['record_count'],
                       'shard_count': len(manifest[name]['shards']),
                       'compressed_bytes': sum(part['bytes'] for part in manifest[name]['shards']),
                       'uncompressed_bytes': sum(part['uncompressed_bytes'] for part in manifest[name]['shards']),
                       'max_row_bytes': (manifest['max_detail_record_bytes'] if name == 'details'
                                         else manifest['max_projection_row_bytes'][name])}
                for name in ('directory', 'search', 'annotations', 'details')}
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
    parser.add_argument('--data-directory', type=Path, help='Write same-origin gzip data shards and a hosted reader shell.')
    parser.add_argument('--max-embedded-bytes', type=int, help='Switch to data shards if the embedded payload exceeds this size.')
    args = parser.parse_args()
    try:
        result = build(args.root, args.output, args.markdown_output, compress=not args.uncompressed,
                       data_directory=args.data_directory, max_embedded_bytes=args.max_embedded_bytes)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Reader build failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())

