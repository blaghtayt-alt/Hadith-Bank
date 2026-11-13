# Final source-apparatus amendment, version 2 — 13 November 2026

The final active ledger preserves the same 38 source occurrences, 36 registered / 2 resolved source-only dispositions, 82 complete nonempty field readings and 74 admitted language fields. It moves exactly 17 numbered Urdu footnote markers and seven explicit verse-reference labels from quotation spans to source context: 24 literal cuts in 18 fields, comprising 178 characters / 329 UTF-8 bytes. No source wording, metadata, report speaker, report family, original language, or parent disposition changes. No additional field receives approval.

Abu Dawud 2118 retains every actual recitation and translated clause, including its Urdu asterisk as a verse separator. Its three Hindi reference labels are separated without removing the surrounding translation parentheses; its three Urdu reference parentheses and Tirmidhi 2096's Urdu verse-reference parenthesis become context. No blanket parenthesis, number, or asterisk removal is performed. There are zero extra whitespace-only cuts and zero whitespace-only selected fragments.

The exact original active gzip (SHA-256 `520e6f17b3608486dd48da21afdf9ac6c6c9a3325b99732d8e23984d7dde0603`), original delivery manifest, and original manual notes are retained as before-evidence. The prior 16-field independent boundary-correction history remains unchanged. `source-apparatus-corrections-v2.json` records every literal range/hash and before/after instruction; `source-apparatus-before-after-v2.json` proves that final quotation positions are exactly the prior positions minus those 24 cuts, with no additional quotation wording. `build_review.py` plus `verify_apparatus.py` compiles these exact decisions and replays the native SourceReviews checks.

Native apply/finish passed for all 38 occurrences. All 188 nonempty field partitions reconstruct exactly, both actual empty fields remain empty, all 106 unread nonempty sibling fields remain context, all 38 raw/parsed pairs were reopened and reparsed against the pinned source checkpoint, and every source metadata preservation check passed. There are now 133 quotation spans; the prior count of 109 in the historical record below predates this final apparatus separation. The original source baseline is unchanged. Shared full-checkout validation, reader build, browser checks, and deployment remain distinct CI gates.

## Preserved original review history

The following is the original package narrative. Version 2's precise source-apparatus boundaries above supersede any earlier inclusion of the enumerated footnote glyphs or reference labels.

# Saved-checkpoint Abu Dawud, Tirmidhi and Ibn Majah review

## Result and scope

This additive package resolves **38 source occurrences saved at `659f21c8a5bbedd3f85aa4c579f4e3b1f215dfc9`**: **36 register** and **2 remain resolved source-only**, with no unresolved decision in the assigned cohort. These are local, source-bound decisions. Their combined repository export, material-registry checks, reader build and deployment remain separate CI gates.

| Collection | Assigned occurrences | Register | Resolved source-only | Complete fields read | Selected language fields | Unread nonempty sibling fields |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Abu Dawud | 14 | 13 | 1 | 33 | 28 | 37 |
| Ibn Majah | 9 | 9 | 0 | 18 | 18 | 27 |
| Tirmidhi | 15 | 14 | 1 | 31 | 28 | 42 |
| Total | 38 | 36 | 2 | 82 | 74 | 106 |

All **38 Hindi and 38 Urdu fields** were individually read in full. In addition, the Arabic and English fields of Abu Dawud2066 were fully read and admitted; the remaining Arabic, English and Roman Urdu fields of Abu Dawud2115 were fully read before exclusion; and the Roman Urdu placeholder of Tirmidhi2089 was read before exclusion. Tirmidhi2089 has actual empty Arabic and English strings, which remain empty.

The82 complete readings contain **34,972 Unicode characters /73,886 UTF-8 bytes**. Of these fields,74 supply selected report wording and8 are fully read source context. The package retains **106 other nonempty sibling fields as unread context**, without implying that resolving their parent reviewed those languages. There are188 nonempty field partitions and two separately preserved empty fields, covering all190 original language slots. The109 selected source spans describe exact boundaries within38 source identities; they do not create109 source occurrences.

## Source binding and validation

The source worker was `43412868540`. The shared saved-evidence manifest is bound by SHA-256 `7ccfc0b69bc848ad22685be6a9ddf3dc89f20cbd4881994d742f1e1d3bbd913c`. It identifies the exact94-entry held checkpoint from which this38-entry cohort is selected. This package separately reopened **38 raw HTML and38 parsed source files**, verified all76 Git blob IDs and stored/decompressed SHA-256 hashes, and reparsed **3,408,374 raw HTML bytes** to reproduce every original source object and printed reference. Parsed JSON totals213,939 bytes. No source HTTP request was made.

`source-baseline.jsonl.gz` preserves the complete assigned source rows. `selected-state-entries.json` preserves their exact saved state entries. `input-evidence-manifest.json` retains the original checkpoint receipt; `source-evidence.json` records this review's own38 reopens/reparses. The active ledger is `../source-review-checkpoint659-abudawud-tirmidhi-ibnmajah-20261113.json.gz`.

Native `SourceReviews.apply()` and `finish()` passed for exactly these38 unique IDs. Every complete source field was reconstructed exactly from the selected quotation spans and retained context; the two source-empty strings were separately checked. Source and canonical input objects were not mutated. Stable occurrence/language-version IDs, exact quotations, source numbering, printed references, source grades, narrator metadata, headings, URLs, snapshot/parsed locators, translation provenance and other immutable metadata remain unchanged. Unsupported canonical identity and grader/translator details remain unknown.

## Independent reading and explicit corrections

The root reviewer independently read all82 nonempty reviewed fields and inspected both empty source fields. The parent dispositions remained36 registration decisions and two source-only exclusions. The independent pass narrowed **16 language fields** to keep explicit lexical/translator explanations as context and to separate the supplied Sulayman age variant from Aisha's primary account. `independent-review-corrections.json` records each exact source hash, original instruction and corrected instruction. The three `manual-*.json` files contain the final explicit readings and boundaries.

The builder processes only those individually written instructions. Its omission lists contain the exact, explicitly reviewed source substrings and expected occurrence counts; there is no keyword, punctuation or sibling-language approval rule. It preserves the surrounding report's component identity across removed context.

For Abu Dawud2121, Aisha's seven/nine-year account and the separately framed six-year Sulayman variant have separate source report families. The source order interleaves the variant with Aisha's account. The existing native engine's family metadata preserves one Aisha family across its ordered before/after components, plus one Sulayman variant family; the lexical zafaf parenthetical remains context. The native validation confirms exactly two report families in each admitted language. No engine change was made.

## Substantive boundary decisions

- **Abu Dawud2115** contains only a named chain and a similar-to-earlier pointer in all five nonempty fields. It is resolved source-only; no preceding report wording is imported.
- **Tirmidhi2089** contains information-not-provided placeholders in Hindi, Urdu and Roman Urdu, with actual empty Arabic and English. It is resolved source-only, preserving all five original states.
- **Abu Dawud2094** supplies actual abbreviated crying/silence variant wording and a later separately transmitted Aisha dialogue. They remain separate attributed components; the intervening addition apparatus and compiler criticism remain context. The abbreviated transmission is not completed from another occurrence.
- **Abu Dawud2112** retains its actual question, answer and instruction; the opening earlier-account comparison and omission note remain context. **2118** retains the explicitly reported khutbat al-hajah teaching, including its quoted recitations and supplied meanings/references, while the final transmission-omission note remains context.
- **Ibn Majah2112** separates the reported Prophetic action from Ibn Abbas's own first-person instruction. **Tirmidhi2069** retains Abu Hurairah's own practice report. **Tirmidhi2070** separates Abu Hurairah's saying from Qatadah's reported practice. These retain their actual speakers and are not relabelled as Prophetic speech or presented as a new medical assessment.
- **Tirmidhi2064** preserves the actually supplied Hindi abridgment without completing it from the longer Urdu field. Its summary marker and the explicitly reviewed Urdu explanatory phrases remain context.
- **Tirmidhi2101** preserves the Abu Bakr/Umar consultation narrative while keeping its lexical and conditional translator explanations outside the selected spans. **2116** retains the actual dialogue, prayer and narrated closing account; its compiler grading and legal deductions remain context.
- **Ibn Majah2082** preserves the actual answer and its supplied attribution while retaining Ibn al-Mubarak's appended criticism separately. **Tirmidhi2095,2102,2106,2132,2133** similarly retain the actual report while keeping compiler route assessments, grades or legal explanations as source context.

Source defects are retained literally. Examples include the broken Hindi honorific/attribution clauses in Abu Dawud2096, Ibn Majah2074 and Tirmidhi2106; the Hindi/Urdu narrator spelling difference in Ibn Majah2119; shorter Hindi wording in Abu Dawud2123 and Tirmidhi2064/2096/2133/2137; differing supplied metadata and in-field grades; and source footnote markers with no supplied footnote body. No missing wording, name, reference or grade was supplied.

## Reproduction and limits

Run `build_review.py --input <verified659f-held-evidence-directory> --engine-dir <checkpoint-scripts-directory> --output <isolated-candidate-repository>`. It checks the fixed source-manifest and importer/review-engine hashes, compiles the explicit notes, reopens/reparses the saved source files and executes the native preservation checks. It writes no generated canonical previews and performs no fetching or upstream mutation.

This is complete-field attribution and boundary review of identified saved source text. The separate independent reading is not a formal independent Pro certification. No new translation, authenticity verdict, rights clearance, whole-queue completion or deployment is asserted.
