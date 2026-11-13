#!/usr/bin/env python3
"""Replay the supplied phase 2 decisions without writing canonical repository data.

The default check uses exact saved source objects and receipt hashes. Use
--verify-raw only in a full checkout to additionally reopen every referenced
stored response and parsed source object. Existing unrelated review documents
are excluded from this isolated replay, so its finish() covers exactly this
manifest's cohort. The complete importer/export remains a separate full-repo
integration gate.
"""
from __future__ import annotations
import argparse
import collections
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

REPORTS = 'reports/web-source-resolution-20261113'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def enc(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def stream(path):
    data = path.read_bytes()
    data = gzip.decompress(data) if path.suffix == '.gz' else data
    text = data.decode()
    decoder = json.JSONDecoder()
    rows, offset = [], 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset < len(text):
            row, offset = decoder.raw_decode(text, offset)
            rows.append(row)
    return rows

def safe_file(root, relative):
    path = Path(relative)
    assert not path.is_absolute() and '..' not in path.parts and '\\' not in relative
    target = root / path
    assert target.is_file() and target.resolve().is_relative_to(root)
    assert not any(p.is_symlink() for p in [target, *target.parents] if p.is_relative_to(root))
    return target

def pairs_unique(items):
    result = {}
    for key, value in items:
        assert key not in result, ('duplicate JSON key', key)
        result[key] = value
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--engine-dir', type=Path)
    parser.add_argument('--verify-raw', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    engines = (args.engine_dir or root / 'scripts').resolve()
    sys.path.insert(0, str(engines))
    import import_deenhindi as importer
    import web_source_reviews as review_module
    import web_commentary_quotes as commentary_module
    manifest = json.loads((root / REPORTS / 'phase2-inputs.json').read_bytes(), object_pairs_hook=pairs_unique)
    totals = collections.Counter()
    by_book = collections.defaultdict(collections.Counter)
    by_cohort = collections.defaultdict(collections.Counter)
    by_language = collections.defaultdict(collections.Counter)
    types = collections.Counter()
    source_bindings = []
    excluded, held = [], []
    all_rows, owning_cohort = {}, {}
    input_checksums = []
    with tempfile.TemporaryDirectory(prefix='hadith-phase2-review-') as temp:
        isolated = Path(temp).resolve()
        for receipt in manifest['copy_receipts']:
            relative = receipt['repository_path']
            source = safe_file(root, relative)
            data = source.read_bytes()
            assert sha(data) == receipt['sha256'] and len(data) == receipt['size_bytes']
            target = isolated / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            input_checksums.append({'path': relative, 'sha256': sha(data), 'size_bytes': len(data),
                                    'supplied_sha256_verified': receipt['supplied_sha256_verified']})
        for cohort in manifest['cohorts']:
            rows = stream(safe_file(root, cohort['source_ledger_path']))
            assert len(rows) == cohort['source_occurrences']
            assert sha(safe_file(root, cohort['source_ledger_path']).read_bytes()) == cohort['source_ledger_sha256']
            assert sha(safe_file(root, cohort['review_path']).read_bytes()) == cohort['review_sha256']
            for saved in rows:
                oid = 'deenhindi-' + saved['collection'] + ':' + saved['number']
                assert oid not in all_rows, ('duplicate source ID between cohorts', oid)
                all_rows[oid], owning_cohort[oid] = saved, cohort['cohort']
        reviews = review_module.SourceReviews(isolated, 'deenhindi')
        assert set(reviews.decisions) == set(all_rows), 'review and source IDs differ'
        for oid, saved in sorted(all_rows.items()):
            original_saved = copy.deepcopy(saved)
            book, cohort = saved['collection'], owning_cohort[oid]
            decision, receipt, action = reviews.decisions[oid]
            source_hash = sha(importer.json_bytes(saved['source_record']))
            assert source_hash == decision['source_record_sha256']
            snapshot = saved['snapshot']
            if decision.get('source_snapshot'):
                assert decision['source_snapshot'] == snapshot
            else:
                assert decision['source_snapshot_sha256'] == snapshot['sha256']
            if 'source_reference_verbatim' in decision:
                assert decision['source_reference_verbatim'] == saved['source_reference_verbatim']
            if 'source_record_url' in decision:
                assert decision['source_record_url'] == snapshot['url']
            original_parsed = {k: saved[k] for k in
                ('schema', 'collection', 'number', 'snapshot', 'source_reference_verbatim', 'source_record')}
            original_parsed['classification'] = saved['intake_classification']
            original_parsed_bytes = importer.json_bytes(original_parsed)
            parsed_hash = sha(original_parsed_bytes)
            assert Path(saved['parsed_path']).name == parsed_hash + '.json.gz', ('parsed source receipt mismatch', oid)
            if 'source_parsed_path' in decision:
                assert decision['source_parsed_path'] == saved['parsed_path']
                assert decision['source_parsed_sha256'] == parsed_hash
            if args.verify_raw:
                stored = safe_file(root, snapshot['path']).read_bytes()
                assert sha(stored) == snapshot['stored_sha256'] and len(stored) == snapshot['stored_bytes']
                raw = gzip.decompress(stored) if snapshot.get('compression') == 'gzip' else stored
                assert sha(raw) == snapshot['sha256'] and len(raw) == snapshot['bytes']
                parsed_stored = safe_file(root, saved['parsed_path']).read_bytes()
                parsed_raw = gzip.decompress(parsed_stored)
                assert sha(parsed_raw) == parsed_hash and parsed_raw == original_parsed_bytes
                totals['raw_response_files_reopened'] += 1
                totals['raw_response_bytes_reopened'] += len(raw)
                totals['parsed_source_files_reopened'] += 1
                totals['parsed_source_bytes_reopened'] += len(parsed_raw)
            before = importer.canonical_record(saved)
            before_snapshot = copy.deepcopy(before)
            after, returned_action = reviews.apply(before, saved=saved)
            assert returned_action == action
            assert saved == original_saved and before == before_snapshot, ('input mutation', oid)
            mutable = {'language_versions', 'text', 'content_kind', 'review', 'report_types', 'extraction'}
            for key in set(before) - mutable:
                assert after[key] == before[key], ('source metadata changed', oid, key)
            assert after['number']['canonical'] is None
            for key in set(before['extraction']) - {'is_excerpt'}:
                assert after['extraction'][key] == before['extraction'][key]
            for key in set(before['review']) - {'status', 'independent_pro_qc', 'certified_release_eligible'}:
                assert after['review'][key] == before['review'][key]
            assert after['review']['independent_pro_qc'] == 'not_performed'
            assert after['review']['certified_release_eligible'] is False
            fields = decision.get('fields', decision.get('field_reviews'))
            by_id = {f.get('version_id', f.get('language_version_id')): f for f in fields}
            assert len(by_id) == len(fields)
            assert len(before['language_versions']) == len(after['language_versions'])
            selected_count = 0
            for old, new in zip(before['language_versions'], after['language_versions']):
                text, language = old['text'], old['language']
                field = by_id.get(old['id'])
                spans = (field.get('selected_spans', field.get('spans', [])) if field else [])
                reviewed = bool(field and field.get('reviewed', field.get('chars_reviewed') == len(text)))
                assert text == saved['source_record'][old['source']['source_field']]
                for key in set(old) - {'text','scope','quotation_status','source','comments','script','match_status'}:
                    assert new[key] == old[key], ('language metadata changed', oid, language, key)
                for key in old['source']:
                    assert new['source'][key] == old['source'][key], ('source language metadata changed', oid, language, key)
                if not field or not field.get('observed_script'):
                    assert new['script'] == old['script']
                else:
                    assert new['script'] == field['observed_script']
                    assert new['source']['importer_script_before_review'] == old['script']
                    assert new['source']['source_script_note'] == field['source_script_note']
                    totals['explicit_source_script_notes'] += 1
                if not field or not (field.get('source_content_mismatch') or {}).get('confirmed'):
                    assert new['match_status'] == old['match_status']
                for dest in (totals, by_language[language], by_book[book], by_cohort[cohort]):
                    dest['nonempty_source_fields'] += 1
                    dest['source_characters'] += len(text)
                    dest['source_utf8_bytes'] += len(text.encode())
                if field:
                    assert field['text_sha256'] == sha(text.encode())
                    if field.get('source_field'):
                        assert saved['source_record'][field['source_field']] == text
                    if 'text_chars' in field:
                        assert field['text_chars'] == len(text)
                if reviewed:
                    assert field['chars_reviewed'] == len(text) and field['bytes_reviewed'] == len(text.encode())
                    for dest in (totals, by_language[language], by_book[book], by_cohort[cohort]):
                        dest['fully_read_fields'] += 1
                        dest['read_characters'] += len(text)
                        dest['read_utf8_bytes'] += len(text.encode())
                else:
                    assert not spans, ('unread field admitted', oid, language)
                    for dest in (totals, by_language[language], by_book[book], by_cohort[cohort]):
                        dest['unread_nonempty_context_fields'] += 1
                pieces = []
                if spans:
                    assert reviewed and action == 'register'
                    selected_count += 1
                    positions = [[s['start'],s['end']] for s in spans]
                    assert new['source']['text_spans']['quotation_spans'] == positions
                    assert new['text'] == ''.join(text[a:b] for a,b in positions)
                    for span in spans:
                        a,b = span['start'],span['end']
                        assert sha(text[a:b].encode()) == span['sha256']
                        pieces.append((a,b,text[a:b],'quotation'))
                    for dest in (totals, by_language[language], by_book[book], by_cohort[cohort]):
                        dest['admitted_language_fields'] += 1
                        dest['quotation_spans'] += len(spans)
                        dest['quotation_characters'] += sum(b-a for a,b in positions)
                        dest['quotation_utf8_bytes'] += sum(len(text[a:b].encode()) for a,b in positions)
                    for component in new['source']['report_component_classifications']:
                        assert component['report_type'] and component['speaker_description']
                        types[component['report_type']] += 1
                else:
                    assert new['text'] is None
                    if reviewed:
                        for dest in (totals, by_language[language], by_book[book], by_cohort[cohort]):
                            dest['fully_read_context_only_fields'] += 1
                for note in new['comments']:
                    if note['scope'] == 'external_corroboration_not_source_text':
                        assert 'source_span' not in note
                        totals['external_corroboration_comments'] += 1
                        continue
                    assert note['scope'] == 'source_context_not_narration'
                    a,b = note['source_span']
                    assert note['text'] == text[a:b] and note['source_text_sha256'] == sha(text[a:b].encode())
                    pieces.append((a,b,note['text'],'context'))
                    totals['retained_context_spans'] += 1
                cursor = 0
                for a,b,body,kind in sorted(pieces):
                    assert a == cursor and b > a and text[a:b] == body, ('field partition mismatch', oid, language, a,b,cursor,kind)
                    cursor = b
                assert cursor == len(text) and ''.join(p[2] for p in sorted(pieces)) == text
                totals['exact_field_partition_checks'] += 1
                if action == 'exclude':
                    assert reviewed, ('excluded parent has unread nonempty field', oid, language)
            assert bool(selected_count) == (action == 'register')
            assert after['review']['source_bound_review']['approved_language_fields'] == selected_count
            if action == 'register':
                admitted = {v['language']:v['text'] for v in after['language_versions'] if v['text'] is not None}
                assert after['text'] == {'arabic': admitted.get('ar'), 'translation': admitted.get('hi')}
            if action == 'exclude':
                excluded.append(oid)
            if action == 'hold':
                held.append(oid)
            for dest in (totals, by_book[book], by_cohort[cohort]):
                dest['source_occurrences'] += 1
                dest[action] += 1
            totals['source_object_checks'] += 1
            totals['reconstructed_parsed_hash_checks'] += 1
            totals['source_metadata_preservation_checks'] += 1
            source_bindings.append({'id': oid, 'cohort': cohort, 'decision': action,
                'source_record_sha256': source_hash, 'source_snapshot_path': snapshot['path'],
                'source_snapshot_sha256': snapshot['sha256'], 'source_snapshot_stored_sha256': snapshot['stored_sha256'],
                'parsed_path': saved['parsed_path'], 'reconstructed_parsed_sha256': parsed_hash})
        reviews.finish()
        assert reviews.seen == set(all_rows)
    summary = {'schema':'hadith-bank-phase2-combined-validation-v1', 'result':'passed',
        'scope':manifest['status'], 'pending_cohort':manifest.get('pending_cohort'),
        'checks':{'supplied_file_checksums_and_copy_receipts':True,
                  'all_review_ids_match_unique_source_ids':True,
                  'source_reviews_apply_and_finish':True, 'source_inputs_not_mutated':True,
                  'source_objects_and_snapshot_receipts_bound':True,
                  'reconstructed_original_parsed_json_hashes_match_paths':True,
                  'literal_metadata_preserved':True, 'complete_exact_language_field_partitions':True,
                  'unread_languages_remain_source_context':True,
                  'all_nonempty_fields_read_for_excluded_occurrences':True,
                  'independent_pro_qc_not_claimed':True},
        'totals':dict(totals), 'per_book':{k:dict(v) for k,v in sorted(by_book.items())},
        'per_cohort':{k:dict(v) for k,v in sorted(by_cohort.items())},
        'language_coverage':{k:dict(v) for k,v in sorted(by_language.items())},
        'report_component_type_counts_across_languages':dict(sorted(types.items())),
        'excluded_occurrence_ids':excluded, 'held_occurrence_ids':held,
        'source_occurrence_id_count':len(all_rows), 'review_document_count':len(manifest['cohorts']),
        'candidate_file_count_verified':len(input_checksums),
        'supplied_file_checksum_count_verified':sum(r['supplied_sha256_verified'] for r in input_checksums),
        'engine_inputs':{Path(m.__file__).name:sha(Path(m.__file__).read_bytes())
                         for m in (importer,review_module,commentary_module)},
        'raw_source_bytes_verified':args.verify_raw,
        'full_checkout_source_and_export_gate':'required' if not args.verify_raw else 'raw source gate passed; full importer/export still required',
        'limits': ['No new source HTTP requests.', 'No generated canonical previews are publication inputs.',
                  'No independent Pro QC, authenticity certification, or cross-edition identity assertion.',
                  'Only this additive manifest is replayed; the full repository importer must still check interaction with existing reviews.',
                  'Raw response and parsed gzip bytes are not reopened unless --verify-raw is explicitly used in a full checkout.'],
        'independent_pro_qc':'not_performed', 'source_http_requests':0}
    output = args.output or root / REPORTS / 'phase2-validation.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(enc(summary))
    (output.parent/'phase2-source-bindings.jsonl.gz').write_bytes(gzip.compress(
        b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
                 for r in source_bindings),mtime=0))
    print(json.dumps({'result':summary['result'], 'totals':summary['totals'],
                      'per_book':{k:{x:v.get(x,0) for x in ('source_occurrences','register','exclude','hold','fully_read_fields','admitted_language_fields')}
                                  for k,v in summary['per_book'].items()},
                      'raw_source_bytes_verified':args.verify_raw},indent=2))

if __name__ == '__main__':
    main()
