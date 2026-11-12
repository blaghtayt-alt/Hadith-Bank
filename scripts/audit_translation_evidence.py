"""Audit primary translation occurrences against a reviewed, byte-bound ledger.

This tool never infers origin from the old display policy, style, OCR or an
unsupported historical flag. A ledger decision is a reviewer assertion; the
hash checks only bind it to the cited evidence and exact translation bytes.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

SCHEMA = 'hadith-bank-translation-evidence-ledger-v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def evidence_path(root, relative):
    require(isinstance(relative, str) and bool(relative), 'Evidence path required')
    candidate = Path(relative)
    require(not candidate.is_absolute() and all(p not in ('', '.', '..') for p in relative.split('/')),
            'Evidence path must be relative and traversal-free')
    resolved = (root / candidate).resolve()
    require(resolved.is_relative_to(root) and resolved.is_file(), 'Evidence file missing or outside root')
    return resolved


def audit(records, ledger, root):
    """Return counts and IDs for primary non-Arabic translations only.

    Arabic originals, empty primary translations, language versions and linked
    counterparts are separate scopes. Every decision must match exactly one
    occurrence and exact UTF-8 translation. Unknown means no accepted decision.
    """
    root = Path(root).resolve()
    require(isinstance(ledger, dict) and ledger.get('schema') == SCHEMA, 'Invalid ledger schema')
    entries = ledger.get('decisions')
    require(isinstance(entries, list), 'Ledger decisions must be an array')
    decisions = {}
    for entry in entries:
        require(isinstance(entry, dict), 'Invalid decision')
        key = entry.get('occurrence_id')
        require(isinstance(key, str) and bool(key.strip()) and key not in decisions,
                'Decision needs a unique occurrence ID')
        require(entry.get('classification') in ('ai', 'human'), 'Only evidence-backed ai/human decisions are stored')
        for field in ('language', 'translation_sha256', 'evidence_path', 'evidence_sha256',
                      'evidence_locator', 'assertion', 'reviewer'):
            require(isinstance(entry.get(field), str) and bool(entry[field].strip()), 'Missing ' + field)
        path = evidence_path(root, entry['evidence_path'])
        require(digest(path.read_bytes()) == entry['evidence_sha256'], 'Evidence hash mismatch: ' + key)
        decisions[key] = entry
    seen, matched = set(), set()
    counts = Counter({'ai': 0, 'human': 0, 'unknown': 0})
    excluded = Counter({'arabic_primary': 0, 'missing_primary_translation': 0})
    identified = {'ai': [], 'human': []}
    for record in records:
        require(isinstance(record, dict), 'Each record must be an object')
        key = record.get('id')
        require(isinstance(key, str) and bool(key.strip()) and key not in seen,
                'Records require unique occurrence IDs')
        seen.add(key)
        language = record.get('language')
        require(isinstance(language, str) and bool(language.strip()), 'Record language required: ' + key)
        if language.lower().replace('_', '-').split('-')[0] == 'ar':
            excluded['arabic_primary'] += 1
            continue
        translation = record.get('text_translation')
        if not isinstance(translation, str) or not translation.strip():
            excluded['missing_primary_translation'] += 1
            continue
        entry = decisions.get(key)
        if entry:
            require(entry['language'] == language, 'Decision language mismatch: ' + key)
            require(entry['translation_sha256'] == digest(translation.encode('utf-8')),
                    'Translation hash mismatch: ' + key)
            matched.add(key)
            classification = entry['classification']
            identified[classification].append(key)
        else:
            classification = 'unknown'
        counts[classification] += 1
    require(matched == set(decisions), 'Ledger contains unmatched or out-of-scope decisions')
    return {'schema': 'hadith-bank-translation-evidence-audit-v1',
            'scope': 'primary non-Arabic translation occurrences with nonblank text',
            'counterparts_and_language_versions_included': False,
            'counts': dict(counts), 'excluded': dict(excluded),
            'evidence_backed_occurrence_ids': {k: sorted(v) for k, v in identified.items()},
            'note': 'Hash binding validates identity and integrity, not the truth of the reviewer assertion.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', required=True, help='Reader projection JSONL')
    parser.add_argument('--ledger', required=True, help='Reviewed evidence ledger JSON')
    parser.add_argument('--root', required=True, help='Repository root for evidence paths')
    parser.add_argument('--include-ids', action='store_true', help='Include evidence-backed occurrence IDs')
    args = parser.parse_args()
    records_path = Path(args.records)
    ledger_path = Path(args.ledger)
    with records_path.open(encoding='utf-8') as stream:
        result = audit((json.loads(line) for line in stream if line.strip()),
                       json.loads(ledger_path.read_text(encoding='utf-8')), args.root)
    with records_path.open('rb') as stream:
        result['records_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
    result['ledger_sha256'] = digest(ledger_path.read_bytes())
    if not args.include_ids:
        result.pop('evidence_backed_occurrence_ids')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
