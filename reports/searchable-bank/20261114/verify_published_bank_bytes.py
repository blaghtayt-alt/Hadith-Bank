#!/usr/bin/env python3
"""Bounded, read-only HTTP evidence for an already deployed Hadith Bank.

Only the explicitly requested JSON report is written. Full quotation text is
neither saved nor printed. This samples three complete records; it is not a
replacement for full-corpus build validation or browser acceptance.
"""
import sys
sys.dont_write_bytecode = True

import argparse
from collections import OrderedDict
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import importlib
import json
from pathlib import Path, PurePosixPath
import re
import signal
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zlib

IDENTITY = ('id', 'language', 'book_key', 'edition', 'source_id')
HEX = re.compile(r'[0-9a-f]{64}\Z')
MAX_HTML = 16 * 1024 * 1024
MAX_METADATA = 4 * 1024 * 1024
MAX_CORE = 16 * 1024 * 1024
MAX_CORE_PLAIN = 128 * 1024 * 1024
MAX_PART = 2 * 1024 * 1024
MAX_RECORD = 2 * 1024 * 1024
MAX_NETWORK = 64 * 1024 * 1024
MAX_REQUESTS = 24
MAX_ROWS = 500000
MAX_PARTS = 10000
MAX_CACHE = 8 * 1024 * 1024


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, minimum=0, maximum=(1 << 53) - 1):
    return type(value) is int and minimum <= value <= maximum


def identifier(value):
    return (isinstance(value, str) and 0 < len(value) <= 2048 and value.strip()
            and re.search(r'[\x00-\x1f\x7f]', value) is None)


def hash_value(value):
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def identity(value):
    require(isinstance(value, dict) and all(identifier(value.get(k)) for k in IDENTITY),
            'Missing or invalid complete source identity')
    return tuple(value[k] for k in IDENTITY)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON object key')
            result[key] = value
        return result

    def invalid_constant(_):
        raise VerificationError('Non-finite JSON number')

    text = raw.decode('utf-8', errors='strict') if isinstance(raw, bytes) else raw
    require(not text.startswith('\ufeff'), 'Unexpected UTF-8 BOM')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)


def object_digest(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode('utf-8'))


def decode_gzip(raw, expected, maximum):
    require(integer(expected, 1, maximum), 'Decoded gzip size exceeds the verifier bound')
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    output = bytearray()
    for offset in range(0, len(raw), 65536):
        block = raw[offset:offset + 65536]
        output.extend(decoder.decompress(block, expected + 1 - len(output)))
        require(len(output) <= expected, 'Gzip output exceeds the declared size')
        require(not decoder.unconsumed_tail, 'Gzip output exceeded the bounded decoder')
        require(not decoder.unused_data, 'Trailing data or concatenated gzip members')
    output.extend(decoder.flush(expected + 1 - len(output)))
    require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
            'Incomplete gzip stream or trailing data')
    require(len(output) == expected, 'Decoded gzip size differs from the descriptor')
    return bytes(output)


class EmbeddedJSON(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.items = {}
        self.active = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'script':
            return
        values = dict(attrs)
        key = values.get('id')
        if key not in ('hadith-snapshot', 'hadith-records'):
            return
        require(len(attrs) == len(values), 'Duplicate attributes on embedded payload')
        require(key not in self.items and self.active is None, 'Duplicate embedded payload')
        self.items[key] = {'attrs': values, 'text': []}
        self.active = key

    def handle_endtag(self, tag):
        if tag.lower() == 'script':
            self.active = None

    def handle_data(self, data):
        if self.active:
            self.items[self.active]['text'].append(data)

    def result(self):
        require(self.active is None and set(self.items) == {'hadith-snapshot', 'hadith-records'},
                'Required embedded snapshot/manifest is absent or incomplete')
        require(self.items['hadith-records']['attrs'].get('data-encoding') == 'gzip-jsonl-lazy-v2',
                'Expected a sharded gzip-jsonl-lazy-v2 published reader')
        return tuple(strict_json(''.join(self.items[key]['text']))
                     for key in ('hadith-snapshot', 'hadith-records'))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise VerificationError('HTTP redirects are not allowed')


class HTTPReader:
    def __init__(self, base, report, timeout, deadline, opener=None):
        parsed = urlsplit(base)
        require(len(base) <= 2048 and parsed.scheme == 'https' and parsed.hostname
                and not parsed.username and not parsed.password and not parsed.query
                and not parsed.fragment and re.search(r'[\\%\x00-\x20\x7f]', base) is None,
                'Use a credential-free HTTPS URL without query, fragment or escaped path')
        require(parsed.path.endswith('/') or parsed.path.endswith('.html'),
                'Base URL must end in / or name an .html page')
        require(all(x not in ('.', '..') for x in parsed.path.split('/')),
                'Base URL has a traversal segment')
        self.base = base
        self.origin = (parsed.scheme, parsed.hostname.lower(), parsed.port or 443)
        self.prefix = urlsplit(urljoin(base, '.')).path
        self.report = report
        self.timeout = timeout
        self.deadline = deadline
        self.opener = opener or build_opener(NoRedirect())
        self.requests = 0
        self.bytes = 0

    def local_url(self, path):
        require(isinstance(path, str) and 0 < len(path) <= 1024
                and re.fullmatch(r'[A-Za-z0-9_./-]+', path) is not None
                and not path.startswith('/')
                and all(x not in ('', '.', '..') for x in path.split('/')),
                'Unsafe local publication path')
        url = urljoin(self.base, path)
        parsed = urlsplit(url)
        require((parsed.scheme, parsed.hostname.lower(), parsed.port or 443) == self.origin
                and parsed.path.startswith(self.prefix), 'Publication path leaves the reader origin/directory')
        return url

    def fetch(self, url, kind, maximum, expected_bytes=None, expected_hash=None):
        parsed = urlsplit(url)
        require((parsed.scheme, parsed.hostname.lower(), parsed.port or 443) == self.origin
                and parsed.path.startswith(self.prefix), 'HTTP request leaves the approved reader directory')
        remaining = self.deadline - time.monotonic()
        require(remaining > 0 and self.requests < MAX_REQUESTS, 'HTTP deadline/request budget exhausted')
        require(integer(maximum, 1, MAX_NETWORK), 'Invalid response size bound')
        if expected_bytes is not None:
            require(integer(expected_bytes, 1, maximum), 'Declared response exceeds its permitted bound')
            maximum = expected_bytes
        require(expected_hash is None or hash_value(expected_hash), 'Invalid expected response digest')
        self.requests += 1
        entry = {'kind': kind, 'url': url, 'started_at_utc': now(), 'body_complete': False}
        self.report['http'].append(entry)
        request = Request(url, headers={'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache',
                                       'User-Agent': 'Hadith-Bank-independent-byte-verification/1'})
        chunks, sha, received = [], hashlib.sha256(), 0
        try:
            with self.opener.open(request, timeout=min(self.timeout, remaining)) as response:
                entry['status'] = response.status
                require(response.status == 200 and response.geturl() == url,
                        'Expected HTTP 200 at the exact requested URL without redirects')
                for name in ('Date', 'Content-Type', 'Content-Length', 'Content-Encoding',
                             'ETag', 'Last-Modified', 'Age'):
                    if response.headers.get(name) is not None:
                        entry[name.lower()] = str(response.headers[name])[:512]
                length = response.headers.get('Content-Length')
                if length is not None:
                    require(len(length) <= 20 and re.fullmatch(r'[0-9]+', length) is not None,
                            'Invalid HTTP Content-Length')
                    length = int(length)
                    require(length <= maximum and (expected_bytes is None or length == expected_bytes),
                            'HTTP Content-Length disagrees with the size bound/descriptor')
                require(response.headers.get('Content-Encoding', '').lower() in ('', 'identity'),
                        'Server applied an unexpected HTTP content encoding')
                request_deadline = min(self.deadline, time.monotonic() + self.timeout)
                while True:
                    require(time.monotonic() < request_deadline, 'HTTP response exceeded its time budget')
                    block = response.read1(min(65536, maximum + 1 - received))
                    if not block:
                        break
                    received += len(block)
                    self.bytes += len(block)
                    sha.update(block)
                    require(received <= maximum and self.bytes <= MAX_NETWORK,
                            'Response or aggregate network body budget exceeded')
                    chunks.append(block)
                require(length is None or received == length, 'Incomplete HTTP response body')
                require(expected_bytes is None or received == expected_bytes, 'Response byte count differs')
                entry.update(bytes=received, sha256=sha.hexdigest(), body_complete=True)
                require(expected_hash is None or entry['sha256'] == expected_hash,
                        'HTTP response SHA-256 differs from the expected publication')
                entry['expected_digest_verified'] = expected_hash is not None
                return b''.join(chunks), entry
        except Exception as error:
            entry.update(bytes=received, received_sha256=sha.hexdigest(),
                         error=type(error).__name__ + ': ' + str(error)[:500])
            raise
        finally:
            entry['finished_at_utc'] = now()


def validate_manifest(manifest, snapshot, http):
    require(isinstance(manifest, dict) and manifest.get('schema') == 'hadith-bank-reader-lazy-v2'
            and manifest.get('encoding') == 'gzip-jsonl-lazy-v2', 'Unsupported lazy manifest')
    count = snapshot['record_count']
    require(manifest.get('record_count') == count and hash_value(manifest.get('jsonl_sha256'))
            and integer(manifest.get('max_shard_bytes'), 1, MAX_PART), 'Lazy manifest count/hash/limit mismatch')
    delivery = snapshot.get('data_delivery') or {}
    require(delivery.get('encoding') == manifest['encoding'] and delivery.get('self_contained') is False
            and delivery.get('jsonl_sha256') == manifest['jsonl_sha256'], 'Snapshot/detail stream binding mismatch')
    paths, prefixes, part_count, detail_bytes = set(), set(), 0, 0
    for name in ('directory', 'search', 'annotations', 'details'):
        spec = manifest.get(name)
        require(isinstance(spec, dict) and spec.get('encoding') == 'gzip-jsonl-shards'
                and spec.get('record_count') == count and hash_value(spec.get('jsonl_sha256'))
                and integer(spec.get('max_shard_bytes'), 1, manifest['max_shard_bytes'])
                and isinstance(spec.get('shards'), list) and 0 < len(spec['shards']) <= MAX_PARTS,
                'Invalid lazy store metadata: ' + name)
        if name == 'details':
            require(spec.get('schema') == 'hadith-bank-reader-shards-v1'
                    and spec['jsonl_sha256'] == manifest['jsonl_sha256']
                    and integer(spec.get('plain_part_bytes'), 1, spec['max_shard_bytes']),
                    'Invalid complete-detail stream metadata')
        running_count = 0
        for index, part in enumerate(spec['shards']):
            require(isinstance(part, dict), 'Invalid part descriptor')
            http.local_url(part.get('path'))
            path = part['path']
            bits = PurePosixPath(path).parts
            require(len(bits) >= 3 and bits[-2] == name and path not in paths,
                    'Duplicate part or inconsistent store directory')
            paths.add(path)
            prefixes.add('/'.join(bits[:-2]))
            require(hash_value(part.get('sha256')) and integer(part.get('bytes'), 1, spec['max_shard_bytes'])
                    and integer(part.get('uncompressed_bytes'), 1, spec['max_shard_bytes'])
                    and integer(part.get('count'), 0, count), 'Invalid bounded shard descriptor')
            if name != 'details':
                require(integer(part.get('first_ordinal')) and integer(part.get('last_ordinal'))
                        and part.get('first_ordinal') == running_count and integer(part.get('count'), 1, count)
                        and part.get('last_ordinal') == running_count + part['count'] - 1,
                        'Noncontiguous directory/search/annotation ordinal range')
            else:
                size = spec['plain_part_bytes']
                require(part['uncompressed_bytes'] <= size and
                        (index == len(spec['shards']) - 1 or part['uncompressed_bytes'] == size),
                        'Noncontiguous complete-detail byte chunks')
                detail_bytes += part['uncompressed_bytes']
            running_count += part['count']
            part_count += 1
        require(running_count == count, 'Store aggregate occurrence count differs: ' + name)
    require(len(prefixes) == 1 and delivery.get('shard_count') == part_count,
            'Lazy store directory or snapshot part count differs')
    return prefixes.pop(), detail_bytes, part_count


def check_core_part(part, snapshot, http, core=True):
    require(isinstance(part, dict) and part.get('encoding') == 'gzip-json'
            and part.get('record_count') == snapshot['record_count']
            and part.get('records_sha256') == snapshot['records_sha256']
            and hash_value(part.get('sha256')) and hash_value(part.get('uncompressed_sha256'))
            and integer(part.get('bytes'), 1, MAX_CORE if core else MAX_PART)
            and integer(part.get('uncompressed_bytes'), 1, MAX_CORE_PLAIN if core else MAX_PART),
            'Invalid discovery size/hash/source binding')
    return http.local_url(part.get('path'))


def select_representatives(rows):
    fawaz = [r for r in rows if r['book_key'] == 'bukhari' and r['language'] == 'ar'
             and re.fullmatch(r'fawaz:[0-9a-f]{12}:bukhari:1', r['id'])
             and re.fullmatch(r'fawaz-bukhari-[0-9a-f]{12}-ar(?:-part-[0-9]+)?', r['source_id'])
             and 'bukhari:1' in (r.get('references') or [])]
    japanese = [r for r in rows if r['book_key'] == 'hadeethenc' and r['language'] == 'ja'
                and re.fullmatch(r'hadeethenc:entry:4560:translation:ja:revision:[0-9a-f]+', r['id'])]
    hindi = [r for r in rows if r['book_key'] == 'bukhari' and r['language'] == 'hi'
             and re.fullmatch(r'deenhindi-bukhari:[0-9]+', r['id'])
             and re.fullmatch(r'deenhindi-bukhari(?:-part-[0-9]+)?', r['source_id'])]
    require(len(fawaz) == 1 and len(japanese) == 1 and hindi,
            'Required Fawaz/Japanese/Hindi representatives are absent or ambiguous')
    minimum = min(int(r['id'].rsplit(':', 1)[1]) for r in hindi)
    hindi = [r for r in hindi if int(r['id'].rsplit(':', 1)[1]) == minimum]
    require(len(hindi) == 1, 'Lowest-number Hindi Bukhari identity is ambiguous')
    labels = ('fawaz_bukhari_1_arabic', 'hadeethenc_4560_japanese', 'hindi_bukhari')
    return [{'label': label, 'ordinal': row['ordinal'],
             'identity': {key: row[key] for key in IDENTITY},
             'canonical_references_from_index': row.get('references') or []}
            for label, row in zip(labels, (fawaz[0], japanese[0], hindi[0]))]


def verify_core(raw, descriptor, snapshot, repo_root):
    plain = decode_gzip(raw, descriptor['uncompressed_bytes'], MAX_CORE_PLAIN)
    require(digest(plain) == descriptor['uncompressed_sha256'], 'Core decoded SHA-256 differs')
    scripts = repo_root / 'scripts'
    require((scripts / 'bank_discovery.py').is_file(), 'Local pure schema decoder is unavailable')
    sys.path.insert(0, str(scripts))
    expand = importlib.import_module('bank_discovery').expand_discovery_payload
    payload = expand(strict_json(plain))
    require(isinstance(payload, dict) and payload.get('schema') == 'hadith-bank-discovery-v1'
            and payload.get('schema') == descriptor.get('schema')
            and payload.get('record_count') == snapshot['record_count']
            and payload.get('records_sha256') == snapshot['records_sha256']
            and isinstance(payload.get('rows'), list) and len(payload['rows']) == snapshot['record_count'],
            'Core payload belongs to a different source snapshot')
    ids, seen = hashlib.sha256(), set()
    for ordinal, row in enumerate(payload['rows']):
        key = identity(row)
        require(integer(row.get('ordinal')) and row['ordinal'] == ordinal and key not in seen,
                'Duplicate or misordered full discovery identity')
        seen.add(key)
        ids.update((row['id'] + '\n').encode('utf-8'))
    require(ids.hexdigest() == payload.get('occurrence_ids_sha256'), 'Ordered discovery ID fingerprint differs')
    require(hash_value(payload.get('indexed_quotation_fields_sha256')), 'Missing quotation-field fingerprint')
    selected = select_representatives(payload['rows'])
    summary = {'schema': payload['schema'], 'record_count': len(payload['rows']),
               'records_sha256': payload['records_sha256'], 'compressed_bytes': len(raw),
               'compressed_sha256': digest(raw), 'uncompressed_bytes': len(plain),
               'uncompressed_sha256': digest(plain), 'ordered_occurrence_ids_sha256': ids.hexdigest(),
               'ordered_ids_recomputed': True, 'full_five_field_identities_unique': True,
               'indexed_quotation_fields_sha256_declared': payload['indexed_quotation_fields_sha256'],
               'schema_decoder': 'scripts/bank_discovery.py:expand_discovery_payload',
               'schema_decoder_file_sha256': digest((scripts / 'bank_discovery.py').read_bytes())}
    return summary, selected


class SelectedRecords:
    def __init__(self, http, manifest, detail_bytes):
        self.http, self.manifest, self.detail_bytes = http, manifest, detail_bytes
        self.cache, self.cache_bytes = OrderedDict(), 0

    def part(self, descriptor, kind):
        path = descriptor['path']
        if path in self.cache:
            self.cache.move_to_end(path)
            return self.cache[path]
        raw, entry = self.http.fetch(self.http.local_url(path), kind, MAX_PART,
                                     descriptor['bytes'], descriptor['sha256'])
        plain = decode_gzip(raw, descriptor['uncompressed_bytes'], MAX_PART)
        require(plain.count(b'\n') == descriptor['count'], 'Shard newline count differs from its descriptor')
        entry.update(uncompressed_bytes=len(plain), uncompressed_sha256=digest(plain),
                     gzip_integrity_and_declared_size_verified=True)
        while self.cache and self.cache_bytes + len(plain) > MAX_CACHE:
            _, old = self.cache.popitem(last=False)
            self.cache_bytes -= len(old)
        self.cache[path] = plain
        self.cache_bytes += len(plain)
        return plain

    def record(self, selected):
        ordinal = selected['ordinal']
        matches = [p for p in self.manifest['directory']['shards']
                   if p['first_ordinal'] <= ordinal <= p['last_ordinal']]
        require(len(matches) == 1, 'Representative has no unique directory part')
        descriptor = matches[0]
        raw = self.part(descriptor, 'selected_directory')
        require(raw.endswith(b'\n'), 'Directory JSONL lacks its final newline')
        lines = raw.split(b'\n')[:-1]
        require(len(lines) == descriptor['count'] and all(lines), 'Directory row count/lines differ')
        seen, offset, chosen = set(), None, None
        for local, line in enumerate(lines):
            row = strict_json(line)
            key = identity(row)
            require(key not in seen, 'Duplicate full identity inside a directory part')
            seen.add(key)
            data = row.get('_reader')
            require(isinstance(data, dict), 'Directory metadata is absent')
            span = data.get('detail')
            require(isinstance(span, list) and len(span) == 2 and integer(span[0])
                    and integer(span[1], 2, MAX_RECORD) and span[0] + span[1] <= self.detail_bytes,
                    'Invalid bounded detail span')
            if offset is None:
                offset = span[0]
                require(descriptor['first_ordinal'] != 0 or offset == 0, 'First detail span does not start at zero')
            require(span[0] == offset, 'Directory spans are not contiguous within their verified part')
            offset += span[1]
            if descriptor['first_ordinal'] + local == ordinal:
                chosen = row
        require(chosen is not None and identity(chosen) == identity(selected['identity']),
                'Directory identity differs from the selected full discovery identity')
        if descriptor['last_ordinal'] == self.manifest['record_count'] - 1:
            require(offset == self.detail_bytes, 'Last directory part does not cover the detail stream end')
        start, length = chosen['_reader']['detail']
        size = self.manifest['details']['plain_part_bytes']
        first, last = start // size, (start + length - 1) // size
        require(last - first + 1 <= 4, 'Representative would require too many detail chunks')
        output, paths = bytearray(), []
        for index in range(first, last + 1):
            part = self.manifest['details']['shards'][index]
            plain = self.part(part, 'selected_complete_detail')
            a, b = max(start - index * size, 0), min(start + length - index * size, len(plain))
            require(0 <= a < b <= len(plain), 'Invalid detail-chunk intersection')
            output.extend(plain[a:b])
            paths.append(part['path'])
        raw_record = bytes(output)
        require(len(raw_record) == length and raw_record.endswith(b'\n') and raw_record.count(b'\n') == 1,
                'Reconstructed span is not exactly one complete JSONL record')
        record = strict_json(raw_record[:-1])
        require(identity(record) == identity(selected['identity']), 'Complete record belongs to a different source identity')
        fingerprints = {}
        for field in ('text_arabic', 'text_translation'):
            value = record.get(field)
            if isinstance(value, str):
                fingerprints[field] = {'codepoints': len(value), 'utf8_bytes': len(value.encode('utf-8')),
                                       'sha256': digest(value.encode('utf-8'))}
        source_hash = (record.get('source') or {}).get('sha256')
        return {**selected, 'directory_part': descriptor['path'], 'declared_detail_span': [start, length],
                'detail_parts': paths, 'exact_span_sha256': digest(raw_record),
                'complete_record_canonical_json_sha256': object_digest(record),
                'complete_five_field_identity_matches': True, 'exact_complete_record_reconstructed': True,
                'source_file_sha256_declared': source_hash if hash_value(source_hash) else None,
                'canonical_record_sha256_declared': (record.get('canonical_record_sha256')
                    if hash_value(record.get('canonical_record_sha256')) else None),
                'primary_text_fingerprints': fingerprints}


def verify(args, report, opener=None):
    http = HTTPReader(args.base_url, report, args.timeout, time.monotonic() + args.overall_timeout, opener)
    report['current_step'] = 'expected_live_html'
    html, html_http = http.fetch(args.base_url, 'expected_html', MAX_HTML, expected_hash=args.expected_html_sha256)
    parser = EmbeddedJSON()
    parser.feed(html.decode('utf-8', errors='strict'))
    parser.close()
    snapshot, manifest = parser.result()
    require(isinstance(snapshot, dict) and integer(snapshot.get('record_count'), 1, MAX_ROWS)
            and hash_value(snapshot.get('records_sha256'))
            and (snapshot.get('site') or {}).get('build_commit') == args.expected_source_commit,
            'Live HTML source commit/count/hash differs from the expected publication')
    prefix, detail_bytes, part_count = validate_manifest(manifest, snapshot, http)
    report['snapshot'] = {'build_commit': args.expected_source_commit, 'record_count': snapshot['record_count'],
                          'records_sha256': snapshot['records_sha256'], 'detail_stream_sha256': manifest['jsonl_sha256'],
                          'detail_stream_bytes_declared': detail_bytes, 'lazy_parts_declared': part_count,
                          'embedded_manifest_object_sha256': object_digest(manifest)}
    report['current_step'] = 'live_build_info_and_disk_manifest'
    build_raw, _ = http.fetch(http.local_url('build-info.json'), 'build_info', MAX_METADATA)
    info = strict_json(build_raw)
    require(isinstance(info, dict) and info.get('schema') == 'hadith-bank-site-build-v1'
            and info.get('status') == 'passed' and info.get('source_commit') == args.expected_source_commit
            and info.get('source_ref') == args.expected_source_commit
            and info.get('record_count') == snapshot['record_count']
            and info.get('search_sha256') == snapshot['records_sha256']
            and info.get('reader_sha256') == args.expected_html_sha256
            and info.get('reader_bytes') == len(html) and info.get('reader_self_contained') is False,
            'Live build-info does not agree with the expected HTML/source snapshot')
    hosted = info.get('hosted_reader') or {}
    descriptor = snapshot.get('discovery')
    require(hosted.get('html_bytes') == len(html) and hosted.get('embedded_encoding') == manifest['encoding']
            and hosted.get('self_contained') is False and hosted.get('shard_count') == part_count
            and hosted.get('discovery_artifact') == descriptor,
            'Hosted reader metadata or discovery descriptor differs from the HTML')
    disk_raw, _ = http.fetch(http.local_url(prefix + '/manifest.json'), 'disk_lazy_manifest', MAX_METADATA)
    require(strict_json(disk_raw) == manifest, 'Live disk manifest differs from the exact embedded manifest')
    report['build_info'] = {'status': info['status'], 'source_commit': info['source_commit'],
                            'record_count': info['record_count'], 'reader_sha256': info['reader_sha256'],
                            'source_binding_agrees': True, 'disk_and_embedded_manifest_equal': True}
    report['current_step'] = 'live_core_index_and_ordered_ids'
    url = check_core_part(descriptor, snapshot, http)
    core_raw, _ = http.fetch(url, 'core_discovery_index', MAX_CORE, descriptor['bytes'], descriptor['sha256'])
    report['discovery'], selected = verify_core(core_raw, descriptor, snapshot, args.repo_root)
    del core_raw
    sampler = SelectedRecords(http, manifest, detail_bytes)
    for selected_record in selected:
        report['current_step'] = selected_record['label']
        report['representatives'].append(sampler.record(selected_record))
    report['current_step'] = 'final_html_stability_check'
    final, _ = http.fetch(args.base_url, 'final_html_stability', MAX_HTML, len(html), args.expected_html_sha256)
    require(final == html, 'Publication changed during representative sampling')
    report['html_stable_through_sampling'] = True
    report['network'] = {'requests': http.requests, 'response_body_bytes': http.bytes,
                         'scope': 'Raw HTTP response body bytes; not browser CDP transport measurements.'}
    report['current_step'] = 'complete'
    report['status'] = 'passed'


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--expected-source-commit', required=True)
    parser.add_argument('--expected-html-sha256', '--expected-reader-sha256', required=True, dest='expected_html_sha256')
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--timeout', type=float, default=20.0, help='Per HTTP response timeout, at most 30 seconds.')
    parser.add_argument('--overall-timeout', type=float, default=180.0, help='Overall deadline, at most 300 seconds.')
    args = parser.parse_args(argv)
    args.expected_source_commit = args.expected_source_commit.lower()
    args.expected_html_sha256 = args.expected_html_sha256.lower()
    if re.fullmatch(r'[0-9a-f]{40}', args.expected_source_commit) is None or not hash_value(args.expected_html_sha256):
        parser.error('Expected source commit and HTML SHA-256 must be exact hexadecimal digests')
    if not 0 < args.timeout <= 30 or not args.timeout <= args.overall_timeout <= 300:
        parser.error('Use 0 < timeout <= 30 and timeout <= overall-timeout <= 300')
    if args.report.suffix != '.json' or args.report.resolve() == Path(__file__).resolve():
        parser.error('Report must name a separate JSON file')
    args.repo_root = args.repo_root.resolve()
    return args


def main(argv=None):
    args = arguments(argv)
    report = {'schema': 'hadith-bank-independent-published-bytes-v1', 'status': 'running',
              'started_at_utc': now(), 'expected': {'url': args.base_url,
                'source_commit': args.expected_source_commit, 'html_sha256': args.expected_html_sha256},
              'limits': {'requests': MAX_REQUESTS, 'total_response_body_bytes': MAX_NETWORK,
                         'core_compressed_bytes': MAX_CORE, 'core_decoded_bytes': MAX_CORE_PLAIN,
                         'part_compressed_and_decoded_bytes': MAX_PART, 'record_bytes': MAX_RECORD,
                         'per_request_seconds': args.timeout, 'overall_seconds': args.overall_timeout},
              'http': [], 'representatives': [],
              'scope': ['Read-only HTTPS GETs; same-origin local paths; redirects rejected; default TLS certificate validation.',
                        'Expected HTML/build binding, core index integrity and ordered IDs, plus three complete source records.',
                        'Full source text is neither saved nor printed; record and text-field fingerprints are metadata only.'],
              'limitations': ['Not a full source audit: entire directory/detail streams and every index part are not downloaded or rehashed.',
                              'The indexed quotation-field fingerprint and original source-file hashes are declared bindings, not independently recomputed corpus-wide here.',
                              'Sampled record object digests describe retrieved complete objects; no independent local canonical baseline is supplied for these objects.',
                              'No browser behavior, external source URL, translation, authenticity or human accessibility review is performed.',
                              'The compact-row schema decoder is the existing pure expand_discovery_payload function; HTTP, hashes and source-span reconstruction are independent.']}
    previous_handler = None
    if hasattr(signal, 'setitimer') and hasattr(signal, 'SIGALRM'):
        previous_handler = signal.getsignal(signal.SIGALRM)
        def deadline(_signum, _frame):
            raise TimeoutError('Overall verification deadline exceeded')
        signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, args.overall_timeout)
    try:
        verify(args, report)
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = type(error).__name__ + ': ' + str(error)[:800]
    finally:
        if previous_handler is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
        report['finished_at_utc'] = now()
        report.setdefault('network', {'requests': len(report['http']),
                                      'response_body_bytes': sum(item.get('bytes', 0) for item in report['http'])})
        args.report.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        require(len(encoded.encode('utf-8')) <= 256 * 1024, 'Evidence report exceeded its metadata-only size bound')
        args.report.write_text(encoded, encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(args.report.resolve()),
                      'requests': report['network']['requests'], 'records_verified': len(report['representatives']),
                      'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
