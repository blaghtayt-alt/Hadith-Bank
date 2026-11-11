"""Prevent automatic counterpart joins from confusing source and citation IDs."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from counterpart_identity import provider_id, provider_identity


class CounterpartIdentityTests(unittest.TestCase):
    def test_provider_entry_and_primary_url_agree_without_mutating_record(self):
        record = {
            'book_key': 'hadeethenc', 'provider_entry_id': '2758',
            'number': {'source_entry_id': '2758'},
            'source': {'record_url': 'https://hadeethenc.com/ja/browse/hadith/2758'},
            'translation_provenance': {'origin': 'unknown'},
        }
        before = copy.deepcopy(record)
        identity = provider_identity(record)
        self.assertEqual(identity['status'], 'linked')
        self.assertEqual(identity['id'], '2758')
        self.assertEqual(identity['candidates'], ['2758'])
        self.assertIn('/source/record_url', identity['basis'])
        self.assertEqual(record, before)

    def test_positive_ascii_integer_ids_only(self):
        for value in [None, True, False, 0, -1, 1.0, '', '0', '01', '-2', '1.5', ' 3', '٣', '3\n']:
            with self.subTest(value=value):
                self.assertIsNone(provider_id({'book_key': 'hadeethenc', 'provider_entry_id': value}))
        self.assertEqual(provider_id({'book_key': 'hadeethenc', 'provider_entry_id': 123}), '123')

    def test_generic_source_field_or_collection_number_is_not_provider_identity(self):
        record = {'book_key': 'muslim', 'provider_entry_id': '74',
                  'number': {'source_entry_id': '74', 'in_book': '2654', 'canonical': '2654'}}
        self.assertEqual(provider_identity(record)['status'], 'absent')

    def test_selected_source_fields_work_in_canonical_and_projected_records(self):
        fields = [
            ('sourceUrl',), ('publication', 'url'), ('source_binding', 'sourceURL'),
            ('selected_parent', 'sourceURL'), ('selected_parent', 'source_url'),
            ('selected_parent', 'url'), ('reference_register_entry', 'sourceURL'),
        ]
        for field in fields:
            for projected in (False, True):
                with self.subTest(field=field, projected=projected):
                    metadata = {}
                    target = metadata
                    for name in field[:-1]:
                        target = target.setdefault(name, {})
                    target[field[-1]] = 'https://hadeethenc.com/api/v1/hadeeths/one/?language=hi&id=4810'
                    source = {'historical_metadata': metadata}
                    if projected:
                        source = {'original_metadata': source}
                    record = {'book_key': 'muslim', 'provider_entry_id': '74', 'source': source}
                    self.assertEqual(provider_id(record), '4810')

    def test_primary_quran_source_link_works_without_generic_provider_id(self):
        record = {'book_key': 'bukhari', 'provider_entry_id': 'H0',
                  'source': {'url': 'https://hadeethenc.com/zh/browse/hadith/4565/'}}
        self.assertEqual(provider_id(record), '4565')
        record['source'] = {'url': 'https://github.com/example/repo',
                            'original_metadata': {'url': 'https://hadeethenc.com/zh/browse/hadith/4565'}}
        self.assertEqual(provider_id(record), '4565')

    def test_incidental_commentary_and_reference_urls_never_assign_identity(self):
        url = 'https://hadeethenc.com/en/browse/hadith/4811'
        record = {'book_key': 'bukhari', 'commentary': {'translation': url},
                  'references': {'items': [{'url': url}]}, 'footnotes': [url],
                  'source': {'original_metadata': {'unrelated_note': url,
                                                   'historical_metadata': {'explanation': url}}}}
        self.assertEqual(provider_identity(record)['status'], 'absent')

    def test_conflicting_primary_source_id_and_selected_url_do_not_join(self):
        record = {'book_key': 'hadeethenc', 'provider_entry_id': '10',
                  'source': {'url': 'https://hadeethenc.com/en/browse/hadith/2'}}
        identity = provider_identity(record)
        self.assertEqual(identity['status'], 'conflict')
        self.assertEqual(identity['candidates'], ['2', '10'])
        self.assertIsNone(provider_id(record))
        url = 'https://hadeethenc.com/api/v1/hadeeths/one/?id=3&id=4'
        self.assertEqual(provider_identity({'source': {'url': url}})['status'], 'conflict')

    def test_untrusted_hosts_and_non_entry_urls_are_rejected(self):
        urls = [
            'https://hadeethenc.com.evil.invalid/en/browse/hadith/1',
            'https://evil.invalid/?next=https://hadeethenc.com/en/browse/hadith/1',
            'https://user@hadeethenc.com/en/browse/hadith/1',
            'https://hadeethenc.com:444/en/browse/hadith/1',
            'https://hadeethenc.com/en/browse/hadith/1extra',
            'https://hadeethenc.com/api/v1/hadeeths/list/?id=1',
            'https://hadeethenc.com/?id=1',
            'https://hadeethenc.com/api/v1/hadeeths/one/?id=0',
            'https://hadeethenc.com/api/v1/hadeeths/one/?id=٣',
            'https://hadeethenc.com/api/v1/hadeeths/one/?id=01',
            'https://[invalid/en/browse/hadith/1',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertIsNone(provider_id({'source': {'url': url}}))

    def test_malformed_or_absent_metadata_is_safe(self):
        for record in [None, [], {}, {'source': None}, {'source': {'historical_metadata': []}},
                       {'source': {'original_metadata': {'historical_metadata': {'selected_parent': 'not an object'}}}}]:
            with self.subTest(record=record):
                self.assertEqual(provider_identity(record)['status'], 'absent')


if __name__ == '__main__':
    unittest.main()
