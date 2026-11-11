"""Consume explicit, source-bound narration alignments; never guess a match.

This adapter does not perform a translation or a scholarly review. It accepts
only reviewed mapping evidence pinned to the exact source and target bytes.
Candidate and unresolved mappings never supply text. A language may provide a
verified external source link without supplying (or claiming to supply) text.
"""
from collections import defaultdict
import copy
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

from counterpart_review import (CONTRACT, object_hash,
                                validate_language_decisions, validate_review_evidence, validate_source_binding)


MANIFEST = 'sources/counterparts/reviewed/manifest.json'
SCHEMA = 'hadith-bank-reviewed-counterpart-sources-v1'
LINK_SCHEMA = 'hadith-bank-counterpart-link-v1'
LANGUAGES = ('arabic', 'english')


def text_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _required_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Reviewed counterpart requires ' + label)
    return value


def _safe_url(value):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme in ('https', 'http') and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None)
    except ValueError:
        return False


def _local(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe reviewed counterpart source path')
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != relative:
        raise ValueError('Unsafe reviewed counterpart source path: ' + relative)
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError('Symlink reviewed counterpart source path: ' + relative)
    if not target.resolve().is_relative_to(root):
        raise ValueError('Reviewed counterpart source path escapes bank')
    return target


def _citation(references, language):
    if not references:
        return '[رقم المصدر غير مذكور]' if language == 'arabic' else '[Source number not supplied]'
    labels = []
    for item in references:
        name = item.get('collection_ar') if language == 'arabic' else item.get('collection')
        name = name or item.get('collection') or item['book_key']
        labels.append(name + ('، رقم ' if language == 'arabic' else ' no. ') + str(item['number']))
    return '[' + '; '.join(labels) + ']'


class ReviewedCounterpartResolver:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.enabled = (self.root / MANIFEST).is_file()
        self.assets, self.bundles = {}, {}
        self.mappings = defaultdict(list)
        if not self.enabled:
            return
        manifest_path = _local(self.root, MANIFEST)
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw)
        if manifest.get('schema') != SCHEMA or not isinstance(manifest.get('bundles'), list):
            raise ValueError('Unrecognized reviewed counterpart manifest')
        self.assets[MANIFEST] = hashlib.sha256(raw).hexdigest()
        for bundle in manifest['bundles']:
            identifier = _required_text(bundle.get('id'), 'bundle id')
            if identifier in self.bundles:
                raise ValueError('Duplicate reviewed counterpart bundle: ' + identifier)
            if (bundle.get('publication') or {}).get('authorized') is not True:
                continue
            for name in ('provider', 'source_name', 'source_snapshot'):
                _required_text(bundle.get(name), name)
            contract = bundle.get('evidence_contract')
            if contract not in (None, CONTRACT):
                raise ValueError('Unsupported reviewed counterpart evidence contract')
            strict = contract == CONTRACT
            source_assets = bundle.get('source_assets')
            if not isinstance(source_assets, list) or not source_assets:
                raise ValueError('Reviewed counterpart bundle requires immutable source assets')
            for asset in source_assets:
                self._asset(asset)
            entries = {}
            for entry in self._rows(bundle['entries']):
                target = _required_text(entry.get('id'), 'target entry id')
                if target in entries:
                    raise ValueError('Duplicate reviewed counterpart target: ' + target)
                self._validate_entry(entry, strict=strict)
                entries[target] = entry
            review_targets = {}
            if strict:
                for item in self._rows(bundle['review_targets']):
                    key = _required_text(item.get('target_key'), 'review input target key')
                    if key in review_targets or object_hash(item.get('entry')) != item.get('target_entry_sha256'):
                        raise ValueError('Invalid or duplicate reviewed input target')
                    self._validate_entry(item['entry'], strict=True)
                    review_targets[key] = item
            self.bundles[identifier] = {'metadata': copy.deepcopy(bundle), 'entries': entries,
                                        'review_targets': review_targets}
            for mapping in self._rows(bundle['mappings']):
                # Unreviewed suggestions remain evidence, never a live assignment.
                if (mapping.get('review') or {}).get('status') != 'verified':
                    continue
                self._validate_mapping(mapping, entries, strict=strict, review_targets=review_targets)
                self.mappings[mapping['record_id']].append((identifier, mapping))

    def _asset(self, descriptor):
        if not isinstance(descriptor, dict) or not _hash(descriptor.get('sha256')):
            raise ValueError('Reviewed counterpart asset requires SHA-256')
        path = _local(self.root, descriptor.get('path'))
        raw = path.read_bytes()
        if (hashlib.sha256(raw).hexdigest() != descriptor['sha256'] or
                'bytes' in descriptor and descriptor['bytes'] != len(raw)):
            raise ValueError('Reviewed counterpart source checksum mismatch: ' + descriptor['path'])
        self.assets[descriptor['path']] = descriptor['sha256']
        return raw

    def _rows(self, descriptor):
        raw = self._asset(descriptor)
        path = descriptor['path']
        if path.endswith('.gz'):
            raw = gzip.decompress(raw)
            path = path[:-3]
        if path.endswith('.jsonl'):
            values = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
        elif path.endswith('.json'):
            values = json.loads(raw)
        else:
            raise ValueError('Reviewed counterpart records require JSON or JSONL')
        if not isinstance(values, list) or any(not isinstance(item, dict) for item in values):
            raise ValueError('Reviewed counterpart records must be objects')
        return values

    def _validate_entry(self, entry, strict=False):
        supplied = False
        for language in LANGUAGES:
            item = entry.get(language)
            if item is None:
                continue
            if not isinstance(item, dict) or not _safe_url(item.get('source_url')):
                raise ValueError('Reviewed counterpart requires a safe source URL')
            text = item.get('text')
            if text is not None:
                _required_text(text, language + ' text')
                if text_hash(text) != item.get('text_sha256'):
                    raise ValueError('Reviewed counterpart text checksum mismatch')
                if item.get('scope') not in (None, 'full_narration', 'source_entry', 'source_excerpt'):
                    raise ValueError('Reviewed counterpart text scope is not supported')
            elif item.get('text_sha256') is not None:
                raise ValueError('External-only counterpart cannot claim a text hash')
            elif item.get('scope') not in (None, 'external_source'):
                raise ValueError('External-only counterpart scope is not supported')
            if item.get('translation_origin') not in ('human', 'ai', 'unknown'):
                raise ValueError('Reviewed counterpart translation origin must be explicit')
            for name in ('source_snapshot', 'source_record_id'):
                if item.get(name) is not None:
                    _required_text(item[name], language + ' ' + name)
            if item.get('citation_note') is not None and not isinstance(item['citation_note'], str):
                raise ValueError('Reviewed counterpart citation note must be text')
            references = item.get('references')
            if (not isinstance(references, list) or not references and not
                    (strict and item.get('reference_status') == 'not_supplied_by_source'
                     and isinstance(item.get('source_record_id'), str) and item['source_record_id'].strip())):
                raise ValueError('Reviewed counterpart requires its own numbered reference')
            for reference in references:
                if not isinstance(reference, dict):
                    raise ValueError('Reviewed counterpart reference must be an object')
                for name in ('book_key', 'collection', 'numbering_scheme'):
                    _required_text(reference.get(name), 'reference ' + name)
                if (type(reference.get('number')) not in (str, int) or
                        not str(reference['number']).strip() or
                        reference.get('scope') not in (('main_quote', 'source_quotation', 'publisher_entry')
                                                       if strict else ('main_quote', 'source_quotation'))):
                    raise ValueError('Reviewed counterpart requires a scoped numbered reference')
            supplied = True
        if not supplied:
            raise ValueError('Reviewed counterpart target supplies neither text nor a source link')

    def _validate_mapping(self, mapping, entries, strict=False, review_targets=None):
        for name in ('record_id', 'source_id', 'language', 'target_id'):
            _required_text(mapping.get(name), name)
        if not _hash(mapping.get('source_text_sha256')) or not _hash(mapping.get('source_file_sha256')):
            raise ValueError('Reviewed mapping requires exact original text and source hashes')
        if mapping.get('relation') not in ('same_narration', 'source_excerpt'):
            raise ValueError('Reviewed mapping relation is not supported')
        review = mapping['review']
        _required_text(review.get('reviewer'), 'actual alignment reviewer')
        _required_text(review.get('method'), 'alignment review method')
        if review['method'].strip().lower() in ('number_only', 'number', 'sequence', 'sequence_only'):
            raise ValueError('Number-only reviewed mapping is not allowed')
        if not isinstance(review.get('evidence'), list) or not review['evidence']:
            raise ValueError('Reviewed mapping requires narration alignment evidence')
        if type(review.get('human_review')) is not bool:
            raise ValueError('Reviewed mapping human-review state must be explicit')
        qualifications = review.get('qualifications', [])
        if (not isinstance(qualifications, list) or
                any(not isinstance(note, str) or not note.strip() for note in qualifications)):
            raise ValueError('Reviewed mapping qualifications must be nonempty text notes')
        target = entries.get(mapping['target_id'])
        if target is None:
            raise ValueError('Reviewed mapping target is absent: ' + mapping['target_id'])
        hashes = mapping.get('target_text_sha256')
        if not isinstance(hashes, dict):
            raise ValueError('Reviewed mapping requires target text hashes')
        for language in LANGUAGES:
            item = target.get(language)
            if item is not None and (language not in hashes or hashes[language] != item.get('text_sha256')):
                raise ValueError('Reviewed mapping target text checksum mismatch')
        if strict:
            if mapping.get('source_text_field') not in ('text_translation', 'text_arabic'):
                raise ValueError('Reviewed mapping needs its exact source text field')
            if any(not _hash(mapping.get(key)) for key in
                   ('source_record_sha256', 'source_locator_sha256', 'target_entry_sha256',
                    'review_target_entry_sha256')):
                raise ValueError('Reviewed mapping requires occurrence and complete target hashes')
            if object_hash(target) != mapping['target_entry_sha256']:
                raise ValueError('Reviewed mapping complete target checksum mismatch')
            source_target = (review_targets or {}).get(mapping.get('review_target_key'))
            if source_target is None or source_target['target_entry_sha256'] != mapping['review_target_entry_sha256']:
                raise ValueError('Reviewed mapping input target checksum mismatch')
            selected = validate_language_decisions(source_target['entry'], mapping.get('language_decisions'),
                                                    review, mapping['review_target_key'])
            selected['id'] = target['id']
            if selected != target:
                raise ValueError('Reviewed mapping language decisions differ from published target')
            validate_review_evidence(review, None, source_target['entry'])

    def _unresolved(self, reason):
        return {'schema': LINK_SCHEMA, 'status': 'unresolved', 'match_method': reason,
                'match_note': None, 'provider_identity': None, 'quotation_evidence': None,
                'arabic': None, 'english': None}

    def for_record(self, record):
        candidates = self.mappings.get(record.get('id'), [])
        if not candidates:
            return None
        if len(candidates) != 1:
            return self._unresolved('ambiguous_reviewed_mapping')
        bundle_id, mapping = candidates[0]
        data = self.bundles[bundle_id]
        bundle, entry = data['metadata'], data['entries'][mapping['target_id']]
        strict = bundle.get('evidence_contract') == CONTRACT
        text_field = mapping.get('source_text_field', 'text_translation') if strict else 'text_translation'
        text = record.get(text_field)
        if (record.get('source_id') != mapping['source_id'] or record.get('language') != mapping['language'] or
                not isinstance(text, str) or text_hash(text) != mapping['source_text_sha256'] or
                (record.get('source') or {}).get('sha256') != mapping['source_file_sha256']):
            return self._unresolved('stale_reviewed_source_binding')
        if strict:
            try:
                validate_source_binding(record, mapping)
            except ValueError:
                return self._unresolved('stale_reviewed_source_binding')
            try:
                validate_review_evidence(mapping['review'], record,
                    data['review_targets'][mapping['review_target_key']]['entry'])
            except ValueError:
                return self._unresolved('invalid_reviewed_quotation_evidence')
        result = {'schema': LINK_SCHEMA, 'status': 'reviewed_parallel',
                  'match_method': 'reviewed_source_narration_alignment',
                  'match_note': 'Reviewed source parallel; wording can differ between editions.',
                  'provider_identity': {'provider': bundle['provider'], 'id': entry['id'], 'status': 'linked'},
                  'quotation_evidence': {'field': text_field, 'relation': mapping['relation'],
                                         'source_text_sha256': mapping['source_text_sha256'],
                                         'source_file_sha256': mapping['source_file_sha256'],
                                         'target_text_sha256': copy.deepcopy(mapping['target_text_sha256']),
                                         'mapping_path': bundle['mappings']['path'],
                                         'mapping_sha256': bundle['mappings']['sha256'],
                                         'review': copy.deepcopy(mapping['review'])},
                  'arabic': None, 'english': None}
        if strict:
            result['quotation_evidence'].update({
                'evidence_contract': CONTRACT,
                'source_record_sha256': mapping['source_record_sha256'],
                'source_locator_sha256': mapping['source_locator_sha256'],
                'target_entry_sha256': mapping['target_entry_sha256'],
                'language_decisions': copy.deepcopy(mapping['language_decisions'])})
        for language in LANGUAGES:
            item = entry.get(language)
            if item is None:
                continue
            counterpart = copy.deepcopy(item)
            counterpart.update({'citation': _citation(item['references'], language),
                'source_name': item.get('source_name') or bundle['source_name'],
                'source_snapshot': item.get('source_snapshot') or bundle['source_snapshot'],
                'source_record_id': item.get('source_record_id') or entry['id'],
                'match_status': 'reviewed_parallel',
                'scope': (item.get('scope') or 'full_narration') if item.get('text') else 'external_source',
                'database_path': bundle['entries']['path'], 'database_sha256': bundle['entries']['sha256'],
                'independent_authenticity_certification': False})
            result[language] = counterpart
        return result
