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

## Reliable remote execution and transfer

The owner requested fixing or avoiding repeated Remote Desktop Commander failures on 11 November 2026. Large encoded transfers and verbose command output repeatedly exhausted conversation context; a tool returning a running PID or call ID is not itself a failure.

- Prefer direct Git or the GitHub connector for repository operations. Check read access and write authentication separately in the environment that holds the files. Use the authenticated device when needed; do not copy credentials between environments.
- Keep file bodies, Base64, archives and complete logs out of the conversation. Transfer bytes directly or pass them between tools inside orchestration code without printing them. Return only status, byte counts, hashes, refs and short error summaries. A line limit does not bound a megabyte-long line.
- Use `scripts/run_logged_task.py` for lengthy or verbose commands. Its job directory stores output and atomic status; reuse that directory to inspect an uncertain execution, not to launch another copy. Keep logs and checkpoints under the ignored `.work/` directory or outside the repository.
- After a running Remote MCP `call_id`, use `get_tool_result`; after a terminal PID, use `read_process_output` or the saved job status. Inspect the existing result before retrying a write, upload, commit or push. Do not restart a pending mutation.
- Reuse verified original files, commits and transfer parts. Keep a compact checkpoint with source commit, destination ref, expected hashes, completed stages and any active call ID/PID. Never restart extraction solely because a chat ended.
- Publish canonical sources and code; the existing `reader-pages.yml` workflow rebuilds generated reader, catalog and search outputs. Preserve concurrent imports by refreshing the destination ref and using a normal fast-forward or an expected-head check.
- Treat browser launch failures separately from data validation. Record the actual error once, use an available browser runtime, and leave UI verification pending until it really runs. Do not report software tests as browser checks.

Examples and recovery rules are in `docs/REMOTE-WORKFLOW.md`. These are execution guidelines, not changes to access controls, source review policy or publication authorization.

## Owner-authorized HadeethEnc source snapshot

On 11 November 2026 the owner explicitly requested uploading the six-language HadeethEnc source dataset, and subsequently stated that HadeethEnc needs no separate bank review. The current decision is recorded in `catalog/review-policy.json`. Apply it to HadeethEnc reading/search views, including supplied HadeethEnc workbooks in the private combined package. Keep the original import statuses as history, original text and IDs unchanged, every Arabic-version flag visible, and `certified_release_eligible=false`; no independent review is claimed. The historical upload audit remains in `datasets/hadeethenc/PUBLICATION-STATUS.json` and is not the current review policy. Publisher conditions continue to apply.

## Owner-authorized Japanese and Vietnamese PDF intakes

On 11 November 2026, after being shown the exact 1,811 Japanese and 3,254 Vietnamese occurrence scope and their pending review/rights qualifications, the owner instructed: "include them into the github bank" and requested an automatically updated website for all bank languages. This authorizes public repository and reader inclusion of the two supplied packages under `attachments/attachments-ja-muslim-c859ce57c211ea1b/` and `attachments/attachments-vi-920394517894aea9/`.

Record this visibility decision separately in `catalog/publication-policy.json` and material manifests. Preserve the packages' exact original bytes and historical `private_candidate`, `independent_pro_qc=pending`, `release_eligible=false`, unknown Arabic/metadata, and rights fields. Do not claim that independent QC occurred or that a publisher granted a new license. Apply the current OCR-only review-display policy below; original pending-review fields remain part of source history. Future owner-approved manifests may add materials in any language under the same separation of visibility, source fidelity, and certification.

## Current owner translation-origin decision

On 11 November 2026 the owner clarified that **only copied old-bank resources are labelled Unknown**, and **all newly added books are Human translations unless their own source explicitly states otherwise**. Apply this rule automatically to current and future registered nonlegacy books and to separately acquired English counterparts. The current policy is recorded in `catalog/provenance-policy.json`.

Keep copied legacy-bank and Iman/Quran-study quotations, including the `legacy-*` and `quran-excerpts-*` source families and the original old-bank source documents, in their current Unknown group. A later import date does not turn an old-bank copy into a new publisher source. Classify each English counterpart from its own source, independently of the parent Chinese or legacy translation. Arabic originals are source texts and must not receive a translation-origin label.

A source's explicit contrary translation declaration takes precedence over the new-book Human default. Preserve its wording or precise locator in `translation_provenance.source_declaration` with a classification and evidence. Do not infer AI translation from OCR, AI extraction, an AI reviewer, alignment work, a missing translator name, or missing metadata. Preserve original AI-origin flags, translator fields and historical evidence separately; the current owner display decision does not rewrite source records or assert new review, authenticity, or rights clearance.

## Owner-authorized embedded hadith extraction and Persian

On 11 November 2026 the owner requested extracting individual hadiths from the old bank's lessons and articles, and from the Quran books in `blaghtayt-alt/iman-companion`, into this bank's normal structured format. The scope is Japanese, Filipino, Vietnamese, Chinese, Uzbek and Hindi, with Persian (`fa`) added. This authorizes publishing the resulting source-preserving registered materials and updating the reader. Preserve the original source snapshots, stable occurrence identities, exact quotation boundaries and source locators. Keep narration text distinct from Quran verses, commentary, historical anecdotes and proverbs. Preserve supplied book names, numbers, narrator/translator information and scoped variant references; leave genuinely unsupported fields null and record unresolved attribution rather than guessing.

Copied old-bank and Quran-book translations remain **Unknown** under the current owner policy, including after segmentation. Preserve historical AI-origin evidence separately. Do not inflate counts by extracting the same occurrence from JSON, Markdown, plain-text and reader mirrors as if each were a different narration. Distinct source versions, wording variants and separately cited occurrences remain distinct and retain their relationships.

## Current OCR-only QC display decision

The owner requested removing QC tags from outsourced, non-OCR materials and specified that QC tags are for OCR materials. Show OCR review badges and the review-count banner only when structured extraction evidence establishes that OCR was used. Human translation, a PDF file extension, or a historical generic review warning alone does not establish OCR. Digital source imports, native PDF text and structured quotation extraction do not receive OCR-QC tags. Preserve original review/status fields in the source and optional audit details; suppressing an inapplicable display tag is not a declaration that independent QC was performed or passed. Keep genuine missing-source, incomplete-quotation and attribution qualifications available separately.

## Owner-authorized Arabic and English counterparts

On 11 November 2026 the owner requested optional Arabic and English counterparts while browsing, with the source collection and hadith number after each quotation, and automatic Arabic/English keyword and number search. This authorizes acquiring official HadeethEnc counterpart exports, publishing the source-preserving linked views, and resolving future registered material during the existing website build. Keep counterparts additive: original occurrence IDs, counts, text, translation-origin classifications and review history remain unchanged. Credit the counterpart's own publisher, version and translation origin separately.

Use explicit primary provider identity, or a unique source-quotation match with supporting references. A parent article's URL alone is insufficient for a quotation in its notes. Never infer an identity from collection numbers alone, promote a provider ID or local sequence to a canonical number, reconstruct missing Arabic, or manufacture an English translation. Distinguish full counterparts from source excerpts and visibly qualify differing publisher versions. Unknown links and absent numbers remain explicit. Preserve immutable source downloads and hashes, source reuse conditions, and unresolved coverage. Counterpart availability is not an independent authenticity or translation certification.

## Owner-authorized Persian native DOCX imports

On 11 November 2026 the owner requested conversion, bank integration and HTML verification of the nine supplied Persian DOCX files: six Faiz al-Bari volumes, two Mukhtasar Sahih Muslim volumes, and the Heravi Riyadh al-Salihin edition. The owner explicitly stated that these imports need no QC tags and that Persian side comments must be removed, retaining hadiths only. These instructions are scoped to the nine `materials/fa-*/manifest.json` registrations added by `scripts/import_persian_docx.py`.

Use the `owner_requested_public_source_import` publication decision and the explicit non-OCR `display_policy.qc_tags=false` policy. Do not add review/QC tags to their reader or search presentation. This display choice makes no independent certification assertion. Named translators printed in the source editions support the Human classification; no new translations were produced. Preserve source citations, grades, headings, local numbering, source defects and missing fields as metadata. Keep narration quotations extracted from notes distinct from complete numbered source occurrences and Companion statements. Do not deduplicate source occurrences or manufacture missing text. Keep removed commentary, original glyphs and extraction evidence outside the hadith/search payload. Preserve exact original DOCX files and the compressed source audits. Rights remain unassessed.

## Owner-authorized Persian Targhib and Tarhib volumes

On 11 November 2026 the owner requested adding the three supplied `targheeb-va-tarheeb-saheeh-va-zaeef-{1,2,3}-Word.docx` volumes to the Persian bank, retaining hadiths only, excluding commentary, and flagging ideological insertions. This authorization covers the three `materials/fa-targhib-bazmandegan-v*/manifest.json` registrations and their exact source documents and extraction evidence.

Preserve the source's differently graded narrations, distinct occurrences, numbered variants and explicitly identified Companion reports. Label partial quotations as excerpts and relate fragments of the same source report. Keep editor/compiler discussions, doctrinal polemics, lexical explanations, and independent non-hadith sayings outside the narration/search payload. Bounded actual narration quotations within such discussions may be registered separately with precise spans. Preserve every removed span and its reason in `imports/persian-targhib-20261111/`; original DOCX bytes remain unchanged.

Keep the edition's three numbering systems distinct from canonical collection numbers. Preserve the exact source assessment and name its individual grader only where explicitly supported; the title-page takhrij credit is separate. Retain source translation defects, absent or unresolved language alignments, and punctuation/font anomalies without synthesizing corrections. The OCR-only display policy applies to this native OOXML import; no new translation, independent Pro certification, or rights clearance is asserted.
