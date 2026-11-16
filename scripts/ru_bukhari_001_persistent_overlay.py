"""Private, frozen Russian Bukhari 1 language-version overlay.

Called by the *actual* Bank views builder after source projections and
counterpart resolution and before search/reader streams are generated.  Does
not create a material, source occurrence, book, numbering link or translation.

Trust boundary: the source directory, ledger, candidate and TRUSTED-PINS.json
are data, not an authority.  The reviewed TRUSTED-PINS bytes and final candidate
are anchored by SHA-256 constants in this separate code.  Changing those
constants is a separate code review, NEVER an automatic pin refresh.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from build_reader import parse_json, validate_record
from language_versions import validate_language_versions

TARGET = 'fawaz:df57907be352:bukhari:1'
RU_ID = TARGET + ':rus'
SOURCE_DIR = 'imports/ru-bukhari-001'
TRUSTED_PINS_SHA256 = 'cb6c7196135b34ed6af06db9daad090249862c85dca3bf72b3df5f95f1b3386a'
CANDIDATE_SHA256 = '63afa399de6cb77e4b9b8c3b10b78c06d61c3e0f8d9dc4e4f3aa85dda6b37f92'
ACTIONS = (
    'copy', 'literal_escape_to_real_line_break', 'copy',
    'exclude_source_verified_commentary_marker', 'copy',
    'exclude_source_verified_commentary_marker', 'copy',
    'exclude_source_verified_commentary_marker', 'copy',
)
ORIGINAL_LANGUAGES = ('ar', 'en', 'ur', 'bn')


def reject(message: str):
    raise ValueError('RU-BUKHARI-001-PERSISTENT-OVERLAY HOLD: ' + message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_file(root: Path, relative: str) -> Path:
    # No traversal, absolute references, symlink path components or dynamic
    # URLs. Captured HTML is read as inert bytes, never parsed as trusted page.
    if not isinstance(relative, str) or not relative or '\\' in relative or any(ord(c) < 32 for c in relative):
        reject('invalid archived evidence path')
    parts = PurePosixPath(relative)
    if (parts.is_absolute() or parts.as_posix() != relative or
            '..' in parts.parts or '.' in parts.parts or
            any(':' in s or not s for s in parts.parts)):
        reject('unsafe archived evidence path: ' + relative)
    path = root
    for segment in parts.parts:
        path = path / segment
        if path.is_symlink():
            reject('symlink in evidence path: ' + relative)
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        reject('missing or escaped evidence file: ' + relative)
    return path


def _checked(root: Path, relative: str, rule: dict) -> bytes:
    if not isinstance(rule, dict) or set(rule) != {'path','bytes','sha256'} or SOURCE_DIR + '/' + rule['path'] != relative:
        reject('source evidence descriptor unexpected: ' + relative)
    data = _safe_file(root, relative).read_bytes()
    if len(data) != rule['bytes'] or digest(data) != rule['sha256']:
        reject('external source pin mismatch: ' + relative)
    return data


def _verify_map(raw: bytes, html: bytes, ledger: dict, pins: dict) -> str:
    source = raw.decode('utf-8', errors='strict')
    if (ledger.get('stable_target_record_id') != TARGET or
            ledger.get('changed_segment_numbers') != [2, 4, 6, 8] or
            not isinstance(ledger.get('segments'), list) or len(ledger['segments']) != 9 or
            ledger.get('raw_field_sha256') != pins['raw_russian']['sha256'] or
            ledger.get('display_text_sha256') != pins['display']['sha256'] or
            ledger.get('html_source_sha256') != pins['captured_html']['sha256']):
        reject('source/display ledger metadata not bound to frozen pins')
    source_chars = output_chars = source_bytes = output_bytes = 0
    before_parts, after_parts = [], []
    for i, segment in enumerate(ledger['segments']):
        if not isinstance(segment, dict):
            reject('non-object span segment')
        before, after = segment.get('before'), segment.get('after')
        if not isinstance(before, str) or not isinstance(after, str):
            reject('non-text span segment')
        be, ae = before.encode('utf-8'), after.encode('utf-8')
        positions = (
            ('source_codepoints', source_chars, len(before)),
            ('source_utf8_bytes', source_bytes, len(be)),
            ('display_codepoints', output_chars, len(after)),
            ('display_utf8_bytes', output_bytes, len(ae)),
        )
        for name, start, size in positions:
            if segment.get(name) != {'start': start, 'end_exclusive': start + size}:
                reject('span offset mismatch: ' + name + ' / ' + str(i + 1))
        action = ACTIONS[i]
        if (segment.get('sequence') != i + 1 or segment.get('action') != action or
                segment.get('before_utf8_sha256') != digest(be) or
                segment.get('after_utf8_sha256') != digest(ae)):
            reject('unapproved span action/hash: ' + str(i + 1))
        if action == 'copy' and before != after:
            reject('narration copy changed: ' + str(i + 1))
        if action == 'literal_escape_to_real_line_break' and (before != r'\n' or after != '\n'):
            reject('unexpected newline transformation')
        if action == 'exclude_source_verified_commentary_marker' and (before != '[' + str((i - 3) // 2 + 1) + ']' or after):
            reject('unexpected commentary-marker boundary')
        before_parts.append(before)
        after_parts.append(after)
        source_chars += len(before)
        source_bytes += len(be)
        output_chars += len(after)
        output_bytes += len(ae)
    text = ''.join(after_parts)
    if (''.join(before_parts) != source or source_chars != len(source) or
            source_bytes != len(raw) or len(text) != pins['display']['codepoints'] or
            output_bytes != pins['display']['utf8_bytes'] or
            digest(text.encode('utf-8')) != pins['display']['sha256'] or
            source.count(r'\n') != 1 or text.count('\n') != 1):
        reject('original narrative cannot reconstruct pinned Russian display')
    anchors = ledger.get('archival_commentary_anchors')
    if not isinstance(anchors, list) or [x.get('id') for x in anchors] != ['1', '2', '3']:
        reject('three comment boundaries not independently present')
    for anchor in anchors:
        span = anchor['html_text_span_utf8']
        start, end = span['byte_start'], span['byte_end_exclusive']
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(html) or
                digest(html[start:end]) != span['utf8_sha256'] or
                not html[start:end].decode('utf-8').startswith('[' + anchor['id'] + ']')):
            reject('missing original Isnad commentary note ' + anchor['id'])
    return text


def _verify_archive(path: Path):
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                reject('archived evidence ZIP has bad CRC: ' + path.name)
    except (OSError, zipfile.BadZipFile) as exc:
        reject('unreadable frozen source archive ' + path.name + ': ' + str(exc))


def load_frozen_candidate(bank_root: Path):
    """Verify original source, span ledger, candidate and parent BEFORE streams.

    No network, no recapture, no dynamic trust-pin regeneration.  Returns a
    fully verified but still private *one-version* parent projection.
    """
    root = Path(bank_root).resolve()
    evidence_root = root / SOURCE_DIR
    pins_bytes = _safe_file(root, SOURCE_DIR + '/TRUSTED-PINS.json').read_bytes()
    if digest(pins_bytes) != TRUSTED_PINS_SHA256:
        reject('TRUSTED-PINS.json changed; separate hardcoded code authority unchanged')
    pins = parse_json(pins_bytes.decode('utf-8'))
    identity = pins['identity']
    if (identity.get('existing_record_id') != TARGET or identity.get('ru_version_id') != RU_ID or
            identity.get('existing_languages') != list(ORIGINAL_LANGUAGES) or
            identity.get('provider_entry_id') != 1 or
            identity.get('scope') != 'same_fawaz_provider_entry_only'):
        reject('frozen identity rules changed')
    source = {}
    for name in (
            'parent_record', 'raw_russian', 'span_map', 'captured_html',
            'original_source_packet', 'projection002_result', 'independent_qc002_result'):
        rule = pins[name]
        source[name] = _checked(root, SOURCE_DIR + '/' + rule['path'], rule)
    for name in ('original_source_packet', 'projection002_result', 'independent_qc002_result'):
        _verify_archive(_safe_file(root, SOURCE_DIR + '/' + pins[name]['path']))
    raw, html = source['raw_russian'], source['captured_html']
    ledger = parse_json(source['span_map'].decode('utf-8'))
    text = _verify_map(raw, html, ledger, pins)
    # The source-field is pinned to the exact included prior API row, not to a
    # missing whole upstream HTTP response (whose SHA cannot be verified).
    with zipfile.ZipFile(_safe_file(root, SOURCE_DIR + '/' + pins['original_source_packet']['path'])) as archive:
        rows = parse_json(archive.read('existing-packet/exact-russian-source-rows.json').decode('utf-8'))
    if not isinstance(rows, list) or not rows or rows[0].get('hadithnumber') != 1 or rows[0].get('text') != raw.decode('utf-8'):
        reject('original pinned Fawaz entry1 API field mismatch')
    for basename, key in (
            ('api-entry1-field.raw.utf8', 'raw_russian'),
            ('isnad-1.html', 'captured_html'),
            ('source-display-map.json', 'span_map')):
        if _safe_file(root, SOURCE_DIR + '/' + basename).read_bytes() != source[key]:
            reject('source asset archive differs from immutable evidence: ' + basename)
    parent = parse_json(source['parent_record'].decode('utf-8'))
    validate_record(parent, 'frozen Fawaz Bukhari1 parent')
    if (parent.get('id') != TARGET or parent.get('language') != 'ar' or
            parent.get('provider_entry_id') != 1 or
            tuple(v.get('language') for v in parent.get('language_versions', ())) != ORIGINAL_LANGUAGES):
        reject('parent identity/four languages not as frozen')
    candidate_bytes = _safe_file(root, SOURCE_DIR + '/candidate/record-one.json').read_bytes()
    if digest(candidate_bytes) != CANDIDATE_SHA256:
        reject('five-version candidate differs from separately pinned accepted bytes')
    candidate = parse_json(candidate_bytes.decode('utf-8'))
    validate_record(candidate, 'accepted private Russian candidate')
    if set(candidate) != set(parent) or len(candidate.get('language_versions', [])) != 5:
        reject('candidate changed top-level fields or five-version count')
    for key in parent:
        if key == 'language_versions':
            if candidate[key][:4] != parent[key]:
                reject('original four versions changed inside candidate')
        elif candidate[key] != parent[key]:
            reject('candidate modifies parent field: ' + key)
    ru = candidate['language_versions'][-1]
    if (ru.get('id') != RU_ID or ru.get('language') != 'ru' or ru.get('script') != 'Cyrl' or
            ru.get('scope') != 'source_entry' or
            ru.get('match_status') != 'same_provider_entry_only_not_canonical_identity' or
            ru.get('text') != text or
            (ru.get('source') or {}).get('source_text_sha256') != pins['raw_russian']['sha256'] or
            (ru.get('source') or {}).get('reversible_span_ledger_sha256') != pins['span_map']['sha256'] or
            (ru.get('source') or {}).get('capture_html_sha256') != pins['captured_html']['sha256'] or
            (ru.get('translation_provenance') or {}).get('ai_translation') != 'unknown' or
            (ru.get('translation_provenance') or {}).get('current_policy', {}).get('classification') != 'human'):
        reject('Russian metadata/wording/source boundary differs from accepted candidate')
    paths = ru['source']
    for field, filename in (
            ('raw_source_archive', 'api-entry1-field.raw.utf8'),
            ('capture_html_archive', 'isnad-1.html'),
            ('reversible_span_ledger_archive', 'source-display-map.json')):
        if paths[field] != SOURCE_DIR + '/' + filename:
            reject('Russian source has an unreviewed/local-missing archive locator: ' + field)
    validate_language_versions(candidate['language_versions'])
    return parent, candidate, {
        'target': TARGET,
        'version_id': RU_ID,
        'trusted_pins_sha256': TRUSTED_PINS_SHA256,
        'candidate_sha256': CANDIDATE_SHA256,
        'raw_source_sha256': pins['raw_russian']['sha256'],
        'source_html_sha256': pins['captured_html']['sha256'],
        'span_map_sha256': pins['span_map']['sha256'],
        'display_sha256': pins['display']['sha256'],
        'old_version_count': len(parent['language_versions']),
        'new_version_count': len(candidate['language_versions']),
        'new_source_occurrences': 0,
    }


def apply_ru_bukhari_001_overlay(bank_root: Path, projection_groups: list) -> dict:
    """Fail closed on missing/changed parent; append exactly one source version.

    Call after the Bank's normal source grouping/counterpart pass, BEFORE the
    search/records.jsonl deletion/rewrite. All other records keep their exact
    objects, IDs, source text, counterpart fields and language versions.
    """
    parent, candidate, result = load_frozen_candidate(bank_root)
    matches = [(group, i, record) for group in projection_groups
               for i, record in enumerate(group) if record.get('id') == TARGET]
    if len(matches) != 1:
        reject('expected exactly one existing Fawaz Bukhari1 parent, found ' + str(len(matches)))
    group, index, record = matches[0]
    language_versions = record.get('language_versions')
    if not isinstance(language_versions, list):
        reject('parent is missing language versions')
    codes = [item.get('language') for item in language_versions]
    if codes == list(ORIGINAL_LANGUAGES):
        if record != parent:
            reject('current four-version parent changed; revision requires Root decision')
        # Construct only the approved additional language-version object.
        # Copy-on-write avoids modifying any other currently shared reference.
        group[index] = candidate
        result['action'] = 'APPENDED_ONE_RUSSIAN_VERSION'
    elif 'ru' in codes:
        if record != candidate:
            reject('preexisting ru conflicts with exact reviewed candidate')
        result['action'] = 'IDEMPOTENT_VERIFIED_EXACT_CANDIDATE'
    else:
        reject('unexpected existing language-version set/order')
    if group[index]['id'] != TARGET or group[index]['language'] != 'ar':
        reject('unexpected changed source-occurrence identity')
    result['source_occurrence_count_unchanged'] = True
    result['source_record_id_unchanged'] = True
    result['original_parent_top_level_fields_unchanged'] = True
    result['original_ar_en_ur_bn_readings_unchanged'] = True
    return result


def bind_validator_expected(bank_root: Path, expected: dict, object_hash) -> dict:
    """Bind validator's re-derived four-version source object to exact RU projection.

    This is deliberately a *second* independently invoked production path.
    The validator must derive the old parent from registered canonical source
    BEFORE this method may extend its expected full-object fingerprint.
    Thus a changed/missing original parent cannot be legitimized by a rehashed
    co-editable RU ledger, source directory, or catalog.  Nothing is written.
    """
    parent, candidate, result = load_frozen_candidate(bank_root)
    descriptor = expected.get(TARGET)
    if not isinstance(descriptor, dict) or not callable(object_hash):
        reject('validator expected target is missing or malformed')
    if descriptor.get('authorized_material') is not True:
        reject('validator target is not an authorized registered material')
    for desc_field, original in (
        ('id', TARGET),
        ('source_id', parent['source_id']),
        ('language', parent['language']),
        ('book_key', parent['book_key']),
        ('edition', parent['edition']),
        ('text_arabic', parent['text_arabic']),
        ('text_translation', parent['text_translation']),
        ('canonical_record_sha256', parent['canonical_record_sha256']),
        ('locator', parent['source']['record_locator']),
        ('source_file', parent['source']['original_file']),
        ('source_sha256', parent['source']['sha256']),
    ):
        if descriptor.get(desc_field) != original:
            reject('canonical validator descriptor changes original parent: ' + desc_field)
    old_projection = {key: value for key, value in parent.items() if key != 'counterparts'}
    frozen_old_hash = object_hash(old_projection)
    if descriptor.get('full_projection_sha256') != frozen_old_hash:
        reject('source-reconstructed old parent differs from frozen original projection')
    projected = {key: value for key, value in candidate.items() if key != 'counterparts'}
    descriptor['full_projection_sha256'] = object_hash(projected)
    result['validator_original_projection_sha256'] = frozen_old_hash
    result['validator_expected_projection_sha256'] = descriptor['full_projection_sha256']
    result['validator_source_fingerprint_reconstructed_first'] = True
    return result
