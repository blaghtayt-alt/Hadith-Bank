"""Freeze explicit own-field notes only after the complete source was read."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def save(batch, notes, source_filename='full-hi-ur-reading-input-60.jsonl'):
    assert Path(source_filename).name == source_filename
    source = (ROOT / 'input' / source_filename).read_bytes()
    rows = list(map(json.loads, source.splitlines()))
    by = {(r['occurrence_id'], r['language']): r for r in rows}
    output = []
    for key, value in notes.items():
        row = by[key]
        assert set(value) == {'note', 'provisional'} and value['note'].strip()
        assert value['provisional'] in ('actual_own_report_present', 'needs_other_siblings_before_disposition', 'no_finite_report_in_this_field')
        assert sha(row['text'].encode()) == row['text_sha256']
        result = {k: v for k, v in row.items() if k not in ('text', 'complete_own_field_read', 'semantic_review_status')}
        result.update(complete_own_field_read=True, candidate_authored=False,
                      source_first_note=value['note'], provisional_field_disposition=value['provisional'])
        output.append(result)
    value = {'schema': 'source-first-complete-own-field-reading-notes-v1',
             'reader': '/root/checkpoint_inventory', 'source_commit': '64f4ed50ed6026855237a5d547a86dd03e73f804',
             'source_input_sha256': sha(source),
             'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'candidate_authored': False, 'fields': output}
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    path = ROOT / ('source-first-notes-' + batch + '.json')
    assert not path.exists(), 'A source-first batch is immutable.'
    path.write_bytes(raw)
    print(json.dumps({'path': str(path), 'sha256': sha(raw), 'fields': len(output),
                      'characters': sum(r['characters'] for r in output),
                      'utf8_bytes': sum(r['utf8_bytes'] for r in output)}))
