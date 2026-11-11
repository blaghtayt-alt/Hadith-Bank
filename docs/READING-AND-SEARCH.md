# Reading and searching the bank

## Choose an entry point

Use **Show Arabic text** and **Show English text** to add available counterparts while keeping the original narration visible. Arabic/English keywords and collection-number references are searchable even when these displays are closed. See [automatic counterparts and coverage](ARABIC-ENGLISH-COUNTERPARTS.md).

- **[Live reader](https://blaghtayt-alt.github.io/Hadith-Bank/):** select a language to see its available collections, source editions and copied-bank documents. Search, narrow the translation origin, and read the full indexed source text.
- **[Readable pages](../browse/README.md):** translations and Arabic in normal paragraphs, with source, translator/process label, page/row locator and optional audit details. The [Japanese public collection](../browse/ja/README.md) includes HadeethEnc, Sahih Muslim volume one, and the newly extracted old-bank/Qur’an-book quotations.
- **[Materials catalog](../catalog/README.md):** all registered datasets and 83 preserved legacy source documents. Original lessons remain available alongside their individually indexed quotation records. Document totals are counted separately from quotation occurrences.
- **Offline HTML:** download [hadith-bank-reader.html](../hadith-bank-reader.html), then open it locally. Rebuild all current views with `python scripts/refresh_bank.py --root . --site-output _site`. Search/filtering and JSON export work without a server or network. A downloaded HTML is a snapshot; download it again to receive later additions. The compressed edition needs a browser with the built-in `DecompressionStream` API; add `--uncompressed` when using `scripts/build_reader.py` for an older browser.
- **Python search:** `python scripts/hadith_search.py '行い' --language ja --limit 5`. It prints readable results by default; `--json` returns structured JSON.

The original structured publication contained **13,488 source occurrences**: 8,423 HadeethEnc entries, 1,811 Japanese Sahih Muslim volume-one entries, and 3,254 Vietnamese entries. The current bank adds bounded quotation records from the older banks and Qur’an-study sources, and includes **Persian** as a seventh language. See the [generated language index](../browse/README.md) for current totals and the [extraction report guide](LEGACY-EXTRACTION.md) for the additional scope. These totals count source occurrences, including partial quotations and distinct appearances in lessons; they do not count unique canonical Hadith.

The earlier, separately held combined package contains **45,788 occurrences in nine languages**, including another 32,300-record intake. That historical package has a different scope; the additional 32,300 records are not included in this public release. See [additional intakes](ADDITIONAL-INTAKES.md) for the current publication status and exact package paths.

## JSON is the main data format

| Layer | Location | Purpose |
| --- | --- | --- |
| Canonical source records | `languages/<language>/books/<book>/editions/<edition>/records.jsonl` | Full source wording, evidence and audit fields; unchanged by view generation. |
| Registered public intake records | `attachments/attachments-ja-muslim-c859ce57c211ea1b/` and `attachments/attachments-vi-920394517894aea9/` | Original Japanese and Vietnamese intake packages, including full structured records, source files and extraction evidence; authorized through `materials/*/manifest.json`. |
| Registered records and extracted quotations | `materials/<material-slug>/` | Original source files or exact source bundles, structured JSON/JSONL and an explicit material manifest; the refresh command discovers all accepted manifests. |
| Simplified search records | `search/<language>/<book>/<edition>/part-*.jsonl` | One flat record per source occurrence, in small ordered shards. |
| Optional whole projection | `search/records.jsonl` | Exact ordered concatenation of the shards; included in generated packages and reproducible locally. |
| Material inventory | `catalog/materials.json` | Counts, source/canonical-file checksums, availability, translation-origin evidence and search-shard manifest. |
| Human/AI provenance evidence | `catalog/translation-origins.json` | Evidence, source URLs, credit pages and the scope of each translation label. |
| Current owner-confirmed origin policy | `catalog/provenance-policy.json` | Human for the confirmed HadeethEnc and Japanese/Vietnamese website imports; Unknown for old-bank copies until explicit later confirmation. Historical metadata remains intact. |
| Related source snapshots | `catalog/related-snapshots.json` | Links the same publisher IDs across source versions without merging records or asserting canonical equivalence. |
| Language inventories | `catalog/languages/<language>.json` | Complete local dataset and legacy-document inventory for each language. |
| Disposable index | `.cache/hadith-search.sqlite` | SQLite full-text cache, rebuilt from verified JSON when needed. |

JSONL is UTF-8 JSON with **one complete object on each line**. A long line is normal and is intended for parsers. Use the reader, a JSON-aware editor or the search command for day-to-day reading. The search shards use unescaped Unicode text, separate fields and stable occurrence IDs.

The [search schema](../schemas/search.record.schema.json) defines the projection. Important fields are:

| Field | Meaning |
| --- | --- |
| `id` | Stable occurrence/revision identifier, preserved from the canonical record. |
| `language`, `source_language_code` | Bank language code and the publisher's code; for example `fil` and `tl`. |
| `book_key`, `edition`, `source_id` | Source book, source snapshot and edition-specific dataset identity. |
| `provider_entry_id` | Publisher entry ID when supplied; it is not automatically a canonical collection number. |
| `text_arabic`, `text_translation` | Exact source text; `null` means missing, with no invented substitute. |
| `number`, `narrator`, `page` | Separate source numbering, narrator/isnad fields and PDF/printed/sheet/row locators. A database row is not a printed page. |
| `source` | Publisher/title, source URL, local original-file path/hash and canonical-record locator. |
| `translator` | Named translator and evidence when the source establishes them. |
| `translation_provenance` | Display label, evidence IDs, human involvement, separate AI flag and limits of the attribution. |
| `topic_tags`, `source_headings`, `editorial_tags` | Publisher topics, supplied book headings and bank workflow labels kept in separate fields. |
| `commentary`, `benefits`, `footnotes`, `references` | Supplementary material kept outside narration text. |
| `review` | Existing review state and issues; a readable view never promotes a source to QC-passed status. |
| `extraction` | Evidence of digital text or OCR extraction. Only evidenced OCR produces normal QC labels. |
| `record_type` | Where applicable, distinguishes a Hadith excerpt, a source-reported meaning, and a Companion report. |

The view removes duplicate citation-line objects while retaining the complete bibliography; generation verifies their exact concatenation. Source-encoded benefits are decoded for display. All full original fields remain in the canonical records. No translation, paraphrase, narrator name, grade or missing Arabic was generated.

The Japanese SQLite and XLSX sources each contain the same 281 publisher IDs. The combined package preserves both source snapshots: 280 translation strings are exactly equal and one differs only in source line-ending characters. These are 281 publisher entries retained in two snapshots, not 562 different Hadiths. The same-provider-ID links and exact-string comparisons are recorded separately; none of them establish canonical narration equivalence.

## Search examples

```bash
python scripts/hadith_search.py '礼拝' --language ja
python scripts/hadith_search.py --language ja --id 2758 --json
python scripts/hadith_search.py --language ja --tag 532
python scripts/hadith_search.py 'نص' --limit 5
python scripts/hadith_search.py --translation-origin publisher_human_workflow --limit 5
python scripts/hadith_search.py '忍耐' --language ja --include-commentary
python scripts/hadith_search.py --book hadeethenc --source hadeethenc-ja-sqlite-a81da9af28f854f6
```

Normal search includes source references, translator and publisher metadata, narration text, titles, IDs, source metadata and supplied topic labels/headings. `--include-commentary` additionally searches commentary, benefits and footnotes. Language/book/source/ID/tag/origin filters are exact. Search normalization ignores Arabic vocalization and tatweel only in search keys; displayed source text remains unchanged. Japanese and Chinese one- and two-character substring searches are supported. No search result asserts canonical equivalence between snapshots.

The SQLite cache uses FTS5 trigram when available and a literal substring fallback. Every invocation verifies the input aggregate checksum/count, and resolved original source files are checked against their supplied SHA-256. The cache is an accelerator, never the authoritative text. It can be deleted and rebuilt.

The old lesson/article documents remain separately cataloged as source evidence. Their extracted quotations are searchable in the unified reader by collection, number and text. Whole-document search remains useful for the surrounding explanations and other material that is intentionally not indexed as a Hadith quotation:

```bash
python scripts/search.py fulltext '2654' --language hi
python scripts/search.py search --language ja --kind package
python scripts/search.py resolve 'package:ja:essential-01-003' --reading
```

Some preserved historical source documents contain old relative links. [The legacy-link map](LEGACY-LINKS.md) identifies available candidates from other revisions and explicitly missing targets without changing the archived document bytes. Current bank catalogs and verified local record locators provide the working navigation.

## Translation labels and sources

The reader's current origin filter uses **Human**, **AI** and **Unknown**. Under the [owner-confirmed policy](../catalog/provenance-policy.json), the original 13,488 HadeethEnc and website-sourced PDF records are Human. Copied old-bank documents and the new old-bank/Qur’an-book quotation records remain Unknown pending owner confirmation. Unknown does not mean AI. These labels do not certify independent linguistic or scholarly review.

The policy overlay is separate from the original source fields. Existing `ai_translation` values, evidence and historical origin descriptions are preserved, including an original `"unknown"` flag on a record whose current owner-confirmed display category is Human. The historical evidence categories are:

| Origin | Display meaning | AI field |
| --- | --- | --- |
| `publisher_human_workflow` | HadeethEnc's publisher describes translators, proofreading and human review. The label applies to the documented publishing process. | Preserved as `"unknown"` for these exported versions. |
| `human_translator_credited` | Human translation credits are established by the specific source, including credited Chinese, Japanese and Vietnamese editions. | Existing evidence-backed `false` retained. |
| `unknown` | Exact-source translator/process attribution has not been established. | Existing value retained; no inference from filename or PDF timestamp. |

The evidence file links to [HadeethEnc's project description](https://hadeethenc.com/ar/home/about), [the publisher's platform list](https://islamiccontent.org/) and [its translation/review workflow](https://islamiccontent.org/About). A related [AI-assisted platform](https://molhem.ai/) describes AI assistance and human review; that capability neither proves nor excludes AI use in these particular exports. Human involvement, absence of AI translation, extraction method and independent bank QC are different fields.

The verified findings, retrieval dates, exact primary URLs and PDF credit-page evidence are also preserved in a [local evidence snapshot](../sources/translation-origin-evidence/2026-11-11/evidence.json), whose checksum is pinned by the policy. This snapshot is identified as extracted findings; it does not claim to be a raw HTML archive.

For the private Chinese sources, the credited translators are **艾乃斯·马风德** for *Riyadh al-Salihin* (PDF page 12; dated afterword on page 358) and **陈克礼** for *Shengxunjing* (PDF page 2, with historical edition statements). No unverified name is supplied for the Bukhari or Muslim PDFs. The source PDFs, exact hashes, extracted credit evidence and page references remain in the private package.

## Rebuild and verify

Python 3.11 or later and its standard library are enough for the builders and search. Run:

```bash
python scripts/refresh_bank.py --root . --site-output _site
python scripts/validate_hadeethenc_public.py
python scripts/validate_bank_views.py --root . --report reports/portable-validation.json
python -m unittest discover -s tests
```

The refresh command checks registered inputs, rebuilds catalog/search/reading views and the HTML, validates them, and stages the hosted site. The [GitHub Pages workflow](../.github/workflows/reader-pages.yml) runs it for changes to `main` and publishes successful builds. Follow [Adding material](ADDING-MATERIAL.md) to register future sources; adding an unregistered PDF alone does not create structured Hadith records.

To include the separately held attachment package, supply its expanded folder and an **external empty output directory**:

```bash
python scripts/build_bank_views.py --bank-root . --attachments /path/to/hadith-bank-private-intake --output /path/to/private-combined-bank
python scripts/build_reader.py --root /path/to/private-combined-bank --output /path/to/private-combined-bank/hadith-bank-reader.html --markdown-output /path/to/private-combined-bank/browse
```

The combined package keeps the original attachment intake under `attachments/attachments-b53d154fa3622b95/`. Later intakes occupy separate roots under `attachments/` and use the additive intake adapter described in [ADDITIONAL-INTAKES.md](ADDITIONAL-INTAKES.md). Language/book/edition catalogs and reading views cover every included source family. Public/private availability, source snapshots and all review flags remain explicit.

Integration checks compare exact text/IDs and source hashes. Extraction checks also reproduce the original quotation slices and their reference evidence. They do not replace independent linguistic or scholarly review. Original review history and Arabic-alignment exceptions remain preserved; normal QC labels are limited to evidenced OCR extraction.

## Current HadeethEnc decision

The owner waived separate bank review for HadeethEnc and requested OCR-only QC labels in the reader. Historical import fields and Arabic alignment notes remain preserved. See the [current policy](CURRENT-REVIEW-POLICY.md).
