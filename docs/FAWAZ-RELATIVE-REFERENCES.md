# Relative-reference batch proposal

This review batch selects 272 Arabic source occurrences from the 7,514 held
occurrences in its verified 31-edition input export. The existing reviewed-span
importer consumes the saved decisions; the isolated proposal generator is not
a runtime dependency.

## Stored decisions and evidence

The Arabic decisions are recorded in `catalog/fawaz-reviewed-spans.json`.
Their exact source-reference proofs and all original held-ID dispositions are
in `reports/fawaz-relative-reference-review-20261112.jsonl.gz`; every decision
has a one-based JSONL line locator and both compressed and decompressed hashes.
The batch manifest is
`reports/fawaz-import-review/relative-reference-review-20261112.json`.
The exact reviewed source-scope exclusions are retained in
`reports/fawaz-import-review/relative-source-scope-exclusions-20261112.json`.

These are review-batch counts, not final whole-bank publication totals. The
frozen decision proposal contained 763,760 bytes (47,923 bytes as deterministic
gzip); its full audit contains 579,617 compressed bytes / 7,928,484 decompressed
bytes. The review-batch manifest preserves the preparation hashes and parser
versions.

The optional offline audit tool is `scripts/fawaz_relative_references.py`.
For an already validated export, run it with `--root PATH --output PATH` and
`--negative-reviews reports/fawaz-import-review/relative-source-scope-exclusions-20261112.json`.
It only proposes source-bound candidates and records unresolved IDs; it never
changes the importer, source texts or catalog. Regenerated proposals require
source review before becoming active decisions.

## Evidence and review coverage

Every selection requires an explicit relative phrase in its own bounded Arabic
source, the immediately preceding raw source array row in the same supplied
section, a matching final chain label or explicit named report reference, and a
backward dependency ending in a separately established Prophetic report. The
terminal attribution must occur inside that terminal's current bounded Arabic
quotation. No source row, including an empty row, is skipped. Numeric adjacency
alone is never used. Typed decimal IDs remain typed provider IDs.

All 1,162 reference, child/parent chain, terminal-attribution, optional alias and
English corroboration spans were checked against exact original text and raw
edition hashes. All 272 complete English source texts were screened for
independent sayings, pure commentary, and distinct-report contamination. The
source-specific parser was rerun for every supplied language and every
candidate's parent and terminal evidence. It preserved 272 Arabic, 272 English,
266 Urdu and 262 Bengali bounded fields; six Urdu and ten Bengali fields are
source-empty. No new text was supplied to those empty fields. This is not a
semantic-equivalence certification of the translations.

Nasai 2480 and 3945 use the newly bounded Arabic spans [0,304) and [0,392), so
the reviewed decisions cannot restore their removed compiler comparison tails.
Other languages retain their own current source-specific boundaries and notes.
Only Arabic decisions and Arabic relative-reference citations are added.

The only source-local narrator alias used is Ibn Shihab / al-Zuhri, supported by
the same pinned edition's literal compound name. Its exact source span is in
each applicable proof. This is chain-wording evidence, not a global narrator or
hadith identity merge.

## Batch results

| Collection | Selected occurrences |
|---|---:|
| Muslim | 189 |
| Abu Dawud | 46 |
| Tirmidhi | 20 |
| Nasai | 11 |
| Bukhari | 4 |
| Ibn Majah | 2 |
| **Total** | **272** |

Five selections have two reference hops: Abu Dawud4926→4925→4924,
Muslim192→191→190,2438→2437→2436,3577→3576→3575,4943→4942→4941.
The other267 have one hop. The source references retain every edge and the
terminal proof. No antecedent wording, canonical number, grade or identity is
copied into a child.

Representative positive evidence includes Muslim94's explicitly named Kahmas
reference,119's Ibn Ulayyah reference,133/188's source-supported Ibn Shihab /
al-Zuhri chain,192's named Jarir reference through191,213's Arabic chain plus
its own English content-reference evidence, and Tirmidhi52's al-Ala chain.

## Exclusions retained

The initial282 candidates were reduced by nine source-scope exclusions and one
dependent child. These records stay in the original-source view:

- Abu Dawud4407: Nafi discussing the prior hadith with Umar ibn Abd al-Aziz;
  the additional text is the latter's inference.
- Abu Dawud4517: an abbreviation followed by Hasan's independent legal opinion.
- Tirmidhi1873,2978,3026: the Arabic source starts an abbreviation then a
  separate report, while English supplies the second report. These need
  language-specific scope decisions, not whole-field promotion.
- Muslim905: source transmission followed by compiler debate;906 is withheld
  because its dependency passes through905.
- Muslim2605: source transmission followed by a narrator's attribution doubt.
- Muslim5986: source transmission followed by a place-name explanation.
- Muslim7273: source transmission followed by a narrator's father's instruction.

All six preexisting negative-reference review records were retained and
hash-checked. Five belong to the current held set; the remaining review concerns
an occurrence already outside that held set and is not used by this proposal.
Tirmidhi111 remains unresolved because the cited110 is not independently
established as a Prophetic report. Tirmidhi49 was not added because its target48
was still held in the frozen audit input, despite a separate newer direct-source
review now being available. The conservative parser also leaves the inspected
Abu Dawud5/37 and Muslim98/242 cases for a later supported grammar expansion.

## Validation and integration limits

Sixteen focused prototype regressions passed, covering source-order evidence,
no numeric/identity merge, explicit relative wording, named-chain requirements,
section/book boundaries, duplicates/order errors, empty/intervening source
records, negative reviews, source-bound English corroboration, multi-hop
dependency roots, exact offsets and source-local aliases.

The publication validator should independently verify the linked proof file,
each referenced raw source/span, the dependency edges and terminal evidence,
and the added Arabic citation/abbreviation qualification. The source validator and reader separately enforce those checks and display the
abbreviated-reading qualification. Source attribution
review does not establish authenticity, independent Pro QC or rights clearance.
