# Reader startup recovery checkpoint — 2026-11-13

## Status

The Fawaz source recovery, GitHub upload and website deployment are complete.
The subsequently observed interactive-reader startup problem is **not fixed**.
This recovery directory contains an unapplied work-in-progress patch, an untested
projector, an unverified proposed producer patch, and the agreed remaining
contracts. It does not change live application code or source decisions.

The execution environment became unavailable during implementation. Local
commands returned an execution-server transport disconnection and browser access
was withdrawn. Do not treat the partial UI patch or the older successful
publication tests as validation of the new reader architecture.

Recovery base: `7e14c380923e9bae49a1992e6f0048fde0014279`.
Its direct parent is the published generated commit
`608459923f1fb52e099905d1244c5acee6604078`.
Resume in a fresh isolated checkout of current main, preserving later source
imports; inspect and apply these patches deliberately rather than resetting main.

## Already published: do not redo or re-upload the Fawaz recovery

- [Merged PR 12](https://github.com/blaghtayt-alt/Hadith-Bank/pull/12).
- Reviewed source commit:
  `24268ec1ec4bd334c5aa52be541ff0d8e48de990`.
- Normal merge commit:
  `40a7fc9ae90624addd9ca92e3649ecbc491c4ce0`.
- [Successful publication run 43333866634](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43333866634).
- [Build job 131585020660](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43333866634/job/131585020660):
  793 software tests passed, full rebuild and guarded generated-file push passed.
- [Deployment job 131595558775](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43333866634/job/131595558775):
  current-bank guard and Pages deployment passed at 2026-11-13 00:26:12 UTC.
- Published build input:
  `6cac42443fee6eca665405ef71cebcbb9ecffba6`.
- Generated commit:
  `608459923f1fb52e099905d1244c5acee6604078`.
- Whole-bank source occurrences in that publication: **87,709**.
  This includes 637 additional Hindi occurrences from the existing separate
  intake, beyond the PR build's 87,072.

### Fawaz result

| Measure | Count |
|---|---:|
| Provider IDs retained | 36,464 |
| Original registered IDs preserved | 29,911 |
| Recovered new positive IDs | 4,014 |
| Fresh positive IDs | 2,295 |
| Total additions | 6,309 |
| Registered IDs | 36,220 |
| Held IDs | 244 |
| Missing original IDs | 0 |
| Changed original language quotations | 0 |

The held IDs comprise 169 entries empty in all supplied languages, 73
explanation/commentary entries, one literal missing marker and one
chain/introduction without report text. Every nonempty language field of every
held ID was individually inspected.

The fresh review also retains **6,112 unread sibling-language fields** as
explicit source context: Arabic 2,099, Urdu 1,866 and Bengali 2,147. These are
fields, not unaccounted provider IDs. They are not admitted quotation text or
default narration-search text. Do not claim complete all-language semantic review.

The previous chat's claimed 6,331-addition / 36,242-registered / 222-held completed
artifact was not recovered. Do not manufacture decisions to match those numbers,
or describe the difference as 22 identified deletions or corrected classifications.

Committed evidence:
- [Transfer diagnosis](https://github.com/blaghtayt-alt/Hadith-Bank/blob/24268ec1ec4bd334c5aa52be541ff0d8e48de990/docs/FAWAZ-TRANSFER-RECOVERY.md).
- [Cohort review summary](https://github.com/blaghtayt-alt/Hadith-Bank/blob/24268ec1ec4bd334c5aa52be541ff0d8e48de990/reports/fawaz-import-review/continuation-20261113/fresh-reviews/cohort-review-summary.json).
- [Published source progress](https://github.com/blaghtayt-alt/Hadith-Bank/blob/6cac42443fee6eca665405ef71cebcbb9ecffba6/imports/web-fawaz-20261112/progress.json).

The source diagnostics artifact was 13996502363, SHA-256
`5a6a5df1a1f3687f2fa936b12decf0ebb4755e0d2b858f882c4a95177cb374c9`.
It matched the successful PR candidate audit. The deployed Pages artifact was
13998605143, 188,270,400 bytes, SHA-256
`af3ab75d8dd7641ea734a947ea6070fc054212c42e9290efcb167c4a72beb54d`.
Actions artifacts have finite retention; the committed source decisions and
reports remain the durable source evidence.

## Actual public UI observations

The primary agent reloaded and visually inspected the
[Fawaz source index](https://blaghtayt-alt.github.io/Hadith-Bank/source-editions/fawaz/index.html).
It showed 36,464 provider entries, 36,220 reader entries and 244 original-source
entries, with these book totals:

| Book | Registered | Held |
|---|---:|---:|
| Abu Dawud | 5,241 | 33 |
| Bukhari | 7,583 | 6 |
| Ibn Majah | 4,343 | 0 |
| Malik | 1,838 | 51 |
| Muslim | 7,508 | 56 |
| Nasai | 5,676 | 89 |
| Nawawi | 42 | 0 |
| Tirmidhi | 3,989 | 9 |

[Muslim 5676's held original-source page](https://blaghtayt-alt.github.io/Hadith-Bank/source-editions/fawaz/muslim/entry-01c129ed7519d254ea277de8.html)
responded and visibly preserved Arabic, English, Urdu and Bengali lexical
explanations outside narration display.

The interactive reader did not complete verification. An ordinary load and one
deep-link navigation became unresponsive to DOM and screenshot requests for
minutes while the source index and held page remained responsive. The observed
loader progressed through parts 70 and 287 of 795 before becoming unresponsive.
A later request to close that reader tab timed out; its final tab state is unknown.

This does not establish an observed out-of-memory exception, browser heap limit
or a specific garbage-collection pause. It establishes an unusable verification
session plus a concrete excessive eager-load design.

## Reader payload and diagnosis

The exact published
[reader manifest](https://github.com/blaghtayt-alt/Hadith-Bank/blob/608459923f1fb52e099905d1244c5acee6604078/hadith-bank-reader-data/manifest.json)
was read and its sizes summed:

- Records: 87,709.
- Compressed parts: 795.
- Compressed bytes: **139,072,149**.
- Decoded JSONL bytes: **1,653,180,693**, approximately 1.54 GiB.
- Source-stream SHA-256:
  `575314081dbc52aa61d6371871f111ed45e4b2709626f26b677d1db3264c44c1`.

The v1 loader retains all parsed full records. Only afterward does it build
citation-pair sets and normalized primary-search strings, then apply the exact
occurrence filter. A deep link therefore does not bypass the eager load.
The additional Fawaz report-group renderer runs only for displayed cards and
does not explain a stall at part 287. No whole-bank O(N^2) loop was found.

An actual 100-record Abu Dawud shard measured 3,016,222 complete JSONL bytes,
827,066 primary-key bytes and 426,465 annotation-key bytes. These two keys alone
were 41.56% of that sample. Repeated long strings within records accounted for
624,136 bytes. This is a sample, not a whole-bank ratio. Interning or putting
the same eager load in a worker would not establish a memory bound.

## Saved implementation state

| File here | What is actually known |
|---|---|
| `reader-template-wip.patch` | Exact hunks from the successfully applied UI edit; only its update path was made relative for replay. The resulting local script passed a Node syntax check before disconnection. No new functional/browser tests passed. |
| `reader_projection.js` | Exact Node projector file from a completed local write. It extracts the existing pure JavaScript search/filter functions. It was not syntax-tested or run. |
| `build-reader-proposed.patch` | Exact issued Python producer patch, including the original absolute path. Its call never returned success before disconnection; the outstanding call was terminated. Whether any local write occurred is unknown. Review and adapt its path before applying. |
| `datastore-contract.md` | Agreed runtime interface and validation plan. **No `reader/lazy-store.js` implementation or runtime tests were written.** |

The unapplied patches do not constitute a complete or runnable repair.
In particular, the template references a missing lazy-store implementation.
The standalone/offline reader path and legacy v1 loader must remain covered.

## Repair architecture and required invariants

Load a small occurrence/filter directory first. Hydrate only the current page's
25 complete records or explicitly selected downloads. Preserve the exact full
record stream, including every source context, reference, report group,
provenance value and null/unknown field.

Keep primary and annotation search data in separate bounded parts. Scan needed
parts when a query requires them; never retain the entire bank's text keys.
Canonical citation-only queries and exact ID/deep-link queries can use directory
metadata. Query cancellation and page generations must prevent an old request
from replacing newer results. A failed or incomplete search must not appear
as a complete zero-result search.

The existing detail gzip parts may split both JSON records and UTF-8 characters.
The directory must map each ordinal to its exact global byte offset and length,
including the terminating newline. Detail hydration validates hashes and lengths,
joins necessary byte slices, decodes strictly and verifies all identity fields.

Use the existing JavaScript normalization and scalar behavior for projections.
Python casefold and number stringification are not interchangeable with JavaScript
lowercase and String. Booleans are excluded by existing searchStrings.
Default search excludes annotation text; with commentary enabled, different
query terms may match primary and annotation fields of the same occurrence.

The browser's decoded-part cache is intended to be bounded at 8 MiB, with at most
four active requests. This is a cache bound, not a claim that the entire page
uses only 8 MiB. Directory objects, visible full records, active requests and
explicit selected downloads also occupy memory.

## Resume sequence

1. Read this checkpoint and current main. Do not repeat the finished Fawaz review,
   original source downloads or 6,309-addition upload.
2. Create an isolated checkout preserving newer main changes. Inspect the
   recoverable template and producer patches; do not apply the producer's old
   absolute filesystem path unchanged.
3. Complete `reader/lazy-store.js` from the adjacent contract. Integrate the
   projector and producer; make the template's inline module replacement explicit.
4. Review the proposed producer for malformed previous-manifest cleanup,
   subprocess backpressure and error termination. Publish a new top manifest
   only after its files are complete. Remove only verified obsolete generated
   parts referenced by the previous manifest; preserve unrelated or edited files.
5. Update portable/site validation for v2. Validate the full detail record stream
   against the canonical source hash; do not substitute a search-projection hash.
   Preserve v1/offline coverage in existing reader-shard tests.
6. Measure and report whole-bank maximum directory/search/annotation row sizes.
   The proposed whole-row stores fail explicitly when a row exceeds the part
   limit; no all-bank maximum had been measured at interruption. Do not truncate.
   Include maxima and directory sizes in final build evidence; refresh_bank
   currently copies only a subset of hosted-reader result fields.
7. Run focused fidelity, search parity, filtering, corruption, cancellation,
   cache-bound and selected-download tests. Review stale page/search behavior.
8. Run the normal full source-preservation and reader build gates. Upload code
   and small review inputs through the authenticated connector, and generate
   large outputs in Actions. Keep current-main guards; do not stop the unrelated
   Hindi intake or force-push merely to avoid a superseded build.
9. After actual successful deployment, test the live ordinary homepage and a
   Fawaz exact-occurrence link in a working browser. Confirm that startup fetches
   directory and required detail parts rather than all full-record parts. Check
   full-text search, commentary opt-in, paging, exact selected JSON, and a held
   original-source page. Only then describe the reader issue as fixed.

## Other historical error findings

The old full-export checkpoint explicitly recorded
`failed_no_space_left_on_device`, a local write failure. Large encoded transfers
and verbose output consumed conversation context. Current-environment direct Git
write authentication was absent, although public reads worked and the connector
could write. Two later reader builds were correctly superseded by concurrent
source updates before deployment; the final publication above succeeded.

A previous `Transport closed` message had no HTTP response code, and the old
`Auto-review stopped` reason was not recovered. Neither establishes a GitHub
rate limit. The 64 KiB review-input chunks and earlier 128 KB transfer pieces are
internal transport choices, not GitHub's general file-size limit.
