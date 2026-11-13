# Website-source queue resolution — 13 November 2026

The owner requested fixing the remaining Deen Hindi acquisition queue and held
entries, the eleven Hadis.islom.uz holds, and the 244 Fawaz source entries.
This checkpoint saves the first concrete repair set. Current generated progress
and deployment remain separate, observable workflow results; these preflight
counts must not be presented as a completed live export.

## Deen Hindi acquisition

At source checkpoint `7b22548d43bccce94cce0e04d734e47458460fac`, 12,371 of
36,390 observed source IDs had been saved. The 24,019 remaining consisted of
23,019 ordinary pending pages and 1,000 historical fetch errors.

All 1,000 archived error responses have now been decompressed and verified
against their stored and original-response SHA256 values. Every one is an
HTTP200 verification page, not a usable hadith page. The exact per-ID audit is
in `imports/web-deenhindi-20261112/retry-audits/`.

The normal serialized worker now supports an explicit, hash-bound, one-request
authorization for a reviewed historical error. It retains prior errors and
attempt receipts, consumes authorization before a request, preserves uncertain
outcomes after interruption, and does not automatically replay a request after
manifest changes. Existing source stops, ordinary routes, request pace and
access checks remain effective. Blanket historical-error retry is limited to
positively identified transient failures.

The active manifest authorizes **only `bukhari:686` as a pilot**. No live retry
was issued during the archive audit. A renewed challenge stops the source;
inspect the actual pilot result before authorizing any other archived error.
The ordinary unfinished queue continues through the existing bounded workflow.

## Deen Hindi held entries

The baseline contains 3,824 held source entries. Exact complete same-language
field matching to existing explicit Fawaz boundary reviews safely resolves
**1,616 entries**, selecting 1,984 fields: 1,469 English, 212 Arabic and303 Urdu.
The preflight checked complete quotation/context partitions for all7,861
nonempty supplied fields in those entries.

This reuses a prior boundary/type/speaker judgment only when the entire field's
UTF8 hash and language agree. It transfers no source identity, provider number,
canonical mapping, chain or grade. All Deen source references and original
fields remain intact. Unmatched sibling languages remain complete source
context and are not asserted to have been read or approved.

Ninety-four matching fields depended on a different Fawaz source occurrence.
They are explicitly excluded from automatic reuse: equal child text does not
establish a Deen-local parent relationship. This leaves **2,208 baseline
entries for separate source-bound review**. Manual book-specific reviews are
under way and will be saved in later checkpoints. The generated reuse ledger is
committed only after every manual and reused source decision passes preflight.
Changed review inputs, a changed engine or missing/tampered generated evidence
trigger a bounded offline refresh.

See `reports/web-source-resolution-20261113/exact-review-reuse-preflight.json`
for the exact baseline, inputs, language counts and verification limits. The
continuing importer applies the same guarded reuse to eligible future saved
entries. Full saved HTML and parsed-object checks remain mandatory in export.

## Hadis.islom.uz

All eleven held primary entries have received a disposition. Six qualify for
registration with their actual attribution; five are headings, pointers,
commentary or wisdom material. Two excluded parents contain three bounded
quoted passages, registered as **two separate commentary occurrences** with
fresh source metadata. Parent numbers, narrators, Arabic, grades and canonical
identities are not inherited by those children.

The complete offline export preserved all8,625 provider entries and produced
**8,622 reader occurrences**:8,620 primary entries plus2 commentary children.
There are5 reviewed primary exclusions and0 unreviewed classification holds.
The Qunut entry retains an unnamed reciter in the Islom source, no asserted
Prophetic attribution, and a separately qualified external Ibn Masud parallel;
its exact Musannaf identity remains unverified.

The evidence, prior ledger, per-ID decisions and complete export verification
are under `imports/web-uzbek-20261112/islom/reviews/islom11-audit/`.

The one known failed source section, `/kitob/32/17`, still returned HTTP500 on
the explicit ordinary recheck at08:58:41UTC. Attempt5 preserves all four earlier
attempts. Its response body matches attempt4; the new request event is retained
separately. All341 successful saved pages were scanned and no untracked
observed collection/section route was found. Publisher catalogue anomalies are
recorded in `coverage/20261113-observed-route-followup.json`; unavailable text or
unobserved routes are not invented.

## Fawaz244

All244 provider IDs and all895 supplied fields have an explicit source-bound
disposition. Six IDs contain recoverable attributed scholarly reports or
sayings: Abu Dawud2424,3338,3339,3587 and Nasai4221,5752. Twenty-one actual
language fields are selected; the Bengali speaker discrepancy in Abu Dawud3587
remains context with an explicit mismatch explanation.

The remaining238 source entries are fully preserved outside the narration
reader:169 are empty in every supplied field,67 are explanation/commentary,
one is a missing-text marker, and one supplies a chain without a report body.
They have completed semantic disposition; these are not238 unread records.
Source gaps remain real, and no missing text has been filled.

The expected full-export totals are36,226 reader occurrences,238 reviewed
source-only occurrences, and0 source-only entries awaiting semantic disposition.
Already registered records' unreviewed sibling-language queues are separate
from these244 parent dispositions and are not claimed complete.

All10,917 prior Abu Dawud/Nasai registered rows remained byte-identical in the
two-book export comparison. The full checkout gate verifies all disposition
bindings and the other source books against the original editions before
publishing refreshed material. Evidence and code-specific validation are in
`reports/fawaz-held-resolution-20261113/`.

## Validation and continuation

The combined local repair tree passed110 offline importer, review, retry,
commentary-isolation and disposition tests. The Islom full export made no
source requests and preserved all eleven original collection ledgers exactly.
The existing GitHub importer and reader workflows remain the full-checkout,
source-integrity and deployment gates. Record their actual outcomes separately
from this saved repair checkpoint.

Classification and preservation work is not independent Pro QC, authenticity
grading, translation-equivalence certification or rights clearance.
