# 穆宛塔圣训集 — Muwatta of Imam Malik

This material contains the owner-supplied Chinese Word edition of the Muwatta,
identified in its preface with Muhammad ibn al-Hasan al-Shaybani. The translator
credit is **穆萨·余崇仁** (Musa Yu Chongren), dated
**2000年十月二十三日于韦州**. The electronic edition credits 绿色中华网站 and
prints `www.xaislam.com`.

The original Word file is stored unchanged as
[穆宛塔圣训集_Muwatta_Chinese.docx](穆宛塔圣训集_Muwatta_Chinese.docx).
The reader offers a direct original Word download. Its display title places the
Chinese name before the English name and identifies the al-Shaybani recension.

## Imported source occurrences

The bank contains **1,006 source reports** from this supplied file across
19 major books and 434 subsection headings: 1,005 explicitly numbered reports
and one unnumbered report. The numbering runs from 1 to 1008 but does not print
196, 528 or 764. An unnumbered Abu Hurayra report occurs between 527 and 529;
its number remains null. No missing number or text is invented.

These are source occurrences, including Prophetic, Companion and Successor
reports; they are not a count of unique Prophetic sayings. All printed numbers
belong to this Chinese source edition. They are not mapped to the commonly
indexed Yahya recension or a canonical provider ID. Arabic originals, English
counterparts, grades and missing narrator information remain unknown unless
supported by separate evidence.

Separate al-Shaybani commentary, translator notes and reviewed inline
explanations are excluded from narration/search text. **594 excluded segments**
remain verbatim in `excluded-commentary.json.gz` and the original document.
Front matter, back matter and headings are retained in the full paragraph ledger.
Brief translation glosses and transmitted narrative details are preserved.
Hadith quotations embedded within excluded commentary have not been separately
extracted as bank occurrences. The 1,006 count covers the main numbered reports
and the identified unnumbered body report, not every quotation anywhere in the
document. Those additional quotations remain available in the original Word
file and source audit.

Report 64 retains its continuation. Report 135 retains Ibn Shihab's addendum as
a separate paragraph within the source occurrence. Reports 453, 604, 606, 621,
960 and 972 refer to preceding material and retain that short source wording;
their missing full quotations are not reconstructed.

## Reproduction and evidence

Run from the repository root:

```console
python scripts/import_chinese_muwatta.py
python scripts/refresh_bank.py --root . --site-output _site
```

The source-specific importer checks the exact DOCX checksum before extraction.
Every retained character is linked to spans in `native-text.txt`, whose only
serialization convention is two newlines between source paragraphs. The
compressed paragraph ledger accounts for all 2,067 body paragraphs, preserving
each paragraph's original text, style and contiguous classification spans.
The source-number ledger records every imported occurrence without renumbering.

The source SHA-256 is
`cf65c0e865be95a709f228b021e23b94dbc2e3a88d52139330b623a070f5d1b3`.
Extraction reads native DOCX XML; no OCR or translation is performed during
this import. The upstream transcription method is not established by the file.
Publication is authorized by the owner's request and recorded in `manifest.json`.
That decision does not assert an independent Pro certification or a new reuse
license; those facts remain explicit in the source metadata.
