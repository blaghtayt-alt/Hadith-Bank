"""Shared, offline contracts for candidate preparation and explicit review.

Nothing in this module approves a narration match. Hashes bind the reviewed
occurrence and target; candidates, numbering hints and text similarity do not.
"""
import copy
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata

CONTRACT = 'occurrence-identity-v1'
QUEUE_SCHEMA = 'hadith-bank-counterpart-review-queue-v1'
RAW_ABU_BASE = 'sources/counterparts/reviewed/zh-abu-dawud-yu-2002-doc/2026-11-11'
LANGUAGES = ('arabic', 'english')
HASH = re.compile(r'[0-9a-f]{64}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def object_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def text_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def substantive_quote(value):
    return isinstance(value, str) and sum(character.isalpha() for character in
        unicodedata.normalize('NFKC', value)) >= 32


def local(root, relative):
    root = Path(root).resolve()
    require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative,
            'Invalid review asset path')
    path = PurePosixPath(relative)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == relative,
            'Unsafe review asset path: ' + relative)
    target = root
    for part in path.parts:
        target /= part
        require(not target.is_symlink(), 'Symlink review asset: ' + relative)
    require(target.resolve().is_relative_to(root), 'Review asset escapes its root')
    return target


def descriptor(root, relative):
    raw = local(root, relative).read_bytes()
    return {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def checked_asset(root, item):
    require(isinstance(item, dict) and isinstance(item.get('sha256'), str) and HASH.fullmatch(item['sha256']),
            'Review asset needs a SHA-256 descriptor')
    raw = local(root, item.get('path')).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == item['sha256'] and
            (item.get('bytes') is None or len(raw) == item['bytes']),
            'Review asset checksum mismatch: ' + item['path'])
    return raw


def read_rows(raw, compressed=False):
    if compressed:
        raw = gzip.decompress(raw)
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    require(all(isinstance(row, dict) for row in rows), 'Review rows must be JSON objects')
    return rows


def rows_bytes(rows):
    return gzip.compress(b''.join(canonical(row) + b'\n' for row in rows), compresslevel=9, mtime=0)


def source_locator(record):
    return {'original_file': (record.get('source') or {}).get('original_file'),
            'canonical_record': copy.deepcopy((record.get('source') or {}).get('record_locator')),
            'source_locator': copy.deepcopy(record.get('source_locator')),
            'page': copy.deepcopy(record.get('page'))}


def source_binding(record, text_field=None):
    field = text_field or ('text_translation' if isinstance(record.get('text_translation'), str)
                          and record['text_translation'].strip() else 'text_arabic')
    require(field in ('text_translation', 'text_arabic') and isinstance(record.get(field), str)
            and record[field].strip(), 'Occurrence has no source text to review: ' + str(record.get('id')))
    source = record.get('source') or {}
    result = {'record_id': record.get('id'), 'source_id': record.get('source_id'),
              'language': record.get('language'), 'source_text_field': field,
              'source_text_sha256': text_hash(record[field]), 'source_file_sha256': source.get('sha256'),
              'source_record_sha256': record.get('canonical_record_sha256'),
              'source_locator_sha256': object_hash(source_locator(record))}
    require(all(isinstance(result[key], str) and result[key] for key in ('record_id', 'source_id', 'language')),
            'Occurrence needs stable source identity')
    require(all(isinstance(result[key], str) and HASH.fullmatch(result[key]) for key in
                ('source_text_sha256', 'source_file_sha256', 'source_record_sha256', 'source_locator_sha256')),
            'Occurrence needs verified canonical/source hashes: ' + result['record_id'])
    return result


def validate_source_binding(record, binding):
    expected = source_binding(record, binding.get('source_text_field'))
    require(all(binding.get(key) == value for key, value in expected.items()),
            'Stale review source binding: ' + str(record.get('id')))


def load_source_records(root):
    """Read canonical registered records and public provider snapshots, no build."""
    from material_registry import load_public_materials
    from build_bank_views import public_projection
    root = Path(root).resolve()
    registry = load_public_materials(root)
    records = [record for group in registry['groups'] for record in group]
    catalog = root / 'datasets/hadeethenc/collections.json'
    if catalog.is_file():
        for collection in json.loads(catalog.read_text(encoding='utf-8'))['collections']:
            raw = checked_asset(root, {'path': collection['records_path'], 'sha256': collection['records_sha256']})
            rows = read_rows(raw)
            require(len(rows) == collection['count'], 'Provider source count changed')
            records.extend(public_projection(row, collection, index + 1) for index, row in enumerate(rows))
    require(len({record['id'] for record in records}) == len(records), 'Duplicate source occurrence ID')
    verified = {}
    for record in records:
        source = record['source']
        path, expected = source['original_file'], source['sha256']
        if path not in verified:
            checked_asset(root, {'path': path, 'sha256': expected})
            verified[path] = expected
        require(verified[path] == expected, 'Conflicting original source hashes')
    return records


def raw_abu_dawud_targets(root):
    """Use the full saved Arabic snapshot as candidates, never approvals."""
    root = Path(root).resolve()
    provenance_path = RAW_ABU_BASE + '/provenance.json'
    if not (root / provenance_path).is_file():
        return {}, []
    provenance = json.loads(local(root, provenance_path).read_text(encoding='utf-8'))
    source = provenance['arabic_source']
    raw_path = RAW_ABU_BASE + '/raw/ara-abudawud.json.gz'
    raw = gzip.decompress(local(root, raw_path).read_bytes())
    require(hashlib.sha256(raw).hexdigest() == source['raw_sha256'] and len(raw) == source['raw_bytes'],
            'Saved full Arabic Abu Dawud snapshot changed')
    assets = [descriptor(root, provenance_path), descriptor(root, raw_path)]
    targets = {}
    for position, row in enumerate(json.loads(raw)['hadiths']):
        text = row.get('text')
        if not isinstance(text, str) or not text.strip():
            continue
        number = str(row['hadithnumber'])
        key = 'raw-abu-dawud:' + number
        require(key not in targets, 'Duplicate raw Abu Dawud target identity')
        entry = {'id': key, 'arabic': {
            'text': text, 'text_sha256': text_hash(text), 'source_url': source['url'],
            'source_record_id': number, 'source_name': 'Sunan Abi Dawud — preserved Arabic source entry',
            'source_snapshot': source['provider'] + ' @ ' + source['revision'],
            'translation_origin': 'unknown', 'scope': 'source_entry',
            'includes_isnad_and_compiler_notes': True,
            'references': [{'book_key': 'abu-dawud', 'collection': 'Sunan Abi Dawud',
                'collection_ar': 'سنن أبي داود', 'number': number,
                'numbering_scheme': 'fawazahmed0/hadith-api ara-abudawud hadithnumber',
                'scope': 'main_quote'}]}, 'english': None}
        targets[key] = {'target_key': key, 'entry': entry, 'target_entry_sha256': object_hash(entry),
                        'candidate_only': True, 'input_assets': [raw_path, provenance_path],
                        'source_locator': {'path': raw_path, 'json_pointer': '/hadiths/' + str(position)},
                        'reuse_note': 'Full saved Arabic source entry; number is a candidate locator, not an approved source match.'}
    return targets, assets


def validate_review_evidence(review, record, entry):
    require(isinstance(review, dict) and isinstance(review.get('reviewer'), str) and review['reviewer'].strip(),
            'Review needs the actual reviewer')
    method = review.get('method')
    require(isinstance(method, str) and method.strip() and method.strip().lower() not in
            ('number', 'number_only', 'sequence', 'sequence_only'), 'Number-only acceptance is not allowed')
    require(type(review.get('human_review')) is bool, 'Review human-review state must be explicit')
    evidence = review.get('evidence')
    require(isinstance(evidence, list) and evidence, 'Review needs source and target quotation evidence')
    for item in evidence:
        require(isinstance(item, dict), 'Review evidence must be structured')
        field, language = item.get('source_field'), item.get('target_language')
        require(field in ('text_arabic', 'text_translation') and language in LANGUAGES,
                'Unsupported quotation evidence field')
        left, right = item.get('source_quote'), item.get('target_quote')
        require(substantive_quote(left)
                and (record is None or left in (record.get(field) or '')),
                'Review quotation is absent from exact source text')
        target = entry.get(language) or {}
        require(substantive_quote(right)
                and right in (target.get('text') or ''),
                'Review quotation is absent from exact target text')
        require(isinstance(item.get('rationale'), str) and item['rationale'].strip(),
                'Review evidence needs the narration comparison')
    qualifications = review.get('qualifications', [])
    require(isinstance(qualifications, list) and all(isinstance(item, str) and item.strip() for item in qualifications),
            'Review qualifications must be text notes')


def selected_entry(base_entry, decisions):
    """Apply explicit independent language approvals; never fill a missing one."""
    require(isinstance(decisions, dict) and set(decisions) == set(LANGUAGES),
            'Both Arabic and English need an explicit language decision')
    result = {'id': base_entry['id'], 'arabic': None, 'english': None}
    for language in LANGUAGES:
        decision = decisions[language]
        require(isinstance(decision, dict) and isinstance(decision.get('rationale'), str)
                and decision['rationale'].strip(), 'Language decision needs a rationale')
        action = decision.get('decision')
        require(action in ('approved_text', 'approved_external', 'unavailable', 'unresolved'),
                'Unsupported language approval')
        require(action == 'approved_text' or not ({'scope', 'coverage', 'citation_note'} & set(decision)),
                'Decision-level scope narrowing applies only to approved stored text')
        if action == 'approved_text':
            item = base_entry.get(language)
            require(isinstance(item, dict) and isinstance(item.get('text'), str) and item['text'].strip(),
                    'Approved language text is absent from the pinned target')
            result[language] = copy.deepcopy(item)
            narrowing = {'scope', 'coverage', 'citation_note'} & set(decision)
            if narrowing:
                require(narrowing == {'scope', 'coverage', 'citation_note'} and
                        decision['scope'] == 'source_excerpt' and decision['coverage'] == 'partial' and
                        isinstance(decision['citation_note'], str) and decision['citation_note'].strip(),
                        'Stored language qualification may only narrow to a documented partial source excerpt')
                # Keep the complete immutable text. The narrower scope describes
                # its correspondence to this occurrence, not a rewritten quote.
                result[language].setdefault('source_scope', item.get('scope'))
                result[language]['scope'] = 'source_excerpt'
                result[language]['coverage'] = 'partial'
                previous_note = item.get('citation_note')
                note = decision['citation_note']
                result[language]['citation_note'] = (previous_note + '\n' + note
                    if previous_note and previous_note != note else note)
        elif action == 'approved_external':
            item = decision.get('counterpart') or base_entry.get(language)
            require(isinstance(item, dict) and item.get('text') is None and item.get('text_sha256') is None,
                    'External approval cannot contain or claim quotation text')
            require(isinstance(item.get('source_url'), str) and decision.get('reviewed_url') == item['source_url'],
                    'External approval must name the exact reviewed source URL')
            result[language] = copy.deepcopy(item)
    require(result['arabic'] is not None or result['english'] is not None, 'Accepted mapping supplies no approved language')
    return result


def validate_language_decisions(base_entry, decisions, review, target_key):
    """Check language evidence and a supplemental external page's identity.

Unknown providers need a pinned counterpart target first. A rationale alone
cannot attach an arbitrary URL to an unrelated Arabic source entry.
"""
    selected = selected_entry(base_entry, decisions)
    for language in LANGUAGES:
        decision, item = decisions[language], selected[language]
        if decision['decision'] == 'approved_text':
            require(any(evidence.get('target_language') == language for evidence in review['evidence']),
                    'Stored ' + language + ' approval needs its own content comparison evidence')
        elif decision['decision'] == 'approved_external':
            page = decision.get('page_review') or review.get('official_page_review')
            require(isinstance(page, dict) and page.get('url') == item['source_url'] and
                    page.get(language + '_compared') is True and
                    isinstance(page.get('retrieved_date'), str) and page['retrieved_date'].strip() and
                    isinstance(page.get('retrieval_reference'), str) and page['retrieval_reference'].strip(),
                    'External language approval needs a separately checked exact source page')
            pinned = base_entry.get(language)
            if pinned is not None:
                expected = copy.deepcopy(pinned)
                if expected.get('text') is not None:
                    expected.update(text=None, text_sha256=None, scope='external_source')
                require(item == expected,
                        'External page metadata or qualifications differ from the pinned language target')
            else:
                arabic = base_entry.get('arabic') or {}
                number = arabic.get('source_record_id')
                expected_reference = ('abu-dawud', number)
                pairs = lambda value: {(ref.get('book_key'), str(ref.get('number')))
                    for ref in value.get('references', []) if isinstance(ref, dict)}
                require(language == 'english' and isinstance(number, str) and
                        re.fullmatch(r'[0-9]+[a-z]?', number) and target_key == 'raw-abu-dawud:' + number and
                        item.get('source_url') == 'https://sunnah.com/abudawud:' + number and
                        item.get('source_record_id') == number and
                        len(item.get('references', [])) == 1 and item['references'][0].get('scope') == 'main_quote' and
                        pairs(item) == {expected_reference} and expected_reference in pairs(arabic),
                        'Supplemental external page lacks a supported exact target identity contract')
    return selected
