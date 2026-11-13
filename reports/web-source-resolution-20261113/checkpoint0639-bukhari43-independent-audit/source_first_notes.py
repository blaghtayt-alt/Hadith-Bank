"""Independent complete original-field readings, recorded before candidate inspection."""
NOTES = {}
def pair(number, hi, ur):
    NOTES[('deenhindi-bukhari:' + number, 'hi')] = hi
    NOTES[('deenhindi-bukhari:' + number, 'ur')] = ur

pair('2228',
     'Read all298 Hindi characters. Anas reports Safiyyah among the captives, her initial assignment to Dihyah and subsequent marriage to the Prophet. All supplied words form the finite historical/Prophetic-action report; preserve the printed milin defect and no additional circumstance.',
     'Read all255 Urdu characters. The entire Anas account supplies the captivity, Dihyah assignment and subsequent marriage sequence. No appended commentary or missing body is present.')
pair('2230',
     'Read all237 Hindi characters. Jabir explicitly reports the Prophet selling a mudabbar slave. Preserve the printed technical term without adding an outside definition; the complete short chain/body is eligible.',
     'Read all216 Urdu characters. The complete Jabir report explicitly supplies the Prophet selling the mudabbar slave. No further legal explanation is added.')
pair('2231',
     'Read all209 Hindi characters. This own chain through Amr explicitly hears Jabir ibn Abdullah report the Messenger selling the mudabbar slave. Preserve this occurrence separately from2230.',
     'Read all181 Urdu characters. The whole own-field chain and finite Messenger-sale report are supplied. Keep its separate provider identity and exact technical term.')
pair('2232',
     'Read all344 Hindi characters. Zayd ibn Khalid and Abu Hurayrah explicitly report the Messenger’s answer regarding the unmarried slave woman, successive conditions and sale after third or fourth occasion. The source’s uncertainty and all conditional scope remain; no extra penalty or certainty is supplied.',
     'Read all315 Urdu characters. The whole question/answer is actually supplied under the two Companions’ hearing attribution. Keep the unmarried qualification, repeat conditions and third-or-fourth uncertainty.')
pair('2233',
     'Read this separate344-character Hindi field in full. Its repeated Zayd/Abu Hurayrah question/answer is supplied with the same third-or-fourth uncertainty and unmarried condition; preserve this own occurrence, without identity merge.',
     'Read this separate315-character Urdu occurrence in full. Its actual wording independently supplies the report. Preserve all conditions and the count uncertainty, despite the identical wording of2232.')
pair('2239',
     'Read all575 Hindi characters. Ibn Abbas reports the arrival and existing fruit-salam periods followed by the Prophet’s measure/weight instruction. The alternative one/two versus two/three years must stay visibly unsettled; the explicit Ismail uncertainty belongs to transmission framing, never Prophetic speech. The repeated Medina identification is lexical context; the source-supplied verb in the alternative-years clause can remain actual narrative completion.',
     'Read all526 Urdu characters. Preserve Ibn Abbas’s arrival/practice report and the Messenger’s actual dates measure/weight instruction. The one/two or two/three-year uncertainty is material and must not become a settled number. The Ismail doubt is a qualified source-transmission voice. The Medina apposition is redundant identity context; the alternate-period action phrase supplies the source’s actual predicate.')
pair('2239.2',
     'Read all92 Hindi characters. This is a same-report notice plus the nominal terms known measure and known weight, without the underlying operative statement. The entire field remains context.',
     'Read all84 Urdu characters. Only an Ibn Abi Najih same-as-above pointer and nominal measure/weight terms are supplied; no operative report predicate is present.')
NOTES[('deenhindi-bukhari:2239.2','ar')] = 'Read all133 Arabic characters. The chain and bi-hadha pointer end with the prepositional fi kaylin malum wa-waznin malum phrase. No independent operative predicate is supplied; keep the entire source as reviewed context.'
NOTES[('deenhindi-bukhari:2239.2','en')] = 'Read all66 English characters. This says as above and mentioning only specific measure. It is metalinguistic/nominal pointer wording, not the missing report body.'
NOTES[('deenhindi-bukhari:2239.2','ur-Latn')] = 'Read all103 Roman Urdu characters. Only same-report framing and nominal known-measure/known-weight terms are supplied. All five siblings have now been read and support source-only disposition, without reconstructing the omitted instruction.'
pair('2240',
     'Read all485 Hindi characters. Ibn Abbas supplies Medina arrival, dates contracts for two/three years and the Messenger’s actual fixed-weight/fixed-term instruction. The whole own field is finite and no lexical appendix is present.',
     'Read all429 Urdu characters. Preserve the complete arrival/practice/instruction sequence and its own weight/term conditions. Do not substitute the measure condition of another occurrence.')
pair('2240.2',
     'Read all145 Hindi characters. Ibn Abi Najih’s actual honorific-pronoun saying supplies known measure, known term and advance payment. The salaf parenthesis is a technical synonym of the already expressed advance-payment act and can remain context; preserve all operative conditions.',
     'Read all132 Urdu characters. The own abbreviated but finite attributed instruction is supplied. The salaf term in parentheses repeats the already stated advance-payment phrase; the measure/term predicates remain intact.')
pair('2241',
     'Read all382 Hindi characters. Ibn Abbas’s report has an actual arrival and weight/term instruction. The parenthetic Medina is the sole supplied destination, and the bai-salam phrase is the actual subject/object of the instruction in this own field; both meaning-bearing qualifications should remain, unlike a duplicate synonym.',
     'Read all342 Urdu characters. The source expressly supplies Medina as the arrival location only in parentheses, and bai-salam as what should have the fixed weight and term. Both carry actual source narrative/operative scope and should remain.')
pair('2242',
     'Read all450 Hindi characters. Preserve the narrator’s unresolved Muhammad-or-Abdullah name, the dispute and referral, Ibn Abi Awfa’s practice across the three named periods and Ibn Abza’s reported agreeing answer. The advance-sale and salaf parenthetical synonyms are explanatory context. Do not relabel the Companions’ practice as direct Prophetic speech.',
     'Read all410 Urdu characters. The narrator’s alternative name and actual questions/answers are supplied; Ibn Abi Awfa states collective practice and Ibn Abza gives the same answer. Keep the actors distinct. The paired advance-sale/salaf synonym labels can be context without deleting the acts.')
pair('2243',
     'Read all450 Hindi characters independently. The repeated dispute/referral/practice/agreement is this separate occurrence, with Muhammad-or-Abdullah uncertainty and source spellings retained. Parenthetic advance-sale/salaf labels are synonym context; the actual period/list/practice and answer remain.',
     'Read all410 Urdu characters. Preserve the independently supplied narrator uncertainty, Ibn Abi Awfa’s practice answer and Ibn Abza’s agreeing answer. The duplicate wording does not merge provider identities; only explanatory synonym parentheses are context.')
pair('2244',
     'Read all591 Hindi characters. The first inquiry and Abdullah’s actual wheat practice/availability answer are supplied. This field omits Urdu’s barley/olive items and much of the later Ibn-Abza testimony link; preserve its printed Kabzi name and broken sent-to/ka-mamla bridge. The resumed we-did-not-ask-about-farming clause may be retained only with its locally incomplete attribution, without filling Urdu’s missing Companions/Prophetic-era clause. Salaf is an advance-payment synonym.',
     'Read all668 Urdu characters. The complete two inquiries and Ibn Abi Awfa/Ibn Abza practice answers are supplied, with the actual wheat/barley/olive list and explicit second Companions/Prophetic-era frame. Keep each speaker and the no-availability-inquiry qualification; only the salaf synonym is context.')
pair('2245',
     'Read all201 Hindi characters. After the comparison notice, actual we-contracted-for-wheat/barley wording is supplied; Shaybani then gives an olive addition and another wheat/barley/raisin practice wording. Preserve these explicit reported variant voices, including the bounded olive addition whose operative practice is supplied in the same field. Do not assert an omitted ultimate Companion or Prophet identity.',
     'Read all197 Urdu characters. The supplied practice and separately attributed Shaybani addition/variant are actual wording, not a wholly empty pointer. Preserve the named transmitter voice while leaving the underlying unnamed we-group unresolved; no additional food is inferred.')
pair('2246',
     'Read all797 Hindi characters. Ibn Abbas’s answer supplies a full Prophetic fruit-sale prohibition. The subsequent question and nearby unnamed person’s estimating explanation are actual narrated dialogue and deserve their own non-Prophetic voice. The final Muadh chain and bare prohibited/same-hadith tail provide no new operative object; keep that transmission appendix context rather than fabricate another complete prohibition.',
     'Read all740 Urdu characters. The full prohibition and the actual unnamed bystander’s answer about estimating are separately voiced report content. The final repeated chain plus bare prohibited and same-hadith notice is transmission apparatus without the repeated operative body; preserve it in context.')
pair('2247',
     'Read all594 Hindi characters. Abu al-Bakhtari separately questions Ibn Umar and Ibn Abbas. The first actual report includes dates and silver-for-gold credit prohibitions; the second has its own edible/weighing wording. Keep two source report voices and all conditions. The advance-sale parenthesis is a technical synonym.',
     'Read all571 Urdu characters. The two named Companion answers supply separate Prophetic report content with differing conditions. Preserve both faithfully and keep the explanatory advance-sale synonym contextual, without replacing one answer with the other.')
pair('2248',
     'Read this separate594-character Hindi field in full. Its two actual Ibn Umar/Ibn Abbas answers and all conditions remain source-local, despite duplication of2247. The advance-sale explanation is synonym context only.',
     'Read this separate571-character Urdu occurrence in full. Keep the two Companion reports, the silver/gold condition and edible/weighing conditions exactly. No provider identity merge follows from the repeated text.')
pair('2249',
     'Read all650 Hindi characters. The separate Ibn Umar and Ibn Abbas prohibition answers are followed by an actual question and an unnamed nearby person’s harvest/store explanation. That finite answer is source dialogue under an unnamed speaker, not an editorial correction and not Prophetic speech. Preserve the whole own narrative and meanings.',
     'Read all624 Urdu characters. All supplied questions and three response voices are actual source content. The final harvest/storage explanation is attributed to a person seated nearby, so retain it separately qualified; do not substitute2246’s different estimate wording.')
pair('2250',
     'Read this separate650-character Hindi field in full. Its Ibn Umar and Ibn Abbas reports are followed by the actual unnamed seated person’s explanation. Preserve all voices and the harvest/store wording, without merging this repeated occurrence with2249.',
     'Read this separate624-character Urdu field in full. All three response voices and actual questions are supplied; the final attributed interpretation remains a separately qualified unnamed-person saying, not Prophetic wording.')
pair('2251',
     'Read all345 Hindi characters. Aisha explicitly reports the Messenger’s grain purchase on credit from a Jewish person and pledge of an iron coat of mail. The whole source chain/action report is supplied without added commentary.',
     'Read all310 Urdu characters. Aisha’s complete action report retains the creditor, credit purchase and exact pledged object. No inferred quantity or timing is inserted.')
pair('2253',
     'Read all589 Hindi characters. Ibn Abbas’s arrival/practice/instruction report is followed by a source-framed Ibn Abi Najih variant. The final parenthetic bai-salam-should-be phrase actually supplies the operative predicate for the printed measure/weight wording, so retain it as an explicitly qualified same-report variant rather than leaving a nominal fragment or inferring missing words.',
     'Read all538 Urdu characters. Preserve the main measure/term instruction and the separately framed measure/weight variant. Its parenthetic bai-salam-honi-chahiye is the supplied operative sentence completion, meaningfully different from a mere synonym, and belongs with that variant in the same report family.')
pair('2254',
     'Read all508 Hindi characters. The narrator reports referral to Ibn Abza and Ibn Abi Awfa, their actual joint practice with the Messenger and later Nabati trade, and their answer that they did not ask about crops. The salam parenthesis is only a synonym for salaf; all operative period/list/non-inquiry scope remains.',
     'Read all486 Urdu characters. The complete two-Companion practice and actual questions/answers are supplied. Preserve the joint speakers, list and fixed term, leaving only the salam synonym as explanatory context.')
pair('2255',
     'Read this separate508-character Hindi field in full. Its actual joint practice, referral and no-crops-inquiry answer are supplied independently; preserve the provider identity and all source words, with the salam synonym contextual.',
     'Read this separate486-character Urdu field in full. The duplicated content does not merge identities. Preserve the source’s actors, trade list, term and no-inquiry answer; the parenthetic salam synonym is context.')
pair('2256',
     'Read all342 Hindi characters. Abdullah reports the sale practice and the Prophet’s actual prohibition. The subsequent Nafi explanation of the technical habl-al-habalah term is a lexical/transmission appendix, not another independently supplied numbered report; preserve it as context, including the printed jan-le wording defect.',
     'Read all318 Urdu characters. The practice/prohibition body is complete. Nafi’s appended definition of habl-al-habalah explicitly explains the term; keep that source apparatus visible as context rather than relabelling it Prophetic wording.')
pair('2257',
     'Read all422 Hindi characters. Jabir’s report supplies the Prophet’s preemption ruling with the undivided-property scope and the limiting boundary/changed-path condition. Preserve the complete own source conditions without projecting a broader rule.',
     'Read all383 Urdu characters. The whole report supplies the preemption ruling and its express divided-boundary/path limitation. Retain the final limiting sentence within the source’s Jabir framing, without adding an outside legal interpretation.')
pair('2259',
     'Read all463 Hindi characters. The two chains lead to Aisha’s actual two-neighbor gift question and the Prophet’s nearer-door answer. The second-chain label is transmission apparatus, while the full question/answer and source chains remain exactly supplied.',
     'Read all432 Urdu characters. Preserve Aisha’s question and the Messenger’s actual answer, with the printed chains. Only the explicit second-chain label is an explanatory apparatus insertion; do not count the two chains as two reports.')
pair('2261',
     'Read all631 Hindi characters. Abu Musa reports arrival with two Ashar men, his disclaimer and the Messenger’s actual refusal to appoint an office-seeker. The my-tribe parenthesis states the men’s relationship to the narrator and can remain meaningful actor scope. The final unnamed-transmitter lan/la word-choice uncertainty is formula-comparison apparatus and must stay visible context, without changing the actual ruling.',
     'Read all581 Urdu characters. Keep the two companions’ tribe relation, Abu Musa’s own lack-of-knowledge statement and the Prophet’s no-appointment reply. The closing lan-versus-la uncertainty is lexical transmission discussion rather than a fresh Prophetic saying; preserve it as context.')
pair('2263',
     'Read all866 Hindi characters. Preserve the source’s abbreviated chain, printed Aisa name and defective cave wording, without repairing them from Urdu. The hiring, guide’s affiliation/pledge, trust, camels, three-night meeting and coastal journey are actual finite narrative. The migration-time parenthesis is actual setting. The entire khirrit-definition sentence is explicit word apparatus and stays context.',
     'Read all892 Urdu characters. Aisha’s full source chain and the Prophet/Abu Bakr guide-hiring sequence are supplied. Keep migration timing, pledge/trust, three-night arrangement and coastal route. The explicit hadith-word khirrit means expert-guide sentence is lexical apparatus, distinct from the surrounding actual narrative.')
pair('2265',
     'Read all816 Hindi characters. Yaala’s campaign/appraisal and employee biting dispute lead to the Prophet’s actual ruling/question. A separate grandfather-route report supplies Abu Bakr’s no-diyah judgment; keep these distinct report families/voices. The Tabuk name is an identity gloss for Jaysh-al-Usrah; the complaint-purpose phrase supplies an actual action purpose and can remain.',
     'Read all760 Urdu characters. Preserve the two actual finite reports: Yaala’s encounter with the Prophet and the separately transmitted Abu Bakr ruling. Do not attribute the latter to the Prophet. The campaign-name gloss is context; the coming-with-complaint circumstance meaningfully supplies the action setting.')
pair('2266',
     'Read this separate816-character Hindi field in full. The own Yaala/Prophet episode and grandfather-route Abu Bakr judgment are supplied independently. Preserve distinct families, the actual complaint circumstance and all source words; the Tabuk identification is explanatory context.',
     'Read this separate760-character Urdu occurrence in full. The duplicate wording does not merge its source identity. Keep the Prophet’s ruling and Abu Bakr’s separate ruling distinctly attributed, with the meaningful complaint-purpose phrase retained.')
pair('2274',
     'Read all494 Hindi characters. Ibn Abbas reports the Prophet’s caravan and city/rural seller prohibitions, then gives an actual answer about brokerage. Commercial and beyond-the-market parentheses meaningfully restrict the caravan encounter; removing them would broaden the printed prohibition. Retain the separate Ibn Abbas explanation as actual narrated dialogue, not Prophetic words.',
     'Read all455 Urdu characters. The commercial-caravan and before-market qualifiers are operative scope, not merely noun synonyms. Preserve them, the Prophet’s actual prohibitions and the question/Ibn Abbas brokerage answer under its own voice.')
pair('2275',
     'Read all960 Hindi characters. Khabbab reports his work/debt and the actual exchange with As ibn Wail, followed by the reported revelation and the source’s verse transliteration/translation. Keep actors and nested Quran wording distinct; As’s claim is his own hostile statement, not an endorsement. The mushrik label is an identity gloss that can remain context. No source-locator label is supplied here.',
     'Read all906 Urdu characters. Preserve Khabbab’s testimony, As ibn Wail’s separate statements and the reported revealed verse with its actual supplied Urdu rendering. The Quran quote is embedded source content, not new reviewer wording or a Prophetic saying. The mushrik apposition is contextual identification; no verse-number apparatus is present.')
pair('2276',
     'Read all2085 Hindi characters. The complete Abu Said account supplies the refused hospitality, unnamed Companion’s negotiated ruqya, actual Fatiha-opening recitation, recovery, payment and later Prophet approval/share request/laughter. Preserve all voices and the actual Surah Fatiha name as the object of the Prophet’s question, not a citation locator. The final Shuba/Abu Bishr same-hearing notice is transmission context. Do not identify the unnamed treating Companion from external knowledge.',
     'Read all1931 Urdu characters. The whole episode and each actual dialogue are supplied, including the recited Arabic Fatiha opening, negotiated goats and the Prophet’s approval. Retain the actual Surah Fatiha name in his question and keep the unnamed Companion unnamed. The closing Shuba same-hearing chain notice remains apparatus context.')
pair('2277',
     'Read all397 Hindi characters. Anas reports Abu Taybah’s cupping, the Prophet’s wage order of one or two sa and the request to reduce his masters’ levy. The source’s one-or-two uncertainty must remain; no exact quantity is inferred.',
     'Read all358 Urdu characters. The entire cupping/payment/intercession account is supplied, with the uncertain one-or-two-sa wage. Preserve all source actions and that unresolved number.')
pair('2278',
     'Read all362 Hindi characters. Ibn Abbas reports the Prophet’s cupping and payment, followed by an actual if-it-were-unlawful inference under the report’s narrator framing. Keep the inference separately qualified as a Companion/narrator appraisal, not words spoken by the Prophet; it is not a wholly separate independent transmission.',
     'Read all334 Urdu characters. Preserve the actual cupping/payment report and the following inferential explanation under the source’s Ibn Abbas reporting frame. The conditional appraisal is not a direct Prophetic quotation and should have its own qualified component in the same family.')
pair('2279',
     'Read all319 Hindi characters. The actual cupping/payment report is followed by a finite if-there-were-karahat rhetorical inference. Retain it as narrator/Companion reasoning under the printed report frame rather than direct Prophetic speech, with the colloquial ending exact.',
     'Read all289 Urdu characters. Both actual action/payment and the final conditional appraisal are supplied. Keep the latter separately qualified under the report’s narrator framing, preserving the source’s colloquial ka-hai-ko wording.')
pair('2283',
     'Read all259 Hindi characters. Abu Hurayrah explicitly reports the Prophet’s prohibition concerning the slave women’s zina earnings. The complete short chain and actual prohibition are supplied; no source commentary or additional ruling is present.',
     'Read all224 Urdu characters. The whole Abu Hurayrah report supplies the actual prohibition under explicit Prophetic attribution. Preserve wording and source identity without additional legal extrapolation.')
pair('2284',
     'Read all271 Hindi characters. Ibn Umar explicitly reports the Prophet’s prohibition of taking the fee described by the source’s damaged nar-kadanay term. Keep that technical/source token exactly rather than silently replacing it with an outside definition.',
     'Read all241 Urdu characters. Ibn Umar’s finite prohibition report is supplied in full. Preserve the printed narkadanay term and its exact source attribution; no modern explanatory wording is added.')
pair('2289',
     'Read all1558 Hindi characters. Salamah reports all three funeral cases: first neither debt nor assets; second debt with three dinars; third three-dinar debt with no assets, followed by Abu Qatadah’s guarantee and the Prophet’s prayer. Keep every question/answer, amount and speaker, especially the Companion’s own guarantee separately within the narrative. No compiler appendix is present.',
     'Read all1406 Urdu characters. The whole three-case funeral account is supplied. Preserve the distinct debt/assets conditions, the three-dinar quantities and Abu Qatadah’s actual payment undertaking, without treating the Companion’s promise as Prophetic words.')
pair('2292',
     'Read all922 Hindi characters. This is Ibn Abbas’s numbered interpretive/historical statement about verse wording, heirs, migration brotherhood and the stated inheritance change. The actual quoted verse words and their operative definition subject are source content, not an external locator; the parenthetic mawaliya-meaning phrase completes the definition. The story-this-is bridge and later repeated brotherhood clarification are explanatory context; the final third-of-estate practical appendix is unattributed explanatory context. Preserve the actual Companion interpretation without turning it into Prophetic speech or silently certifying the claim.',
     'Read all844 Urdu characters. Preserve Ibn Abbas’s actual verse interpretation, historical brotherhood account, stated inheritance change and source permission wording under his own voice. The Quran words and mawali definition subject remain; no surah-number citation is supplied. The generic story bridge, repeated explanatory brotherhood gloss and final practical third-of-estate appendix can stay context rather than be attributed as fresh Prophetic words.')
pair('2293',
     'Read all288 Hindi characters. Anas explicitly reports the Messenger establishing brotherhood between the arriving Abd al-Rahman ibn Awf and Sad ibn Rabi. The whole short own-field report is supplied without explanatory appendix.',
     'Read all257 Urdu characters. The actual arrival/brotherhood report is complete under Anas’s explicit source attribution. Preserve both names and all wording; no identity from another entry is merged.')
pair('2299',
     'Read all363 Hindi characters. Ali explicitly reports the Prophet’s instruction that he give the sacrificed animals’ coverings and skins as charity. Retain the source’s exact two objects and sacrifice relation; no outside rule is supplied.',
     'Read all331 Urdu characters. The complete Ali report and actual instruction are supplied. Preserve the skins/coverings and sacrificed-animal scope exactly.')
pair('2301',
     'Read all1622 Hindi characters. Abd al-Rahman ibn Awf supplies the protection agreement, naming dispute and Badr pursuit/failed protection episode with Umayyah and Bilal’s actual words. Keep the detailed actions, source family-or-property alternative and all violence as historical source narration, not Prophetic instruction. The hostile identity apposition and repeated incoming-party identification can be contextual glosses. The final he-used-to-show-us scar statement changes to an unnamed later witnessing voice, so retain it as a qualified same-family observation rather than Abd al-Rahman’s own first-person speech.',
     'Read all1534 Urdu characters. The complete Abd al-Rahman/Umayyah agreement and Badr episode are supplied with named dialogue and all source defects. Preserve the hostile apposition/incoming-party gloss as context while keeping all actual actions and Bilal’s words. The last scar-showing observation is a later narrator’s us-frame with no uniquely named eyewitness in that clause; keep that voice distinct within the same report family.')
