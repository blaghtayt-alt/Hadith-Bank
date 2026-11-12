#!/usr/bin/env python3
"""Register local structured records for public reading with review facts intact.

Invoking this command authorizes public inclusion of the chosen files. It does
not assert independent QC or a reuse license. JSON source bytes are not changed.
"""
import argparse
import copy
import datetime
import json
from pathlib import Path

from build_bank_views import digest_file, write_json
from build_reader import local, parse_json
from language_versions import validate_language_versions
from material_registry import COMPONENT, LANGUAGE, DECISION, PUBLICATION_DECISIONS, read_rows


def register(root, directory, language, book, edition, name, records, source,
             source_url=None, identifier=None, source_id=None, replace=False):
    root = Path(root).resolve()
    directory = local(root, str(directory))
    relative_directory = directory.relative_to(root).as_posix()
    if len(directory.relative_to(root).parts) != 2 or directory.relative_to(root).parts[0] != 'materials':
        raise ValueError('--directory must be materials/<slug>')
    if not COMPONENT.fullmatch(directory.name) or not LANGUAGE.fullmatch(language) or not COMPONENT.fullmatch(book) or not COMPONENT.fullmatch(edition):
        raise ValueError('Invalid material/language/book/edition key')
    if not directory.is_dir():
        raise ValueError('Create the material directory and copy the files into it first')
    target = local(root, relative_directory + '/manifest.json')
    if target.exists() and not replace:
        raise ValueError('Manifest already exists; use --replace after intentionally updating these source bytes')
    previous = parse_json(target.read_text(encoding='utf-8')) if target.exists() else {}
    if previous and (previous.get('schema') != 'hadith-bank-material-v1' or previous.get('adapter') != 'records-v1'):
        raise ValueError('--replace only updates a records-v1 material manifest')
    # CLI file names are relative to this material folder, never the working directory.
    record_file = local(directory, str(records))
    source_file = local(directory, str(source))
    if not source_file.is_file():
        raise ValueError('Missing local original source file')
    rows = read_rows(record_file)
    ids = set()
    for row in rows:
        if 'language_versions' in row:
            validate_language_versions(row['language_versions'])
        value = row.get('id')
        if not isinstance(value, str) or not value.strip() or value in ids:
            raise ValueError('Every occurrence needs a distinct stable id')
        ids.add(value)
        text = row.get('text')
        if not isinstance(text, dict) or not {'arabic', 'translation'} <= set(text) or any(text[k] is not None and not isinstance(text[k], str) for k in ('arabic', 'translation')):
            raise ValueError('Each record needs text.arabic and text.translation as a string or null')
    item_id = identifier or previous.get('id') or directory.name
    if not COMPONENT.fullmatch(item_id):
        raise ValueError('Invalid material id')
    manifest = copy.deepcopy(previous)
    manifest.update({'schema': 'hadith-bank-material-v1', 'id': item_id, 'adapter': 'records-v1',
                     'language': language, 'book': book, 'edition': edition,
                     'source_id': source_id or previous.get('source_id') or item_id})
    manifest.setdefault('records', {}).update({'path': record_file.relative_to(root).as_posix(),
                                               'sha256': digest_file(record_file), 'count': len(rows)})
    descriptor = manifest.setdefault('source', {})
    descriptor.update({'path': source_file.relative_to(root).as_posix(), 'sha256': digest_file(source_file),
                       'name': name, 'format': source_file.suffix.lstrip('.') or 'unknown'})
    descriptor['url'] = source_url if source_url is not None else descriptor.get('url')
    if 'publication' not in manifest:
        japan = datetime.timezone(datetime.timedelta(hours=9))
        manifest['publication'] = {'authorized': True, 'decision': DECISION,
                                   'decision_date_japan': datetime.datetime.now(japan).date().isoformat()}
    elif manifest['publication'].get('authorized') is not True or manifest['publication'].get('decision') not in PUBLICATION_DECISIONS:
        raise ValueError('Existing publication decision is unsupported; it has not been overwritten')
    write_json(target, manifest)
    return {'manifest': target.relative_to(root).as_posix(), 'records': len(rows),
            'source_text_modified': False, 'publication_authorized': True, 'independent_qc_asserted': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--directory', required=True)
    parser.add_argument('--language', required=True)
    parser.add_argument('--book', required=True)
    parser.add_argument('--edition', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--records', default='records.json')
    parser.add_argument('--source', required=True)
    parser.add_argument('--source-url')
    parser.add_argument('--id', dest='identifier')
    parser.add_argument('--source-id')
    parser.add_argument('--replace', action='store_true')
    args = vars(parser.parse_args(argv))
    try:
        result = register(**args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Material registration failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    main()
