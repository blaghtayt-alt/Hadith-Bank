# Hadis.islom.uz held-source review

Baseline: `1bdc84b9483a068cc56da97046c55ffe756ea478`.

## Scope and result

All 290 baseline held occurrences were read in their complete current main language fields: 543 fields (254 Arabic, 289 Uzbek Cyrillic), totaling 161,827 Unicode characters. Each decision binds the unchanged baseline row, saved HTML snapshot, source column, language-version ID and exact selected passage with SHA-256 evidence.

279 source occurrences have usable narration/report text; 11 remain held. The 279 comprise 128 Prophetic-attributed reports, 119 Companion reports, 6 Successor reports, 3 mixed report parents, 22 abbreviated transmissions and 1 attributed scholarly saying. These are source classifications, not independent authentication.

518 language fields contribute 547 exact source passages. They form 295 ordered reading components belonging to 292 report families under 279 unchanged parent IDs. Entry 4394 contributes six ordered Arabic/Uzbek reading components for three report families. Distinct chains, repeated source occurrences and language editions are retained.

## Remaining held occurrences

| Occurrence | Category | Reason |
|---|---|---|
| islom:book-17:2578 | uncertain_attribution | The complete current fields contain a qunut prayer and an Ibn Abi Shayba citation, but no named speaker or explicit Prophetic attribution. Nearby Umar material uses a different wording; no identity is inferred. Keep held pending exact attribution evidence. |
| islom:book-22:2817 | uncertain_attribution | The isolated saying has no sufficient individual source citation or explicit speaker in the current fields. The anthology title alone does not establish this specific attribution. Preserve the full wording and keep it held. |
| islom:book-22:2829 | uncertain_attribution | The isolated saying has no sufficient individual source citation or explicit speaker in the current fields. The anthology title alone does not establish this specific attribution. Preserve the full wording and keep it held. |
| islom:book-22:2866 | uncertain_attribution | The isolated saying has no sufficient individual source citation or explicit speaker in the current fields. The anthology title alone does not establish this specific attribution. Preserve the full wording and keep it held. |
| islom:book-22:2876 | uncertain_attribution | The isolated saying has no sufficient individual source citation or explicit speaker in the current fields. The anthology title alone does not establish this specific attribution. Preserve the full wording and keep it held. |
| islom:book-23:4377 | uncertain_attribution | The entry provides only the isolated cleanliness/faith saying and its Uzbek rendering, without an individual citation or speaker. No familiar external reference is supplied from memory; retain it held. |
| islom:book-25:5655 | source_context | This material concerns narrator Awf's age relative to Qatada and compiler biographical explanation. It is a narrator annotation, not a separately established narration for publication; preserve it as context. |
| islom:book-30:7784 | source_context | The Arabic is solely a compiler pointer to a repeated Aisha report already given in full; no finite quoted matn or new abbreviated chain is present here. Uzbek contains only numbering. Keep this locator as source context. |
| islom:book-32:13143 | source_context | The complete fields only direct the reader to source hadith 164; there is no actual quoted narration or new transmission text. Preserve this compiler cross-reference without publishing it as matn. |
| islom:book-32:14183 | source_context | Both current fields are only a chapter heading about the merit of adhan. No narration text is present; preserve the heading as source context. |
| islom:book-32:9982 | source_context | Both fields are a chapter heading and compiler legal explanation of how to greet and respond. There is no separately attributed narration; preserve this source context. |

## Exact boundary and preservation decisions

- Al-Adhkar 2413 contains source framing, Arabic dhikr and a quoted Cyrillic transliteration. The transliteration is explicitly labeled; no Uzbek semantic translation is claimed.
- Mixed parent 2749 preserves three separately attributed Companion/Successor reports; its spelling parenthesis, unattributed assertion and legal discussion remain context.
- Mixed parent 4394 retains Arabic reports 1–3 followed by Uzbek readings 1–3 in original order. No narration text is joined across components and no extra provider ID is created.
- Intercession parent 9105 preserves the main report and separately supplied fourth-return variant, including the source Arabic/Uzbek passages. The compiler pointer is context.
- Four otherwise usable Arabic entries (11967, 6972, 7253 and 8285) have numbering-only or narrator-only Uzbek fields. Those complete fields remain context, with no fabricated translation.
- Entry 8638 has a complete first Uzbek report and a visibly truncated second variant. Only the complete report is selected; the incomplete variant remains preserved context.
- Entry 4261 has different source meanings in its Arabic and Uzbek fields. Both exact fields remain source attributed, with an explicit content-mismatch/translation-equivalence qualification.
- Compiler legal discussions, glossary tails, standalone Quran/lesson headings and pure cross-references are excluded from quotation spans while remaining in immutable source evidence and derivative Comments.
- Quran quotations integral to a coherent narration remain inside the report and carry exact nested source-span annotations. No independent verse equivalence is inferred.

## Verification

All 86 existing saved HTML snapshots were checked against their compressed and uncompressed hashes. The saved parser projection exactly matched 580 full source-column checks covering all 290 occurrences, including empty columns. Original source ledgers and checkpoint hashes remain unchanged.

The shared review adapter was independently executed on all 290 baseline rows. All 543 fields reconstructed exactly from selected quotation spans plus retained context. Every original row, source locator, source column, language ID, own-language reference and detached comment survived unchanged. All 21 multi-span language fields projected into exact reader passages; no numeric-only Uzbek text was exposed as a quotation. Stale current-field and baseline-record modifications were rejected.

## Scope limits

This review covers the complete current main fields of these 290 held occurrences. Detached commentary outside those fields was not separately semantically reviewed. Some compiler context inside the main fields contains subsidiary citations that remain context; they have not been expanded into new independent occurrences. No new publisher pages were acquired and no remote commits, dispatches or publication actions were performed by this review task.

Source-bound narration classification and text-boundary evidence do not certify authenticity, translation equivalence, independent Pro QC, or publication rights. Unresolved attribution is left explicit. No missing source text, Arabic counterpart, translation, chain or canonical reference was reconstructed.

## Evidence files

- `source-review-decisions.json`: complete immutable decision ledger.
- `source-review-summary.json`: counts and held reasons. If copied under an active reviews folder, name this `review-coverage-summary.json` because the adapter treats `source-review*.json` as decision files.
- `saved_source_fidelity.json`: 86-snapshot / 580-column source evidence.
- `adapter-audit.json`: independent execution and reader projection evidence.
- `build_review_decisions.py`: finite explicit per-record review specifications, exact selectors and evidence materialization.
- `audit_review_adapter.py`: isolated adapter audit against the real baseline rows.
