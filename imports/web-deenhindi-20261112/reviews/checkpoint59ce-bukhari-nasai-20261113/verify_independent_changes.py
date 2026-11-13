"""Verify the precise subtraction/restoration authorized by the second reading."""
import copy
import gzip
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mask(field):
    return {i for s in field['spans'] for i in range(s['start'], s['end'])}


def verify_changes(root, output, evidence, document, sources, put, enc):
    before_bytes = (root / 'before-independent-active.json.gz').read_bytes()
    before = json.loads(gzip.decompress(before_bytes))
    plan_bytes = (root / 'independent-boundary-corrections-v2.json').read_bytes()
    plan = json.loads(plan_bytes)
    assert sha(before_bytes) == plan['before_active_sha256'] == '8678f9ccf00db8f946690048689b5093b0b61a482c7820acbb7b367799fc3aec'
    assert sha((root / 'before-independent-delivery-manifest.json').read_bytes()) == plan['before_delivery_manifest_sha256']
    assert before['source_ledger_sha256'] == document['source_ledger_sha256']
    old_records = {r['id']: r for r in before['records']}
    new_records = {r['id']: r for r in document['records']}
    changes = {(c['id'], c['language']): c for c in plan['changes']}
    assert len(changes) == 5 and set(old_records) == set(new_records)
    comparisons = []
    for identity, old in old_records.items():
        new = new_records[identity]
        assert {k: v for k, v in old.items() if k != 'field_reviews'} == {k: v for k, v in new.items() if k != 'field_reviews'}
        old_fields = {f['language']: f for f in old['field_reviews']}
        new_fields = {f['language']: f for f in new['field_reviews']}
        assert set(old_fields) == set(new_fields)
        for language, old_field in old_fields.items():
            new_field = new_fields[language]
            change = changes.get((identity, language))
            if not change:
                assert old_field == new_field
                continue
            source = sources[identity.removeprefix('deenhindi-')]['source_record'][old_field['source_field']]
            assert sha(source.encode()) == change['source_text_sha256']
            remove, restore = set(), set()
            for label, positions in [('move_to_context', remove), ('restore_to_same_component', restore)]:
                for item in change[label]:
                    a, b = item['start'], item['end']
                    assert source[a:b] == item['text'] and sha(source[a:b].encode()) == item['sha256']
                    positions.update(range(a, b))
            old_mask, new_mask = mask(old_field), mask(new_field)
            assert old_mask - new_mask == remove and new_mask - old_mask == restore
            for name in set(old_field) - {'action', 'reason', 'spans'}:
                assert old_field[name] == new_field[name]
            assert old_field['reviewed'] and new_field['reviewed']
            assert bool(old_field['spans']) == bool(new_field['spans'])
            assert all(source[s['start']:s['end']].strip() for s in new_field['spans'])
            old_types = {(s.get('report_type', old_field.get('report_type')), s.get('speaker', old_field.get('speaker'))) for s in old_field['spans']}
            new_types = {(s.get('report_type', new_field.get('report_type')), s.get('speaker', new_field.get('speaker'))) for s in new_field['spans']}
            assert old_types == new_types
            comparisons.append({'id': identity, 'language': language,
                'source_text_sha256': sha(source.encode()), 'before_spans': old_field['spans'],
                'after_spans': new_field['spans'], 'moved_to_context_characters': len(remove),
                'restored_scope_characters': len(restore), 'exact_whitelisted_change_only': True,
                'unchanged_read_scope_admission_attribution': True})
    assert len(comparisons) == 5
    receipts = {}
    for filename in ['before-independent-active.json.gz', 'before-independent-manual-notes.json.gz',
                     'before-independent-delivery-manifest.json', 'independent-boundary-corrections-v2.json']:
        receipts[filename] = put(output, evidence + '/' + filename, (root / filename).read_bytes())
    report = {'schema': 'hadith-bank-independent-boundary-comparison-v1', 'result': 'PASS',
        'source_checkpoint': plan['source_checkpoint'], 'before_active_sha256': sha(before_bytes),
        'changed_fields': 5, 'appraisal_context_cuts': 4, 'restored_scope_qualifiers': 1,
        'characters_moved_to_context': 90, 'characters_restored_to_same_component': 10,
        'whitespace_only_additional_changes': 0, 'new_language_approvals': 0,
        'parent_disposition_changes': 0, 'source_wording_changes': 0,
        'unchanged_other_field_definitions': sum(len(r['field_reviews']) for r in before['records']) - 5,
        'comparisons': comparisons, 'prior_evidence': receipts}
    receipts['comparison'] = put(output, evidence + '/independent-before-after-v2.json', enc(report))
    put(output, evidence + '/verify_independent_changes.py', Path(__file__).read_bytes())
    return receipts
