# Searchable Bank implementation checkpoint

## Ownership and scope

Branch: `feat/searchable-bank-20261114`.
Owner: the user-authorized Pro cloud UI/search implementation in this conversation.
Initial main: `3569d453cddc398275597e994c4d182b1e3a5539`.
Baseline observation: 2026-11-14T11:24:47Z.
Live source binding: `a9b041be744c59932ccd79c2f92df23c78978923`.
Live HTML: 1,341,817 bytes, SHA-256 `99f272f1a303ef1c7818a3a1900124c3bed1062733777fdd5b24638275bb22b0`.
Live source stream: 107,693 occurrences; SHA-256 `bf1af61a17f28f66c2368f09282db3dedde685fa3fa6431a0dcbd4d24950cec1`.
Counts describe published source occurrences, not a unique-hadith audit.

This branch owns reader presentation, navigation/search indexing, reader generation integration, focused software/browser tests, and this implementation evidence. It does not own source intake, material registrations, release manifests, review decisions, source PDFs, or README recovery. Deen Hindi intake and separate Hindi release/PDF-recovery work must coexist. No jobs are cancelled and no main history is replaced.

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
