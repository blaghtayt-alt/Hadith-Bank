# Hadith Bank active-books audit — 14 November 2026

**Result:** Japanese Fadael is registered and included in a verified deployment. Four major OCR projects have newer saved checkpoints but no corresponding Bank registration at the audited revision. Eight other tracker-listed book packages are also unregistered; their latest primary checkpoints were not accessible for a current-status check. Two older Portuguese reports were also located and retain their stated review limitations; neither source package is registered. Website intake is continuing, and historical held counts must not be reused as current pending totals.

This is an audit of saved checkpoint evidence, repository registrations and publication records. It did **not** perform new image-to-text proofreading, translation, authenticity assessment or corpus ingestion. The [machine-readable companion](ACTIVE-BOOKS-AUDIT-2026-11-14.json) records denominators, evidence filenames, hashes, unknown fields and source revisions.

## Snapshot and counting rules

The canonical source snapshot is [0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a](https://github.com/blaghtayt-alt/Hadith-Bank/commit/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a), committed **14 November 2026 at 02:31:23 JST**. The generated catalog at that revision was built from [3e574b9e7e4dd7cf8bc23232249004a18692c61c](https://github.com/blaghtayt-alt/Hadith-Bank/commit/3e574b9e7e4dd7cf8bc23232249004a18692c61c) and contains **101,040 source occurrences in 11 primary-language categories**. Its successful [workflow run 43467374230](https://github.com/blaghtayt-alt/Hadith-Bank/actions/runs/43467374230) completed deployment at **02:18:27 JST**. The job record includes successful software checks, Chromium reader verification and deployment. These observations establish that snapshot; they do not claim that every newer canonical import was already live.

The source counts are not unique canonical hadith totals. Repeated source occurrences, editions, variants, explicitly classified reports and excerpts retain their identities. Primary-language buckets do not count every secondary-language field inside multilingual records. A saved archive, an integration check, a registered material and a successful deployment are separate milestones.

Evidence: [generated build report](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/reports/site-build.json), [readable-record counts](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/browse/README.md), [registered-material catalog](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/catalog/registered-materials.json). The exact source manifests were inspected separately from the generated catalog, which can lag current imports.

## Active and recently completed book packages

| Source package | Latest inspected checkpoint | Progress reported by that checkpoint | Bank status at audit revision | Remaining stage |
| --- | --- | --- | --- | --- |
| Japanese Kitab al-Fada’il — 諸々の徳（ハディース集）② | Corrected editorial edition / QC v1 | 25 pages, 621 units, 57 occurrences and 58 notes; all source pages checked in the documented scope | Registered and included in the verified deployment | Retain editorial, source-reference and certification limits |
| Bengali Riyadh al-Salihin | `v2_cp017_patch08`, saved 13 Nov, 16:40 JST | 2,054 pages attempted; 2,053 full cumulative character reviews; one investigated glyph partial; 2,029 occurrence records and 11,484 source units | Not registered | Package-aware adapter, exact source/context mapping and reader validation |
| Hindi Mukhtasar Sahih Bukhari, three volumes | `v0.7.10_QC10`, saved 14 Nov, 02:29 JST | Scoped original-image comparison on all 1,921 pages and all 2,230 numbered bilingual bodies; 4,460 language rows | Not registered | Localized source uncertainties, independent proofreading and destination-specific preparation |
| Urdu Mishkat al-Masabih, five volumes / UM172207 | `v0.14.0`, saved 13 Nov, 19:16 JST | Initial text on 2,790 pages; 1,874 image drafts; 683 separate-author model comparison attempts; 1,514 occurrence fragments | Not registered | 2,107 pages without a comparison, including 916 undrafted pages; exact verification and entry preparation |
| Urdu Al-Adab al-Mufrad | `v0.2.0-pre.18`, saved 13 Nov, 19:46 JST | 372 complete-page comparison attempts plus 28 focused follow-ups; 26 current full-character self-review passes; 1,551 occurrence candidates | Not registered | 346 complete-page character reviews, localized tasks and independent source QC |

The four absent registrations were checked by source identity in the canonical material directories and generated registry. Existing Fawaz Urdu/Bengali fields, Deen Hindi records and Japanese Mishkat excerpts are different sources. They do not establish import of these packages. The five-volume Urdu project is **the same UM172207 Mishkat project**, not a sixth book. **HI_MSB is Mukhtasar Sahih Bukhari**, the Zubaydi abridgment, not Mishkat or the complete Bukhari corpus.

### Japanese Fadael: publication and duplicate presentation

The registered material is `ja-fadael-2-tuwaijri-1438-qc-v1`. All **57 source occurrences** retain their IDs and original/corrected wording. All 57 join existing reviewed reader groups, adding **zero ungrouped reading cards**. This is reviewed presentation grouping; source records were not deleted or merged. The generated Japanese total is **3,520 source occurrences** in the verified snapshot.

The display-origin result is **55 Human readings and two readings with explicit AI-assisted revised/restored clauses**, occurrences 47 and 50. Historical source-origin flags remain separate. Four secondary edition references remain unverified. `certified_release_eligible=false`; the documented line-by-line source checks are not an independent final codepoint certification. The source archive preserves all 621 units and 58 notes; translator-commentary note 19 remains outside narration counts.

Evidence: [material manifest](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/materials/ja-fadael-2-tuwaijri-1438-qc-v1/manifest.json) and [import, grouping and QC scope](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/docs/JAPANESE-FADAEL-QC.md).

### Bengali Riyadh: review completion does not supply a Bank adapter

The checkpoint reports **2,053 fully character-reviewed pages and one investigated localized partial**, V1 PDF962. Its ornate honorific glyph is preserved; an exact fully vocalized Unicode expansion is not established. The **32 semantic source limitations** were investigated and retained, not silently closed. Source wording and original codepoints remain unchanged.

Scoped independent character QC inspected **13 complete pages and 14 localized target pages**; these are scope categories, not an asserted disjoint sum. Semantic QC inspected targeted passages on **97 original pages** and produced **63 additive interpretation corrections**. Neither reviewer claimed an independent reread of all 2,054 pages. The 2,029 occurrences and 11,484 source units are preserved research structures, not already accepted Bank narration records.

The saved preflight checked the actual Bank schema. A simple field rename is insufficient: mixed source aggregates need the current semantic partitions to place narration, Quran quotations, commentary, notes and references in their correct fields. The next concrete deliverable is a package-aware adapter with preservation, ID, boundary and generated-reader validation.

### Hindi Bukhari: the scoped comparison reaches the end

The final comparison covers all **638 + 643 + 640 = 1,921 pages**, including all Arabic and Hindi page fragments for numbered bodies 1–2,230. The checkpoint records **2,223 cumulative correction instructions** and a passing independent integration/archive audit. It explicitly reports **zero fully glyph-verified pages and zero certified verbatim records**. Localized source uncertainties and independent professional proofreading remain. No remaining source page lies outside that scoped comparison pass, but full word/diacritic certification is not claimed.

### Urdu Mishkat: overlapping remaining-work counts

The **2,107 pages without a separate-author comparison** consist of **916 undrafted pages + 1,191 drafted pages without comparison**. Those components must not be added again to the 2,107 total. These separate-author reviews were performed by model workers; human or professional editorial QC is not claimed. A comparison attempt is not an exact-character pass: the checkpoint records **zero exact-character verified pages and zero independent-QC passed pages**.

Its **1,514 occurrence fragments** include **460 incomplete boundaries** and remain uncertified. The next work includes Arabic/Urdu correspondence, commentary/note separation and printed-source references. `bank_ready=false`; the checkpoint itself has not checked the live importer. The 200 new draft pages plus 100 comparisons in v0.14 are different work types, not 300 newly transcribed pages.

### Urdu Adab: use the current pass count

The checkpoint records **400 review events on 372 physical pages**, including 28 follow-ups. Its current full-character self-review count is **26**, superseding the prior 53: **53 − 44 reopened + 17 newly passed = 26**. There are **346 pending complete-page character reviews** and **zero independent source-QC passes**.

The **2,777 pending tasks** contain overlapping page, source, metadata and record concerns. They are not counts of missing words or hadiths. The **1,551 candidates** comprise 1,429 body and 122 frontmatter candidates; none is counted as a certified distinct hadith by this audit.

## Other tracker-listed books

These eight rows are **historical reported progress only**, from checkpoints inspected on **13 November 2026 at 10:43 JST** in `Hadith Extraction Progress.txt`. Latest primary checkpoint filenames, hashes and bytes were not available for independent current-state reconciliation. No subsequent inactivity is inferred. No source-specific registration for these eight packages was found at the audited Bank revision; similarly named old quotations or Fawaz editions are separate identities.

| Book | Historical checkpoint label | Historical reported progress | Qualification / remaining work at that snapshot |
| --- | --- | --- | --- |
| Hindi 300 Hadith | Provisional checkpoint | 300 provisional entries; zero complete Arabic/Hindi entries accepted | Complete bilingual acceptance and independent review remained |
| Hindi Selected Hadith Encyclopedia | `v087` | 370 pages initially inspected; zero fully audited; 33 body-text-only pages covering 251 occurrences | Earlier visual-comparison labels were not full-character passes |
| Hindi Hisn al-Muslim | Draft mapping checkpoint | 132 chapters mapped; 227-page edition | Substantial text/components remained untranscribed |
| Bengali Qudsi Hadith | `v006` | 14 complete visible-text pages, 19 partial and 161 not started, out of 194 | 180 pages not complete; current execution state is unknown |
| Bengali Hisn al-Muslim | `v135` | Raw segmentation on 457 pages; 209 extractor full-character comparisons; 248 partial | Prior completion counts had been reopened after uncertainties |
| Bengali Selected Hadith series, five volumes | `v086` | 340 of 997 pages had extractor comparison; volumes 1–3 had none completed | 657 pages lacked completed comparison; 14 Quran Unicode readings open |
| Urdu Diya-e-Nabawi Nawawi Forty | `v189` | First-pass comparison on 100 of 314 pages; 1,196 matched records reported | First-pass matches are not 1,196 certified hadiths |
| Urdu Hisn al-Muslim | `v093` | Zero fully compared pages of a provisional 173-page edition; 246 limited comparisons and 204 anchors | Fullest-edition selection remained unresolved |

All eight historical rows reported **independent review not run**. The captured tracker corresponds to an older site version; a newer saved version 12 failed deployment, while version 11 has a successful deployment record. The current live tracker body and current local-master checkpoint bytes were not inspected. Saved site versions and successful deployment records therefore do not supply fresh book counts for this table.

## Older Portuguese backlog

The parallel README update retained two earlier Portuguese source projects. This audit read their latest small reports located, dated **9 November and 11 November 2026 JST**. Their report dates are preserved; no later continuation is inferred. No Portuguese source-specific material registration was found in the audited material tree or generated registry.

| Source | Latest located report | Historical reported work | Remaining limits |
| --- | --- | --- | --- |
| Portuguese Sahih al-Bukhari, volume I | `pt_bukhari_v1_coverage_report.txt`, saved 9 Nov, 20:28 JST | Extraction and image inspection of all 914 pages; 2,970 report rows: 2,671 numbered occurrences + 299 unnumbered reports/quotations. Three independent reviewers and passing mechanical checks are reported. | The index on PDF831–911 was not fully character-proofread. Complete Arabic hadith text is absent in this source. Scholarly authenticity and external-edition review were not performed. This volume-I scope does not establish completion of volumes II/III. |
| Portuguese Riyadh al-Salihin, SBMRJ | `pt_riyadh_sbmrj_review_report_pro_qc_v2.txt`, saved 11 Nov, 01:10 JST | 821 pages and 1,869 occurrences preserved; inherited comparison logs cover 3,969 contributing language/page portions. | Exact accuracy, source fidelity and metadata are PARTIAL; Bank readiness is FAIL. Full character/diacritic, paragraph, ancillary-quotation, canonical/chain and bilingual-alignment work remains. 105 prior metadata conflicts still lacked external research. A fresh independent final evaluation of the exact v2 package is required by the saved report. |

These are read report claims, not newly performed image reviews or recomputed corpus checksums. The Riyadh report identifies candidate JSON SHA-256 `1cc3e65e8d4e6cee5de9919f3f555bf7c861866a871704fdc2334e7d0929780e`; this audit did not rehash the candidate. No missing Arabic or source placeholders are filled from another edition.

## Website intake and held-source reconciliation

These counts belong to the **canonical source revision 0d2fa4ebacd1**, not an asserted current live website total.

| Intake | Preserved source entries | Registered occurrences | Pending classification | Other source-only dispositions | Acquisition status |
| --- | ---: | ---: | ---: | --- | --- |
| Deen Hindi | 17,627 of 36,390 | 17,301 | 166 | 160 non-narration entries | 18,763 source pages remain; zero current errors; all 1,000 historical error identities resolved |
| Hadis.islom.uz | 8,625 | 8,622 | 0 | 5 non-narration parents | One failed section remains; zero ordinary pending tasks is not a completed fetch queue |
| Hadis.uz — selected Tirmidhi intake | 607 | 606 | 0 | 1 non-narration entry | Observed queue complete; complete publisher/content coverage is not certified |
| Fawaz configured scope | 36,464 provider identities; 31 edition files acquired | 36,226 | 0 unresolved held identities | 238 resolved dispositions: 67 commentary/explanation + 171 source gaps | No configured edition remains unfetched; sibling-language semantic review is separate |
| Rivoyat | 0 | 0 | 0 | Owner-excluded | Disabled; do not automatically reacquire |

Islom's occurrence accounting is **8,625 − 5 + 2 = 8,622** because two quotation occurrences, containing three bounded passages, are separately registered. It is not a simple subset count of original source entries. Deen Hindi's preservation accounting is **17,301 + 166 + 160 = 17,627**, and **17,627 + 18,763 = 36,390**.

Fawaz's earlier 244-source-only cohort has completed disposition review: **6 recovered reports + 238 resolved source-only dispositions**. `held_occurrences=238` is retained historical/schema terminology; `unresolved_held_occurrences=0` distinguishes it from pending review. The old 6,553 / 4,946 / 1,607 recovery figures are historical, not a current queue.

**Separate sibling-language semantic review remains. Its current remaining-field count was not revalidated.** The latest quantified historical cohort report located records 6,112 fields (Arabic 2,099; Urdu 1,866; Bengali 2,147), but its expected state was 36,220 registered / 244 source-only, preceding the current 36,226 / 238. This audit deliberately records the current field count as unknown. Acquisition of all edition files and completion of provider-ID disposition review do not certify every admitted language boundary.

Evidence: [website intake status](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/imports/web-import-status.json), [Fawaz current progress](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/imports/web-fawaz-20261112/progress.json), [Fawaz dispositions](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/reports/fawaz-held-resolution-20261113/README.md), and [historical sibling-language review scope](https://github.com/blaghtayt-alt/Hadith-Bank/blob/0d2fa4ebacd15e1faa70ec865694ad4dc7f7c31a/reports/fawaz-import-review/continuation-20261113/fresh-reviews/cohort-review-summary.json).

## README and reader-description corrections

The README now lists the **11 accepted languages**, includes active book checkpoint status, excludes Rivoyat from active intake, and distinguishes source commits from generated/deployed counts. Newly documented example editions include Fawaz, Japanese Fadael, Chinese Ibn Majah and the reconstructed Filipino Hisn.

The verified hosted reader is **not self-contained**: the build report records `gzip-jsonl-lazy-v2`, **1,313,824 HTML bytes** and **1,363 companion data shards totaling 264,760,510 bytes**. Downloading the hosted HTML alone does not preserve the corpus. [Website and offline-use instructions](../docs/WEBSITE.md#offline-use) now explain the matching local data directory, local HTTP serving and the separately supported embedded standalone build. The reader hides its offline-download control when no separate standalone URL is configured. No new full-corpus standalone build was produced by this documentation audit.

## Evidence and limits

The JSON companion stores exact remote source paths, revision-bound URLs and SHA-256 values recomputed from the small files read for this audit. Saved off-repository checkpoint report identifiers are:

| Project | Exact saved report | Declared report SHA-256 |
| --- | --- | --- |
| Bengali Riyadh | `bn_riyadh_20261113_v2_cp017_patch08/REPORT.md` | `b950e2c75370a5269620ed3f043ecb57537204b6363a5daf02b953591f29e1da` |
| Hindi Bukhari | `HI_MSB_3V_v0.7.10_QC10_STATUS_EN.txt` | `83bae1d4cdd70c81443f4c258c36f3f32b3e21982a9d34b44207717087e06eb7` |
| Urdu Mishkat | `UR_MISHKAT_172207_v0.14.0_COVERAGE.json` | `22c1d27a5bb1a700cd022924b4288979a19a6f73814a8bae281a79926bef5416` |
| Urdu Adab | `UR_ADAB_MUFRAD_20261113_v0.2.0-pre.18_CHECKPOINT_PROGRESS.txt` | `8425d1f0d4a4fd094ad0c3065386c5be2626dce071cca347227d02b9006d6fd1` |

These four report hashes were **read from their saved checksum/manifest reports**. Their large archives were not downloaded or rehashed during this audit. Off-repository source bytes are not added by this documentation change. Those saved reports establish their reported checkpoint progress; they are not substitute evidence for freshly performed proofreading.

The practical next steps are to implement the Bengali package-aware adapter, complete the remaining source-review work in the Hindi and Urdu projects, refresh the eight local-master checkpoints, and continue the separate acquisition and semantic-review queues with dated evidence. A later import or review should update this audit with its actual revision and review scope, rather than silently reinterpret this dated snapshot.
