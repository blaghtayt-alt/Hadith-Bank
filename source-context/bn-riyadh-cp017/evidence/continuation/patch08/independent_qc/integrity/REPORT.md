# Patch08 independent engineering and integrity QC

**Result: pass_with_explicit_scope_limits.** Candidate revision 4.

## Audited findings

- source_stories: 18
- source_utf16_units_including_controls: 2296570
- records.csv_rows: 2029
- records: 2029
- old_record_fields_compared: 153528
- source_units: 11484
- parent_semantic_rows: 26567
- new_semantic_rows: 16976
- cumulative_semantic_rows: 43543
- active_semantic_rows: 41940
- unique_semantic_IDs: 43535
- inherited_duplicate_ID_groups: 8
- reference_parents_replaced: 207
- page_coverage.csv_rows: 2054
- detailed_character_reviews: 2054
- character_regions: 15106
- full_character_pages: 2053
- new_page_attempts: 10
- legacy_detailed_rechecks: 3
- partial_to_full_upgrades: 13
- semantic_ambiguities_retained: 32
- new_semantic_source_exceptions: 10
- resolved_character_exception_rows: 13
- active_source_exception_rows: 838
- positive_width_active_semantic_rows: 41939
- atomic_source_segments: 55499
- new_source_mapping_rows: 17463
- explicit_historical_code_resolver_entries: 1

## What the checks establish

1. Every parent occurrence ID, its order, and every old record field except data_version are preserved. This includes source references and grades, translation provenance, language quotations, control-bearing source segments, and null canonical fields. The JSON, JSONL, and CSV exports carry the same typed values.
2. All original DOC/PDF input hashes and all 18 raw story files match their authenticated source bytes. Global CP positions are interpreted relative to each story’s recorded start and sliced as UTF-16 code units. The complete source-unit stream reconstructs every story, including nonprinting controls and trailing units.
3. The cumulative semantic ledger retains the parent byte prefix exactly. Every newly authored semantic field is retained through integration; every new source span and nested exact-source context matches its global CP slice. All old inactive interpretations remain inactive, and the eight inherited duplicate-ID groups retain qualified SHA/ordinal references.
4. The 207 inherited reference-role replacements form complete, nonoverlapping partitions of their exact parent spans. Every additional correction prompted by semantic QC has a matching before-ledger hash, row ordinal, retained old row, complete replacement partition, and active replacement rows. No correction grants character-review credit.
5. Atomic source segments have no lost, duplicated, reordered, or overlapping source text within a source unit. All positive-width active semantic, record, and uncertainty boundaries appear as atomic edges; all positive-width active rows are represented. One unchanged zero-width inherited annotation remains in the historical/current ledger but contributes no text or coverage. Record backlinks, character overlaps, evidence mappings, and all 32 ambiguity joins agree exactly with source positions.
6. The current character view has one detailed review per original page. Counts distinguish ten newly attempted/full tail pages, three detailed rechecks of already credited legacy pages, and thirteen old partial-to-full upgrades. V1 PDF page 962 remains partial. Raw before/after evidence and older language flags remain preserved, while a separate current normalization governs the page matrix.
7. Resolved character exceptions remain in history. Only the thirteen explicitly resolved old character rows leave the active view; ten new semantic source exceptions are added. The 22 inherited semantic cases remain unresolved alongside the ten new cases, and current coverage cannot resolve them automatically.
8. New referenced evidence paths resolve to actual files, and every paired file hash checked matches those bytes. This confirms evidence identity and availability. It does not certify that a claimed image observation occurred or that a semantic judgment is correct.
9. Current summary counts are recalculated from the ledgers. Current semantic/character correction indexes, version identifiers, language metadata, and builder/parent identity point to patch08. Older optional patch07 evidence is explicitly named as inherited history.

## Method and evidence

The audit script is independent of the build script and reads the candidate, authenticated parent, source story exports, exact CP spans, current state indexes, before/after corrections, mappings, export formats, and referenced evidence bytes. It does not modify the candidate. All consumed inputs are bound in reviewed_inputs.json.

Checked 137 categories with 2,659,135 assertion evaluations.

## Findings requiring correction

No failing integrity checks remained for these exact reviewed input bytes.

## Reading current and historical data safely

Use the current semantic status index and source partitions as the current classification views. The cumulative semantic ledger and original record fields deliberately retain older interpretations and statuses. Resolve a semantic reference by its ledger SHA-256 plus 1-based row ordinal; an ID-only lookup must return every matching historical row. Multiple equal-width role labels remain visible as qualified multiple authorities. Engineering validation does not collapse them or claim that every label is synonymous.

The inherited empty annotation at cumulative row 6058 (V2 main CP117418–117418) is preserved byte for byte and retains its previous active status. It contributes no source text, atomic span, or review credit. The active-ledger row total includes it, while the positive-width active-row total excludes it.

## Limits and retained uncertainty

- Engineering/integrity verification only. No image or text was manually reread by this audit, and no manual textual QC or whole-book certification is claimed.
- The audited object is the logical cumulative package: candidate stage overrides authenticated parent paths; new continuation/patch08 evidence resolves to frozen author evidence when absent from the stage. Final assembled archive member preservation requires a packaging check.
- The parent archive authentication record is inherited. Every parent input actually consumed by this audit is independently checked against the authenticated member index; this run does not reassemble or reauthenticate all archive chunks.
- Current leaf selection follows the candidate’s documented narrowest-active-span policy. Exact joins and inactivity are tested, but engineering checks cannot certify the semantic meaning of a selected role or intended speaker.
- All source-limited ambiguities remain unresolved; exact interval coverage does not convert them into resolved semantic claims.
- Evidence hash verification establishes identity and availability, not whether the claimed human/model image observation occurred.
- Hash-qualified inherited evidence can retain its former current path. Its exact historical bytes are resolved from the authenticated parent during this audit and must be resolved through the final package member-preservation map after assembly.
- No GitHub writes, Library upload, publication, canonical reconciliation, deduplication, or bank ingestion is performed.

## Reproduction

Run audit_patch08.py with --parent, --stage, --manifest, --evidence-root and a separate --out directory. Exact argv is recorded in REPORT.json. The script exits nonzero if an integrity check fails. A status-only or packaging change must be bound in a final delta manifest and checked before release.
