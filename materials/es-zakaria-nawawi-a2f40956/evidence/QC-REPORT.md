# Targeted independent source-fidelity QC: Zakaria Maza Vielva, Hadiz 2

**Decision: PASS — source fidelity within selected Spanish Hadiz 2 only.** No repository writes, publication or whole-book approval.

## Verified inputs

- Input ZIP SHA-256: `65d49ec6a599254956fc09e3b41e99bdbf730ab20cf539553df0e78264037576`; archive CRC passed.
- All **8** payload files in `selected-manifest.json` matched SHA-256 and byte size.
- Full unmodified **89-page** PDF SHA-256: `a2f40956637a0ffbb38595fbd1aecd05c7cb6dfa0436d374e6bfc689ae12bdf2`.
- Page 2 visibly prints **LOS CUARENTA HADICES**, **Del Imán An-Nawawi**, **Traduccion — Zakaria Maza Vielva**. This named translator evidence comes from the page image, not the PDF metadata's technical `Author` field.

## Source boundary and coverage

- Physical PDF 5 (printed 4) includes **Hadith 1 Spanish conclusion**, followed by **Arabic Hadith 2 beginning**.
- Physical PDF 6 (printed 5) finishes the original Arabic Hadith 2, then starts Spanish **HADIZ-2.** and its narrator introduction (8 selected Spanish lines).
- Physical PDF 7 (printed 6) continues Spanish Hadith 2 (22 selected Spanish lines).
- Physical PDF 8 (printed 7) completes Spanish Hadith 2 and prints **Lo relató Muslim.** (14 selected Spanish lines); Arabic Hadith 3 starts immediately afterward.
- Physical PDF 9 (printed 8) begins **HADIZ-3.** in Spanish (boundary check only).
- Total: **44 selected printed Spanish lines** across three pages; **13 textual segments**, including heading, introduction, complete narrative and final attribution. Page furniture, adjacent Hadiths and Arabic are excluded *only from the Spanish display*. The original Arabic and complete 89-page PDF are retained unmodified under `source/`.

## Fidelity result

The entire selected Spanish span was checked against independently rendered PDF pages, with text-layer line coordinates used as an extraction cross-check. `transcription/hadith2-source-line-layout.txt` preserves line-by-line wording and page-aligned paragraph sequences; `transcription/hadith2-display-paragraphs.txt` changes only physical line wraps and justification spacing. **No words, punctuation, narrator information, or Muslim attribution were corrected, inserted or omitted.** Exact non-whitespace character sequence of the two text artifacts agrees, validated programmatically.

Published details kept untouched: **harapientos**, **ha venido a vosotros**, **Sus Angeles**, **Imán!’dijo:**, **Hora!’Y**, and the printed **Din!’’’**. These are reproduced as printed, not offered as a corrected edition. The user’s selection of *harapientos* is respected; no semantic objection was reopened.

**No extraction errors found in the selected source transcription.** The atypical original punctuation/orthography above is logged as printed-source typography, not an extraction failure.

## Scope and downstream controls

Only **source-to-Spanish transcription fidelity for this single selected edition and narration** passed. This does **not** assert the edition's translation is semantically equivalent to every Arabic version, attest full-book accuracy, approve publication, independently audit translation-production methods or settle repository ownership/rename coordination. The original, separately held Isa Garcia edition is not included in the new text or changed.

## Key included artifacts

- `transcription/hadith2-display-paragraphs.txt` — complete exact Spanish edition text, formatted for display.
- `transcription/hadith2-source-line-layout.txt` — original source line boundaries for audit.
- `selected-hadith2-record.json` — source/edition-specific metadata and page/segment alignment.
- `qc-findings.json` — tests, coverage and issue ledger.
- `source/islamenespanol-mirror.pdf` — exact unchanged original including Arabic.
- `visual-evidence/original-p2-210dpi.png`, `original-p5-210dpi.png`, `original-p6-210dpi.png`, `original-p7-210dpi.png`, `original-p8-210dpi.png` — independently rendered evidence.
- `output-manifest.json` — SHA-256 and byte sizes of all other ZIP members.

The ZIP's own SHA-256 is provided separately in `zakaria-nawawi2-selected-qc.zip.sha256` because a ZIP cannot include its own final hash without changing that hash.
