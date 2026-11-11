#!/usr/bin/env python3
"""Register the supplied Chinese Muwatta DOCX without translating its text.

The original bytes, full paragraph ledger and excluded commentary remain local
and reproducible. Printed numbers refer only to this al-Shaybani source edition.
Run refresh_bank.py afterwards to rebuild offline search and the HTML reader.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

from extract_chinese_muwatta import extract, SOURCE_SHA256
from material_registry import SOURCE_IMPORT_DECISION
from register_material import register


SLUG = 'zh-muwatta-shaybani-yu-2000-docx'
EDITION = 'docx-cf65c0e865be95a7'
SOURCE_FILENAME = '穆宛塔圣训集_Muwatta_Chinese.docx'
ORIGINAL_FILENAME = 'Muwatta_Chinese_Text.docx'
SOURCE_TITLE = '穆宛塔圣训集 — Muwatta of Imam Malik (al-Shaybani recension)'
PREFIX = 'materials/' + SLUG + '/'
NUMBERING_SYSTEM = ('Source-local printed sequence in the Chinese al-Shaybani recension; '
                    'not canonical Yahya-recension or Sunnah.com numbering')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_gzip_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    path.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))


def run(root, source=None):
    root = Path(root).resolve()
    folder = root / PREFIX
    source = Path(source) if source else folder / SOURCE_FILENAME
    original = source.read_bytes()
    if digest(original) != SOURCE_SHA256:
        raise ValueError('The original DOCX does not match this source-specific importer')
    extracted = extract(source)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / SOURCE_FILENAME).write_bytes(original)
    paragraphs = extracted['paragraphLedger']
    native = '\n\n'.join(p['text'] for p in paragraphs)
    (folder / 'native-text.txt').write_text(native, encoding='utf-8')
    offsets, cursor = [], 0
    for paragraph in paragraphs:
        offsets.append(cursor)
        cursor += len(paragraph['text']) + 2
    native_hash = digest(native.encode('utf-8'))
    metadata_path = PREFIX + 'source-metadata.json'
    commentary_path = PREFIX + 'excluded-commentary.json.gz'
    records, source_ledger = [], []
    identifiers = {}
    for sequence, report in enumerate(extracted['reports'], 1):
        p = report['sourceParagraphIndices'][0]
        occurrence_id = 'zh-muwatta:' + EDITION + ':p' + str(p).zfill(6)
        identifiers[report['id']] = occurrence_id
        number = str(report['sourceNumber']) if report['sourceNumber'] is not None else None
        parts = report['bodyParagraphs']
        spans = []
        for part_index, part in enumerate(parts):
            start = offsets[part['paragraphIndex']] + part['start']
            end = offsets[part['paragraphIndex']] + part['end']
            if spans and part['paragraphIndex'] != parts[part_index - 1]['paragraphIndex']:
                # The only multi-paragraph occurrences are adjacent source
                # continuations. Preserve the declared paragraph separator.
                if native[spans[-1][1]:start] != '\n\n':
                    raise ValueError('A continuation would skip source text')
                spans.append([spans[-1][1], start])
            spans.append([start, end])
        translation = ''.join(native[a:b] for a, b in spans)
        if translation != report['text'] or not translation:
            raise ValueError('Retained source spans do not reconstruct the report')
        printed = next((s['text'] for s in paragraphs[p]['segments'] if s['kind'] == 'source_number'), None)
        structure = [heading for heading in (report['book'], report['section']) if heading]
        headings = [heading.get('raw', heading['title']) for heading in structure]
        heading_paragraphs = [heading['sourceParagraphIndex'] for heading in structure]
        issues = [report['sourceNote']] if report.get('sourceNote') else []
        referential = report['sourceNumber'] in (453, 604, 606, 621, 960, 972)
        if referential:
            issues.append('Source report refers to a previous account or action without repeating its full wording. Exact source text retained; no missing wording reconstructed.')
        narrator = re.match(r'^(.{1,90}?)(?:传述|传叙|述)[：:]', translation)
        record = {
            'id': occurrence_id, 'language': 'zh-CN', 'book_key': 'malik', 'edition': EDITION,
            'title': '来源编号 ' + number if number else '原文未编号 — Unnumbered source report',
            'record_type': 'source_narration_occurrence',
            'content_kind': ('referential_source_report' if referential else
                             'numbered_source_report' if number else 'unnumbered_source_report'),
            'text': {'arabic': None, 'translation': translation},
            'source': {'title': SOURCE_TITLE, 'url': None,
                       'original_filename': ORIGINAL_FILENAME, 'metadata_path': metadata_path,
                       'recension': 'Muhammad ibn al-Hasan al-Shaybani',
                       'work_scope': 'Main numbered reports and one identified unnumbered body report across 19 source books; printed numbering gaps preserved. Quotations embedded in excluded commentary are not separately extracted.'},
            'number': {'source_entry_id': number, 'in_book': number, 'canonical': None,
                       'scope': 'source_local', 'numbering_system': NUMBERING_SYSTEM,
                       'source_sequence_position': sequence, 'as_printed': printed,
                       'source_number_status': report['sourceNumberStatus']},
            'narrator': {'name': narrator.group(1) if narrator else None,
                        'basis': 'Opening attribution as supplied; no full isnad reconstruction.'},
            'isnad': None,
            'translator': {'name': '穆萨·余崇仁', 'name_latin': 'Musa Yu Chongren',
                           'role': 'named translator in source preface', 'evidence': metadata_path},
            'translation_provenance': {
                'origin': 'human_translator_credited', 'label': 'Human',
                'basis': 'Source preface credits 译者：穆萨·余崇仁 and dates the translation 2000年十月二十三日于韦州.',
                'human_involvement': 'named_human_translator', 'ai_translation': False,
                'evidence_ids': [metadata_path],
                'scope_note': 'Existing Chinese translation; no new translation generated.'},
            'ai_translation': False, 'topic_tags': [], 'source_headings': headings,
            'source_structure_tags': [
                {'origin': 'source_book_structure', 'source_id': SLUG, 'hierarchy': i + 1,
                 'value_verbatim': title, 'source_locator': {
                     'path': PREFIX + 'native-text.txt', 'paragraph_index_zero_based': heading_paragraphs[i]}}
                for i, title in enumerate(headings)],
            'editorial_tags': {'origin': 'import_pipeline_not_publisher', 'values': [
                'source:' + SLUG, 'language:zh-CN', 'book:malik', 'edition:' + EDITION,
                'method:direct_ooxml', 'format:docx', 'ai_translation:false',
                'canonical_mapping:unverified', 'arabic:not_supplied']},
            'commentary': {'arabic': None, 'translation': None}, 'footnotes': [],
            'references': {'items': [], 'canonical_mapping_status': 'unverified',
                           'number_scope': 'Printed source-edition number only; unnumbered reports remain null.'},
            'grading': {'grade': None, 'grader': None,
                        'basis': 'No authenticity grade inferred from collection membership.'},
            'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None,
                     'doc_paragraphs': report['sourceParagraphIndices'], 'index_base': 0,
                     'basis': 'Native DOCX document-body paragraph indices; stable printed pages not supplied.'},
            'source_locator': {'path': PREFIX + 'native-text.txt',
                               'source_doc_path': PREFIX + SOURCE_FILENAME,
                               'part': 'word/document.xml', 'index_base': 0,
                               'offset_unit': 'Unicode code points in native-text.txt; half-open spans',
                               'paragraph_indices_zero_based': report['sourceParagraphIndices'],
                               'included_source_spans': spans,
                               'excluded_commentary_audit': commentary_path},
            'source_defects': issues, 'related_versions': [],
            'review': {'status': 'native_source_import', 'issues': issues,
                       'independent_pro_qc': 'not_performed', 'release_status': 'source_import',
                       'release_eligible': False, 'certified_release_eligible': False},
            'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                       'source_notice_preserved_in': PREFIX + SOURCE_FILENAME},
            'extraction': {'method': 'direct_ooxml', 'ocr_used': False,
                           'upstream_transcription_method': None, 'is_excerpt': False,
                           'side_commentary_included': False,
                           'included_text_is_exact_source_spans': True,
                           'source_extraction': PREFIX + 'native-text.txt',
                           'paragraph_separator': '\n\n', 'commentary_audit': commentary_path,
                           'continuation_decisions': [part['continuationReason'] for part in parts
                                                      if part.get('continuationReason')],
                           'parenthetical_policy': 'Preserve brief source translation glosses and narrative detail; separate explicitly reviewed interpretive commentary spans.'}}
        records.append(record)
        source_ledger.append({'id': occurrence_id, 'source_number': number,
                              'as_printed': printed, 'sequence_position': sequence,
                              'source_paragraphs': report['sourceParagraphIndices'],
                              'included_source_spans': spans, 'imported': True})
    if len({row['id'] for row in records}) != len(records):
        raise ValueError('Duplicate source occurrence IDs')
    record_path = folder / 'records.jsonl'
    record_path.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                                  for row in records), encoding='utf-8')
    # Full classifications include front/back matter and every discarded span.
    # Excluded text is not placed in commentary/footnotes of searchable records.
    for paragraph in paragraphs:
        for segment in paragraph['segments']:
            if segment.get('recordId'):
                segment['recordId'] = identifiers[segment['recordId']]
    annotations = []
    for item in extracted['annotations']:
        item = dict(item)
        if item.get('recordId'):
            item['recordId'] = identifiers[item['recordId']]
        start = offsets[item['paragraphIndex']]
        item['source_span'] = [start + item['start'], start + item['end']]
        annotations.append(item)
    write_gzip_json(folder / 'paragraph-ledger.json.gz', {
        'schema': 'hadith-bank-source-paragraph-ledger-v1', 'source_sha256': SOURCE_SHA256,
        'index_base': 0, 'paragraph_separator': '\n\n', 'paragraphs': paragraphs})
    write_gzip_json(folder / 'excluded-commentary.json.gz', {
        'schema': 'hadith-bank-excluded-source-spans-v1', 'source_sha256': SOURCE_SHA256,
        'native_text_sha256': native_hash, 'items': annotations,
        'note': 'Exact removed text remains here and in the original Word file, outside narration search. Attributions are not inferred.'})
    write_json(folder / 'source-number-ledger.json', {
        'numbering_system': NUMBERING_SYSTEM, 'missing_printed_numbers': [196, 528, 764],
        'unnumbered_report_has_assigned_number': False, 'entries': source_ledger})
    audit = extracted['audit']
    audit['sourceFile'] = ORIGINAL_FILENAME
    metadata = {
        'schema': 'hadith-bank-source-metadata-v1', 'source_title_as_printed': '穆宛塔圣训集',
        'display_title': SOURCE_TITLE, 'original_filename': ORIGINAL_FILENAME,
        'stored_filename': SOURCE_FILENAME, 'source_sha256': SOURCE_SHA256,
        'source_bytes': len(original), 'source_url': None,
        'publisher_as_printed': '绿色中华网站', 'publisher_website_as_printed': 'www.xaislam.com',
        'translator': {'name': '穆萨·余崇仁', 'date_as_printed': audit['translatorDate'],
                       'evidence_paragraphs_zero_based': [10, 11]},
        'recension': {'name': 'Muhammad ibn al-Hasan al-Shaybani',
                      'evidence_paragraphs_zero_based': [8, 9]},
        'completeness': {'all_supplied_report_text_imported': False,
                         'all_main_numbered_and_identified_unnumbered_reports_imported': True,
                         'commentary_embedded_quotations_separately_extracted': False,
                         'scope_note': 'Main report bodies only; quotations within excluded commentary remain in the original document and source audit.',
                         'full_collection': None,
                         'numbered_report_count': 1005, 'unnumbered_report_count': 1,
                         'first_printed_number': '1', 'last_printed_number': '1008',
                         'missing_printed_numbers': [196, 528, 764],
                         'missing_numbers_filled': False},
        'extraction': {'method': 'direct_ooxml', 'ocr_used': False,
                       'upstream_transcription_method': None, 'native_text_sha256': native_hash,
                       'native_text_path': PREFIX + 'native-text.txt',
                       'paragraph_separator': '\n\n', 'source_audit': audit},
        'record_count': len(records), 'records_sha256': digest(record_path.read_bytes()),
        'review': {'independent_pro_qc': 'not_performed', 'certified_release_eligible': False},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None}}
    write_json(folder / 'source-metadata.json', metadata)
    register(root, PREFIX.rstrip('/'), 'zh-CN', 'malik', EDITION, SOURCE_TITLE,
             'records.jsonl', SOURCE_FILENAME, source_id=SLUG,
             replace=(folder / 'manifest.json').exists())
    manifest_path = folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['publication'] = {
        'authorized': True, 'decision': SOURCE_IMPORT_DECISION,
        'decision_date_japan': '2026-11-11',
        'basis': 'Owner supplied Muwatta_Chinese_Text.docx and requested adding 穆宛塔圣训集 to the bank as a file and implementing it in HTML and code.'}
    manifest['extraction_scope'] = {
        'source_file_count': 1, 'no_batch_limit': True, 'side_commentary_included': False,
        'all_supplied_report_text_imported': False,
        'all_main_numbered_and_identified_unnumbered_reports_imported': True,
        'commentary_embedded_quotations_separately_extracted': False,
        'audit_root': PREFIX.rstrip('/')}
    write_json(manifest_path, manifest)
    result = {'material': SLUG, 'records': len(records), 'numbered_reports': 1005,
              'unnumbered_reports': 1, 'books': 19, 'subsections': 434,
              'missing_printed_numbers': [196, 528, 764],
              'excluded_commentary_segments': len(annotations),
              'source_sha256': SOURCE_SHA256, 'records_sha256': metadata['records_sha256'],
              'native_text_sha256': native_hash,
              'every_paragraph_accounted_for': True,
              'all_translations_reconstruct_from_source_spans': True,
              'independent_pro_qc_performed': False}
    write_json(folder / 'integration-audit.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path, help='Original upload; omit to rebuild from the preserved repository DOCX.')
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.source), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
