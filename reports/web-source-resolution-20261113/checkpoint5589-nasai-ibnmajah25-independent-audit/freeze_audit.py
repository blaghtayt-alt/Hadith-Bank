#!/usr/bin/env python3
"""Freeze the independent final source, semantic-mask and surgical revision audit."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWNER = HERE.parent / 'phase16-checkpoint5589-nasai-ibnmajah25-review'
REL = Path('reports/web-source-resolution-20261113/checkpoint5589-nasai-ibnmajah25-independent-audit')
V1_SHA = 'de0399c89be6d422c9c738404ec2c2474f695aef174da7ecd9a810da0c81ec74'
V2_SHA = 'ecdf0e8a13a7d2591830ca61af738be297e78b62d531f061df94401b5e80ae04'
ACTIVE_SHA = '86892c29af53523850315c3fc59b757218220a2b678cb90841a57c95efbd1b53'
READING_SHA = '91561405fa1e9423fa291f31adb4b86dae06ea6d2a276e784f83710118e4b258'
FINDINGS_SHA = '39d7e8bdc903c673d658c1c670eea1f658f2a8336cc84965fe6c8bebee41d53a'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def bind(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': sha(raw),
        'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw
    else:
        path.write_bytes(raw)


def current_active(manifest):
    entries = [x for x in manifest['files'] if Path(x['path']).parent.as_posix() == 'imports/web-deenhindi-20261112/reviews' and Path(x['path']).name.startswith('source-review-')]
    assert len(entries) == 1
    return entries[0], read(Path(entries[0]['local_path']))


def position_map(field, size):
    result = [None] * size
    for span in field['spans']:
        attribution = {k: v for k, v in span.items() if k not in ['start', 'end', 'sha256']}
        for i in range(span['start'], span['end']):
            assert result[i] is None
            result[i] = attribution
    return result


def main():
    v1p, v2p = OWNER / 'delivery-manifest-v1.json', OWNER / 'delivery-manifest-v2.json'
    assert sha(v1p.read_bytes()) == V1_SHA and sha(v2p.read_bytes()) == V2_SHA
    v1m, v2m = read(v1p), read(v2p)
    before_bindings = []
    for manifest in [v1m, v2m]:
        for item in manifest['files']:
            b = bind(Path(item['local_path']))
            assert b['sha256'] == item['sha256'] and b['bytes'] == item['bytes'] and b['git_blob_sha1'] == item['git_blob_sha1']
    v1entry, before = current_active(v1m)
    v2entry, after = current_active(v2m)
    assert v2entry['sha256'] == ACTIVE_SHA
    assert {k: v for k, v in before.items() if k != 'records'} == {k: v for k, v in after.items() if k != 'records'}
    findings = read(HERE / 'independent-boundary-findings-v1.json')
    assert sha((HERE / 'independent-boundary-findings-v1.json').read_bytes()) == FINDINGS_SHA
    assert sha((HERE / 'complete-independent-source-first-readings.json').read_bytes()) == READING_SHA
    exact = {(x['id'], x['language']): x for x in findings['required_changes']}
    source_rows = list(map(json.loads, (HERE / 'input/cohort.jsonl').read_text().splitlines()))
    sources = {f"deenhindi-{r['collection']}:{r['number']}": r for r in source_rows}
    preserved_fields = preserved_parents = added = added_bytes = 0
    inspected_changes = []
    for br, ar in zip(before['records'], after['records']):
        assert br['id'] == ar['id']
        assert {k: v for k, v in br.items() if k != 'field_reviews'} == {k: v for k, v in ar.items() if k != 'field_reviews'}
        if br == ar:
            preserved_parents += 1
        for bf, af in zip(br['field_reviews'], ar['field_reviews']):
            key = (br['id'], bf['language'])
            if key not in exact:
                assert bf == af, key
                preserved_fields += 1
                continue
            assert {k: v for k, v in bf.items() if k not in ['spans', 'reason', 'source_text_annotations', 'action']} == {k: v for k, v in af.items() if k not in ['spans', 'reason', 'source_text_annotations', 'action']}
            text = sources[br['id']]['source_record'][bf['source_field']]
            change = exact[key]
            a, b = change['start'], change['end']
            assert text[a:b] == change['text']
            bm, am = position_map(bf, len(text)), position_map(af, len(text))
            assert all(bm[i] is None and am[i] is not None for i in range(a, b))
            assert all(bm[i] == am[i] for i in range(len(text)) if not a <= i < b)
            old_labels = {json.dumps(v, sort_keys=True) for v in bm if v is not None}
            assert {json.dumps(v, sort_keys=True) for v in am if v is not None} == old_labels
            annotations = af['source_text_annotations']
            assert len(annotations) == 1 and annotations[0]['new_translation'] is False
            note = annotations[0]['note']
            assert 'Urdu' in note and 'outside quotation marks' in note and 'does not certify' in note
            added += b - a
            added_bytes += len(text[a:b].encode())
            inspected_changes.append({**change, 'unchanged_existing_attributions_and_family': True,
                'visible_source_quotation_placement_annotation': annotations})
    assert (preserved_fields, preserved_parents, added, added_bytes) == (123, 24, 27, 54)
    final_hashes = {x['sha256'] for x in v2m['files']}
    assert all(x['sha256'] in final_hashes for x in v1m['files'])
    assert V1_SHA in final_hashes
    native = read(HERE / 'native-source-audit-final.json')
    assert native['status'] == 'PASS' and native['active_ledger_sha256'] == ACTIVE_SHA
    assert native['candidate_manifest_sha256'] == V2_SHA
    assert native['counts'] == {'register': 25, 'unread_fields': 75, 'partitions': 125,
        'read_fields': 50, 'read_chars': 17084, 'read_bytes': 36958, 'admitted_fields': 50}
    assert native['source_metadata_leaf_equalities_total'] == 5650
    proof = read(HERE / 'field-and-source-proof-final.json.gz')
    assert len(proof['fields']) == 50 and len(proof['source_files']) == 50
    selected_spans = sum(len(x['spans']) for x in proof['fields'])
    receipt = {'schema': 'hadith-bank-independent-final-reading-audit-v1', 'status': 'PASS',
        'source_checkpoint': '5589a3ffc3b43c3324ae26f2b6c4d33152834456',
        'primary_manifest_path': 'phase16-checkpoint5589-nasai-ibnmajah25-review/delivery-manifest-v2.json',
        'primary_manifest_sha256': V2_SHA, 'active_ledger_path': v2entry['path'],
        'active_ledger_sha256': ACTIVE_SHA, 'prior_manifest_sha256': V1_SHA,
        'source_first_complete_reading_receipt_sha256': READING_SHA,
        'all_readings_preceded_candidate_inspection': True,
        'complete_source_fields_actually_read': 50, 'complete_reading_characters': 17084,
        'complete_reading_utf8_bytes': 36958, 'admitted_language_fields': 50,
        'reviewed_context_only_fields': 0, 'unread_sibling_context_fields': 75,
        'registered_occurrences': 25, 'resolved_source_only_occurrences': 0,
        'selected_spans_independently_inspected': selected_spans,
        'all_selected_positions_match_explicit_independent_boundary_plan': True,
        'all_actual_component_types_speakers_and_families_independently_accepted': True,
        'exact_v2_changed_fields': 2, 'selected_characters_restored': added,
        'selected_utf8_bytes_restored': added_bytes, 'selected_characters_removed': 0,
        'unchanged_other_field_decisions': preserved_fields, 'unchanged_complete_parent_records': preserved_parents,
        'all_parent_metadata_and_source_objects_unchanged': True,
        'prior_payload_files_and_prior_manifest_retained_and_unchanged': True,
        'raw_and_parsed_source_files_reopened_and_hashed': 50, 'complete_raw_pages_reparsed': 25,
        'native_lossless_field_partitions': 125, 'metadata_leaf_equalities': 5650,
        'source_review_engine_sha256': native['source_review_engine_sha256'],
        'independent_findings_sha256': FINDINGS_SHA,
        'independent_semantic_plan_sha256': sha((HERE / 'independently-accepted-boundary-plan.json').read_bytes()),
        'native_audit_report_sha256': sha((HERE / 'native-source-audit-final.json').read_bytes()),
        'required_amendments_remaining': [],
        'independent_reconsiderations': findings['independent_reconsiderations'],
        'final_amendments_verified': inspected_changes,
        'scope': 'This is a complete independent reading and source-bound boundary audit of the50 actually admitted Hindi/Urdu fields. No other sibling was linguistically reviewed, no canonical identity or missing text was supplied, and no authenticity certification or live-deployment result is claimed.',
        'source_http_requests': 0, 'github_writes': 0, 'source_or_owner_mutations': 0,
        'independent_pro_qc': 'not_performed'}
    out = HERE / 'publish'
    save(out / REL / 'independent-reading-audit.json', encoded(receipt))
    for local, remote in [
        ('complete-independent-source-first-readings.json', 'complete-independent-source-first-readings.json.gz'),
        ('independent-boundary-findings-v1.json', 'independent-boundary-findings-v1.json'),
        ('independently-accepted-boundary-plan.json', 'independently-accepted-boundary-plan.json.gz'),
        ('native-source-audit-final.json', 'native-source-audit-final.json'),
        ('field-and-source-proof-final.json.gz', 'field-and-source-proof-final.json.gz'),
        ('audit_candidate.py', 'audit_candidate.py'), ('freeze_audit.py', 'freeze_audit.py')]:
        raw = (HERE / local).read_bytes()
        if remote.endswith('.gz') and not local.endswith('.gz'):
            raw = gzip.compress(raw, mtime=0)
        save(out / REL / remote, raw)
    files = [{'path': p.relative_to(out).as_posix(), 'local_path': str(p.resolve()), **bind(p)}
             for p in sorted(out.rglob('*')) if p.is_file()]
    manifest = {'schema': 'hadith-bank-independent-audit-delivery-v1', 'status': 'PASS',
        'source_checkpoint': receipt['source_checkpoint'], 'output_root': str(out.resolve()),
        'primary_manifest_sha256': V2_SHA, 'active_ledger_sha256': ACTIVE_SHA,
        'files': files, 'total_files': len(files), 'total_bytes': sum(x['bytes'] for x in files)}
    save(HERE / 'delivery-manifest.json', encoded(manifest))
    assert sha(v1p.read_bytes()) == V1_SHA and sha(v2p.read_bytes()) == V2_SHA
    print(json.dumps({'status': 'PASS', 'manifest': bind(HERE / 'delivery-manifest.json'),
        'report': bind(out / REL / 'independent-reading-audit.json'),
        'files': len(files), 'bytes': sum(x['bytes'] for x in files), 'selected_spans': selected_spans}, indent=2))


if __name__ == '__main__':
    main()
