#!/usr/bin/env python3
"""Register the source-bound Japanese Fadael QC edition without merging reports.

The first run may stage the exact completed workspace through --workspace.
Subsequent runs reproduce the same records entirely from the local source archive.
Repository narration grouping is a separately reviewed, additive sidecar.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from build_reader import local
from current_provenance import apply_policy, classification, load_policy
from material_registry import (SOURCE_IMPORT_DECISION, checked_supporting_files,
                               normalized_projection, publication)
from register_material import register


SLUG = 'ja-fadael-2-tuwaijri-1438-qc-v1'
PREFIX = 'materials/' + SLUG + '/'
ARCHIVE = PREFIX + 'source-archive/'
BOOK = 'fadael'
EDITION = 'pdf-09a7f220e7bc-qc-v1'
TITLE = '諸々の徳（ハディース集）②'
SOURCE_URL = 'https://islamhouse.com/ja/main'
PDF_PATH = PREFIX + 'source.pdf'
PDF_SHA256 = '09a7f220e7bcf5152520913de57031bb840c80367566cfa71a61ded20bd6acde'
ORIGINAL_JSON = ARCHIVE + 'output/ja_ketab_elfadael/ja_ketab_elfadael_pages.json'
ORIGINAL_JSON_SHA256 = 'd8c583cf6826370d0b540cd264359cb44287162e07758298bf40b06719ac86df'
CORRECTED_JSON = ARCHIVE + 'qc_v1/output/ja_ketab_elfadael_corrected.json'
CORRECTED_JSON_SHA256 = '128792d3b643fdc4be7584fbdad9351348abfb4353d5bf217e90dc476b096de3'
REFERENCE_MAP = ARCHIVE + 'bank_import/work/source_reference_map.json'
REFERENCE_MAP_SHA256 = 'd5068489d348fa94debcc5e50d731aa0f066a46633d7966fb9d45e46fe04f16a'
PRESERVATION = PREFIX + 'preservation-manifest.json'
INTERMEDIATES = PREFIX + 'extraction-intermediates.zip'
INTERMEDIATES_MANIFEST = PREFIX + 'extraction-intermediates-manifest.json'
CONTEXT = PREFIX + 'source-context.json'
NOTES = PREFIX + 'footnotes.json'
AUDIT = PREFIX + 'integration-audit.json'
QC_REPORT = ARCHIVE + 'qc_v1/output/ja_ketab_elfadael_QC_report.json'
CORRECTIONS = ARCHIVE + 'qc_v1/output/ja_ketab_elfadael_corrections.json'
RECORDS = PREFIX + 'records.jsonl'
MANIFEST = PREFIX + 'manifest.json'
SESSION_MODEL_LABEL = 'GPT-6 Astra Pro'
PRIMARY_NAMES = {'bukhari': 'Sahih al-Bukhari', 'muslim': 'Sahih Muslim',
                 'tirmidhi': 'Jami al-Tirmidhi', 'abudawud': 'Sunan Abi Dawud'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def text_sha(text):
    return sha(text.encode('utf-8'))


def write_bytes(path, raw):
    """An identical repeat does not replace the file or change its mtime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == raw:
        return
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)


def write_json(path, value):
    write_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def write_rows(path, rows):
    write_bytes(path, b''.join((json.dumps(row, ensure_ascii=False, sort_keys=True,
                                         separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
                               for row in rows))


def descriptor(root, relative):
    path = local(root, relative)
    raw = path.read_bytes()
    return {'path': relative, 'sha256': sha(raw), 'size_bytes': len(raw)}


def read_checked(root, relative, expected):
    raw = local(root, relative).read_bytes()
    if sha(raw) != expected:
        raise ValueError('Pinned source bytes differ: ' + relative)
    return json.loads(raw)


def is_intermediate(relative):
    return relative.startswith(('work/ja_ketab_elfadael/raw/', 'work/ja_ketab_elfadael/ocr/')) or relative in (
        'work/ja_ketab_elfadael/run_ocr.py', 'work/ja_ketab_elfadael/build_extraction.py',
        'work/ja_ketab_elfadael/tessdata/models.json')


def is_excluded_web_response(relative):
    return relative.startswith('qc_v1/work/') and relative.rsplit('/', 1)[-1] not in (
        'reference_targets.json', 'reference_urls.json')


def retired_loose_path(relative):
    if not relative.startswith(ARCHIVE):
        return False
    original = relative[len(ARCHIVE):]
    return is_intermediate(original) or is_excluded_web_response(original)


def deterministic_intermediates(files):
    """Bundle original bytes with sorted names and a fixed ZIP timestamp/mode."""
    manifest = {'schema': 'japanese-fadael-extraction-intermediates-v1',
                'source_pdf_sha256': PDF_SHA256, 'source_bytes_unchanged': True,
                'files': [{'member': name, 'sha256': sha(raw), 'size_bytes': len(raw)}
                          for name, raw in sorted(files.items())]}
    manifest_raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in [('MANIFEST.json', manifest_raw), *sorted(files.items())]:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue(), manifest_raw


def verify_intermediates(root):
    manifest_raw = local(root, INTERMEDIATES_MANIFEST).read_bytes()
    manifest = json.loads(manifest_raw)
    entries = manifest['files']
    expected = ['MANIFEST.json'] + [entry['member'] for entry in entries]
    if len(expected) != len(set(expected)):
        raise ValueError('Duplicate intermediate member')
    with zipfile.ZipFile(local(root, INTERMEDIATES)) as archive:
        if archive.namelist() != expected or archive.read('MANIFEST.json') != manifest_raw:
            raise ValueError('Intermediate ZIP member manifest differs')
        for entry in entries:
            name = entry['member']
            if not is_intermediate(name) or any(part in ('', '.', '..') for part in name.split('/')):
                raise ValueError('Unexpected intermediate archive member: ' + name)
            raw = archive.read(name)
            if len(raw) != entry['size_bytes'] or sha(raw) != entry['sha256']:
                raise ValueError('Intermediate member bytes differ: ' + name)
    return entries


def stage_workspace(root, workspace):
    """Copy only the completed source, extraction and QC evidence, byte for byte."""
    workspace = Path(workspace).resolve()
    required = {
        'upload/ja_ketab_elfadael.pdf': PDF_SHA256,
        'output/ja_ketab_elfadael/ja_ketab_elfadael_pages.json': ORIGINAL_JSON_SHA256,
        'qc_v1/output/ja_ketab_elfadael_corrected.json': CORRECTED_JSON_SHA256,
        'bank_import/work/source_reference_map.json': REFERENCE_MAP_SHA256,
    }
    for relative, expected in required.items():
        if sha(local(workspace, relative).read_bytes()) != expected:
            raise ValueError('Workspace source does not match pinned edition: ' + relative)
    old = json.loads(local(root, PRESERVATION).read_text(encoding='utf-8')) if local(root, PRESERVATION).exists() else {}
    old_by_origin = {entry.get('original_workspace_path'): entry for entry in old.get('files', [])}
    files = set(required)
    for directory in ('output/ja_ketab_elfadael', 'qc_v1/output', 'qc_v1/reviews',
                      'work/ja_ketab_elfadael/reviews'):
        for path in local(workspace, directory).glob('*'):
            if path.is_file() and path.suffix.lower() in ('.json', '.txt', '.tsv', '.pdf', '.docx'):
                files.add(path.relative_to(workspace).as_posix())
    files.update(('qc_v1/work/reference_targets.json', 'qc_v1/work/reference_urls.json'))
    intermediates = {}
    for directory in ('work/ja_ketab_elfadael/raw', 'work/ja_ketab_elfadael/ocr'):
        for path in local(workspace, directory).glob('*'):
            if path.is_file() and path.suffix.lower() in ('.json', '.txt', '.tsv'):
                intermediates[path.relative_to(workspace).as_posix()] = path.read_bytes()
    for relative in ('work/ja_ketab_elfadael/run_ocr.py', 'work/ja_ketab_elfadael/build_extraction.py',
                     'work/ja_ketab_elfadael/tessdata/models.json'):
        if local(workspace, relative).is_file():
            intermediates[relative] = local(workspace, relative).read_bytes()
    for relative, raw in intermediates.items():
        previous = old_by_origin.get(relative)
        if previous and (previous['sha256'] != sha(raw) or previous['size_bytes'] != len(raw)):
            raise ValueError('Changed intermediate source bytes: ' + relative)
    if local(root, INTERMEDIATES_MANIFEST).exists():
        prior_members = {entry['member']: entry for entry in json.loads(local(root, INTERMEDIATES_MANIFEST).read_bytes())['files']}
        if set(prior_members) != set(intermediates) or any(
                sha(raw) != prior_members[name]['sha256'] for name, raw in intermediates.items()):
            raise ValueError('Refusing to replace previously archived intermediate source bytes')
    preserved = []
    for relative in sorted(files):
        raw = local(workspace, relative).read_bytes()
        target = PDF_PATH if relative == 'upload/ja_ketab_elfadael.pdf' else ARCHIVE + relative
        destination = local(root, target)
        if destination.exists() and destination.read_bytes() != raw:
            raise ValueError('Refusing to overwrite changed archived source bytes: ' + target)
        write_bytes(destination, raw)
        preserved.append({**descriptor(root, target), 'original_workspace_path': relative,
                          'source_bytes_unchanged': True})
    zip_raw, zip_manifest_raw = deterministic_intermediates(intermediates)
    write_bytes(local(root, INTERMEDIATES), zip_raw)
    write_bytes(local(root, INTERMEDIATES_MANIFEST), zip_manifest_raw)
    verify_intermediates(root)
    preserved.extend([descriptor(root, INTERMEDIATES), descriptor(root, INTERMEDIATES_MANIFEST)])
    new_paths = {entry['path'] for entry in preserved}
    # Retire only loose intermediates now verified in the ZIP and external tool
    # response snapshots explicitly excluded from public distribution.
    excluded = []
    bundled = {entry['member']: entry for entry in json.loads(zip_manifest_raw)['files']}
    for entry in old.get('files', []):
        path = entry['path']
        if path in new_paths or not retired_loose_path(path):
            continue
        origin = path[len(ARCHIVE):]
        if is_intermediate(origin):
            if origin not in bundled or bundled[origin]['sha256'] != entry['sha256']:
                raise ValueError('Loose evidence cannot be retired before exact ZIP preservation: ' + path)
        else:
            excluded.append({'original_workspace_path': origin,
                             'reason': 'Raw external web tool response/full retrieved third-party page; URLs and review summaries are retained.'})
        target = local(root, path)
        if target.exists():
            target.unlink()
    excluded_names = sorted({path.name for path in local(workspace, 'qc_v1/work').glob('*.json')
                             if is_excluded_web_response(path.relative_to(workspace).as_posix())})
    write_json(local(root, PRESERVATION), {
        'schema': 'japanese-fadael-preservation-v2', 'original_pdf_sha256': PDF_SHA256,
        'original_json_sha256': ORIGINAL_JSON_SHA256, 'corrected_json_sha256': CORRECTED_JSON_SHA256,
        'reference_map_sha256': REFERENCE_MAP_SHA256,
        'scope': 'Exact original/corrected source files and required QC/reference summaries are individual files. Native/OCR extraction intermediates are byte-preserved in one deterministic ZIP. Raw external web-response snapshots/full retrieved third-party pages are not republished.',
        'intermediate_archive': {'path': INTERMEDIATES, 'manifest_path': INTERMEDIATES_MANIFEST,
                                 'member_count': len(intermediates), 'zip_timestamp': '1980-01-01T00:00:00'},
        'excluded_external_response_filenames': excluded_names,
        'other_exclusions': 'Reproducible page PNGs, temporary font experiments, downloaded OCR models, personal Library upload responses and duplicate delivery ZIP mirrors. Primary URLs and reference reviews remain; historical raw-response identifiers inside archived audit metadata are not runtime source links.',
        'files': preserved,
    })


def verify_preservation(root):
    evidence = json.loads(local(root, PRESERVATION).read_text(encoding='utf-8'))
    files = evidence['files']
    checked_supporting_files(root, {'supporting_files': files}, PRESERVATION)
    verify_intermediates(root)
    by_path = {entry['path']: entry for entry in files}
    if len(by_path) != len(files):
        raise ValueError('Duplicate preservation path')
    for relative, expected in ((PDF_PATH, PDF_SHA256), (ORIGINAL_JSON, ORIGINAL_JSON_SHA256),
                               (CORRECTED_JSON, CORRECTED_JSON_SHA256), (REFERENCE_MAP, REFERENCE_MAP_SHA256)):
        if by_path.get(relative, {}).get('sha256') != expected:
            raise ValueError('Pinned source missing from archive manifest: ' + relative)
    return files


def validate_source(source, original, reference_map):
    expected_notes = set(range(1, 59))
    occurrences = source['occurrences']
    notes = {note['note_number']: note for note in source['footnotes']}
    units = {unit['unit_id']: unit for page in source['pages'] for unit in page['source_units']}
    original_units = {unit['unit_id']: unit for page in original['pages'] for unit in page['source_units']}
    if len(source['pages']) != 25 or len(units) != 621 or len(notes) != 58 or set(notes) != expected_notes:
        raise ValueError('Source page/unit/note coverage differs')
    if len(occurrences) != 57 or len({row['occurrence_id'] for row in occurrences}) != 57:
        raise ValueError('Source occurrence coverage differs')
    if {row['locator_note_number'] for row in occurrences} != expected_notes - {19}:
        raise ValueError('Translator note must not become a hadith occurrence')
    if notes[19]['kind'] != 'translator_commentary':
        raise ValueError('Translator commentary role differs')
    if set(units) != set(original_units) or any(unit['original_text'] != original_units[key]['text'] for key, unit in units.items()):
        raise ValueError('Original source unit wording or IDs were lost')
    body = {key for key, unit in units.items() if unit['kind'] == 'body_line'}
    covered = [key for row in occurrences for key in row['source_unit_ids']]
    if len(covered) != 376 or len(set(covered)) != 376 or set(covered) != body:
        raise ValueError('Occurrence/body-line coverage is not disjoint and exhaustive')
    if Counter(number for row in occurrences for number in row['linked_note_numbers']) != Counter(expected_notes):
        raise ValueError('Every source note must be linked exactly once')
    if reference_map['source_json']['sha256'] != CORRECTED_JSON_SHA256:
        raise ValueError('Reference map is not bound to the final corrected source')
    if set(reference_map['occurrences']) != {row['occurrence_id'] for row in occurrences}:
        raise ValueError('Reference map occurrence IDs differ')
    for row in occurrences:
        mapped = reference_map['occurrences'][row['occurrence_id']]
        if mapped['provenance']['corrected_text_sha256'] != text_sha(row['corrected_text']):
            raise ValueError('Reference map text hash differs: ' + row['occurrence_id'])
        if mapped['provenance']['original_text_sha256'] != text_sha(row['original_text']):
            raise ValueError('Reference map original text hash differs: ' + row['occurrence_id'])
        if row['ai_translation'] != (True if row['locator_note_number'] in (47, 50) else 'unknown'):
            raise ValueError('Unexpected translation-origin source flag')
    return notes, units


def printed_narrator(text):
    # The one source-local enumeration prefix remains in the translation.
    match = re.match(r'^(?:[0-9０-９]+[－\-]\s*)?([^「：（]+)（彼(?:ら|女)?にアッラーのご満悦あれ）', text)
    if match is None:
        return {'name': None, 'null_reason': 'Reliable printed narrator prefix not found'}
    return {'name': match[1], 'as_printed': match[1], 'source_span_codepoints': list(match.span(1)),
            'scope': 'Exact Japanese introductory narrator name; no Arabic normalization or full isnad inferred'}


def references_for(mapped, note):
    items = []
    for original in mapped['primary_references']:
        item = copy.deepcopy(original)
        item.update({'collection': PRIMARY_NAMES[item['collection_id']],
                     'source_citation': item['exact_citation'],
                     'scope': item['relationship_to_occurrence'],
                     'numbering_system': 'Corrected primary collection citation; separately checked Sunnah.com variants retained',
                     'is_accepted_canonical_identity': False,
                     'source_path': CORRECTED_JSON,
                     'source_note_id': note['note_id']})
        items.append(item)
    return {'items': items,
            'original_source_note': note['original_text'], 'corrected_source_note': note['text'],
            'source_wording_attribution': mapped['source_wording_attribution'],
            'preferred_reference_key': mapped['preferred_reference_key'],
            'original_reference_keys': mapped['original_reference_keys'],
            'corrected_reference_keys': mapped['corrected_reference_keys'],
            'canonical_mapping_status': 'primary_content_and_narrator_correspondence_checked_repository_identity_unassigned',
            'reference_map_path': REFERENCE_MAP,
            'reference_map_pointer': '/occurrences/' + note['note_id'].replace('_note_', '_occ_note_'),
            'scope_note': 'Primary correspondence, same-report variants and broader supporting parallels remain distinct; number equality is not a canonical identity decision.'}


def make_record(occurrence, index, source, reference_map, notes, units):
    identity = occurrence['occurrence_id']
    mapped = reference_map['occurrences'][identity]
    n = occurrence['locator_note_number']
    note = notes[n]
    ai = occurrence['ai_translation'] is True
    pointer = '/occurrences/' + str(index)
    all_changes = mapped['provenance']['all_correction_ids']
    source_footnotes = [copy.deepcopy(notes[number]) for number in occurrence['linked_note_numbers']]
    for footnote in source_footnotes:
        footnote.update({'source_path': CORRECTED_JSON, 'source_pdf_path': PDF_PATH,
                         'source_sha256': CORRECTED_JSON_SHA256,
                         'role': 'translator_commentary' if footnote['note_number'] == 19 else 'source_reference',
                         'included_in_hadith_text': False})
    commentary = [footnote['text'] for footnote in source_footnotes if footnote['note_number'] == 19]
    provenance = {
        'origin': 'ai_translation' if ai else 'unknown',
        'ai_translation': True if ai else 'unknown',
        'label': 'AI-assisted editorial revision' if ai else 'Original source translation provenance unknown',
        'basis': 'Explicit AI-assisted revision/restoration in C07/C08 of the corrected edition' if ai else 'Inherited published Japanese translation; source flag remains unknown and owner Human display default is separate',
        'human_involvement': 'original_named_translator; no human review of this corrected candidate established',
        'original_source_ai_translation': 'unknown',
        'new_translation_generated': ai, 'human_review': False,
        'translation_sha256': text_sha(occurrence['corrected_text']),
        'evidence_ids': [CORRECTED_JSON + '#' + pointer, CORRECTIONS],
        'scope_note': 'The original published text remains separately preserved. Only the explicitly logged clauses in occurrences 47/50 are new AI-produced translation; OCR and AI review do not classify other translations as AI.',
    }
    if ai:
        ai_changes = [change for change in source['correction_log']
                      if change['change_id'] in all_changes and change['contains_ai_generated_translation']]
        provenance['source_declaration'] = {
            'classification': 'ai',
            'evidence': CORRECTED_JSON + '#' + pointer + '; explicit AI-generated changes ' + ','.join(change['change_id'] for change in ai_changes),
            'scope': 'Corrected occurrence contains the explicitly identified AI-revised clause; inherited source text is not newly attributed to AI',
        }
        provenance['ai_generation'] = {
            'model': SESSION_MODEL_LABEL, 'model_basis': 'session-declared model label',
            'backend_model_id': None, 'reasoning_effort': None,
            'backend_metadata_status': 'not_exposed', 'human_review': False,
            'translation_sha256': text_sha(occurrence['corrected_text']),
            'reviewer': 'ChatGPT QC agents identified in the preserved source review files',
            'review_effort': 'not_exposed', 'reviewed_bytes': len(occurrence['corrected_text'].encode('utf-8')),
            'reviewed_bytes_scope': 'UTF-8 size of the selected corrected occurrence whose source pages and final rendering were reviewed; not a claim of independent per-codepoint certification',
            'evidence': mapped['review_evidence'],
            'changes': [{'change_id': change['change_id'], 'before': change['before'],
                         'after': change['after'], 'after_utf8_sha256': text_sha(change['after']),
                         'source_unit_ids': change['unit_ids']} for change in ai_changes],
        }
    selected_refs = references_for(mapped, note)
    secondaries = [copy.deepcopy(ref) for ref in reference_map['notes'][str(n)]['corrected_references']
                   if ref['scope'] == 'secondary_edition']
    for ref in secondaries:
        ref['verification_status'] = 'not_independently_verified'
        ref['is_canonical_primary_number'] = False
    selected_refs['secondary_edition_references'] = secondaries
    grade_match = re.match(r'^(良好(?:かつ真正)?な伝承。)', note['text'])
    grade_claims = [{'text': grade_match[1], 'grader': None, 'source_note_id': note['note_id'],
                     'scope': 'Exact source assessment, not a new independent grading'}] if grade_match else []
    return {
        'id': identity, 'source_id': SLUG, 'language': 'ja', 'source_language_code': 'ja',
        'book_key': BOOK, 'edition': EDITION, 'show_in_html_hadith': True,
        'record_type': 'companion_report' if n == 55 else 'hadith_excerpt',
        'content_kind': 'source_bound_report_with_narrator_framing',
        'title': occurrence['subsection'] or occurrence['section'],
        'text': {'arabic': None, 'translation': occurrence['corrected_text']},
        'source': {
            'name': TITLE, 'title': TITLE, 'url': SOURCE_URL, 'record_url': None,
            'url_scope': 'Publisher website printed in the book; not a PDF download URL',
            'original_source_id': source['source_id'], 'original_record_id': identity,
            'editorial_edition_id': source['edition_id'], 'edition_label': source['edition_label_ja'],
            'edition_kind': 'declared_editorially_corrected_source_version',
            'original_pdf': copy.deepcopy(source['source']),
            'original_text': occurrence['original_text'],
            'original_text_sha256': text_sha(occurrence['original_text']),
            'corrected_text_sha256': text_sha(occurrence['corrected_text']),
            'original_source_ai_translation': 'unknown',
            'body_correction_ids': occurrence['correction_ids'],
            'note_correction_ids': mapped['provenance']['note_correction_ids'],
            'all_correction_ids': all_changes,
            'corrected_source_path': CORRECTED_JSON, 'corrected_source_sha256': CORRECTED_JSON_SHA256,
            'original_source_path': ORIGINAL_JSON, 'original_source_sha256': ORIGINAL_JSON_SHA256,
            'corrected_source_pointer': pointer, 'preservation_manifest': PRESERVATION,
            'source_unit_ids': occurrence['source_unit_ids'],
        },
        'number': {'source_entry_id': f'note_{n:03d}', 'source_note_number': n,
                   'in_book': None, 'canonical': None, 'printed_hadith_number': None,
                   'numbering_system': 'Source footnote locator only; no independent printed hadith number'},
        'narrator': printed_narrator(occurrence['corrected_text']), 'isnad': None,
        'translator': {'name': source['bibliography']['translator_ja'],
                       'name_ar_as_printed': source['bibliography']['translator_ar'],
                       'evidence': ORIGINAL_JSON + '#/bibliography',
                       'scope': 'Original published translation credit; AI editorial clauses are separately identified'},
        'ai_translation': True if ai else 'unknown', 'translation_provenance': provenance,
        'commentary': {'arabic': None, 'translation': '\n\n'.join(commentary) or None,
                       'source_note_numbers': [19] if n == 20 else [],
                       'scope': 'Exact translator commentary, separate from hadith matn'},
        'footnotes': source_footnotes, 'references': selected_refs,
        'grading': {'grade': None, 'grader': None, 'as_printed_claims': grade_claims,
                    'scope': 'No overall grade or source-specific grader inferred'},
        'page': {'pdf': occurrence['pdf_pages'], 'printed': mapped['printed_pages'], 'sheet': None, 'row': None,
                 'scope': 'Original 25-page PDF and original printed page labels; corrected layout has different pagination'},
        'source_headings': [value for value in (occurrence['section'], occurrence['subsection']) if value],
        'topic_tags': [], 'editorial_tags': ['source:' + SLUG, 'edition:qc-corrected'],
        'source_locator': {'source_pdf_path': PDF_PATH, 'source_pdf_sha256': PDF_SHA256,
                           'source_path': CORRECTED_JSON, 'source_sha256': CORRECTED_JSON_SHA256,
                           'json_pointer': pointer, 'source_unit_ids': occurrence['source_unit_ids'],
                           'linked_note_numbers': occurrence['linked_note_numbers'],
                           'display_text_sha256': text_sha(occurrence['corrected_text']),
                           'original_text_sha256': text_sha(occurrence['original_text']),
                           'reference_map_path': REFERENCE_MAP},
        'extraction': {'method': 'embedded_pdf_text_with_tesseract_ocr_crosscheck_and_visual_page_review',
                       'ocr_used': True, 'is_excerpt': True,
                       'source_primary_method': source['processing']['primary_method'],
                       'new_ocr_performed_during_import': False},
        'review': {'status': 'source_visual_and_reference_qc_completed_with_declared_scope',
                   'ocr_qc': 'completed', 'independent_pro_qc': 'not_performed_on_final_repository_candidate',
                   'release_status': 'source_imported', 'release_eligible': False,
                   'certified_release_eligible': False, 'human_review': False,
                   'character_by_character_certified': False,
                   'translation_word_for_word_certified': False, 'independent_authenticity_grading': False,
                   'source_qc_report': QC_REPORT, 'reference_review': {**mapped['review_evidence'],
                       'path': ARCHIVE + mapped['review_evidence']['path']},
                   'actual_source_scope': {'pdf_pages': occurrence['pdf_pages'], 'unit_ids': occurrence['source_unit_ids'],
                       'book_pages': 25, 'book_source_units': 621, 'book_primary_reference_checks': 93},
                   'issues': copy.deepcopy(mapped['ambiguities']),
                   'scope_note': 'Completed source fidelity and primary subject/narrator checks are preserved. Publication and this importer do not confer independent final-candidate Pro certification.'},
        'source_defects': {'original_preserved': True, 'corrected_edition_change_ids': all_changes},
        'related_versions': [],
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                   'scope_note': 'Owner import authorization is not a publisher redistribution licence'},
    }


def material_descriptor(manifest):
    return {'adapter': 'records-v1', 'dataset_id': manifest['source_id'],
            'language': manifest['language'], 'book_key': manifest['book'], 'edition': manifest['edition'],
            'source_descriptor': copy.deepcopy(manifest['source']),
            'source_file': manifest['source']['path'], 'source_sha256': manifest['source']['sha256'],
            'canonical_records_path': manifest['records']['path'],
            'canonical_records_sha256': manifest['records']['sha256'],
            'publication': publication(manifest, MANIFEST)}


def project_records(root, rows, manifest):
    material = material_descriptor(manifest)
    policy = load_policy(root)
    projected = [apply_policy(normalized_projection(row, material, index), policy, registered_material=True)
                 for index, row in enumerate(rows)]
    if any(row['text']['translation'] != item['text_translation'] for row, item in zip(rows, projected)):
        raise ValueError('Material projection changed corrected source text')
    if policy and Counter(classification(item) for item in projected) != {'human': 55, 'ai': 2}:
        raise ValueError('Current owner provenance projection differs')
    return projected


def run(root, workspace=None):
    root = Path(root).resolve()
    if workspace is not None:
        stage_workspace(root, workspace)
    supporting = verify_preservation(root)
    source = read_checked(root, CORRECTED_JSON, CORRECTED_JSON_SHA256)
    original = read_checked(root, ORIGINAL_JSON, ORIGINAL_JSON_SHA256)
    reference_map = read_checked(root, REFERENCE_MAP, REFERENCE_MAP_SHA256)
    notes, units = validate_source(source, original, reference_map)
    records = [make_record(occurrence, index, source, reference_map, notes, units)
               for index, occurrence in enumerate(source['occurrences'])]
    # Preserve context as source units, not extra records or searchable matn.
    context = {'schema': 'japanese-fadael-source-context-v1', 'source_id': source['source_id'],
        'edition_id': source['edition_id'], 'source_json_path': CORRECTED_JSON,
        'source_json_sha256': CORRECTED_JSON_SHA256,
        'not_hadith_occurrences': True, 'show_in_html_hadith': False,
        'units': [dict(copy.deepcopy(unit), pdf_page=page['pdf_page'], printed_page=page['printed_page_visible'])
                  for page in source['pages'] for unit in page['source_units'] if unit['kind'] != 'body_line'],
        'translator_commentary_note_numbers': [19],
        'preservation_note': 'Includes front/back matter, headings, page labels, logos and all footnote lines. The full archive retains all 621 units; only 376 body lines form the 57 source occurrences.'}
    write_rows(local(root, RECORDS), records)
    write_json(local(root, CONTEXT), context)
    write_json(local(root, NOTES), source['footnotes'])
    register(root, PREFIX.rstrip('/'), 'ja', BOOK, EDITION, TITLE,
             'records.jsonl', 'source.pdf', source_url=SOURCE_URL,
             source_id=SLUG, replace=local(root, MANIFEST).exists())
    manifest = json.loads(local(root, MANIFEST).read_text(encoding='utf-8'))
    prior_publication = manifest['publication']
    japan = datetime.timezone(datetime.timedelta(hours=9))
    manifest['source'].update({'title_ja': TITLE, 'title_ar': source['bibliography']['title_ar'],
        'original_filename': source['source']['filename'], 'pdf_pages': 25,
        'url_scope': 'Publisher website as printed; not an asserted source download URL',
        'editorial_edition_id': source['edition_id'], 'edition_label_ja': source['edition_label_ja'],
        'metadata_path': CORRECTED_JSON, 'metadata_sha256': CORRECTED_JSON_SHA256,
        'publication_year_as_printed': source['bibliography']['year_as_printed'],
        'translation_credits': copy.deepcopy(source['bibliography'])})
    manifest['publication'].update({'authorized': True, 'decision': SOURCE_IMPORT_DECISION,
        'decision_date_japan': prior_publication.get('decision_date_japan') or datetime.datetime.now(japan).date().isoformat(),
        'authorization_basis': 'Owner requested corrected Japanese book upload to Hadith Bank, HTML integration and no duplicate existing narration groups.',
        'visibility': 'public', 'active_status': 'source_imported',
        'scope': '57 exact corrected source occurrences, original PDF and full original/corrected source archive; note 19 and front/back matter remain separate context.',
        'independent_qc_asserted': False, 'rights_clearance_asserted': False,
        'certified_release_eligible': False})
    manifest['source_partitions'] = {'source_units': 621, 'hadith_body_line_units': 376,
        'source_context_units': 245, 'reader_occurrences': 57, 'footnotes': 58,
        'source_reference_notes': 57, 'translator_commentary_notes': 1,
        'context_path': CONTEXT, 'notes_path': NOTES,
        'context_visible_in_hadith_html': False, 'context_indexed_as_hadith_matn': False}
    manifest['preserved_delivery'] = {'preservation_manifest': PRESERVATION,
        'original_pdf_sha256': PDF_SHA256, 'original_json_path': ORIGINAL_JSON,
        'corrected_json_path': CORRECTED_JSON, 'reference_map_path': REFERENCE_MAP,
        'source_bytes_unchanged': True, 'all_source_units_retained': True,
        'all_note_numbers_retained': True, 'original_and_corrected_versions_separate': True}
    projections = project_records(root, records, manifest)
    audit = {'schema': 'japanese-fadael-integration-audit-v1', 'material': SLUG,
        'source_id': source['source_id'], 'edition_id': source['edition_id'],
        'reader_occurrences': 57, 'original_pdf_pages': 25, 'source_units': 621,
        'body_line_units': 376, 'context_units': 245, 'source_notes': 58,
        'translator_commentary_notes': [19], 'primary_reference_links': 93,
        'unique_corrected_primary_reference_keys': 91, 'unverified_secondary_edition_references': 4,
        'source_ai_translation_counts': {'unknown': 55, 'true': 2},
        'current_origin_counts': dict(Counter(classification(item) for item in projections)),
        'ai_revised_note_numbers': [47, 50], 'new_translation_produced_during_import': False,
        'session_declared_model_for_prior_ai_revisions': SESSION_MODEL_LABEL,
        'backend_model_id': None, 'reasoning_effort': None, 'human_review': False,
        'canonical_identity_assigned_by_importer': False, 'source_occurrences_merged': False,
        'reader_grouping': 'Separate parent-owned hash-bound identity sidecar; never infer grouping from these numbers alone.',
        'evidence_packaging': {'loose_source_and_review_files': len(supporting),
            'intermediate_archive_path': INTERMEDIATES,
            'intermediate_member_count': len(verify_intermediates(root)),
            'raw_external_web_responses_published': False},
        'source_qc_scope': json.loads(local(root, QC_REPORT).read_text(encoding='utf-8'))['coverage'],
        'independent_final_repository_candidate_pro_qc': 'NOT_RUN', 'certified_release_eligible': False,
        'actual_import_validation': {'full_57_occurrence_id_coverage': True,
            'all_376_body_lines_once': True, 'all_58_notes_once': True,
            'exact_corrected_translation_preserved': True, 'all_original_source_unit_text_preserved': True,
            'native_pdf_plus_actual_ocr_evidence_preserved': True,
            'material_registry_projection': True, 'no_missing_source_arabic_fabricated': True},
        'outputs': [descriptor(root, path) for path in (RECORDS, CONTEXT, NOTES)]}
    write_json(local(root, AUDIT), audit)
    generated = [descriptor(root, path) for path in (PRESERVATION, CONTEXT, NOTES, AUDIT)]
    current = {item['path']: item for item in supporting + generated}
    # Preserve parent-owned sidecars and their descriptors on an idempotent rerun.
    for item in manifest.get('supporting_files', []):
        if item['path'] not in current and not retired_loose_path(item['path']):
            current[item['path']] = item
    manifest['supporting_files'] = [current[path] for path in sorted(current)]
    checked_supporting_files(root, manifest, MANIFEST)
    write_json(local(root, MANIFEST), manifest)
    return {'material': SLUG, 'records': len(records), 'records_path': RECORDS,
            'records_sha256': descriptor(root, RECORDS)['sha256'],
            'origin_counts': audit['current_origin_counts'], 'supporting_files': len(current),
            'source_units_preserved': 621, 'source_notes_preserved': 58,
            'publication_decision': SOURCE_IMPORT_DECISION, 'independent_certification': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workspace', type=Path, help='Initial staging directory containing the exact completed source/QC files')
    args = parser.parse_args(argv)
    try:
        result = run(args.root, args.workspace)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Japanese Fadael import failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    main()
