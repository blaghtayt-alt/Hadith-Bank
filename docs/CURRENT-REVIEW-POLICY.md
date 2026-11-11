# Current source review and publication policy

## Current reader display: QC labels for OCR only

The owner requested that QC tags apply to OCR materials only. The reader now checks explicit `ocr_used` flags and structured extraction-method evidence. Website/digital imports, native PDF text and exact quotations extracted from structured JSON do not receive pending-QC badges. A PDF filename or an Unknown translation origin is not evidence of OCR.

The four former badges—publication pending review, source review, independent Pro QC, and private-candidate import history—are absent from normal non-OCR cards. The pending-review banner counts only evidenced OCR records. Historical fields remain available in the source/audit details and canonical records; hiding a badge does not change a historical review result or assert a new review pass. Source alignment, missing references and translation-origin information remain separate from OCR review.

## HadeethEnc decision

The owner stated on 11 November 2026 that HadeethEnc needs no separate Hadith Bank review. The machine-readable decision is [catalog/review-policy.json](../catalog/review-policy.json).

The policy records **No separate bank review required — owner decision** for HadeethEnc source records. The original review fields remain in the audit history. This is an owner decision about the bank's requirement; it is not a claim that independent review was performed.

All **267 Arabic-version alignment flags** in the six-language SQLite import remain visible: Japanese 102, Chinese 103, Hindi 62. The [original exception ledger](../reports/hadeethenc/2026-11-11/public/exceptions.json), raw databases, canonical records, stable IDs and their checksums remain unchanged.

## Translation and source attribution

The owner subsequently confirmed the website-sourced materials as human and requested that old-bank copies remain unknown. The current source-specific rules are in [catalog/provenance-policy.json](../catalog/provenance-policy.json). The reader's simple **Human / AI / Unknown** classification follows these current rules while the original source-level `ai_translation` flag remains available in the provenance history. Thus the currently published HadeethEnc, Japanese Muslim and Vietnamese PDF-derived records display Human; this is an owner source confirmation, not an independent assessment of every translated passage. Copied legacy bank documents display Unknown until an explicit later owner confirmation, with no automatic change on the following day.

HadeethEnc records display **Human translation — HadeethEnc**. This source classification follows the owner's instruction and the provider's [description of its translation project and translator workflow](https://hadeethenc.com/en/home/about). A translator's personal name is shown only when the supplied source identifies it. The original record's `ai_translation` value remains available; an unknown exact-version AI-assistance history is not converted into an independently verified absence of AI use.

The source's [reuse conditions](https://hadeethenc.com/ar/home) require attribution, preservation of its content and supplied version information, among other conditions. Original wording, available source versions and source links remain attached to every record. This organization work creates no new translation.

## Owner-authorized Japanese and Vietnamese PDF publication

On 11 November 2026 the owner explicitly requested public inclusion of the supplied Japanese Sahih Muslim volume-one package (1,811 occurrences) and Vietnamese package (3,254 occurrences across 45 PDFs), after their pending review and rights qualifications were explained. The exact decision and package scope are recorded in [catalog/publication-policy.json](../catalog/publication-policy.json).

These source packages are available under the owner's publication instruction. Their original records retain `private_candidate`, `independent_pro_qc=pending`, and `release_eligible=false` as preparation history. Their extraction evidence states that native PDF text was used without OCR, so normal reader cards no longer display generic pending-QC/import-history badges. Source text, identifiers, page locators, raw Arabic issues, source conditions and unknown rights metadata remain unchanged.

## Old-bank and Qur’an-study quotations

The owner authorized extracting individual quotations from the old banks and the selected Qur’an-study materials in Japanese, Filipino, Vietnamese, Chinese, Uzbek, Hindi and Persian. Exact source text and reference scope are preserved in independently addressable records. The pinned source revision and validation procedure are documented in [the extraction guide](LEGACY-EXTRACTION.md).

These structured digital extractions are not OCR. Their translation origin remains **Unknown** under the owner's earlier instruction for copied old-bank material. Historical source AI flags remain available separately. Extracting a quotation does not establish its translator, authenticate a collection-number match, or supply missing source text.

Future authorized material manifests can add languages to the website. See [adding material](ADDING-MATERIAL.md).

## Other materials

Unregistered source packages keep their existing status. The private combined export contains additional historical material beyond the website's accepted public manifests; its existence does not automatically publish those other sources.

Historical reports remain available as evidence of what was recorded at import time. The current policy is displayed alongside that history.
