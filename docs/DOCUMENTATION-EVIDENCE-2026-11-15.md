# Documentation evidence ledger — 15 November 2026

**Read-only source inspection, documentation edits only.** The source narration texts, source IDs, variants, material manifests, translator/provenance data, review statuses, held source records, release flags and generated 255-row catalogs were not edited.

| Evidence | Pinned revision / link | Verified fact |
| --- | --- | --- |
| Main and generated parent | [`bc0ef56b2358e20f425e961f0bac6511f30fed20`](https://github.com/blaghtayt-alt/Global-Hadith-Library/commit/bc0ef56b2358e20f425e961f0bac6511f30fed20) | Generated from source `9d8db54e0d8a452b967a469c43851780b23245ea` |
| [Build report](https://github.com/blaghtayt-alt/Global-Hadith-Library/blob/bc0ef56b2358e20f425e961f0bac6511f30fed20/reports/site-build.json) | `reports/site-build.json` | 112,571 source occurrences, 255 datasets, 11 primary languages; `independent_qc_performed=false` |
| [Language index](https://github.com/blaghtayt-alt/Global-Hadith-Library/blob/bc0ef56b2358e20f425e961f0bac6511f30fed20/browse/README.md) | Source stream SHA-256 `7ffad228681f43dadfeed49e89eee031d5e6d3c26f55905d26f396ae281a1270` | Primary language buckets sum to 112,571 |
| [Dataset directory](https://github.com/blaghtayt-alt/Global-Hadith-Library/blob/bc0ef56b2358e20f425e961f0bac6511f30fed20/catalog/README.md) | Generated table | 255 source rows, sum 112,571 |
| [Book/download directory](https://github.com/blaghtayt-alt/Global-Hadith-Library/blob/bc0ef56b2358e20f425e961f0bac6511f30fed20/catalog/BOOKS.md) | Generated table | 255 edition/part rows, sum 112,571 |
| [Material registry](https://github.com/blaghtayt-alt/Global-Hadith-Library/blob/bc0ef56b2358e20f425e961f0bac6511f30fed20/catalog/registered-materials.json) | 205 material manifests | 249 datasets / 104,148 occurrences + six publisher HadeethEnc datasets / 8,423 = 255 / 112,571 |
| [Counterpart availability](https://github.com/blaghtayt-alt/Global-Hadith-Library/blob/bc0ef56b2358e20f425e961f0bac6511f30fed20/reports/counterpart-availability.json) | Stored language text | Arabic 89,005; English 72,283; both 63,649; source links counted separately |
| [Fawaz upstream edition catalog](https://github.com/fawazahmed0/hadith-api/blob/df57907be35291c91ad6a6691180e22ca9920784/editions.json) | Pinned `df57907...` | 74 upstream edition entries, ten collections, nine languages, 44 non-Arabic/non-English upstream entries; not Bank imports |
| [Main workflow 43678731786](https://github.com/blaghtayt-alt/Global-Hadith-Library/actions/runs/43678731786) | 15 November 2026 | Build job and Pages publish job successful for pinned source commit |
| [Current site](https://blaghtayt-alt.github.io/Global-Hadith-Library/) | HTTP asset binding | **Unknown**: independently verified live asset SHA unavailable; workflow success is not proof of current HTTP bytes |

**Reconciled arithmetic:** nine focus languages `112571 - 32267 (Arabic primary) - 3684 (English primary) = 76620`. Language buckets across 11 codes total 112,571. Catalog directories each contain 255 parsed rows with sum 112,571. The **15 source-family rows** in [the guide](SOURCE-EDITION-STATUS.md) total 255 datasets/partitions and 112,571 occurrences. Material decomposition `249 + 6 = 255`, `104148 + 8423 = 112571`. Stored Arabic/English text is **not** primary-language registration. Fawaz upstream non-Arabic/non-English languages: French 9 + Indonesian 7 + Russian 3 + Turkish 8 + Tamil 2 + Bengali 8 + Urdu 7 = 44.

The [14 November active-books audit](../reports/ACTIVE-BOOKS-AUDIT-2026-11-14.md) recorded an older 101,040-occurrence / 251-dataset checkpoint and working-package statuses. It remains historical; no held Hindi, Urdu, Bengali or Portuguese packages were silently promoted. At inspection, [PR #20 (503 recovery)](https://github.com/blaghtayt-alt/Global-Hadith-Library/pull/20) and [PR #7 (Filipino transfer)](https://github.com/blaghtayt-alt/Global-Hadith-Library/pull/7) were open; separate owners handle source editions and other UX/localization/QC work.

**Scope test:** this ledger and source guide are documentation. They do not assert global database size/rank, unique hadith totals, full collection coverage, unverified personal translator names, certified human authorship, full-book source QC or source acquisition beyond the registered inventory.
