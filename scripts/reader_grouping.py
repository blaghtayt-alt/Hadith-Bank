"""Hash-bound presentation groups; canonical source occurrences stay separate.

Only sidecars explicitly pinned by an accepted material's supporting_files are
read. A reviewed star links new source occurrences to one existing anchor; this
does not infer a global canonical hadith identity or alter source/search bytes.
"""
import copy
import hashlib
from pathlib import Path

from build_reader import local, parse_json, valid_hash
from counterpart_review import validate_source_binding


SCHEMA = 'hadith-bank-reader-groups-v1'
PREFIX = 'sources/reader-groups/'
RELATIONS = {'same_narration', 'same_narration_core', 'source_excerpt', 'exact_source_copy'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def empty_reader_groups(count):
    return {'schema': SCHEMA, 'groups': [], 'source_occurrence_count': count,
            'grouped_reading_count': count}


def validate_group_documents(documents, records):
    """Validate triples and a one-pass record iterable, retaining linked rows only."""
    entries_to_check, needed_ids, source_scope = [], set(), set()
    for document, authorized_sources, location in documents:
        require(isinstance(document, dict) and document.get('schema') == SCHEMA,
                'Invalid reader grouping schema: ' + location)
        new_sources = document.get('new_source_ids')
        require(isinstance(new_sources, list) and bool(new_sources) and
                all(isinstance(value, str) and value for value in new_sources) and
                len(new_sources) == len(set(new_sources)),
                'Reader grouping needs distinct new_source_ids: ' + location)
        require(set(new_sources) <= set(authorized_sources),
                'Reader grouping source lacks supporting-file authorization: ' + location)
        source_scope.update(new_sources)
        entries = document.get('links')
        require(isinstance(entries, list) and bool(entries),
                'Reader grouping sidecar needs reviewed links: ' + location)
        for entry in entries:
            require(isinstance(entry, dict) and entry.get('relation') in RELATIONS,
                    'Reader grouping requires an explicitly reviewed source relation: ' + location)
            review = entry.get('review')
            require(isinstance(review, dict) and
                    all(isinstance(review.get(key), str) and bool(review[key].strip())
                        for key in ('reviewer', 'method', 'evidence')) and
                    type(review.get('human_review')) is bool and
                    isinstance(review.get('qualifications', []), list) and
                    all(isinstance(value, str) for value in review.get('qualifications', [])),
                    'Reader grouping needs explicit review evidence: ' + location)
            for key in ('source', 'target'):
                binding = entry.get(key)
                require(isinstance(binding, dict), 'Missing reader grouping ' + key + ' binding: ' + location)
                identifier = binding.get('record_id')
                require(isinstance(identifier, str) and identifier,
                        'Reader grouping binding needs an occurrence ID: ' + location)
                needed_ids.add(identifier)
            entries_to_check.append((entry, set(new_sources)))
    by_id, count = {}, 0
    for record in records:
        identifier = record.get('id')
        count += 1
        if identifier in needed_ids:
            require(identifier not in by_id,
                    'Reader grouping requires distinct stable IDs for linked occurrences: ' + identifier)
            by_id[identifier] = record
    links = []
    for entry, new_sources in entries_to_check:
        bound = []
        for key in ('source', 'target'):
            binding = entry[key]
            record = by_id.get(binding['record_id'])
            require(record is not None, 'Reader grouping occurrence is missing: ' + binding['record_id'])
            validate_source_binding(record, binding)
            bound.append(record)
        source, target = bound
        require(source['source_id'] in new_sources,
                'Reader grouping source is outside its declared new-source scope: ' + source['id'])
        require(source['id'] != target['id'], 'Reader grouping cannot link an occurrence to itself')
        if entry['relation'] == 'exact_source_copy':
            require(entry['source']['source_text_sha256'] == entry['target']['source_text_sha256'],
                    'Exact source copy requires identical chosen quotation bytes: ' + source['id'])
        links.append((source, target, entry))
    seen_sources, grouped = set(), {}
    for source, target, entry in links:
        require(source['id'] not in seen_sources,
                'Duplicate or ambiguous reader grouping source: ' + source['id'])
        seen_sources.add(source['id'])
        require(target['source_id'] not in source_scope,
                'Reader grouping target must be an existing source outside the new-source scope: ' + target['id'])
        grouped.setdefault(target['id'], []).append({
            'source_occurrence_id': source['id'], 'target_occurrence_id': target['id'],
            'relation': entry['relation'], 'review': copy.deepcopy(entry['review'])})
    require(not seen_sources.intersection(grouped), 'Chained or cyclic reader grouping is not permitted')
    result = empty_reader_groups(count)
    result['groups'] = [{'id': target, 'anchor_id': target,
                         'member_ids': [target, *sorted(item['source_occurrence_id'] for item in comparisons)],
                         'comparisons': sorted(comparisons, key=lambda item: item['source_occurrence_id'])}
                        for target, comparisons in sorted(grouped.items())]
    result['grouped_reading_count'] -= len(seen_sources)
    return result


def load_reader_groups(root, records, catalog=None):
    """Load only exact, accepted supporting-file sidecars, without registry reload.

    ``catalog`` is the already validated material catalog. If omitted, read its
    local JSON descriptor. Unreferenced files under sources/reader-groups are
    never discovered or granted authority by their directory location alone.
    """
    root = Path(root).resolve()
    if catalog is None:
        path = local(root, 'catalog/materials.json')
        catalog = parse_json(path.read_text(encoding='utf-8')) if path.exists() else {}
    require(isinstance(catalog, dict), 'Invalid catalog for reader grouping')
    descriptors = {}
    for material in catalog.get('materials', []):
        for descriptor in material.get('supporting_files', []):
            relative = descriptor.get('path')
            if not isinstance(relative, str) or not relative.startswith(PREFIX):
                continue
            require(relative.endswith('.json'), 'Reader grouping sidecar must be JSON: ' + relative)
            publication = material.get('publication') or {}
            require(publication.get('authorized') is True and
                    isinstance(material.get('dataset_id'), str) and material['dataset_id'],
                    'Reader grouping supporting file is not an accepted material: ' + relative)
            expected = valid_hash(descriptor.get('sha256'), relative + '.sha256')
            previous = descriptors.get(relative)
            require(previous is None or previous['sha256'] == expected,
                    'Conflicting reader grouping supporting-file hashes: ' + relative)
            item = descriptors.setdefault(relative, {'sha256': expected, 'sources': set()})
            item['sources'].add(material['dataset_id'])
    documents = []
    for relative, descriptor in sorted(descriptors.items()):
        path = local(root, relative)
        require(path.is_file(), 'Missing reader grouping sidecar: ' + relative)
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == descriptor['sha256'],
                'Reader grouping sidecar checksum mismatch: ' + relative)
        documents.append((parse_json(raw.decode('utf-8')), descriptor['sources'], relative))
    return validate_group_documents(documents, records)
