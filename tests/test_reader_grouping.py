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
from bank_discovery import build_discovery_payload
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
                                input=json.dumps({'records': self.records, 'mapping': mapping(self.records),
                                                  'discovery': build_discovery_payload(self.records, {
                                                      'record_count': len(self.records), 'records_sha256': '0' * 64,
                                                      'reader_groups': mapping(self.records)})}),
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

    def test_compact_group_then_lazy_versions_preserve_sources_and_selection(self):
        # Execute the real compact renderer and on-demand workspace against a
        # small DOM implementation. Browser layout/accessibility has its own gate.
        for index in (1, 2):
            self.records[index]['source_scoped_content'] = {
                'segments': [{'source_segment_id': 'TEST-scope-' + str(index), 'story': 'main',
                              'cp_start': 0, 'cp_end': 1, 'text_verbatim': 'TEST scoped passage ' + str(index),
                              'role_candidates': ['TEST source role'], 'leaf_semantic_references': [],
                              'source_ambiguity_ids': []}],
                'footnotes': [], 'uncertainties': {}}
        constructors = 'function meta(' + self.template.split('function meta(', 1)[1].split('function updateSelection(', 1)[0]
        discovery = 'const discoveryMode=' + self.template.split('const discoveryMode=', 1)[1].split('async function applyFilters(', 1)[0]
        identity = 'function occurrenceIndexes(' + self.template.split('function occurrenceIndexes(', 1)[1].split('function clearExactOccurrence(', 1)[0]
        program = r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),records=input.records,names={},snapshot={book_titles:{}};
const discoveryEngine=require('./reader/discovery-engine.js').create(input.discovery);
const walk=node=>[node,...(node.childNodes||[]).flatMap(walk)];
const matches=(node,selector)=>selector.startsWith('#')?node.id===selector.slice(1):selector.startsWith('.')?(node.className||'').split(/\s+/).includes(selector.slice(1)):node.tag===selector;
class TestNode {
 constructor(tag){this.tag=tag;this.childNodes=[];this.dataset={};this.events={};this.open=false;this.value='';this._text='';this.className='';}
 append(...nodes){for(const node of nodes){if(node&&typeof node==='object'){if(node.parentNode)node.parentNode.childNodes=node.parentNode.childNodes.filter(old=>old!==node);node.parentNode=this;}this.childNodes.push(node);}}
 setAttribute(key,value){this[key]=value;}getAttribute(key){return this[key]??null;}
 addEventListener(key,handler){this.events[key]=handler;}replaceChildren(...nodes){for(const old of this.childNodes)if(old&&typeof old==='object')old.parentNode=null;this.childNodes=[];this.append(...nodes);}
 querySelector(selector){return walk(this).slice(1).find(node=>matches(node,selector))||null;}
 querySelectorAll(selector){return walk(this).slice(1).filter(node=>matches(node,selector));}
 get classList(){return {add:(name)=>this.className=[...new Set(this.className.split(/\s+/).filter(Boolean).concat(name))].join(' ')};}
 get options(){return this.childNodes.filter(node=>node.tag==='option');}
 get selectedOptions(){return this.options.filter(node=>node.value===this.value);}
 set textContent(text){this._text=String(text);this.childNodes=[];}get textContent(){return this._text+this.childNodes.map(node=>typeof node==='string'?node:node.textContent||'').join('');}
 focus(){}scrollIntoView(){}
}
const Node=TestNode,fields={};
for(const id of ['results','results-heading','result-count','page-meta','previous','next','discovery-results','narration-workspace','workspace-heading','workspace-status','workspace-content','workspace-versions','shared-reading-tools','search-suggestions'])fields[id]=new TestNode('div');
for(const id of ['query','language-filter','book-filter','source-filter','origin-filter','counterpart-filter','source-book-filter','chapter-filter','source-topic-filter','narrator-filter','type-filter','grade-filter','preferred-language'])fields[id]=new TestNode('input');
fields['language-filter'].value='ja';fields['preferred-language'].value='ja';fields['show-arabic']={checked:false};fields['show-english']={checked:false};
const roots=[...Object.values(fields)],toolbar=new TestNode('div'),workspaceTop=new TestNode('div'),pagination=new TestNode('nav');
const document={body:new TestNode('body'),createElement:tag=>new TestNode(tag),createTextNode:text=>Object.assign(new TestNode('#text'),{textContent:text}),createDocumentFragment:()=>new TestNode('fragment'),querySelector(selector){if(selector==='.results-toolbar')return toolbar;if(selector==='.workspace-top')return workspaceTop;if(selector==='.pagination')return pagination;return roots.flatMap(walk).find(node=>matches(node,selector))||null;}};
const $=id=>fields[id]||roots.flatMap(walk).find(node=>node.id===id),icon=()=>new TestNode('svg'),site={repository_url:'https://github.com/TEST/TEST',source_ref:'main',live_url:'https://example.invalid/bank/'},offline=false,window={location:new URL('https://example.invalid/bank/')},navigator={onLine:true};
const history={pushState(_a,_b,url){window.location=new URL(url);},replaceState(_a,_b,url){window.location=new URL(url);}};
const sourceDownloadsByPath=new Map(),nf=new Intl.NumberFormat('en'),PAGE_SIZE=25;
const hydrated=[],hostedStore={getRecord:async ordinal=>{hydrated.push(ordinal);return records[ordinal];}};
""" + self.helpers + r"""
const readerGroups=createReaderGroupIndex(records,input.mapping),occurrenceOrdinals=readerGroups.ordinals;
const result=discoveryEngine.search({query:'',preferredLanguage:'ja',filters:{language:'ja'}});
const state={page:0,matches:result.results.map(item=>item.ordinal),discoveryResults:result.results,matchingOccurrences:result.matchedOccurrences,selected:new Set(),openOrdinal:null};
const updateSelection=()=>{},beginView=()=>({controller:new AbortController()}),isCurrentView=()=>true,pendingView=()=>{},updateActiveFilters=()=>{},cancelView=()=>{},failedView=error=>{throw error;};
""" + identity + constructors + discovery + r"""
(async()=>{
 const viewTransitions=[];renderHome();viewTransitions.push(document.body.dataset.discoveryView);
 await render();viewTransitions.push(document.body.dataset.discoveryView);const compact=walk(fields.results).filter(node=>node.className==='compact-result');
 const initialHydrated=[...hydrated],first=compact[0],checkbox=walk(first).find(node=>node.tag==='input');checkbox.checked=true;checkbox.events.change();
 const compactSelection=[...state.selected].sort(),initialCounts=fields['result-count'].textContent;
 await openNarrationWorkspace(1,result.results.find(item=>item.members.includes(1)),{updateURL:false});
 viewTransitions.push(document.body.dataset.discoveryView);
 const firstHydrated=[...hydrated],full=walk(fields['workspace-content']).find(node=>node.className==='record-card'),evidence=$('workspace-evidence').textContent;
 const capture=(card)=>({id:card.dataset.occurrenceId,sourceText:walk(card).filter(node=>node.className==='narration').map(node=>node.textContent),text:card.textContent,links:walk(card).filter(node=>node.tag==='a').map(node=>node.href),badges:walk(card).filter(node=>(node.className||'').startsWith('reading-origin')).map(node=>node.textContent)});
 const captured=[capture(full)],compare=fields['workspace-content'].querySelector('#compare-source-version');
 compare.value='0';await compare.events.change();captured.push(capture($('workspace-comparison-content').querySelector('.source-version')));
 compare.value='2';await compare.events.change();captured.push(capture($('workspace-comparison-content').querySelector('.source-version')));
 const comparisonCount=walk($('workspace-comparison-content')).filter(node=>node.className==='source-version').length;
 const workspaceHydrated=[...hydrated];fields.query.value='anchor intended wording';
 const broader=discoveryEngine.search({query:fields.query.value,mode:'wording',preferredLanguage:'ja'});
 state.discoveryResults=broader.results;state.matchingOccurrences=broader.matchedOccurrences;state.broaderWording=broader.broaderWording;renderSuggestions(broader);await render();viewTransitions.push(document.body.dataset.discoveryView);
 const broaderCard=fields.results.querySelector('.compact-result'),preferredPreview=broaderCard.querySelector('.result-excerpt').textContent;
 await broaderCard.querySelector('.show-matching-wording').events.click();
 const matching=broaderCard.querySelector('.matching-wording'),quoted=discoveryEngine.search({query:'"anchor intended wording"',mode:'wording'});
 const broaderView={note:fields['search-suggestions'].textContent,terms:broaderCard.querySelector('.broader-wording-terms').textContent,
  counts:fields['result-count'].textContent,preferredPreview,matchingText:matching.querySelector('.result-excerpt').textContent,
  matchingSource:matching.querySelector('.reading-source').href,matchingHydrated:hydrated.slice(workspaceHydrated.length),quotedResults:quoted.results.length,quotedBroader:quoted.broaderWording};
 renderHome();viewTransitions.push(document.body.dataset.discoveryView);
 process.stdout.write(JSON.stringify({compactCount:compact.length,initialHydrated,firstHydrated,hydrated:workspaceHydrated,compactSelection,captured,evidence,comparisonCount,counts:initialCounts,broaderView,viewTransitions,records,exported:compactSelection.map(index=>records[index])}));
})().catch(error=>{process.stderr.write(error.stack);process.exitCode=1;});
"""
        actual = self.run_js(program)
        self.assertEqual(actual['compactCount'], 2)
        self.assertEqual(actual['viewTransitions'], ['home', 'results', 'workspace', 'results', 'home'])
        self.assertEqual(actual['initialHydrated'], [], 'Compact results must not hydrate full source records')
        self.assertEqual(actual['firstHydrated'], [1], 'Opening one family loads only its selected source')
        self.assertEqual(actual['hydrated'], [1, 0, 2])
        self.assertEqual(actual['comparisonCount'], 1, 'Changing the comparison replaces that view, not its source data')
        by_id = {row['id']: row for row in actual['captured']}
        for row in self.records[:3]:
            view = by_id[row['id']]
            self.assertIn(row['text_translation'], view['sourceText'])
            self.assertIn(row['footnotes'][0]['text'], view['text'])
            self.assertIn(row['references']['items'][0]['source_citation'], view['text'])
            self.assertIn(row['source']['record_url'], view['links'])
            self.assertIn('PDF page ' + str(row['page']['pdf'][0]), view['text'])
        self.assertIn('AI translation', by_id['TEST-occurrence-1']['badges'])
        self.assertIn('Human translation', by_id['TEST-occurrence-2']['badges'])
        self.assertIn('TEST scoped passage 1', by_id['TEST-occurrence-1']['text'])
        self.assertNotIn('TEST scoped passage 2', by_id['TEST-occurrence-1']['text'])
        self.assertIn('TEST scoped passage 2', by_id['TEST-occurrence-2']['text'])
        self.assertNotIn('TEST scoped passage 1', by_id['TEST-occurrence-2']['text'])
        self.assertNotIn('TEST scoped passage', by_id['TEST-occurrence-0']['text'])
        self.assertIn('TEST review does not establish complete chain equality.', actual['evidence'])
        self.assertIn('"human_review": false', actual['evidence'])
        self.assertEqual(actual['compactSelection'], [0, 1, 2])
        self.assertEqual(actual['exported'], self.records[:3])
        self.assertIn('2 results', actual['counts'])
        self.assertIn('3 matching source occurrences', actual['counts'])
        broader = actual['broaderView']
        self.assertIn('Broader wording matches', broader['note'])
        self.assertIn('not an exact phrase', broader['note'])
        self.assertIn('Found: anchor, wording', broader['terms'])
        self.assertIn('Not found: intended', broader['terms'])
        self.assertIn('Broader wording matches', broader['counts'])
        self.assertEqual(broader['preferredPreview'], self.records[1]['text_translation'])
        self.assertEqual(broader['matchingText'], self.records[0]['text_translation'])
        self.assertEqual(broader['matchingSource'], self.records[0]['source']['record_url'])
        self.assertEqual(broader['matchingHydrated'], [0], 'Matching wording must hydrate its English source, not the Japanese preview member')
        self.assertEqual(broader['quotedResults'], 0)
        self.assertIsNone(broader['quotedBroader'])
        self.assertEqual(actual['records'], self.records)

    def test_standalone_reference_is_recognized_without_reinterpreting_quoted_words(self):
        self.records[3]['references'] = {'items': []}
        self.records[3]['number'] = {'in_book': '1', 'source_entry_id': '1'}
        self.records[3]['title'] = 'TEST local Muslim 1 label'
        helper = 'function discoveryRequestMode(' + self.template.split(
            'function discoveryRequestMode(', 1)[1].split('const discoveryFilters=', 1)[0]
        actual = self.run_js(r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const discoveryEngine=require('./reader/discovery-engine.js').create(input.discovery);
""" + helper + r"""
const cases=[['Bukhari 1','wording'],['Muslim 1','wording'],['صحيح البخاري ١','wording'],
 ['"Bukhari 1"','wording'],['“Bukhari 1”','wording'],['Bukhari 1 intentions','wording'],
 ['edition 1','wording'],['provider 1','wording'],['Bukhari 1','topic']];
const modes=cases.map(([query,mode])=>discoveryRequestMode(query,mode));
const results=discoveryEngine.search({query:'Muslim 1',mode:discoveryRequestMode('Muslim 1'),group:false});
process.stdout.write(JSON.stringify({modes,matches:results.matchedOccurrences,records:input.records}));
""")
        self.assertEqual(actual['modes'], ['reference', 'reference', 'reference',
                                         'wording', 'wording', 'wording', 'wording', 'wording', 'topic'])
        self.assertEqual(actual['matches'], [0, 1, 2], 'Local/provider number 1 must not become a canonical citation')
        self.assertEqual(actual['records'], self.records)

    def test_matching_excerpt_binds_exact_source_reading_and_preserves_original_unicode(self):
        self.records[0]['text_translation'] = ('TEST opening context. ' * 30
            + '🧪 TEST needle late & <script>literal</script> source wording.' + ' TEST following text.' * 20)
        self.records[0]['language_versions'] = [
            {'id': 'TEST-arabic', 'language': 'ar', 'text': 'نَصّ تَجْرِيبِيّ: إنَّما الصَّلَاة. 🧪',
             'source': {'name': 'TEST Arabic source', 'record_url': 'https://example.invalid/arabic'},
             'scope': 'source_entry', 'match_status': 'same_source_record'},
            {'id': 'TEST-context', 'language': 'en', 'text': 'TEST needle late context only.',
             'source': {'name': 'TEST contextual source'}, 'scope': 'source_context'},
        ]
        helper = 'function matchingSourceExcerpt(' + self.template.split(
            'function matchingSourceExcerpt(', 1)[1].split('function appendMatchingWordAction(', 1)[0]
        actual = self.run_js(r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),records=input.records,names={},snapshot={book_titles:{}},hostedStore=null;
const discoveryEngine=require('./reader/discovery-engine.js').create(input.discovery);
""" + self.helpers + helper + r"""
const hit=discoveryEngine.search({query:'needle late',mode:'wording',preferredLanguage:'ja'}).results[0];
const extracted=matchingSourceExcerpt(records[hit.matchedOrdinal],hit,'needle late');
const selectedMember=matchingSourceExcerpt(records[hit.ordinal],hit,'needle late');
const arabic={matchLocation:{field:'quotation',language:'ar',readingId:'TEST-arabic',term:'الصلاة'}};
const normalized=matchingSourceExcerpt(records[0],arabic,'انما'),expanded=matchingSourceExcerpt(records[0],arabic,'prayer');
const context=matchingSourceExcerpt(records[0],{matchLocation:{field:'quotation',language:'en',readingId:'TEST-context'}},'needle late');
const wrongLanguage=matchingSourceExcerpt(records[0],{matchLocation:{field:'quotation',language:'ja',readingId:'source-translation'}},'needle late');
const metadata=matchingSourceExcerpt(records[0],{matchLocation:{field:'metadata',language:'en',readingId:'source-translation'}},'needle late');
const duplicate=JSON.parse(JSON.stringify(records[0]));duplicate.language_versions.push({...duplicate.language_versions[0]});
const ambiguous=matchingSourceExcerpt(duplicate,arabic,'انما');
process.stdout.write(JSON.stringify({hit:{ordinal:hit.ordinal,matchedOrdinal:hit.matchedOrdinal,excerptKind:hit.excerptKind},extracted,selectedMember,normalized,expanded,context,wrongLanguage,metadata,ambiguous,records}));
""")
        self.assertEqual(actual['hit'], {'ordinal': 1, 'matchedOrdinal': 0, 'excerptKind': 'source-preview'})
        excerpt = actual['extracted']
        self.assertEqual(excerpt['reading']['id'], 'source-translation')
        self.assertEqual(excerpt['reading']['language'], 'en')
        self.assertEqual(excerpt['reading']['source']['record_url'], self.records[0]['source']['record_url'])
        self.assertIn('needle late', excerpt['text'])
        self.assertIn('<script>literal</script>', excerpt['text'])
        self.assertIn(excerpt['text'], self.records[0]['text_translation'])
        self.assertGreater(excerpt['start'], 180, 'Late matches must be read from the actual complete source')
        exact_arabic = self.records[0]['language_versions'][0]['text']
        self.assertEqual(actual['normalized']['text'], exact_arabic)
        self.assertEqual(actual['expanded']['text'], exact_arabic)
        for key in ('selectedMember', 'context', 'wrongLanguage', 'metadata', 'ambiguous'):
            self.assertIsNone(actual[key], key + ' must not borrow or infer a different source reading')
        self.assertEqual(actual['records'], self.records)

    def test_collection_choices_disambiguate_labels_without_merging_source_keys(self):
        helper = 'function collectionChoiceLabels(' + self.template.split(
            'function collectionChoiceLabels(', 1)[1].split('function fillFilter(', 1)[0]
        actual = self.run_js(r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const languageLabel=code=>({fa:'Persian',uz:'Uzbek',vi:'Vietnamese',en:'English'}[code]||code);
""" + helper + r"""
const samples=[
 {book_key:'riyadh-al-salihin',language:'fa',languages:['fa','ar','en']},
 {book_key:'riyad-as-salihin',language:'uz',languages:['uz','ar','en']},
 {book_key:'riyad-as-salihin',language:'vi'},
 {book_key:'TEST-distinct-B',language:'en'},{book_key:'TEST-distinct-A',language:'en'},
 {book_key:'TEST-unique',language:'fa'}];
const labels=new Map([['riyadh-al-salihin','Riyadh al-Salihin'],['riyad-as-salihin','Riyadh al-Salihin'],
 ['TEST-distinct-B','TEST collection'],['TEST-distinct-A','TEST collection'],['TEST-unique','TEST unique collection']]);
const before=JSON.stringify(samples),display=collectionChoiceLabels(samples,labels),reversed=collectionChoiceLabels([...samples].reverse(),new Map([...labels].reverse()));
process.stdout.write(JSON.stringify({display:Object.fromEntries(display),reversed:Object.fromEntries(reversed),labels:Object.fromEntries(labels),unchanged:before===JSON.stringify(samples),count:display.size}));
""")
        self.assertEqual(actual['display']['riyadh-al-salihin'], 'Riyadh al-Salihin · Persian sources')
        self.assertEqual(actual['display']['riyad-as-salihin'], 'Riyadh al-Salihin · Uzbek / Vietnamese sources')
        self.assertEqual(actual['display']['TEST-distinct-A'], 'TEST collection · English sources · Source group 1')
        self.assertEqual(actual['display']['TEST-distinct-B'], 'TEST collection · English sources · Source group 2')
        self.assertEqual(actual['display']['TEST-unique'], 'TEST unique collection')
        self.assertEqual(actual['display'], actual['reversed'], 'Presentation names must be independent of source ordering')
        self.assertEqual(actual['count'], 5)
        self.assertEqual(actual['labels']['riyadh-al-salihin'], actual['labels']['riyad-as-salihin'])
        self.assertTrue(actual['unchanged'])


if __name__ == '__main__':
    unittest.main()
