"""Save only explicitly supplied notes after complete original-field reading."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parent
def record(name,notes):
    source=(ROOT/'input/full-hi-ur-reading-input-32.jsonl').read_bytes()
    available={(r['occurrence_id'],r['language']):r for r in map(json.loads,source.splitlines())}
    rows=[]
    for key,note in notes.items():
        r=available[key];assert note.strip() and r['text']
        rows.append({**r,'complete_own_field_read':True,'independent_note':note,
            'primary_candidate_or_semantic_notes_opened_before_reading':False})
    value={'schema':'independent-complete-source-first-reading-batch-v1',
        'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_commit':'0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a',
        'original_reading_input_sha256':hashlib.sha256(source).hexdigest(),'fields':rows,
        'complete_fields_read':len(rows),'characters_read':sum(r['characters'] for r in rows),
        'utf8_bytes_read':sum(r['utf8_bytes'] for r in rows),'primary_candidate_opened':False}
    p=ROOT/name;assert not p.exists();b=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();p.write_bytes(b)
    print(json.dumps({'path':name,'fields':len(rows),'characters':value['characters_read'],'utf8_bytes':value['utf8_bytes_read'],'sha256':hashlib.sha256(b).hexdigest()}))
