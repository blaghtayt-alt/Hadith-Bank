# Uzbek web importer recovery

The implementation at `scripts/import_uzbek_web.py` was recovered byte for byte from its authoring patches after the execution environment became unavailable. Its SHA256 matches the final script recorded before that outage:

`584e1dc7e987301f01c85a2c98526cfd353eacc32a03f28513d1a492cd3c14fb`

**This recovery contains code and documentation. It does not restore the previously acquired publisher text, HTML snapshots, records, manifests or checkpoints. Those source bytes must be retrieved again through the importer. Historical intake counts from the unavailable workspace must not be reported as published records in the recovered branch.**

## Acquisition

The importer follows public collection and section links for Rivoyat and Hadis.islom.uz. It uses ordinary public HTML, including Rivoyat's rendered copy payloads and Islom's separate Arabic/Uzbek columns. It does not query private databases, use disallowed API routes, infer canonical numbers, perform OCR or create translations.

Each HTTP response is retained as a content-addressed gzip snapshot. The saved metadata includes original and stored SHA256 values, retrieval time and URL. Compressed source-entry ledgers retain accepted and held items, exact source columns and detached commentary.

## Run

From repository root:

```sh
python scripts/import_uzbek_web.py --site rivoyat --max-pages 100 --max-seconds 600 --delay 1
python scripts/import_uzbek_web.py --site islom --max-pages 100 --max-seconds 600 --delay 1
```

Time and request budgets apply per site. An in-flight request may finish before export. Each run saves completed work and rotates between collections. Authentication, rate or robots blocks stop acquisition without an automatic workaround. Unexpected empty markup is a recorded failure, not a completed page.

Current progress is written to:

- `imports/web-uzbek-20261112/rivoyat/checkpoint.json`
- `imports/web-uzbek-20261112/rivoyat/progress.json`
- `imports/web-uzbek-20261112/islom/checkpoint.json`
- `imports/web-uzbek-20261112/islom/progress.json`

Task states are `pending`, `done`, `failed` and `blocked`. An exhausted request budget never means that a website has been completely imported.

After source acquisition, offline export is available:

```sh
python scripts/import_uzbek_web.py --site all --export-only
```

Run the normal bank refresh and validation workflow after export.

## Language and classification handling

The primary material language is `uz`. Exact Arabic, Uzbek Latin and Uzbek Cyrillic text are separate `language_versions` with their own source references, comments and provenance. No unseen language counterpart is manufactured.

Source-attributed speech, actions, dialogue, tacit approval and narrated dhikr/duas are retained. A narrow rule also handles cited abbreviated matn in the publisher-declared 101/2002 Hadith anthologies. This source-attribution decision is separate from authenticity grading. Uncited or unresolved items remain outside the reader.

Explicit source commentary boundaries create own-language `source_commentary` entries. Additional narrations quoted inside commentary have not automatically been segmented into new occurrences. Changed source text is retained as a separate held candidate; a change confined to Uzbek Cyrillic also receives a distinct identity.

The implementation preserves current source provenance separately from the owner's display policy. It does not claim a redistribution license or independent Pro review.

## Publication files and validation

Materials use `records-v1` and include `supporting_files` for their source evidence. Compressed descriptors specify `compression: gzip`, stored hash and size, plus the expanded-response or uncompressed-ledger hash. Persistent 40 MiB part assignments keep individual publication files bounded without moving earlier occurrences between parts.

`tests/test_uzbek_web_import.py` adds synthetic regression fixtures for source-byte checks, multilingual identity, variant holds, comments, empty-parser failures, citation scope, request controls and stable publication partitions. These fixtures are not hadith texts and perform no network requests. They must pass CI on the recovery branch before the importer is used there.
