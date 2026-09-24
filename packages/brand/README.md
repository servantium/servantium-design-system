# @servantium/brand

The one place Servantium's identity lives. If a logo, Astro, the email header art, the company address or a public link appears anywhere — website, help, portal, email, a deck — it should come from here.

## What's in it

| Path | What | Source of truth |
|---|---|---|
| `company.json` | Legal name, postal address, public URLs, footer link order | This file. Every URL was checked to return 200 when added. |
| `assets/logo/` | `servantium-logo.png` (on light), `servantium-logo-white.png` (on dark) | Copied from servantium.com, 723×170 |
| `assets/astro/astro-<pose>.svg` | **Astro the Astronaut** — waving, captain, detective, professor, cowboy | Copied from the Flutter app's `assets/astronaut_*.svg` |
| `assets/astro/astro-<pose>.png` | Astro rasterised, 240×240 | **Generated** — `npm run render` |
| `assets/email/header-<size>.{svg,jpg}` | The email banner art ("forest night sky"), compact / standard / hero | **Generated**, seeded so a re-render isn't a redesign |

SVG is the master; PNG and JPG are build outputs. Email clients can't show SVG, so anything an email uses has a raster version — but nobody hand-exports one. Edit the SVG (or the art generator in `scripts/render.mjs`), run `npm run render`, commit both.

## Using it

```ts
import { company, addressLine, footerLinks, assetUrl } from '@servantium/brand';

company.urls.help          // https://help.servantium.com
addressLine()              // Servantium Inc. · 1111B S Governors Ave STE 48074, Dover, DE 19904
footerLinks()              // [{ label: 'Help Center', href: 'https://help.servantium.com' }, …]
assetUrl('astro/astro-waving.png', 'https://assets.servantium.com/brand')
```

## Change once, update everywhere

There are two kinds of consumer, and they get updates in different ways.

**Bundled consumers** — the website, help, portal and prototypes — import this package. They pick up a change the same way they already pick up Verdant tokens: tag a design-system release, and `publish.yml` opens a pull request in each one.

**URL consumers** — email, Firebase templates, OG images, decks, G2/Capterra listings — can't bundle anything. An email is HTML that downloads its images from the internet every time it's opened. For these, the answer is **one stable public address per asset**:

```
https://assets.servantium.com/brand/logo/servantium-logo-white.png
https://assets.servantium.com/brand/astro/astro-waving.png
https://assets.servantium.com/brand/email/header-hero.jpg
```

Because the email loads the image when it's opened, replacing the file at that address updates **every email ever sent** — last year's welcome emails show this year's Astro. That only works if the addresses never change, so they are unversioned on purpose.

### Proposed hosting (not set up yet)

| | |
|---|---|
| **Where** | A Cloudflare R2 bucket on a custom domain, `assets.servantium.com` |
| **Published by** | The design-system release workflow: on tag, upload `packages/brand/assets/**` |
| **Headers** | `Cross-Origin-Resource-Policy: cross-origin` · `Cache-Control: public, max-age=86400` |
| **Why not servantium.com/brand?** | It already hosts the logo, but every response carries `Cross-Origin-Resource-Policy: same-site`, which tells browser engines to refuse the image anywhere else. Gmail and Outlook fetch through their own servers and don't care; Apple Mail with Privacy Protection off does. It also ties brand assets to website deploys. |

Until that exists, `DEFAULT_ASSET_BASE` in `src/index.ts` is `null` and assets resolve to relative paths — right for previews, wrong for a real send.

The Flutter app bundles its own copies of Astro. That's engineering's repo; when Astro changes, copy the SVGs from here or point the app at the hosted URLs.

## Links that change after an email is sent

`company.json` fixes every link for the next release. It can't fix emails already delivered — those are frozen with whatever URL they were sent with.

The fix is a redirect layer: emails link to `https://servantium.com/go/help`, `/go/privacy`, `/go/terms`, and the website's `_redirects` maps each to its real destination. Move the help center, change one redirect, and every email ever sent follows. **Not set up** — it's a change to the website repo. Once it exists, point `company.json`'s `urls` at the `/go/` paths.

The postal address is different: it's text, baked in at send time. That's correct — a legal footer should show the address as it was when the email was sent.
