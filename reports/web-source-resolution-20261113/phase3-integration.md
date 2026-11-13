# Recovered Deen Hindi reviews and reader repair — 13 November 2026

## Saved inputs and new decisions

The acquisition recovery was actually committed at `b65b894adfc1fcd80ff2ebbcedba60970e4f163f`
by [worker 43409749980](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43409749980).
It preserved 12,775 common entries and restored 508 missing downloaded entries,
without new source HTTP requests. Its held-source artifact was downloaded and
all 234 archived source files were independently checked against the manifest;
all 117 raw HTML responses reparsed to the exact saved source objects and references.

The historical-error pilot was actually saved at `46f2ffbb77e5be8a3698ddd2655302053ca9c2b5`
by [worker 43411434552](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43411434552).
Its old failed response, new raw HTML, parsed record, receipt and preserved error
history were independently verified. See `bukhari-686-saved-pilot-proof.json`.

| Additive review package | Entries | Register | Source-only | Complete fields read | Selected fields | Unread siblings retained |
|---|---:|---:|---:|---:|---:|---:|
| Recovered Nasai | 22 | 21 | 1 | 110 | 105 | 0 |
| Recovered Muslim | 30 | 29 | 1 | 150 | 140 | 0 |
| Recovered Abu Dawud and Tirmidhi | 29 | 29 | 0 | 58 | 58 | 87 |
| Recovered Bukhari and Ibn Majah | 36 | 36 | 0 | 72 | 72 | 108 |
| Saved Bukhari 686 pilot | 1 | 1 | 0 | 5 | 5 | 0 |
| **Total** | **118** | **116** | **2** | **395** | **380** | **195** |

All 590 source-field partitions preserve the exact full fields. The 15 read
fields without an admitted report remain reviewed context. The two source-only
identities are `deenhindi-nasai:1990` and `deenhindi-muslim:2032`, each containing
only chains or references rather than the actual report. No field was filled
from another language or a neighboring entry. Printed references, grades,
narrator nulls, variants and source identities remain unchanged. Each package
includes its own source-bound ledger, preserved baseline and validation evidence.

At the pilot save, Deen Hindi had 13,284 fetched = 13,045 registered + 118 held
+ 121 source-only. These new decisions project 13,161 registered + 123 source-only
and zero held for that fixed cohort. A full repository export must confirm the
derived manifests; subsequent acquisition can add new review work.

## Retry activation after the saved pilot

All 1,000 original historical failure bodies had previously been decompressed
and checked against their exact source identities and stored hashes. The first
ordinary retry, `bukhari:686`, succeeded and was saved with its consumed receipt.
The active candidate retains all 1,000 original authorizations, records that
saved proof and leaves 999 unconsumed identities eligible. The retry consumer
recognizes the already consumed pilot; changing the manifest does not replay it.

`stop_batch_after_reviewed_retry` is now false. Each authorization still permits
at most one ordinary request; source access checks, request delay, persistent
block state, prior failures, per-ID request receipts and serialized acquisition
remain in force. A renewed challenge stops acquisition. No block is cleared.

At `46f2ffb`, acquisition still has 22,107 ordinary pending pages and 999
historical errors, totaling 23,106. The original approximately 24k acquisition
queue is ongoing, not complete.

## Concrete reader failure and repair

[Reader 43409749952](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43409749952)
passed the Python/Node tests, Fawaz reviewed export, website reviews-only export
and official counterpart sync. The shared refresh then failed at
`Occurrence has no source text to review: deenhindi-malik:1057`.

The source has an admitted Urdu reading and absent Arabic/English primary
fields. The shared review helper previously accepted only those two primaries.
The repair supports an exact stable-ID secondary language-version binding,
including text/language and whole-version hash, throughout queue preparation,
compilation and runtime evidence checking. Existing primary bindings retain
their format. Missing, ambiguous, stale or context-only versions fail; no
primary text is synthesized and no counterpart is approved automatically.

The actual source fixture and all 44 focused counterpart tests passed. A second
agent independently reviewed the three-script diff and found no concrete
stale-binding or unintended-acceptance defect. See
`reader-secondary-language-validation.json` and `reader-secondary-language-fix.md`.
Full shared rebuild, browser tests and actual deployment remain workflow gates.

## Other requested queues

The actual Fawaz export observed in that reader job reported 36,226 registered,
238 resolved source-only and zero unresolved parent dispositions. The 244
requested cases are six admitted reports plus 238 preserved source-only cases.
The separately recorded unread sibling-language queue is not represented as
complete. Hadis.islom.uz's eleven requested parents are resolved; saved exports
have 8,622 registered occurrences and zero holds. Its unavailable source route
`/kitob/32/17` remains HTTP500 and is not represented as repaired.

These are source-bound semantic and preservation decisions. Independent Pro QC,
new authenticity grading and language-equivalence certification are not claimed.
