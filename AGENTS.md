# Contributor requirements

This repository contains the standalone Hadith Bank and its generated reader website. Changes must keep accepted source languages and their required original Arabic quotations self-contained.

1. Preserve the exact verified Arabic and translated source text; store extraction correction patches, source editions, printed and PDF page locators, narrator chains, original collection numbers, footnotes and reviews separately. Do not invent missing details.
2. Never merge two narrations, chains, collection occurrences, editions or translation versions solely because their text or reference numbers match. Keep stable occurrence IDs and exact source references.
3. Label every new AI-produced translation explicitly. Record actual model, translation hash, reviewer, review effort, reviewed bytes, evidence and human-review status. Use ai_translation=true only with evidence; false only for established published human translations; otherwise unknown.
4. OCR is an extraction method, not proof that the translation was AI-generated. Keep original PDF text, OCR text, corrections and review logs distinct.
5. Require independent Pro QC over the exact final candidate version and its verified source before claiming a certified release. Owner-authorized pending-review publication is permitted only within the explicit scope recorded in a publication manifest and the current owner decisions below. Record actual checked pages and character/diacritic coverage; separate source transcription fidelity from metadata correctness and narrational authenticity. Public visibility is not a QC pass.
6. Preserve source reuse conditions and rights qualifications. Do not infer a license from online availability, prior Git content, or an owner's publication instruction. Unassessed rights must remain unassessed. Respect private-source restrictions except where the owner explicitly authorizes the identified material's public inclusion, as recorded below.
7. Always retain evidence and explicit null/unknown fields for uncited grades, Arabic originals, names, editions, translator information and unsupported canonical matches. Do not back-translate and label it original Arabic.
8. Search and resolve must work completely offline against files inside this repository. All runtime source locators must be local, checksum-verifiable and path-traversal safe.
9. Generate the website's language list from the accepted material manifests. The owner requested support for all bank languages and automatic integration of future additions. A new language is accepted through an explicitly authorized material manifest; do not silently publish an unrelated staged package.
10. Do not rewrite or delete previously copied verbatim source bytes just to normalize style, remove source anomalies, or manufacture a clean QC status. Version changes must preserve before/after evidence.

## Owner-authorized HadeethEnc source snapshot

On 11 November 2026 the owner explicitly requested uploading the six-language HadeethEnc source dataset, and subsequently stated that HadeethEnc needs no separate bank review. The current decision is recorded in `catalog/review-policy.json`. Apply it to HadeethEnc reading/search views, including supplied HadeethEnc workbooks in the private combined package. Keep the original import statuses as history, original text and IDs unchanged, every Arabic-version flag visible, and `certified_release_eligible=false`; no independent review is claimed. The historical upload audit remains in `datasets/hadeethenc/PUBLICATION-STATUS.json` and is not the current review policy. Publisher conditions continue to apply.

## Owner-authorized Japanese and Vietnamese PDF intakes

On 11 November 2026, after being shown the exact 1,811 Japanese and 3,254 Vietnamese occurrence scope and their pending review/rights qualifications, the owner instructed: "include them into the github bank" and requested an automatically updated website for all bank languages. This authorizes public repository and reader inclusion of the two supplied packages under `attachments/attachments-ja-muslim-c859ce57c211ea1b/` and `attachments/attachments-vi-920394517894aea9/`.

Record this visibility decision separately in `catalog/publication-policy.json` and material manifests. Preserve the packages' exact original bytes and historical `private_candidate`, `independent_pro_qc=pending`, `release_eligible=false`, unknown Arabic/metadata, and rights fields. Do not claim that independent QC occurred or that a publisher granted a new license. The reader must clearly display the current pending-review publication state alongside source history. Future owner-approved manifests may add materials in any language under the same separation of visibility, source fidelity, and certification.

## Current owner translation-origin decision

The owner confirmed on 11 November 2026 that HadeethEnc and the identified website-sourced Japanese/Vietnamese materials are human translations. Apply the scoped current display classification in `catalog/provenance-policy.json`, preserving original source AI-origin flags and evidence separately. Material copied from the old Hadith Bank, especially Japanese and including other legacy languages, remains **Unknown** until the owner explicitly confirms it. Do not change that status automatically on a calendar date. Use Human, AI and Unknown as reader categories; unknown is neither an AI assertion nor a QC failure. The source confirmation does not complete independent review.
