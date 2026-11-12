"""Non-mutating language views for one preserved source occurrence.

Explicit language versions keep their own sources and citations. Compatibility
fields are only suppressed when they are aliases of the same supplied version;
separate source occurrences and separately supplied versions are never merged.
"""
from counterpart_display import (counterpart_source_data, counterpart_citation,
                                 counterpart_qualification, counterpart_translation_origin)
from book_titles import book_label


LANGUAGE_LABELS = {
    'ar': 'Arabic', 'en': 'English', 'hi': 'Hindi', 'ur': 'Urdu',
    'ur-Latn': 'Roman Urdu', 'uz': 'Uzbek', 'uz-Latn': 'Uzbek · Latin',
    'uz-Cyrl': 'Uzbek · Cyrillic', 'ja': 'Japanese', 'fa': 'Persian',
    'fa-IR': 'Persian', 'fil': 'Filipino', 'vi': 'Vietnamese',
    'zh': 'Chinese', 'zh-CN': 'Chinese (Simplified)', 'pt': 'Portuguese',
    'bn': 'Bengali',
}


def _has_text(value):
    return isinstance(value, str) and bool(value.strip())


def _same_language(language, compatibility_language):
    return language == compatibility_language or (
        '-' not in compatibility_language and language.startswith(compatibility_language + '-'))


def _same_source(version, record):
    if version.get('match_status') == 'same_source_record':
        return True
    own, parent = version.get('source') or {}, record.get('source') or {}
    own_url, parent_url = own.get('record_url') or own.get('url'), parent.get('record_url') or parent.get('url')
    return bool(own_url and own_url == parent_url)


def _legacy_alias(versions, language, text, record):
    return any(_same_language(item['language'], language) and item.get('text') == text
               and _same_source(item, record) for item in versions)


def _origin(provenance):
    # Import lazily: current_provenance also uses the reader's input utilities.
    from current_provenance import classification
    return classification({'translation_provenance': provenance or {}})


def _legacy_citation(record, language):
    references = record.get('references') or {}
    items = references.get('items') if isinstance(references, dict) else None
    relevant = [item for item in (items or []) if isinstance(item, dict)
                and item.get('scope') not in ('commentary', 'unresolved')]
    if relevant:
        return counterpart_citation({'references': relevant}, 'arabic' if language == 'ar' else 'english')
    number = record.get('number') or {}
    label = book_label(record.get('book_key') or '', record.get('language') or '') or 'Collection not supplied'
    supplied = number.get('in_book')
    # A fallback number belongs to the selected source; it is never promoted to
    # a canonical collection number or inferred from an entry ID.
    number_label = 'Source number ' + str(supplied) if supplied is not None else 'hadith number not supplied'
    return '[' + label + ' · ' + number_label + ']'


def reading_direction(reading):
    language = str(reading.get('language') or '').replace('_', '-').lower()
    if 'latn' in language.split('-') or reading.get('script') == 'Latn':
        return 'ltr'
    return 'rtl' if language.split('-')[0] in ('ar', 'fa', 'ur') else 'auto'


def _view(item, *, role, primary=False, heading=None, citation=None, qualification=''):
    language = item.get('language') or ''
    arabic = language.split('-')[0] == 'ar'
    source = item.get('source') if isinstance(item.get('source'), dict) else {}
    references = item.get('references') if isinstance(item.get('references'), list) else []
    comments = item.get('comments') if isinstance(item.get('comments'), list) else []
    provenance = item.get('translation_provenance')
    return {
        'id': item.get('id'), 'language': language, 'script': item.get('script'),
        'text': item.get('text'), 'source': source, 'references': references,
        'comments': comments, 'translation_provenance': provenance,
        'scope': item.get('scope'), 'match_status': item.get('match_status'),
        'role': role, 'primary': primary,
        'heading': heading or LANGUAGE_LABELS.get(language, language),
        'citation': citation or counterpart_citation(item, 'arabic' if arabic else 'english'),
        'qualification': qualification,
        'translation_origin': None if arabic else _origin(provenance),
    }


def language_readings(record):
    """Return Arabic, English, and other supplied readings without editing data."""
    supplied = [item for item in (record.get('language_versions') or [])
                if isinstance(item, dict) and isinstance(item.get('language'), str)
                and item['language'] and (_has_text(item.get('text')) or item.get('scope') == 'external_source')]
    language = record.get('language') or ''
    original = record.get('text_translation')
    views = [_view(item, role='supplied', primary=(
        _same_language(item['language'], language) and item.get('text') == original and _same_source(item, record)))
        for item in supplied]
    references = record.get('references') or {}
    legacy_references = references.get('items', []) if isinstance(references, dict) else []
    commentary = record.get('commentary') or {}
    if _has_text(original) and not _legacy_alias(supplied, language, original, record):
        views.append(_view({
            'id': 'source-translation', 'language': language, 'text': original,
            'source': record.get('source') or {}, 'references': legacy_references,
            'comments': [commentary['translation']] if _has_text(commentary.get('translation')) else [],
            'translation_provenance': record.get('translation_provenance'),
            'scope': 'source_entry', 'match_status': 'same_source_record',
        }, role='source_translation', primary=True, citation=_legacy_citation(record, language)))
    arabic = record.get('text_arabic')
    if (_has_text(arabic) and not _legacy_alias(supplied, 'ar', arabic, record)
            and not (language.split('-')[0] == 'ar' and original == arabic)):
        views.append(_view({
            'id': 'source-arabic', 'language': 'ar', 'text': arabic,
            'source': record.get('source') or {}, 'references': legacy_references,
            'comments': [commentary['arabic']] if _has_text(commentary.get('arabic')) else [],
            'translation_provenance': None, 'scope': 'source_entry', 'match_status': 'same_source_record',
        }, role='source_arabic', primary=not _has_text(original), heading='Arabic source text',
            citation=_legacy_citation(record, 'ar')))
    for name, code in (('arabic', 'ar'), ('english', 'en')):
        data = counterpart_source_data(record, name)
        if data is None:
            continue
        # Suppress compatibility aliases only; keep every explicitly supplied version.
        if any(item['language'] == code and item.get('text') == data.get('text') and
               (item.get('source', {}).get('record_url') or item.get('source', {}).get('url')) == data.get('source_url')
               for item in supplied):
            continue
        suffix = {'external_source': ' · read at source', 'full_narration': ' · full narration',
                  'source_entry': ' source entry', 'source_excerpt': ' source excerpt'}.get(data.get('scope'), '')
        view = _view({
            'id': 'counterpart-' + name, 'language': code, 'text': data.get('text'),
            'source': {'name': data.get('source_name'), 'record_url': data.get('source_url')},
            'references': data.get('references'), 'comments': data.get('comments'),
            'translation_provenance': data.get('translation_provenance'),
            'scope': data.get('scope'), 'match_status': data.get('match_status'),
        }, role='counterpart', heading=name.title() + suffix,
            citation=counterpart_citation(data, name), qualification=counterpart_qualification(data, record))
        if code == 'en':
            view['translation_origin'] = counterpart_translation_origin(data)
        views.append(view)
    priority = lambda view: (0 if view['language'].split('-')[0] == 'ar' else
                             1 if view['language'].split('-')[0] == 'en' else
                             2 if view['primary'] else 3)
    return sorted(views, key=priority)


def available_languages(record):
    """Source language plus supplied locally available languages."""
    from language_versions import available_language_codes
    return available_language_codes(record)
