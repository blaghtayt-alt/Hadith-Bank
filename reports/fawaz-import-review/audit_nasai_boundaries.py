"""Read-only all-field audit of the pinned Nasai boundary patch and Abu2251."""
from pathlib import Path
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2], help='Repository checkout containing the reviewed importer and helper code')
parser.add_argument('--raw-root', type=Path, required=True, help='Exact pinned edition JSON files with their .receipt.json files')
parser.add_argument('--baseline-root', type=Path, required=True, help='Unchanged final-v1 export containing classification/nasai.jsonl.gz')
parser.add_argument('--baseline-boundaries', type=Path, required=True, help='Baseline boundary helper with SHA25613d9a00a...')
parser.add_argument('--reviewed-spans', type=Path, help='Catalog decisions JSON or deterministic gzip; defaults to the checkout catalog')
parser.add_argument('--output', type=Path, required=True, help='New JSON audit receipt destination; do not overwrite an immutable earlier receipt')
args = parser.parse_args()
HERE = args.root.resolve()
SOURCE = args.raw_root.resolve()
BASELINE = args.baseline_root.resolve()
sys.path.insert(0, str(HERE / 'scripts'))
import import_fawaz_bulk as importer
import fawaz_attribution as attribution
import fawaz_boundaries as current


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


old_path = args.baseline_boundaries.resolve()
assert digest(old_path.read_bytes()) == '13d9a00a96668cf68b02f5a16a84c8cd724d87852c041c877b6e0c54d16ed624'
spec = importlib.util.spec_from_file_location('nasai_old_boundaries', old_path)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
current_sha = digest((HERE / 'scripts/fawaz_boundaries.py').read_bytes())
attribution_sha = digest((HERE / 'scripts/fawaz_attribution.py').read_bytes())
decision_path = args.reviewed_spans or HERE / 'catalog/fawaz-reviewed-spans.json'
decision_bytes = decision_path.read_bytes()
if decision_path.suffix == '.gz':
    decision_bytes = gzip.decompress(decision_bytes)
decision_doc = json.loads(decision_bytes)
decisions = {(d['provider_book'], d['provider_edition'].split('-', 1)[0], d['typed_hadithnumber']): d
             for d in decision_doc['decisions']}


def partition(raw, book, language, splitter):
    q, notes, spans = importer.split_compiler_note(raw, book, language)
    out = splitter(raw, book, language)
    if out is None:
        return {'quotation': q, 'notes': notes, 'spans': spans, 'pending_reason': None}
    return out


def verify(raw, result):
    spans = result['spans']
    quotations = spans.get('quotation_spans', [spans.get('quotation', [0, 0])])
    quotations = [s for s in quotations if s[0] < s[1]]
    notes = spans.get('notes', [])
    assert result['quotation'] == ''.join(raw[a:b] for a, b in quotations)
    assert result['notes'] == [raw[a:b] for a, b in notes]
    cursor = 0
    for begin, end in sorted(quotations + notes):
        assert begin == cursor and begin < end <= len(raw), (begin, end, cursor, len(raw))
        cursor = end
    assert cursor == len(raw)
    if result.get('pending_reason'):
        assert not result['quotation'] and result['notes'] == [raw]


def summarize(result):
    return {'quotation_sha256': digest(result['quotation'].encode()),
            'note_sha256': [digest(note.encode()) for note in result['notes']],
            'spans': result['spans'], 'pending_reason': result.get('pending_reason')}


groups = collections.OrderedDict()
snapshots = []
changed = []
counts = collections.Counter()
rule_counts = collections.Counter()
for prefix, language_info in importer.LANGUAGES.items():
    language = language_info[0]
    path = SOURCE / (prefix + '-nasai.json')
    raw = path.read_bytes()
    receipt = json.loads(path.with_suffix('.receipt.json').read_bytes())
    assert digest(raw) == receipt['sha256']
    data = importer.parse_json(raw.decode())
    snapshots.append({'provider_edition': prefix + '-nasai', 'sha256': digest(raw),
                      'rows': len(data['hadiths']), 'url': receipt['url']})
    for position, row in enumerate(data['hadiths']):
        text = row['text']
        identity = importer.typed_identity(row['hadithnumber'])
        previous = partition(text, 'nasai', language, old.split_source_reading)
        after = partition(text, 'nasai', language, current.split_source_reading)
        verify(text, previous)
        verify(text, after)
        counts['verified_fields'] += 1
        if after != previous:
            counts['matched_fields_' + language] += 1
            rule_counts[after['spans'].get('rule', 'unknown')] += 1
        decision = decisions.get(('nasai', prefix, identity))
        before_effective, after_effective = dict(previous), dict(after)
        if decision:
            q, n, s = importer.apply_reviewed_span(text, decision)
            before_effective = after_effective = {'quotation': q, 'notes': n, 'spans': s, 'pending_reason': None}
            verify(text, after_effective)
        old_item = {'row': row, 'metadata': data['metadata'], **before_effective}
        new_item = {'row': row, 'metadata': data['metadata'], **after_effective}
        if decision and decision.get('action') != 'source_context_only':
            old_item['reviewed_source_span'] = new_item['reviewed_source_span'] = decision
        group = groups.setdefault(identity, {'before': {}, 'after': {}, 'changes': []})
        group['before'][prefix] = old_item
        group['after'][prefix] = new_item
        if after != previous:
            effective = (before_effective['quotation'], before_effective['notes'], before_effective.get('pending_reason')) != (
                after_effective['quotation'], after_effective['notes'], after_effective.get('pending_reason'))
            record = {'provider_book': 'nasai', 'provider_edition': prefix + '-nasai',
                      'typed_hadithnumber': identity, 'source_json_pointer': '/hadiths/' + str(position) + '/text',
                      'source_snapshot_sha256': digest(raw), 'source_text_sha256': digest(text.encode()),
                      'source_characters': len(text), 'before': summarize(previous), 'after': summarize(after),
                      'effective_reading_changed': effective, 'catalog_reviewed_span_preserved': bool(decision)}
            changed.append(record)
            group['changes'].append(record)
            counts['effective_changed_fields_' + language] += effective

baseline_rows = {x['typed_hadithnumber']: x for x in [json.loads(line) for line in gzip.open(
    BASELINE / importer.IMPORT / 'classification/nasai.jsonl.gz', 'rt')]}
outcomes = []
for identity, group in groups.items():
    before = importer.classify_group(group['before'])
    after = importer.classify_group(group['after'])
    baseline = baseline_rows[identity]['classification']
    evidence_before = attribution.explicit_report_evidence(group['before'])
    evidence_after = attribution.explicit_report_evidence(group['after'])
    if group['changes'] or before != after:
        outcome = {'typed_hadithnumber': identity, 'baseline_final_v1': baseline,
                   'current_classifier_before_boundaries': before, 'after_boundaries': after,
                   'guarded_evidence_before': evidence_before, 'guarded_evidence_after': evidence_after,
                   'changed_language_fields': [r['provider_edition'] for r in group['changes']]}
        outcomes.append(outcome)
        for record in group['changes']:
            record['baseline_final_v1_classification'] = baseline['classification']
            record['current_classifier_before_boundaries'] = before['classification']
            record['after_boundary_classification'] = after['classification']
    if group['changes']:
        counts['affected_provider_occurrences'] += 1
        counts['affected_baseline_' + baseline['classification']] += 1
        counts['affected_after_' + after['classification']] += 1
        if baseline['classification'] != 'hadith' and before['classification'] == 'hadith':
            counts['affected_newly_matched_classifier_occurrences'] += 1
    if before['classification'] == 'hadith' and after['classification'] != 'hadith':
        counts['classifier_promotions_prevented_or_existing_matn_demoted'] += 1

abu_path = SOURCE / 'eng-abudawud.json'
abu_data = importer.parse_json(abu_path.read_text())
abu_changed = []
for row in abu_data['hadiths']:
    before = partition(row['text'], 'abudawud', 'en', old.split_source_reading)
    after = partition(row['text'], 'abudawud', 'en', current.split_source_reading)
    if before != after:
        verify(row['text'], after)
        abu_changed.append(importer.typed_identity(row['hadithnumber']))
assert abu_changed == ['2251'], abu_changed
index, abu = next((i, r) for i, r in enumerate(abu_data['hadiths']) if importer.typed_identity(r['hadithnumber']) == '2251')
abu_out = partition(abu['text'], 'abudawud', 'en', current.split_source_reading)
verify(abu['text'], abu_out)
assert len(abu_out['spans']['quotation_spans']) == 2
abu_proof = {'provider_book': 'abudawud', 'typed_hadithnumber': '2251', 'provider_edition': 'eng-abudawud',
             'source_json_pointer': '/hadiths/' + str(index) + '/text', 'source_snapshot_sha256': digest(abu_path.read_bytes()),
             'source_text_sha256': digest(abu['text'].encode()), 'after': summarize(abu_out),
             'one_provider_occurrence_preserved': True}

assert current_sha == digest((HERE / 'scripts/fawaz_boundaries.py').read_bytes()), 'Boundary file changed during audit'
assert attribution_sha == digest((HERE / 'scripts/fawaz_attribution.py').read_bytes()), 'Attribution file changed during audit'
summary = dict(counts)
summary['matched_fields_total'] = len(changed)
summary['effective_changed_fields_total'] = sum(r['effective_reading_changed'] for r in changed)
summary['abudawud_english_rows_checked_for_unintended_changes'] = len(abu_data['hadiths'])
summary['abudawud_english_changed_ids'] = abu_changed
summary['pending_language_fields'] = [{key: r[key] for key in ('provider_edition', 'typed_hadithnumber')}
                                      for r in changed if r['after']['pending_reason']]
summary['classification_demotions'] = [r['typed_hadithnumber'] for r in outcomes
    if r['current_classifier_before_boundaries']['classification'] == 'hadith' and r['after_boundaries']['classification'] != 'hadith']
proof = {'schema': 'hadith-bank-fawaz-source-boundary-batch-audit-v1', 'revision': importer.REVISION,
         'scope': 'Exact source fidelity of all four pinned Nasai editions and every changed language field; source-local compiler/grade/bibliography separation, not independent authenticity or semantic translation certification.',
         'boundary_helper_sha256': current_sha, 'attribution_helper_sha256': attribution_sha,
         'importer_sha256': digest((HERE / 'scripts/import_fawaz_bulk.py').read_bytes()),
         'catalog_decisions_sha256_at_start': digest(decision_bytes), 'source_snapshots': snapshots,
         'original_source_bytes_changed': False, 'provider_id_merges': 0, 'summary': summary,
         'rule_counts': dict(rule_counts), 'changed_fields': changed, 'affected_outcomes': outcomes,
         'abudawud2251': abu_proof}
out = args.output.resolve()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
print(json.dumps({'path': str(out), 'sha256': digest(out.read_bytes()), 'bytes': out.stat().st_size,
                  'summary': summary, 'boundary_helper_sha256': current_sha}, ensure_ascii=False))
