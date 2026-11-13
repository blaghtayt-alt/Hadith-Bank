# Website source review — 13 November 2026

This batch continues the owner's three selected website imports. It preserves
the existing source identities, original HTML/parsed objects, language-specific
wording and source-local references. Registration is distinct from acquisition,
and source attribution/boundary review is distinct from authenticity grading or
independent Pro certification.

## Initial review decisions

| Source | Previously held occurrences reviewed | Register | Still outside the reader |
| --- | ---: | ---: | --- |
| Hadis.islom.uz | 290 | 279 | 11: six unresolved attributions and five source-context entries |
| Hadis.uz Tirmidhi | 37 | 35 | One unresolved saying and one editorial/transmission note |
| Deen Hindi, first held Bukhari cohort | 300 | 300 | Eleven individual language readings stay as complete source context |
| **Total** | **627** | **614** | **13 source occurrences remain outside the reader** |

The first Hindi cohort is a fixed list of 300 source IDs, selected in the saved
inventory order at baseline commit
`1bdc84b9483a068cc56da97046c55ffe756ea478`. It is not a guessed range of consecutive
hadith numbers. Concurrent acquisition after that baseline is preserved.

These counts are source occurrences. Separate reports or bilingual readings
inside one provider occurrence do not become extra fetched entries. The review
does not infer cross-edition canonical numbering from a website's display number.

## Hadis.islom.uz

All 290 held occurrences and their 543 existing main language fields were read:
254 Arabic and 289 Uzbek Cyrillic fields, containing 161,827 Unicode characters.
Detached commentary outside those fields was not separately semantically
reviewed. The selected material comprises 518 fields and 547 exact passages.

The 279 admitted parents include 128 Prophetic reports, 119 Companion reports,
six Successor reports, three mixed-report parents, 22 abbreviated transmissions
and one attributed scholarly saying. Each keeps its actual report type and
speaker qualification. An omitted speaker in an abbreviated transmission is not
filled from another language.

The complete offline export produces **8,614 registered source occurrences and
11 held occurrences from all 8,625 saved entries**. The full source ledgers remain
unchanged. The six unresolved attributions are `book-17:2578`, `book-22:2817`,
`book-22:2829`, `book-22:2866`, `book-22:2876`, and `book-23:4377`. The other five
held entries contain a narrator-age annotation, two pure cross-references, a
chapter heading, and compiler explanation. Their exact reasons remain in the
review coverage ledger.

Boundary examples include the following:

- `book-17:2413` preserves source framing, Arabic dhikr and the publisher's
  Cyrillic transliteration as separate passages, with the transliteration
  identified explicitly.
- `book-23:4394` contains six ordered reading components representing three
  report families: Arabic 1/2/3 followed by Uzbek 1/2/3. The reader shows six
  separate excerpt blocks while preserving one provider occurrence and three
  report families.
- Numeric-only Uzbek fields remain source context even where the same entry's
  Arabic report can be admitted.
- `book-23:4261` has materially different Arabic and Uzbek content. The exact
  readings remain independently qualified; the provider ID does not certify
  translation equivalence.

### Acquisition and count reconciliation

One ordinary public request rechecked the already observed section
`https://hadis.islom.uz/kitob/32/17` on 13 November. It again returned HTTP 500.
The 6,976-byte response was preserved, the attempt count advanced from three to
four, and all earlier failure evidence was retained. No retry allowance was
reset and no alternate access route was used.

All 341 saved page snapshots passed their stored and expanded checksums. An
explicit navigation audit inspected 30,959 nonempty href anchors. Its 673
catalog/section link appearances resolve to 341 distinct URLs, all represented
in the checkpoint. None of those observed navigation URLs was overlooked.
One navigation target is the failed section; the home-page seed brings the
checkpoint to 342 tasks, of which 341 succeeded. This finite saved-page audit
does not establish whole-website completeness. Every one of **9,059
recognized report-container appearances** matches the complete source columns
of **8,625 preserved provider occurrences**. The other **434 appearances** repeat
the same provider identity and exact text under additional section locators;
there are no unaccounted report containers in those saved pages.

The advertised collection totals sum to **9,740**, versus **8,625** preserved
provider occurrences: an unresolved numerical difference of **1,115**.
Number-label gaps are documented as gaps, not as invented missing
narrations or a count of known missing texts. The failed section, source-side
coverage and commentary quotations remain separate open matters.

Evidence:

- `imports/web-uzbek-20261112/islom/reviews/`
- `imports/web-uzbek-20261112/islom/coverage/20261113-failed-section-recheck.json`
- `imports/web-uzbek-20261112/islom/coverage/20261113-catalog-reconciliation.json`
- `imports/web-uzbek-20261112/islom/coverage/20261113-observed-navigation-audit.json.gz`

## Hadis.uz Tirmidhi

The review read all 37 primary fields, 132 attached comment paragraphs, 37
headings and four additional ordered-list blocks. Exact saved HTML and parsed
objects were verified; all 37 canonical baselines were reconstructed before
applying decisions.

The result is 35 additional registrations, including 34 whole primary fields
and one exact excerpt from entry 598. Entry 323 remains an unattributed saying;
entry 564 is source-critical editorial/transmission discussion explicitly
identified as a note. Actual Companion, scholar and historical reports retain
their true attributions. Integral Quran quotations are annotated inside their
coherent reports, without presenting them as independent Prophetic speech.

The complete checkpoint has **607 saved entries: 605 registered, one held and
one excluded as non-narration source context** after applying the decisions.
The observed 670-task queue remains complete. This does not certify that all
content the website might contain has been discovered.

The original 37-record held archive is retained as an immutable review baseline
even after the current derived held archive shrinks. Its stored SHA-256 is
`ca229635bb236d3962204e7ed23f6d08ff6b57b5b379c349d7109db5b5dd27ce`.
Additional quotations found in comments are recorded separately as candidates;
they are not silently merged into a primary narration or counted as new source
downloads.

The four ordered-list blocks in entries 51, 67, 71 and 75 contain 3,309 Unicode
characters. They were preserved in the saved HTML and review ledger but omitted
from the original paragraph-only comment extraction. The review adapter now
verifies their exact HTML locators, stored and expanded snapshot hashes, and
complete text before exposing them as source-context comments. A finite statement
attributed to the Prophet inside entry 75's list is also recorded as an additional
candidate, with its own exact boundaries and no inherited primary reference or
grade. This recovery changes neither primary quotations nor occurrence counts.

Evidence: `imports/web-hadisuz-20261112/reviews/`.

## Deen Hindi: complete first-300 language review

All **1,500 source fields across the fixed 300 occurrences** have now been read
individually. The active ledger selects **1,489 language fields**; eleven retain
complete source context because they contain unresolved attribution or only a
pointer. Every parent has at least one eligible language reading, so the cohort
adds **300 registrations**, not 1,489 source occurrences.

| Language | Complete fields read | Selected readings | Context-only readings |
| --- | ---: | ---: | ---: |
| Arabic | 300 | 297 | 3 |
| English | 300 | 299 | 1 |
| Hindi | 300 | 299 | 1 |
| Urdu | 300 | 297 | 3 |
| Roman Urdu | 300 | 297 | 3 |
| **Total** | **1,500** | **1,489** | **11** |

### Preserved first pass and subsequent language reviews

The first pass read Arabic and English for all 300 selected occurrences, plus
all five language fields for the first ten. That is **630 fields actually read**.
It selected 623 fields: 297 Arabic, 299 English, nine Hindi, nine Urdu and nine
Roman Urdu. Six reviewed fields retain unresolved attribution and one English
field is a translation pointer rather than supplied narration text. The other
870 fields were explicitly unreviewed in this first pass. Three subsequent
independent language passes supplied their own complete reading coverage and
source hashes: 290 Hindi fields (174,118 characters), 290 Urdu fields (160,613
characters), and 290 Roman Urdu fields (192,703 characters). Only those previously
unread fields were replaced in the active ledger. The frozen first-pass bytes,
the first ten decisions in each of those languages, and all record identities
remain unchanged. Each supplement and its validation evidence is retained.

All 600 pinned evidence files for this cohort were verified: 300 saved HTML
snapshots and 300 parsed source objects. Every HTML snapshot reparsed to the
same five-language source object and literal source citation. The complete
1,500-field selected-plus-context partition reconstructs the original wording.
The immutable first-pass decision copy remains available alongside the active
review ledger when later language-field decisions are added.

Different language content is not corrected by copying another field. Entry
1114's Arabic and Urdu describe seated companions, while its English describes
them standing; that source difference is explicit. Entry 486 has usable Urdu
report wording while its English is only a pointer. Eight Hindi source fields
actually use Latin script; their original wording, Hindi language label and
version IDs remain intact, with the observed script and a visible qualification.

Entry 848's Companion and Successor practices remain separate. The Arabic,
English and Urdu decisions keep the criticized claimed Prophetic report together
with its criticism as source context. Hindi and Roman Urdu expose the supplied
third component with explicit source-rejection qualifications before the
quotations. Its criticism is preserved, and the source page's generic Sahih
label is not treated as authentication of that component. Compiler explanations
and transmission comparisons are separated using exact spans; substantive
abbreviated transmissions retain their own qualified attribution.

Acquisition continues independently. At the observed 07:15:57 UTC checkpoint
saved in commit `5fb2171233e514bd9ca5bdd4d5b7cd541cfd0c48`,
11,461 entries were saved, 7,611 were registered by the existing intake, 3,850
were held, and 24,929 inventory entries had not been fetched successfully. The
latter included 1,000 historical errors. Applying this fixed review adds 300
registrations to the applicable acquisition checkpoint; later downloads may
change the overall totals.

Historical verification-page errors are not requeued by this review. The active
Hindi worker remains serialized, bounded and checkpointed, and its existing
HTTP 200 verification-stop guard remains in force.

Evidence: `imports/web-deenhindi-20261112/reviews/`.

## Application and publication behavior

`scripts/web_source_reviews.py` validates source snapshot bindings, baseline
objects, complete field hashes, Unicode offsets, selected-span hashes and
reviewed-language coverage before producing derivatives. Original source objects
are not rewritten. Unknown or unreviewed fields become language-specific source
context and remain outside default narration search. Separate report components
use the reader's existing exact-passage presentation.

The serialized website-import workflow applies newly saved review inputs in a
short **offline export cycle** before another acquisition batch. It validates
the registry, saves the resulting source/material checkpoint and requests the
reader build. After a concurrent main-branch update, changed reviews are
re-exported offline against the combined saved sources before registry
validation and publication. This refresh preserves the original
before-acquisition receipt. The authorized Hindi queue then resumes after that successful
save. An unchanged decision set and unchanged review adapter do not create an
idle repeat loop. Existing source blocks, exhausted failures and owner exclusions
remain enforced.

The final local validation passed 188 software tests, including reader,
importer, source-preservation, evidence-tampering, partial-update rejection and
continuation checks. Separate real-source audits exercised all 290 Islom and all
37 Hadis.uz decisions. The complete Hindi cohort was exported through the actual
importer and validated by the material registry: 300 registered parents, 1,489
selected language readings, exact reconstruction of all 1,500 source fields,
600 original evidence files unchanged, and zero HTTP requests. These are
software/evidence checks, not independent Pro or authenticity
certification. A saved decision commit is distinct from the later successful
material-export and Pages-deployment checkpoints.
