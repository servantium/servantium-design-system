# @servantium/brand

The one place Servantium's identity lives. If a logo, Astro, the email header art, the company address or a public link appears anywhere — website, help, portal, email, a deck — it should come from here.

## What's in it

| Path | What | Source of truth |
|---|---|---|
| `company.json` | Legal name, postal address, public URLs, email addresses, LinkedIn, footer link order | This file. Every live URL was checked to return 200 when added; `status` is planned and its footer link stays hidden (`live: false`). |
| `assets/logo/` | Wordmark (colour and white) and symbol (colour and white), PNG | servantium.com and the Flutter app. No vector master exists yet. |
| `assets/icon/` | Favicons, touch icon, and `glyph/`: 33 line icons from the website | servantium.com |
| `assets/og/` | Default social cards for the website and help center | servantium.com, help.servantium.com |
| `assets/astro/` | **Astro the Astronaut**, 12 poses: SVG masters, PNGs **generated** | The website's `Astronaut.astro` |
| `assets/email/` | The email banner art ("forest night sky") and the bookend strip | **Generated** by `scripts/render.mjs`, seeded so a re-render isn't a redesign |
| `assets/social/` | The LinkedIn circle for footers | **Generated** |
| `assets.manifest.json` | Every asset's permanent, fingerprinted address | **Generated** by `npm run manifest` |

SVG is the master where one exists; PNG and JPG are build outputs. Email clients can't show SVG, so anything an email uses has a raster version, and nobody hand-exports one: edit the SVG (or the generator in `scripts/render.mjs`), run `npm run render`, commit both.

## Using it

```ts
import { company, addressLine, footerLinks, hostedUrl } from '@servantium/brand';

company.urls.help          // https://help.servantium.com
addressLine()              // Servantium Inc. · 1111B S Governors Ave STE 48074, Dover, DE 19904
footerLinks()              // [{ label: 'Help Center', href: 'https://help.servantium.com' }, …]
hostedUrl('logo/servantium-logo-white.png')
                           // https://assets.servantium.com/logo/servantium-logo-white.73c2cede0a.png
```

## Two kinds of consumer

**Bundled consumers** (the website, help, portal and prototypes) import this package and pick up a change with a design-system release.

**URL consumers** (email, Firebase templates, decks, social cards, listings) can't bundle anything. They load images from [assets.servantium.com](https://assets.servantium.com/index.html), where every file has a permanent address that includes a fingerprint of its contents. A changed file gets a new address and old addresses keep working, so an email keeps showing what it was sent with. [docs/asset-library.md](./docs/asset-library.md) covers the schema, what's in the library, what isn't (other companies' logos come from Brandfetch), and how to add a file.

The Flutter app bundles its own copies of Astro. That's engineering's repo; when Astro changes, copy the SVGs from here or point the app at the hosted files.

## Links that change after an email is sent

`company.json` fixes every link for the next release. It can't fix emails already delivered — those are frozen with whatever URL they were sent with.

The fix is a redirect layer: emails link to `https://servantium.com/go/help`, `/go/privacy`, `/go/terms`, and the website's `_redirects` maps each to its real destination. Move the help center, change one redirect, and every email ever sent follows. **Not set up** — it's a change to the website repo. Once it exists, point `company.json`'s `urls` at the `/go/` paths.

The postal address is different: it's text, baked in at send time. That's correct — a legal footer should show the address as it was when the email was sent.
