"""Versioned, individually accepted prefatory-route boundaries after v1 review.

The forty full-field readings and all source-first judgments remain unchanged.
Only the thirty-four exact route intervals in the frozen independent finding
are additionally retained as context. This does not approve a new field.
"""
import copy
import hashlib
import json
from pathlib import Path
import manual_rules as original

ROOT = Path(__file__).resolve().parent
raw = (ROOT / 'supplemental-chain-findings-v1.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == '3dee206d2a59d230fb9adc8706ec20c80afd978a7608531935de15622e7234a5'
FINDINGS = json.loads(raw)
SPECS = copy.deepcopy(original.SPECS)
READINGS = copy.deepcopy(original.READINGS)
RETAINED_HONORIFICS = copy.deepcopy(original.RETAINED_HONORIFICS)
RETAINED_NONHONORIFIC = copy.deepcopy(original.RETAINED_NONHONORIFIC)
RETAINED_MARKER_WORDS = copy.deepcopy(original.RETAINED_MARKER_WORDS)
BOUNDARY_REFINEMENTS = copy.deepcopy(original.BOUNDARY_REFINEMENTS)
BOUNDARY_REFINEMENTS['versioned_supplemental_prefatory_route_review'] = {
    'stage': 'versioned_supplemental_prefatory_route_review',
    'independent_finding_sha256': hashlib.sha256(raw).hexdigest(),
    'previous_primary_and_independent_PASS_remain_immutable': True,
    'judgment': 'After inspecting every exact proposed source range, separate the pure multi-step prefatory transmitter routes from the report body. Preserve the coherent final-reporter predicate, every finite scene and all original source identities in their metadata and complete source context. No generic chain pattern was used to classify any unread text.',
    'scope': '32 previously read fields across16 parents;34 literal ranges. No source, parent disposition, reading credit, actual speaker, report type, component or family identity changes.',
    'special_case_2494': 'Two separate cuts per language preserve the first finite Urwah-asked-Aisha clause between the routes and the entire later question and answer. Do not absorb the first actual scene into a blanket prefix.',
    'source_first_notes_are_historical_and_unchanged': True,
}

for finding in FINDINGS['findings']:
    key = finding['id'].removeprefix('deenhindi-')
    language = finding['language']
    spec = SPECS[key]
    assert language in spec['languages'] and language in spec['read_languages']
    extra = spec.setdefault('exclude_substrings', {}).setdefault(language, [])
    for cut in finding['cuts']:
        assert cut['text'] and cut['text'] not in extra
        extra.append(cut['text'])
    spec.setdefault('versioned_boundary_refinements', {})[language] = {
        'independent_finding_sha256': hashlib.sha256(raw).hexdigest(),
        'cuts': copy.deepcopy(finding['cuts']),
        'reason': finding['reason'],
        'prior_complete_reading_note_unchanged': True,
    }
