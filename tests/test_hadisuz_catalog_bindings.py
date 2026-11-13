"""Source-bound catalogue ancestry tests using the exact saved seed and /3 HTML."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_hadisuz as importer

FIXTURE = Path(__file__).resolve().parent / 'fixtures/hadisuz-saved-catalog-pages.json'
CHAPTER = importer.ORIGIN + '/hadiths/3'
TOPIC = importer.ORIGIN + '/hadiths/4'


def synthetic(title, children='', panel_title=None, outside=''):
    label = title if panel_title is None else panel_title
    return ('<h1>' + title + '</h1><div class="col-md-9">'
            '<a href="/hadith/615">TEST detail</a></div>'
            '<div class="col-md-3"><div class="panel">'
            '<h3 class="panel-title">Манбалар</h3><div class="panel-body">' + label + '</div>'
            '<ul class="list-group">' + children + '</ul></div></div>' + outside).encode()


class HadisuzCatalogBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        guard = mock.patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('No HTTP permitted'))
        guard.start()
        self.addCleanup(guard.stop)
        self.pages = {page['url']: page for page in json.loads(FIXTURE.read_text())['pages']}
        self.worker = importer.Importer(self.root, max_pages=1, max_seconds=30, delay=0)

    def raw(self, url):
        page = self.pages[url]
        raw = page['raw_html'].encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), page['source_snapshot']['sha256'])
        return raw

    def save_source(self, url, raw):
        snapshot = self.worker.preserve(raw, url, {'retrieved_at': 'TEST saved time',
            'status': 200, 'final_url': url, 'content_type': 'text/html; charset=utf-8'})
        self.worker.state['snapshots'][url] = snapshot
        return snapshot

    def process(self, url, raw):
        snapshot = self.save_source(url, raw)
        self.worker.enqueue(url, 'catalog', 'TEST observed parent')
        task = next(task for task in self.worker.state['tasks'] if task['url'] == url)
        self.worker.process(task, raw, snapshot)
        return task, snapshot

    def seed(self):
        return self.process(importer.CATALOG, self.raw(importer.CATALOG))

    def chapter(self):
        self.seed()
        return self.process(CHAPTER, self.raw(CHAPTER))

    def test_actual_seed_binds_exact_seven_labels_and_actual_chapter_binds_111_children(self):
        seed_task, seed_snapshot = self.seed()
        self.assertEqual(len(self.worker.catalog_bindings), 8)
        for path, label in importer.CATALOG_TITLES.items():
            if path == '/hadiths/1':
                continue
            binding = self.worker.catalog_bindings[importer.ORIGIN + path]
            self.assertEqual(binding['label'], label)
            self.assertEqual(binding['parent_url'], importer.CATALOG)
            self.assertEqual(binding['parent_snapshot_sha256'], seed_snapshot['sha256'])
            self.assertEqual(binding['href_as_parsed'], importer.ORIGIN + path)
        task, snapshot = self.process(CHAPTER, self.raw(CHAPTER))
        self.assertEqual(task['discovery']['title'], 'Таҳорат боблари')
        self.assertEqual(len(task['discovery']['catalog_links']), 111)
        self.assertEqual(len(self.worker.catalog_bindings), 119)
        self.assertEqual(task['discovery']['next'], [CHAPTER + '?page=2'])
        binding = self.worker.catalog_bindings[TOPIC]
        self.assertEqual(binding['label'], 'Таҳоратсиз намоз қабул эмас')
        self.assertEqual(binding['parent_url'], CHAPTER)
        self.assertEqual(binding['parent_snapshot_sha256'], snapshot['sha256'])
        self.assertEqual(binding['parent_snapshot_path'], snapshot['path'])
        self.assertTrue(importer.allowed_url(TOPIC + '?page=2', 'catalog', self.worker.catalog_bindings))
        self.assertFalse(importer.allowed_url(TOPIC + '?page=2', 'catalog'))
        self.worker.validate_catalog_bindings()
        self.assertEqual(self.worker.requests, 0)

    def test_resume_revalidates_all_bindings_without_changing_source_bytes_or_objects(self):
        self.chapter()
        self.worker.state['entries'] = {'TEST original source': {'unchanged': True}}
        self.worker.save()
        before = copy.deepcopy(self.worker.state)
        stored = {item['path']: (self.root / item['path']).read_bytes()
                  for item in self.worker.state['snapshots'].values()}
        resumed = importer.Importer(self.root, max_pages=1, max_seconds=30, delay=0)
        self.assertEqual(resumed.state, before)
        self.assertEqual(resumed.requests, 0)
        for path, raw in stored.items():
            self.assertEqual((self.root / path).read_bytes(), raw)
        self.assertEqual(resumed.fetch(CHAPTER)[0], self.raw(CHAPTER))

    def test_legacy_checkpoint_bootstraps_from_saved_seed_and_preserves_failure_history(self):
        seed = self.save_source(importer.CATALOG, self.raw(importer.CATALOG))
        chapter = self.save_source(CHAPTER, self.raw(CHAPTER))
        self.worker.state['tasks'][0]['status'] = 'done'
        failed = {'url': CHAPTER, 'kind': 'catalog', 'status': 'failed', 'attempts': 3,
                  'discovered_on': importer.CATALOG, 'error': 'TEST prior title parser guard'}
        self.worker.state['tasks'].append(copy.deepcopy(failed))
        self.worker.state['events'].append({'url': CHAPTER, 'error': failed['error'], 'actual_requests': 1})
        self.worker.state['entries'] = {'TEST original source': {'unchanged': True}}
        self.worker.state.pop('catalog_bindings')
        self.worker.state.pop('catalog_bindings_schema')
        history = copy.deepcopy(self.worker.state['events'])
        self.worker.save()
        resumed = importer.Importer(self.root, max_pages=1, max_seconds=30, delay=0)
        self.assertEqual(len(resumed.catalog_bindings), 8)
        task = next(task for task in resumed.state['tasks'] if task['url'] == CHAPTER)
        self.assertEqual(task, failed)
        resumed.process(task, self.raw(CHAPTER), chapter)
        self.assertEqual(task['status'], 'done')
        self.assertEqual(task['attempts'], 3)
        self.assertEqual(resumed.state['events'], history)
        self.assertEqual(resumed.state['entries'], {'TEST original source': {'unchanged': True}})
        self.assertEqual(resumed.state['snapshots'][importer.CATALOG], seed)
        self.assertEqual(resumed.state['snapshots'][CHAPTER], chapter)
        self.assertEqual(len(resumed.catalog_bindings), 119)
        self.assertEqual(resumed.requests, 0)

    def test_unknown_route_requires_an_actual_link_in_a_validated_parent_panel(self):
        route = importer.ORIGIN + '/hadiths/2'
        self.seed()
        self.worker.enqueue(route, 'catalog', CHAPTER)
        self.assertFalse(any(task['url'] == route for task in self.worker.state['tasks']))
        with self.assertRaisesRegex(ValueError, 'outside authorized public routes'):
            self.worker.fetch(route)
        raw = synthetic('Таҳорат боблари', '<a href="/hadiths/2">TEST explicitly observed topic</a>')
        self.process(CHAPTER, raw)
        self.assertEqual(self.worker.catalog_bindings[route]['label'], 'TEST explicitly observed topic')
        self.assertTrue(importer.allowed_url(route, 'catalog', self.worker.catalog_bindings))
        self.assertTrue(any(task['url'] == route for task in self.worker.state['tasks']))
        self.worker.validate_catalog_bindings([route + '?page=1'])

    def test_wrong_target_title_is_retained_but_cannot_discover_children(self):
        self.seed()
        before = copy.deepcopy(self.worker.catalog_bindings)
        raw = synthetic('TEST wrong title', '<a href="/hadiths/2">TEST child</a>')
        snapshot = self.save_source(CHAPTER, raw)
        task = next(task for task in self.worker.state['tasks'] if task['url'] == CHAPTER)
        with self.assertRaisesRegex(ValueError, 'observed parent-link label'):
            self.worker.process(task, raw, snapshot)
        self.assertEqual(self.worker.catalog_bindings, before)
        self.assertEqual(self.worker.checked(snapshot), raw)

    def test_known_chapter_titles_match_own_parent_labels_and_root_keeps_original_guard(self):
        self.seed()
        for path, label in importer.CATALOG_TITLES.items():
            with self.subTest(path=path):
                parsed = importer.parse_catalog(synthetic(label), importer.ORIGIN + path, self.worker.catalog_bindings)
                self.assertEqual(parsed['title'], label)
        with self.assertRaisesRegex(ValueError, 'authorized Tirmidhi collection'):
            importer.parse_catalog(synthetic('TEST other collection'), importer.CATALOG, self.worker.catalog_bindings)
        with self.assertRaisesRegex(ValueError, 'observed parent-link label'):
            importer.parse_catalog(synthetic('Сунани Термизий'), CHAPTER, self.worker.catalog_bindings)

    def test_generic_footer_and_mismatched_sidebar_do_not_bind_other_routes(self):
        self.seed()
        raw = synthetic('Таҳорат боблари', '<a href="/hadiths/2">TEST unrelated</a>',
                        panel_title='TEST different source',
                        outside='<footer>Сунани Термизий <a href="/hadiths/45">TEST outside link</a></footer>')
        task, _ = self.process(CHAPTER, raw)
        self.assertEqual(task['discovery']['chapters'], [])
        self.assertEqual(len(self.worker.catalog_bindings), 8)

    def test_changed_parent_hash_and_corrupt_parent_bytes_fail_before_resume_or_request(self):
        self.chapter()
        original = copy.deepcopy(self.worker.catalog_bindings)
        self.worker.catalog_bindings[TOPIC]['parent_snapshot_sha256'] = '0' * 64
        self.worker.save()
        with self.assertRaisesRegex(ValueError, 'parent snapshot binding mismatch'):
            importer.Importer(self.root, max_pages=1, max_seconds=30, delay=0)
        with self.assertRaisesRegex(ValueError, 'parent snapshot binding mismatch'):
            self.worker.fetch(TOPIC)
        self.worker.state['catalog_bindings'] = original
        self.worker.save()
        parent_path = self.root / self.worker.state['snapshots'][CHAPTER]['path']
        parent_path.write_bytes(b'TEST changed saved parent bytes')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            importer.Importer(self.root, max_pages=1, max_seconds=30, delay=0)

    def test_forged_unobserved_route_binding_cannot_authorize_fetch_or_resume(self):
        self.chapter()
        route = importer.ORIGIN + '/hadiths/2'
        forged = copy.deepcopy(self.worker.catalog_bindings[TOPIC])
        forged.update(url=route, href_as_parsed=route, label='TEST invented route', label_source_text='TEST invented route')
        self.worker.catalog_bindings[route] = forged
        with self.assertRaisesRegex(ValueError, 'exact validated parent link'):
            self.worker.fetch(route)
        self.worker.save()
        with self.assertRaisesRegex(ValueError, 'exact validated parent link'):
            importer.Importer(self.root, max_pages=1, max_seconds=30, delay=0)

    def test_cycles_unbound_ancestors_and_query_registry_keys_are_rejected(self):
        self.chapter()
        original = copy.deepcopy(self.worker.catalog_bindings)
        self.worker.catalog_bindings[CHAPTER]['parent_url'] = TOPIC
        with self.assertRaisesRegex(ValueError, 'Cyclic catalogue binding'):
            self.worker.validate_catalog_bindings()
        self.worker.state['catalog_bindings'] = copy.deepcopy(original)
        self.worker.catalog_bindings[TOPIC]['parent_url'] = importer.ORIGIN + '/hadiths/2'
        with self.assertRaisesRegex(ValueError, 'Unbound or invalid catalogue ancestor'):
            self.worker.validate_catalog_bindings()
        self.worker.state['catalog_bindings'] = copy.deepcopy(original)
        self.worker.catalog_bindings[TOPIC + '?page=1'] = copy.deepcopy(original[TOPIC])
        with self.assertRaisesRegex(ValueError, 'Invalid catalogue binding registry key'):
            self.worker.validate_catalog_bindings()

    def test_existing_label_cannot_be_overwritten_or_reparented(self):
        task, snapshot = self.chapter()
        before = copy.deepcopy(self.worker.catalog_bindings)
        link = copy.deepcopy(task['discovery']['catalog_links'][0])
        self.assertEqual(link['url'], TOPIC)
        link['label'] = 'TEST changed existing label'
        with self.assertRaisesRegex(ValueError, 'cannot be overwritten'):
            self.worker.register_catalog_links(CHAPTER, self.raw(CHAPTER), snapshot, [link])
        self.assertEqual(self.worker.catalog_bindings, before)
        self.worker.process(task, self.raw(CHAPTER), snapshot)
        self.assertEqual(self.worker.catalog_bindings, before)

    def test_parent_evidence_is_required_and_registration_update_is_atomic(self):
        self.seed()
        raw = synthetic('Таҳорат боблари', '<a href="/hadiths/2">TEST observed topic</a>')
        snapshot = self.save_source(CHAPTER, raw)
        parsed = importer.parse_catalog(raw, CHAPTER, self.worker.catalog_bindings)
        before = copy.deepcopy(self.worker.catalog_bindings)
        wrong = dict(snapshot, sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'exact saved parent HTML'):
            self.worker.register_catalog_links(CHAPTER, raw, wrong, parsed['catalog_links'])
        self.assertEqual(self.worker.catalog_bindings, before)
        forged = dict(parsed['catalog_links'][0], url=importer.ORIGIN + '/hadiths/999')
        with self.assertRaisesRegex(ValueError, 'exact validated parent link'):
            self.worker.register_catalog_links(CHAPTER, raw, snapshot, parsed['catalog_links'] + [forged])
        self.assertEqual(self.worker.catalog_bindings, before)


if __name__ == '__main__':
    unittest.main()
