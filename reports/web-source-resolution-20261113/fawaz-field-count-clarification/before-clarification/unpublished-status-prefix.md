# Current checkpoint: final 102 saved-source holds reviewed, with generated-export and deployment boundaries preserved

This update is anchored to the independently read-back publication `31c01136611b163683a01b47833bf74354820851` and immutable source checkpoint `64f4ed50ed6026855237a5d547a86dd03e73f804`. It adds four final source-bound review ledgers for the remaining 102 new held parents from that saved acquisition batch. Their complete primary reviews and independent final gates support **100 registrations and two resolved source-only parents**. Together with the previously published 86 and 85 decisions, all **273 parent dispositions** in the fixed 64f4 held cohort are now resolved in review inputs. Applying these review inputs in a later generated export is a separate step.

The earlier status document is preserved byte for byte below this prefix and in the phase23 publication evidence. This update also records the intervening generated-reader checkpoint, the concurrent Bengali PR14 merge, the previous publication's fresh independent readback, and the distinction between a successful build and an actual Pages deployment. Source text, source-local numbering, acquisition pacing, retry histories and workflow controls are preserved.

## What this review adds

| Assigned source cohort | Parent decisions | Complete own fields actually read | Admitted fields | Read source-context fields | Unread sibling fields |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bukhari 30 | 30 registered | 66 | 60 | 6 | 84 |
| Muslim 13 + Ibn Majah 13 | 25 registered; Muslim 2725 source-only | 55 | 50 | 5 | 75 |
| Nasai 15 | 15 registered | 30 | 30 | 0 | 45 |
| Abu Dawud 13 + Tirmidhi 18 | 30 registered; Abu Dawud 2720 source-only | 65 | 60 | 5 | 90 |
| **Total** | **100 registered; 2 resolved source-only** | **216** | **200** | **16** | **294** |

The 216 complete fields contain **112,759 characters / 239,747 UTF-8 bytes**. Both whole-parent source-only decisions are based on all five of that parent's own source fields. Other unread sibling fields remain explicitly unread. Bukhari 2773 and 2774 retain their actual finite Arabic/English reports while the completely read Hindi, Urdu and Roman-Urdu chain-only fields remain context.

Every assigned original response and parsed snapshot is bound to saved-source hashes. The source proof covers **204 saved files / 102 complete raw reparses**; the final native integration checks **510 lossless source-field partitions, 425 selected spans and 23,460 source/parent/language metadata leaf equalities**. The final integration adds four active ledgers to the prior 49, producing **53 active ledgers / 3,763 manual parent IDs**, with the previous 49 ledgers, their source dependencies and all 3,661 earlier decisions unchanged. This integration is a structural/source-integrity gate; it does not create additional linguistic reading credit. See the [combined102 validation report](../reports/web-source-resolution-20261113/checkpoint64f4-independent-integration/validation-report.json), which binds all four primary and independent final packages.

All four independent semantic comparisons finished before publication. Versioned amendments retain the original primary payloads, manifests and initial reading notes:

- **Bukhari:** ten selected ranges across eight fields become complete source context: 1,253 characters / 2,717 bytes. The affected nominal version apparatus and appended explanatory passages occur in 2709, 2718, 2737 and 2763. The actual finite report bodies, meaningful conditions, speaker attributions and surviving component identities remain exact. A separate root reading of the complete 2737/2763 originals records why those particular appended explanations fall under the owner's source-context rule.
- **Ibn Majah 2732 Urdu:** restore the eight-character / 12-byte adjective `( واضح )` inside Abd al-Malik's existing event-specific appraisal. The exact historical voice and existing report family remain intact; this is not a new parent or a reconstructed translation.
- **Nasai 2732 Hindi/Urdu:** move only the two tenth-day calendar definitions, 33 characters / 65 bytes, into context after the already printed Yawm al-Nahr. The actual named event day, sacrifice, eighth-day command timing, quantities and finite chronology remain selected. The earlier primary judgment remains visible in the immutable v1 evidence.
- **Tirmidhi 2711 Urdu:** remove the unsupported word `door/` from one English review description. The own source prints an identity exchange without that location. All source ranges and attribution metadata remain exact.

The review follows the owner's distinction between an actual numbered report/saying and appended apparatus. Companion and Successor reports, attributed sayings, finite abbreviated transmissions and actual historical encounters remain eligible under their own voices. A named transmission frame alone does not turn an explanatory side note into a main report. Missing predicates, places, subjects and wording remain unfilled; sibling translations and canonical-number guesses are not used to repair them.

## Actual saved export versus the fixed-source review projection

The complete source-state file still belongs to the 64f4 acquisition checkpoint. A later generated reader commit, `d304bef0c7955377026a0c2aeebdd677b1e05b0a`, consumed the previous 86 review decisions and changed the generated progress/staged/context/reuse outputs. Therefore the historical acquisition-worker count and the later saved generated-export count must be kept separate.

| Explicitly bounded state | Fetched | Registered | Resolved source context | Held | Unfetched |
| --- | ---: | ---: | ---: | ---: | ---: |
| Historical 64f4 acquisition-worker export | 18,570 | 18,132 | 165 | 273 | 17,820 |
| Actual d304 generated export, preserved through a6c52f35 and 31c011 | 18,570 | 18,216 | 167 | 187 | 17,820 |
| Projection after the published 85 decisions, on the same saved source | 18,570 | 18,300 | 168 | 102 | 17,820 |
| Projection after these final 102 decisions, on the same saved source | **18,570** | **18,400** | **170** | **0** | **17,820** |

The last two rows are **review projections**, pending a generated export that actually consumes the corresponding review inputs. They do not claim a new acquisition, a new saved export or a live deployment. In particular, the prior 86 decisions have already been consumed in d304 and are not added to its counts a second time. The final arithmetic agrees whether computed from the historical 273-hold checkpoint or the later 187-hold generated export.

The actual d304 progress body is 460,060 bytes, SHA256 `b205eaaf981fdb83286c4ca38b4ef0cff6065b0608ea84cd3d12ad24a94be1dd`, Git blob `558b4eaa1aa7d7174447db9e5475880681ef6226`. The immutable saved source-state Git blob remains `1435508cde81d7873f1e4c75854f6844fee4fdaa`. The previously published [64f4 acquisition audit](../reports/web-source-resolution-20261113/acquisition-run43480836830-saved-state-audit.json) remains the full history/control proof and is referenced without being rewritten.

## Newly reconciled GitHub checkpoints

- **Previous review publication:** `31c01136611b163683a01b47833bf74354820851`, parent `a6c52f35a320b10259bc7cc6200c53118d77f149`, is independently read back. The fresh check binds 28 complete ancestor/path-tree relationships, 19 unique tree objects and five complete bodies: four active review ledgers plus the entire status document. It verifies the previous 45 ledgers and resulting 49-ledger/3,661-ID state, the exact priority queue, the generated-export/source-state distinction and preservation of the actual parent's unrelated entries. Other payload bodies were not all downloaded again. See [phase22 readback](../reports/web-source-resolution-20261113/phase22-independent-readback/readback-receipt.json).
- **Generated reader checkpoint:** `d304bef0c7955377026a0c2aeebdd677b1e05b0a` is a direct child of `7a3462ef5513e3c116ead9a496420e8b9f484841`. Its generated Deen outputs include the 187-hold counts above. The actual 7a reader run `43492613360` completed Pages deployment successfully at **2026-11-13 19:59:53 UTC** after its guarded generated push. The receipt records 978 Python tests, 43 Node checks, 14 Chromium checks, 102,452 source records across 251 datasets and reader SHA256 `f69034acc5a6d3cbc906ee79f4c8b59d1f840573c294a23b3c4cbb613a093631`. Artifact metadata is bound; the 319,498,102-byte archive was not downloaded, and no CDN-byte readback is claimed. See [7a successful-deployment receipt](../reports/web-source-resolution-20261113/reader-7a3462e-successful-deployment-receipt.json).
- **Concurrent Bengali merge:** PR14, “Add Bengali Riyadh source context and preserved sources,” merged at `a6c52f35a320b10259bc7cc6200c53118d77f149` on top of d304. The API records 268 changed files. Its source-context data, scripts, reader changes and materials tree `acb1af952bed34e600c1503b8a55ea9cd8698620` are preserved. The PR author's asset/occurrence claims were not independently re-audited in this Deen review. This merge is newer than the verified 7a deployment. See [concurrent-checkpoint reconciliation](../reports/web-source-resolution-20261113/concurrent-d304-a6c-checkpoints/reconciliation-receipt.json).
- **Superseded a6 reader:** run `43497811581` completed software/export/shared-build/browser checks, including 994 Python tests, 43 Node checks and 14 Chromium checks. Its normal publication guard observed the newer 31c011 head at **20:29:11 UTC**. Its locally generated `2619c199cdb24f1edb3c46026259f93ff2da5bdd` commit was not pushed; artifact upload and Pages deployment were skipped. The normal guard requested successor run `43501979566`. The observation ended at **20:37:54 UTC**, when that successor was still working. See [a6 supersession receipt](../reports/web-source-resolution-20261113/reader-a6c52f35-superseded-receipt.json). A successful superseded build is not counted as a deployed checkpoint.

These receipts have explicit cutoffs. Publication must still use a fresh expected-head lease and preserve any verified descendant's generated or unrelated changes. This document does not predict a later reader's result.

## Remaining work and limits

The saved acquisition inventory still contains **17,820 unfetched entries**. Source run `43480836830` successfully saved 64f4, then its continuation request received **HTTP 422 because target workflow 415715399 was disabled**. The available evidence does not establish who disabled it or why. This review does not enable or dispatch it, alter pacing, consume another retry authorization or bypass a stop control. All 1,000 historical error/attempt histories remain preserved in the separate acquisition audit; there are zero current recorded acquisition errors at the bounded saved checkpoint.

For the original **3,942 Deen held parents**, the recorded parent outcomes remain **3,821 registered and 121 resolved source-only**. The language-level priority queue remains **6,311 unread Hindi/Urdu fields across 3,354 parent IDs**: 3,260 Hindi and 3,051 Urdu. This update covers new64f4 held parents and makes no reading claim for that older queue. Its exact SHA256 remains `8fd3e27cbfb6ae42a32e70268fe9793ecc228012afd8335a5efc1f869b1fe349`; the active original477 ledger remains `6d099f91f2e406b6ca026930f4437cc1ce3983e26883cfedc3049f9cbb2f91a7`.

The original **Fawaz 244** and **Hadis.islom.uz 11** disposition work remains separately recorded in the history below. Fawaz's 238 historical source-only occurrences are resolved context, not 238 newly unresolved holds. The distinct Islom catalog route `kitob/32/17` still has its recorded HTTP500/attempt5 gap; parent-disposition completion does not erase a catalog-fetch failure.

`independent_pro_qc` remains **`not_performed`**, and no certified release or religious-authenticity certification is claimed. The independent checks recorded here concern complete source reading, attribution, scope, exact source preservation and native integration. Parent-disposition completion, five-language coverage, source acquisition, generated export, software validation and deployment remain separately evidenced states.

---

