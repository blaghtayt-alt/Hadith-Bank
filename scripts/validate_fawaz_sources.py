#!/usr/bin/env python3
"""Verify Fawaz source fidelity, exact text partitions and occurrence accounting.

This validates preservation and bookkeeping, not narrational authenticity or
scholarly certification. It does not run an extraction/classification rule again.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse

import import_fawaz_bulk as source
from build_reader import local, parse_json


UNSET = object()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(left, right):
    """Keep scalar JSON types significant, including numeric source identifiers."""
    return json.dumps(left, ensure_ascii=False, sort_keys=True, allow_nan=False) == json.dumps(
        right, ensure_ascii=False, sort_keys=True, allow_nan=False)


def identity(book, number):
    return 'fawaz:' + source.REVISION[:12] + ':' + book + ':' + urllib.parse.quote(number, safe='._-')


def check_spans(values, length, label):
    require(isinstance(values, list), label + ' must be an array')
    cursor, result = 0, []
    for span in values:
        require(isinstance(span, list) and len(span) == 2 and all(type(v) is int for v in span),
                label + ' must contain integer offset pairs')
        start, end = span
        require(0 <= cursor <= start <= end <= length, label + ' overlaps, is unordered or is out of bounds')
        if start < end:
            result.append(span)
        cursor = end
    return result


def verify_partition(original, spans, quotation=UNSET, notes=UNSET, *, pending=False):
    """Check exact original Unicode-character spans, including interleaved notes."""
    require(isinstance(original, str) and isinstance(spans, dict), 'Missing source text or span evidence')
    require('notes' in spans, 'Missing note spans')
    if 'quotation_spans' in spans:
        quotations = check_spans(spans['quotation_spans'], len(original), 'Quotation spans')
        if 'quotation' in spans:
            require(len(quotations) <= 1 and spans['quotation'] == (quotations[0] if quotations else [0, 0]),
                    'Legacy quotation span disagrees with exact quotation spans')
    else:
        require('quotation' in spans, 'Missing quotation spans')
        quotations = check_spans([spans['quotation']], len(original), 'Quotation spans')
    note_spans = check_spans(spans['notes'], len(original), 'Note spans')
    cursor = 0
    for start, end in sorted(quotations + note_spans):
        require(start == cursor, 'Quotation/note partition has an overlap or an omitted source span')
        cursor = end
    require(cursor == len(original), 'Quotation/note partition does not cover the complete source field')
    extracted = ''.join(original[start:end] for start, end in quotations)
    expected_notes = [original[start:end] for start, end in note_spans]
    if pending:
        require(not quotations and quotation is None and bool(original.strip()),
                'Pending source context must have no narration quotation')
    elif quotation is not UNSET:
        require(isinstance(quotation, str) and quotation == extracted,
                'Displayed quotation differs from its exact source spans')
    if notes is not UNSET:
        require(notes == expected_notes, 'Displayed source notes differ from their exact source spans')
    return {'quotation_spans': quotations, 'notes': note_spans, 'quotation': extracted}


def verify_report_components(original, info, quotation_status):
    """Check compound source units without joining or discarding internal citations."""
    spans = info['text_spans']
    count = info.get('source_report_count', 1)
    boundaries = info.get('source_report_boundaries')
    retained = spans.get('retained_internal_citation_spans', [])
    require(type(count) is int and count >= 1, 'Invalid source report count')
    if boundaries is None:
        require(count == 1 and quotation_status != 'multiple_source_reports' and not retained,
                'Multiple source reports lack exact component boundaries')
        return 0, 0
    components = check_spans(boundaries, len(original), 'Source report boundaries')
    citations = check_spans(retained, len(original), 'Retained internal citation spans')
    require(len(components) == len(boundaries) == count and len(citations) == len(retained),
            'Source report count differs from its nonempty components')
    require((quotation_status == 'multiple_source_reports') == (count > 1),
            'Source report count and quotation status disagree')
    for key, expected in (('source_report_count', count), ('source_report_boundaries', boundaries)):
        if key in spans:
            require(same(spans[key], expected), 'Nested source report evidence disagrees with reading metadata')
    quotation = verify_partition(original, spans)['quotation']
    # Explicitly retained citations may bridge the components, as in Nawawi27.
    # Every selected character must still have exactly one documented role.
    verify_partition(original, {'quotation_spans': sorted(components + citations), 'notes': spans['notes']}, quotation)
    return count, len(citations)


def read_json(root, relative):
    return parse_json(local(root, relative).read_text(encoding='utf-8'))


def manifest_records(root, manifest):
    descriptor = manifest['records']
    path = local(root, descriptor['path'])
    require(path.stat().st_size <= source.MAX_CANONICAL_BYTES, 'Canonical Fawaz shard exceeds 40 MiB')
    digest, count = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for raw in stream:
            digest.update(raw)
            require(bool(raw.strip()), 'Empty canonical JSONL row: ' + descriptor['path'])
            count += 1
            yield parse_json(raw.decode('utf-8'))
    require(digest.hexdigest() == descriptor['sha256'] and count == descriptor['count'],
            'Canonical shard hash or count mismatch: ' + descriptor['path'])


def version_fingerprint(version):
    value = version.get('text')
    active = isinstance(value, str) and bool(value.strip())
    return {'language': version['language'], 'status': 'text' if active else 'source_context',
            'source_context_kind': None if active else version.get('quotation_status'),
            'quotation_sha256': source.sha(value.encode()) if isinstance(value, str) else None,
            'source_text_sha256': version['source']['source_text_sha256']}


class SourceAudit:
    def __init__(self, root):
        self.root = root.resolve()
        self.state = read_json(root, source.IMPORT + '/state.json')
        self.progress = read_json(root, source.IMPORT + '/progress.json')
        require(self.state.get('revision') == source.REVISION, 'Unexpected source revision')
        self.inputs, self.datasets, self.groups = self.state['inputs'], {}, collections.defaultdict(dict)
        self.counts = collections.Counter()
        self.by_language = collections.defaultdict(collections.Counter)
        self.accepted, self.held, self.ledgers = {}, {}, {}
        self.sizes = []
        for key, descriptor in self.inputs.items():
            require(descriptor.get('source_path') == key, 'Saved input key differs from its source path: ' + key)
            raw = source.checked_snapshot(root, descriptor)
            self.counts['verified_snapshots'] += 1
            if key == 'editions.json':
                self.catalog = parse_json(raw.decode('utf-8'))
            if key.startswith('editions/'):
                edition = Path(key).stem
                prefix, book = edition.split('-', 1)
                dataset = parse_json(raw.decode('utf-8'))
                self.datasets[edition] = dataset
                self.counts['verified_edition_snapshots'] += 1
                self.counts['source_edition_rows'] += len(dataset['hadiths'])
                self.counts['nonempty_source_text_fields'] += sum(bool(row['text'].strip()) for row in dataset['hadiths'])
                processed = self.progress['by_book'].get(book)
                if processed is None or (processed.get('processed_languages') is not None
                                         and prefix not in processed['processed_languages']):
                    # A saved optional edition need not be selected by a legacy
                    # plan. Its original bytes still verify above, but it is not
                    # part of this checkpoint's derived occurrence inventory.
                    continue
                for position, row in enumerate(dataset['hadiths']):
                    number = source.typed_identity(row['hadithnumber'])
                    self.groups[(book, number)].setdefault(prefix, []).append(position)

    def row(self, book, prefix, position):
        dataset = self.datasets[prefix + '-' + book]
        require(type(position) is int and 0 <= position < len(dataset['hadiths']), 'Source row position is out of bounds')
        return dataset['hadiths'][position]

    def reading(self, record, book, version):
        info = version['source']
        edition = info['provider_edition']
        prefix, own_book = edition.split('-', 1)
        require(own_book == book and prefix in source.LANGUAGES, 'Reading belongs to another provider book or edition')
        require((version['language'], version.get('script')) == (source.LANGUAGES[prefix][0], source.LANGUAGES[prefix][2]),
                'Reading language/script differs from its own edition')
        pointer = re.fullmatch(r'/hadiths/(\d+)', info['json_pointer'])
        require(pointer is not None and info.get('field') == 'text', 'Invalid exact source text locator')
        original = self.row(book, prefix, int(pointer[1]))
        require(record['id'] == identity(book, source.typed_identity(original['hadithnumber'])), 'Reading changed provider occurrence identity')
        descriptor = self.inputs['editions/' + edition + '.json']
        for own, saved in [('snapshot_path', 'path'), ('snapshot_sha256', 'sha256'),
                           ('snapshot_stored_sha256', 'stored_sha256'), ('url', 'url'), ('revision', 'revision')]:
            require(info.get(own) == descriptor[saved], 'Reading source descriptor mismatch: ' + own)
        require(info.get('snapshot_compression') == 'gzip', 'Reading source compression mismatch')
        require(info['source_text_sha256'] == source.sha(original['text'].encode()), 'Original language text hash mismatch')
        expected_url = source.entry_url(edition, original['hadithnumber'])
        require(info['record_url'] == expected_url, 'Reading source URL belongs to a different edition or provider entry')
        context_kind = version.get('quotation_status')
        pending = context_kind in ('boundary_pending', 'content_mismatch')
        notes = [item for item in version.get('comments', []) if isinstance(item, dict)
                 and item.get('scope') in ('source_compiler_note', 'source_context_not_narration')]
        require(all(item.get('source_url') == expected_url for item in notes), 'Source notes use another reading source URL')
        if pending:
            expected_scope = 'source_context' if context_kind == 'content_mismatch' else 'external_source'
            expected_boundary = 'content_mismatch' if context_kind == 'content_mismatch' else 'pending'
            require(version.get('scope') == expected_scope and info.get('quotation_boundary_status') == expected_boundary
                    and bool(info.get('quotation_boundary_reason')), 'Pending reading lacks its explicit source-context state')
            require(notes and all(item['scope'] == 'source_context_not_narration' for item in notes),
                    'Pending reading must preserve context outside the narration text')
            if context_kind == 'content_mismatch':
                require(version.get('match_status') == 'provider_entry_content_mismatch',
                        'Mismatched source context must not claim an established counterpart')
        else:
            require(isinstance(version.get('text'), str) and bool(version['text'].strip()), 'Active reading has no quotation')
            require(all(item['scope'] == 'source_compiler_note' for item in notes), 'Active reading mislabels source context')
        partition = verify_partition(original['text'], info['text_spans'], version.get('text'),
                                     [item['text'] for item in notes], pending=pending)
        report_components, internal_citations = verify_report_components(original['text'], info, version.get('quotation_status'))
        require(same(version['grading'], original['grades']), 'A reading changed its own source grades')
        supplied_numbers = {name: original.get(name) for name in ('hadithnumber', 'arabicnumber', 'reference')}
        require(same(version['provider_numbers'], supplied_numbers), 'A reading changed its own typed source numbering')
        reference = version['references'][0]
        require(reference.get('url') == expected_url and reference.get('canonical_mapping_status') == 'not_inferred'
                and same(reference.get('provider_numbers'), supplied_numbers), 'Language reference/numbering ownership mismatch')
        assessments = [item for item in version.get('comments', []) if isinstance(item, dict)
                       and item.get('scope') == 'provider_assessment_metadata']
        require(same([item.get('source_grade') for item in assessments], original['grades']), 'Visible assessment notes omit or change source grades')
        for item, grade in zip(assessments, original['grades']):
            label = 'Source assessment — ' + (str(grade['name']) if grade.get('name') is not None else 'Assessor not supplied')
            label += ': ' + (str(grade['grade']) if grade.get('grade') is not None else 'Grade not supplied')
            require(item.get('text') == label and item.get('source_url') == expected_url, 'Visible assessment disagrees with its source metadata')
        metadata = source.edition_metadata(self.catalog, book, prefix)
        author = metadata.get('author')
        compiler_credit = book == 'nawawi' and author == 'Imam Nawawi'
        translator = (author if prefix != 'ara' and not compiler_credit and isinstance(author, str)
                      and author.strip() and author.lower() != 'unknown' else None)
        require((info.get('translator') or {}).get('name') == translator, 'Reading borrowed or invented a translator')
        require(info.get('catalog_author_as_supplied') == author and info.get('catalog_source_as_supplied') == metadata.get('source'),
                'Reading changed catalog attribution')
        require(version.get('translation_provenance') is None if prefix == 'ara' else
                isinstance(version.get('translation_provenance'), dict) and version['translation_provenance'].get('translator') == translator,
                'Translation provenance does not belong to this reading')
        self.counts['verified_language_readings'] += 1
        self.counts['source_note_spans'] += len(notes)
        self.counts['source_assessments'] += len(assessments)
        self.counts['disjoint_quotation_readings'] += len(partition['quotation_spans']) > 1
        self.counts['verified_source_report_components'] += report_components
        self.counts['retained_internal_citation_spans'] += internal_citations
        self.by_language[version['language']]['source_context' if pending else 'active_quotations'] += 1
        return prefix

    def record(self, record, book, requested_languages):
        number = record['source']['provider_identity']['typed_hadithnumber']
        identifier = identity(book, number)
        require(record['source']['provider_identity']['book'] == book and record['book_key'] == source.BOOKS[book][0],
                'Registered collection differs from its own provider collection')
        require(record['id'] == identifier and identifier not in self.accepted, 'Duplicate or changed registered occurrence ID')
        require((book, number) in self.groups, 'Registered occurrence is absent from saved provider sources')
        original_group = self.groups[(book, number)]
        require(all(len(positions) == 1 for positions in original_group.values()), 'Duplicate provider rows were silently merged')
        require(record['number']['canonical'] is None, 'Provider numbering was promoted to canonical numbering')
        require(same(record['number']['source_entry_id'], parse_json(number)), 'Primary provider identifier changed JSON type or value')
        own = {}
        for version in record['language_versions']:
            prefix = self.reading(record, book, version)
            require(prefix in requested_languages, 'Reading belongs to an unrequested edition')
            require(prefix not in own and version['id'] == identifier + ':' + prefix, 'Duplicate or changed language-version identity')
            own[prefix] = version
        primary = next((item for item in own.values() if item['language'] == record['language'] and item.get('text')), None)
        require(primary is not None and record['text']['translation'] == primary['text'], 'Primary text differs from its own language reading')
        require(record['text']['arabic'] == own.get('ara', {}).get('text'), 'Arabic compatibility text differs from its own reading')
        availability = record['source'].get('language_availability')
        if availability is not None:
            catalog_names = {item['name'] for item in self.catalog[book]['collection']}
            unpublished = {source.LANGUAGES[p][0]: p for p in source.LANGUAGES
                           if p + '-' + book not in catalog_names}
            require(set(availability) == {source.LANGUAGES[p][0] for p in requested_languages} | set(unpublished),
                    'Missing configured or catalog-unavailable language state')
            for code, prefix in unpublished.items():
                require(prefix not in own and prefix + '-' + book not in self.datasets
                        and availability[code] == 'edition_not_published_in_pinned_catalog',
                        'A catalog-unavailable language was invented or marked as fetched/pending')
                self.by_language[code]['edition_not_published_in_pinned_catalog'] += 1
            for prefix in requested_languages:
                code = source.LANGUAGES[prefix][0]
                if prefix in own:
                    if own[prefix].get('quotation_status') == 'content_mismatch':
                        expected = 'provider_content_mismatch'
                    else:
                        expected = 'boundary_pending_source_context' if own[prefix].get('text') is None else 'available'
                elif prefix + '-' + book not in self.datasets:
                    expected = 'edition_pending'
                elif prefix not in original_group:
                    expected = 'provider_entry_absent'
                else:
                    raw = self.row(book, prefix, original_group[prefix][0])['text']
                    expected = 'narration_prefix_absent' if raw.strip() else 'source_text_empty'
                require(availability[code] == expected, 'Incorrect empty/missing/source-context state for ' + identifier + ':' + code)
                self.by_language[code][expected] += 1
        self.accepted[identifier] = {version['id']: version_fingerprint(version) for version in own.values()}

    def run(self):
        processed = self.progress['by_book']
        for manifest_path in sorted((self.root / 'materials').glob('fawaz-*/manifest.json')):
            manifest = parse_json(manifest_path.read_text(encoding='utf-8'))
            index_path = local(self.root, manifest['source']['path'])
            index_raw = index_path.read_bytes()
            require(source.sha(index_raw) == manifest['source']['sha256'], 'Material source-index hash mismatch')
            index = parse_json(index_raw.decode('utf-8'))
            book = index['provider_book']
            require(index['revision'] == source.REVISION and book in processed, 'Material belongs to an unprocessed source book')
            prefixes = processed[book].get('processed_languages') or list(index['edition_metadata'])
            require(set(index['source_snapshots']) == set(source.DOCUMENTS) | {
                'editions/' + prefix + '-' + book + '.json' for prefix in prefixes},
                'Material source index omits a processed language or source document')
            require(set(index['edition_metadata']) == set(prefixes), 'Material source index has the wrong edition catalog entries')
            for prefix in prefixes:
                require(same(index['edition_metadata'][prefix], source.edition_metadata(self.catalog, book, prefix)),
                        'Material source index changed language catalog metadata')
            require(manifest['book'] == source.BOOKS[book][0], 'Material collection does not match its source index')
            expected_paths = set()
            for key, descriptor in index['source_snapshots'].items():
                require(key in self.inputs and same(descriptor, self.inputs[key]), 'Material source index changed a saved snapshot descriptor')
                expected_paths.add(descriptor['path'])
            supporting = manifest['supporting_files']
            require(len({item['path'] for item in supporting}) == len(supporting)
                    and {item['path'] for item in supporting} == expected_paths, 'Material source dependency set is incomplete or duplicated')
            saved_by_path = {value['path']: value for value in self.inputs.values()}
            for item in supporting:
                descriptor = saved_by_path[item['path']]
                require(item['sha256'] == descriptor['stored_sha256'] and item['size_bytes'] == descriptor['stored_bytes']
                        and item.get('original_response_sha256') == descriptor['sha256'] and item.get('compression') == 'gzip',
                        'Material supporting-source checksum declaration mismatch')
            self.sizes.append(local(self.root, manifest['records']['path']).stat().st_size)
            self.counts['registry_materials'] += 1
            requested = processed[book].get('requested_languages') or index.get('requested_languages') or list(index['edition_metadata'])
            for record in manifest_records(self.root, manifest):
                try:
                    require(record['language'] == manifest['language'] and record['edition'] == manifest['edition'],
                            'Material primary language or storage edition differs from its canonical records')
                    self.record(record, book, requested)
                except (ValueError, KeyError, TypeError, IndexError) as error:
                    raise ValueError(str(record.get('id')) + ': ' + str(error)) from error
        expected_ids = {identity(book, number) for book, number in self.groups if book in processed}
        for book in processed:
            held_path = local(self.root, source.IMPORT + '/held/' + book + '.jsonl.gz')
            with gzip.open(held_path, 'rt', encoding='utf-8') as stream:
                for line in stream:
                    item = parse_json(line)
                    number = item['typed_hadithnumber']
                    identifier = identity(book, number)
                    require(identifier not in self.accepted and identifier not in self.held and item['show_in_html_hadith'] is False,
                            'Held occurrence is duplicated or was promoted without changing its disposition')
                    group = self.groups[(book, number)]
                    require(set(item['source_versions']) == set(group), 'Held occurrence lost a source language')
                    empty = True
                    for prefix, versions in item['source_versions'].items():
                        require(sorted(value['position'] for value in versions) == group[prefix], 'Held occurrence lost or duplicated a source row')
                        descriptor = self.inputs['editions/' + prefix + '-' + book + '.json']
                        for value in versions:
                            original = self.row(book, prefix, value['position'])
                            require(same(value['row'], original) and value['source_path'] == descriptor['path']
                                    and value['source_sha256'] == descriptor['sha256'], 'Held source row or source binding changed')
                            verify_partition(original['text'], value['text_spans'])
                            empty = empty and not original['text'].strip()
                            self.counts['verified_held_source_rows'] += 1
                    self.counts['held_all_source_texts_empty' if empty else 'held_with_nonempty_source_text'] += 1
                    self.held[identifier] = item['classification'].get('reason', 'reason_not_supplied')
            with gzip.open(local(self.root, source.IMPORT + '/classification/' + book + '.jsonl.gz'), 'rt', encoding='utf-8') as stream:
                for line in stream:
                    item = parse_json(line)
                    identifier = identity(book, item['typed_hadithnumber'])
                    require(identifier not in self.ledgers, 'Duplicate classification ledger identity')
                    status = item['classification']['classification']
                    require((status == 'hadith' and identifier in self.accepted) or (status == 'held' and identifier in self.held),
                            'Classification ledger disagrees with material/held disposition')
                    self.ledgers[identifier] = {'status': status, 'reason': item['classification'].get('reason')}
        require(set(self.accepted) | set(self.held) == expected_ids == set(self.ledgers), 'Source occurrence coverage has omissions or additions')
        require(len(self.accepted) == self.progress['registered_occurrences'] and len(self.held) == self.progress['held_occurrences']
                and len(expected_ids) == self.progress['provider_occurrences'], 'Progress counts differ from exact source occurrence inventory')
        for key in ('held_all_source_texts_empty', 'held_with_nonempty_source_text', 'registry_materials',
                    'verified_language_readings', 'verified_held_source_rows', 'source_note_spans', 'disjoint_quotation_readings'):
            self.counts.setdefault(key, 0)
        return {**dict(self.counts), 'status': 'passed', 'source_revision': source.REVISION,
                'registered_occurrences': len(self.accepted), 'held_occurrences': len(self.held),
                'provider_occurrences': len(expected_ids), 'largest_canonical_shard_bytes': max(self.sizes, default=0),
                'held_reasons_as_supplied': dict(collections.Counter(self.held.values())),
                'languages': {code: dict(counts) for code, counts in self.by_language.items()},
                'acquisition_complete': self.progress['complete'],
                'scope': 'Exact source fidelity and accounting only; held nonempty text is not automatically classified as non-hadith.',
                'independent_authenticity_assessment': False}


def reconcile(audit, previous_root):
    previous_root = previous_root.resolve()
    previous_state = read_json(previous_root, source.IMPORT + '/state.json')
    for key, descriptor in previous_state['inputs'].items():
        require(descriptor.get('source_path') == key and key in audit.inputs, 'A previous source input disappeared')
        source.checked_snapshot(previous_root, descriptor)
        require(descriptor['sha256'] == audit.inputs[key]['sha256'] and descriptor['stored_sha256'] == audit.inputs[key]['stored_sha256'],
                'Original source bytes were changed between exports')
    previous, details = {}, {}
    for path in sorted((previous_root / source.IMPORT / 'classification').glob('*.jsonl.gz')):
        book = path.name.removesuffix('.jsonl.gz')
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            for line in stream:
                item = parse_json(line)
                identifier = identity(book, item['typed_hadithnumber'])
                require(identifier not in previous, 'Duplicate previous ledger identity')
                previous[identifier] = {'status': item['classification']['classification'], 'reason': item['classification'].get('reason')}
    require(set(previous) <= set(audit.ledgers), 'A previous provider occurrence is missing from the new export')
    for path in sorted((previous_root / 'materials').glob('fawaz-*/manifest.json')):
        manifest = parse_json(path.read_text(encoding='utf-8'))
        for record in manifest_records(previous_root, manifest):
            require(record['id'] not in details and previous.get(record['id'], {}).get('status') == 'hadith',
                    'Previous material inventory disagrees with its classification ledger')
            details[record['id']] = {version['id']: version_fingerprint(version) for version in record['language_versions']}
    previous_progress = read_json(previous_root, source.IMPORT + '/progress.json')
    require(len(details) == previous_progress['registered_occurrences']
            and sum(value['status'] == 'held' for value in previous.values()) == previous_progress['held_occurrences']
            and len(previous) == previous_progress['provider_occurrences'], 'Previous checkpoint counts differ from its source ID inventory')
    original_held, demoted, language_changes = [], [], []
    for identifier, old in previous.items():
        current = audit.ledgers[identifier]
        transition = {'id': identifier, 'previous_status': old['status'], 'previous_reason': old['reason'],
                      'current_status': current['status'], 'current_reason': current['reason']}
        if old['status'] == 'held':
            original_held.append(transition)
        elif current['status'] == 'held':
            demoted.append(transition)
        if identifier in details and identifier in audit.accepted:
            for version_id, old_version in details[identifier].items():
                new_version = audit.accepted[identifier].get(version_id)
                if new_version != old_version:
                    language_changes.append({'id': identifier, 'language_version_id': version_id,
                                             'previous': old_version, 'current': new_version})
    return {'previous_provider_occurrences': len(previous),
            'previous_registered': sum(value['status'] == 'hadith' for value in previous.values()),
            'previous_held': len(original_held),
            'previous_held_now_registered': sum(value['current_status'] == 'hadith' for value in original_held),
            'previous_held_still_held': sum(value['current_status'] == 'held' for value in original_held),
            'previous_registered_now_held_count': len(demoted),
            'previous_registered_language_changes_count': len(language_changes),
            'original_held_reconciliation': original_held,
            'previous_registered_now_held': demoted,
            'previous_registered_language_changes': language_changes,
            'new_provider_ids': sorted(set(audit.ledgers) - set(previous))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--compare-root', type=Path, help='Previous verified export for complete occurrence-ID reconciliation')
    parser.add_argument('--output', type=Path, help='Write the complete JSON audit, including every previous held ID when comparing')
    args = parser.parse_args(argv)
    try:
        audit = SourceAudit(args.root)
        result = audit.run()
        if args.compare_root:
            result['comparison'] = reconcile(audit, args.compare_root)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_name(args.output.name + '.tmp')
            temporary.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8')
            temporary.replace(args.output)
        summary = {key: value for key, value in result.items() if key != 'comparison'}
        if 'comparison' in result:
            summary['comparison'] = {key: value for key, value in result['comparison'].items() if not isinstance(value, list)}
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, IndexError, OSError, EOFError) as error:
        print('Fawaz source validation failed: ' + str(error)[:1000], file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
