# Pinned Fawaz Hadith API bulk intake

The owner requested the named websites and their cited upstream sources, then
specifically identified Deen Hindi's credit to Fawaz Ahmed Hadith API and Sunnah.
This intake registers **Fawaz provider occurrences separately**. It does not claim
that a Deen Hindi page was fetched, change Deen Hindi's queue, or merge another
publisher's edition with this source by number.

## Finite source scope

The authorized source is `fawazahmed0/hadith-api`, revision
`df57907be35291c91ad6a6691180e22ca9920784`. The plan in
`catalog/fawaz-bulk-plan.json` selects the seven full collections and the
unsuffixed Arabic, English and Urdu editions: **21 whole-edition JSON files**.
There is no Hindi or Roman Urdu edition in this source catalog. The `ara-*1`
files are diacritic-stripped variants and are not substitutes for the preserved
Arabic editions.

Primary documentation:

- [Provider README](https://github.com/fawazahmed0/hadith-api/blob/df57907be35291c91ad6a6691180e22ca9920784/README.md): whole-edition `/editions/{editionName}.json` endpoint.
- [Edition catalog](https://github.com/fawazahmed0/hadith-api/blob/df57907be35291c91ad6a6691180e22ca9920784/editions.json): language and edition-level attribution.
- [Contribution documentation](https://github.com/fawazahmed0/hadith-api/blob/df57907be35291c91ad6a6691180e22ca9920784/CONTRIBUTING.md): shared provider numbering across input editions.
- [Provider references](https://github.com/fawazahmed0/hadith-api/blob/df57907be35291c91ad6a6691180e22ca9920784/References.md): project-wide direct/indirect credits, not verified per-record ancestry.
- [Repository license](https://github.com/fawazahmed0/hadith-api/blob/df57907be35291c91ad6a6691180e22ca9920784/LICENSE): Unlicense declaration concerning software; upstream translation rights remain separately unassessed.

All five metadata documents are saved alongside the exact edition responses.
Their revision, source URL, retrieval receipt, raw hash, deterministic gzip hash
and byte sizes remain in the source state. Source files are never edited.

## Run bounded batches

```sh
python scripts/import_fawaz_bulk.py --root . --fetch --max-books 1
python scripts/import_fawaz_bulk.py --root . --export-only
```

The default plan permits seven books in a run. Each successful whole file is
saved and checkpointed before the next request. A complete book requires all
three expected source files plus the source documents; partial books stay out of
the material registry. The final export can retain completed books even when a
later source fails. The workflow validates this complete dependency set before
saving a batch and rebuilding the website.

Previously fetched files can be adopted without network requests:

```sh
python scripts/import_fawaz_bulk.py --root . --export-only --adopt-dir /path/to/audited-downloads
```

Each edition needs `{edition}.json` and `{edition}.receipt.json`. The pinned catalog
uses `editions-pinned.json` and `editions-pinned.receipt.json`. The other documents
use their source filename plus `.receipt.json`. Receipts require the exact pinned
`url`, `commit`, raw `sha256`, `bytes` and acquisition time. Mutable branch/CDN
receipts cannot stand in for pinned evidence.

`--export-only` makes no network calls. Saved compressed and expanded hashes are
verified before exporting. An unreviewed access denial is preserved and never
retried. `--retry-failed` permits an explicitly inspected transient failure to be
retried; it does not override a saved access denial. Rejected malformed responses
remain source evidence and are not promoted into active inputs.

## Identity, language and counts

The importer joins only a unique **typed provider `hadithnumber` within the same
pinned collection**, following the provider's declared edition structure. It
also verifies agreement of shared `reference` and `arabicnumber` values. It never
joins by array position, casts fractional identifiers to integers, or treats
identical text as proof that separate source occurrences are one narration.
Duplicate identities or conflicting supplied metadata remain held.

`hadithnumber`, `arabicnumber` and `reference.book`/`reference.hadith` are preserved
independently in each language version. Canonical cross-publisher numbers remain
null/uninferred. The API's documented per-entry link is supplied per language;
the imported bytes come from that language's pinned whole-edition snapshot and
exact `/hadiths/<position>` locator.

Each registered occurrence retains its available Arabic, English and Urdu
versions. Empty source fields remain empty in the source and create no invented
language text. Each version keeps its own translator/catalog metadata, literal
grades, source comments, source locator and hash. Source grades are also visible
as explicitly attributed assessment notes; the bank does not assign a uniform
grade or a new authenticity decision. Unknown authors remain null. The current
owner policy classifies nonlegacy published translations for display, preserving
the original unknown/explicit source provenance independently. Arabic source
text has no translation-origin label; this digital intake receives no OCR badge.

The primary source language is the first nonempty retained quotation (Arabic,
then English, then Urdu). Separate material groups and storage parts satisfy the
existing registry format without changing occurrence IDs. JSONL material parts
are bounded to 40 MiB; source-edition identity and exact source evidence remain
explicit.

## Classification and source comments

Initial registration uses explicit source-bound Prophetic attribution evidence,
including speech and actions. A book label or supplied grade alone is insufficient.
Prophetic names require complete word boundaries; `النبيذ` does not match
`النبي`. A wish that the Prophet had explained something, or a possessive mention
of his pulpit while another person speaks, remains held for subject attribution.
Uncertain entries, all-empty placeholders, conflicting identities, independent
sayings and source introductions are preserved outside Hadith HTML/search.
An unrecognized attribution is **not** a final finding that the passage is
non-Prophetic. In particular, section number zero alone is not an introduction:
Ibn Majah's section zero is the Book of the Sunnah.

For supported explicit Abu Dawud/Abu Isa compiler-note markers, the narration
prefix and commentary tail are separated only by exact character offsets. Their
concatenation reproduces the source field. Notes remain in that language's own
collapsible comments. A compiler tail may contain another report; these tails are
retained with additional narration extraction pending, not counted as new
occurrences. Remaining Arabic Malik/Bukhari named-compiler markers and unlabelled
Tirmidhi grading tails are held as `commentary_boundary_pending`: they can be
commentary or part of the narrational context, so the importer does not invent a
boundary. Unsupported or ambiguous material remains subject to later
source-bound review. This mechanical boundary/attribution triage is not an
independent scholarly classification or final certification.

Full source JSONs, metadata, held records and classification ledgers live under
`imports/web-fawaz-20261112/`. `progress.json` distinguishes acquired source files,
provider occurrences, registered occurrences, held occurrences, completed books,
pending books and a stop reason. “Complete” means the configured source files
were acquired and processed; it does not mean every source entry is a publishable
Prophetic narration or that every language has text.
