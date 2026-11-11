#!/usr/bin/env python3
"""Generate readable/search views without changing canonical source records.

Public mode reads the bank's published HadeethEnc snapshots and explicitly
owner-authorized materials/*/manifest.json sources. An optional unregistered
local attachment intake is included only in a separate private output tree.
All views preserve occurrences, source text, source locators and review status.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

from current_provenance import POLICY_PATH as CURRENT_PROVENANCE_PATH, apply_policy as apply_provenance_policy, classification, load_policy as load_provenance_policy
from review_display_policy import extraction_metadata


LANG_NAMES = {'ja': 'Japanese', 'fil': 'Filipino / Tagalog', 'vi': 'Vietnamese',
              'zh-CN': 'Chinese', 'uz': 'Uzbek', 'hi': 'Hindi', 'ur': 'Urdu',
              'bn': 'Bengali', 'pt': 'Portuguese', 'fa': 'Persian'}
POLICY_PATH = 'catalog/translation-origins.json'
REVIEW_POLICY_PATH = 'catalog/review-policy.json'
EVIDENCE_PATH = 'sources/translation-origin-evidence/2026-11-11/evidence.json'
SCHEMA = 'hadith-bank-search-record-v1'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def local(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Invalid local path')
    pure = PurePosixPath(relative)
    if pure.is_absolute() or '..' in pure.parts or any(':' in x for x in pure.parts):
        raise ValueError('Unsafe local path: ' + relative)
    path = (root / pure).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Local path escapes bank: ' + relative)
    return path


def translation_info(record, source_kind, book):
    ai = record.get('ai_translation', 'unknown')
    if source_kind == 'hadeethenc':
        return {
            'origin': 'publisher_human_workflow',
            'label': 'Human translation — HadeethEnc',
            'basis': 'owner_source_classification_and_publisher_described_workflow',
            'translation_classification': 'human',
            'human_involvement': 'publisher_described_translation_proofreading_and_review',
            'ai_translation': ai,
            'evidence_ids': ['hadeethenc-platform', 'publisher-translation-workflow', 'ai-assistance-scope'],
            'scope_note': 'Human source classification follows the owner instruction and publisher translation workflow. The individual translator and exact-version AI assistance are not stated; the historic AI flag is preserved.',
            'policy_path': POLICY_PATH,
        }
    translator = record.get('translator') or {}
    if ai is False and translator.get('name') and book in ('riyadh-al-salihin', 'shengxunjing'):
        return {
            'origin': 'human_translator_credited',
            'label': 'Human translation — ' + translator['name'],
            'basis': 'named_translator_and_historical_date_in_supplied_source',
            'human_involvement': 'named_human_translator',
            'ai_translation': False,
            'evidence_ids': ['pdf-human-' + book],
            'scope_note': 'Credit and date evidence establish translation origin, not the accuracy of every extracted character.',
            'policy_path': POLICY_PATH,
        }
    return {
        'origin': 'unknown',
        'label': 'Published-source translation — translator not identified',
        'basis': 'supplied_source_has_no_established_translator_credit',
        'human_involvement': 'not_established', 'ai_translation': ai,
        'evidence_ids': [],
        'scope_note': 'Translation authorship is not inferred from the file name, PDF timestamp or extraction method.',
        'policy_path': POLICY_PATH,
    }


def public_projection(record, collection, line_number):
    p = record['provenance']
    language = collection['language']
    source_code = record['source_language_code']
    entry = record['source_entry_id']
    tags = []
    for tag in record.get('topic_tags', []):
        category = tag.get('category_verbatim') or {}
        tags.append({'id': str(category.get('id')) if category.get('id') is not None else None,
                     'label': category.get('title'),
                     'path': [x.get('title') for x in tag.get('ancestors_including_self_verbatim', []) if x.get('title')],
                     'origin': 'publisher_taxonomy'})
    commentary = record['commentary']
    references = record['source_references']
    bibliography = references.get('bibliography_verbatim')
    if bibliography:
        assert ''.join(x['text_verbatim'] for x in references.get('citation_lines', [])) == bibliography
    compact_references = {key: copy.deepcopy(value) for key, value in references.items() if key != 'citation_lines'}
    compact_references['citation_line_count'] = len(references.get('citation_lines', []))
    arabic_benefits = commentary.get('arabic_benefits_raw_json_verbatim')
    if isinstance(arabic_benefits, str):
        try:
            arabic_benefits = json.loads(arabic_benefits)
        except ValueError:
            arabic_benefits = {'unparsed_source_json': arabic_benefits}
    issues = []
    if record['arabic_alignment']['status'] != 'exact_provider_id_version_and_text_match':
        issues.append(record['arabic_alignment']['status'])
    source_id = 'hadeethenc-' + source_code + '-' + collection['edition']
    return {
        'schema_version': SCHEMA, 'id': record['record_id'],
        'language': language, 'source_language_code': source_code,
        'book_key': collection['book'], 'edition': collection['edition'],
        'source_id': source_id, 'provider_entry_id': entry,
        'title': record.get('title_verbatim'),
        'text_arabic': record['texts']['arabic_verbatim'],
        'text_translation': record['texts']['translation_verbatim'],
        'number': {'source_entry_id': entry, 'in_book': None, 'canonical': None},
        'narrator': copy.deepcopy(record['narration']),
        'source': {
            'name': 'HadeethEnc.com',
            'work_title': record['publication']['translation_work'],
            'url': 'https://hadeethenc.com/' + source_code,
            'record_url': 'https://hadeethenc.com/' + source_code + '/browse/hadith/' + entry,
            'download_url': p['source_download_url'],
            'original_file': p['local_database_path'],
            'sha256': p['database_sha256'],
            'record_locator': {'path': collection['records_path'], 'line': line_number},
            'format': 'sqlite', 'retrieved_at': p['retrieved_at'],
        },
        'translator': {'name': record['publication']['translator'], 'evidence': None,
                       'publisher': record['publication']['publisher']},
        'translation_provenance': translation_info(record, 'hadeethenc', 'hadeethenc'),
        'extraction': extraction_metadata(record),
        'topic_tags': tags,
        'editorial_tags': list(record.get('editorial_tags', {}).get('values', [])),
        'source_headings': [],
        'review': {'status': record['review']['release_status'], 'issues': issues,
                   'independent_pro_qc': record['review']['independent_pro_qc'],
                   'release_status': record['review']['release_status'],
                   'certified_release_eligible': record['review'].get('certified_release_eligible', False)},
        'commentary': {'arabic': commentary.get('arabic_explanation_verbatim'),
                       'translation': commentary.get('translation_explanation_verbatim')},
        'benefits': {'translation': commentary.get('translation_benefits_decoded'),
                    'arabic': arabic_benefits},
        'footnotes': [], 'footnote_status': copy.deepcopy(record['footnotes']),
        'references': compact_references,
        'grading': copy.deepcopy(record['grading']),
        'page': {'pdf': [], 'printed': [], 'sheet': None, 'row': p['source_rowid'],
                 'row_scope': 'SQLite source row; not a printed page'},
        'related_versions': copy.deepcopy(record['related_versions']),
        'canonical_record_sha256': hashlib.sha256(canonical(record)).hexdigest(),
    }


def attachment_projection(record, collection, index, prefix):
    out = {
        'schema_version': SCHEMA, 'id': record['id'],
        'language': record['language'], 'source_language_code': record['source_language_code'],
        'book_key': collection['book'], 'edition': collection['edition'],
        'source_id': collection['source_id'],
        'provider_entry_id': record['number'].get('source_entry_id'),
        'title': record.get('title', {}).get('translation'),
        'text_arabic': record['text']['arabic'], 'text_translation': record['text']['translation'],
        'number': copy.deepcopy(record['number']), 'narrator': copy.deepcopy(record['narrator']),
        'source': {'name': 'HadeethEnc.com' if collection['book'] == 'hadeethenc' else record['source']['title'],
                   'work_title': record['book']['title'],
                   'url': record['source'].get('url'), 'record_url': record['source'].get('url'),
                   'original_file': prefix + '/' + record['source']['package_file'],
                   'sha256': record['source']['sha256'],
                   'record_locator': {'path': prefix + '/' + collection['records_path'], 'json_pointer': '/' + str(index)},
                   'format': record['source']['format']},
        'translator': copy.deepcopy(record['translator']),
        'translation_provenance': translation_info(record, 'hadeethenc' if collection['book'] == 'hadeethenc' else 'pdf', collection['book']),
        'extraction': extraction_metadata(record),
        'topic_tags': [],
        'editorial_tags': list(record.get('editorial_tags', {}).get('values', [])),
        'source_headings': [x['value_verbatim'] for x in record.get('source_structure_tags', [])],
        'review': {'status': record['review']['status'], 'issues': copy.deepcopy(record['review']['issues']),
                   'independent_pro_qc': record['review']['independent_pro_qc'],
                   'release_status': record['review']['release_status'], 'certified_release_eligible': False},
        'commentary': copy.deepcopy(record['commentary']), 'benefits': copy.deepcopy(record.get('benefits')),
        'footnotes': copy.deepcopy(record['footnotes']), 'references': copy.deepcopy(record['references']),
        'grading': copy.deepcopy(record['grading']), 'page': copy.deepcopy(record['page']),
        'related_versions': copy.deepcopy(record.get('related_versions', [])),
        'source_occurrence_group': copy.deepcopy(record.get('source_occurrence_group')),
        'canonical_record_sha256': hashlib.sha256(canonical(record)).hexdigest(),
    }
    return out


def policy():
    return {
        'schema': 'hadith-bank-translation-origin-evidence-v1', 'as_of_date_japan': '2026-11-11',
        'local_evidence': EVIDENCE_PATH,
        'principle': 'Display human translation evidence and its scope; AI translation, human review and extraction method are separate facts.',
        'evidence': [
            {'id': 'hadeethenc-platform', 'url': 'https://islamiccontent.org/',
             'scope': 'publisher_platform_identity',
             'finding': 'The association identifies HadeethEnc as one of its platforms.'},
            {'id': 'publisher-translation-workflow', 'url': 'https://islamiccontent.org/About',
             'additional_url': 'https://hadeethenc.com/ar/home/about',
             'scope': 'publisher_organization_workflow_not_individual_passage_authorship',
             'finding': 'The publisher describes translators, language proofreading, religious review and approval. Named translators and AI use for these exact exported passages are not stated.'},
            {'id': 'ai-assistance-scope', 'url': 'https://molhem.ai/',
             'scope': 'platform_capability_not_evidence_that_these_exports_used_it',
             'finding': 'The association-associated platform describes AI assistance with human review. Its existence neither proves nor excludes AI use in any particular bank record.'},
            {'id': 'pdf-human-riyadh-al-salihin', 'source_file': '163819884895551.pdf',
             'source_sha256': 'ac1cd8a6821e3affcd3a10c5d0c4863e19cf4f1b4a36f3505834ab491eb0c4c8',
             'translator': '艾乃斯·马风德', 'credit_pdf_page': 12,
             'dated_afterword_pdf_page': 358, 'afterword_date': '1999-02-15',
             'date_scope': 'signed afterword; not an inferred publication date',
             'scope': 'named_historical_human_translator_in_source'},
            {'id': 'pdf-human-shengxunjing', 'source_file': '163819897387558.pdf',
             'source_sha256': '64d260b8d79a3d53b755bb2d271d5e5314ca486299c3e173fbb32d77230000f1',
             'translator': '陈克礼', 'credit_pdf_page': 2,
             'edition_statement': '1981-1-1', 'volume_year_statements': ['1954', '1981'],
             'scope': 'named_historical_human_translator_in_source'},
        ],
        'classification_rules': {
            'publisher_human_workflow': 'Human source classification follows the owner instruction and publisher-described translator workflow; exact-record ai_translation stays as supplied.',
            'human_translator_credited': 'Named translator and historical source evidence support human origin.',
            'unknown': 'No established author/process attribution for the exact source; retain unknown.',
        },
        'source_record_policy': 'Canonical records and their historic assertions are unchanged. These evidence-backed labels are a separately versioned display/search layer.',
        'human_translation_does_not_equal_bank_qc_pass': True,
    }


def apply_review_policy(projected, review_policy):
    """Add the current owner decision without rewriting historic import facts."""
    rule = review_policy.get('hadeethenc', {})
    if (review_policy.get('schema') != 'hadith-bank-review-policy-v1' or
            rule.get('decision') != 'owner_waived_separate_bank_review' or
            rule.get('separate_bank_review_required') is not False):
        raise ValueError('Invalid or unsupported current HadeethEnc review policy')
    for record in projected:
        if record['book_key'] == 'hadeethenc' and record['source']['name'] == 'HadeethEnc.com':
            record['review']['current_policy'] = {
                'separate_bank_review_required': False,
                'status': 'not_required_by_owner',
                'label': rule['label'],
                'decision_date_japan': rule['decision_date_japan'],
                'independent_review_performed': False,
                'historical_status_preserved': True,
                'arabic_alignment_flags_retained': True,
                'policy_path': REVIEW_POLICY_PATH,
            }


def write_catalog_readme(output, catalog):
    private = catalog['scope'] == 'private_combined_sources'
    lines = [
        '# All-materials catalog', '',
        ('This private combined package contains ' if private else 'This public bank contains ') +
        '**' + format(catalog['record_count'], ',') + ' source occurrences** in ' +
        str(len(catalog['by_language'])) + ' languages, plus **' +
        str(len(catalog['legacy_materials'])) + ' preserved legacy source files**.', '',
        'Counts describe source occurrences across translations and editions. They are not unique canonical Hadith totals.', '',
        '[Read all narration records](../browse/README.md) · [Search instructions](../docs/READING-AND-SEARCH.md) · '
        '[Machine-readable inventory](materials.json) · [Translation evidence](translation-origins.json)', '',
        '## Narration datasets available here', '',
        '| Language | Source book | Edition | Records | Read | Source |',
        '| --- | --- | --- | ---: | --- | --- |',
    ]
    for item in catalog['materials']:
        folder = '/'.join((item['language'], item['book_key'], item['edition']))
        lines.append('| ' + LANG_NAMES.get(item['language'], item['language']) +
                     ' | ' + item['book_key'] + ' | `' + item['edition'] + '` | ' +
                     format(item['count'], ',') + ' | [Read](../browse/' + folder +
                     '/README.md) | [Original file](../' + item['source_file'] + ') |')
    lines += ['', '## Current translation classification', '',
              '| Classification | Source occurrences |', '| --- | ---: |']
    for origin, count in catalog['current_translation_origins'].items():
        lines.append('| ' + origin.title() + ' | ' + format(count, ',') + ' |')
    lines += ['', 'The scoped [owner source confirmation](provenance-policy.json) determines the current Human, AI and Unknown grouping. '
              'Copied old-bank source documents and their extracted quotations remain Unknown pending owner confirmation.', '',
              '### Preserved source attribution history', '',
              '| Original evidence category | Source occurrences |', '| --- | ---: |']
    for origin, count in catalog['translation_origins'].items():
        lines.append('| `' + origin + '` | ' + format(count, ',') + ' |')
    lines += ['', 'Human involvement is displayed with its source and scope. Individual AI-use flags and bank review status remain separate.', '',
              '## Legacy lessons, readings and source packages', '',
              '[Browse all ' + str(len(catalog['legacy_materials'])) + ' source files](../browse/materials/legacy.md). '
              'The existing organization contains ' + str(catalog['legacy_organization']['packages']) +
              ' packages, ' + str(catalog['legacy_organization']['reading_only']) +
              ' reading-only items and ' + str(catalog['legacy_organization']['source_metadata_records']) +
              ' source metadata records. Original documents remain preserved; their extracted quotation occurrences are indexed separately in the registered datasets above. Document counts are not added to quotation counts.', '',
              'Use `python scripts/search.py fulltext QUERY --language ja` for their existing local document search.', '']
    if catalog['private_materials_not_in_this_tree']:
        pending_count = sum(item['count'] for item in catalog['private_materials_not_in_this_tree'])
        lines += ['## Separate private attachment intake', '',
                  'The following **' + format(pending_count, ',') + ' occurrences** are registered here as metadata. Their full texts and original files remain in the private combined package.', '',
                  '| Language | Book | Source snapshot | Occurrences |',
                  '| --- | --- | --- | ---: |']
        for item in catalog['private_materials_not_in_this_tree']:
            lines.append('| ' + LANG_NAMES.get(item['language'], item['language']) + ' | ' + item['book_key'] +
                         ' | `' + item['edition'] + '` | ' + format(item['count'], ',') + ' |')
        lines += ['', '[Private intake organization and review status](../docs/ATTACHMENT-INTAKE.md).', '']
    lines += ['## Review state', '',
              'The reader shows QC labels only for text with explicit OCR extraction evidence. '
              'Digital source imports, native PDF text and structured quotations do not receive pending-QC badges. '
              'Original import/review history, source-alignment notes and rights metadata remain preserved in record details. '
              '[Current review policy](review-policy.json). '
              '[Mechanical fidelity report](../reports/reading-views-validation.json).', '']
    (output / 'catalog/README.md').write_text('\n'.join(lines), encoding='utf-8')


def write_snapshot_relationships(output, projection_groups):
    """Link publisher IDs across snapshots without merging source occurrences."""
    grouped = {}
    for group in projection_groups:
        for record in group:
            if record['book_key'] == 'hadeethenc' and record['provider_entry_id'] is not None:
                key = (record['language'], str(record['provider_entry_id']))
                grouped.setdefault(key, []).append(record)
    links, counts = [], {}
    for (language, provider_id), records in sorted(grouped.items()):
        if len({r['source_id'] for r in records}) < 2:
            continue
        same_translation = all(r['text_translation'] == records[0]['text_translation'] for r in records)
        same_arabic = all(r['text_arabic'] == records[0]['text_arabic'] for r in records)
        links.append({
            'language': language, 'provider': 'HadeethEnc.com', 'provider_entry_id': provider_id,
            'basis': 'same_publisher_entry_id_in_distinct_source_snapshots',
            'canonical_narration_equivalence_verified': False,
            'source_occurrences': [{'id': r['id'], 'source_id': r['source_id'],
                                    'edition': r['edition'], 'locator': r['source']['record_locator']}
                                   for r in records],
            'exact_translation_strings_equal': same_translation,
            'exact_arabic_strings_equal': same_arabic,
        })
        info = counts.setdefault(language, {'overlapping_provider_ids': 0, 'source_occurrences': 0,
                                           'identical_translation_groups': 0, 'identical_arabic_groups': 0})
        info['overlapping_provider_ids'] += 1
        info['source_occurrences'] += len(records)
        info['identical_translation_groups'] += int(same_translation)
        info['identical_arabic_groups'] += int(same_arabic)
    result = {
        'schema': 'hadith-bank-snapshot-relationships-v1',
        'comparison': 'Exact stored strings; no normalization or canonical inference.',
        'occurrences_merged': 0, 'by_language': counts, 'links': links,
    }
    write_json(output / 'catalog/related-snapshots.json', result)
    return counts


def write_entry_points(output, catalog):
    """Keep root and language entry points in sync with the local package scope."""
    index_path = output / 'index.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    existing = {item['language']: item for item in index.get('languages', [])}
    entries = []
    order = ['ja', 'fil', 'vi', 'zh-CN', 'uz', 'hi', 'bn', 'ur', 'pt']
    for language in sorted(catalog['by_language'], key=lambda v: order.index(v) if v in order else 999):
        datasets = [item for item in catalog['materials'] if item['language'] == language]
        legacy = [item for item in catalog['legacy_materials'] if item['language'] == language]
        relative = 'catalog/languages/' + language + '.json'
        write_json(output / relative, {
            'schema': 'hadith-bank-language-materials-v1', 'language': language,
            'name': LANG_NAMES.get(language, language), 'scope': catalog['scope'],
            'record_count': catalog['by_language'][language], 'count_unit': catalog['count_unit'],
            'datasets': datasets, 'legacy_materials': legacy,
            'reading_index': 'browse/' + language + '/README.md',
            'related_snapshots': 'catalog/related-snapshots.json',
        })
        entry = copy.deepcopy(existing.get(language, {'language': language, 'name': LANG_NAMES.get(language, language),
                                                      'catalog': relative}))
        entry['materials_catalog'] = relative
        entry['record_count'] = catalog['by_language'][language]
        entry['source_dataset_count'] = len(datasets)
        entry['books'] = sorted(set(entry.get('books', [])) | {item['book_key'] for item in datasets})
        entry['readingIndex'] = 'browse/' + language + '/README.md'
        entries.append(entry)
    index.update({
        'scope': catalog['scope'], 'recordCount': catalog['record_count'],
        'languageCount': len(catalog['by_language']), 'countUnit': catalog['count_unit'],
        'sourceDatasetCount': len(catalog['materials']), 'sourceDatasets': catalog['materials'],
        'languages': entries, 'materialsCatalog': 'catalog/materials.json',
        'readingIndex': 'browse/README.md', 'relatedSnapshots': 'catalog/related-snapshots.json',
        'translationOriginEvidence': POLICY_PATH,
        'currentReviewPolicy': REVIEW_POLICY_PATH,
    })
    registered_path = output / 'catalog/registered-materials.json'
    if registered_path.is_file():
        registered = json.loads(registered_path.read_text(encoding='utf-8'))
        index['registeredMaterials'] = 'catalog/registered-materials.json'
        previous = [item for item in index.get('publicIntakes', []) if not item.get('materialManifest')]
        for manifest in registered['manifests']:
            members = [item for item in catalog['materials'] if item.get('manifest_path') == manifest['path']]
            previous.append({'id': manifest['id'], 'kind': manifest['adapter'],
                             'materialManifest': manifest['path'], 'count': sum(item['count'] for item in members),
                             'status': 'published_pending_review', 'publicTextPublished': True,
                             'independentProQC': 'pending', 'sourceReviewHistoryPreserved': True,
                             'publication': manifest['publication']})
        index['publicIntakes'] = previous
    if catalog['scope'] == 'private_combined_sources':
        for intake in index.get('privateIntakes', []):
            intake['catalog'] = intake.get('catalog') or 'attachments/' + intake['id'] + '/collections.json'
            intake['availableLocally'] = local(output, intake['catalog']).is_file()
        index['datasets'] = [item for item in index.get('datasets', [])
                             if item['id'] != 'attachments-b53d154fa3622b95'] + [{
            'id': 'attachments-b53d154fa3622b95',
            'catalog': 'attachments/attachments-b53d154fa3622b95/collections.json',
            'count': sum(item['count'] for item in catalog['materials']
                         if item['canonical_records_path'].startswith('attachments/attachments-b53d154fa3622b95/')),
            'release_status': 'private_candidate', 'publicTextPublished': False,
        }]
    write_json(index_path, index)
    if catalog['scope'] != 'private_combined_sources':
        return
    public_count = sum(item['count'] for item in catalog['materials']
                       if item['release_status'] == 'published_unreviewed_source_import')
    private_count = catalog['record_count'] - public_count
    lines = [
        '# Hadith Bank — all materials', '',
        '**' + format(catalog['record_count'], ',') + ' source records · ' + str(len(catalog['by_language'])) +
        ' languages · ' + str(len(catalog['materials'])) + ' source datasets**', '',
        '[Open the offline reader](hadith-bank-reader.html) · [Browse by language](browse/README.md) · '
        '[Complete source catalog](catalog/README.md)', '',
        'This package brings together the ' + format(public_count, ',') + ' public HadeethEnc source occurrences, the ' + format(private_count, ',') + ' supplied '
        'PDF/XLSX occurrences, and 83 preserved legacy source documents. Source occurrences across languages, '
        'editions and snapshots are kept separate. These totals are not a count of unique canonical Hadith.', '',
        '## Start here', '',
        'Extract the ZIP, then open **hadith-bank-reader.html** in a browser. It includes all ' + format(catalog['record_count'], ',') + ' indexed '
        'records and works offline. Filter by language, collection, source edition or translation origin; '
        'search Arabic or translated text and export selected records as readable JSON.', '',
        'The folders under `browse/` provide paginated reading views. The folders under `search/` contain '
        'UTF-8 JSONL organized by language → book → edition. Each record retains its exact source text, '
        'stable ID, original source locator, available narrator/number/page fields, attribution and review state.', '',
        '## Language coverage', '',
        '| Language | Public snapshot records | Supplied file records | Total source records | Browse |',
        '| --- | ---: | ---: | ---: | --- |',
    ]
    for entry in entries:
        language = entry['language']
        public = sum(item['count'] for item in catalog['materials'] if item['language'] == language
                     and item['release_status'] == 'published_unreviewed_source_import')
        total = catalog['by_language'][language]
        lines.append('| ' + LANG_NAMES.get(language, language) + ' | ' + format(public, ',') + ' | ' +
                     format(total - public, ',') + ' | ' + format(total, ',') +
                     ' | [Read](browse/' + language + '/README.md) |')
    lines += [
        '', '## Japanese 281-entry collection', '',
        'The public SQLite collection and the supplied Japanese v1.8.0 workbook each contain 281 publisher '
        'entries. They share the same 281 publisher IDs and are retained as separate source snapshots. '
        'They must not be counted as 562 different Hadith. '
        '[Open both Japanese editions](browse/ja/hadeethenc/README.md). '
        '[Exact source-overlap report](catalog/related-snapshots.json).', '',
        '## Sources and translation labels', '',
        'HadeethEnc entries show the publisher-described human translation and review process. '
        'Where a supplied historical source credits a translator, the name is shown. Unknown exact-version '
        'AI assistance remains unknown. Translation origin, extraction method and bank QC status are separate '
        'fields. [Attribution evidence](catalog/translation-origins.json).', '',
        '## Original files and record locations', '',
        '| Material | Local location |', '| --- | --- |',
        '| Public source records | `languages/<language>/books/<book>/editions/<edition>/` |',
        '| Supplied PDF/XLSX records, originals and audit evidence | Separate source packages under `attachments/` |',
        '| Unified search records | `search/<language>/<book>/<edition>/part-*.jsonl` |',
        '| Readable pages | `browse/<language>/<book>/<edition>/` |',
        '| Every dataset and its exact source hash | `catalog/materials.json` |',
        '| Legacy document inventory | `browse/materials/legacy.md` |', '',
        'All runtime files are contained in this package. Website links identify original sources; they are '
        'not needed for reading or search. Legacy source documents retain historical links verbatim; '
        'the bank catalogs and verified local locators are the current navigation.', '',
        '## Search from Python', '', '```bash',
        "python scripts/hadith_search.py '礼拝' --language ja --limit 5",
        'python scripts/hadith_search.py --language ja --id 2758 --json',
        '```', '', '[Full format and search guide](docs/READING-AND-SEARCH.md).', '',
        '## Review status', '',
        'Separate bank review of HadeethEnc is not required under the owner decision of 11 November 2026. '
        'The original import statuses and Arabic alignment notes remain preserved. Other source-specific '
        'review and publication qualifications remain unchanged. [Current review policy](catalog/review-policy.json). '
        'This organization pass does not certify '
        'transcription, translation accuracy, canonical matching or authenticity. '
        '[Exact-copy validation](reports/reading-views-validation.json).', '',
    ]
    (output / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


def build(bank_root, output, attachments=None):
    bank_root, output = bank_root.resolve(), output.resolve()
    from material_registry import load_public_materials
    registered = load_public_materials(bank_root, validate_attachment_roots=not attachments)
    if attachments and output == bank_root:
        raise ValueError('Private attachment views require a separate output directory')
    if output != bank_root and (output.is_relative_to(bank_root) or bank_root.is_relative_to(output)):
        raise ValueError('Separate output must not overlap the public bank directory')
    if attachments:
        attachments = attachments.resolve()
        if attachments.is_relative_to(output) or output.is_relative_to(attachments):
            raise ValueError('Attachment input and generated output directories must not overlap')
    if output != bank_root:
        if output.exists() and any(output.iterdir()):
            raise ValueError('Separate output directory must be new or empty')
        shutil.copytree(bank_root, output, ignore=shutil.ignore_patterns('.git', '.cache', '__pycache__', 'browse', 'search', 'catalog', 'hadith-bank-reader.html'))
    output.mkdir(parents=True, exist_ok=True)
    if output != bank_root:
        for supplemental in ('catalog/legacy-link-resolution.json', REVIEW_POLICY_PATH, CURRENT_PROVENANCE_PATH):
            if not local(bank_root, supplemental).is_file():
                continue
            local(output, supplemental).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local(bank_root, supplemental), local(output, supplemental))
        supplemental = 'catalog/additional-private-intakes.json'
        if local(bank_root, supplemental).is_file():
            shutil.copy2(local(bank_root, supplemental), local(output, supplemental))
    review_policy = json.loads(local(output, REVIEW_POLICY_PATH).read_text(encoding='utf-8'))
    provenance_policy = load_provenance_policy(output)
    attribution = policy()
    evidence = local(output, EVIDENCE_PATH)
    attribution['local_evidence_sha256'] = digest_file(evidence)
    current_evidence = 'sources/translation-origin-evidence/2026-11-11/current-policy-evidence.json'
    attribution['current_owner_and_source_evidence'] = {
        'path': current_evidence, 'sha256': digest_file(local(output, current_evidence))}
    write_json(output / POLICY_PATH, attribution)
    published = json.loads((output / 'datasets/hadeethenc/collections.json').read_text(encoding='utf-8'))
    projection_groups = []
    materials = []
    comparison = []
    source_hashes = {}
    for collection in published['collections']:
        path = local(output, collection['records_path'])
        if digest_file(path) != collection['records_sha256']:
            raise ValueError('Canonical record checksum mismatch: ' + collection['records_path'])
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        if len(rows) != collection['count']:
            raise ValueError('Canonical record count mismatch')
        projected = [public_projection(r, collection, i + 1) for i, r in enumerate(rows)]
        apply_review_policy(projected, review_policy)
        for view in projected:
            apply_provenance_policy(view, provenance_policy)
        for row, view in zip(rows, projected):
            assert view['text_arabic'] == row['texts']['arabic_verbatim']
            assert view['text_translation'] == row['texts']['translation_verbatim']
        projection_groups.append(projected)
        first = projected[0]
        materials.append({'dataset_id': first['source_id'], 'language': collection['language'],
                          'book_key': collection['book'], 'edition': collection['edition'],
                          'source_name': first['source']['name'], 'count': len(projected),
                          'release_status': collection['release_status'], 'available_locally': True,
                          'source_file': first['source']['original_file'], 'source_sha256': first['source']['sha256'],
                          'canonical_records_path': collection['records_path'],
                          'canonical_records_sha256': collection['records_sha256'],
                          'translation_provenance': first['translation_provenance'],
                          'current_review_policy': first['review'].get('current_policy')})
        comparison.append({'path': collection['records_path'], 'sha256': collection['records_sha256'],
                           'records': len(rows), 'arabic_and_translation_equal': True})
    attachment_summary = json.loads((output / 'reports/attachments/attachments-b53d154fa3622b95/summary.json').read_text(encoding='utf-8'))
    pending = []
    if attachments:
        attachments = attachments.resolve()
        prefix = 'attachments/attachments-b53d154fa3622b95'
        target = output / prefix
        shutil.copytree(attachments, target)
        ac = json.loads((target / 'collections.json').read_text(encoding='utf-8'))
        for collection in ac['collections']:
            path = local(target, collection['records_path'])
            if digest_file(path) != collection['records_sha256']:
                raise ValueError('Attachment record checksum mismatch')
            rows = json.loads(path.read_text(encoding='utf-8'))
            if len(rows) != collection['count']:
                raise ValueError('Attachment count mismatch')
            projected = [attachment_projection(r, collection, i, prefix) for i, r in enumerate(rows)]
            apply_review_policy(projected, review_policy)
            for view in projected:
                apply_provenance_policy(view, provenance_policy)
            for row, view in zip(rows, projected):
                assert view['text_arabic'] == row['text']['arabic']
                assert view['text_translation'] == row['text']['translation']
            projection_groups.append(projected)
            first = projected[0]
            materials.append({'dataset_id': first['source_id'], 'language': collection['language'],
                              'book_key': collection['book'], 'edition': collection['edition'],
                              'source_name': first['source']['name'], 'count': len(projected),
                              'release_status': collection['release_status'], 'available_locally': True,
                              'source_file': first['source']['original_file'], 'source_sha256': first['source']['sha256'],
                              'canonical_records_path': prefix + '/' + collection['records_path'],
                              'canonical_records_sha256': collection['records_sha256'],
                              'translation_provenance': first['translation_provenance'],
                              'current_review_policy': first['review'].get('current_policy')})
            comparison.append({'path': prefix + '/' + collection['records_path'],
                               'sha256': collection['records_sha256'], 'records': len(rows),
                               'arabic_and_translation_equal': True})
    else:
        for c in attachment_summary['collections']:
            pending.append({'dataset_id': c['source_id'], 'language': c['language'],
                            'book_key': c['book'], 'edition': c['edition'], 'count': c['count'],
                            'release_status': 'private_candidate', 'available_locally': False,
                            'source_sha256': c['source_sha256'],
                            'location_note': 'Available in the separate private attachment package; not a public runtime locator.'})
    # Registration changes public availability, never canonical review history.
    known_dataset_ids = {item['dataset_id'] for item in materials}
    for material, projected in zip(registered['materials'], registered['groups']):
        if material['dataset_id'] in known_dataset_ids:
            raise ValueError('Registered source duplicates an existing source: ' + material['dataset_id'])
        known_dataset_ids.add(material['dataset_id'])
        materials.append(material)
        projection_groups.append(projected)
        comparison.append({'path': material['canonical_records_path'],
                           'sha256': material['canonical_records_sha256'], 'records': material['count'],
                           'arabic_and_translation_equal': True, 'publication_manifest': material['manifest_path']})
    write_json(output / 'catalog/registered-materials.json', {
        'schema': 'hadith-bank-registered-materials-v1', 'manifests': registered['manifests'],
        'source_dataset_count': len(registered['materials']),
        'record_count': sum(item['count'] for item in registered['materials']),
        'source_review_statuses_preserved': True, 'independent_qc_performed': False,
    })
    # The PDF adapters retain this evidence locator from the original integration.
    if any(item['adapter'] == 'pdf-intake-package-v1' for item in registered['materials']):
        write_json(output / 'catalog/intake-translation-origins.json', {
            'schema': 'hadith-bank-intake-translation-origins-v1',
            'note': 'Source-specific human credits and unknown AI flags are preserved, independently of publication authorization.',
            'materials': [{'dataset_id': item['dataset_id'], 'translation_provenance': item['translation_provenance']}
                          for item in registered['materials'] if item['adapter'] == 'pdf-intake-package-v1'],
        })
    registry_path = local(output, 'catalog/additional-private-intakes.json')
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        present_ids = {item['dataset_id'] for item in materials + pending}
        now_public = {item['dataset_id']: item for item in registered['materials']}
        allowed_fields = {'dataset_id', 'language', 'book_key', 'edition', 'count',
                          'release_status', 'available_locally', 'source_sha256',
                          'source_name', 'source_pdf_pages', 'intake_id',
                          'public_text_published', 'location_note'}
        for item in registry['materials']:
            if isinstance(item, dict) and item.get('dataset_id') in now_public:
                current = now_public[item['dataset_id']]
                if (item.get('count') != current['count'] or item.get('source_sha256') != current['source_sha256']):
                    raise ValueError('Previously registered intake differs from authorized source: ' + item['dataset_id'])
                item.update({'available_locally': True, 'public_text_published': True,
                             'source_file': current['source_file'],
                             'canonical_records_path': current['canonical_records_path'],
                             'source_metadata_path': current.get('source_metadata_path'),
                             'publication': current['publication'],
                             'location_note': 'Full records, source files and evidence are now in this repository; original pending-review facts are preserved.'})
                continue
            if (not isinstance(item, dict) or set(item) - allowed_fields or
                    item.get('available_locally') is not False or
                    item.get('public_text_published') is not False or
                    item.get('release_status') != 'private_candidate' or
                    type(item.get('count')) is not int or item['count'] < 0):
                raise ValueError('Additional private registry must contain held-source metadata only')
            if item['dataset_id'] in present_ids:
                raise ValueError('Duplicate dataset in additional private registry: ' + item['dataset_id'])
            pending.append(item)
            present_ids.add(item['dataset_id'])
        registry['review_status'] = 'Original private_candidate/source-review-pending history preserved; current public availability is recorded per source.'
        registry['scope'] = 'public_repository_source_registration'
        write_json(registry_path, registry)
    search_root = output / 'search'
    if search_root.exists():
        # Only this generator's reproducible projections are replaced.
        for path in search_root.rglob('part-*.jsonl'):
            path.unlink()
    search_root.mkdir(exist_ok=True)
    whole = search_root / 'records.jsonl'
    shards = []
    ids = set()
    language_counts, origin_counts, current_origin_counts = Counter(), Counter(), Counter()
    with whole.open('wb') as stream:
        for projected in projection_groups:
            for start in range(0, len(projected), 100):
                block = projected[start:start + 100]
                first = block[0]
                shard_dir = search_root / first['language'] / first['book_key'] / first['edition']
                shard_dir.mkdir(parents=True, exist_ok=True)
                shard_path = shard_dir / ('part-' + str(start // 100 + 1).zfill(4) + '.jsonl')
                encoded = []
                for item in block:
                    if item['id'] in ids:
                        raise ValueError('Duplicate occurrence ID across inputs: ' + item['id'])
                    ids.add(item['id'])
                    language_counts[item['language']] += 1
                    origin_counts[item['translation_provenance']['origin']] += 1
                    current_origin_counts[classification(item)] += 1
                    original = item['source']['original_file']
                    if original not in source_hashes:
                        source_hashes[original] = digest_file(local(output, original))
                    if source_hashes[original] != item['source']['sha256']:
                        raise ValueError('Original source checksum mismatch: ' + original)
                    encoded.append(json.dumps(item, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n')
                data = b''.join(encoded)
                shard_path.write_bytes(data)
                stream.write(data)
                shards.append({'path': shard_path.relative_to(output).as_posix(),
                               'sha256': hashlib.sha256(data).hexdigest(), 'count': len(block), 'bytes': len(data)})
    legacy = json.loads((output / 'reports/IMPORT-STATUS.json').read_text(encoding='utf-8'))
    legacy_index = json.loads((output / 'organized/INDEX.json').read_text(encoding='utf-8'))
    catalog = {
        'schema': 'hadith-bank-materials-v1', 'title': 'Hadith Bank',
        'scope': 'private_combined_sources' if attachments else 'public_source_snapshots',
        'record_count': len(ids), 'count_unit': 'source narration/entry occurrences across editions; not unique canonical Hadith',
        'by_language': dict(sorted(language_counts.items())), 'translation_origins': dict(origin_counts),
        'current_translation_origins': dict(sorted(current_origin_counts.items())),
        'materials': materials, 'private_materials_not_in_this_tree': pending,
        'legacy_materials': [apply_provenance_policy({'language': f['language'], 'path': f['path'], 'sha256': f['sha256'],
                             'bytes': f['bytes'], 'source_revision': f['source_revision'],
                             'kind': 'legacy_source_document', 'translation_origin': 'unknown',
                             'available_locally': True}, provenance_policy) for f in legacy['files']],
        'legacy_organization': {'metadata_index': 'organized/INDEX.json',
                                'packages': len(legacy_index['packages']),
                                'reading_only': len(legacy_index['readingsOnly']),
                                'source_metadata_records': len(legacy_index['sourceRecords'])},
        'search': {'records_path': 'search/records.jsonl', 'records_sha256': digest_file(whole),
                   'count': len(ids), 'shards': shards,
                   'whole_file_optional': True, 'ordered_shards_equal_whole_file': True},
        'translation_evidence': POLICY_PATH,
        'current_review_policy': REVIEW_POLICY_PATH,
        'current_provenance_policy': CURRENT_PROVENANCE_PATH if provenance_policy else None,
        'registered_materials': 'catalog/registered-materials.json',
        'related_snapshots': 'catalog/related-snapshots.json',
        'legacy_link_resolution': 'catalog/legacy-link-resolution.json',
        'no_new_translation_created': True, 'canonical_sources_unchanged': True,
        'snapshot_equivalence_note': 'Provider ID overlap links source snapshots; snapshots and occurrences are not silently merged.',
    }
    write_json(output / 'catalog/materials.json', catalog)
    write_snapshot_relationships(output, projection_groups)
    write_entry_points(output, catalog)
    write_catalog_readme(output, catalog)
    write_json(output / 'reports/reading-views-validation.json', {
        'schema': 'hadith-bank-reading-views-validation-v1', 'status': 'passed',
        'records_compared': len(ids), 'unique_occurrence_ids': len(ids),
        'source_record_files': comparison, 'source_assets_hashed': len(source_hashes),
        'canonical_sources_unchanged': True, 'text_normalization': 'none in stored/display values',
        'translation_origins': dict(origin_counts), 'search_sha256': catalog['search']['records_sha256'],
        'current_translation_origins': dict(sorted(current_origin_counts.items())),
        'shards': len(shards), 'review_status_promoted': False,
        'provenance_note': 'Translation process evidence is scoped separately from exact-record AI-origin and bank QC.',
    })
    return {'records': len(ids), 'languages': dict(language_counts), 'datasets': len(materials),
            'private_datasets_listed_separately': len(pending), 'legacy_files': len(legacy['files']),
            'search_bytes': whole.stat().st_size, 'shards': len(shards), 'translation_origins': dict(origin_counts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--attachments', type=Path)
    args = parser.parse_args()
    try:
        result = build(args.bank_root, args.output or args.bank_root, args.attachments)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, AssertionError) as exc:
        sys.exit('View generation failed: ' + str(exc))


if __name__ == '__main__':
    main()
