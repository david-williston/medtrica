---
title: Release Notes
description: Versioned updates and change history for the Medtrica website.
hideMeta: true
robotsNoIndex: true
searchHidden: true
hiddenInRss: true
sitemap:
  disable: true
---

## Release notes

Updates use calendar versions: year.month.day, followed by `.1`, `.2` and so on for further releases on the same day.

Current site version: {{< site-version >}}

### v2026.10.19.1 · October 19, 2026

**Mobile search and visual refinements**

- Reduced typography slightly while keeping comfortable spacing and large touch targets.
- Added a prominent search link to the mobile header on every page.
- Displayed the product-range icons at their original size instead of enlarging low-resolution images.
- Clarified that product quote buttons open an email app, with visible contact alternatives.
- Linked every historical commit to its GitHub changes and included merged-branch commits in the history generator.
- Enabled GitHub Pages deployments from version tags.

### v2026.10.19 · October 19, 2026

**A complete catalog, clearer reading, and versioned updates**

- Migrated the available product catalog, photos, specifications, options, documents, blog articles and company pages to Hugo and PaperMod on GitHub Pages.
- Added larger typography, clearer mobile navigation, corrected list spacing, and layouts that accommodate enlarged text.
- Rebuilt the contact page with USA and Canada office details, directions links and embedded Google Maps.
- Added subtle page animations and rotating button glints, respecting reduced-motion preferences.
- Aligned the colors with the Medtrica logo’s navy and violet.
- Added calendar-versioned releases, a footer version, and these release notes with change history.

The deferred content-formatting review is tracked in [GitHub issue #1](https://github.com/david-williston/medtrica/issues/1).

## Complete commit history

Every commit is listed below, including the work before versioning was introduced. The initial release includes all eight commits from the original site build through the branding and versioning update. Select a commit number to view its changes on GitHub.

{{< git-history >}}
