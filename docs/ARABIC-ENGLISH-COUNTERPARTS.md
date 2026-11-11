# Arabic and English counterparts

The reader offers **Show Arabic text** and **Show English text**. These controls add source counterparts beside the original-language occurrence. Each supplied counterpart retains its exact text, a bracketed collection-and-number citation when available, publisher credit, source URL, source version and its own translation-origin label. The original occurrence's Unknown/Human/AI classification is unchanged.

Arabic and English narration keywords and explicit collection/number references are searchable whether the display controls are open or closed. Arabic, Persian and Western digit forms are normalized for searching only. Source text and downloaded JSON retain the original characters. The language selector continues to describe the original bank occurrence, so counterpart languages do not inflate occurrence counts.

For example, `Sahih Muslim 1907`, `Muslim no. 1907`, `صحيح مسلم رقم ١٩٠٧` and `Muslim ۱۹۰۷` address the same collection/number pair. Add narration words to narrow the results further. A record citing Bukhari 1 and Muslim 1907 cannot satisfy `Bukhari 1907`. Distinct works such as Nasa'i's Sunan and al-Sunan al-Kubra retain separate search identities.

## What automatic matching establishes

The official English HadeethEnc export supplies English quotations, corresponding Arabic text and Arabic revision identifiers. The preserved Arabic export supplies bibliography only when the provider ID, Arabic version and quotation match. Existing translated source records and the official Persian export provide additional quotation-identity evidence.

- Primary HadeethEnc occurrence IDs link automatically to the same publisher entry. Differing Arabic revisions are labeled as related publisher versions.
- A provider URL inherited from a lesson or article additionally requires a quotation match. Its notes cannot inherit the main hadith's identity just because they share a parent file.
- Other matches require a unique literal source quotation, using available cited references as corroboration. Number-only or semantic guesses are not used.
- Full counterparts remain labeled when the original record preserves only an excerpt or reported meaning.
- Publication years, volume/page locators, source-entry IDs and local sequence labels are not hadith numbers. Bibliographic collection numbers remain publisher-reported references, not an independent verification of every route or wording variant.

Some materials cannot yet be linked: for example, unnumbered translations without an approved Arabic quotation or a matching source-language passage. Their original text remains fully available. The reader states that a counterpart is not linked; it never silently generates a substitute translation. Some linked publisher entries also lack a safely established collection number.

See the generated [coverage and unresolved-record report](../reports/counterpart-coverage.json) and [source manifest](../sources/counterparts/hadeethenc/manifest.json).

## Automatic integration and reproducible commands

The website workflow discovers provider IDs from canonical source registries, verifies existing cached exports, and fetches an updated official export when newly registered IDs are missing. Matching is rerun during every bank rebuild. Supported additions therefore receive available counterparts without hand-editing records. A missing English publisher entry stays unresolved and is recorded explicitly.

```bash
# Reuse verified cached sources, or retrieve an export needed for new IDs.
python scripts/sync_hadeethenc_counterparts.py --root .

# Verify the cache and rebuild with no network requests.
python scripts/sync_hadeethenc_counterparts.py --root . --offline
python scripts/refresh_bank.py --root . --site-output _site

# Explicitly update the official source versions, preserving earlier bytes.
python scripts/sync_hadeethenc_counterparts.py --root . --refresh
```

The source manifest pins the exact SQLite databases, ZIPs and publisher-version evidence. Changed exports receive new content-addressed filenames and prior manifests are retained. The browser's reading, searching and JSON export remain self-contained and offline. Source website links require an Internet connection.

HadeethEnc's [publisher conditions](https://hadeethenc.com/en/home) continue to apply. This integration creates no new translation and claims no independent scholarly, translation or OCR review.
