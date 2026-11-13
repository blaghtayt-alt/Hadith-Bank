"""The two exact participant-scope restorations accepted after independent review.

The complete v1 specification and initial source-first judgments remain intact.
Every other field rule is inherited unchanged.
"""
import copy
from manual_readings import READINGS as V1_READINGS

READINGS=copy.deepcopy(V1_READINGS)
for language in ('hi','ur'):
    spec=READINGS[('1467',language)]
    assert len(spec['context'])==1
    spec['context']=[]
    spec['final_note']=(
        'Read this entire own source field. Umm Salamah asks about spending on '
        'Abu Salamah sons and explicitly states that they are also her children; '
        'the Prophet supplied affirmative answer and reward promise remain exact. '
        'Retain the first-person former-husband parenthesis as actual participant '
        'and temporal scope within her question. The shared-child statement alone '
        'does not supply the former marital relationship. This narrowly refines '
        'the initial biographical-gloss interpretation, which remains preserved '
        'in the immutable source-first receipt and v1 candidate. No other words, '
        'attribution, report component or family are changed.'
    )
