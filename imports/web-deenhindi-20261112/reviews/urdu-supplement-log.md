# Independent Urdu field supplement for the frozen first 300 Deen Hindi records

## Outcome

All 290 previously unread Urdu fields in ordinals 11–300 of the frozen Bukhari cohort were read completely. The review covers 160,613 Unicode code points. It selects 288 fields: 217 whole fields and 71 fields with explicit excerpt or component boundaries. The selected material contains 155,543 characters in 330 exact spans belonging to 324 language-specific report components. The remaining 5,070 characters are preserved as source context.

Two Urdu fields, provider numbers 342 and 402.2, contain only an abbreviated direction to another transmission without substantive supplied report wording. Both were read and remain complete source context. They are not failed downloads. No replacement text was reconstructed.

The supplement retains the 300 source occurrence identities and their original registration decisions. It does not create 288 new source occurrences. Together with the frozen first ten Urdu reviews, all 300 Urdu fields have now been read: 297 have selected text; the original number 4 attribution uncertainty remains unchanged, alongside the two newly reviewed pointer-only fields.

## Exact artifacts and integration

The wrapper is `20261113-held-bukhari-first300-urdu-supplement.json`, with SHA-256:

`e1bfd079175ee55c41fd5c09b80cc8217785eba10a88d9c7e530e3337780622e`

It uses `hadith-bank-web-source-review-v1`, with `supplement_type=field_replacements`, one `field_reviews` entry per record, and explicit inherited `decision=register`. Each replacement is keyed by exact parent record ID, Urdu language-version ID, source-record hash, snapshot hash, field hash and length. Every selected and context span has a hash and Python Unicode code-point offsets. Report components have stable IDs, actual speaker descriptions and report types.

The exact parent review is `imports/web-deenhindi-20261112/reviews/20261113-held-bukhari-first300.json`, SHA-256:

`7a7771c8584601684a0e2a28b264dc3884e95bed5309c533641f9c446a55c293`

The source baseline remains `1bdc84b9483a068cc56da97046c55ffe756ea478`. The cohort was not expanded or reordered to follow newer acquisition checkpoints. All seven frozen first-pass artifacts remain byte-identical.

Merge the explicit Urdu replacements into their matching parent records. Do not place this wrapper beside the parent as a separate additive `source-review*.json` ledger: its IDs intentionally overlap the parent, and its other four language decisions are inherited through the parent rather than repeated. The final merged publication ledger should retain the parent and supplement hashes as audit provenance. The sibling Hindi supplement is a separate review and is not included in this supplement's counts or validation fixture.

## Actual field decisions that require care

- **239:** The Urdu same-chain reference is followed by actual stagnant-water prohibition wording. After an explicit second reading, it is retained as `abbreviated_transmission`, with an unnamed speaker of the source's referenced preceding chain and `ultimate_speaker=null`. Neither the Prophet's identity nor missing chain names were borrowed from English. The adapter preserves the null ultimate speaker in the report component.
- **342 and 402.2:** These are the two pure pointers retained as context; no substantive missing narration is supplied from another field.
- **486:** The Urdu field contains a complete Ibn Umar travel/prayer report and is selected. The English translation-pointer decision remains unchanged.
- **834:** The Urdu field supplies a legible invocation and its report. Its selection does not repair or approve the distinct standalone Arabic field containing replacement characters.
- **839 and 840:** The supplied Urdu fields contain the short childhood water-memory report. No longer Itban narrative was appended from another language.
- **848:** Ibn Umar's and al-Qasim's practices are selected as two distinct components. The following claimed Prophetic prohibition and the source's attached criticism stay together as complete source context. This is a boundary decision, not independent authenticity grading.
- **1037:** Urdu identifies Ibn Umar in the supplied chain. The attribution remains a Companion-attributed invocation/dialogue rather than importing the English field's explicit Prophetic attribution.
- **1114:** Urdu explicitly says that the companions also prayed seated. The independently reviewed English says they prayed standing. The supplement adds a confirmed Urdu/English source-content difference with exact evidence spans and hashes for both fields. The already frozen Arabic/English difference remains unchanged. Each original reading is preserved without harmonization.
- **1132.2:** Urdu itself identifies the Prophet in parentheses, supporting the abbreviated practice report. This does not resolve the unnamed subject in the separate Arabic field.
- **1133:** Urdu says the Messenger was lying at dawn. It is retained without changing that wording into explicit sleeping from another field.
- **1155:** The Urdu sermon framing attributes the comment to Abu Huraira. Abdullah ibn Rawaha's explicitly identified poem is a separate component; poet-identification framing and terminal corroborating-chain notices are context. The English speaker assignment was not copied into Urdu.
- **1174:** Ibn Abbas's prayer testimony and the later tentative timing dialogue remain separate reports. The later speakers' expressed conjecture is not promoted to an established fact about the Prophet. The standalone parenthetical no-intervening-sunnah explanation is context.

Own-field name qualifications are retained where the Urdu source phrases names differently, including 226, 575, 1082 and 1083. These are source wording qualifications; no unreviewed sibling field was labelled a confirmed content mismatch. Integrated translation clarifications remain part of coherent narration where appropriate, while manually identified standalone compiler, legal, Quran and explanatory spans remain source context. Selecting a narrative does not assert that every word in it is direct speech by one speaker.

## Validation performed

`python urdu-supplement/validate_supplement.py` completed with `status=PASS`.

The validator replaced exactly 290 Urdu field decisions and left 1,210 other field decisions unchanged. It applied all 300 records through the shared `scripts/web_source_reviews.py` adapter, using `canonical_record(saved)` from the exact saved importer. All 1,500 original language fields reconstruct exactly from the selected and context partitions, with no missing, overlapping or changed characters. The original saved objects, canonical inputs, baselines, references and occurrence IDs remain unchanged.

The tested shared adapter SHA-256 is:

`3e180bdcb5cbcad17f039900b4e80394e0755ecbed7c3f163b1d379cf0f6c495`

The tested saved importer SHA-256 is:

`2802fdbde35f74e32cae95fe6e3d81d2ce3d25da052f09d9c8d6e6d7bd0c0206`

The supplement validator also rechecked all 600 locally saved evidence files against the frozen pinned-GitHub receipts: 300 parsed gzip files and 300 raw HTML gzip files. Compressed bytes, decompressed hashes and Git blob identities all match. Every HTML snapshot reparses to the complete exact original five-language source object and literal source reference. The original independent pinned-GitHub evidence audit has SHA-256 `b27a9058559b8d45ea9e77f6c6879e3c78781af9f7148aea0db3eeea2bd43115`. This supplemental recheck used the saved bytes; it made no further network requests.

The parent-plus-Urdu validation fixture contains 920 reviewed fields and 911 selected fields. Its 580 unread fields are 290 Hindi and 290 Roman Urdu fields; the separate Hindi review is intentionally absent from this fixture. Original reviewed uncertainties and the English pointer remain unchanged. These are fixture-specific coverage counts, not a claim about the separately merged final release or the whole Deen Hindi queue.

The machine-readable coverage and validation reports accompany this log. The manual `notes-*.jsonl` files record all 290 individually authored decisions and the exact boundary markers used by the serializer. The serializer resolves those explicitly chosen markers to offsets; it does not classify or approve source text by a general matching heuristic.

## Scope and limitations

`independent_pro_qc=not_performed` throughout. This is complete semantic reading of the supplied Urdu fields for attribution and narration boundaries, with structural source-integrity checks. It does not certify translation accuracy, individual glyphs/diacritics, canonical cross-edition identity or authenticity. Source-local numbers and literal source references remain separate from unknown external canonical references.

No Deen Hindi request, historical error retry, workflow dispatch, remote mutation or restart was performed. The current healthy acquisition worker and concurrent import checkpoints were left untouched. No new translations, missing wording, chains or canonical references were generated.
