#!/usr/bin/env python3
"""Generate the GitHub book directory from the accepted publication catalog."""
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from build_reader import (component, escaped, local, parse_json, site_metadata,
                          source_download_label, source_download_url, write)
from build_discovery import book_label, language_label


def write_catalog(root, catalog=None, site=None):
    root = Path(root).resolve()
    catalog = catalog if catalog is not None else parse_json(
        local(root, 'catalog/materials.json').read_text(encoding='utf-8'))
    settings = site_metadata(catalog, site)
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
             'This directory is generated from the published material catalog. It lists the collection, '
             'actual source-edition name, preserved occurrence count, reading pages and available original downloads. '
             'A collection may be represented by selected quotations, excerpts, one volume or several editions. '
             'An entry does not assert that the entire original book is present.', '',
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
            lines += ['### ' + escaped(book_label(book)), '',
                      '[Browse collection](' + base + 'browse/' + lang + '/' + book + '/)', '',
                      '| Source edition as recorded | Occurrences | Read | Original source |',
                      '| --- | ---: | --- | --- |']
            for material in sorted(grouped[(lang, book)], key=lambda item: (item['edition'], item['dataset_id'])):
                edition = component(material['edition'])
                descriptor = material.get('source_descriptor') or {}
                name = material.get('source_name') or descriptor.get('name') or material['dataset_id']
                name = escaped(name).replace('|', '&#124;').replace('\n', ' ')
                read_url = base + 'browse/' + lang + '/' + book + '/' + edition + '/'
                path = material.get('source_file') or descriptor.get('path')
                label = source_download_label(path)
                if label and local(root, path).is_file():
                    source = '[' + label + '](' + source_download_url(path, settings) + ')'
                elif path:
                    # Check path syntax before making a GitHub link. Canonical files
                    # can be absent from a sparse local checkout; GitHub retains them.
                    local(root, path)
                    url = (settings['repository_url'] + '/blob/' + quote(settings['source_ref'], safe='') + '/' +
                           '/'.join(quote(part, safe='') for part in path.split('/')))
                    source = '[Source data](' + url + ')'
                else:
                    source = 'See record provenance'
                lines.append('| ' + name + '<br><code>' + escaped(edition) + '</code> | ' +
                             format(material.get('count', 0), ',') + ' | [Read edition](' + read_url +
                             ') | ' + source + ' |')
    lines += ['', '## Source and indexing notes', '',
              'Word/PDF links are provided only for preserved files in those formats. No replacement '
              'translation or conversion is generated for this directory. Reuse conditions remain those '
              'recorded with each source.', '',
              '[Machine-readable catalog](materials.json) · [Search-engine discovery](../docs/SEARCH-ENGINE-DISCOVERY.md) · '
              '[Website sitemap](' + base + 'sitemap.xml)', '']
    write(root / 'catalog/BOOKS.md', '\n'.join(lines))
    return {'languages': len(languages), 'collection_language_pairs': len(grouped),
            'source_editions': sum(map(len, grouped.values()))}
