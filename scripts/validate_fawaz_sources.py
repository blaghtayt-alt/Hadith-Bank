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
        self.reviewed = source.reviewed_source_spans(root)
        self.review_files, self.relative_checks, self.relative_readings = {}, [], {}
        self.relative_source_keys = set()
        for decision in self.reviewed.values():
            relation = decision.get('source_reference')
            if not relation:
                continue
            book = decision['provider_book']
            for binding in (relation['parent_source'], relation.get('independent_terminal')):
                if binding:
                    prefix = binding['provider_edition'].split('-', 1)[0]
                    self.relative_source_keys.add((book, prefix, binding['typed_hadithnumber']))
            for evidence in relation.get('reference_evidence', []):
                binding = evidence['source']
                prefix = binding['provider_edition'].split('-', 1)[0]
                self.relative_source_keys.add((book, prefix, binding['typed_hadithnumber']))
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

    def relative_source(self, binding, expected=None, default_edition=None):
        """Bind review evidence to an immutable saved row, never an array join."""
        edition = binding.get('provider_edition', binding.get('edition', default_edition))
        require(isinstance(edition, str) and '-' in edition, 'Relative evidence lacks its own edition')
        prefix, book = edition.split('-', 1)
        key = (book, prefix, binding['typed_hadithnumber'])
        require(expected is None or key == expected, 'Relative evidence belongs to another source occurrence')
        require(binding.get('provider_book', book) == book, 'Relative evidence changed provider book')
        path = 'editions/' + edition + '.json'
        require(path in self.inputs and edition in self.datasets, 'Relative evidence source was not acquired')
        descriptor = self.inputs[path]
        position = binding['source_position']
        original = self.row(book, prefix, position)
        require(source.typed_identity(original['hadithnumber']) == key[2], 'Relative evidence changed typed source identity')
        require(self.groups.get((book, key[2]), {}).get(prefix) == [position],
                'Relative evidence has a missing or ambiguous source identity')
        require(binding['source_path'] in (path, descriptor['path'])
                and binding['source_raw_sha256'] == descriptor['sha256']
                and binding['source_text_sha256'] == source.sha(original['text'].encode()),
                'Relative evidence source hash or path mismatch')
        pointers = [binding[name] for name in ('json_pointer', 'source_json_pointer') if name in binding]
        urls = [binding[name] for name in ('provider_url', 'source_url') if name in binding]
        require(pointers and all(value == '/hadiths/' + str(position) + '/text' for value in pointers),
                'Relative evidence source pointer mismatch')
        require(urls and all(value == descriptor['url'] for value in urls), 'Relative evidence source URL mismatch')
        if 'reference_as_supplied' in binding:
            require(same(binding['reference_as_supplied'], original['reference']), 'Relative evidence changed source reference')
        return key, original

    def relative_span(self, evidence, expected=None, quotation_spans=None, default_edition=None):
        binding = evidence.get('source', evidence)
        key, original = self.relative_source(binding, expected, default_edition)
        spans = check_spans([evidence['span']], len(original['text']), 'Relative evidence span')
        require(len(spans) == 1 and evidence['text'] == original['text'][spans[0][0]:spans[0][1]],
                'Relative evidence text differs from its exact source span')
        if quotation_spans is not None:
            require(any(start <= spans[0][0] < spans[0][1] <= end for start, end in quotation_spans),
                    'Relative evidence lies outside the bounded narration')
        return key, spans[0]

    def relative_review_file(self, locator):
        require(locator.get('compression') == 'gzip' and locator.get('format') == 'jsonl',
                'Unsupported relative review evidence format')
        path = locator['path']
        hashes = (locator['stored_sha256'], locator['raw_sha256'])
        if path not in self.review_files:
            stored = local(self.root, path).read_bytes()
            require(source.sha(stored) == hashes[0], 'Relative review evidence stored hash mismatch')
            raw = gzip.decompress(stored)
            require(source.sha(raw) == hashes[1], 'Relative review evidence raw hash mismatch')
            rows = [parse_json(line) for line in raw.decode('utf-8').splitlines()]
            self.review_files[path] = (hashes, rows)
            self.counts['verified_relative_review_files'] += 1
        saved_hashes, rows = self.review_files[path]
        require(hashes == saved_hashes, 'Relative review file descriptors disagree')
        line = locator['line']
        require(type(line) is int and 1 <= line <= len(rows), 'Relative review evidence line is out of bounds')
        return rows[line - 1]

    def verify_relative_reference(self, book, version, original, partition):
        """Verify reviewed relation evidence and display; do not infer a new link."""
        edition = version['source']['provider_edition']
        prefix = edition.split('-', 1)[0]
        child = (book, prefix, source.typed_identity(original['hadithnumber']))
        decision = self.reviewed.get(child, {})
        relation = decision.get('source_reference')
        extra = version['references'][1:]
        if not relation:
            require(not extra and version.get('quotation_status') != 'abbreviated_source_report',
                    'A relative reference has no hash-bound reviewed decision')
            return
        self.relative_source(decision, child)
        require(decision.get('quotation_kind') == 'source_explicit_abbreviated_transmission'
                and decision.get('classification') == 'source_attributed_prophetic_narration'
                and all(decision.get(key) is False for key in ('canonical_identity_inferred',
                           'parent_text_inserted', 'independent_authenticity_assessment')),
                'Relative decision changed its limited source-attribution scope')
        require(same(decision['quotation_spans'], partition['quotation_spans'])
                and decision['quotation_sha256'] == source.sha(partition['quotation'].encode()),
                'Relative quotation differs from its hash-bound reviewed span')
        require(version.get('scope') == 'source_excerpt'
                and version.get('quotation_status') == 'abbreviated_source_report'
                and version['source'].get('quotation_kind') == decision['quotation_kind'],
                'Relative narration lacks its visible abbreviated-source qualification')
        require(relation.get('relation') == 'source_explicit_previous_report_variant', 'Unknown reviewed source relation')
        parent_binding = relation['parent_source']
        parent = (book, prefix, parent_binding['typed_hadithnumber'])
        _, parent_row = self.relative_source(parent_binding, parent)
        parent_spans = check_spans(parent_binding['quotation_spans'], len(parent_row['text']), 'Relative parent quotation spans')
        require(parent != child and parent_spans and parent_binding['source_position'] + 1 == decision['source_position']
                and same(parent_row['reference'].get('book'), original['reference'].get('book')),
                'Relative parent is not the reviewed preceding source row in its own section')
        self.relative_checks.append((parent, parent_spans, True))
        own_evidence = []
        for evidence in relation['reference_evidence']:
            binding = evidence['source']
            if set(binding) == {'provider_edition', 'typed_hadithnumber'}:
                require(binding == {'provider_edition': edition, 'typed_hadithnumber': child[2]},
                        'Compact relative citation borrowed another language or occurrence')
                checked = {**evidence, 'source': decision}
            else:
                checked = evidence
            evidence_prefix, evidence_book = binding['provider_edition'].split('-', 1)
            key, span = self.relative_span(checked, (book, evidence_prefix, child[2]),
                                          partition['quotation_spans'] if evidence_prefix == prefix else None)
            require(evidence_book == book, 'Relative reference crosses provider collections')
            self.relative_checks.append((key, [span], False))
            if key == child:
                own_evidence.append(evidence)
        require(len(own_evidence) == 1, 'Relative citation must have exactly one own-language source cue')
        parent_number = parse_json(parent[2])
        expected = {'collection': source.BOOKS[book][1], 'number': str(parent_number),
                    'source_citation': own_evidence[0]['text'],
                    'url': source.entry_url(parent_binding['provider_edition'], parent_number),
                    'scope': 'source_explicit_previous_report_variant', 'numbering_system': 'fawaz_api_hadithnumber',
                    'canonical_mapping_status': 'not_inferred',
                    'relation_evidence': 'Source wording, named chain and observed source order checked together',
                    'identity_merged': False, 'parent_text_inserted': False}
        require(same(extra, [expected]), 'Displayed relative reference changed citation, URL, identity or scope')
        if 'review_evidence_locator' in decision:
            proof = self.relative_review_file(decision['review_evidence_locator'])
            self.relative_source(proof, child)
            require(proof.get('status') == 'reviewed_relative_reference_proposal'
                    and proof.get('antecedent_text_inserted') is False
                    and proof.get('canonical_identity_inferred') is False
                    and [proof['quotation_span']] == partition['quotation_spans'], 'Relative review ledger row or scope mismatch')
            path = relation['dependency_path']
            terminal_binding = relation['independent_terminal']
            terminal = (book, prefix, terminal_binding['typed_hadithnumber'])
            require(isinstance(path, list) and len(path) >= 2 and all(isinstance(v, str) for v in path)
                    and len(path) == len(set(path)) and path[:2] == [child[2], parent[2]]
                    and path[-1] == terminal[2] and terminal_binding['provider_edition'] == edition
                    and proof['dependency_path'] == path and proof['independent_terminal'] == terminal[2],
                    'Relative dependency path changed or contains a cycle')
            for index in range(1, len(path) - 1):
                link = self.reviewed.get((book, prefix, path[index]), {}).get('source_reference', {})
                target = link.get('parent_source', {})
                require(target.get('provider_edition') == edition and target.get('typed_hadithnumber') == path[index + 1],
                        'Relative dependency path contains an unreviewed intermediate link')
            require(not self.reviewed.get(terminal, {}).get('source_reference'), 'Relative terminal depends on another relative link')
            self.relative_source(proof['antecedent'], parent, edition)
            require(same(proof['antecedent']['same_declared_section'], original['reference']['book'])
                    and proof['source_order'] == 'previous_source_row_not_numeric_adjacency', 'Relative source-order evidence changed')
            key, span = self.relative_span(proof['reference_evidence'], child, partition['quotation_spans'])
            require(span == own_evidence[0]['span'] and proof['reference_evidence']['text'] == own_evidence[0]['text'],
                    'Compact relative citation disagrees with its immutable review ledger')
            self.relative_span(proof['child_chain_evidence'], child, partition['quotation_spans'])
            self.relative_span(proof['antecedent_chain_evidence'], parent, parent_spans)
            key, span = self.relative_span(proof['independent_terminal_evidence'], terminal)
            require(proof['independent_terminal_evidence'].get('independent_of_relative_reference_chain') is True
                    and proof['independent_terminal_evidence'].get('independent_authenticity_assessment') is False,
                    'Relative terminal proof changed its independent attribution scope')
            self.relative_checks.append((key, [span], False))
            if proof.get('source_local_alias_evidence'):
                key, _ = self.relative_span(proof['source_local_alias_evidence'])
                require(key[:2] == child[:2], 'Named-chain alias evidence belongs to another edition')
            boundaries = proof['current_language_boundaries']
            for language, boundary in boundaries.items():
                _, raw_row = self.relative_source(boundary['source'], (book, language, child[2]))
                result = verify_partition(raw_row['text'], {'quotation_spans': boundary['quotation_spans'], 'notes': boundary['note_spans']})
                require(boundary['quotation_sha256'] == source.sha(result['quotation'].encode()), 'Relative review language-boundary hash mismatch')
            if proof.get('additional_content_reference'):
                evidence = proof['additional_content_reference']
                own_prefix = evidence['edition'].split('-', 1)[0]
                self.relative_span(evidence, (book, own_prefix, child[2]), boundaries[own_prefix]['quotation_spans'])
            review = proof['source_review']
            require(all(review.get(key) is False for key in ('source_identity_merged', 'parent_text_inserted',
                                                             'independent_authenticity_assessment')),
                    'Relative review ledger asserts identity, completion or certification')
        else:
            chain = relation['named_chain_evidence']
            self.relative_span(chain['child_node'], child, partition['quotation_spans'])
            self.relative_span(chain['parent_node'], parent, parent_spans)
            self.relative_span(chain['parent_continuation'], parent, parent_spans)
            if chain.get('source_explicit_name_equivalence'):
                key, _ = self.relative_span(chain['source_explicit_name_equivalence'])
                require(key[:2] == child[:2], 'Named-chain alias evidence belongs to another edition')
            self.relative_span(relation['parent_prophetic_attribution'], parent, parent_spans)
            order = relation['observed_order_evidence']
            require(order['source_language'] == prefix and order['parent_position'] == parent_binding['source_position']
                    and order['child_position'] == decision['source_position']
                    and order['adjacent_in_pinned_source_array'] is True
                    and same(order['same_supplied_section'], original['reference']['book']), 'Relative observed-order evidence changed')
            for role, number in (('parent', parent[2]), ('child', child[2])):
                name = 'corroborating_english_' + role + '_position'
                if name in order:
                    require(source.typed_identity(self.row(book, 'eng', order[name])['hadithnumber']) == number,
                            'Relative corroborating language position identifies another occurrence')
        self.counts['verified_relative_references'] += 1

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
        self.verify_relative_reference(book, version, original, partition)
        source_key = (book, prefix, source.typed_identity(original['hadithnumber']))
        if source_key in self.relative_source_keys and not pending:
            self.relative_readings[source_key] = partition['quotation_spans']
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
        require(record['references'].get('canonical_mapping_status') == 'not_inferred'
                and same(record['references']['items'], [reference for version in record['language_versions'] for reference in version['references']]),
                'Occurrence references differ from their own-language citations')
        if primary and primary.get('quotation_status') == 'abbreviated_source_report':
            require(record['extraction'].get('is_excerpt') is True, 'Abbreviated primary source report is not marked as an excerpt')
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
        for key, spans, exact in self.relative_checks:
            actual = self.relative_readings.get(key)
            require(actual and (same(actual, spans) if exact else all(
                any(start <= left < right <= end for start, end in actual) for left, right in spans)),
                'Relative evidence target is absent, held, or outside its registered narration: ' + str(key))
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
