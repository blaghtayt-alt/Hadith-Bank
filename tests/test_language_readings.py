"""Synthetic fixtures: no test text represents an actual religious quotation."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader
from language_display import language_readings, available_languages, reading_direction
from language_versions import available_language_codes
from test_reader import fixture, READER_SNAPSHOT_JS
from test_counterpart_reader import counterparts


def multilingual_fixture():
    record = fixture()
    record.update(language='hi', text_translation='TEST Hindi source quotation', text_arabic='نص تجريبي')
    record['commentary'] = {}
    record['language_versions'] = []
    for code, quotation, collection, number in [
        ('ar', record['text_arabic'], 'TEST Arabic book', 'AR-12'),
        ('en', 'TEST English quotation <script>TEST-UNSAFE</script>', 'TEST English book', 'EN-24'),
        ('hi', record['text_translation'], 'TEST Hindi book', 'HI-36'),
        ('ur-Latn', 'TEST Roman Urdu quotation', 'TEST Roman Urdu book', 'UR-48'),
        ('uz-Cyrl', 'TEST Uzbek Cyrillic quotation', 'TEST Uzbek book', 'UZ-60'),
    ]:
        record['language_versions'].append({
            'id': 'TEST-version-' + code, 'language': code, 'text': quotation,
            'source': {'name': 'TEST publisher ' + code,
                       'record_url': 'https://example.invalid/' + code + '/entry'},
            'references': [{'collection': collection, 'number': number, 'scope': 'main_quote',
                            'url': 'https://example.invalid/' + code + '/reference'}],
            'comments': [{'text': 'COMMENT-ONLY-' + code, 'source_url': 'https://example.invalid/' + code + '/notes'}],
            'translation_provenance': None if code == 'ar' else {
                'ai_translation': 'unknown', 'current_policy': {'classification': 'ai' if code == 'en' else 'human'}},
            'scope': 'source_entry', 'match_status': 'same_source_record',
        })
    return record


class LanguageReadingTests(unittest.TestCase):
    def test_one_view_per_explicit_version_preserves_own_citations_and_bytes(self):
        record = multilingual_fixture()
        before = copy.deepcopy(record)
        readings = language_readings(record)
        self.assertEqual([item['language'] for item in readings], ['ar', 'en', 'hi', 'ur-Latn', 'uz-Cyrl'])
        self.assertEqual([item['translation_origin'] for item in readings], [None, 'ai', 'human', 'human', 'human'])
        self.assertIn('TEST English book · EN-24', readings[1]['citation'])
        self.assertNotIn('HI-36', readings[1]['citation'])
        self.assertEqual(readings[1]['source']['record_url'], 'https://example.invalid/en/entry')
        self.assertEqual(readings[1]['comments'], record['language_versions'][1]['comments'])
        self.assertEqual(record, before)

    def test_equal_wording_does_not_merge_explicit_versions_or_other_sources(self):
        record = multilingual_fixture()
        other = copy.deepcopy(record['language_versions'][2])
        other.update(id='TEST-another-edition', match_status='reviewed_parallel')
        other['source'] = {'name': 'TEST separate source', 'record_url': 'https://example.invalid/second'}
        record['language_versions'].append(other)
        self.assertEqual(sum(item['language'] == 'hi' for item in language_readings(record)), 2)
        record['language_versions'] = [other]
        self.assertEqual(sum(item['language'] == 'hi' for item in language_readings(record)), 2)

    def test_legacy_text_and_approved_counterparts_keep_separate_sources(self):
        record = fixture()
        record['counterparts'] = counterparts()
        before = copy.deepcopy(record)
        readings = language_readings(record)
        self.assertEqual([item['role'] for item in readings],
                         ['source_arabic', 'counterpart', 'counterpart', 'source_translation'])
        self.assertEqual(readings[0]['source'], record['source'])
        self.assertEqual(readings[2]['source']['record_url'], record['counterparts']['english']['source_url'])
        self.assertIn('Related publisher version:', readings[2]['qualification'])
        self.assertEqual(record, before)

    def test_source_numbers_are_labeled_and_provider_ids_are_not_hadith_numbers(self):
        record = fixture()
        self.assertNotIn('101', language_readings(record)[0]['citation'])
        record['number']['in_book'] = 'TEST-local-17'
        self.assertIn('Source number TEST-local-17', language_readings(record)[0]['citation'])
        supplied = multilingual_fixture()
        supplied['language_versions'][1]['references'] = []
        english = next(item for item in language_readings(supplied) if item['language'] == 'en')
        self.assertEqual(english['citation'], '[Collection and hadith number not supplied]')

    def test_script_language_filters_and_latin_direction(self):
        record = multilingual_fixture()
        self.assertEqual(available_languages(record), available_language_codes(record))
        self.assertEqual(available_languages(record), ['ar', 'en', 'hi', 'ur', 'ur-Latn', 'uz', 'uz-Cyrl'])
        directions = {item['language']: reading_direction(item) for item in language_readings(record)}
        self.assertEqual(directions['ar'], 'rtl')
        self.assertEqual(directions['ur-Latn'], 'ltr')
        self.assertEqual(directions['uz-Cyrl'], 'auto')

    def test_markdown_has_per_language_notes_links_and_safe_quoted_text(self):
        record = multilingual_fixture()
        record['language_versions'][1]['source']['record_url'] = 'javascript:TEST-UNSAFE'
        record['language_versions'][1]['comments'][0]['source_url'] = 'javascript:TEST-NOTE'
        before = copy.deepcopy(record)
        page = reader.markdown_record(record, 1)
        self.assertIn('English · notes and commentary', page)
        self.assertIn('[TEST English book · EN-24]', page)
        self.assertIn('Translation origin: AI', page)
        self.assertIn('&lt;script&gt;TEST-UNSAFE&lt;/script&gt;', page)
        self.assertNotIn('href="javascript:', page)
        self.assertIn('<section class="language-reading" lang="ur-Latn">', page)
        self.assertIn('<p dir="ltr">TEST Roman Urdu quotation</p>', page)
        self.assertEqual(record, before)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser parity')
    def test_browser_views_filters_and_commentary_search_match_python(self):
        records = [multilingual_fixture(), fixture(2)]
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = READER_SNAPSHOT_JS + '''const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};
const valueText = ''' + helpers + '''
const scope=resolveMaterialFilters(records,{language:'en'});
process.stdout.write(JSON.stringify({views:languageReadings(records[0]),languages:availableLanguageCodes(records[0]),
 englishRows:scope.rows.map(item=>item.id),key:primarySearchKey(records[0]),notes:annotationSearchKey(records[0]),records}));'''
        run = subprocess.run([shutil.which('node'), '-e', program,], input=json.dumps(records),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        self.assertEqual(actual['views'], language_readings(records[0]))
        self.assertEqual(actual['languages'], available_language_codes(records[0]))
        self.assertEqual(actual['englishRows'], [records[0]['id']])
        self.assertIn('test english quotation', actual['key'])
        self.assertNotIn('comment-only-en', actual['key'])
        self.assertIn('comment-only-en', actual['notes'])
        self.assertEqual(actual['records'], records)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for DOM construction regression')
    def test_language_panel_dom_owns_sources_notes_and_open_controls(self):
        """Exercise DOM construction, not a substitute for a browser layout test."""
        record = multilingual_fixture()
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        constructors = 'function detail(' + template.split('function detail(', 1)[1].split('function sourceFiles(', 1)[0]
        panels = 'function languageReading(' + template.split('function languageReading(', 1)[1].split('function card(', 1)[0]
        program = READER_SNAPSHOT_JS + '''const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};
class TestNode {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.attributes={};this.events={};this.open=false;}
 get childNodes(){return this.children;}
 append(...nodes){this.children.push(...nodes);}
 setAttribute(key,value){this.attributes[key]=value;}
 addEventListener(key,handler){this.events[key]=handler;}
 querySelector(tag){return this.children.find(node=>node.tag===tag) || this.children.flatMap(node=>node.querySelector?[node.querySelector(tag)]:[]).find(Boolean);}
 focus(){this.focused=true;} scrollIntoView(){this.scrolled=true;}
}
const document={createElement:tag=>new TestNode(tag)},fields={'language-filter':{value:''},'show-arabic':{checked:true},'show-english':{checked:true}};
const $=id=>fields[id],icon=name=>new TestNode('svg');
const valueText = ''' + helpers + constructors + panels + '''
const card=new TestNode('article');appendLanguageReadings(card,records[0],7);
const nodes=node=>[node,...node.children.flatMap(nodes)],all=nodes(card);
const sections=all.filter(node=>node.tag==='details' && node.className==='language-reading');
const english=sections.find(node=>node.dataset.language==='en'),englishNodes=nodes(english);
const roman=sections.find(node=>node.dataset.language==='ur-Latn'),wasClosed=!roman.open;
const romanButton=all.find(node=>node.tag==='button' && node.textContent==='Roman Urdu');romanButton.events.click();
process.stdout.write(JSON.stringify({count:sections.length,arabicOpen:sections.find(node=>node.dataset.language==='ar').open,
 englishOpen:english.open,notesClosed:!englishNodes.find(node=>node.className==='detail reading-notes').open,
 englishLinks:englishNodes.filter(node=>node.tag==='a').map(node=>({href:node.href,target:node.target,rel:node.rel})),
 citation:englishNodes.find(node=>node.className==='reading-citation').textContent,
 romanWasClosed:wasClosed,romanOpened:roman.open,romanFocused:roman.querySelector('summary').focused,
 romanDirection:nodes(roman).find(node=>node.tag==='p' && node.className==='narration').dir,
 sourceTextNodes:englishNodes.filter(node=>node.tag==='p' && node.className==='narration').map(node=>node.textContent),records}));'''
        run = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps([record]),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        self.assertEqual(actual['count'], 5)
        self.assertTrue(actual['arabicOpen'])
        self.assertTrue(actual['englishOpen'])
        self.assertTrue(actual['notesClosed'])
        self.assertEqual({link['href'] for link in actual['englishLinks']}, {
            'https://example.invalid/en/entry', 'https://example.invalid/en/reference',
            'https://example.invalid/en/notes'})
        self.assertTrue(all(link['target'] == '_blank' and link['rel'] == 'noopener noreferrer'
                            for link in actual['englishLinks']))
        self.assertEqual(actual['citation'], '[TEST English book · EN-24]')
        self.assertTrue(actual['romanWasClosed'] and actual['romanOpened'] and actual['romanFocused'])
        self.assertEqual(actual['romanDirection'], 'ltr')
        self.assertIn(record['language_versions'][1]['text'], actual['sourceTextNodes'])
        self.assertEqual(actual['records'], [record])

    @unittest.skipUnless(shutil.which('node'), 'Node is required for exact-occurrence link checks')
    def test_exact_occurrence_links_do_not_match_prefixes_and_clear_on_new_search(self):
        first, second = multilingual_fixture(), multilingual_fixture()
        first.update(id='TEST:1', source_id='deenhindi-TEST')
        second.update(id='TEST:10', source_id='deenhindi-TEST')
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        apply = 'function applyFilters(){' + template.split('function applyFilters(){', 1)[1].split('$("query").addEventListener', 1)[0]
        clear = 'function clearExactOccurrence(){' + template.split('function clearExactOccurrence(){', 1)[1].split('const names =', 1)[0]
        program = READER_SNAPSHOT_JS + '''const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};
const state={exactOccurrence:'TEST:1',matches:[]},fields={query:{value:''},'language-filter':{value:''},'book-filter':{value:''},'source-filter':{value:''},'origin-filter':{value:''},'include-commentary':{checked:false}};
const $=id=>fields[id],render=()=>{},window={location:{href:'https://example.invalid/index.html?occurrence=TEST%3A1&keep=yes'}},history={replaceState(_a,_b,url){this.url=url.href;}};
const valueText = ''' + helpers + apply + clear + '''
(async()=>{applyFilters();const exact=state.matches.map(i=>records[i].id);state.exactOccurrence='TEST:missing';applyFilters();const missing=state.matches;
clearExactOccurrence();applyFilters();const all=state.matches.map(i=>records[i].id);const link=await recordPageURL(records[0],{live_url:'https://example.invalid/bank/'});
process.stdout.write(JSON.stringify({exact,missing,all,link,historyURL:history.url}));})();'''
        run = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps([first, second]),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        self.assertEqual(actual['exact'], ['TEST:1'])
        self.assertEqual(actual['missing'], [])
        self.assertEqual(actual['all'], ['TEST:1', 'TEST:10'])
        self.assertEqual(actual['link'], 'https://example.invalid/bank/index.html?occurrence=TEST%3A1')
        self.assertEqual(actual['historyURL'], 'https://example.invalid/index.html?keep=yes')

    @unittest.skipUnless(shutil.which('node'), 'Node is required for supplied-version availability parity')
    def test_supplied_arabic_and_english_count_as_available_text(self):
        from counterpart_coverage import availability_for
        record = multilingual_fixture()
        record['text_arabic'] = None
        linked = copy.deepcopy(record)
        for version in linked['language_versions']:
            if version['language'] == 'en':
                version.update(text=None, scope='external_source')
        unsafe = copy.deepcopy(linked)
        unsafe['language_versions'][1]['source']['record_url'] = 'javascript:TEST-UNSAFE'
        samples = [record, linked, unsafe]
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = READER_SNAPSHOT_JS + '''const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify({states:records.map(counterpartAvailability),
 choices:records.map(r=>({text:matchesCounterpartAvailability(r,'both-text'),link:matchesCounterpartAvailability(r,'english-link')}))}));'''
        run = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(samples),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        self.assertEqual(actual['states'], [availability_for(item) for item in samples])
        self.assertEqual(actual['states'], [
            {'arabic': 'text', 'english': 'text'},
            {'arabic': 'text', 'english': 'external_link'},
            {'arabic': 'text', 'english': 'missing'}])
        self.assertEqual(actual['choices'], [
            {'text': True, 'link': False}, {'text': False, 'link': True}, {'text': False, 'link': False}])


if __name__ == '__main__':
    unittest.main()
