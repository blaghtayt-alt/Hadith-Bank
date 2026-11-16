"""Portable Hindi source uncertainty real-caller regression.

Uses exact pinned 14 source-detail records bundled in tests/fixtures;
never reads private workspaces or substitutes stubbed production modules.
"""
from pathlib import Path
from html.parser import HTMLParser
from unittest.mock import patch
from collections import Counter
import copy
import hashlib
import json
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT
sys.path.insert(0,str(CODE/'scripts'))
from source_uncertainty_notes import (AUTHORITY_SHA256, WARNING, _approved_authority,
    validated_parts, exact_quotation, exact_source_reconstruction, source_parts_html,
    checked_source_identity, quotation_fragments)
from material_registry import normalized_projection
from build_reader import validate_record, markdown_record, reader_ui_assets
from language_display import language_readings
from build_discovery import render_language_reading
from bank_discovery import expected_discovery_row, build_discovery_payload, expected_discovery_segments, tokenize

RECORDS=json.loads((ROOT/'tests/fixtures/software_rebase/hindi-fourteen.json').read_text(encoding='utf-8'))
APPROVED=json.loads((CODE/'scripts/source_uncertainty_authority.json').read_text(encoding='utf-8'))
SHA=lambda x: hashlib.sha256(x).hexdigest()


def raw_row(record):
    row={key:copy.deepcopy(record[key]) for key in [
        'id','language','book_key','edition','source','number','review',
        'translation_provenance','translator','narrator','page','commentary',
        'references','grading','rights','extraction','topic_tags','editorial_tags',
        'source_headings','ai_translation','title','source_uncertainty_projection'
    ] if key in record}
    row['text']={'arabic':record.get('text_arabic'),'translation':record.get('text_translation')}
    row['source']['source_text_record_id']=record['source_uncertainty_projection']['text_record_id']
    return row


def material(record):
    return {'dataset_id':'private-software-test','language':'hi','book_key':'bukhari',
            'edition':record['edition'],'canonical_records_path':'materials/private-test.json',
            'source_file':'sources/private-test.pdf','source_sha256':'0'*64,
            'source_descriptor':{'name':'Private tested Hindi source bound','format':'pdf'},
            'publication':{'visibility':'private','status':'not_published','authorized':False}}


class HTMLParts(HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.notes=0;self.notes_outside=True;self.words=[]
    def handle_starttag(self,tag,attrs):
        classes=(dict(attrs).get('class') or '').split()
        if 'source-uncertainty' in classes:
            self.notes+=1
            if any('quotation' in parent or 'source-quote' in parent for parent in self.stack):self.notes_outside=False
        self.stack.append(classes)
    def handle_endtag(self,tag):
        if self.stack:self.stack.pop()
    def handle_data(self,data):
        if any('source-quote' in parent for parent in self.stack):self.words.append(data)


class SoftwareRepairRealRoutes(unittest.TestCase):
    def test_closed_authority_exact_bindings_and_statuses(self):
        self.assertEqual(SHA((CODE/'scripts/source_uncertainty_authority.json').read_bytes()),AUTHORITY_SHA256)
        self.assertEqual(APPROVED['closed_application_sha256'],'546ec5472082407e31467487fbeae4346b6041da18cd10d8e61d5a8ca69c43d0')
        self.assertEqual(len(RECORDS),len(APPROVED['bindings']))
        statuses=Counter()
        for record in RECORDS:
            binding=APPROVED['bindings'][record['id']]
            self.assertEqual(binding['body_sha256'],SHA(record['text_translation'].encode()))
            self.assertEqual(binding['text_record_id'],record['number']['source_entry_id'])
            self.assertEqual(binding['text_record_id'],record['source']['original_metadata']['source_text_record_id'])
            self.assertEqual(binding['annotations'],sorted(record['source_uncertainty_projection']['annotations'],key=lambda a:(a['start'],a['end'])))
            for a in binding['annotations']:statuses[a['kind']]+=1
        self.assertEqual(dict(statuses),{'accepted_uncertain_reading':15,'unfilled_source_gap':1,'unreviewed_source_gap':2})
        self.assertEqual(WARNING,'(OCR wasn’t clear)')

    def test_all_14_real_normalizer_registry_language_static_markdown_preview(self):
        for index,record in enumerate(RECORDS):
            with self.subTest(record=record['id']):
                row=raw_row(record)
                projected=normalized_projection(row,material(record),index)
                self.assertEqual(projected['text_translation'],record['text_translation'])
                self.assertEqual(projected['source_uncertainty_projection'],record['source_uncertainty_projection'])
                self.assertEqual(projected['review']['release_eligible'],False)
                validate_record(record,record['id'])
                readings=language_readings(record)
                self.assertEqual(len(readings),1)
                parts=readings[0]['source_uncertainty_parts']
                self.assertEqual(exact_source_reconstruction(parts),record['text_translation'])
                self.assertEqual(sum(x['kind']=='note' for x in parts),len(record['source_uncertainty_projection']['annotations']))
                if any(part['kind']=='gap' for part in parts):
                    with self.assertRaisesRegex(ValueError,'incomplete source quotation'):exact_quotation(parts)
                else:
                    self.assertEqual(exact_quotation(parts),record['text_translation'])
                static=render_language_reading(readings[0],record)
                markdown=markdown_record(record,index+1)
                for markup in (static,markdown):
                    parsed=HTMLParts();parsed.feed(markup)
                    self.assertEqual(parsed.notes,len(record['source_uncertainty_projection']['annotations']))
                    self.assertTrue(parsed.notes_outside)
                    self.assertEqual(markup.count(WARNING),len(record['source_uncertainty_projection']['annotations']))
                    self.assertNotIn('⟦',markup)
                    self.assertNotIn('<br>',markup.split('<div class="source-reading"',1)[1].split('</div>',1)[0])
                preview=expected_discovery_row(record,index)['readings'][0]
                self.assertNotIn('⟦',preview['text'])
                self.assertNotIn('OCR',preview['text'])
                self.assertEqual(preview['sourceUncertainty'],True)
                self.assertEqual(len(expected_discovery_segments(record)),len(quotation_fragments(parts)))

    def test_high_severity_mutations_fail_all_real_callers(self):
        base=next(record for record in RECORDS if record['id']=='HI-MSB-V1-P0374-N0434')
        mutations={}
        r=copy.deepcopy(base)
        held=next(a for a in r['source_uncertainty_projection']['annotations'] if a['kind']=='unreviewed_source_gap')
        held['kind']='unfilled_source_gap'  # original high HOLD, body/hash unchanged
        mutations['promoted_U014']=r
        r=copy.deepcopy(base)
        r['text_translation']='X'+r['text_translation'][1:]
        r['source_uncertainty_projection']['expected_body_sha256']=SHA(r['text_translation'].encode())
        mutations['self_rehashed_body']=r
        r=copy.deepcopy(base)
        r['source_uncertainty_projection']['text_record_id']='unrelated-text-record-999'
        mutations['wrong_projection_text_id']=r
        r=copy.deepcopy(base);r['number']['source_entry_id']='unrelated-text-record-999'
        mutations['wrong_number_text_id']=r
        r=copy.deepcopy(base);r['source']['original_metadata']['source_text_record_id']='unrelated-text-record-999'
        mutations['wrong_source_text_id']=r
        r=copy.deepcopy(base);r['id']='unrelated-parent-id'
        r['source_uncertainty_projection']['record_id']='unrelated-parent-id'
        mutations['wrong_parent_id']=r
        r=copy.deepcopy(base);r['source_uncertainty_projection']['annotations'][0]['issue_id']='invented-authority'
        mutations['new_issue_status_id']=r
        r=copy.deepcopy(base);r['source_uncertainty_projection']['annotations'].pop()
        mutations['dropped_hold']=r
        r=copy.deepcopy(base);r['source_uncertainty_projection']['annotations'][0]['start']+=1
        r['source_uncertainty_projection']['annotations'][0]['span_sha256']=SHA(r['text_translation'][r['source_uncertainty_projection']['annotations'][0]['start']:r['source_uncertainty_projection']['annotations'][0]['end']].encode())
        mutations['self_rehashed_offset']=r
        for title,r in mutations.items():
            with self.subTest(attack=title):
                with self.assertRaises(ValueError):validate_record(r,r['id'])
                with self.assertRaises(ValueError):language_readings(r)
                with self.assertRaises(ValueError):markdown_record(r,1)
                with self.assertRaises(ValueError):expected_discovery_row(r,0)
                raw=raw_row(r)
                with self.assertRaises(ValueError):normalized_projection(raw,material(r),0)

    def test_0106_U007_and_0149_gap_unchanged(self):
        for suffix,expected in [('N0839',{'unreviewed_source_gap':1}),('N1675',{'unfilled_source_gap':1})]:
            r=next(r for r in RECORDS if r['id'].endswith(suffix))
            counts=Counter(a['kind'] for a in r['source_uncertainty_projection']['annotations'])
            for kind,n in expected.items():self.assertEqual(counts[kind],n)
            parts=language_readings(r)[0]['source_uncertainty_parts']
            self.assertEqual(sum(x['kind']=='gap' for x in parts),1)
            with self.assertRaisesRegex(ValueError,'incomplete'):exact_quotation(parts)

    def test_discovery_postings_and_visible_fragment_phrase_boundaries(self):
        snapshot={'record_count':len(RECORDS),'records_sha256':'a'*64}
        payload=build_discovery_payload(RECORDS,snapshot)
        self.assertEqual(len(payload['rows']),14)
        for row in payload['rows']:
            for preview in row['readings']:
                self.assertNotIn('⟦',preview['text'])
                self.assertNotIn(WARNING,preview['text'])
        self.assertFalse(any('u014' in term or 'u007' in term for term in payload['terms']))
        for r in RECORDS:
            row=payload['rows'][next(i for i,x in enumerate(RECORDS) if x['id']==r['id'])]
            self.assertEqual(row['searchSegments'],expected_discovery_segments(r))
        # Synthetic quote parts only, NOT an unauthorized new source projection.
        from source_uncertainty_notes import quotation_fragments
        parts=[{'kind':'quotation','source_text':'ab'}, {'kind':'gap','source_text':'⟦GAP⟧'},
               {'kind':'note','text':WARNING}, {'kind':'quotation','source_text':'cd'}]
        self.assertEqual(quotation_fragments(parts),['ab','cd'])
        with self.assertRaisesRegex(ValueError,'incomplete'):exact_quotation(parts)

    def test_bad_or_missing_trust_anchor_rejected(self):
        r=RECORDS[0]
        _approved_authority.cache_clear()
        try:
            with patch.object(Path,'read_bytes',side_effect=FileNotFoundError('trust map missing')):
                with self.assertRaisesRegex(ValueError,'quotation withheld'):
                    validated_parts(r['text_translation'],r['source_uncertainty_projection'],record_id=r['id'])
        finally:
            _approved_authority.cache_clear()
        self.assertTrue(validated_parts(r['text_translation'],r['source_uncertainty_projection'],record_id=r['id']))

    def test_legacy_no_opt_in_projector_byte_parity_to_pinned_current_main(self):
        legacy=[copy.deepcopy(r) for r in RECORDS[:4]]
        for row in legacy:row.pop('source_uncertainty_projection')
        data=''.join(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n' for row in legacy)
        cmd=['node',str(CODE/'scripts/reader_projection.js'),str(CODE/'reader/template.html')]
        result=subprocess.run(cmd,input=data.encode('utf-8'),capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
        self.assertEqual(SHA(result.stdout),
            'c4c25b9750b6624c57cca9d0934c0263df7dc8bd49d789c1b12f43f5af339632')
        self.assertEqual(SHA((CODE/'scripts/source_glyphs.py').read_bytes()),
            '384e5e70dadeaab91e73d1b4dcc62501b44b788dad6bef15c53f3b7d378570a6')

    def test_production_css_exists_with_source_notes_and_glyphs_preserved(self):
        style,icons=reader_ui_assets(CODE/'reader')
        self.assertIn('.source-reading .source-uncertainty',style)
        self.assertIn('.source-copy-quotation:disabled',style)
        self.assertGreater(len(icons),12000)
        css=CODE/'reader/reading-room.css'
        # Previous current main CSS is an exact prefix. Hindi CSS is append-only.
        self.assertEqual(SHA(css.read_bytes()[:46030]),
            '71a360316e9fe753f4daa3238c0cb16a5ff94e0fd8d9250a3da5f2706ddb191b')

if __name__=='__main__':unittest.main(verbosity=2)
