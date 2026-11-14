"""Download-role regressions using synthetic files, never source-book content."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_book_catalog


class BookDownloadColumnsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / 'catalog').mkdir()
        self.settings = {
            'repository_url': 'https://github.com/example/synthetic-bank',
            'source_ref': 'test/download-labels',
            'live_url': 'https://example.test/bank/',
        }

    def add_file(self, relative):
        content = ('SYNTHETIC FILE ONLY: ' + relative + '\n').encode('utf-8')
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return {'path': relative, 'sha256': hashlib.sha256(content).hexdigest()}

    def material(self, relative='materials/synthetic/source.pdf', **overrides):
        source = self.add_file(relative)
        result = {
            'dataset_id': 'synthetic-edition',
            'language': 'ja',
            'book_key': 'unclassified',
            'edition': 'synthetic-volume-1',
            'count': 3,
            'source_name': 'SYNTHETIC SUPPLIED EDITION',
            'source_file': source['path'],
            'source_sha256': source['sha256'],
            'supporting_files': [],
            'available_locally': True,
            'public_text_published': True,
            'review_status': {'independent_certification': False},
            'translation_provenance': {'origin': 'unknown'},
        }
        result.update(overrides)
        return result

    def mapped_material(self):
        material = self.material()
        word = self.add_file('materials/synthetic/corrected text.docx')
        pdf = self.add_file('materials/synthetic/corrected text.pdf')
        notes = self.add_file('materials/synthetic/correction notes.txt')
        material['supporting_files'] = deepcopy([word, pdf, notes])
        metadata = {material['dataset_id']: {
            'source_file': material['source_file'],
            'source_sha256': material['source_sha256'],
            'extracted_text': [word, pdf],
            'notes': notes,
            'qualification': 'Corrected extraction; disclosed AI edits | limited\n<synthetic review>',
        }}
        return material, metadata

    def columns(self, material, metadata=None):
        return build_book_catalog.download_columns(
            self.root, material, self.settings, metadata or {})

    def file_url(self, relative, kind='raw'):
        return ('https://github.com/example/synthetic-bank/' + kind +
                '/test%2Fdownload-labels/' + quote(relative, safe='/'))

    def save_metadata(self, entries):
        (self.root / 'catalog/book-downloads.json').write_text(json.dumps({
            'schema': 'hadith-bank-book-downloads-v1', 'editions': entries,
        }), encoding='utf-8')

    def generate(self, materials):
        catalog = {'title': 'Synthetic catalog only', 'materials': materials}
        result = build_book_catalog.write_catalog(self.root, catalog, self.settings)
        document = (self.root / 'catalog/BOOKS.md').read_text(encoding='utf-8')
        return result, document

    @staticmethod
    def edition_rows(document):
        return [line for line in document.splitlines()
                if line.startswith('| ') and '<code>' in line]

    def test_native_word_inputs_remain_supplied_sources(self):
        for extension in ('.doc', '.DOCX'):
            with self.subTest(extension=extension):
                # A suggestive filename and a supporting PDF are not provenance.
                material = self.material('materials/synthetic/corrected 原本' + extension)
                material['supporting_files'] = [
                    self.add_file('materials/synthetic/unmapped-generated.pdf')]
                extracted, original, other = self.columns(material)
                self.assertEqual(extracted, 'Not linked')
                self.assertIn('Original PDF unverified', original)
                self.assertNotIn('[Original source (PDF)]', original)
                self.assertEqual(other, '[Supplied source (Word ' + extension.lower() +
                                 ')](' + self.file_url(material['source_file']) + ')')
                self.assertNotIn('unmapped-generated', extracted + original + other)

    def test_only_the_recorded_primary_pdf_is_an_original_source(self):
        material = self.material('materials/synthetic/exact source 原本.PDF')
        material['supporting_files'] = [
            self.add_file('materials/synthetic/another-edition.pdf')]
        extracted, original, other = self.columns(material)
        self.assertEqual(original, '[Original source (PDF)](' +
                         self.file_url(material['source_file']) + ')')
        self.assertEqual(extracted, 'Not linked')
        self.assertEqual(other, '—')
        self.assertNotIn('another-edition', original)

    def test_descriptor_source_fallback_keeps_the_same_binding(self):
        material, metadata = self.mapped_material()
        source_path = material.pop('source_file')
        material['source_descriptor'] = {
            'path': source_path, 'sha256': material.pop('source_sha256'),
            'name': 'SYNTHETIC DESCRIPTOR EDITION',
        }
        extracted, original, _ = self.columns(material, metadata)
        self.assertIn('[Extracted text (Word)]', extracted)
        self.assertEqual(original, '[Original source (PDF)](' + self.file_url(source_path) + ')')

    def test_corrected_derivatives_keep_their_roles_and_qualification(self):
        material, metadata = self.mapped_material()
        before = deepcopy((material, metadata))
        entry = metadata[material['dataset_id']]
        extracted, original, other = self.columns(material, metadata)
        self.assertIn('[Extracted text (Word)](' +
                      self.file_url(entry['extracted_text'][0]['path']) + ')', extracted)
        self.assertIn('[Extracted text (PDF)](' +
                      self.file_url(entry['extracted_text'][1]['path']) + ')', extracted)
        self.assertIn('Corrected extraction; disclosed AI edits &#124; limited &lt;synthetic review&gt;',
                      extracted)
        self.assertIn('[preserved correction notes](' +
                      self.file_url(entry['notes']['path'], 'blob') + ')', extracted)
        self.assertNotIn('|', extracted)
        self.assertNotIn('\n', extracted)
        self.assertEqual(original, '[Original source (PDF)](' +
                         self.file_url(material['source_file']) + ')')
        self.assertNotIn('corrected%20text', original + other)
        self.assertEqual(other, '—')
        self.assertEqual((material, metadata), before)

    def test_mapping_requires_the_exact_source_path_and_declared_hash(self):
        for fault in ('other-path', 'other-hash', 'missing-source-hash'):
            with self.subTest(fault=fault):
                material, metadata = self.mapped_material()
                entry = metadata[material['dataset_id']]
                if fault == 'other-path':
                    entry['source_file'] = 'materials/another-edition/source.pdf'
                elif fault == 'other-hash':
                    entry['source_sha256'] = '0' * 64
                else:
                    material.pop('source_sha256')
                with self.assertRaises(ValueError):
                    self.columns(material, metadata)

    def test_derivatives_and_notes_require_preserved_support_bindings(self):
        faults = ('undeclared-path', 'wrong-hash', 'missing-hash',
                  'missing-catalog-hash', 'missing-file', 'primary-source-alias')
        for role in ('derivative', 'notes'):
            for fault in faults:
                with self.subTest(role=role, fault=fault):
                    material, metadata = self.mapped_material()
                    entry = metadata[material['dataset_id']]
                    item = entry['notes'] if role == 'notes' else entry['extracted_text'][0]
                    target = item['path']
                    if fault == 'undeclared-path':
                        material['supporting_files'] = [
                            support for support in material['supporting_files']
                            if support['path'] != target]
                    elif fault == 'wrong-hash':
                        item['sha256'] = '0' * 64
                    elif fault == 'missing-hash':
                        item.pop('sha256')
                    elif fault == 'missing-catalog-hash':
                        next(support for support in material['supporting_files']
                             if support['path'] == target).pop('sha256')
                    elif fault == 'missing-file':
                        (self.root / target).unlink()
                    else:
                        item.update(path=material['source_file'], sha256=material['source_sha256'])
                        material['supporting_files'].append(deepcopy(item))
                    with self.assertRaises(ValueError):
                        self.columns(material, metadata)

    def test_source_and_support_paths_cannot_escape_or_normalize_silently(self):
        unsafe_paths = (
            '../outside.pdf', '/outside.pdf', 'materials//source.pdf',
            'materials/./source.pdf', 'materials\\source.pdf',
            'https://example.test/source.pdf', 'materials/bad\nsource.pdf',
        )
        for role in ('source', 'derivative', 'notes'):
            for unsafe in unsafe_paths:
                with self.subTest(role=role, path=repr(unsafe)):
                    material, metadata = self.mapped_material()
                    entry = metadata[material['dataset_id']]
                    if role == 'source':
                        material['source_file'] = unsafe
                        entry['source_file'] = unsafe
                    elif role == 'notes':
                        entry['notes']['path'] = unsafe
                    else:
                        entry['extracted_text'][0]['path'] = unsafe
                    with self.assertRaises(ValueError):
                        self.columns(material, metadata)

    def test_symlinks_are_rejected_even_when_the_target_is_inside_the_bank(self):
        for role in ('source', 'derivative', 'notes'):
            with self.subTest(role=role):
                material, metadata = self.mapped_material()
                entry = metadata[material['dataset_id']]
                item = ({'path': material['source_file'], 'sha256': material['source_sha256']}
                        if role == 'source' else entry['notes'] if role == 'notes'
                        else entry['extracted_text'][0])
                link = 'materials/synthetic/' + role + '-link' + Path(item['path']).suffix
                (self.root / link).symlink_to(self.root / item['path'])
                item['path'] = link
                if role == 'source':
                    material['source_file'] = link
                    entry['source_file'] = link
                else:
                    material['supporting_files'].append(deepcopy(item))
                with self.assertRaises(ValueError):
                    self.columns(material, metadata)

    def test_missing_primary_pdf_never_promotes_an_alternative_pdf(self):
        material = self.material()
        (self.root / material['source_file']).unlink()
        material['source_descriptor'] = {'url': 'https://example.test/publisher-candidate.pdf'}
        material['supporting_files'] = [self.add_file('materials/synthetic/alternative.pdf')]
        extracted, original, other = self.columns(material)
        self.assertEqual(extracted, 'Not linked')
        self.assertEqual(original, 'Original PDF unverified')
        self.assertEqual(other, '[Source data](' + self.file_url(material['source_file'], 'blob') + ')')
        self.assertNotIn('alternative.pdf', extracted + original + other)
        self.assertNotIn('publisher-candidate', extracted + original + other)

    def test_a_publisher_url_without_a_preserved_file_stays_unverified(self):
        material = self.material()
        material.pop('source_file')
        material.pop('source_sha256')
        material['source_descriptor'] = {'url': 'https://example.test/candidate.pdf'}
        self.assertEqual(self.columns(material),
                         ('Not linked', 'Original PDF unverified', 'See record provenance'))

    def test_non_document_source_data_link_is_retained(self):
        material = self.material('materials/synthetic/source data.jsonl.gz')
        extracted, original, other = self.columns(material)
        self.assertEqual(extracted, 'Not linked')
        self.assertEqual(original, 'Original PDF unverified')
        self.assertEqual(other, '[Source data](' + self.file_url(material['source_file'], 'blob') + ')')

    def test_a_mapping_cannot_claim_extraction_without_a_supported_download(self):
        for fault in ('no-downloads', 'unsupported-format'):
            with self.subTest(fault=fault):
                material, metadata = self.mapped_material()
                entry = metadata[material['dataset_id']]
                entry['extracted_text'] = []
                if fault == 'unsupported-format':
                    text_file = self.add_file('materials/synthetic/extracted.txt')
                    material['supporting_files'].append(deepcopy(text_file))
                    entry['extracted_text'] = [text_file]
                with self.assertRaises(ValueError):
                    self.columns(material, metadata)

    def test_catalog_keeps_publication_filter_titles_counts_and_read_identity(self):
        word = self.material('materials/synthetic/原本.docx', dataset_id='public-word',
                             edition='volume-b', count=1234,
                             source_name='原題 | Synthetic & <title>\nSecond line')
        pdf = self.material('materials/synthetic/volume-a.pdf', dataset_id='public-pdf',
                            edition='volume-a', count=2)
        pdf['source_descriptor'] = {'path': pdf.pop('source_file'),
                                    'name': 'SYNTHETIC DESCRIPTOR TITLE'}
        pdf.pop('source_name')
        data = self.material('materials/synthetic/data.jsonl', dataset_id='public-data',
                             language='en', edition='source-data', count=7)
        hidden = dict(word, dataset_id='unpublished', source_name='HIDDEN UNPUBLISHED TITLE',
                      public_text_published=False, edition='../hidden', count=9000000)
        unavailable = dict(word, dataset_id='unavailable', source_name='HIDDEN UNAVAILABLE TITLE',
                           available_locally=False, edition='../hidden', count=8000000)
        materials = [word, hidden, data, unavailable, pdf]
        before = deepcopy(materials)
        result, document = self.generate(materials)
        self.assertEqual(result, {'languages': 2, 'collection_language_pairs': 2, 'source_editions': 3})
        self.assertIn('Extracted text | Original source (PDF) | Other source formats', document)
        self.assertIn('— 1,236 source occurrences', document)
        self.assertIn('— 7 source occurrences', document)
        self.assertNotIn('HIDDEN', document)
        self.assertNotIn('../hidden', document)
        rows = self.edition_rows(document)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(len(row.split('|')[1:-1]) == 6 for row in rows))
        word_row = next(row for row in rows if '<code>volume-b</code>' in row)
        cells = [cell.strip() for cell in word_row.split('|')[1:-1]]
        self.assertEqual(cells[0], '原題 &#124; Synthetic &amp; &lt;title&gt; Second line<br><code>volume-b</code>')
        self.assertEqual(cells[1], '1,234')
        self.assertEqual(cells[2], '[Read edition](https://example.test/bank/browse/ja/unclassified/volume-b/)')
        self.assertEqual(cells[3], 'Not linked')
        self.assertIn('Supplied source (Word .docx)', cells[5])
        pdf_row = next(row for row in rows if '<code>volume-a</code>' in row)
        self.assertIn('SYNTHETIC DESCRIPTOR TITLE', pdf_row)
        self.assertIn('/browse/ja/unclassified/volume-a/', pdf_row)
        self.assertIn('| 2 |', pdf_row)
        self.assertEqual(materials, before)

    def test_catalog_reads_explicit_derivative_metadata_without_losing_notes(self):
        material, metadata = self.mapped_material()
        self.save_metadata(metadata)
        _, document = self.generate([material])
        row, = self.edition_rows(document)
        cells = [cell.strip() for cell in row.split('|')[1:-1]]
        self.assertEqual(len(cells), 6)
        self.assertIn('Extracted text (Word)', cells[3])
        self.assertIn('Extracted text (PDF)', cells[3])
        self.assertIn('disclosed AI edits', cells[3])
        self.assertIn('preserved correction notes', cells[3])
        self.assertIn('Original source (PDF)', cells[4])
        self.assertNotIn('corrected%20text', cells[4])

    def test_stale_metadata_id_is_rejected_before_overwriting_the_directory(self):
        material, metadata = self.mapped_material()
        self.save_metadata({'no-longer-in-the-catalog': metadata[material['dataset_id']]})
        previous = self.root / 'catalog/BOOKS.md'
        previous.write_text('SYNTHETIC PREVIOUS DIRECTORY', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.generate([material])
        self.assertEqual(previous.read_text(encoding='utf-8'), 'SYNTHETIC PREVIOUS DIRECTORY')

    def test_empty_or_nonobject_metadata_entries_cannot_be_silently_ignored(self):
        material = self.material()
        for invalid in ({}, [], None, ''):
            with self.subTest(entry=invalid):
                self.save_metadata({material['dataset_id']: invalid})
                with self.assertRaises(ValueError):
                    self.generate([material])


if __name__ == '__main__':
    unittest.main()
