# Japanese and Vietnamese source intakes — 11 November 2026

The owner explicitly requested adding the supplied Vietnamese and Japanese texts to the GitHub bank and hosted reader. Their **5,065 source occurrences** are included alongside the **8,423 HadeethEnc occurrences**, giving **13,488 occurrences in that initial structured publication**. Later old-bank/Qur’an-book quotation additions are documented in [the extraction guide](LEGACY-EXTRACTION.md); the generated catalog shows the complete current total. Their exact source records, stable IDs, original PDFs and evidence remain intact in the two source packages under `attachments/`.

Current public visibility is recorded separately from historical source review in [the publication policy](../catalog/publication-policy.json) and `materials/*/manifest.json`. These are **public pending-review source imports**, not independently certified releases.

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

The Vietnamese package retains explicit human translation credits for 2,248 records and historical `ai_translation=unknown` for 1,006. Under the owner's later source confirmation, the reader displays all of these website-sourced records as **Human**; the separate [current provenance policy](../catalog/provenance-policy.json) preserves those original flags. No new translation was generated. Unknown metadata is not evidence of machine translation. All original source-specific translator evidence remains inside the package.

The supplied Japanese source does not provide complete original Arabic narrations. The Vietnamese PDFs contain Arabic with broken text-layer glyph mapping and ordering. Approved `text.arabic` stays null in both intakes; extracted fragments/raw Arabic and their evidence remain separate. No generated Arabic is substituted.

## Local organization and search

Each complete source package occupies a separate intake root under `attachments/`. Internal paths in unchanged canonical records resolve relative to that intake root. The unified projection adds repository-relative, hash-verified source and record locators. The current packages are `attachments-ja-muslim-c859ce57c211ea1b` and `attachments-vi-920394517894aea9`.

The normalized search and reading views remain organized by `language → book → edition`. The edition key identifies the exact source-file checksum; it does not invent a bibliographic edition. Narration text, notes, commentary, references, narrator information and grading remain separate fields.

Use `catalog/materials.json`, `catalog/languages/` and the reader's language, collection and source filters. The original publication contained 52 source datasets: six HadeethEnc snapshots and 46 PDF editions from these two packages. Japanese has 2,092 occurrences (281 HadeethEnc plus 1,811 Muslim); Vietnamese has 4,457 (1,203 HadeethEnc plus 3,254 from the supplied PDFs). Other current bank languages remain available in the same reader.

The earlier private combined export contains 45,788 occurrences across 64 source datasets and nine languages. It is a separate historical export with additional source snapshots; that total must not be presented as the current public website total. Different source versions remain distinct, even when they share a provider entry or printed number.

The additive adapter verifies the source package manifests, IDs and text before registering the new datasets. It records a mechanical integration report and does not promote a source to independently reviewed status. The standalone portable validator checks local source hashes, canonical record equality, catalogs, search shards, reader payload and navigation.

## Review and publication status

The original PDF-intake records retain their preparation history: `private_candidate`, independent source QC pending, and release eligibility false. The current owner decision authorizes public access while preserving those historical fields and keeping that history in record details. The extraction metadata identifies native PDF text without OCR, so normal cards display no pending-QC/import-history badges under the current OCR-only display rule. Existing source exceptions, incomplete Arabic repair, unresolved canonical alignment and unassessed rights remain visible. HadeethEnc's separate-review waiver still applies only to HadeethEnc; the PDF intakes have not acquired a QC pass.

The exact supplied Vietnamese JSON and Japanese ZIP were compared by SHA-256 with the integration inputs and matched. Their source records were not re-extracted. The earlier audit of 40,723 occurrences remains historical evidence for that scope; the expanded package has its own integration and portable validation reports.

The registration history and current availability are in [catalog/additional-private-intakes.json](../catalog/additional-private-intakes.json). Its historical filename is retained for stable links; accepted entries now point to actual local source material. See [adding material](ADDING-MATERIAL.md) for automatic integration and [the website guide](WEBSITE.md) for deployment.
