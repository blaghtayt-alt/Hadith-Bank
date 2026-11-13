"""Serialize explicit Nasai22 decisions after the frozen47-field reading pass."""
from pathlib import Path
import hashlib
import json
import pprint

HERE = Path(__file__).resolve().parent
assert not (HERE / 'delivery-manifest-v1.json').exists()
raw = (HERE / 'source-first-complete-reading.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == '86652d131ab33fb6b8af45f4a042008f3b19a0cb9db55b481b03caaddc0571f8'
receipt = json.loads(raw)
assert receipt['all_full_fields_read_before_candidate_creation']

WHO = {
 '2628': ('companion_question_and_recipient_qualified_prophetic_reply', 'Aisha gives her actual question and receives the supplied negative answer with its for-you Hajj qualification'),
 '2632': ('companion_report_of_vow_question_and_conditional_reply', 'Ibn Abbas reports the sister’s unfulfilled vow, her brother’s question and the actual conditional debt analogy and replies'),
 '2637': ('companion_question_and_prophetic_reply', 'Abu Razin supplies his father’s old age and inability, then receives the actual on-his-behalf Hajj and Umrah reply'),
 '2641': ('companion_historical_encounter_and_prophetic_reply', 'Ibn Abbas reports Fadl’s riding position, the Khatham woman’s approach, the actual looking and face-turning, her father question and the affirmative reply'),
 '2646': ('companion_report_of_child_question_and_affirmative_reply', 'Ibn Abbas reports the woman lifting her child and asking; the source supplies the complete affirmative reply and reward addressed to her'),
 '2648': ('companion_report_of_group_encounter_and_prophetic_reply', 'Ibn Abbas reports the Rawha encounter, reciprocal identity questions and the woman’s child question with the actual reply'),
 '2650': ('companion_journey_report_with_conditional_instruction', 'Aisha reports the dated departure and the instruction to those without hady to end ihram after tawaf; each field keeps only its own journey wording'),
 '2659': ('companion_report_of_prophetic_actions', 'Ibn Umar reports the actual overnight stay and mosque prayer in the source’s own Dhul-Hulayfah locality wording'),
 '2664': ('companion_family_journey_and_relayed_prophetic_instruction', 'Abu Bakr reports the family journey, Asma’s childbirth, his approach and the instruction relayed to her, including the explicit except-tawaf restriction'),
 '2666': ('companion_report_of_prophetic_prohibition', 'Ibn Umar reports the supplied prohibition concerning a muhrim and saffron/wars-dyed clothing'),
 '2670': ('companion_report_of_question_and_conditional_clothing_reply', 'Ibn Umar reports the actual clothing question and full answer with the no-shoes condition and below-ankle limit; the singular/plural transmitter apparatus remains separate'),
 '2682': ('companion_question_and_time_limited_prophetic_reply', 'Hafsa asks the actual ihram question and receives the talbid/hady reply with its until-Hajj-completion condition'),
 '2684': ('companion_personal_practice_with_temporal_qualifications', 'Aisha reports her own perfuming with both hands and the source’s actual entering/ending-ihram temporal qualifications'),
 '2685': ('companion_personal_practice_with_temporal_qualifications', 'Aisha reports her own perfuming before entering ihram and before tawaf for ending it'),
 '2686': ('source_abbreviated_companion_report', 'Each own field keeps Aisha’s printed attribution and temporal clauses; the missing Hindi main action is not filled from Urdu'),
 '2687': ('companion_personal_practice_with_event_sequence', 'Aisha reports perfuming at entering ihram and for ending it after the Aqabah stoning but before the House tawaf'),
 '2688': ('companion_personal_practice_and_actual_comparison', 'Aisha reports her perfuming for ending and entering ihram and the actual unlike-your-perfume comparison; the unassigned yani explanation remains context'),
 '2690': ('companion_personal_practice_with_pronominal_recipient', 'Aisha reports her habitual best-available perfuming at the honorifically addressed recipient’s entering ihram; this field does not itself name that recipient'),
 '2691': ('source_abbreviated_companion_report', 'Each own field retains Aisha’s supplied temporal/intention clauses; the missing Hindi application action and perfume description are not filled'),
 '2692': ('companion_personal_practice_with_date_and_material', 'Aisha reports perfuming before ihram and on the tenth of Dhul-Hijjah before tawaf, with the supplied musk-mixture description'),
 '2701': ('companion_personal_practice_and_observation', 'Aisha reports her best-available perfuming and actual observation of shine in the head and beard at the source’s printed before-ihram time'),
}
SPECS = {}
for number, (kind, voice) in WHO.items():
    key = 'nasai:' + number
    fields = [field for field in receipt['fields'] if field['id'] == 'deenhindi-' + key]
    assert {field['language'] for field in fields} == {'hi', 'ur'}
    SPECS[key] = {
        'id': key, 'decision': 'register', 'languages': ['hi', 'ur'], 'read_languages': ['hi', 'ur'],
        'field_notes': {field['language']: field['reading_note'] for field in fields},
        'shared_report_family': True, 'report_type': kind, 'speaker': voice,
        'reason': 'Actual supplied report content is retained under its own visible source attribution and exact wording. No missing main action, absent identity, omitted body, canonical mapping or sibling translation is supplied.'
    }
context_fields = [field for field in receipt['fields'] if field['id'] == 'deenhindi-nasai:2636']
assert {field['language'] for field in context_fields} == {'ar', 'hi', 'ur', 'ur-Latn', 'en'}
SPECS['nasai:2636'] = {
    'id': 'nasai:2636', 'decision': 'exclude', 'languages': [],
    'read_languages': ['ar', 'hi', 'ur', 'ur-Latn', 'en'],
    'field_notes': {field['language']: field['reading_note'] for field in context_fields},
    'shared_report_family': False, 'report_type': 'transmission_and_comparison_apparatus',
    'speaker': 'The source provides only a route to Ibn Abbas and a similar-report pointer, with an English grade label; no ultimate report body is supplied.',
    'reason': 'All five own nonempty source fields were fully read. They contain only transmission chains, same-report pointers and an English grade label, with no supplied finite narration body. Preserve every byte as resolved source context without importing a neighbouring report.'
}
SPECS['nasai:2628']['exclude_substrings'] = {'hi': ['(मक़बूल)'], 'ur': ['( مقبول )']}
SPECS['nasai:2628']['annotations'] = {language: 'The for-you parenthesis is material recipient scope and remains in the source-rendered reply. The maqbul parenthesis is only a duplicate lexical rendering of mabroor and is preserved separately as context.' for language in ['hi', 'ur']}
SPECS['nasai:2632']['annotations'] = {language: 'The parenthetic death-before-performing-Hajj condition limits the actual vow/debt question and is retained as source-rendered narrative scope.' for language in ['hi', 'ur']}
SPECS['nasai:2646']['annotations'] = {language: 'The parenthetic affirmative child-Hajj predication is retained as supplied reply wording, not promoted to an external legal determination or claimed as verbatim wording in another source language.' for language in ['hi', 'ur']}
SPECS['nasai:2650']['exclude_substrings'] = {'hi': ['(क़ुरबानी का जानवर)'], 'ur': ['( قربانی کا جانور )']}
SPECS['nasai:2650']['annotations'] = {
    'hi': 'Medina is the supplied departure location and stays. The later approach join lacks Urdu’s stated Mecca destination and only-Hajj purpose; neither is inserted. Hady’s duplicate definition is context.',
    'ur': 'The source-rendered Medina departure location, only-Hajj purpose and Mecca approach remain, including the duplicated from wording. Hady’s duplicate technical definition is context.'
}
SPECS['nasai:2664']['annotations'] = {'hi': 'The informing step and the subject join are abbreviated in this own field. Keep the supplied childbirth/approach and actual relayed command, including the except-tawaf restriction, without inserting Urdu’s informing sentence or repairing source spellings.'}
SPECS['nasai:2670']['exclude_substrings'] = {
    'hi': ['(अम्र बिन अली ने दूसरी बार क़मीस के बजाय जमा के सीग़े के साथ कुमिस कहा)'],
    'ur': ['( عمرو بن علی نے دوسری بار قمیص کے بجائے جمع کے صیغے کے ساتھ قمص کہا )']
}
SPECS['nasai:2682']['exclude_substrings'] = {'hi': ['(बालों को जमाना)', '(क़ुर्बानी के जानवर)'], 'ur': ['۱؎', '۲؎']}
SPECS['nasai:2684']['annotations'] = {language: 'Preserve the printed before-ending-ihram wording; the next occurrence’s before-tawaf wording is not substituted.' for language in ['hi', 'ur']}
for number in ['2686', '2691']:
    SPECS['nasai:' + number]['components'] = {
        'hi': [{'report_type': 'truncated_companion_report_with_missing_main_action',
                'speaker': 'Aisha’s printed Hindi fragment supplies attribution and temporal/intention predication but omits her main action. Perfuming and any missing final predicate or quality are not inserted from another field.'}],
        'ur': [{'report_type': 'companion_personal_practice_with_temporal_qualifications',
                'speaker': 'Aisha’s own Urdu field expressly supplies her perfuming action and its actual temporal qualifications; no neighbouring version is inserted.'}]
    }
    SPECS['nasai:' + number]['annotations'] = {'hi': 'This saved Hindi field is truncated before its main action is supplied. Its actual temporal/intention clauses remain visible as a qualified fragment. No perfume, missing predicate, additional quality or different temporal condition is inserted.'}
SPECS['nasai:2688']['stop_before'] = {'hi': 'यानी यह ख़ुशबू', 'ur': 'یعنی یہ خوشبو'}
SPECS['nasai:2688']['annotations'] = {language: 'The actual unlike-your-perfume comparison remains in the attributed report. The subsequent expressly marked yani explanation is unassigned source interpretation, preserved fully as context rather than silently attributed to Aisha.' for language in ['hi', 'ur']}
SPECS['nasai:2690']['annotations'] = {language: 'The honorific recipient pronoun is left as printed. This short field does not itself name the recipient, so no identity is borrowed from the surrounding numbered reports.' for language in ['hi', 'ur']}
SPECS['nasai:2701']['annotations'] = {language: 'The source explicitly places the observed shine before ihram. That printed timing is retained without external harmonization.' for language in ['hi', 'ur']}
assert len(SPECS) == 22 and sum(len(spec['read_languages']) for spec in SPECS.values()) == 47
assert sum(len(spec['languages']) for spec in SPECS.values()) == 42
(HERE / 'manual_rules.py').write_text('"""Explicit decisions after the complete frozen47-field source-first pass."""\nSPECS = ' + pprint.pformat(SPECS, width=115, sort_dicts=True) + '\n')

source = (HERE.parent / 'phase21-checkpoint0d2fa-nasai-ibnmajah16-review/build_delivery.py').read_text()
old_scope = 'Nasai6/IbnMajah10 at checkpoint0d2fa. All32 complete Hindi and Urdu originals were read before candidate creation; all16 parents contain actual supplied finite content. All48 other nonempty sibling fields remain unread. Every source slot and metadata value is preserved; actual voices, quantities, conditions and damaged wording are distinguished from exact lexical, locator and transmitter apparatus. No observed-script correction or source-only parent is proposed.'
new_scope = 'Nasai22 at checkpoint17cd. All44 complete Hindi/Urdu fields and the three remaining own fields of2636 were read before candidate creation.21 parents have supplied report content;2636 is source-only after all five own fields were read.63 other nonempty siblings remain unread. Source-rendered recipient, condition and journey scope remain; the two truncated Hindi main-action predicates are disclosed and left unfilled. Exact lexical/word-form/pointer/interpretive apparatus stays context. No source text, number, narrator or script is repaired.'
replacements = [
    (old_scope, new_scope), ('Nasai6/IbnMajah10', 'Nasai22'),
    ('checkpoint0d2fa-nasai-ibnmajah16', 'checkpoint17cd-nasai22'),
    ('0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a', '17cd396eb858a29162505d545aad556ac73ce9ce'),
    ('639e2cf5033c7f1d637689c511c8709165a1cd62cf561d811e3d8522bbb365d9', 'e606722e94cffde01f011c34bd9cd7dbe53003b8522a1d4f24c8545223f78f17'),
    ('phase19-successor-acquisition-monitor/held-evidence', 'phase21-successor-acquisition-monitor/held-evidence'),
    ('len(specifications) == 16', 'len(specifications) == 22'), ("{'nasai':6,'ibnmajah':10}", "{'nasai':22}"),
    ('8d3f9b4f0321db8210ada007271ecad8691ebb9a48407fd4826fcfebe06790ca', '86652d131ab33fb6b8af45f4a042008f3b19a0cb9db55b481b03caaddc0571f8'),
    ('(32,13693,29601)', '(47,12443,26863)'), ('len(own_fields) == 32', 'len(own_fields) == 47'),
    ('passed for all16', 'passed for all22'), ('== (16, 0)', '== (21, 1)'),
    ('== (32, 32, 0, 48)', '== (47, 42, 5, 63)'), ('== (13693, 29601)', '== (12443, 26863)'),
    ('partitions == 80', 'partitions == 110'), ('== (80,80,0)', '== (110,110,0)'),
    ('len(apparatus_rows) == 32', 'len(apparatus_rows) == 42'), ('All32 admitted fields', 'All42 admitted fields'),
    ('range(1,5)', 'range(1,8)'), ('full-hi-ur-reading-input-32.jsonl', 'full-hi-ur-reading-input-44.jsonl'),
    ("'build_delivery.py','freeze_source_first.py','prepare_primary.py']", "'build_delivery.py','freeze_source_first.py','prepare_primary.py','additional2636-source-only-input-3.jsonl']"),
]
for old, new in replacements:
    assert old in source, old
    source = source.replace(old, new)
source = source.replace('    args = parser.parse_args()\n', "    args = parser.parse_args()\n    assert not args.manifest_file.exists(), 'Frozen publication cannot be rebuilt in place.'\n")
(HERE / 'build_delivery.py').write_text(source)
print('Prepared22 explicit parents from47 complete original readings;63 sibling fields remain unread.')
