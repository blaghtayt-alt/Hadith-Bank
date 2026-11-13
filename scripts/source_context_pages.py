"""Validate and stage explicitly registered source-only context pages."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil


def load_context_pages(root):
    root = Path(root).resolve()
    manifest = root / 'source-context' / 'manifest.json'
    if not manifest.exists():
        if (root / 'source-context' / 'bn-riyadh-cp017').exists():
            raise ValueError('Bengali source context is present without its manifest')
        return []
    if manifest.is_symlink() or manifest.parent.is_symlink():
        raise ValueError('Source context manifest must not use symlinks')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('schema') != 'hadith-bank-source-context-v1' or not isinstance(data.get('pages'), list):
        raise ValueError('Invalid source context manifest')
    pages, ids, paths = [], set(), set()
    for entry in data['pages']:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', entry['id']) or entry['id'] in ids or not isinstance(entry.get('title'), str) or not entry['title'].strip() or not isinstance(entry.get('files'), list):
            raise ValueError('Invalid source context page')
        ids.add(entry['id'])
        validated = []
        for item in entry['files']:
            relative = item.get('path') if isinstance(item, dict) else None
            digest = item.get('sha256') if isinstance(item, dict) else None
            size = item.get('bytes') if isinstance(item, dict) else None
            if not isinstance(relative, str) or not re.fullmatch(r'source-context/[A-Za-z0-9._/-]+', relative) or any(p in ('', '.', '..') for p in relative.split('/')) or relative in paths or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest) or type(size) is not int or size < 0:
                raise ValueError('Invalid source context file')
            target = root.joinpath(*PurePosixPath(relative).parts)
            if any(parent.is_symlink() for parent in (target, *target.parents) if parent != root and parent.is_relative_to(root)) or not target.is_file() or target.stat().st_size != size:
                raise ValueError('Missing or unsafe source context file: ' + relative)
            h = hashlib.sha256()
            with target.open('rb') as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    h.update(block)
            if h.hexdigest() != digest:
                raise ValueError('Source context checksum mismatch: ' + relative)
            paths.add(relative)
            validated.append({'path': relative, 'sha256': digest, 'bytes': size})
        if entry.get('html') not in {item['path'] for item in validated} or not entry['html'].endswith('.html'):
            raise ValueError('Source context page HTML is not registered')
        bengali_paths = [item['path'] for item in validated if item['path'].startswith('source-context/bn-riyadh-cp017/')]
        if entry['id'] == 'bn-riyadh-cp017' or bengali_paths:
            if entry['id'] != 'bn-riyadh-cp017' or entry['html'] != 'source-context/bn-riyadh-cp017/reader.html':
                raise ValueError('Bengali source context must retain its registered identity and path')
            from validate_bn_source_context import verify
            verify(root, entry)
        pages.append({'id': entry['id'], 'title': entry['title'], 'html': entry['html'], 'files': validated})
    if (root / 'source-context' / 'bn-riyadh-cp017').exists() and 'bn-riyadh-cp017' not in ids:
        raise ValueError('Bengali source context is present but omitted from its manifest')
    return pages


def stage_context_assets(root, staging, pages):
    root, staging = Path(root).resolve(), Path(staging).resolve()
    for page in pages:
        for item in page['files']:
            source = root.joinpath(*PurePosixPath(item['path']).parts)
            target = staging.joinpath(*PurePosixPath(item['path']).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            h = hashlib.sha256()
            with target.open('rb') as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    h.update(block)
            if target.stat().st_size != item['bytes'] or h.hexdigest() != item['sha256']:
                raise ValueError('Source context staged checksum mismatch: ' + item['path'])
