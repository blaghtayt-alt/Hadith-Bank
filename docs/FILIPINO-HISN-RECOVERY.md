# Filipino Hisn final v2: transfer recovery and integration contract

## Actual status

The owner requested continuing the interrupted upload on 12 November 2026 and
changing the approach that had repeatedly exhausted the conversation or returned
an unknown error. This change supplies a bounded, resumable transfer utility. It
does **not** register Filipino v2 records or report that their upload succeeded.

At the inspected main commit `7d3c7312389bfc9d21bafb1b490ac2ca99c40ac9`, there is
no Filipino final-v2 material registration. The existing
`materials/quran-excerpts-fil-hisn-al-muslim/` is a different older source and must
remain unchanged. A successful earlier blob upload without a recorded object
SHA or a reachable tree cannot establish that the final package is available.

The accessible saved files contain final **v1**, not the required final **v2**.
The original v2 scratch link was recovered from the source conversation, but its
workspace is unavailable to this continuation. No v2 source bytes were inspected
in this recovery. Do not substitute final v1 or the unrelated older `QC_v2`
generation, and do not reconstruct corrected source text or classifications
from a conversation summary.

| Identity | Expected value from the prior checkpoint |
| --- | --- |
| Exact final package | `FIL_HISN_FINAL_PRO_REVIEW_20261112_HOLD_v2.zip` |
| ZIP bytes | `415468251` |
| ZIP SHA-256 | `f5681984775bc18fd5ceaca6ea15477f8b05d94686b65b62bab7ef7373ba7e05` |
| Source PDF | `FIL-HISN-PRIVATE.pdf` |
| PDF bytes | `5321887` |
| PDF SHA-256 | `3e409dd7266c2a150645ecfea548f266edf80c9c5df5129aa8df7a977d248a07` |
| Reported complete record count | `323` (not reverified here) |
| Reported hadith/dhikr-context partition | `295` (not reverified here) |
| Reported other partitions | `15` independent, `8` Quran/author-only, `5` attribution-unresolved (not reverified here) |
| Source review | `HOLD`; further separate independent final check pending |

The previous 474 mechanical checks and 16 reopened images belong to the prior
review checkpoint. They are not new checks performed by the recovery utility.

## Recover the minimum exact originals first

The standalone source and audit files can be delivered directly, without a
duplicate 415 MB ZIP or the old page-image tree. The v2 delivery listed:

- `README.md`
- `corrected_all_records.json`, `.jsonl`, `.csv`
- `hisn_hadith_dhikr_context_HOLD.json`
- `independent_non_prophetic_HOLD.json`
- `quran_and_author_only_HOLD.json`
- `attribution_unresolved_HOLD.json`
- `book_metadata.json`
- `full_before_after_correction_log.jsonl`
- `unresolved_exceptions.csv`
- `record_blocker_index.json`
- `validation_report.json`
- `output_sha256.json`

Retain their actual v2 paths and bytes when recovered. Read `output_sha256.json`
to identify and verify every required dependency; this list of displayed files
does not prove that it includes the complete classification/annotation dependency
closure. The separate original PDF was recovered in this continuation and its
`5321887` bytes match the SHA-256 above. This is a byte-integrity check only;
no new page rendering or visual review was performed.

The immediate unblock is the exact v2 data/audit delivery, or the exact original
v2 ZIP when standalone files are unavailable. The source images do not need to
be rendered again. A checksum list without the corresponding files does not
restore their contents.

## Bounded transfer fallback

Prefer authenticated Git or direct file transfer when available. Use
`scripts/package_review_transfer.py` only when a limited transport requires
small resumable parts. It operates on an explicitly supplied, hash-checked ZIP
and an explicit member selection; it never chooses records or interprets a
review verdict.

Inspect the real ZIP member inventory locally. Write the exact selected member
names to the selection file required by the utility. Select canonical source
data, audit dependencies, metadata and the original PDF; do not select page
renders or nested historical archives merely to make a standalone-file import
depend on them. The whole input ZIP hash is verified before packaging. File and
part hashes bind the selected originals to the transport manifest.

`selection.json` is a JSON array of exact ZIP member names. Once the real v2
ZIP and the explicit selection are available, the bounded commands are:

```console
python scripts/package_review_transfer.py pack --archive /path/to/FIL_HISN_FINAL_PRO_REVIEW_20261112_HOLD_v2.zip --expected-sha256 f5681984775bc18fd5ceaca6ea15477f8b05d94686b65b62bab7ef7373ba7e05 --selection /path/to/selection.json --output .work/fil-hisn-transfer
python scripts/package_review_transfer.py verify --input .work/fil-hisn-transfer --expected-sha256 f5681984775bc18fd5ceaca6ea15477f8b05d94686b65b62bab7ef7373ba7e05
python scripts/package_review_transfer.py reassemble --input .work/fil-hisn-transfer --output .work/fil-hisn-restored --expected-sha256 f5681984775bc18fd5ceaca6ea15477f8b05d94686b65b62bab7ef7373ba7e05
```

These commands are a preparation recipe, not a record that the unavailable v2
package has already been processed. The default transport part limit is 256 KiB.
Retain the `manifest_sha256` from the successful pack result independently of
the transferred parts. At the receiving end, pass it with
`--expected-manifest-sha256` to both `verify` and `reassemble`. The archive-hash
argument checks the recorded package identity; the trusted manifest hash binds
the selected-file hashes and part map themselves. Self-consistent untrusted
metadata is not proof that the received bytes belong to the expected source.

Keep transport parts and checkpoints under `.work/` or outside the checkout.
Pass bytes between tools programmatically without printing file bodies or
Base64. On an uncertain upload, check the existing part/blob against the manifest
before retrying it. A matching completed part can be reused. A corrupted part
must fail validation; it must not be silently accepted as a completed transfer.

Verify and restore all selected originals before source registration. Transport
verification establishes byte fidelity only; it does not check classifications,
Arabic glyphs, provenance or narrational authenticity. The utility performs no
network request, repository mutation, source correction or review approval.

After exact source registration, publish canonical source files and changed code
in one tree based on the current repository head. The normal
`.github/workflows/reader-pages.yml` rebuilds catalog/search/reader outputs.
Do not send all generated mirrors through the transfer channel. Preserve
concurrent changes using a normal fast-forward or an expected-head ref update.

## Required integration once the bytes are available

1. Verify final-v2 hashes, parse the real data and audit structures, and reconcile
   all 323 source IDs. Verify partition membership and exact source fields.
   Preserve v1's 17 number observations, 22 page-map corrections, p106 heading
   and N260's three synchronized text fields using the actual correction
   evidence, not reported counts alone.
2. Create a distinct Filipino `records-v1` material. Put only the approved-for-
   visibility 295 hadith/dhikr-context rows in its registered record file. Keep
   all 323 originals and the 28 other records in separate source/audit artifacts.
   Current `material_registry.py` registers every row in a material record file;
   arbitrary `show_in_html_hadith=false` and `HOLD` fields do not filter it.
3. Keep Prophetic dhikr, narrated actions, dialogue, attribution and hadith-bearing
   notes attached to their source context. Preserve Quran passages and author
   commentary with distinct annotations. Do not convert source-local Hisn item
   numbers into canonical collection numbers or invent missing English.
4. Keep `HOLD`, the pending independent final check and
   `certified_release_eligible=false`. Record the owner's requested visibility
   as `owner_requested_public_pending_review` separately. Preserve historical
   review, rights and AI-origin evidence; apply current display policy without
   rewriting the original records.
5. Put `records.path` and `source.path` inside the new material's own directory.
   The current material validator requires both to use that prefix. An already
   verified Git blob may be reused at a second tree path when its exact bytes
   match; a source path into another material is rejected.
6. Preserve blockers in `review.issues` and audit/source pointers in
   `source_locator`, since those fields survive current reader projection.
   Keep rich original annotations in the immutable source delivery as well.

## New HTML framework compatibility

The inspected framework is draft [PR #6](https://github.com/blaghtayt-alt/Hadith-Bank/pull/6),
head `838b1efa119ed312d1615826a93eb143b510c0d3`, branch
`feature/multilingual-web-imports-20261112`. It adds optional `language_versions`
while retaining existing `text.arabic` and `text.translation` compatibility.
Check its actual current state again before integration.

Preserve compatibility text and add source-bound versions for each supplied
language, with stable version IDs, exact text, own source name, own references,
notes and translation provenance. Use `match_status: "same_source_record"` only
for the actual same source record. Identical compatibility text allows the new
renderer to avoid duplicate panels. Source numbers alone do not authorize
linking another edition or language.

Language-version comments should carry their exact note in `text`, plus a
source URL or precise locator. Rich arbitrary comment objects without `text`
can validate but render blank in the inspected UI. Main currently keeps
`language_versions` in canonical source files but does not project those fields
into the reader. Do not claim the new collapsible language panels are live until
that framework is actually merged, built and verified.

No final-v2 text review, independent Pro check, material publication or UI
verification is claimed by this recovery change.
