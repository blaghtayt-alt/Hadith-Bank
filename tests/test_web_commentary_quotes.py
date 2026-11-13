"""Commentary boundaries, source bindings, and metadata isolation regression tests."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from web_commentary_quotes import CommentaryQuotes, SCHEMA, FOLDER, canonical_hash, sha
from language_versions import validate_language_versions, quotation_parts, language_search_values

class CommentaryQuoteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.folder=self.root/FOLDER;self.folder.mkdir(parents=True)
        self.file=self.folder/'commentary-quotations-test.json'
        raw=b'TEST original HTML'
        self.snapshot=self.root/'snapshot.html.gz';self.snapshot.write_bytes(gzip.compress(raw,mtime=0))
        self.text='TEST context | TEST first quote | TEST explanation | TEST second quote | TEST end'
        self.parent={'id':'islom:TEST:1','language':'uz','source_language_code':'uz-Cyrl','book_key':'TEST',
            'edition':'TEST-source-edition','source':{'publisher':'TEST publisher','title':'TEST source book',
            'url':'https://example.org/TEST','record_url':'https://example.org/TEST/1'},
            'source_locator':{'path':'snapshot.html.gz','sha256':sha(raw),'record_url':'https://example.org/TEST/1'},
            'text':{'arabic':'UNRELATED PARENT ARABIC','translation':'UNRELATED PARENT POINTER164'},
            'number':{'canonical':'164','in_book':'177'},'narrator':{'name':'TEST PARENT NARRATOR'},
            'references':{'items':[{'number':'164'}]},'grading':{'grade':'TEST PARENT GRADE','grader':'TEST GRADER'},
            'language_versions':[{'id':'islom:TEST:1:uz-Cyrl','language':'uz-Cyrl','script':'Cyrl',
            'text':'UNRELATED PARENT POINTER164','comments':[{'text':self.text}],
            'translation_provenance':{'ai_translation':'unknown'}}],
            'rights':{'status':'not_assessed_for_publication'},'ai_translation':'unknown',
            'translation_provenance':{'origin':'unknown'}}
        child='islom:TEST:1:commentary-report-1'
        spans=[]
        for phrase in ['TEST first quote','TEST second quote']:
            start=self.text.index(phrase)
            spans.append({'start':start,'end':start+len(phrase),'text':phrase,'sha256':sha(phrase.encode()),
                'report_type':'prophetic_report_excerpt','speaker':'TEST explicitly named speaker',
                'component_id':'report-1','source_report_family_id':child})
        external=self.folder/'external-test.json';external.write_bytes(b'TEST external evidence')
        self.spec={'proposed_occurrence_id':child,'supplement_id':child,'parent_occurrence_id':self.parent['id'],
            'decision':'register','registered_source_occurrences':1,'independent_pro_qc':'not_performed',
            'certified_release_eligible':False,'parent_baseline_record_sha256':canonical_hash(self.parent),
            'source_snapshot':{**self.parent['source_locator'],'stored_sha256':sha(self.snapshot.read_bytes())},
            'source_record_url':'https://example.org/TEST/1',
            'source_field_path':['language_versions',0,'comments',0,'text'],
            'source_version_id':'islom:TEST:1:uz-Cyrl','language':'uz-Cyrl',
            'source_field_sha256':sha(self.text.encode()),'full_field_chars_reviewed':len(self.text),
            'full_field_bytes_reviewed':len(self.text.encode()),'selected_spans':spans,
            'quoted_passages':2,'source_report_families':1,'description':'TEST independent commentary report; parent pointer is unrelated.',
            'external_corroboration':[{'path':external.relative_to(self.root).as_posix(),
                'sha256':sha(external.read_bytes()),'url':'https://example.org/EXTERNAL',
                'work':'TEST external work no867','relationship':'TEST corroboration only; no source grade/number transfer.'}]}
        self.doc={'schema':SCHEMA,'site':'islom','enabled':True,'records':[self.spec]}
        self.save()

    def save(self):self.file.write_text(json.dumps(self.doc))

    def test_child_boundaries_preserve_context_and_do_not_inherit_parent_metadata(self):
        before=copy.deepcopy(self.parent)
        adapter=CommentaryQuotes(self.root,'islom')
        child,=adapter.children(self.parent);adapter.finish()
        self.assertEqual(self.parent,before)
        self.assertEqual(child['id'],self.spec['proposed_occurrence_id'])
        self.assertIsNone(child['number']['canonical']);self.assertIsNone(child['number']['in_book'])
        self.assertIsNone(child['number']['source_entry_id']);self.assertIsNone(child['narrator']['name'])
        self.assertIsNone(child['grading']['grade']);self.assertIsNone(child['grading']['grader'])
        self.assertIsNone(child['text']['arabic']);self.assertEqual(child['references']['items'],[])
        version=child['language_versions'][0];validate_language_versions([version])
        blocks=quotation_parts(version)
        self.assertEqual(len(blocks),1)
        self.assertEqual([p['text'] for p in blocks[0]['passages']],['TEST first quote','TEST second quote'])
        self.assertTrue(blocks[0]['passages'][1]['gap_before'])
        search=str(list(language_search_values(child)))
        self.assertNotIn('UNRELATED PARENT',search);self.assertNotIn('TEST explanation',search)
        self.assertNotIn('TEST external work',search)
        self.assertIn('TEST external work',str(list(language_search_values(child,include_comments=True))))
        pieces=[(s['start'],s['text']) for s in self.spec['selected_spans']]
        pieces += [(c['source_span'][0],c['text']) for c in version['comments'] if 'source_span' in c]
        self.assertEqual(''.join(t for _,t in sorted(pieces)),self.text)

    def test_changed_parent_or_field_or_span_or_snapshot_fails_closed(self):
        changed=copy.deepcopy(self.parent);changed['language_versions'][0]['comments'][0]['text']+=' altered'
        with self.assertRaisesRegex(ValueError,'parent baseline changed'):
            CommentaryQuotes(self.root,'islom').children(changed)
        initial=copy.deepcopy(self.spec)
        for change,pattern in [('source_field_sha256','comment field checksum'),('span','child span checksum'),
                               ('coverage','complete comment review')]:
            self.spec.clear();self.spec.update(copy.deepcopy(initial))
            if change=='span':self.spec['selected_spans'][0]['sha256']='0'*64
            elif change=='coverage':self.spec['full_field_chars_reviewed']-=1
            else:self.spec[change]='0'*64
            self.save()
            with self.assertRaisesRegex(ValueError,pattern):CommentaryQuotes(self.root,'islom').children(self.parent)
        self.spec.clear();self.spec.update(initial);self.save()
        self.snapshot.write_bytes(gzip.compress(b'CHANGED source',mtime=0))
        with self.assertRaisesRegex(ValueError,'evidence checksum'):
            CommentaryQuotes(self.root,'islom').children(self.parent)

    def test_inherited_reference_and_unsafe_external_dependency_fail_closed(self):
        self.spec['source_printed_collection_references']=[{'number':'164','scope':'source_entry'}];self.save()
        with self.assertRaisesRegex(ValueError,'unbound or inherited source reference'):
            CommentaryQuotes(self.root,'islom').children(self.parent)
        self.spec.pop('source_printed_collection_references')
        self.spec['external_corroboration'][0]['path']='../elsewhere';self.save()
        with self.assertRaisesRegex(ValueError,'unsafe local evidence path'):
            CommentaryQuotes(self.root,'islom').children(self.parent)

    def test_missing_parent_duplicate_identity_and_implicit_enable_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'parents absent'):
            CommentaryQuotes(self.root,'islom').finish()
        self.doc['records'].append(copy.deepcopy(self.spec));self.save()
        with self.assertRaisesRegex(ValueError,'duplicate commentary child identity'):
            CommentaryQuotes(self.root,'islom')
        self.doc['records'].pop();self.doc.pop('enabled');self.save()
        with self.assertRaisesRegex(ValueError,'explicit enabled'):
            CommentaryQuotes(self.root,'islom')

if __name__=='__main__':unittest.main()
