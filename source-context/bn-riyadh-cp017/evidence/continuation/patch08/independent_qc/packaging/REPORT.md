# Patch08 independent packaging code review

**Result: PASS for the reviewed packaging code, after one minor diagnostic correction.** No open release-blocking code defect was found. The final real checkpoint still requires root's final input freeze, streamed export and artifact verification. This review supplies no source-text QC or bank-readiness credit.

Reviewed at 2026-11-13T07:19:00.304199+00:00. The reviewer was independent of the original packager author and applied the diagnostic correction after root expressly authorized it.

## Exact code identities

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `package_patch08_streaming.py`, initial review | 55,900 | `68857ead6b580dede1eb1077221ec715dd12818ef49e2b3617d3c876c7fa7681` |
| `package_patch08_streaming.py`, reviewed corrected code | 56,163 | `74916d992cf75f769856804a1aa56b96f26b051a9293c61c8f95b2e585d9509f` |
| `REBUILD_CHECKPOINT.py`, unchanged | 11,764 | `72dced454297b8cd9c3b5e028151f88010be3387d406280e811d98d6502bdac5` |

The exact correction is preserved in `inspect_diagnostic_fix.diff`. `REPORT.json` fingerprints the code, author evidence, parent authentication/index, focused regression and diff.

## Finding and correction

**PKG-001 — low severity, fixed.** The original `--inspect` branch constructed inventory rows without the lightweight checks used by `inventory_new()`. A raw ZIP filename could receive a passing inspection with `new_nested_archives: 0`; stage-only immutable-source checks were also skipped. `--prepare` already rejected those inputs, so this did not bypass the final freeze.

The corrected `new_archive_path()` helper at lines 399–408 applies the existing filename, canonical-path and immutable-source rules. Both `inventory_new()` and `--inspect` now call it. Inspection remains read-only and does not require a final report or create a freeze. No archive-writing, member-preservation, hash-graph, companion-selection or rebuild behavior changed.

The focused regression reproduced the old false zero, then checked rejection of a raw ZIP, a stage ZIP part, replacement of `data/all_source_paragraphs.jsonl`, and a new protected `originals/` path. It also checked that ordinary provisional inspection still passes without a final report/freeze and that freeze inventory retains its nested-archive rejection. The fixtures verify that inspection does not change their files or bytes. All six revised-behavior checks passed.

## Preservation and input safety

The pinned parent archive identity is SHA-256 `9de6f653de73a932a46a555e30bfe3817cf2fd9bfa22b4f0ded5158f12c01d85`, 2,083,816,792 archive bytes and **18,626 members**. Its indexed uncompressed member bytes total 6,268,168,687. The actual read-only inspection checked index/receipt identities, materialized membership, internal metadata identity and consistency. This reviewer did not repeat the full parent byte rehash; `--prepare` and archive streaming perform those checks.

`make_plan()` produces exactly one retained destination for each authenticated parent member. Replaced current derivatives and both old internal metadata files move beneath `prior_checkpoint_derivatives/v2_cp016_patch07/`; other parent paths remain unchanged. Every parent is hashed while streaming, every final ZIP member is reread and hashed, and the final expected bytes are compared with every preservation-map row. Duplicate paths and file/directory collisions stop packaging.

Canonical relative paths, path-component symlink checks, ordinary-file checks and Linux `O_NOFOLLOW` directory-relative reads protect source access. Protected sources/history and existing image paths cannot be overwritten by a stage replacement. Input roots cannot overlap each other, and freeze/output locations cannot overlap an input tree. Source handles are read-only; delivery destinations and files are created exclusively.

## Final input freeze and hash coverage

The freeze includes every stage file and every visible raw file outside `__pycache__`, including independent QC reports and images present when root freezes the release. Required final qualification documents and structural validation are checked, and the executing packager is bound to the frozen raw code hash. The freeze itself lives outside the input trees. Inventory and hashes are rechecked when freezing, when loading the freeze, after main archive verification and after companion creation.

The hash structure has no circular self-hashes:

- `MANIFEST.json` lists all payloads except itself and `SHA256SUMS.txt`.
- `SHA256SUMS.txt` lists all payloads and `MANIFEST.json`.
- External `PARTS_MANIFEST.json` binds both internal metadata files, the freeze digest, ordered parts, the logical complete ZIP and all companions.
- The receipt's own SHA-256 is written separately. Companion validation and overall validation are serialized before their own fingerprints are appended to later metadata.

The raw audit reports are ordinary frozen inputs. Their inclusion does not depend on putting a release receipt inside its own archive.

## Streaming, verification and companions

`SplitWriter` limits every part to **402,653,184 bytes (384 MiB)**. The main ZIP streams directly to ordered parts with ZIP64 support; no joined large ZIP is created. Verification rereads all part hashes, the logical aggregate hash and each uncompressed member's size/SHA-256 through a seekable multipart reader. Exact ZIP, manifest and checksum membership are checked.

The portable helper checks ordered parts, aggregate ZIP, metadata and every main ZIP member without extraction. Assembly occurs only with explicit `--output`, using a new temporary destination followed by rename after successful verification. `--verify-companions` checks each companion file's full hash; member-by-member companion verification occurs in the packager.

Working data selects the current cumulative records, raw source units, annotations, semantic partitions, character mappings, exception history/status and current qualification documents. The audit export includes every frozen raw evidence/QC file, selected small stage reports and preservation/checksum/freeze metadata. All companion ZIP members and standalone exports are reread for size and SHA-256 equality. Current qualification files remain present, and packaging never upgrades their source or QC conclusions.

Neither script performs network publication, repository mutation or source extraction.

## Evidence and practical limits

The original author's full synthetic suite remains honestly bound to packager hash `68857ead…`. Its reported coverage includes split-boundary seeking, ZIP64, member tampering, unsafe paths, collisions, symlinks, frozen input drift, preservation, companion hashes, verify-only behavior and tiny optional assembly. It was reviewed and not unnecessarily repeated. The corrected packager hash is supported by the focused regression in `INSPECT_PATH_POLICY_TEST_RESULTS.json` and the actual read-only inspection.

At 07:17:12 UTC, actual inspection passed with 18,626 parent members, 42 stage files and 436 raw files, including 154 independent-QC files. That was a **provisional snapshot** while root was finalizing reports, before this review was added; it is not the release inventory. Final report presence was false at that time, which inspection correctly allowed. No real freeze or export was performed by this reviewer.

Archive-name rejection is an extension/name policy, not a universal archive-content scanner. A broader filename scan covering ZIP, 7z, TAR, TGZ, GZ, BZ2, XZ, RAR, ZST and ISO found no new input archive candidates. The review assumes ordinary cooperative filesystem use and does not certify resistance to an adversarial actor changing filesystem paths concurrently on every operating system.

Root should include these completed review files and all other final QC evidence in the final freeze, then execute the actual packaging and preserve its exact final validation receipts. Packaging integrity does not establish Bengali/Arabic source correctness, semantic adjudication, corpus-wide image reading or bank readiness.
