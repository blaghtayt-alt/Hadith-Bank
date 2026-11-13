"""Freeze independent boundary findings and reopen all saved source pairs."""
from pathlib import Path
import gzip, hashlib, json, sys

ROOT = Path(__file__).resolve().parent
PRIMARY = ROOT.parent / 'phase16-checkpoint5589-bukhari-ibnmajah25-review'
PARTITION = ROOT.parent / 'phase16-checkpoint5589-input-partitions/checkpoint-bukhari20-ibnmajah5'
SOURCES = ROOT.parent / 'phase15-successor-acquisition-monitor/held-evidence/sources'
sys.path.insert(0, str(ROOT.parent / 'hindi-resolve/work/scripts'))
import import_deenhindi as importer
sha = lambda data: hashlib.sha256(data).hexdigest()
enc = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
git = lambda data: hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

source_bytes = (ROOT / 'input/cohort.jsonl').read_bytes()
assert sha(source_bytes) == 'fc4811705927bd5b345dacd6f2aa741eecc5a9b0e4796ed76d559b43ac33c09b'
rows = [json.loads(line) for line in source_bytes.splitlines()]
by_id = {'deenhindi-' + row['collection'] + ':' + row['number']: row for row in rows}
manifest_bytes = (PRIMARY / 'delivery-manifest-v1.json').read_bytes()
assert sha(manifest_bytes) == 'b0374c06bf91919c44bf18dbb6bba0ae2dc11fd869c31e4075a2b928a3806de7'
manifest = json.loads(manifest_bytes)
for item in manifest['files']:
    data = Path(item['local_path']).read_bytes()
    assert sha(data) == item['sha256'] and len(data) == item['bytes']
active = next(item for item in manifest['files'] if '/source-review-' in item['path'])
active_bytes = Path(active['local_path']).read_bytes()
assert sha(active_bytes) == '40fda5a93fc01c65c2fd7594a3b465b80b4a0fab09df9c01cdd242819c89e149'
decisions = {row['id']: row for row in json.loads(gzip.decompress(active_bytes))['records']}
read_bytes = (ROOT / 'complete-independent-source-first-readings.json').read_bytes()
assert sha(read_bytes) == '01af6cd8922ddbf2d77731d48f731f02644a8b1b511741f2c4266cf9576a8595'
requested = []
for number, language, literal, reason in [
    ('2349', 'hi', '(इस बात की)', 'This deictic gloss repeats the complete surrounding happiness/cause construction. Preserve Sahl’s actual narrative and every position of Abu Hazim’s separately qualified uncertainty.'),
    ('2349', 'ur', '( اس بات کی )', 'The source already supplies the full happiness and following cause. This deictic restatement is explanatory context, without changing the actual meal account or Abu Hazim’s own material uncertainty.'),
    ('2382', 'hi', '(ये कहा कि)', 'This said-formula is transmission wording apparatus. Both numerical alternatives, the explicit OR and all Dawud’s named material-doubt component must remain selected; the quantity is not settled.'),
    ('2382', 'ur', '( یہ کہا کہ )', 'The parenthesis is a formula introducing alternative transmitted wording. Preserve the two thresholds, OR and Dawud’s full named uncertainty; only this formula becomes context.'),
]:
    oid = 'deenhindi-bukhari:' + number
    source_field = importer.LANGUAGE_FIELDS[language]
    text = by_id[oid]['source_record'][source_field]
    assert text.count(literal) == 1
    a = text.index(literal); b = a + len(literal)
    decision = next(field for field in decisions[oid]['field_reviews'] if field['language'] == language)
    positions = {i for span in decision['spans'] for i in range(span['start'], span['end'])}
    assert set(range(a, b)) <= positions
    requested.append({'occurrence_id': oid, 'language': language, 'source_field': source_field,
                      'source_text_sha256': sha(text.encode()), 'start': a, 'end': b,
                      'text': literal, 'sha256': sha(literal.encode()), 'utf8_bytes': len(literal.encode()),
                      'requested_disposition': 'context', 'reason': reason,
                      'source_record_sha256': sha(importer.json_bytes(by_id[oid]['source_record']))})
findings = {'schema': 'hadith-bank-independent-boundary-findings-v1',
    'source_commit': '5589a3ffc3b43c3324ae26f2b6c4d33152834456',
    'independent_source_first_receipt_sha256': sha(read_bytes),
    'primary_v1_manifest_sha256': sha(manifest_bytes), 'primary_v1_active_sha256': sha(active_bytes),
    'complete_source_fields_independently_read': 50, 'all50_candidate_fields_and_actual_masks_inspected': True,
    'all25_parent_dispositions_supported': True, 'requested_changes': requested,
    'requested_occurrences': 2, 'requested_fields': 4, 'removed_characters': 48, 'removed_utf8_bytes': 90,
    'no_requested_parent_or_component_identity_changes': True,
    'explicit_initial_note_refinements': [
        {'occurrence_id': 'deenhindi-bukhari:2345', 'languages': ['hi', 'ur'],
         'initial_view': 'The first independent notes considered the precaution parenthesis redundant with the stated fear.',
         'refinement': 'After rechecking the whole report and attribution split, retain the source’s precautionary mode of the actual discontinuance. It qualifies the response to possible unknown guidance, without converting that possibility into an established Prophetic prohibition. The initial notes remain unchanged.'},
        {'occurrence_id': 'deenhindi-bukhari:2375', 'languages': ['hi', 'ur'],
         'initial_view': 'The first notes considered the thought/idea parenthesis redundant with the earlier plan.',
         'refinement': 'Retain the source’s explicit prospective intention bridge for the income-funded marriage meal. It describes a plan in the actual narrator’s account rather than an accomplished outcome; the impending-marriage relation and later transmitter voice switch remain as well. Initial notes remain unchanged.'},
        {'occurrence_id': 'deenhindi-bukhari:2334', 'languages': ['hi', 'ur'],
         'initial_view': 'The first notes called for preservation of the source ellipsis before the chapter label.',
         'refinement': 'The candidate preserves the entire ellipsis and heading as visible context after a complete report sentence. No supplied report words or omission-dependent qualification are lost; no punctuation-only restoration is requested.'},
    ],
    'supported_specific_scopes': ['2325 mixed-script Hindi and actual parties', '2327 unnamed passive prohibition issuer',
        '2346/2347 exact separate occurrences and Layth legal context', '2349 named material uncertainty',
        '2375 damaged Hindi inquiry/action seams without Urdu repair', '2376 participant/comparison/afterlife scopes',
        '2382 both quantity alternatives and named doubt', '2303 purpose/need condition and footnote-only context'],
    'independent_pro_qc': 'not_performed', 'source_http_requests': 0, 'github_writes': 0}
dest = ROOT / 'independent-boundary-findings-v1.json'
assert not dest.exists(); dest.write_bytes(enc(findings))

partition_bytes = (PARTITION / 'source-verification.json').read_bytes()
assert sha(partition_bytes) == '8aa53008d7cdf677ca9600991fec9748229586d0d789053273cb76b13c487c60'
partition = json.loads(partition_bytes)
verified = []
for record in partition['records']:
    saved = by_id[record['occurrence_id']]
    assert record['source_record_sha256'] == sha(importer.json_bytes(saved['source_record']))
    file_checks = []
    for receipt in record['files']:
        path = SOURCES / receipt['path']
        assert not path.is_symlink() and '..' not in Path(receipt['path']).parts
        stored = path.read_bytes(); plain = gzip.decompress(stored)
        assert len(stored) == receipt['stored_bytes'] and sha(stored) == receipt['stored_sha256']
        assert len(plain) == receipt['plain_bytes'] and sha(plain) == receipt['plain_sha256']
        assert git(stored) == receipt['git_blob_sha1']
        if receipt['kind'] == 'raw':
            body, reference = importer.parse_record(plain, saved['collection'], saved['number'])
            assert body == saved['source_record'] and reference == saved['source_reference_verbatim']
        else:
            expected = {k: saved[k] for k in ('schema', 'collection', 'number', 'snapshot', 'source_record', 'source_reference_verbatim')}
            expected['classification'] = saved['intake_classification']
            assert json.loads(plain) == expected
        file_checks.append({k: v for k, v in receipt.items() if k != 'shared_local_path'})
    verified.append({'occurrence_id': record['occurrence_id'], 'source_record_sha256': record['source_record_sha256'],
                     'source_reference_verbatim': saved['source_reference_verbatim'], 'files': file_checks,
                     'raw_reparse_exact': True, 'full_immutable_parsed_object_exact': True})
assert len(verified) == 25 and sum(len(x['files']) for x in verified) == 50
proof = {'schema': 'hadith-bank-independent-saved-source-verification-v1', 'result': 'PASS',
         'source_commit': partition['source_commit'], 'source_files': 50, 'raw_reparses': 25,
         'original_cohort_sha256': sha(source_bytes), 'partition_proof_sha256': sha(partition_bytes),
         'authoritative_new100_manifest_sha256': partition['source_manifest_sha256'],
         'source_http_requests': 0, 'github_writes': 0, 'records': verified}
proof_path = ROOT / 'independent-source-verification.json'
assert not proof_path.exists(); proof_path.write_bytes(enc(proof))
print(json.dumps({'findings_sha256': sha(dest.read_bytes()), 'source_proof_sha256': sha(proof_path.read_bytes()),
                  'requested_fields': 4, 'source_files': 50, 'raw_reparses': 25}, indent=2))
