#!/usr/bin/env python3
"""Batch-import the owner's Hadis.uz Tirmidhi catalogue through public links.

Catalogue previews discover detail URLs; only detail-page narration paragraphs
enter the reader. Source assessments and commentary remain separate. The
publisher URL ID is never interpreted as a canonical hadith number.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

from import_deenhindi import atomic, immutable, json_bytes, digest, now
from import_uzbek_web import Node, Tree, plain


ORIGIN = 'https://hadis.uz'
CATALOG = ORIGIN + '/hadiths/1'
BASE = 'imports/web-hadisuz-20261112'
SLUG = 'hadisuz-tirmidhi-uz-web'
EDITION = 'hadisuz-tirmidhi-web-20261112'
TITLE = 'Сунани Термизий — Sunan at-Tirmidhi'
AGENT = 'HadithBankSourceImporter/1.0'
MAX_PART = 40 * 1024 * 1024
MAX_RESPONSE = 20 * 1024 * 1024
INFO_PATHS = {'/page/about-project', '/page/sunani-termiziy'}
PROPHET = re.compile(r'Расулуллоҳ|Набий\b|Пайғамбар|Расули\s+[Аа]крам', re.I)
COMMENT_START = re.compile(r'^(?:Бу ҳадис|Ушбу ҳадис|Бу бобда|Шарҳ|Изоҳ|Ал-Ироқий|Имом\s)', re.I)
COLLECTION_CREDIT_SCOPE = 'publisher_collection_credit_not_per_entry_identity'
COLLECTION_CREDIT_MARKERS = {
    '/page/about-project': (
        ('translation_edition', re.compile(r'^Ҳадислар учун манба сифатида\b')),
        ('electronic_source', re.compile(r'^Камина шу китобларни\b')),
    ),
    '/page/sunani-termiziy': (
        ('translator', re.compile(r'^Мирзо Кенжабек, таржимон\b')),
        ('translation_source_edition', re.compile(r'^1\.\s+Мазкур таржима\b')),
        ('translation_resources', re.compile(r'^2\.\s+Ҳадисларни ўрганишда\b')),
        ('commentary_sources', re.compile(r'^7\.\s+Сахифа остида\b')),
    ),
}


def row_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def allowed_url(url, kind=None):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'hadis.uz' or parsed.fragment:
        return False
    if parsed.path == '/robots.txt':
        return kind == 'robots' and not parsed.query
    if parsed.path in INFO_PATHS:
        return kind in (None, 'info') and not parsed.query
    if re.fullmatch(r'/hadith/[1-9][0-9]*', parsed.path):
        return kind in (None, 'detail') and not parsed.query
    if parsed.path != '/hadiths/1' or kind not in (None, 'catalog'):
        return False
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    return not query or (set(query) == {'page'} and len(query['page']) == 1 and
                         re.fullmatch(r'[1-9][0-9]*', query['page'][0]) is not None)


class PublicRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        url = urllib.parse.urljoin(request.full_url, newurl)
        kind = 'robots' if request.full_url.endswith('/robots.txt') else None
        if not allowed_url(url, kind) or url != request.full_url:
            raise ValueError('Redirect changes the observed public source identity; review required')
        return super().redirect_request(request, fp, code, msg, headers, url)


def source_tree(raw):
    return Tree(raw.decode('utf-8', errors='strict')).root


def observed_links(tree, base):
    for node in tree.all(lambda n: n.tag == 'a' and n.attrs.get('href')):
        url = urllib.parse.urljoin(base, node.attrs['href'])
        if allowed_url(url):
            yield node, url


def parse_catalog(raw, url):
    tree = source_tree(raw)
    heading = tree.first(lambda n: n.tag == 'h1')
    if heading is None or 'Термизий' not in plain(heading):
        raise ValueError('Catalogue title does not identify the authorized Tirmidhi collection')
    column = tree.first(lambda n: n.has('col-md-9'))
    if column is None:
        raise ValueError('Missing observed catalogue content column')
    details = []
    for node, link in observed_links(column, url):
        if allowed_url(link, 'detail') and link not in details:
            details.append(link)
    if not details:
        raise ValueError('Empty catalogue layout; no completion inferred')
    next_pages = []
    for node, link in observed_links(column, url):
        if allowed_url(link, 'catalog') and 'next' in node.attrs.get('rel', '').split():
            next_pages.append(link)
    if len(set(next_pages)) > 1:
        raise ValueError('Ambiguous catalogue next-page links')
    info = sorted({link for _, link in observed_links(tree, url) if allowed_url(link, 'info')})
    return {'details': details, 'next': list(dict.fromkeys(next_pages)), 'info': info,
            'title': plain(heading), 'previews_not_registered': True}


def content_paragraphs(tree):
    column = tree.first(lambda n: n.has('col-md-9'))
    if column is None:
        raise ValueError('Missing observed detail content column')
    paragraphs = []
    unexpected = []
    for child in column.children:
        if not isinstance(child, Node):
            if child.strip():
                unexpected.append('unwrapped_text')
            continue
        if child.tag in ('script', 'hr') or child.has('ya-share2'):
            break
        if child.tag == 'p' and not child.has('text-center'):
            if plain(child):
                paragraphs.append(child)
        elif plain(child):
            unexpected.append(child.tag)
    return paragraphs, unexpected


def parse_detail(raw, url):
    if not allowed_url(url, 'detail'):
        raise ValueError('Unexpected detail URL')
    tree = source_tree(raw)
    paragraphs, unexpected = content_paragraphs(tree)
    if not paragraphs:
        raise ValueError('No detail paragraphs; preserve for parser review')
    first = paragraphs[0]
    text = plain(first, True)
    marked = first.first(lambda n: n.tag in ('b', 'strong')) is not None
    attribution = PROPHET.search(text)
    issues = []
    if unexpected:
        issues.append('unrecognized_body_structure')
    if not marked or COMMENT_START.match(text):
        issues.append('narration_boundary_not_established')
    if text.rstrip().endswith((':', '：')):
        issues.append('primary_quotation_incomplete_before_following_context')
    if not attribution:
        issues.append('prophetic_attribution_not_established')
    if re.search(r'[\u0600-\u06ff]', text):
        issues.append('mixed_or_unexpected_primary_language_requires_review')
    comments = []
    references = []
    grades = []
    for number, node in enumerate(paragraphs[1:], 2):
        note = plain(node, True)
        role = 'source_commentary'
        if re.match(r'^(?:Бу|Ушбу) ҳадис\b', note, re.I) and re.search(r'саҳиҳ|ҳасан|заиф|ғариб', note, re.I):
            role = 'source_assessment'
            grades.append(note)
        comment = {'text': note, 'language': 'uz-Cyrl', 'kind': role,
                   'source_url': url, 'source_locator': {'paragraph': number}}
        comments.append(comment)
        if re.search(r'Бухорий|Муслим|Абу Довуд|Насоий|Ибн Можа|Термизий', note, re.I):
            references.append({'source_citation': note, 'url': url,
                'scope': 'source_commentary_citation', 'source_language': 'uz-Cyrl',
                'number': None, 'canonical_mapping_status': 'unverified',
                'source_locator': {'paragraph': number}})
        for link_node in node.all(lambda n: n.tag == 'a' and n.attrs.get('href')):
            target = urllib.parse.urljoin(url, link_node.attrs['href'])
            if urllib.parse.urlsplit(target).scheme in ('https', 'http'):
                references.append({'source_citation': plain(link_node) or target,
                    'url': target, 'scope': 'publisher_link_in_source_commentary',
                    'source_language': 'uz-Cyrl', 'canonical_mapping_status': 'unverified',
                    'source_locator': {'paragraph': number}})
    heading = tree.first(lambda n: n.tag == 'h1')
    return {'source_entry_id': urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1],
            'url': url, 'title': plain(heading) or None, 'text': text,
            'comments': comments, 'references': references, 'grades': grades,
            'content_kind': 'prophetic_report' if not issues else 'classification_pending_hidden',
            'classification': {'method': 'publisher_first_narration_paragraph_v1',
                'matched_marker': attribution.group() if attribution else None,
                'issues': issues, 'authenticity_assessed': False},
            'body_paragraphs': [plain(node, True) for node in paragraphs],
            'primary_paragraph': 1, 'unexpected_body_elements': unexpected}


def collection_credit_statements(raw, url, snapshot):
    """Keep observed publisher credit paragraphs verbatim, with their scope.

    These collection introductions identify source editions and resources, not
    a verified translator or canonical identity for every individual entry.
    Only the observed credit paragraph openings select text; complete metadata
    pages, including all other introduction material, remain in the snapshot.
    """
    if not allowed_url(url, 'info') or snapshot.get('url') != url:
        raise ValueError('Collection credit snapshot does not match its source URL')
    tree = source_tree(raw)
    column = tree.first(lambda n: n.has('col-md-9')) or tree.first(lambda n: n.has('main'))
    if column is None:
        raise ValueError('Missing public collection metadata body')
    markers = COLLECTION_CREDIT_MARKERS[urllib.parse.urlsplit(url).path]
    statements = []
    for number, paragraph in enumerate(column.all(lambda n: n.tag == 'p'), 1):
        text = plain(paragraph, True)
        kind = next((name for name, pattern in markers if pattern.match(text)), None)
        if kind is None:
            continue
        links = []
        for node in paragraph.all(lambda n: n.tag == 'a' and n.attrs.get('href')):
            target = urllib.parse.urljoin(url, node.attrs['href'])
            if urllib.parse.urlsplit(target).scheme in ('http', 'https'):
                links.append({'name': plain(node) or target, 'url': target})
        statements.append({'name': text, 'url': url, 'scope': COLLECTION_CREDIT_SCOPE,
            'source_language': 'uz-Cyrl', 'credit_kind': kind, 'cited_links': links,
            'source_locator': {'path': snapshot['path'], 'sha256': snapshot['sha256'],
                'selector': '.col-md-9 p', 'paragraph': number}})
    if not statements:
        raise ValueError('No observed collection credit paragraphs; metadata parser review required')
    return statements


def record_from(parsed, snapshot, credits, credit_statements=None):
    identifier = 'hadisuz:tirmidhi:' + parsed['source_entry_id']
    citation = {'collection': TITLE, 'number': None, 'source_entry_id': parsed['source_entry_id'],
        'source_citation': 'Hadis.uz source entry ' + parsed['source_entry_id'],
        'url': parsed['url'], 'scope': 'source_entry', 'source_language': 'uz-Cyrl',
        'numbering_system': 'Publisher URL database ID; printed and canonical numbers not established',
        'canonical_mapping_status': 'unverified'}
    refs = [citation, *parsed['references']]
    upstream = []
    for credit in credit_statements or []:
        refs.append({'source_citation': credit['name'], 'url': credit['url'],
            'scope': credit['scope'], 'source_language': credit['source_language'],
            'credit_kind': credit['credit_kind'], 'number': None,
            'canonical_mapping_status': 'not_inferred', 'source_locator': credit['source_locator']})
        upstream.append(credit)
        for link in credit['cited_links']:
            upstream.append({**link, 'scope': COLLECTION_CREDIT_SCOPE,
                'credited_by': credit['url'], 'source_locator': credit['source_locator']})
    provenance = {'ai_translation': 'unknown', 'translator': None,
        'basis': 'Exact entry has no translation-origin declaration; current new-book display policy is separate.',
        'evidence': snapshot['path']}
    return {'id': identifier, 'language': 'uz', 'source_language_code': 'uz-Cyrl',
        'book_key': 'tirmidhi', 'edition': EDITION, 'title': parsed['title'],
        'record_type': 'source_narration_occurrence', 'content_kind': parsed['content_kind'],
        'classification': parsed['classification'],
        'text': {'arabic': None, 'translation': parsed['text']},
        'language_versions': [{'id': identifier + ':uz-Cyrl', 'language': 'uz-Cyrl',
            'script': 'Cyrl', 'text': parsed['text'], 'scope': 'source_entry',
            'match_status': 'same_source_record', 'translation_provenance': provenance,
            'source': {'name': 'Hadis.uz', 'url': parsed['url'], 'record_url': parsed['url'],
                'snapshot_path': snapshot['path'], 'snapshot_sha256': snapshot['sha256'],
                'upstream_sources': upstream, 'collection_credit_evidence': credits},
            'references': refs, 'comments': parsed['comments']}],
        'source': {'title': TITLE, 'url': CATALOG, 'record_url': parsed['url'],
            'publisher': 'Hadis.uz', 'collection_credit_evidence': credits,
            'metadata_scope': 'own_entry_with_separately_scoped_collection_credits'},
        'number': {'source_entry_id': parsed['source_entry_id'], 'in_book': None,
            'canonical': None, 'scope': 'publisher_source_local',
            'numbering_system': 'Publisher URL database ID; no canonical equivalence inferred'},
        'references': {'items': refs, 'canonical_mapping_status': 'unverified'},
        'narrator': {'name': None, 'basis': 'Narration attribution retained verbatim.'},
        'translator': {'name': None, 'basis': 'Collection credits are retained separately from this entry.'},
        'ai_translation': 'unknown',
        'translation_provenance': {'origin': 'unknown', 'label': 'Unknown', **provenance},
        'commentary': {'arabic': None, 'translation': None}, 'footnotes': [],
        'grading': {'grade': None, 'grader': None, 'source_assessments': parsed['grades'],
            'basis': 'Exact source paragraphs retained; individual assessor not inferred.'},
        'source_headings': [value for value in (TITLE, parsed['title']) if value], 'topic_tags': [], 'related_versions': [],
        'review': {'status': 'digital_source_import', 'independent_pro_qc': 'not_performed',
            'release_eligible': False, 'certified_release_eligible': False,
            'issues': parsed['classification']['issues']},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None},
        'extraction': {'method': 'public_html_primary_narration_paragraph', 'ocr_used': False,
            'source_snapshot': snapshot['path'], 'original_html_sha256': snapshot['sha256'],
            'is_excerpt': False, 'upstream_transcription_method': None},
        'source_locator': {'path': snapshot['path'], 'sha256': snapshot['sha256'],
            'format': 'gzip_compressed_original_http_html', 'record_url': parsed['url'],
            'selector': '.col-md-9 > p:first-of-type', 'paragraph': 1,
            'text_hashes': {'uz-Cyrl': digest(parsed['text'].encode())}},
        'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None}}


class Importer:
    def __init__(self, root, max_pages=60, max_seconds=600, delay=1.25):
        self.root = Path(root).resolve()
        self.folder = self.root / BASE
        self.folder.mkdir(parents=True, exist_ok=True)
        self.state_path = self.folder / 'checkpoint.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {
            'schema': 'hadith-bank-hadisuz-checkpoint-v1', 'origin': ORIGIN,
            'catalogue': CATALOG, 'tasks': [], 'snapshots': {}, 'entries': {},
            'collection_credits': {}, 'part_assignments': {}, 'events': []}
        if self.state.get('catalogue') != CATALOG:
            raise ValueError('Unexpected checkpoint catalogue')
        plan_path = self.root / 'catalog/web-import-plan.json'
        if plan_path.exists():
            plan = json.loads(plan_path.read_text())
            if plan.get('sources', {}).get('hadisuz', {}).get('excluded_by_owner'):
                raise ValueError('Hadis.uz excluded by owner; acquisition and registration stopped')
        self.max_pages, self.deadline, self.delay = max_pages, time.monotonic() + max_seconds, delay
        self.requests, self.last_request = 0, 0
        self.robot = None
        self.opener = urllib.request.build_opener(PublicRedirects())
        self.enqueue(CATALOG, 'catalog', 'owner_provided_catalogue')

    def save(self):
        atomic(self.state_path, json_bytes(self.state))

    def enqueue(self, url, kind, discovered_on):
        if not allowed_url(url, kind):
            return
        if not any(task['url'] == url for task in self.state['tasks']):
            self.state['tasks'].append({'url': url, 'kind': kind, 'status': 'pending',
                                       'attempts': 0, 'discovered_on': discovered_on})

    def checked(self, descriptor):
        path = self.root / descriptor['path']
        if path.is_symlink() or self.root not in path.resolve().parents:
            raise ValueError('Unsafe stored source path')
        stored = path.read_bytes()
        if digest(stored) != descriptor['stored_sha256']:
            raise ValueError('Stored source checksum mismatch')
        raw = gzip.decompress(stored)
        if digest(raw) != descriptor['sha256']:
            raise ValueError('Original source checksum mismatch')
        return raw

    def preserve(self, raw, url, metadata, kind='html'):
        name = digest(url.encode())[:16] + '-' + digest(raw)[:16] + '.' + kind + '.gz'
        path = self.folder / 'snapshots' / name
        stored = gzip.compress(raw, mtime=0)
        immutable(path, stored)
        return {**metadata, 'url': url, 'path': str(path.relative_to(self.root)),
                'sha256': digest(raw), 'stored_sha256': digest(stored),
                'bytes': len(raw), 'size_bytes': len(stored), 'compression': 'gzip'}

    def fetch(self, url, robots=False):
        if url in self.state['snapshots']:
            descriptor = self.state['snapshots'][url]
            return self.checked(descriptor), descriptor
        if self.state.get('access_block'):
            raise RuntimeError('Prior access block retained; automatic retry prohibited')
        if not allowed_url(url, 'robots' if robots else None):
            raise ValueError('Source URL outside authorized public routes')
        if not robots and (self.robot is None or not self.robot.can_fetch(AGENT, url)):
            raise PermissionError('robots_disallowed: ' + url)
        if self.requests >= self.max_pages or time.monotonic() >= self.deadline:
            raise StopIteration('request_or_time_budget')
        pause = self.delay - (time.monotonic() - self.last_request)
        if pause > 0:
            time.sleep(pause)
        self.requests += 1
        self.last_request = time.monotonic()
        request = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,text/plain'})
        with self.opener.open(request, timeout=40) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError('Response exceeds preservation limit')
            descriptor = self.preserve(raw, url, {'retrieved_at': now(), 'status': response.status,
                'final_url': response.geturl(), 'content_type': response.headers.get('Content-Type')},
                'txt' if robots else 'html')
        self.state['snapshots'][url] = descriptor
        self.save()
        return raw, descriptor

    def error(self, url, error, task=None):
        status = getattr(error, 'code', None)
        event = {'url': url, 'time': now(), 'status': status,
                 'error': type(error).__name__ + ': ' + str(error)[:300]}
        if isinstance(error, urllib.error.HTTPError):
            try:
                body = error.read(MAX_RESPONSE + 1)
                if len(body) <= MAX_RESPONSE:
                    event['response'] = self.preserve(body, url, {'retrieved_at': event['time'], 'status': status}, 'error')
            except OSError as capture_error:
                event['response_capture_error'] = type(capture_error).__name__
        blocked = status in (401, 403, 429) or isinstance(error, PermissionError)
        if blocked:
            self.state['access_block'] = {**event, 'automatic_retry_allowed': False}
        if task is not None:
            task.update({'status': 'blocked' if blocked else 'failed', 'error': event['error']})
            if isinstance(error, ValueError) or status == 404:
                task['attempts'] = 3
        self.state['events'].append(event)
        self.save()

    def process(self, task, raw, snapshot):
        url = task['url']
        if task['kind'] == 'catalog':
            parsed = parse_catalog(raw, url)
            for next_url in parsed['info']:
                self.enqueue(next_url, 'info', url)
            for next_url in parsed['details']:
                self.enqueue(next_url, 'detail', url)
            for next_url in parsed['next']:
                self.enqueue(next_url, 'catalog', url)
            task['discovery'] = parsed
        elif task['kind'] == 'info':
            tree = source_tree(raw)
            column = tree.first(lambda n: n.has('col-md-9')) or tree.first(lambda n: n.has('main'))
            if column is None:
                raise ValueError('Missing public collection metadata body')
            collection_credit_statements(raw, url, snapshot)
            self.state['collection_credits'][url] = {'url': url, 'snapshot': snapshot,
                'text': plain(column, True), 'scope': COLLECTION_CREDIT_SCOPE}
        else:
            parsed = parse_detail(raw, url)
            data = json_bytes(parsed)
            path = self.folder / 'parsed' / (parsed['source_entry_id'] + '-' + digest(data)[:16] + '.json.gz')
            stored = gzip.compress(data, mtime=0)
            immutable(path, stored)
            self.state['entries'][parsed['source_entry_id']] = {
                'path': str(path.relative_to(self.root)), 'sha256': digest(data),
                'stored_sha256': digest(stored), 'size_bytes': len(stored),
                'compression': 'gzip', 'snapshot': snapshot, 'url': url}
        task.update({'status': 'done', 'snapshot': snapshot['path']})
        task.pop('error', None)

    def run(self):
        if self.state.get('access_block'):
            return self.export()
        robots_url = ORIGIN + '/robots.txt'
        if robots_url not in self.state['snapshots'] and self.state.get('robot_attempts', 0) >= 3:
            return self.export()
        attempts = self.state.get('robot_attempts', 0)
        try:
            if robots_url not in self.state['snapshots']:
                self.state['robot_attempts'] = attempts + 1
            raw, _ = self.fetch(robots_url, robots=True)
            self.robot = urllib.robotparser.RobotFileParser()
            self.robot.parse(raw.decode('utf-8', errors='strict').splitlines())
            self.state.pop('robots_error', None)
        except StopIteration:
            self.state['robot_attempts'] = attempts
            return self.export()
        except Exception as error:
            self.state['robots_error'] = type(error).__name__ + ': ' + str(error)[:300]
            self.error(robots_url, error)
            return self.export()
        attempted = set()
        while True:
            task = next((item for item in self.state['tasks'] if item['url'] not in attempted and
                         item['status'] in ('pending', 'failed') and item['attempts'] < 3), None)
            if task is None or self.state.get('access_block'):
                break
            attempted.add(task['url'])
            attempts = task['attempts']
            try:
                task['attempts'] = attempts + 1
                raw, snapshot = self.fetch(task['url'])
                self.process(task, raw, snapshot)
                self.save()
            except StopIteration:
                task['attempts'] = attempts
                break
            except Exception as error:
                self.error(task['url'], error, task)
        return self.export()

    def export(self):
        rows, held, supporting = [], [], {}
        credits = [{'url': item['url'], 'snapshot_path': item['snapshot']['path'],
                    'snapshot_sha256': item['snapshot']['sha256'], 'scope': item['scope']}
                   for item in self.state['collection_credits'].values()]
        credit_statements = []
        for item in self.state['collection_credits'].values():
            # Re-read immutable, checksum-verified HTML even for older checkpoints;
            # a cached plain-text field is not the evidence for visible credits.
            credit_statements.extend(collection_credit_statements(
                self.checked(item['snapshot']), item['url'], item['snapshot']))
        for entry in self.state['entries'].values():
            parsed = json.loads(self.checked(entry))
            self.checked(entry['snapshot'])
            row = record_from(parsed, entry['snapshot'], credits, credit_statements)
            (rows if parsed['content_kind'] == 'prophetic_report' else held).append(row)
        for snapshot in self.state['snapshots'].values():
            self.checked(snapshot)
            supporting[snapshot['path']] = {'path': snapshot['path'],
                'sha256': snapshot['stored_sha256'], 'size_bytes': snapshot['size_bytes'],
                'compression': 'gzip', 'original_response_sha256': snapshot['sha256'],
                'url': snapshot['url']}
        for entry in self.state['entries'].values():
            supporting[entry['path']] = {'path': entry['path'], 'sha256': entry['stored_sha256'],
                'size_bytes': entry['size_bytes'], 'compression': 'gzip',
                'uncompressed_sha256': entry['sha256']}
        active = []
        mapping = self.state['part_assignments']
        groups, sizes = collections.defaultdict(list), collections.Counter()
        for row in sorted(rows, key=lambda r: int(r['number']['source_entry_id'])):
            part = mapping.get(row['id'])
            if part is None:
                continue
            groups[part].append(row)
            sizes[part] += len(row_bytes(row))
        part = max(groups, default=1)
        for row in sorted(rows, key=lambda r: int(r['number']['source_entry_id'])):
            if row['id'] in mapping:
                continue
            size = len(row_bytes(row))
            if size > MAX_PART:
                raise ValueError('One source record exceeds the publication shard limit')
            if sizes[part] + size > MAX_PART:
                part += 1
            mapping[row['id']] = part
            groups[part].append(row)
            sizes[part] += size
        tasks = self.state['tasks']
        report = {'schema': 'hadith-bank-hadisuz-progress-v1', 'site': 'hadisuz',
            'catalogue': CATALOG, 'source_entries_obtained': len(rows) + len(held),
            'prophetic_source_entries_registered': len(rows), 'classification_pending_hidden': len(held),
            'pending_requests': sum(t['status'] == 'pending' for t in tasks),
            'retryable_errors': sum(t['status'] == 'failed' and t['attempts'] < 3 for t in tasks),
            'errors': sum(t['status'] == 'failed' for t in tasks) + bool(self.state.get('robots_error')),
            'startup_stopped': bool(self.state.get('robots_error')) and self.state.get('robot_attempts', 0) >= 3,
            'blocked': bool(self.state.get('access_block')),
            'access_block': self.state.get('access_block'),
            'done': bool(tasks) and all(t['status'] == 'done' for t in tasks) and not self.state.get('access_block'),
            'task_counts': dict(collections.Counter(t['status'] for t in tasks)),
            'complete_content_import_certified': False,
            'scope_note': 'Observed catalogue links only; source occurrences, not deduplicated canonical hadiths. Held classifications and commentary quotations remain separate.'}
        atomic(self.folder / 'held-records.jsonl.gz', gzip.compress(b''.join(row_bytes(r) for r in held), mtime=0))
        for number, part_rows in sorted(groups.items()):
            slug = SLUG if number == 1 else SLUG + '-part-' + str(number).zfill(4)
            folder = self.root / 'materials' / slug
            edition = EDITION if number == 1 else EDITION + '-part-' + str(number).zfill(4)
            for row in part_rows:
                row['edition'] = edition
            data = b''.join(row_bytes(r) for r in sorted(part_rows, key=lambda r: r['id']))
            if len(data) > MAX_PART:
                raise ValueError('Existing publication shard exceeds 40MiB; explicit repartition needed')
            atomic(folder / 'records.jsonl', data)
            evidence = {'schema': 'hadith-bank-hadisuz-source-evidence-v1', 'publisher': 'Hadis.uz',
                'catalogue': CATALOG, 'collection_credits': list(self.state['collection_credits'].values()),
                'entry_snapshots': [self.state['entries'][r['number']['source_entry_id']] for r in part_rows],
                'acquisition': 'Ordinary public HTML; observed catalogue pagination and detail links only',
                'scope': report, 'rights': {'status': 'not_assessed_for_publication'}}
            source_data = json_bytes(evidence)
            atomic(folder / 'source-evidence.json', source_data)
            prefix = str(folder.relative_to(self.root))
            manifest = {'schema': 'hadith-bank-material-v1', 'adapter': 'records-v1',
                'id': slug, 'source_id': slug, 'language': 'uz', 'book': 'tirmidhi', 'edition': edition,
                'records': {'path': prefix + '/records.jsonl', 'sha256': digest(data), 'count': len(part_rows)},
                'source': {'path': prefix + '/source-evidence.json', 'sha256': digest(source_data),
                    'name': TITLE + ' — Hadis.uz', 'format': 'web-source-evidence-json', 'url': CATALOG},
                'publication': {'authorized': True, 'decision': 'owner_requested_public_source_import',
                    'decision_date_japan': '2026-11-12', 'basis': 'Owner explicitly supplied the Hadis.uz Tirmidhi catalogue and requested integration.'},
                'supporting_files': list(supporting.values()), 'extraction_scope': report,
                'counterpart_policy': {'mode': 'disabled', 'reason': 'Only source-bound language versions are displayed; source-local URL IDs do not establish canonical equivalents.'},
                'storage_shard': {'part': number, 'parts': len(groups), 'max_canonical_bytes': MAX_PART,
                    'original_source_edition': EDITION, 'occurrence_ids_unchanged': True}}
            atomic(folder / 'manifest.json', json_bytes(manifest))
            active.append(slug)
        for folder in (self.root / 'materials').glob(SLUG + '*') if (self.root / 'materials').exists() else []:
            if folder.name not in active and folder.is_dir():
                raise ValueError('Stale registered Hadis.uz shard requires explicit review; no automatic deletion')
        atomic(self.folder / 'progress.json', json_bytes(report))
        self.save()
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--max-pages', type=int, default=60)
    parser.add_argument('--max-seconds', type=float, default=600)
    parser.add_argument('--delay', type=float, default=1.25)
    parser.add_argument('--export-only', action='store_true')
    args = parser.parse_args(argv)
    if args.max_pages < 1 or args.max_seconds <= 0 or args.delay < 1:
        parser.error('Positive page/time budgets and delay >=1 second required')
    importer = Importer(args.root, args.max_pages, args.max_seconds, args.delay)
    report = importer.export() if args.export_only else importer.run()
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
