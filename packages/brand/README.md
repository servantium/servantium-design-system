# @servantium/brand

The one place Servantium's identity lives. If a logo, Astro, the email header art, the company address or a public link appears anywhere — website, help, portal, email, a deck — it should come from here.

## What's in it

| Path | What | Source of truth |
|---|---|---|
| `company.json` | Legal name, postal address, public URLs, email addresses, LinkedIn, footer link order | This file. Every live URL was checked to return 200 when added; `status` is planned and its footer link stays hidden (`live: false`). |
| `assets/logo/` | `servantium-logo.png` (on light), `servantium-logo-white.png` (on dark) | Copied from servantium.com, 723×170 |
| `assets/astro/astro-<pose>.svg` | **Astro the Astronaut** — waving, captain, detective, professor, cowboy | Copied from the Flutter app's `assets/astronaut_*.svg` |
| `assets/astro/astro-<pose>.png` | Astro rasterised, 240×240 | **Generated** — `npm run render` |
| `assets/email/header-{standard,hero}.{svg,jpg}` | The email banner art ("forest night sky"): standard, and a taller hero for when a mascot is in the banner | **Generated**, seeded so a re-render isn't a redesign |
| `assets/email/footer-bar.{svg,jpg}` | The bookend strip of the same sky under every email | **Generated**, same seed |
| `assets/social/linkedin.{svg,png}` | The LinkedIn circle in the email footer | SVG from the website footer; PNG **generated** |

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

### Hosting

They'll be served from a Cloudflare R2 bucket, `servantium-assets`, on `assets.servantium.com`, uploaded by the email workflow on each production release. **Not set up yet.** [docs/hosting.md](./docs/hosting.md) is the plan: what goes in the bucket, its structure, headers, access, cost and the setup steps.

Until it exists, `DEFAULT_ASSET_BASE` in `src/index.ts` is `null` and assets resolve to relative paths. That's right for previews and wrong for a real send.

The Flutter app bundles its own copies of Astro. That's engineering's repo; when Astro changes, copy the SVGs from here or point the app at the hosted URLs.

## Links that change after an email is sent

`company.json` fixes every link for the next release. It can't fix emails already delivered — those are frozen with whatever URL they were sent with.

The fix is a redirect layer: emails link to `https://servantium.com/go/help`, `/go/privacy`, `/go/terms`, and the website's `_redirects` maps each to its real destination. Move the help center, change one redirect, and every email ever sent follows. **Not set up** — it's a change to the website repo. Once it exists, point `company.json`'s `urls` at the `/go/` paths.

The postal address is different: it's text, baked in at send time. That's correct — a legal footer should show the address as it was when the email was sent.
