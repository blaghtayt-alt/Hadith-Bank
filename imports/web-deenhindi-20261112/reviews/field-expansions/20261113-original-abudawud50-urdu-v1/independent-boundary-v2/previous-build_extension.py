"""Serialize50 source-read Urdu additions and prove preservation of all636 parents."""
from pathlib import Path
import collections
import copy
import gzip
import hashlib
import json
import re
import sys
import tempfile

from manual_urdu_readings import READINGS

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent / 'hindi-resolve/work/scripts'
sys.path.insert(0, str(SCRIPTS))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

EXTENSION = '20261113-original-abudawud50-urdu-v1'
EVIDENCE = Path('imports/web-deenhindi-20261112/reviews/field-expansions') / EXTENSION
OUT = ROOT / 'publish-v1'
FIELDS = {'ar': 'textArabic', 'en': 'translationEnglish', 'hi': 'translationHindi',
          'ur': 'translationUrdu', 'ur-Latn': 'translationUrduRoman'}

def sha(data): return hashlib.sha256(data).hexdigest()
def gitsha(data): return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def enc(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): assert path.read_bytes() == data, ('immutable candidate collision', str(path))
    else: path.write_bytes(data)

def locate(text, literal):
    assert text.count(literal) == 1, ('nonunique explicit boundary', literal)
    at = text.index(literal)
    return at, at + len(literal)

def complement(text, spans):
    gaps, cursor = [], 0
    for span in spans:
        a, b = span['start'], span['end']
        assert cursor <= a < b <= len(text)
        if cursor < a: gaps.append((cursor, a))
        cursor = b
    if cursor < len(text): gaps.append((cursor, len(text)))
    return gaps

def normalize_receipt(version):
    value = copy.deepcopy(version)
    receipt = value['source'].get('manual_review', {})
    for key in ('sha256', 'uncompressed_sha256'):
        receipt.pop(key, None)
    return value

selection_bytes = (ROOT / 'selection.json').read_bytes()
selection = json.loads(selection_bytes)
input_bytes = (ROOT / 'full-urdu-reading-input-50.jsonl').read_bytes()
source50_bytes = (ROOT / 'source-ledger-50.jsonl').read_bytes()
reading_receipt_bytes = (ROOT / 'complete-source-first-reading-receipt.json').read_bytes()
source_proof_bytes = (ROOT / 'source-verification.json').read_bytes()
dependency_bytes = (ROOT / 'published-dependency-verification.json').read_bytes()
assert sha(selection_bytes) == 'ee2cab1cc02eb1ce242dcd8b76f5e9a72cdbe2ad21de8ead0f12827783aab552'
assert sha(input_bytes) == selection['full_urdu_reading_input_sha256'] == '4336a5dcf5dce8301b2a88bad7d1e0a473d362823e5007c605bec890778839ae'
assert sha(source50_bytes) == selection['source_ledger50_sha256'] == '72fd4ccc70a9e492e29a7445e27c1a886894d01652a46847db4562a870849912'
assert sha(reading_receipt_bytes) == '9cbae8adc2e193e7f9adc01a80b92e620efee4dbedbf8d9b13d7cf749d40813a'
assert sha(source_proof_bytes) == '97b163507d2dfa61953dcf80086a7782336373fde61c428c964254ec9d6fce35'
assert sha(dependency_bytes) == 'af9505930959e9fe3c6121db4de08e6378feaf04c03c3d32c116b6988f8b7543'
dependency = json.loads(dependency_bytes)
assert dependency['status'] == 'PASS' and dependency['commit'] == '6b20d4578c85ec2a8fb00bb7a7796f487cde755f'
reading_receipt = json.loads(reading_receipt_bytes)
assert reading_receipt['candidate_existed_when_recorded'] is False
assert reading_receipt['fully_read_fields'] == 50 and reading_receipt['characters'] == 21750 and reading_receipt['utf8_bytes'] == 38287
notes_before = {row['occurrence_id']: row for row in reading_receipt['readings']}
inputs = [json.loads(line) for line in input_bytes.splitlines()]
targets = {row['occurrence_id']: row for row in inputs}
selected = {row['occurrence_id']: row for row in selection['selected']}
source50 = {'deenhindi-' + row['collection'] + ':' + row['number']: row
            for row in map(json.loads, source50_bytes.splitlines())}
assert len(targets) == len(source50) == len(READINGS) == 50
assert set(targets) == set(source50) == set(selected) == set(notes_before)
assert {identity.split(':')[1] for identity in targets} == set(READINGS)

old_bytes = (ROOT / 'staged-inputs/previous-active636.json.gz').read_bytes()
baseline_bytes = (ROOT / 'staged-inputs/source-ledger636.jsonl.gz').read_bytes()
queue_before = (ROOT / 'staged-inputs/previous-priority-field-queue.jsonl.gz').read_bytes()
assert sha(old_bytes) == selection['prior_active_sha256'] == '6167b575a7f944a149f2db965ee937a4f9f74d856e39194b13ac7fcad6bc6abf'
assert sha(baseline_bytes) == selection['source_baseline636_sha256']
assert sha(queue_before) == selection['prior_queue_sha256'] == 'f5fa86ff645098396c7daf978f7491bddff6fd9104f5e50acc72f7d02701a660'
assert {item['sha256'] for item in dependency['files']} == {sha(old_bytes), sha(queue_before)}
old = json.loads(gzip.decompress(old_bytes))
assert sha(gzip.decompress(baseline_bytes)) == old['source_cohort_sha256']
new = copy.deepcopy(old)
old_rows = {row['id']: row for row in old['records']}
new_rows = {row['id']: row for row in new['records']}
assert len(old_rows) == len(new_rows) == 636
proofs = {row['occurrence_id']: row for row in json.loads(source_proof_bytes)['records']}
notes, cuts_report, changes, preserved_hindi, apparatus = [], [], [], [], []

for identity, item in targets.items():
    source = source50[identity]
    number = source['number']
    spec = READINGS[number]
    decision, prior = new_rows[identity], old_rows[identity]
    before_fields = {field['language']: field for field in prior['field_reviews']}
    assert 'ur' not in before_fields and decision['decision'] == prior['decision'] == 'register'
    assert decision['source_record_sha256'] == sha(importer.json_bytes(source['source_record'])) == proofs[identity]['source_record_sha256']
    assert source['snapshot'] == selected[identity]['source_snapshot']
    assert before_fields['hi'] == selected[identity]['existing_hindi_decision']
    text = source['source_record']['translationUrdu']
    assert text == item['text'] and sha(text.encode()) == item['text_sha256'] == notes_before[identity]['text_sha256']
    assert len(text) == item['characters'] == notes_before[identity]['characters_read']
    assert len(text.encode()) == item['utf8_bytes'] == notes_before[identity]['utf8_bytes_read']
    for file in proofs[identity]['files']:
        data = (ROOT / 'sources' / file['path']).read_bytes()
        assert len(data) == file['stored_bytes'] and sha(data) == file['stored_sha256'] and gitsha(data) == file['git_blob_sha1']
        plain = gzip.decompress(data)
        assert len(plain) == file['bytes'] and sha(plain) == file['sha256']
    original_note = notes_before[identity]['source_first_note']
    ranges = sorted(locate(text, literal) for literal in spec['context'])
    assert all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:]))
    for a, b in ranges:
        cuts_report.append({'occurrence_id': identity, 'language': 'ur', 'text_sha256': item['text_sha256'],
                            'start': a, 'end': b, 'text': text[a:b], 'sha256': sha(text[a:b].encode()),
                            'reason': original_note})
    components = spec['components'] or [{'start': None, 'end': None, 'report_type': spec['report_type'],
                                         'speaker': spec['speaker'], 'source_report_family_id': 'ur-source-report'}]
    spans, previous_end = [], 0
    for index, part in enumerate(components, 1):
        a = 0 if part['start'] is None else locate(text, part['start'])[0]
        b = len(text) if part['end'] is None else locate(text, part['end'])[0]
        assert previous_end <= a < b <= len(text), (identity, 'component order', index, a, b)
        previous_end = b
        pieces = [(a, b)]
        for left, right in ranges:
            changed = []
            for x, y in pieces:
                if y <= left or right <= x: changed.append((x, y))
                else:
                    if x < left: changed.append((x, left))
                    if right < y: changed.append((right, y))
            pieces = changed
        for x, y in pieces:
            assert text[x:y].strip(), (identity, 'whitespace-only selected piece', x, y)
            spans.append({'start': x, 'end': y, 'sha256': sha(text[x:y].encode()),
                          'component_id': 'ur-report-' + str(index), 'report_type': part['report_type'],
                          'speaker': part['speaker'], 'source_report_family_id': part['source_report_family_id'],
                          'reason': original_note})
    assert spans
    gaps = complement(text, spans)
    assert all(any(x <= a < b <= y for x, y in gaps) for a, b in ranges)
    action = 'whole' if len(spans) == 1 and spans[0]['start'] == 0 and spans[0]['end'] == len(text) else 'excerpts'
    field = {'language_version_id': identity + ':ur', 'language': 'ur', 'source_field': 'translationUrdu',
             'text_sha256': sha(text.encode()), 'text_chars': len(text), 'action': action,
             'reviewed': True, 'chars_reviewed': len(text), 'bytes_reviewed': len(text.encode()),
             'review_method': 'complete_own_urdu_field_manual_reading_and_exact_source_span_review',
             'review_scope': 'The complete saved Urdu field, with each actual speaker, scope qualifier, finite variant and source apparatus assessed independently; no new Hindi reading or authenticity certification.',
             'review_extension_id': EXTENSION, 'report_type': spec['report_type'], 'speaker': spec['speaker'],
             'reason': original_note, 'spans': spans, 'independent_pro_qc': 'not_performed'}
    if spec['annotations']:
        field['source_text_annotations'] = []
        for annotation in spec['annotations']:
            a, b = locate(text, annotation['literal'])
            field['source_text_annotations'].append({k: v for k, v in annotation.items() if k != 'literal'} |
                {'source_span': [a, b], 'text_sha256': sha(text[a:b].encode())})
    decision['field_reviews'].append(field)
    assert decision['field_reviews'][:-1] == prior['field_reviews']
    preserved_hindi.append({'occurrence_id': identity, 'language_version_id': before_fields['hi']['language_version_id'],
                            'before_and_after_hindi_decision_sha256': sha(enc(before_fields['hi'])),
                            'unchanged': True, 'new_hindi_reading_claimed': False})
    notes.append({'occurrence_id': identity, 'source_record_sha256': decision['source_record_sha256'],
                  'language': 'ur', 'source_field': 'translationUrdu', 'reading_order': item['reading_order'],
                  'complete_field_text': text, 'text_sha256': item['text_sha256'],
                  'characters_read': len(text), 'utf8_bytes_read': len(text.encode()),
                  'complete_own_field_read': True, 'source_first_note': original_note,
                  'decision': action, 'report_type': spec['report_type'], 'speaker': spec['speaker'],
                  'selected_spans': spans, 'report_components': len(components),
                  'source_report_families': len({part['source_report_family_id'] for part in components}),
                  'retained_context': [{'start': a, 'end': b, 'text': text[a:b], 'sha256': sha(text[a:b].encode())} for a, b in gaps]})
    changes.append({'occurrence_id': identity, 'language': 'ur', 'source_record_sha256': decision['source_record_sha256'],
                    'whole_field_sha256': field['text_sha256'], 'prior_state': 'implicit_unreviewed_sibling',
                    'prior_explicit_urdu_decision': None, 'new_field_decision_sha256': sha(enc(field)),
                    'new_action': action, 'source_parent_disposition_unchanged': True,
                    'all_existing_explicit_field_objects_unchanged': True})
    # This is an inventory of already reviewed characters, never an admission heuristic.
    selected_positions = {i for span in spans for i in range(span['start'], span['end'])}
    for match in re.finditer(r'\([^()]*\)|[۰-۹٠-٩0-9]+؎', text):
        positions = set(range(match.start(), match.end()))
        overlap = positions & selected_positions
        state = 'selected_as_source_narrative_scope_or_predicate' if overlap == positions else 'retained_as_source_context' if not overlap else 'split_by_explicit_boundary'
        assert state != 'split_by_explicit_boundary', (identity, match.group())
        apparatus.append({'occurrence_id': identity, 'language': 'ur', 'start': match.start(), 'end': match.end(),
                          'text': match.group(), 'sha256': sha(match.group().encode()), 'disposition': state,
                          'individual_own_field_reason': original_note})

notes_bytes = gzip.compress(enc({'schema': 'hadith-bank-language-extension-full-reading-notes-v1',
    'extension_id': EXTENSION, 'source_commit': selection['source_commit_to_verify'],
    'baseline_published_commit': dependency['commit'], 'reader': '/root/checkpoint_inventory',
    'independent_pro_qc': 'not_performed', 'full_reading_input_sha256': sha(input_bytes), 'fields': notes}), mtime=0)
new.setdefault('field_review_extensions', []).append({'extension_id': EXTENSION,
    'source_commit': selection['source_commit_to_verify'], 'baseline_published_commit': dependency['commit'],
    'previous_active_ledger': {'path': (EVIDENCE / 'previous-review-ledger.json.gz').as_posix(), 'sha256': sha(old_bytes)},
    'reading_notes': {'path': (EVIDENCE / 'complete-field-reading-notes.json.gz').as_posix(), 'sha256': sha(notes_bytes)},
    'original_source_baseline_path': selection['source_baseline636_path'], 'original_source_baseline_sha256': sha(baseline_bytes),
    'source_occurrences': 50, 'complete_fields_read': 50, 'newly_admitted_fields': 50,
    'complete_fields_by_language': {'ur': 50}, 'characters_read': 21750, 'utf8_bytes_read': 38287,
    'existing_hindi_decisions_preserved': 50, 'new_hindi_readings_claimed': 0,
    'all_existing_record_dispositions_and_explicit_fields_unchanged': True, 'independent_pro_qc': 'not_performed'})
assert {k: v for k, v in old.items() if k not in ('records', 'field_review_extensions')} == {
    k: v for k, v in new.items() if k not in ('records', 'field_review_extensions')}
assert new['field_review_extensions'][:-1] == old.get('field_review_extensions', [])
new_bytes = gzip.compress(enc(new), mtime=0)

sources636 = [json.loads(line) for line in gzip.decompress(baseline_bytes).splitlines()]
assert len(sources636) == 636
counts = collections.Counter()
before_coverage, after_coverage = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
derived = []
with tempfile.TemporaryDirectory(prefix='native-validation-', dir=ROOT) as temp:
    validation = Path(temp)
    write(validation / 'before' / selection['prior_active_path'], old_bytes)
    write(validation / 'after' / selection['prior_active_path'], new_bytes)
    before_reviews, after_reviews = SourceReviews(validation / 'before', 'deenhindi'), SourceReviews(validation / 'after', 'deenhindi')
    for saved in sources636:
        identity = f"deenhindi-{saved['collection']}:{saved['number']}"
        baseline = importer.canonical_record(saved)
        untouched = copy.deepcopy(baseline)
        before_result, before_action = before_reviews.apply(baseline, saved=saved)
        after_result, after_action = after_reviews.apply(baseline, saved=saved)
        assert baseline == untouched and before_action == after_action == old_rows[identity]['decision'] == new_rows[identity]['decision']
        counts['parents_native_applied'] += 1
        counts['unchanged_parent_dispositions'] += 1
        counts['parent_' + after_action] += 1
        prior, revised = old_rows[identity], new_rows[identity]
        assert {k: v for k, v in prior.items() if k != 'field_reviews'} == {k: v for k, v in revised.items() if k != 'field_reviews'}
        if identity not in targets:
            assert prior == revised
            counts['untouched_complete_parent_decisions'] += 1
        else:
            assert revised['field_reviews'][:-1] == prior['field_reviews']
            assert saved == source50[identity]
        counts['existing_explicit_field_decisions_preserved'] += len(prior['field_reviews'])
        for key, value in baseline.items():
            if key not in ('text', 'language_versions', 'review', 'extraction', 'content_kind'):
                assert after_result[key] == before_result[key] == value, (identity, 'parent metadata', key)
                counts['parent_metadata_equalities'] += 1
        assert after_result['review']['independent_pro_qc'] == 'not_performed'
        assert after_result['review']['certified_release_eligible'] is False
        assert after_result['number']['canonical'] is None
        old_fields = {f['language_version_id']: f for f in prior['field_reviews']}
        new_fields = {f['language_version_id']: f for f in revised['field_reviews']}
        assert len(baseline['language_versions']) == len(after_result['language_versions']) == len(before_result['language_versions'])
        for original, before_version, after_version in zip(baseline['language_versions'], before_result['language_versions'], after_result['language_versions']):
            version_id, language = original['id'], original['language']
            old_field, new_field = old_fields.get(version_id), new_fields.get(version_id)
            changed = identity in targets and language == 'ur'
            if changed:
                assert old_field is None and new_field is not None and new_field['reviewed'] is True
                assert before_version['text'] is None and after_version['text']
                counts['newly_reviewed_and_admitted_urdu_fields'] += 1
            else:
                assert old_field == new_field
                assert normalize_receipt(before_version) == normalize_receipt(after_version), (identity, language, 'prior derived version changed beyond active-ledger receipt')
                counts['unchanged_explicit_or_implicit_field_slots'] += 1
            for key in ('id', 'language', 'references', 'translation_provenance'):
                assert after_version[key] == original[key]
                counts['language_metadata_equalities'] += 1
            expected_script = new_field.get('observed_script', original['script']) if new_field else original['script']
            assert after_version['script'] == expected_script
            counts['language_metadata_equalities'] += 1
            for key, value in original['source'].items():
                assert after_version['source'][key] == value, (identity, language, key)
                counts['language_source_metadata_equalities'] += 1
            text = original['text']
            assert text == saved['source_record'][FIELDS[language]]
            spans = new_field.get('spans', []) if new_field else []
            if spans: assert after_version['text'] == ''.join(text[s['start']:s['end']] for s in spans)
            else: assert after_version['text'] is None
            pieces = []
            for span in spans:
                a, b = span['start'], span['end']
                assert sha(text[a:b].encode()) == span['sha256']
                pieces.append((a, b, text[a:b]))
            for comment in after_version.get('comments', []):
                if 'source_span' in comment:
                    a, b = comment['source_span']
                    assert comment['scope'] == 'source_context_not_narration'
                    assert comment['text'] == text[a:b] and comment['source_text_sha256'] == sha(text[a:b].encode())
                    pieces.append((a, b, comment['text']))
            cursor = 0
            for a, b, part in sorted(pieces):
                assert a == cursor and a < b and part == text[a:b], (identity, language, 'lossless partition', a, b, cursor)
                cursor = b
            assert cursor == len(text) and ''.join(part for a, b, part in sorted(pieces)) == text
            counts['lossless_nonempty_source_field_partitions'] += 1
            for counter, field in [(before_coverage, old_field), (after_coverage, new_field)]:
                counter[language]['nonempty_fields'] += 1
                reviewed = bool(field and field.get('reviewed', field.get('chars_reviewed') == len(text)))
                counter[language]['reviewed_fields'] += reviewed
                counter[language]['admitted_fields'] += bool(field and field.get('spans'))
                counter[language]['unread_context_fields'] += not reviewed
        derived.append(after_result)
    before_reviews.finish()
    after_reviews.finish()
    engine_sha = after_reviews.engine_sha256
assert counts['parents_native_applied'] == counts['unchanged_parent_dispositions'] == 636
assert counts['parent_register'] == 612 and counts['parent_exclude'] == 24
assert counts['untouched_complete_parent_decisions'] == 586
assert counts['existing_explicit_field_decisions_preserved'] == 819
assert counts['newly_reviewed_and_admitted_urdu_fields'] == 50
assert counts['unchanged_explicit_or_implicit_field_slots'] == 3068
assert counts['lossless_nonempty_source_field_partitions'] == 3118
assert after_coverage['ur']['reviewed_fields'] - before_coverage['ur']['reviewed_fields'] == 50
assert after_coverage['ur']['admitted_fields'] - before_coverage['ur']['admitted_fields'] == 50
for language in ('hi', 'ar', 'en', 'ur-Latn'):
    assert before_coverage[language] == after_coverage[language]

queue_lines = gzip.decompress(queue_before).splitlines(keepends=True)
remaining_lines, removed = [], []
for line in queue_lines:
    row = json.loads(line)
    if row['id'] in targets:
        assert row == selected[row['id']]['frozen_queue_record']
        assert len(row['fields']) == 1 and row['fields'][0]['language'] == 'ur'
        assert row['fields'][0]['text_sha256'] == targets[row['id']]['text_sha256']
        assert row['active_review_path'] == selection['prior_active_path']
        removed.append({'id': row['id'], 'field': row['fields'][0], 'source_record_sha256': row['source_record_sha256'],
                        'before_queue_record_sha256': sha(enc(row)), 'original_json_line_sha256': sha(line)})
    else:
        remaining_lines.append(line)
assert len(removed) == 50 and {r['id'] for r in removed} == set(targets)
remaining = [json.loads(line) for line in remaining_lines]
remaining_by_language = collections.Counter(f['language'] for row in remaining for f in row['fields'])
assert len(remaining) == 3434 and remaining_by_language == {'hi': 3320, 'ur': 3131}
assert sum(remaining_by_language.values()) == 6451
queue_after = gzip.compress(b''.join(remaining_lines), mtime=0)
queue_delta = {'schema': 'hadith-bank-exact-field-queue-delta-v1', 'status': 'PASS',
    'extension_id': EXTENSION, 'before_sha256': sha(queue_before), 'after_sha256': sha(queue_after),
    'before_occurrences': 3484, 'before_fields': 6501, 'removed_fields': 50, 'removed_occurrences': 50,
    'remaining_occurrences': 3434, 'remaining_fields': 6451, 'remaining_by_language': dict(remaining_by_language),
    'removed': removed, 'all_other_json_line_bytes_values_and_order_unchanged': True,
    'source_occurrence_count_delta': 0, 'registration_delta': 0}
report = {'schema': 'hadith-bank-language-field-extension-validation-v1', 'status': 'PASS',
    'extension_id': EXTENSION, 'selection_scope': selection['selection_rule'],
    'source_commit': selection['source_commit_to_verify'], 'baseline_published_commit': dependency['commit'],
    'initially_staged_selection_retained_and_later_publication_independently_bound': True,
    'newly_fully_read_fields': 50, 'newly_admitted_fields': 50, 'newly_read_context_only_fields': 0,
    'newly_read_occurrences': 50, 'characters_read': 21750, 'utf8_bytes_read': 38287,
    'new_readings_by_language': {'ur': 50}, 'new_hindi_readings_claimed': 0,
    'preserved_existing_selected_hindi_fields': 50,
    'new_selected_spans': sum(len(n['selected_spans']) for n in notes),
    'new_selected_characters': sum(s['end']-s['start'] for n in notes for s in n['selected_spans']),
    'new_selected_utf8_bytes': sum(len(n['complete_field_text'][s['start']:s['end']].encode()) for n in notes for s in n['selected_spans']),
    'new_explicit_report_components': sum(n['report_components'] for n in notes),
    'new_source_report_families_within_these_fields': sum(n['source_report_families'] for n in notes),
    'new_retained_context_gaps': sum(len(n['retained_context']) for n in notes),
    'enumerated_literal_apparatus_cuts': len(cuts_report),
    'counts': dict(counts), 'coverage_before': {k: dict(v) for k,v in before_coverage.items()},
    'coverage_after': {k: dict(v) for k,v in after_coverage.items()},
    'prior_active_ledger_sha256': sha(old_bytes), 'active_ledger_sha256': sha(new_bytes),
    'prior_queue_sha256': sha(queue_before), 'queue_after_sha256': sha(queue_after),
    'source_baseline636_sha256': sha(baseline_bytes), 'source50_baseline_sha256': sha(source50_bytes),
    'source_first_reading_receipt_sha256': sha(reading_receipt_bytes),
    'source_verification_sha256': sha(source_proof_bytes), 'published_dependency_receipt_sha256': sha(dependency_bytes),
    'source_review_engine_sha256': engine_sha,
    'native_source_reviews_before_and_after_apply_finish': 'PASS for all636 parents in each replay',
    'raw_parsed_files_reopened_and_hash_verified': 100, 'complete_raw_reparses': 50,
    'all_original_record_dispositions_and_explicit_field_objects_preserved': True,
    'all_other_derived_language_versions_preserved_except_updated_active_ledger_receipt_hash': True,
    'registration_delta': 0, 'source_occurrence_delta': 0,
    'remaining_original3942_priority_fields': 6451, 'remaining_original3942_priority_occurrences': 3434,
    'remaining_priority_by_language': dict(remaining_by_language),
    'source_http_requests': 0, 'github_writes': 0, 'independent_pro_qc': 'not_performed',
    'independent_exact_candidate_audit': 'pending separate final-hash-bound handoff'}

write(OUT / selection['prior_active_path'], new_bytes)
write(OUT / selection['prior_queue_path'], queue_after)
payload = {
    'previous-review-ledger.json.gz': old_bytes, 'previous-priority-field-queue.jsonl.gz': queue_before,
    'source-ledger-50.jsonl.gz': gzip.compress(source50_bytes, mtime=0),
    'selection-at-preparation.json.gz': gzip.compress(selection_bytes, mtime=0),
    'full-urdu-reading-input-50.jsonl.gz': gzip.compress(input_bytes, mtime=0),
    'source-verification.json.gz': gzip.compress(source_proof_bytes, mtime=0),
    'complete-source-first-reading-receipt.json.gz': gzip.compress(reading_receipt_bytes, mtime=0),
    'complete-field-reading-notes.json.gz': notes_bytes,
    'published-dependency-verification.json': dependency_bytes,
    'manual_urdu_readings.py': (ROOT / 'manual_urdu_readings.py').read_bytes(),
    'build_extension.py': Path(__file__).read_bytes(),
    'preserved-existing-hindi50.json': enc({'previous_active_ledger_sha256': sha(old_bytes), 'records': preserved_hindi}),
    'exact-field-decision-delta.json': enc({'before_active_sha256': sha(old_bytes), 'after_active_sha256': sha(new_bytes), 'fields': changes}),
    'explicit-apparatus-cuts.json': enc({'scope': 'Only these50 completely read Urdu fields; all other context gaps are itemized in the full notes.', 'blanket_parenthesis_rule': False, 'cuts': cuts_report}),
    'selected-apparatus-inventory.json': enc({'scope': 'Inventory after individual complete-field reading and explicit boundary decisions; never used to decide admission.', 'items': apparatus}),
    'priority-field-queue-delta.json': enc(queue_delta), 'validation.json': enc(report),
}
for name, data in payload.items(): write(OUT / EVIDENCE / name, data)
write(ROOT / 'validation-v1.json', enc(report))
write(ROOT / 'derived-preview-v1.jsonl.gz', gzip.compress(importer.rows_bytes(derived), mtime=0))
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'local_path': str(path),
                      'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': gitsha(data)})
portable = {'schema': 'hadith-bank-language-extension-portable-manifest-v1', 'extension_id': EXTENSION,
    'source_commit': selection['source_commit_to_verify'], 'baseline_published_commit': dependency['commit'],
    'active_ledger_path': selection['prior_active_path'], 'active_ledger_sha256': sha(new_bytes),
    'files': [{k:v for k,v in row.items() if k != 'local_path'} for row in files]}
portable_bytes = enc(portable)
write(OUT / EVIDENCE / 'portable-manifest.json', portable_bytes)
files.append({'path': (EVIDENCE / 'portable-manifest.json').as_posix(), 'local_path': str(OUT / EVIDENCE / 'portable-manifest.json'),
              'bytes': len(portable_bytes), 'sha256': sha(portable_bytes), 'git_blob_sha1': gitsha(portable_bytes)})
manifest = {'schema': 'hadith-bank-language-extension-delivery-v1', 'extension_id': EXTENSION,
    'active_ledger_path': selection['prior_active_path'], 'active_ledger_sha256': sha(new_bytes),
    'queue_path': selection['prior_queue_path'], 'queue_sha256': sha(queue_after),
    'files': files, 'total_files': len(files), 'total_bytes': sum(row['bytes'] for row in files), 'validation': report}
manifest_bytes = enc(manifest)
write(ROOT / 'delivery-manifest-v1.json', manifest_bytes)
print(json.dumps({'status': 'PASS', 'manifest_sha256': sha(manifest_bytes), 'active_sha256': sha(new_bytes),
                  'queue_sha256': sha(queue_after), 'files': len(files), 'bytes': manifest['total_bytes'],
                  'counts': dict(counts), 'selected_spans': report['new_selected_spans'],
                  'selected_characters': report['new_selected_characters'], 'selected_bytes': report['new_selected_utf8_bytes'],
                  'remaining_priority_fields': 6451, 'remaining_priority_occurrences': 3434}, indent=2))
