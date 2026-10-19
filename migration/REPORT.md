# Medtrica migration audit — 19 October 2026

The crawler inspected **313 public internal URLs**, starting with every sitemap and following navigation, attachment pages and pagination. It also retrieved the public WordPress article API and checked the media inventory to recover missing content.

## Imported content

- **71 distinct products**, including every product in the product sitemap. The sitemap’s 72 entries include the catalog index.
- **22 category indexes**, including usable indexes for positioning pads and body bags whose old category URLs redirected to other content.
- **45 blog articles**, including six recovered from empty HTML responses through the public WordPress API. The post sitemap’s extra entry is the blog index.
- Company, OEM, contact, sitemap, attachment and archive pages.
- **389 locally hosted image files** and **82 locally hosted PDF documents**. Original full-size product photos remain available; Hugo makes smaller WebP previews.
- **442 product option values** (sizes, materials, quantities and similar choices), plus the descriptions, tables and product codes shown on the original pages.

## Verification

Automated checks compare every product’s source paragraphs, table rows and option values to the generated HTML: **71 products, 1,161 paragraphs/table rows, 442 option values**. A separate link check covers every generated HTML file and local page/media target, including aliases and search URLs. Both domain-root and GitHub Pages project-path builds are checked. Browser checks cover representative catalog, product and search pages.

These checks do not open every page manually or crawl the external websites cited by articles.

## Source failures and handling

**60 older article image URLs and four reference URLs return HTTP 404 on the original server.** These failures are recorded in `assets.json`; missing images retain their descriptive text with an unavailable-image caption, and failed reference anchors retain their text. No replacement photos or article text were invented. All product gallery images and product PDF downloads imported successfully.

The original server also returns 404 for two linked articles (the sciatica and hypoallergenic-mattress buying guides) and two obsolete category paths. The category links now point to the correct local categories. The unavailable articles remain listed in `crawl.json`, and the retained unresolved content reference is recorded in `issues.json`.

Hundreds of unrelated links in spam comments were excluded. Tracking code, third-party scripts and WordPress backend forms were removed. Product inquiries use email/phone. Public government and third-party references point to their external source sites rather than to obsolete uploaded HTML copies.

## Performance changes

Catalog, product and search links stay within the GitHub Pages site. Images and PDF documents are hosted locally. Catalog thumbnails and gallery previews use WebP; below-the-fold images load lazily. Legacy aliases are retained for bookmarks, while catalog links go directly to their destination pages.
