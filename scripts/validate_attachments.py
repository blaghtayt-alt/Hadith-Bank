#!/usr/bin/env python3
"""Independently validate a private attachment intake, using only the stdlib.

This checks the adapter against the bundled extraction evidence. It does not
certify the original extraction, scholarly authenticity, translation accuracy,
reuse rights, or independent Pro publication QC. No importer code is executed.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET


EVIDENCE = 'evidence/extraction-package/'
SCHEMA = 'hadith-bank-attachment-candidate-v1'
LANGUAGE_ALIASES = {'zh': 'zh-CN'}
HEADINGS = ('division', 'part', 'volume', 'chapter', 'section', 'subsection')
REVIEW_ADDITIONS = {
    'release_status': 'private_candidate',
    'independent_pro_qc': 'pending',
    'release_eligible': False,
    'mechanical_validation_report': 'reports/validation.json',
}
EXTRA_FIELDS = {
    'extraction_schema_version', 'source_language_code', 'record_id',
    'occurrence_id', 'content_kind', 'topic_tags', 'source_structure_tags',
    'editorial_tags', 'rights', 'metadata_gaps', 'source_occurrence_group',
    'related_source_entries',
}
MISSING = object()


def canonical(value):
    """JSON equality that distinguishes false from 0 and preserves all strings."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('non-finite JSON value')


def _nonempty_string(value):
    return isinstance(value, str) and bool(value)


def _integer(value, minimum=0):
    return type(value) is int and value >= minimum


class Audit:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.errors = []
        self.error_count = 0
        self.hashes = {}
        self.source_ids = set()
        self.candidate_ids = set()
        self.languages = collections.Counter()
        self.ai = collections.Counter()
        self.related = collections.defaultdict(list)
        self.groups = collections.defaultdict(list)
        self.structure_ids = set()
        self.tag_counts = collections.Counter()
        self.checked_records = 0
        self.exact_records = 0
        self.source_files = set()
        self.rows = {}
        self.manifest_counts = {}
        self.manifest_hash = None
        self.source_manifest_hash = None
        self.expected_records = None
        self.collection_count = 0
        self.missing_translation = 0

    def error(self, code, location, detail):
        self.error_count += 1
        # Diagnostics identify fields; they never copy narration text into reports.
        if len(self.errors) < 100:
            self.errors.append({'code': code, 'location': str(location),
                                'detail': detail})

    def same(self, actual, expected, location, code='value_mismatch'):
        if actual is MISSING or expected is MISSING or canonical(actual) != canonical(expected):
            self.error(code, location, 'Value does not match the evidence-derived contract.')
            return False
        return True

    def local(self, base, relative, location, required=True):
        """Reject traversal, ambiguous spelling, symlinks and remote locators."""
        if (not _nonempty_string(relative) or '\\' in relative or
                any(c in relative for c in ('\x00', '\n', '\r'))):
            self.error('unsafe_path', location, 'Expected a nonempty local POSIX path.')
            return None
        pure = pathlib.PurePosixPath(relative)
        if (pure.is_absolute() or '..' in pure.parts or not pure.parts or
                ':' in pure.parts[0] or relative != pure.as_posix() or
                any(part in ('', '.') for part in relative.split('/'))):
            self.error('unsafe_path', location, 'Absolute, traversal or ambiguous path rejected.')
            return None
        base = pathlib.Path(base).resolve()
        path = base.joinpath(*pure.parts)
        part = base
        for name in pure.parts:
            part = part / name
            if part.is_symlink():
                self.error('unsafe_path', location, 'Symlink locators are not permitted.')
                return None
        try:
            path.resolve().relative_to(base)
        except (ValueError, OSError):
            self.error('unsafe_path', location, 'Local path escapes its package root.')
            return None
        if required and not path.is_file():
            self.error('missing_file', location, 'Required local file is absent.')
            return None
        return path

    def file_hash(self, path):
        if path is None:
            return None
        if path not in self.hashes:
            try:
                h = hashlib.sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(block)
                self.hashes[path] = h.hexdigest()
            except OSError:
                self.error('file_read', path.relative_to(self.root), 'Cannot read local file.')
                self.hashes[path] = None
        return self.hashes[path]

    def load(self, relative, base=None):
        base = self.root if base is None else base
        path = self.local(base, relative, relative)
        if path is None:
            return None
        try:
            return json.loads(path.read_text(encoding='utf-8'),
                              object_pairs_hook=_object,
                              parse_constant=_invalid_constant)
        except (OSError, UnicodeError, ValueError):
            self.error('invalid_json', relative, 'Cannot read strict UTF-8 JSON.')
            return None

    def manifest(self, base, label, excluded):
        manifest = self.local(base, 'checksums.sha256', label + '/checksums.sha256')
        if manifest is None:
            return {}
        entries = {}
        try:
            lines = manifest.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeError):
            self.error('manifest_read', label, 'Cannot read checksum manifest.')
            return entries
        for number, line in enumerate(lines, 1):
            match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
            where = label + '/checksums.sha256:' + str(number)
            if not match:
                self.error('manifest_syntax', where, 'Expected SHA-256, two spaces and local path.')
                continue
            expected, relative = match.groups()
            if relative in entries:
                self.error('manifest_duplicate', where, 'Duplicate checksum entry.')
                continue
            entries[relative] = expected
            if relative in excluded:
                self.error('manifest_excluded', where, 'Self or validation report must be excluded.')
            path = self.local(base, relative, where)
            if path is not None and self.file_hash(path) != expected:
                self.error('checksum_mismatch', label + '/' + relative,
                           'File bytes differ from their manifest digest.')
        actual = set()
        for path in base.rglob('*'):
            relative = path.relative_to(base).as_posix()
            if path.is_symlink():
                self.error('unsafe_path', label + '/' + relative,
                           'Package must not contain symlinks.')
            elif path.is_file() and relative not in excluded:
                actual.add(relative)
        for relative in sorted(actual - set(entries)):
            self.error('manifest_unlisted', label + '/' + relative,
                       'File is absent from the complete checksum manifest.')
        for relative in sorted(set(entries) - actual):
            self.error('manifest_missing', label + '/' + relative,
                       'Manifest entry is absent or disallowed.')
        self.manifest_counts[label] = len(entries)
        return entries

    def source_rows(self, path, location):
        """Read only worksheet/row identities; do not re-extract translation text."""
        if path is None:
            return None
        if path in self.rows:
            return self.rows[path]
        result = {}
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        relns = '{http://schemas.openxmlformats.org/package/2006/relationships}'
        rid = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
        try:
            with zipfile.ZipFile(path) as archive:
                workbook = ET.fromstring(archive.read('xl/workbook.xml'))
                rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
                targets = {r.attrib['Id']: r.attrib['Target']
                           for r in rels.findall(relns + 'Relationship')
                           if r.attrib.get('TargetMode') != 'External'}
                for sheet in workbook.findall('s:sheets/s:sheet', ns):
                    target = targets[sheet.attrib[rid]]
                    target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
                    pure = pathlib.PurePosixPath(target)
                    if '..' in pure.parts or '\\' in target:
                        raise ValueError('unsafe worksheet member')
                    xml = ET.fromstring(archive.read(pure.as_posix()))
                    result[sheet.attrib['name']] = {
                        int(row.attrib['r'])
                        for row in xml.findall('s:sheetData/s:row', ns)
                    }
        except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile):
            self.error('source_workbook', location, 'Cannot verify original workbook row bounds.')
            result = None
        self.rows[path] = result
        return result

    def page_bounds(self, record, dataset, source_rows, location):
        page = record.get('page')
        if not isinstance(page, dict):
            self.error('source_bounds', location + '.page', 'Expected original page locator object.')
            return
        pdf = page.get('pdf')
        if not isinstance(pdf, list) or any(not _integer(p, 1) for p in pdf):
            self.error('source_bounds', location + '.page.pdf', 'Expected positive one-based PDF pages.')
            return
        if dataset['format'] == 'pdf':
            count = dataset.get('pdf_pages')
            if not _integer(count, 1) or not pdf or any(p > count for p in pdf):
                self.error('source_bounds', location + '.page.pdf', 'PDF locator exceeds recorded source bounds.')
            if page.get('sheet') is not None or page.get('row') is not None:
                self.error('source_bounds', location + '.page', 'PDF must not acquire spreadsheet row locators.')
        elif dataset['format'] == 'xlsx':
            if pdf or not _nonempty_string(page.get('sheet')) or not _integer(page.get('row'), 1):
                self.error('source_bounds', location + '.page', 'Invalid spreadsheet sheet/row locator.')
            elif source_rows is not None and page['row'] not in source_rows.get(page['sheet'], set()):
                self.error('source_bounds', location + '.page', 'Sheet/row does not exist in the original workbook.')

    def core(self, original, record, location):
        before = self.error_count
        for field, value in original.items():
            actual = record.get(field, MISSING)
            if field == 'schema_version':
                expected = SCHEMA
            elif field == 'language':
                expected = LANGUAGE_ALIASES.get(value, value)
            elif field == 'source':
                expected = dict(value, package_file=EVIDENCE + value['package_file'])
                self.local(self.root, record.get('source', {}).get('package_file'),
                           location + '.source.package_file')
            elif field == 'provenance':
                if not isinstance(actual, dict):
                    self.error('original_field_changed', location + '.provenance', 'Original provenance is missing.')
                    continue
                if 'bank_intake' in value:
                    self.error('source_reserved_field', location + '.provenance', 'Original evidence uses reserved bank_intake key.')
                actual = {k: v for k, v in actual.items() if k != 'bank_intake'}
                expected = value
            elif field == 'review':
                if any(k in value for k in REVIEW_ADDITIONS):
                    self.error('source_reserved_field', location + '.review', 'Original review uses reserved intake keys.')
                expected = dict(value, **REVIEW_ADDITIONS)
            else:
                expected = value
            self.same(actual, expected, location + '.' + field, 'original_field_changed')
        self.same(sorted(set(record) - set(original)), sorted(EXTRA_FIELDS),
                  location + '.added_fields', 'unexpected_fields')
        if self.error_count == before:
            self.exact_records += 1

    def additions(self, original, record, dataset, collection, index, location):
        lang = collection['language']
        for field, expected in {
            'record_id': original['id'], 'occurrence_id': original['id'],
            'extraction_schema_version': original['schema_version'],
            'source_language_code': original['language'],
            'content_kind': 'source_narration_occurrence_not_independently_classified',
            'topic_tags': [],
        }.items():
            self.same(record.get(field, MISSING), expected, location + '.' + field)
        intake = {
            'adapter_version': '1.0.0',
            'source_records_path': EVIDENCE + dataset['records_file'],
            'source_json_pointer': '/' + str(index),
            'extraction_record_sha256': digest(original),
            'text_payload_sha256': digest(original['text']),
            'source_package_checksums_sha256': self.source_manifest_hash,
            'source_language_code': original['language'],
            'bank_language_code': lang,
            'language_alias_note': 'Directory alias only; no locale or script conversion.',
            'new_translation_created': False,
            'canonical_identity_inferred': False,
        }
        self.same(record.get('provenance', {}).get('bank_intake', MISSING), intake,
                  location + '.provenance.bank_intake', 'intake_provenance')

        headings = []
        expected_tags = []
        for field in HEADINGS:
            value = original['book'].get(field)
            if not isinstance(value, str) or not value:
                continue
            headings.append({'field': field, 'value_verbatim': value})
            tag = {
                'tag_id': ('structure:' + original['source']['sha256'][:16] + ':' +
                           digest(headings)[:20]),
                'origin': 'source_book_structure', 'language': original['language'],
                'field': field, 'value_verbatim': value,
                'source_id': original['source']['source_id'],
                'hierarchy_verbatim': list(headings),
                'evidence': {
                    'source_field': 'book.' + field,
                    'extraction_record_id': original['id'],
                    'record_location': original['page'],
                    'location_scope': 'narration under heading, not certified heading page',
                },
            }
            expected_tags.append(tag)
            self.structure_ids.add(tag['tag_id'])
        self.same(record.get('source_structure_tags', MISSING), expected_tags,
                  location + '.source_structure_tags', 'source_structure_tag')
        self.tag_counts['records_with_source_structure'] += bool(expected_tags)
        self.tag_counts['source_structure_assignments'] += len(expected_tags)

        ai = str(original['ai_translation']).lower()
        source_tag = 'hadeethenc' if dataset['format'] == 'xlsx' else dataset['source_id']
        expected_values = [
            'source:' + source_tag, 'language:' + lang,
            'book:' + collection['book'], 'edition:' + collection['edition'],
            'format:' + dataset['format'],
            'method:' + original['provenance']['extraction_method'],
            'review:pending_independent_pro', 'ai_translation:' + ai,
            'kind:narration_occurrence', 'rights:pending', 'canonical_mapping:unverified',
            'arabic:' + ('present' if original['text']['arabic'] else 'not_supplied'),
            'translation:' + ('present' if original['text']['translation'] else 'not_supplied'),
        ]
        if original['review']['issues']:
            expected_values.append('source_issues:flagged')
        if original['narration_unit'] not in ('source_entry', 'source_occurrence'):
            expected_values.append('segmentation:split_source_occurrence')
        self.same(record.get('editorial_tags', MISSING),
                  {'origin': 'import_pipeline_not_publisher', 'values': expected_values},
                  location + '.editorial_tags', 'editorial_tags')
        self.tag_counts['editorial_assignments'] += len(expected_values)
        self.ai[ai] += 1
        self.missing_translation += original['text']['translation'] is None

        rights = record.get('rights')
        if not isinstance(rights, dict):
            self.error('rights', location + '.rights', 'Private rights metadata is missing.')
        else:
            for field, value in {
                'status': 'not_assessed_for_publication', 'reuse_basis': None,
                'publication_authorized_by_this_import': False,
                'source_conditions_path': EVIDENCE + dataset['source_metadata'],
            }.items():
                self.same(rights.get(field, MISSING), value, location + '.rights.' + field, 'rights')
            self.local(self.root, rights.get('source_conditions_path'), location + '.rights.source_conditions_path')

        gaps = ['independent_pro_publication_qc', 'public_redistribution_basis',
                'canonical_occurrence_mapping', 'narration_authenticity_classification',
                'publisher_topic_taxonomy_not_supplied']
        for missing, label in [
            (original['translator']['name'] is None, 'named_translator'),
            (original['book']['edition'] is None, 'bibliographic_edition'),
            (original['narrator']['name'] is None, 'separate_narrator_name'),
            (original['text']['arabic'] is None, 'source_arabic_not_supplied'),
            (original['text']['translation'] is None, 'source_translation_not_supplied'),
            (dataset['format'] == 'xlsx', 'translation_edition_scope_not_independently_verified'),
        ]:
            if missing:
                gaps.append(label)
        self.same(record.get('metadata_gaps', MISSING), gaps, location + '.metadata_gaps')

        if dataset['format'] == 'xlsx':
            group = {'id': 'hadeethenc:' + dataset['source_sha256'] + ':row:' + str(original['page']['row']),
                     'basis': 'same exact spreadsheet source row; not canonical identity'}
        elif isinstance(original.get('relations'), dict) and original['relations'].get('numbered_occurrence_id'):
            group = {'id': original['relations']['numbered_occurrence_id'],
                     'basis': 'numbered source occurrence retained by extraction'}
        elif original.get('source_occurrence_id'):
            group = {'id': original['source_occurrence_id'],
                     'basis': 'source occurrence retained by extraction'}
        else:
            group = {'id': original['id'], 'basis': 'individual extracted source occurrence'}
        self.same(record.get('source_occurrence_group', MISSING), group,
                  location + '.source_occurrence_group', 'source_group')
        self.groups[group['id']].append(original['id'])
        entry_id = original['number'].get('source_entry_id')
        related = None
        if dataset['format'] == 'xlsx' and entry_id:
            related = {
                'provider': 'HadeethEnc.com', 'entry_id': entry_id,
                'index_path': 'indexes/hadeethenc-related-entries.json',
                'basis': 'same publisher entry ID only; not canonical identity or variant alignment',
            }
            self.related[entry_id].append({
                'id': original['id'], 'language': lang,
                'source_language_code': original['language'],
                'source_id': dataset['source_id'], 'records_path': collection['records_path'],
                'json_pointer': '/' + str(index),
            })
        self.same(record.get('related_source_entries', MISSING), related,
                  location + '.related_source_entries', 'related_entry')

    def dataset(self, dataset, collection):
        relative = dataset['records_file']
        where = collection.get('records_path', '<missing records path>')
        metadata = self.load(EVIDENCE + dataset['source_metadata'])
        if not isinstance(metadata, dict):
            self.error('source_metadata', relative, 'Source metadata must be an object.')
            return
        source_path = self.local(self.root, EVIDENCE + metadata.get('package_original_file', ''),
                                 relative + ':original source')
        if source_path is not None:
            self.source_files.add(source_path)
            self.same(self.file_hash(source_path), dataset['source_sha256'],
                      relative + ':original source', 'source_checksum')
        for field, expected in [('source_id', dataset['source_id']),
                                ('sha256', dataset['source_sha256']),
                                ('language', dataset['language']), ('format', dataset['format'])]:
            self.same(metadata.get(field, MISSING), expected, relative + ':source.' + field)
        rows = self.source_rows(source_path, relative) if dataset['format'] == 'xlsx' else None
        parts = pathlib.PurePosixPath(relative).parts
        if len(parts) != 4 or parts[-1] != 'records.json' or not re.fullmatch('[a-z0-9-]+', parts[1]):
            self.error('source_layout', relative, 'Unexpected language/book/edition source layout.')
            return
        edition = ('xlsx-' + metadata['version'] + '-' + dataset['source_sha256'][:16]
                   if dataset['format'] == 'xlsx' else 'pdf-' + dataset['source_sha256'][:16])
        language = LANGUAGE_ALIASES.get(dataset['language'], dataset['language'])
        expected_path = ('languages/' + language + '/books/' + parts[1] + '/editions/' + edition + '/records.json')
        expected_collection = {
            'language': language, 'source_language_code': dataset['language'],
            'book': parts[1], 'edition': edition, 'records_path': expected_path,
            'count': dataset['records'], 'source_id': dataset['source_id'],
            'source_sha256': dataset['source_sha256'],
            'source_records_path': EVIDENCE + relative,
            'source_file': EVIDENCE + metadata['package_original_file'],
            'source_metadata_path': EVIDENCE + dataset['source_metadata'],
            'coverage_path': EVIDENCE + dataset['coverage_file'],
            'exceptions_path': EVIDENCE + dataset['exceptions_file'],
            'release_status': 'private_candidate', 'format': dataset['format'],
            'source_entries': dataset.get('source_entries'), 'pdf_pages': dataset.get('pdf_pages'),
        }
        for field, expected in expected_collection.items():
            self.same(collection.get(field, MISSING), expected, str(where) + ':' + field, 'collection_metadata')
        # These new locators must resolve inside the candidate, not archival paths.
        for field in ['source_records_path', 'records_path', 'source_file', 'source_metadata_path',
                      'coverage_path', 'exceptions_path']:
            self.local(self.root, collection.get(field), str(where) + ':' + field)
        records_path = self.local(self.root, collection.get('records_path'), str(where))
        if records_path is not None:
            self.same(self.file_hash(records_path), collection.get('records_sha256', MISSING),
                      str(where) + ':records_sha256', 'collection_checksum')
        original = self.load(EVIDENCE + relative)
        records = self.load(collection.get('records_path'))
        if not isinstance(original, list) or not isinstance(records, list):
            self.error('records_shape', str(where), 'Source and candidate records must be JSON arrays.')
            return
        self.same(len(original), dataset['records'], relative + ':count', 'record_count')
        self.same(len(records), len(original), str(where) + ':count', 'record_count')
        manifest_path = str(pathlib.PurePosixPath(expected_path).parent / 'manifest.json')
        self.same(self.load(manifest_path), collection, manifest_path, 'collection_manifest')
        for index, source_record in enumerate(original):
            location = str(where) + '#/' + str(index)
            if not isinstance(source_record, dict) or not _nonempty_string(source_record.get('id')):
                self.error('original_record', location, 'Source record requires an occurrence ID.')
                continue
            if source_record['id'] in self.source_ids:
                self.error('duplicate_source_id', location, 'Original occurrence ID is not unique.')
            self.source_ids.add(source_record['id'])
            if index >= len(records):
                continue
            record = records[index]
            if not isinstance(record, dict) or not _nonempty_string(record.get('id')):
                self.error('candidate_record', location, 'Candidate record requires an occurrence ID.')
                continue
            if record['id'] in self.candidate_ids:
                self.error('duplicate_candidate_id', location, 'Candidate occurrence ID is not unique.')
            self.candidate_ids.add(record['id'])
            self.checked_records += 1
            self.languages[language] += 1
            try:
                self.same(source_record.get('schema_version', MISSING), '1.0.0', location + ':source.schema_version')
                self.same(source_record.get('language', MISSING), dataset['language'], location + ':source.language')
                for field, value in [('sha256', dataset['source_sha256']), ('source_id', dataset['source_id']),
                                     ('format', dataset['format']), ('package_file', metadata['package_original_file'])]:
                    self.same(source_record['source'].get(field, MISSING), value, location + ':source.' + field)
                self.page_bounds(source_record, dataset, rows, location)
                self.core(source_record, record, location)
                self.additions(source_record, record, dataset, collection, index, location)
            except (KeyError, TypeError, ValueError, AttributeError):
                self.error('record_contract', location, 'Missing or malformed source/candidate contract field.')

    def run(self):
        if not self.root.is_dir():
            self.error('missing_root', '.', 'Candidate root is not a directory.')
            return self.result()
        outer = self.manifest(self.root, 'candidate', {'checksums.sha256', 'reports/validation.json'})
        evidence_root = self.root / EVIDENCE
        if self.local(self.root, EVIDENCE + 'checksums.sha256', EVIDENCE + 'checksums.sha256') is not None:
            self.manifest(evidence_root, 'extraction-package', {'checksums.sha256'})
        self.manifest_hash = self.file_hash(self.local(self.root, 'checksums.sha256', 'checksums.sha256'))
        self.source_manifest_hash = self.file_hash(self.local(self.root, EVIDENCE + 'checksums.sha256', EVIDENCE + 'checksums.sha256'))
        gate = self.load('PUBLICATION-GATE.json')
        if not isinstance(gate, dict):
            self.error('publication_gate', 'PUBLICATION-GATE.json', 'Closed publication gate is required.')
        else:
            self.same(gate.get('allowed', MISSING), False, 'PUBLICATION-GATE.json:allowed', 'publication_gate')
            self.same(gate.get('release_eligible_records', MISSING), 0,
                      'PUBLICATION-GATE.json:release_eligible_records', 'publication_gate')
        catalog = self.load(EVIDENCE + 'catalog.json')
        collections_index = self.load('collections.json')
        if not isinstance(catalog, dict) or not isinstance(collections_index, dict):
            self.error('catalog', 'collections.json', 'Both source and candidate catalogs are required.')
            return self.result()
        datasets, entries = catalog.get('datasets'), collections_index.get('collections')
        if not isinstance(datasets, list) or not isinstance(entries, list):
            self.error('catalog', 'collections.json', 'Dataset and collection arrays are required.')
            return self.result()
        self.same(collections_index.get('schema', MISSING), 'hadith-bank-attachment-collections-v1', 'collections.json:schema')
        self.same(collections_index.get('release_status', MISSING), 'private_candidate', 'collections.json:release_status')
        self.expected_records = catalog.get('record_count')
        self.collection_count = len(entries)
        self.same(len(entries), len(datasets), 'collections.json:count', 'collection_count')
        lookup = {}
        records_paths = set()
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict) or not _nonempty_string(entry.get('source_records_path')):
                self.error('collection', 'collections.json#/' + str(i), 'Collection source locator is required.')
                continue
            if entry['source_records_path'] in lookup:
                self.error('duplicate_collection', 'collections.json#/' + str(i), 'Source collection is duplicated.')
            lookup[entry['source_records_path']] = entry
            path = entry.get('records_path')
            self.local(self.root, entry['source_records_path'], 'collections.json:source_records_path')
            self.local(self.root, path, 'collections.json:records_path')
            if _nonempty_string(path):
                if path in records_paths:
                    self.error('duplicate_collection', 'collections.json#/' + str(i), 'Candidate records path is duplicated.')
                records_paths.add(path)
        source_counts = collections.Counter()
        expected_source_paths = set()
        for dataset in datasets:
            try:
                if not isinstance(dataset, dict) or not _integer(dataset.get('records')):
                    raise ValueError('dataset contract')
                source_path = EVIDENCE + dataset['records_file']
                if source_path in expected_source_paths:
                    self.error('duplicate_dataset', source_path, 'Original source dataset is duplicated.')
                expected_source_paths.add(source_path)
                source_counts[dataset['language']] += dataset['records']
                entry = lookup.get(source_path)
                if entry is None:
                    self.error('missing_collection', source_path, 'Original dataset has no corresponding bank collection.')
                    continue
                self.dataset(dataset, entry)
            except (KeyError, TypeError, ValueError, AttributeError):
                self.error('dataset_contract', 'catalog.json', 'Missing or malformed dataset contract field.')
        self.same(sorted(lookup), sorted(expected_source_paths), 'collections.json:source_coverage', 'source_coverage')
        self.same(dict(source_counts), catalog.get('by_language', MISSING), 'catalog.json:by_language', 'record_count')
        self.same(sum(source_counts.values()), self.expected_records, 'catalog.json:record_count', 'record_count')
        self.same(self.checked_records, self.expected_records, 'records_checked', 'record_count')
        self.same(len(self.source_ids), self.expected_records, 'source_unique_ids', 'record_count')
        self.same(len(self.candidate_ids), self.expected_records, 'candidate_unique_ids', 'record_count')
        self.same(sorted(self.source_ids), sorted(self.candidate_ids), 'occurrence_ids', 'identity_preservation')
        self.same(collections_index.get('record_count', MISSING), self.expected_records, 'collections.json:record_count', 'record_count')
        actual_record_paths = {p for p in outer if p.startswith('languages/') and p.endswith('/records.json')}
        self.same(sorted(actual_record_paths), sorted(records_paths), 'collections.json:record_files', 'unindexed_records')
        self.indexes_and_reports(entries, catalog)
        return self.result()

    def indexes_and_reports(self, entries, catalog):
        related = self.load('indexes/hadeethenc-related-entries.json')
        self.same(related, {
            'basis': 'same publisher entry ID only; not canonical identity or exact variant alignment',
            'groups': [{'entry_id': key, 'occurrences': self.related[key]}
                       for key in sorted(self.related)],
        }, 'indexes/hadeethenc-related-entries.json', 'related_index')
        grouped = self.load('indexes/source-occurrence-groups.json')
        self.same(grouped, {
            'basis': 'exact source occurrence/row segmentation relationships; no deduplication',
            'groups': [{'source_occurrence_id': key, 'record_ids': self.groups[key]}
                       for key in sorted(self.groups) if len(self.groups[key]) > 1],
        }, 'indexes/source-occurrence-groups.json', 'source_group_index')
        for language, count in self.languages.items():
            path = 'languages/' + language + '/catalog.json'
            self.same(self.load(path), {
                'schema': 'hadith-bank-attachment-language-v1', 'language': language,
                'record_count': count, 'collections': [e for e in entries if e.get('language') == language],
                'release_status': 'private_candidate',
            }, path, 'language_catalog')
        summary = self.load('reports/intake-summary.json')
        if not isinstance(summary, dict):
            self.error('intake_summary', 'reports/intake-summary.json', 'Intake summary is required.')
            return
        expected = {
            'schema': 'hadith-bank-attachment-intake-summary-v1',
            'intake_id': 'attachments-' + self.source_manifest_hash[:16] if self.source_manifest_hash else None,
            'record_count': self.expected_records, 'datasets': len(entries),
            'by_language': dict(self.languages), 'ai_translation': dict(self.ai),
            'records_without_translation': self.missing_translation,
            'tag_counts': {**dict(self.tag_counts), 'distinct_source_structure_tags': len(self.structure_ids),
                           'publisher_topic_assignments': 0},
            'source_package_checksums_sha256': self.source_manifest_hash,
            'source_package_files_verified': self.manifest_counts.get('extraction-package'),
            'source_package_catalog_sha256': self.file_hash(self.root / EVIDENCE / 'catalog.json'),
            'source_text_altered': False, 'new_translations_generated': 0,
            'occurrence_ids_preserved': True, 'deduplicated_or_removed_records': 0,
            'publication_status': 'private_candidate_not_published',
            'published_translation_entries': 0, 'independent_pro_publication_qc': 'pending',
            'collections': entries,
        }
        for field, value in expected.items():
            self.same(summary.get(field, MISSING), value, 'reports/intake-summary.json:' + field, 'intake_summary')

    def result(self):
        return {
            'schema': 'hadith-bank-attachment-validation-v1',
            'status': 'passed' if self.error_count == 0 else 'failed',
            'success': self.error_count == 0,
            'validation_scope': 'Mechanical package integrity and lossless adapter comparison against bundled extraction evidence.',
            'source_authenticity_independently_verified': False,
            'source_visual_qc_performed_by_this_validator': False,
            'semantic_narration_completeness_certified': False,
            'independent_pro_publication_qc': 'pending',
            'publication_allowed': False, 'release_eligible_records': 0,
            'expected_records_from_source_catalog': self.expected_records,
            'records_checked': self.checked_records,
            'records_with_exact_original_fields': self.exact_records,
            'unique_source_occurrence_ids': len(self.source_ids),
            'unique_bank_occurrence_ids': len(self.candidate_ids),
            'collections': self.collection_count, 'by_language': dict(sorted(self.languages.items())),
            'ai_translation': dict(sorted(self.ai.items())),
            'original_source_assets_checked': len(self.source_files),
            'files_hashed': len(self.hashes), 'manifest_entries': self.manifest_counts,
            'candidate_checksums_sha256': self.manifest_hash,
            'source_package_checksums_sha256': self.source_manifest_hash,
            'error_count': self.error_count, 'errors': self.errors,
            'errors_truncated': self.error_count > len(self.errors),
            'limitations': [
                'Bundled checksums establish internal integrity, not an external authenticity signature.',
                'Original extraction defects, uncertain boundaries and partial visual review remain unchanged.',
                'No independent Pro review, translation review, canonical alignment or reuse clearance is performed.',
            ],
        }


def validate(root, report=None):
    """Return a validation result. Write JSON only when an explicit report is supplied."""
    audit = Audit(root)
    result = audit.run()
    if report is not None:
        target = pathlib.Path(report).absolute()
        resolved = target.resolve()
        # Never allow --report to overwrite source bytes or another candidate file.
        if resolved.is_relative_to(audit.root) and resolved != audit.root / 'reports/validation.json':
            raise ValueError('Inside the candidate, the only report destination is reports/validation.json')
        if target.is_symlink() or any(p.is_symlink() for p in target.parents):
            raise ValueError('Report destination may not use symlinks')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8', newline='\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=pathlib.Path, required=True)
    parser.add_argument('--report', type=pathlib.Path,
                        help='Optional JSON output path; candidate reports/validation.json is manifest-excluded.')
    args = parser.parse_args()
    try:
        result = validate(args.root, args.report)
    except (OSError, ValueError) as error:
        parser.exit(1, 'Attachment validation failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
