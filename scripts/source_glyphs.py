"""Opt-in, source-bound PNG glyphs for exact verbatim quotation spans.

Canonical UTF-8 text is never replaced.  The only browser image payloads are
bounded data URIs created here from checked, local PNG bytes.  A proposed
accessible transcription is NOT a review or release determination.
"""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import zlib

_HASH = re.compile(r'[0-9a-f]{64}\Z')
_RAW = re.compile(r'U\+[0-9A-F]{4,6}\Z')
_ASSET = re.compile(r'assets/[A-Za-z0-9][A-Za-z0-9_.-]*\.png\Z')
_CLIP = re.compile(r'evidence/glyph-review/[A-Za-z0-9][A-Za-z0-9_.-]*\.png\Z')
_REVIEW = re.compile(r'evidence/literal-qc/[A-Za-z0-9][A-Za-z0-9_.-]*\.json\Z')
_PREVIOUS = re.compile(r'evidence/source-preservation/[A-Za-z0-9][A-Za-z0-9_.-]*\.json\Z')
_ACCESS_STATUS = ('proposed_pending_independent_qc', 'independent_literal_word_sequence_passed')
_ARABIC = re.compile(r'[\u0600-\u06ff \u200c\u200d]+\Z')
_MAX_GLYPHS = 8
_MAX_PNG_BYTES = 8192
_PNG_MAGIC = b'\x89PNG\r\n\x1a\n'

# Approved by the separate owner-supplied independent literal review. This immutable
# code-side anchor, NOT any candidate record or material manifest, is the authority
# for a narrowly scoped literal-word-order PASS. Updating candidate checksums can
# never grant that PASS to different review bytes. Future editions need separate
# deliberate approval; this is not a global review policy or release permission.
_FRENCH_H2_LITERAL_AUTHORITY = {
    'material_path': 'materials/fr-maach-nawawi-2021/records.json',
    'record_id': 'maach-2021-french-nawawi2:fr:p0007-0009:entry0002',
    'source_id': 'maach-2021-french-nawawi2',
    'pdf_sha256': '3d36eb9be1657c0d8fc683d34ddc73db450800ae91b9eefb2746d0ff12c0e90d',
    'fr_text_sha256': '295cc8a6f976a05309f428368da76730f0838910cee77ce8b9fc846a32b59386',
    'result_id': 'FR-MAACH-H2-ARABIC-A11Y-LITERALS-QC-001-RESULT-001',
    'result_file': 'evidence/literal-qc/QC-RESULT.json',
    'result_sha256': '115fe308cd48b0f7254311cb563087d2842a764bdf8b4059173949b0b1f4c607',
    'predecessor_file': 'evidence/source-preservation/records-before-literal-qc-promotion.json',
    'predecessor_sha256': 'eed4c58abf35b9f4ca88c2291a3d8b9f119b4ceaf14ce152246a7313975e5730',
    'glyphs': (
        ('text.translation', 7, 8, 'U+F074', 'assets/F074.png',
         'cfd1cf9621c0f14103115ae4494f2fb49fd4de525533ba5b98fe93a93f5ad230',
         'رضي الله عنه', 7, 'evidence/glyph-review/context-F074.png',
         'cb534b974f7fa5b118571b1ed7473eeb20b71aa0c0d67da475f8415c89f0bac2'),
        ('text.translation', 110, 111, 'U+F072', 'assets/F072.png',
         '87ef734b566b609ec0891f6a495d27c5a1bf78238f9e48c9481410993d0d5ae5',
         'صلى الله عليه وسلم', 7, 'evidence/glyph-review/context-F072.png',
         'b0f1cda0cc897bc531bf243b3b9e1a9682ed7e8176c35a315f6889a5eed3c15d'),
    ),
}


def _require(check, message):
    if not check:
        raise ValueError('Source glyph: ' + message)


def _relative_file(root, folder, relative, pattern):
    _require(isinstance(relative, str) and bool(pattern.fullmatch(relative)), 'unsafe asset/evidence path')
    base = PurePosixPath(folder)
    _require(len(base.parts) >= 2 and base.parts[0] == 'materials', 'not a material-owned directory')
    full = (base / relative).as_posix()
    target = Path(root).resolve()
    for part in PurePosixPath(full).parts:
        target /= part
        _require(not target.is_symlink(), 'symlinks are forbidden in source asset paths')
    _require(target.resolve().is_relative_to(Path(root).resolve()) and target.is_file(),
             'source asset must exist within its own material directory')
    return full, target


def _checked_png(data, max_bytes=_MAX_PNG_BYTES, max_dimension=64):
    _require(isinstance(data, bytes) and 60 <= len(data) <= max_bytes and
             data.startswith(_PNG_MAGIC), 'not a bounded PNG')
    offset = 8
    chunks = []
    image = bytearray()
    dimensions = None
    while offset < len(data):
        _require(offset + 12 <= len(data), 'truncated PNG chunk')
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset + 4:offset + 8]
        _require(length <= max_bytes and offset + length + 12 <= len(data), 'invalid PNG chunk length')
        payload = data[offset + 8:offset + 8 + length]
        actual_crc = struct.unpack_from('>I', data, offset + 8 + length)[0]
        _require(zlib.crc32(kind + payload) & 0xffffffff == actual_crc, 'invalid PNG chunk CRC')
        _require(kind in (b'IHDR', b'IDAT', b'IEND'), 'unsupported PNG content')
        chunks.append(kind)
        if kind == b'IHDR':
            _require(dimensions is None and len(payload) == 13, 'invalid PNG header')
            width, height, depth, color, compress, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            _require(1 <= width <= max_dimension and 1 <= height <= max_dimension and depth == 8 and color == 2 and
                     compress == filtering == interlace == 0, 'unsupported PNG dimensions/format')
            dimensions = (width, height)
        if kind == b'IDAT':
            image.extend(payload)
        if kind == b'IEND':
            _require(length == 0 and offset + 12 == len(data), 'invalid PNG final chunk')
        offset += length + 12
    _require(chunks[0] == b'IHDR' and chunks[-1] == b'IEND' and
             chunks.count(b'IHDR') == chunks.count(b'IEND') == 1 and b'IDAT' in chunks and
             chunks.index(b'IDAT') == 1 and
             not any(kind != b'IDAT' for kind in chunks[1:-1]), 'invalid PNG chunk sequence')
    _require(dimensions is not None, 'missing PNG dimensions')
    # Bound expansion as well as compressed bytes: no decompression bomb.
    expected = dimensions[1] * (1 + dimensions[0] * 3)
    stream = zlib.decompressobj()
    try:
        raw = stream.decompress(bytes(image), expected + 1)
        _require(len(raw) == expected and stream.eof and not stream.unused_data and
                 not stream.unconsumed_tail and not stream.flush(), 'PNG raster is not exact')
    except zlib.error as error:
        raise ValueError('Source glyph: invalid PNG image data') from error
    for row in range(dimensions[1]):
        _require(raw[row * (dimensions[0] * 3 + 1)] in (0, 1, 2, 3, 4), 'unsupported PNG row filter')
    return dimensions


def _declared_hash(material, path):
    supporting = material.get('supporting_files') or []
    expected = [entry.get('sha256') for entry in supporting
                if isinstance(entry, dict) and entry.get('path') == path]
    _require(len(expected) == 1 and isinstance(expected[0], str) and _HASH.fullmatch(expected[0]),
             'source glyph and evidence files must be explicitly declared in supporting_files')
    return expected[0]



def _has_trusted_literal_authority(row, material, folder, glyphs):
    """Require one *complete* source-scoped approval, outside mutable receipts.

    An absent/altered report, a rehashed candidate receipt, or one inconsistent
    record-level review value downgrades ALL the record's image labels to pending.
    Image/PUA safety checks still run separately in project_source_glyphs().
    """
    authority = _FRENCH_H2_LITERAL_AUTHORITY
    if (folder + '/records.json' != authority['material_path'] or
            row.get('id') != authority['record_id'] or row.get('language') != 'fr' or
            row.get('book_key') != 'nawawi' or row.get('edition') != 'maach-first-2021' or
            (row.get('source') or {}).get('id') != authority['source_id'] or
            material.get('dataset_id') != authority['source_id'] or
            (row.get('source') or {}).get('sha256') != authority['pdf_sha256'] or
            material.get('source_sha256') != authority['pdf_sha256'] or
            (row.get('text') or {}).get('arabic') is not None or
            hashlib.sha256((row.get('text') or {}).get('translation', '').encode('utf-8')).hexdigest()
            != authority['fr_text_sha256']):
        return False
    review = row.get('review') or {}
    if (not isinstance(review, dict) or
            review.get('glyph_accessibility_result_id') != authority['result_id'] or
            review.get('glyph_accessibility_result_sha256') != authority['result_sha256'] or
            review.get('glyph_accessibility_status') !=
            'independent_literal_words_and_letters_passed_unvowelled_only;_production_accessibility_pending' or
            review.get('release_eligible') is not False or
            review.get('certified_release_eligible') is not False or
            not isinstance(glyphs, list) or len(glyphs) != len(authority['glyphs'])):
        return False
    for entry, expected in zip(glyphs, authority['glyphs']):
        if not isinstance(entry, dict) or not isinstance(entry.get('accessibility'), dict):
            return False
        a = entry['accessibility']
        if (a.get('status') != 'independent_literal_word_sequence_passed' or
                a.get('source_pdf_sha256') != authority['pdf_sha256'] or
                (entry.get('field'), entry.get('start'), entry.get('end'),
                 entry.get('raw_codepoint'), entry.get('file'), entry.get('sha256'),
                 a.get('arabic_literal'), a.get('source_pdf_page'), a.get('source_clip'),
                 a.get('source_clip_sha256')) != expected):
            return False
        receipt = a.get('independent_review') or {}
        if (not isinstance(receipt, dict) or
                receipt.get('result_id') != authority['result_id'] or
                receipt.get('result_file') != authority['result_file'] or
                receipt.get('result_sha256') != authority['result_sha256'] or
                receipt.get('reviewed_candidate_file') != authority['predecessor_file'] or
                receipt.get('reviewed_candidate_sha256') != authority['predecessor_sha256']):
            return False
    # The manifest is not an approval authority: even its self-consistent
    # rehash must match these *code-side* source/QC digest pins.
    for relative, expected in (
        (authority['result_file'], authority['result_sha256']),
        (authority['predecessor_file'], authority['predecessor_sha256']),
        *((g[4], g[5]) for g in authority['glyphs']),
        *((g[8], g[9]) for g in authority['glyphs']),
    ):
        try:
            if _declared_hash(material, folder + '/' + relative) != expected:
                return False
        except (ValueError, KeyError, TypeError):
            return False
    return True


def _verified_literal_review(root, folder, material, row, entry, access):
    """Evidence-bound status; checks the exact independent review and reviewed predecessor.

    This proves only the letters and word order of the two imaged source glyphs.
    No browser contrast, pronunciation, release or entire-entry certification follows.
    """
    receipt = access.get('independent_review')
    _require(isinstance(receipt, dict) and set(receipt) == {
        'result_id', 'result_file', 'result_sha256',
        'reviewed_candidate_file', 'reviewed_candidate_sha256'},
        'independent literal PASS requires its exact review receipt and reviewed predecessor')
    for key in ('result_sha256', 'reviewed_candidate_sha256'):
        _require(isinstance(receipt[key], str) and _HASH.fullmatch(receipt[key]),
                 'invalid review digest')
    result_path, result_file = _relative_file(root, folder, receipt['result_file'], _REVIEW)
    reviewed_path, reviewed_file = _relative_file(root, folder, receipt['reviewed_candidate_file'], _PREVIOUS)
    for path, file, digest, maximum in (
        (result_path, result_file, receipt['result_sha256'], 32768),
        (reviewed_path, reviewed_file, receipt['reviewed_candidate_sha256'], 65536)):
        _require(_declared_hash(material, path) == digest and file.stat().st_size <= maximum and
                 hashlib.sha256(file.read_bytes()).hexdigest() == digest,
                 'independent review/predecessor not hash-bound to declared local evidence')
    try:
        report = json.loads(result_file.read_bytes())
        predecessor = json.loads(reviewed_file.read_bytes())
    except (ValueError, UnicodeError) as error:
        raise ValueError('Source glyph: malformed independent review evidence') from error
    _require(isinstance(predecessor, list) and len(predecessor) == 1 and
             isinstance(predecessor[0], dict) and predecessor[0].get('id') == row.get('id') and
             predecessor[0].get('text', {}).get('translation') == row['text']['translation'] and
             predecessor[0].get('source', {}).get('sha256') == material['source_sha256'],
             'reviewed predecessor must be the same source ID and exact raw matn')
    previous_glyphs = predecessor[0].get('source_glyphs') or []
    matches = [item for item in previous_glyphs if isinstance(item, dict) and
               item.get('start') == entry['start'] and item.get('end') == entry['end'] and
               item.get('raw_codepoint') == entry['raw_codepoint'] and
               item.get('sha256') == entry['sha256'] and
               item.get('accessibility', {}).get('arabic_literal') == access['arabic_literal'] and
               item.get('accessibility', {}).get('status') == 'proposed_pending_independent_qc']
    _require(len(matches) == 1, 'literal review not bound to exact preceding proposal')
    integrity = report.get('input_integrity') if isinstance(report, dict) else None
    _require(isinstance(integrity, dict) and report.get('result_id') == receipt['result_id'] and
             report.get('status') == 'SCOPED_TWO_LITERAL_IMAGE_QC_COMPLETE' and
             integrity.get('records_json_sha256') == receipt['reviewed_candidate_sha256'] and
             integrity.get('raw_fr_matn_utf8_sha256') ==
             hashlib.sha256(row['text']['translation'].encode('utf-8')).hexdigest() and
             integrity.get('source_pdf_sha256') == material['source_sha256'] and
             integrity.get('raw_pua_offsets_verified', {}).get(entry['raw_codepoint']) == entry['start'] and
             integrity.get('asset_png_sha256', {}).get(entry['raw_codepoint'][2:]) == entry['sha256'] and
             integrity.get('context_png_sha256', {}).get(entry['raw_codepoint'][2:]) ==
             access['source_clip_sha256'], 'independent review binds a different source, image, or raw offset')
    verdicts = [v for v in report.get('verdicts', []) if isinstance(v, dict) and
                v.get('glyph') == entry['raw_codepoint']]
    _require(len(verdicts) == 1, 'independent review glyph verdict is absent or duplicated')
    verdict = verdicts[0]
    locators = verdict.get('source_image_locators') or {}
    _require(verdict.get('verdict') == 'PASS' and
             verdict.get('raw_fr_field') == entry['field'] and
             verdict.get('raw_fr_codepoint_start') == entry['start'] and
             verdict.get('raw_fr_codepoint_end_exclusive') == entry['end'] and
             verdict.get('proposed_arabic_literal') == access['arabic_literal'] and
             verdict.get('diacritic_policy', '').startswith('An unvowelled') and
             verdict.get('input_asset_sha256') == entry['sha256'] and
             verdict.get('input_context_sha256') == access['source_clip_sha256'] and
             locators.get('physical_pdf_page') == access['source_pdf_page'],
             'scoped independent verdict does not PASS this exact literal/source glyph')
    return {'result_id': receipt['result_id'],
            'result_sha256': receipt['result_sha256'],
            'reviewed_candidate_sha256': receipt['reviewed_candidate_sha256'],
            'scope': 'source_image_unvowelled_words_and_letters_only'}

def project_source_glyphs(row, material, bank_root):
    """Produce a small safe view only for records explicitly containing source_glyphs.

    Each mapping fixes one character in text.translation by 0-based Unicode
    *codepoint* offsets.  The original canonical raw character remains intact.
    """
    glyphs = row.get('source_glyphs')
    if glyphs is None:
        return None
    _require(isinstance(glyphs, list) and 1 <= len(glyphs) <= _MAX_GLYPHS,
             'source_glyphs must contain 1-8 explicit entries')
    text = row.get('text', {}).get('translation')
    _require(isinstance(text, str), 'only a supplied text.translation may be mapped')
    folder = PurePosixPath(material['canonical_records_path']).parent.as_posix()
    _require(folder.startswith('materials/'), 'glyphs require a material-owned canonical record')
    source = row.get('source') or {}
    _require(source.get('sha256') == material['source_sha256'] and _HASH.fullmatch(source['sha256']),
             'glyph source must match the material original PDF hash')
    declared_pages = set((row.get('page') or {}).get('pdf') or [])
    trusted_approval = _has_trusted_literal_authority(row, material, folder, glyphs)
    viewed = []
    previous_end = -1
    for entry in glyphs:
        _require(isinstance(entry, dict) and set(entry) == {
            'field', 'start', 'end', 'raw_codepoint', 'file', 'sha256', 'accessibility'},
            'mapping fields must match the safe schema')
        start, end = entry['start'], entry['end']
        _require(entry['field'] == 'text.translation' and type(start) is int and type(end) is int and
                 0 <= start < end == start + 1 <= len(text) and start >= previous_end,
                 'expected one ordered source-local codepoint span')
        raw = entry['raw_codepoint']
        _require(isinstance(raw, str) and _RAW.fullmatch(raw) and
                 0xe000 <= int(raw[2:], 16) <= 0xf8ff and text[start:end] == chr(int(raw[2:], 16)),
                 'codepoint does not match canonical source text')
        expected = entry['sha256']
        _require(isinstance(expected, str) and _HASH.fullmatch(expected), 'invalid glyph hash')
        path, target = _relative_file(bank_root, folder, entry['file'], _ASSET)
        _require(_declared_hash(material, path) == expected, 'asset hash not declared exactly')
        raw_png = target.read_bytes()
        _require(hashlib.sha256(raw_png).hexdigest() == expected, 'PNG SHA256 mismatch')
        width, height = _checked_png(raw_png)
        access = entry['accessibility']
        _require(isinstance(access, dict) and set(access) == ({
            'status', 'arabic_literal', 'source_pdf_page', 'source_clip',
            'source_clip_sha256', 'source_pdf_sha256'} | (
            {'independent_review'} if access.get('status') == 'independent_literal_word_sequence_passed' else set())),
            'accessible text needs pinned image evidence and the exact review gate')
        _require(access['status'] in _ACCESS_STATUS,
                 'unsupported accessibility review status')
        literal = access['arabic_literal']
        _require(isinstance(literal, str) and 1 <= len(literal) <= 80 and
                 _ARABIC.fullmatch(literal) and literal.strip() == literal,
                 'accessible literal must be bounded Arabic script, never HTML')
        _require(type(access['source_pdf_page']) is int and access['source_pdf_page'] in declared_pages and
                 access['source_pdf_sha256'] == material['source_sha256'],
                 'source page/PDF hash are not bound to this record')
        clip_path, clip = _relative_file(bank_root, folder, access['source_clip'], _CLIP)
        clip_hash = access['source_clip_sha256']
        _require(isinstance(clip_hash, str) and _HASH.fullmatch(clip_hash) and
                 _declared_hash(material, clip_path) == clip_hash and
                 hashlib.sha256(clip.read_bytes()).hexdigest() == clip_hash,
                 'source image evidence checksum mismatch')
        _require(clip.stat().st_size <= 65536 and clip.read_bytes().startswith(_PNG_MAGIC),
                 'source crop must be a bounded PNG')
        checked_review = None
        if trusted_approval:
            try:
                checked_review = _verified_literal_review(bank_root, folder, material, row, entry, access)
            except (ValueError, KeyError, TypeError):
                # A missing/modified supporting QC file cannot promote a status.
                # Preserve original PNG+raw text and present the label as pending.
                trusted_approval = False
        projection = {'field': 'text_translation', 'start': start, 'end': end,
                      'raw_codepoint': raw, 'source_path': path, 'sha256': expected,
                      'width': width, 'height': height,
                      'data_uri': 'data:image/png;base64,' + base64.b64encode(raw_png).decode('ascii'),
                      'alt_ar': literal, 'accessibility_status': 'proposed_pending_independent_qc',
                      'evidence': {'source_pdf_page': access['source_pdf_page'],
                                   'source_pdf_sha256': access['source_pdf_sha256'],
                                   'source_clip': clip_path, 'source_clip_sha256': clip_hash}}
        if checked_review is not None:
            projection['independent_literal_review'] = checked_review
        viewed.append(projection)
        previous_end = end
    if trusted_approval and all('independent_literal_review' in item for item in viewed):
        for item in viewed:
            item['accessibility_status'] = 'independent_literal_word_sequence_passed'
    else:
        # Atomic fail-closed gate: never leave the first glyph "approved" when
        # the second glyph or evidence failed. Historic raw metadata is untouched.
        for item in viewed:
            item.pop('independent_literal_review', None)
    return viewed


def escaped_source_glyph_prose(value, mappings, offset=0, direction='auto', wrap=True):
    """Literal static/Markdown HTML reading with data-embedded verified PNGs.

    Mappings must come from project_source_glyphs(), not a raw user record.
    """
    import html
    _require(direction in ('auto', 'ltr', 'rtl'), 'invalid static text direction')
    chars = list(value)
    if not mappings:
        content = html.escape(value, quote=True).replace('\n', '<br>\n')
        return '<p dir="' + direction + '">' + content + '</p>' if wrap else content
    chosen = [g for g in mappings if offset <= g['start'] < offset + len(chars)]
    if any(g['end'] > offset + len(chars) or chars[g['start'] - offset] != chr(int(g['raw_codepoint'][2:], 16))
           for g in chosen):
        raise ValueError('Source glyph: static passage span does not match checked text')
    chunks = ['<p dir="' + direction + '">'] if wrap else []
    cursor = 0
    for g in chosen:
        pos = g['start'] - offset
        chunks.append(html.escape(''.join(chars[cursor:pos]), quote=True).replace('\n', '<br>\n'))
        # Not HTML from the record: all fields were validated and constructed by the compiler.
        chunks.append('<img class="source-glyph" lang="ar" alt="' + html.escape(g['alt_ar'], quote=True) +
                      '" style="height:1.5em;max-height:31px;width:auto;vertical-align:-.42em" data-accessibility-status="' +
                      g['accessibility_status'] + '" data-source-codepoint="' +
                      g['raw_codepoint'] + '" width="' + str(g['width']) + '" height="' + str(g['height']) +
                      '" src="' + g['data_uri'] + '">')
        cursor = pos + 1
    chunks.append(html.escape(''.join(chars[cursor:]), quote=True).replace('\n', '<br>\n'))
    if wrap:
        chunks.append('</p>')
    return ''.join(chunks)
