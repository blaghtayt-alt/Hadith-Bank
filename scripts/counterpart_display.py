"""Presentation of additive source counterparts; never infer a text match."""
from urllib.parse import urlsplit


def counterpart_data(record, language):
    values = record.get('counterparts') or {}
    value = values.get(language) if isinstance(values, dict) else None
    return value if (isinstance(value, dict) and isinstance(value.get('text'), str)
                     and value['text'].strip()) else None


def counterpart_source_data(record, language):
    """Include an explicit external-only source without claiming text is present."""
    data = counterpart_data(record, language)
    if data is not None:
        return data
    values = record.get('counterparts') or {}
    value = values.get(language) if isinstance(values, dict) else None
    if not isinstance(value, dict) or value.get('scope') != 'external_source':
        return None
    source_url = value.get('source_url')
    if not isinstance(source_url, str) or any(ord(c) < 32 for c in source_url):
        return None
    try:
        parsed = urlsplit(source_url)
        if (parsed.scheme in ('https', 'http') and parsed.hostname and
                parsed.username is None and parsed.password is None):
            return value
    except ValueError:
        pass
    return None


def counterpart_search_values(record):
    """Only public narration/citation fields belong in ordinary text search."""
    for language in ('arabic', 'english'):
        data = counterpart_source_data(record, language)
        if data is None:
            continue
        yield data.get('text')
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
    if data.get('match_status') == 'reviewed_parallel':
        notes.append('Reviewed source parallel; wording can differ between editions.')
    extraction = record.get('extraction') or {}
    quotation_evidence = (record.get('counterparts') or {}).get('quotation_evidence') or {}
    is_excerpt = (extraction.get('is_excerpt') is True or
                  'excerpt' in str(record.get('record_type') or record.get('content_kind') or '') or
                  quotation_evidence.get('relation') == 'source_excerpt')
    if data.get('scope') == 'source_entry':
        selected = 'Chinese source' if str(record.get('language') or '').lower().startswith('zh') else 'selected source'
        notes.append("May include the compiler's notes; the " + selected + ' can be an excerpt.')
    if data.get('scope') == 'source_excerpt':
        notes.append('Source excerpt; this parallel does not supply the complete source entry.')
    if data.get('scope') in ('full_narration', 'external_source') and is_excerpt:
        notes.append(('Linked source entry' if data.get('scope') == 'external_source'
                      else 'Full narration') + '; the selected source preserves an excerpt or reported meaning.')
    citation_note = data.get('citation_note')
    if isinstance(citation_note, str) and citation_note.strip():
        notes.append(citation_note.strip())
    return ' '.join(notes)


def counterpart_alignment_notes(record):
    values = record.get('counterparts') or {}
    if values.get('status') != 'reviewed_parallel':
        return []
    review = (values.get('quotation_evidence') or {}).get('review') or {}
    if review.get('human_review') is False:
        notice = 'Narration alignment checked by an automated assistant. No independent scholarly certification is claimed.'
    elif review.get('human_review') is True:
        notice = 'Narration alignment checked by a human reviewer. No independent scholarly certification is claimed.'
    else:
        notice = 'The alignment review process is not specified. No independent scholarly certification is claimed.'
    notes = review.get('qualifications') or []
    return [notice] + [note for note in notes if isinstance(note, str) and note.strip()]
