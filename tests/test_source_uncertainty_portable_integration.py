"""Portable source-bound uncertainty source-part tests. No external/private paths.

Uses exact pinned 14-record fixture, not a source review or release gate.
"""
import copy
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=ROOT
sys.path.insert(0,str(CANDIDATE/'scripts'))
from source_uncertainty_notes import (digest,validated_parts,exact_quotation,
                                      exact_source_reconstruction,source_parts_html)
RECORDS=json.loads((ROOT/'tests/fixtures/software_rebase/hindi-fourteen.json').read_text())

class Structure(HTMLParser):
    def __init__(self):
        super().__init__();self.stack=[];self.notes=[];self.quote=[];self.gaps=[]
    def handle_starttag(self,tag,attrs):
        attr=dict(attrs);klass=(attr.get('class') or '').split()
        if 'source-uncertainty' in klass:
            self.notes.append(not any(t in ('q','blockquote') or 'quotation' in c for t,c in self.stack))
        if tag not in ('br','img','hr','input','meta','link'):
            self.stack.append((tag,klass))
    def handle_endtag(self,tag):
        if tag in ('br',):return
        if self.stack:self.stack.pop()
    def handle_data(self,data):
        if any('quotation' in c for t,c in self.stack):self.quote.append(data)
        if any('source-gap' in c for t,c in self.stack):self.gaps.append(data)

class TestSourceUncertainty(unittest.TestCase):
    def validate(self,r,**kwargs):
        return validated_parts(r['text_translation'],r['source_uncertainty_projection'],record_id=r['id'],**kwargs)
    def test_every_14_exact_source_reconstruction_and_exact_18_notes(self):
        all_parts=[self.validate(r,expected_body_sha256=r['source_uncertainty_projection']['expected_body_sha256']) for r in RECORDS]
        assert len(RECORDS)==14
        assert sum(sum(p['kind']=='note' for p in parts) for parts in all_parts)==18
        assert sum(sum(p['review_status']=='unreviewed' for p in parts if p['kind']=='note') for parts in all_parts)==2
        assert sum(sum(p['kind']=='gap' for p in parts) for parts in all_parts)==3
        for r,parts in zip(RECORDS,all_parts):
            with self.subTest(record=r['id']):
                self.assertEqual(exact_source_reconstruction(parts),r['text_translation'])
                self.assertEqual(digest(r['text_translation']),r['source_uncertainty_projection']['expected_body_sha256'])
                if any(part['kind']=='gap' for part in parts):
                    self.assertRaisesRegex(ValueError,'incomplete source quotation',exact_quotation,parts)
                else:
                    self.assertEqual(exact_quotation(parts),r['text_translation'])
                markup=source_parts_html(parts,language='hi',line_breaks=True)
                parser=Structure();parser.feed(markup)
                self.assertTrue(all(parser.notes))
                self.assertNotIn('⟦', ''.join(parser.quote))
                self.assertEqual(len(parser.notes),len(r['source_uncertainty_projection']['annotations']))
    def test_triple_and_single_cases_frozen(self):
        byid={r['id']:r for r in RECORDS}
        cases=[('HI-MSB-V1-P0374-N0434',3,1),('HI-MSB-V2-P0090-N0839',1,1),('HI-MSB-V3-P0188-N1675',0,1)]
        for name,approved,gaps in cases:
            r=byid[name];parts=self.validate(r)
            self.assertEqual(sum(p['kind']=='quotation' and 'issue_id' in p for p in parts),approved)
            self.assertEqual(sum(p['kind']=='gap' for p in parts),gaps)
            self.assertRaisesRegex(ValueError,'incomplete source quotation',exact_quotation,parts)
    def test_source_body_digest_must_be_externally_bound(self):
        r=copy.deepcopy(RECORDS[0]);self.assertRaises(ValueError,self.validate,r,expected_body_sha256='0'*64)
        r['text_translation']+='x';self.assertRaises(ValueError,self.validate,r)
        r=copy.deepcopy(RECORDS[0]);r['source_uncertainty_projection']['expected_body_sha256']=digest('unauthorized')
        self.assertRaises(ValueError,self.validate,r)
    def test_span_mutations_fail_closed(self):
        r=RECORDS[0]
        for change in ({'start':True},{'end':False},{'start':-1},{'end':0},
                       {'span_sha256':'0'*64},{'kind':'invented'},
                       {'start':100000},{'issue_id':''}):
            x=copy.deepcopy(r);x['source_uncertainty_projection']['annotations'][0].update(change)
            with self.subTest(change=change):self.assertRaises(ValueError,self.validate,x)
        x=copy.deepcopy(r);x['source_uncertainty_projection']['annotations'].append(copy.deepcopy(x['source_uncertainty_projection']['annotations'][0]))
        self.assertRaises(ValueError,self.validate,x)
    def test_overlap_and_unannotated_marker_fail_closed(self):
        r=next(r for r in RECORDS if r['id'].endswith('N0434'))
        x=copy.deepcopy(r)
        a=x['source_uncertainty_projection']['annotations'][0]
        x['source_uncertainty_projection']['annotations'][1]['start']=a['start']
        self.assertRaises(ValueError,self.validate,x)
        x=copy.deepcopy(r);x['source_uncertainty_projection']['annotations']=[note for note in x['source_uncertainty_projection']['annotations'] if not note['kind'].endswith('source_gap')]
        self.assertRaises(ValueError,self.validate,x)
    def test_source_bound_record_id_glyph_combo_and_schema(self):
        x=copy.deepcopy(RECORDS[0]);x['source_uncertainty_projection']['record_id']='other'
        self.assertRaises(ValueError,self.validate,x)
        self.assertRaises(ValueError,self.validate,RECORDS[0],glyphs=[{'mock':'glyph'}])
        x=copy.deepcopy(RECORDS[0]);x['source_uncertainty_projection']['nonsense']=True
        self.assertRaises(ValueError,self.validate,x)
    def test_escape_safety_and_unapproved_synthetic_body_fail_closed(self):
        value='आ😀<script> & नभ'
        a={'issue_id':'QC" onload="alert(1)', 'start':2,'end':11,
           'kind':'accepted_uncertain_reading','span_sha256':digest(''.join(list(value)[2:11]))}
        p={'schema':'source_uncertainty_projection.v1','record_id':'s1','text_record_id':'s1-HI',
           'field':'text.translation','expected_body_sha256':digest(value),'annotations':[a]}
        self.assertRaises(ValueError,validated_parts,value,p,record_id='s1')
        rendered=source_parts_html([{'kind':'quotation','start':0,'end':len(value),
                                    'source_text':value}],language='hi" onclick="alert(1)',line_breaks=True)
        self.assertNotIn('<script>',rendered)
        self.assertNotIn(' onclick="',rendered)
        self.assertIn('आ😀',rendered)

    def test_unreviewed_not_approved_and_0149_gap(self):
        r=next(r for r in RECORDS if r['id'].endswith('N1675'))
        parts=self.validate(r)
        self.assertEqual(sum(p['kind']=='gap' for p in parts),1)
        self.assertEqual(sum(p.get('review_status')=='unreviewed' for p in parts),0)
        self.assertIn('[Source gap: exact reading unavailable]',source_parts_html(parts,language='hi'))
        self.assertRaisesRegex(ValueError,'incomplete source quotation',exact_quotation,parts)
    def test_legacy_without_opt_in_unchanged(self):
        legacy=copy.deepcopy(RECORDS[0]);legacy.pop('source_uncertainty_projection')
        self.assertEqual(legacy['text_translation'],RECORDS[0]['text_translation'])
        self.assertNotIn('source_uncertainty_projection',legacy)

if __name__=='__main__':unittest.main(verbosity=2)
