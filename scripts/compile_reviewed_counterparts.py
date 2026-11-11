#!/usr/bin/env python3
"""Compile explicit occurrence reviews into a new immutable counterpart bundle.

Preparation never approves a match. This compiler checks each review against
current canonical sources, exact pinned target bytes and independent language
decisions. It appends one authorized bundle; it never edits an older bundle.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from counterpart_review import (CONTRACT, LANGUAGES, QUEUE_SCHEMA, canonical,
    checked_asset, descriptor, load_source_records, local, object_hash, read_rows,
    require, rows_bytes, source_binding, validate_review_evidence,
    validate_source_binding, validate_language_decisions)
from prepare_counterpart_review import collect_targets
from resolve_counterparts import CounterpartResolver
from reviewed_counterparts import MANIFEST, SCHEMA, ReviewedCounterpartResolver

COMPONENT = re.compile(r'[a-z0-9][a-z0-9._-]{0,119}\Z')


def _unique(rows, key, label):
    values = {}
    for row in rows:
        identifier = row.get(key)
        require(isinstance(identifier, str) and identifier and identifier not in values,
                'Duplicate or missing ' + label)
        values[identifier] = row
    return values


def _path(root, value):
    candidate = Path(value)
    return candidate if candidate.is_absolute() else root / candidate


def compile_reviews(root, queue, reviews, bundle_id, snapshot, publication_basis,
                    source_name='Reviewed Arabic and English source parallels', check_only=False):
    root = Path(root).resolve()
    require(COMPONENT.fullmatch(bundle_id or '') and COMPONENT.fullmatch(snapshot or ''),
            'Bundle ID and snapshot must be safe version identifiers')
    require(isinstance(publication_basis, str) and publication_basis.strip(),
            'Record the existing owner authorization for this exact source scope')
    require(isinstance(source_name, str) and source_name.strip(), 'Bundle needs a source name')
    queue_path, reviews_path = _path(root, queue), _path(root, reviews)
    if queue_path.is_dir():
        queue_path /= 'manifest.json'
    queue_raw, review_raw = queue_path.read_bytes(), reviews_path.read_bytes()
    prepared = json.loads(queue_raw)
    require(prepared.get('schema') == QUEUE_SCHEMA and prepared.get('status') == 'candidates_only'
            and prepared.get('publication_ready') is False,
            'Compiler requires an explicitly unapproved preparation manifest')
    queue_rows = _unique(read_rows(checked_asset(queue_path.parent, prepared['queue']), compressed=True),
                         'record_id', 'prepared occurrence')
    targets = _unique(read_rows(checked_asset(queue_path.parent, prepared['targets']), compressed=True),
                      'target_key', 'prepared target')
    for item in prepared.get('input_assets', []):
        checked_asset(root, item)
    reviews_rows = read_rows(review_raw, compressed=reviews_path.suffix == '.gz')
    decisions = _unique(reviews_rows, 'record_id', 'review occurrence')
    require(decisions, 'Review file is empty')
    records = _unique(load_source_records(root), 'id', 'registered occurrence')
    resolver = CounterpartResolver(root, list(records.values()))
    current_targets, current_assets = collect_targets(root, list(records.values()), resolver, prepared['profile'])
    entries, mappings, review_inputs, source_assets = {}, [], {}, {}
    counts = Counter({'submitted': len(decisions), 'verified': 0, 'unresolved': 0, 'rejected': 0,
                      'arabic_text': 0, 'arabic_external': 0, 'english_text': 0, 'english_external': 0})
    validator = ReviewedCounterpartResolver.__new__(ReviewedCounterpartResolver)
    for identifier, decision in sorted(decisions.items()):
        record = records.get(identifier)
        require(record is not None and identifier in queue_rows,
                'Review occurrence is absent from the registered prepared scope: ' + identifier)
        validate_source_binding(record, decision)
        validate_source_binding(record, queue_rows[identifier])
        status = decision.get('status')
        require(status in ('verified', 'unresolved', 'rejected'), 'Unsupported review decision status')
        counts[status] += 1
        if status != 'verified':
            require(isinstance(decision.get('reason'), str) and decision['reason'].strip(),
                    'Unresolved or rejected decisions need a reason')
            continue
        for existing_bundle, _ in resolver.reviewed.mappings.get(identifier, []):
            require(existing_bundle == bundle_id,
                    'Occurrence already has a reviewed assignment; preserve it and use a separately reviewed supplement: '
                    + identifier)
        key = decision.get('target_key')
        target, current = targets.get(key), current_targets.get(key)
        require(target is not None and current is not None,
                'Reviewed target is not in the prepared, locally verifiable source inventory')
        require(target.get('candidate_only') is True and
                object_hash(target.get('entry')) == target.get('target_entry_sha256') ==
                decision.get('target_entry_sha256') == current.get('target_entry_sha256'),
                'Stale or modified complete review target binding')
        base_entry = target['entry']
        validator._validate_entry(base_entry, strict=True)
        require(decision.get('relation') in ('source_excerpt', 'same_narration'),
                'Review must distinguish a source excerpt from the same narration')
        review = copy.deepcopy(decision.get('review'))
        validate_review_evidence(review, record, base_entry)
        review['status'] = 'verified'
        entry = validate_language_decisions(base_entry, decision.get('language_decisions'), review, key)
        # The content hash makes distinct language/variant decisions distinct.
        entry['id'] = 'reviewed-' + object_hash(entry)
        validator._validate_entry(entry, strict=True)
        mapping = {**source_binding(record, decision['source_text_field']),
            'target_id': entry['id'], 'target_entry_sha256': object_hash(entry),
            'target_text_sha256': {language: (entry[language] or {}).get('text_sha256')
                                   for language in LANGUAGES},
            'review_target_key': key, 'review_target_entry_sha256': target['target_entry_sha256'],
            'relation': decision['relation'], 'review': review,
            'language_decisions': copy.deepcopy(decision['language_decisions'])}
        validator._validate_mapping(mapping, {entry['id']: entry}, strict=True, review_targets={key: target})
        entries[entry['id']] = entry
        mappings.append(mapping)
        review_inputs[key] = target
        for path in current.get('input_assets', []):
            require(path in current_assets, 'Target source is not checksum pinned')
            source_assets[path] = current_assets[path]
        for path in (record['source']['original_file'], record['source']['record_locator']['path']):
            source_assets[path] = descriptor(root, path)
        for language in LANGUAGES:
            item = entry[language]
            if item is not None:
                counts[language + ('_text' if item.get('text') else '_external')] += 1
    result = {'bundle_id': bundle_id, 'snapshot': snapshot, 'evidence_contract': CONTRACT,
              'check_only': check_only, 'source_text_modified': False,
              'independent_authenticity_certification': False, **dict(counts)}
    require(mappings, 'No verified mappings; keep these decisions in the review backlog')
    base = 'sources/counterparts/reviewed/' + bundle_id + '/' + snapshot
    payload = {
        'entries.jsonl.gz': rows_bytes([entries[key] for key in sorted(entries)]),
        'mappings.jsonl.gz': rows_bytes(mappings),
        'review-targets.jsonl.gz': rows_bytes([review_inputs[key] for key in sorted(review_inputs)]),
        'prepared-source-bindings.jsonl.gz': rows_bytes([queue_rows[key] for key in sorted(decisions)]),
        'preparation-manifest.json': queue_raw,
        'review-decisions-original.jsonl' + ('.gz' if reviews_path.suffix == '.gz' else ''): review_raw,
    }

    def output_asset(filename):
        raw = payload[filename]
        return {'path': base + '/' + filename, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    for filename in payload:
        if filename not in ('entries.jsonl.gz', 'mappings.jsonl.gz', 'review-targets.jsonl.gz'):
            source_assets[base + '/' + filename] = output_asset(filename)
    bundle = {'id': bundle_id, 'provider': 'hadith-bank-reviewed-source-alignment',
        'source_name': source_name, 'source_snapshot': snapshot, 'evidence_contract': CONTRACT,
        'publication': {'authorized': True, 'basis': publication_basis,
                        'independent_qc_asserted': False, 'rights_clearance_asserted': False},
        'entries': output_asset('entries.jsonl.gz'), 'mappings': output_asset('mappings.jsonl.gz'),
        'review_targets': output_asset('review-targets.jsonl.gz'),
        'source_assets': [source_assets[path] for path in sorted(source_assets)],
        'coverage': dict(counts), 'new_translations_created': False}
    manifest_path = local(root, MANIFEST)
    previous = manifest_path.read_bytes() if manifest_path.exists() else None
    manifest = json.loads(previous) if previous is not None else {'schema': SCHEMA, 'bundles': []}
    require(manifest.get('schema') == SCHEMA and isinstance(manifest.get('bundles'), list),
            'Existing reviewed source registry is invalid')
    existing = [item for item in manifest['bundles'] if item.get('id') == bundle_id]
    destination = local(root, base)
    if existing:
        require(len(existing) == 1 and existing[0] == bundle,
                'Bundle ID already exists with different content; use a new versioned bundle ID')
        require(destination.is_dir() and {item.name for item in destination.iterdir()} == set(payload)
                and all((destination / filename).read_bytes() == raw for filename, raw in payload.items()),
                'Existing immutable bundle differs from the reviewed compilation')
        return {**result, 'status': 'already_compiled', 'bundle_path': base}
    require(not destination.exists(), 'Refusing to replace an existing immutable bundle folder')
    if check_only:
        return {**result, 'status': 'validated', 'bundle_path': base}
    manifest['bundles'].append(bundle)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.review-bundle-', dir=destination.parent))
    registry_temp = None
    lock_path, lock_descriptor = manifest_path.parent / '.counterpart-compile.lock', None
    try:
        for filename, raw in payload.items():
            (staging / filename).write_bytes(raw)
        try:
            lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise ValueError('Another counterpart compilation owns the registry lock; inspect it before retrying') from None
        os.write(lock_descriptor, canonical({'pid': os.getpid(), 'bundle_id': bundle_id, 'snapshot': snapshot}) + b'\n')
        # Recheck the registry immediately before the append; concurrent imports
        # must be re-read and recompiled, never overwritten.
        require((manifest_path.read_bytes() if manifest_path.exists() else None) == previous,
                'Reviewed source registry changed during compilation; retry from fresh inputs')
        staging.rename(destination)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix='.review-manifest-', dir=manifest_path.parent, delete=False) as handle:
            registry_temp = Path(handle.name)
            handle.write(canonical(manifest) + b'\n')
        registry_temp.replace(manifest_path)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if registry_temp is not None and registry_temp.exists():
            registry_temp.unlink()
        if lock_descriptor is not None:
            os.close(lock_descriptor)
            lock_path.unlink()
    return {**result, 'status': 'compiled', 'bundle_path': base}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--queue', required=True, help='Generated queue folder or manifest.json')
    parser.add_argument('--reviews', required=True, help='Separate reviewed JSONL or JSONL.gz sidecar')
    parser.add_argument('--bundle-id', required=True)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--publication-basis', required=True, help='Existing owner authorization and exact scope')
    parser.add_argument('--source-name', default='Reviewed Arabic and English source parallels')
    parser.add_argument('--check-only', action='store_true')
    args = vars(parser.parse_args(argv))
    try:
        result = compile_reviews(**args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Counterpart compilation failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
