# Hadith Bank — Delivery acceptance report

**Provisional status: Integrated; publication and live verification pending.**

All six searchable-bank improvements are implemented and passed candidate acceptance in [Actions run 43602603900](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43602603900). [PR #16](https://github.com/blaghtayt-alt/Hadith-Bank/pull/16) was merged on 14 November 2026 at 14:40:59 UTC as [90a24f97f086494000e921e7bec4c8cce14e57ea](https://github.com/blaghtayt-alt/Hadith-Bank/commit/90a24f97f086494000e921e7bec4c8cce14e57ea). The integrated-main delivery is tracked separately in [run 43608019736](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43608019736).

**Every corpus, size and performance figure below describes the accepted PR candidate, not an already published main build.** Fresh main reports, successful deployment and independent live observations must complete the reserved sections before this document becomes a final delivery claim.

## Revision and integration evidence

The accepted feature head is `5ef914fae31d94a5f9acc06884a47dbad78c3789`. Actions actually tested the synthetic merge `ff5a1c6996ee82253cf5c4c34f4eea93e5177a37`; its complete source snapshot is the basis of the candidate evidence. The final main merge has parents `4d466c80bc78d21b4c8b596677c0ec78f5c61b24` and that feature head. It therefore incorporates a newer main source revision than the tested candidate.

The recorded integration comparison identifies exactly 27 changed presentation, search, build, test and evidence paths relative to the main parent. `outside_owned_scope` is empty, and `source_registry_release_paths_changed_by_merge` is false. This establishes the feature merge's scoped changes while retaining concurrent importer work. It does not turn an older candidate's corpus totals into current published totals. The underlying record is `.work/searchable-bank-integration-proof.json`.

At 15:04 UTC, main `9ea5cbae4a6704a0c98254adcd3bb7a4318148f1` is a direct child of the UI merge. Its complete Git diff contains 528 importer-scoped paths (478 additions, 50 modifications), no deletions and no overlap with the 27 owned paths. The authorized importer completed successfully. GitHub replaced the earlier pending 90a run 43606134903 with current-source run 43608019736 through the existing queue policy; this session canceled no jobs. The scope record is `main-9ea5-scope-check.json.gz`.

## Six-requirement acceptance map

Commit links identify exact implementation or corrective changes. Tests in this table passed for candidate run 43602603900. The live-status column remains pending for the integrated publication; limitations are recorded separately.

| Feature | Commits | Tests | Live status | Limitations |
|---|---|---|---|---|
| **1. Evidence-bound narration families** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [9bb4de57](https://github.com/blaghtayt-alt/Hadith-Bank/commit/9bb4de57e44ffc82ebc3bb1d41213ecbe09e1989), [7fde4516](https://github.com/blaghtayt-alt/Hadith-Bank/commit/7fde4516c6fce0707177644e81885ddfdcfc8bff) | Accepted mappings and exact source/provider bindings authorize presentation grouping. Tests reject number collisions, changed quotation evidence and duplicate complete identities, while preserving distinct editions sharing a short ID. Corpus validation reconstructs every family; Chromium opens versions and evidence. | Pending deployed-revision grouping/workspace checks. | Qualifications and uncertain identities remain separate. This is not a unique-hadith or new scholarly identity audit. |
| **2. Compact ranked index and lazy delivery** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [594a84d8](https://github.com/blaghtayt-alt/Hadith-Bank/commit/594a84d84dd8d5de82c514d37645031a2afe787c), [694aaa66](https://github.com/blaghtayt-alt/Hadith-Bank/commit/694aaa667e7a7521fa36ef200da286864c7f821a), [98cd9e83](https://github.com/blaghtayt-alt/Hadith-Bank/commit/98cd9e835a24039f2eb7cd9f3bcebd193800f4f9) | Query postings, visible previews and selected full details load separately. Cache, cancellation, corruption, source binding, offline failure/retry and exact staging-copy regressions pass. Both benchmark targets complete every cold/warm query. | Pending live timing/bytes and error-state review. | Core startup has a transfer cost; commentary/context search remains explicitly slower. Unrequested hosted details are not automatically available offline. |
| **3. Reference, wording and topic journeys** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [527c9277](https://github.com/blaghtayt-alt/Hadith-Bank/commit/527c927745b1f462b985cf606fa81a9abb83a28a), [926c024b](https://github.com/blaghtayt-alt/Hadith-Bank/commit/926c024b47da0baf11da61a29053e513ebdac61a) | Tests cover canonical/local/provider numbering, strict phrases, Arabic and multilingual normalization, late quotation matches, no results, suggestions and negation-preserving broader wording. Actual browser journeys pass. | Pending representative public searches on the expected revision. | Broader results disclose missing terms; synonyms/transliteration are bounded editorial retrieval aids, not source taxonomy, semantic-equivalence guarantees or religious rulings. |
| **4. Preferred-language results and source workspace** | [527c9277](https://github.com/blaghtayt-alt/Hadith-Bank/commit/527c927745b1f462b985cf606fa81a9abb83a28a), [926c024b](https://github.com/blaghtayt-alt/Hadith-Bank/commit/926c024b47da0baf11da61a29053e513ebdac61a), [4277317c](https://github.com/blaghtayt-alt/Hadith-Bank/commit/4277317cee8255047d7ceb900ad93a12c03cc769) | Preferred previews and actual matching passages retain separate source/language attribution. Tests preserve explicit versions, stored/link/pending/missing states, qualified links, exports and history. Chromium passes page-return/selection, keyboard, RTL and recovery checks. | Pending public workspace, navigation and source-link checks. | Missing translations are not generated; exact passages can require one selective detail request. Accessibility-tree checks are not human screenreader testing. |
| **5. Evidence-backed navigation and facets** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [527c9277](https://github.com/blaghtayt-alt/Hadith-Bank/commit/527c927745b1f462b985cf606fa81a9abb83a28a), [41f00591](https://github.com/blaghtayt-alt/Hadith-Bank/commit/41f00591f215c907e3734b49410bd4a5962bc660) | Source heading hierarchy, category, narrator, report type and named-authority grade checks pass, including combined facets and browsing after clearing Reference mode. Validators reject invented metadata. | Pending representative published navigation review. | Coverage follows supplied evidence; unknown remains unknown. Generic source types do not automatically become Prophetic reports, and displayed grades remain attributed assessments. |
| **6. Friendly, distinct edition identities** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [926c024b](https://github.com/blaghtayt-alt/Hadith-Bank/commit/926c024b47da0baf11da61a29053e513ebdac61a), [b81baa3a](https://github.com/blaghtayt-alt/Hadith-Bank/commit/b81baa3a7aa827a5266c976b7373aa5ca83b9cef) | Tests require accepted source/partition evidence before grouping technical chunks, retain genuine volumes, reject stale manifests and distinguish unrelated equal captions. Browser checks preserve qualified identities. | Pending published caption/provenance examples. | Titles alone never prove equivalence; “Source edition N” disambiguates presentation and does not invent a publisher edition. |

Candidate software gates passed **1,063 Python tests, 48 lazy-store Node tests and 22 search-engine Node tests**, with no failures or skipped Node tests.

The focused regressions are in `tests/test_bank_discovery.py`, `tests/test_discovery_engine.js`, `tests/test_discovery_binding.py`, `tests/test_lazy_store.js`, `tests/test_language_readings.py`, `tests/test_reader_grouping.py` and `tests/test_refresh_reader_reuse.py`. Actual browser evidence records 15 reader check groups, 18 discovery-fixture groups and two production-corpus groups, all passed. Production-corpus here means the staged site served inside Actions, not public Pages.

## Observed candidate mobile and accessibility limitations

The 390px-wide actual-corpus PNGs from candidate run 43602603900 were visually reviewed. These observations describe the staged candidate, not public Pages.

- **Vertical explanatory space:** The home hero is collapsed during discovery, but explanatory text, availability information and disclosures still occupy substantial vertical space. The first reference card begins around document y819 and the broader-wording card around y1076. Full-page PNGs do not record `scrollY`, so these are not exact viewport-position claims.
- **Long source captions:** Source metadata wraps within mobile cards. The closed native source-version selector truncates long selected captions; fuller source context remains in the workspace panels and provenance.
- **Initial preview versus matching passage:** A short preferred-language preview can precede the meaningful hit; a visible normalized query token does not establish that the whole searched phrase appears there. “Show matching wording” retrieves an exact passage from its own identified source reading. The supplied production PNGs show this control but do not show it expanded, so exact passage binding is supported by the automated tests rather than visually demonstrated in these captures.
- **Automated accessibility scope:** Chromium checks cover keyboard navigation, focus, RTL, horizontal overflow, DOM/ARIA and the accessibility tree. They do not constitute a human screenreader session with NVDA, JAWS or VoiceOver, or comprehensive accessibility conformance.

## Candidate source preservation and exclusions

Fresh portable validation completed at **2026-11-14 14:32:03 UTC**. It compared **109,406 complete public projection objects and 109,406 complete reader objects**, checked the same number of canonical-record digests, compared **84,303,437 Arabic/translation codepoints**, hashed **54,919 source/legacy files** and **1,273 ordered source shards**, and verified **1,502 reader data shards**. There were zero validation failures. The snapshot contains **252 datasets in 11 languages**.

| Candidate fingerprint | SHA-256 |
|---|---|
| Ordered source and reader-detail stream | `0d3fb7b7645ccefc4c60623814fe612ba6f6cf6957dc1559c8103d0d97dc4b6d` |
| Ordered occurrence IDs | `38edd4552085fc8409c23b8b863dfea1eaadd586429cf0b72d624deaa75d0f91` |
| Exact accepted quotation fields | `251a818a8e69dfc8cefe8e4be8e2063f5111e8e6337285fcb3be20f8c7ba31db` |
| Reader HTML, 1,805,106 bytes | `408afa16b07377a8b6d47cf21a7ab3133c441b9b7861d35b665e9c86eb076811` |

Public-scope checks preserve allowed datasets, source review/rights statuses and exclusions of unregistered attachments or extra text. **238 Fawaz source entries remain preserved outside narration search**. Their separate audit reconciles 171 source gaps and 67 commentary exclusions, with zero unresolved held dispositions. Counterpart preparation is candidates-only and accepts zero new alignments.

The candidate's **2,475 evidence families contain 8,555 source occurrences**, producing **103,326 presentation results** including singletons. These are presentation and source-occurrence counts, not independently authenticated unique narrations. The reports' edition count of 252 is dataset-level; they do not expose a distinct friendly-edition-group total.

Compared with the previous f07 candidate, all **365 additional occurrences** belong to five DeenHindi datasets in a newer importer snapshot. Source fingerprints therefore legitimately differ. Portable `source_files_modified:false` means no change during validation; `baseline_git.performed:false` does not itself establish historical cross-commit equality. Full-object fidelity does not certify original transcription, translation quality, religious authenticity or rights.

## Candidate performance, including startup

The [successful candidate benchmark](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43602603900) used Chromium 151.0.7922.34 at 1366×900. Each query began in a new browser context; its warm repeat followed only a completed cold search. Across both targets, all 16 query measurements and eight startups completed, with no pending/failed requests or page errors. Transfer figures are completed CDP encoded bytes, not decoded file size. Cold totals include startup, search, decoding and rendering. MB in the table means 1,000,000 bytes.

| Query | Cold journey, baseline → candidate | Cold bytes, baseline → candidate | Warm search, baseline → candidate |
|---|---:|---:|---:|
| Bukhari 1 | 2.733 → 2.197 s | 9.46 → 10.27 MB | 584 → 89 ms |
| actions depend on intentions | 11.487 → 2.300 s | 81.17 → 12.02 MB | 9,161 → 91 ms |
| anger | 12.224 → 2.356 s | 86.34 → 13.73 MB | 9,326 → 99 ms |
| controlling anger | 11.900 → 2.327 s | 79.66 → 14.07 MB | 8,995 → 79 ms |

**Startup is a real tradeoff.** Baseline startup transferred **3,327,964 bytes**; the candidate transferred **9,804,277 bytes**. Startup time was approximately 1.99–2.04 seconds versus 2.04–2.08 seconds on this local host. Consequently, the candidate's complete cold Bukhari journey transferred **8.54% more bytes**, despite taking 19.6% less time. The three wording/topic journeys transferred 82.34–85.19% fewer total cold bytes and took approximately 80% less time. All candidate warm repeats transferred zero additional bytes.

These are **one sample per query and warmth**, not percentile or statistical latency estimates. Both snapshots were served locally without CPU/network throttling. Baseline source `a9b041be744c59932ccd79c2f92df23c78978923` contains 107,693 occurrences; the candidate contains 109,406. This is an observed end-to-end comparison with different source snapshots and retrieval semantics, not an isolated same-corpus experiment or a public mobile-network measurement.

Bukhari 1 preserves 26 matching occurrences as 15 results. Remembered wording returns 12 explicitly broader results, not an exact-phrase success claim. Topic expansion changes anger/controlling-anger results deliberately; larger counts are not accuracy scores. Measured candidate searches load query index/preview parts without scanning full source-text, directory, detail or commentary stores. Optional commentary search retains its separately labelled slower path.

## Candidate packaging and publication limits

The core index is **7,998,782 compressed bytes**, expanding to **79,935,103 bytes**. There are 161 posting parts and 428 preview parts; the entire index inventory totals **100,440,209 compressed bytes**. Browsing does not download that complete inventory at startup.

The recorded site counter is **942,693,162 bytes**, below the unchanged **950,000,000-byte** gate, while retaining 38,782 stable narration pages. This counter precedes final build-info/marker writes. Adding those known metadata writes gives a **derived**, not independently inventoried, staged total of **943,532,061 bytes**, leaving 6,467,939 bytes. Continuing imports can change the integrated build's size; its fresh gate remains mandatory.

Candidate acceptance archive: **7,019,061 bytes**, SHA-256 `2d3a811a692b3c969c04251e468bebabc75fc4a54fa8a7e2977fd2a1b38d0cf5`. Portable report SHA-256: `80582a337e2df3681ee6b6a9bfb8ecf873684e559042737971c67c0129778f9e`; site report: `56478e2ada1205413f26439ffecb3d26321223156f694e570d1a2bef17d7427a`. Benchmark summary comes from `.work/ci-run43602603900/benchmark-summary.json`; its raw report SHA-256 is `9d281e30723a227cbe1c18f3ea78a761d9fadef24496024a0146a6003897b39c`. Failed-run checked-in reports are not substituted for these fresh records.

## Current delivery checkpoint

The preceding pre-feature run 43605440177 ended at 15:18:21 UTC after its existing 45-minute build limit. Generated synchronization, artifact upload and publication were skipped; this session requested no cancellation. The current descendant run 43608019736 started its build job 132491079685 at 15:18:24 UTC and retains the integrated 90-minute budget and all validation/publication gates. Source and live results remain pending.

An additional read-only [live byte verifier](verify_published_bank_bytes.py) is prepared for use after publication. It checks the exact expected HTML/source revision, live build-info and manifests, compressed/decoded core index and occurrence identities, and three selectively reconstructed complete source records. It then refetches HTML to reject a revision change during sampling. The helper has passed a syntax check; it has not yet run against the new public site. It requires the implemented repository checkout via `--repo-root`, the expected source commit and the fresh expected HTML SHA-256. Its result will supplement the full corpus and browser evidence, not replace them.

## Reserved integrated-main and live acceptance

Fill these fields from fresh evidence; do not copy candidate values merely because the feature code is unchanged.

| Required final evidence | Current entry |
|---|---|
| Integrated source checkout and main validation report | **PENDING** — run 43608019736; record actual checkout, report timestamp/hash, source count, source/ID/quotation fingerprints and exclusion checks. |
| Integrated site size and browser acceptance | **PENDING** — record fresh portable/site reports, size counter, browser conclusions and any snapshot differences. |
| Published generated commit and deployment | **PENDING** — record generated commit, expected-head/current-main guards, deployment run/job, conclusion, URL and UTC completion time. |
| Independent live artifact binding | **PENDING** — record public HTTP observation, HTML bytes/hash, build commit, index descriptor and compressed/decoded/source/ID verification. |
| Independent live behavior and measurements | **PENDING** — record representative search/workspace/source links, mobile/keyboard/RTL observations, live cold/warm results and screenshots. |
| Final evidence revision and decision | **PENDING** — record evidence-branch commit and close each six-row live status only after successful verification. |

The [f07d5beb live gate](https://github.com/blaghtayt-alt/Hadith-Bank/commit/f07d5bebfdbe333e05159fa8b710495eab4ae249) requires expected HTML and source bindings, validates core-index integrity, independently checks the browser navigation response, exercises production mobile/workspace/wording behavior and measures four live cold/warm searches. Its bounded stale-publication retry cannot count an old site as success.

That gate does not redownload every raw source object, fetch every unused data part, repeat every controlled fixture scenario on public Pages, follow every external source URL or perform a human screenreader session. Full-source preservation comes from the integrated build validation; live checks establish that the intended validated revision is actually served and that representative journeys work. Until those fields are completed, the delivery remains **Integrated; publication/live pending**.
