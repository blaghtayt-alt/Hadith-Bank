# HadeethEnc six-language corpus — uploaded source snapshot

> **Current HadeethEnc policy (11 November 2026):** the owner waived separate bank review. The earlier pending-review statements below describe the historical import. Original source flags, Arabic alignment notes and other materials’ review requirements remain unchanged. See [current policy](CURRENT-REVIEW-POLICY.md).

The actual Hadith bodies are included in Hadith-Bank: **8,423 translations with embedded original Arabic**, covering 2,328 publisher entry IDs. Counts: Japanese 281; Filipino/Tagalog 1,949; Vietnamese 1,203; Chinese 2,256; Uzbek 420; Hindi 2,314.

## Status

The owner explicitly requested public upload after receiving the pending-review report. This is **published_unreviewed_source_import**, not a verified release. Independent Pro QC, human review, canonical authentication and semantic translation verification have not been performed. All prior warnings and 267 Arabic-alignment exceptions remain. Earlier private-candidate audit reports are historical; the current audit is under reports/hadeethenc/2026-11-11/public/.

## Where the text is

Full JSONL records: languages/<code>/books/hadeethenc/editions/sqlite-<snapshot-hash>/records.jsonl. Each line contains the actual Arabic and translated Hadith, separate explanation/benefits, publisher categories, source attribution, grading labels and provenance. The local registry is datasets/hadeethenc/collections.json. Original ZIPs and SQLite databases are included under sources/hadeethenc/snapshots/2026-11-11/raw/. No second repository or network lookup is required.

## Tags, fidelity and limits

Publisher topic labels, category IDs, hierarchy and category-relation rows remain unchanged. Editorial/import tags are separate. Occurrence IDs and exact source-row revision IDs are retained. Provider entry IDs are not canonical collection Hadith numbers. Cross-language links are provider-entry links, not asserted chain or narration-family identities.

No translations were created and no source wording was corrected or normalized. All source-row values are preserved, including genuine source anomalies. AI/human translation authorship remains unknown for every entry. Missing translators, editions, structured narrator chains, canonical occurrence mappings and named grading assessors remain null/unknown.

8,156 entries match the supporting Arabic export by provider ID, source version and exact text. The remaining 267 retain their embedded Arabic but do not inherit bibliography or Arabic grades from a different version: Japanese 102, Chinese 103, Hindi 62. In 266 cases the specified Arabic version is absent; one has differing text at the same ID/version.

## Attribution and source version

Source/publisher: **HadeethEnc.com**. Its own hadith-api repository documents the same provider, not a second corpus. Retain source credit and all original version metadata when redistributing. The official source offers conditional republication requiring unchanged content, attribution, version preservation/disclosure, correction reporting, updates and suitable presentation. Full source terms are preserved with the evidence. The import neither grants an unrestricted license nor certifies that every downstream reuse meets those conditions.

The source exports include ar_version; that field is an Arabic revision, not a verified translation-edition number. The exact archive/database SHA-256, retrieval time and available source version are disclosed per record. Translation-version numbers not supplied by the source remain unknown; no website version is substituted. Chinese bank code zh-CN maps to source code zh without asserting a publisher-specific locale; Filipino uses source code tl. Uzbek script is preserved exactly.

## Offline tools

```text
python scripts/search_hadeethenc.py --language ja --id 2758
python scripts/search.py hadith --language fil --limit 3
python scripts/validate_hadeethenc_public.py
python scripts/validate.py
```

The current owner policy displays Human for this source and applies QC badges only to evidenced OCR. Original review and authorship metadata remains in record details. Programmatic validation compares every source row, mapped field and publisher taxonomy with the included raw databases, checks exact Arabic-version alignment and verifies local file hashes. This is a mechanical check, not independent Pro QC.
