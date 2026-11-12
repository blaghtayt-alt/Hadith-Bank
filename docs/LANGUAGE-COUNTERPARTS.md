# Arabic and English counterpart intake

The shared resolver runs for every accepted source language. Coverage reports count actual Arabic and English availability independently: source text, linked quotation text, an external-only source page, or a missing language. An unresolved match can coexist with Arabic already printed in the source. Supporting a language or registering a book does not establish complete counterpart coverage.

`prepare_counterpart_review.py` prepares a review backlog. `compile_reviewed_counterparts.py` accepts explicit occurrence-level decisions into a new immutable bundle. Neither command translates text, establishes narrational authenticity, grants reuse rights, or certifies an independent review.

## 1. Register the new source occurrence set

Use the normal material intake described in [ADDING-MATERIAL.md](ADDING-MATERIAL.md). Preserve the original document, its exact text, source/edition information, extraction history, locators and original collection numbers. Supply a distinct registered `source_id`, edition and stable occurrence IDs for another edition or installment. Do not replace an earlier Chinese source or reuse its occurrence IDs merely because local numbers or words agree.

The generic review workflow reads accepted `materials/*/manifest.json` registrations and the published HadeethEnc collection snapshots. It verifies original document checksums and canonical records directly; it does not require a generated website. Unknown Arabic or English remains absent. There is no back-translation fallback.

## 2. Prepare candidates

From the repository root:

```sh
python scripts/prepare_counterpart_review.py \
  --source-id new-registered-source-id \
  --profile abu-dawud \
  --output .work/new-source-counterpart-queue
```

Omit `--source-id` for the entire bank. `--profile all` is the default. `--profile registered` omits the supplemental full Abū Dāwūd raw index; registered publisher and reviewed target entries remain available. `--include-resolved` includes already available occurrences for a diagnostic queue. `--max-candidates` bounds suggestions per occurrence (default 8, maximum 50). A reviewer may add a known candidate from the saved target inventory with `--include-target raw-abu-dawud:NUMBER`; this still grants no approval.

The output folder contains a deterministic compressed queue, a compressed inventory of the target candidates used in that queue, and a manifest of counts and input checksums. Each queue row binds its occurrence identity, original document SHA-256, exact canonical record SHA-256, quotation hash and source locator hash. Counts distinguish candidates from occurrences with no candidate. `accepted_by_this_preparation` is always zero and `publication_ready` is false.

The bank refresh also generates this backlog under `reports/counterpart-review/`. Preparation checks Arabic and English separately, so an Arabic-only reviewed mapping with no English still enters the backlog. Its availability rules are the same as the reader and coverage report, including native English/Arabic and safe external-only links.

**Keep manual review files outside the generated output directory.** A refresh may replace only its own generated files and refuses to replace a folder containing manual decisions.

### Candidate evidence and future Chinese Abū Dāwūd sources

Candidate generation uses cached indexes of publisher targets, unique or ambiguous Arabic quotation matches, scoped references and already reviewed source text. A previous approval is a suggestion for another occurrence, never an inherited approval. Source numbering and a Chinese local sequence may supply a low-priority search hint; neither can establish a match.

The `abu-dawud` profile verifies and reuses the full saved `ara-abudawud.json.gz` snapshot recorded by the original Chinese bundle's provenance. It is not limited to the target subset used by the first Chinese edition. Candidate keys are `raw-abu-dawud:NUMBER`, where the number is the raw provider's locator. An empty raw entry is omitted instead of being reconstructed. The separately preserved Chinese bundle and its source corrections remain untouched.

The full Arabic entries may contain narrator chains and compiler notes. Preserve their scope as `source_entry` and record a source excerpt when appropriate. Different chains, Companion reports, neighboring entries and text fragments require explicit comparison. A shared local number, a matching topic or similarity score cannot distinguish them reliably.

Previously approved Chinese English quotations are occurrence-specific. Reusing their stored text for another source requires a fresh English content decision, with exact source/English anchors and the corresponding qualifications. An Arabic approval cannot grant English approval.

## 3. Record explicit review decisions

Create a separate UTF-8 JSONL sidecar, one decision per source occurrence, following [counterpart-review.schema.json](../schemas/counterpart-review.schema.json). Preserve the exact current hashes. The helpers in `scripts/counterpart_review.py` avoid hand-calculating a different hash convention:

```python
import sys
sys.path.insert(0, "scripts")  # Run this example from the repository root.
from counterpart_review import source_binding, raw_abu_dawud_targets

# record is the normalized canonical occurrence read by load_source_records.
# Defaults to text_translation when present, including Chinese-only books.
binding = source_binding(record)
targets, assets = raw_abu_dawud_targets(root)
target = targets["raw-abu-dawud:NUMBER"]
target_hash = target["target_entry_sha256"]
```

The source binding can use `text_translation` or `text_arabic`. The compiler also verifies the preparation row against the current occurrence, even when the reviewer uses the other field. The locator hash covers the original-file path, canonical record locator, preserved source locator and page metadata. The target hash covers the complete assembled entry, including URLs, references and scope; it is not merely an Arabic text hash or a raw JSON-row hash.

An accepted row requires all of these:

- `status: "verified"`, `target_key`, `target_entry_sha256`, and `relation: "same_narration"` or `"source_excerpt"`.
- An actual reviewer identity, meaningful review method, explicit `human_review` boolean, substantive source/target quotation evidence and any qualifications. AI-assisted alignment review is not human review and does not turn an existing translation into an AI translation.
- Exact literal `source_quote` and `target_quote` anchors, their source field and target language, and a rationale explaining the comparison. Each anchor must contain at least 32 Unicode letters after NFKC normalization. Numbers or punctuation do not count. Short or ambiguous sources remain unresolved unless a future separately verifiable context contract is implemented.
- Separate `language_decisions.arabic` and `language_decisions.english`, each with a rationale. Accepted stored text requires evidence whose `target_language` matches that language. English evidence cannot be substituted with an Arabic-only anchor.

Language decisions are:

| Decision | Result |
| --- | --- |
| `approved_text` | Copy the exact text and metadata from the pinned candidate target. New or edited text is rejected. |
| `approved_external` | Supply only a reviewed source page with `text: null`, `text_sha256: null` and `scope: "external_source"`. The URL is not stored or searchable English quotation text. |
| `unavailable` | Preserve this language as absent. |
| `unresolved` | Preserve this language as absent pending a supported match. |

For an approved stored quotation that covers only part of this source occurrence,
add all three decision fields `scope: "source_excerpt"`, `coverage: "partial"`,
and a specific `citation_note`. The complete pinned quotation and its text hash
remain unchanged. The compiler preserves the original scope as `source_scope`,
retains any existing citation note and appends the occurrence-specific limitation.
The English evidence and rationale must explain which source clause is covered
and which additional clause or variant is not. Other scope/coverage overrides,
or a partial claim without its visible note, are rejected. Broader publisher-entry
reference scopes remain `publisher_entry`; they are not promoted to exact
main-quotation references.

For an external link, `reviewed_url` must equal the counterpart's exact source URL. Record `page_review` on that language decision, or `review.official_page_review`, with the same URL, the actual retrieved date, a retrieval reference, and `arabic_compared: true` or `english_compared: true` for the approved language. Preserve important partial coverage in `counterpart.coverage` and `counterpart.citation_note`; a source page that translates only one clause must not imply full English coverage.

If the external language target already exists in the pinned candidate, all its metadata and qualifications must be preserved. A stored-text target may be converted to an external link only by clearing text and its hash and setting external scope; partial-coverage notes cannot be removed. Supplemental English for `raw-abu-dawud:NUMBER` may use only the exact `https://sunnah.com/abudawud:NUMBER` page with that source-record ID and one matching Abū Dāwūd main-quote reference. The page still needs a separate actual content check. Other supplemental external providers must first have independently pinned target metadata and a supported identity contract; arbitrary URLs with a rationale are rejected.

An uncertain entire mapping uses `status: "unresolved"` and a reason; a rejected candidate uses `status: "rejected"` and a reason. They do not produce live mappings. Review notes and source bytes remain available for later work. A file containing only unresolved/rejected decisions stays in the backlog rather than producing an empty published bundle.

## 4. Validate, then compile the exact approved scope

```sh
python scripts/compile_reviewed_counterparts.py \
  --queue .work/new-source-counterpart-queue \
  --reviews .work/new-source-review-decisions.jsonl \
  --bundle-id new-source-alignment-v1 \
  --snapshot 2026-11-11 \
  --publication-basis "Existing owner authorization and this exact reviewed source scope" \
  --check-only
```

Use lowercase safe bundle IDs and snapshot identifiers. After the checks pass, run the same command without `--check-only` to create the local bundle and append its descriptor to `sources/counterparts/reviewed/manifest.json`. This records an existing authorization; it does not create permission for an unrelated source. Commit/publication and the normal website workflow remain separate steps.

The compiler reloads current canonical sources, verifies every reviewed source and target hash, reconstructs candidate targets from their pinned inputs, checks each exact anchor and language decision, and rejects stale source text, metadata, locators or targets. A target URL/reference change also invalidates its complete entry hash. The compiled bundle preserves the exact original review sidecar, preparation metadata, selected source bindings, comparison target entries and their immutable inputs. Existing source documents, canonical records and older counterpart bundles are unchanged.

The generic bundle declares `evidence_contract: "occurrence-identity-v1"`. Runtime resolution repeats its source-identity and exact evidence checks and leaves a stale occurrence unresolved. The frozen original Chinese bundle retains its existing contract and compiler. Exact reruns are idempotent; differing bytes under an existing bundle ID are rejected. A second generic assignment to an occurrence already covered by a reviewed bundle is refused because competing assignments would be ambiguous. Keep a proposed additional language for such an occurrence in the backlog until an explicit append-only supplementation contract is available.

The public availability report is the completion measure. Passing software tests, generating candidates, accepting one language, or linking an external page does not establish that every bank occurrence has both Arabic and stored English text.

## Number suffixes and source-version content holds

A source citation such as `Muslim 2577a` and a publisher bibliography citation such as `Muslim 2577` retain their original forms. The automatic resolver may treat the bare-number/suffixed-number pair as corroboration only after a substantive Arabic quotation is equal to, or contained in, the pinned target quotation and the target is unique. Two different suffixes remain conflicting. The suffix does not enable number-only matching, translated-phrase-only matching, or treating a shorter target as covering a longer source. The evidence stores both citations and does not assert equivalence between numbered routes.

Content review is separate from matching and translation origin. Exact English source versions with a concrete meaning discrepancy are recorded in `catalog/counterpart-quality-policy.json`. A hold applies only to that publisher ID and text hash; it removes the derived English quotation and its external-link fallback while retaining the original downloaded bytes, Arabic and Human/Unknown source-origin decisions. A different corrected English version needs its own review. A genuinely bounded translation excerpt can instead be accepted with an explicit partial-coverage note.

The [12 November continuation audit](../reports/counterpart-continuation-2026-11-12.md) distinguishes newly reviewed mappings, restored suffix matches, additions, content holds and remaining missing languages. It does not treat unrecovered work from an interrupted session as published evidence.
