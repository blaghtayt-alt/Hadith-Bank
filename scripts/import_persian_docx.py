#!/usr/bin/env python3
"""Adapt the nine owner-supplied Persian DOCX extractions to records-v1.

The upstream source-aware extracts and audits are retained under imports/.
This adapter preserves every supplied occurrence and exact final text field;
it neither deduplicates nor infers canonical numbers, grades or translations.
Run refresh_bank.py after this command to regenerate all reading/search views.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
from collections import Counter

from register_material import register
from material_registry import SOURCE_IMPORT_DECISION


IMPORT_ROOT = 'imports/persian-docx-20261111'
COMMENTARY_POLICY = 'Owner requested hadiths only; separable translator/editorial comments excluded.'
NO_QC = {'qc_tags': False, 'decision': 'owner_requested_no_qc_tags_for_non_ocr',
         'basis': 'Owner instruction on 2026-11-11: these native Persian DOCX imports do not need QC tags.'}
EXPECTED_COUNTS = {'fa-faiz-al-bari-v1': 412, 'fa-faiz-al-bari-v2': 451,
                   'fa-faiz-al-bari-v3': 504, 'fa-faiz-al-bari-v4': 466,
                   'fa-faiz-al-bari-v5': 337, 'fa-faiz-al-bari-v6': 457,
                   'fa-muslim-mundhiri-tarshabi-v1': 1104,
                   'fa-muslim-mundhiri-tarshabi-v2': 1128,
                   'fa-riyadh-heravi-1394-digital': 1946}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_input(base, relative):
    path = base / relative
    if path.is_file():
        raw = path.read_text(encoding='utf-8')
    else:
        with gzip.open(str(path) + '.gz', 'rt', encoding='utf-8') as stream:
            raw = stream.read()
    return [json.loads(line) for line in raw.splitlines()] if relative.endswith('.jsonl') else json.loads(raw)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def configurations(extracted):
    configs = []
    for volume in range(1, 7):
        metadata = read_input(extracted, f'bukhari/volume{volume}.metadata.json')
        configs.append({'family': 'bukhari', 'volume': volume,
                        'slug': f'fa-faiz-al-bari-v{volume}', 'book': 'bukhari',
                        'edition': f'faiz-al-bari-heravi-v{volume}',
                        'name': f'فیض الباری — مختصر صحیح البخاری، جلد {volume}',
                        'title': metadata['title'], 'filename': metadata['file_name'],
                        'sha256': metadata['file_sha256'], 'translator': metadata['author_translator_commentator'],
                        'metadata': metadata, 'metadata_input': f'bukhari/volume{volume}.metadata.json',
                        'url': 'https://www.aqeedeh.com/'})
    for volume in (1, 2):
        metadata = read_input(extracted, f'muslim/muslim-v{volume}.metadata.json')
        configs.append({'family': 'muslim', 'volume': volume,
                        'slug': f'fa-muslim-mundhiri-tarshabi-v{volume}', 'book': 'muslim',
                        'edition': f'mukhtasar-mundhiri-tarshabi-v{volume}',
                        'name': f'مختصر صحیح مسلم — منذری / ترشابی، جلد {volume}',
                        'title': metadata['title'], 'filename': metadata['source_file'],
                        'sha256': metadata['source_sha256'], 'translator': metadata['translator'],
                        'metadata': metadata, 'metadata_input': f'muslim/muslim-v{volume}.metadata.json',
                        'url': 'https://aqeedeh.com/book_files/orig-html/1661.html' if volume == 1
                               else 'https://www.aqeedeh.com/book_files/html/1743.html'})
    metadata = read_input(extracted, 'riyadh/edition-metadata.json')
    configs.append({'family': 'riyadh', 'volume': None, 'slug': metadata['edition_id'],
                    'book': 'riyadh-al-salihin', 'edition': 'heravi-1394-digital',
                    'name': 'ترجمه فارسی ریاض الصالحین — عبد الله خاموش هروی',
                    'title': metadata['source_title'],
                    'filename': 'tarjomeye-farsi-reyaz-al-salehin-heravi-Word.docx',
                    'sha256': metadata['source_sha256'],
                    'translator': metadata['translator_and_commentator_as_printed'],
                    'metadata': metadata, 'metadata_input': 'riyadh/edition-metadata.json',
                    'url': 'https://aqeedeh.com/book_files/html/444.html'})
    return configs


def rows_for(config, extracted):
    family, volume = config['family'], config['volume']
    if family == 'bukhari':
        files = ['hadith_only_primary_records.jsonl', 'variant_records.jsonl',
                 'explicit_hadith_quotation_records.jsonl']
        return [(r, 'bukhari/' + f) for f in files for r in read_input(extracted, 'bukhari/' + f)
                if r['source_volume'] == volume]
    if family == 'muslim':
        files = [f'muslim-v{volume}.main.jsonl', f'muslim-v{volume}.confirmed-ancillary-hadiths.jsonl']
        return [(r, 'muslim/' + f) for f in files for r in read_input(extracted, 'muslim/' + f)]
    return [(r, 'riyadh/integration-records.jsonl') for r in read_input(extracted, 'riyadh/integration-records.jsonl')]


def locator_for(row, config):
    locator = copy.deepcopy(row.get('source_locator', {}))
    locator.setdefault('file', config['filename'])
    locator.setdefault('part', 'word/document.xml')
    locator['index_base'] = 0
    if row.get('source_paragraphs'):
        locator['paragraphs_by_role'] = copy.deepcopy(row['source_paragraphs'])
    if row.get('aligned_translation_locator'):
        locator['aligned_translation'] = copy.deepcopy(row['aligned_translation_locator'])
    return locator


def paragraph_labels(locator):
    if locator.get('part') != 'word/document.xml':
        return [f"{locator['part']} note {locator.get('footnote_id', locator.get('note_id'))}, paragraph "
                f"{locator.get('paragraph_index', locator.get('paragraph_index_zero_based'))} (zero-based)"]
    by_role = locator.get('paragraphs_by_role')
    if by_role:
        return sorted(set(p for values in by_role.values() for p in values))
    for key in ('paragraph_start_zero_based', 'paragraph_start', 'paragraph_index_zero_based', 'paragraph_index'):
        if locator.get(key) is not None:
            return [locator[key]]
    return []


def references_for(row):
    original = row.get('references') or {}
    result = {'items': copy.deepcopy(original if isinstance(original, list) else
                                    [{'field': key, 'value': value} for key, value in original.items()
                                     if value is not None and value != []]),
              'canonical_mapping_status': 'Source citations preserved as printed; no independent canonical matching asserted.'}
    return result


def cited_label(row):
    refs = row.get('references') or {}
    labels = []
    if isinstance(refs, list):
        for ref in refs:
            for number in ref.get('numbers', []):
                labels.append(str(ref.get('collection') or ref.get('citation_label_raw') or 'Source') + ' ' + str(number))
    else:
        for ref in refs.get('citations_as_printed', []):
            number = ref.get('number_as_printed')
            if number is not None:
                labels.append(str(ref.get('collection') or 'Source') + ' ' + str(number))
    return list(dict.fromkeys(labels))


def adapt(row, config, upstream_file):
    family = config['family']
    text = copy.deepcopy(row['text'])
    assert set(text) >= {'arabic', 'translation'}
    assert any(text.get(key) for key in ('arabic', 'translation')), row['id']
    original_kind = row.get('record_type', row.get('record_kind'))
    kind = row.get('content_kind', row.get('occurrence_kind'))
    if family == 'muslim':
        kind = ('numbered_source_narration' if row.get('number', {}).get('source_local_raw') is not None
                else 'unnumbered_source_narration') if original_kind == 'main_hadith_occurrence' else original_kind
    primary = original_kind in ('hadith', 'hadith_occurrence', 'translation_occurrence', 'main_hadith_occurrence')
    variant = kind == 'unnumbered_source_variant'
    companion = 'companion' in (original_kind or '') or 'companion' in (kind or '')
    fragment = 'fragment' in (kind or '') or any('fragment' in str(note).lower() for note in row.get('source_notes', []))
    role = 'variant' if variant else 'primary' if primary else 'companion_excerpt' if companion else 'quotation_excerpt'
    local_number = (row.get('number') or {}).get('source_local_raw') if family == 'muslim' else row.get('source_local_number')
    heading = ('Companion report excerpt' if companion else 'Hadith quotation excerpt') if not primary else (
              'Unnumbered source variant' if variant else 'Source narration fragment' if fragment else 'Hadith')
    title = heading + (' ' + str(local_number) if local_number is not None else '')
    locator = locator_for(row, config)
    headings = [h['text'] if isinstance(h, dict) else h for h in row.get('source_headings', [])]
    narrator = copy.deepcopy(row.get('narrator') or {})
    if not isinstance(narrator, dict):
        narrator = {'as_printed': narrator}
    refs = row.get('references') or {}
    narrator.setdefault('name', narrator.get('name_as_printed') or narrator.get('as_printed') or
                         narrator.get('arabic_as_written_without_diacritics') or
                         (refs.get('narrator_as_printed') or refs.get('opening_attribution_as_printed')
                          if isinstance(refs, dict) else None))
    narrator.setdefault('basis', 'Source attribution only; full chain not reconstructed.')
    defects = copy.deepcopy(row.get('source_exceptions', row.get('source_notes', [])))
    # Only source/editorial metadata, never the excluded commentary prose, enters the reader.
    grading = copy.deepcopy(row.get('authenticity') or {'grade': None, 'grader': None,
                                'basis': 'No independent authenticity grade inferred from the source book.'})
    if row.get('grade'):
        grading['source_assessment'] = copy.deepcopy(row['grade'])
    if isinstance(refs, dict) and refs.get('grading_as_printed'):
        grading['source_grades_as_printed'] = copy.deepcopy(refs['grading_as_printed'])
    refdata = references_for(row)
    if row.get('grade'):
        refdata['items'].append({'field': 'source_assessment', 'value': copy.deepcopy(row['grade'])})
    related = []
    for parent in list(row.get('parent_ids') or []) + [row.get('parent_id'), row.get('parent_record_id'),
                                                     row.get('related_record_id')]:
        if parent and parent not in [r['id'] for r in related]:
            related.append({'id': parent, 'relationship': 'source_context_or_variant',
                            'same_narration_asserted': False})
    metadata_path = f"materials/{config['slug']}/source-metadata.json"
    record = {
        'id': row['id'], 'language': 'fa', 'book_key': config['book'], 'edition': config['edition'],
        'title': title, 'text': text, 'record_type': original_kind, 'content_kind': kind,
        'source': {'title': config['title'], 'url': config['url'], 'volume': config['volume'],
                   'original_filename': config['filename'], 'metadata_path': metadata_path,
                   'work_scope': 'Persian translation of an abridgment' if family in ('bukhari', 'muslim')
                                 else 'Persian translation of Riyadh al-Salihin'},
        'number': {'in_book': local_number, 'source_entry_id': None, 'canonical': None,
                   'source_cited': cited_label(row),
                   'source_sequence_position': row.get('source_sequence_position', row.get('local_sequence')),
                   'printed_labels': copy.deepcopy(row.get('printed_labels', {
                       'arabic': local_number, 'translation': row.get('translation_local_number')})),
                   'numbering_system': row.get('numbering_system', (row.get('number') or {}).get('numbering_system'))
                        or 'Source-local numbering; not canonical Bukhari/Muslim numbering'},
        'narrator': narrator, 'isnad': copy.deepcopy(row.get('isnad', row.get('full_isnad'))),
        'translator': {'name': config['translator'], 'evidence': metadata_path,
                       'role': 'named source translator'},
        'translation_provenance': {'origin': 'human_translator_credited', 'label': 'Human',
                                  'basis': 'Named translator printed in the supplied source edition.',
                                  'human_involvement': 'named_human_translator', 'ai_translation': False,
                                  'evidence_ids': [metadata_path],
                                  'scope_note': 'Existing published Persian wording; no new translation was generated.'},
        'ai_translation': False,
        'topic_tags': [],
        'source_headings': headings,
        'source_structure_tags': [{'origin': 'source_book_structure', 'source_id': config['slug'],
                                   'hierarchy': i + 1, 'original_field': 'source_headings',
                                   'value_verbatim': heading, 'source_locator': copy.deepcopy(locator),
                                   'locator_scope': 'narration_under_heading',
                                   'heading_metadata_as_supplied': {
                                       k: copy.deepcopy(v) for k, v in row['source_headings'][i].items()
                                       if k not in ('text', 'raw_text', 'text_raw')}
                                       if isinstance(row['source_headings'][i], dict) else {}}
                                  for i, heading in enumerate(headings)],
        'editorial_tags': {'origin': 'import_pipeline_not_publisher', 'values': [
            'source:' + config['slug'], 'language:fa', 'method:direct_ooxml', 'book:' + config['book'],
            'edition:' + config['edition'], 'format:docx', 'kind:' + str(kind), 'ai_translation:false',
            'canonical_mapping:source_cited_unverified',
            'arabic:' + ('supplied' if text['arabic'] else 'not_supplied'),
            'translation:' + ('supplied' if text['translation'] else 'not_supplied')]},
        'commentary': {'arabic': None, 'translation': None}, 'footnotes': [],
        'references': refdata, 'grading': grading,
        'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': None,
                 'docx_paragraphs': paragraph_labels(locator), 'index_base': 0,
                 'basis': 'OOXML source positions; reliable per-occurrence printed pagination unavailable.'},
        'source_locator': locator, 'source_defects': defects, 'related_versions': related,
        'review': {'status': 'native_source_import', 'issues': defects,
                   'independent_pro_qc': 'not_performed', 'release_status': 'source_import',
                   'release_eligible': False, 'certified_release_eligible': False},
        'rights': {'status': 'not_assessed_for_publication', 'reuse_basis': None,
                   'source_notice_preserved_in': f"materials/{config['slug']}/source.docx"},
        'extraction': {'method': 'direct_ooxml', 'ocr_used': False, 'batch_limit': None,
                       'side_commentary_included': False, 'commentary_policy': COMMENTARY_POLICY,
                       'occurrence_role': role,
                       'source_extraction': f'{IMPORT_ROOT}/extracted/{upstream_file}.gz',
                       'source_extraction_id': row['id'],
                       'font_evidence': f'{IMPORT_ROOT}/audit/font-evidence/font-decoding-evidence.json',
                       'exact_text_fields_preserved_by_adapter': True}}
    if row.get('extraction'):
        record['extraction']['source_extractor'] = copy.deepcopy(row['extraction'])
    return record


def run(root, extracted, source_root=None):
    counts, all_ids = [], set()
    for config in configurations(extracted):
        folder = root / 'materials' / config['slug']
        folder.mkdir(parents=True, exist_ok=True)
        original = source_root / config['filename'] if source_root else folder / 'source.docx'
        if digest(original) != config['sha256']:
            raise ValueError('Original source checksum mismatch: ' + config['filename'])
        if source_root:
            shutil.copyfile(original, folder / 'source.docx')
        inputs = rows_for(config, extracted)
        rows = [adapt(row, config, path) for row, path in inputs]
        if len(rows) != EXPECTED_COUNTS[config['slug']]:
            raise ValueError('Unexpected full-document occurrence count for ' + config['slug'])
        for (raw, _), row in zip(inputs, rows):
            assert row['id'] not in all_ids, 'Duplicate occurrence id: ' + row['id']
            all_ids.add(row['id'])
            assert row['text'] == raw['text'], 'Adapter altered hadith text: ' + row['id']
            assert row['commentary'] == {'arabic': None, 'translation': None} and not row['footnotes']
            assert not any(tag.startswith(('qc:', 'review:')) for tag in row['editorial_tags']['values'])
        record_file = folder / 'records.jsonl'
        record_file.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                                      for row in rows), encoding='utf-8')
        metadata = copy.deepcopy(config['metadata'])
        metadata['commentary_policy'] = COMMENTARY_POLICY
        metadata['imported_record_count'] = len(rows)
        metadata['source_original_filename'] = config['filename']
        write_json(folder / 'source-metadata.json', metadata)
        register(root, f"materials/{config['slug']}", 'fa', config['book'], config['edition'],
                 config['name'], 'records.jsonl', 'source.docx', source_url=config['url'],
                 source_id=config['slug'], replace=(folder / 'manifest.json').exists())
        manifest = json.loads((folder / 'manifest.json').read_text())
        manifest['publication'] = {'authorized': True, 'decision': SOURCE_IMPORT_DECISION,
                                   'decision_date_japan': '2026-11-11'}
        manifest['display_policy'] = copy.deepcopy(NO_QC)
        manifest['extraction_scope'] = {'source_file_count': 1, 'no_batch_limit': True,
                                        'side_commentary_included': False,
                                        'audit_root': IMPORT_ROOT + '/audit/' + config['family']}
        write_json(folder / 'manifest.json', manifest)
        role_counts = Counter(row['extraction']['occurrence_role'] for row in rows)
        report = {'source_id': config['slug'], 'book': config['book'], 'volume': config['volume'],
                  'source_filename': config['filename'], 'source_sha256': config['sha256'],
                  'records_sha256': digest(record_file), 'records': len(rows),
                  'roles': dict(role_counts), 'all_text_fields_equal_extractor_output': True,
                  'missing_arabic': sum(not row['text']['arabic'] for row in rows),
                  'missing_translation': sum(not row['text']['translation'] for row in rows)}
        write_json(folder / 'integration-audit.json', report)
        counts.append(report)
    report = {'schema': 'hadith-bank-persian-integration-v1', 'source_documents': len(counts),
              'records': sum(row['records'] for row in counts), 'unique_ids': len(all_ids),
              'source_occurrences_not_unique_narrations': True, 'deduplicated': False,
              'batch_limit': None, 'commentary_in_text': False, 'qc_tags_added': False,
              'sources': counts}
    write_json(root / 'reports/persian-docx-integration.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--extraction-root', type=Path)
    parser.add_argument('--source-root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    report = run(root, (args.extraction_root or root / IMPORT_ROOT / 'extracted').resolve(), args.source_root)
    print(json.dumps({'source_documents': report['source_documents'], 'records': report['records'],
                      'unique_ids': report['unique_ids']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
