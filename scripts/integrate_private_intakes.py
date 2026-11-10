#!/usr/bin/env python3
"""Add verified attachment packages to an existing private combined bank.

This adapter never edits canonical source files or extracts/translates source text.
It preserves existing search-shard bytes and appends separate source occurrences.
Only the two declared attachment package formats are supported. Public trees are
rejected. Source-level review and redistribution qualifications are retained.
"""
import argparse
from collections import Counter
import copy
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys

from build_bank_views import (SCHEMA, canonical, digest_file, write_json,
                              write_entry_points, write_catalog_readme)
from build_reader import build as build_reader, load_records, local


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify_package(root):
    """Verify every supplied package file; reject unlisted files and symlinks."""
    root = root.resolve()
    if (root / 'SHA256SUMS.json').is_file():
        checksum_name = 'SHA256SUMS.json'
        entries = read(root / checksum_name)['files']
    elif (root / 'SHA256SUMS.txt').is_file():
        checksum_name = 'SHA256SUMS.txt'
        entries = []
        for line in (root / checksum_name).read_text(encoding='utf-8').splitlines():
            if line.strip():
                sha, path = line.split('  ', 1)
                entries.append({'path': path, 'sha256': sha})
    else:
        raise ValueError('Package has no supported checksum manifest')
    declared = set()
    verified = []
    for item in entries:
        rel = item['path']
        if rel in declared:
            raise ValueError('Duplicate checksum path: ' + rel)
        declared.add(rel)
        path = local(root, rel)
        if not path.is_file() or digest_file(path) != item['sha256']:
            raise ValueError('Package checksum mismatch: ' + rel)
        if 'bytes' in item and path.stat().st_size != item['bytes']:
            raise ValueError('Package byte-count mismatch: ' + rel)
        verified.append({'path': rel, 'sha256': item['sha256'], 'bytes': path.stat().st_size})
    files = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink not permitted in intake package')
        if path.is_file():
            files.add(path.relative_to(root).as_posix())
    if files != declared | {checksum_name}:
        raise ValueError('Unlisted or missing package files: ' + str(sorted(files ^ (declared | {checksum_name}))))
    verified.append({'path': checksum_name, 'sha256': digest_file(root / checksum_name),
                     'bytes': (root / checksum_name).stat().st_size})
    return verified


def describe_package(root):
    manifest = read(root / 'manifest.json')
    if manifest.get('package_id', '').startswith('vietnamese-upload-'):
        source_catalog = read(local(root.resolve(), manifest['source_catalog']))
        collections = []
        for s in source_catalog:
            records = local(root.resolve(), s['records_file'])
            collections.append({
                'language': s['language'], 'book': s['book_id'],
                'edition': s['source_snapshot'], 'source_id': s['source_id'],
                'records_path': s['records_file'], 'records_sha256': digest_file(records),
                'count': s['record_count'], 'source_file': s['package_file'],
                'source_sha256': s['sha256'], 'pdf_pages': s['pdf_pages'],
                'release_status': 'private_candidate', 'format': 'pdf',
                'source_metadata_path': s['records_file'].rsplit('/', 1)[0] + '/manifest.json',
            })
        return {'id': 'attachments-vi-' + manifest['input_sha256'][:16],
                'count': manifest['record_count'], 'collections': collections,
                'catalog_path': 'catalog/sources.json', 'source_pdf_pages': manifest['source_pdf_pages'],
                'kind': 'vietnamese_source_booklets', 'scope': 'supplied booklets, not complete canonical collections'}
    if manifest.get('schema') == 'hadith-bank-private-intake-package-v1' and manifest.get('language') == 'ja':
        collections = read(local(root.resolve(), manifest['collection_catalog']))['collections']
        return {'id': 'attachments-ja-muslim-' + manifest['source_sha256'][:16],
                'count': manifest['counts']['records'], 'collections': collections,
                'catalog_path': manifest['collection_catalog'],
                'source_pdf_pages': manifest['counts']['source_pages'],
                'kind': 'japanese_muslim_web_volume_1',
                'scope': 'supplied volume-one web PDF; abbreviated references remain abbreviated',
                'record_types': manifest['counts']['record_types']}
    raise ValueError('Unsupported attachment intake manifest')


def translation_info(record, prefix):
    ai = record.get('ai_translation', 'unknown')
    translator = record['translator']
    credited = [translator['name']] if translator.get('name') else translator.get('credited_names', [])
    evidence = copy.deepcopy(translator.get('evidence'))
    supported = ai is False and bool(credited) and bool(evidence)
    return {
        'origin': 'human_translator_credited' if supported else 'unknown',
        'label': ('Human translation — ' + '、'.join(credited)) if supported else 'Published-source translation — origin unresolved',
        'basis': 'human_translation_credit_in_supplied_source' if supported else 'source_specific_translation_role_not_established',
        'human_involvement': 'named_human_translator_in_source' if supported else 'not_established',
        'ai_translation': ai,
        'evidence_ids': ['source-translation-' + record['source']['sha256'][:16]],
        'scope_note': ('Source credit establishes human translation origin; extraction fidelity and exact canonical mapping remain pending. '
                       'Named volume translators do not establish individual per-occurrence assignment.' if supported else
                       'Unknown is not a claim of machine translation. Source credits and all original flags remain preserved.'),
        'policy_path': 'catalog/intake-translation-origins.json',
        'original_provenance': copy.deepcopy(record.get('translation_provenance', record.get('translation_origin'))),
        'evidence_package_root': prefix,
    }


def project(record, collection, position, prefix):
    """Normalize navigation, preserving canonical content and all uncertain fields."""
    if record['review'].get('release_status') != 'private_candidate' or record['review'].get('release_eligible') is not False:
        raise ValueError('Intake record lacks required private-candidate qualification: ' + record['id'])
    source = record['source']
    title = record.get('title')
    title = title.get('translation') if isinstance(title, dict) else title
    review = copy.deepcopy(record['review'])
    review['certified_release_eligible'] = False
    result = {
        'schema_version': SCHEMA, 'id': record['id'],
        'language': record['language'], 'source_language_code': record['source_language_code'],
        'book_key': collection['book'], 'edition': collection['edition'],
        'source_id': collection['source_id'], 'provider_entry_id': record['number'].get('source_entry_id'),
        'title': title, 'text_arabic': record['text']['arabic'], 'text_translation': record['text']['translation'],
        'number': copy.deepcopy(record['number']), 'narrator': copy.deepcopy(record['narrator']),
        'source': {
            'name': source.get('source_site_as_printed') or source['title'],
            'work_title': record['book']['title'], 'url': source.get('url', source.get('source_url_as_printed')),
            'record_url': source.get('url', source.get('source_url_as_printed')),
            'original_file': prefix + '/' + source['package_file'], 'sha256': source['sha256'],
            'record_locator': {'path': prefix + '/' + collection['records_path'], 'json_pointer': '/' + str(position)},
            'format': source['format'], 'intake_root': prefix,
            'source_metadata_path': prefix + '/' + collection['source_metadata_path'],
            'source_url_live_verified': source.get('url_live_verified', False),
            'canonical_record_path_resolution': 'Paths inside preserved source records resolve relative to intake_root.',
        },
        'translator': copy.deepcopy(record['translator']),
        'translation_provenance': translation_info(record, prefix),
        'topic_tags': copy.deepcopy(record.get('topic_tags', [])),
        'editorial_tags': list(record['editorial_tags']['values']),
        'source_headings': [x['value_verbatim'] for x in record.get('source_structure_tags', [])],
        'review': review, 'commentary': copy.deepcopy(record['commentary']),
        'benefits': copy.deepcopy(record.get('benefits')), 'footnotes': copy.deepcopy(record['footnotes']),
        'references': copy.deepcopy(record['references']), 'grading': copy.deepcopy(record['grading']),
        'page': copy.deepcopy(record['page']), 'related_versions': copy.deepcopy(record.get('related_versions', [])),
        'source_occurrence_group': copy.deepcopy(record.get('source_occurrence_group')),
        'record_type': record.get('record_type'), 'content_kind': record.get('content_kind'),
        'isnad': copy.deepcopy(record.get('isnad')),
        'rights': copy.deepcopy(record.get('rights')),
        'metadata_gaps': copy.deepcopy(record.get('metadata_gaps')),
        'related_source_entries': copy.deepcopy(record.get('related_source_entries', [])),
        'ai_translation': record['ai_translation'],
        'canonical_record_sha256': hashlib.sha256(canonical(record)).hexdigest(),
    }
    # Unapproved Arabic stays only in preserved canonical evidence, never in text_arabic.
    if record.get('source_text'):
        result['source_text_evidence'] = {'path': prefix + '/' + collection['records_path'],
                                          'json_pointer': '/' + str(position) + '/source_text',
                                          'approved_arabic_original': False}
    return result


def verify_existing_stream(root, catalog):
    rows, _, info = load_records(root)
    ids = {r['id'] for r in rows}
    if len(ids) != len(rows):
        raise ValueError('Existing bank has duplicate occurrence IDs')
    # Check all shards even when the optional complete stream is available.
    stream_hash = hashlib.sha256()
    for shard in catalog['search']['shards']:
        path = local(root, shard['path'])
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != shard['sha256'] or len(data) != shard['bytes']:
            raise ValueError('Existing shard checksum or size mismatch: ' + shard['path'])
        if len(data.splitlines()) != shard['count']:
            raise ValueError('Existing shard record count mismatch: ' + shard['path'])
        stream_hash.update(data)
    if stream_hash.hexdigest() != info['records_sha256']:
        raise ValueError('Existing ordered shards disagree with full stream')
    return ids, {r['id']: hashlib.sha256(canonical(r)).hexdigest() for r in rows}


def refresh_entry_points(root, catalog, intakes):
    """Reuse common catalog output; correct its original single-intake assumptions."""
    write_entry_points(root, catalog)
    write_catalog_readme(root, catalog)
    index = read(root / 'index.json')
    # This historic intake retains exactly its own count, not every private record.
    for dataset in index.get('datasets', []):
        if dataset.get('id') == 'attachments-b53d154fa3622b95':
            dataset['count'] = sum(m['count'] for m in catalog['materials']
                                   if m['canonical_records_path'].startswith('attachments/attachments-b53d154fa3622b95/'))
    for intake in intakes:
        entry = {'id': intake['id'], 'catalog': intake['root'] + '/' + intake['catalog_path'],
                 'count': intake['count'], 'availableLocally': True,
                 'release_status': 'private_candidate', 'publicTextPublished': False}
        index.setdefault('datasets', []).append(copy.deepcopy(entry))
        index.setdefault('privateIntakes', []).append(copy.deepcopy(entry))
    write_json(root / 'index.json', index)
    total = format(catalog['record_count'], ',')
    private_total = sum(m['count'] for m in catalog['materials'] if m['release_status'] != 'published_unreviewed_source_import')
    text = (root / 'README.md').read_text(encoding='utf-8')
    text = text.replace('the 32,300 supplied ', 'the ' + format(private_total, ',') + ' supplied ')
    text = text.replace('all 40,723 indexed ', 'all ' + total + ' indexed ')
    text = text.replace('`attachments/attachments-b53d154fa3622b95/` |', '`attachments/<intake-id>/` |')
    text += ('\n## Added source packages\n\n'
             '| Package | Source occurrences | Source pages | Scope |\n| --- | ---: | ---: | --- |\n')
    for intake in intakes:
        text += '| [' + intake['kind'] + '](' + intake['root'] + '/README.md) | ' + format(intake['count'], ',') + ' | ' + str(intake['source_pdf_pages']) + ' | ' + intake['scope'] + ' |\n'
    text += ('\nThe Japanese Muslim source contains 1,406 narration/report occurrences, 214 variant occurrences and '
             '191 abbreviated route/reference occurrences. Its 1,811 entries do not establish completeness of '
             'the three-volume printed work. Vietnamese coverage is limited to the 45 supplied booklets.\n\n'
             'Both added packages retain `private_candidate`, pending independent review and '
             '`release_eligible=false`. Approved Arabic text is null: Japanese lacks complete Arabic originals, '
             'and the Vietnamese PDFs have unapproved Arabic text-layer mappings retained as raw evidence.\n\n'
             '[Additive integration verification](reports/private-intake-integration.json) · '
             '[Preserved earlier 40,723-record audit](reports/history/organization-final-audit-40723.json)\n')
    (root / 'README.md').write_text(text, encoding='utf-8')


def merge_intake_metadata(catalog, plans, previous_evidence, new_evidence):
    """Keep prior intake history and evidence resolvable across additive runs."""
    history = copy.deepcopy(catalog.get('additive_intake_history', []))
    new_history = [{'intake_id': p['id'], 'count': p['count'], 'root': p['root'],
                    'report': 'reports/private-intake-integration.json'} for p in plans]
    intake_ids = [p['intake_id'] for p in history + new_history]
    if len(intake_ids) != len(set(intake_ids)):
        raise ValueError('Intake history identity already registered')
    evidence = copy.deepcopy(previous_evidence) + copy.deepcopy(new_evidence)
    evidence_ids = [item['id'] for item in evidence]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError('Translation evidence identity already registered')
    return history + new_history, evidence


def integrate(root, package_paths, render=True):
    root = root.resolve()
    catalog = read(local(root, 'catalog/materials.json'))
    if catalog.get('scope') != 'private_combined_sources':
        raise ValueError('Private intake integration refuses public repository trees')
    old_catalog = copy.deepcopy(catalog)
    ids, original_object_hashes = verify_existing_stream(root, catalog)
    original_count = len(ids)
    existing_ids = set(ids)
    existing_datasets = {m['dataset_id'] for m in catalog['materials']}
    original_stream_hash = catalog['search']['records_sha256']
    plans = []
    projections = []
    evidence = []
    comparisons = []
    planned_shards = set()
    prior_evidence_path = root / 'catalog/intake-translation-origins.json'
    previous_evidence = read(prior_evidence_path).get('evidence', []) if prior_evidence_path.exists() else []
    from jsonschema import Draft202012Validator
    validator = Draft202012Validator(read(root / 'schemas/search.record.schema.json'))
    for supplied in package_paths:
        supplied = supplied.resolve()
        checks = verify_package(supplied)
        plan = describe_package(supplied)
        prefix = 'attachments/' + plan['id']
        if local(root, prefix).exists():
            raise ValueError('Intake is already present; no existing package is overwritten: ' + prefix)
        plan.update({'root': prefix, 'source_root': str(supplied), 'verified_files': checks})
        count = 0
        for c in plan['collections']:
            if c['source_id'] in existing_datasets:
                raise ValueError('Dataset identity already registered: ' + c['source_id'])
            existing_datasets.add(c['source_id'])
            path = local(supplied, c['records_path'])
            if digest_file(path) != c['records_sha256']:
                raise ValueError('Canonical records checksum mismatch')
            rows = read(path)
            if len(rows) != c['count']:
                raise ValueError('Canonical count mismatch')
            if digest_file(local(supplied, c['source_file'])) != c['source_sha256']:
                raise ValueError('Source PDF checksum mismatch')
            projected = []
            for position, record in enumerate(rows):
                rid = record['id']
                if rid in ids:
                    raise ValueError('Occurrence identity collision: ' + rid)
                ids.add(rid)
                if (record['source']['package_file'] != c['source_file'] or
                        record['source']['sha256'] != c['source_sha256'] or record['language'] != c['language']):
                    raise ValueError('Record source identity differs from its collection')
                item = project(record, c, position, prefix)
                validator.validate(item)
                for key in ('number', 'narrator', 'translator', 'commentary', 'footnotes', 'references', 'grading', 'page', 'related_versions'):
                    if item[key] != record.get(key, []):
                        raise ValueError('Preservation failure: ' + key)
                if item['text_arabic'] != record['text']['arabic'] or item['text_translation'] != record['text']['translation']:
                    raise ValueError('Source text changed during projection')
                if item['review'].get('current_policy') is not None:
                    raise ValueError('HadeethEnc waiver must not apply to private PDF intakes')
                projected.append(item)
            first = projected[0]
            for start in range(0, len(projected), 100):
                rel = '/'.join(('search', first['language'], first['book_key'], first['edition'], 'part-' + str(start // 100 + 1).zfill(4) + '.jsonl'))
                if local(root, rel).exists() or rel in planned_shards:
                    raise ValueError('Refusing to overwrite existing search shard: ' + rel)
                planned_shards.add(rel)
            projections.append(projected)
            count += len(projected)
            catalog['materials'].append({
                'dataset_id': c['source_id'], 'language': c['language'], 'book_key': c['book'],
                'edition': c['edition'], 'source_name': first['source']['name'], 'count': len(projected),
                'release_status': 'private_candidate', 'available_locally': True,
                'source_file': first['source']['original_file'], 'source_sha256': first['source']['sha256'],
                'canonical_records_path': prefix + '/' + c['records_path'],
                'canonical_records_sha256': c['records_sha256'],
                'translation_provenance': first['translation_provenance'], 'current_review_policy': None,
                'intake_id': plan['id'], 'source_pdf_pages': c.get('pdf_pages'),
            })
            evidence.append({'id': 'source-translation-' + c['source_sha256'][:16], 'source_id': c['source_id'],
                             'canonical_records_path': prefix + '/' + c['records_path'],
                             'source_metadata_path': prefix + '/' + c['source_metadata_path'],
                             'source_file': prefix + '/' + c['source_file'], 'source_sha256': c['source_sha256'],
                             'translator': copy.deepcopy(rows[0]['translator']),
                             'ai_translation_counts': dict(Counter(str(r['ai_translation']).lower() for r in rows)),
                             'scope': 'source credit or unknown; extraction and scholarly review remain separate'})
            comparisons.append({'canonical_path': prefix + '/' + c['records_path'], 'records': len(rows),
                                'canonical_sha256': c['records_sha256'], 'exact_ids_text_and_metadata_preserved': True})
        if count != plan['count']:
            raise ValueError('Package aggregate count mismatch')
        plans.append(plan)
    intake_history, evidence = merge_intake_metadata(catalog, plans, previous_evidence, evidence)
    # All inputs pass before the private output is mutated.
    for plan in plans:
        target = local(root, plan['root'])
        shutil.copytree(Path(plan['source_root']), target)
        if verify_package(target) != plan['verified_files']:
            raise ValueError('Copied package failed exact verification')
    whole = local(root, catalog['search']['records_path'])
    if not whole.exists():
        with whole.open('wb') as stream:
            for shard in catalog['search']['shards']:
                with local(root, shard['path']).open('rb') as source:
                    shutil.copyfileobj(source, stream)
    old_size = whole.stat().st_size
    language_counts = Counter(catalog['by_language'])
    origin_counts = Counter(catalog['translation_origins'])
    added = []
    with whole.open('ab') as stream:
        for projected in projections:
            for start in range(0, len(projected), 100):
                block = projected[start:start + 100]
                first = block[0]
                rel = '/'.join(('search', first['language'], first['book_key'], first['edition'], 'part-' + str(start // 100 + 1).zfill(4) + '.jsonl'))
                path = local(root, rel)
                if path.exists():
                    raise ValueError('Refusing to overwrite existing search shard: ' + rel)
                data = b''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n' for r in block)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                stream.write(data)
                item = {'path': rel, 'sha256': hashlib.sha256(data).hexdigest(), 'count': len(block), 'bytes': len(data)}
                catalog['search']['shards'].append(item)
                added.append(item)
                for r in block:
                    language_counts[r['language']] += 1
                    origin_counts[r['translation_provenance']['origin']] += 1
    with whole.open('rb') as stream:
        prefix_digest = hashlib.sha256(stream.read(old_size)).hexdigest()
    if prefix_digest != original_stream_hash:
        raise ValueError('Existing complete search-stream prefix changed')
    catalog.update({'record_count': len(ids), 'by_language': dict(sorted(language_counts.items())),
                    'translation_origins': dict(origin_counts)})
    catalog['private_materials_not_in_this_tree'] = [m for m in catalog['private_materials_not_in_this_tree']
                                                  if m['dataset_id'] not in existing_datasets]
    catalog['search'].update({'count': len(ids), 'records_sha256': digest_file(whole)})
    catalog['additive_intake_history'] = intake_history
    write_json(root / 'catalog/materials.json', catalog)
    write_json(root / 'catalog/intake-translation-origins.json', {
        'schema': 'hadith-bank-private-intake-translation-evidence-v1',
        'principle': 'Preserve exact source credits and ai_translation flags; do not infer missing translators or approve extraction fidelity.',
        'evidence': evidence})
    refresh_entry_points(root, catalog, plans)
    # Retain the prior completed audit, clearly scope the new one to additive organization.
    history = root / 'reports/history'
    history.mkdir(exist_ok=True)
    for name in ('organization-final-audit.json', 'reading-views-validation.json'):
        prior = root / 'reports' / name
        if prior.exists():
            saved = history / (prior.stem + '-' + str(original_count) + '.json')
            if saved.exists() and saved.read_bytes() != prior.read_bytes():
                raise ValueError('Existing history would be overwritten')
            if not saved.exists():
                shutil.copyfile(prior, saved)
    final_rows, _, verification = load_records(root)
    if ({r['id']: hashlib.sha256(canonical(r)).hexdigest() for r in final_rows[:original_count]} != original_object_hashes
            or {r['id'] for r in final_rows} != ids):
        raise ValueError('Existing occurrence projections changed or IDs lost')
    del final_rows
    report = {
        'schema': 'hadith-bank-private-intake-integration-v1', 'status': 'passed',
        'scope': 'mechanical additive organization; no new source-character or scholarly QC',
        'as_of_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'baseline': {'records': original_count, 'search_stream_sha256': original_stream_hash,
                     'preserved_audit': 'reports/history/organization-final-audit-' + str(original_count) + '.json'},
        'records_added': len(ids - existing_ids), 'record_count': len(ids), 'source_dataset_count': len(catalog['materials']),
        'by_language': catalog['by_language'], 'original_search_shards_unchanged': len(old_catalog['search']['shards']),
        'original_search_stream_preserved_as_exact_byte_prefix': True,
        'existing_projection_objects_compared': original_count,
        'new_projection_schema_records_checked': len(ids - existing_ids),
        'new_source_record_comparisons': comparisons, 'new_shards': added,
        'intakes': [{k: v for k, v in p.items() if k not in ('source_root', 'collections')} for p in plans],
        'search_stream_sha256': verification['records_sha256'],
        'source_occurrences_merged': 0, 'source_text_modified': False,
        'source_pdf_page_images_reviewed': 0, 'independent_source_qc_performed': False,
        'review_status_promoted': False, 'private_candidate_text_published': False,
        'limitations': ['This audit verifies packaging and projections, not PDF image/character fidelity.',
                       'Arabic originals and canonical mappings retain source-specific unresolved status.',
                       'The prior audit covers the original 40,723 occurrences; this additive audit covers the new packages and preservation of those projections.'],
    }
    if render:
        report['reader_build'] = build_reader(root, root / 'hadith-bank-reader.html', root / 'browse')
        report['reader_sha256'] = digest_file(root / 'hadith-bank-reader.html')
    write_json(root / 'reports/private-intake-integration.json', report)
    write_json(root / 'catalog/new-private-intake-metadata.json', {
        'schema': 'hadith-bank-additional-private-intakes-v1',
        'record_count': len(ids - existing_ids),
        'materials': [{k: v for k, v in m.items() if k in ('dataset_id', 'language', 'book_key', 'edition', 'count', 'source_sha256', 'release_status')}
                      | {'available_locally': False, 'location_note': 'Available in separate private combined package; not a public runtime locator.'}
                      for m in catalog['materials'][len(old_catalog['materials']):]],
        'intakes': [{k: p[k] for k in ('id', 'count', 'kind', 'scope', 'source_pdf_pages')} for p in plans],
    })
    return {k: report[k] for k in ('status', 'record_count', 'records_added', 'source_dataset_count', 'by_language', 'search_stream_sha256')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank-root', type=Path, required=True)
    parser.add_argument('--package', type=Path, action='append', required=True)
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args()
    try:
        result = integrate(args.bank_root, args.package, not args.no_render)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Private intake integration failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
