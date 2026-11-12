# Japanese research-v3 — pending source transfer

**Source transfer is blocked. No Japanese research-v3 ZIP, original PDFs, source records or research evidence have been uploaded into this directory.** This directory contains a documentation-only integration request. It is not an accepted material registration, a successful upload receipt or release approval.

The owner requested bank upload and integration on 12 November 2026. The request authorizes repository work; the preserved research checkpoint still contains explicit display/release holds. [package-request.json](package-request.json) records the exact recovery target, current compatibility findings and continuation requirements.

## Exact recovery target

- Package: `Japanese_Hadith_Sayings_Reports_Research_v3_20261112_PARTIAL_HOLD.zip`
- Expected bytes: **89,158,437**
- Expected SHA-256: `331d2973511301c6cd50d3e2a8612e135defda529e855b8b03894490005c01fa`
- [Saved source package](https://chatgpt.com/library?file_id=libfile_fde3_f-7eb5872317808191b5caac0c69078982_c3a5ae5e9e0c8191af5d21c39948b9f7&account_id=personal) — requires the owner's authorized file access.
- [Saved SHA-256 sidecar](https://chatgpt.com/library?file_id=libfile_fde3_f-260495806b4c8191afb067ff202af30f_c3a5ae5e9e0c8191af5d21c39948b9f7&account_id=personal)

The saved-file metadata and sidecar were read during this integration attempt. The ZIP bytes were not retrieved or rehashed because the execution environment was unavailable. Expected hashes must not be described as a completed repository transfer verification.

## Checkpoint inventory

These figures come from the completed research-v3 checkpoint. **They were not recounted from the package in this transfer attempt.**

| Whole-record proposed route | Records |
| --- | ---: |
| Hadith proposals | 1,147 |
| Non-hadith | 186 |
| Quran source context | 429 |
| Mixed-source parents | 106 |
| Unresolved origin | 21 |
| **Total preserved source records** | **1,889** |

The 1,889 source records preserve the 1,687-record baseline and 202 previously added occurrences. The checkpoint also contains 122 exact Prophetic components within 79 mixed parents and 45 related external witness links. Those are **not** 167 additional source occurrences. The original 414 Quran entries remain separately preserved.

Source-attributed Prophetic supplications, dhikr, actions, approvals and reports remain eligible hadith classifications. Their devotional form is not a reason to exclude them. Non-Prophetic sayings, commentary and unresolved attributions remain separate. This request performs no new record-level classification.

## Current framework findings

The inspected main commit was [9c2018215500dad58173da574988df98f414c2d8](https://github.com/blaghtayt-alt/Hadith-Bank/tree/9c2018215500dad58173da574988df98f414c2d8). The requested private ChatGPT conversation could not be fetched, so uncommitted changes from that conversation are not verified here.

The bank already builds the reading-room HTML and language counterparts from canonical material registrations. Follow [ADDING-MATERIAL](../../docs/ADDING-MATERIAL.md) and [READER-DESIGN](../../docs/READER-DESIGN.md), and refresh the framework state before continuing. Do not edit generated reader HTML, search shards or catalogs by hand.

The inspected [material registry](https://github.com/blaghtayt-alt/Hadith-Bank/blob/9c2018215500dad58173da574988df98f414c2d8/scripts/material_registry.py) projects **every registered row**. Its canonical projection does not carry or enforce `show_in_html_hadith:false`. The same projections feed reader HTML, search, individual pages and exports. Empty material registrations are invalid.

Accordingly, **do not register this all-HOLD package with `records-v1`**. Keeping a false flag in its original JSON does not prevent publication in the inspected framework. The existing `counterpart_policy.mode=disabled` can withhold Arabic/English matching, but it does not hide the primary Japanese record.

A preserved intake outside `materials/` can be added without changing the reader framework. Native PDF/DOCX/XLS/XLSX files cannot simply be unpacked into an unregistered folder: the current validator rejects unregistered source documents anywhere in the repository. General ZIP files are also ignored by the current `.gitignore`; a later exact archive transfer needs an intentional scoped exception or explicit tracking.

## Continuation

1. Retrieve the exact saved ZIP and verify the expected size and SHA-256 before extracting it. Do not rebuild source content from this receipt or repeat whole-book OCR.
2. Verify its manifests and original-record hashes. Preserve the full source package, separate enrichment, bibliography, evidence, page/record coverage and historical exception logs.
3. Preserve non-hadith material in its separate bank folder; preserve Quran context and unknown/mixed parents outside the Hadith reader corpus. Exact components retain their parent IDs and source spans.
4. Apply the existing release/display holds through a validated intake path. If framework support for held registrations is added, test that held/non-hadith/unknown sentinels remain absent from HTML, search, static narration pages, sitemaps and public exports while accepted sources remain unchanged.
5. Record actual uploaded files and hashes, source-record counts, workflow results and any visible subset in a new completed-transfer receipt. Preserve this request as history.
6. Perform the required **new, separate independent Pro evaluation over the exact final candidate bytes** before asserting certified bank inclusion.

## What this request changes

It records the authorized work and recovery instructions in the bank repository. It adds **zero** narration records to HTML/search, creates **no** material manifest, modifies **no** source text, and performs **no** OCR, fresh page audit or independent final QC. All research-v3 source records remain held in the saved package.
