# Medtrica · Hugo + PaperMod

A responsive medical products catalog built with Hugo and the actual PaperMod theme. The homepage and CSS are customized; content pages, search, metadata and feeds use PaperMod. Original Medtrica images are stored locally.

## Preview

Install Hugo 0.158.0 or newer (CI pins 0.168.0), then run:

```sh
hugo server --bind 127.0.0.1
```

Open http://localhost:1313/. Production build: `hugo --gc --minify`.

## GitHub Pages

1. Create a GitHub repository and push these files to its `main` branch.
2. In **Settings → Pages → Build and deployment**, choose **GitHub Actions**.
3. The included workflow builds and deploys the site on every push to `main`; pull requests build without deploying.

The workflow uses GitHub’s configured Pages URL, including project subpaths. `hugo.toml` uses `https://medtrica.com/` for local production builds. For domain cutover, configure `medtrica.com` in Pages settings and update DNS only when ready. No custom domain file is included, so previews do not claim the existing domain.

## Editing

- `content/products/`: category pages in Markdown.
- `data/products.json`: homepage category cards.
- `content/about.md`, `content/contact.md`, `content/oem-private-label.md`: company pages.
- `layouts/home.html`: homepage.
- `assets/css/extended/medtrica.css`: PaperMod style extensions.
- `static/images/`: original Medtrica assets.

The PaperMod source is vendored under `themes/PaperMod` with its MIT license. Retrieved from upstream master on 2026-10-19; replace this directory deliberately when updating the theme.

## Content scope

This is a redesigned category catalog, not a complete migration of the legacy WordPress product inventory or blog. Company details and product ranges were adapted from https://medtrica.com/, /about/ and /oem-private-label/. Verify contact details before launch. Detailed specifications, regulatory claims, individual SKUs and legacy article content have not been imported. Original page URLs will need a redirect plan when the full legacy URL inventory is available; GitHub Pages does not support server-side redirects.

Inquiries use working email and telephone links. A cart, checkout, newsletter subscription and backend contact form are not included. No GitHub repository or deployment has been created by this local build.
