"""Portable actual-route Hindi source uncertainty checks, without mock modules.

Hashes of ordinary no-opt-in output are measured against pinned current main,
not a fixed private path. Source decisions and hold states are immutable inputs.
"""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from language_display import language_readings
from build_reader import validate_record, markdown_record
from build_discovery import render_language_reading
from bank_discovery import expected_discovery_row

FIX=ROOT/'tests/fixtures/software_rebase'
RECORDS=json.loads((FIX/'hindi-fourteen.json').read_text(encoding='utf-8'))
EXPECTED=json.loads((FIX/'legacy-main-output-hashes.json').read_text(encoding='utf-8'))['route_hashes']
sha=lambda value:hashlib.sha256(value.encode('utf-8')).hexdigest()

class SourceHTML(HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.words=[];self.notes=[]
    def handle_starttag(self,tag,attrs):
        classes=(dict(attrs).get('class') or '').split()
        if 'source-uncertainty' in classes:
            self.notes.append(not any('quotation' in parent or 'source-quote' in parent for parent in self.stack))
        if tag not in ('br','meta','input','link','img','hr'):self.stack.append(classes)
    def handle_endtag(self,tag):
        if tag not in ('br','meta','input','link','img','hr') and self.stack:self.stack.pop()
    def handle_data(self,data):
        if any('source-quote' in parent for parent in self.stack):self.words.append(data)

class TestPortableProductionRoutes(unittest.TestCase):
    def test_actual_exact14_validator_and_source_identity(self):
        self.assertEqual(len(RECORDS),14)
        for r in RECORDS:
            with self.subTest(r=r['id']):self.assertIsNone(validate_record(r,r['id']))

    def test_exact14_language_versions_one_bound_primary(self):
        for r in RECORDS:
            views=language_readings(r)
            bound=[v for v in views if 'source_uncertainty_parts' in v]
            with self.subTest(r=r['id']):
                self.assertEqual(len(bound),1)
                self.assertTrue(bound[0]['primary'])
                self.assertEqual(bound[0]['language'],'hi')
                self.assertEqual(bound[0]['text'],r['text_translation'])

    def test_real_static_pages_keep_notes_outside_quote(self):
        for r in RECORDS:
            view=next(v for v in language_readings(r) if 'source_uncertainty_parts' in v)
            markup=render_language_reading(view,r)
            parser=SourceHTML();parser.feed(markup)
            with self.subTest(r=r['id']):
                self.assertTrue(all(parser.notes))
                self.assertEqual(len(parser.notes),len(r['source_uncertainty_projection']['annotations']))
                self.assertNotIn('⟦',markup)
                self.assertIn('class="source-reading"',markup)

    def test_real_markdown_keeps_notes_outside_quote(self):
        for i,r in enumerate(RECORDS,1):
            markup=markdown_record(r,i)
            parser=SourceHTML();parser.feed(markup)
            with self.subTest(r=r['id']):
                self.assertTrue(all(parser.notes))
                self.assertEqual(len(parser.notes),len(r['source_uncertainty_projection']['annotations']))
                self.assertNotIn('⟦',markup)
                self.assertIn('(OCR wasn’t clear)',markup)
                self.assertIn('class="source-reading"',markup)

    def test_compact_preview_no_internal_marker_and_scope_flag(self):
        for i,r in enumerate(RECORDS):
            row=expected_discovery_row(r,i)
            with self.subTest(r=r['id']):
                self.assertTrue(row.get('sourceUncertainty'))
                hi=next(p for p in row['readings'] if p['language']=='hi')
                self.assertTrue(hi.get('sourceUncertainty'))
                self.assertNotIn('⟦',hi['text']);self.assertNotIn('(OCR wasn’t clear)',hi['text'])

    def test_legacy_language_versions_match_pinned_main(self):
        for r in RECORDS:
            x=copy.deepcopy(r);x.pop('source_uncertainty_projection')
            values=language_readings(x)
            actual=sha(json.dumps(values,sort_keys=True,ensure_ascii=False,separators=(',',':')))
            with self.subTest(r=r['id']):self.assertEqual(actual,EXPECTED[x['id']]['language_readings'])

    def test_legacy_markdown_matches_pinned_main(self):
        for i,r in enumerate(RECORDS,1):
            x=copy.deepcopy(r);x.pop('source_uncertainty_projection')
            with self.subTest(r=r['id']):self.assertEqual(sha(markdown_record(x,i)),EXPECTED[x['id']]['markdown'])

    def test_legacy_static_matches_pinned_main(self):
        for r in RECORDS:
            x=copy.deepcopy(r);x.pop('source_uncertainty_projection')
            view=language_readings(x)[0]
            with self.subTest(r=r['id']):self.assertEqual(sha(render_language_reading(view,x)),EXPECTED[x['id']]['static'])

    def test_mutated_body_digest_fails_actual_routes(self):
        r=copy.deepcopy(RECORDS[0]);r['source_uncertainty_projection']['expected_body_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'quotation withheld'):validate_record(r,r['id'])
        with self.assertRaisesRegex(ValueError,'quotation withheld'):language_readings(r)
        with self.assertRaisesRegex(ValueError,'quotation withheld'):markdown_record(r,1)
        with self.assertRaisesRegex(ValueError,'quotation withheld'):expected_discovery_row(r,0)

    def test_explicit_0149_gap_still_unsupplied(self):
        r=next(r for r in RECORDS if r['id'].endswith('N1675'))
        html=render_language_reading(language_readings(r)[0],r)
        self.assertIn('[Source gap: exact reading unavailable]',html)
        self.assertNotIn('⟦',html)

if __name__=='__main__':unittest.main(verbosity=2)
