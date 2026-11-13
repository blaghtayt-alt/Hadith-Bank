# Bounded held-source evidence for ordinary acquisition runs

## Purpose and result

Ordinary Deen Hindi acquisition runs can add new held entries, but the existing small recovery artifact covers only the original 508 recovered downloads. This additive exporter produces a bounded review bundle from the worker's **actual saved local Git HEAD**. It does not download pages, rebuild derivatives, make review decisions, change queue/control state or publish repository files.

The candidate is locally validated with **seven focused offline tests** and an independent read-only code review. Live artifact production remains a workflow gate after publication of this package.

## Bundle contents and limits

Each run-attempt bundle contains `held-source-records.jsonl`, `held-state-entries.json`, `checkpoint.json`, `evidence-manifest.json`, and the selected entries' existing raw HTML and parsed JSON gzip files beneath `sources/`. It contains no canonical material export, translated text, full intake state, or unrelated source archive.

Selection is a deterministic prefix ordered by collection key and then the observed source inventory order. It is limited to **250 held records** and **32 MiB for the entire final directory**, including records, state-entry descriptors, receipts, manifests and compressed source files. The receipt reports total held, selected and remaining queue counts, the selected IDs, the next held ID, and a hash of the complete ordered held-ID list. A zero-held queue or a prefix shortened by the byte limit is a normal diagnostic result. If even the first complete record and its receipts cannot fit, the exporter fails visibly without replacing an earlier bundle.

Only selected entries receive raw/parsed verification in this exporter. The complete committed staged queue is read to establish selection and remaining counts; the bundle does not claim that omitted entries were reparsed or semantically reviewed.

## Exact checkpoint and source verification

The exporter requires the explicit saved commit SHA from `git rev-parse HEAD`. It reads that fixed commit through `git cat-file`, verifies each Git blob identity, and requires the corresponding working-tree bytes to match the committed bytes. It binds state, progress, inventory, staged files and executed verifier code with exact receipts. Dirty relevant inputs or a changed local HEAD fail the export. It performs no fetch and does not substitute `GITHUB_SHA` or the current remote branch.

This distinction matters when a successful save is already retained as an ancestor of a newer concurrent main commit, and when the existing no-change save branch legitimately retains its older checkout. The receipt says **saved local HEAD**, and makes no claim to be the latest main revision or deployed site.

For each selected entry, the existing `recover_deenhindi_artifact.checked_entry()` verifier checks source-local identity and inventory membership, source URL/status, stored and uncompressed SHA-256, byte counts where supplied, safe local paths and bounded decompression. The current HTML parser must reproduce the complete parsed source object and printed reference. The selected staged row must retain that same source object, snapshot, reference, parsed path and intake classification. Existing output markers are also bounded and checked against symlink traversal.

Only the ignored `.work/deenhindi-held-evidence/<run-id>-<attempt>/` directory is written. Replacement is atomic, clears obsolete prior output and rejects an unrecognized destination. Source files and state remain unchanged.

## Workflow behavior

The two new steps follow the existing save, reader dispatch, acquisition continuation, run summary and pause steps. Export requires a successful save and a non-cancelled job; upload requires this export step's success. Both steps use `continue-on-error: true`, so diagnostics introduce no new prerequisite for checkpoint preservation, reader dispatch or acquisition continuation. A failed current export cannot upload an older bundle.

The artifact name is `deenhindi-held-evidence-<run-id>-<attempt>`, retained for 14 days. The existing diagnostic log artifact also receives the exporter's bounded logged-task output. Existing permissions, concurrency, source request budgets, cadence, recovery handling, save/rebase guards and continuation conditions are unchanged. A structured comparison of the original and patched workflows verifies this after removing the two added diagnostic steps and their two relevant path-list additions.

## Focused checks and handoff

The seven tests use synthetic TEST pages, real isolated Git repositories, the production source verifier and the workflow's actual export command through the production logged-task wrapper. They cover stable selection and exact remaining counts, reproducible output, full-directory byte accounting, zero-held success, source corruption and parser disagreement, absent committed files, preservation of a prior diagnostic on failure, dirty state/progress, mismatched expected HEAD, and an older saved HEAD while origin/main and the triggering SHA differ. Existing state controls and source bytes remain unchanged throughout.

YAML parsing, ten Bash blocks and six embedded Python blocks also pass syntax checks. The current workflow and recovery verifier baselines were verified against GitHub at `817b1d071f59bb5a10c8921858811279c6faf776`. The recovery verifier and importer are reused without modification.

The delivery manifest lists the exporter, the additive workflow change, its focused test, validation evidence and independent assessment. This package is separate from phase 3's published source reviews and secondary-language reader repair.
