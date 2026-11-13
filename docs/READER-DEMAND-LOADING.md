# Reader loading and source preservation

## Problem and scope

The published v1 reader loaded every complete record before displaying a page
or applying an exact-occurrence link. The saved baseline at
`a625c374d83b6fa878c40c8d2093b43dca209090` contains 88,015 occurrences,
798 compressed detail parts, 139,641,145 compressed bytes and 1,659,791,315
decoded JSONL bytes. Its compact full-record stream SHA-256 is
`017bdd42930d1d075662306507a08d9c58402b5668a2e9bc4e8fddaad0695874`.
Those bytes were downloaded and individually verified for the full-size repair
test. This diagnosis is an excessive eager workload, not an observed browser
out-of-memory exception or a GitHub rate-limit response.

The repair changes delivery and rendering. It does not reclassify, translate,
delete or merge source records. The completed Fawaz import remains 36,220
registered identities and 244 preserved source-only identities. Its separate
6,112 unread sibling-language fields remain source context; this software work
does not complete their semantic review.

## Hosted v2 delivery

`scripts/build_reader.py` produces a small occurrence directory and separate
primary-search, annotation-search and full-detail stores. Full-detail
serialization and chunk boundaries retain the v1 byte stream. The JavaScript
projector uses the reader's existing normalization and filter functions, so
numeric conversion, Unicode behavior, citation scopes and commentary exclusions
are shared with the existing reader.

`reader/lazy-store.js` verifies and freezes the directory, then hydrates only the
visible page or explicitly selected downloads. An exact occurrence or a
canonical citation can be resolved from directory metadata without scanning
all narration text. Text searches scan only relevant bounded parts; commentary
is separate and opt-in. A cancelled or incomplete scan cannot become a complete
zero-result search. View generations prevent older requests from overwriting a
newer query or page.

The decoded-part LRU is capped at 8 MiB and the transport allows at most four
active requests. This is a cache bound, not a total browser-memory claim:
directory objects, visible records, in-flight requests and explicitly selected
download bytes also require memory. Full records and whole-bank normalized keys
are not retained in the cache. Collapsed record audits serialize their full JSON
only when opened.

Each full-record locator is a global UTF-8 byte offset and length. Records and
characters may cross detail chunks. Hydration verifies compressed hashes,
compressed and decoded lengths, strict UTF-8, the complete JSONL record and all
five occurrence identity fields. Source objects, unknown values and null fields
remain intact. All data URLs are safe local paths on the same origin.

The original canonical input hash remains `snapshot.records_sha256`. The compact
detail serialization hash is separately stored in
`snapshot.data_delivery.jsonl_sha256` and the v2 manifest. These can differ when
the original JSONL contains different formatting; text and full-object
preservation are checked independently. A search-index hash never substitutes
for the full-detail hash.

## Publication and recovery

New content-addressed parts are prepared before publication. HTML and manifest
replacement retain the previous playable files on failure. Obsolete generated
parts are removed only when their paths and SHA-256 match the prior manifest;
edited or unrelated files are preserved. Subprocess input, output and bounded
diagnostics drain independently, and failed projection children are terminated
and reaped.

The existing reader workflow keeps its expected-head guards and preserves
concurrent source imports. Large generated outputs are rebuilt in Actions.
Only source code and compact evidence are transferred by the assistant.
Standalone embedded readers and the legacy v1 loader remain supported.

## Verification

The focused suites exercise real producer/runtime search parity, complete
object preservation, Unicode chunk boundaries, corruption, cancellation,
request deduplication, timeouts, cache bounds, atomic publication and rollback.
Legacy filter tests keep their original assertions and initialize the new
asynchronous lifecycle explicitly.

```sh
python -m unittest discover -s tests
node --test tests/test_lazy_store.js
python scripts/verify_reader_browser.py --site-root _site \
  --report .work/reader-browser-smoke.json
```

The browser smoke script creates explicitly labelled synthetic TEST records,
checks selective startup, pagination, exact-ID and citation queries, commentary,
stale searches, exact selected JSON and the standalone offline reader. It also
checks the real built site's startup and a deep link. GitHub Actions installs
Playwright 1.62.0 and Chromium for this gate. The local execution sandbox rejected
native browser socket creation, so local Python/Node checks are not represented
as browser passes.

Publication is complete only after the exact source revision passes the full
repository gates, generated-file synchronization and Pages deployment, followed
by a live reader check. A saved branch or an uploaded blob alone is not evidence
of deployment.
