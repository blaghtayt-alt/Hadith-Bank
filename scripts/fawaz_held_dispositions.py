"""Exact-source dispositions for reviewed Fawaz entries outside the reader.

A disposition never admits a report. Admission still requires a separate
hash-bound quotation decision and the normal importer classification. These
records distinguish completed exclusions/source gaps from unreviewed holds.
"""
import gzip
import io
import json

from fawaz_review_inputs import (
    INPUT_SCHEMA, MANIFEST_PATH, MAX_MEMBER_BYTES, MAX_RAW_BYTES,
    MAX_STORED_BYTES, _digest, _header, _json, _path, _read, _size,
    _verified, json_bytes, require, sha256,
)

SCHEMA = 'hadith-bank-fawaz-held-dispositions-v1'
SOURCE_GAPS = {'source_empty', 'source_placeholder', 'source_chain_without_matn'}
COMMENTARY = {'source_explanation_or_commentary', 'source_quran_and_legal_explanation'}
EXCLUSIONS = SOURCE_GAPS | COMMENTARY
COUNT_FIELDS = (
    'resolved_excluded_occurrences', 'resolved_source_gap_occurrences',
    'resolved_commentary_occurrences', 'unresolved_held_occurrences',
    'recovered_reviewed_occurrences',
)


def load_held_dispositions(root, *, repository, revision):
    """Load an optional compressed, size/hash-pinned review ledger."""
    path = _path(root, MANIFEST_PATH)
    if not path.exists():
        return {}
    manifest = _json(_read(path, MAX_MEMBER_BYTES, MANIFEST_PATH), MANIFEST_PATH)
    _header(manifest, repository, revision, INPUT_SCHEMA, MANIFEST_PATH)
    spec = manifest.get('held_dispositions')
    if spec is None:
        return {}
    stored = _verified(root, spec, MAX_STORED_BYTES)
    require(spec.get('compression') == 'gzip', 'Held dispositions must use gzip')
    size = _size(spec.get('raw_bytes'), MAX_RAW_BYTES, 'held dispositions')
    digest = _digest(spec.get('raw_sha256'), 'held dispositions')
    with gzip.GzipFile(fileobj=io.BytesIO(stored), mode='rb') as stream:
        raw = stream.read(size + 1)
    require(len(raw) == size and sha256(raw) == digest,
            'Held disposition expanded checksum or size mismatch')
    document = _json(raw, spec['path'])
    _header(document, repository, revision, SCHEMA, spec['path'])
    records = document.get('records')
    require(isinstance(records, list) and document.get('cohort_size') == len(records),
            'Held disposition cohort size mismatch')
    result = {}
    for record in records:
        require(isinstance(record, dict), 'Invalid held disposition')
        book, number = record.get('provider_book'), record.get('typed_hadithnumber')
        require(isinstance(book, str) and book and isinstance(number, str) and number,
                'Held disposition lacks its exact typed provider identity')
        key = book, number
        require(key not in result, 'Duplicate held disposition identity')
        require(record.get('review_status') == 'complete'
                and record.get('all_supplied_language_fields_checked') is True
                and isinstance(record.get('reason'), str) and record['reason'].strip(),
                'Held disposition lacks a complete source review and reason')
        action, category = record.get('disposition'), record.get('category')
        require((action == 'registered_source_report' and category == 'source_report_recovered')
                or (action == 'resolved_source_exclusion' and category in EXCLUSIONS),
                'Unsupported held disposition/category')
        fields = record.get('source_fields')
        require(isinstance(fields, list) and fields, 'Held disposition lacks source fields')
        require(record.get('reader_admission_requires_separate_positive_span_decisions') is True
                and record.get('source_gap_filled') is False,
                'A disposition cannot supply a missing report or admit a narration')
        result[key] = {**record, '_ledger_path': spec['path'], '_ledger_sha256': digest}
    return result


def verify_source_bindings(record, rows):
    """Bind all supplied fields, source rows and positions, including empties."""
    book = record['provider_book']
    expected = {}
    for field in record['source_fields']:
        key = field.get('provider_edition'), field.get('position')
        require(isinstance(key[0], str) and type(key[1]) is int and key[1] >= 0
                and key not in expected, 'Invalid or repeated disposition source field')
        expected[key] = field
    observed = set()
    for prefix, versions in rows.items():
        for version in versions:
            row, position = version['row'], version['position']
            key = prefix + '-' + book, position
            require(key in expected and key not in observed,
                    'Disposition source field inventory changed')
            observed.add(key)
            field = expected[key]
            snapshot = version.get('snapshot') or {
                'path': version.get('source_path'), 'sha256': version.get('source_sha256')}
            text = row['text']
            require(isinstance(text, str), 'Disposition source text is not a string')
            exact = {
                'source_path': snapshot['path'], 'source_sha256': snapshot['sha256'],
                'source_row_sha256': sha256(json_bytes(row)),
                'source_text_sha256': sha256(text.encode('utf-8')),
                'source_text_codepoints': len(text), 'source_text_utf8_bytes': len(text.encode('utf-8')),
                'source_text_is_empty': not bool(text.strip()),
                'checked_spans': [[0, len(text)]] if text else [],
                'source_numbering': {name: row.get(name) for name in ('hadithnumber', 'arabicnumber', 'reference')},
                'source_grades_as_supplied': row.get('grades', []),
            }
            require(all(field.get(name) == value for name, value in exact.items()),
                    'Disposition source row, wording, reference, grade or binding changed: ' + repr(key))
    require(observed == set(expected), 'Disposition lost a supplied source language or row')
    all_empty = all(field['source_text_is_empty'] for field in expected.values())
    require((record['category'] == 'source_empty') == all_empty,
            'Source-empty disposition disagrees with exact supplied fields')


def review_resolution_for_group(dispositions, book, number, rows, classification):
    record = (dispositions or {}).get((book, number))
    if record is None:
        return None
    verify_source_bindings(record, rows)
    positive = record['disposition'] == 'registered_source_report'
    require(classification['classification'] == ('hadith' if positive else 'held'),
            'Held disposition cannot change the independently classified reader admission')
    if positive:
        positive_fields = 0
        for field in record['source_fields']:
            prefix = field['provider_edition'].split('-', 1)[0]
            item = next(value for value in rows[prefix] if value['position'] == field['position'])
            if field['outcome'] == 'reviewed_report_passages':
                decision = item.get('reviewed_source_span') or {}
                require(decision.get('source_text_sha256') == field['source_text_sha256']
                        and bool(decision.get('quotation_spans')) and bool(decision.get('report_type')),
                        'Recovered disposition lacks its separate exact positive report decision')
                positive_fields += 1
            elif field['outcome'] == 'resolved_source_content_mismatch':
                require(item.get('quotation_status') == 'content_mismatch'
                        and not item['quotation'].strip() and item['notes'] == [item['row']['text']],
                        'Resolved language discrepancy was promoted or its source context changed')
            else:
                require(field['source_text_is_empty'],
                        'Recovered source has an unreviewed nonempty language field')
        require(positive_fields > 0, 'Recovered disposition has no positive report field')
    return {
        'status': 'registered_source_report' if positive else 'resolved_source_exclusion',
        'category': record['category'], 'reason': record['reason'],
        'semantic_review_pending': False,
        'source_gap_not_filled': record['category'] in SOURCE_GAPS,
        'source_fields_checked': len(record['source_fields']),
        'ledger_path': record['_ledger_path'], 'ledger_sha256': record['_ledger_sha256'],
        'scope': 'Exact supplied source fields; independent authenticity and already-registered sibling-language queues are separate.',
    }


def disposition_counts(ledger):
    counts = {field: 0 for field in COUNT_FIELDS}
    for item in ledger:
        resolution = item.get('review_resolution') or {}
        if item['classification']['classification'] == 'held':
            if resolution.get('status') == 'resolved_source_exclusion':
                counts['resolved_excluded_occurrences'] += 1
                key = ('resolved_source_gap_occurrences' if resolution['category'] in SOURCE_GAPS
                       else 'resolved_commentary_occurrences')
                counts[key] += 1
            else:
                counts['unresolved_held_occurrences'] += 1
        elif resolution.get('status') == 'registered_source_report':
            counts['recovered_reviewed_occurrences'] += 1
    return counts


def source_view_resolution_text(item):
    """Plain, visible review outcome; no blanket claim that source gaps are filled."""
    resolution = item.get('review_resolution') or {}
    if resolution.get('status') != 'resolved_source_exclusion':
        return None
    return ('Review complete. ' + resolution['reason'] +
            ' The complete original source entry and its references are preserved below.')


def audit_export_dispositions(audit):
    """Check written statuses against a completed exact-source fidelity audit."""
    import import_fawaz_bulk as source

    dispositions = load_held_dispositions(audit.root, repository=source.REPOSITORY,
                                          revision=source.REVISION)
    if not dispositions:
        return {'status': 'not_configured'}
    seen = set()
    totals = {field: 0 for field in COUNT_FIELDS}
    verified_fields = 0
    for book, progress in audit.progress['by_book'].items():
        with gzip.open(audit.root / source.IMPORT / 'classification' / (book + '.jsonl.gz'),
                       'rt', encoding='utf-8') as stream:
            ledger = [json.loads(line) for line in stream]
        with gzip.open(audit.root / source.IMPORT / 'held' / (book + '.jsonl.gz'),
                       'rt', encoding='utf-8') as stream:
            held = {item['typed_hadithnumber']: item for item in map(json.loads, stream)}
        for entry in ledger:
            number = entry['typed_hadithnumber']
            key = book, number
            if key not in dispositions:
                require('review_resolution' not in entry,
                        'Export claims an unrecorded semantic disposition')
                continue
            require(key not in seen, 'Export repeats a disposition identity')
            seen.add(key)
            rows = {}
            for prefix, positions in audit.groups[key].items():
                snapshot = audit.inputs['editions/' + prefix + '-' + book + '.json']
                for position in positions:
                    original = audit.row(book, prefix, position)
                    decision = audit.reviewed.get((book, prefix, number))
                    item = {'row': original, 'position': position, 'snapshot': snapshot}
                    if decision:
                        quote, notes, _ = source.apply_reviewed_span(original['text'], decision)
                        item.update(quotation=quote, notes=notes)
                        if decision.get('action') in ('source_context_only', 'source_attribution_pending'):
                            item['quotation_status'] = ('content_mismatch' if decision['action'] == 'source_context_only'
                                                        else 'attribution_pending')
                        else:
                            item['reviewed_source_span'] = decision
                    rows.setdefault(prefix, []).append(item)
            expected = review_resolution_for_group(dispositions, book, number, rows, entry['classification'])
            require(entry.get('review_resolution') == expected,
                    'Written classification ledger changed its source disposition')
            if number in held:
                require(held[number].get('review_resolution') == expected,
                        'Written held-source page changed its source disposition')
            verified_fields += expected['source_fields_checked']
        counts = disposition_counts(ledger)
        require(all(progress.get(field) == value for field, value in counts.items()),
                'Per-book held-disposition totals disagree with written source records')
        for field, value in counts.items():
            totals[field] += value
    require(seen == set(dispositions), 'A reviewed source disposition is absent from the export')
    require(all(audit.progress.get(field) == value for field, value in totals.items()),
            'Aggregate held-disposition totals disagree with written source records')
    require(totals['resolved_excluded_occurrences'] + totals['unresolved_held_occurrences']
            == audit.progress['held_occurrences'], 'Held accounting lost a source occurrence')
    return {'status': 'passed', 'reviewed_cohort_occurrences': len(seen),
            'verified_original_source_fields': verified_fields, **totals,
            'scope': 'Completed semantic dispositions for formerly held IDs; source gaps remain explicit and already-registered sibling-language queues are separate.'}


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    from validate_fawaz_sources import SourceAudit

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    audit = SourceAudit(args.root)
    audit.run()
    print(json.dumps(audit_export_dispositions(audit), sort_keys=True))
