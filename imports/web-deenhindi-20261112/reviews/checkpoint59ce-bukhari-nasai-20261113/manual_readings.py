"""Replay the five explicit independent corrections to previously read fields."""
from pathlib import Path
import copy,gzip,json
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    before=json.loads(gzip.decompress((ROOT/'before-independent-manual-notes.json.gz').read_bytes()))
    plan=json.loads((ROOT/'independent-boundary-corrections-v2.json').read_bytes())
    after=copy.deepcopy(before)
    for change in plan['changes']:
        key=change['id'].removeprefix('deenhindi-');lang=change['language']
        assert after[key]['fields'][lang]==change['before']
        after[key]['fields'][lang]=change['after']
    for book in ['bukhari','nasai']:
        payload={'source_read':'Complete own-field readings with the exact independent second-reading amendments enumerated in the adjacent correction receipt.','source_checkpoint':plan['source_checkpoint'],'records':[r for k,r in after.items() if k.startswith(book+':')]}
        (ROOT/('manual-'+book+'.json')).write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
