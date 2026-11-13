"""Direct preserved-source download regressions; all fixtures are synthetic."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from test_reader import READER_SNAPSHOT_JS


NODE = os.environ.get('CODEX_PRIMARY_RUNTIME_NODE') or shutil.which('node')
TEMPLATE = Path(__file__).resolve().parents[1] / 'reader/template.html'


@unittest.skipUnless(NODE, 'Node is required for source-download checks')
class SourceDownloadTests(unittest.TestCase):
    def evaluate(self, samples):
        template = TEMPLATE.read_text(encoding='utf-8')
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        link = template.split('function sourceDownloadLink(source) {', 1)[1].split('function citationList(', 1)[0]
        program = READER_SNAPSHOT_JS + '''const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const records=[],names={},document={createElement:tag=>({tag})};
const valueText = ''' + helpers + '''
function sourceDownloadLink(source) {''' + link + '''
const result=input.map(sample=>{
  globalThis.site=sample.site;
  return {info:sourceDownloadInfo(sample.source,sample.site),link:sourceDownloadLink(sample.source),
          local:recordFileURL(sample.source?.original_file,sample.site,'file:'),
          view:recordFileURL(sample.source?.original_file,sample.site,'https:')};
});
process.stdout.write(JSON.stringify(result));'''
        result = subprocess.run([NODE, '-e', program], input=json.dumps(samples),
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_word_and_pdf_downloads_keep_title_filename_and_local_source(self):
        # Repository name "blob" guards against replacing the wrong URL segment.
        site = {'repository_url': 'https://github.com/TEST/blob/', 'source_ref': 'a' * 40}
        title = '中文测试书名 — TEST Chinese source <script>TEST</script>'
        paths = ['materials/TEST/中文_TEST #.docx', 'materials/TEST/TEST.DOC',
                 'materials/TEST/TEST.pdf']
        result = self.evaluate([{'source': {'original_file': path, 'name': title}, 'site': site}
                                for path in paths])
        raw_base = 'https://github.com/TEST/blob/raw/' + 'a' * 40 + '/'
        expected_paths = ['materials/TEST/%E4%B8%AD%E6%96%87_TEST%20%23.docx',
                          'materials/TEST/TEST.DOC', 'materials/TEST/TEST.pdf']
        for item, path, encoded in zip(result, paths, expected_paths):
            self.assertEqual(item['info']['href'], raw_base + encoded + '?download=1')
            self.assertEqual(item['link']['href'], item['info']['href'])
            self.assertEqual(item['link']['download'], path.rsplit('/', 1)[1])
            self.assertTrue(item['link']['title'].startswith(title + ' — '))
            self.assertEqual(item['link']['textContent'], item['info']['label'])
            self.assertNotIn('innerHTML', item['link'])
            self.assertEqual(item['local'], encoded)
            self.assertIn('/blob/' + 'a' * 40 + '/', item['view'])
            self.assertEqual(item['link']['rel'], 'noopener noreferrer')
        self.assertEqual([item['info']['label'] for item in result],
                         ['Download original Word (DOCX)', 'Download original Word (DOC)',
                          'Download original PDF'])

    def test_unsafe_paths_sites_and_unsupported_files_have_no_download(self):
        site = {'repository_url': 'https://github.com/TEST/TEST', 'source_ref': 'main'}
        bad_paths = ['../TEST.docx', '/TEST.pdf', 'TEST\\TEST.doc', 'TEST//TEST.pdf',
                     'TEST/./TEST.pdf', 'https://example.invalid/TEST.pdf', 'TEST\nTEST.docx',
                     'records.jsonl', 'TEST.html', 'TEST.pdf?redirect=1', None]
        samples = [{'source': {'original_file': path, 'format': 'pdf'}, 'site': site}
                   for path in bad_paths]
        samples += [{'source': {'original_file': 'TEST.pdf'}, 'site': unsafe} for unsafe in [
            None, {}, {'repository_url': 'https://github.com/TEST/TEST?redirect=1', 'source_ref': 'main'},
            {'repository_url': 'https://example.invalid/TEST/TEST', 'source_ref': 'main'},
            {'repository_url': site['repository_url'], 'source_ref': 'TEST/../main'},
        ]]
        for item in self.evaluate(samples):
            self.assertIsNone(item['info'])
            self.assertIsNone(item['link'])

    def test_encoded_components_stay_literal_and_download_is_visible(self):
        site = {'repository_url': 'https://github.com/TEST/TEST', 'source_ref': 'feature/TEST'}
        result = self.evaluate([{'source': {'original_file': 'materials/%2e%2e/TEST.pdf'},
                                 'site': site}])[0]
        self.assertEqual(result['info']['href'],
                         'https://github.com/TEST/TEST/raw/feature%2FTEST/materials/%252e%252e/TEST.pdf?download=1')
        template = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn('const originalDownload=sourceDownloadLink(record.source);', template)
        self.assertLess(template.index('const originalDownload=sourceDownloadLink(record.source);'),
                        template.index('const sourceDetails=element("details","source-details");'))


if __name__ == '__main__':
    unittest.main()
