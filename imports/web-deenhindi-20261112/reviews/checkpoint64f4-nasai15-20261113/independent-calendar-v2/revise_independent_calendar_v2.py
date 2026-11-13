#!/usr/bin/env python3
"""Apply two independently checked calendar-definition cuts; preserve all v1 evidence."""
from pathlib import Path
import copy
import gzip
import hashlib
import importlib.util
import json
import pprint
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OLD = HERE / 'publish'
OUT = HERE / 'publish-v2'
EVID = Path('imports/web-deenhindi-20261112/reviews/checkpoint64f4-nasai15-20261113')
ACTIVE = Path('imports/web-deenhindi-20261112/reviews/source-review-checkpoint64f4-nasai15-20261113.json.gz')
REV = EVID / 'independent-calendar-v2'
AUDIT = HERE.parent / 'phase23-checkpoint64f4-nasai15-independent-audit'
sha = lambda b: hashlib.sha256(b).hexdigest()
git = lambda b: hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
enc = lambda x: (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def put(path, data):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    assert not p.exists(), str(p)
    p.write_bytes(data)


def replace_once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def main():
    assert not OUT.exists() and not (HERE / 'delivery-manifest-v2.json').exists()
    before_manifest = (HERE / 'delivery-manifest-v1.json').read_bytes()
    assert sha(before_manifest) == 'f98a9ca4644a15fa2bfedfd2a1c571d84275a7e1f315a2090f3c0f4409e75438'
    old_manifest = json.loads(before_manifest)
    assert len(old_manifest['files']) == 21
    for f in old_manifest['files']:
        data = (OLD / f['path']).read_bytes()
        assert len(data) == f['bytes'] and sha(data) == f['sha256'] and git(data) == f['git_blob_sha1']
        put(REV / 'before-v1/payload' / f['path'], data)
    put(REV / 'before-v1/delivery-manifest-v1.json', before_manifest)
    bindings = {
        'independent-boundary-findings-v1.json': '2beb8ed12982a6b6376f5f82bc11adac312acd83d9a5fb5d60f3706add0ce8c1',
        'accepted-reviewed-field-plan-v1.json': 'e1d9160c8d2b0ae9d379a8412409357bf68c1c69e53267ca21bc384dd88c7f8a',
    }
    for name, expected in bindings.items():
        data = (AUDIT / name).read_bytes()
        assert sha(data) == expected
        put(REV / name, data)
    findings = json.loads((AUDIT / 'independent-boundary-findings-v1.json').read_bytes())
    plan = json.loads((AUDIT / 'accepted-reviewed-field-plan-v1.json').read_bytes())
    accepted = {(r['id'], r['language']): r for r in plan['fields']}
    assert len(accepted) == 30 and len(findings['required_findings']) == 2
    assert (plan['selected_characters_added'], plan['selected_characters_removed'], plan['selected_utf8_bytes_removed']) == (0, 33, 65)
    spec = importlib.util.spec_from_file_location('original_manual_rules', HERE / 'manual_rules.py')
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    specs = copy.deepcopy(original.SPECS)
    rule = specs['nasai:2732']
    for finding in findings['required_findings']:
        assert finding['id'] == 'deenhindi-nasai:2732'
        language = finding['language']
        rule['exclude_substrings'].setdefault(language, []).append(finding['text'])
        old_note = rule['field_notes'][language]
        note = replace_once(old_note, 'Hajj completion/10Dhul-Hijjah sacrifice/Mina-return/tawaf sequence.',
            'Hajj completion/Yawm al-Nahr sacrifice/Mina-return/tawaf sequence.')
        note = replace_once(note,
            'Preserve the finite yani chronology clauses, Urdu there place pointer,8Dhul-Hijjah condition and both10Dhul-Hijjah qualifications as material source rendering.',
            'Preserve the finite yani chronology clauses, Urdu there place pointer and8Dhul-Hijjah command-time condition as material source rendering. Refine the initial calendar decision: the tenth-Dhul-Hijjah parenthesis defines the already printed Yawm al-Nahr and remains complete source context; the named actual event day and sacrifice remain selected. The eighth-day wording supplies otherwise absent command timing and remains selected.')
        rule['field_notes'][language] = note
        rule['annotations'][language] = replace_once(rule['annotations'][language],
            'Only explicit note markers and duplicate technical slaughter/hady glosses become context;',
            'Explicit note markers, duplicate technical slaughter/hady glosses and the tenth-day calendar definition after the already named Yawm al-Nahr become context; the actual named day and eighth-day command timing remain selected;')
    for key in specs:
        if key != 'nasai:2732':
            assert specs[key] == original.SPECS[key]
    assert {k:v for k,v in rule.items() if k not in ('exclude_substrings','field_notes','annotations')} == {
        k:v for k,v in original.SPECS['nasai:2732'].items() if k not in ('exclude_substrings','field_notes','annotations')}
    (HERE / 'manual_rules_v2.py').write_text(
        '"""Two bounded calendar-definition refinements; original notes preserved in before-v1."""\nSPECS = '
        + pprint.pformat(specs, width=120, sort_dicts=False) + '\n', encoding='utf-8')
    builder = (HERE / 'build_delivery.py').read_text()
    builder = replace_once(builder,
        "    args = parser.parse_args()",
        "    parser.add_argument('--rules-file', type=Path, default=HERE / 'manual_rules.py')\n    args = parser.parse_args()")
    builder = replace_once(builder,
        "reading_module = module('manual_rules', HERE / 'manual_rules.py')",
        "reading_module = module('manual_rules', args.rules_file)")
    builder = replace_once(builder,
        "dump(HERE / 'validated-derived-records.json.gz', rendered)",
        "dump(HERE / 'validated-derived-records-v2.json.gz', rendered)")
    builder = replace_once(builder,
        "        target.write_bytes((HERE/name).read_bytes())",
        "        source = args.rules_file if name == 'manual_rules.py' else Path(__file__) if name == 'build_delivery.py' else HERE/name\n        target.write_bytes(source.read_bytes())")
    builder = builder.replace('delivery-manifest-v1.json', 'delivery-manifest-v2-intermediate.json')
    (HERE / 'build_delivery_v2.py').write_text(builder, encoding='utf-8')
    intermediate = HERE / 'delivery-manifest-v2-intermediate.json'
    subprocess.run([sys.executable, str(HERE / 'build_delivery_v2.py'),
        '--output-dir', str(OUT), '--manifest-file', str(intermediate),
        '--rules-file', str(HERE / 'manual_rules_v2.py')], check=True)
    before_bytes, after_bytes = (OLD / ACTIVE).read_bytes(), (OUT / ACTIVE).read_bytes()
    assert sha(before_bytes) == '52e11ef9b376797269f4a09bbc0f31cf0629f9c9236d6b6577185f3e2341dd76'
    before, after = [json.loads(gzip.decompress(b)) for b in (before_bytes, after_bytes)]
    assert {k:v for k,v in before.items() if k != 'records'} == {k:v for k,v in after.items() if k != 'records'}
    oldrows, newrows = [{r['id']:r for r in x['records']} for x in (before, after)]
    assert oldrows.keys() == newrows.keys() and len(oldrows) == 15
    sources = {'deenhindi-'+r['collection']+':'+r['number']:r for r in
        map(json.loads, (HERE / 'input/cohort.jsonl').read_bytes().splitlines())}
    changed, unchanged_read, unchanged_unread, unchanged_parents = [], 0, 0, 0
    removed_chars = removed_bytes = added_chars = span_count = 0
    for rid, oldrow in oldrows.items():
        newrow = newrows[rid]
        assert {k:v for k,v in oldrow.items() if k != 'field_reviews'} == {k:v for k,v in newrow.items() if k != 'field_reviews'}
        unchanged_parents += oldrow == newrow
        for old, new in zip(oldrow['field_reviews'], newrow['field_reviews'], strict=True):
            key = (rid, old['language'])
            span_count += len(new['spans'])
            if old['reviewed']:
                assert new['spans'] == accepted[key]['accepted_spans'], key
            if old == new:
                unchanged_read += bool(old['reviewed'])
                unchanged_unread += not old['reviewed']
                continue
            assert rid == 'deenhindi-nasai:2732' and old['language'] in ('hi','ur')
            assert {k:v for k,v in old.items() if k not in ('spans','reason','source_text_annotations')} == {
                k:v for k,v in new.items() if k not in ('spans','reason','source_text_annotations')}
            text = sources[rid]['source_record'][old['source_field']]
            oldmask = {i for s in old['spans'] for i in range(s['start'],s['end'])}
            newmask = {i for s in new['spans'] for i in range(s['start'],s['end'])}
            finding = next(f for f in findings['required_findings'] if f['language'] == old['language'])
            a,b = finding['source_span']
            assert text[a:b] == finding['text'] and sha(text.encode()) == finding['source_field_sha256']
            assert oldmask-newmask == set(range(a,b)) and not newmask-oldmask
            removed_chars += len(oldmask-newmask)
            removed_bytes += len(text[a:b].encode())
            added_chars += len(newmask-oldmask)
            changed.append({'id':rid,'language':old['language'],'source_span':[a,b],
                'text':text[a:b],'source_field_sha256':sha(text.encode()),
                'before_field_sha256':sha(enc(old)),'after_field_sha256':sha(enc(new)),
                'before_reason':old['reason'],'after_reason':new['reason'],
                'before_annotations':old['source_text_annotations'], 'after_annotations':new['source_text_annotations'],
                'accepted_independent_spans_exact':True})
    assert (len(changed),unchanged_read,unchanged_unread,unchanged_parents) == (2,28,45,14)
    assert (removed_chars,removed_bytes,added_chars,span_count) == (33,65,0,51)
    old_stats = json.loads((OLD/EVID/'validation-and-coverage-summary.json').read_bytes())
    new_stats = json.loads((OUT/EVID/'validation-and-coverage-summary.json').read_bytes())
    assert old_stats == new_stats
    for f in old_manifest['files']:
        assert (OLD/f['path']).read_bytes() == (OUT/REV/'before-v1/payload'/f['path']).read_bytes()
    for name in ['source-first-complete-reading.json','source-verification.json'] + ['initial-reading-notes-%02d.json'%i for i in range(1,5)]:
        assert (OLD/EVID/name).read_bytes() == (OUT/EVID/name).read_bytes() == (HERE/name).read_bytes()
    receipt = {
        'schema':'hadith-bank-bounded-independent-calendar-amendment-v2', 'result':'PASS',
        'source_checkpoint':'64f4ed50ed6026855237a5d547a86dd03e73f804',
        'before_manifest_sha256':sha(before_manifest),'before_active_ledger_sha256':sha(before_bytes),
        'after_active_ledger_sha256':sha(after_bytes),'source_baseline_sha256':after['source_ledger_sha256'],
        'independent_findings_sha256':bindings['independent-boundary-findings-v1.json'],
        'accepted_full_read_field_plan_sha256':bindings['accepted-reviewed-field-plan-v1.json'],
        'changes':changed,'changed_reviewed_fields':2,'selected_characters_removed':33,
        'selected_utf8_bytes_removed':65,'selected_characters_added':0,
        'all30_independent_accepted_masks_and_surviving_component_metadata_exact':True,
        'other28_reviewed_field_definitions_exact':True,'all45_unread_field_definitions_exact':True,
        'other14_whole_parents_exact':True,'all15_parent_decisions_and_source_metadata_exact':True,
        'all21_original_payloads_and_manifest_archived_exact':True,
        'all_initial_source_first_notes_and_receipts_unchanged':True,
        'explicit_refinement':'The initial primary notes treated both tenth-day calendar definitions as material ritual timing. Complete own-field rereading and independent comparison distinguish these lexical calendar equivalents after the already named Yawm al-Nahr from the eighth-day command condition, whose otherwise absent temporal scope remains selected. Only the two tenth-day appositions move to complete source context; the named day, sacrifice, eighth-day timing, all actual finite chronology, quantities, and source qualifications remain selected. The initial judgment is preserved verbatim in before-v1 evidence.',
        'native_totals':new_stats,'selected_spans_after':51,'native_lossless_partitions':75,
        'source_files_reopened':30,'raw_html_reparses':15,'new_readings_claimed':0,
        'source_text_changes':0,'new_translation_created':False,'source_http_requests':0,
        'github_writes':0,'shared_engine_changes':0,'independent_pro_qc':'not_performed',
        'limitation':'The primary amendment passes its bound plan and native checks; the final independent v2 audit is a separate gate.'}
    receipt_bytes = enc(receipt)
    put(REV/'amendment-receipt.json', receipt_bytes)
    put(REV/'revise_independent_calendar_v2.py', Path(__file__).read_bytes())
    put(REV/'manual_rules_v2.py', (HERE/'manual_rules_v2.py').read_bytes())
    def binding(p,local=False):
        b=p.read_bytes()
        f={'path':p.relative_to(OUT).as_posix(),'bytes':len(b),'size_bytes':len(b),'sha256':sha(b),'git_blob_sha1':git(b)}
        if local:f.update(local_path=str(p),source_path=str(p))
        return f
    portable = OUT/EVID/'package-file-manifest.json'
    portable.write_bytes(enc({'schema':'hadith-bank-source-review-package-manifest-v2',
        'source_checkpoint':receipt['source_checkpoint'],'active_ledger':ACTIVE.as_posix(),
        'source_baseline':after['source_ledger_path'],'summary':new_stats,
        'amendment_receipt':{'path':(REV/'amendment-receipt.json').as_posix(),'sha256':sha(receipt_bytes)},
        'manifest_excludes_its_own_recursive_hash':True,
        'files':[binding(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p != portable]}))
    files=[binding(p,True) for p in sorted(OUT.rglob('*')) if p.is_file()]
    final={'output_root':str(OUT),'summary':new_stats,'version':2,
        'amendment_receipt_sha256':sha(receipt_bytes),'files':files,
        'total_files':len(files),'total_bytes':sum(f['bytes'] for f in files)}
    final_bytes=enc(final)
    (HERE/'delivery-manifest-v2.json').write_bytes(final_bytes)
    print(json.dumps({'result':'FROZEN_V2','manifest_sha256':sha(final_bytes),
        'active_ledger_sha256':sha(after_bytes),'amendment_receipt_sha256':sha(receipt_bytes),
        'files':len(files),'bytes':final['total_bytes'],'removed_selected_chars':33,
        'removed_selected_utf8_bytes':65,'selected_spans':51,'partitions':75,
        'unchanged_read_fields':28,'unchanged_unread_fields':45,'unchanged_parents':14},indent=2))


if __name__ == '__main__':
    main()
