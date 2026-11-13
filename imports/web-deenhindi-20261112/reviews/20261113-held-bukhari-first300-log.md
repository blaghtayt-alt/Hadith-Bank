# Deen Hindi: first 300 held Bukhari occurrences

## Frozen first-pass decision

This review explicitly registers each of 300 source occurrences using only its individually supported language fields. It does not approve every supplied language. The main decision file is `20261113-held-bukhari-first300.json`, schema `hadith-bank-web-source-review-v1`, SHA-256 `7a7771c8584601684a0e2a28b264dc3884e95bed5309c533641f9c446a55c293`.

For discovery by the shared adapter, publish these exact bytes under the filename `source-review-20261113-held-bukhari-first300.json`. The adapter intentionally scans `source-review*.json`. The date-prefixed source file remains the frozen local original; its SHA is authoritative.

The baseline is repository commit `1bdc84b9483a068cc56da97046c55ffe756ea478`. The selection follows the importer's collection order, then the source's observed inventory identifier order, taking the first 300 held rows. All are Bukhari; the first provider number is `4` and the last is `1178`. This is an explicit identifier list, not an invented continuous range. Decimal suffixes and separate occurrences with repeated wording survive unchanged.

The exact staged Bukhari blob is `a1cae430a684f806a0f46be5943971299e22f75e`; the observed inventory blob is `b647bafa25f312d687df79f6611d9f7af2420150`. Both complete input files were checked against their Git blob identities.

## Actual reading coverage

The single-model reviewer was GPT-6 Astra Pro. Independent Pro QC was not performed. No translation was generated; no independent authenticity, translation-accuracy, character or diacritic certification is asserted.

All 300 Arabic fields and all 300 English fields were read for attribution, report type and narration boundaries. The first ten records—`4`, `11`, `32`, `45`, `51`, `57`, `58`, `59`, `60`, `67`—were also read in Hindi, Urdu and Roman Urdu. Arabic fields after these first ten were semantically read in a viewing copy with diacritics, tatweel and RTL marks hidden. All offsets, hashes and selected text refer to the unchanged original Unicode fields.

| Language | Available fields | Fields actually read | Fields with selected narration | Unread fields |
| --- | ---: | ---: | ---: | ---: |
| Arabic | 300 | 300 | 297 | 0 |
| English | 300 | 300 | 299 | 0 |
| Hindi | 300 | 10 | 9 | 290 |
| Urdu | 300 | 10 | 9 | 290 |
| Roman Urdu | 300 | 10 | 9 | 290 |
| Total | 1,500 | 630 | 623 | 870 |

The original 1,500 fields contain 826,157 Unicode code points. Actual semantic reading covers 298,723 code points. The selected passages contain 291,540 code points; complete retained source context accounts for the other 534,617. Those totals are distinct from an independent exact-character reading certification.

There are 536 whole-field selections and 87 excerpt selections, comprising 679 exact spans and 678 language-specific report components. These are components within the same 300 provider occurrences, not additional occurrence identities. Nine records have selected text in all five languages; ten records received actual all-five-field reading. No missing sibling decision implies approval.

## Attribution and boundaries

Explicit Prophetic actions, descriptions, prayers, dhikr, dialogue, and abbreviated transmissions qualify alongside speech. Companion, Successor and historical reports use their actual speakers and report types. A Companion statement is not converted to a Prophetic quotation. Source-local numbering remains source-local; external canonical identities are null unless independently supported elsewhere.

The principal retained uncertainties are:

- Bukhari `4`: the English field explicitly names the Prophet as the quoted speaker. Arabic, Hindi, Urdu and Roman Urdu leave the first-person speaker insufficiently explicit in the supplied fields and remain complete reviewed-but-uncertain source context.
- Bukhari `834`: the Arabic invocation contains literal replacement characters. It remains context without a fabricated emendation; English is independently selected.
- Bukhari `1132.2`: the Arabic abbreviated field has an unnamed subject and remains uncertain. English explicitly identifies the Prophet and is independently selected.
- Bukhari `486`: English supplies only a direction to consult another translation. It is reviewed source context, not an invented English quotation. The Arabic report is selected independently.

Bukhari `848` contains two supported practices: Ibn Umar's and al-Qasim's. These are separate selected components. The subsequent claimed Prophetic prohibition and the source's attached criticism that it is not sound/incorrect remain together in full same-language context. The review does not supply its own authenticity grade.

Bukhari `1114` contains a confirmed Arabic/English content difference: Arabic says the companions prayed sitting; English says they prayed standing. Both original fields were read and retained as distinct supplied readings. Only these two actually inspected fields carry `source_content_mismatch.confirmed=true`. Unread languages are never labelled mismatches.

Bukhari `1037` and `1155` retain the actual attribution scope in each field. English's explicit attribution is not silently copied into Arabic. Poetry within `1008`, `1009` and `1155` retains its named poet rather than becoming the Prophet's authored verse.

On a second reading of appended passages, actual reports and explicit abbreviated variants were retained as separate components in records such as `104`, `119`, `192`, `218`, `263`, `473`, `482`, `530`, `569` and `922`. Pure compiler corroboration, explanatory tails, editorial cross-references and specifically bounded asides remain source context. Separately narrated components in `365`, `572`, `665`, `668`, `974`, `1051`, `1065`, `1066`, `1077` and `1090` have distinct component IDs and attribution. Integrated source translation wording and lexical clarifications remain where part of a coherent narrative; a whole selected passage is not asserted to be a verbatim speech by a single person.

## Source-byte and adapter validation

All 600 immutable source files for this cohort were downloaded from the pinned GitHub commit, not from Deen Hindi:

- 300 parsed JSON gzip files: 798,693 compressed bytes; 1,868,022 decompressed bytes.
- 300 raw HTML gzip snapshots: 4,955,013 compressed bytes; 27,122,398 decompressed bytes.

For every file, the fetched Git blob identity and the applicable compressed/decompressed SHA-256 were checked. Every parsed file is byte-identical to the reconstructed original saved source object. Every raw HTML snapshot was parsed again using the unchanged pinned importer, reproducing all 1,500 language fields and all 300 literal source citations exactly. A single GitHub transport disconnect was resolved by a bounded read retry after retaining all verified progress. No Deen Hindi request, historical error retry, workflow dispatch or remote mutation occurred.

The structural validator checks all identities, source hashes, own-field hashes, exact selected-span hashes and original-field partitions. Each source field is completely accounted for by selected passages plus preserved context with no gaps, overlaps or changes. The critical uncertainty, variant, criticism and mismatch cases above have explicit assertions.

The shared `web_source_reviews.py` adapter was exercised on all 300 `canonical_record(saved)` rows. All 1,500 source fields retain exact selected/context partitions. Original saved objects, canonical input rows and baselines remain unchanged. Component grouping and actual speaker/type classifications survive. Unreviewed primary Hindi remains null as narration text while its full original field stays in visible context. The adapter preserves the two verified mismatch flags and does not claim certification.

The detailed artifacts are the coverage, structural validation, adapter validation and 600-file evidence validation JSON files beside this log. Raw verified source bytes are retained locally under the isolated `evidence/` directory; they already exist at the immutable repository paths and do not need duplicate publication.

## Continuing work

This first pass is frozen before supplemental language review. Additional Urdu and Hindi decisions must be recorded separately and merged only as explicit field replacements bound to these same source objects and this frozen review hash. Roman Urdu outside the first ten remains unread unless a later actual reading pass is recorded.

The acquisition worker is independent of this classification batch. The latest separately observed checkpoint is commit `1357582cbf9d65c3df8cbe7bf9be84c9060197f7`, updated at 2026-11-13 06:38:54 UTC: 10,965 fetched, 7,275 registered, 3,690 classification-pending, 24,425 pending fetch and 1,000 historical errors. It is unblocked. Run `43380588603`, job `131737210386`, was actively processing bounded batches after the previous run succeeded. Integration must retain this concurrent acquisition work and must not dispatch a duplicate worker.

The separate acquisition/recovery audit checks the original 1,000 HTTP-200 no-payload errors. None overlaps a successful imported identity or carries a parsed source path in the pinned checkpoint. Seven saved failed responses, one per collection, were downloaded from GitHub and verified as soft-verification pages without extractable hadith payload. No recoverable Hindi payload was identified in those checkpoint records; this is not an exhaustive claim about unrelated public archives. The independently cited Fawaz catalog has no Hindi edition and cannot fill missing Hindi or establish Deen identity merely through matching numbers.
