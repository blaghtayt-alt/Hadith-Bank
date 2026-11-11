# Add material to the bank and website

The reader rebuilds from structured records registered under `materials/`. Add one material folder, register it, then commit or merge it into `main`. The workflow discovers the manifest and updates the website, language/book/edition catalogs, searchable text, reading pages and downloadable HTML automatically.

The folder and its source text become public when uploaded to this public repository. Registration records the owner's publication instruction; it does not certify independent review or change an unknown reuse/translation status into a verified one. Preserve the actual provenance, permission evidence and remaining qualifications.

## 1. Prepare one source edition

Create a new folder, for example `materials/my-source/`, with these files:

| File | Contents |
| --- | --- |
| `records.json` **or** `records.jsonl` | One record for each distinct source narration, variant or occurrence. |
| `source.pdf` or another original source file | The exact source used for the records. The helper accepts other file types, including a text source. |
| Optional evidence/correction files | Existing source metadata, citations, review logs and before/after corrections. Keep record references local to the repository. |
| `manifest.json` | Generated in the next step; declares identity, language, collection, source, counts and hashes. |

Use a separate folder and edition identifier for a different source edition. Repeated text, different chains, multiple translated versions and separately printed occurrences must not be collapsed into one record.

### Record format

`records.json` is a UTF-8 JSON array. `records.jsonl` has one complete JSON object on each line. Each record needs a nonempty, globally unique `id` and a `text` object with separate `arabic` and `translation` values. Use a string for supplied source wording and `null` when it is missing. Keep source omissions and their explanations; never invent a replacement narration.

This is a **literal TEST example of the format**, not Hadith material:

```json
[
  {
    "id": "test-example:ja:source-001:p0001:occ0001",
    "title": "TEST",
    "text": {
      "arabic": null,
      "translation": "TEST"
    },
    "number": {
      "in_book": null,
      "canonical": null
    },
    "narrator": {"name": null},
    "translator": {"name": null},
    "page": {"pdf": [1], "printed": []},
    "ai_translation": "unknown",
    "review": {
      "status": "pending",
      "independent_pro_qc": "pending",
      "release_eligible": false
    },
    "rights": {
      "status": "not_assessed_for_publication",
      "reuse_basis": null
    },
    "footnotes": [],
    "references": {}
  }
]
```

For an actual addition, replace the TEST values with the exact source wording and evidence. Preserve separate fields for available source numbers, narrator/isnad, translator, pages, commentary, notes, references, grading, topic/source-structure tags, variants, corrections and review history. The canonical JSON retains additional supplied metadata.

Keep IDs stable across corrections to the same occurrence. Use a different ID for a different occurrence or source edition. Do not infer human/AI translation from the fact that a file was scanned or OCR-extracted: use `false` only where human translation is established, `true` where AI translation is established, and `"unknown"` otherwise. The reader displays these as **Human**, **AI** and **Unknown**; Unknown is not a claim of AI translation.

The current [source-origin policy](../catalog/provenance-policy.json) also records the owner's source confirmations. It labels the HadeethEnc and currently supplied website-sourced Japanese/Vietnamese materials **Human**, while material copied from the older bank stays **Unknown** until the owner confirms it. This display policy preserves the original import flags and review history. New sources do not inherit the current sources' Human classification merely because they use the same language or book.

## 2. Register the folder

Run this from the repository root with Python 3.11 or later. Substitute the folder, language, collection, edition and printed source title for your material:

```bash
python scripts/register_material.py --root . --directory materials/my-source --language ja --book muslim --edition edition-1 --name "Printed source title" --records records.json --source source.pdf
```

For JSONL, use `--records records.jsonl`. An optional `--source-url` records the source's attribution URL; the original file is still stored locally. Optional `--id` and `--source-id` let you supply stable identifiers instead of the helper's defaults.

| Argument | Meaning |
| --- | --- |
| `--directory` | This material's folder under `materials/`. |
| `--language` | Language code, such as `ja`, `vi`, `fil`, `zh-CN`, `hi` or `ar`. A new code becomes available in the reader automatically. |
| `--book` | Stable collection/book slug, such as `muslim`, `bukhari` or `abu-dawud`. |
| `--edition` | Stable identifier for this source edition or snapshot. |
| `--name` | Actual title/name of the supplied source. |
| `--records` | Records filename within the material folder; defaults to `records.json`. |
| `--source` | Original source filename within the same folder. |

The helper checks the records and computes the record count and SHA-256 hashes. It writes a `hadith-bank-material-v1` manifest with repository-relative paths and an explicit owner-publication decision. You do not need to calculate hashes or edit the HTML manually.

## 3. Check locally, then upload

```bash
python scripts/refresh_bank.py --root . --site-output _site
```

Open `_site/index.html` to inspect the complete updated reader. Search for an exact phrase from the new source and use its language, collection and source-edition filters. Check that missing values and review qualifications are shown accurately.

Commit the material folder through Git, or use GitHub's **Add file → Upload files** for a suitable-size folder. Keep `manifest.json`, the records and the original source together in the same change. If using a pull request, merge it into `main` after the validation job succeeds.

The **[Update Hadith Bank website](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)** run then rebuilds and publishes the site. It also synchronizes generated bank catalogs, search shards, reading pages and the HTML in the repository. The [website URL](https://blaghtayt-alt.github.io/Hadith-Bank/) remains unchanged.

You can commit just the canonical material folder; the workflow produces the derived files. Do not manually edit `search/`, `browse/`, generated catalog entries or the embedded HTML to add a narration. Such changes would be replaced by the next canonical-data build.

## Correct or extend an existing source

Edit the existing canonical records, retaining their occurrence IDs, source wording history and actual review state. Add a separate correction log where source bytes change. If you are adding a different edition, create a new material folder instead of overwriting the previous source.

After an intended edit to the records or original source file, re-run the same registration command with **`--replace`**:

```bash
python scripts/register_material.py --root . --directory materials/my-source --language ja --book muslim --edition edition-1 --name "Printed source title" --records records.json --source source.pdf --replace
python scripts/refresh_bank.py --root . --site-output _site
```

`--replace` recomputes the manifest's hashes and count while retaining its existing optional metadata and publication decision. Commit the changed canonical data, correction evidence and manifest together. An accidental data edit without its updated hash fails validation rather than silently changing the website.

If you used explicit `--id`, `--source-id` or `--source-url` values originally, retain them when updating. Always inspect the manifest diff before committing; changing the language/book/edition identity can change where a source appears.

## Existing supplied packages

The current Japanese Sahih Muslim and Vietnamese PDF packages use the `pdf-intake-package-v1` adapter. Their manifests point to the unchanged full packages under `attachments/`, preserving their original records, page/source evidence, shortened references, raw Arabic, review logs and checksums. They are not re-extracted during a website build.

Ordinary new additions use the simpler `records-v1` format documented above. Do not hand-convert an existing package merely to make it fit this example. Its package adapter can preserve the original structure and register its source editions without changing their text.

## What automatic integration does and does not do

| Input/change | Result |
| --- | --- |
| Valid registered JSON/JSONL plus its local original source | Included in the next successful build. |
| New registered language or collection | Appears automatically in the reader filters and generated indexes. |
| Corrected canonical record plus updated manifest | Rebuilds the same occurrence; original IDs and supplied correction history remain available. |
| A PDF uploaded without structured narration records and a manifest | Stored as a file, but not automatically segmented into searchable narrations. |
| Duplicate IDs, malformed JSON, unsafe/missing paths or incorrect hashes | Build fails; the last successful live site remains available. |
| Pending review, missing Arabic or unknown translator/rights fields | Retained as qualifications; the build does not invent facts or claim scholarly approval. |

Extracting a PDF, checking every character against its pages, repairing Arabic and evaluating source/translation authenticity are separate tasks. Automatic integration validates the registered data and builds the reader; it does not perform those reviews.

[Website and deployment details](WEBSITE.md) · [Material manifest schema](../schemas/material-manifest.schema.json) · [Material record schema](../schemas/material-record.schema.json) · [Review and rights policy](REVIEW-AND-RIGHTS.md)
