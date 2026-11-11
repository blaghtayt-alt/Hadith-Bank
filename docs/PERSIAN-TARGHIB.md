# Persian Targhib and Tarhib source import

The three supplied volumes of **ترغیب و ترهیب صحیح و ضعیف**, translated by **موسی بازماندگان**, are registered as separate Persian source editions. Their title pages credit al-Mundhiri as author and Muhammad Nasir al-Din al-Albani for takhrij. The edition is identified as the first digital edition, dated مهر (میزان) 1397 / محرم 1440, and names کتابخانه قلم.

The owner requested these source files for the bank on 11 November 2026, with hadiths only and commentary excluded. The original DOCX files are preserved byte for byte. Registration authorizes their repository and reader inclusion; it does not assert independent scholarly certification or a new reuse license.

## Included material

<!-- COUNTS_START -->
| Volume | Registered quotation units | Original source |
| --- | ---: | --- |
| 1 | 2,416 | [DOCX](../materials/fa-targhib-bazmandegan-v1/source.docx) |
| 2 | 2,834 | [DOCX](../materials/fa-targhib-bazmandegan-v2/source.docx) |
| 3 | 2,054 | [DOCX](../materials/fa-targhib-bazmandegan-v3/source.docx) |
| **Total** | **7,304** | **Three unchanged source files** |
<!-- COUNTS_END -->

These counts describe registered source quotation units, including wording variants, partial quotations, and separately typed Companion reports. They are not a count of unique canonical hadiths or a claim that every quotation is authentic. Fragments of the same source report retain an explicit relationship.

Narration text is kept separate from source headings, references, grades and the three printed numbering systems. The unified source sequence, Sahih/Daif subcollection sequence and chapter-local label do not become canonical Bukhari, Muslim or other collection numbers. A leading zero on a supplemental entry is not hadith number zero.

The source includes sound, good, weak, very weak, rejected and fabricated assessments, together with more specific qualifications. These printed assessments remain visible; mixed-grade qualifications are preserved in full. An individually named grader is recorded where the source explicitly supplies one. The edition's al-Albani takhrij credit is stored separately and is not assigned automatically to every quoted assessment.

## Commentary and ideological material

The source contains explicit theological, legal and sectarian editorial discussion. It is excluded from narration text, with exact source locations retained in the audit. Twenty-five specifically flagged footnotes were checked against the original DOCX footnotes. Examples are:

| Volume | Source number | Original footnote | Editorial subject |
| --- | --- | --- | --- |
| 1 | 26 | 100 | Divine descent and criticism of ta'wil |
| 1 | 987 | 1084 | Interpretation of tawassul |
| 1 | 1455 | 1491 | Anti-Shia polemical statement |
| 2 | 1790 | 70 | Anti-Sufi discussion |
| 3 | 5201 | 1038 | Interpretation excluding the Companions from the Hawd warning |

These are the source editors' comments, not words attributed to the Prophet in the extracted narration. The targeted review did not establish Shia doctrine inserted into the quoted matn. That finding does not certify every translation as free of interpretive choices.

A total of **81 exact inline spans in 62 source paragraphs** were removed only after comparing their exact spans with the surrounding narration. Parentheses and square brackets were not removed wholesale: some enclose genuine narration wording or text whose source grade differs. Explicitly bounded narration quotations found within a footnote or commentary remain separately identified as excerpts. Two independent sayings attributed to Jesus and 11 separately reviewed later-speaker or uncertain-attribution units are excluded from the searchable corpus. Later scholarly advice, definitions and grading-only quotations are excluded from the narration payload and retained in the audit.

## Source qualifications

The following source issues remain available in the affected records' source notes:

- Volume 1, source number 38: the Persian rendering appears to reverse the religious means and worldly ends in the Arabic expression. The supplied wording is preserved and flagged.
- The same source number retains the short translator's gloss «(به حلم و فرصت دادن من)» alongside «أَبِي يَغْتَرُّونَ». It remains part of the supplied translation, with its interpretive character recorded here; the targeted removal audit is not a claim that every explanatory translation choice has been eliminated.
- Volume 3, source number 3964: the main Persian wording reverses who asks and who is asked. Its bracketed alternate agrees with the Arabic and is retained; no replacement translation was generated.
- Volume 3, paragraph p00816: the supplied Persian wording interprets the Arabic statement about time as events occurring by God's will. Both supplied texts are retained and the interpretive rendering is qualified.
- Volume 3, paragraph p02033: an original custom-font honorific following Muhammad decodes to رضي الله عنه. The source anomaly is preserved and flagged rather than silently normalized.
- Source punctuation defects and unresolved bilingual alignment remain explicit. A missing language field means that text is absent or not securely aligned for that extracted unit; it does not necessarily mean the wording is absent everywhere in the volume.

Additional detected interpretations, including the honor/status explanation at volume 3 source number 5232, are preserved in the removal audit and excluded from the narration.

## Reproduction and verification

`scripts/import_persian_targhib.py` verifies original DOCX hashes, replays the frozen quotation spans against their OOXML paragraphs, decodes only the documented custom-font mappings, applies the reviewed commentary removals, and registers the three materials. It rejects changed source spans and partially overlapping extra selections. It does not produce translations or infer canonical identities.

```bash
python scripts/import_persian_targhib.py --root .
python -m unittest discover -s tests -p 'test_persian_targhib_source.py'
python scripts/refresh_bank.py --root . --site-output _site
```

The final text-span audit, original and continuing review decisions, excluded prose, exact inline patches and frozen extraction inputs are under `imports/persian-targhib-20261111/`. The evidence manifest supplies paths, sizes and SHA-256 hashes. Source DOCX files and record checksums are separately declared in each material manifest.

Three remaining literal U+F0BB source-font tokens have no evidenced mapping. Their exact source characters and an explicit warning remain in the affected records; custom footnote markers were handled separately from narration.

The source fidelity checks establish reproducible extraction from the selected spans. They are not an independent Pro certification, exhaustive semantic translation certification, or new hadith authenticity assessment. Native OOXML extraction is non-OCR, so the existing OCR-only badge policy applies. Historical review fields and unassessed rights remain intact.

## Files and reports

- [Volume 1 source](../materials/fa-targhib-bazmandegan-v1/source.docx) · [manifest](../materials/fa-targhib-bazmandegan-v1/manifest.json)
- [Volume 2 source](../materials/fa-targhib-bazmandegan-v2/source.docx) · [manifest](../materials/fa-targhib-bazmandegan-v2/manifest.json)
- [Volume 3 source](../materials/fa-targhib-bazmandegan-v3/source.docx) · [manifest](../materials/fa-targhib-bazmandegan-v3/manifest.json)
- [Integration report](../reports/persian-targhib-integration.json)
- [Release verification](../reports/persian-targhib-verification.json)
- [Content review summary](../reports/persian-targhib-content-review.json)
- [Frozen evidence manifest](../imports/persian-targhib-20261111/evidence-manifest.json)

In the reader, each quotation links to its original volume and offers a direct **Download DOCX** link from GitHub. The three DOCX files are the supplied originals; no PDF conversion is implied.
