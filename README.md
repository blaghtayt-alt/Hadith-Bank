# Hadith Bank

## Read and search online

### [Open the Hadith Bank website](https://blaghtayt-alt.github.io/Hadith-Bank/)

[![Website build](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml/badge.svg)](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

[All languages and current counts](browse/README.md) · [Source catalog](catalog/README.md) · [Offline HTML](https://blaghtayt-alt.github.io/Hadith-Bank/hadith-bank-reader.html) · [Add material](docs/ADDING-MATERIAL.md)

The website searches the narration texts in this repository, with language, collection, source-edition and translation-origin filters. It includes HadeethEnc, Japanese Sahih Muslim volume one, Vietnamese PDF-derived texts, and individual quotations extracted from the old banks and Qur’an-study materials. Persian is included alongside Japanese, Filipino, Vietnamese, Chinese, Uzbek and Hindi. New languages appear automatically when their registered material passes the build checks.

This is a standalone bank. Canonical JSON/JSONL records, original source files, source locators, review history, catalogs and search tools are kept here. Source links provide attribution; the reader's search data is embedded in its HTML and does not depend on Iman Companion or an external Hadith API.

**The hosted reader updates after a successful build of `main`.** Use the site's **Download offline reader** button to keep a local copy. A file already saved in your Downloads folder is a snapshot; download it again to get later additions. The website URL above is the shared, automatically refreshed entry point.

## Download original books

In the reader, open **Browse available materials → Download books and source materials**. Choose **Download Word (.doc)**, **Download Word (.docx)** or **Download PDF** for the source you want. The same download links appear in each applicable narration card under **Source & translation details**.

Downloads preserve the supplied file format:

- Chinese Sunan Abī Dāwūd: [original Word document (.doc)](materials/zh-abu-dawud-yu-2002-doc/艾布达吾德圣训_Sunan_Abi_Dawud.doc).
- Persian books: original `.docx` files in their respective [material folders](materials/).
- Japanese and Vietnamese PDF sources: the preserved [Japanese package](attachments/attachments-ja-muslim-c859ce57c211ea1b/) and [Vietnamese package](attachments/attachments-vi-920394517894aea9/).

You can also open these folders on GitHub, select a source file and download its raw contents. The reader offers only Word or PDF files actually preserved in the repository. Its offline HTML contains searchable narration data; original-book downloads use GitHub, while a complete downloaded repository also retains the source files locally.

## Included source collections

The following imports form the original structured collection. The [generated catalog](catalog/materials.json) and website include the additional old-bank and Qur’an-book quotation extractions described below and show the complete current totals.

| Source collection | Occurrences in this publication | Source and review information |
| --- | ---: | --- |
| HadeethEnc — Japanese, Filipino, Vietnamese, Chinese, Uzbek and Hindi snapshots | 8,423 | Original source bytes and Arabic-version flags retained; separate bank review waived by the owner. |
| Japanese Sahih Muslim, supplied volume-one PDF | 1,811 | Native PDF text; original text, variants and shortened references retained. |
| Vietnamese Sahih al-Bukhari booklets | 767 | Native PDF text; full supplied text and source-specific provenance retained. |
| Vietnamese Sahih Muslim booklets | 971 | Native PDF text; full supplied text and source-specific provenance retained. |
| Vietnamese Sunan Abi Dawud booklets | 1,316 | Native PDF text; full supplied text and source-specific provenance retained. |
| Vietnamese 200 Golden Hadith | 200 | Native PDF text; source omissions and qualifications retained. |
| **Original structured imports** | **13,488** | **Source occurrences; additional extracted quotations are included in the current catalog.** |

Different narrations, chains, translations, repeated source occurrences and editions remain distinct. The Japanese Muslim source includes 191 shortened route/reference occurrences. Missing original Arabic remains null; raw PDF Arabic and its extraction issues are retained separately where supplied. Public availability does not mean that transcription, translation, Arabic alignment or scholarly grading has been independently certified.

### Individual quotations from the old bank and Qur’an books

The earlier Japanese count of **281** counted the Japanese HadeethEnc snapshot. It did not count the quotations embedded in the older lessons and articles. Those documents did contain hadiths. Their explicitly bounded quotations now have individual records, organized by the cited collection and number when the source provides them. The original articles remain available as evidence.

The same extraction covers the selected old-bank and Qur’an-study sources in all seven bank languages. Quotations, reported meanings and Companion reports are labeled separately. Qur’an verses, explanations, proverbs and historical remarks are excluded from hadith quotation counts. Missing collection numbers remain unknown; source references are not silently converted into verified canonical numbering. Old-bank translation origin remains **Unknown**, including Japanese and Persian, until the owner confirms it.

[Extraction scope, evidence and validation](docs/LEGACY-EXTRACTION.md) explains the source snapshot, quotation boundaries, mirror handling and remaining source limitations. Counts represent source occurrences, including partial quotations and repeated appearances in different lessons; they are not unique canonical Hadith totals.

Language shortcuts: [Japanese](browse/ja/README.md) · [Filipino](browse/fil/README.md) · [Vietnamese](browse/vi/README.md) · [Chinese](browse/zh-CN/README.md) · [Uzbek](browse/uz/README.md) · [Hindi](browse/hi/README.md) · [Persian](browse/fa/README.md). The [all-language index](browse/README.md) is regenerated as languages are added.

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

**QC labels apply to OCR materials only.** The website imports, native PDF text and structured quotation extractions do not receive the four generic pending-QC/import-history badges. Original review history stays available in record details; source-alignment and missing-attribution information remain visible. This display rule does not claim that a new independent review occurred. See [current review policy](docs/CURRENT-REVIEW-POLICY.md), [the intake guide](docs/ADDITIONAL-INTAKES.md) and [contributor requirements](AGENTS.md).
