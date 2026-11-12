# Hadith Bank — multilingual hadith texts and source books

**Sunni hadith texts, translations and source books in Japanese, Chinese, Persian, Filipino, Vietnamese, Uzbek and Hindi.** Search a quotation, browse a collection or source edition, and download the original Word or PDF where it is available. Each record keeps its own source reference, translation origin and provenance.

## Read, search and find a book

### [Search Hadith Bank](https://blaghtayt-alt.github.io/Hadith-Bank/)

[![Website build](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml/badge.svg)](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

[Browse languages and books](https://blaghtayt-alt.github.io/Hadith-Bank/browse/) · [Book titles, editions and downloads](catalog/BOOKS.md) · [Current counts](browse/README.md) · [Source catalog](catalog/README.md) · [Offline reader](https://blaghtayt-alt.github.io/Hadith-Bank/hadith-bank-reader.html)

| Language | Read online | Read in this repository |
| --- | --- | --- |
| Japanese — 日本語 | [日本語のハディース](https://blaghtayt-alt.github.io/Hadith-Bank/browse/ja/) | [Japanese records](browse/ja/README.md) |
| Chinese — 中文 | [中文圣训](https://blaghtayt-alt.github.io/Hadith-Bank/browse/zh-CN/) | [Chinese records](browse/zh-CN/README.md) |
| Persian — فارسی | [احادیث فارسی](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fa/) | [Persian records](browse/fa/README.md) |
| Filipino / Tagalog | [Hadith sa Filipino](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fil/) | [Filipino records](browse/fil/README.md) |
| Vietnamese — Tiếng Việt | [Hadith tiếng Việt](https://blaghtayt-alt.github.io/Hadith-Bank/browse/vi/) | [Vietnamese records](browse/vi/README.md) |
| Uzbek — O‘zbekcha | [O‘zbekcha hadislar](https://blaghtayt-alt.github.io/Hadith-Bank/browse/uz/) | [Uzbek records](browse/uz/README.md) |
| Hindi — हिन्दी | [हिन्दी हदीस](https://blaghtayt-alt.github.io/Hadith-Bank/browse/hi/) | [Hindi records](browse/hi/README.md) |

The [generated language index](https://blaghtayt-alt.github.io/Hadith-Bank/browse/) and [material catalog](catalog/materials.json) show the accepted corpus and current totals. New languages appear automatically when their owner-authorized registrations pass the build checks.

The interactive reader searches narration text and supplied references, with language, collection, source-edition and translation-origin filters. Arabic and English counterparts are available where a supported source match exists. Their coverage is recorded separately; an available counterpart does not imply a complete Arabic or English edition of every book.

Use **Arabic & English availability** to select stored bilingual text, English source-page links, or occurrences still awaiting one or both languages. The [book-by-book availability report](reports/counterpart-availability.md) counts Arabic text, English text, external links and missing languages independently. Arabic already present in a book remains available even when its English counterpart is unresolved.

The [latest Arabic/English continuation audit](reports/counterpart-continuation-2026-11-12.md) records the newly checked source matches, exact-version English content holds and remaining coverage. Counterparts use preserved published texts; the build does not create translations.

Every registered book enters the same language-linking workflow. The build refreshes a [source-bound candidate review queue](reports/counterpart-review/manifest.json) for missing counterparts. See [Arabic/English integration and future Chinese Abū Dāwūd additions](docs/LANGUAGE-COUNTERPARTS.md) for preparing and compiling new reviewed mappings. Future installments and editions retain separate source files, numbering and occurrence identities.

Every indexed source occurrence also has a separate HTML reading page. These pages contain the text before JavaScript runs and link through language, book and edition indexes. They provide stable destinations for sharing a particular narration and for search-engine discovery. The [sitemap](https://blaghtayt-alt.github.io/Hadith-Bank/sitemap.xml) is rebuilt with the corpus. See [search-engine discovery](docs/SEARCH-ENGINE-DISCOVERY.md) for the design and indexing setup.

## Books and source collections

The following are examples of preserved source editions. The automatically generated [book catalog](catalog/BOOKS.md) lists all current editions, their actual source titles, reading links and available downloads.

| Source title or collection | Language and scope | Read |
| --- | --- | --- |
| HadeethEnc | Japanese, Filipino, Vietnamese, Chinese, Uzbek and Hindi source snapshots | [All languages](https://blaghtayt-alt.github.io/Hadith-Bank/browse/) |
| Sahih Muslim | Japanese supplied volume-one PDF, including source variants and shortened references | [Japanese Sahih Muslim](https://blaghtayt-alt.github.io/Hadith-Bank/browse/ja/muslim/) |
| Sahih al-Bukhari, Sahih Muslim, Sunan Abi Dawud and 200 Golden Hadith | Supplied Vietnamese booklets | [Vietnamese books](https://blaghtayt-alt.github.io/Hadith-Bank/browse/vi/) |
| 艾布·达吾德圣训集（部分译本） — Sunan Abī Dāwūd | Partial Chinese edition | [Chinese Sunan Abi Dawud](https://blaghtayt-alt.github.io/Hadith-Bank/browse/zh-CN/abu-dawud/) |
| 穆宛塔圣训集 — Muwatta of Imam Malik | Chinese edition of the al-Shaybani recension | [Chinese Muwatta](https://blaghtayt-alt.github.io/Hadith-Bank/browse/zh-CN/malik/) |
| 穆斯林的堡垒 — Hisn al-Muslim | Chinese source quotations; source transcription passed, canonical details remain under review | [Chinese Hisn al-Muslim](https://blaghtayt-alt.github.io/Hadith-Bank/browse/zh-CN/hisn-al-muslim/) |
| فیض الباری — مختصر صحیح البخاری — Faiz al-Bari | Six supplied Persian volumes | [Persian Bukhari sources](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fa/bukhari/) |
| مختصر صحیح مسلم — Mukhtasar Sahih Muslim | Two supplied Persian volumes, al-Mundhiri / Tarshabi edition | [Persian Muslim sources](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fa/muslim/) |
| ترجمه فارسی ریاض الصالحین — Riyadh al-Salihin | Persian translation credited to Abd Allah Khamush Heravi | [Persian Riyadh al-Salihin](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fa/riyadh-al-salihin/) |
| ترغیب و ترهیب صحیح و ضعیف — Al-Targhib wa-l-Tarhib | Three supplied Persian volumes, Musa Bazmandegan edition | [Persian Targhib and Tarhib](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fa/targhib-wa-tarhib/) |

The bank also contains individually extracted quotations from older lessons, articles and Qur’an-study materials. Their supplied references include collections such as Sahih al-Bukhari, Sahih Muslim, Jami al-Tirmidhi, Sunan Ibn Majah, Musnad Ahmad, Al-Adab al-Mufrad and Hisn al-Muslim. A collection appearing in an index can represent selected quotations or a partial source edition. It does not establish that the complete book is available in that language.

Different narrations, chains, repeated source occurrences, translations and editions remain distinct. Counts are **source occurrences**, including explicitly labeled excerpts, variants, Companion reports and fragments; they are not unique canonical hadith totals. Source-local numbers, provider entry IDs and canonical collection numbers remain separate.

## Download original books

Open the [book catalog](catalog/BOOKS.md), a book’s online edition page, or **Browse available materials → Download books and source materials** in the interactive reader. Choose the available **Word (.doc)**, **Word (.docx)** or **PDF** download. Applicable narration pages also link to their preserved source file.

Examples:

- 穆宛塔圣训集 — Muwatta: [original Chinese Word document (.docx)](https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/materials/zh-muwatta-shaybani-yu-2000-docx/穆宛塔圣训集_Muwatta_Chinese.docx).
- 艾布达吾德圣训 — Sunan Abī Dāwūd: [original Chinese Word document (.doc)](https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/materials/zh-abu-dawud-yu-2002-doc/艾布达吾德圣训_Sunan_Abi_Dawud.doc).
- 穆斯林的堡垒 — Hisn al-Muslim: [original Chinese PDF](https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/materials/zh-cn-hisn-muslim-1a09ee75/zh-hisn.pdf), with [preserved final data and evaluation](docs/CHINESE-HISN.md).
- Persian books: original `.docx` files linked from the [book catalog](catalog/BOOKS.md) and preserved in their [material folders](materials/).
- Japanese and Vietnamese PDF sources: preserved in the [Japanese package](attachments/attachments-ja-muslim-c859ce57c211ea1b/) and [Vietnamese package](attachments/attachments-vi-920394517894aea9/).

Downloads keep the supplied file format and original bytes. A Word source is not presented as a PDF unless that PDF is actually preserved. The offline HTML contains searchable narration data; original-book downloads use GitHub. A full downloaded repository also retains its local source files. Availability does not grant a new redistribution license; source-specific reuse conditions and unassessed rights remain recorded.

## Source text, attribution and review

This is a standalone bank. Canonical JSON/JSONL records, original sources, page and paragraph locators, review history, catalogs and search tools are kept here. The interactive reader’s search data is embedded in its HTML and does not depend on Iman Companion or an external Hadith API.

Arabic, translation, collection and number, narrator/isnad, translator, source locators, tags, commentary, footnotes, references and grading remain separate fields. Missing original Arabic and unsupported metadata remain null or unknown. Source-text anomalies and different publisher versions are preserved and qualified, rather than silently corrected or merged.

The reader uses **Human**, **AI** and **Unknown** translation-origin labels. Under the owner’s current rule, **all newly added books and separately acquired English counterparts are Human unless their own source explicitly states otherwise**. **Unknown is reserved for copied old-bank resources**, including quotations extracted from old Iman/Qur’an-study material. An explicit source declaration of AI translation is retained and displayed as AI. OCR, AI extraction, AI review and an unnamed translator do not make a new book’s translation Unknown. The [source-origin policy](catalog/provenance-policy.json) and each material’s provenance retain the current decision separately from historical source flags. Arabic originals do not receive a translation-origin label.

**QC labels apply to OCR materials only.** Website imports, native PDF text and structured quotation extractions do not receive generic pending-QC badges. Historical review fields and genuine source-alignment or attribution qualifications remain available. Public availability, a Human label or a linked Arabic/English counterpart does not certify transcription, translation, canonical identity or scholarly authenticity.

[Current review policy](docs/CURRENT-REVIEW-POLICY.md) · [Translation-origin evidence](catalog/translation-origins.json) · [Contributor requirements](AGENTS.md) · [Rights and review](docs/REVIEW-AND-RIGHTS.md)

### Quotations extracted from lessons and Qur’an books

Explicitly bounded quotations from the selected older-bank and Qur’an-study sources have individual records, organized by the cited collection and number when supplied. The original documents remain available as evidence. Quotations, reported meanings and Companion reports are labeled separately. Qur’an verses, explanations, proverbs and historical remarks are excluded from hadith quotation counts.

[Extraction scope, evidence and validation](docs/LEGACY-EXTRACTION.md) documents quotation boundaries, source snapshots, mirror handling and remaining limitations. Source references are not silently promoted to verified canonical numbering. Some earlier supplied-file datasets remain metadata-only; the [material catalog](catalog/materials.json) marks availability, and those datasets do not enter the searchable-record total.

## Add material and update the website

1. Create an owner-authorized folder under `materials/` containing structured narration records and the original source file.
2. Follow [Adding material](docs/ADDING-MATERIAL.md) to register its language, book, edition, source, record count and file hashes in `manifest.json`.
3. Commit the folder to GitHub and merge it into `main`. The **Update Hadith Bank website** workflow validates the data, rebuilds catalogs and reading/search pages, and deploys the site.

The same build updates the language and book indexes, individual HTML pages, book-download catalog and sitemap. Do not edit generated narration pages or add language options by hand. JSON arrays and JSONL are supported. A PDF alone supplies evidence; searchable narrations also need structured text records. The build does not create a new translation or perform a scholarly review.

**The hosted site updates after a successful build of `main`.** A previously downloaded reader remains a snapshot. Use **Download offline reader** again to get later additions.

[Full import instructions](docs/ADDING-MATERIAL.md) · [Automatic publication](docs/WEBSITE.md) · [Search-engine discovery](docs/SEARCH-ENGINE-DISCOVERY.md) · [Build/deployment status](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

## Repository and website organization

| Material | Location |
| --- | --- |
| Registered records, source documents and manifest | `materials/<material-slug>/` |
| Preserved Japanese and Vietnamese source packages | `attachments/` |
| Original HadeethEnc records | `languages/<language>/books/hadeethenc/editions/<edition>/records.jsonl` |
| Paginated reading views on GitHub | `browse/<language>/<book>/<edition>/` |
| Book titles, source editions and downloads | `catalog/BOOKS.md` |
| Checksum-verified search shards | `search/<language>/<book>/<edition>/part-*.jsonl` |
| Language, source, provenance and checksum catalogs | `catalog/` |
| Hosted language, book and edition indexes | `_site/browse/` |
| Hosted individual narration pages | `_site/hadith/<language>/<book>/<edition>/<stable-id-hash>.html` |
| Hosted sitemap index and its shards | `_site/sitemap.xml` and generated sitemap files |
| Self-contained offline reader | `hadith-bank-reader.html` |

The workflow builds `_site/` as the deployment artifact. Its individual HTML pages are generated from the accepted data rather than maintained as thousands of additional source files in Git. Existing source paths and occurrence IDs remain stable.

## Search offline

Python 3.11 or later is sufficient; the bank tools use the standard library.

```bash
python scripts/hadith_search.py '礼拝' --language ja --limit 5
python scripts/hadith_search.py --language ja --book muslim --limit 5
python scripts/hadith_search.py --language vi --book bukhari --limit 5
python scripts/search.py fulltext '2758' --language ja --limit 5
```

The browser reader searches the same local corpus and exports selected records as JSON. Search-key normalization does not alter displayed wording. [Search field guide](docs/READING-AND-SEARCH.md) · [Search record schema](schemas/search.record.schema.json).

## Rebuild and validate

```bash
python scripts/refresh_bank.py --root . --site-output _site
python -m unittest discover -s tests
```

The refresh command verifies canonical files and hashes, rebuilds the accepted language/book/edition views, validates the search stream and reader, and stages the static reading pages and sitemap. Invalid input stops publication; a failed GitHub build leaves the previously deployed website available. These checks establish software and source-preservation behavior, not independent scholarly certification.
