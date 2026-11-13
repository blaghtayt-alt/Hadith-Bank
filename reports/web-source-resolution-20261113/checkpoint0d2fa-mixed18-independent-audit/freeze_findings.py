"""Freeze the independent decisions made after all 48 complete originals."""
from pathlib import Path
import copy
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PRIMARY = ROOT.parent / 'phase21-checkpoint0d2fa-abudawud-tirmidhi18-review'

def sha(value):
    return hashlib.sha256(value).hexdigest()

def enc(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def put(path, value):
    data = enc(value)
    if path.exists():
        assert path.read_bytes() == data, path
    else:
        path.write_bytes(data)
    return sha(data)

own_bytes = (ROOT / 'complete-independent-source-first-readings.json').read_bytes()
assert sha(own_bytes) == '3450dd1f29ac0fb5908c547ad90517a2bc5a9e8b95ce3ec6187aef5c762e3f89'
own = json.loads(own_bytes)
assert own['candidate_or_primary_notes_opened'] is False
assert own['all_complete_fields_read_before_candidate_inspection']
assert (own['complete_fields'], own['characters'], own['utf8_bytes']) == (48, 13826, 27038)
readings = {(field['id'], field['language']): field for field in own['fields']}
manifest_bytes = (PRIMARY / 'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_bytes) == 'e3514907ac9d889dc4bb58a8a47386eb535d0e6307bc837f56ae2aae263793f2'
manifest = json.loads(manifest_bytes)
active_file = next(file for file in manifest['files'] if file['path'].startswith('imports/web-deenhindi-20261112/reviews/source-review-'))
active_bytes = Path(active_file['local_path']).read_bytes()
assert sha(active_bytes) == '672e1b32189c64a5739c7fbce5bb61615986aeb7739ed7d9b8a626baed46019d'
ledger = json.loads(gzip.decompress(active_bytes))
records = {record['id']: record for record in ledger['records']}
assert len(records) == 18
fields = {(record['id'], field['language']): field for record in records.values() for field in record['field_reviews']}
assert fields.keys() == readings.keys()

batch_notes = {
    4: (25, 32, 4, "All eight exact candidate masks and attributions inspected. Tirmidhi2549 Hindi retains its own condensed transmission and actual Said recipient frame. Urdu's three reception/account components and its no-truly-inferior qualification are accepted, but two omitted parentheses identify the lower-ranking recipient and the Paradise-inhabitant referent of 'we'; restore them as source-qualified participant scope. Tirmidhi2551 Hindi/Urdu each omit the printed Fajr/Maghrib prayer-name parenthesis; restore this restriction on the prayer instruction while preserving the source's after-sunset wording and the different before-sunset verse rendering. No canonical correction or claim of verbatim Prophetic wording is made. Tirmidhi2558's complete death-ram episode and both counterfactuals are accepted; grading stays context. Tirmidhi2565's actual expressly cited finite houri-voices fragment is accepted with unknown ultimate speaker; verse/listening exposition remains context."),
    5: (33, 40, 0, "All eight exact candidate masks and attributions accepted. Tirmidhi2579 retains the own molar/Uhud comparison and leaves grading context. Tirmidhi2619 retains the finite leaving-prayer clause with its own anonymous report predicate, including shirk OR kufr, and does not fill the preceding route or ultimate speaker. AbuDawud2582 Arabic/English/Roman are complete technical definitions of the racing terms and remain context, completing all five source-only fields. AbuDawud2610 Arabic separates the multi-step route and explicit Malik conjecture from Ibn Umar's actual prohibition, retaining its coherent final-reporter predicate."),
    6: (41, 48, 0, "All eight exact candidate masks and attributions accepted. AbuDawud2610 English and Roman retain the finite prohibition and leave explicitly personal Malik speculation in context; the short Roman Nafi/Ibn-Umar frame remains coherent and no broken English ending is supplied. AbuDawud2617 Arabic/English/Roman are entirely the geographical Ubna/Yubna identification and its framing, completing all five source-only fields without promoting the explanatory exchange to another narration. Tirmidhi2565 Arabic/English/Roman independently supply the expressly cited finite houri-voices fragment; the unknown ultimate speaker, abbreviated scope and source defects remain qualified, while the route, verse and listening exposition are context."),
}
for batch, (start, end, count, note) in batch_notes.items():
    put(ROOT / f'candidate-inspection-notes-{batch:02d}.json', {
        'schema': 'hadith-bank-independent-candidate-inspection-v1',
        'primary_manifest_sha256': sha(manifest_bytes),
        'active_sha256': sha(active_bytes),
        'complete_candidate_fields_inspected': list(range(start, end + 1)),
        'finding_count': count,
        'conclusion': note,
    })
covered = []
for batch in range(1, 7):
    note = json.loads((ROOT / f'candidate-inspection-notes-{batch:02d}.json').read_bytes())
    covered += note['complete_candidate_fields_inspected']
assert covered == list(range(1, 49))

specs = [
    ('deenhindi-tirmidhi:2549', 'ur', 2244, 2267, '( ادنیٰ مرتبے والے کو )', 'Restore the source-rendered lower-ranking recipient identification. After the higher-ranking person approaches and meets the lower-ranking person, this supplies the referent of the ensuing garment/reaction pronouns; removing it loses a material participant relation. Keep it within the existing transmitted-account component, qualified as the source rendering, without declaring the explanatory words verbatim Prophetic speech.'),
    ('deenhindi-tirmidhi:2549', 'ur', 2468, 2476, '( جنتی )', 'Restore the source-rendered Paradise-inhabitant referent of the first-person plural in the future account. The local source distinguishes the participants returning to their homes from the current reception-dialogue speakers. Preserve this participant scope in the existing account component, without creating another occurrence or claiming verbatim wording.'),
    ('deenhindi-tirmidhi:2551', 'hi', 377, 392, '(फ़ज्र और मग़रिब)', 'Restore the own-field prayer-name parenthesis because it restricts which prayers the instruction concerns. Preserve Fajr/Maghrib and the printed after-setting timing exactly, even though the later actually recited verse says before setting. Qualify these names as source-rendered scope; do not replace Maghrib from external knowledge or claim that the parenthesis is verbatim Prophetic wording.'),
    ('deenhindi-tirmidhi:2551', 'ur', 374, 390, '( فجر اور مغرب )', 'Restore the own-field Fajr/Maghrib prayer restriction. It is material scope of the instruction, rather than a dispensable synonym. Preserve both its after-setting timing and the later verse rendering exactly, with transparent source-rendering qualification and no cross-language or canonical repair.'),
]
findings = []
for ident, language, start, end, exact, reason in specs:
    reading = readings[ident, language]
    text = reading['text']
    assert text[start:end] == exact
    field = fields[ident, language]
    assert not any(max(start, span['start']) < min(end, span['end']) for span in field['spans'])
    findings.append({
        'id': ident, 'language': language,
        'kind': 'restore_material_source_rendered_scope',
        'start': start, 'end': end, 'text': exact,
        'sha256': sha(exact.encode()), 'characters': len(exact), 'utf8_bytes': len(exact.encode()),
        'source_text_sha256': reading['sha256'], 'reason': reason,
        'initial_independent_reading_note': reading['initial_independent_reading_note'],
        'own_parent_note_history': reading['own_parent_note_history'],
    })

changed = {(finding['id'], finding['language']) for finding in findings}
expected_ranges = {
    ('deenhindi-tirmidhi:2549', 'ur'): [(0, 164), (164, 210), (210, 2757)],
    ('deenhindi-tirmidhi:2551', 'hi'): [(0, 587)],
    ('deenhindi-tirmidhi:2551', 'ur'): [(0, 570)],
}
plans = []
inspected = []
for key, reading in readings.items():
    ident, language = key
    field = fields[key]
    spans = copy.deepcopy(field['spans'])
    if key in changed:
        new_spans = []
        for start, end in expected_ranges[key]:
            candidates = [span for span in spans if max(start, span['start']) < min(end, span['end'])]
            assert candidates
            signatures = [{k: v for k, v in span.items() if k not in ['start', 'end', 'sha256']} for span in candidates]
            assert all(signature == signatures[0] for signature in signatures)
            new_spans.append(dict(signatures[0], start=start, end=end, sha256=sha(reading['text'][start:end].encode())))
        before_mask = {i for span in spans for i in range(span['start'], span['end'])}
        after_mask = {i for span in new_spans for i in range(span['start'], span['end'])}
        additions = {i for finding in findings if (finding['id'], finding['language']) == key for i in range(finding['start'], finding['end'])}
        assert after_mask - before_mask == additions and not before_mask - after_mask
        spans = new_spans
    plans.append({'id': ident, 'language': language, 'decision': records[ident]['decision'], 'source_text_sha256': reading['sha256'], 'expected_spans': spans})
    inspected.append({'id': ident, 'language': language, 'complete_source_first_reading_sha256': reading['sha256'], 'original_blind_note': reading['initial_independent_reading_note'], 'v1_field': field, 'expected_spans': spans, 'decision': 'bounded_source_scope_restoration_required' if key in changed else 'accepted_v1_exact'})
assert len(findings) == 4 and len(changed) == 3
assert sum(finding['characters'] for finding in findings) == 62
plan_sha = put(ROOT / 'accepted-reviewed-field-plan.json', {'schema': 'hadith-bank-independent-accepted-field-plan-v1', 'primary_v1_manifest_sha256': sha(manifest_bytes), 'independent_source_first_sha256': sha(own_bytes), 'reviewed_fields': plans})
finding_sha = put(ROOT / 'independent-boundary-findings-v1.json', {
    'schema': 'hadith-bank-independent-boundary-findings-v1',
    'primary_v1_manifest_sha256': sha(manifest_bytes),
    'active_v1_sha256': sha(active_bytes),
    'independent_source_first_sha256': sha(own_bytes),
    'accepted_field_plan_sha256': plan_sha,
    'all48_exact_candidate_fields_inspected_after_complete_original_readings': True,
    'findings': findings,
    'accepted_unchanged_fields': 45,
    'changed_fields': 3, 'changed_parents': 2,
    'restore_ranges': 4,
    'restore_characters': sum(finding['characters'] for finding in findings),
    'restore_utf8_bytes': sum(finding['utf8_bytes'] for finding in findings),
    'all_inspected_fields': inspected,
    'required_preservation': {
        'all45_other_read_fields_exact': True,
        'all42_unread_fields_exact': True,
        'all16_other_whole_parents_exact': True,
        'all_existing_component_identity_and_voice_metadata_exact': True,
        'all24_v1_payload_files_and_v1_manifest_archived_exact': True,
        'all_source_bytes_and_metadata_exact': True,
        'initial_notes_retained_with_transparent_final_refinement': True,
        'new_reading_credit': 0,
        'new_parent_registration_credit': 0,
        'new_canonical_occurrences': 0,
    },
})
print(json.dumps({'findings_sha256': finding_sha, 'plan_sha256': plan_sha, 'findings': len(findings), 'fields': len(changed), 'parents': len({ident for ident, language in changed}), 'characters': sum(finding['characters'] for finding in findings), 'utf8_bytes': sum(finding['utf8_bytes'] for finding in findings)}, indent=2))
