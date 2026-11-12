"""Validate and project independently attributed source language versions."""
import copy
import re
from urllib.parse import urlsplit

LANGUAGE = re.compile(r'[A-Za-z][A-Za-z0-9-]{0,63}\Z')


def validate_language_versions(versions, location='language_versions'):
    if not isinstance(versions, list):
        raise ValueError(location + ' must be an array')
    seen = set()
    for position, version in enumerate(versions):
        label = location + '[' + str(position) + ']'
        if not isinstance(version, dict):
            raise ValueError(label + ' must be an object')
        identity = version.get('id')
        if not isinstance(identity, str) or not identity.strip() or identity in seen:
            raise ValueError(label + ' requires a distinct stable version id')
        seen.add(identity)
        language = version.get('language')
        if not isinstance(language, str) or not LANGUAGE.fullmatch(language):
            raise ValueError(label + ' requires a language code')
        value = version.get('text')
        context_only = ((version.get('scope') == 'external_source' and version.get('quotation_status') in ('boundary_pending', 'attribution_pending'))
                        or (version.get('scope') == 'source_context' and version.get('quotation_status') == 'content_mismatch'))
        if context_only and value is not None:
            raise ValueError(label + ' cannot display unbounded source context as quotation text')
        if not context_only and (not isinstance(value, str) or not value.strip()):
            raise ValueError(label + ' requires supplied nonempty text')
        source = version.get('source')
        if not isinstance(source, dict) or not isinstance(source.get('name'), str) or not source['name'].strip():
            raise ValueError(label + ' requires its own named source')
        for field in ('url', 'record_url'):
            if source.get(field) is not None and not isinstance(source[field], str):
                raise ValueError(label + '.source.' + field + ' must be text or null')
        references = version.get('references', [])
        if not isinstance(references, list) or any(not isinstance(item, dict) for item in references):
            raise ValueError(label + '.references must be an object array')
        comments = version.get('comments', [])
        if not isinstance(comments, list) or any(not isinstance(item, (str, dict)) for item in comments):
            raise ValueError(label + '.comments must be an array of source strings or objects')
        if context_only:
            links = [source.get(field) for field in ('record_url', 'url')]
            if not any(isinstance(link, str) and urlsplit(link).scheme in ('http', 'https')
                       and urlsplit(link).netloc for link in links):
                raise ValueError(label + ' requires a safe source link for a pending quotation')
            if not any(isinstance(item, dict) and item.get('scope') == 'source_context_not_narration'
                       and isinstance(item.get('text'), str) and item['text'].strip() for item in comments):
                raise ValueError(label + ' requires preserved source context for a pending quotation')
        provenance = version.get('translation_provenance')
        if provenance is not None:
            if not isinstance(provenance, dict):
                raise ValueError(label + '.translation_provenance must be an object or null')
            flag = provenance.get('ai_translation', 'unknown')
            if type(flag) is not bool and flag != 'unknown':
                raise ValueError(label + ' has an invalid AI translation flag')
    return versions


def _quotation_status_qualification(version):
    if version.get('quotation_status') == 'content_mismatch':
        return ('This provider ID contains different material in this language. Its full source text is '
                'preserved under Comments and is not a translation or Arabic counterpart of the displayed narration.')
    if version.get('quotation_status') == 'boundary_pending':
        return ('This source combines narration and commentary. Its complete text is preserved '
                'under Comments while the narration boundary is reviewed.')
    if version.get('quotation_status') == 'attribution_pending':
        return ('The attribution in this language remains under review. Its complete source text is preserved '
                'under Comments; another language is not used to supply an unnamed speaker.')
    if version.get('quotation_status') == 'disjoint_source_spans':
        return ('This reading preserves separate source spans. Intervening source notes are retained under Comments.')
    if version.get('quotation_status') == 'abbreviated_source_report':
        return ('This edition abbreviates the report and explicitly refers to another source entry. '
                'The exact abbreviated wording is preserved here; open References for the cited report.')
    if version.get('quotation_status') == 'multiple_source_reports':
        count = (version.get('source') or {}).get('source_report_count', 2)
        label = str(count) if type(count) is int and count > 2 else 'two'
        return ('This source entry preserves ' + label + ' separately attributed reports in their original order. '
                'They remain one provider entry, with their distinct narrator introductions and source references.')
    return ''


def quotation_qualification(version):
    value = _quotation_status_qualification(version)
    source = version.get('source') or {}
    notes = [source.get(key) for key in ('report_classification_note', 'source_report_alignment_note')]
    groups = source.get('source_report_groups')
    if isinstance(groups, list) and any(isinstance(group, list) and len(group) > 1 for group in groups):
        notes.append('Some reports contain separate source passages. Intervening source text is retained under Comments.')
    return ' '.join(part for part in [value, *(note.strip() for note in notes if isinstance(note, str))] if part)


def quotation_parts(version):
    """Project exact source components as separate blocks without editing text.

    Source offsets count Unicode code points. The stored searchable quotation is
    their exact concatenation; presentation keeps reports and internal citations
    visibly separate. Incomplete legacy evidence falls back to the whole text.
    """
    text = version.get('text')
    source = version.get('source') or {}
    spans = source.get('text_spans') or {}
    if not isinstance(text, str) or not text:
        return []
    if 'source_report_groups' in source:
        groups = source['source_report_groups']
        if (not isinstance(groups, list) or not groups
                or any(not isinstance(group, list) or not group for group in groups)
                or type(source.get('source_report_count')) is not int
                or source['source_report_count'] != len(groups)
                or source.get('source_report_boundaries') is not None):
            return []
        flattened = [span for group in groups for span in group]
        if flattened != spans.get('quotation_spans'):
            return []
        previous = 0
        for span in flattened:
            if (not isinstance(span, list) or len(span) != 2
                    or any(type(value) is not int for value in span)
                    or not 0 <= previous <= span[0] < span[1]):
                return []
            previous = span[1]
        if sum(end - start for start, end in flattened) != len(text):
            return []
        cursor, result = 0, []
        for index, group in enumerate(groups):
            passages = []
            for position, span in enumerate(group):
                end = cursor + span[1] - span[0]
                passages.append({'text': text[cursor:end], 'source_span': span,
                                 'gap_before': position > 0 and group[position - 1][1] < span[0]})
                cursor = end
            result.append({'label': 'Source report ' + str(index + 1),
                           'text': ''.join(passage['text'] for passage in passages),
                           'source_spans': group, 'passages': passages})
        return result
    boundaries = source.get('source_report_boundaries')
    if version.get('quotation_status') == 'multiple_source_reports' and isinstance(boundaries, list):
        pairs = [(span, 'Source report ' + str(i + 1)) for i, span in enumerate(boundaries)]
        pairs += [(span, 'Source citation') for span in spans.get('retained_internal_citation_spans', [])]
    elif version.get('quotation_status') == 'disjoint_source_spans':
        boundaries = spans.get('quotation_spans')
        if not isinstance(boundaries, list):
            return []
        pairs = [(span, 'Source excerpt ' + str(i + 1)) for i, span in enumerate(boundaries)]
    else:
        return []
    if len(pairs) < 2 or any(not isinstance(span, list) or len(span) != 2 or
            any(type(value) is not int for value in span) or not 0 <= span[0] < span[1] for span, _ in pairs):
        return []
    pairs.sort(key=lambda pair: pair[0][0])
    if any(left[0][1] > right[0][0] for left, right in zip(pairs, pairs[1:])):
        return []
    if sum(span[1] - span[0] for span, _ in pairs) != len(text):
        return []
    cursor, result = 0, []
    for span, label in pairs:
        end = cursor + span[1] - span[0]
        result.append({'label': label, 'text': text[cursor:end], 'source_span': span})
        cursor = end
    return result


def project_language_versions(versions, default_policy=None):
    """Apply display policy to a copy, preserving original text and evidence."""
    from current_provenance import legacy_source, source_translation_declaration
    result = copy.deepcopy(validate_language_versions(versions))
    for version in result:
        if version['language'].split('-')[0].lower() == 'ar':
            continue
        provenance = version.setdefault('translation_provenance', {})
        if provenance is None:
            provenance = version['translation_provenance'] = {}
        provenance.setdefault('ai_translation', 'unknown')
        declaration = source_translation_declaration(version)
        if declaration:
            decision = copy.deepcopy(default_policy) if default_policy else {}
            decision.update(classification=declaration['classification'],
                            basis='explicit_source_translation_declaration',
                            source_declaration_evidence=declaration['evidence'])
            provenance['current_policy'] = decision
        elif default_policy and not legacy_source(version):
            provenance['current_policy'] = copy.deepcopy(default_policy)
    return result


def available_language_codes(record):
    """Return all locally supplied readings, including base/script filters."""
    from counterpart_display import counterpart_source_data
    codes = set()
    primary = record.get('language')
    if isinstance(primary, str) and primary:
        codes.add(primary)
    if record.get('text_arabic'):
        codes.add('ar')
    for key, code in (('arabic', 'ar'), ('english', 'en')):
        counterpart = counterpart_source_data(record, key)
        if counterpart and counterpart.get('text'):
            codes.add(code)
    for version in record.get('language_versions') or []:
        if isinstance(version, dict) and version.get('text') and isinstance(version.get('language'), str):
            codes.add(version['language'])
    for code in list(codes):
        if '-' in code:
            codes.add(code.split('-')[0])
    return sorted(codes)


def language_search_values(record, include_comments=False):
    """Keep commentary out of default narration searches."""
    for version in record.get('language_versions') or []:
        if not isinstance(version, dict):
            continue
        if include_comments:
            yield version.get('comments', [])
            continue
        for key in ('id', 'language', 'script', 'text', 'references'):
            yield version.get(key)
        source = version.get('source') or {}
        for key in ('name', 'url', 'record_url'):
            yield source.get(key)
