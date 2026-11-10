#!/usr/bin/env python3
"""Register a lossless PDF/XLSX extraction package as a PRIVATE Hadith Bank intake.

This adapter does not translate, OCR, infer canonical identities, or authorize
publication. All original extraction files remain byte-identical evidence.
"""
import argparse
import collections
import copy
import hashlib
import json
import pathlib
import re
import shutil
import sys

SCHEMA = 'hadith-bank-attachment-candidate-v1'
EVIDENCE = pathlib.PurePosixPath('evidence/extraction-package')
LANGUAGES = {
    'ja': ('ja', 'Japanese'), 'vi': ('vi', 'Vietnamese'),
    'zh': ('zh-CN', 'Chinese'), 'uz': ('uz', 'Uzbek'),
    'hi': ('hi', 'Hindi'), 'ur': ('ur', 'Urdu'),
    'bn': ('bn', 'Bengali'), 'pt': ('pt', 'Portuguese'),
}
HEADINGS = ('division', 'part', 'volume', 'chapter', 'section', 'subsection')


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8', newline='\n')


def local(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Invalid local locator')
    p = pathlib.PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or ':' in p.parts[0]:
        raise ValueError('Unsafe local locator: ' + relative)
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Escaping local locator: ' + relative)
    return target


def verify_source_package(root):
    manifest = root / 'checksums.sha256'
    expected = set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        digest, relative = line.split('  ', 1)
        if not re.fullmatch('[0-9a-f]{64}', digest) or relative in expected:
            raise ValueError('Invalid or duplicate source manifest entry')
        path = local(root, relative)
        if not path.is_file() or file_sha(path) != digest:
            raise ValueError('Source integrity failure: ' + relative)
        expected.add(relative)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != expected | {'checksums.sha256'}:
        raise ValueError('Source files differ from complete checksum manifest')
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Source package must not contain symlinks')
    return file_sha(manifest), len(expected)


def evidence_path(relative):
    return (EVIDENCE / relative).as_posix()


def source_group(record, dataset):
    if dataset['format'] == 'xlsx':
        return {'id': 'hadeethenc:' + dataset['source_sha256'] + ':row:' +
                str(record['page']['row']),
                'basis': 'same exact spreadsheet source row; not canonical identity'}
    relations = record.get('relations') or {}
    if isinstance(relations, dict) and relations.get('numbered_occurrence_id'):
        return {'id': relations['numbered_occurrence_id'],
                'basis': 'numbered source occurrence retained by extraction'}
    if record.get('source_occurrence_id'):
        return {'id': record['source_occurrence_id'],
                'basis': 'source occurrence retained by extraction'}
    return {'id': record['id'], 'basis': 'individual extracted source occurrence'}


def structure_tags(record):
    tags = []
    hierarchy = []
    for field in HEADINGS:
        value = record['book'].get(field)
        if not isinstance(value, str) or not value:
            continue
        hierarchy.append({'field': field, 'value_verbatim': value})
        tags.append({
            'tag_id': 'structure:' + record['source']['sha256'][:16] + ':' +
                      sha(canonical(hierarchy))[:20],
            'origin': 'source_book_structure',
            'language': record['language'],
            'field': field, 'value_verbatim': value,
            'source_id': record['source']['source_id'],
            'hierarchy_verbatim': copy.deepcopy(hierarchy),
            'evidence': {
                'source_field': 'book.' + field,
                'extraction_record_id': record['id'],
                'record_location': copy.deepcopy(record['page']),
                'location_scope': 'narration under heading, not certified heading page',
            },
        })
    return tags


def adapt(record, dataset, book, edition, original_index, manifest_sha):
    out = copy.deepcopy(record)
    source_language = record['language']
    language = LANGUAGES[source_language][0]
    out['schema_version'] = SCHEMA
    out['extraction_schema_version'] = record['schema_version']
    out['language'] = language
    out['source_language_code'] = source_language
    out['record_id'] = record['id']
    out['occurrence_id'] = record['id']
    out['content_kind'] = 'source_narration_occurrence_not_independently_classified'
    out['source']['package_file'] = evidence_path(record['source']['package_file'])
    out['provenance']['bank_intake'] = {
        'adapter_version': '1.0.0',
        'source_records_path': evidence_path(dataset['records_file']),
        'source_json_pointer': '/' + str(original_index),
        'extraction_record_sha256': sha(canonical(record)),
        'text_payload_sha256': sha(canonical(record['text'])),
        'source_package_checksums_sha256': manifest_sha,
        'source_language_code': source_language,
        'bank_language_code': language,
        'language_alias_note': 'Directory alias only; no locale or script conversion.',
        'new_translation_created': False,
        'canonical_identity_inferred': False,
    }
    out['review'].update({
        'release_status': 'private_candidate',
        'independent_pro_qc': 'pending',
        'release_eligible': False,
        'mechanical_validation_report': 'reports/validation.json',
    })
    # Supplied files have no publisher category tables. Do not invent topic IDs.
    out['topic_tags'] = []
    out['source_structure_tags'] = structure_tags(record)
    ai = str(record['ai_translation']).lower()
    source_tag = 'hadeethenc' if dataset['format'] == 'xlsx' else dataset['source_id']
    values = [
        'source:' + source_tag, 'language:' + language, 'book:' + book,
        'edition:' + edition, 'format:' + dataset['format'],
        'method:' + record['provenance']['extraction_method'],
        'review:pending_independent_pro', 'ai_translation:' + ai,
        'kind:narration_occurrence', 'rights:pending', 'canonical_mapping:unverified',
        'arabic:' + ('present' if record['text']['arabic'] else 'not_supplied'),
        'translation:' + ('present' if record['text']['translation'] else 'not_supplied'),
    ]
    if record['review']['issues']:
        values.append('source_issues:flagged')
    if record['narration_unit'] not in ('source_entry', 'source_occurrence'):
        values.append('segmentation:split_source_occurrence')
    out['editorial_tags'] = {'origin': 'import_pipeline_not_publisher', 'values': values}
    out['rights'] = {
        'status': 'not_assessed_for_publication',
        'reuse_basis': None,
        'publication_authorized_by_this_import': False,
        'source_conditions_path': evidence_path(dataset['source_metadata']),
        'note': ('Publisher headers, attribution and version notices are preserved. '
                 'Compliance with applicable reuse conditions is not certified by this import.'
                 if dataset['format'] == 'xlsx' else
                 'Supplied PDF and source translation rights have not been established.'),
    }
    gaps = ['independent_pro_publication_qc', 'public_redistribution_basis',
            'canonical_occurrence_mapping', 'narration_authenticity_classification',
            'publisher_topic_taxonomy_not_supplied']
    if record['translator']['name'] is None:
        gaps.append('named_translator')
    if record['book']['edition'] is None:
        gaps.append('bibliographic_edition')
    if record['narrator']['name'] is None:
        gaps.append('separate_narrator_name')
    if record['text']['arabic'] is None:
        gaps.append('source_arabic_not_supplied')
    if record['text']['translation'] is None:
        gaps.append('source_translation_not_supplied')
    if dataset['format'] == 'xlsx':
        gaps.append('translation_edition_scope_not_independently_verified')
    out['metadata_gaps'] = gaps
    out['source_occurrence_group'] = source_group(record, dataset)
    entry_id = record['number'].get('source_entry_id')
    out['related_source_entries'] = ({
        'provider': 'HadeethEnc.com', 'entry_id': entry_id,
        'index_path': 'indexes/hadeethenc-related-entries.json',
        'basis': 'same publisher entry ID only; not canonical identity or variant alignment',
    } if dataset['format'] == 'xlsx' and entry_id else None)
    return out


def refresh_checksums(root):
    excluded = {'checksums.sha256', 'reports/validation.json'}
    lines = []
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel not in excluded:
            lines.append(file_sha(path) + '  ' + rel)
    (root / 'checksums.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(lines)


def build(input_root, output, bank_root=None):
    input_root, output = input_root.resolve(), output.resolve()
    bank_root = (bank_root or pathlib.Path(__file__).resolve().parents[1]).resolve()
    if output.is_relative_to(bank_root):
        raise ValueError('Private candidate must remain outside the public repository')
    if output.is_relative_to(input_root) or input_root.is_relative_to(output):
        raise ValueError('Input and output trees must not overlap')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be new or empty')
    manifest_sha, verified_files = verify_source_package(input_root)
    catalog = json.loads((input_root / 'catalog.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(input_root, output / EVIDENCE)
    collections_index = []
    counts = collections.Counter()
    ai_counts = collections.Counter()
    related = collections.defaultdict(list)
    groups = collections.defaultdict(list)
    seen_ids = set()
    per_language = collections.defaultdict(list)
    structure_tag_ids = set()
    tag_counts = collections.Counter()
    missing_translation = 0
    for dataset in catalog['datasets']:
        src_path = local(input_root, dataset['records_file'])
        records = json.loads(src_path.read_text(encoding='utf-8'))
        if len(records) != dataset['records']:
            raise ValueError('Source catalog count mismatch')
        source_language = dataset['language']
        language, label = LANGUAGES[source_language]
        parts = pathlib.PurePosixPath(dataset['records_file']).parts
        book = parts[1]
        if not re.fullmatch('[a-z0-9-]+', book):
            raise ValueError('Unsafe book slug')
        source_meta = json.loads(local(input_root, dataset['source_metadata']).read_text(encoding='utf-8'))
        if dataset['format'] == 'xlsx':
            version = source_meta.get('version')
            if not isinstance(version, str) or not re.fullmatch('v[0-9.]+', version):
                raise ValueError('Missing literal XLSX export version')
            edition = 'xlsx-' + version + '-' + dataset['source_sha256'][:16]
        else:
            edition = 'pdf-' + dataset['source_sha256'][:16]
        directory = pathlib.PurePosixPath('languages') / language / 'books' / book / 'editions' / edition
        converted = []
        for i, record in enumerate(records):
            if record['id'] in seen_ids:
                raise ValueError('Duplicate input occurrence ID: ' + record['id'])
            seen_ids.add(record['id'])
            if record['language'] != source_language or record['source']['sha256'] != dataset['source_sha256']:
                raise ValueError('Record source does not match catalog')
            original = local(input_root, record['source']['package_file'])
            if not original.is_file():
                raise ValueError('Original source missing')
            item = adapt(record, dataset, book, edition, i, manifest_sha)
            converted.append(item)
            ai_counts[str(item['ai_translation']).lower()] += 1
            missing_translation += item['text']['translation'] is None
            for tag in item['source_structure_tags']:
                structure_tag_ids.add(tag['tag_id'])
            tag_counts['records_with_source_structure'] += bool(item['source_structure_tags'])
            tag_counts['source_structure_assignments'] += len(item['source_structure_tags'])
            tag_counts['editorial_assignments'] += len(item['editorial_tags']['values'])
            groups[item['source_occurrence_group']['id']].append(item['id'])
            if item['related_source_entries']:
                related[item['related_source_entries']['entry_id']].append({
                    'id': item['id'], 'language': language, 'source_language_code': source_language,
                    'source_id': dataset['source_id'], 'records_path': (directory / 'records.json').as_posix(),
                    'json_pointer': '/' + str(i),
                })
        destination = output / directory / 'records.json'
        write_json(destination, converted)
        collection = {
            'language': language, 'source_language_code': source_language,
            'language_name': label, 'book': book, 'edition': edition,
            'edition_scope': 'source asset snapshot; not an inferred print edition',
            'records_path': (directory / 'records.json').as_posix(),
            'records_sha256': file_sha(destination), 'count': len(converted),
            'source_id': dataset['source_id'], 'source_sha256': dataset['source_sha256'],
            'source_records_path': evidence_path(dataset['records_file']),
            'source_file': converted[0]['source']['package_file'] if converted else None,
            'source_metadata_path': evidence_path(dataset['source_metadata']),
            'coverage_path': evidence_path(dataset['coverage_file']),
            'exceptions_path': evidence_path(dataset['exceptions_file']),
            'release_status': 'private_candidate',
            'source_entries': dataset.get('source_entries'), 'pdf_pages': dataset.get('pdf_pages'),
            'format': dataset['format'],
        }
        write_json(output / directory / 'manifest.json', collection)
        counts[language] += len(converted)
        collections_index.append(collection)
        per_language[language].append(collection)
    if len(seen_ids) != catalog['record_count']:
        raise ValueError('Total source occurrence count mismatch')
    write_json(output / 'collections.json', {
        'schema': 'hadith-bank-attachment-collections-v1', 'collections': collections_index,
        'primary_format': 'UTF-8 JSON array; one source narration occurrence per object',
        'record_count': len(seen_ids), 'release_status': 'private_candidate',
    })
    write_json(output / 'indexes/hadeethenc-related-entries.json', {
        'basis': 'same publisher entry ID only; not canonical identity or exact variant alignment',
        'groups': [{'entry_id': key, 'occurrences': value} for key, value in sorted(related.items())],
    })
    write_json(output / 'indexes/source-occurrence-groups.json', {
        'basis': 'exact source occurrence/row segmentation relationships; no deduplication',
        'groups': [{'source_occurrence_id': key, 'record_ids': value}
                   for key, value in sorted(groups.items()) if len(value) > 1],
    })
    for language, entries in sorted(per_language.items()):
        write_json(output / 'languages' / language / 'catalog.json', {
            'schema': 'hadith-bank-attachment-language-v1', 'language': language,
            'record_count': counts[language], 'collections': entries,
            'release_status': 'private_candidate',
        })
    summary = {
        'schema': 'hadith-bank-attachment-intake-summary-v1',
        'intake_id': 'attachments-' + manifest_sha[:16],
        'record_count': len(seen_ids), 'datasets': len(collections_index),
        'by_language': dict(sorted(counts.items())), 'ai_translation': dict(ai_counts),
        'records_without_translation': missing_translation,
        'tag_counts': {**dict(tag_counts), 'distinct_source_structure_tags': len(structure_tag_ids),
                       'publisher_topic_assignments': 0},
        'source_package_checksums_sha256': manifest_sha,
        'source_package_files_verified': verified_files,
        'source_package_catalog_sha256': file_sha(input_root / 'catalog.json'),
        'source_text_altered': False, 'new_translations_generated': 0,
        'occurrence_ids_preserved': True, 'deduplicated_or_removed_records': 0,
        'prior_sqlite_intake': 'Separate source format/revision; overlap is not adjudicated and totals must not be added as unique narrations.',
        'publication_status': 'private_candidate_not_published',
        'published_translation_entries': 0,
        'independent_pro_publication_qc': 'pending',
        'source_fidelity_review': 'Original extraction checks and limited review coverage preserved; no new full visual certification.',
        'collections': collections_index,
    }
    write_json(output / 'reports/intake-summary.json', summary)
    write_json(output / 'PUBLICATION-GATE.json', {
        'allowed': False, 'release_eligible_records': 0,
        'reasons': [
            'Independent Pro publication QC of exact final corpus is pending.',
            'Reuse basis and applicable publication conditions are not established for this intake.',
            'Source-fidelity, metadata, completeness and canonical-alignment limitations remain as recorded.',
        ],
        'public_branch_is_publication': True,
    })
    write_json(output / 'FIELD-MAPPING.json', {
        'original_evidence': EVIDENCE.as_posix(),
        'unchanged_fields': 'All original fields except schema_version, directory-language alias, relocated source.package_file; provenance and review gain bank-only keys.',
        'identities': 'id, record_id and occurrence_id retain the original extraction occurrence ID.',
        'main_format': 'records.json arrays; evidence records and raw rows are not additional bank entries.',
        'language_alias': {'zh': 'zh-CN'},
        'tag_policy': 'Publisher topic_tags empty without supplied taxonomy; literal headings in source_structure_tags; import metadata in editorial_tags.',
        'source_rows_and_pages': 'Spreadsheet rows remain sheet/row locators, never printed-page guesses.',
        'version_policy': 'XLSX export labels and checksums identify supplied snapshots; no silent SQLite/current API enrichment.',
    })
    for name in ['search_attachments.py', 'validate_attachments.py', 'import_attachments.py']:
        src = bank_root / 'scripts' / name
        if src.is_file():
            (output / 'scripts').mkdir(exist_ok=True)
            shutil.copyfile(src, output / 'scripts' / name)
    for name in ['attachment.record.schema.json', 'extraction.record.schema.json']:
        src = bank_root / 'schemas' / name
        if src.is_file():
            (output / 'schemas').mkdir(exist_ok=True)
            shutil.copyfile(src, output / 'schemas' / name)
    readme = (
        '# Hadith Bank — private attachment intake\n\n'
        f'{len(seen_ids):,} source narration occurrences from {len(collections_index)} supplied PDF/XLSX sources. '
        'This bank candidate contains the actual texts and all original files locally. '
        'It has not been approved for public release.\n\n'
        'Main records: languages/<code>/books/<book>/editions/<source-snapshot>/records.json. '
        'Each object preserves text, book/number, narrator, source, translator and page separately. '
        'Chinese directory code zh-CN is an organizational alias; source code zh and all characters are preserved.\n\n'
        'Publisher topic categories were not supplied; topic_tags is empty. '
        'Literal source headings are source_structure_tags. Operational tags are editorial_tags. '
        'Arabic/translation/commentary/footnotes, source defects, repeated occurrences, split relationships, '
        'uncertain metadata and AI-translation evidence are preserved.\n\n'
        'The exact previous extraction package is evidence/extraction-package/. Its raw rows, source entries, '
        'PDF pages and ancillary texts are evidence, not extra primary records. '
        'Historical absolute paths in its original audits are mapped by its audit/artifact-path-map.json.\n\n'
        'Python 3, offline:\n\n'
        '    python scripts/validate_attachments.py --root .\n'
        '    python scripts/search_attachments.py --root . --language ja --limit 3\n'
        '    python scripts/search_attachments.py --root . --language zh-CN --book bukhari --limit 3\n'
        '    python scripts/search_attachments.py --root . --tag review:pending_independent_pro --limit 3\n\n'
        'See PUBLICATION-GATE.json, reports/intake-summary.json, reports/validation.json, '
        'FIELD-MAPPING.json and checksums.sha256. checksums.sha256 covers all files except itself '
        'and reports/validation.json, which reports validation of this manifest.\n'
    )
    (output / 'README.md').write_text(readme, encoding='utf-8')
    refresh_checksums(output)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.input, args.output)
        print(json.dumps({k: v for k, v in result.items() if k != 'collections'},
                         ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.exit('Attachment import failed: ' + str(error))
