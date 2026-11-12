# Fawaz pending review — continuation interrupted before publication

Recorded 2026-11-12 17:35:10 UTC.

## Actual status

The continuation recovered the previously audited 4,429 additions, reconciled 701 later language decisions covering 462 new provider IDs, and reconstructed 55 previously specified Urdu Muslim entries. The local assembly contained 6,311 language decisions and targeted 34,857 registered provider occurrences / 1,607 held, preserving the 36,464-ID inventory. This would add 4,946 to the published 29,911 baseline.

**These are candidate figures, not a completed reader update.** The full local material export stopped with no disk space, then the execution filesystem changed. Both the original review workspaces and the new assembled candidate became inaccessible. No candidate catalog, canonical material export, full decision archive or new reader deployment was saved to GitHub in this continuation.

The durable JSON checkpoint records the exact observed hashes, software checks and unfinished gates. A hash and a count cannot recreate missing decisions. The existing public source files and earlier remote recovery inputs remain intact.

## Exact evidence preserved here

- `urd-malik18-grouped-decision.json` contains one fully recovered 381-character original source field and its reviewed boundaries. The source hash was recomputed after environment replacement and matches the original.
- `verified-reference-rechecks.json` preserves two source-number comparisons checked directly against their published references.
- `interruption-checkpoint.json` distinguishes the earlier completed in-memory audit, later assembled candidate, incomplete written export and unpublished status.

These are review inputs and recovery metadata. They do not replace the unavailable full catalog.

## Grouped report support required

A source entry can contain three reports but four selected passages when commentary interrupts one report. Use `source_report_groups` as an ordered list of span groups. Flattening it must equal `quotation_spans` exactly. `source_report_count` equals the group count. Grouped component classifications use `spans`; legacy ungrouped classifications retain `span`. Do not supply bounding envelopes as `source_report_boundaries` for grouped reports.

Validate ordering, nonempty source bounds, no overlap, complete quotation/note partition, and speaker evidence within the corresponding group. Render one report label per group and separate internal passage blocks, with an indication that intervening text remains in Comments. Notes must stay outside default hadith search.

The implementation before the environment change passed 183 Fawaz tests and 19 language-reading tests, including Python/Node Unicode parity and grouped rendering-output checks. Those implementation files and local logs are currently unavailable; rerun tests after restoring or rebuilding them. A live-browser check and independent Pro QC were not performed.

## Resume safely

Recover actual catalog bytes matching `1d467374e3d1a657370fc3234a9e3298e3b1df0c21f66332f7c3a6e9391c6cff`, or recover the audited 4,429 base plus its later input files. Do not downgrade or overwrite the published source inventory to match an incomplete recovery.

Export canonical materials, run the exact source audit with the preservation baseline, validate the written registry, then verify reader and search behavior. Refresh main and preserve concurrent Hindi work before publication. Only then report the actual registered and held counts as published.
