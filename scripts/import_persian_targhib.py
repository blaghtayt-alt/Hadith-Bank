#!/usr/bin/env python3
"""Register the three supplied Targhib DOCX volumes from preserved extractions.

This adapter verifies quotation spans against the original OOXML, decodes only
documented custom-font runs, and separates specifically reviewed inline comments.
It never generates translations, invents canonical numbers, or deduplicates.
"""
import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from register_material import register
from material_registry import SOURCE_IMPORT_DECISION


IMPORT = 'imports/persian-targhib-20261111'
FONT_EVIDENCE = 'imports/persian-docx-20261111/audit/font-evidence/font-decoding-evidence.json'
BOOK = 'targhib-wa-tarhib'
TRANSLATOR = 'موسی بازماندگان'
TITLE = 'الترغيب والترهيب صحيح [وضعيف]'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
SOURCE_HASHES = {
    1: 'e63b6f070089e91d013f8e4e5757871701d54a4d7aa487c8f98e0e994c7304a4',
    2: '613679de5d9b9bd579c1a79aa6647bf845f239b2887e3736f21d510a906bbede',
    3: 'f1b4f5afb2c227350e0fb634aa177e0ce080bd31e4da421592c01206907ca33e',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_data(path):
    path = Path(path)
    if not path.exists() and Path(str(path) + '.gz').exists():
        path = Path(str(path) + '.gz')
    raw = gzip.decompress(path.read_bytes()).decode('utf-8') if path.suffix == '.gz' else path.read_text(encoding='utf-8')
    return [json.loads(line) for line in raw.splitlines()] if '.jsonl' in path.name else json.loads(raw)


def read_source(path, volume, font_evidence):
    """Use the same zero-based descendant-paragraph order as the source ledger."""
    cmap = font_evidence['ctraditional']['map']
    amap = {chr(int(k, 16)): v for k, v in font_evidence['aga']['map'].items()}
    amap['\uf020'] = ' '
    paragraphs = {}
    with ZipFile(path) as archive:
        for part in ('word/document.xml', 'word/footnotes.xml', 'word/endnotes.xml'):
            if part not in archive.namelist():
                continue
            xml = ET.fromstring(archive.read(part))
            for index, p in enumerate(xml.findall('.//' + W + 'p')):
                raw, decoded, offsets, changes, anchors = '', '', [0], [], []
                for ri, run in enumerate(p.findall('.//' + W + 'r')):
                    fonts_node = run.find(W + 'rPr/' + W + 'rFonts')
                    fonts = list(fonts_node.attrib.values()) if fonts_node is not None else []
                    cmap_run = cmap if 'CTraditional Arabic' in fonts else amap if any(f.startswith('AGA Arabesque') for f in fonts) else {}
                    # Dump/extractor concatenate run text, then preserve non-text tokens.
                    text = ''.join((e.text or '') if e.tag == W + 't' else '\t' if e.tag == W + 'tab' else '\n' if e.tag == W + 'br' else '' for e in run)
                    for char in text:
                        replacement = cmap_run.get(char, char)
                        if replacement != char:
                            changes.append({'run': ri, 'raw_offset': len(raw), 'original': char, 'decoded': replacement})
                        raw += char
                        decoded += replacement
                        offsets.append(len(decoded))
                    custom_footnote_mark = False
                    for token in run:
                        if token.tag == W + 'footnoteReference':
                            anchors.append({'decoded_offset': len(decoded), 'id': token.get(W + 'id')})
                            custom_footnote_mark = token.get(W + 'customMarkFollows') == '1'
                        elif token.tag == W + 'sym':
                            char = chr(int(token.get(W + 'char'), 16))
                            family = token.get(W + 'font', '')
                            mapping = cmap if family == 'CTraditional Arabic' else amap if family.startswith('AGA Arabesque') else {}
                            replacement = mapping.get(char, char)
                            annotation = custom_footnote_mark and family == 'MRT_Nazanin' and token.get(W + 'char').upper() == 'F020'
                            if annotation:
                                replacement = ' '
                            decoded += replacement
                            offsets[-1] = len(decoded)
                            changes.append({'run': ri, 'raw_offset': len(raw), 'symbol': token.get(W + 'char'), 'font': family, 'decoded': replacement,
                                            'role': 'custom_footnote_annotation_replaced_with_word_boundary' if annotation else 'font_symbol'})
                pid = f'v{volume}:{Path(part).stem}:p{index:05d}'
                paragraphs[pid] = {'id': pid, 'part': part, 'index': index, 'raw': raw, 'decoded': decoded, 'offsets': offsets, 'font_changes': changes, 'footnote_anchors': anchors}
    return paragraphs


def reviewed_patches(raw_patches, paragraphs):
    mapped = {}
    for patch in raw_patches['patches']:
        pid = f'v{patch["volume"]}:document:p{patch["paragraph_1based"] - 1:05d}'
        source = paragraphs[pid]
        assert source['raw'] == patch['source_text'], ('Inline-patch source differs', pid)
        assert hashlib.sha256(source['raw'].encode()).hexdigest() == patch['source_sha256']
        for i, change in enumerate(patch['remove_spans']):
            a, b = change['start'], change['end']
            assert source['raw'][a:b] == change['text'], pid
            start, end = source['offsets'][a], source['offsets'][b]
            mapped.setdefault(pid, []).append({**change, 'start': start, 'end': end,
                'raw_start': a, 'raw_end': b, 'decoded_text': source['decoded'][start:end],
                'language': change.get('language', patch.get('language', 'translation')),
                'patch_id': f'{pid}:inline-{i + 1:02d}'})
    return mapped


def apply_removals(text, operations):
    """Apply the union of source-bound deletion ranges once, retaining all else."""
    merged = []
    for start, end, replacement in sorted(operations):
        assert replacement == '' and 0 <= start <= end <= len(text)
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    for start, end in reversed(merged):
        text = text[:start] + text[end:]
    return text


def materialize_main_text(row, paragraphs, patches):
    result, audit, applied = {}, {}, []
    for language in ('arabic', 'translation'):
        before_parts, after_parts, audit_parts = [], [], []
        for span in row['extraction_spans'][language]:
            pid = span['paragraph_id']
            source = paragraphs[pid]
            start, end = span['start'], span['end']
            raw = source['decoded'][start:end]
            assert raw == span['raw_decoded_span'], ('Source-span mismatch', row['id'], pid)
            operations = []
            for change in span.get('transformations', []):
                assert change['operation'] == 'remove_empty_footnote_anchor_parentheses', change
                a, b = change['start'] - start, change['end'] - start
                assert raw[a:b] == change['original'] and source['footnote_anchors']
                operations.append((a, b, ''))
            before = apply_removals(raw, operations)
            before_parts.append(before.strip())
            inline = []
            for change in patches.get(pid, []):
                if change['language'] != language or change['end'] <= start or change['start'] >= end:
                    continue
                assert start <= change['start'] < change['end'] <= end, ('Partially overlapping patch', row['id'], pid)
                operations.append((change['start'] - start, change['end'] - start, ''))
                inline.append(change['patch_id'])
                applied.append(change['patch_id'])
            after = apply_removals(raw, operations)
            after_parts.append(after.strip())
            audit_parts.append({'paragraph_id': pid, 'start': start, 'end': end,
                                'coordinate_system': 'font-decoded source Unicode codepoints',
                                'source_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                                'extractor_transformations': span.get('transformations', []),
                                'inline_patch_ids': inline})
        expected = '\n'.join(before_parts)
        assert expected == (row['text'][language] or ''), ('Adapter text differs from extractor', row['id'], language)
        result[language] = '\n'.join(after_parts) or None
        audit[language] = audit_parts
    return result, audit, applied


def materialize_ancillary_text(row, paragraphs):
    result, audit = {}, {}
    for language in ('arabic', 'translation'):
        pieces, audit_parts = [], []
        for span in row['source_locator']['spans'][language]:
            pid = f'v{row["source_volume"]}:{Path(span["part"]).stem}:p{span["paragraph_index_zero_based"]:05d}'
            source = paragraphs[pid]
            a, b = span['start_char'], span['end_char']
            assert source['raw'][a:b] == span['text_as_extracted'], ('Ancillary source-span mismatch', row['id'], pid)
            start, end = source['offsets'][a], source['offsets'][b]
            text = source['decoded'][start:end]
            # Only actual footnote-anchor parentheses are removed from a quotation.
            if source['footnote_anchors']:
                text = re.sub(r'\(\s*\)', '', text)
            pieces.append(text.strip())
            audit_parts.append({'paragraph_id': pid, 'start_char': a, 'end_char': b,
                                'coordinate_system': 'raw OOXML text Unicode codepoints',
                                'raw_sha256': hashlib.sha256(span['text_as_extracted'].encode()).hexdigest()})
        result[language] = '\n'.join(pieces) or None
        audit[language] = audit_parts
    return result, audit


def adapt(row, text, span_audit, applied, volume, ancillary=False):
    slug = f'fa-targhib-bazmandegan-v{volume}'
    edition = f'bazmandegan-1397-v{volume}'
    local = copy.deepcopy(row.get('local_numbers') or {})
    printed = local.get('unified')
    supplemental = printed == '0'
    kind = row.get('kind') or row.get('record_type') or 'hadith_excerpt'
    excerpt = ancillary or bool(row.get('source_notes', {}).get('is_source_excerpt'))
    grade = row.get('source_grade')
    grading = copy.deepcopy(row.get('grading') or {})
    if grade:
        grading.update({'source_grade_as_printed': grade,
                        'grader': row.get('source_grade_grader_override', row.get('source_grade_grader')),
                        'edition_grading_credit': 'محمد ناصر الدين الألبانی',
                        'attribution_basis': row.get('source_grade_attribution_basis') or row.get('source_grade_attribution') or 'Assessment printed in the supplied edition; the title page credits al-Albani for takhrij. An individual assessor is not inferred for an unattributed quotation.',
                        'independent_bank_grade': None})
    else:
        grading.setdefault('grade', None)
        grading.setdefault('grader', None)
        grading.setdefault('basis', 'No occurrence-specific assessment supplied; no grade inherited from another report.')
        grade = grading.get('grade') or grading.get('source_grade_as_printed')
    companion = 'companion' in kind or bool(grade and 'موقوف' in grade)
    successor = 'successor' in kind or bool(grade and 'مقطوع' in grade)
    record_type = 'companion_report_excerpt' if companion and excerpt else 'companion_report' if companion else 'successor_report' if successor else 'hadith_excerpt' if excerpt else 'hadith_occurrence'
    title = 'Companion report' if companion else 'Successor report' if successor else 'Hadith excerpt' if excerpt else 'Hadith'
    if printed and not supplemental:
        title += ' ' + printed
    elif supplemental:
        title += ' · supplemental source entry'
    if grade:
        title += ' — source grade: ' + str(grade)
    elif excerpt:
        title += ' — grade not supplied'
    notes = []
    if text['translation'] is None:
        notes.append('Persian translation is absent or not securely aligned for this source unit; no translation was generated.')
    if text['arabic'] is None:
        notes.append('Arabic text is not supplied or securely aligned for this occurrence; no original was reconstructed.')
    if supplemental:
        notes.append('The printed leading zero marks a supplemental source entry, not canonical hadith number 0.')
    if applied:
        notes.append('Separately reviewed translator/editorial explanation was excluded from narration text; exact original and removed spans remain in the import audit.')
    supplied_notes = row.get('source_notes')
    if isinstance(supplied_notes, list):
        notes.extend(copy.deepcopy(supplied_notes))
    elif isinstance(supplied_notes, dict):
        if supplied_notes.get('alignment') == 'unpaired_unequal_units':
            notes.append('This source unit has no securely established bilingual alignment; the separate source wording is preserved.')
        if supplied_notes.get('pending_paragraph_review'):
            notes.append('Source context has unresolved extraction boundaries; consult the preserved audit.')
        notes.extend(supplied_notes.get('issues', []))
    notes.extend(copy.deepcopy(row.get('source_defects') or []))
    unresolved_glyphs = sorted({f'U+{ord(char):04X}' for value in text.values() if value for char in value if unicodedata.category(char) == 'Co'})
    if unresolved_glyphs:
        notes.append('Unresolved original source font token(s) ' + ', '.join(unresolved_glyphs) + ' are preserved. No exact font mapping is evidenced; consult the original DOCX rather than assume a replacement character.')
    headings_value = row.get('source_headings') or []
    headings = [x['text'] for x in headings_value.values()] if isinstance(headings_value, dict) else [x['text'] if isinstance(x, dict) else x for x in headings_value]
    references = copy.deepcopy(row.get('references') or [])
    if isinstance(references, list):
        references = {'items': references}
    for item in references.get('items', []):
        if not item.get('scope'):
            item['scope'] = 'source_citation' if ancillary else 'surrounding_source_block_context'
    references['canonical_mapping_status'] = 'Source attribution only; no independent canonical collection-number match asserted.'
    if grade:
        references['source_grade_as_printed'] = str(grade)
    metadata_path = f'materials/{slug}/source-metadata.json'
    ids = sorted({s['paragraph_id'] for spans in span_audit.values() for s in spans})
    locator = {'file': f'materials/{slug}/source.docx', 'parts': sorted({paragraph_id.split(':')[1] for paragraph_id in ids}),
               'index_base': 0, 'paragraph_ids': ids,
               'extraction_audit': f'{IMPORT}/audit/final-text-spans.jsonl.gz', 'extraction_audit_id': row['id']}
    record = {
        'id': row['id'], 'language': 'fa', 'book_key': BOOK, 'edition': edition,
        'title': title, 'text': text, 'record_type': record_type,
        'content_kind': 'quoted_companion_saying' if companion else 'successor_report' if successor else 'hadith_quotation_excerpt' if excerpt else 'numbered_source_narration',
        'source': {'title': TITLE, 'url': 'https://www.qalamlib.com/', 'volume': volume,
                   'original_filename': f'targheeb-va-tarheeb-saheeh-va-zaeef-{volume}-Word.docx',
                   'metadata_path': metadata_path, 'work_scope': 'Combined Sahih and Daif Targhib source edition; contains differently graded reports.'},
        'number': {'in_book': printed if printed and not supplemental else None, 'source_entry_id': None,
                   'canonical': None, 'source_cited': [], 'printed_labels': local or None,
                   'numbering_system': 'Unified source sequence / classified subcollection / chapter-local label; not canonical collection numbering'},
        'narrator': copy.deepcopy(row.get('narrator') or {'name': None, 'basis': 'Attribution remains within supplied narration; no name inferred.'}),
        'isnad': row.get('isnad'),
        'translator': copy.deepcopy(row.get('translator') or {'name': TRANSLATOR, 'evidence': metadata_path, 'role': 'named source translator'}),
        'translation_provenance': {'origin': 'human_translator_credited', 'label': 'Human', 'ai_translation': False,
            'human_involvement': 'named_human_translator', 'basis': 'Translator credit printed in all three supplied source volumes.',
            'evidence_ids': [metadata_path], 'scope_note': 'Existing published Persian wording; no new translation was produced.'},
        'ai_translation': False, 'topic_tags': [], 'source_headings': headings,
        'source_structure_tags': [{'origin': 'source_book_structure', 'source_id': slug, 'hierarchy': i + 1, 'value_verbatim': h,
                                  'locator_scope': 'narration_under_heading'} for i, h in enumerate(headings)],
        'editorial_tags': {'origin': 'import_pipeline_not_publisher', 'values': [
            'source:' + slug, 'language:fa', 'method:direct_ooxml', 'book:' + BOOK, 'edition:' + edition,
            'format:docx', 'kind:' + record_type, 'ai_translation:false',
            'arabic:' + ('supplied' if text['arabic'] else 'not_supplied'),
            'translation:' + ('supplied' if text['translation'] else 'not_supplied')]},
        'commentary': {'arabic': None, 'translation': None}, 'footnotes': [],
        'references': references, 'grading': grading,
        'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None, 'docx_paragraphs': ids, 'index_base': 0,
                 'basis': 'Exact OOXML paragraph/span locators; reliable occurrence-level printed pagination is unavailable.'},
        'source_locator': locator, 'source_defects': notes,
        'related_versions': [],
        'review': {'status': 'native_source_import', 'issues': copy.deepcopy(notes), 'independent_pro_qc': 'not_performed',
                   'release_status': 'source_import', 'release_eligible': False, 'certified_release_eligible': False},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None, 'source_notice_preserved_in': f'materials/{slug}/source.docx'},
        'extraction': {'method': 'direct_ooxml', 'ocr_used': False, 'is_excerpt': excerpt,
                       'new_translation_produced': False, 'side_commentary_included': False,
                       'batch_limit': None, 'deduplicated': False, 'font_evidence': FONT_EVIDENCE,
                       'bilingual_alignment': (row.get('source_notes') or {}).get('alignment') if isinstance(row.get('source_notes'), dict) else None,
                       'unresolved_source_glyphs': unresolved_glyphs,
                       'source_extraction': f'{IMPORT}/extracted/' + ('ancillary-targhib.jsonl.gz' if ancillary else f'v{volume}-records.jsonl.gz'),
                       'source_extraction_id': row['id'], 'inline_commentary_patch_ids': applied},
    }
    parent = row.get('related_parent_id')
    if parent:
        record['source_locator']['source_block_id'] = parent
    if row.get('fragment_group_key'):
        record['source_locator']['fragment_group_id'] = row['fragment_group_key']
        note = 'This quotation is a fragment of the source report at ' + row['fragment_group_key'] + '; separately retained fragments are not complete independent hadiths.'
        record['source_defects'].append(note)
        record['review']['issues'].append(note)
    return record


def attach_source_qualifications(record, review):
    """Keep observed source translation defects visible without rewriting text."""
    paragraph_ids = set(record['source_locator']['paragraph_ids'])
    findings = []
    for finding in review.get('confirmed_source_translation_concerns', []):
        points = finding.get('paragraphs_1based', [])
        if finding.get('paragraph_1based') is not None:
            points = points + [finding['paragraph_1based']]
        locators = {f'v{finding["volume"]}:document:p{int(p) - 1:05d}' for p in points}
        if not (paragraph_ids & locators):
            continue
        findings.append({'issue': finding['issue'], 'source_paragraphs': sorted(paragraph_ids & locators),
                         'audit': IMPORT + '/audit/ideology-review.json.gz',
                         'resolution': 'Original source wording retained; no new translation or certification.'})
        note = 'Source translation qualification: ' + finding['issue']
        record['source_defects'].append(note)
        record['review']['issues'].append(note)
    if findings:
        record['source_translation_qualifications'] = findings
    for finding in review.get('continued_source_qualifications', []):
        locators = set(finding.get('paragraph_ids', []))
        if finding.get('paragraph_id'):
            locators.add(finding['paragraph_id'])
        if not (paragraph_ids & locators):
            continue
        note = 'Source qualification: ' + finding['issue']
        record['source_defects'].append(note)
        record['review']['issues'].append(note)


def additional_rows(selections, main_rows, ancillary, paragraphs, volume):
    """Recover reviewed disjoint quotations without counting a physical span twice."""
    occupied = {}
    for row in main_rows:
        for language, spans in row['extraction_spans'].items():
            for span in spans:
                occupied.setdefault(span['paragraph_id'], []).append((span['start'], span['end']))
    for row in ancillary:
        if row['source_volume'] != volume:
            continue
        for language, spans in row['source_locator']['spans'].items():
            for span in spans:
                pid = f'v{volume}:{Path(span["part"]).stem}:p{span["paragraph_index_zero_based"]:05d}'
                offsets = paragraphs[pid]['offsets']
                occupied.setdefault(pid, []).append((offsets[span['start_char']], offsets[span['end_char']]))
    rows, skipped = [], []
    for selection in selections:
        pid = selection['paragraph_id']
        if not pid.startswith(f'v{volume}:'):
            continue
        source = paragraphs[pid]
        assert hashlib.sha256(source['decoded'].encode()).hexdigest() == selection['decoded_sha256'], ('Additional quotation source mismatch', pid)
        a, b = selection['start'], selection['end']
        assert 0 <= a < b <= len(source['decoded']) and source['decoded'][a:b] == selection['text'], ('Additional quotation span mismatch', pid)
        language = {'ar': 'arabic', 'fa': 'translation'}[selection['language']]
        previous = occupied.get(pid, [])
        if any(x <= a and b <= y for x, y in previous):
            skipped.append({'paragraph_id': pid, 'start': a, 'end': b, 'reason': 'Same physical quotation already included in another selected source span.'})
            continue
        assert not any(a < y and x < b for x, y in previous), ('Partially overlapping quotation selections', pid, a, b)
        raw = source['decoded'][a:b]
        transformations = []
        if source['footnote_anchors']:
            transformations = [{'operation': 'remove_empty_footnote_anchor_parentheses', 'start': a + m.start(),
                                'end': a + m.end(), 'original': m.group()} for m in re.finditer(r'\(\s*\)', raw)]
        text = re.sub(r'\(\s*\)', '', raw).strip() if transformations else raw.strip()
        fields = {'arabic': None, 'translation': None}
        fields[language] = text
        spans = {'arabic': [], 'translation': []}
        spans[language].append({'paragraph_id': pid, 'start': a, 'end': b, 'raw_decoded_span': raw,
                                'transformations': transformations})
        row = {'id': f'fa-targhib-v{volume}-quote-p{source["index"]:05d}-s{a:05d}',
               'volume': volume, 'kind': selection.get('kind', 'hadith_excerpt'), 'text': fields,
               'source_grade': selection.get('source_grade'), 'references': selection.get('references', []),
               'source_notes': {'is_source_excerpt': True, 'alignment': 'separately_reviewed_quotation',
                                'issues': ['Bounded quotation inside source commentary; surrounding explanation excluded.']},
               'extraction_spans': spans}
        for key in ('source_grade_grader', 'source_grade_grader_override', 'source_grade_attribution', 'source_grade_attribution_basis', 'bilingual_pair_key', 'fragment_group_key'):
            if key in selection:
                row[key] = selection[key]
        rows.append(row)
        occupied.setdefault(pid, []).append((a, b))
    paired, groups = [], {}
    for row in rows:
        pair = row.get('bilingual_pair_key')
        if pair:
            groups.setdefault(pair, []).append(row)
        else:
            paired.append(row)
    for key, members in groups.items():
        if len(members) == 1:
            paired.extend(members)
            continue
        assert len(members) == 2 and {next(lang for lang, text in row['text'].items() if text) for row in members} == {'arabic', 'translation'}, ('Invalid reviewed bilingual pair', key)
        primary = copy.deepcopy(next(row for row in members if row['text']['arabic']))
        translated = next(row for row in members if row['text']['translation'])
        assert primary['kind'] == translated['kind'], ('Bilingual report kinds differ', key)
        assert not primary['source_grade'] or not translated['source_grade'] or primary['source_grade'] == translated['source_grade'], ('Bilingual grade conflict', key)
        primary['text']['translation'] = translated['text']['translation']
        primary['extraction_spans']['translation'] = translated['extraction_spans']['translation']
        primary['source_notes']['alignment'] = 'explicit_reviewed_bilingual_quotation_pair'
        if not primary['source_grade']:
            primary['source_grade'] = translated['source_grade']
        paired.append(primary)
    return paired, skipped


def run(root, input_root, source_root=None):
    font = read_data(root / FONT_EVIDENCE)
    originals, paragraphs = {}, {}
    for volume in (1, 2, 3):
        filename = f'targheeb-va-tarheeb-saheeh-va-zaeef-{volume}-Word.docx'
        original = source_root / filename if source_root else root / f'materials/fa-targhib-bazmandegan-v{volume}/source.docx'
        assert digest(original) == SOURCE_HASHES[volume], ('Original DOCX hash differs', volume)
        originals[volume] = original
        paragraphs.update(read_source(original, volume, font))
    patch_input = read_data(input_root / 'inline-commentary-patches.json')
    patches = reviewed_patches(patch_input, paragraphs)
    ancillary = read_data(input_root / 'ancillary-targhib.jsonl')
    content_review = read_data(root / IMPORT / 'audit/ideology-review.json')
    content_review['continued_source_qualifications'] = read_data(root / IMPORT / 'audit/source-qualifications.json')
    selections = read_data(input_root / 'additional-quotation-spans.json')
    exclusions = {item['id']: item for item in read_data(input_root / 'excluded-source-units.json')}
    all_rows, all_audit, all_applied, counts, skipped_quotes, omitted = [], [], [], [], [], []
    for volume in (1, 2, 3):
        records = []
        main_rows = read_data(input_root / f'v{volume}-records.jsonl')
        extra_rows, skipped = additional_rows(selections, main_rows, ancillary, paragraphs, volume)
        extra_ids = {row['id'] for row in extra_rows}
        skipped_quotes.extend(skipped)
        for row in main_rows + extra_rows:
            text, audit, applied = materialize_main_text(row, paragraphs, patches)
            record = adapt(row, text, audit, applied, volume)
            if row['id'] in extra_ids:
                record['extraction']['source_extraction'] = IMPORT + '/extracted/additional-quotation-spans.json.gz'
            if row['id'] in exclusions:
                omitted.append({'scope_decision': exclusions[row['id']], 'candidate_record': record, 'text_spans': audit})
                continue
            records.append(record)
            all_audit.append({'id': row['id'], 'text_spans': audit, 'final_text_sha256': hashlib.sha256(json.dumps(text, ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
            all_applied.extend(applied)
        for row in ancillary:
            if row['source_volume'] != volume:
                continue
            text, audit = materialize_ancillary_text(row, paragraphs)
            records.append(adapt(row, text, audit, [], volume, ancillary=True))
            all_audit.append({'id': row['id'], 'text_spans': audit, 'final_text_sha256': hashlib.sha256(json.dumps(text, ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
        for record in records:
            attach_source_qualifications(record, content_review)
            assert any(record['text'].values()), ('Empty narration', record['id'])
        fragment_groups = {}
        for record in records:
            group = record['source_locator'].get('fragment_group_id')
            if group:
                fragment_groups.setdefault(group, []).append(record['id'])
        for record in records:
            group = record['source_locator'].get('fragment_group_id')
            if group:
                record['related_versions'] = [{'id': ident, 'relation': 'another_fragment_of_same_source_report',
                                               'basis': 'Exact reviewed source paragraph and commentary context.'}
                                              for ident in fragment_groups[group] if ident != record['id']]
        slug = f'fa-targhib-bazmandegan-v{volume}'
        folder = root / 'materials' / slug
        folder.mkdir(parents=True, exist_ok=True)
        if originals[volume].resolve() != (folder / 'source.docx').resolve():
            shutil.copyfile(originals[volume], folder / 'source.docx')
        record_file = folder / 'records.jsonl'
        record_file.write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in records), encoding='utf-8')
        metadata = {'title': TITLE, 'volume': volume, 'author_as_printed': 'ابومحمد، زكی الدين المنذری',
                    'translator_as_printed': TRANSLATOR, 'takhrij_as_printed': 'محمد ناصر الدين الألبانی',
                    'edition_as_printed': 'اول (دیجیتال)', 'date_as_printed': 'مهر (میزان) 1397 ه‍ .ش - محرم 1440 ه‍ .ق',
                    'source_as_printed': 'کتابخانه قلم www.qalamlib.com',
                    'source_sha256': SOURCE_HASHES[volume], 'title_page_part': 'word/document.xml',
                    'credit_paragraphs_zero_based': [10, 11, 14, 15, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 33, 34, 35, 36, 37, 38],
                    'commentary_policy': 'Hadith/report quotations only; editorial commentary, introductions and footnote prose remain outside the reader payload.',
                    'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None},
                    'imported_record_count': len(records)}
        write_json(folder / 'source-metadata.json', metadata)
        register(root, f'materials/{slug}', 'fa', BOOK, f'bazmandegan-1397-v{volume}',
                 f'ترغیب و ترهیب صحیح و ضعیف — موسی بازماندگان، جلد {volume}', 'records.jsonl', 'source.docx',
                 source_url='https://www.qalamlib.com/', source_id=slug, replace=(folder / 'manifest.json').exists())
        manifest = read_data(folder / 'manifest.json')
        manifest['publication'] = {'authorized': True, 'decision': SOURCE_IMPORT_DECISION, 'decision_date_japan': '2026-11-11',
                                   'owner_instruction': 'Add these three uploaded Persian volumes; hadiths only, exclude comments, flag ideological insertions.'}
        manifest['display_policy'] = {'qc_tags': False, 'decision': 'owner_requested_no_qc_tags_for_non_ocr',
                                     'basis': 'Current owner OCR-only display policy; these are verified native OOXML extractions with no OCR.'}
        manifest['extraction_scope'] = {'source_file_count': 1, 'side_commentary_included': False,
                                        'audit_root': IMPORT + '/audit', 'no_batch_limit': True}
        write_json(folder / 'manifest.json', manifest)
        summary = {'volume': volume, 'source_id': slug, 'records': len(records), 'source_sha256': SOURCE_HASHES[volume],
                   'records_sha256': digest(record_file), 'by_record_type': dict(Counter(r['record_type'] for r in records)),
                   'missing_arabic': sum(r['text']['arabic'] is None for r in records),
                   'missing_translation': sum(r['text']['translation'] is None for r in records)}
        write_json(folder / 'integration-audit.json', summary)
        counts.append(summary)
        all_rows.extend(records)
    assert len({r['id'] for r in all_rows}) == len(all_rows), 'Duplicate occurrence ID'
    assert {row['scope_decision']['id'] for row in omitted} == set(exclusions), 'Scope exclusion no longer matches the frozen candidate IDs'
    expected_patches = {p['patch_id'] for values in patches.values() for p in values}
    absent_patches = sorted(expected_patches - set(all_applied))
    audit_path = root / IMPORT / 'audit/final-text-spans.jsonl.gz'
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_bytes(gzip.compress(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in all_audit).encode(), mtime=0))
    (audit_path.parent / 'omitted-non-hadith-source-units.jsonl.gz').write_bytes(gzip.compress(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in omitted).encode(), mtime=0))
    report = {'schema': 'hadith-bank-persian-targhib-integration-v1', 'source_documents': 3, 'records': len(all_rows),
              'source_occurrences_not_unique_hadiths': True, 'deduplicated': False, 'ocr_used': False,
              'commentary_in_payload': False, 'independent_certification_claimed': False,
              'inline_patches_applied': len(set(all_applied)), 'inline_patches_outside_imported_spans': absent_patches,
              'additional_quotation_selections': len(selections), 'already_included_physical_quotes': skipped_quotes,
              'omitted_non_hadith_or_uncertain_attribution_units': len(omitted),
              'records_with_unresolved_source_glyphs': sum(bool(r['extraction']['unresolved_source_glyphs']) for r in all_rows),
              'sources': counts}
    write_json(root / 'reports/persian-targhib-integration.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--input-root', type=Path)
    parser.add_argument('--source-root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    report = run(root, (args.input_root or root / IMPORT / 'extracted').resolve(), args.source_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
