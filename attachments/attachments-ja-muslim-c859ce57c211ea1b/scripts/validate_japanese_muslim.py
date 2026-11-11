#!/usr/bin/env python3
"""Independent mechanical validation of the Japanese Muslim attachment intake.

This validates source-byte, schema, text-span and export consistency. It does not
certify visual character fidelity, semantic narration boundaries or authenticity.
Offsets are Python Unicode codepoints into each source line plus its terminal LF.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE_SHA256 = 'c859ce57c211ea1bfddb98b268241da25fe077782dd4d6be4cd9e10628b18d6a'
ROLES = {'front_matter', 'colophon', 'section_heading', 'section_title',
         'section_footnote', 'printed_reference', 'translation', 'footnote', 'commentary'}
RECORD_ROLES = {'translation', 'footnote', 'commentary'}
PRINT_RE = re.compile(r'^[１２３123]巻\s*[PＰpｐ][.．。]?\s*\d')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def span_key(span):
    return (span.get('line_id'), span.get('start'), span.get('end'),
            span.get('role'), span.get('component_id'))


def run(args):
    errors, warnings = [], []
    checks = {}
    report = {
        'validator': 'independent-japanese-muslim-mechanical-v1',
        'scope': 'mechanical_source_and_structure_validation_only',
        'independent_pro_visual_qc_performed': False,
        'visual_character_coverage_claimed': False,
        'semantic_boundary_certification_claimed': False,
        'source_fidelity_status': 'embedded_text_and_span_consistency_only',
        'inputs': {}, 'checks': checks, 'errors': errors, 'warnings': warnings,
    }

    def err(code, **detail):
        errors.append({'code': code, **detail})

    def warn(code, **detail):
        warnings.append({'code': code, **detail})

    for field in ['pdf', 'lines', 'pages', 'schema', 'records', 'jsonl', 'ledger', 'sections', 'metadata']:
        value = getattr(args, field, None)
        if value:
            p = Path(value)
            try:
                display_path = p.resolve().relative_to(Path(args.root).resolve()).as_posix()
            except ValueError:
                display_path = str(p)
            report['inputs'][field] = {'path': display_path, 'sha256': sha(p), 'bytes': p.stat().st_size}
    if report['inputs']['pdf']['sha256'] != SOURCE_SHA256:
        err('source_pdf_sha256_mismatch', expected=SOURCE_SHA256, actual=report['inputs']['pdf']['sha256'])

    lines = load_jsonl(args.lines)
    ids = [x.get('id') for x in lines]
    repeated_ids = [k for k, n in Counter(ids).items() if n != 1]
    if repeated_ids:
        err('source_line_ids_not_unique', ids=repeated_ids)
    lm = {x['id']: x for x in lines}
    order = {x['id']: i for i, x in enumerate(lines)}
    by_page = defaultdict(list)
    for line in lines:
        by_page[line['pdf_page']].append(line)
    pages = load_json(args.pages)
    pm = {x['pdf_page']: x['text'] for x in pages}
    if len(pm) != len(pages):
        err('raw_page_numbers_not_unique')
    if sorted(pm) != list(range(1, 581)):
        err('raw_page_range_not_1_to_580', observed=sorted(pm))
    try:
        import fitz
        doc = fitz.open(args.pdf)
        checks['pdf_page_count'] = len(doc)
        if len(doc) != 580:
            err('source_pdf_page_count_mismatch', observed=len(doc), expected=580)
        checks['fresh_pdf_text_pages_compared'] = 0
        for n in sorted(pm):
            if n < 1 or n > len(doc):
                err('raw_page_outside_pdf', pdf_page=n)
                continue
            fresh = doc[n-1].get_text()
            checks['fresh_pdf_text_pages_compared'] += 1
            if fresh != pm[n]:
                err('raw_page_not_equal_fresh_embedded_text', pdf_page=n)
        doc.close()
    except ImportError:
        err('pymupdf_missing_cannot_independently_compare_pdf')
    for n, text in pm.items():
        reconstructed = ''.join(line['text'] + '\n' for line in by_page[n])
        if reconstructed != text:
            err('line_reconstruction_not_equal_raw_page', pdf_page=n)
        for i, line in enumerate(by_page[n], start=1):
            if line['line_index'] != i:
                err('line_index_out_of_sequence', line_id=line['id'], expected=i)
            offset = line.get('page_char_start')
            if not isinstance(offset, int) or text[offset:offset+len(line['text'])] != line['text']:
                err('source_line_offset_mismatch', line_id=line['id'])
    checks['source_lines_checked'] = len(lines)
    checks['source_characters_including_lf'] = sum(len(x['text']) + 1 for x in lines)
    print_lines = {x['id']: x for x in lines if PRINT_RE.match(x['text'].strip())}
    checks['printed_reference_lines_detected'] = len(print_lines)
    if len(print_lines) != 327:
        warn('printed_reference_regex_count_differs_from_observed_327', observed=len(print_lines))
    if any(not x['text'].lstrip().startswith(('1巻','１巻')) for x in print_lines.values()):
        err('print_declaration_outside_volume_1')

    if not args.records:
        report['status'] = 'passed' if not errors else 'failed'
        return report

    records = load_json(args.records)
    if not isinstance(records, list):
        err('records_json_is_not_array')
        report['status'] = 'failed'
        return report
    rids = [r.get('id') for r in records]
    rm = {r.get('id'): r for r in records}
    dup_ids = [k for k, n in Counter(rids).items() if n > 1]
    if dup_ids:
        err('duplicate_record_ids', ids=dup_ids)
    checks['records_checked'] = len(records)
    checks['unique_record_ids'] = len(rm)
    if args.jsonl:
        jl = load_jsonl(args.jsonl)
        if jl != records:
            err('json_and_jsonl_records_differ', json_count=len(records), jsonl_count=len(jl))
        checks['json_jsonl_equal'] = jl == records
    else:
        warn('jsonl_not_supplied')

    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator(load_json(args.schema))
        for idx, r in enumerate(records):
            for e in validator.iter_errors(r):
                err('record_schema_error', record_index=idx, record_id=r.get('id'),
                    path='/'.join(map(str, e.path)), message=e.message)
        checks['record_schema_validated'] = True
    except ImportError:
        err('jsonschema_missing')

    if not args.ledger:
        err('line_attribution_ledger_not_supplied')
        report['status'] = 'failed'
        return report
    ledger = load_jsonl(args.ledger)
    assigned = defaultdict(list)
    by_record = defaultdict(list)
    by_section = defaultdict(list)
    span_reconstruction = {}
    for index, row in enumerate(ledger):
        lid = row.get('line_id')
        if lid not in lm:
            err('ledger_unknown_line_id', ledger_index=index, line_id=lid)
            continue
        line = lm[lid]
        data = line['text'] + '\n'
        start, end = row.get('start'), row.get('end')
        if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(data)):
            err('ledger_invalid_character_span', ledger_index=index, line_id=lid, start=start, end=end, line_characters=len(data))
            continue
        if row.get('text') != data[start:end]:
            err('ledger_text_not_exact_source_slice', ledger_index=index, line_id=lid)
        if row.get('pdf_page') != line['pdf_page']:
            err('ledger_pdf_page_mismatch', ledger_index=index, line_id=lid)
        if row.get('role') not in ROLES:
            err('ledger_unknown_role', ledger_index=index, role=row.get('role'))
        assigned[lid].append((start, end, index))
        span_reconstruction[(lid, start, end)] = data[start:end]
        if row.get('record_id') is not None:
            if row['record_id'] not in rm:
                err('ledger_unknown_record_id', ledger_index=index, record_id=row['record_id'])
            by_record[row['record_id']].append(row)
        elif row.get('role') in RECORD_ROLES:
            err('narration_component_without_record_owner', ledger_index=index, line_id=lid, role=row.get('role'))
        if row.get('section_id') is not None:
            by_section[row['section_id']].append(row)
    coverage_gaps, overlaps = [], []
    for lid, line in lm.items():
        spans = sorted(assigned[lid])
        cursor = 0
        for start, end, index in spans:
            if start > cursor:
                coverage_gaps.append({'line_id': lid, 'start': cursor, 'end': start})
            elif start < cursor:
                overlaps.append({'line_id': lid, 'start': start, 'end': min(cursor, end), 'ledger_index': index})
            cursor = max(cursor, end)
        limit = len(line['text']) + 1
        if cursor < limit:
            coverage_gaps.append({'line_id': lid, 'start': cursor, 'end': limit})
    if coverage_gaps:
        err('unassigned_source_character_ranges', ranges=coverage_gaps)
    if overlaps:
        err('multiply_assigned_source_character_ranges', ranges=overlaps)
    checks['ledger_spans_checked'] = len(ledger)
    checks['attributed_characters'] = sum(row['end']-row['start'] for row in ledger if isinstance(row.get('end'), int) and isinstance(row.get('start'), int))
    checks['unassigned_character_ranges'] = len(coverage_gaps)
    checks['overlapping_character_ranges'] = len(overlaps)
    checks['ledger_role_counts'] = dict(Counter(row.get('role') for row in ledger))

    section_table = None
    if args.sections:
        sc = load_json(args.sections)
        if isinstance(sc, dict):
            sc = sc.get('sections', sc.get('items', []))
        if isinstance(sc, list):
            section_table = {s.get('id',s.get('section_id')): s for s in sc}
            checks['sections_in_catalog'] = len(section_table)
        else:
            err('sections_not_array_or_sections_envelope')
    previous_source_position = None
    for idx, r in enumerate(records):
        rid = r.get('id')
        if r.get('record_id') != rid or r.get('occurrence_id') != rid:
            err('record_identity_alias_mismatch', record_id=rid)
        if r.get('language') != 'ja' or r.get('source_language_code') != 'ja':
            err('record_language_not_ja', record_id=rid)
        if r.get('ai_translation') is not False:
            err('published_human_translation_flag_not_false', record_id=rid)
        tp = r.get('translation_provenance')
        if tp is not None:
            if tp.get('ai_translation') is not False:
                err('translation_provenance_flag_inconsistent', record_id=rid)
            if not tp.get('evidence_ids') and not tp.get('evidence'):
                err('human_translation_provenance_has_no_evidence', record_id=rid)
        else:
            warn('record_translation_provenance_absent', record_id=rid)
        for number_field in ['in_book', 'canonical', 'printed_label']:
            if r.get('number', {}).get(number_field) is not None:
                err('unsupported_hadith_number_for_unnumbered_pdf', record_id=rid, field=number_field, value=r['number'][number_field])
        if r.get('source', {}).get('sha256') != SOURCE_SHA256:
            err('record_source_sha256_mismatch', record_id=rid)
        for path_field in ['package_file']:
            val = r.get('source', {}).get(path_field)
            if val and (Path(val).is_absolute() or '..' in Path(val).parts):
                err('unsafe_source_local_path', record_id=rid, field=path_field, value=val)
        spans = r.get('provenance', {}).get('source_spans', [])
        expected = by_record.get(rid, [])
        if Counter(map(span_key, spans)) != Counter(map(span_key, expected)):
            err('record_spans_disagree_with_primary_ledger', record_id=rid,
                record_span_count=len(spans), ledger_span_count=len(expected))
        positions = [(order.get(s.get('line_id'), -1), s.get('start', -1)) for s in spans]
        if positions != sorted(positions):
            err('record_spans_out_of_source_order', record_id=rid)
        if positions:
            first = positions[0]
            if previous_source_position is not None and first <= previous_source_position:
                err('records_not_in_source_order', record_id=rid)
            previous_source_position = first
        else:
            err('record_has_no_source_spans', record_id=rid)
        parts = []
        translation_parts = []
        for s in spans:
            key = (s.get('line_id'), s.get('start'), s.get('end'))
            if key not in span_reconstruction:
                err('record_span_not_in_ledger', record_id=rid, span=s)
                continue
            part = span_reconstruction[key]
            parts.append(part)
            if s.get('role') == 'translation':
                translation_parts.append(part)
        reconstructed = ''.join(parts)
        if r.get('source_unit_text_verbatim') != reconstructed:
            err('record_source_unit_text_mismatch', record_id=rid)
        translation_reconstructed = ''.join(translation_parts)
        if r.get('text', {}).get('translation') != translation_reconstructed:
            err('translation_not_exact_translation_span_concatenation', record_id=rid)
        actual_pages = sorted({lm[s['line_id']]['pdf_page'] for s in spans if s.get('line_id') in lm})
        if r.get('page', {}).get('pdf') != actual_pages:
            err('record_page_list_not_equal_source_span_pages', record_id=rid,
                actual=r.get('page', {}).get('pdf'), expected=actual_pages)
        section_id = r.get('book', {}).get('section_id')
        if section_id is None:
            err('record_section_id_missing', record_id=rid)
        elif section_table is not None and section_id not in section_table:
            err('record_section_id_not_in_catalog', record_id=rid, section_id=section_id)
        row_sections = {row.get('section_id') for row in expected}
        if row_sections and row_sections != {section_id}:
            err('record_section_disagrees_with_ledger', record_id=rid, section_id=section_id, ledger_section_ids=list(row_sections))
        page = r.get('page', {})
        if page.get('printed_reference_scope') != 'section':
            err('printed_page_scope_not_section', record_id=rid)
        print_id = page.get('printed_reference_line_id')
        if print_id not in print_lines:
            err('printed_reference_line_not_source_declaration', record_id=rid, line_id=print_id)
        else:
            printed = page.get('printed', [])
            if printed and printed != [print_lines[print_id]['text']]:
                err('printed_pages_not_verbatim_section_declaration', record_id=rid, observed=printed, expected=[print_lines[print_id]['text']])
            if section_id is not None:
                declaration_sections = {row.get('section_id') for row in ledger if row.get('line_id') == print_id and row.get('role') == 'printed_reference'}
                if declaration_sections != {section_id}:
                    err('print_reference_belongs_to_other_section', record_id=rid, declaration_sections=list(declaration_sections), section_id=section_id)
        review = r.get('review', {})
        if review.get('independent_pro_qc') != 'pending' or review.get('release_eligible') is not False:
            err('record_overstates_release_or_review', record_id=rid)

    # Validate every auxiliary representation against its primary source spans.
    component_count = 0
    arabic_fragment_count = 0
    relationship_count = 0
    declared_component_ids = []

    def span_text(spans):
        pieces = []
        for span in spans:
            lid, start, end = span.get('line_id'), span.get('start'), span.get('end')
            if lid not in lm or not isinstance(start, int) or not isinstance(end, int):
                return None
            pieces.append((lm[lid]['text'] + '\n')[start:end])
        return ''.join(pieces)

    for r in records:
        rid = r['id']
        primary = r['provenance']['source_spans']
        if r['provenance'].get('source_sha256') != SOURCE_SHA256:
            err('provenance_source_sha256_mismatch', record_id=rid)
        if r['provenance'].get('ai_generated_translation') is not False:
            err('extraction_provenance_claims_generated_translation', record_id=rid)
        if r['provenance'].get('source_line_ids') != list(dict.fromkeys(x['line_id'] for x in primary)):
            err('source_line_id_list_not_equal_span_order', record_id=rid)
        component_spans = []
        for role, items in [('footnote', r['footnotes']), ('commentary', r['commentary']['items'])]:
            for item in items:
                component_count += 1
                note_id = item.get('note_id')
                declared_component_ids.append(note_id)
                spans = item.get('source_spans', [])
                if item.get('text_verbatim') != span_text(spans):
                    err('component_text_not_equal_source_spans', record_id=rid, note_id=note_id)
                if item.get('attached_record_id') != rid:
                    err('component_record_attachment_mismatch', record_id=rid, note_id=note_id)
                if any(x.get('role') != role or x.get('component_id') != note_id for x in spans):
                    err('component_role_or_id_mismatch', record_id=rid, note_id=note_id)
                expected = [x for x in primary if x.get('role') == role and x.get('component_id') == note_id]
                if Counter(map(span_key, spans)) != Counter(map(span_key, expected)):
                    err('component_spans_not_equal_record_primary_spans', record_id=rid, note_id=note_id)
                note_pages = sorted({lm[x['line_id']]['pdf_page'] for x in spans if x.get('line_id') in lm})
                if item.get('pdf_pages') != note_pages:
                    err('component_pages_mismatch', record_id=rid, note_id=note_id)
                component_spans.extend(spans)
        expected_components = [x for x in primary if x.get('role') in {'footnote', 'commentary'}]
        if Counter(map(span_key, component_spans)) != Counter(map(span_key, expected_components)):
            err('record_ancillary_component_coverage_mismatch', record_id=rid)
        commentary_text = ''.join(x['text_verbatim'] for x in r['commentary']['items'])
        if r['commentary']['translation'] != (commentary_text or None):
            err('commentary_aggregate_text_mismatch', record_id=rid)
        narrator_spans = ((r.get('narrator') or {}).get('evidence') or {}).get('source_spans', [])
        if narrator_spans and r['narrator'].get('verbatim') != span_text(narrator_spans):
            err('narrator_evidence_text_mismatch', record_id=rid)
        for frag in r.get('embedded_arabic_fragments', []):
            arabic_fragment_count += 1
            lid = frag.get('line_id')
            if lid not in lm:
                err('arabic_fragment_unknown_line', record_id=rid, line_id=lid)
                continue
            start, end = frag.get('line_start'), frag.get('line_end')
            if lm[lid]['text'][start:end] != frag.get('text_verbatim'):
                err('arabic_fragment_not_literal_source_slice', record_id=rid, line_id=lid)
            if frag.get('pdf_page') != lm[lid]['pdf_page']:
                err('arabic_fragment_page_mismatch', record_id=rid, line_id=lid)
            if not any(x['line_id'] == lid and x['start'] <= start and x['end'] >= end for x in primary):
                err('arabic_fragment_outside_record_source_unit', record_id=rid, line_id=lid)
            if frag.get('canonical_arabic_substitution') is not False:
                err('arabic_fragment_substituted_canonical_text', record_id=rid, line_id=lid)
        for link in r.get('related_versions', []):
            relationship_count += 1
            target = link.get('record_id')
            if target not in rm or target == rid:
                err('related_record_target_invalid', record_id=rid, target=target)
                continue
            if link.get('relation') == 'exact_extracted_translation_text':
                if r['text']['translation'] != rm[target]['text']['translation']:
                    err('exact_text_relation_not_exact', record_id=rid, target=target)
                actual = hashlib.sha256(r['text']['translation'].encode('utf-8')).hexdigest()
                if link.get('basis_sha256') != actual:
                    err('related_text_hash_mismatch', record_id=rid, target=target)
            if link.get('canonical_equivalence_asserted') is not False:
                err('unsupported_canonical_equivalence_claim', record_id=rid, target=target)
    if len(set(declared_component_ids)) != len(declared_component_ids):
        err('duplicate_note_component_ids')
    checks['record_note_and_commentary_components_checked'] = component_count
    checks['embedded_arabic_fragments_checked'] = arabic_fragment_count
    checks['related_record_links_checked'] = relationship_count

    if section_table is not None:
        section_note_count = 0
        all_section_records = []
        for sid, section in section_table.items():
            expected_records = [r['id'] for r in records if r['book']['section_id'] == sid]
            if section.get('record_ids') != expected_records:
                err('section_record_membership_or_order_mismatch', section_id=sid)
            all_section_records.extend(section.get('record_ids', []))
            lid = section.get('header_line_id')
            if lid not in lm or section.get('header') != lm[lid]['text']:
                err('section_header_not_literal_source_line', section_id=sid)
            title_ids = section.get('title_line_ids', [])
            if any(lid not in lm for lid in title_ids):
                err('section_title_unknown_source_line', section_id=sid)
            elif section.get('title_verbatim') != ''.join(lm[lid]['text'] + '\n' for lid in title_ids):
                err('section_title_not_literal_source_lines', section_id=sid)
            expected_section_notes = [row for row in by_section.get(sid, []) if row.get('role') == 'section_footnote']
            actual_section_notes = []
            for note in section.get('notes', []):
                section_note_count += 1
                spans = note.get('source_spans', [])
                if note.get('text_verbatim') != span_text(spans):
                    err('section_note_not_literal_source_spans', section_id=sid, note_id=note.get('note_id'))
                actual_section_notes.extend(spans)
            if Counter(map(span_key, actual_section_notes)) != Counter(map(span_key, expected_section_notes)):
                err('section_note_span_coverage_mismatch', section_id=sid)
        if Counter(all_section_records) != Counter(rids):
            err('section_catalog_record_coverage_mismatch')
        checks['section_note_components_checked'] = section_note_count
    report['status'] = 'passed' if not errors else 'failed'
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    edition = 'languages/ja/books/muslim/editions/pdf-c859ce57c211ea1b'
    p.add_argument('--root', default='.', help='Package root; relative file arguments are resolved here.')
    p.add_argument('--pdf', default='sources/ja-muslim-web.pdf')
    p.add_argument('--lines', default='evidence/lines.jsonl')
    p.add_argument('--pages', default='evidence/raw-pages.json')
    p.add_argument('--schema', default='schemas/attachment.record.schema.json')
    p.add_argument('--records', default=edition + '/records.json')
    p.add_argument('--jsonl', default=edition + '/records.jsonl')
    p.add_argument('--ledger', default='evidence/line-attribution.jsonl')
    p.add_argument('--sections', default=edition + '/sections.json')
    p.add_argument('--metadata', help='Optional source metadata file to pin in the report.')
    p.add_argument('--raw-only', action='store_true', help='Check PDF/raw-page/line evidence without candidate records.')
    p.add_argument('--report', default='reports/independent-validation.json')
    args = p.parse_args()
    package_root = Path(args.root).resolve()
    if args.raw_only:
        args.records = args.jsonl = args.ledger = args.sections = None
    for field in ['pdf', 'lines', 'pages', 'schema', 'records', 'jsonl', 'ledger', 'sections', 'metadata', 'report']:
        value = getattr(args, field, None)
        if value is not None:
            path = Path(value)
            setattr(args, field, str(path if path.is_absolute() else package_root / path))
    try:
        report = run(args)
    except Exception as ex:
        report = {'status': 'validator_error', 'error_type': type(ex).__name__, 'message': str(ex)}
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report.get('status'), 'errors': len(report.get('errors', [])),
                      'warnings': len(report.get('warnings', [])), 'report': str(path),
                      'checks': report.get('checks', {})}, ensure_ascii=False))
    if report.get('status') == 'validator_error':
        print(report['message'], file=sys.stderr)
    return 0 if report.get('status') == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
