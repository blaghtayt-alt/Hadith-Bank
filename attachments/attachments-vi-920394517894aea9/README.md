# Vietnamese Hadith Bank intake

Prepared 11 November 2026 from the user-supplied `vietnamese(1).zip`.

## Contents and status

This package contains **3,254 structured source occurrences and explicit variants** extracted from **45 PDFs / 1,586 pages**. The Vietnamese texts are present in each record. The originals, raw Arabic text layer, page evidence, source references, annotations, translator credits and extraction history accompany them.

| Collection | PDFs | PDF pages | Occurrence records |
|---|---:|---:|---:|
| Sahih al-Bukhari | 15 | 409 | 767 |
| Sahih Muslim | 15 | 618 | 971 |
| Sunan Abi Dawud | 14 | 522 | 1316 |
| HAI TRĂM HADITH VÀNG CỦA NABI MUHAMMAD | 1 | 37 | 200 |
| **Total** | **45** | **1,586** | **3,254** |

These counts describe the supplied files. They are not counts of unique canonical hadith and do not establish that an entire collection is present. Repeated numbers, repeated wording and distinct variants remain separate occurrences.

The status is **private candidate / independent full review pending**. The package is organized for staged import into the bank. It is not a publication-certified corpus. No repository merge or public publication was performed by this extraction.

## Main data

- `vietnamese-hadith-bank.json`: a UTF-8 array of all 3,254 complete structured records.
- `vietnamese-hadith-bank.jsonl`: the same records, one JSON object per line, for streaming and search.
- `languages/vi/books/<book>/editions/pdf-<sha256-prefix>/records.json`: the bank layout, with one source snapshot per PDF.
- `catalog/sources.json`, `catalog/books.json`, `catalog/languages.json`, and `catalog/record-index.jsonl`: machine-readable lookup tables.
- `sources/vi/<book>/pdf-<hash>/source.pdf`: all 45 original PDF byte streams, verified by SHA-256.
- `evidence/pdf-<hash>/`: complete native page text, line coordinates, source-specific extraction records, chapter material, footnotes, changes and exceptions.

The book routes are `bukhari`, `muslim`, `abu-dawud`, and `200-golden-hadith`. The hash-based edition directory identifies the exact source file, not a newly inferred bibliographic edition.

## Record fields

Every record has stable `id`, `record_id` and `occurrence_id` values based on the PDF hash and the source marker's page/block/line position. The `source_order` field preserves reading order. Inserting a missed earlier occurrence does not change later anchor identities. IDs are tied to this source byte stream and extraction coordinate system; a different source PDF remains a new snapshot.

`text.translation` contains the extracted Vietnamese narration. `book` and `number` retain the collection, source chapter and printed labels. `number.canonical` remains null because this task did not independently establish exact canonical variants. The source's parenthetical references and citation strings remain available separately.

`narrator` records an available introductory attribution, not an invented full isnad. `references`, `commentary`, `footnotes` and `grading` retain separately identifiable source material. Reported grades name the grader when printed and are scoped to the source occurrence; this does not establish independent authenticity verification. Embedded commentary or extra reports inside an occurrence/footnote still require semantic review.

`source`, `translator`, `page` and `provenance` provide source filenames, PDF hashes, available human credits, PDF and printed-page locators, and source-line references. Unknown edition/year/chain metadata remains null or explicitly unresolved. Technical PDF creation dates are preserved as PDF metadata and are not promoted to publication dates.

`source_structure_tags` use literal printed chapter headings. `editorial_tags` are explicitly labelled as import-pipeline labels. `topic_tags` remains empty because no independently supported topical taxonomy was supplied.

## Arabic and special glyphs

The PDFs contain Arabic, but their embedded text layers have broken letter mappings, reading order and diacritics. **`text.arabic` is null**, and the extracted Arabic is retained as **`source_text.arabic_embedded_raw`**, with any evidenced digit-only derivative in a separate unapproved field. The Arabic must be repaired against the original page images before it is treated as clean text.

Vietnamese honorific signs sometimes use private-use font characters. The original characters remain in the primary text and evidence. The searchable derivative removes those glyph codes and joins whitespace; it does not rewrite or translate wording. No new Arabic or Vietnamese translation was generated.

## Numeric decoding

Some PDFs visibly print a number such as 117 but map it to 111 in their extracted text. The accepted decoder resolves the exact PDF font resource from content-stream text operations and maps original glyph IDs through that font's embedded cmap. It changes only unambiguous ASCII digits, retains raw characters and logs each correction. The initial family-name experiment was rejected because it could corrupt valid text; its proposals are not part of the delivered records.

The accepted decoder corrected 1,324 digits in the Bukhari/anthology pipeline and 3,779 in Muslim evidence. The Abu Dawud audit changed 0 digits. These are character corrections, not numbers of altered narrations. No source numbering gaps were filled by inferred sequences.

## Translation provenance

`ai_translation` follows the bank's three-state policy:

- **false: 2,248 records.** A named human translation credit or explicit translation colophon is evidenced within the source PDF.
- **unknown: 1,006 records.** The particular source did not establish the translator role/method sufficiently. Some have a credited human name or adjacent-series context, but the role was not made explicit in that PDF. Unknown is not a claim that the text is AI translated.
- **true: 0 records.** No new translation was produced during this work.

Exact spellings such as Abu Rohman/Abu Rahman and Abu Fadil/ABU FAUDIL are preserved with page evidence. See `reports/translation-provenance.json` for every unknown source and the decision definitions.

## Source exceptions

The original printed anomalies remain traceable:

- Bukhari 2223: printed 54 followed by 56.
- Bukhari 2528:219 followed by 230.
- Bukhari 2498:127 appears twice; Bukhari 2550 repeats 5 and 15.
- Abu Dawud 2479:1889 followed by 1900 in both columns.
- Abu Dawud 2335, PDF p22: footnote 9 overlaps the narration columns around 1247; both embedded layers remain preserved.
- Muslim 2441, PDF p36: Arabic local label 76 differs from Vietnamese 75-(410f).
- The anthology's entry 188 has an Arabic narration and a Vietnamese introductory phrase, but no Vietnamese translated body. The omission is marked; no replacement was generated.

A numbering jump alone does not prove how many canonical narrations are missing. See `reports/source-exceptions.json` and the source-specific ledgers.

## Verification and review limits

Mechanical checks validate the existing bank schema, 3,254 unique anchored IDs, source-byte hashes, JSON/JSONL agreement, aggregate/edition agreement, page ranges, source spans and text-payload hashes. All 1,586 saved native page texts were compared against extraction from their included PDFs.

Targeted visual inspection checked representative boundaries, font errors, source defects, footnotes and translator credits. **All-page visual comparison and full character/Arabic diacritic review were not completed.** Review scope is documented separately for each reviewer in `reports/coverage.json`; overlapping sample counts are not summed into a false complete-review claim. Independent Pro final evaluation remains pending for all records.

## Search

The search tool uses the Python standard library and supports accent-insensitive Vietnamese substring search:

```bash
python tools/search.py --query "le nguyen" --book muslim --limit 10
python tools/search.py --book abu-dawud --number 997
python tools/search.py --book 200-golden-hadith --number 188
python tools/search.py --query "Allah" --ai-status unknown --limit 5
```

Search results include provenance and review warnings. The tool does not treat a local printed number as a verified canonical number.

## Validate or reproduce

Install the pinned packages in `requirements.txt`, then:

```bash
python tools/validate.py --source-pages
python tools/reproduce_extraction.py --output /path/to/new-empty-directory
```

The first command rechecks the delivered package. The second copies included originals and portable extraction scripts to a new directory and reproduces the source-specific extraction. It does not overwrite delivered bank JSON. The exact source-specific outputs before bank projection are also retained in each evidence directory.

## Staged merge

1. Validate the package and preserve the original PDFs/evidence with the intake.
2. Choose either the aggregate file or the per-edition records for import; they are equivalent representations of the same occurrence IDs. Add the 45 source-snapshot directories beneath `languages/vi/books/` without replacing existing editions or other languages.
3. Import by `record_id`, preserve all occurrences and source-specific reference labels, and register the source catalog. Treat byte-identical repeated imports as the same source identity.
4. Keep every record's `private_candidate`, `independent_pro_qc: pending` and `release_eligible: false` qualifications. Do not collapse variants or connect canonical records by number alone.
5. Rebuild the bank's catalogs/search index through its own current importer. Review gates apply before promotion to a published layer.

This package has no runtime dependency on Iman Companion or another repository. Source reuse conditions are preserved for later review; no public redistribution authorization is inferred by this import.
