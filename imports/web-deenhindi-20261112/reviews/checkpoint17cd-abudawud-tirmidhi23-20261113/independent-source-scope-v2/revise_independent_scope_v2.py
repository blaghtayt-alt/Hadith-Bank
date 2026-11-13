#!/usr/bin/env python3
"""Apply six independently agreed field refinements; preserve all frozen v1 bytes."""
from pathlib import Path
import copy, gzip, hashlib, json, pprint, subprocess, sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import manual_boundaries

PREFIX = 'imports/web-deenhindi-20261112/reviews/checkpoint17cd-abudawud-tirmidhi23-20261113'
ACTIVE = 'imports/web-deenhindi-20261112/reviews/source-review-checkpoint17cd-abudawud-tirmidhi23-20261113.json.gz'
OLD = ROOT / 'publish-v1'
OUT = ROOT / 'publish-v2'
REV = PREFIX + '/independent-source-scope-v2'
AUDIT = ROOT.parent / 'phase22-checkpoint17cd-mixed23-independent-audit'
sha = lambda b: hashlib.sha256(b).hexdigest()
enc = lambda x: (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def put(path, data):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def positions(field):
    return {i for s in field['spans'] for i in range(s['start'], s['end'])}


def label(field, index):
    return {k: v for k, v in next(s for s in field['spans'] if s['start'] <= index < s['end']).items()
            if k not in ('start', 'end', 'sha256')}


def replace_once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def main():
    assert not OUT.exists() and not (ROOT / 'delivery-manifest-v2.json').exists()
    manifest_bytes = (ROOT / 'delivery-manifest-v1.json').read_bytes()
    assert sha(manifest_bytes) == '147636cd951ff1714315f9b83b13362be327059a80d8361485172422f2a43565'
    manifest = json.loads(manifest_bytes)
    assert len(manifest['files']) == 27
    for f in manifest['files']:
        data = (OLD / f['path']).read_bytes()
        assert sha(data) == f['sha256'] and len(data) == f['bytes']
        put(REV + '/before-v1/payload/' + f['path'], data)
    put(REV + '/before-v1/delivery-manifest-v1.json', manifest_bytes)
    provenance = {
        'independent-boundary-findings-v1.json': '26264137521acb4ff79aa07ea876b2c201ccfffd1c41a615ce59c5e573afe31a',
        'accepted-reviewed-field-plan.json': 'f4acef0523c00a8b656a15b87df8800e13554507ce84c1ed9c816601dc8cc218',
        'independent-boundary-findings-v2.json': '6cda382a2d116e2f7b193d5a26d1888c6d135a1ebf265606d0211567e55ea5ed',
        'accepted-reviewed-field-plan-v2.json': '1ec8f955b73bcf791a28153a4e646a4280dc929198bc5716947b209192d76086',
        'speaker-qualification-plan-refinement.json': '0df1cbaf75bb7e0229387b0975475802e52f62364216d9b1080c6e3fb8f3969d',
        'peer-scope-adjudication-2622.json': '2b25450fb5622a567d958e594f4525d3ed9de0aa2c80cf27499891717233dda0',
        'root-scope-adjudication-2622.json': '3901df834a53dd4e40b55101ebd59318813526d8ad3c81ad0896a0f10195e5bd',
        'umbrella-description-refinement.json': 'd855f266746edcb8c9e2fe15c4461949ac5a443207882f3f2821dc67f003b1b5',
    }
    for name, expected in provenance.items():
        data = (AUDIT / name).read_bytes()
        assert sha(data) == expected
        put(REV + '/' + name, data)
    findings = json.loads((AUDIT / 'independent-boundary-findings-v2.json').read_bytes())
    plan = json.loads((AUDIT / 'accepted-reviewed-field-plan-v2.json').read_bytes())
    supplement = json.loads((AUDIT / 'umbrella-description-refinement.json').read_bytes())
    expected = {(f['id'], f['language']): f for f in plan['reviewed_fields']}
    changes = {(f['id'], f['language']): f for f in findings['findings']}
    assert len(changes) == 6 and len(expected) == 46
    umbrellas = {(f['id'], f['language']): f for f in supplement['changes']}
    sources = {r['collection'] + ':' + r['number']: r
               for r in map(json.loads, (ROOT / 'input/cohort.jsonl').read_bytes().splitlines())}
    records = copy.deepcopy(manual_boundaries.records)
    refined_reasons = {
        ('abudawud:2645', 'hi'): "Jarir reports the Khatham expedition, attempted protection by prostration, hasty killing, half compensation and the actual question/answer about both fires. The source-printed Islam/kufr parenthesis supplies material referents for that reply and remains qualified source-rendered scope, without an independent claim of verbatim historical wording. The exact half amount, condition and all source defects remain unchanged.",
        ('abudawud:2645', 'ur'): "The complete Urdu supplies the incident, half-diya response and fire question/answer. The Islam/kufr parenthesis materially identifies both fire referents and remains qualified source-rendered reply scope. The body footnotes and appended Abu Dawud transmitter-list/omitted-Jarir criticism stay context; no additional narrated event or verbatim historical parenthesis claim is made.",
        ('abudawud:2658', 'hi'): "The source-named बारे supplies the Hunayn encounter, a plural group's scattering and the Messenger's dismounting/walking. The source's defeat-and-flight parenthesis adds finite historical circumstances and remains within this source-rendered observation. The plural group stays unidentified, the defective Hindi wording is not repaired, and no separate incident is invented.",
        ('abudawud:2658', 'ur'): "The full Urdu supplies the encounter, scattering and dismounting observation. Its defeat-and-flight clause adds actual finite circumstances and remains as qualified source-rendered action/sequence scope. Preserve the original plural pronoun without deciding which group it names from another version, and retain all surrounding wording exactly.",
        ('tirmidhi:2622', 'hi'): "Abdullah ibn Shaqiq's actual report of the Companions' view, including its prayer exception, remains selected under his own voice. Tirmidhi's appended explicitly heard Abu Musab doctrinal/legal ruling is preserved completely as attributed compiler legal commentary. Its local hearing attribution does not alter its commentary role under the project's source-apparatus rule. Hindi's missing repentance-success/otherwise contrast and damaged join remain unchanged in context; nothing is filled from Urdu. This distinction does not reject a saying because of its severity, later speaker or absence of Prophetic attribution.",
        ('tirmidhi:2622', 'ur'): "The complete Urdu has the main Abdullah ibn Shaqiq report of the Companions' view and an appended Abu Musab doctrinal/legal ruling introduced by Tirmidhi's hearing. Admit the main attributed report only. Preserve the complete appendix, including its own repentance/otherwise condition and lexical definition, as attributed compiler legal commentary. The commentary role, rather than severity or a requirement for Prophetic attribution, determines its context placement; the full supplied wording remains available.",
    }
    for row in records:
        rid = 'deenhindi-' + row['key']
        for language, field in row['fields'].items():
            key = (rid, language)
            if key not in changes:
                continue
            finding = changes[key]
            text = sources[row['key']]['source_record'][{'hi': 'translationHindi', 'ur': 'translationUrdu'}[language]]
            assert sha(text.encode()) == finding['source_text_sha256']
            assert text[finding['start']:finding['end']] == finding['text']
            assert sha(finding['text'].encode()) == finding['sha256']
            if finding['kind'] == 'restore_material_source_rendered_scope':
                omissions = [c for c in field['omit_source_context'] if c['text'] == finding['text']]
                assert len(omissions) == 1 and omissions[0]['expected_count'] == 1
                field['omit_source_context'] = [c for c in field['omit_source_context'] if c != omissions[0]]
                if row['key'] == 'abudawud:2645':
                    correction = findings['speaker_description_qualification_corrections']
                    assert field['speaker'] == correction['previous_speaker_description']
                    field['speaker'] = correction['expected_speaker_description']
                    for span in field['spans']:
                        assert span['speaker'] == correction['previous_speaker_description']
                        span['speaker'] = correction['expected_speaker_description']
            else:
                assert row['key'] == 'tirmidhi:2622'
                assert len(field['spans']) == 2 and field['spans'][1]['component_id'] == 'independently-heard-abu-musab-saying'
                field['spans'] = field['spans'][:1]
                field['omit_source_context'] = []
                for name, previous in umbrellas[key]['previous'].items():
                    assert field[name] == previous
                    field[name] = umbrellas[key]['expected'][name]
            field['reason'] = refined_reasons[(row['key'], language)]
            field['reason'] += " V2 explicit reconsideration: the immutable initial source-first notes and complete v1 selections are retained in before evidence. The independent complete-field comparison and its source-role adjudication support this bounded refinement; no new reading, parent registration or canonical identity is claimed."
    (ROOT / 'manual_boundaries_v2.py').write_text(
        '"""Six exact independent source-scope refinements; original notes remain immutable."""\nrecords = '
        + pprint.pformat(records, width=110, sort_dicts=False) + '\n', encoding='utf-8')
    compiler = (ROOT / 'compile_review.py').read_text()
    compiler = replace_once(compiler, 'from manual_boundaries import records as instructions', 'from manual_boundaries_v2 import records as instructions')
    compiler = replace_once(compiler, "OUT=ROOT/'publish-v1'", "OUT=ROOT/'publish-v2'")
    compiler = compiler.replace('delivery-manifest-v1.json', 'delivery-manifest-v2.json')
    compiler = replace_once(compiler,
        "for n in ('source_first_notes.py','manual_boundaries.py','compile_review.py'):put(PREFIX+'/'+n,(ROOT/n).read_bytes())",
        "for target,source in (('source_first_notes.py','source_first_notes.py'),('manual_boundaries.py','manual_boundaries_v2.py'),('compile_review.py','compile_review_v2.py')):put(PREFIX+'/'+target,(ROOT/source).read_bytes())")
    compiler = replace_once(compiler,
        'Primary scope and the initial notes are preserved for the independent review gate.',
        'Version2 applies exactly six independently reviewed field refinements: four material source-scope restorations and the complete appended T2622 legal commentary retained as attributed context. Initial notes and every v1 payload remain unchanged in the versioned archive; the final hash-bound independent gate remains separate.')
    (ROOT / 'compile_review_v2.py').write_text(compiler)
    subprocess.run([sys.executable, str(ROOT / 'compile_review_v2.py')], check=True)
    before = json.loads(gzip.decompress((OLD / ACTIVE).read_bytes()))
    after = json.loads(gzip.decompress((OUT / ACTIVE).read_bytes()))
    oldrows = {r['id']: r for r in before['records']}
    newrows = {r['id']: r for r in after['records']}
    assert oldrows.keys() == newrows.keys()
    unchanged_fields = unchanged_parents = added_chars = removed_chars = added_bytes = removed_bytes = 0
    prior_selected = final_selected = final_spans = 0
    comparison = []
    for rid, oldrow in oldrows.items():
        newrow = newrows[rid]
        assert {k: v for k, v in oldrow.items() if k != 'field_reviews'} == {k: v for k, v in newrow.items() if k != 'field_reviews'}
        if oldrow == newrow:
            unchanged_parents += 1
        for old, new in zip(oldrow['field_reviews'], newrow['field_reviews'], strict=True):
            key = (rid, new['language'])
            assert new['spans'] == expected[key]['expected_spans'], key
            assert new['text_sha256'] == old['text_sha256'] == expected[key]['source_text_sha256']
            a, b = positions(old), positions(new)
            prior_selected += len(a); final_selected += len(b); final_spans += len(new['spans'])
            if key not in changes:
                assert old == new
                unchanged_fields += 1
                continue
            finding = changes[key]
            allowed = {'spans', 'reason'}
            if rid == 'deenhindi-abudawud:2645': allowed.add('speaker')
            if rid == 'deenhindi-tirmidhi:2622': allowed.update(('speaker', 'report_type'))
            assert {k: v for k, v in old.items() if k not in allowed} == {k: v for k, v in new.items() if k not in allowed}
            assert b - a == {i for start, end in finding['selection_add_ranges'] for i in range(start, end)}
            assert a - b == {i for start, end in finding['selection_remove_ranges'] for i in range(start, end)}
            for i in a & b:
                before_label, after_label = label(old, i), label(new, i)
                if rid == 'deenhindi-abudawud:2645':
                    assert before_label.pop('speaker') == findings['speaker_description_qualification_corrections']['previous_speaker_description']
                    assert after_label.pop('speaker') == findings['speaker_description_qualification_corrections']['expected_speaker_description']
                assert before_label == after_label
            text = sources[rid.removeprefix('deenhindi-')]['source_record'][new['source_field']]
            added_chars += len(b-a); removed_chars += len(a-b)
            added_bytes += len(''.join(text[i] for i in sorted(b-a)).encode())
            removed_bytes += len(''.join(text[i] for i in sorted(a-b)).encode())
            comparison.append({'id': rid, 'language': new['language'], 'before_field': old, 'after_field': new,
                               'exact_accepted_spans': True, 'surviving_component_id_type_family_and_actual_voice_preserved': True})
    assert (unchanged_fields, unchanged_parents, added_chars, added_bytes, removed_chars, removed_bytes) == (40, 20, 135, 283, 333, 697)
    assert (prior_selected, final_selected, final_spans) == (21311, 21113, 71)
    assert before['source_ledger_sha256'] == after['source_ledger_sha256']
    assert sha((ROOT / 'complete-source-first-readings.json').read_bytes()) == '429027e9525d6ce2e4965262523a3c7f20181b425251c864f01fe79f539345ff'
    assert sha((ROOT / 'source_first_notes.py').read_bytes()) == 'ec61368ae08341d30a624049b8ee835aaba21a71991fe64f908b9444876094d3'
    for f in manifest['files']:
        assert (OLD / f['path']).read_bytes() == (OUT / REV / 'before-v1/payload' / f['path']).read_bytes()
    receipt = {'schema': 'hadith-bank-bounded-independent-source-scope-amendment-v2', 'result': 'PASS',
        'source_checkpoint': after['source_checkpoint'], 'before_manifest_sha256': sha(manifest_bytes),
        'before_active_sha256': sha((OLD / ACTIVE).read_bytes()), 'after_active_sha256': sha((OUT / ACTIVE).read_bytes()),
        'provenance': provenance, 'exact_findings': findings['findings'], 'changed_field_comparison': comparison,
        'changed_fields': 6, 'changed_parents': 3, 'restored_ranges': 4, 'restored_characters': 135,
        'restored_utf8_bytes': 283, 'selected_characters_moved_to_context': 333,
        'selected_utf8_bytes_moved_to_context': 697, 'additional_whitespace_changes': 0,
        'final_selected_characters': 21113, 'final_selected_spans': 71,
        'all46_exact_final_span_definitions_match_accepted_plan': True,
        'two_abu2645_boundary_descriptions_match_authorized_supplement': True,
        'two_t2622_umbrella_descriptions_match_authorized_supplement': True,
        'only_two_legal_appendix_component_families_removed_from_selection': True,
        'unchanged_reviewed_fields': 40, 'unchanged_unread_nonempty_slots': 69,
        'unchanged_whole_parents': 20, 'parent_dispositions_unchanged': {'register': 23, 'source_only': 0},
        'all27_v1_payloads_and_manifest_archived_and_rehashed': True,
        'initial_notes_and_source_first_receipt_unchanged': True, 'new_semantic_reading_credit': 0,
        'new_parent_registration_credit': 0, 'source_http_requests': 0, 'github_writes': 0,
        'canonical_identity_fills': 0, 'independent_pro_qc': 'not_performed',
        'final_independent_hash_bound_gate': 'pending_parent'}
    put(REV + '/amendment-receipt.json', enc(receipt))
    put(REV + '/revise_independent_scope_v2.py', Path(__file__).read_bytes())
    packaging = (ROOT / 'package_review.py').read_text()
    packaging = replace_once(packaging, 'from manual_boundaries import records as instructions', 'from manual_boundaries_v2 import records as instructions')
    packaging = replace_once(packaging, "OUT=ROOT/'publish-v1'", "OUT=ROOT/'publish-v2'")
    packaging = packaging.replace('delivery-manifest-v1.json', 'delivery-manifest-v2.json').replace('boundary-view-v1.json', 'boundary-view-v2.json')
    packaging = packaging.replace('9be6b24bbca390f3317bc9b44bf08ebb55f84f3dae9e4e84e931d84607126134', sha((OUT / ACTIVE).read_bytes()))
    retained = {(f['id'].removeprefix('deenhindi-'), f['language'], f['text']): f['reason']
                for f in findings['findings'] if f['kind'] == 'restore_material_source_rendered_scope'}
    packaging = replace_once(packaging, '\ndef main():', '\nRETAINED.update(' + repr(retained) + ')\n\ndef main():')
    packaging = packaging.replace("totals['quotation_spans']==79 and totals['selected_characters']==21311", "totals['quotation_spans']==71 and totals['selected_characters']==21113")
    packaging = packaging.replace("counts['material_scopes_or_quotations']==38", "counts['material_scopes_or_quotations']==42")
    packaging = packaging.replace("cuts['literal_omissions']==26", "cuts['literal_omissions']==20").replace("'literal_context_cuts_inside_components':26", "'literal_context_cuts_inside_components':20")
    packaging = replace_once(packaging, "report={'schema':", "report={'revision':'v2 after exact independent scope and compiler-commentary refinements; all v1 bytes and initial source-first judgments archived','amendment_receipt_path':PREFIX+'/independent-source-scope-v2/amendment-receipt.json','schema':")
    packaging = replace_once(packaging,
        'T2622 separately attributes the Companion-view report to Abdullah ibn Shaqiq and the explicitly heard substantive scholarly saying to Abu Musab via Tirmidhi. The latter is a source quotation under the expanded attributed-sayings scope, not a Prophetic saying, contemporary legal advice or endorsement. Hindi’s missing repentance contrast is not filled from Urdu. The independent gate may assess this distinction separately.',
        'T2622 retains the actual Companion-view report under Abdullah ibn Shaqiq. The complete appended Abu Musab doctrinal/legal ruling, explicitly heard by Tirmidhi, is preserved as attributed compiler legal commentary. This source-role determination follows the owner rule rather than severity, speaker date or a Prophetic-only restriction. Hindi’s absent repentance contrast remains unfilled; the initial broader selection and its reasons remain archived with the explicit reconsideration.')
    (ROOT / 'package_review_v2.py').write_text(packaging)
    subprocess.run([sys.executable, str(ROOT / 'package_review_v2.py')], check=True)
    print(json.dumps({'amendment_receipt_sha256': sha((OUT / REV / 'amendment-receipt.json').read_bytes()),
                      'unchanged_reviewed_fields': unchanged_fields, 'unchanged_whole_parents': unchanged_parents,
                      'restored_characters': added_chars, 'moved_to_context_characters': removed_chars,
                      'selected_characters': final_selected, 'selected_spans': final_spans}, indent=2))


if __name__ == '__main__':
    main()
