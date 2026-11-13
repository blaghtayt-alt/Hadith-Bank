"""Serialize individually read Urdu decisions; preserve the published477 baseline."""
from pathlib import Path
import collections
import copy
import gzip
import hashlib
import json
import shutil
import sys
from manual_urdu_readings_v2 import READINGS

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

EXTENSION = '20261113-ibnmajah114-remaining-urdu-v1'
EVIDENCE = Path('imports/web-deenhindi-20261112/reviews/field-expansions') / EXTENSION
OUT = ROOT / 'publish-v2'
VALIDATION = ROOT / 'validation-repo-v2'
SOURCE_COMMIT = 'cdb66dbcf9ee781fe232219724d05033a0fcab13'
BASELINE_PUBLICATION = '5749ec389f1925f4d5e05a34d64c39acbc1f90f4'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def gitsha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, ('immutable candidate collision', str(path))
    else:
        path.write_bytes(data)

def locate(text, literal):
    assert isinstance(literal, str) and text.count(literal) == 1, ('explicit boundary is not unique', literal)
    start = text.index(literal)
    return start, start + len(literal)

def complement(text, spans):
    cursor = 0
    result = []
    for span in spans:
        start, end = span['start'], span['end']
        assert 0 <= cursor <= start < end <= len(text)
        if cursor < start:
            result.append((cursor, start))
        cursor = end
    if cursor < len(text):
        result.append((cursor, len(text)))
    return result

selection_bytes = (ROOT / 'selection.json').read_bytes()
selection = json.loads(selection_bytes)
input_bytes = (ROOT / 'full-urdu-reading-input-114.jsonl').read_bytes()
assert sha(input_bytes) == 'c0d0e1e0ac94a06ae6462a7d6e1d206203b6bd74b6933882682930eeefa22010'
inputs = [json.loads(line) for line in input_bytes.splitlines()]
targets = {row['occurrence_id']: row for row in inputs}
assert len(inputs) == len(targets) == len(READINGS) == 114 and set(targets) == set(READINGS)
assert all(row['language'] == 'ur' for row in inputs)
assert selection['source_commit'] == SOURCE_COMMIT
assert selection['selected_occurrences'] == selection['selected_fields'] == 114
selected = {row['occurrence_id']: row for row in selection['selected']}
assert set(selected) == set(targets)

old_bytes = (ROOT / 'staged-inputs/previous-active477.json.gz').read_bytes()
queue_before = (ROOT / 'staged-inputs/previous-priority-field-queue.jsonl.gz').read_bytes()
baseline_bytes = (ROOT / 'staged-inputs/source-ledger477.jsonl.gz').read_bytes()
assert sha(old_bytes) == selection['prior_active_sha256'] == '8677e17f00443d1c8f298b803209339cdc67fa924c5065163d602841128fd812'
assert sha(queue_before) == selection['prior_queue_sha256'] == '750281919cb4ba531347c355af1a7cc8710c1ae24047c039af62cd3b854a07c0'
old = json.loads(gzip.decompress(old_bytes))
new = copy.deepcopy(old)
assert sha(baseline_bytes) == old['source_ledger_sha256']
assert sha(gzip.decompress(baseline_bytes)) == old['source_ledger_uncompressed_sha256']
old_rows = {row['occurrence_id']: row for row in old['records']}
new_rows = {row['occurrence_id']: row for row in new['records']}
assert len(old_rows) == len(new_rows) == 477

source114_bytes = (ROOT / 'source-ledger-114.jsonl').read_bytes()
assert sha(source114_bytes) == selection['source_ledger114_sha256'] == 'e44627c85a214b008566a6297b26d44556702bcb7756acbcfacc87f64836789b'
sources = {'deenhindi-' + row['collection'] + ':' + row['number']: row
           for row in map(json.loads, source114_bytes.splitlines())}
assert set(sources) == set(targets)
source_proof_bytes = (ROOT / 'source-verification.json').read_bytes()
assert sha(source_proof_bytes) == 'ce83d0f7fa4cc0c7039a77452b4b3aeaa1a27d12c154a02972a4cc936882cfa3'
source_proof = json.loads(source_proof_bytes)
assert source_proof['status'] == 'PASS' and source_proof['source_commit'] == SOURCE_COMMIT
assert source_proof['raw_parsed_pairs_reopened_and_reparsed'] == source_proof['source_objects_verified'] == 114
assert source_proof['source_files_fetched_from_pinned_GitHub_blobs'] == 228
source_checks = {row['occurrence_id']: row for row in source_proof['records']}
assert set(source_checks) == set(targets)
dependency_bytes = (ROOT / 'published-dependency-verification.json').read_bytes()
dependency = json.loads(dependency_bytes)
assert dependency['status'] == 'PASS' and dependency['commit'] == BASELINE_PUBLICATION
assert {row['sha256'] for row in dependency['files']} == {sha(old_bytes), sha(queue_before)}

notes = []
explicit_cuts = []
field_changes = []
preserved_hindi = []
for identity, item in targets.items():
    saved = sources[identity]
    decision = new_rows[identity]
    prior = old_rows[identity]
    spec = READINGS[identity]
    assert decision['decision'] == 'register'
    assert decision['source_record_sha256'] == sha(importer.json_bytes(saved['source_record'])) == source_checks[identity]['source_record_sha256']
    assert saved['snapshot'] == decision['source_snapshot']
    assert saved['source_reference_verbatim'] == decision['source_reference_verbatim'] == source_checks[identity]['source_reference_verbatim']
    assert saved['parsed_path'] == source_checks[identity]['source_parsed_descriptor']['path']
    for descriptor in source_checks[identity]['files']:
        data = (ROOT / 'sources' / descriptor['path']).read_bytes()
        assert sha(data) == descriptor['stored_sha256'] and gitsha(data) == descriptor['git_blob_sha1']
        assert len(data) == descriptor['stored_bytes']
        plain = gzip.decompress(data)
        assert sha(plain) == descriptor['sha256'] and len(plain) == descriptor['bytes']
    field = next(field for field in decision['fields'] if field['language'] == 'ur')
    before_field = copy.deepcopy(field)
    assert before_field == selected[identity]['old_urdu_decision']
    assert field['reviewed'] is False and not field['selected_spans'] and field['decision'] == 'unreviewed'
    assert item['source_field'] == field['source_field'] == 'translationUrdu'
    text = saved['source_record'][field['source_field']]
    assert text == item['text'] and sha(text.encode()) == item['text_sha256'] == field['text_sha256']
    assert len(text) == item['characters'] == field['text_chars']
    assert len(text.encode()) == item['utf8_bytes']
    hindi = next(field for field in decision['fields'] if field['language'] == 'hi')
    assert hindi['reviewed'] is True and hindi == selected[identity]['existing_hindi_decision']
    preserved_hindi.append({'occurrence_id': identity, 'version_id': hindi['version_id'],
                            'text_sha256': hindi['text_sha256'],
                            'before_and_after_field_decision_sha256': sha(encoded(hindi)),
                            'unchanged': True, 'new_hindi_reading_claimed': False})

    cuts = []
    for literal in spec.get('context', []):
        start, end = locate(text, literal)
        cuts.append((start, end))
        explicit_cuts.append({'occurrence_id': identity, 'language': 'ur',
                              'whole_field_sha256': sha(text.encode()), 'start': start, 'end': end,
                              'text': text[start:end], 'sha256': sha(text[start:end].encode()),
                              'decision': 'retained_source_context', 'reason': spec['note']})
    cuts.sort()
    assert all(a[1] <= b[0] for a, b in zip(cuts, cuts[1:]))
    spans = []
    last = 0
    for index, part in enumerate(spec.get('segments', [{'start': None, 'end': None}]), 1):
        start = 0 if part['start'] is None else locate(text, part['start'])[0]
        end = len(text) if part['end'] is None else locate(text, part['end'])[0]
        assert 0 <= last <= start < end <= len(text), (identity, index, start, end)
        last = end
        retained = [(start, end)]
        for left, right in cuts:
            next_retained = []
            for a, b in retained:
                if b <= left or right <= a:
                    next_retained.append((a, b))
                else:
                    if a < left:
                        next_retained.append((a, left))
                    if right < b:
                        next_retained.append((right, b))
            retained = next_retained
        for a, b in retained:
            assert text[a:b].strip(), (identity, 'whitespace-only selected fragment', a, b)
            spans.append({'start': a, 'end': b, 'sha256': sha(text[a:b].encode()),
                          'component_id': 'ur-report-' + str(index),
                          'report_type': part.get('type', spec['type']),
                          'speaker': part.get('speaker', spec['speaker']), 'reason': spec['note'],
                          **({'source_report_family_id': part['source_report_family_id']} if 'source_report_family_id' in part else {})})
    assert spans, ('this individually read field must supply its selected body', identity)
    context = complement(text, spans)
    assert all(any(a <= x < y <= b for a, b in context) for x, y in cuts)
    action = 'whole' if len(spans) == 1 and spans[0]['start'] == 0 and spans[0]['end'] == len(text) else 'excerpts'
    field.update(decision=action, reviewed=True, chars_reviewed=len(text), bytes_reviewed=len(text.encode()),
                 review_scope='complete_current_language_field', review_extension_id=EXTENSION,
                 review_method='complete_own_field_manual_reading_and_exact_span_decisions',
                 reason=spec['note'], selected_spans=spans, report_type=spec['type'],
                 speaker=spec['speaker'], independent_pro_qc='not_performed')
    notes.append({'occurrence_id': identity, 'source_record_sha256': decision['source_record_sha256'],
                  'language': 'ur', 'source_field': field['source_field'], 'version_id': field['version_id'],
                  'reading_order': item['reading_order'], 'complete_field_text': text,
                  'full_field_sha256': sha(text.encode()), 'chars_read': len(text), 'utf8_bytes_read': len(text.encode()),
                  'complete_own_field_read': True, 'decision': action, 'semantic_reading': spec['note'],
                  'selected_spans': spans, 'retained_context': [
                      {'start': a, 'end': b, 'text': text[a:b], 'sha256': sha(text[a:b].encode())} for a, b in context]})
    field_changes.append({'occurrence_id': identity, 'language': 'ur', 'version_id': field['version_id'],
                          'source_text_sha256': field['text_sha256'],
                          'before_field_decision_sha256': sha(encoded(before_field)),
                          'after_field_decision_sha256': sha(encoded(field)),
                          'before_decision': before_field['decision'], 'after_decision': action,
                          'parent_disposition_unchanged': True})

assert sum(row['chars_read'] for row in notes) == 29305
assert sum(row['utf8_bytes_read'] for row in notes) == 51820
notes_bytes = gzip.compress(encoded({'schema': 'hadith-bank-field-reading-extension-v1',
    'extension_id': EXTENSION, 'source_commit': SOURCE_COMMIT, 'baseline_published_commit': BASELINE_PUBLICATION,
    'reader': '/root/queue_audit', 'independent_pro_qc': 'not_performed',
    'frozen_reading_input_sha256': sha(input_bytes), 'fields': notes}), mtime=0)
new['field_review_extensions'].append({'extension_id': EXTENSION, 'source_commit': SOURCE_COMMIT,
    'baseline_published_commit': BASELINE_PUBLICATION,
    'previous_active_ledger': {'path': (EVIDENCE / 'previous-review-ledger.json.gz').as_posix(), 'sha256': sha(old_bytes)},
    'reading_notes': {'path': (EVIDENCE / 'complete-field-reading-notes.json.gz').as_posix(), 'sha256': sha(notes_bytes)},
    'occurrences': 114, 'complete_fields_read': 114, 'complete_fields_by_language': {'ur': 114},
    'languages': ['ur'], 'already_reviewed_hindi_fields_preserved': 114,
    'existing_record_dispositions_unchanged': True, 'previous_other_language_decisions_unchanged': True,
    'independent_pro_qc': 'not_performed'})
assert {k: v for k, v in old.items() if k not in ('records', 'field_review_extensions')} == {
    k: v for k, v in new.items() if k not in ('records', 'field_review_extensions')}
assert new['field_review_extensions'][:-1] == old['field_review_extensions']
v1_manifest_bytes = (ROOT / 'delivery-manifest-v1.json').read_bytes()
assert sha(v1_manifest_bytes) == '0d4b693122fb5fee5728b8c7e6b9939febb3342a1621f31f3d0c855d8cecaad1'
v1_active = (ROOT / 'publish-v1' / selection['prior_active_path']).read_bytes()
assert sha(v1_active) == '1d8452cad2cc644aa33f019df1bfbba9034975adb4f8a60146940e2b297cf21e'
v1 = json.loads(gzip.decompress(v1_active))
changed_from_v1 = []
unchanged_from_v1 = 0
for earlier, revised in zip(v1['records'], new['records']):
    assert {k:v for k,v in earlier.items() if k != 'fields'} == {k:v for k,v in revised.items() if k != 'fields'}
    for before_field, after_field in zip(earlier['fields'], revised['fields']):
        if before_field != after_field:
            key = (revised['occurrence_id'], after_field['language'])
            assert key in [('deenhindi-ibnmajah:835','ur'),('deenhindi-ibnmajah:1250','ur')]
            before_mask = [i for span in before_field['selected_spans'] for i in range(span['start'], span['end'])]
            after_mask = [i for span in after_field['selected_spans'] for i in range(span['start'], span['end'])]
            assert before_mask == after_mask
            changed_from_v1.append({'occurrence_id':key[0],'language':key[1],
                'source_text_sha256':after_field['text_sha256'],
                'before_field_sha256':sha(encoded(before_field)),'after_field_sha256':sha(encoded(after_field)),
                'selected_codepoints_unchanged':True,
                'change':'Honorific-pronoun attribution qualification only.' if key[0].endswith(':835') else 'Two adjacent testimonial/Prophetic attribution components at137 within one source report family; all293 codepoints selected.'})
        else:
            unchanged_from_v1 += 1
assert len(changed_from_v1) == 2 and unchanged_from_v1 == 2383
AMENDMENT = EVIDENCE / 'independent-attribution-v2'
new['field_review_extensions'][-1]['independent_attribution_amendment'] = {
    'previous_candidate_ledger':{'path':(AMENDMENT/'previous-active-ledger.json.gz').as_posix(),'sha256':sha(v1_active)},
    'previous_candidate_manifest_sha256':sha(v1_manifest_bytes),
    'changed_fields':2,'other_field_decisions_unchanged':2383,'all_selected_source_codepoints_unchanged':True,
    'reason':'Independently requested835 honorific-pronoun qualification and1250 witness/appraisal separation within one report family.'}
new_bytes = gzip.compress(encoded(new), mtime=0)
write(OUT / selection['prior_active_path'], new_bytes)
write(OUT / EVIDENCE / 'previous-review-ledger.json.gz', old_bytes)
write(OUT / EVIDENCE / 'previous-priority-field-queue.jsonl.gz', queue_before)
write(OUT / EVIDENCE / 'complete-field-reading-notes.json.gz', notes_bytes)
write(OUT / EVIDENCE / 'full-urdu-reading-input-114.jsonl.gz', gzip.compress(input_bytes, mtime=0))
write(OUT / EVIDENCE / 'source-ledger-114.jsonl.gz', gzip.compress(source114_bytes, mtime=0))
write(OUT / EVIDENCE / 'source-verification.json.gz', gzip.compress(source_proof_bytes, mtime=0))
write(OUT / EVIDENCE / 'selection-at-preparation.json.gz', gzip.compress(selection_bytes, mtime=0))
write(OUT / EVIDENCE / 'published-dependency-verification.json', dependency_bytes)
write(OUT / EVIDENCE / 'manual_urdu_readings_v2.py', (ROOT / 'manual_urdu_readings_v2.py').read_bytes())
write(OUT / EVIDENCE / 'build_extension_v2.py', Path(__file__).read_bytes())
write(OUT / EVIDENCE / 'preserved-existing-hindi114.json', encoded({'schema': 'preserved-existing-language-fields-v1',
    'previous_active_ledger_sha256': sha(old_bytes), 'records': preserved_hindi}))
write(OUT / EVIDENCE / 'exact-field-decision-delta.json', encoded({'schema': 'source-bound-field-extension-delta-v1',
    'before_active_sha256': sha(old_bytes), 'after_active_sha256': sha(new_bytes), 'fields': field_changes}))
write(OUT / EVIDENCE / 'explicit-apparatus-decisions.json', encoded({'schema': 'source-hash-bound-apparatus-decisions-v1',
    'scope': 'Only these114 individually read Urdu fields. Complementary report-boundary contexts are fully itemized in the reading notes.',
    'decisions': explicit_cuts, 'blanket_parenthesis_rule': False}))

write(OUT / AMENDMENT / 'previous-active-ledger.json.gz', v1_active)
write(OUT / AMENDMENT / 'previous-delivery-manifest.json', v1_manifest_bytes)
write(OUT / AMENDMENT / 'previous-manual_urdu_readings.py', (ROOT/'manual_urdu_readings.py').read_bytes())
write(OUT / AMENDMENT / 'previous-complete-field-reading-notes.json.gz', (ROOT/'publish-v1'/EVIDENCE/'complete-field-reading-notes.json.gz').read_bytes())
write(OUT / AMENDMENT / 'exact-attribution-amendment.json', encoded({
    'schema':'hadith-bank-exact-attribution-amendment-v1','status':'PASS',
    'previous_candidate_sha256':sha(v1_active),'revised_candidate_sha256':sha(new_bytes),
    'fields':changed_from_v1,'unchanged_field_decisions':unchanged_from_v1,
    'parent_dispositions_unchanged':477,'selection_context_codepoint_union_unchanged':True,
    'reading_scope_unchanged':{'ur':114,'characters':29305,'utf8_bytes':51820}}))
# Replay the full477 ledger and prove only the114 own Urdu fields changed.
if VALIDATION.exists():
    shutil.rmtree(VALIDATION)
shutil.copytree(OUT, VALIDATION)
write(VALIDATION / old['source_ledger_path'], baseline_bytes)
original_sources = [json.loads(line) for line in gzip.decompress(baseline_bytes).splitlines()]
assert len(original_sources) == 477
reviews = SourceReviews(VALIDATION, 'deenhindi')
counts = collections.Counter()
before_coverage = collections.defaultdict(collections.Counter)
after_coverage = collections.defaultdict(collections.Counter)
derived = []
for saved in original_sources:
    identity = 'deenhindi-' + saved['collection'] + ':' + saved['number']
    before = importer.canonical_record(saved)
    untouched_input = copy.deepcopy(before)
    result, action = reviews.apply(before, saved=saved)
    assert before == untouched_input and action == 'register'
    prior = old_rows[identity]
    decision = new_rows[identity]
    assert {k: v for k, v in prior.items() if k != 'fields'} == {k: v for k, v in decision.items() if k != 'fields'}
    counts['unchanged_parent_dispositions'] += 1
    if identity not in targets:
        assert decision == prior
        counts['untouched_rows'] += 1
    else:
        assert saved['source_record'] == sources[identity]['source_record']
        assert saved['snapshot'] == sources[identity]['snapshot'] and saved['parsed_path'] == sources[identity]['parsed_path']
    for key, value in before.items():
        if key not in ('text', 'language_versions', 'review', 'extraction', 'content_kind'):
            assert result.get(key) == value, (identity, 'parent metadata', key)
            counts['parent_metadata_invariants'] += 1
    assert result['number']['canonical'] is None and result['review']['independent_pro_qc'] == 'not_performed'
    assert result['review']['certified_release_eligible'] is False
    assert len(prior['fields']) == len(decision['fields']) == len(before['language_versions']) == len(result['language_versions']) == 5
    for old_field, field, original, version in zip(prior['fields'], decision['fields'], before['language_versions'], result['language_versions']):
        language = field['language']
        changed = identity in targets and language == 'ur'
        if changed:
            assert old_field != field and field['reviewed'] is True and old_field['reviewed'] is False
            counts['newly_reviewed_urdu_fields'] += 1
        else:
            assert old_field == field, (identity, language, 'unchanged field decision')
            counts['unchanged_field_decisions'] += 1
            if old_field.get('review_extension_id') == '20261113-ibnmajah50-83-hindi-urdu-v2':
                counts['phase9_83_fields_preserved'] += 1
        if 'observed_script' in old_field:
            assert old_field['observed_script'] == field['observed_script'] == version['script']
            assert old_field['source_script_note'] == field['source_script_note']
            counts['existing_script_corrections_preserved'] += 1
        else:
            assert version['script'] == original['script']
        for key in ('id', 'language', 'references', 'translation_provenance'):
            assert version[key] == original[key], (identity, language, key)
            counts['language_metadata_invariants'] += 1
        for key, value in original['source'].items():
            assert version['source'][key] == value, (identity, language, 'source', key)
            counts['language_source_metadata_invariants'] += 1
        text = original['text']
        assert text == saved['source_record'][field['source_field']]
        assert field['text_sha256'] == sha(text.encode()) and field['text_chars'] == len(text)
        spans = field['selected_spans']
        if spans:
            assert version['text'] == ''.join(text[span['start']:span['end']] for span in spans)
        else:
            assert version['text'] is None
        pieces = []
        for span in spans:
            a, b = span['start'], span['end']
            assert sha(text[a:b].encode()) == span['sha256']
            pieces.append((a, b, text[a:b]))
        for comment in version.get('comments', []):
            if 'source_span' in comment:
                a, b = comment['source_span']
                assert comment['scope'] == 'source_context_not_narration'
                assert comment['text'] == text[a:b] and comment['source_text_sha256'] == sha(text[a:b].encode())
                pieces.append((a, b, comment['text']))
        cursor = 0
        for a, b, part in sorted(pieces):
            assert a == cursor and a < b and part == text[a:b]
            cursor = b
        assert cursor == len(text) and ''.join(part for a, b, part in sorted(pieces)) == text
        counts['lossless_field_partitions'] += 1
        for coverage, candidate in ((before_coverage, old_field), (after_coverage, field)):
            coverage[language]['nonempty_fields'] += 1
            coverage[language]['reviewed_fields'] += int(candidate['reviewed'])
            coverage[language]['admitted_fields'] += int(bool(candidate['selected_spans']))
            coverage[language]['unread_context_fields'] += int(not candidate['reviewed'])
    if identity == 'deenhindi-ibnmajah:1250':
        ur = next(v for v in result['language_versions'] if v['language']=='ur')
        assert ur['source']['source_report_count'] == ur['source']['source_report_family_count'] == 1
        assert len(ur['source']['report_component_classifications']) == 2
        assert ur['text'] == targets[identity]['text']
    derived.append(result)
reviews.finish()
assert counts['unchanged_parent_dispositions'] == 477 and counts['untouched_rows'] == 363
assert counts['newly_reviewed_urdu_fields'] == 114 and counts['unchanged_field_decisions'] == 2271
assert counts['lossless_field_partitions'] == 2385 and counts['existing_script_corrections_preserved'] == 19
assert counts['phase9_83_fields_preserved'] == 83
assert after_coverage['ur']['reviewed_fields'] - before_coverage['ur']['reviewed_fields'] == 114
assert after_coverage['ur']['admitted_fields'] - before_coverage['ur']['admitted_fields'] == 114
for language in ('hi', 'ar', 'en', 'ur-Latn'):
    assert before_coverage[language] == after_coverage[language]

# Remove exactly the114 completed source-bound Urdu queue slots, preserving all other values/order.
queue = [json.loads(line) for line in gzip.decompress(queue_before).splitlines()]
assert sum(len(row['fields']) for row in queue) == 6615 and len(queue) == 3598
removed = []
remaining = []
for row in queue:
    keep = []
    for pending in row['fields']:
        if row['id'] in targets and pending['language'] == 'ur':
            assert pending['source_field'] == 'translationUrdu' and pending['text_sha256'] == targets[row['id']]['text_sha256']
            assert row['source_record_sha256'] == new_rows[row['id']]['source_record_sha256']
            assert row['active_review_path'] == selection['prior_active_path']
            removed.append({'id': row['id'], 'field': pending, 'source_record_sha256': row['source_record_sha256'],
                            'prior_queue_record_sha256': sha(encoded(row))})
        else:
            keep.append(pending)
    if keep:
        retained = copy.deepcopy(row)
        retained['fields'] = keep
        assert retained == row, 'Every selected occurrence has only Urdu pending; other queue rows must remain exact.'
        remaining.append(retained)
assert len(removed) == 114 and {row['id'] for row in removed} == set(targets)
remaining_by_language = collections.Counter(field['language'] for row in remaining for field in row['fields'])
assert remaining_by_language == {'hi': 3320, 'ur': 3181}
assert len(remaining) == 3484 and sum(remaining_by_language.values()) == 6501
assert not [row for row in remaining if row['id'].startswith('deenhindi-ibnmajah:') and row['active_review_path'] == selection['prior_active_path']]
queue_after = gzip.compress(b''.join((json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode() for row in remaining), mtime=0)
write(OUT / selection['prior_queue_path'], queue_after)
queue_delta = {'schema': 'hadith-bank-exact-field-queue-delta-v1', 'status': 'PASS',
    'before_sha256': sha(queue_before), 'after_sha256': sha(queue_after), 'removed_count': 114,
    'removed': removed, 'remaining_fields': 6501, 'remaining_occurrences': 3484,
    'remaining_by_language': dict(remaining_by_language), 'all_other_rows_values_and_order_unchanged': True,
    'source_occurrence_count_delta': 0, 'registration_delta': 0}
write(OUT / EVIDENCE / 'priority-field-queue-delta.json', encoded(queue_delta))

selected_count = sum(len(row['selected_spans']) for row in notes)
selected_chars = sum(span['end'] - span['start'] for row in notes for span in row['selected_spans'])
selected_bytes = sum(len(row['complete_field_text'][span['start']:span['end']].encode()) for row in notes for span in row['selected_spans'])
report = {'schema': 'hadith-bank-language-field-extension-validation-v1', 'status': 'PASS',
    'extension_id': EXTENSION, 'source_commit': SOURCE_COMMIT, 'baseline_published_commit': BASELINE_PUBLICATION,
    'dependency_status': 'Prepared while phase9-v2 was staged; exact prior ledger and queue were subsequently independently reopened at5749ec3 before this candidate was serialized.',
    'newly_reviewed_occurrences': 114, 'newly_fully_read_fields': 114, 'newly_admitted_fields': 114,
    'newly_read_context_only_fields': 0, 'newly_read_characters': 29305, 'newly_read_utf8_bytes': 51820,
    'new_admissions_by_language': {'ur': 114}, 'new_hindi_readings_claimed': 0,
    'new_selected_spans': selected_count, 'new_selected_characters': selected_chars, 'new_selected_utf8_bytes': selected_bytes,
    'counts': dict(counts), 'full477_coverage_before': {key: dict(value) for key, value in before_coverage.items()},
    'full477_coverage_after': {key: dict(value) for key, value in after_coverage.items()},
    'source_count_delta': 0, 'registration_delta': 0, 'prior_active_ledger_sha256': sha(old_bytes),
    'new_active_ledger_sha256': sha(new_bytes), 'all_previous_477_record_dispositions_unchanged': True,
    'already_reviewed_hindi_fields_preserved': 114, 'phase9_83_fields_preserved': 83,
    'native_source_reviews_apply_and_finish': 'PASS for all477 records',
    'raw_and_parsed_source_pairs_independently_reopened_and_reparsed': 114,
    'source_provenance_report_sha256': sha(source_proof_bytes), 'frozen_reading_input_sha256': sha(input_bytes),
    'explicit_apparatus_cuts': len(explicit_cuts), 'source_http_requests': 0, 'github_writes': 0,
    'remaining_original3942_priority_fields': 6501, 'remaining_original3942_priority_occurrences': 3484,
    'remaining_original3942_priority_by_language': dict(remaining_by_language),
    'independent_pro_qc': 'not_performed', 'independent_candidate_audit': 'pending exact v2 manifest handoff',
    'attribution_v2_changed_fields':2,'v1_other_field_decisions_unchanged':2383,
    'all_v1_selected_codepoints_and_context_unchanged':True,
    'ibnmajah1250_ordered_attribution_components':2,'ibnmajah1250_source_report_families':1}
write(OUT / EVIDENCE / 'validation.json', encoded(report))
write(ROOT / 'validation-v2.json', encoded(report))
write(ROOT / 'derived-preview-v2.jsonl.gz', gzip.compress(importer.rows_bytes(derived), mtime=0))
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'local_path': str(path),
                      'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': gitsha(data)})
portable = {'schema': 'hadith-bank-language-extension-portable-manifest-v1',
    'extension_id': EXTENSION, 'source_commit': SOURCE_COMMIT, 'baseline_published_commit': BASELINE_PUBLICATION,
    'active_ledger_path': selection['prior_active_path'], 'active_ledger_sha256': sha(new_bytes),
    'files': [{key: value for key, value in row.items() if key != 'local_path'} for row in files]}
write(OUT / EVIDENCE / 'portable-manifest.json', encoded(portable))
data = (OUT / EVIDENCE / 'portable-manifest.json').read_bytes()
files.append({'path': (EVIDENCE / 'portable-manifest.json').as_posix(), 'local_path': str(OUT / EVIDENCE / 'portable-manifest.json'),
              'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': gitsha(data)})
manifest = {'schema': 'hadith-bank-language-extension-delivery-v1', 'files': files,
    'total_files': len(files), 'total_bytes': sum(row['bytes'] for row in files),
    'active_ledger_path': selection['prior_active_path'], 'active_ledger_sha256': sha(new_bytes), 'validation': report}
write(ROOT / 'delivery-manifest-v2.json', encoded(manifest))
print(json.dumps({'status': 'PASS', 'active_sha256': sha(new_bytes), 'manifest_sha256': sha(encoded(manifest)),
                  'files': len(files), 'bytes': manifest['total_bytes'], 'counts': dict(counts),
                  'new_selected_spans': selected_count, 'new_selected_characters': selected_chars,
                  'new_selected_utf8_bytes': selected_bytes, 'remaining_priority_fields': 6501}, indent=2))
