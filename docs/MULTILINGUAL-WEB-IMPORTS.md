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

Each language's reference disclosure also retains literal citations that have
no parsed collection or number, source-local numbering qualifications, and
canonical-mapping status. A pending detail-page notice is shown on the affected
reading until its detailed source references and notes have actually been
retrieved. An empty comments array does not establish that the publisher has no
comments.

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

An access denial during the first robots request is a site-level block too.
The importer saves the URL, HTTP status and event before exporting its existing
local records, then checks that stop before any subsequent robots request.
The initial GitHub run's Rivoyat HTTP 403 is documented in its retained worker
stop with the verified diagnostic artifact hash. That stop remains in place;
the other two authorized sources continue independently.

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
pagination; Rivoyat also maintains a separate detail-metadata queue. The status
report separates pending page and detail requests. Do not add these together as
remaining hadith counts. Queue
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

### Recovered source checkpoint, 12 November 2026

The later fresh 836-entry seed (797 registered occurrences, 39 held entries)
was recovered and verified against both frozen file manifests: 162 files,
10,367,141 bytes, with no hash mismatches. Its exact files are preserved in
[the seed recovery archive](../imports/web-seed-recovery-20261112/manifest.json).
Concatenate the listed archive parts in order before decompressing the tar.
The archive's original paths and file bytes are preserved.

The newer automated acquisition already contained all 6 Deen Hindi and 761
Islom registered seed identities, so their newer queues were retained. The
missing 30 Rivoyat occurrences and two held entries were recovered without
adding duplicate Deen/Islom occurrences. The integrated checkpoint contains
7,301 obtained entries: 7,024 registered and 277 held. Together with the
37,201 existing bank occurrences, this checkpoint targets 44,225 occurrences;
the authoritative published total is the successful website build report.
Later acquisition runs can increase these counts.

Two previously saved Rivoyat detail responses were recovered with original and
compressed hashes intact. Their exact URLs and all three narration texts match
the section snapshots. Their source assessments, references and notes are now
attached to the corresponding language versions. All 90 stored language texts
across the 30 recovered public occurrences remain unchanged. Twenty-eight
public occurrences still have pending detailed references/notes; the complete
32-entry source ledger has 30 pending detail tasks, including the two held
entries.

The GitHub acquisition runner received HTTP 403 for Rivoyat's robots.txt in
[run 43179396269](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43179396269).
The durable access block and worker stop remain in force. Cached successful
robots evidence does not override that block. Exporting verified saved source
bytes does not make new requests to the blocked host. Deen Hindi and Islom's
finite queues remain enabled; Islom's saved transient HTTP 500 is subject to
the existing bounded retry policy.
