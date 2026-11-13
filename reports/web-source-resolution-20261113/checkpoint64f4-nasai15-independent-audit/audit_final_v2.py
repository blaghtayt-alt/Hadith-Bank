"""Independent final source, semantic-plan, surgical and native audit of Nasai15 v2."""
from pathlib import Path
import collections
import copy
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
OWNER = WORK / 'phase23-checkpoint64f4-nasai15-review'
CENTRAL = WORK / 'phase22-successor-acquisition-monitor/complete-held-evidence'
ACTIVE = 'imports/web-deenhindi-20261112/reviews/source-review-checkpoint64f4-nasai15-20261113.json.gz'
EVID = 'imports/web-deenhindi-20261112/reviews/checkpoint64f4-nasai15-20261113'
PIN = '64f4ed50ed6026855237a5d547a86dd03e73f804'
M2_SHA = '17a62ba0e1c9e90a09e52497c981926455cbc90f9ea831c425aa2007bbdaf9cc'
A2_SHA = '6302d9223454de28685d5f665688f2fd40c10b0292b1081802da97b9c61f8a98'
M1_SHA = 'f98a9ca4644a15fa2bfedfd2a1c571d84275a7e1f315a2090f3c0f4409e75438'
A1_SHA = '52e11ef9b376797269f4a09bbc0f31cf0629f9c9236d6b6577185f3e2341dd76'
READ_SHA = 'dbd2b4f8d1aa09eb4bda2075791cf7b317518df385d8bfa8fb416d54b324b801'
FIND_SHA = '2beb8ed12982a6b6376f5f82bc11adac312acd83d9a5fb5d60f3706add0ce8c1'
PLAN_SHA = 'e1d9160c8d2b0ae9d379a8412409357bf68c1c69e53267ca21bc384dd88c7f8a'
SOURCE_SHA = 'fad5e4e118850c7d49bbeb590f44c2af1c80d35d9552c0a623f2cbb362da6270'
FIELDS = {'ar': 'textArabic', 'hi': 'translationHindi', 'ur': 'translationUrdu',
          'ur-Latn': 'translationUrduRoman', 'en': 'translationEnglish'}
sys.dont_write_bytecode = True
sys.path.insert(0, str(WORK / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews


def sha(data):
    return hashlib.sha256(data).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def bind(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': sha(data),
            'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, ('immutable output differs', str(path))
    else:
        path.write_bytes(data)


def leaves(value):
    if isinstance(value, dict):
        return sum(map(leaves, value.values()))
    if isinstance(value, list):
        return sum(map(leaves, value))
    return 1


def equal(a, b):
    assert a == b
    return leaves(a)


def positions(field):
    return {i for span in field['spans'] for i in range(span['start'], span['end'])}


def pure(span):
    return {k: v for k, v in span.items() if k != 'reason'}


baseline_raw = (ROOT / 'input/cohort.jsonl').read_bytes()
assert sha(baseline_raw) == '23013833e118d6b9585cfe40c2f41021f50c06d0673d12f71add638a25c68052'
source_rows = list(map(json.loads, baseline_raw.splitlines()))
sources = {'deenhindi-' + r['collection'] + ':' + r['number']: r for r in source_rows}
assert len(sources) == len(source_rows) == 15
for path, expected in (
    (ROOT / 'complete-independent-source-first-readings.json', READ_SHA),
    (ROOT / 'independent-boundary-findings-v1.json', FIND_SHA),
    (ROOT / 'accepted-reviewed-field-plan-v1.json', PLAN_SHA),
    (ROOT / 'input/own-source-verification.json', SOURCE_SHA),
):
    assert bind(path)['sha256'] == expected
reading = read(ROOT / 'complete-independent-source-first-readings.json')
assert not reading['primary_candidate_and_notes_inspected']
assert (reading['complete_fields_read'], reading['characters_read'], reading['utf8_bytes_read']) == (30, 13448, 28971)
read_fields = {(r['occurrence_id'], r['language']): r for r in reading['fields']}
assert len(read_fields) == 30 and all(r['complete_own_field_read'] and not r['primary_candidate_or_semantic_notes_opened_before_reading'] for r in reading['fields'])
findings = read(ROOT / 'independent-boundary-findings-v1.json')
plan_doc = read(ROOT / 'accepted-reviewed-field-plan-v1.json')
plan = {(r['id'], r['language']): r for r in plan_doc['fields']}
assert set(plan) == set(read_fields) and len(findings['required_findings']) == 2
assert findings['all_other28_read_fields_accepted'] and findings['accepted_exact_plan_sha256'] == PLAN_SHA
manifest_path = OWNER / 'delivery-manifest-v2.json'
assert bind(manifest_path)['sha256'] == M2_SHA
manifest = read(manifest_path)
repo = ROOT / 'validation/final'
payload = []
for item in manifest['files']:
    relative = Path(item['path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    path = Path(item['local_path'])
    assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(OWNER)
    observed = bind(path)
    assert all(observed[k] == item[k] for k in ('bytes', 'sha256', 'git_blob_sha1'))
    put(repo / relative, path.read_bytes())
    payload.append({'path': str(relative), 'owner_path': str(path), **observed})
assert len(payload) == len({r['path'] for r in payload}) == 48
assert bind(repo / ACTIVE)['sha256'] == A2_SHA
active = read(repo / ACTIVE)
baseline = repo / active['source_ledger_path']
assert bind(baseline)['sha256'] == active['source_ledger_sha256']
assert list(map(json.loads, gzip.decompress(baseline.read_bytes()).splitlines())) == source_rows
before_path = ROOT / 'input/primary-active-v1.json.gz'
assert bind(before_path)['sha256'] == A1_SHA
before = read(before_path)
old = {r['id']: r for r in before['records']}
new = {r['id']: r for r in active['records']}
assert set(old) == set(new) == set(sources)
assert {k: v for k, v in before.items() if k != 'records'} == {k: v for k, v in active.items() if k != 'records'}
requested = {
    ('deenhindi-nasai:2732', 'hi'): (1507, 1522, '(10वीं ज़िलहज्ज)'),
    ('deenhindi-nasai:2732', 'ur'): (1442, 1460, '( دسویں ذی الحجہ )'),
}
changes = []
unchanged_fields = unchanged_parents = 0
for ident, left in old.items():
    right = new[ident]
    assert {k: v for k, v in left.items() if k != 'field_reviews'} == {k: v for k, v in right.items() if k != 'field_reviews'}
    if ident != 'deenhindi-nasai:2732':
        assert left == right
        unchanged_parents += 1
    a = {f['language']: f for f in left['field_reviews']}
    b = {f['language']: f for f in right['field_reviews']}
    assert set(a) == set(b) == set(FIELDS)
    for language, previous in a.items():
        key = (ident, language)
        final = b[language]
        if key in plan:
            assert sha(enc(previous)) == plan[key]['v1_field_sha256']
            assert previous['spans'] == plan[key]['current_spans']
            assert [pure(s) for s in final['spans']] == [pure(s) for s in plan[key]['accepted_spans']]
        if key not in requested:
            assert previous == final
            unchanged_fields += 1
            continue
        stable = lambda field: {k: v for k, v in field.items() if k not in ('spans', 'reason', 'source_text_annotations')}
        assert stable(previous) == stable(final)
        start, end, literal = requested[key]
        text = sources[ident]['source_record'][previous['source_field']]
        assert text[start:end] == literal
        assert positions(previous) - positions(final) == set(range(start, end))
        assert not positions(final) - positions(previous)
        old_attributes = {i: {k: v for k, v in s.items() if k not in ('start', 'end', 'sha256', 'reason')} for s in previous['spans'] for i in range(s['start'], s['end'])}
        for span in final['spans']:
            attrs = {k: v for k, v in span.items() if k not in ('start', 'end', 'sha256', 'reason')}
            assert all(attrs == old_attributes[i] for i in range(span['start'], span['end']))
        changes.append({'id': ident, 'language': language, 'start': start, 'end': end,
                        'text': literal, 'characters': end - start, 'utf8_bytes': len(literal.encode()),
                        'before_field_sha256': sha(enc(previous)), 'after_field_sha256': sha(enc(final)),
                        'all_surviving_attribution_and_report_family_values_exact': True})
assert unchanged_fields == 73 and unchanged_parents == 14
assert sum(r['characters'] for r in changes) == 33 and sum(r['utf8_bytes'] for r in changes) == 65
v1manifest_path = OWNER / 'delivery-manifest-v1.json'
assert bind(v1manifest_path)['sha256'] == M1_SHA
v1manifest = read(v1manifest_path)
archive = Path(EVID) / 'independent-calendar-v2/before-v1'
assert (repo / archive / 'delivery-manifest-v1.json').read_bytes() == v1manifest_path.read_bytes()
assert len(v1manifest['files']) == 21
for item in v1manifest['files']:
    data = Path(item['local_path']).read_bytes()
    assert sha(data) == item['sha256'] and len(data) == item['bytes']
    assert (repo / archive / 'payload' / item['path']).read_bytes() == data
authority = read(CENTRAL / 'evidence-manifest.json')
entries = read(CENTRAL / 'held-state-entries.json')
assert authority['saved_head'] == PIN
engine = SourceReviews(repo, 'deenhindi')
counts = collections.Counter()
metadata = collections.Counter()
source_proofs, field_proofs = [], []
for ident, saved in sources.items():
    entry = entries[saved['collection'] + ':' + saved['number']]
    assert entry['parsed']['path'] == saved['parsed_path']
    for descriptor in (saved['snapshot'], entry['parsed']):
        path = ROOT / 'sources' / descriptor['path']
        observed = bind(path)
        assert all(observed[k] == authority['files'][descriptor['path']][k] for k in ('bytes', 'sha256', 'git_blob_sha1'))
        plain = importer.checked_bytes(ROOT / 'sources', descriptor)
        source_proofs.append({'id': ident, 'path': descriptor['path'], **observed,
                              'plain_bytes': len(plain), 'plain_sha256': sha(plain)})
    parsed = json.loads(importer.checked_bytes(ROOT / 'sources', entry['parsed']))
    for key in ('collection', 'number', 'source_record', 'source_reference_verbatim', 'snapshot'):
        assert parsed[key] == saved[key]
    assert parsed['classification'] == saved.get('intake_classification', saved['classification'])
    obj, reference = importer.parse_record(importer.checked_bytes(ROOT / 'sources', saved['snapshot']), saved['collection'], saved['number'])
    assert obj == saved['source_record'] and reference == saved['source_reference_verbatim']
    decision = new[ident]
    assert decision['source_record_sha256'] == sha(importer.json_bytes(obj))
    assert decision['source_snapshot'] == saved['snapshot'] and decision['source_reference_verbatim'] == reference
    assert decision['collection'] == saved['collection'] and decision['number'] == saved['number']
    assert decision['verified_external_reference'] is None
    original = importer.canonical_record(saved)
    untouched = copy.deepcopy(original)
    revised, action = engine.apply(copy.deepcopy(original), saved=saved)
    assert original == untouched and action == decision['decision'] == 'register'
    counts['register'] += 1
    assert revised['review']['independent_pro_qc'] == 'not_performed'
    assert revised['review']['certified_release_eligible'] is False
    for key, value in original.items():
        if key not in ('text', 'language_versions', 'review', 'content_kind', 'extraction'):
            metadata['parent'] += equal(value, revised[key])
    fields = {f['language']: f for f in decision['field_reviews']}
    originals = {v['language']: v for v in original['language_versions']}
    revised_fields = {v['language']: v for v in revised['language_versions']}
    assert len(fields) == len(decision['field_reviews']) == 5
    assert set(fields) == set(originals) == set(revised_fields) == set(FIELDS)
    for language, name in FIELDS.items():
        key = (ident, language)
        text = obj[name]
        assert isinstance(text, str) and text
        before_field, after_field, field = originals[language], revised_fields[language], fields[language]
        assert before_field['text'] == text and field['source_field'] == name
        assert field['language_version_id'] == ident + ':' + language
        assert field['text_sha256'] == sha(text.encode()) and field['text_chars'] == len(text)
        reviewed = key in read_fields
        assert field['reviewed'] is reviewed
        assert field['chars_reviewed'] == (len(text) if reviewed else 0)
        assert field['bytes_reviewed'] == (len(text.encode()) if reviewed else 0)
        counts['source_slots'] += 1
        cursor = 0
        for span in field['spans']:
            start, end = span['start'], span['end']
            assert cursor <= start < end <= len(text)
            assert span['sha256'] == sha(text[start:end].encode())
            assert all(span[k] for k in ('component_id', 'report_type', 'speaker', 'source_report_family_id'))
            cursor = end
        counts['selected_spans'] += len(field['spans'])
        counts['selected_characters'] += len(positions(field))
        counts['selected_utf8_bytes'] += sum(len(text[s['start']:s['end']].encode()) for s in field['spans'])
        if reviewed:
            own = read_fields[key]
            assert own['text'] == text and own['text_sha256'] == sha(text.encode())
            assert own['source_record_sha256'] == sha(importer.json_bytes(obj))
            assert [pure(s) for s in field['spans']] == [pure(s) for s in plan[key]['accepted_spans']]
            assert field['spans'] and field['action'] in ('whole', 'excerpts')
            counts['complete_fields_read'] += 1
            counts['characters_read'] += len(text)
            counts['utf8_bytes_read'] += len(text.encode())
            counts['admitted_fields'] += 1
        else:
            assert not field['spans'] and field['action'] == 'unreviewed' and after_field['text'] is None
            counts['unread_context_fields'] += 1
        assert (after_field['text'] or '') == ''.join(text[s['start']:s['end']] for s in field['spans'])
        context = [(c['source_span'][0], c['source_span'][1], c['text']) for c in after_field['comments'] if c.get('source_span') is not None]
        pieces = [(s['start'], s['end'], text[s['start']:s['end']]) for s in field['spans']] + context
        cursor = 0
        for start, end, literal in sorted(pieces):
            assert start == cursor and text[start:end] == literal
            cursor = end
        assert cursor == len(text) and ''.join(t for a, b, t in sorted(pieces)) == text
        counts['lossless_nonempty_partitions'] += 1
        if reviewed:
            counts['reviewed_context_gaps'] += len(context)
        assert 'observed_script' not in field and before_field['script'] == after_field['script']
        for k, value in before_field.items():
            if k not in ('text', 'scope', 'source', 'comments'):
                metadata['language'] += equal(value, after_field[k])
        for k, value in before_field['source'].items():
            metadata['source'] += equal(value, after_field['source'][k])
        for i, comment in enumerate(before_field.get('comments', [])):
            for k, value in comment.items():
                metadata['previous_comments'] += equal(value, after_field['comments'][i][k])
        field_proofs.append({'id': ident, 'language': language, 'source_field_sha256': sha(text.encode()),
            'complete_own_field_read': reviewed, 'exact_final_field_definition_sha256': sha(enc(field)),
            'selected_spans': field['spans'], 'context_ranges': [[a, b] for a, b, t in context],
            'lossless_full_source_partition': True})
engine.finish()
assert (counts['register'], counts['source_slots'], counts['lossless_nonempty_partitions']) == (15, 75, 75)
assert (counts['complete_fields_read'], counts['characters_read'], counts['utf8_bytes_read']) == (30, 13448, 28971)
assert (counts['admitted_fields'], counts['unread_context_fields'], counts['selected_spans']) == (30, 45, 51)
assert len(source_proofs) == 30 and len(field_proofs) == 75
for item in payload:
    assert bind(Path(item['owner_path'])) == {k: item[k] for k in ('bytes', 'sha256', 'git_blob_sha1')}
assert bind(manifest_path)['sha256'] == M2_SHA
assert (ROOT / 'input/cohort.jsonl').read_bytes() == baseline_raw
proof = {'schema': 'independent-source-semantic-plan-and-native-proof-v2',
    'source_files': source_proofs, 'fields': field_proofs, 'primary_payload': payload,
    'exact_v1_to_v2_changes': changes}
proof_bytes = gzip.compress(enc(proof), mtime=0)
put(ROOT / 'field-and-source-proof-final.json.gz', proof_bytes)
report = {'schema': 'independent-complete-reading-final-audit-v2', 'status': 'PASS',
    'source_checkpoint': PIN, 'primary_manifest': 'delivery-manifest-v2.json',
    'primary_manifest_sha256': M2_SHA, 'primary_payload_files_verified': len(payload),
    'primary_active_path': ACTIVE, 'primary_active_sha256': A2_SHA,
    'source_baseline_path': active['source_ledger_path'], 'source_baseline_sha256': active['source_ledger_sha256'],
    'prior_primary_manifest_sha256': M1_SHA, 'prior_primary_active_sha256': A1_SHA,
    'independent_source_first_receipt_sha256': READ_SHA, 'independent_source_proof_sha256': SOURCE_SHA,
    'independent_complete_boundary_findings_sha256': FIND_SHA,
    'accepted_exact_complete_field_plan_sha256': PLAN_SHA,
    'counts': dict(counts), 'registered_parents': 15, 'resolved_source_only_parents': 0,
    'reviewed_context_fields': 0, 'empty_source_fields': 0,
    'metadata_leaf_equalities': dict(metadata), 'metadata_leaf_equalities_total': sum(metadata.values()),
    'source_files_reopened': 30, 'complete_source_reparses': 15,
    'stored_plain_git_hashes_pass': True, 'native_apply_and_finish_pass': True,
    'exact_changes': changes, 'characters_moved_to_context': 33, 'utf8_bytes_moved_to_context': 65,
    'characters_added': 0, 'unchanged_other_field_definitions': 73, 'unchanged_whole_parents': 14,
    'all_retained_source_positions_types_speakers_components_and_families_exact': True,
    'all21_v1_payloads_plus_original_manifest_archived_exact': True,
    'initial_source_first_receipts_and_notes_unchanged': True,
    'all_independently_accepted_field_masks_match': True,
    'exact_original_source_objects_references_grades_and_unknowns_preserved': True,
    'unread_siblings_have_no_selected_text': True, 'primary_candidate_input_mutation': False,
    'required_amendments': [], 'open_findings': [],
    'transparent_initial_refinements': findings['refinements_of_preserved_initial_notes'],
    'resolution': 'The two tenth-DhulHijja appositions are lexical calendar equivalences adjacent to the already named event day and now remain complete source context. The eighth-DhulHijja command timing, sacrifice act and all other material source scope remain selected. The incomplete endings and source-local voice limits are retained with explicit qualifications, without invented continuations.',
    'field_source_proof_sha256': sha(proof_bytes), 'new_reading_credit_from_amendment': 0,
    'source_http_requests': 0, 'github_writes': 0,
    'limitations': 'Independent source-bound reading and boundary audit only. No authenticity certification, external canonical verification or deployment claim. Exactly30 original Hindi/Urdu fields were read;45 other source fields remain unread context.'}
put(ROOT / 'independent-final-audit.json', enc(report))
print(json.dumps({'status': 'PASS', 'report_sha256': sha(enc(report)), 'counts': dict(counts),
                  'metadata_leaf_equalities': sum(metadata.values()), 'source_files': 30, 'reparses': 15}))
