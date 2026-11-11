#!/usr/bin/env python3
"""Discover explicitly registered public material without changing source records.

Publication authorization is an owner decision. It is never a claim of source
fidelity, independent review, licensing clearance, or narrational authenticity.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from collections import Counter

from build_reader import local, parse_json, valid_hash, validate_record
from build_bank_views import SCHEMA, canonical, digest_file
from current_provenance import apply_material_policy, apply_policy, classification, decision_for, load_policy
from review_display_policy import extraction_metadata


SCHEMA_NAME = 'hadith-bank-material-v1'
DECISION = 'owner_requested_public_pending_review'
SOURCE_IMPORT_DECISION = 'owner_requested_public_source_import'
PUBLICATION_DECISIONS = (DECISION, SOURCE_IMPORT_DECISION)
COMPONENT = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\Z')
LANGUAGE = re.compile(r'[A-Za-z][A-Za-z0-9-]*\Z')
BOOK_DISPLAY_DECISION = 'owner_requested_no_qc_tags_for_published_book'
BOOK_DISPLAY_SOURCES = {
    'zh-cn-ibn-majah-yu-2013': 'e3bc24bcee435894fc3826622839dd819f8c79eb83af5252f5389831fa76b383',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_file(root, relative, expected):
    target = local(root, relative)
    require(target.is_file(), 'Missing material file: ' + relative)
    expected = valid_hash(expected, relative + '.sha256')
    require(digest_file(target) == expected, 'Material checksum mismatch: ' + relative)
    return target


def read_rows(path):
    if path.suffix == '.jsonl':
        rows = []
        with path.open(encoding='utf-8') as stream:
            for number, line in enumerate(stream, 1):
                require(bool(line.strip()), 'Blank material JSONL line: ' + str(number))
                rows.append(parse_json(line))
    else:
        require(path.suffix == '.json', 'Records must be .json or .jsonl')
        rows = parse_json(path.read_text(encoding='utf-8'))
    require(isinstance(rows, list) and bool(rows), 'Material records must be a nonempty JSON array or JSONL stream')
    require(all(isinstance(row, dict) for row in rows), 'Every material record must be an object')
    return rows


def publication(manifest, relative):
    decision = manifest.get('publication')
    require(isinstance(decision, dict) and decision.get('authorized') is True,
            'Material needs explicit publication.authorized=true: ' + relative)
    require(decision.get('decision') in PUBLICATION_DECISIONS, 'Unsupported publication decision: ' + relative)
    date = decision.get('decision_date_japan')
    require(isinstance(date, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', date), 'Publication decision date must be YYYY-MM-DD')
    datetime.date.fromisoformat(date)
    status = 'published_pending_review' if decision['decision'] == DECISION else 'published_source_import'
    return {'visibility': 'public', 'status': status, 'authorized': True,
            'decision': decision['decision'], 'decision_date_japan': date, 'manifest_path': relative,
            'independent_qc_asserted': False, 'rights_clearance_asserted': False}


def with_publication(record, authorization):
    record['publication'] = copy.deepcopy(authorization)
    record['publication']['historical_release_status'] = record['review'].get('release_status')
    return record


def preserve_translation_declarations(projected, row, material):
    """Keep accepted attribution evidence available after normalization.

    Manifest declarations and canonical occurrence declarations stay separate
    so conflicting source assertions are detected instead of overwritten.
    """
    if 'source_declaration' in row:
        projected['source_declaration'] = copy.deepcopy(row['source_declaration'])
    source = projected['source']
    descriptor = material.get('source_descriptor') or {}
    original_source = row.get('source') or {}
    for key in ('translation_declaration', 'source_declaration'):
        if key in descriptor:
            source[key] = copy.deepcopy(descriptor[key])
        if key in original_source:
            source.setdefault('original_metadata', {})[key] = copy.deepcopy(original_source[key])
    return projected


def display_policy_for(manifest, authorization, relative):
    policy = manifest.get('display_policy')
    if policy is None:
        return None
    require(isinstance(policy, dict) and policy.get('qc_tags') is False and
            isinstance(policy.get('basis'), str) and bool(policy['basis'].strip()),
            'Invalid explicit display policy: ' + relative)
    source = manifest.get('source') or {}
    require(isinstance(source, dict), 'Display policy requires a source descriptor: ' + relative)
    if policy.get('decision') == 'owner_requested_no_qc_tags_for_non_ocr':
        require(manifest.get('adapter') == 'records-v1' and source.get('format') == 'docx' and
                authorization['decision'] == SOURCE_IMPORT_DECISION,
                'No-QC display policy requires an authorized direct DOCX source import')
    elif policy.get('decision') == BOOK_DISPLAY_DECISION:
        require(authorization.get('authorized') is True and authorization.get('visibility') == 'public' and
                authorization.get('decision') in PUBLICATION_DECISIONS and
                manifest.get('adapter') == 'records-v1' and source.get('format') == 'pdf' and
                manifest.get('id') in BOOK_DISPLAY_SOURCES and
                manifest.get('source_id') == manifest.get('id') and
                source.get('sha256') == BOOK_DISPLAY_SOURCES[manifest['id']] and
                manifest.get('language') == 'zh-CN' and manifest.get('book') == 'ibn-majah',
                'Published-book display decision applies only to its identified source PDF')
    else:
        raise ValueError('Unsupported explicit display decision: ' + relative)
    return copy.deepcopy(policy)




def normalized_projection(row, material, position):
    require(isinstance(row.get('id'), str) and bool(row['id'].strip()), 'Every material occurrence needs a stable id')
    text = row.get('text')
    require(isinstance(text, dict) and {'arabic', 'translation'} <= set(text),
            'Record text requires explicit arabic and translation fields (string or null): ' + row['id'])
    require(all(text[k] is None or isinstance(text[k], str) for k in ('arabic', 'translation')),
            'Record text must be a string or null: ' + row['id'])
    for key, expected in (('language', material['language']), ('book_key', material['book_key']), ('edition', material['edition'])):
        require(key not in row or row[key] == expected, 'Record/material identity mismatch: ' + key)
    for key in ('source', 'translator', 'narrator', 'number', 'page', 'review', 'commentary', 'references', 'grading', 'rights', 'extraction'):
        require(key not in row or isinstance(row[key], dict), 'Record ' + key + ' must be an object')
    extraction = row.get('extraction', {})
    require(extraction.get('ocr_used') is None or type(extraction.get('ocr_used')) is bool,
            'extraction.ocr_used must be true, false, or null')
    require(extraction.get('method') is None or isinstance(extraction.get('method'), str),
            'extraction.method must be text or null')
    require(extraction.get('is_excerpt') is None or type(extraction.get('is_excerpt')) is bool,
            'extraction.is_excerpt must be true, false, or null')
    for key in ('footnotes', 'topic_tags', 'source_headings', 'related_versions'):
        require(key not in row or isinstance(row[key], list), 'Record ' + key + ' must be an array')
    ai = row.get('ai_translation', 'unknown')
    require(ai is True or ai is False or ai == 'unknown', 'ai_translation must be true, false, or unknown')
    translator = copy.deepcopy(row.get('translator', {'name': None, 'evidence': None}))
    origin = copy.deepcopy(row.get('translation_provenance'))
    if origin is None:
        origin = {'origin': 'unknown', 'label': 'Translation origin not established',
                  'basis': 'No source-specific translation provenance supplied',
                  'human_involvement': 'not_established', 'ai_translation': ai, 'evidence_ids': []}
    require(isinstance(origin, dict), 'translation_provenance must be an object')
    require(origin.get('ai_translation', ai) == ai, 'Conflicting AI translation flags')
    origin.setdefault('ai_translation', ai)
    origin.setdefault('origin', 'unknown')
    origin.setdefault('label', 'Unknown' if origin['origin'] in ('unknown', 'legacy_source_history') else 'Source attribution supplied')
    origin.setdefault('basis', (origin.get('current_policy') or {}).get('basis', 'Original source attribution metadata; no additional evidence inferred'))
    origin.setdefault('human_involvement', 'not_established')
    origin.setdefault('evidence_ids', [])
    origin.setdefault('scope_note', 'Original source metadata is preserved; current translation classification follows the recorded provenance evidence and owner policy.')
    # A standalone registered material need not have a bank policy file. Source
    # paths stay explicit; a bank decision carries its own current_policy path.
    origin.setdefault('policy_path', None)
    review = copy.deepcopy(row.get('review', {}))
    review.setdefault('status', 'source_review_pending')
    review.setdefault('issues', [])
    review.setdefault('independent_pro_qc', 'pending')
    review.setdefault('release_status', 'source_candidate')
    review.setdefault('release_eligible', False)
    # A publication manifest never grants independent certification.
    review.setdefault('certified_release_eligible', False)
    descriptor = material['source_descriptor']
    original_source = copy.deepcopy(row.get('source', {}))
    locator = {'path': material['canonical_records_path']}
    if material['canonical_records_path'].endswith('.jsonl'):
        locator['line'] = position + 1
    else:
        locator['json_pointer'] = '/' + str(position)
    source = {'name': descriptor['name'], 'work_title': original_source.get('title', descriptor['name']),
              'url': original_source.get('url', descriptor.get('url')), 'record_url': original_source.get('record_url'),
              'original_file': material['source_file'], 'sha256': material['source_sha256'],
              'record_locator': locator, 'format': descriptor.get('format', 'unknown'),
              'original_metadata': original_source}
    title = row.get('title')
    if isinstance(title, dict):
        title = title.get('translation')
    require(title is None or isinstance(title, str), 'Record title must be text or null')
    tags = row.get('editorial_tags', [])
    tags = tags.get('values', []) if isinstance(tags, dict) else tags
    require(isinstance(tags, list), 'editorial_tags must be an array or values object')
    result = {
        'schema_version': SCHEMA, 'id': row['id'], 'language': material['language'],
        'source_language_code': row.get('source_language_code', material['language']),
        'book_key': material['book_key'], 'edition': material['edition'], 'source_id': material['dataset_id'],
        'provider_entry_id': row.get('number', {}).get('source_entry_id'), 'title': title,
        'text_arabic': text['arabic'], 'text_translation': text['translation'],
        'number': copy.deepcopy(row.get('number', {'source_entry_id': None, 'in_book': None, 'canonical': None})),
        'narrator': copy.deepcopy(row.get('narrator', {'name': None})), 'source': source,
        'translator': translator, 'translation_provenance': origin,
        'extraction': {**extraction_metadata(row),
                       **({'is_excerpt': extraction['is_excerpt']} if type(extraction.get('is_excerpt')) is bool else {})},
        'topic_tags': copy.deepcopy(row.get('topic_tags', [])), 'editorial_tags': copy.deepcopy(tags),
        'source_headings': copy.deepcopy(row.get('source_headings', [])), 'review': review,
        'commentary': copy.deepcopy(row.get('commentary', {'arabic': None, 'translation': None})),
        'benefits': copy.deepcopy(row.get('benefits')), 'footnotes': copy.deepcopy(row.get('footnotes', [])),
        'references': copy.deepcopy(row.get('references', {})), 'grading': copy.deepcopy(row.get('grading', {})),
        'page': copy.deepcopy(row.get('page', {'pdf': [], 'printed': [], 'sheet': None, 'row': None})),
        'related_versions': copy.deepcopy(row.get('related_versions', [])),
        'rights': copy.deepcopy(row.get('rights', {'status': 'not_assessed_for_publication', 'reuse_basis': None})),
        'record_type': row.get('record_type'), 'content_kind': row.get('content_kind'),
        'isnad': copy.deepcopy(row.get('isnad')), 'ai_translation': ai,
        'canonical_record_sha256': hashlib.sha256(canonical(row)).hexdigest(),
    }
    with_publication(result, material['publication'])
    if material.get('display_policy') is not None:
        result['display_policy'] = copy.deepcopy(material['display_policy'])
    for key in ('source_structure_tags', 'source_locator', 'source_defects'):
        if key in row:
            result[key] = copy.deepcopy(row[key])
    if extraction.get('method') == 'direct_ooxml' and extraction.get('ocr_used') is False:
        # Keep the native DOCX extraction details without replacing the common
        # evidence-backed OCR projection used by existing registered sources.
        result['extraction'] = {**copy.deepcopy(extraction), **result['extraction']}
    preserve_translation_declarations(result, row, material)
    apply_material_policy(result, material)
    validate_record(result, row['id'])
    return result


def project_for_material(row, material, position):
    if material.get('adapter') == 'records-v1':
        return normalized_projection(row, material, position)
    require(material.get('adapter') == 'pdf-intake-package-v1', 'Unsupported material adapter')
    from integrate_private_intakes import project
    prefix = material['intake_root']
    collection = {'book': material['book_key'], 'edition': material['edition'],
                  'source_id': material['dataset_id'],
                  'records_path': str(PurePosixPath(material['canonical_records_path']).relative_to(prefix)),
                  'source_metadata_path': str(PurePosixPath(material['source_metadata_path']).relative_to(prefix))}
    projected = project(row, collection, position, prefix)
    projected['extraction'] = extraction_metadata(row)
    preserve_translation_declarations(projected, row, material)
    return apply_material_policy(with_publication(projected, material['publication']), material)


def load_public_materials(root, validate_attachment_roots=True):
    """Return verified material descriptors, projections, and allowed source files."""
    root = Path(root).resolve()
    provenance_policy = load_policy(root)
    registry = root / 'materials'
    require(not registry.is_symlink(), 'Material registry must not be a symlink')
    if registry.exists():
        require(registry.is_dir(), 'materials must be a directory')
        for child in registry.iterdir():
            require(not child.is_symlink(), 'Material folders must not be symlinks')
            if child.is_dir():
                require((child / 'manifest.json').is_file(), 'Material folder needs manifest.json: ' + child.name)
            else:
                require(child.name in ('README.md', '.gitkeep'), 'Place material files inside materials/<slug> with manifest.json')
    manifests = sorted(registry.glob('*/manifest.json')) if registry.exists() else []
    result = {'materials': [], 'groups': [], 'manifests': [], 'authorized_files': {}, 'package_roots': []}
    ids, source_ids, occurrence_ids, locations, editions = set(), set(), set(), set(), set()
    for path in manifests:
        relative = path.relative_to(root).as_posix()
        path = local(root, relative)
        require(path.is_file(), 'Missing material manifest')
        manifest = parse_json(path.read_text(encoding='utf-8'))
        require(isinstance(manifest, dict) and manifest.get('schema') == SCHEMA_NAME, 'Invalid material manifest: ' + relative)
        identifier = manifest.get('id')
        require(isinstance(identifier, str) and COMPONENT.fullmatch(identifier), 'Unsafe material id')
        require(identifier not in ids, 'Duplicate material id: ' + identifier)
        ids.add(identifier)
        authorization = publication(manifest, relative)
        adapter = manifest.get('adapter')
        require(adapter in ('records-v1', 'pdf-intake-package-v1'), 'Unsupported material adapter: ' + str(adapter))
        display_policy = display_policy_for(manifest, authorization, relative)
        result['manifests'].append({'path': relative, 'sha256': digest_file(path), 'id': identifier, 'adapter': adapter,
                                    'publication': authorization})
        collection_rows = []
        if adapter == 'pdf-intake-package-v1':
            from integrate_private_intakes import describe_package, verify_package
            prefix = manifest.get('package_root')
            require(isinstance(prefix, str) and re.fullmatch(r'attachments/[A-Za-z0-9][A-Za-z0-9._-]*', prefix),
                    'PDF package_root must identify one attachments subdirectory')
            require(prefix not in result['package_roots'], 'Duplicate registered package root')
            package = local(root, prefix)
            require(package.is_dir(), 'Missing package root: ' + prefix)
            for file in verify_package(package):
                result['authorized_files'][prefix + '/' + file['path']] = file['sha256']
            result['package_roots'].append(prefix)
            package_info = describe_package(package)
            for collection in package_info['collections']:
                canonical_path = prefix + '/' + collection['records_path']
                records_path = checked_file(root, canonical_path, collection['records_sha256'])
                rows = read_rows(records_path)
                require(len(rows) == collection['count'], 'Package canonical count mismatch')
                material = {'dataset_id': collection['source_id'], 'language': collection['language'],
                            'book_key': collection['book'], 'edition': collection['edition'],
                            'count': len(rows), 'release_status': collection['release_status'],
                            'source_file': prefix + '/' + collection['source_file'],
                            'source_sha256': collection['source_sha256'], 'canonical_records_path': canonical_path,
                            'canonical_records_sha256': collection['records_sha256'],
                            'source_metadata_path': prefix + '/' + collection['source_metadata_path'],
                            'intake_root': prefix, 'source_pdf_pages': collection.get('pdf_pages')}
                collection_rows.append((material, rows))
        else:
            for key in ('language', 'book', 'edition', 'source_id'):
                require(isinstance(manifest.get(key), str) and bool(manifest[key]), 'Material manifest requires ' + key)
            require(LANGUAGE.fullmatch(manifest['language']), 'Invalid language code')
            require(COMPONENT.fullmatch(manifest['book']) and COMPONENT.fullmatch(manifest['edition']), 'Unsafe book or edition key')
            records, source = manifest.get('records'), manifest.get('source')
            require(isinstance(records, dict) and isinstance(source, dict), 'Material requires records and source descriptors')
            require(isinstance(source.get('name'), str) and bool(source['name']), 'Material source name is required')
            own_prefix = path.parent.relative_to(root).as_posix() + '/'
            require(all(isinstance(descriptor.get('path'), str) and descriptor['path'].startswith(own_prefix)
                        for descriptor in (records, source)),
                    'Material records and source must stay inside their own materials/<slug> directory')
            records_path = checked_file(root, records.get('path'), records.get('sha256'))
            checked_file(root, source.get('path'), source.get('sha256'))
            rows = read_rows(records_path)
            require(type(records.get('count')) is int and len(rows) == records['count'], 'Material record count mismatch')
            result['authorized_files'][source['path']] = source['sha256']
            result['authorized_files'][records['path']] = records['sha256']
            material = {'dataset_id': manifest['source_id'], 'language': manifest['language'],
                        'book_key': manifest['book'], 'edition': manifest['edition'], 'count': len(rows),
                        'release_status': ('source_imported' if authorization['decision'] == SOURCE_IMPORT_DECISION
                                           else 'source_review_pending'), 'source_file': source['path'], 'source_sha256': source['sha256'],
                        'canonical_records_path': records['path'], 'canonical_records_sha256': records['sha256'],
                        'source_descriptor': copy.deepcopy(source)}
            collection_rows.append((material, rows))
        for material, rows in collection_rows:
            require(material['dataset_id'] not in source_ids, 'Duplicate registered source id: ' + material['dataset_id'])
            require(material['canonical_records_path'] not in locations, 'Duplicate registered canonical records path')
            edition_key = (material['language'], material['book_key'], material['edition'])
            require(edition_key not in editions, 'Duplicate language/book/edition registration')
            editions.add(edition_key)
            source_ids.add(material['dataset_id']); locations.add(material['canonical_records_path'])
            require(LANGUAGE.fullmatch(material['language']) and COMPONENT.fullmatch(material['book_key']) and COMPONENT.fullmatch(material['edition']),
                    'Unsafe material language/book/edition path component')
            material.update({'adapter': adapter, 'manifest_path': relative, 'publication': authorization,
                             'available_locally': True, 'public_text_published': True})
            if display_policy is not None:
                material['display_policy'] = copy.deepcopy(display_policy)
            projected = [project_for_material(row, material, position) for position, row in enumerate(rows)]
            for record in projected:
                apply_policy(record, provenance_policy, registered_material=True)
                require(record['id'] not in occurrence_ids, 'Duplicate material occurrence id: ' + record['id'])
                occurrence_ids.add(record['id'])
                require(record['source']['original_file'] == material['source_file'] and
                        record['source']['sha256'] == material['source_sha256'], 'Canonical source differs from material declaration')
                checked_file(root, record['source']['original_file'], record['source']['sha256']) if record is projected[0] else None
            material['source_name'] = projected[0]['source']['name']
            decisions = [record['translation_provenance'].get('current_policy') for record in projected]
            decision = decisions[0]
            material['translation_provenance'] = copy.deepcopy(projected[0]['translation_provenance'])
            if not all(item == decision for item in decisions):
                # A source can explicitly identify an AI-translated passage in
                # an otherwise Human-default book. Keep occurrence decisions
                # separate; the validator reconstructs each exact projection.
                descriptor = {key: value for key, value in material.items() if key != 'translation_provenance'}
                decision = decision_for(descriptor, provenance_policy, registered_material=True) or decision
                material['current_translation_policy_overrides'] = {
                    record['id']: copy.deepcopy(item)
                    for record, item in zip(projected, decisions) if item != decision}
                material['current_translation_origin_counts'] = dict(sorted(Counter(
                    classification(record) for record in projected).items()))
                material['translation_provenance']['classification_scope'] = 'dataset_default_with_record_overrides'
                if decision is None:
                    material['translation_provenance'].pop('current_policy', None)
                else:
                    material['translation_provenance']['current_policy'] = copy.deepcopy(decision)
            if decision is not None:
                material['current_translation_policy'] = copy.deepcopy(decision)
            result['materials'].append(material); result['groups'].append(projected)
    if validate_attachment_roots and (root / 'attachments').exists():
        actual = set()
        for path in (root / 'attachments').iterdir():
            require(path.is_dir() and not path.is_symlink(), 'Unregistered file or symlink in attachments')
            actual.add(path.relative_to(root).as_posix())
        require(actual == set(result['package_roots']), 'Unregistered attachment package roots: ' + str(sorted(actual - set(result['package_roots']))))
    return result
