"""Verify and archive the exact post-reading Bukhari20 prefatory-route amendment."""
from pathlib import Path
import copy
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
REL = Path('imports/web-deenhindi-20261112/reviews')
EVID = REL / 'checkpoint3e574-bukhari20-20261113'
ACTIVE = REL / 'source-review-checkpoint3e574-bukhari20-20261113.json.gz'
ARCHIVE = EVID / 'independent-chain-amendment-v2' / 'previous-primary-v1'
FINDING_SHA = '3dee206d2a59d230fb9adc8706ec20c80afd978a7608531935de15622e7234a5'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def binding(raw):
    return {'bytes': len(raw), 'sha256': sha(raw),
            'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}


def put(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, ('immutable v2 archive collision', str(path))
    else:
        path.write_bytes(raw)


def positions(spans):
    return {p for span in spans for p in range(span['start'], span['end'])}


def validate_and_archive(out, decisions, sources, rendered):
    old_manifest_raw = (HERE / 'delivery-manifest-v1.json').read_bytes()
    assert sha(old_manifest_raw) == 'f4d36fd87bd822212fe13f06ba757cf91210d4f4bcc876c09d697db4fd14e333'
    old_manifest = json.loads(old_manifest_raw)
    old_active_raw = (HERE / 'publish-v1' / ACTIVE).read_bytes()
    assert sha(old_active_raw) == 'f76a7094f2af052c6764dd6f5fe78ab89f8b99d6a14820c1e9919d87f6be041d'
    before = json.loads(gzip.decompress(old_active_raw))
    after_raw = (out / ACTIVE).read_bytes()
    after = json.loads(gzip.decompress(after_raw))
    assert after['records'] == decisions
    assert {k: v for k, v in after.items() if k != 'records'} == {k: v for k, v in before.items() if k != 'records'}
    findings_raw = (HERE / 'supplemental-chain-findings-v1.json').read_bytes()
    assert sha(findings_raw) == FINDING_SHA
    finding_document = json.loads(findings_raw)
    findings = {(f['id'], f['language']): f for f in finding_document['findings']}
    assert len(findings) == 32
    source_map = {'deenhindi-' + s['collection'] + ':' + s['number']: s for s in sources}
    old_records = {r['id']: r for r in before['records']}
    new_records = {r['id']: r for r in after['records']}
    assert set(old_records) == set(new_records) == set(source_map) and len(new_records) == 20
    changed_fields, unchanged_fields, unchanged_parents = [], 0, 0
    removed_chars = removed_bytes = ranges = 0
    for identity, old in old_records.items():
        new = new_records[identity]
        assert {k: v for k, v in new.items() if k != 'field_reviews'} == {k: v for k, v in old.items() if k != 'field_reviews'}
        assert len(new['field_reviews']) == len(old['field_reviews']) == 5
        if new == old:
            unchanged_parents += 1
        for old_field, new_field in zip(old['field_reviews'], new['field_reviews']):
            language = old_field['language']; key = (identity, language)
            text = source_map[identity]['source_record'][old_field['source_field']]
            assert new_field['text_sha256'] == old_field['text_sha256'] == sha(text.encode())
            if key not in findings:
                assert new_field == old_field
                unchanged_fields += 1
                continue
            f = findings[key]
            assert sha(encoded(old_field)) == f['before_field_sha256']
            assert f['source_text_sha256'] == sha(text.encode())
            assert old_field['reviewed'] and new_field['reviewed']
            expected = copy.deepcopy(old_field)
            expected['spans'] = f['expected_spans']
            expected['action'] = 'excerpts'
            assert new_field == expected, (identity, language, 'unexpected field mutation')
            excluded = set()
            for cut in f['cuts']:
                a, b = cut['start'], cut['end']
                assert 0 <= a < b <= len(text) and text[a:b] == cut['text']
                assert sha(text[a:b].encode()) == cut['sha256']
                assert text.count(cut['text']) == 1
                excluded.update(range(a, b)); ranges += 1
            old_mask, new_mask = positions(old_field['spans']), positions(new_field['spans'])
            removed = old_mask & excluded
            assert new_mask == old_mask - excluded and not new_mask - old_mask
            assert len(removed) == f['newly_removed_selected_characters']
            byte_count = sum(len(text[p].encode()) for p in removed)
            assert byte_count == f['newly_removed_selected_utf8_bytes']
            removed_chars += len(removed); removed_bytes += byte_count
            # Every retained source position keeps its original type/voice/component/family.
            for span in new_field['spans']:
                prior = [s for s in old_field['spans'] if s['start'] <= span['start'] < span['end'] <= s['end']]
                assert len(prior) == 1
                assert {k: v for k, v in span.items() if k not in ('start', 'end', 'sha256')} == {
                    k: v for k, v in prior[0].items() if k not in ('start', 'end', 'sha256')}
                assert span['sha256'] == sha(text[span['start']:span['end']].encode())
            changed_fields.append({'id': identity, 'language': language,
                'source_text_sha256': sha(text.encode()),
                'before_field_sha256': sha(encoded(old_field)), 'after_field_sha256': sha(encoded(new_field)),
                'cuts': f['cuts'], 'removed_selected_characters': len(removed),
                'removed_selected_utf8_bytes': byte_count, 'added_selected_characters': 0,
                'all_retained_type_speaker_component_family_values_equal': True})
    assert len(changed_fields) == 32 and unchanged_fields == 68 and unchanged_parents == 4
    assert len({f['id'] for f in changed_fields}) == 16
    assert (removed_chars, removed_bytes, ranges) == (5210, 8028, 34)
    # The two actual2494 question clauses are separated by a context-only route;
    # they remain finite scene content, never swallowed by a blanket prefix.
    for lang, first_scene in [('hi', (218, 280)), ('ur', (186, 237))]:
        f = next(f for f in new_records['deenhindi-bukhari:2494']['field_reviews'] if f['language'] == lang)
        assert any(s['start'] == first_scene[0] and s['end'] == first_scene[1] for s in f['spans'])
        assert all(s['source_report_family_id'] == 'deenhindi-bukhari:2494:report-1' for s in f['spans'])
    archives = []
    for item in old_manifest['files']:
        original = Path(item['local_path']); raw = original.read_bytes()
        assert binding(raw) == {k: item[k] for k in ('bytes', 'sha256', 'git_blob_sha1')}
        archived = ARCHIVE / item['path']
        put(out / archived, raw)
        archives.append({'original_path': item['path'], 'archive_path': archived.as_posix(), **binding(raw)})
    assert len(archives) == 22
    archived_manifest = ARCHIVE / 'delivery-manifest-v1.json'
    put(out / archived_manifest, old_manifest_raw)
    # Keep the original independent PASS as explicitly historical evidence too.
    peer_root = HERE.parent / 'phase19-checkpoint3e574-bukhari20-independent-audit'
    prior_audit_manifest = (peer_root / 'delivery-manifest.json').read_bytes()
    assert sha(prior_audit_manifest) == '9c1df8f55f3b605248ebc11d45f170fe796fc07b7963a2dd1b26f376daf44274'
    put(out / EVID / 'independent-chain-amendment-v2' / 'previous-independent-PASS-manifest.json', prior_audit_manifest)
    old_report = None
    for item in json.loads(prior_audit_manifest)['files']:
        if item['sha256'] == 'fbc822211aebcc4a430489968fc60769a242fabcc7bafb00b8dd84f555da5fe1':
            old_report = Path(item['local_path']).read_bytes()
    assert old_report is not None and sha(old_report) == 'fbc822211aebcc4a430489968fc60769a242fabcc7bafb00b8dd84f555da5fe1'
    put(out / EVID / 'independent-chain-amendment-v2' / 'previous-independent-PASS-report.json', old_report)
    # Recheck every frozen source/primary input after serialization and archiving.
    assert (HERE / 'delivery-manifest-v1.json').read_bytes() == old_manifest_raw
    for item in old_manifest['files']:
        assert sha(Path(item['local_path']).read_bytes()) == item['sha256']
    assert len(rendered) == 20
    return {'schema': 'hadith-bank-versioned-chain-boundary-amendment-v1', 'status': 'PRIMARY_NATIVE_PASS_INDEPENDENT_V2_GATE_PENDING',
        'source_checkpoint': '3e574b9e7e4dd7cf8bc23232249004a18692c61c',
        'active_ledger_path': ACTIVE.as_posix(), 'before_active_sha256': sha(old_active_raw),
        'after_active_sha256': sha(after_raw), 'primary_v1_manifest_sha256': sha(old_manifest_raw),
        'independent_supplemental_findings_sha256': FINDING_SHA,
        'prior_independent_PASS_manifest_sha256': sha(prior_audit_manifest),
        'initial_source_first_receipt_sha256': '9b9f53ebd4769ce2cf43c1d680ad1466599cf63ccf4dbe29650b435c7f04f9a3',
        'initial_source_first_notes_and_v1_payloads_unchanged': True,
        'archived_original_payloads': archives, 'archived_original_manifest': archived_manifest.as_posix(),
        'refinement': 'The primary and first independent candidate review retained these prefatory routes. After the concrete supplemental consistency check, both reviewers accept exactly the enumerated pure transmission routes as source context, preserving all original names in metadata/context, all finite scenes and coherent final-reporter framing. This refinement does not retroactively rewrite either original reading or PASS.',
        'register': 20, 'source_only': 0, 'complete_fields_previously_read': 40,
        'characters_previously_read': 25526, 'utf8_bytes_previously_read': 42474,
        'new_fields_read': 0, 'selected_language_fields': 40, 'unread_context_fields': 60,
        'affected_occurrences': 16, 'affected_fields': 32, 'source_ranges': ranges,
        'removed_selected_characters': removed_chars, 'removed_selected_utf8_bytes': removed_bytes,
        'added_selected_characters': 0, 'unchanged_reviewed_fields': 8, 'unchanged_unread_fields': 60,
        'unchanged_complete_parents': unchanged_parents, 'all_parent_metadata_and_source_identities_equal': True,
        'every_retained_position_keeps_type_speaker_component_family': True,
        'fields': changed_fields, 'native_lossless_partitions': 100,
        'source_site_requests': 0, 'github_writes': 0, 'independent_pro_qc': 'not_performed'}
