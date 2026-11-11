# Chinese Sunan Abi Dawud: Arabic and English source parallels

This bundle adds source counterparts to the 2,828 occurrences in the supplied
Chinese Word edition, **艾布·达吾德圣训集（部分译本）**, translated by Musa Yu
Chongren. The original Chinese text, source-local numbers, stable IDs and source
Word file remain unchanged.

The reviewed correspondence covers **2,827 source occurrences**. Chinese local
number **2440** remains unresolved: the likely parallel differs in both the
narrator and the wording. Its candidate number is audit evidence, not a public
assignment. Exact language coverage and the selected English editions are
recorded in [coverage.json](coverage.json).

## Reading the linked languages

- **Arabic source entry** contains the exact upstream Arabic entry, including
  its chain and any compiler discussion. The Chinese occurrence can be one
  report or an excerpt within that entry. The complete entry is not labelled as
  one uninterrupted prophetic quotation.
- **English text** is copied unchanged from the authorized HadeethEnc English
  export, only after the particular Chinese occurrence has been checked against
  that English report. Its own source URL, publisher ID, Arabic revision and
  English export version are retained. An English excerpt is labelled as such.
- **Read English at source** is a direct link to the corresponding Sunnah.com
  source page. It supplies no offline English text and is not counted as English
  text availability. No complete third-party English collection is republished.

Each language has its own reference. HadeethEnc publisher bibliography references
are preserved separately from a reviewed Arabic-source cross-reference. Where
HadeethEnc names Abu Dawud but gives no hadith number, the displayed number is
explicitly described as the reviewed cross-reference, not a publisher-supplied
number. A parallel from another collection keeps that collection's reference.

The English at standard source **2319** describes another narration. The Arabic
match is retained, but that English source is not assigned. The two reports
associated with **907** and **907b** retain distinct source pages and texts; the
working source URL for 907b is its Sunnah.com URN.

Use the reader's Arabic and English controls to open the counterparts.
**Alignment notes** preserves known differences, source defects and excerpt
boundaries. Review was performed by an automated assistant, with the actual
reviewer recorded per occurrence. This is a narration correspondence, not an
independent scholarly authentication, full chain certification or certification
of every translated word.

## Original books and source downloads

The reader's **Browse available materials → Download books and source
materials** section, and each applicable **Source & translation details** panel,
link directly to preserved GitHub originals. The file's actual format is shown:
PDF, Word DOCX or Word DOC. The
[original Chinese DOC](../../../../../materials/zh-abu-dawud-yu-2002-doc/艾布达吾德圣训_Sunan_Abi_Dawud.doc)
is available without opening the structured record files.

## Reproducibility and evidence

- [provenance.json](provenance.json) records the publication scope, source
  revisions, original hashes, source conditions and known limitations.
- `raw/ara-abudawud.json.gz` preserves the exact Arabic dataset downloaded at
  the recorded Git revision. The printed Arabic edition is not identified by
  that provider and remains unknown.
- `raw/supplements/` preserves the two individually consulted Arabic passages.
  The initial 907 capture is retained, and an explicit character boundary
  excludes the page's grade/reference/share footer from the displayed Arabic.
- `reviews/` contains the exact individual review sidecars, including the six
  agreeing second reviews and the unresolved occurrence. Research-English
  hashes remain as evidence; the research-English corpus itself is not included.
- `entries.jsonl.gz` and `mappings.jsonl.gz` are deterministic compiled assets.
  The parent registry verifies the assets by SHA-256. Source or target drift and
  ambiguous assignments fail closed rather than creating an inferred link.
- `english-display-decisions.jsonl.gz` records the accepted English versions and
  which one is selected for each source occurrence. Distinct source occurrences
  remain distinct even when they quote the same source entry.

Rebuild this bundle from its retained local review inputs:

```console
python scripts/build_chinese_abu_dawud_counterparts.py --root .
```

The normal bank refresh consumes this registry and rebuilds the reader, Arabic
and English search, and source citations. No network request or model matching
is performed while resolving these published links.
