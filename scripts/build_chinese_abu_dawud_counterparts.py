#!/usr/bin/env python3
"""Compile explicit Chinese Abu Dawud alignments, never candidate proposals.

All inputs are local and pinned. Original Chinese text and local numbering are
read only. Research English is not redistributed. Arabic source entries retain
their chains and compiler notes; licensed English requires occurrence-level
review in addition to a reviewed Arabic parallel.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3

from counterpart_references import parse_provider_references
from reviewed_counterparts import ReviewedCounterpartResolver


SOURCE_ID = 'zh-abu-dawud-yu-2002-doc'
BASE = 'sources/counterparts/reviewed/' + SOURCE_ID + '/2026-11-11'
MANIFEST = 'sources/counterparts/reviewed/manifest.json'
REVIEW_FILES = ('water-reviewed', 'prayer-early-reviewed', 'prayer-late-reviewed',
                'post-prayer-reviewed', 'jihad-reviewed')
SCHEMA = 'hadith-bank-reviewed-counterpart-sources-v1'
UNRESOLVED_ID = 'zh-abu-dawud:doc-cbff2d2c521e553c:cp251075'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def text_hash(value):
    return digest(value.encode('utf-8'))


def read_json(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def read_rows(path):
    raw = path.read_bytes()
    if path.suffix == '.gz':
        raw = gzip.decompress(raw)
    return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_rows(path, rows):
    data = ''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                   for row in rows).encode('utf-8')
    path.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))


def descriptor(root, relative):
    raw = (root / relative).read_bytes()
    return {'path': relative, 'sha256': digest(raw), 'bytes': len(raw)}


def checked_file(root, relative, expected):
    raw = (root / relative).read_bytes()
    if digest(raw) != expected:
        raise ValueError('Immutable input checksum mismatch: ' + relative)
    return raw


def provider_rows(root, relative, expected):
    checked_file(root, relative, expected)
    path = (root / relative).resolve()
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in connection.execute('SELECT * FROM hadeeths')]
    finally:
        connection.close()
    result = {}
    for row in rows:
        key = str(row['id'])
        if key in result:
            raise ValueError('Ambiguous publisher occurrence: ' + key)
        result[key] = row
    return result


def reference(number, *, reviewed=False):
    return {'book_key': 'abu-dawud', 'collection': 'Sunan Abi Dawud',
            'collection_ar': 'سنن أبي داود', 'number': str(number),
            'numbering_scheme': ('reviewed_source_parallel' if reviewed else
                                 'Sunnah.com global Sunan Abi Dawud numbering'),
            'scope': 'source_quotation' if reviewed else 'main_quote'}


def normalized_review(row, path, line):
    nested = row.get('evidence') or {}
    review = row.get('review') or {}
    identifier = row.get('chinese_record_id') or row.get('source_record_id')
    return {
        'id': identifier,
        'number': str(row['canonical_number']),
        'source_text_sha256': row.get('source_text_sha256') or nested.get('chinese_text_sha256'),
        'arabic_sha256': row.get('arabic_target_sha256') or nested.get('arabic_text_sha256'),
        'anchor': row.get('source_evidence_substring') or nested.get('chinese_anchor'),
        'rationale': row.get('rationale') or nested.get('matching_content_paraphrase_en'),
        'reviewer': row.get('reviewer') or review.get('reviewer'),
        'human_review': row.get('human_review', review.get('human_review')),
        'method': row.get('review_basis') or review.get('method') or row.get('review_type'),
        'relation': row['relation'], 'url': row['reference_url'],
        'qualifications': row.get('qualifications') or [],
        'english_unavailable_reason': row.get('english_unavailable_reason'),
        'audit_path': path, 'audit_row': line,
        'source_local_number': str(row['source_local_number']),
    }


def validate_english_occurrence_review(row, chinese, source_reviews):
    """Bind the separate English compatibility decision to each Chinese text."""
    approved = row.get('approved_chinese_record_ids')
    evidence = row.get('chinese_occurrence_review')
    if (not isinstance(approved, list) or any(not isinstance(key, str) for key in approved) or
            len(approved) != len(set(approved)) or not isinstance(evidence, dict) or
            evidence.get('human_review') is not False or
            not isinstance(evidence.get('reviewer'), str) or not evidence['reviewer'].strip() or
            not isinstance(evidence.get('method'), str) or not evidence['method'].strip()):
        raise ValueError('English needs an explicit occurrence-level compatibility review')
    hashes = evidence.get('source_text_sha256_by_id')
    if not isinstance(hashes, dict) or set(hashes) != set(approved):
        raise ValueError('English occurrence approvals and reviewed hashes differ')
    number = str(row['canonical_number'])
    for identifier in approved:
        if (identifier not in chinese or identifier not in source_reviews or
                source_reviews[identifier][0]['number'] != number or
                hashes[identifier] != text_hash(chinese[identifier]['text']['translation'])):
            raise ValueError('English occurrence approval is stale or outside its reviewed Arabic target')
    return approved


def compile_bundle(root):
    base = root / BASE
    provenance = read_json(base / 'provenance.json')
    original = provenance['original_source']
    raw_chinese = checked_file(root, original['records_path'], original['records_sha256'])
    checked_file(root, original['original_file'], original['sha256'])
    records = [json.loads(line) for line in raw_chinese.decode('utf-8').splitlines() if line.strip()]
    chinese = {row['id']: row for row in records}
    if len(chinese) != 2828 or len(chinese) != len(records):
        raise ValueError('Chinese source occurrence count changed')

    raw_arabic = gzip.decompress((base / 'raw/ara-abudawud.json.gz').read_bytes())
    if digest(raw_arabic) != provenance['arabic_source']['raw_sha256']:
        raise ValueError('Arabic snapshot checksum mismatch')
    arabic = {str(row['hadithnumber']): row['text'] for row in json.loads(raw_arabic)['hadiths']}
    supplements = {}
    for number in ('907', '907b'):
        item = read_json(base / ('raw/supplements/' + number + '.json'))
        if item['id'] != number:
            raise ValueError('Supplement identity mismatch')
        arabic[number], supplements[number] = item['arabic'], item
    capture = read_json(base / 'raw/supplements/907.capture.json')
    bounded = supplements['907']
    extraction = bounded['extraction']
    capture_raw = (base / 'raw/supplements/907.capture.json').read_bytes()
    lo, hi = extraction['source_character_span']
    if (digest(capture_raw) != extraction['raw_capture_sha256'] or
            capture['arabic'][lo:hi] != bounded['arabic'] or 'Grade:' in bounded['arabic']):
        raise ValueError('Supplement907 narration boundary is not verified')

    reviews = defaultdict(list)
    audit_paths = []
    for name in REVIEW_FILES:
        relative = BASE + '/reviews/' + name + '.jsonl.gz'
        audit_paths.append(relative)
        for line, raw in enumerate(read_rows(root / relative), 1):
            row = normalized_review(raw, relative, line)
            source = chinese.get(row['id'])
            target = arabic.get(row['number'])
            if source is None or not target or row['human_review'] is not False:
                raise ValueError('Unrecognized reviewed occurrence: ' + str(row['id']))
            source_text = source['text']['translation']
            if (text_hash(source_text) != row['source_text_sha256'] or
                    text_hash(target) != row['arabic_sha256'] or
                    not row['anchor'] or row['anchor'] not in source_text or
                    not row['rationale'] or not row['reviewer'] or not row['method']):
                raise ValueError('Content review evidence mismatch: ' + row['id'])
            reviews[row['id']].append(row)
    for identifier, rows in reviews.items():
        if len({(r['number'], r['arabic_sha256'], r['url']) for r in rows}) != 1:
            raise ValueError('Conflicting reviewed assignments: ' + identifier)

    unresolved_path = BASE + '/reviews/jihad-unresolved.jsonl.gz'
    unresolved = read_rows(root / unresolved_path)
    if (set(chinese) - set(reviews) != {UNRESOLVED_ID} or len(reviews) != 2827 or
            len(unresolved) != 1 or unresolved[0]['chinese_record_id'] != UNRESOLVED_ID or
            unresolved[0]['source_text_sha256'] != text_hash(chinese[UNRESOLVED_ID]['text']['translation'])):
        raise ValueError('Accepted/unresolved source coverage changed; review explicitly')

    he = provenance['authorized_english']
    english_rows = provider_rows(root, he['english_database'], he['english_database_sha256'])
    he_arabic = provider_rows(root, he['arabic_database'], he['arabic_database_sha256'])
    english_review_path = BASE + '/reviews/hadeethenc-english-reviewed.jsonl.gz'
    english_reviews = read_rows(root / english_review_path)
    approved_english = defaultdict(list)
    omitted_english = []
    for row in english_reviews:
        number, identifier = str(row['canonical_number']), str(row['provider_id'])
        item, arabic_row = english_rows[identifier], he_arabic[identifier]
        if (row['human_review'] is not False or row['relation'] not in ('full_parallel', 'source_excerpt') or
                not row.get('reviewer') or not row.get('rationale') or
                row['source_url'] != 'https://hadeethenc.com/en/browse/hadith/' + identifier or
                row['arabic_target_sha256'] != text_hash(arabic[number]) or
                row['hadeethenc_arabic_sha256'] != text_hash(item['hadeeth_ar']) or
                row['english_text_sha256'] != text_hash(item['hadeeth']) or
                item['hadeeth_ar'] != arabic_row['hadeeth'] or item['ar_version'] != arabic_row['version']):
            raise ValueError('English parallel source/version mismatch: ' + identifier)
        publisher_refs = parse_provider_references(arabic_row.get('reference') or '')
        if publisher_refs != row['references']:
            raise ValueError('English publisher bibliography mismatch: ' + identifier)
        approved_ids = validate_english_occurrence_review(row, chinese, reviews)
        has_abu_dawud_attribution = ('أبو داود' in (arabic_row.get('attribution') or '') or
                                     'أبي داود' in (arabic_row.get('attribution') or ''))
        if not publisher_refs and not has_abu_dawud_attribution:
            omitted_english.append({'canonical_number': number, 'provider_id': identifier,
                                    'reason': 'No numbered publisher reference or explicit Abu Dawud attribution.'})
            continue
        for source_id in approved_ids:
            approved_english[source_id].append((row, item, publisher_refs))

    entries, mappings = {}, []
    decisions = []
    counts = Counter()
    for source in records:
        identifier = source['id']
        if identifier not in reviews:
            continue
        rows = reviews[identifier]
        primary = rows[0]
        number, url = primary['number'], primary['url']
        qualifications = list(dict.fromkeys(note for r in rows for note in r['qualifications']))
        entry_id = 'abu-dawud:' + number
        arabic_source = {
            'text': arabic[number], 'text_sha256': text_hash(arabic[number]),
            'source_url': url, 'translation_origin': 'unknown',
            'references': [reference(number)], 'scope': 'source_entry',
            'source_name': 'Sunan Abi Dawud — Arabic source entry',
            'source_record_id': number,
            'source_snapshot': ('Individual source-page Arabic capture, 2026-11-11' if number in supplements else
                                'fawazahmed0/hadith-api ara-abudawud @ ' + provenance['arabic_source']['revision']),
            'includes_isnad_and_compiler_notes': True,
        }
        english_source = None
        choices = approved_english.get(identifier, [])
        if choices:
            # All choices must be explicitly accepted for this source occurrence.
            # Select one for display; retain all versions and decisions in the audit.
            choices.sort(key=lambda c: (c[0]['relation'] != 'full_parallel', not bool(c[2]), int(c[0]['provider_id'])))
            review, item, publisher_refs = choices[0]
            provider_id = str(review['provider_id'])
            entry_id += ':hadeethenc:' + provider_id
            refs = [{**r, 'scope': 'source_quotation'} for r in publisher_refs]
            citation_note = None
            if not refs:
                refs = [reference(number, reviewed=True)]
                citation_note = ('The collection number is a reviewed Arabic-source cross-reference; '
                                 'HadeethEnc’s bibliography does not supply a hadith number.')
            english_source = {
                'text': item['hadeeth'], 'text_sha256': text_hash(item['hadeeth']),
                'source_url': review['source_url'], 'translation_origin': 'human',
                'source_name': 'HadeethEnc.com — English ' + he['english_version'],
                'source_snapshot': 'HadeethEnc English ' + he['english_version'] + '; Arabic revision ' + str(item['ar_version']),
                'source_record_id': provider_id, 'references': refs,
                'publisher_references': publisher_refs, 'citation_note': citation_note,
                'reviewed_parallel_reference': reference(number, reviewed=True),
                'scope': 'full_narration' if review['relation'] == 'full_parallel' else 'source_excerpt',
                'publisher_database_path': he['english_database'],
                'publisher_database_sha256': he['english_database_sha256'],
                'source_arabic_version': item['ar_version'],
                'bibliography_arabic_version_aligned': True,
                'parallel_review': {'reviewer': review['reviewer'], 'human_review': False,
                                    'rationale': review['rationale'], 'audit_path': english_review_path,
                                    'chinese_occurrence_review': review['chinese_occurrence_review']},
            }
            qualifications.extend('English parallel: ' + note for note in review.get('qualifications', []))
            decisions.append({'record_id': identifier, 'selected_provider_id': provider_id,
                              'accepted_provider_ids': [str(choice[0]['provider_id']) for choice in choices],
                              'selection': 'Prefer full reviewed report, numbered publisher references, then stable provider ID.'})
            counts['english_text_occurrences'] += 1
        elif number != '2319' and not any(row['english_unavailable_reason'] for row in rows):
            entry_id += ':english-source'
            english_source = {
                'text': None, 'text_sha256': None, 'source_url': url,
                'translation_origin': 'unknown', 'references': [reference(number)],
                'scope': 'external_source', 'source_record_id': number,
                'source_name': 'Sunnah.com — linked English source page',
                'source_snapshot': 'External source link; English text is not stored in the bank',
            }
            counts['english_external_link_occurrences'] += 1
        else:
            reasons = [r['english_unavailable_reason'] for r in rows if r['english_unavailable_reason']]
            qualifications.extend(reasons or ['The paired English at source2319 is a different narration; no English counterpart is assigned.'])
            counts['english_unavailable_among_linked'] += 1
        entry = {'id': entry_id, 'arabic': arabic_source, 'english': english_source}
        if entry_id in entries and entries[entry_id] != entry:
            raise ValueError('Target entry metadata conflict: ' + entry_id)
        entries[entry_id] = entry
        evidence = [{
            'review_asset': row['audit_path'], 'review_row': row['audit_row'],
            'source_local_number': row['source_local_number'], 'source_quote': row['anchor'],
            'narration_comparison': row['rationale'], 'reviewer': row['reviewer'],
            'method': row['method'],
        } for row in rows]
        mappings.append({
            'record_id': identifier, 'source_id': SOURCE_ID, 'language': 'zh-CN',
            'source_text_sha256': primary['source_text_sha256'],
            'source_file_sha256': original['sha256'], 'target_id': entry_id,
            'target_text_sha256': {'arabic': arabic_source['text_sha256'],
                                   'english': english_source['text_sha256'] if english_source else None},
            'relation': 'source_excerpt' if any(r['relation'] == 'source_excerpt' for r in rows) else 'same_narration',
            'review': {'status': 'verified', 'reviewer': '; '.join(dict.fromkeys(r['reviewer'] for r in rows)),
                       'method': 'Individual narration-content comparison; original source and target bytes bound by SHA-256. See per-review evidence and qualifications.',
                       'evidence': evidence, 'qualifications': list(dict.fromkeys(qualifications)),
                       'human_review': False, 'independent_authenticity_certification': False,
                       'translation_fidelity_certified': False},
        })
    coverage = {
        'schema': 'hadith-bank-chinese-abu-dawud-counterpart-coverage-v1',
        'source_records': len(records), 'accepted_source_occurrences': len(mappings),
        'arabic_text_occurrences': len(mappings), 'unresolved_source_occurrences': len(unresolved),
        'distinct_arabic_source_entries': len({row[0]['number'] for row in reviews.values()}),
        'distinct_display_entries': len(entries), **dict(counts),
        'additional_agreeing_reviews': sum(len(rows) - 1 for rows in reviews.values()),
        'qualified_source_occurrences': sum(bool(row['review']['qualifications']) for row in mappings),
        'source_ids_and_text_unchanged': True, 'human_review': False,
        'independent_scholarly_certification': False, 'unresolved': unresolved,
        'english_parallels_not_used_without_reference': omitted_english,
    }
    write_rows(base / 'entries.jsonl.gz', [entries[key] for key in sorted(entries)])
    write_rows(base / 'mappings.jsonl.gz', mappings)
    write_rows(base / 'english-display-decisions.jsonl.gz', decisions)
    write_json(base / 'coverage.json', coverage)
    source_paths = audit_paths + [unresolved_path, english_review_path,
        BASE + '/reviews/hadeethenc-english-unresolved.jsonl.gz',
        BASE + '/reviews/review-union-audit.json', BASE + '/provenance.json',
        BASE + '/raw/ara-abudawud.json.gz', BASE + '/raw/supplements/907.json',
        BASE + '/raw/supplements/907.capture.json', BASE + '/raw/supplements/907b.json',
        BASE + '/english-display-decisions.jsonl.gz', he['english_database'], he['arabic_database'],
        original['original_file'], original['records_path']]
    bundle = {
        'id': SOURCE_ID + '-parallels-2026-11-11', 'provider': 'hadith-bank-reviewed-source-parallels',
        'source_name': 'Sunan Abi Dawud source parallels for the supplied Chinese edition',
        'source_snapshot': '2026-11-11 reviewed alignment; source-specific versions retained per language',
        'publication': provenance['publication'],
        'entries': descriptor(root, BASE + '/entries.jsonl.gz'),
        'mappings': descriptor(root, BASE + '/mappings.jsonl.gz'),
        'coverage': descriptor(root, BASE + '/coverage.json'),
        'source_assets': [descriptor(root, path) for path in source_paths],
    }
    manifest_path = root / MANIFEST
    manifest = read_json(manifest_path) if manifest_path.exists() else {'schema': SCHEMA, 'bundles': []}
    if manifest.get('schema') != SCHEMA:
        raise ValueError('Unrecognized existing reviewed registry')
    manifest['bundles'] = [b for b in manifest['bundles'] if b.get('id') != bundle['id']] + [bundle]
    write_json(manifest_path, manifest)
    # Exercise the same immutable source validation as production.
    resolver = ReviewedCounterpartResolver(root)
    for source in records:
        normalized = {'id': source['id'], 'source_id': SOURCE_ID, 'language': 'zh-CN',
                      'text_translation': source['text']['translation'], 'source': {'sha256': original['sha256']}}
        value = resolver.for_record(normalized)
        if source['id'] == UNRESOLVED_ID:
            if value is not None:
                raise ValueError('Unresolved source acquired an assignment')
        elif not value or value['status'] != 'reviewed_parallel':
            raise ValueError('Production resolver rejected compiled mapping: ' + source['id'])
    checked_file(root, original['records_path'], original['records_sha256'])
    print(json.dumps(coverage, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    compile_bundle(args.root.resolve())
