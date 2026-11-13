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

### Confirmed material export

Review/code commit `4b0a367f023231ffe151f02d241c2527a08d4eb6` was applied by the
serialized source workflow. Commit
`7319a8788b64f48fc89cdb93119e3b6dcbf72a47` records all **614 additional
registrations** against the then-current acquisition checkpoints. The saved
progress files for all three sources bind the same review engine SHA-256,
`507632a7bdea8f0cbdbfb25f8950d4fe23eace25af37e621edd07dd9c221cc78`.

| Source at that export | Saved | Registered | Held | Excluded source context |
| --- | ---: | ---: | ---: | ---: |
| Deen Hindi | 11,919 | 8,231 | 3,688 | 0 |
| Hadis.islom.uz | 8,625 | 8,614 | 11 | 0 |
| Hadis.uz Tirmidhi | 607 | 605 | 1 | 1 |

These are confirmed repository/material counts. They do not by themselves
establish a completed Pages deployment. Later acquisition batches can change
the totals without changing this fixed review cohort.

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

The exported checkpoint has **607 saved entries: 605 registered, one held and
one excluded as non-narration source context** after applying the decisions.
The original 670-task queue was complete. The subsequent navigation audit found
additional explicitly linked chapter/topic catalogues outside the old route
allowlist, so that original queue is not a complete coverage boundary.

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

### Recovery of omitted chapter and topic routes

The finite audit verified all 61 saved pages of the original main catalogue,
plus the two saved information pages. The first 60 catalogue pages each expose
ten distinct detail links and the last exposes seven: all 607 link targets
are represented in the saved source cohort. There is no explicit numerical
grand total on those pages. Eight unused numeric URL labels therefore remain
URL-label gaps, not proof of eight missing narrations.

The saved main page also explicitly links seven chapter catalogues which the
old route allowlist omitted:

| Observed route | Exact parent-link label |
| --- | --- |
| `/hadiths/3` | Таҳорат боблари |
| `/hadiths/15` | Намоз боблари |
| `/hadiths/17` | Витр боблари |
| `/hadiths/18` | Жумъа боблари |
| `/hadiths/19` | Ҳайит боблари |
| `/hadiths/20` | Сафар боблари |
| `/hadiths/430` | Закот китоби |

The first ordinary chapter request returned HTTP 200 and the exact expected
heading, `Таҳорат боблари`. Its sidebar supplied 111 further topic links. The
previous title check expected the book title on every catalogue, so it rejected
this valid chapter response. The response bytes and parser-failure history were
retained, and that saved response was subsequently processed offline after the
scoped parser correction. No additional request was needed for that correction.

The revised importer admits a descendant catalogue only through its actual link
in the sources panel of an already validated parent. A checkpoint binding keeps
the exact href, link text, parent URL and parent snapshot hashes. Each target
heading must match its own parent-link label; the book root still identifies
Tirmidhi. Resume and fetch operations revalidate that ancestry against the saved
HTML. Pagination uses actual observed links. Unknown routes, changed headings,
invented links and conflicting bindings stop processing; numeric ranges are not
used to discover pages.

The bounded recovery follows only catalogue pages. Its page counts measure
navigation coverage, not newly downloaded hadith entries. Newly observed detail
URLs, if any, stay as pending tasks for the ordinary importer. The merged
production checkpoint retains the latest 605 material-part assignments and
original source entries. The batch controller reads pending work from that
durable checkpoint, so an older exported `done` flag cannot hide the new queue.

The run stopped at its bounded time budget after **96 ordinary catalogue
requests in total**, including the first chapter probe: seven chapter roots,
65 pagination pages/aliases and 24 topic roots. All returned HTTP 200. The
post-correction run issued 95 requests and took 602.963 seconds including its
final in-flight response. It made no detail-page requests and no material exports.
The original parser-failure event remains recorded; there are no active failed
tasks or source access stops in this recovered Hadis.uz queue.

The final saved-page audit covers **157 catalogue pages**: 61 original and 96
new. Their 1,323 detail-link appearances resolve to the same **607 unique saved
detail URLs**, with no newly discovered detail URLs. It adds 523 observed
catalogue tasks and proves ancestry for 459 catalogue routes. The merged
checkpoint contains **1,193 tasks: 766 done and 427 catalogue tasks pending**.
Every observed in-scope catalogue URL is queued, and every queued catalogue
has saved-link evidence. Pending pages may expose further links, so the full
observed catalogue queue and whole-book coverage remain incomplete.

The exact acquisition checkpoint is frozen separately. The production merge
starts from commit `7319a8788b64f48fc89cdb93119e3b6dcbf72a47` and retains all
605 current part assignments, 607 source entries, 670 existing tasks and 671
existing snapshot descriptors. It adds only the new bindings, 523 tasks,
96 snapshot descriptors and the preserved historical parser event. Its SHA-256
is `06843aa904281b9c9c65f132e521949bc774733fb1757a8e8a36543ca9dc8bd9`.
Independent validation rechecked 98 saved source witnesses, all 459 binding
ancestries and the actual discovery links for all 523 added tasks, with zero
HTTP requests. Source and registered-material bytes are not regenerated by
this navigation merge.

Evidence: `imports/web-hadisuz-20261112/coverage/`. The frozen acquisition
checkpoint is evidence of the recovery run; it is distinct from the merged
production checkpoint and its newer material-export state.

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

Acquisition continues independently. At the confirmed material export in commit
`7319a8788b64f48fc89cdb93119e3b6dcbf72a47`, 11,919 entries were saved,
8,231 were registered and 3,688 were held. Of the 36,390 observed inventory
entries, 23,471 ordinary fetches and 1,000 historical errors remained, a total
of 24,471 entries not yet fetched successfully. Saved entries had increased by
1,411 from the owner's 10,508-entry continuation table. These held totals include
newly acquired entries as well as the 300 resolved by this fixed review.

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

The initial review-package validation passed 188 local software tests, including reader,
importer, source-preservation, evidence-tampering, partial-update rejection and
continuation checks. Separate real-source audits exercised all 290 Islom and all
37 Hadis.uz decisions. The complete Hindi cohort was exported through the actual
importer and validated by the material registry: 300 registered parents, 1,489
selected language readings, exact reconstruction of all 1,500 source fields,
600 original evidence files unchanged, and zero HTTP requests. These are
software/evidence checks, not independent Pro or authenticity
certification. A saved decision commit is distinct from the later successful
material-export and Pages-deployment checkpoints.

The subsequent navigation follow-up passed **218 local software tests**. The
saved receipt binds the tested importer, batch controller, review adapter,
test files and exact source fixtures; the compressed test log is retained.
Real-checkpoint validation separately confirms the additive source-queue merge
and preservation of the latest production registration state. Website deployment
remains a distinct workflow outcome and is not inferred from these checks.
