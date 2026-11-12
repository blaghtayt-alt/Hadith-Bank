# Deen Hindi web intake

This intake uses ordinary public HTML from `https://deenhindi.com/hadith`.
It does not use OCR, authenticated endpoints, `/api/`, or `/_next/` requests.
The seven collection inventories observed during the initial investigation
contained 36,390 distinct source entry identifiers. A new run records its own
observed queue. These identifiers are not a claim that every entry has already
been downloaded, translated, classified, or independently reviewed.

## Workspace recovery

The importer and its regression tests were recovered from the conversation's
code-edit history after the execution workspace became unavailable on
12 November 2026. The original source-response snapshots and the source-bound
manual genre decision from that workspace were not recovered. They must not
be recreated or assigned old checksums. Source acquisition in the recovery
branch must make real public HTTP requests and retain the bytes actually
received. Current counts must come from the resulting `progress.json`.

## Resume

From the repository root:

```sh
python scripts/import_deenhindi.py --root . --max-records 100 --max-seconds 600 --delay-seconds 1.25
```

The importer visits books in round-robin order and skips already saved source
entries. `--max-records 0` rebuilds derived material files completely offline.
A nonblocking previous error is retried only with `--retry-errors`. HTTP 401,
403, or 429 creates a persistent block. Later runs make no network requests
while that block remains. No proxy or access-control bypass is implemented.

`progress.json` records imported, registered, staged, remaining and error
counts. `done` means every queued source entry was fetched successfully; it
does not certify the texts or approve staged classifications. `blocked` and
`requires_attention` distinguish a stop from normal remaining work.

## Evidence and exact text

- `inventory.json`: observed per-book identifiers and original-page evidence.
- `state.json`: resumable imported identifiers and saved source-object hashes.
- `raw/*.html.gz`: deterministic gzip storage of exact original HTML bytes.
- `parsed/*/*.json.gz`: complete source record objects and intake metadata.
- `classification-overrides.json`: optional source-hash-bound individual genre decisions.
- `staged/*.jsonl`: preserved unresolved/mixed items outside Hadith HTML.
- `materials/deenhindi-*/records.jsonl`: registered source occurrences.
- `materials/deenhindi-*/source-index.json`: current source-file inventory.

For compressed responses, `sha256` in snapshot metadata is the checksum of
the original response bytes; `stored_sha256` checks the gzip file. Manifest
`supporting_files[].sha256` always checks the actual stored file. The source
index is a regenerated inventory. Original response and source text bytes
remain recoverable and checksum-verifiable.

Canonical JSONL files are partitioned by their actual UTF-8 size, with a
40 MiB limit per file. The first part retains the existing material ID and
edition. Additional parts use deterministic `-part-002`, `-part-003` suffixes.
Occurrence IDs and per-language version IDs are unchanged and occur in only
one active part. Every part has its own source index and supporting-file
manifest. These are storage parts of the same source edition. Collection
coverage in `progress.json` is counted once per original collection.

All five source language fields are retained in the parsed objects. Present
fields become separate `language_versions` with their own source citation and
comments array. Empty source strings remain empty in the source object and
become `null` in the canonical main text. No missing Arabic or English is
invented. Source references use the website's own collection numbering and
are not silently promoted to another edition's canonical numbering.

The source's About page credits Fawaz Ahmed Hadith API and Sunnah.com at site
level. That credit is not evidence that a particular language's exact wording
matches a particular upstream edition. Source translation origin remains
`unknown` unless explicit evidence is available; the bank's separate current
display policy applies independently. No new translation is generated here.

## Publication and classification

The owner authorized this source import on 12 November 2026. Registration uses
`owner_requested_public_pending_review`; independent Pro certification and
rights clearance are not asserted. The site's rights notice is retained and
reuse remains unassessed.

Explicit Prophetic attribution can include narrated actions, dhikr, prayers,
and dialogue. A website book label or grade alone does not establish that an
entry is a Prophetic report. Ambiguous items stay outside the registered
reader. The initially inspected Muslim entry 1 combined introductory
commentary, Quran passages, and embedded hadith material. Mixed entries need
precise span classification. Missing Arabic or English must remain absent.
An individual classification decision must bind to the exact newly saved
source bytes; the unavailable earlier override must not be reconstructed.
