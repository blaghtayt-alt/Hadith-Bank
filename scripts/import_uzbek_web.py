#!/usr/bin/env python3
"""Resume publisher-page imports from Rivoyat and hadis.islom.uz.

Only linked, robots-allowed public HTML is fetched. No private/API endpoint,
number-range probing, OCR, back-translation, or canonical-number inference is
used. Exact HTTP bytes are retained as content-addressed gzip snapshots.

Examples:
  python scripts/import_uzbek_web.py --site islom --max-pages 80
  python scripts/import_uzbek_web.py --site rivoyat --max-pages 120
  python scripts/import_uzbek_web.py --site all --export-only

The request budget is a resumable checkpoint, never a completeness claim.
Records lacking explicit source-bound Prophetic attribution remain staged,
outside registered reader materials. A lexical attribution check is not an
independent review or an authenticity judgement.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

from web_source_reviews import SourceReviews


BASE = 'imports/web-uzbek-20261112'
SCHEMA = 'hadith-bank-web-import-checkpoint-v1'
AGENT = 'HadithBankImporter/0.1 (+public-source-import; no-model-training)'
PUBLICATION_PART_BYTES = 40 * 1024 * 1024
SITES = {'rivoyat': 'https://rivoyat.com', 'islom': 'https://hadis.islom.uz'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
BLOCK = {'p', 'div', 'blockquote', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr'}
DIACRITICS = re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def excluded_by_owner(root, site):
    path = Path(root) / 'catalog/web-import-plan.json'
    if not path.exists():
        return False
    plan = json.loads(path.read_text(encoding='utf-8'))
    return bool(plan.get('sources', {}).get(site, {}).get('excluded_by_owner'))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(json_bytes(value))
    temp.replace(path)


def packed_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json_bytes(value), mtime=0))


class Node:
    def __init__(self, tag='root', attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def has(self, cls):
        return cls in (self.attrs.get('class') or '').split()

    def all(self, test=lambda node: True):
        for item in self.children:
            if isinstance(item, Node):
                if test(item):
                    yield item
                yield from item.all(test)

    def first(self, test):
        return next(self.all(test), None)

    def text(self, blocks=False):
        if self.tag in ('script', 'style'):
            return ''
        if self.tag == 'br':
            return '\n' if blocks else ''
        result = ''.join(item.text(blocks) if isinstance(item, Node) else item for item in self.children)
        return ('\n' + result + '\n') if blocks and self.tag in BLOCK else result


class Tree(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        # Source HTML sometimes omits a p closing tag. Apply the normal HTML
        # paragraph closure rather than nesting unrelated paragraphs.
        if tag == 'p' and self.stack[-1].tag == 'p':
            self.stack.pop()
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def plain(node, blocks=False):
    if node is None:
        return ''
    value = node.text(blocks)
    if blocks:
        return '\n'.join(line.strip() for line in value.splitlines() if line.strip()).strip()
    return value.strip()


def links(tree):
    return list(tree.all(lambda n: n.tag == 'a' and n.attrs.get('href')))


def script_texts(source):
    for match in re.finditer(r'self\.__next_f\.push\((.*?)\)</script>', source, re.S):
        try:
            value = json.loads(match.group(1))
            if len(value) > 1 and isinstance(value[1], str):
                yield value[1]
        except (ValueError, TypeError):
            continue


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def rivoyat_payloads(source):
    """Read the same public copy payload used by the rendered page buttons."""
    result = {}
    decoder = json.JSONDecoder()
    flight = ''.join(script_texts(source))
    for match in re.finditer(r'(?:^|\n)[0-9a-f]+:', flight):
        start = match.end()
        try:
            value, _ = decoder.raw_decode(flight[start:])
        except ValueError:
            continue
        for item in walk(value):
            if not isinstance(item, dict) or not isinstance(item.get('parts'), dict):
                continue
            part = item['parts']
            if not isinstance(part.get('url'), str):
                continue
            if not all(isinstance(part.get(k), str) for k in ('arabic', 'latin', 'cyrillic')):
                continue
            # Unresolved Flight references are not source text.
            if any(re.fullmatch(r'\$[A-Za-z0-9]+', part[k]) for k in ('arabic', 'latin', 'cyrillic')):
                continue
            result[part['url']] = part
    return result


def normalize_attribution(value):
    return DIACRITICS.sub('', value).replace('ـ', '').replace('ٱ', 'ا')


def classify(arabic, translation, collection=None):
    """Conservative source-marker triage, with every rejected item preserved."""
    ar = normalize_attribution(arabic or '')
    uz = translation or ''
    # Inclusive of sayings, actions, tacit approval, dhikr/duas and surrounding
    # narration context; this does not equate source attribution with sahih.
    for pattern in (r'رسول\s+الله', r'النبي\b', r'النبيّ', r'نبي\s+الله'):
        match = re.search(pattern, ar)
        if match:
            return 'prophetic_report', {'basis': 'Explicit Prophetic attribution in this source entry',
                                        'source_language': 'ar', 'matched_marker': match.group(0),
                                        'method': 'lexical_source_attribution_triage_v1',
                                        'independent_classification_review': 'not_performed'}
    match = re.search(r'(?i)(Rasululloh|Расулуллоҳ|Payg[ʻʼ‘’\u0027]?ambar|Пайғамбар|Nabiy\b|Набий\b)', uz)
    if match:
        return 'prophetic_report', {'basis': 'Explicit Prophetic attribution in this source entry',
                                    'source_language': 'uz', 'matched_marker': match.group(0),
                                    'method': 'lexical_source_attribution_triage_v1',
                                    'independent_classification_review': 'not_performed'}
    # These two publisher-declared anthologies contain deliberately abbreviated
    # matn without an isnad/"Prophet said" prefix. Their exact source title plus
    # an explicit narration citation can support SOURCE attribution. An uncited
    # proverb (e.g. the book's cradle-to-grave saying) remains unknown. This rule
    # is not used for Musannaf works that mix Prophetic and Companion reports.
    declaration = (collection or {}).get('bounded_matn_declaration')
    if declaration:
        citation = re.search(r'(?:رواه|أخرجه|اخرجه|متفق\s+عليه)[^\n]{1,350}', ar)
        prefix = ar.lstrip('\ufeff \n\t*0123456789.-–()')
        explicitly_non_prophetic = re.match(r'^(?:عن\s|قال\s+(?!الله\b)|كان\s+(?:ابن|أبو|ابو|عمر|علي|عثمان|عبد\s+الله))', prefix)
        if citation and citation.start() > 8 and not explicitly_non_prophetic:
            return 'prophetic_report', {
                'basis': 'Bounded matn in a publisher-declared Prophetic hadith anthology with an explicit narration-source citation. Source attribution is preserved separately from authenticity.',
                'source_language': 'ar', 'matched_marker': citation.group(0),
                'work_declaration': declaration,
                'method': 'source_declared_bounded_matn_and_citation_v1',
                'independent_classification_review': 'not_performed',
                'authenticity_assessed': False}
    return 'unknown', {'basis': 'No explicit Prophetic marker established by the conservative importer; may include Companion/successor sayings, Quran-only items or referential reports.',
                       'method': 'lexical_source_attribution_triage_v1',
                       'independent_classification_review': 'pending'}


COMMENT_MARKER = re.compile(r'^(?:Шарҳ\s*[:：.]|Изоҳ\s*[:：.]|Ҳадиснинг аҳамияти|Ҳадисдан олинадиган|Ҳадиснинг ворид|Фойдалар\s*[:：.]|Фойдалари\s*[:：.]|شرح\s*[:：]|الشرح\s*[:：])', re.I)


def split_islom_text(value):
    """Separate only explicit commentary headings; uncertain tails stay staged."""
    lines = value.splitlines()
    for i, line in enumerate(lines):
        if i > 0 and COMMENT_MARKER.search(line.strip()):
            return '\n'.join(lines[:i]), '\n'.join(lines[i:]), 'explicit_commentary_heading'
    return value, None, None


def source_ref(collection, number, citation, url, language):
    return {'collection': collection, 'number': number, 'source_citation': citation,
            'url': url, 'scope': 'source_entry', 'numbering_system': 'publisher_source_local',
            'source_language': language, 'canonical_mapping_status': 'unverified'}


def prose_references(value, url, language):
    """Keep explicit publisher citations without manufacturing canonical IDs."""
    out = []
    for line in (value or '').splitlines():
        line = line.strip()
        if language == 'ar':
            cite = re.search(r'(?:ر[َوُِّْ]*و[َاُِّْ]*اه|م[ُّ]*ت[َّ]*ف[َ]*ق|\[(?:خ|م)\s*\d)', line)
        else:
            cite = re.search(r'^(?:Имом .{1,100}ривоят|Муттафақун|Бухорий .{0,30}ривоят|Муслим .{0,30}ривоят)', line)
        if cite:
            out.append({'collection': None, 'number': None, 'source_citation': line,
                        'url': url, 'scope': 'source_supplied_citation',
                        'source_language': language, 'canonical_mapping_status': 'not_inferred'})
    return out


def rivoyat_language_text(node, language, source_titles=False):
    """Project publisher-labelled scripts without translating or mixing them.

    Arabic labels in grading/source metadata are supplied in HTML title
    attributes. They are used only for those labels, never as narration text.
    """
    if node is None:
        return ''

    def visit(item):
        if not isinstance(item, Node):
            if language == 'ar' and re.search(r'[A-Za-z\u0400-\u052f]', item):
                return ''
            return item
        if item.tag in ('script', 'style', 'svg'):
            return ''
        if item.has('lat'):
            return item.text() if language == 'uz-Latn' else ''
        if item.has('kir') or item.attrs.get('lang') == 'uz-Cyrl':
            return item.text() if language == 'uz-Cyrl' else ''
        if item.attrs.get('lang') == 'ar' or item.has('hk-ar'):
            return item.text() if language == 'ar' else ''
        title = item.attrs.get('title', '')
        if language == 'ar' and source_titles and re.search(r'[\u0600-\u06ff]', title):
            return title
        if item.tag == 'br':
            return '\n'
        text = ''.join(visit(child) for child in item.children)
        return '\n' + text + '\n' if item.tag in BLOCK else text

    return '\n'.join(line.strip() for line in visit(node).splitlines() if line.strip())


def rivoyat_detail_metadata(source, row, snapshot):
    """Read bounded detail metadata only after all supplied texts match.

    Cross-references are statements made by this publisher, not independently
    accepted identities or evidence for the translation's upstream publisher.
    Similar-hadith suggestions and site-wide credits are outside this parser.
    """
    url = row['source']['record_url']
    if snapshot.get('url') != url or snapshot.get('final_url', url) != url:
        raise ValueError('detail_source_identity_mismatch: response URL differs')
    part = rivoyat_payloads(source).get(url)
    if part is None:
        raise ValueError('detail_source_identity_unresolved: exact copy payload absent')
    fields = {'ar': 'arabic', 'uz-Latn': 'latin', 'uz-Cyrl': 'cyrillic'}
    for version in row.get('language_versions', []):
        field = fields.get(version['language'])
        if field is None or part.get(field) != version['text']:
            raise ValueError('detail_source_text_mismatch: ' + version['language'])
    tree = Tree(source).root
    main = tree.first(lambda n: n.tag == 'main')
    cards = list(main.all(lambda n: n.has('h-card'))) if main else []
    if len(cards) != 1:
        raise ValueError('detail_layout_unresolved: expected one narration card')
    container = main.first(lambda n: n.has('hukm'))
    output = {'schema': 'hadith-bank-rivoyat-detail-metadata-v1',
              'source_url': url, 'snapshot_path': snapshot['path'],
              'snapshot_sha256': snapshot['sha256'],
              'identity_basis': 'Exact publisher URL and all source-language text SHA256 values',
              'matched_language_text_sha256': {v['language']: sha(v['text'].encode())
                  for v in row.get('language_versions', [])},
              'scope': 'Publisher detail grading, its attached notes and explicitly listed other sources; similar-hadith suggestions excluded',
              'translation_upstream_source_verified': False,
              'languages': {language: {'references': [], 'comments': [], 'grading_details': []}
                            for language in fields},
              'grading_rows': 0, 'listed_source_rows': 0,
              'metadata_container_present': container is not None}
    if container is None:
        return output

    def citation(node, language, kind, boundary, collection_node=None, locator_node=None):
        value = rivoyat_language_text(node, language, source_titles=True)
        if not value:
            return None
        return {'collection': rivoyat_language_text(collection_node, language, source_titles=True) or None,
                'number': None, 'source_citation': value,
                'source_locator_text': plain(locator_node) or None,
                'url': url, 'scope': kind, 'source_language': language,
                'canonical_mapping_status': 'not_inferred',
                'translation_source_verified': False,
                'boundary_basis': boundary, 'snapshot_path': snapshot['path'],
                'snapshot_sha256': snapshot['sha256']}

    for listing in container.all(lambda n: n.has('hk-list')):
        for ordinal, item in enumerate(n for n in listing.children if isinstance(n, Node) and n.tag == 'li'):
            output['grading_rows'] += 1
            chip = item.first(lambda n: n.has('chip'))
            who = item.first(lambda n: n.has('hk-who'))
            sources = list(item.all(lambda n: n.has('hk-src') or n.has('hk-also')))
            notes = list(item.all(lambda n: n.has('hk-tx')))
            for language, values in output['languages'].items():
                grade = rivoyat_language_text(chip, language, source_titles=True)
                grader = rivoyat_language_text(who, language, source_titles=True)
                details = {'grade': grade or None, 'grader': grader or None,
                           'is_primary_as_marked_by_publisher': item.has('is-main'),
                           'source_order': ordinal + 1, 'source_url': url,
                           'snapshot_path': snapshot['path'], 'snapshot_sha256': snapshot['sha256'],
                           'basis': 'Publisher-supplied detail-page assessment; no independent authenticity decision'}
                if grade or grader:
                    values['grading_details'].append(details)
                if grade:
                    values['comments'].append({'kind': 'publisher_grade', 'text': grade,
                        'attributed_to': grader or None, 'source_url': url,
                        'boundary_basis': '.hukm .hk-list > li .chip',
                        'snapshot_path': snapshot['path'], 'snapshot_sha256': snapshot['sha256']})
                for node in sources:
                    title = node.first(lambda n: bool(n.attrs.get('title')))
                    reference = citation(node, language, 'publisher_grading_reference',
                                         '.hukm .hk-list > li .hk-src/.hk-also', title)
                    if reference:
                        values['references'].append(reference)
                for node in notes:
                    text = rivoyat_language_text(node, language)
                    if text:
                        values['comments'].append({'kind': 'source_grading_commentary', 'text': text,
                            'attributed_to': grader or None, 'source_url': url,
                            'boundary_basis': '.hukm .hk-list > li .hk-tx',
                            'snapshot_path': snapshot['path'], 'snapshot_sha256': snapshot['sha256'],
                            'contains_independently_quoted_material': 'not_separately_audited'})
    for listing in container.all(lambda n: n.has('mb-list')):
        for item in (n for n in listing.children if isinstance(n, Node) and n.tag == 'li'):
            output['listed_source_rows'] += 1
            title = item.first(lambda n: bool(n.attrs.get('title')))
            locator = item.first(lambda n: n.has('mb-loc'))
            for language, values in output['languages'].items():
                reference = citation(item, language, 'publisher_listed_other_source',
                                     '.hukm .mb-list > li', title, locator)
                if reference:
                    values['references'].append(reference)
    return output


def base_record(site, collection, source_entry_id, record_url, texts, references, snapshot,
                source_title, source_number, comments=None, grade=None, metadata=None):
    identity = f'{site}:{collection["key"]}:{source_entry_id}'
    classification, evidence = classify(texts.get('ar'), texts.get('uz-Latn') or texts.get('uz-Cyrl'), collection)
    book_key = collection['key']
    versions = []
    source_name = 'Rivoyat' if site == 'rivoyat' else 'Hadis.islom.uz'
    for language, value in texts.items():
        if not value:
            continue
        translator = collection.get('translator')
        provenance = None if language == 'ar' else {
            'ai_translation': 'unknown', 'translator': None,
            'basis': 'No source-specific AI declaration or named translator established for this exact entry. Current bank display policy is applied separately.',
            'evidence': snapshot['path']}
        if provenance is not None and translator:
            provenance.update({'ai_translation': False, 'translator': translator['name'],
                               'basis': 'Named human translator explicitly credited in this collection introduction.',
                               'evidence': translator['evidence']})
        versions.append({'id': identity + ':' + language, 'language': language,
                         'script': 'Arab' if language == 'ar' else ('Latn' if language.endswith('Latn') else 'Cyrl'),
                         'text': value,
                         'source': {'name': source_name, 'url': record_url, 'record_url': record_url,
                                    'snapshot_path': snapshot['path'], 'snapshot_sha256': snapshot['sha256'],
                                    'upstream_sources': []},
                         'references': references.get(language, []),
                         'comments': (comments or {}).get(language, []),
                         'translation_provenance': provenance,
                         'scope': 'source_entry', 'match_status': 'same_source_record'})
    row = {
        'id': identity, 'language': 'uz', 'source_language_code': 'uz-Latn' if site == 'rivoyat' else 'uz-Cyrl',
        'book_key': book_key, 'edition': 'publisher-web-20261112',
        'title': source_title, 'record_type': 'source_narration_occurrence',
        'content_kind': classification, 'classification': {'value': classification, **evidence},
        'text': {'arabic': texts.get('ar') or None,
                 'translation': texts.get('uz-Latn') or texts.get('uz-Cyrl') or None},
        'language_versions': versions,
        'source': {'title': collection['title'], 'url': collection['url'], 'record_url': record_url,
                   'publisher': source_name, 'metadata_scope': 'same_publisher_entry',
                   'original_metadata': metadata or {}},
        'number': {'source_entry_id': source_entry_id, 'in_book': source_number, 'canonical': None,
                   'scope': 'publisher_source_local', 'numbering_system': 'Publisher website numbering; no canonical equivalence inferred'},
        'narrator': {'name': None, 'basis': 'Narration context preserved verbatim; no narrator identity inferred'},
        'translator': {'name': None, 'evidence': None},
        'translation_provenance': {'origin': 'unknown', 'label': 'Unknown', 'ai_translation': 'unknown',
                                   'basis': 'Original provenance remains unknown; current owner new-book display policy is separate.',
                                   'evidence_ids': [snapshot['path']]},
        'ai_translation': 'unknown',
        'references': {'items': [ref for items in references.values() for ref in items],
                       'canonical_mapping_status': 'unverified'},
        'commentary': {'arabic': None, 'translation': None}, 'footnotes': [],
        'grading': {'grade': grade, 'grader': None, 'basis': 'Exact source grade string when supplied; no independent authenticity assessment'},
        'source_headings': [collection['title']], 'topic_tags': [], 'related_versions': [],
        'review': {'status': 'digital_source_import', 'issues': [], 'independent_pro_qc': 'not_performed',
                   'release_status': 'source_import', 'release_eligible': False, 'certified_release_eligible': False},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                   'source_notice_preserved_in': BASE + '/discovery/' + site + '-robots.txt'},
        'extraction': {'method': 'public_html_embedded_copy_payload' if site == 'rivoyat' else 'public_html_language_columns',
                       'ocr_used': False, 'is_excerpt': False, 'upstream_transcription_method': None,
                       'original_html_sha256': snapshot['sha256'], 'source_snapshot': snapshot['path']},
        'source_locator': {'path': snapshot['path'], 'sha256': snapshot['sha256'],
                           'format': 'gzip_compressed_original_http_html', 'record_url': record_url,
                           'text_hashes': {lang: sha(text.encode()) for lang, text in texts.items() if text}},
        'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None},
    }
    if collection.get('translator'):
        row['translator'] = collection['translator']
        row['ai_translation'] = False
        row['translation_provenance'].update({'origin': 'human_translator_credited', 'label': 'Human',
            'ai_translation': False, 'basis': 'Named translator credited in this collection introduction.',
            'evidence_ids': [collection['translator']['evidence']]})
    if classification != 'prophetic_report':
        row['review']['status'] = 'classification_pending_hidden'
        row['review']['issues'].append('Not registered in Hadith HTML/search until source-bound classification is established.')
    return row


class Importer:
    def __init__(self, root, site, max_pages, delay, timeout=45, max_seconds=600):
        self.root, self.site, self.origin = Path(root).resolve(), site, SITES[site]
        if excluded_by_owner(self.root, site):
            raise ValueError('Source excluded by owner; acquisition and registration disabled: ' + site)
        self.folder = self.root / BASE / site
        self.folder.mkdir(parents=True, exist_ok=True)
        self.state_path = self.folder / 'checkpoint.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {
            'schema': SCHEMA, 'site': site, 'origin': self.origin, 'created_at': now(),
            'collections': {}, 'tasks': [], 'snapshots': {}, 'events': [],
            'all_available_content_imported': False}
        self.max_pages, self.delay, self.timeout = max_pages, delay, timeout
        self.deadline = time.monotonic() + max_seconds
        self.requests = 0
        self.last_request = 0
        self.robot = None
        self.records = {}
        files = list(self.folder.glob('collection-*.jsonl.gz'))
        files.extend(file for file in self.folder.glob('collection-*.jsonl') if not file.with_suffix('.jsonl.gz').exists())
        for file in files:
            data = gzip.decompress(file.read_bytes()) if file.suffix == '.gz' else file.read_bytes()
            for line in data.decode('utf8').splitlines():
                if line:
                    row = json.loads(line)
                    self.records[row['id']] = row

    def enrich_local_metadata(self):
        """Fill citation/translator fields from already preserved source bytes."""
        for key, collection in self.state['collections'].items():
            snapshot = self.state['snapshots'].get(collection['url'])
            if snapshot:
                body = gzip.decompress((self.root / snapshot['path']).read_bytes())
                if sha(body) != snapshot['sha256']:
                    raise ValueError('Source snapshot checksum mismatch during metadata enrichment')
                text = plain(Tree(body.decode('utf8')).root, blocks=True)
                match = re.search(r'(?:^|\n)\s*Таржимон\s*[:：]\s*([^\n]{2,80})', text)
                if match:
                    collection['translator'] = {'name': match.group(1).strip(), 'evidence': snapshot['path'],
                        'url': collection['url'], 'source_declaration': match.group(0).strip()}
                elif self.site == 'islom':
                    match = re.search(r'Араб\s+тилидан\s+([^\n]{2,80}?)\s+таржимаси', text)
                    if match:
                        collection['translator'] = {'name': match.group(1).strip(), 'evidence': snapshot['path'],
                            'url': collection['url'], 'source_declaration': match.group(0)}
                if self.site == 'islom' and key in ('book-22', 'book-23'):
                    if ('101 ҳадис' in text and key == 'book-22') or ('الأحَادِيث النَّبَوِيَّة' in text and key == 'book-23'):
                        collection['bounded_matn_declaration'] = {
                            'title_as_supplied': collection['title'], 'snapshot_path': snapshot['path'],
                            'url': collection['url'],
                            'basis': 'Publisher identifies this bounded anthology as hadith/Prophetic hadith; entry-level narration citation is additionally required.'}
            for row in self.records.values():
                if row['book_key'] != key:
                    continue
                credit = collection.get('translator')
                if credit:
                    row['translator'] = credit
                    row['ai_translation'] = False
                    row['translation_provenance'].update({'origin': 'human_translator_credited', 'label': 'Human',
                        'ai_translation': False, 'basis': 'Named translator credited in the source collection introduction.',
                        'evidence_ids': [credit['evidence']]})
                classification, evidence = classify(row['text'].get('arabic'), row['text'].get('translation'), collection)
                if row['content_kind'] == 'unknown' and classification == 'prophetic_report' and row['review'].get('status') != 'source_variant_pending_hidden':
                    row['content_kind'] = classification
                    row['classification'] = {'value': classification, **evidence}
                    row['review']['status'] = 'digital_source_import'
                    row['review']['issues'] = [issue for issue in row['review']['issues'] if issue != 'Not registered in Hadith HTML/search until source-bound classification is established.']
                for version in row.get('language_versions', []):
                    language = version['language']
                    if self.site == 'islom':
                        existing = {json.dumps(r, sort_keys=True, ensure_ascii=False) for r in version['references']}
                        for reference in prose_references(version['text'], row['source']['record_url'], language):
                            if json.dumps(reference, sort_keys=True, ensure_ascii=False) not in existing:
                                version['references'].append(reference)
                        if row.get('separated_commentary', {}).get(language):
                            comment = row['separated_commentary'][language]
                            version['comments'] = [{'text': comment, 'source_url': row['source']['record_url'],
                                'kind': 'source_commentary', 'boundary_basis': 'explicit_commentary_heading',
                                'contains_independently_quoted_material': 'not_separately_audited'}]
                            version['comments_status'] = 'source_commentary_separately_preserved'
                    if language != 'ar' and credit:
                        version['translation_provenance'] = {'ai_translation': False, 'translator': credit['name'],
                            'basis': 'Named human translator credited in this source collection introduction.',
                            'evidence': credit['evidence']}
                row['references']['items'] = [ref for version in row.get('language_versions', []) for ref in version['references']]
            if any(row['book_key'] == key for row in self.records.values()):
                self.checkpoint_records(key)

    def prepare_detail_metadata_queue(self):
        """Retain a resumable task for every exact source occurrence."""
        if self.site != 'rivoyat':
            return
        tasks = self.state.setdefault('detail_metadata_tasks', {})
        for row in self.records.values():
            task = tasks.setdefault(row['id'], {
                'record_id': row['id'], 'record_url': row['source']['record_url'],
                'status': 'pending', 'stage': 'awaiting_source_detail_snapshot',
                'language_codes': [v['language'] for v in row.get('language_versions', [])],
                'fields_to_check': ['language_specific_citations', 'source_commentary',
                                    'upstream_source_credit', 'grading_details'],
                'section_snapshot_path': row.get('source_locator', {}).get('path'),
                'section_snapshot_sha256': row.get('source_locator', {}).get('sha256'),
                'expected_language_text_sha256': {
                    v['language']: sha(v['text'].encode()) for v in row.get('language_versions', [])},
            })
            task.update({'url': task['record_url'], 'kind': 'detail', 'collection': row['book_key']})
            status = 'detail_metadata_pending' if task['status'] != 'done' else 'detail_metadata_source_parsed'
            row['detail_metadata_status'] = status
            row['source']['detail_metadata_status'] = status
            row['source']['detail_metadata_queue_path'] = BASE + '/rivoyat/detail-metadata-queue.json'
            for version in row.get('language_versions', []):
                version['source']['detail_metadata_status'] = status
                if task['status'] != 'done':
                    version['references_status'] = 'section_reference_only_detail_metadata_pending'
                    if not version.get('comments'):
                        version['comments_status'] = 'detail_metadata_pending'
        counts = dict(collections.Counter(task['status'] for task in tasks.values()))
        self.state['detail_metadata_counts'] = counts
        atomic_json(self.folder / 'detail-metadata-queue.json', {
            'schema': 'hadith-bank-detail-metadata-queue-v1', 'site': self.site,
            'task_counts': counts, 'tasks': list(tasks.values()),
            'section_import_fetches_detail_pages': False,
            'bounded_detail_worker_implemented': True,
            'completion_requirement': 'Fetch the exact linked detail page under the same robots/rate controls; retain original response bytes; validate source-text identity and language-specific field boundaries before accepting enrichment.',
            'no_missing_field_content_inferred': True})

    def apply_detail_metadata(self, task, source, snapshot):
        row = self.records[task['record_id']]
        hashes = {v['language']: sha(v['text'].encode()) for v in row.get('language_versions', [])}
        if hashes != task['expected_language_text_sha256']:
            raise ValueError('detail_queue_source_hash_mismatch')
        metadata = rivoyat_detail_metadata(source, row, snapshot)
        # No narration field or accepted language identity is modified here.
        for version in row.get('language_versions', []):
            values = metadata['languages'].get(version['language'], {})
            for field in ('references', 'comments', 'grading_details'):
                existing = version.setdefault(field, [])
                known = {json_bytes(value) for value in existing}
                for value in values.get(field, []):
                    if json_bytes(value) not in known:
                        existing.append(value)
                        known.add(json_bytes(value))
            # Citations to other works do not establish the source of this
            # particular Uzbek translation. Keep that distinction explicit.
            version['source']['cited_works'] = values.get('references', [])
            version['source']['translation_upstream_source_verified'] = False
            version['source']['detail_snapshot_path'] = snapshot['path']
            version['source']['detail_snapshot_sha256'] = snapshot['sha256']
            version['references_status'] = 'source_detail_fields_parsed_canonical_identity_unverified'
            version['comments_status'] = ('source_detail_notes_preserved' if values.get('comments')
                                          else 'no_notes_in_supported_detail_blocks')
        row['references']['items'] = [ref for version in row.get('language_versions', [])
                                     for ref in version['references']]
        row['source']['detail_metadata'] = {key: value for key, value in metadata.items() if key != 'languages'}
        row['grading']['source_details'] = {lang: value['grading_details']
                                           for lang, value in metadata['languages'].items()}
        row['source']['original_metadata']['detail_page_metadata_status'] = 'source_snapshot_parsed'
        task.update({'status': 'done', 'stage': 'source_snapshot_parsed', 'finished_at': now(),
                     'snapshot_path': snapshot['path'], 'snapshot_sha256': snapshot['sha256'],
                     'grading_rows': metadata['grading_rows'],
                     'listed_source_rows': metadata['listed_source_rows']})
        task.pop('error', None)

    def enrich_cached_details(self):
        """Parse only already saved detail snapshots; never initiates HTTP."""
        if self.site != 'rivoyat':
            return
        for task in self.state.get('detail_metadata_tasks', {}).values():
            if task['status'] != 'pending' or task['record_url'] not in self.state['snapshots']:
                continue
            try:
                source, snapshot = self.fetch({'url': task['record_url']})
                self.apply_detail_metadata(task, source, snapshot)
            except Exception as error:
                task.update({'status': 'failed', 'attempts': 3,
                             'error': type(error).__name__ + ': ' + str(error)[:300],
                             'stage': 'source_identity_or_parser_review_required'})

    def preserve_request_error(self, url, error):
        """Retain an error response without retrying or changing access routes."""
        evidence = {'url': url, 'retrieved_at': now(), 'error': type(error).__name__ + ': ' + str(error)[:300]}
        if isinstance(error, urllib.error.HTTPError):
            evidence['status'] = error.code
            try:
                body = error.read(60 * 1024 * 1024 + 1)
                if len(body) <= 60 * 1024 * 1024:
                    path = self.folder / 'responses' / (sha(url.encode())[:16] + '-' + sha(body)[:16] + '.body.gz')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists():
                        path.write_bytes(gzip.compress(body, mtime=0))
                    evidence.update({'path': str(path.relative_to(self.root)), 'bytes': len(body),
                                     'sha256': sha(body), 'stored_sha256': sha(path.read_bytes()),
                                     'compression': 'gzip', 'response_complete': True})
                else:
                    evidence['response_body_status'] = 'exceeds_preservation_limit_not_saved'
            except Exception as capture_error:
                evidence['response_body_status'] = 'unavailable: ' + type(capture_error).__name__
        self.state['events'].append(evidence)
        if getattr(error, 'code', None) in (401, 403, 429) or str(error).startswith('robots_disallowed'):
            self.state['site_access_block'] = evidence
            self.state['site_stop_reason'] = 'Source access denied; automatic acquisition paused. No automatic bypass or retry.'
        return evidence

    def enqueue(self, url, kind, collection=None):
        parsed = urllib.parse.urlsplit(urllib.parse.urljoin(self.origin, url))
        if parsed.netloc != urllib.parse.urlsplit(self.origin).netloc:
            return
        url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ''))
        if any(task['url'] == url for task in self.state['tasks']):
            return
        self.state['tasks'].append({'url': url, 'kind': kind, 'collection': collection, 'status': 'pending'})

    def save(self):
        self.state['updated_at'] = now()
        self.state['counts'] = dict(collections.Counter(t['status'] for t in self.state['tasks']))
        self.state['record_counts'] = dict(collections.Counter(row['content_kind'] for row in self.records.values()))
        self.state['detail_metadata_counts'] = dict(collections.Counter(
            task['status'] for task in self.state.get('detail_metadata_tasks', {}).values()))
        pending = any(t['status'] != 'done' for t in self.state['tasks'])
        self.state['all_linked_pages_processed'] = (not (self.state.get('access_block') or self.state.get('site_access_block'))
                                                    and not pending and bool(self.state['tasks']))
        # Site content may exceed declared/indexed items or quote additional
        # narrations inside commentary: never equate queue exhaustion to all.
        self.state['all_available_content_imported'] = False
        atomic_json(self.state_path, self.state)

    def request(self, url, robots=False):
        if self.state.get('access_block') or self.state.get('site_access_block'):
            raise RuntimeError('prior_source_access_block: automatic acquisition paused')
        if not robots and self.robot is not None and not self.robot.can_fetch(AGENT, url):
            raise RuntimeError('robots_disallowed: ' + url)
        if self.requests >= self.max_pages:
            raise StopIteration('request_budget')
        if time.monotonic() >= self.deadline:
            raise StopIteration('time_budget')
        wait = self.delay - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        self.requests += 1
        self.last_request = time.monotonic()
        request = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,text/plain;q=0.9'})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            final_url = response.geturl()
            if urllib.parse.urlsplit(final_url).netloc != urllib.parse.urlsplit(self.origin).netloc:
                raise RuntimeError('unexpected_cross_host_redirect: ' + final_url)
            body = response.read(60 * 1024 * 1024 + 1)
            if len(body) > 60 * 1024 * 1024:
                raise RuntimeError('response_exceeds_60MiB_safety_limit')
            return body, {'url': url, 'final_url': final_url, 'status': response.status,
                          'content_type': response.headers.get('Content-Type'), 'retrieved_at': now(),
                          'bytes': len(body), 'sha256': sha(body)}

    def robots(self):
        path = self.root / BASE / 'discovery' / (self.site + '-robots.txt')
        if path.exists():
            body = path.read_bytes()
        else:
            body, evidence = self.request(self.origin + '/robots.txt', robots=True)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            atomic_json(path.with_suffix('.metadata.json'), evidence)
        robot = urllib.robotparser.RobotFileParser()
        robot.parse(body.decode('utf8', 'replace').splitlines())
        self.robot = robot
        self.state['robots'] = {'path': str(path.relative_to(self.root)), 'sha256': sha(body),
                                'checked_user_agent': AGENT,
                                'api_access_used': False}

    def fetch(self, task):
        url = task['url']
        cached = self.state['snapshots'].get(url)
        if cached:
            body = gzip.decompress((self.root / cached['path']).read_bytes())
            if sha(body) != cached['sha256']:
                raise RuntimeError('cached_snapshot_checksum_mismatch')
            return body.decode('utf8'), cached
        # Adopt same-session discovery bytes without refetching/reinventing them.
        aliases = {
            'rivoyat': {'/': 'rivoyat-home', '/buxoriy': 'rivoyat-buxoriy', '/buxoriy/1': 'rivoyat-buxoriy-1', '/yordam': 'rivoyat-help'},
            'islom': {'/': 'islom-home', '/kitob/24/1': 'islom-arbain', '/kitob/28/0': 'islom-riyadh-0'}}
        alias = aliases[self.site].get(urllib.parse.urlsplit(url).path)
        adopted = self.root / BASE / 'discovery' / ((alias or 'missing') + '.html')
        if alias and adopted.exists():
            body = adopted.read_bytes()
            metadata = {'url': url, 'final_url': url, 'status': 200, 'content_type': 'text/html',
                        'retrieved_at': dt.datetime.fromtimestamp(adopted.stat().st_mtime, dt.timezone.utc).isoformat(),
                        'bytes': len(body), 'sha256': sha(body),
                        'acquisition': 'adopted_exact_same_session_HTTP_discovery_snapshot'}
        else:
            body, metadata = self.request(url)
        path = self.folder / 'snapshots' / (sha(url.encode())[:16] + '-' + metadata['sha256'][:16] + '.html.gz')
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(gzip.compress(body, mtime=0))
        metadata['path'] = str(path.relative_to(self.root))
        metadata['stored_sha256'] = sha(path.read_bytes())
        self.state['snapshots'][url] = metadata
        return body.decode('utf8'), metadata

    def catalogue(self, tree, snapshot):
        for a in links(tree):
            href = a.attrs['href']
            if self.site == 'rivoyat':
                if not re.fullmatch(r'/[a-z][a-z-]+', href):
                    continue
                title_node = a.first(lambda n: n.has('lat'))
                label = plain(a, blocks=True)
                # Adjacent Latin/Cyrillic spans have no separating whitespace in
                # the source DOM, so a trailing word-boundary is inappropriate.
                if 'hadis' not in label or 'kitob' not in label:
                    continue
                title = plain(title_node) or label
                match = re.search(r'([\d\s]+) hadis', label)
                count = int(re.sub(r'\s', '', match.group(1))) if match else None
                key = href[1:]
            else:
                if not re.fullmatch(r'/kitob/\d+', href):
                    continue
                label = plain(a, blocks=True)
                match = re.search(r'(\d+)\s*$', label)
                count = int(match.group(1)) if match else None
                title = label[:match.start()].strip() if match else label
                key = 'book-' + href.split('/')[-1]
            url = self.origin + href
            self.state['collections'].setdefault(key, {'key': key, 'title': title, 'url': url,
                                                       'advertised_count': count,
                                                       'catalogue_snapshot': snapshot['path']})
            self.enqueue(url, 'collection', key)
        if self.site == 'rivoyat':
            self.enqueue('/yordam', 'evidence')
        if not self.state['collections']:
            raise ValueError('No recognizable publisher collections on the homepage; catalogue coverage is unresolved')

    def sections(self, tree, task, source):
        collection = self.state['collections'][task['collection']]
        basepath = urllib.parse.urlsplit(collection['url']).path
        for a in links(tree):
            href = a.attrs['href']
            path = urllib.parse.urlsplit(href).path
            if re.fullmatch(re.escape(basepath) + r'/\d+', path):
                self.enqueue(href, 'section', task['collection'])
        collection['section_count'] = sum(t['kind'] == 'section' and t['collection'] == task['collection'] for t in self.state['tasks'])
        if not collection['section_count']:
            raise ValueError('No linked sections found for this collection; cannot mark collection enumeration complete')
        # Publisher introduction text is evidence, not a narration.
        evidence = {'url': task['url'], 'kind': 'publisher_collection_introduction',
                    'text': plain(tree.first(lambda n: n.tag == 'main') or tree, blocks=True)}
        match = re.search(r'(?:^|\n)\s*Таржимон\s*[:：]\s*([^\n]{2,80})', evidence['text'])
        if match:
            collection['translator'] = {'name': match.group(1).strip(),
                'evidence': self.state['snapshots'][task['url']]['path'], 'url': task['url'],
                'source_declaration': match.group(0).strip()}
        packed_json(self.folder / 'introductions' / (task['collection'] + '.json.gz'), evidence)

    def add_record(self, row):
        old = self.records.get(row['id'])
        if old is not None:
            if old['text'] != row['text'] or [(v['language'], v['text']) for v in old['language_versions']] != [(v['language'], v['text']) for v in row['language_versions']]:
                # A source changes its text while preserving identity: retain a
                # separate candidate version rather than overwrite accepted text.
                fingerprint = {'text': row['text'], 'language_versions': [
                    {'language': version['language'], 'text': version['text']} for version in row['language_versions']]}
                row['id'] += ':version-' + sha(json_bytes(fingerprint))[:16]
                for version in row['language_versions']:
                    version['id'] = row['id'] + ':' + version['language']
                row['content_kind'] = 'unknown'
                row['review']['status'] = 'source_variant_pending_hidden'
                row['related_versions'].append({'id': old['id'], 'relationship': 'same_publisher_id_different_source_bytes'})
            else:
                return
        self.records[row['id']] = row

    def rivoyat_records(self, tree, source, task, snapshot):
        collection = self.state['collections'][task['collection']]
        payloads = rivoyat_payloads(source)
        cards = list(tree.all(lambda n: n.has('h-card')))
        parsed_count = 0
        for card in cards:
            anchor = card.first(lambda n: n.tag == 'a' and n.has('num'))
            if anchor is None:
                continue
            url = urllib.parse.urljoin(self.origin, anchor.attrs['href'])
            part = payloads.get(url)
            if part is None:
                arabic = plain(card.first(lambda n: n.has('ar-body')), blocks=True)
                body = card.first(lambda n: n.tag == 'p' and n.attrs.get('data-open-area') == 'true')
                part = {'arabic': arabic,
                        'latin': plain(body.first(lambda n: n.has('lat'))) if body else '',
                        'cyrillic': plain(body.first(lambda n: n.has('kir'))) if body else '',
                        'reference': plain(anchor), 'grade': plain(card.first(lambda n: n.has('grade-link'))),
                        'url': url, 'fallback': 'public_rendered_html_text'}
            number = urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1]
            source_id = urllib.parse.urlsplit(url).path[len('/' + collection['key'] + '/'):]
            texts = {'ar': part['arabic'], 'uz-Latn': part['latin'], 'uz-Cyrl': part['cyrillic']}
            refs = {lang: [source_ref(collection['title'], number, part.get('reference'), url, lang)] for lang in texts}
            row = base_record('rivoyat', collection, source_id, url, texts, refs, snapshot,
                              part.get('reference') or collection['title'] + ' ' + number, number,
                              grade=part.get('grade'), metadata={'copy_payload': part,
                                  'detail_page_metadata_status': 'not_separately_fetched',
                                  'unknown_upstream_provenance_not_inferred': True})
            row['extraction']['method'] = part.get('fallback', 'public_html_embedded_copy_payload')
            self.add_record(row)
            parsed_count += 1
        if parsed_count == 0:
            raise ValueError('No recognizable numbered Rivoyat cards on a linked section; held as parser/coverage failure, not completed')
        self.pagination(tree, task)

    def pagination(self, tree, task):
        basepath = urllib.parse.urlsplit(task['url']).path
        for a in links(tree):
            href = urllib.parse.urljoin(self.origin, a.attrs['href'])
            parsed = urllib.parse.urlsplit(href)
            if parsed.path == basepath and parsed.query and parsed.netloc == urllib.parse.urlsplit(self.origin).netloc:
                self.enqueue(href, 'section', task['collection'])

    def islom_records(self, tree, source, task, snapshot):
        collection = self.state['collections'][task['collection']]
        containers = list(tree.all(lambda n: n.has('bookin_main_bob_block') and (n.attrs.get('id') or '').startswith('hadis')))
        parsed_count = 0
        for container in containers:
            uznode = container.first(lambda n: n.has('bookin_main_uzbek_text'))
            arnode = container.first(lambda n: n.has('bookin_main_arabic_text'))
            if uznode is None and arnode is None:
                continue
            title = plain(container.first(lambda n: n.has('table_hadith_number')))
            anchor = container.first(lambda n: n.tag == 'a' and re.fullmatch(r'/kitob/\d+/\d+/[^/]+', n.attrs.get('href', '')))
            url = urllib.parse.urljoin(self.origin, anchor.attrs['href']) if anchor else task['url'] + '#' + container.attrs['id']
            raw_id = (uznode or arnode).attrs.get('id', '')
            source_id = re.sub(r'^(?:uzbek|arabic)', '', raw_id) or sha(url.encode())[:16]
            number_match = re.match(r'(\d+)', title)
            number = number_match.group(1) if number_match else None
            uzfull, arfull = plain(uznode, blocks=True), plain(arnode, blocks=True)
            uz, uzcomment, uzreason = split_islom_text(uzfull)
            ar, arcomment, arreason = split_islom_text(arfull)
            refs = {lang: [source_ref(collection['title'], number, title, url, lang)] for lang in ('ar', 'uz-Cyrl')}
            refs['ar'].extend(prose_references(ar, url, 'ar'))
            refs['uz-Cyrl'].extend(prose_references(uz, url, 'uz-Cyrl'))
            # Source citations remain verbatim. Parse no numeric canonical link
            # from unreviewed prose or from book-local display ordinals.
            texts = {'ar': ar, 'uz-Cyrl': uz}
            row = base_record('islom', collection, source_id, url, texts, refs, snapshot, title, number,
                              metadata={'html_provider_id': source_id, 'html_anchor': container.attrs['id'],
                                        'paragraph_text_separator': '\n',
                                        'commentary_split_basis': {'ar': arreason, 'uz-Cyrl': uzreason}})
            # Full mixed-language columns, detached commentary and any embedded
            # additional reports stay in the source ledger, outside Hadith HTML.
            row['source_columns'] = {'ar': arfull, 'uz-Cyrl': uzfull}
            row['separated_commentary'] = {'ar': arcomment, 'uz-Cyrl': uzcomment}
            for version in row['language_versions']:
                if row['separated_commentary'].get(version['language']):
                    version['comments_status'] = 'source_commentary_preserved_in_audit_pending_boundary_review'
            row['source_locator']['html_element_ids'] = {'ar': arnode.attrs.get('id') if arnode else None,
                                                        'uz-Cyrl': uznode.attrs.get('id') if uznode else None}
            if uzcomment or arcomment:
                row['extraction']['is_excerpt'] = True
                row['extraction']['commentary_embedded_reports_separately_extracted'] = False
                row['review']['issues'].append('Explicit source commentary is retained outside narration text; additional reports quoted inside commentary await separate extraction.')
            self.add_record(row)
            parsed_count += 1
        if parsed_count == 0:
            raise ValueError('No recognizable numbered Islom language columns on a linked section; held as parser/coverage failure, not completed')

    def checkpoint_records(self, key):
        rows = [r for r in self.records.values() if r['book_key'] == key]
        rows.sort(key=lambda r: r['id'])
        path = self.folder / ('collection-' + key + '.jsonl.gz')
        temp = path.with_suffix('.gz.tmp')
        temp.write_bytes(gzip.compress(b''.join(json_bytes(r) for r in rows), mtime=0))
        temp.replace(path)
        # Transitional files are exact same-run derived ledgers, not original
        # publisher bytes; their complete UTF-8 contents now live in gzip.
        old = self.folder / ('collection-' + key + '.jsonl')
        if old.exists():
            old.unlink()

    def run(self):
        self.prepare_detail_metadata_queue()
        self.enqueue('/', 'home')
        detail_tasks = self.state.get('detail_metadata_tasks', {})
        if self.state.get('access_block') or self.state.get('site_access_block') or any(task['status'] == 'blocked'
                for task in [*self.state['tasks'], *detail_tasks.values()]):
            self.state['site_stop_reason'] = 'Prior HTTP/robots block requires an explicit access review; no automatic bypass or block retry.'
            self.save()
            return self.export()
        robots_url = self.origin + '/robots.txt'
        robots_task = next((t for t in self.state['tasks'] if t['url'] == robots_url), None)
        if robots_task and robots_task['status'] == 'failed' and robots_task.get('attempts', 0) >= 3:
            self.state['last_stop_reason'] = 'robots_transient_retry_limit_requires_attention'
            self.save()
            return self.export()
        try:
            self.robots()
            if robots_task:
                robots_task.update({'status': 'done', 'finished_at': now()})
                robots_task.pop('error', None)
        except StopIteration as reason:
            self.state['last_stop_reason'] = str(reason)
            self.save()
            return self.export()
        except Exception as error:
            if robots_task is None:
                robots_task = {'url': robots_url, 'kind': 'robots', 'collection': None}
                self.state['tasks'].append(robots_task)
            evidence = self.preserve_request_error(robots_url, error)
            robots_task.update({'status': 'blocked' if self.state.get('site_access_block') else 'failed',
                                'attempts': robots_task.get('attempts', 0) + 1,
                                'error': 'HTTP ' + str(error.code) if isinstance(error, urllib.error.HTTPError) else evidence['error']})
            self.state['last_stop_reason'] = 'robots_access_blocked' if robots_task['status'] == 'blocked' else 'robots_request_failed'
            self.save()
            return self.export()
        # Retry transient failures only in a subsequent run, at most three
        # times. Authentication/rate/robots blocks are never retried here.
        for task in [*self.state['tasks'], *detail_tasks.values()]:
            if task['status'] == 'failed' and task.get('attempts', 1) < 3 and not task.get('error', '').startswith('HTTP 404'):
                task['status'] = 'pending'
        while True:
            if time.monotonic() >= self.deadline:
                self.state['last_stop_reason'] = 'time_budget'
                break
            pending = [task for task in [*self.state['tasks'], *detail_tasks.values()] if task['status'] == 'pending']
            if not pending:
                break
            completed = collections.Counter(task['collection'] for task in self.state['tasks']
                if task['kind'] == 'section' and task['status'] == 'done')
            # First enumerate the complete collection catalogue; then fairly
            # alternate collections rather than exhaust a giant work first.
            rank = {'home': 0, 'robots': 0, 'collection': 1, 'evidence': 2,
                    'section': 4 if self.state.get('last_work_kind') == 'section' else 3,
                    'detail': 3 if self.state.get('last_work_kind') == 'section' else 4}
            task = min(pending, key=lambda t: (rank[t['kind']], completed[t['collection']]))
            try:
                task['attempts'] = task.get('attempts', 0) + 1
                source, snapshot = self.fetch(task)
                tree = Tree(source).root
                if task['kind'] == 'home':
                    self.catalogue(tree, snapshot)
                elif task['kind'] == 'collection':
                    self.sections(tree, task, source)
                elif task['kind'] == 'section':
                    if self.site == 'rivoyat':
                        self.rivoyat_records(tree, source, task, snapshot)
                    else:
                        self.islom_records(tree, source, task, snapshot)
                    self.checkpoint_records(task['collection'])
                    self.prepare_detail_metadata_queue()
                    detail_tasks = self.state.get('detail_metadata_tasks', {})
                elif task['kind'] == 'detail':
                    self.apply_detail_metadata(task, source, snapshot)
                    self.checkpoint_records(task['collection'])
                task['status'], task['finished_at'] = 'done', now()
                task['snapshot_path'] = snapshot['path']
                self.state['last_work_kind'] = task['kind']
            except StopIteration as reason:
                task['attempts'] -= 1
                self.state['last_stop_reason'] = str(reason)
                break
            except urllib.error.HTTPError as error:
                task['status'] = 'blocked' if error.code in (401, 403, 429) else 'failed'
                task['error'] = 'HTTP ' + str(error.code)
                self.preserve_request_error(task['url'], error)
                self.save()
                # Never switch credentials, hosts, API routes or proxies to get
                # around a rejection; a rate/auth block stops this whole site.
                if error.code in (401, 403, 429):
                    break
            except Exception as error:
                task['status'] = 'blocked' if str(error).startswith('robots_disallowed') else 'failed'
                task['error'] = type(error).__name__ + ': ' + str(error)[:300]
                self.preserve_request_error(task['url'], error)
                if task['kind'] == 'detail' and isinstance(error, ValueError):
                    task['attempts'] = 3
                    task['stage'] = 'source_identity_or_parser_review_required'
                if task['status'] == 'blocked':
                    self.save()
                    break
            self.save()
        self.save()
        return self.export()

    def write_material_parts(self, slug, manifest, records):
        """Keep stable occurrence-to-part assignments below GitHub blob limits."""
        target = PUBLICATION_PART_BYTES
        mapping = self.state.setdefault('material_partitions', {}).setdefault(slug, {})
        groups, sizes = {}, collections.Counter()
        fresh = []
        for row in records:
            # Raw copy payloads are already preserved in the source ledger and
            # original HTML; don't repeat three extra text copies in the reader.
            row = json.loads(json.dumps(row, ensure_ascii=False))
            metadata = row.get('source', {}).get('original_metadata', {})
            payload = metadata.pop('copy_payload', None)
            if payload is not None:
                metadata['copy_payload_field_names'] = sorted(payload)
                metadata['copy_payload_preserved_in_source_snapshot'] = True
            encoded = json_bytes(row)
            if len(encoded) > target:
                raise ValueError('A single source entry exceeds the 40MiB publication-part limit; explicit handling required')
            part = mapping.get(row['id'])
            if part is None:
                fresh.append((row, encoded))
            else:
                groups.setdefault(int(part), []).append((row, encoded))
                sizes[int(part)] += len(encoded)
        part = max(groups, default=1)
        for row, encoded in fresh:
            if sizes[part] + len(encoded) > target:
                part += 1
            mapping[row['id']] = part
            groups.setdefault(part, []).append((row, encoded))
            sizes[part] += len(encoded)
        source_descriptor = manifest['source']
        source_bytes = (self.root / source_descriptor['path']).read_bytes()
        if sha(source_bytes) != source_descriptor['sha256']:
            raise ValueError('Publication source evidence checksum mismatch')
        source_filename = Path(source_descriptor['path']).name
        source_edition = manifest['edition']
        for part, entries in groups.items():
            if sizes[part] > 90 * 1024 * 1024:
                raise ValueError('Existing publication part grew above 90MiB; preserve it and review a partition migration before upload')
            part_slug = slug if part == 1 else slug + '-part-' + str(part).zfill(4)
            folder = self.root / 'materials' / part_slug
            folder.mkdir(parents=True, exist_ok=True)
            # Each registered part owns its source file and a unique internal
            # edition key. This suffix identifies a publication partition, not
            # a newly inferred publisher edition. Occurrence/version IDs stay
            # unchanged, and persistent assignments keep earlier parts stable.
            part_edition = source_edition if part == 1 else source_edition + '-part-' + str(part).zfill(4)
            part_rows = []
            for row, _ in sorted(entries, key=lambda e: e[0]['id']):
                row['edition'] = part_edition
                part_rows.append(row)
            part_bytes = b''.join(json_bytes(row) for row in part_rows)
            (folder / 'records.jsonl').write_bytes(part_bytes)
            owned_source = folder / source_filename
            owned_source.write_bytes(source_bytes)
            part_manifest = json.loads(json.dumps(manifest, ensure_ascii=False))
            part_manifest['id'] = part_manifest['source_id'] = part_slug
            part_manifest['edition'] = part_edition
            part_manifest['source'] = {**source_descriptor,
                'path': str(owned_source.relative_to(self.root)), 'sha256': sha(source_bytes)}
            part_manifest['records'] = {'path': str((folder / 'records.jsonl').relative_to(self.root)),
                                        'sha256': sha(part_bytes), 'count': len(entries)}
            part_manifest['extraction_scope']['source_edition_key_before_partitioning'] = source_edition
            part_manifest['extraction_scope']['publication_part'] = part
            part_manifest['extraction_scope']['records_in_this_part'] = len(entries)
            part_manifest['extraction_scope']['part_assignment_basis'] = 'Persistent source-occurrence IDs; new entries append without moving previous assignments'
            atomic_json(folder / 'manifest.json', part_manifest)

    def export(self):
        reviews = SourceReviews(self.root, self.site) if self.site == 'islom' else None
        baselines = {identity: copy.deepcopy(row) for identity, row in self.records.items()
                     if reviews and identity in reviews.decisions}
        self.prepare_detail_metadata_queue()
        self.enrich_cached_details()
        self.prepare_detail_metadata_queue()
        self.enrich_local_metadata()
        reviewed_rows, decisions = {}, {}
        for identity, row in self.records.items():
            reviewed_rows[identity], decisions[identity] = (reviews.apply(row, baseline=baselines.get(identity))
                if reviews else (row, None))
        if reviews:
            reviews.finish()
        summaries = []
        for key, collection in self.state['collections'].items():
            all_rows = [r for r in reviewed_rows.values() if r['book_key'] == key]
            accepted = [r for r in all_rows if decisions[r['id']] == 'register' or
                        (decisions[r['id']] is None and r['content_kind'] == 'prophetic_report')]
            excluded = [r for r in all_rows if decisions[r['id']] == 'exclude']
            held = [r for r in all_rows if decisions[r['id']] == 'hold' or
                    (decisions[r['id']] is None and r['content_kind'] != 'prophetic_report')]
            tasks = [t for t in self.state['tasks'] if t.get('collection') == key]
            detail_tasks = [t for t in self.state.get('detail_metadata_tasks', {}).values()
                            if t.get('collection') == key]
            summary = {'collection': key, 'title': collection['title'], 'advertised_count': collection['advertised_count'],
                       'source_entries_obtained': len(all_rows), 'prophetic_source_entries_registered': len(accepted),
                       'registered_source_occurrences': len(accepted), 'non_narration_source_entries': len(excluded),
                       'registration_count_scope': 'Legacy prophetic count includes explicitly reviewed numbered reports and sayings under their actual report type.',
                       'classification_pending_hidden': len(held), 'page_tasks': dict(collections.Counter(t['status'] for t in tasks)),
                       'detail_metadata_tasks': dict(collections.Counter(t['status'] for t in detail_tasks)),
                       'all_declared_entries_obtained': len(all_rows) == collection['advertised_count'] if collection['advertised_count'] is not None else None,
                       'complete_import_certified': False}
            summaries.append(summary)
            if not accepted:
                continue
            slug = self.site + '-' + key + '-uz-web'
            folder = self.root / 'materials' / slug
            folder.mkdir(parents=True, exist_ok=True)
            prefix = str(folder.relative_to(self.root)) + '/'
            records = []
            for original in accepted:
                row = dict(original)
                row.pop('source_columns', None)
                row.pop('separated_commentary', None)
                records.append(row)
            records.sort(key=lambda r: r['id'])
            record_bytes = b''.join(json_bytes(row) for row in records)
            (folder / 'records.jsonl').write_bytes(record_bytes)
            source_urls = {collection['url'], *(t['url'] for t in tasks), *(t['record_url'] for t in detail_tasks)}
            snapshots = [v for u, v in self.state['snapshots'].items() if u in source_urls]
            bundle = {'schema': 'hadith-bank-web-source-evidence-v1', 'publisher': self.site,
                      'collection': collection, 'snapshots': snapshots, 'checkpoint': str(self.state_path.relative_to(self.root)),
                      'source_entry_ledger': BASE + '/' + self.site + '/collection-' + key + '.jsonl.gz',
                      'retrieval_method': 'ordinary_public_HTTP_HTML', 'api_used': False,
                      'detail_metadata_scope': 'bounded_source_details_with_explicit_remaining_queue' if self.site == 'rivoyat' else 'source_language_columns',
                      'detail_metadata_queue_path': BASE + '/rivoyat/detail-metadata-queue.json' if self.site == 'rivoyat' else None,
                      'rights': {'status': 'not_assessed_for_publication', 'robots': self.state.get('robots')},
                      'scope': summary}
            atomic_json(folder / 'source-evidence.json', bundle)
            evidence_bytes = (folder / 'source-evidence.json').read_bytes()
            manifest = {'schema': 'hadith-bank-material-v1', 'id': slug, 'adapter': 'records-v1',
                        'language': 'uz', 'book': key, 'edition': 'publisher-web-20261112', 'source_id': slug,
                        'records': {'path': prefix + 'records.jsonl', 'sha256': sha(record_bytes), 'count': len(records)},
                        'source': {'path': prefix + 'source-evidence.json', 'sha256': sha(evidence_bytes),
                                   'name': collection['title'] + ' — ' + ('Rivoyat' if self.site == 'rivoyat' else 'Hadis.islom.uz'),
                                   'format': 'web-source-evidence-json', 'url': collection['url']},
                        'publication': {'authorized': True, 'decision': 'owner_requested_public_source_import',
                                        'decision_date_japan': '2026-11-12',
                                        'basis': 'Owner requested importing all three identified websites and supporting all languages with source-specific references and comments.'},
                        'extraction_scope': summary,
                        'counterpart_policy': {'mode': 'disabled', 'reason': 'Only exact same-source-entry language versions are accepted in this intake. External canonical Arabic/English/other-language matching requires separately verified source identity.'}}
            manifest['supporting_files'] = [
                {'path': snapshot['path'], 'sha256': snapshot['stored_sha256'],
                 'size_bytes': (self.root / snapshot['path']).stat().st_size,
                 'original_response_sha256': snapshot['sha256'], 'format': 'html+gzip', 'compression': 'gzip',
                 'url': snapshot['url']}
                for snapshot in snapshots]
            ledger_path = self.folder / ('collection-' + key + '.jsonl.gz')
            manifest['supporting_files'].append({'path': str(ledger_path.relative_to(self.root)),
                'sha256': sha(ledger_path.read_bytes()), 'size_bytes': ledger_path.stat().st_size,
                'format': 'jsonl+gzip', 'compression': 'gzip',
                'uncompressed_sha256': sha(gzip.decompress(ledger_path.read_bytes())),
                'role': 'complete_source_entry_and_commentary_ledger'})
            if reviews:
                manifest['supporting_files'].extend(reviews.supporting_files())
            if self.site == 'rivoyat':
                queue_path = self.folder / 'detail-metadata-queue.json'
                manifest['supporting_files'].append({'path': str(queue_path.relative_to(self.root)),
                    'sha256': sha(queue_path.read_bytes()), 'size_bytes': queue_path.stat().st_size,
                    'format': 'json', 'role': 'detail_metadata_queue_and_source_parse_receipts'})
            self.write_material_parts(slug, manifest, records)
        self.save()
        report = {'site': self.site, 'updated_at': now(), 'requests_this_run': self.requests,
                  'collections': summaries, 'task_counts': self.state.get('counts', {}),
                  'source_entries_obtained': len(self.records),
                  'prophetic_source_entries_registered': sum(s['prophetic_source_entries_registered'] for s in summaries),
                  'registered_source_occurrences': sum(s['registered_source_occurrences'] for s in summaries),
                  'non_narration_source_entries': sum(s['non_narration_source_entries'] for s in summaries),
                  'source_review_inputs': reviews.supporting_files() if reviews else [],
                  'source_review_engine_sha256': reviews.engine_sha256 if reviews else None,
                  'classification_pending_hidden': sum(s['classification_pending_hidden'] for s in summaries),
                  'access_block': self.state.get('site_access_block') or self.state.get('access_block'),
                  'site_stop_reason': self.state.get('site_stop_reason'),
                  'all_linked_pages_processed': self.state.get('all_linked_pages_processed', False),
                  'all_available_content_imported': False,
                  'blocked': bool(self.state.get('site_access_block') or self.state.get('access_block')) or any(t['status'] == 'blocked'
                      for t in [*self.state['tasks'], *self.state.get('detail_metadata_tasks', {}).values()]),
                  'block_reason': self.state.get('site_stop_reason'),
                  'errors': sum(t['status'] == 'failed'
                      for t in [*self.state['tasks'], *self.state.get('detail_metadata_tasks', {}).values()]),
                  'page_task_scope': 'catalogue_and_section_pages',
                  'detail_metadata_pending_count': sum(task.get('status') != 'done' for task in self.state.get('detail_metadata_tasks', {}).values()),
                  'detail_metadata_counts': self.state.get('detail_metadata_counts', {}),
                  'detail_metadata_queue_path': BASE + '/rivoyat/detail-metadata-queue.json' if self.site == 'rivoyat' else None,
                  'all_detail_metadata_processed': (bool(self.state.get('detail_metadata_tasks')) and all(task.get('status') == 'done' for task in self.state.get('detail_metadata_tasks', {}).values())) if self.site == 'rivoyat' else None,
                  'scope_note': 'Advertised counts are publisher counts, not unique Prophetic hadiths. Completeness remains unverified until all linked sections and held classifications are reconciled.'}
        atomic_json(self.folder / 'progress.json', report)
        self.save()
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--site', choices=['all', *SITES], default='all')
    parser.add_argument('--max-pages', type=int, default=100, help='Maximum new HTTP requests per site, including robots when not cached')
    parser.add_argument('--delay', type=float, default=1.0, help='Minimum interval between public requests; minimum 0.5 seconds')
    parser.add_argument('--export-only', action='store_true')
    parser.add_argument('--max-seconds', type=float, default=600, help='Graceful per-site time budget; saves and exports completed pages')
    args = parser.parse_args()
    if args.max_pages < 1 or args.delay < 0.5 or args.max_seconds < 1:
        parser.error('max-pages and max-seconds must be positive; delay must be at least 0.5 seconds')
    for site in SITES if args.site == 'all' else [args.site]:
        if excluded_by_owner(args.root, site):
            print(json.dumps({'site': site, 'state': 'excluded_by_owner',
                              'acquisition_enabled': False, 'registered_occurrences': 0}), flush=True)
            continue
        importer = Importer(args.root, site, args.max_pages, args.delay, max_seconds=args.max_seconds)
        report = importer.export() if args.export_only else importer.run()
        print(json.dumps({k: v for k, v in report.items() if k != 'collections'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
