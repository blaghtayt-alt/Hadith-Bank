#!/usr/bin/env python3
"""Extract source-bound narration occurrences from the older bank's digital readers.

This is a deterministic segmentation/import operation, not a new translation or
an authenticity assessment. Original documents, historical metadata, distinct
source versions and the owner's current Unknown-origin decision are preserved.
Run after populating .cache/legacy-extraction-sources from the pinned Git tree,
or rerun using the exact source bundles emitted with each registered material.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil

from legacy_reference_parser import COLLECTIONS, parse_references
from register_material import register

ROOT = Path(__file__).resolve().parents[1]
REPO = 'blaghtayt-alt/iman-companion'
PIN = 'ae2c07599767ee7182c40d3ff2264fcdac98d182'
LANGUAGES = ('ja', 'fil', 'vi', 'zh-CN', 'uz', 'hi', 'fa')
EDITION = 'legacy-embedded-ae2c075-v1'
POLICY = {'classification': 'unknown',
          'basis': 'owner_withheld_confirmation_of_old_bank_copies',
          'decision_date_japan': '2026-11-11',
          'policy_path': 'catalog/provenance-policy.json'}

# These are source-marked typography spans inside linguistic explanation, not
# independently bounded narration occurrences. Keep their text in the source
# bundle and record the exclusion without altering the original lesson.
LESSON_GLOSS_SPANS = {
    ('materials/hadith/essential-fa/003.json', '/blocks/7/parts/1/text'): 'می\u200cگرداند',
    ('materials/hadith/essential-fa/003.json', '/blocks/8/parts/1/text'): 'رحمان',
    ('materials/hadith/essential-fa/003.json', '/blocks/10/parts/3/text'): 'بر',
    ('materials/hadith/essential-uz/003.json', '/blocks/7/parts/1/text'): 'буради',
}

# Additional narrations explicitly quoted inside displayed publisher footnotes.
# These are kept separate from the main quotation and no unsupplied number is
# borrowed from that main quotation's references.
HEART_NOTE_NARRATIONS = {
    ('closeness-02', 'ja', 0): ('アッラーに対して希望的な観測をもつことなしには、この世を去ってはならない。', False),
    ('trust-03', 'ja', 0): ('アッラーに対して希望的な観測をもつことなしには、この世を去ってはならない。', False),
    ('sabr-03', 'vi', 0): ('Người phụ nữ khóc cho đứa con nhỏ của bà', True),
}

EXTRA_WORK_TITLES = {'mishkat-al-masabih': 'Mishkat al-Masabih'}

# Exact source-bounded narrations found in displayed notes and the linked
# published glossary. Historical full-parent evidence is not counted again.
DISPLAYED_NOTE_NARRATIONS = [
    {'path': 'materials/hadith/essential-ja/004.json', 'pointer': '/notes/34/text',
     'text': 'あなたの主*は誰か？あなたの宗教は何か？あなたの預言者*は誰か？'},
    {'path': 'materials/hadith/essential-ja/004.json', 'pointer': '/notes/35/text',
     'text': '偽信者*というものは、二つの羊の群れの間を彷徨（さまよ）う、一頭の羊のようなものである。時にはそちらに行ったり、また別の時にはこちらに行ったりするのだ',
     'narrator': 'イブン・ウマル', 'numbering': 'muslim_book_local_17'},
    {'path': 'materials/hadith/essential-ja/002.json', 'pointer': '/reader/sections/2/notes/0/text',
     'text': 'アッラーよ、心を向けられるお方よ、私たちの心を、あなたに従う方へお向けください。',
     'record_type': 'hadith_meaning_excerpt', 'narrator': 'アブドッラー・イブン・アムル'},
    {'path': 'materials/hadith/essential-ja/002.json', 'pointer': '/reader/sections/10/notes/0/text',
     'text': '王座はかれ（アッラー*）の足台で、御座（みくら）の大きさは際限（さいげん）がない',
     'record_type': 'companion_report_excerpt', 'narrator': 'イブン・アッバース', 'numbering': 'hakim_volume_page'},
    {'path': 'materials/hadith/essential-ja/002.json', 'pointer': '/reader/sections/11/notes/0/text',
     'text': 'アッラーの恵みについて深く考えなさい。アッラーご自身について深く考えてはならない',
     'record_type': 'hadith_meaning_excerpt', 'work': "Al-Mu'jam al-Awsat"},
    {'path': 'materials/hadith/essential-fil/002.json', 'pointer': '/reader/sections/2/notes/0/text',
     'text': 'O Allāh, Tagapagbaling ng mga puso, ibaling Mo ang aming mga puso sa pagsunod sa Iyo.',
     'record_type': 'hadith_meaning_excerpt', 'narrator': '‘Abdullāh ibn ‘Amr'},
    {'path': 'materials/hadith/essential-fil/002.json', 'pointer': '/reader/sections/11/notes/0/text',
     'text': 'Pagnilayan ninyo ang mga biyaya ni Allāh, at huwag ninyong pagnilayan si Allāh mismo.',
     'record_type': 'hadith_meaning_excerpt', 'narrator': 'Ibn ‘Umar', 'work': "Al-Mu'jam al-Awsat"},
    {'path': 'materials/hadith/essential-ja/001.json', 'pointer': '/readers/ja/sourceDependencies/glossaryEntries/4/notes/2',
     'text': '預言者*の数は十二万四千人で、使徒*の数はその内、三一五人', 'numbering': 'mishkat_glossary'},
    {'path': 'materials/hadith/essential-hi/002.json', 'pointer': '/reader/mainNotes/0/text',
     'text': 'मैं ही राजा हूँ।', 'numbering': 'bukhari_note_context'},
    {'path': 'materials/hadith/essential-hi/003.json', 'pointer': '/notes/3/text',
     'text': 'मैं ही राजा हूँ।', 'numbering': 'bukhari_note_context'},
]


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode('utf-8')).hexdigest()


def git_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def escape(value):
    return str(value).replace('~', '~0').replace('/', '~1')


def pointer_get(document, pointer):
    current = document
    for part in pointer.lstrip('/').split('/') if pointer else []:
        part = part.replace('~1', '/').replace('~0', '~')
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def walk(value, pointer=''):
    yield pointer, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, pointer + '/' + escape(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, pointer + '/' + str(index))


def strings(value):
    return [(p, v) for p, v in walk(value) if isinstance(v, str)]


def values(value):
    return value.values() if isinstance(value, dict) else value or []


def adjacent_reference_text(text):
    """Return the first immediately following citation, excluding later prose."""
    found = parse_references(text)
    if not found or found[0]['start'] > 100:
        return None
    start = found[0]['start']
    last = found[0]['end']
    # A closing reference bracket ends the citation even when the following
    # explanation names other reports. Semicolons inside a bracket are retained.
    close = re.search(r'[\])）］】。\n]', text[last:])
    end = last + close.end() if close else last
    return text[start:end]


def refs(text, locator=None, scope='main_quote', allow_unnumbered=True):
    """Transcribe citations with their source string; never identify by number alone."""
    if not isinstance(text, str):
        return []
    result = []
    for item in parse_references(text):
        s = 'variant' if item['scope'] == 'parallel_variant_citation' else scope
        if item['numbering_scheme'] == 'unresolved_volume_page_or_number':
            s = 'unresolved'
        title = item['collection_title']
        if item['collection'] == 'hakim' and not re.search(r'المستدرك|mustadrak', item.get('citation', ''), re.I):
            title = 'Al-Hakim'
        result.append({'book_key': item['collection'], 'collection': title,
                       'number': item['number'], 'scope': s, 'source_citation': text,
                       'citation_code_points': [item['start'], item['end']],
                       'locator': copy.deepcopy(locator),
                       'numbering_scheme': item['numbering_scheme'],
                       'verification': item['verification']})
    if not result and allow_unnumbered:
        # A named collection with no number is useful evidence, not a guessed ID.
        for key, (title, alias) in COLLECTIONS.items():
            match = re.search(alias, text, re.I)
            if match:
                if key == 'hakim' and not re.search(r'المستدرك|mustadrak', text, re.I):
                    title = 'Al-Hakim'
                result.append({'book_key': key, 'collection': title, 'number': None,
                               'scope': scope, 'source_citation': text,
                               'citation_code_points': [match.start(), match.end()],
                               'locator': copy.deepcopy(locator),
                               'numbering_scheme': 'number_not_supplied',
                               'verification': 'collection_named_in_supplied_source'})
    return result


def dedupe_refs(items):
    result, seen = [], set()
    for item in items:
        key = (item['book_key'], item.get('number'), item['scope'])
        if key in seen:
            next(x for x in result if (x['book_key'], x.get('number'), x['scope']) == key).setdefault(
                'additional_evidence', []).append({'source_citation': item['source_citation'],
                                                  'locator': item.get('locator')})
        else:
            result.append(item)
            seen.add(key)
    return result


def origin_history(metadata):
    """Keep historical flags separate from the current owner-set display label."""
    evidence = []
    ai = 'unknown'
    for pointer, value in strings(metadata):
        if any(key in pointer.lower() for key in ['authorship', 'translationmethod', 'translationstatus', 'provenance', 'route']):
            if re.search(r'AI[- ]translated|AI translation|gpt-[0-9]|model[- ]authored', value, re.I):
                ai = True
                evidence.append({'pointer': pointer, 'value': value})
    if isinstance(metadata, dict) and isinstance(metadata.get('ai_translation'), bool):
        ai = metadata['ai_translation']
    return ai, evidence


def selected_parent_person(metadata, role):
    """Read only a named person field explicitly scoped to the selected parent.

    Narrative context, comparison narrations, Quran credits and the source's
    ``narrator_as_published`` collection attribution are not person-name fields.
    A retained translator credit does not change the owner's Unknown-origin
    decision or independently certify the historical metadata.
    """
    parent = metadata.get('selected_parent') or {}
    parent_locator = metadata.get('selected_parent_locator')
    if not isinstance(parent, dict) or not parent_locator:
        return None, None
    paths = {
        'translator': ('/publication/translator', '/publication/translator_as_printed',
                       '/publication/translatorAnnotator', '/metadata/translator',
                       '/metadata/individualTranslator'),
        'narrator': ('/publication/selectedNarrator', '/metadata/narrator'),
    }[role]
    candidates = []
    for pointer in paths:
        try:
            value = pointer_get(parent, pointer)
        except (KeyError, TypeError, IndexError):
            continue
        if (not isinstance(value, str) or not value.strip()
                or re.search(r'\b(?:unknown|not (?:named|identified|supplied|established)|unidentified|unspecified)\b', value, re.I)):
            continue
        locator = copy.deepcopy(parent_locator)
        locator['json_pointer'] += pointer
        candidates.append({'value': value, 'locator': locator,
                           'historical_metadata_pointer': '/selected_parent' + pointer,
                           'basis': 'explicit_selected_parent_person_field'})
    names = {x['value'] for x in candidates}
    if len(names) == 1:
        return candidates[0]['value'], candidates
    # Conflicting names need adjudication; do not arbitrarily choose one.
    return None, candidates or None


class Extractor:
    def __init__(self, root=ROOT, cache=None):
        self.root = Path(root)
        self.cache = Path(cache) if cache else self.root / '.cache/legacy-extraction-sources'
        self.documents = {}
        self.audit = []
        self.records = []
        self.events = []
        self.arabic_banks = {}
        self.aliases = collections.defaultdict(list)

    def add_document(self, path, raw, repository=REPO, revision=PIN, language=None):
        data = raw.decode('utf-8')
        key = repository + ':' + path
        obj = {'repository': repository, 'revision': revision, 'path': path,
               'sha256': sha(raw), 'git_blob_sha': git_sha(raw), 'bytes': len(raw),
               'raw_utf8': data, 'language': language}
        self.documents[key] = obj
        return obj

    def doc(self, path):
        return self.documents[REPO + ':' + path]

    def decoded(self, doc):
        return json.loads(doc['raw_utf8'])

    def locate(self, doc, pointer, bounds=None):
        out = {k: doc[k] for k in ('repository', 'revision', 'path', 'sha256', 'git_blob_sha')}
        out['json_pointer'] = pointer
        if bounds is not None:
            out['code_points'] = list(bounds)
        return out

    def load(self):
        if self.cache.exists():
            for file in sorted(self.cache.glob('materials/**/*.json')):
                path = file.relative_to(self.cache).as_posix()
                if '/heart-reminder/quran/' in path:
                    continue
                lang = self.language_for(path)
                self.add_document(path, file.read_bytes(), language=lang)
        if not self.documents:
            # Source bundles make the import reproducible without cache/network.
            for file in sorted((self.root / 'materials').glob('legacy-*/source-bundle.json')):
                bundle = json.loads(file.read_text(encoding='utf-8'))
                for original in bundle['documents']:
                    raw = original['raw_utf8'].encode('utf-8')
                    assert sha(raw) == original['sha256']
                    assert git_sha(raw) == original['git_blob_sha']
                    self.documents[original['repository'] + ':' + original['path']] = original
        if not self.documents:
            raise ValueError('No pinned source cache or preserved material bundles found')
        catalog = json.loads((self.root / 'catalog/materials.json').read_text(encoding='utf-8'))
        remote_by_hash = collections.defaultdict(list)
        remote_by_json = collections.defaultdict(list)
        for doc in self.documents.values():
            remote_by_hash[doc['sha256']].append(doc)
            if doc['repository'] == REPO:
                remote_by_json[sha(json.dumps(self.decoded(doc), ensure_ascii=False, sort_keys=True))].append(doc)
        for entry in catalog['legacy_materials']:
            path = self.root / entry['path']
            raw = path.read_bytes()
            assert sha(raw) == entry['sha256'], entry['path']
            # Preserved bundles also contain local bank documents. They must not
            # match themselves and hide a semantic mirror on an offline rerun.
            matching = [d for d in remote_by_hash[sha(raw)]
                        if d['repository'] == REPO and d['language'] == entry['language']]
            if matching:
                doc = matching[0]
                self.aliases[doc['repository'] + ':' + doc['path']].append(copy.deepcopy(entry))
                self.audit.append({'path': entry['path'], 'repository': 'Hadith-Bank',
                                   'sha256': sha(raw), 'status': 'exact_byte_mirror',
                                   'canonical_source': doc['path'], 'language': entry['language']})
            else:
                doc = self.add_document(entry['path'], raw, 'Hadith-Bank', entry.get('source_revision'), entry['language'])
                semantic = remote_by_json.get(sha(json.dumps(json.loads(raw), ensure_ascii=False, sort_keys=True)), []) if path.suffix == '.json' else []
                if semantic:
                    match = next((x for x in semantic if x['language'] == entry['language']), None)
                    if match:
                        doc['semantic_mirror_of'] = match['path']
                        self.aliases[match['repository'] + ':' + match['path']].append({**copy.deepcopy(entry), 'mirror_kind': 'identical_parsed_json_different_serialization'})
                self.audit.append({'path': entry['path'], 'repository': 'Hadith-Bank',
                                   'sha256': sha(raw), 'status': 'semantic_mirror' if doc.get('semantic_mirror_of') else 'distinct_legacy_source',
                                   'canonical_source': doc.get('semantic_mirror_of'),
                                   'language': entry['language']})
        ar = self.doc('materials/hadith/ar.json')
        self.arabic_banks = {str(x['id']): (i, x) for i, x in enumerate(self.decoded(ar)['items'])}

    @staticmethod
    def language_for(path):
        m = re.search(r'/essential-([^/]+)/', path)
        if m:
            return m.group(1)
        m = re.search(r'/al-fitnah-al-muntazarah/([^/]+)/', path)
        if m:
            return m.group(1)
        m = re.search(r'/(?:book-publication-readers|source-acceptances)/([^/]+)/', path)
        if m:
            return m.group(1)
        m = re.search(r'/(' + '|'.join(LANGUAGES) + r')\.json$', path)
        if m:
            return m.group(1)
        return None

    def event(self, doc, pointer, status, reason, **extra):
        self.events.append({'source': self.locate(doc, pointer), 'status': status, 'reason': reason, **extra})

    def emit(self, doc, lang, pointer, *, bounds=None, citations=None, title=None,
             arabic=None, arabic_locator=None, narrator=None, footnotes=None,
             metadata=None, context=None, excerpt=False, record_type='hadith',
             related=None, qualification=None, source_entry=None, translator=None):
        raw = pointer_get(self.decoded(doc), pointer)
        assert isinstance(raw, str), (doc['path'], pointer)
        start, end = bounds or (0, len(raw))
        text = raw[start:end]
        assert text and 0 <= start <= end <= len(raw)
        items = dedupe_refs(citations or [])
        primary = next((x for x in items if x['scope'] == 'main_quote' and x.get('number')), None)
        if primary is None:
            primary = next((x for x in items if x['scope'] == 'main_quote'), None)
        book = primary['book_key'] if primary else 'unclassified'
        identity = '|'.join([doc['repository'], doc['path'], doc['sha256'], pointer, str(start), str(end)])
        ident = 'legacy.' + lang + '.' + sha(identity)[:24]
        metadata = copy.deepcopy(metadata or {})
        ai, evidence = origin_history(metadata)
        supplied_narrator, narrator_evidence = selected_parent_person(metadata, 'narrator')
        supplied_translator, translator_evidence = selected_parent_person(metadata, 'translator')
        narrator = narrator or supplied_narrator
        translator = translator or supplied_translator
        if excerpt and record_type in ('hadith', 'companion_report'):
            record_type += '_excerpt'
        source = self.locate(doc, pointer, (start, end))
        source['excerpt_sha256'] = sha(text)
        issues = []
        if not primary or not primary.get('number'):
            issues.append('Canonical collection number is not supplied for this exact selected quote; no number has been inferred.')
        if arabic is None:
            issues.append('An exact source-linked Arabic quote is not available in this extraction; no back-translation was created.')
        if excerpt:
            issues.append('This is a source quotation excerpt, not a claim to contain the complete canonical narration.')
        if qualification:
            issues.extend(qualification if isinstance(qualification, list) else [qualification])
        record = {'id': ident, 'language': lang, 'book_key': book, 'edition': EDITION,
                  'title': title, 'text': {'arabic': arabic, 'translation': text},
                  'record_type': record_type,
                  'content_kind': 'companion_report' if record_type.startswith('companion_report') else 'hadith',
                  'number': {'source_entry_id': source_entry, 'in_book': primary.get('number') if primary else None,
                             'canonical': None, 'numbering_scheme': 'as_cited_in_selected_source'},
                  'narrator': {'name': narrator, 'basis': 'explicit_source_field' if narrator else 'not_supplied',
                               'evidence': narrator_evidence},
                  'translator': {'name': translator, 'evidence': translator_evidence},
                  'source': {'title': title or 'Older Hadith Bank extracted quotation',
                             'url': 'https://github.com/' + REPO + '/blob/' + PIN + '/' + doc['path'] if doc['repository'] == REPO else None,
                             'legacy_document': source,
                             'byte_identical_local_aliases': self.aliases.get(doc['repository'] + ':' + doc['path'], []),
                             'historical_metadata': metadata,
                             'arabic_quote_locator': arabic_locator},
                  'references': {'items': items, 'identity_claim': 'Citations transcribed from supplied source; no independent canonical text equivalence asserted.'},
                  'extraction': {'ocr_used': False, 'method': 'structured_json_quote_extraction',
                                 'source_bounds': source, 'text_sha256': sha(text), 'is_excerpt': bool(excerpt),
                                 'arabic_alignment': 'explicit_source_quote_binding' if arabic is not None else 'not_available'},
                  'footnotes': copy.deepcopy(footnotes or []),
                  'commentary': {'arabic': None, 'translation': context},
                  'related_versions': copy.deepcopy(related or []),
                  'ai_translation': ai,
                  'translation_provenance': {'origin': 'legacy_source_history', 'ai_translation': ai,
                                             'current_policy': copy.deepcopy(POLICY),
                                             'historical_evidence': evidence,
                                             'scope_note': 'Segmentation does not create a new translation. Historical source assertions remain separate from the owner-required Unknown display classification.'},
                  'review': {'status': 'source_bound_structured_extraction', 'issues': issues,
                             'independent_pro_qc': 'not_applicable_to_digital_segmentation',
                             'release_eligible': False, 'certified_release_eligible': False},
                  'rights': {'status': 'historical_source_conditions_preserved',
                             'reuse_basis': 'Owner-authorized inclusion; original source conditions and qualifications remain in the exact source bundle. No new permission is inferred.'}}
        assert not any(r['id'] == ident for r in self.records), ident
        self.records.append(record)
        self.event(doc, pointer, 'extracted', 'Exact supplied narration quotation', record_id=ident, code_points=[start, end])
        return record

    def citation_fields(self, doc, value, base='', scope='main_quote'):
        """Only explicit bibliographic fields, never arbitrary explanation paragraphs."""
        out = []
        keys = {'reference', 'references', 'ref', 'published_attribution', 'source_identity',
                'referenceText', 'original_source_url', 'sourceURL', 'source_url'}
        for pointer, child in strings(value):
            if pointer.rsplit('/', 1)[-1] in keys:
                out += refs(child, self.locate(doc, base + pointer), scope)
        return out

    def generic_bank(self, doc):
        d = self.decoded(doc)
        lang = d['language']
        ardoc = self.doc('materials/hadith/ar.json')
        for i, item in enumerate(d['items']):
            p = '/items/' + str(i)
            citations = refs(item.get('reference'), self.locate(doc, p + '/reference'))
            arabic = arloc = None
            pair = self.arabic_banks.get(str(item.get('id')))
            if pair:
                ai, ar = pair
                source_refs = {(x['book_key'], x['number']) for x in citations if x['number']}
                arrefs = {(x['book_key'], x['number']) for x in refs(ar.get('reference')) if x['number']}
                # Original application entry ID + supplied reference identity is an
                # explicit paired-bank relation, not a free number-only lookup.
                if source_refs and source_refs == arrefs:
                    arabic, arloc = ar['text'], self.locate(ardoc, '/items/' + str(ai) + '/text')
                    arloc['pairing_basis'] = 'same_original_application_entry_id_and_equal_supplied_reference_set'
            self.emit(doc, lang, p + '/text', citations=citations, title=item.get('reference'),
                      arabic=arabic, arabic_locator=arloc, metadata=item,
                      context=item.get('explanation'), excerpt=item.get('isExcerpt', False), source_entry=str(item.get('id')))

    def reader(self, d):
        if isinstance(d.get('reader'), dict):
            return '/reader', d['reader']
        if isinstance(d.get('reading'), dict):
            return '/reading', d['reading']
        if 'readers' in d:
            lang = next(iter(d['readers']))
            return '/readers/' + lang, d['readers'][lang]
        return '', d

    def simple_lesson(self, doc):
        d = self.decoded(doc); lang = doc['language']; base, r = self.reader(d)
        title = r.get('title', d.get('title'))
        notes = {str(n.get('id')): n for n in r.get('notes', []) if isinstance(n, dict)}
        main_id = None
        if isinstance(r.get('main'), str):
            main_pointer = base + '/main'
        else:
            main_pointer = next((base + '/blocks/' + str(i) + '/text' for i, b in enumerate(r.get('blocks', [])) if b.get('kind') in ('main', 'hadith')), None)
        if main_pointer:
            citation = r.get('reference', d.get('reference'))
            items = refs(citation, self.locate(doc, base + '/reference'))
            main_notes = r.get('mainNotes', []) + r.get('referenceNotes', [])
            for note in main_notes:
                if isinstance(note, dict):
                    items += refs(note.get('text'), self.locate(doc, base + '/referenceNotes'), allow_unnumbered=False)
            arabic, aloc = self.main_arabic(doc, d)
            if not any(x.get('number') for x in items) and arabic is not None:
                adoc = self.doc(aloc['path'])
                aref = self.decoded(adoc).get('reference', {}).get('text')
                items += refs(aref, self.locate(adoc, '/reference/text'))
            rec = self.emit(doc, lang, main_pointer, citations=items, title=title,
                            arabic=arabic, arabic_locator=aloc, metadata={k: v for k, v in d.items() if k not in ['reader', 'reading', 'readers', 'blocks']},
                            footnotes=main_notes, source_entry=d.get('id'))
            main_id = rec['id']
        containers = r.get('sections') or r.get('blocks') or []
        container_key = 'sections' if 'sections' in r else 'blocks'
        for i, block in enumerate(containers):
            bp = base + '/' + container_key + '/' + str(i)
            if block.get('kind') in ('main', 'hadith'):
                continue
            block_notes = {**notes, **{str(n.get('id')): n for n in block.get('notes', []) if isinstance(n, dict)}}
            parts = block.get('parts', [])
            for j, part in enumerate(parts):
                pp = bp + '/parts/' + str(j)
                if part.get('kind') != 'hadith':
                    if part.get('kind') == 'quran':
                        self.event(doc, pp, 'excluded', 'Quran verse, not a hadith occurrence')
                    continue
                note_ids = []
                for after in parts[j + 1:]:
                    if after.get('kind') == 'hadith':
                        break
                    if isinstance(after.get('marker'), dict):
                        note_ids.append(str(after['marker'].get('id')))
                selected_notes = [block_notes[n] for n in note_ids if n in block_notes]
                items = []
                for note in selected_notes:
                    items += refs(note.get('text'), self.locate(doc, bp + '/notes'), allow_unnumbered=True)
                # Some formats attach note IDs directly to quotation parts.
                for key in ['reference', 'ref']:
                    if isinstance(part.get(key), str):
                        items += refs(part[key], self.locate(doc, pp + '/' + key))
                if not items:
                    after = parts[j + 1] if j + 1 < len(parts) else {}
                    adjacent = adjacent_reference_text(after.get('text', ''))
                    if adjacent:
                        items += refs(adjacent, self.locate(doc, bp + '/parts/' + str(j + 1) + '/text'))
                quoted = part.get('text', '').strip('「」『』“”«»\" ')
                expected_gloss = LESSON_GLOSS_SPANS.get((doc['path'], pp + '/text'))
                if expected_gloss is not None:
                    assert part.get('text') == expected_gloss, 'Changed source gloss needs re-adjudication'
                    self.event(doc, pp, 'excluded', 'Single-word grammatical or lexical explanation, not an independent narration quote')
                    continue
                if not items and main_id and quoted and quoted in pointer_get(d, main_pointer):
                    main_record = next(x for x in self.records if x['id'] == main_id)
                    items = copy.deepcopy(main_record['references']['items'])
                    for item in items:
                        item['quote_relation'] = 'verbatim_substring_of_same_lesson_main_narration'
                if quoted in {'الرَّحمن', 'الرحمن', 'Раҳмон', 'अर-रहमान', 'رحمن', '慈悲あまねきお方', '全て', 'すべて'}:
                    self.event(doc, pp, 'excluded', 'Single-word commentary gloss, not an independent narration quote')
                    continue
                self.emit(doc, lang, pp + '/text', citations=items, title=title,
                          arabic=part.get('sourceArabic') or part.get('arabic'),
                          arabic_locator=self.locate(doc, pp) if part.get('sourceArabic') or part.get('arabic') else None,
                          footnotes=selected_notes, context=block.get('text'), metadata={'part': part, 'source_notes': selected_notes},
                          excerpt=True, related=[{'relation': 'appears_in_lesson_with', 'id': main_id}] if main_id else [],
                          source_entry=d.get('id'))

    def main_arabic(self, doc, d):
        match = re.search(r'(\d{3})\.json$', doc['path'])
        if not match:
            return None, None
        path = 'materials/hadith/essential-ar/01/' + match.group(1) + '.json'
        adoc = self.documents.get(REPO + ':' + path)
        if not adoc:
            return None, None
        ad = self.decoded(adoc)
        if ad.get('id') != d.get('id'):
            return None, None
        main = ad.get('mainNarration', {}).get('text')
        return main, self.locate(adoc, '/mainNarration/text') if main else None

    def first_lesson(self, doc):
        d = self.decoded(doc); lang = doc['language']; base, reader = self.reader(d)
        prefix = f'materials/hadith/essential-{lang}/sources/'
        bindings = []; parents = {}; extra = {}; identities = {}; register_doc = None
        if lang in ('ja', 'uz'):
            bindings = reader['fieldBindings']
            parents = {p['id']: p for p in reader['sourceParents']}
            parent_base = base + '/sourceParents'
            register_path = prefix + ('HADITH-REFERENCES949.json' if lang == 'ja' else 'HADITH-REFERENCE-REGISTER930.json')
            register_doc = self.doc(register_path); extra = self.decoded(register_doc)
        else:
            carrier_path = prefix + ('SOURCE-CARRIER908.json' if lang == 'fa' else 'SOURCE-CARRIER-TEXT896.json')
            carrier_doc = self.doc(carrier_path); carrier = self.decoded(carrier_doc)
            parents = carrier['parents']; identities = carrier.get('identities', {})
            bound_doc = self.doc(prefix + 'ALL115-EXACT-QUOTE-BOUNDS908.json')
            bindings = self.decoded(bound_doc)
            extra = carrier
        main_pointer = base + ('/main' if lang in ('ja', 'uz') else '/mainNarration/text' if lang == 'fa' else '/main_text')
        main_text = pointer_get(d, main_pointer)
        if lang in ('ja', 'uz'):
            mainbinding = next(b for b in bindings if str(b['fieldId']) == '2')
        else:
            mainbinding = next(b for b in bindings if str(b['field_id']) == '2')['source_binding']
        maincitations, mainmeta = self.first_references(doc, lang, '2', mainbinding, parents, extra, register_doc)
        arabic, arloc = self.main_arabic(doc, d)
        main = self.emit(doc, lang, main_pointer, title=reader.get('title'), citations=maincitations,
                         arabic=arabic, arabic_locator=arloc, metadata=mainmeta,
                         source_entry=d.get('id'))
        main['narrator']['source_context'] = reader.get('main_frame') or reader.get('mainNarration', {}).get('frame') or None
        for i, binding in enumerate(bindings):
            field = str(binding.get('fieldId') or binding.get('field_id'))
            source_binding = binding.get('source_binding', binding)
            kind = str(source_binding.get('kind') or source_binding.get('type') or '').lower()
            if field == '2':
                self.event(doc, main_pointer, 'mirror', 'Main field is already represented by one complete main narration', field_id=field)
                continue
            if 'quran' in kind:
                self.event(doc, base, 'excluded', 'Quran field, not a hadith', field_id=field)
                continue
            if field in ('4', '56'):
                self.event(doc, base, 'excluded', 'Scholar appraisal' if field == '4' else 'One-word gloss nested in a longer quotation', field_id=field)
                continue
            if lang in ('ja', 'uz'):
                locations = binding.get('readingLocations', [])
                # The reader's exact field mapping supplies every genuine occurrence.
                mapped = []
                for loc in locations:
                    if loc['unitPart'] == 'mainNarration':
                        continue
                    bi = next((n for n, b in enumerate(reader['sections']) if b['id'] == loc['unitPart']), None)
                    if bi is not None:
                        mapped.append((base + '/sections/' + str(bi) + '/text', loc['bounds']['codePoints']))
                if not mapped:
                    # Some old UZ bindings use separate part fields without explicit
                    # location arrays; exact typed part values are equally locatable.
                    for bi, b in enumerate(reader['sections']):
                        for pi, part in enumerate(b.get('parts', [])):
                            if str(part.get('field')) == field:
                                mapped.append((base + f'/sections/{bi}/parts/{pi}/text', None))
                ar = binding.get('sourceArabic'); arloc = self.locate(doc, base + '/fieldBindings/' + str(i) + '/sourceArabic') if ar else None
            else:
                container = binding['container']
                if container == 'main':
                    continue
                key = 'commentary' if lang == 'fa' else 'sections'
                bi = next(n for n, b in enumerate(reader[key]) if b['id'] == container)
                mapped = [(base + '/' + key + '/' + str(bi) + '/text', binding['cp'])]
                identity = identities.get(str(source_binding.get('identity')), {}) if lang == 'fa' else next((x for x in extra.get('source_decisions', []) if str(x.get('identity')) == str(source_binding.get('identity'))), {})
                ar = identity.get('sourceArabic')
                arloc = None
                if ar:
                    if lang == 'fa':
                        ar_pointer = '/identities/' + str(source_binding.get('identity')) + '/sourceArabic'
                    else:
                        decision_index = next(n for n, x in enumerate(extra['source_decisions'])
                                              if str(x.get('identity')) == str(source_binding.get('identity')))
                        ar_pointer = f'/source_decisions/{decision_index}/sourceArabic'
                    arloc = self.locate(carrier_doc, ar_pointer)
                    assert pointer_get(self.decoded(carrier_doc), ar_pointer) == ar
                par = parents.get(source_binding.get('parent_id'), {})
                if not ar:
                    ar = par.get('Arabic_source')
                    arloc = self.locate(carrier_doc, '/parents/' + escape(source_binding.get('parent_id')) + '/Arabic_source') if ar else None
            citations, meta = self.first_references(doc, lang, field, source_binding, parents, extra, register_doc)
            for pointer, bounds in mapped:
                text = pointer_get(d, pointer)
                selected = text[slice(*bounds)] if bounds else text
                expected = source_binding.get('text')
                # A source field can intentionally exclude surrounding quote marks;
                # the checked reading span remains the exact emitted string.
                if expected and selected != expected:
                    if expected not in selected:
                        raise ValueError('Source/reading bound mismatch: ' + doc['path'] + ' field ' + field)
                footnotes = []
                for note in reader.get('readerNotes', reader.get('notes', [])):
                    if str(field) in [str(x) for x in note.get('field_ids', note.get('bound_field_ids', []))] or note.get('id') in source_binding.get('reader_note_ids', []):
                        footnotes.append(note)
                warning = None
                if field in ('33', '75', '92'):
                    warning = 'The lesson source records distinguish original Arabic wording and a selected published parallel. The Arabic field is the explicitly linked original lesson excerpt; references retain those separate scopes.'
                self.emit(doc, lang, pointer, bounds=bounds, title=reader.get('title'), citations=citations,
                          arabic=ar, arabic_locator=arloc, metadata=meta, context=text if bounds else None,
                          footnotes=footnotes, excerpt=True, qualification=warning,
                          record_type='companion_report' if field == '80' else 'hadith',
                          related=[{'relation': 'excerpt_in_lesson', 'id': main['id'], 'source_field_id': field}], source_entry=field)

    def first_references(self, doc, lang, field, binding, parents, extra, register_doc):
        pid = binding.get('parentId', binding.get('parent_id'))
        parent = parents.get(pid, {})
        items = []
        meta = {'source_field_id': field, 'source_binding': copy.deepcopy(binding),
                'selected_parent_id': pid, 'selected_parent': copy.deepcopy(parent)}
        if lang in ('ja', 'uz'):
            reader_base, reader = self.reader(self.decoded(doc))
            parent_index = next((i for i, p in enumerate(reader.get('sourceParents', [])) if p.get('id') == pid), None)
            if parent_index is not None:
                meta['selected_parent_locator'] = self.locate(doc, reader_base + f'/sourceParents/{parent_index}')
        else:
            parent_doc = self.doc(f'materials/hadith/essential-{lang}/sources/' +
                                 ('SOURCE-CARRIER908.json' if lang == 'fa' else 'SOURCE-CARRIER-TEXT896.json'))
            if pid in self.decoded(parent_doc).get('parents', {}):
                meta['selected_parent_locator'] = self.locate(parent_doc, '/parents/' + escape(pid))
        if lang == 'ja':
            found = next(((i, x) for i, x in enumerate(extra['entries']) if str(x.get('fieldId')) == field), None)
            if found:
                i, entry = found; meta['reference_register_entry'] = entry
                for key in ('sourceURL',):
                    items += refs(entry.get(key), self.locate(register_doc, f'/entries/{i}/{key}'))
                grade = entry.get('gradeFindings', {})
                if not items:
                    for p, s in strings(grade):
                        items += refs(s, self.locate(register_doc, f'/entries/{i}/gradeFindings' + p), allow_unnumbered=False)
                items += refs(entry.get('actualSpeakerAndVariant'), self.locate(register_doc, f'/entries/{i}/actualSpeakerAndVariant'), 'variant', allow_unnumbered=False)
        elif lang == 'uz':
            match_ids = {'2': 'main', **{str(x): '66–68' for x in (66, 67, 68)}, **{str(x): '79–81' for x in (79, 80, 81)}}
            wanted = match_ids.get(field, field)
            found = next(((i, x) for i, x in enumerate(extra['entries']) if str(x.get('identity')) == wanted), None)
            if found:
                i, entry = found; meta['reference_register_entry'] = entry
                items += refs(entry['note'], self.locate(register_doc, f'/entries/{i}/note'))
        else:
            carrier_doc = self.doc(f'materials/hadith/essential-{lang}/sources/' + ('SOURCE-CARRIER908.json' if lang == 'fa' else 'SOURCE-CARRIER-TEXT896.json'))
            pp = '/parents/' + escape(pid)
            items += self.citation_fields(carrier_doc, parent, pp)
            for k in ['full_notes', 'full_translation', 'text']:
                if k in parent:
                    for p, s in strings(parent[k]):
                        items += refs(s, self.locate(carrier_doc, pp + '/' + k + p), allow_unnumbered=False)
            decisions = extra.get('source_decisions', extra.get('identities', {}))
            decision = next((x for x in values(decisions) if str(x.get('identity', x.get('id'))) == str(binding.get('identity'))), None)
            if decision:
                meta['identity_history'] = decision
        # Main-derived excerpts are explicitly bound to the same main source parent.
        main_fields = {'2', '5', '6', '28', '37', '38', '39', '54', '55', '82', '96'}
        if field in main_fields and not any(x.get('number') for x in items):
            adoc = self.doc('materials/hadith/essential-ar/01/001.json')
            reference = self.decoded(adoc)['reference']['text']
            items += refs(reference, self.locate(adoc, '/reference/text'))
        # Preserve actual target-source bibliographic numbering in the documented
        # exceptional parallel cases; never silently replace it with the original.
        overrides = {
            ('ja', '75'): [('ahmad', '13939')], ('ja', '92'): [('muslim', '993')],
            ('ja', '95'): [('muslim', '2679a')], ('ja', '83'): [('muslim', '2246')],
            ('ja', '33'): [('bukhari', '2447'), ('ahmad', '5798')],
            ('uz', '33'): [('muslim', '2578')], ('uz', '75'): [('muslim', '2675d')],
            ('uz', '92'): [('bukhari', '7419')], ('uz', '95'): [('muslim', '2679a')],
            ('hi', '75'): [('tirmidhi', '2388')], ('hi', '92'): [('bukhari', '4684')],
            ('hi', '95'): [('muslim', '2679')],
            ('fa', '75'): [('muslim', '2675')], ('fa', '92'): [('bukhari', '4684'), ('muslim', '993')],
            ('fa', '95'): [('muslim', '2679')],
        }
        target = overrides.get((lang, field))
        if target:
            # Every asserted override must occur as an explicit citation somewhere
            # inside this field's own complete parent/register evidence.
            candidates = []
            for p, s in strings(meta):
                candidates += refs(s, {'source_document': doc['path'], 'metadata_pointer': p}, allow_unnumbered=False)
            new = []
            for book, number in target:
                match = next((x for x in candidates if x['book_key'] == book and x['number'] == number), None)
                if match:
                    match = copy.deepcopy(match); match['scope'] = 'main_quote'; new.append(match)
            if new:
                for x in items:
                    if (x['book_key'], x.get('number')) not in target:
                        x['scope'] = 'variant'
                items = new + items
        if lang in ('hi', 'fa') and field == '33':
            # The selected Jabir/HadeethEnc5787 parent names Muslim but gives no
            # explicit numbering here; do not borrow Ibn Umar's original number.
            for x in items:
                x['scope'] = 'variant'
            attribution = parent.get('published_attribution') or parent.get('api_full_object', {}).get('attribution') or 'Muslim'
            items.insert(0, {'book_key': 'muslim', 'collection': COLLECTIONS['muslim'][0], 'number': None,
                             'scope': 'main_quote', 'source_citation': attribution,
                             'locator': {'source_document': doc['path'], 'parent_id': pid},
                             'numbering_scheme': 'number_not_supplied', 'verification': 'selected_parent_attribution'})
        if lang == 'uz' and field in ('74', '79', '80', '81'):
            for x in items:
                x['scope'] = 'variant'
            book = 'hakim' if field in ('79', '80', '81') else 'ahmad'
            note = meta.get('reference_register_entry', {}).get('note', '')
            items.insert(0, {'book_key': book, 'collection': 'Al-Hakim' if book == 'hakim' else COLLECTIONS[book][0], 'number': None,
                             'scope': 'main_quote', 'source_citation': note,
                             'locator': self.locate(register_doc, '/entries'), 'numbering_scheme': 'number_not_supplied',
                             'verification': 'selected_publisher_names_collection_without_number'})
        return items, meta

    def filipino005(self, doc):
        d = self.decoded(doc); body = d['reader']
        # Audited exact code-point spans, avoiding Quran, commentary, and nested
        # dialogue within the initial complete narration. Source hash is pinned.
        spans = [(66, 1224, 1225, 1240), (1967, 2027, 2028, 2074),
                 (2098, 2140, 2141, 2256), (2405, 2491, 2492, 2504),
                 (3296, 3322, 3323, 3388), (6557, 6666, 6667, 6682),
                 (6708, 6798, 6799, 6845), (18949, 19018, 19066, 19167),
                 (19339, 19391, 19392, 19438)]
        for i, (a, b, ca, cb) in enumerate(spans):
            citation = body[ca:cb]
            items = refs(citation, self.locate(doc, '/reader', (ca, cb)))
            if i == 2:
                for item in items:
                    item['scope'] = 'variant'
            arabic, arloc = self.main_arabic(doc, d) if i == 0 else (None, None)
            self.emit(doc, 'fil', '/reader', bounds=(a, b), citations=items, title=d.get('title'),
                      arabic=arabic, arabic_locator=arloc, excerpt=i != 0,
                      metadata={'source_citation': citation, 'quran_spans_retained_in_original': True},
                      qualification='The target quotes Ang mga Saligan ng Pananampalataya, item34. Ahmad19876 is explicitly a separate comparison, not an asserted direct identity.' if i == 2 else None,
                      source_entry=d.get('id'))
        self.event(doc, '/reader', 'excluded', 'Quran passages, scholarly appraisals and commentary remain in original document; nine independently bounded narration quotes extracted')

    def heart(self, doc):
        d = self.decoded(doc); r = d['reading']; lang = d['language']; topic = doc['path'].split('/')[-2]
        items = refs(r.get('reader_credit'), self.locate(doc, '/reading/reader_credit'))
        evidence = []
        prefix = 'materials/hadith/heart-reminder/' + topic + '/sources/'
        for other in self.documents.values():
            if other['path'].startswith(prefix) and 'QURAN' not in other['path']:
                od = self.decoded(other)
                # The complete source carrier's protected Arabic parent is the
                # source paired to this card, not arbitrary hints/parallel reports.
                for key, val in od.items():
                    if isinstance(val, dict) and ('protected' in key.lower() or key == 'actual_primary'):
                        for rk in ('reference', 'references'):
                            if isinstance(val.get(rk), str):
                                items += refs(val[rk], self.locate(other, '/' + escape(key) + '/' + rk))
                evidence.append({'source': self.locate(other, ''), 'metadata': od})
        notes = r.get('required_published_notes', r.get('published_meaning_notes', []))
        if not isinstance(notes, list):
            notes = [notes]
        context = r.get('narrator_context') or r.get('narrator_note')
        quote_key = 'hadith' if 'hadith' in r else 'hadith_excerpts' if 'hadith_excerpts' in r else 'quoted_sections'
        q = r.get(quote_key)
        if isinstance(q, str):
            pointers = [('/reading/' + quote_key, None)]
        elif isinstance(q, list):
            pointers = []
            for i, part in enumerate(q):
                if isinstance(part, str):
                    pointers.append(('/reading/' + quote_key + '/' + str(i), None))
                elif isinstance(part, dict):
                    # Explicit source sections are kept separate; no invented
                    # punctuation or fusion across narrator/variant boundaries.
                    for key in ('text', 'quote', 'hadith'):
                        if isinstance(part.get(key), str):
                            pointers.append(('/reading/' + quote_key + '/' + str(i) + '/' + key, part)); break
        else:
            self.event(doc, '/reading', 'unresolved', 'No recognized narration quote field')
            return
        parent_ids = []
        for pointer, part in pointers:
            section_items = copy.deepcopy(items)
            if part:
                section_items = refs(part.get('reference') or part.get('credit'), self.locate(doc, pointer.rsplit('/', 1)[0])) + section_items
            rec = self.emit(doc, lang, pointer, citations=section_items, title=r.get('title'),
                      footnotes=notes,
                      metadata={'reader_metadata': {k: v for k, v in r.items() if k not in ['hadith', 'hadith_excerpts', 'quoted_sections']},
                                'source_metadata': {k: v for k, v in d.items() if k != 'reading'},
                                'source_carrier_links': [x['source'] for x in evidence], 'section_metadata': part},
                      excerpt=quote_key != 'hadith' or len(pointers) > 1,
                      source_entry=d.get('contentId'),
                      qualification='This source card supplies separately bounded quoted sections. Each is an occurrence/excerpt, not an additional claim of a distinct canonical hadith.' if len(pointers) > 1 else None)
            parent_ids.append(rec['id'])
        notes_key = 'required_published_notes' if 'required_published_notes' in r else 'published_meaning_notes'
        for i, note in enumerate(notes):
            note_text = note.get('text') if isinstance(note, dict) else note
            if not isinstance(note_text, str):
                continue
            note_pointer = f'/reading/{notes_key}/{i}' + ('/text' if isinstance(note, dict) else '')
            chosen = HEART_NOTE_NARRATIONS.get((topic, lang, i))
            if chosen:
                selected, is_variant = chosen
                assert note_text.count(selected) == 1, (doc['path'], note_pointer)
                start = note_text.index(selected)
                citation_items = refs(note_text, self.locate(doc, note_pointer))
                assert any(item['book_key'] == 'muslim' for item in citation_items)
                self.emit(doc, lang, note_pointer, bounds=(start, start + len(selected)),
                          citations=citation_items, title=r.get('title'), context=note_text,
                          metadata={'publisher_note': note, 'note_role': 'additional_variant_wording' if is_variant else 'separately_quoted_hadith'},
                          excerpt=True, source_entry=d.get('contentId'),
                          related=[{'relation': 'variant_quoted_in_source_note' if is_variant else 'hadith_quoted_in_source_note', 'id': ident} for ident in parent_ids],
                          qualification='Publisher footnote quotes this narration separately. The source names Sahih Muslim without supplying a number for this precise quotation; no main-record number is inherited.')
            elif re.search(r'「[^「」]+」|“[^“”]+”|«[^«»]+»', note_text):
                self.event(doc, note_pointer, 'excluded',
                           'Displayed note explains a word or phrase from the main quotation; no separately attributed narration.')

    def article(self, doc):
        d = self.decoded(doc); lang = doc['language']
        for i, p in enumerate(d.get('paragraphs', [])):
            base = '/paragraphs/' + str(i)
            quote = p.get('quotation')
            if isinstance(quote, dict) and 'companion' in str(quote.get('kind')).lower():
                self.emit(doc, lang, base + '/quotation/text', citations=refs(p.get('reference'), self.locate(doc, base + '/reference')) + refs(quote.get('sourceURL'), self.locate(doc, base + '/quotation/sourceURL')),
                          title=d.get('title'), arabic=quote.get('sourceArabic'), arabic_locator=self.locate(doc, base + '/quotation/sourceArabic'),
                          narrator='عبد الرحمن بن عوف', record_type='companion_report', excerpt=True,
                          metadata={'paragraph': p, 'original_article_provenance': {k: v for k, v in d.items() if k != 'paragraphs'}},
                          footnotes=p.get('sourceRecordNotes', []), context=p.get('commentary'), source_entry='C2464',
                          qualification='Companion statement, not a saying attributed to the Prophet. Tirmidhi and Darussalam grades remain separately attributed in the preserved source.')
                return
        # JA/FA/HI/ZH final readers have segment arrays; their exact public source
        # binding supplies the quote and the original Arabic in one linked object.
        folder = doc['path'].rsplit('/', 1)[0] + '/'
        for other in self.documents.values():
            if other['path'].startswith(folder) and 'SOURCE' in other['path']:
                od = self.decoded(other)
                for i, binding in enumerate(od.get('bindings', [])):
                    if 'companion' not in str(binding.get('kind')).lower():
                        continue
                    text = binding['text']
                    matches = [(p, s) for p, s in strings(d.get('paragraphs', [])) if s == text and p.endswith('/text')]
                    if matches:
                        pointer = '/paragraphs' + matches[0][0]; src = doc
                    else:
                        pointer = '/bindings/' + str(i) + '/text'; src = other
                    parent = next(x for x in od['fullSelectedParents'] if x['key'] == binding['parentKey'])
                    citations = refs(parent.get('sourceURL'), self.locate(other, '/fullSelectedParents'))
                    self.emit(src, lang, pointer, citations=citations, title=d.get('title'),
                              arabic=binding.get('sourceArabic'), arabic_locator=self.locate(other, '/bindings/' + str(i) + '/sourceArabic'),
                              narrator=parent.get('speaker'), record_type='companion_report', excerpt=True,
                              metadata={'binding': binding, 'selected_parent': parent, 'historical_provenance': d.get('provenance')},
                              footnotes=od.get('requiredNotes', []), source_entry=binding['id'],
                              qualification='Companion statement, not a saying attributed to the Prophet. Original Tirmidhi hasan and separate Darussalam daif assessments are retained without a new grading claim.')
                    return
        self.event(doc, '/paragraphs', 'unresolved', 'Article has no recognized Companion quote binding')

    def displayed_note_excerpts(self):
        for selection in DISPLAYED_NOTE_NARRATIONS:
            doc = self.doc(selection['path'])
            pointer, selected = selection['pointer'], selection['text']
            text = pointer_get(self.decoded(doc), pointer)
            assert isinstance(text, str) and text.count(selected) == 1, selection
            start = text.index(selected)
            locator = self.locate(doc, pointer)
            citations = refs(text, locator)
            numbering = selection.get('numbering')
            qualification = ['This narration is quoted inside a displayed publisher note or linked published glossary; the complete note remains source context.']
            if numbering == 'muslim_book_local_17':
                citations = [item for item in citations if item['book_key'] == 'muslim']
                assert len(citations) == 1 and citations[0]['number'] == '17'
                citations[0].update(numbering_scheme='number_within_source_named_book',
                                    source_book_title='偽信者*の特徴の書')
                qualification.append('The printed 17 is within the named Book of the Characteristics of the Hypocrites; no global Sahih Muslim number is inferred.')
            elif numbering == 'hakim_volume_page':
                assert 'アル=ハキーム2：338' in text
                citations = [{'book_key': 'hakim', 'collection': 'Al-Hakim', 'work_title': None,
                              'number': None, 'volume': '2', 'page': '338', 'scope': 'main_quote',
                              'source_citation': text, 'locator': locator,
                              'numbering_scheme': 'source_volume_page_not_hadith_number',
                              'verification': 'explicit_source_author_and_volume_page'}]
                qualification.append('Al-Hakim is cited as author with volume 2, page 338. This source note does not establish an exact work title or hadith number.')
            elif numbering == 'mishkat_glossary':
                assert 'アッ＝タブリーズィー' in text and '灯火（ともしび）の壁龕（へきがん）' in text and '（5737）' in text
                citations = [{'book_key': 'mishkat-al-masabih', 'collection': 'Mishkat al-Masabih',
                              'work_title_as_cited': '灯火（ともしび）の壁龕（へきがん）',
                              'author_as_cited': 'アッ＝タブリーズィー', 'number': '5737', 'scope': 'main_quote',
                              'source_citation': text, 'locator': locator,
                              'numbering_scheme': 'as_cited_in_source_glossary',
                              'verification': 'source_glossary_attribution_not_independent_canonical_alignment'}]
                qualification.append('The glossary attributes an al-Albani assessment to this count report. The preceding weak-report comment concerns another report; no new authenticity assessment is made.')
            elif numbering == 'bukhari_note_context':
                assert '4812, 6519, 7382, 7413' in text
                citations = [{'book_key': 'bukhari', 'collection': 'Sahih al-Bukhari', 'number': None,
                              'scope': 'main_quote', 'source_citation': text, 'locator': locator,
                              'numbering_scheme': 'precise_fragment_number_not_supplied',
                              'verification': 'collection_explicit_in_same_publisher_note'}]
                citations += [{'book_key': 'bukhari', 'collection': 'Sahih al-Bukhari', 'number': value,
                               'scope': 'source_note_context', 'source_citation': text, 'locator': locator,
                               'numbering_scheme': 'source_note_citation_list',
                               'verification': 'four_references_cite_surrounding_note_not_individually_aligned_to_fragment'}
                              for value in ('4812', '6519', '7382', '7413')]
                qualification.append('The publisher cites four Bukhari references for the surrounding note. This short fragment is not independently assigned to one number.')
            if selection.get('work'):
                citations = [item for item in citations if item['book_key'] == 'tabarani']
                # The Filipino text spells the author with combining marks.
                # Its explicit source work title and numeral are sufficient to
                # transcribe this citation when the common parser misses it.
                if not any(item.get('number') == '6319' for item in citations):
                    assert '6319' in text and ('Awsaṭ' in text or '中伝承集' in text)
                    citations = [{'book_key': 'tabarani', 'collection': 'Al-Tabarani', 'number': '6319',
                                  'scope': 'main_quote', 'source_citation': text, 'locator': locator,
                                  'numbering_scheme': 'as_cited_in_source',
                                  'verification': 'explicit_source_work_and_number'}]
                for item in citations:
                    item['work_title'] = selection['work']
            assert citations, (doc['path'], pointer, 'missing source citation')
            record = self.emit(doc, doc['language'], pointer, bounds=(start, start + len(selected)),
                               citations=citations, title='Narration quoted in a source note',
                               metadata={'source_note': text, 'selection': copy.deepcopy(selection)},
                               context=text, excerpt=True,
                               record_type=selection.get('record_type', 'hadith_excerpt'),
                               source_entry=pointer, qualification=qualification)
            if numbering in ('muslim_book_local_17', 'hakim_volume_page', 'bukhari_note_context'):
                record['number']['numbering_scheme'] = citations[0]['numbering_scheme']
            if selection.get('narrator'):
                name = selection['narrator']
                assert text.count(name) == 1
                at = text.index(name)
                record['narrator'] = {'name': name, 'basis': 'explicit_attribution_in_same_source_note',
                                     'evidence': [{'value': name, 'locator': self.locate(doc, pointer, (at, at + len(name)))}]}
            if numbering == 'mishkat_glossary':
                record['grading'] = {'assessments': [{'grade_as_cited': '真正*', 'grader_as_cited': 'アル＝アルバーニー',
                                    'scope': 'selected_prophet_and_messenger_count_report_only',
                                    'source_citation': text, 'source_locator': locator,
                                    'independent_verification': False}]}

    def run(self):
        self.load()
        for key, doc in sorted(self.documents.items()):
            path = doc['path']
            if doc.get('semantic_mirror_of'):
                status = 'semantic_mirror'
            elif '/book-publication-readers/ja/hadith/' in path:
                original = self.doc('materials/hadith/essential-ja/001.json')
                source = self.decoded(original)['readers']['ja']
                projection = self.decoded(doc)
                assert any(x['path'] == original['path'] and x['sha256'] == original['sha256'] for x in projection['inputBindings'])
                displayed = [s for _, s in strings(projection['sections'][0])]
                assert source['main'] in displayed
                assert all(any(b['text'] in s for s in displayed) for b in source['fieldBindings'])
                status = 'normalization_mirror_all_115_source_fields_verified'
            elif doc['language'] not in LANGUAGES:
                status = 'source_evidence'
            elif re.fullmatch(r'materials/hadith/(?:fa|hi|zh-CN)\.json', path):
                self.generic_bank(doc); status = 'extracted_reader'
            elif (re.search(r'/essential-[^/]+/\d{3}\.json$', path) or re.search(r'/books/essential/editions/[^/]+/\d{3}\.json$', path)):
                if path.endswith('/001.json'):
                    self.first_lesson(doc)
                elif path.endswith('/005.json'):
                    self.filipino005(doc)
                else:
                    self.simple_lesson(doc)
                status = 'extracted_reader'
            elif re.search(r'/heart-reminder/[^/]+/(?:ja|fil|vi|uz)\.json$', path) and '/quran/' not in path:
                self.heart(doc); status = 'extracted_reader'
            elif '/al-fitnah-al-muntazarah/' in path and ('FINAL' in path or 'READING' in path) and 'SOURCE' not in path:
                self.article(doc); status = 'extracted_reader'
            elif path.endswith(('.md', '.txt')):
                status = 'rendering_mirror'
            else:
                status = 'source_evidence'
            self.audit.append({'repository': doc['repository'], 'path': path, 'sha256': doc['sha256'],
                               'language': doc['language'], 'status': status,
                               'extracted_occurrences': sum(1 for r in self.records if r['source']['legacy_document']['repository'] == doc['repository'] and r['source']['legacy_document']['path'] == path)})
        self.displayed_note_excerpts()
        self.save()

    def bundle(self, lang):
        docs = [d for d in self.documents.values() if d['language'] == lang or d['language'] is None or d['language'] == 'ar']
        return {'schema': 'hadith-bank-exact-source-bundle-v1', 'source_repository': REPO,
                'pinned_revision': PIN, 'language': lang,
                'preservation': 'raw_utf8.encode("utf-8") reconstructs each original byte-for-byte, including CRLF; sha256 and Git blob SHA are checked.',
                'documents': sorted(docs, key=lambda d: (d['repository'], d['path'])),
                'local_byte_identical_aliases': dict(self.aliases)}

    def save(self):
        groups = collections.defaultdict(list)
        for rec in self.records:
            groups[(rec['language'], rec['book_key'])].append(rec)
        expected_slugs = {f'legacy-{lang}-{book}' for lang, book in groups}
        for folder in (self.root / 'materials').glob('legacy-*'):
            manifest = folder / 'manifest.json'
            if folder.name not in expected_slugs and manifest.exists():
                old = json.loads(manifest.read_text(encoding='utf-8'))
                if old.get('edition') == EDITION:
                    shutil.rmtree(folder)
        materials = []
        bundles = {lang: self.bundle(lang) for lang in sorted({x[0] for x in groups})}
        for (lang, book), rows in sorted(groups.items()):
            slug = f'legacy-{lang}-{book}'
            folder = self.root / 'materials' / slug
            write_json(folder / 'records.json', rows)
            write_json(folder / 'source-bundle.json', bundles[lang])
            result = register(self.root, 'materials/' + slug, lang, book, EDITION,
                              'Older Hadith Bank — ' + lang + ' — ' + ('Al-Hakim' if book == 'hakim' else EXTRA_WORK_TITLES.get(book, COLLECTIONS.get(book, ('Unclassified source citations',))[0])),
                              'records.json', 'source-bundle.json',
                              source_url='https://github.com/' + REPO + '/tree/' + PIN,
                              identifier=slug, source_id=slug, replace=(folder / 'manifest.json').exists())
            materials.append(result)
        unresolved = [{'id': r['id'], 'language': r['language'], 'source': r['source']['legacy_document'],
                       'issues': r['review']['issues']} for r in self.records if r['number']['in_book'] is None]
        report = {'schema': 'hadith-bank-legacy-extraction-audit-v1', 'source_repository': REPO, 'source_pin': PIN,
                  'count_unit': 'source quotation occurrence; excerpts, source revisions and Companion reports remain distinct; not a count of unique canonical hadiths',
                  'records': len(self.records), 'by_language': dict(collections.Counter(r['language'] for r in self.records)),
                  'by_collection': dict(collections.Counter(r['book_key'] for r in self.records)),
                  'by_type': dict(collections.Counter(r['record_type'] for r in self.records)),
                  'with_source_linked_arabic': sum(r['text']['arabic'] is not None for r in self.records),
                  'with_cited_number': sum(r['number']['in_book'] is not None for r in self.records),
                  'with_explicit_narrator_name': sum(r['narrator']['name'] is not None for r in self.records),
                  'with_explicit_translator_credit': sum(r['translator']['name'] is not None for r in self.records),
                  'excerpt_occurrences': sum(r['extraction']['is_excerpt'] for r in self.records),
                  'translation_display': 'Unknown for every imported legacy occurrence; source historical flags preserved',
                  'ocr_used': False, 'materials': materials,
                  'source_coverage': self.audit, 'quote_decisions': self.events,
                  'unresolved_numbered_attributions': unresolved,
                  'exclusions': ['Quran verses (Quran-book hadith extraction is a separate registered import)',
                                 'Scholar appraisals, commentary and one-word glosses',
                                 'JSON/Markdown/TXT rendering mirrors of the same occurrence',
                                 'Iman test-fixtures and automation-test-material articles'],
                  'independent_authenticity_or_translation_certification_claimed': False}
        write_json(self.root / 'reports/legacy-extraction-audit.json', report)
        print(json.dumps({k: report[k] for k in ['records', 'by_language', 'by_collection', 'by_type', 'with_source_linked_arabic', 'with_cited_number', 'excerpt_occurrences']}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--source-cache', type=Path)
    args = parser.parse_args()
    Extractor(args.root, args.source_cache).run()


if __name__ == '__main__':
    main()
