# Japanese Sahih Muslim — volume 1 source intake

## Deliverable and scope

This package contains **1,811 structured source occurrences** extracted from the supplied **580-page WEB版　日訳サヒーフ・ムスリム PDF**. It follows the standalone Hadith Bank attachment candidate schema and the language → book → edition organization.

The body contains **volume 1** labels only, with **327 source sections** and section-level print-page references spanning **1巻 P.27–574**. The front matter describes a three-volume Japanese translation; the supplied file does not establish completeness of all three volumes or even every printed volume-one occurrence. Preserve this scope in the catalog.

| Source occurrence kind | Count |
| --- | ---: |
| Narration/source report text | 1,406 |
| Variant wording/report occurrence | 214 |
| Abbreviated route/reference occurrence | 191 |
| Total source occurrences | 1,811 |

These are source-occurrence counts, **not a count of unique canonical Hadiths**. Classification remains an extraction classification, not a final authenticity or semantic classification. A shortened reference stays shortened; no full text is manufactured to fill it.

## Files and organization

The main JSON is `languages/ja/books/muslim/editions/pdf-c859ce57c211ea1b/records.json`. It is a UTF-8 JSON **array**, one object per extracted source occurrence. `records.jsonl` in the same directory contains the identical objects, one per line. The directory also contains `sections.json`, `footnotes.json`, and an edition manifest.

`source.json` contains the work, compiler, translation credits, publication history, Arabic base editions, PDF metadata, scope and evidence. `sources/ja-muslim-web.pdf` is the exact supplied original. `evidence/raw-pages.json` and `evidence/lines.jsonl` preserve every embedded-text page and line. `evidence/line-attribution.jsonl` assigns every character to narration, note, commentary, heading, reference, front matter or colophon. All offset values count Unicode codepoints into the original line **plus its terminal LF**, starting at zero.

`reports/coverage.json`, `reports/page-coverage.jsonl`, `reports/exceptions.json`, the boundary correction log and reviewer reports record completed checks and unresolved work. `SHA256SUMS.txt` pins the package files. No other repository or remote file is required to read the material.

## Record fields

| Field | Meaning |
| --- | --- |
| `id`, `record_id`, `occurrence_id` | Same stable identity, based on source hash and PDF line/character position. |
| `sequence_in_source` | Extraction order; **never a Hadith number**. |
| `text.translation` | Source Japanese report/variant text with original extracted characters and line endings. It includes the printed narrator introduction. |
| `text.arabic` | Null: the source supplies no complete Arabic narration originals. |
| `source_unit_text_verbatim` | Whole source occurrence with its physically following notes/commentary, preserved for auditing. |
| `embedded_arabic_fragments` | Exact short Arabic terms/fragments occurring in Japanese text or notes; raw order retained and flagged. |
| `narrator` | Source opening attribution, lexical name/descriptor where identifiable, and evidence. No reconstructed full chain or normalized person identity. |
| `book` | Collection, literal short/expanded source headings, section ID, volume and asset edition ID. |
| `number` | Printed/canonical numbers remain null because none were established. |
| `page.pdf` | Exact PDF pages covered by the source occurrence and its physically attached components. |
| `page.printed` | Exact printed section reference. Scope is explicitly `section`; precise narration print pages are not guessed. |
| `translator` | All three credited translators retained; `name:null` where per-occurrence assignment is unverified. |
| `footnotes`, `commentary`, `references` | Separate source components and cited-reference candidates with locations. |
| `source_structure_tags` | Literal headings and volume labels with evidence. |
| `topic_tags` | Empty as required by the current candidate schema; no publisher taxonomy was supplied. |
| `related_source_entries`, `related_versions` | Contextual route links and exact-text links; no automatic canonical-equivalence claim. |
| `review`, `rights`, `metadata_gaps` | Pending independent review and publication qualifications, separate from successful extraction. |

All original repeated occurrences remain. The repeated article on PDF356–359 and the out-of-order print-page reference on PDF470 are recorded as source anomalies. Source spellings are not silently repaired. The composite ascent account on PDF121–123 retains explicit embedded transmission attributions; final canonical route alignment remains pending. The note links on PDF151 preserve physical position and also identify the earlier source markers they explain.

## Human translation and source evidence

The source credits **磯崎定基、飯森嘉助、小笠原良治** (PDF6). Its front matter describes an original **1987** Japanese publication by **日本サウディアラビア協会**, a **2001** reprint by **日本ムスリム協会**, and a web foreword dated **2009-11-20** (PDF2,5–6). The dated named credits support `ai_translation:false` throughout. This status concerns the historical Japanese translation. Extraction and structuring are separately marked `ai_assisted_extraction:true`.

Per-occurrence translator attribution is not guessed from the approximate division in the foreword. The exact source wording of that division, including 斎戒の書, is preserved in metadata. The PDF's 2013 creation metadata is not asserted as a publication date. The colophon URL is preserved as printed and was not live verified.

## Search

The search script uses Python's standard library and reads the actual records. It searches across PDF line wraps using a normalized comparison view; source strings remain untouched.

```bash
python scripts/search.py "天国" --has-report-text --limit 5
python scripts/search.py --narrator "アーイシャ" --limit 5
python scripts/search.py --section "ウドゥー" --pdf-page 194 --limit 0
python scripts/search.py --record-type variant_reference --limit 3
```

Add `--full` to return complete record objects or `--id ID` to retrieve a specific occurrence. Use `--text-only` to exclude headings and notes from keyword matching. JSON and JSONL inputs are both supported with `--records PATH`.

## Validation and reproducibility

Install `requirements.txt` to run the validator or reproduce extraction. Search itself has no third-party dependencies.

```bash
python scripts/validate_japanese_muslim.py --root . --report reports/local-validation.json
python scripts/rebuild.py --root . --output-dir rebuilt-candidate
```

The rebuild directory must be new or empty. Rebuilding verifies the original source SHA-256, re-extracts the text layer, applies the frozen boundary decisions and compares regenerated JSON/JSONL hashes to this package. It does not conduct new semantic or visual review. Pinning the supplied PyMuPDF version preserves the extraction behavior.

The independent mechanical checks cover **580 pages, 14,819 lines and 435,835 codepoints including LF**, with every text-layer codepoint assigned exactly once. JSON/JSONL equality, schema, IDs, page links, note/commentary components, Arabic fragment slices and related-record links are checked. Detailed results are in `reports/validation.json` and `reports/independent-integration-review.json`.

**19 of 580 original page images were inspected** for selected metadata/layout/boundary/Arabic issues. This is not a full visual character-fidelity pass. Targeted boundary reviews and their actual inspected contexts are logged. Full independent final evaluation, exhaustive semantic boundary/ancillary quotation review, canonical numbering/Arabic/route alignment and scoped grading remain pending.

## Merge into the bank

`merge-manifest.json` contains the package catalog entry and a repository-prefixed form. Stage this complete package under the distinct intake root `attachments/attachments-ja-muslim-c859ce57c211ea1b` so its source/evidence files cannot overwrite another intake. All paths inside the canonical records are package-root-relative. Register the language/book/edition catalog entry and regenerate the bank's search views.

The current bank view builder may hardcode an earlier intake. Its translator detection also needs to honor this package's explicit `translation_provenance.kind = human_translator_credited`; the per-occurrence `translator.name` remains null without contradicting established human authorship. When producing the normalized bank search schema, map that `kind` to `origin` and preserve the underlying evidence. Use `benefits:{}` if that key is emitted, for compatibility with the existing search runtime.

This package is **ready for private candidate intake** with `release_status:private_candidate`, `independent_pro_qc:pending` and `release_eligible:false`. It has not been merged or publicly published. Public web availability in the source does not establish a redistribution license. The source review and publication gates remain separate from the mechanical extraction pass.
