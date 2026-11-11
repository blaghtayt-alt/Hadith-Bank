"""Verify the reader's pinned, fully embedded presentation assets."""
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader


class ReaderUIAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        source = Path(reader.__file__).resolve().parents[1] / 'reader/vendor'
        shutil.copytree(source, self.directory / 'vendor')
        (self.directory / 'reading-room.css').write_text(
            '/* TEST */\n.test { color: var(--jade-12); }\n', encoding='utf-8')

    def test_all_pinned_assets_and_notices_are_embedded_deterministically(self):
        styles, sprite = reader.reader_ui_assets(self.directory)
        self.assertEqual((styles, sprite), reader.reader_ui_assets(self.directory))
        for scale in ('jade', 'sand', 'gold'):
            self.assertIn('--' + scale + '-12:', styles)
        self.assertIn('.test { color: var(--jade-12); }', styles)
        for package in ('radix-colors', 'radix-icons'):
            notice = (self.directory / 'vendor' / package / 'LICENSE').read_text(encoding='utf-8')
            self.assertIn(notice.rstrip(), styles)
        svg = ET.fromstring(sprite)
        self.assertEqual(svg.get('aria-hidden'), 'true')
        symbols = svg.findall('{http://www.w3.org/2000/svg}symbol')
        self.assertEqual({item.get('id') for item in symbols},
                         {'icon-' + name for name in reader.UI_ICON_NAMES})
        self.assertEqual(len(symbols), len(reader.UI_ICON_NAMES))
        self.assertTrue(all(item.get('viewBox') == '0 0 15 15' for item in symbols))
        self.assertNotRegex(styles, r'@import\b|\burl\s*\(')
        self.assertNotRegex(sprite, r'\b(?:href|src)=')

    def test_modified_vendor_asset_is_rejected(self):
        target = self.directory / 'vendor/radix-icons/reader.svg'
        target.write_bytes(target.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            reader.reader_ui_assets(self.directory)

    def test_network_styles_are_rejected_before_embedding(self):
        target = self.directory / 'reading-room.css'
        target.write_text('@import "https://example.invalid/TEST.css";', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'self-contained'):
            reader.reader_ui_assets(self.directory)

    def test_markers_inside_source_text_are_not_replaced_again(self):
        markers = ('__HADITH_RECORDS_JSON__', '__HADITH_SNAPSHOT_JSON__',
                   '__HADITH_ENCODING__', '__HADITH_UI_STYLES__', '__HADITH_UI_ICONS__')
        replacements = {marker: 'TEST-' + str(index) for index, marker in enumerate(markers)}
        replacements[markers[0]] = 'TEST ' + ' '.join(markers)
        rendered = reader.render_template('|'.join(markers), replacements)
        self.assertEqual(rendered, '|'.join(replacements[marker] for marker in markers))
        for marker in markers:
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(ValueError, 'must contain one'):
                    reader.render_template('|'.join(markers) + marker, replacements)


if __name__ == '__main__':
    unittest.main()
