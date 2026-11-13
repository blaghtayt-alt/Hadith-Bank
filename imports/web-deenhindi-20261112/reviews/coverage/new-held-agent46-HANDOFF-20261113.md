# Newly acquired Deen Hindi held rows: agent 46

## Result

All 46 assigned rows are resolved: **44 register, 2 source-only exclude, 0 held**. They are disjoint from the earlier 636-row Abu Dawud/Tirmidhi cohort and the root agent's new 35-row cohort.

| Book | Assigned | Register | Source-only |
| --- | ---: | ---: | ---: |
| Muslim | 5 | 4 | 1 |
| Abu Dawud | 18 | 18 | 0 |
| Tirmidhi | 6 | 6 | 0 |
| Nasai | 10 | 10 | 0 |
| Ibn Majah | 7 | 6 | 1 |

Source commit: `eb6061e1d4115d141d3f2d723ec83fc57f34b1b2`, including the preserved concurrent import data. The assignment file was `hindi-resolve/new-held-agent46-eb6061e.jsonl`.

## Publication files

`publish-files.json` gives the exact local path, repository destination, bytes and SHA256 of every deliverable. Publish the compressed review and **its bound source baseline together**:

- `source-review-20261113-new-held-agent46-eb6061e.json.gz` under `imports/web-deenhindi-20261112/reviews/`.
- `20261113-new-held-agent46-eb6061e.jsonl.gz` under `imports/web-deenhindi-20261112/reviews/baselines/`.

The review document explicitly binds the baseline path and compressed-byte SHA256. Omitting or relocating the baseline without updating the review will correctly fail adapter validation. Do not also publish the uncompressed equivalent review: it contains the same IDs and would create duplicate decisions.

The publication manifest also includes a compressed manual-reading ledger, handoff summary and detailed character/byte coverage as supporting evidence.

## Actual full-field reading

All 45 nonempty English fields and all 46 Hindi fields were individually read completely. For the two source-only rows, every available Urdu, Arabic and Roman Urdu field was additionally read. Total: **96 complete nonempty fields**, **37,815 characters**, **68,758 UTF-8 bytes**.

44 English and 44 Hindi fields contain selected actual reports: 88 admitted language fields and 35,575 selected source characters. The remaining eight fully read fields are source-only. The 130 unread nonempty Arabic/Urdu/Roman Urdu sibling fields remain complete source context and are not approved quotations.

- **Muslim 1967:** every language contains a chain pointer and transmitter-name correction, without a report body. No adjacent hadith is imported.
- **Ibn Majah 1955:** English and Arabic are empty; all three other languages explicitly state the supplied source lacks the hadith text.

## Decisions and preservation

Compiler grading, vocabulary, biography, chain criticism and bare pointers remain context. Actual alternative report wording is selected with its own attribution. Companion/scholarly speech is labeled separately from Prophet speech.

English/Hindi differences were independently reviewed and preserved. Examples include Abu Dawud 1922's pace wording, 1957's finger gesture, 1958's questioner/transmitter naming, 1960's caliph list, and Nasai 1978's Naji/Nafi attribution. Hindi omissions in Nasai 1961's debt guarantee and Ibn Majah 1952's initial wife count are not repaired from English. Tirmidhi 1960's English reply is passively attributed, while Hindi explicitly names the Messenger; decisions preserve that difference. Abu Dawud 1968 has real added report wording in both fields, with limited attribution in Hindi; it is distinguished from a bare chain notice.

This is manual attribution and boundary review, not independent Pro QC, authenticity assessment, transcription certification or a new translation. Original field words, source metadata, IDs, snapshots and source-local numbering remain unchanged.

## Validation

Both uncompressed and compressed candidates passed the actual `SourceReviews` adapter for all 46 exact source records. Every selected source span and field is SHA256-bound, and quotations plus context reconstruct the exact source text. The compressed baseline decompresses byte-for-byte to the original assigned source file. All nonempty fields of each excluded parent have explicit reviewed context decisions. ID disjointness against the baseline 636 and root's new 35 was checked.

No source HTTP requests, live importer jobs or upstream repository changes were made by this agent. Parent integration still needs the combined current repository rebuild and publication validation.
