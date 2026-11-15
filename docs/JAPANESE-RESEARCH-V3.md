# Japanese reports, dhikr and prayers — research-v3 integration

The owner explicitly requested HTML integration on 12 November 2026. The bank uses a separately derived, **owner-authorized pending-review** subset of the exact research-v3 package. This is a visibility decision; original research/source holds and the requirement for a new separate independent Pro final evaluation remain.

## Reader sources and counts

| Japanese source | Whole source records | Mixed-parent excerpts | Reader source occurrences |
| --- | ---: | ---: | ---: |
| ムスリムの砦 — Hisn al-Muslim | 245 | 16 | **261** |
| イスラームのメッセージ | 303 | 3 | **306** |
| イスラームの基本知識 | 591 | 59 | **650** |
| 大塚マスジド 金曜日礼拝ホトバ 要約 — 2023年9月1日 | 8 | 1 | **9** |
| **Total** | **1,147** | **79** | **1,226** |

These counts use **original source occurrence IDs**, consistently with the existing bank. They are not a count of unique canonical hadith texts or chains. The 122 exact Prophetic components inside 79 mixed parents remain separate component annotations, with their original IDs, boundaries and scoped references. They do not create 122 additional source-occurrence cards. The 45 related external witness links are not extra extracted records. Different source occurrences and editions are not deduplicated.

The [task-start snapshot](../imports/japanese-research-v3-20261112/before-counts.json) contained 37,201 bank occurrences, including 2,237 Japanese occurrences. Before this Japanese integration, a separate concurrent import added 6,994 occurrences. The verified integration parent at `abc92527fbb85c657d7229bb8ccd46466516dd59` therefore contains **44,195** bank occurrences and **2,237** Japanese occurrences. This import adds **1,226**, and the fully compared generated reader/search catalog contains **45,421** overall and **3,463** Japanese occurrences across **199** registered datasets. The [count-change ledger](../imports/japanese-research-v3-20261112/count-change.json) separates the concurrent additions from this import and records exact catalog/search/reader hashes. Future unrelated imports may increase live totals; consult the generated [material catalog](../catalog/materials.json) and [site build report](../reports/site-build.json) for the current snapshot.

## Sources and provenance

The four original PDFs are stored with their material registrations, unchanged:

- [Hisn PDF](../materials/ja-hisn-2007-research-v3/source.pdf) · [manifest](../materials/ja-hisn-2007-research-v3/manifest.json)
- [Message PDF](../materials/ja-islam-message-research-v3/source.pdf) · [manifest](../materials/ja-islam-message-research-v3/manifest.json)
- [Basic Knowledge PDF](../materials/ja-tokyo-basic-2012-research-v3/source.pdf) · [manifest](../materials/ja-tokyo-basic-2012-research-v3/manifest.json)
- [Otsuka PDF](../materials/ja-otsuka-20230901-research-v3/source.pdf) · [manifest](../materials/ja-otsuka-20230901-research-v3/manifest.json)

The [Japanese bibliography](../imports/japanese-research-v3-20261112/Japanese_bibliography.json) retains exact edition evidence and null reasons. Hisn credits サイード佐藤 and ファーティマ佐藤. Named translators for the other three exact PDFs remain unestablished; authors and issuing institutions do not substitute for translators. The bank's current new-book Human display policy remains distinct from named-translator evidence.

Japanese reading text comes from exact preserved source fields or selected code-point spans. The [whole-record selection ledger](../imports/japanese-research-v3-20261112/selection/whole_record_display_selections.json) uses 705 existing Japanese text fields and 442 existing raw Japanese/kana fields. It binds 27 preassembled Japanese fields to their exact field hash instead of inventing contiguous raw offsets.

The [mixed-parent selection ledger](../imports/japanese-research-v3-20261112/selection/mixed_parent_display_selections.json) retains all 122 child IDs. Display joins between separate spans are explicitly presentation separators. Hisn074 and162 select the Japanese report within the approved component and leave broken raw Arabic outside the Japanese reading. Hisn099 and translator-note051 use only their approved practice/greeting spans; their parent Quran text is not substituted.

Source summaries and biographical narratives receive a reported-meaning qualification. Kana-only renditions are identified as kana rather than Japanese meaning translations. Formula wording with separately unverified contextual use retains that distinction. These qualifications do not exclude prayers, dhikr or reports merely because they are devotional or describe actions.

## Classification and separate storage

All 1,889 original source records are preserved: the 1,687-record corrected-v2 baseline and 202 additions already present in research-v3. The [current publication ledger](../imports/japanese-research-v3-20261112/publication-decisions.json) enumerates every original ID and keeps historical flags separate from the later visibility decision.

The other 663 original source occurrences are outside the registered Hadith reader subset:

- **186 non-hadith records** in [the non-hadith folder](../non-hadith/japanese-research-v3-20261112/).
- **429 Quran/context records**, including the unchanged original 414 Quran entries, in [source context](../imports/japanese-research-v3-20261112/source-context/quran/).
- **21 unresolved-origin records** in [unclassified storage](../unclassified/japanese-research-v3-20261112/unresolved/).
- **27 mixed parents without approved component selections** remain hidden. All 106 complete mixed parents, including the 79 with separately selected Prophetic excerpts, are preserved [outside the reader](../unclassified/japanese-research-v3-20261112/mixed-parents/).

The complete mixed parent is never treated as a wholly Prophetic quotation. Quran quoted inside an otherwise coherent Prophetic recitation/practice report remains identified in the research metadata and is not counted as an extra hadith.

## Research references and language panels

Every reading retains its Japanese PDF/page and source-record locator. Printed source citations and researched external witnesses remain separate. Witness collection numbers, editions, scope, variant relationships and source-attributed assessments do not create an exclusive canonical identity for the Japanese wording.

Candidate Arabic and English are preserved in the research evidence. The explicit material counterpart hold prevents their automatic or reviewed promotion to accepted language counterparts. This import does not generate a new translation or fill missing language panels with guessed text.

The canonical records include a Japanese `language_versions` entry with its own source, references and comments, plus the existing compatibility fields. They use the multilingual-panel framework merged in [PR #6](https://github.com/blaghtayt-alt/Hadith-Bank/pull/6). The shared build generates the reader and search; the importer supplies canonical sources and never manually edits generated HTML.

## Exact archive preservation and reproduction

The original ZIP is **89,158,437 bytes**, SHA-256:

```text
331d2973511301c6cd50d3e2a8612e135defda529e855b8b03894490005c01fa
```

All bytes are stored in [16 ordered binary parts](../imports/japanese-research-v3-20261112/preserved-delivery/archive-parts.json). This includes the complete 160 MB master JSON, all 23 CSV exports, research evidence, original inputs, historical coverage and correction/exception logs. Concatenation reproduces the exact original ZIP; it is not a re-created source package.

Restore it locally with:

```bash
python scripts/import_japanese_research_v3.py --root . --restore-only
```

Reproduce the current selected reader files and partitions from the verified archive and hash-bound selection ledgers with:

```bash
python scripts/import_japanese_research_v3.py --root .
python scripts/refresh_bank.py --root . --site-output _site
```

The importer also preserves selected original JSON files as deterministic gzip files. Their expanded bytes/hashes and stored bytes/hashes are listed in [the integration audit](../imports/japanese-research-v3-20261112/integration-audit.json). The complete archive remains authoritative for original serialization and the full evidence set.

## Verification scope

Recovery verified the ZIP size/hash, all 1,478 ZIP members' CRCs and all 1,476 non-self-referential output-manifest file hashes. Reader validation binds every selected field/span to preserved source bytes, checks occurrence IDs and excluded partitions, and retains the four original PDF hashes.

The complete software suite passed **497 tests**, including **15 Japanese source-preservation and routing checks**. All **1,226** new generated reader/search records, all **663** excluded IDs, all four PDF downloads and the **6,994** concurrent source IDs passed the bounded end-to-end comparison. The public workflow must complete the full registered-bank build and portable validation before deployment; see the generated site-build report and workflow run for that separate gate. Detailed prepublication receipts are retained in [validation](../imports/japanese-research-v3-20261112/validation/).

No whole-book OCR, fresh 686-page audit or independent final Pro evaluation was performed for this integration. Historical research-v2/v3 coverage and all unresolved source, Arabic, semantic, bibliography and reference qualifications remain preserved. Software tests and website publication do not certify narrational authenticity or exact translation fidelity.

The earlier [blocked-transfer request](../imports/japanese-research-v3-20261112/package-request.json) remains unchanged as history. This documented import and its current publication ledger supersede that earlier transfer status, without rewriting its source-review history.
