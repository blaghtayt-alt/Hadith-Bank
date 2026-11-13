#!/usr/bin/env python3
"""Verify the bounded original-only phase17 source packet from pinned GitHub reads."""
import base64
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bind(raw):
    return {'bytes': len(raw), 'sha256': sha(raw),
        'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}


def main():
    source_path = HERE / 'input/source-25.jsonl'
    assert sha(source_path.read_bytes()) == '8b5454d4143ad95c480fb1b6115f670a6e75ff8c8584f309c4c0cd7d3db600a7'
    sources = list(map(json.loads, source_path.read_bytes().splitlines()))
    assert len(sources) == 25 and {r['collection'] for r in sources} == {'bukhari'}
    selected = json.loads((HERE / 'input/selection.json').read_bytes())
    assert sha((HERE / 'input/selection.json').read_bytes()) == 'be655a49396693283f17d0eaac5a6eedebe59e4e67bb923ac41dc89916766ac9'
    prior_state_path = WORK / 'phase3-checkpoint-monitor/input/before-46f2-state.json'
    prior_state_raw = prior_state_path.read_bytes()
    assert sha(prior_state_raw) == 'c4fe6fcdae519e8befe87dc7dd13a2627ab6eade280d34ca75697279a5b0dc2b'
    prior_state = json.loads(prior_state_raw)
    entries = json.loads((HERE / 'input/prior-saved-state-descriptors.json').read_bytes())
    responses = {}
    for file in sorted((HERE / 'input/github-sources').glob('file-*.json')):
        response = json.loads(file.read_bytes())
        assert response['encoding'] == 'base64'
        assert response['requested_ref'] == 'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d'
        path = response['requested_path']
        assert path not in responses
        raw = base64.b64decode(response['content'])
        binding = bind(raw)
        assert binding['git_blob_sha1'] == response['sha']
        local = HERE / 'source-evidence' / path
        local.parent.mkdir(parents=True, exist_ok=True)
        if local.exists():
            assert local.read_bytes() == raw
        else:
            local.write_bytes(raw)
        responses[path] = {'source_commit': response['requested_ref'], 'path': path,
            'github_url': response['display_url'], 'github_blob_sha1': response['sha'],
            **binding, 'response_json_sha256': sha(file.read_bytes())}
    assert len(responses) == 50
    records = []
    for source in sources:
        key = source['collection'] + ':' + source['number']
        entry = entries[key]
        assert entry == prior_state['imported'][key]
        assert entry['parsed']['path'] == source['parsed_path']
        files = []
        for descriptor in [source['snapshot'], entry['parsed']]:
            path = descriptor['path']
            plain = importer.checked_bytes(HERE / 'source-evidence', descriptor)
            assert sha(plain) == descriptor['sha256']
            assert responses[path]['sha256'] == descriptor['stored_sha256']
            if 'stored_bytes' in descriptor:
                assert responses[path]['bytes'] == descriptor['stored_bytes']
            if 'bytes' in descriptor:
                assert len(plain) == descriptor['bytes']
            files.append({**responses[path], 'plain_sha256': sha(plain), 'plain_bytes': len(plain)})
        parsed = json.loads(importer.checked_bytes(HERE / 'source-evidence', entry['parsed']))
        for field in ['collection', 'number', 'source_record', 'source_reference_verbatim', 'snapshot']:
            assert parsed[field] == source[field], (key, field)
        assert parsed['classification'] == source.get('intake_classification', source['classification'])
        raw = importer.checked_bytes(HERE / 'source-evidence', source['snapshot'])
        reparsed, reference = importer.parse_record(raw, source['collection'], source['number'])
        assert reparsed == source['source_record'] and reference == source['source_reference_verbatim']
        source_hash = sha(importer.json_bytes(reparsed))
        selected_item = next(r for r in selected['selected'] if r['id'] == 'deenhindi-' + key)
        assert source_hash == selected_item['source_record_sha256']
        records.append({'id': 'deenhindi-' + key, 'source_record_sha256': source_hash,
            'source_reference_verbatim': reference, 'source_snapshot': source['snapshot'],
            'parsed_descriptor': entry['parsed'], 'files': files,
            'complete_original_source_object_and_reference_reparsed': True,
            'immutable_intake_classification_and_current_annotation_preserved': True})
    reading_path = HERE / 'input/full-hi-ur-reading-input-50.jsonl'
    assert sha(reading_path.read_bytes()) == '7e7e10e8d24a857a5261db2219af52816874763c56465163cc358640168acc3e'
    reading_rows = list(map(json.loads, reading_path.read_bytes().splitlines()))
    by_id = {'deenhindi-' + r['collection'] + ':' + r['number']: r for r in sources}
    assert len(reading_rows) == 50
    for row in reading_rows:
        original = by_id[row['occurrence_id']]['source_record'][row['source_field']]
        assert original == row['text'] and sha(original.encode()) == row['text_sha256']
        assert row['complete_own_field_read'] is False
    report = {'schema': 'hadith-bank-original-extension-source-verification-v1', 'status': 'PASS',
        'source_commit': 'e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d',
        'selection_sha256': sha((HERE / 'input/selection.json').read_bytes()),
        'selected_source_baseline_sha256': sha(source_path.read_bytes()),
        'full_field_input_sha256': sha(reading_path.read_bytes()),
        'active_ledger_baseline_sha256': selected['active_review_sha256'],
        'whole477_source_baseline_sha256': selected['source_baseline_sha256'],
        'canonical_queue_sha256': selected['canonical_queue_sha256'],
        'selected_occurrences': 25, 'saved_files_reopened': 50, 'complete_raw_reparses': 25,
        'all_stored_plain_and_git_blob_hashes_match': True,
        'all_source_record_objects_and_references_exact': True,
        'all50_reading_input_fields_equal_original_baseline': True,
        'prior_descriptor_authority': {'source_commit': '46f2ffbb', 'state_sha256': sha(prior_state_raw),
            'git_blob_sha1': bind(prior_state_raw)['git_blob_sha1'],
            'role': 'Exact historical immutable parsed descriptors only; current file identity is independently pinned by each e3f88 GitHub response.'},
        'parser_sha256': sha(Path(importer.__file__).read_bytes()),
        'linguistic_readings_claimed_by_this_verifier': 0,
        'source_site_requests': 0, 'github_mutations': 0, 'records': records}
    target = HERE / 'input/source-verification.json'
    encoded = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    if target.exists():
        assert target.read_bytes() == encoded
    else:
        target.write_bytes(encoded)
    print(json.dumps({'status': 'PASS', 'report': str(target), **bind(encoded),
        'source_files': 50, 'raw_reparses': 25,
        'stored_source_bytes': sum(r['bytes'] for r in responses.values())}))


if __name__ == '__main__':
    main()
