"""Freeze the independently completed original-field readings before candidate inspection."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import shutil

from source_first_notes import NOTES

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'phase17-original-bukhari25-hi-ur'
PIN = 'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d'
EXPECTED = {
    'full-hi-ur-reading-input-50.jsonl': '7e7e10e8d24a857a5261db2219af52816874763c56465163cc358640168acc3e',
    'source-25.jsonl': '8b5454d4143ad95c480fb1b6115f670a6e75ff8c8584f309c4c0cd7d3db600a7',
    'selection.json': 'be655a49396693283f17d0eaac5a6eedebe59e4e67bb923ac41dc89916766ac9',
    'source-verification.json': '4209276da8dc2c2c7cc1c77ff4d902984f4bb1f8419510b0d345f1185c7ef035',
}

def digest(data):
    return sha256(data).hexdigest()

def main():
    output = HERE / 'complete-independent-source-first-readings.json'
    assert not output.exists(), 'Refusing to replace a frozen reading receipt'
    (HERE / 'input').mkdir(exist_ok=True)
    for name, expected in EXPECTED.items():
        raw = (SOURCE / 'input' / name).read_bytes()
        assert digest(raw) == expected, name
        dest = HERE / 'input' / name
        if dest.exists():
            assert dest.read_bytes() == raw
        else:
            dest.write_bytes(raw)
    original = [json.loads(line) for line in (HERE / 'input' / 'full-hi-ur-reading-input-50.jsonl').read_text().splitlines()]
    assert len(original) == 50
    assert len({row['occurrence_id'] for row in original}) == 25
    assert {(r['occurrence_id'], r['language']) for r in original} == set(NOTES)
    fields = []
    for row in original:
        assert row['source_commit'] == PIN
        assert row['complete_own_field_read'] is False
        assert row['semantic_review_status'] == 'prepared_not_read'
        assert len(row['text']) == row['characters']
        assert len(row['text'].encode()) == row['utf8_bytes']
        assert digest(row['text'].encode()) == row['text_sha256']
        fields.append({**row,
            'complete_own_field_read': True,
            'semantic_review_status': 'independent_complete_source_first_reading',
            'source_value_state': 'nonempty',
            'independent_note': NOTES[(row['occurrence_id'], row['language'])],
        })
    assert sum(r['characters'] for r in fields) == 40338
    assert sum(r['utf8_bytes'] for r in fields) == 86636
    assert Counter(r['language'] for r in fields) == {'hi': 25, 'ur': 25}
    result = {
        'schema': 'hadith-bank-independent-complete-original-field-readings-v1',
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'reader': '/root/queue_audit',
        'source_commit': PIN,
        'full_reading_input_sha256': EXPECTED['full-hi-ur-reading-input-50.jsonl'],
        'source_ledger_sha256': EXPECTED['source-25.jsonl'],
        'selection_sha256': EXPECTED['selection.json'],
        'author_source_proof_sha256': EXPECTED['source-verification.json'],
        'notes_script_sha256': digest((HERE / 'source_first_notes.py').read_bytes()),
        'candidate_or_manual_boundaries_opened_before_freeze': False,
        'coordination_context': 'Only the original source input, source metadata, and author preparation/status messages were inspected. All 50 complete original field texts were displayed and independently read before opening any candidate, author semantic notes, selected positions, or proposed boundaries. Initial judgments are preserved for explicit comparison and refinement after candidate inspection.',
        'selected_occurrences': 25,
        'complete_fields_read': 50,
        'languages': {'hi': 25, 'ur': 25},
        'characters_read': 40338,
        'utf8_bytes_read': 86636,
        'unread_other_languages': 'Arabic, English and Roman Urdu sibling fields were not newly read in this independent pass. This is a field expansion of existing registered parents, not a fresh whole-parent exclusion review.',
        'fields': fields,
        'source_http_requests': 0,
        'github_writes': 0,
        'independent_pro_qc': False,
    }
    raw = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
    output.write_bytes(raw)
    print(json.dumps({'path': str(output), 'sha256': digest(raw), 'bytes': len(raw), 'fields': 50, 'characters': 40338, 'utf8_bytes': 86636}, indent=2))

if __name__ == '__main__':
    main()
