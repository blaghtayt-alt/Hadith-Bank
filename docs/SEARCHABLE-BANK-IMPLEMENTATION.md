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

Search/index/UI implementation, full-corpus preservation checks, browser tests,
benchmarks, integration and publication remain pending. Local Chromium cannot
open its required Unix socket in this execution environment; actual interactive
baseline checks use the available cloud browser, and exact network/performance
measurements will run in the existing permitted Actions browser runtime. No
browser security setting or validation gate is disabled.
