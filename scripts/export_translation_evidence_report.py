"""Produce a compact CSV index of the reviewed primary-translation decisions."""
import argparse
import csv
import json
from pathlib import Path
from audit_translation_evidence import audit

FIELDS = ('occurrence_id', 'language', 'book', 'source_reference', 'source_number', 'reported_references',
          'classification', 'source_url', 'translator', 'evidence_locator',
          'model', 'translation_status', 'review_status')


def export(root, output):
    root = Path(root).resolve()
    ledger_path = root / 'catalog/translation-evidence-decisions-20261113.json'
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    decisions = {item['occurrence_id']: item for item in ledger['decisions']}
    records = {}
    for path in sorted((root / 'materials').glob('legacy-*/records.json')):
        for row in json.loads(path.read_text(encoding='utf-8')):
            if row.get('id') in decisions:
                if row['id'] in records:
                    raise ValueError('Duplicate occurrence ID: ' + row['id'])
                records[row['id']] = row
    if set(records) != set(decisions):
        raise ValueError('Missing or extra decision occurrences')
    projected = ({'id': row['id'], 'language': row['language'],
                  'text_translation': row['text']['translation']} for row in records.values())
    audit(projected, ledger, root)
    with Path(output).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        for identifier in sorted(records):
            row = records[identifier]; decision = decisions[identifier]
            source = row.get('source') or {}; metadata = source.get('historical_metadata') or {}
            binding = metadata.get('source_binding') or {}
            references = (row.get('references') or {}).get('items') or []
            cited = '; '.join(' '.join(str(item.get(k) or '') for k in ('collection', 'number')).strip()
                              + ' [' + str(item.get('scope') or 'unspecified') + ']'
                              for item in references if isinstance(item, dict)
                              and (item.get('collection') or item.get('number')))
            value = {
                'occurrence_id': identifier, 'language': row['language'], 'book': row['book_key'],
                'source_reference': source.get('title') or '',
                'source_number': (row.get('number') or {}).get('in_book') or '',
                'reported_references': cited,
                'classification': decision['classification'],
                'source_url': binding.get('sourceURL') or source.get('url') or '',
                'translator': (row.get('translator') or {}).get('name') or 'unknown',
                'evidence_locator': decision['evidence_path'] + ' :: ' + decision['evidence_locator'],
                'model': decision.get('actual_model') or 'unknown',
                'translation_status': metadata.get('translationStatus') or 'source credit',
                'review_status': metadata.get('translationReviewStatus') or 'not established by this audit',
            }
            # Guard spreadsheet formula evaluation for source-supplied cells.
            for key, item in value.items():
                if isinstance(item, str) and item.lstrip().startswith(('=', '+', '-', '@')):
                    value[key] = "'" + item
            writer.writerow(value)
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print('Exported reviewed occurrence rows:', export(args.root, args.output))


if __name__ == '__main__':
    main()
