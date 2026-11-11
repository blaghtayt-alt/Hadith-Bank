# Website and automatic updates

**Live reader:** <https://blaghtayt-alt.github.io/Hadith-Bank/>

**Workflow:** [Update Hadith Bank website](https://github.com/blaghtayt-alt/Hadith-Bank/actions/workflows/reader-pages.yml)

The website is generated from the canonical data in this repository. It offers every language found in the successfully registered corpus. The public reader is self-contained HTML, so searching and exporting its embedded records do not call an external Hadith service.

The reader's translation-origin filter uses **Human**, **AI** and **Unknown**. Current HadeethEnc and supplied website-sourced Japanese/Vietnamese material is Human under the owner's source confirmation. Older-bank copied material remains Unknown until its origin is confirmed; Unknown does not mean AI. These display decisions are recorded in the [source-origin policy](../catalog/provenance-policy.json) without replacing original source flags or review history. Translation origin and independent quality review remain separate questions.

## What happens after material is added

1. An owner-approved material folder is committed or merged into `main`.
2. GitHub Actions runs the software tests and `python scripts/refresh_bank.py --root . --site-output _site`.
3. The refresh command discovers `materials/*/manifest.json`, checks records and local source files, rebuilds catalogs/search/reading pages, and validates the generated reader.
4. The workflow commits changed generated catalogs, search shards, reading pages, reports and `hadith-bank-reader.html` back to `main`.
5. GitHub Pages deploys the verified `_site` artifact. The public URL stays the same.

The workflow uses a normal Git push and checks whether `main` advanced during the build. It never force-pushes over a newer material addition. A stale run skips publication; a rejected push or failed validation does not deploy its artifact. The next successful run updates the website.

Generated commits use GitHub's built-in workflow token and a `[skip ci]` message. They do not start an endless rebuild loop. Pull requests run the tests and full build with read-only repository permissions; only a successful `main` run can synchronize generated files and deploy.

## Website versus a downloaded HTML file

| Entry point | Updates |
| --- | --- |
| Hosted website URL | Updates after a successful build/deployment from `main`. Refresh the browser to load the current build. |
| **Download offline reader** on the website | Saves the current reader and all its searchable records in one HTML file. |
| A previously downloaded `hadith-bank-reader.html` | Remains the saved snapshot. Download a fresh copy for later additions. |
| Full Git checkout | `git pull` retrieves canonical additions and synchronized generated files. You can rebuild locally as well. |

A `file:///C:/...` address refers only to a file on that computer. Use the HTTPS website URL when linking the bank in a README or sharing it with someone else.

The standalone HTML uses the browser's built-in gzip decompression. To create an uncompressed reader for a browser without that API, use `python scripts/build_reader.py --root . --output reader-uncompressed.html --uncompressed`.

## Diagnose an update that has not appeared

Open the workflow link above and inspect the latest run for the commit that added the material. The **Rebuild and validate all registered material** step reports malformed JSON, duplicate occurrence IDs, missing local sources, hash mismatches and other input problems. Correct the indicated canonical input or manifest and push the correction.

The website keeps its last successful deployment when a build fails. The reader's build information identifies its source revision, so compare that with the commit you expected. A successful build followed by a failed deploy is a Pages configuration/deployment problem, not proof that the new narrations were lost.

For a manual rebuild, open **Actions → Update Hadith Bank website → Run workflow**, choose `main`, and run it. Manual runs on other branches do not publish.

## Repository setup

Under **Settings → Pages → Build and deployment**, the publishing source must be **GitHub Actions**. The deployment environment is `github-pages`. The workflow needs `contents: write` only for the main job that synchronizes generated files. Its separate deployment job uses `pages: write` and `id-token: write` to deploy the artifact.

If branch rules prevent GitHub Actions from committing generated files, the synchronization step fails and the site remains at its last good deployment. Adjust the repository's intended bot/branch policy or commit the generated output through the permitted review route; do not force-push around the rule.

The site contains the built reader and its download copy, not a web server for every evidence file. Hosted source links open the corresponding source/evidence path in the GitHub repository. A full downloaded bank retains its local original-file locators.

## Official GitHub references

- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Checkout action](https://github.com/actions/checkout)
- [Python setup action](https://github.com/actions/setup-python)
- [Pages deployment action](https://github.com/actions/deploy-pages)
- [Workflow triggers and the built-in token](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
