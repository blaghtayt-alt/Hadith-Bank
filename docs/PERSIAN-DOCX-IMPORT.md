# Persian DOCX import — 11 November 2026

Nine owner-supplied native DOCX files produce **6,805 source occurrences**. The
combined reader contains **21,458 occurrences**, preserving the **14,653**
records already published before this integration. Persian now has **7,078**
occurrences: the **6,805** new source occurrences and **273** previously
registered legacy occurrences. These counts describe
source occurrences, including repeated quotations and versions; they are not
counts of unique complete Prophetic narrations.

The original prepared import was based on 13,488 existing records and produced
a 20,293-record reader. Its historical extraction and HTML reports are retained
unchanged. The combined integration preserves the later legacy extraction,
Unknown translation classifications and OCR-only display policy. The final
comparison is recorded in `reports/persian-merged-publication-verification.json`.

## Reconciled counts

| Source edition | Main text occurrences | Separate variants | Additional excerpts | Total |
|---|---:|---:|---:|---:|
| Faiz al-Bari, volume 1 | 323 | 0 | 89 | 412 |
| Faiz al-Bari, volume 2 | 376 | 1 | 74 | 451 |
| Faiz al-Bari, volume 3 | 427 | 1 | 76 | 504 |
| Faiz al-Bari, volume 4 | 389 | 0 | 77 | 466 |
| Faiz al-Bari, volume 5 | 307 | 0 | 30 | 337 |
| Faiz al-Bari, volume 6 | 403 | 0 | 54 | 457 |
| Mukhtasar Sahih Muslim, volume 1 | 1,072 | 0 | 32 | 1,104 |
| Mukhtasar Sahih Muslim, volume 2 | 1,118 | 0 | 10 | 1,128 |
| Riyadh al-Salihin, Heravi edition | 1,896 | 0 | 50 | 1,946 |
| **Total** | **6,311** | **2** | **492** | **6,805** |

The 492 ancillary entries comprise 489 hadith quotation occurrences and three
explicit Companion quotation occurrences. Some quotations are fragments, or are
available in only one language. Their types and missing fields are preserved.
They do not inherit a blanket authenticity grade or canonical collection merely
because they appear in a commentary on that collection.

## Scope and text policy

The source translations are credited to **دکتر عبدالرحیم فیروز هروی** (Faiz
al-Bari), **عبدالقادر ترشابی** (Mukhtasar Muslim), and **عبد الله خاموش هروی**
(Riyadh). Their source title-page evidence is retained in each material's
`source-metadata.json`. The reader classifies the existing Persian translations
as **Human**. No new translation was produced.

Faiz al-Bari is a translation/commentary of an **abridgment** of Bukhari; the
Muslim source is al-Mundhiri's **Mukhtasar**. Neither local numbering scheme is
silently treated as the full canonical collection's numbering. Printed original
collection citations are preserved as source-cited references, without claiming
independent canonical matching. Printed source gradings are metadata, not a new
bank authenticity judgment.

Per the owner's instruction, separable translator comments, editorial
explanations and footnote prose do not enter the narration text, search
annotations or HTML records. Clear additional reports quoted within those
notes have their quoted words retained as separate excerpt records; their
surrounding explanation is excluded. Ordinary parentheticals that form part of
the translation, narrator explanations within the report, and narration
variants are not removed by a blanket punctuation rule.

All Persian canonical records have empty commentary and footnote fields. The
no-QC display policy is explicit and scoped to these nine native DOCX imports.
The reader, Markdown and CLI do not attach QC/review labels to these records.
This instruction is not recorded as an independent certification pass.

## Completeness and source defects

All **35,654 body paragraphs** from the nine DOCX files are accounted for in
source ledgers. Footnote parts are also captured. No batch limit or
deduplication was used.

* Faiz al-Bari has 2,230 numbered source positions. Five positions contain only
  references to other entries, with no narration text. Their pointers are
  retained in the audit rather than counted as fabricated text records. The
  remaining 2,225 main text occurrences include local 1590 with no supplied
  Arabic and the surviving Persian fragment between 1770 and 1772. The latter
  has **no printed number assigned**: 1771 is recorded only as the inferred
  sequence position. Its source explicitly warns of missing material.
* Muslim preserves eight letter-suffixed serials, both distinct entries printed
  as 1193, and three unnumbered narrations. The report between 1340 and 1342 is
  preserved without inventing a surviving printed 1341 label.
* Riyadh contains all 1,896 sequence positions, including malformed headings
  and 31 source numbering/label anomalies. Printed Arabic and Persian labels
  remain separate from the reconstructed sequence.

Reliable per-occurrence printed pagination cannot be established from these
DOCX files. Zero-based OOXML paragraph locators are used. Where a chapter's
table of contents supplies a page, that value is retained as heading metadata,
not presented as the hadith's page.

## Font handling

Native Word custom fonts encode many honorifics as ordinary letters or private
symbols. Decoding is scoped to explicitly identified CTraditional Arabic and
AGA Arabesque font runs, with original tokens, transformations, font hashes and
rendered glyph evidence retained outside the reader payload.

Muslim local 285 contains a Quran quotation in legacy HQPB symbols. The matching
publisher paragraph was retained as evidence and supplies exactly
`﴿ قٓۚ وَٱلۡقُرۡءَانِ﴾`; no further Quran wording was supplied. The adjacent
literal `ب` is treated as a preposition through a specifically documented
contextual interpretation, because both source formats apply symbol styling
there. This is a scoped recovery, not a general HQPB font map. The complete
paragraph alignment and the original symbol sequence are recorded in
`imports/persian-docx-20261111/audit/muslim/publisher-text-recoveries.json`.

Seven literal private-use characters in the Muslim files have lost their
special-font assignment: the inherited IRNazli font does not map those
codepoints, and the publisher HTML retains them too. Six `U+F020` spacing
positions are converted to ordinary spaces. One `U+F072` after `آنحضرت` in
local 137 is interpreted as the corresponding verified AGA salawat glyph.
These are explicitly scoped **contextual recoveries**, not claims of a direct
IRNazli mapping. Original codepoints, offsets, font evidence and the inference
are retained. Ordinary-font source abbreviations such as `ص` and `÷` remain
as supplied; no global Arabic-letter substitution is used.

## Reported doctrinal and excerpt findings

The screening includes Arabic and Persian narration text and the additional
excerpts, not only the discarded notes. No explicit Shia-specific doctrinal
assertion was identified in the reviewed candidate contexts. This is targeted
screening and contextual review, not exhaustive theological certification.
Mentions of Ali, the Prophet's family, twelve rulers, or family blessings alone
were not treated as sufficient sectarian evidence. No narration was deleted
because of a doctrinal-screening result.

The owner was warned about the following concrete passages:

1. **Excluded translator note:** Riyadh local 1251, body paragraph 6893, begins
   `ش: در بینش شیعه روزهء روز دهم محرم (عاشوراء) ناپسند است`. This note explicitly
   describes a Shia view and makes an associated historical claim. It is not
   hadith text and does not establish the translator's affiliation. The note
   is excluded from every canonical narration/search record; the Ashura hadith
   itself is retained.
2. **Context needed inside a narration:** Faiz al-Bari volume 6, local 1844,
   cited Bukhari 5117–5118, reports temporary-marriage permission. Its own
   chapter heading states the final prohibition. Volume 5, local 1651, cited
   Bukhari 4216, reports prohibition. Both reports and their source headings
   remain. This finding does not establish Shia interpolation.
3. **Source-stated weak-chain excerpt:** `fa-faiz-al-bari-v5-fn324-p2-q001`,
   `«فاطمه و دو فرزندش»`. The source commentator, citing Ibn Kathir, describes
   the report's chain as weak. The quotation is a fragment; that source
   assessment and its scope are retained.
4. **Source-stated weak-chain excerpt:** `fa-faiz-al-bari-v6-fn353-p2-q001`,
   `«حاکم نباید جز در حالتی که سیر و سیراب باشد، قضاوت نماید»`. The source says
   Bayhaqi relates this with a weak chain. That is preserved as the source's
   assessment, not an independent new grading or a sectarian classification.

Detailed evidence is in the family screening reports under the import audit.

## Tagging and integration

`topic_tags` remains empty because no publisher taxonomy was supplied.
`source_structure_tags` retains the exact chapter/section text, source origin,
hierarchy, actual heading metadata and the narration locator's scope.
`editorial_tags` uses the existing `import_pipeline_not_publisher` origin and
the established source/language/method/book/edition/format/kind/text-availability
prefixes. No `review:` or `qc:` tags are added.

The original DOCX bytes, canonical records and manifest SHA-256 values are
stored in `materials/fa-*/`. Compressed upstream extraction snapshots and
removed-source audits are separate under `imports/persian-docx-20261111/`.
Only `records.jsonl` files declared by the nine manifests enter the reader.
The audit and original documents intentionally preserve source material that
the owner excluded from narration display.

To regenerate from the retained final extraction snapshots:

```bash
python scripts/import_persian_docx.py --root .
python -m unittest discover -s tests
python scripts/refresh_bank.py --root . --site-output _site
```

The first command preserves every final text field exactly and gates the full
per-source counts. The refresh command checks manifests and source hashes,
rebuilds search/Markdown/HTML, and verifies the embedded record payload. The
upstream source-aware extractors and raw ledgers are preserved for additional
inspection. Rights remain unassessed; no new license is inferred.
