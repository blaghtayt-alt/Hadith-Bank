# Website and automatic updates

**Search and interactive reader:** [Hadith Bank](https://blaghtayt-alt.github.io/Hadith-Bank/)

**Static reading pages:** [Languages and books](https://blaghtayt-alt.github.io/Hadith-Bank/browse/)

**Workflow:** [Update Hadith Bank website](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

The website is generated from the accepted canonical data in this repository. It offers every language found in the successfully registered corpus. The interactive reader is self-contained HTML: searching and exporting its embedded records do not call an external Hadith service. Individual reading pages provide the same source texts in ordinary HTML, with language, book and edition navigation and links to the repository and original documents.

The reader’s translation-origin filter uses **Human**, **AI** and **Unknown**. Under the owner’s current rule, newly added books and separately acquired English counterparts are Human unless their own source explicitly states otherwise. Copied old-bank and Iman/Qur’an-study material remains Unknown until confirmed. An explicit source declaration of AI translation takes precedence. Each English counterpart follows its own source classification; Arabic originals have no translation-origin label. These decisions are recorded in the [source-origin policy](../catalog/provenance-policy.json) and material provenance without replacing historical flags or review records. Translation origin and independent quality review remain separate questions.

## What happens after material is added

1. An owner-approved material folder is committed or merged into `main`.
2. GitHub Actions runs the software tests and `python scripts/refresh_bank.py --root . --site-output _site`.
3. The refresh command discovers `materials/*/manifest.json`, checks records and local source files, rebuilds catalogs/search/Markdown views, and validates the interactive reader.
4. The static discovery generator builds language, book and edition indexes, a stable page for each accepted source occurrence, and the sitemap index and its shards. The generated [book catalog](../catalog/BOOKS.md) connects source-edition names with reading and download links.
5. The workflow commits changed generated catalogs, search shards, Markdown reading pages, reports and `hadith-bank-reader.html` back to `main`.
6. GitHub Pages deploys the verified `_site` artifact. Its individual HTML pages are generated deployment files; they are not maintained as thousands of extra checked-in source files.

The workflow uses a normal Git push and checks whether `main` advanced during the build. It never force-pushes over a newer material addition. A stale run skips publication; a rejected push or failed validation does not deploy its artifact. The next successful run updates the website.

Generated commits use GitHub’s built-in workflow token and a `[skip ci]` message. They do not start an endless rebuild loop. Pull requests run tests and the full build with read-only repository permissions; only a successful `main` run can synchronize generated files and deploy.

## Website and repository entry points

| Entry point | Purpose and updates |
| --- | --- |
| [Main website](https://blaghtayt-alt.github.io/Hadith-Bank/) | Interactive search and filters; updates after a successful build/deployment from `main`. |
| [Language and book indexes](https://blaghtayt-alt.github.io/Hadith-Bank/browse/) | Ordinary HTML links to source editions and individual occurrences; regenerated with the same accepted corpus. |
| `hadith/<language>/<book>/<edition>/<stable-id-hash>.html` on the website | Individual source text, provenance and available source downloads. The URL derives from the stable occurrence ID. |
| [Book catalog](../catalog/BOOKS.md) | Human-readable source-edition titles and reading/download links in GitHub. |
| [Sitemap](https://blaghtayt-alt.github.io/Hadith-Bank/sitemap.xml) | Machine-readable discovery of canonical reading URLs; regenerated on each successful build. |
| **Download offline reader** | Saves the current reader and all its searchable records in one HTML file. |
| Previously downloaded `hadith-bank-reader.html` | Remains the saved snapshot; download a fresh copy for later additions. |
| Full Git checkout | `git pull` retrieves canonical additions and synchronized generated files; rebuild locally to produce `_site/`. |

Use HTTPS website URLs when sharing a reading page. A file address such as `file:///C:/...` refers only to a file on that computer.

The standalone reader uses the browser’s built-in gzip decompression. To create an uncompressed reader for a browser without that API:

```bash
python scripts/build_reader.py --root . --output reader-uncompressed.html --uncompressed
```

The individual HTML reading pages do not need JavaScript to display their narration text. They do not embed the whole search dataset. Word and PDF originals remain direct GitHub downloads, avoiding duplication of every source binary in the hosted site.

## Search-engine discovery

The static reading pages include page-specific titles and descriptions, self-referencing canonical URLs, and ordinary HTML navigation. Their sitemap lists the same canonical URLs. Distinct source editions and language occurrences stay distinct; the build does not infer translation equivalence or canonical hadith numbers for search-engine metadata.

[Search-engine discovery and owner setup](SEARCH-ENGINE-DISCOVERY.md) explains the sitemap, GitHub project-site robots behavior and optional Google Search Console submission. Publication of crawlable pages does not establish that a search engine has indexed them or assigned a particular ranking.

## Diagnose an update that has not appeared

Open the workflow link above and inspect the latest run for the commit that added the material. The **Rebuild and validate all registered material** step reports malformed JSON, duplicate occurrence IDs, missing local sources, hash mismatches and other input problems. Correct the identified input or manifest and push the correction.

The website keeps its last successful deployment when a build fails. The reader’s build information identifies its source revision; compare it with the expected commit. A successful build followed by a failed deployment is a Pages configuration/deployment problem, not proof that the new narrations were lost.

For a manual rebuild, open **Actions → Update Hadith Bank website → Run workflow**, choose `main`, and run it. Manual runs on other branches do not publish.

## Repository setup

Under **Settings → Pages → Build and deployment**, the publishing source must be **GitHub Actions**. The deployment environment is `github-pages`. The workflow needs `contents: write` only for the main job that synchronizes generated files. Its separate deployment job uses `pages: write` and `id-token: write` to deploy the artifact.

If branch rules prevent GitHub Actions from committing generated files, synchronization fails and the site remains at its last good deployment. Use the repository’s intended bot permissions or permitted review route; do not force-push around the rule.

Hosted source links open the preserved source/evidence paths in GitHub. A full downloaded bank retains the local original-file locators. Source bytes, occurrence IDs, publication decisions, review history and source-specific rights are not rewritten to generate reading pages.

## Official references

- [Custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Configuring the publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [Checkout action](https://github.com/actions/checkout)
- [Python setup action](https://github.com/actions/setup-python)
- [Pages deployment action](https://github.com/actions/deploy-pages)
- [Workflow triggers and the built-in token](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [Google’s crawlable-link guidance](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)
