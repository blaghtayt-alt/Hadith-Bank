"""Real producer-to-browser transport parity; all source text is synthetic."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_reader


def synthetic_record(index):
    return {
        'id': 'TEST-occurrence-' + str(index), 'language': 'en', 'book_key': 'bukhari',
        'edition': 'TEST edition', 'source_id': 'TEST source',
        'source': {'name': 'TEST publisher'}, 'translator': {},
        'translation_provenance': {'ai_translation': False}, 'review': {},
        'topic_tags': [], 'editorial_tags': [], 'source_headings': [],
        'text_arabic': None,
        'text_translation': f'TEST {index} العربية ۱۲۳ ٤٥٦ 漢 字 ß İ sigmaΣ ' +
                            ('more text ' * 120 if index % 3 == 0 else ''),
        'title': None, 'number': {'in_book': index}, 'references': {},
        'unknown': {'extra': 'unchanged', 'values': [None, True, False, 1.2, 1e21]},
        'grading': {'score': 1e21, 'flags': [True, False]},
        'footnotes': [{'text': 'TEST annotation-only target'}],
        'language_versions': [{'language': 'ur', 'text': None,
                               'comments': [{'text': 'TEST pending-sibling'}]}],
    }


@unittest.skipUnless(shutil.which('node'), 'Node is required for browser transport parity')
class LazyReaderParityTests(unittest.TestCase):
    def test_actual_producer_runtime_preserves_search_filter_and_complete_record_semantics(self):
        with tempfile.TemporaryDirectory(prefix='reader-parity-') as name:
            root = Path(name)
            records = [synthetic_record(index) for index in range(50)]
            manifest = build_reader.write_lazy_reader_shards(records, root / 'index.html',
                                                             root / 'data', 16384)
            (root / 'input.json').write_text(json.dumps({
                'repository_root': str(ROOT), 'manifest': manifest, 'records': records,
            }, ensure_ascii=False), encoding='utf-8')
            program = r'''
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=process.argv[1],input=JSON.parse(fs.readFileSync(path.join(root,'input.json')));
const lazy=require(path.join(input.repository_root,'reader/lazy-store.js'));
const projector=require(path.join(input.repository_root,'scripts/reader_projection.js'))
 .createProjector(fs.readFileSync(path.join(input.repository_root,'reader/template.html'),'utf8'));
globalThis.crypto=require('crypto').webcrypto;
const calls=[];
const store=lazy.create(input.manifest,'https://fixture.invalid/index.html',()=>{},{
 fetch:async url=>{
  const relative=new URL(url).pathname.slice(1);calls.push(relative);
  return new Response(fs.readFileSync(path.join(root,relative)));
 },cacheBytes:32768
});
(async()=>{
 const directory=await store.loadDirectory();
 assert.equal(directory.length,input.records.length);
 const startupCalls=calls.length;
 assert(calls.every(relative=>relative.startsWith('data/directory/')));
 const projected=input.records.map(record=>projector(record,[0,10]));
 for(let i=0;i<directory.length;i++){
  for(const key of ['id','language','book_key','edition','source_id'])
   assert.equal(directory[i][key],input.records[i][key]);
  for(const key of ['languages','origin','availability','ocr_pending','citation_pairs'])
   assert.deepStrictEqual(directory[i]._reader[key],projected[i][0]._reader[key]);
 }
 // The normalization baseline is the browser's original pure functions. The
 // transport must not silently substitute Python case folding/scalar conversion.
 assert(projected[0][1].includes('123 456'));
 assert(projected[0][1].includes('漢字'));
 assert(projected[0][1].includes('1e+21'));
 assert(!projected[0][1].includes('true'));
 assert(!projected[0][1].includes('pending-sibling'));
 assert(projected[0][2].includes('pending-sibling'));
 const chosen=[0,1,16,20,49];
 const hydrated=await store.getRecords(chosen,{concurrency:4});
 for(let i=0;i<chosen.length;i++) assert.deepStrictEqual(hydrated[i],input.records[chosen[i]]);
 // Exported objects keep unknown/null fields and source context exactly.
 assert.deepStrictEqual(JSON.parse(JSON.stringify(hydrated)),chosen.map(i=>input.records[i]));
 const queries=[[],['test'],['123','456'],['σ'],['i̇'],['ß'],['target'],
                ['test','target'],['pending-sibling'],['1e+21'],['true']];
 let searches=0;
 for(const query of queries)for(const include of [false,true]){
  const candidates=[49,15,1,33,20,0];
  const expected=candidates.filter(i=>query.every(term=>
   (projected[i][1]+(include?'\n'+projected[i][2]:'')).includes(term)));
  const actual=await store.search(candidates,query,include);
  assert.deepStrictEqual(actual,expected);searches++;
 }
 const cache=store.cacheStats();
 assert(cache.bytes<=32768);assert.equal(cache.activeRequests,0);
 assert.equal(cache.queuedRequests,0);assert.equal(cache.inFlight,0);
 console.log(JSON.stringify({records:directory.length,searches,startupCalls,cache}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
'''
            run = subprocess.run([shutil.which('node'), '-e', program, str(root)],
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result['records'], 50)
            self.assertEqual(result['searches'], 22)
            self.assertEqual(result['startupCalls'], len(manifest['directory']['shards']))
            self.assertLessEqual(result['cache']['maxActiveRequests'], 4)


if __name__ == '__main__':
    unittest.main()
