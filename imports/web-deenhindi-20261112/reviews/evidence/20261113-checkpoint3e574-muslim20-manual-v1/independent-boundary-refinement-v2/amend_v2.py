"""Apply the explicitly agreed phase19 boundaries; preserve every frozen v1 byte."""
from pathlib import Path
import ast
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'publish-v2'
PEER = ROOT.parent / 'phase19-checkpoint3e574-muslim20-independent-audit'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews
from manual_source_first_readings import NOTES
from verify_local_sources import verify as verify_local_sources

sha = lambda data: hashlib.sha256(data).hexdigest()
enc = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
COMMIT = '3e574b9e7e4dd7cf8bc23232249004a18692c61c'
NAME = '20261113-checkpoint3e574-muslim20-manual-v1'
SOURCE_ONLY = {'2484', '2512', '2519', '2540', '2551'}
REV = Path('imports/web-deenhindi-20261112/reviews')
EVIDENCE = REV / 'evidence' / NAME
ACTIVE = REV / ('source-review-' + NAME + '.json.gz')
AMEND = EVIDENCE / 'independent-boundary-refinement-v2'

assert not (ROOT / 'delivery-manifest-v2.json').exists(), 'Do not rewrite a frozen package.'
v1_manifest_bytes = (ROOT / 'delivery-manifest-v1.json').read_bytes()
assert sha(v1_manifest_bytes) == '5850b223457d7b89dc0e0e5b7e354af176924c524240bf6d713ab70cac54fc81'
v1_manifest = json.loads(v1_manifest_bytes)
old_active = (ROOT / 'publish-v1' / ACTIVE).read_bytes()
assert sha(old_active) == '0bbd74ad3c3b0cfe05813936739886ff8f464dd6a7aa0e16f2c49667d66843dc'
old_doc = json.loads(gzip.decompress(old_active))
findings_bytes = (PEER / 'independent-boundary-findings-v1.json').read_bytes()
assert sha(findings_bytes) == 'b68399b2a2db3370112bf270eccc454b52d4e2f020be31d4889d6640b8062bd8'
findings = json.loads(findings_bytes)
assert findings['primary_active_sha256'] == sha(old_active)
assert findings['primary_manifest_sha256'] == sha(v1_manifest_bytes)
accepted_plan_bytes = (PEER / 'accepted-reviewed-field-plan-v1.2.json').read_bytes()
assert sha(accepted_plan_bytes) == 'aca4cf394178bfd09c430a800b3557065fe2d858f1af0a60909b9f5249098139'
accepted_plan = json.loads(accepted_plan_bytes)
metadata_supplement_bytes = (PEER / 'source-scope-description-supplement.json').read_bytes()
assert sha(metadata_supplement_bytes) == '97dcb51ca36d80addb806bf9af6e2fe4a94b44d9eff026bba2d8915c7ee6fd6f'
metadata_supplement = json.loads(metadata_supplement_bytes)
assert sha((PEER / 'prefatory-route-description-supplement.json').read_bytes()) == '26889020c0012f555808b09c2f54f423c53e0169b32ffcedc34f5ad897123f21'
grouped = collections.defaultdict(list)
for item in findings['findings']:
    grouped[item['id'], item['language']].append(copy.deepcopy(item))
assert len(grouped) == 18 and len({key[0] for key in grouped}) == 9


def put(relative, data):
    path = OUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


archived = []
for f in v1_manifest['files']:
    data = Path(f['local_path']).read_bytes()
    assert len(data) == f['bytes'] and sha(data) == f['sha256']
    put(Path(f['path']), data)
    dest = put(AMEND / 'previous-v1' / f['path'], data)
    archived.append({'original_path': f['path'], 'archived_path': dest.relative_to(OUT).as_posix(),
                     'bytes': len(data), 'sha256': sha(data)})
assert len(archived) == 14
put(AMEND / 'previous-v1/delivery-manifest-v1.json', v1_manifest_bytes)
for name in ('boundary-view-v1.json', 'derived-preview-v1.jsonl.gz', 'validation-v1.json'):
    put(AMEND / 'previous-v1-derived' / name, (ROOT / name).read_bytes())
for name in ('independent-boundary-findings-v1.json', 'accepted-reviewed-field-plan.json',
             'accepted-reviewed-field-plan-v1.1.json', 'accepted-reviewed-field-plan-v1.2.json',
             'source-scope-description-supplement.json', 'prefatory-route-description-supplement.json'):
    put(AMEND / name, (PEER / name).read_bytes())

source_bytes = (ROOT / 'input/cohort.jsonl').read_bytes()
assert sha(source_bytes) == '86a0593c08e0284ebf0ff6118c773451e8a5f807983a2e88491f26878aecbab0'
rows = [json.loads(line) for line in source_bytes.splitlines()]
saved_by_id = {'deenhindi-' + row['collection'] + ':' + row['number']: row for row in rows}
old_records = {row['occurrence_id']: row for row in old_doc['records']}

refinements = {
    'deenhindi-muslim:2487': 'Final v2 refinement: the complete multi-step prefatory route, including its genealogy apposition, is retained as source context before the final reporter’s actual predicate. The announced three decisions, supplied charity/gift body, legal domain and without-hesitation eating instruction remain exact. This supersedes the earlier boundary treatment of the prefatory route without rewriting the initial full reading.',
    'deenhindi-muslim:2501': 'Final v2 refinement: the supplied three-tens predicate is part of the source-rendered gesture description and remains selected. Preserve its unresolved tension with the printed twenty-nine. The final no-word-thirty comparison remains context; neither source wording nor numerical discrepancy is harmonized.',
    'deenhindi-muslim:2517': 'Final v2 refinement: the source’s Eid qualification identifies the festival/end-of-month domain of the fast-breaking command and remains selected. It is meaningful act scope, not an interchangeable synonym. All conditions, source honorific wording and thirty-day quantity remain exact.',
    'deenhindi-muslim:2525': 'Final v2 refinement: the exact introductory multi-step name list is context; the complete Saad final-reporter frame, actual hand actions, saying and third-time finger reduction remain selected without an invented numerical total.',
    'deenhindi-muslim:2534': 'Final v2 refinement: the two prefatory transmitters remain source context, while the complete Sahl frame, actual recitation, thread practice and supplied revelation account remain selected and unmodified.',
    'deenhindi-muslim:2535': 'Final v2 refinement: the two prefatory transmitters remain context before Sahl’s coherent frame. Preserve all actual own thread practice and subsequent understanding, without supplying the absent opening verse.',
    'deenhindi-muslim:2543': 'Final v2 metadata refinement only: the Hindi transmitter is printed as defective इश्क़, not an explicitly corrected Ishaq. Preserve that exact defect in the source-qualified description; every selected position and the unknown ultimate voice remain unchanged.',
    'deenhindi-muslim:2544': 'Final v2 refinement: the two prefatory names remain context. The complete Samurah hearing frame, explicitly named Muhammad the Messenger, both negative objects and until-it-spreads condition remain selected.',
    'deenhindi-muslim:2552': 'Final v2 refinement: only the multi-step prefatory routes/lists in Arabic, Hindi, Urdu and Roman Urdu move to context. Each final Zayd frame and all three separately qualified voices remain selected; the actual pronoun/honorific differences, missing links, English measure and same-family relationships are unchanged.'}

descriptions = {}
for item in metadata_supplement['changes']:
    descriptions[item['id'], item['language'], item['component_id']] = {
        'before': item['before_speaker_description'], 'after': item['after_speaker_description']}
descriptions['deenhindi-muslim:2487', 'ur', 'report-1'] = {
    'before': 'Aisha’s source report announces three legal decisions but supplies only the actual charity/gift account and eating instruction here. The legal domain and without-hesitation manner remain supplied scope; only the route genealogy apposition is context.',
    'after': 'Aisha’s source report announces three legal decisions but supplies only the actual charity/gift account and eating instruction here. The legal domain and without-hesitation manner remain supplied scope; the full prefatory route and its inserted genealogy remain source context.'}
for item in findings['findings']:
    if item['change'] == 'qualify_source_defective_transmitter_name_in_one_component_metadata':
        descriptions[item['id'], item['language'], item['component_id']] = {
            'before': item['before_speaker'], 'after': item['after_speaker']}
assert len(descriptions) == 5

original_rules = (ROOT / 'manual_boundaries.py').read_bytes()
assert original_rules == (ROOT / 'publish-v1' / EVIDENCE / 'manual_boundaries.py').read_bytes()
append = '\n\n# Explicit final v2 refinements. The original source-first NOTES remain immutable.\n'
append += 'V2_EXACT_CHANGES = ' + repr(dict(grouped)) + '\n'
append += 'V2_DESCRIPTIONS = ' + repr(descriptions) + '\n'
append += 'V2_REFINEMENTS = ' + repr(refinements) + '\n'
append += '''for (_oid, _language), _items in V2_EXACT_CHANGES.items():
    _note = READINGS[_oid.removeprefix('deenhindi-')][_language]
    for _item in _items:
        if _item['change'] == 'move_multi_step_prefatory_route_to_context':
            # Existing genealogy cuts are already wholly inside this exact prefix.
            _note['context'] = [_cut for _cut in _note['context']
                if not (isinstance(_cut, str) and _cut in _item['text'])]
            _note['context'].append({'start': _item['start'], 'end': _item['end'], 'text': _item['text']})
        elif _item['change'] == 'restore_source_supplied_narrative_scope':
            assert _note['context'].count(_item['text']) == 1
            _note['context'].remove(_item['text'])
            _note['retained_meaningful_structures'].append(_item['text'])
        else:
            assert _item['change'] == 'qualify_source_defective_transmitter_name_in_one_component_metadata'
    for (_did, _dlang, _component), _change in V2_DESCRIPTIONS.items():
        if (_did, _dlang) != (_oid, _language):
            continue
        _parts = [part for part in _note.get('segments', []) if part.get('id') == _component and 'speaker' in part]
        if _parts:
            assert len(_parts) == 1 and _parts[0]['speaker'] == _change['before']
            _parts[0]['speaker'] = _change['after']
        else:
            assert _note['speaker'] == _change['before']
            _note['speaker'] = _change['after']
    _note['note'] += ' ' + V2_REFINEMENTS[_oid]
    _note['boundary_refinement'] = {'version': 'v2', 'initial_full_reading_note_preserved': True,
        'independent_findings_sha256': 'b68399b2a2db3370112bf270eccc454b52d4e2f020be31d4889d6640b8062bd8',
        'final_source_bound_judgment': V2_REFINEMENTS[_oid]}
'''
new_rules = original_rules + append.encode()
v2_rules = ROOT / 'manual_boundaries_v2.py'
v2_rules.write_bytes(new_rules)
spec = importlib.util.spec_from_file_location('phase19_final_v2_boundaries', v2_rules)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
READINGS = module.READINGS
put(EVIDENCE / 'manual_boundaries.py', new_rules)

# Reuse only the frozen source-span functions; never rerun the v1 package writer.
packager = (ROOT / 'package_and_validate.py').read_text()
assert packager.encode() == (ROOT / 'publish-v1' / EVIDENCE / 'package_and_validate.py').read_bytes()
functions = [node for node in ast.parse(packager).body if isinstance(node, ast.FunctionDef)
             and node.name in ('anchor', 'complement', 'span_for', 'field_review')]
assert {node.name for node in functions} == {'anchor', 'complement', 'span_for', 'field_review'}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(ROOT / 'package_and_validate.py'), 'exec'), globals())
document = copy.deepcopy(old_doc)
records = document['records']
positions = lambda field: {i for span in field['selected_spans'] for i in range(span['start'], span['end'])}
normalize = lambda span: {key: value for key, value in span.items() if key != 'reason'}
approved = {(field['id'], field['language']): field for field in accepted_plan['fields']}
assert len(approved) == 58
differences = []
for record in records:
    oid = record['occurrence_id']
    base = importer.canonical_record(saved_by_id[oid])
    for index, before in enumerate(list(record['fields'])):
        key = oid, before['language']
        if key not in grouped:
            continue
        text = base['language_versions'][index]['text']
        after = field_review(base['language_versions'][index], index,
                             READINGS[oid.removeprefix('deenhindi-')][key[1]])
        cut, restored = set(), set()
        for item in grouped[key]:
            assert item['source_text_sha256'] == sha(text.encode())
            if 'start' not in item:
                continue
            start, end = item['start'], item['end']
            assert text[start:end] == item['text'] and sha(text[start:end].encode()) == item['sha256']
            if item['change'] == 'restore_source_supplied_narrative_scope':
                restored.update(range(start, end))
            else:
                cut.update(range(start, end))
        before_mask, after_mask = positions(before), positions(after)
        assert after_mask == (before_mask - cut) | restored
        assert after_mask - before_mask == restored
        assert [normalize(span) for span in after['selected_spans']] == approved[key]['approved_spans']
        for name in ('version_id', 'language', 'source_field', 'field_path', 'text_sha256',
                     'text_chars', 'reviewed', 'chars_reviewed', 'bytes_reviewed'):
            assert before[name] == after[name]
        removed = before_mask - after_mask
        record['fields'][index] = after
        differences.append({'occurrence_id': oid, 'language': key[1],
            'before_field_sha256': sha(enc(before)), 'after_field_sha256': sha(enc(after)),
            'removed_selected_characters': len(removed),
            'removed_selected_utf8_bytes': sum(len(text[i].encode()) for i in removed),
            'restored_characters': len(restored),
            'restored_utf8_bytes': sum(len(text[i].encode()) for i in restored),
            'exact_independent_final_span_plan_match': True, 'explicit_changes': grouped[key]})

unchanged_fields = unchanged_parents = 0
for record in records:
    before = old_records[record['occurrence_id']]
    assert {k: v for k, v in record.items() if k != 'fields'} == {k: v for k, v in before.items() if k != 'fields'}
    unchanged_parents += record == before
    for old_field, final_field in zip(before['fields'], record['fields']):
        if old_field == final_field:
            unchanged_fields += 1
        else:
            assert (record['occurrence_id'], final_field['language']) in grouped
        if final_field['reviewed']:
            plan = approved[record['occurrence_id'], final_field['language']]
            assert [normalize(span) for span in final_field['selected_spans']] == plan['approved_spans']
assert len(differences) == 18 and unchanged_fields == 82 and unchanged_parents == 11
assert sum(x['removed_selected_characters'] for x in differences) == 712
assert sum(x['removed_selected_utf8_bytes'] for x in differences) == 1491
assert sum(x['restored_characters'] for x in differences) == 31
assert sum(x['restored_utf8_bytes'] for x in differences) == 52
active_data = gzip.compress(enc(document), mtime=0)
put(ACTIVE, active_data)
reading_receipt = (ROOT / 'complete-source-first-readings.json').read_bytes()
assert sha(reading_receipt) == 'dc0c5d01715f1e1784af223fd588e90ccc05f4f8b920ab6700882ec824c61ba0'
put(EVIDENCE / 'manual-field-boundary-notes.json.gz', gzip.compress(enc({
    'schema': 'hadith-bank-manual-field-boundaries-v2', 'source_commit': COMMIT,
    'source_first_receipt_sha256': sha(reading_receipt), 'records': READINGS,
    'explicit_v2_refinements': refinements, 'initial_source_first_notes_rewritten': False,
    'no_heuristic_batch_approvals': True, 'independent_pro_qc': 'not_performed'}), mtime=0))
boundary_view = []
for decision in records:
    saved = saved_by_id[decision['occurrence_id']]
    boundary_view.append({'occurrence_id': decision['occurrence_id'], 'decision': decision['decision'],
        'source_record_sha256': decision['source_record_sha256'],
        'fields': [{'language': f['language'], 'text_sha256': f['text_sha256'],
            'source_text': saved['source_record'][f['source_field']], 'reason': f['reason'],
            'selected': [dict(s, text=saved['source_record'][f['source_field']][s['start']:s['end']]) for s in f['selected_spans']],
            'context': [dict(s, text=saved['source_record'][f['source_field']][s['start']:s['end']]) for s in f['reviewed_context_spans']]}
            for f in decision['fields'] if f['reviewed']]})
put(EVIDENCE / 'selected-context-boundary-view.json.gz', gzip.compress(enc(boundary_view), mtime=0))
local_source_validation = verify_local_sources()
assert local_source_validation['result'] == 'PASS'
baseline_path = EVIDENCE / 'source-ledger-20.jsonl.gz'
baseline_data = (OUT / baseline_path).read_bytes()
assert gzip.decompress(baseline_data) == source_bytes
native = packager[packager.index('engine = SourceReviews'):packager.index('\nmanifest =')]
native = native.replace('validation-v1.json', 'validation-v2.json').replace('boundary-view-v1.json', 'boundary-view-v2.json').replace('derived-preview-v1.jsonl.gz', 'derived-preview-v2.jsonl.gz')
exec(compile(native, str(ROOT / 'package_and_validate.py') + ' [native v2 replay]', 'exec'), globals())
assert totals['admitted_characters'] == 8026 and totals['admitted_utf8_bytes'] == 16559
assert totals['selected_spans'] == 51 and totals['typed_components'] == 45
receipt = {'schema': 'hadith-bank-exact-independent-boundary-refinement-v2', 'result': 'PASS',
    'source_commit': COMMIT, 'previous_manifest_sha256': sha(v1_manifest_bytes),
    'previous_active_sha256': sha(old_active), 'final_active_sha256': sha(active_data),
    'independent_findings_sha256': sha(findings_bytes), 'accepted_final_span_plan_sha256': sha(accepted_plan_bytes),
    'primary_assessment': 'Reopened every affected whole source field and accepted the exact14 prefatory-route cuts, three source-scope restorations and source-defect metadata refinement. The five descriptive metadata updates remain tied to these same fields and do not alter source speakers or family identities.',
    'original_source_first_receipt_sha256': sha(reading_receipt), 'original_source_first_notes_unchanged': True,
    'multi_step_prefix_ranges_to_context': 14, 'newly_removed_selected_characters': 712,
    'newly_removed_selected_utf8_bytes': 1491, 'restored_characters': 31, 'restored_utf8_bytes': 52,
    'descriptive_speaker_metadata_changes': [{'id': oid, 'language': lang, 'component_id': component, **change}
        for (oid, lang, component), change in descriptions.items()],
    'no_unrequested_position_changes': True, 'unchanged_other_field_definitions': 82,
    'unchanged_other_reviewed_fields': 40, 'unchanged_unread_fields': 42, 'unchanged_whole_parents': 11,
    'all_parent_metadata_and_dispositions_exact': True, 'component_type_and_family_identities_preserved': True,
    'changes': differences, 'refinements': refinements, 'complete_v1_payloads_archived': archived,
    'all_v1_payloads_rehashed_unchanged': True, 'native_SourceReviews_apply_finish': 'PASS',
    'native_counts': dict(totals), 'source_files_reopened': 40, 'raw_reparses': 20,
    'source_http_requests': 0, 'github_writes': 0, 'independent_pro_qc': 'not_performed'}
put(AMEND / 'exact-amendment-and-validation.json', enc(receipt))
put(AMEND / 'amend_v2.py', Path(__file__).read_bytes())
for f in v1_manifest['files']:
    data = Path(f['local_path']).read_bytes()
    assert len(data) == f['bytes'] and sha(data) == f['sha256']
assert (ROOT / 'delivery-manifest-v1.json').read_bytes() == v1_manifest_bytes
portable_path = EVIDENCE / 'portable-manifest.json'
files = [{'path': p.relative_to(OUT).as_posix(), 'local_path': str(p), 'bytes': p.stat().st_size,
          'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*'))
         if p.is_file() and p.relative_to(OUT) != portable_path]
manifest = {'schema': 'hadith-bank-source-review-delivery-v2', 'source_commit': COMMIT, 'result': 'PASS',
    'review_batch': NAME, 'active_ledger_path': ACTIVE.as_posix(), 'active_ledger_sha256': sha(active_data),
    'previous_manifest_sha256': sha(v1_manifest_bytes),
    'amendment_receipt_path': (AMEND / 'exact-amendment-and-validation.json').as_posix(),
    'amendment_receipt_sha256': sha(enc(receipt)), 'expected_delta': v1_manifest['expected_delta'], 'files': files}
portable = {k: copy.deepcopy(v) for k, v in manifest.items() if k != 'files'}
portable['schema'] = 'hadith-bank-source-review-portable-manifest-v2'
portable['files'] = [{k: v for k, v in f.items() if k != 'local_path'} for f in files]
dest = put(portable_path, enc(portable))
manifest['files'].append({'path': portable_path.as_posix(), 'local_path': str(dest),
                         'bytes': dest.stat().st_size, 'sha256': sha(dest.read_bytes())})
data = enc(manifest)
(ROOT / 'delivery-manifest-v2.json').write_bytes(data)
print(json.dumps({'result': 'PASS', 'manifest_sha256': sha(data), 'active_sha256': sha(active_data),
    'files': len(manifest['files']), 'bytes': sum(x['bytes'] for x in manifest['files']),
    'amendment_sha256': sha(enc(receipt)), 'counts': dict(totals)}, indent=2))
