#!/usr/bin/env python3
"""Search the Hadith Bank's flat, checksum-verified JSONL projection offline.

Input contract: catalog/materials.json has a search object with records_sha256
and count, plus records_path and/or ordered shards [{path, sha256, count, bytes}].
When the whole records_path file is absent, shards are verified individually and
against the concatenated records_sha256. Their bytes must form the same JSONL.

Each line is one flat narration occurrence. Required fields are documented in
_REQUIRED_FIELDS below. Text is never normalized in the source or returned data.
Only disposable search keys and the query are case/width folded, with Arabic
vocalization/tatweel and CJK line wraps ignored for matching. Query words are
ANDed literal substrings across text and record metadata, including references,
translator/source details, occurrence IDs and editions. FTS5 trigram accelerates terms of three or more Unicode
characters when available; escaped LIKE remains the authoritative match test.

Filters are exact: language (zh/tl aliases accepted), book_key, source_id,
occurrence/provider entry ID, topic ID/label or editorial tag, and translation
origin. Human/AI/Unknown use the current source classification; other origin
filters retain their historical evidence-specific meaning. No records or
versions are merged. Commentary, supplied benefits, footnotes and preserved
source context are searched only with include_commentary=True /
--include-commentary. Top-level annotation fields are returned only with that
option; original source metadata remains preserved for provenance. Optional
benefits may be null or an object containing original strings or decoded lists
of strings; supplied values remain unchanged.

The entire input stream is hash-verified before any cache is used. Results are
read from that verified input, never from cached text. The cache is disposable,
stays under root/.cache, and is refreshed when bytes or normalization change.
This search performs no translation, authenticity assessment or release review.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import sys
import tempfile
import unicodedata

from current_provenance import classification as current_translation_origin
from counterpart_display import (counterpart_data, counterpart_search_values,
                                 counterpart_citation, counterpart_qualification)
from citation_search import has_noncanonical_numbering, record_citation_pairs, split_citation_query


VERSION = 'hadith-bank-search-v1'
CACHE_VERSION = '7:literal-substrings:arabic-persian-cjk:arabic-digits:paired-citations:scoped-source-metadata:current-origin:record-metadata'
CATALOG_PATH = 'catalog/materials.json'
DEFAULT_DATABASE = '.cache/hadith-search.sqlite'
LANGUAGE_ALIASES = {'zh': 'zh-CN', 'tl': 'fil'}
_SHA256 = re.compile(r'[0-9a-fA-F]{64}\Z')
_CJK = '\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f'
_CJK_SPACING = re.compile(r'(?<=[' + _CJK + r'])\s+(?=[' + _CJK + r'])')
_REQUIRED_FIELDS = (
    'id', 'language', 'source_language_code', 'book_key', 'edition', 'source_id',
    'provider_entry_id', 'title', 'text_arabic', 'text_translation', 'number',
    'narrator', 'source', 'translator', 'translation_provenance', 'topic_tags',
    'editorial_tags', 'source_headings', 'review', 'commentary', 'footnotes',
    'references', 'page',
)
_ANNOTATION_FIELDS = frozenset(('commentary', 'footnotes', 'benefits'))
_PRIMARY_SEARCH_FIELDS = (
    'id', 'language', 'source_language_code', 'book_key', 'edition', 'source_id',
    'provider_entry_id', 'title', 'text_arabic', 'text_translation', 'number',
    'translator', 'references', 'topic_tags', 'editorial_tags', 'source_headings',
    'page', 'isnad', 'record_type', 'content_kind', 'grading',
)
_SOURCE_SEARCH_FIELDS = (
    'name', 'work_title', 'title', 'publisher', 'edition', 'isbn', 'url',
    'record_url', 'original_file', 'record_locator', 'format', 'sha256',
)
_NARRATOR_SEARCH_FIELDS = ('name', 'names', 'verbatim', 'chain', 'isnad')
_SOURCE_CONTEXT_FIELDS = ('original_metadata', 'original_context', 'context', 'historical_metadata')


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON object key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Non-finite JSON value is not supported')


def _json(data):
    return json.loads(data, object_pairs_hook=_object, parse_constant=_constant)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def _hash_file(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def _local(root, relative, *, required=True):
    """All source locators are canonical, local, and free of symlink escapes."""
    if (not isinstance(relative, str) or not relative or '\\' in relative or
            any(ord(c) < 32 for c in relative)):
        raise ValueError('Unsafe local path')
    path = PurePosixPath(relative)
    if (path.is_absolute() or '..' in path.parts or path.as_posix() != relative or
            any(part in ('', '.') or ':' in part for part in relative.split('/'))):
        raise ValueError('Unsafe local path: ' + relative)
    result = root
    for part in path.parts:
        result = result / part
        if result.is_symlink():
            raise ValueError('Symlink source/cache path is not allowed: ' + relative)
    try:
        result.resolve().relative_to(root)
    except ValueError as error:
        raise ValueError('Local path escapes root: ' + relative) from error
    if required and not result.is_file():
        raise ValueError('Missing local file: ' + relative)
    return result


def _sha(value, label):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(label + ' must be a SHA-256 hexadecimal digest')
    return value.lower()


def _count(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(label + ' must be a nonnegative integer')
    return value


def _load_catalog(root):
    try:
        catalog = _json(_local(root, CATALOG_PATH).read_text(encoding='utf-8'))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('Catalog is not valid UTF-8 JSON') from error
    if not isinstance(catalog, dict) or not isinstance(catalog.get('search'), dict):
        raise ValueError('catalog/materials.json requires a search object')
    specification = catalog['search']
    _sha(specification.get('records_sha256'), 'search.records_sha256')
    _count(specification.get('count'), 'search.count')
    return catalog


class VerifiedStream:
    """A fresh full-stream digest plus locations for exact original result lines."""
    def __init__(self, root, specification):
        self.root = root
        self.sha256 = _sha(specification['records_sha256'], 'search.records_sha256')
        self.count = _count(specification['count'], 'search.count')
        self.locations = []
        self.files = []
        whole = specification.get('records_path')
        whole_path = _local(root, whole, required=False) if whole is not None else None
        if whole_path is not None and whole_path.exists():
            if not whole_path.is_file():
                raise ValueError('search.records_path is not a regular file')
            self.mode = 'single_file'
            files = [(whole_path, None)]
        else:
            shards = specification.get('shards')
            if not isinstance(shards, list) or not shards:
                raise ValueError('Search records file is absent and no ordered shards are supplied')
            self.mode = 'shards'
            files = []
            seen = set()
            for item in shards:
                if not isinstance(item, dict):
                    raise ValueError('Every search shard must be an object')
                path = _local(root, item.get('path'))
                if path in seen:
                    raise ValueError('Duplicate search shard path')
                seen.add(path)
                _sha(item.get('sha256'), 'shard.sha256')
                _count(item.get('count'), 'shard.count')
                _count(item.get('bytes'), 'shard.bytes')
                files.append((path, item))
        aggregate = hashlib.sha256()
        for file_index, (path, shard) in enumerate(files):
            digest = hashlib.sha256()
            byte_count = 0
            line_count = 0
            last = b''
            with path.open('rb') as stream:
                initial = os.fstat(stream.fileno())
                for raw in stream:
                    if not raw.strip():
                        raise ValueError('Blank lines are not narration records: ' + str(path.relative_to(root)))
                    digest.update(raw)
                    aggregate.update(raw)
                    self.locations.append((file_index, byte_count, len(raw), hashlib.sha256(raw).digest()))
                    byte_count += len(raw)
                    line_count += 1
                    last = raw
                final = os.fstat(stream.fileno())
            if (initial.st_size, initial.st_mtime_ns) != (final.st_size, final.st_mtime_ns):
                raise ValueError('Search input changed during integrity verification')
            if shard is not None:
                if digest.hexdigest() != shard['sha256'].lower():
                    raise ValueError('SHA-256 mismatch for search shard: ' + shard['path'])
                if byte_count != shard['bytes'] or line_count != shard['count']:
                    raise ValueError('Byte/count mismatch for search shard: ' + shard['path'])
                if file_index < len(files) - 1 and last and not last.endswith(b'\n'):
                    raise ValueError('A nonfinal shard must end with a JSONL newline')
            self.files.append(path)
        if aggregate.hexdigest() != self.sha256:
            raise ValueError('SHA-256 mismatch for complete search input stream')
        if len(self.locations) != self.count:
            raise ValueError('Record count mismatch for complete search input stream')

    def _decode(self, raw, number):
        try:
            value = _json(raw.decode('utf-8'))
        except (UnicodeError, ValueError) as error:
            raise ValueError('Invalid UTF-8 JSON narration at search line ' + str(number)) from error
        if not isinstance(value, dict):
            raise ValueError('Search line is not a JSON object: ' + str(number))
        return value

    def records(self):
        number = 0
        for path in self.files:
            with path.open('rb') as stream:
                for raw in stream:
                    if number >= len(self.locations) or hashlib.sha256(raw).digest() != self.locations[number][3]:
                        raise ValueError('Search input changed after verification')
                    number += 1
                    yield number, self._decode(raw, number)
        if number != self.count:
            raise ValueError('Search input changed after verification')

    def record(self, number):
        if type(number) is not int or not 1 <= number <= self.count:
            raise ValueError('Cached result points outside the verified source stream')
        file_index, offset, size, digest = self.locations[number - 1]
        with self.files[file_index].open('rb') as stream:
            stream.seek(offset)
            raw = stream.read(size)
        if hashlib.sha256(raw).digest() != digest:
            raise ValueError('Search input changed after verification')
        return self._decode(raw, number)


def _fold(value, *, join_cjk=True):
    """Search-only normalization; never apply this to result/source fields."""
    value = unicodedata.normalize('NFKC', value).casefold()
    value = value.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789'))
    value = ''.join(char for char in value if char != '\u0640' and not (
        unicodedata.category(char).startswith('M') and
        ('ARABIC' in unicodedata.name(char, '') or '\u0610' <= char <= '\u061a' or
         '\u064b' <= char <= '\u065f' or char == '\u0670' or
         '\u06d6' <= char <= '\u06ed' or '\u08d3' <= char <= '\u08ff')
    ))
    value = value.translate(str.maketrans({'\u064a': '\u06cc', '\u0643': '\u06a9', '\u200c': '', '\u200d': ''}))
    if join_cjk:
        value = _CJK_SPACING.sub('', value)
    return ' '.join(value.split())


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)
    elif type(value) in (int, float):
        yield str(value)


def _tag_values(record):
    values = list(record['editorial_tags'])
    for topic in record['topic_tags']:
        values.extend((topic['id'], topic['label']))
    return set(value for value in values if value)


def _keys(record):
    # Explicit bibliographic fields keep complete parent narrations and lesson
    # explanations in source.original_metadata out of quotation-only searches.
    # This changes disposable search keys, never the preserved source object.
    source, narrator = record.get('source') or {}, record.get('narrator') or {}
    values = [record.get(field) for field in _PRIMARY_SEARCH_FIELDS]
    values += [source.get(field) for field in _SOURCE_SEARCH_FIELDS]
    values += [narrator.get(field) for field in _NARRATOR_SEARCH_FIELDS]
    values += list(counterpart_search_values(record))
    # Normalize within each source field, then separate fields so a CJK substring
    # cannot be manufactured by joining a title to the start of the narration.
    body = '\n'.join(_fold(s) for value in values for s in _strings(value))
    annotation_values = [record.get(field) for field in ('commentary', 'benefits', 'footnotes')]
    annotation_values += [source.get(field) for field in _SOURCE_CONTEXT_FIELDS]
    annotation_values.append(narrator.get('source_context'))
    annotations = '\n'.join(_fold(s) for value in annotation_values for s in _strings(value))
    return body, annotations


def _validate_record(root, record):
    missing = set(_REQUIRED_FIELDS) - set(record)
    if missing:
        raise ValueError('Flat narration is missing fields: ' + ', '.join(sorted(missing)))
    for field in ('id', 'language', 'source_language_code', 'book_key', 'edition', 'source_id'):
        if not isinstance(record[field], str) or not record[field]:
            raise ValueError('Flat narration requires nonempty ' + field)
    for field in ('provider_entry_id', 'title', 'text_arabic', 'text_translation'):
        if record[field] is not None and not isinstance(record[field], str):
            raise ValueError('Flat narration ' + field + ' must be a string or null')
    if not record['text_arabic'] and not record['text_translation']:
        raise ValueError('Flat narration has neither Arabic nor translation text')
    for field in ('number', 'source', 'translator', 'translation_provenance', 'review',
                  'commentary', 'references', 'page'):
        if not isinstance(record[field], dict):
            raise ValueError('Flat narration ' + field + ' must be an object')
    if record['narrator'] is not None and not isinstance(record['narrator'], dict):
        raise ValueError('Flat narration narrator must be an object or null')
    if not isinstance(record['footnotes'], list):
        raise ValueError('Flat narration footnotes must be an array')
    if record.get('benefits') is not None and not isinstance(record['benefits'], dict):
        raise ValueError('Flat narration benefits must be an object or null when supplied')
    for field in ('editorial_tags', 'source_headings'):
        if not isinstance(record[field], list) or any(not isinstance(x, str) for x in record[field]):
            raise ValueError('Flat narration ' + field + ' must be a string array')
    if not isinstance(record['topic_tags'], list):
        raise ValueError('Flat narration topic_tags must be an array')
    for tag in record['topic_tags']:
        if (not isinstance(tag, dict) or not isinstance(tag.get('id'), str) or
                not isinstance(tag.get('label'), str) or not isinstance(tag.get('path'), list) or
                any(not isinstance(x, str) for x in tag['path'])):
            raise ValueError('Topic tags require string id/label and a string path array')
    provenance = record['translation_provenance']
    if not isinstance(provenance.get('origin'), str) or not provenance['origin']:
        raise ValueError('Translation provenance requires an explicit origin state')
    if type(provenance.get('ai_translation')) is not bool and provenance.get('ai_translation') != 'unknown':
        raise ValueError('Translation provenance ai_translation must be true, false or unknown')
    source = record['source']
    for field in ('name', 'url', 'record_url', 'format'):
        if source.get(field) is not None and not isinstance(source[field], str):
            raise ValueError('Source ' + field + ' must be a string or null')
    original = _local(root, source.get('original_file'))
    _sha(source.get('sha256'), 'source.sha256')
    locator = source.get('record_locator')
    if not isinstance(locator, dict):
        raise ValueError('Source requires a record_locator object')
    _local(root, locator.get('path'))
    pointer = locator.get('json_pointer')
    line = locator.get('line')
    if not ((isinstance(pointer, str) and (pointer == '' or pointer.startswith('/'))) or
            (type(line) is int and line >= 1)):
        raise ValueError('Source record_locator requires a JSON pointer or positive line')
    return original


def _cache_path(root, database):
    if database == ':memory:':
        return None
    value = DEFAULT_DATABASE if database is None else str(database)
    given = Path(value)
    if given.is_absolute():
        try:
            value = given.relative_to(root).as_posix()
        except ValueError as error:
            raise ValueError('Search cache must be under root/.cache') from error
    if not value.startswith('.cache/'):
        raise ValueError('Search cache must be under root/.cache')
    path = _local(root, value, required=False)
    if path.suffix not in ('.sqlite', '.sqlite3', '.db'):
        raise ValueError('Search cache needs a .sqlite, .sqlite3 or .db suffix')
    if path.exists() and not path.is_file():
        raise ValueError('Search cache path is not a regular file')
    return path


def _connect(path, *, readonly=False):
    if path is None:
        connection = sqlite3.connect(':memory:')
    elif readonly:
        connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    else:
        connection = sqlite3.connect(path)
    try:
        connection.execute('PRAGMA trusted_schema=OFF')
        connection.execute('PRAGMA foreign_keys=ON')
    except BaseException:
        connection.close()
        raise
    return connection


def _create_fts(connection):
    try:
        connection.execute("CREATE VIRTUAL TABLE search_fts USING fts5(body, annotations, content='records', content_rowid='line', tokenize='trigram')")
        return 'trigram'
    except sqlite3.OperationalError:
        return 'like'


def _build_cache(connection, stream):
    connection.executescript('''
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE records(
            line INTEGER PRIMARY KEY, id TEXT NOT NULL, language TEXT NOT NULL,
            book_key TEXT NOT NULL, source_id TEXT NOT NULL, provider_entry_id TEXT,
            translation_origin TEXT NOT NULL, current_translation_origin TEXT NOT NULL,
            body TEXT NOT NULL, annotations TEXT NOT NULL
        );
        CREATE TABLE tags(record_line INTEGER NOT NULL, value TEXT NOT NULL,
            PRIMARY KEY(record_line, value), FOREIGN KEY(record_line) REFERENCES records(line));
        CREATE TABLE citation_pairs(record_line INTEGER NOT NULL, book_key TEXT NOT NULL, number TEXT NOT NULL,
            PRIMARY KEY(record_line, book_key, number), FOREIGN KEY(record_line) REFERENCES records(line));
        CREATE INDEX records_identity ON records(id);
        CREATE INDEX records_provider ON records(provider_entry_id);
        CREATE INDEX records_language ON records(language);
        CREATE INDEX records_book ON records(book_key);
        CREATE INDEX records_source ON records(source_id);
        CREATE INDEX records_origin ON records(translation_origin);
        CREATE INDEX records_current_origin ON records(current_translation_origin);
        CREATE INDEX tags_value ON tags(value, record_line);
        CREATE INDEX citation_pair_values ON citation_pairs(book_key, number, record_line);
    ''')
    engine = _create_fts(connection)
    with connection:
        for line, record in stream.records():
            _validate_record(stream.root, record)
            body, annotations = _keys(record)
            connection.execute('INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
                line, record['id'], record['language'], record['book_key'], record['source_id'],
                record['provider_entry_id'], record['translation_provenance']['origin'],
                current_translation_origin(record), body, annotations,
            ))
            connection.executemany('INSERT INTO tags VALUES (?, ?)',
                                   ((line, tag) for tag in sorted(_tag_values(record))))
            connection.executemany('INSERT INTO citation_pairs VALUES (?, ?, ?)',
                                   ((line, key, number) for key, number in sorted(record_citation_pairs(record))))
        if engine == 'trigram':
            connection.execute("INSERT INTO search_fts(search_fts) VALUES ('rebuild')")
        connection.executemany('INSERT INTO metadata VALUES (?, ?)', [
            ('version', CACHE_VERSION), ('records_sha256', stream.sha256),
            ('count', str(stream.count)), ('engine', engine),
        ])
    return engine


def _read_cache(path, stream):
    if not path.is_file():
        return None
    receipt = _local(stream.root, path.relative_to(stream.root).as_posix() + '.meta.json', required=False)
    try:
        data = _json(receipt.read_text(encoding='utf-8'))
        if (not isinstance(data, dict) or data.get('version') != CACHE_VERSION or
                data.get('records_sha256') != stream.sha256 or data.get('count') != stream.count or
                data.get('database_sha256') != _hash_file(path)):
            return None
        connection = _connect(path, readonly=True)
        try:
            metadata = dict(connection.execute('SELECT key, value FROM metadata'))
            if (metadata.get('version') != CACHE_VERSION or metadata.get('records_sha256') != stream.sha256 or
                    metadata.get('count') != str(stream.count) or metadata.get('engine') not in ('trigram', 'like') or
                    connection.execute('SELECT COUNT(*) FROM records').fetchone()[0] != stream.count):
                connection.close()
                return None
            return connection, metadata['engine']
        except sqlite3.DatabaseError:
            connection.close()
            return None
    except (OSError, UnicodeError, ValueError, sqlite3.DatabaseError):
        return None


def _cache(stream, database):
    path = _cache_path(stream.root, database)
    if path is None:
        connection = _connect(None)
        try:
            engine = _build_cache(connection, stream)
            return connection, engine, True, None
        except Exception:
            connection.close()
            raise
    cached = _read_cache(path, stream)
    if cached is not None:
        return cached[0], cached[1], False, path
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='hadith-search-', suffix='.sqlite', dir=path.parent)
    os.close(handle)
    temporary = Path(temporary)
    connection = None
    try:
        connection = _connect(temporary)
        engine = _build_cache(connection, stream)
        connection.close()
        connection = None
        receipt = {'version': CACHE_VERSION, 'records_sha256': stream.sha256,
                   'count': stream.count, 'database_sha256': _hash_file(temporary)}
        temporary.replace(path)
        receipt_path = _local(stream.root, path.relative_to(stream.root).as_posix() + '.meta.json', required=False)
        receipt_path.write_text(_canonical(receipt) + '\n', encoding='utf-8')
        return _connect(path, readonly=True), engine, True, path
    finally:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)


def _like(value):
    return '%' + value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


def _where(terms, filters, include_commentary, engine, citation_pairs=()):
    clauses, parameters = [], []
    for key in ('language', 'book_key', 'source_id'):
        if filters.get(key) is not None:
            clauses.append('r.' + key + ' = ?')
            parameters.append(filters[key])
    if filters.get('translation_origin') is not None:
        origin = filters['translation_origin']
        column = 'current_translation_origin' if origin in ('human', 'ai', 'unknown') else 'translation_origin'
        clauses.append('r.' + column + ' = ?')
        parameters.append(origin)
    if filters['entry_id'] is not None:
        clauses.append('(r.id = ? OR r.provider_entry_id = ?)')
        parameters.extend([filters['entry_id'], filters['entry_id']])
    if filters['tag'] is not None:
        clauses.append('EXISTS (SELECT 1 FROM tags t WHERE t.record_line = r.line AND t.value = ?)')
        parameters.append(filters['tag'])
    for book_key, number in citation_pairs:
        clauses.append('EXISTS (SELECT 1 FROM citation_pairs c WHERE c.record_line = r.line AND c.book_key = ? AND c.number = ?)')
        parameters.extend((book_key, number))
    if engine == 'trigram':
        long_terms = [term for term in terms if len(term) >= 3]
        if long_terms:
            phrases = ['"' + term.replace('"', '""') + '"' for term in long_terms]
            if not include_commentary:
                phrases = ['body : ' + phrase for phrase in phrases]
            clauses.append('r.line IN (SELECT rowid FROM search_fts WHERE search_fts MATCH ?)')
            parameters.append(' AND '.join(phrases))
    expression = "(r.body || char(10) || r.annotations)" if include_commentary else 'r.body'
    for term in terms:
        clauses.append(expression + " LIKE ? ESCAPE '\\'")
        parameters.append(_like(term))
    return (' WHERE ' + ' AND '.join(clauses) if clauses else ''), parameters


def _matches(record, terms, filters, include_commentary, citation_pairs=()):
    origin = (current_translation_origin(record) if filters['translation_origin'] in ('human', 'ai', 'unknown')
              else record['translation_provenance']['origin'])
    for key, value in [('language', record['language']), ('book_key', record['book_key']),
                       ('source_id', record['source_id']),
                       ('translation_origin', origin)]:
        if filters[key] is not None and value != filters[key]:
            return False
    if filters['entry_id'] is not None and filters['entry_id'] not in (record['id'], record['provider_entry_id']):
        return False
    if filters['tag'] is not None and filters['tag'] not in _tag_values(record):
        return False
    if not set(citation_pairs).issubset(record_citation_pairs(record)):
        return False
    body, annotations = _keys(record)
    searchable = body + ('\n' + annotations if include_commentary else '')
    return all(term in searchable for term in terms)


def search(root, query='', *, language=None, book=None, source=None, entry_id=None,
           tag=None, translation_origin=None, limit=10, include_commentary=False,
           database=None):
    """Return matched/shown/results; every returned text comes from verified JSONL."""
    root = Path(root).resolve()
    if not isinstance(query, str) or '\x00' in query:
        raise ValueError('Query must be a string without NUL characters')
    if type(limit) is not int or limit < 0:
        raise ValueError('Limit must be a nonnegative integer')
    if type(include_commentary) is not bool:
        raise ValueError('include_commentary must be a boolean')
    for name, value in [('language', language), ('book', book), ('source', source),
                        ('entry_id', entry_id), ('tag', tag), ('translation_origin', translation_origin)]:
        if value is not None and not isinstance(value, str):
            raise ValueError(name + ' must be a string or null')
    filters = {'language': LANGUAGE_ALIASES.get(language, language), 'book_key': book,
               'source_id': source, 'entry_id': entry_id, 'tag': tag,
               'translation_origin': translation_origin}
    citation_pairs, other_query = split_citation_query(_fold(query, join_cjk=False))
    terms = list(dict.fromkeys(other_query.split()))
    catalog = _load_catalog(root)
    stream = VerifiedStream(root, catalog['search'])
    connection, engine, rebuilt, cache_path = _cache(stream, database)
    try:
        where, parameters = _where(terms, filters, include_commentary, engine, citation_pairs)
        try:
            matched = connection.execute('SELECT COUNT(*) FROM records r' + where, parameters).fetchone()[0]
            selected = connection.execute('SELECT r.line FROM records r' + where + ' ORDER BY r.line LIMIT ?',
                                          parameters + [limit]).fetchall()
        except sqlite3.OperationalError:
            # Some SQLite builds accept the table but lack a query capability.
            # The literal LIKE fallback has the same matching semantics.
            where, parameters = _where(terms, filters, include_commentary, 'like', citation_pairs)
            matched = connection.execute('SELECT COUNT(*) FROM records r' + where, parameters).fetchone()[0]
            selected = connection.execute('SELECT r.line FROM records r' + where + ' ORDER BY r.line LIMIT ?',
                                          parameters + [limit]).fetchall()
            engine = 'like'
        results = []
        source_hashes = {}
        for (line,) in selected:
            record = stream.record(line)
            original = _validate_record(root, record)
            if not _matches(record, terms, filters, include_commentary, citation_pairs):
                raise ValueError('Cached result disagrees with the verified source record; remove the disposable cache')
            if original not in source_hashes:
                source_hashes[original] = _hash_file(original)
            if source_hashes[original] != record['source']['sha256'].lower():
                raise ValueError('SHA-256 mismatch for result original source: ' + record['source']['original_file'])
            # Retain optional provenance/grade/version fields too. The concise
            # default omits annotations only; it must not discard metadata.
            result = {field: value for field, value in record.items()
                      if include_commentary or field not in _ANNOTATION_FIELDS}
            result['url'] = record['source'].get('record_url') or record['source'].get('url')
            if include_commentary:
                result['commentary'] = record['commentary']
                result['footnotes'] = record['footnotes']
                if 'benefits' in record:
                    result['benefits'] = record['benefits']
            results.append(result)
        return {
            'schema': VERSION, 'query': query, 'filters': filters,
            'query_interpretation': {'citation_pairs': [{'book_key': key, 'number': number} for key, number in citation_pairs], 'text_terms': terms},
            'matched': matched, 'shown': len(results), 'limit': limit,
            'include_commentary': include_commentary,
            'results': results,
            'integrity': {'records_sha256': stream.sha256, 'records_verified': stream.count,
                          'input_mode': stream.mode, 'input_files_verified': len(stream.files),
                          'result_source_files_verified': len(source_hashes)},
            'cache': {'rebuilt': rebuilt, 'engine': engine,
                      'path': cache_path.relative_to(root).as_posix() if cache_path else ':memory:'},
            'review_note': 'Search preserves per-record provenance and review status; it performs no translation or release review.',
        }
    finally:
        connection.close()


def format_results(result):
    """Human output emphasizes narration, attribution and translation origin."""
    lines = [f"{result['matched']} matching occurrences; showing {result['shown']}."]
    for index, item in enumerate(result['results'], 1):
        lines.extend(['', f"{index}. {item['id']}",
                      f"Language: {item['language']} | Book: {item['book_key']} | Edition: {item['edition']}"])
        if item['title']:
            lines.append('Title: ' + item['title'])
        number = item['number'].get('in_book')
        if number is not None:
            label = 'Source number: ' if has_noncanonical_numbering(item['number']) else 'Printed number: '
            lines.append(label + str(number))
        if item['provider_entry_id'] is not None:
            lines.append('Provider entry: ' + item['provider_entry_id'])
        lines.extend(['', 'Arabic:', item['text_arabic'] or '(not supplied)',
                      '', 'Translation:', item['text_translation'] or '(not supplied)'])
        for language in ('arabic', 'english'):
            counterpart = counterpart_data(item, language)
            if counterpart is None:
                continue
            lines.extend(['', language.title() + ' counterpart:', counterpart['text'],
                          counterpart_citation(counterpart, language)])
            qualification = counterpart_qualification(counterpart, item)
            if qualification:
                lines.append(qualification)
            lines.append('Counterpart source: ' + (counterpart.get('source_name') or '(not named)'))
            if counterpart.get('source_url'):
                lines.append('Counterpart URL: ' + counterpart['source_url'])
            if language == 'english':
                lines.append('Counterpart translation origin: ' + ('Human' if counterpart.get('translation_origin') == 'human' else 'Unknown'))
        narrator = item['narrator'] or {}
        if narrator.get('name'):
            lines.extend(['', 'Narrator: ' + str(narrator['name'])])
        translator = item['translator'].get('name')
        provenance = item['translation_provenance']
        origin = current_translation_origin(item).title()
        historical_origin = provenance.get('label') or provenance['origin']
        lines.extend(['', 'Source: ' + (item['source'].get('name') or item['source_id']),
                      'URL: ' + (item['url'] or '(not supplied)'),
                      'Translator: ' + (str(translator) if translator is not None else '(not named in supplied source)'),
                      'Translation origin: ' + origin,
                      'Source-origin history: ' + historical_origin + ' [' + provenance['origin'] + ']',
                      'Preserved source AI translation: ' + str(provenance['ai_translation']).lower()])
        page = item['page']
        locations = []
        if page.get('pdf'):
            locations.append('PDF page ' + ', '.join(str(p) for p in page['pdf']))
        if page.get('printed'):
            locations.append('printed page ' + ', '.join(str(p) for p in page['printed']))
        if page.get('sheet') is not None:
            locations.append('sheet ' + str(page['sheet']))
        if page.get('row') is not None:
            locations.append('row ' + str(page['row']))
        if page.get('docx_paragraphs'):
            locations.append('DOCX paragraph ' + ', '.join(str(p) for p in page['docx_paragraphs']))
        if locations:
            lines.append('Location: ' + '; '.join(locations))
        review = item['review']
        current_policy = review.get('current_policy')
        current_label = current_policy.get('label') if isinstance(current_policy, dict) else None
        hide_qc = item.get('display_policy', {}).get('qc_tags') is False
        if not hide_qc:
            if current_label:
                lines.append('Current review policy: ' + str(current_label))
            review_prefix = 'Historical import review: ' if current_label else 'Review: '
            lines.append(review_prefix + str(review.get('status', 'unknown')) +
                         '; independent Pro QC: ' + str(review.get('independent_pro_qc', 'unknown')) +
                         '; release: ' + str(review.get('release_status', 'unknown')))
        issues = review.get('issues')
        if issues:
            lines.append(('Source notes: ' if hide_qc else 'Recorded issues: ') + '; '.join(_strings(issues)))
        if result['include_commentary']:
            commentary = item['commentary']
            for field, label in [('arabic', 'Arabic commentary'), ('translation', 'Translated commentary')]:
                if commentary.get(field):
                    lines.extend(['', label + ':', commentary[field]])
            benefits = item.get('benefits') or {}
            for field, label in [('arabic', 'Arabic benefits'), ('translation', 'Translated benefits')]:
                supplied = list(_strings(benefits.get(field)))
                if supplied:
                    lines.extend(['', label + ':'] + supplied)
            if item['footnotes']:
                lines.extend(['', 'Footnotes:'] + list(_strings(item['footnotes'])))
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('query', nargs='?', default='', help='Literal words/substrings; all terms must match')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--language')
    parser.add_argument('--book')
    parser.add_argument('--source')
    parser.add_argument('--id', dest='entry_id', help='Exact provider entry ID or occurrence ID')
    parser.add_argument('--tag', help='Exact topic ID, topic label or editorial tag')
    parser.add_argument('--translation-origin',
                        help='Current human/ai/unknown category, or an exact historical origin label')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--json', action='store_true', help='Return structured JSON instead of reading text')
    parser.add_argument('--include-commentary', action='store_true',
                        help='Also search preserved source context and search/display commentary, benefits and footnotes')
    parser.add_argument('--database', help='Disposable database under root/.cache, or :memory:')
    args = parser.parse_args(argv)
    try:
        result = search(args.root, args.query, language=args.language, book=args.book,
                        source=args.source, entry_id=args.entry_id, tag=args.tag,
                        translation_origin=args.translation_origin, limit=args.limit,
                        include_commentary=args.include_commentary, database=args.database)
    except (OSError, ValueError, sqlite3.DatabaseError) as error:
        parser.exit(1, 'Hadith search failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_results(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
