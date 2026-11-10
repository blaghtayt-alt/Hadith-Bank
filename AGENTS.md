# Contributor requirements

This repository is the standalone Hadith Bank, not a live application. Changes must keep its six selected languages and their required original Arabic quotations self-contained.

1. Preserve the exact verified Arabic and translated source text; store extraction correction patches, source editions, printed and PDF page locators, narrator chains, original collection numbers, footnotes and reviews separately. Do not invent missing details.
2. Never merge two narrations, chains, collection occurrences, editions or translation versions solely because their text or reference numbers match. Keep stable occurrence IDs and exact source references.
3. Label every new AI-produced translation explicitly. Record actual model, translation hash, reviewer, review effort, reviewed bytes, evidence and human-review status. Use ai_translation=true only with evidence; false only for established published human translations; otherwise unknown.
4. OCR is an extraction method, not proof that the translation was AI-generated. Keep original PDF text, OCR text, corrections and review logs distinct.
5. Require independent Pro QC over the exact final candidate version and its verified source before publication. Record actual checked pages and character/diacritic coverage; separate source transcription fidelity from metadata correctness and narrational authenticity.
6. Do not publish copyrighted or private PDFs, candidate text or source translations without an appropriate reuse basis. Previously available Git content is not a blanket licensing grant.
7. Always retain evidence and explicit null/unknown fields for uncited grades, Arabic originals, names, editions, translator information and unsupported canonical matches. Do not back-translate and label it original Arabic.
8. Search and resolve must work completely offline against files inside this repository. All runtime source locators must be local, checksum-verifiable and path-traversal safe.
9. Keep the public language scope limited to Japanese, Filipino, Vietnamese, Simplified Chinese, Uzbek and Hindi unless explicitly expanded by the repository owner.
10. Do not rewrite or delete previously copied verbatim source bytes just to normalize style, remove source anomalies, or manufacture a clean QC status. Version changes must preserve before/after evidence.

## Owner-authorized HadeethEnc source snapshot

On 11 November 2026 the owner explicitly requested uploading the six-language HadeethEnc source dataset, and subsequently stated that HadeethEnc needs no separate bank review. The current decision is recorded in `catalog/review-policy.json`. Apply it to HadeethEnc reading/search views, including supplied HadeethEnc workbooks in the private combined package. Keep the original import statuses as history, original text and IDs unchanged, every Arabic-version flag visible, and `certified_release_eligible=false`; no independent review is claimed. The historical upload audit remains in `datasets/hadeethenc/PUBLICATION-STATUS.json` and is not the current review policy. Other PDF/OCR requirements and the existing public/private source scope are unchanged. Publisher conditions continue to apply.
