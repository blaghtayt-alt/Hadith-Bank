"""Reuse explicit prior boundary reviews for identical complete source fields.

This is a text-equality proof, not an edition/number concordance. Deen Hindi
keeps every original identity, reference, grade and source snapshot. No fuzzy,
normalized or cross-language match is permitted. Unmatched sibling fields
remain complete source context. A prior pending or negative decision is never
turned into a narration approval.
"""
from __future__ import annotations

import collections
import copy
import hashlib
import json
from pathlib import Path

from fawaz_review_inputs import load_review_catalog, json_bytes, gzip_bytes
from fawaz_report_types import validate_report_metadata


PLAN_PATH = 'catalog/deenhindi-review-reuse-plan.json'
LEDGER_PATH = 'imports/web-deenhindi-20261112/review-reuse/exact-field-decisions.json.gz'
INPUT_COPY_FOLDER = 'imports/web-deenhindi-20261112/review-reuse/inputs'
REPOSITORY = 'fawazahmed0/hadith-api'
REVISION = 'df57907be35291c91ad6a6691180e22ca9920784'
METHOD = 'identical_complete_same_language_prior_boundary_review_v1'
LANGUAGES = {'ara': 'ar', 'eng': 'en', 'urd': 'ur', 'ben': 'bn'}
FIELDS = {'ar': 'textArabic', 'en': 'translationEnglish', 'ur': 'translationUrdu'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError('Deen Hindi review reuse: ' + message)


def checked_input_path(root, relative):
    root, pure = Path(root), Path(relative)
    require(not pure.is_absolute() and '..' not in pure.parts
            and '\\' not in relative and ':' not in relative,
            'unsafe prior review input path')
    path = root / pure
    require(path.resolve().is_relative_to(root.resolve())
            and not any(p.is_symlink() for p in [path, *path.parents]
                        if p.is_relative_to(root)), 'unsafe prior review input path')
    return path


def input_copy_receipts(inputs):
    """Bind immutable source-path copies to their original working inputs."""
    return [{'path': INPUT_COPY_FOLDER + '/' + item['sha256'] + '/' + item['path'],
             'sha256': item['sha256'], 'size_bytes': item['size_bytes'],
             'original_input_path': item['path'],
             'role': 'exact_same_language_prior_boundary_review_input_copy'}
            for item in inputs]


def input_receipts(root):
    """Small fingerprints also let a source worker notice a new prior review."""
    root = Path(root)
    plan_path = root / PLAN_PATH
    if not plan_path.is_file():
        return []
    plan = json.loads(plan_path.read_bytes())
    require(plan.get('schema') == 'hadith-bank-exact-field-review-reuse-plan-v1'
            and plan.get('site') == 'deenhindi'
            and plan.get('method') == METHOD, 'invalid explicit reuse plan')
    if plan.get('enabled') is not True:
        return []
    require(plan.get('repository') == REPOSITORY and plan.get('revision') == REVISION,
            'prior source revision must stay pinned')
    paths = [PLAN_PATH, 'catalog/fawaz-review-inputs.json',
             'scripts/deenhindi_review_reuse.py', 'scripts/fawaz_review_inputs.py',
             'scripts/fawaz_report_types.py']
    manifest = json.loads((root / paths[1]).read_bytes())
    paths.extend(manifest[key]['path'] for key in ('baseline', 'recovered_catalog', 'phase_archive'))
    paths.extend(item['path'] for item in manifest.get('additional_reviews', []))
    result = []
    for relative in sorted(set(paths)):
        path = checked_input_path(root, relative)
        require(path.is_file(), 'missing prior review input')
        data = path.read_bytes()
        result.append({'path': relative, 'sha256': sha(data), 'size_bytes': len(data),
                       'role': 'exact_same_language_prior_boundary_review_input'})
    return result


def _groups(text, decision):
    """Validate original review ranges before projecting their same bytes."""
    require(sha(text.encode()) == decision.get('source_text_sha256'), 'full text hash mismatch')
    spans = decision.get('quotation_spans')
    require(isinstance(spans, list) and spans, 'positive reviewed spans required')
    cursor = 0
    for span in spans:
        require(isinstance(span, list) and len(span) == 2
                and all(type(n) is int for n in span)
                and 0 <= cursor <= span[0] < span[1] <= len(text)
                and text[span[0]:span[1]].strip(), 'invalid original reviewed span')
        cursor = span[1]
    validate_report_metadata(text, decision)
    if decision.get('source_report_groups'):
        return decision['source_report_groups']
    if len(spans) == 1:
        return [spans]
    if (decision.get('source_report_count') == 1
            and decision.get('source_report_relationship') == 'separate_passages_of_one_source_report'
            and decision.get('source_passage_boundaries') == spans
            and not decision.get('source_report_boundaries')):
        return [spans]
    require(decision.get('source_report_count') == len(spans)
            and decision.get('source_report_boundaries') == spans,
            'disjoint spans need an explicit original report relationship')
    return [[span] for span in spans]


def _speaker(speakers):
    return '; '.join((s.get('name_as_supplied') or 'unnamed in the supplied field')
                     + ' (' + s['role'] + ')' for s in speakers)


def _projection(text, decision):
    groups = _groups(text, decision)
    components = decision.get('report_component_classifications', [])
    spans = []
    for index, group in enumerate(groups, 1):
        component = next((c for c in components
                          if c.get('spans', [c.get('span')]) == group), None)
        attribution = component or decision
        typ = attribution.get('report_type')
        if typ is None:
            require(decision.get('classification') == 'source_attributed_prophetic_narration',
                    'legacy positive review does not state Prophetic attribution')
            typ, speaker = 'prophetic_report', 'Muhammad, as explicitly attributed in this complete source field'
        else:
            speaker = _speaker(attribution['reported_speakers'])
        reason = (attribution.get('report_classification_note')
                  or decision.get('report_classification_note')
                  or decision.get('decision_note') or decision.get('reason'))
        require(isinstance(reason, str) and reason.strip(), 'prior boundary rationale missing')
        for start, end in group:
            spans.append({'start': start, 'end': end, 'sha256': sha(text[start:end].encode()),
                          'component_id': 'report-' + str(index), 'report_type': typ,
                          'speaker': speaker, 'reason': reason})
    return spans


def _signature(spans):
    # Two equal texts with inconsistent earlier boundaries/types/speakers do
    # not acquire approval merely because one candidate was encountered first.
    return [(s['start'], s['end'], s['component_id'], s['report_type'], s['speaker']) for s in spans]


class ExactReviewReuse:
    def __init__(self, root, *, decisions=None):
        self.root = Path(root)
        self.inputs = input_receipts(root) if decisions is None else []
        self.enabled = decisions is not None or bool(self.inputs)
        self.index = collections.defaultdict(list)
        self.records, self.conflicts, self.context_dependent = [], [], []
        self.prepared = None
        self.evidence_inputs = []
        if not self.enabled:
            return
        if decisions is None:
            catalog = load_review_catalog(self.root, repository=REPOSITORY, revision=REVISION)
            require(catalog is not None, 'prior reviewed catalog is missing')
            decisions = catalog['decisions']
        for decision in decisions:
            prefix = decision['provider_edition'].split('-', 1)[0]
            language = LANGUAGES.get(prefix)
            if language in FIELDS:
                self.index[(language, decision['source_text_sha256'])].append(decision)

    def review(self, saved):
        if not self.enabled:
            return None
        identity = 'deenhindi-' + saved['collection'] + ':' + saved['number']
        fields = []
        for language, source_field in FIELDS.items():
            text = saved['source_record'].get(source_field)
            if not isinstance(text, str) or not text.strip():
                continue
            candidates = self.index.get((language, sha(text.encode())), [])
            dependent = [d for d in candidates if d.get('source_reference')]
            if dependent:
                self.context_dependent.append({'id': identity, 'language': language,
                    'reason': 'prior_review_depends_on_another_source_occurrence',
                    'prior_decision_sha256': [sha(json_bytes(d)) for d in dependent]})
            positive = [d for d in candidates if d.get('quotation_spans')
                        and not d.get('action') and not d.get('source_reference')]
            if not positive:
                continue
            if any(d.get('action') for d in candidates):
                self.conflicts.append({'id': identity, 'language': language,
                                      'reason': 'positive_and_pending_or_negative_prior_decisions'})
                continue
            projected = [_projection(text, d) for d in positive]
            if any(_signature(p) != _signature(projected[0]) for p in projected[1:]):
                self.conflicts.append({'id': identity, 'language': language,
                                      'reason': 'inconsistent_prior_boundaries_or_attribution'})
                continue
            evidence = [{'repository': REPOSITORY, 'revision': REVISION,
                         'provider_book': d['provider_book'], 'provider_edition': d['provider_edition'],
                         'typed_hadithnumber': d['typed_hadithnumber'],
                         'decision_sha256': sha(json_bytes(d)),
                         'full_source_text_sha256': d['source_text_sha256']}
                        for d in positive]
            spans = projected[0]
            fields.append({'language_version_id': identity + ':' + language,
                           'language': language, 'source_field': source_field,
                           'text_sha256': sha(text.encode()), 'text_chars': len(text),
                           'reviewed': True, 'review_method': METHOD,
                           'review_scope': 'Exact complete same-language bytes match an existing explicit boundary review; no new manual reading, translation verification, source identity equivalence or authenticity certification is claimed.',
                           'chars_reviewed': len(text), 'bytes_reviewed': len(text.encode()),
                           'prior_review_evidence': evidence,
                           'action': 'whole' if len(spans) == 1 and spans[0]['start'] == 0
                                     and spans[0]['end'] == len(text) else 'excerpts',
                           'spans': spans,
                           'reason': 'Reused the explicit prior attribution and boundaries for this identical complete language field. Deen Hindi source identity, references and grades remain independently supplied. ' +
                                     ' '.join(dict.fromkeys(s['reason'] for s in spans))})
        if not fields:
            return None
        source_bytes = (json.dumps(saved['source_record'], ensure_ascii=False,
                                  sort_keys=True, indent=2) + '\n').encode()
        decision = {'id': identity, 'collection': saved['collection'], 'number': saved['number'],
                    'decision': 'register', 'review_method': METHOD,
                    'source_record_sha256': sha(source_bytes),
                    'source_snapshot': copy.deepcopy(saved['snapshot']),
                    'source_reference_verbatim': saved['source_reference_verbatim'],
                    'numbering_system': 'deenhindi_source_local', 'verified_external_reference': None,
                    'reason': 'Only independently exact same-language source fields with an explicit positive prior boundary review are selected. Other complete fields remain source context.',
                    'field_reviews': fields}
        self.records.append(decision)
        return decision

    def prepare(self):
        if not self.enabled:
            return None
        self.prepared = None
        self.evidence_inputs = []
        copies = []
        receipts = input_copy_receipts(self.inputs)
        for original, receipt in zip(self.inputs, receipts):
            source = checked_input_path(self.root, original['path'])
            require(source.is_file(), 'missing prior review input')
            data = source.read_bytes()
            require(sha(data) == original['sha256'] and len(data) == original['size_bytes'],
                    'prior review input changed during preparation: ' + original['path'])
            target = checked_input_path(self.root, receipt['path'])
            copies.append((target, data))
        document = {'schema': 'hadith-bank-exact-field-review-reuse-ledger-v1',
                    'site': 'deenhindi', 'method': METHOD,
                    'independent_pro_qc': 'not_performed',
                    'input_receipts': self.inputs,
                    'supporting_input_copies': receipts,
                    'scope': 'Boundary/type/speaker review reuse for byte-identical full fields only. No edition, source identity, number, grade, chain or external reference is transferred. Unmatched fields are not approved.',
                    'records': self.records, 'conflicts': self.conflicts,
                    'context_dependent_fields_not_reused': self.context_dependent}
        raw = json_bytes(document)
        stored = gzip_bytes(raw)
        path = self.root / LEDGER_PATH
        self.prepared = path, stored, copies
        self.evidence_inputs = receipts
        return {'path': LEDGER_PATH, 'sha256': sha(stored), 'size_bytes': len(stored),
                'compression': 'gzip', 'uncompressed_sha256': sha(raw),
                'method': METHOD, 'role': 'exact_same_language_prior_boundary_review_decisions'}

    def supporting_files(self):
        return copy.deepcopy(self.evidence_inputs)

    def commit(self):
        if not self.enabled:
            return
        require(self.prepared is not None, 'reuse evidence must be prepared before commit')
        path, stored, copies = self.prepared
        # Validate every existing immutable copy before changing any durable
        # evidence. A corrupted copy must never be silently overwritten.
        for target, data in copies:
            checked_input_path(self.root, str(target.relative_to(self.root)))
            require(not target.exists() or (target.is_file() and target.read_bytes() == data),
                    'immutable prior review input copy changed: ' + str(target.relative_to(self.root)))
        for target, data in copies:
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.tmp')
            require(not temporary.is_symlink(), 'unsafe temporary input copy')
            temporary.write_bytes(data)
            temporary.replace(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_bytes(stored)
        temporary.replace(path)

    def save(self):
        receipt = self.prepare()
        self.commit()
        return receipt
