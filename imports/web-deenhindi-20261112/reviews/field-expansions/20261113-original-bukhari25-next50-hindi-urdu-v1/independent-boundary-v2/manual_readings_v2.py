"""Bounded independent-review refinements; immutable v1 and initial notes remain."""
import copy
from manual_readings import READINGS as ORIGINAL_READINGS
READINGS = copy.deepcopy(ORIGINAL_READINGS)

REFINEMENTS = {
 '1493': "Final independent-review refinement: the purchase-for-emancipation purpose, original owners, wala condition, consultation/reply and separately introduced meat/charity/gift encounter remain complete. The enslaved-status parenthesis duplicates the surrounding transaction and is explanatory apposition retained in source context. Preserve both ordered actual encounters and their original speakers/components. The original broader parenthesis judgment remains in the immutable source-first notes and v1 archive.",
 '1507': "Final independent-review refinement: preserve the Prophet's actual one-sa dates-or-barley instruction and the distinct later people's two-mudd wheat equivalence under Ibn Umar's reporting voice. The parenthetic half-sa wording is an explanatory unit conversion, retained as source context; the actual reported two-mudd quantity and equivalence remain selected. Do not attribute the explanatory conversion as additional speech. The original quantity-based judgment remains archived unchanged.",
 '1513': "Final independent-review refinement: preserve the actual Fadl/woman encounter, source's wanted-to-turn wording, the old father's incapacity to sit on the camel, the on-his-behalf question, yes reply and explicit final Farewell-Pilgrimage dating sentence. The opening Farewell-Pilgrimage parenthesis duplicates that final actual dating and is explanatory context, as is the redundant badal label. No actual event circumstance or condition is removed. Initial notes remain archived unchanged."
}
CUTS = {
 ('1493','hi'): '(जो बाँदी थीं)', ('1493','ur'): '( جو باندی تھیں )',
 ('1507','hi'): "(आधा सा'अ)", ('1507','ur'): '( آدھا صاع )',
 ('1513','hi'): '(हज्जतुल विदा में)', ('1513','ur'): '( حجۃ الوداع میں )'
}
for (number, language), literal in CUTS.items():
    rule=READINGS[number,language]
    rule['context'].append(literal)
    rule['refined_reading_note']=REFINEMENTS[number]
    rule['annotations']=[REFINEMENTS[number]]

rule=READINGS['1536','hi']
rule['speaker']="Hindi retains its damaged initial bin-Umayyah actor and later Ya’la name; the actual revelation/Umrah encounter and later exchange with the interlocutor printed अत have separate voices"
rule['segments'][1]['speaker']="The source’s first-person questioner, not externally identified, asks the interlocutor printed अत in this Hindi field about the three-wash instruction and receives the actual yes answer; this is not additional Prophetic speech"
rule['refined_reading_note']="Final independent-review metadata refinement: retain the complete Hindi revelation/Umrah encounter and separate actual later question/yes dialogue at exactly their v1 positions. The initial bin-Umayyah actor remains damaged; the later Ya’la spelling does not repair it. The Hindi interlocutor is printed अत, and that exact supplied name is acknowledged without silently completing it from Urdu or external identity. The first-person questioner remains unnamed. Original source-first notes and v1 metadata are archived unchanged."
rule['annotations']=["The source’s missing initial personal name and shortened route remain absent; its later Ya’la mention does not repair that earlier join. The last first-person questioner’s name is not inferred from the route. The interlocutor is printed अत in this Hindi field, and no Urdu-derived completion is supplied."]
assert len(READINGS)==50
