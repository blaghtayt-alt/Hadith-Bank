#!/usr/bin/env python3
"""Import the exact reconstructed Filipino Hisn source into the active reader.

This is a deterministic source adapter, not OCR, translation, canonical matching
or independent scholarly review. Historical source evaluations remain in the
preserved delivery; the owner's later publication decision controls visibility.
"""
import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from material_registry import SOURCE_IMPORT_DECISION
from register_material import register


SLUG = 'fil-hisn-muslim-3e409dd7'
PREFIX = 'materials/' + SLUG + '/'
IMPORT = 'imports/filipino-hisn-reconstructed-20261112/'
RECONSTRUCTION = IMPORT + 'reconstruction/'
SOURCE_JSON = RECONSTRUCTION + 'data/corrected_all_records.json.gz'
SOURCE_METADATA = RECONSTRUCTION + 'data/book_metadata.json'
PRESERVATION_MANIFEST = IMPORT + 'preservation-manifest.json'
CLASSIFICATIONS = RECONSTRUCTION + 'data/content_classification_reconstructed_v2.json.gz'
BLOCKER_INDEX = RECONSTRUCTION + 'audit/record_blocker_index.json.gz'
SOURCE_PDF = PREFIX + 'FIL-HISN-PRIVATE.pdf'
SOURCE_HASH = '3e409dd7266c2a150645ecfea548f266edf80c9c5df5129aa8df7a977d248a07'
SOURCE_SIZE = 5321887
INPUT_HASH = '9607d998949390d4608af9355e40fe24186fcf04c0ff1fd26cc7df95a78bb3d7'
METADATA_HASH = '8e28533cc1353b8d862924bf132ab0e37c55480ab71e469ddf856a1a923140bd'
EDITION = 'pdf-3e409dd7-third-edition'
TITLE = 'Hisnul Muslim — Hisn al-Muslim'
SOURCE_URL = 'https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/' + SOURCE_PDF
ACTIVE_CLASSIFICATION = 'content_classification_reconstructed_v2'
READER_PARTITION = 'hisn_hadith_dhikr_context'
EXPECTED_COUNTS = {READER_PARTITION: 298, 'independent_non_prophetic': 14,
                   'quran_and_author_only': 6, 'attribution_unresolved': 5}
PARTITION_PATHS = {
    'non_hadith': 'non-hadith/' + SLUG + '/records.jsonl',
    'independent_non_prophetic': 'non-hadith/' + SLUG + '/independent_non_prophetic.jsonl',
    'quran_and_author_only': 'non-hadith/' + SLUG + '/quran_and_author_only.jsonl',
    'attribution_unresolved': 'unclassified/' + SLUG + '/records.jsonl',
}
OWNER_INSTRUCTIONS = ['integrate into the bank and the html',
                      'integrate into html , dont keep as hold']
COUNTERPART_REASON = (
    'Only Arabic printed in the identified Filipino PDF is supplied by this import. '
    'Retained external narration evidence is not an approved counterpart or canonical '
    'occurrence mapping; automatic and reviewed counterpart assignment is disabled.')
JOIN = '\n\n'
ARABIC_LETTERS = re.compile(r'[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]')
FILIPINO_TYPES = {'narration', 'translation', 'quran_translation', 'transliteration'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                            for row in rows), encoding='utf-8')


def read_checked(path, expected):
    raw = path.read_bytes()
    expanded = gzip.decompress(raw) if path.suffix == '.gz' else raw
    if sha(expanded) != expected:
        raise ValueError('Unexpected expanded source bytes: ' + str(path))
    return json.loads(expanded)


def occurrence_id(record_id):
    """A source occurrence survives review/version changes without duplication."""
    return SLUG + ':' + record_id


def descriptor(root, relative):
    path = root / relative
    return {'path': relative, 'sha256': sha(path.read_bytes()), 'size_bytes': path.stat().st_size}


def verify_preservation(root):
    manifest = json.loads((root / PRESERVATION_MANIFEST).read_text(encoding='utf-8'))
    if manifest['source_pdf_sha256'] != SOURCE_HASH:
        raise ValueError('Preservation manifest identifies a different source PDF')
    entries, seen = [], set()
    for item in manifest['files']:
        name = item['path']
        parts = PurePosixPath(name).parts
        if (not name.startswith(RECONSTRUCTION) or '\\' in name or
                any(part in ('', '.', '..') for part in parts) or name in seen):
            raise ValueError('Unsafe or duplicate preservation path: ' + name)
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Preserved source path escapes repository: ' + name)
        raw = path.read_bytes()
        if len(raw) != item['size_bytes'] or sha(raw) != item['sha256']:
            raise ValueError('Preserved source checksum/size mismatch: ' + name)
        compression = item.get('compression')
        if compression not in (None, 'none', 'gzip'):
            raise ValueError('Unsupported preservation compression: ' + name)
        if compression == 'gzip':
            expanded = gzip.decompress(raw)
            if (sha(expanded) != item['uncompressed_sha256'] or
                    len(expanded) != item['uncompressed_size_bytes']):
                raise ValueError('Expanded preservation checksum/size mismatch: ' + name)
        seen.add(name)
        entries.append(copy.deepcopy(item))
    if not {SOURCE_JSON, SOURCE_METADATA, CLASSIFICATIONS, BLOCKER_INDEX} <= seen:
        raise ValueError('Missing required preserved source and audit files')
    return entries + [descriptor(root, PRESERVATION_MANIFEST)]


def validate_source(data):
    rows = data['records']
    if data['book']['source_sha256'] != SOURCE_HASH or data['book']['pdf_page_count'] != 276:
        raise ValueError('Source PDF identity or extent changed')
    ids = [r['record_id'] for r in rows]
    if len(ids) != 323 or len(set(ids)) != 323:
        raise ValueError('Expected exactly 323 distinct source records')
    counts = Counter(r[ACTIVE_CLASSIFICATION]['record_partition'] for r in rows)
    if dict(counts) != EXPECTED_COUNTS:
        raise ValueError('Reconstructed routing changed: ' + str(dict(counts)))
    segment_ids, candidate_count = set(), 0
    aggregates = {'arabic': {'arabic', 'quran_arabic'},
                  'translation': {'translation', 'quran_translation'},
                  'transliteration': {'transliteration'}, 'narration': {'narration'},
                  'commentary': {'commentary'}}
    for row in rows:
        classification = row[ACTIVE_CLASSIFICATION]
        if (classification['record_id'] != row['record_id'] or
                classification['source_wording_unchanged'] is not True or
                classification['separate_independent_final_evaluation'] != 'NOT_RUN'):
            raise ValueError('Source classification identity/history changed')
        components = {c['segment_id']: c for c in row['components']}
        roles = classification['component_roles']
        if (len(components) != len(row['components']) or
                {r['segment_id'] for r in roles} != set(components)):
            raise ValueError('Component/role coverage differs: ' + row['record_id'])
        for component in row['components']:
            if component['segment_id'] in segment_ids or not isinstance(component['text'], str):
                raise ValueError('Duplicate segment or invalid source text')
            segment_ids.add(component['segment_id'])
        for role in roles:
            component = components[role['segment_id']]
            if sha(component['text'].encode('utf-8')) != role['source_text_sha256']:
                raise ValueError('Source component hash changed: ' + component['segment_id'])
            candidate_count += role['preserved_prior_candidate'] is True
        for field, types in aggregates.items():
            value = JOIN.join(c['text'] for c in row['components'] if c['type'] in types) or None
            if value != row[field]:
                raise ValueError('Source aggregate differs from exact components: ' + row['record_id'])
        for annotation in classification['exact_source_subspan_annotations']:
            text = components[annotation['segment_id']]['text']
            start, end = annotation['start_codepoint'], annotation['end_codepoint']
            quote = annotation.get('text_verbatim', annotation.get('exact_source_quote'))
            if not 0 <= start < end <= len(text) or text[start:end] != quote:
                raise ValueError('Source subspan annotation changed: ' + row['record_id'])
        if row['isnad_as_printed'] is not None or row['original_hadith_collection_title_verified'] is not None:
            raise ValueError('Unexpected new chain/canonical verification in source')
    if len(segment_ids) != 1500 or candidate_count != 493:
        raise ValueError('Expected 1500 source components and 493 retained candidate components')


def component_language(component):
    if component['type'] in ('arabic', 'quran_arabic'):
        return 'ar'
    if component['type'] == 'commentary' and ARABIC_LETTERS.search(component['text']):
        return 'ar'
    return 'fil'


def display_role(component, role):
    """Plain display roles are distinct from historical approval/status strings."""
    if 'QURAN' in role or component['type'].startswith('quran_'):
        return 'Quran within source narration or practice context'
    if component['type'] == 'commentary':
        return 'Source instruction or commentary'
    if any(word in role for word in ('OTHER_SPEAKER', 'COMPANION', 'BEDOUIN', 'UNNAMED_LISTENER')):
        return 'Other speaker or narrator within hadith context'
    if any(word in role for word in ('EDITORIAL', 'COMPILER')):
        return 'Compiler wording within source context'
    if component['type'] == 'transliteration':
        return 'Source transliteration'
    if component['type'] == 'narration':
        return 'Source narration and dialogue'
    return 'Hadith, dhikr or narration context'


def assemble(components, roles):
    parts, sequence, offset = [], [], 0
    for component in components:
        if parts:
            offset += len(JOIN)
        text = component['text']
        sequence.append({'segment_id': component['segment_id'], 'source_type': component['type'],
            'source_text_sha256': sha(text.encode('utf-8')), 'pdf_page': component['pdf_page'],
            'printed_page': component.get('printed_page'), 'zone': component.get('zone'),
            'content_role': display_role(component, roles[component['segment_id']]['content_role']),
            'display_start_codepoint': offset, 'display_end_codepoint': offset + len(text)})
        parts.append(text)
        offset += len(text)
    return JOIN.join(parts) or None, sequence


def source_references(source):
    items = copy.deepcopy(source['references'])
    for reference in items:
        reference['source_citation'] = reference['reference_as_printed']
        reference['scope'] = 'printed_source_reference_shared_by_source_readings'
        reference['source_path'] = SOURCE_PDF
        reference['source_sha256'] = SOURCE_HASH
        page = reference.get('pdf_page')
        reference['url'] = SOURCE_URL + ('#page=' + str(page) if page else '')
    return items


def source_notes(source, language, selected_ids, roles):
    """Render actual notes and narrowly scoped annotations in existing panels."""
    result = [{'kind': 'context_annotation', 'not_source_wording': True,
        'text': ('Reading scope: this source occurrence preserves hadith, dhikr and narration '
                 'context. Quran recitation, other speakers and compiler wording retain '
                 'their distinct roles; the whole passage is not labelled direct Prophetic speech.')}]
    components = {c['segment_id']: c for c in source['components']}
    annotated_segments = {a['segment_id'] for a in source[ACTIVE_CLASSIFICATION]['exact_source_subspan_annotations']}
    for component in source['components']:
        if component_language(component) != language:
            continue
        kind = component['type']
        role = roles[component['segment_id']]['content_role']
        note = {'segment_id': component['segment_id'], 'pdf_page': component['pdf_page'],
                'printed_page': component.get('printed_page'), 'source_path': SOURCE_JSON,
                'source_url': SOURCE_URL + '#page=' + str(component['pdf_page']),
                'source_text_sha256': sha(component['text'].encode('utf-8'))}
        if kind in ('commentary', 'footnote'):
            result.append({**note, 'kind': 'source_' + kind, 'text': component['text'],
                           'included_in_body': component['segment_id'] in selected_ids,
                           'content_role': display_role(component, role)})
        if component['segment_id'] in selected_ids and component['segment_id'] not in annotated_segments:
            label = display_role(component, role)
            if label.startswith(('Quran', 'Other speaker', 'Compiler')) or kind == 'commentary':
                result.append({**note, 'kind': 'context_annotation', 'not_source_wording': True,
                               'content_role': label,
                               'text': label + ' (' + component['segment_id'] + '):\n' + component['text']})
    for annotation in source[ACTIVE_CLASSIFICATION]['exact_source_subspan_annotations']:
        component = components[annotation['segment_id']]
        if component_language(component) != language:
            continue
        quote = annotation.get('text_verbatim', annotation.get('exact_source_quote'))
        label = annotation['role'].replace('_', ' ').capitalize()
        result.append({'kind': 'context_annotation', 'not_source_wording': True,
            'segment_id': component['segment_id'], 'pdf_page': component['pdf_page'],
            'source_path': SOURCE_JSON, 'content_role': annotation['role'],
            'start_codepoint': annotation['start_codepoint'], 'end_codepoint': annotation['end_codepoint'],
            'exact_source_quote': quote,
            'text': label + ' (' + component['segment_id'] + '):\n' + quote})
    return result


def first_printed_number(source):
    for item in source['printed_item_numbers']:
        if isinstance(item, str) and item:
            return item
        if isinstance(item, dict):
            for key in ('printed_number_latin', 'printed_number_arabic'):
                if isinstance(item.get(key), str) and item[key]:
                    return item[key]
    return None


def make_record(source, index, book):
    decision = source[ACTIVE_CLASSIFICATION]
    if decision['record_partition'] != READER_PARTITION:
        raise ValueError('Only hadith/dhikr/context records may enter the reader')
    identity = occurrence_id(source['record_id'])
    pointer = '/records/' + str(index)
    roles = {r['segment_id']: r for r in decision['component_roles']}
    filipino = [c for c in source['components'] if c['type'] in FILIPINO_TYPES or
                (c['type'] == 'commentary' and c.get('zone') == 'body' and component_language(c) == 'fil')]
    arabic = [c for c in source['components'] if c['type'] in ('arabic', 'quran_arabic')]
    fil_text, fil_sequence = assemble(filipino, roles)
    ar_text, ar_sequence = assemble(arabic, roles)
    if not fil_text or ar_text != source['arabic']:
        raise ValueError('Missing source reading or altered original Arabic: ' + source['record_id'])
    refs = source_references(source)
    citation = JOIN.join(r['reference_as_printed'] for r in refs) or (
        'Hisnul Muslim · source record ' + source['record_id'] + ' · PDF page(s) ' +
        ', '.join(str(page) for page in source['pdf_pages']))
    credits = book['translation_book']
    provenance = {'origin': 'human_translator_credited', 'label': 'Human',
        'ai_translation': False, 'human_involvement': 'named_human_translator',
        'basis': 'The original source credits ' + credits['translator_as_printed'] + ' on PDF page 2.',
        'evidence_ids': [SOURCE_METADATA + '#/translation_identity'],
        'scope_note': 'Existing printed human Filipino translation and source transliteration; no new translation was generated.'}
    page = source['pdf_pages'][0] if source['pdf_pages'] else None
    source_descriptor = {'name': TITLE, 'title': TITLE, 'url': SOURCE_URL,
        'record_url': SOURCE_URL + ('#page=' + str(page) if page else ''),
        'original_source_id': source['book_id'], 'original_record_id': source['record_id'],
        'original_record_pointer': pointer, 'original_record_source_sha256': source['record_source_sha256'],
        'final_delivery_path': SOURCE_JSON, 'final_delivery_sha256': INPUT_HASH,
        'final_delivery_compression': 'gzip', 'final_delivery_hash_scope': 'uncompressed_original_bytes',
        'source_metadata_path': SOURCE_METADATA, 'source_metadata_sha256': METADATA_HASH,
        'source_component_ids': [c['segment_id'] for c in source['components']]}
    readings = []
    for language, text, sequence in (('fil', fil_text, fil_sequence), ('ar', ar_text, ar_sequence)):
        if not text:
            continue
        selected_ids = {item['segment_id'] for item in sequence}
        readings.append({'id': identity + ':' + language, 'language': language,
            'script': 'Arab' if language == 'ar' else 'Latn', 'text': text,
            'source': copy.deepcopy(source_descriptor), 'references': copy.deepcopy(refs),
            'citation': citation, 'comments': source_notes(source, language, selected_ids, roles),
            'translation_provenance': copy.deepcopy(provenance) if language == 'fil' else None,
            'scope': 'source_narration_dhikr_context', 'match_status': 'same_source_record',
            'source_component_ids': [item['segment_id'] for item in sequence]})
    names = source['narrator_attributions_as_printed'] or []
    printed_names = list(dict.fromkeys(n['name_as_printed'] for n in names if n.get('name_as_printed')))
    headings = list(dict.fromkeys(source['chapter_titles_as_printed'] +
                                 [c['text'] for c in source['components'] if c['type'] == 'heading']))
    number = first_printed_number(source)
    return {'id': identity, 'language': 'fil', 'source_language_code': 'fil',
        'book_key': 'hisn-al-muslim', 'edition': EDITION,
        'record_type': 'hadith_context', 'content_kind': 'hadith_dhikr_narration_context',
        'title': headings[0] if headings else ('Source item ' + number if number else 'Unnumbered source narration'),
        'text': {'arabic': ar_text, 'translation': fil_text}, 'language_versions': readings,
        'source': source_descriptor,
        'number': {'source_entry_id': source['record_id'], 'in_book': number, 'canonical': None,
                   'as_printed': copy.deepcopy(source['printed_item_numbers']), 'scope': 'source_local',
                   'numbering_system': 'Printed Hisnul Muslim item label and preserved source record ID; not canonical collection numbering'},
        'narrator': {'name': ' / '.join(printed_names) if printed_names else None,
                     'as_printed': copy.deepcopy(names), 'basis': 'Names explicitly recorded in the supplied source only; no external identity or chain supplied.'},
        'isnad': None,
        'translator': {'name': credits['translator_as_printed'], 'evidence': SOURCE_METADATA + '#/translation_identity',
                       'evidence_pdf_page': 2, 'corrector_as_printed': credits['corrector_as_printed']},
        'ai_translation': False, 'translation_provenance': provenance,
        'topic_tags': [], 'editorial_tags': ['source:' + SLUG, 'canonical_mapping:unverified',
            'arabic:' + ('source_supplied' if ar_text else 'not_supplied'), 'content:hadith_dhikr_context'],
        'source_headings': headings, 'commentary': {'arabic': None, 'translation': None},
        'footnotes': [],
        'references': {'items': refs, 'canonical_mapping_status': 'unverified',
                       'scope_note': 'Exact references printed in this PDF; numbers and grades are source claims, not newly verified canonical mappings.'},
        'grading': {'grade': None, 'grader': None, 'claims_as_printed': copy.deepcopy(source['grading_claims_as_printed']),
                    'basis': 'Printed grade claims are retained with their source text; no new authenticity grade is assigned.'},
        'page': {'pdf': copy.deepcopy(source['pdf_pages']), 'printed': copy.deepcopy(source['printed_pages']), 'sheet': None, 'row': None},
        'source_locator': {'path': SOURCE_JSON, 'compression': 'gzip', 'uncompressed_sha256': INPUT_HASH,
            'json_pointer': pointer, 'original_record_id': source['record_id'],
            'source_record_sha256': source['record_source_sha256'],
            'source_pdf_path': SOURCE_PDF, 'source_pdf_sha256': SOURCE_HASH,
            'source_component_ids': [c['segment_id'] for c in source['components']],
            'source_components_json_pointer': pointer + '/components',
            'source_footnotes_json_pointer': pointer + '/footnotes',
            'classification_path': CLASSIFICATIONS,
            'historical_classification_json_pointer': pointer + '/' + ACTIVE_CLASSIFICATION,
            'historical_review_json_pointer': pointer + '/review', 'blocker_index_path': BLOCKER_INDEX,
            'classification_qualifications': {'render_as_direct_prophetic_quote': False,
                'context_only_source_form': decision['context_only_source_form'],
                'exact_annotations_json_pointer': pointer + '/' + ACTIVE_CLASSIFICATION + '/exact_source_subspan_annotations'},
            'display_sequences': {'fil': fil_sequence, 'ar': ar_sequence}, 'join_separator': JOIN,
            'display_joins': {'kind': 'double_newline_between_exact_source_components', 'separator': JOIN},
            'offset_basis': 'Zero-based end-exclusive Unicode code points in the displayed reading',
            'language_text_sha256': {'fil': sha(fil_text.encode('utf-8')), 'ar': sha(ar_text.encode('utf-8')) if ar_text else None},
            'original_aggregate_sha256': {field: sha(source[field].encode('utf-8')) if source[field] else None
                                        for field in ('arabic', 'translation', 'transliteration', 'narration', 'commentary')},
            'parent_record_ids_preserved': copy.deepcopy(source['parent_record_ids'])},
        'review': {'status': 'source_imported', 'release_status': 'source_imported',
            'independent_pro_qc': 'NOT_RUN', 'release_eligible': False, 'certified_release_eligible': False,
            'issues': ['Owner requested active source import into the bank and HTML.',
                       'Source text, metadata and local exceptions remain documented in the preserved source audits.',
                       'No new independent final evaluation, canonical identity approval or authenticity grade is asserted.'],
            'historical_review_path': SOURCE_JSON, 'historical_review_pointer': pointer + '/review'},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                   'source_notice_preserved_in': SOURCE_PDF,
                   'historical_source_rights_path': SOURCE_JSON, 'historical_source_rights_pointer': pointer + '/reuse_rights_status'},
        'extraction': {'method': 'exact_saved_source_components', 'ocr_used': None, 'is_excerpt': None,
            'new_ocr_performed': False, 'new_pdf_pages_visually_reviewed': 0,
            'source_text_changed': False, 'source_extraction_history': SOURCE_JSON,
            'source_extraction_history_pointer': '/book/text_method'},
        'related_versions': []}


def partition_wrapper(source, index):
    return {'id': occurrence_id(source['record_id']), 'original_record_id': source['record_id'],
        'classification': source[ACTIVE_CLASSIFICATION]['record_partition'],
        'classification_decision': copy.deepcopy(source[ACTIVE_CLASSIFICATION]),
        'original_source_record': copy.deepcopy(source), 'visible_in_hadith_html': False,
        'source_locator': {'path': SOURCE_JSON, 'compression': 'gzip', 'uncompressed_sha256': INPUT_HASH,
                           'json_pointer': '/records/' + str(index)}}


def run(root):
    root = Path(root).resolve()
    raw_pdf = (root / SOURCE_PDF).read_bytes()
    if len(raw_pdf) != SOURCE_SIZE or sha(raw_pdf) != SOURCE_HASH:
        raise ValueError('Original PDF bytes changed')
    supporting = verify_preservation(root)
    source = read_checked(root / SOURCE_JSON, INPUT_HASH)
    metadata = read_checked(root / SOURCE_METADATA, METADATA_HASH)
    if metadata['source_pdf_sha256'] != SOURCE_HASH:
        raise ValueError('Metadata identifies a different PDF')
    validate_source(source)
    records, partitions = [], {key: [] for key in EXPECTED_COUNTS if key != READER_PARTITION}
    for index, row in enumerate(source['records']):
        route = row[ACTIVE_CLASSIFICATION]['record_partition']
        if route == READER_PARTITION:
            records.append(make_record(row, index, source['book']))
        else:
            partitions[route].append(partition_wrapper(row, index))
    write_rows(root / PREFIX / 'records.jsonl', records)
    non_hadith = [partition_wrapper(row, index) for index, row in enumerate(source['records'])
                  if row[ACTIVE_CLASSIFICATION]['record_partition'] in ('independent_non_prophetic', 'quran_and_author_only')]
    write_rows(root / PARTITION_PATHS['non_hadith'], non_hadith)
    for route, rows in partitions.items():
        write_rows(root / PARTITION_PATHS[route], rows)
    canonical_readback = [json.loads(line) for line in (root / PREFIX / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
    if canonical_readback != records:
        raise ValueError('Canonical JSONL round trip changed values')
    for route, rows in partitions.items():
        readback = [json.loads(line) for line in (root / PARTITION_PATHS[route]).read_text(encoding='utf-8').splitlines()]
        if readback != rows:
            raise ValueError('Partition JSONL round trip changed source values')
    all_ids = [r['id'] for r in records] + [r['id'] for rows in partitions.values() for r in rows]
    if len(all_ids) != 323 or len(set(all_ids)) != 323:
        raise ValueError('Routing is not disjoint and exhaustive')
    audit_path = PREFIX + 'integration-audit.json'
    output_paths = [PREFIX + 'records.jsonl', *PARTITION_PATHS.values()]
    audit = {'schema': 'filipino-hisn-source-integration-v1',
        'publication_decision': SOURCE_IMPORT_DECISION, 'active_status': 'source_imported',
        'owner_instructions': OWNER_INSTRUCTIONS, 'source_pdf': descriptor(root, SOURCE_PDF),
        'source_json': {'path': SOURCE_JSON, 'compression': 'gzip', 'uncompressed_sha256': INPUT_HASH},
        'source_metadata': descriptor(root, SOURCE_METADATA), 'preservation_manifest': descriptor(root, PRESERVATION_MANIFEST),
        'provenance': 'Reconstructed from the exact v1 checkpoint and supplied transcript; not recovered byte-identical original v2.',
        'routing_counts': EXPECTED_COUNTS, 'reader_count': len(records), 'separate_non_hadith_count': len(non_hadith),
        'source_record_count': 323, 'source_component_count': 1500, 'prior_prophetic_candidate_components_preserved': 493,
        'original_arabic_present': sum(r['text']['arabic'] is not None for r in records),
        'original_arabic_missing': sum(r['text']['arabic'] is None for r in records),
        'source_wording_changes': 0, 'new_pdf_pages_visually_reviewed': 0, 'new_ocr_performed': False,
        'independent_final_evaluation': 'NOT_RUN', 'certified_release_eligible': False,
        'canonical_mapping_added': False, 'external_counterpart_added': False, 'new_translation_generated': False,
        'historical_source_fidelity': 'PARTIAL', 'historical_metadata': 'PARTIAL',
        'historical_bank_status': 'FAIL/HOLD', 'historical_status_is_not_current_visibility': True,
        'source_record_ids_by_partition': {kind: [r['record_id'] for r in source['records']
                                               if r[ACTIVE_CLASSIFICATION]['record_partition'] == kind]
                                           for kind in EXPECTED_COUNTS},
        'projection_contract': {'ordered_components': True, 'join_separator': JOIN,
            'filipino_component_types': sorted(FILIPINO_TYPES),
            'filipino_inline_commentary': 'Non-Arabic commentary in body zone remains ordered and separately labelled in notes.',
            'arabic_aggregate_unchanged': True, 'footnote_array_aliases_not_duplicated': True,
            'printed_references_used_verbatim': True, 'occurrence_id_rule': SLUG + ':<original record_id>'},
        'validation': {'input_hash_binding': True, 'source_component_hash_binding': True,
            '493_prior_candidate_components_preserved': True, 'routing_disjoint_exhaustive': True,
            'canonical_and_partition_jsonl_round_trip': True, 'original_aggregate_consistency': True,
            'exact_subspan_annotation_consistency': True},
        'outputs': [descriptor(root, path) for path in output_paths]}
    write_json(root / audit_path, audit)
    register(root, PREFIX.rstrip('/'), 'fil', 'hisn-al-muslim', EDITION, TITLE,
             'records.jsonl', 'FIL-HISN-PRIVATE.pdf', source_url=SOURCE_URL,
             source_id=SLUG, replace=(root / PREFIX / 'manifest.json').exists())
    manifest_path = root / PREFIX / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['source'].update({'title_fil': 'Hisnul Muslim', 'title_en': 'Hisn al-Muslim',
        'subtitle_as_printed': 'KUTANG-TANGGULAN NG MUSLIM', 'original_filename': 'FIL-HISN-PRIVATE.pdf',
        'pdf_pages': 276, 'catalog_page_count_as_printed': 280,
        'metadata_path': SOURCE_METADATA, 'metadata_sha256': METADATA_HASH,
        'edition_as_printed': source['book']['translation_book']['edition_as_printed'],
        'edition_publication_year': None, 'translation_credits': copy.deepcopy(metadata['translation_identity'])})
    manifest['publication'] = {'authorized': True, 'decision': SOURCE_IMPORT_DECISION,
        'decision_date_japan': '2026-11-12', 'owner_instruction': OWNER_INSTRUCTIONS[-1],
        'owner_instructions': OWNER_INSTRUCTIONS, 'visibility': 'public', 'active_status': 'source_imported',
        'scope': 'Exact reconstructed delivery and original PDF; 298 hadith/dhikr/narration-context source occurrences in active HTML; 14 independent, 6 Quran-author and 5 unresolved records retained separately.',
        'independent_qc_asserted': False, 'rights_clearance_asserted': False, 'certified_release_eligible': False,
        'historical_review_audit': audit_path}
    manifest['counterpart_policy'] = {'mode': 'disabled', 'reason': COUNTERPART_REASON}
    manifest['supporting_files'] = supporting + [descriptor(root, audit_path)]
    manifest['source_partitions'] = {'original_records': 323, 'reader_hadith_context_records': len(records),
        'non_hadith': {'count': len(non_hadith), 'path': PARTITION_PATHS['non_hadith'], 'visible_in_hadith_html': False},
        **{route: {'count': len(rows), 'path': PARTITION_PATHS[route], 'visible_in_hadith_html': False}
           for route, rows in partitions.items()},
        'classification_path': CLASSIFICATIONS, 'blocker_index_path': BLOCKER_INDEX}
    manifest['preserved_delivery'] = {'path': IMPORT, 'source_json_path': SOURCE_JSON,
        'source_json_uncompressed_sha256': INPUT_HASH, 'original_expanded_bytes_unchanged': True,
        'preservation_manifest': PRESERVATION_MANIFEST, 'source_component_count': 1500,
        'prior_prophetic_candidate_components': 493, 'candidate_enrichment_accepted': False,
        'recovered_original_v2': False}
    write_json(manifest_path, manifest)
    return {'material': SLUG, 'records': len(records), 'partitions': {k: len(v) for k, v in partitions.items()},
            'manifest': PREFIX + 'manifest.json', 'integration_audit': audit_path,
            'publication_decision': SOURCE_IMPORT_DECISION, 'active_status': 'source_imported',
            'source_wording_changed': False, 'independent_final_evaluation': 'NOT_RUN'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        result = run(args.root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Filipino Hisn import failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    main()
