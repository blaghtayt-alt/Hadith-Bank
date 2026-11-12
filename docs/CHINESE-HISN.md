# 穆斯林的堡垒 — Hisn al-Muslim

The owner authorized public inclusion of this Chinese final delivery and its original PDF on 12 November 2026. All 279 source records remain in the unchanged delivery. The reader uses only the selected hadith quotations and attributed Prophetic prayers, dhikr and reports, with exact source spans and stable original IDs. The [integration audit](../materials/zh-cn-hisn-muslim-1a09ee75/integration-audit.json) and [material manifest](../materials/zh-cn-hisn-muslim-1a09ee75/manifest.json) record the current partition counts.

## Read and download

- [Chinese Hisn reading pages](https://blaghtayt-alt.github.io/Hadith-Bank/browse/zh-CN/hisn-al-muslim/)
- [Original Chinese PDF](https://github.com/blaghtayt-alt/Hadith-Bank/raw/main/materials/zh-cn-hisn-muslim-1a09ee75/zh-hisn.pdf)
- [Final JSON](../imports/chinese-hisn-final-20261110/zh_hisn_final_corrected.json), [JSONL](../imports/chinese-hisn-final-20261110/zh_hisn_final_corrected.jsonl) and [CSV](../imports/chinese-hisn-final-20261110/zh_hisn_final_corrected.csv)
- [Page data](../imports/chinese-hisn-final-20261110/zh_hisn_final_pages.jsonl) and [source metadata](../imports/chinese-hisn-final-20261110/zh_hisn_final_metadata.json)
- [Final evaluation report](../imports/chinese-hisn-final-20261110/FINAL_EVALUATION_REPORT_JA.txt) and [delivery receipt](../imports/chinese-hisn-final-20261110/zh_hisn_final_delivery_receipt.json)
- [Independent artifact review](../imports/chinese-hisn-final-20261110/independent_final_artifact_review.json), [historical release gate](../imports/chinese-hisn-final-20261110/RELEASE_GATE.json) and [original review-package checksums](../imports/chinese-hisn-final-20261110/SHA256SUMS.txt)
- [Repository delivery manifest](../imports/chinese-hisn-final-20261110/TRANSFER_MANIFEST.json), with the exact byte counts and hashes of every preserved standalone original

The seven requested standalone delivery files and the original PDF are stored directly, alongside three supplied evaluation-evidence files. The full evaluation ZIP is not mirrored here or required by the reader build. The original review-package checksums and delivery receipt remain byte-identical; they describe the larger prior evaluation package and can name evidence that is not part of this standalone repository delivery. The repository delivery manifest identifies exactly what is available here.

The PDF is the original 52-page file, SHA-256 `1a09ee75c544d3ced4ac287bd9c996aec9e508f7c98c0965b5e3744131c2cfd4`. The final JSON has SHA-256 `0c000f5f5cfac6ba52bd8339b205bcdd775f952ace81bc261930960fda8f38d5`. No new OCR or translation was performed for this integration. The supplied file formats and original bytes are retained; a new Word edition has not been manufactured.

## Source fidelity and unresolved research

The original final evaluation records Chinese source-transcription **PASS**, overall **PARTIAL** and bank-readiness **FAIL**. Its review covered all 52 source pages and 279 records. Public inclusion follows the owner's later instruction and does not change those historical findings or claim new independent Pro certification.

Unapproved Arabic and reference enrichments remain available in the archived evidence. They do not become displayed Arabic/English counterparts, verified canonical numbers, narrator chains or accepted grades. A material-specific counterpart hold blocks both automatic and reviewed matching. New source-bound approval is required before enabling a counterpart. The Chinese text is shown under the current new-book **Human** translation policy; translation origin is separate from source or authenticity review.

## Record boundaries and separate archives

The [classification ledger](../imports/chinese-hisn-final-20261110/classification/decisions.json) binds each decision to its original record ID and Chinese text hashes. Every retained character is tied to an exact span in `body_text_verbatim`. Any display separator between discontinuous spans is explicitly recorded, and excluded commentary is retained in [the excluded-span ledger](../imports/chinese-hisn-final-20261110/classification/excluded_segments.json).

Non-hadith material is preserved in [its separate folder](../non-hadith/zh-cn-hisn-muslim-1a09ee75/); unresolved classifications are preserved in [the unclassified folder](../unclassified/zh-cn-hisn-muslim-1a09ee75/). Neither folder is registered as a hadith material or included in Hadith HTML/search. Qur'an passages, reference-only records and editorial explanations must not be reclassified merely to increase the displayed count. Equally, source-attributed Prophetic practices, prayers and dhikr are eligible hadith reports; they are not excluded simply because their form is an instruction or supplication.

The current partition is **251 hadith records, 23 non-hadith records and 5 unresolved records**. The retained Prophetic-practice summaries are labelled **Reported meaning** in the reader. Their wording remains the compiler's source summary, with that qualification preserved; they are not relabelled as direct quotations. The earlier classification and the change log remain in the classification folder.

`scripts/import_chinese_hisn.py` reproduces the canonical selected records and manifests from the preserved delivery and hash-bound classification ledger. The regular `scripts/refresh_bank.py` workflow then discovers the registration, rebuilds the catalog and HTML, and links each record to the preserved source PDF. Exact delivery bytes, rights qualifications and unresolved metadata remain unchanged.
