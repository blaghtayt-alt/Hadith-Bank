#!/usr/bin/env python3
"""Bounded read-only check of reporting changes after revision-4 content QC."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import re
import sys

Q = Path(__file__).resolve().parent
W = Q.parents[3]
E = W/'patches/patch08'
P = W/'work/cp016_parent/bn_riyadh_20261113_v2_cp016_patch07'
S = W/'work/patch08_integration_output/bn_riyadh_20261113_v2_cp017_patch08'
EP = 'continuation/patch08/'
VERSION = 'v2_cp017_patch08'
PARENT_SHA = '9de6f653de73a932a46a555e30bfe3817cf2fd9bfa22b4f0ded5158f12c01d85'
CONTENT_MANIFEST_SHA = 'a8a0a5314abc92e2a75284567571deb495aaf240c32a525cd3266b1b512c49a5'
CONTENT_REPORT_SHA = '4b3a42e9a6a215fb5ff6052563e38ca79e6dc6891e8d035d7b0a7f3ff252b9f8'
PREPARED_SHA = 'd60f125b646bed02c955a6221310857a9f3f674ccb279ec205ccd5a73a631ae7'
checks = {}
inputs = {}
cache = {}
metrics = {}


def check(name, good, detail=None):
    r = checks.setdefault(name, {'evaluations': 0, 'failures': 0, 'examples': []})
    r['evaluations'] += 1
    if not good:
        r['failures'] += 1
        if len(r['examples']) < 8:
            r['examples'].append(detail)
    return good


def sha(p):
    p = Path(p).resolve()
    st = p.stat()
    k = str(p), st.st_size, st.st_mtime_ns
    if k not in cache:
        with p.open('rb') as f:
            cache[k] = hashlib.file_digest(f, 'sha256').hexdigest()
    return cache[k]


def use(p):
    p = Path(p).resolve()
    inputs.setdefault(str(p), {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    return p


def readj(p):
    return json.loads(use(p).read_bytes())


def readjl(p):
    with use(p).open(encoding='utf8', newline='') as f:
        return [json.loads(x) for x in f if x.strip()]


def resolve(rel):
    p = Path(rel)
    if p.is_absolute():
        return p
    if (S/rel).is_file():
        return S/rel
    if rel.startswith(EP) and (E/rel[len(EP):]).is_file():
        return E/rel[len(EP):]
    if (P/rel).is_file():
        return P/rel
    return W/rel


def norm(x):
    if isinstance(x, str):
        for pref in [str(E)+'/', 'patches/patch08/']:
            if x.startswith(pref):
                return EP+x[len(pref):]
        if x.startswith(str(P)+'/'):
            return x[len(str(P))+1:]
        return x
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    return x


def diff(a, b, path='$'):
    if type(a) is not type(b):
        return [{'path': path, 'before': a, 'after': b}]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            q = path+'.'+k
            if k not in a:
                out.append({'path': q, 'added': b[k]})
            elif k not in b:
                out.append({'path': q, 'removed': a[k]})
            else:
                out += diff(a[k], b[k], q)
        return out
    if a != b:
        return [{'path': path, 'before': a, 'after': b}]
    return []


allowed = {
    'resume_state.json': ['independent_patch_QC', 'next_actions', 'next_phase', 'remaining_not_fully_verified_character_pages', 'remaining_whole_page_character_reviews_scope', 'unattempted_character_pages'],
    'metadata.json': ['counts.completion_claim', 'counts.independent_patch_character_unique_pages', 'counts.release_status', 'counts.remaining_scope.independent_Pro_QC', 'execution_and_qc.independent_patch_QC', 'execution_and_qc.self_review', 'execution_and_qc.separate_independent_Pro_QC', 'patch08_continuation.independent_QC_status', 'patch08_continuation.independent_patch_QC', 'patch08_continuation.semantic_interpretations_corrected_after_QC', 'release_status'],
    'remaining_work.json': ['bank_adapter_and_local_reader_validation_complete', 'bank_import_preflight', 'independent_Pro_QC', 'independent_patch_QC', 'retained_investigated_semantic_source_uncertainties', 'separate_independent_Pro_QC', 'source_limited_glyph_next_step', 'status', 'unattempted_original_pages', 'unclassified_lexical_intervals', 'uninvestigated_assigned_character_cases'],
    'validation.json': ['QC_report', 'content_candidate_revision', 'independent_patch_QC'],
    'coverage.json': ['independent_Pro_QC', 'independent_patch_QC', 'patch08_delta.independent_QC_status', 'patch08_delta.independent_patch_QC', 'patch08_delta.semantic_interpretations_corrected_after_QC', 'semantic_integration.independent_patch_QC', 'status'],
    'continuation/integration/integration_summary.json': ['independent_patch_QC'],
    'continuation/patch08/patch08_summary.json': ['independent_QC_status', 'independent_patch_QC', 'semantic_interpretations_corrected_after_QC']
}


def main():
    use(Path(__file__))
    binding = readj(Q/'RESULT_BINDING.json')
    for r in binding['files']:
        p = use(Q/r['path'])
        check('immutable_content_audit_artifacts', p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], r['path'])
    check('immutable_content_report_identity', sha(Q/'REPORT.json') == CONTENT_REPORT_SHA)
    candidate = readj(Q/'REVIEWED_CANDIDATE_REVISION4.json')
    check('reviewed_candidate_manifest_identity', sha(Q/'REVIEWED_CANDIDATE_REVISION4.json') == CONTENT_MANIFEST_SHA and candidate['candidate_revision'] == 4)
    before = {r['path']: r for r in candidate['files']}
    status_diffs = {}
    unchanged = []
    for rel, r in before.items():
        p = use(S/rel)
        if rel in allowed:
            old = use(Q/'reviewed_status_revision4'/rel)
            check('saved_pre_reporting_status_bytes', sha(old) == r['sha256'] and old.stat().st_size == r['bytes'], rel)
            d = diff(readj(old), readj(p))
            check('status_only_allowed_JSON_paths', {x['path'][2:] for x in d} == set(allowed[rel]), [rel, [x['path'] for x in d]])
            status_diffs[rel] = d
        else:
            check('all_reviewed_core_files_byte_identical', p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], rel)
            unchanged.append(rel)
    check('all_seven_status_snapshots_used', set(status_diffs) == set(allowed))
    metrics['unchanged_reviewed_core_files'] = len(unchanged)
    metrics['status_documents_changed'] = len(status_diffs)
    metrics['allowed_status_JSON_changes'] = sum(len(x) for x in status_diffs.values())

    receipt_path = W/'work/patch08_integration_output/FINAL_RELEASE_PREPARED.json'
    receipt = readj(receipt_path)
    receipt_copy = use(E/'release_documentation/FINAL_RELEASE_PREPARED.json')
    check('final_preparation_receipt_pinned', sha(receipt_path) == sha(receipt_copy) == PREPARED_SHA)
    check('final_preparation_candidate_revision', receipt['version'] == VERSION and receipt['reviewed_content_candidate_revision'] == 4)
    stage_inventory = {p.relative_to(S).as_posix() for p in S.rglob('*') if p.is_file()}
    check('final_receipt_exhaustive_stage_inventory', stage_inventory == {r['path'] for r in receipt['generated']})
    for r in receipt['generated']:
        p = use(S/r['path'])
        check('final_preparation_generated_hashes', p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], r['path'])
    metrics['final_stage_files'] = len(stage_inventory)
    expected_new = {'QC_REPORT.json', 'README.md', 'READ_FIRST_EN.txt', 'READ_FIRST_JA.txt', 'changes_since_previous_checkpoint.jsonl', 'checkpoint_lineage.json', EP+'patch08_report.md', 'corrections.jsonl', 'logs_index.json', 'release_integrity_validation.json'}
    check('only_expected_new_reporting_files', stage_inventory-set(before) == expected_new, sorted(stage_inventory-set(before)))

    qc = readj(S/'QC_REPORT.json')
    cov, meta, rem, resume = [readj(S/rel) for rel in ['coverage.json', 'metadata.json', 'remaining_work.json', 'resume_state.json']]
    summary = readj(S/'continuation/integration/integration_summary.json')
    delta = readj(S/(EP+'patch08_summary.json'))
    validation = readj(S/'validation.json')
    release = readj(S/'release_integrity_validation.json')
    check('current_QC_copies_consistent', cov['independent_patch_QC'] == meta['execution_and_qc']['independent_patch_QC'] == qc)
    check('current_summary_copies_consistent', cov['semantic_integration'] == summary and cov['patch08_delta'] == meta['patch08_continuation'] == delta)
    check('aggregate_QC_content_binding', qc['reviewed_content_candidate_revision'] == 4 and qc['reviewed_content_candidate_manifest_sha256'] == CONTENT_MANIFEST_SHA)
    check('all_QC_core_hash_maps_consistent', qc['source_content_sha256'] == release['source_content_sha256'] == receipt['source_content_sha256'])
    for rel, digest in qc['source_content_sha256'].items():
        check('QC_core_hashes_bound_to_reviewed_candidate', rel in before and before[rel]['sha256'] == digest == sha(S/rel), rel)
    reports = {}
    for r in qc['reviewed_component_reports']:
        p = use(resolve(r['path']))
        body = readj(p)
        reports[r['component']] = body
        check('component_report_link_hash_and_status', sha(p) == r['sha256'] and body['status'] == r['status'], r['component'])
    check('all_four_QC_components_present', set(reports) == {'character', 'semantic', 'integrity', 'packaging'})
    check('source_limits_and_no_whole_book_promotion', all(qc[k] is False for k in ['all_source_words_and_controls_changed', 'all_2054_pages_independently_reread', 'every_semantic_interpretation_independently_reread', 'whole_book_independent_Pro_QC', 'pure_matn_certification', 'canonical_identity_or_grade_certification', 'bank_ready', 'publication_performed']))
    check('final_delta_link_qualified', EP+'independent_qc/integrity/FINAL_DELTA_REVIEW.json' in qc['final_status_metadata_verification'])
    check('final_release_integrity_scope', release['engineering_QC_report_sha256'] == CONTENT_REPORT_SHA and release['bank_ready'] is False and release['publication_performed'] is False and validation['content_candidate_revision'] == 4)

    observations = readjl(E/'independent_qc/semantic/actual_image_observations.jsonl')
    page_keys = {(r['source_volume'], r['pdf_page']) for r in observations}
    scope = reports['semantic']['manual_scope']
    reported_pages = {(int(k[-2:]), n) for k, pages in scope['displayed_page_numbers'].items() for n in pages}
    check('semantic_targeted_page_scope_exactly_97', len(observations) == len(page_keys) == scope['pdf_pages_actually_displayed'] == 97 and page_keys == reported_pages)
    for r in observations:
        p = use(resolve(r['path']))
        check('semantic_targeted_observation_image_binding', r['displayed'] is True and sha(p) == r['sha256'] and 'no full-character verification' in r['inspection_scope'], [r['source_volume'], r['pdf_page']])
    check('semantic_manual_scope_qualifications_preserved', scope['original_new_rows_read'] == 950 and scope['final_correction_rows_read'] == 139 and scope['all_selected_rows_read'] == 1089 and scope['original_new_rows_not_manually_read'] == 15887 and scope['pdf_pages_not_displayed'] == 1957)
    check('character_scope_copied_exactly', qc['independent_character_scope'] == reports['character']['scope'] and qc['independent_character_scope']['actually_read_unique_pages'] == 27 and qc['independent_character_scope']['actual_full_page_views'] == 13 and qc['independent_character_scope']['localized_target_pages'] == 14)
    metrics['targeted_semantic_PDF_pages'] = len(page_keys)
    metrics['targeted_semantic_pages_by_volume'] = dict(collections.Counter(v for v, p in page_keys))
    metrics['independent_character_scope'] = {'unique_pages': 27, 'full_pages': 13, 'localized_pages': 14}

    uncertainties = readjl(S/'continuation/integration/semantic_uncertainties.jsonl')
    current_unc = readjl(S/'continuation/integration/semantic_uncertainty_current_status.jsonl')
    cases = readjl(E/'independent_qc/semantic/case_observations.jsonl')
    byid = {r.get('uncertainty_id') or r.get('exception_id'): r for r in uncertainties}
    caseids = {r['uncertainty_id'] for r in cases}
    check('all_32_source_cases_retained_and_independently_reported', len(uncertainties) == len(current_unc) == len(cases) == len(byid) == len(caseids) == 32 and caseids == set(byid))
    for r in current_unc:
        check('no_source_uncertainty_resolved_by_final_reporting', r['uncertainty_id'] in caseids and r['current_semantic_uncertainty_resolved'] is False and r['investigation_complete'] is True, r['uncertainty_id'])
    for r in cases:
        original = byid[r['uncertainty_id']]
        check('case_source_spans_and_actual_page_scope', r['source_volume'] == original['source_volume'] and r['source_spans'] == original['source_spans'] and all((r['source_volume'], p) in page_keys for p in r['pdf_pages_actually_displayed']), r['uncertainty_id'])
    check('retained_case_counts_in_reports', qc['retained_investigated_semantic_source_uncertainties'] == rem['retained_investigated_semantic_source_uncertainties'] == reports['semantic']['findings']['source_limited_uncertainties_retained'] == scope['uncertainty_cases_read'] == 32 and reports['semantic']['findings']['source_limited_uncertainties_resolved'] == 0)
    check('character_limit_and_empty_queues_accurate', qc['retained_character_partial_pages'] == {'1': [962], '2': []} and cov['current_character_review_partition']['full_pages'] == 2053 and cov['current_character_review_partition']['partial_pages'] == 1 and rem['unattempted_original_pages'] == resume['unattempted_character_pages'] == rem['unclassified_lexical_intervals'] == qc['remaining_unclassified_lexical_intervals'] == 0)
    metrics['retained_source_uncertainties'] = len(byid)

    readme = use(S/'README.md').read_text(encoding='utf8')
    check('README_and_patch_report_identical', sha(S/'README.md') == sha(S/(EP+'patch08_report.md')))
    check('README_semantic_scope_97_targeted_pages', '**97 original PDF pages**' in readme and 'It does not claim an independent reread of every semantic row or all 2,054 pages.' in readme)
    table = re.findall(r'^\| `([^`]+)` \| ([^|]+) \| (.+) \|$', readme, re.M)
    check('README_lists_exactly_all_32_source_cases', len(table) == 32 and {r[0] for r in table} == caseids)
    for uid, loc, note in table:
        row = byid[uid]
        expected = f"V{row['source_volume']}: "+'; '.join(f"{sp['story']} CP{sp['cp_start']}–{sp['cp_end']}" for sp in row['source_spans'])
        check('README_source_case_CP_locations_exact', loc.strip() == expected and bool(note.strip()), uid)
    check('README_no_bank_publication_or_pure_matn_claim', '**No bank upload, repository write, registration or publication was performed.**' in readme and 'bank-specific adapter/registration work remains separate' in readme and 'not proof that every interpretation has received independent manual review' in readme)
    check('README_distinguishes_historical_authority', 'ledger SHA-256 plus 1-based row ordinal' in readme and 'zero-width semantic annotation' in readme and 'HISTORICAL_CODE_RESOLUTION.json' in readme)

    new_sem = readjl(S/(EP+'integration/new_semantic_decisions.jsonl'))
    expected_changes = [{'change': 'patch08_completion', 'version': VERSION, 'summary': delta, 'source_text_changed': False}]
    expected_changes += [{'change': 'additive_exact_source_semantic_interpretation', 'version': VERSION, 'decision_id': r['decision_id'], 'source_volume': r['source_volume'], 'story': r['story'], 'cp_start': r['cp_start'], 'cp_end': r['cp_end'], 'source_text_changed': False} for r in new_sem]
    expected_corrections = []
    for name in ['character_region_corrections', 'character_review_corrections']:
        expected_corrections += [{'version': VERSION, 'kind': name, 'source_text_changed': False, 'evidence': norm(r)} for r in readjl(E/'partial_review'/f'{name}.jsonl')]
    for kind, p in [('parent_reference_interpretation_refinement', E/'reference_refinement/semantic_correction_overlay.jsonl'), ('independent_semantic_QC_interpretation_correction', E/'qc_corrections/semantic_correction_overlay.jsonl')]:
        expected_corrections += [{'version': VERSION, 'kind': kind, 'source_text_changed': False, 'evidence': norm(r)} for r in readjl(p)]
    for rel, expected in [('changes_since_previous_checkpoint.jsonl', expected_changes), ('corrections.jsonl', expected_corrections)]:
        old = use(P/rel).read_bytes()
        new = use(S/rel).read_bytes()
        check('append_only_history_journal_exact_parent_prefix', new.startswith(old), rel)
        suffix = [json.loads(line) for line in new[len(old):].splitlines() if line.strip()]
        check('journal_suffix_exact_qualified_changes', suffix == expected, rel)
        metrics[rel+'_new_rows'] = len(suffix)
    check('journal_and_QC_correction_counts', len(new_sem) == 16976 and len(expected_corrections) == 298 and delta['semantic_interpretations_corrected_after_QC'] == qc['semantic_interpretations_corrected_after_QC'] == 63)

    oldline = readj(P/'checkpoint_lineage.json')
    lineage = readj(S/'checkpoint_lineage.json')
    oldprior = oldline['prior_continuation_checkpoints']
    check('lineage_prior_chain_preserved', lineage['prior_continuation_checkpoints'][:-1] == oldprior and len(lineage['prior_continuation_checkpoints']) == len(oldprior)+1)
    check('lineage_exact_immediate_parent', lineage['prior_continuation_checkpoints'][-1] == {'version': 'v2_cp016_patch07', 'zip_bytes': 2083816792, 'zip_sha256': PARENT_SHA, 'manifest_sha256': sha(P/'MANIFEST.json')} and lineage['immediate_parent_zip_sha256'] == PARENT_SHA and lineage['current_version'] == VERSION and lineage['old_versions_modified'] is False)
    changed_lineage = {x['path'] for x in diff(oldline, lineage)}
    check('lineage_only_current_identity_updates', changed_lineage <= {'$.prior_continuation_checkpoints', '$.current_version', '$.immediate_parent_zip_sha256', '$.current_continuation_note'})

    oldlogs = readj(P/'logs_index.json')
    logs = readj(S/'logs_index.json')
    check('existing_log_path_order_preserved', [r['path'] for r in logs['files']] == [r['path'] for r in oldlogs['files']])
    for a, b in zip(oldlogs['files'], logs['files']):
        check('old_log_fields_preserved_except_current_hash_rowcount', {k: v for k, v in a.items() if k not in ['sha256', 'rows']} == {k: v for k, v in b.items() if k not in ['sha256', 'rows']}, a['path'])
    for k, v in oldlogs.items():
        if k not in ['scope', 'files']:
            check('historical_log_sections_preserved', logs.get(k) == v, k)
    for section in ['files', 'patch08_evidence_files']:
        for r in logs[section]:
            p = resolve(r['path'])
            exists = p.is_file()
            check('indexed_log_evidence_path_and_hash', exists and sha(p) == r['sha256'], [section, r['path']])
            if exists:
                use(p)
                if 'bytes' in r:
                    check('indexed_log_evidence_size', p.stat().st_size == r['bytes'], r['path'])
                if section == 'files' and p.suffix == '.jsonl':
                    with p.open('rb') as f:
                        count = sum(bool(line.strip()) for line in f)
                    check('current_log_JSONL_row_counts', r.get('rows') == count, r['path'])
    check('current_log_links_and_bank_preflight', logs['patch08_current_view_root'] == EP.rstrip('/') and logs['patch08_QC_report'] == 'QC_REPORT.json' and resolve(rem['bank_import_preflight']).is_file() and rem['bank_adapter_and_local_reader_validation_complete'] is False)
    metrics['existing_log_paths_validated'] = len(logs['files'])
    metrics['patch08_log_evidence_entries_validated'] = len(logs['patch08_evidence_files'])

    for r in list(inputs.values()):
        p = Path(r['path'])
        check('delta_review_inputs_stable', p.is_file() and p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], r['path'])
    failed = {k: v for k, v in checks.items() if v['failures']}
    status = 'pass_final_status_and_documentation_delta' if not failed else 'requires_correction'
    result = {
        'audit_id': 'patch08-final-status-documentation-delta', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': status,
        'content_candidate_revision': 4, 'content_candidate_manifest_sha256': CONTENT_MANIFEST_SHA, 'immutable_content_REPORT_sha256': CONTENT_REPORT_SHA,
        'final_preparation_receipt': EP+'release_documentation/FINAL_RELEASE_PREPARED.json', 'final_preparation_receipt_sha256': PREPARED_SHA,
        'audit_script_sha256': sha(Path(__file__)), 'metrics': metrics, 'check_categories': len(checks), 'assertion_evaluations': sum(r['evaluations'] for r in checks.values()),
        'failures': failed, 'checks': checks, 'status_document_diffs': status_diffs, 'unchanged_core_files': unchanged,
        'bound_inputs': sorted(inputs.values(), key=lambda x: x['path']),
        'scope': 'Bounded verification of reporting/status changes, immutable content/report hashes, journal prefixes and suffixes, lineage, log references and exact reported QC scope; no repeated whole-content or manual textual review.',
        'semantic_scope_statement': '97 distinct original PDF pages have targeted semantic observation records (59 V1, 38 V2); this does not add full-page character credit. All 32 source-limited cases remain unresolved after completed investigation.',
        'post_logs_snapshot_artifacts': ['continuation/patch08/release_documentation/FINAL_RELEASE_PREPARED.json', EP+'independent_qc/integrity/audit_final_delta.py', EP+'independent_qc/integrity/FINAL_DELTA_REVIEW.json', EP+'independent_qc/integrity/FINAL_DELTA_HANDOFF.json'],
        'post_logs_snapshot_note': 'The retained final-preparation receipt and this final delta evidence postdate the logs snapshot; the forthcoming freeze and internal archive manifest are the exhaustive member inventory.',
        'immutable_content_report_modified': False, 'source_content_modified_by_this_audit': False, 'manual_textual_QC_claimed': False, 'bank_ready_claimed': False, 'publication_performed': False,
        'archive_verification_remaining': 'The actual freeze, archive/part/member verification and portable delivery checks remain the packaging gate; this report does not claim they have run.'
    }
    (Q/'FINAL_DELTA_REVIEW.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    handoff = {'status': status, 'content_candidate_revision': 4, 'final_delta_review_sha256': sha(Q/'FINAL_DELTA_REVIEW.json'), 'immutable_content_REPORT_sha256': sha(Q/'REPORT.json'), 'final_preparation_receipt_sha256': PREPARED_SHA, 'source_content_unchanged': not checks['all_reviewed_core_files_byte_identical']['failures'], 'all_delta_audit_writes_complete': True, 'no_more_writes_planned_before_freeze': True, 'ready_for_authorized_freeze_and_packaging': not failed, 'failures': {k: r['failures'] for k, r in failed.items()}, 'metrics': metrics}
    (Q/'FINAL_DELTA_HANDOFF.json').write_text(json.dumps(handoff, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'status': status, 'checks': len(checks), 'assertions': result['assertion_evaluations'], 'failures': handoff['failures'], 'metrics': metrics, 'final_delta_review_sha256': handoff['final_delta_review_sha256'], 'all_writes_complete': True}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
