# Fawaz: complete disposition review of the 244 held entries

This checkpoint reviews every source field for the 244 provider occurrences that were outside the narration reader at repository commit `7b22548d43bccce94cce0e04d734e47458460fac`. The source remains `fawazahmed0/hadith-api` revision `df57907be35291c91ad6a6691180e22ca9920784`.

## Decisions

| Outcome | Provider occurrences |
| --- | ---: |
| Recovered as their actual attributed report or saying | 6 |
| All supplied language text fields empty | 169 |
| Explanations and commentary | 66 |
| Quran quotation within legal explanation | 1 |
| Explicit missing-text marker | 1 |
| Chain/introduction without a transmitted body | 1 |
| **Total reviewed** | **244** |

The 238 exclusions and source gaps remain in the original-source view. They have completed semantic disposition review; they are not 238 unread classification tasks. Source gaps remain explicit and are not filled with wording from another edition. No provider occurrence is deleted.

After the normal full-source publication gate succeeds, expected accounting is **36,464 provider occurrences, 36,226 registered reports and 238 source-only entries, with 0 of those held entries awaiting semantic disposition**. These totals are source occurrences, not globally deduplicated reports. Previously registered occurrences can still have separate sibling-language context queues; this 244-entry review does not claim to complete those queues.

### Six recoveries

| Provider ID | Actual report type | Independently selected languages | Source material retained as context |
| --- | --- | --- | --- |
| Abu Dawud 2424 | Historical transmission account by al-Awzai | Arabic, Bengali, English, Urdu | Explanatory identification and appended criticism attributed to Malik |
| Abu Dawud 3338 | Historical exchange involving Shubah and an unnamed man | Arabic, Bengali, English, Urdu | Appended criticism attributed to Yahya ibn Main; English explanatory parenthesis |
| Abu Dawud 3339 | Attributed saying by Shubah | Arabic, Bengali, English, Urdu | Original assessments remain separate metadata |
| Abu Dawud 3587 | Attributed testimonial saying by Muadh ibn Muadh | Arabic, English, Urdu | Identity glosses, Urdu note marker, and the complete Bengali field with a conflicting speaker attribution |
| Nasai 4221 | Historical transmission-inquiry dialogue | Arabic, Bengali, English | The Urdu source field is empty; the referenced aqiqah report body is not inserted |
| Nasai 5752 | Attributed testimonial saying by Abu Usamah | Arabic, Bengali, English | The Urdu source field is empty |

These six entries are not relabelled as sayings of the Prophet. Nasai 916 remains a verse explanation. Source grades are preserved without a new bank authenticity judgment.

## Exact reading and source coverage

All **75 nonempty occurrences** were read in every supplied language. This is **204 nonempty fields and 50,159 Unicode codepoints**. The ledger additionally binds **691 empty fields**, giving **895 source-language rows** across all 244 occurrences.

| Language | Supplied fields | Nonempty fields read | Codepoints read | Original-edition rows verified locally |
| --- | ---: | ---: | ---: | ---: |
| Arabic | 217 | 46 | 10,276 | 155 |
| Bengali | 217 | 46 | 8,586 | 146 |
| English | 217 | 46 | 8,472 | 217 |
| Urdu | 244 | 66 | 22,825 | 238 |
| **Total** | **895** | **204** | **50,159** | **756** |

Every field was inspected from the exact GitHub-held source copies preserved in `input/held/`. The original complete pinned editions were independently reacquired for 18 editions, allowing 756 row-for-row comparisons. Tool transfer limits prevented local reacquisition of six larger original edition files, leaving **139 original-edition row comparisons for the full-checkout gate**. All language fields belonging to the six recoveries were independently compared with complete original pinned editions locally.

The normal export reads and verifies all original snapshots, then the new held-disposition gate compares every ledger binding and every written disposition. Publication must pass that gate; the local receipt does not claim that the 139 remaining original-edition comparisons have already run here.

## Evidence files

- `dispositions.json` and its deterministic compressed copy contain all 244 decisions, individual reasons, prior decisions, exact source positions, complete row hashes, full field hashes, checked ranges, source-local numbering and source grades.
- `additional-reviews.json.gz` contains 22 additive language decisions: 21 selected report fields and the explicit Bengali speaker discrepancy. All decision identities are disjoint from the previously assembled 13,922 decisions.
- `input/held/` preserves the eight exact prior held archives, including the six records that leave the held output after export. Existing historical ledgers are not rewritten.
- `reference-checks.json` records six independently checked Sunnah.com pages. Collection, in-book and English-translation numbering are kept separate. No external reference number or grade replaces Fawaz metadata, and no saved HTML response is claimed.
- `local-validation.json` records the complete Abu Dawud and Nasai before/after export comparison. All **10,917 previously registered records are byte-identical**; exactly four Abu Dawud and two Nasai records are added.
- `recovered-records.jsonl.gz` provides the six reviewable local candidate records, including all excluded source context and their actual source speaker/type.
- `verified-local-primary-files.json` lists the 18 original editions actually reacquired and hash-verified locally.

## Adapter behavior and validation

The new disposition module does not admit reports. A recovery must independently pass the existing quotation decision, source hash, speaker-span, report-group and importer classification checks. A changed source field, grade, reference, position or missing language causes a failure. A source-only exclusion cannot override a positive importer result and a positive disposition cannot override a held result.

The exporter adds these separate metrics without changing the meaning of `held_occurrences`:

- `resolved_excluded_occurrences`
- `resolved_source_gap_occurrences`
- `resolved_commentary_occurrences`
- `unresolved_held_occurrences`
- `recovered_reviewed_occurrences`

Original-source pages show their completed review reason and the source index labels them as reviewed. Unknown future holds remain explicitly awaiting review. The reviewed-export publication gate independently checks that the written held records, classification ledgers and per-book/global metrics match the bound disposition ledger.

Seven focused tests pass: all-field coverage, text/grade/language tampering, source-gap protection, no admission by disposition alone, exact quotation/context partitions, additive catalog loading, and reviewed-versus-pending status accounting. Full original-edition regressions for the two changed books also pass.

After running the repository's normal reviewed export, the independent disposition check can be run directly:

```sh
python scripts/fawaz_held_dispositions.py --root .
python -m unittest discover -s tests -p test_fawaz_held_dispositions.py -v
```

This review does not claim independent Pro QC, translation equivalence between divergent fields, a canonical-number concordance, or authenticity certification.
