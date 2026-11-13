# Patch08 independent character QC

**Result: pass within the reviewed scope, with one retained source-limited exception.**

The reviewed character components are ready for integration. No blocking character defect or required correction was found. This is a fresh independent reading of 13 complete pages and 14 localized targets, supported by original-PDF rendering, source CP checks, PDF glyph draws and embedded font evidence. It does not certify an independent reread of all 2,054 pages.

## What was actually read

| Scope | Volume 1 | Volume 2 | Count |
|---|---|---|---:|
| Complete pages | 8 | 1, 2, 1022–1031 | 13 |
| Localized targets only | 150, 178, 315, 399, 433, 600, 641, 671, 962 | 148, 405, 407, 699, 721 | 14 |

The review actually displayed 28 authenticated images: 13 complete page images and 15 target images, including both the 24× and 60× honorific views. Every supplied image matched an independent original-PDF rerender pixel for pixel. The immutable original PDFs contain 1,023 and 1,031 pages. Their entire page counts are not this review’s visual scope.

The original files, source story exports, relevant parent ledgers and all files in both author branches were hashed at the beginning. `reviewed_inputs.json` binds 238 files. A final recheck found no changed input.

## Findings that determine the result

### Thirteen localized resolutions are supported

The original PDFs draw the disputed marks described in the 13 proposed resolutions. Several marks overlap a letter or another vowel, so visual stroke count alone cannot establish the number of source codepoints. Original glyph identities, draw origins and nonempty font outlines corroborate the specific duplicated marks. The Arabic source order, anomalous vowels and Bengali duplicate ra-phala remain unchanged.

| Page | Exact target/source range | Independent conclusion |
|---|---|---|
| V1 p150 | main CP 174825–174827 (end exclusive); `.ٰ` | The left-of-حسن mark is visibly a dot adjoining an upright curved stroke. Independent original-PDF trace confirms glyph15 period and glyph100 superscript alef at the same origin. The after transcription .ٰ correctly retains both source characters; this does not license replacement with a comma. |
| V1 p178 | main CP 206002–206013 (end exclusive); `لأََِخْرَقَ` | Two diagonal strokes are visible below the lam-alef cluster. The original trace has two coincident fatha draws at one origin plus a distinct kasra draw, explaining why three source combining codepoints form two visible diagonal shapes. The unusual source order and all three marks are retained. |
| V2 p148 | main CP 130427–130429 (end exclusive); `َّ` | The target above the first ra of خَرَّ is a shadda-shaped form crossed by a diagonal. Independent glyph draws account for both shadda and fatha. The raw combining order remains fatha then shadda. The surrounding large region is inherited; it was not fully reread in this review. |
| V1 p315 | main CP 361397–361399 (end exclusive); `ٍٍ` | The target امْرئٍٍ shows two pairs of diagonal strokes, one pair overlapping the lower letter and one pair below it. Separate original-PDF draws of kasratan glyph79 corroborate both U+064D characters. No intended grammatical correction is inferred. |
| V1 p399 | main CP 454737–454748 (end exclusive); `لأََِجْرِكِ` | As on p178, two visible diagonals below lam-alef correspond to two coincident fatha draws and one separate kasra draw. The exact source cluster لأََِجْرِكِ is therefore preserved, with geometric overlap documented separately from the Unicode sequence. |
| V2 p405 | main CP 363776–363779 (end exclusive); `نََ` | In the blue Arabic word, one diagonal stands above nun and another crosses its left terminal. The trace independently identifies both as fatha draws separate from nun. The after transcription retains نََ; the broader paragraph uses only inherited display mappings. |
| V2 p407 | main CP 365576–365579 (end exclusive); `ئْْ` | One sukun loop is above the final hamza-on-ya; a second loop overlaps its left terminal. Two actual sukun glyph draws establish the duplicated source marks. The source ئْْ is preserved and the rest of the paragraph remains inherited. |
| V1 p433 | main CP 494359–494361 (end exclusive); `ََ` | The wide crop contains the actual dal in فَأَقْعَدََتْهُ. A diagonal above it and a second diagonal crossing its lower stroke are visible. Both have independent fatha draws. The new crop correctly includes the target that the older narrow crop missed. |
| V1 p600 | main CP 687905–687908 (end exclusive); `لِِ` | The lam bowl is crossed by a diagonal and a second diagonal lies below. Both are kasra glyphs in the original trace, separate from the lam outline. The source لِِ is retained and the earlier one-stroke impression is correctly superseded. |
| V1 p641 | main CP 736494–736503 (end exclusive); `প্র্রশস্ত` | The Bengali initial conjunct has an overlapping extra leftward stroke. The actual page content uses resource F2/xref9919, drawing প্র ligature glyph308 followed by extra ra-phala glyph436. Independent GSUB inspection confirms virama+ra -> glyph436 and pa+glyph436 -> glyph308. The source প্র্রশস্ত must remain doubled. |
| V1 p671 | main CP 769837–769845 (end exclusive); `فَقَالََ` | The final lam in فَقَالََ has one fatha above and another diagonal crossing its bowl. The original trace supplies two distinct fatha draws, so the after transcription correctly retains the source duplicate. |
| V2 p699 | main CP 638270–638274 (end exclusive); `ذِِّ` | Two lower diagonals and a small shadda overlapping the dhal baseline are visible in فَيُعَذِِّبُهُ. The original trace accounts for two kasras and one shadda separately from the letter. The source combining order ذِِّ remains exact. |
| V2 p721 | main CP 657031–657034 (end exclusive); `هَِ` | The final heh in أَظْفَارِهَِ has a crossing diagonal and a separate lower diagonal. The first is a fatha glyph and the second a kasra glyph in the original trace. Both source vowels are retained; neither is normalized to an expected reading. |
| V1 p962 | main CP 1076183–1076184 (end exclusive); `` | Both 24x and 60x views show one stacked ornate honorific with the lexical reading رضي الله عنهم. Original font F25/xref2233 maps U+F079 to the same 14-contour glyph92. That identifies the raw character and graphic, but does not establish an exact Unicode decomposition of every internal mark. Keeping the visible transcription null and the exception open is justified. |

### One exception remains open

V1 p962, main CP 1076183–1076184, contains the single source codepoint U+F079. Both enlarged views show the ornate stacked honorific, and the original embedded AGA Arabesque font confirms glyph92 with 14 contours. Its lexical reading is رضي الله عنهم. The PDF font does not separately encode every interior diacritic, and this review does not establish a complete vocalized Unicode expansion. The correct result is to preserve the original codepoint, leave the visible transcription null, and retain `p07-1-929-v01-p0962-r05-chars-unresolved`. This retained source limitation is not a newly introduced defect.

### Appendix and cover evidence is source-faithful

All 220 tail character regions were compared with the 13 full-page views and their raw source spans. The covered source intervals have no missing codepoints: V1 main [6771,6837), V2 main [0,605), and V2 main [951605,959535).

The appendix has 53 rows including its header and 52 numbered entries. The independently read printed-number sequence matches the bridge file. Each row has three visible content columns and a fourth empty DOC row-terminator slot. All 212 cell slots were checked against exact source slices and terminators. Entries continued across page boundaries remain joined to their original row.

The critic cells for printed references **917, 954, 1649, 1731 and 1765** are empty in the original. There are five source cells but seven page-level blank regions because 954 and 1731 span pages. No critic name is supplied.

The source anomalies are visible and correctly preserved: the ampersand after entry794; the incomplete critic label beginning only র ইবনু হাওশাব; repeated করে করে in entry801; literal less-than signs in entries894,896 and1495; and এতটি in entry1498. The cover metadata and image logos are distinguished from report body text.

The appendix’s weak-grade heading, critic labels and quoted excerpts remain edition claims. This review does not independently grade hadith, authenticate chains, identify every narrator, establish canonical numbering, or certify an excerpt as complete matn.

## Structural corroboration

The independent checks passed 2216 assertions with zero unresolved assertion failures. Material checks include:

- 28 original-PDF rerenders matched author evidence pixel for pixel.
- All 14 review and 14 region correction before-states matched the authenticated parent exactly.
- Every declared exact source slice matched the parent raw story export.
- The 13 resolution events reference existing parent exceptions; the remaining honorific exception is retained.
- The selected original glyph draws and extracted font bytes/outlines match the supplied evidence.
- Bengali p641 uses the actual F2 resource and the embedded GSUB rules independently corroborate the extra ra-phala.
- Every completed after-transcription can be derived from unchanged source plus exact inherited display mappings; existing difference records are preserved.
- All 156 parent semantic evidence links and 19 new tail semantic spans match exact source/parent records.

The source-derived transcriptions for large inherited regions were checked mechanically. Only their localized target crops were independently reread here; the remainder of those pages retains its previous review provenance.

## Page observation ledger

The full machine-readable per-page observations, exact CP spans, region IDs and image hashes are in `page_observations.jsonl`; the appendix row/cell observations are in `appendix_row_observations.jsonl`. The following notes record what the complete-page readings established:

### V1 p8

Read the complete two-line Bengali preface ending and footer 8. The text begins ছাড়া, preserves সৎকাজ and the parenthesis (নড়া-চড়ার), and ends নেই।. The rest of the page is blank. Raw paragraph/page controls have no visible ink.

### V2 p1

Read the Bengali title, (২য় খণ্ড), three-language bracketed line, author and editorial credits, 2013 - 1434, and the IslamHouse.com logo. The Bengali author form আন-নাওয়াবী is preserved as source text. There is no printed footer. The logo is an image/object occurrence linked to a DOC hyperlink field, not newly invented body text.

### V2 p2

Read all Arabic cover lines: رياض الصالحين; الجزء الثاني; the Bengali-language label; author, تحقيق, ترجمة and مراجعة credits; date line and IslamHouse.com logo. Hamzas and letter dots are consistent with the source transcription. The cover has no footer. Attribution and editorial credit remain edition claims.

### V2 p1022

Read the appendix title declaring its weak-hadith list, three visible column headings, all five numbered entries and their critic labels, and footer 1022. Entry 292 continues its critic label onto the next page. The middle heading says হাদীসের মতন, while the entries visibly contain excerpt omissions; no full-matn claim follows from the heading.

### V2 p1023

Read the continuing critic label উভয়ে মাজহূল at the top, entries 360 through 486, and the opening excerpt and critic fragments of 524. All six printed entry numbers and footer 1023 agree. The source name আশিয়াহ and the printed wording/ellipsis lengths are retained. Entry 524 continues on the next page.

### V2 p1024

Read the continuation of 524, including হাওশাব in its critic cell, then entries 583, 589, 601, 718 and 736. Literal quotation marks, the parenthetical (৭), du’a punctuation, critic labels and footer 1024 agree. The absent horizontal boundary between the last two entries is source layout; the printed entry numbers and exact DOC row controls distinguish them.

### V2 p1025

Read all six entries and footer 1025. Entry 794 visibly ends its excerpt with an ampersand and its critic label begins only র ইবনু হাওশাব. Entry 801 visibly repeats করে করে. Entry 894 visibly contains <-এর and continues to the next page. None of these literal source anomalies is repaired by inference.

### V2 p1026

Read the continuation of 894, entries 895, 896, 917, 951, and the opening of 954, plus footer 1026. A literal < follows নাবী in 896. The critic cells for 917 and 954 are visibly empty. The body of 954 continues on 1027; the blank critic cell is one source cell across both pages.

### V2 p1027

Read the continuation of 954 and its blank critic space, then entries 990, 1007, 1067, 1103, 1166 and the start of 1244. Underlining in 1103 is a layout/style feature and is not extra text. Critic fragments and footer 1027 agree. The last entry and its critic label continue on 1028.

### V2 p1028

Read the continuation of 1244 and critic surname রহমান, then all printed numbers 1256, 1274, 1343, 1394, 1402, 1495, their visible excerpts and critic labels. The 1495 excerpt continues on 1029. Footer 1028 and source punctuation agree; no absent words are supplied to incomplete excerpts.

### V2 p1029

Read the continuing 1495 excerpt including literal <-কে, then 1498, 1500, 1501 and 1526 with their critic labels and footer 1029. Entry 1498 visibly reads এতটি, so an editorial replacement with একটি would be unsupported. The Bengali transliteration of the du’a is retained literally rather than substituted with an Arabic expansion.

### V2 p1030

Read entries 1547, 1577, 1649, 1679, 1686 and the opening of 1731, including italic critic names and footer 1030. The critic cells of 1649 and 1731 are empty. The latter remains blank on the continuation page. Source spelling, ellipses and quote marks agree with the exact mappings.

### V2 p1031

Read the continuation of 1731, entries 1765, 1841 and 1882, end marker সমাপ্ত, and footer 1031. Critic cells for continuing 1731 and 1765 are empty. Labels সা‘লাবা আলখুশানী and হাকাম ইবনু মুস‘য়াব are retained as printed source labels. The visible blank remainder contains no omitted body text.

## Accepted coverage arithmetic

The tail contribution adds 10 newly attempted and fully reviewed pages. The three legacy cover/preface rechecks add detail and zero new page credit. Localized follow-up contributes zero new attempts and 13 completions of inherited partial pages, with V1 p962 remaining partial. Independent QC itself adds no new bank-coverage credit.

## Handoff and limits

No corrective edit is required for the reviewed character component files. Retain the single honorific exception and all source-literal anomalies. Integration must apply the exact reviewed overlays against their cited parent states.

This report binds the author component files through `reviewed_inputs.json`. It does not independently verify the bytes of the final merged package, confer whole-bank certification, or convert inherited whole-page review into fresh independent visual review. A separate candidate integration check is required.
