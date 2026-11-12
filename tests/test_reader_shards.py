"""Synthetic reader transport tests; no fixture is a religious quotation."""
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader
import validate_bank_views as validator
from test_reader import fixture


class ReaderShardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'catalog').mkdir()
        (self.root / 'search').mkdir()
        self.output = self.root / 'reader.html'
        self.records = [fixture(), fixture(2)]
        self.records[0]['text_translation'] = 'TEST العربية 🌿 漢字 ' * 800
        self.save()

    def save(self):
        raw = b''.join((json.dumps(record, ensure_ascii=False) + '\n').encode('utf-8') for record in self.records)
        (self.root / 'search/records.jsonl').write_bytes(raw)
        self.catalog = {'search': {'records_path': 'search/records.jsonl',
                                  'records_sha256': hashlib.sha256(raw).hexdigest(), 'count': len(self.records)},
                        'materials': [{'dataset_id': 'TEST', 'supporting_files': [{'path': 'TEST/audit.html'}]}]}
        (self.root / 'catalog/materials.json').write_text(json.dumps(self.catalog), encoding='utf-8')

    def build(self, **options):
        return reader.build(self.root, self.output, **options)

    def payload(self, identifier='hadith-records'):
        source = self.output.read_text(encoding='utf-8')
        match = re.search(r'<script\b[^>]*\bid="' + identifier + r'"[^>]*>(.*?)</script\s*>', source, re.S)
        self.assertIsNotNone(match)
        return match.group(1)

    def projected(self):
        return [(record['id'], validator.object_hash(record)) for record in self.records]

    def test_default_remains_self_contained_and_omits_audit_only_manifest_inventory(self):
        result = self.build()
        self.assertTrue(result['self_contained'])
        self.assertEqual(result['embedded_encoding'], 'gzip-base64')
        self.assertEqual(json.loads(gzip.decompress(base64.b64decode(self.payload()))), self.records)
        snapshot = json.loads(self.payload('hadith-snapshot'))
        self.assertNotIn('supporting_files', snapshot['materials'][0])
        self.assertIn('supporting_files', self.catalog['materials'][0])
        report = validator.verify_reader(self.root, 'reader.html', self.projected(), self.catalog['search'])
        self.assertEqual(report['embedded_objects_compared'], len(self.records))

    def test_bounded_shards_preserve_large_records_unicode_order_and_hashes(self):
        result = self.build(data_directory=self.root / 'data', max_shard_bytes=1024)
        self.assertFalse(result['self_contained'])
        manifest = json.loads(self.payload())
        self.assertEqual(manifest, json.loads((self.root / 'data/manifest.json').read_text()))
        self.assertGreater(len(manifest['shards']), 2)
        self.assertTrue(any(part['count'] == 0 for part in manifest['shards']))
        self.assertTrue(all(part['bytes'] <= 1024 and part['uncompressed_bytes'] <= 1024 for part in manifest['shards']))
        self.assertEqual(list(validator.reader_shard_records(self.output, manifest)), self.records)
        raw = b''.join(gzip.decompress((self.root / part['path']).read_bytes()) for part in manifest['shards'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['jsonl_sha256'])
        self.assertEqual(validator.verify_reader(self.root, 'reader.html', self.projected(),
                                                self.catalog['search'])['data_shards_verified'], len(manifest['shards']))
        self.build(data_directory=self.root / 'data', max_shard_bytes=1024)
        self.assertEqual(json.loads(self.payload()), manifest)

    def test_threshold_chooses_sibling_data_folder_and_empty_hosted_stream_is_valid(self):
        result = self.build(max_embedded_bytes=1)
        self.assertEqual(Path(result['data_directory']), self.root / 'reader-data')
        self.assertEqual(result['embedded_encoding'], 'gzip-jsonl-shards')
        self.records = []
        self.save()
        self.build(data_directory=self.root / 'empty')
        self.assertEqual(list(validator.reader_shard_records(self.output, json.loads(self.payload()))), [])
        self.assertEqual(validator.verify_reader(self.root, 'reader.html', [], self.catalog['search'])['embedded_objects_compared'], 0)

    def test_validator_rejects_tampering_bad_counts_and_unsafe_paths(self):
        self.build(data_directory=self.root / 'data', max_shard_bytes=1024)
        manifest = json.loads(self.payload())
        target = self.root / manifest['shards'][0]['path']
        original = target.read_bytes()
        target.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            list(validator.reader_shard_records(self.output, manifest))
        target.write_bytes(original)
        for change, message in [
            (lambda item: item['shards'][0].update(count=item['shards'][0]['count'] + 1), 'count'),
            (lambda item: item['shards'][0].update(path='../TEST.gz'), 'path'),
            (lambda item: item.update(jsonl_sha256='0' * 64), 'SHA-256'),
            (lambda item: item.update(record_count=item['record_count'] + 1), 'count'),
        ]:
            altered = copy.deepcopy(manifest)
            change(altered)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                list(validator.reader_shard_records(self.output, altered))

    def test_writer_rejects_escaping_or_symlinked_data_paths(self):
        with self.assertRaisesRegex(ValueError, 'inside'):
            self.build(data_directory=self.root.parent / 'TEST-outside')
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.build(data_directory=self.root / 'TEST%2Funsafe')
        (self.root / 'data').mkdir()
        (self.root / 'outside.json').write_text('{}')
        (self.root / 'data/manifest.json').symlink_to(self.root / 'outside.json')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.build(data_directory=self.root / 'data')

    def test_regeneration_prunes_only_unchanged_previous_generated_chunks(self):
        self.build(data_directory=self.root / 'data', max_shard_bytes=1024)
        previous = json.loads(self.payload())
        edited = self.root / previous['shards'][0]['path']
        edited.write_bytes(b'TEST manually edited')
        unrelated = self.root / 'data/TEST-unrelated.txt'
        unrelated.write_text('TEST preserve')
        self.records = [fixture(3)]
        self.save()
        self.build(data_directory=self.root / 'data', max_shard_bytes=1024)
        current = {item['path'] for item in json.loads(self.payload())['shards']}
        self.assertEqual(edited.read_bytes(), b'TEST manually edited')
        self.assertEqual(unrelated.read_text(), 'TEST preserve')
        for part in previous['shards'][1:]:
            if part['path'] not in current:
                self.assertFalse((self.root / part['path']).exists())

    @unittest.skipUnless(shutil.which('node'), 'Node is required for the native JavaScript gzip loader')
    def test_javascript_loader_checks_integrity_and_reassembles_cross_shard_unicode(self):
        self.build(data_directory=self.root / 'data', max_shard_bytes=1024)
        manifest = json.loads(self.payload())
        chunks = {item['path']: base64.b64encode((self.root / item['path']).read_bytes()).decode('ascii')
                  for item in manifest['shards']}
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        loader = 'async function loadReaderShards(' + template.split('async function loadReaderShards(', 1)[1].split('\nlet records,', 1)[0]
        program = '''
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
globalThis.crypto=require('crypto').webcrypto;
let tamper=false,calls=[],progress=[];
globalThis.fetch=async(url,options)=>{
 const path=new URL(url).pathname.slice(1),bytes=Buffer.from(input.chunks[path],'base64');
 calls.push({path,credentials:options.credentials,redirect:options.redirect});
 if(tamper)bytes[bytes.length-1]^=1;
 return new Response(bytes,{status:200});
};
''' + loader + '''
(async()=>{
 const records=await loadReaderShards(input.manifest,'https://example.invalid/index.html',value=>progress.push(value));
 async function failure(manifest,url){try{await loadReaderShards(manifest,url);return null;}catch(error){return error.message;}}
 tamper=true;const integrity=await failure(input.manifest,'https://example.invalid/index.html');tamper=false;
 const bad=structuredClone(input.manifest);bad.shards[0].count++;bad.record_count++;
 const count=await failure(bad,'https://example.invalid/index.html');
 const file=await failure(input.manifest,'file:///TEST/index.html');
 process.stdout.write(JSON.stringify({records,integrity,count,file,calls,progress}));
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
        run = subprocess.run([shutil.which('node'), '-e', program],
                             input=json.dumps({'manifest': manifest, 'chunks': chunks}),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        self.assertEqual(actual['records'], self.records)
        self.assertIn('integrity', actual['integrity'])
        self.assertIn('count', actual['count'])
        self.assertIn('web server', actual['file'])
        self.assertTrue(all(item['credentials'] == 'same-origin' and item['redirect'] == 'error'
                            for item in actual['calls']))
        self.assertEqual(actual['progress'][-1]['loaded'], len(self.records))


if __name__ == '__main__':
    unittest.main()
