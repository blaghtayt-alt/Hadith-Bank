JA KETAB EL FADAEL — FULL TEXT EXTRACTION / OCR CROSS-CHECK

Source: ja_ketab_elfadael.pdf, 25 PDF pages.
Title: 諸々の徳（ハディース集）② / كتاب الفضائل

START HERE
- ja_ketab_elfadael_extracted.txt: readable UTF-8 visible transcript, with explicit PDF-page boundaries.
- ja_ketab_elfadael_pages.json: structured pages, source lines, coordinates, original and OCR text, and separated footnotes.
- ja_ketab_elfadael_verification.json: scope, corrections, hidden-text handling, coverage checks and limitations.

METHOD AND COVERAGE
All 25 pages were extracted with both PyMuPDF and Poppler. All 25 rendered source pages received a direct line-by-line image comparison. Independent Tesseract OCR was run at 300 dpi using Japanese/English and Arabic as appropriate. Raw OCR is retained as evidence, not treated as authoritative.
There are 58 footnotes: 57 source-reference/attribution notes and one translator commentary (note 19). These counts are NOT a count of verified hadith records.
All inline footnote markers 1–58 and footnote texts 1–58 are present. No page was skipped.

TEXT POLICY
Japanese source wording, source reference numbers, punctuation, and original editorial inconsistencies are preserved. Arabic reading-order defects are repaired from the visible page. The visible IslamHouse.com logo is transcribed on each page. Decorative flourishes are stored separately from language. The back-cover running title/page 23 exists in the underlying PDF text layer but is covered by artwork: it is preserved in raw data and excluded from the visible transcript. Poppler's extra cover-page 8 characters are also absent from the image and are not included in the transcript.
The body and footnotes remain separate in JSON. Source line wrapping is preserved in TXT. Page boundary labels are editorial, not original book text. Layout padding and excessive blank lines are simplified. All original unmodified extraction data remains in raw/.

AI TRANSPARENCY
No new translation was generated. The PDF names its translator but does not establish the use or absence of AI, so ai_translation is unknown. The task used AI-assisted visual transcription/review of the source and automated text extraction/OCR.

LIMITS
This is an extraction with complete page/line visual coverage, not a certified character-by-character critical edition. Source references were not authenticated against external collections. Hadith occurrences have not been segmented for a specific live importer, and nothing was published to the Bank.

PACKAGE
source/: unchanged original PDF.
raw/: unchanged extractor outputs and per-page text/span data.
ocr/: raw Tesseract text and TSV coordinates/confidence, comparison results, run log and model provenance.
reviews/: page-specific image-review findings.
scripts/: the extraction/verification and OCR workflow used for this task; original workspace layout is expected if rerunning without modification.

Source SHA-256: 09a7f220e7bcf5152520913de57031bb840c80367566cfa71a61ded20bd6acde
