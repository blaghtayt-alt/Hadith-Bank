#!/usr/bin/env python3
"""Extract the supplied 2013 Chinese Sunan Ibn Majah PDF, with source audit.

This importer is deliberately edition-specific. It never fetches another edition,
uses the supplied TXT as primary text, invents Arabic, or equates local chapter
numbers with canonical Ibn Majah numbers. Existing ABBYY OCR is preserved before
any page-image-verified correction. Publication/certification are separate steps.

Requires PyMuPDF (fitz) and Poppler pdftotext. Run against the original PDF:
  python scripts/import_chinese_ibn_majah.py --pdf /path/736950612-1.pdf
The PDF SHA256 is fixed in the resulting source metadata; reruns fail for a
different source rather than applying edition-specific boundaries to it.
"""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess

import fitz

SLUG = 'zh-cn-ibn-majah-yu-2013'
TITLE = '伊本·马哲圣训集 — Sunan Ibn Majah'
PDF_NAME = '伊本·马哲圣训集_Sunan_Ibn_Majah.pdf'
SOURCE_SHA256 = 'e3bc24bcee435894fc3826622839dd819f8c79eb83af5252f5389831fa76b383'
MARKER = re.compile(r'^[\[［【]\s*(\d{1,3})\s*[\]］】]')
SECTION = re.compile(r'^[\s\'\".,，。·•‘’“”]*[第笫].{1,12}[节節]')
CIRCLED = re.compile(r'[①-⑳]')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl_gz(path, rows):
    # Stable compressed bytes make the complete source audit reproducible.
    payload = ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows)
    path.write_bytes(gzip.compress(payload.encode('utf-8'), mtime=0))


def cjk_median(spans):
    sizes = [s['size'] for s in spans for c in s['text'] if '\u4e00' <= c <= '\u9fff']
    return round(statistics.median(sizes), 3) if sizes else None


def pdf_lines(document):
    pages = []
    for n, page in enumerate(document, 1):
        lines = []
        for block in page.get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)['blocks']:
            for line in block.get('lines', []):
                spans = line['spans']
                text = ''.join(s['text'] for s in spans)
                if not text.strip():
                    continue
                lines.append({'text': text, 'bbox': [round(v, 3) for v in line['bbox']],
                              'cjk_median_font_size': cjk_median(spans),
                              'fonts': sorted(set(s['font'] for s in spans))})
        lines.sort(key=lambda row: (round(row['bbox'][1], 1), row['bbox'][0]))
        # ABBYY occasionally emits the bracket number and its adjacent Chinese
        # words as two overlapping line objects. Reading strictly by y would put
        # the words before their number. Rejoin only horizontally disjoint pieces
        # sharing the same visual baseline; keep every original fragment.
        groups = []
        for line in lines:
            x0, y0, x1, y1 = line['bbox']
            found = None
            for group in reversed(groups[-3:]):
                gx0, gy0, gx1, gy1 = group['bbox']
                overlap = min(y1, gy1) - max(y0, gy0)
                if overlap > 0.5 * min(y1 - y0, gy1 - gy0) and (x1 <= gx0 + 1 or x0 >= gx1 - 1):
                    found = group
                    break
            if found is None:
                groups.append({'bbox': line['bbox'][:], 'fragments': [line]})
            else:
                found['fragments'].append(line)
                found['bbox'] = [min(x0, found['bbox'][0]), min(y0, found['bbox'][1]),
                                 max(x1, found['bbox'][2]), max(y1, found['bbox'][3])]
        lines = []
        for group in groups:
            fragments = sorted(group['fragments'], key=lambda row: row['bbox'][0])
            sizes = [row['cjk_median_font_size'] for row in fragments if row['cjk_median_font_size'] is not None]
            row = {'text': ''.join(part['text'] for part in fragments), 'bbox': group['bbox'],
                   'cjk_median_font_size': statistics.median(sizes) if sizes else None,
                   'fonts': sorted(set(font for part in fragments for font in part['fonts']))}
            if len(fragments) > 1:
                row['raw_fragments'] = fragments
            lines.append(row)
        lines.sort(key=lambda row: (round(row['bbox'][1], 1), row['bbox'][0]))
        for index, row in enumerate(lines):
            row['line_index'] = index
        pages.append({'pdf_page': n, 'width': page.rect.width, 'height': page.rect.height,
                      'lines': lines})
    return pages


def line_role(line, page):
    text = line['text'].strip()
    x0, y0, x1, y1 = line['bbox']
    if y0 < 57:
        return 'running_header'
    # Every printed page footer is a short centered numeric token. Do not use
    # a vertical crop alone: long footnotes reach into the same lower margin.
    if y0 > 720 and x0 > 185 and x1 < 355 and len(text) < 22:
        return 'printed_page_footer'
    if page['pdf_page'] == 197 and text == '—' and x0 > 410 and y0 > 200:
        return 'citation_ocr_fragment_replaced_from_page_image'
    if re.fullmatch(r'[-—_\s.·•]+', text):
        return 'rule_or_scan_noise'
    if text == '奉普慈特慈的安拉之名':
        return 'opening_formula'
    if SECTION.match(text):
        return 'section_heading'
    return 'body'


def import_pdf(root, original):
    material = root / 'materials' / SLUG
    audit = material / 'audit'
    audit.mkdir(parents=True, exist_ok=True)
    corrections = json.loads((audit / 'verified-corrections.json').read_text(encoding='utf-8'))
    supplemental = audit / 'additional-body-corrections.json'
    if supplemental.exists():
        extra = json.loads(supplemental.read_text(encoding='utf-8'))
        if isinstance(extra, dict) and extra.get('source_sha256') != SOURCE_SHA256:
            raise ValueError('Supplemental corrections do not identify the verified source PDF')
        corrections['body_corrections'].extend(extra if isinstance(extra, list) else extra['body_corrections'])
    expected = json.loads((audit / 'expected-chapter-counts.json').read_text(encoding='utf-8'))
    expected_total = expected.pop('total')
    original_hash = sha256(original)
    if original_hash != SOURCE_SHA256:
        raise ValueError('This importer only accepts the verified supplied PDF SHA256')
    previous = material / 'source-metadata.json'
    if previous.exists() and json.loads(previous.read_text(encoding='utf-8'))['source_sha256'] != original_hash:
        raise ValueError('Source PDF differs from the previously extracted edition')
    source = material / PDF_NAME
    if original.resolve() != source.resolve():
        shutil.copyfile(original, source)
    if sha256(source) != original_hash:
        raise ValueError('Original PDF copy differs')
    document = fitz.open(source)
    if len(document) != 487:
        raise ValueError('This edition-specific importer requires the supplied 487-page PDF')
    pages = pdf_lines(document)
    write_jsonl_gz(audit / 'pdf-lines-raw.jsonl.gz', pages)
    raw_text = subprocess.run(['pdftotext', '-layout', str(source), '-'], check=True, capture_output=True).stdout
    (audit / 'pdf-layout-raw.txt.gz').write_bytes(gzip.compress(raw_text, mtime=0))

    # Correct markers only with the separate visual review evidence. Patch the
    # marker at the start of the exact source line, never a matching body number.
    applied = []
    number_patches = collections.defaultdict(list)
    for patch in corrections['number_corrections']:
        number_patches[patch['pdf_page']].append(patch)
    by_page = {p['pdf_page']: p for p in pages}
    for page, patches in number_patches.items():
        for patch in patches:
            matches = [l for l in by_page[page]['lines'] if l['text'].strip().startswith(patch['before'])]
            if len(matches) != 1:
                raise ValueError(f'Non-unique verified marker patch: {patch!r}: {len(matches)}')
            line = matches[0]
            old = line['text']
            new = old.replace(patch['before'], patch['after'], 1)
            line['corrected_text'] = new
            line['original_marker'] = patch['before']
            applied.append({**patch, 'kind': 'number_marker', 'line_index': line['line_index'],
                            'line_before': old, 'line_after': new, 'bbox': line['bbox']})

    starts = {v['start_page']: int(k) for k, v in expected.items()}
    excluded, records, segments, chapters, footnotes = [], [], [], [], []
    current_chapter = None
    chapter_title = None
    section_title = None
    current = None
    sequence = collections.defaultdict(list)

    def finish():
        nonlocal current
        if current is None:
            return
        if not current['lines']:
            raise ValueError('Empty narration occurrence: ' + repr(current))
        text = ''.join(l['text'].strip() for l in current['lines']).strip()
        # Whitespace here is the PDF line-break/layout layer, not new wording.
        before_body_corrections = text
        for patch in corrections['body_corrections']:
            if patch['chapter'] == current['chapter'] and patch['local_number'] == current['local_number']:
                # Poppler and MuPDF differ only in layout spaces for these verified patches.
                before, after = patch['before'], patch['after']
                if text.count(before) != 1:
                    raise ValueError(f'Body patch does not match exact record: {patch!r}')
                text = text.replace(before, after, 1)
                applied.append({**patch, 'kind': 'narration_text', 'occurrence_id': current['id']})
        footnote_markers = sorted(set(CIRCLED.findall(text)))
        footnote_references = [{'marker': marker, 'pdf_page': line['pdf_page'], 'source_line_index': line['line_index']}
                              for line in current['lines'] for marker in CIRCLED.findall(line['text'])]
        if footnote_markers:
            text = CIRCLED.sub('', text)
        if not text:
            raise ValueError('Empty narration after separating footnote markers')
        pdf_pages = list(dict.fromkeys(l['pdf_page'] for l in current['lines']))
        suspect_latin = sorted(set(re.findall(r'[A-Za-z]{1,12}', text)))
        suspect_symbols = sorted(set(re.findall(r'[\ufffd■□£€¥\^]', text)))
        issues = ['ocr_full_character_collation_pending']
        if suspect_latin:
            issues.append('possible_ocr_latin_artifact')
        if suspect_symbols:
            issues.append('possible_ocr_symbol_artifact')
        if re.search(r'[\[【［]\d+[\]】］]', text):
            issues.append('embedded_number_marker_requires_review')
        key = f"chapter-{current['chapter']:02d}:hadith-{current['local_number']:03d}"
        locators = [{'pdf_page': l['pdf_page'], 'line_index': l['line_index'], 'bbox': l['bbox']} for l in current['lines']]
        title = f"第{current['chapter']}章 · 第{current['local_number']}条"
        narrator = re.match(r'^(.{1,55}?)(?:传述|传说|说)[：:]?', text)
        row = {
            'id': current['id'], 'language': 'zh-CN', 'book_key': 'ibn-majah',
            'edition': f'yu-2013-pdf-{original_hash[:16]}', 'title': title,
            'text': {'arabic': None, 'translation': text},
            'record_type': 'hadith_occurrence', 'content_kind': 'numbered_source_narration',
            'source': {'title': TITLE, 'title_zh': '伊本·马哲圣训集', 'title_en': 'Sunan Ibn Majah',
                       'compiler': '伊本·马哲', 'publisher': '宗教文化出版社', 'edition_year': 2013,
                       'original_filename': '736950612-1.pdf', 'url': None,
                       'metadata_path': f'materials/{SLUG}/source-metadata.json',
                       'work_scope': 'Chinese translated collection; full narrator chains abridged by translator'},
            'number': {'source_entry_id': key, 'in_book': f"{current['chapter']}:{current['local_number']}",
                       'canonical': None, 'chapter': current['chapter'], 'local_number': current['local_number'],
                       'numbering_system': 'Chinese edition chapter-local numbers; not canonical global Ibn Majah numbers',
                       'source_cited': [f"伊本·马哲圣训集 / Sunan Ibn Majah, chapter {current['chapter']}, local no. {current['local_number']}"],
                       'source_sequence_position': len(records) + 1,
                       'printed_marker_raw': current['marker_raw'], 'printed_marker_corrected': current['marker']},
            'narrator': {'name': narrator.group(1) if narrator else None,
                         'name_as_extracted': narrator.group(1) if narrator else None,
                         'basis': 'Source attribution prefix in Chinese OCR; no Arabic identity inferred'},
            'isnad': None,
            'translator': {'name': '穆萨·余崇仁', 'role': 'named published translator',
                           'evidence': f'materials/{SLUG}/source-metadata.json#title-pdf-page-2'},
            'translation_provenance': {'origin': 'human_translator_credited', 'label': 'Human',
                                      'ai_translation': False, 'human_involvement': 'named_human_translator',
                                      'basis': 'Named Chinese translator credited on PDF title page 2 and 2013 printed edition colophon page 486.',
                                      'evidence_ids': [f'materials/{SLUG}/source-metadata.json'],
                                      'scope_note': 'Published Chinese source wording; no new translation generated. OCR fidelity is separately pending.'},
            'ai_translation': False, 'topic_tags': [], 'source_headings': current['headings'],
            'editorial_tags': ['source:' + SLUG, 'language:zh-CN', 'book:ibn-majah', 'method:abbyy_ocr_pdf_layer',
                              'numbering:chapter_local', 'canonical_mapping:unknown'],
            'commentary': {'arabic': None, 'translation': None, 'items': [],
                           'excluded_audit': f'materials/{SLUG}/audit/excluded-lines.jsonl.gz'},
            'footnotes': [{**reference, 'text': None,
                           'status': 'marker_separated; full page footnotes preserved in audit, not in hadith search text',
                           'audit_path': f'materials/{SLUG}/audit/footnotes.jsonl.gz'} for reference in footnote_references],
            'references': {'items': [], 'canonical_mapping_status': 'unknown; chapter-local source labels only'},
            'grading': {'grade': None, 'grader': None, 'basis': 'No authenticity grade inferred from inclusion in Sunan Ibn Majah'},
            'page': {'pdf': pdf_pages, 'printed': [p - 63 for p in pdf_pages], 'sheet': None, 'row': None,
                     'basis': 'One-based PDF page index; printed body pages 1–416 map to PDF64–479'},
            'source_locator': {'file': f'materials/{SLUG}/{PDF_NAME}', 'sha256': original_hash,
                               'pdf_pages': pdf_pages, 'index_base': 1, 'lines': locators,
                               'raw_segment_path': f'materials/{SLUG}/audit/record-segments.jsonl.gz',
                               'raw_segment_id': current['id']},
            'source_defects': [{'type': 'possible_ocr_latin_artifact', 'tokens': suspect_latin}] if suspect_latin else [],
            'related_versions': [],
            'review': {'status': 'ocr_source_review_pending', 'issues': issues, 'ocr_qc': 'pending',
                       'independent_pro_qc': 'pending', 'release_status': 'source_candidate',
                       'release_eligible': False, 'certified_release_eligible': False,
                       'character_collation': 'not_complete', 'narrational_authenticity': 'not_assessed'},
            'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                       'source_notice_preserved_in': f'materials/{SLUG}/{PDF_NAME}',
                       'owner_upload_authorization_is_not_publisher_license': True},
            'extraction': {'method': 'abbyy_ocr_pdf_layer_geometry_extraction', 'ocr_used': True,
                           'is_excerpt': False, 'source_pdf_sha256': original_hash, 'supplied_txt_consulted': False,
                           'arabic_original_status': 'not_present_in_this_Chinese_hadith_body',
                           'full_isnad_status': 'abridged_by_published_translator',
                           'commentary_policy': 'Headings, running headers, printed footers, and page footnotes separated; integral narration quotations retained.',
                           'corrections_path': f'materials/{SLUG}/audit/verified-corrections.json',
                           'whitespace_policy': 'Join extracted PDF line wraps; trim layout whitespace at line boundaries only; do not normalize punctuation or wording.'}}
        if suspect_symbols:
            row['source_defects'].append({'type': 'possible_ocr_symbol_artifact', 'tokens': suspect_symbols})
        records.append(row)
        segments.append({'id': current['id'], 'chapter': current['chapter'], 'local_number': current['local_number'],
                         'lines': current['lines'], 'text_before_body_corrections_and_marker_removal': before_body_corrections,
                         'text_final_sha256': hashlib.sha256(text.encode()).hexdigest()})
        current = None

    for page in pages:
        n = page['pdf_page']
        if not 64 <= n <= 479:
            excluded.append({'pdf_page': n, 'reason': 'front_matter_or_end_matter', 'line_indices': [l['line_index'] for l in page['lines']]})
            continue
        if n in starts:
            finish()
            current_chapter = starts[n]
            section_title = None
            candidates = [l['text'].strip() for l in page['lines']
                          if l['bbox'][1] > 80 and re.match(r'^第.{1,12}章', l['text'].strip())]
            if len(candidates) != 1:
                raise ValueError(f'Chapter title ambiguous on PDF{n}: {candidates!r}')
            chapter_title = candidates[0]
            chapters.append({'chapter': current_chapter, 'title': chapter_title,
                             'start_pdf_page': n, 'printed_start_page': n - 63,
                             'expected_count': expected[str(current_chapter)]['expected_count_from_final_local_number']})
        in_footnotes = False
        for line in page['lines']:
            raw = line['text'].strip()
            text = line.get('corrected_text', line['text']).strip()
            role = line_role(line, page)
            if role in ('running_header', 'printed_page_footer', 'rule_or_scan_noise', 'opening_formula',
                        'citation_ocr_fragment_replaced_from_page_image'):
                excluded.append({'pdf_page': n, 'reason': role, **line})
                continue
            if text == chapter_title and n in starts:
                excluded.append({'pdf_page': n, 'reason': 'chapter_heading', **line})
                continue
            size = line['cjk_median_font_size']
            if (size is not None and size < 9.4 and line['bbox'][1] > 400 and len(text) > 8) or (CIRCLED.match(text) and line['bbox'][1] > 400):
                in_footnotes = True
            if in_footnotes:
                footnotes.append({'pdf_page': n, **line})
                excluded.append({'pdf_page': n, 'reason': 'page_footnote', **line})
                continue
            if role == 'section_heading':
                finish()
                section_title = text
                excluded.append({'pdf_page': n, 'reason': role, **line})
                continue
            marker = MARKER.match(text)
            if marker:
                finish()
                local_no = int(marker.group(1))
                sequence[current_chapter].append(local_no)
                identifier = f'zh-ibn-majah-{original_hash[:16]}-c{current_chapter:02d}-n{local_no:03d}'
                current = {'id': identifier, 'chapter': current_chapter, 'local_number': local_no,
                           'marker': marker.group(0), 'marker_raw': line.get('original_marker', marker.group(0)),
                           'headings': [x for x in (chapter_title, section_title) if x], 'lines': []}
                text = text[marker.end():].lstrip()
            if current is None:
                if text:
                    excluded.append({'pdf_page': n, 'reason': 'unassigned_text_requires_review', **line})
                continue
            if text:
                current['lines'].append({'pdf_page': n, 'line_index': line['line_index'], 'bbox': line['bbox'],
                                         'raw_text': line['text'], 'text': text})
    finish()
    for chapter in chapters:
        expected_seq = list(range(1, chapter['expected_count'] + 1))
        actual = sequence[chapter['chapter']]
        if actual != expected_seq:
            missing = sorted(set(expected_seq) - set(actual))
            duplicates = [n for n, count in collections.Counter(actual).items() if count != 1]
            raise ValueError(f'Chapter {chapter["chapter"]} numbering mismatch: missing={missing}, duplicates={duplicates}, actual_count={len(actual)}')
        chapter['actual_count'] = len(actual)
    if len(records) != expected_total or len({r['id'] for r in records}) != len(records):
        raise ValueError('Total or stable occurrence identity mismatch')
    records_path = material / 'records.jsonl'
    records_path.write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in records), encoding='utf-8')
    write_jsonl_gz(audit / 'excluded-lines.jsonl.gz', excluded)
    write_jsonl_gz(audit / 'footnotes.jsonl.gz', footnotes)
    write_jsonl_gz(audit / 'record-segments.jsonl.gz', segments)
    write_json(audit / 'applied-corrections.json', applied)
    write_json(audit / 'chapters.json', chapters)
    anomaly_rows = [{'id': r['id'], 'chapter': r['number']['chapter'], 'local_number': r['number']['local_number'],
                     'pdf_pages': r['page']['pdf'], 'issues': r['review']['issues'][1:], 'source_defects': r['source_defects']}
                    for r in records if len(r['review']['issues']) > 1]
    write_json(audit / 'ocr-anomalies.json', anomaly_rows)
    summary = {'source_sha256': original_hash, 'records_sha256': sha256(records_path),
               'record_count': len(records), 'chapter_count': len(chapters), 'main_body_pdf_pages': [64, 479],
               'main_body_printed_pages': [1, 416], 'source_pdf_pages': len(document),
               'all_local_number_sequences_complete': True,
               'numbering_note': '4,354 source numbered occurrences. The generic introduction gives 4,341 for Ibn Majah; source chapter-local enumeration is retained without inventing canonical matches.',
               'cross_page_occurrences': sum(len(r['page']['pdf']) > 1 for r in records),
               'source_footnote_lines_excluded': len(footnotes), 'excluded_lines_by_reason': dict(collections.Counter(r['reason'] for r in excluded)),
               'applied_number_marker_corrections': sum(x['kind'] == 'number_marker' for x in applied),
               'applied_body_corrections': sum(x['kind'] == 'narration_text' for x in applied),
               'records_with_automatically_detected_possible_ocr_artifacts': len(anomaly_rows),
               'full_character_fidelity_review_complete': False, 'independent_pro_qc': 'pending',
               'certified_release_eligible': False, 'supplied_txt_consulted': False,
               'pdf_is_primary_authority': True, 'duplicate_occurrences_deduplicated': False,
               'unassigned_text': [x for x in excluded if x['reason'] == 'unassigned_text_requires_review']}
    write_json(material / 'integration-audit.json', summary)
    metadata = {**corrections['metadata'], 'source_sha256': original_hash,
                'source_file': f'materials/{SLUG}/{PDF_NAME}', 'original_filename': '736950612-1.pdf',
                'source_pdf_metadata': document.metadata, 'source_pdf_page_count': len(document),
                'edition_key': f'yu-2013-pdf-{original_hash[:16]}',
                'full_isnad_omitted_by_source_translator': True, 'isnad_scope_evidence_pdf_pages': [15, 16],
                'translation_origin': 'published_named_human_translator', 'ai_translation': False,
                'title_and_translator_evidence_pdf_page': 2, 'colophon_evidence_pdf_page': 486,
                'extraction_method': 'ABBYY OCR layer of scanned source PDF; MuPDF geometry segmentation and Poppler raw text archive',
                'extraction_software': {'pymupdf': fitz.VersionBind,
                                        'pdftotext': subprocess.run(['pdftotext', '-v'], capture_output=True, text=True).stderr.splitlines()[0]},
                'ocr_used': True, 'txt_consulted': False,
                'source_body_page_range': [64, 479], 'source_body_printed_range': [1, 416],
                'rights': {'status': 'not_assessed_for_publication', 'publisher_license': None,
                           'source_notice_preserved_in_original_pdf': True},
                'review': {'source_page_regions_visually_checked': sorted({2, 486} | {p['pdf_page'] for p in corrections['number_corrections'] + corrections['body_corrections']}),
                           'review_scope': 'Bibliographic fields, damaged number markers, and targeted body corrections recorded in the correction audit; not full character collation.',
                           'independent_pro_qc': 'pending', 'certified_release_eligible': False}}
    write_json(material / 'source-metadata.json', metadata)
    print(json.dumps({k: v for k, v in summary.items() if k != 'unassigned_text'}, ensure_ascii=False, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--pdf', type=Path, required=True)
    args = parser.parse_args()
    import_pdf(args.root.resolve(), args.pdf.resolve())
