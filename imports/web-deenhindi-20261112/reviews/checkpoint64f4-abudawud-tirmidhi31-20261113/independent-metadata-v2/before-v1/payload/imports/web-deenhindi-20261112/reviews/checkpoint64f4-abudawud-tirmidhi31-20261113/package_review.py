#!/usr/bin/env python3
"""Freeze the primary 31 review with exact source, reading and apparatus evidence."""
import collections
import gzip
import hashlib
import json
import re
from pathlib import Path

from manual_boundaries import records as instructions

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'publish-v1'
COHORT = 'checkpoint64f4-abudawud-tirmidhi31-20261113'
PREFIX = 'imports/web-deenhindi-20261112/reviews/' + COHORT
ACTIVE = 'imports/web-deenhindi-20261112/reviews/source-review-' + COHORT + '.json.gz'
sha = lambda b: hashlib.sha256(b).hexdigest()
blob = lambda b: hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
enc = lambda x: (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def put(path, data):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return {'path': path, 'bytes': len(data), 'sha256': sha(data), 'git_blob_sha1': blob(data)}


# Each of these exact parenthetical units was considered in its complete own field.
# This is an inventory of those explicit decisions, not a blanket parentheses rule.
RETAINED = {
    ('abudawud:2725', 'hi', '(हबशा से)'): 'The source supplies the arrival origin; retaining it preserves the reported journey scope without an external completion.',
    ('abudawud:2725', 'hi', '(माल-ए-गनीमत से)'): 'The source specifies the property from which the allocation or gift came, a material object restriction.',
    ('abudawud:2725', 'ur', '( حبشہ سے )'): 'The source-rendered arrival origin is part of the reported journey scope.',
    ('abudawud:2725', 'ur', '( مال غنیمت سے )'): 'The source identifies the property source of the reported allocation or gift.',
    ('abudawud:2729', 'hi', '(उम्म-ए-ज़ियाद अल-अशजईयाह)'): 'The source explicitly identifies the otherwise relational grandmother reporter; her name is retained as supplied attribution.',
    ('abudawud:2729', 'ur', '(ام زیاد اشجعیہ)'): 'This source-supplied name identifies the grandmother who narrates the expedition; no external identity is supplied.',
    ('tirmidhi:2711', 'hi', '(क्या है?)'): 'The parenthesis supplies the questioning predicate in the actual reported reply, qualified as the source rendering.',
    ('tirmidhi:2711', 'ur', '( کیا ہے؟ )'): 'This is the source-rendered questioning predicate of the reply, not a detached definition.',
    ('tirmidhi:2718', 'hi', '(बादशाहों)'): 'The source restricts the intended foreign recipients to kings, preserving the reported participant domain.',
    ('tirmidhi:2718', 'hi', '(मोहर के लिए)'): 'The actual purpose of making the ring is supplied in the source and remains part of the narrated action.',
    ('tirmidhi:2718', 'ur', '( بادشاہوں )'): 'The source specifies the king recipients of the intended letters.',
    ('tirmidhi:2718', 'ur', '( مہر کے لیے )'): 'The source-rendered sealing purpose belongs to the reported ring-making action.',
    ('tirmidhi:2722', 'hi', '(आप पर सलामती हो)'): 'This is the actual complete supplied rendering of the bounded greeting quotation; the omitted longer story is not filled.',
    ('tirmidhi:2728', 'hi', '(बस इतना ही काफी है)'): 'The source supplies a finite sufficiency predicate in the answer; preserve its limiting scope without claiming verbatim historical parentheses.',
    ('tirmidhi:2728', 'ur', '( بس اتنا ہی کافی ہے )'): 'The finite source-rendered sufficiency answer limits the response and remains with the reported dialogue.',
    ('tirmidhi:2732', 'hi', '(उस वक़्त)'): 'The supplied temporal connection binds the arrival to the Messenger being in Aisha’s home.',
    ('tirmidhi:2732', 'hi', '(बढ़ कर)'): 'The source supplies an actual advancing movement in the greeting scene.',
    ('tirmidhi:2732', 'ur', '( اس وقت )'): 'This source-rendered time qualification belongs to the narrated arrival scene.',
    ('tirmidhi:2732', 'ur', '( بڑھ کر )'): 'The source supplies the advancing action before the embrace and kiss.',
    ('tirmidhi:2733', 'hi', '(मूसा अलैहिस्सलाम को दी गयी)'): 'The source identifies the recipient/domain of the nine-sign question; retain that supplied question scope.',
    ('tirmidhi:2733', 'hi', '(आप का जवाब सुन कर)'): 'This is the finite hearing/response transition leading to the interlocutors’ action and testimony.',
    ('tirmidhi:2733', 'ur', '( موسیٰ علیہ السلام کو دی گئیں )'): 'The source specifies to whom the signs in the actual question were given, without reconstructing any absent signs.',
    ('tirmidhi:2733', 'ur', '( آپ کا جواب سن کر )'): 'The source expressly supplies the hearing transition before the reported kiss and testimony.',
    ('tirmidhi:2739', 'hi', '(इस मौक़े पर सिर्फ़)'): 'The source restricts the actual reply to this occasion and formula; preserve that material response scope.',
    ('tirmidhi:2739', 'ur', '( اس موقع پر صرف )'): 'The source-rendered occasion-only restriction limits the actual reply, rather than supplying a detached lexical definition.',
}


def main():
    assert not (ROOT / 'delivery-manifest-v1.json').exists(), 'Primary is already frozen'
    raw = (OUT / ACTIVE).read_bytes()
    assert sha(raw) == '5c1a6498cee4032d90466d365424b468cabb8548a10793932f451ef72306dfd4'
    doc = json.loads(gzip.decompress(raw))
    v = json.loads((OUT / PREFIX / 'validation.json').read_bytes())
    totals = v['totals']
    assert (totals['source_occurrences'], totals['register'], totals['exclude']) == (31, 30, 1)
    assert (totals['complete_fields_read'], totals['admitted_language_fields'], totals['read_context_fields'], totals['unread_context_fields']) == (65, 60, 5, 90)
    assert (totals['quotation_spans'], totals['selected_characters'], totals['exact_complete_field_partitions']) == (126, 23182, 155)
    fields = json.loads(gzip.decompress((OUT / PREFIX / 'complete-field-readings-and-boundaries.json.gz').read_bytes()))['fields']
    assert len(fields) == 65
    rules = {(r['key'], lang): f for r in instructions for lang, f in r['fields'].items()}
    inventory, used, counts, views, separators = [], set(), collections.Counter(), [], []
    for f in fields:
        text = f['text']
        key = (f['occurrence_id'].removeprefix('deenhindi-'), f['language'])
        rule = rules[key]
        mask = {i for s in f['selected_spans'] for i in range(s['start'], s['end'])}
        assert all(s['text'].strip() and '؎' not in s['text'] for s in f['selected_spans'])
        assert not any(re.search(r'\(\s*[0-9۰-۹٠-٩]+\s*\)', s['text']) for s in f['selected_spans'])
        assert not any(re.search(r'(?:سورۃ|सौराह)\s*[^()]{0,24}:', s['text']) for s in f['selected_spans'])
        stack = []
        for i, char in enumerate(text):
            if char == '(':
                stack.append(i)
            elif char == ')':
                assert stack
                a = stack.pop()
                literal = text[a:i + 1]
                if not set(range(a, i + 1)) <= mask:
                    continue
                specific = key + (literal,)
                if specific in RETAINED:
                    reason = RETAINED[specific]
                    used.add(specific)
                    category = 'individually_read_material_scope_or_quotation'
                    counts['material_scopes_or_quotations'] += 1
                else:
                    assert re.fullmatch(r'\(\s*(?:सल्लल्लाहु|रज़ियल्लाहु|रज़ियल्लाहु|रदि अल्लाहु|रदी अल्लाहु|रज़ि|रज़ि|अलैहिस्सलाम|صلی اللہ|رضی (?:اللہ|الله)|ﷺ)[^()]*\)', literal), (specific, literal)
                    reason = 'Exact printed honorific retained without normalization.'
                    category = 'source_honorific'
                    counts['honorifics'] += 1
                inventory.append({'id': f['occurrence_id'], 'language': f['language'], 'field_sha256': f['text_sha256'], 'start': a, 'end': i + 1, 'text': literal, 'sha256': sha(literal.encode()), 'category': category, 'reason': reason})
        assert not stack
        base = set()
        for s in rule.get('spans', []):
            a = 0 if s['from'] is None else text.index(s['from'])
            b = len(text) if s['to'] is None else text.index(s['to'], a)
            base.update(range(a, b))
        literal_cuts = set()
        for cut in rule.get('omit_source_context', []):
            a = 0
            for _ in range(cut['expected_count']):
                a = text.index(cut['text'], a)
                b = a + len(cut['text'])
                literal_cuts.update(range(a, b))
                a = b
        groups = []
        for i in sorted(base - mask - literal_cuts):
            if groups and groups[-1][1] == i:
                groups[-1][1] = i + 1
            else:
                groups.append([i, i + 1])
        for a, b in groups:
            assert not text[a:b].strip()
            separators.append({'id': f['occurrence_id'], 'language': f['language'], 'start': a, 'end': b, 'text': text[a:b], 'sha256': sha(text[a:b].encode()), 'reason': 'Isolated whitespace between separately excluded apparatus is preserved as context instead of a whitespace-only quotation.'})
        views.append({'id': f['occurrence_id'], 'language': f['language'], 'text': text, 'reason': f['actual_field_review']['reason'], 'selected_spans': f['selected_spans'], 'retained_context': f['retained_context']})
    assert used == set(RETAINED) and counts['material_scopes_or_quotations'] == 25
    cuts = json.loads((OUT / PREFIX / 'explicit-source-apparatus-context.json').read_bytes())
    assert cuts['literal_omissions'] == 40
    put(PREFIX + '/retained-source-parentheses.json', enc({'scope': 'All balanced selected parentheses. Each non-honorific reason was authored individually after reading the complete own field; this inventory supplies no automatic semantic admission rule.', 'counts': dict(counts), 'items': inventory, 'selected_footnote_markers': 0, 'selected_numeric_apparatus_labels': 0, 'selected_explicit_verse_locator_labels': 0, 'isolated_context_separators': separators}))
    (ROOT / 'boundary-view-v1.json').write_bytes(enc(views))
    original = (ROOT / 'input/full-field-reading-input-65.jsonl').read_bytes()
    assert sha(original) == '338d7f7538549fe6110871ca7dd7a1cb6fbad9c6219ffcca4accd0a350f20dc1'
    put(PREFIX + '/original-full-field-reading-input-65.jsonl.gz', gzip.compress(original, mtime=0))
    put(PREFIX + '/additional-abudawud2720-originals.jsonl', (ROOT / 'input/additional-abudawud2720-originals.jsonl').read_bytes())
    put(PREFIX + '/original-source-verification.json', (ROOT / 'source-verification.json').read_bytes())
    put(PREFIX + '/original-partition-source-verification.json', (ROOT / 'input/source-verification.json').read_bytes())
    put(PREFIX + '/original-partition-delivery-manifest.json', (ROOT / 'input/original-partition-delivery-manifest.json').read_bytes())
    for name in ('freeze_source_first.py', 'prepare_originals.py'):
        put(PREFIX + '/' + name, (ROOT / name).read_bytes())
    report = {
        'schema': 'hadith-bank-source-bound-primary-review-v1', 'result': 'PASS',
        'source_commit': doc['source_checkpoint'],
        'cohort': 'Exactly 31 new saved 64f4 occurrences: 13 Abu Dawud and 18 Tirmidhi, disjoint from the other three assigned new 102 groups.',
        'source_worker_run_id': 43480836830, 'artifact_id': 14067478999,
        'source_worker_outcome': 'The source checkpoint save succeeded; the overall run later failed when normal continuation returned HTTP 422 for a disabled workflow. This review does not enable or dispatch it.',
        'source_packet_scope': 'The original bounded artifact selected 250 of 273 held entries. A separately verified immutable GitHub supplement supplies the omitted 23. This review binds that documented local union, not an enlarged original artifact; the 250-record and byte caps remain unchanged.',
        'active_ledger_path': ACTIVE, 'active_ledger_sha256': sha(raw),
        'source_baseline_path': doc['source_ledger_path'], 'source_baseline_sha256': doc['source_ledger_sha256'],
        'source_first_receipt_sha256': 'b043183c9fa4a3a46bc66053d878f978ab9d2b8c5afc9916485c5862dc9b486e',
        'source_first_notes_sha256': '4c6abd0dbd5504fdd1d2d2ef132d4ffa6ba08790e31a3c0012a9a4b293c4757a',
        'actual_readings': {'full_fields': 65, 'characters': 28670, 'utf8_bytes': 61240, 'admitted': 60, 'reviewed_context_only': 5, 'unread_siblings': 90, 'empty_siblings': 0},
        'dispositions': {'registered': 30, 'source_only': 1, 'unresolved': 0},
        'source_only_ids': ['deenhindi-abudawud:2720'],
        'native_validation': v, 'literal_context_cuts_inside_components': 40,
        'retained_parentheses': dict(counts),
        'isolated_context_separator_characters': sum(s['end'] - s['start'] for s in separators),
        'source_files_reopened': 62, 'exact_raw_reparses': 31,
        'complete_post_serialization_field_boundary_inspections': 65,
        'scope_qualifications': [
            'Abu Dawud 2720 was read in all five own languages. Each supplies only a transmission route, questioning about transmission or a same-as-above pointer; no missing report body is imported.',
            'Abu Dawud 2707 keeps the Qinnasrin history and Muadh’s embedded Khaybar account as distinct source report families. Abu Dawud 2729 separates the grandmother’s expedition account from Hashraj’s later share question and her actual dates reply.',
            'Abu Dawud 2722 preserves the appended finite killing clause with unresolved pronouns. Abu Dawud 2745 retains actual passive alternate allocation wording as a variant in the same family, with its giver unnamed and compiler route criticism in context.',
            'Tirmidhi 2715 retains the actual transmitted Syriac-learning command as a same-family variant. Tirmidhi 2717 keeps the bounded letter wording and source rendering while excluding the omitted-remainder pointer, lexical synonyms and external biographical apparatus.',
            'Tirmidhi 2733 uses five ordered components in one encounter family for the interlocutors, reported answer, response, follow-up question and their own David-prayer/fear explanation. Its nine enumeration labels per language are apparatus; every actual instruction and the own Hindi बेगाना versus Urdu بےگناہ wording remains uncorrected.',
            'Tirmidhi 2738 retains the source’s literal Hindi &quot; text and actual supplied formula translations. Tirmidhi 2743.4 retains only its finite third-occasion reply with the source’s honorific-marked pronoun, without supplying a name or the missing earlier exchange.',
            'Tirmidhi 2748 leaves the relative reporter as Thabit’s father and keeps the compiler’s narrator-identification discussion outside. Tirmidhi 2753 does not fill the missing Hindi intermediary from the explicit Urdu Hudhayfa link. Tirmidhi 2759 preserves the passive prescription without inventing its prescriber.',
            'Material source-rendered participant, purpose, temporal, question-domain and answer-predicate qualifications remain exact. Their parentheses are not asserted to be verbatim historical speech. Explicit lexical synonyms, grades, route and name criticism, omitted-body pointers and footnote markers remain lossless context.',
            'All source-local identifiers, wording defects, grades, references, source credits, scripts, unknown identities and raw/parsed bytes remain unchanged. Only the 65 actually read fields receive reading credit; the other 90 complete sibling fields remain unread context.'
        ],
        'peer_notes_inspected_before_primary_freeze': False,
        'source_http_requests': 0, 'github_writes': 0, 'shared_engine_changes': 0,
        'independent_pro_qc': 'not_performed', 'certified_release_eligible': False,
        'limitations': 'Primary complete own-field review and local native/source preservation only. Independent second reading, combined repository export and this review’s actual publication/deployment are separate gates.'
    }
    put('reports/web-source-resolution-20261113/checkpoint64f4-abudawud-tirmidhi31-primary-review.json', enc(report))
    put(PREFIX + '/package_review.py', Path(__file__).read_bytes())

    def files(local=False):
        result = []
        for p in sorted(OUT.rglob('*')):
            if not p.is_file() or (not local and p.relative_to(OUT).as_posix() == PREFIX + '/portable-manifest.json'):
                continue
            b = p.read_bytes()
            f = {'path': p.relative_to(OUT).as_posix(), 'bytes': len(b), 'sha256': sha(b), 'git_blob_sha1': blob(b)}
            if local:
                f['local_path'] = str(p)
            result.append(f)
        return result

    fs = files()
    put(PREFIX + '/portable-manifest.json', enc({'schema': 'hadith-bank-portable-review-package-v1', 'source_commit': doc['source_checkpoint'], 'active_ledger_sha256': sha(raw), 'files': fs, 'total_files': len(fs), 'total_bytes': sum(f['bytes'] for f in fs)}))
    fs = files(True)
    m = {'schema': 'hadith-bank-source-review-delivery-v1', 'source_commit': doc['source_checkpoint'], 'active_ledger_path': ACTIVE, 'active_ledger_sha256': sha(raw), 'source_baseline_sha256': doc['source_ledger_sha256'], 'files': fs, 'total_files': len(fs), 'total_bytes': sum(f['bytes'] for f in fs)}
    mb = enc(m)
    (ROOT / 'delivery-manifest-v1.json').write_bytes(mb)
    print(json.dumps({'status': 'FROZEN', 'manifest_sha256': sha(mb), 'active_ledger_sha256': sha(raw), 'files': len(fs), 'bytes': m['total_bytes'], 'actual_readings': report['actual_readings'], 'dispositions': report['dispositions'], 'retained_parentheses': dict(counts), 'isolated_separator_characters': report['isolated_context_separator_characters']}, indent=2))


if __name__ == '__main__':
    main()
