#!/usr/bin/env python3
"""Prepare a bounded offline review queue; never approve or publish matches."""
import argparse
from collections import Counter, defaultdict
import copy
import json
from pathlib import Path
import re
import shutil
import tempfile
import unicodedata

from counterpart_review import (QUEUE_SCHEMA, LANGUAGES, canonical, descriptor, load_source_records,
    local, object_hash, raw_abu_dawud_targets, require, rows_bytes, source_binding, source_locator,
    source_text, text_hash)
from resolve_counterparts import (CounterpartResolver, normalize_quote, source_references,
                                  reference_key, narration_reference_scope)
from citation_search import reference_pair
from counterpart_coverage import availability_for
from reviewed_counterparts import MANIFEST as REVIEWED_MANIFEST


def arabic_key(text):
    # Candidate comparison only; never modifies retained quotation bytes.
    return normalize_quote(text).translate(str.maketrans({'ی': 'ي', 'ک': 'ك'}))


def words(text):
    plain = ''.join(character for character in unicodedata.normalize('NFKC', text or '')
                    if unicodedata.category(character)[0] != 'M')
    return {word for token in re.findall(r'\w+', plain) if 4 <= len(word := arabic_key(token)) <= 50}


def printed_arabic_quote_anchors(text):
    """Keep exact, balanced source quotation spans as unapproved review hints."""
    pairs = {'«': '»', '“': '”', '‹': '›', '「': '」'}
    stack, spans = [], []
    for index, character in enumerate(text):
        if character in pairs:
            stack.append((character, index))
        elif stack and character == pairs[stack[-1][0]]:
            opening, start = stack.pop()
            spans.append((start + 1, index, opening + character))
    anchors = []
    for start, end, delimiters in sorted(set(spans)):
        quote = text[start:end]
        normalized = arabic_key(quote)
        letters = sum(unicodedata.category(character).startswith('L') and
                      'ARABIC' in unicodedata.name(character, '') for character in normalized)
        if letters >= 64:
            anchors.append({'field': 'text_arabic', 'start': start, 'end': end,
                'text': quote, 'sha256': text_hash(quote), 'delimiters': delimiters,
                'normalized': normalized, 'arabic_letters': letters})
    return anchors


def arabic_key_positions(text):
    """Map candidate-only normalization back to untouched target characters."""
    normalized, positions = [], []
    for index, character in enumerate(text):
        value = unicodedata.normalize('NFKC', character).casefold().translate(
            str.maketrans({'ی': 'ي', 'ک': 'ك'}))
        for letter in value:
            if (letter.isspace() or letter == '\u0640' or
                    unicodedata.category(letter)[0] in ('P', 'M', 'Z') or
                    unicodedata.category(letter) == 'Cf'):
                continue
            normalized.append(letter)
            positions.append(index)
    return ''.join(normalized), positions


def collect_targets(root, records, resolver, profile='all'):
    targets, assets = {}, {}
    for path, sha in resolver.assets.items():
        # The registry can append bundles; immutable target files remain pinned.
        if path == REVIEWED_MANIFEST:
            continue
        assets[path] = {'path': path, 'sha256': sha, 'bytes': local(root, path).stat().st_size}
    for bundle_id, bundle in resolver.reviewed.bundles.items():
        for identifier, original in bundle['entries'].items():
            key = 'reviewed:' + bundle_id + ':' + identifier
            entry = copy.deepcopy(original)
            entry['id'] = key
            targets[key] = {'target_key': key, 'entry': entry, 'target_entry_sha256': object_hash(entry),
                'candidate_only': True, 'input_assets': [bundle['metadata']['entries']['path']],
                'reuse_note': 'Existing review belongs to its original occurrences. New occurrences need their own language approvals.'}
    for identifier, item in resolver.entries.items():
        key = 'hadeethenc:' + identifier
        entry = {'id': key}
        for language, code in (('arabic', 'ar'), ('english', 'en')):
            text = item[language]
            refs = copy.deepcopy(item['references'])
            for reference in refs:
                reference.setdefault('scope', 'main_quote')
                reference.setdefault('numbering_scheme', 'HadeethEnc publisher bibliography')
            entry[language] = {'text': text, 'text_sha256': text_hash(text),
                'source_url': 'https://hadeethenc.com/' + code + '/browse/hadith/' + identifier,
                'source_record_id': identifier, 'source_name': 'HadeethEnc.com',
                'source_snapshot': 'Pinned English export ' + str(resolver.manifest.get('english_version')) +
                    '; Arabic revision ' + str(item['ar_version']),
                'translation_origin': 'human' if language == 'english' else 'unknown',
                'scope': 'full_narration', 'references': refs,
                **({'reference_status': 'not_supplied_by_source'} if not refs else {})}
        targets[key] = {'target_key': key, 'entry': entry, 'target_entry_sha256': object_hash(entry),
            'candidate_only': True, 'input_assets': [resolver.manifest['english_database']['path'],
                resolver.manifest['arabic_database']['path']],
            'reuse_note': 'Pinned publisher occurrence and version; source compatibility still requires review.'}
    if profile in ('all', 'abu-dawud'):
        raw_targets, raw_assets = raw_abu_dawud_targets(root)
        targets.update(raw_targets)
        assets.update({item['path']: item for item in raw_assets})
    return targets, assets


class CandidateIndex:
    def __init__(self, targets, records, resolver):
        self.targets = targets
        self.exact, self.references, self.tokens = defaultdict(set), defaultdict(set), defaultdict(set)
        self.quote_references, self.target_quote_references = defaultdict(set), {}
        self.arabic = {}
        self.arabic_positions = {}
        self.translation_donors = defaultdict(set)
        self.identity_donors = defaultdict(set)
        for key, target in targets.items():
            entry = target['entry']
            text = (entry.get('arabic') or {}).get('text') or ''
            normalized = arabic_key(text)
            if normalized:
                self.arabic[key] = normalized
                self.exact[normalized].add(key)
                for token in words(text):
                    self.tokens[token].add(key)
            for language in LANGUAGES:
                for reference in (entry.get(language) or {}).get('references') or []:
                    pair = reference_key(reference)
                    if pair:
                        self.references[pair].add(key)
            # A quoted Arabic anchor needs this target's own narration-level
            # reference, not a number inherited from an unrelated English link.
            quote_refs = set()
            for reference in (entry.get('arabic') or {}).get('references') or []:
                if (not narration_reference_scope(reference) or
                        reference.get('scope') not in (None, 'main_quote', 'source_citation',
                                                      'source_quotation', 'publisher_entry')):
                    continue
                pair = reference_pair(reference)
                if pair:
                    quote_refs.add(pair)
                    self.quote_references[pair].add(key)
            self.target_quote_references[key] = quote_refs
        for record in records:
            reviewed = resolver.reviewed.for_record(record)
            if not reviewed or reviewed['status'] != 'reviewed_parallel':
                continue
            binding = source_binding(record)
            for bundle_id, mapping in resolver.reviewed.mappings.get(record['id'], []):
                key = 'reviewed:' + bundle_id + ':' + mapping['target_id']
                if key not in targets:
                    continue
                self.identity_donors[object_hash(binding)].add(key)
                translation = record.get('text_translation')
                if isinstance(translation, str) and translation.strip():
                    self.translation_donors[(record['language'], text_hash(translation))].add(key)

    def candidates(self, record, limit=8):
        found = {}

        def add(key, score, reason):
            if key not in self.targets:
                return
            item = found.setdefault(key, {'target_key': key, 'score': score, 'reasons': [],
                'target_entry_sha256': self.targets[key]['target_entry_sha256'], 'candidate_only': True,
                'source_compatibility_verified': False})
            item['score'] = max(score, item['score'])
            if reason not in item['reasons']:
                item['reasons'].append(reason)

        for key in self.identity_donors.get(object_hash(source_binding(record)), []):
            add(key, 100, 'same_occurrence_binding_previously_reviewed; new language approval still required')
        translation = record.get('text_translation')
        if isinstance(translation, str):
            for key in self.translation_donors.get((record['language'], text_hash(translation)), []):
                add(key, 80, 'exact_translation_in_another_reviewed_occurrence; identity not inherited')
        arabic = record.get('text_arabic') or ''
        normalized = arabic_key(arabic)
        for key in self.exact.get(normalized, []):
            add(key, 95, 'normalized_Arabic_equal; occurrence review required')
        if len(normalized) >= 32:
            token_sets = sorted((self.tokens[token] for token in words(arabic) if token in self.tokens), key=len)
            choices = set().union(*token_sets[:3]) if token_sets else set()
            for key in sorted(choices)[:1000]:
                target = self.arabic[key]
                if normalized in target:
                    add(key, 90, 'source_Arabic_excerpt_in_target; boundaries and narrator require review')
                elif len(target) >= 64 and target in normalized:
                    add(key, 70, 'target_Arabic_excerpt_in_source; boundaries require review')
        references = {reference_pair(reference) for reference in source_references(record)} - {None}
        choices = set().union(*(self.quote_references.get(pair, set()) for pair in references)) if references else set()
        for anchor in printed_arabic_quote_anchors(arabic) if choices else []:
            matched = [key for key in sorted(choices) if key in self.arabic and
                       self.arabic[key].count(anchor['normalized']) == 1]
            for key in matched:
                if key not in self.arabic_positions:
                    target_text = self.targets[key]['entry']['arabic']['text']
                    self.arabic_positions[key] = arabic_key_positions(target_text)
                target_normalized, positions = self.arabic_positions[key]
                if target_normalized != self.arabic[key]:
                    continue
                offset = target_normalized.index(anchor['normalized'])
                start, end = positions[offset], positions[offset + len(anchor['normalized']) - 1] + 1
                target_text = self.targets[key]['entry']['arabic']['text']
                target_quote = target_text[start:end]
                if arabic_key(target_quote) != anchor['normalized']:
                    continue
                add(key, 88, 'source_printed_Arabic_quote_anchor_with_shared_reference; candidate only, narrator and complete language coverage require review')
                found[key].setdefault('quoted_arabic_anchors', []).append({
                    'source': {name: value for name, value in anchor.items() if name != 'normalized'},
                    'source_arabic_sha256': text_hash(arabic),
                    'target': {'language': 'arabic', 'start': start, 'end': end,
                               'text': target_quote, 'sha256': text_hash(target_quote)},
                    'shared_explicit_references': [list(pair) for pair in sorted(
                        references.intersection(self.target_quote_references[key]))],
                    'reference_compatible_matching_targets': len(matched),
                    'target_anchor_occurrence_count': 1,
                    'literal_anchor_in_target': anchor['text'] in target_text,
                    'source_context_outside_anchor_preserved': True,
                    'candidate_only': True, 'source_compatibility_verified': False,
                    'coverage_decision': 'not_approved; inspect all source clauses and each target language'})
        for reference in source_references(record):
            for key in self.references.get(reference_key(reference), []):
                add(key, 40, 'shared_cited_reference; number alone cannot approve')
        if record.get('book_key') == 'abu-dawud' and str(record.get('language', '')).startswith('zh'):
            number = (record.get('number') or {}).get('source_entry_id')
            if number is not None:
                add('raw-abu-dawud:' + str(number), 5,
                    'Chinese_source_local_number_hint_only; standard_number_identity_not_established')
        return sorted(found.values(), key=lambda item: (-item['score'], item['target_key']))[:limit]


def availability(record, value):
    return availability_for({**record, 'counterparts': value})


def write_queue(output, queue, targets, manifest):
    output = Path(output).absolute()
    require(not output.is_symlink() and not any(parent.is_symlink() for parent in output.parents),
            'Review output cannot be a symlink')
    allowed = {'.counterpart-review-generated', 'manifest.json', 'queue.jsonl.gz', 'targets.jsonl.gz'}
    if output.exists():
        require(output.is_dir() and (not any(output.iterdir()) or
                (output / '.counterpart-review-generated').is_file()), 'Refusing to replace a non-generated review folder')
        require({item.name for item in output.iterdir()} <= allowed,
                'Keep manual reviews outside the generated review queue folder')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.review-queue-', dir=output.parent))
    previous = None
    try:
        (staging / 'queue.jsonl.gz').write_bytes(rows_bytes(queue))
        (staging / 'targets.jsonl.gz').write_bytes(rows_bytes(targets))
        manifest['queue'] = descriptor(staging, 'queue.jsonl.gz')
        manifest['targets'] = descriptor(staging, 'targets.jsonl.gz')
        (staging / 'manifest.json').write_bytes(canonical(manifest) + b'\n')
        (staging / '.counterpart-review-generated').write_text('Candidate preparation only; no accepted links.\n')
        if output.exists():
            previous = Path(tempfile.mkdtemp(prefix='.review-previous-', dir=output.parent))
            previous.rmdir()
            output.rename(previous)
        try:
            staging.rename(output)
        except BaseException:
            if previous:
                previous.rename(output)
                previous = None
            raise
        if previous:
            shutil.rmtree(previous)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def prepare_review(root, output='.work/counterpart-review', records=None, source_id=None,
                   include_resolved=False, profile='all', max_candidates=8, include_targets=None):
    root = Path(root).resolve()
    require(profile in ('all', 'abu-dawud', 'registered'), 'Unknown candidate profile')
    require(type(max_candidates) is int and 1 <= max_candidates <= 50, 'Candidate limit must be between 1 and 50')
    records = load_source_records(root) if records is None else list(records)
    require(len({row['id'] for row in records}) == len(records), 'Duplicate preparation occurrence IDs')
    selected = [record for record in records if source_id is None or record['source_id'] == source_id]
    require(source_id is None or selected, 'Registered source ID not found: ' + str(source_id))
    resolver = CounterpartResolver(root, records)
    targets, assets = collect_targets(root, records, resolver, profile)
    index = CandidateIndex(targets, records, resolver)
    queue, used, counts, sources = [], set(include_targets or []), Counter(), Counter()
    for record in sorted(selected, key=lambda row: row['id']):
        value = record.get('counterparts') if 'counterparts' in record else resolver.for_record(record)
        current = availability(record, value)
        requested = [language for language in LANGUAGES if current[language] == 'missing']
        counts['inspected_occurrences'] += 1
        if not include_resolved and not requested:
            counts['already_linked_occurrences'] += 1
            continue
        binding = source_binding(record)
        candidates = index.candidates(record, max_candidates)
        used.update(item['target_key'] for item in candidates)
        queue.append({**binding, 'status': 'candidate', 'requested_languages': requested,
            'existing_availability': current, 'existing_match_status': (value or {}).get('status'),
            'existing_match_method': (value or {}).get('match_method'),
            'source_locator': source_locator(record),
            'source_preview': source_text(record, binding['source_text_field'])[:240],
            'source_book_key': record.get('book_key'), 'source_edition': record.get('edition'),
            'source_number': copy.deepcopy(record.get('number')), 'candidates': candidates})
        sources[record['source_id']] += 1
        counts['candidate_occurrences' if candidates else 'occurrences_without_candidate'] += 1
        for language in requested:
            counts[language + '_missing_occurrences'] += 1
    require(used <= set(targets), 'An explicitly requested candidate target is unavailable')
    manifest = {'schema': QUEUE_SCHEMA, 'status': 'candidates_only', 'publication_ready': False,
        'matching_is_not_approval': True, 'new_translations_created': False,
        'source_id': source_id, 'profile': profile, 'max_candidates': max_candidates,
        'counts': {**dict(counts), 'queued_occurrences': len(queue), 'candidate_targets': len(used),
                   'available_candidate_targets': len(targets), 'accepted_by_this_preparation': 0},
        'by_source_id': dict(sorted(sources.items())),
        'input_assets': [assets[key] for key in sorted(assets)],
        'review_instruction': 'Each occurrence requires content evidence and separate Arabic/English decisions. Numbers, similarity, and previous occurrence approvals are candidates only.'}
    destination = Path(output)
    if not destination.is_absolute():
        destination = root / destination
    require(destination.resolve() != root and not root.is_relative_to(destination.resolve()), 'Unsafe review output directory')
    write_queue(destination, queue, [targets[key] for key in sorted(used)], manifest)
    return {'schema': QUEUE_SCHEMA, 'status': 'candidates_only', **manifest['counts'],
            'output': str(destination), 'manifest': str(destination / 'manifest.json'),
            'queue_bytes': manifest['queue']['bytes'], 'target_bytes': manifest['targets']['bytes']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', default='.work/counterpart-review')
    parser.add_argument('--source-id')
    parser.add_argument('--profile', choices=('all', 'abu-dawud', 'registered'), default='all')
    parser.add_argument('--max-candidates', type=int, default=8)
    parser.add_argument('--include-resolved', action='store_true')
    parser.add_argument('--include-target', dest='include_targets', action='append')
    args = vars(parser.parse_args(argv))
    try:
        result = prepare_review(**args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Counterpart preparation failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
