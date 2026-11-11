#!/usr/bin/env python3
"""Import the owner-supplied Chinese Sunan Abi Dawud legacy Word edition.

The binary source, native text, every retained source span, and every excluded
comment span are retained. The source-specific parse plan is versioned next to
the material. No OCR, translations, canonical-number matching, or authenticity
certification is performed. This command does not rebuild the global website.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct

from register_material import register
from material_registry import SOURCE_IMPORT_DECISION


SLUG = 'zh-abu-dawud-yu-2002-doc'
EDITION = 'doc-cbff2d2c521e553c'
SOURCE_SHA256 = 'cbff2d2c521e553c6eb11a75d6079fe526930295b7a3fc4726cc8e7a4e0a42c8'
SOURCE_FILENAME = '艾布达吾德圣训_Sunan_Abi_Dawud.doc'
ORIGINAL_FILENAME = '1039713868-艾布达吾德圣训.doc'
SOURCE_TITLE = '艾布·达吾德圣训集（部分译本） — Sunan Abī Dāwūd (partial Chinese edition)'
SOURCE_URL = 'https://www.scribd.com/document/1039713868/艾布达吾德圣训'
PREFIX = 'materials/' + SLUG + '/'
NUMBERING_SYSTEM = 'Source-local printed Chinese edition sequence; not independently matched to canonical Sunan Abi Dawud numbering'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_gzip_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    path.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))


def extract_native_doc(data):
    """Read CFB streams and the Word CLX piece table without executing Word."""
    if sha256(data) != SOURCE_SHA256:
        raise ValueError('This source-specific importer requires the registered original DOC checksum')
    if data[:8] != bytes.fromhex('d0cf11e0a1b11ae1'):
        raise ValueError('Not a Compound File Binary document')
    u16 = lambda b, p: struct.unpack_from('<H', b, p)[0]
    u32 = lambda b, p: struct.unpack_from('<I', b, p)[0]
    sector_size = 1 << u16(data, 30)
    mini_sector_size = 1 << u16(data, 32)
    end = 0xfffffff0

    def sector(sid):
        result = data[(sid + 1) * sector_size:(sid + 2) * sector_size]
        if len(result) != sector_size:
            raise ValueError('CFB sector out of bounds')
        return result

    fat_ids = [v for v in struct.unpack_from('<109I', data, 76) if v < end]
    difat = u32(data, 68)
    for _ in range(u32(data, 72)):
        words = struct.unpack('<%dI' % (sector_size // 4), sector(difat))
        fat_ids.extend(v for v in words[:-1] if v < end)
        difat = words[-1]
    fat = []
    for sid in fat_ids:
        fat.extend(struct.unpack('<%dI' % (sector_size // 4), sector(sid)))

    def chain(sid, allocation=fat, read_sector=sector):
        chunks, seen = [], set()
        while sid < end:
            if sid in seen or sid >= len(allocation):
                raise ValueError('CFB chain cycle or invalid sector')
            seen.add(sid)
            chunks.append(read_sector(sid))
            sid = allocation[sid]
        return b''.join(chunks)

    directory = chain(u32(data, 48))
    entries = {}
    for offset in range(0, len(directory), 128):
        row = directory[offset:offset + 128]
        size = u16(row, 64)
        if size and row[66]:
            entries[row[:size - 2].decode('utf-16le')] = {
                'type': row[66], 'sector': u32(row, 116),
                'size': struct.unpack_from('<Q', row, 120)[0]}
    mini_fat_bytes = chain(u32(data, 60))
    mini_fat = list(struct.unpack('<%dI' % (len(mini_fat_bytes) // 4), mini_fat_bytes))
    root = entries['Root Entry']
    mini_stream = chain(root['sector'])[:root['size']]

    def stream(name):
        row = entries[name]
        if row['size'] < u32(data, 56):
            result = chain(row['sector'], mini_fat,
                           lambda sid: mini_stream[sid * mini_sector_size:(sid + 1) * mini_sector_size])
        else:
            result = chain(row['sector'])
        if len(result) < row['size']:
            raise ValueError('Truncated CFB stream: ' + name)
        return result[:row['size']]

    word = stream('WordDocument')
    table_name = '1Table' if u16(word, 10) & 0x200 else '0Table'
    table = stream(table_name)
    ccp_text = u32(word, 76)
    clx = table[u32(word, 418):u32(word, 418) + u32(word, 422)]
    cursor = 0
    while clx[cursor] == 1:
        cursor += 3 + u16(clx, cursor + 1)
    if clx[cursor] != 2:
        raise ValueError('Missing Word Pcdt structure')
    plc_size = u32(clx, cursor + 1)
    plc = clx[cursor + 5:cursor + 5 + plc_size]
    if (plc_size - 4) % 12:
        raise ValueError('Invalid piece table size')
    piece_count = (plc_size - 4) // 12
    cps = struct.unpack_from('<%dI' % (piece_count + 1), plc)
    pieces, chunks = [], []
    for i in range(piece_count):
        encoded_fc = u32(plc, 4 * (piece_count + 1) + 8 * i + 2)
        compressed = bool(encoded_fc & 0x40000000)
        byte_offset = encoded_fc & 0x3fffffff
        count = cps[i + 1] - cps[i]
        if compressed:
            byte_offset //= 2
            text = word[byte_offset:byte_offset + count].decode('cp1252')
        else:
            text = word[byte_offset:byte_offset + 2 * count].decode('utf-16le')
        chunks.append(text)
        pieces.append({'cp_start': cps[i], 'cp_end': cps[i + 1],
                       'byte_offset': byte_offset, 'compressed': compressed})
    text = ''.join(chunks)[:ccp_text]
    if len(text) != ccp_text or '\ufffd' in text:
        raise ValueError('Unexpected native text length or decoding replacement')
    # This source has BMP characters only. CR -> LF is one character to one
    # character, so native Word CP positions remain valid in native-text.txt.
    if len(text.encode('utf-16le')) != 2 * len(text):
        raise ValueError('This source locator scheme requires BMP-only text')
    text = text.replace('\r', '\n')
    return text, {'method': 'direct_binary_doc', 'ocr_used': False,
                  'streams': ['WordDocument', table_name], 'pieces': pieces,
                  'ccp_text': ccp_text, 'native_text_sha256': sha256(text.encode()),
                  'native_text_characters': len(text),
                  'normalization': 'Paragraph CR replaced one-to-one by LF only; no wording normalization.'}


def subtract_spans(start, end, removals):
    cursor, result = start, []
    for left, right in sorted(removals):
        left, right = max(start, left), min(end, right)
        if right <= cursor or left >= end:
            continue
        if left > cursor:
            result.append([cursor, left])
        cursor = max(cursor, right)
    if cursor < end:
        result.append([cursor, end])
    return result


def trim_spans(text, spans):
    spans = [list(s) for s in spans if s[0] < s[1]]
    while spans:
        a, b = spans[0]
        while a < b and text[a].isspace():
            a += 1
        if a < b:
            spans[0][0] = a
            break
        spans.pop(0)
    while spans:
        a, b = spans[-1]
        while b > a and text[b - 1].isspace():
            b -= 1
        if a < b:
            spans[-1][1] = b
            break
        spans.pop()
    return spans


def read_plan(path, text):
    reviewed = json.loads(path.read_text(encoding='utf-8'))
    if reviewed['source_sha256'] != SOURCE_SHA256 or reviewed['source_text_sha256'] != sha256(text.encode()):
        raise ValueError('Extraction plan does not match the native source')
    paragraphs = text.split('\n')
    offsets, position = [], 0
    for paragraph in paragraphs:
        offsets.append(position)
        position += len(paragraph) + 1
    for row in reviewed['paragraph_role_overrides'] + reviewed['unnumbered_narration_continuations']:
        if sha256(paragraphs[row['paragraph_index']].encode()) != row['text_sha256']:
            raise ValueError('Reviewed paragraph hash mismatch')
    events = []
    for kind, rows in (('entry', reviewed['entry_starts']),
                       ('book', reviewed['book_headings']),
                       ('chapter', reviewed['chapter_headings'])):
        for row in rows:
            events.append((offsets[row['paragraph_index']] + row.get('char_offset', 0), kind, row))
    events.sort(key=lambda event: event[0])
    if len({event[0] for event in events}) != len(events):
        raise ValueError('Overlapping source entry or heading boundaries')
    entries, exclusions = [], []
    book, chapter = None, None
    for index, (start, kind, row) in enumerate(events):
        if kind == 'book':
            book, chapter = row, None
            continue
        if kind == 'chapter':
            chapter = row
            continue
        end = events[index + 1][0] if index + 1 < len(events) else len(text)
        p = row['paragraph_index']
        include = row['printed_number'] not in reviewed.get('exclude_numbered_commentary_ids', reviewed['numbered_commentary_ids'])
        entry = {'source_span': [start, end],
                 'body_start': offsets[p] + row['marker_end'],
                 'number': row['printed_number'],
                 'number_as_printed': paragraphs[p][row['char_offset']:row['marker_end']],
                 'paragraph_index_zero_based': p,
                 'source_headings': [heading['title'] for heading in (book, chapter) if heading],
                 'heading_paragraphs': [heading['paragraph_index'] for heading in (book, chapter) if heading],
                 'embedded_start': row['char_offset'] > 0,
                 'include': include}
        if row['printed_number'] in reviewed['numbered_commentary_ids']:
            entry['content_kind'] = 'attributed_explanatory_report'
            entry['reason'] = 'Separately numbered lexical or explanatory source statement; not direct Prophetic speech.'
        for override in reviewed.get('entry_overrides', []):
            if (override['paragraph_index'], override.get('char_offset', 0)) == (p, row['char_offset']):
                if override.get('source_span_sha256') != sha256(text[start:end].encode()):
                    raise ValueError('Source entry override does not match exact source span')
                for key in ('source_defects', 'is_excerpt', 'content_kind'):
                    if key in override:
                        entry[key] = override[key]
        entries.append(entry)
        if not include:
            exclusions.append({'span': [start, end], 'text': text[start:end],
                               'paragraph_index_zero_based': p, 'source_entry_id': row['printed_number'],
                               'reason': 'numbered_lexical_or_explanatory_comment'})
    non_narration_roles = {'front_matter', 'section_invocation', 'explicit_editorial_note',
                           'editorial_note_continuation', 'ancillary_explanation_or_compiler_comment'}
    for row in reviewed['paragraph_role_overrides']:
        if row['role'] in non_narration_roles:
            p = row['paragraph_index']
            a, b = offsets[p], min(len(text), offsets[p] + len(paragraphs[p]) + 1)
            exclusions.append({'span': [a, b], 'text': text[a:b],
                               'paragraph_index_zero_based': p, 'reason': row['role']})
    for row in reviewed['inline_editorial_removals']:
        p = row['paragraph_index']
        a, b = offsets[p] + row['char_start'], offsets[p] + row['char_end']
        if text[a:b] != row['text']:
            raise ValueError('Reviewed inline text mismatch')
        exclusions.append({'span': [a, b], 'text': text[a:b],
                           'paragraph_index_zero_based': p, 'reason': row['reason']})
    return {'entries': entries, 'exclusions': sorted(exclusions, key=lambda row: row['span']),
            'missing_numbers': reviewed['numbering']['absent_printed_numbers']}


def run(root, source=None):
    root = Path(root).resolve()
    folder = root / PREFIX
    folder.mkdir(parents=True, exist_ok=True)
    original = Path(source).resolve() if source else folder / SOURCE_FILENAME
    data = original.read_bytes()
    native, extraction = extract_native_doc(data)
    if original != (folder / SOURCE_FILENAME).resolve():
        shutil.copyfile(original, folder / SOURCE_FILENAME)
    (folder / 'native-text.txt').write_bytes(native.encode('utf-8'))
    plan = read_plan(folder / 'extraction-plan.json', native)
    # The plan fixes all boundary decisions to exact checksummed source spans.
    exclusions = plan['exclusions']
    for item in exclusions:
        a, b = item['span']
        if native[a:b] != item['text']:
            raise ValueError('Excluded span does not equal original text')
    removed_intervals = [item['span'] for item in exclusions]
    duplicate_numbers = Counter(str(item['number']) for item in plan['entries'])
    records, ledger, parentheticals = [], [], []
    for sequence, entry in enumerate(plan['entries'], 1):
        start, end = entry['source_span']
        body_start = entry['body_start']
        number = str(entry['number'])
        occurrence_id = 'zh-abu-dawud:' + EDITION + ':cp' + str(start).zfill(6)
        removed = [item for item in exclusions if item['span'][0] < end and item['span'][1] > body_start]
        included = trim_spans(native, subtract_spans(body_start, end, removed_intervals))
        translation = ''.join(native[a:b] for a, b in included)
        ledger_item = {'id': occurrence_id, 'source_entry_id': number,
                       'sequence_position': sequence, 'source_span': [start, end],
                       'paragraph_index_zero_based': entry['paragraph_index_zero_based'],
                       'included_source_spans': included,
                       'imported': entry.get('include', True),
                       'reason': entry.get('reason')}
        ledger.append(ledger_item)
        if not entry.get('include', True):
            continue
        if not translation:
            raise ValueError('Empty narration after comment separation: ' + occurrence_id)
        # Exact retained intervals are the sole source of the translated field.
        assert translation == ''.join(native[a:b] for a, b in included)
        issues = list(entry.get('source_defects', []))
        if duplicate_numbers[number] > 1:
            issues.append('Printed local number occurs more than once; each source occurrence retains its own stable ID.')
        if entry.get('embedded_start'):
            issues.append('Source printed this entry inside the preceding paragraph; split at its explicit numbered attribution.')
        narrator_match = re.match(r'^(.{1,55}?)(?:传述|传叙|述)[：:]', translation)
        narrator = narrator_match.group(1) if narrator_match else None
        headings = entry.get('source_headings', [])
        metadata_path = PREFIX + 'source-metadata.json'
        locator = {'path': PREFIX + 'native-text.txt',
                   'source_doc_path': PREFIX + SOURCE_FILENAME,
                   'stream': 'WordDocument', 'index_base': 0,
                   'offset_unit': 'Unicode code point; also native Word CP for this BMP source',
                   'source_span': [start, end],
                   'paragraph_index_zero_based': entry['paragraph_index_zero_based'],
                   'included_source_spans': included,
                   'excluded_commentary_audit': PREFIX + 'excluded-commentary.json.gz'}
        record = {
            'id': occurrence_id, 'language': 'zh-CN', 'book_key': 'abu-dawud', 'edition': EDITION,
            'title': '来源编号 ' + number, 'text': {'arabic': None, 'translation': translation},
            'record_type': 'source_narration_occurrence',
            'content_kind': entry.get('content_kind', 'numbered_source_report'),
            'source': {'title': SOURCE_TITLE, 'url': SOURCE_URL,
                       'original_filename': ORIGINAL_FILENAME,
                       'metadata_path': metadata_path,
                       'work_scope': 'Supplied partial Chinese DOC through local number 2868 and the fourteenth source book; no full-collection claim.'},
            'number': {'source_entry_id': number, 'in_book': number, 'canonical': None,
                       'scope': 'source_local', 'numbering_system': NUMBERING_SYSTEM,
                       'source_sequence_position': sequence, 'as_printed': entry['number_as_printed']},
            'narrator': {'name': narrator, 'basis': 'Source opening attribution only; no full isnad reconstruction.'},
            'isnad': None,
            'translator': {'name': '穆萨·余崇仁', 'name_latin': 'Musa Yu Chongren',
                           'evidence': metadata_path, 'role': 'named translator in source preface'},
            'translation_provenance': {'origin': 'human_translator_credited', 'label': 'Human',
                                      'basis': 'The supplied source has a translator preface signed 穆萨·余崇仁书 and dated 2002年8月于银川新城.',
                                      'human_involvement': 'named_human_translator', 'ai_translation': False,
                                      'evidence_ids': [metadata_path],
                                      'scope_note': 'Existing Chinese translation; no new translation generated.'},
            'ai_translation': False, 'topic_tags': [], 'source_headings': headings,
            'source_structure_tags': [{'origin': 'source_book_structure', 'source_id': SLUG,
                                       'hierarchy': i + 1, 'value_verbatim': heading,
                                       'source_locator': {'path': PREFIX + 'native-text.txt',
                                                          'paragraph_index_zero_based': entry['heading_paragraphs'][i]}}
                                      for i, heading in enumerate(headings)],
            'editorial_tags': {'origin': 'import_pipeline_not_publisher', 'values': [
                'source:' + SLUG, 'language:zh-CN', 'book:abu-dawud', 'edition:' + EDITION,
                'method:direct_binary_doc', 'format:doc', 'ai_translation:false',
                'canonical_mapping:unverified', 'arabic:not_supplied']},
            'commentary': {'arabic': None, 'translation': None}, 'footnotes': [],
            'references': {'items': [], 'canonical_mapping_status': 'unverified',
                           'number_scope': 'Source-local printed entry number only.'},
            'grading': {'grade': None, 'grader': None,
                        'basis': 'No authenticity grade inferred from collection membership.'},
            'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None,
                     'doc_paragraphs': [entry['paragraph_index_zero_based']], 'index_base': 0,
                     'basis': 'Native Word paragraph and character positions; printed pagination unavailable.'},
            'source_locator': locator, 'source_defects': issues, 'related_versions': [],
            'review': {'status': 'native_source_import', 'issues': issues,
                       'independent_pro_qc': 'not_performed', 'release_status': 'source_import',
                       'release_eligible': False, 'certified_release_eligible': False},
            'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                       'source_notice_preserved_in': PREFIX + SOURCE_FILENAME},
            'extraction': {'method': 'direct_binary_doc', 'ocr_used': False,
                           'is_excerpt': entry.get('is_excerpt', False), 'side_commentary_included': False,
                           'included_text_is_exact_source_spans': True,
                           'source_extraction': PREFIX + 'native-text.txt',
                           'commentary_audit': PREFIX + 'excluded-commentary.json.gz',
                           'parenthetical_policy': 'Retain source translation connectives, action details and citation locators; inventory separately; exclude only explicitly reviewed commentary spans.'}}
        records.append(record)
        for a, b in included:
            for match in re.finditer(r'[（(][^（）()]*[）)]', native[a:b]):
                parentheticals.append({'record_id': occurrence_id,
                                       'span': [a + match.start(), a + match.end()],
                                       'text': match.group(), 'disposition': 'retained_source_translation',
                                       'attribution': 'Source parenthesis; semantic origin not independently certified.'})
    record_path = folder / 'records.jsonl'
    record_path.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                                   for row in records), encoding='utf-8')
    if len({row['id'] for row in records}) != len(records):
        raise ValueError('Duplicate stable occurrence IDs')
    write_gzip_json(folder / 'excluded-commentary.json.gz', {
        'schema': 'hadith-bank-excluded-source-spans-v1', 'source_sha256': SOURCE_SHA256,
        'native_text_sha256': extraction['native_text_sha256'],
        'offset_unit': 'zero-based Unicode code points into native-text.txt; half-open spans',
        'items': exclusions,
        'note': 'Excluded from hadith/search payload, retained verbatim here and in original source. No sectarian classification is inferred.'})
    write_gzip_json(folder / 'parenthetical-inventory.json.gz', {'items': parentheticals})
    write_json(folder / 'source-number-ledger.json', {'entries': ledger})
    metadata = {'schema': 'hadith-bank-source-metadata-v1',
                'source_title_as_printed': '艾布·达吾德圣训集', 'display_title': SOURCE_TITLE,
                'original_filename': ORIGINAL_FILENAME, 'stored_filename': SOURCE_FILENAME,
                'source_sha256': SOURCE_SHA256, 'source_bytes': len(data), 'source_url': SOURCE_URL,
                'translator_as_printed': '穆萨·余崇仁书', 'translator_name': '穆萨·余崇仁',
                'translator_evidence': {'section': '译者序', 'paragraph_index_zero_based': 17,
                                        'date_as_printed': '2002年8月于银川新城',
                                        'native_text_path': PREFIX + 'native-text.txt'},
                'completeness': {'status': 'partial_source', 'full_collection': False,
                                 'first_printed_number': '1', 'last_printed_number': '2868',
                                 'final_book_as_printed': '十四、田赋、特许战利品及为官之道部',
                                 'source_number_gaps': plan.get('missing_numbers', []),
                                 'numbering_defects_preserved': True},
                'extraction': extraction, 'record_count': len(records),
                'numbered_source_entry_count': len(ledger),
                'excluded_numbered_comments': [x['source_entry_id'] for x in ledger if not x['imported']],
                'records_sha256': sha256(record_path.read_bytes()),
                'commentary_policy': 'Separate explicit notes and reviewed source commentary; preserve all removed spans verbatim with offsets.',
                'review': {'independent_pro_qc': 'not_performed', 'certified_release_eligible': False},
                'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None}}
    write_json(folder / 'source-metadata.json', metadata)
    register(root, PREFIX.rstrip('/'), 'zh-CN', 'abu-dawud', EDITION, SOURCE_TITLE,
             'records.jsonl', SOURCE_FILENAME, source_url=SOURCE_URL, source_id=SLUG,
             replace=(folder / 'manifest.json').exists())
    manifest_path = folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['publication'] = {'authorized': True, 'decision': SOURCE_IMPORT_DECISION,
                               'decision_date_japan': '2026-11-11',
                               'basis': 'Owner requested adding this Chinese Sunan Abi Dawud file and its hadiths to the bank and repository on 11 November 2026.'}
    manifest['extraction_scope'] = {'source_file_count': 1, 'no_batch_limit': True,
                                    'side_commentary_included': False, 'source_is_partial': True,
                                    'audit_root': PREFIX.rstrip('/')}
    write_json(manifest_path, manifest)
    result = {'material': SLUG, 'records': len(records), 'numbered_source_entries': len(ledger),
              'excluded_numbered_comments': metadata['excluded_numbered_comments'],
              'source_sha256': SOURCE_SHA256, 'records_sha256': metadata['records_sha256'],
              'native_text_sha256': extraction['native_text_sha256'],
              'all_translations_reconstruct_from_source_spans': True,
              'independent_pro_qc_performed': False}
    write_json(folder / 'integration-audit.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path, help='Optional original upload path; omitted for reproducible re-import from the repository source.')
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.source), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
