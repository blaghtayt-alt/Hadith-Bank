# Lazy reader datastore contract (implementation not written)

This is the agreed interface, not a completed implementation. At interruption
no reader/lazy-store.js or new runtime tests had been written.

## Manifest

Top-level fields:

    schema: hadith-bank-reader-lazy-v2
    encoding: gzip-jsonl-lazy-v2
    record_count
    jsonl_sha256
    max_shard_bytes
    directory
    search
    annotations
    details

directory, search and annotations each contain:

    encoding: gzip-jsonl-shards
    record_count
    jsonl_sha256
    max_shard_bytes
    shards:
      path, sha256, bytes, uncompressed_bytes,
      count, first_ordinal, last_ordinal

These three stores contain complete JSONL rows. Ordinal ranges must be contiguous,
cover 0 through record_count minus one, and satisfy
count === last_ordinal - first_ordinal + 1.

Directory rows:

    {
      id, language, book_key, edition, source_id,
      _reader: {
        languages,
        origin,
        availability: { arabic, english },
        ocr_pending,
        citation_pairs,
        detail: [globalUTF8ByteOffset, byteLengthIncludingNewline]
      }
    }

Search and annotation rows are [ordinal, exactNormalizedKeyString], including
empty keys. The producer uses the existing JavaScript primarySearchKey and
annotationSearchKey functions. Preserve the exact JavaScript normalization,
number conversion and exclusion of boolean search scalars.

details retains the existing v1 shard schema and byte chunks and adds
plain_part_bytes. A record or UTF-8 character can cross detail chunks.
All nonfinal detail chunks must have exactly plain_part_bytes decoded bytes.
All paths are relative to the containing HTML's directory.

## Interface

Create reader/lazy-store.js as an inline-browser and Node-compatible module:

    const store = HadithLazyStore.create(
      manifest, baseURL, onProgress = () => {}, options = {}
    );

    await store.loadDirectory({ signal } = {});
    await store.getRecord(ordinal, { signal } = {});
    await store.getRecords(ordinals, { signal, concurrency } = {});
    await store.search(
      candidateOrdinals, normalizedTerms, includeCommentary,
      { signal, onProgress } = {}
    );

    store.cacheStats();

create synchronously validates the manifest. loadDirectory returns the complete
directory only after verification and reuses it thereafter. Freeze directory rows
and nested metadata so callers cannot change validated locators.

Progress:

    {
      phase: "directory" | "search" | "annotations",
      loaded, total, part, parts, complete
    }

complete becomes true only after successful completion. A failed or cancelled
operation never returns partial results.

## Memory and transport

- Keep the directory and an LRU capped at 8 MiB of decoded shard bytes across
  detail/search/annotation stores. Do not cache parsed full records or all text keys.
- Expose cache bytes, entries and concurrency through cacheStats for tests.
- Maximum four active requests globally; getRecords defaults to three workers.
- Deduplicate requests for the same shard with separate caller subscriptions.
  Abort the underlying request only when every subscriber has cancelled.
- Retain same-origin and safe-relative-path restrictions, same-origin credentials
  and redirect:error.
- Enforce compressed and decoded lengths while reading. Verify compressed SHA-256
  before decompression. Use fatal UTF-8 decoding.
- Default timeout 30 seconds; options may lower timeout/cache sizes for tests.
- Only a displayed page or explicit selected records may retain full objects.
  A record larger than the cache may be assembled from necessary parts without
  becoming an unlimited cache entry.

Validate all directory identifier strings, language arrays, origin classifications,
text/external_link/missing availability states, OCR boolean, citation pairs and
detail spans. Spans must be contiguous in ordinal order and cover the complete
declared full-record stream.

getRecord derives necessary part indices from the byte span and plain_part_bytes,
joins exact byte slices, requires one complete JSONL record, and verifies id,
language, book_key, edition and source_id against the directory. Never hydrate
a summary projection as though it were a full record.

## Search

Root's template prefilters by language, book, source, origin, counterpart availability,
exact occurrence and canonical citation pairs. The datastore then:

1. Validates candidate ordinals, removes duplicates and preserves their order.
2. Cancels any older search.
3. Returns candidates immediately for empty terms without fetching text stores.
4. Skips parts whose ordinal ranges contain no candidates.
5. Parses one bounded search part at a time and releases its key strings.
6. Tracks term matches with compact per-candidate bitsets. With annotations on,
   each term may match either primary or annotation text; different terms can
   match different sections of one occurrence.
7. Scans annotation parts only for candidates with unresolved terms.
8. Returns complete ordered matches after every required part passes.

Cancellation and superseded searches reject with AbortError. Corruption,
incomplete data and timeouts are explicit errors, never complete zero matches.
Directory counts and visible result totals are distinct from unfinished scans.

## Selected JSON and UI

Snapshot selected ordinals in original source order. Hydrate and serialize each
complete record progressively. Do not substitute summaries or omit unknown fields.
Create no download on any failed or cancelled record. This avoids retaining a
second selected-object array, but the output bytes still depend on the user's
explicit selection size; do not claim all exports have an 8 MiB total memory cap.

Search and page requests need generation IDs. Cancel previous operations as soon
as new input invalidates them. Delay JSON.stringify(record, null, 2) for the
collapsed full-record audit until that disclosure opens.

An exact full source ID entered in the query field should resolve as an ID rather
than being accidentally parsed as a canonical collection citation. Keep the
existing collection-number scope exclusions for ordinary citation queries.

## Required focused tests

Use Node with fake fetch, real gzip, WebCrypto and deterministic bounded fixtures.

- Directory startup fetches no details, primary or annotation text.
- One record fetches only its intersecting chunks; concurrent callers share requests.
- Cross-part UTF-8 characters and multi-part records reconstruct exactly.
- Cache stays under its decoded-byte cap; eviction refetches only needed parts.
- Search skips irrelevant ranges and preserves candidate order.
- Terms split across primary and annotation fields match only with commentary on.
- Empty queries/candidates fetch no text parts.
- Wrong digest, compressed/decoded length, UTF-8, ordinals, counts, spans and detail
  IDs fail explicitly without partial success.
- Cancellation releases requests; newer searches reject old results and still work.
- One failed request cancels remaining work for that operation.
- Request concurrency and timeout stay bounded.
- Unsafe paths, cross-origin URLs and unsupported file-protocol operation are rejected.
- Old full-record versus new-projection query parity includes Arabic/Persian digits,
  CJK, numeric values, narrator/source fields, context-only sibling fields, and
  canonical versus provider/local numbering.
- Filtering retains exact available-language, origin-policy, counterpart text/link/
  missing and OCR-display semantics.
- Selected JSON parses to the exact selected original objects after paging,
  filter changes and cache eviction.

Whole-bank row maxima have not been measured. The proposed producer rejects
oversized whole search rows instead of truncating. Change the agreed fragment
format only if actual measurements demonstrate that need, then test cross-fragment
search semantics explicitly.

Finally verify a real-size ordinary homepage, exact Fawaz deep link, full-text
search, commentary opt-in, paging and selected download in an available browser.
The former successful publication's 793 tests do not validate this new design.
