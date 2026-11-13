# Current checkpoint: another 85 held parents resolved; 64f4 acquisition fully audited

This entry records the next independently compared review cohort against the published review baseline [`7a3462e`](https://github.com/blaghtayt-alt/Hadith-Bank/commit/7a3462ef5513e3c116ead9a496420e8b9f484841). Every byte of the previous 121,575-byte status document is retained below and archived with this publication. Earlier entries describe their own dated checkpoints and should not be read as the current saved export.

## Reviewed 85-parent cohort

The 85 held parents were saved at [`17cd396`](https://github.com/blaghtayt-alt/Hadith-Bank/commit/17cd396eb858a29162505d545aad556ac73ce9ce). Four independent comparisons are complete, and the combined native review loader verifies84 registrations and one resolved source-context parent, `deenhindi-nasai:2636`. All five of that parent's own fields were read before its source-context decision; they contain transmission pointers rather than a supplied finite report.

| Review group | Parents | Registered | Source context | Complete own fields read |
|---|---:|---:|---:|---:|
| Bukhari 14 and Ibn Majah 8 |22|22|0|44|
| Muslim 14 and Ibn Majah 4 |18|18|0|36|
| Nasai 22 |22|21|1|47|
| Abu Dawud 17 and Tirmidhi 6 |23|23|0|46|
| Total |85|84|1|173|

The 173 complete readings cover 79,196 characters / 170,479 UTF-8 bytes. 168 language fields have admitted source spans; five read fields remain source context. The 252 other nonempty language fields remain explicitly unread context. All 425 source-language slots have exact, lossless selected/context partitions. The 170 saved source files and 85 raw HTML reparses are bound to the original checkpoint. This is not a claim that all five languages of every registered parent were reviewed.

The final independent comparison restored material house/location, time and referent qualifiers where required, while preserving their source-rendering status. In the Abu Dawud/Tirmidhi group, 135 characters returned to selected text and 333 previously selected characters moved to compiler commentary. The appended Tirmidhi 2622 doctrinal/legal ruling remains fully available as attributed source context; the main Abdullah ibn Shaqiq report of the Companions' view remains admitted. These are source-role decisions, not authenticity determinations. Source defects, incomplete Hindi predicates and unresolved honorific/pronominal speakers were preserved and qualified, with no wording supplied from another language.

The publication adds four active ledgers: 45 existing ledgers / 3,576 manual IDs become 49 ledgers / 3,661 manual IDs. Every prior ledger and decision is preserved. The original 3942 priority queue is unchanged at 6,311 Hindi/Urdu fields across 3,354 parents (Hindi 3,260; Urdu 3,051). Primary v1 evidence, subsequent bounded amendments, original reading notes and independent final reports are retained. See the [combined integration report](../reports/web-source-resolution-20261113/checkpoint17cd-independent-integration/validation-report.json) and the [publication inputs](../reports/web-source-resolution-20261113/phase22-publication-inputs-v1/staging-inputs.json).

## Actual saved acquisition and unconsumed review projection

The complete audit of [`64f4ed5`](https://github.com/blaghtayt-alt/Hadith-Bank/commit/64f4ed50ed6026855237a5d547a86dd03e73f804) verifies these actual saved counts:

| Saved state at 64f4 | Count |
|---|---:|
| Source inventory |36,390|
| Fetched |18,570|
| Registered |18,132|
| Resolved source-context entries |165|
| Classification held |273|
| Not fetched |17,820|
| Current source errors |0|

All 18,089 prior imported descriptors, all 1,000 historical error objects and all 1,000 consumed retry authorizations are preserved exactly. The next 481 fetched entries comprise 379 ordinary registrations and 102 new holds; the 171 prior held source rows are unchanged. All 273 held raw/parsed pairs were reopened and reparsed. The bounded artifact's original 250-record cap was preserved: 23 omitted records were completed using exact previously saved or pinned GitHub source files. The 379 other newly registered pages were not individually reread by this audit. See the [full saved-state audit](../reports/web-source-resolution-20261113/acquisition-run43480836830-saved-state-audit.json).

The saved 64f4 worker ran before the published 86-parent review and this 85-parent review were consumed. Applying those two completed cohorts to that fixed saved state gives a **projection** of 18,300 registered, 168 resolved source-context entries and 102 remaining holds, with 18,570 fetched and 17,820 unfetched unchanged. This is not a newly saved acquisition export. The additional 102 held parents are in a separately frozen review cohort and are not counted as resolved by this entry.

## Continuation and reader status

Acquisition run[`43480836830`](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43480836830) successfully saved 64f4, requested its ordinary reader and exported evidence. Its continuation step then failed with HTTP 422 because the target workflow 415715399 was disabled. The log does not establish who disabled it or why. The workflow was not enabled, dispatched or bypassed; the source plan, cadence and stop guards are unchanged. The 17,820 unfetched entries remain outstanding. See the [exact continuation receipt](../reports/web-source-resolution-20261113/acquisition-run43480836830-disabled-continuation-receipt.json).

The completed reader for b7f21, run[`43486700136`](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43486700136), passed 978 Python, 43 Node and 14 Chromium checks with 101,989 source records. Its supersession guard observed 7a3462e, so upload and deployment were skipped. That successful run is not a deployment receipt. The ordinary 7a3462e successor reader was observed in progress during preparation; this publication makes no new live-site claim. The last separately verified deployment receipt remains the earlier 3e574 source checkpoint, with no direct CDN recheck claimed here.

## Original requested cohorts and remaining scope

The original Deen Hindi 3,942 held parents have recorded parent decisions: 3,821 registered and 121 retained as resolved source context. The 6,311 priority language fields above remain separate unfinished language-review work. Fawaz's 244 flagged entries were classified into six recovered registrations and 238 resolved source-context entries, with 895 own nonempty fields reviewed; empty source content was not invented. The 11 Hadis.islom.uz flags yielded six registered parents, two embedded report components and five source-context parents. Its separate catalog-route failure remains documented. These earlier results are preserved below.

The current work is source-bound extraction and attribution review. Independent Pro QC has not been performed, certified-release eligibility remains false, and no authenticity certification is implied. Acquisition completion, remaining language review, new saved exports and live deployment each require their own evidence.

---

