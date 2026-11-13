"""Preserve complete v1 and rebuild only the independently accepted2732 Urdu scope."""
from pathlib import Path
import copy
import gzip
import hashlib
import json
import runpy

HERE = Path(__file__).resolve().parent
OUT = HERE / 'publish-v2'
NAME = '20261113-checkpoint64f4-muslim13-ibnmajah13-manual-v1'
E = Path('imports/web-deenhindi-20261112/reviews/evidence') / NAME
A = E / 'independent-appraisal-amendment-v2'
PEER = HERE.parent / 'phase23-checkpoint64f4-muslim-ibnmajah26-independent-audit'
sha = lambda b: hashlib.sha256(b).hexdigest()
git = lambda b: hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
enc = lambda v: (json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
assert not (HERE / 'delivery-manifest-v2.json').exists(), 'Frozen v2 must not be rewritten.'


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, ('immutable data differs', str(path))
    else:
        path.write_bytes(data)


v1raw = (HERE / 'delivery-manifest-v1.json').read_bytes()
assert sha(v1raw) == '594c078166ec14b6d4d04a542311bba33486db7fdff8781cb477e88b26571fda'
v1 = json.loads(v1raw)
assert len(v1['files']) == 24
old_bindings = []
for item in v1['files']:
    data = Path(item['local_path']).read_bytes()
    assert len(data) == item['bytes'] and sha(data) == item['sha256']
    put(OUT / A / 'previous-v1' / item['path'], data)
    old_bindings.append({'path': item['path'], 'bytes': len(data), 'sha256': sha(data)})
put(OUT / A / 'previous-v1/delivery-manifest-v1.json', v1raw)
for name in ['validation-v1.json', 'boundary-view-v1.json', 'derived-preview-v1.jsonl.gz']:
    put(OUT / A / 'previous-v1-local' / name, (HERE / name).read_bytes())
inputs = {}
for name, expected in [
        ('independent-boundary-findings-v1.json', '4b0acdb485f3e1631da3bd0af9c00966850331bf6897b2c137afb974a94c0f26'),
        ('accepted-field-plan-v1.json', '3b06334282103408e95bfc3e3f331816751569e693a498fb0586c109addbb725')]:
    data = (PEER / name).read_bytes()
    assert sha(data) == expected
    put(OUT / A / name, data)
    inputs[name] = json.loads(data)
put(OUT / A / 'amend_v2.py', Path(__file__).read_bytes())
builder = (HERE / 'package_and_validate.py').read_text()
replacements = {
    'from manual_boundaries import READINGS': 'from manual_boundaries_v2 import READINGS',
    "OUT = ROOT / 'publish-v1'": "OUT = ROOT / 'publish-v2'",
    'delivery-manifest-v1.json': 'candidate-builder-v2-manifest.json',
    'validation-v1.json': 'validation-v2.json',
    'boundary-view-v1.json': 'boundary-view-v2.json',
    'derived-preview-v1.jsonl.gz': 'derived-preview-v2.jsonl.gz',
    "'manual_boundaries.py', 'verify_local_sources.py'": "'manual_boundaries.py', 'manual_boundaries_v2.py', 'verify_local_sources.py'",
    "'freeze_source_first_readings.py', 'package_and_validate.py'": "'freeze_source_first_readings.py', 'package_and_validate.py', 'package_and_validate_v2.py'",
}
for before, after in replacements.items():
    assert before in builder, before
    builder = builder.replace(before, after)
put(HERE / 'package_and_validate_v2.py', builder.encode())
runpy.run_path(str(HERE / 'package_and_validate_v2.py'), run_name='__main__')
candidate = json.loads((HERE / 'candidate-builder-v2-manifest.json').read_bytes())
old_active = Path(next(f['local_path'] for f in v1['files'] if f['path'] == v1['active_ledger_path'])).read_bytes()
new_active = (OUT / v1['active_ledger_path']).read_bytes()
assert sha(old_active) == '568ed5cdb8cc1f1ab5dd965e12998f5622338a8e26365da83d5f379cb5f01b7f'
old_document, new_document = [json.loads(gzip.decompress(v)) for v in (old_active, new_active)]
assert {k:v for k,v in old_document.items() if k != 'records'} == {k:v for k,v in new_document.items() if k != 'records'}
old = {r['occurrence_id']:r for r in old_document['records']}
new = {r['occurrence_id']:r for r in new_document['records']}
plan = {(f['id'],f['language']): f['expected_field_review'] for f in inputs['accepted-field-plan-v1.json']['fields']}
assert len(plan) == 130 and set(old) == set(new)
sources = {'deenhindi-' + r['collection'] + ':' + r['number']:r
           for r in map(json.loads, (HERE / 'input/cohort.jsonl').read_bytes().splitlines())}
checks = {'unchanged_whole_parents':0, 'unchanged_other_fields':0, 'unchanged_other_reviewed_fields':0,
          'unchanged_unread_fields':0, 'restored_characters':0, 'restored_utf8_bytes':0, 'removed_characters':0}
for oid, before in old.items():
    after = new[oid]
    assert {k:v for k,v in before.items() if k != 'fields'} == {k:v for k,v in after.items() if k != 'fields'}
    if oid != 'deenhindi-ibnmajah:2732':
        assert before == after
        checks['unchanged_whole_parents'] += 1
    for bf, af in zip(before['fields'], after['fields']):
        key = (oid, bf['language'])
        assert af == plan[key], ('final field differs from accepted complete plan', key)
        if key != ('deenhindi-ibnmajah:2732', 'ur'):
            assert bf == af
            checks['unchanged_other_fields'] += 1
            checks['unchanged_other_reviewed_fields' if bf['reviewed'] else 'unchanged_unread_fields'] += 1
            continue
        text = sources[oid]['source_record'][bf['source_field']]
        assert sha(text.encode()) == bf['text_sha256'] == af['text_sha256']
        assert text[1452:1460] == '( واضح )'
        positions = lambda f: {p for s in f['selected_spans'] for p in range(s['start'],s['end'])}
        old_positions, new_positions = positions(bf), positions(af)
        assert new_positions - old_positions == set(range(1452,1460)) and not old_positions - new_positions
        assert len(af['selected_spans']) == len(bf['selected_spans']) - 1
        changed_component = [s for s in af['selected_spans'] if s['component_id'] == 'abd-al-malik-judgment-appraisal']
        assert len(changed_component) == 1 and (changed_component[0]['start'], changed_component[0]['end']) == (1278,1486)
        def labels(field):
            return {s['component_id']:(s['report_type'],s['source_report_family_id']) for s in field['selected_spans']}
        assert labels(bf) == labels(af)
        old_speakers = {s['component_id']:s['speaker'] for s in bf['selected_spans']}
        for s in af['selected_spans']:
            if s['component_id'] != 'abd-al-malik-judgment-appraisal':
                assert s['speaker'] == old_speakers[s['component_id']]
        checks['restored_characters'] += 8
        checks['restored_utf8_bytes'] += len(text[1452:1460].encode())
assert checks == {'unchanged_whole_parents':25, 'unchanged_other_fields':129,
    'unchanged_other_reviewed_fields':54, 'unchanged_unread_fields':75,
    'restored_characters':8, 'restored_utf8_bytes':12, 'removed_characters':0}
initial = (HERE / 'complete-source-first-readings.json').read_bytes()
assert sha(initial) == '5f4d83fb03c7cfd889333e94e6738f4bf82880d2331506dc2122ad5eac96fc6c'
for item in v1['files']:
    assert sha(Path(item['local_path']).read_bytes()) == item['sha256']
assert (HERE / 'delivery-manifest-v1.json').read_bytes() == v1raw
validation = json.loads((HERE / 'validation-v2.json').read_bytes())
assert validation['counts']['selected_spans'] == 115 and validation['counts']['typed_components'] == 91
assert validation['counts']['reviewed_context_gaps'] == 52 and validation['counts']['retained_meaningful_structures'] == 37
receipt = {'schema':'hadith-bank-source-bound-exact-appraisal-scope-amendment-v2', 'result':'PASS',
    'source_commit':v1['source_commit'], 'previous_manifest_sha256':sha(v1raw),
    'previous_active_sha256':sha(old_active), 'final_active_sha256':sha(new_active),
    'independent_findings_sha256':'4b0acdb485f3e1631da3bd0af9c00966850331bf6897b2c137afb974a94c0f26',
    'complete_accepted_plan_sha256':'3b06334282103408e95bfc3e3f331816751569e693a498fb0586c109addbb725',
    'checks':checks, 'all130_final_field_definitions_equal_independent_complete_plan':True,
    'all24_v1_payloads_and_original_manifest_archived_exact':True, 'previous_files':old_bindings,
    'initial_source_first_receipt_unchanged':sha(initial), 'initial_context_judgment_preserved':True,
    'explicit_reconsideration':'The immutable initial source reading treated the parenthetic clear adjective as a supplementary lexical clarification. The independent complete-field reading instead distinguished it as event-specific scope inside Abd al-Malik’s own appraisal of this judgment. Having reopened the entire Urdu field, the primary reviewer accepts that distinction: the complete no-doubt clause does not make the actual adjective disposable. The eight printed characters are retained as qualified source rendering within the same historical speaker component and report family, not as a new event, a verbatim historical guarantee, a Prophet saying, a definition, or a detached compiler reliability comment. The wala definition and final marker remain context.',
    'parent_dispositions_changed':0, 'component_id_type_actor_family_changed':0,
    'new_occurrences_created':0, 'new_linguistic_reading_credit':0,
    'source_http_requests':0, 'github_writes':0, 'independent_pro_qc':'not_performed',
    'native_validation_sha256':sha((HERE / 'validation-v2.json').read_bytes())}
put(OUT / A / 'amendment-receipt.json', enc(receipt))
put(HERE / 'amendment-receipt-v2.json', enc(receipt))
portable_path = E / 'portable-manifest.json'
files = []
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.relative_to(OUT) != portable_path:
        data = p.read_bytes()
        files.append({'path':p.relative_to(OUT).as_posix(), 'local_path':str(p),
                      'bytes':len(data), 'sha256':sha(data), 'git_blob_sha1':git(data)})
portable = {k:copy.deepcopy(v) for k,v in candidate.items() if k != 'files'}
portable.update(schema='hadith-bank-source-review-portable-manifest-v2',
                files=[{k:v for k,v in item.items() if k != 'local_path'} for item in files])
(OUT / portable_path).write_bytes(enc(portable))
data = (OUT / portable_path).read_bytes()
files.append({'path':portable_path.as_posix(), 'local_path':str(OUT / portable_path),
              'bytes':len(data), 'sha256':sha(data), 'git_blob_sha1':git(data)})
final = {k:copy.deepcopy(v) for k,v in candidate.items() if k != 'files'}
final.update(schema='hadith-bank-source-review-delivery-v2', files=files,
             total_files=len(files), total_bytes=sum(f['bytes'] for f in files),
             amendment_receipt_sha256=sha(enc(receipt)), previous_v1_manifest_sha256=sha(v1raw))
put(HERE / 'delivery-manifest-v2.json', enc(final))
print(json.dumps({'result':'PASS', 'manifest_sha256':sha(enc(final)), 'active_sha256':sha(new_active),
                  'amendment_receipt_sha256':sha(enc(receipt)), 'files':len(files),
                  'bytes':final['total_bytes'], 'checks':checks}, indent=2))
