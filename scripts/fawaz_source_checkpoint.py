"""Compact immutable source/quotation fingerprints for Fawaz export comparison."""
import gzip
import hashlib
import json
from pathlib import Path

SCHEMA = 'hadith-bank-fawaz-preservation-snapshot-v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_snapshot(audit, path, source_commit=None):
    """Call only after SourceAudit.run has verified the complete existing export."""
    value = {
        'schema': SCHEMA, 'source_revision': audit.state['revision'],
        'source_commit': source_commit,
        'scope': 'Verified source bytes, complete provider IDs, and every registered own-language quotation; not authenticity certification.',
        'inputs': {key: {name: item[name] for name in ('sha256', 'stored_sha256', 'source_path')}
                   for key, item in audit.inputs.items()},
        'ledger': audit.ledgers, 'registered_language_fingerprints': audit.accepted,
        'counts': {'provider_occurrences': len(audit.ledgers),
                   'registered_occurrences': len(audit.accepted), 'held_occurrences': len(audit.held)},
    }
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()
    path = Path(path)
    stored = gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(stored)
    temporary.replace(path)
    return {'path': str(path), 'sha256': hashlib.sha256(stored).hexdigest(),
            'raw_sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(stored), **value['counts']}


def compare_snapshot(audit, path, expected_sha256):
    require(isinstance(expected_sha256, str) and len(expected_sha256) == 64,
            'A preservation comparison requires the expected snapshot SHA-256')
    path = Path(path)
    stored = path.read_bytes()
    require(hashlib.sha256(stored).hexdigest() == expected_sha256,
            'Preservation snapshot checksum mismatch')
    previous = json.loads(gzip.decompress(stored) if path.suffix == '.gz' else stored)
    require(previous.get('schema') == SCHEMA and previous.get('source_revision') == audit.state['revision'],
            'Preservation snapshot schema or pinned provider revision mismatch')
    for key, old in previous['inputs'].items():
        current = audit.inputs.get(key)
        require(current is not None and all(current.get(name) == old[name]
                for name in ('sha256', 'stored_sha256', 'source_path')),
                'Original source input changed or disappeared: ' + key)
    ledger = previous['ledger']
    details = previous['registered_language_fingerprints']
    counts = previous['counts']
    require(len(ledger) == counts['provider_occurrences'] and len(details) == counts['registered_occurrences']
            and sum(item['status'] == 'held' for item in ledger.values()) == counts['held_occurrences'],
            'Preservation snapshot counts disagree with its inventory')
    require(set(details) == {key for key, item in ledger.items() if item['status'] == 'hadith'},
            'Preservation snapshot registered fingerprints disagree with its ledger')
    missing = sorted(set(ledger) - set(audit.ledgers))
    demoted, changed, transitions = [], [], []
    for identifier, old in ledger.items():
        current = audit.ledgers.get(identifier)
        if current is None:
            continue
        transition = {'id': identifier, 'previous_status': old['status'], 'previous_reason': old['reason'],
                      'current_status': current['status'], 'current_reason': current['reason']}
        if old['status'] == 'held':
            transitions.append(transition)
        elif current['status'] != 'hadith':
            demoted.append(transition)
        if identifier in details and identifier in audit.accepted:
            for version_id, old_version in details[identifier].items():
                new_version = audit.accepted[identifier].get(version_id)
                if old_version != new_version:
                    changed.append({'id': identifier, 'language_version_id': version_id,
                                    'previous': old_version, 'current': new_version})
    return {'comparison_snapshot_sha256': expected_sha256, 'previous_source_commit': previous.get('source_commit'),
            'previous_provider_occurrences': len(ledger), 'previous_registered': len(details),
            'previous_held': len(transitions),
            'previous_held_now_registered': sum(item['current_status'] == 'hadith' for item in transitions),
            'previous_held_still_held': sum(item['current_status'] == 'held' for item in transitions),
            'missing_previous_provider_ids': missing,
            'previous_registered_now_held_count': len(demoted),
            'previous_registered_language_changes_count': len(changed),
            'original_held_reconciliation': transitions,
            'previous_registered_now_held': demoted, 'previous_registered_language_changes': changed,
            'new_provider_ids': sorted(set(audit.ledgers) - set(ledger))}


def require_preserved(comparison):
    require(not comparison.get('missing_previous_provider_ids') and not comparison.get('new_provider_ids')
            and comparison['previous_registered_now_held_count'] == 0
            and comparison['previous_registered_language_changes_count'] == 0,
            'Previously registered source IDs or own-language quotations were changed; publication stopped')
