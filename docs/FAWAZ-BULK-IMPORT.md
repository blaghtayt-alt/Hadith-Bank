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
unsuffixed Arabic, English, Urdu and Bengali editions. The catalog also supplies
Bengali Nawawi, so its Arabic/English/Bengali editions are included as the eighth
collection: **31 whole-edition JSON files** in total. The first batch acquired the 21 Arabic/English/Urdu editions; the owner
then explicitly requested Bengali, adding seven `ben-*` editions from the same
pinned revision. This covers every Urdu and Bengali edition in the pinned catalog: seven Urdu
and eight Bengali files. Urdu Nawawi is not published there; its absence is
explicit and no fabricated endpoint is requested. The original three-language
plan remains supported.
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

The default plan permits eight books in a run. Each successful whole file is
saved and checkpointed before the next request. The original Arabic/English/Urdu
files plus the source documents form a complete base book for the seven original
collections. Nawawi requires its supplied Arabic and English base editions,
with Bengali added from its own verified file. Adding Bengali does
not remove those verified readings while its whole-edition file is pending.
The added language enters the book only after its source verifies; acquisition
is complete only when every configured edition is present. A partial original
base book stays outside the material registry. The final export retains complete
base books even when a later source fails. The workflow validates the complete
dependency set of every registered reading before saving a batch and rebuilding
the website.

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

Each registered occurrence retains its available Arabic, English, Urdu and Bengali
versions. Empty source fields remain empty in the source and create no invented
language text. Each version keeps its own translator/catalog metadata, literal
grades, source comments, source locator and hash. Source grades are also visible
as explicitly attributed assessment notes; the bank does not assign a uniform
grade or a new authenticity decision. Unknown authors remain null. The current
owner policy classifies nonlegacy published translations for display, preserving
the original unknown/explicit source provenance independently. Arabic source
text has no translation-origin label; this digital intake receives no OCR badge.

The primary source language is the first nonempty retained quotation (Arabic,
then English, Urdu and Bengali). Adding Bengali therefore preserves the primary
language of an existing occurrence. Separate material groups and storage parts satisfy the
existing registry format without changing occurrence IDs. JSONL material parts
are bounded to 40 MiB; source-edition identity and exact source evidence remain
explicit.

Per-occurrence `source.language_availability` and classification ledgers
distinguish available text, an empty source field, an absent provider entry, a
pending edition, a source field with no retained narration prefix, and a language
whose complete mixed source remains available as boundary-pending context. A missing
Bengali field never borrows another language's text or translator.

### Verified Bengali source acquisition

All seven pinned Bengali files were acquired locally on 12 November 2026, with
exact response hashes and receipts. They contain 36,390 provider entries and
35,795 nonempty text fields; 595 source fields are empty.

| Edition | Provider entries | Nonempty source fields | Empty source fields |
| --- | ---: | ---: | ---: |
| `ben-abudawud` | 5,274 | 5,270 | 4 |
| `ben-bukhari` | 7,589 | 7,529 | 60 |
| `ben-ibnmajah` | 4,343 | 4,336 | 7 |
| `ben-malik` | 1,858 | 1,749 | 109 |
| `ben-muslim` | 7,563 | 7,360 | 203 |
| `ben-nasai` | 5,765 | 5,656 | 109 |
| `ben-tirmidhi` | 3,998 | 3,895 | 103 |
| **Total** | **36,390** | **35,795** | **595** |

The additional `ben-nawawi` file has 42 entries and 42 nonempty fields. Across
all eight Bengali editions the totals are 36,432 entries, 35,837 nonempty fields
and 595 empty fields. Its Arabic and English companions also have all 42 entries;
the provider publishes no Urdu Nawawi edition at this revision.

The Bengali editions have no duplicate typed IDs and exactly the same ID sets
as the pinned Arabic and English editions. Every shared Bengali ID agrees with
the existing Arabic/English/Urdu `reference`, `arabicnumber` and grade arrays.
Bengali does not supply the 31 additional fractional Urdu Malik entries or the
Urdu Muslim entry zero. These remain explicit missing-language states. No new
provider occurrence is inferred from the added language.

The pinned catalog names the seven original Bengali authors as `Unknown`;
translator names therefore remain null. Its Nawawi editions name `Imam Nawawi`
as author in Arabic, English and Bengali. This compiler credit is preserved,
with no inferred English or Bengali translator. The owner’s current Human display policy remains separate
from the missing individual attribution. These are verified acquisition counts,
not claims that every source field is hadith-only. The saved import progress and
website build report record the actual publication revision independently.

## Classification and source comments

Initial registration uses explicit source-bound Prophetic attribution evidence,
including speech and actions. A book label or supplied grade alone is insufficient.
Prophetic names require complete word boundaries; `النبيذ` does not match
`النبي`. A wish that the Prophet had explained something, or a possessive mention
of his pulpit while another person speaks, remains held for subject attribution.
Uncertain entries, all-empty placeholders, conflicting identities and independent
sayings are preserved outside Hadith HTML/search. Actual Prophetic reports inside
introductions remain eligible after their own source boundaries are established.
An unrecognized attribution is **not** a final finding that the passage is
non-Prophetic. In particular, section number zero alone is not an introduction:
Ibn Majah's section zero is the Book of the Sunnah. Muslim also uses zero for
unavailable references beyond its introduction. Its explicit section-details
provider-ID range distinguishes those later records without changing any
original reference field or inferring a canonical number.

For supported explicit Abu Dawud/Abu Isa compiler-note markers, the narration
prefix and commentary tail are separated only by exact character offsets. Their
concatenation reproduces the source field. Notes remain in that language's own
collapsible comments. A compiler tail may contain another report; these tails are
retained with additional narration extraction pending, not counted as new
occurrences. Bengali source fields also use observed Bengali compiler
introductions, embedded Arabic compiler introductions, and narrowly marked
Tirmidhi dash-grade sentences as boundaries. Detection normalization never
rewrites the saved text or its displayed source spans. Supplemental exact-span rules separate supported Tirmidhi grading/parallel-report
comments and Bukhari/Malik compiler tails. Explicitly bracketed inline glosses
can retain multiple disjoint quotation spans; each span and every intervening
comment reconstruct the original text. The reader visibly identifies those
excerpts. A compiler name inside an isnad is not automatically a note boundary.

A language whose mixed discussion lacks a supported local boundary retains its
complete text as `source_context_not_narration` comments, its own references and
source link, and a visible `boundary_pending` explanation. Its `text` is null
and its scope is `external_source`. Other bounded languages remain registered.
Such context is excluded from narration search and locally available quotation
counts; it is accessible through that language's collapsible source/comments
panel. Arabic offsets are never transferred to a translation.

A verified content mismatch uses a different state: `scope=source_context`,
`quotation_status=content_mismatch`, and `text=null`. The original source is
still available in that language's comments, but it is not counted as either
quotation text or a linked Arabic/English counterpart. For Malik224, the Arabic,
English and Bengali sources contain al-Qasim's independent ruling, while the
Urdu field contains two separately attributed Prophetic reports. Only the Urdu
reports enter the narration text. Their separate components and mismatch note
are preserved; no corresponding Arabic or English is manufactured.

`catalog/fawaz-reviewed-spans.json` contains individually source-hash-bound
excerpts and introduction reports. Hash changes reject these decisions. It
retains the Urdu Muslim preface's Aisha report and the bounded Prophetic
quotation in the next mixed discussion while keeping surrounding Quran and
compiler text in comments. Abbreviated transmissions retain their exact wording
and separate provider IDs. Four explicitly reviewed relative-reference cases also
link to their own-language predecessor source: Tirmidhi2619→2618,
Muslim1431→1430 and7467→7466, and Abu Dawud2268→2267. Exact source wording,
named-chain evidence and observed source order support those relations together.
The parent text is never inserted and the occurrence IDs are not merged. Cases
with omitted Prophetic attribution, commentary-only continuations or competing
chains remain unresolved; source adjacency alone is not an identity rule.
Explicit source attribution establishes content scope only; it is not
independent authentication or translation certification.

Nawawi's original provider entry27 contains two separately attributed reports.
It remains one source occurrence with an explicit two-report notice, original
narrator introductions and an intact internal citation. It is not silently
concatenated or counted as two newly discovered provider IDs. Source variants
in entries5/19 and the Companion's advice after entry40 retain their own exact
boundaries and source comments.

The hash-bound regression review covers 40 language fields across ten original
provider entries. It restores narration after inline compiler glosses, a
compiler-transmitted dhikr and genuine reports with unmatched source punctuation;
it isolates Tirmidhi3254's Prophetic prayer from surrounding Quran and commentary
in all four languages. Exact source punctuation remains unchanged. Urdu Malik1788
also preserves its extra report with an explicit note that only the first report
has parallel readings in the other supplied languages.

## Source integrity and reader loading

`scripts/validate_fawaz_sources.py` independently checks the complete source
inventory, every displayed quotation and comment span, original numbering and
grades, translator metadata, source-context exclusions, component boundaries,
all provider IDs, and material hashes/counts. It does not rerun the classification
rule to declare itself correct and does not certify authenticity. The workflow
requires this validation before saving its whole-book batch. `--compare-root`
also produces a complete per-ID reconciliation against a previous verified
export, including every previously held occurrence and changes to old readings.

The hosted reader fetches at most six checked data shards concurrently. It
assembles them in manifest order, preserves Unicode/record fragments crossing
shard boundaries, and returns no partial bank when any checksum, size or count
fails. Source files and the exact source stream are unchanged by this loading
optimization.

Full source JSONs, metadata, held records and classification ledgers live under
`imports/web-fawaz-20261112/`. `progress.json` distinguishes acquired source files,
provider occurrences, registered occurrences, held occurrences, completed books,
pending books and a stop reason. “Complete” means the configured source files
were acquired and processed; it does not mean every source entry is a publishable
Prophetic narration or that every language has text.
