#!/usr/bin/env python3
"""Bind the complete independent candidate inspection and one exact requested restoration."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWNER = ROOT.parent / 'phase23-checkpoint64f4-muslim-ibnmajah26-review'
sha = lambda b: hashlib.sha256(b).hexdigest()
enc = lambda o: (json.dumps(o, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
read = lambda p: json.loads(p.read_bytes())


def main():
    assert not (ROOT / 'independent-boundary-findings-v1.json').exists()
    own_bytes = (ROOT / 'complete-independent-source-first-readings.json').read_bytes()
    assert sha(own_bytes) == 'a2a8ef84e907963f0ece1dd7376ea7a7d0cff1e0ca31561ed35f8a9d99a20377'
    own = json.loads(own_bytes)
    assert own['primary_notes_or_candidate_inspected_before_freeze'] is False
    mb = (OWNER / 'delivery-manifest-v1.json').read_bytes()
    assert sha(mb) == '594c078166ec14b6d4d04a542311bba33486db7fdff8781cb477e88b26571fda'
    m = json.loads(mb)
    assert len(m['files']) == 24
    for f in m['files']:
        b = Path(f['local_path']).read_bytes()
        assert len(b) == f['bytes'] and sha(b) == f['sha256']
    raw = (OWNER / 'publish-v1' / m['active_ledger_path']).read_bytes()
    assert sha(raw) == m['active_ledger_sha256'] == '568ed5cdb8cc1f1ab5dd965e12998f5622338a8e26365da83d5f379cb5f01b7f'
    before = json.loads(gzip.decompress(raw))
    after = copy.deepcopy(before)
    row = next(r for r in after['records'] if r['occurrence_id'] == 'deenhindi-ibnmajah:2732')
    field = next(f for f in row['fields'] if f['language'] == 'ur')
    sources = {r['collection'] + ':' + r['number']: r for r in map(json.loads, (ROOT / 'input/cohort.jsonl').read_bytes().splitlines())}
    text = sources['ibnmajah:2732']['source_record']['translationUrdu']
    a, b = 1452, 1460
    literal = text[a:b]
    assert literal == '( واضح )' and len(literal) == 8 and len(literal.encode()) == 12
    old_field = copy.deepcopy(field)
    old_reason = field['reason']
    old_clause = 'The clear adjective repeats the ruler’s already stated no-doubt appraisal and is initially assessed as explanatory appraisal context; the actual quoted assessment otherwise remains.'
    new_clause = 'The printed clear adjective is an event-specific qualification within Abd al-Malik’s actual judgment appraisal, so it remains as qualified source-rendered scope. It defines no technical word and is not a detached compiler or transmitter-reliability comment. The immutable initial notes and v1 context placement remain preserved with this explicit reconsideration.'
    assert old_reason.count(old_clause) == 1
    new_reason = old_reason.replace(old_clause, new_clause)
    field['reason'] = new_reason
    old_speaker = 'Abd al-Malik supplies his actual appraisal in this case. The supplementary clear adjective is lexical context; the complete doubt/appraisal predicates remain his speech.'
    new_speaker = 'Abd al-Malik supplies his actual appraisal in this case. The printed clear adjective remains as qualified source-rendered appraisal scope within his historical statement; it is not a detached compiler definition or a Prophet saying.'
    relevant = [s for s in field['selected_spans'] if s['component_id'] == 'abd-al-malik-judgment-appraisal']
    assert len(relevant) == 2 and [(s['start'], s['end']) for s in relevant] == [(1278, 1452), (1460, 1486)]
    assert all(s['speaker'] == old_speaker for s in relevant)
    assert {k: v for k, v in relevant[0].items() if k not in ('start', 'end', 'sha256')} == {k: v for k, v in relevant[1].items() if k not in ('start', 'end', 'sha256')}
    merged = {**relevant[0], 'end': 1486, 'sha256': sha(text[1278:1486].encode()), 'speaker': new_speaker}
    result = []
    for span in field['selected_spans']:
        if span is relevant[0]:
            result.append(merged)
        elif span is relevant[1]:
            continue
        else:
            result.append(span)
    field['selected_spans'] = result
    for span in field['selected_spans']:
        span['reason'] = new_reason
    for key in ('explicit_context_cuts', 'reviewed_context_spans'):
        removed = [s for s in field[key] if (s['start'], s['end']) == (a, b)]
        assert len(removed) == 1
        field[key] = [s for s in field[key] if s not in removed]
    for span in field['reviewed_context_spans']:
        span['reason'] = new_reason
    assert field['retained_meaningful_structures'] == []
    field['retained_meaningful_structures'].append({'start': a, 'end': b, 'text': literal, 'sha256': sha(literal.encode()), 'reason': new_reason})
    old_positions = {i for s in old_field['selected_spans'] for i in range(s['start'], s['end'])}
    new_positions = {i for s in field['selected_spans'] for i in range(s['start'], s['end'])}
    assert new_positions - old_positions == set(range(a, b)) and not old_positions - new_positions
    assert field['speaker'] == old_field['speaker'] and field['report_type'] == old_field['report_type']
    all_old = {(r['occurrence_id'], f['language']): f for r in before['records'] for f in r['fields']}
    all_new = {(r['occurrence_id'], f['language']): f for r in after['records'] for f in r['fields']}
    assert len(all_old) == len(all_new) == 130
    assert [key for key in all_old if all_old[key] != all_new[key]] == [('deenhindi-ibnmajah:2732', 'ur')]
    finding = {
        'id': 'deenhindi-ibnmajah:2732', 'language': 'ur',
        'kind': 'restore_source_rendered_historical_actor_appraisal_scope',
        'source_text_sha256': sha(text.encode()), 'start': a, 'end': b,
        'text': literal, 'sha256': sha(literal.encode()),
        'selection_add_ranges': [[a, b]], 'selection_remove_ranges': [],
        'source_characters_restored': 8, 'source_utf8_bytes_restored': 12,
        'existing_component_id': 'abd-al-malik-judgment-appraisal',
        'expected_component_span': [1278, 1486],
        'expected_report_type': relevant[0]['report_type'],
        'expected_source_report_family_id': relevant[0]['source_report_family_id'],
        'before_field_reason': old_reason, 'expected_field_reason': new_reason,
        'before_component_speaker_description': old_speaker, 'expected_component_speaker_description': new_speaker,
        'rationale': 'The adjective qualifies Abd al-Malik’s actually quoted judgment assessment within this particular historical case. It explains no technical term and is neither detached compiler exposition nor a transmitter-reliability appraisal. The previous no-doubt statement does not justify discarding supplied wording as redundant. Restore only the exact printed unit, under the same actor/type/family and source-rendering qualification; do not claim independent historical or verbatim certification.'
    }
    findings = {
        'schema': 'hadith-bank-independent-final-findings-v1',
        'source_commit': before['source_commit'],
        'primary_manifest_sha256': sha(mb), 'primary_active_ledger_sha256': sha(raw),
        'own_source_first_sha256': sha(own_bytes),
        'own_source_reparse_proof_sha256': sha((ROOT / 'source-verification.json').read_bytes()),
        'all55_candidate_fields_and_exact_masks_types_speakers_actually_inspected': True,
        'all5_own_nonempty_source_only_fields_read': True,
        'findings': [finding], 'parent_decision_changes': 0,
        'required_preservation': {'all24_v1_payload_files_and_manifest_archived_exact': True,
                                  'other54_reviewed_fields_exact': True, 'all75_unread_field_definitions_exact': True,
                                  'other25_whole_parents_exact': True, 'all_existing_component_ids_types_actual_actors_and_families_exact': True,
                                  'all_other_selected_positions_exact': True, 'initial_primary_and_independent_source_first_notes_preserved': True},
        'source_http_requests': 0, 'github_writes': 0, 'independent_pro_qc': 'not_performed'
    }
    plan = {'schema': 'hadith-bank-exact-independent-field-plan-v1', 'source_commit': before['source_commit'],
            'primary_active_ledger_sha256': sha(raw),
            'fields': [{'id': rid, 'language': language, 'expected_field_review': f} for (rid, language), f in all_new.items()],
            'expected_selected_span_count': sum(len(f['selected_spans']) for f in all_new.values()),
            'expected_registered': 25, 'expected_source_only': 1, 'expected_complete_readings': 55,
            'source_characters_restored': 8, 'source_utf8_bytes_restored': 12}
    assert plan['expected_selected_span_count'] == 115
    refinements = {
        'schema': 'hadith-bank-independent-reading-refinements-v1',
        'initial_receipt_sha256': sha(own_bytes), 'initial_notes_unchanged': True,
        'refinements': [
            {'fields': ['muslim:2793:hi', 'muslim:2793:ur'], 'initial_note': 'The immediate Ibn Dinar/Ibn Umar relay was initially called route context.', 'final_assessment': 'The actual field has a short immediate attribution, not a multistep prefatory transmitter list. Keeping that local frame is consistent with the separate-chain rule and preserves the qualified Hindi speaker defect. Both primary masks are accepted unchanged.'},
            {'fields': ['muslim:2774:hi', 'muslim:2774:ur'], 'initial_note': 'The later reception/counting dialogue was initially described as needing a separate family.', 'final_assessment': 'The candidate keeps it separately voiced and typed within the same numbered count-explanation account. The distinct actors and later reception event remain explicit, so a common source-report family does not turn it into Prophet speech or an invented additional canonical occurrence. Both masks/types are accepted unchanged.'},
            {'fields': ['ibnmajah:2734:hi'], 'initial_note': 'The independent initial note called the deceased person freed.', 'final_assessment': 'That descriptor is unsupported by this own field. The original only says my slave; the candidate correctly does not infer manumission. The original mistaken note remains immutable, while this explicit correction and the final audit retain the actual source status without importing the express emancipation from2741.'},
        ]
    }
    binding = {'schema': 'hadith-bank-independent-candidate-binding-v1', 'primary_manifest_sha256': sha(mb),
               'active_ledger_path': m['active_ledger_path'], 'active_ledger_sha256': sha(raw),
               'all_primary_payload_file_hashes_verified': 24, 'payload_bytes': sum(f['bytes'] for f in m['files']),
               'boundary_view_sha256': sha((OWNER / 'boundary-view-v1.json').read_bytes()),
               'candidate_opened_only_after_frozen_independent_source_first_receipt': sha(own_bytes),
               'independent_reading_fields': 55, 'fully_compared_candidate_fields': 55}
    for name, obj in [('independent-boundary-findings-v1.json', findings), ('accepted-field-plan-v1.json', plan), ('independent-reading-refinements.json', refinements), ('v1-candidate-binding.json', binding)]:
        data = enc(obj)
        (ROOT / name).write_bytes(data)
        print(name, len(data), sha(data))


if __name__ == '__main__':
    main()
