import copy
import gzip
import json
from html.parser import HTMLParser
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_discovery as discovery
import build_fawaz_source_views as views
import import_fawaz_bulk as bulk


class OriginalTexts(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.active, self.parts, self.texts = False, [], []
        self.feed(markup)

    def handle_starttag(self, tag, attributes):
        if tag == 'p' and 'original-source-text' in dict(attributes).get('class', '').split():
            self.active, self.parts = True, []

    def handle_data(self, value):
        if self.active:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if tag == 'p' and self.active:
            self.texts.append(''.join(self.parts))
            self.active = False


class FawazSourceViewsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'bank'
        self.output = Path(self.temporary.name) / 'site'
        self.root.mkdir()
        self.site = {'repository_url': 'https://github.com/blaghtayt-alt/Hadith-Bank',
                     'live_url': 'https://blaghtayt-alt.github.io/Hadith-Bank/', 'source_ref': 'a' * 40}
        self.reader_ids = {'fawaz:' + bulk.REVISION[:12] + ':bukhari:1'}
        self.state = {'inputs': {}}
        catalog = {'bukhari': {'name': 'Sahih al Bukhari', 'collection': []}}
        source_versions = {}
        self.original_texts = []
        for prefix in ('ara', 'eng', 'urd', 'ben'):
            raw_text = {'ara': 'نص أصلي\n<شرح> &', 'eng': 'A compiler note <script>alert(1)</script>\n& exact text',
                        'urd': 'اصل عبارت', 'ben': 'মূল পাঠ'}[prefix]
            self.original_texts.append(raw_text)
            rows = [{'hadithnumber': 1, 'arabicnumber': 1, 'text': 'Registered quotation', 'reference': {'book': 1, 'hadith': 1}, 'grades': []},
                    {'hadithnumber': 2, 'arabicnumber': 2, 'text': raw_text, 'reference': {'book': 1, 'hadith': 2}, 'grades': [{'name': 'Source assessor', 'grade': prefix}]}]
            name = prefix + '-bukhari'
            catalog['bukhari']['collection'].append({'name': name, 'book': 'bukhari', 'language': bulk.LANGUAGES[prefix][1], 'author': 'Listed credit'})
            key = 'editions/' + name + '.json'
            saved = self.save_snapshot(key, {'metadata': {'name': catalog['bukhari']['name'],
                                                          'sections': {'1': 'Fixture section'}},
                                             'hadiths': rows})
            source_versions[prefix] = [{'position': 1, 'row': rows[1], 'source_path': saved['path'], 'source_sha256': saved['sha256'],
                                        'text_spans': {'quotation': [0, len(raw_text)], 'notes': []}}]
        self.save_snapshot('editions.json', catalog)
        availability = {code: 'available' for code in ('ar', 'en', 'ur', 'bn')}
        self.ledger = [{'provider_book': 'bukhari', 'typed_hadithnumber': '1', 'classification': {'classification': 'hadith', 'reason': 'explicit_source_attribution'}, 'language_availability': availability},
                       {'provider_book': 'bukhari', 'typed_hadithnumber': '2', 'classification': {'classification': 'held', 'reason': 'prophetic_attribution_or_quotation_boundary_not_established'}, 'language_availability': availability}]
        self.held = [{**copy.deepcopy(self.ledger[1]), 'show_in_html_hadith': False, 'source_versions': source_versions}]
        self.progress = {'revision': bulk.REVISION, 'provider_occurrences': 2, 'held_occurrences': 1,
                         'by_book': {'bukhari': {'provider_occurrences': 2, 'registered_occurrences': 1, 'held_occurrences': 1,
                                                'processed_languages': ['ara', 'eng', 'urd', 'ben']}}}
        self.save_inputs()

    def save_snapshot(self, key, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        saved = bulk.snapshot(self.root, key, raw, {'url': bulk.provider_url(key)})
        self.state['inputs'][key] = saved
        return saved

    def save_inputs(self):
        for name, data in [('state.json', self.state), ('progress.json', self.progress)]:
            bulk.save_json(self.root, bulk.IMPORT + '/' + name, data)
        for folder, values in [('held', self.held), ('classification', self.ledger)]:
            path = self.root / bulk.IMPORT / folder / 'bukhari.jsonl.gz'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(b''.join(bulk.encoded(item) for item in values), mtime=0))

    def render(self):
        self.writer = discovery.Writer(self.root, self.output, self.site)
        return views.render(self.writer, reader_occurrence_ids=self.reader_ids)

    def test_every_id_has_destination_and_original_fields_survive_html_escaping(self):
        report = self.render()
        self.assertEqual(report['provider_occurrences'], 2)
        self.assertEqual(report['original_source_pages'], 1)
        self.assertEqual(report['reader_occurrences'], 1)
        self.assertFalse(report['included_in_narration_search'])
        self.assertEqual(self.writer.pages, [])
        detail = (self.output / views.source_path('bukhari', '2')).read_text()
        self.assertEqual(OriginalTexts(detail).texts, self.original_texts)
        self.assertNotIn('<script>alert(1)</script>', detail)
        self.assertIn('noindex,follow', detail)
        self.assertIn('data-source-languages="ur"', detail)
        self.assertIn('References and source for this language', detail)
        for prefix in ('ara', 'eng', 'urd', 'ben'):
            self.assertIn(bulk.entry_url(prefix + '-bukhari', 2), detail)
        index = (self.output / views.BASE / 'bukhari/index.html').read_text()
        self.assertIn('Provider entry 1', index)
        self.assertIn('Provider entry 2', index)
        self.assertIn('?occurrence=fawaz%3A' + bulk.REVISION[:12] + '%3Abukhari%3A1', index)
        self.assertIn(Path(views.source_path('bukhari', '2')).name, index)
        self.assertEqual(report['pages'], 3)

    def test_tampered_held_wording_or_metadata_fails_against_pinned_original(self):
        for field, value in [('text', 'replacement'), ('grades', []), ('reference', {'book': 999})]:
            with self.subTest(field=field):
                original = self.held[0]['source_versions']['eng'][0]['row'][field]
                self.held[0]['source_versions']['eng'][0]['row'][field] = value
                self.save_inputs()
                with self.assertRaisesRegex(ValueError, 'Original source field mismatch'):
                    self.render()
                self.held[0]['source_versions']['eng'][0]['row'][field] = original

    def test_missing_held_id_fails_accounting(self):
        self.held = []
        self.save_inputs()
        with self.assertRaisesRegex(ValueError, 'Incomplete source-view occurrence accounting'):
            self.render()

    def test_phantom_or_type_changed_ledger_id_fails_saved_edition_union(self):
        # Matching counts do not prove the actual provider IDs were preserved.
        # Integer 1, decimal 1.0 and string "1" are distinct source identities.
        for identity in ('999', '1.0', '"1"'):
            with self.subTest(identity=identity):
                self.ledger[0]['typed_hadithnumber'] = identity
                self.save_inputs()
                with self.assertRaises(ValueError):
                    self.render()

    def test_missing_held_language_is_not_silently_omitted(self):
        # Its row still exists in the saved English edition, and the ledger
        # still declares English available; three rendered languages are not
        # a complete original-source view of this occurrence.
        del self.held[0]['source_versions']['eng']
        self.save_inputs()
        with self.assertRaises(ValueError):
            self.render()

    def test_missing_duplicate_id_position_is_not_silently_omitted(self):
        key = 'editions/eng-bukhari.json'
        data = json.loads(bulk.checked_snapshot(self.root, self.state['inputs'][key]))
        duplicate = copy.deepcopy(data['hadiths'][1])
        duplicate['text'] = 'A second exact source row under the same provider ID'
        data['hadiths'].append(duplicate)
        saved = self.save_snapshot(key, data)
        version = self.held[0]['source_versions']['eng'][0]
        version['source_path'], version['source_sha256'] = saved['path'], saved['sha256']
        self.save_inputs()
        with self.assertRaises(ValueError):
            self.render()

    def test_duplicate_id_and_empty_source_field_remain_one_occurrence(self):
        key = 'editions/eng-bukhari.json'
        data = json.loads(bulk.checked_snapshot(self.root, self.state['inputs'][key]))
        duplicate = copy.deepcopy(data['hadiths'][1])
        duplicate['text'] = ''
        data['hadiths'].append(duplicate)
        saved = self.save_snapshot(key, data)
        versions = self.held[0]['source_versions']['eng']
        versions[0]['source_path'], versions[0]['source_sha256'] = saved['path'], saved['sha256']
        versions.append({'position': 2, 'row': duplicate, 'source_path': saved['path'],
                         'source_sha256': saved['sha256'],
                         'text_spans': {'quotation': [0, 0], 'notes': []}})
        self.save_inputs()
        report = self.render()
        self.assertEqual(report['provider_occurrences'], 2)
        self.assertEqual(report['original_source_pages'], 1)
        detail = (self.output / views.source_path('bukhari', '2')).read_text()
        self.assertEqual(OriginalTexts(detail).texts, self.original_texts)
        self.assertEqual(detail.count('References and source for this language'), 5)
        self.assertIn('The provider supplied an empty text field for this language.', detail)

    def test_repeated_same_source_position_does_not_inflate_readings(self):
        versions = self.held[0]['source_versions']['eng']
        versions.append(copy.deepcopy(versions[0]))
        self.save_inputs()
        with self.assertRaises(ValueError):
            self.render()

    def test_valid_snapshots_cannot_be_relabelled_under_other_language_keys(self):
        # Swap both the valid descriptors and their matching held rows: all
        # raw hashes, source positions and row comparisons still agree. The
        # input-key/source-path binding must catch the wrong language labels.
        ara, eng = 'editions/ara-bukhari.json', 'editions/eng-bukhari.json'
        self.state['inputs'][ara], self.state['inputs'][eng] = self.state['inputs'][eng], self.state['inputs'][ara]
        versions = self.held[0]['source_versions']
        versions['ara'], versions['eng'] = versions['eng'], versions['ara']
        self.save_inputs()
        with self.assertRaises(ValueError):
            self.render()

    def test_registered_destinations_require_verified_reader_occurrence_ids(self):
        for reader_ids in (set(), {'fawaz:' + bulk.REVISION[:12] + ':bukhari:999'}):
            with self.subTest(reader_ids=reader_ids):
                self.reader_ids = reader_ids
                with self.assertRaises(ValueError):
                    self.render()

    def test_source_views_do_not_infer_reader_ids_when_caller_omits_them(self):
        writer = discovery.Writer(self.root, self.output, self.site)
        with self.assertRaises(ValueError):
            views.render(writer)

    def test_source_pages_are_stable_under_pagination(self):
        with patch.object(views, 'PAGE_SIZE', 1):
            report = self.render()
        self.assertEqual(report['pages'], 4)
        self.assertTrue((self.output / views.source_path('bukhari', '2')).is_file())
        self.assertTrue((self.output / views.BASE / 'bukhari/page-2.html').is_file())

    def test_missing_intake_adds_no_pages(self):
        (self.root / bulk.IMPORT / 'progress.json').unlink()
        report = self.render()
        self.assertEqual(report['pages'], 0)
        self.assertEqual(self.writer.files, 0)


if __name__ == '__main__':
    unittest.main()
