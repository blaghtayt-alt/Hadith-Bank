# Hadith Bank — multilingual hadith texts and source books

**Sunni hadith texts, translations and source books in Arabic, Bengali, Chinese, English, Filipino, Hindi, Japanese, Persian, Urdu, Uzbek and Vietnamese.** Search a quotation, browse a collection or source edition, and download preserved source files or separately identified extracted text where available. Each record keeps its own source reference, translation origin and provenance.

## Read, search and find a book

### [Search Hadith Bank](https://blaghtayt-alt.github.io/Hadith-Bank/)

[![Website build](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml/badge.svg)](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

[Browse languages and books](https://blaghtayt-alt.github.io/Hadith-Bank/browse/) · [Book titles, editions and downloads](catalog/BOOKS.md) · [Current counts](browse/README.md) · [Source catalog](catalog/README.md) · [Reader and offline use](#read-and-search-offline) · [Books being prepared](#books-being-prepared) · [Detailed active-books audit](reports/ACTIVE-BOOKS-AUDIT-2026-11-14.md)

| Language | Read online | Read in this repository |
| --- | --- | --- |
| Arabic — العربية | [الأحاديث العربية](https://blaghtayt-alt.github.io/Hadith-Bank/browse/ar/) | [Arabic records](browse/ar/README.md) |
| Bengali — বাংলা | [বাংলা হাদিস](https://blaghtayt-alt.github.io/Hadith-Bank/browse/bn/) | [Bengali records](browse/bn/README.md) |
| English | [Hadith in English](https://blaghtayt-alt.github.io/Hadith-Bank/browse/en/) | [English records](browse/en/README.md) |
| Japanese — 日本語 | [日本語のハディース](https://blaghtayt-alt.github.io/Hadith-Bank/browse/ja/) | [Japanese records](browse/ja/README.md) |
| Chinese — 中文 | [中文圣训](https://blaghtayt-alt.github.io/Hadith-Bank/browse/zh-CN/) | [Chinese records](browse/zh-CN/README.md) |
| Persian — فارسی | [احادیث فارسی](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fa/) | [Persian records](browse/fa/README.md) |
| Filipino / Tagalog | [Hadith sa Filipino](https://blaghtayt-alt.github.io/Hadith-Bank/browse/fil/) | [Filipino records](browse/fil/README.md) |
| Vietnamese — Tiếng Việt | [Hadith tiếng Việt](https://blaghtayt-alt.github.io/Hadith-Bank/browse/vi/) | [Vietnamese records](browse/vi/README.md) |
| Urdu — اردو | [اردو احادیث](https://blaghtayt-alt.github.io/Hadith-Bank/browse/ur/) | [Urdu records](browse/ur/README.md) |
| Uzbek — O‘zbekcha | [O‘zbekcha hadislar](https://blaghtayt-alt.github.io/Hadith-Bank/browse/uz/) | [Uzbek records](browse/uz/README.md) |
| Hindi — हिन्दी | [हिन्दी हदीस](https://blaghtayt-alt.github.io/Hadith-Bank/browse/hi/) | [Hindi records](browse/hi/README.md) |

The [generated language index](https://blaghtayt-alt.github.io/Hadith-Bank/browse/) and [material catalog](catalog/materials.json) show the latest built corpus. New languages appear automatically when their owner-authorized registrations pass the build checks. Language-index counts use each occurrence’s primary registration language; multilingual records can also contain Arabic, English, Urdu, Bengali and other supplied readings in their language panels. A primary-language bucket is not the total coverage of that language.

The interactive reader searches narration text and supplied references, with language, collection, source-edition and translation-origin filters. Arabic and English counterparts are available where a supported source match exists. Their coverage is recorded separately; an available counterpart does not imply a complete Arabic or English edition of every book.

Use **Arabic & English availability** to select stored bilingual text, English source-page links, or occurrences still awaiting one or both languages. The [book-by-book availability report](reports/counterpart-availability.md) counts Arabic text, English text, external links and missing languages independently. Arabic already present in a book remains available even when its English counterpart is unresolved.

The [12 November Arabic/English continuation audit](reports/counterpart-continuation-2026-11-12.md) records the newly checked source matches, exact-version English content holds and remaining coverage. Counterparts use preserved published texts; the build does not create translations.

Every registered book enters the same language-linking workflow. The build refreshes a [source-bound candidate review queue](reports/counterpart-review/manifest.json) for missing counterparts. See [Arabic/English integration and future Chinese Abū Dāwūd additions](docs/LANGUAGE-COUNTERPARTS.md) for preparing and compiling new reviewed mappings. Future installments and editions retain separate source files, numbering and occurrence identities.

The established corpus retains separate HTML reading pages with text available before JavaScript runs. New large web editions use stable occurrence links into the multilingual reader and the same language, book and edition indexes. The [sitemap](https://blaghtayt-alt.github.io/Hadith-Bank/sitemap.xml) is rebuilt with the corpus. See [search-engine discovery](docs/SEARCH-ENGINE-DISCOVERY.md) for the design and indexing setup.

Deen Hindi, Hadis.islom.uz and the selected Hadis.uz Tirmidhi source use resumable queues, language-specific references and collapsible comments. **Rivoyat is excluded by the owner and its intake is disabled.** See the [multilingual import framework](docs/MULTILINGUAL-WEB-IMPORTS.md), [Hadis.uz scope](docs/HADISUZ-IMPORT.md) and [current repository intake status](imports/web-import-status.json). Started intake does not establish complete source coverage.

## Coverage and recent additions

**Status audit: 14 November 2026 (Japan time).** The figures below are dated checkpoints. Acquisition, classification, registration, generated catalogs and deployment have separate evidence; an ongoing import can advance before the next reader build. The [detailed active-books audit](reports/ACTIVE-BOOKS-AUDIT-2026-11-14.md) and [JSON evidence summary](reports/ACTIVE-BOOKS-AUDIT-2026-11-14.json) record exact review scopes, source revisions, report hashes and unresolved evidence gaps.

### Generated corpus snapshot

The [committed build report at the audited revision](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/reports/site-build.json) contains:

| Measure | Recorded scope |
| --- | ---: |
| Registered source occurrences in the generated reader | **101,040** |
| Primary registration languages | **11** |
| Source datasets / editions in that build | **251** |
| Build’s source revision | `3e574b9e7e4dd7cf8bc23232249004a18692c61c` |

The corresponding [website workflow](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43467374230) completed its build and Pages deployment on 14 November at 02:18 JST. Later source registrations are separate from that deployed build. Use the [latest build report](reports/site-build.json), [generated reading counts](browse/README.md) and [workflow history](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml) for subsequent revisions.

These counts describe preserved **source occurrences**, not unique canonical hadiths, every language field, or independently authenticated narrations. A reviewed reader group can show several source versions together while retaining their individual records and provenance.

### Recent registered editions and recovery

| Addition | Registered scope | Evidence and qualifications |
| --- | --- | --- |
| **諸々の徳（ハディース集）② — Kitab al-Fadael**, Japanese | **57 new source occurrences** from the 25-page source; Japanese generated total **3,463 → 3,520** | All 57 have reviewed links to existing reader groups, adding **zero ungrouped reader cards**. Original/corrected text and all source IDs remain distinct. Two revised/restored readings explicitly retain AI-assisted translation labels. [Source, corrections and grouping](docs/JAPANESE-FADAEL-QC.md) |
| **伊本·马哲圣训集 — Sunan Ibn Majah**, Chinese | **4,354 source occurrences**, 39 source chapters | Source numbering restarts by chapter; it is not a global canonical number. Original PDF and correction evidence are preserved. [Source and import scope](docs/CHINESE-IBN-MAJAH.md) |
| **Four Japanese research sources** | **1,226 occurrences**: ムスリムの砦 / Hisn **261**; イスラームのメッセージ **306**; イスラームの基本知識 **650**; 大塚マスジド khutbah summary **9** | Owner-authorized pending-review reader subset; the full 1,889-record source and excluded context remain preserved. Source and counterpart qualifications continue to apply. [Source-by-source accounting](docs/JAPANESE-RESEARCH-V3.md) |
| **Hisnul Muslim — KUTANG-TANGGULAN NG MUSLIM**, Filipino | **298 reader occurrences** from **323 preserved source records** | Active owner-authorized import. Non-narration material and five unresolved-attribution records remain separate; earlier review history is preserved. [Filipino source and status](docs/FILIPINO-HISN.md) |
| **Fawaz Arabic / English / Urdu / Bengali editions** | **31 of 31 edition files**, **8 collections**, **36,226 registered provider occurrences** | All **36,464 provider identities** are accounted for. The former 244-case cohort became six additional registrations and **238 resolved source-only records**; unresolved source dispositions are **0**. Review of individual sibling-language fields remains separate. [Progress](imports/web-fawaz-20261112/progress.json) · [Import scope](docs/FAWAZ-BULK-IMPORT.md) |

Fawaz covers Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasai, Ibn Majah and Malik in the four configured languages, plus Nawawi in Arabic, English and Bengali. Its pinned catalog supplies **no Urdu Nawawi or Hindi edition**. The 238 source-only records comprise **67 commentary/discussion items and 171 source gaps**; they remain preserved with their dispositions. “All edition files acquired” and “all source identities classified” do not certify every translation, language boundary, chain or grade. Separate sibling-language semantic review remains; its current remaining-field count was not revalidated in this audit. The older 6,112-field figure belongs to a historical review cohort and is not presented as a current total.

### Website acquisition and review queues

This table is pinned to [saved repository revision `0d2fa4e`](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/imports/web-import-status.json). Check the [current status file](imports/web-import-status.json) for later batches.

| Source | Saved source entries | Registered occurrences | Awaiting classification | Preserved source-only | Remaining acquisition / coverage |
| --- | ---: | ---: | ---: | ---: | --- |
| **Deen Hindi** | **17,627** | **17,301** | **166** | **160** | **18,763 entry pages** remain from the observed 36,390-entry inventory. All **1,000 historical-error identities** are resolved; historical retries pending: **0**. |
| **Hadis.islom.uz** | **8,625** | **8,622** | **0** | **5 primary entries** | One section remains unavailable with HTTP 500; source coverage reconciliation remains. |
| **Hadis.uz — Tirmidhi** | **607** | **606** | **0** | **1** | The observed public queue is complete; this is not a claim of exhaustive historical collection coverage. |

Hadis.islom.uz’s registration count includes **8,620 accepted primary entries plus two separately extracted commentary occurrences**, so it is not a simple subtraction from the primary-entry inventory. Deen Hindi’s new saved batches can produce new review items even after an earlier held cohort is resolved. Neither queue completion nor registration is independent source certification. [Detailed recovery and remaining review](docs/WEB-SOURCE-RESOLUTION-20261113.md)

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

Different narrations, chains, repeated source occurrences, translations and editions remain distinct. Counts are **source occurrences**, including explicitly labeled excerpts, variants, Companion/Successor reports, attributed sayings and fragments; they are not unique canonical hadith totals. Source-local numbers, provider entry IDs and canonical collection numbers remain separate. Reviewed reader grouping is an additional presentation layer: it does not delete duplicate-looking source records or transfer an edition’s identity to another.

## Books being prepared

These are separately saved extraction and review projects, **outside the registered corpus at this audit**. Their checkpoint counts are not added to the Bank or website totals. Existing quotations or another edition of the same title do not establish that these working packages have been imported.

| Book and language | Latest inspected checkpoint | Saved progress | Remaining work |
| --- | --- | --- | --- |
| **Mukhtasar Sahih Bukhari — Hindi**, three volumes | `HI_MSB_3V_v0.7.10-QC10` | Initial transcription and a scoped image-comparison pass cover **1,921 pages**, **2,230 numbered occurrences** and **4,460 Arabic/Hindi rows**. | Retained local source readings and independent proofreading remain. The checkpoint records **0 certified-verbatim records**, **0 fully glyph-verified pages** and independent professional proofreading pending. |
| **Mishkat al-Masabih — Urdu**, five volumes | `UR_MISHKAT_172207_v0.14.0` | Initial text for **2,790 pages**; **1,874 image drafts** and **683 separate-author model full-page comparison attempts**. | **2,107 pages** have no full-page comparison attempt. The **1,514 occurrence fragments** remain uncertified, including **460 incomplete boundaries**; no fully character-verified pages or Bank-ready status is claimed. |
| **Al-Adab al-Mufrad — Urdu** | `UR_ADAB_MUFRAD_20261113_v0.2.0-pre.18` | Candidate comparison attempts cover all **372 physical pages**. The latest 400-event patch includes focused revisits. | **26 pages** currently have full character self-review credit; **346 complete-page character reviews** remain. Independent source QC covers **0 pages**. **2,777 tasks** remain across source readings, annotations, metadata and review; task categories overlap. |
| **Riyadh al-Salihin — Bengali**, two volumes | `v2_cp017_patch08` | **2,029 source occurrences / 11,484 source units** preserved; character-review attempts cover **2,054 pages**, with **2,053 marked full** and one localized glyph partial. Scoped independent patch QC passed after corrections. | Retain **32 investigated source limitations** and the glyph partial. A package-aware adapter and local reader validation are still required; the checkpoint records **no Bank upload or registration**. |

The table summarizes the saved packages’ own evidence; this README audit performed no new page proofreading. A comparison attempt, full author review, scoped independent patch QC and whole-book certification are different measures. In particular, Bengali patch QC does not claim an independent reread of all 2,054 pages, and Mishkat fragments are not complete verified hadith entries. Mishkat’s separate-author comparisons are model reviews; the checkpoint does not claim human or professional proofreading. The five-volume Urdu project is this same UM172207 Mishkat package. HI_MSB identifies the Hindi Zubaydi abridgment of Sahih Bukhari, not Mishkat.

Checkpoint evidence is maintained with those separate working packages: `HI_MSB_3V_v0.7.10_QC10_RESUME.json`, `UR_MISHKAT_172207_v0.14.0_COVERAGE.json`, `UR_ADAB_MUFRAD_20261113_v0.2.0-pre.18_CHECKPOINT_REVIEW_SUMMARY.json`, and the `v2_cp017_patch08` `REPORT.md`. The first was saved on 14 November JST; the other three on 13 November JST. These filenames identify resumable work, not public downloads from this repository.

Eight further Hindi, Bengali and Urdu books appear in an older tracker: Hindi 300 Hadith, Hindi Selected Hadith Encyclopedia, Hindi Hisn, Bengali Qudsi, Bengali Hisn, the five-volume Bengali Selected Hadith series, Urdu Diya-e-Nabawi Nawawi Forty and Urdu Hisn. Their latest primary checkpoint bytes could not be inspected, so the [historical tracker table](reports/ACTIVE-BOOKS-AUDIT-2026-11-14.md#other-tracker-listed-books) retains the 13 November, 10:43 JST snapshot with current progress explicitly unknown. No source-specific registration for these eight packages was found at the audited Bank revision.

Older saved reports also cover **Portuguese Sahih al-Bukhari volume I** (`pt_bukhari_v1`, 9 November) and **Portuguese Riyadh al-Salihin, SBMRJ** (`pro_qc_v2`, 11 November). Bukhari I reports scoped image review of 914 pages and 2,970 source report rows, with character-review limits. Riyadh retains 821 pages and 1,869 occurrences with source fidelity PARTIAL and Bank readiness FAIL. Their [separate backlog evidence](reports/ACTIVE-BOOKS-AUDIT-2026-11-14.md#older-portuguese-backlog) does not establish recent continuation or publication; no Portuguese source-specific registration was found at the audited revision. Completion of Bukhari volumes II/III is not claimed.

Current priorities are to finish the bounded Hindi queue and language-field reviews, reconcile the remaining Uzbek source gap, prepare these book-specific adapters after their required review work, and resolve evidence-supported Arabic/English counterparts. Source uncertainties and original wording remain explicit throughout.

<a id="download-original-books"></a>

## Download original sources and extracted text

Open the [book catalog](catalog/BOOKS.md) for separate **Extracted text**, **Original source (PDF)** and **Other source formats** columns. **Extracted text (Word)** identifies a preserved extracted or corrected Word document; any generated PDF stays in the extracted-text column. **Original source (PDF)** links the exact preserved source-input PDF for that edition or volume. **Supplied source (Word .doc/.docx)** retains an actual Word input under Other source formats. Where no exact original PDF is linked, the table says **Original PDF unverified**.

A book’s online edition page, **Browse available materials → Download books and source materials** in the interactive reader, and applicable narration pages also link to the preserved source inputs.

Examples:

- 穆宛塔圣训集 — Muwatta: [original Chinese Word document (.docx)](https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/materials/zh-muwatta-shaybani-yu-2000-docx/穆宛塔圣训集_Muwatta_Chinese.docx).
- 艾布达吾德圣训 — Sunan Abī Dāwūd: [original Chinese Word document (.doc)](https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/materials/zh-abu-dawud-yu-2002-doc/艾布达吾德圣训_Sunan_Abi_Dawud.doc).
- 穆斯林的堡垒 — Hisn al-Muslim: [original Chinese PDF](https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/materials/zh-cn-hisn-muslim-1a09ee75/zh-hisn.pdf), with [preserved final data and evaluation](docs/CHINESE-HISN.md).
- Persian books: original `.docx` files linked from the [book catalog](catalog/BOOKS.md) and preserved in their [material folders](materials/).
- Japanese and Vietnamese PDF sources: preserved in the [Japanese package](attachments/attachments-ja-muslim-c859ce57c211ea1b/) and [Vietnamese package](attachments/attachments-vi-920394517894aea9/).

Preserved source downloads keep the supplied file format and original bytes. The Persian DOCX inputs are supplied Word sources, not generated Word exports. A publisher PDF candidate is not substituted for an unverified edition, and a converted or corrected PDF is not labeled as an original. Extracted downloads retain their recorded corrections, attribution and review limits; their notes do not establish a new source review. “Not linked” does not mean that extraction never occurred. The hosted reader loads its searchable data from local site shards; original-book downloads use GitHub. A full downloaded repository retains the local source files and reader data. See [offline use](#read-and-search-offline) for the complete required files. Availability does not grant a new redistribution license; source-specific reuse conditions and unassessed rights remain recorded.

## Source text, attribution and review

This is a standalone bank. Canonical JSON/JSONL records, original sources, page and paragraph locators, review history, catalogs and search tools are kept here. The hosted reader loads checksum-verified data shards from the same site as needed; it does not query Iman Companion or an external Hadith service at reading time. An explicitly built standalone reader embeds its data instead. [Current reader delivery](docs/READER-DEMAND-LOADING.md)

Arabic, translation, collection and number, narrator/isnad, translator, source locators, tags, commentary, footnotes, references and grading remain separate fields. Missing original Arabic and unsupported metadata remain null or unknown. Source-text anomalies and different publisher versions are preserved and qualified, rather than silently corrected or merged.

The reader uses **Human**, **AI** and **Unknown** translation-origin labels. Under the owner’s current rule, **all newly added books and separately acquired English counterparts are Human unless their own source explicitly states otherwise**. **Unknown is reserved for copied old-bank resources**, including quotations extracted from old Iman/Qur’an-study material. An explicit source declaration of AI translation is retained and displayed as AI. OCR, AI extraction, AI review and an unnamed translator do not make a new book’s translation Unknown. The [source-origin policy](catalog/provenance-policy.json) and each material’s provenance retain the current decision separately from historical source flags. Arabic originals do not receive a translation-origin label.

**QC labels apply to evidenced OCR materials, subject to recorded source-specific owner display decisions.** Website imports, native PDF text and structured quotation extractions do not receive generic pending-QC badges. Historical review fields and genuine source-alignment or attribution qualifications remain available. Public availability, a Human label or a linked Arabic/English counterpart does not certify transcription, translation, canonical identity or scholarly authenticity.

[Current review policy](docs/CURRENT-REVIEW-POLICY.md) · [Translation-origin evidence](catalog/translation-origins.json) · [Contributor requirements](AGENTS.md) · [Rights and review](docs/REVIEW-AND-RIGHTS.md)

### Quotations extracted from lessons and Qur’an books

Explicitly bounded quotations from the selected older-bank and Qur’an-study sources have individual records, organized by the cited collection and number when supplied. The original documents remain available as evidence. Quotations, reported meanings and Companion reports are labeled separately. Qur’an passages and editorial explanations remain separately classified. Within the owner-authorized numbered-collection scope, source-bound Companion/Successor reports, historical reports and attributed sayings may be registered under their actual type and speaker. Unrelated historical prose, proverbs and editorial comments in legacy lessons remain source context. A non-Prophetic speaker’s words are never relabeled as the Prophet’s words.

[Extraction scope, evidence and validation](docs/LEGACY-EXTRACTION.md) documents quotation boundaries, source snapshots, mirror handling and remaining limitations. Source references are not silently promoted to verified canonical numbering. Some earlier supplied-file datasets remain metadata-only; the [material catalog](catalog/materials.json) marks availability, and those datasets do not enter the searchable-record total.

## Add material and update the website

1. Create an owner-authorized folder under `materials/` containing structured narration records and the original source file.
2. Follow [Adding material](docs/ADDING-MATERIAL.md) to register its language, book, edition, source, record count and file hashes in `manifest.json`.
3. Commit the folder to GitHub and merge it into `main`. The **Update Hadith Bank website** workflow validates the data, rebuilds catalogs and reading/search pages, and deploys the site.

The same build updates the language and book indexes, individual HTML pages, book-download catalog and sitemap. Do not edit generated narration pages or add language options by hand. JSON arrays and JSONL are supported. A PDF alone supplies evidence; searchable narrations also need structured text records. The build does not create a new translation or perform a scholarly review.

**The hosted site updates after a successful build and deployment of `main`.** A saved offline copy remains a snapshot. Refresh the complete reader/data copy or rebuild a standalone export to receive later additions.

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
| Hosted reader shell and checksum-verified data shards | `hadith-bank-reader.html` + `hadith-bank-reader-data/` |
| Optional standalone offline export | Built with `scripts/build_reader.py` without external-data options |
| Dated active-book, review and intake evidence | `reports/ACTIVE-BOOKS-AUDIT-2026-11-14.md` and its JSON companion |

The workflow builds `_site/` as the deployment artifact. Its individual HTML pages are generated from the accepted data rather than maintained as thousands of additional source files in Git. Existing source paths and occurrence IDs remain stable.

## Read and search offline

**The current hosted `hadith-bank-reader.html` is a reader shell, not a complete one-file corpus.** Keep it together with the matching `hadith-bank-reader-data/` directory. From a downloaded repository, serve that local copy:

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Open [the local reader](http://127.0.0.1:8000/hadith-bank-reader.html). Its data stays on your computer; original-book or external-reference links still need their saved files or an internet connection. Preserve the shell and data from the same build so their hashes agree.

A separate self-contained export is supported:

```bash
python scripts/build_reader.py --root . --output hadith-bank-offline.html
```

Open that generated file directly. Add `--uncompressed` for a browser without built-in gzip decompression. A whole-corpus embedded export can be large; the sharded local copy loads records as needed. A **Download offline reader** link is only available when that build supplies a separate offline artifact. [Reader loading and preservation](docs/READER-DEMAND-LOADING.md) · [Detailed offline-use instructions](docs/WEBSITE.md#offline-use)

For command-line text search, Python 3.11 or later is sufficient; the search tools use the standard library.

```bash
python scripts/hadith_search.py '礼拝' --language ja --limit 5
python scripts/hadith_search.py --language ja --book muslim --limit 5
python scripts/hadith_search.py --language vi --book bukhari --limit 5
python scripts/search.py fulltext '2758' --language ja --limit 5
```

The browser reader searches the same corpus, including supplied language panels and their references, and exports selected records as JSON. For a question such as “Which reports discuss prayer?”, start with words from the source language, for example `prayer` or `礼拝`, then narrow the language, collection and edition filters. Search matches stored text and references; search-key normalization does not alter displayed wording. [Search field guide](docs/READING-AND-SEARCH.md) · [Search record schema](schemas/search.record.schema.json).

## Rebuild and validate

```bash
python scripts/refresh_bank.py --root . --site-output _site
python -m unittest discover -s tests
node --test tests/test_lazy_store.js
```

The refresh command verifies canonical files and hashes, rebuilds the accepted language/book/edition views, validates the search stream and reader, and stages the static reading pages and sitemap. The full reader build also uses Node.js for its search projections. The website workflow adds browser verification before deployment. Invalid input stops publication; a failed GitHub build leaves the previously deployed website available. These checks establish software and source-preservation behavior, not independent scholarly certification.

