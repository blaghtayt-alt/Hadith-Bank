# PDF and XLSX attachment intake

## Registered scope

This intake contains **32,300 source narration occurrences from 12 supplied files**:
eight HadeethEnc XLSX exports and four Chinese PDFs. The structured texts and
original evidence are in a private, self-contained bank candidate. The public
repository contains its importer, schemas, offline search, validation, and
non-text registration audit. Registration does not grant publication approval.

| Bank language | Source code | Narration occurrences |
| --- | --- | ---: |
| Japanese (`ja`) | `ja` | 281 |
| Vietnamese (`vi`) | `vi` | 1,208 |
| Chinese (`zh-CN`) | `zh` | 22,443 |
| Uzbek (`uz`) | `uz` | 421 |
| Hindi (`hi`) | `hi` | 2,346 |
| Urdu (`ur`) | `ur` | 2,257 |
| Bengali (`bn`) | `bn` | 1,953 |
| Portuguese (`pt`) | `pt` | 1,391 |
| **Total** | | **32,300** |

The owner's request to add all supplied records covers these eight intake
languages. This batch contains no Filipino records. Existing public Filipino
material remains part of the bank. The public corpus's six-language scope is
unchanged while the new text intake awaits publication approval.

## Organization and identity

Primary records are UTF-8 JSON arrays at:

`languages/<bank-code>/books/<book>/editions/<source-snapshot>/records.json`

Book slugs are `hadeethenc`, `bukhari`, `muslim`, `riyadh-al-salihin`, and
`shengxunjing`. Snapshot directories use `xlsx-<literal-export-version>-<sha256-prefix>`
or `pdf-<sha256-prefix>`. They identify the actual supplied asset, without asserting
an otherwise unknown bibliographic edition.

Each object retains separate `text`, `book`, `number`, `narrator`, `source`,
`translator`, and `page` fields, together with Arabic/translation distinctions,
isnad evidence, citations, commentary, benefits, footnotes, grades, variants,
correction history and review issues wherever supplied. Original occurrence IDs
remain unchanged; `record_id` and `occurrence_id` mirror them. Printed collection
numbers, source entry IDs, source order and canonical numbers remain distinct.

`zh-CN` is the bank's directory alias for source code `zh`; no Chinese locale,
script conversion or source text change is inferred. Source code `pt` remains
Portuguese without guessing a Brazilian locale. A spreadsheet row remains a
sheet/row locator; it is not a printed book page.

## Tagging standard

Three separate fields make each tag's origin explicit:

- **`topic_tags`** preserves publisher taxonomy when supported. It is empty in
  this intake because the supplied files contain no publisher category tables.
  HadeethEnc category IDs are not invented or borrowed from a different snapshot.
- **`source_structure_tags`** retains literal division, part, volume, chapter,
  section and subsection headings. Each tag records `origin: source_book_structure`,
  the source ID, hierarchy, original field, and narration locator. That locator
  identifies a narration under the heading, not a certified heading-page number.
- **`editorial_tags`** uses the existing `import_pipeline_not_publisher` origin
  and prefixes `source:`, `language:`, `method:`, `review:`, and `ai_translation:`.
  It also records `book:`, `edition:`, `format:`, `kind:`, `rights:`,
  `canonical_mapping:`, and text-availability tags. These labels organize the
  import and do not authenticate a narration or amend the source wording.

For example, `review:pending_independent_pro`, `rights:pending`,
`canonical_mapping:unverified`, and `arabic:not_supplied` are explicit searchable
states. The operational record type is a source narration occurrence; prophetic,
Companion, Successor and historical-report classification is not silently inferred.

## Source preservation and relationships

The complete previous extraction package is retained byte-for-byte under
`evidence/extraction-package/`, with its original 12 attachments, raw source rows,
PDF page text, source-entry records, ancillary material, coverage, exceptions,
extraction scripts, review logs and checksum manifest. The adapter changes only
the bank schema identifier, directory-language alias and local source locator;
it adds bank metadata to provenance and review. All other original fields are
compared exactly by the new validator.

Only the 12 main `records.json` arrays count as primary records. Source rows,
unsplit entries and raw-page evidence must not be counted again. Repeated printed
numbers and separately reported variants remain separate records. Source-group
and HadeethEnc entry indexes link related evidence without deduplication or
claiming canonical narration identity.

The earlier **8,423-entry SQLite candidate is a separate intake**. Its counts
overlap five languages in this XLSX batch, but the exact private SQLite bytes
were unavailable for a full cross-intake comparison here. Do not add the totals
and call the result unique Hadith. Preserve source versions and compare exact
records before any future merge or equivalence decision.

## Review, AI provenance and release status

`ai_translation` remains `unknown` for 25,124 records and `false` for 7,176
records whose extraction includes explicit historical human-translator evidence
in the Riyadh and Shengxunjing PDFs. No new translation was generated. Missing
Arabic in 20,153 PDF occurrences and the one absent Portuguese split translation
remain null. Source wording, numbering defects and truncations are not repaired
by guesswork.

Mechanical preservation and metadata checks are separate from source-fidelity
review, translation accuracy, narrational authenticity and publication rights.
Original targeted reviews and their limited coverage are retained, without
turning them into full-corpus approval.

Every record remains `release_status: private_candidate`,
`independent_pro_qc: pending`, and `release_eligible: false`.
`PUBLICATION-GATE.json` remains closed. The requirements in `AGENTS.md` and
`docs/REVIEW-AND-RIGHTS.md` apply to exact final bytes: independent Pro publication
QC and an appropriate reuse basis must be recorded before public release.
A public branch or pull request containing candidate text would also be publication.

## Reproduce and use offline

Keep the private output directory outside this public Git checkout. Input is the
expanded `hadith-bank-structured-json.zip` extraction package with its existing
`catalog.json` and `checksums.sha256`.

```bash
python scripts/import_attachments.py --input PRIVATE_EXTRACTION --output PRIVATE_INTAKE
python scripts/validate_attachments.py --root PRIVATE_INTAKE --report PRIVATE_INTAKE/reports/validation.json
python scripts/search_attachments.py --root PRIVATE_INTAKE --language ja --limit 3
python scripts/search_attachments.py --root PRIVATE_INTAKE --language zh-CN --book bukhari --limit 3
python scripts/search_attachments.py --root PRIVATE_INTAKE --tag review:pending_independent_pro --limit 3
```

Conversion, validation and search use Python's standard library and require no
network access. JSON Schemas are included for additional schema-aware consumers.
Hash verification and path-boundary checks protect local resolution. Search does
not omit records merely because Arabic, translation or metadata is absent.
