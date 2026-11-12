"""Synthetic fixtures: no test text represents an actual religious quotation."""
import copy
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_reader as reader
from build_discovery import render_language_reading, uses_shared_web_reader, occurrence_link
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


def multilingual_translator_fixture():
    record = multilingual_fixture()
    record['translator'] = {'name': 'TEST parent translator'}
    record['source']['translator'] = {'name': 'TEST parent source translator'}
    record['translation_provenance']['translator'] = 'TEST parent provenance translator'
    versions = {item['language']: item for item in record['language_versions']}
    versions['ar']['source']['translator'] = {'name': 'TEST Arabic catalog author'}
    versions['ar']['translation_provenance'] = {'translator': 'TEST Arabic metadata name'}
    names = {'ar': None, 'en': 'TEST English translator <script>TEST-LITERAL</script>',
             'hi': 'TEST Hindi translator', 'ur-Latn': None, 'uz-Cyrl': None}
    versions['en']['source']['translator'] = {'name': names['en']}
    versions['en']['translation_provenance']['translator'] = 'TEST English fallback translator'
    versions['hi']['source']['translator'] = {'name': None}
    versions['hi']['translation_provenance']['translator'] = names['hi']
    versions['ur-Latn']['source']['translator'] = {'name': ' Unknown '}
    versions['ur-Latn']['translation_provenance']['translator'] = 'unknown'
    return record, names


class LanguageReadingTests(unittest.TestCase):
    def test_markdown_online_links_use_existing_shared_or_static_destinations(self):
        record = multilingual_fixture()
        record.update(id='TEST:1&other=2', source_id='fawaz-TEST')
        before = copy.deepcopy(record)
        site = {'live_url': 'https://example.invalid/bank/'}
        page = reader.markdown_record(record, 1, site=site)
        self.assertIn('[Open this narration online](https://example.invalid/bank/?occurrence=TEST%3A1%26other%3D2)', page)
        self.assertEqual(record, before)
        static_page = reader.markdown_record(fixture(), 1, site=site)
        self.assertIn('[Open this narration online](https://example.invalid/bank/hadith/ja/fixture-book/snapshot-a/', static_page)
        self.assertNotIn('?occurrence=', static_page)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for shared-reader link parity')
    def test_bulk_and_hadisuz_links_use_exact_shared_reader_occurrences(self):
        records = []
        for prefix in ('fawaz-', 'hadisuz-'):
            record = multilingual_fixture()
            record.update(id=prefix + 'TEST:1.5', source_id=prefix + 'TEST')
            self.assertTrue(uses_shared_web_reader(record))
            self.assertEqual(occurrence_link(record, 'languages/uz.html'),
                             '../?occurrence=' + prefix + 'TEST%3A1.5')
            records.append(record)
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        function = 'const recordPageURL =' + template.split('const recordPageURL =', 1)[1].split('const recordFileURL =', 1)[0]
        program = function + '''
const rows=JSON.parse(require('fs').readFileSync(0,'utf8'));
Promise.all(rows.map(row=>recordPageURL(row,{live_url:'https://example.invalid/bank/'})))
.then(urls=>process.stdout.write(JSON.stringify(urls)));
'''
        result = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps(records),
                                text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), [
            'https://example.invalid/bank/index.html?occurrence=fawaz-TEST%3A1.5',
            'https://example.invalid/bank/index.html?occurrence=hadisuz-TEST%3A1.5'])

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

    def test_markdown_keeps_raw_only_citation_and_numbering_qualifiers_in_own_reading(self):
        record = multilingual_fixture()
        english = record['language_versions'][1]
        english['references'].append({'collection': None, 'number': None,
            'source_citation': 'TEST raw attribution <not normalized>',
            'scope': 'source_supplied_citation', 'numbering_system': 'publisher_source_local',
            'canonical_mapping_status': 'not_inferred', 'url': english['source']['record_url']})
        english['source']['upstream_sources'] = [{'name': 'TEST site credit', 'url': 'https://example.invalid/credit',
            'scope': 'site_level_attribution_not_record_verified'}]
        before = copy.deepcopy(record)
        page = reader.markdown_record(record, 1)
        own = page.split('<section class="language-reading" lang="en">', 1)[1].split('</section>', 1)[0]
        other = page.split('<section class="language-reading" lang="hi">', 1)[1].split('</section>', 1)[0]
        self.assertIn('<details class="reading-references">', own)
        self.assertIn('English · references (2)', own)
        self.assertIn('TEST raw attribution &lt;not normalized&gt;', own)
        self.assertNotIn('TEST raw attribution', other)
        self.assertIn('Numbering: publisher source local', own)
        self.assertIn('Canonical mapping: not inferred', own)
        self.assertIn('site level attribution not record verified', own)
        self.assertEqual(own.count('href="' + english['source']['record_url'] + '"'), 1)
        self.assertEqual(record, before)

    def test_pending_detail_metadata_notice_tracks_the_saved_source_state(self):
        record = multilingual_fixture()
        english = record['language_versions'][1]
        notice = 'Detailed source references and notes have not been retrieved yet.'
        english['source']['detail_metadata_status'] = 'detail_metadata_pending'
        english['references_status'] = 'section_reference_only_detail_metadata_pending'
        english['comments_status'] = 'detail_metadata_pending'
        before = copy.deepcopy(record)
        page = reader.markdown_record(record, 1)
        own = page.split('<section class="language-reading" lang="en">', 1)[1].split('</section>', 1)[0]
        other = page.split('<section class="language-reading" lang="hi">', 1)[1].split('</section>', 1)[0]
        self.assertIn(notice, own)
        self.assertNotIn(notice, other)
        self.assertEqual(record, before)
        english['source']['detail_metadata_status'] = 'detail_metadata_source_parsed'
        english['references_status'] = 'source_detail_fields_parsed_canonical_identity_unverified'
        english['comments_status'] = 'no_notes_in_supported_detail_blocks'
        self.assertNotIn(notice, reader.markdown_record(record, 1))

    def test_static_language_reading_preserves_raw_references_and_pending_state(self):
        record = multilingual_fixture()
        english = record['language_versions'][1]
        english['source']['detail_metadata_status'] = 'detail_metadata_pending'
        english['references'] += [
            {'source_citation': 'TEST raw-only citation <script>preserve literally</script>',
             'scope': 'source_supplied_citation', 'numbering_system': 'publisher_source_local',
             'canonical_mapping_status': 'not_inferred'},
            {'collection': 'TEST repeated source', 'url': english['source']['record_url']},
            {'collection': 'TEST alternate URL', 'source_url': 'https://example.invalid/upstream'},
            {'source_citation': 'TEST unsafe link retained as text', 'url': 'javascript:TEST-UNSAFE'},
        ]
        before = copy.deepcopy(record)
        readings = {item['language']: item for item in language_readings(record)}
        own = render_language_reading(readings['en'])
        other = render_language_reading(readings['hi'])
        notice = 'Detailed source references and notes have not been retrieved yet.'
        self.assertIn('References for this language (5)', own)
        self.assertIn('TEST raw-only citation &lt;script&gt;preserve literally&lt;/script&gt;', own)
        self.assertIn('Numbering: publisher source local', own)
        self.assertIn('Canonical mapping: not inferred', own)
        self.assertIn('source supplied citation', own)
        self.assertIn(notice, own)
        self.assertNotIn('TEST raw-only citation', other)
        self.assertNotIn(notice, other)
        self.assertNotIn('href="javascript:', own)
        self.assertNotIn('<script>', own)
        self.assertIn('href="https://example.invalid/upstream" target="_blank" rel="noopener noreferrer"', own)
        self.assertEqual(own.count('href="' + english['source']['record_url'] + '"'), 1)
        self.assertIn('COMMENT-ONLY-en', own)
        self.assertNotIn('COMMENT-ONLY-hi', own)
        self.assertEqual(record, before)
        readings['en']['source']['detail_metadata_status'] = 'detail_metadata_source_parsed'
        self.assertNotIn(notice, render_language_reading(readings['en']))

    def test_static_translator_credit_is_explicit_and_language_owned(self):
        record, names = multilingual_translator_fixture()
        before = copy.deepcopy(record)
        for reading in language_readings(record):
            with self.subTest(language=reading['language']):
                page = render_language_reading(reading)
                name = names[reading['language']]
                if name:
                    source = page.split('<p class="reading-source">', 1)[1].split('</p>', 1)[0]
                    self.assertIn('<span class="reading-translator"> · Translator: ' +
                                  html.escape(name) + '</span>', source)
                else:
                    self.assertNotIn('reading-translator', page)
                    self.assertNotIn('Translator:', page)
                if reading['language'] == 'ar':
                    self.assertNotIn('Translation origin:', page)
                self.assertNotIn('TEST parent', page)
                self.assertNotIn('TEST English fallback translator', page)
                self.assertNotIn('<script>', page)
        self.assertEqual(record, before)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser parity')
    def test_browser_views_filters_and_commentary_search_match_python(self):
        records = [multilingual_fixture(), fixture(2)]
        note = 'TEST source narrator differs <script>preserve literal note</script>'
        records[0]['language_versions'][1]['source']['source_report_alignment_note'] = note
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
        english = next(item for item in actual['views'] if item['language'] == 'en')
        self.assertEqual(english['qualification'], note)
        self.assertEqual(english['text'], records[0]['language_versions'][1]['text'])
        page = render_language_reading(english)
        self.assertIn(html.escape(note), page)
        self.assertNotIn('<script>', page)
        self.assertEqual(actual['languages'], available_language_codes(records[0]))
        self.assertEqual(actual['englishRows'], [records[0]['id']])
        self.assertIn('test english quotation', actual['key'])
        self.assertNotIn('comment-only-en', actual['key'])
        self.assertIn('comment-only-en', actual['notes'])
        self.assertEqual(actual['records'], records)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser parity')
    def test_pending_language_context_has_own_panel_but_is_not_searchable_matn(self):
        record = multilingual_fixture()
        record['language_versions'][1].update(text=None, scope='external_source', quotation_status='boundary_pending')
        record['language_versions'][0]['quotation_status'] = 'disjoint_source_spans'
        record['language_versions'][0]['source']['source_report_alignment_note'] = 'TEST source word differs.'
        record['language_versions'][4]['quotation_status'] = 'multiple_source_reports'
        record['language_versions'][4]['source']['source_report_alignment_note'] = 'TEST first report only has parallel readings.'
        record['language_versions'][3].update(text=None, scope='source_context', quotation_status='content_mismatch')
        record['language_versions'][2].update(scope='source_excerpt', quotation_status='abbreviated_source_report')
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        program = READER_SNAPSHOT_JS + '''const records=JSON.parse(require('fs').readFileSync(0,'utf8')),names={};
const valueText = ''' + helpers + '''
process.stdout.write(JSON.stringify({views:languageReadings(records[0]),languages:availableLanguageCodes(records[0]),
key:primarySearchKey(records[0]),notes:annotationSearchKey(records[0])}));'''
        run = subprocess.run([shutil.which('node'), '-e', program], input=json.dumps([record]),
                             text=True, capture_output=True, check=True)
        actual = json.loads(run.stdout)
        self.assertEqual(actual['views'], language_readings(record))
        own = next(item for item in actual['views'] if item['language'] == 'en')
        self.assertIsNone(own['text'])
        self.assertIn('narration boundary', own['qualification'])
        self.assertIn('EN-24', own['citation'])
        self.assertNotIn('en', actual['languages'])
        self.assertNotIn('comment-only-en', actual['key'])
        self.assertIn('comment-only-en', actual['notes'])
        self.assertIn('separate source spans', actual['views'][0]['qualification'])
        self.assertIn('TEST source word differs.', actual['views'][0]['qualification'])
        self.assertIn('two separately attributed reports', next(item for item in actual['views'] if item['language'] == 'uz-Cyrl')['qualification'])
        self.assertIn('TEST first report only', next(item for item in actual['views'] if item['language'] == 'uz-Cyrl')['qualification'])
        self.assertIn('not a translation or Arabic counterpart', next(item for item in actual['views'] if item['language'] == 'ur-Latn')['qualification'])
        self.assertIn('exact abbreviated wording', next(item for item in actual['views'] if item['language'] == 'hi')['qualification'])

    @unittest.skipUnless(shutil.which('node'), 'Node is required for DOM construction regression')
    def test_language_panel_dom_owns_sources_notes_and_open_controls(self):
        """Exercise DOM construction, not a substitute for a browser layout test."""
        record, translator_names = multilingual_translator_fixture()
        record['language_versions'][1]['source']['detail_metadata_status'] = 'detail_metadata_pending'
        record['language_versions'][1]['references'].append({'collection': None, 'number': None,
            'source_citation': 'TEST raw-only citation <script>preserve as text</script>',
            'scope': 'source_supplied_citation', 'numbering_system': 'publisher_source_local',
            'canonical_mapping_status': 'not_inferred',
            'url': record['language_versions'][1]['source']['record_url']})
        template = (Path(reader.__file__).resolve().parents[1] / 'reader/template.html').read_text()
        helpers = template.split('const valueText =', 1)[1].split('function fillFilter(', 1)[0]
        constructors = 'function detail(' + template.split('function detail(', 1)[1].split('function sourceFiles(', 1)[0]
        panels = 'function citationList(' + template.split('function citationList(', 1)[1].split('function card(', 1)[0]
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
const completedReading=languageReadings(records[0]).find(reading=>reading.language==='en');
const completed=languageReading({...completedReading,source:{...completedReading.source,detail_metadata_status:'detail_metadata_source_parsed'}},8,1);
const roman=sections.find(node=>node.dataset.language==='ur-Latn'),wasClosed=!roman.open;
const romanButton=all.find(node=>node.tag==='button' && node.textContent==='Roman Urdu');romanButton.events.click();
process.stdout.write(JSON.stringify({count:sections.length,arabicOpen:sections.find(node=>node.dataset.language==='ar').open,
 englishOpen:english.open,notesClosed:!englishNodes.find(node=>node.className==='detail reading-notes').open,
 referencesClosed:!englishNodes.find(node=>node.className==='detail reading-references').open,
 pendingNotice:englishNodes.find(node=>node.className==='counterpart-note reading-pending')?.textContent,
 completedNotice:nodes(completed).some(node=>node.className==='counterpart-note reading-pending'),
 referenceText:englishNodes.filter(node=>['citation-verbatim','citation-scope'].includes(node.className)).map(node=>node.textContent),
 translators:Object.fromEntries(sections.map(section=>[section.dataset.language,
   nodes(section).find(node=>node.className==='reading-reference').children
     .filter(node=>node.className==='reading-translator').map(node=>node.textContent)])),
 hindiText:nodes(sections.find(node=>node.dataset.language==='hi')).map(node=>node.textContent || '').join(' '),
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
        self.assertTrue(actual['referencesClosed'])
        self.assertEqual(actual['pendingNotice'], 'Detailed source references and notes have not been retrieved yet.')
        self.assertFalse(actual['completedNotice'])
        self.assertIn(record['language_versions'][1]['references'][1]['source_citation'], actual['referenceText'])
        self.assertIn('Numbering: publisher source local', actual['referenceText'])
        self.assertIn('Canonical mapping: not inferred', actual['referenceText'])
        self.assertEqual(actual['translators'], {language: [' · Translator: ' + name] if name else []
                                                for language, name in translator_names.items()})
        self.assertNotIn('TEST raw-only citation', actual['hindiText'])
        self.assertEqual(sum(link['href'] == record['language_versions'][1]['source']['record_url']
                             for link in actual['englishLinks']), 1)
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
