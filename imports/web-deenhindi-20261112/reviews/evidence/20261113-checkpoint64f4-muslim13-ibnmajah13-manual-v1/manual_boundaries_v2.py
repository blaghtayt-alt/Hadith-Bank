"""Exact one-field scope refinement after independent full-source review; v1 remains immutable."""
import copy
from manual_boundaries import READINGS as INITIAL_READINGS
READINGS = copy.deepcopy(INITIAL_READINGS)
field = READINGS['ibnmajah:2732']['ur']
assert field['context'].count('( واضح )') == 1
field['context'].remove('( واضح )')
field['retained_meaningful_structures'].append('( واضح )')
field['note'] = 'Read all1572 characters. The source independently supplies the three children, mother’s death, property/wala succession, Syria/plague deaths, Umar’s hearing and reported rule, named witnesses, the later reversed2000-dinar case/Hisham appeal, Abd alMalik’s assessment and continued possession. Preserve all as this source’s own historical report, with its actual voices and linkages. The wala/right-of-inheritance definition and explicit final1 marker are context. The printed clear adjective is an event-specific qualification within Abd al-Malik’s actual judgment appraisal, so it remains as qualified source-rendered scope. It defines no technical word and is not a detached compiler or transmitter-reliability comment. The immutable initial notes and v1 context placement remain preserved with this explicit reconsideration. No Hindi name/date/episode is repaired.'
appraisals = [part for part in field['segments'] if part['id'] == 'abd-al-malik-judgment-appraisal']
assert len(appraisals) == 1
appraisals[0]['speaker'] = 'Abd al-Malik supplies his actual appraisal in this case. The printed clear adjective remains as qualified source-rendered appraisal scope within his historical statement; it is not a detached compiler definition or a Prophet saying.'
