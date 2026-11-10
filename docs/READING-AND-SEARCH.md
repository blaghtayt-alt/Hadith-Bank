# Reading and searching the bank

## Choose an entry point

- **[Readable pages](../browse/README.md):** translations and Arabic in normal paragraphs, with source, translator/process label, page/row locator, review state and optional audit details. The Japanese public collection has [281 entries](../browse/ja/hadeethenc/sqlite-a81da9af28f854f6/README.md).
- **[Materials catalog](../catalog/README.md):** every locally available dataset and all 83 preserved legacy source files. In the public repository, attachment intake is listed as separate metadata; in the combined download, all 64 datasets and their original files are included.
- **Offline HTML:** download [hadith-bank-reader.html](../hadith-bank-reader.html), then open it locally. Rebuild it with `python scripts/build_reader.py --root . --output hadith-bank-reader.html`. Search/filtering and JSON export work without a server or network. The compressed edition needs a browser with the built-in `DecompressionStream` API; add `--uncompressed` when building for an older browser.
- **Python search:** `python scripts/hadith_search.py '行い' --language ja --limit 5`. It prints readable results by default; `--json` returns structured JSON.

The public repository contains 8,423 HadeethEnc source occurrences in six languages. The private combined package contains those occurrences and 37,365 supplied attachment occurrences, for **45,788 occurrences in nine languages**. This includes the earlier 32,300-record intake plus 3,254 Vietnamese and 1,811 Japanese Muslim source occurrences. A repeated provider ID across languages or snapshots remains a separate record. These totals do not count unique canonical Hadith.

## JSON is the main data format

| Layer | Location | Purpose |
| --- | --- | --- |
| Canonical source records | `languages/<language>/books/<book>/editions/<edition>/records.jsonl` | Full source wording, evidence and audit fields; unchanged by view generation. |
| Supplied-file canonical records (combined package) | `attachments/attachments-b53d154fa3622b95/languages/<language>/books/<book>/editions/<edition>/records.json` | Separate PDF/XLSX source occurrences, with the originals and extraction evidence retained in the same intake package. |
| Simplified search records | `search/<language>/<book>/<edition>/part-*.jsonl` | One flat record per source occurrence, in small ordered shards. |
| Optional whole projection | `search/records.jsonl` | Exact ordered concatenation of the shards; included in generated packages and reproducible locally. |
| Material inventory | `catalog/materials.json` | Counts, source/canonical-file checksums, availability, translation-origin evidence and search-shard manifest. |
| Human/AI provenance evidence | `catalog/translation-origins.json` | Evidence, source URLs, credit pages and the scope of each translation label. |
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

Legacy lessons, source envelopes and readings are separately cataloged because they have not all been segmented into narration records. Their existing offline search remains available:

```bash
python scripts/search.py fulltext '2654' --language hi
python scripts/search.py search --language ja --kind package
python scripts/search.py resolve 'package:ja:essential-01-003' --reading
```

Some preserved historical source documents contain old relative links. [The legacy-link map](LEGACY-LINKS.md) identifies available candidates from other revisions and explicitly missing targets without changing the archived document bytes. Current bank catalogs and verified local record locators provide the working navigation.

## Translation labels and sources

| Origin | Display meaning | AI field |
| --- | --- | --- |
| `publisher_human_workflow` | HadeethEnc's publisher describes translators, proofreading and human review. The label applies to the documented publishing process. | Preserved as `"unknown"` for these exported versions. |
| `human_translator_credited` | Human translation credits are established by the specific source, including credited Chinese, Japanese and Vietnamese editions. | Existing evidence-backed `false` retained. |
| `unknown` | Exact-source translator/process attribution has not been established. | Existing value retained; no inference from filename or PDF timestamp. |

The evidence file links to [HadeethEnc's project description](https://hadeethenc.com/ar/home/about), [the publisher's platform list](https://islamiccontent.org/) and [its translation/review workflow](https://islamiccontent.org/About). A related [AI-assisted platform](https://molhem.ai/) describes AI assistance and human review; that capability neither proves nor excludes AI use in these particular exports. Human involvement, absence of AI translation, extraction method and independent bank QC are different fields.

The verified findings, retrieval dates, exact primary URLs and PDF credit-page evidence are also preserved in a [local evidence snapshot](../sources/translation-origin-evidence/2026-11-11/evidence.json), whose checksum is pinned by the policy. This snapshot is identified as extracted findings; it does not claim to be a raw HTML archive.

For the private Chinese sources, the credited translators are **艾乃斯·马风德** for *Riyadh al-Salihin* (PDF page 12; dated afterword on page 358) and **陈克礼** for *Shengxunjing* (PDF page 2, with historical edition statements). No unverified name is supplied for the Bukhari or Muslim PDFs. The source PDFs, exact hashes, extracted credit evidence and page references remain in the private package.

## Rebuild and verify

Python 3.9 or later and its standard library are enough for the builders and search. Run:

```bash
python scripts/build_bank_views.py
python scripts/build_reader.py --root . --output hadith-bank-reader.html --markdown-output browse
python scripts/validate_hadeethenc_public.py
python scripts/validate_bank_views.py --root . --report reports/portable-validation.json
python -m unittest discover -s tests -p 'test_hadith_search.py'
python -m unittest discover -s tests -p 'test_reader.py'
```

To include the separately held attachment package, supply its expanded folder and an **external empty output directory**:

```bash
python scripts/build_bank_views.py --bank-root . --attachments /path/to/hadith-bank-private-intake --output /path/to/private-combined-bank
python scripts/build_reader.py --root /path/to/private-combined-bank --output /path/to/private-combined-bank/hadith-bank-reader.html --markdown-output /path/to/private-combined-bank/browse
```

The combined package keeps the original attachment intake under `attachments/attachments-b53d154fa3622b95/`. Later intakes occupy separate roots under `attachments/` and use the additive intake adapter described in [ADDITIONAL-INTAKES.md](ADDITIONAL-INTAKES.md). Language/book/edition catalogs and reading views cover every included source family. Public/private availability, source snapshots and all review flags remain explicit.

Integration checks compare exact text/IDs and source hashes. They do not replace independent linguistic or scholarly review. The existing pending QC status and Arabic-alignment exceptions continue to apply.

## Current HadeethEnc decision

The owner waived separate bank review for HadeethEnc. The reader and commands show this current decision separately from the unchanged historical import fields and Arabic alignment notes. See the [current policy](CURRENT-REVIEW-POLICY.md). Other materials retain their existing source-specific qualifications.
