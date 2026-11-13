# Muslim and Malik held-cohort disposition

The 576 source-local Deen entries in the pinned cohort now have explicit semantic dispositions: **487 registered source reports and 89 reviewed source-only exclusions or source gaps; zero awaiting a record disposition**. Muslim contributes 419 registrations and 68 exclusions; Malik contributes 68 registrations and 21 exclusions. A source-only exclusion remains an intact provider record and is not a deleted or invented narration.

## Scope and reading coverage

The cohort combines the initially assigned Muslim 431 and Malik 89 entries with the additional 56 Muslim entries left held after the source-reference dependency guard was strengthened. All 513 nonempty English fields were read completely. All 63 entries with empty English and Arabic were read in Hindi, Urdu and Roman Urdu. The 75 English fields that did not independently support registration then received complete Arabic, Hindi, Urdu and Roman Urdu readings. This is manual semantic reading with exact source-span selection; no pattern or number-based batch approval is used.

| Coverage | Count |
|---|---:|
| Provider records | 576 |
| Source field slots | 2,880 |
| Empty source fields inventoried | 126 |
| Nonempty source fields | 2,754 |
| Complete nonempty fields actually read | 1,002 |
| Selected language fields | 588 |
| Read fields retained as context | 414 |
| Unreviewed sibling fields retained as context | 1,752 |
| Unicode codepoints read | 334,977 |
| UTF-8 bytes read | 423,610 |

Every one of the 89 excluded entries has all of its nonempty fields read and its empty fields inventoried. The 1,752 unread sibling fields are retained intact as source context and are not admitted narration text. Record-level completion does not claim complete review of every language version. `field-coverage.json.gz` gives the exact status, full-text hash, length and read coverage for each of the 2,880 field slots.

## Semantic decisions

Actual Companion reports, historical events and specifically transmitted early-authority sayings retain their actual speakers and types. They are not recast as Prophetic quotations. Where a source supplies a genuine abbreviated report body but leaves its ultimate speaker or actor unnamed, the attribution explicitly says so. Bare chains, pointers, isolated temporal or lexical fragments and words expressly omitted by a transmission remain source-only. Compiler legal explanations remain context even where an actual report can be extracted from the same field.

Secondary-language readings recovered reports absent from English. Examples include the long Paradise-rank account in Muslim 465, the Urdu/Roman prayer report in Muslim 1375, the night-time invitation report in Muslim 1777, and two separately attributed reports preceding the legal discussion in Malik 1397. Where the shared provider fields visibly carry different narrator identities, added report bodies or shortened wording, the reviewed fields carry an explicit content-mismatch annotation. No missing language, chain, name, connective, count or report body is filled from another field.

Nine Deen Muslim entries, 76–82 and84–85, omit a source-local speaker and narrator. Their 27 complete Hindi/Urdu/Roman fields were separately read by the cohort reviewer, the root reviewer and an independent queue reviewer. The root and queue reviewer also checked the exact saved HTML and seven external primary parallels. These nine are registered with qualified external-corroboration types and visible evidence notes, while retaining null local narrator, local numbering, original grade and missing Arabic/English. Muslim 79/80 remain fragments containing only the first of three announced conditions. Muslim 85 preserves its actual variant ordering and wording; it is not assigned an exact canonical witness or completed from another version. The durable `nine-corroboration-evidence` sibling directory contains the named evidence and independent assessment.

## Reproducible source binding and validation

`source-baseline.jsonl.gz` contains all 576 original parsed source objects and snapshot receipts. Its stored checksum is bound in the active review document. Each decision also binds its original source object and HTML snapshot; every reviewed field binds its exact UTF-8 hash and complete character/byte coverage. Every selected passage has literal codepoint offsets, a selected-text checksum, an actual report type and a speaker description. Context is the exact complement of the selected passages.

The native `SourceReviews` engine successfully applied all 576 decisions and completed its missing-ID and evidence checks. An additional 6,786 invariants checked unchanged IDs, local numbers, narrators, grades, references, source locators and provenance, and reconstructed every original nonempty field from its selected passages and retained context. The input cohort bytes remained unchanged. No upstream repository writes were performed by this reviewer.

`manual-review-specifications.json.gz` preserves the initial per-ID reading decisions, all secondary-language decisions, the Roman reading inventory and the qualified external plan. `disposition-ledger.json.gz` records the final disposition and specific reason for every ID. `validation-and-coverage-summary.json` records exact totals and the review-engine digest. These mechanical checks do not assert independent Pro certification, authenticity grading or translation certification.
