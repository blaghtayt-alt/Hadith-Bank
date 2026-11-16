"""Verify registered Malay fields against the exact preserved publisher workbook."""
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / 'materials/ms-hadeethenc-v1-2-0-50095a98'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

class PublisherWorkbookBindingTests(unittest.TestCase):
    def test_native_body_title_grade_and_citation_bind_to_original_cells(self):
        workbook = MATERIAL / 'source.xlsx'
        self.assertEqual(hashlib.sha256(workbook.read_bytes()).hexdigest(),
                         '50095a987d9486d986d01f31c758dceff4b8d349bc6f1f54bdfaf7f860374f03')
        with zipfile.ZipFile(workbook) as archive:
            self.assertIsNone(archive.testzip())
            strings = [''.join(t.text or '' for t in s.findall('.//m:t', NS))
                       for s in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
            sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
            cells = {}
            for cell in sheet.findall('.//m:sheetData/m:row/m:c', NS):
                value = cell.find('m:v', NS)
                value = value.text if value is not None else ''
                cells[cell.get('r')] = strings[int(value)] if cell.get('t') == 's' else value
        records = json.loads((MATERIAL / 'records.json').read_bytes())
        manifest = json.loads((MATERIAL / 'manifest.json').read_bytes())
        self.assertEqual(len(records), 147)
        self.assertEqual(len({r['id'] for r in records}), 147)
        self.assertEqual(manifest['counterpart_policy']['mode'], 'disabled')
        for record in records:
            row = str(record['source']['row_one_based'])
            with self.subTest(id=record['id'], source_row=row):
                self.assertEqual(record['source']['provider_record_id'], cells['A' + row])
                self.assertEqual(record['text']['translation'], cells['E' + row])
                self.assertEqual(record['title'], cells.get('C' + row) or None)
                self.assertEqual(record['grading']['grade_as_printed'], cells.get('L' + row, ''))
                self.assertEqual(record['references']['source_citation_as_supplied'], cells.get('M' + row, ''))
                self.assertEqual(record['references']['citation_as_printed'], cells.get('M' + row) or None)
                self.assertIsNone(record['text']['arabic'])
                self.assertIsNone(record['number']['canonical'])
                self.assertIsNone(record['number']['in_book'])
                self.assertEqual(record['references']['items'], [])
                self.assertIs(record['references']['counterpart_verified'], False)
                self.assertIs(record['grading']['independent_authenticity_assessed'], False)
                self.assertEqual(record['translation_provenance']['origin'], 'unknown')

if __name__ == '__main__':
    unittest.main()
