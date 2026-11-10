# Additional supplied JSON intakes — 11 November 2026

The newly supplied Vietnamese and Japanese JSON files are incorporated additively into the private combined package. Their exact source records, stable occurrence IDs, original source files and evidence remain intact. The public bank registers their source-edition metadata; public searchable text continues to contain the six authorized HadeethEnc snapshots.

## New source inventory

| Language | Source | Source PDFs | Source PDF pages | Source occurrences |
| --- | --- | ---: | ---: | ---: |
| Vietnamese | Sahih al-Bukhari booklets | 15 | 409 | 767 |
| Vietnamese | Sahih Muslim booklets | 15 | 618 | 971 |
| Vietnamese | Sunan Abi Dawud booklets | 14 | 522 | 1,316 |
| Vietnamese | 200 Golden Hadith | 1 | 37 | 200 |
| Japanese | WEB Sahih Muslim, supplied volume-one PDF | 1 | 580 | 1,811 |
| **Total added** | | **46** | **2,166** | **5,065** |

These are source-occurrence counts. They preserve explicit variants, repeated source occurrences and shortened route references. They do not establish complete canonical collection coverage or unique canonical Hadith totals. The Japanese source contains 1,406 narration/report occurrences, 214 variant occurrences and 191 shortened route/reference occurrences. No missing narration is filled in.

## Source and translation evidence

The Japanese source credits 磯崎定基、飯森嘉助、小笠原良治. The source's 1,811 records preserve `ai_translation=false`, while the per-occurrence translator remains unassigned where not established.

The Vietnamese package retains explicit human translation credits for 2,248 records and `ai_translation=unknown` for 1,006. No new translation was generated. Unknown records are not labeled as machine translated. All original source-specific translator evidence remains inside the package.

The supplied Japanese source does not provide complete original Arabic narrations. The Vietnamese PDFs contain Arabic with broken text-layer glyph mapping and ordering. Approved `text.arabic` stays null in both intakes; extracted fragments/raw Arabic and their evidence remain separate. No generated Arabic is substituted.

## Local organization and search

Each complete source package occupies a separate private intake root under `attachments/`. Internal paths in unchanged canonical records resolve relative to that intake root. The unified projection adds repository-relative, hash-verified source and record locators.

The normalized search and reading views remain organized by `language → book → edition`. The edition key identifies the exact source-file checksum; it does not invent a bibliographic edition. Narration text, notes, commentary, references, narrator information and grading remain separate fields.

Use the combined package's `catalog/materials.json` for all 64 source datasets and `catalog/languages/` for per-language lookup. The original 40,723 source occurrences are preserved alongside the 5,065 additions, for 45,788 occurrences in nine languages. The two 281-entry Japanese HadeethEnc snapshots remain separate from this Japanese Muslim source.

The additive adapter verifies the source package manifests, IDs and text before registering the new datasets. It records a mechanical integration report and does not promote a source to independently reviewed status. The standalone portable validator checks local source hashes, canonical record equality, catalogs, search shards, reader payload and navigation.

## Review and publication status

Both new PDF intakes remain `private_candidate`, independent source QC pending, with release eligibility false. Existing source exceptions, incomplete Arabic repair and unresolved canonical alignment stay visible. HadeethEnc's separate-review waiver applies only to HadeethEnc.

The exact supplied Vietnamese JSON and Japanese ZIP were compared by SHA-256 with the integration inputs and matched. Their source records were not re-extracted. The earlier audit of 40,723 occurrences remains historical evidence for that scope; the expanded package has its own integration and portable validation reports.

The metadata-only inventory is [catalog/additional-private-intakes.json](../catalog/additional-private-intakes.json).
