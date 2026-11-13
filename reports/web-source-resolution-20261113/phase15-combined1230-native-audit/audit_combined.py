"""Independently apply all six staged Deen ledgers to the complete 1230 sources.

No frozen publication or baseline is changed. This is a combined native and
source-preservation check; it does not add a semantic decision or reread claim.
"""
from pathlib import Path
import collections
import copy
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PAYLOAD = WORK / 'phase15-final-publication/publish'
REVIEWS = Path('imports/web-deenhindi-20261112/reviews')
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews, unique_pairs

ACTIVE = {
    'source-review-20261113-abudawud-tirmidhi-manual.json.gz': ('7a1893ac1e838c73b7f4dfa5d4a47ed805b1f5fb82571f633bc86d4804c79f8a', 636),
    'source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz': ('ac53483e3eab6c0a4c508c86180c75091792e895b5e29f602a061aa2cd080c62', 477),
    'source-review-20261113-checkpoint0639-muslim25-manual-v1.json.gz': ('9fc8bf7fbee9027a1ad5cfd4c8debd4d18ba596e57dab9d70bab69cfdf0783fa', 25),
    'source-review-checkpoint0639-abudawud-tirmidhi21-20261113.json.gz': ('b4735dc63110fd87e92205140a305fee5164f26eafe8b09bddcbca7643a13e34', 21),
    'source-review-checkpoint0639-bukhari43-20261113.json.gz': ('9819890c10d434ca3df69a4ebfee3f70d0aaadfb2aebc56360ebd740e79d9677', 43),
    'source-review-checkpoint0639-nasai-ibnmajah28-20261113.json.gz': ('8d0dbd308198463389e36ad67ca94095b0402089cbef8a3b5ab0bbcd29de5eb6', 28),
}
EXTERNAL_BASELINES = {
    'source-review-20261113-abudawud-tirmidhi-manual.json.gz': (
        WORK / 'phase14-original-abudawud50-urdu/input/pinned/imports/web-deenhindi-20261112/reviews/baselines/20261113-abudawud-tirmidhi-636.jsonl.gz',
        'imports/web-deenhindi-20261112/reviews/baselines/20261113-abudawud-tirmidhi-636.jsonl.gz',
        '4afcb71aa692313ca711d55132a31d9b378d7cf0b242eb4d1b8682b795cc9aee'),
    'source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz': (
        WORK / 'phase14-original-bukhari30-hi-ur/pinned-inputs/imports/web-deenhindi-20261112/reviews/evidence/20261113-bukhari-ibnmajah-manual-v1-source-ledger.jsonl.gz',
        'imports/web-deenhindi-20261112/reviews/evidence/20261113-bukhari-ibnmajah-manual-v1-source-ledger.jsonl.gz',
        '5c9598c1c61cee509155013dde44221de2e17f11bd29d0f475092f2a6e86fb36'),
}


def sha(data): return hashlib.sha256(data).hexdigest()
def gitsha(data): return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def enc(obj): return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def read(path):
    b = path.read_bytes()
    return json.loads(gzip.decompress(b) if path.suffix == '.gz' else b, object_pairs_hook=unique_pairs)
def lines(path):
    b = path.read_bytes()
    if path.suffix == '.gz': b = gzip.decompress(b)
    return [json.loads(x, object_pairs_hook=unique_pairs) for x in b.splitlines() if x.strip()]
def oid(row): return row.get('id', row.get('occurrence_id')) or 'deenhindi-' + row['collection'] + ':' + str(row['number'])
def binding(path):
    b = path.read_bytes()
    return {'bytes': len(b), 'sha256': sha(b), 'git_blob_sha1': gitsha(b)}
def leaves(v):
    if isinstance(v, dict): return sum(leaves(x) for x in v.values())
    if isinstance(v, list): return sum(leaves(x) for x in v)
    return 1
def equal(a, b):
    assert a == b
    return leaves(a)


def main():
    repo = ROOT / 'validation/repo'
    frozen_inputs = []
    # Copy all staged review evidence, preserving every current input byte.
    for path in sorted((PAYLOAD / REVIEWS).rglob('*')):
        if not path.is_file(): continue
        assert not path.is_symlink()
        relative = path.relative_to(PAYLOAD)
        out = repo / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(path.read_bytes())
        frozen_inputs.append({'path': relative.as_posix(), 'local_input': str(path), **binding(path)})
    actual_names = {p.name for p in (repo / REVIEWS).glob('source-review*.json*')}
    assert actual_names == set(ACTIVE)
    for name, (path, relative, digest) in EXTERNAL_BASELINES.items():
        assert binding(path)['sha256'] == digest
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists(): assert destination.read_bytes() == path.read_bytes()
        else: destination.write_bytes(path.read_bytes())
        frozen_inputs.append({'path': relative, 'local_input': str(path), **binding(path)})
    sources, decisions, ledger_for_id = {}, {}, {}
    ledger_bindings, baseline_bindings = [], []
    for name, (digest, expected_count) in ACTIVE.items():
        path = repo / REVIEWS / name
        assert sha(path.read_bytes()) == digest
        ledger = read(path)
        if name in EXTERNAL_BASELINES:
            _, relative, expected_baseline = EXTERNAL_BASELINES[name]
        else:
            relative, expected_baseline = ledger['source_ledger_path'], ledger['source_ledger_sha256']
        baseline = repo / relative
        assert sha(baseline.read_bytes()) == expected_baseline
        source_rows = lines(baseline)
        source_by_id = {oid(x): x for x in source_rows}
        rows = ledger.get('records', ledger.get('decisions'))
        assert len(rows) == len(source_rows) == len(source_by_id) == expected_count
        assert {oid(x) for x in rows} == set(source_by_id)
        for decision in rows:
            identity = oid(decision)
            assert identity not in decisions and identity not in sources
            decisions[identity] = decision
            sources[identity] = source_by_id[identity]
            ledger_for_id[identity] = name
            assert decision['source_record_sha256'] == sha(importer.json_bytes(sources[identity]['source_record']))
        ledger_bindings.append({'path': (REVIEWS / name).as_posix(), **binding(path), 'records': len(rows)})
        baseline_bindings.append({'path': relative, **binding(baseline), 'records': len(source_rows)})
    assert len(sources) == len(decisions) == 1230
    engine = SourceReviews(repo, 'deenhindi')
    assert set(engine.decisions) == set(decisions)
    counts, metadata = collections.Counter(), collections.Counter()
    ledgers, languages = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    details, script_fixes, empty_fields = [], [], []
    for identity in sorted(sources):
        saved, decision = sources[identity], decisions[identity]
        source_hash_before = sha(enc(saved))
        original = importer.canonical_record(saved)
        before = copy.deepcopy(original)
        revised, action = engine.apply(original, saved=saved)
        assert original == before and sha(enc(saved)) == source_hash_before
        assert action == decision['decision'] and action in ['register', 'exclude']
        assert revised['review']['independent_pro_qc'] == 'not_performed'
        assert revised['review']['certified_release_eligible'] is False
        for key, value in before.items():
            if key not in ['text', 'language_versions', 'review', 'content_kind', 'extraction']:
                metadata['parent'] += equal(value, revised[key])
        versions = {v['language']: v for v in before['language_versions']}
        after_versions = {v['language']: v for v in revised['language_versions']}
        assert set(versions) == set(after_versions)
        assert [v['id'] for v in before['language_versions']] == [v['id'] for v in revised['language_versions']]
        fields = decision.get('fields', decision.get('field_reviews', []))
        by_language = {f['language']: f for f in fields}
        assert len(by_language) == len(fields) and set(by_language) <= set(importer.LANGUAGE_FIELDS)
        row_fields = []
        for language, provider_field in importer.LANGUAGE_FIELDS.items():
            counts['source_field_slots'] += 1
            value = saved['source_record'].get(provider_field)
            if value is None or value == '':
                assert language not in versions and language not in after_versions
                counts['empty_source_slots'] += 1
                empty_fields.append({'id': identity, 'language': language, 'source_field': provider_field,
                                     'exact_source_value': value, 'preserved_in_immutable_baseline': True})
                continue
            old, new = versions[language], after_versions[language]
            assert old['text'] == value
            f = by_language.get(language)
            reviewed = bool(f and f['reviewed'])
            spans = f.get('spans', f.get('selected_spans', [])) if f else []
            if f:
                assert f['text_sha256'] == sha(value.encode())
                assert f['chars_reviewed'] == (len(value) if reviewed else 0)
                assert f['bytes_reviewed'] == (len(value.encode()) if reviewed else 0)
                assert f['source_field'] == provider_field
            assert new['source']['manual_review']['field_reviewed'] is reviewed
            assert not spans or reviewed
            assert (new['text'] or '') == ''.join(value[s['start']:s['end']] for s in spans)
            parts = []
            for span in spans:
                a, b = span['start'], span['end']
                assert 0 <= a < b <= len(value) and sha(value[a:b].encode()) == span['sha256']
                parts.append((a, b, value[a:b]))
            for comment in new.get('comments', []):
                if comment.get('source_span') is None: continue
                a, b = comment['source_span']
                assert comment['scope'] == 'source_context_not_narration'
                assert comment['text'] == value[a:b] and comment['source_text_sha256'] == sha(value[a:b].encode())
                parts.append((a, b, comment['text']))
            cursor = 0
            for a, b, text in sorted(parts):
                assert a == cursor and a < b <= len(value) and text == value[a:b]
                cursor = b
            assert cursor == len(value) and ''.join(x[2] for x in sorted(parts)) == value
            counts['nonempty_lossless_partitions'] += 1
            status = 'admitted' if spans else 'read_context' if reviewed else 'unread_context'
            counts[status] += 1
            languages[language][status] += 1
            if reviewed:
                counts['read_fields'] += 1
                counts['read_chars'] += len(value)
                counts['read_utf8_bytes'] += len(value.encode())
            if action == 'exclude': assert reviewed and not spans
            for key, old_value in old.items():
                if key in ['text', 'scope', 'source', 'comments']: continue
                if key == 'script' and old_value != new[key]:
                    assert f and reviewed and new[key] == f['observed_script'] and f['source_script_note']
                    script_fixes.append({'id': identity, 'language': language, 'before': old_value, 'after': new[key]})
                else:
                    metadata['language'] += equal(old_value, new[key])
            for key, old_value in old['source'].items(): metadata['source'] += equal(old_value, new['source'][key])
            for i, comment in enumerate(old.get('comments', [])):
                for key, old_value in comment.items(): metadata['previous_comments'] += equal(old_value, new['comments'][i][key])
            row_fields.append({'language': language, 'source_field_sha256': sha(value.encode()),
                               'characters': len(value), 'status': status,
                               'selected_ranges': [[s['start'], s['end']] for s in spans],
                               'complete_lossless_partition': True})
        counts[action] += 1
        ledgers[ledger_for_id[identity]][action] += 1
        details.append({'id': identity, 'ledger': ledger_for_id[identity], 'action': action,
                        'source_record_sha256': decision['source_record_sha256'], 'fields': row_fields})
    engine.finish()
    assert (counts['register'], counts['exclude']) == (1201, 29)
    assert (counts['source_field_slots'], counts['nonempty_lossless_partitions'], counts['empty_source_slots']) == (6150, 6088, 62)
    for item in frozen_inputs:
        assert all(binding(Path(item['local_input']))[k] == item[k] for k in ['bytes', 'sha256', 'git_blob_sha1'])
    report = {'schema': 'hadith-bank-independent-six-ledger1230-native-audit-v1', 'status': 'PASS',
              'source_cohorts': {'existing_abudawud_tirmidhi': 636, 'existing_bukhari_ibnmajah': 477, 'checkpoint0639_new': 117},
              'active_ledgers': ledger_bindings, 'baselines': baseline_bindings,
              'parent_ids': 1230, 'duplicate_parent_ids': [], 'counts': dict(counts),
              'by_ledger': dict(ledgers), 'language_coverage': dict(languages),
              'metadata_leaf_equalities': dict(metadata), 'metadata_leaf_equalities_total': sum(metadata.values()),
              'observed_script_corrections': script_fixes, 'native_apply_finish': 'PASS',
              'all_original_source_objects_unchanged': True, 'all_original_parent_metadata_unchanged': True,
              'all_input_files_unchanged': True, 'copied_staged_evidence_and_baseline_files': len(frozen_inputs),
              'source_review_engine_sha256': engine.engine_sha256,
              'source_importer_sha256': sha(Path(importer.__file__).read_bytes()),
              'scope': 'Joint native application of exactly the six staged active ledgers to complete hash-bound636+477+117 baselines. No new semantic reading or source acquisition. Full raw-source verification and independent linguistic audits remain bound by their separate completed packages.',
              'source_http_requests': 0, 'github_writes': 0, 'independent_pro_qc': 'not_performed'}
    prefix = Path('reports/web-source-resolution-20261113/phase15-combined1230-native-audit')
    outputs = {
        prefix / 'validation-report.json': enc(report),
        prefix / 'source-partitions-and-input-bindings.json.gz': gzip.compress(enc({'records': details, 'empty_fields': empty_fields,
            'inputs': [{k:v for k,v in f.items() if k != 'local_input'} for f in frozen_inputs]}), mtime=0),
        prefix / 'audit_combined.py': Path(__file__).read_bytes(),
    }
    files = []
    for relative, data in outputs.items():
        path = ROOT / 'publish' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        assert not path.exists()
        path.write_bytes(data)
        files.append({'path': relative.as_posix(), 'local_path': str(path), **binding(path)})
    manifest = {'schema': 'independent-combined-native-audit-delivery-v1', 'status': 'PASS', 'files': files,
                'total_files': len(files), 'total_bytes': sum(x['bytes'] for x in files), 'counts': dict(counts)}
    (ROOT / 'delivery-manifest.json').write_bytes(enc(manifest))
    print(json.dumps({'status': 'PASS', 'counts': dict(counts), 'metadata_leaf_equalities': sum(metadata.values()),
                      'manifest_sha256': sha(enc(manifest)), 'report_sha256': sha(enc(report)),
                      'files': len(files), 'bytes': manifest['total_bytes']}, indent=2))


if __name__ == '__main__':
    main()
