"""Reopen the already-saved 23 raw/parsed pairs without any network operation."""
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer

sha = lambda value: hashlib.sha256(value).hexdigest()
git = lambda value: hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest()


def verify():
    baseline = (ROOT / 'input/cohort.jsonl').read_bytes()
    proof_bytes = (ROOT / 'source-verification.json').read_bytes()
    assert sha(baseline) == 'cf22bcd083b4cdb70cce62ca81bb73a60571ec62da390d980e8c584bcd65f29e'
    assert sha(proof_bytes) == 'f4ce34db82fc8edaaf1ac38b692087618f50ec338f60c82062f53eef9fae277e'
    proof = json.loads(proof_bytes)
    rows = [json.loads(line) for line in baseline.splitlines()]
    records = {item['occurrence_id']: item for item in proof['records']}
    files = 0
    for saved in rows:
        identity = 'deenhindi-' + saved['collection'] + ':' + saved['number']
        record = records[identity]
        assert record['source_record_sha256'] == sha(importer.json_bytes(saved['source_record']))
        for receipt in record['files']:
            path = ROOT / 'sources' / receipt['path']
            assert not path.is_symlink()
            stored = path.read_bytes()
            plain = gzip.decompress(stored)
            assert len(stored) == receipt['stored_bytes'] and sha(stored) == receipt['stored_sha256']
            assert len(plain) == receipt['bytes'] and sha(plain) == receipt['sha256']
            assert git(stored) == receipt['git_blob_sha1']
            if receipt['kind'] == 'raw':
                body, reference = importer.parse_record(plain, saved['collection'], saved['number'])
                assert body == saved['source_record'] and reference == saved['source_reference_verbatim']
            else:
                expected = {key: saved[key] for key in ('schema', 'collection', 'number', 'snapshot', 'source_reference_verbatim', 'source_record')}
                expected['classification'] = saved['intake_classification']
                assert json.loads(plain) == expected
            files += 1
    assert len(rows) == 23 and files == 46
    return {'result': 'PASS', 'source_commit': proof['source_commit'], 'source_files': files,
            'raw_reparses': len(rows), 'source_http_requests': 0, 'github_writes': 0}


if __name__ == '__main__':
    print(json.dumps(verify(), sort_keys=True))
