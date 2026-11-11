# 伊本·马哲圣训集 — Sunan Ibn Majah

This registered Chinese source is the supplied 487-page scan, translated by 穆萨·余崇仁 and published by 宗教文化出版社. The colophon identifies the first edition as April 2013 and this printing as November 2013. The ISBN is 978-7-80254-670-7. Bibliographic evidence is on PDF pages 2 and 486.

## Imported scope

The material contains **4,354 numbered source occurrences in 39 chapters**, from PDF pages 64–479 (printed pages 1–416). Every chapter's local sequence is checked from 1 through its final printed number. The generic introduction mentions 4,341 hadiths; that statement is retained in the audit and does not replace the actual enumeration in this Chinese edition.

The numbers restart in each chapter. A reader reference such as `2:137` means Chinese source chapter 2, local entry 137. It is **not** a global canonical Ibn Majah number. Canonical Arabic/English matches remain unknown unless separately supported by source evidence. Repeated source occurrences have not been deduplicated.

The published translator states that full narrator chains were abridged (PDF pages 15–16). Available Chinese attribution text is preserved; missing Arabic text, complete isnad and authenticity grades remain null. The title does not imply that all narrations are authentic.

## Source and extraction

- Original PDF: [`伊本·马哲圣训集_Sunan_Ibn_Majah.pdf`](../materials/zh-cn-ibn-majah-yu-2013/伊本·马哲圣训集_Sunan_Ibn_Majah.pdf).
- Original SHA-256: `e3bc24bcee435894fc3826622839dd819f8c79eb83af5252f5389831fa76b383`.
- Material: `materials/zh-cn-ibn-majah-yu-2013/manifest.json`.
- Edition: `yu-2013-pdf-e3bc24bcee435894`.
- Canonical data: `materials/zh-cn-ibn-majah-yu-2013/records.jsonl`.

The PDF is the text authority. Its embedded OCR was created by ABBYY FineReader PDF 15. The importer preserves the raw page text and line geometry before separating numbered narrations from page headers, footers, chapter/section headings and footnotes. Narrations continuing onto another page retain all contributing PDF and printed page locators. Qur'an quotations and source citations that form part of a narration remain within that occurrence.

The supplied TXT was not used. Individually checked OCR repairs retain before/after text, page evidence and source-image crops in `audit/verified-corrections.json`, `audit/additional-body-corrections.json`, and `audit/applied-corrections.json`. Removed material remains in the compressed source audit; it is not silently discarded or mixed into narration search text.

The source is a credited published human translation. The owner subsequently requested no further OCR work or OCR/QC labels for this outsourced book. Its source-specific manifest decision suppresses those badges and excludes these records from the pending-review banner. The supplied PDF's existing ABBYY OCR metadata, original extraction records and correction evidence remain unchanged. Automated structural checks, targeted image corrections and an independent sample review are recorded separately from full character-level review. **The display decision does not assert independent Pro QC or narrational authentication; no certified release is claimed.**

The owner's current request authorizes this book, its original PDF and its registered reader/search views to be added to the public bank. This publication decision does not assert a new publisher license. Original rights notices remain in the source, and reuse rights remain unassessed.

## Reproduce the extraction and reader

The importer requires PyMuPDF and Poppler `pdftotext`; recorded dependency versions are in the source metadata. It rejects a PDF whose SHA-256 differs from the identified source.

```bash
python scripts/import_chinese_ibn_majah.py --pdf /path/to/736950612-1.pdf
python scripts/register_material.py --root . --directory materials/zh-cn-ibn-majah-yu-2013 --language zh-CN --book ibn-majah --edition yu-2013-pdf-e3bc24bcee435894 --name '伊本·马哲圣训集 — Sunan Ibn Majah' --records records.jsonl --source '伊本·马哲圣训集_Sunan_Ibn_Majah.pdf' --replace
python scripts/refresh_bank.py --root . --site-output _site
```

An intentional extraction correction requires the correction evidence, regenerated records and updated manifest together. Preserve occurrence IDs, the original PDF and raw extraction evidence. A new independent review must bind to the final candidate's exact hash; a later edit cannot inherit an earlier review silently.

The existing website workflow regenerates the catalogs, browse pages, search shards and reader from this manifest. In Chinese views, collection labels show the Chinese title before the English title. Other languages retain their existing labels.

## Preserved transfer evidence

The completed recovery transferred 66 verified parts and restored all 94 canonical material files without changing the source PDF or records. The [transport manifest](../imports/chinese-ibn-majah-20261111/transport/manifest.json) retains the archive identity and exact file/hash inventory; the [executed integrity report](../reports/chinese-ibn-majah-transport.json) records the successful restoration and occurrence checks. Temporary binary parts and the one-use restore workflow were removed after restoration to avoid keeping a second copy of the source package in the published tree. These two retained JSON files are historical transfer evidence, not a separate downloadable archive.
