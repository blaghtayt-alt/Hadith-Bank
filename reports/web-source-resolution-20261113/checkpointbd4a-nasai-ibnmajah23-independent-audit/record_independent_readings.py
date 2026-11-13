"""Freeze explicit independent notes only after complete source-field reading."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def save(batch,notes):
    primary=(ROOT/'input/full-hi-ur-reading-input-46.jsonl').read_bytes()
    additional=(ROOT/'input/additional-nasai2412-originals.jsonl').read_bytes()
    rows=list(map(json.loads,primary.splitlines()))+list(map(json.loads,additional.splitlines()))
    by={(r['occurrence_id'],r['language']):r for r in rows}
    assert len(by)==49
    output=[]
    for key,note in notes.items():
        row=by[key];assert note.strip() and sha(row['text'].encode())==row['text_sha256']
        item={k:v for k,v in row.items() if k not in ['text','complete_own_field_read','semantic_review_status']}
        item.update(complete_own_field_read=True,candidate_viewed=False,author_semantic_notes_viewed=False,
                    independent_source_first_note=note)
        output.append(item)
    value={'schema':'independent-complete-source-first-reading-notes-v1',
        'reader':'/root/checkpoint_inventory','source_commit':'bd4a75695d3c695e98bf8efa5ce07764ac5e2633',
        'source_input_sha256':sha(primary),'additional_input_sha256':sha(additional),
        'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'candidate_viewed':False,'author_semantic_notes_viewed':False,'fields':output}
    data=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    path=ROOT/('independent-readings-'+batch+'.json');assert not path.exists();path.write_bytes(data)
    print(json.dumps({'path':str(path),'sha256':sha(data),'fields':len(output),
        'characters':sum(r['characters'] for r in output),'utf8_bytes':sum(r['utf8_bytes'] for r in output)}))
