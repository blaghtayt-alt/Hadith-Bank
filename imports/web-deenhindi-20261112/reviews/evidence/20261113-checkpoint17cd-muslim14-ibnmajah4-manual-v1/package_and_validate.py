"""Package explicitly read Muslim14/IbnMajah4 fields and verify native source preservation offline."""
import collections
import copy
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

from manual_boundaries import READINGS
from manual_source_first_readings import NOTES
from verify_local_sources import verify as verify_local_sources

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

COMMIT = '17cd396eb858a29162505d545aad556ac73ce9ce'
NAME = '20261113-checkpoint17cd-muslim14-ibnmajah4-manual-v1'
SOURCE_ONLY = set()
OUT = ROOT / 'publish-v1'
REV = Path('imports/web-deenhindi-20261112/reviews')
EVIDENCE = REV / 'evidence' / NAME
ACTIVE = REV / ('source-review-' + NAME + '.json.gz')
sha = lambda value: hashlib.sha256(value).hexdigest()
enc = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

assert not (ROOT / 'delivery-manifest-v1.json').exists(), 'Frozen package must not be rewritten.'


def put(relative, data):
    path = OUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def anchor(text, literal):
    assert isinstance(literal, str) and text.count(literal) == 1, ('nonunique or missing explicit anchor', literal, text.count(literal))
    return text.index(literal)


def complement(text, spans):
    result = []
    cursor = 0
    for span in spans:
        start, end = span['start'], span['end']
        assert 0 <= cursor <= start < end <= len(text)
        if start > cursor: result.append((cursor, start))
        cursor = end
    if cursor < len(text): result.append((cursor, len(text)))
    return result


def span_for(text, start, end, part, note):
    assert 0 <= start < end <= len(text) and text[start:end].strip(), (start, end, part, repr(text[max(0,start-40):min(len(text),end+40)]))
    return {'start': start, 'end': end, 'sha256': sha(text[start:end].encode()),
            'component_id': part.get('id', 'report-1'),
            'report_type': part.get('type', note['type']),
            'speaker': part.get('speaker', note['speaker']),
            'source_report_family_id': note['source_report_family_id'],
            'reason': note['note']}


def field_review(version, index, note):
    text = version['text']
    result = {'version_id': version['id'], 'language': version['language'],
              'source_field': importer.LANGUAGE_FIELDS[version['language']],
              'field_path': ['language_versions', index, 'text'],
              'text_sha256': sha(text.encode()), 'text_chars': len(text),
              'reviewed': note is not None,
              'chars_reviewed': len(text) if note else 0,
              'bytes_reviewed': len(text.encode()) if note else 0}
    if note is None:
        result.update(decision='unreviewed', selected_spans=[], review_scope='not_read_in_this_batch',
                      reason='This sibling field has not received its own complete semantic reading in this batch. Its entire original text is retained as context, without quotation admission.')
        return result
    spans, cuts = [], []
    if not note['context_all']:
        for item in note['context']:
            if isinstance(item, str):
                start = anchor(text, item)
                cuts.append((start, start + len(item)))
            elif 'start' in item:
                start, end = item['start'], item['end']
                assert type(start) is int and type(end) is int and 0 <= start < end <= len(text)
                assert text[start:end] == item['text'], (version['id'], item)
                cuts.append((start, end))
            else:
                literal, count = item['text'], item['count']
                assert type(count) is int and count > 1 and text.count(literal) == count
                cursor = 0
                for _ in range(count):
                    start = text.index(literal, cursor)
                    cuts.append((start, start + len(literal)))
                    cursor = start + len(literal)
        cuts.sort()
        assert all(a[1] <= b[0] for a, b in zip(cuts, cuts[1:]))
        if 'exact_selections' in note:
            assert not cuts and 'segments' not in note
            for item in note['exact_selections']:
                start = anchor(text, item['text'])
                spans.append(span_for(text, start, start + len(item['text']), item, note))
        else:
            last = 0
            for part in note.get('segments', [{'start': None, 'end': None, 'id': 'report-1'}]):
                start = 0 if part['start'] is None else part['start'] if type(part['start']) is int else anchor(text, part['start'])
                end = len(text) if part['end'] is None else part['end'] if type(part['end']) is int else anchor(text, part['end'])
                assert 0 <= last <= start < end <= len(text)
                last = end
                keep = [(start, end)]
                for cut_start, cut_end in cuts:
                    pieces = []
                    for a, b in keep:
                        if cut_end <= a or b <= cut_start: pieces.append((a, b))
                        else:
                            if a < cut_start: pieces.append((a, cut_start))
                            if cut_end < b: pieces.append((cut_end, b))
                    keep = pieces
                spans.extend(span_for(text, a, b, part, note) for a, b in keep)
        assert spans
    contexts = complement(text, spans)
    assert all(any(x <= a < b <= y for x, y in contexts) for a, b in cuts)
    selected_positions = {i for span in spans for i in range(span['start'], span['end'])}
    retained = []
    for literal in note.get('retained_meaningful_structures', []):
        assert literal in text
        for match in re.finditer(re.escape(literal), text):
            a, b = match.span()
            assert set(range(a, b)) <= selected_positions, ('meaningful qualifier lost', version['id'], literal)
            retained.append({'start': a, 'end': b, 'text': literal, 'sha256': sha(literal.encode()),
                             'reason': note['note']})
    result.update(decision='source_context' if not spans else 'whole' if len(spans) == 1 and spans[0]['start'] == 0 and spans[0]['end'] == len(text) else 'excerpts',
                  selected_spans=spans, reason=note['note'],
                  review_method='manual_complete_own_field_reading_and_exact_span_selection',
                  review_scope='Complete own saved field read for its supplied report, voices, defects and boundaries; no sibling fills missing wording or attribution.',
                  reviewed_context_spans=[{'start': a, 'end': b, 'sha256': sha(text[a:b].encode()), 'reason': note['note']} for a, b in contexts],
                  explicit_context_cuts=[{'start': a, 'end': b, 'sha256': sha(text[a:b].encode()), 'text': text[a:b]} for a, b in cuts],
                  retained_meaningful_structures=retained)
    if spans: result.update(report_type=note['type'], speaker=note['speaker'])
    if 'boundary_refinement' in note: result['boundary_refinement'] = note['boundary_refinement']
    if 'source_text_annotations' in note: result['source_text_annotations'] = copy.deepcopy(note['source_text_annotations'])
    return result


source_bytes = (ROOT / 'input/cohort.jsonl').read_bytes()
assert sha(source_bytes) == '4e89ffeedce15ea35358c8c1d5dd4079047505909ad82e436b9730f8ba90c28a'
rows = [json.loads(line) for line in source_bytes.splitlines()]
source_checks = json.loads((ROOT / 'source-verification.json').read_bytes())
checks = {r['occurrence_id']: r for r in source_checks['records']}
assert source_checks['result'] == 'PASS' and source_checks['source_commit'] == COMMIT
assert source_checks['source_files_reopened'] == 36 and source_checks['complete_raw_reparses'] == 18
assert len(rows) == len(READINGS) == len(checks) == 18
reading_receipt = (ROOT / 'complete-source-first-readings.json').read_bytes()
assert sha(reading_receipt) == '9f0c4a8c57b6f864be0be5afe64698e69e83f6ea81e9c0d4d21722210ce2c2e4'
reading_input = (ROOT / 'input/full-hi-ur-reading-input-36.jsonl').read_bytes()
assert sha(reading_input) == '2f2fb4a801e29497ed7f62f768af9d1899c19063b89e1b26a2fda9b9e17ab5bc'

reading_rows = [json.loads(line) for line in reading_input.splitlines()]
receipt = json.loads(reading_receipt)
assert len(reading_rows) == len(NOTES) == receipt['complete_fields_read'] == 36
for note_file in receipt['source_first_note_files']:
    assert sha((ROOT/note_file['name']).read_bytes()) == note_file['sha256']
assert {(r['occurrence_id'], r['language']) for r in reading_rows} == set(NOTES)
assert {(oid, language) for oid, fields in READINGS.items() for language in fields} == {(r['occurrence_id'].removeprefix('deenhindi-'), r['language']) for r in reading_rows}
assert {r['occurrence_id']: r['source_record_sha256'] for r in reading_rows} == {oid: r['source_record_sha256'] for oid, r in checks.items()}
for r in reading_rows:
    assert sha(r['text'].encode()) == r['text_sha256']
    assert receipt['fields'][reading_rows.index(r)]['source_first_note'] == NOTES[r['occurrence_id'], r['language']]
local_source_validation = verify_local_sources()
assert local_source_validation['result'] == 'PASS'
records, boundary_view = [], []
for saved in rows:
    key = saved['collection'] + ':' + saved['number']
    oid = 'deenhindi-' + key
    baseline = importer.canonical_record(saved)
    fields = [field_review(v, i, READINGS[key].get(v['language'])) for i, v in enumerate(baseline['language_versions'])]
    assert len(fields) == 5 and all(saved['source_record'][name] for name in importer.LANGUAGE_FIELDS.values())
    chosen = any(f['selected_spans'] for f in fields)
    if not chosen: assert all(f['reviewed'] and f['decision'] == 'source_context' for f in fields)
    parsed = next(item for item in checks[oid]['files'] if item['kind'] == 'parsed')
    decision = {'occurrence_id': oid, 'collection': saved['collection'], 'number': saved['number'],
        'decision': 'register' if chosen else 'exclude',
        'source_record_sha256': sha(importer.json_bytes(saved['source_record'])),
        'source_snapshot': saved['snapshot'], 'source_parsed_path': saved['parsed_path'],
        'source_parsed_sha256': parsed['sha256'],
        'source_reference_verbatim': saved['source_reference_verbatim'],
        'numbering_system': 'deenhindi_source_local', 'external_canonical_identity': None,
        'verified_external_reference': None, 'independent_pro_qc': 'not_performed',
        'reviewer': 'OpenAI assistant /root/queue_audit; complete own-field source reading, not Pro certification',
        'report_type': 'source_numbered_report_with_individually_qualified_components' if chosen else 'source_only_transmission_or_omission_apparatus',
        'speaker': 'See each independently read field and component for its actual supplied voice and limitations.' if chosen else None,
        'reason': ('The individually read source fields support only the selected actual reports or finite fragments under their own attribution. Missing wording, speakers and source defects are not repaired; unread siblings remain context.' if chosen else
                   'All five nonempty own language fields were completely read and supply only the source-bound transmission or negative-omission apparatus described separately in their immutable reading notes. No affirmative body of the missing narration is supplied or reconstructed; every byte and all metadata remain source context.'),
        'fields': fields, 'inspected_empty_source_fields': []}
    assert decision['source_record_sha256'] == checks[oid]['source_record_sha256']
    records.append(decision)
    boundary_view.append({'occurrence_id': oid, 'decision': decision['decision'],
        'source_record_sha256': decision['source_record_sha256'],
        'fields': [{'language': f['language'], 'text_sha256': f['text_sha256'],
            'source_text': saved['source_record'][f['source_field']], 'reason': f['reason'],
            'selected': [dict(s, text=saved['source_record'][f['source_field']][s['start']:s['end']]) for s in f['selected_spans']],
            'context': [dict(s, text=saved['source_record'][f['source_field']][s['start']:s['end']]) for s in f['reviewed_context_spans']]} for f in fields if f['reviewed']]})

put(EVIDENCE / 'selected-context-boundary-view.json.gz', gzip.compress(enc(boundary_view), mtime=0))
baseline_path = EVIDENCE / 'source-ledger-18.jsonl.gz'
baseline_data = gzip.compress(source_bytes, mtime=0)
put(baseline_path, baseline_data)
document = {'schema': 'hadith-bank-web-source-review-v1', 'site': 'deenhindi',
    'review_batch': NAME, 'review_date_utc': '2026-11-13', 'source_commit': COMMIT,
    'independent_pro_qc': 'not_performed', 'source_ledger_path': baseline_path.as_posix(),
    'source_ledger_sha256': sha(baseline_data), 'source_ledger_uncompressed_sha256': sha(source_bytes),
    'scope': '18 new checkpoint17cd held occurrences:14 Muslim and4 IbnMajah.36 complete own fields were read and admitted,18 Hindi and18 Urdu;54 unread sibling fields remain complete source context. Every parent supplies its own finite report or encounter. Pure routes, omitted-continuation pointers, predicate-free nominal variants and explicit lexical apparatus remain context. Damaged Hindi2669 attribution, Urdu2701 printed name and cross-language2664 omissions remain qualified without repair. No canonical identity or authenticity certification is asserted.',
    'source_first_receipt_sha256': sha(reading_receipt), 'records': records}
active_data = gzip.compress(enc(document), mtime=0)
put(ACTIVE, active_data)
for name in ('source-verification.json', 'complete-source-first-readings.json'):
    put(EVIDENCE / (name + '.gz'), gzip.compress((ROOT / name).read_bytes(), mtime=0))
put(EVIDENCE / 'partition-receipt.json.gz', gzip.compress((ROOT / 'input/partition-receipt.json').read_bytes(), mtime=0))
put(EVIDENCE / 'full-hi-ur-reading-input-36.jsonl.gz', gzip.compress(reading_input, mtime=0))
put(EVIDENCE / 'manual-field-boundary-notes.json.gz', gzip.compress(enc({'schema': 'hadith-bank-manual-field-boundaries-v1',
    'source_commit': COMMIT, 'source_first_receipt_sha256': sha(reading_receipt),
    'records': READINGS, 'no_heuristic_batch_approvals': True, 'independent_pro_qc': 'not_performed'}), mtime=0))
for name in ('source_first_batch01.py', 'source_first_batch02.py', 'source_first_batch03.py', 'manual_source_first_readings.py', 'manual_boundaries.py', 'verify_local_sources.py', 'prepare_sources.py', 'freeze_source_first_readings.py', 'package_and_validate.py'):
    put(EVIDENCE / name, (ROOT / name).read_bytes())

engine = SourceReviews(OUT, 'deenhindi')
totals = collections.Counter()
coverage = collections.defaultdict(collections.Counter)
derived = []
parent_keys = ('id', 'language', 'book_key', 'edition', 'title', 'source', 'number', 'narrator', 'translator', 'ai_translation',
               'translation_provenance', 'commentary', 'footnotes', 'references', 'grading', 'page', 'source_headings', 'rights', 'source_locator')


def count_leaves(value):
    if isinstance(value, dict): return sum(count_leaves(v) for v in value.values()) if value else 1
    if isinstance(value, list): return sum(count_leaves(v) for v in value) if value else 1
    return 1


for saved, decision in zip(rows, records):
    baseline = importer.canonical_record(saved)
    before = copy.deepcopy(baseline)
    result, action = engine.apply(baseline, saved=saved)
    assert baseline == before and action == decision['decision']
    for key in parent_keys:
        assert result.get(key) == before.get(key), (decision['occurrence_id'], key)
        totals['parent_metadata_value_equalities'] += count_leaves(before.get(key))
    assert result['number']['canonical'] is None
    assert result['review']['independent_pro_qc'] == 'not_performed' and result['review']['certified_release_eligible'] is False
    assert len(result['language_versions']) == len(before['language_versions']) == 5
    admitted = {}
    for original, version, field in zip(before['language_versions'], result['language_versions'], decision['fields']):
        text, language, spans = original['text'], original['language'], field['selected_spans']
        assert original['id'] == version['id'] == field['version_id']
        assert language == version['language'] == field['language']
        assert sha(text.encode()) == field['text_sha256'] and saved['source_record'][field['source_field']] == text
        for key, value in original.items():
            if key not in ('text', 'scope', 'quotation_status', 'comments', 'source'):
                assert version.get(key) == value, (decision['occurrence_id'], language, key)
                totals['language_metadata_value_equalities'] += count_leaves(value)
        for key, value in original['source'].items():
            assert version['source'].get(key) == value, (decision['occurrence_id'], language, 'source', key)
            totals['source_metadata_value_equalities'] += count_leaves(value)
        assert original.get('comments', []) == []
        for counter in (totals, coverage[language]): counter['nonempty_fields'] += 1
        if field['reviewed']:
            assert field['chars_reviewed'] == len(text) and field['bytes_reviewed'] == len(text.encode())
            assert ('deenhindi-' + saved['collection'] + ':' + saved['number'], language) in NOTES
            for counter in (totals, coverage[language]):
                counter['complete_fields_read'] += 1
                counter['characters_read'] += len(text)
                counter['utf8_bytes_read'] += len(text.encode())
        else:
            assert not spans and field['decision'] == 'unreviewed' and field['chars_reviewed'] == field['bytes_reviewed'] == 0
            for counter in (totals, coverage[language]): counter['unread_context_fields'] += 1
        pieces = []
        if spans:
            assert field['reviewed'] and version['text'] == ''.join(text[s['start']:s['end']] for s in spans)
            admitted[language] = version['text']
            for s in spans:
                a, b = s['start'], s['end']
                assert sha(text[a:b].encode()) == s['sha256']
                pieces.append((a, b, text[a:b]))
            for counter in (totals, coverage[language]):
                counter['admitted_fields'] += 1
                counter['selected_spans'] += len(spans)
                counter['admitted_characters'] += len(version['text'])
                counter['admitted_utf8_bytes'] += len(version['text'].encode())
            classifications = version['source']['report_component_classifications']
            assert {c['source_report_family_id'] for c in classifications} == {saved['collection'] + ':' + saved['number'] + ':source-numbered-report'}
            for c in classifications:
                assert c['speaker_description'] and c['report_type']
                assert c['spans'] == [[s['start'], s['end']] for s in spans if s['component_id'] == c['component_id']]
            totals['typed_components'] += len(classifications)
        else:
            assert version['text'] is None
            if field['reviewed']:
                for counter in (totals, coverage[language]): counter['fully_read_context_only_fields'] += 1
        for comment in version['comments']:
            a, b = comment['source_span']
            assert comment['scope'] == 'source_context_not_narration' and comment['text'] == text[a:b]
            assert comment['source_text_sha256'] == sha(text[a:b].encode())
            pieces.append((a, b, comment['text']))
        cursor = 0
        for a, b, value in sorted(pieces):
            assert a == cursor and a < b and text[a:b] == value
            cursor = b
        assert cursor == len(text) and ''.join(x[2] for x in sorted(pieces)) == text
        if field['reviewed']:
            assert [c['source_span'] for c in version['comments']] == [[c['start'], c['end']] for c in field['reviewed_context_spans']]
            totals['reviewed_context_gaps'] += len(version['comments'])
            totals['retained_meaningful_structures'] += len(field['retained_meaningful_structures'])
        totals['lossless_partitions'] += 1
    expected_languages = {'hi', 'ur'}
    assert set(admitted) == expected_languages
    if action == 'register':
        assert result['text'] == {'arabic': admitted.get('ar'), 'translation': admitted.get('hi')}
    else:
        assert not admitted and result['text'] == before['text']
    totals[action + '_occurrences'] += 1
    derived.append(result)
engine.finish()
assert totals['register_occurrences'] == 18 and totals['exclude_occurrences'] == 0
assert totals['nonempty_fields'] == totals['lossless_partitions'] == 90
assert totals['complete_fields_read'] == 36 and totals['admitted_fields'] == 36
assert totals['fully_read_context_only_fields'] == 0 and totals['unread_context_fields'] == 54
assert totals['characters_read'] == 12695 and totals['utf8_bytes_read'] == 27402
validation = {'schema': 'hadith-bank-manual-source-review-validation-v1', 'result': 'PASS',
    'source_commit': COMMIT, 'review_batch': NAME, 'counts': dict(totals),
    'language_coverage': {k: dict(v) for k, v in coverage.items()},
    'source_only_ids': ['deenhindi-muslim:' + n for n in sorted(SOURCE_ONLY, key=int)],
    'actual_reading_scope': '36 complete own fields:18 Hindi and18 Urdu;12,695 characters/27,402 UTF8 bytes.36 admitted;0 fully read context-only;54 unread sibling fields. Parent registration does not imply that all languages were reviewed.',
    'abbreviated_finite_fragment_and_question_voices_remain_qualified': True,
    'local_source_reverification': local_source_validation,
    'all_source_only_nonempty_fields_completely_read': True, 'raw_parsed_pairs_reopened_and_reparsed': 18,
    'source_fields_modified': 0, 'source_metadata_modified': 0, 'source_identity_merges': 0,
    'canonical_identity_asserted': False, 'independent_pro_qc': 'not_performed',
    'source_http_requests': 0, 'github_writes': 0, 'native_SourceReviews_apply_finish': 'PASS',
    'active_ledger_path': ACTIVE.as_posix(), 'active_ledger_sha256': sha(active_data),
    'source_ledger_path': baseline_path.as_posix(), 'source_ledger_sha256': sha(baseline_data),
    'source_ledger_uncompressed_sha256': sha(source_bytes), 'source_first_receipt_sha256': sha(reading_receipt),
    'code_inputs': {name: sha(Path(module.__file__).read_bytes()) for name, module in
                    [('import_deenhindi', importer), ('web_source_reviews', sys.modules['web_source_reviews']),
                     ('web_commentary_quotes', sys.modules['web_commentary_quotes'])]}}
put(Path('reports/web-source-resolution-20261113') / (NAME + '-validation.json'), enc(validation))
(ROOT / 'validation-v1.json').write_bytes(enc(validation))
(ROOT / 'boundary-view-v1.json').write_bytes(enc(boundary_view))
(ROOT / 'derived-preview-v1.jsonl.gz').write_bytes(gzip.compress(importer.rows_bytes(derived), mtime=0))
manifest = {'schema': 'hadith-bank-source-review-delivery-v1', 'source_commit': COMMIT,
    'result': 'PASS', 'review_batch': NAME, 'active_ledger_path': ACTIVE.as_posix(),
    'active_ledger_sha256': sha(active_data),
    'expected_delta': {'registered': 18, 'held': -18, 'source_only': 0,
                       'admitted_hindi_fields': 18, 'admitted_urdu_fields': 18,
                       'admitted_arabic_fields': 0, 'admitted_english_fields': 0,
                       'admitted_roman_urdu_fields': 0},
    'files': [{'path': p.relative_to(OUT).as_posix(), 'local_path': str(p), 'bytes': p.stat().st_size,
               'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]}
portable = {k: copy.deepcopy(v) for k, v in manifest.items() if k != 'files'}
portable['schema'] = 'hadith-bank-source-review-portable-manifest-v1'
portable['files'] = [{k: v for k, v in f.items() if k != 'local_path'} for f in manifest['files']]
portable_path = put(EVIDENCE / 'portable-manifest.json', enc(portable))
manifest['files'].append({'path': portable_path.relative_to(OUT).as_posix(), 'local_path': str(portable_path),
                         'bytes': portable_path.stat().st_size, 'sha256': sha(portable_path.read_bytes())})
(ROOT / 'delivery-manifest-v1.json').write_bytes(enc(manifest))
print(json.dumps({'result': 'PASS', 'counts': dict(totals), 'active_sha256': sha(active_data),
                  'manifest_sha256': sha(enc(manifest)), 'files': len(manifest['files']),
                  'bytes': sum(f['bytes'] for f in manifest['files'])}, indent=2))
