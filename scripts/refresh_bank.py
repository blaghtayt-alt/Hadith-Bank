#!/usr/bin/env python3
"""Rebuild and validate every registered source, then atomically stage the reader.

Run after adding materials/<slug>/manifest.json and its local records/source files.
Uses Python's standard library and the local Node search projector; never
extracts, translates, or certifies text.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from build_bank_views import build as build_views, write_json
from build_reader import (build as build_reader, load_records, site_metadata,
                          local, parse_json, _reader_manifest_parts)
from build_discovery import build as build_discovery
from build_book_catalog import write_catalog as write_book_catalog
from validate_bank_views import validate
from prepare_counterpart_review import prepare_review
from source_context_pages import load_context_pages, stage_context_assets


def git_revision(root):
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def reader_build_metrics(result):
    """Keep transport/row measurements while omitting local output paths."""
    fields = ('html_bytes', 'embedded_encoding', 'self_contained', 'shard_count',
              'shard_bytes', 'detail_shard_count', 'directory_bytes',
              'max_projection_row_bytes', 'max_detail_record_bytes',
              'reader_store_metrics', 'discovery_statistics', 'discovery_artifact')
    return {key: result[key] for key in fields if key in result}


def reusable_reader_parts(root, copied_reader, info, data_name, settings):
    """Bind the already source-validated reader to the exact staging inputs.

    This is a transport reuse gate, not a replacement for refresh's full public
    source validation. Canonical search JSONL and compact reader JSONL hashes
    are deliberately checked against their respective bindings.
    """
    def require(condition, message):
        if not condition:
            raise ValueError('Cannot reuse validated reader: ' + message)

    require(info.get('status') == 'passed' and info.get('reader_self_contained') is False,
            'missing completed validation or sharded-reader status')
    raw = copied_reader.read_bytes()
    require(type(info.get('reader_bytes')) is int and len(raw) == info['reader_bytes'] and
            hashlib.sha256(raw).hexdigest() == info.get('reader_sha256'),
            'HTML bytes differ from the validated reader')
    document = raw.decode('utf-8')
    snapshots = re.findall(r'<script\b[^>]*\bid="hadith-snapshot"[^>]*>(.*?)</script\s*>', document, re.S | re.I)
    records = re.findall(r'(<script\b[^>]*\bid="hadith-records"[^>]*>)(.*?)</script\s*>', document, re.S | re.I)
    require(len(snapshots) == 1 and len(records) == 1, 'ambiguous reader snapshot or manifest')
    snapshot, manifest = parse_json(snapshots[0]), parse_json(records[0][1])
    require(isinstance(snapshot, dict) and isinstance(manifest, dict), 'invalid snapshot or manifest')
    catalog = parse_json(local(root, 'catalog/materials.json').read_text(encoding='utf-8'))
    search = catalog.get('search') or {}
    count, source_hash = info.get('record_count'), info.get('search_sha256')
    require(type(count) is int and count >= 0 and isinstance(source_hash, str) and
            re.fullmatch(r'[0-9a-f]{64}', source_hash) and
            search.get('count') == count == snapshot.get('record_count') == manifest.get('record_count') and
            catalog.get('record_count', count) == count and
            search.get('records_sha256') == source_hash == snapshot.get('records_sha256'),
            'source snapshot hash or occurrence count differs')
    require(snapshot.get('site') == site_metadata(catalog, settings), 'source/site revision differs')
    delivery, transport = snapshot.get('data_delivery') or {}, info.get('reader_transport') or {}
    encoding = manifest.get('encoding')
    require(manifest.get('schema') == 'hadith-bank-reader-lazy-v2' and encoding == 'gzip-jsonl-lazy-v2' and
            re.search(r'\bdata-encoding="gzip-jsonl-lazy-v2"', records[0][0]) and
            delivery.get('self_contained') is False and delivery.get('encoding') == encoding and
            delivery.get('jsonl_sha256') == manifest.get('jsonl_sha256') and
            transport.get('self_contained') is False and transport.get('embedded_encoding') == encoding and
            transport.get('html_bytes') == len(raw), 'reader transport differs from validation inputs')
    disk_manifest = parse_json(local(root, data_name + '/manifest.json').read_text(encoding='utf-8'))
    require(disk_manifest == manifest, 'data manifest differs from embedded reader manifest')
    parts = _reader_manifest_parts(manifest)
    require(delivery.get('shard_count') == len(parts) == transport.get('shard_count') and
            transport.get('shard_bytes') == sum(part.get('bytes', -1) for part in parts),
            'shard transport measurements differ')
    discovery = snapshot.get('discovery')
    require(isinstance(discovery, dict) and discovery == transport.get('discovery_artifact') and
            discovery.get('record_count') == count and discovery.get('records_sha256') == source_hash and
            isinstance(discovery.get('parts'), list), 'discovery snapshot differs from validated transport')
    discovery_parts = [discovery, *discovery['parts']]
    for part in discovery_parts:
        require(isinstance(part, dict) and part.get('record_count') == count and
                part.get('records_sha256') == source_hash and
                isinstance(part.get('path'), str) and part['path'].startswith(data_name + '/discovery/'),
                'discovery path or source binding differs')
    parts += discovery_parts
    seen = set()
    for part in parts:
        relative = part.get('path')
        require(isinstance(relative, str) and relative.startswith(data_name + '/') and relative not in seen and
                type(part.get('bytes')) is int and part['bytes'] > 0 and
                isinstance(part.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', part['sha256']),
                'unsafe, duplicate or incomplete data descriptor')
        local(root, relative)
        seen.add(relative)
    return manifest, parts


def verify_reused_reader_copy(staging, data_name, manifest, parts):
    """Check copied transport bytes, including against changes during copying."""
    directory = staging / data_name
    for parent, directories, files in os.walk(directory, followlinks=False):
        if any((Path(parent) / name).is_symlink() for name in directories + files):
            raise ValueError('Cannot reuse validated reader: copied data contains a symlink')
    copied_manifest = parse_json(local(staging, data_name + '/manifest.json').read_text(encoding='utf-8'))
    if copied_manifest != manifest:
        raise ValueError('Cannot reuse validated reader: copied manifest changed')
    for part in parts:
        path = local(staging, part['path'])
        if not path.is_file() or path.stat().st_size != part['bytes']:
            raise ValueError('Cannot reuse validated reader: copied data size differs: ' + part['path'])
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != part['sha256']:
            raise ValueError('Cannot reuse validated reader: copied data SHA-256 differs: ' + part['path'])


def stage_site(root, output, info):
    output = Path(output)
    output = (root / output).absolute() if not output.is_absolute() else output.absolute()
    if (output == root or root.is_relative_to(output) or output.name in ('attachments', 'materials', 'sources', '.git') or
            output.is_symlink() or any(p.is_symlink() for p in output.parents)):
        raise ValueError('Unsafe site output directory')
    marker = '.hadith-bank-generated-site'
    if output.exists() and (not output.is_dir() or (any(output.iterdir()) and not (output / marker).is_file())):
        raise ValueError('Refusing to replace a non-generated site directory: ' + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.hadith-site-', dir=output.parent))
    backup = None
    try:
        shutil.copyfile(root / 'hadith-bank-reader.html', staging / 'hadith-bank-reader.html')
        settings = {'source_ref': info['source_ref'],
                    **({'build_commit': info['source_commit']} if info.get('source_commit') else {})}
        if info.get('reader_self_contained') is False:
            data_name = 'hadith-bank-reader-data'
            manifest, parts = reusable_reader_parts(root, staging / 'hadith-bank-reader.html',
                                                   info, data_name, settings)
            # Keep links as links until validation rejects them; never follow
            # an unexpected data-tree symlink into unrelated source files.
            shutil.copytree(local(root, data_name), staging / data_name, symlinks=True)
            verify_reused_reader_copy(staging, data_name, manifest, parts)
            shutil.copyfile(staging / 'hadith-bank-reader.html', staging / 'index.html')
            info['hosted_reader'] = dict(info['reader_transport'])
        else:
            settings['offline_reader_url'] = site_metadata({}, settings)['live_url'].rstrip('/') + '/hadith-bank-reader.html'
            data_name = 'reader-data'
            hosted = build_reader(root, staging / 'index.html', site=settings,
                                  data_directory=staging / data_name)
            info['hosted_reader'] = reader_build_metrics(hosted)
        stage_context_assets(root, staging, load_context_pages(root))
        discovery = build_discovery(root, staging, site={
            'source_ref': info['source_ref'],
            **({'build_commit': info['source_commit']} if info.get('source_commit') else {}),
        })
        info['discovery'] = discovery
        (staging / '.nojekyll').write_text('', encoding='utf-8')
        (staging / marker).write_text('Generated by scripts/refresh_bank.py\n', encoding='utf-8')
        write_json(staging / 'build-info.json', info)
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix='.hadith-site-previous-', dir=output.parent))
            backup.rmdir()
            os.replace(output, backup)
        try:
            os.replace(staging, output)
        except BaseException:
            if backup is not None:
                os.replace(backup, output)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
        return output
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def refresh(root, site_output='_site'):
    root = Path(root).resolve()
    # Invalid registrations fail before staging or deploying a replacement site.
    view_result = build_views(root, root)
    source_commit = os.environ.get('GITHUB_SHA') or git_revision(root)
    site = {'source_ref': os.environ.get('GITHUB_SHA') or 'main'}
    if source_commit:
        site['build_commit'] = source_commit
    reader_result = build_reader(root, root / 'hadith-bank-reader.html', root / 'browse', site=site,
                                 max_embedded_bytes=75_000_000)
    catalog = json.loads((root / 'catalog/materials.json').read_text(encoding='utf-8'))
    write_book_catalog(root, catalog, site)
    # Prepare generated navigation targets before checking README/book links.
    # Candidates stay outside the reader and cannot approve a language match.
    review_records, _, _ = load_records(root)
    review_queue = prepare_review(root, 'reports/counterpart-review', records=review_records)
    del review_records
    report_path = root / 'reports/portable-validation.json'
    report = validate(root, mode='public', report_path=report_path)
    write_json(report_path, report)
    info = {'schema': 'hadith-bank-site-build-v1', 'status': 'passed',
            'source_commit': source_commit, 'source_ref': site['source_ref'],
            'record_count': catalog['record_count'], 'by_language': catalog['by_language'],
            'source_dataset_count': len(catalog['materials']),
            'search_sha256': catalog['search']['records_sha256'],
            'reader_sha256': report['reader']['sha256'], 'reader_bytes': report['reader']['bytes'],
            'reader_self_contained': reader_result['self_contained'],
            'reader_transport': reader_build_metrics(reader_result),
            'canonical_source_bytes_unchanged': True, 'independent_qc_performed': False,
            'counterpart_review': {
                **{key: value for key, value in review_queue.items() if key not in ('output', 'manifest')},
                'manifest': 'reports/counterpart-review/manifest.json',
            },
            'registry': 'materials/*/manifest.json',
            'validation_report': 'reports/portable-validation.json'}
    staged = stage_site(root, site_output, info)
    write_json(root / 'reports/site-build.json', info)
    return {**info, 'site_output': str(staged), 'search_shards': view_result['shards'],
            'markdown_pages': reader_result.get('markdown_pages')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--site-output', type=Path, default=Path('_site'))
    args = parser.parse_args(argv)
    try:
        result = refresh(args.root, args.site_output)
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        parser.exit(1, 'Bank refresh failed; no replacement site was staged: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    main()

