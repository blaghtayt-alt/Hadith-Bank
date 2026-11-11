# Hadith Bank

## Read and search online

### [Open the Hadith Bank website](https://blaghtayt-alt.github.io/Hadith-Bank/)

[![Website build](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml/badge.svg)](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

[All languages and current counts](browse/README.md) · [Source catalog](catalog/README.md) · [Offline HTML](https://blaghtayt-alt.github.io/Hadith-Bank/hadith-bank-reader.html) · [Add material](docs/ADDING-MATERIAL.md)

The website searches the narration texts in this repository, with language, collection, source-edition and translation-origin filters. It includes the Japanese Sahih Muslim volume-one and Vietnamese PDF-derived texts, alongside the existing HadeethEnc sources. New languages appear automatically when their registered material passes the build checks.

This is a standalone bank. Canonical JSON/JSONL records, original source files, source locators, review history, catalogs and search tools are kept here. Source links provide attribution; the reader's search data is embedded in its HTML and does not depend on Iman Companion or an external Hadith API.

**The hosted reader updates after a successful build of `main`.** Use the site's **Download offline reader** button to keep a local copy. A file already saved in your Downloads folder is a snapshot; download it again to get later additions. The website URL above is the shared, automatically refreshed entry point.

## Included source collections

The following source occurrences were included in the 11 November 2026 publication. The [generated catalog](catalog/materials.json) and website show the current totals after later additions.

| Source collection | Occurrences in this publication | Source and review information |
| --- | ---: | --- |
| HadeethEnc — Japanese, Filipino, Vietnamese, Chinese, Uzbek and Hindi snapshots | 8,423 | Original source bytes and Arabic-version flags retained; separate bank review waived by the owner. |
| Japanese Sahih Muslim, supplied volume-one PDF | 1,811 | Full supplied text, variants and shortened references retained; independent source QC remains pending. |
| Vietnamese Sahih al-Bukhari booklets | 767 | Full supplied text and source-specific provenance retained; independent source QC remains pending. |
| Vietnamese Sahih Muslim booklets | 971 | Full supplied text and source-specific provenance retained; independent source QC remains pending. |
| Vietnamese Sunan Abi Dawud booklets | 1,316 | Full supplied text and source-specific provenance retained; independent source QC remains pending. |
| Vietnamese 200 Golden Hadith | 200 | Source omissions and qualifications retained; independent source QC remains pending. |
| **Total** | **13,488** | **Source occurrences, not a count of unique canonical Hadiths.** |

Different narrations, chains, translations, repeated source occurrences and editions remain distinct. The Japanese Muslim source includes 191 shortened route/reference occurrences. Missing original Arabic remains null; raw PDF Arabic and its extraction issues are retained separately where supplied. Public availability does not mean that transcription, translation, Arabic alignment or scholarly grading has been independently certified.

Language shortcuts: [Japanese](browse/ja/README.md) · [Filipino](browse/fil/README.md) · [Vietnamese](browse/vi/README.md) · [Chinese](browse/zh-CN/README.md) · [Uzbek](browse/uz/README.md) · [Hindi](browse/hi/README.md). The [all-language index](browse/README.md) is regenerated as languages are added.

## Add material and let the HTML update

1. Create a folder under `materials/`, containing the structured narration records and their original source file.
2. Run the registration command in [Adding material](docs/ADDING-MATERIAL.md). It records the language, book, edition, source, record count and file hashes in `manifest.json`.
3. Commit or upload that folder to GitHub and merge it into `main`. The **Update Hadith Bank website** workflow validates the records, rebuilds the catalogs and reader, synchronizes the generated files, and deploys the website.

You do not edit the large HTML file or add language options by hand. JSON arrays and JSONL are supported. A PDF alone supplies evidence; searchable narrations also need structured text records. The build preserves existing review and rights qualifications and does not perform or claim a new scholarly review.

[Full instructions, exact record example and update procedure](docs/ADDING-MATERIAL.md) · [How automatic publication works](docs/WEBSITE.md) · [Build/deployment status](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

## Organization

| Material | Location |
| --- | --- |
| Registered new material and its original files | `materials/<material-slug>/` |
| Registration manifest | `materials/<material-slug>/manifest.json` |
| Preserved Japanese and Vietnamese source packages | `attachments/attachments-ja-muslim-c859ce57c211ea1b/` and `attachments/attachments-vi-920394517894aea9/` |
| Original HadeethEnc records | `languages/<language>/books/hadeethenc/editions/<edition>/records.jsonl` |
| Readable, paginated text | `browse/<language>/<book>/<edition>/` |
| Unified, checksum-verified search shards | `search/<language>/<book>/<edition>/part-*.jsonl` |
| Language, source, edition, provenance and checksum catalogs | `catalog/` |
| Hosted build output | `_site/` — built and deployed by the workflow |
| Self-contained offline reader | `hadith-bank-reader.html` |

JSON is the main machine-readable format. Arabic, translation, source collection/number, narrator/isnad, translator, page/row locator, tags, commentary, footnotes, references, grading and review history remain separate fields. Unknown information stays null or unknown. Rebuilding the reader never invents missing text or promotes a record to reviewed status.

Some earlier supplied-file datasets are still cataloged as metadata-only. The [material catalog](catalog/materials.json) records availability explicitly; their counts are not included in the website's searchable-record total.

## Search offline

Python 3.11 or later is sufficient; the bank tools use the standard library.

```bash
python scripts/hadith_search.py '礼拝' --language ja --limit 5
python scripts/hadith_search.py --language ja --book muslim --limit 5
python scripts/hadith_search.py --language vi --book bukhari --limit 5
python scripts/search.py fulltext '2758' --language ja --limit 5
```

The browser reader offers the same local corpus with filters and JSON export. Search-key normalization does not alter displayed source wording. [Search field guide](docs/READING-AND-SEARCH.md) · [Search record schema](schemas/search.record.schema.json).

## Rebuild and validate locally

```bash
python scripts/refresh_bank.py --root . --site-output _site
python -m unittest discover -s tests
```

The first command discovers every registration manifest, checks the canonical files and their hashes, rebuilds language/book/edition views, validates the complete search stream and reader, and stages the website. Open `_site/index.html` locally to inspect the result. Invalid input stops the build; a failed GitHub build leaves the previously deployed website available.

## Attribution and review

The reader uses three translation-origin labels: **Human**, **AI** and **Unknown**. The owner confirmed the HadeethEnc sources and the currently supplied website-sourced Japanese/Vietnamese materials as **Human**. Material copied from the older bank, especially the legacy Japanese material, stays **Unknown** until the owner confirms its origin. Unknown does not mean AI-generated. The [source-origin policy](catalog/provenance-policy.json) records these decisions separately from the original source flags and review history.

HadeethEnc's human-translation workflow, the owner review decision and source-version alignment notes remain documented in [translation-origin evidence](catalog/translation-origins.json) and [current review policy](docs/CURRENT-REVIEW-POLICY.md).

The Japanese and Vietnamese PDF intakes are public under the owner's explicit instruction. Their original `private_candidate` fields are preserved as import history; independent QC remains pending, and rights/Arabic/source exceptions remain visible. The publication decision is separate from evidence of review or licensing. See [the intake guide](docs/ADDITIONAL-INTAKES.md), [review and rights requirements](docs/REVIEW-AND-RIGHTS.md) and [contributor requirements](AGENTS.md).
