# HadeethEnc six-language import — private pending review

## Actual outcome, 11 November 2026 (Japan)

8,423 translated entries were downloaded and converted from official SQLite exports: Japanese 281, Filipino/Tagalog 1,949, Vietnamese 1,203, Chinese 2,256, Uzbek 420, Hindi 2,314. Every entry contains actual translated Hadith text and the Arabic text embedded in its source export. These are translation occurrences across 2,328 publisher entry IDs, not 8,423 unique canonical narrations.

**The new text corpus is private and has NOT been pushed to this public repository.** The repository contains the reproducible importer, validator, offline search, tests, schema and non-text audit. Existing public material is unchanged. Candidate-only paths in audit reports are not public runtime dependencies.

## Attribution and preservation

Source and publisher: HadeethEnc.com. The islamhouse-dev/hadith-api repository documents this same provider's API; it is not a second independent Hadith corpus.

The source API codes tl and zh are retained alongside bank directory codes fil and zh-CN. The Chinese directory is an organizational alias, not proof of a publisher-specified Chinese locale. Uzbek script is unchanged. No new translations, OCR or scripture corrections were generated.

Arabic, translated text, explanations, benefits, raw source fields, bibliography, grading labels and publisher categories remain separate. Publisher topic tags retain category IDs, hierarchy and relation-row evidence; import-status tags are explicitly editorial. AI/human authorship is unknown for these exact passages, so ai_translation is unknown, not automatically false merely because they came from a website.

Each provider entry/language occurrence and exact row revision has its own ID. Cross-language links use only the provider's entry ID and never assert identical canonical narration, chain or edition. Book references are retained verbatim and are not converted into verified canonical occurrences or guessed narrator/number mappings.

## Arabic alignment

8,156 entries have an exact publisher-ID, Arabic-version and text match to the downloaded Arabic export. 267 do not: Japanese 102, Chinese 103, Hindi 62. Their source-embedded Arabic remains intact. Current-version bibliography and Arabic grades are not silently attached to those entries. See the exception ledger for exact reasons and source IDs.

## Verification limits and publication gate

All 8,423 imported rows and 67,384 mapped fields passed programmatic comparison with the source SQLite databases, with checksums for all 14 source files. This is not independent Pro QC, scholarly authentication, human review or semantic translation verification. Three synthetic-fixture tests check lossless import, version/text mismatch quarantine, altered-text rejection and the closed release gate.

The site permits republication under conditions including unmodified content, publisher attribution, version disclosure/preservation and keeping translations updated. The export contains ar_version, which is **not** a confirmed translation-edition number. Translation authors, exact translation versions, canonical occurrence mappings, full narrator-chain segmentation and named grading assessors remain unknown unless supported. No publication permission beyond the source's stated conditions is inferred.

Do not publish the candidate until independent Pro QC and all applicable publication requirements are satisfied. Do not upload it to a public branch or pull request as a workaround.

## Reproduce from downloaded snapshots

Use Python 3, standard library only for conversion, validation and search. Input is a private directory containing raw/{ja,tl,vi,zh,uz,hi,ar}.sqlite, their original .sqlite.zip archives, and export-manifest-v2.json (source URLs, UTC retrieval times and hashes). Keep candidate output outside the public repository.

```text
python scripts/import_hadeethenc.py --input PRIVATE_INPUT --output PRIVATE_CANDIDATE
python scripts/validate_hadeethenc.py --root PRIVATE_CANDIDATE
python scripts/search_hadeethenc.py --root PRIVATE_CANDIDATE --language ja --id 2758
python scripts/search_hadeethenc.py --root PRIVATE_CANDIDATE --language fil --topic-id 1
python -m unittest discover -s tests -p test_hadeethenc_import.py
```

Search always displays the unknown-authorship and pending-review warning. Metadata classification and full-text search require no network. The import scope is every row in the downloaded official snapshots, not a verified inventory of all live API entries.

Audit: reports/hadeethenc/2026-11-11/summary.json, validation.json and exceptions.json.
