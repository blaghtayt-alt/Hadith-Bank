import copy
import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import import_fawaz_bulk as source
from fawaz_held_dispositions import (
    disposition_counts, load_held_dispositions, review_resolution_for_group,
    source_view_resolution_text, verify_source_bindings,
)
from fawaz_review_inputs import load_review_catalog
from validate_fawaz_sources import verify_partition


class HeldDispositions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dispositions = load_held_dispositions(ROOT, repository=source.REPOSITORY,
                                                  revision=source.REVISION)
        report = ROOT / 'reports/fawaz-held-resolution-20261113'
        cls.held = {}
        for path in (report / 'input/held').glob('*.jsonl.gz'):
            for line in gzip.open(path, 'rt', encoding='utf-8'):
                row = json.loads(line)
                cls.held[row['provider_book'], row['typed_hadithnumber']] = row
        doc = json.loads(gzip.decompress((report / 'additional-reviews.json.gz').read_bytes()))
        cls.decisions = {(d['provider_book'], d['provider_edition'].split('-')[0],
                          d['typed_hadithnumber']): d for d in doc['decisions']}

    def runtime_rows(self, key):
        rows = copy.deepcopy(self.held[key]['source_versions'])
        for prefix, versions in rows.items():
            for item in versions:
                decision = self.decisions.get((key[0], prefix, key[1]))
                if decision:
                    quote, notes, spans = source.apply_reviewed_span(item['row']['text'], decision)
                    item.update(quotation=quote, notes=notes, spans=spans)
                    if decision.get('action') == 'source_context_only':
                        item['quotation_status'] = 'content_mismatch'
                    else:
                        item['reviewed_source_span'] = decision
        return rows

    def test_every_exact_source_field_is_bound(self):
        self.assertEqual(set(self.dispositions), set(self.held))
        self.assertEqual(len(self.held), 244)
        for key, row in self.held.items():
            verify_source_bindings(self.dispositions[key], row['source_versions'])
        fields = [field for record in self.dispositions.values() for field in record['source_fields']]
        self.assertEqual(len(fields), 895)
        self.assertEqual(sum(not field['source_text_is_empty'] for field in fields), 204)

    def test_changed_text_or_grade_or_missing_language_fails(self):
        key = ('abudawud', '2424')
        for mutation in ('text', 'grade', 'language'):
            rows = copy.deepcopy(self.held[key]['source_versions'])
            if mutation == 'text':
                rows['eng'][0]['row']['text'] += ' invented completion'
            elif mutation == 'grade':
                rows['eng'][0]['row']['grades'].append({'name': 'New assessor', 'grade': 'New grade'})
            else:
                del rows['ben']
            with self.assertRaises(ValueError):
                verify_source_bindings(self.dispositions[key], rows)

    def test_source_gap_cannot_be_filled_or_admitted(self):
        key = ('bukhari', '4843')
        rows = self.runtime_rows(key)
        with self.assertRaises(ValueError):
            review_resolution_for_group(self.dispositions, *key, rows, {'classification': 'hadith'})
        key = ('malik', '631.5')
        rows = self.runtime_rows(key)
        self.assertEqual(rows['urd'][0]['row']['text'], 'مسنگ')
        rows['urd'][0]['row']['text'] = 'A report supplied from another edition'
        with self.assertRaises(ValueError):
            review_resolution_for_group(self.dispositions, *key, rows, {'classification': 'held'})

    def test_positive_disposition_alone_never_admits_a_report(self):
        key = ('abudawud', '3339')
        with self.assertRaises(ValueError):
            review_resolution_for_group(self.dispositions, *key, self.runtime_rows(key),
                                        {'classification': 'held'})
        rows = self.runtime_rows(key)
        del rows['eng'][0]['reviewed_source_span']
        with self.assertRaises(ValueError):
            review_resolution_for_group(self.dispositions, *key, rows, {'classification': 'hadith'})

    def test_own_language_report_and_note_partitions_preserve_every_character(self):
        positives = 0
        for (book, prefix, number), decision in self.decisions.items():
            text = self.held[book, number]['source_versions'][prefix][0]['row']['text']
            quote, notes, spans = source.apply_reviewed_span(text, decision)
            verify_partition(text, spans, quote)
            if decision.get('action') == 'source_context_only':
                self.assertEqual((book, prefix, number), ('abudawud', 'ben', '3587'))
                self.assertEqual(quote, '')
                self.assertEqual(notes, [text])
            else:
                positives += 1
                self.assertNotEqual(decision['report_type'], 'prophetic_report')
        self.assertEqual(positives, 21)

    def test_existing_review_catalog_remains_additive(self):
        catalog = load_review_catalog(ROOT, repository=source.REPOSITORY, revision=source.REVISION)
        catalog_keys = {(d['provider_book'], d['provider_edition'].split('-')[0],
                         d['typed_hadithnumber']) for d in catalog['decisions']}
        self.assertTrue(set(self.decisions) <= catalog_keys)
        self.assertGreaterEqual(len(catalog_keys), 13944)

    def test_completed_exclusions_are_separate_from_unknown_holds(self):
        ledger = []
        for key, record in self.dispositions.items():
            classification = {'classification': ('hadith' if record['disposition'] == 'registered_source_report' else 'held')}
            resolution = review_resolution_for_group(self.dispositions, *key, self.runtime_rows(key), classification)
            item = {'classification': classification, 'review_resolution': resolution}
            ledger.append(item)
            if classification['classification'] == 'held':
                self.assertTrue(source_view_resolution_text(item).startswith('Review complete.'))
        counts = disposition_counts(ledger)
        self.assertEqual(counts, {'resolved_excluded_occurrences': 238,
            'resolved_source_gap_occurrences': 171, 'resolved_commentary_occurrences': 67,
            'unresolved_held_occurrences': 0, 'recovered_reviewed_occurrences': 6})
        ledger.append({'classification': {'classification': 'held'}})
        self.assertEqual(disposition_counts(ledger)['unresolved_held_occurrences'], 1)
        self.assertIsNone(source_view_resolution_text(ledger[-1]))


if __name__ == '__main__':
    unittest.main()
