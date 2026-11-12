#!/usr/bin/env python3
"""Register the exact Chinese Hisn delivery with its saved genre/span decisions.

This adapter does not OCR, translate, authenticate, or accept candidate parallels.
The immutable delivery remains authoritative; only selected Chinese quotation
spans enter the reader. Run refresh_bank.py afterwards for generated views.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from material_registry import DECISION
from register_material import register


SLUG = 'zh-cn-hisn-muslim-1a09ee75'
PREFIX = 'materials/' + SLUG + '/'
IMPORT = 'imports/chinese-hisn-final-20261110/'
EDITION = 'pdf-1a09ee75-final-20261110'
TITLE = '穆斯林的堡垒 — Hisn al-Muslim'
SOURCE_HASH = '1a09ee75c544d3ced4ac287bd9c996aec9e508f7c98c0965b5e3744131c2cfd4'
INPUT_HASH = '0c000f5f5cfac6ba52bd8339b205bcdd775f952ace81bc261930960fda8f38d5'
DECISIONS_HASH = 'ddf3d53429a49d975c41ee47b6b41ef4ef8196c01f21a397c36f8ebf762cb0d4'
EXCLUSIONS_HASH = '438d7bfb102aee04760e433dd126ad403cc93ae9abaa08f9e43a945b9c00281b'
EXPECTED_COUNTS = {'hadith': 251, 'non_hadith': 23, 'unknown': 5}
COUNTERPART_HOLD = ('Final evaluation has no bank-approved Arabic or English occurrence. '
                    'Preserve enrichment as evidence only; require a separate explicit '
                    'source-bound approval before enabling counterpart resolution.')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                            for row in rows), encoding='utf-8')


def read_checked(path, expected):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('Unexpected source bytes: ' + str(path))
    return json.loads(raw)


def retained_text(body, decision):
    """Join exact selected spans with explicitly recorded display separators."""
    text, joins, previous = [], [], None
    spans = decision['included_body_spans']
    if not spans:
        raise ValueError('A reader quotation needs selected spans')
    for segment, (start, end) in zip(decision['selected_segments'], spans, strict=True):
        if not (0 <= start < end <= len(body)) or (previous is not None and previous > start):
            raise ValueError('Invalid or overlapping selected body span')
        fragment = body[start:end]
        if (segment['start'], segment['end']) != (start, end) or fragment != segment['text_verbatim'] or sha(fragment.encode()) != segment['sha256']:
            raise ValueError('Selected segment differs from exact source body')
        if previous is not None:
            gap = body[previous:start]
            separator = gap if not gap or gap.isspace() else '\n'
            text.append(separator)
            joins.append({'between_body_offsets': [previous, start], 'separator': separator,
                          'kind': 'original_whitespace' if separator == gap else 'display_newline_between_selected_spans'})
        text.append(fragment)
        previous = end
    return ''.join(text), joins


def validate_classifications(source, ledger, exclusions):
    rows = source['records']
    decisions = ledger['decisions']
    if ledger['input_sha256'] != INPUT_HASH or exclusions['input_sha256'] != INPUT_HASH:
        raise ValueError('Classification ledger names a different input')
    if len(rows) != 279 or len(decisions) != 279 or len({r['record_id'] for r in rows}) != 279:
        raise ValueError('Source identities or classification coverage changed')
    if dict(Counter(d['classification'] for d in decisions)) != EXPECTED_COUNTS:
        raise ValueError('Saved genre partition changed')
    by_id, expected_exclusions = {}, set()
    for index, (row, decision) in enumerate(zip(rows, decisions, strict=True)):
        if row['record_id'] != decision['record_id'] or decision['source_record_index'] != index:
            raise ValueError('Record/classification identity mismatch')
        for key, field in (('source_text_sha256', 'source_text_verbatim'), ('body_text_sha256', 'body_text_verbatim')):
            if sha(row[field].encode()) != decision[key]:
                raise ValueError('Classification source-text binding changed')
        if decision['classification'] == 'hadith':
            retained_text(row['body_text_verbatim'], decision)
        elif decision['included_body_spans'] or decision['selected_segments']:
            raise ValueError('Hidden genre has reader spans')
        cursor = 0
        for start, end in sorted(decision['included_body_spans'] + decision['excluded_body_spans']):
            if start != cursor or not start < end <= len(row['body_text_verbatim']):
                raise ValueError('Included and excluded spans must partition the full source body')
            cursor = end
        if cursor != len(row['body_text_verbatim']):
            raise ValueError('Included and excluded spans must partition the full source body')
        expected_exclusions.update((row['record_id'], start, end)
                                   for start, end in decision['excluded_body_spans'])
        by_id[row['record_id']] = row
    actual_exclusions = set()
    for excluded in exclusions['segments']:
        key = (excluded['record_id'], excluded['start'], excluded['end'])
        if key in actual_exclusions:
            raise ValueError('Duplicate excluded source span')
        actual_exclusions.add(key)
        row = by_id[excluded['record_id']]
        if row['body_text_verbatim'][excluded['start']:excluded['end']] != excluded['text_verbatim']:
            raise ValueError('Excluded span differs from preserved source')
    if actual_exclusions != expected_exclusions:
        raise ValueError('Excluded-span ledger does not match classification decisions')


def make_record(source, decision, metadata):
    original_index = decision['source_record_index']
    source_pointer = '/records/' + str(original_index)
    translation, joins = retained_text(source['body_text_verbatim'], decision)
    number = source['printed_entry_number']
    names = source['source_attribution'].get('named_reporters_as_printed') or []
    heading = (source.get('chapter') or {}).get('heading_verbatim')
    summary = decision.get('source_wording_is_compiler_summary') is True
    qualifiers = {key: decision[key] for key in (
        'source_summary_qualification', 'source_wording_is_compiler_summary',
        'render_as_direct_prophetic_quote', 'scope_correction') if key in decision}
    return {
        'id': source['record_id'], 'language': 'zh-CN', 'book_key': 'hisn-al-muslim', 'edition': EDITION,
        'source_language_code': 'zh',
        'record_type': 'hadith_meaning_excerpt' if summary else 'hadith_excerpt',
        'content_kind': decision['subtype'],
        'title': ('来源编号 ' + number) if number is not None else '原文未编号 — Unnumbered source quotation',
        'text': {'arabic': None, 'translation': translation},
        'source': {'title': TITLE, 'url': metadata['distribution_provenance']['official_source_url'],
                   'original_source_id': source['source_id'], 'original_record_id': source['record_id'],
                   'final_delivery_path': IMPORT + 'zh_hisn_final_corrected.json',
                   'final_delivery_sha256': INPUT_HASH, 'final_delivery_pointer': source_pointer,
                   'source_metadata_path': IMPORT + 'zh_hisn_final_metadata.json'},
        'number': {'source_entry_id': number, 'in_book': number, 'canonical': None,
                   'scope': 'source_local', 'numbering_system': 'Chinese Hisn source-local printed entry label; not a canonical collection number',
                   'as_printed': source['printed_label_verbatim'], 'local_marker': source['printed_local_marker']},
        'narrator': {'name': ' / '.join(n['name_verbatim'] for n in names) if names else None,
                     'as_printed': names, 'basis': 'Printed Chinese attribution only; full chain and Arabic identity remain unapproved.'},
        'isnad': None,
        'translator': {'name': '叶赛尔', 'name_variants_as_printed': metadata['translator_credits_as_printed'],
                       'evidence': IMPORT + 'zh_hisn_final_metadata.json#/translator_credits_as_printed',
                       'independently_verified_identity': None},
        'ai_translation': False,
        'translation_provenance': {'origin': 'human_translator_credited', 'label': 'Human',
            'ai_translation': False, 'human_involvement': 'named_human_translator',
            'basis': metadata['translation_origin']['basis'],
            'evidence_ids': [IMPORT + 'zh_hisn_final_metadata.json#/translation_origin'],
            'scope_note': 'Existing published Chinese translation. No new translation generated; historical source metadata preserved.'},
        'topic_tags': [], 'editorial_tags': ['source:' + SLUG, 'canonical_mapping:unapproved', 'arabic:not_approved'],
        'source_headings': [heading] if heading else [],
        'commentary': {'arabic': None, 'translation': None}, 'footnotes': [],
        'references': {'items': source['references'], 'canonical_mapping_status': 'unapproved',
                       'scope_note': 'Only references printed in the Chinese PDF; candidate enrichment remains outside the reader.'},
        'grading': {'grade': None, 'grader': None, 'basis': 'No candidate grade promoted from the final evaluation.'},
        'page': {'pdf': source['pdf_pages'], 'printed': source['printed_pages'], 'sheet': None, 'row': None},
        'source_locator': {'path': IMPORT + 'zh_hisn_final_corrected.json', 'json_pointer': source_pointer,
            'source_pdf_path': PREFIX + 'zh-hisn.pdf', 'source_pdf_sha256': SOURCE_HASH,
            'body_text_sha256': decision['body_text_sha256'], 'included_body_spans': decision['included_body_spans'],
            'offset_basis': 'Zero-based half-open Unicode code points in body_text_verbatim', 'display_joins': joins,
            'classification_path': IMPORT + 'classification/decisions.json',
            'excluded_body_spans_path': IMPORT + 'classification/excluded_segments.json',
            **({'classification_qualifications': qualifiers} if qualifiers else {})},
        'review': {'status': 'PASS_SOURCE_TRANSCRIPTION_ONLY', 'independent_pro_qc': 'partial',
            'release_status': 'FAIL_BANK_READINESS', 'release_eligible': False, 'certified_release_eligible': False,
            'issues': ['Chinese source transcription PASS; canonical identity, Arabic, full chains and grades remain PARTIAL/unapproved.',
                       'Owner authorized pending-review reading; this visibility decision does not certify authenticity.',
                       *([decision['source_summary_qualification']] if decision.get('source_summary_qualification') else [])],
            'historical_source_review': source['review'],
            'historical_publication_assessment': source['publication_assessment']},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                   'source_notice_preserved_in': PREFIX + 'zh-hisn.pdf'},
        'extraction': {'method': 'exact_saved_json_segments', 'ocr_used': None, 'is_excerpt': True,
            'new_ocr_performed': False, 'new_pdf_pages_visually_reviewed': 0,
            'included_text_is_exact_source_spans': True, 'classification_is_authenticity_approval': False,
            'historical_evaluation_id': 'ZH-HISN-FINAL-2026-11-10',
            'source_extraction_history': IMPORT + 'FINAL_EVALUATION_REPORT_JA.txt'},
        'related_versions': []}


def run(root):
    root = Path(root).resolve()
    archive, material = root / IMPORT, root / PREFIX
    if sha((material / 'zh-hisn.pdf').read_bytes()) != SOURCE_HASH:
        raise ValueError('Original PDF changed')
    source = read_checked(archive / 'zh_hisn_final_corrected.json', INPUT_HASH)
    ledger = read_checked(archive / 'classification/decisions.json', DECISIONS_HASH)
    exclusions = read_checked(archive / 'classification/excluded_segments.json', EXCLUSIONS_HASH)
    validate_classifications(source, ledger, exclusions)
    metadata = source['source_metadata']
    if metadata['current_review']['bank_readiness'] != 'FAIL':
        raise ValueError('Historical final evaluation changed')
    records, partitions = [], {'non_hadith': [], 'unknown': []}
    for original, decision in zip(source['records'], ledger['decisions'], strict=True):
        if decision['classification'] == 'hadith':
            records.append(make_record(original, decision, metadata))
        else:
            partitions[decision['classification']].append({'id': original['record_id'],
                'classification': decision['classification'], 'classification_decision': decision,
                'original_source_record': original, 'visible_in_hadith_html': False})
    write_rows(material / 'records.jsonl', records)
    partition_paths = {'non_hadith': 'non-hadith/' + SLUG + '/records.jsonl',
                       'unknown': 'unclassified/' + SLUG + '/records.jsonl'}
    for kind, rows in partitions.items():
        target = root / partition_paths[kind]
        write_rows(target, rows)
        (target.parent / 'README.md').write_text('# Chinese Hisn: ' + kind.replace('_', ' ') + '\n\n'
            'Preserved source occurrences and the saved genre decisions. These records are not registered '
            'as a material and do not enter the Hadith HTML or its search index.\n\n'
            'The byte-identical original delivery remains under `imports/chinese-hisn-final-20261110/`. '
            'These JSONL wrappers preserve the original record values, not the original JSON serialization.\n', encoding='utf-8')
    register(root, PREFIX.rstrip('/'), 'zh-CN', 'hisn-al-muslim', EDITION, TITLE,
             'records.jsonl', 'zh-hisn.pdf', source_url=metadata['distribution_provenance']['official_source_url'],
             source_id=SLUG, replace=(material / 'manifest.json').exists())
    manifest = json.loads((material / 'manifest.json').read_text(encoding='utf-8'))
    manifest['source'].update({'title_zh': '穆斯林的堡垒', 'title_en': 'Hisn al-Muslim',
        'original_filename': 'zh-hisn.pdf', 'pdf_pages': 52,
        'metadata_path': IMPORT + 'zh_hisn_final_metadata.json'})
    manifest['counterpart_policy'] = {'mode': 'disabled', 'reason': COUNTERPART_HOLD}
    manifest['publication'] = {'authorized': True, 'decision': DECISION, 'decision_date_japan': '2026-11-12',
        'owner_instruction': 'upload them into our bank and integrate into html , upload source pdf in bank material sources also',
        'scope': 'Exact final delivery and original PDF; 251 classified Chinese hadith quotations and reports in HTML, including 13 labelled compiler practice summaries; 23 non-hadith and 5 unknown records outside Hadith HTML.',
        'independent_qc_asserted': False, 'rights_clearance_asserted': False,
        'historical_bank_readiness': 'FAIL', 'historical_overall_status': 'PARTIAL',
        'source_fidelity': 'PASS', 'certified_release_eligible': False}
    manifest['source_partitions'] = {'original_records': 279, 'reader_hadith_records': len(records),
        'non_hadith': {'count': len(partitions['non_hadith']), 'path': partition_paths['non_hadith'], 'visible_in_hadith_html': False},
        'unknown': {'count': 5, 'path': partition_paths['unknown'], 'visible_in_hadith_html': False},
        'classification_path': IMPORT + 'classification/decisions.json', 'classification_sha256': DECISIONS_HASH,
        'classification_change_log': IMPORT + 'classification/classification-change-log.json'}
    manifest['preserved_delivery'] = {'path': IMPORT, 'source_json_sha256': INPUT_HASH,
        'original_bytes_unchanged': True, 'candidate_enrichment_accepted': False}
    write_json(material / 'manifest.json', manifest)
    audit = {'schema': 'hadith-bank-chinese-hisn-integration-v1', 'input_sha256': INPUT_HASH,
        'source_pdf_sha256': SOURCE_HASH, 'decisions_sha256': DECISIONS_HASH, 'counts': EXPECTED_COUNTS,
        'source_records': 279, 'reader_records': len(records), 'source_ids_preserved': True,
        'new_visual_page_review_count': 0, 'new_ocr_performed': False, 'new_canonical_or_arabic_approval': False,
        'historical_source_fidelity': 'PASS', 'historical_bank_readiness': 'FAIL',
        'historical_overall_status': 'PARTIAL', 'public_visibility': 'owner_authorized_pending_review',
        'certified_release_eligible': False, 'counterparts_disabled': True,
        'records_sha256': sha((material / 'records.jsonl').read_bytes()), 'partitions': partition_paths}
    write_json(material / 'integration-audit.json', audit)
    return {'material': SLUG, 'source_records': 279, 'reader_records': len(records),
            'non_hadith': len(partitions['non_hadith']), 'unknown': len(partitions['unknown']),
            'original_source_modified': False, 'candidate_counterparts_published': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(run(args.root), ensure_ascii=False))


if __name__ == '__main__':
    main()
