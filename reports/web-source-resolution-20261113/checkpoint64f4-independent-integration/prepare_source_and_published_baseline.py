"""Offline exact102 source preparation; no review decisions or network operations."""
from pathlib import Path, PurePosixPath
import collections, datetime, gzip, hashlib, json, sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
COMMIT = '64f4ed50ed6026855237a5d547a86dd03e73f804'
REVIEWS = Path('imports/web-deenhindi-20261112/reviews')
QUEUE = 'reports/web-source-resolution-20261113/current-original3942-priority-field-queue.jsonl.gz'
COHORT_SHA = 'ba7da40f01485df7d0010e2d2660f6f5ee773389eb986aafe8e00a22b5bb9ab3'
MONITOR = WORK / 'phase22-successor-acquisition-monitor'
EVIDENCE = MONITOR / 'complete-held-evidence'
PARTITIONS = WORK / 'phase23-checkpoint64f4-input-partitions'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews, unique_pairs

def sha(b): return hashlib.sha256(b).hexdigest()
def git(kind, b): return hashlib.sha1(kind.encode() + b' ' + str(len(b)).encode() + b'\0' + b).hexdigest()
def enc(v): return (json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def read(p):
    p = Path(p); b = p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix == '.gz' else b, object_pairs_hook=unique_pairs)
def lines(p):
    p = Path(p); b = p.read_bytes(); b = gzip.decompress(b) if p.suffix == '.gz' else b
    return [json.loads(l, object_pairs_hook=unique_pairs) for l in b.splitlines() if l.strip()]
def safe(p):
    p = str(p); v = PurePosixPath(p)
    assert p and not v.is_absolute() and '..' not in v.parts and '\\' not in p
    return v
def bind(p):
    b = Path(p).read_bytes()
    return {'bytes': len(b), 'sha256': sha(b), 'git_blob_sha1': git('blob', b)}
def identity(r): return r.get('occurrence_id', r.get('id')) or 'deenhindi-' + r['collection'] + ':' + str(r['number'])
def immutable(p, b):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists(): assert p.read_bytes() == b, ('Frozen output differs', str(p))
    else: p.write_bytes(b)

def prepare_source():
    target = ROOT / 'prepared-source-cohort.json'
    assert not target.exists(), 'Frozen source preparation must not be rewritten.'
    cohort_path = MONITOR / 'next-review-cohort/held-source-records.jsonl'
    assert bind(cohort_path)['sha256'] == COHORT_SHA
    rows = lines(cohort_path); sources = {identity(r): r for r in rows}
    keys = {k.removeprefix('deenhindi-') for k in sources}
    assert len(rows) == len(sources) == 102
    assert collections.Counter(r['collection'] for r in rows) == {'bukhari':30, 'muslim':13, 'nasai':15, 'ibnmajah':13, 'abudawud':13, 'tirmidhi':18}
    input_path = MONITOR / 'next-review-cohort/input-manifest.json'
    assert bind(input_path)['sha256'] == 'b7f9cc79ce5d85e8fdfd300c5e4db5100b2eeb9d008b97df7b76dcb2ca32d4f7'
    partition_path = PARTITIONS / 'partition-audit.json'
    assert bind(partition_path)['sha256'] == '8da3752c265de27648b43a6e29d3bcff73a27df311f7690740b7aae30801d30b'
    partition = read(partition_path)
    assert partition['source_commit'] == COMMIT and partition['source_cohort_sha256'] == COHORT_SHA
    groups, all_ids = [], set()
    for item in partition['partitions']:
        p = PARTITIONS / item['partition']
        mp = p / 'input-delivery-manifest.json'
        assert bind(mp)['sha256'] == item['manifest_sha256']
        manifest = read(mp); assert manifest['source_commit'] == COMMIT
        for f in manifest['files']:
            fp = Path(f['local_path']); assert fp.is_file() and not fp.is_symlink()
            receipt = bind(fp)
            assert all(receipt[k] == f[k] for k in receipt)
        group = lines(p / 'cohort.jsonl'); ids = {identity(r) for r in group}
        assert len(group) == len(ids) == item['count'] and not ids & all_ids
        assert all(sources[identity(r)] == r for r in group)
        all_ids |= ids
        groups.append({'name': item['partition'], 'input_manifest': bind(mp),
            'source_cohort': bind(p / 'cohort.jsonl'), 'ids': sorted(ids)})
    assert all_ids == set(sources)
    manifest_path = EVIDENCE / 'evidence-manifest.json'
    assert bind(manifest_path)['sha256'] == 'c2abcc3fb29dbada01127031b902026f785be51b225d590407d8917465a80a0c'
    evidence = read(manifest_path); assert evidence['saved_head'] == COMMIT
    for key, name in [('held_source_records','held-source-records.jsonl'), ('held_state_entries','held-state-entries.json')]:
        receipt = bind(EVIDENCE / name)
        assert all(receipt[k] == evidence[key][k] for k in ['bytes','sha256'])
    checkpoint = read(EVIDENCE / 'checkpoint.json')
    assert checkpoint['saved_head'] == COMMIT
    assert checkpoint['selected_held_entries'] == checkpoint['held_entries_total'] == 273
    assert checkpoint['remaining_held_queue_count'] == 0
    assert checkpoint['original_bounded_selected_held_entries'] == 250
    assert checkpoint['original_bounded_remaining_held_queue_count'] == 23
    held = {identity(r): r for r in lines(EVIDENCE / 'held-source-records.jsonl')}
    entries = read(EVIDENCE / 'held-state-entries.json')
    prior_monitor = WORK / 'phase21-successor-acquisition-monitor'
    old_path = prior_monitor / 'held-evidence/held-source-records.jsonl'
    old171 = {identity(r): r for r in lines(old_path)}
    assert len(held) == len(entries) == 273 and len(old171) == 171
    assert not set(old171) & set(sources)
    assert set(held) == set(old171) | set(sources)
    assert all(held[k] == v for k,v in old171.items())
    assert all(held[k] == v for k,v in sources.items())
    state_path = MONITOR / 'saved-checkpoint/state.json'
    state_receipt = checkpoint['input_receipts']['imports/web-deenhindi-20261112/state.json']
    assert all(bind(state_path)[k] == state_receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    state = read(state_path); assert len(state['imported']) == 18570
    prior_path = prior_monitor / 'saved-checkpoint/state.json'
    prior_checkpoint = read(prior_monitor / 'held-evidence/checkpoint.json')
    assert prior_checkpoint['saved_head'] == '17cd396eb858a29162505d545aad556ac73ce9ce'
    prior_receipt = prior_checkpoint['input_receipts']['imports/web-deenhindi-20261112/state.json']
    assert all(bind(prior_path)[k] == prior_receipt[k] for k in ['bytes','sha256','git_blob_sha1'])
    prior = read(prior_path)
    assert len(prior['imported']) == 18089 and not keys & set(prior['imported'])
    files = []
    for oid, row in sources.items():
        key = oid.removeprefix('deenhindi-'); entry = entries[key]
        assert entry == state['imported'][key]
        assert entry['collection'] == row['collection'] and entry['number'] == row['number']
        assert entry['parsed']['path'] == row['parsed_path']
        assert sha(importer.json_bytes(row['source_record'])) == evidence['source_record_sha256'][key]
        for kind, desc in [('raw',row['snapshot']), ('parsed',entry['parsed'])]:
            relative = str(safe(desc['path'])); p = EVIDENCE / 'sources' / relative
            assert p.is_file() and not p.is_symlink()
            b = bind(p); given = evidence['files'][relative]
            assert all(b[k] == given[k] for k in b)
            plain = importer.checked_bytes(EVIDENCE / 'sources', desc)
            if kind == 'raw':
                body, ref = importer.parse_record(plain, row['collection'], row['number'])
                assert body == row['source_record'] and ref == row['source_reference_verbatim']
            else:
                parsed = json.loads(plain, object_pairs_hook=unique_pairs)
                expected = {k:row[k] for k in ['schema','collection','number','source_record','source_reference_verbatim','snapshot']}
                expected['classification'] = row.get('intake_classification', row['classification'])
                assert parsed == expected
            files.append({'id':oid, 'kind':kind, 'path':relative, **b,
                'plain_bytes':len(plain), 'plain_sha256':sha(plain)})
    assert len(files) == len({f['path'] for f in files}) == 204
    progress_path = MONITOR / 'saved-checkpoint/progress.json'
    pr = checkpoint['input_receipts']['imports/web-deenhindi-20261112/progress.json']
    assert all(bind(progress_path)[k] == pr[k] for k in ['bytes','sha256','git_blob_sha1'])
    progress = read(progress_path)
    assert (progress['imported_count'], progress['registered_hadith_count'], progress['non_narration_source_entries'], progress['classification_pending_count']) == (18570,18132,165,273)
    proof = {'schema':'hadith-bank-checkpoint64f4-source-integration-preparation-v1', 'result':'SOURCE_PROVENANCE_PASS',
        'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_commit':COMMIT,
        'source_cohort':bind(cohort_path), 'source_cohort_count':102, 'source_cohort_ids':sorted(sources),
        'collection_counts':dict(collections.Counter(r['collection'] for r in rows)), 'partitions':groups,
        'partition_audit':bind(partition_path), 'all_four_partitions_disjoint_and_exact_cover':True,
        'full_saved_64f4_state':bind(state_path), 'full_saved_64f4_imported_count':18570,
        'all102_saved_imported_descriptors_exact':True, 'all102_absent_from_all18089_prior_imported_ids':True,
        'prior_17cd_state':bind(prior_path), 'complete_historical_64f4_held_count':273,
        'old171_source_rows_exact':True, 'old171_cohort':bind(old_path),
        'complete_evidence_manifest':bind(manifest_path), 'complete_checkpoint':bind(EVIDENCE/'checkpoint.json'),
        'complete_descriptors':bind(EVIDENCE/'held-state-entries.json'),
        'original_bounded_artifact_selected':250, 'committed_supplemented_omitted_rows':23,
        'new102_source_files_reopened':204, 'new102_raw_reparses_exact':102,
        'historical_64f4_worker_progress':bind(progress_path),
        'historical_64f4_worker_counts':{k:progress[k] for k in ['imported_count','registered_hadith_count','non_narration_source_entries','classification_pending_count','pending_fetch_count','errors_count','blocked','done']},
        'historical_progress_is_not_current_published_generated_export':True,
        'published_review_baseline_checked_here':False, 'final_primary_and_independent_gates_checked_here':False,
        'new_linguistic_readings':0, 'new_semantic_decisions':0, 'source_requests':0, 'github_writes':0,
        'history_scope':'Full saved-state bytes, assigned descriptors and absence from all prior imported IDs are independently checked here. Full historical error/retry/control preservation remains the separately frozen acquisition audit; no current export/deployment claim is made.'}
    immutable(ROOT/'input/source-cohort-102.jsonl', cohort_path.read_bytes())
    immutable(ROOT/'new102-raw-parsed-source-proof.json.gz', gzip.compress(enc({'records':files}), mtime=0))
    immutable(target, enc(proof))
    print(json.dumps({'result':proof['result'], 'source_preparation':bind(target), 'sources':102,
        'files':204, 'raw_reparses':102, 'prior_imported_ids_checked':18089}))

if __name__ == '__main__': prepare_source()
