#!/usr/bin/env python3
"""Reproduce the owner-authorized Japanese reader subset from exact saved bytes.

Publication is a later owner decision. Original source/research holds remain in
the immutable archive and separate metadata; this importer never certifies QC.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile
from collections import Counter

from register_material import register

IMPORT = 'imports/japanese-research-v3-20261112'
ARCHIVE_HASH = '331d2973511301c6cd50d3e2a8612e135defda529e855b8b03894490005c01fa'
ARCHIVE_SIZE = 89158437
ARCHIVE_ROOT = 'Japanese_Hadith_Sayings_Reports_Research_v3_20261112_PARTIAL_HOLD'
OWNER_INSTRUCTION = 'continue integration into html , tell me after finish previous count and new count of hadtihs'
SOURCES = {
    'ja_hisn_2007': ('ja-hisn-2007-research-v3', 'hisn-al-muslim', 'ムスリムの砦', 'Hisn al-Muslim', 261),
    'ja_islam_message': ('ja-islam-message-research-v3', 'islam-message', 'イスラームのメッセージ', 'The Message of Islam', 306),
    'ja_otsuka_20230901': ('ja-otsuka-20230901-research-v3', 'otsuka-khutba', '大塚マスジド 金曜日礼拝ホトバ 要約 — 2023年9月1日', 'Otsuka Friday sermon summary', 9),
    'ja_tokyo_basic_2012': ('ja-tokyo-basic-2012-research-v3', 'basic-knowledge-of-islam', 'イスラームの基本知識', 'Basic Knowledge of Islam', 650),
}
SELECTION_HASHES = {
    'whole_record_display_selections.json': '67670a060e901c00af4cb74cb20f42eff2db1583a911e3945e46c8e9c00e92b8',
    'mixed_parent_display_selections.json': '7cfe049ec72b44fb0fe2045f3ce271f47cbd3c9a3212a17ec7147e8d8b6b3668',
    'whole_record_text_roles.json': '3c4079bfecd6cc52e5864ddc2b709d78f8591a47b133d734efd45496f9a53958',
}
COUNTERPART_HOLD = ('Original Arabic/source transcriptions and external Arabic/English witnesses remain in preserved research. '
                    'No source-bound language alignment approval is granted by this pending-review publication.')
REFERENCE_BINDINGS = {
    'ja_tokyo_basic_2012-r136:v3:c001': {
        'parent_record_id': 'ja_tokyo_basic_2012-r136',
        'selected_text_sha256': 'a4badc5757605dec52b9a8802d011ea36cc0c86ace920398f88fe4d7d7f35087',
        'evidence_id': 'tokyo-reports-turn256view0',
        'basis': 'The preserved Ibn Hisham witness explicitly describes the selected silence under insult (فلم يكلمه رسول الله). The original component omitted its evidence ID, while the parent collection link retains it.',
        'scope_limit': 'Description only, not legal tacit approval. Hamza subsequent action/dialogue is excluded; this binding does not independently verify every chronological detail.',
        'original_component_metadata_changed': False,
        'new_external_research_or_authenticity_grade': False,
    },
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')


def local(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Unsafe local source path')
    return path


def restore_archive(root):
    """Restore exact ZIP bytes from bounded transport parts; no source rewrite."""
    manifest = json.loads((root / IMPORT / 'preserved-delivery/archive-parts.json').read_text())
    if manifest['original_sha256'] != ARCHIVE_HASH or manifest['original_size_bytes'] != ARCHIVE_SIZE:
        raise ValueError('Unexpected archive identity')
    destination = root / '.work/japanese-research-v3' / manifest['original_filename']
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size == ARCHIVE_SIZE and file_sha(destination) == ARCHIVE_HASH:
        return destination
    parts = manifest['parts']
    if [p['index'] for p in parts] != list(range(1, len(parts) + 1)):
        raise ValueError('Archive part order differs')
    temporary = destination.with_suffix('.assembling')
    try:
        with temporary.open('wb') as output:
            for descriptor in parts:
                path = local(root, descriptor['path'])
                data = path.read_bytes()
                if len(data) != descriptor['size_bytes'] or sha(data) != descriptor['sha256']:
                    raise ValueError('Archive part checksum mismatch: ' + descriptor['path'])
                output.write(data)
        if temporary.stat().st_size != ARCHIVE_SIZE or file_sha(temporary) != ARCHIVE_HASH:
            raise ValueError('Reassembled archive mismatch')
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def read_selections(root):
    result = {}
    for filename, expected in SELECTION_HASHES.items():
        data = (root / IMPORT / 'selection' / filename).read_bytes()
        if sha(data) != expected:
            raise ValueError('Reviewed display-selection ledger changed: ' + filename)
        result[filename] = json.loads(data)
    return (result['whole_record_display_selections.json'],
            result['mixed_parent_display_selections.json'],
            result['whole_record_text_roles.json']['by_record_id'])


def verify_selection(selection, original, component_index, is_mixed=False):
    raw = original['raw_text']
    if sha(raw.encode()) != selection['source_raw_text_sha256']:
        raise ValueError('Original source text changed: ' + original['record_id'])
    if is_mixed:
        selected = []
        for part in selection['parts']:
            component = component_index[part['component_id']]
            start, end = part['approved_component_span']
            display_start, display_end = part['selected_display_span']
            if (component.get('parent_record_id') or component.get('record_id')) != original['record_id'] or [component['start_char'], component['end_char']] != [start, end]:
                raise ValueError('Component identity mismatch')
            if component['classification'] != 'prophetic_hadith' or component.get('component_boundary_unresolved'):
                raise ValueError('Unresolved/non-Prophetic component cannot enter reader')
            if not start <= display_start < display_end <= end:
                raise ValueError('Display span exceeds approved component')
            if sha(raw[start:end].encode()) != component['source_slice_sha256']:
                raise ValueError('Component source changed')
            text = raw[display_start:display_end]
            if text != part['selected_text'] or sha(text.encode()) != part['selected_text_sha256']:
                raise ValueError('Display component differs from source')
            selected.append(text)
        text = selection['display_assembly']['separator'].join(selected)
    else:
        text = original[selection['source_field']]
    if text != selection['selected_text'] or sha(text.encode()) != selection['selected_text_sha256']:
        raise ValueError('Reader selection differs from original field/spans')
    if not text.strip():
        raise ValueError('Empty reader selection')
    return text


def evidence_references(original, enrichment, selection=None, is_mixed=False):
    """Keep witness identity/numbering separate from Japanese occurrence identity."""
    items = []
    original_refs = original.get('printed_references') or original.get('canonical_source_claims') or []
    if not isinstance(original_refs, list):
        original_refs = [original_refs]
    for reference in ([] if is_mixed else original_refs):
        entry = copy.deepcopy(reference) if isinstance(reference, dict) else {'source_citation': str(reference)}
        if isinstance(entry.get('book_as_printed'), str):
            entry.setdefault('collection', entry['book_as_printed'])
        if 'number_as_printed' in entry:
            entry.setdefault('number', entry['number_as_printed'])
        if isinstance(entry.get('citation_as_printed'), str):
            entry.setdefault('source_citation', entry['citation_as_printed'])
        entry.setdefault('scope', 'as_printed_reference_unresolved_identity')
        entry.setdefault('numbering_system', 'Printed source claim; original scope retained, no inferred canonical mapping')
        items.append(entry)
    research = enrichment.get('hadith_origin_research_v3') or {}
    links = research.get('collection_links') or (enrichment.get('current_reference_research') or {}).get('v3_collection_links') or []
    if not links:
        prior = (enrichment.get('current_reference_research') or {}).get('prior_research_v1_result_preserved') or {}
        if prior.get('verified_original_collection'):
            urls = prior.get('evidence_urls') or []
            numbering = prior.get('numbering_edition')
            links = [{'collection': prior['verified_original_collection'], 'hadith_number': prior.get('verified_hadith_number'),
                      'book_chapter': prior.get('verified_book_chapter'), 'numbering_scheme': numbering,
                      'edition': numbering.get('printed_edition') if isinstance(numbering, dict) else None,
                      'url': next((u for u in urls if '/hisn' not in u), urls[0] if urls else None),
                      'relationship': prior.get('verification_status'), 'scope': prior.get('verified_arabic_scope'),
                      'evidence_ids': prior.get('evidence_ids'), 'attributed_grades': prior.get('grading_attribution'),
                      'match_scope': prior.get('match_scope'), 'uncertainty': prior.get('uncertainty')}]
    selected_evidence = {eid for part in (selection or {}).get('parts', []) for eid in part.get('evidence_ids', [])}
    applied_bindings = []
    for part in (selection or {}).get('parts', []):
        binding = REFERENCE_BINDINGS.get(part['component_id'])
        if binding:
            if binding['parent_record_id'] != original['record_id'] or binding['selected_text_sha256'] != part['selected_text_sha256']:
                raise ValueError('Reference binding source identity differs')
            selected_evidence.add(binding['evidence_id'])
            applied_bindings.append({'component_id': part['component_id'], **copy.deepcopy(binding)})
    excluded_parent_witnesses = 0
    for link in links:
        witness_evidence = set(link.get('evidence_ids') or [])
        if link.get('evidence_id'):
            witness_evidence.add(link['evidence_id'])
        if is_mixed and not selected_evidence.intersection(witness_evidence):
            excluded_parent_witnesses += 1
            continue
        relationship = link.get('relationship') or 'relationship_not_established'
        entry = {key: copy.deepcopy(link.get(key)) for key in ('collection', 'book_chapter', 'numbering_scheme', 'edition', 'url', 'evidence_id', 'evidence_ids', 'attributed_grades', 'null_reasons', 'match_scope', 'uncertainty')}
        scope_text = 'Research witness: ' + str(relationship) + '. ' + str(link.get('scope') or 'Exact relationship to this selected wording remains unestablished.')
        if link.get('uncertainty'):
            scope_text += ' Qualifications: ' + '; '.join(str(x) for x in link['uncertainty'])
        for binding in applied_bindings:
            if binding['evidence_id'] in witness_evidence:
                scope_text += ' ' + binding['scope_limit']
        entry.update({'number': link.get('hadith_number'), 'scope': scope_text,
                      'source_url': link.get('url'), 'relationship': relationship,
                      'numbering_system': link.get('numbering_scheme') or 'Witness numbering only; Japanese edition correspondence remains partial',
                      'witness_scope': link.get('scope'), 'is_accepted_canonical_identity': False,
                      'source_citation': str(link.get('url') or '')})
        items.append(entry)
    return {'items': items, 'canonical_mapping_status': 'research_witnesses_with_scope_limits',
            'scope_note': 'Collection numbers and grades belong to each separately identified witness. They do not assign a unique chain, full wording or print edition to the Japanese occurrence.',
            'complete_research_path': IMPORT + '/preserved-source/metadata/enrichment_by_record_id.json.gz',
            'record_id': original['record_id'], 'excluded_parent_witness_count': excluded_parent_witnesses,
            'integration_reference_bindings': applied_bindings,
            'selected_witness_null_reason': 'No evidence-bound original-collection witness is established for the selected component. Parent-context references were not substituted.' if is_mixed and not items else None,
            'component_reference_policy': 'Mixed-parent witnesses are displayed only when their evidence IDs bind to a selected Prophetic component; other parent-context references remain in preserved research.' if is_mixed else None}


def role_comments(roles, is_mixed):
    labels = roles.get('suggested_qualifications', [])
    messages = []
    if 'reported_meaning_or_author_narrative' in labels:
        messages.append('刊行物にある要約・伝記叙述です。預言者の発言の逐語訳とは区別しています。')
    if any('kana' in label for label in labels):
        messages.append('原資料のカナ表記です。日本語による意味の翻訳ではありません。')
    if any('context' in label or 'formula_origin' in label for label in labels):
        messages.append('文言に対応する伝承はありますが、この箇所での使用状況まで同じ伝承で確認されたとは限りません。')
    if is_mixed:
        messages.append('混在した原文から、預言者に関する部分を抜粋しています。各部分のID・出典範囲は別々に保存しています。')
    return messages


def make_record(original, enrichment, selection, bibliography, roles, origin_pointer, decisions_hash, is_mixed):
    rid, sid = original['record_id'], selection['source_id']
    slug, book, title, _, _ = SOURCES[sid]
    pdf_hash = bibliography['source_pdf_sha256']
    names = bibliography.get('translator_names_for_exact_pdf')
    pages = original.get('pdf_pages') or [p.get('pdf_page_number') for p in original.get('spans', []) if p.get('pdf_page_number')]
    pages = list(dict.fromkeys(pages))
    refs = evidence_references(original, enrichment, selection, is_mixed)
    comments = role_comments(roles, is_mixed)
    meaning = 'reported_meaning_or_author_narrative' in roles.get('suggested_qualifications', [])
    source_kind = original.get('content_type') or 'prophetic_source_occurrence'
    if is_mixed and any(word in source_kind for word in ('narrative', 'biographical', 'paraphrase')):
        meaning = True
        comments.append('刊行物による叙述の抜粋です。預言者の発言の逐語訳とは区別しています。')
    if refs.get('selected_witness_null_reason'):
        comments.append('この抜粋に対応する原典の伝承・番号は未確定です。周辺の話題に関する参考文献は、対応する出典として扱っていません。')
    ai = False if names else 'unknown'
    provenance = {'origin': 'human_translator_credited' if names else 'unknown', 'ai_translation': ai,
                  'human_involvement': 'named_human_translator' if names else 'named_translator_not_established',
                  'basis': 'Exact Japanese PDF bibliography; new-book display classification follows the recorded owner policy.',
                  'evidence_ids': [bibliography['bibliography_id']], 'new_translation_generated': False}
    source = {'title': title, 'name': title, 'url': bibliography.get('original_source_url'),
              'original_source_id': sid, 'original_record_id': rid,
              'bibliography_path': IMPORT + '/Japanese_bibliography.json',
              'original_source_record': origin_pointer,
              'preserved_archive_manifest': IMPORT + '/preserved-delivery/archive-parts.json',
              'original_source_holds_preserved': True}
    source_number = original.get('source_entry_label')
    historical = {k: copy.deepcopy(original[k]) for k in ('metadata_status', 'review_status', 'independent_qc', 'independent_qc_v2', 'arabic_transcription_review', 'source_character_fidelity_notes_v2') if k in original}
    reported_extraction = str(original.get('extraction_method') or '')
    ocr = True if 'ocr' in reported_extraction.lower() else False if 'text_layer' in reported_extraction.lower() else None
    current_form = enrichment.get('content_forms') or []
    record = {
        'id': rid, 'language': 'ja', 'source_language_code': 'ja', 'book_key': book,
        'edition': 'pdf-' + pdf_hash[:12], 'show_in_html_hadith': True,
        'record_type': 'hadith_meaning_excerpt' if meaning else 'hadith_excerpt',
        'content_kind': source_kind,
        'title': original.get('source_chapter_title') or original.get('source_title') or ('原資料の番号 ' + str(source_number) if source_number else '原資料の伝承・祈願の抜粋'),
        'text': {'arabic': None, 'translation': selection['selected_text']},
        'source': source,
        'number': {'source_entry_id': source_number, 'in_book': source_number, 'canonical': None,
                   'numbering_system': 'Japanese source-local printed label; not an original-collection hadith number'},
        'narrator': {'name': original.get('narrator_as_printed'), 'scope': 'Japanese printed attribution only; external witness narrators are separate'},
        'isnad': original.get('complete_isnad_as_printed') or original.get('isnad_as_printed'),
        'translator': {'name': '・'.join(names) if names else None, 'names': names,
                       'null_reason': bibliography.get('translator_null_reason'),
                       'evidence': IMPORT + '/Japanese_bibliography.json#/' + sid},
        'ai_translation': ai, 'translation_provenance': provenance,
        'commentary': {'arabic': None, 'translation': '\n\n'.join(comments) or None,
                       'scope': 'Reader metadata qualifications; not verbatim source commentary'},
        'footnotes': [], 'references': refs,
        'grading': {'grade': None, 'grader': None, 'as_printed_claims': copy.deepcopy(original.get('grade_claims') or []),
                    'scope': 'Witness-specific attributed assessments remain with their reference; no overall grade inferred'},
        'page': {'pdf': pages, 'printed': [], 'printed_page_null_reason': 'Not independently established for this reader projection; exact PDF locators retained', 'sheet': None, 'row': None},
        'topic_tags': [], 'source_headings': [original['source_chapter_title']] if original.get('source_chapter_title') else [],
        'editorial_tags': ['source:' + slug, 'content:prophetic', *['form:' + str(x) for x in current_form]],
        'source_locator': {'original_record_id': rid, 'original_source_id': sid,
                           'source_pdf_path': 'materials/' + slug + '/source.pdf', 'source_pdf_sha256': pdf_hash,
                           'raw_text_sha256': selection['source_raw_text_sha256'],
                           'display_text_sha256': selection['selected_text_sha256'],
                           'selection_path': IMPORT + '/selection/' + ('mixed_parent_display_selections.json' if is_mixed else 'whole_record_display_selections.json'),
                           'selection_record_id': rid, 'source_record': origin_pointer,
                           'source_field': selection.get('source_field'),
                           'component_ids': [p['component_id'] for p in selection.get('parts', [])],
                           'parts': copy.deepcopy(selection.get('parts', [])),
                           'display_assembly': copy.deepcopy(selection.get('display_assembly')),
                           'does_not_merge_or_deduplicate_source_occurrences': True},
        'extraction': {'method': 'exact_preserved_source_field_or_component_projection', 'ocr_used': ocr,
                       'source_extraction_method': original.get('extraction_method'),
                       'is_excerpt': True, 'new_ocr_performed': False, 'new_original_pages_reviewed': 0},
        'review': {'status': 'source_and_reference_review_partial', 'independent_pro_qc': 'pending',
                   'release_status': 'PARTIAL_HOLD_SOURCE_HISTORY', 'release_eligible': False, 'certified_release_eligible': False,
                   'historical_show_in_html_hadith': False, 'historical_source_review': historical,
                   'historical_release_gates': copy.deepcopy(enrichment.get('release_gates')),
                   'issues': ['Current visibility follows the later explicit owner instruction. Source/research holds and separate independent final evaluation remain.'],
                   'current_publication_decision': {'path': IMPORT + '/publication-decisions.json', 'sha256': decisions_hash,
                                                    'original_record_id': rid, 'decision': 'owner_requested_public_pending_review'}},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None},
        'related_versions': [],
    }
    record['language_versions'] = [{'id': rid + ':ja:printed-source', 'language': 'ja', 'script': 'Jpan',
        'text': selection['selected_text'], 'source': {'name': title, 'url': bibliography.get('original_source_url'),
        'original_file': 'materials/' + slug + '/source.pdf', 'sha256': pdf_hash},
        'references': refs['items'], 'comments': comments, 'translation_provenance': copy.deepcopy(provenance),
        'scope': 'source_excerpt', 'match_status': 'same_source_record'}]
    return record


def run(root, archive=None):
    root = Path(root).resolve()
    archive = Path(archive) if archive else restore_archive(root)
    if archive.stat().st_size != ARCHIVE_SIZE or file_sha(archive) != ARCHIVE_HASH:
        raise ValueError('Research-v3 input archive differs')
    whole, mixed, roles = read_selections(root)
    if len(whole) != 1147 or len(mixed) != 79 or set(whole) & set(mixed):
        raise ValueError('Reviewed source-occurrence selection changed')
    with zipfile.ZipFile(archive) as z:
        members = {x['file']: x for x in json.loads(z.read(ARCHIVE_ROOT + '/manifests/output_manifest.json'))['files']}
        def read_bytes(name):
            data = z.read(ARCHIVE_ROOT + '/' + name)
            expected = members[name]
            if len(data) != expected['size_bytes'] or sha(data) != expected['sha256']:
                raise ValueError('Packaged file differs: ' + name)
            return data
        baseline = json.loads(read_bytes('sources/source_records_baseline.json'))
        added = json.loads(read_bytes('sources/source_records_added.json'))
        originals = baseline + added
        by_id = {r['record_id']: r for r in originals}
        if len(by_id) != 1889 or len(baseline) != 1687 or len(added) != 202:
            raise ValueError('Source IDs or counts differ')
        enrichment = json.loads(read_bytes('metadata/enrichment_by_record_id.json'))
        routing = json.loads(read_bytes('metadata/routing.json'))
        bibliography = json.loads(read_bytes('metadata/Japanese_bibliography.json'))
        components = json.loads(read_bytes('proposed_bank/hadith/components.json'))['components']
        component_index = {c['component_id']: c for c in components}
        if len(component_index) != 122:
            raise ValueError('Component count differs')
        route_by_id = {r['record_id']: r for r in routing}
        if set(whole) != {r['record_id'] for r in routing if r['proposed_route'] == 'proposed_bank/hadith'}:
            raise ValueError('Whole-record selection is not the original proposed hadith route')
        if set(mixed) != {c.get('parent_record_id') or c.get('record_id') for c in components}:
            raise ValueError('Mixed-parent set differs from approved components')
        for rid, selection in {**whole, **mixed}.items():
            if rid in whole and enrichment[rid]['classification'] != 'prophetic_hadith':
                raise ValueError('Non-Prophetic whole record cannot enter reader')
            verify_selection(selection, by_id[rid], component_index, rid in mixed)
        preserved = []
        retain = ['sources/source_records_baseline.json', 'sources/source_records_added.json',
                  'metadata/enrichment_by_record_id.json', 'metadata/routing.json', 'metadata/release_gate.json',
                  'metadata/component_origin_reviews_v3.json', 'metadata/source_span_assembly.json',
                  'evidence/all_evidence.json', 'manifests/record_hashes.json',
                  'proposed_bank/hadith/related_prophetic_witnesses.json', 'source_context/quran/baseline_414_unchanged.json']
        for name in retain:
            data = read_bytes(name)
            target = root / IMPORT / 'preserved-source' / (name + '.gz')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
            preserved.append({'original_archive_member': name, 'repository_path': target.relative_to(root).as_posix(),
                              'compression': 'gzip', 'original_bytes': len(data), 'original_sha256': sha(data),
                              'stored_bytes': target.stat().st_size, 'stored_sha256': file_sha(target)})
        (root / IMPORT / 'Japanese_bibliography.json').write_bytes(read_bytes('metadata/Japanese_bibliography.json'))
        selection_ids = set(whole) | set(mixed)
        decisions = []
        for rid, original in by_id.items():
            selection = whole.get(rid) or mixed.get(rid)
            decisions.append({'record_id': rid, 'source_id': route_by_id[rid]['source_id'],
                'historical_classification': enrichment[rid]['classification'],
                'historical_show_in_html_hadith': enrichment[rid]['show_in_html_hadith'],
                'source_raw_text_sha256': sha(original['raw_text'].encode()),
                'show_in_html_hadith': rid in selection_ids,
                'publication_scope': 'selected_prophetic_components_only' if rid in mixed else 'selected_original_source_field' if rid in whole else 'outside_hadith_reader',
                'selection_text_sha256': selection['selected_text_sha256'] if selection else None,
                'component_ids': [p['component_id'] for p in selection.get('parts', [])] if selection else [],
                'original_source_text_modified': False, 'certified_release_eligible': False})
        publication = {'schema': 'hadith-bank-japanese-research-v3-publication-decisions-v1',
            'source_archive_sha256': ARCHIVE_HASH, 'decision_date_japan': '2026-11-12',
            'owner_instruction': OWNER_INSTRUCTION, 'decision': 'owner_requested_public_pending_review',
            'historical_package_status': 'PARTIAL_HOLD', 'source_records': 1889, 'reader_occurrences': 1226,
            'whole_source_occurrences': 1147, 'mixed_parent_excerpt_occurrences': 79,
            'preserved_child_component_ids': 122, 'hidden_source_occurrences': 663,
            'source_certification_holds_changed': False, 'independent_final_pro_qc_performed': False,
            'counting_unit': 'Original source record ID; components remain separately identified inside their parent occurrence',
            'decisions': decisions}
        write_json(root / IMPORT / 'publication-decisions.json', publication)
        write_json(root / IMPORT / 'reference-binding-overlays.json', {
            'schema': 'japanese-research-v3-integration-reference-bindings-v1',
            'source_archive_sha256': ARCHIVE_HASH, 'bindings_by_component_id': REFERENCE_BINDINGS,
            'source_text_and_historical_metadata_modified': False,
            'scope': 'Localized linking correction using preserved evidence; not new source research or final independent QC',
            'unresolved_selected_source': {'ja_tokyo_basic_2012-r005': 'The selected Prophetic arrangement assertion is not established by the parent Companion compilation-history witnesses; matching citation remains null.'}})
        decision_hash = file_sha(root / IMPORT / 'publication-decisions.json')
        pointers = {r['record_id']: {'path': IMPORT + '/preserved-source/sources/source_records_' + kind + '.json.gz',
                    'compression': 'gzip', 'json_pointer': '/' + str(i)}
                    for kind, rows in [('baseline', baseline), ('added', added)] for i, r in enumerate(rows)}
        records_by_source = {sid: [] for sid in SOURCES}
        for rid, original in by_id.items():
            selection = whole.get(rid) or mixed.get(rid)
            if selection:
                sid = selection['source_id']
                records_by_source[sid].append(make_record(original, enrichment[rid], selection, bibliography[sid],
                    roles.get(rid, {}), pointers[rid], decision_hash, rid in mixed))
        material_results = []
        for sid, (slug, book, title, english, count) in SOURCES.items():
            records = records_by_source[sid]
            if len(records) != count:
                raise ValueError('Unexpected source count: ' + sid)
            directory = root / 'materials' / slug
            directory.mkdir(parents=True, exist_ok=True)
            original_pdf = read_bytes(bibliography[sid]['packaged_original_pdf'])
            if sha(original_pdf) != bibliography[sid]['source_pdf_sha256']:
                raise ValueError('Original Japanese PDF differs')
            (directory / 'source.pdf').write_bytes(original_pdf)
            write_rows(directory / 'records.jsonl', records)
            result = register(root, 'materials/' + slug, 'ja', book, records[0]['edition'], title,
                'records.jsonl', 'source.pdf', source_url=bibliography[sid]['original_source_url'],
                source_id=slug, replace=(directory / 'manifest.json').exists())
            manifest = json.loads((directory / 'manifest.json').read_text())
            manifest['source'].update({'title_ja': title, 'title_en': english,
                'metadata_path': IMPORT + '/Japanese_bibliography.json', 'original_source_id': sid})
            manifest['publication'].update({'owner_instruction': OWNER_INSTRUCTION,
                'scope': 'Enumerated Japanese source-supported Prophetic occurrences and exact components; non-hadith and unknown rows excluded.',
                'publication_decisions_path': IMPORT + '/publication-decisions.json', 'publication_decisions_sha256': decision_hash,
                'historical_source_package_status': 'PARTIAL_HOLD', 'independent_qc_asserted': False,
                'certified_release_eligible': False})
            manifest['counterpart_policy'] = {'mode': 'disabled', 'reason': COUNTERPART_HOLD}
            manifest['preserved_delivery'] = {'path': IMPORT + '/preserved-delivery/archive-parts.json',
                'original_zip_sha256': ARCHIVE_HASH, 'original_bytes_unchanged': True, 'format': 'ordered_exact_binary_archive_parts'}
            manifest['source_partitions'] = {'reader_occurrences': count, 'whole_source_occurrences': sum(r['id'] in whole for r in records),
                'mixed_parent_excerpts': sum(r['id'] in mixed for r in records),
                'classification_path': IMPORT + '/publication-decisions.json', 'hidden_records_remain_outside_registry': True}
            write_json(directory / 'manifest.json', manifest)
            material_results.append({'source_id': sid, 'material_id': slug, 'reader_count': count,
                'records_sha256': file_sha(directory / 'records.jsonl'), 'original_pdf_sha256': sha(original_pdf)})
        partitions = {'non_hadith': [], 'quran': [], 'unresolved': [], 'mixed_parents': []}
        for route in routing:
            rid = route['record_id']
            kind = ('non_hadith' if route['proposed_route'] == 'proposed_bank/non_hadith' else
                    'quran' if route['proposed_route'] == 'source_context/quran' else
                    'mixed_parents' if route['proposed_route'] == 'hold/mixed_source_parents' else
                    'unresolved' if rid not in selection_ids else None)
            if kind:
                partitions[kind].append({'id': rid, 'show_in_html_hadith': False,
                    'historical_route': route, 'original_source_record': by_id[rid],
                    'parent_only_exact_components_displayed': rid in mixed,
                    'current_publication_decisions_path': IMPORT + '/publication-decisions.json'})
        targets = {'non_hadith': 'non-hadith/japanese-research-v3-20261112/records.jsonl',
            'quran': IMPORT + '/source-context/quran/records.jsonl',
            'unresolved': 'unclassified/japanese-research-v3-20261112/unresolved/records.jsonl',
            'mixed_parents': 'unclassified/japanese-research-v3-20261112/mixed-parents/records.jsonl'}
        for kind, rows in partitions.items():
            write_rows(root / targets[kind], rows)
        audit = {'schema': 'hadith-bank-japanese-research-v3-integration-v1',
            'input_archive_sha256': ARCHIVE_HASH, 'original_source_records': 1889,
            'reader_source_occurrences': 1226, 'whole_records': 1147, 'mixed_parent_excerpts': 79,
            'component_annotations_preserved': 122, 'external_witness_links_not_counted_as_records': 45,
            'hidden_original_source_occurrences': 663, 'materials': material_results,
            'partitions': {k: {'path': targets[k], 'count': len(v), 'registered_as_hadith': False} for k, v in partitions.items()},
            'original_source_files_preserved': True, 'source_ids_preserved': True,
            'new_ocr_performed': False, 'new_page_audit_count': 0, 'independent_final_pro_qc_performed': False,
            'certified_release_eligible': False, 'current_visibility': 'owner_authorized_pending_review',
            'candidate_arabic_english_promoted': False, 'publication_decisions_sha256': decision_hash,
            'compressed_exact_source_files': preserved}
        write_json(root / IMPORT / 'integration-audit.json', audit)
    return {k: audit[k] for k in ('reader_source_occurrences', 'whole_records', 'mixed_parent_excerpts', 'hidden_original_source_occurrences', 'candidate_arabic_english_promoted')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--restore-only', action='store_true')
    args = parser.parse_args()
    if args.restore_only:
        print(restore_archive(args.root.resolve()))
    else:
        print(json.dumps(run(args.root, args.archive), ensure_ascii=False))
