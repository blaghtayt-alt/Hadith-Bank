#!/usr/bin/env python3
"""Remove one unprinted location from one review reason; preserve every source span."""
import copy
import gzip
import hashlib
import json
import pprint
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import manual_boundaries

OLD = ROOT / 'publish-v1'
OUT = ROOT / 'publish-v2'
PREFIX = 'imports/web-deenhindi-20261112/reviews/checkpoint64f4-abudawud-tirmidhi31-20261113'
ACTIVE = 'imports/web-deenhindi-20261112/reviews/source-review-checkpoint64f4-abudawud-tirmidhi31-20261113.json.gz'
REV = PREFIX + '/independent-metadata-v2'
AUDIT = ROOT.parent / 'phase23-checkpoint64f4-mixed31-independent-audit'
sha = lambda b: hashlib.sha256(b).hexdigest()
enc = lambda x: (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def put(path, data):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def replace_once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def main():
    assert not OUT.exists() and not (ROOT / 'delivery-manifest-v2.json').exists()
    manifest_bytes = (ROOT / 'delivery-manifest-v1.json').read_bytes()
    assert sha(manifest_bytes) == '8cc3ad78ef48415e0c66964472d5fee88da34334891f5d926e9c0ebeb9054fc5'
    manifest = json.loads(manifest_bytes)
    assert len(manifest['files']) == 28
    for f in manifest['files']:
        data = (OLD / f['path']).read_bytes()
        assert len(data) == f['bytes'] and sha(data) == f['sha256']
        put(REV + '/before-v1/payload/' + f['path'], data)
    put(REV + '/before-v1/delivery-manifest-v1.json', manifest_bytes)
    provenance = {
        'independent-findings-v1.json': '10bd0184685de52befe9fc28e9c69429c2b8aae3672793e12202ebe6ac029751',
        'accepted-reviewed-field-plan-v1.json': 'b0a78242dfb8adc8e1ac4c489844b8ad8d8a763aa7ba3c12369bc39a4ea7a8ae',
    }
    for name, expected in provenance.items():
        data = (AUDIT / name).read_bytes()
        assert sha(data) == expected
        put(REV + '/' + name, data)
    findings = json.loads((AUDIT / 'independent-findings-v1.json').read_bytes())
    assert len(findings['findings']) == 1 and findings['boundary_changes'] == findings['parent_decision_changes'] == 0
    finding = findings['findings'][0]
    assert (finding['id'], finding['language'], finding['field_key']) == ('deenhindi-tirmidhi:2711', 'ur', 'reason')
    assert finding['before'].replace('door/', '', 1) == finding['expected']
    assert finding['before'].count('door/') == 1
    plan = json.loads((AUDIT / 'accepted-reviewed-field-plan-v1.json').read_bytes())
    expected_fields = {(r['id'], r['language']): r for r in plan['reviewed_fields']}
    assert len(expected_fields) == 65
    records = copy.deepcopy(manual_boundaries.records)
    row = next(r for r in records if r['key'] == 'tirmidhi:2711')
    assert row['fields']['ur']['reason'] == finding['before']
    row['fields']['ur']['reason'] = finding['expected']
    (ROOT / 'manual_boundaries_v2.py').write_text(
        '"""One exact independent metadata correction; no boundary, voice or source change."""\nrecords = '
        + pprint.pformat(records, width=110, sort_dicts=False) + '\n', encoding='utf-8')
    compiler = (ROOT / 'compile_review.py').read_text()
    compiler = replace_once(compiler, 'from manual_boundaries import records as instructions', 'from manual_boundaries_v2 import records as instructions')
    compiler = replace_once(compiler, "OUT=ROOT/'publish-v1'", "OUT=ROOT/'publish-v2'")
    compiler = compiler.replace('delivery-manifest-v1.json', 'delivery-manifest-v2.json')
    compiler = replace_once(compiler,
        "for n in ('source_first_notes.py','manual_boundaries.py','compile_review.py'):put(PREFIX+'/'+n,(ROOT/n).read_bytes())",
        "for target,source in (('source_first_notes.py','source_first_notes.py'),('manual_boundaries.py','manual_boundaries_v2.py'),('compile_review.py','compile_review_v2.py')):put(PREFIX+'/'+target,(ROOT/source).read_bytes())")
    (ROOT / 'compile_review_v2.py').write_text(compiler)
    subprocess.run([sys.executable, str(ROOT / 'compile_review_v2.py')], check=True)
    before_raw = (OLD / ACTIVE).read_bytes()
    after_raw = (OUT / ACTIVE).read_bytes()
    before, after = map(lambda b: json.loads(gzip.decompress(b)), (before_raw, after_raw))
    oldrows = {r['id']: r for r in before['records']}
    newrows = {r['id']: r for r in after['records']}
    assert oldrows.keys() == newrows.keys() and len(oldrows) == 31
    changed = []
    unchanged_fields = unchanged_parents = spans = 0
    for rid, oldrow in oldrows.items():
        newrow = newrows[rid]
        assert {k: v for k, v in oldrow.items() if k != 'field_reviews'} == {k: v for k, v in newrow.items() if k != 'field_reviews'}
        unchanged_parents += oldrow == newrow
        for old, new in zip(oldrow['field_reviews'], newrow['field_reviews'], strict=True):
            key = (rid, old['language'])
            assert new == expected_fields[key]['expected_field_review'], key
            assert new['spans'] == old['spans'] == expected_fields[key]['expected_spans']
            spans += len(new['spans'])
            if old == new:
                unchanged_fields += 1
            else:
                assert key == ('deenhindi-tirmidhi:2711', 'ur')
                assert old['reason'] == finding['before'] and new['reason'] == finding['expected']
                assert {k: v for k, v in old.items() if k != 'reason'} == {k: v for k, v in new.items() if k != 'reason'}
                changed.append({'id': rid, 'language': old['language'], 'before': old['reason'], 'after': new['reason'], 'all_source_ranges_and_attribution_metadata_unchanged': True})
    assert (len(changed), unchanged_fields, unchanged_parents, spans) == (1, 64, 30, 126)
    assert before['source_ledger_sha256'] == after['source_ledger_sha256']
    assert sha((ROOT / 'complete-source-first-readings.json').read_bytes()) == 'b043183c9fa4a3a46bc66053d878f978ab9d2b8c5afc9916485c5862dc9b486e'
    assert sha((ROOT / 'source_first_notes.py').read_bytes()) == '4c6abd0dbd5504fdd1d2d2ef132d4ffa6ba08790e31a3c0012a9a4b293c4757a'
    for f in manifest['files']:
        assert (OLD / f['path']).read_bytes() == (OUT / REV / 'before-v1/payload' / f['path']).read_bytes()
    native = json.loads((OUT / PREFIX / 'validation.json').read_bytes())
    assert native['result'] == 'PASS'
    assert native['totals'] == json.loads((OLD / PREFIX / 'validation.json').read_bytes())['totals']
    receipt = {
        'schema': 'hadith-bank-bounded-independent-metadata-amendment-v2', 'result': 'PASS',
        'source_checkpoint': after['source_checkpoint'],
        'before_manifest_sha256': sha(manifest_bytes), 'before_active_ledger_sha256': sha(before_raw),
        'after_active_ledger_sha256': sha(after_raw), 'source_baseline_sha256': after['source_ledger_sha256'],
        'independent_findings_sha256': provenance['independent-findings-v1.json'],
        'accepted_full_field_plan_sha256': provenance['accepted-reviewed-field-plan-v1.json'],
        'changes': changed, 'changed_field_reasons': 1,
        'review_description_characters_removed': 5, 'review_description_utf8_bytes_removed': 5,
        'source_characters_added': 0, 'source_characters_removed': 0,
        'source_selected_spans_preserved': 126, 'other_reviewed_field_definitions_exact': 64,
        'unread_field_slots_exact': 90, 'other_whole_parents_exact': 30,
        'all28_original_payload_files_and_manifest_archived_exact': True,
        'initial_source_first_notes_and_reading_receipt_unchanged': True,
        'native_lossless_partitions': 155, 'source_files_reopened': 62, 'raw_html_reparses': 31,
        'native_totals': native['totals'],
        'explicit_refinement': 'The earlier review description introduced a door despite the own source only supplying requested appearance/permission and an identity exchange. This v2 removes only that unsupported descriptive word and slash. Every actual source quotation, context partition, actor, family, type and parent decision remains exact; the earlier wording and all initial notes remain available in immutable before evidence.',
        'new_readings_claimed': 0, 'new_translation_created': False,
        'source_http_requests': 0, 'github_writes': 0, 'shared_engine_changes': 0,
        'independent_pro_qc': 'not_performed',
        'limitation': 'This primary amendment is bound to the independent plan; the independent final hash-bound audit is a separate gate.'
    }
    receipt_bytes = enc(receipt)
    put(REV + '/amendment-receipt.json', receipt_bytes)
    put(REV + '/revise_independent_metadata_v2.py', Path(__file__).read_bytes())
    packager = (ROOT / 'package_review.py').read_text()
    packager = replace_once(packager, 'from manual_boundaries import records as instructions', 'from manual_boundaries_v2 import records as instructions')
    packager = replace_once(packager, "OUT = ROOT / 'publish-v1'", "OUT = ROOT / 'publish-v2'")
    packager = packager.replace('delivery-manifest-v1.json', 'delivery-manifest-v2.json')
    packager = replace_once(packager, '5c1a6498cee4032d90466d365424b468cabb8548a10793932f451ef72306dfd4', sha(after_raw))
    packager = replace_once(packager, "(ROOT / 'boundary-view-v1.json')", "(ROOT / 'boundary-view-v2.json')")
    packager = replace_once(packager,
        "'schema': 'hadith-bank-source-bound-primary-review-v1', 'result': 'PASS',",
        "'schema': 'hadith-bank-source-bound-primary-review-v1', 'result': 'PASS', 'version': 2, 'bounded_metadata_amendment': " + repr({'receipt_path': REV + '/amendment-receipt.json', 'receipt_sha256': sha(receipt_bytes), 'changed_field_reasons': 1, 'source_boundary_changes': 0, 'earlier_source_first_notes_unchanged': True}) + ',')
    (ROOT / 'package_review_v2.py').write_text(packager)
    subprocess.run([sys.executable, str(ROOT / 'package_review_v2.py')], check=True)
    final_manifest = (ROOT / 'delivery-manifest-v2.json').read_bytes()
    final = json.loads(final_manifest)
    for f in final['files']:
        b = (OUT / f['path']).read_bytes()
        assert len(b) == f['bytes'] and sha(b) == f['sha256']
    print(json.dumps({'result': 'FROZEN_V2', 'manifest_sha256': sha(final_manifest), 'active_ledger_sha256': sha(after_raw), 'amendment_receipt_sha256': sha(receipt_bytes), 'files': final['total_files'], 'bytes': final['total_bytes'], 'changed_reasons': 1, 'other_reviewed_fields_exact': 64, 'unread_slots_exact': 90, 'other_parents_exact': 30, 'spans_exact': 126, 'source_text_changes': 0}, indent=2))


if __name__ == '__main__':
    main()
