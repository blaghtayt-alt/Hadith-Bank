#!/usr/bin/env python3
"""Package a completed, self-contained bank with hashes and ZIP CRC validation."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.is_relative_to(root):
        parser.error('Archive output must be outside the bank tree')
    catalog = json.loads((root / 'catalog/materials.json').read_text(encoding='utf-8'))
    audit_path = 'reports/portable-validation.json'
    audit = json.loads((root / audit_path).read_text(encoding='utf-8'))
    if (audit.get('status') != 'passed' or audit.get('scope') != catalog['scope'] or
            audit.get('record_count') != catalog['record_count'] or
            audit.get('source_dataset_count') != len(catalog['materials']) or
            audit.get('search_stream_sha256') != catalog['search']['records_sha256']):
        raise ValueError('Complete portable validation over the current full package before packaging')
    reader = audit['reader']
    if sha256(root / reader['path']) != reader['sha256']:
        raise ValueError('Reader changed since portable validation')
    for item in audit['source_files']:
        if sha256(root / item['path']) != item['sha256']:
            raise ValueError('Source file changed since portable validation: ' + item['path'])
    files = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in ('.git', '.cache', '__pycache__') for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError('Symlink not permitted in portable package: ' + relative.as_posix())
        if not path.is_file() or path.name.endswith('.pyc') or relative.as_posix() == 'PACKAGE-MANIFEST.json':
            continue
        files.append({'path': relative.as_posix(), 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    manifest = {
        'schema': 'hadith-bank-complete-package-manifest-v2',
        'scope': catalog['scope'], 'record_count': catalog['record_count'],
        'by_language': catalog['by_language'], 'source_dataset_count': len(catalog['materials']),
        'count_unit': catalog['count_unit'],
        'organization_audit': audit_path,
        'organization_audit_status': audit.get('status'),
        'historical_organization_audit': 'reports/organization-final-audit.json',
        'file_count_excluding_manifest': len(files), 'files': files,
        'manifest_self_hash_excluded': True,
    }
    manifest_path = root / 'PACKAGE-MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for item in files:
            archive.write(root / item['path'], root.name + '/' + item['path'])
        archive.write(manifest_path, root.name + '/PACKAGE-MANIFEST.json')
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError('ZIP CRC mismatch: ' + bad)
        archived_count = len(archive.infolist())
    print(json.dumps({'archive': str(output), 'bytes': output.stat().st_size,
                      'sha256': sha256(output), 'files': archived_count,
                      'zip_crc_validation': 'passed', 'record_count': catalog['record_count']}, indent=2))


if __name__ == '__main__':
    main()
