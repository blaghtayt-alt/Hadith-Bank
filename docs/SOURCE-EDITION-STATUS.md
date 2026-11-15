# Global Hadith Library — book editions, source descriptions and statuses

**Verified generated snapshot: 15 November 2026.** [Main `bc0ef56b2358`](https://github.com/blaghtayt-alt/Global-Hadith-Library/commit/bc0ef56b2358e20f425e961f0bac6511f30fed20) contains reader outputs sourced from [`9d8db54e0d8a452b967a469c43851780b23245ea`](https://github.com/blaghtayt-alt/Global-Hadith-Library/commit/9d8db54e0d8a452b967a469c43851780b23245ea).

Global Hadith Library emphasizes **non-Arabic/non-English texts**—Bengali, Chinese, Filipino, Hindi, Japanese, Persian, Urdu, Uzbek and Vietnamese. **Arabic and English remain included** as their own registered editions, reference readings, `language_versions` and searchable counterparts. This is an edition-based corpus, not a claim about unique canonical narrations, global ranking, entire book coverage, scholarly authentication or completed QC.

[Full generated book-and-download directory](../catalog/BOOKS.md) · [Source-by-source registered catalog](../catalog/README.md) · [Evidence ledger](DOCUMENTATION-EVIDENCE-2026-11-15.md)

## Primary-registration language counts

| Language | Source occurrences | Read edition index |
| --- | ---: | --- |
| বাংলা — Bengali | 44 | [Browse](../browse/bn/README.md) |
| فارسی — Persian | 14,382 | [Browse](../browse/fa/README.md) |
| Filipino / Tagalog | 2,354 | [Browse](../browse/fil/README.md) |
| हिन्दी — Hindi | 30,919 | [Browse](../browse/hi/README.md) |
| 日本語 — Japanese | 3,520 | [Browse](../browse/ja/README.md) |
| اردو — Urdu | 231 | [Browse](../browse/ur/README.md) |
| O‘zbekcha — Uzbek | 9,780 | [Browse](../browse/uz/README.md) |
| Tiếng Việt — Vietnamese | 4,555 | [Browse](../browse/vi/README.md) |
| 简体中文 — Chinese | 10,835 | [Browse](../browse/zh-CN/README.md) |
| العربية — Arabic (reference) | 32,267 | [Browse](../browse/ar/README.md) |
| English (reference) | 3,684 | [Browse](../browse/en/README.md) |
| **Total** | **112,571** | [Browse all](../browse/README.md) |

The **nine non-Arabic/non-English primary-language buckets contain 76,620 occurrences**, but this is *not* a count of available non-Arabic/non-English `language_versions`. A record with Arabic as its primary registration can have Urdu or Bengali text, and a Hindi record may have Arabic/English text. The [Arabic/English field-availability report](../reports/counterpart-availability.md) counts stored text and external source-only links separately.

## All registered source families

The following **15 disjoint source families exhaustively account for all 255 published dataset/partition rows** and 112,571 occurrences in the generated catalogs; every specific edition/part and its recorded book title is individually linked in [BOOKS.md](../catalog/BOOKS.md). Storage partitions do not necessarily correspond to whole source books.

| Recorded source family | Dataset or storage-part rows | Registered occurrences | Scope and source format |
| --- | ---: | ---: | --- |
| HadeethEnc publisher SQLite snapshots | 6 | 8,423 | Six named original language snapshots; source IDs and languages preserved. |
| Deen Hindi website | 17 | 28,335 | Seventeen Hindi storage partitions, not seventeen complete books; acquisition backlog separate. |
| Persian *Faiz al-Bari* (Mukhtasar Bukhari) | 6 | 2,627 | Six original source DOCX volumes of an abridgment, not full Sahih al-Bukhari. |
| Persian *Mukhtasar Sahih Muslim* (al-Mundhiri/Tarshabi) | 2 | 2,232 | Two supplied DOCX source volumes of a specific abridgment. |
| Persian *Riyadh al-Salihin* (Heravi) | 1 | 1,946 | Original DOCX source; exact Heravi edition/credits preserved. |
| Persian *Targhib wa Tarhib* (Bazmandegan) | 3 | 7,304 | Three original DOCX volumes; source narrations/commentary kept distinct. |
| Fawaz Ahmed Hadith API | 43 | 36,226 | 31 pinned edition JSON files from eight selected collections, stored in 43 parts; multilingual versions inside records. |
| Filipino *KUTANG-TANGGULAN NG MUSLIM* / Hisn | 1 | 298 | One original PDF; 323 preserved source records versus 298 registered occurrences; holds kept. |
| Hadis.uz Uzbek Tirmidhi | 1 | 606 | Publisher-specific web intake, not proven full collection. |
| Hadis.islom.uz Uzbek sources | 11 | 8,622 | Eleven publisher-book partitions; separately extracted commentary counted distinctly. |
| Japanese research PDFs and *Fadael* II | 5 | 1,283 | Four research selections (1,226) plus Fadael II (57); review boundaries preserved. |
| Japanese Muslim vol. I and Vietnamese PDFs | 46 | 5,065 | Japanese volume-one PDF 1,811 plus 45 Vietnamese source PDF parts 3,254; not entire source collections. |
| Old-bank lessons and article quotations | 49 | 867 | Source-bounded quotations, not complete cited collections; translation-origin limitations. |
| Qur’an-study quotations | 60 | 298 | Attributed sayings/quotations from study texts; commentary not relabeled Prophetic. |
| Chinese original PDF / Word sources | 4 | 8,439 | Partial Abu Dawud, Hisn al-Muslim, 2013 Ibn Majah, al-Shaybani Muwatta; preserve each input format. |
| **All registered rows** | **255** | **112,571** | Not unique or authenticated narrations. |

The separate [registration index](../catalog/registered-materials.json) accounts for **205 manifests, 249 material datasets and 104,148 occurrences**. Six original HadeethEnc publisher datasets add **8,423**: `249 + 6 = 255`; `104,148 + 8,423 = 112,571`. The **83 preserved legacy source documents** and privately held datasets are not added to reader occurrence totals.

## Edition-specific descriptions and downloads

| Actual book or source edition | Edition/source identity and format | Registered scope, interpretation and limitations |
| --- | --- | --- |
| Chinese **伊本·马哲圣训集** | **2013 PDF**, translator **穆萨·余崇仁** | **4,354** occurrences, 39 chapters, chapter-local numbering (not invented global numbers). [Source evidence](CHINESE-IBN-MAJAH.md) |
| Chinese **艾布达吾德圣训** | Explicitly **partial** Abu Dawud, original **Word .doc** | **2,828** occurrences. Do not replace the Word input with a different PDF edition. |
| Chinese **穆宛塔圣训集** | **al-Shaybani recension**, supplied **Word .docx** | **1,006** occurrences, not interchangeable with other Muwatta recensions. |
| Chinese **穆斯林的堡垒** | Hisn al-Muslim supplied **source PDF** | **251** reader quotations/reports; non-hadith content/source limitations retained. [Review and file](CHINESE-HISN.md) |
| Japanese **Sahih Muslim**, volume one | One supplied original **PDF** | **1,811** occurrences; not the complete Muslim collection. |
| Four Japanese research sources | Hisn **261**, Message of Islam **306**, Basic Knowledge **650**, Otsuka khutbah **9** | **1,226** selected occurrences versus **1,889** preserved source records. [Source accounting](JAPANESE-RESEARCH-V3.md) |
| Japanese **諸々の徳（ハディース集）②** | Distinct 25-page Fadael PDF edition | **57** occurrences; two explicitly AI-assisted readings remain labeled, correction/review limits retained. [Evidence](JAPANESE-FADAEL-QC.md) |
| Filipino **KUTANG-TANGGULAN NG MUSLIM** | Identified Hisn source **PDF**, third edition | **298** reader occurrences from **323** original source records; attribution holds/source-only entries remain separate. [Status](FILIPINO-HISN.md) |
| Vietnamese Bukhari, Muslim, Abu Dawud, *200 Golden Hadith* | Original supplied **PDF booklets/parts** | **3,254** occurrences from 45 source-specific parts. No entire-book claim. |
| Persian **Faiz al-Bari / Mukhtasar Bukhari** | Six supplied original **DOCX** source volumes | **2,627** occurrences of an abridgment; not unabridged Sahih al-Bukhari. [Source guide](PERSIAN-DOCX-IMPORT.md) |
| Persian **Mukhtasar Sahih Muslim** | Two original **DOCX** volumes, al-Mundhiri / Tarshabi edition | **2,232** occurrences; its own abridged source edition. |
| Persian **Riyadh al-Salihin** | Source-specific original **DOCX**, Heravi translation/edition | **1,946** occurrences; credits do not transfer to other editions. |
| Persian **Targhib wa Tarhib** | Three supplied original **DOCX** volumes, Musa Bazmandegan edition | **7,304** occurrences; hadith report text distinct from commentary. [Source guide](PERSIAN-TARGHIB.md) |

In [the download table](../catalog/BOOKS.md), **Extracted text (Word/PDF)** means a documented derivative with its own corrections, while **Original source (PDF)** means the actual preserved PDF input for that edition. **Supplied source (Word .doc/.docx)** is an original Word input, **not** an extracted Word output. If an exact edition's source PDF is not linked, it stays **Original PDF unverified**; a different publisher PDF, derived PDF or Word input is not silently substituted.

## Fawaz publisher catalog versus actual Bank editions

The registered source uses [Fawaz Ahmed Hadith API's pinned `df57907be352...` commit](https://github.com/fawazahmed0/hadith-api/tree/df57907be35291c91ad6a6691180e22ca9920784). The Bank contains **31 acquired Arabic/English/Urdu/Bengali edition JSON files** across eight selected collections, registered as **43 storage partitions and 36,226 provider occurrences**. Some stored source records carry multiple `language_versions`. A provider entry number or matching wording is **not** proof of cross-publisher or globally canonical narration identity.

The independently read [pinned Fawaz `editions.json`](https://github.com/fawazahmed0/hadith-api/blob/df57907be35291c91ad6a6691180e22ca9920784/editions.json) lists **74 upstream edition entries**, **10 collections**, **nine languages**: Arabic 20, English 10, **French 9, Indonesian 7, Russian 3, Turkish 8, Tamil 2, Bengali 8, Urdu 7**. The last seven languages total **44 non-Arabic/non-English upstream catalog entries**. They **include some editions already registered** and are **neither 44 approved imports nor evidence that all are missing**. A separate owner handles their source-by-source reconciliation. [Current pinned import/hold distinctions](FAWAZ-BULK-IMPORT.md).

Deen Hindi, Hadis.islom.uz, Hadis.uz, Fawaz and HadeethEnc preserve **different provider/project identities**. Institution/provider attribution is not proof of a personally named human translator. If a translator, exact Arabic counterpart or independent grade is unknown, retain the explicit unknown, source wording and source-only references. The owner-excluded **Rivoyat** remains excluded.

## Status, review and historical limits

**Acquired** means saved source material; **registered** means a source occurrence accepted into a Bank dataset; **generated** means that a specified build includes it; **workflow deployed** means that Pages reported a successful publication job; **live verified** requires directly checked current HTTP asset bytes; **QC reviewed** applies only to the exact source text and pages that were actually inspected. None of these states implies the others. Multiple source occurrences can form one reader card without merging original records or changes to narrator/chain identities.

A [15 November main workflow](https://github.com/blaghtayt-alt/Global-Hadith-Library/actions/runs/43678731786) successfully completed its build and Pages publication jobs for source commit `9d8db54e...`. **Direct verification of the live site's current asset revision was unavailable**, so the current HTTP site binding is **unknown**, not assumed from main. The [14 November active-books audit](../reports/ACTIVE-BOOKS-AUDIT-2026-11-14.md) remains a **dated checkpoint** for locally held Hindi, Urdu, Bengali and Portuguese books; their saved work packages are not added to today's registered counts without source-specific registration evidence.

Translation-origin display labels **Human / AI / Unknown** follow the preserved owner policy and explicit source exceptions; a Human display label alone does not prove a named translator or independent translation fidelity. Copied legacy material keeps its Unknown classification, documented AI exceptions are visible, and OCR extraction is not itself AI translation. No source's QC state, release flag, original text, per-edition variant, page number, translator credit or source-only hold is changed by this description. [Provenance](../catalog/provenance-policy.json) · [Review policy](CURRENT-REVIEW-POLICY.md).

## Offline reading

The generated `hadith-bank-reader.html` is a **shell, not a one-file offline corpus**. Keep the matching `hadith-bank-reader-data/` directory, run `python -m http.server 8000 --bind 127.0.0.1` from the repository root, then open `http://127.0.0.1:8000/hadith-bank-reader.html`. A separately generated fully embedded standalone export differs from the hosted shell; opening the shell via `file:` does not load its shards. [Complete instructions](WEBSITE.md#offline-use).
