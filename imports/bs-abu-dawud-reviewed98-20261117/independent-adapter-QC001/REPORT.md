# BS-ABUDAWUD-ACCEPTED98-ACTUAL-ADAPTER-INDEPENDENT-QC-001

**Verdict: PASS — bounded, PRIVATE, pinned PR28 98-record actual Bank adapter. Not release approval.**

## Inputs and exact code

- Outer: 74,210,243 bytes, SHA-256 `85451f5d58395c48dc38b5b9ed8cf17594679f16d77ce4b29ff9227981922300`; CRC and all **13** manifest payload hashes PASS.
- Original103 ZIP: 7,686,130 bytes, SHA-256 `1a805f39c90422b0cf6dbf69085c7620165f64b45c8a82c69d08c58b9d9cba9d`; CRC and all **69** payload hashes PASS.
- Producer98 ZIP: 681,803 bytes, SHA-256 `b93326bff8ad7308b5f8f4ebcc46db908e6136b556bb6200d64aa25af33a05aa`; CRC and all **146** payload hashes PASS.
- Pinned exact stock code PR28 `2df9d4a3`, ZIP SHA-256 `24879f8440359ab9811102874c61306b174939f64dd47e3beb98d51dbb19225b`, **125** unchanged files (see `CODE_SHA256.json`).
- Original physical PDF, 474 pages, 71,722,974 bytes, SHA-256 `8eefb724e62a53f2197b09a3aca5185ffe8c219cb5ce615063920798a00b700a`; checked by bytes, checksum and page count. Original words, crops and old 110-case source QC were not re-reviewed.

## Independent actual-code routes

The exact pinned PR28 production scripts, **without software modifications**, ran inside a copied private test fixture. All three CLI processes exited **0** with empty stderr. Direct stock `load_public_materials` and `load_records` also passed.

| Actual route | Bounded result |
|---|---:|
| `build_bank_views.py` | 98 JSONL records, SHA-256 `4eee77e125dc7d68f4448207a97abf4241db6ce7b08992d8dedea81cd4cfeabe` |
| `build_reader.py` | 98 embedded gzip reader records, HTML 722,212 bytes, SHA-256 `c4230502feac515a6da82058ea8332238e2abfe91e87ffcaa3e893b2f3778a2a` |
| Markdown | 4 data pages / 9 Markdown files / 378,646 bytes |
| `build_discovery.py` | 98 distinct static record HTML pages, 109 generated files / 675,830 bytes |
| Original PDFs copied into generated static site | **0** |
| Root receipt parity | Candidate, projected search and reader HTML hashes all independently match the supplied Root receipt |

The actual projected search, embedded reader, 98 static HTML pages, and Markdown have been checked against all **98 exact accepted Bosnian bodies/IDs**. Each record has its original candidate ID, selected source version, printed-source-only number, original PDF SHA, physical page list, source regions, actual reader line locator, original translator and current display provenance. See `RECORD_BY_RECORD.json` for 98 per-case SHA bindings and generated static-page paths.

## Scope accounting and classifications

- Source universe: 110 first printed source occurrences; **103** previously source-fidelity PASS (not newly source-reviewed).
- Seven genuine source holds remain **3, 16, 52, 62, 84, 106, 108**.
- Five additional source-role exclusions remain **37, 72, 86, 87, 102**.
- Registered private subset: **98 distinct** source-scoped occurrences; kind labels **73 source reports/sayings, 14 expressly labeled Hadith, 9 source fragments and 2 Companion reports**. This is *not* a claim of 98 complete independently validated Prophetic hadiths.
- All 17 confirmed text successors are retained as previous QC evidence; **16** occur in the 98-row subset. No. 102 is source-role excluded. No. 107's geometry-only successor is included with unchanged body; held No. 108 remains excluded.
- The older canonical assertions for original 1–5 are retained as **historical evidence only**. In all 98 active records: `number.canonical=null`, `number.in_book=null`, explicit source-local numbering, `references.canonical=null`, `related_versions=[]`, counterpart mode `disabled` and `text.arabic=null`. No Arabic/English/commentary readings added.
- `Mahmut Karalić` remains the credited human translator. The current **Human** owner display-policy classification is distinct from historical per-source process flags. All source-record rights/release gates remain unassessed/false.

## Negative tests

**3,508 independent assertions passed** with zero failures. Six deliberate changes to QA fixture files were rejected by the stock registry: bad record checksum, bad original PDF checksum, explicit withheld record, duplicate ID, counterpart opt-out bypass, and unauthorized manifest. All mutated fixture files were restored byte-for-byte. Ten additional deliberate in-memory changes were rejected by a separate source-approval QC gate: body, page, canonical reference, counterpart addition, Arabic insertion, role promotion, translator change, rights promotion, excluded case 52 and fabricated occurrence ID. Native format validation is **not** claimed to enforce all of the independent source-approval policy gates.

## Corrected capacity point; genuine remaining gates

The earlier 71.7 MB PDF versus 19.7 MB site-headroom HOLD is **withdrawn**: the actual `source_download_url` constructs a repository `/raw/<ref>/materials/...pdf` link and the generated static QA directory contains **no copy** of the original PDF. The original must remain available at the exact repository material path when release is separately authorized; live URL response was not checked.

**PENDING:** actual added HTML/data bytes in a *full Bank build* and the full-site 950 MB gate; full-corpus CI and cross-code integration; current live/hosted pages and PDFs; publication, right-to-reuse, per-narration authenticity/canonical counterpart approval. The isolated test used empty other-collection fixtures and a synthetic `authorized=true` test Manifest **solely to run unmodified registry code**. Neither this manifest nor any generated QA output may be deployed. The actual proposed `manifest.private-draft.json` remains `publication.authorized=false` and is not a valid publication request.

**No shared or public writes, code/source changes, source 111+ extraction, network requests, additional workers, or publication.**
