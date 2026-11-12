# Hadis.uz Tirmidhi intake

The owner supplied `https://hadis.uz/hadiths/1` on 12 November 2026. This is a separate source from `hadis.islom.uz`. The first catalogue page identifies **Сунани Термизий** and links to public detail pages and its next catalogue page.

## Bounded batches

```sh
python scripts/import_hadisuz.py --root . --max-pages 60 --max-seconds 600 --delay 1.25
python scripts/import_hadisuz.py --root . --export-only
```

The request budget includes robots and collection information pages when not already saved. The importer follows observed `rel=next` links for the supplied collection and observed `/hadith/<id>` detail links. It does not generate number ranges, request private APIs, follow authentication/backend/profile routes, or infer a corpus from placeholder sidebar collections. The site's observed sitemap is incomplete relative to the current catalogue and is not used as the queue's limit.

Exact response bytes are stored as content-addressed gzip snapshots with their source URL, retrieval time, HTTP status, expanded SHA-256 and stored SHA-256. Parsed detail objects are retained separately. Completed tasks and their records survive a later interruption; exports happen once at the end of a batch. Source files, canonical records and checkpoints are saved together by the repository workflow.

Progress and recovery state live at:

- `imports/web-hadisuz-20261112/checkpoint.json`
- `imports/web-hadisuz-20261112/progress.json`
- `imports/web-hadisuz-20261112/snapshots/`
- `imports/web-hadisuz-20261112/parsed/`
- `imports/web-hadisuz-20261112/held-records.jsonl.gz`

Transient request failures have at most three attempts across batches. Empty or unfamiliar detail layouts require parser review. HTTP 401/403/429 and robots denials remain explicit access blocks and are not automatically retried. Offline export remains available for previously saved valid evidence. Exhausted robots retrieval failures set `startup_stopped`; a scheduler must not repeatedly launch that stopped source.

## Narration and commentary boundaries

Catalogue cards are previews, not registered occurrences. The inspected detail pages place the primary narration in the first content-column paragraph, with italic/emphasis attribution and bold/strong matn. Subsequent paragraphs contain source assessments, references to other collections, lexical explanations, Quran quotations and scholarly discussions. Some scholarly paragraphs also use bold type, so selecting all bold text would be incorrect.

The importer registers only the first source narration paragraph when its boundary, expected language and Prophetic attribution are supported. A paragraph ending in a colon before missing continuation, a changed body layout, independent saying, or unestablished attribution remains outside the Hadith reader. The complete page and all parsed paragraphs remain preserved. Additional narrations mentioned in commentary are not silently promoted into new occurrences.

Every accepted occurrence contains its own Uzbek Cyrillic language version, source URL, exact quoted text, references and separate comments. Source grading paragraphs are retained with an unknown individual assessor where that person is not stated. Collection attribution pages are retained separately; they are not a substitute for exact per-entry identity evidence. Current new-book translation-origin policy applies independently of the historical provenance fields.

### Visible publisher collection credits

The saved `about-project` page explicitly credits the Tirmidhi translation to Мирзо Кенжабек, names «Адолат» (1999), and says the electronic books came from `www.ziyouz.com`. The saved `sunani-termiziy` introduction separately describes the translator, source edition, translation resources, and commentary sources. The importer preserves the exact Uzbek paragraphs, including source spelling and punctuation, in this language version's references and publisher-credit panel. Each paragraph has its own information-page URL, paragraph number, immutable snapshot path and SHA-256; observed external credit links are retained as links without automatically acquiring another source.

These statements use `publisher_collection_credit_not_per_entry_identity` scope. They describe the collection and the publisher's use of resources; they do not assign an independently verified translator, canonical number, or upstream edition match to each entry. Entry-level translator fields remain null. Introductory quotations and unrelated project acknowledgements stay in the complete saved information pages rather than becoming narration text or entry commentary. Offline reexport derives visible credits from the checksum-verified original HTML, including for older checkpoints that only stored URL/hash pointers in records; it never relies on a cached plain-text credit field. Reexport changes the credit metadata, while narration text, separate entry comments and original response bytes remain unchanged.

The audited pages contain Uzbek Cyrillic text. Arabic and English are not manufactured. Numeric detail URL IDs such as `615` are publisher database IDs; printed and canonical collection numbers remain null. A separately verified counterpart decision would be required to link another edition's Arabic or English.

## Registration and limits

Accepted records are registered under `materials/hadisuz-tirmidhi-uz-web/`. Stable occurrence and language-version IDs are retained when later batches append records. Canonical JSONL files use persistent 40 MiB publication shards when needed. Every supporting original and parsed record is hash-checked by the material registry.

This is an owner-authorized digital-source import. It adds no OCR-QC badge and asserts neither independent certification nor new reuse rights. Exhausting the observed fetch queue does not establish that the site's whole historical collection or every embedded commentary quotation has been imported.
