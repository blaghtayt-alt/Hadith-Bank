"""Synthetic adapter fixtures only; fixture text is not religious source text."""
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import import_attachments as importer
import validate_attachments as validator


class AttachmentValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.source = self.root / 'source'
        self.candidate = self.root / 'candidate'
        datasets = []
        for format_, book, edition in [('xlsx', 'hadeethenc', 'v1.0.0'),
                                       ('pdf', 'fixture-book', 'fixture-source')]:
            directory = self.source / 'zh' / book / edition
            original = directory / 'original' / ('fixture.' + format_)
            original.parent.mkdir(parents=True)
            if format_ == 'xlsx':
                with zipfile.ZipFile(original, 'w') as archive:
                    archive.writestr('xl/workbook.xml',
                        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                        '<sheets><sheet name="Worksheet" sheetId="1" r:id="rId1"/></sheets></workbook>')
                    archive.writestr('xl/_rels/workbook.xml.rels',
                        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                        '<Relationship Id="rId1" Target="worksheets/sheet1.xml" '
                        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
                        '</Relationships>')
                    archive.writestr('xl/worksheets/sheet1.xml',
                        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                        '<sheetData><row r="3"><c r="A3"><v>101</v></c></row></sheetData></worksheet>')
            else:
                # This validator verifies preserved source bytes and declared PDF
                # bounds; it deliberately does not claim to parse/visually QC PDFs.
                original.write_bytes(b'%PDF-1.4\nSYNTHETIC SOURCE ASSET\n%%EOF\n')
            sha = hashlib.sha256(original.read_bytes()).hexdigest()
            source_id = 'fixture-' + format_
            original_rel = original.relative_to(self.source).as_posix()
            relative = directory.relative_to(self.source).as_posix()
            record = {
                'schema_version': '1.0.0', 'id': source_id + ':1',
                'language': 'zh', 'record_type': 'narration',
                'narration_unit': 'source_entry' if format_ == 'xlsx' else 'source_occurrence',
                'text': {'arabic': 'ARABIC FIXTURE' if format_ == 'xlsx' else None,
                         'translation': 'TRANSLATION FIXTURE\nWITH EXACT LINE BREAK'},
                'book': {'title': 'FIXTURE TITLE', 'chapter': 'FIXTURE CHAPTER',
                         'section': None, 'edition': 'v1.0.0' if format_ == 'xlsx' else None,
                         'compiler': None},
                'number': {'in_book': '1', 'canonical': None,
                           'source_entry_id': '101' if format_ == 'xlsx' else None},
                'narrator': {'name': None, 'verbatim': None, 'language': None},
                'source': {'source_id': source_id, 'file': original.name, 'sha256': sha,
                           'title': 'FIXTURE TITLE', 'format': format_,
                           'package_file': original_rel, 'url': None},
                'translator': {'name': 'FIXTURE HUMAN TRANSLATOR' if format_ == 'pdf' else None,
                               'evidence': 'SYNTHETIC HUMAN EVIDENCE' if format_ == 'pdf' else None},
                'page': {'pdf': [1] if format_ == 'pdf' else [], 'printed': [],
                         'sheet': 'Worksheet' if format_ == 'xlsx' else None,
                         'row': 3 if format_ == 'xlsx' else None},
                'references': {'arabic': None, 'translation': None, 'items': []},
                'commentary': {'arabic': None, 'translation': None, 'items': []},
                'footnotes': [], 'grading': {'text': None},
                'ai_translation': False if format_ == 'pdf' else 'unknown',
                'provenance': {'extraction_method': 'fixture_bytes', 'original_flag': False},
                'review': {'status': 'fixture_review_pending', 'issues': []},
            }
            records = [record]
            if format_ == 'xlsx':
                split = copy.deepcopy(record)
                split['id'] = source_id + ':2'
                split['text']['translation'] = None
                split['narration_unit'] = 'explicit_variant_occurrence'
                split['review']['issues'] = ['fixture_split_review_pending']
                records.append(split)
            importer.write_json(directory / 'records.json', records)
            importer.write_json(directory / 'source.json', {
                'source_id': source_id, 'language': 'zh', 'sha256': sha,
                'format': format_, 'version': 'v1.0.0',
                'package_original_file': original_rel,
            })
            importer.write_json(directory / 'coverage.json', {'records': len(records)})
            importer.write_json(directory / 'exceptions.json', [])
            datasets.append({
                'language': 'zh', 'source_id': source_id, 'format': format_,
                'source_file': original.name, 'source_sha256': sha,
                'records': len(records), 'records_file': relative + '/records.json',
                'source_metadata': relative + '/source.json',
                'coverage_file': relative + '/coverage.json',
                'exceptions_file': relative + '/exceptions.json',
                'source_entries': 1, 'pdf_pages': 2 if format_ == 'pdf' else None,
            })
        importer.write_json(self.source / 'catalog.json', {
            'schema_version': '1.0.0', 'record_count': 3,
            'by_language': {'zh': 3}, 'datasets': datasets,
        })
        self.write_source_manifest()
        importer.build(self.source, self.candidate)

    def tearDown(self):
        self.temp.cleanup()

    def write_source_manifest(self):
        lines = [hashlib.sha256(path.read_bytes()).hexdigest() + '  ' +
                 path.relative_to(self.source).as_posix()
                 for path in sorted(self.source.rglob('*'))
                 if path.is_file() and path.name != 'checksums.sha256']
        (self.source / 'checksums.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def read(self, relative):
        return json.loads((self.candidate / relative).read_text(encoding='utf-8'))

    def write(self, relative, value):
        importer.write_json(self.candidate / relative, value)

    def mutate_record(self, function, collection_index=0):
        """Refresh every advertised candidate checksum, so semantic checks matter."""
        catalog = self.read('collections.json')
        collection = catalog['collections'][collection_index]
        records = self.read(collection['records_path'])
        function(records[0])
        self.write(collection['records_path'], records)
        collection['records_sha256'] = importer.file_sha(self.candidate / collection['records_path'])
        self.write('collections.json', catalog)
        manifest = str(pathlib.PurePosixPath(collection['records_path']).parent / 'manifest.json')
        self.write(manifest, collection)
        language_path = 'languages/zh-CN/catalog.json'
        language = self.read(language_path)
        language['collections'] = catalog['collections']
        self.write(language_path, language)
        summary = self.read('reports/intake-summary.json')
        summary['collections'] = catalog['collections']
        self.write('reports/intake-summary.json', summary)
        importer.refresh_checksums(self.candidate)

    def assert_failed_with(self, code):
        result = validator.validate(self.candidate)
        self.assertFalse(result['success'], result)
        self.assertIn(code, {error['code'] for error in result['errors']}, result)
        return result

    def test_exact_private_intake_and_optional_report(self):
        report = self.candidate / 'reports/validation.json'
        result = validator.validate(self.candidate, report)
        self.assertTrue(result['success'], result)
        self.assertEqual(result['records_checked'], 3)
        self.assertEqual(result['records_with_exact_original_fields'], 3)
        self.assertEqual(result['ai_translation'], {'false': 1, 'unknown': 2})
        self.assertFalse(result['publication_allowed'])
        self.assertFalse(result['source_visual_qc_performed_by_this_validator'])
        self.assertEqual(self.read('reports/validation.json'), result)
        self.assertTrue(validator.validate(self.candidate)['success'])

    def test_text_tamper_fails_even_after_manifest_refresh(self):
        self.mutate_record(lambda r: r['text'].__setitem__('translation', 'ALTERED FIXTURE'))
        result = self.assert_failed_with('original_field_changed')
        self.assertFalse(any(e['code'] == 'checksum_mismatch' for e in result['errors']))
        self.assertTrue(any(e['location'].endswith('.text') for e in result['errors']))

    def test_source_path_traversal_is_rejected(self):
        self.mutate_record(lambda r: r['source'].__setitem__('package_file', '../../outside.txt'))
        self.assert_failed_with('unsafe_path')

    def test_collection_path_traversal_is_rejected_without_reading_outside(self):
        catalog = self.read('collections.json')
        catalog['collections'][0]['records_path'] = '../outside.json'
        self.write('collections.json', catalog)
        importer.refresh_checksums(self.candidate)
        self.assert_failed_with('unsafe_path')

    def test_missing_original_source_fails(self):
        catalog = self.read('collections.json')
        (self.candidate / catalog['collections'][0]['source_file']).unlink()
        importer.refresh_checksums(self.candidate)
        self.assert_failed_with('missing_file')

    def test_publication_gate_cannot_be_opened(self):
        gate = self.read('PUBLICATION-GATE.json')
        gate['allowed'] = True
        self.write('PUBLICATION-GATE.json', gate)
        importer.refresh_checksums(self.candidate)
        self.assert_failed_with('publication_gate')

    def test_original_ai_and_review_values_cannot_be_reclassified(self):
        self.mutate_record(lambda r: r.__setitem__('ai_translation', False))
        self.assert_failed_with('original_field_changed')

    def test_heading_tag_must_retain_literal_source_value(self):
        self.mutate_record(lambda r: r['source_structure_tags'][0].__setitem__('value_verbatim', 'INVENTED HEADING'))
        self.assert_failed_with('source_structure_tag')

    def test_report_cannot_overwrite_candidate_evidence(self):
        with self.assertRaises(ValueError):
            validator.validate(self.candidate, self.candidate / 'collections.json')


if __name__ == '__main__':
    unittest.main()
