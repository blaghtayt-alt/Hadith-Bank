# Persian source extraction evidence

`extracted/` contains the final source-aware record snapshots consumed by
`scripts/import_persian_docx.py`. JSONL snapshots use gzip with a fixed timestamp.
`audit/` preserves source paragraphs, commentary-removal decisions, symbol
evidence, numbering exceptions and targeted doctrinal-screening findings.
Neither directory is embedded as commentary in the reader.

The authoritative original DOCX bytes are `materials/fa-*/source.docx`, with
the original upload filename recorded in each source metadata file. See
`docs/PERSIAN-DOCX-IMPORT.md` and `reports/persian-docx-integration.json` for scope,
counts and the owner's hadith-only/no-QC display instructions.

`SHA256SUMS.json` records stored and uncompressed checksums. The original font
binaries are not redistributed; their URLs/hashes and observed glyph evidence
are retained. The publisher's single matching Muslim 285 paragraph is retained
with its complete-page hash and explicit recovery scope.

The upstream extractors expect a scratch layout with `upload/` original files
and `work/{bukhari,muslim,riyadh,font-evidence}/` sibling directories. Their
scripts and required evidence are preserved in the audit. Rebuilding the bank
from the final snapshots requires only Python's standard library and the two
commands documented in the import guide; re-extraction additionally uses lxml.
