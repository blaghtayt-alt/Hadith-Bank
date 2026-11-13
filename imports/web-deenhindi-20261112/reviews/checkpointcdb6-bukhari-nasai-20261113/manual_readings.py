"""Explicit complete own-language readings of 50 new cdb66d saved occurrences.

Every decision below is individually authored from the full source field.
Helpers serialize exact boundaries; they never infer semantic approval.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
CHECKPOINT = 'cdb66dbcf9ee781fe232219724d05033a0fcab13'

def whole(kind, speaker, reason):
    return {'action': 'whole', 'report_type': kind, 'speaker': speaker, 'reason': reason}

def passage(start, stop, kind, speaker, component, family=None):
    return {'from': start, 'to': stop, 'report_type': kind, 'speaker': speaker, 'component_id': component,
            **({'source_report_family_id': family} if family else {})}

def excerpts(reason, spans, omissions=()):
    return {'action': 'excerpts', 'reason': reason, 'spans': spans,
            **({'omit_source_context': [{'text': item[0], 'expected_count': item[2] if len(item) == 3 else 1, 'reason': item[1]}
                for item in omissions]} if omissions else {})}

def body(kind, speaker, reason, omissions=(), stop=None):
    return excerpts(reason, [passage(None, stop, kind, speaker, 'report-1')], omissions)

def context(reason):
    return {'action': 'source_context', 'reason': reason}

def rec(key, hi, ur, **additional):
    return {'key': key, 'decision': 'register', 'fields': {'hi': hi, 'ur': ur, **additional}}

GLOSS = 'Explicit source lexical or identifying explanation; retain the exact supplied words as source context and keep surrounding narration in its original component.'
FOOTNOTE = 'Source footnote marker; retain the exact glyph as context without inventing an absent note.'
records = []

records.append(rec('bukhari:758',
    body('companion_historical_dialogue_reporting_prophetic_practice', 'Jabir ibn Samurah reporting Sad ibn Abi Waqqas speaking to Umar and Umar answering',
         'Read the complete Hindi field. Sad describes his own zuhr/asr prayer leadership as following the Prophet, with longer first two and shorter last two rakahs; Umar expresses his expectation of him. This is the actual Companion dialogue, not a direct Prophetic quotation. Only the parenthetic identification of the pronoun as Kufans is source explanation.',
         [('(कूफ़ा वालों)', GLOSS)]),
    body('companion_historical_dialogue_reporting_prophetic_practice', 'Jabir ibn Samurah reporting Sad ibn Abi Waqqas speaking to Umar and Umar answering',
         'Read the entire Urdu field independently. Preserve Sad’s comparison with Prophetic practice and Umar’s response under their actual speakers. Separate only the parenthetic identification of those whom he led as the Kufans.',
         [('( کوفہ والوں )', GLOSS)])
))
records.append(rec('bukhari:763',
    body('prophetic_report_with_companion_recollection', 'Ibn Abbas reporting Umm al-Fadl’s recollection of hearing the Prophet recite',
         'Read the whole Hindi field: Umm al-Fadl hears the actual al-Mursalat incipit, addresses her son, and remembers hearing that surah in maghrib near the end of the Prophet’s life. Keep the recited words and supplied chronology; only the parenthetic identification as his mother is context.',
         [('(उन की माँ)', GLOSS)]),
    body('prophetic_report_with_companion_recollection', 'Ibn Abbas reporting Umm al-Fadl’s recollection of hearing the Prophet recite',
         'Read the complete Urdu field, including the quoted Quran incipit and the actual mother-son conversation. The source’s last-life timing remains as written. The explicit pronoun-identifying mother gloss is kept outside the report body.',
         [('( ان کی ماں )', GLOSS)])
))
records.append(rec('bukhari:770',
    whole('companion_historical_dialogue_reporting_prophetic_practice', 'Jabir ibn Samurah reporting Umar’s complaint inquiry and Sad ibn Abi Waqqas’s answer',
          'Read the full Hindi field. Umar describes the Kufans’ complaints, Sad explains long first and short last rakahs as he experienced behind the Prophet, and Umar affirms him. Preserve all supplied names/spellings and the distinct occurrence; no shared-number or parallel-report substitution.'),
    whole('companion_historical_dialogue_reporting_prophetic_practice', 'Jabir ibn Samurah reporting Umar’s complaint inquiry and Sad ibn Abi Waqqas’s answer',
          'Read the full Urdu field independently. The actual Companion dialogue and Sad’s retrospective statement about Prophetic practice are complete report content. No compiler conclusion or numbered apparatus is appended.')
))
records.append(rec('bukhari:773',
    body('prophetic_historical_report_with_source_attribution_defect', 'The supplied Hindi chain through Said ibn Jubayr, with its missing intermediary and damaged initial Prophetic attribution left unfilled',
         'Read the complete Hindi field. Its opening chain and honorific are visibly truncated and its return-to-the-people passage is abridged; retain those defects without filling from Urdu. The actual story later explicitly names the Prophet praying fajr at Nakhlah. Retain the conditional parenthetic when-we-go-toward-the-sky wording as the supplied limitation in the reported dialogue. Retain the revealed Quran incipit and its own Hindi translation, which are actual cited scripture within the account. Separate only the lexical identification of the flaming projectile.',
         [('(शिहाब-इ-साकिब)', GLOSS)]),
    body('prophetic_historical_report', 'Ibn Abbas reporting the Nakhlah prayer and the jinn’s reported conversation and response',
         'Read the entire Urdu field, including the oath, the return to their people and the revealed incipit with its Urdu translation. These actual narrative words are retained; the shorter Hindi is not repaired from them. The ascent-condition parenthesis limits the narrated event and remains with that dialogue. Only the lexical equivalent for the projectiles is source context.',
         [('( شہاب ثاقب )', GLOSS)])
))
records.append(rec('bukhari:774',
    whole('companion_statement_reporting_prophetic_recitation', 'Ibn Abbas describing the Prophet’s loud and quiet recitation and citing scripture in support',
          'Read the entire Hindi field. Ibn Abbas describes obedience to the given recitation instructions, then supplies the actual translated scripture about the Lord not forgetting and the Messenger’s example. Keep these words as part of Ibn Abbas’s attributed statement; do not turn his final scriptural reasoning into a separately invented Prophetic quotation.'),
    whole('companion_statement_reporting_prophetic_recitation', 'Ibn Abbas describing the Prophet’s loud and quiet recitation and citing scripture in support',
          'Read the entire Urdu field independently. The loud/quiet practice and the actual scriptural wording supplied by Ibn Abbas remain together under that speaker. There are no explicit verse locator labels or footnote glyphs to cut.')
))
records.append(rec('bukhari:774.2',
    whole('prophetic_report', 'Anas reporting the unnamed Ansari imam’s practice, his companions’ objection and the Prophet’s dialogue with him',
          'Read the complete Hindi field. Preserve the separate decimal occurrence, the actual qul-hu-Allahu-ahad incipit, the repeated-prayer practice, the companions’ preference for their imam, and the complete question/love/Paradise answer. The Ansari remains unnamed.'),
    whole('prophetic_report', 'Anas reporting the unnamed Ansari imam’s practice, his companions’ objection and the Prophet’s dialogue with him',
          'Read the full Urdu field independently, including all the conditional leadership dialogue and the Prophet’s actual final statement. The recited surah incipit is narrative content; it is not a bibliographic surah label. No identity is borrowed from another occurrence.')
))


records.append(rec('bukhari:783',
    body('prophetic_report', 'Abu Bakrah reporting reaching the Prophet while he was bowing and the Prophet’s response',
         'Read the entire Hindi field. Keep the actual bowing before reaching the row and the complete blessing followed by the prohibition on repetition. The parenthetic purpose of coming to pray is explanatory context.',
         [('(नमाज़ पढ़ने के लिए)', GLOSS)]),
    body('prophetic_report', 'Abu Bakrah reporting reaching the Prophet while he was bowing and the Prophet’s response',
         'Read the full Urdu field independently. The approach, bowing, later mention and blessing/prohibition form one actual report; separate only the explicit prayer-purpose gloss.',
         [('( نماز پڑھنے کے لیے )', GLOSS)])
))
records.append(rec('bukhari:784',
    whole('companion_historical_report_reporting_prophetic_practice', 'Imran ibn Husayn describing Ali’s prayer at Basrah and its resemblance to prayer with the Prophet',
          'Read the complete Hindi field. Its actual finite event is prayer behind Ali, followed by Imran’s recollection and observation of Ali’s takbirs. Preserve the source’s Mutarrif spelling; do not recast Ali’s individual movements as a directly witnessed act of the Prophet.'),
    whole('companion_historical_report_reporting_prophetic_practice', 'Imran ibn Husayn describing Ali’s prayer at Basrah and its resemblance to prayer with the Prophet',
          'Read the complete Urdu field. Ali’s prayer, Imran’s remembrance of earlier Prophetic prayer and the raising/lowering takbirs are attributed exactly as supplied. There is no appended explanatory apparatus.')
))
records.append(rec('bukhari:785',
    whole('companion_practice_and_comparison_with_prophetic_prayer', 'Abu Salamah transmitting Abu Hurayrah’s prayer leadership and Abu Hurayrah’s own comparison',
          'Read the full Hindi field. The movements belong to Abu Hurayrah and the final first-person claim of close resemblance is his own statement; it is not direct speech of the Prophet. Preserve the supplied chain and honorifics.'),
    whole('companion_practice_and_comparison_with_prophetic_prayer', 'Abu Salamah transmitting Abu Hurayrah’s prayer leadership and Abu Hurayrah’s own comparison',
          'Read the full Urdu field independently. Keep Abu Hurayrah’s raising/lowering takbirs and his actual concluding comparison under his speaker identity, without adding a Prophetic approval.')
))
records.append(rec('bukhari:787',
    body('historical_observation_and_companion_statement', 'Ikrimah describing an unnamed man and reporting Ibn Abbas’s response',
         'Read the whole Hindi field. Ikrimah’s observation at Maqam Ibrahim and Ibn Abbas’s actual rebuke/question are finite historical content. The man stays unnamed and the rhetorical mother expression remains verbatim; only the parenthetic praying gloss is context.',
         [('(नमाज़ पढ़ते हुए)', GLOSS)]),
    body('historical_observation_and_companion_statement', 'Ikrimah describing an unnamed man and reporting Ibn Abbas’s response',
         'Read the entire Urdu field. Retain the actual standing/sitting/bowing takbir observation and the Companion’s rhetorical response. Separate the explicit explanation that the man was praying, without inventing his identity.',
         [('( نماز پڑھتے ہوئے )', GLOSS)])
))
records.append(rec('bukhari:788',
    body('historical_observation_and_companion_statement', 'Ikrimah reporting prayer behind an unnamed elderly man and Ibn Abbas’s answer',
         'Read the complete Hindi field, including the final alternate-chain sentence. The finite prayer, count of twenty-two takbirs, Ikrimah’s criticism and Ibn Abbas’s answer are the body. The parenthetic zuhr identification and explicit total-prayer explanation are context; the count and surrounding prayer setting remain. The final Musa/Aban/Qatadah chain supplies no further body and remains context.',
         [('(ज़ोहर की)', GLOSS), ('(तमाम नमाज़ में)', GLOSS)], stop='और मूसा बिन इस्माईल ने यूँ भी बयान किया'),
    body('historical_observation_and_companion_statement', 'Ikrimah reporting prayer behind an unnamed elderly man and Ibn Abbas’s answer',
         'Read the full Urdu field independently, including the alternate transmission tail. Preserve the elderly man’s anonymity, the twenty-two count and the complete rebuke. Separate the two parenthetic explanations and the final chain-only corroboration, which adds no event wording.',
         [('( ظہر کی )', GLOSS), ('( تمام نماز میں )', GLOSS)], stop='اور موسیٰ بن اسماعیل نے یوں بھی بیان کیا')
))
records.append(rec('bukhari:790',
    whole('historical_report_of_instruction_with_unstated_instructor', 'Musab ibn Sad describing his own hands and quoting his father’s explanation',
          'Read the whole Hindi field. Musab’s action and his father’s correction are actual events. The father describes being prohibited and instructed in passive wording; the text does not name the issuer, so no direct Prophetic speaker is supplied. The father remains identified by the supplied relationship.'),
    whole('historical_report_of_instruction_with_unstated_instructor', 'Musab ibn Sad describing his own hands and quoting his father’s explanation',
          'Read the complete Urdu field. Retain the joined palms, thighs, correction and knees instruction exactly. The passive prohibition/instruction remains passive, with no identity imported from a parallel.')
))
records.append(rec('bukhari:791',
    whole('companion_statement', 'Zayd ibn Wahb reporting Hudhayfah ibn al-Yaman’s admonition to an unnamed worshipper',
          'Read the full Hindi field. Hudhayfah’s criticism of incomplete bowing/prostration and the conditional warning if the man died are his own actual words. Preserve the source’s description of the sunnah on which Muhammad was created; do not normalize it or attribute this rebuke as a direct Prophetic quotation.'),
    whole('companion_statement', 'Zayd ibn Wahb reporting Hudhayfah ibn al-Yaman’s admonition to an unnamed worshipper',
          'Read the complete Urdu field independently. The unnamed recipient stays unnamed and the death warning remains conditional. This is the Companion’s supplied admonition, not a new project ruling.')
))
records.append(rec('bukhari:792',
    whole('prophetic_report', 'Al-Bara ibn Azib describing the relative duration of the Prophet’s prayer positions',
          'Read the full Hindi field. Keep the approximate equality and the explicit exceptions for standing and the sitting of tashahhud, which limit the timing claim. There is no separate lexical or locator apparatus.'),
    whole('prophetic_report', 'Al-Bara ibn Azib describing the relative duration of the Prophet’s prayer positions',
          'Read the entire Urdu field. Its bowing, prostration, intervening pause and post-bowing duration comparison remains qualified by approximately and the two stated exceptions.')
))


records.append(rec('bukhari:797',
    whole('companion_practice_and_comparison_with_prophetic_prayer', 'Abu Salamah transmitting Abu Hurayrah’s promise to demonstrate similar prayer and his subsequent qunut practice',
          'Read the complete Hindi field. Abu Hurayrah’s comparison, specified prayers/last rakahs and timing after sami Allah are actual content. The final yani clause states his concrete supplication for believers and imprecation against unbelievers; it is a narrated action description, not merely a lexical definition, and remains under that Companion’s practice.'),
    whole('companion_practice_and_comparison_with_prophetic_prayer', 'Abu Salamah transmitting Abu Hurayrah’s promise to demonstrate similar prayer and his subsequent qunut practice',
          'Read the complete Urdu field independently. Retain the actual utterance, the last-rakah timing in each named prayer and the final description of whom he prayed for/against. The introductory yani does not turn these finite narrated actions into an external compiler ruling.')
))
records.append(rec('bukhari:798',
    body('companion_statement', 'Anas stating that qunut is recited in fajr and maghrib',
         'Read the full Hindi field. Its report body is Anas’s passive statement about the two prayers; the text does not name a Prophetic speaker or an individual performer. The parenthetic expansion of Abu Qilabah’s name is source identification context.',
         [('(अब्दुल्लाह बिन ज़ैद)', GLOSS)]),
    body('companion_statement', 'Anas stating that qunut is recited in fajr and maghrib',
         'Read the full Urdu field. Preserve Anas’s supplied statement and passive form without assigning it to a missing actor. Separate only the parenthetic personal-name gloss in the chain.',
         [('(عبداللہ بن زید)', GLOSS)])
))
records.append(rec('bukhari:799',
    whole('prophetic_report', 'Rifaah ibn Rafi al-Zuraqi reporting the prayer utterance of an unnamed man and the Prophet’s response',
          'Read the entire Hindi field. The actual prayer formulas, question, unnamed man’s acknowledgment and the report of more than thirty angels remain complete. Keep the unusual supplied honorific for Imam Malik and the original quantitative wording.'),
    whole('prophetic_report', 'Rifaah ibn Rafi al-Zuraqi reporting the prayer utterance of an unnamed man and the Prophet’s response',
          'Read the entire Urdu field independently, including all the quotation punctuation and embedded directional marks. These are actual prayer utterances within the event, not external scripture reference apparatus; the speaking man stays unnamed.')
))
records.append(rec('bukhari:800',
    whole('historical_prayer_report_with_source_attribution_ambiguity', 'Thabit transmitting Anas’s account of the Prophet’s prayer, with the source’s later pronoun and honorific left unresolved',
          'Read the complete Hindi field. The opening says Anas described the Prophet’s prayer, while the subsequent aap pronouns carry Prophetic honorifics in this translation. Preserve that supplied ambiguity instead of silently deciding whether the demonstration subject is Anas or the Prophet. The prolonged standing and observers’ thought that he forgot are actual finite report wording.'),
    whole('historical_prayer_report_with_source_attribution_ambiguity', 'Thabit transmitting Anas’s account of the Prophet’s prayer, with the source’s later pronoun and honorific left unresolved',
          'Read the full Urdu field independently. Keep the exact Anas/Prophetic-prayer framing and later honorific/pronouns as written; do not repair their referent from another language or source. Retain the observers’ conjecture as conjecture, not a finding that the prayer leader forgot.')
))
records.append(rec('bukhari:801',
    whole('prophetic_report', 'Al-Bara ibn Azib describing the relative duration of the Prophet’s prayer positions',
          'Read the whole Hindi field. Preserve this occurrence’s own approximate equality statement. It has no added standing/tashahhud exception, so no wording is imported from the separately reviewed792 occurrence.'),
    whole('prophetic_report', 'Al-Bara ibn Azib describing the relative duration of the Prophet’s prayer positions',
          'Read the complete Urdu field. The stated bowing/prostration/post-bowing/sitting comparison is admitted exactly, with approximately retained and no expansion from any parallel.')
))
records.append(rec('bukhari:802',
    excerpts('Read the full Hindi field. Its chain is shortened/damaged and remains so. The first actual component is Malik ibn al-Huwayrith’s demonstration outside the prayer time; the second is Abu Qilabah’s own comparison with Abu Yazid and description of that teacher’s sitting before standing. Keep the one-occasion parenthesis as event framing; separate only the explicit by-praying explanation. Preserve khare/tumninat source defects.',
        [passage(None, 'अबू किलबह ने बयां किया', 'companion_prayer_demonstration_reporting_prophetic_practice', 'Abu Qilabah describing Malik ibn al-Huwayrith’s prayer demonstration', 'malik-demonstration'),
         passage('अबू किलबह ने बयां किया', None, 'scholarly_historical_observation', 'Abu Qilabah comparing Malik’s prayer with Abu Yazid and describing Abu Yazid’s practice', 'abu-qilabah-comparison')],
        [('(नमाज़ पढ़ कर)', GLOSS)]),
    excerpts('Read the complete Urdu field. Preserve the named Malik demonstration and the separately attributed Abu Qilabah/Abu Yazid comparison as two actual components. The outside-prayer-time fact and one-occasion framing stay; the parenthetic by-praying identification becomes source context. No missing Hindi chain is supplied from this fuller Urdu.',
        [passage(None, 'ابوقلابہ نے بیان کیا', 'companion_prayer_demonstration_reporting_prophetic_practice', 'Abu Qilabah describing Malik ibn al-Huwayrith’s prayer demonstration', 'malik-demonstration'),
         passage('ابوقلابہ نے بیان کیا', None, 'scholarly_historical_observation', 'Abu Qilabah comparing Malik’s prayer with Abu Yazid and describing Abu Yazid’s practice', 'abu-qilabah-comparison')],
        [('( نماز پڑھ کر )', GLOSS)])
))
records.append(rec('bukhari:803',
    whole('companion_practice_and_comparison_with_prophetic_prayer_with_source_text_defects', 'The supplied Hindi transmitters describing Abu Hurayrah’s prayer and his comparison; final pronoun left as supplied',
          'Read the complete Hindi field. Preserve the abbreviated chain, missing transition and damaged hamidah quotation without completing them from Urdu. The finite Abu Hurayrah prayer sequence, first-sitting transition, oath and comparison remain. The final honorific pronoun and death statement are retained verbatim without inventing an unstated referent.'),
    whole('companion_practice_and_comparison_with_prophetic_prayer', 'Abu Bakr ibn Abd al-Rahman and Abu Salamah describing Abu Hurayrah’s prayer and his comparison; final pronoun left as supplied',
          'Read the full Urdu field independently. Keep every actual takbir/prayer formula, obligatory/nonobligatory and Ramadan/other-month qualifications, the prayer sequence and oath. Preserve the final source pronoun in the until-death statement rather than borrowing or assigning a name from another occurrence.')
))


records.append(rec('bukhari:805',
    excerpts('Read the entire Hindi field. Its chain is truncated, while Anas remains explicitly named. Preserve the main fall/injury/prayer account, Sufyan’s finite seated-prayer variant, the resumed Prophetic instruction, and the finite arm/shin injury variants in their original order. These are alternative transmitted components of one report family, not independent eyewitness reports by Sufyan or Ibn Jurayj. The preposition comparison, Ma’mar same-report/memory check and isolated wording comparison stay context. No anatomy or missing chain is filled from Urdu.',
        [passage(None, 'सुफ़यान ने अक्सर', 'prophetic_report', 'Anas’s account as transmitted in the supplied damaged Hindi chain', 'main-opening', 'horse-fall-prayer-variants'),
         passage('इस गिरने से', 'सुफ़यान ने एक मर्तबा कहा', 'prophetic_report', 'Anas’s account as transmitted in the supplied damaged Hindi chain', 'main-opening', 'horse-fall-prayer-variants'),
         passage('सुफ़यान ने एक मर्तबा कहा', 'जब आप (सल्लल्लाहु अलैहि वसल्लम) नमाज़ से फारिग हो गए', 'transmitted_finite_variant_report', 'Sufyan transmitting an alternative wording of Anas’s seated-prayer account, not claiming his own eyewitness presence', 'seated-prayer-variant', 'horse-fall-prayer-variants'),
         passage('जब आप (सल्लल्लाहु अलैहि वसल्लम) नमाज़ से फारिग हो गए', '(सुफ़यान ने अपने शागिर्द', 'prophetic_report', 'Resumed instruction within Anas’s transmitted account of the Prophet’s prayer', 'main-instruction-resumed', 'horse-fall-prayer-variants'),
         passage('सुफ़यान ने ये भी कहा', 'जब हम ज़ुहरी के पास से निकले', 'transmitted_finite_variant_report', 'Sufyan recalling al-Zuhri’s supplied right-arm injury wording in the same account', 'right-arm-variant', 'horse-fall-prayer-variants'),
         passage('जब हम ज़ुहरी के पास से निकले', None, 'transmitted_finite_variant_report', 'Ibn Jurayj reporting his presence at al-Zuhri’s transmission of the right-shin wording', 'right-shin-variant', 'horse-fall-prayer-variants')]),
    excerpts('Read the complete Urdu field. Retain the main Anas report and the separately attributed finite seated-prayer, right-arm and right-shin variants as ordered components of the same source report family. Sufyan transmits the original account rather than becoming its eyewitness. Keep the preposition substitution, Ma’mar corroboration/memory appraisal and isolated prayer-wording comparison outside the report quotations. Preserve the differing side/arm/shin wording exactly, with no harmonization.',
        [passage(None, 'سفیان نے اکثر', 'prophetic_report', 'Anas’s account as transmitted through al-Zuhri and Sufyan', 'main-opening', 'horse-fall-prayer-variants'),
         passage('اس گرنے سے', 'سفیان نے ایک مرتبہ کہا', 'prophetic_report', 'Anas’s account as transmitted through al-Zuhri and Sufyan', 'main-opening', 'horse-fall-prayer-variants'),
         passage('سفیان نے ایک مرتبہ کہا', 'جب آپ صلی اللہ علیہ وسلم نماز سے فارغ ہو گئے', 'transmitted_finite_variant_report', 'Sufyan transmitting an alternative wording of Anas’s seated-prayer account, not claiming his own eyewitness presence', 'seated-prayer-variant', 'horse-fall-prayer-variants'),
         passage('جب آپ صلی اللہ علیہ وسلم نماز سے فارغ ہو گئے', '( سفیان نے اپنے شاگرد', 'prophetic_report', 'Resumed instruction within Anas’s transmitted account of the Prophet’s prayer', 'main-instruction-resumed', 'horse-fall-prayer-variants'),
         passage('سفیان نے یہ بھی کہا', 'جب ہم زہری کے پاس سے نکلے', 'transmitted_finite_variant_report', 'Sufyan recalling al-Zuhri’s supplied right-arm injury wording in the same account', 'right-arm-variant', 'horse-fall-prayer-variants'),
         passage('جب ہم زہری کے پاس سے نکلے', None, 'transmitted_finite_variant_report', 'Ibn Jurayj reporting his presence at al-Zuhri’s transmission of the right-shin wording', 'right-shin-variant', 'horse-fall-prayer-variants')])
))
records.append(rec('bukhari:808',
    whole('companion_statement_with_qualified_transmitter_recollection', 'Hudhayfah’s admonition, with Abu Wail’s qualified recollection of the final warning',
          'Read the full Hindi field. Its abbreviated chain remains unrepaired. The finite observation and you-have-not-prayed admonition are followed by Abu Wail’s I-seem-to-remember qualification and an actual conditional warning. Retain that uncertainty with the warning instead of turning the final recollection into an unqualified statement.'),
    whole('companion_statement_with_qualified_transmitter_recollection', 'Hudhayfah’s admonition, with Abu Wail’s qualified recollection of the final warning',
          'Read the complete Urdu field independently. Preserve the supplied full chain, the unnamed worshipper and Abu Wail’s explicit memory uncertainty before Hudhayfah’s if-you-die warning. It is an actual finite attributed addition, not merely a similarity pointer.')
))
records.append(rec('bukhari:809',
    body('prophetic_report_of_received_instruction', 'Ibn Abbas reporting that the Prophet was instructed concerning prostration',
         'Read the complete Hindi field. Keep the stated seven body parts and the hair/clothes instruction. The issuer of the passive command remains unstated. Separate the parenthetic introduction to the list and the added nose gloss, while preserving every body part explicitly enumerated outside those glosses.',
         [("(वो सात अ'ज़ा यह हैं)", GLOSS), ("(म' नाक)", GLOSS)]),
    body('prophetic_report_of_received_instruction', 'Ibn Abbas reporting that the Prophet was instructed concerning prostration',
         'Read the entire Urdu field. Preserve the source grammar and the actual enumerated parts; separate the two explicit explanatory parentheses, including the nose identification, without adding a different enumeration from another report.',
         [('( وہ سات اعضاء یہ ہیں )', GLOSS), ('( مع ناک )', GLOSS)])
))
records.append(rec('bukhari:811',
    body('prophetic_report', 'Abdullah ibn Yazid transmitting al-Bara ibn Azib’s description of following the Prophet’s prostration',
         'Read the whole Hindi field. The statement that al-Bara could not lie is the transmitter’s reliability appraisal and remains context, not al-Bara’s prayer observation. The parenthetic explanation of the prayer formula is also context. Preserve the actual formula and the complete waiting-until-forehead-on-ground condition.',
         [('वो झूठ नहीं बोल सकते थे।', 'The transmitter’s reliability appraisal is source context, not the observed prayer report or a Prophetic statement.'),
          ('(यानी रुकू से सर उठाते)', GLOSS)]),
    body('prophetic_report', 'Abdullah ibn Yazid transmitting al-Bara ibn Azib’s description of following the Prophet’s prostration',
         'Read the complete Urdu field independently. Keep the actual congregational timing observation, but separate the transmitter’s not-a-liar appraisal and the explicit parenthetic explanation of raising the head. No separate identity or certainty is inferred from the appraisal.',
         [('وہ جھوٹ نہیں بول سکتے تھے۔', 'The transmitter’s reliability appraisal is source context, not the observed prayer report or a Prophetic statement.'),
          ('( یعنی رکوع سے سر اٹھاتے )', GLOSS)])
))
records.append(rec('bukhari:814',
    body('prophetic_prayer_setting_and_instruction_with_unstated_instructor', 'Sahl ibn Sad describing the worshippers’ short garments and a passively reported instruction to the women',
         'Read the full Hindi field. Preserve the tied-garment setting and the condition that the men first sit fully. The source does not name who gave the women the instruction, so that issuer is not supplied. Separate only the explicit prostration-position gloss.',
         [('(सज्दा से)', GLOSS)]),
    body('prophetic_prayer_setting_and_instruction_with_unstated_instructor', 'Sahl ibn Sad describing the worshippers’ short garments and a passively reported instruction to the women',
         'Read the entire Urdu field. Keep the reason for the garment arrangement, the temporal restriction and the passive instruction. The parenthetic from-prostration identification is retained as context.',
         [('( سجدہ سے )', GLOSS)])
))
records.append(rec('bukhari:815',
    whole('prophetic_report_of_received_instruction', 'Ibn Abbas reporting that the Prophet was instructed concerning seven bones and hair/clothes',
          'Read the whole Hindi field. Preserve this shorter actual account without importing the detailed enumeration from809. The command remains passively attributed to an unstated issuer.'),
    whole('prophetic_report_of_received_instruction', 'Ibn Abbas reporting that the Prophet was instructed concerning seven bones and hair/clothes',
          'Read the complete Urdu field. Its seven-bones statement and hair/clothes prohibition are the entire finite report; nothing is appended from another occurrence.')
))
records.append(rec('bukhari:820',
    whole('prophetic_report', 'Al-Bara ibn Azib describing the duration of prostration, bowing and sitting between prostrations',
          'Read the full Hindi field. Keep the three stated positions and approximately equal qualifier exactly. No unmentioned standing or other timing element is added.'),
    whole('prophetic_report', 'Al-Bara ibn Azib describing the duration of prostration, bowing and sitting between prostrations',
          'Read the complete Urdu field independently, including the supplied chain names and the approximate duration comparison. No lexical apparatus or reference label is present.')
))


records.append(rec('nasai:751',
    body('companion_statement', 'Qatadah reporting his question to Jabir ibn Zayd and Jabir’s transmission of Ibn Abbas’s statement',
         'Read the full Hindi field. The actual question and Ibn Abbas’s attributed answer about a menstruating woman and dog remain Companion-level content. Yahya ibn Said’s final comment that Shubah narrated it marfu is attribution apparatus, not additional report wording and not a basis for promoting the supplied answer to direct Prophetic speech.',
         stop="याहया बिन सईद कहते हैं"),
    body('companion_statement', 'Qatadah reporting his question to Jabir ibn Zayd and Jabir’s transmission of Ibn Abbas’s statement',
         'Read the complete Urdu field independently. Retain the finite question/answer at its actual attribution. The final marfu-transmission assessment is retained as source context rather than used to invent a missing Prophetic speaker.',
         stop='یحییٰ بن سعید کہتے ہیں')
))
records.append(rec('nasai:752',
    whole('prophetic_historical_report_with_explicit_transmission_paraphrase', 'Ibn Abbas reporting riding with al-Fadl and passing part of the row, with the source’s paraphrase qualification retained',
          'Read the complete Hindi field. Its parenthesis explicitly qualifies the following narrated words as their reported meaning; keep that qualification with the finite account rather than silently converting paraphrase to verbatim wording. Preserve Arafat, the female donkey, partial row crossing and no recorded response.'),
    body('prophetic_historical_report_with_explicit_transmission_paraphrase', 'Ibn Abbas reporting riding with al-Fadl and passing part of the row, with the source’s paraphrase qualification retained',
         'Read the entire Urdu field. Keep the transmitter’s parenthetic paraphrase qualification, which governs the following body rather than defining a word. The only detached apparatus is the numbered footnote glyph. Preserve the supplied Arafah wording and nonbreaking space.',
         [('۱؎', FOOTNOTE)]),
    ar=whole('prophetic_historical_report_with_explicit_transmission_paraphrase', 'Ibn Abbas reporting the donkey arrival and row crossing, with the transmitted meaning qualifier',
             'Read the full own Arabic chain and body. Retain thumma dhakara kalimatan manaha as the explicit transmission qualification and all the finite dismounting/grazing/no-response actions. No outside place wording is substituted.'),
    en=whole('prophetic_historical_report_with_explicit_transmission_paraphrase', 'Ibn Abbas reporting the donkey arrival and row crossing, with the transmitted meaning qualifier',
             'Read the full own English field through its unclosed final quotation. Retain Then he said something to that effect as the source’s qualification, not an invented verbatim claim; preserve missing terminal punctuation and spacing exactly.')
))
records.append(rec('nasai:754',
    whole('prophetic_report', 'Ibn Abbas reporting passing the praying Prophet and the two girls who approached his knees',
          'Read the whole Hindi field. Keep both finite episodes, the unnamed Hashimi boy, the two Abd al-Muttalib girls and both no-breaking-prayer statements. No personal identity or legal conclusion is added.'),
    body('prophetic_report', 'Ibn Abbas reporting passing the praying Prophet and the two girls who approached his knees',
         'Read the complete Urdu field independently. Both actual episodes and their stated outcomes remain. Remove only the explicit footnote marker from the admitted text, preserving it as context.',
         [('۱؎', FOOTNOTE)])
))
records.append(rec('nasai:755',
    whole('prophetic_report', 'Aishah describing her position before the praying Prophet and her own movement',
          'Read the full Hindi field. Preserve Aishah’s stated reluctance to cross before him and her actual sliding movement; it is her reported thought/action, not an added generalized ruling.'),
    body('prophetic_report', 'Aishah describing her position before the praying Prophet and her own movement',
         'Read the complete Urdu field. Keep her intention, reluctance and subsequent movement; the terminal numbered footnote marker alone is context.',
         [('۱؎', FOOTNOTE)])
))
records.append(rec('nasai:762',
    body('prophetic_report', 'Aishah describing the mat prayer, the Prophet’s instruction and his subsequent practice',
         'Read the entire Hindi field. Retain the parenthetic only-as-much quantity restriction with the actual as-you-are-able instruction; it limits the injunction rather than defining a term. Keep the mat, followers, reward wording, continuity advice and until-death account exactly. The smaller parenthetic identification of what people tire from is explicit explanatory context.',
         [('(अमल से)', GLOSS)]),
    body('prophetic_report', 'Aishah describing the mat prayer, the Prophet’s instruction and his subsequent practice',
         'Read the complete Urdu field independently. Retain the restrictive quantity framing and the full actual narrative/quotation, including the source’s reward wording and persistence. Separate only the parenthetic from-work explanatory identification; no theology is rewritten from another language.',
         [('( عمل سے )', GLOSS)]),
    ar=whole('prophetic_report', 'Aishah reporting the mat prayer and the Prophet’s instruction and subsequent practice',
             'Read the entire own Arabic chain and body, including ma tutiqun, hatta tamallu, the continuity/minimum qualification and the final prayer-place/persistence account. All are actual supplied report text; nothing is filled from translations.'),
    en=body('prophetic_report', 'Aishah reporting the mat prayer and the Prophet’s instruction and subsequent practice',
            'Read the entire own English field. Preserve the instruction’s as-much-as-you-can restriction, until relation, continuity qualification and imperfect ending. The parenthetic reward and death explanations are retained in context; their nonparenthetic equivalents in independently reviewed Hindi/Urdu are not erased or normalized.',
            [('(of giving reward)', GLOSS), ('(in death)', GLOSS)])
))
records.append(rec('nasai:765',
    body('prophetic_report', 'Salamah ibn al-Akwa asking about his shirt and reporting the Prophet’s fastening instruction',
         'Read the full Hindi field and its own Arabic/English siblings. The finite question and fastening-with-even-a-thorn answer are admitted; the parenthetic yes-pray phrase explicitly spells out an implied permission and stays as source explanation. No absent answer words are supplied to another language.',
         [('(हां पढ़ लो)', GLOSS)]),
    body('prophetic_report', 'Salamah ibn al-Akwa asking about his shirt and reporting the Prophet’s fastening instruction',
         'Read the full Urdu field independently. Preserve the hunt, sole-shirt condition, actual question and fastening instruction, including even a thorn. The parenthetic affirmative explanation is source context rather than part of the unqualified quoted answer.',
         [('( ہاں پڑھ لو )', GLOSS)]),
    ar=whole('prophetic_report', 'Salamah ibn al-Akwa asking about his shirt and reporting the Prophet’s fastening instruction',
             'Read the full own Arabic chain and dialogue. It supplies the finite wazurruhu instruction with wa-law bi-shawkah; no separate nam/yes is added from the Hindi/Urdu parentheses.'),
    en=whole('prophetic_report', 'Salamah ibn al-Akwa asking about his shirt and reporting the Prophet’s fastening instruction',
             'Read the complete own English field. Keep the question and Fasten it to yourself even with a thorn as written, including its missing closing quotation punctuation and original spacing.')
))
records.append(rec('nasai:766',
    body('prophetic_prayer_setting_and_instruction_with_unstated_instructor', 'Sahl ibn Sad describing the garment arrangement and a passive instruction to the women',
         'Read the entire Hindi field. The source’s children comparison, garment arrangement and until-men-sit-upright limit remain. The issuer of the instruction is unstated. The parenthetic identification of the women as praying behind the men is explanatory context.',
         [('(जो मर्दों के पीछे पढ़ रही थीं)', GLOSS)]),
    body('prophetic_prayer_setting_and_instruction_with_unstated_instructor', 'Sahl ibn Sad describing the garment arrangement and a passive instruction to the women',
         'Read the complete Urdu field. Preserve the actual comparison, setting and temporal restriction without inventing the instructor. Separate only the explicit parenthetic explanation of the women’s position.',
         [('( جو مردوں کے پیچھے پڑھ رہی تھیں )', GLOSS)])
))


records.append(rec('nasai:770',
    whole('prophetic_report', 'Uqbah ibn Amir describing the silk garment, prayer and the Prophet’s subsequent statement',
          'Read the full Hindi field. Retain the appearance-qualified as-if-disliking-it observation and the exact subsequent statement. The source’s spelling of the gift word is not normalized; no general ruling is added.'),
    whole('prophetic_report', 'Uqbah ibn Amir describing the silk garment, prayer and the Prophet’s subsequent statement',
          'Read the complete Urdu field. The gift, wearing, prayer, forceful removal, qualified observation and actual quoted statement are all finite report content with no detached apparatus.')
))
records.append(rec('nasai:773',
    body('prophetic_report', 'Aishah describing the shared garment, local washing and repeated prayer/rest sequence',
         'Read the entire Hindi field, including both conditional contacts and both no-going-beyond descriptions. The two identical parenthetic blood identifications are explicit explanations and are each retained as context at their own exact position. Keep the menstrual setting and all actual conditional/repeated actions, including the source typo lete.',
         [('(ख़ून)', GLOSS, 2)]),
    body('prophetic_report', 'Aishah describing the shared garment, local washing and repeated prayer/rest sequence',
         'Read the complete Urdu field independently. Preserve each conditional event and the restriction to the affected place. Both occurrences of the blood-identification gloss are separately bounded source context; the rest of the account remains unchanged.',
         [('( خون )', GLOSS, 2)])
))
records.append(rec('nasai:781',
    whole('prophetic_report_with_transmitter_wording_variation', 'Malik ibn al-Huwayrith reporting his visit with a relative/companion and the Prophet’s travel instruction',
          'Read the full Hindi field. Retain the parenthetic sometimes-he-said qualification between cousin and companion: it is an actual transmitted wording variation, not a lexical label, and removing it would erase uncertainty. The two-person travel condition and elder-leadership instruction remain intact.'),
    body('prophetic_report_with_transmitter_wording_variation', 'Malik ibn al-Huwayrith reporting his visit with a relative/companion and the Prophet’s travel instruction',
         'Read the full Urdu field. Preserve the variant cousin/companion phrasing and its supplied split parenthesis, without harmonizing the description. Separate only the terminal footnote marker.',
         [('۱؎', FOOTNOTE)])
))
records.append(rec('nasai:785',
    whole('prophetic_historical_report', 'Anas describing the Prophet’s final prayer with the people behind Abu Bakr',
          'Read the complete Hindi field. Keep its own last-prayer claim, behind-Abu-Bakr placement and garment arrangement exactly. Do not reconcile chronology or leadership with neighboring sources.'),
    whole('prophetic_historical_report', 'Anas describing the Prophet’s final prayer with the people behind Abu Bakr',
          'Read the complete Urdu field independently. The shoulder/underarm garment details and the source’s final-prayer attribution are actual report wording, with no additional illness or posture imported.')
))
records.append(rec('nasai:786',
    whole('prophetic_historical_report', 'Aishah reporting Abu Bakr’s prayer leadership while the Prophet was in the row',
          'Read the entire short Hindi field. It contains a finite leadership event and the Prophet’s stated position in the row, so it is actual body rather than a chain-only pointer. No seated/standing or illness detail is added.'),
    whole('prophetic_historical_report', 'Aishah reporting Abu Bakr’s prayer leadership while the Prophet was in the row',
          'Read the entire Urdu field. Preserve the short independent event exactly, including Abu Bakr’s leadership and the Prophet being in the row; no continuation is borrowed.')
))
records.append(rec('nasai:791',
    whole('prophetic_report', 'Anas describing the Prophet’s private conversation after the iqamah and the people beginning to sleep',
          'Read the whole Hindi field. The iqamah, private conversation with an unnamed man and delay until the people began sleeping are actual supplied events. No ablution conclusion or person identity is inferred.'),
    body('prophetic_report', 'Anas describing the Prophet’s private conversation after the iqamah and the people beginning to sleep',
         'Read the complete Urdu field independently. Preserve the until relation and all finite actions; only the numbered footnote glyph becomes context.',
         [('۱؎', FOOTNOTE)])
))
records.append(rec('nasai:793',
    whole('prophetic_report', 'Sahl ibn Sad reporting the reconciliation visit, Abu Bakr’s leadership and the Prophet’s subsequent instructions',
          'Read the complete long Hindi field. Preserve the Banu Amr ibn Awf dispute, zuhr/asr timing, conditional instruction to Bilal, Abu Bakr’s usual attention, clapping, hand signal, thanksgiving, backward movement and complete Abu Quhafah answer. The final men/women instruction remains its actual quoted wording; no parallel version supplies changes.'),
    body('prophetic_report', 'Sahl ibn Sad reporting the reconciliation visit, Abu Bakr’s leadership and the Prophet’s subsequent instructions',
         'Read the complete long Urdu field independently. All dialogue and ordered actions, including Abu Bakr’s usual nonturning behavior and the conditional prayer instruction, remain. The one internal footnote marker after the Prophet moves through the people is exact source apparatus, not narrative wording.',
         [('۱؎', FOOTNOTE)])
))
records.append({'key': 'nasai:796', 'decision': 'exclude',
    'reason': 'All five complete fields were read. Every field provides only another transmission chain and a similarity pointer, with no finite report body. Keep the entire occurrence as resolved source-only evidence; no content is imported from795 or another source.',
    'fields': {
        'hi': context('Read the entire Hindi field: this chain also transmits a similar hadith from Abu Nadrah. It is only a chain/similarity pointer, with the supplied haidith spelling left unchanged.'),
        'ur': context('Read the entire Urdu field: the same chain also narrates a similar hadith from Abu Nadrah. No event, act or saying body is present.'),
        'ar': context('Read the full Arabic chain through Suwayd ibn Nasr, Abd Allah, al-Jurayri and Abu Nadrah, ending nahwahu. It supplies no finite report body.'),
        'en': context('Read the entire English field: another chain from Abu Nadrah, with Abu Saeed as a parenthetic chain identification, and similar narration. Neither the name nor the pointer supplies a body.'),
        'ur-Latn': context('Read the complete Roman Urdu field: Is sanad se bhi Abu Nadra se isi jaisi hadith marwi hai. It is only the similarity-pointer sentence, not report content.')
    }
})


records.append(rec('nasai:798',
    body('prophetic_report', 'Jabir describing the Prophet’s zuhr leadership and Abu Bakr’s audible repetition',
         'Read the full Hindi field. Preserve the actual zuhr, behind-position and repeated Allahu akbar statements. The parenthetic identification of what Abu Bakr made audible is explanatory context, while the surrounding transmission action stays.',
         [('(आप की तकबीर)', GLOSS)]),
    body('prophetic_report', 'Jabir describing the Prophet’s zuhr leadership and Abu Bakr’s audible repetition',
         'Read the entire Urdu field independently. Keep the actual leadership and repetition sequence; separate only the parenthetic pronoun/object identification.',
         [('( آپ کی تکبیر )', GLOSS)])
))
records.append(rec('nasai:802',
    whole('prophetic_historical_report_with_narrative_time_qualification', 'Anas describing the household visit, the Prophet’s invitation to pray and the subsequent prayer',
          'Read the complete Hindi field. Preserve the named aunt Umm Haram, unnamed orphan and supplied household group. The parenthetic statement that this was not a prayer time is a finite narrator’s timing qualification, not a word definition or words newly attributed to the Prophet; keep it within the narrated account.'),
    whole('prophetic_historical_report_with_narrative_time_qualification', 'Anas describing the household visit, the Prophet’s invitation to pray and the subsequent prayer',
          'Read the full Urdu field independently. The quoted invitation and narrator’s parenthetic outside-prayer-time statement remain under their distinct roles inside the same historical report. Do not fill a particular prayer or identify the orphan.')
))
records.append(rec('nasai:804',
    whole('prophetic_report', 'Ibn Abbas describing his place beside the Prophet and Aishah’s prayer behind them',
          'Read the entire Hindi field. Preserve the repeated beside-the-Prophet wording and the explicit Aishah identity exactly, without harmonizing them with another household-prayer occurrence.'),
    whole('prophetic_report', 'Ibn Abbas describing his place beside the Prophet and Aishah’s prayer behind them',
          'Read the complete Urdu field. Both the repeated spatial statement and Aishah’s named placement are actual source content; no identity or missing detail is borrowed.')
))
records.append(rec('nasai:805',
    whole('prophetic_report', 'Anas reporting prayer with an unnamed woman of his household and the Prophet',
          'Read the entire Hindi field. The finite placement of Anas on the right and the household woman behind is complete body. The woman stays unnamed; she is not identified from802 or any parallel.'),
    whole('prophetic_report', 'Anas reporting prayer with an unnamed woman of his household and the Prophet',
          'Read the full Urdu field independently. Preserve the right/behind placements and the supplied household relationship without filling a personal name.')
))
records.append(rec('nasai:808',
    body('companion_historical_dialogue_with_source_address_variation', 'Qays ibn Ibad reporting the man identified as Ubayy ibn Kab; the final Abu Yaqub address remains unreconciled',
         'Read the complete Hindi field. Keep Qays’s anger and loss of attention, the post-prayer turning sequence, the actual covenant claim and the later threefold statement/dialogue. The parenthetic salutation-completion phrase supplies narrative timing and remains with the event. Separate only the lexical ahd and defective hukm glosses; preserve the actual Abu Yaqub address without reconciling it to Ubayy through outside identity knowledge. The covenant is Ubayy’s reported assertion, not an invented direct Prophetic quote.',
         [('(अहद)', GLOSS), ('(हुक्म)', GLOSS)]),
    body('companion_historical_dialogue_with_source_address_variation', 'Qays ibn Ibad reporting the man identified as Ubayy ibn Kab; the final Abu Yaqub address remains unreconciled',
         'Read the complete Urdu field independently. The prayer-row encounter, stated covenant, qiblah turn, repeated declaration and question/answer are actual Companion historical content. Keep the salutation-completion timing qualifier and the source’s Abu Yaqub address. The ahd/hukkam synonym parentheses are lexical context, not separate report words.',
         [('( عہد )', GLOSS), ('( حکام )', GLOSS)])
))
records.append(rec('nasai:809',
    body('prophetic_report', 'Abu Hurayrah describing the lined-up congregation, the Prophet’s departure before takbir and his washed return',
         'Read the entire Hindi field. Preserve the crucial before-takbir timing, stay-in-place instruction, continuous standing wait and return with dripping hair, followed by takbir and prayer. Separate only the two explicit technical identifications of the takbir; no alternate account’s timing is substituted.',
         [('(तकबीर-ए-तहरीमा)', GLOSS), ('(तहरीमा)', GLOSS)]),
    body('prophetic_report', 'Abu Hurayrah describing the lined-up congregation, the Prophet’s departure before takbir and his washed return',
         'Read the full Urdu field independently. Keep the doubled ke wording and all temporal relations exactly. The two parenthetic tahrimah explanations remain source context; the finite sequence is not harmonized with another report.',
         [('( تکبیر تحریمہ )', GLOSS), ('( تحریمہ )', GLOSS)])
))
records.append(rec('nasai:814',
    whole('prophetic_report', 'Anas reporting the Prophet’s instruction to align the rows before the opening takbir',
          'Read the complete Hindi field. The solid-wall comparison and seeing-behind explanation are actual supplied quoted words, with the before-takbir timing retained. There is no detached locator or footnote to remove.'),
    body('prophetic_report', 'Anas reporting the Prophet’s instruction to align the rows before the opening takbir',
         'Read the complete Urdu field. Retain the actual wall simile and the entire stated reason; separate only the one internal footnote glyph, preserving its adjacent nonbreaking spaces.',
         [('۱؎', FOOTNOTE)])
))


# Independent second-reading amendment v2. The original frozen v1 remains
# unchanged at the parent workspace and is included as before evidence.
_by_key = {record['key']: record for record in records}
_restored_qualifiers = {
    ('bukhari:788', 'hi'): ('(तमाम नमाज़ में)', 'Read the complete Hindi field. Restore the explicit total-prayer qualifier with the twenty-two takbir count, because it scopes that number to the whole prayer. Keep the zuhr-identification gloss and the final alternate-chain pointer as context. Preserve the unnamed elderly man and Ibn Abbas’s actual response.'),
    ('bukhari:788', 'ur'): ('( تمام نماز میں )', 'Read the complete Urdu field. Retain the total-prayer qualification with the twenty-two count. Only the zuhr identification and final chain-only corroboration remain context; the count is not presented without its source scope.'),
    ('bukhari:809', 'hi'): ("(म' नाक)", 'Read the full Hindi instruction. Retain with-nose because it supplies an actual member restriction in the listed prostration instruction, rather than merely renaming an already supplied word. Only the parenthetic introduction to the seven-part list remains explanatory context. No different enumeration is imported.'),
    ('bukhari:809', 'ur'): ('( مع ناک )', 'Read the complete Urdu instruction. Preserve the sole supplied nose term with the forehead member and all the actual listed parts. Keep only the explicit list-introduction explanation as context; the passive command’s issuer remains unstated.'),
    ('bukhari:814', 'hi'): ('(सज्दा से)', 'Read the entire Hindi field. Retain the from-prostration restriction with the head-raising instruction so the quoted command is not broadened. Preserve the garment setting and until-men-sit-fully limit; the unnamed instruction-giver stays unnamed.'),
    ('bukhari:814', 'ur'): ('( سجدہ سے )', 'Read the complete Urdu field. Retain from-prostration as the domain of the head-raising instruction, alongside its temporal restriction. The clothing setting, passive attribution and all original words remain unchanged.'),
    ('nasai:765', 'hi'): ('(हां पढ़ लो)', 'Read the complete own Hindi question and answer. Retain the finite affirmative reply following he-said together with the fastening instruction; its parenthetic typography does not make it a lexical definition. The separately read Arabic/English lack that reply and are preserved independently, with no cross-language erasure or filling.'),
    ('nasai:765', 'ur'): ('( ہاں پڑھ لو )', 'Read the complete own Urdu dialogue. Keep the finite affirmative reply with the thorn-fastening answer exactly as supplied after he-said. Its absence in Arabic/English does not remove it from this source language; those fields remain unchanged.')
}
for (_key, _language), (_literal, _reason) in _restored_qualifiers.items():
    _field = _by_key[_key]['fields'][_language]
    _old = _field.get('omit_source_context', [])
    assert sum(item['text'] == _literal for item in _old) == 1
    _new = [item for item in _old if item['text'] != _literal]
    if _new:
        _field['omit_source_context'] = _new
    else:
        _field.pop('omit_source_context', None)
    _field['reason'] = _reason
for _language, _start, _stop in (
    ('hi', "ज़ुहरी ने यूँ कहा 'व लकल हम्द'", 'सुफ़यान ने ये भी कहा'),
    ('ur', 'زہری نے یوں کہا «ولك الحمد', 'سفیان نے یہ بھی کہا')
):
    _field = _by_key['bukhari:805']['fields'][_language]
    assert len(_field['spans']) == 6
    _field['spans'].insert(4, passage(_start, _stop,
        'transmitted_prayer_formula_variant',
        'Al-Zuhri’s transmitted prayer-formula wording within the Anas report family, not a new eyewitness or personal-prayer claim by al-Zuhri',
        'dhikr-formula-variant', 'horse-fall-prayer-variants'))
    _field['reason'] = (
        'Read the entire own-language field. Preserve six ordered components in one report family: '
        'the main opening, Sufyan’s seated-prayer variant, the resumed instruction, al-Zuhri’s affirmative '
        'prayer-formula wording, and the right-arm/right-shin variants. The actual dhikr formula is '
        'transmitted report content, not merely a word-form label. The preposition comparison and '
        'Ma’mar same-report/memory discussion remain context. All source damage, pronouns and '
        'body-part variants remain exact, without filling from another language.')


if __name__ == '__main__':
    assert len(records) == 50 and len({r['key'] for r in records}) == 50
    for collection in ('bukhari', 'nasai'):
        selected = [r for r in records if r['key'].startswith(collection + ':')]
        document = {'schema': 'hadith-bank-manual-complete-field-reading-specification-v1',
                    'source_checkpoint': CHECKPOINT,
                    'read_method': 'Every explicitly reviewed field was read completely before its individual semantic decision and exact source boundary were authored.',
                    'records': selected}
        (ROOT / ('manual-' + collection + '.json')).write_text(
            json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + '\n')

