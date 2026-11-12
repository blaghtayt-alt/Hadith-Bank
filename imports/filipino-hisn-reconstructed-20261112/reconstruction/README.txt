FIL_HISN_RECONSTRUCTED_v2_HOLD_20261112T081653Z_8043d352
FILIPINO | HISN AL-MUSLIM | NEW RECONSTRUCTED v2 | HOLD

PROVENANCE
This is a new reconstruction from the exact attached v1 archive and the
substantive instructions/report reproduced by the user. It is NOT recovery of
the original v2 ZIP and is NOT byte-identical to that missing artifact.
The original chat and standalone Pasted text.txt were not accessed.

STATUS
Source fidelity: PARTIAL. Metadata: PARTIAL. Bank: FAIL/HOLD.
Release-approved records: 0. Separate independent final evaluation: NOT_RUN.
No repository change, integration, publication, or other-chat contact occurred.
The coauthors helped construct this output; they are not its independent final
evaluators. Mechanical PASS is not semantic, authenticity or release approval.

CONTENTS
data/corrected_all_records.json: complete323 records and1500 components.
data/corrected_all_records.jsonl and .csv: lossless complete-record exports.
data/records_export_envelope.json: top-level JSON metadata for exact round trips.
data/components.jsonl and .csv: all original component objects, unchanged.
data/book_metadata.json: inherited metadata plus reconstruction status.
partitions/*_HOLD.json: four disjoint complete-record context partitions.
audit/replayable_patch.json: RFC6902 patch from exact v1 data to this data.
audit/full_before_after_correction_log.jsonl: exact325 mutation records.
audit/classification_before_after_decisions.jsonl: old versus active decisions.
audit/unresolved_exceptions.json/.jsonl/.csv: all230 original exceptions and scopes.
audit/record_blocker_index.json: all323 record scopes and separate package gate.
coverage/: actual targeted visual work and inherited historical coverage.
validation/: mechanical and delivered-script verification results.
provenance/: input identities and preserved archive-member hashes.
coauthor_work/: targeted evidence, decisions and actual inspection logs.
SHA256_MANIFEST.json: exact sizes/hashes of every other packaged file.

CURRENT ROUTING
Use records[*].content_classification_reconstructed_v2.
Do not treat the unchanged content_classification_final_pro or v5 annotations as
the current decision; those fields are preserved historical evidence. Original
kind fields, source values, reference claims and hashes also remain unchanged.

The298 hadith/dhikr/context records are source-context associations, NOT298
verified Prophetic matns or unique narrations. Quran and its renderings remain
Quran; compiler instructions remain commentary/instructions; other speakers are
identified; variants and exact-occurrence limitations remain. Retained external
evidence never replaces or supplements the PDF-verbatim source fields.
There are14 independent non-Prophetic,6 Quran/author-only and5 unresolved records.
All493 inherited candidate COMPONENTS remain, with zero new candidate promotions.
Candidate classification and record context grouping do not authorize release.

ORIGINALS
preserved_inputs/FIL_HISN_FINAL_PRO_REVIEW_20261112_HOLD_v1.zip is the original
384,986,021-byte archive, unchanged. It preserves the original PDF, exact v5 ZIP,
all preceding versions, images, source fields, audits and evidence as supplied.
Extract it to a directory called v1_extracted to resolve its member paths.
Paths in old files keep their historical bindings. In v1, prior_package/ refers
to extraction of inputs/FIL_HISN_QC_v5_REVIEW_PACKAGE.zip, not to a new download.

REPRODUCE
After extracting v1, run the delivered apply_reconstruction_patch.py with the
original data/corrected_all_records.json, audit/replayable_patch.json, and a new
output path. The result exactly reproduces the corrected JSON bytes.
The same script applies audit/book_metadata_replayable_patch.json to original
book_metadata.json. export_reconstructed_data.py reproduces JSONL, CSV, envelope
and four partitions from corrected JSON. --help describes each interface.
The session builder is preserved as a construction log; the two replay/export
scripts are the portable reproduction interfaces.

VALIDATE
python3 scripts/validate_reconstructed_package.py --root . --read-only
Read-only mode checks data and the final manifest without rewriting artifacts.
The original construction validation has5,941 checks and no failures;14 further
checks execute the delivered replay/export scripts and compare exact bytes.
Final manifest validation and outer ZIP identity are recorded in the standalone
delivery manifest created after packaging. Checks are not forced to lost-v2's474.

CSV WARNING ABOUT FORMAT
record_json/component_json cells preserve complete nested data and may exceed
spreadsheet cell-size limits. Use a CSV/JSON parser for lossless processing.
No spreadsheet truncation is an acceptable substitute for these exports.

See FINAL_RECONSTRUCTION_REPORT.txt for decisions, differences and unresolved IDs.
