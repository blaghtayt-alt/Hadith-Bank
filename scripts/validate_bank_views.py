#!/usr/bin/env python3
"""Validate local bank views without changing canonical files or using a network.

The combined mode derives all totals from its catalog. Public mode additionally
pins the six original snapshots and verifies explicitly registered owner-authorized
material manifests. This validates
organization, byte preservation and local dependencies; it is not source-page,
translation, authenticity, copyright or independent Pro QC.
"""
import argparse
import base64
from collections import Counter
import datetime
import gzip
import hashlib
import html
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from current_provenance import apply_policy as apply_provenance_policy, classification, decision_for, load_policy as load_provenance_policy
from review_display_policy import extraction_metadata
from resolve_counterparts import CounterpartResolver


PUBLIC_BASELINE = '9688bbfb6e53832169acdc4ef5127ef8fc1fb259'
# language: source code, count, raw database SHA-256, canonical JSONL SHA-256.
# These are the exact owner-authorized public snapshot, not an editable catalog.
PUBLIC_SNAPSHOTS = {
    'ja': ('ja', 281, 'a81da9af28f854f6d44456657228ca7bc244aea70d5665717797b9cee7530847', '35650ff990760029aaa3f7f03b5c94c55759aa104a3dc0c8e35d9c24dc3359c9'),
    'fil': ('tl', 1949, 'e8fa6e4c26c11c060c36621cc7fb257a3e8daab957f1bb226ad3940688a72abb', '4329ff9582d8c88e9f394078b80acd354f5d0e83ffb5fcbfc9e4e372a5c97f63'),
    'vi': ('vi', 1203, '3fb9e549494ff0f60454b034add71b0cefe72deb3e4fffce98f4bf90a79abcd7', 'edcea9fc2017d45c9803cdbea873755da4c820126692824a85359d3f22837c8d'),
    'zh-CN': ('zh', 2256, 'a22a0e545c70b320b451ebc37022f1fe24b74e03f6b26972444753517944a604', 'd7aa6c6d2d6d74685e66e4ddbb40fb5f7c2d091894d708d3b1f6799b3754dcff'),
    'uz': ('uz', 420, '8241193c5ac1f3bcc2c708ebb5dc3ee42313e04f6a32d04b3010f2b38c9506a7', '3c9e01b66288242ad61b1ebc8d94e0c49c098492e057de4df8e7a1c2b27f48bf'),
    'hi': ('hi', 2314, '3b74b6c4da6dc8838741fae5d7f2281cdb3ae896f9614c987e78baf8cccfd45d', '28f86705f984c270f1e393c7e69d8ba158998b633772460fa7d2957bb98d29c9'),
}


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def local(root, relative, exists=True):
    """Require a normalized portable relative path and reject symlinks."""
    require(isinstance(relative, str) and bool(relative), 'Missing local path')
    pure = PurePosixPath(relative)
    require(not pure.is_absolute() and pure.as_posix() == relative and
            all(part not in ('', '.', '..') and ':' not in part for part in relative.split('/')) and
            '\\' not in relative and not any(ord(c) < 32 for c in relative), 'Unsafe local path: ' + relative)
    target = root
    for part in pure.parts:
        target = target / part
        require(not target.is_symlink(), 'Symlink local dependency: ' + relative)
    require(target.resolve().is_relative_to(root), 'Local path escapes bank: ' + relative)
    if exists:
        require(target.is_file(), 'Missing local file: ' + relative)
    return target


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def parse_json(data):
    def invalid_constant(value):
        raise ValidationError('Non-finite JSON constant: ' + value)
    return json.loads(data, object_pairs_hook=unique_pairs, parse_constant=invalid_constant)


def read_json(root, relative):
    return parse_json(local(root, relative).read_bytes())


def object_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def count(value, field):
    require(type(value) is int and value >= 0, 'Invalid nonnegative count: ' + field)
    return value


def checked_hash(root, relative, expected, evidence):
    require(isinstance(expected, str) and re.fullmatch(r'[0-9a-f]{64}', expected), 'Invalid SHA-256: ' + relative)
    path = local(root, relative)
    actual = file_hash(path)
    require(actual == expected, 'SHA-256 mismatch: ' + relative)
    evidence[relative] = {'path': relative, 'bytes': path.stat().st_size, 'sha256': actual}
    return path


def source_rows(path):
    if path.suffix == '.jsonl':
        with path.open('rb') as stream:
            for line_number, line in enumerate(stream, 1):
                require(bool(line.strip()), 'Blank canonical JSONL line: ' + str(line_number))
                yield line_number - 1, parse_json(line)
    else:
        rows = parse_json(path.read_bytes())
        require(isinstance(rows, list), 'Canonical JSON file must contain an array: ' + path.name)
        yield from enumerate(rows)


def public_materials():
    expected = {}
    for language, (source_code, total, raw_hash, record_hash) in PUBLIC_SNAPSHOTS.items():
        edition = 'sqlite-' + raw_hash[:16]
        identifier = 'hadeethenc-' + source_code + '-' + edition
        expected[identifier] = {
            'dataset_id': identifier, 'language': language, 'book_key': 'hadeethenc',
            'edition': edition, 'count': total,
            'source_file': 'sources/hadeethenc/snapshots/2026-11-11/raw/' + source_code + '.sqlite',
            'source_sha256': raw_hash,
            'canonical_records_path': 'languages/' + language + '/books/hadeethenc/editions/' + edition + '/records.jsonl',
            'canonical_records_sha256': record_hash,
        }
    return expected


def public_expected(row, material, position, policy, provenance_policy=None):
    """Independently map every public view field to its frozen canonical source.

    A full object comparison prevents private commentary, metadata, unknown extra
    fields or substituted narration text from entering a public projection.
    """
    source_code, entry = row['source_language_code'], row['source_entry_id']
    provenance, publication, commentary = row['provenance'], row['publication'], row['commentary']
    references = {k: v for k, v in row['source_references'].items() if k != 'citation_lines'}
    references['citation_line_count'] = len(row['source_references'].get('citation_lines', []))
    arabic_benefits = commentary.get('arabic_benefits_raw_json_verbatim')
    if isinstance(arabic_benefits, str):
        try:
            arabic_benefits = parse_json(arabic_benefits)
        except ValueError:
            arabic_benefits = {'unparsed_source_json': arabic_benefits}
    topic_tags = []
    for tag in row.get('topic_tags', []):
        category = tag.get('category_verbatim') or {}
        topic_tags.append({'id': str(category['id']) if category.get('id') is not None else None,
                           'label': category.get('title'),
                           'path': [x['title'] for x in tag.get('ancestors_including_self_verbatim', []) if x.get('title')],
                           'origin': 'publisher_taxonomy'})
    alignment = row['arabic_alignment']['status']
    review = {'status': row['review']['release_status'],
              'issues': [] if alignment == 'exact_provider_id_version_and_text_match' else [alignment],
              'independent_pro_qc': row['review']['independent_pro_qc'],
              'release_status': row['review']['release_status'],
              'certified_release_eligible': row['review'].get('certified_release_eligible', False)}
    if policy:
        review['current_policy'] = {
            'separate_bank_review_required': False, 'status': 'not_required_by_owner',
            'label': policy['label'], 'decision_date_japan': policy['decision_date_japan'],
            'independent_review_performed': False, 'historical_status_preserved': True,
            'arabic_alignment_flags_retained': True, 'policy_path': 'catalog/review-policy.json',
        }
    result = {
        'schema_version': 'hadith-bank-search-record-v1', 'id': row['record_id'],
        'language': material['language'], 'source_language_code': source_code,
        'book_key': 'hadeethenc', 'edition': material['edition'], 'source_id': material['dataset_id'],
        'provider_entry_id': entry, 'title': row.get('title_verbatim'),
        'text_arabic': row['texts']['arabic_verbatim'], 'text_translation': row['texts']['translation_verbatim'],
        'number': {'source_entry_id': entry, 'in_book': None, 'canonical': None}, 'narrator': row['narration'],
        'source': {'name': 'HadeethEnc.com', 'work_title': publication['translation_work'],
                   'url': 'https://hadeethenc.com/' + source_code,
                   'record_url': 'https://hadeethenc.com/' + source_code + '/browse/hadith/' + entry,
                   'download_url': provenance['source_download_url'],
                   'original_file': provenance['local_database_path'], 'sha256': provenance['database_sha256'],
                   'record_locator': {'path': material['canonical_records_path'], 'line': position + 1},
                   'format': 'sqlite', 'retrieved_at': provenance['retrieved_at']},
        'translator': {'name': publication['translator'], 'evidence': None, 'publisher': publication['publisher']},
        'translation_provenance': {
            'origin': 'publisher_human_workflow', 'label': 'Human translation — HadeethEnc',
            'basis': 'owner_source_classification_and_publisher_described_workflow', 'translation_classification': 'human',
            'human_involvement': 'publisher_described_translation_proofreading_and_review', 'ai_translation': row['ai_translation'],
            'evidence_ids': ['hadeethenc-platform', 'publisher-translation-workflow', 'ai-assistance-scope'],
            'scope_note': 'Human source classification follows the owner instruction and publisher translation workflow. The individual translator and exact-version AI assistance are not stated; the historic AI flag is preserved.',
            'policy_path': 'catalog/translation-origins.json'},
        'topic_tags': topic_tags, 'editorial_tags': row.get('editorial_tags', {}).get('values', []), 'source_headings': [],
        'review': review,
        'extraction': extraction_metadata(row),
        'commentary': {'arabic': commentary.get('arabic_explanation_verbatim'), 'translation': commentary.get('translation_explanation_verbatim')},
        'benefits': {'translation': commentary.get('translation_benefits_decoded'), 'arabic': arabic_benefits},
        'footnotes': [], 'footnote_status': row['footnotes'], 'references': references,
        'grading': row['grading'],
        'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': provenance['source_rowid'], 'row_scope': 'SQLite source row; not a printed page'},
        'related_versions': row['related_versions'], 'canonical_record_sha256': object_hash(row),
    }
    return apply_provenance_policy(result, provenance_policy)


def expected_record(row, material, position, is_jsonl, policy, provenance_policy=None):
    if material.get('adapter') in ('pdf-intake-package-v1', 'records-v1'):
        from material_registry import project_for_material
        projected = project_for_material(row, material, position)
        return {'id': projected['id'], 'full_projection_sha256': object_hash(projected),
                'text_arabic': projected['text_arabic'], 'text_translation': projected['text_translation'],
                'canonical_record_sha256': object_hash(row), 'source_id': material['dataset_id'],
                'language': material['language'], 'book_key': material['book_key'], 'edition': material['edition'],
                'locator': projected['source']['record_locator'], 'source_file': material['source_file'],
                'source_sha256': material['source_sha256'], 'authorized_material': True}
    if 'texts' in row and 'record_id' in row:
        expected = public_expected(row, material, position, policy, provenance_policy)
        return {'id': row['record_id'], 'full_projection_sha256': object_hash(expected),
                'text_arabic': expected['text_arabic'], 'text_translation': expected['text_translation'],
                'canonical_record_sha256': expected['canonical_record_sha256'],
                'source_id': material['dataset_id'], 'language': material['language'],
                'book_key': material['book_key'], 'edition': material['edition'],
                'locator': expected['source']['record_locator'],
                'source_file': material['source_file'], 'source_sha256': material['source_sha256']}
    require('id' in row and isinstance(row.get('text'), dict), 'Unsupported canonical record shape')
    locator = {'path': material['canonical_records_path']}
    locator['line' if is_jsonl else 'json_pointer'] = position + 1 if is_jsonl else '/' + str(position)
    preserved = {field: row[field] for field in ('number', 'narrator', 'translator', 'commentary', 'footnotes', 'references', 'grading', 'page') if field in row}
    review = row.get('review', {})
    return {'id': row['id'], 'canonical_record_sha256': object_hash(row),
            'text_arabic': row['text'].get('arabic'), 'text_translation': row['text'].get('translation'),
            'source_id': material['dataset_id'], 'language': material['language'], 'book_key': material['book_key'],
            'edition': material['edition'], 'locator': locator,
            'source_file': material['source_file'], 'source_sha256': material['source_sha256'],
            'ai_translation': row.get('ai_translation', 'unknown'), 'preserved_fields': preserved,
            'review_fields': {k: review[k] for k in ('status', 'issues', 'independent_pro_qc', 'release_status') if k in review}}


def compare_projection(record, expected, root, public, counterpart_resolver=None):
    if counterpart_resolver is None and 'counterparts' in record:
        counterpart_resolver = CounterpartResolver(root)
    identifier = expected['id']
    for field in ('id', 'source_id', 'language', 'book_key', 'edition', 'text_arabic', 'text_translation', 'canonical_record_sha256'):
        require(record.get(field) == expected[field], 'Projection/source mismatch for ' + identifier + ': ' + field)
    source = record.get('source') or {}
    require(source.get('record_locator') == expected['locator'], 'Canonical locator mismatch: ' + identifier)
    require(source.get('original_file') == expected['source_file'] and source.get('sha256') == expected['source_sha256'], 'Original source locator mismatch: ' + identifier)
    local(root, source['original_file'])
    local(root, source['record_locator']['path'])
    if 'full_projection_sha256' in expected:
        original = {key: value for key, value in record.items() if key != 'counterparts'}
        require(object_hash(original) == expected['full_projection_sha256'], 'Public projection fields differ from authorized source and policy: ' + identifier)
    else:
        require(not public, 'Private canonical shape in public projection')
        for field, value in expected['preserved_fields'].items():
            require(record.get(field) == value, 'Preserved metadata changed for ' + identifier + ': ' + field)
        require(record.get('translation_provenance', {}).get('ai_translation') == expected['ai_translation'], 'AI origin flag changed: ' + identifier)
        for field, value in expected['review_fields'].items():
            require(record.get('review', {}).get(field) == value, 'Historical review changed for ' + identifier + ': ' + field)
        require(record.get('review', {}).get('certified_release_eligible') is False, 'Private source release status promoted: ' + identifier)
    if counterpart_resolver is not None and counterpart_resolver.enabled:
        require(record.get('counterparts') == counterpart_resolver.for_record(record),
                'Counterpart differs from its verified source/matching evidence: ' + identifier)
    else:
        require('counterparts' not in record, 'Counterpart lacks a verified source manifest: ' + identifier)
    for relative in (record.get('translation_provenance', {}).get('policy_path'),
                     record.get('translation_provenance', {}).get('current_policy', {}).get('policy_path'),
                     record.get('review', {}).get('current_policy', {}).get('policy_path')):
        if relative is not None:
            local(root, relative)
    if public and not expected.get('authorized_material'):
        require('attachments/' not in json.dumps(record, ensure_ascii=False), 'Attachment path appears in public projection: ' + identifier)


def verify_shards(root, search, expected, public):
    counterpart_resolver = CounterpartResolver(root)
    require(isinstance(search.get('shards'), list) and search['shards'], 'Missing ordered search shards')
    aggregate, seen, paths, projected_hashes = hashlib.sha256(), set(), set(), []
    by_language, by_dataset, current_origins, text_codepoints = Counter(), Counter(), Counter(), 0
    for shard in search['shards']:
        relative = shard['path']
        require(relative not in paths, 'Duplicate search shard path: ' + relative)
        paths.add(relative)
        path = local(root, relative)
        digest, size, rows, last = hashlib.sha256(), 0, 0, b''
        with path.open('rb') as stream:
            for raw in stream:
                digest.update(raw); aggregate.update(raw); size += len(raw); last = raw
                require(bool(raw.strip()), 'Blank search JSONL line: ' + relative)
                record = parse_json(raw)
                require(isinstance(record, dict), 'Non-object search record: ' + relative)
                identifier = record.get('id')
                require(isinstance(identifier, str) and identifier in expected, 'Unexpected projected occurrence: ' + str(identifier))
                require(identifier not in seen, 'Duplicate projected occurrence: ' + identifier)
                compare_projection(record, expected[identifier], root, public, counterpart_resolver)
                seen.add(identifier); rows += 1
                by_language[record['language']] += 1; by_dataset[record['source_id']] += 1
                current_origins[classification(record)] += 1
                text_codepoints += sum(len(record.get(k) or '') for k in ('text_arabic', 'text_translation'))
                projected_hashes.append((identifier, object_hash(record)))
        require(digest.hexdigest() == shard['sha256'], 'Shard SHA-256 mismatch: ' + relative)
        require(size == count(shard['bytes'], 'shard.bytes') and rows == count(shard['count'], 'shard.count'), 'Shard byte/record count mismatch: ' + relative)
        require(not last or last.endswith(b'\n'), 'Search shard lacks terminal newline: ' + relative)
    require(seen == set(expected), 'Search stream omits canonical occurrences')
    require(len(seen) == count(search['count'], 'search.count'), 'Search record count mismatch')
    require(aggregate.hexdigest() == search['records_sha256'], 'Ordered shard aggregate SHA-256 mismatch')
    whole = local(root, search['records_path'], exists=False)
    if whole.exists():
        require(whole.is_file() and file_hash(whole) == search['records_sha256'], 'Whole search stream hash mismatch')
    else:
        require(search.get('whole_file_optional') is True, 'Required whole search stream missing')
    return projected_hashes, dict(sorted(by_language.items())), dict(sorted(by_dataset.items())), text_codepoints, dict(sorted(current_origins.items()))


def reader_shard_records(path, manifest):
    """Verify bounded local transport pieces and yield complete JSONL records."""
    require(isinstance(manifest, dict) and manifest.get('schema') == 'hadith-bank-reader-shards-v1'
            and manifest.get('encoding') == 'gzip-jsonl-shards', 'Unsupported reader shard manifest')
    require(isinstance(manifest.get('shards'), list), 'Reader manifest shards must be an array')
    expected_count = count(manifest.get('record_count'), 'reader.record_count')
    require(isinstance(manifest.get('jsonl_sha256'), str) and
            re.fullmatch(r'[0-9a-f]{64}', manifest['jsonl_sha256']), 'Invalid reader stream SHA-256')
    seen, pending, total = set(), b'', 0
    aggregate = hashlib.sha256()
    for part in manifest['shards']:
        require(isinstance(part, dict), 'Invalid reader shard descriptor')
        relative = part.get('path')
        require(isinstance(relative, str) and not re.search(r'[%?#]', relative),
                'Unsafe reader shard path')
        require(relative not in seen, 'Duplicate reader shard path')
        seen.add(relative)
        target = local(path.parent, relative)
        expected_bytes = count(part.get('bytes'), 'reader.shard.bytes')
        expected_plain = count(part.get('uncompressed_bytes'), 'reader.shard.uncompressed_bytes')
        require(0 < expected_bytes <= 2 * 1024 * 1024 and expected_plain <= 2 * 1024 * 1024,
                'Reader shard exceeds its size bound')
        require(target.stat().st_size == expected_bytes, 'Reader shard byte count mismatch')
        raw = target.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == part.get('sha256'), 'Reader shard SHA-256 mismatch')
        with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as stream:
            plain = stream.read(expected_plain + 1)
        require(len(plain) == expected_plain, 'Reader shard uncompressed byte count mismatch')
        aggregate.update(plain)
        require(plain.count(b'\n') == count(part.get('count'), 'reader.shard.count'),
                'Reader shard record count mismatch')
        lines = (pending + plain).split(b'\n')
        pending = lines.pop()
        for line in lines:
            require(bool(line), 'Reader shard contains a blank JSONL record')
            record = parse_json(line)
            require(isinstance(record, dict), 'Reader shard contains a non-object record')
            total += 1
            require(total <= expected_count, 'Reader shard stream has excess records')
            yield record
    require(not pending, 'Reader shard stream lacks terminal newline')
    require(total == expected_count, 'Reader shard stream record count mismatch')
    require(aggregate.hexdigest() == manifest['jsonl_sha256'], 'Reader JSONL stream SHA-256 mismatch')


def verify_reader(root, relative, projected_hashes, search):
    path = local(root, relative)
    source = path.read_text(encoding='utf-8')
    payload = re.search(r'<script\b[^>]*\bid="hadith-records"[^>]*>(.*?)</script\s*>', source, re.S | re.I)
    require(payload is not None, 'Missing embedded reader payload')
    encoding = payload.group(0).split('>', 1)[0]
    sharded = 'data-encoding="gzip-jsonl-shards"' in encoding
    shard_count = 0
    if sharded:
        manifest = parse_json(payload.group(1))
        require(isinstance(manifest, dict) and isinstance(manifest.get('shards'), list),
                'Invalid reader shard manifest')
        shard_count = len(manifest['shards'])
        records = reader_shard_records(path, manifest)
    else:
        data = (gzip.decompress(base64.b64decode(payload.group(1).strip(), validate=True))
                if 'data-encoding="gzip-base64"' in encoding else payload.group(1))
        records = parse_json(data)
        require(isinstance(records, list) and len(records) == len(projected_hashes),
                'Reader occurrence count mismatch')
    compared = 0
    for record in records:
        require(compared < len(projected_hashes), 'Reader has excess occurrences')
        identifier, expected_hash = projected_hashes[compared]
        require(isinstance(record, dict) and record.get('id') == identifier and object_hash(record) == expected_hash,
                'Reader differs from source projection: ' + identifier)
        compared += 1
    require(compared == len(projected_hashes), 'Reader occurrence count mismatch')
    snapshot = re.search(r'<script\b[^>]*\bid="hadith-snapshot"[^>]*>(.*?)</script\s*>', source, re.S | re.I)
    require(snapshot is not None, 'Missing reader snapshot')
    summary = parse_json(snapshot.group(1))
    require(summary.get('record_count') == compared and summary.get('records_sha256') == search['records_sha256'],
            'Reader snapshot differs from search catalog')
    require(not re.search(r'<script\b[^>]*\bsrc\s*=|<link\b[^>]*\brel=["\']stylesheet', source, re.I),
            'Reader has external script/style dependency')
    return {'path': relative, 'sha256': file_hash(path), 'bytes': path.stat().st_size,
            'embedded_objects_compared': compared, 'data_shards_verified': shard_count,
            'external_script_or_stylesheet_dependencies': False}


def verify_navigation(root, anticipated_report=None):
    pages = [root / 'README.md']
    for subdir in ('browse', 'catalog'):
        directory = root / subdir
        require(directory.is_dir() and not directory.is_symlink(), 'Missing/unsafe navigation directory: ' + subdir)
        pages.extend(sorted(directory.rglob('*.md')))
    checked, external = 0, 0
    for path in pages:
        local(root, path.relative_to(root).as_posix())
        text = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
        links = re.findall(r'(?<!!)\[[^\]\n]*\]\(([^\s)]+)(?:\s+[^)]*)?\)', text)
        links.extend(re.findall(r'<a\s[^>]*href="([^"]+)"', text))
        for href in links:
            parsed = urlsplit(html.unescape(href))
            if parsed.scheme or parsed.netloc:
                external += 1; continue
            if not parsed.path:
                continue
            decoded = unquote(parsed.path)
            require('\\' not in decoded and not any(ord(c) < 32 for c in decoded), 'Unsafe navigation href')
            target = (path.parent / decoded).resolve()
            require(target.is_relative_to(root), 'Navigation escapes bank: ' + path.relative_to(root).as_posix())
            relative = target.relative_to(root).as_posix()
            # Navigation may intentionally name a directory; validate each path component.
            local(root, relative, exists=False)
            require(target.exists() or target == anticipated_report, 'Missing navigation target: ' + relative)
            checked += 1
    return {'markdown_files_checked': len(pages), 'local_targets_checked': checked,
            'external_links_not_requested': external, 'fragment_anchors_checked': False}


def verify_git_baseline(root, baseline, evidence, registered_files=None):
    require(bool(re.fullmatch(r'[0-9a-f]{40,64}', baseline)), 'Git baseline must be a full hexadecimal commit ID')
    command = ['git', '-C', str(root)]
    location = subprocess.run(command + ['rev-parse', '--show-toplevel'], check=True, capture_output=True, text=True).stdout.strip()
    require(Path(location).resolve() == root, 'Git baseline repository must be the validated bank root')
    commit = subprocess.run(command + ['rev-parse', '--verify', baseline + '^{commit}'], check=True, capture_output=True, text=True).stdout.strip()
    # Include the frozen source-support directories, not just the data files
    # named by the current catalog. This covers categories, edition manifests,
    # the Arabic support database, original archives and acquisition evidence.
    prefixes = ['sources/hadeethenc/snapshots/2026-11-11']
    prefixes.extend(str(PurePosixPath(m['canonical_records_path']).parent) for m in public_materials().values())
    baseline_files = subprocess.run(command + ['ls-tree', '-r', '--name-only', commit, '--'] + prefixes,
                                    check=True, capture_output=True, text=True).stdout.splitlines()
    baseline_paths = set(subprocess.run(command + ['ls-tree', '-r', '--name-only', commit],
                                       check=True, capture_output=True, text=True).stdout.splitlines())
    registered_files = registered_files or {}
    targets = dict(evidence)
    for relative, expected_hash in registered_files.items():
        require(file_hash(local(root, relative)) == expected_hash, 'Registered source checksum differs: ' + relative)
        require(relative not in targets or targets[relative]['sha256'] == expected_hash,
                'Registered source differs from catalog source: ' + relative)
        targets[relative] = {'sha256': expected_hash}
    for relative in baseline_files:
        if relative not in targets:
            path = local(root, relative)
            targets[relative] = {'sha256': file_hash(path)}
    checked, additions = [], []
    for relative, item in sorted(targets.items()):
        if relative not in baseline_paths:
            require(relative in registered_files, 'Unregistered source absent from baseline Git commit: ' + relative)
            additions.append({'path': relative, 'sha256': item['sha256']})
            continue
        result = subprocess.run(command + ['show', commit + ':' + relative], capture_output=True)
        require(result.returncode == 0, 'Source file absent from baseline Git commit: ' + relative)
        require(hashlib.sha256(result.stdout).hexdigest() == item['sha256'], 'Source bytes differ from baseline Git: ' + relative)
        checked.append(relative)
    return {'commit': commit, 'files_compared': len(checked), 'catalog_source_and_legacy_files': len(evidence),
            'additional_frozen_source_support_files': len(set(baseline_files) - set(evidence)),
            'all_existing_bytes_equal': True, 'new_registered_files_absent_from_baseline': len(additions),
            'new_registered_files': additions,
            'comparison_scope': 'Every existing source byte compared with Git; new registered source files separately checksum-verified.',
            'network_used': False, 'paths': checked}


def validate(root, mode='auto', reader='hadith-bank-reader.html', baseline=None, report_path=None):
    root = Path(root).resolve()
    catalog = read_json(root, 'catalog/materials.json')
    require(isinstance(catalog, dict), 'Invalid materials catalog')
    scope = catalog.get('scope')
    require(scope in ('public_source_snapshots', 'private_combined_sources'), 'Unknown catalog scope')
    public = scope == 'public_source_snapshots' if mode == 'auto' else mode == 'public'
    require((scope == 'public_source_snapshots') == public, 'Requested mode disagrees with catalog scope')
    materials = catalog.get('materials')
    require(isinstance(materials, list) and bool(materials), 'Missing source datasets')
    policy = read_json(root, 'catalog/review-policy.json').get('hadeethenc', {})
    provenance_policy = load_provenance_policy(root)
    require(policy.get('decision') == 'owner_waived_separate_bank_review' and policy.get('separate_bank_review_required') is False and policy.get('independent_review_performed') is False, 'Unrecognized current HadeethEnc policy')
    registered = {'materials': [], 'authorized_files': {}, 'manifests': []}
    if public:
        from material_registry import load_public_materials
        registered = load_public_materials(root)
        require(policy.get('label') == 'No separate bank review required — owner decision' and policy.get('decision_date_japan') == '2026-11-11', 'Public policy text differs from owner decision')
        allowed = public_materials()
        for material in registered['materials']:
            require(material['dataset_id'] not in allowed, 'Registered source duplicates a frozen snapshot')
            allowed[material['dataset_id']] = material
        require(len(materials) == len(allowed) and {m['dataset_id'] for m in materials} == set(allowed), 'Public dataset scope differs from authorized snapshots and material manifests')
        for material in materials:
            require(all(material.get(k) == v for k, v in allowed[material['dataset_id']].items()), 'Public snapshot metadata/hash mismatch: ' + material['dataset_id'])
        forbidden = [p.relative_to(root).as_posix() for p in root.rglob('*')
                     if '.git' not in p.parts and p.is_file() and p.suffix.lower() in ('.pdf', '.xlsx', '.xls', '.docx')
                     and p.relative_to(root).as_posix() not in registered['authorized_files']]
        require(not forbidden, 'Unregistered source documents present in public tree: ' + ', '.join(forbidden[:5]))
    evidence, expected, datasets, canonical_paths, expected_counts = {}, {}, set(), set(), Counter()
    for material in materials:
        identifier, relative = material['dataset_id'], material['canonical_records_path']
        require(identifier not in datasets and relative not in canonical_paths, 'Duplicate dataset or canonical path')
        datasets.add(identifier); canonical_paths.add(relative)
        checked_hash(root, material['source_file'], material['source_sha256'], evidence)
        for supporting in material.get('supporting_files', []):
            checked_hash(root, supporting['path'], supporting['sha256'], evidence)
        path = checked_hash(root, relative, material['canonical_records_sha256'], evidence)
        total = 0
        for position, row in source_rows(path):
            require(isinstance(row, dict), 'Canonical record is not an object: ' + relative)
            item = expected_record(row, material, position, path.suffix == '.jsonl', policy, provenance_policy)
            require(isinstance(item['id'], str) and item['id'] not in expected, 'Duplicate/missing canonical occurrence ID')
            expected[item['id']] = item; total += 1
        require(total == count(material['count'], 'material.count'), 'Canonical dataset count mismatch: ' + identifier)
        expected_counts[material['language']] += total
    for legacy in catalog.get('legacy_materials', []):
        path = checked_hash(root, legacy['path'], legacy['sha256'], evidence)
        require(path.stat().st_size == count(legacy['bytes'], 'legacy.bytes'), 'Legacy byte count mismatch: ' + legacy['path'])
        require(legacy.get('translation_origin') == 'unknown' and legacy.get('current_policy') == decision_for(legacy, provenance_policy),
                'Legacy origin differs from pending owner confirmation: ' + legacy['path'])
    require(len(expected) == count(catalog['record_count'], 'catalog.record_count') and dict(expected_counts) == catalog['by_language'], 'Catalog counts differ from canonical occurrences')
    projected_hashes, by_language, by_dataset, codepoints, current_origins = verify_shards(root, catalog['search'], expected, public)
    require(by_language == catalog['by_language'], 'Projected language totals differ from catalog')
    require(by_dataset == {m['dataset_id']: m['count'] for m in materials}, 'Projected dataset totals differ from catalog')
    require(catalog.get('current_translation_origins') == current_origins, 'Current translation classification totals differ from catalog')
    for language, total in by_language.items():
        language_catalog = read_json(root, 'catalog/languages/' + language + '.json')
        require(language_catalog.get('language') == language and language_catalog.get('record_count') == total and
                language_catalog.get('datasets') == [m for m in materials if m['language'] == language], 'Language catalog mismatch: ' + language)
    reader_result = verify_reader(root, reader, projected_hashes, catalog['search'])
    navigation = verify_navigation(root, report_path)
    git_result = verify_git_baseline(root, baseline, evidence, registered['authorized_files']) if baseline else {'performed': False, 'reason': 'No local Git baseline requested'}
    # Source files must still match after all view comparisons.
    for relative, item in evidence.items():
        require(file_hash(local(root, relative)) == item['sha256'], 'Source changed during validation: ' + relative)
    return {
        'schema': 'hadith-bank-portable-validation-v1', 'status': 'passed', 'scope': scope,
        'current_translation_origins': current_origins,
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'record_count': len(expected), 'source_dataset_count': len(materials),
        'by_language': by_language, 'by_dataset': by_dataset,
        'coverage': {'canonical_occurrences_compared': len(expected), 'projection_objects_compared': len(projected_hashes),
                     'exact_arabic_and_translation_codepoints_compared': codepoints,
                     'canonical_record_files_hashed': len(materials), 'source_and_legacy_files_hashed': len(evidence),
                     'ordered_search_shards_hashed': len(catalog['search']['shards']),
                     'canonical_record_digest_checks': len(expected),
                     'complete_public_projection_objects_reconstructed': len(expected) if public else sum('full_projection_sha256' in e for e in expected.values()),
                     'pdf_page_images_reviewed': 0, 'source_glyph_or_linguistic_reviews_performed': 0},
        'source_files': list(evidence.values()), 'search_stream_sha256': catalog['search']['records_sha256'],
        'reader': reader_result, 'navigation': navigation, 'baseline_git': git_result,
        'public_scope': {'enforced': public, 'authorized_dataset_count': len(allowed) if public else None,
                         'public_snapshot_hashes_pinned': public,
                         'unregistered_attachment_paths_and_extra_text_excluded': public,
                         'registered_material_manifests_verified': len(registered['manifests']),
                         'unregistered_source_documents_absent': public,
                         'source_review_and_rights_statuses_preserved': True},
        'runtime_source_files_local': True, 'network_requests': 0,
        'source_files_modified': False, 'independent_pro_qc_performed': False,
        'prior_audit_reports_modified': False, 'failures': [],
        'limitations': ['Comparisons establish equality with preserved canonical records, not source-page transcription accuracy.',
                        'No translation, narration-authenticity, rights or independent Pro QC was performed.',
                        'Reader payload equality is checked; visual browser behavior and remote URLs are not tested.',
                        'Historical broken links inside verbatim legacy documents are outside the generated-navigation check.'],
        'validator_sha256': file_hash(Path(__file__)),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--mode', choices=('auto', 'public', 'combined'), default='auto')
    parser.add_argument('--reader', default='hadith-bank-reader.html', help='Relative reader path inside bank')
    parser.add_argument('--baseline-ref', help='Optional full commit ID in this bank\'s local Git repository')
    parser.add_argument('--report', help='Optional reports/portable-validation*.json path inside bank; never overwrites source evidence')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    destination = None
    try:
        if args.report:
            require(bool(re.fullmatch(r'reports/portable-validation(?:-[A-Za-z0-9_-]+)?\.json', args.report)), 'Report output must be reports/portable-validation[-suffix].json')
            destination = local(root, args.report, exists=False)
        report = validate(root, args.mode, args.reader, args.baseline_ref, destination)
        if destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': report['status'], 'scope': report['scope'], 'records': report['record_count'],
                          'datasets': report['source_dataset_count'], 'shards': report['coverage']['ordered_search_shards_hashed'],
                          'baseline_git_files': report['baseline_git'].get('files_compared', 0), 'report': args.report}, ensure_ascii=False))
        return 0
    except (ValidationError, ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
