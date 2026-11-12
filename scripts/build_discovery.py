#!/usr/bin/env python3
"""Generate source-preserving, crawlable pages from the verified public stream.

The interactive/offline reader remains separate. These views add stable document
URLs, ordinary links and sitemaps; they do not translate, merge, or certify text.
Only records in the checked search stream become public narration pages.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
import math
from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import quote, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

from build_reader import (
    LANGUAGE_NAMES, component, load_records, local, number_label, page_label,
    record_type_info, safe_url, script_json, site_metadata, source_downloads,
    source_download_url, text, citation_parts,
)
from counterpart_display import (
    counterpart_alignment_notes, counterpart_citation, counterpart_qualification,
    counterpart_source_data, counterpart_translation_origin,
)
from current_provenance import classification
from book_titles import book_label as collection_label
from review_display_policy import review_badges, text_direction
from language_display import language_readings, reading_direction


PAGE_SIZE = 100
SITEMAP_PAGE_SIZE = 40000
# GitHub Pages' published-site limit is 1 GB. Leave room for deployment metadata.
MAX_SITE_BYTES = 950_000_000
NATIVE_LANGUAGE_NAMES = {
    'ar': 'العربية', 'bn': 'বাংলা', 'en': 'English', 'fa': 'فارسی',
    'fa-IR': 'فارسی', 'fil': 'Filipino / Tagalog', 'hi': 'हिन्दी',
    'ja': '日本語', 'pt': 'Português', 'pt-BR': 'Português', 'ur': 'اردو',
    'uz': 'O‘zbekcha', 'vi': 'Tiếng Việt', 'zh': '中文', 'zh-CN': '简体中文',
}
LANGUAGE_HEADINGS = {
    'fa': 'احادیث فارسی', 'fa-IR': 'احادیث فارسی', 'fil': 'Hadith sa Filipino',
    'hi': 'हिन्दी हदीस', 'ja': '日本語のハディース', 'uz': 'O‘zbekcha hadislar',
    'vi': 'Hadith tiếng Việt', 'zh': '中文圣训', 'zh-CN': '中文圣训',
    'ar': 'الأحاديث العربية', 'en': 'Hadith in English',
}
BOOK_NAMES = {
    'bukhari': 'Sahih al-Bukhari', 'muslim': 'Sahih Muslim',
    'abu-dawud': 'Sunan Abi Dawud', 'tirmidhi': 'Jami al-Tirmidhi',
    'ibn-majah': 'Sunan Ibn Majah', 'nasai': 'Sunan al-Nasai',
    'ahmad': 'Musnad Ahmad', 'malik': 'Muwatta of Imam Malik',
    'riyad-as-salihin': 'Riyad al-Salihin', 'riyadh-al-salihin': 'Riyad al-Salihin',
    'hisn-al-muslim': 'Hisn al-Muslim', 'adab-al-mufrad': 'Al-Adab al-Mufrad',
    'targhib-wa-tarhib': 'Al-Targhib wa al-Tarhib',
    'mishkat-al-masabih': 'Mishkat al-Masabih', 'hadeethenc': 'HadeethEnc',
    '200-golden-hadith': '200 Golden Hadith',
    'hakim': 'Reports attributed to al-Hakim',
    'tabarani': 'Reports attributed to al-Tabarani',
    'ibn-hibban': 'Reports attributed to Ibn Hibban',
    'unclassified': 'Collection not identified in the source',
}
STYLE = '''
.language-reading{padding:0;overflow:hidden}.language-reading>summary{padding:1rem 1.2rem;background:#f1f5ed}.language-reading>summary span{font-size:.8rem;color:var(--muted);font-weight:400;margin-inline-start:.7rem}.reading-content{padding:0 1.2rem 1rem}.language-reading .quotation{border:0;padding:0;background:transparent}.reading-source{border-top:1px solid var(--line);padding-top:.7rem;font-size:.9rem}.reading-notes{background:#f8f8f2}.reading-citation{font-size:.92rem;overflow-wrap:anywhere}
:root{color-scheme:light;--ink:#173e35;--paper:#faf8ef;--line:#d9e2d9;--muted:#52665c}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:18px/1.7 system-ui,sans-serif}
a{color:#075e4b;text-decoration-thickness:.07em;text-underline-offset:.18em;overflow-wrap:anywhere}a:hover{color:#8a6114}
header,main,footer{max-width:960px;margin:auto;padding:1.1rem 1.4rem}header{border-bottom:1px solid var(--line)}
nav{display:flex;gap:1rem;flex-wrap:wrap;font-size:.92rem}.brand{font-weight:750;font-size:1.2rem}
h1{font-size:clamp(1.65rem,4vw,2.35rem);line-height:1.3;overflow-wrap:anywhere}h2{font-size:1.3rem;margin-top:2rem}
h3{font-size:1.08rem}.muted,footer{color:var(--muted);font-size:.92rem}.text{white-space:pre-wrap;overflow-wrap:anywhere}
.quotation{font-size:1.13rem;margin:1.4rem 0;padding:1.2rem;border-inline-start:4px solid #bd9345;background:#fffef9}
.arabic{font-size:1.3rem}.panel,details{border:1px solid var(--line);border-radius:12px;padding:1rem;margin:1rem 0;background:#fffef9}
summary{cursor:pointer;font-weight:650}dl{display:grid;grid-template-columns:10rem minmax(0,1fr);gap:.4rem 1rem}dt{font-weight:650}dd{margin:0;overflow-wrap:anywhere}
ul.records{padding:0;list-style:none}ul.records>li{padding:.85rem 0;border-bottom:1px solid var(--line)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem;list-style:none;padding:0}.cards>li{padding:1rem;background:#fffef9;border:1px solid var(--line);border-radius:12px}
.badge{display:inline-block;font-size:.82rem;border:1px solid #b7cdbd;border-radius:20px;padding:.1rem .7rem;margin:.1rem .2rem .1rem 0}
.notice{padding:1rem;border-inline-start:3px solid #bd9345}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.82rem}code{font-size:.85em;overflow-wrap:anywhere}
.pagination{margin:1rem 0;display:flex;gap:.65rem;flex-wrap:wrap}.pagination a,.pagination strong{padding:.15rem .45rem}
footer{border-top:1px solid var(--line);margin-top:2rem}.skip{position:absolute;left:-10000px}.skip:focus{left:1rem;top:1rem;background:white}
@media(max-width:600px){body{font-size:17px}header,main,footer{padding:1rem}dl{grid-template-columns:1fr;gap:.2rem}dd{margin-bottom:.6rem}}
'''.strip() + '\n'


def esc(value):
    return html.escape(text(value), quote=True)


def language_name(code):
    english = LANGUAGE_NAMES.get(code, code)
    native = NATIVE_LANGUAGE_NAMES.get(code)
    return native + ' — ' + english if native and native != english else english


def language_heading(code):
    return LANGUAGE_HEADINGS.get(code, language_name(code) + ' hadiths')


def book_name(key, language=''):
    # Retain qualified wording for attribution groups in static pages.
    return collection_label(key, language, english=BOOK_NAMES.get(key))


# Public display helpers shared by repository indexes and reader navigation.
language_label = language_name
book_label = book_name


def title_markup(label):
    """Keep native/English title portions isolated inside left-to-right UI."""
    return '<bdi dir="ltr">' + ' — '.join('<bdi>' + esc(part) + '</bdi>'
                                         for part in label.split(' — ')) + '</bdi>'


def record_path(record):
    """Stable occurrence URL, independent of order, pagination and numbering."""
    parts = [component(record[field]) for field in ('language', 'book_key', 'edition')]
    identity = record.get('id')
    if not isinstance(identity, str) or not identity:
        raise ValueError('A discovery page requires a stable string occurrence ID')
    token = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]
    return '/'.join(['hadith', *parts, token + '.html'])


def uses_shared_web_reader(record):
    return bool(record.get('language_versions')) and str(record.get('source_id') or '').startswith(
        ('deenhindi-', 'rivoyat-', 'islom-', 'hadisuz-', 'fawaz-'))


def occurrence_link(record, current):
    if uses_shared_web_reader(record):
        return relative_link(current, 'index.html') + '?occurrence=' + quote(record['id'], safe='')
    return relative_link(current, record_path(record))


def public_path(relative):
    return relative[:-len('index.html')] if relative.endswith('index.html') else relative


def canonical_url(relative, site):
    live = urlsplit(site['live_url'])
    base = urlunsplit((live.scheme, live.netloc, quote(live.path.rstrip('/') + '/', safe='/%'), '', ''))
    return base + quote(public_path(relative), safe='/')


def relative_link(current, target):
    """Use ordinary relative links while canonicals use the public Pages URL."""
    public = public_path(target)
    path = posixpath.relpath(public or '.', posixpath.dirname(current) or '.')
    if (not public or public.endswith('/')) and not path.endswith('/'):
        path += '/'
    return path


def repository_file(root, relative, site):
    if not isinstance(relative, str) or not relative:
        return None
    # Validate path syntax and traversal without requiring a full local checkout.
    # Source paths are supplied by the already verified public catalog/records;
    # CI has the complete tree, while a sparse development checkout may omit them.
    local(root, relative)
    return (site['repository_url'] + '/blob/' + quote(site['source_ref'], safe='') + '/' +
            '/'.join(quote(part, safe='') for part in relative.split('/')))


def compact(value, limit=160):
    value = ' '.join(text(value).split())
    return value if len(value) <= limit else value[:limit - 1].rstrip() + '…'


def literal(value, language, css='text'):
    # No normalization: extraction anomalies, line breaks and source text stay literal.
    return ('<div class="' + css + '" lang="' + esc(language) + '" dir="' +
            text_direction(language) + '">' + esc(value) + '</div>')


def detail(title, content):
    return '<details><summary>' + esc(title) + '</summary>' + content + '</details>'


def reading_translator(reading):
    """Return only this reading's explicitly named translator, never its parent's."""
    if reading['language'].split('-')[0] == 'ar':
        return None
    source = reading.get('source') or {}
    supplied = source.get('translator')
    provenance = reading.get('translation_provenance') or {}
    credited = provenance.get('translator') if isinstance(provenance, dict) else None
    candidates = [supplied.get('name') if isinstance(supplied, dict) else None,
                  credited.get('name') if isinstance(credited, dict) else credited]
    unnamed = {'unknown', 'not named', 'not supplied', 'unspecified', 'n/a'}
    return next((value.strip() for value in candidates if isinstance(value, str)
                 and value.strip() and value.strip().lower() not in unnamed), None)


def render_language_reading(reading):
    """Each reading retains its own quotation, references and source notes."""
    language = reading['language']
    source = reading.get('source') or {}
    url = safe_url(source.get('record_url')) or safe_url(source.get('url'))
    credit = source.get('name') or 'Source not named'
    opened = reading.get('primary') or language.split('-')[0] in ('ar', 'en')
    body = ['<details class="language-reading"' + (' open' if opened else '') +
            '><summary>' + esc(reading.get('heading') or language) + '<span>' +
            esc(language) + '</span></summary><div class="reading-content">']
    if reading.get('qualification'):
        body.append('<p class="notice">' + esc(reading['qualification']) + '</p>')
    if reading.get('text'):
        body.append('<div class="text quotation" lang="' + esc(language) + '" dir="' +
                    reading_direction(reading) + '">' + esc(reading['text']) + '</div>')
    if reading.get('citation'):
        body.append('<p class="reading-citation" dir="auto">' + esc(reading['citation']) + '</p>')
    body.append('<p class="reading-source">' + ('<a href="' + esc(url) +
                '" target="_blank" rel="noopener noreferrer">' + esc(credit) + '</a>' if url else esc(credit)))
    translator = reading_translator(reading)
    if translator:
        body.append('<span class="reading-translator"> · Translator: ' + esc(translator) + '</span>')
    if language.split('-')[0] != 'ar' and reading.get('translation_origin'):
        body.append(' · Translation origin: ' +
                    {'human': 'Human', 'ai': 'AI', 'unknown': 'Unknown'}[reading['translation_origin']])
    body.append('</p>')
    if source.get('detail_metadata_status') == 'detail_metadata_pending':
        body.append('<p class="notice reading-pending">Detailed source references and notes have not been retrieved yet.</p>')
    references = reading.get('references') or []
    reference_parts = []
    for reference in references:
        reference_parts.extend(citation_parts(reference))
        own_url = (safe_url(reference.get('url')) or safe_url(reference.get('source_url'))
                   if isinstance(reference, dict) else None)
        if own_url and own_url != url:
            reference_parts.append('<p><a href="' + esc(own_url) +
                                   '" target="_blank" rel="noopener noreferrer">Reference at source</a></p>')
    if references:
        body.append(detail('References for this language (' + str(len(references)) + ')', ''.join(reference_parts)))
    upstream = []
    for item in source.get('upstream_sources') or []:
        if isinstance(item, dict):
            own_url = safe_url(item.get('url'))
            label = item.get('name') or 'Upstream source'
            upstream.append('<p>' + ('<a href="' + esc(own_url) + '" target="_blank" rel="noopener noreferrer">' +
                            esc(label) + '</a>' if own_url else esc(label)) +
                            (' · ' + esc(item['scope']) if item.get('scope') else '') + '</p>')
    if upstream:
        body.append(detail('Upstream credits supplied by this source', ''.join(upstream)))
    comments = []
    for comment in reading.get('comments') or []:
        value = comment.get('text') if isinstance(comment, dict) else comment
        if value:
            comments.append('<div class="text" dir="' + reading_direction(reading) + '">' + esc(value) + '</div>')
        own_url = safe_url(comment.get('source_url')) if isinstance(comment, dict) else None
        if own_url:
            comments.append('<p><a href="' + esc(own_url) + '" target="_blank" rel="noopener noreferrer">Comment source</a></p>')
    if comments:
        body.append('<details class="reading-notes"><summary>Notes and comments · ' +
                    str(len(reading['comments'])) + '</summary>' + ''.join(comments) + '</details>')
    body.append('</div></details>')
    return ''.join(body)


def data_details(title, value):
    if not value:
        return ''
    return detail(title, '<pre dir="auto">' + esc(json.dumps(value, ensure_ascii=False, indent=2)) + '</pre>')


def download_links(items, site):
    if not items:
        return ''
    return '<ul>' + ''.join(
        '<li><a href="' + esc(source_download_url(item['path'], site)) + '">' +
        esc(item['label']) + '</a> — ' + esc(item['source_name']) + '</li>'
        for item in sorted(items, key=lambda item: item['path'])) + '</ul>'


class Writer:
    def __init__(self, root, output, site):
        self.root, self.output, self.site = root, output, site
        self.pages = []
        self.bytes = 0
        self.files = 0

    def write(self, relative, content):
        path = local(self.output, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = content.encode('utf-8') if isinstance(content, str) else content
        path.write_bytes(raw)
        self.bytes += len(raw)
        self.files += 1

    def page(self, relative, title, description, body, language='en', schema=None, indexable=True):
        canonical = canonical_url(relative, self.site)
        # A 404 document is served at arbitrary paths, so its assets/navigation
        # must not resolve relative to the missing requested address.
        href = lambda target: esc(relative_link(relative, target) if indexable else canonical_url(target, self.site))
        graph = {'@context': 'https://schema.org', '@type': 'CollectionPage',
                 'name': title, 'description': description, 'url': canonical,
                 'inLanguage': language}
        if schema:
            graph.update(schema)
        robots = '' if indexable else '<meta name="robots" content="noindex,follow">\n'
        content = ('<!doctype html>\n<html lang="' + esc(language) + '">\n<head>\n'
                   '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                   '<title>' + esc(title) + '</title>\n<meta name="description" content="' + esc(description) + '">\n'
                   '<link rel="canonical" href="' + esc(canonical) + '">\n' + robots +
                   '<meta property="og:type" content="website">\n<meta property="og:title" content="' + esc(title) + '">\n'
                   '<meta property="og:description" content="' + esc(description) + '">\n'
                   '<meta property="og:url" content="' + esc(canonical) + '">\n'
                   '<link rel="stylesheet" href="' + href('assets/discovery.css') + '">\n'
                   '<script type="application/ld+json">' + script_json(graph) + '</script>\n'
                   '</head>\n<body><a class="skip" href="#content">Skip to text</a>\n'
                   '<header><a class="brand" href="' + href('browse/index.html') + '">Hadith Bank</a>'
                   '<nav aria-label="Main navigation"><a href="' + href('hadith-bank-reader.html') + '">Search all texts</a>'
                   '<a href="' + href('browse/index.html') + '">Languages and books</a>'
                   '<a href="' + esc(self.site['repository_url']) + '">GitHub repository</a></nav></header>\n'
                   '<main id="content">' + body + '</main>\n'
                   '<footer><p>Hadith Bank preserves source occurrences, translations, editions and attribution. '
                   'Availability is not independent certification of transcription, translation or authenticity.</p>'
                   '<nav aria-label="Source navigation"><a href="' + esc(self.site['repository_url']) + '">Repository and original files</a>'
                   '<a href="' + esc(self.site['repository_url'] + '/blob/main/catalog/materials.json') + '">Source data catalog</a>'
                   '<a href="' + href('sitemap.xml') + '">Sitemap</a></nav></footer></body></html>\n')
        self.write(relative, content)
        if indexable:
            self.pages.append(relative)


def source_title(record):
    return text((record.get('source') or {}).get('name')) or book_name(record['book_key'], record['language'])


def record_title(record):
    source = compact(source_title(record), 110)
    collection = book_name(record['book_key'], record['language'])
    identity = record_path(record).rsplit('/', 1)[-1][:10]
    parts = [source, collection if collection.casefold() not in source.casefold() else '', compact(number_label(record), 85),
             language_name(record['language']), identity, 'Hadith Bank']
    return ' | '.join(part for part in parts if part)


def record_description(record):
    primary = record.get('text_translation') or record.get('text_arabic')
    return compact(primary, 145) or (book_name(record['book_key'], record['language']) + ' source occurrence. ' + number_label(record))


def record_downloads(record, downloads, sources):
    original = (record.get('source') or {}).get('original_file')
    paths = [original, sources.get(record['source_id'])]
    return [downloads[path] for path in dict.fromkeys(paths) if path in downloads]


def render_record(writer, record, downloads, sources):
    path = record_path(record)
    language, book, edition = (record[key] for key in ('language', 'book_key', 'edition'))
    edition_path = 'browse/' + '/'.join((language, book, edition)) + '/index.html'
    source = record['source']
    kind = record_type_info(record) or {'label': 'Source occurrence', 'note': 'A separately preserved source occurrence.'}
    origin = {'human': 'Human', 'ai': 'AI', 'unknown': 'Unknown'}[classification(record)]
    link = lambda target: esc(relative_link(path, target))
    body = ['<nav aria-label="Breadcrumbs"><a href="' + link('browse/' + language + '/index.html') + '">' +
            esc(language_name(language)) + '</a><a href="' + link('browse/' + language + '/' + book + '/index.html') + '">' +
            title_markup(book_name(book, language)) + '</a><a href="' + link(edition_path) + '">Source edition</a></nav>',
            '<h1>' + title_markup(book_name(book, language)) + ' — ' + esc(number_label(record)) + '</h1>']
    if record.get('title'):
        body.append(literal(record['title'], language))
    body.append('<p><span class="badge">' + esc(kind['label']) + '</span>'
                '<span class="badge">' + esc(language_name(language)) + '</span>'
                '<span class="badge">Translation: ' + origin + '</span></p>')
    if kind['label'] != 'Hadith':
        body.append('<p class="muted">' + esc(kind['note']) + '</p>')
    if origin == 'AI':
        body.append('<p class="notice">This translation is identified as AI-generated in the source metadata.</p>')
    elif origin == 'Unknown':
        body.append('<p class="muted">Translation origin is unknown; no human or AI origin is asserted.</p>')
    if (record.get('display_policy') or {}).get('qc_tags') is not False:
        body.extend('<p class="notice">' + esc(badge['label']) + '</p>' for badge in review_badges(record))
    readings = language_readings(record)
    if readings:
        body.extend(render_language_reading(reading) for reading in readings)
    else:
        body.append('<p>Text is not supplied in this source projection; the source locator is preserved below.</p>')
    if counterpart_alignment_notes(record):
        body.append(detail('Alignment notes', ''.join('<p>' + esc(note) + '</p>' for note in counterpart_alignment_notes(record))))
    source_url = safe_url(source.get('record_url')) or safe_url(source.get('url'))
    source_display = '<a href="' + esc(source_url) + '">' + esc(source_title(record)) + '</a>' if source_url else esc(source_title(record))
    metadata = [('Source book or publication', source_display), ('Collection', title_markup(book_name(book, language))),
                ('Source numbering', esc(number_label(record))), ('Source edition', esc(edition)),
                ('Source location', esc(page_label(record))),
                ('Translator', esc((record.get('translator') or {}).get('name') or 'Not named in the supplied source')),
                ('Translation origin', origin)]
    if record.get('source_headings'):
        metadata.append(('Source headings', esc(record['source_headings'])))
    if (record.get('narrator') or {}).get('name'):
        metadata.append(('Narrator', esc(record['narrator']['name'])))
    body.append('<section class="panel"><h2>Source and translation</h2><dl>' + ''.join(
        '<dt>' + esc(name) + '</dt><dd dir="auto">' + value + '</dd>' for name, value in metadata) + '</dl>' +
        download_links(record_downloads(record, downloads, sources), writer.site) + '</section>')
    commentary = record.get('commentary') or {}
    notes = []
    for field, code in (('translation', language), ('arabic', 'ar')):
        if commentary.get(field):
            notes.append(literal(commentary[field], code))
    if record.get('footnotes'):
        notes.append('<pre dir="auto">' + esc(json.dumps(record['footnotes'], ensure_ascii=False, indent=2)) + '</pre>')
    if notes:
        body.append(detail('Commentary and footnotes supplied by the source', ''.join(notes)))
    for label, key in (('Source numbering details', 'number'),
                       ('Source references', 'references'), ('Source grading', 'grading'),
                       ('Benefits supplied by the source', 'benefits'), ('Narrator and chain', 'narrator'),
                       ('Source translation-origin history', 'translation_provenance')):
        body.append(data_details(label, record.get(key)))
    locator = source.get('record_locator') or {}
    original_links = []
    for label, relative in (('Canonical source record', locator.get('path')),
                            ('Preserved original file', source.get('original_file'))):
        url = repository_file(writer.root, relative, writer.site)
        if url:
            original_links.append('<p><a href="' + esc(url) + '">' + label + '</a></p>')
    original_links.append('<p>Occurrence ID: <code>' + esc(record['id']) + '</code></p>')
    original_links.append('<pre dir="auto">' + esc(json.dumps({'record_locator': locator,
        'original_sha256': source.get('sha256'), 'source_notes': (record.get('review') or {}).get('issues', [])},
        ensure_ascii=False, indent=2)) + '</pre>')
    body.append(detail('Source locators and source notes', ''.join(original_links)))
    canonical = canonical_url(path, writer.site)
    work = {'@type': 'CreativeWork', '@id': canonical + '#occurrence', 'url': canonical,
            'name': source_title(record) + ' — ' + number_label(record), 'inLanguage': language,
            'identifier': {'@type': 'PropertyValue', 'propertyID': 'Hadith Bank occurrence ID', 'value': record['id']},
            'isPartOf': {'@type': 'CreativeWork', 'name': source_title(record), 'url': canonical_url(edition_path, writer.site)}}
    if source_url:
        work['citation'] = source_url
    writer.page(path, record_title(record), record_description(record), ''.join(body), language,
                {'@type': 'WebPage', 'mainEntity': work})


def occurrence_list(records, current):
    lines = ['<ul class="records">']
    for record in records:
        kind = record_type_info(record)
        label = compact(record.get('title'), 110) or compact(record.get('text_translation') or record.get('text_arabic'), 110)
        if not label:
            label = (kind or {}).get('label', 'Source occurrence')
        lines.append('<li><a href="' + esc(occurrence_link(record, current)) + '" dir="auto">' +
                     esc(label) + '</a><br><span class="muted">' + esc(number_label(record)) +
                     (' · ' + esc(kind['label']) if kind else '') + '</span></li>')
    return ''.join(lines) + '</ul>'


def pagination(directory, current, pages, selected):
    links = []
    for page in range(1, pages + 1):
        target = directory + ('index.html' if page == 1 else 'page-' + str(page) + '.html')
        links.append('<strong aria-current="page">' + str(page) + '</strong>' if page == selected else
                     '<a href="' + esc(relative_link(current, target)) + '">' + str(page) + '</a>')
    return '<nav class="pagination" aria-label="Edition pages">' + ''.join(links) + '</nav>' if pages > 1 else ''


def render_indexes(writer, records, downloads, sources):
    groups, languages = defaultdict(list), defaultdict(Counter)
    for record in records:
        key = tuple(record[field] for field in ('language', 'book_key', 'edition'))
        groups[key].append(record)
        languages[key[0]][key[1]] += 1
    books = defaultdict(list)
    for (language, book, edition), items in sorted(groups.items()):
        # Preserve the edition order in the verified source stream. Stable
        # occurrence URLs do not require sorting source-local numbering.
        books[(language, book)].append((edition, items))
        directory = 'browse/' + '/'.join((language, book, edition)) + '/'
        editions = sorted(set(source_title(record) for record in items))
        page_count = max(1, math.ceil(len(items) / PAGE_SIZE))
        group_downloads = {item['path']: item for record in items for item in record_downloads(record, downloads, sources)}
        for page_number in range(1, page_count + 1):
            current = directory + ('index.html' if page_number == 1 else 'page-' + str(page_number) + '.html')
            heading = book_name(book, language) + ' — ' + language_name(language)
            native_title = compact(editions[0], 110)
            collection = book_name(book, language)
            title = (native_title + (' | ' + collection if collection.casefold() not in native_title.casefold() else '') +
                     ' | ' + language_name(language) + ' | ' + edition + ' | Page ' + str(page_number) + ' | Hadith Bank')
            body = '<nav aria-label="Breadcrumbs"><a href="' + esc(relative_link(current, 'browse/' + language + '/index.html')) + '">' + esc(language_name(language)) + '</a>'
            body += '<a href="' + esc(relative_link(current, 'browse/' + language + '/' + book + '/index.html')) + '">' + title_markup(book_name(book, language)) + '</a></nav>'
            body += '<h1>' + title_markup(heading) + '</h1><p>' + esc(' · '.join(editions)) + '</p>'
            body += '<p class="muted">' + str(len(items)) + ' source occurrences in this edition. Source numbering, excerpts and variants are retained. '
            body += 'This count does not assert that the entire original collection is present.</p>'
            body += download_links(list(group_downloads.values()), writer.site)
            body += pagination(directory, current, page_count, page_number)
            body += occurrence_list(items[(page_number - 1) * PAGE_SIZE:page_number * PAGE_SIZE], current)
            body += pagination(directory, current, page_count, page_number)
            writer.page(current, title, compact(' · '.join(editions) + '. ' + str(len(items)) +
                        ' source occurrences with individual texts, references and available original-book downloads.'), body, language)
    for (language, book), entries in sorted(books.items()):
        current = 'browse/' + language + '/' + book + '/index.html'
        count = sum(len(items) for _, items in entries)
        heading = book_name(book, language) + ' — ' + language_heading(language)
        body = '<p><a href="' + esc(relative_link(current, 'browse/' + language + '/index.html')) + '">' + esc(language_name(language)) + '</a></p><h1>' + title_markup(heading) + '</h1>'
        body += '<p>' + str(count) + ' source occurrences across ' + str(len(entries)) + ' editions or source snapshots. '
        body += 'Some sources contain excerpts or quotations; availability does not mean the complete book is present.</p><ul class="cards">'
        for edition, items in entries:
            title = ' · '.join(sorted(set(source_title(record) for record in items)))
            target = 'browse/' + language + '/' + book + '/' + edition + '/index.html'
            group_downloads = {item['path']: item for record in items for item in record_downloads(record, downloads, sources)}
            body += '<li><a href="' + esc(relative_link(current, target)) + '" dir="auto">' + esc(title) + '</a><br>'
            body += '<span class="muted">' + esc(edition) + ' · ' + str(len(items)) + ' source occurrences</span>'
            body += download_links(list(group_downloads.values()), writer.site) + '</li>'
        body += '</ul>'
        writer.page(current, heading + ' | Hadith Bank', compact(book_name(book, language) + ' in ' + language_name(language) +
                    ': source editions, individual narrations, exact references and original books where available.'), body, language)
    for language, book_counts in sorted(languages.items()):
        current = 'browse/' + language + '/index.html'
        heading = language_heading(language) + ' — ' + LANGUAGE_NAMES.get(language, language)
        body = '<p><a href="' + esc(relative_link(current, 'browse/index.html')) + '">All languages</a></p><h1>' + title_markup(heading) + '</h1>'
        body += ('<p>' + str(sum(book_counts.values())) + ' source occurrences in ' + str(len(book_counts)) +
                 ' collection groups. Choose a book, source edition and individual text.</p><ul class="cards">')
        for book, count in sorted(book_counts.items()):
            target = 'browse/' + language + '/' + book + '/index.html'
            body += '<li><a href="' + esc(relative_link(current, target)) + '">' + title_markup(book_name(book, language)) + '</a><br>' + str(count) + ' source occurrences</li>'
        body += '</ul>'
        writer.page(current, heading + ' | Hadith Bank', compact(language_heading(language) + '. ' +
                    str(sum(book_counts.values())) + ' source occurrences, book editions and available Word/PDF downloads.'), body, language)
    current = 'browse/index.html'
    body = '<h1>Hadith Bank — languages and books</h1><p>Read individual hadiths and source quotations with their book, numbering, translation origin and original material.</p>'
    body += '<p>' + str(len(records)) + ' source occurrences in ' + str(len(languages)) + ' languages. '
    body += 'Repeated source occurrences, excerpts, Companion reports and edition variants remain distinct.</p><ul class="cards">'
    for language, book_counts in sorted(languages.items()):
        body += '<li><a href="' + esc(relative_link(current, 'browse/' + language + '/index.html')) + '" lang="' + esc(language) + '">' + esc(language_heading(language)) + '</a><br>'
        body += esc(language_name(language)) + ' · ' + str(sum(book_counts.values())) + ' source occurrences</li>'
    body += '</ul><h2>Find a book</h2><p>Each language lists only source collections present in the verified bank. Original PDF, DOC and DOCX downloads are linked on their book and narration pages when preserved.</p>'
    writer.page(current, 'Hadith Bank | Multilingual hadith texts, books and source downloads',
                'Browse actual hadith texts by language, book and source edition. Find individual narrations, references and preserved PDF or Word books.', body)
    return {'languages': {language: sum(counts.values()) for language, counts in sorted(languages.items())},
            'language_count': len(languages), 'book_language_count': len(books), 'edition_count': len(groups)}


def write_sitemaps(writer, pages, page_size=SITEMAP_PAGE_SIZE):
    if type(page_size) is not int or not 1 <= page_size <= 50000:
        raise ValueError('Sitemap page size must be between 1 and 50000')
    urls = sorted({canonical_url(path, writer.site) for path in ['index.html', *pages]})
    sitemap_paths = []
    for offset in range(0, len(urls), page_size):
        document = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for url in urls[offset:offset + page_size]:
            ET.SubElement(ET.SubElement(document, 'url'), 'loc').text = url
        # Keep sitemap files at the project root: their normal directory scope
        # then covers both browse/ and hadith/ without Search Console exceptions.
        path = 'sitemap-' + str(len(sitemap_paths) + 1).zfill(4) + '.xml'
        raw = ET.tostring(document, encoding='utf-8', xml_declaration=True) + b'\n'
        if len(raw) > 50_000_000:
            raise ValueError('Sitemap exceeds the 50 MB uncompressed limit')
        writer.write(path, raw)
        sitemap_paths.append(path)
    document = ET.Element('sitemapindex', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in sitemap_paths:
        ET.SubElement(ET.SubElement(document, 'sitemap'), 'loc').text = canonical_url(path, writer.site)
    writer.write('sitemap.xml', ET.tostring(document, encoding='utf-8', xml_declaration=True) + b'\n')
    return {'sitemap_count': len(sitemap_paths), 'sitemap_url_count': len(urls), 'sitemap': canonical_url('sitemap.xml', writer.site)}


def build(root, output, site=None, records=None, catalog=None):
    """Build into a fresh staged site. Optional inputs must come from load_records.

    The caller can reuse the already verified records/catalog from a reader build.
    Supplying just one is rejected. Existing discovery trees are never removed:
    refresh_bank stages a fresh directory and atomically replaces the old site.
    """
    root = Path(root).resolve()
    output = Path(output).absolute()
    if output == root or root.is_relative_to(output) or any(path.is_symlink() for path in [output, *output.parents]):
        raise ValueError('Unsafe discovery output directory')
    if (records is None) != (catalog is None):
        raise ValueError('Provide both verified records and catalog or neither')
    if records is None:
        records, catalog, _ = load_records(root)
    settings = site_metadata(catalog, site)
    output.mkdir(parents=True, exist_ok=True)
    for name in ('browse', 'hadith', 'sitemaps'):
        if (output / name).exists():
            raise ValueError('Discovery output must be a fresh staged site: ' + name)
    seen_ids, seen_paths = set(), set()
    for record in records:
        path = record_path(record)
        if record['id'] in seen_ids or path in seen_paths:
            raise ValueError('Duplicate occurrence ID or discovery URL collision: ' + record['id'])
        seen_ids.add(record['id'])
        seen_paths.add(path)
    downloads = {item['path']: item for item in source_downloads(root, records, catalog)}
    sources = {item['dataset_id']: item.get('source_file') for item in catalog.get('materials', [])}
    writer = Writer(root, output, settings)
    writer.write('assets/discovery.css', STYLE)
    index_info = render_indexes(writer, records, downloads, sources)
    static_record_count = 0
    for record in sorted(records, key=lambda item: (item['language'], item['book_key'], item['edition'], item['id'])):
        if not uses_shared_web_reader(record):
            render_record(writer, record, downloads, sources)
            static_record_count += 1
    writer.page('404.html', 'Page not found | Hadith Bank', 'Find a language, book or source text in Hadith Bank.',
                '<h1>Page not found</h1><p>This address is not part of the published bank. '
                '<a href="' + esc(canonical_url('browse/index.html', settings)) + '">Browse languages and books</a> '
                'or use the search reader.</p>', indexable=False)
    sitemap_info = write_sitemaps(writer, writer.pages)
    site_bytes = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
    report = {'schema': 'hadith-bank-discovery-v1', 'record_pages': static_record_count,
              'shared_reader_occurrences': len(records) - static_record_count,
              'index_pages': len(writer.pages) - static_record_count, 'indexable_pages': len(writer.pages),
              'generated_files': writer.files + 1, 'generated_bytes': writer.bytes,
              'site_bytes': site_bytes, 'source_records_sha256': catalog['search']['records_sha256'],
              'source_texts_unchanged': True, 'independent_qc_performed': False,
              **index_info, **sitemap_info}
    # Include the report itself in byte/file totals. The integer-length fixed
    # point converges after its decimal digit lengths stop changing.
    for _ in range(8):
        report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        report_bytes = len(report_text.encode('utf-8'))
        totals = writer.bytes + report_bytes, site_bytes + report_bytes
        if totals == (report['generated_bytes'], report['site_bytes']):
            break
        report['generated_bytes'], report['site_bytes'] = totals
    else:
        raise ValueError('Could not finalize discovery size report')
    if report['site_bytes'] >= MAX_SITE_BYTES:
        raise ValueError('Published site exceeds the conservative 950 MB GitHub Pages size budget: ' + str(report['site_bytes']))
    writer.write('discovery-info.json', report_text)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True, help='Fresh website staging directory')
    args = parser.parse_args(argv)
    try:
        result = build(args.root, args.output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, 'Discovery build failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
