#!/usr/bin/env python3
"""Freeze reviewed extraction evidence for the Targhib import adapter."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis-root', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    source = args.analysis_root.resolve()
    target = args.root.resolve() / 'imports/persian-targhib-20261111'
    for name in ('audit', 'extracted', 'tools', 'audit/native-paragraphs'):
        (target / name).mkdir(parents=True, exist_ok=True)

    def put(relative, data):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == '.gz' else data)

    # Freeze exact prior and continuing review evidence without normalizing it.
    for path in sorted(source.iterdir()):
        if path.suffix in ('.json', '.jsonl'):
            put('audit/' + path.name + '.gz', path.read_bytes())
    for path in sorted((source / 'source').glob('*.json*')):
        put('audit/native-paragraphs/' + path.name + '.gz', path.read_bytes())
    for volume in (1, 2, 3):
        for name in ('records', 'paragraph-ledger', 'blocks', 'excluded', 'references-audit', 'ambiguities'):
            path = source / f'targhib-candidates/v{volume}-{name}.jsonl'
            put(('extracted/' if name == 'records' else 'audit/') + path.name + '.gz', path.read_bytes())
        path = source / f'targhib-candidates/v{volume}-summary.json'
        put('audit/' + path.name, path.read_bytes())
    put('extracted/ancillary-targhib.jsonl.gz', (source / 'ancillary-targhib.jsonl').read_bytes())
    put('extracted/excluded-source-units.json.gz', (source / 'excluded-source-units.json').read_bytes())

    original = json.loads((source / 'inline-commentary-patches.json').read_text())
    merged = {}
    history = []
    paths = [source / 'inline-commentary-patches.json'] + sorted(source.glob('v*-inline-commentary-patches.json'))
    for path in paths:
        value = json.loads(path.read_text())
        patches = value['patches'] if isinstance(value, dict) else value
        history.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'paragraphs': len(patches)})
        for patch in patches:
            key = (patch['volume'], patch['paragraph_1based'])
            if key not in merged:
                merged[key] = copy.deepcopy(patch)
                continue
            current = merged[key]
            assert current['source_sha256'] == patch['source_sha256'] and current['source_text'] == patch['source_text'], key
            by_span = {(span['start'], span['end']): span for span in current['remove_spans']}
            for span in patch['remove_spans']:
                previous = by_span.get((span['start'], span['end']))
                assert not previous or previous['text'] == span['text'], key
                by_span.setdefault((span['start'], span['end']), copy.deepcopy(span))
            current['remove_spans'] = list(by_span.values())
    for key, patch in merged.items():
        text = patch['source_text']
        assert hashlib.sha256(text.encode()).hexdigest() == patch['source_sha256'], key
        spans = sorted(patch['remove_spans'], key=lambda item: item['start'])
        for index, span in enumerate(spans):
            assert text[span['start']:span['end']] == span['text'], key
            assert index == 0 or spans[index - 1]['end'] <= span['start'], key
        after = text
        for span in reversed(spans):
            after = after[:span['start']] + after[span['end']:]
        patch['remove_spans'] = spans
        patch['after_exact_span_removal'] = after
    combined = {'schema_version': 1, 'scope': original.get('scope'),
                'review_history': history, 'independent_certification_claimed': False,
                'patches': [merged[key] for key in sorted(merged)]}
    put('extracted/inline-commentary-patches.json.gz', encode(combined))

    extra = []
    for path in sorted(source.glob('v*-additional-quotation-spans.json')):
        extra.extend(json.loads(path.read_text()))
    put('extracted/additional-quotation-spans.json.gz', encode(extra))
    qualifications = []
    for path in sorted(source.glob('v*-review-notes.json')):
        notes = json.loads(path.read_text())
        for item in notes.get('source_defect_qualifications', []):
            if item.get('source_number') != '3964':  # Preserved in the original ideology audit.
                qualifications.append(item)
    qualifications.extend([
        {'paragraph_id': 'v1:document:p05179', 'issue': 'The original source punctuation has an unmatched bracket. Exact punctuation is retained without an inferred repair.'},
        {'paragraph_id': 'v2:document:p01750', 'issue': 'The source alternative reading has irregular quotation closure; its exact selected wording is retained without reconstruction.'},
        {'paragraph_id': 'v2:document:p00265', 'issue': 'The original Persian paragraph lacks a closing quotation mark before the following Companion report; no mark was invented.'},
    ])
    put('audit/source-qualifications.json.gz', encode(qualifications))

    # Retain the exact segmentation logic, with only portable evidence paths.
    extractor = (source / 'extract_targhib.py').read_text()
    extractor = extractor.replace('import json,re,collections,hashlib', 'import json,re,collections,hashlib,gzip')
    extractor = extractor.replace('BASE=Path(__file__).resolve().parent', "BASE=Path(__file__).resolve().parents[1]/'audit'")
    extractor = extractor.replace("SOURCE=BASE/'source'; OUT=BASE/'targhib-candidates';OUT.mkdir(exist_ok=True)",
                                  "SOURCE=BASE/'native-paragraphs'; OUT=BASE/'recomputed-candidates';OUT.mkdir(exist_ok=True)")
    extractor = extractor.replace("REPO=BASE.parent/'Hadith-Bank'", "REPO=Path(__file__).resolve().parents[3]")
    marker = 'DECISIONS={}\n'
    helper = "def read_frozen(path):\n return path.read_text() if path.exists() else gzip.decompress(Path(str(path)+'.gz').read_bytes()).decode('utf-8')\n"
    extractor = extractor.replace(marker, helper + marker)
    extractor = extractor.replace("BASE.glob('v*-ambiguity-decisions.json')", "BASE.glob('v*-ambiguity-decisions.json.gz')")
    extractor = extractor.replace('json.loads(decision_path.read_text())', "json.loads(gzip.decompress(decision_path.read_bytes()).decode('utf-8'))")
    extractor = extractor.replace("(SOURCE/f'v{v}-document.jsonl').read_text()", "read_frozen(SOURCE/f'v{v}-document.jsonl')")
    put('tools/extract_reviewed_body.py', extractor.encode())
    put('tools/prepare_frozen_inputs.py', Path(__file__).read_bytes())
    manifest = []
    for path in sorted(target.rglob('*')):
        if path.is_file() and path.name not in ('evidence-manifest.json', 'final-text-spans.jsonl.gz', 'omitted-non-hadith-source-units.jsonl.gz', 'README.md'):
            manifest.append({'path': path.relative_to(args.root.resolve()).as_posix(),
                             'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    put('evidence-manifest.json', encode({'schema': 'persian-targhib-frozen-evidence-v1',
        'independent_certification_claimed': False, 'inline_paragraphs': len(merged),
        'inline_removed_spans': sum(len(p['remove_spans']) for p in merged.values()),
        'additional_quotation_selections': len(extra), 'files': manifest}))
    print(json.dumps({'frozen_files': len(manifest), 'inline_paragraphs': len(merged),
                      'inline_removed_spans': sum(len(p['remove_spans']) for p in merged.values()),
                      'additional_quotation_selections': len(extra)}))


if __name__ == '__main__':
    main()
