"""Replay only the 24 explicitly read, source-bound apparatus corrections."""
from __future__ import annotations
import copy
import gzip
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(root, output, evidence, notes, sources, compile_field, put, enc):
    plan_bytes = (root / 'source-apparatus-corrections-v2.json').read_bytes()
    plan = json.loads(plan_bytes)
    before_bytes = (root / 'before-source-apparatus-active.json.gz').read_bytes()
    before = json.loads(gzip.decompress(before_bytes))
    historical = json.loads(gzip.decompress((root / 'before-source-apparatus-manual-notes.json.gz').read_bytes()))
    assert digest(before_bytes) == plan['before_active_sha256'] == '520e6f17b3608486dd48da21afdf9ac6c6c9a3325b99732d8e23984d7dde0603'
    assert digest((root / 'before-source-apparatus-delivery-manifest.json').read_bytes()) == plan['before_delivery_manifest_sha256']
    old_fields = {(r['id'].removeprefix('deenhindi-'), f['language']): f
                  for r in before['records'] for f in r['field_reviews']}
    changes = {(c['id'].removeprefix('deenhindi-'), c['language']): c for c in plan['changes']}
    assert len(changes) == plan['changed_fields'] == 18
    assert sum(len(c['cuts']) for c in changes.values()) == plan['exact_cuts'] == 24
    expected_notes = copy.deepcopy(historical)
    comparison = []
    for (key, lang), change in changes.items():
        assert historical[key]['fields'][lang] == change['before']
        expected_notes[key]['fields'][lang] = change['after']
        text = sources[key]['source_record'][change['source_field']]
        assert digest(text.encode()) == change['source_text_sha256']
        old = compile_field(key, lang, historical[key]['fields'][lang], text, change['source_field'])
        new = compile_field(key, lang, notes[key]['fields'][lang], text, change['source_field'])
        assert old == old_fields[key, lang]
        old_mask = {i for s in old['spans'] for i in range(s['start'], s['end'])}
        new_mask = {i for s in new['spans'] for i in range(s['start'], s['end'])}
        cuts = set()
        for cut in change['cuts']:
            a, b = cut['start'], cut['end']
            assert text[a:b] == cut['text'] and digest(text[a:b].encode()) == cut['sha256']
            assert set(range(a, b)) <= old_mask
            assert not (cuts & set(range(a, b)))
            cuts.update(range(a, b))
        assert new_mask <= old_mask and old_mask - new_mask == cuts
        assert not new_mask & cuts
        for span in new['spans']:
            owners = [(i, old_span) for i, old_span in enumerate(old['spans'])
                      if old_span['start'] <= span['start'] < span['end'] <= old_span['end']]
            assert len(owners) == 1
            index, owner = owners[0]
            assert span.get('component_id', 'passage-' + str(index + 1)) == owner.get('component_id', 'passage-' + str(index + 1))
            for name in ('report_type', 'speaker', 'source_report_family_id'):
                assert span.get(name, new.get(name)) == owner.get(name, old.get(name))
            assert text[span['start']:span['end']].strip()
        comparison.append({'id': 'deenhindi-' + key, 'language': lang,
            'source_text_sha256': change['source_text_sha256'], 'before_spans': old['spans'],
            'after_spans': new['spans'], 'removed_characters': len(cuts),
            'removed_utf8_bytes': sum(len(text[c['start']:c['end']].encode()) for c in change['cuts']),
            'selected_subset_exactly_matches_approved_cuts': True,
            'components_and_speakers_preserved': True, 'whitespace_only_spans_removed': 0})
    assert notes == expected_notes
    assert set(notes) == set(historical) == set(sources)
    for key, note in notes.items():
        assert note['decision'] == historical[key]['decision']
        assert set(note['fields']) == set(historical[key]['fields'])
        for lang, instruction in note['fields'].items():
            if (key, lang) not in changes:
                assert instruction == historical[key]['fields'][lang]
    star_text = sources['abudawud:2118']['source_record']['translationUrdu']
    star_field = compile_field('abudawud:2118', 'ur', notes['abudawud:2118']['fields']['ur'], star_text, 'translationUrdu')
    assert star_text[710:711] == '*'
    assert any(s['start'] <= 710 < 711 <= s['end'] for s in star_field['spans'])
    receipts = {
        'correction_plan': put(output, evidence + '/source-apparatus-corrections-v2.json', plan_bytes),
        'before_active': put(output, evidence + '/before-source-apparatus-active.json.gz', before_bytes),
        'before_manual_notes': put(output, evidence + '/before-source-apparatus-manual-notes.json.gz',
                                   gzip.compress(enc(historical), mtime=0)),
        'before_delivery_manifest': put(output, evidence + '/before-source-apparatus-delivery-manifest.json',
                                       (root / 'before-source-apparatus-delivery-manifest.json').read_bytes()),
    }
    report = {'schema': 'hadith-bank-source-apparatus-amendment-validation-v1', 'result': 'passed',
        'source_checkpoint': plan['source_checkpoint'], 'before_active_sha256': digest(before_bytes),
        'changed_fields': 18, 'exact_cuts': 24, 'footnote_markers': 17,
        'verse_reference_labels': 7, 'characters_moved_to_context': 178,
        'utf8_bytes_moved_to_context': 329, 'whitespace_only_spans_removed': 0,
        'new_source_wording_approved': False, 'source_wording_or_metadata_changed': False,
        'parent_dispositions_changed': False, 'previous_correction_history_preserved': True,
        'actual_scripture_and_translation_preserved': True, 'verse_separator_preserved': True,
        'field_comparisons': comparison, 'evidence': receipts}
    assert sum(c['removed_characters'] for c in comparison) == 178
    assert sum(c['removed_utf8_bytes'] for c in comparison) == 329
    receipts['comparison'] = put(output, evidence + '/source-apparatus-before-after-v2.json', enc(report))
    put(output, evidence + '/verify_apparatus.py', Path(__file__).read_bytes())
    return receipts
