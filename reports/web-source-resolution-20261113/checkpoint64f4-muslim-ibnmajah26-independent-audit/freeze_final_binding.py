#!/usr/bin/env python3
"""Verify the owner's final one-field amendment against the complete independent plan."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWNER = ROOT.parent / 'phase23-checkpoint64f4-muslim-ibnmajah26-review'
sha = lambda b: hashlib.sha256(b).hexdigest()
blob = lambda b: hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
enc = lambda o: (json.dumps(o, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def main():
    assert not (ROOT / 'final-candidate-binding.json').exists()
    m1b = (OWNER / 'delivery-manifest-v1.json').read_bytes()
    m2b = (OWNER / 'delivery-manifest-v2.json').read_bytes()
    assert sha(m1b) == '594c078166ec14b6d4d04a542311bba33486db7fdff8781cb477e88b26571fda'
    assert sha(m2b) == 'a8df0f90ce43ead3e8424ea88efa6d36a1cfcc86817df82b07b43576249fba90'
    m1, m2 = map(json.loads, (m1b, m2b))
    assert len(m1['files']) == 24 and len(m2['files']) == 58
    out = OWNER / 'publish-v2'
    for f in m2['files']:
        p = out / f['path']
        assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(out.resolve())
        b = p.read_bytes()
        assert len(b) == f['bytes'] and sha(b) == f['sha256']
        if 'git_blob_sha1' in f:
            assert blob(b) == f['git_blob_sha1']
    archive_manifest = [f['path'] for f in m2['files'] if f['path'].endswith('/previous-v1/delivery-manifest-v1.json')]
    assert len(archive_manifest) == 1 and (out / archive_manifest[0]).read_bytes() == m1b
    archive = Path(archive_manifest[0]).parent
    for f in m1['files']:
        before = (OWNER / 'publish-v1' / f['path']).read_bytes()
        assert len(before) == f['bytes'] and sha(before) == f['sha256']
        assert (out / archive / f['path']).read_bytes() == before
    raw1 = (OWNER / 'publish-v1' / m1['active_ledger_path']).read_bytes()
    raw2 = (out / m2['active_ledger_path']).read_bytes()
    assert sha(raw1) == '568ed5cdb8cc1f1ab5dd965e12998f5622338a8e26365da83d5f379cb5f01b7f'
    assert sha(raw2) == m2['active_ledger_sha256'] == '48a5d68858f20144a51f9525b7b234700bdeab7530d47030ab97a4422938941d'
    d1, d2 = map(lambda b: json.loads(gzip.decompress(b)), (raw1, raw2))
    assert d1['source_first_receipt_sha256'] == d2['source_first_receipt_sha256']
    for f in m1['files']:
        if any(x in Path(f['path']).name for x in ('source_first_batch', 'manual_source_first_readings', 'complete-source-first-readings')):
            assert (out / f['path']).read_bytes() == (OWNER / 'publish-v1' / f['path']).read_bytes()
    expected_bytes = (ROOT / 'accepted-field-plan-v1.json').read_bytes()
    assert sha(expected_bytes) == '3b06334282103408e95bfc3e3f331816751569e693a498fb0586c109addbb725'
    expected = {(f['id'], f['language']): f['expected_field_review'] for f in json.loads(expected_bytes)['fields']}
    old = {r['occurrence_id']: r for r in d1['records']}
    new = {r['occurrence_id']: r for r in d2['records']}
    assert old.keys() == new.keys() and len(old) == 26
    changed, unchanged_parents, reviewed, unread, spans = [], 0, 0, 0, 0
    for rid in old:
        assert {k: v for k, v in old[rid].items() if k != 'fields'} == {k: v for k, v in new[rid].items() if k != 'fields'}
        unchanged_parents += old[rid] == new[rid]
        for a, b in zip(old[rid]['fields'], new[rid]['fields'], strict=True):
            key = (rid, b['language'])
            assert b == expected[key], key
            reviewed += b['reviewed']
            unread += not b['reviewed']
            spans += len(b['selected_spans'])
            if a != b:
                changed.append(key)
    assert changed == [('deenhindi-ibnmajah:2732', 'ur')]
    assert (unchanged_parents, reviewed, unread, spans) == (25, 55, 75, 115)
    assert sum(len({s['component_id'] for s in f['selected_spans']}) for r in d1['records'] for f in r['fields']) == 91
    assert sum(len({s['component_id'] for s in f['selected_spans']}) for r in d2['records'] for f in r['fields']) == 91
    a = next(f for f in old['deenhindi-ibnmajah:2732']['fields'] if f['language'] == 'ur')
    b = next(f for f in new['deenhindi-ibnmajah:2732']['fields'] if f['language'] == 'ur')
    pa = {i for s in a['selected_spans'] for i in range(s['start'], s['end'])}
    pb = {i for s in b['selected_spans'] for i in range(s['start'], s['end'])}
    assert pb - pa == set(range(1452, 1460)) and not pa - pb
    label_keys = ('component_id', 'report_type', 'source_report_family_id')
    la = {i: {k: s[k] for k in label_keys} for s in a['selected_spans'] for i in range(s['start'], s['end'])}
    lb = {i: {k: s[k] for k in label_keys} for s in b['selected_spans'] for i in range(s['start'], s['end'])}
    assert all(la[i] == lb[i] for i in pa)
    assert {tuple(x.values()) for x in la.values()} == {tuple(x.values()) for x in lb.values()}
    firstb = (ROOT / 'complete-independent-source-first-readings.json').read_bytes()
    assert sha(firstb) == 'a2a8ef84e907963f0ece1dd7376ea7a7d0cff1e0ca31561ed35f8a9d99a20377'
    first = json.loads(firstb)
    assert sha((ROOT / 'independent_readings.py').read_bytes()) == first['own_notes_sha256']
    refinements = json.loads((ROOT / 'independent-reading-refinements.json').read_bytes())
    fields = []
    for rid, record in new.items():
        for f in record['fields']:
            if f['reviewed']:
                fields.append({'id': rid, 'language': f['language'], 'text_sha256': f['text_sha256'],
                               'approved_spans': [{k: s[k] for k in ('start', 'end', 'sha256', 'component_id', 'report_type', 'speaker', 'source_report_family_id')} for s in f['selected_spans']],
                               'complete_original_field_previously_read': True,
                               'all_final_quotation_context_boundaries_and_attribution_actually_assessed': True,
                               'final_field_definition_equals_independent_plan': True})
    assert len(fields) == 55
    assessment = {'schema': 'hadith-bank-independent-final-field-assessment-v1',
                  'all55_candidate_fields_independently_assessed': True, 'all_final_target_reason_and_speaker_descriptions_actually_read': True,
                  'source_first_reading_receipt_sha256': sha(firstb), 'accepted_field_plan_sha256': sha(expected_bytes),
                  'fields': fields, 'open_findings': [], 'initial_note_refinements': refinements['refinements']}
    amendment = {'requested_changed_fields': 1, 'changed_fields': changed,
                 'source_characters_restored': 8, 'source_utf8_bytes_restored': 12,
                 'source_characters_removed': 0, 'all_existing_component_ids_report_types_actual_actors_and_families_preserved': True,
                 'other_field_definitions_exact': 129, 'other_reviewed_fields_exact': 54,
                 'unread_context_fields_exact': 75, 'other_whole_parents_exact': 25,
                 'selected_spans_before': 116, 'selected_spans_after': 115,
                 'typed_components_preserved': 91, 'all24_v1_payload_files_and_manifest_archived_exact': True,
                 'initial_primary_and_independent_reading_notes_preserved': True,
                 'before_manifest_sha256': sha(m1b), 'before_active_ledger_sha256': sha(raw1),
                 'after_manifest_sha256': sha(m2b), 'after_active_ledger_sha256': sha(raw2),
                 'accepted_full130_field_plan_sha256': sha(expected_bytes)}
    binding = {'schema': 'hadith-bank-independent-final-candidate-binding-v1',
               'all55_complete_original_fields_and_candidate_boundaries_independently_read': True,
               'owner_accepted_all_requested_changes': True,
               'owner_manifest_path': str(OWNER / 'delivery-manifest-v2.json'),
               'owner_manifest_sha256': sha(m2b), 'owner_output_directory': 'publish-v2',
               'active_ledger_sha256': sha(raw2), 'approved_admitted_fields': 50,
               'independent_amendment_result': amendment, 'candidate_mutations_by_auditor': 0}
    for name, obj in [('final-field-boundary-assessment.json', assessment), ('final-candidate-binding.json', binding)]:
        data = enc(obj)
        (ROOT / name).write_bytes(data)
        print(name, len(data), sha(data))


if __name__ == '__main__':
    main()
