#!/usr/bin/env python3
"""Reproduce the pinned embedded-source census and alternate-format checks.

The default mode uses only committed source bundles and the captured full tree.
--snapshot and --tree bootstrap missing evidence from an already obtained local
snapshot; every byte must match the pinned tree before it can be preserved.
The comparison removes whitespace only. Listed numbering/footnote rendering
differences are audited separately and never rewrite either source version.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PIN = 'ae2c07599767ee7182c40d3ff2264fcdac98d182'
REPO = 'blaghtayt-alt/iman-companion'
LANGUAGES = ('ja', 'fil', 'vi', 'zh-CN', 'uz', 'hi', 'fa')
EVIDENCE = 'sources/embedded-inventory'
REPORT = 'reports/embedded-source-inventory.json'
ADDITIONAL_LINKED_PATHS = {
    'materials/hadith/heart-reminder/closeness-02/tokyo112-companion.json',
    'materials/hadith/heart-reminder/trust-03/tokyo112-companion.json',
}

# These exact source-note phrases explain a title or translation choice; none
# is presented in its paragraph as an independent narration.
CONTEXT_PHRASES = {
    'صحیح سنن ابن\u200cماجه': 'Bibliographic book title, explicitly distinguished from a grading claim in the Persian source note.',
    'pagkatapos niyang pumanaw': 'Filipino source-note explanation of the Companion report translation.',
    'pagkatapos niya': 'Filipino source-note explanation of the Companion report translation.',
    'Vafot etganlaridan keyin': 'Uzbek source-note explanation of the Companion report translation.',
    'u zotdan keyin': 'Uzbek source-note explanation of the Companion report translation.',
    'Sau khi Người qua đời': 'Vietnamese source-note explanation of the Companion report translation.',
    'sau Người': 'Vietnamese source-note explanation of the Companion report translation.',
    '与使者在一起': 'Chinese source-note explanation of the Companion report time context.',
}

RENDERED_INDEX_DIFFERENCES = {
    'materials/hadith/heart-reminder/desire-01/ja.md': [('[21]', '')],
    'materials/hadith/heart-reminder/desire-03/ja.md': [('13 ', '')],
    'materials/hadith/heart-reminder/peace-01/ja.md': [('5－', ''), ('伝承6）', '伝承）')],
    'materials/hadith/heart-reminder/peace-03/ja.md': [('伝承11）', '伝承）')],
    'materials/hadith/heart-reminder/sabr-01/ja.md': [('伝承3）', '伝承）')],
    'materials/hadith/heart-reminder/sabr-03/vi.md': [('Hadith số 31: ', '')],
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def leaves(value, pointer=''):
    if isinstance(value, str):
        yield pointer, value
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from leaves(item, pointer + '/' + str(i))
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, pointer + '/' + str(key).replace('~', '~0').replace('/', '~1'))


def normalize(text):
    return re.sub(r'\s+', '', text)


def language(path):
    for lang in LANGUAGES:
        if '/' + lang + '/' in path or re.search('/' + re.escape(lang) + r'\.(?:json|md|txt)$', path) or '-' + lang + '/' in path:
            return lang
    return 'ar' if '/essential-ar/' in path or path.endswith('/ar.json') else None


def target_path(path):
    return bool(re.search(r'(?:tadabbur|quran|hadith|articles)', path) and language(path) in LANGUAGES)


def quotes(text):
    for match in re.finditer(r'「([^「」]*)」|“([^“”]*)”|«([^«»]*)»|"([^"\n]*)"', text):
        for group in range(1, 5):
            if match.group(group) is not None:
                value = match.group(group)
                if len(value.strip()) >= 3:
                    yield match.start(group), match.end(group), value
                break


def load_sources(root):
    sources, seen = {}, set()
    for pattern in ('legacy-*/source-bundle.json', 'quran-excerpts-*/source-bundle.json'):
        for file in sorted((root / 'materials').glob(pattern)):
            raw = file.read_bytes()
            if digest(raw) in seen:
                continue
            seen.add(digest(raw))
            bundle = json.loads(raw)
            member = 'documents' if 'documents' in bundle else 'files'
            for i, entry in enumerate(bundle[member]):
                if entry.get('repository') not in (None, REPO):
                    continue
                text_key = 'raw_utf8' if 'raw_utf8' in entry else 'raw_text'
                text = entry[text_key]
                original = text.encode('utf-8')
                assert digest(original) == entry['sha256']
                assert blob(original) == entry['git_blob_sha']
                item = {'raw_utf8': text, 'sha256': digest(original), 'git_blob_sha': blob(original),
                        'byte_count': len(original), 'evidence_file': file.relative_to(root).as_posix(),
                        'evidence_pointer': f'/{member}/{i}/{text_key}', 'language': language(entry['path'])}
                if entry['path'] in sources:
                    assert sources[entry['path']]['raw_utf8'] == text
                else:
                    sources[entry['path']] = item
    return sources


def run(root, snapshot=None, tree_input=None, write=True):
    tree_path = root / EVIDENCE / 'pinned-tree.json'
    if not tree_path.exists():
        if tree_input is None:
            raise ValueError('First run needs the already obtained pinned --tree')
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        tree_path.write_bytes(tree_input.read_bytes())
    tree_raw = tree_path.read_bytes()
    full_tree = json.loads(tree_raw)
    assert full_tree['truncated'] is False
    assert full_tree['sha'] == '29954180b2d0ed67e15bed4bdbceb362bb8e4d33'
    tree = {item['path']: item for item in full_tree['tree'] if item.get('type') == 'blob'}
    legacy_path = root / 'reports/legacy-extraction-audit.json'
    quran_path = root / 'reports/quran-hadith-extraction.json'
    legacy, quran = json.loads(legacy_path.read_bytes()), json.loads(quran_path.read_bytes())
    old = {item['path']: (i, item) for i, item in enumerate(legacy['source_coverage']) if item['repository'] == REPO}
    q = {item['path']: (i, item) for i, item in enumerate(quran['source_files'])}
    primary = {path for path in tree if target_path(path)}
    scope = primary | old.keys() | q.keys() | ADDITIONAL_LINKED_PATHS
    sources = load_sources(root)
    supplement_path = root / EVIDENCE / 'supplemental-source-bundle.json'
    missing = sorted(scope - sources.keys())
    if not supplement_path.exists():
        if snapshot is None:
            raise ValueError('First run needs an already obtained local --snapshot')
        files = []
        for path in missing:
            raw = (snapshot / path).read_bytes()
            assert blob(raw) == tree[path]['sha'], path
            files.append({'path': path, 'git_blob_sha': blob(raw), 'sha256': digest(raw),
                          'byte_count': len(raw), 'raw_utf8': raw.decode('utf-8')})
        dump(supplement_path, {'schema': 'hadith-bank-embedded-supplemental-source-v1',
                              'repository': REPO, 'commit': PIN, 'files': files})
    supplementary = json.loads(supplement_path.read_bytes())
    assert supplementary['commit'] == PIN
    for i, item in enumerate(supplementary['files']):
        raw = item['raw_utf8'].encode('utf-8')
        assert blob(raw) == item['git_blob_sha'] and digest(raw) == item['sha256']
        assert blob(raw) == tree[item['path']]['sha']
        sources[item['path']] = {**item, 'language': language(item['path']),
                                 'evidence_file': supplement_path.relative_to(root).as_posix(),
                                 'evidence_pointer': f'/files/{i}/raw_utf8'}
    assert scope <= sources.keys(), sorted(scope - sources.keys())

    string_rows = collections.defaultdict(list)
    parsed = {}
    for path, source in sources.items():
        if path.endswith('.json') and path in (old.keys() | q.keys() | ADDITIONAL_LINKED_PATHS):
            parsed[path] = json.loads(source['raw_utf8'])
            for pointer, value in leaves(parsed[path]):
                string_rows[language(path)].append((path, pointer, normalize(value)))
    # Prefer the closest field and short scalar evidence, not huge raw carriers.
    for rows in string_rows.values():
        rows.sort(key=lambda item: (len(item[2]), item[0], item[1]))

    def find_quote(value, lang, paired=None):
        needle = normalize(value)
        if paired and paired in parsed:
            for pointer, text in leaves(parsed[paired]):
                if needle in normalize(text):
                    return {'path': paired, 'json_pointer': pointer, 'comparison': 'whitespace_only'}
        for path, pointer, haystack in string_rows[lang] + string_rows[None] + string_rows['ar']:
            if needle in haystack:
                return {'path': path, 'json_pointer': pointer, 'comparison': 'whitespace_only'}
        return None

    rows, comparisons = [], []
    for path in sorted(scope):
        source = sources[path]
        raw = source['raw_utf8'].encode('utf-8')
        assert len(raw) == tree[path]['size'] and blob(raw) == tree[path]['sha'], path
        row = {'path': path, 'language': language(path), 'scope': 'target_language_candidate' if path in primary else 'linked_supporting_source',
               **{key: source[key] for key in ('sha256', 'git_blob_sha', 'byte_count', 'evidence_file', 'evidence_pointer')},
               'pinned_git_bytes_verified': True}
        if path in ADDITIONAL_LINKED_PATHS:
            row.update(status='examined_linked_quran_companion',
                       reason='Explicitly linked Japanese Surat al-Ikhlas appendix. Quran verses, publisher title and commentary; no independent hadith narration.')
        elif path in q:
            i, entry = q[path]
            row.update(status=entry['status'], reason=entry['reason'],
                       ledger='reports/quran-hadith-extraction.json', ledger_pointer=f'/source_files/{i}')
        elif path in old:
            i, entry = old[path]
            row.update(status=entry['status'], extracted_occurrences=entry.get('extracted_occurrences', 0),
                       ledger='reports/legacy-extraction-audit.json', ledger_pointer=f'/source_coverage/{i}')
        elif '/automation-test-material-' in path or path.startswith('test-fixtures/'):
            lang = language(path)
            literal_path = f'test-fixtures/missing-book-test-material/generated/{lang}/articles/source.txt'
            assert sources[literal_path]['raw_utf8'].strip() == 'TEST TEST'
            row.update(status='excluded_explicit_test_fixture', literal_source=literal_path,
                       reason='Temporary automation material and its receipts; literal body is TEST TEST, not a religious source.')
        elif '/hadith-bank/' in path or path.endswith('/README.md'):
            row.update(status='examined_catalog_or_navigation_metadata',
                       reason='Read source catalog/README. Contains source links, integrity metadata, edition or review context; not an independent narration body.')
            if path.endswith('.json'):
                catalog = json.loads(source['raw_utf8'])
                assert catalog.get('schema') == 'iman-hadith-source-bank-v1'
                row['linked_readings'] = [r['reading']['path'] for r in catalog.get('records', [])]
                assert all(p in sources for p in row['linked_readings'])
        elif path in ('books/units/current/ja/hadith/essential-01-001.json',
                      'materials/book-publication-readers/ja/hadith/essential-01-001-current-source-v1.json'):
            projection = json.loads(source['raw_utf8'])
            other = json.loads(sources['materials/book-publication-readers/ja/hadith/essential-01-001-current-source-v1.json']['raw_utf8'])
            assert projection['sections'] == other['sections']
            original_path = 'materials/hadith/essential-ja/001.json'
            original = parsed[original_path]['readers']['ja']
            displayed = [s for _, s in leaves(projection['sections'][0])]
            assert original['main'] in displayed
            assert all(any(field['text'] in s for s in displayed) for field in original['fieldBindings'])
            assert any(binding['path'] == original_path and binding['sha256'] == sources[original_path]['sha256']
                       for binding in projection['inputBindings'])
            row.update(status='verified_compiled_mirror', canonical_source=original_path,
                       main_narration_exact=True, source_fields_checked=len(original['fieldBindings']),
                       both_compiled_sections_identical=True)
        elif path.startswith('materials/source-acceptances/'):
            acceptance = json.loads(source['raw_utf8'])
            for binding in acceptance['sourceBindings']:
                assert sources[binding['path']]['sha256'] == binding['sha256'], binding['path']
            row.update(status='verified_acceptance_metadata', bindings_checked=len(acceptance['sourceBindings']),
                       reason='Source-binding and approval metadata; no independent narration body.')
        elif path.endswith(('.md', '.txt')):
            lang, text = language(path), source['raw_utf8']
            paired = path.rsplit('.', 1)[0] + '.json'
            checks = []
            for start, end, value in quotes(text):
                hit = find_quote(value, lang, paired)
                check = {'char_start': start, 'char_end': end, 'text_sha256': digest(value.encode('utf-8'))}
                if hit:
                    check.update(status='matches_structured_source', source=hit)
                elif value in CONTEXT_PHRASES:
                    check.update(status='examined_non_narration_context', text=value, reason=CONTEXT_PHRASES[value])
                else:
                    parts = [part.strip() for part in value.splitlines() if part.strip()]
                    matches = [find_quote(part, lang, paired) for part in parts]
                    assert len(parts) > 1 and all(matches), (path, value)
                    check.update(status='matches_separate_source_fields', parts=[{'text': part, 'source': match} for part, match in zip(parts, matches)])
                checks.append(check)
            record_checks = []
            if paired in parsed:
                original = parsed[paired]
                fields = [(f'/items/{i}/text', item['text']) for i, item in enumerate(original.get('items', []))]
                fields += [(pointer, value) for pointer, value in leaves(original)
                           if re.search(r'/reading/(?:hadith|hadith_excerpts|quoted_sections)(?:/|$)', pointer)
                           and not pointer.endswith(('credit', 'reference', 'role', 'id'))]
                for pointer, value in fields:
                    check = {'json_pointer': pointer, 'source_text_sha256': digest(value.encode('utf-8'))}
                    if normalize(value) in normalize(text):
                        check['status'] = 'exact_except_layout_whitespace'
                    else:
                        changes = RENDERED_INDEX_DIFFERENCES.get(path)
                        assert changes, (path, pointer)
                        adjusted = value
                        for before, after in changes:
                            adjusted = adjusted.replace(before, after, 1)
                        assert normalize(adjusted) in normalize(text), (path, pointer)
                        check.update(status='documented_printed_number_or_footnote_marker_difference',
                                     differences=[list(change) for change in changes])
                    record_checks.append(check)
            is_note = 'SOURCE-NOTE' in path or 'SOURCE-VERSION' in path or 'SOURCE-TEXTS-' in path
            row.update(status='examined_source_note_or_carrier' if is_note else 'verified_text_rendering',
                       paired_json=paired if paired in parsed else None,
                       quotation_spans_checked=len(checks), primary_text_fields_checked=len(record_checks),
                       comparison_entry=len(comparisons),
                       reason='Exact pinned bytes preserved. Quoted spans and available primary fields compared against structured sources; context-only phrases and print-index differences separately recorded.')
            comparisons.append({'path': path, 'quotation_checks': checks, 'primary_text_checks': record_checks})
        else:
            raise AssertionError('Unclassified source path: ' + path)
        rows.append(row)

    local_rows = []
    local_catalog = json.loads((root / 'catalog/materials.json').read_bytes())
    for entry in local_catalog['legacy_materials']:
        local_raw = (root / entry['path']).read_bytes()
        assert digest(local_raw) == entry['sha256']
        relative = re.split(r'/editions/[^/]+/', entry['path'], maxsplit=1)[1]
        remote_path = f'materials/hadith/essential-{entry["language"]}/' + relative
        remote_raw = sources[remote_path]['raw_utf8'].encode('utf-8')
        if local_raw == remote_raw:
            status = 'exact_byte_mirror'
        elif entry['path'].endswith('.json'):
            assert json.loads(local_raw) == json.loads(remote_raw), entry['path']
            status = 'identical_json_different_serialization'
        else:
            assert normalize(local_raw.decode('utf-8')) == normalize(remote_raw.decode('utf-8')), entry['path']
            status = 'identical_text_different_layout_whitespace'
        local_rows.append({'path': entry['path'], 'language': entry['language'],
                           'sha256': digest(local_raw), 'byte_count': len(local_raw),
                           'source_revision': entry.get('source_revision'), 'status': status,
                           'verified_pinned_counterpart': remote_path,
                           'counterpart_git_blob_sha': tree[remote_path]['sha']})

    result = {'schema': 'hadith-bank-embedded-source-inventory-v1', 'source_repository': REPO,
              'source_commit': PIN, 'tree_sha': full_tree['sha'], 'full_tree_truncated': False,
              'full_tree_path': tree_path.relative_to(root).as_posix(), 'full_tree_sha256': digest(tree_raw),
              'scope_rule': 'All pinned paths containing hadith, quran, tadabbur or articles and target language as a path directory, essential-language directory, or JSON/MD/TXT basename; plus every linked source in both extraction ledgers.',
              'target_languages': list(LANGUAGES), 'candidate_path_count': len(primary),
              'linked_supporting_source_count': len(scope - primary), 'inventoried_files': len(rows),
              'all_original_git_blobs_verified': True,
              'local_bank_source_count': len(local_rows),
              'local_bank_source_status_counts': dict(sorted(collections.Counter(r['status'] for r in local_rows).items())),
              'status_counts': dict(sorted(collections.Counter(r['status'] for r in rows).items())),
              'original_ledgers': [{'path': p.relative_to(root).as_posix(), 'sha256': digest(p.read_bytes())} for p in (legacy_path, quran_path)],
              'supplemental_source_bundle': {'path': supplement_path.relative_to(root).as_posix(),
                                             'sha256': digest(supplement_path.read_bytes()), 'files': len(supplementary['files'])},
              'scope_qualifications': ['Counts are source occurrences and excerpts; not independently verified unique canonical hadith identities.',
                  'Full source parents, Quran verses, commentary and unselected comparison variants are preserved as evidence and not silently promoted to new narration records.',
                  'Comparison evidence distinguishes exact stored bytes, whitespace-only rendering comparisons, cited numbering/footnote differences, and examined explanatory prose.',
                  'Missing source citation and person metadata remain explicitly unresolved. This file is an extraction inventory, not an authenticity or translation certification.'],
              'files': rows, 'local_bank_sources': local_rows,
              'supplemental_text_comparisons': comparisons}
    if write:
        dump(root / REPORT, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--tree', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = run(args.root, args.snapshot, args.tree, write=not args.check)
    if args.check:
        stored = json.loads((args.root / REPORT).read_bytes())
        assert result == stored, 'Inventory differs; investigate changed source or ledger bytes'
    print(json.dumps({key: result[key] for key in ('inventoried_files', 'candidate_path_count', 'linked_supporting_source_count', 'status_counts')}, indent=2))


if __name__ == '__main__':
    main()
