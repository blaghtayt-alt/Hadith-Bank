"""Hash-bound, own-language report attribution for the expanded source scope."""

REPORT_TYPES = {
    'prophetic_report', 'companion_report', 'successor_report',
    'attributed_saying', 'historical_report', 'abbreviated_transmission',
    'mixed_attributed_reports',
}
SPEAKER_ROLES = {'prophet', 'companion', 'successor', 'other', 'unresolved'}
REPORT_METADATA_FIELDS = (
    'report_type', 'reported_speakers', 'report_classification_note',
    'report_component_classifications',
)


def validate_report_metadata(text, decision):
    """Reject invented speaker strings, out-of-quotation evidence and vague types.

    This validates the review's evidence binding, not the historical truth of
    an attribution. Legacy Prophetic-only decisions remain unchanged.
    """
    if 'report_type' not in decision:
        if any(key in decision for key in REPORT_METADATA_FIELDS[1:]):
            raise ValueError('Report attribution metadata requires a report type')
        return
    if decision['report_type'] not in REPORT_TYPES:
        raise ValueError('Unsupported source report type')
    if not isinstance(decision.get('report_classification_note'), str) or not decision['report_classification_note'].strip():
        raise ValueError('Reviewed report type needs a visible attribution explanation')
    quotations = decision.get('quotation_spans', [])

    def check_speakers(speakers, bounds):
        if not isinstance(speakers, list) or not speakers:
            raise ValueError('Reviewed report needs explicit source speaker metadata')
        for speaker in speakers:
            if not isinstance(speaker, dict) or speaker.get('role') not in SPEAKER_ROLES:
                raise ValueError('Unsupported source speaker role')
            name, spans = speaker.get('name_as_supplied'), speaker.get('source_spans')
            if not isinstance(spans, list):
                raise ValueError('Speaker evidence spans are required')
            for span in spans:
                if (not isinstance(span, list) or len(span) != 2
                        or not all(type(x) is int for x in span)
                        or not any(a <= span[0] < span[1] <= b for a, b in bounds)):
                    raise ValueError('Speaker evidence must lie inside its own source quotation')
            if name is None:
                if speaker['role'] != 'unresolved':
                    raise ValueError('An unnamed speaker must remain explicitly unresolved')
            elif (not isinstance(name, str) or not name.strip() or not spans
                    or not any(name in text[a:b] for a, b in spans)):
                raise ValueError('Speaker name must be copied from exact own-language evidence')

    check_speakers(decision.get('reported_speakers'), quotations)
    components = decision.get('report_component_classifications', [])
    if not isinstance(components, list):
        raise ValueError('Report component classifications must be a list')
    if decision['report_type'] == 'mixed_attributed_reports' and not components:
        raise ValueError('Mixed report types require component-level attribution')
    seen = set()
    boundaries = decision.get('source_report_boundaries') or quotations
    for component in components:
        span = component.get('span') if isinstance(component, dict) else None
        if (span not in boundaries or tuple(span) in seen
                or component.get('report_type') not in REPORT_TYPES - {'mixed_attributed_reports'}):
            raise ValueError('Report classification must match one exact source component')
        seen.add(tuple(span))
        check_speakers(component.get('reported_speakers'), [span])
    if decision['report_type'] == 'mixed_attributed_reports' and seen != {tuple(x) for x in boundaries}:
        raise ValueError('Every mixed source report needs its own classification')


def report_type_qualification(source):
    """The reviewer supplies the precise source-specific wording for display."""
    note = source.get('report_classification_note')
    return note.strip() if isinstance(note, str) else ''
