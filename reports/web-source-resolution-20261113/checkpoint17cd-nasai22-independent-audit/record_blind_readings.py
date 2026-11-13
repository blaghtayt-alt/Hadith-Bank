"""Save only explicitly supplied notes after complete original-field reading."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parent
def record(name,notes):
    source=(ROOT/'input/full-hi-ur-reading-input-44.jsonl').read_bytes()
    extra=(ROOT/'input/additional2636-source-only-input-3.jsonl').read_bytes()
    available={(r['occurrence_id'],r['language']):r for r in map(json.loads,source.splitlines()+extra.splitlines())}
    rows=[]
    for key,note in notes.items():
        r=available[key];assert note.strip() and r['text']
        rows.append({**r,'complete_own_field_read':True,'independent_note':note,
            'primary_candidate_or_semantic_notes_opened_before_reading':False})
    value={'schema':'independent-complete-source-first-reading-batch-v1',
        'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_commit':'17cd396eb858a29162505d545aad556ac73ce9ce',
        'original_reading_input_sha256':hashlib.sha256(source).hexdigest(),'additional_original_input_sha256':hashlib.sha256(extra).hexdigest(),'fields':rows,
        'complete_fields_read':len(rows),'characters_read':sum(r['characters'] for r in rows),
        'utf8_bytes_read':sum(r['utf8_bytes'] for r in rows),'primary_candidate_opened':False}
    p=ROOT/name;assert not p.exists();b=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();p.write_bytes(b)
    print(json.dumps({'path':name,'fields':len(rows),'characters':value['characters_read'],'utf8_bytes':value['utf8_bytes_read'],'sha256':hashlib.sha256(b).hexdigest()}))
