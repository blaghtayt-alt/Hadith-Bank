#!/usr/bin/env python3
"""Verify and archive the four exact independent boundary amendments."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REL = Path('imports/web-deenhindi-20261112/reviews')
EVID = REL / 'checkpoint5589-bukhari20-ibnmajah5-20261113'
ACTIVE = REL / 'source-review-checkpoint5589-bukhari20-ibnmajah5-20261113.json.gz'
OLD_MANIFEST_SHA = 'b0374c06bf91919c44bf18dbb6bba0ae2dc11fd869c31e4075a2b928a3806de7'
FINDINGS_SHA = '296611a02dfc733551ddf582723fcbe5723ad9304abbe06ec7ba18970c31aa1d'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': sha(raw),
        'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def preserve(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw
    else:
        path.write_bytes(raw)


def masks(field, size):
    result = [None] * size
    for span in field['spans']:
        identity = {k: v for k, v in span.items() if k not in ('start', 'end', 'sha256')}
        for i in range(span['start'], span['end']):
            assert result[i] is None
            result[i] = identity
    return result


def main():
    old_manifest_path = HERE / 'delivery-manifest-v1.json'
    assert sha(old_manifest_path.read_bytes()) == OLD_MANIFEST_SHA
    before_manifest = json.loads(old_manifest_path.read_bytes())
    for item in before_manifest['files']:
        assert binding(Path(item['local_path'])) == {k: item[k] for k in ('bytes', 'sha256', 'git_blob_sha1')}
    old = json.loads(gzip.decompress((HERE / 'publish-v1' / ACTIVE).read_bytes()))
    new = json.loads(gzip.decompress((HERE / 'publish-v2' / ACTIVE).read_bytes()))
    assert {k: v for k, v in old.items() if k != 'records'} == {k: v for k, v in new.items() if k != 'records'}
    source = {f"deenhindi-{r['collection']}:{r['number']}": r['source_record'] for r in map(json.loads, (HERE / 'input/cohort.jsonl').read_text().splitlines())}
    cuts = {
        ('deenhindi-bukhari:2349', 'hi'): (193, 204, '(इस बात की)'),
        ('deenhindi-bukhari:2349', 'ur'): (172, 185, '( اس بات کی )'),
        ('deenhindi-bukhari:2382', 'hi'): (314, 325, '(ये कहा कि)'),
        ('deenhindi-bukhari:2382', 'ur'): (274, 287, '( یہ کہا کہ )'),
    }
    unchanged_fields, unchanged_parents, removed_chars, removed_bytes = 0, 0, 0, 0
    changes = []
    for before, after in zip(old['records'], new['records']):
        assert before['id'] == after['id']
        assert {k: v for k, v in before.items() if k != 'field_reviews'} == {k: v for k, v in after.items() if k != 'field_reviews'}
        if before == after:
            unchanged_parents += 1
        for bf, af in zip(before['field_reviews'], after['field_reviews']):
            key = (before['id'], bf['language'])
            assert bf['language'] == af['language']
            if key not in cuts:
                assert bf == af, key
                unchanged_fields += 1
                continue
            assert {k: v for k, v in bf.items() if k not in ('spans', 'reason')} == {k: v for k, v in af.items() if k not in ('spans', 'reason')}
            text = source[before['id']][bf['source_field']]
            start, end, literal = cuts[key]
            assert text[start:end] == literal
            bm, am = masks(bf, len(text)), masks(af, len(text))
            assert all(bm[i] is not None and am[i] is None for i in range(start, end))
            assert all(am[i] == bm[i] for i in range(len(text)) if not start <= i < end)
            removed_chars += end - start
            removed_bytes += len(literal.encode())
            changes.append({'id': key[0], 'language': key[1], 'source_field_sha256': bf['text_sha256'],
                'start': start, 'end': end, 'text': literal, 'operation': 'move_exact_source_apparatus_to_context',
                'all_other_selected_positions_and_component_metadata_unchanged': True})
    assert len(changes) == 4 and unchanged_fields == 121 and unchanged_parents == 23
    assert (removed_chars, removed_bytes) == (48, 90)
    findings = HERE.parent / 'phase16-checkpoint5589-bukhari-ibnmajah25-independent-audit/independent-boundary-findings-v1.json'
    assert sha(findings.read_bytes()) == FINDINGS_SHA
    out = HERE / 'publish-v2'
    archive = out / EVID / 'independent-boundary-amendment-v2'
    archived = []
    for item in before_manifest['files']:
        old_path, new_path = Path(item['local_path']), out / item['path']
        if not new_path.exists() or old_path.read_bytes() != new_path.read_bytes():
            target = archive / ('previous-' + old_path.name)
            preserve(target, old_path.read_bytes())
            archived.append({'original_path': item['path'], 'archived_path': target.relative_to(out).as_posix(), **binding(target)})
    preserve(archive / 'previous-delivery-manifest-v1.json', old_manifest_path.read_bytes())
    preserve(archive / 'independent-boundary-findings-v1.json', findings.read_bytes())
    preserve(archive / 'finalize_v2.py', Path(__file__).read_bytes())
    receipt = {'schema': 'hadith-bank-exact-independent-boundary-amendment-v1', 'status': 'PASS',
        'source_checkpoint': '5589a3ffc3b43c3324ae26f2b6c4d33152834456',
        'previous_delivery_manifest_sha256': OLD_MANIFEST_SHA,
        'previous_active_sha256': sha((HERE / 'publish-v1' / ACTIVE).read_bytes()),
        'active_sha256': sha((out / ACTIVE).read_bytes()), 'independent_findings_sha256': FINDINGS_SHA,
        'complete_source_first_reading_receipt_sha256': sha((HERE / 'complete-source-first-reading-receipt.json').read_bytes()),
        'exact_changed_fields': len(changes), 'unchanged_field_decisions': unchanged_fields,
        'unchanged_complete_parent_records': unchanged_parents,
        'all_parent_metadata_exact': True, 'source_objects_unchanged': True,
        'selected_characters_moved_to_context': removed_chars, 'selected_utf8_bytes_moved_to_context': removed_bytes,
        'newly_selected_characters': 0, 'component_attributions_types_and_families_changed': 0,
        'parent_dispositions_or_language_reading_claims_changed': 0,
        'registered': 25, 'resolved_source_only': 0, 'complete_read_fields': 50,
        'admitted_fields': 50, 'unread_context_fields': 75, 'native_lossless_partitions': 125,
        'all_previous_payload_files_and_manifest_unchanged': True,
        'changes': changes, 'versioned_before_evidence': archived}
    preserve(archive / 'amendment-receipt.json', encoded(receipt))
    # The candidate has not yet been handed off: finalize its two package indexes
    # after archiving the immutable earlier payload and exact amendment evidence.
    portable = out / EVID / 'package-file-manifest.json'
    prior_portable = json.loads(portable.read_bytes())
    def file_binding(p, local=False):
        result = {'path': p.relative_to(out).as_posix(), **binding(p)}
        if local:
            result.update(local_path=str(p.resolve()), source_path=str(p.resolve()))
        return result
    prior_portable['files'] = [file_binding(p) for p in sorted(out.rglob('*')) if p.is_file() and p != portable]
    prior_portable['independent_boundary_amendment_receipt'] = (archive / 'amendment-receipt.json').relative_to(out).as_posix()
    portable.write_bytes(encoded(prior_portable))
    delivery = {'output_root': str(out.resolve()), 'summary': prior_portable['summary'],
        'files': [file_binding(p, True) for p in sorted(out.rglob('*')) if p.is_file()]}
    (HERE / 'delivery-manifest-v2.json').write_bytes(encoded(delivery))
    for item in before_manifest['files']:
        assert binding(Path(item['local_path'])) == {k: item[k] for k in ('bytes', 'sha256', 'git_blob_sha1')}
    assert sha(old_manifest_path.read_bytes()) == OLD_MANIFEST_SHA
    print(json.dumps({'manifest': binding(HERE / 'delivery-manifest-v2.json'),
        'active': binding(out / ACTIVE), 'files': len(delivery['files']),
        'bytes': sum(x['bytes'] for x in delivery['files']), 'amendment_receipt': binding(archive / 'amendment-receipt.json')}, indent=2))


if __name__ == '__main__':
    main()
