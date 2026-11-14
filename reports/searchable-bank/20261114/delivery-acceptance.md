# Hadith Bank — Delivery acceptance and handoff report

**All six improvements are implemented, accepted in software and staged-browser validation, and merged. Deployment and new-UI live acceptance remain deferred by the existing current-head guard while Hindi imports continue.**

[PR #16](https://github.com/blaghtayt-alt/Hadith-Bank/pull/16) merged on 14 November 2026 at 14:40:59 UTC as `90a24f97f086494000e921e7bec4c8cce14e57ea`. Fresh integrated-main [run 43608019736](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43608019736) passed its build and validation gates for source `9ea5cbae4a6704a0c98254adcd3bb7a4318148f1`. Before publication, main advanced. The guard correctly returned `superseded`, `publish:false`; website upload and deployment were skipped. This report is a completed handoff of implementation and acceptance evidence, **not a completed-publication claim**.

## Revision boundaries and publication state

The feature merge changed exactly 27 presentation, search, build, test and evidence paths relative to its main parent. Its [integration proof](pr-acceptance-43602603900/integration-proof.json) records no changes outside that scope and no source, registry or release edits by the feature merge. Concurrent importer work remains intact.

| Revision role | Exact identity and evidence scope |
|---|---|
| Feature integration | `90a24f97f086494000e921e7bec4c8cce14e57ea`; merged feature head `5ef914fae31d94a5f9acc06884a47dbad78c3789`. |
| Accepted PR/performance source | `ff5a1c6996ee82253cf5c4c34f4eea93e5177a37`, run 43602603900. |
| Fresh accepted integrated source | `9ea5cbae4a6704a0c98254adcd3bb7a4318148f1`, run 43608019736; 109,772 occurrences. |
| Generated **local, unpublished** commit | `34a79043de67bab00a87516e22044a9d86060e86`; withheld by the publication guard. |
| Main observed at the latest checkpoint | `f2ac3dee3636e9113190a7689494041420c4a15b`; not validated by the accepted 9ea artifact. |
| Still-building earlier main revision | `9cd0c75a75f4194a6f9aad4705c5df4fd3edad1e`; its final guard/publication outcome remains open. |
| Actually served public build | `5a6cb8e999941615414e7ae66051aff5935e08a8`; previous reader, 109,211 occurrences. |

The [earlier scope check](main-9cd0-scope-check.json.gz) identifies `9cd` as a direct child of `1a9ce2205896948eb29695b28c2934ae78c93329`, with 531 Hindi-import paths changed: 481 additions, 50 modifications, no deletions and no overlap with the 27 feature-owned paths. The latest complete Git comparison identifies `f2ac3dee3636e9113190a7689494041420c4a15b` as a direct child of `9cd`, changing 529 DeenHindi importer/source-status paths: 476 additions, 53 modifications, no deletions and no feature-owned overlap. These scope proofs distinguish source updates from the implemented interface; they do not validate the newer corpus.

At **16:32:47 UTC**, the automatic retry for `9cd`, [run 43613385963](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43613385963), build job `132503111842`, was still rebuilding. Main’s advance to `f2ac` creates a second supersession of the source revision being built; the `9cd` job’s own final guard result is **not yet known**. The newer [reader run 43616104169](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43616104169) was pending, while [importer run 43616106583](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43616106583) remained in progress. Neither active nor queued work is recorded as a passed or published result.

The exact guard result, skipped upload/deploy conclusions and phase times are in [publication-receipt.json](integrated-43608019736/publication-receipt.json).

## Six-requirement acceptance map

The implementation and focused regressions passed PR acceptance and fresh integrated-source gates. Each public live acceptance remains deferred until a current revision is successfully published; none is closed by an active or pending retry.

| Feature | Commits | Tests | Live status | Limitations |
|---|---|---|---|---|
| **1. Evidence-bound narration families** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [9bb4de57](https://github.com/blaghtayt-alt/Hadith-Bank/commit/9bb4de57e44ffc82ebc3bb1d41213ecbe09e1989), [7fde4516](https://github.com/blaghtayt-alt/Hadith-Bank/commit/7fde4516c6fce0707177644e81885ddfdcfc8bff) | Accepted mappings and exact source/provider bindings authorize presentation grouping. Tests reject number collisions, changed quotation evidence and duplicate complete identities, while preserving distinct editions sharing a short ID. Corpus validation reconstructs every family; Chromium opens versions and evidence. | **Deferred:** awaiting current-head publication, then grouping/workspace checks. | Qualifications and uncertain identities remain separate. This is not a unique-hadith or new scholarly identity audit. |
| **2. Compact ranked index and lazy delivery** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [594a84d8](https://github.com/blaghtayt-alt/Hadith-Bank/commit/594a84d84dd8d5de82c514d37645031a2afe787c), [694aaa66](https://github.com/blaghtayt-alt/Hadith-Bank/commit/694aaa667e7a7521fa36ef200da286864c7f821a), [98cd9e83](https://github.com/blaghtayt-alt/Hadith-Bank/commit/98cd9e835a24039f2eb7cd9f3bcebd193800f4f9) | Query postings, visible previews and selected full details load separately. Cache, cancellation, corruption, source binding, offline failure/retry and exact staging-copy regressions pass. PR benchmark targets complete all cold/warm queries. | **Deferred:** awaiting current-head publication, then live timing/bytes/recovery. | Core startup has a transfer cost; commentary/context search remains explicitly slower. Unrequested hosted details are not automatically available offline. |
| **3. Reference, wording and topic journeys** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [527c9277](https://github.com/blaghtayt-alt/Hadith-Bank/commit/527c927745b1f462b985cf606fa81a9abb83a28a), [926c024b](https://github.com/blaghtayt-alt/Hadith-Bank/commit/926c024b47da0baf11da61a29053e513ebdac61a) | Tests cover canonical/local/provider numbering, strict phrases, Arabic and multilingual normalization, late quotation matches, no results, suggestions and negation-preserving broader wording. Controlled and staged-corpus browser journeys pass. | **Deferred:** awaiting current-head publication, then representative searches. | Broader results disclose missing terms; synonyms/transliteration are bounded editorial retrieval aids, not source taxonomy, semantic-equivalence guarantees or religious rulings. |
| **4. Preferred-language results and source workspace** | [527c9277](https://github.com/blaghtayt-alt/Hadith-Bank/commit/527c927745b1f462b985cf606fa81a9abb83a28a), [926c024b](https://github.com/blaghtayt-alt/Hadith-Bank/commit/926c024b47da0baf11da61a29053e513ebdac61a), [4277317c](https://github.com/blaghtayt-alt/Hadith-Bank/commit/4277317cee8255047d7ceb900ad93a12c03cc769) | Preferred previews and actual matching passages retain separate source/language attribution. Tests preserve versions, stored/link/pending/missing states, qualified links, exports and history. Chromium passes page-return/selection, keyboard, RTL and recovery checks. | **Deferred:** awaiting current-head publication, then workspace/navigation/source links. | Missing translations are not generated; exact passages can require one selective detail request. Accessibility-tree checks are not human screenreader testing. |
| **5. Evidence-backed navigation and facets** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [527c9277](https://github.com/blaghtayt-alt/Hadith-Bank/commit/527c927745b1f462b985cf606fa81a9abb83a28a), [41f00591](https://github.com/blaghtayt-alt/Hadith-Bank/commit/41f00591f215c907e3734b49410bd4a5962bc660) | Source heading hierarchy, category, narrator, report type and named-authority grade checks pass, including combined facets and browsing after clearing Reference mode. Validators reject invented metadata. | **Deferred:** awaiting current-head publication, then hierarchy and facets. | Coverage follows supplied evidence; unknown remains unknown. Generic source types do not automatically become Prophetic reports, and displayed grades remain attributed assessments. |
| **6. Friendly, distinct edition identities** | [055d3107](https://github.com/blaghtayt-alt/Hadith-Bank/commit/055d310754a2faea9f8bb796790ee4e401c45a5e), [926c024b](https://github.com/blaghtayt-alt/Hadith-Bank/commit/926c024b47da0baf11da61a29053e513ebdac61a), [b81baa3a](https://github.com/blaghtayt-alt/Hadith-Bank/commit/b81baa3a7aa827a5266c976b7373aa5ca83b9cef) | Tests require accepted source/partition evidence before grouping technical chunks, retain genuine volumes, reject stale manifests and distinguish unrelated equal captions. Browser checks preserve qualified identities. | **Deferred:** awaiting current-head publication, then captions and provenance. | Titles alone never prove equivalence; “Source edition N” disambiguates presentation and does not invent a publisher edition. |

Fresh integrated gates passed **1,063 Python tests, 48 lazy-store Node tests and 22 search-engine Node tests**. The full corpus step took **27m 22s**; the build job took **43m 56s**. Browser reports passed 15 reader check groups, 18 discovery-fixture groups and two production-corpus groups. Some fixture checks overlap across reports; these counts are not additive counts of unique assertions. “Production corpus” means the staged site served inside Actions.

Evidence: [corpus-summary.json](integrated-43608019736/corpus-summary.json), [reader-runtime.zip](integrated-43608019736/reader-runtime.zip), [artifact-manifest.json](integrated-43608019736/artifact-manifest.json) and [Fawaz preservation evidence](integrated-43608019736/fawaz-preservation.zip).

## Fresh integrated-source fidelity and exclusions

Portable validation completed at **2026-11-14 15:59:14 UTC**. It compared **109,772 complete public projection objects, canonical-record digests and complete reader objects**, checked **84,732,771 Arabic/translation codepoints**, hashed **55,651 source/legacy files** and **1,276 ordered source shards**, and verified **1,509 reader data shards**. All passed. The accepted snapshot contains **252 datasets in 11 languages**.

| Integrated 9ea fingerprint | SHA-256 |
|---|---|
| Ordered source stream | `aafde0add2ad1f77ed7c5f79edf518fbfe3dc212ad117625ec8602bb9deb8e39` |
| Ordered occurrence IDs | `616f3fc8835b64a3b82410f21a582d2f2f60751aa4b65682f06c9e133bd2a084` |
| Exact accepted quotation fields | `6b87d0d85863b5e44d91da214e773c2c99ba1a19b71919048e6a277e439de554` |
| Reader HTML, 1,807,788 bytes | `d221fc56e30f767fcd4da57a9229bedf30ebfa20c08930f379d308a67c068a48` |

The production detail-stream hash happens to equal the source-stream hash here. Byte-identical JSON serialization is not a general preservation invariant: the browser fixture deliberately reports `canonical_bytes_match_reader_bytes:false` while verifying decoded complete-object equality and exact quotation fields.

Compared with the accepted PR snapshot, **366 additional occurrences** occur entirely in five Hindi datasets: Abu Dawud +93, Bukhari +73, Ibn Majah +42, Muslim +73 and Nasai +85. The report inventories show 732 added source files, no removals and 29 changed hashes, all on DeenHindi paths. This describes source-snapshot growth; differing corpus/ID/quotation fingerprints do not establish UI-induced rewriting.

Public-scope checks, pinned source hashes and review/rights statuses passed unchanged. Fawaz views still account for **36,464 provider occurrences: 36,226 reader occurrences and 238 excluded original-source entries**. Excluded source texts remain preserved and outside narration search. The separately scoped saved-review preservation gate passed; this UI work does not claim new scholarly review. Counterpart queue preparation remains candidates-only and accepts zero new alignments.

There are **2,475 evidence-bound families containing 8,555 source occurrences**, producing **103,692 presentation results** including singletons. These are not independently authenticated unique-hadith counts. The reported 252 editions are dataset-level; the reports do not provide a distinct friendly-edition-group total.

`source_files_modified:false` means stable bytes during validation. `baseline_git.performed:false` does not establish a complete historical cross-commit comparison. Full-object fidelity protects accepted records and provenance; it does not certify original transcription, translation accuracy, narration authenticity or rights.

## Integrated index and packaging

The core discovery index is **8,017,733 compressed bytes**, expanding to **80,170,898 bytes**. Its SHA-256 is `0ba4d3e5011b7920200e5d7054bde636f0214870cd351c49b44527e486db8658`. Another 162 posting parts and 429 preview parts bring the complete index inventory to **101,037,781 compressed bytes**. Startup does not download the complete inventory. The fresh production browser confirms that home requests no full detail parts and binds the observed HTML, source count/hash and index descriptor to the accepted build.

The site counter is **944,890,264 bytes**, below the unchanged **950,000,000-byte** gate, retaining 38,782 stable narration pages. The counter precedes final build-info/marker writes; adding those known writes gives a **derived**, not independently inventoried, staged total of **945,731,991 bytes**, leaving **4,268,009 bytes**. Continuing imports can consume headroom; subsequent builds must pass the same gate.

The runtime archive is **6,725,930 bytes**, SHA-256 `1c65eee874b9c47402d981c4c945198c0121c1cc5d4ec67c6b45847c9602dad5`. Its six report hashes and source/HTML/index bindings were independently checked against the saved artifact manifest. These are fresh successful-build reports, not checked-in reports left behind by a failed stage.

## PR performance evidence, including startup regression

The following measurements belong only to [PR run 43602603900](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43602603900): baseline source `a9b041be744c59932ccd79c2f92df23c78978923` with 107,693 occurrences, versus candidate `ff5a1c6996ee82253cf5c4c34f4eea93e5177a37` with 109,406. They are **not live measurements or a 9ea benchmark**.

Chromium 151.0.7922.34 used a 1366×900 viewport. Every query started in a fresh context, and its warm repeat followed a completed cold search. All 16 search measurements and eight startups completed without pending/failed requests or page errors. Bytes are completed CDP encoded transfer; cold totals include startup and query work. MB means 1,000,000 bytes.

| Query | Cold journey, baseline → candidate | Cold bytes, baseline → candidate | Warm search, baseline → candidate |
|---|---:|---:|---:|
| Bukhari 1 | 2.733 → 2.197 s | 9.46 → 10.27 MB | 584 → 89 ms |
| actions depend on intentions | 11.487 → 2.300 s | 81.17 → 12.02 MB | 9,161 → 91 ms |
| anger | 12.224 → 2.356 s | 86.34 → 13.73 MB | 9,326 → 99 ms |
| controlling anger | 11.900 → 2.327 s | 79.66 → 14.07 MB | 8,995 → 79 ms |

**Startup transferred more:** 3,327,964 baseline bytes versus 9,804,277 candidate bytes, with approximately 1.99–2.04 versus 2.04–2.08 seconds on the local host. The complete cold Bukhari journey therefore transferred **8.54% more**, despite being faster in this sample. The three wording/topic journeys transferred **82.34–85.19% fewer** cold bytes and took about 80% less time. Candidate warm repeats required zero additional bytes.

These are **one sample per query and warmth**, without CPU/network throttling, percentile estimates or statistical confidence. Different source snapshots and retrieval semantics prevent an isolated same-corpus attribution. Bukhari 1 preserves 26 matching occurrences as 15 results. The remembered wording query yields 12 transparently broader results, not an exact-phrase success. Topic expansion changes counts deliberately; more results are not an accuracy score. Optional commentary search retains its labelled slower path.

## Observed visual and review limits

Fresh integrated 390px-wide CI screenshots for 9ea were reviewed against the accepted PR captures. No concrete visual regression was found; the captured result cards and source panels remain pixel-identical below the updated information areas. These are staged screenshots, not new public UI screenshots. Explanations/disclosures still use substantial vertical space: first reference and broader-wording cards begin around document y819 and y1076 respectively. Full-page screenshots do not establish exact viewport positions. Source captions wrap; closed native selectors truncate long selected labels, with fuller provenance available in workspace panels.

A preferred-language preview may precede the actual hit. “Show matching wording” retrieves an exact passage with its own source identity. Production screenshots show the control but do not demonstrate it expanded; exact passage binding is established by automated fixtures.

Chromium covers keyboard navigation, focus, RTL, overflow, DOM/ARIA and accessibility-tree behavior. It does not establish comprehensive accessibility conformance or a human NVDA, JAWS or VoiceOver session. No new PDF page/glyph, independent linguistic, translation, authenticity or rights review is claimed. Neither corpus equality nor representative browser checks follow every external source URL.

## Actual live observation and remaining acceptance

The latest verified live receipt available to this report is the [16:35–16:36 UTC HTTP observation](live-observation-20261114T163600Z.json). It establishes that Pages then served the previous build `5a6cb8e999941615414e7ae66051aff5935e08a8`: **HTTP 200**, **1,350,084 HTML bytes**, SHA-256 `da1e5f4827fa8df243e83c97ccc8e0c8401cce9d58586170a0fced8304163fd1`, **109,211 occurrences and 252 datasets**. The HTML response at **16:35:52 UTC** remained identical on its **16:36:00 UTC** refetch, and the intervening build-info response agrees. The compact discovery descriptor and new discovery engine are absent. This is affirmative evidence that the new interface was **not yet live**, not merely an unperformed check.

The independent [live byte verifier](verify_published_bank_bytes.py) is prepared and syntax-checked but **has not run for the new UI because no new-UI deployment occurred**. After publication it requires the fresh expected source commit and HTML hash, validates live build-info/manifests/core index, and selectively reconstructs three complete representative records by full identity and declared byte spans. A final HTML refetch rejects revision drift. It supplements the full-corpus validation; it does not download or audit every unused source part.

The existing [live gate](https://github.com/blaghtayt-alt/Hadith-Bank/commit/f07d5bebfdbe333e05159fa8b710495eab4ae249) additionally checks expected revision/HTML bindings, actual mobile/workspace/wording behavior and four live cold/warm searches. Its bounded retries cannot count an old site as success.

**Remaining delivery requirements are a revision that stays current through the complete build and publication check, an actual successful deployment, and passing expected-revision live gates and independent verification.** The guard remains intact: the `9cd` automatic retry is still rebuilding and the newer `f2ac` reader run is pending under the existing workflow. Continuing imports can advance main again; no successful outcome is assumed for either run. The accepted `9ea` evidence, latest source head and observed `5a` public build remain separate. New-UI live acceptance remains deferred.
