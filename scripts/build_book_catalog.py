#!/usr/bin/env python3
"""Generate the GitHub book directory from the accepted publication catalog."""
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from build_reader import (component, escaped, local, parse_json, site_metadata,
                          source_download_url, write)
from build_discovery import book_label, language_label


DOWNLOAD_COLUMNS = ('| Source edition as recorded | Occurrences | Read | Extracted text | '
                    'Original source (PDF) | Other source formats |')
DOWNLOAD_RULE = '| --- | ---: | --- | --- | --- | --- |'
DOWNLOAD_DESCRIPTION = (
    'This directory is generated from the published material catalog. It lists the collection, '
    'actual source-edition name, preserved occurrence count, reading pages and available downloads. '
    'Extracted text is separate from the preserved original source PDF and other supplied source formats. '
    'A collection may be represented by selected quotations, excerpts, one volume or several editions. '
    'An entry does not assert that the entire original book is present.')
DOWNLOAD_NOTES = (
    'Original source (PDF) links point to preserved source-input PDFs for the recorded edition or volume. '
    'Supplied Word sources retain their actual format under Other source formats; they are not relabeled '
    'as extracted text. Extracted text links identify separately preserved derivatives, with corrections '
    'and review limits retained in their linked notes. A generated PDF is never an original source PDF. '
    'Not linked does not mean that extraction never occurred. Original PDF unverified means that no '
    'exact original PDF is linked for that row; no alternative edition or converted file is substituted. '
    'No translation, conversion or source review is performed for this directory. Reuse conditions remain '
    'those recorded with each source.')


def repository_file_url(path, settings):
    return (settings['repository_url'] + '/blob/' + quote(settings['source_ref'], safe='') + '/' +
            '/'.join(quote(part, safe='') for part in path.split('/')))


def book_download_metadata(root):
    path = local(root, 'catalog/book-downloads.json')
    if not path.is_file():
        return {}
    data = parse_json(path.read_text(encoding='utf-8'))
    if data.get('schema') != 'hadith-bank-book-downloads-v1' or not isinstance(data.get('editions'), dict):
        raise ValueError('Invalid book-download display metadata')
    if any(not isinstance(entry, dict) or not entry for entry in data['editions'].values()):
        raise ValueError('Book-download entries must be nonempty objects')
    return data['editions']


def download_columns(root, material, settings, metadata):
    """Keep source inputs and explicitly evidenced derivative downloads separate."""
    descriptor = material.get('source_descriptor') or {}
    path = material.get('source_file') or descriptor.get('path')
    extracted = 'Not linked'
    original_pdf = 'Original PDF unverified'
    other = '—'
    if path:
        source = local(root, path)  # Validate even when the checkout is sparse.
        suffix = Path(path).suffix.lower()
        if suffix == '.pdf' and source.is_file():
            original_pdf = '[Original source (PDF)](' + source_download_url(path, settings) + ')'
        elif suffix in ('.doc', '.docx') and source.is_file():
            other = '[Supplied source (Word ' + suffix + ')](' + source_download_url(path, settings) + ')'
            original_pdf = 'Original PDF unverified — Word source supplied'
        else:
            other = '[Source data](' + repository_file_url(path, settings) + ')'
    else:
        other = 'See record provenance'

    entry = metadata.get(material['dataset_id'])
    if entry is not None:
        source_hash = material.get('source_sha256') or descriptor.get('sha256')
        if (entry.get('source_file') != path or not source_hash or
                entry.get('source_sha256') != source_hash):
            raise ValueError('Book-download source identity mismatch: ' + material['dataset_id'])
        supporting = {item['path']: item.get('sha256') for item in material.get('supporting_files', [])}

        def verified_support(item):
            target = item['path']
            checked = local(root, target)
            if (target == path or not item.get('sha256') or
                    supporting.get(target) != item['sha256'] or not checked.is_file()):
                raise ValueError('Unverified book-download supporting file: ' + target)
            return target

        links = []
        for item in entry.get('extracted_text', []):
            target = verified_support(item)
            suffix = Path(target).suffix.lower()
            if suffix not in ('.doc', '.docx', '.pdf'):
                raise ValueError('Unsupported extracted-text format: ' + target)
            label = 'Extracted text (PDF)' if suffix == '.pdf' else 'Extracted text (Word)'
            links.append('[' + label + '](' + source_download_url(target, settings) + ')')
        if not links:
            raise ValueError('Book-download metadata has no extracted text: ' + material['dataset_id'])
        notes = verified_support(entry['notes'])
        qualification = escaped(entry['qualification']).replace('|', '&#124;').replace('\n', ' ')
        extracted = (' · '.join(links) + '<br>' + qualification + ' — [preserved correction notes](' +
                     repository_file_url(notes, settings) + ')')
    return extracted, original_pdf, other


def write_catalog(root, catalog=None, site=None):
    root = Path(root).resolve()
    catalog = catalog if catalog is not None else parse_json(
        local(root, 'catalog/materials.json').read_text(encoding='utf-8'))
    settings = site_metadata(catalog, site)
    downloads = book_download_metadata(root)
    unknown = set(downloads) - {material['dataset_id'] for material in catalog.get('materials', [])}
    if unknown:
        raise ValueError('Unknown book-download dataset IDs: ' + ', '.join(sorted(unknown)))
    base = settings['live_url'].rstrip('/') + '/'
    grouped = defaultdict(list)
    for material in catalog.get('materials', []):
        if material.get('available_locally') is False or material.get('public_text_published') is False:
            continue
        key = tuple(component(material[field]) for field in ('language', 'book_key'))
        grouped[key].append(material)
    languages = sorted({language for language, _ in grouped})
    lines = ['# Hadith Bank — books and source editions', '',
             '[Read and search online](' + base + ') · [Browse book pages](' + base + 'browse/) · '
             '[Repository overview](../README.md)', '',
             DOWNLOAD_DESCRIPTION, '',
             'Counts describe source occurrences, including distinct variants and Companion reports; '
             'they are not counts of unique canonical hadiths. Source wording, numbering, translation origin '
             'and review qualifications remain attached to each record.', '',
             '## Languages', '']
    for language in languages:
        total = sum(item.get('count', 0) for (lang, _), items in grouped.items()
                    if lang == language for item in items)
        lines.append('- [' + escaped(language_label(language)) + '](' + base + 'browse/' + language +
                     '/) — ' + format(total, ',') + ' source occurrences')
    for language in languages:
        lines += ['', '## ' + escaped(language_label(language)), '',
                  '[All collections in this language](' + base + 'browse/' + language + '/)', '']
        for lang, book in sorted(grouped):
            if lang != language:
                continue
            lines += ['### ' + escaped(book_label(book, language)), '',
                      '[Browse collection](' + base + 'browse/' + lang + '/' + book + '/)', '',
                      DOWNLOAD_COLUMNS, DOWNLOAD_RULE]
            for material in sorted(grouped[(lang, book)], key=lambda item: (item['edition'], item['dataset_id'])):
                edition = component(material['edition'])
                descriptor = material.get('source_descriptor') or {}
                name = material.get('source_name') or descriptor.get('name') or material['dataset_id']
                name = escaped(name).replace('|', '&#124;').replace('\n', ' ')
                read_url = base + 'browse/' + lang + '/' + book + '/' + edition + '/'
                downloads_for_edition = download_columns(root, material, settings, downloads)
                lines.append('| ' + name + '<br><code>' + escaped(edition) + '</code> | ' +
                             format(material.get('count', 0), ',') + ' | [Read edition](' + read_url +
                             ') | ' + ' | '.join(downloads_for_edition) + ' |')
    lines += ['', '## Source and indexing notes', '',
              DOWNLOAD_NOTES, '',
              '[Machine-readable catalog](materials.json) · [Search-engine discovery](../docs/SEARCH-ENGINE-DISCOVERY.md) · '
              '[Website sitemap](' + base + 'sitemap.xml)', '']
    write(root / 'catalog/BOOKS.md', '\n'.join(lines))
    return {'languages': len(languages), 'collection_language_pairs': len(grouped),
            'source_editions': sum(map(len, grouped.values()))}
