# Hadith Bank — standalone six-language corpus

An independent, locally searchable archive of **Japanese, Filipino, Vietnamese, Simplified Chinese, Uzbek and Hindi** Hadith-related source material, with the Arabic passages and source evidence carried by each imported publication.

No app installation, second repository, external file pointer, API token or network access is required to browse or resolve the local records. Third-party primary-source web citations, where present in the materials, are provenance, **not runtime dependencies**.

## Languages

| Language | Code | Catalog |
| --- | --- | --- |
| Japanese | ja | [Browse](languages/ja/README.md) |
| Filipino | fil | [Browse](languages/fil/README.md) |
| Vietnamese | vi | [Browse](languages/vi/README.md) |
| Chinese (Simplified) | zh-CN | [Browse](languages/zh-CN/README.md) |
| Uzbek | uz | [Browse](languages/uz/README.md) |
| Hindi | hi | [Browse](languages/hi/README.md) |

Source material is organized by **language → book → edition/source revision**.
The published revision is checksum-pinned. Other previously public but unindexed files are preserved under a separate edition/revision folder to avoid silently treating them as independently approved.

## Current import and trust boundaries

This migration copies 83 language-specific source files, including 8 cataloged source packages, 6 readings with missing complete source envelopes, and associated unindexed files. The metadata index includes 182 source metadata records. **These are not counts of independently authenticated Hadith.**

The imported source packages were already public, but the import is not independent Pro quality control and does not establish accuracy, scholastic authenticity, copyright permission, human translation or full-book completeness. Check the individual catalog, source-conditions records and [audit](reports/IMPORT-STATUS.json). Do not treat an unindexed file or a reading-only entry as approved.

Original text is preserved without paraphrase. Arabic, translation, isnad, citations, grades, commentary, metadata, edition markers and source conditions are retained only where present and supported. Source occurrences are not deduplicated or merged. Missing fields remain unknown; no synthetic Arabic source or narrator/grade is supplied.

The supplemental bank field `ai_translation` is set to `"unknown"` on imported catalog and index records: historic model-assisted review by itself does **not** establish whether each underlying translation was written by AI. Any future AI-created translation must be explicitly labeled and separately attributed with traceable evidence.

## Offline usage

Requires Python 3, standard library only:

```bash
python scripts/search.py search --language ja --kind package
python scripts/search.py search "Muslim 2654" --language vi --kind source
python scripts/search.py resolve "package:ja:essential-01-003" --reading
python scripts/search.py fulltext "2654" --language hi
python scripts/validate.py
```

The search utility reads the copied files **locally**, verifies the expected byte lengths and SHA-256 digests on record resolution, and can inspect a source envelope member and JSON Pointer. Full-text search scans copied JSON, Markdown and text; it does not pretend to segment every passage into an authenticated narration.

## Design and verification

- [Catalog index](index.json)
- [Source metadata and local locators](organized/INDEX.json)
- [Audit and hashes](reports/IMPORT-STATUS.json)
- [Corpus limitations](docs/REVIEW-AND-RIGHTS.md)
- [Contributing rules](AGENTS.md)
- [Index schema](schemas/index.schema.json)

## Source coverage limits

This public repository intentionally contains **only the six language families above**, along with Arabic quotations already contained in those source packages. It does not yet include completed, independently QC-passed OCR books or a claim to cover all narrations in these languages. An edition/translation should only be promoted after source alignment, rights review, complete page comparison and a separate recorded Pro QC decision.
