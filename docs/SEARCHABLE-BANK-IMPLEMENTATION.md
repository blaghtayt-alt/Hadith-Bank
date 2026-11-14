# Searchable Bank implementation checkpoint

This file records the implementation and validation history. Pending states
below describe their recorded checkpoints. Current integration and publication
evidence is maintained in [PR #16](https://github.com/blaghtayt-alt/Hadith-Bank/pull/16).

## Ownership and scope

Branch: `feat/searchable-bank-20261114`.
Owner: the user-authorized Pro cloud UI/search implementation in this conversation.
Initial main: `3569d453cddc398275597e994c4d182b1e3a5539`.
Baseline observation: 2026-11-14T11:24:47Z.
Live source binding: `a9b041be744c59932ccd79c2f92df23c78978923`.
Live HTML: 1,341,817 bytes, SHA-256 `99f272f1a303ef1c7818a3a1900124c3bed1062733777fdd5b24638275bb22b0`.
Live source stream: 107,693 occurrences; SHA-256 `bf1af61a17f28f66c2368f09282db3dedde685fa3fa6431a0dcbd4d24950cec1`.
Counts describe published source occurrences, not a unique-hadith audit.

This branch owns reader presentation, navigation/search indexing, reader generation integration, focused software/browser tests, and this implementation evidence. It does not own source intake, material registrations, release manifests, review decisions, source PDFs, or README recovery. Deen Hindi intake and separate Hindi release/PDF-recovery work must coexist. Other workers' jobs are not cancelled and main history is not replaced. The existing PR concurrency policy may supersede this branch's own older validation run when its revision changes.

## Authorized requirements

1. Evidence-bound presentation families using accepted mappings only; preserve every occurrence/version and keep uncertain identities separate.
2. Compact multilingual ranked search with lazy details, measured cold/warm bytes and latency, cancellation and honest loading/error/offline states.
3. Reference, remembered-wording and topic journeys; distinct numbering systems; phrases, Arabic search normalization, explicitly editorial synonyms/spelling assistance.
4. Compact preferred-language results, on-demand Arabic/English/selected-language workspace, exact stored/link/missing states, source evidence and preserved deep links/export/reading controls.
5. Evidence-backed collection/book/chapter, narrator, content-type and named-authority grade facets; separately labelled editorial topic navigation.
6. Friendly edition/translator labels, technical parts grouped only by evidenced edition identity, distinct editions disambiguated; hashes remain in provenance.

## Preservation and acceptance

- Source IDs, exact source wording, source-stream hashes, exclusion policies, provenance and all source/review/variant evidence remain unchanged by UI/index transformations.
- Exact-reference, phrase, Arabic normalization, multilingual preference, no-result, ambiguity, numbering collision, facet, missing-counterpart, evidence-grouping, source-link and deep-link regressions.
- Actual desktop/mobile, keyboard, accessibility-tree/screenreader-semantics and RTL checks. Do not equate semantics checks with a human screenreader session.
- Measure baseline and candidate cold/warm search time and network bytes. Preserve raw observations and distinguish completed from partial searches.
- Reconcile current main before integration. Use small scoped commits and expected-head/normal fast-forward or merge operations; never force-push.
- Record integrated source commit, successful deployment run, live artifact hashes and representative live outcomes separately.
- Finish with a six-row feature/commit/test/live-status/limitations record.

## Current stage

Selective detail retrieval is implemented: opening one occurrence loads only its
verified directory part plus the required exact detail chunks. Full-directory
verification remains available and unchanged. All 45 lazy-store tests passed,
including selective-request, corrupted-hash, discontinuous-span, cancellation,
Unicode reconstruction, source-identity, cache and export regressions.

The source-bound multilingual index, query-only postings and page-preview
delivery, evidence families, source facets and friendly edition grouping are
implemented in `055d310754a2faea9f8bb796790ee4e401c45a5e`.
Generation and source-binding validation are implemented in
`9bb4de57e44ffc82ebc3bb1d41213ecbe09e1989`. Their gates compare every derived
identity, exact preview and source-language/provenance field, rebuild family
evidence, check reference/facet coverage, and verify all compressed part hashes
and posting structure. This is source-preservation verification, not an
independent religious or translation review or a proof of exhaustive recall.

The complete local Python suite passed 1,038 tests in 59.652 seconds on
2026-11-14T11:53:31Z. Later focused UI/adapter fixes are tested separately and
will pass the full suite again in Actions. The current refreshed input from
initial main contains 108,502 source occurrences in 252 registered datasets,
2,151,071,356 source-view bytes, and source-stream SHA-256
`29a3831017a5c4dd717ce7494bcbc84e8277fa565ca07e3b0caf4da218d2a611`.
Its larger count reflects imports newer than the original live baseline.

A local complete reader build was killed with exit 137 while the existing
loader was materializing the source corpus, before an output was produced.
A bounded streaming pass separately verified all 1,263 source shards, counts
and aggregate hash at roughly 130 MiB peak RSS; full reader publication and
actual browser gates will run in the repository's Actions environment.

Compact search/topic/library journeys, preferred-language result cards, exact
on-demand matching wording, source-version comparisons, scoped deep links and
friendly distinct collection labels are implemented in
`527c927745b1f462b985cf606fa81a9abb83a28a`. Its 97 focused UI/search regression
tests and final inline JavaScript syntax check passed.

Full-corpus
index measurements, actual browser tests, integration and publication remain
pending. Local Chromium cannot
open its required Unix socket in this execution environment; actual interactive
baseline checks use the available cloud browser, and exact network/performance
measurements will run in the existing permitted Actions browser runtime. No
browser security setting or validation gate is disabled.

## Full-corpus findings before browser acceptance

PR #16 reconciles main `4f8b169d5a9662e6e3e6b4e6a60f2a2a82951861` in
normal two-parent merge `a6356931c721c502645fa7f51b6ac86e8a84e2ed`. Its
505 importer-path changes and the 23 initial UI/search paths had no overlap.

The measured 108,502-occurrence index used a 7,962,272-byte navigation transfer,
160 selectively requested posting parts and 424 page-preview parts. Bukhari 1
retained all 26 matching source occurrences as 15 evidence-bound presentation
results; it needed no word-posting part and 503,562 bytes of preview parts.
These are local artifact byte measurements, not internet timing. Later friendly
caption refinements require final Actions artifact measurements.

Full-corpus tests exposed the old all-word limitation for remembered wording.
The corrected unquoted-wording path offers explicitly labelled broader results
only after strict matching yields none; it requires at least two meaningful
query words and every query negation within one actual stored reading. Found
and missing terms and the matched language are visible. Reference/ID searches
and quoted phrases remain strict. The example “actions depend on intentions”
then finds 12 broader source results; its quoted form remains zero.

The old published site already occupied 934,787,115 bytes. To accommodate the
new index without raising the 950 MB gate or removing stable pages/source
content, static source metadata now uses compact, safely escaped JSON with
identical decoded values. Redundant optional social/page metadata is omitted
while ordinary titles, descriptions, canonical links and structured source
identities remain. Lossless reader-part gzip compression is strengthened.
Measured metadata savings were 44,345,309 bytes; duplicate social tags accounted
for 27,239,241 bytes on the 38,782 existing narration pages. Recompressing the
old reader stores saved another 4,932,686 bytes. Final staged-site size remains
an enforced Actions gate, not an inferred publication result.

The complete local suite subsequently passed 1,043 Python tests and all 66 Node
tests after the wording/packaging corrections. A further staging optimization
reuses the exact already-validated sharded reader instead of generating its
index twice: HTML/source/site/manifest bindings and every copied data part's
bytes and SHA-256 are checked before publication. All ten focused reuse tests
and four existing staging-integration tests pass; standalone-to-hosted builds
still follow their original path. Actual Chromium fixture checks now run before
the expensive corpus build, with the real-corpus checks retained afterward.

## First actual Chromium findings

Actions run `43594697977` checked out synthetic merge
`2f0ded91b727b992453476a494d6927289492424`, combining feature
`694aaa667e7a7521fa36ef200da286864c7f821a` and current source main
`a5ffb77d730d5706ca7ef94582e222c46d49a8ca`. All 1,053 Python tests and both
Node suites passed. Actual Chromium passed the home keyboard/live-region,
default-field reference recognition, numbering-collision, evidence-family and
preferred-language checks, then failed when opening the workspace.

Diagnosis reproduced against the actual fixture and lazy transport: directory
validation still rejected repeated short occurrence IDs even when the complete
source identities belonged to distinct editions. Because an entire directory
part is verified before use, that collision also blocked an unrelated source in
the same part. The corrective change must validate complete identities and keep
true duplicate-identity, corruption, span and source-binding checks intact.

The failed-run archive `14113908683` is 4,148,743 bytes with SHA-256
`b59dec5f38d9ee7961ab0d809d3de2096316f6baf605a5657cabe1fae46c84e0`.
Its fixture JSON and desktop home/result screenshots are actual new evidence;
its pre-existing portable/site reports are not new build evidence because that
stage was skipped. Screenshot inspection also identified the need to condense
the home introduction while showing results or a workspace.

An independent live refetch at 2026-11-14T12:31:18Z still returned the original
1,341,817-byte HTML, SHA-256
`99f272f1a303ef1c7818a3a1900124c3bed1062733777fdd5b24638275bb22b0`,
bound to `a9b041be744c59932ccd79c2f92df23c78978923` and 107,693 source
occurrences. This is the baseline, not publication of the new feature.

The complete-identity correction is in
`7fde4516c6fce0707177644e81885ddfdcfc8bff`. All 48 lazy-store tests pass,
including distinct editions with a shared raw ID, true duplicate-identity
rejection, and rejection of a correctly named ID with the wrong edition's
detail. The exact failing 11-record fixture also passes selective and complete
directory retrieval in Node. This is a transport reproduction, not a new
Chromium pass.

`43df8e547d81e304fb7d64714bea2ba4693ae7d2` restores the full introduction on
home and removes it from visual flow during search and reading. Fourteen
focused UI tests pass, including home/results/workspace/return transitions;
actual updated viewport geometry remains a browser gate. The 541 paths changed
between source main `4f8b169d5a9662e6e3e6b4e6a60f2a2a82951861` and
`a5ffb77d730d5706ca7ef94582e222c46d49a8ca` have no overlap with the 26
scoped feature paths.

After those fixes, all 1,053 Python tests passed locally in 60.796 seconds at
2026-11-14T12:37:26Z. The browser verifier now records the exact failing phase,
traceback, bounded rendered/error/focus state, request failures and a screenshot
before closing a failed page. Existing assertions remain; viewport checks now
require the first desktop result above y600 and verify that the full home hero
is restored. Five focused verifier-planning tests, syntax and fixture generation
pass. The next actual Chromium run is still required.

Run `43595830933` then tested merge
`44f69a5b7481e73dce980ee63ebea4d0f95e75a0` (feature `7a62dfd3` plus source
main `a5ffb77d`). Actual Chromium passed nine check groups, including the
previously blocked workspace, exact source/version comparisons, source links,
RTL, separate preferred/matching languages, transparent broader wording,
phrases, Arabic normalization, no-results, topic/spelling aids and unique-ID
Back navigation. It stopped at a stale test expectation that required raw
edition IDs in friendly captions. The actual screenshot and index show distinct
`Source edition 5`/`Source edition 6` captions; source identities remain A/B.

The verifier correction now checks the exact distinct friendly captions, both
original edition/source attributes, every qualified link identity field, and the
existing full-object/deep-link audit. It does not weaken the ambiguity gate or
invent a published edition name. The run's verified evidence archive
`14114044840` has 4,372,762 bytes and SHA-256
`56c58dc02590e44ee12d22b668bbd7b7b420528c77ab742f4317803988e86aff`.
Its unchanged pre-existing portable/site reports remain excluded from new
build evidence because the corpus stage was skipped.

A read-only audit of the remaining real fixture assertions reproduced a second
interaction defect in the engine: after choosing Reference, clearing the query
and browsing a collection/book/chapter returned zero results. The reference
rejection guard must apply only to nonempty queries. Empty and whitespace-only
queries now browse the same filtered source set in every journey; nonempty
invalid references remain strict. The existing browser facet assertion is kept
unchanged, with an additional engine regression using the same fixture and its
actual evidenced parent/chapter metadata.
All 22 focused Node engine tests pass after this one-condition correction; the
48 lazy-store tests remain passed. The full Actions gates still apply.
