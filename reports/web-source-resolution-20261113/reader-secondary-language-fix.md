# Reader build repair: an admitted secondary language is reviewable source text

## Observed failure

Reader run [43409749952](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43409749952), on source commit `92bf9cdf87f5919b91eadfce8f338e283e6d12bb`, passed its 946 Python tests, Node tests, Fawaz export, website-review export and counterpart-source synchronization. The shared refresh then stopped at 2026-11-13 10:52:30 UTC with:

> Occurrence has no source text to review: deenhindi-malik:1057

Browser validation, generated-file publication, Pages upload and deployment did not run. This was a build failure, not a superseded deployment.

The failing path is `refresh_bank.refresh()` → `prepare_counterpart_review.prepare_review()` → `counterpart_review.source_binding()`. The generated counterpart candidate queue accepted only the flattened `text_translation` or `text_arabic` fields. The material registry and reader already support source language versions whose independently admitted text is not in either primary field.

## Actual source case

Malik 1057 belongs to the exact prior-review reuse complement, not the manual Muslim/Malik cohort. Its original Arabic and English source strings are empty. Hindi and Roman Urdu are retained as unread context. Its independently reused Urdu field supplies **224 selected characters in two exact spans**. Native `SourceReviews.apply()` correctly leaves both canonical primary fields null while retaining that Urdu reading and its complete source context.

The regression fixture contains the actual saved source object, original snapshot and parsed-source receipts, and deterministic prior-review reuse decision produced from the phase 2 reviewed catalog. It introduces no new semantic decision. The test applies that decision with the native adapter, registers the derivative in a temporary fixture material, and runs the actual material projection and counterpart queue. Its temporary material explicitly identifies the frozen JSON fixture as the test asset; it does not fabricate archived HTML.

## Change

The three changed consumers recognize a secondary field through `language_versions:<stable-version-id>`. A default binding keeps the existing primary-translation/Arabic preference. When both are absent, it deterministically chooses an existing nonempty quotation version; context-only, pending, missing and ambiguous versions are rejected.

The binding records the exact version ID, its own language code, the selected-text SHA-256 and a SHA-256 of the complete language-version object, in addition to the existing occurrence, canonical-record, source-file and locator checks. The complete-version hash includes source context and metadata. The occurrence's primary language and its primary text values are unchanged.

The queue uses that same exact field for its preview. Explicit counterpart quotation evidence, compilation and runtime validation use the same accessor and binding, so a generated secondary-field candidate cannot silently switch languages during later review. Existing primary-field bindings retain their original shape. Preparation still approves zero counterparts, and no candidate matching rule was broadened.

## Focused validation

**44 tests passed**: 21 existing counterpart review workflow/compiler tests, 19 existing reviewed-counterpart resolver tests and four new secondary-language regressions.

The new tests cover the actual Malik 1057 review and material projection; unchanged source/canonical files and empty primary fields; exact Urdu queue preview and zero automatic approval; explicit TEST-only counterpart compilation/runtime consumption; rejection of changed quotation text, version language, ID, retained context, missing/duplicate versions and missing binding metadata; and rejection of absent primary or context-only text as substitute evidence. The existing tests continue to cover stale source/target hashes, per-language approvals, partial coverage, immutable bundles, missing English, number-only rejection and source preservation.

The baseline versions of all three changed scripts and the unchanged compiler were verified against their GitHub blob IDs at `b65b894adfc1fcd80ff2ebbcedba60970e4f163f`. The patch is isolated; no importer, source-review decision, source text, registry guard or workflow was edited. No GitHub writes or source HTTP requests were made by this work.

The complete repository refresh and eventual browser/deployment checks remain CI gates. This report establishes a focused repair of the observed failure and its affected binding consumers; it does not claim a successful new deployment.
