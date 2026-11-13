# Website-source queue resolution — 13 November 2026

## Current status — phase18 source-bound review of the next 92 saved occurrences

This update records the completed manual and independent review of the 92 Deen Hindi occurrences first held at source checkpoint `bd4a75695d3c695e98bf8efa5ce07764ac5e2633`. It adds four review ledgers with their exact source baselines, reading notes, independent audits and combined native validation. The reviewed set is fixed by source IDs and saved byte hashes. Its members are separate from the earlier 100-occurrence review and from the later 80 newly held occurrences.

The 92 decisions comprise **87 registrations and five source-only dispositions**. Actual complete reading coverage is **199 nonempty fields: 131,417 characters and 275,705 UTF-8 bytes**. Of those, 174 fields contain admitted report text and 25 were completely read and retained as source context. Another 259 nonempty sibling fields remain unread context; two source fields are empty. These categories account for all 460 language-field slots. A parent registration is not a claim that all of its language fields were read.

| Review group | Source occurrences | Registered | Source-only | Complete fields read | Fields admitted |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bukhari 22 and Ibn Majah 1 | 23 | 23 | 0 | 46 | 46 |
| Muslim 23 | 23 | 22 | 1 | 49 | 44 |
| Nasai 16 and Ibn Majah 7 | 23 | 22 | 1 | 49 | 44 |
| Abu Dawud 8, Tirmidhi 9, Muslim 4 and Ibn Majah 2 | 23 | 20 | 3 | 55 | 40 |
| **Total** | **92** | **87** | **5** | **199** | **174** |

Each admitted language received its own full-field reading. All nonempty language fields of every source-only occurrence were read before that disposition. The five source-only IDs are `deenhindi-muslim:2445`, `deenhindi-nasai:2412`, `deenhindi-abudawud:2423`, `deenhindi-muslim:2464` and `deenhindi-muslim:2466`. Their source words, references and metadata remain available as source context. Their dispositions do not remove source records or replace missing report bodies.

The primary reviews and separate independent readings preserve actual speaker distinctions, supplied finite fragments, meaningful conditions and reported uncertainty. They retain actual recitation and the source's own rendering while separating compiler apparatus, omitted-continuation pointers and explanatory glosses. Damaged source wording and incomplete attribution remain explicitly qualified; no adjacent occurrence, other language or canonical number supplies missing words. Every selected passage is bound to the original field by offsets and hashes, with the complementary source text preserved. These are source-bound classifications and preservation checks, not independent authenticity certification.

### Actual acquisition checkpoint and the separate review projection

The latest acquisition receipt included with this update is bound to **`3e574b9e7e4dd7cf8bc23232249004a18692c61c`**. Its saved Deen progress and exact held-ID comparison are distinct from the manual review decisions staged here.

| Deen measure | Actual saved export at `3e574b9` | Projection after applying these 92 decisions to that same saved source set |
| --- | ---: | ---: |
| Fetched source occurrences | 17,131 | 17,131 |
| Registered occurrences | 16,804 | 16,891 |
| Source-only occurrences | 155 | 160 |
| Held occurrences | 172 | 80 |
| Inventory entries still unfetched | 19,259 | 19,259 |

The acquisition audit compares actual IDs: all 92 older held occurrences remain in that saved 172-entry held set, and the other 80 are new. It also checks consumption of the preceding 100-occurrence review. Thus 80 is an identified remaining cohort, not an assumption from subtracting totals. The complete acquisition/history receipt records the precise state, source and retry preservation scope. It accompanies this publication without changing acquisition state or issuing a new source request.

The right-hand column is a fixed-source projection. Publishing the decisions does not itself prove that the serialized worker has saved a later export with those numbers, that the reader has rebuilt from that later export, or that the live website has deployed it. Those outcomes require their own exact saved-head receipts. Acquisition remains incomplete at the actual checkpoint because 19,259 inventory entries are still unfetched.

### Original Hindi and Urdu field queue remains separate

The original-cohort priority queue remains **6,361 pending fields across 3,379 source occurrences: 3,285 Hindi and 3,076 Urdu**. Its canonical compressed bytes retain SHA-256 `74ce384bca242d5c130ddd1347774ab0c7e94e51185175d62cd8158e09e1a64a`. This update does not overwrite that queue or any of the 33 active review ledgers already published at `f9be12177046e372df088f96b255fd09914fad5a`. The four new ledgers cover only the distinct saved 92-occurrence cohort.

The preceding phase17 extension actually read 50 Hindi/Urdu fields on 25 existing Bukhari parents. Its independent GitHub read-back is now included: the complete active ledger, queue and status-document bodies match the published payload, and the other 32 active review entries plus the acquisition entries retain their before/after Git identities. The read-back checked three complete bodies totaling 1,194,770 bytes through 14 complete rehashed ancestor trees with 961 entries. It does not claim a second linguistic reading or a repeat of the full native review test. The phase17 commit remains `f9be12177046e372df088f96b255fd09914fad5a`, parent `d0a863b0966c7eb1ae1d5c36202de282caf77cab`.

### Reader validation is recorded at its actual head

The completed reader run [43456458994](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43456458994), built from `e3f88ac8a1ee34034c42c1778ff0c85d24b2a40d`, passed **959 Python tests, 43 Node tests, the full export/build checks and all ten Chromium checks**. Its build contained 100,097 records across 250 datasets. The observed log duration was about 34 minutes 46 seconds under the published 45-minute build cap.

That result is bounded to the recorded build. Its publication guard observed the newer `d0a863b` main head, reported the build superseded, and skipped upload and deployment. It is therefore evidence of successful software, export, build and browser validation, not evidence that the present review package or current main was deployed. The complete hash-bound reader receipt is retained at `reports/web-source-resolution-20261113/reader-e3f88-phase15-success-superseded-receipt.json`.

The subsequent completed [run 43462389218](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43462389218), built from `d0a863b0966c7eb1ae1d5c36202de282caf77cab`, also passed its full gates: **978 Python tests, 43 Node tests and 14 browser checks**, with 100,653 records across 251 datasets. Its actual guard then observed `3e574b9`, so upload and deployment were again skipped. This second exact-head result is recorded separately in `reports/web-source-resolution-20261113/reader-d0a863-phase16-success-superseded-receipt.json`. Neither completed build demonstrates deployment of the current phase18 decisions.

### Evidence and preservation boundaries

All four primary packages retain their source-first reading receipts, exact saved source baselines, source references and immutable earlier candidate versions where an amendment was necessary. Their four independent packages record actual separate readings and precise final boundary checks. The combined integration validates the fixed 92-ID source set, all 184 saved raw/parsed files and complete reparses, current published-ledger disjointness, actual field coverage and exact native output. It reconstructs all 458 nonempty field partitions without losing source text and preserves the two empty slots. The native loader accepts all 37 ledgers and 3,410 manual decision IDs; `apply`/`finish` is exercised for these 92 new decisions. The 3,318 prior manual IDs are preserved, not newly read by the integration. It binds the final approved package hashes rather than an earlier provisional candidate.

The publication staging manifest under `reports/web-source-resolution-20261113/phase18-publication-inputs-v1/` retains the exact input package manifests and the phase17 publication, tree and final-manifest receipts. It verifies unique repository paths, exact file hashes and allowed overwrite scope. The current status document is the only previously existing path replaced; four new active ledgers and additive evidence paths are introduced. Prior review ledgers, the canonical priority queue and acquisition files remain outside this update's write set.

The complete previous 82,957-byte status document is archived unchanged with SHA-256 `9746d1eb87ce8f47ae6e35d0781b675544ac8f19017a69e2177d0f8fd16a9708`. Its entire body also follows below as historical material. Historical counters, projections and then-pending checks retain their original temporal scope; they are not substituted for the exact current receipts above.

## Historical material retained from the phase17 document

