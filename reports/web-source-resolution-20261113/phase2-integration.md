# Deen Hindi phase 2: combined source-review integration

Status: **all six manual cohorts assembled; full-checkout source/export gate pending**. Local adapter replay and preservation checks passed.

This additive candidate covers **2,289 source occurrences**: **2,168 register**, **121 remain source-only exclusions**, and **0 held**. Every occurrence ID is unique across the supplied cohorts.

## Counts by book

| Source book | Parents | Register | Source-only exclusions | Held | Complete fields read | Admitted language fields |
|---|---:|---:|---:|---:|---:|---:|
| abudawud | 304 | 300 | 4 | 0 | 417 | 397 |
| bukhari | 285 | 285 | 0 | 0 | 285 | 285 |
| ibnmajah | 221 | 220 | 1 | 0 | 232 | 227 |
| malik | 89 | 68 | 21 | 0 | 139 | 72 |
| muslim | 505 | 436 | 69 | 0 | 893 | 540 |
| nasai | 529 | 523 | 6 | 0 | 573 | 543 |
| tirmidhi | 356 | 336 | 20 | 0 | 450 | 361 |
| **Total** | **2,289** | **2,168** | **121** | **0** | **2,989** | **2,425** |

## Inputs and review scope

| Cohort | Parents | Register | Source-only exclusions | Held | Source assignment checkpoint |
|---|---:|---:|---:|---:|---|
| abudawud-tirmidhi-636 | 636 | 612 | 24 | 0 | `7b22548d43bccce94cce0e04d734e47458460fac` |
| new-held-agent-46 | 46 | 44 | 2 | 0 | `eb6061e1d4115d141d3f2d723ec83fc57f34b1b2` |
| bukhari-ibnmajah-477 | 477 | 477 | 0 | 0 | `7b22548d43bccce94cce0e04d734e47458460fac` |
| nasai-519 | 519 | 513 | 6 | 0 | `7b22548d43bccce94cce0e04d734e47458460fac` |
| new-held-root-35 | 35 | 35 | 0 | 0 | `eb6061e1d4115d141d3f2d723ec83fc57f34b1b2` |
| muslim-malik-576 | 576 | 487 | 89 | 0 | `7b22548d43bccce94cce0e04d734e47458460fac` |

## Complete held-source coverage and saved-cohort projection

All **3,942 formerly held entries** at `eb6061e1d4115d141d3f2d723ec83fc57f34b1b2` are covered: **2,289 explicit manual decisions** and **1,653 exact prior-review reuse decisions**. The sets are disjoint, and there are no uncovered IDs. The reuse complement contains 1,616 original held entries plus 37 newly acquired held entries.

The current pinned Fawaz catalog, including the phase 1 additional decisions, provides **2,021 exact same-language field approvals** for that complement. Every reused field has byte-identical complete text and positive prior boundary evidence. All **8,046 nonempty fields** across those source occurrences reconstruct exactly; unmatched siblings remain context. Reuse does not claim new manual reading, translation equivalence, matching canonical identities or transferred grades.

| Book | Fetched at checkpoint | Already registered | Newly registered by manual review | Newly registered by exact reuse | Registered after review | Source-only | Held |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| abudawud | 1,838 | 1,218 | 300 | 316 | 1,834 | 4 | 0 |
| bukhari | 1,851 | 1,557 | 285 | 9 | 1,851 | 0 | 0 |
| ibnmajah | 1,832 | 1,439 | 220 | 172 | 1,831 | 1 | 0 |
| malik | 1,716 | 683 | 68 | 944 | 1,695 | 21 | 0 |
| muslim | 1,849 | 1,213 | 436 | 131 | 1,780 | 69 | 0 |
| nasai | 1,842 | 1,298 | 523 | 15 | 1,836 | 6 | 0 |
| tirmidhi | 1,847 | 1,425 | 336 | 66 | 1,827 | 20 | 0 |
| **Total** | **12,775** | **8,833** | **2,168** | **1,653** | **12,654** | **121** | **0** |

**These are verified source-object preflight results, not a completed publication.** The 8,833 already registered entries come from the preserved GitHub progress snapshot; all 3,942 held-source objects were checked individually through manual or exact-reuse decisions. The normal full-checkout rebuild and export must still produce and verify the final derived totals.

No generated reuse ledger was written or included. `phase2-reuse-output-bindings.jsonl.gz` records only source, decision and derived-output checksums plus field-span receipts for the replay. The normal importer creates its own current reuse ledger.

The original source-assignment commits remain attached to their cohorts. The later workflow-only main revision does not replace those source baselines. Where a supplied review document does not itself declare a commit, `phase2-inputs.json` explicitly distinguishes the assignment checkpoint from document metadata; exact source-object and cohort hashes provide the binding.

Across these cohorts, reviewers recorded complete reading of **2,989 nonempty fields**, covering **1,152,657 Unicode characters / 1,433,009 UTF-8 bytes**. The decisions admit **2,425 language fields** containing **2,852 exact source spans**. The other **8,258 nonempty fields** remain source context. Reading one language does not approve another language, establish translation equivalence, or repair differences between source fields.

Every nonempty field of each excluded occurrence received its own reading. Excluded source bodies and metadata remain in the evidence ledger and in source-context output; exclusion does not delete the source occurrence. Bare chains, pointers to another occurrence and provider placeholders are not filled from neighboring reports.

The nine qualified Muslim registrations include the finalized external-evidence package. Its separate assessment records 27 complete own-field readings, nine raw-response hash/reparse checks and seven primary parallels read. This is an additional assessment of the same nine source occurrences, not another nine registrations or another 27 unique admitted fields. Missing Arabic/English bodies, unnamed source narrators and unasserted canonical identities remain unchanged. The assessment explicitly does not claim independent Pro QC.

## Verification performed

- Verified **80 input file receipts**, including **41 independently supplied file checksums**. Files without a supplied checksum have exact copy receipts clearly labeled as such.
- Replayed all decisions together through the current `SourceReviews.apply()` implementation and completed `SourceReviews.finish()` with exact equality between loaded decisions and processed source IDs.
- Verified **2,289 source-object hashes**, exact snapshot metadata bindings and **2,289 reconstructed original parsed-object hashes** against their content-addressed parsed paths.
- Verified **11,247 complete nonempty language fields**: ordered selected spans and retained context reconstruct every original character exactly, with no overlap, omission or added wording.
- Confirmed that input objects were not mutated. Source-local IDs and numbers, printed references, narrator fields, literal grades, headings, translation provenance, snapshot locators and other unchanged metadata remain exact. Canonical numbering remains unasserted.
- Confirmed that admitted fields were individually marked fully read, unread fields retain their complete source context, and every excluded occurrence has all nonempty source fields read.
- Confirmed that no decision claims independent Pro QC or certified release eligibility. No new translation was created.

## Local limits and required full-checkout gate

**This local pass does not reopen the original raw HTML responses or parsed gzip files.** It verifies supplied exact source objects, receipt metadata, reconstructed parsed JSON and complete field partitions. The raw-source check counts for this pass are zero. Those bytes remain in the existing repository and must be checked in a complete checkout.

Before derived data is published, the serialized full-checkout importer must load the new additive reviews alongside existing reviews, reopen and verify the saved source files, rebuild the derived records and export them through the normal repository gates. This local subset replay cannot establish that the complete current repository has no unrelated review conflicts.

The included validator supports `--verify-raw` in a full checkout. It verifies both stored and decompressed response hashes/lengths and exact decompressed parsed-source bytes. It still does not replace the complete importer/export gate.

```bash
python reports/web-source-resolution-20261113/validate-phase2.py --verify-raw
```

For the isolated local candidate, the recorded replay used:

```bash
python phase2-integration/repo/reports/web-source-resolution-20261113/validate-phase2.py --engine-dir hindi-resolve/work/scripts
```

## Engine receipts

| Unchanged engine file | SHA-256 |
|---|---|
| `import_deenhindi.py` | `c2b6df1d243b7e9c695358d9f06221c4cba45e880a1a215e4ef697008ed144d0` |
| `web_commentary_quotes.py` | `d90b6152fe421cf8b63ca5725c7a6deb85e07998f67b2b81cf204af553f81f73` |
| `web_source_reviews.py` | `1411cbcb4ca2bdcbe4db7df9828c69c9ff482b0a011fea43ffd72b292e0c7c15` |

## Publication package

The review portion contains additive decision ledgers, original-source baselines, reading evidence and integration reports. Explicitly supplied implementation repairs are listed below. Generated canonical previews and local authoring scratch files are excluded. The integration agent did not edit the shared import engine. All source HTTP request counts for this integration are zero.

`phase2-publication-manifest.json` lists every package file other than itself. The standalone handoff manifest outside the repository candidate also includes the repository manifest file, avoiding a circular self-hash. Publication must preserve all relative paths and bytes, especially document-bound baseline and evidence paths.

`phase2-validation.json` supplies machine-readable counts and gate results. `phase2-source-bindings.jsonl.gz` supplies one receipt per source occurrence. `phase2-inputs.json` records all exact-copy receipts, cohort boundaries and assignment provenance.

## Supplied implementation repairs

These explicitly handed-off code and configuration files accompany the additive source reviews. Their original test receipts are retained; the integration assembly does not claim to have independently rerun the originating suites.

| Repair | Supplied test result | Evidence |
|---|---|---|
| workflow fixture repair | 13 passed | `reports/web-source-resolution-20261113/workflow-fixture-repair-handoff.json` |
| single reviewed retry pilot checkpoint | 71 passed | `reports/hindi-pilot-checkpoint-20261113.json` |
| immutable reuse evidence paths with combined pilot importer | 74 passed | `reports/web-source-resolution-20261113/reuse-source-path-repair-validation.json` |

The pilot authorization remains restricted to the reviewed Bukhari 686 entry. Its checkpoint setting ends that batch after the reviewed retry; ordinary continuation and any wider retry authorization remain separately controlled. The source verification and access-stop guards remain in force.
