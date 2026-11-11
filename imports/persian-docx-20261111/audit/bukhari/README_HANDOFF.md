# Faiz al-Bari Persian extraction handoff

The six uploaded DOCX volumes are a Persian translation and commentary of an abridgment of Sahih al-Bukhari. They are not the complete canonical collection. The named source translator/commentator is Dr. Abdulrahim Firooz Heravi (دکتر عبدالرحیم فیروز هروی); the translation provenance is Human.

## Integrate these three files

| File | Rows | Meaning |
| --- | ---: | --- |
| hadith_only_primary_records.jsonl | 2,225 | Source numbered text positions, including one clearly labeled surviving fragment |
| variant_records.jsonl | 2 | Separately supplied unnumbered Arabic/Persian variants |
| explicit_hadith_quotation_records.jsonl | 400 | 399 quoted Hadith excerpts and 1 correctly attributed companion quotation |
| **Total** | **2,627** | Unique source-occurrence IDs; no batch limit |

| Volume | Numbered text positions | Unnumbered variants | Ancillary excerpts | Integration rows |
| --- | ---: | ---: | ---: | ---: |
| 1 | 323 | 0 | 89 | 412 |
| 2 | 376 | 1 | 74 | 451 |
| 3 | 427 | 1 | 76 | 504 |
| 4 | 389 | 0 | 77 | 466 |
| 5 | 307 | 0 | 30 | 337 |
| 6 | 403 | 0 | 54 | 457 |
| **Total** | **2,225** | **2** | **400** | **2,627** |

The five source positions containing only a pointer to an earlier narration are preserved in reference_only_positions.jsonl but excluded from text-record totals. They are local numbers 231, 429, 870, 961, and 1774. All 2,230 original source positions remain in primary_records.jsonl for audit.

## Reader text and attribution

Use the final `text.arabic` and `text.translation` fields. Honorific glyphs are decoded only in runs explicitly using the verified CTraditional Arabic font. Raw strings, run metadata, exact source paragraph locators, and transformation evidence remain separately preserved. Exact trailing printed source citations were moved from Arabic narration text into references metadata. Arbitrary bracketed text was not stripped.

All separable commentary and footnote prose is excluded from the integration text. All 2,703 footnotes remain in the source archives; 400 exact quotation excerpts are separately included where attribution could be supported. Two detached source editorial paragraphs are excluded. Inline parentheticals within the translated narration remain as printed. Canonical main records have null commentary and empty footnote arrays. No QC tags were added.

`supporting_records.jsonl` is an audit file containing commentary context and ambiguous candidates; do not integrate it. Ancillary excerpts may cite other Hadith collections or lack a precise reference. Do not label all ancillary material as canonical Bukhari or give it a blanket sahih grade. One quotation, fa-faiz-al-bari-v5-fn225-p0-q001, is Ali's speech and is correctly typed companion_report rather than Prophetic Hadith.

## Source defects retained

- Local 1590, volume 5 paragraph 697: the source supplies a substantive Persian translation but no Arabic narration. Arabic remains null.
- Inferred source sequence position 1771, volume 5 paragraph 1882: only a Persian fragment survives. The source itself says printed page 391 / Word page 270 is incomplete. No missing Arabic, number, or text was invented.
- Numbering typos, duplicates, citation-label typos, and unscoped references remain as printed. See numbering_and_source_exceptions.json for all 37 recorded exceptions.
- Exact zero-based XML paragraph locators are authoritative. Printed page numbers were not inferred from Word pagination.

## Screening findings

hadith_content_screening.json binds the screening findings to the final input hashes. All 2,627 integration records were mechanically scanned; 108 localized matches in 79 distinct records were reviewed. No explicitly Shia-specific doctrinal assertion was identified in those matched contexts. This is targeted screening, not a universal theological certification or independent authentication of all Hadith references.

Three concrete content flags should be reported:

1. Volume 6 local 1844 (source cites Bukhari 5117–5118) reports temporary-marriage permission. Its own chapter heading explicitly states the final prohibition; volume 5 local 1651 (source cites Bukhari 4216) contains a prohibition narration. Preserve the chapter metadata so the permission excerpt is not misleadingly isolated. This is a context warning, not evidence of a Shia interpolation.
2. fa-faiz-al-bari-v5-fn324-p2-q001, «فاطمه و دو فرزندش»: the source explicitly calls the chain weak. Preserve the scoped source-grade metadata.
3. fa-faiz-al-bari-v6-fn353-p2-q001, «حاکم نباید جز در حالتی که سیر و سیراب باشد، قضاوت نماید»: the source explicitly describes the chain as weak. Preserve the scoped source-grade metadata.

Twelve-rulers wording, family virtues, prayer leadership, general divine protection, Hajj tamattu, and the place-name Ghadir al-Ashtat were reviewed without treating those topics alone as proof of Shia doctrine. No record was omitted or rewritten on ideological grounds. Separate source-commentary discussions are in doctrinal_review.json and are excluded from the reader.

## Reproduction and validation

Run extract_bukhari.py, validate_bukhari.py, and build_screening_audit.py with the configured primary Python runtime. The validator passed for all six unchanged original DOCX hashes, all 15,714 body paragraphs, all 8,256 footnote paragraphs, all 23,970 coverage-ledger entries, every reconstructed primary/variant record, and every exact ancillary quote span. It also checks unique IDs, empty commentary fields, and scoped grading-evidence spans. Canonical citations were not independently verified against an external edition.

file_hashes.json inventories the final integration and audit deliverables. HTML integration and publication are handled by the parent task; this extraction handoff does not itself claim the live site is verified.
