#!/usr/bin/env python3
"""Acquire official Arabic/English companion snapshots without changing bank text.

Bulk SQLite exports are preferred to per-entry API calls. A valid existing
snapshot is reused without network requests. New explicit provider IDs or
--refresh fetch current exports; --offline only verifies/reuses local sources.
Raw source bytes are immutable: changed downloads receive content-addressed
filenames and the previous manifest is retained before the current pointer moves.
"""
import argparse
from contextlib import closing
import datetime
import email.utils
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import time
import urllib.error
import urllib.request
import zipfile

SCHEMA = 'hadith-bank-hadeethenc-counterpart-sources-v1'
BASE = Path('sources/counterparts/hadeethenc')
USER_AGENT = 'Hadith-Bank source comparison (public API)'
TERMS_URL = 'https://hadeethenc.com/en/home'
VERSION_URL = 'https://hadeethenc.com/en/check/en/v1.0.0'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def local(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Unsafe counterpart source path')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe counterpart source path')
    result = root / path
    if any(parent.is_symlink() for parent in [result, *result.parents]):
        raise ValueError('Counterpart source path contains a symlink')
    if not result.resolve().is_relative_to(root):
        raise ValueError('Counterpart source escaped the repository')
    return result


def descriptor(root, path):
    return {'path': path.relative_to(root).as_posix(),
            'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size}


def store_bytes(root, snapshot, filename, data):
    directory = local(root, (snapshot / 'raw').as_posix())
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / filename
    if target.exists() and target.read_bytes() != data:
        target = directory / (digest(data)[:16] + '-' + filename)
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError('Content-addressed source collision')
    else:
        temporary = target.with_suffix(target.suffix + '.partial')
        temporary.write_bytes(data)
        temporary.replace(target)
    return target


def _retry_wait(error, attempt):
    value = error.headers.get('Retry-After')
    try:
        delay = float(value) if value is not None else 2 ** (attempt + 1)
    except ValueError:
        try:
            moment = email.utils.parsedate_to_datetime(value)
            delay = (moment - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        except (TypeError, ValueError):
            delay = 2 ** (attempt + 1)
    if delay > 600:
        raise RuntimeError('Provider requested a later retry; leave the saved snapshot unchanged') from error
    remaining = max(1, delay)
    while remaining > 0:
        part = min(30, remaining)
        time.sleep(part)
        remaining -= part


def fetch(url, limit=64 * 1024 * 1024):
    """Read only documented public provider resources and respect rate limits."""
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={
                'User-Agent': USER_AGENT, 'Accept': '*/*'})
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read(limit + 1)
                if len(raw) > limit:
                    raise ValueError('Provider source exceeds the bounded download size')
                return raw, {'source_url': url, 'final_url': response.url,
                             'http_status': response.status,
                             'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        except urllib.error.HTTPError as error:
            if attempt == 3 or error.code not in (429, 500, 502, 503, 504):
                raise
            _retry_wait(error, attempt)


def _unpack(raw, language):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        expected = language + '.sqlite'
        if archive.namelist() != [expected]:
            raise ValueError('Unexpected files in the provider SQLite archive')
        member = archive.getinfo(expected)
        if member.file_size > 128 * 1024 * 1024:
            raise ValueError('Expanded provider database exceeds the bounded size')
        return archive.read(expected)


def _connect(path):
    connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def english_ids(path):
    with closing(_connect(path)) as connection:
        columns = {row[1] for row in connection.execute('PRAGMA table_info(hadeeths)')}
        if not {'id', 'hadeeth', 'hadeeth_ar', 'ar_version'} <= columns:
            raise ValueError('Official English export lacks required source fields')
        rows = list(connection.execute('SELECT id, hadeeth, hadeeth_ar FROM hadeeths'))
    ids = [str(row['id']) for row in rows]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r'[1-9][0-9]*', item) for item in ids):
        raise ValueError('Duplicate or invalid provider IDs in English export')
    if any(not isinstance(row['hadeeth'], str) or not row['hadeeth'].strip() for row in rows):
        raise ValueError('English export contains a missing hadith body')
    return set(ids)


def required_provider_ids(root):
    from counterpart_identity import provider_id
    from material_registry import checked_file, load_public_materials, read_rows
    # Read the accepted canonical registries, not yesterday's generated search
    # shards: this runs before the reader refresh when a new import is published.
    found = set()
    catalog_path = local(root, 'datasets/hadeethenc/collections.json')
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
        for collection in catalog['collections']:
            path = checked_file(root, collection['records_path'], collection['records_sha256'])
            for row in read_rows(path):
                identifier = provider_id({'book_key': 'hadeethenc',
                                          'provider_entry_id': row.get('source_entry_id')})
                if identifier is not None:
                    found.add(identifier)
    registry = load_public_materials(root)
    for group in registry['groups']:
        for row in group:
            if (identifier := provider_id(row)) is not None:
                found.add(identifier)
    return found


def verify_manifest(root, manifest):
    if manifest.get('schema') != SCHEMA:
        raise ValueError('Unrecognized counterpart source manifest')
    entries = [manifest['english_database'], manifest['arabic_database']]
    entries.extend(manifest.get('raw_exports', []))
    entries.extend(manifest.get('api_arabic_evidence', []))
    for auxiliary in manifest.get('auxiliary_translation_databases', []):
        entries.append(auxiliary)
        if auxiliary.get('version_evidence'):
            entries.append(auxiliary['version_evidence'])
    if manifest.get('version_evidence'):
        entries.append(manifest['version_evidence'])
    for entry in entries:
        path = local(root, entry['path'])
        if not path.is_file() or digest(path.read_bytes()) != entry['sha256']:
            raise ValueError('Counterpart source SHA-256 mismatch: ' + entry['path'])
    return english_ids(local(root, manifest['english_database']['path']))


def alignment(root, english_path, arabic_path):
    exact, missing, different = 0, [], []
    with closing(_connect(english_path)) as english, closing(_connect(arabic_path)) as arabic:
        index = {}
        for row in arabic.execute('SELECT id, version, hadeeth FROM hadeeths'):
            index.setdefault((row['id'], row['version']), []).append(row['hadeeth'])
        for row in english.execute('SELECT id, ar_version, hadeeth_ar FROM hadeeths ORDER BY id'):
            matches = index.get((row['id'], row['ar_version']), [])
            item = {'id': str(row['id']), 'arabic_version': row['ar_version']}
            if not matches:
                missing.append(item)
            elif row['hadeeth_ar'] in matches:
                exact += 1
            else:
                different.append(item)
    return {'exact_provider_id_version_and_text_match': exact,
            'missing_version': missing, 'different_text': different}


def _write_manifest(root, manifest):
    path = local(root, (BASE / 'manifest.json').as_posix())
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if path.exists() and path.read_bytes() != raw:
        archive = path.parent / 'manifests'
        archive.mkdir(exist_ok=True)
        old = path.read_bytes()
        (archive / (digest(old) + '.json')).write_bytes(old)
    temporary = path.with_suffix('.partial')
    temporary.write_bytes(raw)
    temporary.replace(path)


def _snapshot_stamp(snapshot=None):
    stamp = snapshot or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}(?:T[0-9]{6})?', stamp):
        raise ValueError('Snapshot must use YYYY-MM-DD or YYYY-MM-DDTHHMMSS')
    return stamp


def _sync_auxiliary(root, manifest, languages, *, refresh=False, offline=False, snapshot=None):
    """Cache publisher translations used only to verify an existing occurrence."""
    entries = {entry['language']: entry for entry in manifest.get('auxiliary_translation_databases', [])}
    for language in sorted(languages):
        if not re.fullmatch(r'[a-z]{2,3}', language) or language in ('ar', 'en'):
            raise ValueError('Auxiliary language must be another provider language code')
        if language in entries and (not refresh or offline):
            continue
        if offline:
            raise ValueError('No verified auxiliary translation snapshot exists: ' + language)
        directory = BASE / _snapshot_stamp(snapshot)
        url = 'https://hadeethenc.com/downloads/sqlite/' + language + '.sqlite.zip'
        raw, metadata = fetch(url)
        archive = store_bytes(root, directory, language + '.sqlite.zip', raw)
        database = store_bytes(root, directory, language + '.sqlite', _unpack(raw, language))
        available = english_ids(database)
        version_bytes, version_meta = fetch('https://hadeethenc.com/en/check/' + language + '/v1.0.0')
        version_path = store_bytes(root, directory, 'version-' + language + '.html', version_bytes)
        match = re.search(r'There is a new version\s*\((v[0-9.]+)\)', version_bytes.decode('utf-8'))
        entries[language] = {'language': language, **descriptor(root, database),
                             'rows': len(available), 'version': match.group(1) if match else None,
                             'source_url': url, 'retrieved_at': metadata['retrieved_at'],
                             'version_evidence': descriptor(root, version_path)}
        manifest['raw_exports'].extend([{**metadata, **descriptor(root, archive)},
                                       {**version_meta, **descriptor(root, version_path)}])
    if entries:
        manifest['auxiliary_translation_databases'] = [entries[key] for key in sorted(entries)]


def sync(root, *, refresh=False, offline=False, required_ids=None, snapshot=None,
         auxiliary_languages=None):
    root = Path(root).resolve()
    required = set(required_provider_ids(root) if required_ids is None else required_ids)
    if any(not isinstance(item, str) or not re.fullmatch(r'[1-9][0-9]*', item) for item in required):
        raise ValueError('Required counterpart identities must be positive provider ID strings')
    current = local(root, (BASE / 'manifest.json').as_posix())
    auxiliary = set(auxiliary_languages or [])
    if current.is_file():
        previous = json.loads(current.read_text(encoding='utf-8'))
        available = verify_manifest(root, previous)
        auxiliary.update(entry['language'] for entry in previous.get('auxiliary_translation_databases', []))
        if (not refresh and required <= available) or offline:
            result = json.loads(json.dumps(previous))
            result['requested_provider_ids'] = sorted(required, key=int)
            result['requested_id_count'] = len(required)
            result['missing_provider_ids'] = sorted(required - available, key=int)
            result['additional_provider_ids'] = sorted(available - required, key=int)
            _sync_auxiliary(root, result, auxiliary, offline=offline, snapshot=snapshot)
            verify_manifest(root, result)
            if result != previous:
                _write_manifest(root, result)
            return result
    elif offline:
        raise ValueError('No verified local counterpart source snapshot exists')
    stamp = _snapshot_stamp(snapshot)
    directory = BASE / stamp
    exports, databases = [], {}
    for language in ('en', 'ar'):
        url = 'https://hadeethenc.com/downloads/sqlite/' + language + '.sqlite.zip'
        raw, metadata = fetch(url)
        archive = store_bytes(root, directory, language + '.sqlite.zip', raw)
        database = store_bytes(root, directory, language + '.sqlite', _unpack(raw, language))
        exports.append({**metadata, **descriptor(root, archive)})
        databases[language] = database
    version_bytes, version_meta = fetch(VERSION_URL)
    version_path = store_bytes(root, directory, 'version-en.html', version_bytes)
    exports.append({**version_meta, **descriptor(root, version_path)})
    match = re.search(r'There is a new version\s*\((v[0-9.]+)\)', version_bytes.decode('utf-8'))
    available = english_ids(databases['en'])
    manifest = {
        'schema': SCHEMA, 'snapshot': stamp, 'provider': 'HadeethEnc.com',
        'english_database': {**descriptor(root, databases['en']), 'rows': len(available)},
        'arabic_database': descriptor(root, databases['ar']),
        'english_version': match.group(1) if match else None,
        'retrieved_at': exports[0]['retrieved_at'], 'source_url': exports[0]['source_url'],
        'terms_url': TERMS_URL, 'api_documentation_url': 'https://github.com/islamhouse-dev/hadith-api',
        'version_evidence': descriptor(root, version_path), 'raw_exports': exports,
        'requested_provider_ids': sorted(required, key=int), 'requested_id_count': len(required),
        'downloaded_id_count': len(available), 'missing_provider_ids': sorted(required - available, key=int),
        'additional_provider_ids': sorted(available - required, key=int),
        'arabic_alignment': alignment(root, databases['en'], databases['ar']),
        'translation_classification': 'human',
        'classification_basis': 'owner_source_confirmation_and_publisher_translation_workflow',
        'content_policy': {'preserve_source_text': True, 'companion_only': True,
                           'independent_translation_or_authenticity_certification': False,
                           'reuse_conditions': 'Publisher conditions require unchanged content, attribution, version information and current-version maintenance.'}}
    _sync_auxiliary(root, manifest, auxiliary, refresh=True, snapshot=stamp)
    verify_manifest(root, manifest)
    _write_manifest(root, manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--snapshot')
    parser.add_argument('--auxiliary-language', action='append', default=[],
                        help='Cache this provider translation as identity evidence, not as bank occurrences')
    args = parser.parse_args()
    try:
        result = sync(args.root, refresh=args.refresh, offline=args.offline, snapshot=args.snapshot,
                      auxiliary_languages=args.auxiliary_language)
    except (OSError, ValueError, KeyError, RuntimeError, sqlite3.Error, zipfile.BadZipFile) as error:
        parser.exit(1, 'Counterpart sync failed; existing source bytes retained: ' + str(error) + '\n')
    print(json.dumps({'status': 'complete' if not result['missing_provider_ids'] else 'partial',
                      'requested': result['requested_id_count'], 'available': result['downloaded_id_count'],
                      'missing_provider_ids': result['missing_provider_ids'], 'english_version': result['english_version'],
                      'manifest': (BASE / 'manifest.json').as_posix()}, ensure_ascii=False, indent=2))
    return 0 if not result['missing_provider_ids'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
