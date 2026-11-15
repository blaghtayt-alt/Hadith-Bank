#!/usr/bin/env python3
"""Check staged or live gzip XML sitemaps against published source-bound metadata.

This verifies the actual response bytes, not an HTML preview or a successful
GitHub commit. It never rewrites sitemaps, sources, review state or the site.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
CHILD = re.compile(r'sitemap-[0-9]{4,}\.xml\.gz\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
MAX_GZIP = 12 * 1024 * 1024
MAX_XML = 50_000_000


def require(ok, message):
    if not ok:
        raise ValueError('Sitemap verification: ' + message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_relative(base, location, *, child=False):
    value = urlsplit(location)
    origin = urlsplit(base)
    require(value.scheme == origin.scheme == 'https' and value.netloc == origin.netloc
            and not value.query and not value.fragment and location.startswith(base),
            'sitemap URL is outside its canonical HTTPS project root')
    relative = unquote(location[len(base):])
    parts = PurePosixPath(relative).parts
    require((bool(relative) or not child) and not relative.startswith('/')
            and all(part not in ('.', '..') for part in parts)
            and '\\' not in relative and '\x00' not in relative,
            'sitemap URL has unsafe path segments')
    if child:
        require(CHILD.fullmatch(relative) is not None,
                'child sitemap is not a supported compressed XML URL')
    return relative


def decode_gzip(data):
    require(data[:2] == b'\x1f\x8b' and len(data) <= MAX_GZIP,
            'child sitemap response is not bounded gzip')
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            plain = stream.read(MAX_XML + 1)
    except (OSError, EOFError) as error:
        raise ValueError('Sitemap verification: invalid gzip body') from error
    require(len(plain) <= MAX_XML, 'uncompressed child sitemap exceeds 50 MB')
    return plain


def verify(*, site_root=None, production_url=None, expected_source_commit=None,
           fetcher=None):
    require((site_root is None) != (production_url is None),
            'select exactly one local stage or public production site')
    root = Path(site_root).resolve() if site_root is not None else None
    if root is not None:
        require(root.is_dir() and not root.is_symlink(), 'missing staged website')
    else:
        production_url = production_url.rstrip('/') + '/'
        parsed = urlsplit(production_url)
        require(parsed.scheme == 'https' and parsed.hostname and not parsed.username
                and not parsed.password and not parsed.query and not parsed.fragment,
                'invalid public site URL')
    response_headers = {}

    def read(relative):
        require(relative and '\\' not in relative and all(part not in ('.', '..')
                for part in PurePosixPath(relative).parts), 'unsafe requested asset')
        if root is not None:
            target = root / relative
            require(target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(root),
                    'staged sitemap asset is missing or unsafe: ' + relative)
            return target.read_bytes()
        url = production_url + relative
        if fetcher is not None:
            result = fetcher(url)
            if isinstance(result, tuple):
                value, headers = result
                response_headers[relative] = headers
                return value
            return result
        request = Request(url, headers={
            'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache',
            'User-Agent': 'HadithBank-Sitemap-Verification/1.0'})
        try:
            with urlopen(request, timeout=45) as response:
                require(response.status == 200 and response.geturl() == url,
                        'published asset redirected or did not return 200: ' + relative)
                response_headers[relative] = {
                    'content_type': response.headers.get('Content-Type'),
                    'content_encoding': response.headers.get('Content-Encoding'),
                    'content_disposition': response.headers.get('Content-Disposition')}
                data = response.read(MAX_GZIP + 5_000_000)
                require(len(data) < MAX_GZIP + 5_000_000,
                        'published sitemap response is unexpectedly large')
                return data
        except OSError as error:
            raise ValueError('Sitemap verification: public asset unavailable: ' + relative) from error

    info = json.loads(read('build-info.json'))
    require(info.get('status') == 'passed', 'site build-info is not passed')
    if expected_source_commit:
        require(info.get('source_commit') == expected_source_commit,
                'public source revision differs from expected commit')
    discovery = info.get('discovery') or {}
    source = discovery.get('source_records_sha256')
    require(isinstance(source, str) and HEX64.fullmatch(source),
            'missing verified source-record stream SHA-256')
    sitemap_url = discovery.get('sitemap')
    require(isinstance(sitemap_url, str) and sitemap_url.endswith('/sitemap.xml'),
            'build does not report a canonical sitemap root')
    base = sitemap_url[:-len('sitemap.xml')]
    if root is None:
        require(production_url == base, 'live site root differs from source-bound build-info')

    index_raw = read('sitemap.xml')
    index = ET.fromstring(index_raw)
    require(index.tag == NS + 'sitemapindex', 'root sitemap is not an XML index')
    locations = [elem.text for elem in index.findall(NS + 'sitemap/' + NS + 'loc')]
    require(locations and all(isinstance(loc, str) for loc in locations),
            'empty or invalid sitemap index')
    children = [checked_relative(base, loc, child=True) for loc in locations]
    expected_count = discovery.get('sitemap_count')
    require(len(children) == expected_count and len(children) == len(set(children)),
            'sitemap shard count or uniqueness differs from build')
    expected_hashes = discovery.get('sitemap_original_xml_sha256') or []
    require(len(expected_hashes) == len(children) and all(
            isinstance(h, str) and HEX64.fullmatch(h) for h in expected_hashes),
            'source-bound uncompressed XML hashes are missing')

    urls, original_total, compressed_total = [], 0, 0
    for name, expected_hash in zip(children, expected_hashes):
        compressed = read(name)
        plain = decode_gzip(compressed)
        require(digest(plain) == expected_hash,
                'compressed sitemap does not reproduce build-verified XML: ' + name)
        root_xml = ET.fromstring(plain)
        require(root_xml.tag == NS + 'urlset', 'child sitemap is not XML urlset')
        values = [item.text for item in root_xml.findall(NS + 'url/' + NS + 'loc')]
        require(all(isinstance(url, str) for url in values) and len(values) <= 40000,
                'invalid child sitemap URL list')
        for url in values:
            checked_relative(base, url)
        urls.extend(values)
        compressed_total += len(compressed)
        original_total += len(plain)
    require(len(urls) == discovery.get('sitemap_url_count')
            and len(set(urls)) == len(urls) and urls == sorted(urls),
            'sitemap URL inventory is incomplete, duplicated or out of order')
    require(base in urls, 'site homepage is missing from canonical sitemap')
    require(original_total == discovery.get('sitemap_uncompressed_bytes')
            and compressed_total == discovery.get('sitemap_stored_bytes')
            and original_total - compressed_total == discovery.get('sitemap_lossless_bytes_saved'),
            'published compressed sitemap bytes disagree with source-bound manifest')

    if root is not None:
        for address in urls:
            relative = address[len(base):]
            filename = unquote(relative)
            file = root / (filename + 'index.html' if filename.endswith('/') or not filename else
                           filename if filename.endswith('.html') else filename + '/index.html')
            require(file.is_file() and file.resolve().is_relative_to(root),
                    'sitemap canonical URL does not resolve in staged site: ' + address)

    return {
        'schema': 'hadith-bank-sitemap-delivery-verification-v1',
        'status': 'passed',
        'mode': 'staged' if root is not None else 'live',
        'site_base': base,
        'source_commit': info.get('source_commit'),
        'source_records_sha256': source,
        'root_sitemap_sha256': digest(index_raw),
        'child_sitemaps': children,
        'child_xml_sha256': expected_hashes,
        'canonical_url_count': len(urls),
        'canonical_urls_sha256': digest(json.dumps(urls, ensure_ascii=False,
                                                  separators=(',', ':')).encode('utf-8')),
        'child_compressed_bytes': compressed_total,
        'child_uncompressed_bytes': original_total,
        'lossless_sitemap_bytes_saved': original_total - compressed_total,
        'http_response_headers': response_headers,
        'legacy_uncompressed_child_url_compatibility': 'not_published_see_docs',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--site-root', type=Path)
    group.add_argument('--production-url')
    parser.add_argument('--expected-source-commit')
    parser.add_argument('--report', type=Path, required=True)
    options = parser.parse_args()
    result = verify(site_root=options.site_root, production_url=options.production_url,
                    expected_source_commit=options.expected_source_commit)
    options.report.parent.mkdir(parents=True, exist_ok=True)
    options.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                              encoding='utf-8')
    print(json.dumps({key: result[key] for key in (
        'status', 'mode', 'source_commit', 'canonical_url_count',
        'child_compressed_bytes', 'lossless_sitemap_bytes_saved')}))


if __name__ == '__main__':
    main()
