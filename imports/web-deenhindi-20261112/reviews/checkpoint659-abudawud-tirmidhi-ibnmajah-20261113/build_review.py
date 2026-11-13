#!/usr/bin/env python3
"""Compile explicit complete-field readings against saved source bytes; no fetching."""
from __future__ import annotations
import argparse
import collections
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
COHORT = 'checkpoint659-abudawud-tirmidhi-ibnmajah-20261113'
CHECKPOINT = '659f21c8a5bbedd3f85aa4c579f4e3b1f215dfc9'
INPUT_MANIFEST_SHA256 = '7ccfc0b69bc848ad22685be6a9ddf3dc89f20cbd4881994d742f1e1d3bbd913c'
REVIEW_ENGINE_SHA256 = 'cc253d0d89d839f79a99e5209824b953fa6ac21be80fdb898a130025cbc7114b'
REVIEWS = 'imports/web-deenhindi-20261112/reviews'
EVIDENCE = REVIEWS + '/' + COHORT
ACTIVE = REVIEWS + '/source-review-' + COHORT + '.json.gz'
BASELINE = EVIDENCE + '/source-baseline.jsonl.gz'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def put(root, relative, data):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {'path': relative, 'bytes': len(data), 'sha256': sha(data)}


def safe(root, relative):
    p = Path(relative)
    assert not p.is_absolute() and '..' not in p.parts and '\\' not in relative
    result = root / p
    assert result.is_file() and result.resolve().is_relative_to(root.resolve())
    assert not any(q.is_symlink() for q in [result, *result.parents] if q.is_relative_to(root))
    return result


def compile_field(key, language, instruction, text, field_name):
    assert isinstance(text, str) and text.strip()
    result = {'language_version_id': 'deenhindi-' + key + ':' + language,
        'language': language, 'source_field': field_name, 'action': instruction['action'],
        'reviewed': True, 'chars_reviewed': len(text), 'bytes_reviewed': len(text.encode()),
        'text_sha256': sha(text.encode()), 'reason': instruction['reason'],
        'review_method': 'manual_full_field_reading_of_saved_source',
        'review_scope': 'The complete own-language field was read for attribution and exact boundaries; this is not independent Pro certification.'}
    for name in ('report_type', 'speaker'):
        if name in instruction:
            result[name] = instruction[name]
    if instruction['action'] == 'whole':
        assert not instruction.get('omit_source_context')
        result['spans'] = [{'start': 0, 'end': len(text), 'sha256': sha(text.encode())}]
        return result
    if instruction['action'] in ('source_context', 'source_context_only'):
        result['spans'] = []
        return result
    assert instruction['action'] in ('excerpt', 'excerpts')
    base_spans = []
    for index, selection in enumerate(instruction['spans']):
        for marker in (selection['from'], selection['to']):
            assert marker is None or text.count(marker) == 1, ('ambiguous boundary', key, language, marker)
        start = 0 if selection['from'] is None else text.index(selection['from'])
        end = len(text) if selection['to'] is None else text.index(selection['to'], start)
        assert 0 <= start < end <= len(text)
        base_spans.append({'start': start, 'end': end,
            'component_id': selection.get('component_id', 'passage-' + str(index + 1)),
            'report_type': selection['report_type'], 'speaker': selection['speaker'],
            **({'source_report_family_id': selection['source_report_family_id']}
               if 'source_report_family_id' in selection else {})})
    omissions = []
    for omission in instruction.get('omit_source_context', []):
        marker = omission['text']
        assert marker and text.count(marker) == omission['expected_count']
        offset = 0
        for _ in range(omission['expected_count']):
            start = text.index(marker, offset)
            end = start + len(marker)
            assert sum(s['start'] <= start < end <= s['end'] for s in base_spans) == 1
            omissions.append((start, end))
            offset = end
    omissions.sort()
    assert all(left[1] <= right[0] for left, right in zip(omissions, omissions[1:]))
    spans = []
    for base in base_spans:
        cuts = [pair for pair in omissions if base['start'] <= pair[0] < pair[1] <= base['end']]
        cursor = base['start']
        for start, end in cuts + [(base['end'], base['end'])]:
            if cursor < start and text[cursor:start].strip():
                spans.append({**base, 'start': cursor, 'end': start,
                              'sha256': sha(text[cursor:start].encode())})
            cursor = end
    assert spans and all(a['end'] <= b['start'] for a, b in zip(spans, spans[1:]))
    result['spans'] = spans
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Verified659f held-evidence directory')
    parser.add_argument('--engine-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'publish')
    args = parser.parse_args()
    input_root, output = args.input.resolve(), args.output.resolve()
    sys.path.insert(0, str(args.engine_dir.resolve()))
    import import_deenhindi as importer
    import web_source_reviews as review_module
    import web_commentary_quotes as commentary_module
    input_bytes = (input_root / 'held-source-records.jsonl').read_bytes()
    input_manifest_bytes = (input_root / 'evidence-manifest.json').read_bytes()
    assert sha(input_manifest_bytes) == INPUT_MANIFEST_SHA256
    artifact_evidence = json.loads(input_manifest_bytes)
    assert artifact_evidence['source_commit'] == CHECKPOINT and artifact_evidence['status'] == 'PASS'
    assert artifact_evidence['source_count'] == 94 and artifact_evidence['source_rows_sha256'] == sha(input_bytes)
    assert artifact_evidence['parser_sha256'] == sha(Path(importer.__file__).read_bytes())
    assert sha(Path(review_module.__file__).read_bytes() + Path(commentary_module.__file__).read_bytes()) == REVIEW_ENGINE_SHA256
    all_rows = [json.loads(line) for line in input_bytes.decode().splitlines() if line.strip()]
    rows = sorted([r for r in all_rows if r['collection'] in ('abudawud', 'tirmidhi', 'ibnmajah')],
                  key=lambda r: (r['collection'], int(r['number'])))
    assert len(rows) == 38
    sources = {r['collection'] + ':' + r['number']: r for r in rows}
    assert len(sources) == len(rows)
    state_entries = json.loads((input_root / 'held-state-entries.json').read_bytes())
    notes, manual_receipts = {}, []
    for path in sorted(ROOT.glob('manual-*.json')):
        data = path.read_bytes()
        manual_receipts.append(put(output, EVIDENCE + '/' + path.name, data))
        for record in json.loads(data)['records']:
            key = record['key']
            assert key in sources and key not in notes
            assert {'hi', 'ur'} <= set(record['fields'])
            assert record['decision'] in ('register', 'exclude')
            notes[key] = record
    assert set(notes) == set(sources)
    historical_notes = json.loads(gzip.decompress((ROOT / 'before-source-apparatus-manual-notes.json.gz').read_bytes()))
    corrections = json.loads((ROOT / 'independent-review-corrections.json').read_bytes())
    assert corrections['corrected_language_fields'] == 16
    for item in corrections['changes']:
        key = item['id'].removeprefix('deenhindi-')
        assert historical_notes[key]['fields'][item['language']] == item['after']
        assert sha(sources[key]['source_record'][item['source_field']].encode()) == item['source_text_sha256']
    correction_receipt = put(output, EVIDENCE + '/independent-review-corrections.json',
                             (ROOT / 'independent-review-corrections.json').read_bytes())
    from verify_apparatus import verify as verify_apparatus
    apparatus_receipts = verify_apparatus(ROOT, output, EVIDENCE, notes, sources, compile_field, put, enc)
    input_receipt = put(output, EVIDENCE + '/input-evidence-manifest.json', input_manifest_bytes)
    selected_state_receipt = put(output, EVIDENCE + '/selected-state-entries.json',
                                 enc({key: state_entries[key] for key in sources}))
    baseline_raw = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in rows).encode()
    baseline = put(output, BASELINE, gzip.compress(baseline_raw, mtime=0))
    raw_checks, decisions = [], []
    totals = collections.Counter()
    books, languages = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for key, saved in sources.items():
        snapshot, entry = saved['snapshot'], state_entries[key]
        assert entry['collection'] == saved['collection'] and entry['number'] == saved['number']
        assert entry['parsed']['path'] == saved['parsed_path']
        source_hash = sha(importer.json_bytes(saved['source_record']))
        assert source_hash == artifact_evidence['source_record_sha256'][key]
        verified = []
        for relative in (snapshot['path'], saved['parsed_path']):
            data = safe(input_root / 'sources', relative).read_bytes()
            expected = artifact_evidence['files'][relative]
            assert expected['source_commit'] == CHECKPOINT
            assert len(data) == expected['bytes'] and sha(data) == expected['sha256']
            assert git_blob(data) == expected['git_blob_sha1']
            uncompressed = gzip.decompress(data)
            assert len(uncompressed) == expected['uncompressed_bytes']
            assert sha(uncompressed) == expected['uncompressed_sha256']
            verified.append({'path': relative, **expected})
        stored_raw = safe(input_root / 'sources', snapshot['path']).read_bytes()
        assert sha(stored_raw) == snapshot['stored_sha256'] and len(stored_raw) == snapshot['stored_bytes']
        raw = gzip.decompress(stored_raw)
        assert sha(raw) == snapshot['sha256'] and len(raw) == snapshot['bytes']
        parsed_stored = safe(input_root / 'sources', saved['parsed_path']).read_bytes()
        parsed_bytes = gzip.decompress(parsed_stored)
        assert sha(parsed_stored) == entry['parsed']['stored_sha256']
        assert sha(parsed_bytes) == entry['parsed']['sha256']
        assert Path(saved['parsed_path']).name == sha(parsed_bytes) + '.json.gz'
        expected_parsed = {k: saved[k] for k in ('schema', 'collection', 'number', 'snapshot', 'source_reference_verbatim', 'source_record')}
        expected_parsed['classification'] = saved['intake_classification']
        assert json.loads(parsed_bytes) == expected_parsed and parsed_bytes == importer.json_bytes(expected_parsed)
        actual_object, actual_reference = importer.parse_record(raw, saved['collection'], saved['number'])
        assert actual_object == saved['source_record'] and actual_reference == saved['source_reference_verbatim']
        field_reviews = [compile_field(key, lang, instruction,
            saved['source_record'][importer.LANGUAGE_FIELDS[lang]], importer.LANGUAGE_FIELDS[lang])
            for lang, instruction in notes[key]['fields'].items()]
        action = notes[key]['decision']
        if action == 'exclude':
            assert not any(f['spans'] for f in field_reviews)
            assert set(notes[key]['fields']) == {lang for lang, field in importer.LANGUAGE_FIELDS.items()
                                                if saved['source_record'].get(field)}
        else:
            assert any(f['spans'] for f in field_reviews)
        decisions.append({'id': 'deenhindi-' + key, 'decision': action,
            'reason': notes[key].get('reason', 'Each admitted language field was read independently and exact report boundaries selected; unread sibling fields remain complete source context.'),
            'source_record_sha256': source_hash, 'source_snapshot_sha256': snapshot['sha256'],
            'source_record_url': snapshot['url'], 'source_parsed_path': saved['parsed_path'],
            'source_parsed_sha256': sha(parsed_bytes), 'source_reference_verbatim': saved['source_reference_verbatim'],
            'field_reviews': field_reviews})
        raw_checks.append({'id': 'deenhindi-' + key, 'source_record_sha256': source_hash,
            'raw_sha256': sha(raw), 'raw_bytes': len(raw), 'parsed_sha256': sha(parsed_bytes),
            'parsed_bytes': len(parsed_bytes), 'files': verified, 'exact_current_parser_object_and_reference': True})
        totals.update(raw_responses_reopened_and_reparsed=1, parsed_source_files_reopened=1,
                      raw_response_bytes=len(raw), parsed_source_bytes=len(parsed_bytes))
    document = {'schema': 'hadith-bank-web-source-review-v1', 'site': 'deenhindi',
        'review_scope': 'Individual complete Hindi and Urdu readings in38 newly held source occurrences, plus explicitly documented secondary readings. Actual speakers, separate report components and all context are preserved.',
        'source_checkpoint': CHECKPOINT, 'source_ledger_path': BASELINE,
        'source_ledger_sha256': baseline['sha256'], 'source_ledger_uncompressed_sha256': sha(baseline_raw),
        'manual_decision_files': manual_receipts, 'independent_boundary_review': correction_receipt,
        'source_apparatus_amendment_v2': apparatus_receipts,
        'independent_pro_qc': 'not_performed', 'independent_pro_qc_performed': False,
        'new_translation_created': False, 'records': decisions}
    active_receipt = put(output, ACTIVE, gzip.compress(importer.json_bytes(document), mtime=0))
    native = review_module.SourceReviews(output, 'deenhindi')
    assert set(native.decisions) == {'deenhindi-' + key for key in sources}
    partitions = []
    for key, saved in sources.items():
        saved_before = copy.deepcopy(saved)
        original = importer.canonical_record(saved)
        original_before = copy.deepcopy(original)
        after, action = native.apply(original, saved=saved)
        assert saved == saved_before and original == original_before
        assert action == notes[key]['decision']
        book = saved['collection']
        fields = {f['language_version_id']: f for f in native.decisions[after['id']][0]['field_reviews']}
        for name in set(original) - {'language_versions', 'text', 'content_kind', 'review', 'report_types', 'extraction'}:
            assert after[name] == original[name], ('metadata', key, name)
        for name in original['extraction']:
            if name != 'is_excerpt':
                assert after['extraction'][name] == original['extraction'][name]
        assert after['review']['independent_pro_qc'] == 'not_performed'
        assert after['review']['certified_release_eligible'] is False and after['number']['canonical'] is None
        selected = {}
        for old, new in zip(original['language_versions'], after['language_versions'], strict=True):
            language, text = old['language'], old['text']
            field = fields.get(old['id'])
            for name in set(old) - {'text', 'scope', 'quotation_status', 'source', 'comments'}:
                assert new[name] == old[name], ('language metadata', key, language, name)
            for name in old['source']:
                assert new['source'][name] == old['source'][name]
            pieces = []
            if field:
                assert field['chars_reviewed'] == len(text) and field['bytes_reviewed'] == len(text.encode())
                assert field['text_sha256'] == sha(text.encode())
                for counter in (totals, books[book], languages[language]):
                    counter.update(complete_fields_read=1, characters_read=len(text), utf8_bytes_read=len(text.encode()))
                if field['spans']:
                    positions = [[s['start'], s['end']] for s in field['spans']]
                    assert new['source']['text_spans']['quotation_spans'] == positions
                    assert new['text'] == ''.join(text[a:b] for a, b in positions)
                    selected[language] = new['text']
                    for span in field['spans']:
                        a, b = span['start'], span['end']
                        assert sha(text[a:b].encode()) == span['sha256']
                        pieces.append((a, b, text[a:b], 'quotation'))
                    for counter in (totals, books[book], languages[language]):
                        counter.update(admitted_language_fields=1, quotation_spans=len(field['spans']))
                    if key == 'abudawud:2121':
                        assert new['source']['source_report_family_count'] == 2
                        assert new['source']['source_report_count'] == 2
                        assert new['quotation_status'] == 'disjoint_source_spans'
                else:
                    assert new['text'] is None and new['source']['manual_review']['field_reviewed'] is True
                    for counter in (totals, books[book], languages[language]):
                        counter['read_context_fields'] += 1
            else:
                assert new['text'] is None and new['source']['manual_review']['field_reviewed'] is False
                for counter in (totals, books[book], languages[language]):
                    counter['unread_nonempty_context_fields'] += 1
            for comment in new['comments']:
                assert comment['scope'] == 'source_context_not_narration'
                a, b = comment['source_span']
                assert comment['text'] == text[a:b] and comment['source_text_sha256'] == sha(text[a:b].encode())
                pieces.append((a, b, comment['text'], 'context'))
            cursor = 0
            for a, b, body, kind in sorted(pieces):
                assert a == cursor and b > a and body == text[a:b]
                cursor = b
            assert cursor == len(text) and ''.join(p[2] for p in sorted(pieces)) == text
            partitions.append({'id': old['id'], 'source_field': old['source']['source_field'],
                'source_text_sha256': sha(text.encode()), 'source_chars': len(text), 'read': bool(field),
                'parts': [{'start': a, 'end': b, 'sha256': sha(body.encode()), 'role': kind}
                          for a, b, body, kind in sorted(pieces)]})
            for counter in (totals, books[book], languages[language]):
                counter.update(exact_complete_field_partitions=1, nonempty_source_fields=1, source_language_slots=1)
        for lang, field_name in importer.LANGUAGE_FIELDS.items():
            value = saved['source_record'].get(field_name)
            if value is None or value == '':
                assert not any(v['language'] == lang for v in original['language_versions'])
                partitions.append({'id': original['id'] + ':' + lang, 'source_field': field_name,
                    'source_original_state': value, 'source_chars': 0, 'read': False, 'parts': []})
                for counter in (totals, books[book], languages[lang]):
                    counter.update(empty_source_fields_preserved=1, source_language_slots=1)
        if action == 'register':
            assert {'hi', 'ur'} <= set(selected)
            assert after['text'] == {'arabic': selected.get('ar'), 'translation': selected['hi']}
        else:
            assert not selected and after['text'] == original['text']
        assert after['review']['source_bound_review']['approved_language_fields'] == len(selected)
        totals['source_metadata_preservation_checks'] += 1
        for counter in (totals, books[book]):
            counter['source_occurrences'] += 1
            counter[action] += 1
    native.finish()
    assert totals['source_occurrences'] == 38 and totals['register'] == 36 and totals['exclude'] == 2
    assert totals['complete_fields_read'] == 82 and totals['characters_read'] == 34972
    assert totals['admitted_language_fields'] == 74 and totals['read_context_fields'] == 8
    assert totals['exact_complete_field_partitions'] == 188 and totals['source_language_slots'] == 190
    assert totals['unread_nonempty_context_fields'] == 106 and totals['empty_source_fields_preserved'] == 2
    evidence = {'schema': 'hadith-bank-saved-checkpoint-review-evidence-v1', 'result': 'passed',
        'source_checkpoint': CHECKPOINT, 'source_worker_run_id': artifact_evidence['worker_run_id'],
        'input_evidence_manifest': input_receipt, 'selected_state_entries': selected_state_receipt,
        'input_files': [{'path': name, 'bytes': (input_root/name).stat().st_size,
                         'sha256': sha((input_root/name).read_bytes())} for name in
                        ('held-source-records.jsonl', 'held-state-entries.json', 'evidence-manifest.json')],
        'source_http_requests': 0, 'github_writes': 0, 'records': raw_checks}
    put(output, EVIDENCE + '/source-evidence.json', enc(evidence))
    put(output, EVIDENCE + '/field-partitions.json.gz', gzip.compress(enc(partitions), mtime=0))
    coverage = {'schema': 'hadith-bank-checkpoint-review-validation-v1', 'result': 'passed',
        'source_checkpoint': CHECKPOINT, 'active_review': active_receipt, 'source_baseline': baseline,
        'totals': dict(totals), 'by_book': {k: dict(v) for k, v in sorted(books.items())},
        'by_language': {k: dict(v) for k, v in sorted(languages.items())},
        'hold_decisions': 0, 'source_only_decisions': 2, 'unprocessed_decisions': 0,
        'source_apparatus_amendment_v2': {'exact_cuts': 24, 'changed_fields': 18,
            'characters_moved_to_context': 178, 'utf8_bytes_moved_to_context': 329,
            'whitespace_only_spans_removed': 0, 'evidence': apparatus_receipts},
        'independent_complete_reading': {'reviewer': 'root agent', 'nonempty_fields': 82,
            'empty_fields_inspected': 2, 'corrected_fields': 16, 'correction_receipt': correction_receipt,
            'formal_independent_pro_certification': False},
        'checks': {'exact_unique_source_and_review_ids': True, 'source_reviews_apply_and_finish': True,
            'raw_stored_and_uncompressed_hashes': True, 'parsed_stored_and_uncompressed_hashes': True,
            'all76_source_git_blob_hashes': True, 'current_parser_exact_source_object_and_reference': True,
            'all_source_metadata_preserved': True, 'source_and_canonical_inputs_not_mutated': True,
            'exact_full_field_partitions': True, 'unread_siblings_retained_context': True,
            'all_nonempty_exclusion_fields_read': True, 'both_actual_empty_fields_preserved': True,
            'explicit_independent_corrections_applied': True, 'two2121_report_families_preserved': True,
            'only24_explicit_apparatus_cuts_applied': True, 'before_active_and_manual_history_preserved': True,
            'no_engine_changes': True, 'no_source_http_requests': True, 'no_github_writes': True},
        'engine_sha256': {Path(m.__file__).name: sha(Path(m.__file__).read_bytes()) for m in
                          (importer, review_module, commentary_module)},
        'limits': 'Local exact-source review replay. Shared full-repository export, registry validation, reader/browser build and deployment remain separate CI gates.',
        'independent_pro_qc': 'not_performed', 'new_translation_created': False}
    put(output, EVIDENCE + '/validation.json', enc(coverage))
    put(output, EVIDENCE + '/build_review.py', Path(__file__).read_bytes())
    print(json.dumps({'result': 'passed', 'totals': dict(totals), 'by_book': coverage['by_book'],
                      'active_review': active_receipt, 'source_baseline': baseline}, ensure_ascii=False))


if __name__ == '__main__':
    main()
