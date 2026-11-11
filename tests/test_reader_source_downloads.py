"""TEST-only source files and counterpart links for reader regressions."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader
from counterpart_display import counterpart_qualification, counterpart_translation_origin
from citation_search import record_citation_pairs
from test_reader import fixture


class ReaderSourceDownloadsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.relative = 'materials/TEST/中文 TEST #.doc'
        path = self.root / self.relative
        path.parent.mkdir(parents=True)
        path.write_bytes(b'TEST source document, no religious content')
        self.record = fixture()
        self.record['source'].update(original_file=self.relative,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.site = {'repository_url': 'https://github.com/TEST/TEST', 'source_ref': 'TEST/branch'}
        self.template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()

    def node(self, body, sample):
        helpers = self.template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = "const input=JSON.parse(require('fs').readFileSync(0,'utf8'));const records=[],names={};\nconst valueText = " + helpers + body
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(sample),
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_only_existing_preserved_word_and_pdf_files_are_downloadable(self):
        before = copy.deepcopy(self.record)
        catalog = {'materials': [{'source_file': self.relative, 'source_sha256': self.record['source']['sha256'],
            'language': 'ja', 'book_key': 'TEST', 'source_name': 'TEST book', 'available_locally': True},
            {'source_file': 'TEST-missing.pdf', 'available_locally': True},
            {'source_file': 'TEST-private.docx', 'available_locally': False}],
            'legacy_materials': [{'path': 'TEST.txt', 'available_locally': True}]}
        (self.root / 'TEST-private.docx').write_bytes(b'TEST private')
        (self.root / 'TEST.txt').write_bytes(b'TEST text')
        downloads = reader.source_downloads(self.root, [self.record], catalog)
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]['path'], self.relative)
        self.assertEqual(downloads[0]['label'], 'Download Word (.doc)')
        self.assertEqual(downloads[0]['sha256'], self.record['source']['sha256'])
        self.assertEqual(self.record, before)
        markdown = reader.markdown_record(self.record, 1, self.root, self.root,
                                         {item['path']: item for item in downloads}, self.site)
        self.assertIn('Download Word (.doc)', markdown)
        self.assertIn('/raw/TEST%2Fbranch/materials/TEST/', markdown)
        self.assertIn('Original file:', markdown)
        self.assertIn('Canonical record:', markdown)
        self.assertNotIn('Download PDF', markdown)

    def test_declared_source_hash_mismatch_and_symlinks_stop_the_build(self):
        self.record['source']['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            reader.source_downloads(self.root, [self.record], {})
        path = self.root / self.relative
        destination = path.with_suffix('.bin')
        path.rename(destination)
        path.symlink_to(destination)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            reader.source_downloads(self.root, [self.record], {})

    @unittest.skipUnless(shutil.which('node'), 'Node is required for URL parity')
    def test_download_urls_encode_unicode_and_refs_and_reject_unsafe_paths(self):
        paths = [self.relative, 'TEST FILE.DOCX', 'TEST #.PDF', '%2e%2e/TEST.pdf']
        invalid = ['../TEST.pdf', '/TEST.pdf', 'TEST\\TEST.pdf', 'TEST//TEST.pdf', 'TEST/./TEST.pdf',
                   'TEST\nTEST.pdf', 'https://example.invalid/TEST.pdf', 'TEST.json', 'TEST.doc.exe']
        actual = self.node('''
process.stdout.write(JSON.stringify({urls:input.paths.map(path=>sourceDownloadURL(path,input.site)),
 labels:input.paths.map(sourceDownloadLabel),invalid:input.invalid.map(path=>sourceDownloadURL(path,input.site)),
 refs:input.refs.map(source_ref=>sourceDownloadURL("TEST.pdf",{...input.site,source_ref}))}));''',
            {'site': self.site, 'paths': paths, 'invalid': invalid, 'refs': ['../main', 'TEST/../main', '/main', 'TEST//main', 'TEST?x', '']})
        self.assertEqual(actual['urls'], [reader.source_download_url(path, self.site) for path in paths])
        self.assertEqual(actual['labels'], ['Download Word (.doc)', 'Download Word (.docx)', 'Download PDF', 'Download PDF'])
        self.assertEqual(actual['invalid'], [None] * len(invalid))
        self.assertEqual(actual['refs'], [None] * 6)
        self.assertIn('/raw/TEST%2Fbranch/', actual['urls'][0])
        self.assertIn('%E4%B8%AD%E6%96%87%20TEST%20%23.doc', actual['urls'][0])
        self.assertTrue(actual['urls'][3].endswith('/%252e%252e/TEST.pdf'))
        for relative in invalid:
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                reader.source_download_url(relative, self.site)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for reader rendering')
    def test_downloads_render_in_source_details_and_materials_with_provenance_links(self):
        downloads = reader.source_downloads(self.root, [self.record], {})
        source_function = 'function sourceFiles(' + self.template.split('function sourceFiles(', 1)[1].split('function citationList(', 1)[0]
        books_function = 'function bookDownloads(' + self.template.split('function bookDownloads(', 1)[1].split('function renderAvailableMaterials(', 1)[0]
        actual = self.node(self.dom() + '''
const site=input.site,offline=false,window={location:{protocol:"https:"}},nf=new Intl.NumberFormat("en");
const sourceDownloads=input.downloads,sourceDownloadsByPath=new Map(sourceDownloads.map(item=>[item.path,item]));
''' + source_function + books_function + '''
process.stdout.write(JSON.stringify({source:sourceFiles(input.source),materials:bookDownloads({language:"ja"})}));''',
            {'site': self.site, 'downloads': downloads, 'source': self.record['source']})
        for key in ('source', 'materials'):
            links = [node for node in self.walk(actual[key]) if node.get('tag') == 'a']
            self.assertTrue(any(node.get('textContent') == 'Download Word (.doc)' and '/raw/' in node.get('href', '') for node in links))
        source_links = [node for node in self.walk(actual['source']) if node.get('tag') == 'a']
        self.assertTrue(any(node.get('textContent') == 'Source file' and '/blob/' in node.get('href', '') for node in source_links))
        self.assertTrue(any(node.get('textContent') == 'Canonical record file' for node in source_links))

    @staticmethod
    def dom():
        return '''
class TestNode {constructor(tag){this.tag=tag;this.childNodes=[];}append(...children){this.childNodes.push(...children);}setAttribute(name,value){this[name]=value;}}
const document={createElement:tag=>new TestNode(tag),createTextNode:text=>({textContent:text})};
'''

    def walk(self, node):
        yield node
        for child in node.get('childNodes', []):
            if isinstance(child, dict):
                yield from self.walk(child)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for counterpart controls')
    def test_external_english_remains_accessible_with_both_toggle_states(self):
        source = {'text': None, 'text_sha256': None, 'scope': 'external_source',
            'source_url': 'https://example.invalid/TEST/987654', 'source_name': 'TEST external source',
            'translation_origin': 'unknown', 'match_status': 'reviewed_parallel',
            'citation_note': 'TEST reference number comes from the reviewed Arabic source.',
            'references': [{'book_key': 'abu-dawud', 'collection': 'TEST Sunan Abi Dawud',
                            'number': '987654', 'numbering_scheme': 'TEST', 'scope': 'main_quote'}]}
        self.record['counterparts'] = {'status': 'reviewed_parallel', 'english': source, 'arabic': None,
            'quotation_evidence': {'relation': 'source_excerpt', 'review': {'status': 'verified', 'human_review': False,
                'qualifications': ['TEST source and target differ in narrator attribution.']}}}
        presentation = 'function detail(' + self.template.split('function detail(', 1)[1].split('function suppliedText(', 1)[0]
        disclosure = 'function languageDisclosure(' + self.template.split('function languageDisclosure(', 1)[1].split('function appendLanguageReadings(', 1)[0]
        actual = self.node(self.dom() + '''
let checked=false;const $=()=>({checked});
''' + presentation + disclosure + '''
const closed=languageDisclosure(input.record,"english");checked=true;const opened=languageDisclosure(input.record,"english");
process.stdout.write(JSON.stringify({closed,opened,key:primarySearchKey(input.record),pairs:[...recordCitationPairs(input.record)],
 note:counterpartQualification(input.record.counterparts.english,input.record),hasText:!!counterpartData(input.record,"english")}));''',
            {'record': self.record})
        self.assertFalse(actual['closed']['open'])
        self.assertTrue(actual['opened']['open'])
        self.assertFalse(actual['hasText'])
        self.assertIn('abu-dawud:987654', actual['pairs'])
        self.assertEqual(record_citation_pairs(self.record), {('abu-dawud', '987654')})
        self.assertEqual(actual['note'], counterpart_qualification(source, self.record))
        self.assertIn(source['citation_note'], actual['note'])
        for state in ('closed', 'opened'):
            links = [node for node in self.walk(actual[state]) if node.get('tag') == 'a']
            self.assertEqual(links[0]['href'], source['source_url'])
            self.assertTrue(links[0]['textContent'].startswith('Read English at source'))
            text = json.dumps(actual[state])
            self.assertIn('Alignment notes', text)
            self.assertIn('checked by an automated assistant', text)
            self.assertIn('TEST source and target differ in narrator attribution.', text)
        markdown = reader.markdown_record(self.record, 1)
        self.assertIn('English · read at source', markdown)
        self.assertIn('Translation origin: Unknown', markdown)
        self.assertIn('<summary>Alignment notes</summary>', markdown)
        self.assertIn('checked by an automated assistant', markdown)
        self.assertIn('TEST source and target differ in narrator attribution.', markdown)
        self.assertIn(source['citation_note'], markdown)
        self.assertNotIn('English · not linked yet', markdown)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for counterpart controls')
    def test_english_uses_own_current_origin_and_arabic_has_no_translation_label(self):
        english = {'text': None, 'scope': 'external_source',
            'source_url': 'https://example.invalid/TEST/en/123',
            'source_name': 'TEST English source', 'translation_origin': 'unknown',
            'current_translation_policy': {'classification': 'human', 'basis': 'TEST source policy'},
            'references': []}
        arabic = {'text': 'TEST نص عربي', 'scope': 'source_entry',
            'source_url': 'https://example.invalid/TEST/ar/123',
            'source_name': 'TEST Arabic source', 'translation_origin': 'unknown', 'references': []}
        self.record['counterparts'] = {'english': english, 'arabic': arabic}
        before = copy.deepcopy(self.record)
        presentation = 'function detail(' + self.template.split('function detail(', 1)[1].split('function suppliedText(', 1)[0]
        disclosure = 'function inlineArabicReading(' + self.template.split('function inlineArabicReading(', 1)[1].split('function appendLanguageReadings(', 1)[0]
        actual = self.node(self.dom() + 'const $=()=>({checked:true});\n' + presentation + disclosure + '''
process.stdout.write(JSON.stringify({english:languageDisclosure(input.record,"english"),
 arabic:languageDisclosure(input.record,"arabic"),origin:counterpartTranslationOrigin(input.record.counterparts.english)}));''',
            {'record': self.record})
        self.assertEqual(actual['origin'], counterpart_translation_origin(english))
        self.assertIn('Translation origin: Human', json.dumps(actual['english']))
        self.assertNotIn('Translation origin: Unknown', json.dumps(actual['english']))
        self.assertNotIn('Translation origin:', json.dumps(actual['arabic']))
        markdown = reader.markdown_record(self.record, 1)
        english_section = markdown.split('<summary>English · read at source</summary>', 1)[1].split('</details>', 1)[0]
        arabic_section = markdown.split('<summary>Arabic source entry</summary>', 1)[1].split('</details>', 1)[0]
        self.assertIn('Translation origin: Human', english_section)
        self.assertNotIn('Translation origin:', arabic_section)
        self.assertEqual(self.record, before)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for source-entry rendering')
    def test_arabic_source_entry_label_distinguishes_compiler_notes_from_narration(self):
        source = {'text': 'TEST نص تجريبي فقط', 'scope': 'source_entry',
            'source_url': 'https://example.invalid/TEST/ar/987654', 'source_name': 'TEST source entry',
            'match_status': 'reviewed_parallel', 'citation': '[TEST source no. 987654]'}
        self.record.update(language='zh-CN', counterparts={'status': 'reviewed_parallel', 'arabic': source,
            'quotation_evidence': {'relation': 'source_excerpt', 'review': {'human_review': False}}})
        presentation = 'function detail(' + self.template.split('function detail(', 1)[1].split('function suppliedText(', 1)[0]
        disclosure = 'function inlineArabicReading(' + self.template.split('function inlineArabicReading(', 1)[1].split('function appendLanguageReadings(', 1)[0]
        actual = self.node(self.dom() + 'const $=()=>({checked:true});\n' + presentation + disclosure + '''
process.stdout.write(JSON.stringify({view:languageDisclosure(input.record,"arabic"),
 note:counterpartQualification(input.record.counterparts.arabic,input.record)}));''', {'record': self.record})
        self.assertEqual(actual['note'], counterpart_qualification(source, self.record))
        self.assertIn("May include the compiler's notes; the Chinese source can be an excerpt.", actual['note'])
        serialized = json.dumps(actual['view'], ensure_ascii=False)
        self.assertIn('Arabic source entry', serialized)
        self.assertIn(source['text'], serialized)
        self.assertNotIn('full narration', serialized.lower())
        markdown = reader.markdown_record(self.record, 1)
        self.assertIn('<summary>Arabic source entry</summary>', markdown)
        self.assertIn('Chinese source can be an excerpt.', markdown)
        self.assertNotIn('full narration', markdown.lower())

    @unittest.skipUnless(shutil.which('node'), 'Node is required for source-excerpt rendering')
    def test_english_excerpt_heading_and_qualification_do_not_claim_completeness(self):
        source = {'text': 'TEST partial English source text.', 'scope': 'source_excerpt',
            'source_url': 'https://example.invalid/TEST/en/987654', 'source_name': 'TEST publisher',
            'translation_origin': 'human', 'match_status': 'reviewed_parallel', 'citation': '[TEST no. 987654]'}
        self.record['counterparts'] = {'status': 'reviewed_parallel', 'english': source}
        presentation = 'function detail(' + self.template.split('function detail(', 1)[1].split('function suppliedText(', 1)[0]
        disclosure = 'function languageDisclosure(' + self.template.split('function languageDisclosure(', 1)[1].split('function appendLanguageReadings(', 1)[0]
        actual = self.node(self.dom() + 'const $=()=>({checked:true});\n' + presentation + disclosure + '''
process.stdout.write(JSON.stringify({view:languageDisclosure(input.record,"english"),
 note:counterpartQualification(input.record.counterparts.english,input.record)}));''', {'record': self.record})
        self.assertEqual(actual['note'], counterpart_qualification(source, self.record))
        self.assertIn('does not supply the complete source entry', actual['note'])
        serialized = json.dumps(actual['view'])
        self.assertIn('English source excerpt', serialized)
        self.assertIn(source['text'], serialized)
        self.assertNotIn('full narration', serialized.lower())
        markdown = reader.markdown_record(self.record, 1)
        self.assertIn('<summary>English source excerpt</summary>', markdown)
        self.assertIn('does not supply the complete source entry', markdown)
        self.assertNotIn('full narration', markdown.lower())


if __name__ == '__main__':
    unittest.main()
