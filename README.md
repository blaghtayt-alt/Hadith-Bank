# Hadith Bank

**8,423 HadeethEnc source occurrences in six languages, with Arabic, source attribution and separate narration fields.**

[Read the narrations](browse/README.md) · [Japanese: all 281 entries](browse/ja/hadeethenc/sqlite-a81da9af28f854f6/README.md) · [Complete materials catalog](catalog/README.md) · [Offline reader](hadith-bank-reader.html)

The bank works independently. All public narration text, original source databases, local record locators, schemas and search tools are included. Reading and search work offline after downloading the repository. External source links provide attribution.

## Read by language

| Language | Public source occurrences | Read | Structured catalog |
| --- | ---: | --- | --- |
| Japanese | 281 | [Read](browse/ja/README.md) | [JSON](catalog/languages/ja.json) |
| Filipino / Tagalog | 1,949 | [Read](browse/fil/README.md) | [JSON](catalog/languages/fil.json) |
| Vietnamese | 1,203 | [Read](browse/vi/README.md) | [JSON](catalog/languages/vi.json) |
| Chinese | 2,256 | [Read](browse/zh-CN/README.md) | [JSON](catalog/languages/zh-CN.json) |
| Uzbek | 420 | [Read](browse/uz/README.md) | [JSON](catalog/languages/uz.json) |
| Hindi | 2,314 | [Read](browse/hi/README.md) | [JSON](catalog/languages/hi.json) |
| **Total** | **8,423** | [All languages](browse/README.md) | [All datasets](catalog/materials.json) |

Counts describe source occurrences. Different languages, chains, book occurrences and source editions remain separate. They are not a unique canonical Hadith total.

## How the material is organized

| Material | Location |
| --- | --- |
| Canonical source records | `languages/<language>/books/<book>/editions/<edition>/records.jsonl` |
| Readable, paginated text | `browse/<language>/<book>/<edition>/` |
| Unified JSONL search records | `search/<language>/<book>/<edition>/part-*.jsonl` |
| Language, source, edition and checksum catalog | `catalog/materials.json` and `catalog/languages/` |
| Original HadeethEnc databases and download evidence | `sources/hadeethenc/snapshots/2026-11-11/` |
| Preserved legacy lessons and source documents | [83-file inventory](browse/materials/legacy.md) |
| Source edition relationships | `catalog/related-snapshots.json` |
| Current HadeethEnc review decision | `catalog/review-policy.json` |

JSON is the main machine-readable format. Each search record has separate fields for Arabic, translation, source, book/number, narrator/isnad, translator, page/row locator, tags, commentary, benefits, footnotes, references, grading, source hashes and review history. Missing information stays null or unknown. No new translation or missing source text is invented.

**For ordinary reading**, use the paginated links above. **For browser search**, download `hadith-bank-reader.html` and open it locally. It contains its own data, offers language/source filters and exports selected records as JSON. GitHub's file page displays source code; download the HTML to use the reader.

## Search

Python 3 is sufficient; the search tools use the standard library.

```bash
python scripts/hadith_search.py '礼拝' --language ja --limit 5
python scripts/hadith_search.py --language ja --id 2758 --json
python scripts/hadith_search.py 'HadeethEnc.com' --language fil --limit 3
python scripts/hadith_search.py 'Muslim' --language vi --include-commentary
python scripts/search.py fulltext '2758' --language ja --limit 5
```

Unified search includes narration text, source references, translators and source metadata. Commentary, benefits and footnotes are optional. General document search also reads JSONL. Search verifies the input stream's checksums and uses a disposable local cache; normalization is applied only to search keys, preserving returned text exactly.

[Search examples and field guide](docs/READING-AND-SEARCH.md) · [Search record schema](schemas/search.record.schema.json)

## Human translation, attribution and review

HadeethEnc entries are labeled **Human translation — HadeethEnc**, following the owner's source classification and the provider's [description of its translator workflow](https://hadeethenc.com/en/home/about). The named translator is retained when evidenced; none is invented. The exact imported AI-origin flags remain visible with their original scope. [Translation-origin evidence](catalog/translation-origins.json).

**The owner waived separate bank review for HadeethEnc on 11 November 2026.** This current decision appears in the reader and search alongside the preserved import history. The **267 Arabic-version alignment notes** remain available: Japanese 102, Chinese 103, Hindi 62. The waiver does not assert that review was performed or that those notes were resolved. [Current policy](docs/CURRENT-REVIEW-POLICY.md) · [Original alignment ledger](reports/hadeethenc/2026-11-11/public/exceptions.json).

Original texts, stable IDs, source databases and historical import records remain unchanged. Publisher conditions apply. Translation origin, source-version alignment, transcription fidelity and scholarly authenticity remain separate facts.

## Supplied PDF/XLSX materials

The combined package contains **45,788 source occurrences across nine languages and 64 source datasets**: the 8,423 public occurrences plus **37,365 supplied-file occurrences**. It retains the original attachments and all 83 legacy source documents.

The public catalog registers the supplied-file intake accurately as separate metadata. Its held source files remain in the combined package with their existing publication qualifications. That intake includes Bengali, Urdu and Portuguese alongside the shared language families. See [intake organization](docs/ATTACHMENT-INTAKE.md) and [the metadata inventory](browse/materials/private.md).

The Japanese SQLite snapshot and supplied v1.8.0 workbook each contain the same 281 publisher IDs. Both snapshots are preserved in the combined package; they do not represent 562 distinct Hadiths.

The latest additive intakes contribute **3,254 Vietnamese occurrences from 45 PDFs** and **1,811 Japanese Sahih Muslim volume-one occurrences from the supplied 580-page PDF**. The Japanese intake includes 191 abbreviated route/reference occurrences; its source scope is preserved. These PDF packages retain their private-candidate and pending-review status. Their source editions are registered as metadata in [the additional intake catalog](catalog/additional-private-intakes.json), with details in [the intake guide](docs/ADDITIONAL-INTAKES.md).

## Rebuild and validate

```bash
python scripts/build_bank_views.py
python scripts/build_reader.py --root . --output hadith-bank-reader.html --markdown-output browse
python scripts/validate.py
python scripts/validate_hadeethenc_public.py
python scripts/validate_bank_views.py --root . --report reports/portable-validation.json
python -m unittest discover -s tests
```

Generated reading/search views preserve canonical text and source IDs. The whole `search/records.jsonl` is optional and reproducible; the published checkout includes its ordered, checksum-verified shards. [Organization validation](reports/organization-final-audit.json).
