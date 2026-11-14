"""Disposable, source-preserving index for the searchable Hadith Bank.

The index contains exact short previews, source-declared navigation metadata and
weighted positional postings.  It is not a source edition, translation, grading
decision or canonical identity registry.  Every ordinal addresses the unchanged
reader stream; full records remain in the existing verified detail store.
"""
from __future__ import annotations

import base64
from collections import Counter, defaultdict
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

from book_titles import book_label
from citation_search import COLLECTION_ALIASES, normalized as citation_normalized, record_citation_pairs
from counterpart_identity import provider_identity
from language_display import language_readings, LANGUAGE_LABELS
from review_display_policy import needs_ocr_review, review_badges


SCHEMA = 'hadith-bank-discovery-v1'
PREVIEW_CHARACTERS = 180
MAX_INDEX_BYTES = 384 * 1024 * 1024
MAX_COMPRESSED_BYTES = 96 * 1024 * 1024
MAX_POSTING_PART_BYTES = 1024 * 1024
PREVIEW_ROWS_PER_PART = 256
MAX_QUERY_TOKENS = 128
SEGMENT_GAP = MAX_QUERY_TOKENS + 1
TEXT, TITLE, NARRATOR, TOPIC, REFERENCE, SOURCE, METADATA = 1, 2, 4, 8, 16, 32, 64
_SHA = re.compile(r'[0-9a-f]{64}\Z')
_TECHNICAL = re.compile(r'(?:^|[-_:])(?:sqlite|snapshot|api|sha256|part)[-_:]|[0-9a-f]{12,}', re.I)
_ARABIC_MARKS = re.compile('[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d3-\u08ff]')
_SEARCH_MAP = str.maketrans({**dict(zip('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')),
                          'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ی': 'ي', 'ک': 'ك'})

# These are optional editorial navigation aids.  They are never written into a
# source record and never presented as a source quotation or a religious ruling.
EDITORIAL_TOPICS = [
    {'id': 'intentions', 'label': 'Intentions', 'terms': ['intention', 'intentions', 'niyyah', 'niya', 'النية', 'النيات', 'نية', 'نيات']},
    {'id': 'anger', 'label': 'Anger', 'terms': ['anger', 'angry', 'wrath', 'غضب', 'الغضب', 'تغضب']},
    {'id': 'parents', 'label': 'Parents', 'terms': ['parent', 'parents', 'mother', 'father', 'والدين', 'الوالدين', 'والديه', 'الأم', 'الأب']},
    {'id': 'prayer', 'label': 'Prayer', 'terms': ['prayer', 'prayers', 'pray', 'praying', 'salah', 'salat', 'صلاة', 'الصلاة', 'والصلاة', 'صلوات']},
    {'id': 'charity', 'label': 'Charity', 'terms': ['charity', 'alms', 'sadaqah', 'sadaqa', 'صدقة', 'الصدقة', 'صدقات']},
    {'id': 'patience', 'label': 'Patience', 'terms': ['patience', 'patient', 'sabr', 'صبر', 'الصبر']},
    {'id': 'fasting', 'label': 'Fasting', 'terms': ['fasting', 'fasts', 'sawm', 'siyam', 'صيام', 'الصيام', 'صوم']},
    {'id': 'remembrance', 'label': 'Remembrance', 'terms': ['remembrance', 'dhikr', 'zikr', 'ذكر', 'الذكر']},
]


def normalize(value):
    """Fold a disposable key; preserve Indic vowels and every original string."""
    value = unicodedata.normalize('NFKC', str(value)).lower().translate(_SEARCH_MAP)
    value = _ARABIC_MARKS.sub('', value).replace('\u0640', '')
    output, latin = [], False
    for char in unicodedata.normalize('NFD', value):
        category = unicodedata.category(char)
        if category == 'Cf':
            continue
        if category.startswith('M'):
            if not latin:
                output.append(char)
            continue
        latin = 'LATIN' in unicodedata.name(char, '')
        output.append(char)
    return unicodedata.normalize('NFC', ''.join(output))


def _cjk(char):
    code = ord(char)
    return (0x3040 <= code <= 0x30ff or 0x3400 <= code <= 0x9fff or
            0xf900 <= code <= 0xfaff or 0x20000 <= code <= 0x2fa1f)


@lru_cache(maxsize=4096)
def tokenize(value):
    """Unicode words and CJK characters, suitable for positional phrase search."""
    words, current = [], []
    for char in normalize(value):
        if _cjk(char):
            if current:
                words.append(''.join(current)); current = []
            words.append(char)
        elif unicodedata.category(char)[0] in ('L', 'N', 'M'):
            current.append(char)
        elif current:
            words.append(''.join(current)); current = []
    if current:
        words.append(''.join(current))
    return tuple(words)


def _strings(value):
    if isinstance(value, str) and value.strip():
        yield value
    elif type(value) in (int, float):
        yield str(value)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def _scalar(value):
    return value if isinstance(value, str) and value.strip() else str(value) if type(value) in (int, float) else None


def _origin(record):
    value = record.get('translation_provenance') or {}
    policy = value.get('current_policy') or record.get('current_policy') or {}
    if policy.get('classification') in ('human', 'ai', 'unknown'):
        return policy['classification']
    flag = value.get('ai_translation', record.get('ai_translation'))
    if flag is True:
        return 'ai'
    if flag is False or value.get('origin') in ('publisher_human_workflow', 'human_translator_credited'):
        return 'human'
    return 'unknown'


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def quotation_fingerprint_fields(record):
    """Exact accepted quotation strings for an independent preservation digest."""
    return [record['id'], [[item['language'], item.get('id'), item['text']]
                          for item in language_readings(record)
                          if isinstance(item.get('text'), str) and item['text'].strip()
                          and item.get('scope') not in ('source_context', 'external_source')
                          and item.get('quotation_status') not in
                          ('content_mismatch', 'boundary_pending', 'attribution_pending')]]


def quotation_fingerprint_bytes(record):
    return json.dumps(quotation_fingerprint_fields(record), ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8') + b'\n'


def expected_discovery_segments(record):
    """Recompute source-bound phrase/preview locators without building postings."""
    result, seen, position = [], set(), 0
    for reading in language_readings(record):
        value = reading.get('text')
        if (not isinstance(value, str) or not value.strip() or value in seen or
                reading.get('scope') in ('source_context', 'external_source') or
                reading.get('quotation_status') in ('content_mismatch', 'boundary_pending', 'attribution_pending')):
            continue
        seen.add(value)
        length = len(tokenize(value))
        result.append({'start': position, 'length': length, 'language': reading['language'],
                       'readingId': reading.get('id'), 'role': reading.get('role')})
        position += length + SEGMENT_GAP
    return result


def load_discovery_material_metadata(root, materials):
    """Read only registered manifests to retain explicit storage-part evidence."""
    root = Path(root).resolve()
    result = []
    for material in materials:
        item = dict(material)
        relative = item.get('manifest_path')
        if relative:
            if not isinstance(relative, str) or '\\' in relative or relative.startswith('/') or any(x in ('', '.', '..') for x in relative.split('/')):
                raise ValueError('Discovery material manifest path is unsafe')
            path = root / relative
            if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
                raise ValueError('Discovery material manifest must not traverse symlinks')
            if not path.is_file():
                raise ValueError('Registered discovery material manifest is missing: ' + relative)
            manifest = json.loads(path.read_text(encoding='utf-8'))
            if manifest.get('adapter') == 'pdf-intake-package-v1':
                # The existing registry already verifies the complete package
                # and projects its collections. This manifest is only a package
                # pointer: its ID is not a source ID and it has no edition/chunk
                # identity to import. Check the accepted pointer scope, and keep
                # the catalog metadata without inventing partition evidence.
                prefix = manifest.get('package_root')
                paths = [item.get(key) for key in ('source_file', 'canonical_records_path', 'source_metadata_path')]
                if (item.get('adapter') != 'pdf-intake-package-v1' or
                        not isinstance(prefix, str) or not re.fullmatch(r'attachments/[A-Za-z0-9][A-Za-z0-9._-]*', prefix) or
                        prefix != item.get('intake_root') or
                        not all(isinstance(value, str) and value.startswith(prefix + '/') and
                                not any(part in ('', '.', '..') for part in value.split('/')) and '\\' not in value for value in paths) or
                        (manifest.get('publication') or {}).get('authorized') is not True or
                        (item.get('publication') or {}).get('authorized') is not True):
                    raise ValueError('Discovery intake pointer differs from accepted catalog: ' + relative)
                result.append(item)
                continue
            if (manifest.get('source_id', manifest.get('id')) != item.get('dataset_id') or
                    manifest.get('language') != item.get('language') or manifest.get('book') != item.get('book_key') or
                    manifest.get('edition') != item.get('edition') or
                    (manifest.get('source') or {}).get('sha256') != item.get('source_sha256') or
                    (manifest.get('records') or {}).get('sha256') != item.get('canonical_records_sha256')):
                raise ValueError('Discovery material manifest differs from accepted catalog: ' + relative)
            for field in ('storage_shard', 'extraction_scope'):
                if isinstance(manifest.get(field), dict):
                    item[field] = manifest[field]
        result.append(item)
    return result


def _varint(target, value):
    if type(value) is not int or value < 0:
        raise ValueError('Discovery posting needs a nonnegative integer')
    while value >= 128:
        target.append((value & 127) | 128); value >>= 7
    target.append(value)


def validate_discovery_posting(encoded, record_count, expected_df):
    """Check a single encoded posting without materializing its positions.

    This independently validates the wire contract: canonical safe varints,
    increasing in-range ordinals and positions, known masks, text-position
    consistency, and exact document frequency. It does not claim to recompute
    tokenization or prove retrieval recall from the source text.
    """
    if type(record_count) is not int or record_count < 0 or type(expected_df) is not int or not 0 <= expected_df <= record_count:
        raise ValueError('Invalid discovery posting frequency/count')
    if not isinstance(encoded, str):
        raise ValueError('Discovery posting must be base64 text')
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError('Invalid discovery posting base64') from error
    offset = 0

    def read():
        nonlocal offset
        value, shift, start = 0, 0, offset
        while offset < len(raw):
            byte = raw[offset]; offset += 1
            value += (byte & 127) << shift
            if value > 2 ** 53 - 1 or shift > 49:
                raise ValueError('Discovery posting integer exceeds safe range')
            if not byte & 128:
                if offset - start > 1 and byte == 0:
                    raise ValueError('Noncanonical discovery posting integer')
                return value
            shift += 7
        raise ValueError('Truncated discovery posting integer')

    ordinal, count, positions = -1, 0, 0
    while offset < len(raw):
        delta, mask, length = read(), read(), read()
        ordinal += delta
        if delta <= 0 or ordinal >= record_count or mask <= 0 or mask > 127:
            raise ValueError('Invalid discovery posting ordinal or field mask')
        if bool(mask & TEXT) != bool(length) or length > len(raw) - offset:
            raise ValueError('Invalid discovery posting text positions')
        position = -1
        for _ in range(length):
            delta = read(); position += delta
            if delta <= 0 or position > 2 ** 53 - 1:
                raise ValueError('Invalid discovery posting position')
        positions += length; count += 1
        if count > expected_df:
            raise ValueError('Discovery posting document frequency differs')
    if count != expected_df:
        raise ValueError('Discovery posting document frequency differs')
    return {'documents': count, 'positions': positions, 'bytes': len(raw)}


def _named_values(value):
    if isinstance(value, str) and value.strip():
        return [value]
    if isinstance(value, list):
        return list(dict.fromkeys(name for item in value for name in _named_values(item)))
    if isinstance(value, dict):
        return _named_values(value.get('name') or value.get('name_as_supplied'))
    return []


def _navigation(record, readings):
    narrator = record.get('narrator') or {}
    narrators = _named_values(narrator.get('name')) + _named_values(narrator.get('names'))
    chapters = []
    for item in record.get('source_headings') or []:
        if isinstance(item, str) and item.strip():
            chapters.append(item)
        elif isinstance(item, dict):
            value = item.get('title') or item.get('heading') or item.get('value_verbatim')
            if isinstance(value, str) and value.strip():
                chapters.append(value)
    for field in ('chapter', 'chapter_title', 'section_title'):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            chapters.append(value)
        elif isinstance(value, dict) and isinstance(value.get('title'), str) and value['title'].strip():
            chapters.append(value['title'])
    structure = [item for item in record.get('source_structure_tags') or []
                 if isinstance(item, dict) and item.get('origin') == 'source_book_structure'
                 and type(item.get('hierarchy')) is int and item['hierarchy'] > 0
                 and isinstance(item.get('value_verbatim'), str) and item['value_verbatim'].strip()]
    structure.sort(key=lambda item: item['hierarchy'])
    source_path = [item['value_verbatim'] for item in structure]
    source_books = [source_path[0]] if source_path else []
    hierarchy_basis = 'source_structure_tags' if source_path else None
    chapters.extend(source_path[1:])
    source = record.get('source') or {}
    original = source.get('original_metadata') or {}
    if (not source_path and source.get('format') == 'pinned_json_source_index' and
            isinstance(original.get('provider_identity'), dict) and
            re.fullmatch(r'[0-9a-f]{40}', str(original.get('revision') or '')) and
            isinstance(record.get('title'), str) and record['title'].strip()):
        supplied_numbers = (record.get('number') or {}).get('as_supplied_by_language') or {}
        primary_number = supplied_numbers.get(record.get('language')) or {}
        if type((primary_number.get('reference') or {}).get('book')) in (int, str):
            # import_fawaz_bulk.source_section_name copies this title from the
            # pinned edition's explicit sections dictionary. No new role is
            # inferred from arbitrary narration titles.
            source_books = [record['title']]
            source_path = [record['title']]
            hierarchy_basis = 'pinned_provider_section'
    topics = []
    for item in record.get('topic_tags') or []:
        if not isinstance(item, dict) or not isinstance(item.get('label'), str) or not item['label'].strip():
            continue
        topics.append({'value': str(item.get('id') or item['label']), 'label': item['label'],
                       'path': [x for x in item.get('path') or [] if isinstance(x, str)], 'origin': 'source'})
    types = set(value for value in record.get('report_types') or [] if isinstance(value, str) and value)
    if isinstance(record.get('report_type'), str) and record['report_type']:
        types.add(record['report_type'])
    for reading in readings:
        if not isinstance(reading.get('text'), str) or not reading['text'].strip():
            continue
        source = reading.get('source') or {}
        if isinstance(source.get('report_type'), str) and source['report_type']:
            types.add(source['report_type'])
    if not types:
        kind = record.get('content_kind') or record.get('record_type')
        mapping = {'source_attributed_prophetic_narration': 'prophetic_report',
                   'companion_report': 'companion_report', 'quoted_companion_saying': 'companion_report',
                   'quoted_companion_report': 'companion_report', 'companion_report_excerpt': 'companion_report',
                   'successor_report': 'successor_report', 'scholar_saying': 'scholar_saying',
                   'commentary': 'commentary', 'hadith': 'hadith', 'hadith_occurrence': 'hadith',
                   'hadith_excerpt': 'hadith_excerpt', 'source_fragment': 'source_fragment'}
        if kind in mapping:
            types.add(mapping[kind])
    grades, unattributed = [], []

    def add_grades(value, language=None, provider_names=False):
        if isinstance(value, list):
            for item in value:
                add_grades(item, language, True)
        elif isinstance(value, dict):
            grade = _scalar(value.get('grade'))
            authority = _scalar(value.get('grader') or value.get('authority') or
                                (value.get('name') if provider_names else None))
            if grade and authority:
                item = {'value': authority + '\x1f' + grade, 'label': grade + ' — ' + authority,
                        'grade': grade, 'authority': authority}
                if language:
                    item['language'] = language
                if item not in grades:
                    grades.append(item)
            elif grade and grade not in unattributed:
                unattributed.append(grade)
            own = value.get('source_assessments_by_language')
            if isinstance(own, dict):
                for code, items in own.items():
                    add_grades(items, code)
    add_grades(record.get('grading'))
    for version in record.get('language_versions') or []:
        if isinstance(version, dict):
            add_grades(version.get('grading'), version.get('language'))
    return {'narrators': list(dict.fromkeys(narrators)), 'chapters': list(dict.fromkeys(chapters)),
            'sourceBooks': source_books, 'sourcePath': source_path, 'sourceHierarchyBasis': hierarchy_basis,
            'topics': topics, 'reportTypes': sorted(types),
            'reportType': next(iter(types)) if len(types) == 1 else 'mixed' if types else 'unknown',
            'grades': grades, 'unattributedGrades': unattributed}


def _edition(record, material):
    source = record.get('source') or {}
    language, book, edition = record['language'], record['book_key'], record['edition']
    title = source.get('work_title') or source.get('name') or material.get('source_name') or book_label(book, language)
    title = title if isinstance(title, str) and title.strip() else book_label(book, language)
    translator = record.get('translator') or {}
    translator_name = _scalar(translator.get('name')) if isinstance(translator, dict) else None
    source_edition = _scalar(source.get('edition'))
    shard = material.get('storage_shard') or {}
    extraction_scope = material.get('extraction_scope') or {}
    declared_edition = _scalar(shard.get('original_source_edition') or
                               extraction_scope.get('source_edition_key_before_partitioning'))
    if declared_edition:
        source_edition = declared_edition
    supplied_edition = source_edition or (edition if not _TECHNICAL.search(edition) else None)
    if supplied_edition and (_TECHNICAL.search(supplied_edition) or re.search(r'(?:^|-)web-\d{8}', supplied_edition)):
        supplied_edition = None
    pieces = [title, LANGUAGE_LABELS.get(language, language)]
    if translator_name:
        pieces.append(translator_name)
    if supplied_edition and supplied_edition not in title:
        pieces.append(supplied_edition)
    original = source.get('original_file') or material.get('source_file')
    checksum = source.get('sha256') or material.get('source_sha256')
    key = record['source_id']
    evidence = None
    if isinstance(original, str) and original and isinstance(checksum, str) and _SHA.fullmatch(checksum):
        binding = [language, book, original, checksum, translator_name, source_edition]
        key = 'source-edition-' + _sha(json.dumps(binding, ensure_ascii=False, separators=(',', ':')))[:20]
        evidence = {'basis': 'same_exact_source_file', 'path': original, 'sha256': checksum}
    descriptor = material.get('source_descriptor') or {}
    source_url = descriptor.get('url') or source.get('url')
    format_name = descriptor.get('format') or source.get('format')
    if declared_edition and isinstance(source_url, str) and source_url.startswith(('https://', 'http://')):
        # Explicit importer metadata, rather than a filename pattern, declares
        # that the records are transport partitions of one source edition.
        if (shard.get('occurrence_ids_unchanged') is True or
                type(extraction_scope.get('publication_part')) is int):
            source_base = shard.get('original_source_id') or re.sub(r'-part-\d+$', '', record['source_id'])
            binding = [language, book, source_base, declared_edition, source_url, format_name, translator_name]
            key = 'source-edition-' + _sha(json.dumps(binding, ensure_ascii=False, separators=(',', ':')))[:20]
            evidence = {'basis': 'explicit_registered_storage_partition', 'manifest': material.get('manifest_path'),
                        'originalSourceEdition': declared_edition, 'originalSourceId': source_base,
                        'path': original, 'sha256': checksum, 'sourceURL': source_url}
    elif (format_name == 'pinned_json_source_index' and isinstance(checksum, str) and _SHA.fullmatch(checksum)
          and isinstance(source_url, str) and re.fullmatch(r'https://github\.com/fawazahmed0/hadith-api/tree/[0-9a-f]{40}', source_url)
          and re.fullmatch(r'fawaz-[a-z0-9-]+-[0-9a-f]{12}-[a-z]+(?:-part-\d+)?', record['source_id'])):
        # The Fawaz producer copies the same source-index bytes into each part;
        # its documented namespace, pinned URL and exact checksum bind them.
        source_base = re.sub(r'-part-\d+$', '', record['source_id'])
        binding = [language, book, source_base, source_url, checksum, translator_name]
        key = 'source-edition-' + _sha(json.dumps(binding, ensure_ascii=False, separators=(',', ':')))[:20]
        evidence = {'basis': 'pinned_provider_identical_source_index', 'path': original, 'sha256': checksum,
                    'sourceURL': source_url, 'originalSourceId': source_base}
    return {'sourceName': title, 'editionLabel': ' · '.join(dict.fromkeys(pieces)),
            'translator': translator_name, 'editionGroup': key, 'editionEvidence': evidence}


def _provider_family(record):
    """Consume established source identity/accepted alignments; never match text."""
    policy = record.get('counterpart_policy') or {}
    if policy.get('mode') == 'disabled':
        return None
    identity = provider_identity(record)
    arabic = record.get('text_arabic')
    if record.get('book_key') == 'hadeethenc' and identity['status'] == 'linked' and isinstance(arabic, str) and arabic.strip():
        digest = _sha(arabic)
        return {'key': 'hadeethenc:' + identity['id'] + ':' + digest,
                'basis': 'same_publisher_entry_and_exact_source_arabic', 'provider': 'hadeethenc',
                'providerId': identity['id'], 'arabicSha256': digest,
                'relation': 'same_publisher_arabic_version', 'evidenceFields': identity['basis']}
    counterparts = record.get('counterparts') or {}
    proof = counterparts.get('quotation_evidence') or {}
    linked = counterparts.get('provider_identity') or {}
    target = counterparts.get('arabic') or {}
    target_text = target.get('text')
    if not isinstance(target_text, str) or not target_text.strip():
        return None
    status, relation = counterparts.get('status'), proof.get('relation')
    if status not in ('exact', 'reviewed_parallel') or linked.get('status') != 'linked':
        return None
    if relation not in ('normalized_exact', 'source_excerpt', 'same_narration'):
        return None
    source_field = proof.get('field')
    source_text = record.get(source_field) if isinstance(source_field, str) else None
    if not isinstance(source_text, str) or proof.get('source_text_sha256') != _sha(source_text):
        return None
    target_hash = proof.get('target_text_sha256')
    if isinstance(target_hash, dict):
        target_hash = target_hash.get('arabic')
    if target_hash != _sha(target_text):
        return None
    if proof.get('source_file_sha256') and proof['source_file_sha256'] != (record.get('source') or {}).get('sha256'):
        return None
    provider = linked.get('provider')
    identifier = linked.get('id')
    if not isinstance(provider, str) or not provider or not isinstance(identifier, str) or not identifier:
        return None
    if status == 'exact':
        if counterparts.get('match_method') not in ('provider_id_and_source_quotation', 'unique_source_quotation', 'unique_source_quotation_and_citation'):
            return None
        target_identity = provider_identity({'source': {'record_url': target.get('source_url')}})
        # Some unique-quotation assignments retain absent original provider
        # identity. They remain separate unless the accepted wrapper links it.
        if provider != 'hadeethenc' or target_identity.get('id') != identifier:
            return None
    else:
        if counterparts.get('match_method') != 'reviewed_source_narration_alignment':
            return None
        if not isinstance(proof.get('review'), dict) or not proof.get('mapping_path') or not _SHA.fullmatch(str(proof.get('mapping_sha256') or '')):
            return None
    return {'key': provider.lower() + ':' + identifier + ':' + target_hash,
            'basis': 'accepted_counterpart_alignment', 'provider': provider, 'providerId': identifier,
            'arabicSha256': target_hash, 'relation': relation, 'evidence': proof}


def _families(rows, candidates, accepted):
    """Explicit groups take precedence; inferred identity chains are forbidden."""
    id_counts = Counter(row['id'] for row in rows)
    ids = {row['id']: row['ordinal'] for row in rows if id_counts[row['id']] == 1}
    owner, groups = {}, []
    for item in (accepted or {}).get('groups') or []:
        members = item.get('member_ids') or []
        if not isinstance(members, list) or len(members) < 2 or any(x not in ids for x in members):
            raise ValueError('Discovery received an invalid prevalidated reader group')
        ordinals = [ids[x] for x in members]
        if any(x in owner for x in ordinals):
            raise ValueError('Discovery received overlapping prevalidated reader groups')
        group = {'id': 'reviewed:' + str(item['id']), 'members': ordinals,
                 'evidence': {'basis': 'accepted_reader_group', 'comparisons': item.get('comparisons') or []}}
        groups.append(group)
        for ordinal in ordinals:
            owner[ordinal] = group['id']
    by_key = defaultdict(list)
    for ordinal, candidate in candidates.items():
        if ordinal not in owner and id_counts[rows[ordinal]['id']] == 1:
            by_key[candidate['key']].append(ordinal)
    for key, members in sorted(by_key.items()):
        if len(members) < 2:
            continue
        group_id = 'provider:' + key
        groups.append({'id': group_id, 'members': members, 'evidence': {
            'basis': 'accepted_provider_identity_and_source_binding',
            'memberRelations': [{'ordinal': ordinal, **{k: v for k, v in candidates[ordinal].items() if k != 'key'}} for ordinal in members]}})
        for ordinal in members:
            owner[ordinal] = group_id
    for row in rows:
        row['groupId'] = owner.get(row['ordinal'])
    return groups


def _facet_items(rows):
    counts = defaultdict(Counter)
    labels = defaultdict(dict)
    for row in rows:
        values = {'language': [(code, LANGUAGE_LABELS.get(code, code)) for code in row['languages']],
                  'book': [(row['book_key'], row['collection'])],
                  'source': [(row['editionGroup'], row['editionLabel'])],
                  'origin': [(row['origin'], row['origin'].title())],
                  'narrator': [(value, value) for value in row['narrators']],
                  'sourceBook': [(value, value) for value in row.get('sourceBooks') or []],
                  'chapter': [(value, value) for value in row['chapters']],
                  'reportType': [(value, value.replace('_', ' ').capitalize()) for value in row['reportTypes']],
                  'grade': [(value['value'], value['label']) for value in row['grades']],
                  'topic': [(value['value'], value['label']) for value in row['topics']]}
        for facet, items in values.items():
            for value, label in set(items):
                counts[facet][value] += 1
                labels[facet].setdefault(value, label)
    return {facet: [{'value': value, 'label': labels[facet][value], 'count': count}
                    for value, count in sorted(values.items(), key=lambda pair: (labels[facet][pair[0]], pair[0]))]
            for facet, values in sorted(counts.items())}


def expected_discovery_row(record, ordinal, material=None, *, reading_sets=None):
    """Derive exact source-bound navigation/previews for independent validation.

    The producer can pass its already computed ``(all_readings, quotations)``.
    Independent validators should omit that optimization. ``baseEditionLabel``
    is the source-derived label before deterministic whole-bank disambiguation;
    ``editionLabel`` may acquire a display suffix only after all rows are known.
    Search positions and presentation-family IDs are validated separately.
    """
    if not isinstance(record, dict) or any(not isinstance(record.get(key), str) or not record[key]
                                          for key in ('id', 'language', 'book_key', 'edition', 'source_id')):
        raise ValueError('Discovery requires complete source occurrence identities')
    if type(ordinal) is not int or ordinal < 0:
        raise ValueError('Discovery row ordinal must be nonnegative')
    if reading_sets is None:
        all_readings = language_readings(record)
        readings = [item for item in all_readings if isinstance(item.get('text'), str) and item['text'].strip()
                    and item.get('scope') not in ('source_context', 'external_source')
                    and item.get('quotation_status') not in ('content_mismatch', 'boundary_pending', 'attribution_pending')]
    else:
        all_readings, readings = reading_sets
    previews = {}
    for reading in sorted(readings, key=lambda item: not item.get('primary')):
        code = reading['language']
        if code not in previews:
            text = reading['text']
            own_source = reading.get('source') or {}
            previews[code] = {'language': code, 'text': text[:PREVIEW_CHARACTERS], 'scope': reading.get('scope'),
                              'role': reading.get('role'), 'truncated': len(text) > PREVIEW_CHARACTERS,
                              'translationOrigin': reading.get('translation_origin'),
                              'sourceName': own_source.get('name'),
                              'sourceURL': own_source.get('record_url') or own_source.get('url')}
    language_states = {}
    for reading in all_readings:
        state = 'missing'
        if reading in readings:
            state = 'text'
        elif reading.get('quotation_status') == 'content_mismatch':
            state = 'content_mismatch'
        elif reading.get('quotation_status') in ('boundary_pending', 'attribution_pending'):
            state = 'pending_review'
        elif reading.get('scope') == 'external_source':
            own_source = reading.get('source') or {}
            address = own_source.get('record_url') or own_source.get('url')
            try:
                parsed = urlsplit(address) if isinstance(address, str) else None
                if parsed and parsed.scheme in ('https', 'http') and parsed.hostname and not parsed.username and not parsed.password:
                    state = 'external_link'
            except ValueError:
                pass
        language_states[reading['language']] = state
    # A stored reading wins over a same-language external-only alternative.
    language_states.update({code: 'text' for code in previews})
    pairs = sorted(':'.join(pair) for pair in record_citation_pairs(record))
    labels = [book_label(pair.rsplit(':', 1)[0], 'en') + ' ' + pair.rsplit(':', 1)[1] for pair in pairs]
    number = record.get('number') or {}
    row = {key: record[key] for key in ('id', 'language', 'book_key', 'edition', 'source_id')}
    row.update(ordinal=ordinal, title=_scalar(record.get('title')), collection=book_label(record['book_key'], 'en'),
               reference='; '.join(labels) if labels else 'Canonical reference not established', references=pairs,
               sourceNumber=_scalar(number.get('in_book')), providerNumber=_scalar(record.get('provider_entry_id') or number.get('source_entry_id')),
               readings=list(previews.values()), languages=sorted(previews), languageStates=language_states,
               availability={name: language_states.get(code) if language_states.get(code) in ('text', 'external_link') else 'missing'
                             for name, code in (('arabic', 'ar'), ('english', 'en'))},
               origin=_origin(record), ocrPending=needs_ocr_review(record), review=review_badges(record),
               **_edition(record, material or {}), **_navigation(record, readings))
    row['baseEditionLabel'] = row['editionLabel']
    # Source category IDs can be local to a provider/edition. Never equate two
    # taxonomies merely because both call a category "1" or "Prayer".
    for topic in row['topics']:
        topic['sourceTopicId'] = topic['value']
        topic['value'] = row['editionGroup'] + '\x1f' + topic['value']
    return row


def build_discovery_payload(records, snapshot):
    """Index one ordered, verified stream without editing any input record.

    ``snapshot`` is the already validated reader metadata, including
    ``reader_groups`` and material descriptors.  Postings index every supplied
    quotation word, not just the display previews.  Annotation text is omitted
    and remains available through the reader's explicit commentary search.
    """
    rows, postings, previous, frequencies, reference_index, candidates = [], {}, {}, Counter(), defaultdict(list), {}
    materials = {m['dataset_id']: m for m in snapshot.get('materials') or [] if isinstance(m, dict) and isinstance(m.get('dataset_id'), str)}
    identifiers = set()
    id_hash, text_hash = hashlib.sha256(), hashlib.sha256()
    for ordinal, record in enumerate(records):
        if not isinstance(record, dict) or any(not isinstance(record.get(key), str) or not record[key] for key in ('id', 'language', 'book_key', 'edition', 'source_id')):
            raise ValueError('Discovery requires complete source occurrence identities')
        identity = tuple(record[key] for key in ('id', 'language', 'book_key', 'edition', 'source_id'))
        if identity in identifiers:
            raise ValueError('Discovery full occurrence identity is duplicated')
        identifiers.add(identity); id_hash.update((record['id'] + '\n').encode('utf-8'))
        all_readings = language_readings(record)
        readings = [reading for reading in all_readings if isinstance(reading.get('text'), str) and reading['text'].strip()
                    and reading.get('scope') not in ('source_context', 'external_source')
                    and reading.get('quotation_status') not in ('content_mismatch', 'boundary_pending', 'attribution_pending')]
        text_hash.update(json.dumps([record['id'], [[x['language'], x.get('id'), x['text']] for x in readings]],
                                   ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8') + b'\n')
        row = expected_discovery_row(record, ordinal, materials.get(record['source_id']),
                                     reading_sets=(all_readings, readings))
        pairs = row['references']
        labels = [book_label(pair.rsplit(':', 1)[0], 'en') + ' ' + pair.rsplit(':', 1)[1] for pair in pairs]
        rows.append(row)
        candidate = _provider_family(record)
        if candidate:
            candidates[ordinal] = candidate
        for pair in pairs:
            reference_index[pair].append(ordinal)
        doc = {}

        def index_text(value, mask, start=None):
            tokens = tokenize(value)
            for position, token in enumerate(tokens):
                entry = doc.setdefault(token, [0, []]); entry[0] |= mask
                if start is not None:
                    entry[1].append(start + position)
            return len(tokens)

        position, seen_text, segments = 0, set(), []
        for reading in readings:
            value = reading['text']
            if value in seen_text:
                continue
            seen_text.add(value)
            length = index_text(value, TEXT, position)
            segments.append({'start': position, 'length': length, 'language': reading['language'],
                             'readingId': reading.get('id'), 'role': reading.get('role')})
            position += length + SEGMENT_GAP
        row['searchSegments'] = segments
        for value in _strings(record.get('title')):
            index_text(value, TITLE)
        narrator = record.get('narrator') or {}
        for key in ('name', 'names', 'verbatim', 'chain', 'isnad'):
            for value in _strings(narrator.get(key)):
                index_text(value, NARRATOR)
        for value in _strings([record.get('topic_tags'), record.get('source_headings')]):
            index_text(value, TOPIC)
        for value in labels:
            index_text(value, REFERENCE)
        for value in _strings([record.get('references'), record.get('number')]):
            index_text(value, REFERENCE)
        for value in _strings([row['collection'], row['sourceName'], row['editionLabel'], record.get('translator')]):
            index_text(value, SOURCE)
        for key in ('id', 'source_id', 'edition', 'provider_entry_id', 'record_type', 'content_kind', 'grading', 'editorial_tags'):
            for value in _strings(record.get(key)):
                index_text(value, METADATA)
        for token, (mask, positions) in doc.items():
            packed = postings.setdefault(token, bytearray())
            _varint(packed, ordinal - previous.get(token, -1)); previous[token] = ordinal
            _varint(packed, mask); _varint(packed, len(positions))
            prior = -1
            for value in positions:
                _varint(packed, value - prior); prior = value
            frequencies[token] += 1
    expected_count = snapshot.get('record_count', snapshot.get('count'))
    if type(expected_count) is int and expected_count != len(rows):
        raise ValueError('Discovery record count differs from verified source snapshot')
    groups = _families(rows, candidates, snapshot.get('reader_groups'))
    # Equal labels do not collapse editions. Stable display ordinals only
    # disambiguate labels whose evidence keys are different.
    names = defaultdict(set)
    for row in rows:
        names[row['editionLabel']].add(row['editionGroup'])
    disambiguation = {label: {key: i + 1 for i, key in enumerate(sorted(keys))}
                      for label, keys in names.items() if len(keys) > 1}
    for row in rows:
        if row['editionLabel'] in disambiguation:
            row['editionLabel'] += ' · Source edition ' + str(disambiguation[row['editionLabel']][row['editionGroup']])
    terms = sorted(postings)
    payload = {'schema': SCHEMA, 'record_count': len(rows), 'records_sha256': snapshot.get('records_sha256'),
               'occurrence_ids_sha256': id_hash.hexdigest(), 'indexed_quotation_fields_sha256': text_hash.hexdigest(),
               'preview_characters': PREVIEW_CHARACTERS, 'rows': rows, 'terms': terms,
               'postings': [[frequencies[token], base64.b64encode(postings[token]).decode('ascii')] for token in terms],
               'reference_index': dict(sorted(reference_index.items())), 'groups': groups, 'facets': _facet_items(rows),
               'collection_aliases': [[key, citation_normalized(pattern)] for key, pattern in COLLECTION_ALIASES],
               'editorial': {'label': 'Editorial search aids — not source text or a religious ruling',
                             'topics': EDITORIAL_TOPICS, 'source_text_changed': False},
               'limits': {'max_query_tokens': MAX_QUERY_TOKENS, 'max_query_characters': 512},
               'statistics': {'terms': len(terms), 'postings': sum(frequencies.values()),
                              'reading_families': len(rows) - sum(len(group['members']) - 1 for group in groups),
                              'grouped_occurrences': sum(len(group['members']) for group in groups)}}
    tokenize.cache_clear()
    return payload


def serialize_discovery(payload):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(raw) > MAX_INDEX_BYTES:
        raise ValueError('Discovery index exceeds decoded size limit; partition the derived index before publication')
    return raw


def _compact_rows(payload):
    """Intern repeated navigation values; source strings remain exact pool values."""
    rows = payload['rows']
    columns = sorted(set().union(*(row.keys() for row in rows)) - {'ordinal'}) if rows else []
    pools, encoded = {}, [[] for _ in rows]
    for field in columns:
        values, lookup, indices = [], {}, []
        for row in rows:
            value = row.get(field)
            key = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            if key not in lookup:
                lookup[key] = len(values); values.append(value)
            indices.append(lookup[key])
        pooled = len(values) < len(rows) * 0.8
        if pooled:
            pools[field] = values
        for index, row in enumerate(rows):
            encoded[index].append(indices[index] if pooled else row.get(field))
    return {**payload, 'rows': encoded, 'row_columns': columns, 'row_pools': pools}


def expand_discovery_payload(payload):
    """Expand compact wire rows for independent validation; no source mutation."""
    if 'row_columns' not in payload:
        return payload
    columns, pools = payload['row_columns'], payload.get('row_pools') or {}
    if not isinstance(columns, list) or len(columns) != len(set(columns)):
        raise ValueError('Invalid compact discovery columns')
    rows = []
    for ordinal, values in enumerate(payload['rows']):
        if not isinstance(values, list) or len(values) != len(columns):
            raise ValueError('Invalid compact discovery row')
        row = {'ordinal': ordinal}
        for key, value in zip(columns, values):
            if key in pools:
                if type(value) is not int or not 0 <= value < len(pools[key]):
                    raise ValueError('Invalid compact discovery pool index')
                value = pools[key][value]
            row[key] = value
        row.setdefault('readings', [])
        rows.append(row)
    return {**payload, 'rows': rows}


def write_discovery_artifact(payload, directory, relative_prefix=''):
    """Publish compact navigation first, query postings and page previews separately.

    The returned descriptor points to navigation metadata. Each payload includes
    bounded content-addressed posting/preview descriptors. Files are written
    before the parent descriptor is returned. Previous content is never deleted.
    Inline/offline builders may still embed the complete original payload.
    """
    directory = Path(directory)
    if directory.is_symlink() or any(parent.is_symlink() for parent in directory.parents):
        raise ValueError('Discovery output must not traverse symlinks')
    if relative_prefix and (relative_prefix.startswith(('/', '\\')) or '\\' in relative_prefix or
                            any(part in ('', '.', '..') for part in relative_prefix.strip('/').split('/'))):
        raise ValueError('Discovery artifact prefix must be a safe relative path')
    directory.mkdir(parents=True, exist_ok=True)

    def publish(part, prefix, extra=None):
        raw = serialize_discovery(part)
        compressed = gzip.compress(raw, compresslevel=6, mtime=0)
        if len(compressed) > MAX_COMPRESSED_BYTES:
            raise ValueError('Discovery part exceeds transfer size limit')
        digest = hashlib.sha256(compressed).hexdigest()
        name = prefix + '-' + digest + '.json.gz'
        target = directory / name
        if target.is_symlink():
            raise ValueError('Discovery output must not be a symlink')
        if target.exists() and target.read_bytes() != compressed:
            raise ValueError('Content-addressed discovery output has conflicting bytes')
        if not target.exists():
            temporary = directory / ('.' + name + '.tmp')
            if temporary.exists():
                raise ValueError('Discovery publication already has a pending temporary file')
            try:
                with temporary.open('xb') as handle:
                    handle.write(compressed)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        return {'path': (relative_prefix.rstrip('/') + '/' if relative_prefix else '') + name,
                'schema': part['schema'], 'encoding': 'gzip-json', 'sha256': digest, 'bytes': len(compressed),
                'uncompressed_sha256': hashlib.sha256(raw).hexdigest(), 'uncompressed_bytes': len(raw),
                'record_count': payload['record_count'], 'records_sha256': payload.get('records_sha256'), **(extra or {})}

    posting_parts, posting_index, batch, batch_bytes, first = [], [], [], 0, 0

    def flush_postings():
        nonlocal first, batch, batch_bytes
        if not batch:
            return
        body = {'schema': SCHEMA + '-postings', 'record_count': payload['record_count'],
                'records_sha256': payload.get('records_sha256'), 'first_term': first,
                'postings': batch}
        posting_parts.append(publish(body, 'discovery-postings', {'first_term': first, 'term_count': len(batch)}))
        first += len(batch); batch, batch_bytes = [], 0

    for frequency, encoded in payload['postings']:
        if batch and batch_bytes + len(encoded) > MAX_POSTING_PART_BYTES:
            flush_postings()
        posting_index.append([frequency, len(posting_parts)])
        batch.append(encoded); batch_bytes += len(encoded) + 3
    flush_postings()
    preview_parts = []
    for first in range(0, len(payload['rows']), PREVIEW_ROWS_PER_PART):
        rows = payload['rows'][first:first + PREVIEW_ROWS_PER_PART]
        body = {'schema': SCHEMA + '-previews', 'record_count': payload['record_count'],
                'records_sha256': payload.get('records_sha256'), 'first_ordinal': first,
                'previews': [row['readings'] for row in rows]}
        preview_parts.append(publish(body, 'discovery-previews', {'first_ordinal': first, 'row_count': len(rows)}))
    navigation = {**payload,
                  'rows': [{key: value for key, value in row.items() if key != 'readings'} for row in payload['rows']],
                  'postings': posting_index, 'postings_shards': posting_parts, 'preview_shards': preview_parts,
                  'delivery': 'query-postings-and-page-previews'}
    descriptor = publish(_compact_rows(navigation), 'discovery')
    descriptor['parts'] = posting_parts + preview_parts
    descriptor['total_bytes'] = descriptor['bytes'] + sum(part['bytes'] for part in descriptor['parts'])
    descriptor['delivery'] = navigation['delivery']
    return descriptor
