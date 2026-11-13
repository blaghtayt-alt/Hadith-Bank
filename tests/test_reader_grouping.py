"""Approved presentation grouping; every quotation here is synthetic TEST text."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from counterpart_review import source_binding
from reader_grouping import SCHEMA, load_reader_groups, validate_group_documents
from test_reader import fixture, READER_SNAPSHOT_JS, READER_FILTER_HARNESS_JS


def records_fixture():
    result = []
    for index, (language, source, origin) in enumerate([
            ('en', 'TEST-existing', 'human'), ('ja', 'TEST-new', 'ai'),
            ('ja', 'TEST-new', 'human'), ('ja', 'TEST-unrelated', 'unknown')]):
        row = fixture(index)
        row.update(id='TEST-occurrence-' + str(index), language=language,
                   source_id=source, book_key='TEST-new-book' if source == 'TEST-new' else 'TEST-old-book',
                   canonical_record_sha256=hashlib.sha256(('TEST canonical ' + str(index)).encode()).hexdigest())
        row['text_translation'] = ['TEST anchor wording preserved exactly.',
            '検証用のAI改訳。<script>TEST literal</script>\nTEST-new-word',
            '検証用の刊行済み訳文。TEST-published-word',
            'TEST unrelated similar citation remains separate.'][index]
        row['text_arabic'] = None
        row['source'].update(name='TEST source ' + str(index), original_file='materials/' + source + '/source.pdf',
                             record_url='https://example.invalid/source/' + str(index),
                             record_locator={'path': 'materials/' + source + '/records.json', 'json_pointer': '/' + str(index)})
        row['translation_provenance']['current_policy'] = {'classification': origin, 'basis': 'TEST explicit evidence'}
        row['translation_provenance']['ai_translation'] = origin == 'ai' if origin != 'unknown' else 'unknown'
        row['footnotes'] = [{'text': 'TEST footnote ' + str(index)}]
        row['references'] = {'items': [{'collection': 'muslim', 'number': '1', 'scope': 'main_quote',
                                       'source_citation': 'TEST source citation ' + str(index)}]}
        row['page'] = {'pdf': [index + 10], 'printed': [index + 8]}
        row['commentary']['translation'] = 'TEST annotation-only-' + str(index)
        result.append(row)
    return result


def link(source, target):
    return {'source': source_binding(source), 'target': source_binding(target),
            'relation': 'same_narration', 'review': {
                'reviewer': 'TEST reviewer', 'method': 'TEST exact source comparison',
                'human_review': False, 'evidence': 'TEST comparison of source text and narrator evidence.',
                'qualifications': ['TEST review does not establish complete chain equality.']}}


def document(records):
    return {'schema': SCHEMA, 'new_source_ids': ['TEST-new'],
            'links': [link(records[1], records[0]), link(records[2], records[0])]}


def mapping(records):
    return validate_group_documents([(document(records), {'TEST-new'}, 'TEST.json')], records)


class ReaderGroupingContractTests(unittest.TestCase):
    def setUp(self):
        self.records = records_fixture()
        self.before = copy.deepcopy(self.records)

    def check(self, value, records=None):
        return validate_group_documents([(value, {'TEST-new'}, 'TEST.json')],
                                        self.records if records is None else records)

    def test_one_anchor_retains_source_occurrences_and_accepts_one_pass_generator(self):
        consumed = []
        def stream():
            for record in self.records:
                consumed.append(record['id'])
                yield record
        result = self.check(document(self.records), stream())
        self.assertEqual(result['source_occurrence_count'], 4)
        self.assertEqual(result['grouped_reading_count'], 2)
        group = result['groups'][0]
        self.assertEqual(group['id'], self.records[0]['id'])
        self.assertEqual(group['anchor_id'], self.records[0]['id'])
        self.assertEqual(group['member_ids'], [row['id'] for row in self.records[:3]])
        self.assertEqual(group['comparisons'][0]['review'], document(self.records)['links'][0]['review'])
        self.assertEqual(consumed, [row['id'] for row in self.records])
        self.assertEqual(self.records, self.before)

    def test_relations_and_qualifications_are_preserved_without_promoting_scope(self):
        for relation in ('same_narration', 'same_narration_core', 'source_excerpt'):
            value = document(self.records)
            value['links'][0]['relation'] = relation
            comparison = self.check(value)['groups'][0]['comparisons'][0]
            self.assertEqual(comparison['relation'], relation)
            self.assertEqual(comparison['review'], value['links'][0]['review'])
            self.assertIs(comparison['review']['human_review'], False)
        value['links'][0]['relation'] = 'exact_source_copy'
        with self.assertRaisesRegex(ValueError, 'identical chosen quotation bytes'):
            self.check(value)
        rows = copy.deepcopy(self.records)
        rows[1]['text_translation'] = rows[0]['text_translation']
        value['links'][0] = link(rows[1], rows[0])
        value['links'][0]['relation'] = 'exact_source_copy'
        self.assertEqual(self.check(value, rows)['groups'][0]['comparisons'][0]['relation'], 'exact_source_copy')

    def test_every_source_and_target_binding_is_exact(self):
        original = document(self.records)
        for position in (0, 1):
            for mutation in ('text', 'canonical', 'source_hash', 'page'):
                with self.subTest(position=position, mutation=mutation):
                    rows = copy.deepcopy(self.records)
                    if mutation == 'text': rows[position]['text_translation'] += ' EDITED'
                    if mutation == 'canonical': rows[position]['canonical_record_sha256'] = 'f' * 64
                    if mutation == 'source_hash': rows[position]['source']['sha256'] = 'e' * 64
                    if mutation == 'page': rows[position]['page']['pdf'].append(999)
                    with self.assertRaisesRegex(ValueError, 'Stale review source binding'):
                        self.check(original, rows)

    def test_missing_duplicate_self_and_new_source_targets_are_rejected(self):
        valid = document(self.records)
        values = []
        value = copy.deepcopy(valid); value['links'][0]['target']['record_id'] = 'TEST-missing'; values.append(value)
        value = copy.deepcopy(valid); value['links'].append(copy.deepcopy(value['links'][0])); values.append(value)
        value = copy.deepcopy(valid); value['links'][0] = link(self.records[1], self.records[1]); values.append(value)
        value = copy.deepcopy(valid); value['links'][0] = link(self.records[1], self.records[2]); values.append(value)
        value = copy.deepcopy(valid); value['links'] = [link(self.records[1], self.records[2]), link(self.records[2], self.records[1])]; values.append(value)
        value = copy.deepcopy(valid); value['links'][0]['relation'] = 'same_reference_number'; values.append(value)
        value = copy.deepcopy(valid); value['links'][0]['review'].pop('evidence'); values.append(value)
        value = copy.deepcopy(valid); value['new_source_ids'] = ['TEST-unapproved']; values.append(value)
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(value)
        with self.assertRaisesRegex(ValueError, 'distinct stable'):
            self.check(valid, [*self.records, self.records[0]])

    def test_only_checksum_pinned_accepted_supporting_files_authorize_links(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            relative = 'sources/reader-groups/TEST.json'
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_text('THIS UNREGISTERED FILE IS NOT READ')
            empty = load_reader_groups(root, iter(self.records), catalog={'materials': []})
            self.assertEqual(empty['groups'], [])
            self.assertEqual(empty['grouped_reading_count'], 4)
            raw = json.dumps(document(self.records)).encode()
            path.write_bytes(raw)
            descriptor = {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest()}
            catalog = {'materials': [{'dataset_id': 'TEST-new', 'publication': {'authorized': True},
                                      'supporting_files': [descriptor]}]}
            self.assertEqual(load_reader_groups(root, iter(self.records), catalog=catalog), mapping(self.records))
            path.write_bytes(raw + b' ')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                load_reader_groups(root, iter(self.records), catalog=catalog)
            path.write_bytes(raw)
            catalog['materials'][0]['publication']['authorized'] = False
            with self.assertRaisesRegex(ValueError, 'not an accepted material'):
                load_reader_groups(root, self.records, catalog=catalog)
            catalog['materials'][0]['publication']['authorized'] = True
            catalog['materials'][0]['dataset_id'] = 'TEST-other-source'
            with self.assertRaisesRegex(ValueError, 'lacks supporting-file authorization'):
                load_reader_groups(root, self.records, catalog=catalog)


@unittest.skipUnless(shutil.which('node'), 'Node is required for reader grouping regression')
class ReaderGroupingUITests(unittest.TestCase):
    def setUp(self):
        self.records = records_fixture()
        self.template = (ROOT / 'reader/template.html').read_text()
        self.helpers = 'const valueText =' + self.template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]

    def run_js(self, program):
        result = subprocess.run([shutil.which('node'), '-e', program],
                                input=json.dumps({'records': self.records, 'mapping': mapping(self.records)}),
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_filter_search_and_exact_links_group_only_approved_occurrences(self):
        filters = 'async function applyFilters(){' + self.template.split('function applyFilters(){', 1)[1].split('$("query").addEventListener', 1)[0]
        program = READER_SNAPSHOT_JS + '''
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),records=input.records,names={};
const state={matches:[],exactOccurrence:null},fields={query:{value:''},'language-filter':{value:''},'book-filter':{value:''},'source-filter':{value:''},'origin-filter':{value:''},'include-commentary':{checked:false}};
const $=id=>fields[id],render=()=>{};
''' + self.helpers + READER_FILTER_HARNESS_JS + '''
const readerGroups=createReaderGroupIndex(records,input.mapping);
''' + filters + '''
(async()=>{
 const cases=[{}, {source:'TEST-new'}, {language:'ja'}, {origin:'ai'}, {origin:'human'},
  {language:'ja',origin:'human'}, {source:'TEST-existing'}, {book:'TEST-new-book'},
  {occurrence:'TEST-occurrence-2'}, {query:'TEST-occurrence-1'}, {query:'TEST-new-word'},
  {query:'annotation-only-2'}, {query:'annotation-only-2',comments:true}];
 const results=[];
 for(const item of cases){
  state.exactOccurrence=item.occurrence || null;fields.query.value=item.query || '';
  for(const key of ['language','book','source','origin'])fields[key+'-filter'].value=item[key] || '';
  fields['include-commentary'].checked=!!item.comments;await applyFilters();
  results.push({cards:state.matches.map(index=>records[index].id),occurrences:state.matchingOccurrences.length});
 }
 process.stdout.write(JSON.stringify({results,records,page:readerGroupPageOrdinals([1],readerGroups)}));
})().catch(error=>{process.stderr.write(error.stack);process.exitCode=1;});
'''
        actual = self.run_js(program)
        expected = [[0, 3], [1], [1, 3], [1], [0], [2], [0], [1], [2], [1], [1], [], [2]]
        self.assertEqual([row['cards'] for row in actual['results']],
                         [['TEST-occurrence-' + str(index) for index in row] for row in expected])
        self.assertEqual(actual['results'][0]['occurrences'], 4)
        self.assertEqual(actual['page'], [1, 0, 2])
        self.assertEqual(actual['records'], self.records)

    def test_grouped_dom_has_one_card_full_source_versions_and_lossless_selection(self):
        # Real card/render constructors with a small DOM harness, not a browser-layout claim.
        for index in (1, 2):
            self.records[index]['source_scoped_content'] = {
                'segments': [{'source_segment_id': 'TEST-scope-' + str(index), 'story': 'main',
                              'cp_start': 0, 'cp_end': 1, 'text_verbatim': 'TEST scoped passage ' + str(index),
                              'role_candidates': ['TEST source role'], 'leaf_semantic_references': [],
                              'source_ambiguity_ids': []}],
                'footnotes': [], 'uncertainties': {}}
        constructors = 'function meta(' + self.template.split('function meta(', 1)[1].split('function updateSelection(', 1)[0]
        renderer = 'async function render(' + self.template.split('async function render(', 1)[1].split('async function applyFilters(', 1)[0]
        program = '''
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),records=input.records,names={},snapshot={book_titles:{}};
class TestNode {
 constructor(tag){this.tag=tag;this.childNodes=[];this.dataset={};this.events={};this.open=false;}
 append(...nodes){this.childNodes.push(...nodes);}setAttribute(key,value){this[key]=value;}
 addEventListener(key,handler){this.events[key]=handler;}replaceChildren(...nodes){this.childNodes=nodes;}
 querySelector(){return null;}
}
const Node=TestNode,document={createElement:tag=>new TestNode(tag),createTextNode:text=>Object.assign(new TestNode('#text'),{textContent:text}),createDocumentFragment:()=>new TestNode('fragment')};
const fields={'language-filter':{value:'ja'},'origin-filter':{value:''},'show-arabic':{checked:false},'show-english':{checked:false},results:new TestNode('div'),'result-count':{},'page-meta':{},previous:{},next:{}};
const $=id=>fields[id],icon=()=>new TestNode('svg'),site={repository_url:'https://github.com/TEST/TEST',source_ref:'main',live_url:''},offline=false,window={location:{protocol:'https:'}};
const sourceDownloadsByPath=new Map(),nf=new Intl.NumberFormat('en'),PAGE_SIZE=25;
let hydrated=[];const hostedStore={getRecords:async ordinals=>{hydrated=ordinals;return ordinals.map(index=>records[index]);}};
''' + self.helpers + '''
const readerGroups=createReaderGroupIndex(records,input.mapping),state={page:0,matches:[1,3],matchingOccurrences:[1,2,3],selected:new Set()};
const updateSelection=()=>{},beginView=()=>({controller:new AbortController()}),isCurrentView=()=>true,pendingView=()=>{},updateActiveFilters=()=>{},failedView=error=>{throw error;};
''' + constructors + renderer + '''
(async()=>{
 await render();const walk=node=>[node,...(node.childNodes || []).flatMap(walk)],all=walk(fields.results);
 const cards=all.filter(node=>node.className==='record-card'),versions=all.filter(node=>node.className==='source-version');
 const first=cards[0],firstNodes=walk(first),checkbox=firstNodes.find(node=>node.tag==='input');checkbox.checked=true;checkbox.events.change();
 const sourceText=firstNodes.filter(node=>node.className==='narration').map(node=>node.textContent);
 const scopedByOccurrence=Object.fromEntries([first,...versions].map(card=>{
  const panel=card.childNodes.find(node=>(node.childNodes || []).some(child=>child.className==='source-scoped-content'));
  return [card.dataset.occurrenceId,panel?walk(panel).map(node=>node.textContent || '').join('\\n'):''];
 }));
 process.stdout.write(JSON.stringify({cardCount:cards.length,versions:versions.length,representative:first.dataset.occurrenceId,
  group:first.dataset.groupId,sourceText,scopedByOccurrence,badges:firstNodes.filter(node=>(node.className || '').startsWith('reading-origin')).map(node=>node.textContent),
  text:firstNodes.map(node=>node.textContent || '').join('\\n'),links:firstNodes.filter(node=>node.tag==='a').map(node=>node.href),
  selected:[...state.selected].sort(),hydrated,counts:fields['result-count'].textContent,records}));
})().catch(error=>{process.stderr.write(error.stack);process.exitCode=1;});
'''
        actual = self.run_js(program)
        self.assertEqual(actual['cardCount'], 2)
        self.assertEqual(actual['versions'], 2)
        self.assertEqual(actual['representative'], 'TEST-occurrence-1')
        self.assertEqual(actual['group'], 'TEST-occurrence-0')
        for row in self.records[:3]:
            self.assertIn(row['text_translation'], actual['sourceText'])
            self.assertIn(row['footnotes'][0]['text'], actual['text'])
            self.assertIn(row['references']['items'][0]['source_citation'], actual['text'])
            self.assertIn(row['source']['record_url'], actual['links'])
            self.assertIn('PDF page ' + str(row['page']['pdf'][0]), actual['text'])
        self.assertIn('AI translation', actual['badges'])
        self.assertIn('Human translation', actual['badges'])
        self.assertIn('TEST scoped passage 1', actual['scopedByOccurrence']['TEST-occurrence-1'])
        self.assertNotIn('TEST scoped passage 2', actual['scopedByOccurrence']['TEST-occurrence-1'])
        self.assertIn('TEST scoped passage 2', actual['scopedByOccurrence']['TEST-occurrence-2'])
        self.assertNotIn('TEST scoped passage 1', actual['scopedByOccurrence']['TEST-occurrence-2'])
        self.assertEqual(actual['scopedByOccurrence']['TEST-occurrence-0'], '')
        self.assertIn('Source comparison', actual['text'])
        self.assertIn('TEST review does not establish complete chain equality.', actual['text'])
        self.assertIn('Human review\nNo', actual['text'])
        self.assertEqual(actual['selected'], [0, 1, 2])
        self.assertEqual(actual['hydrated'], [1, 0, 2, 3])
        self.assertIn('2 matching reading cards', actual['counts'])
        self.assertIn('3 matching source occurrences', actual['counts'])
        self.assertEqual(actual['records'], self.records)


if __name__ == '__main__':
    unittest.main()
