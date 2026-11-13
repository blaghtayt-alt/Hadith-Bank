# Deen Hindi: Abu Dawud and Tirmidhi manual source review

## Result

All 636 assigned saved source occurrences have a final decision: 612 register and 24 exclude as source-only. There are no held or unprocessed rows in this assigned cohort. Abu Dawud contributes 282 register and 4 source-only decisions from 286 assigned rows. Tirmidhi contributes 330 register and 20 source-only decisions from 350 assigned rows.

The authoritative assignment was `hindi-resolve/remaining-after-context-guard.jsonl`. It includes the 15 additional context-dependent Abu Dawud and 15 additional Tirmidhi rows. `source-cohort.jsonl` retains the exact assigned saved records and snapshots; `cohort-metadata.json` binds the original and selected cohort bytes.

## Publication candidate

Publish **one** of these equivalent files under `imports/web-deenhindi-20261112/reviews/`:

- `source-review-20261113-abudawud-tirmidhi-manual.json.gz` (recommended, deterministic gzip)
- `source-review-20261113-abudawud-tirmidhi-manual.json` (uncompressed equivalent)

Do not publish both versions: they contain the same 636 IDs and the adapter intentionally rejects duplicate decisions. Both file hashes and sizes are in `handoff-summary.json`. The adapter already supports compressed source-review files.

Supporting audit material can be stored alongside the candidate or in an evidence subdirectory:

- `manual-reading-ledger-20261113-abudawud-tirmidhi.json.gz`: complete individually written field decisions and explicitly superseded draft revisions.
- `handoff-summary.json`: exact book/field coverage, excluded IDs, candidate hashes and sizes.
- `review-coverage.json`: actual reading character/byte counts and adapter validation result.
- `HANDOFF.md`: scope and integration instructions.

The uncompressed review's SHA256 is `664ec77eccdd9130c19717193823f65976f9f25518f1a3643a512f9a01f2197d`.

## Actual reading coverage

819 complete nonempty language fields were manually read, totaling 311,816 source characters and 404,901 UTF-8 bytes. The decisions admit 710 language fields and preserve 109 fully read fields solely as context. Exact selected quotation characters total 248,764.

| Source language | Nonempty source fields | Fully read | Fields with selected quotation content | Unread nonempty fields retained as context |
| --- | ---: | ---: | ---: | ---: |
| English | 605 | 605 | 586 | 0 |
| Hindi | 636 | 131 | 107 | 505 |
| Urdu | 636 | 33 | 9 | 603 |
| Arabic | 605 | 21 | 3 | 584 |
| Roman Urdu | 636 | 29 | 5 | 607 |

Arabic and English each have 31 empty fields. Empty fields were inspected where needed but are not counted as full-text readings. In particular, all 31 English-empty parents were inspected through their real saved language fields. The only source-only outcomes among those English-empty parents are six explicit unavailable-information placeholders.

The remaining 2,299 nonempty sibling fields were not approved and remain complete source context. Parent registration does not imply review or quotation admission of those languages. This is a manual attribution and quotation-boundary review, not independent Pro QC, authenticity verification, source-transcription certification, or a new translation.

## Source-only outcomes

All nonempty language fields of every excluded occurrence were actually read. There are 18 bare-chain/pointer occurrences and 6 explicit unavailable-information placeholders. No report from another occurrence was imported to fill them.

- Abu Dawud bare-chain/source-apparatus rows: **180, 308, 895, 1839**.
- Tirmidhi bare-chain/source-apparatus rows: **166, 196, 226, 280, 285, 343, 403, 441, 535, 612, 615, 654, 872, 1697**.
- Tirmidhi unavailable-information placeholders: **391.2, 455, 457, 458, 1561.2, 1884.2**.

“Exclude” removes these source-only occurrences from quotation registration; all immutable source records, fields, chain notices, grades, commentary and snapshot evidence remain preserved.

## Attribution and boundary decisions

The review selects only content actually present in each independently read field. Compiler grading, transmitter criticism, related-reporter catalogues, lexical commentary, generic legal-school summaries and bare chains remain context. Actual transmitted report fragments can be retained with limited attribution when the source supplies real wording. No missing ultimate speaker is filled from a neighboring report.

Companion, Successor and independently attributed scholarly statements retain their actual types and speakers. They are not promoted to direct Prophet speech. Named actual scholarly quotations are distinguished from generalized compiler summaries. For example, Tirmidhi 867 preserves Ayyub al-Sakhtiyani's transmitted historical statement, while its following biographical identification remains context. Tirmidhi 651's English chain/criticism is source-only; separately read source-language fields contain an explicit named scholars' fifty-dirham statement selected under its own attribution.

Abu Dawud 907's empty English is resolved from its actually read Hindi and Urdu, each with two separate reports. The Hindi/Urdu source differences are preserved. Hindi 543 explicitly attributes a final statement to the Prophet where English does not; that attribution is admitted only in Hindi. Hindi 1526 is visibly damaged, so its source words remain unchanged; independently read Urdu provides its own complete report rather than repairing Hindi. Hindi-labeled Latin-script fields (including Abu Dawud 336/362 and Tirmidhi 1395) are marked with the actual observed script, without changing source words or field labels.

Draft bare-chain admissions were corrected after the parent clarified the no-body rule. `review-revisions.json` and the compressed ledger preserve the superseded draft evidence; the final candidate contains only the corrected decisions.

## Verification and remaining integration work

`build_reviews.py` recompiles only explicit manual decisions. It does not classify text. It binds every source record, snapshot, field and selected span by SHA256 and checks that selected quotations plus source-context spans reconstruct the complete source string exactly.

The actual `SourceReviews` adapter was exercised against all 636 exact saved records in an isolated fixture; `finish()` passed with no unknown IDs, duplicate fields, missing source decisions or span/hash errors. Every excluded occurrence's reviewed-language set was also checked against all its nonempty source-language fields. No source records were mutated and no Deen source requests or upstream repository writes were performed by this review agent.

Parent integration should combine this candidate with the other disjoint review sets and run the current full repository rebuild/validation. This isolated result does not itself claim the combined website was rebuilt or deployed.
