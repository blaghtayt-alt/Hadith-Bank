"""Presentation of additive source counterparts; never infer a text match."""


def counterpart_data(record, language):
    values = record.get('counterparts') or {}
    value = values.get(language) if isinstance(values, dict) else None
    return value if (isinstance(value, dict) and isinstance(value.get('text'), str)
                     and value['text'].strip()) else None


def counterpart_search_values(record):
    """Only public narration/citation fields belong in ordinary text search."""
    for language in ('arabic', 'english'):
        data = counterpart_data(record, language)
        if data is None:
            continue
        yield data['text']
        yield data.get('citation')
        references = data.get('references')
        if not isinstance(references, list):
            continue
        for reference in references:
            if isinstance(reference, dict):
                for field in ('book_key', 'collection', 'collection_ar', 'number', 'source_citation'):
                    yield reference.get(field)


def counterpart_citation(data, language):
    supplied = data.get('citation')
    citation = supplied.strip() if isinstance(supplied, str) else ''
    if not citation and isinstance(data.get('references'), list):
        labels = []
        for reference in data['references']:
            if not isinstance(reference, dict):
                continue
            name = (reference.get('collection_ar') if language == 'arabic' else None)
            name = name or reference.get('collection') or reference.get('book_key')
            if not isinstance(name, str) or not name:
                continue
            number = reference.get('number')
            if type(number) not in (str, int, float) or str(number) == '':
                number = 'الرقم غير متوفر' if language == 'arabic' else 'number not supplied'
            labels.append(name + ' · ' + str(number))
        citation = '; '.join(labels)
    if not citation:
        citation = ('مرجع الحديث ورقمه غير متوفرين' if language == 'arabic'
                    else 'Collection and hadith number not supplied')
    return citation if citation.startswith('[') and citation.endswith(']') else '[' + citation + ']'


def counterpart_qualification(data, record):
    notes = []
    if data.get('match_status') == 'related_version':
        notes.append('Related publisher version: Arabic wording or revision differs from the linked source version.')
    extraction = record.get('extraction') or {}
    quotation_evidence = (record.get('counterparts') or {}).get('quotation_evidence') or {}
    is_excerpt = (extraction.get('is_excerpt') is True or
                  'excerpt' in str(record.get('record_type') or record.get('content_kind') or '') or
                  quotation_evidence.get('relation') == 'source_excerpt')
    if data.get('scope') == 'full_narration' and is_excerpt:
        notes.append('Full narration; the selected source preserves an excerpt or reported meaning.')
    return ' '.join(notes)
