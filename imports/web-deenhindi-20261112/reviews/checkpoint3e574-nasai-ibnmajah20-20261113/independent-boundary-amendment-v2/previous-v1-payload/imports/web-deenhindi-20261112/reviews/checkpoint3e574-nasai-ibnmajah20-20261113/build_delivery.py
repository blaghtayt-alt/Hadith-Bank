#!/usr/bin/env python3
"""Serialize explicitly read Nasai13/IbnMajah7 fields without changing source evidence."""
from __future__ import annotations

import argparse
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
REL = Path('imports/web-deenhindi-20261112/reviews')
EVID = REL / 'checkpoint3e574-nasai-ibnmajah20-20261113'
ACTIVE = REL / 'source-review-checkpoint3e574-nasai-ibnmajah20-20261113.json.gz'
CHECKPOINT = '3e574b9e7e4dd7cf8bc23232249004a18692c61c'
FIELDS = {'ar': 'textArabic', 'hi': 'translationHindi', 'ur': 'translationUrdu',
          'ur-Latn': 'translationUrduRoman', 'en': 'translationEnglish'}
BASELINE_SHA = '0c794e514bcbebcda174dab501a3139963bda68b636a5a3b1049db0ce93f9a15'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = encoded(value)
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == '.gz' else data)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scripts', type=Path, default=WORK / 'hindi-resolve/work/scripts')
    parser.add_argument('--evidence', type=Path,
        default=WORK / 'phase18-successor-acquisition-monitor/held-evidence')
    parser.add_argument('--output-dir', type=Path, default=HERE / 'publish')
    parser.add_argument('--manifest-file', type=Path, default=HERE / 'delivery-manifest-v1.json')
    args = parser.parse_args()
    sys.path.insert(0, str(args.scripts))
    import import_deenhindi as importer
    from web_source_reviews import SourceReviews
    helper = module('span_serializer', WORK / 'deen-muslim-malik-review/build_delivery.py')
    sys.path.insert(0, str(HERE))
    reading_module = module('manual_rules', HERE / 'manual_rules.py')
    specifications = reading_module.SPECS
    baseline = (HERE / 'input/cohort.jsonl').read_bytes()
    assert sha(baseline) == BASELINE_SHA
    records = [json.loads(line) for line in baseline.splitlines()]
    assert len(records) == len(specifications) == 20
    assert {r['collection'] + ':' + r['number'] for r in records} == set(specifications)
    assert collections.Counter(r['collection'] for r in records) == {'nasai':13,'ibnmajah':7}
    reading_bytes = (HERE / 'source-first-complete-reading.json').read_bytes()
    assert sha(reading_bytes) == 'dafc871d2b94e2976220e2a11309c15a3c550a1e4cc6bf4d5f217cb23ab9fe70'
    own_reading = json.loads(reading_bytes)
    assert own_reading['source_commit'] == CHECKPOINT
    assert own_reading['all_full_fields_read_before_candidate_creation'] is True
    assert (own_reading['complete_fields'], own_reading['characters'], own_reading['utf8_bytes']) == (40,10697,21245)
    own_fields = {(f['id'], f['language']):f for f in own_reading['fields']}
    expected_read = {('deenhindi-' + k, lang) for k,v in specifications.items() for lang in v['read_languages']}
    assert len(own_fields) == 40 and set(own_fields) == expected_read
    entries = json.loads((args.evidence / 'held-state-entries.json').read_bytes())
    evidence_manifest = json.loads((args.evidence / 'evidence-manifest.json').read_bytes())
    assert evidence_manifest['saved_head'] == CHECKPOINT
    source_root = args.evidence / 'sources'
    out = args.output_dir
    baseline_relative = EVID / 'source-baseline.jsonl.gz'
    baseline_path = out / baseline_relative
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_bytes(gzip.compress(baseline, mtime=0))
    decisions, coverage, dispositions, verification = [], [], [], []
    for saved in records:
        local_id = saved['collection'] + ':' + saved['number']
        identity = 'deenhindi-' + local_id
        rules = specifications[saved['collection'] + ':' + saved['number']]
        assert rules['id'] == local_id
        assert set(rules['field_notes']) == set(rules['read_languages'])
        assert set(rules['languages']) <= set(rules['read_languages']) <= set(FIELDS)
        assert rules['decision'] in ('register', 'exclude')
        assert rules['decision'] == 'register' or (not rules['languages'] and set(rules['read_languages']) == set(FIELDS))
        entry = entries[local_id]
        parsed_bytes = importer.checked_bytes(source_root, entry['parsed'])
        parsed = json.loads(parsed_bytes)
        assert entry['parsed']['path'] == saved['parsed_path']
        for key in ('collection', 'number', 'source_record', 'source_reference_verbatim', 'snapshot'):
            assert parsed[key] == saved[key], (identity, key)
        html = importer.checked_bytes(source_root, saved['snapshot'])
        source, reference = importer.parse_record(html, saved['collection'], saved['number'])
        assert source == saved['source_record'] and reference == saved['source_reference_verbatim']
        source_hash = sha(importer.json_bytes(source))
        file_evidence = []
        for descriptor in (saved['snapshot'], entry['parsed']):
            p = source_root / descriptor['path']
            stored = p.read_bytes()
            authority = evidence_manifest['files'][descriptor['path']]
            git_blob = hashlib.sha1(b'blob ' + str(len(stored)).encode() + b'\0' + stored).hexdigest()
            assert sha(stored) == authority.get('stored_sha256', authority['sha256']) and git_blob == authority['git_blob_sha1']
            file_evidence.append({'path': descriptor['path'], **authority})
        verification.append({'id': identity, 'source_url': saved['snapshot']['url'],
            'snapshot': saved['snapshot'], 'parsed': entry['parsed'], 'files': file_evidence,
            'source_record_sha256': source_hash, 'raw_response_reopened': True,
            'stored_and_original_hashes_verified': True,
            'current_parser_object_and_reference_match': True})
        decision = {'id': identity, 'collection': saved['collection'], 'number': saved['number'],
            'decision': rules['decision'], 'source_record_sha256': source_hash,
            'source_snapshot': copy.deepcopy(saved['snapshot']),
            'source_reference_verbatim': saved['source_reference_verbatim'],
            'numbering_system': 'deenhindi_source_local', 'verified_external_reference': None,
            'reason': rules['reason'], 'field_reviews': []}
        coverage_row = {'id': identity, 'source_record_sha256': source_hash,
            'source_url': saved['snapshot']['url'], 'decision': rules['decision'], 'fields': []}
        for language, field in FIELDS.items():
            text = source[field]
            assert isinstance(text, str), (identity, field)
            if not text:
                assert language not in rules['read_languages'] and language not in rules['languages']
                coverage_row['fields'].append({'language':language,'source_field':field,'text_sha256':sha(b''),'text_chars':0,'text_bytes':0,'field_reviewed':False,'chars_reviewed':0,'bytes_reviewed':0,'status':'empty_source_field','reading_note':'Original source value is exactly an empty string; no semantic reading or admission is claimed.','boundary_reason':'Preserve original empty slot; no invented text.','selected_spans':[]})
                continue
            reviewed = language in rules['read_languages']
            if reviewed:
                frozen = own_fields[(identity, language)]
                assert frozen['text'] == text and frozen['sha256'] == sha(text.encode())
                assert frozen['characters'] == len(text) and frozen['utf8_bytes'] == len(text.encode())
                assert frozen['complete_field_read'] is True
            selected = language in rules['languages']
            note = rules['field_notes'].get(language,
                'This complete sibling field was not linguistically read in this review; preserve it as unread source context.')
            reason = rules['reason'] + ' Complete-field reading: ' + note if reviewed else note
            spans = helper.field_spans(text, rules, language) if selected else []
            for span in spans:
                family = 'report-1' if rules.get('shared_report_family') else span['component_id']
                span['source_report_family_id'] = identity + ':' + family
            whole = len(spans) == 1 and spans[0]['start'] == 0 and spans[0]['end'] == len(text)
            action = 'whole' if whole else 'excerpts' if spans else 'source_context' if reviewed else 'unreviewed'
            field_review = {'language_version_id': identity + ':' + language,
                'language': language, 'source_field': field, 'text_sha256': sha(text.encode()),
                'text_chars': len(text), 'reviewed': reviewed,
                'chars_reviewed': len(text) if reviewed else 0,
                'bytes_reviewed': len(text.encode()) if reviewed else 0,
                'action': action, 'reason': reason, 'spans': spans}
            if reviewed:
                field_review.update(review_method='manual_complete_field_reading_and_exact_span_selection',
                    review_scope='This entire source field was read independently. Actual supplied reports are classified by their own speaker and exact words. No neighboring identity, omitted body, translated sibling, or number match is used to fill it.')
            if language in rules.get('annotations', {}):
                field_review['source_text_annotations'] = [{
                    'kind': 'own_field_attribution_or_wording_qualification',
                    'note': rules['annotations'][language], 'new_translation': False}]
            if language in rules.get('observed_scripts', {}):
                assert reviewed and selected
                field_review['observed_script'] = rules['observed_scripts'][language]
                field_review['source_script_note'] = rules['script_notes'][language]
            decision['field_reviews'].append(field_review)
            coverage_row['fields'].append({'language': language, 'source_field': field,
                'text_sha256': field_review['text_sha256'], 'text_chars': len(text),
                'text_bytes': len(text.encode()), 'field_reviewed': reviewed,
                'chars_reviewed': field_review['chars_reviewed'],
                'bytes_reviewed': field_review['bytes_reviewed'],
                'status': 'selected_report' if selected else 'reviewed_source_context' if reviewed else 'unreviewed_source_context',
                'reading_note': note, 'boundary_reason': reason,
                'selected_spans': [[s['start'], s['end']] for s in spans]})
        decisions.append(decision)
        coverage.append(coverage_row)
        dispositions.append({'id': identity, 'decision': rules['decision'],
            'semantic_disposition': 'resolved_registered_report' if rules['decision'] == 'register'
                else 'resolved_source_only_no_supplied_report_body',
            'semantic_review_pending': False, 'reason': rules['reason'],
            'source_record_sha256': source_hash, 'snapshot_sha256': saved['snapshot']['sha256'],
            'source_url': saved['snapshot']['url'], 'source_reference_verbatim': saved['source_reference_verbatim'],
            'reviewed_nonempty_fields': len(rules['read_languages']),
            'selected_fields': len(rules['languages']), 'external_attribution_corroboration': False})
    dump(out / ACTIVE, {'schema': 'hadith-bank-web-source-review-v1', 'site': 'deenhindi',
        'independent_pro_qc': 'not_performed', 'source_ledger_path': baseline_relative.as_posix(),
        'source_ledger_sha256': sha(baseline_path.read_bytes()), 'records': decisions})
    dump(out / EVID / 'manual-reading-and-boundary-specifications.json.gz', {
        'scope': 'Nasai13/IbnMajah7 at checkpoint3e574. All40 Hindi-labelled/Urdu fields were read completely before candidate creation; all20 parents contain actual supplied finite content. Three Hindi-labelled fields visibly contain Latin-script Roman Urdu and receive only explicit script metadata correction, with source identities/text preserved.58 nonempty siblings remain unread and2 original source slots remain exactly empty. All material scope, quantities and actor distinctions remain; lexical/omission/equivalent-wording apparatus stays in lossless context.',
        'all_five_fields_read': False, 'source_checkpoint': CHECKPOINT,
        'specifications': list(specifications.values())})
    dump(out / EVID / 'field-coverage.json.gz', coverage)
    dump(out / EVID / 'disposition-ledger.json.gz', dispositions)
    dump(out / EVID / 'raw-source-verification.json.gz', {
        'source_checkpoint': CHECKPOINT,
        'source_evidence_manifest_sha256': sha((args.evidence / 'evidence-manifest.json').read_bytes()),
        'current_parser_sha256': sha(Path(importer.__file__).read_bytes()),
        'reopened_source_responses': len(verification), 'rows': verification})
    native = SourceReviews(out, 'deenhindi')
    rendered, metadata_checks, partitions, script_corrections = [], 0, 0, []
    for saved, decision in zip(records, decisions):
        original = importer.canonical_record(saved)
        revised, disposition = native.apply(copy.deepcopy(original), saved=saved)
        assert disposition == decision['decision']
        for key in ('id', 'number', 'narrator', 'grading', 'references', 'source_locator', 'source'):
            assert revised[key] == original[key], (decision['id'], key)
            metadata_checks += 1
        assert len(original['language_versions']) == len(revised['language_versions']) == sum(bool(saved['source_record'][f]) for f in FIELDS.values())
        for before, after in zip(original['language_versions'], revised['language_versions']):
            for key in ('id', 'language'):
                assert after.get(key) == before.get(key), (decision['id'], key)
                metadata_checks += 1
            rule = next(f for f in decision['field_reviews'] if f['language_version_id'] == before['id'])
            if 'observed_script' in rule:
                assert before['script'] == 'Deva' and after['script'] == rule['observed_script'] == 'Latn'
                assert after['source']['importer_script_before_review'] == before['script']
                assert after['source']['source_script_note'] == rule['source_script_note']
                script_corrections.append({'id':decision['id'],'language':before['language'],
                    'before':before['script'],'after':after['script'],'reason':rule['source_script_note']})
            else:
                assert after.get('script') == before.get('script'), decision['id']
                metadata_checks += 1
            text = before['text']
            selected = after['source'].get('text_spans', {}).get('quotation_spans', [])
            assert (after['text'] or '') == ''.join(text[a:b] for a, b in selected)
            parts = [(a, b, text[a:b]) for a, b in selected]
            parts.extend((c['source_span'][0], c['source_span'][1], c['text'])
                for c in after['comments'] if c.get('source_span') is not None)
            cursor = 0
            for start, end, value in sorted(parts):
                assert start == cursor and value == text[start:end]
                cursor = end
            assert cursor == len(text) and ''.join(p[2] for p in sorted(parts)) == text
            partitions += 1
        rendered.append(revised)
    native.finish()
    all_fields = [f for row in coverage for f in row['fields']]
    stats = {'records': len(decisions),
        'registered_records': sum(d['decision'] == 'register' for d in decisions),
        'resolved_source_only_records': sum(d['decision'] == 'exclude' for d in decisions),
        'source_only_ids': [d['id'] for d in decisions if d['decision'] == 'exclude'],
        'unresolved_record_dispositions': 0, 'source_field_slots': len(all_fields),
        'nonempty_source_fields': sum(f['text_chars'] > 0 for f in all_fields),
        'exact_empty_source_fields': sum(f['status'] == 'empty_source_field' for f in all_fields),
        'fully_read_nonempty_fields': sum(f['field_reviewed'] for f in all_fields),
        'selected_language_fields': sum(f['status'] == 'selected_report' for f in all_fields),
        'reviewed_context_fields': sum(f['status'] == 'reviewed_source_context' for f in all_fields),
        'unreviewed_sibling_context_fields': sum(f['status'] == 'unreviewed_source_context' for f in all_fields),
        'complete_fields_chars_read': sum(f['chars_reviewed'] for f in all_fields),
        'complete_fields_utf8_bytes_read': sum(f['bytes_reviewed'] for f in all_fields),
        'source_responses_reopened_hashed_and_reparsed': len(verification),
        'source_snapshot_files_verified': len(verification) * 2,
        'exact_source_metadata_checks': metadata_checks, 'exact_lossless_field_partitions': partitions,
        'source_review_engine_sha256': native.engine_sha256,
        'by_language': {language: dict(collections.Counter(f['status'] for f in all_fields if f['language'] == language))
            for language in FIELDS},
        'source_script_corrections': script_corrections,
        'source_first_complete_reading_sha256': sha(reading_bytes),
        'validation': 'SourceReviews apply/finish passed for all20; exact original-field partitions and all stated metadata invariants passed. Each original HTML and parsed snapshot was reopened and checked against stored, decompressed and Git blob hashes, then reparsed against the full saved source object and source reference.',
        'source_checkpoint': CHECKPOINT, 'independent_pro_qc': 'not_performed'}
    assert (stats['registered_records'], stats['resolved_source_only_records']) == (20, 0)
    assert (stats['fully_read_nonempty_fields'], stats['selected_language_fields'], stats['reviewed_context_fields'], stats['unreviewed_sibling_context_fields']) == (40, 40, 0, 58)
    assert (stats['complete_fields_chars_read'], stats['complete_fields_utf8_bytes_read']) == (10697, 21245)
    assert partitions == 98
    assert len(script_corrections) == 3
    assert (stats['source_field_slots'],stats['nonempty_source_fields'],stats['exact_empty_source_fields']) == (100,98,2)
    assert (HERE / 'input/cohort.jsonl').read_bytes() == baseline
    dump(out / EVID / 'validation-and-coverage-summary.json', stats)
    dump(HERE / 'validated-derived-records.json.gz', rendered)
    # This inventory describes completed manual selections. It does not classify
    # text, infer semantics, or claim any unread sibling was read.
    apparatus_rows, exact_context = [], []
    for saved, decision in zip(records, decisions):
        rules = specifications[saved['collection'] + ':' + saved['number']]
        for field in decision['field_reviews']:
            text = saved['source_record'][field['source_field']]
            selected = [(s['start'], s['end']) for s in field['spans']]
            if not selected:
                continue
            retained_parentheses, stack = [], []
            for index, char in enumerate(text):
                if char == '(':
                    stack.append(index)
                elif char == ')' and stack:
                    first, last = stack.pop(), index + 1
                    if any(a <= first and last <= b for a,b in selected):
                        retained_parentheses.append({'start':first,'end':last,
                            'text':text[first:last],
                            'complete_field_reading_note':rules['field_notes'][field['language']]})
            selected_markers = [{'start':m.start(),'end':m.end(),'text':m.group()}
                for m in re.finditer(r'[0-9۰-۹٠-٩]+[؎؏]|[؎؏]|\[[^\]]+\]|\*', text)
                if any(a <= m.start() and m.end() <= b for a,b in selected)]
            cursor = 0
            for first,last in selected + [(len(text),len(text))]:
                if first > cursor:
                    literal = text[cursor:first]
                    exact_context.append({'id':decision['id'],'language':field['language'],
                        'source_field_sha256':field['text_sha256'],'start':cursor,'end':first,
                        'text':literal,'text_sha256':sha(literal.encode()),
                        'reason':rules['field_notes'][field['language']]})
                cursor = last
            apparatus_rows.append({'id':decision['id'],'language':field['language'],
                'source_field_sha256':field['text_sha256'],
                'retained_parentheses':retained_parentheses,
                'selected_literal_apparatus_markers':selected_markers})
    assert len(apparatus_rows) == 40
    assert not any(f['selected_literal_apparatus_markers'] for f in apparatus_rows)
    dump(out / EVID / 'source-apparatus-inventory.json.gz', {
        'schema':'hadith-bank-explicit-source-apparatus-inventory-v1',
        'source_checkpoint':CHECKPOINT,'active_ledger':ACTIVE.as_posix(),
        'active_ledger_sha256':sha((out / ACTIVE).read_bytes()),
        'scope':'All40 admitted fields after complete own-field reading; literal inventories verify the frozen decisions without making any new semantic decision or classifying unread fields.',
        'selected_fields':len(apparatus_rows),
        'exact_source_context_gaps':len(exact_context),
        'selected_literal_apparatus_markers':0,
        'context_gaps':exact_context,'fields':apparatus_rows,
    })
    for name in ['manual_rules.py','source-first-complete-reading.json','source-verification.json',
                 'build_delivery.py','freeze_source_first.py','prepare_primary.py']:
        target=out/EVID/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((HERE/name).read_bytes())
    def file_binding(path, local=False):
        data = path.read_bytes()
        binding = {
            'path': path.relative_to(out).as_posix(), 'bytes': len(data),
            'size_bytes': len(data), 'sha256': sha(data),
            'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
        }
        if local:
            binding.update(local_path=str(path), source_path=str(path))
        return binding
    portable = out / EVID / 'package-file-manifest.json'
    dump(portable, {
        'schema': 'hadith-bank-source-review-package-manifest-v1',
        'source_checkpoint': CHECKPOINT,
        'active_ledger': ACTIVE.as_posix(),
        'source_baseline': baseline_relative.as_posix(),
        'summary': stats,
        'manifest_excludes_its_own_recursive_hash': True,
        'files': [file_binding(p) for p in sorted(out.rglob('*')) if p.is_file() and p != portable],
    })
    dump(args.manifest_file, {'output_root': str(out), 'summary': stats,
        'files': [file_binding(p, local=True) for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
