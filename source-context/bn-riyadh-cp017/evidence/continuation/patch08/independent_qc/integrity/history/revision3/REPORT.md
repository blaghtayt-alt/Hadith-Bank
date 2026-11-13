# Patch08 independent engineering and integrity QC

**Result: pass_with_explicit_scope_limits.** Candidate revision 3.

## Audited findings

- source_stories: 18
- source_utf16_units_including_controls: 2296570
- records.csv_rows: 2029
- records: 2029
- old_record_fields_compared: 153528
- source_units: 11484
- parent_semantic_rows: 26567
- new_semantic_rows: 16850
- cumulative_semantic_rows: 43417
- active_semantic_rows: 41875
- unique_semantic_IDs: 43409
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
- atomic_source_segments: 55434
- new_source_mapping_rows: 17337

## Method and evidence

The audit script is independent of the build script and reads the candidate, authenticated parent, source story exports, exact CP spans, current state indexes, before/after corrections, mappings, export formats, and referenced evidence bytes. It does not modify the candidate. All consumed inputs are bound in reviewed_inputs.json.

Checked 124 categories with 2,609,635 assertion evaluations.

## Findings requiring correction

No failing integrity checks remained for these exact reviewed input bytes.

## Limits and retained uncertainty

- Engineering/integrity verification only. No image or text was manually reread by this audit, and no manual textual QC or whole-book certification is claimed.
- The audited object is the logical cumulative package: candidate stage overrides authenticated parent paths; new continuation/patch08 evidence resolves to frozen author evidence when absent from the stage. Final assembled archive member preservation requires a packaging check.
- The parent archive authentication record is inherited. Every parent input actually consumed by this audit is independently checked against the authenticated member index; this run does not reassemble or reauthenticate all archive chunks.
- Current leaf selection follows the candidate’s documented narrowest-active-span policy. Exact joins and inactivity are tested, but engineering checks cannot certify the semantic meaning of a selected role or intended speaker.
- All source-limited ambiguities remain unresolved; exact interval coverage does not convert them into resolved semantic claims.
- Evidence hash verification establishes identity and availability, not whether the claimed human/model image observation occurred.
- No GitHub writes, Library upload, publication, canonical reconciliation, deduplication, or bank ingestion is performed.

## Reproduction

Run audit_patch08.py with --parent, --stage, --manifest, --evidence-root and a separate --out directory. The script exits nonzero if an integrity check fails. A status-only or packaging change must be bound in a final delta manifest and checked before release.
