#!/usr/bin/env python3
"""Independent engineering audit of the patch08 logical cumulative package.

This script does not import or execute build_patch08.py, assign semantic roles,
inspect image content, award manual review credit, publish, or alter the input
candidate. Its output directory must be separate from the candidate/evidence.
"""
from __future__ import annotations
import argparse
import bisect
import collections
import csv
import datetime
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

VERSION = 'v2_cp017_patch08'
AUTH_SHA = '9de6f653de73a932a46a555e30bfe3817cf2fd9bfa22b4f0ded5158f12c01d85'
SEM = 'continuation/integration/semantic_interval_decisions.jsonl'
STATUS = 'continuation/integration/semantic_current_status_index.jsonl'
ATOMS = 'continuation/integration/current_source_semantic_segments.jsonl'
UNITS = 'data/all_source_units_annotated.jsonl'
CR = 'continuation/integration/character_reviews.jsonl'
CG = 'continuation/integration/character_regions.jsonl'
UNC = 'continuation/integration/semantic_uncertainties.jsonl'
EP = 'continuation/patch08/'


def same_json(a, b):
    """JSON-value equality that also distinguishes booleans/integers/floats."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same_json(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same_json(x, y) for x, y in zip(a, b))
    return a == b


class Audit:
    def __init__(self, args):
        self.a = args
        self.P = args.parent.resolve()
        self.S = args.stage.resolve()
        self.E = args.evidence_root.resolve()
        self.O = args.out.resolve()
        self.checks = {}
        self.metrics = {}
        self.notes = []
        self.inputs = {}
        self.digest_cache = {}
        self.references = set()
        self.reference_stats = collections.Counter()
        self.O.mkdir(parents=True, exist_ok=True)
        self.manifest = self.readj(args.manifest)
        self.index = {r['path'].split('/', 1)[1]: r for r in self.readj(self.E/'PARENT_ARCHIVE_MEMBER_INDEX.json')}
        self.use(Path(__file__))

    def check(self, name, ok, detail=None):
        c = self.checks.setdefault(name, {'evaluations': 0, 'failures': 0, 'examples': []})
        c['evaluations'] += 1
        if not ok:
            c['failures'] += 1
            if len(c['examples']) < 12:
                c['examples'].append(detail)
        return ok

    def digest(self, p):
        p = Path(p).resolve()
        st = p.stat()
        key = (str(p), st.st_size, st.st_mtime_ns)
        if key not in self.digest_cache:
            with p.open('rb') as f:
                self.digest_cache[key] = hashlib.file_digest(f, 'sha256').hexdigest()
        return self.digest_cache[key]

    def use(self, p):
        p = Path(p).resolve()
        st = p.stat()
        row = {'path': str(p), 'bytes': st.st_size, 'sha256': self.digest(p)}
        self.inputs.setdefault(str(p), row)
        if p.is_relative_to(self.P):
            rel = p.relative_to(self.P).as_posix()
            expected = self.index.get(rel) if hasattr(self, 'index') else None
            if expected:
                self.check('authenticated_parent_input_bytes', row['bytes'] == expected['bytes'] and row['sha256'] == expected['sha256'], rel)
        return p

    def resolve(self, rel):
        rel = str(rel)
        if Path(rel).is_absolute():
            return Path(rel)
        p = self.S/rel
        if p.is_file():
            return p
        if rel.startswith(EP):
            p = self.E/rel[len(EP):]
            if p.is_file():
                return p
        if rel.startswith('patches/patch08/'):
            return self.E/rel[len('patches/patch08/'):]
        return self.P/rel

    def readj(self, p):
        return json.loads(self.use(p).read_bytes())

    def readjl(self, p):
        with self.use(p).open('r', encoding='utf8', newline='') as f:
            return [json.loads(line) for line in f if line.strip()]

    def currentj(self, rel):
        return self.readj(self.resolve(rel))

    def currentjl(self, rel):
        return self.readjl(self.resolve(rel))

    def emit(self, label):
        fails = sum(c['failures'] for c in self.checks.values())
        print(json.dumps({'completed': label, 'check_categories': len(self.checks), 'violations': fails}), flush=True)

    def source_text(self, v, story, lo, hi):
        s = self.stories[(v, story)]
        if not (s['cp_start'] <= lo <= hi <= s['cp_end']):
            raise ValueError((v, story, lo, hi, s['cp_start'], s['cp_end']))
        return s['_utf16'][(lo-s['cp_start'])*2:(hi-s['cp_start'])*2].decode('utf-16-le')

    def span(self, r, v=None, label='exact_global_CP_span'):
        try:
            v = r.get('source_volume', v)
            text = self.source_text(v, r['story'], r['cp_start'], r['cp_end'])
            return self.check(label, text == r['text_verbatim'], {'id': r.get('decision_id', r.get('region_id')), 'volume': v, 'story': r['story'], 'cp_start': r['cp_start'], 'cp_end': r['cp_end']})
        except (KeyError, ValueError, UnicodeError) as e:
            return self.check(label, False, {'id': r.get('decision_id'), 'error': str(e)[:250]})

    def prefix(self, rel):
        p, q = self.use(self.P/rel), self.use(self.resolve(rel))
        with p.open('rb') as a, q.open('rb') as b:
            ok = True
            while part := a.read(4*1024*1024):
                if part != b.read(len(part)):
                    ok = False
                    break
        self.check('exact_parent_byte_prefix', ok, rel)

    def normal(self, x):
        if isinstance(x, str):
            for prefix in (str(self.E)+'/', 'patches/patch08/'):
                if x.startswith(prefix):
                    return EP+x[len(prefix):]
            if x.startswith(str(self.P)+'/'):
                return x[len(str(self.P))+1:]
            return x
        if isinstance(x, list):
            return [self.normal(v) for v in x]
        if isinstance(x, dict):
            return {k: self.normal(v) for k, v in x.items()}
        return x

    def manifest_check(self, ending=False):
        for r in self.manifest['files']:
            p = self.S/r['path']
            exists = p.is_file()
            self.check('candidate_binding_end' if ending else 'candidate_binding_start', exists and p.stat().st_size == r['bytes'] and self.digest(p) == r['sha256'], r['path'])
            if exists:
                self.use(p)
        self.check('manifest_parent_identity', self.manifest['parent_checkpoint_sha256'] == AUTH_SHA)

    def sources(self):
        auth = self.readj(self.E/'PARENT_AUTHENTICATION.json')
        self.check('parent_authentication_record', auth['archive_sha256'] == AUTH_SHA and auth['archive_members'] == len(self.index) == 18626 and auth['status'] == 'pass')
        self.stories = {}
        for v in (1, 2):
            rel = f'source_exports/v{v:02d}/doc_all_stories.json'
            p, q = self.P/rel, self.resolve(rel)
            self.check('source_story_exports_unchanged', self.digest(p) == self.digest(q), rel)
            content = self.readj(q)
            for story, r in content.items():
                raw = r['text'].encode('utf-16-le')
                self.check('source_story_global_utf16_bounds', len(raw)//2 == r['cp_end']-r['cp_start'], [v, story])
                self.stories[(v, story)] = {**r, '_utf16': raw}
                rel2 = f'all_source_text/v{v:02d}_{story}_raw.txt'
                p2, q2 = self.use(self.P/rel2), self.use(self.resolve(rel2))
                self.check('all_raw_story_bytes_and_controls_preserved', p2.read_bytes() == q2.read_bytes() == r['text'].encode('utf8'), [v, story])
        for inp in self.currentj('metadata.json')['inputs']:
            rel = 'originals/'+inp['filename']
            p = self.use(self.resolve(rel))
            self.check('original_DOC_PDF_input_hashes', p.stat().st_size == inp['bytes'] and self.digest(p) == inp['sha256'] == self.index[rel]['sha256'], rel)
        self.metrics['source_stories'] = len(self.stories)
        self.metrics['source_utf16_units_including_controls'] = sum(len(v['_utf16'])//2 for v in self.stories.values())
        self.emit('original sources and global CP bases')

    def export_check(self, rows, rel):
        csv.field_size_limit(1 << 30)
        with self.use(self.resolve(rel)).open('r', encoding='utf8', newline='') as f:
            reader = csv.DictReader(f)
            fields = list(dict.fromkeys(k for r in rows for k in r))
            self.check('CSV_exact_field_union', reader.fieldnames == fields, rel)
            count = 0
            for n, (expect, got) in enumerate(itertools.zip_longest(rows, reader), 1):
                count += 1
                if not self.check('CSV_row_count_and_order', expect is not None and got is not None, [rel, n]):
                    continue
                for k in fields:
                    if k not in expect:
                        correct = got[k] == ''
                    else:
                        v = expect[k]
                        if isinstance(v, (dict, list)):
                            try:
                                correct = same_json(json.loads(got[k]), v)
                            except (json.JSONDecodeError, TypeError):
                                correct = False
                        else:
                            text = 'null' if v is None else ('true' if v else 'false') if isinstance(v, bool) else str(v)
                            correct = got[k] == text
                    self.check('CSV_lossless_typed_values', correct, [rel, n, k])
            self.metrics[rel+'_rows'] = count

    def records_units(self):
        self.parent_records = self.readjl(self.P/'records.jsonl')
        self.records = self.currentjl('records.jsonl')
        self.check('record_count_and_ID_order', len(self.records) == len(self.parent_records) == 2029 and [r['record_id'] for r in self.records] == [r['record_id'] for r in self.parent_records])
        self.check('primary_record_ID_uniqueness', len({r['record_id'] for r in self.records}) == len(self.records))
        old_fields = 0
        for old, new in zip(self.parent_records, self.records):
            for k, v in old.items():
                if k != 'data_version':
                    old_fields += 1
                    self.check('every_old_record_field_preserved', k in new and same_json(new[k], v), [old['record_id'], k])
            self.check('record_current_data_version', new['data_version'] == VERSION, new['record_id'])
            self.check('record_new_annotation_safety', new['continuation_patch08']['source_text_changed'] is False and new['continuation_patch08']['pure_matn_verification_inferred'] is False, new['record_id'])
        self.check('records_JSON_JSONL_equivalence', same_json(self.currentj('records.json'), self.records))
        self.export_check(self.records, 'records.csv')
        self.metrics.update({'records': len(self.records), 'old_record_fields_compared': old_fields})
        self.parent_units = self.readjl(self.P/UNITS)
        self.units = self.currentjl(UNITS)
        self.check('source_unit_ID_sequence', len(self.units) == len(self.parent_units) == 11484 and [r['paragraph_id'] for r in self.units] == [r['paragraph_id'] for r in self.parent_units])
        self.unit_by_id = {r['paragraph_id']: r for r in self.units}
        self.check('source_unit_ID_uniqueness', len(self.unit_by_id) == len(self.units))
        story_units = collections.defaultdict(list)
        for old, new in zip(self.parent_units, self.units):
            for k, v in old.items():
                self.check('every_old_source_unit_field_preserved', k in new and same_json(new[k], v), [old['paragraph_id'], k])
            self.span({**new, 'text_verbatim': new['raw_text']}, label='source_unit_exact_GLOBAL_CP')
            story_units[(new['source_volume'], new['story'])].append(new)
        for key, story in self.stories.items():
            items = story_units[key]
            cursor = story['cp_start']
            for r in items:
                self.check('source_units_complete_ordered_story_partition', r['cp_start'] == cursor and r['cp_end'] >= cursor, [key, r['paragraph_id'], cursor])
                cursor = r['cp_end']
            self.check('source_units_complete_ordered_story_partition', cursor == story['cp_end'], [key, cursor, story['cp_end']])
            self.check('source_units_reconstruct_entire_story_including_controls', ''.join(r['raw_text'] for r in items) == story['text'], key)
        self.metrics['source_units'] = len(self.units)
        self.emit('all source units and records; JSON/JSONL/CSV')

    def semantics(self):
        self.parent_sem = self.readjl(self.P/SEM)
        self.parent_status = self.readjl(self.P/STATUS)
        self.sem = self.currentjl(SEM)
        self.status = self.currentjl(STATUS)
        self.new_sem = self.currentjl(EP+'integration/new_semantic_decisions.jsonl')
        self.sem_sha = self.digest(self.resolve(SEM))
        self.parent_sem_sha = self.digest(self.P/SEM)
        self.prefix(SEM)
        self.check('new_semantics_exact_suffix', self.sem[len(self.parent_sem):] == self.new_sem)
        self.check('semantic_status_row_count', len(self.sem) == len(self.status))
        self.active = {}
        pids = collections.defaultdict(list)
        cids = collections.defaultdict(list)
        for n, r in enumerate(self.parent_sem, 1):
            pids[r['decision_id']].append(n)
        for n, (r, st) in enumerate(zip(self.sem, self.status), 1):
            cids[r['decision_id']].append(n)
            self.span(r, label='cumulative_semantics_exact_GLOBAL_CP')
            self.check('semantic_status_SHA_ordinal_ID', st['ledger_sha256'] == self.sem_sha and st['ledger_1_based_row'] == n and st['decision_id'] == r['decision_id'], n)
            if st['current_interpretation_active']:
                self.active[n] = r
            if n <= len(self.parent_status) and not self.parent_status[n-1]['current_interpretation_active']:
                self.check('historically_inactive_never_reactivated', st['current_interpretation_active'] is False, [n, r['decision_id']])
        dup_old = {k: v for k, v in pids.items() if len(v) > 1}
        dup_new = {k: v for k, v in cids.items() if len(v) > 1}
        self.check('only_eight_inherited_duplicate_ID_groups', len(dup_old) == 8 and dup_new == dup_old, dup_new)
        self.check('new_semantic_IDs_unique_and_disjoint', len({r['decision_id'] for r in self.new_sem}) == len(self.new_sem) and not (set(pids) & {r['decision_id'] for r in self.new_sem}))
        for r in self.new_sem:
            for k in ('canonical_identity', 'canonical_number', 'verified_grade'):
                self.check('no_canonical_identity_or_grade_invented', r.get(k) is None, [r['decision_id'], k])
            for k in ('source_text_changed', 'source_wording_modified', 'canonical_identity_inferred', 'verified_grade_inferred', 'pure_matn_verified'):
                self.check('no_new_source_rewrite_or_verification_promotion', r.get(k, False) is False, [r['decision_id'], k])
        audit = self.currentj(EP+'integration/semantic_identifier_audit.json')
        self.check('current_duplicate_audit_exact', audit['ledger_sha256'] == self.sem_sha and audit['inherited_duplicate_id_groups'] == dup_new and audit['new_duplicate_id_groups'] == 0)
        overlays = self.currentjl(EP+'integration/semantic_correction_overlay.jsonl')
        self.check('reference_parent_replacement_count', len(overlays) == 207)
        byid = {r['decision_id']: r for r in self.new_sem}
        for o in overlays:
            n = o['parent_ledger_1_based_row']
            old = self.parent_sem[n-1]
            self.check('reference_overlay_parent_SHA_ordinal', o['parent_ledger_sha256'] == self.parent_sem_sha and old['decision_id'] == o['parent_decision_id'] and self.parent_status[n-1]['current_interpretation_active'], o['overlay_id'])
            replacements = [byid[k] for k in o['replacement_decision_ids']]
            ordered = sorted(replacements, key=lambda r: (r['cp_start'], r['cp_end']))
            cursor = old['cp_start']
            for r in ordered:
                self.check('reference_replacement_complete_exact_partition', r['source_volume'] == old['source_volume'] and r['story'] == old['story'] and r['cp_start'] == cursor and r['cp_end'] > cursor, [o['overlay_id'], r['decision_id']])
                cursor = r['cp_end']
            self.check('reference_replacement_complete_exact_partition', cursor == old['cp_end'] and ''.join(r['text_verbatim'] for r in ordered) == old['text_verbatim'], o['overlay_id'])
            self.check('reference_parent_inactive_replacements_active', n not in self.active and all(cids[r['decision_id']][0] in self.active for r in replacements), o['overlay_id'])
        newly_inactive = [n for n, st in enumerate(self.parent_status, 1) if st['current_interpretation_active'] and n not in self.active]
        self.check('only_explicit_reference_parent_deactivations', sorted(newly_inactive) == sorted(o['parent_ledger_1_based_row'] for o in overlays), newly_inactive)
        qc = self.currentjl(EP+'integration/independent_QC_semantic_correction_overlay.jsonl')
        self.check('independent_QC_refinement_overlays_present', len(qc) >= 2)
        before_hashes = {}
        for o in qc:
            count = o['before_ledger_row_count']
            if count not in before_hashes:
                h = hashlib.sha256()
                with self.use(self.resolve(SEM)).open('rb') as f:
                    for n, line in enumerate(f, 1):
                        if n > count:
                            break
                        h.update(line)
                before_hashes[count] = h.hexdigest()
            n = o['before_ledger_1_based_row']
            before = self.sem[n-1]
            self.check('QC_overlay_exact_before_SHA_ordinal_and_row', o['before_ledger_sha256'] == before_hashes[count] and same_json(o['before_decision'], before), o['overlay_id'])
            replacements = [byid[k] for k in o['replacement_decision_ids']]
            cursor = before['cp_start']
            for r in sorted(replacements, key=lambda x: x['cp_start']):
                self.check('QC_refinement_complete_exact_partition', r['source_volume'] == before['source_volume'] and r['story'] == before['story'] and r['cp_start'] == cursor and r['cp_end'] > cursor, [o['overlay_id'], r['decision_id']])
                cursor = r['cp_end']
            self.check('QC_refinement_complete_exact_partition', cursor == before['cp_end'] and ''.join(r['text_verbatim'] for r in sorted(replacements, key=lambda x: x['cp_start'])) == before['text_verbatim'], o['overlay_id'])
            self.check('QC_original_retained_inactive_replacements_active', n not in self.active and self.status[n-1]['superseded_by_patch08_decision_ids'] == o['replacement_decision_ids'] and all(cids[r['decision_id']][0] in self.active for r in replacements), o['overlay_id'])
            self.check('QC_refinement_no_source_change_or_page_credit', o['old_row_retained_historically'] is True and o['source_text_changed'] is False and o['source_codepoints_changed'] == o['new_character_credit'] == 0, o['overlay_id'])
        self.check('only_explicit_new_row_deactivations', {n for n in range(len(self.parent_sem)+1, len(self.sem)+1) if n not in self.active} == {r['before_ledger_1_based_row'] for r in qc})
        branches = collections.defaultdict(list)
        for r in self.new_sem:
            branches[r['patch08_source_branch']].append(r)
        for name, integrated in branches.items():
            raw = self.normal(self.readjl(self.E/name/'semantic_decisions.jsonl'))
            self.check('all_author_decisions_retained_in_branch_order', [r['decision_id'] for r in raw] == [r['decision_id'] for r in integrated], name)
            for before, after in zip(raw, integrated):
                for k, v in before.items():
                    self.check('every_raw_author_semantic_field_preserved', k in after and same_json(after[k], v), [before['decision_id'], k])
        ledger_rows_by_hash = {self.parent_sem_sha: self.parent_sem, self.sem_sha: self.sem}
        for count, digest in before_hashes.items():
            ledger_rows_by_hash[digest] = self.sem[:count]
        historical_parent_regions = {r['region_id']: r for r in self.readjl(self.P/CG)}

        def nested_evidence(obj, v=None, story=None, owner=None):
            if isinstance(obj, list):
                for q in obj:
                    nested_evidence(q, v, story, owner)
            elif isinstance(obj, dict):
                v = obj.get('source_volume', v)
                story = obj.get('story', story)
                if all(k in obj for k in ('cp_start', 'cp_end', 'text_verbatim')) and v and story:
                    self.span({**obj, 'story': story}, v, 'new_semantic_nested_source_evidence_exact')
                if all(k in obj for k in ('ledger_sha256', 'ledger_1_based_row', 'decision_id')):
                    rows = ledger_rows_by_hash.get(obj['ledger_sha256'])
                    if rows is None:
                        matches = [self.P/r for r, m in self.index.items() if m['sha256'] == obj['ledger_sha256'] and r.endswith('.jsonl')]
                        if matches:
                            rows = self.readjl(matches[0])
                            ledger_rows_by_hash[obj['ledger_sha256']] = rows
                    n = obj['ledger_1_based_row']
                    self.check('new_semantic_evidence_qualified_historical_refs_resolve', rows is not None and 1 <= n <= len(rows) and rows[n-1].get('decision_id') == obj['decision_id'], [owner, obj])
                if 'source_story_utf8_sha256' in obj and v and story:
                    expected = hashlib.sha256(self.stories[v, story]['text'].encode('utf8')).hexdigest()
                    self.check('new_semantic_source_story_hash_exact', obj['source_story_utf8_sha256'] == expected, owner)
                for ident in obj.get('inherited_character_region_ids', []):
                    self.check('new_semantic_inherited_region_ID_exists', ident in historical_parent_regions, [owner, ident])
                for ref in obj.get('prior_character_regions', []):
                    if isinstance(ref, dict) and 'region_id' in ref:
                        old = historical_parent_regions.get(ref['region_id'])
                        self.check('new_semantic_prior_character_reference_resolves', old is not None and old['source_volume'] == v and old['pdf_page'] == ref['pdf_page'], [owner, ref])
                        if old and 'overlap_cp' in ref:
                            lo, hi = ref['overlap_cp']
                            self.check('new_semantic_prior_character_overlap_is_real', any(sp['story'] == story and sp['cp_start'] <= lo < hi <= sp['cp_end'] for sp in old.get('source_spans', [])), [owner, ref])
                for q in obj.values():
                    nested_evidence(q, v, story, owner)
        for r in self.new_sem:
            nested_evidence(r, owner=r['decision_id'])
        self.metrics['independent_QC_semantic_refinements'] = {'superseded_rows_retained': len(qc), 'exact_replacement_rows': sum(len(x['replacement_decision_ids']) for x in qc)}
        self.metrics.update({'parent_semantic_rows': len(self.parent_sem), 'new_semantic_rows': len(self.new_sem), 'cumulative_semantic_rows': len(self.sem), 'active_semantic_rows': len(self.active), 'unique_semantic_IDs': len(cids), 'inherited_duplicate_ID_groups': len(dup_new), 'reference_parents_replaced': len(overlays)})
        self.emit('semantic prefix, status authority, exact CP, replacements and identities')

    def characters(self):
        oldreviews, oldregions = self.readjl(self.P/CR), self.readjl(self.P/CG)
        self.reviews, self.regions = self.currentjl(CR), self.currentjl(CG)
        self.review_by_id = {r['review_id']: r for r in self.reviews}
        self.region_by_id = {r['region_id']: r for r in self.regions}
        self.check('unique_character_review_and_region_IDs', len(self.review_by_id) == len(self.reviews) and len(self.region_by_id) == len(self.regions))
        corrections = []
        for kind, oldrows, nowrows, rel, hashkey in [('review', oldreviews, self.review_by_id, 'character_review_corrections.jsonl', 'parent_review_ledger_sha256'), ('region', oldregions, self.region_by_id, 'character_region_corrections.jsonl', 'parent_region_ledger_sha256')]:
            corr = self.normal(self.readjl(self.E/'partial_review'/rel))
            corrections.extend(corr)
            byid = {r[kind+'_id']: r for r in corr}
            expected_hash = self.digest(self.P/(CR if kind == 'review' else CG))
            for old in oldrows:
                ident = old[kind+'_id']
                expected = old
                if ident in byid:
                    c = byid[ident]
                    self.check('character_before_state_and_ledger_exact', same_json(c['before_'+kind], old) and c[hashkey] == expected_hash, ident)
                    expected = c['after_'+kind]
                self.check('character_parent_row_preserved_or_explicitly_corrected', ident in nowrows, ident)
                if ident in nowrows:
                    for k, v in expected.items():
                        self.check('character_after_state_matches_exact_evidence', k in nowrows[ident] and same_json(nowrows[ident][k], v), [ident, k])
            tail = self.normal(self.readjl(self.E/'tail_review'/('character_reviews.jsonl' if kind == 'review' else 'character_regions.jsonl')))
            self.check('character_only_explicit_additions', set(nowrows) == {r[kind+'_id'] for r in oldrows+tail}, kind)
            for r in tail:
                for k, v in r.items():
                    self.check('tail_character_evidence_exact', k in nowrows[r[kind+'_id']] and same_json(nowrows[r[kind+'_id']][k], v), [r[kind+'_id'], k])
        self.pages = self.currentjl('data/page_coverage.jsonl')
        self.export_check(self.pages, 'page_coverage.csv')
        oldpages = {(r['source_volume'], r['pdf_page']): r for r in self.readjl(self.P/'data/page_coverage.jsonl')}
        current = {(r['source_volume'], r['pdf_page']): r for r in self.reviews}
        expected = {(v, p) for v, total in [(1, 1023), (2, 1031)] for p in range(1, total+1)}
        self.check('current_character_one_review_per_original_page', set(current) == expected and len(current) == len(self.reviews) == 2054)
        full = {k for k, r in current.items() if r['full_visible_character_review_complete'] is True}
        self.check('current_character_partition_exact', len(full) == 2053 and expected-full == {(1, 962)})
        for r in self.pages:
            k = r['source_volume'], r['pdf_page']
            self.check('page_matrix_current_review_and_completion', r['current_character_review_id'] == current[k]['review_id'] and r['full_visible_character_review_complete'] == current[k]['full_visible_character_review_complete'] and r['full_character_diacritic_reading_order_review_complete'] == current[k]['full_visible_character_review_complete'], k)
        for r in self.reviews:
            ids = [x['region_id'] for x in self.regions if x['review_id'] == r['review_id']]
            self.check('review_region_membership_exact', set(ids) == set(r['region_ids']) and len(r['region_ids']) == len(set(r['region_ids'])), r['review_id'])
            for ident in ids:
                q = self.region_by_id[ident]
                self.check('region_page_identity_matches_review', (q['source_volume'], q['pdf_page']) == (r['source_volume'], r['pdf_page']), ident)
        for r in self.regions:
            for sp in r.get('source_spans', []):
                if all(k in sp for k in ('story', 'cp_start', 'cp_end', 'text_verbatim')):
                    self.span(sp, r['source_volume'], 'all_character_region_exact_GLOBAL_CP')
        tail = self.normal(self.readjl(self.E/'tail_review/character_reviews.jsonl'))
        newcredit = {(r['source_volume'], r['pdf_page']) for r in tail if r.get('new_page_attempt_credit') == 1}
        legacy = {(r['source_volume'], r['pdf_page']) for r in tail if r.get('new_page_attempt_credit') == 0}
        self.check('tail_no_false_page_credit', newcredit == {(2, p) for p in range(1022, 1032)} and legacy == {(1, 8), (2, 1), (2, 2)})
        self.check('tail_legacy_preexisting_full_flags', all(oldpages[k]['full_visible_character_review_complete'] is True for k in legacy))
        oldfull = {k for k, r in oldpages.items() if r['full_visible_character_review_complete'] is True}
        upgrades = full-oldfull-newcredit
        self.check('thirteen_inherited_partial_upgrades', len(upgrades) == 13 and not oldfull-full, sorted(upgrades))
        self.metrics.update({'detailed_character_reviews': len(self.reviews), 'character_regions': len(self.regions), 'full_character_pages': len(full), 'partial_character_pages': [list(x) for x in sorted(expected-full)], 'new_page_attempts': len(newcredit), 'legacy_detailed_rechecks': len(legacy), 'partial_to_full_upgrades': len(upgrades)})
        self.current_character = current
        normalization = self.currentjl(EP+'integration/current_language_presence.jsonl')
        norm_by_page = {(r['source_volume'], r['pdf_page']): r for r in normalization}
        self.check('language_normalization_one_row_per_page', len(normalization) == len(norm_by_page) == 2054 and set(norm_by_page) == expected)
        language_counts = collections.Counter()
        for key, review in current.items():
            n = norm_by_page[key]
            regs = [self.region_by_id[x] for x in review['region_ids']]
            labels = sorted({r.get('language', 'und') for r in regs})
            self.check('current_language_region_labels_and_raw_flags', n['review_id'] == review['review_id'] and n['region_language_labels'] == labels and n['raw_current_review_check_flags_preserved'] == {'arabic': review.get('all_visible_arabic_diacritics_checked'), 'bengali': review.get('bengali_characters_checked')}, key)
            explicit = review.get('visible_language_presence') or review.get('language_presence_normalization', {}).get('visible_language_presence') or {}
            for name, code in [('arabic', 'ar'), ('bengali', 'bn')]:
                present = explicit.get(name, code in labels or 'mul' in labels)
                self.check('language_presence_not_inferred_from_vacuous_check_flag', n['visible_language_presence'][name] == present, [key, name])
                relevant = [r for r in regs if r.get('language') in [code, 'mul']]
                if present is True:
                    language_counts[name+'_present_pages'] += 1
                    verified = review['full_visible_character_review_complete'] is True or (bool(relevant) and all(r['status'] == 'character_verified' and not r.get('unresolved_items') for r in relevant))
                    state = 'checked' if verified else 'incomplete_or_localized_uncertainty'
                else:
                    state = 'not_applicable' if present is False else 'presence_not_established'
                self.check('language_normalized_states_supported_by_current_evidence', n['normalized_check_states'][name] == state, [key, name])
            self.check('language_metadata_adds_no_review_credit', n['new_page_credit'] == 0 and n['independent_QC_claim_by_metadata'] is False and n['current_version'] == VERSION, key)
            self.check('character_review_current_normalization_pointer', review['current_language_presence_metadata_ref'] == {'path': EP+'integration/current_language_presence.jsonl', 'source_volume': key[0], 'pdf_page': key[1]}, key)
        for page in self.pages:
            key = page['source_volume'], page['pdf_page']
            self.check('page_matrix_current_language_and_wording_status', page['current_language_presence'] == norm_by_page[key] and page['wording_review_all_regions_complete'] == current[key]['full_visible_character_review_complete'], key)
            expected_old = {k: oldpages[key].get(k) for k in ['wording_review_all_regions_complete', 'remaining_region_scope', 'visual_inspection_scope', 'current_language_presence']}
            self.check('prior_page_status_retained_exactly', page['patch08_prior_page_status_metadata'] == expected_old, key)
        nsummary = self.currentj(EP+'integration/language_presence_normalization.json')
        self.check('language_summary_current_counts', nsummary['review_rows'] == len(normalization) and nsummary['inherited_full_pages_without_detailed_review_row'] == {'1': [], '2': []} and all(nsummary[k] == v for k, v in language_counts.items()))
        self.metrics['current_language_presence_counts'] = dict(language_counts)
        self.emit('character structural evidence, before/after, page credit and exports')

    def exceptions(self):
        self.unc = self.currentjl(UNC)
        oldunc = self.readjl(self.P/UNC)
        us = self.currentjl('continuation/integration/semantic_uncertainty_current_status.jsonl')
        self.prefix(UNC)
        self.check('semantic_ambiguity_ledger_count', len(oldunc) == 22 and len(self.unc) == len(us) == 32)
        uhash = self.digest(self.resolve(UNC))
        self.unc_by_id = {}
        for n, (r, st) in enumerate(zip(self.unc, us), 1):
            uid = r.get('uncertainty_id') or r.get('exception_id')
            self.unc_by_id[uid] = r
            self.check('ambiguities_not_automatically_resolved', st['uncertainty_id'] == uid and st['ledger_sha256'] == uhash and st['ledger_1_based_row'] == n and st['current_semantic_uncertainty_resolved'] is False, uid)
            for sp in r['source_spans']:
                self.span(sp, r['source_volume'], 'all_ambiguity_source_spans_exact')
        self.check('ambiguity_IDs_unique', len(self.unc_by_id) == len(self.unc))
        resolutions = self.normal(self.readjl(self.E/'partial_review/source_exception_resolutions.jsonl'))
        resolved = {x for r in resolutions for x in r['resolution_of_exception_ids']}
        oldactive = self.readjl(self.P/'unresolved_exceptions.jsonl')
        active = self.currentjl('unresolved_exceptions.jsonl')
        oldkeep = [r for r in oldactive if r.get('exception_id') not in resolved]
        removed = [r for r in oldactive if r.get('exception_id') in resolved]
        additions = self.unc[len(oldunc):]
        self.check('source_exception_active_view_exact', same_json(active, oldkeep+additions))
        self.check('only_thirteen_character_exception_resolutions', len(resolutions) == len(resolved) == len(removed) == 13)
        self.check('removed_character_exceptions_retained_verbatim', same_json(removed, self.currentjl(EP+'integration/resolved_character_exception_history.jsonl')))
        for rel, suffix in [('source_exception_history.jsonl', additions), ('source_exception_resolution_index.jsonl', resolutions)]:
            self.prefix(rel)
            old = self.readjl(self.P/rel)
            current = self.currentjl(rel)
            self.check('source_exception_history_suffix_exact', current[len(old):] == suffix, rel)
        self.metrics.update({'semantic_ambiguities_retained': len(self.unc), 'new_semantic_source_exceptions': len(additions), 'resolved_character_exception_rows': len(removed), 'active_source_exception_rows': len(active)})
        self.emit('ambiguities and exception history/current view')

    def partitions_and_mappings(self):
        self.atoms = self.currentjl(ATOMS)
        self.atom_by_id = {r['source_segment_id']: r for r in self.atoms}
        self.check('atomic_segment_ID_uniqueness', len(self.atom_by_id) == len(self.atoms))
        byunit = collections.defaultdict(list)
        recordatoms = collections.defaultdict(list)
        bystory_atoms = collections.defaultdict(list)
        for r in self.atoms:
            byunit[r['source_unit_id']].append(r)
            bystory_atoms[(r['source_volume'], r['story'])].append(r)
            self.span(r, label='all_atomic_segments_exact_GLOBAL_CP')
            for rid in r['source_occurrence_record_ids']:
                recordatoms[rid].append(r['source_segment_id'])
        boundaries = {key: {p for r in rows for p in (r['cp_start'], r['cp_end'])} for key, rows in bystory_atoms.items()}
        for n, row in self.active.items():
            edges = boundaries.get((row['source_volume'], row['story']), set())
            self.check('every_active_semantic_boundary_has_atomic_edge', row['cp_start'] in edges and row['cp_end'] in edges and row['cp_end'] > row['cp_start'], [n, row['decision_id']])
        for row in self.records:
            edges = boundaries.get((row['source_volume'], row['doc_story']), set())
            self.check('every_record_boundary_has_atomic_edge', row['doc_cp_start'] in edges and row['doc_cp_end'] in edges, row['record_id'])
        for uid, row in self.unc_by_id.items():
            for span in row['source_spans']:
                edges = boundaries.get((row['source_volume'], span['story']), set())
                self.check('every_uncertainty_boundary_has_atomic_edge', span['cp_start'] in edges and span['cp_end'] in edges, uid)
        for unit in self.units:
            items = byunit[unit['paragraph_id']]
            cursor = unit['cp_start']
            for r in items:
                self.check('atomic_partitions_no_gaps_or_overlaps', r['source_volume'] == unit['source_volume'] and r['story'] == unit['story'] and r['cp_start'] == cursor and r['cp_end'] > cursor, r['source_segment_id'])
                cursor = r['cp_end']
                self.check('atomic_parent_record_mapping_preserved', r.get('parent_record_id') == unit.get('parent_record_id'), r['source_segment_id'])
            self.check('atomic_partitions_reconstruct_raw_exactly', cursor == unit['cp_end'] and ''.join(r['text_verbatim'] for r in items) == unit['raw_text'], unit['paragraph_id'])
            self.check('source_unit_atom_backlinks_exact', unit['patch08_semantic_segment_ids'] == [r['source_segment_id'] for r in items], unit['paragraph_id'])
        self.check('every_atom_maps_one_retained_source_unit', set(byunit) == set(self.unit_by_id))
        indexes = {}
        data = collections.defaultdict(list)
        for n, r in self.active.items():
            data[r['source_volume'], r['story']].append((r['cp_start'], r['cp_end'], n))
        indexes['sem'] = {k: RangeIndex(v) for k, v in data.items()}
        data = collections.defaultdict(list)
        for r in self.records:
            data[r['source_volume'], r['doc_story']].append((r['doc_cp_start'], r['doc_cp_end'], r['record_id']))
        indexes['rec'] = {k: RangeIndex(v) for k, v in data.items()}
        data = collections.defaultdict(list)
        for r in self.units:
            data[r['source_volume'], r['story']].append((r['cp_start'], r['cp_end'], r['paragraph_id']))
        indexes['unit'] = {k: RangeIndex(v) for k, v in data.items()}
        data = collections.defaultdict(list)
        for r in self.regions:
            for sp in r.get('source_spans', []):
                data[r['source_volume'], sp['story']].append((sp['cp_start'], sp['cp_end'], r['region_id']))
        indexes['char'] = {k: RangeIndex(v) for k, v in data.items()}
        data = collections.defaultdict(list)
        for uid, r in self.unc_by_id.items():
            for sp in r['source_spans']:
                data[r['source_volume'], sp['story']].append((sp['cp_start'], sp['cp_end'], uid))
        indexes['unc'] = {k: RangeIndex(v) for k, v in data.items()}
        indexes['atom'] = {k: RangeIndex([(r['cp_start'], r['cp_end'], r['source_segment_id']) for r in v]) for k, v in bystory_atoms.items()}

        def overlaps(kind, key, a, b):
            idx = indexes[kind].get(key)
            return idx.overlap(a, b) if idx else []

        ambiguity_seen = collections.Counter()
        active_seen = set()
        roles = collections.Counter()
        conflicts = []
        for r in self.atoms:
            key, a, b = (r['source_volume'], r['story']), r['cp_start'], r['cp_end']
            semranges = [x for x in overlaps('sem', key, a, b) if x[0] <= a and b <= x[1]]
            ords = {x[2] for x in semranges}
            active_seen.update(ords)
            self.check('atomic_all_active_semantic_refs_exact', set(r['all_active_semantic_row_ordinals']) == ords, r['source_segment_id'])
            width = min((x[1]-x[0] for x in semranges), default=None)
            leaf = {x[2] for x in semranges if x[1]-x[0] == width}
            self.check('atomic_current_leaf_authority_exact', {x['ledger_1_based_row'] for x in r['leaf_semantic_references']} == leaf, r['source_segment_id'])
            for ref in r['leaf_semantic_references']:
                n = ref['ledger_1_based_row']
                self.check('atomic_leaf_SHA_ordinal_ID_active', n in self.active and ref['ledger_sha256'] == self.sem_sha and ref['decision_id'] == self.sem[n-1]['decision_id'], [r['source_segment_id'], ref])
            expectedroles = {self.active[n]['after_role'] for n in leaf}
            self.check('atomic_roles_from_current_leaf_rows_only', set(r['role_candidates']) == expectedroles, r['source_segment_id'])
            roles[len(expectedroles)] += 1
            if len(expectedroles) > 1:
                conflicts.append({'source_segment_id': r['source_segment_id'], 'role_candidates': r['role_candidates'], 'leaf_semantic_references': r['leaf_semantic_references']})
            recs = {x[2] for x in overlaps('rec', key, a, b) if x[0] <= a and b <= x[1]}
            self.check('atomic_all_record_mappings_exact', set(r['source_occurrence_record_ids']) == recs, r['source_segment_id'])
            chars = {x[2] for x in overlaps('char', key, a, b)}
            self.check('atomic_all_character_overlap_joins_exact', set(r['character_region_ids']) == chars and set(r['pdf_pages']) == {self.region_by_id[x]['pdf_page'] for x in chars}, r['source_segment_id'])
            uncertainty = {x[2] for x in overlaps('unc', key, a, b) if x[0] <= a and b <= x[1]}
            flagged = [self.active[n] for n in ords if self.active[n].get('retained_uncertainty_id') or self.active[n].get('unresolved_field')]
            uncertainty.update(x['retained_uncertainty_id'] for x in flagged if x.get('retained_uncertainty_id'))
            self.check('atomic_ambiguity_joins_complete', set(r['source_ambiguity_ids']) == uncertainty, r['source_segment_id'])
            if uncertainty or flagged:
                self.check('atomic_ambiguity_never_coverage_resolved', r['classification_state'] == 'reviewed_source_ambiguity', r['source_segment_id'])
            for uid in uncertainty:
                ambiguity_seen[uid] += 1
            if any(c.isalnum() for c in r['text_verbatim']):
                self.check('no_unclassified_lexical_atom', r['classification_state'] in ['reviewed_source_ambiguity', 'reviewed_source_classification'] and bool(ords or uncertainty), r['source_segment_id'])
            self.check('atomic_no_source_or_canonical_promotion', r['source_text_changed'] is False and r['canonical_identity_inferred'] is False, r['source_segment_id'])
        self.check('every_semantic_ambiguity_has_exact_atomic_join', set(self.unc_by_id) <= set(ambiguity_seen), sorted(set(self.unc_by_id)-set(ambiguity_seen)))
        self.check('every_active_semantic_row_represented_in_atomic_view', active_seen == set(self.active), sorted(set(self.active)-active_seen))
        for r in self.records:
            self.check('record_to_atomic_backlinks_complete', r['continuation_patch08']['current_semantic_segment_ids'] == recordatoms[r['record_id']], r['record_id'])
        mapped = self.currentjl(EP+'integration/new_source_to_output_mapping.jsonl')
        self.prefix('continuation/integration/current_character_source_to_output_mapping.jsonl')
        oldmap = self.readjl(self.P/'continuation/integration/current_character_source_to_output_mapping.jsonl')
        newmap = self.currentjl('continuation/integration/current_character_source_to_output_mapping.jsonl')
        self.check('current_source_mapping_exact_suffix', newmap[len(oldmap):] == mapped)
        semantic_mapped = []
        for r in mapped:
            self.span(r, label='new_evidence_mapping_exact_GLOBAL_CP')
            key, a, b = (r['source_volume'], r['story']), r['cp_start'], r['cp_end']
            for kind, field in [('unit', 'source_unit_ids'), ('rec', 'occurrence_record_ids'), ('atom', 'current_semantic_segment_ids')]:
                self.check('new_evidence_mapping_complete_overlap_sets', set(r[field]) == {x[2] for x in overlaps(kind, key, a, b)}, [r['evidence_id'], field])
            if r['evidence_kind'] == 'patch08_semantic_span':
                semantic_mapped.append(r['evidence_id'])
                ref = r['semantic_reference']
                n = ref['ledger_1_based_row']
                self.check('new_mapping_qualified_semantic_reference', ref['ledger_sha256'] == self.sem_sha and ref['decision_id'] == r['evidence_id'] == self.sem[n-1]['decision_id'], r['evidence_id'])
        self.check('every_new_semantic_row_has_mapping', semantic_mapped == [r['decision_id'] for r in self.new_sem])
        summary = self.currentj(EP+'integration/semantic_partition_summary.json')
        states = dict(collections.Counter(r['classification_state'] for r in self.atoms))
        self.check('partition_summary_matches_recomputed', summary['source_segments'] == len(self.atoms) and summary['source_units'] == len(self.units) and summary['classification_states'] == states)
        self.metrics.update({'atomic_source_segments': len(self.atoms), 'atomic_classification_states': states, 'atomic_distinct_role_candidate_counts': dict(roles), 'new_source_mapping_rows': len(mapped), 'uncertainty_to_atomic_join_counts': dict(ambiguity_seen)})
        self.notes.append('Equal-width active semantic rows may expose multiple role labels; these labels and qualified references are retained rather than collapsed. This audit verifies their data joins, not semantic equivalence of labels.')
        self.write('multiple_leaf_role_labels.json', conflicts)
        self.emit('lossless atomic partitions, all record/evidence mappings and ambiguity joins')

    def evidence_paths(self):
        path_suffix = re.compile(r'\.(?:png|jpe?g|webp|pdf|docx?|jsonl?|csv|txt|py)$', re.I)
        seen = set()
        failures = []

        def locate(value, context, expected=None, historical=False):
            p = Path(value)
            candidates = []
            if p.is_absolute():
                candidates.append(p)
            else:
                candidates.append(self.E.parents[1]/value)
                if value.startswith('patches/patch08/'):
                    candidates.append(self.E/value[len('patches/patch08/'):])
                if value.startswith(EP):
                    candidates.append(self.E/value[len(EP):])
                if historical:
                    candidates.append(self.P/value)
                candidates += [self.S/value, self.P/value]
                candidates += [context.parent/value]
                if value.startswith('images/'):
                    candidates += [a/value for a in list(context.parents)[:4]]
                if '/' not in value and value.startswith('bn_riyadh_'):
                    candidates.append(self.P/'originals'/value)
            candidates = list(dict.fromkeys(c.resolve() for c in candidates if c.is_file()))
            if expected:
                matching = [c for c in candidates if self.digest(c) == expected]
                if matching:
                    return matching[0]
            return candidates[0] if candidates else None

        def walk(obj, context, trail):
            if isinstance(obj, list):
                for n, v in enumerate(obj):
                    walk(v, context, trail+f'[{n}]')
            elif isinstance(obj, dict):
                child_context = context
                for basekey in ('file', 'evidence_file', 'ledger_path'):
                    val = obj.get(basekey)
                    if isinstance(val, str) and path_suffix.search(val):
                        q = locate(val, context)
                        if q:
                            child_context = q
                            break
                for k, v in obj.items():
                    if isinstance(v, str) and path_suffix.search(v) and not v.startswith(('https://', 'http://')):
                        # Bare source labels and prose ending in an extension are not file assertions.
                        ispath = k in ('path', 'file', 'image', 'image_path', 'local_path', 'page_ledger', 'source_pdf') or k.endswith(('_path', '_file', '_ledger'))
                        if not ispath:
                            continue
                        hashkeys = [k+'_sha256']
                        if k in ('path', 'file', 'local_path'):
                            hashkeys += ['sha256']
                        if k in ('image', 'image_path'):
                            hashkeys += ['image_sha256']
                        if k == 'source_pdf':
                            hashkeys += ['source_pdf_sha256']
                        if k.endswith('_file'):
                            hashkeys += [k[:-5]+'_sha256']
                        expected = next((obj[h] for h in hashkeys if isinstance(obj.get(h), str) and re.fullmatch('[a-f0-9]{64}', obj[h])), None)
                        ident = (v, expected, str(child_context.parent))
                        if ident in seen:
                            continue
                        seen.add(ident)
                        found = locate(v, child_context, expected, k.startswith(('parent_', 'inherited_', 'prior_')))
                        ok = found is not None
                        self.check('referenced_evidence_path_resolves', ok, {'path': v, 'from': str(context), 'field': trail+'.'+k})
                        if not ok:
                            failures.append({'path': v, 'from': str(context), 'field': trail+'.'+k, 'expected_sha256': expected})
                            continue
                        self.use(found)
                        self.references.add(str(found))
                        self.reference_stats['paths_resolved'] += 1
                        if expected:
                            self.check('referenced_evidence_SHA_matches_actual_bytes', self.digest(found) == expected, {'path': v, 'actual_path': str(found), 'expected': expected, 'actual': self.digest(found)})
                            self.reference_stats['paired_hashes_checked'] += 1
                    else:
                        walk(v, child_context, trail+'.'+k)

        documents = []
        for p in self.E.iterdir():
            if p.is_dir() and p.name not in ['independent_qc', 'bank_preflight', 'candidate_history', '__pycache__']:
                documents.extend(sorted(p.glob('*.json')))
                documents.extend(sorted(p.glob('*.jsonl')))
        # All candidate additions are examined, plus cumulative current character
        # rows. Parent semantic evidence already belongs to the authenticated parent.
        for p in documents:
            obj = self.readjl(p) if p.suffix == '.jsonl' else self.readj(p)
            walk(obj, p, '$')
        for rel in [EP+'integration/new_semantic_decisions.jsonl', EP+'integration/semantic_investigation_status.jsonl', EP+'integration/source_scope_observations.jsonl']:
            p = self.resolve(rel)
            walk(self.readjl(p), p, '$')
        self.metrics['evidence_reference_checks'] = dict(self.reference_stats)
        self.write('evidence_path_findings.json', failures)
        self.emit('new referenced evidence paths and declared hashes')

    def metadata(self):
        cov = self.currentj('coverage.json')
        meta = self.currentj('metadata.json')
        rem = self.currentj('remaining_work.json')
        resume = self.currentj('resume_state.json')
        summary = self.currentj('continuation/integration/integration_summary.json')
        delta = self.currentj(EP+'patch08_summary.json')
        self.check('semantic_summary_duplicate_export_exact', summary == cov['semantic_integration'])
        self.check('current_metadata_version', summary.get('data_version') == VERSION and meta.get('version') == VERSION and cov.get('data_version') == VERSION and resume.get('checkpoint_target') == VERSION)
        expected = {'explicit_semantic_interval_decisions': len(self.sem), 'active_semantic_interval_decisions': len(self.active), 'patch_decision_rows': len(self.new_sem), 'explicit_semantic_unique_decision_IDs': len({r['decision_id'] for r in self.sem}), 'current_semantic_uncertainty_rows': len(self.unc)}
        for k, v in expected.items():
            self.check('current_semantic_summary_recomputed_counts', summary.get(k) == v, [k, summary.get(k), v])
        expected_before = sum(bool(x['current_interpretation_active']) for x in self.parent_status) + len(self.new_sem)
        self.check('historical_and_current_pre_overlay_counts_distinct', 'historical_unsuppressed_rows_before_current_correction_overlay' not in summary and summary.get('prior_cp016_historical_unsuppressed_rows_before_correction_overlay') == 26540 and summary.get('current_active_rows_before_patch08_correction_overlays') == expected_before and summary.get('current_active_rows_after_patch08_correction_overlays') == len(self.active))
        for k, v in {'semantic_rows_cumulative': len(self.sem), 'active_semantic_rows': len(self.active), 'new_semantic_decisions': len(self.new_sem), 'new_page_attempts': 10, 'new_full_character_pages': 10, 'inherited_partial_to_full_upgrades': 13, 'legacy_flag_detailed_rechecks': 3, 'full_visible_character_pages_cumulative': 2053, 'unattempted_character_pages': 0, 'prior_semantic_cases_resolved': 0}.items():
            self.check('current_patch_summary_recomputed_counts', delta.get(k) == v, [k, delta.get(k), v])
        for source, part in [('coverage', cov['current_character_review_partition']), ('remaining', rem['current_character_review_partition']), ('resume', resume['current_character_review_partition'])]:
            self.check('metadata_character_partition_consistent', part['attempted_pages'] == 2054 and part['full_pages'] == 2053 and part['partial_pages'] == 1 and part['unattempted_pages'] == 0 and part['partial_page_list'] == {'1': [962], '2': []}, source)
        for source, value in [('summary.current_inherited_semantic_ID_collision_audit', summary.get('current_inherited_semantic_ID_collision_audit')), ('summary.current_semantic_correction_overlay', summary.get('current_semantic_correction_overlay')), ('resume.current_additive_semantic_overlay', resume['continuation_tooling'].get('current_additive_semantic_overlay')), ('resume.current_semantic_ID_collision_audit', resume['continuation_tooling'].get('current_semantic_ID_collision_audit')), ('resume.current_semantic_correction_overlay', resume['continuation_tooling'].get('current_semantic_correction_overlay'))]:
            self.check('current_semantic_aliases_are_patch08', isinstance(value, str) and value.startswith(EP), [source, value])
        parent_identity = resume['continuation_tooling'].get('builder_parent_identity', {})
        self.check('current_builder_alias_patch08', 'patch08' in resume['continuation_tooling'].get('recovery_builder', '') and parent_identity == {'version': 'v2_cp016_patch07', 'archive_sha256': AUTH_SHA}, parent_identity)
        optional_old = ['current_semantic_boundary_extension_evidence', 'current_partial_semantic_confirmations', 'current_same_patch_boundary_redistribution_history', 'current_partial_semantic_confirmation_status', 'current_same_patch_semantic_local_correction_history']
        self.check('inherited_optional_patch07_evidence_explicitly_historical', all(k not in resume['continuation_tooling'] for k in optional_old) and 'partial_semantic_confirmation_evidence' not in rem)
        for source, value in [('coverage.current_language_presence_metadata', cov.get('current_language_presence_metadata')), ('coverage.current_inherited_character_correction_overlay', cov.get('current_inherited_character_correction_overlay'))]:
            self.check('current_character_aliases_are_patch08', isinstance(value, str) and value.startswith(EP), [source, value])
        self.check('source_provenance_metadata_unchanged', meta['inputs'] == self.readj(self.P/'metadata.json')['inputs'] and meta['bibliographic_evidence'] == self.readj(self.P/'metadata.json')['bibliographic_evidence'] and meta['source_fidelity_policy'] == self.readj(self.P/'metadata.json')['source_fidelity_policy'])
        self.check('bank_readiness_not_claimed', delta.get('bank_ready') is False and rem.get('whole_book_independent_review_complete') is False)
        correction_index = self.currentj(summary['current_semantic_correction_overlay'])
        self.check('current_correction_index_ledger_identity', correction_index['current_semantic_ledger_sha256'] == self.sem_sha)
        for r in correction_index['current_patch_overlays']:
            self.check('current_correction_index_ledger_rows', len(self.currentjl(r['path'])) == r['rows'], r['path'])
        character_index = self.currentj(cov['current_inherited_character_correction_overlay'])
        self.check('current_character_correction_index_complete', set(character_index['current_patch_overlays']) == {EP+'partial_review/character_region_corrections.jsonl', EP+'partial_review/character_review_corrections.jsonl'})
        self.emit('current status/counts/aliases and unchanged source provenance')

    def write(self, name, obj):
        (self.O/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

    def finish(self):
        self.manifest_check(ending=True)
        for row in list(self.inputs.values()):
            p = Path(row['path'])
            self.check('reviewed_inputs_stable_through_audit', p.is_file() and p.stat().st_size == row['bytes'] and self.digest(p) == row['sha256'], row['path'])
        failed = {k: v for k, v in self.checks.items() if v['failures']}
        stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        limitations = [
            'Engineering/integrity verification only. No image or text was manually reread by this audit, and no manual textual QC or whole-book certification is claimed.',
            'The audited object is the logical cumulative package: candidate stage overrides authenticated parent paths; new continuation/patch08 evidence resolves to frozen author evidence when absent from the stage. Final assembled archive member preservation requires a packaging check.',
            'The parent archive authentication record is inherited. Every parent input actually consumed by this audit is independently checked against the authenticated member index; this run does not reassemble or reauthenticate all archive chunks.',
            'Current leaf selection follows the candidate’s documented narrowest-active-span policy. Exact joins and inactivity are tested, but engineering checks cannot certify the semantic meaning of a selected role or intended speaker.',
            'All source-limited ambiguities remain unresolved; exact interval coverage does not convert them into resolved semantic claims.',
            'Evidence hash verification establishes identity and availability, not whether the claimed human/model image observation occurred.',
            'Hash-qualified inherited evidence can retain its former current path. Its exact historical bytes are resolved from the authenticated parent during this audit and must be resolved through the final package member-preservation map after assembly.',
            'No GitHub writes, Library upload, publication, canonical reconciliation, deduplication, or bank ingestion is performed.'
        ]
        status = 'pass_with_explicit_scope_limits' if not failed else 'requires_correction'
        reproduction = [sys.executable, str(Path(__file__).resolve()), '--parent', str(self.P), '--stage', str(self.S), '--manifest', str(self.a.manifest.resolve()), '--evidence-root', str(self.E), '--out', str(self.O)]
        report = {'audit_id': 'patch08-independent-engineering-integrity', 'utc': stamp, 'status': status, 'candidate_revision': self.manifest.get('candidate_revision'), 'candidate_manifest_sha256': self.digest(self.a.manifest), 'audit_script_sha256': self.digest(Path(__file__)), 'reproduction_argv': reproduction, 'candidate_stage': str(self.S), 'parent_archive_sha256': AUTH_SHA, 'metrics': self.metrics, 'check_categories': len(self.checks), 'total_assertion_evaluations': sum(x['evaluations'] for x in self.checks.values()), 'failure_categories': len(failed), 'failures': failed, 'checks': self.checks, 'notes': self.notes, 'limitations': limitations, 'manual_textual_QC_performed_by_this_audit': False, 'bank_ready_asserted': False, 'publication_performed': False}
        self.write('REPORT.json', report)
        self.write('reviewed_inputs.json', {'utc': stamp, 'candidate_revision': self.manifest.get('candidate_revision'), 'candidate_manifest_sha256': self.digest(self.a.manifest), 'files': sorted(self.inputs.values(), key=lambda r: r['path'])})
        self.write('HANDOFF.json', {'status': status, 'candidate_revision': self.manifest.get('candidate_revision'), 'candidate_manifest_sha256': self.digest(self.a.manifest), 'report': str(self.O/'REPORT.json'), 'reproducible_audit_script': str(Path(__file__).resolve()), 'failure_categories': len(failed), 'metrics': self.metrics, 'independent_engineering_review_complete': not failed, 'manual_textual_review_claimed': False, 'whole_book_independent_textual_QC_claimed': False, 'packaging_final_delta_required': True})
        lines = ['# Patch08 independent engineering and integrity QC', '', f'**Result: {status}.** Candidate revision {self.manifest.get("candidate_revision")}.', '', '## Audited findings', '']
        for k, v in self.metrics.items():
            if isinstance(v, (int, str)):
                lines.append(f'- {k}: {v}')
        lines += ['', '## What the checks establish', '',
            '1. Every parent occurrence ID, its order, and every old record field except data_version are preserved. This includes source references and grades, translation provenance, language quotations, control-bearing source segments, and null canonical fields. The JSON, JSONL, and CSV exports carry the same typed values.',
            '2. All original DOC/PDF input hashes and all 18 raw story files match their authenticated source bytes. Global CP positions are interpreted relative to each story’s recorded start and sliced as UTF-16 code units. The complete source-unit stream reconstructs every story, including nonprinting controls and trailing units.',
            '3. The cumulative semantic ledger retains the parent byte prefix exactly. Every newly authored semantic field is retained through integration; every new source span and nested exact-source context matches its global CP slice. All old inactive interpretations remain inactive, and the eight inherited duplicate-ID groups retain qualified SHA/ordinal references.',
            '4. The 207 inherited reference-role replacements form complete, nonoverlapping partitions of their exact parent spans. Every additional correction prompted by semantic QC has a matching before-ledger hash, row ordinal, retained old row, complete replacement partition, and active replacement rows. No correction grants character-review credit.',
            '5. Atomic source segments have no lost, duplicated, reordered, or overlapping source text within a source unit. All active semantic, source-record, and uncertainty boundaries appear as atomic edges; all active rows are represented. Record backlinks, character overlaps, evidence mappings, and all 32 ambiguity joins agree exactly with source positions.',
            '6. The current character view has one detailed review per original page. Counts distinguish ten newly attempted/full tail pages, three detailed rechecks of already credited legacy pages, and thirteen old partial-to-full upgrades. V1 PDF page 962 remains partial. Raw before/after evidence and older language flags remain preserved, while a separate current normalization governs the page matrix.',
            '7. Resolved character exceptions remain in history. Only the thirteen explicitly resolved old character rows leave the active view; ten new semantic source exceptions are added. The 22 inherited semantic cases remain unresolved alongside the ten new cases, and current coverage cannot resolve them automatically.',
            '8. New referenced evidence paths resolve to actual files, and every paired file hash checked matches those bytes. This confirms evidence identity and availability. It does not certify that a claimed image observation occurred or that a semantic judgment is correct.',
            '9. Current summary counts are recalculated from the ledgers. Current semantic/character correction indexes, version identifiers, language metadata, and builder/parent identity point to patch08. Older optional patch07 evidence is explicitly named as inherited history.',
            '', '## Method and evidence', '', 'The audit script is independent of the build script and reads the candidate, authenticated parent, source story exports, exact CP spans, current state indexes, before/after corrections, mappings, export formats, and referenced evidence bytes. It does not modify the candidate. All consumed inputs are bound in reviewed_inputs.json.', '', f'Checked {len(self.checks)} categories with {sum(x["evaluations"] for x in self.checks.values()):,} assertion evaluations.', '', '## Findings requiring correction', '']
        if failed:
            for k, v in failed.items():
                lines += [f'### {k}', '', f'{v["failures"]} violations in {v["evaluations"]} evaluations.', '', '```json', json.dumps(v['examples'], ensure_ascii=False, indent=2), '```', '']
        else:
            lines += ['No failing integrity checks remained for these exact reviewed input bytes.', '']
        lines += ['## Reading current and historical data safely', '', 'Use the current semantic status index and source partitions as the current classification views. The cumulative semantic ledger and original record fields deliberately retain older interpretations and statuses. Resolve a semantic reference by its ledger SHA-256 plus 1-based row ordinal; an ID-only lookup must return every matching historical row. Multiple equal-width role labels remain visible as qualified multiple authorities. Engineering validation does not collapse them or claim that every label is synonymous.', '', '## Limits and retained uncertainty', ''] + ['- '+x for x in limitations] + ['', '## Reproduction', '', 'Run audit_patch08.py with --parent, --stage, --manifest, --evidence-root and a separate --out directory. Exact argv is recorded in REPORT.json. The script exits nonzero if an integrity check fails. A status-only or packaging change must be bound in a final delta manifest and checked before release.', '']
        (self.O/'REPORT.md').write_text('\n'.join(lines), encoding='utf8')
        print(json.dumps({'status': status, 'failure_categories': len(failed), 'failures': {k: v['failures'] for k, v in failed.items()}, 'metrics': self.metrics, 'report': str(self.O/'REPORT.json')}, ensure_ascii=False), flush=True)
        return 1 if failed else 0


class RangeIndex:
    """Independent sorted range query with prefix end maxima."""
    def __init__(self, rows):
        self.rows = sorted(rows)
        self.starts = [x[0] for x in self.rows]
        self.max_end = []
        m = -1
        for x in self.rows:
            m = max(m, x[1])
            self.max_end.append(m)

    def overlap(self, a, b):
        first = bisect.bisect_right(self.max_end, a)
        last = bisect.bisect_left(self.starts, b)
        return [x for x in self.rows[first:last] if x[1] > a]


def main():
    w = Path(__file__).resolve().parents[4]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', type=Path, default=w/'work/cp016_parent/bn_riyadh_20261113_v2_cp016_patch07')
    p.add_argument('--stage', type=Path, default=w/'work/patch08_integration_output/bn_riyadh_20261113_v2_cp017_patch08')
    p.add_argument('--manifest', type=Path, default=w/'patches/patch08/REVIEW_CANDIDATE.json')
    p.add_argument('--evidence-root', type=Path, default=w/'patches/patch08')
    p.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    args = p.parse_args()
    audit = Audit(args)
    audit.manifest_check()
    audit.sources()
    audit.records_units()
    audit.semantics()
    audit.characters()
    audit.exceptions()
    audit.partitions_and_mappings()
    audit.evidence_paths()
    audit.metadata()
    return audit.finish()


if __name__ == '__main__':
    sys.exit(main())
