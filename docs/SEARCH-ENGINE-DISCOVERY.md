# Search-engine discovery

Hadith Bank publishes ordinary HTML reading pages so that a person can reach a particular source quotation or book from a search result. The interactive reader remains available for filtering and offline search.

**Browse:** [Languages and books](https://blaghtayt-alt.github.io/Hadith-Bank/browse/)

**Book titles and downloads:** [Generated book catalog](../catalog/BOOKS.md)

**Sitemap:** [sitemap.xml](https://blaghtayt-alt.github.io/Hadith-Bank/sitemap.xml)

## What the build generates

`scripts/refresh_bank.py` runs `scripts/build_discovery.py` against the accepted, checksum-verified search corpus. It generates these paths in the `_site/` deployment artifact:

| Website path, under `/Hadith-Bank/` | Content |
| --- | --- |
| `browse/` | Accepted languages and links to their books |
| `browse/<language>/` | Collections available in that language |
| `browse/<language>/<book>/` | Source editions and their actual titles |
| `browse/<language>/<book>/<edition>/` | Edition information, downloads and paginated links to records |
| `hadith/<language>/<book>/<edition>/<stable-id-hash>.html` | One preserved source occurrence, its reference and provenance |
| `sitemap.xml` | Sitemap index pointing to generated URL lists |

The record path uses the first 24 hexadecimal characters of the SHA-256 of the stable occurrence ID. Reordering records or adding unrelated material therefore does not renumber existing reading URLs. Distinct occurrences and editions remain distinct even when their wording or numbers match.

Every individual page contains its narration text in the initial HTML. It has a descriptive title, a text-derived description, a canonical URL, and links to the source edition and GitHub repository. Original Word/PDF downloads use the verified files already preserved in GitHub. Native-language text and titles remain visible, including right-to-left text where appropriate. Metadata-only and private/unavailable catalog entries do not become new published narration pages.

This structure follows Google’s [JavaScript SEO guidance](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics) and [crawlable-link guidance](https://developers.google.com/search/docs/crawling-indexing/links-crawlable): useful initial HTML and real `<a href>` links let crawlers reach content without operating a search form.

## Source fidelity comes first

The static pages reuse accepted source records. They do not create a new translation, claim independent QC, invent a missing Arabic text, convert source-local numbers into canonical numbers, or merge repeated narrations. Human/AI/Unknown translation classifications, excerpt/variant descriptions and applicable OCR-review labels follow the existing reader policies.

Canonical URLs identify each page itself. Different source editions and translations are not all canonicalized to an English page. Automatic `hreflang` groups are omitted because a shared collection name or number does not establish that two records are equivalent translations. Any future language-alternate links must have verified correspondence and follow Google’s [localized-version requirements](https://developers.google.com/search/docs/specialty/international/localized-versions).

Structured data describes only facts shown on the page. It does not add unsupported author, edition, license, ISBN, publication-date or authenticity claims. Valid markup alone does not guarantee a special search appearance; see Google’s [structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).

## Sitemap and hosting

The sitemap contains absolute canonical website URLs. The build splits the URL lists at no more than 40,000 entries per file, below Google’s limit of 50,000 URLs or 50 MB uncompressed per sitemap. It omits `lastmod` when a trustworthy content-change date is unavailable, rather than claiming every unchanged record was modified at build time. See [Google’s sitemap documentation](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

Static reading pages are lightweight and share styling; they do not each embed the entire search dataset. Source-book binaries remain in GitHub. The build checks the hosted output size against [GitHub Pages’ published-site limit](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

The Markdown book catalog is committed with generated repository catalogs. The individual HTML pages and sitemap are deployed from `_site/`, so new imports regenerate the site without adding thousands of manually maintained files to the repository.

## Optional owner setup in Google Search Console

Publishing the sitemap makes it available; it does not by itself verify a Search Console property or submit the sitemap to Google.

1. In [Google Search Console](https://search.google.com/search-console/), add or open the URL-prefix property **`https://blaghtayt-alt.github.io/Hadith-Bank/`**.
2. Complete an ownership-verification method offered for that property. Preserve any required verification file or tag through future site builds.
3. Open **Sitemaps** and submit **`sitemap.xml`**, whose full URL is **`https://blaghtayt-alt.github.io/Hadith-Bank/sitemap.xml`**.
4. Use **URL Inspection** on a book page and an individual narration page to examine Google’s indexing status. The sitemap handles the larger set of URLs; repeated requests for the same page do not speed up crawling.

Google states that crawling can take days to weeks, and a crawl request does not guarantee inclusion. Search rankings and snippets are determined by the search engine. See [requesting a recrawl](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl).

## GitHub project-site robots behavior

This is a GitHub **project** site. The robots file that can govern it is at the host root:

`https://blaghtayt-alt.github.io/robots.txt`

A file at `/Hadith-Bank/robots.txt` would be inside a subdirectory and would not serve as that host’s authoritative robots file. This repository does not claim to control the account-root site. Its crawlable links and published sitemap provide discovery paths; crawling is allowed by default unless an applicable rule blocks it. See Google’s [robots.txt location rules](https://developers.google.com/crawling/docs/robots-txt/create-robots-txt).

If the account-root site is managed separately, its owner can reference the project’s sitemap there. That is a separate host-level change, not a requirement to create misleading project-level robots rules.

## Maintaining discoverability

Keep source occurrence IDs stable, preserve old source paths, and use the normal registration/build workflow for additions. Do not edit generated narration pages individually. Review the generated catalog and live sitemap after deployment, and use Search Console to distinguish a publication problem from a search-indexing delay.

The build and focused software tests check URL stability, escaping, multilingual text, source-download paths, sitemap consistency and source-preserving behavior. A successful deployment establishes that pages are available to crawl; only the search engine’s own indexing reports establish whether it has indexed a given page.
