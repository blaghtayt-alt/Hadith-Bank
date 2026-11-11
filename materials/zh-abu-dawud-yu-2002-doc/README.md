# 艾布达吾德圣训部分译本 Sunan Abi Dawud partial Chinese edition

This material imports the exact owner-supplied legacy Word file into the Chinese
Hadith Bank. The source identifies the work as `艾布·达吾德圣训集` and its
translator preface is signed `穆萨·余崇仁书`, dated `2002年8月于银川新城`.
The file is a **partial source**, ending in its fourteenth book at local printed
entry 2868. The bank does not describe it as the complete Sunan Abi Dawud.

## Source and scope

| Item | Value |
| --- | --- |
| Original uploaded filename | `1039713868-艾布达吾德圣训.doc` |
| Repository filename | `艾布达吾德圣训_Sunan_Abi_Dawud.doc` |
| Original file size | 794,112 bytes |
| Original SHA-256 | `cbff2d2c521e553c6eb11a75d6079fe526930295b7a3fc4726cc8e7a4e0a42c8` |
| Edition ID | `doc-cbff2d2c521e553c` |
| Source language | `zh-CN` |
| Numbered source items | 2,834 |
| Imported narration occurrences | 2,828 |
| Numbered comment-only items retained in the audit | 1432, 1434, 1440, 2604, 2847, 2866 |
| Attribution URL | <https://www.scribd.com/document/1039713868/艾布达吾德圣训> |

Counts refer to source occurrences, including transmitted reports, and do not
assert a count of distinct or independently authenticated Prophetic sayings.
Arabic originals, canonical-number matches, and authenticity grades have not
been supplied or inferred. Named translator evidence supports the Human
translation-origin classification; no new translation was produced.

## Source preservation and boundaries

The original DOC is byte-identical to the upload. The importer reads its native
Word CFB streams and CLX piece table. It uses no OCR. `native-text.txt` contains
the full native text, with paragraph carriage returns replaced one-for-one by
line feeds. All its characters are in the Unicode BMP, so its zero-based
Unicode character positions also correspond to native Word CP positions.

Each narration has exact half-open source intervals in
`source_locator.included_source_spans`. Joining those slices of `native-text.txt`
reconstructs the narration text exactly. Source wording, spelling, and printed
number anomalies are retained.

`extraction-plan.json` records the checked source boundaries and paragraph roles.
It splits five paragraphs that each contain two explicitly numbered entries.
Numbers 1599, 2455, 2489, and 2505 occur twice; each occurrence receives a distinct
ID based on its original character position. Numbers 1499, 2566, 2640–2669,
2749–2753, and 2783 are absent. No missing text or numbers have been invented.

The second source occurrence numbered 2455, at native character position 253672,
ends mid-sentence with `白尼·奈迪尔被驱逐时，` in the supplied DOC. It is retained
as a visibly labeled source fragment, with an explicit source-defect note.

The source contains 106 explicit note paragraphs, 11 note-continuation
paragraphs, 36 additional explanatory or compiler-comment paragraphs, six
comment-only numbered items, and six reviewed inline editorial spans. These
are excluded from the narration payload and retained verbatim with locators in
`excluded-commentary.json.gz` and the original source. The prefaces are retained
there as well. The long editorial insertion within local entry 18 and the
inline geographic note within entry 1087 are explicitly separated.

Parentheses are not deleted indiscriminately. Source wording that supplies
narrative connections, action details, repetition counts, or Quran locators is
preserved and inventoried in `parenthetical-inventory.json.gz`. The compiler's
additional narrated quotation within local entry 2459 is retained; a speaker's
name alone does not make a paragraph editorial commentary. No sectarian
classification is inferred from these extraction decisions.

`source-number-ledger.json` accounts for all 2,834 numbered items, including the
six items outside narration search. The source-local numbering is explicitly
labeled in every imported record and is never promoted to a canonical number.

## Reproduce this material

From the repository root, using Python 3.11 or later:

```bash
python scripts/import_chinese_abu_dawud.py --root .
```

The importer verifies the original checksum and the native-text checksum before
applying the source-specific plan. It regenerates the records, source ledger,
metadata, audit files, and material manifest. It does not rebuild the website;
the normal registered-material workflow performs that step.

The owner authorized repository and reader inclusion on 11 November 2026.
Independent Pro QC has not been performed, and this material is not a certified
release. Reuse rights remain unassessed; the publication instruction does not
create a publisher license.
