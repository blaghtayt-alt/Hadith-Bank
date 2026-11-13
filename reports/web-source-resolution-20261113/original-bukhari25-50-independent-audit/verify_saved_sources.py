"""Read-only independent pinned-source and deterministic-selection verification."""
from collections import Counter
from decimal import Decimal
from hashlib import sha256, sha1
from pathlib import Path
import base64
import gzip
import json
import sys

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parent / 'phase17-original-bukhari25-hi-ur'
sys.path.insert(0, str(HERE.parent / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer

PIN = 'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d'
sha = lambda b: sha256(b).hexdigest()
git = lambda b: sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
enc = importer.json_bytes

def main():
    dest = HERE / 'independent-source-verification.json'
    assert not dest.exists(), 'Refusing to replace frozen source proof'
    source_bytes = (HERE / 'input/source-25.jsonl').read_bytes()
    assert sha(source_bytes) == '8b5454d4143ad95c480fb1b6115f670a6e75ff8c8584f309c4c0cd7d3db600a7'
    saved_rows = [json.loads(x) for x in source_bytes.splitlines()]
    by_id = {'deenhindi-' + s['collection'] + ':' + s['number']: s for s in saved_rows}
    assert len(by_id) == 25
    original_input = (HERE / 'input/full-hi-ur-reading-input-50.jsonl').read_bytes()
    assert sha(original_input) == '7e7e10e8d24a857a5261db2219af52816874763c56465163cc358640168acc3e'
    readings = [json.loads(x) for x in original_input.splitlines()]
    selection_bytes = (HERE / 'input/selection.json').read_bytes()
    assert sha(selection_bytes) == 'be655a49396693283f17d0eaac5a6eedebe59e4e67bb923ac41dc89916766ac9'
    selection = json.loads(selection_bytes)
    author_proof_bytes = (HERE / 'input/source-verification.json').read_bytes()
    assert sha(author_proof_bytes) == '4209276da8dc2c2c7cc1c77ff4d902984f4bb1f8419510b0d345f1185c7ef035'
    author_proof = json.loads(author_proof_bytes)
    responses = {}
    for response_path in sorted((PRIMARY / 'input/github-sources').glob('*.json')):
        raw = response_path.read_bytes()
        response = json.loads(raw)
        assert response['requested_ref'] == PIN
        assert response['requested_path'] not in responses
        assert response['encoding'] == 'base64'
        responses[response['requested_path']] = (response, sha(raw))
    assert len(responses) == 50
    records = []
    for item in author_proof['records']:
        saved = by_id[item['id']]
        assert item['source_record_sha256'] == sha(enc(saved['source_record']))
        assert item['source_snapshot'] == saved['snapshot']
        assert item['source_reference_verbatim'] == saved['source_reference_verbatim']
        assert item['parsed_descriptor']['path'] == saved['parsed_path']
        checks = []
        for receipt in item['files']:
            rel = receipt['path']
            assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
            source_path = PRIMARY / 'source-evidence' / rel
            assert not source_path.is_symlink()
            stored = source_path.read_bytes()
            plain = gzip.decompress(stored)
            response, response_digest = responses[rel]
            assert response_digest == receipt['response_json_sha256']
            assert response['display_url'] == f'https://github.com/blaghtayt-alt/Hadith-Bank/blob/{PIN}/{rel}'
            assert base64.b64decode(response['content']) == stored
            assert response['sha'] == receipt['github_blob_sha1'] == receipt['git_blob_sha1'] == git(stored)
            assert sha(stored) == receipt['sha256'] and len(stored) == receipt['bytes']
            assert sha(plain) == receipt['plain_sha256'] and len(plain) == receipt['plain_bytes']
            assert receipt['source_commit'] == PIN
            if rel == saved['snapshot']['path']:
                assert sha(stored) == saved['snapshot']['stored_sha256']
                assert sha(plain) == saved['snapshot']['sha256']
                assert len(stored) == saved['snapshot']['stored_bytes']
                assert len(plain) == saved['snapshot']['bytes']
                body, reference = importer.parse_record(plain, saved['collection'], saved['number'])
                assert body == saved['source_record']
                assert reference == saved['source_reference_verbatim']
                kind = 'raw'
            else:
                assert rel == saved['parsed_path']
                assert sha(stored) == item['parsed_descriptor']['stored_sha256']
                assert sha(plain) == item['parsed_descriptor']['sha256']
                expected = {k: saved[k] for k in ('schema','collection','number','snapshot','source_record','source_reference_verbatim')}
                expected['classification'] = saved['intake_classification']
                assert json.loads(plain) == expected
                kind = 'parsed'
            checks.append({**receipt, 'kind': kind, 'response_content_bytes_equal': True})
        assert {x['kind'] for x in checks} == {'raw','parsed'}
        records.append({'occurrence_id': item['id'], 'source_record_sha256': item['source_record_sha256'],
                        'source_reference_verbatim': saved['source_reference_verbatim'],
                        'raw_reparse_complete_object_and_reference_equal': True,
                        'immutable_intake_classification_preserved': True,
                        'full_original_parsed_object_equal': True, 'files': checks})
    assert len(records) == 25 and sum(len(x['files']) for x in records) == 50
    pinned = PRIMARY / 'input/pinned'
    dependencies = []
    for path_key, hash_key in [('active_review_path','active_review_sha256'),
                              ('source_baseline_path','source_baseline_sha256'),
                              ('canonical_queue_path','canonical_queue_sha256')]:
        raw = (pinned / selection[path_key]).read_bytes()
        assert sha(raw) == selection[hash_key]
        dependencies.append({'path': selection[path_key], 'sha256': sha(raw), 'bytes': len(raw), 'git_blob_sha1': git(raw)})
    active = json.loads(gzip.decompress((pinned / selection['active_review_path']).read_bytes()))
    prior = {r['occurrence_id']: r for r in active['records']}
    assert len(prior) == 477
    full_raw = gzip.decompress((pinned / selection['source_baseline_path']).read_bytes())
    full_rows = [json.loads(x) for x in full_raw.splitlines()]
    full_map = {'deenhindi-' + s['collection'] + ':' + s['number']: s for s in full_rows}
    assert len(full_map) == 477 and set(prior) == set(full_map)
    assert active['source_ledger_path'] == selection['source_baseline_path']
    assert active['source_ledger_sha256'] == selection['source_baseline_sha256']
    assert active['source_ledger_uncompressed_sha256'] == sha(full_raw)
    for oid, saved in by_id.items():
        assert full_map[oid] == saved
        assert prior[oid]['decision'] == 'register'
    qraw = gzip.decompress((pinned / selection['canonical_queue_path']).read_bytes())
    queue = [json.loads(x) for x in qraw.splitlines()]
    assert len(queue) == 3404 and sum(len(r['fields']) for r in queue) == 6411
    qmap = {x['id']: x for x in queue}
    eligible = [r['id'] for r in queue if r['id'] in prior and r['id'].startswith('deenhindi-bukhari:')
                and {'hi','ur'} <= {f['language'] for f in r['fields']}]
    eligible.sort(key=lambda oid: (Decimal(oid.split(':',1)[1]), oid))
    assert len(eligible) == 201
    assert list(by_id) == eligible[:25]
    for reading in readings:
        oid = reading['occurrence_id']; lang = reading['language']
        assert reading['text'] == by_id[oid]['source_record'][reading['source_field']]
        assert reading['source_record_sha256'] == sha(enc(by_id[oid]['source_record']))
        old_field = next(f for f in prior[oid]['fields'] if f['language'] == lang)
        assert old_field['reviewed'] is False and old_field['decision'] == 'unreviewed'
        assert not old_field['selected_spans']
        assert sha(enc(old_field)) == reading['original_active_field_sha256']
        qfield = next(f for f in qmap[oid]['fields'] if f['language'] == lang)
        assert qfield['text_sha256'] == reading['text_sha256'] == sha(reading['text'].encode())
        assert len(reading['text']) == reading['characters']
        assert len(reading['text'].encode()) == reading['utf8_bytes']
    published_proof_path = HERE.parent / 'phase16-checkpoint5589-independent-integration/prepared-source-and-published-baseline.json'
    published_proof_raw = published_proof_path.read_bytes()
    assert sha(published_proof_raw) == '3757b51d7a2996f4ee04132ad661a53a5a88a661e458a65a7fb14c2218c76c70'
    published_proof = json.loads(published_proof_raw)
    assert published_proof['published_review_baseline_commit'] == PIN
    bound_active = next(x for x in published_proof['published_ledger_bindings'] if x['path'] == selection['active_review_path'])
    assert bound_active['sha256'] == dependencies[0]['sha256']
    assert bound_active['git_blob_sha1'] == dependencies[0]['git_blob_sha1']
    bound_source = next(x for x in published_proof['published_source_ledger_dependencies'] if x['path'] == selection['source_baseline_path'])
    assert bound_source['sha256'] == dependencies[1]['sha256']
    assert bound_source['git_blob_sha1'] == dependencies[1]['git_blob_sha1']
    result = {'schema': 'hadith-bank-independent-original-extension-source-verification-v1',
        'result': 'PASS', 'source_commit': PIN, 'independent_reviewer': '/root/queue_audit',
        'source_files_reopened': 50, 'complete_raw_reparses': 25,
        'all_saved_bytes_equal_exact_pinned_github_response_content': True,
        'all_stored_plain_and_git_blob_hashes_match': True,
        'all_source_objects_references_and_intake_annotations_equal': True,
        'all50_original_input_fields_bound_to_own_source_objects': True,
        'selected_source_ledger_sha256': sha(source_bytes), 'full_reading_input_sha256': sha(original_input),
        'selection_sha256': sha(selection_bytes), 'author_proof_sha256': sha(author_proof_bytes),
        'prior_active_rows': 477, 'prior_full_source_rows': 477,
        'deterministic_selection': {'eligible_paired_bukhari': 201, 'selected': 25,
            'rule': 'First25 by Decimal(source number), then unchanged source ID; both Hi and Ur must be pending in this477-parent active ledger.',
            'exact_selected_ids': list(by_id), 'all50_selected_prior_field_decisions_unreviewed': True},
        'queue': {'occurrences': 3404, 'pending_fields': 6411, 'sha256': selection['canonical_queue_sha256']},
        'dependencies': dependencies,
        'published_active_and_source_binding': {'previous_independent_proof_sha256': sha(published_proof_raw),
            'base_commit': PIN, 'active_git_blob_sha1': dependencies[0]['git_blob_sha1'],
            'source_git_blob_sha1': dependencies[1]['git_blob_sha1'],
            'scope': 'Rehashed exact frozen dependency bytes and matched previously independently verified published e3f88 review tree/baseline bindings. This is not a later-main claim.'},
        'records': records, 'parser_sha256': sha(Path(importer.__file__).read_bytes()),
        'candidate_inspected_by_this_script': False, 'new_semantic_readings_claimed_by_verifier': 0,
        'source_http_requests': 0, 'github_writes': 0}
    dest.write_bytes(enc(result))
    print(json.dumps({'result':'PASS','path':str(dest),'sha256':sha(dest.read_bytes()),'source_files':50,'raw_reparses':25,'selected_fields':50},indent=2))

if __name__ == '__main__':
    main()
