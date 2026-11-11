#!/usr/bin/env python3
"""Extract source-bounded Hadith occurrences from pinned Quran-study materials.

No translation, paraphrase, canonical-number inference, or OCR is performed.
The deliberately small source-specific selectors are backed by preserved source
bytes. Published explanation, narrative summaries, Quran verses, and proverbs
are accounted for in the coverage ledger rather than promoted to narrations.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from legacy_reference_parser import COLLECTIONS, parse_references


PIN = 'ae2c07599767ee7182c40d3ff2264fcdac98d182'
REPOSITORY = 'blaghtayt-alt/iman-companion'
LANGUAGES = ('ja', 'fil', 'vi', 'zh-CN', 'uz', 'hi', 'fa')
LANGUAGE_NAMES = {'ja': 'Japanese', 'fil': 'Filipino', 'vi': 'Vietnamese',
                  'zh-CN': 'Simplified Chinese', 'uz': 'Uzbek', 'hi': 'Hindi', 'fa': 'Persian'}
TITLES = {k: v[0] for k, v in COLLECTIONS.items()}
TITLES.update({'adab-al-mufrad': 'Al-Adab al-Mufrad', 'riyad-as-salihin': 'Riyad as-Salihin',
               'hisn-al-muslim': 'Hisn al-Muslim', 'unclassified': 'Unresolved collection'})
EDITION = 'iman-quran-excerpts-ae2c075'
FATIHA = 'materials/tadabbur/fatiha-extended'
IKHLAS = 'materials/tadabbur/sources/112'
QIYAMAH = 'materials/tadabbur/ja/extended/075-sources'
HEART = 'materials/hadith/heart-reminder/quran'
TYPE_LABELS = {'hadith_excerpt': 'Hadith excerpt',
               'hadith_meaning_excerpt': 'Hadith meaning excerpt',
               'companion_report_excerpt': 'Companion report excerpt'}

# These choices are indexes of the explicitly printed quotations in their
# source paragraphs, not guessed offsets or generated translations.
FATIHA_QUOTE_INDEX = {
    'H27': 1, 'H28': 2, 'H29': 0, 'H0': 0, 'H1': 0, 'H2': 1, 'H3': 3,
    'H4': 0, 'H5': 0, 'H6': 1, 'H7': 0, 'H8': 0, 'H9': 0, 'H10': 1,
    'H11': 2, 'H12': 0, 'H13': 2, 'H14': 2, 'H15': 0, 'H16': 0,
    'H17': 3, 'H18': 0, 'H19': 1, 'H20': 0, 'H21': 1, 'H22': 0,
    'H23': 0, 'H24': 1, 'H25': 0, 'H26': 0,
}
FATIHA_FIL_INDEX = dict(FATIHA_QUOTE_INDEX, H27=0, H13=1, H14=1, H17=2)
JA_FATIHA_MEANINGS = {'H27','H28','H29','H1','H5','H7','H8','H9','H12','H15','H16','H21','H22','H23','H24','H25'}
FIL_FATIHA_MEANINGS = {'H29','H0','H1','H5','H9','H12','H15','H18','H21','H22'}
FATIHA_EXCLUSIONS = {
    ('ja','H26'): 'Publisher commentary in Ibn Kathir, explicitly separate from the translated Hadith matn.',
    ('fil','H28'): 'The book gives an unquoted descriptive summary; no separately bounded Hadith words.',
    ('fa','H20'): 'The selected formula comes from the publisher explanation field, not translated matn.',
    ('vi','H29'): 'Indirect narrative summary of the question, not a directly quoted translation.',
    ('zh-CN','H29'): 'Indirect narrative summary of the question, not a directly quoted translation.',
}
IKHLAS_EXCLUSIONS = {
    34: 'Historical Badr slogan attributed in Ibn Hisham; not a Prophetic Hadith quotation.',
    49: 'Reported linguistic example involving a weaned camel; not scripture or Hadith.',
    96: 'Reported question of the polytheists or an indirect scholarly narrative; not Prophetic speech.',
    131: 'Unattributed illustrative proverb; not a Prophetic report.',
}
IKHLAS_SPECIFIC_EXCLUSIONS = {
    ('ja',32): 'Historical textbook quotation of Bilal; not a translated complete or explicitly bound Ibn Masud report.',
    ('fil',32): 'Historical textbook quotation of Bilal; no established translation of Ibn Majah150.',
    ('zh-CN',32): 'Historical textbook quotation of Bilal, not a canonical narration translation.',
    ('fa',82): 'The selected Persian words are scholarly explanation in note311, not translated prayer matn.',
    ('vi',62): 'Selected Vietnamese meaning is in HadeethEnc explanation, not its transliterated matn.',
    ('zh-CN',36): 'Selected Chinese words are a meaning-dependent explanation of the ten-recitation report.',
    ('hi',60): 'Selected Hindi sentence is an Ibn Baz scholarly paraphrase in IslamQA, not translated matn.',
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_sha(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def pointer_part(part):
    return str(part).replace('~', '~0').replace('/', '~1')


def pointer_get(value, pointer):
    for part in pointer.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def leaves(value, pointer=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, pointer + '/' + pointer_part(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, pointer + '/' + str(index))
    elif isinstance(value, str):
        yield pointer, value


def find_string(value, wanted, preferred=None):
    hits = [(p, s) for p, s in leaves(value) if wanted in s]
    if preferred:
        hits.sort(key=lambda x: (not preferred(x[0]), len(x[1]), x[0]))
    else:
        hits.sort(key=lambda x: (len(x[1]), x[0]))
    return hits[0] if hits else None


def quote_spans(text):
    result = []
    for match in re.finditer(r'「([^「」]*)」|“([^“”]*)”|«([^«»]*)»|"([^"\n]*)"', text):
        for group in range(1, 5):
            if match.group(group) is not None:
                result.append((match.start(group), match.end(group), match.group(group)))
                break
    return result


def integer_text(text):
    return ''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in text)


def references(text, scope='main_quote', locator=None):
    """Transcribe citations; never use a number to establish wording identity."""
    if not isinstance(text, str):
        return []
    parsed = parse_references(text)
    # Source tables frequently omit spaces in machine-generated canonical labels.
    for key, title, expression in [
        ('abu-dawud', TITLES['abu-dawud'], r'(?:AbuDawud|abudawud|Ab[iu]\s+Dawud)[:\s]*(\d+[a-z]?)'),
        ('ibn-majah', TITLES['ibn-majah'], r'IbnMajah[:\s]*(\d+[a-z]?)'),
        ('adab-al-mufrad', TITLES['adab-al-mufrad'], r'adab[:\s]*(\d+[a-z]?)'),
        ('riyad-as-salihin', TITLES['riyad-as-salihin'], r'Riyad[:\s#]*(\d+[a-z]?)'),
        ('hisn-al-muslim', TITLES['hisn-al-muslim'], r'Hisn[:\s#]*(\d+[a-z]?)(?![\d/])'),
    ]:
        for match in re.finditer(expression, text, re.I):
            parsed.append({'collection': key, 'collection_title': title,
                           'number': match.group(1), 'citation': match.group(0),
                           'start': match.start(), 'end': match.end(),
                           'numbering_scheme': 'as_cited_in_source'})
    parsed.sort(key=lambda x: x['start'])
    out, seen = [], set()
    for item in parsed:
        # Compact English source annotations write e.g. Bukhari5013parallel.
        # The first p is part of 'parallel', not a numbered variant suffix.
        if (re.search(r'[A-Za-z]$', item['number']) and item.get('end',0) < len(text)
                and re.match(r'[A-Za-z]', text[item['end']])):
            item = dict(item, number=item['number'][:-1], citation=item['citation'][:-1])
        # Hisn2015/1436 is the publication year, never an item number.
        if item['collection'] == 'hisn-al-muslim' and re.search(r'Hisn\s*20\d\d',item['citation'],re.I):
            continue
        key = item['collection'], item['number']
        if key in seen:
            continue
        seen.add(key)
        resolved_scope = 'unresolved' if '/' in item['number'] else scope
        row = {'book_key': item['collection'], 'collection': item['collection_title'],
               'number': item['number'] if '/' not in item['number'] else None,
               'scope': resolved_scope, 'source_citation': item['citation'],
               'numbering_scheme': item['numbering_scheme'],
               'verification': 'explicit_source_citation_not_independent_edition_alignment'}
        if locator:
            row['locator'] = locator
        out.append(row)
    return out


def choose_reference(items, key, number=None, citation=None, scope='main_quote'):
    found = next((copy.deepcopy(x) for x in items if x['book_key'] == key and
                  (number is None or x['number'] == str(number))), None)
    if found is None:
        if citation is None:
            raise ValueError('Missing source evidence for reference: ' + str((key, number)))
        found = {'book_key': key, 'collection': TITLES[key], 'number': str(number) if number is not None else None,
                 'source_citation': citation, 'verification': 'explicit_source_citation_not_independent_edition_alignment'}
    found['scope'] = scope
    return found


def unique_references(items):
    out, seen = [], set()
    for item in items:
        key = item['book_key'], item.get('number'), item['scope'], item['source_citation']
        if key not in seen:
            out.append(item); seen.add(key)
    return out


class Extractor:
    def __init__(self, snapshot=None, tree=None, bundled=None):
        self.snapshot = Path(snapshot) if snapshot is not None else None
        if bundled is not None:
            self.tree = {path: {'path': path, 'type': 'blob', 'sha': entry['git_blob_sha'],
                                'size': entry['byte_count']} for path, entry in bundled.items()}
            self.raw = {path: entry['raw_text'].encode('utf-8') for path, entry in bundled.items()}
        else:
            tree_rows = json.loads(Path(tree).read_text())
            tree_rows = tree_rows.get('tree', tree_rows) if isinstance(tree_rows, dict) else tree_rows
            self.tree = {x['path']: x for x in tree_rows if x.get('type') == 'blob'}
            self.raw = {}
        self.docs, self.used = {}, collections.defaultdict(set)
        self.records, self.decisions = [], []

    @classmethod
    def from_bundles(cls, root):
        """Replay from the checked-in source bytes, without an acquisition cache."""
        files = {}
        for path in sorted((Path(root) / 'materials').glob('quran-excerpts-*/source-bundle.json')):
            bundle = json.loads(path.read_text(encoding='utf-8'))
            assert bundle['commit'] == PIN and bundle['repository'] == REPOSITORY, path
            for entry in bundle['files']:
                raw = entry['raw_text'].encode('utf-8')
                assert len(raw) == entry['byte_count'] and sha256(raw) == entry['sha256'], entry['path']
                assert blob_sha(raw) == entry['git_blob_sha'], entry['path']
                previous = files.setdefault(entry['path'], entry)
                assert previous == entry, 'Conflicting bundled source: ' + entry['path']
        assert files, 'No bundled Quran source bytes found'
        return cls(bundled=files)

    def source_bytes(self, path):
        if path not in self.raw:
            assert self.snapshot is not None, 'Missing bundled source: ' + path
            self.raw[path] = (self.snapshot / path).read_bytes()
        raw = self.raw[path]
        assert blob_sha(raw) == self.tree[path]['sha'], 'Pinned Git blob mismatch: ' + path
        return raw

    def document(self, path, language=None):
        if path not in self.docs:
            raw = self.source_bytes(path)
            self.docs[path] = json.loads(raw)
        if language:
            self.used[language].add(path)
        return self.docs[path]

    def location(self, path, pointer, text=None, start=None):
        value = pointer_get(self.document(path), pointer)
        assert isinstance(value, str), (path, pointer)
        if text is None:
            text, start = value, 0
        elif start is None:
            assert value.count(text) == 1, ('Nonunique text requires explicit offset', path, pointer, text)
            start = value.index(text)
        end = start + len(text)
        assert value[start:end] == text, (path, pointer, start, end)
        return {'path': path, 'git_blob_sha': self.tree[path]['sha'], 'sha256': sha256(self.raw[path]),
                'json_pointer': pointer, 'char_start': start, 'char_end': end,
                'offset_unit': 'Unicode code points in decoded JSON string',
                'decoded_utf8_start': len(value[:start].encode('utf-8')),
                'decoded_utf8_end': len(value[:end].encode('utf-8')),
                'text_sha256': sha256(text.encode('utf-8'))}

    def decision(self, language, family, token, status, reason, path, pointer=None, **extra):
        self.decisions.append({'language': language, 'family': family, 'source_token': token,
                               'status': status, 'reason': reason, 'path': path,
                               'json_pointer': pointer, **extra})

    def emit(self, language, family, token, path, pointer, text, record_type, refs,
             metadata=None, metadata_locator=None, context=None, arabic=None, arabic_locator=None,
             narrator=None, translator=None, source_url=None, notes=None, start=None):
        assert record_type in TYPE_LABELS
        assert text and text.strip()
        loc = self.location(path, pointer, text, start)
        main = next((x for x in refs if x['scope'] == 'main_quote'), None)
        book = main['book_key'] if main else 'unclassified'
        number = main.get('number') if main else None
        occurrence = f'iman-quran-{language}-{family}-{token}'.replace(':','-').lower()
        assert all(x['id'] != occurrence for x in self.records), occurrence
        self.used[language].add(path)
        if metadata_locator:
            self.used[language].add(metadata_locator['path'])
        if arabic_locator:
            self.used[language].add(arabic_locator['path'])
        # Every displayed citation is itself a reproducible source substring,
        # not a generated bibliographical sentence or a normalized paraphrase.
        for ref in refs:
            reference_location = ref.get('locator') or metadata_locator or {'path':path,'json_pointer':pointer}
            reference_document = self.document(reference_location['path'])
            container = pointer_get(reference_document, reference_location['json_pointer'])
            hit = find_string(container, ref['source_citation'])
            assert hit, ('Citation not at evidence locator', language, family, token, ref, reference_location)
            string_pointer = reference_location['json_pointer'] + hit[0]
            ref['locator'] = self.location(reference_location['path'],string_pointer,ref['source_citation'],hit[1].index(ref['source_citation']))
            self.used[language].add(reference_location['path'])
        context_note = 'This is an explicitly bounded source excerpt, not the complete Hadith. Separate occurrences are not distinct-Hadith counts.'
        if record_type == 'companion_report_excerpt':
            context_note += ' The quoted words are attributed to a Companion, not to the Prophet.'
        record = {
            'id': occurrence, 'language': language, 'book_key': book, 'edition': EDITION,
            'title': TYPE_LABELS[record_type] + ' — ' + {'fatiha':'Al-Fatiha study','ikhlas':'Al-Ikhlas study','qiyamah':'Al-Qiyamah study','quran-footnote':'Quran translation footnote'}[family] + ' / ' + token,
            'record_type': record_type, 'content_kind': record_type,
            'text': {'arabic': arabic, 'translation': text},
            'number': {'source_entry_id': token, 'in_book': number, 'canonical': None,
                       'numbering_scheme': 'as_cited_in_source' if number else 'unresolved'},
            'source': {'title': f'{LANGUAGE_NAMES[language]} Hadith excerpts in Quran-study materials',
                       'repository': REPOSITORY, 'commit': PIN, 'family': family, 'source_token': token,
                       'url': source_url or f'https://github.com/{REPOSITORY}/blob/{PIN}/{path}',
                       'record_url': f'https://github.com/{REPOSITORY}/blob/{PIN}/{path}',
                       'original_locator': loc, 'metadata_locator': metadata_locator,
                       'arabic_locator': arabic_locator, 'source_classification': record_type,
                       'is_excerpt': True, 'context_note': context_note,
                       'original_source_metadata': metadata or {},
                       'original_context': context},
            'narrator': {'name': narrator, 'evidence': metadata_locator if narrator else None},
            'translator': {'name': translator, 'evidence': metadata_locator if translator else None},
            'references': {'items': unique_references(refs), 'scope_note': 'Main citation follows the selected source; original-source and parallel citations do not assert identical wording.'},
            'extraction': {'method': 'structured_source_quote', 'ocr_used': False,
                           'scope': 'Exact source JSON string selection; no OCR or translation during extraction.'},
            'translation_provenance': {'origin': 'unknown', 'label': 'Unknown', 'ai_translation': 'unknown',
                                       'basis': 'Copied Iman/old-bank material: owner confirmation pending. Historical source wording and authorship metadata remain preserved.',
                                       'human_involvement': 'not_established', 'evidence_ids': []},
            'ai_translation': 'unknown',
            'commentary': {'arabic': None, 'translation': context_note + (('\n' + notes) if notes else '')},
            'footnotes': [], 'review': {'status': 'source_extracted', 'independent_pro_qc': 'not_asserted',
                                      'release_status': 'source_candidate', 'release_eligible': False,
                                      'certified_release_eligible': False, 'issues': []},
            'rights': {'status': 'source_conditions_preserved', 'reuse_basis': None,
                       'scope_note': 'Original source credits, conditions, historical review flags and limitations are retained in the source bundle.'},
        }
        self.records.append(record)
        self.decision(language, family, token, 'extracted', 'Exact bounded source quote or explicitly labeled Hadith meaning.', path, pointer,
                      record_id=occurrence, record_type=record_type, book=book, number=number)
        return record

    def fatiha(self):
        route_path = FATIHA + '/uz/sources.json'
        routes = self.document(route_path)['quotationRoutes']
        routes = [(i, x) for i, x in enumerate(routes) if re.fullmatch(r'H\d+', x['id'])]
        common = {x['id']: (i, x) for i, x in routes}
        arabic_path = 'materials/tadabbur/ar/extended/001.json'
        original = self.document(arabic_path)
        for language in LANGUAGES:
            reading_path, source_path = FATIHA + '/' + language + '/reading.json', FATIHA + '/' + language + '/sources.json'
            reading, source = self.document(reading_path, language), self.document(source_path, language)
            self.used[language].add(route_path)
            units = {x['id']: (i, x) for i, x in enumerate(reading['units'])}
            candidates = []
            if language == 'fa':
                candidates = [(x['id'], x, '/sourceDetails/sourceSelections/' + str(i)) for i, x in enumerate(source['sourceDetails']['sourceSelections']) if re.fullmatch(r'H\d+[AB]?', x.get('id', ''))]
            elif language in ('vi', 'zh-CN'):
                candidates = [(k, v, '/sourceDetails/quotationSelections/hadithOccurrences/' + k) for k, v in source['sourceDetails']['quotationSelections']['hadithOccurrences'].items()]
            elif language == 'uz':
                candidates = [(x['id'], x, '/quotationRoutes/' + str(i)) for i, x in routes]
            elif language == 'hi':
                for ui, unit in enumerate(reading['units']):
                    for bi, block in enumerate(unit['blocks']):
                        for si, span in enumerate(block.get('spans', [])):
                            if re.fullmatch(r'H\d+', span.get('sourceToken', '')):
                                candidates.append((span['sourceToken'], span, f'/units/{ui}/blocks/{bi}/spans/{si}'))
            else:
                candidates = [(key, {}, None) for key in common]
            for token, selected, meta_pointer in candidates:
                base = re.sub('[AB]$', '', token)
                ri, route = common[base]
                ui, unit = units[route['unit']]
                bi = route['block']; block = unit['blocks'][bi]
                bptr = f'/units/{ui}/blocks/{bi}/text'
                exclusion = FATIHA_EXCLUSIONS.get((language, base))
                if base == 'H28':
                    exclusion = 'Single-word gloss or explanation of khidaj (incomplete), not a separate bounded narration; adjacent report quotation is preserved.'
                if exclusion:
                    self.decision(language, 'fatiha', token, 'excluded_non_narration', exclusion, reading_path, bptr, metadata_pointer=meta_pointer)
                    continue
                if language in ('ja', 'fil'):
                    choices = quote_spans(block['text'])
                    qi = (FATIHA_QUOTE_INDEX if language == 'ja' else FATIHA_FIL_INDEX)[base]
                    start, end, text = choices[qi]
                    source_kind = 'own_labeled_meaning' if base in (JA_FATIHA_MEANINGS if language == 'ja' else FIL_FATIHA_MEANINGS) else 'published_excerpt'
                    selected = {'selection_method': 'reviewed_printed_quote_boundary', 'quote_index': qi, 'kind': source_kind}
                    metadata_location = {'path': reading_path, 'json_pointer': f'/units/{ui}/blocks/{bi}'}
                else:
                    text = selected['text']; start = block['text'].find(text)
                    assert start >= 0, (language, token, 'Selected quotation missing from current reading')
                    metadata_location = {'path': reading_path if language == 'hi' else source_path, 'json_pointer': meta_pointer}
                    source_kind = selected.get('kind', '')
                    if language == 'hi':
                        own = source['sourceDetails']['summary']['hadithRoutes']['directOriginalMeanings']
                        source_kind = 'own_labeled_meaning' if base in own else 'published_excerpt'
                own = 'own' in source_kind.lower() or 'direct' in source_kind.lower()
                record_type = 'hadith_meaning_excerpt' if own else 'hadith_excerpt'
                original_locator = route.get('originalLocator', {})
                arquote = original_locator.get('originalArabicQuote', route.get('originalArabicQuote'))
                original_ref = original_locator.get('reference', route.get('originalReference'))
                assert original_ref and arquote, (language, token)
                original_refs = references(original_ref, locator={'path': route_path, 'json_pointer': '/quotationRoutes/' + str(ri)})
                assert original_refs, original_ref
                refs = copy.deepcopy(original_refs)
                notes = None; narrator = None
                # Published alternative is intentionally not relabeled with the
                # original Arabic lesson's narrator/number.
                if base == 'H13' and not own:
                    notes = 'Selected published report is the Umar/Muslim parallel; the original Arabic lesson cites Abu Hurayra/Bukhari50.'
                    if language == 'uz':
                        citation = route['qualification']; citation_locator = {'path':route_path,'json_pointer':'/quotationRoutes/'+str(ri)+'/qualification'}
                    elif language in ('ja','fil'):
                        ni = 2 if language == 'ja' else 1
                        citation = reading['readerNotes'][ni]['text']; citation_locator = {'path':reading_path,'json_pointer':f'/readerNotes/{ni}/text'}
                    elif language in ('vi','zh-CN'):
                        citation = selected['grade']['takhrij']; citation_locator = {'path':source_path,'json_pointer':meta_pointer+'/grade/takhrij'}
                    else:
                        citation = None; citation_locator = None
                    refs = ([choose_reference([], 'muslim', '8a' if language == 'uz' else None,citation=citation)] if citation else [])
                    if refs:
                        refs[0]['locator'] = citation_locator
                    refs += [{**x, 'scope': 'variant'} for x in original_refs]
                    narrator = 'Umar ibn al-Khattab' if language in ('ja','fil','uz') else None
                if language == 'zh-CN' and base == 'H25':
                    notes = selected['rationale']
                    refs = [choose_reference([], 'tirmidhi', citation=selected['rationale'])]
                    refs += [choose_reference([], k, citation=selected['rationale'], scope='variant') for k in ('ibn-majah','ahmad')]
                    refs += [{**x, 'scope': 'variant'} for x in original_refs]
                    narrator = 'Safwan ibn Assal'
                if language == 'fil' and base == 'H24':
                    refs = [{**x, 'scope': 'variant'} for x in original_refs]
                    notes = 'Source reading note2 identifies the selected wording as al-Barqani’s additional report, not the complete Muslim1920 text. Selected-source collection number unresolved.'
                if language == 'fil' and base == 'H4':
                    refs = [choose_reference([], 'ahmad', citation=source['sourceDetails']['conditionsAndVersions']['NewMuslimsHajj']['scope'])]
                    refs[0]['locator'] = {'path':source_path,'json_pointer':'/sourceDetails/conditionsAndVersions/NewMuslimsHajj/scope'}
                    refs += [{**x, 'scope': 'variant'} for x in original_refs]
                if language == 'fa' and base == 'H0':
                    cp = '/sourceDetails/creditsConditionsAndVersions/books/SeparEMomen/literalScope'
                    source_refs = references(pointer_get(source,cp),scope='commentary',locator={'path':source_path,'json_pointer':cp})
                    refs = [choose_reference(source_refs,'abu-dawud','5092'), choose_reference(source_refs,'ahmad','20447',scope='variant')]
                    refs += [{**x,'scope':'variant'} for x in original_refs]
                if language == 'fa' and base == 'H25':
                    refs = [{**x,'scope':'commentary'} for x in original_refs]
                    notes = 'The published parent branch is not explicitly resolved in this pinned source companion; original Bukhari6169 remains context, not an asserted number for this target translation.'
                if language in ('fil','vi') and base == 'H25':
                    notes = reading['readerNotes'][1]['text']
                    narrator = 'Ibn Masud'
                # Keep all explicitly stated variant qualifications, rather than
                # treating reference equality as a proof of matching text.
                for field in ('rationale', 'qualification', 'scope_and_variant'):
                    if isinstance(selected.get(field), str):
                        refs += references(selected[field], scope='commentary', locator=metadata_location)
                        notes = '\n'.join(x for x in (notes, selected[field]) if x)
                artext, arloc = None, None
                if own or (language == 'uz' and base != 'H13'):
                    arkey = 'intro' if route['unit'] == 'intro:1' else route['unit']
                    arblocks = original['entries'][arkey]['blocks']
                    # Intro has no ayah block; verse units share the same block
                    # indexes in the source and translated reading.
                    aptr = f'/entries/{pointer_part(arkey)}/blocks/{bi}/text'
                    avalue = pointer_get(original, aptr)
                    if arquote in avalue:
                        artext = arquote
                        arloc = self.location(arabic_path, aptr, artext)
                    else:
                        # Original quotation table is itself preserved evidence.
                        afield = '/originalLocator/originalArabicQuote' if route.get('originalLocator') else '/originalArabicQuote'
                        artext = arquote
                        arloc = self.location(route_path, '/quotationRoutes/' + str(ri) + afield)
                record = self.emit(language, 'fatiha', token, reading_path, bptr, text, record_type, refs,
                                   metadata=selected, metadata_locator=metadata_location, context=block['text'],
                                   arabic=artext, arabic_locator=arloc, narrator=narrator,
                                   source_url=selected.get('sourceURL'), notes=notes, start=start)
                record['source']['original_arabic_reference'] = {'source_token': base, 'reference': original_ref,
                    'scope': 'original_lesson_reference; published parallels may differ',
                    'locator': {'path': route_path, 'json_pointer': '/quotationRoutes/' + str(ri)}}
            # Original Arabic prose also summarizes reports without quoting
            # them. Inventory these citations, never silently claim full text.
            for unit_id, (ui, unit) in units.items():
                arkey = 'intro' if unit_id == 'intro:1' else unit_id
                for bi, arblock in enumerate(original['entries'][arkey]['blocks']):
                    citation_text = arblock.get('bibliographyPresentation', {}).get('originalText')
                    if not citation_text:
                        continue
                    citation_refs = references(citation_text, scope='commentary')
                    if citation_refs:
                        self.decision(language, 'fatiha', f'context-{unit_id}-{bi}', 'context_inventory',
                                      'Original lesson bibliography retained as context; no new narration inferred from a citation.',
                                      arabic_path, f'/entries/{pointer_part(arkey)}/blocks/{bi}/bibliographyPresentation/originalText',
                                      references=citation_refs)
            self.used[language].add(arabic_path)

    def ikhlas(self):
        for language in LANGUAGES:
            evidence_paths = [p for p in self.tree if p.startswith(f'{IKHLAS}/{language}/')
                              and Path(p).name.startswith('IKHLAS') and p.endswith('.json')]
            assert len(evidence_paths) == 1, (language, evidence_paths)
            evidence_path = evidence_paths[0]
            evidence = self.document(evidence_path, language)
            if language == 'ja':
                selections, selection_pointer = evidence['nonQ_selected17'], '/nonQ_selected17'
                routes = []
            elif language == 'uz':
                selections, selection_pointer = evidence['nonQuran']['all17selections'], '/nonQuran/all17selections'
                routes = evidence['nonQuran']['all26routes']
                route_pointer = '/nonQuran/all26routes'
            else:
                selections, selection_pointer = evidence['selected_nonQ'], '/selected_nonQ'
                route_key = next((k for k,v in evidence.items() if '26' in k and isinstance(v,list)), None)
                routes = evidence[route_key] if route_key else []
                route_pointer = '/' + route_key if route_key else None
            route_lookup = {int(x.get('inventory_index', x.get('index', -1))): (i,x) for i,x in enumerate(routes)}
            occurrences = collections.defaultdict(list)
            for unit in range(1,5):
                path = f'{IKHLAS}/{language}/112-{unit:03d}.json'
                document = self.document(path, language)
                for pointer, value in leaves(document):
                    if not pointer.endswith('/text') or '/segments/' not in pointer:
                        continue
                    segment = pointer_get(document, pointer.rsplit('/',1)[0])
                    match = re.fullmatch(r'N:(\d+)(?::\d+)?', str(segment.get('binding','')))
                    if match:
                        occurrences[int(match.group(1))].append((path,pointer,value,segment))
            for number in sorted(occurrences):
                key = 'N:' + str(number) if language == 'ja' else str(number)
                selected = selections.get(key)
                assert selected is not None, (language, key)
                sptr = selection_pointer + '/' + pointer_part(key)
                mloc = {'path': evidence_path, 'json_pointer': sptr}
                reason = IKHLAS_SPECIFIC_EXCLUSIONS.get((language,number), IKHLAS_EXCLUSIONS.get(number))
                route = route_lookup.get(number, (None,{}))[1]
                for occindex, (path,pointer,text,segment) in enumerate(occurrences[number]):
                    token = 'N' + str(number) + (('-' + str(occindex+1)) if len(occurrences[number]) > 1 else '')
                    if reason:
                        self.decision(language,'ikhlas',token,'excluded_non_narration',reason,path,pointer,
                                      metadata_locator=mloc, text=text)
                        continue
                    selection_kind = selected.get('classification', selected.get('kind',selected.get('type','')))
                    own = 'own' in selection_kind.lower() or 'direct_arabic' in selection_kind.lower() or selection_kind == 'original_nonq_meaning'
                    meaning = own or selection_kind in ('published_nonq_meaning',)
                    record_type = 'companion_report_excerpt' if number == 32 else 'hadith_meaning_excerpt' if meaning else 'hadith_excerpt'
                    identity = selected.get('actual_identity', selected.get('reference', selected.get('original_report_identity', selected.get('identity',''))))
                    flat_fields = {k:v for k,v in selected.items() if isinstance(v,str) and k not in ('text','full_original_parent','full_published_parent_Hindi','full_published_parent_Arabic')}
                    reftext = '\n'.join(flat_fields.values())
                    all_refs = references(reftext,scope='commentary',locator=mloc)
                    original_reftext = str(route.get('classification','')) + ' ' + str(route.get('current_arabic_context',''))
                    rloc = {'path':evidence_path,'json_pointer':route_pointer+'/'+str(route_lookup[number][0])} if route else mloc
                    original_refs = references(original_reftext,scope='commentary',locator=rloc)
                    primary = []
                    # Explicit selected-source identity takes priority. References
                    # to a source's parallel or original lesson stay secondary.
                    identity_refs = references(identity, locator=mloc)
                    if identity_refs:
                        primary = [identity_refs[0]]
                    elif own and original_refs:
                        primary = [{**original_refs[0], 'scope':'main_quote'}]
                    elif number == 32:
                        primary = [choose_reference(all_refs+original_refs,'ibn-majah','150',citation=reftext or original_reftext)]
                    elif number in (30,70,84,101) and original_refs:
                        primary = [{**original_refs[0], 'scope':'main_quote'}]
                    elif number == 24 and language == 'fil':
                        cited = reftext + '\n' + str(route.get('route',''))
                        primary = [choose_reference(references(cited),'bukhari','5013',citation=cited)]
                    elif number == 24 and language == 'hi':
                        primary = [choose_reference([], 'bukhari',citation=selected['assessment'])]
                    elif number == 36 and language == 'fil':
                        primary = [choose_reference(original_refs,'bukhari','3293')]
                    elif number in (12,62,82,89) and original_refs:
                        primary = [{**original_refs[0],'scope':'main_quote'}]
                    if language == 'uz' and number in (24,36):
                        primary = references(selected['parent'],locator=mloc)
                    if language == 'vi' and number in (36,84):
                        primary = [choose_reference([], 'hisn-al-muslim', '68' if number == 36 else '67',citation=identity)]
                    if language == 'vi' and number == 82:
                        primary = [choose_reference([], 'riyad-as-salihin','67',citation=identity)]
                        primary[0]['numbering_scheme'] = 'selected_Vietnamese_abridgment_number_not_canonical_Riyad_number'
                    if language == 'fil' and number == 12:
                        primary = [choose_reference([], 'hisn-al-muslim','128',citation=selected['full_scope_assessment'])]
                    if language == 'fil' and number == 82:
                        primary = [choose_reference([], 'hisn-al-muslim',citation=selected['full_scope_assessment'])]
                    if language == 'hi' and number == 36:
                        primary = [choose_reference([], 'hisn-al-muslim',citation=selected['credit'])]
                    if language == 'hi' and number == 82:
                        primary = [choose_reference(all_refs,'bukhari','6313')]
                    if language == 'ja' and number == 36:
                        primary = references(identity,locator=mloc)[:1] # Hisn93, not original hundred/day frame.
                    if language == 'ja' and number in (60,84):
                        primary = [] # Source explicitly supplies no collection/narrator.
                    if language in ('fil','vi') and number == 60:
                        primary = [] # Longer published disease report, not a full Bukhari5678 translation.
                    if language == 'zh-CN' and number == 126:
                        primary = [choose_reference(all_refs,'nasai','5438')]
                    if language == 'zh-CN' and number == 24:
                        primary = [] # Source only calls this the short Abu Said parallel, no number established here.
                    if language == 'uz' and number == 82:
                        primary = references(selected['parent'],locator=mloc) # Published Riyad812; original247 differs.
                    # A primary reference is one source attribution, not a claim
                    # that every comparative reference has identical wording.
                    refs = primary + all_refs + original_refs
                    arabic, aloc = None, None
                    aq = selected.get('arabic',selected.get('Arabic_original_token',route.get('arabic')))
                    # Arabic selected in a different narration is not paired to
                    # the published target merely because of a similar meaning.
                    if aq and (own or number == 32 or language == 'fa' and number in (12,24,60,126)):
                        found = find_string(evidence,aq,lambda p:p.startswith(sptr) or 'routes' in p)
                        if found:
                            arabic = aq; aloc = self.location(evidence_path,found[0],aq)
                    if language == 'ja' and own:
                        # The Japanese envelope explicitly binds each selected
                        # N-token to a bilingual sentence. Use that mapping,
                        # never a same-number search of unrelated Arabic.
                        paired = evidence['all148_independent_meaning_decisions']
                        mapped = [(i,row) for i,row in enumerate(paired)
                                  if any(b.get('binding') == 'N:'+str(number) and b.get('text') == text
                                         for b in row.get('bindings',[]))]
                        if len(mapped) == 1:
                            ai, arrow = mapped[0]; quoted = quote_spans(arrow['Arabic'])
                            if len(quoted) == 1:
                                arabic = arrow['Arabic'][quoted[0][0]-1:quoted[0][1]+1]
                                aloc = self.location(evidence_path,f'/all148_independent_meaning_decisions/{ai}/Arabic',arabic)
                    narrator = None
                    source_info = selected.get('source',{})
                    if not isinstance(source_info,dict): source_info = {}
                    parent = source_info.get('complete_parent_notes',{})
                    if isinstance(parent,dict):
                        narrator = parent.get('hadeeth_intro') or None
                    if narrator is None and not (language == 'ja' and number in (60,84)):
                        # Only names literally present in the selected-source
                        # identity field qualify; later comparative names are
                        # not substituted for the selected report's narrator.
                        candidates = list(re.finditer(r'Ibn\s*Abbas|Ibn\s*Masud|AbdullahIbnMasud|Abu\s*Hurayra[h]?|Abu\s*Darda|Abu\s*Said|Abu\s*Ayyub|Abu\s*Bakr|Muadh|Aisha|Thawban|[Aa]l[-\s]*Bara|Uqba[h]?(?:\s+IbnAmir)?',identity))
                        if candidates:
                            narrator = candidates[0].group(0)
                    translator = source_info.get('translator')
                    if not isinstance(translator,str): translator = None
                    if translator is None and language == 'ja':
                        credit = selected.get('short_credit','')
                        match = re.search(r'（([^（）]+)訳）',credit)
                        if match: translator = match.group(1)
                    notes = '\n'.join(v for k,v in flat_fields.items() if k in ('scope_and_variant','context_and_variant_decision','full_scope_assessment','actual_identity','reference','scope','classification'))
                    if number == 12:
                        notes += '\nThe selected words occur inside the Ibn Abbas report about Ibrahim or Muhammad. The same words also occur in Quran3:173; this record preserves the report occurrence and its source context.'
                    if number == 32:
                        notes += '\nBilal is the quoted speaker. This is a Companion utterance within the Ibn Masud report, not speech of the Prophet.'
                    self.emit(language,'ikhlas',token,path,pointer,text,record_type,refs,
                              metadata=selected,metadata_locator=mloc,context=segment,
                              arabic=arabic,arabic_locator=aloc,narrator=narrator,translator=translator,
                              source_url=selected.get('source_url',source_info.get('url')),notes=notes)
            for route_index, route in enumerate(routes):
                number = int(route.get('inventory_index',route.get('index',-1)))
                if number not in occurrences:
                    self.decision(language,'ikhlas','N'+str(number),'excluded_no_selected_quote',
                                  'Source route is narrative/context or an unselected comparison; no selected N-bound quotation in current reading.',
                                  evidence_path,route_pointer+'/'+str(route_index),
                                  source_classification=route.get('classification'),source_metadata=route)

    def qiyamah(self):
        path = QIYAMAH + '/NON-QURAN-SOURCE-RECORDS658.json'
        records = self.document(path,'ja')
        paragraphs_path = QIYAMAH + '/PARAGRAPHS-AND-SEMANTIC-RUNS658.json'
        paragraphs = self.document(paragraphs_path,'ja')
        for index,item in enumerate(records):
            quotes = item['selectedJapaneseMeaningOrQuote']
            if not quotes:
                self.decision('ja','qiyamah',item['id'],'excluded_non_narration',
                              'Source explicitly classifies this as narrative summary, not quoted Hadith text.',path,'/'+str(index),
                              references=item['reference'],source_classification=item['classification'])
                continue
            refs = references(item['reference'],locator={'path':path,'json_pointer':f'/{index}/reference'})
            if item['id'] == 'H09':
                refs = [{**r,'scope':'main_quote' if r['book_key']=='ibn-majah' else 'variant'} for r in refs]
            if item['id'] == 'H10':
                refs = [choose_reference(refs,'abu-dawud','884')]
                refs[0]['alternate_numbering'] = {'book':'2','hadith':'494','english':'883'}
            for qi,quote in enumerate(quotes):
                locations = [(pi,p) for pi,p in enumerate(paragraphs) if p.get('paragraphId') in item['paragraphIds'] and quote in p.get('text','')]
                assert len(locations) == 1,(item['id'],len(locations))
                pi,paragraph = locations[0]
                token = item['id'] + ('-'+str(qi+1) if len(quotes)>1 else '')
                typ = 'hadith_excerpt' if item['classification'] == '刊行された日本語訳からの引用' else 'hadith_meaning_excerpt'
                self.emit('ja','qiyamah',token,paragraphs_path,f'/{pi}/text',quote,typ,refs,
                          metadata=item,metadata_locator={'path':path,'json_pointer':'/'+str(index)},
                          context=paragraph['text'],narrator=item.get('narrator'),notes=item['contextAndVariantNote'])
            for key in item['unitKeys']:
                unit = key.split(':')[-1]
                self.document(f'materials/tadabbur/ja/extended/075/{int(unit):03d}.json','ja')
        # Notes/credits are indispensable context, not additional occurrences.
        for name in ('NON-QURAN-PUBLISHED-NOTES658.json','PUBLISHED-NOTES658.json','FRONTMATTER-AND-BIBLIOGRAPHY658.json'):
            self.document(QIYAMAH+'/'+name,'ja')

    def heart_quran(self):
        for language in ('ja','fil','vi','uz'):
            path = HEART+'/'+language+'.json'
            document = self.document(path)
            self.decision(language,'heart-quran','verse-bodies','excluded_quran',
                          'Protected Quran verse bodies and explanatory notes are not Hadith records; separate numbered quotation in Sato companion handled below.',
                          path, '/verses',verse_count=len(document['verses']))
        path = HEART+'/sato-155-context.json'
        document = self.document(path,'ja')
        pointer = '/contexts/4/footnotes'
        note = pointer_get(document,pointer)
        quote = quote_spans(note)[0][2]
        citation = re.search(r'アフマド[0-9０-９]+',note).group(0)
        refs = [choose_reference([], 'ahmad', integer_text(re.search(r'[0-9０-９]+',citation).group(0)),citation=citation)]
        credit_path=HEART+'/source-credits.json'; credits=self.document(credit_path,'ja')
        self.emit('ja','quran-footnote','sato-29-2-note1',path,pointer,quote,'hadith_excerpt',refs,
                  metadata={'source':document['source'],'version':document['version'],'verse':'29:2','credit_id':document['credit_id']},
                  metadata_locator={'path':path,'json_pointer':'/contexts/4'},context=note,
                  translator='サイード佐藤',notes='The published ellipsis is preserved. This is a Hadith quotation inside a Quran translator footnote, not a Quran verse.')
        for verse in ('2:186','3:173','9:40'):
            p=HEART+'/ja.json';d=self.document(p)
            self.decision('ja','heart-quran','historical-note-'+verse,'excluded_non_narration',
                          'Unnumbered historical retelling or question in Quran commentary; not promoted to a canonical Hadith translation.',
                          p,'/verses/'+verse+'/notes/0',text=d['verses'][verse]['notes'][0])

    def scoped_source_files(self):
        for path,entry in sorted(self.tree.items()):
            if not any(t in path.lower() for t in ('quran','tadabbur')):
                continue
            match=re.search(r'(?:^|/)('+'|'.join(re.escape(x) for x in LANGUAGES)+r')(?:/|\.|$)',path)
            if not match:
                continue
            language=match.group(1)
            if not path.endswith(('.json','.md','.txt')):
                continue
            yield path, entry, language

    def markdown_comparisons(self):
        """Check actual rendered quotations, not a filename-based mirror guess.

        Whitespace is collapsed only for comparisons; all original source bytes
        and emitted record text remain unchanged. Quotation delimiters are not
        Hadith classifiers: Quran quotations, titles and commentary also occur
        in this audit and are matched to their preserved structured fields.
        """
        normalized = lambda text: re.sub(r'\s+', ' ', text).strip()
        fields = collections.defaultdict(list)
        for path, entry, language in self.scoped_source_files():
            if path.endswith('.json'):
                for pointer, value in leaves(self.document(path)):
                    if value.strip():
                        fields[language].append((normalized(value), path, pointer, value))
        credits_path = HEART + '/source-credits.json'
        common = [(normalized(value), credits_path, pointer, value)
                  for pointer, value in leaves(self.document(credits_path)) if value.strip()]
        for language in LANGUAGES:
            fields[language] = sorted(fields[language] + common, key=lambda x: (len(x[0]), x[1], x[2]))
        cache = {}

        def match_field(text, language):
            key = language, normalized(text)
            if key not in cache:
                hit = next((x for x in fields[language] if key[1] in x[0]), None)
                cache[key] = None if hit is None else {
                    'path': hit[1], 'json_pointer': hit[2],
                    'source_field_sha256': sha256(hit[3].encode('utf-8')),
                    'comparison': 'exact_substring' if text in hit[3] else 'layout_whitespace_only',
                }
            result = cache[key]
            if result:
                self.used[language].add(result['path'])
            return result

        output = []
        for path, entry, language in self.scoped_source_files():
            if not path.endswith(('.md', '.txt')):
                continue
            raw = self.source_bytes(path)
            text = raw.decode('utf-8')
            self.used[language].add(path)
            paired_path = str(Path(path).with_suffix('.json'))
            if paired_path not in self.tree:
                # These seven complete notes were read in the recovery audit.
                # They discuss citations/conditions/model review, not additional
                # narrated text. They are preserved, never called JSON mirrors.
                assert path.startswith(IKHLAS + '/') and 'NOTE' in Path(path).name, path
                output.append({'path': path, 'language': language, 'sha256': sha256(raw),
                               'status': 'examined_source_note',
                               'assessment': 'Complete source note read: edition, translation, source-scope, provenance, review and reuse qualifications; no additional bounded Hadith narration.',
                               'is_format_mirror': False, 'new_narration_occurrences': 0})
                continue
            paired = self.document(paired_path)
            self.used[language].add(paired_path)
            checks = []
            for index, (start, end, quote) in enumerate(quote_spans(text)):
                if not quote.strip():
                    continue
                match = match_field(quote, language)
                if match:
                    matches = [match]
                    status = 'matched_structured_source_field'
                else:
                    # Published Quran quotation marks sometimes open in one
                    # verse and close after several verse headings/credits.
                    # Account for each visible component, without joining it
                    # into a newly invented narration.
                    parts = [line.strip().removeprefix('> ').strip() for line in quote.splitlines()
                             if line.strip() and not line.lstrip().startswith('#')
                             and not re.fullmatch(r'\s*\[[^\]]+\]\([^)]+\)\s*', line)]
                    matches = [match_field(part, language) for part in parts]
                    assert parts and all(matches), ('Unaccounted Markdown quotation', path, index, quote)
                    status = 'matched_rendered_quran_sequence_and_credits'
                checks.append({'quote_index': index, 'char_start': start, 'char_end': end,
                               'text_sha256': sha256(quote.encode('utf-8')), 'status': status,
                               'source_fields': matches})
            source_strings = [normalized(s) for _, s in leaves(paired)]
            source_text = '\n'.join(source_strings)
            excerpts = []
            for record in self.records:
                quote = record['text']['translation']
                if record['language'] != language or normalized(quote) not in source_text:
                    continue
                assert normalized(quote) in normalized(text), ('Missing excerpt in rendered mirror', path, record['id'])
                excerpts.append({'record_id': record['id'],
                                 'comparison': 'exact_substring' if quote in text else 'layout_whitespace_only'})
            output.append({'path': path, 'language': language, 'sha256': sha256(raw),
                           'status': 'verified_format_mirror', 'is_format_mirror': True,
                           'paired_json_path': paired_path,
                           'paired_json_sha256': sha256(self.source_bytes(paired_path)),
                           'quotation_checks': checks, 'extracted_record_checks': excerpts,
                           'unaccounted_quoted_spans': 0, 'new_narration_occurrences': 0,
                           'scope': 'Every delimited quotation matched against preserved structured source fields; applicable extracted excerpts compared separately. This does not assert whole-file byte identity.'})
        return output

    def coverage(self, markdown_comparisons):
        rows=[]
        compared = {x['path']: x for x in markdown_comparisons}
        for path,entry,language in self.scoped_source_files():
            occurrences=[x for x in self.records if x['source']['original_locator']['path']==path]
            decisions=[x for x in self.decisions if x['path']==path]
            raw = self.source_bytes(path)
            if path.endswith(('.md','.txt')):
                comparison = compared[path]
                if comparison['is_format_mirror']:
                    status='verified_format_mirror';reason='Actual quotation content and applicable extracted passages compared against preserved structured source fields; no extra narration occurrences.'
                else:
                    status='examined_source_note';reason=comparison['assessment']
            elif occurrences:
                status='examined_extracted';reason='Bounded source occurrences emitted; exclusions and context decisions are separately inventoried.'
            elif path.startswith(('books/units/current/','materials/book-publication-readers/')):
                status='excluded_compiled_mirror';reason='Compiled publication projection of the same Al-Ikhlas reading; no duplicate narration records.'
            elif '/075/' in path or path.endswith('/075.json'):
                status='covered_by_authoritative_occurrence_index';reason='All16 non-Quran source records mapped against original paragraphs:10 quotes extracted,6 summaries excluded.'
            elif path.endswith('/extended/112.json'):
                status='covered_by_sentence_bindings';reason='The four112-00N source files supply exact N-boundings and distinguish Quran/commentary from quoted Hadith.'
            elif path in self.used[language]:
                status='preserved_evidence_or_context';reason='Preserved as exact source evidence, not an independent record family.'
            elif '/heart-reminder/quran/' in path:
                status='examined_quran_and_context';reason='Quran bodies, notes and placements examined; numbered Hadith in Sato companion extracted separately.'
            else:
                status='examined_supporting_metadata';reason='Glossary, source conditions, Quran dependencies, notes, or duplicate reading representation; no independent Hadith occurrence.'
            self.used[language].add(path)
            rows.append({'path':path,'language':language,'git_blob_sha':entry['sha'],'byte_count':entry.get('size'),
                         'locally_verified':True,'sha256':sha256(raw),
                         'status':status,'reason':reason,'extracted_occurrences':len(occurrences),
                         'decision_count':len(decisions)})
        return rows

    def write(self, root):
        root=Path(root)
        markdown_comparisons = self.markdown_comparisons()
        coverage = self.coverage(markdown_comparisons)
        groups=collections.defaultdict(list)
        for record in self.records:
            groups[(record['language'],record['book_key'])].append(record)
        bundles={}
        for language,paths in self.used.items():
            entries=[]
            for path in sorted(paths):
                raw=self.source_bytes(path)
                entries.append({'path':path,'git_blob_sha':self.tree[path]['sha'],
                                'sha256':sha256(raw),'byte_count':len(raw),'encoding':'utf-8',
                                'raw_text':raw.decode('utf-8')})
            bundles[language]={'schema':'hadith-bank-pinned-source-bundle-v1','repository':REPOSITORY,'commit':PIN,
                               'language':language,'files':entries,
                               'preservation':'Encode each raw_text as UTF-8 to reproduce exact original bytes, including CRLF. Hashes are verified against the pinned Git tree.',
                               'source_origin_policy':'Unknown pending owner confirmation; historical original metadata is not rewritten.'}
        manifests=[]
        for (language,book),rows in sorted(groups.items()):
            slug='quran-excerpts-'+language.lower()+'-'+book
            folder=root/'materials'/slug
            dump(folder/'records.json',sorted(rows,key=lambda x:x['id']))
            dump(folder/'source-bundle.json',bundles[language])
            manifest={'schema':'hadith-bank-material-v1','id':slug,'adapter':'records-v1','language':language,
                      'book':book,'edition':EDITION,'source_id':slug,
                      'records':{'path':f'materials/{slug}/records.json','sha256':sha256((folder/'records.json').read_bytes()),'count':len(rows)},
                      'source':{'path':f'materials/{slug}/source-bundle.json','sha256':sha256((folder/'source-bundle.json').read_bytes()),
                                'name':f'{LANGUAGE_NAMES[language]} Quran-study Hadith excerpts — {TITLES.get(book,book)}',
                                'format':'json','url':f'https://github.com/{REPOSITORY}/tree/{PIN}'},
                      'publication':{'authorized':True,'decision':'owner_requested_public_pending_review','decision_date_japan':'2026-11-11'}}
            dump(folder/'manifest.json',manifest);manifests.append(manifest)
        record_counts=collections.Counter(x['language'] for x in self.records)
        types=collections.Counter(x['record_type'] for x in self.records)
        families=collections.Counter(x['source']['family'] for x in self.records)
        unique_refs=collections.defaultdict(set)
        for record in self.records:
            if record['number']['in_book']:
                unique_refs[record['language']].add((record['book_key'],record['number']['in_book']))
        report={'schema':'hadith-bank-quran-extraction-report-v1','source_repository':REPOSITORY,'source_commit':PIN,
                'languages':list(LANGUAGES),'occurrences':len(self.records),'by_language':dict(record_counts),
                'by_type':dict(types),'by_family':dict(families),'material_count':len(manifests),
                'distinct_primary_reference_groups_by_language':{k:len(v) for k,v in unique_refs.items()},
                'unresolved_primary_number_occurrences':sum(not x['number']['in_book'] for x in self.records),
                'counting_note':'Occurrences are bounded source fragments. Repeated Muslim395 fragments and source versions remain separate; distinct reference groups are not independently verified unique-Hadith identities.',
                'source_files':coverage,'decisions':self.decisions,
                'markdown_comparisons':markdown_comparisons,
                'coverage_verification':{
                    'source_files_in_scope':len(coverage),
                    'source_files_hash_verified_and_preserved':len(coverage),
                    'verified_format_mirrors':sum(x['is_format_mirror'] for x in markdown_comparisons),
                    'separate_source_notes':sum(not x['is_format_mirror'] for x in markdown_comparisons),
                    'delimited_quotation_comparisons':sum(len(x.get('quotation_checks',[])) for x in markdown_comparisons),
                    'unaccounted_markdown_quoted_spans':0,
                    'method':'Pinned Git blob and SHA256 verification of all scoped files; actual Markdown quotation comparisons plus separate source-note inspection; emitted words remain exact source slices.',
                    'independent_scholarly_certification':False},
                'scope_limitations':['Full reports summarized only in commentary are not reconstructed or retranslated.',
                                     'Unselected archive parents, comparison variants and alternate-format mirrors are preserved as evidence where used, not added to the Hadith count.',
                                     'Missing primary collection numbers, narrators, translators or Arabic alignments remain unresolved/null.',
                                     'Historical source review/AI flags remain in exact original bundles; current origin is Unknown pending owner confirmation.'],
                'record_types':TYPE_LABELS,'extraction_method':'structured_source_quote','ocr_used':False,
                'records':[{'id':x['id'],'language':x['language'],'record_type':x['record_type'],
                            'book':x['book_key'],'number':x['number']['in_book'],'locator':x['source']['original_locator']} for x in self.records]}
        dump(root/'reports/quran-hadith-extraction.json',report)
        return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--tree',type=Path)
    args=parser.parse_args(argv)
    if bool(args.snapshot) != bool(args.tree):
        parser.error('--snapshot and --tree must be supplied together; omit both to replay bundled sources offline')
    extractor=Extractor(args.snapshot,args.tree) if args.snapshot else Extractor.from_bundles(args.root)
    extractor.fatiha();extractor.ikhlas();extractor.qiyamah();extractor.heart_quran()
    report=extractor.write(args.root)
    print(json.dumps({k:report[k] for k in ('occurrences','by_language','by_type','by_family','material_count','unresolved_primary_number_occurrences')},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
