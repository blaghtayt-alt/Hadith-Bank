"""Freeze individually authored source-first notes without reading a candidate."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
INPUT = WORK / 'phase19-checkpoint3e574-input-partitions/root-nasai13-ibnmajah7'
READING_SHA = 'bda781923e040e3941516f296430f726147ad1faf4ed03e6c4986d86939ce316'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def data(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def freeze(batch, notes):
    raw = (INPUT / 'full-hi-ur-reading-input-40.jsonl').read_bytes()
    assert sha(raw) == READING_SHA
    original = [json.loads(line) for line in raw.splitlines()]
    rows = {(r['occurrence_id'], r['language']): r for r in original}
    output = []
    for key, language, note in notes:
        source = rows[('deenhindi-' + key, language)]
        text = source['text']
        assert sha(text.encode()) == source['text_sha256']
        assert len(text) == source['characters'] and len(text.encode()) == source['utf8_bytes']
        row = {k:v for k,v in source.items() if k not in ('text','semantic_review_status')}
        row.update(complete_own_field_read=True, candidate_inspected=False,
                   author_semantic_notes_inspected=False, source_first_note=note,
                   reader='/root/checkpoint_inventory')
        output.append(row)
    assert len({(r['occurrence_id'],r['language']) for r in output}) == len(output)
    report = {'schema':'independent-complete-own-field-reading-batch-v1',
              'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
              'source_input_sha256':READING_SHA, 'candidate_inspected':False,
              'author_semantic_notes_inspected':False, 'fields':output,
              'complete_fields':len(output),
              'characters_read':sum(r['characters'] for r in output),
              'utf8_bytes_read':sum(r['utf8_bytes'] for r in output)}
    path=HERE/f'source-first-notes-{batch:02d}.json'
    assert not path.exists(),path
    path.write_bytes(data(report))
    print(json.dumps({'path':str(path),'sha256':sha(path.read_bytes()),'fields':len(output)}))


def aggregate():
    batches=[]; fields=[]
    for path in sorted(HERE.glob('source-first-notes-*.json')):
        raw=path.read_bytes(); report=json.loads(raw)
        assert not report['candidate_inspected'] and not report['author_semantic_notes_inspected']
        batches.append({'path':path.name,'bytes':len(raw),'sha256':sha(raw)})
        fields.extend(report['fields'])
    original=[json.loads(line) for line in (INPUT/'full-hi-ur-reading-input-40.jsonl').read_bytes().splitlines()]
    assert len(fields)==40 and {(r['occurrence_id'],r['language']) for r in fields}=={(r['occurrence_id'],r['language']) for r in original}
    report={'schema':'independent-complete-source-first-reading-receipt-v1',
            'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
            'reader':'/root/checkpoint_inventory','candidate_inspected':False,
            'author_semantic_notes_inspected':False,'source_input_sha256':READING_SHA,
            'source_commit':'3e574b9e7e4dd7cf8bc23232249004a18692c61c',
            'complete_fields_read':40,'characters_read':sum(r['characters'] for r in fields),
            'utf8_bytes_read':sum(r['utf8_bytes'] for r in fields),
            'other_sibling_fields_read':0,'batches':batches,'fields':fields}
    assert (report['characters_read'],report['utf8_bytes_read'])==(10697,21245)
    path=HERE/'complete-independent-source-first-readings.json'
    assert not path.exists()
    path.write_bytes(data(report))
    print(json.dumps({'path':str(path),'sha256':sha(path.read_bytes()),'fields':40}))
