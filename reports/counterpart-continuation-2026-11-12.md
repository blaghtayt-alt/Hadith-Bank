# Arabic and English counterpart continuation — 12 November 2026

This continuation starts from public commit `9f1433a6e534d7195f6a6524847cff1f7cf2de52`. The interrupted session's exact unpublished 305-mapping files could not be recovered from the available workspace, repository or saved files. Its stated additions are not counted as publication evidence. The present batch contains fresh, source-bound decisions made from the bank's preserved canonical records and publisher snapshots.

## Actual availability changes

The regenerated bank adds Arabic text to **155** existing source occurrences and English text to **248** existing source occurrences. Five exact English source versions are withheld from 21 previously available occurrences because of specific source-content discrepancies. The net English increase is therefore **227**. The original **36,950 source occurrences** remain unchanged.

| Availability measure | Before | After | Change |
| --- | ---: | ---: | ---: |
| Arabic text | 25,787 | 25,942 | +155 |
| English text | 9,342 | 9,569 | +227 net |
| English external-link only | 2,677 | 2,677 | 0 |
| English text or external source link | 12,019 | 12,246 | +227 net |
| Missing Arabic | 11,163 | 11,008 | −155 |
| Neither English text nor an English source link | 24,931 | 24,704 | −227 |

English text is still absent from 27,381 occurrences, including the 2,677 occurrences that have only an external English link. This continuation does not claim complete Arabic/English coverage of the bank.

| Source language | Arabic text added | English text added | Existing English withheld | Net English change |
| --- | ---: | ---: | ---: | ---: |
| Persian | 0 | 77 | 0 | +77 |
| Filipino | 0 | 1 | 5 | −4 |
| Hindi | 0 | 3 | 5 | −2 |
| Japanese | 17 | 20 | 2 | +18 |
| Uzbek | 0 | 4 | 2 | +2 |
| Vietnamese | 85 | 85 | 2 | +83 |
| Chinese | 53 | 58 | 5 | +53 |
| **Total** | **155** | **248** | **21** | **+227** |

The [machine-readable validation](counterpart-continuation-2026-11-12/validation.json) and [occurrence-level changes](counterpart-continuation-2026-11-12/availability-changes.json.gz) bind these totals to the baseline and regenerated records.

## Reviewed scope

| Source language | Occurrences with a recorded decision | Approved mappings | Arabic approvals | English approvals | Unresolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| Persian | 91 | 77 | 77 | 75 | 14 |
| Chinese | 104 | 59 | 59 | 58 | 45 |
| Japanese | 31 | 18 | 18 | 18 | 13 |
| Vietnamese | 97 | 85 | 85 | 84 | 12 |
| **Total** | **323** | **239** | **239** | **235** | **84** |

These are occurrence-level alignment decisions, not unique canonical hadith totals or availability gains. All 77 Persian approvals already had original Arabic. The Chinese reviewer screened 106 candidate pairs for 104 occurrences and read 95 full Chinese/Arabic/English triplets; early rejections did not constitute full triplet review. The Persian and Japanese/Vietnamese reviews compared 91 and 128 complete source/target cases respectively. No original PDF pages were re-OCRed or newly certified.

The Chinese approvals include 50 Sunan Ibn Majah occurrences, one Muwatta occurrence, six legacy quotations and two Quran-study quotations. Source-local chapter numbering and edition identities remain unchanged. Unknown original grades, numbers and uncertain classifications remain unknown. An unresolved manual decision grants no accepted counterpart. The 84 unresolved entries describe the review bundles' decisions; two Japanese occurrences subsequently receive counterparts through independently supported suffix matching, as recorded in the validation file.

## Number suffixes

The [suffix audit](counterpart-suffix-audit-2026-11-12.json) records 14 baseline occurrences whose substantial Arabic quotations match a unique publisher entry but whose source citations have a suffix absent from the publisher bibliography. Both number forms are preserved. Thirty translation-only suggestions were not automatically accepted by this exception. One Chinese case also appears in a manual bundle and is counted only once in the final availability comparison. The union is 252 source occurrences supported by the new manual mappings or the suffix exception; this is distinct from newly available text counts.

## English content decisions

The exact-version [quality policy](../catalog/counterpart-quality-policy.json) keeps translation origin separate from translation fidelity. Newly identified wording problems are withheld by publisher ID and exact English text hash. Original Arabic, original translations, raw source exports, numbering, IDs and review history remain preserved.

English sources that cover only a bounded part of a longer Arabic narration remain available with explicit partial-coverage notes. The display does not imply that their English covers omitted clauses.

| Publisher entry | Previously available occurrences withheld | Specific discrepancy in the pinned English version |
| --- | ---: | --- |
| HadeethEnc 5461 | 3 | The conversion/martyrdom sentence loses the killer as its explicit subject and grammatically attaches the later actions to Allah. |
| HadeethEnc 5937 | 3 | Distress at the return is rendered as a change of heart, altering that distinct supplication clause. |
| HadeethEnc 5986 | 6 | Believing the soothsayer is added as a condition absent from the paired Arabic narration. |
| HadeethEnc 6380 | 3 | Donkeys become monkeys, and the camel/cow milk-quantity associations are swapped. |
| HadeethEnc 65045 | 6 | Being among the most knowledgeable is rendered as the single most knowledgeable. |
| **Total** | **21** | |

These are exact-text-hash decisions, not permanent exclusions of a provider or an entire hadith. The earlier HadeethEnc 65015 decision remains unchanged. The pinned English versions for 4952 and 64646 retain their original bytes and receive partial-coverage qualifications across five and three current occurrences respectively. Translation origin remains Human under the existing owner policy; origin and textual fidelity are separate attributes.

## Reproducible evidence

- [Persian review audit](counterpart-continuation-2026-11-12/fa-review-audit.json.gz)
- [Chinese review audit](counterpart-continuation-2026-11-12/zh-review-audit.json.gz)
- [Japanese and Vietnamese review audit](counterpart-continuation-2026-11-12/ja-vi-review-audit.json.gz)
- [Independent suffix-code review](counterpart-continuation-2026-11-12/suffix-code-review.json)
- [Independent partial-policy code review](counterpart-continuation-2026-11-12/partial-policy-code-review.json)
- [Reviewed source registry](../sources/counterparts/reviewed/manifest.json), containing exact source and target hashes, immutable review decisions, source bindings and per-language scope qualifications.
- [Current availability by language and source](counterpart-availability.md).

Alignment review was performed by automated assistants. Human review, independent Pro certification, narrational authenticity certification and new redistribution rights are not asserted. No new translations were generated.

## Verification status

All **400 software tests passed**, including the suffix-evidence safeguards and hash-bound partial-coverage policy. The full rebuild and portable validation passed, generating 36,950 individual narration pages and 594 discovery indexes for seven languages. A separate comparison confirms the exact same occurrence IDs and canonical source text, numbering, translation-origin and review hashes as the baseline. Original documents and publisher exports have no changes.

The [local generated-page checks](counterpart-continuation-2026-11-12/local-generated-qa.json) passed 11 checks: the complete embedded reader stream, four selected-export payload records, eight representative narration pages and discovery totals. The representative pages cover new Persian, Chinese, Japanese and Vietnamese counterparts, two partial English versions and two held English versions. Four rendered original PDF/DOCX links resolve to the exact preserved local source paths and hashes.

Local Chromium could not launch because its process-singleton socket was denied by the environment. No local browser page loaded, and the static checks are not reported as browser interactions or visual checks. Interactive search, display toggles and export are checked in the live cloud browser after deployment. The publication receipt separately records the actual source commit, generated commit, deployment and live-site results.
