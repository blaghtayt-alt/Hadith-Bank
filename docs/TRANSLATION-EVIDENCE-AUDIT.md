# Evidence-bound translation-origin audit

The reader's historical Human default for new books is a display decision, not evidence about how the exact text was translated. Unknown does not mean AI. OCR, AI-assisted extraction, automatic alignment, a reviewer, a missing translator credit and prose style are not evidence that a translation was AI-produced. Retain the historical policy and source fields; never silently rewrite them based on this audit.

`scripts/audit_translation_evidence.py` can check reviewed decisions against a reader projection JSONL. It counts **primary non-Arabic translation occurrences with nonblank primary text**. Arabic originals and empty primary translations are reported as exclusions. Linked English/Arabic counterparts and other `language_versions` are not audited in this first scope; neither the resulting counts nor an absence of AI decisions describe the whole bank. Source occurrences are not unique canonical hadiths. A zero-entry ledger means no decisions were supplied, not that evidence has been researched or that no AI translations exist.

The ledger is a JSON object with schema `hadith-bank-translation-evidence-ledger-v1` and a `decisions` array. Each decision requires an `occurrence_id`, exact primary `language`, `classification` (`human` or `ai`), SHA-256 of the exact UTF-8 `text_translation`, a repository-relative `evidence_path` and its `evidence_sha256`, a precise `evidence_locator`, an `assertion` describing what the source establishes, and a `reviewer`. A reviewer must actually inspect the cited material and its relationship to the exact translation. A human translator credit can support authorship within its documented edition and scope; it does not establish the absence of all assistance or independent QC. A credible explicit generation record can support AI origin. Do not promote a publisher-wide workflow, source-wide credit, an owner default, or an unrelated translation to proof for a specific text. An unresolved or conflicting case receives no decision. Document known model, reviewer, review effort and reviewed bytes for AI-produced translations; retain explicit unknowns where missing.

Run with local, checksum-verified reader projection and evidence files:

```sh
python scripts/audit_translation_evidence.py --records path/to/reader-records.jsonl --ledger path/to/decisions.json --root .
```

The default output is compact; use `--include-ids` only when the occurrence IDs are needed. Save a report outside source files, with commit and input checksums, before comparing results. The tool fails on duplicates, unmatched decisions, changed translation or evidence bytes, missing required fields, and unsafe evidence paths. Hash verification binds a decision to the supplied bytes: it does not verify the truth, completeness, rights status, or scope of the reviewer's assertion. This tool is an audit preparation; it does not update reader labels, edit records, publish data, or independently certify a translation.
