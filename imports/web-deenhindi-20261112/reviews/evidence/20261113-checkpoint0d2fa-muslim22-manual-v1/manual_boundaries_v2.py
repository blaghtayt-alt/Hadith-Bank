"""Two exact participant-variant restorations; immutable v1 readings remain separate."""
import copy
from manual_boundaries import READINGS as ORIGINAL_READINGS
READINGS=copy.deepcopy(ORIGINAL_READINGS)
SPEAKER='The source’s expressly identified Abu-Kurayb version adds the finite statement that the other Companion was Abu Musa. This is a qualified transmitted participant-identity variant, not Aisha’s direct words, the transmitter’s eyewitness claim, or a new scene/canonical occurrence.'
for language,start in [('hi',844),('ur',781)]:
    f=READINGS['muslim:2556'][language]
    f['note']='Final independent-review refinement: retain the complete Abu Atiyyah/Masruq visit, Aisha question, Abdullah answer and Messenger-practice reply. The yani Ibn Masud apposition remains explanatory context; Hindi’s देर synonym also remains context. In contrast, the expressly attributed final Abu-Kurayb-version addition supplies a finite new predicate identifying the otherwise unnamed other participant as Abu Musa. Retain that exact addition as a separate qualified component in the same source report family, without attributing it to Aisha, claiming eyewitness testimony, or creating another incident. The original context-only judgment is preserved unchanged in the source-first notes and complete v1 archive, with this explicit reconsideration recorded separately.'
    f['speaker']='Abu Atiyyah reports the actual visit, Aisha question, Abdullah answer and Messenger-practice reply. A separately qualified same-family version component supplies the other participant’s identity; the yani Ibn Masud apposition remains context.'
    f['segments'].append({'start':start,'end':None,'id':'transmitted-other-companion-identity',
        'type':'explicit_transmitted_participant_identity_variant','speaker':SPEAKER})
    f['boundary_refinement']={'reason':'Independent complete source reading distinguished a new finite participant-identity predicate from the earlier appositional name explanation.',
        'version':'v2','prior_initial_reading_preserved':True,'source_positions_restored':[start,930 if language=='hi' else 864],
        'independent_findings_sha256':'ed6bb3f68631b447bd75d781c9deb38bc42a62486f4d10c674c0888793ad26b8',
        'new_occurrences_created':0,'new_linguistic_reading_credit':0}
