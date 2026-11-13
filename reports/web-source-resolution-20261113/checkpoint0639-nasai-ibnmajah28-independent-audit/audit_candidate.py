"""Independent audit after 65 actual original-field readings.

Only isolated validation/output files are written. Source and owner candidates
remain untouched. Semantic masks are explicitly frozen after the independent
reading and complete candidate-boundary inspection; no classifier is used.
"""
from pathlib import Path
import argparse
import collections
import copy
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
SCRIPTS = WORK / 'hindi-resolve/work/scripts'
sys.path.insert(0, str(SCRIPTS))
import import_deenhindi as importer
from web_source_reviews import SourceReviews

OWNER = WORK / 'phase15-checkpoint0639-nasai-ibnmajah28-review'
CENTRAL = WORK / 'phase13-successor-acquisition-monitor/held-evidence'
COMMIT = '0639af7fd15786284b4c413fced77e38eec8825a'
READING_SHA = 'ae3aca312883b0b07c343c1dbda696b5b090b5df7ba68b1238a32a2d3a32d4f3'
FIELDS = {'ar': 'textArabic', 'hi': 'translationHindi', 'ur': 'translationUrdu',
          'ur-Latn': 'translationUrduRoman', 'en': 'translationEnglish'}
EXCLUDED = {'deenhindi-nasai:2259', 'deenhindi-nasai:2295'}
SCRIPT_FIXES = {('deenhindi-ibnmajah:' + n, 'hi') for n in ['2223', '2249', '2251']}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gitsha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def jb(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def leaf_count(value):
    if isinstance(value, dict):
        return sum(leaf_count(v) for v in value.values())
    if isinstance(value, list):
        return sum(leaf_count(v) for v in value)
    return 1


def equal(before, after):
    assert before == after
    return leaf_count(before)


def binding(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': gitsha(data)}


def audit(manifest_name, manifest_sha, active_sha, final):
    receipt_path = ROOT / 'independent-complete-source-first-readings.json'
    assert sha(receipt_path.read_bytes()) == READING_SHA
    receipt = read(receipt_path)
    assert receipt['candidate_or_primary_notes_opened'] is False
    reading_fields = {(x['local_id'], x['language']): x for x in receipt['fields']}
    assert len(reading_fields) == 65
    source_rows = [json.loads(line) for line in (ROOT / 'input/cohort.jsonl').read_bytes().splitlines()]
    saved_by_id = {'deenhindi-' + x['collection'] + ':' + x['number']: x for x in source_rows}
    assert len(saved_by_id) == len(source_rows) == 28
    central_rows = {'deenhindi-' + x['collection'] + ':' + x['number']: x for x in
                    map(json.loads, (CENTRAL.parent / 'next-review-cohort/held-source-records.jsonl').read_bytes().splitlines())}
    assert all(central_rows[k] == v for k, v in saved_by_id.items())

    manifest_path = OWNER / manifest_name
    assert sha(manifest_path.read_bytes()) == manifest_sha
    manifest = read(manifest_path)
    repo = ROOT / 'validation' / ('final' if final else 'v1-native')
    frozen = []
    for item in manifest['files']:
        relative = Path(item['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        local = Path(item.get('local_path') or item['source_path'])
        assert local.is_file() and not local.is_symlink() and local.resolve().is_relative_to(OWNER)
        b = binding(local)
        assert b['sha256'] == item['sha256'] and b['bytes'] == item.get('bytes', item.get('size_bytes'))
        assert not item.get('git_blob_sha1') or b['git_blob_sha1'] == item['git_blob_sha1']
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(local.read_bytes())
        frozen.append({'path': item['path'], 'local_path': str(local), **b})
    assert len({x['path'] for x in frozen}) == len(frozen)
    item = next(x for x in frozen if '/source-review-' in x['path'])
    assert item['sha256'] == active_sha
    active = read(repo / item['path'])
    baseline = repo / active['source_ledger_path']
    assert sha(baseline.read_bytes()) == active['source_ledger_sha256']
    assert [json.loads(x) for x in gzip.decompress(baseline.read_bytes()).splitlines()] == source_rows
    decisions = {d['id']: d for d in active['records']}
    assert len(decisions) == len(active['records']) == 28 and set(decisions) == set(saved_by_id)

    authority = read(CENTRAL / 'evidence-manifest.json')
    assert authority['saved_head'] == COMMIT
    state_entries = read(CENTRAL / 'held-state-entries.json')
    source_root = CENTRAL / 'sources'
    engine = SourceReviews(repo, 'deenhindi')
    expected = read(ROOT / 'independently-accepted-boundary-plan.json') if final else None
    expected_by_key = {(x['id'], x['language']): x for x in expected['fields']} if final else {}
    source_proof, field_proof = [], []
    counts = collections.Counter()
    metadata = collections.Counter()
    script_fixes = []
    for identity, saved in saved_by_id.items():
        key = saved['collection'] + ':' + saved['number']
        decision = decisions[identity]
        entry = state_entries[key]
        for desc in [saved['snapshot'], entry['parsed']]:
            plain = importer.checked_bytes(source_root, desc)
            path = source_root / desc['path']
            given = authority['files'][desc['path']]
            b = binding(path)
            assert b['sha256'] == given['sha256'] and b['git_blob_sha1'] == given['git_blob_sha1']
            assert b['bytes'] == given['bytes']
            source_proof.append({'id': identity, 'path': desc['path'], **b, 'plain_sha256': sha(plain)})
        parsed = json.loads(importer.checked_bytes(source_root, entry['parsed']))
        assert entry['parsed']['path'] == saved['parsed_path']
        for name in ['collection', 'number', 'source_record', 'source_reference_verbatim', 'snapshot']:
            assert parsed[name] == saved[name]
        assert parsed['classification'] == saved.get('intake_classification', saved['classification'])
        record, reference = importer.parse_record(importer.checked_bytes(source_root, saved['snapshot']),
                                                  saved['collection'], saved['number'])
        assert record == saved['source_record'] and reference == saved['source_reference_verbatim']
        assert decision['source_record_sha256'] == sha(importer.json_bytes(record))
        assert decision['source_reference_verbatim'] == reference
        original = importer.canonical_record(saved)
        revised, action = engine.apply(copy.deepcopy(original), saved=saved)
        assert action == decision['decision'] == ('exclude' if identity in EXCLUDED else 'register')
        counts[action] += 1
        for name, value in original.items():
            if name not in ['text', 'language_versions', 'review', 'content_kind', 'extraction']:
                metadata['parent'] += equal(value, revised[name])
        fields = {f['language']: f for f in decision['field_reviews']}
        assert len(fields) == len(decision['field_reviews']) == 5 and set(fields) == set(FIELDS)
        assert len(original['language_versions']) == len(revised['language_versions']) == 5
        for before, after in zip(original['language_versions'], revised['language_versions']):
            lang = before['language']
            f = fields[lang]
            text = record[FIELDS[lang]]
            assert before['text'] == text and f['source_field'] == FIELDS[lang]
            assert f['text_sha256'] == sha(text.encode()) and f['text_chars'] == len(text)
            reviewed = (key, lang) in reading_fields
            assert f['reviewed'] is reviewed
            assert f['chars_reviewed'] == (len(text) if reviewed else 0)
            assert f['bytes_reviewed'] == (len(text.encode()) if reviewed else 0)
            spans = f['spans']
            selected = [False] * len(text)
            for s in spans:
                a, b = s['start'], s['end']
                assert 0 <= a < b <= len(text) and sha(text[a:b].encode()) == s['sha256']
                assert not any(selected[a:b])
                selected[a:b] = [True] * (b - a)
                assert s['speaker'].strip() and s['report_type'].strip()
            if reviewed:
                read_note = reading_fields[(key, lang)]
                assert read_note['sha256'] == sha(text.encode())
                assert read_note['characters'] == len(text) and read_note['utf8_bytes'] == len(text.encode())
                counts['read_fields'] += 1
                counts['read_chars'] += len(text)
                counts['read_bytes'] += len(text.encode())
                counts['admitted_fields' if spans else 'reviewed_context_fields'] += 1
                if final:
                    plan = expected_by_key[(identity, lang)]
                    assert plan['source_field_sha256'] == sha(text.encode())
                    accepted = [True] * len(text)
                    for a, b in plan['context_ranges']:
                        accepted[a:b] = [False] * (b - a)
                    assert selected == accepted, (identity, lang, 'independent semantic mask differs')
            else:
                counts['unread_fields'] += 1
                assert not spans and after['text'] is None
            assert (after['text'] or '') == ''.join(text[s['start']:s['end']] for s in spans)
            pieces = [(s['start'], s['end'], text[s['start']:s['end']]) for s in spans]
            pieces += [(c['source_span'][0], c['source_span'][1], c['text']) for c in
                       after.get('comments', []) if c.get('source_span') is not None]
            cursor = 0
            for a, b, t in sorted(pieces):
                assert a == cursor and text[a:b] == t
                cursor = b
            assert cursor == len(text) and ''.join(t for _, _, t in sorted(pieces)) == text
            counts['partitions'] += 1
            for name, value in before.items():
                if name in ['text', 'scope', 'source', 'comments']:
                    continue
                if name == 'script' and (identity, lang) in SCRIPT_FIXES:
                    assert value == 'Deva' and after[name] == f['observed_script'] == 'Latn'
                    assert f['source_script_note']
                    script_fixes.append({'id': identity, 'language': lang, 'before': value, 'after': after[name]})
                else:
                    metadata['language'] += equal(value, after[name])
            for name, value in before['source'].items():
                metadata['source'] += equal(value, after['source'][name])
            for i, comment in enumerate(before.get('comments', [])):
                for name, value in comment.items():
                    metadata['previous_comments'] += equal(value, after['comments'][i][name])
            if reviewed:
                field_proof.append({'id': identity, 'language': lang, 'source_field_sha256': sha(text.encode()),
                                    'characters': len(text), 'utf8_bytes': len(text.encode()),
                                    'selected_mask_sha256': sha(bytes(selected)), 'spans': spans,
                                    'own_complete_reading': True, 'exact_independent_mask_check': final})
        if identity == 'deenhindi-nasai:2275':
            for lang in FIELDS:
                spans = fields[lang]['spans']
                assert len({s['component_id'] for s in spans}) == 2
                assert len({s['source_report_family_id'] for s in spans}) == 1
            assert 'sick' in json.dumps(fields['en']['source_text_annotations'])
            assert 'nursing' in json.dumps(fields['en']['source_text_annotations'])
        if identity == 'deenhindi-nasai:2276' and final:
            for lang in ['hi', 'ur']:
                spans = fields[lang]['spans']
                assert len({s['component_id'] for s in spans}) == 2
                assert len({s['source_report_family_id'] for s in spans}) == 1
        if identity in EXCLUDED:
            assert all(f['reviewed'] and not f['spans'] for f in fields.values())
    engine.finish()
    assert (counts['register'], counts['exclude'], counts['partitions']) == (26, 2, 140)
    assert (counts['read_fields'], counts['read_chars'], counts['read_bytes']) == (65, 20762, 40583)
    assert (counts['admitted_fields'], counts['reviewed_context_fields'], counts['unread_fields']) == (55, 10, 75)
    assert len(script_fixes) == 3 and len(source_proof) == 56
    for item in frozen:
        assert binding(Path(item['local_path']))['sha256'] == item['sha256']
    assert sha(manifest_path.read_bytes()) == manifest_sha
    report = {'schema': 'hadith-bank-independent-reading-and-native-audit-v1',
              'status': 'PASS' if final else 'NATIVE_PROVENANCE_PASS_SEMANTIC_AMENDMENT_PENDING',
              'source_checkpoint': COMMIT, 'candidate_manifest_sha256': manifest_sha,
              'active_ledger_path': next(x['path'] for x in frozen if '/source-review-' in x['path']),
              'active_ledger_sha256': active_sha, 'baseline_path': active['source_ledger_path'],
              'baseline_sha256': active['source_ledger_sha256'], 'frozen_candidate_files_checked': len(frozen),
              'all_owner_files_unchanged': True, 'source_first_reading_receipt_sha256': READING_SHA,
              'counts': dict(counts), 'source_metadata_leaf_equalities': dict(metadata),
              'source_metadata_leaf_equalities_total': sum(metadata.values()),
              'source_snapshot_files_reopened': 56, 'raw_reparses': 28,
              'all_complete_source_objects_and_references_equal': True,
              'all_stored_plain_and_git_blob_hashes_checked': True,
              'source_evidence_manifest_sha256': sha((CENTRAL / 'evidence-manifest.json').read_bytes()),
              'script_corrections': script_fixes, 'source_review_engine_sha256': engine.engine_sha256,
              'source_parser_sha256': sha(Path(importer.__file__).read_bytes()),
              'semantic_boundary_plan_sha256': sha((ROOT / 'independently-accepted-boundary-plan.json').read_bytes()) if final else None,
              'required_amendments': [] if final else ['Eight exact source-scope restorations and two same-family event-voice splits'],
              'no_neighbor_identity_or_translation_fill': True, 'source_http_requests': 0, 'github_mutations': 0,
              'independent_pro_qc': 'not_performed',
              'limitations': 'This independently read, source-bound candidate only; no authenticity certification or live deployment claim.'}
    suffix = 'final' if final else 'v1-preflight'
    (ROOT / ('native-source-audit-' + suffix + '.json')).write_bytes(jb(report))
    (ROOT / ('field-and-source-proof-' + suffix + '.json.gz')).write_bytes(gzip.compress(jb({
        'fields': field_proof, 'source_files': source_proof,
        'candidate_files': [{k: v for k, v in f.items() if k != 'local_path'} for f in frozen]}), mtime=0))
    print(json.dumps({'status': report['status'], 'counts': dict(counts),
                      'metadata_equalities': sum(metadata.values()), 'report_sha256': sha(jb(report))}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--active-sha256', required=True)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    audit(args.manifest, args.manifest_sha256, args.active_sha256, args.final)
