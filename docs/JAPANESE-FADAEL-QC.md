# Japanese Fadael, volume 2: corrected source intake

The material `ja-fadael-2-tuwaijri-1438-qc-v1` registers **57 source occurrences** from **諸々の徳（ハディース集）②** (`كتاب الفضائل`), attributed in the book to ムハンマド・ブン・イブラーヒーム・アッ＝トゥワイジュリー. The original credits identify translator サイード佐藤, reviewer ファーティマ佐藤 and editor ムハンマド・サーリフ金子. The printed year is **1438**; no Gregorian edition year is inferred.

The source is the 25-page PDF `ja_ketab_elfadael.pdf`, SHA-256 `09a7f220e7bcf5152520913de57031bb840c80367566cfa71a61ded20bd6acde`. The publisher URL `https://islamhouse.com/ja/main` is recorded exactly as printed. It is not presented as the PDF download address.

## Source and publication scope

The owner requested uploading the corrected book, integrating it into Hadith Bank HTML and avoiding duplicate narration groups. The material uses `owner_requested_public_source_import`. This makes the identified source available; it does not assert a publisher licence, an independent authenticity grading, or independent Pro certification of the final repository candidate.

The registered book key is `fadael`; the edition key is `pdf-09a7f220e7bc-qc-v1`. Every record keeps the exact existing `JA_KETAB_ELFADAEL_09a7f220e7bc_occ_note_NNN` identifier. Footnote numbers are **source locators**, so `number.in_book`, `number.canonical` and `number.printed_hadith_number` remain null.

`text.translation` is exactly the corrected edition's `corrected_text`, including its narrator introductions, source-local prefix, quotation boundaries, excerpt markers, inline note markers and collection attribution. Each record also retains the full `original_text`, its hash, and the body and note correction IDs. No source words are removed to create a cleaner reading. The one leading `1－` in occurrence 33 stays in its translation; the separately parsed narrator name is アーイシャ.

The source supplies Japanese report text, not Arabic hadith matn. Every registered `text.arabic` is null. Arabic titles and the basmala remain in source context and cannot substitute for the report's Arabic. Printed Japanese narrator names are copied from the actual introductory span. No Arabic narrator normalization, chain, unsupported grader or canonical identity is invented. The dialogue in occurrence 55 remains a Companion report, with タルハ as the printed introductory narrator and the corrected Ibn Abi Awfa reply preserved in the text.

## Preserved evidence and non-hadith material

`materials/ja-fadael-2-tuwaijri-1438-qc-v1/preservation-manifest.json` binds each archived file to its byte count and SHA-256. The original and corrected complete JSON, original PDF, corrected PDF/DOCX/TXT, correction logs and required source/render/reference QC summaries remain individual files. Native extraction and OCR text/TSV intermediates are preserved byte for byte in **one deterministic `extraction-intermediates.zip`**, with fixed timestamps, sorted member names, and a checksum manifest both inside and beside the ZIP. It retains all **621 source units** and **58 footnotes**. Raw external web tool responses and full retrieved third-party pages are excluded from publication; primary URLs and the reference review summaries remain. Historical raw-response identifiers in immutable audit metadata are not runtime source links. Reproducible page PNGs, temporary font experiments, downloaded OCR models, personal Library upload responses and duplicate delivery ZIP mirrors are also excluded; the recorded review scopes/coordinates and both PDFs remain available.

The 57 occurrences account for all **376 body-line units**, each once. `source-context.json` preserves the other **245 units**: both covers and their credits, contents, opening formula and preface, section/subsection headings, page labels, logos, all footnote lines, the publication addendum and back cover. The complete 58 structured notes are also in `footnotes.json`.

**Note 19 is translator commentary**, linked to occurrence 20. It is retained in the commentary panel and footnote metadata, outside hadith matn and occurrence counts. Source context is not registered as additional hadiths. The source PDF, JSON, TXT and corrected document are different representations of one source intake, not separate occurrence sets.

## Reference and narration identity boundaries

The archived `source_reference_map.json` carries **93 primary-reference links**, corresponding to **91 unique corrected collection keys**. Primary reference numbering is kept separately from reviewed Sunnah.com variants such as Muslim `2607c`, `2752c` and `2552c`. A variant suffix is evidence about the checked record, not an unrecorded alteration of a printed citation.

The corrected references include note 5, Bukhari **5253 → 5653**, and note 20, Bukhari **5304 → 52** / Muslim **2983 → 1599**. Original citations remain visible in provenance. Body-only `correction_ids` are combined with footnote-only C01, C02 and C10 so these changes cannot disappear during import.

Primary correspondence, same-report variants, partial correspondences and broader parallels retain distinct scopes. In particular:

- Notes 21 and 41 cite the same Bukhari 13 / Muslim 45 report family but preserve two source wording selections.
- Note 31's Muslim 2554 is a broader kinship parallel to the selected Bukhari 5988 wording.
- Note 35's Muslim 2983 is an Abu Hurayra orphan-care parallel to the Japanese Sahl report in Bukhari 5304.
- Corrected note 20 and note 35 are different reports; obsolete references in note 20 must not create a false duplicate.
- Four secondary edition citations in notes 26 and 58 remain **not independently verified**. Their numbers are not promoted to primary collection IDs.

The importer assigns no canonical hadith ID and merges no source occurrence. Proven matching narration identities may share a reader group through a separate reviewed binding sidecar. Similar meaning, a shared narrator or matching numbers alone is insufficient. Distinct source occurrences, collection witnesses, chains, translations and edition evidence remain preserved even when the reader groups them.

### Reviewed reader grouping

The final grouping sidecar is `sources/reader-groups/ja-ketab-elfadael-v1.json`, with its exact bytes authorized through the material's checksum-bound supporting descriptor. Its review evidence is retained under `grouping-review/` in the material. **All 57 links received two independent selected-target comparisons**: two are complete Japanese quotations already present in legacy records (notes 3 and 7), and 55 use stored Fawaz Arabic narration-core anchors. The second review independently reloaded all selected target IDs and record/text hashes. The per-source qualifications remain part of each binding; representative anchors do not certify a unique repeated collection position or a complete chain.

Every source occurrence ID, original/corrected text, edition, provenance flag and review history remains intact. These links add **zero ungrouped reader cards** while preserving the 57 new source occurrences. No held Japanese research-v3 target was selected and no research-v3 counterpart hold was overridden. The grouping review does not approve new Arabic/English counterpart publication or confer translation/authenticity certification.

Reader statistics distinguish source occurrence counts from grouped cards. At the inspected local baseline, the expected arithmetic was 92,711 → 92,768 total source occurrences and 3,463 → 3,520 Japanese source occurrences. These are baseline-dependent expectations, not final remote totals; concurrent imports must be included before the published count is reported.

## Translation origin and QC

The original translation-origin flag remains **unknown** for all inherited source text. Under the current owner policy, the 55 occurrences without new AI translation display as **Human**, with that display decision separate from original provenance.

Occurrences **47 and 50** explicitly contain AI-assisted revised/restored clauses (C07 and C08). They retain `ai_translation=true` and an explicit `source_declaration.classification=ai`, taking precedence over the new-book Human default. The session-declared model is **GPT-6 Astra Pro**; the backend model identifier and reasoning effort were not exposed and remain null. Translation hashes, corrected clause hashes, source unit IDs and review evidence are retained. `human_review=false` is explicit. The rest of the original report is not relabelled as newly AI-authored.

Extraction used the native PDF text, a real Tesseract OCR cross-check and visual inspection, so `ocr_used=true`. Completed source QC covered all **25 original pages**, **621 units**, **58 notes** and **93 primary reference occurrences**. The saved review scope does not certify every codepoint, a word-for-word translation, every chain or an independent final repository release. Four secondary edition references remain unverified, and source interpretation qualifications are retained.

## Reproduction and verification

After the initial archive is staged, the importer works fully offline:

```sh
python scripts/import_japanese_fadael.py
python -m unittest discover -s tests -p test_japanese_fadael.py
```

The optional first-stage command is `python scripts/import_japanese_fadael.py --workspace /path/to/completed/workspace`. Pinned original/corrected JSON, PDF and reference-map hashes prevent silent substitution. Changed archived inputs fail validation instead of being overwritten.

The importer checks the `material_registry` projection and applies the current provenance policy, expecting 55 Human and 2 AI readings without changing their source AI flags. Focused tests cover exact text/ID preservation, complete unit/note coverage, reference correction and parallel scopes, original/corrected file hashes, translation-origin display, idempotent offline regeneration and preservation of additive parent-owned binding sidecars. The importer does not commit, push, deploy, or change the global reader/catalog/UI code.
