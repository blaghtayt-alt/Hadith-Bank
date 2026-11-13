# Deen Hindi: 477 complete-field manual decisions

## Integration result

All **477 assigned provider occurrences** have an independently read, attributable report in at least one of their own saved language fields: **263 Bukhari and 214 Ibn Majah**, including the two context-dependent additional Ibn Majah entries **338 and 835**. The decisions register those existing provider occurrences. They create no new provider IDs or canonical matches.

Expected queue effect against the assigned saved sources: **477 more registered parents and 477 fewer held parents**. There are **478 admitted language fields** because Ibn Majah 1762 has separate Arabic and English decisions. All decisions set `independent_pro_qc` to `not_performed`. Weakness, authenticity and canonical correspondence were not independently certified.

Copy the contents of `publish/` into the refreshed repository. The active review is:

`imports/web-deenhindi-20261112/reviews/source-review-20261113-bukhari-ibnmajah-manual-v1.json.gz`

Its SHA-256 is **`cc569049f1bf77ae0dcbe2b4a792f53dc396c88f0bbbf31bb5f05c698a980a9b`**. It has no code changes or dependencies on another occurrence’s semantic decision. The companion source ledger retains all original saved provider objects, snapshot receipts, source references and intake classifications. The reviewed source objects and exact field hashes must still match when integrating into newer main.

## Honest language coverage

| Source language field | Fully read and boundary-decided | Admitted as report text | Read but retained only as context | Unread sibling fields retained as context |
| --- | ---: | ---: | ---: | ---: |
| Hindi (`hi`) | 153 | 151 | 2 | 324 |
| English (`en`) | 326 | 326 | 0 | 151 |
| Arabic (`ar`) | 1 | 1 | 0 | 476 |
| Urdu (`ur`) | 0 | 0 | 0 | 477 |
| Roman Urdu (`ur-Latn`) | 0 | 0 | 0 | 477 |
| **Total** | **480** | **478** | **2** | **1,905** |

Bukhari’s admitted fields are 22 Hindi and 241 English. Ibn Majah’s are 129 Hindi, 85 English and one Arabic. Nineteen source fields labelled Hindi contain Latin script; each has an explicit script note while retaining its original provider field identity. This is not a claim that those fields are Devanagari Hindi or that the unread siblings were reviewed.

The complete readings cover **226,377 Unicode code points / 287,862 UTF-8 bytes**. Selected report passages cover **220,090 code points / 279,379 bytes**, in **631 exact spans**. The source fields together contain 1,267,031 code points / 2,060,955 bytes. Their remaining **1,046,941 code points / 1,781,576 bytes** stay as context. The **541 report components across admitted language fields** are presentation/attribution groupings, not 541 new independent source occurrences; one entry can contain multiple voices, a repeated provider telling, or two independently read language versions.

## Review decisions that matter

- **Ibn Majah 338 and 835:** both additional context-dependent entries were read directly in their own Hindi-labelled field. No Fawaz or another source occurrence’s boundary decision was transferred. Entry 338 has a finite abbreviated report in Latin script and retains the ultimate speaker’s uncertainty; entry 835 has an explicit own-field Prophetic observation.
- **Ibn Majah 284:** the Hindi field ends midway through its answer. Its complete saved field was read and retained only as context. The independently read complete English report supplies the admitted text; the source grade and alternate-chain notice stay context.
- **Ibn Majah 1762:** the Hindi field prints `शहरों`. It is retained literally as reviewed context, without silently changing that word into “husbands.” The complete English field and complete Arabic chain/matn were separately read and admitted on their own wording.
- **Abbreviated reports:** finite independently stated acts remain usable without importing missing text. For example, Ibn Majah 849’s independently stated prayer leadership is admitted; the previous-report pointer and unclearly attributed added statement remain context. Entry 1241 preserves the actual historical dialogue while explicitly leaving the omitted subject of “a new matter” unspecified.
- **Actual voices:** Companion practices, successor observations, narrator follow-ups, quotations within a report and later scholarly statements are identified by their own speaker. Examples include Bukhari 1228.2, 1390.2 and 1390.3; Ibn Majah 630, 1006, 1071, 1169, 1611, 1630, 1800 and 1801. They are not all described as direct Prophetic speech.
- **Embedded source criticism:** Ibn Majah 248’s source `Maudu'` label and criticism, 309’s `Da'if` and critical discussion, 374’s correctness/error note, and the grades or chain notices in other selected fields remain context. The provider’s separate grade field also remains unchanged. Registration here is an attribution/boundary decision, not an authenticity upgrade.
- **Mixed reports:** exact component boundaries separate later questions, alternate transmitter wordings and observations when their voices change. Source alternatives and contradictions remain visible, including Sufyan’s uncertain count in Ibn Majah 927, the different burial descriptions in 1470/1471, and different initial marriage ages in 1876/1877.
- **Provider repetition:** Ibn Majah 1891 repeats the report in its English field. Both source tellings are preserved as separate components inside the same provider occurrence; they are neither deduplicated nor counted as new parent IDs.
- **Unattributed explanatory material:** lexical glosses, editorial calendar conversions, extra legal explanations, source-grade labels and cross-references remain context where they do not form the independently attributable report. These passages are retained byte-exactly in the source ledger and character-exactly in the derivative context partition.

Every record carries its own substantive decision reason and source-bound span hashes. The decisions were authored after reading the full selected field, not inferred by a keyword, length, collection-membership or grade heuristic. Field length was used only to organize the reading order. No new translations or external canonical identities were produced.

## Offline validation

`package_and_validate.py` loaded the current parent workspace’s `import_deenhindi.canonical_record` and `SourceReviews` implementation. It passed the complete **477-record apply/finish cycle** and the following checks:

1. All 477 exact saved provider objects match their review hashes, snapshot receipts and printed references.
2. Every one of the **2,385 original language fields** is reconstructed exactly by its selected report spans plus retained context spans. No character is dropped, duplicated or inserted in that partition.
3. The original occurrence ID, source entry number, null canonical number, printed reference, provider grade, narrator metadata and snapshot locator remain unchanged for every parent.
4. Unread languages have null quotation text and retain the complete original field as context. An English or Arabic admission does not populate the Hindi primary translation slot.
5. Every admitted field has full-field reading counts and exact nonoverlapping span hashes. Both reviewed-context Hindi fields have no admitted spans.
6. All nineteen Latin-script Hindi-labelled fields receive their explicit script note without changing provider field identity.
7. Every occurrence remains uncertified for independent Pro QC and has no asserted canonical identity.

The full metrics and code-input hashes are in `validation.json` and the identical packaged evidence report. `derived-preview.jsonl.gz` is a local validation preview; root should generate canonical materials using the refreshed upstream importer rather than copy this preview into materials.

**Raw response verification limit:** the 477 existing snapshot receipt bindings and source objects were checked, but the corresponding raw HTML and parsed gzip files are not present in this local review workspace. This review therefore does not claim to have reopened those original response bytes. Upstream integration must retain and validate the existing immutable snapshots. No source requests were made for this Deen review.

## Files and reproducibility

- `publish/`: four repository-ready files: active decisions, immutable source ledger, validation evidence and this handoff as evidence.
- `decisions/`: 477 individual authored JSON checkpoints.
- `original-475.jsonl` and `additional-2.jsonl`: exact supplied assignment snapshots.
- `review_builder.py` and `record_*.py`: explicit per-entry authoring helpers; these do not classify unread text.
- `package_and_validate.py`: full offline package/partition verification.
- `derived-preview.jsonl.gz`: all 477 validated canonical derivatives for inspection.
- `source-bindings.json`: the 477 source-object/snapshot bindings.
- `handoff-manifest.json`: hashes and sizes of the four repository-ready files.

No upstream repository or other agent workspace was modified. All files in this handoff were written under `/workspace/scratch/44aeee8a6071/deen-bukhari-ibnmajah-review`.
