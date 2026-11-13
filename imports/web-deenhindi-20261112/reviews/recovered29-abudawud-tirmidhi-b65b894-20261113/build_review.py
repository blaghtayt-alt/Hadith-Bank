#!/usr/bin/env python3
"""Compile explicit reading notes and validate exact saved evidence; no fetching."""
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

ROOT = Path(__file__).resolve().parent
COHORT = 'recovered29-abudawud-tirmidhi-b65b894-20261113'
CHECKPOINT = 'b65b894adfc1fcd80ff2ebbcedba60970e4f163f'
REVIEWS = 'imports/web-deenhindi-20261112/reviews'
EVIDENCE = REVIEWS + '/' + COHORT
ACTIVE = REVIEWS + '/source-review-' + COHORT + '.json.gz'
BASELINE = EVIDENCE + '/source-baseline.jsonl.gz'


def sha(data):
    return hashlib.sha256(data).hexdigest()


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
        'review_scope': 'Own complete language field read for attribution and boundaries; no independent authenticity or transcription certification.'}
    for attr in ('report_type', 'speaker'):
        if attr in instruction:
            result[attr] = instruction[attr]
    if instruction['action'] == 'whole':
        spans = [{'start': 0, 'end': len(text), 'sha256': sha(text.encode())}]
    elif instruction['action'] in ('excerpt', 'excerpts'):
        spans = []
        for i, selection in enumerate(instruction['spans']):
            start = 0 if selection['from'] is None else text.index(selection['from'])
            end = len(text) if selection['to'] is None else text.index(selection['to'], start)
            assert 0 <= start < end <= len(text), (key, language)
            for marker in (selection['from'], selection['to']):
                assert marker is None or text.count(marker) == 1, ('ambiguous boundary', key, language, marker)
            spans.append({'start': start, 'end': end, 'sha256': sha(text[start:end].encode()),
                'component_id': selection.get('component_id', 'passage-' + str(i + 1)),
                'report_type': selection['report_type'], 'speaker': selection['speaker']})
    else:
        assert instruction['action'] in ('source_context', 'source_context_only')
        spans = []
    result['spans'] = spans
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Verified recovered held-artifact input directory')
    parser.add_argument('--engine-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'publish')
    args = parser.parse_args()
    input_root, output = args.input.resolve(), args.output.resolve()
    sys.path.insert(0, str(args.engine_dir.resolve()))
    import import_deenhindi as importer
    import web_source_reviews as review_module
    import web_commentary_quotes as commentary_module
    all_rows = [json.loads(line) for line in (input_root / 'held-source-records.jsonl').read_text().splitlines() if line.strip()]
    rows = sorted([r for r in all_rows if r['collection'] in ('abudawud', 'tirmidhi')],
                  key=lambda r: (r['collection'], int(r['number'])))
    assert len(rows) == 29
    sources = {r['collection'] + ':' + r['number']: r for r in rows}
    assert len(sources) == len(rows)
    artifact_evidence = json.loads((input_root / 'evidence-manifest.json').read_bytes())
    state_entries = json.loads((input_root / 'held-state-entries.json').read_bytes())
    summary = json.loads((input_root / 'summary.json').read_bytes())
    assert summary['current_imported_entries'] == 13283 and summary['held_recovered_entries'] == 117
    assert summary['current_importer_sha256'] == sha(Path(importer.__file__).read_bytes())
    assert summary['current_review_engine_sha256'] == sha(Path(review_module.__file__).read_bytes() + Path(commentary_module.__file__).read_bytes())
    notes, manual_receipts = {}, []
    for path in sorted(ROOT.glob('manual-*.json')):
        data = path.read_bytes()
        manual_receipts.append(put(output, EVIDENCE + '/' + path.name, data))
        for record in json.loads(data)['records']:
            key = record['key']
            assert key in sources and key not in notes, ('duplicate or foreign note', key)
            assert set(record['fields']) == {'en', 'hi'}
            notes[key] = record['fields']
    assert set(notes) == set(sources), 'Every assigned source must have its own explicit notes'
    baseline_raw = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in rows).encode()
    baseline = put(output, BASELINE, gzip.compress(baseline_raw, mtime=0))
    raw_checks, decisions = [], []
    totals, books, languages = collections.Counter(), collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
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
            assert len(data) == expected['bytes'] and sha(data) == expected['sha256']
            verified.append({'path': relative, 'stored_bytes': len(data), 'stored_sha256': sha(data)})
        stored_raw = safe(input_root / 'sources', snapshot['path']).read_bytes()
        assert sha(stored_raw) == snapshot['stored_sha256'] and len(stored_raw) == snapshot['stored_bytes']
        raw = gzip.decompress(stored_raw)
        assert sha(raw) == snapshot['sha256'] and len(raw) == snapshot['bytes']
        parsed_stored = safe(input_root / 'sources', saved['parsed_path']).read_bytes()
        parsed_bytes = gzip.decompress(parsed_stored)
        assert sha(parsed_stored) == entry['parsed']['stored_sha256']
        assert sha(parsed_bytes) == entry['parsed']['sha256']
        assert Path(saved['parsed_path']).name == sha(parsed_bytes) + '.json.gz'
        parsed = json.loads(parsed_bytes)
        expected_parsed = {k: saved[k] for k in ('schema', 'collection', 'number', 'snapshot', 'source_reference_verbatim', 'source_record')}
        expected_parsed['classification'] = saved['intake_classification']
        assert parsed == expected_parsed and parsed_bytes == importer.json_bytes(expected_parsed)
        actual_object, actual_reference = importer.parse_record(raw, saved['collection'], saved['number'])
        assert actual_object == saved['source_record'] and actual_reference == saved['source_reference_verbatim']
        field_reviews = [compile_field(key, lang, instruction, saved['source_record'][importer.LANGUAGE_FIELDS[lang]], importer.LANGUAGE_FIELDS[lang]) for lang, instruction in notes[key].items()]
        assert len(field_reviews) == 2 and all(f['spans'] for f in field_reviews)
        decisions.append({'id': 'deenhindi-' + key, 'decision': 'register',
            'reason': 'Independently read Hindi and English fields each contain attributed report wording. Other language fields remain complete unread source context.',
            'source_record_sha256': source_hash, 'source_snapshot_sha256': snapshot['sha256'],
            'source_record_url': snapshot['url'], 'source_parsed_path': saved['parsed_path'],
            'source_parsed_sha256': sha(parsed_bytes), 'source_reference_verbatim': saved['source_reference_verbatim'],
            'field_reviews': field_reviews})
        raw_checks.append({'id': 'deenhindi-' + key, 'source_record_sha256': source_hash,
            'raw_sha256': sha(raw), 'raw_bytes': len(raw), 'parsed_sha256': sha(parsed_bytes),
            'parsed_bytes': len(parsed_bytes), 'files': verified, 'exact_current_parser_object_and_reference': True})
        totals['raw_responses_reopened_and_reparsed'] += 1
        totals['parsed_source_files_reopened'] += 1
        totals['raw_response_bytes'] += len(raw)
        totals['parsed_source_bytes'] += len(parsed_bytes)
    document = {'schema': 'hadith-bank-web-source-review-v1', 'site': 'deenhindi',
        'review_scope': 'Individual full-field reading of Hindi and English in 29 recovered Abu Dawud and Tirmidhi source occurrences. Named companion and historical reports retain actual attribution; no unread-field or cross-occurrence approval.',
        'source_checkpoint': CHECKPOINT, 'source_ledger_path': BASELINE,
        'source_ledger_sha256': baseline['sha256'], 'source_ledger_uncompressed_sha256': sha(baseline_raw),
        'manual_decision_files': manual_receipts, 'independent_pro_qc': 'not_performed',
        'independent_pro_qc_performed': False, 'new_translation_created': False, 'records': decisions}
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
        assert action == 'register'
        book = saved['collection']
        fields = {f['language_version_id']: f for f in native.decisions[after['id']][0]['field_reviews']}
        for name in set(original) - {'language_versions', 'text', 'content_kind', 'review', 'report_types', 'extraction'}:
            assert after[name] == original[name], ('metadata', key, name)
        for name in original['extraction']:
            if name != 'is_excerpt': assert after['extraction'][name] == original['extraction'][name]
        assert after['review']['independent_pro_qc'] == 'not_performed' and after['review']['certified_release_eligible'] is False
        assert after['number']['canonical'] is None
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
                positions = [[s['start'], s['end']] for s in field['spans']]
                assert new['source']['text_spans']['quotation_spans'] == positions
                assert new['text'] == ''.join(text[a:b] for a, b in positions)
                selected[language] = new['text']
                for span in field['spans']:
                    a, b = span['start'], span['end']
                    assert sha(text[a:b].encode()) == span['sha256']
                    pieces.append((a, b, text[a:b], 'quotation'))
                for counter in (totals, books[book], languages[language]):
                    counter['complete_fields_read'] += 1
                    counter['admitted_language_fields'] += 1
                    counter['quotation_spans'] += len(field['spans'])
                    counter['characters_read'] += len(text)
                    counter['utf8_bytes_read'] += len(text.encode())
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
                'source_text_sha256': sha(text.encode()), 'source_chars': len(text),
                'read': bool(field), 'parts': [{'start': a, 'end': b, 'sha256': sha(body.encode()), 'role': kind} for a, b, body, kind in sorted(pieces)]})
            for counter in (totals, books[book], languages[language]):
                counter['exact_complete_field_partitions'] += 1
        assert set(selected) == {'en', 'hi'}
        assert after['text'] == {'arabic': None, 'translation': selected['hi']}
        assert after['review']['source_bound_review']['approved_language_fields'] == 2
        totals['source_metadata_preservation_checks'] += 1
        for counter in (totals, books[book]):
            counter['source_occurrences'] += 1
            counter['register'] += 1
    native.finish()
    assert totals['source_occurrences'] == 29 and totals['complete_fields_read'] == 58
    assert totals['exact_complete_field_partitions'] == 145 and totals['unread_nonempty_context_fields'] == 87
    evidence = {'schema': 'hadith-bank-recovered-review-evidence-v1', 'result': 'passed',
        'source_checkpoint': CHECKPOINT, 'held_export_artifact': {'id': 14029806818,
            'archive_bytes': 2440509, 'archive_sha256': 'c22e3d12b7f242ccebd2e272ed202993479d2d4d05bcbdfe672ebbdae6caeff6',
            'archive_verification': 'Parent independently verified archive; this review reopens its extracted receipts and raw/parsed bytes.'},
        'recovery_id': summary['recovery_id'], 'original_interrupted_artifact': summary['artifact'],
        'input_files': [{'path': name, 'bytes': (input_root/name).stat().st_size,
                         'sha256': sha((input_root/name).read_bytes())} for name in
                        ('held-source-records.jsonl', 'held-state-entries.json', 'evidence-manifest.json', 'summary.json')],
        'records': raw_checks}
    put(output, EVIDENCE + '/source-evidence.json', enc(evidence))
    put(output, EVIDENCE + '/field-partitions.json.gz', gzip.compress(enc(partitions), mtime=0))
    coverage = {'schema': 'hadith-bank-recovered-review-validation-v1', 'result': 'passed',
        'source_checkpoint': CHECKPOINT, 'active_review': active_receipt, 'source_baseline': baseline,
        'totals': dict(totals), 'by_book': {k: dict(v) for k, v in sorted(books.items())},
        'by_language': {k: dict(v) for k, v in sorted(languages.items())},
        'hold_decisions': 0, 'source_only_decisions': 0, 'unprocessed_decisions': 0,
        'checks': {'exact_unique_source_and_review_ids': True, 'source_reviews_apply_and_finish': True,
            'raw_stored_and_uncompressed_hashes': True, 'parsed_stored_and_uncompressed_hashes': True,
            'current_parser_exact_source_object_and_reference': True, 'all_source_metadata_preserved': True,
            'source_and_canonical_inputs_not_mutated': True, 'exact_full_field_partitions': True,
            'unread_siblings_retained_context': True, 'no_engine_changes': True, 'no_source_http_requests': True},
        'engine_sha256': {Path(m.__file__).name: sha(Path(m.__file__).read_bytes()) for m in
                          (importer, review_module, commentary_module)},
        'limits': 'Local exact-source review replay; shared full-repository export, registry checks and deployment remain CI gates.',
        'independent_pro_qc': 'not_performed', 'new_translation_created': False}
    put(output, EVIDENCE + '/validation.json', enc(coverage))
    put(output, EVIDENCE + '/build_review.py', Path(__file__).read_bytes())
    print(json.dumps({'result': 'passed', 'totals': dict(totals), 'by_book': coverage['by_book'],
                      'active_review': active_receipt, 'source_baseline': baseline}, ensure_ascii=False))


if __name__ == '__main__':
    main()
