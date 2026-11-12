# Uzbek web importer recovery

The original implementation at `scripts/import_uzbek_web.py` was recovered byte for byte from its authoring patches after the execution environment became unavailable. Its recovered-base SHA256 matches the final script recorded before that outage (the subsequently validated partition and metadata-queue fixes change the current script hash):

`584e1dc7e987301f01c85a2c98526cfd353eacc32a03f28513d1a492cd3c14fb`

**Code recovery alone does not restore previously acquired publisher text. Reuse verified preserved source snapshots and checkpoints when available. Only source files actually present and verified in the current checkout count as acquired; historical intake counts from the unavailable workspace must not be reported as published records in the recovered branch.** The fresh seed subsequently recovered from the surviving workspace is recorded separately from newer acquisition progress under `imports/web-seed-recovery-20261112/`. Current per-site progress and material manifests determine live counts.

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

Task states are `pending`, `done`, `failed` and `blocked`. The page queue covers catalogue and section pages; a failed robots request also receives its own durable task. An exhausted request budget never means that a website has been completely imported.

Rivoyat section extraction uses only metadata supplied in the section response. Each acquired source occurrence has a durable separate task in `imports/web-uzbek-20261112/rivoyat/detail-metadata-queue.json`, with its exact detail URL, expected source-language text hashes, original snapshot locator, and the fields still to inspect. The bounded detail worker alternates with section acquisition after catalogue discovery, shares the same HTTP/time budgets and robots policy, and saves completed work before stopping. Page coverage and detail coverage are reported separately. `detail_metadata_pending` remains explicit until the exact detail response is parsed; an empty section comments array is not evidence that the detail page has no commentary.

Before adding metadata, the parser requires the exact detail URL and byte-identical Arabic, Uzbek Latin and Uzbek Cyrillic text for every stored language version. It reads the observed `.hukm` grading/source block, keeping the publisher's grade, attributed grader, cited work, locator strings and attached notes separate by language. Original Arabic labels supplied in HTML `title` attributes are retained as labels. They are never substituted for narration text. Listed works and grade references are publisher claims, with canonical matching unverified; they do not establish the origin of the Uzbek translation. Similar-hadith suggestions are excluded from citations. Missing source names stay null. Unknown layouts or changed text require explicit source/parser review, and the prior narration remains unchanged.

The parser was checked against the two preserved public detail responses for `buxoriy/1/1` and `muslim/1/17c`. This is parser validation against those saved responses, not independent authenticity review or a claim that every possible detail-page layout is supported. Complete original responses are preserved even when a field is outside the recognized metadata blocks.

### Access stop and offline enrichment

The GitHub acquisition worker received HTTP 403 from `https://rivoyat.com/robots.txt`. That denial is an access stop, not a parser error to bypass. Automatic Rivoyat HTTP acquisition remains paused while its durable `site_access_block` or worker stop is present. The importer now records 401/403/429 and robots denials before returning, saves the error response bytes when available, and checks prior blocks **before any new HTTP request**. Transient robots/network failures are recorded separately and have a limited retry count. No change of host, proxy, credentials or user-agent is used to evade a denial.

`--export-only` performs no HTTP. It can enrich entries from already saved, checksum-verified detail snapshots while retaining the access stop, source text, occurrence IDs and remaining queue. The snapshot must be present in the checkpoint's `snapshots` map under the exact linked detail URL. Parsed details and their snapshot hashes become material supporting evidence. Retrieval timestamps that were not captured remain unknown.

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

Materials use `records-v1` and include `supporting_files` for their source evidence. Compressed descriptors specify `compression: gzip`, stored hash and size, plus the expanded-response or uncompressed-ledger hash. Persistent 40 MiB part assignments keep individual publication files bounded without moving earlier occurrences between parts. Every part owns a copy of the same checksum-verified source-evidence file in its own material directory. Later parts use a unique internal edition suffix in both manifest and records while preserving the original source edition in scope metadata. Occurrence and language-version IDs do not change when a part is created.

`tests/test_uzbek_web_import.py` covers source-byte checks, multilingual identity, variant holds, comments, empty-parser failures, citation scope, request controls, stable publication partitions, real registry validation across a forced small part cap, and explicit detail queue state. Detail regressions also verify script separation, exclusion of unrelated suggestions, preservation of missing source names, exact-text mismatch holds, idempotent offline enrichment during an access stop, export dependency closure, bounded continuation, durable robots 403 stops and distinct transient errors. Fixtures use synthetic parser tokens, not hadith texts or translations, and perform no network requests.
