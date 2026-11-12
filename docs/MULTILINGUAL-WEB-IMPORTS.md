# Multilingual website imports

The owner authorized importing Deen Hindi, Rivoyat and Hadis.islom.uz on
12 November 2026, including source-specific references, comments, collapsible
language panels and language/book/collection filters. Current repository intake
totals are in [web-import-status.json](../imports/web-import-status.json).
These count preserved source occurrences, not unique canonical hadiths.

## Reading framework

A source occurrence can contain several supplied language versions. Arabic,
English and the primary source language open first. Each version has its own
exact text, publisher/record link, references, translation attribution, and
nested comments. Missing source text remains absent; no translations or Arabic
originals are generated.

Language filters match all stored readings, including approved counterparts.
Uzbek Latin, Uzbek Cyrillic and Roman Urdu retain their script codes.
Base-language filters include their script variants. Book, collection, source
edition and translation-origin filters continue to work. Commentary is not
included in ordinary narration keyword searches unless explicitly requested.

The additive [language-version schema](../schemas/language-version.schema.json)
keeps existing materials compatible:

| Field | Meaning |
| --- | --- |
| id | Stable source-bound version identity |
| language, script | Supplied language/script |
| text | Exact source text |
| source | This version's publisher, record URL and scoped upstream credits |
| references | Literal citation and explicitly scoped source numbering |
| comments | Separately bounded notes and their source locators |
| translation_provenance | Original evidence, separate from current display policy |
| scope, match_status | Source entry or independently supported language relationship |

Different source occurrences, editions, chains and translation versions remain
separate. Matching numbers or similar text do not establish identity. Website
About-page credits remain site-level credits; they do not prove an exact
upstream source for every translation. A specific supplied upstream citation
stays with its own language.

## Adapters and source preservation

| Website | Acquisition route | Discovery |
| --- | --- | --- |
| [Deen Hindi](https://deenhindi.com/hadith) | Ordinary public HTML with embedded structured source objects | Seven observed collection inventories; preserve their actual identifiers and suffixes |
| [Rivoyat](https://rivoyat.com/) | Public catalogue, book/section pagination and exact language copy payloads | 26 observed catalogue collections |
| [Hadis.islom.uz](https://hadis.islom.uz/) | Public collection/section HTML and Arabic/Uzbek columns | 11 observed catalogue collections |

Robots evidence and public-page responses are preserved. No private API, login
or access-block workaround is used. Exact original responses are compressed
losslessly with deterministic gzip. Both stored-byte and original-response
SHA256 values are recorded. Parsed objects and full mixed-content ledgers remain
distinct from the reader subset.

Material supporting_files descriptors explicitly register these local originals
and ledgers. Missing/corrupt bytes, conflicting identities and record counts
fail validation. Canonical material files split into bounded parts before
individual Git files become too large; source occurrence IDs remain unchanged.

Source pages can contain introductions, Quran quotations, explanatory prose,
independent sayings, abbreviated hadiths and further narrations inside comments.
Bounded source-declared hadiths and Prophetic actions, dhikr and dialogue are
eligible without requiring a literal speech marker. Unresolved boundaries or
attribution remain in the full intake ledger outside Hadith HTML. Held content
is not discarded or described as fully imported.

The owner's source-import authorization controls publication visibility.
Historical review/AI-origin fields and source reuse qualifications remain intact.
The existing Human default for new nonlegacy sources applies unless their own
source explicitly states otherwise. This display policy does not establish a
missing translator, independent certification or a new publisher license.
Arabic receives no translation-origin label; digital HTML extraction receives
no OCR badge.

## Bounded continuation

[import-web-hadith.yml](../.github/workflows/import-web-hadith.yml) resumes the
finite queues hourly. The first acquisition batch is capped at five minutes per
host; later batches use the source-specific request/delay/time budgets in
[web-import-plan.json](../catalog/web-import-plan.json). Each host is sequential;
independent hosts can run concurrently.

Successful validation commits source evidence and checkpoints before dispatching
the normal website build. A stopped or blocked worker still saves its valid
checkpoint. Unexpected worker failures are persisted in
[web-import-worker-stops.json](../imports/web-import-worker-stops.json) and
require inspection before explicit removal. Saved authentication/rate/robots
blocks are never automatically retried. Failed jobs retain recovery artifacts.

Each worker now saves a separate result receipt as it finishes. Status and stop
files use atomic replacement, so an interrupted write cannot leave half a JSON
checkpoint. A failed worker does not discard the other hosts' completed results.
Hard process timeouts remain stopped for inspection; reaching the importer's
normal time budget leaves a resumable queue.

Every workflow outcome retains a small diagnostic artifact, including successful
runs with blocked or stopped sources. It contains worker logs/results, the logged
test and batch commands, run/attempt IDs, the checked-out commit, and the
available checkpoint. The job summary distinguishes batch and save outcomes;
counts from a failed save do not establish repository publication. Failed or
canceled jobs additionally retain acquired source evidence for recovery.
Website build dispatch is a separate step after saving the checkpoint, and it
also runs when the source files are unchanged. If a source push succeeds but
the build request fails, the next run retries that request before it can pause
the schedule. A completed source save and a completed website deployment remain
separate outcomes.

Completed pages are not refreshed. The workflow disables its schedule when all
fetch queues are complete or when no enabled source can continue. A paused,
blocked or failed queue is never labelled complete. Inspect the retained cause,
repair the affected checkpoint/code if needed, and re-enable the workflow to
resume the already authorized intake. The plan's global or per-source enabled
field can pause further intake. A newly authorized source requires an explicit
plan update.

The public material registry also rejects canonical rows explicitly marked
`show_in_html_hadith=false`. Keep those rows in original source or supporting
evidence outside the registered reader subset; registration cannot silently
strip their hold marker or change the declared record counts.

Commands:

    python scripts/web_import_batch.py --root .
    python scripts/web_import_batch.py --root . --status-only
    python scripts/import_deenhindi.py --root . --max-records 100 --max-seconds 600 --delay-seconds 1.25
    python scripts/import_uzbek_web.py --root . --site rivoyat --max-pages 100 --max-seconds 600 --delay 1.25
    python scripts/import_uzbek_web.py --root . --site islom --max-pages 100 --max-seconds 600 --delay 1.25

Deen's remaining queue counts entry pages. Uzbek remaining queues count linked
catalogue/section pages, often containing many entries and revealing further
pagination. Do not add these together as remaining hadith counts. Queue
completion still leaves held classifications and completeness to reconcile.

## Large-corpus delivery

New web editions use normal language/book/edition indexes and exact
?occurrence=stable-id links into the shared reader. Existing static occurrence
URLs remain available. This avoids duplicating full HTML pages for hundreds of
thousands of new records.

The hosted reader loads ordered gzip shards with byte counts, SHA256 and record
counts. The self-contained reader remains available while it fits the repository
file budget; oversized output becomes a reader plus its complete data directory.
A shell by itself is not described as an offline download. CLI search and
resolution continue to use checked local files without network access.
The conservative 950 MB website budget prevents an oversized build from
replacing the live site.

The browser still ultimately retains the loaded corpus and its search index in
memory. Sharding controls transfer/file size and decompression peaks; it is not
a claim of constant-memory or server-side search.

## Recovery checkpoint

The initial workspace intake obtained 4,271 source entries, of which 4,042 were
registered candidates and 229 held for boundary/attribution review. The
workspace became unavailable before those snapshots were committed. These are
historical execution counts, not current published repository totals.

Importer/UI code was recovered from retained tool-call patches. The Uzbek
importer matched its recorded pre-failure SHA256 exactly. Other recovered code
requires a fresh CI run. No original hadith text, original snapshot hash, or
manual source-bound override was reconstructed from memory. Fresh publication
counts must come from real reacquisition and checked source bytes. See
[Uzbek recovery](UZBEK-WEB-IMPORT-RECOVERY.md) and
[Deen intake operations](../imports/web-deenhindi-20261112/README.md).
