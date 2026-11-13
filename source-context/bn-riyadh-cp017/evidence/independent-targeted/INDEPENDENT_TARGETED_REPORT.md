# Independent targeted review — Bengali Riyadh private reader

Review status: **partial; not a whole-book pass and not release clearance.** Reviewer is a separate collaborator from the reader author. This report records only the original page images actually displayed during this run. Images were freshly rendered locally at 2x from the supplied original PDFs, without OCR. Scope is limited to the named spans and their immediate visible contexts; no complete page or character-by-character page QC is claimed.

## Bound artifacts

- Original V1 PDF SHA-256: be5be91ae127c276209722e4a1365cde783ffff3aad04c60d510154a72e31e22.
- Original V2 PDF SHA-256: 194ba1091bbe7e63c564462b290821818ecf419aec6937286bb2bea1992032f5.
- v3 reader SHA-256: 27823d777cf9c349ab360f4702a58d77471ded388671337d075b1ce907697c5d.
- v4 reader SHA-256: 171305eacf5defeee5c332f6b83facbd851ec06e9bf2b17a21a894983cd9b054.
- v5 reader SHA-256: ef16da3ca91acd642cab6dba2f815d9ca4cf9ad461bed8963ebb543b574fa3c7.
- v6 reader SHA-256: fe74185ab53a120593c5d470f1a3870eae89dc32d4ae66c691fd40442020fb10.

Fresh render PNGs and their SHA-256 hashes are in this review directory; exact changes and references are retained by ledger SHA-256 plus one-based row ordinal in the v2 DISPLAY_MAPPING_CHANGES.json, v4 CHANGE_VALIDATION.json, and this directory's V3_V4_COMPARISON.json and INDEPENDENT_DATA_COMPARISON.json. Original page images, not the unreliable PDF text layer, were viewed.

## Visual findings and actual coverage

Twelve page images were displayed, but only localized passages were examined. V1 pages 130, 132, 136, 138, 139, 165, 174, 945, 946 and 962; V2 pages 524 and 525. This count adds no complete-page character-review credit.

- V1 p130 CP152460–152468, p132 CP153741–153803, p136 CP159590–159600, p138 CP161669–161679, p139 CP162632–162724, p174 CP202407–202511, p945 CP1057756–1057860 and CP1058503–1058581: the visible Bengali uses অর্থাৎ or যার অর্থ to introduce source-supplied meanings of preceding supplications. In p132, the wording clearly renders the preceding Arabic prayer; in p139 the meaning includes explanatory phrasing; p174 visibly leaves the opening parenthesis unclosed before the printed citation. The earlier broad display label ‘explanation or commentary’ can mislead when a passage supplies a translation. v6's neutral ‘source-supplied meaning or translation’ is supported as a display label for these exact eight atoms. It does not resolve speaker boundaries, authenticate the text, or assert translator authorship beyond the retained original roles.
- V1 p165 CP191062–191063 is a single space labeled translator_supplemental_narrative. The page was viewed, but this one whitespace position could not be independently located visually; the v6 pending-context group is conservative. No independent exact-position visual pass is claimed.
- V1 p946 CP1059113–1059129 and CP1059141–1059166: the printed Bengali meaning follows the transliterated prayer and includes a separate parenthetical insertion between these fragments. Pending source context is conservative. These two fragments must not be silently combined into an unqualified quotation.
- V1 p962: the whole page image was viewed at 2x; this inspection does not establish the exact internal diacritics or full Unicode expansion of the U+F079 glyph. The existing source-limited uncertainty remains open. This is not an independent resolution of CP1076183–1076184.
- V2 pp524–525: five exact author_hypothetical_illustrative_dialogue_not_prophetic_report atoms, CP479003–479045, CP479201–479266, CP479425–479538, CP479567–479653 and CP479754–479820, appear as hypothetical example statements/questions embedded in numbered explanatory discussion. The final example crosses the p524/p525 boundary. Moving these five from source report passage to pending source context in v4 is supported; no source text, underlying roles, or ledger decisions were altered. This does not adjudicate other flagged contextual roles.

## Independent mechanical comparison

V3_V4_COMPARISON.json independently checks all 55,499 atoms and shows exactly five display-group changes, with original roles, text, metadata and qualified references unchanged. INDEPENDENT_DATA_COMPARISON.json confirms v4 and v5 embedded data are byte-identical and v5 to v6 changes exactly the eight display-group fields above; every other embedded atom field and all occurrence, story and uncertainty data compare equal. The v5/v6 reader is a distinct artifact and still needs independent reader interaction and integrated-bank testing.

Independently calculated from v6 embedded data: 41,079 atoms are linked to occurrence entries and 14,420 are not; six of 32 semantic uncertainty IDs are absent from occurrence-linked atoms; 37 unlinked atoms carry the provisional source-report group. These counts describe occurrence backlinks, not missing source bytes or unique hadith. V5/v6 add an explorer according to the author's report, but this reviewer has not independently exercised it. None of the 37 candidates is approved for inclusion by this finding.

## Outstanding work

The earlier independent patch character review covered 13 complete pages and 14 localized targets, and semantic QC covered 1,089 rows across 97 pages; these are historical scopes, not this review's new page credit. A genuine independent review of remaining source pages and final integrated artifacts, Arabic/Bengali wording and diacritics, semantic boundaries and roles, and all corrected versions remains open. The display-category lexical survey still requires substantive review beyond these exact cases; source-only material and the 37 unlinked report candidates need explicit eligibility and boundary decisions. No claim of complete authentication, grading, canonical number reconciliation or independent final QC is made.

Preserve the V1 p962 glyph, 32 semantic uncertainties, 85 private-use occurrences including 83 unknown-meaning occurrences, source edition and raw wording, and all hash-qualified ledger references. The bank-specific structured reader and actual deployment have not been reviewed here. No repository write, upload, publication, OCR restart, or source modification was performed by this reviewer.
