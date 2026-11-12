"""Describe actual reading availability independently of matching status.

A source can already contain Arabic while its English parallel is unresolved.
An external link is usable online but is never counted as stored quotation text.
No source records are changed by this report.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path

from counterpart_display import counterpart_source_data
from urllib.parse import urlsplit


FIELDS = ('total', 'arabic_text', 'arabic_link', 'arabic_available',
          'english_text', 'english_link', 'english_available',
          'missing_arabic', 'missing_english', 'both_text', 'both_available',
          'arabic_only', 'english_only', 'neither_available')


def has_text(value):
    return isinstance(value, str) and bool(value.strip())


def availability_for(record):
    """Return text / external_link / missing for each language, not QC claims."""
    language = str(record.get('language') or '').lower().split('-')[0]
    result = {}
    for key, code in (('arabic', 'ar'), ('english', 'en')):
        data = counterpart_source_data(record, key)
        source_text = (record.get('text_arabic') if key == 'arabic' else None)
        native_text = record.get('text_translation') if language == code else None
        versions = [item for item in record.get('language_versions') or [] if isinstance(item, dict)
                    and str(item.get('language', '')).split('-')[0].lower() == code]
        version_text = any(has_text(item.get('text')) for item in versions)
        version_link = False
        for item in versions:
            source = item.get('source') or {}
            url = source.get('record_url') or source.get('url')
            if item.get('scope') == 'external_source' and isinstance(url, str):
                try:
                    parsed = urlsplit(url)
                    version_link = version_link or (parsed.scheme in ('http', 'https') and bool(parsed.netloc) and not parsed.username and not parsed.password)
                except ValueError:
                    pass
        if version_text or has_text(source_text) or has_text(native_text) or data and has_text(data.get('text')):
            result[key] = 'text'
        elif data is not None or version_link:
            result[key] = 'external_link'
        else:
            result[key] = 'missing'
    return result


def empty_counts():
    return Counter({field: 0 for field in FIELDS})


def add_availability(counts, availability):
    counts['total'] += 1
    present = {}
    for language in ('arabic', 'english'):
        state = availability[language]
        present[language] = state != 'missing'
        if state == 'text':
            counts[language + '_text'] += 1
        elif state == 'external_link':
            counts[language + '_link'] += 1
        if present[language]:
            counts[language + '_available'] += 1
        else:
            counts['missing_' + language] += 1
    if all(availability[k] == 'text' for k in present):
        counts['both_text'] += 1
    if all(present.values()):
        counts['both_available'] += 1
    elif present['arabic']:
        counts['arabic_only'] += 1
    elif present['english']:
        counts['english_only'] += 1
    else:
        counts['neither_available'] += 1


def build_report(records):
    totals = empty_counts()
    languages = defaultdict(empty_counts)
    sources = {}
    for record in records:
        state = availability_for(record)
        language = record.get('language') or 'und'
        source_id = record.get('source_id') or 'unspecified'
        source = sources.setdefault(source_id, {
            'source_id': source_id, 'language': language,
            'book_key': record.get('book_key'), 'edition': record.get('edition'),
            'source_name': (record.get('source') or {}).get('name') or source_id,
            'counts': empty_counts(),
        })
        for counts in (totals, languages[language], source['counts']):
            add_availability(counts, state)
    return {
        'schema': 'hadith-bank-counterpart-availability-v1',
        'count_unit': 'preserved source occurrence',
        'totals': dict(totals),
        'by_language': {key: dict(value) for key, value in sorted(languages.items())},
        'by_source': {key: {**value, 'counts': dict(value['counts'])}
                      for key, value in sorted(sources.items())},
        'definitions': {
            'text': 'Nonempty preserved source text or a linked quotation is available in the bank.',
            'external_link': 'An explicit external-only source link is available; no text is stored.',
            'missing': 'Neither source text nor an accepted external-only source link is available.',
            'both_available': 'Arabic and English each have text or an accepted source link.',
            'matching_status': 'A separate alignment diagnostic; unresolved can coexist with source-supplied Arabic.',
        },
        'new_translations_created': False,
        'independent_translation_or_authenticity_certification': False,
    }


def _cell(value):
    return str(value or '').replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def markdown_report(report):
    total = report['totals']
    lines = [
        '# Arabic and English availability', '',
        'Generated from every registered source occurrence in this snapshot. '
        'This report is regenerated when books or reviewed language links change.', '',
        f"**{total['total']:,} source occurrences**: Arabic text {total['arabic_text']:,}; "
        f"English text {total['english_text']:,}; English source links {total['english_link']:,}.", '',
        'Text and external-only links are counted separately. An English source link requires '
        'an internet connection and does not add searchable English quotation text to the offline bank. '
        'An unresolved alignment can still have Arabic from its original book.', '',
        '## By language', '',
        '| Language | Occurrences | Arabic text | English text | English links | Missing Arabic | Missing English |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for language, counts in report['by_language'].items():
        lines.append('| ' + ' | '.join([_cell(language)] + [f'{counts[key]:,}' for key in
            ('total', 'arabic_text', 'english_text', 'english_link', 'missing_arabic', 'missing_english')]) + ' |')
    lines += ['', '## By source edition', '',
              '| Source edition | Language | Occurrences | Arabic text | English text | English links | Missing Arabic | Missing English |',
              '|---|---|---:|---:|---:|---:|---:|---:|']
    for source_id, source in report['by_source'].items():
        counts = source['counts']
        lines.append('| ' + ' | '.join([_cell(source_id), _cell(source['language'])] +
            [f'{counts[key]:,}' for key in ('total', 'arabic_text', 'english_text', 'english_link',
                                           'missing_arabic', 'missing_english')]) + ' |')
    lines += ['', '## Continuing the language integration', '',
              'New books enter the same resolver and availability report automatically. '
              'Missing language links remain explicit. Candidate parallels need source-bound review '
              'before they can supply text or external language links.', '',
              'See [the language-linking workflow](../docs/LANGUAGE-COUNTERPARTS.md) and '
              '[the generated review queue](counterpart-review/manifest.json). '
              'Numbering, narrator variants and source excerpts must retain their original scope.', '']
    return '\n'.join(lines)


def write_reports(root, records):
    report = build_report(records)
    directory = Path(root) / 'reports'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'counterpart-availability.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (directory / 'counterpart-availability.md').write_text(markdown_report(report), encoding='utf-8')
    return report
