#!/usr/bin/env python3
"""PROTOTYPE: propose source-local abbreviated-report links; never import them.

Reads a previously validated Fawaz export. Every held occurrence gets a ledger
disposition. Positive candidates require their own bounded Arabic reference,
source order/section, corroborating chain wording and a backward path to an
independently registered Prophetic report. IDs, grades and bodies are never
copied from the antecedent. The JSON output is deliberately not an importer
decision schema; candidates require source review before integration.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

REVISION = 'df57907be35291c91ad6a6691180e22ca9920784'
IMPORT = Path('imports/web-fawaz-20261112')
MARKS = re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]')
TRANSMISSION = r'(?:و?حدثنا|و?حدثني|و?اخبرنا|و?اخبرني|و?انبانا|و?انباني|سمعت|عن)'
CHAIN_START = re.compile(r'^\s*(?:و?حدث(?:نا|ني)|و?اخبر(?:نا|ني)|و?عن)\b')
CHAIN_WORD = re.compile(r'\b' + TRANSMISSION + r'\s+')
NAME_STOP = re.compile(r'\s+(?:' + TRANSMISSION + r'|قال|قالا|قالوا|يحدث|ذكر|بهذا|في هذا|مثله|نحوه|ان|انه|كلهم|كلاهما)\b')
SPEECH_START = re.compile(r'\bقال(?:ا|وا|ت)?\s+(?!' + TRANSMISSION + r'\b)')
RELATIVE = re.compile(r'\b(?:(?:بهذا|في هذا|بمثل هذا)\s+الاسناد|بهذا\s+الحديث|باسناده|'
                      r'ب?مثله|نحوه|(?:مثل|بمثل|بمعني|معني|نحو)\s+حديث)\b')
NAMED_REFERENCE = re.compile(r'(?:مثل|بمثل|بمعني|معني|نحو)\s+حديث\s+([^،؛:.!?"«»“”]{1,75})')
CONTENT_REFERENCE = re.compile(r'بهذا\s+الحديث|ب?مثله|نحوه|(?:مثل|بمثل|بمعني|معني|نحو)\s+حديث|وزاد|لم\s+يذكر')
EN_CONTENT_REFERENCE = re.compile(r'\b(?:this|same|similar|above|previous)\s+(?:hadith|hadeeth|tradition|narration)\b', re.I)
ATTRIBUTION_NEGATION = re.compile(r'لم\s+يرفع|لا\s+يرفع|لم\s+يسنده|لم\s+يذكر\s+(?:النبي|رسول\s+الله)|'
                                r'موقوف|لا\s+ادري\s+ا?عن\s+النبي')
GENERIC_NAMES = {'رجل', 'رجلين', 'شيخ', 'بعضهم', 'غير واحد', 'ابيه', 'ابو', 'ابي', 'عمه',
                 'امه', 'جده', 'الناس', 'النبي', 'رسول الله', 'الله', 'الثقة', 'فلان'}
COMMON_SINGLE = {'محمد', 'احمد', 'علي', 'حسن', 'سعيد', 'يحيي', 'مالك', 'ابراهيم', 'عبد'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def typed(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def normalize(text):
    result, offsets = [], []
    table = str.maketrans('أإآىٱ', 'ااايا')
    for position, char in enumerate(text):
        if MARKS.fullmatch(char) or unicodedata.category(char) == 'Cf':
            continue
        char = char.translate(table)
        if char.isspace():
            if result and result[-1] == ' ':
                continue
            char = ' '
        result.append(char)
        offsets.append(position)
    return ''.join(result), offsets


def source_evidence(node, normalized_span, normalized_offsets, role):
    a, b = normalized_span
    start = normalized_offsets[a] + node['span'][0]
    end = normalized_offsets[b - 1] + node['span'][0] + 1
    while end < len(node['text']) and unicodedata.combining(node['text'][end]):
        end += 1
    return {'edition': node['edition'], 'typed_hadithnumber': node['id'],
            'source_position': node['position'], 'source_raw_sha256': node['source_sha256'],
            'source_text_sha256': digest(node['text'].encode()), 'span': [start, end],
            'text': node['text'][start:end], 'role': role, **node.get('source_info', {})}


def name_key(value):
    value = value.strip(' \t\r\n-ـ،؛:.()')
    value = re.sub(r'\bابو\b', 'ابي', value)
    return ' '.join(value.split())


def chain_names(normalized):
    stop = SPEECH_START.search(normalized)
    prefix = normalized[:stop.start()] if stop else normalized
    result = []
    markers = list(CHAIN_WORD.finditer(prefix))
    for index, match in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(prefix)
        value = re.split(r'[،؛:.!?"«»“”]', prefix[match.end():end], 1)[0]
        cut = NAME_STOP.search(value)
        value = value[:cut.start()] if cut else value
        value = value.split(' - ', 1)[0]
        leading = len(value) - len(value.lstrip(' -ـ،؛:.()'))
        value = value.strip(' -ـ،؛:.()')
        key = name_key(value)
        if (not key or key in GENERIC_NAMES or len(key) < 3 or len(key.split()) > 12 or
                re.search(r'[^\u0621-\u063a\u0641-\u064a\u066e-\u06d3\u06fa-\u06fc ]', key)):
            continue
        start = match.end() + leading
        result.append({'key': key, 'span': [start, start + len(value)]})
    return result


def comparable(left, right, aliases):
    if left == right:
        return True, None
    alias = aliases.get((left, right))
    if alias:
        return True, alias
    # A literal qualified chain label contains the shorter label; preserve
    # this as corroborating wording, never as a global person-identity merge.
    short, long = sorted((left, right), key=len)
    qualified_short = (len(short.split()) >= 2 and len(short) >= 7) or (short.startswith('ال') and len(short) >= 5)
    if qualified_short and long.startswith(short + ' '):
        remainder = long[len(short) + 1:]
        if remainder.startswith(('ال', 'بن ', 'ابن ')):
            return True, None
    return False, None


def propose(nodes, negatives=None, aliases=None):
    """Pure source-order pass. Returns held-ID ledger; never changes any node."""
    negatives, aliases = negatives or {}, aliases or {}
    if (len({node['id'] for node in nodes}) != len(nodes) or
            any(a['position'] >= b['position'] for a, b in zip(nodes, nodes[1:]))):
        raise ValueError('Source positions and typed identities must be unique and ordered')
    previous, resolved, ledger = None, {}, []
    for node in nodes:
        key = node['id']
        own = node.get('quotation', '')
        normalized, offsets = normalize(own)
        direct = node.get('independent_prophetic', False)
        if direct:
            resolved[key] = {'root': key, 'path': [key], 'direct': True,
                             'root_evidence': node.get('independent_attribution_evidence')}
        elif (node.get('status') == 'hadith' and previous is not None and
              node.get('reviewed_relative_parent') == previous['id'] and previous['id'] in resolved and
              node.get('reviewed_relative_parent_span') == previous.get('span')):
            # Reuse an already validated, hash-bound Arabic relation. It is
            # still a dependency, never a newly invented independent anchor.
            prior = resolved[previous['id']]
            resolved[key] = {**prior, 'path': [key] + prior['path'], 'direct': False}
        if node.get('status') != 'held':
            previous = node
            continue
        item = {'provider_book': node['book'], 'provider_edition': node['edition'],
                'typed_hadithnumber': key, 'source_position': node['position'],
                'source_raw_sha256': node['source_sha256'],
                'source_text_sha256': digest(node['text'].encode()),
                **node.get('source_info', {}),
                'canonical_identity_inferred': False, 'antecedent_text_inserted': False,
                'status': 'unresolved', 'reason': 'no_bounded_arabic_reading'}
        marker = RELATIVE.search(normalized) if own else None
        if key in negatives:
            item.update(reason='retained_negative_source_review', negative_review=negatives[key])
        elif own and ATTRIBUTION_NEGATION.search(normalized):
            item['reason'] = 'source_explicitly_qualifies_or_denies_prophetic_attribution'
        elif not own:
            pass
        elif not marker or not CHAIN_START.search(normalized):
            item['reason'] = 'no_explicit_relative_transmission_frame'
        elif re.search(r'["«“]', normalized[:marker.start()]):
            item['reason'] = 'relative_phrase_inside_prior_quoted_or_mixed_context'
        elif not CONTENT_REFERENCE.search(normalized) and not (
                EN_CONTENT_REFERENCE.search(node.get('english_quotation', '')) and node.get('english_reference_evidence')):
            item['reason'] = 'chain_only_reference_needs_content_relation_evidence'
        elif (previous is None or previous['book'] != node['book'] or previous['edition'] != node['edition'] or
              node['section'] in (None, 0) or previous['section'] != node['section']):
            item['reason'] = 'no_preceding_source_in_same_declared_section'
        elif not previous.get('quotation', '').strip():
            item['reason'] = 'preceding_source_reading_absent_or_unbounded'
        else:
            parent = previous
            pn, po = normalize(parent.get('quotation', ''))
            cnames, pnames = chain_names(normalized[:marker.start()]), chain_names(pn)
            explicit = NAMED_REFERENCE.search(normalized)
            if explicit:
                value = re.split(r'\s+(?:واسناده|الا|غير|وزاد|في|مع)\b', explicit.group(1), 1)[0].strip()
                if value:
                    cnames.append({'key': name_key(value), 'span': [explicit.start(1), explicit.start(1) + len(value)],
                                   'explicit_named_reference': True})
            matches = []
            # The continuation must reach the child's final named chain link
            # (or its explicitly named reference), not just a shared collector.
            for child_name in cnames[-1:]:
                for parent_name in pnames:
                    same, alias = comparable(child_name['key'], parent_name['key'], aliases)
                    if same and (len(child_name['key'].split()) > 1 or child_name['key'] not in COMMON_SINGLE):
                        matches.append((child_name, parent_name, alias))
            item['antecedent'] = {'typed_hadithnumber': parent['id'], 'source_position': parent['position'],
                                  'source_text_sha256': digest(parent['text'].encode()),
                                  'source_raw_sha256': parent['source_sha256'],
                                  'same_declared_section': node['section'], **parent.get('source_info', {})}
            if not matches:
                item['reason'] = 'named_chain_not_corroborated'
            elif parent['id'] not in resolved:
                item['reason'] = 'antecedent_not_independently_established_or_resolved'
            elif len(resolved[parent['id']]['path']) >= 32:
                item['reason'] = 'reference_depth_requires_separate_review'
            else:
                # Prefer the latest named chain anchor or an explicit named
                # reference; never use a bare shared identifier/number.
                child_name, parent_name, alias = max(matches,
                    key=lambda pair: (pair[0].get('explicit_named_reference', False), pair[0]['span'][0]))
                item.update(status='positive_candidate', reason='explicit_relative_wording_and_named_source_chain',
                    quotation_span=node['span'], source_order='previous_source_row_not_numeric_adjacency',
                    reference_evidence=source_evidence(node, marker.span(), offsets, 'own_relative_reference'),
                    child_chain_evidence=source_evidence(node, child_name['span'], offsets, 'own_chain_label'),
                    antecedent_chain_evidence=source_evidence(parent, parent_name['span'], po, 'antecedent_chain_label'),
                    independent_terminal=resolved[parent['id']]['root'],
                    independent_terminal_evidence=resolved[parent['id']]['root_evidence'],
                    dependency_path=[key] + resolved[parent['id']]['path'])
                if alias:
                    item['source_local_alias_evidence'] = alias
                if not CONTENT_REFERENCE.search(normalized):
                    item['additional_content_reference_language'] = 'en'
                    item['additional_content_reference'] = node.get('english_reference_evidence')
                resolved[key] = {'root': item['independent_terminal'], 'path': item['dependency_path'], 'direct': False,
                                 'root_evidence': item['independent_terminal_evidence']}
        ledger.append(item)
        previous = node
    return ledger


def single_span(spans):
    values = spans.get('quotation_spans', [spans['quotation']] if 'quotation' in spans else [])
    return values[0] if len(values) == 1 and values[0][1] > values[0][0] else None


def registered_arabic_attribution(node, classification):
    """Use only an independently established attribution in this Arabic field.

    Newer explicit-report classifications retain original offsets, while legacy
    classifications retain normalized evidence. A reviewed Arabic quotation is
    eligible only when it has no relative-source dependency of its own. An
    English/Urdu/Bengali decision never supplies the missing Arabic attribution.
    """
    own = node.get('quotation', '')
    if classification.get('classification') != 'hadith' or not own or not node.get('span'):
        return None
    reason = classification.get('reason')
    normalized, offsets = normalize(own)
    if reason == 'explicit_prophetic_attribution' and classification.get('evidence_language') == 'ar':
        needle = normalize(classification.get('evidence', ''))[0]
        start = normalized.find(needle) if needle else -1
        if start < 0:
            return None
        proof = source_evidence(node, (start, start + len(needle)), offsets,
                                'independent_registered_prophetic_attribution')
        method = classification.get('method')
    elif reason == 'explicit_source_report_attribution' and classification.get('source_language') == 'ara':
        span = classification.get('span')
        if (not isinstance(span, list) or len(span) != 2 or
                not all(type(v) is int for v in span) or not 0 <= span[0] < span[1] <= len(own) or
                own[span[0]:span[1]] != classification.get('text')):
            return None
        start, end = node['span'][0] + span[0], node['span'][0] + span[1]
        proof = {'edition': node['edition'], 'typed_hadithnumber': node['id'],
                 'source_position': node['position'], 'source_raw_sha256': node['source_sha256'],
                 'source_text_sha256': digest(node['text'].encode()), 'span': [start, end],
                 'text': node['text'][start:end], 'role': 'independent_registered_prophetic_attribution',
                 **node.get('source_info', {})}
        method = classification.get('rule')
    elif reason == 'reviewed_explicit_source_attribution':
        decision = classification.get('evidence') or {}
        if (decision.get('provider_edition') != node['edition'] or decision.get('source_reference') or
                decision.get('typed_hadithnumber') != node['id'] or
                decision.get('source_text_sha256') != digest(node['text'].encode()) or
                decision.get('quotation_spans') != [node['span']]):
            return None
        proof = {'edition': node['edition'], 'typed_hadithnumber': node['id'],
                 'source_position': node['position'], 'source_raw_sha256': node['source_sha256'],
                 'source_text_sha256': digest(node['text'].encode()), 'span': node['span'],
                 'text': own, 'role': 'independent_registered_prophetic_attribution',
                 **node.get('source_info', {})}
        method = 'hash_bound_reviewed_own_arabic_quotation'
    else:
        return None
    return {**proof, 'classification_method': method, 'classification_reason': reason,
            'independent_of_relative_reference_chain': True, 'independent_authenticity_assessment': False}


def load_export(root):
    state = json.loads((root / IMPORT / 'state.json').read_text())
    if state['revision'] != REVISION:
        raise ValueError('Unexpected source revision')
    sources, spans, statuses, negatives = {}, {}, {}, {}
    for key, desc in state['inputs'].items():
        if not key.startswith(('editions/ara-', 'editions/eng-')):
            continue
        saved = (root / desc['path']).read_bytes()
        raw = gzip.decompress(saved)
        if digest(saved) != desc['stored_sha256'] or digest(raw) != desc['sha256']:
            raise ValueError('Source snapshot checksum mismatch: ' + key)
        sources[Path(key).stem] = {'rows': json.loads(raw)['hadiths'], 'descriptor': desc}
    for path in (root / IMPORT / 'classification').glob('*.jsonl.gz'):
        book = path.name.removesuffix('.jsonl.gz')
        with gzip.open(path, 'rt') as stream:
            for line in stream:
                item = json.loads(line)
                statuses[(book, item['typed_hadithnumber'])] = item['classification']
    for path in (root / IMPORT / 'held').glob('*.jsonl.gz'):
        book = path.name.removesuffix('.jsonl.gz')
        with gzip.open(path, 'rt') as stream:
            for line in stream:
                item = json.loads(line)
                for prefix in ('ara', 'eng'):
                    versions = item['source_versions'].get(prefix, [])
                    if len(versions) == 1:
                        spans[(book, item['typed_hadithnumber'], prefix)] = single_span(versions[0]['text_spans'])
    for path in (root / 'materials').glob('fawaz-*/manifest.json'):
        manifest = json.loads(path.read_text())
        descriptor = manifest['records']
        hasher = hashlib.sha256()
        with (root / descriptor['path']).open('rb') as stream:
            for line in stream:
                hasher.update(line)
                record = json.loads(line)
                identity = record['source']['provider_identity']
                book, ident = identity['book'], identity['typed_hadithnumber']
                for version in record['language_versions']:
                    for prefix, language in [('ara', 'ar'), ('eng', 'en')]:
                        if (version['language'] == language and version.get('text') and
                                version['source'].get('provider_edition') == prefix + '-' + book and
                                version['source'].get('source_report_count', 1) in (None, 1)):
                            spans[(book, ident, prefix)] = single_span(version['source']['text_spans'])
        if hasher.hexdigest() != descriptor['sha256']:
            raise ValueError('Canonical source span index changed: ' + descriptor['path'])
    return sources, spans, statuses


def audit(root, negatives_path=None):
    sources, spans, statuses = load_export(root)
    negative_reviews = {}
    if negatives_path:
        data = json.loads(negatives_path.read_text())
        for item in data.get('negative_reference_reviews', []):
            source = item['source']
            saved = sources[source['provider_edition']]
            row = saved['rows'][source['source_position']]
            if (saved['descriptor']['sha256'] != source['source_raw_sha256'] or
                    digest(row['text'].encode()) != source['source_text_sha256'] or
                    typed(row['hadithnumber']) != source['typed_hadithnumber']):
                raise ValueError('A retained negative source review no longer matches its exact source')
            negative_reviews[(source['provider_book'], source['typed_hadithnumber'])] = item
    ledger, source_hashes = [], {}
    for edition, source in sorted(sources.items()):
        if not edition.startswith('ara-'):
            continue
        book = edition[4:]
        source_hashes[edition] = source['descriptor']['sha256']
        english_source = sources.get('eng-' + book, {})
        english = {typed(row['hadithnumber']): (position, row)
                   for position, row in enumerate(english_source.get('rows', []))}
        duplicates = collections.Counter(typed(row['hadithnumber']) for row in source['rows'])
        nodes, aliases = [], {}
        for position, row in enumerate(source['rows']):
            ident = typed(row['hadithnumber'])
            classification = statuses.get((book, ident), {})
            span = spans.get((book, ident, 'ara')) if duplicates[ident] == 1 else None
            own = row['text'][span[0]:span[1]] if span else ''
            node = {'book': book, 'edition': edition, 'id': ident, 'position': position,
                'section': row.get('reference', {}).get('book'), 'text': row['text'],
                'span': span, 'quotation': own, 'source_sha256': source['descriptor']['sha256'],
                'status': classification.get('classification'), 'independent_prophetic': False,
                'source_info': {'source_url': source['descriptor']['url'],
                    'source_path': source['descriptor']['path'],
                    'source_json_pointer': f'/hadiths/{position}/text'}}
            attribution = registered_arabic_attribution(node, classification)
            if attribution:
                node['independent_prophetic'] = True
                node['independent_attribution_evidence'] = attribution
            decision = classification.get('evidence')
            if isinstance(decision, dict) and decision.get('source_reference'):
                relation = decision['source_reference']
                parent = relation.get('parent_source', {})
                parent_position = parent.get('source_position')
                if (decision.get('provider_edition') == edition and decision.get('typed_hadithnumber') == ident and
                        decision.get('source_text_sha256') == digest(row['text'].encode()) and
                        decision.get('quotation_spans') == [span] and
                        relation.get('relation') == 'source_explicit_previous_report_variant' and
                        parent.get('provider_edition') == edition and type(parent_position) is int and
                        parent_position + 1 == position and parent_position >= 0 and
                        parent.get('typed_hadithnumber') == typed(source['rows'][parent_position]['hadithnumber']) and
                        parent.get('source_text_sha256') == digest(source['rows'][parent_position]['text'].encode()) and
                        parent.get('source_raw_sha256') == source['descriptor']['sha256']):
                    node['reviewed_relative_parent'] = parent['typed_hadithnumber']
                    node['reviewed_relative_parent_span'] = single_span({'quotation_spans':parent['quotation_spans']})
            enspan = spans.get((book, ident, 'eng'))
            if enspan and ident in english:
                enposition, enrow = english[ident]
                entext = enrow['text']
                node['english_quotation'] = entext[enspan[0]:enspan[1]]
                match = EN_CONTENT_REFERENCE.search(node['english_quotation'])
                if match:
                    node['english_reference_evidence'] = {'edition': 'eng-' + book,
                        'typed_hadithnumber': ident, 'source_position': enposition,
                        'source_raw_sha256': english_source['descriptor']['sha256'],
                        'source_path': english_source['descriptor']['path'],
                        'source_url': english_source['descriptor']['url'],
                        'source_json_pointer': f'/hadiths/{enposition}/text',
                        'source_text_sha256': digest(entext.encode()),
                        'span': [enspan[0] + match.start(), enspan[0] + match.end()], 'text': match.group()}
            nodes.append(node)
            normalized, offsets = normalize(row['text'])
            match = re.search(r'\bابن شهاب الزهري\b', normalized)
            if match:
                full_node = {**node, 'span': [0, len(row['text'])]}
                evidence = source_evidence(full_node, match.span(), offsets, 'explicit_same_edition_full_name')
                aliases[('ابن شهاب', 'الزهري')] = evidence
                aliases[('الزهري', 'ابن شهاب')] = evidence
        local_negatives = {key[1]: value for key, value in negative_reviews.items() if key[0] == book}
        ledger.extend(propose(nodes, local_negatives, aliases))
    indexed = {(item['provider_book'], item['typed_hadithnumber']) for item in ledger}
    for (book, ident), classification in statuses.items():
        if classification['classification'] == 'held' and (book, ident) not in indexed:
            ledger.append({'provider_book': book, 'typed_hadithnumber': ident,
                'status': 'unresolved', 'reason': 'no_unique_saved_arabic_source_row',
                'canonical_identity_inferred': False, 'antecedent_text_inserted': False})
    expected = {key for key, value in statuses.items() if value['classification'] == 'held'}
    actual = {(item['provider_book'], item['typed_hadithnumber']) for item in ledger}
    if actual != expected or len(ledger) != len(expected):
        raise ValueError('Held-ID accounting is incomplete or contains duplicate dispositions')
    summary = {'schema': 'hadith-bank-relative-reference-audit-v1', 'status': 'proposal_only',
        'source_revision': REVISION, 'held_ids_accounted': len(ledger),
        'positive_candidates': sum(item['status'] == 'positive_candidate' for item in ledger),
        'by_reason': dict(collections.Counter(item['reason'] for item in ledger)),
        'by_book': {book: dict(collections.Counter(item['status'] for item in ledger if item['provider_book'] == book))
                    for book in sorted({item['provider_book'] for item in ledger})},
        'source_sha256s': source_hashes,
        'scope': 'Source-reference proposals only. No import, text completion, identity merging, authenticity assessment or publication decision.'}
    return ledger, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--negative-reviews', type=Path)
    args = parser.parse_args()
    ledger, summary = audit(args.root.resolve(), args.negative_reviews)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'all-held-ids.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in ledger))
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == '__main__':
    main()
