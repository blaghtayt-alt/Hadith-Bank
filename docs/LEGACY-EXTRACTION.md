# Individual hadiths from the legacy banks and Qur’an books

## Included source occurrences

This update indexes the bounded hadith quotations that were previously stored inside lessons, articles and Qur’an-study materials. The original 281 Japanese HadeethEnc records remain intact. Their count never represented all hadiths embedded in the old Japanese bank.

| Language | Legacy lessons and articles | Qur’an-study sources | Newly indexed | Complete public reader |
| --- | ---: | ---: | ---: | ---: |
| Japanese (`ja`) | 94 | 51 | 145 | 2,237 |
| Filipino (`fil`) | 66 | 41 | 107 | 2,056 |
| Vietnamese (`vi`) | 58 | 40 | 98 | 4,555 |
| Chinese (`zh-CN`) | 100 | 40 | 140 | 2,396 |
| Uzbek (`uz`) | 90 | 42 | 132 | 552 |
| Hindi (`hi`) | 227 | 43 | 270 | 2,584 |
| Persian (`fa`) | 232 | 41 | 273 | 273 |
| **Total** | **867** | **298** | **1,165** | **14,653** |

The original 13,488 structured imports remain unchanged. The new material has 109 language/collection manifests: 49 legacy groups and 60 Qur’an-book groups. Counts are source occurrences, including separately located excerpts, repeated appearances and distinct source versions; they are not unique canonical hadith counts. The 83 older document-level entries remain available and are not added to the narration count.

## Sources and exact boundaries

The Iman Companion source is pinned to commit `ae2c07599767ee7182c40d3ff2264fcdac98d182`. Previously archived Hadith Bank source documents retain their original revisions. Each new record retains its original path, Git blob identity, SHA-256, JSON pointer and exact Unicode character boundaries. Encoding the stored raw source strings as UTF-8 reproduces the original bytes.

Qur’an-study coverage includes Al-Fatihah, Al-Ikhlas, the Japanese Al-Qiyamah material, and the cited Japanese Qur’an-footnote occurrence. All 188 scoped Qur’an-study source files were hash-verified and preserved. The 66 Markdown/text files are accounted for through 59 actual mirror comparisons and seven separately inspected source notes. The comparison ledger checks 1,272 delimited quotations without leaving unaccounted Markdown quotation spans.

The complete source census accounts for 739 pinned Iman Companion files and all 83 archived bank documents. It explicitly excludes 56 TEST fixtures from narration counts. The 83 archived bank files comprise 53 byte-identical mirrors, four identical JSON documents with different serialization, and 26 text mirrors that differ only in layout whitespace.

Preserved source bundles make the bank and the two extraction scripts usable offline. Raw sources are never silently substituted by a newer repository revision, an external API, or a newly generated translation.

## Record types

| Type | Occurrences | Interpretation |
| --- | ---: | --- |
| `hadith` | 454 | The main source narration, without an added assertion that every canonical route or wording is complete. |
| `hadith_excerpt` | 595 | A bounded quotation that may contain only part of a narration. |
| `hadith_meaning_excerpt` | 100 | A passage explicitly presented by its source as the reported meaning. |
| `companion_report_excerpt` | 16 | A separately labeled report or words attributed to a Companion. |
| **Total** | **1,165** | **Source occurrences across the seven languages.** |

Qur’an verses, scholarly explanations, single-word glosses, proverbs and unbounded historical retellings are not promoted to hadith records. An author’s explanatory paraphrase is not presented as Prophetic speech. Discontinuous source quotations are kept as separate fragments rather than joined into a sentence the source never supplied.

## References and translation origin

Collection names, source-supplied numbers and variant scopes remain separate fields. **959 occurrences have a source-cited primary number; 206 do not.** The latter comprise 187 legacy records and 19 Qur’an-book records. A source citation is not independent verification of an edition’s canonical numbering. Unsupported canonical matches remain null, and unresolved attribution is retained in the record and report.

The legacy extraction includes 553 exactly source-linked Arabic fields, 34 explicit narrator names and six translator credits. Credit promotion uses the selected source parent’s scalar field and retains an exact evidence locator. The remaining names are not inferred from collection attributions or surrounding commentary. Source-linked Arabic does not certify alignment with a different Arabic edition.

Every new legacy/Qur’an-book record is **Unknown** for translation origin until the owner confirms it. This remains true when a translator’s name is supplied. Historical human/AI assertions stay preserved in source metadata; segmentation is not new translation. The existing 13,488 owner-confirmed HadeethEnc and website imports remain Human.

## OCR display and search behavior

The new records are structured digital quotation extractions with `ocr_used=false`. Their cards do not show OCR-QC badges, and they do not contribute to an OCR-pending banner. The same display rule applies to confirmed digital website text and native PDF text. Actual evidenced OCR retains its review labels. Original review fields and Arabic alignment notes remain available in record details.

Normal search covers quotation text, supplied narration metadata, collection references, translator and source bibliographic details. The commentary option additionally searches surrounding source context, explanations, benefits and footnotes. Historical source context does not silently enter a quotation-only search. Both HTML and the command-line search support the current Human/AI/Unknown categories.

Examples:

```bash
python scripts/hadith_search.py 'bukhari 2311' --language ja --translation-origin unknown
python scripts/hadith_search.py 'muslim 2654' --language ja --translation-origin unknown
python scripts/hadith_search.py --language fa --translation-origin unknown --limit 10
```

## Recovery audit

The recovered checkpoint contained 866 legacy records. The final extraction contains 867, including 13 narrations or reported meanings previously retained only inside displayed notes or a linked published glossary. Seven duplicate appearances from alternate representations of the same lesson were mapped to retained occurrence IDs. Five standalone lexical glosses were excluded. All 854 surviving Arabic and translated text values match the recovered checkpoint exactly.

The displayed-note audit records 493 exact source locations across 43 documents, including the 13 newly indexed quotations and the summaries, lexical notes and metadata intentionally retained as context.

`reports/legacy-extraction-recovery.json` retains the previous record-file hashes, every removed record in full, its exclusion or retained-ID mapping, and the before/after metadata changes. No previous source text was discarded to manufacture a clean result. The corrected extractor also repairs 32 Hindi Arabic locators so they identify exact scalar source fields rather than a surrounding list.

## Reproduce and verify

From a complete checkout:

```bash
python scripts/extract_legacy_hadith.py --root .
python scripts/extract_quran_hadith.py --root .
python scripts/audit_embedded_source_inventory.py --root .
python scripts/refresh_bank.py --root . --site-output _site
python -m unittest discover -s tests
```

The extraction scripts recover the frozen sources from checked-in bundles when no acquisition cache is supplied. The refresh step validates registrations and source hashes, rebuilds every search shard and reading page, embeds the full records in the HTML, and validates exact object equality against the authorized source projections.

The checks distinguish source-byte fidelity, extraction boundaries, searchable metadata and display policy. They do not assert a new independent theological, linguistic, authenticity or grading certification.

## Evidence files

- [Legacy extraction and per-quotation decisions](../reports/legacy-extraction-audit.json)
- [Recovered-checkpoint correction history](../reports/legacy-extraction-recovery.json)
- [Qur’an extraction, all-source coverage and mirror comparisons](../reports/quran-hadith-extraction.json)
- [Displayed-note and glossary coverage](../reports/displayed-note-coverage.json)
- [Complete source inventory](../reports/embedded-source-inventory.json)
- [Portable bank validation](../reports/portable-validation.json)
- [Current generated website build](../reports/site-build.json)
- [Current source-origin policy](../catalog/provenance-policy.json)
- [OCR-only display policy](../catalog/review-policy.json)
