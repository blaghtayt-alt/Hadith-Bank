"""Four exact independent-review apparatus cuts; retain the complete v1 evidence."""
from copy import deepcopy
import manual_rules as original

READINGS = deepcopy(original.READINGS)
SPECS = deepcopy(original.SPECS)
BOUNDARY_REFINEMENTS = deepcopy(original.BOUNDARY_REFINEMENTS)
RETAINED_HONORIFICS = set(original.RETAINED_HONORIFICS)
RETAINED_NONHONORIFIC = deepcopy(original.RETAINED_NONHONORIFIC)
RETAINED_MARKER_WORDS = deepcopy(original.RETAINED_MARKER_WORDS)

EXACT_REFINEMENTS = [
    ('bukhari:2349', 'hi', '(इस बात की)',
     'Independent boundary review refines the initial narrative-link judgment: this deictic parenthesis is redundant with the complete happiness predicate and its following cause. Preserve it as context; all actual Sahl wording, Abu Hazim material uncertainty and component voices remain selected.'),
    ('bukhari:2349', 'ur', '( اس بات کی )',
     'Independent boundary review refines the initial narrative-link judgment: this deictic parenthesis is redundant with the complete happiness predicate and its following cause. Preserve it as context; all actual Sahl wording, Abu Hazim material uncertainty and component voices remain selected.'),
    ('bukhari:2382', 'hi', '(ये कहा कि)',
     'Independent boundary review separates this said-formula as transmission wording apparatus. Both actual quantity alternatives, their explicit OR and the entire named Dawud threshold-uncertainty component remain selected in the same family.'),
    ('bukhari:2382', 'ur', '( یہ کہا کہ )',
     'Independent boundary review separates this said-formula as transmission wording apparatus. Both actual quantity alternatives, their explicit OR and the entire named Dawud threshold-uncertainty component remain selected in the same family.'),
]
for key, language, literal, reason in EXACT_REFINEMENTS:
    SPECS[key].setdefault('exclude_substrings', {}).setdefault(language, []).append(literal)
    SPECS[key]['field_notes'][language] += ' Final independent refinement: ' + reason
    BOUNDARY_REFINEMENTS[key + ':' + language] = (
        BOUNDARY_REFINEMENTS.get(key + ':' + language, '') + ' ' + reason).strip()
    del RETAINED_NONHONORIFIC[(key, language, literal)]
