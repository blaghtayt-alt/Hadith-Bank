"""Validate a narrow, source-preserving primary Hadisuz323 review candidate.

All inputs are saved GitHub files at one pinned commit. No network is used.
The candidate is for an independent reading before any publication decision.
"""
from __future__ import annotations
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parent
PINNED = ROOT / 'input/pinned'
sys.path.insert(0, str(PINNED / 'scripts'))
import import_hadisuz as importer
from web_source_reviews import SourceReviews, canonical_hash

COMMIT = 'cdb66dbcf9ee781fe232219724d05033a0fcab13'
IDENTITY = 'hadisuz:tirmidhi:323'
BASE = 'imports/web-hadisuz-20261112'
ACTIVE = BASE + '/reviews/source-review-hadisuz-held-20261113.json.gz'
ORIGINALS = BASE + '/reviews/original-held-records-20261113.jsonl.gz'
EVIDENCE = BASE + '/reviews/hadisuz323-primary-review-20261113'
REPORT = 'reports/web-source-resolution-20261113/hadisuz323-primary-review'
PUBLISH = ROOT / 'publish'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def gitsha(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

def jb(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def loadgz(p):
    return json.loads(gzip.decompress(p.read_bytes()))

def put(path, data):
    p = PUBLISH / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p

def descriptor_checked(descriptor):
    p = PINNED / descriptor['path']
    stored = p.read_bytes()
    assert sha(stored) == descriptor['stored_sha256']
    if 'size_bytes' in descriptor:
        assert len(stored) == descriptor['size_bytes']
    raw = gzip.decompress(stored)
    assert sha(raw) == descriptor['sha256']
    if 'bytes' in descriptor:
        assert len(raw) == descriptor['bytes']
    return raw

def at(x, path):
    for part in path:
        x = x[part]
    return x

def copy_to(root, relative):
    p = root / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PINNED / relative, p)

def main():
    retrieved = json.loads((ROOT / 'input/github-retrieval-metadata.json').read_text())['files']
    retrieved += json.loads((ROOT / 'input/github-retrieval-added-metadata-final.json').read_text())
    retrieved += json.loads((ROOT / 'input/github-retrieval-legacy-ol-metadata.json').read_text())
    assert len({f['path'] for f in retrieved}) == len(retrieved)
    file_receipts = []
    for item in retrieved:
        data = (PINNED / item['path']).read_bytes()
        assert gitsha(data) == item['git_blob_sha1'], item['path']
        file_receipts.append({**item, 'bytes': len(data), 'sha256': sha(data)})

    state = json.loads((PINNED / BASE / 'checkpoint.json').read_text())
    progress = json.loads((PINNED / BASE / 'progress.json').read_text())
    entry = state['entries']['323']
    raw = descriptor_checked(entry['snapshot'])
    parsed = json.loads(descriptor_checked(entry))
    assert importer.parse_detail(raw, entry['url']) == parsed
    tree = importer.source_tree(raw)
    paragraphs, unexpected = importer.content_paragraphs(tree)
    assert not unexpected and len(paragraphs) == 2
    assert [importer.plain(p, True) for p in paragraphs] == parsed['body_paragraphs']

    credits = [{'url': c['url'], 'snapshot_path': c['snapshot']['path'],
                'snapshot_sha256': c['snapshot']['sha256'], 'scope': c['scope']}
               for c in state['collection_credits'].values()]
    credit_statements = []
    for c in state['collection_credits'].values():
        credit_statements.extend(importer.collection_credit_statements(
            descriptor_checked(c['snapshot']), c['url'], c['snapshot']))
    row = importer.record_from(parsed, entry['snapshot'], credits, credit_statements)
    original_bytes = (PINNED / ORIGINALS).read_bytes()
    original_rows = [json.loads(line) for line in gzip.decompress(original_bytes).splitlines()]
    original_by_id = {x['id']: x for x in original_rows}
    assert len(original_rows) == len(original_by_id) == 37
    assert row == original_by_id[IDENTITY]

    old_bytes = (PINNED / ACTIVE).read_bytes()
    old = loadgz(PINNED / ACTIVE)
    assert old['source_ledger_sha256'] == sha(original_bytes)
    old_map = {d['occurrence_id']: d for d in old['decisions']}
    assert len(old_map) == len(old['decisions']) == 37
    assert canonical_hash(row) == old_map[IDENTITY]['baseline_record_sha256']

    before_engine = SourceReviews(PINNED, 'hadisuz')
    before_outputs = {}
    for r in original_rows:
        before_outputs[r['id']] = before_engine.apply(copy.deepcopy(r))[0]
    before_engine.finish()
    current_held = [json.loads(line) for line in gzip.decompress(
        (PINNED / BASE / 'held-records.jsonl.gz').read_bytes()).splitlines()]
    assert len(current_held) == 1 and current_held[0]['id'] == IDENTITY
    assert before_outputs[IDENTITY] == current_held[0]

    candidate = copy.deepcopy(old)
    target = next(d for d in candidate['decisions'] if d['occurrence_id'] == IDENTITY)
    primary = target['fields'][0]
    text = at(row, primary['field_path'])
    commentary = at(row, target['fields'][1]['field_path'])
    assert len(text) == 173 and len(commentary) == 214
    reason = (
        'The complete source field explicitly reports Amr ibn al-Harith ibn Mustaliq saying '
        'that it used to be said, followed by a finite saying. Under the expanded numbered '
        'reports-and-sayings policy, this is an attributed transmission of an anonymous saying. '
        'The ultimate speaker, the relayer\'s biographical class and any Prophetic attribution '
        'remain unestablished; the passive wording stays visible. The following explanation '
        'remains separate source commentary. No missing wording or canonical identity is supplied.')
    speaker = ('Amr ibn al-Harith ibn Mustaliq relaying an unnamed saying; '
               'the ultimate speaker is not supplied and no Prophetic attribution is asserted')
    primary.update(decision='whole', reason=reason,
                   report_type='transmitted_anonymous_saying', speaker=speaker,
                   selected_spans=[{'start': 0, 'end': len(text), 'sha256': sha(text.encode()),
                       'component_id': 'amr-transmitted-anonymous-saying',
                       'report_type': 'transmitted_anonymous_saying', 'speaker': speaker,
                       'source_report_family_id': 'hadisuz323-own-transmitted-saying',
                       'ultimate_speaker': {'name': None, 'status': 'not_supplied_by_source',
                                            'prophetic_attribution': 'not_established'},
                       'reason': reason}])
    target['overalldecision'] = 'register'
    target['reason'] = reason
    target['review_refinement'] = {
        'reviewer': {'kind': 'AI_assistant', 'model': 'GPT-6 Astra Pro'},
        'status': 'primary_semantic_review_candidate_pending_independent_reading',
        'source_commit': COMMIT, 'previous_decision': 'hold',
        'prior_review_path': EVIDENCE + '/previous-active-review.json.gz',
        'prior_review_sha256': sha(old_bytes),
        'previous_reason_retained_in_full_prior_ledger': True,
        'basis': 'Finite anonymous saying is itself transmitted by the source-named relayer; no ultimate speaker is invented.',
        'independent_pro_qc': 'not_performed', 'human_review': 'not_performed'}
    candidate['supplemental_review'] = {
        'occurrence_ids': [IDENTITY], 'source_commit': COMMIT,
        'kind': 'narrow_primary_review_refinement',
        'prior_active_sha256': sha(old_bytes),
        'all_other_36_decisions_unchanged': True,
        'historical_top_level_reviewer_and_source_commit_preserved': True,
        'independent_semantic_reading': 'pending_separate_receipt',
        'independent_pro_qc': 'not_performed'}
    new_map = {d['occurrence_id']: d for d in candidate['decisions']}
    assert set(new_map) == set(old_map)
    assert all(new_map[k] == old_map[k] for k in old_map if k != IDENTITY)
    assert target['fields'][1] == old_map[IDENTITY]['fields'][1]
    for key in old_map[IDENTITY]:
        if key not in ('overalldecision', 'reason', 'fields'):
            assert target[key] == old_map[IDENTITY][key]

    new_bytes = gzip.compress(jb(candidate), mtime=0)
    put(ACTIVE, new_bytes)
    put(EVIDENCE + '/previous-active-review.json.gz', old_bytes)
    put(EVIDENCE + '/source-baseline323.json', jb(row))
    put(EVIDENCE + '/previous-held323.json', jb(current_held[0]))
    put(EVIDENCE + '/source-first-reading-notes.json',
        (ROOT / 'independent-primary-reading-notes.json').read_bytes())
    full_reading = {
        'schema': 'hadith-bank-full-own-field-reading-evidence-v1',
        'occurrence_id': IDENTITY, 'source_commit': COMMIT,
        'source_snapshot': entry['snapshot'], 'parsed_source': entry,
        'fields': [{'field_path': f['field_path'], 'language': f['language'],
                    'text': at(row, f['field_path']),
                    'text_sha256': sha(at(row, f['field_path']).encode()),
                    'characters': len(at(row, f['field_path'])),
                    'utf8_bytes': len(at(row, f['field_path']).encode()),
                    'complete_field_read': True,
                    'selected_ranges': [[s['start'], s['end']] for s in f['selected_spans']],
                    'decision': f['decision'], 'reason': f['reason']}
                   for f in target['fields']],
        'heading': {'text': row['title'], 'sha256': sha(row['title'].encode()),
                    'complete_heading_read': True, 'decision': 'source_metadata_only'},
        'body_fields_read': 2, 'body_characters_read': 387, 'body_utf8_bytes_read': 710,
        'admitted_language_fields': 1, 'reviewed_context_fields': 1,
        'absent_source_languages': ['Arabic', 'English'],
        'unread_body_fields': 0, 'canonical_number_inferred': False,
        'source_site_requests': 0, 'independent_pro_qc': 'not_performed'}
    put(EVIDENCE + '/full-field-reading-and-boundaries.json', jb(full_reading))

    validation_root = ROOT / 'validation/full37'
    for item in retrieved:
        if '/reviews/' in item['path'] or '/snapshots/' in item['path']:
            copy_to(validation_root, item['path'])
    active_path = validation_root / ACTIVE
    active_path.write_bytes(new_bytes)
    engine = SourceReviews(validation_root, 'hadisuz')
    counts = {'register': 0, 'hold': 0, 'exclude': 0}
    partitions = 0
    metadata_checks = 0
    for original in original_rows:
        decision = new_map[original['id']]
        output, action = engine.apply(copy.deepcopy(original))
        counts[action] += 1
        for key in ('id', 'language', 'source_language_code', 'book_key', 'edition', 'title',
                    'classification', 'source', 'number', 'references', 'narrator', 'translator',
                    'ai_translation', 'translation_provenance', 'commentary', 'footnotes',
                    'grading', 'source_headings', 'topic_tags', 'related_versions', 'rights',
                    'source_locator', 'page'):
            assert output[key] == original[key], (original['id'], key)
            metadata_checks += 1
        for f in decision['fields']:
            full = at(original, f['field_path'])
            assert f['text_sha256'] == sha(full.encode())
            assert f['chars_reviewed'] == len(full) and f['bytes_reviewed'] == len(full.encode())
            if len(f['field_path']) == 5:
                assert at(output, f['field_path']) == full
            else:
                vi = f['field_path'][1]
                v = output['language_versions'][vi]
                spans = [[s['start'], s['end']] for s in f['selected_spans']]
                if spans:
                    assert v['text'] == ''.join(full[a:b] for a,b in spans)
                    intervals = sorted(spans + v['source']['text_spans']['notes'])
                    cursor = 0
                    for a,b in intervals:
                        assert a == cursor
                        cursor = b
                    assert cursor == len(full)
                    assert ''.join(full[a:b] for a,b in intervals) == full
                else:
                    assert v['text'] is None
                    assert any(c.get('source_span') == [0,len(full)] and c['text'] == full for c in v['comments'])
            partitions += 1
        if original['id'] == IDENTITY:
            assert output['language_versions'][0]['text'] == text
            assert output['language_versions'][0]['comments'][0]['text'] == commentary
            assert 'ultimate speaker is not supplied' in output['language_versions'][0]['source']['report_classification_note']
            assert output['text']['arabic'] is None
            assert output['number']['canonical'] is None
            assert output['narrator']['name'] is None
            put(EVIDENCE + '/candidate-native323.json', jb(output))
    engine.finish()
    assert counts == {'register': 36, 'hold': 0, 'exclude': 1}
    assert partitions == 169

    # Exercise the real exporter in a labelled one-entry fixture. It uses actual
    # saved raw/parsed bytes and real credits, but is not a full607-source export.
    export_root = ROOT / 'validation/one-entry-export'
    required = [entry['path'], entry['snapshot']['path']] + [
        c['snapshot']['path'] for c in state['collection_credits'].values()]
    for relative in required:
        copy_to(export_root, relative)
    single = copy.deepcopy(candidate)
    single['decisions'] = [target]
    single['source_ledger_path'] = BASE + '/reviews/fixture-source323.jsonl.gz'
    single_original = gzip.compress(importer.row_bytes(row), mtime=0)
    single['source_ledger_sha256'] = sha(single_original)
    er = export_root / BASE / 'reviews'
    er.mkdir(parents=True, exist_ok=True)
    (er / 'fixture-source323.jsonl.gz').write_bytes(single_original)
    (er / 'source-review-fixture323.json.gz').write_bytes(gzip.compress(jb(single), mtime=0))
    worker = importer.Importer(export_root, max_pages=1, max_seconds=30, delay=1)
    worker.state.update(entries={'323': copy.deepcopy(entry)},
        snapshots={x['url']: copy.deepcopy(x) for x in [entry['snapshot']] +
                   [c['snapshot'] for c in state['collection_credits'].values()]},
        collection_credits=copy.deepcopy(state['collection_credits']),
        part_assignments={}, tasks=[{'url': entry['url'], 'kind': 'detail', 'status': 'done', 'attempts': 1}])
    with mock.patch.object(worker.opener, 'open', side_effect=AssertionError('Offline exporter attempted HTTP')):
        exported = worker.export()
    assert exported['source_entries_obtained'] == exported['registered_source_occurrences'] == 1
    assert exported['classification_pending_hidden'] == exported['non_narration_source_entries'] == 0
    fixture_record = json.loads((export_root / 'materials' / importer.SLUG / 'records.jsonl').read_text())
    assert fixture_record['id'] == IDENTITY and fixture_record['text']['translation'] == text
    assert fixture_record['language_versions'][0]['comments'][0]['text'] == commentary

    provenance = {
        'schema': 'hadith-bank-pinned-github-source-verification-v1',
        'repository': 'blaghtayt-alt/Hadith-Bank', 'source_commit': COMMIT,
        'transport': 'GitHub connector fetch_file and fetch_blob only; no source-site request',
        'verified_files': file_receipts, 'verified_file_count': len(file_receipts),
        'source_occurrence_id': IDENTITY, 'source_entry_descriptor': entry,
        'raw_to_parsed_exact': True, 'current_record_from_exact_original_baseline': True,
        'current_held_exact_prior_native_review_output': True,
        'baseline_record_sha256': canonical_hash(row),
        'full_source_body_paragraphs': 2, 'unexpected_body_elements': [],
        'full_source_body_examined': True,
        'no_hidden_additional_body_or_ordered_list': True,
        'collection_credit_snapshot_hashes_verified': 2,
        'collection_credit_statements_reparsed': len(credit_statements),
        'collection_credit_per_translation_reassessment': False,
        'original_active_sha256': sha(old_bytes), 'original_baseline_sha256': sha(original_bytes),
        'no_source_mutation': True}
    put(REPORT + '/source-verification.json', jb(provenance))
    report = {
        'schema': 'hadith-bank-hadisuz323-primary-review-validation-v1', 'status': 'PASS',
        'candidate_semantic_status': 'primary_review_complete_independent_reading_pending',
        'source_commit': COMMIT, 'occurrence_id': IDENTITY,
        'active_path': ACTIVE, 'old_active_sha256': sha(old_bytes), 'new_active_sha256': sha(new_bytes),
        'existing_baseline_sha256': sha(original_bytes),
        'source_review_engine_sha256': engine.engine_sha256,
        'candidate': {'scope': 'one existing held occurrence; not a new source identity',
            'body_fields_completely_read': 2, 'characters_read': 387, 'utf8_bytes_read': 710,
            'heading_completely_read': True, 'admitted_fields': 1, 'reviewed_context_fields': 1,
            'selected_span': [0, 173], 'selected_utf8_bytes': 316,
            'commentary_retained_characters': 214, 'commentary_retained_utf8_bytes': 394,
            'actual_report_type': 'transmitted_anonymous_saying',
            'ultimate_speaker': None, 'prophetic_attribution': 'not_established',
            'canonical_number': None, 'source_local_id': '323'},
        'preservation': {'unchanged_other_parent_decisions': 36,
            'unchanged_other_field_decisions': 168, 'unchanged_target_comment_decision': True,
            'prior_active_bytes_preserved': True, 'source_baseline_bytes_unchanged': True,
            'source_raw_and_parsed_bytes_unchanged': True,
            'source_ids_references_grades_nulls_exact': True,
            'historical_classification_and_review_records_preserved': True},
        'native_validation': {'all37_apply_and_finish': 'PASS', 'counts': counts,
            'all_field_lossless_partitions': partitions, 'metadata_key_equalities': metadata_checks,
            'old_37_apply_finish': 'PASS', 'old323_equals_published_held': True,
            'one_entry_real_exporter_no_http': 'PASS',
            'one_entry_fixture_counts': {k:exported[k] for k in ('source_entries_obtained',
               'registered_source_occurrences','classification_pending_hidden','non_narration_source_entries')},
            'full607_source_export': 'not_run; exact current worker must rebuild after future publication'},
        'pinned_saved_counts': {k:progress[k] for k in ('source_entries_obtained','registered_source_occurrences',
            'classification_pending_hidden','non_narration_source_entries')},
        'conditional_projected_counts': {'source_entries_obtained':607,
            'registered_source_occurrences':606,'classification_pending_hidden':0,
            'non_narration_source_entries':1,
            'qualification':'Only if independently accepted and rebuilt by the current worker; not yet saved/published.'},
        'independent_pro_qc':'not_performed','human_review':'not_performed',
        'source_site_requests':0,'github_mutations':0,
        'remaining_gate':'Independent full source reading before publication; no unresolved technical blocker.'}
    put(REPORT + '/validation-report.json', jb(report))
    put(REPORT + '/reproduce-validation.py', Path(__file__).read_bytes())
    files=[]
    for path in sorted(PUBLISH.rglob('*')):
        if not path.is_file(): continue
        data=path.read_bytes(); files.append({'path':path.relative_to(PUBLISH).as_posix(),
            'local_path':str(path),'bytes':len(data),'sha256':sha(data),'git_blob_sha1':gitsha(data)})
    manifest={'schema':'hadith-bank-local-publication-handoff-v1','source_commit':COMMIT,
        'status':'primary_candidate_pending_independent_semantic_reading',
        'repository':'blaghtayt-alt/Hadith-Bank','files':files,
        'file_count':len(files),'total_bytes':sum(f['bytes'] for f in files),
        'expected_existing_files':[{ 'path':ACTIVE,'sha256':sha(old_bytes)},
                                   {'path':ORIGINALS,'sha256':sha(original_bytes)}],
        'source_occurrence_ids':[IDENTITY],'no_github_writes':True,
        'full_source_evidence_local_root':str(PINNED),
        'native_validation':report['native_validation'],
        'validation_report_sha256':sha(jb(report))}
    (ROOT/'delivery-manifest.json').write_bytes(jb(manifest))
    print(json.dumps({'status':'PASS','files':len(files),'bytes':manifest['total_bytes'],
        'manifest_sha256':sha(jb(manifest)),'active_sha256':sha(new_bytes),
        'native_counts':counts,'partitions':partitions,'candidate_body_chars':387,
        'candidate_status':manifest['status']}))

if __name__ == '__main__': main()
