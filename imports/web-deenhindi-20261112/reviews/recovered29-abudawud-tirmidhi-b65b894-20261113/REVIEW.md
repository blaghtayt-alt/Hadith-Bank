# Recovered Abu Dawud and Tirmidhi source review

## Result and source binding

This additive manual review resolves **29 recovered source occurrences**: **18 Abu Dawud and 11 Tirmidhi**, all registered with independently read Hindi and English fields. There are no source-only or unresolved decisions in this assigned cohort. These are local validated decisions; shared export, material-registry validation, reader build and deployment are separate CI gates.

The source checkpoint is `b65b894adfc1fcd80ff2ebbcedba60970e4f163f`. The recovered held-evidence artifact is `14029806818`, with 2,440,509 archive bytes and SHA-256 `c22e3d12b7f242ccebd2e272ed202993479d2d4d05bcbdfe672ebbdae6caeff6`. The parent independently verified that archive. This review separately reopened and verified the extracted raw and parsed files for every assigned occurrence and reparsed the saved HTML with the checkpoint's importer. No source HTTP request was made.

The active ledger is `../source-review-recovered29-abudawud-tirmidhi-b65b894-20261113.json.gz`. Its immutable source baseline, exact manual notes, source receipts, field partitions and validation report are in this directory. These paths are additive and contain no generated canonical material previews.

## Reading coverage

| Collection | Source occurrences | Registered | Complete Hindi fields read/admitted | Complete English fields read/admitted | Other nonempty fields retained unread | Exact field partitions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Abu Dawud | 18 | 18 | 18 | 18 | 54 | 90 |
| Tirmidhi | 11 | 11 | 11 | 11 | 33 | 55 |
| Total | 29 | 29 | 29 | 29 | 87 | 145 |

The 58 complete fields read contain 24,641 Unicode characters / 44,393 UTF-8 bytes. The ledger selects 61 exact quotation spans. The three additional spans describe explicit internal boundaries; they do not create new source occurrence IDs. Arabic, Urdu and Roman Urdu fields were not semantically read or approved in this review and remain complete source context.

The individually written `manual-001.json`, `manual-002.json` and `manual-003.json` files record each field's actual reading, attribution, scope and boundaries. There is no cross-language or cross-occurrence approval rule. The builder only compiles these supplied decisions and checks their evidence.

## Boundary decisions

- Abu Dawud 2009 retains Abu Rafi's report about the pitched tent and the separately transmitted description of his luggage-guard role, with their actual attribution. Uthman's appended location wording and its explanatory treatment remain context.
- Abu Dawud 2010 retains the encampment account and the reported pact. Zuhri's final lexical explanation of *khaif* remains context in both reviewed languages.
- Abu Dawud 2030 retains the question, answer and instruction about the horns. The appended English identification of Ibn as-Sarh's maternal uncle is transmitter apparatus. Hindi does not contain that appended sentence and is reviewed on its own wording.
- Abu Dawud 2056 retains the dialogue and its supplied name alternatives. The inline English report of Zuhair's uncertainty is context. The two selected English spans remain one report component across that intervening note.
- Abu Dawud 2061 is retained as a composite attributed report: the Salim/Sahlah account, Aisha's later practice, and the other wives' reported response keep their own speaker relationships. The companion positions are not recast as Prophetic speech.
- Tirmidhi 1990, 1996, 2038, 2042, 2045 and 2052 preserve their appended grades, parallel-reporter catalogues or explanatory glosses as source context where present. The English Hasan and Hindi Hasan Sahih in 1990 are left as supplied. The poison explanation in 2045 is not folded into the selected report wording.

All other reviewed fields are admitted in full because their own complete text contains an attributed account without a separate appended compiler block. Parenthetical wording supplied as part of the translation remains exact. Incomplete punctuation, source spellings, differing transliterations, units, omissions and the incomplete Hindi closing in Abu Dawud 2057 are preserved without correction or supplementation.

## Validation performed

`validation.json` records a successful native `SourceReviews.apply()` / `finish()` replay covering exactly these 29 IDs. It verifies unique source/decision IDs, all 58 field hashes and full-reading lengths, all selected span hashes, and all 145 exact quotation/context partitions. The source objects and canonical inputs were not mutated. Occurrence and language-version identities, source numbering and references, literal grades, narrator metadata, headings, URLs, snapshot locators, provenance and other immutable metadata remain unchanged. Canonical identity remains unassessed.

`source-evidence.json` records successful reopening of 29 raw HTML snapshots and 29 parsed snapshots, including compressed and uncompressed hashes, 2,607,286 raw HTML bytes and 164,773 parsed JSON bytes. The current parser reproduced each exact source object and printed reference. The frozen source baseline contains the corresponding complete saved rows. `field-partitions.json.gz` records every complete source field's hash, span coordinates and quotation/context role.

To reproduce the local compilation and validation, run this directory's `build_review.py` with `--input` pointing to the verified recovered held-artifact extraction, `--engine-dir` pointing to the checkpoint's `scripts` directory, and `--output` pointing to an isolated candidate repository directory. It performs no fetching and does not edit the importer or shared review engine.

This is attribution and boundary review of saved source text. It creates no translation, supplies no missing wording, makes no independent authenticity or transcription certification, and does not claim that the resulting candidate has been deployed.
