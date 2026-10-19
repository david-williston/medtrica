# Medtrica · Hugo + PaperMod

Full public-content migration of Medtrica’s WordPress website, with a customized PaperMod homepage, catalog, product pages, search, blog and company pages. Hosted at https://david-williston.github.io/medtrica/.

## Local preview

Install Hugo 0.158.0 or newer (CI pins 0.168.0), then run:

```sh
hugo server
```

Production build: `hugo --gc --minify`. The configured base URL includes `/medtrica/`; GitHub Actions uses the Pages URL automatically. For a future custom domain, configure it in GitHub Pages and update the base URL. No DNS cutover is performed by this repository.

## Content

- `content/legacy/`: imported pages, original product descriptions, tables, options and blog articles. Front matter sets the source URL path explicitly; filenames are stable hashes of the canonical source URL.
- `migration/pages.json`: maps readable original URLs and titles to their Markdown source files.
- `migration/crawl.json`: full crawl inventory and HTTP results.
- `migration/assets.json`: local media inventory and original source file failures.
- `migration/issues.json`: unresolved source content links.
- `data/catalog.json` and `data/routes.json`: product/category/article relationships and page resolution.
- `static/media/`: downloaded original photos and documents.
- `layouts/product.html` and `layouts/catalog.html`: product and listing templates.
- `assets/css/extended/medtrica.css`: PaperMod style extensions.

PaperMod is vendored under `themes/PaperMod` with its MIT license. Retrieved from upstream master on 2026-10-19.

## Repeating the migration

The crawler follows public sitemap URLs, attachment pages, internal navigation and pagination. It excludes administration, tracking/query links and spam comment links. It recovers empty article responses through the public WordPress API. The cache is stored at `/private/tmp/medtrica-crawl`.

```sh
python3 -m venv /private/tmp/medtrica-tools
/private/tmp/medtrica-tools/bin/pip install beautifulsoup4
/private/tmp/medtrica-tools/bin/python scripts/crawl_medtrica.py
/private/tmp/medtrica-tools/bin/python scripts/migrate_medtrica.py
hugo --gc --minify --cleanDestinationDir
python3 scripts/verify_site.py
/private/tmp/medtrica-tools/bin/python scripts/verify_content.py
```

Migration regenerates `content/legacy`, the catalog data, and migration reports. Review changes before committing. Recorded failed assets are not retried automatically; remove their entries from `migration/assets.json` to retry restored source files.

## Hosting and performance

GitHub Pages uses the included Actions workflow. Pushes to `main` build and deploy; pull requests build without deployment. Product links resolve directly to local pages, and search uses local paths. Images and documents are served by GitHub Pages. Catalog/gallery previews use Hugo-generated WebP images with lazy loading; full original photos remain accessible.

Legacy URLs and the first version’s six category URLs are retained through local aliases. The catalog itself links to the destination directly. Government and third-party references link to their original external destinations rather than serving obsolete uploaded copies of those websites.

## Migration limits

See [the migration report](migration/REPORT.md) for exact coverage and source failures. Product and article text is preserved from the source. Broken source images are marked as unavailable, with no invented replacement photos. Unavailable linked articles are recorded rather than fabricated. Spam comments, trackers, WordPress scripts, and backend forms are not imported. Product inquiries use email/phone; GitHub Pages does not run WordPress cart, checkout, captcha, newsletter or form-processing services.
