"""Freeze the independently agreed ten exact source-context changes, preserving v1."""
from pathlib import Path
import copy
import gzip
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
EVID = Path('imports/web-deenhindi-20261112/reviews/checkpoint64f4-bukhari30-20261113')
ACTIVE = Path('imports/web-deenhindi-20261112/reviews/source-review-checkpoint64f4-bukhari30-20261113.json.gz')
PEER = WORK / 'phase23-checkpoint64f4-bukhari30-independent-audit'
ADJ = WORK / 'phase23-bukhari2737-2763-independent-scope-adjudication/independent-complete-original-role-adjudication.json'
sha = lambda data: hashlib.sha256(data).hexdigest()
enc = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
git = lambda data: hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def binding(data):
    return {'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': git(data)}


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, ('immutable output mismatch', str(path))
    else:
        path.write_bytes(data)


def mask(field):
    return {i for span in field['spans'] for i in range(span['start'], span['end'])}


def pure(span):
    return {k: v for k, v in span.items() if k != 'reason'}


v1raw = (HERE / 'delivery-manifest-v1.json').read_bytes()
assert sha(v1raw) == '98355c7137fb76a49d6fafe206c101d39a844d84f8806d13744d51f13affa6db'
v1 = json.loads(v1raw)
draft = json.loads((HERE / 'candidate-delivery-manifest-v2.json').read_bytes())
for manifest in (v1, draft):
    for row in manifest['files']:
        assert binding(Path(row['local_path']).read_bytes()) == {k: row[k] for k in ('bytes', 'sha256', 'git_blob_sha1')}
findings_raw = (PEER / 'independent-boundary-findings-v1.json').read_bytes()
plan_raw = (PEER / 'accepted-reviewed-field-plan-v1.json').read_bytes()
adj_raw = ADJ.read_bytes()
assert sha(findings_raw) == 'bf430ffd0c50b2c74e0ea9e344fffa0c9192bda4c163c00cec28d8cfe3b6e542'
assert sha(plan_raw) == '5fea4564f4760468bd9fa30f42a1dc58ef8901709d6813dd00b9b1e045fb35a6'
assert sha(adj_raw) == '7937df3d88852ebf5eb0dc6b43b81dd6a7d42e15d6c8bca97347113821cd9fcc'
findings = json.loads(findings_raw)
plan = {(r['occurrence_id'], r['language']): r for r in json.loads(plan_raw)['fields']}
assert len(plan) == 66
before_raw = (HERE / 'publish-v1' / ACTIVE).read_bytes()
after_raw = (HERE / 'candidate-v2' / ACTIVE).read_bytes()
assert sha(before_raw) == '7a8b51bfb7112971ef04613efae7fabfa9a87fa87da820b9bf659081cff25c3f'
before_doc, after_doc = [json.loads(gzip.decompress(raw)) for raw in (before_raw, after_raw)]
assert {k: v for k, v in before_doc.items() if k != 'records'} == {k: v for k, v in after_doc.items() if k != 'records'}
before = {r['id']: r for r in before_doc['records']}
after = {r['id']: r for r in after_doc['records']}
source_rows = list(map(json.loads, (HERE / 'input/cohort.jsonl').read_bytes().splitlines()))
source = {'deenhindi-' + r['collection'] + ':' + r['number']: r for r in source_rows}
assert set(before) == set(after) == set(source) and len(before) == 30
affected = {key for key, value in plan.items() if value['expected_removed_positions']}
affected_parents = {key[0] for key in affected}
assert len(affected) == 8 and len(affected_parents) == 4
changes = []
unchanged_fields = unchanged_parents = peer_plan_checks = surviving_spans = 0
for ident, old in before.items():
    new = after[ident]
    assert {k: v for k, v in old.items() if k not in ('field_reviews', 'reason')} == {k: v for k, v in new.items() if k not in ('field_reviews', 'reason')}
    if ident not in affected_parents:
        assert old == new
        unchanged_parents += 1
    old_fields = {f['language']: f for f in old['field_reviews']}
    new_fields = {f['language']: f for f in new['field_reviews']}
    assert set(old_fields) == set(new_fields)
    for language, f in old_fields.items():
        key = (ident, language)
        g = new_fields[language]
        if key in plan:
            assert [pure(s) for s in g['spans']] == plan[key]['expected_spans'], (key, 'exact independent span/voice plan')
            assert g['text_sha256'] == plan[key]['source_text_sha256']
            peer_plan_checks += 1
        if key not in affected:
            assert f == g, key
            unchanged_fields += 1
            continue
        stable = lambda item: {k: v for k, v in item.items() if k not in ('spans', 'reason', 'source_text_annotations')}
        assert stable(f) == stable(g), (key, 'unchanged reading/source/action metadata')
        assert mask(f) - mask(g) == set(plan[key]['expected_removed_positions'])
        assert not mask(g) - mask(f) and not plan[key]['expected_added_positions']
        old_by_range = {(s['start'], s['end']): s for s in f['spans']}
        for span in g['spans']:
            assert pure(span) == pure(old_by_range[(span['start'], span['end'])])
            surviving_spans += 1
        for request in findings['requested_changes']:
            if (request['occurrence_id'], request['language']) != key:
                continue
            text = source[ident]['source_record'][f['source_field']]
            start, end = request['start'], request['end']
            assert text[start:end] == request['text']
            assert sha(text[start:end].encode()) == request['sha256']
            assert (start, end) in old_by_range
            assert not any(start < s['end'] and s['start'] < end for s in g['spans'])
            assert pure(old_by_range[(start, end)]) == {
                **request['removed_component'], 'start': start, 'end': end, 'sha256': request['sha256']}
            changes.append(copy.deepcopy(request))
assert (len(changes), unchanged_fields, unchanged_parents, peer_plan_checks) == (10, 142, 26, 66)
assert sum(c['removed_characters'] for c in changes) == 1253
assert sum(c['removed_utf8_bytes'] for c in changes) == 2717
summary = draft['summary']
assert {k: v for k, v in summary.items() if k not in ('selected_spans', 'selected_characters')} == {k: v for k, v in v1['summary'].items() if k not in ('selected_spans', 'selected_characters')}
assert (summary['selected_spans'], summary['selected_characters']) == (133, 33818)
assert (v1['summary']['selected_spans'] - summary['selected_spans'], v1['summary']['selected_characters'] - summary['selected_characters']) == (10, 1253)
out = HERE / 'publish-v2'
archive = EVID / 'independent-source-role-v2/before-v1'
for row in draft['files']:
    if row['path'] != str(EVID / 'package-file-manifest.json'):
        put(out / row['path'], Path(row['local_path']).read_bytes())
for row in v1['files']:
    put(out / archive / 'payload' / row['path'], Path(row['local_path']).read_bytes())
put(out / archive / 'delivery-manifest-v1.json', v1raw)

# Replay the published layout as well, so archived old ledgers cannot become active.
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
native = SourceReviews(out, 'deenhindi')
partition_count = 0
for saved in source_rows:
    original = importer.canonical_record(saved)
    revised, disposition = native.apply(copy.deepcopy(original), saved=saved)
    assert disposition == 'register'
    for key, value in original.items():
        if key not in ('text', 'language_versions', 'review', 'extraction', 'content_kind'):
            assert revised[key] == value
    assert revised['review']['independent_pro_qc'] == 'not_performed'
    assert revised['review']['certified_release_eligible'] is False
    for left, right in zip(original['language_versions'], revised['language_versions']):
        for key in ('id', 'language', 'script', 'references', 'translation_provenance'):
            assert right.get(key) == left.get(key)
        for key, value in left['source'].items():
            assert right['source'][key] == value
        text = left['text']
        spans = right['source'].get('text_spans', {}).get('quotation_spans', [])
        parts = [(a, b, text[a:b]) for a, b in spans]
        parts.extend((c['source_span'][0], c['source_span'][1], c['text']) for c in right['comments'] if c.get('source_span') is not None)
        assert (right['text'] or '') == ''.join(text[a:b] for a, b in spans)
        cursor = 0
        for start, end, value in sorted(parts):
            assert start == cursor and value == text[start:end]
            cursor = end
        assert cursor == len(text) and ''.join(p[2] for p in sorted(parts)) == text
        partition_count += 1
native.finish()
assert partition_count == 150
receipt = {
    'schema': 'hadith-bank-exact-source-role-refinement-v2', 'status': 'PASS',
    'source_checkpoint': '64f4ed50ed6026855237a5d547a86dd03e73f804',
    'previous_manifest_sha256': sha(v1raw), 'previous_active_sha256': sha(before_raw),
    'final_active_sha256': sha(after_raw), 'independent_findings_sha256': sha(findings_raw),
    'independent_complete_field_plan_sha256': sha(plan_raw),
    'root_original_field_role_adjudication_sha256': sha(adj_raw),
    'all66_reviewed_fields_match_exact_peer_span_voice_plan': True,
    'exact_changes': changes, 'changed_fields': 8, 'changed_parents': 4,
    'whole_selected_ranges_moved_to_context': 10, 'removed_characters': 1253,
    'removed_utf8_bytes': 2717, 'added_characters': 0,
    'unchanged_other_field_definitions': 142, 'unchanged_whole_parents': 26,
    'parent_source_metadata_and_dispositions_unchanged': True,
    'all_surviving_span_positions_types_speakers_components_and_families_exact': True,
    'component_ids_not_renumbered': True,
    'description_changes': 'Only affected parent/field reasons and source annotations describe the final role distinction. The obsolete generic span reasons are omitted from the affected explicit spans; their exact prior text remains archived. All retained classification, speaker, component and family values are exact.',
    'initial_complete_source_first_receipt_unchanged': True,
    'initial_notes_and_all_v1_payloads_preserved': True,
    'v1_payload_files_archived': len(v1['files']), 'v1_manifest_archived': True,
    'final_native_summary': summary, 'final_packaged_layout_native_partitions': partition_count,
    'final_independent_gate_pending': True,
    'reason': 'Two passages are nominal version apparatus without their own finite report predicate. The other two are explicitly appended explanations of the preceding reports. Preserve them in complete source context. Named attribution and legal content alone do not determine exclusion; actual report role does. Every retained report, source condition, quotation and meaningful uncertainty stays exact.',
    'new_language_reading_credit': 0, 'github_writes': 0, 'source_http_requests': 0,
}
amend = EVID / 'independent-source-role-v2'
put(out / amend / 'amendment-receipt.json', enc(receipt))
put(out / amend / 'independent-boundary-findings-v1.json', findings_raw)
put(out / amend / 'accepted-reviewed-field-plan-v1.json', plan_raw)
put(out / amend / 'root-original-field-role-adjudication.json', adj_raw)
put(out / amend / 'package_v2.py', Path(__file__).read_bytes())


def record(path, local=False):
    row = {'path': path.relative_to(out).as_posix(), **binding(path.read_bytes())}
    if local:
        row.update(local_path=str(path), source_path=str(path))
    return row


portable = out / EVID / 'package-file-manifest.json'
put(portable, enc({'schema': 'hadith-bank-source-review-package-manifest-v2',
    'source_checkpoint': receipt['source_checkpoint'], 'active_ledger': str(ACTIVE),
    'source_baseline': str(EVID / 'source-baseline.jsonl.gz'),
    'summary': summary, 'amendment': receipt, 'manifest_excludes_its_own_recursive_hash': True,
    'files': [record(p) for p in sorted(out.rglob('*')) if p.is_file() and p != portable]}))
manifest = {'schema': 'hadith-bank-source-review-delivery-v2', 'output_root': str(out),
    'summary': summary, 'amendment': receipt,
    'files': [record(p, True) for p in sorted(out.rglob('*')) if p.is_file()]}
manifest.update(total_files=len(manifest['files']), total_bytes=sum(r['bytes'] for r in manifest['files']))
put(HERE / 'delivery-manifest-v2.json', enc(manifest))
put(HERE / 'amendment-receipt-v2.json', enc(receipt))
for row in v1['files']:
    data = Path(row['local_path']).read_bytes()
    assert binding(data) == {k: row[k] for k in ('bytes', 'sha256', 'git_blob_sha1')}
    assert (out / archive / 'payload' / row['path']).read_bytes() == data
assert (HERE / 'delivery-manifest-v1.json').read_bytes() == v1raw
print(json.dumps({'status': 'PASS', 'manifest_sha256': sha(enc(manifest)),
    'active_sha256': sha(after_raw), 'files': manifest['total_files'], 'bytes': manifest['total_bytes'],
    'amendment_receipt_sha256': sha(enc(receipt)), 'removed_characters': 1253,
    'removed_utf8_bytes': 2717, 'unchanged_fields': 142, 'unchanged_parents': 26}))
