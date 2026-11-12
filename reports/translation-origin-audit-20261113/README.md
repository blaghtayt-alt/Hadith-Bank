# Reviewed legacy translation-origin decisions

[See the 191 reviewed occurrences](decisions.csv). Each row is a **primary translation source occurrence** with its stable ID, language, source book, reported references and their scope, source URL, classification, named translator where known, evidence locator, model and review status. The source number is transcribed from the supplied source reference; it is not an independently verified canonical numbering claim. CSV cells that could be interpreted as spreadsheet formulas are prefixed with an apostrophe for safe viewing. Quotation text is not reproduced in this index.

The review began with 1,165 occurrences displayed Unknown in the 80,763-occurrence catalog at base commit `ca5f3f18e682376ce2c91e5f97f4b0d7e24eb4c6`. It identifies 187 AI-translated primary occurrences from explicit translation-status statements in their retained source records: 72 Persian, 76 Hindi and 39 Chinese. The original source bytes and each selected translation span were checked against their recorded hashes. The historical statuses refer to AI translation/review or pending verification; they do not establish independent human review, actual model, accuracy or authenticity.

Four additional occurrences, three Japanese and one Uzbek, have source-matched translator credits. The historical source text and source-credit findings are documented in `sources/translation-origin-evidence/2026-11-13/legacy-selected-source-audit.txt`; that file is an audit note, not a copy or checksum of the linked primary documents. Nine more records carry historical AI flags but their per-quotation attribution scope remains unresolved, so they remain Unknown. The other occurrences have not all been independently researched; Unknown is not evidence of either human or AI translation.

These are source-occurrence counts, not unique canonical hadith totals, and this bounded review does not establish total AI translation across the whole bank, its linked counterparts, or other language versions. Existing Human labels elsewhere include a prior owner display default and must not be interpreted as verified authorship. Source records and previous display decisions are preserved.

The CSV is reproducible from the checked ledger and canonical records:

```sh
python scripts/export_translation_evidence_report.py --root . --output reports/translation-origin-audit-20261113/decisions.csv
```
