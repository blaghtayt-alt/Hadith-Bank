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


## Owner-authorized multilingual website intake

On 12 November 2026 the owner requested proceeding with all three identified sites: deenhindi.com/hadith, rivoyat.com and hadis.islom.uz. The owner authorized importing their hadiths, retaining each language's own or explicitly cited upstream references and comments, adding collapsible language panels, and preserving language/book/collection filters. This covers source-preserving deenhindi-*, rivoyat-* and islom-* registrations and their imports/web-*-20261112 evidence.

Continue the finite source queues through the bounded import plan. Preserve source bytes, empty fields, source-local numbering, supplied language versions and immutable evidence. Keep site-wide credits distinct from a verified per-translation upstream source. Do not merge identities by numbers or similar text. Retain mixed introductions, independent sayings and unresolved spans outside Hadith HTML until narration boundaries are supported. Prophetic practices, dhikr, dialogue and explicitly attributed abbreviated matn remain eligible; a literal speech marker is not mandatory. The authorization changes visibility only, with no new translation, independent certification or rights clearance asserted. Existing provenance and OCR-only display policies remain in effect.

### Current Rivoyat exclusion

Later on 12 November 2026 the owner explicitly withdrew Rivoyat from this intake because its translation source was unknown and requested removal of every hadith acquired from `rivoyat.com`. This instruction overrides the earlier Rivoyat authorization above: remove its registered source occurrences from the bank and reader, disable its intake, and do not reacquire or re-register Rivoyat material automatically. Reinstatement requires explicit new owner authorization. This exclusion is scoped to Rivoyat; it does not withdraw authorization for Deen Hindi, Hadis.islom.uz, or separately attributed identified upstream editions.

### Identified upstream whole-book editions

The owner's same request includes sources explicitly cited by those sites. On 12 November 2026 the owner supplied Deen Hindi's source acknowledgement naming Fawaz and Sunnah.com and requested batch acquisition. This covers the separately attributed Arabic, English and Urdu editions of the seven Deen hadith collections in `catalog/fawaz-bulk-plan.json`, pinned to `fawazahmed0/hadith-api` revision `df57907be35291c91ad6a6691180e22ca9920784`, with source evidence under `imports/web-fawaz-20261112/` and `materials/fawaz-*` registrations. It does not include the site's separate Quran/Tanzil sources.

Keep exact upstream files, edition IDs, hashes, source-declared grades and numbering. Register complete verified book batches; keep partial or corrupt downloads outside the reader and retain explicit missing-language states. The upstream editions are their own source occurrences, not a claim that every Deen translation comes from that edition. Do not replace Deen records, transfer identity by matching numbers, invent missing Hindi, or turn collection-wide credits into per-language evidence. Apply current translation-origin and non-OCR display policies while retaining independent provenance and rights qualifications. Acquisition and visibility do not assert independent certification or a new redistribution licence.

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

The owner subsequently requested Arabic/English integration across **all bank hadiths** and preparation for **future Chinese Abū Dāwūd additions**. Use the shared resolver and availability report for every registered source, and prepare missing counterparts through `docs/LANGUAGE-COUNTERPARTS.md`. Separate Arabic already present, stored English quotations, external-only language links and missing counterparts; runtime support for all sources does not mean all occurrences have both languages. Keep the original Chinese compiler and mappings immutable. A new installment or edition requires its own source identity and evidence-bound mapping decisions; do not transfer mappings by local number or similarity alone. Candidate queues are preparation artifacts and never grant publication as accepted parallels. Arabic approval and English approval are separate decisions, with source and target hashes, exact evidence and excerpt/variant qualifications retained.

## Owner-authorized Persian native DOCX imports

On 11 November 2026 the owner requested conversion, bank integration and HTML verification of the nine supplied Persian DOCX files: six Faiz al-Bari volumes, two Mukhtasar Sahih Muslim volumes, and the Heravi Riyadh al-Salihin edition. The owner explicitly stated that these imports need no QC tags and that Persian side comments must be removed, retaining hadiths only. These instructions are scoped to the nine `materials/fa-*/manifest.json` registrations added by `scripts/import_persian_docx.py`.

Use the `owner_requested_public_source_import` publication decision and the explicit non-OCR `display_policy.qc_tags=false` policy. Do not add review/QC tags to their reader or search presentation. This display choice makes no independent certification assertion. Named translators printed in the source editions support the Human classification; no new translations were produced. Preserve source citations, grades, headings, local numbering, source defects and missing fields as metadata. Keep narration quotations extracted from notes distinct from complete numbered source occurrences and Companion statements. Do not deduplicate source occurrences or manufacture missing text. Keep removed commentary, original glyphs and extraction evidence outside the hadith/search payload. Preserve exact original DOCX files and the compressed source audits. Rights remain unassessed.

## Owner-authorized Persian Targhib and Tarhib volumes

On 11 November 2026 the owner requested adding the three supplied `targheeb-va-tarheeb-saheeh-va-zaeef-{1,2,3}-Word.docx` volumes to the Persian bank, retaining hadiths only, excluding commentary, and flagging ideological insertions. This authorization covers the three `materials/fa-targhib-bazmandegan-v*/manifest.json` registrations and their exact source documents and extraction evidence.

Preserve the source's differently graded narrations, distinct occurrences, numbered variants and explicitly identified Companion reports. Label partial quotations as excerpts and relate fragments of the same source report. Keep editor/compiler discussions, doctrinal polemics, lexical explanations, and independent non-hadith sayings outside the narration/search payload. Bounded actual narration quotations within such discussions may be registered separately with precise spans. Preserve every removed span and its reason in `imports/persian-targhib-20261111/`; original DOCX bytes remain unchanged.

Keep the edition's three numbering systems distinct from canonical collection numbers. Preserve the exact source assessment and name its individual grader only where explicitly supported; the title-page takhrij credit is separate. Retain source translation defects, absent or unresolved language alignments, and punctuation/font anomalies without synthesizing corrections. The OCR-only display policy applies to this native OOXML import; no new translation, independent Pro certification, or rights clearance is asserted.

## Owner-authorized Chinese Sunan Ibn Majah PDF import

On 11 November 2026 the owner explicitly requested adding the supplied `736950612-1.pdf` to the Chinese bank, extracting from the PDF and consulting the TXT only for uncertainty, uploading the original PDF, and showing the Chinese title before the English title. This authorizes public repository and reader inclusion of `materials/zh-cn-ibn-majah-yu-2013/`, its 4,354 numbered source occurrences and original PDF, under the manifest's `owner_requested_public_pending_review` decision.

The title is 伊本·马哲圣训集 — Sunan Ibn Majah, translated by 穆萨·余崇仁, 2013 edition. Preserve chapter-local numbering separately from unknown canonical global references. Keep exact original source bytes, raw extraction, separate footnotes/headings and before/after correction evidence. No new translation is produced, and no publisher license or full independent Pro QC is asserted. See `docs/CHINESE-IBN-MAJAH.md` and the source-specific audit.

The owner subsequently stated on 11 November 2026: "we got it from a book outsoruce so no need for ocr". Do not perform additional OCR work for this import. Apply the manifest's `owner_requested_no_qc_tags_for_published_book` display decision to this identified material and original PDF hash only: omit its OCR/QC badges and its contribution to the pending-review banner. The supplied PDF's existing ABBYY OCR evidence, original review status and correction history remain unchanged; this display choice does not assert that no OCR was used or that independent certification passed.

## Owner-authorized Chinese Hisn al-Muslim final delivery

On 12 November 2026 the owner explicitly requested uploading the Chinese Hisn final delivery into the bank, integrating it into HTML, and adding its original PDF to the material sources after being shown Chinese transcription PASS, overall PARTIAL and bank-readiness FAIL. This authorizes the identified `materials/zh-cn-hisn-muslim-1a09ee75/` registration and exact originals under `imports/chinese-hisn-final-20261110/`. It is a pending-review publication decision; preserve the historical evaluation and `certified_release_eligible=false`.

Keep all 279 original records byte-identical in the delivery. Only source-bound hadith quotations and attributed Prophetic prayers, dhikr and reports enter the registered reader subset. Store non-hadith source items and unresolved classifications separately outside Hadith HTML and search. Preserve the classification ledger, exact source spans and change history. Do not omit a report solely because it describes a practice or dhikr rather than quoted speech. Do not promote candidate Arabic, English, canonical mappings, chains or grades: this material's explicit counterpart hold takes precedence over automatic and reviewed matching until a new source-bound approval is recorded. The new-book Human translation policy applies without asserting authenticity or rights clearance. See `docs/CHINESE-HISN.md`.

## Owner-selected Uzbek sources

On 12 November 2026, after excluding Rivoyat, the owner selected
`https://hadis.islom.uz/` and `https://hadis.uz/hadiths/1` for Uzbek intake,
with the latter scoped to Sunan/Jami al-Tirmidhi. This authorizes the separate
`hadisuz-*` material registrations and `imports/web-hadisuz-20261112/` source
evidence. Preserve publisher attribution and any specifically supported
translator/edition credits, exact narration/comment boundaries and source-local
identifiers. Do not treat the numeric detail URL as a canonical hadith number
or assume a language text not supplied by this source. Follow only observed
ordinary public catalogue, pagination and detail routes; retain gaps and
access stops explicitly. The existing source-preservation, Human display and
non-OCR review-display policies apply without claiming independent certification.

## Owner-authorized Japanese research-v3 reader integration

On 12 November 2026, after the blocked-transfer handoff and the package's preserved HOLD status were explained, the owner explicitly instructed: "continue integration into html , tell me after finish previous count and new count of hadtihs". This authorizes the separately derived pending-review Japanese reader subset bound to `imports/japanese-research-v3-20261112/publication-decisions.json` and the exact original archive SHA-256 `331d2973511301c6cd50d3e2a8612e135defda529e855b8b03894490005c01fa`.

Keep the original archive, all 1,889 source records and their historical false display/release flags unchanged. The new visibility ledger selects 1,226 original source occurrence IDs: 1,147 whole-record selections and exact Prophetic excerpts from 79 mixed parents. Preserve all 122 child component IDs and boundaries within those parents; do not count formula fragments as additional source occurrences, and do not merge their separate reference or chain evidence. The 45 related external witnesses are reference links, not newly extracted source records.

Only the selected source fields/spans enter the four Japanese material registrations. Preserve non-hadith material, Quran context, unresolved classifications and complete mixed parents outside Hadith HTML/search. Dhikr, prayers and reports of the Prophet's actions remain eligible content; distinguish source summaries, biographies, kana renditions and context-qualified formula occurrences from exact direct quotations. Keep Hisn099 and translator-note051 Quran text outside their selected Prophetic excerpts.

Current visibility is `owner_requested_public_pending_review`; it does not change the original source/Arabic/semantic holds or perform the required separate exact-final-byte independent Pro evaluation. Keep `certified_release_eligible=false` and the material counterpart hold. Do not promote candidate Arabic/English, research witness numbers, editions, chains or grades into accepted canonical identity. Hisn's printed translator credits remain separate from the three exact PDFs with unestablished translator names. The new-book Human display policy applies without inventing translator identities. See `docs/JAPANESE-RESEARCH-V3.md`.

## Owner-authorized Filipino Hisn reconstructed source import

On 12 November 2026 the owner requested "integrate into the bank and the html" and then "integrate into html , dont keep as hold" for the reconstructed Filipino Hisn al-Muslim delivery. This authorizes active public source import of `materials/fil-hisn-muslim-3e409dd7/`, its original `FIL-HISN-PRIVATE.pdf`, and its reconstruction evidence under `imports/filipino-hisn-reconstructed-20261112/`. Apply `owner_requested_public_source_import`; do not impose a publication hold or present the current source import as a HOLD release.

Preserve the historical reconstructed delivery and its earlier HOLD assessment unchanged. The current publication decision does not claim that independent final evaluation was run or that source/metadata uncertainties were resolved. Keep the 298 hadith, narrated dhikr and coherent narration-context records available in HTML. Preserve the 14 independent non-Prophetic records, 6 Quran/author-only records and 5 unresolved-attribution records separately. Do not turn an entire mixed context record into a single exact Prophetic quotation. Retain supported narrator framing, dialogue, instructions, variants and hadith-bearing footnotes with their scope annotations; authenticity grading is separate from content classification.

Preserve exact source wording, all 323 source records and 1,500 components in the lossless source archive. Keep the source edition distinct from the older Filipino Hisn excerpts. Use the Arabic actually printed in this source; do not promote the reconstruction's external counterpart candidates or fabricate absent text, grades, chains, dates or canonical identities. Keep human translator attribution, OCR evidence, specific uncertainties and `independent_pro_qc=NOT_RUN` accurate. See `docs/FILIPINO-HISN.md` and the material's publication manifest.

## Owner-requested Urdu, Bengali and continued upstream recovery

On 12 November 2026 the owner explicitly requested Urdu and Bengali from
`https://github.com/fawazahmed0/hadith-api` and instructed continuing work on the
11,555 source occurrences held by the initial narrow import rules. This extends
the pinned seven-book intake to the Arabic, English, Urdu and Bengali editions
in `catalog/fawaz-bulk-plan.json`. Reuse verified saved whole editions; fetch
only missing editions and keep the source identities unchanged.

The pinned catalog also supplies Bengali Nawawi, alongside Arabic and English,
so this request includes those three editions as the eighth collection. There
is no Urdu Nawawi edition in that catalog: preserve that absence and do not
request a guessed edition. The catalog's shared `Imam Nawawi` author credit is
the collection compiler; retain it without labelling him a Bengali or English
translator. The configured scope is 31 edition files, including all seven Urdu
and all eight Bengali editions in the pinned catalog.

Review the whole held set in source-bound batches. Include explicit Prophetic
speech, acts, descriptions, practices, dhikr, dialogue and attributed abbreviated
transmissions when supported by the source. A missing section reference, an
introduction label, or a rule limited to literal speech is not itself a reason
to omit an otherwise established narration. Hash-bound reviewed excerpts may
separate a narration from surrounding Quran, compiler or narrator discussion.
Do not complete abbreviated wording or infer a canonical cross-edition identity.

Each language retains its own text boundaries, references and comments. If one
language's mixed narration/commentary cannot yet be separated, preserve its full
source text in that language's source-context comments, visibly explain the
pending boundary, and keep any independently supported other language readings.
Do not index that context as hadith matn or count it as supplied quotation text.
If the provider supplies different content under the same ID in different
languages, preserve that mismatch explicitly. Such a language's context is not
an Arabic/English counterpart or a translation of the displayed narration.
Preserve actual source-empty entries, independent sayings, compiler discussion
and unresolved attribution in the complete source/classification ledger outside
Hadith HTML. Account for every provider ID; a held source is not a failed or
missing download. The existing source fidelity, translation-origin, rights and
non-certification policies continue to apply.
