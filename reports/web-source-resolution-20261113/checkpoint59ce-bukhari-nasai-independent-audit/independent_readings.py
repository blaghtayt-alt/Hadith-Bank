"""Independent complete-field observations, recorded before ledger comparison."""

READINGS = {}


def both(key, hindi, urdu):
    READINGS[key] = {'hi': hindi, 'ur': urdu}


both('bukhari:690.2',
    'Complete Abu Nuaym/Sufyan/Abu Ishaq same-report pointer; the parenthesis also points to an unprinted preceding report. No report body.',
    'Complete same-chain/as-above statement, with no actual reported event or speech body.')
READINGS['bukhari:690.2'].update({
    'ar': 'Read the whole haddathana Abu Nuaym/an Sufyan/an Abi Ishaq/nahwahu bi-hadha chain. No matn is supplied.',
    'en': 'Read the complete short field: narrator Abu Ishaq followed only by As above. Source-only supported.',
    'ur-Latn': 'Read the whole Roman pointer including its parenthetic preceding-hadith explanation. No supplied body.',
})
both('bukhari:695',
    'Read the complete Uthman exchange and separately introduced al-Zuhri opinion. Hindi lacks the explicit siege/you-are-the-imam framing supplied in Urdu; do not insert it. Uthman permits joining good while avoiding bad; al-Zuhri gives a separate condition-limited legal saying, not Prophetic speech.',
    'Read the full besieged-Uthman scene and question about the rebel-appointed imam, his good-versus-bad answer, and the separately transmitted al-Zuhri saying with its necessity exception. These two actual voices require distinct attribution.')
both('bukhari:698',
    'Read the entire Ibn Abbas/Maymuna night-prayer report: move left to right, thirteen rakats, sleep/snoring, caller and no new ablution. Witr-included and Fajr parentheticals are explanatory; the final Amr/Bukayr same-transmission corroboration is source apparatus.',
    'Read all Urdu words independently, including habitual snoring as part of the report and the concluding transmitter verification. Preserve thirteen and the no-ablution condition; do not add a missing body from the final pointer.')
both('bukhari:700',
    'Read the complete chain and Muadh praying with the Prophet then leading his people. Actual Companion practice, not Muadh\u2019s words relabelled as Prophetic speech.',
    'Read the complete separate provider occurrence. Preserve its own chain and Muadh\u2019s two prayer settings; do not merge with711.')
both('bukhari:704',
    'Read the man\u2019s long-Fajr complaint, Abu Masud\u2019s description of the Prophet\u2019s anger and the instruction to shorten prayer for weak/old/occupied people. The from-prayer/people parenthesis is explanatory context.',
    'Read the entire independently supplied complaint, anger and instruction. Keep the actual named reporter and stated reasons; the parenthetic object explanation is context.')
both('bukhari:708',
    'Read Anas\u2019s shortest-but-complete prayer observation and shortening upon hearing a child lest the mother be distressed. The motive is unparenthesized actual narrative wording and should remain.',
    'Read the complete Urdu field. Both lightness/completeness and the mother\u2019s possible distress are actual supplied qualifications, not generic detachable commentary.')
both('bukhari:711',
    'Read this separate Sulayman/Abu Numan/Hammad/Ayyub/Amr/Jabir transmission of Muadh\u2019s two prayer settings. Keep711 distinct from700.',
    'Read the complete Urdu chain and practice report independently; no side explanation or locator appears in its body.')
both('bukhari:719',
    'Read Anas\u2019s report of the prayer call, the Messenger turning towards the people, straight/close rows and seeing behind his back. Entire actual instruction supplied.',
    'Read the complete Urdu chain and the row/seeing-behind instruction. No explanatory parenthesis or source locator is embedded.')
both('bukhari:726',
    'Read Ibn Abbas\u2019s night prayer, being moved by the head to the right, sleep, caller and prayer without new ablution. Hindi prints Qutaib in the chain; preserve it without replacing it from Urdu. Home/tahajjud and caller-purpose parentheses are context.',
    'Read all Urdu wording; it prints Kurayb and doubled punctuation in the chain. The two supplied setting/purpose explanations are separable; the actual movement/sleep/no-ablution sequence remains.')
both('bukhari:727',
    'Read Anas and an orphan boy praying behind the Prophet with Umm Sulaym behind them. The orphan\u2019s parenthetic personal name is an identity gloss, not independent narrator evidence for other fields.',
    'Read the complete Urdu report. The mother is explicitly named in main text; the boy\u2019s parenthetic identity is context. Preserve the actual spatial arrangement.')
both('bukhari:728',
    'Read Ibn Abbas standing on the left, head-or-arm alternative, movement right and the hand gesture. The nested home parenthesis and tahajjud label are explanatory; preserve the actual head-or-arm uncertainty.',
    'Read the whole Urdu account independently. Do not collapse head or arm into one choice, and do not delete the actual gesture as an inferred paraphrase; it is supplied narrative.')
both('bukhari:733',
    'Read the fall/injury/seated-prayer scene and the instruction to follow the imam through takbir, bow, rising, the two printed dhikr formulas and prostration. The formulas are actual recitation content.',
    'Read the complete Urdu sequence and both Arabic formulas. These are spoken-prayer text, not Quran locator labels or editorial apparatus.')
both('bukhari:740',
    'Read Sahl\u2019s passive report that people were ordered to place the right hand on the left wrist. The later Abu Hazim attribution and Ismail active/passive wording comparison are transmission apparatus; the initial command\u2019s giver is not named in its own clause.',
    'Read the full Urdu field. Sahl\u2019s actual transmitted instruction is distinguishable from the following discussion of whether/how it is raised to the Prophet. Preserve that qualification without changing the source to direct Prophetic speech.')
both('bukhari:747',
    'Read Abdullah ibn Yazid\u2019s sermon framing and al-Bara\u2019s standing-until-prostration observation. The not-a-liar appraisal is narrator criticism/assessment, not matn. The Companions identity and final then-they-prostrated parentheses are explanations.',
    'Read the entire Urdu chain and observation. Preserve the actual timing and keep narrator reliability and the two added explanations separately visible as context.')
READINGS['bukhari:747'].update({
    'ar': 'Read the complete Arabic chain, sermon setting, wa-kana ghayra kadhub reliability appraisal and the standing-until-seeing-prostration body. The appraisal is not part of the observed prayer act.',
    'en': 'Read all English text. The parenthetic al-Bara-not-a-liar statement is source assessment; the Prophet honorific stays with the actual report. The observed timing is finite and complete.',
})
both('bukhari:748',
    'Read the eclipse prayer, people\u2019s forward/backward question and the Prophet\u2019s Paradise/cluster/until-world-exists answer. The in-prayer parenthesis is setting clarification; the counterfactual condition must remain.',
    'Read every Urdu clause independently. Preserve both the desired cluster and the if-I-had-taken-it counterfactual rather than reporting actual acquisition.')
both('bukhari:754',
    'Read the whole curtain/Fajr/rows/smile/Abu Bakr retreat/near-disruption/gesture/death narrative. Illness, emotion and seeing-him explanations are context candidates, but goya (as if) in the long parenthesis limits the following prayer-abandonment statement and must not be lost. Preserve the source\u2019s chasht death-time wording.',
    'Read the full Urdu narrative. The goya (as if) scope inside the long parenthesis matters: dropping it would turn near-disruption into an unqualified departure statement. Preserve the printed chasht wording despite Arabic/English\u2019s differing end-of-day phrase.')
READINGS['bukhari:754'].update({
    'ar': 'Read all Arabic clauses through wa-tuwuffiya min akhiri dhalika al-yawm. Keep the Muslims\u2019 near/intended disruption and the ending time literally; do not alter it to the target-language chasht phrase.',
    'en': 'Read the complete English narrative. Intended to leave is qualified action, and the parenthetic verge-of-trial wording is an explanatory phrasing. Preserve the last-hours-of-that-day ending independently.',
})
both('bukhari:755',
    'Read every damaged Hindi clause. Several chain, complaint and Saad-identifying segments are absent; the accuser is unnamed and the booty-distribution clause lacks Urdu\u2019s second negation. Do not repair any of those. Preserve Saad\u2019s conditional prayer, the old man\u2019s own curse explanation, and separate Abdul Malik\u2019s actual later eyewitness account. The parenthetic recitation/hear/seeing/cause/consequence explanations are context.',
    'Read the complete Urdu complaint/investigation account, the named Usama ibn Qatada/Abu Sada accusation, Saad\u2019s if-he-is-lying prayer, the man\u2019s later self-description and Abdul Malik\u2019s separate eyewitness observation. The person\u2019s curse explanation is his assertion, not an independently verified causal judgment.')
both('nasai:683',
    'Read Abu al-Shatha\u2019s observation of Abu Hurayra and a man leaving after adhan. The disobedience judgment is Abu Hurayra\u2019s own saying, not a quoted command of the Prophet.',
    'Read the complete Urdu occurrence independently. Preserve the observer, Abu Hurayra\u2019s judgment and Abu al-Qasim honorific without merging684.')
both('nasai:684',
    'Read the entire damaged Hindi field. It supplies the leaving-after-adhan event and a disobedience judgment but loses the named judge before the stranded anhu closing. Keep that voice unnamed; do not insert Abu Hurayra from Urdu or683.',
    'Read the full Urdu report, which explicitly names Abu Hurayra as the judge. This own-field named attribution is supported separately from the damaged Hindi.')
both('nasai:686',
    'Read Kurayb\u2019s question, Ibn Abbas\u2019s eleven-with-Witr/sleep/snoring/Bilal/two-rakat/leading-prayer report and no-again-ablution clause. Salat al-layl is a lexical synonym; the word again limits the final negation.',
    'Read the whole Urdu field. The parenthetic salat al-layl synonym is an explanation; parenthetic phir se (again) limits no ablution and should not become an assertion of no ablution ever.')
both('nasai:701',
    'Read Talq\u2019s full delegation, pledge, prayer, remaining-water request, demolition/building instruction, water/distance exchange, return, adhan and monk episode. The kalisa synonym is lexical context; the monk\u2019s truth-call statement belongs to the monk, not the Prophet.',
    'Read all Urdu clauses, including the added go-purpose parenthesis, church synonym, mixing-water statement and final Tay monk\u2019s speech/disappearance. Preserve the actual distinct speakers and report uncertainty without inventing a later fate.')
both('nasai:702',
    'Read the complete fourteen-day arrival, Banu Najjar escort, Abu Ayyub arrival, prayer sites, land-price dialogue, graves/palms/ruins preparation and construction/chant. The final prayer is expressly the workers\u2019 plural saying while the Messenger was with them; do not present it solely as his direct speech.',
    'Read every Urdu clause and its printed grammatical defects. Keep the actual construction sequence, refusal of price and the final collective invocation under its supplied plural voice.')
both('nasai:703',
    'Read the Aisha/Ibn Abbas death-time cloth/breathing account and the supplied condemnation of turning prophets\u2019 graves into places of prostration. It is a complete reported utterance, without an added verse locator.',
    'Read the full Urdu field independently. Preserve the dual reporter attribution and the source\u2019s actual utterance; no new authenticity or legal conclusion is asserted.')
both('nasai:710',
    'Read the full Aisha/Saad wound/tent report. Ahzab is an alternative battle-name gloss. Hindi loses the named actor before the stranded alayhi-wasallam suffix; do not fill the tent-builder from Urdu.',
    'Read the complete Urdu report: it expressly names the Messenger as tent-builder. The Ahzab gloss and exact ۱؎ footnote marker are source apparatus, while the nearby-visiting purpose is actual supplied narrative.')
both('nasai:712',
    'Read the complete riders/Najd/Thumama/chief/pillar report. The captured-and-brought parenthesis is explanatory; the final this-is-an-abridgment statement is compiler context, not a reason to reject the finite body.',
    'Read the complete Urdu version independently. Preserve Thumama\u2019s actual name/tribe/chief status and being tied to a pillar, while retaining the abridgment notice separately.')
both('nasai:720',
    'Read the complete Alqama/Aswad/Abdullah same-report pointer. No supplied narration body.',
    'Read every Urdu word; it names transmitters and only says a similar report was mentioned. Source-only supported.')
READINGS['nasai:720'].update({
    'ar': 'Read the whole Ishaq/Nadr/Shuba/Sulayman/Ibrahim/Alqama/Aswad/Abdullah chain ending fa-dhakara nahwahu. No report body.',
    'en': 'Read the complete Sulaiman/Ibrahim chain and and-he-narrated-something-similar ending. The parenthetic narrate is transmission clarification, not matn.',
    'ur-Latn': 'Read the full Roman Urdu same-report pointer. No event, saying or supplied abbreviated body is present.',
})
both('nasai:732',
    'Read Abu Said ibn al-Mualla\u2019s own plural market/mosque/prayer practice during the Messenger\u2019s time. This is a Companion practice report, not an explicit command from the Prophet.',
    'Read the complete Urdu report independently, preserving the temporal setting and own plural practice without adding an unprinted instruction.')

assert len(READINGS) == 27
assert sum(len(fields) for fields in READINGS.values()) == 64
