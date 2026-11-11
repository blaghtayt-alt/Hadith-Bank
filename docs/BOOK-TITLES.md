# Native-first book display titles

The reader and generated book pages display the selected language’s attested collection name before the existing English name: `Native title — English title`. Display names are defined in `scripts/book_titles.py`. They do not rewrite record keys, canonical routes, source-edition names, source quotations, numbering, or counterpart matches.

## Resolution rules

- Prefer the collection title recorded in a preserved source or a primary publisher’s language-specific citation. Keep abridgment, volume, translator, and recension names at source-edition level.
- If a distinct local title is not established, use the original Arabic name before English. English and mixed-language collection filters keep one English label; individual records and source editions keep their own language.
- Filipino and Vietnamese sources often use the same Romanized title as English. Use the original Arabic title in those cases instead of repeating effectively the same name. Retain documented local titles such as the Filipino Hisn title and Vietnamese Riyadh title.
- `hakim`, `tabarani`, and `ibn-hibban` also represent attribution groups. Their original-name prefix identifies the compiler; it does not assign every occurrence to a specific work. Static pages retain their existing qualified English wording.
- HadeethEnc is a provider name. Keep the brand where no distinct attested local display name is recorded. `unclassified` is a translated UI status, not a book title.
- Language and book aliases affect lookup only. Unknown collection keys remain visible. Do not apply Simplified Chinese titles to Traditional Chinese codes.
- Plain-text labels are embedded in offline-reader metadata and escaped at output. Native and English segments use bidirectional isolation in reading headings, tiles, and static book labels.

## Title evidence

Checked on 2026-11-12 (Japan time). Local paths refer to preserved repository sources. Web links refer to the publishers’ own titles or collection citations. A title citation establishes a name only; it does not certify any translation or change publication/review status.

| Language | Collection key | Display prefix | Evidence |
| --- | --- | --- | --- |
| fa | `abu-dawud` | سنن ابی‌داوود | [Publisher](https://hadeethenc.com/fa/browse/hadith/5886) |
| fa | `adab-al-mufrad` | الأدب المفرد | [Publisher](https://islamhouse.com/fa/khotab/2834456/) |
| fa | `ahmad` | مُسنَد احمد | [Publisher](https://hadeethenc.com/fa/browse/hadith/65027) |
| fa | `bukhari` | صحیح البخاری | `materials/fa-faiz-al-bari-v1/source-metadata.json` |
| fa | `ibn-majah` | سنن ابن‌ماجه | [Publisher](https://hadeethenc.com/fa/browse/hadith/5487) |
| fa | `muslim` | صحیح مسلم | `materials/fa-muslim-mundhiri-tarshabi-v1/source-metadata.json` |
| fa | `riyadh-al-salihin` | ریاض الصالحین | `materials/fa-riyadh-heravi-1394-digital/source-metadata.json` |
| fa | `targhib-wa-tarhib` | ترغیب و ترهیب | `materials/fa-targhib-bazmandegan-v1/manifest.json` |
| fa | `tirmidhi` | سنن ترمذی | [Publisher](https://hadeethenc.com/fa/browse/hadith/6614) |
| fil | `hisn-al-muslim` | KUTANG-TANGGULAN NG MUSLIM | [Publisher](https://islamhouse.com/tl/books/1091/) |
| hi | `abu-dawud` | सुनन अबू दावूद | [Publisher](https://hadeethenc.com/hi/browse/hadith/10046) — Hindi source-collection citation, parsed line 23 |
| hi | `adab-al-mufrad` | अल-अदब अल-मुफ़रद | [Publisher](https://hadeethenc.com/hi/browse/hadith/66179) — Hindi source-collection citation; also preserved official SQLite snapshot record below |
| hi | `ahmad` | मुसनद अह़मद | [Publisher](https://hadeethenc.com/hi/browse/hadith/11303) — Hindi source-collection citation, parsed line 23 |
| hi | `bukhari` | सह़ीह़ बुख़ारी | [Publisher](https://hadeethenc.com/hi/browse/hadith/10404) — Hindi source-collection citation, parsed line 29 |
| hi | `hisn-al-muslim` | हिस्नुल्-मुस्लिम | [Publisher](https://islamhouse.com/hi/books/2842335/) — Book page title; parenthetical description omitted from collection name |
| hi | `ibn-majah` | सुनन इब्ने माजह | [Publisher](https://hadeethenc.com/hi/browse/hadith/65172) — Hindi source-collection citation, parsed line 23 |
| hi | `muslim` | सहीह मुस्लिम | `materials/legacy-hi-muslim/records.json` |
| hi | `tirmidhi` | सुनन तिर्मिज़ी | [Publisher](https://hadeethenc.com/hi/browse/hadith/5976) — Hindi source-collection citation, parsed line 28 |
| ja | `abu-dawud` | スナン・アブー・ダーウード | [Publisher](https://islamhouse.com/ja/articles/330792/) — Footnote 1; parsed line 267 |
| ja | `adab-al-mufrad` | アル＝アダブ・アル＝ムフラド | [Publisher](https://islamhouse.com/ja/articles/330792/) — Footnote 65; parsed line 386 |
| ja | `ahmad` | ムスナド・アフマド | `materials/legacy-ja-bukhari/records.json` |
| ja | `bukhari` | サヒーフ・アル＝ブハーリー | `materials/legacy-ja-bukhari/records.json` |
| ja | `hisn-al-muslim` | ムスリムの砦 | `materials/legacy-ja-abu-dawud/records.json` |
| ja | `ibn-majah` | スナン・イブン・マージャ | [Publisher](https://islamhouse.com/ja/articles/330792/) — Footnote 16; parsed line 295 |
| ja | `mishkat-al-masabih` | ミシカート アルマサビーハ | [Publisher](https://d1.islamhouse.com/data/ja/ih_books/single/ja_New_muslim_guide.pdf) — Printed page 123, footnote 2; PDF page index 147 / viewer page 148; parsed lines 3599-3600 |
| ja | `muslim` | サヒーフ・ムスリム | `catalog/materials.json` |
| ja | `tirmidhi` | スナン・アッ＝ティルミズィー | [Publisher](https://islamhouse.com/ja/articles/330792/) — Footnote 17; parsed line 297 |
| uz | `abu-dawud` | Сунани Абу Довуд | [Publisher](https://hadeethenc.com/uz/browse/hadith/65012) |
| uz | `adab-al-mufrad` | Ал-Адаб ал-Муфрад | [Publisher](https://islamhouse.com/uz/audios/2786043/) |
| uz | `ahmad` | Муснади Аҳмад | [Publisher](https://hadeethenc.com/uz/browse/hadith/3336) |
| uz | `bukhari` | Саҳиҳ ал-Бухорий | `materials/legacy-uz-bukhari/records.json` |
| uz | `ibn-majah` | Сунани Ибн Можа | [Publisher](https://hadeethenc.com/uz/browse/hadith/65045) |
| uz | `muslim` | Саҳиҳ Муслим | `materials/legacy-uz-bukhari/records.json` |
| uz | `riyadh-al-salihin` | Риёзус-солиҳийн | `materials/legacy-uz-bukhari/records.json` |
| uz | `tirmidhi` | Жомеъ ат-Термизий | `materials/legacy-uz-tirmidhi/records.json` |
| vi | `200-golden-hadith` | HAI TRĂM HADITH VÀNG CỦA NABI MUHAMMAD | `attachments/attachments-vi-920394517894aea9/languages/vi/books/200-golden-hadith/editions/pdf-c7dcc5d2a0abffdd/records.json` |
| vi | `hisn-al-muslim` | حصن المسلم | [Publisher](https://islamhouse.com/read/vi/hisnul-muslim-193987) |
| vi | `riyadh-al-salihin` | Những Ngôi Vườn Của Những Người Ngoan Đạo | [Publisher](https://islamhouse.com/vi/books/2784706) |
| zh-CN | `abu-dawud` | 艾布·达吾德圣训集 | `materials/zh-abu-dawud-yu-2002-doc/source-metadata.json` — /source_title_as_printed |
| zh-CN | `adab-al-mufrad` | 道德箴言集 | [Publisher: Hisn al-Muslim title and book citations](https://risala.prh.gov.sa/zh/contents/1490) |
| zh-CN | `ahmad` | 艾哈迈德圣训集 | [Publisher: Hisn al-Muslim title and book citations](https://risala.prh.gov.sa/zh/contents/1490) |
| zh-CN | `bukhari` | 布哈里圣训实录 | `materials/zh-muwatta-shaybani-yu-2000-docx/native-text.txt` — native OOXML front matter |
| zh-CN | `hadeethenc` | 圣训翻译百科全书 | [Publisher site title](https://hadeethenc.com/zh/browse/hadith/66233) |
| zh-CN | `hisn-al-muslim` | 穆斯林的堡垒 | [Publisher: Hisn al-Muslim title and book citations](https://risala.prh.gov.sa/zh/contents/1490) |
| zh-CN | `ibn-majah` | 伊本·马哲圣训集 | `materials/zh-cn-ibn-majah-yu-2013/source-metadata.json` — /title_zh |
| zh-CN | `malik` | 穆宛塔圣训集 | `materials/zh-muwatta-shaybani-yu-2000-docx/source-metadata.json` — /source_title_as_printed |
| zh-CN | `muslim` | 穆斯林圣训实录 | `materials/zh-muwatta-shaybani-yu-2000-docx/native-text.txt` — native OOXML front matter |
| zh-CN | `nasai` | 奈萨仪圣训集 | `materials/zh-cn-ibn-majah-yu-2013/audit/pdf-layout-raw.txt.gz` — preserved prefatory bibliography |
| zh-CN | `tirmidhi` | 提尔米兹圣训集 | `materials/zh-cn-ibn-majah-yu-2013/audit/pdf-layout-raw.txt.gz` — preserved prefatory bibliography |

## Original-title fallback

The Arabic collection names follow the [publisher’s collection directory](https://sunnah.com/), supported by the original Arabic references already preserved in the bank. The Targhib title is also recorded in the Persian source metadata and original references. Compiler names for attribution groups remain compiler names.

`Sunan` and `Jami` are source-used title variants for Tirmidhi. The local label follows the cited language-specific source while the existing English label remains `Jami al-Tirmidhi`; titles of separate `Sahih Sunan` selections are not substituted.

## Verification

Existing navigation tests check that changing language resets only incompatible filters. Shared-title checks compare Python and browser output, including aliases, mixed-language aggregation, exact source preservation, and title use in static, Markdown, and catalog pages. The normal Pages workflow rebuilds every generated view from the accepted source stream.
