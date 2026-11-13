# Independent semantic QC — patch08

**Result: pass after corrections, within the independently reviewed scope described below.** Candidate revision 4 has no remaining implementation finding from this review. All 32 source-limited semantic uncertainties remain unresolved; completing their investigation does not supply information missing from the source.

## Candidate and independence

This review binds candidate manifest SHA-256 `a8a0a5314abc92e2a75284567571deb495aaf240c32a525cd3266b1b512c49a5` and the 43,543-row semantic ledger SHA-256 `3628eb0009ad4e728ba3db8290c554ad1ffcf5592b6a62ac00471e8dbfa4f361`. The reviewer used the immutable parent PDF files and global-CP DOC story exports, displayed independently rendered page images, and read the selected source passages afresh. The author branches were not edited by this reviewer. The author applied the findings through qualified additive overlays, which were then independently rechecked.

The PDF sources contain 1,023 and 1,031 pages. Exact source text was read with CR and embedded controls preserved; CP offsets were evaluated against each story’s global start. Source spelling, printed contradictions and incomplete punctuation were not silently repaired.

## What was manually reviewed

The manual ledger sample comprises **950 of 16,837 original new rows**, plus **all 139 final correction rows**: **1,089 rows in total**, including 866 lexical rows and 223 nonlexical rows. Their exact source intervals cover 51,944 unique CP. Context read around them is recorded separately and is not used to inflate the ledger-row count. The 65 documented groups are purposive checks of specific semantic risks, not a random sample or an estimate of the error rate in the remainder.

- All 22 inherited uncertainty cases and all 10 newly reported cases were independently investigated against the targeted source images and DOC context. All 28 additive uncertainty qualification spans were read.
- Nineteen complete inventory gaps were read: 1, 5, 9, 22, 27, 71, 302, 422, 498, 613, 977, 1371, 1545, 1558, 1564, 1577, 2083, 2085 and 2102. These cover preface/Quran boundaries, numbered reports, nested dialogue, report variants, narrated practice, explanations and grades.
- The long Sahl report 802 was followed through its fighter, disputants, Prophetic response, Abu Darda and Sahl layers. Reports 854, 888, 893 and 901 were checked for Companion dialogue, anticipated versus actual responses, repeated question/answer turns and the Divine–servant dialogue. Five additional broad parents 5352, 5479, 24360, 24624 and 24702 were read completely in context.
- Sixteen reference parents, comprising 43 replacement rows, were read. Parents 7554, 7559, 7573 and 7594 were checked against the actual date-eating/fighting reports on V2 pages 289–291. Their action and participant-speech text must not be treated as a collection reference.
- All 49 nonbibliographic/nonseparator additions in the late/footnote branch were read, together with 18 complete surrounding source-note contexts. Additional bibliographic examples distinguish a collection title containing Sahih from a source-claimed chain grade.
- All 11 header-field rows and all 19 tail/cover rows were read. Field instructions and cached page numbers, publication credits and a grading-editor credit are apparatus rather than report authenticity conclusions.

**97 unique PDF pages were actually displayed.** Every page is listed in `actual_image_observations.jsonl`, with the render hash and targeted inspection scope. Preparing a render did not earn review credit. These were semantic inspections of relevant passages and local context, not 97 new full-page character reviews.

## Findings and verified corrections

| Finding class | Historical targets | Corrective result |
|---|---:|---|
| Collection reference included a Bengali grade |2|Hasan/Sahih claims separated from Abu Dawud/Tirmidhi references, delimiters, anchor and controls.|
| Bengali explanatory insertion remained inside a broad narration/attribution cue |8|Ten printed insertions separated, while surrounding narrative and attribution wording remain intact.|
| Quoted lexical text reverted to narration at a misplaced offset |52|39 Bengali Prophetic, 8 Arabic Prophetic and 5 Bengali participant-speech rows corrected.|
| Blank-only row affected by the same offset path |1|The one space receives a structural role; no speaker claim is attached to it.|

The first two grade/reference findings were in h888 and h893. A focused grade-term scan of new main-story reference/collection labels distinguished these genuine claims from Sahih appearing in a collection title. The findings were checked against the printed source, not accepted merely because a keyword matched.

The parenthesis follow-up first inspected all 18 matches in the newly added narration/scene/reporter label family. It separated actual explanatory insertions from named narrator cues, list ordinals and honorifics. Extending the same check to explicit attribution/introduction label variants produced eight further relevant main-story candidates after collection/reference metadata and already-qualified uncertainty labels were excluded. Five required additional insertion boundaries; the other three were correctly labeled honorifics or a translation-introduction cue. The two finite adjudication files record every decision. The source wording for the Jibril-report “third” qualification is not treated as a third named speaker.

The list-number example in h243 also exposed a separate voice error. A focused closing-quote scan produced 44 candidates; 36 were confirmed Prophetic-speech continuations incorrectly labeled as narration. The remaining eight were valid inner speech, narrated practice, or narration after only closing punctuation. The author traced the defect to helper-generated suffix anchors: a trailing whitespace suffix could be located at an earlier internal space. An isolated replay using exact integer offsets identified 53 affected old rows, including fragments without closing quotation marks and Arabic text. **Every proposed changed partition was independently read**; replay by itself was not treated as semantic proof. All 36 manually detected closing-quote errors are included in that causal set.

The final application contains 63 SHA-and-ordinal-qualified overlays and 139 exact replacement spans. Recheck verified each historical before-row, each bound prior-ledger prefix, every replacement CP slice and complete partition, and the final status/atomic views. All 63 superseded interpretations are inactive; all historical rows remain present; all 139 replacements are active and represented in the current atoms. The source text is unchanged. Detailed results are in `final_correction_recheck.json`.

## Source limitations retained

All 32 case decisions support retention. They concern unprinted quote/parenthesis endpoints, unnamed speakers or gloss suppliers, pronominal assessment subjects, and source-internal Arabic/Bengali attribution differences. The review does not select an external canonical identity to make the languages agree. Examples include h1616 Arabic linkage versus the Bengali named narrator; h1798 Abu Bakra/Abu Hurayra; h987 Abu Hurayra/Abu Abdullah; h990 Ibn Amr/Ibn Umar; and the h802 father/Bishr versus explicit Bengali Qays layer. The Sufyan transition and note 169 Ibn Hajar antecedent remain localized uncertainties.

The current uncertainty status view contains exactly the 32 independently reviewed IDs, all investigation-complete and none resolved. The retained qualified alternatives must remain available to downstream users. There are also 106 current atoms with more than one equal-width qualified leaf label. Their strings and identities were checked, and the source-limited combinations were reviewed through the case work; this report does not assert that every label pair is universally interchangeable.

## Mechanical checks, separate from manual semantic reading

Every one of the 16,976 new rows, including 139 corrections, was checked for exact immutable source text and valid global-CP bounds. There were zero source mismatches, zero duplicate new decision IDs and zero unexpected source-mutation/verified-grade/canonical-identity assertions in the checked fields. All 79 investigation-status overlays and 207 reference-refinement overlays were checked for qualified target identity and exact additive partition/link consistency. The 63 final correction overlays received the additional integrated-status check described above. These checks receive **zero manual semantic-review credit**.

The full candidate reconstruction, record preservation, all-source-unit partition and package checks belong to the separate engineering review. This semantic report does not substitute an automated exact-text pass for source interpretation.

## Exact remaining scope

**15,887 original new decision rows were not independently reread manually.** They received exact-source/CP checks and the author’s review. **1,957 PDF pages were not independently displayed by this reviewer.** Many displayed pages were examined only for their targeted passages. No claim is made of an exhaustive independent reread of 2,054 pages, every new semantic span, or every inherited semantic row.

No external canonical narrator identification, independent hadith grading or source-edition reconciliation was performed. These are source-faithful classifications and explicitly attributed source claims. The 32 retained ambiguities remain limitations of the supplied source, not unfinished coding corrections.

| Author branch | New rows checked mechanically | Rows manually read | Rows not manually read |
|---|---:|---:|---:|
|semantic_review|28|28|0|
|semantics_v1_early|199|80|119|
|semantics_v1_early_b|3,672|84|3,588|
|semantics_v1_early_c|1,938|61|1,877|
|semantics_v1_middle|3,775|176|3,599|
|semantics_v1_late_and_notes|1,010|86|924|
|semantics_v2_gaps|3,990|206|3,784|
|reference_refinement|389|43|346|
|header_story_review|11|11|0|
|semantics_broad_v1_root|543|80|463|
|semantics_broad_v1|1,263|76|1,187|
|root_scope_review|0|0|0|
|tail_review|19|19|0|
|qc_corrections|139|139|0|

The zero-row root_scope_review branch contributes the Sufyan uncertainty rather than new decision rows. Its source issue is included in the 32-case review.

## Actually displayed page inventory

- **v01:** 3, 11, 15, 31, 32, 33, 34, 70, 87, 110, 112, 139, 149, 156, 164, 241, 252, 282, 285, 289, 292, 304, 305, 317, 318, 324, 333, 422, 463, 517, 518, 554, 555, 556, 614, 621, 802, 803, 804, 823, 863, 864, 865, 866, 867, 904, 905, 929, 931, 932, 937, 938, 939, 976, 980, 981, 991, 1014, 1016.
- **v02:** 146, 149, 165, 200, 201, 202, 203, 232, 289, 290, 291, 469, 470, 480, 509, 510, 533, 624, 625, 688, 689, 690, 691, 710, 711, 802, 803, 838, 839, 840, 852, 906, 907, 912, 913, 914, 915, 916.

## Case-by-case independent observations

### qc-inherited-01 — p03-v01-p0112-unmatched-parenthesis-semantic-scope

Volume 1; displayed source pages: 112.

Two openings precede গুরুত্বপূর্ণ and তুমি; the visible close follows রেখো. The first endpoint is absent. The qualification preserves the identifiable Prophetic outer report and does not invent the explanatory scope.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-02 — p03-v02-1223-main-Divine-speech-end

Volume 2; displayed source pages: 200, 201, 202.

Arabic pp200–201 has one outer quotation continuing beyond وأنا أجزي به; Bengali p201 prints a close after the reward sentence. The main Arabic Divine endpoint remains source-limited. The full containing qualification is appropriate only with narrower introduction/reference/utterance children retained.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-03 — p03-v02-1223-Muslim-variant-Divine-speech-end

Volume 2; displayed source pages: 201, 202, 203.

The Muslim variant on p201 names God within an outer quotation but supplies no independent inner close. Bengali pp202–203 closes after the abstention-for-Me clause. Retaining an Arabic endpoint ambiguity is justified.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-04 — p04-v01-p0304-0305-unclosed-parenthesis-349726

Volume 1; displayed source pages: 304, 305.

The opening before কিন্তু on p304 remains unclosed through the h223 ending on p305. Inner explanatory pairs are visible. No endpoint should be synthesized from the following report or from an inner pair.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-05 — p05-v01-p0518-embedded-report-end

Volume 1; displayed source pages: 517, 518.

The starred paragraph on p518 is commentary and explicitly introduces Abu Hurayra’s report. The single opening before প্রত্যেকের has no matching close before the মুক্তিপণ explanation. The disputed যেহেতু sentence cannot be assigned exclusively to either voice from the typography.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-06 — p05-v01-p0554-0556-469-final-speaker-scope

Volume 1; displayed source pages: 554, 555, 556.

Arabic p554 switches from Abu Dharr’s account into the Prophet’s Gabriel retelling. Final قلت/قال lacks an explicit return to a named layer; Bengali p556 also leaves the wider retelling open. Both final-dialogue qualifications avoid asserting a final questioner or respondent.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-07 — p05-v01-p0621-536-definition-speaker

Volume 1; displayed source pages: 621.

Arabic p621 closes after اليد السفلى and then gives the giving/asking definition without a new speaker name. Bengali encloses that definition within the quoted translation. The different printed boundaries are preserved.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-08 — p05-root-v02-p0533-unclosed-explanatory-bracket

Volume 2; displayed source pages: 533.

The Bengali Quran rendering on p533 opens [ before অনুসরণ and never prints ]. The dash does not identify a bracket endpoint. The Arabic green Quran line and its reference remain distinct from the Bengali supplement.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-09 — p05-v02-footnote-cp1018528-1018577-source_pronominal_work_grade_report_subject_locally_unresolved-derived-semantic-uncertainty

Volume 2; displayed source pages: 469, 470.

Footnote502 on p470 opens with an explicit Albani first-person cue, then refers to Hakim and Daeefa before using তিনি for the very-weak claim. Its new pronominal grader is not uniquely named. This is a source grading comment, not a verified-grade determination.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-10 — p05-v02-main-cp0432880-0432932-Quran_following_clause_speaker_boundary_locally_unspecified-derived-semantic-uncertainty

Volume 2; displayed source pages: 480.

The Quran 3:37 excerpt on p480 contains Maryam’s reply and the ensuing إن الله يرزق clause without a separate inner ending delimiter in either language. The entire passage remains Quran; the internal speaker boundary is properly qualified.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-11 — p05-v02-footnote-cp1020929-1020948-source_Albani_comment_with_unspecified_pronoun_antecedent-derived-semantic-uncertainty

Volume 2; displayed source pages: 509, 510.

The Hasan Sahih line at the top of p509 belongs to h1525. h1526 supplies only Tirmidhi as its collection tail; footnote527 on p510 says তিনি এরূপই বলেছেন without a named claim antecedent. The uncertainty is real and cannot be filled from h1525.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-12 — p06-v01-p0803_0804_722_final_speaker

Volume 1; displayed source pages: 802, 803, 804.

Pages802–804 delimit the taught istikhara supplication and then introduce قال / তিনি বলেন without repeating a name. The final instruction is outside the supplication, with a further Bengali explanatory parenthesis. Qualification avoids over-attributing that final instruction.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-13 — p06-v01-p0823_746_final_exception_speaker

Volume 1; displayed source pages: 823.

Ibn Umar is the ongoing speaker in the Arabic/Bengali discourse on p823. The further exception follows ثم يقول / তারপর বললেন, so contextual Ibn Umar discourse is supported; its ultimate prophetic versus explanatory attribution is not explicitly resolved.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-14 — p06-v02-p0625-1616-source-reporter-antecedent

Volume 2; displayed source pages: 624, 625.

The preceding h1615 on p624 names Ibn Abbas. Arabic h1616 on p625 uses وعنه, while the Bengali h1616 attribution explicitly names Jabir. The bilingual presentation difference is visible and retained.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-15 — p06-v02-p0688-1677-cloud-gloss-attribution

Volume 2; displayed source pages: 688, 689.

The dash-delimited وهو السحاب on p688 explains العنان. Neither it nor the corresponding Bengali variant on p689 names the gloss supplier. A lexical gloss role with unresolved attribution is supported.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-16 — p06-v02-p0691-note680-unspecified-prior-claim

Volume 2; displayed source pages: 690, 691.

Footnote680 on p691 explicitly names Albani, Hayyan ibn Ala, and Ghayatul Maram299, but its opening তিনি এরূপই বলেছেন has no recoverable explicit prior claim in h1679 on pp690–691. The uncertainty is appropriately narrow; known criticism and reference are retained.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-17 — p06-v02-p0711-Ruyani-commentary-attribution-end

Volume 2; displayed source pages: 710, 711.

The explanation on p711 follows h1702 and names Ruyani/Al-Bahr, then continues into the contrast about paved/mosaic floors without a quote end or reattribution. This is non-Prophetic commentary with an unresolved named-source endpoint.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-18 — p06-root-v02-p0803-hypothetical-second-quote-scope

Volume 2; displayed source pages: 802, 803.

The Bengali instruction on p803 closes the first hypothetical praise example and opens another single quote before এবং আল্লাহ. Only the outer close is visible at the end. The unmarked inner ending remains unresolved; [জ্ঞানের] is an explanatory insertion.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-19 — p07-v02-p0839-0840-h1819-duration-speaker

Volume 2; displayed source pages: 838, 839, 840.

The Arabic duration uncertainty appears inside the outer quotation on p839; Bengali p840 similarly places আমি জানি না within the translated block. No separate speaker is named for the forty-day/month/year alternatives.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-20 — p07-v02-p0852-h1832-lexical-gloss-speaker

Volume 2; displayed source pages: 852.

The Arabic يريد and dash-marked explanation of العوافي on p852 clearly perform a lexical explanatory function. The source does not name their supplier. The qualification prevents assuming the whole printed quotation is a single pure speech layer.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-21 — p07-v02-p0913-h1876-bengali-quote-end

Volume 2; displayed source pages: 906, 912, 913, 914.

Bengali p913 opens a Prophetic aside and continues through settlement, marriage, and death without a closing mark; p914 continues historical dialogue. Arabic p906 closes its shorter corresponding aside. The source also visibly lacks the name component after ইবনে; neither omission is silently repaired.

**Disposition:** retain the source-limited uncertainty.

### qc-inherited-22 — p07-v02-p0907-h1876-following-comment-speaker

Volume 2; displayed source pages: 906, 907, 912, 913, 915, 916.

Arabic p907 names the Prophet for one observation and then uses unnamed قال for the meat/water comment. Bengali pp915–916 visibly closes the first observation and says বর্ণনাকারী বলেন for the comment. The Bengali presentation is clear; the Arabic speaker is not inserted from it.

**Disposition:** retain the source-limited uncertainty.

### qc-new-01 — p08-v02-p0802-h1798-bilingual-narrator-difference

Volume 2; displayed source pages: 802.

V2p802 visibly names أبي بكرة in Arabic h1798 and আবূ হুরাইরা in its Bengali line. The discrepancy is real; neither form may be silently harmonized.

**Disposition:** retain the source-limited uncertainty.

### qc-new-02 — p08-v01-p0139-h84-inline-gloss-suppliers

Volume 1; displayed source pages: 139.

Both يعني explanations are visible in Arabic h84 on p139. They explain the departure and the addressed satan without naming a gloss supplier. The explanatory roles preserve this limit.

**Disposition:** retain the source-limited uncertainty.

### qc-new-03 — p08-v01-p0149-h91-hypothetical-bequest-inner-boundary

Volume 1; displayed source pages: 149.

The p149 top lines retain a single opening before the hypothetical bequest and only the outer closing quotation. The final অথচ sentence has no separately printed inner endpoint. The inheritance parenthesis is independently explanatory.

**Disposition:** retain the source-limited uncertainty.

### qc-new-04 — p08-v01-p0164-h111-inline-gloss-suppliers

Volume 1; displayed source pages: 164.

The supplication in h111 on p164 includes two dash-marked يعني glosses identifying the demonstratives. The words explain the supplication rather than constituting another named utterance; the supplier is not given.

**Disposition:** retain the source-limited uncertainty.

### qc-new-05 — p08-v01-p0241-h174-simile-warning-subject

Volume 1; displayed source pages: 241.

Arabic p241 puts the warning after the army-warner comparison كأنه منذر جيش يقول; Bengali explicitly says তিনি বলতেন. The cautious Arabic comparison role retains the two source-supported readings rather than equating the language-specific presentation.

**Disposition:** retain the source-limited uncertainty.

### qc-new-06 — p08-v02-p0149-note169-IbnHajar-judgment-subject

Volume 2; displayed source pages: 149.

V2p149 note169 names Yahya ibn al-Hasan, then Musa ibn Yaqub, then uses এর সম্পর্কে / তিনি in Ibn Hajar’s judgment before a corrective contrast mentioning Ashath and Musa. The unexpanded antecedent is rightly preserved.

**Disposition:** retain the source-limited uncertainty.

### qc-new-07 — p08-v01-sufyan-unmarked-return-to-reported-speech

Volume 1; displayed source pages: 31, 32, 33, 34.

V1pp31–32 visibly closes a prior phrase and names Sufyan before the Syria comment, then continues the creation-of-the-door account with no new named speaker boundary. Bengali pp33–34 puts the Sufyan comment in parentheses. The Arabic return-to-report layer is not uniquely delimited.

**Disposition:** retain the source-limited uncertainty.

### qc-new-08 — p08-v01-p1014-h987-bilingual-narrator-difference

Volume 1; displayed source pages: 1014.

The Arabic attribution on p1014 says أبي هريرة; the Bengali attribution says আবূ আব্দুল্লাহ. Both names are clear. The candidate preserves this source discrepancy.

**Disposition:** retain the source-limited uncertainty.

### qc-new-09 — p08-v01-p1016-h990-bilingual-narrator-difference

Volume 1; displayed source pages: 1016.

The Arabic Ibn Amr spelling, including final waw, is visible on p1016; Bengali names Abdullah ibn Umar. No harmonized narrator identity is justified by the edition alone.

**Disposition:** retain the source-limited uncertainty.

### qc-new-10 — p08-v01-p0863-0865-h802-bilingual-narrator-layer

Volume 1; displayed source pages: 863, 864, 865.

Arabic p863 explicitly has Qays reporting from his father, the associate of Abu Darda. Bengali p864 starts incompletely but parenthetically names Bishr; p865 explicitly names Qays at the eyewitness return. The candidate’s language-specific narrator-role wording and retained ambiguity are supported.

**Disposition:** retain the source-limited uncertainty.

## Evidence and handoff

The complete source-bound observations are in `case_observations.jsonl` and `span_observations.jsonl`. `sampling_inventory.json` lists every selected row and group; `reviewed_inputs.json` binds every actually used source/author file and displayed render with its review scope. The finite follow-up queues, adjudications and final corrective recheck are retained for reproduction and audit. This pass is complete for that defined scope.
