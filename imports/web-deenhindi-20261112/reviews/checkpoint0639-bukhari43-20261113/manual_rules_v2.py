"""Seven exact field amendments after independent complete-source review.

The v1 specifications and actual source-first notes remain unchanged. These
changes refine boundaries/voice labels only; no new field was inferred/read.
"""
import copy
import manual_rules as before

READINGS = copy.deepcopy(before.READINGS)
SPECS = copy.deepcopy(before.SPECS)
RETAINED_HONORIFICS = copy.deepcopy(before.RETAINED_HONORIFICS)
RETAINED_NONHONORIFIC = copy.deepcopy(before.RETAINED_NONHONORIFIC)
RETAINED_MARKER_WORDS = copy.deepcopy(before.RETAINED_MARKER_WORDS)
BOUNDARY_REFINEMENTS = copy.deepcopy(before.BOUNDARY_REFINEMENTS)

AMENDED_FIELDS = {
    ('deenhindi-bukhari:2239', 'hi'), ('deenhindi-bukhari:2239', 'ur'),
    ('deenhindi-bukhari:2244', 'hi'),
    ('deenhindi-bukhari:2256', 'hi'), ('deenhindi-bukhari:2256', 'ur'),
    ('deenhindi-bukhari:2261', 'hi'), ('deenhindi-bukhari:2261', 'ur'),
}

rules = SPECS['bukhari:2239']
rules['reason'] = (
    'Keep the actual Medina setting, duration predicate and named one/two versus '
    'two/three uncertainty as source transmission qualification, not Prophetic '
    'uncertainty. The repeated parenthetic Medina population label is identity '
    'apparatus; the arrival already supplies that place. Preserve the own '
    'measure-or-weight conjunction.')
rules['exclude_substrings'] = {'hi': ['(मदीना के)'], 'ur': ['( مدینہ کے )']}
for lang, literal in [('hi', '(मदीना के)'), ('ur', '( مدینہ کے )')]:
    RETAINED_NONHONORIFIC.pop(('bukhari:2239', lang, literal))
    rules['field_notes'][lang] += (
        ' Independent v2 refinement: the parenthetic Medina label duplicates '
        'the already stated arrival setting and is now complete context. '
        'Both duration alternatives and Ismail uncertainty remain selected.')
    BOUNDARY_REFINEMENTS['bukhari:2239:' + lang + ':independent-v2'] = (
        'The initial interpretation treated the repeated Medina label as '
        'essential population scope. Complete independent rereading confirms '
        'that this duplicate identifies the already established setting; '
        'only its exact parenthetic characters move to source context.')

rules = SPECS['bukhari:2244']
rules['reason'] = (
    'Keep the coherent first inquiry and own-field finite continuations. '
    'Hindi retains the dispatch to its literally named Kabzi and a separately '
    'qualified resumed negative we-clause, while the damaged orphan between '
    'them remains context. No speaker link, trade predicate or corrected name '
    'is filled from Urdu. Urdu keeps its complete separately named second '
    'inquiry and answer.')
rules['components']['hi'].append({
    'start_at': 'और हम उन से यह नहीं पूछते थे कि उन के पास खेती है या नहीं.',
    'stop_before': None,
    'report_type': 'unattributed_abbreviated_collective_report_fragment',
    'speaker': (
        'Unidentified resumed we-voice in the damaged Hindi second passage; '
        'the source does not supply its missing speaker link, so it is not '
        'identified as Ibn Abza and no unprinted trade predicate is supplied.'),
})
rules['source_report_family_by_component'] = {'report-3': 'report-2'}
rules['annotations']['hi'] = (
    'The printed source names/spellings and wheat-only first account remain '
    'literal. The final dispatch is finite. After the orphan ka-mamla-kartay-thay '
    'fragment, the supplied negative we-did-not-ask-whether-they-had-fields '
    'clause is also finite and is retained as an unidentified resumed we-voice '
    'in the second source family. Its missing speaker link is not borrowed '
    'from the Urdu Ibn-Abza account; the orphan remains complete context.')
rules['field_notes']['hi'] += (
    ' Independent v2 rereading distinguishes the final finite negative '
    'we-clause [533,591) from the damaged orphan [516,533). Only the complete '
    'negative clause is restored as a separately qualified unknown voice.')
BOUNDARY_REFINEMENTS['bukhari:2244:hi:independent-v2'] = (
    'The prior boundary refinement admitted the finite dispatch but kept the '
    'whole subsequent seam in context. Independent rereading separates its '
    'orphan fragment from a complete resumed negative we-clause. The latter '
    'is now its own component within the existing second family, with the '
    'speaker-link gap explicit. Initial notes and v1 remain preserved.')

rules = SPECS['bukhari:2256']
rules['report_type'] = 'prophetic_prohibition_with_preserved_term_explanation'
rules['speaker'] = 'The source-named Abdullah reports the practice and prohibition; Nafi term explanation stays context'
rules['reason'] = (
    'Retain the source-named Abdullah report without expanding his name. '
    'The expressly appended Nafi definition of the technical term is an '
    'explanation, so it remains complete source context rather than a '
    'registered saying component. Preserve the defective Hindi jaan-le '
    'wording there without correcting it from the Urdu birth verb.')
for lang in ['hi', 'ur']:
    rules['components'][lang] = rules['components'][lang][:1]
    rules['field_notes'][lang] += (
        ' Independent v2 refinement: the final explicitly labelled Nafi '
        'technical-term definition is complete explanatory context. Its '
        'attribution and source wording are preserved, but it is no longer '
        'selected as a report component.')
    BOUNDARY_REFINEMENTS['bukhari:2256:' + lang + ':independent-v2'] = (
        'The initial classification admitted the named explanatory statement. '
        'On full source rereading, its express function is to define the '
        'technical term rather than supply another event or independent '
        'report; the exact appendix is therefore retained as context under '
        'the project explanation exclusion. No earlier source words change.')
rules['annotations']['hi'] = (
    'The final explanatory Hindi jaan-le wording remains exactly in complete '
    'source context. No birth-verb repair or expanded Abdullah identity is '
    'introduced, and the definition is not part of the selected quotation.')

rules = SPECS['bukhari:2261']
rules.pop('exclude_substrings')
rules['reason'] = (
    'Keep the actual dialogue and the supplied my-tribe relation identifying '
    'the accompanying men. That first-person relationship is narrative actor '
    'scope, not a redundant name gloss. The final unnamed lan/la formula '
    'comparison remains complete transmission context, without resolving it.')
for lang, literal in [('hi', '(मेरे क़बीला)'), ('ur', '( میرے قبیلہ )')]:
    RETAINED_NONHONORIFIC[('bukhari:2261', lang, literal)] = (
        'The source supplies the actual first-person tribal relationship of '
        'the accompanying actors, not just another label for the narrator.')
    rules['field_notes'][lang] += (
        ' Independent v2 refinement restores the exact my-tribe relation as '
        'actual actor scope. The final lan/la formula apparatus stays context.')
    BOUNDARY_REFINEMENTS['bukhari:2261:' + lang + ':independent-v2'] = (
        'The initial pass called the parenthetic relationship an identity '
        'gloss. The complete source establishes an actual relation between '
        'the narrator and accompanying actors; retain those exact words '
        'while keeping the unrelated final formula comparison in context.')
